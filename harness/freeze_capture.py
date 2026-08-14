#!/usr/bin/env python3
"""One-shot freeze capture. Run ON the device, at the freeze, before killing.

This is the script that produced logs/live-20260812/separable-freeze/. It reads
each thread twice with a gap and nothing else, so unlike stall_watch*.py it does
not walk kernel stacks for fifty threads ten times a second -- brief #28 records
that doing so measurably amplified the very freezes it was there to catch.

What it answers in one pass:

  is anything running          thread states, and utime/stime moved or not
  what is each thread waiting  syscall number, arguments, sp and pc
  is the wait escapable        futex operation and whether a timeout was passed
  will anyone wake it          the futex word itself, read from /proc/pid/mem
  is the wait a mutex          val==2 is mutex contention, val==0 is not
  what is actually loaded      sha256 of every bind-mounted Wine module
  is it the environment        dmesg tail, memory, swap, clock cap, temperatures

Usage, at the freeze:

    python3 freeze_capture.py --out /tmp/freeze-$(date +%Y%m%d-%H%M)

Then copy the directory off the device and only then kill the game.
"""

import argparse
import glob
import json
import os
import re
import struct
import subprocess
import time

COMM = "mgs2_sse_rg353v"

# The game runs 32-bit under Box86, so its futex is 240 (or 422 for the time64
# variant) and ioctl is 54. The arm64 numbers are here as well so this script can
# be exercised against a native process, where futex is 98.
SYSCALLS = {
    54: "ioctl", 240: "futex", 422: "futex_time64", 142: "select",   # arm32
    98: "futex", 29: "ioctl", 73: "ppoll",                           # arm64
}

# futex operation word, low bits, after masking the flags.
FUTEX_PRIVATE = 128
FUTEX_CLOCK_REALTIME = 256
FUTEX_OPS = {0: "WAIT", 1: "WAKE", 9: "WAIT_BITSET", 10: "WAKE_BITSET"}

MOUNT_TARGETS = [
    "/usr/lib/wine/i386-windows/wined3d.dll",
    "/usr/lib/wine/i386-windows/d3d8.dll",
    "/usr/lib/wine/i386-windows/user32.dll",
    "/usr/lib/wine/i386-windows/dmime.dll",
    "/usr/lib/wine/i386-windows/dmusic.dll",
    "/usr/lib/wine/i386-windows/dmsynth.dll",
    "/usr/lib/wine/i386-windows/dsound.dll",
    "/usr/lib/wine/i386-unix/opengl32.so",
    "/usr/lib/wine/i386-unix/winewayland.so",
    "/usr/lib/wine/i386-unix/win32u.so",
    "/usr/lib/wine/i386-unix/ntdll.so",
    "/usr/bin/box86",
]


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as stream:
            return stream.read().strip()
    except OSError:
        return None


def find_pid(comm):
    found = []
    for entry in os.listdir("/proc"):
        if entry.isdigit() and read(f"/proc/{entry}/comm") == comm:
            found.append(int(entry))
    if len(found) != 1:
        raise SystemExit(f"expected exactly one {comm!r}, found {found}")
    return found[0]


def decode_futex_op(op):
    """Name the operation and say whether the wait can ever time out."""
    base = op & ~(FUTEX_PRIVATE | FUTEX_CLOCK_REALTIME)
    flags = []
    if op & FUTEX_PRIVATE:
        flags.append("PRIVATE")
    if op & FUTEX_CLOCK_REALTIME:
        flags.append("CLOCK_REALTIME")
    return "_".join([FUTEX_OPS.get(base, f"op{base}")] + flags)


def sample(pid):
    """One pass over every thread: state, times, and the pending syscall."""
    out = {}
    for task in glob.glob(f"/proc/{pid}/task/*"):
        tid = os.path.basename(task)
        stat = read(f"{task}/stat")
        if not stat:
            continue
        # comm is parenthesised and may contain spaces; split on the last ')'.
        fields = stat[stat.rindex(")") + 2:].split()
        out[tid] = {
            "comm": read(f"{task}/comm"),
            "state": fields[0],
            "utime": int(fields[11]),
            "stime": int(fields[12]),
            "wchan": read(f"{task}/wchan"),
            "syscall": read(f"{task}/syscall"),
        }
    return out


def peek_word(pid, address):
    """Read one 32-bit word out of the live process."""
    try:
        with open(f"/proc/{pid}/mem", "rb", buffering=0) as memory:
            memory.seek(address)
            data = memory.read(4)
        return struct.unpack("<I", data)[0] if len(data) == 4 else None
    except (OSError, ValueError, OverflowError):
        return None


def region_of(pid, address):
    for line in (read(f"/proc/{pid}/maps") or "").splitlines():
        match = re.match(r"([0-9a-f]+)-([0-9a-f]+) (\S+).*?(\S*)$", line)
        if match and int(match.group(1), 16) <= address < int(match.group(2), 16):
            return f"{match.group(1)}-{match.group(2)} {match.group(3)} {match.group(4) or '[anon]'}"
    return "unmapped"


def analyse_waits(pid, threads):
    """The part that decides whether a stuck thread can ever be woken."""
    verdicts = []
    for tid, info in sorted(threads.items(), key=lambda kv: -kv[1]["utime"]):
        raw = (info.get("syscall") or "").split()
        if not raw or raw[0] in ("running", "-1"):
            continue
        try:
            number = int(raw[0])
        except ValueError:
            continue
        if SYSCALLS.get(number) not in ("futex", "futex_time64"):
            continue
        uaddr = int(raw[1], 16)
        op = int(raw[2], 16)
        val = int(raw[3], 16)
        timeout = int(raw[4], 16)
        word = peek_word(pid, uaddr)
        verdicts.append({
            "tid": tid,
            "comm": info["comm"],
            "utime": info["utime"],
            "uaddr": hex(uaddr),
            "region": region_of(pid, uaddr),
            "operation": decode_futex_op(op),
            "expected_val": val,
            "timeout": "NONE (untimed wait)" if timeout == 0 else hex(timeout),
            "futex_word": None if word is None else word,
            "still_blocked": None if word is None else (word == val),
            # A contended glibc mutex waits for 2. Waiting for 0 means waiting
            # for the word to become non-zero: a semaphore or event, not a mutex.
            "shape": "mutex contention" if val == 2 else
                     "semaphore/event (waits for non-zero)" if val == 0 else
                     f"waits while word == {val}",
        })
    return verdicts


def sha256(path):
    try:
        return subprocess.run(["sha256sum", path], capture_output=True, text=True,
                              timeout=30).stdout.split()[0]
    except (OSError, subprocess.SubprocessError, IndexError):
        return None


def environment():
    mounted = {t: sha256(t) for t in MOUNT_TARGETS if os.path.exists(t)}
    meminfo = {}
    for line in (read("/proc/meminfo") or "").splitlines():
        key, _, rest = line.partition(":")
        if key in ("MemTotal", "MemFree", "MemAvailable", "SwapTotal", "SwapFree"):
            meminfo[key] = rest.strip()
    temps = {p: read(p) for p in sorted(glob.glob("/sys/class/thermal/thermal_zone*/temp"))}
    policies = {}
    for policy in sorted(glob.glob("/sys/devices/system/cpu/cpufreq/policy*")):
        policies[os.path.basename(policy)] = {
            "scaling_max_freq": read(f"{policy}/scaling_max_freq"),
            "cpuinfo_max_freq": read(f"{policy}/cpuinfo_max_freq"),
            "governor": read(f"{policy}/scaling_governor"),
        }
    return {
        "mounted_sha256": mounted,
        "meminfo": meminfo,
        "thermal": temps,
        "cpufreq": policies,
        "uptime_boottime_s": (read("/proc/uptime") or "").split()[0:1],
        "gpu_cur_freq": [read(p) for p in glob.glob("/sys/class/devfreq/*/cur_freq")],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int)
    parser.add_argument("--comm", default=COMM)
    parser.add_argument("--gap", type=float, default=6.0,
                        help="seconds between the two thread samples")
    parser.add_argument("--out", required=True, help="output directory")
    args = parser.parse_args()

    pid = args.pid or find_pid(args.comm)
    os.makedirs(args.out, exist_ok=True)

    first = sample(pid)
    time.sleep(args.gap)
    second = sample(pid)

    progressed, frozen = [], []
    for tid, info in second.items():
        was = first.get(tid)
        if not was:
            continue
        moved = (info["utime"] - was["utime"]) + (info["stime"] - was["stime"])
        row = {"tid": tid, "comm": info["comm"], "state": info["state"],
               "utime": info["utime"], "ticks_moved": moved,
               "wchan": info["wchan"], "syscall": info["syscall"]}
        (progressed if moved else frozen).append(row)

    report = {
        "pid": pid,
        "gap_s": args.gap,
        "thread_count": len(second),
        "any_thread_running": any(t["state"] == "R" for t in second.values()),
        "threads_that_moved": sorted(progressed, key=lambda r: -r["ticks_moved"]),
        "threads_that_did_not_move": sorted(frozen, key=lambda r: -r["utime"]),
        "wait_analysis": analyse_waits(pid, second),
        "environment": environment(),
    }

    with open(f"{args.out}/report.json", "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    for name, path in (("maps", f"/proc/{pid}/maps"),
                       ("environ", f"/proc/{pid}/environ"),
                       ("status", f"/proc/{pid}/status")):
        body = read(path)
        if body:
            with open(f"{args.out}/{name}.txt", "w", encoding="utf-8") as stream:
                stream.write(body.replace("\0", "\n") + "\n")
    for tid in second:
        stack = read(f"/proc/{pid}/task/{tid}/stack")
        if stack:
            with open(f"{args.out}/stack-{tid}.txt", "w", encoding="utf-8") as stream:
                stream.write(stack + "\n")
    subprocess.run(f"dmesg | tail -80 > {args.out}/dmesg-tail.txt", shell=True, timeout=60)

    print(f"pid {pid}: {len(frozen)} of {len(second)} threads did not move in {args.gap}s")
    print(f"any thread in R: {report['any_thread_running']}")
    print("An untimed wait on an unchanged word is NORMAL for an idle worker: a")
    print("parked threadpool looks identical to a deadlock at this level. What")
    print("carried the 2026-08-12 diagnosis was WHICH threads stopped -- the")
    print("highest-utime ones, which have to run for a frame to be drawn. Rows are")
    print("ordered by utime, so read the top ones and ignore the zero-time workers.")
    for row in report["wait_analysis"]:
        verdict = "unchanged" if row["still_blocked"] else "word changed"
        print(f"  tid {row['tid']:>7} [{row['comm']}] utime={row['utime']} "
              f"{row['operation']} timeout={row['timeout']} {row['shape']} -> {verdict}")
    print(f"written to {args.out}")


if __name__ == "__main__":
    main()

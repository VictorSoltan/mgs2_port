#!/usr/bin/env python3
"""What the machine is doing during a freeze, on the same clock as the game log.

The player reports freezes after a save loads and when enemies enter -- both are
"new content appears" events. That admits several causes with very different
fixes (shader/program creation, texture upload, Box86 translating newly reached
guest code, reading assets off the SD card, faulting pages back in from zram),
and guessing between them has been expensive in this project before.

So this samples the machine instead. Everything is stamped with uptime in
milliseconds, which is exactly what the presenter's `tick=` already prints, so a
stall in the game log lands on a sample here with no clock fitting at all.

Two record kinds:
  P  every --period ms: process aggregate -- CPU, faults, I/O, memory, swap
  T  every --thread-period ms: per-thread state and CPU, to say WHICH thread
     stalled and whether it stalled runnable, on disk, or asleep

usage: stall_probe.py --out FILE [--period 50] [--seconds 240] [--comm NAME]
"""
import argparse
import os
import sys
import time


def mono_ms():
    """The game's `tick=` and perf's timestamps are both CLOCK_MONOTONIC, so this
    is too. /proc/uptime is NOT interchangeable with it: uptime counts suspended
    time and monotonic does not, and this device sleeps on its own -- a run once
    came back with the two clocks 24 minutes apart."""
    return int(time.clock_gettime(time.CLOCK_MONOTONIC) * 1000)


def boot_ms():
    return int(time.clock_gettime(time.CLOCK_BOOTTIME) * 1000)


def find_pid(comm):
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        try:
            with open("/proc/%s/comm" % name) as fh:
                if fh.read().strip() == comm:
                    return int(name)
        except OSError:
            continue
    return None


def read_kv(path, keys, sep=":"):
    """meminfo is "key: value"; vmstat is "key value". Parsing vmstat with the
    colon form matched nothing and silently reported every swap counter as zero,
    which reads exactly like "no swapping happened"."""
    out = {}
    try:
        with open(path) as fh:
            for line in fh:
                if sep:
                    k, _, v = line.partition(sep)
                else:
                    k, _, v = line.partition(" ")
                k = k.strip()
                if k in keys:
                    out[k] = int(v.split()[0])
    except OSError:
        pass
    return out


def slurp(path, default=""):
    try:
        with open(path) as fh:
            return fh.read().strip()
    except OSError:
        return default


def proc_stat_fields(raw):
    """(state, minflt, majflt, utime+stime) from a /proc/.../stat body.

    comm can contain spaces and parentheses, so the split has to be on the LAST
    ')'. After that rest[0] is field 3, so field N is rest[N-3]:
    minflt 10 -> 7, majflt 12 -> 9, utime 14 -> 11, stime 15 -> 12.
    Getting this wrong is quiet rather than loud: rest[6] is the flags word,
    which is a large constant, and rest[8] is cminflt, which moves only when a
    child is reaped -- both look like plausible fault counts and neither is one.
    """
    rest = raw.rpartition(")")[2].split()
    return rest[0], int(rest[7]), int(rest[9]), int(rest[11]) + int(rest[12])


def proc_stat(pid):
    with open("/proc/%d/stat" % pid) as fh:
        return proc_stat_fields(fh.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--comm", default="mgs2_sse_rg353v")
    ap.add_argument("--period", type=int, default=50)
    ap.add_argument("--thread-period", type=int, default=100)
    ap.add_argument("--stack-period", type=int, default=500)
    ap.add_argument("--seconds", type=int, default=240)
    ap.add_argument("--wait", type=int, default=180, help="seconds to wait for the process")
    a = ap.parse_args()

    deadline = time.monotonic() + a.wait
    pid = None
    while pid is None and time.monotonic() < deadline:
        pid = find_pid(a.comm)
        if pid is None:
            time.sleep(0.5)
    if pid is None:
        sys.stderr.write("no process named %s within %ds\n" % (a.comm, a.wait))
        return 2

    have_io = os.path.exists("/proc/%d/io" % pid)
    fh = open(a.out, "w", 1)
    fh.write("# pid=%d comm=%s period=%d clock=CLOCK_MONOTONIC_ms\n"
             % (pid, a.comm, a.period))
    fh.write("# per-process io accounting: %s\n"
             % ("available" if have_io else
                "ABSENT (no CONFIG_TASK_IO_ACCOUNTING) -- io columns are -1, not zero"))
    fh.write("# B %d boot_ms at start, for detecting a suspend mid-run\n" % boot_ms())
    fh.write("# P t_ms state minflt majflt cputicks rchar read_bytes wchar "
             "write_bytes pswpin pswpout pgmajfault memavail_kb swapfree_kb nthreads\n")
    fh.write("# T t_ms tid comm state cputicks minflt majflt wchan syscall\n")
    fh.write("# K t_ms tid comm kernel_stack (';'-joined)\n")

    vm_keys = {"pswpin", "pswpout", "pgmajfault", "pgpgin"}
    mem_keys = {"MemAvailable", "SwapFree"}
    io_keys = {"rchar", "wchar", "read_bytes", "write_bytes"}

    end = time.monotonic() + a.seconds
    next_thread = next_stack = 0.0
    period = a.period / 1000.0
    while time.monotonic() < end:
        t0 = time.monotonic()
        try:
            t = mono_ms()
            state, minflt, majflt, cpu = proc_stat(pid)
            io = read_kv("/proc/%d/io" % pid, io_keys) if have_io else {}
            miss = 0 if have_io else -1
            vm = read_kv("/proc/vmstat", vm_keys, sep=None)
            mem = read_kv("/proc/meminfo", mem_keys)
            tids = os.listdir("/proc/%d/task" % pid)
            fh.write("P %d %s %d %d %d %d %d %d %d %d %d %d %d %d %d\n" % (
                t, state, minflt, majflt, cpu,
                io.get("rchar", miss), io.get("read_bytes", miss),
                io.get("wchar", miss), io.get("write_bytes", miss),
                vm.get("pswpin", 0), vm.get("pswpout", 0), vm.get("pgmajfault", 0),
                mem.get("MemAvailable", 0), mem.get("SwapFree", 0), len(tids)))

            want_stack = t0 >= next_stack
            if want_stack:
                next_stack = t0 + a.stack_period / 1000.0
            if t0 >= next_thread:
                next_thread = t0 + a.thread_period / 1000.0
                for tid in tids:
                    base = "/proc/%d/task/%s/" % (pid, tid)
                    try:
                        with open(base + "stat") as th:
                            raw = th.read()
                        name = raw.partition("(")[2].rpartition(")")[0]
                        st, tmin, tmaj, tcpu = proc_stat_fields(raw)
                    except (OSError, IndexError, ValueError):
                        continue
                    # A stall that shows no CPU anywhere is a thread waiting, and
                    # cycles-based perf is blind to it: there are no samples while
                    # a thread is off-CPU. wchan and syscall name the wait itself.
                    wchan = slurp(base + "wchan", "?").replace(" ", "_") or "?"
                    sc = slurp(base + "syscall", "?").split(" ")[0] or "?"
                    fh.write("T %d %s %s %s %d %d %d %s %s\n"
                             % (t, tid, name, st, tcpu, tmin, tmaj, wchan, sc))
                    if want_stack and st != "R":
                        stk = slurp(base + "stack", "")
                        if stk:
                            frames = [ln.partition("] ")[2].strip()
                                      for ln in stk.splitlines() if "] " in ln]
                            if frames:
                                fh.write("K %d %s %s %s\n"
                                         % (t, tid, name, ";".join(frames[:12])))
        except (OSError, IndexError, ValueError):
            if not os.path.exists("/proc/%d" % pid):
                fh.write("# process gone at %d\n" % mono_ms())
                break
        slack = period - (time.monotonic() - t0)
        if slack > 0:
            time.sleep(slack)
    fh.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

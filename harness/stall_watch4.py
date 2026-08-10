#!/usr/bin/env python3
"""Low-overhead, trigger-only MGS2 stall capture for RG353VS.

Normal operation reads one /proc stat file every 100 ms.  If the game main
thread accumulates no CPU ticks for the configured threshold, the watcher takes
one short burst of syscall/wchan/stack/sched snapshots for main, wined3d_cs and
wineserver.  File-descriptor maps are saved once at startup, not polled.
"""

import argparse
import datetime
import os
import struct
import time


GAME_COMM = "mgs2_sse_rg353v"


def read(path, default=""):
    try:
        with open(path, "r", errors="replace") as handle:
            return handle.read().strip()
    except OSError as exc:
        return "%s: %s" % (default, exc)


def find_process(comm):
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        if read("/proc/%s/comm" % name) == comm:
            return int(name)
    return None


def find_thread(pid, comm):
    task_dir = "/proc/%d/task" % pid
    try:
        tids = os.listdir(task_dir)
    except OSError:
        return None
    for tid in tids:
        if read("%s/%s/comm" % (task_dir, tid)) == comm:
            return int(tid)
    return None


def cpu_ticks(pid):
    stat = read("/proc/%d/stat" % pid)
    try:
        fields = stat[stat.rfind(")") + 2:].split()
        return int(fields[11]) + int(fields[12])
    except (ValueError, IndexError):
        return None


def fd_map(pid):
    result = []
    path = "/proc/%d/fd" % pid
    try:
        names = sorted(os.listdir(path), key=lambda value: int(value))
    except OSError as exc:
        return ["fd map unavailable: %s" % exc]
    for name in names:
        try:
            target = os.readlink("%s/%s" % (path, name))
        except OSError as exc:
            target = "<%s>" % exc
        result.append("%s -> %s" % (name, target))
    return result


def ntsync_wait_details(pid, syscall_text):
    """Decode a compat ioctl(NTSYNC_IOC_WAIT_*, args) at trigger time."""
    try:
        fields = syscall_text.split()
        if int(fields[0], 0) != 54:  # compat ioctl
            return "not an ioctl"
        request = int(fields[2], 0)
        if request not in (0xC0284E82, 0xC0284E83):
            return "ioctl request=%#x is not NTSYNC_IOC_WAIT" % request
        args_ptr = int(fields[3], 0)
        with open("/proc/%d/mem" % pid, "rb", buffering=0) as handle:
            handle.seek(args_ptr)
            raw = handle.read(40)
            timeout, objs_ptr, count, index, flags, owner, alert, pad = \
                    struct.unpack("<QQIIIIII", raw)
            if count > 64:
                return "invalid ntsync count=%u" % count
            handle.seek(objs_ptr)
            raw_objs = handle.read(count * 4)
            objects = struct.unpack("<%dI" % count, raw_objs) if count else ()
        mapped = []
        for fd in objects:
            try:
                target = os.readlink("/proc/%d/fd/%d" % (pid, fd))
            except OSError as exc:
                target = "<%s>" % exc
            mapped.append("%d:%s" % (fd, target))
        if timeout == 0xffffffffffffffff:
            timeout_text = "infinite"
        elif flags & 0x1:
            deadline = timeout / 1000000000.0
            remaining = deadline - time.time()
            timeout_text = "%s remaining=%.3fs" % (
                    datetime.datetime.fromtimestamp(deadline,
                    datetime.timezone.utc).isoformat(), remaining)
        else:
            timeout_text = "monotonic_ns=%u remaining=%.3fs" % (
                    timeout, timeout / 1000000000.0 - time.monotonic())
        return ("request=%s timeout=%#x (%s) objs=%#x count=%u index=%u flags=%#x "
                "owner=%u alert=%u objects=[%s]" %
                ("WAIT_ANY" if request == 0xC0284E82 else "WAIT_ALL",
                timeout, timeout_text, objs_ptr, count, index, flags, owner, alert,
                ", ".join(mapped)))
    except (OSError, ValueError, IndexError, struct.error) as exc:
        return "decode unavailable: %s" % exc


def snapshot_target(label, pid, tid):
    base = "/proc/%d/task/%d" % (pid, tid)
    syscall_text = read("%s/syscall" % base, "unavailable")
    lines = ["TARGET %s pid=%d tid=%d comm=%s" %
            (label, pid, tid, read("%s/comm" % base, "?"))]
    lines.append("--- syscall")
    lines.append(syscall_text)
    if label == "main":
        lines.append("--- ntsync wait decode")
        lines.append(ntsync_wait_details(pid, syscall_text))
    for name in ("wchan", "stack", "sched", "status"):
        lines.append("--- %s" % name)
        lines.append(read("%s/%s" % (base, name), "unavailable"))
    return "\n".join(lines)


def capture(output, game_pid, cs_tid, server_pid, game_fds, server_fds,
        stalled_ms, ticks):
    targets = [("main", game_pid, game_pid)]
    if cs_tid:
        targets.append(("wined3d_cs", game_pid, cs_tid))
    if server_pid:
        targets.append(("wineserver", server_pid, server_pid))

    with open(output, "w") as handle:
        handle.write("MGS2 STALLWATCH4 trigger wall=%.6f stalled_ms=%.1f main_ticks=%s\n" %
                (time.time(), stalled_ms, ticks))
        handle.write("cap=%s temp=%s\n" % (
                read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq", "?"),
                read("/sys/class/thermal/thermal_zone0/temp", "?")))
        handle.write("\nGAME FD MAP (captured before polling)\n")
        handle.write("\n".join(game_fds) + "\n")
        handle.write("\nGAME FD MAP (captured at trigger)\n")
        handle.write("\n".join(fd_map(game_pid)) + "\n")
        if server_pid:
            handle.write("\nWINESERVER FD MAP (captured before polling)\n")
            handle.write("\n".join(server_fds) + "\n")
            handle.write("\nWINESERVER FD MAP (captured at trigger)\n")
            handle.write("\n".join(fd_map(server_pid)) + "\n")
        for burst in range(3):
            handle.write("\nSNAPSHOT %d monotonic=%.6f\n" % (burst, time.monotonic()))
            for label, pid, tid in targets:
                handle.write(snapshot_target(label, pid, tid) + "\n")
            handle.flush()
            if burst != 2:
                time.sleep(0.05)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=300.0)
    parser.add_argument("--interval-ms", type=float, default=100.0)
    parser.add_argument("--trigger-ms", type=float, default=500.0)
    parser.add_argument("--wait-game", type=float, default=0.0,
            help="seconds to wait for the game process before giving up")
    parser.add_argument("--require-cs", action="store_true",
            help="arm only after the wined3d_cs thread exists")
    parser.add_argument("--wait-cs", type=float, default=60.0,
            help="seconds to wait for wined3d_cs when --require-cs is used")
    parser.add_argument("--output", default="/tmp/mgs2-stall-watch4-capture.log")
    args = parser.parse_args()

    game_pid = find_process(GAME_COMM)
    wait_deadline = time.monotonic() + args.wait_game
    while not game_pid and time.monotonic() < wait_deadline:
        # A full /proc process-name scan is relatively expensive on this A55.
        # Before the game exists, one scan per second is early enough to catch
        # its startup stalls without becoming part of the workload itself.
        time.sleep(1.0)
        game_pid = find_process(GAME_COMM)
    if not game_pid:
        raise SystemExit("game not running")
    cs_tid = find_thread(game_pid, "wined3d_cs")
    cs_deadline = time.monotonic() + args.wait_cs
    while args.require_cs and cs_tid is None and time.monotonic() < cs_deadline:
        time.sleep(0.5)
        if find_process(GAME_COMM) != game_pid:
            raise SystemExit("game exited before wined3d_cs appeared")
        cs_tid = find_thread(game_pid, "wined3d_cs")
    if args.require_cs and cs_tid is None:
        raise SystemExit("wined3d_cs did not appear before wait timeout")
    server_pid = find_process("wineserver")
    game_fds = fd_map(game_pid)
    server_fds = fd_map(server_pid) if server_pid else []
    start = time.monotonic()
    last_progress = start
    last_ticks = cpu_ticks(game_pid)
    interval = max(args.interval_ms, 50.0) / 1000.0
    print("watching game=%d cs=%s wineserver=%s interval=%.3fs trigger=%.3fs" %
            (game_pid, cs_tid, server_pid, interval, args.trigger_ms / 1000.0), flush=True)

    while time.monotonic() - start < args.duration:
        time.sleep(interval)
        now = time.monotonic()
        ticks = cpu_ticks(game_pid)
        if ticks is None:
            raise SystemExit("game exited before trigger")
        if ticks != last_ticks:
            last_ticks = ticks
            last_progress = now
            continue
        stalled_ms = (now - last_progress) * 1000.0
        if stalled_ms >= args.trigger_ms:
            if cs_tid is None:
                cs_tid = find_thread(game_pid, "wined3d_cs")
            capture(args.output, game_pid, cs_tid, server_pid,
                    game_fds, server_fds, stalled_ms, ticks)
            print("triggered after %.1f ms -> %s" % (stalled_ms, args.output), flush=True)
            return 0

    print("no stall detected", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

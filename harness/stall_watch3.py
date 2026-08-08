#!/usr/bin/env python3
"""Low-impact classifier for MGS2 multi-second frame stalls.

Unlike stall_watch2.py this never reads wchan and never walks every thread. It
samples only the game's main thread, wined3d_cs (if present), and wineserver once
every 500 ms. When the presenter's existing "MGS2 STALL" line arrives, it reports
the preceding CPU, disk, temperature, and CPU-cap window. A two-second gap in
the active batcher's once-per-second telemetry is reported too, catching short
stalls that can fall below the presenter's 500 ms threshold.

Run on the device only for a reproduction run. It is deliberately diagnostic,
not part of the production launcher.
"""

import glob
import os
import sys
import time
from collections import deque

GAME_COMM = "mgs2_sse_rg353v"
POLL_SECONDS = 0.5
HISTORY_SECONDS = 15


def read(path, default=""):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return default


def find_pid(comm):
    for path in glob.glob("/proc/[0-9]*"):
        if read(path + "/comm") == comm:
            return path.rsplit("/", 1)[-1]
    return None


def ticks(stat):
    if not stat:
        return None
    fields = stat[stat.rfind(")") + 2:].split()
    try:
        return int(fields[11]) + int(fields[12])
    except (IndexError, ValueError):
        return None


def game_threads(pid):
    result = {}
    for tid_path in glob.glob("/proc/%s/task/*" % pid):
        tid = tid_path.rsplit("/", 1)[-1]
        name = read(tid_path + "/comm")
        if name not in (GAME_COMM, "wined3d_cs"):
            continue
        result[name] = ticks(read(tid_path + "/stat"))
    return result


def disk_read_sectors():
    try:
        return int(read("/sys/block/mmcblk0/stat").split()[2])
    except (IndexError, ValueError):
        return 0


def sample(game_pid, server_pid):
    return {
        "time": time.time(),
        "threads": game_threads(game_pid),
        "wineserver": ticks(read("/proc/%s/stat" % server_pid)) if server_pid else None,
        "disk": disk_read_sectors(),
        "cap": read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq", "?"),
        "temp": read("/sys/class/thermal/thermal_zone0/temp", "?"),
    }


def delta(first, last, key):
    a, b = first.get(key), last.get(key)
    return "-" if a is None or b is None else str(b - a)


def report(history, line):
    if len(history) < 2:
        return
    first, last = history[0], history[-1]
    print("\n=== %s" % line.strip())
    print("window=%.1fs disk_read=%dKB cap=%s->%s temp=%s->%s" %
          (last["time"] - first["time"], (last["disk"] - first["disk"]) // 2,
           first["cap"], last["cap"], first["temp"], last["temp"]))
    for name in (GAME_COMM, "wined3d_cs"):
        print("%-18s cpu_ticks=%s" %
              (name, delta({"v": first["threads"].get(name)}, {"v": last["threads"].get(name)}, "v")))
    print("%-18s cpu_ticks=%s" %
          ("wineserver", delta({"v": first["wineserver"]}, {"v": last["wineserver"]}, "v")))
    print("Interpretation: near-zero disk and CPU during a stall supports a Wine sync wait; "
          "rising disk supports streaming; rising CPU identifies the busy side.")


def main():
    if len(sys.argv) < 2:
        print("usage: stall_watch3.py <game-log> [seconds]", file=sys.stderr)
        return 2
    log_path = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    game_pid = find_pid(GAME_COMM)
    if not game_pid:
        print("game not running", file=sys.stderr)
        return 1
    try:
        log = open(log_path, "r", errors="ignore")
    except OSError as exc:
        print(exc, file=sys.stderr)
        return 1
    log.seek(0, os.SEEK_END)
    history = deque(maxlen=int(HISTORY_SECONDS / POLL_SECONDS))
    deadline = time.time() + duration
    last_batch_line = None
    gap_reported = False
    print("watching game=%s, interval=%.1fs, no wchan reads" % (game_pid, POLL_SECONDS), flush=True)
    while time.time() < deadline:
        server_pid = find_pid("wineserver")
        history.append(sample(game_pid, server_pid))
        for line in log.readlines():
            if "MGS2BATCH:" in line and "switched to" not in line:
                last_batch_line = time.time()
                gap_reported = False
            if "MGS2 STALL" in line:
                report(history, line)
        if last_batch_line and not gap_reported:
            gap = time.time() - last_batch_line
            if gap >= 2.0:
                report(history, "MGS2 BATCH-GAP %.1f ms" % (gap * 1000.0))
                gap_reported = True
        time.sleep(POLL_SECONDS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

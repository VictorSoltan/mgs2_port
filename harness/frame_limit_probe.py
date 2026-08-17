#!/usr/bin/env python3
"""Decide what actually limits the reinforcement frame: CPU, GPU, or thermal cap.

Every renderer conclusion in this project has been normalised against an assumed
fixed 1,992,000 Hz CPU cap.  On 2026-08-14 the launcher's own thermal ladder was
observed holding the cap between 1,104,000 and 1,608,000 at ~82 C during a live
fight, which makes that assumption unverified for every earlier profile.  At the
same time a cycle-weighted re-analysis put wined3d_cs at 0.65 of a core and the
whole process at 1.53 of four cores, i.e. nothing is CPU-saturated.  Those two
facts are not compatible with a single explanation, and they call for different
work, so this probe separates them before anything is written.

It is an external 1 Hz sampler.  It reads a bounded set of files -- one cpufreq
policy, two thermal zones, one GPU devfreq node, and utime/stime for a fixed
list of threads chosen once at start -- and writes to tmpfs.  It never reads
`wchan`, never attaches to the process, and produces no output from any Wine,
mixer or driver thread.  Both of those mistakes cost this project days; see rule
2 in AGENTS.md.

Usage on the device, started only after the player reports reinforcements:

    python3 /tmp/frame_limit_probe.py --seconds 45 --output /tmp/framelimit

Then copy /tmp/framelimit.csv and /tmp/framelimit.json off the console.
"""

import argparse
import json
import os
import pathlib
import re
import sys
import time

CPU_POLICY = "/sys/devices/system/cpu/cpufreq/policy0"
GPU_DEVFREQ = "/sys/class/devfreq/fde60000.gpu"
ZONES = {"cpu": "/sys/class/thermal/thermal_zone0/temp",
         "gpu": "/sys/class/thermal/thermal_zone1/temp"}
STATS_RE = re.compile(
    r"tick=(\d+) (\d+) frames in (\d+) ms = ([0-9.]+) fps"
    r"(?: \| readback ([0-9.]+) ms/f)?(?: \| copy ([0-9.]+) ms/f)?")
# Threads worth following. Everything else is folded into "other".
TRACKED = 8


def read_int(path, default=None):
    try:
        with open(path, encoding="ascii") as stream:
            return int(stream.read().strip())
    except (OSError, ValueError):
        return default


def read_text(path, default=""):
    try:
        with open(path, encoding="ascii", errors="replace") as stream:
            return stream.read().strip()
    except OSError:
        return default


def find_pid(comm):
    matches = [int(n) for n in os.listdir("/proc") if n.isdigit()
               and read_text(f"/proc/{n}/comm") == comm]
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one {comm!r} process, found {matches}")
    return matches[0]


def thread_cpu(pid, tid):
    """Returns (comm, utime+stime) in clock ticks, or None if the thread is gone."""
    raw = read_text(f"/proc/{pid}/task/{tid}/stat")
    if not raw:
        return None
    # comm is parenthesised and may contain spaces; split on the last ')'.
    close = raw.rfind(")")
    open_paren = raw.find("(")
    if close < 0 or open_paren < 0:
        return None
    comm = raw[open_paren + 1:close]
    fields = raw[close + 2:].split()
    try:
        # After comm and state, field indices 11 and 12 are utime and stime.
        return comm, int(fields[11]) + int(fields[12])
    except (IndexError, ValueError):
        return None


def gpu_trans_stat():
    """Cumulative ms spent at each GPU frequency, from devfreq trans_stat."""
    out = {}
    raw = read_text(f"{GPU_DEVFREQ}/trans_stat")
    for line in raw.splitlines():
        # rows look like: "   *300000000:      0    12    0   1234"
        line = line.strip().lstrip("*").strip()
        parts = line.split(":")
        if len(parts) != 2 or not parts[0].strip().isdigit():
            continue
        tail = parts[1].split()
        if not tail:
            continue
        try:
            out[int(parts[0].strip())] = int(tail[-1])
        except ValueError:
            continue
    return out


def latest_frame_stats(log_path):
    """Last present-stats line in the game log, if the launcher is emitting them."""
    if not log_path:
        return None
    try:
        data = pathlib.Path(log_path).read_text(errors="replace")
    except OSError:
        return None
    last = None
    for match in STATS_RE.finditer(data):
        last = match
    if not last:
        return None
    return {
        "tick": int(last.group(1)),
        "frames": int(last.group(2)),
        "ms": int(last.group(3)),
        "fps": float(last.group(4)),
        "readback_ms": float(last.group(5)) if last.group(5) else None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=45)
    parser.add_argument("--comm", default="mgs2_sse_rg353v")
    parser.add_argument("--pid", type=int)
    parser.add_argument("--game-log", default="/tmp/autoload-game.log")
    parser.add_argument("--output", default="/tmp/framelimit")
    args = parser.parse_args()

    pid = args.pid or find_pid(args.comm)
    hz = os.sysconf("SC_CLK_TCK")

    # Choose the tracked threads once, by cumulative CPU so far, and never
    # re-enumerate: a growing scan is exactly the sampler that perturbed the
    # thing it was measuring last time.
    tids = sorted(os.listdir(f"/proc/{pid}/task"), key=int)
    seed = []
    for tid in tids:
        got = thread_cpu(pid, tid)
        if got:
            seed.append((got[1], tid, got[0]))
    seed.sort(reverse=True)
    tracked = [(tid, comm) for _cpu, tid, comm in seed[:TRACKED]]
    print(f"pid {pid}, {len(tids)} threads, following {len(tracked)}: "
          + ", ".join(f"{c}:{t}" for t, c in tracked), file=sys.stderr)

    rows = []
    prev = {tid: thread_cpu(pid, tid) for tid, _c in tracked}
    prev_trans = gpu_trans_stat()
    start_trans = dict(prev_trans)
    prev_wall = time.monotonic()
    t0 = prev_wall

    while time.monotonic() - t0 < args.seconds:
        time.sleep(1.0)
        now = time.monotonic()
        dt = now - prev_wall
        prev_wall = now

        row = {
            "t": round(now - t0, 3),
            "cpu_cur_khz": read_int(f"{CPU_POLICY}/scaling_cur_freq"),
            "cpu_max_khz": read_int(f"{CPU_POLICY}/scaling_max_freq"),
            "cpu_temp_mc": read_int(ZONES["cpu"]),
            "gpu_temp_mc": read_int(ZONES["gpu"]),
            "gpu_cur_hz": read_int(f"{GPU_DEVFREQ}/cur_freq"),
            "gpu_target_hz": read_int(f"{GPU_DEVFREQ}/target_freq"),
            "threads": {},
        }
        for tid, comm in tracked:
            got = thread_cpu(pid, tid)
            before = prev.get(tid)
            if got and before:
                # Fraction of one core this thread executed over the interval.
                row["threads"][f"{comm}:{tid}"] = round(
                    (got[1] - before[1]) / hz / dt, 4)
            prev[tid] = got
        frame = latest_frame_stats(args.game_log)
        if frame:
            row["fps"] = frame["fps"]
            row["readback_ms"] = frame["readback_ms"]
        rows.append(row)

    end_trans = gpu_trans_stat()
    residency = {}
    total_ms = 0
    for freq, ms in end_trans.items():
        delta = ms - start_trans.get(freq, 0)
        if delta > 0:
            residency[freq] = delta
            total_ms += delta

    def mean(key):
        vals = [r[key] for r in rows if r.get(key) is not None]
        return round(sum(vals) / len(vals), 2) if vals else None

    thread_names = [f"{c}:{t}" for t, c in tracked]
    occupancy = {}
    for name in thread_names:
        vals = [r["threads"].get(name) for r in rows if r["threads"].get(name) is not None]
        if vals:
            occupancy[name] = {"mean_core": round(sum(vals) / len(vals), 3),
                               "peak_core": round(max(vals), 3)}
    busiest = max(occupancy.values(), key=lambda v: v["mean_core"])["mean_core"] if occupancy else 0.0
    total_core = round(sum(v["mean_core"] for v in occupancy.values()), 3)

    gpu_res = {str(f): {"ms": ms, "share": round(ms / total_ms, 4)}
               for f, ms in sorted(residency.items())} if total_ms else {}
    top_gpu = max(residency, key=residency.get) if residency else None
    gpu_max = read_int(f"{GPU_DEVFREQ}/max_freq")

    summary = {
        "pid": pid,
        "seconds": args.seconds,
        "samples": len(rows),
        "cpu_cur_khz_mean": mean("cpu_cur_khz"),
        "cpu_max_khz_mean": mean("cpu_max_khz"),
        "cpu_max_khz_min": min((r["cpu_max_khz"] for r in rows if r["cpu_max_khz"]), default=None),
        "cpu_temp_c_mean": round(mean("cpu_temp_mc") / 1000, 2) if mean("cpu_temp_mc") else None,
        "gpu_temp_c_mean": round(mean("gpu_temp_mc") / 1000, 2) if mean("gpu_temp_mc") else None,
        "fps_mean": mean("fps"),
        "readback_ms_mean": mean("readback_ms"),
        "thread_occupancy_cores": occupancy,
        "busiest_thread_cores": busiest,
        "total_cores_busy": total_core,
        "gpu_freq_residency": gpu_res,
        "gpu_freq_max_hz": gpu_max,
        "gpu_time_at_max_share": gpu_res.get(str(gpu_max), {}).get("share") if gpu_max else None,
        "gpu_top_freq_hz": top_gpu,
    }

    # The decision rule, fixed before the numbers are read.
    verdicts = []
    if summary["cpu_max_khz_min"] and summary["cpu_max_khz_min"] < 1992000:
        verdicts.append(
            f"THERMAL: the CPU cap fell to {summary['cpu_max_khz_min']} kHz during the "
            f"fight, so it was NOT pinned at 1992000. Every per-core figure derived "
            f"from an assumed 1992 MHz, including the 0.65-core reading, is invalid "
            f"and must be recomputed at the measured clock.")
    if busiest >= 0.90:
        verdicts.append(
            f"CPU-BOUND: the busiest thread ran {busiest:.2f} of a core. A native ARM "
            f"bridge for the hottest WineD3D path has a real target.")
    elif busiest <= 0.75 and summary.get("gpu_time_at_max_share", 0) \
            and summary["gpu_time_at_max_share"] > 0.5:
        verdicts.append(
            f"GPU-BOUND: no thread exceeded {busiest:.2f} of a core while the GPU sat "
            f"at its maximum frequency {summary['gpu_time_at_max_share']*100:.0f}% of "
            f"the time. Removing CPU cycles will not raise the frame rate.")
    elif busiest <= 0.75:
        verdicts.append(
            f"NEITHER: the busiest thread ran {busiest:.2f} of a core and the GPU did "
            f"not sit at its maximum. The frame is lost to waiting or serialisation, "
            f"not to raw CPU or GPU throughput. Do not write any optimisation yet.")
    summary["verdict"] = verdicts or ["inconclusive; see the rows"]

    out = pathlib.Path(args.output)
    with out.with_suffix(".json").open("w", encoding="ascii") as stream:
        json.dump({"summary": summary, "rows": rows}, stream, indent=2, sort_keys=True)
    with out.with_suffix(".csv").open("w", encoding="ascii") as stream:
        cols = ["t", "cpu_cur_khz", "cpu_max_khz", "cpu_temp_mc", "gpu_temp_mc",
                "gpu_cur_hz", "gpu_target_hz", "fps", "readback_ms"] + thread_names
        stream.write(",".join(cols) + "\n")
        for r in rows:
            vals = [r.get(c, "") for c in cols[:9]] + \
                   [r["threads"].get(n, "") for n in thread_names]
            stream.write(",".join("" if v is None else str(v) for v in vals) + "\n")

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

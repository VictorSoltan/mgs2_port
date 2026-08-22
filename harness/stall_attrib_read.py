#!/usr/bin/env python3
"""Name the cause of each freeze by lining the game log up against stall_probe.py.

Both sides stamp uptime in milliseconds -- the presenter already prints `tick=`
and the probe records the same clock -- so the windows join exactly, with no
clock fitting and no guessing.

The first question is not which subsystem but WHERE the stall lives, and one
column answers it: the probe's own sampling gap. The probe is a separate process
doing nothing but reading procfs every 50 ms. If it kept sampling smoothly while
the game stood still, nothing global stopped and the freeze is work inside the
game's own threads. If the probe stalled too, the machine stalled -- memory
reclaim, zram, or the SD card -- and no amount of GL-side work will fix it.

usage: stall_attrib_read.py <game log> <probe csv> [--worst-ms 100]
"""
import argparse
import re
import sys

STATS = re.compile(r"tick=(\d+)\s+(\d+) frames in (\d+) ms")
WORST = re.compile(r"frame time: worst (\d+) ms \| over 50/100/200/500 ms: "
                   r"(\d+)/(\d+)/(\d+)/(\d+)")
CLK = 100.0   # USER_HZ


def load_probe(path):
    p, t = [], []
    for line in open(path, errors="replace"):
        f = line.split()
        if not f or f[0] == "#":
            continue
        try:
            if f[0] == "P":
                p.append(dict(t=int(f[1]), state=f[2], minflt=int(f[3]),
                              majflt=int(f[4]), cpu=int(f[5]), rchar=int(f[6]),
                              rbytes=int(f[7]), wchar=int(f[8]), wbytes=int(f[9]),
                              pswpin=int(f[10]), pswpout=int(f[11]),
                              pgmajf=int(f[12]), memav=int(f[13]),
                              swapfree=int(f[14]), nthr=int(f[15])))
            elif f[0] == "T":
                t.append((int(f[1]), f[2], f[3], f[4], int(f[5])))
        except (ValueError, IndexError):
            continue
    return p, t


def windows(path):
    """(tick_end, span_ms, frames, worst_ms, buckets) per 60-frame report."""
    out, pend = [], None
    for line in open(path, errors="replace"):
        m = STATS.search(line)
        if m:
            pend = (int(m.group(1)), int(m.group(3)), int(m.group(2)))
            continue
        m = WORST.search(line)
        if m and pend:
            out.append(pend + (int(m.group(1)),
                               tuple(int(m.group(i)) for i in range(2, 6))))
            pend = None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("probe")
    ap.add_argument("--worst-ms", type=int, default=100)
    ap.add_argument("--offset-ms", type=int, default=0,
                    help="added to the game log's tick to reach the probe's clock. "
                         "The game stamps CLOCK_MONOTONIC; /proc/uptime is BOOTTIME, "
                         "and the two diverge by however long the device has slept.")
    a = ap.parse_args()

    P, T = load_probe(a.probe)
    W = [(w[0] + a.offset_ms,) + tuple(w[1:]) for w in windows(a.log)]
    if not P:
        sys.exit("probe file has no samples")
    print("probe %d samples, %.1f s covered (%d..%d)"
          % (len(P), (P[-1]["t"] - P[0]["t"]) / 1000.0, P[0]["t"], P[-1]["t"]))
    print("game log %d reporting windows" % len(W))

    gaps = [P[i + 1]["t"] - P[i]["t"] for i in range(len(P) - 1)]
    gaps.sort()
    print("probe sampling gap: p50 %d ms, p99 %d ms, max %d ms"
          % (gaps[len(gaps) // 2], gaps[int(len(gaps) * 0.99)], gaps[-1]))

    bad = [w for w in W if w[3] >= a.worst_ms and P[0]["t"] <= w[0] <= P[-1]["t"]]
    print("\n%d windows with a frame at or over %d ms, inside the probe's coverage\n"
          % (len(bad), a.worst_ms))
    if not bad:
        return

    hdr = ("  worst  frames    CPU%%  probegap   majflt   swapin  read_KB"
           "  memavail  busiest thread")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for tick, span, frames, worst, buckets in bad:
        lo, hi = tick - span, tick
        s = [x for x in P if lo <= x["t"] <= hi]
        if len(s) < 2:
            print("  %5d  %6d   (no probe samples in window)" % (worst, frames))
            continue
        wall = s[-1]["t"] - s[0]["t"]
        g = max(s[i + 1]["t"] - s[i]["t"] for i in range(len(s) - 1))
        cpu_ms = (s[-1]["cpu"] - s[0]["cpu"]) * 1000.0 / CLK
        tt = [x for x in T if lo <= x[0] <= hi]
        busiest = ""
        if tt:
            per = {}
            for _, tid, nm, st, c in tt:
                per.setdefault((tid, nm), []).append(c)
            ranked = sorted(((v[-1] - v[0], k) for k, v in per.items()), reverse=True)
            d, (tid, nm) = ranked[0]
            busiest = "%s %.0f ms" % (nm, d * 1000.0 / CLK)
        print("  %5d  %6d  %5.0f%%  %6d ms  %7d  %7d  %7d  %8d  %s"
              % (worst, frames,
                 100.0 * cpu_ms / wall if wall else 0, g,
                 s[-1]["majflt"] - s[0]["majflt"],
                 s[-1]["pswpin"] - s[0]["pswpin"],
                 (s[-1]["rbytes"] - s[0]["rbytes"]) // 1024,
                 s[-1]["memav"], busiest))

    print("\nreading this table")
    print("  probegap large   -> the probe stalled too: the machine stalled, not the game")
    print("  probegap ~50 ms  -> only the game stopped; the freeze is its own work")
    print("  CPU% near 100    -> a thread was running flat out (compile, translate, copy)")
    print("  CPU% low + gap   -> it was blocked, not computing: I/O, fault, or a lock")
    print("  majflt/swapin    -> pages came back from zram or disk during the window")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Slice a perf profile to the freeze windows and say what is EXTRA in them.

A flat profile of a whole run cannot answer this: the expensive things during a
freeze are mostly the same things that are expensive the rest of the time, only
more so. What names a cause is the difference between the freeze windows and the
calm ones, in cycles per second of wall clock.

Both sides are CLOCK_MONOTONIC -- perf records with -k mono and the presenter
prints `tick=` from the same clock -- so the windows join with no fitting.

usage: freeze_profile_read.py <game log> <perf.script> [--worst-ms 300]
"""
import argparse
import re
from collections import defaultdict

STATS = re.compile(r"tick=(\d+)\s+(\d+) frames in (\d+) ms")
WORST = re.compile(r"frame time: worst (\d+) ms \| over 50/100/200/500 ms: "
                   r"(\d+)/(\d+)/(\d+)/(\d+)")
SAMPLE = re.compile(
    r"^\s*(.+?)\s+(\d+)\s+(\d+\.\d+):\s+(\d+)\s+(\S+):\s+([0-9a-f]+)\s+(.*)\s+\((\S+)\)\s*$")


def classify(dso):
    if "perf-" in dso and dso.endswith(".map"):
        return "[JIT] guest code"
    if dso.endswith("/box86") or dso == "box86":
        return "box86 native"
    if "libmali" in dso:
        return "libmali (driver)"
    if "kallsyms" in dso or dso.startswith("["):
        return "kernel"
    return dso.rsplit("/", 1)[-1]


def windows(path):
    out, pend = [], None
    for line in open(path, errors="replace"):
        m = STATS.search(line)
        if m:
            pend = (int(m.group(1)), int(m.group(3)))
            continue
        m = WORST.search(line)
        if m and pend:
            out.append((pend[0], pend[1], int(m.group(1))))
            pend = None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("script")
    ap.add_argument("--worst-ms", type=int, default=300)
    ap.add_argument("--top", type=int, default=12)
    a = ap.parse_args()

    S = []
    bad_lines = 0
    for line in open(a.script, errors="replace"):
        if not line.strip():
            continue
        m = SAMPLE.match(line)
        if not m:
            bad_lines += 1
            continue
        S.append((float(m.group(3)) * 1000.0, m.group(1), int(m.group(4)),
                  m.group(7).strip(), classify(m.group(8))))
    if not S:
        raise SystemExit("no samples parsed (%d unparsed lines)" % bad_lines)
    S.sort()
    print("perf: %d samples parsed, %d unparsed, %.1f s covered"
          % (len(S), bad_lines, (S[-1][0] - S[0][0]) / 1000.0))

    W = windows(a.log)
    hot, calm = [], []
    for tick, span, worst in W:
        (hot if worst >= a.worst_ms else calm).append((tick - span, tick))
    print("windows: %d frozen (worst >= %d ms), %d calm"
          % (len(hot), a.worst_ms, len(calm)))
    if not hot:
        return

    def collect(spans):
        cy, wall = defaultdict(int), 0.0
        sym = defaultdict(int)
        for lo, hi in spans:
            if hi < S[0][0] or lo > S[-1][0]:
                continue
            wall += (hi - lo) / 1000.0
            for t, comm, per, s, k in S:
                if lo <= t <= hi:
                    cy[k] += per
                    sym[(k, s)] += per
        return cy, sym, wall

    hc, hs, hw = collect(hot)
    cc, cs, cw = collect(calm)
    if not hw:
        raise SystemExit("frozen windows lie outside the profile's coverage")

    print("\ncycles per SECOND OF WALL CLOCK, frozen vs calm (%.1f s vs %.1f s)\n"
          % (hw, cw))
    print("  %-22s %14s %14s %14s" % ("where", "frozen", "calm", "extra"))
    print("  " + "-" * 66)
    keys = sorted(set(hc) | set(cc), key=lambda k: -(hc[k] / hw - (cc[k] / cw if cw else 0)))
    for k in keys:
        h = hc[k] / hw
        c = cc[k] / cw if cw else 0
        print("  %-22s %14.3g %14.3g %+14.3g" % (k, h, c, h - c))

    print("\nbiggest per-symbol increases (cycles/s of wall clock)\n")
    print("  %-14s %-42s %13s" % ("where", "symbol", "extra"))
    print("  " + "-" * 72)
    rank = sorted(set(hs) | set(cs),
                  key=lambda k: -(hs[k] / hw - (cs[k] / cw if cw else 0)))
    for k in rank[:a.top]:
        d = hs[k] / hw - (cs[k] / cw if cw else 0)
        print("  %-14s %-42s %+13.3g" % (k[0][:14], k[1][:42], d))


if __name__ == "__main__":
    main()

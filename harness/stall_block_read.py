#!/usr/bin/env python3
"""Who was blocked, on what, during each freeze.

perf answers "what ran". It cannot answer "what waited", because a thread that is
off-CPU produces no samples -- and the freezes here are mostly waiting: during a
5.5 s one, all four cores together carried about 1.4 cores of work and the GL
thread left the CPU entirely for 1.9 s.

So this reads the probe's per-thread wchan, syscall and kernel stacks instead,
and lays them out as a timeline across each stall the presenter reported. Both
sides are CLOCK_MONOTONIC, so they join directly.

usage: stall_block_read.py <game log> <probe csv> [--min-ms 400]
"""
import argparse
import re
from collections import defaultdict, Counter

STALL = re.compile(r"MGS2 STALL tick=(\d+) frame took (\d+) ms")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("probe")
    ap.add_argument("--min-ms", type=int, default=400)
    ap.add_argument("--threads", type=int, default=6)
    a = ap.parse_args()

    T, K = [], []
    for line in open(a.probe, errors="replace"):
        f = line.split()
        if not f or f[0] == "#":
            continue
        try:
            if f[0] == "T" and len(f) >= 10:
                T.append((int(f[1]), f[2], f[3], f[4], int(f[5]), f[8], f[9]))
            elif f[0] == "K":
                K.append((int(f[1]), f[2], f[3], " ".join(f[4:])))
        except (ValueError, IndexError):
            continue
    if not T:
        raise SystemExit("probe has no per-thread records with wchan "
                         "(old format?) -- rerun the capture with the current probe")

    stalls = []
    for line in open(a.log, errors="replace"):
        m = STALL.search(line)
        if m and int(m.group(2)) >= a.min_ms:
            stalls.append((int(m.group(1)) - int(m.group(2)), int(m.group(1)),
                           int(m.group(2))))
    lo0, hi0 = T[0][0], T[-1][0]
    print("probe covers %.1f s; %d stalls reported, %d inside it"
          % ((hi0 - lo0) / 1000.0, len(stalls),
             sum(1 for s in stalls if s[0] >= lo0 and s[1] <= hi0)))

    for lo, hi, dur in stalls:
        if lo < lo0 or hi > hi0:
            continue
        rows = [x for x in T if lo <= x[0] <= hi]
        if not rows:
            continue
        print("\n" + "=" * 78)
        print("STALL %d ms  (tick %d..%d)" % (dur, lo, hi))
        cpu = defaultdict(list)
        st = defaultdict(Counter)
        wc = defaultdict(Counter)
        for t, tid, nm, state, c, wchan, sc in rows:
            cpu[(tid, nm)].append(c)
            st[(tid, nm)][state] += 1
            if state != "R":
                wc[(tid, nm)][wchan] += 1
        ranked = sorted(cpu, key=lambda k: -(cpu[k][-1] - cpu[k][0]))
        print("  %-16s %8s %-22s %s" % ("thread", "CPU ms", "state", "blocked in"))
        print("  " + "-" * 74)
        for k in ranked[:a.threads]:
            ms = (cpu[k][-1] - cpu[k][0]) * 10
            states = " ".join("%s:%d" % (s, n) for s, n in st[k].most_common())
            top = " ".join("%s(%d)" % (w, n) for w, n in wc[k].most_common(2))
            print("  %-16s %8d %-22s %s" % (k[1][:16], ms, states, top[:40]))
        ks = [x for x in K if lo <= x[0] <= hi]
        if ks:
            seen = Counter()
            for _, tid, nm, stk in ks:
                seen[(nm, stk)] += 1
            print("\n  kernel stacks seen while blocked (count x thread: stack)")
            for (nm, stk), n in seen.most_common(4):
                print("    %2dx %-15s %s" % (n, nm[:15], stk[:150]))


if __name__ == "__main__":
    main()

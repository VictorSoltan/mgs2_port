#!/usr/bin/env python3
"""Read an island A/B run: the paired ms/frame difference, and its own controls.

`device/launch-island-ab.sh <entry>` switches one island entry between the native
ARM route and the guest body every 64 displayed frames, ABBA, inside one live
process, and prints a line per completed cycle. Reducing those lines by hand is
how the entry-10 result was produced; doing it by hand is also how the filter
below gets forgotten, so it lives here instead.

WHAT IT COMPUTES

    difference   median of (routed - unrouted) ms/frame, over BALANCED cycles

A cycle is balanced when the two arms' call counts for the measured entry agree
within --tolerance (2% by default). This is the covariate that makes the number
readable: on the entry-10 run it collapsed the spread from sd 8.67 to 2.39
without moving the median (-8.83 -> -8.87), so it removes noise rather than
selecting a favourable subset. Both medians are printed for exactly that reason
-- if the filter MOVES the median, say so in the brief instead of quoting it.

THREE CONTROLS, PRINTED WHETHER OR NOT THEY PASS

1. Zero calls in both arms. Then the entry was never called, or -- the trap this
   check exists for -- the box86 binary has no A/B wrapper for it, so both arms
   ran routed and the difference is structurally 0. That is a false negative that
   looks exactly like "no effect", so it is reported as a REFUSAL, not a result.
2. Tick total against the launcher's own MGS2_GL_STATS frame counter, which is
   produced by different code on the other side of the emulator. Do NOT use the
   per-arm frame counts for this: the blocks are DEFINED in ticks, so that
   comparison is circular and holds whatever the tick counts.
3. Sign agreement across cycles. A real effect of this size showed 30 of 30
   cycles on one side; a split is a reason to distrust the median.

usage: island_ab_read.py <launch log> [--tolerance 0.02] [--all]
"""
import argparse
import math
import random
import re
import statistics
import sys

CYCLE = re.compile(
    r"MGS2 A/B cycle (\d+): routed ([\d.]+) ms/f \(n=(\d+), (\d+) calls\),"
    r" unrouted ([\d.]+) ms/f \(n=(\d+), (\d+) calls\),"
    r" routed-unrouted ([-+][\d.]+) ms/f, ticks (\d+)")
ARMED = re.compile(r"MGS2 A/B: island entry (\d+) toggled every (\d+) displayed frames")
STATS = re.compile(r"MGS2 present stats: tick=[\d.]+ (\d+) frames in ([\d.]+) ms")


def read(path):
    cycles, armed, frames, stats_ms = [], None, 0, 0.0
    with open(path, errors="replace") as fh:
        for line in fh:
            m = CYCLE.search(line)
            if m:
                g = m.groups()
                cycles.append(dict(cycle=int(g[0]), routed=float(g[1]),
                                   routed_n=int(g[2]), routed_calls=int(g[3]),
                                   unrouted=float(g[4]), unrouted_n=int(g[5]),
                                   unrouted_calls=int(g[6]),
                                   diff=float(g[7]), ticks=int(g[8])))
                continue
            m = ARMED.search(line)
            if m:
                armed = (int(m.group(1)), int(m.group(2)))
                continue
            m = STATS.search(line)
            if m:
                frames += int(m.group(1))
                stats_ms += float(m.group(2))
    return cycles, armed, frames, stats_ms


def exact_sign_p(negative, positive):
    """Exact two-sided sign test; callers omit ties."""
    n = negative + positive
    if not n:
        return 1.0
    k = min(negative, positive)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2.0 ** n)
    return min(1.0, 2.0 * tail)


def work_normalised(cycles, iterations=20000, seed=20260822):
    """Per-call cost difference, using every cycle instead of only balanced ones.

    WHY THIS EXISTS, AND WHAT IT COSTS

    The balanced-cycle median is the primary metric and stays that.  It needs the
    two arms to do the same amount of work inside one cycle, which a scene that
    drifts faster than a block simply never provides: the p72b session yielded 5
    balanced cycles out of 28, with a spread that says nothing.

    This estimator divides each arm's frame time by that arm's calls per frame,
    so scene weight cancels instead of disqualifying the cycle.  Its assumption
    is that frame time scales with the number of native applications -- true for
    a draw-bound renderer, false for a frame dominated by something else -- and
    the confidence interval does NOT cover that assumption, only sampling noise.

    The sign test is reported separately because it survives the assumption: it
    asks only whether the routed arm was cheaper per call, cycle by cycle.
    """
    per = []
    for c in cycles:
        if c["routed_n"] <= 0 or c["unrouted_n"] <= 0:
            raise ValueError(
                f"cycle {c.get('cycle', '?')} has a zero per-arm frame count")
        if not c["routed_calls"] or not c["unrouted_calls"]:
            continue
        routed = c["routed"] / (c["routed_calls"] / c["routed_n"])
        unrouted = c["unrouted"] / (c["unrouted_calls"] / c["unrouted_n"])
        per.append((routed - unrouted,
                    (c["routed_calls"] / c["routed_n"]
                     + c["unrouted_calls"] / c["unrouted_n"]) / 2))
    if len(per) < 2:
        return None
    deltas = [item[0] for item in per]
    workload = statistics.median([item[1] for item in per])
    n = len(deltas)
    favour = sum(1 for value in deltas if value < 0)
    oppose = sum(1 for value in deltas if value > 0)
    p_value = exact_sign_p(favour, oppose)

    rng = random.Random(seed)
    boot = sorted(statistics.median(rng.choices(deltas, k=n)) * workload
                  for _ in range(iterations))
    return dict(n=n, sign_n=favour + oppose, favour=favour, p=p_value,
                workload=workload,
                median=statistics.median(deltas) * workload,
                lo=boot[int(0.025 * iterations)], hi=boot[int(0.975 * iterations)],
                below_one=sum(1 for b in boot if b < -1.0) / iterations)


def spread(values):
    if not values:
        return None
    med = statistics.median(values)
    mean = statistics.fmean(values)
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    se = sd / len(values) ** 0.5 if len(values) > 1 else 0.0
    return dict(n=len(values), median=med, mean=mean, sd=sd, se=se)


def show(label, s):
    if not s:
        print(f"{label:<22} no cycles")
        return
    print(f"{label:<22} n={s['n']:<4} median {s['median']:+.3f}  mean {s['mean']:+.3f}"
          f"  sd {s['sd']:.2f}  se {s['se']:.2f}  ms/frame")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log")
    ap.add_argument("--tolerance", type=float, default=0.02,
                    help="max relative call-count imbalance for a balanced cycle")
    ap.add_argument("--all", action="store_true", help="print every cycle")
    ap.add_argument("--min-calls", type=int,
                    help="high-call subset: balanced cycles with at least this "
                         "many routed calls (default: the balanced median)")
    ap.add_argument("--plateau-width", type=float, default=0.05,
                    help="a plateau is the largest group of balanced cycles whose "
                         "routed call counts sit within this fraction of each other")
    args = ap.parse_args()

    cycles, armed, frames, stats_ms = read(args.log)
    if armed:
        print(f"entry {armed[0]}, {armed[1]}-frame blocks, ABBA")
    if not cycles:
        print("no completed A/B cycles in this log -- the run never reached "
              f"{4 * (armed[1] if armed else 64)} displayed frames.")
        return 2

    zero_frames = [c["cycle"] for c in cycles
                   if c["routed_n"] <= 0 or c["unrouted_n"] <= 0]
    if zero_frames:
        print("\nREFUSED: zero per-arm frame count in cycle(s): "
              + ", ".join(map(str, zero_frames)))
        print("The work-normalised result would divide by this count, so the run"
              " is malformed and no effect is reported.")
        return 2

    silent = [c for c in cycles if not c["routed_calls"] and not c["unrouted_calls"]]
    if len(silent) == len(cycles):
        print(f"\nREFUSED: all {len(cycles)} cycles recorded ZERO calls in both arms.")
        print("Either the entry is never called on this route, or this box86 binary")
        print("has no A/B wrapper for it -- in which case both arms ran ROUTED and")
        print("the difference is structurally zero. Check the binary before reading")
        print("this as 'no effect'.")
        return 2

    def imbalance(c):
        hi = max(c["routed_calls"], c["unrouted_calls"])
        return abs(c["routed_calls"] - c["unrouted_calls"]) / hi if hi else 1.0

    balanced = [c for c in cycles if imbalance(c) <= args.tolerance]

    if args.all:
        print("\ncycle  routed ms/f  unrouted ms/f     diff   routed calls  unrouted calls  bal")
        for c in cycles:
            print(f"{c['cycle']:>5}  {c['routed']:>11.3f}  {c['unrouted']:>13.3f}"
                  f"  {c['diff']:>+7.3f}   {c['routed_calls']:>12}  {c['unrouted_calls']:>14}"
                  f"  {'y' if imbalance(c) <= args.tolerance else '.'}")

    print()
    all_s = spread([c["diff"] for c in cycles])
    bal_s = spread([c["diff"] for c in balanced])
    show("all cycles", all_s)
    show(f"balanced (<={args.tolerance:.0%})", bal_s)

    if bal_s and all_s:
        moved = bal_s["median"] - all_s["median"]
        print(f"\nthe filter moved the median by {moved:+.3f} ms/frame"
              f" ({'noise removed' if abs(moved) < 0.5 else 'CHANGES THE ANSWER -- say so'})")

    if balanced:
        r = statistics.fmean([c["routed"] for c in balanced])
        u = statistics.fmean([c["unrouted"] for c in balanced])
        print(f"\narms: routed {r:.1f} ms/f = {1000 / r:.1f} fps,"
              f" unrouted {u:.1f} ms/f = {1000 / u:.1f} fps"
              f"   ->  {1000 / r - 1000 / u:+.2f} fps at this spot")
        favour = sum(1 for c in balanced if c["diff"] < 0)
        print(f"sign: {favour} of {len(balanced)} balanced cycles favour routed")

    # A single median over a whole session mixes scenes. The pre-registered
    # secondary metrics are therefore the repeated call-count plateau -- the
    # largest cluster of balanced cycles at one workload -- and the high-call
    # half, which is where the entry is actually hot. Neither replaces the
    # balanced median; they say whether it is carried by one scene.
    if balanced:
        counts = sorted(c["routed_calls"] for c in balanced)
        best = []
        for anchor in counts:
            group = [c for c in balanced
                     if anchor <= c["routed_calls"] <= anchor * (1 + args.plateau_width)]
            if len(group) > len(best):
                best = group
        if len(best) > 1:
            lo = min(c["routed_calls"] for c in best)
            hi = max(c["routed_calls"] for c in best)
            show(f"plateau {lo}-{hi}", spread([c["diff"] for c in best]))
            favour = sum(1 for c in best if c["diff"] < 0)
            print(f"{'':<22} {favour} of {len(best)} favour routed")
        cut = args.min_calls if args.min_calls is not None else statistics.median(counts)
        high = [c for c in balanced if c["routed_calls"] >= cut]
        if high and len(high) != len(balanced):
            show(f"high-call (>={int(cut)})", spread([c["diff"] for c in high]))
            favour = sum(1 for c in high if c["diff"] < 0)
            print(f"{'':<22} {favour} of {len(high)} favour routed")

    work = work_normalised(cycles)
    if work:
        print("\nwork-normalised (all %d cycles, scene weight divided out):" % work["n"])
        print("  routed cheaper per call in %d of %d non-ties"
              "  (exact two-sided sign test p=%.4g)"
              % (work["favour"], work["sign_n"], work["p"]))
        print("  effect at %.0f calls/frame: median %+.2f ms/frame,"
              " 95%% bootstrap CI [%+.2f, %+.2f]"
              % (work["workload"], work["median"], work["lo"], work["hi"]))
        print("  bootstrap medians below -1.0 ms/frame: %.0f%%" % (100 * work["below_one"]))
        print("  ASSUMES frame time scales with call count; the CI covers sampling"
              " noise only.\n  The sign test does not depend on that assumption.")

    print()
    if silent:
        print(f"note: {len(silent)} of {len(cycles)} cycles recorded no calls in either"
              " arm (menus, loading, or a scene that does not reach the entry)")
    ticks = cycles[-1]["ticks"]
    if frames:
        # MGS2_GL_STATS reports in whole blocks, so its total lags the harness by
        # up to one block. Only a gap LARGER than that is a real disagreement.
        print(f"tick control: {ticks} harness ticks against {frames} frames from"
              f" MGS2_GL_STATS  ({100.0 * ticks / frames:.1f}%);"
              f" launcher mean {stats_ms / frames:.1f} ms/frame")
        print("              the launcher counts whole blocks only, so it lags by"
              " up to one block -- read the excess against the block size, not"
              " against zero")
    else:
        print(f"tick control: NOT AVAILABLE -- {ticks} harness ticks and no"
              " 'present stats' line in this log. Run with MGS2_PLAY_WINEDEBUG"
              " containing err+all and MGS2_GL_STATS set, or the only frame"
              " counter in the run is the one being tested.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

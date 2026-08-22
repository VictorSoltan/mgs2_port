#!/usr/bin/env python3
"""Reduce a present A/B run: does removing the GPU wait shorten the frame?

`device/launch-present-ab.sh` flips MGS2_GL_ASYNC every N displayed frames inside
one live process, ABBA, and prints one `MGS2 PRESENT A/B block=` line per block.
This reduces those lines to a paired difference and prints the controls that
decide whether the difference may be quoted at all.

WHAT IT COMPUTES

    delta   median over ABBA cycles of
            mean(frametime of the two async blocks) - mean(the two sync blocks)

    A cycle is four consecutive blocks, arms sync async async sync. Averaging
    each arm's two blocks cancels a linear trend across the cycle -- scene drift,
    the SoC warming up -- which a plain A/B/A/B leaves in the estimate. Negative
    means async is faster.

THREE CONTROLS, PRINTED WHETHER OR NOT THEY PASS

1. THE MANIPULATION CHECK, and the only one that can void the run. The async arm
   must actually show the GPU wait collapse. If `wait` does not fall on the async
   arm, the switch did not do what it claims and there is no null to report --
   only a broken run. This is the present-branch equivalent of island_ab_read's
   "zero calls in both arms": a false negative that looks exactly like no effect.
2. Balance. Frame counts per arm within tolerance, no VOID blocks, no dropped
   frames. Blocks are defined in frames, so a frame-count imbalance means the
   presenter skipped work in one arm and the arms are not comparable.
3. Sign agreement across cycles, with an exact two-sided sign test. A median
   whose cycles split near 50/50 is noise wearing a number.

STEP CHANGES, WHICH ABBA DOES NOT HANDLE

ABBA cancels a LINEAR trend across the cycle. It does not cancel a step -- a
door opening into a new room, a menu closing, a cutscene starting -- and a step
lands entirely inside whichever arm was running when it happened. The two sync
blocks sit at positions 0 and 3, so they bracket the cycle: if they disagree
with each other, something changed inside the cycle that is not drift, and the
cycle is dropped. This is what --stability does, and it is the filter that
matters most in a run driven by someone actually playing.

QUANTISATION, WHICH IS WHY "NOT ON THE CAP" IS NOT THE SAME AS "FREE"

With MGS2_GL_SHM_BUFFERS=2 the presenter cannot start a frame until the
compositor releases a buffer, so every delivered frame time is a whole multiple
of the compositor period. A block whose mean lands between two multiples is not
a block running at that speed -- it is a MIXTURE of frames sitting on the
multiple below and the multiple above. In that regime shaving 2 ms off the CPU
does not make the frame 2 ms shorter; it tips some frames across a boundary and
changes the mixture. The delivered rate really does improve, but the effect is a
property of the boundary, not of the frame, and it does not extrapolate to a
heavy scene sixty milliseconds deep.

So a cycle only answers the gate when quantisation cannot dominate it: by
default the frame must be at least --min-ft (four periods, i.e. 15 fps or
slower), which is precisely the heavy regime the whole question is about.
Cycles between the caps are reported under their own heading and are never
allowed to produce a verdict.

THE FRAME CAP, AND WHY IT IS A CONTROL AND NOT A NUISANCE

Blocks pinned at the display or engine cap cannot answer the gate: the limiter
absorbs whatever the arm saves, so both arms read the same rate no matter what
the presenter does. Those cycles are therefore reported SEPARATELY, as a negative
control -- an instrument that invents a difference will invent one there too. The
verdict is taken from the cycles below the cap; if there are none, the run did not
reach a scene that could answer the question and says so.

The verdict follows the gate written into the launcher: a null closes the dmabuf
presenter, a win opens it, a failed manipulation check closes nothing.

usage: present_ab_read.py <launch log> [--threshold 2.0] [--tolerance 0.02] [--all]
"""
import argparse
import math
import random
import re
import statistics
import sys

BLOCK = re.compile(
    r"MGS2 PRESENT A/B block=(\d+) arm=(sync|async) frames=(\d+) span=([\d.]+) "
    r"fps=([\d.]+) ft_mean=([\d.]+) p50=([\d.]+) p95=([\d.]+) p99=([\d.]+) "
    r"ftmax=([\d.]+) readback=([\d.]+) wait=([-\d.]+) pixel=([-\d.]+) "
    r"gpucopy=([\d.]+) copy=([-\d.]+) acquire=([\d.]+) "
    r"slow=(\d+)/(\d+)/(\d+)/(\d+) drop=(\d+)")
VOID = re.compile(r"MGS2 PRESENT A/B block=(\d+) arm=(sync|async) VOID")
STATS = re.compile(r"MGS2 present stats: tick=[\d.]+ (\d+) frames in ([\d.]+) ms")

FIELDS = ("block arm frames span fps ft_mean p50 p95 p99 ftmax readback wait "
          "pixel gpucopy copy acquire s50 s100 s200 s500 drop").split()
ARM_ORDER = ("sync", "async", "async", "sync")


def parse(path):
    blocks, voids, stats = [], [], []
    with open(path, errors="replace") as fh:
        for line in fh:
            m = BLOCK.search(line)
            if m:
                vals = list(m.groups())
                rec = {"arm": vals[1]}
                for name, raw in zip(FIELDS, vals):
                    if name == "arm":
                        continue
                    rec[name] = int(raw) if name in ("block", "frames", "s50",
                                                     "s100", "s200", "s500",
                                                     "drop") else float(raw)
                blocks.append(rec)
                continue
            m = VOID.search(line)
            if m:
                voids.append(int(m.group(1)))
                continue
            m = STATS.search(line)
            if m:
                stats.append((int(m.group(1)), float(m.group(2))))
    return blocks, voids, stats


def boot_ci(sample, reps=20000, seed=20260822):
    if len(sample) < 2:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    n = len(sample)
    meds = sorted(statistics.median(rng.choices(sample, k=n)) for _ in range(reps))
    return meds[int(0.025 * reps)], meds[int(0.975 * reps)]


def sign_p(pos, neg):
    """Exact two-sided sign test; ties are dropped before calling."""
    n = pos + neg
    if not n:
        return 1.0
    k = min(pos, neg)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2.0 ** n)
    return min(1.0, 2.0 * tail)


def cycles_of(blocks):
    """Group into ABBA cycles, keyed off the driver's own block index so a
    trimmed log cannot silently re-phase the pattern."""
    by_index = {b["block"]: b for b in blocks}
    out = []
    for start in range(0, (max(by_index) if by_index else -1) + 1, 4):
        quad = [by_index.get(start + i) for i in range(4)]
        if any(q is None for q in quad):
            continue
        if tuple(q["arm"] for q in quad) != ARM_ORDER:
            continue
        out.append(quad)
    return out


def arm_delta(quad, key):
    sync = [q[key] for q in quad if q["arm"] == "sync"]
    asyn = [q[key] for q in quad if q["arm"] == "async"]
    return statistics.fmean(asyn) - statistics.fmean(sync)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("--threshold", type=float, default=2.0,
                    help="percent of frame time below which the branch is closed")
    ap.add_argument("--tolerance", type=float, default=0.02,
                    help="allowed per-arm frame-count imbalance within a cycle")
    ap.add_argument("--all", action="store_true", help="print every block")
    ap.add_argument("--period", type=float, default=1000.0 / 60.0,
                    help="compositor frame period in ms (default 16.667)")
    ap.add_argument("--cap-k", type=int, default=2,
                    help="highest vsync multiple treated as a cap (default 2, "
                         "i.e. 60 and 30 fps)")
    ap.add_argument("--cap-tol", type=float, default=0.03,
                    help="how close to a multiple counts as pinned (default 3%%)")
    ap.add_argument("--no-cap", action="store_true",
                    help="treat no block as capped")
    ap.add_argument("--min-ft", type=float, default=None,
                    help="minimum block frame time in ms for a cycle to answer "
                         "the gate (default 4 x --period)")
    ap.add_argument("--stability", type=float, default=0.15,
                    help="max disagreement between a cycle's two sync blocks "
                         "before the cycle is dropped (default 15%%)")
    args = ap.parse_args()

    blocks, voids, stats = parse(args.log)
    if not blocks:
        print("REFUSAL: no `MGS2 PRESENT A/B block=` lines. Wrong driver, or "
              "MGS2_PRESENT_AB was not set.")
        return 2

    # ---- the frame cap ---------------------------------------------------
    # A run walks through more than one cap -- 60 fps on the menus, 30 fps in
    # play -- so "the fastest block" does not find them. What every cap here has
    # in common is that it is a whole multiple of the compositor period, and
    # what a CPU-bound heavy scene has in common is that it is not. So the test
    # is explicit and auditable rather than clever: a block is pinned when its
    # mean frame time sits within --cap-tol of k * --period for k up to --cap-k.
    #
    # cap_k stops at 2 on purpose. Higher multiples start colliding with real
    # heavy frames -- 7 * 16.667 is 116.7 ms, which is exactly where this game's
    # worst scenes live -- and a limiter that holds a frame to one seventh of
    # vsync is not a thing this stack does.
    def cap_multiple(b):
        if args.no_cap or args.period <= 0.0:
            return 0
        for k in range(1, max(1, args.cap_k) + 1):
            if abs(b["ft_mean"] - k * args.period) <= args.cap_tol * k * args.period:
                return k
        return 0

    def capped(b):
        return cap_multiple(b) > 0

    pinned_blocks = [b for b in blocks if capped(b)]
    cap = (1000.0 / statistics.median([b["ft_mean"] for b in pinned_blocks])
           if pinned_blocks else None)

    quads = cycles_of(blocks)
    print("blocks parsed        %d (sync %d, async %d)"
          % (len(blocks), sum(b["arm"] == "sync" for b in blocks),
             sum(b["arm"] == "async" for b in blocks)))
    print("complete ABBA cycles %d" % len(quads))
    if voids:
        print("VOID blocks          %d  <-- %s" % (len(voids), voids[:10]))

    if args.all:
        print()
        for b in blocks:
            print("  block %3d %-5s n=%3d %6.3f fps  ft %7.2f  p95 %7.2f  "
                  "wait %6.3f  pixel %6.3f  drop %d"
                  % (b["block"], b["arm"], b["frames"], b["fps"], b["ft_mean"],
                     b["p95"], b["wait"], b["pixel"], b["drop"]))

    if not quads:
        print("\nREFUSAL: no complete ABBA cycle. Nothing pairs, nothing is "
              "reported.")
        return 2

    def stable(q):
        a = [b["ft_mean"] for b in q if b["arm"] == "sync"]
        if len(a) != 2:
            return False
        m = statistics.fmean(a)
        return m > 0 and abs(a[0] - a[1]) / m <= args.stability

    unstable = [q for q in quads if not stable(q)]
    quads = [q for q in quads if stable(q)]
    if unstable:
        print("dropped as unstable   %d cycles whose two sync blocks disagree by "
              "more than %.0f%% -- the scene stepped inside the cycle"
              % (len(unstable), 100.0 * args.stability))

    min_ft = args.min_ft if args.min_ft is not None else 4.0 * args.period

    def deep(q):
        return all(b["ft_mean"] >= min_ft for b in q)

    free   = [q for q in quads if not any(capped(b) for b in q) and deep(q)]
    quant  = [q for q in quads if not any(capped(b) for b in q) and not deep(q)]
    pinned = [q for q in quads if all(capped(b) for b in q)]
    mixed  = len(quads) - len(free) - len(quant) - len(pinned)
    if cap is not None:
        seen = sorted({cap_multiple(b) for b in pinned_blocks})
        print("\nframe cap             %d of %d blocks sit on a vsync multiple "
              "(k=%s of %.3f ms)"
              % (len(pinned_blocks), len(blocks),
                 ",".join(str(k) for k in seen), args.period))
    print("cycles deep enough    %d at or below %.1f ms (%.1f fps), the only "
          "ones that answer the gate" % (len(free), min_ft, 1000.0 / min_ft))
    print("  in the quantised band %d   pinned to a cap %d   straddling %d"
          % (len(quant), len(pinned), mixed))

    # ---- control 1: the manipulation check -------------------------------
    sync_wait = statistics.median([b["wait"] for b in blocks if b["arm"] == "sync"])
    asyn_wait = statistics.median([b["wait"] for b in blocks if b["arm"] == "async"])
    collapsed = asyn_wait < 0.5 * sync_wait
    print("\nCONTROL 1  GPU wait, median per block")
    print("           sync arm (gpu_finish)   %8.3f ms/f" % sync_wait)
    print("           async arm (deferred)    %8.3f ms/f" % asyn_wait)
    print("           collapsed to %.0f%% of the sync arm: %s"
          % (100.0 * asyn_wait / sync_wait if sync_wait else float("nan"),
             "PASS" if collapsed else "FAIL"))
    if sync_wait <= 0.0:
        print("           NOTE: sync wait is zero -- run without "
              "MGS2_GL_READ_SPLIT=1 cannot report gpu_finish, so this control "
              "is unavailable and the run is not readable.")

    # ---- control 2: balance ---------------------------------------------
    scope = free if cap is not None else quads
    imbalance, dropped = [], 0
    for q in scope:
        ns = sum(b["frames"] for b in q if b["arm"] == "sync")
        na = sum(b["frames"] for b in q if b["arm"] == "async")
        if ns:
            imbalance.append(abs(na - ns) / ns)
        dropped += sum(b["drop"] for b in q)
    worst = max(imbalance) if imbalance else 0.0
    balanced = [q for q, im in zip(scope, imbalance) if im <= args.tolerance]
    print("\nCONTROL 2  balance")
    print("           worst per-cycle frame imbalance %.2f%% (tolerance %.0f%%): %s"
          % (100.0 * worst, 100.0 * args.tolerance,
             "PASS" if worst <= args.tolerance else "CHECK"))
    print("           cycles within tolerance %d of %d" % (len(balanced), len(scope)))
    print("           frames dropped by the presenter %d: %s"
          % (dropped, "PASS" if dropped == 0 else "CHECK"))
    if stats:
        print("           independent MGS2_GL_STATS windows %d, %d frames total"
              % (len(stats), sum(n for n, _ in stats)))

    # ---- the estimate ----------------------------------------------------
    if quant:
        d_q = [arm_delta(q, "ft_mean") for q in quant]
        base_q = statistics.median(
            [b["ft_mean"] for q in quant for b in q if b["arm"] == "sync"])
        lo_q, hi_q = boot_ci(d_q)
        print("\nQUANTISED BAND    %d cycles, sync arm %.2f ms (%.2f fps)"
              % (len(quant), base_q, 1000.0 / base_q))
        print("         async - sync             %+8.2f ms/frame  CI [%+.2f, %+.2f]"
              % (statistics.median(d_q), lo_q, hi_q))
        print("         NOT a verdict. Between two vsync multiples this measures "
              "how the frame mixture shifts, not how long the frame takes.")

    if not scope:
        print("\nREFUSAL: not one cycle reached %.1f ms (%.1f fps). Every cycle "
              "was either pinned to a vsync multiple, where the limiter absorbs "
              "whatever the presenter saves, or inside the quantised band, where "
              "the number measures the boundary and not the frame. This run did "
              "not reach a scene that can answer the gate."
              % (min_ft, 1000.0 / min_ft))
        if pinned:
            d_cap = [arm_delta(q, "ft_mean") for q in pinned]
            print("         (capped cycles, for the record: median async - sync "
                  "%+.3f ms over %d cycles)" % (statistics.median(d_cap), len(d_cap)))
        return 2

    use = balanced if balanced else scope
    if not balanced:
        print("\n           no cycle passed the balance filter; reporting all "
              "cycles instead, and the number is weaker for it")

    d_ft = [arm_delta(q, "ft_mean") for q in use]
    d_p95 = [arm_delta(q, "p95") for q in use]
    d_p99 = [arm_delta(q, "p99") for q in use]
    med = statistics.median(d_ft)
    lo, hi = boot_ci(d_ft)
    pos = sum(1 for d in d_ft if d > 0)
    neg = sum(1 for d in d_ft if d < 0)
    p = sign_p(pos, neg)

    base_ft = statistics.median(
        [b["ft_mean"] for q in use for b in q if b["arm"] == "sync"])
    base_fps = 1000.0 / base_ft if base_ft else float("nan")
    new_fps = 1000.0 / (base_ft + med) if base_ft + med > 0 else float("nan")
    pct = 100.0 * med / base_ft if base_ft else float("nan")

    print("\nRESULT   over %d cycles" % len(use))
    print("         sync-arm frame time      %8.2f ms  (%.2f fps)" % (base_ft, base_fps))
    print("         async - sync             %+8.2f ms/frame  (%+.2f%%)" % (med, pct))
    print("         95%% bootstrap CI         [%+.2f, %+.2f] ms" % (lo, hi))
    print("         implied fps              %.2f -> %.2f" % (base_fps, new_fps))
    print("         p50/p95/p99 deltas       %+.2f / %+.2f / %+.2f ms"
          % (med, statistics.median(d_p95), statistics.median(d_p99)))
    if pinned:
        d_cap = [arm_delta(q, "ft_mean") for q in pinned]
        m_cap = statistics.median(d_cap)
        lo_c, hi_c = boot_ci(d_cap)
        print("\nNEGATIVE CONTROL  %d cycles pinned to a vsync multiple "
              "(~%.1f fps)" % (len(pinned), cap))
        print("         async - sync             %+8.3f ms/frame  CI [%+.3f, %+.3f]"
              % (m_cap, lo_c, hi_c))
        print("         the limiter absorbs both arms here, so anything other "
              "than ~0 means the instrument itself is biased: %s"
              % ("PASS" if abs(m_cap) < 0.5 else "FAIL -- do not trust the result above"))

    print("\nCONTROL 3  sign agreement")
    print("           async faster in %d of %d cycles, slower in %d, "
          "exact two-sided sign test p=%.4f"
          % (neg, len(d_ft), pos, p))

    # ---- verdict ---------------------------------------------------------
    print("\nVERDICT")
    if not collapsed:
        print("  VOID. The async arm did not collapse the GPU wait, so the")
        print("  switch did not do what the run assumes. This is not a null and")
        print("  it closes nothing -- fix the arm and run it again.")
        return 1
    crosses_zero = not (lo > 0 or hi < 0)
    if abs(pct) < args.threshold or crosses_zero:
        print("  NULL, and it is a real one: the wait collapsed and the frame did")
        print("  not shorten. The present branch is closed. Do not build a dmabuf")
        print("  presenter on the strength of the `readback` figure -- that figure")
        print("  is GPU wait, and this run removed it for free with no fps to show.")
        if crosses_zero and abs(pct) >= args.threshold:
            print("  (the point estimate clears the threshold but the CI crosses")
            print("   zero, so the magnitude is not established either way)")
    elif med < 0:
        print("  WIN. The wait collapsed and the frame shortened with it, which")
        print("  overturns brief 28's cross-run zero by a better measurement.")
        print("  GBM -> dma-buf -> EGLImage -> zwp_linux_dmabuf_v1 is now the")
        print("  next project: it takes this win without the frame of latency")
        print("  that MGS2_GL_ASYNC pays, and the owner already rejected that")
        print("  latency once.")
    else:
        print("  ASYNC IS WORSE by more than the threshold. The deferred path")
        print("  costs more than the wait it removes -- most likely the on-GPU")
        print("  glCopyTexSubImage2D. That closes MGS2_GL_ASYNC but NOT dmabuf,")
        print("  which has no such copy; price dmabuf off the NO_READBACK ceiling")
        print("  run instead of this one.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

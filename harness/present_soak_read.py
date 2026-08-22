#!/usr/bin/env python3
"""Paired stall/freeze soak: does one presenter hitch more than the other?

Two hangs on 2026-08-22 landed on the dmabuf presenter and none on shm, and a
144-minute FINALPLAY8 session logged two in-play frames over 500 ms. Neither
observation is a rate: "two hangs in a day" cannot be compared with anything,
and attributing hitches to a patch on that basis would be guesswork dressed as a
finding.

So this reads the same same-process ABBA the performance runs use, but with long
arms, and reports HITCHES PER 1000 FRAMES per arm instead of frame times. The
presenter already counts them per block -- `slow=a/b/c/d` is the number of frames
over 50, 100, 200 and 500 ms -- so nothing new has to be instrumented; the ABBA
just has to run long enough for the counts to mean something.

Why paired arms rather than two runs: a hitch rate depends on the scene, the
save, the route and the SoC temperature far more than on the presenter, and none
of those repeat across runs. Interleaving the arms inside one session is the only
way the comparison holds.

ONLY >200 ms AND >500 ms COUNT AS HITCHES. The presenter's buckets are
exclusive, and in combat the frame itself is 66-71 ms, so every ordinary frame
lands in the ">50 ms" bucket and a slower arm looks like it hitches constantly.
The first read of this soak showed shm at 115 "hitches" per 1000 frames purely
because it was running at 15 fps. Those two columns are printed but must not be
compared between arms.

PAIRED BY CYCLE, not summed globally. Arms are a minute long here, and a minute
of play is not the same scene twice; only the A-B-B-A grouping keeps the
comparison honest, exactly as in the frame-time reducer.

STARTUP IS EXCLUDED by a rule fixed in advance: blocks before --skip-blocks are
dropped, because loading a save legitimately produces multi-second frames and
whichever arm happens to own them would win or lose the run on an artefact.

usage: present_soak_read.py <log> [--skip-blocks 8] [--min-frames 200]
"""
import argparse
import re
import sys

BLOCK = re.compile(
    r"PRESENT A/B block=(\d+) arm=(sync|async) frames=(\d+) span=([\d.]+) .*?"
    r"slow=(\d+)/(\d+)/(\d+)/(\d+)")
STALL = re.compile(r"MGS2 STALL tick=([\d.]+) frame took (\d+) ms")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("--skip-blocks", type=int, default=8,
                    help="drop this many leading blocks: startup and save load")
    ap.add_argument("--min-frames", type=int, default=200,
                    help="refuse to report an arm with fewer accumulated frames")
    a = ap.parse_args()

    arms = {"sync": {"frames": 0, "span": 0.0, "s50": 0, "s100": 0, "s200": 0,
                     "s500": 0, "blocks": 0},
            "async": {"frames": 0, "span": 0.0, "s50": 0, "s100": 0, "s200": 0,
                      "s500": 0, "blocks": 0}}
    stalls = []
    with open(a.log, errors="replace") as fh:
        for line in fh:
            m = STALL.search(line)
            if m:
                stalls.append(int(m.group(2)))
            m = BLOCK.search(line)
            if not m:
                continue
            if int(m.group(1)) < a.skip_blocks:
                continue
            d = arms[m.group(2)]
            d["blocks"] += 1
            d["frames"] += int(m.group(3))
            d["span"] += float(m.group(4))
            for i, k in enumerate(("s50", "s100", "s200", "s500")):
                d[k] += int(m.group(5 + i))

    print("blocks after skipping the first %d: sync %d, async %d"
          % (a.skip_blocks, arms["sync"]["blocks"], arms["async"]["blocks"]))
    thin = [k for k, v in arms.items() if v["frames"] < a.min_frames]
    if thin:
        print("REFUSAL: %s has fewer than %d frames -- a hitch rate from that is "
              "noise, not a rate." % (", ".join(thin), a.min_frames))
        return 2

    print("\n%-8s %8s %9s %10s %10s %10s %10s"
          % ("arm", "frames", "minutes", ">50ms", ">100ms", ">200ms", ">500ms"))
    for k in ("sync", "async"):
        d = arms[k]
        label = "shm" if k == "sync" else "dmabuf"
        print("%-8s %8d %9.1f %10d %10d %10d %10d"
              % (label, d["frames"], d["span"] / 60000.0,
                 d["s50"], d["s100"], d["s200"], d["s500"]))

    print("\nper 1000 frames")
    print("%-8s %10s %10s %10s %10s" % ("arm", ">50ms", ">100ms", ">200ms", ">500ms"))
    rate = {}
    for k in ("sync", "async"):
        d = arms[k]
        f = d["frames"] / 1000.0
        rate[k] = tuple(d[x] / f for x in ("s50", "s100", "s200", "s500"))
        print("%-8s %10.2f %10.2f %10.2f %10.2f"
              % ("shm" if k == "sync" else "dmabuf", *rate[k]))

    print("\n>50 and >100 are NOT comparable between arms: at 15 fps every frame")
    print("exceeds 50 ms, so the slower arm always looks like it hitches more.")
    print("dmabuf - shm on the two buckets that mean something, per 1000 frames")
    print("  " + "  ".join("%s %+.3f" % (n, rate["async"][i + 2] - rate["sync"][i + 2])
                           for i, n in enumerate((">200", ">500"))))

    # Paired by cycle: block%4 -> A B B A, the same grouping the frame-time
    # reducer uses, so a scene change inside a cycle hits both arms.
    cyc = {}
    with open(a.log, errors="replace") as fh:
        for line in fh:
            m = BLOCK.search(line)
            if not m:
                continue
            b = int(m.group(1))
            if b < a.skip_blocks:
                continue
            c = b // 4
            e = cyc.setdefault(c, {"sync": [0, 0, 0], "async": [0, 0, 0]})
            d = e[m.group(2)]
            d[0] += int(m.group(3))                 # frames
            d[1] += int(m.group(7))                 # >200 ms
            d[2] += int(m.group(8))                 # >500 ms
    full = [c for c, e in sorted(cyc.items())
            if e["sync"][0] and e["async"][0]]
    print("\ncomplete cycles with both arms present: %d" % len(full))
    if full:
        d200 = d500 = 0.0
        for c in full:
            e = cyc[c]
            d200 += e["async"][1] / (e["async"][0] / 1000.0) - e["sync"][1] / (e["sync"][0] / 1000.0)
            d500 += e["async"][2] / (e["async"][0] / 1000.0) - e["sync"][2] / (e["sync"][0] / 1000.0)
        print("  mean paired difference per 1000 frames: >200 %+.3f, >500 %+.3f"
              % (d200 / len(full), d500 / len(full)))
        if len(full) < 10:
            print("  fewer than 10 cycles -- direction only, not a rate")

    if stalls:
        print("\nframes over 500 ms logged individually: %d" % len(stalls))
        print("  " + ", ".join("%d ms" % v for v in sorted(stalls, reverse=True)[:8]))
        print("  (these are NOT split by arm -- the STALL line carries no arm; use"
              " the >500ms column above for the paired comparison)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

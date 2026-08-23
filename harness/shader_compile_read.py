#!/usr/bin/env python3
"""What the Mali shader compiler actually does, before designing a cache for it.

The short 0.5-1.1 s freezes are GLSL compilation inside libmali: wined3d_cs is
CPU-bound in R state, 70-92% of its cycles in libmali, and every libstdc++ cycle
in a whole run falls inside a freeze. That much is settled. What is NOT settled
is which cache would help, and the two answers need different patches:

  * the same shaders recompiled again and again  -> a program-binary cache pays
    off within a single run, and across runs too
  * every compile a different shader             -> an in-run cache buys almost
    nothing; the win has to come from persisting binaries between runs, or from
    compiling them before the player can see the stall

So this reads the ring wined3d already fills (magic 'GPU2') and answers exactly
that: how many compiles, how much time, how many DISTINCT sources, and how much
of the total time went into sources that were compiled more than once.

Symbol-free, like gl_census_delta.py: the ring starts with its own magic, so it
is found by scanning the process rather than by needing an unstripped DLL.

usage: shader_compile_read.py <pid> [--reset]
"""
import argparse
import re
import struct
import sys
from collections import defaultdict

MAGIC = 0x32555047          # 'GPU2'
PBC_MAGIC = 0x31434250      # 'PBC1' -- program-binary cache accounting
CAPACITY = 512
EVENT = struct.Struct("<9i")        # commit, op, tid, duration_us, a, b, c, d, object
HEADER = struct.Struct("<4I")       # magic, version, capacity, next_sequence
OPS = {5: "link program", 6: "compile shader", 8: "link separable stage",
       9: "validate pipeline", 10: "slow bind"}


def readable_regions(pid):
    out = []
    with open("/proc/%d/maps" % pid) as fh:
        for line in fh:
            m = re.match(r"([0-9a-f]+)-([0-9a-f]+) (\S{4}) \S+ \S+ \S+\s*(.*)", line)
            if not m or "r" not in m.group(3):
                continue
            out.append((int(m.group(1), 16), int(m.group(2), 16), m.group(4)))
    return out


def find_rings(pid):
    pat = struct.pack("<II", MAGIC, 1)
    rings = []
    with open("/proc/%d/mem" % pid, "rb", 0) as mem:
        for lo, hi, _ in readable_regions(pid):
            try:
                mem.seek(lo)
                blob = mem.read(hi - lo)
            except (OSError, ValueError, OverflowError):
                continue
            i = blob.find(pat)
            while i >= 0:
                cap, seq = struct.unpack_from("<II", blob, i + 8)
                if cap == CAPACITY:
                    need = HEADER.size + CAPACITY * EVENT.size
                    if i + need <= len(blob):
                        rings.append((seq, blob[i + HEADER.size:i + need]))
                i = blob.find(pat, i + 4)
    return rings


PBC_FIELDS = ("state hits misses stores open_fail short_file gl_error link_false "
              "store_no_len store_no_data store_write_fail last_format last_size "
              "last_src_len roundtrip_tried roundtrip_ok roundtrip_err").split()


def read_pbc(pid):
    pat = struct.pack("<IIII", PBC_MAGIC, 1, 4 + len(PBC_FIELDS),
                      (~PBC_MAGIC) & 0xFFFFFFFF)
    out = []
    with open("/proc/%d/mem" % pid, "rb", 0) as mem:
        for lo, hi, _ in readable_regions(pid):
            try:
                mem.seek(lo)
                blob = mem.read(hi - lo)
            except (OSError, ValueError, OverflowError):
                continue
            i = blob.find(pat)
            while i >= 0:
                n = 4 + len(PBC_FIELDS)
                out.append(struct.unpack("<%dI" % n, blob[i:i + n * 4])[4:])
                i = blob.find(pat, i + 4)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pid", type=int)
    a = ap.parse_args()

    for rec in read_pbc(a.pid):
        print("program-binary cache accounting")
        for name, v in zip(PBC_FIELDS, rec):
            if name in ("last_format",):
                print("  %-18s 0x%x" % (name, v))
            else:
                print("  %-18s %d" % (name, v))
        print()

    rings = find_rings(a.pid)
    if not rings:
        sys.exit("no 'GPU2' ring found -- is MGS2_GPU_PROBE set for this run?")

    for seq, blob in rings:
        events = [EVENT.unpack_from(blob, k * EVENT.size) for k in range(CAPACITY)]
        events = [e for e in events if e[0]]         # committed only
        kept = len(events)
        print("ring: %d events recorded in total, %d still in the buffer%s"
              % (seq, kept, " (WRAPPED, oldest lost)" if seq > CAPACITY else ""))

        by_op = defaultdict(lambda: [0, 0])
        for _c, op, _t, us, _a, _b, _cc, _d, _o in events:
            by_op[op][0] += 1
            by_op[op][1] += us
        print("\n  %-24s %8s %12s %10s" % ("op", "count", "total ms", "mean ms"))
        for op in sorted(by_op):
            n, us = by_op[op]
            print("  %-24s %8d %12.1f %10.2f"
                  % (OPS.get(op, "op %d" % op), n, us / 1000.0, us / 1000.0 / n))

        comp = [e for e in events if e[1] == 6]
        if comp:
            per = defaultdict(lambda: [0, 0])
            for _c, _op, _t, us, lo32, hi32, size, _d, _o in comp:
                key = (hi32 & 0xffffffff) << 32 | (lo32 & 0xffffffff)
                per[key][0] += 1
                per[key][1] += us
            total_us = sum(v[1] for v in per.values())
            repeat = {k: v for k, v in per.items() if v[0] > 1}
            repeat_us = sum(v[1] - v[1] / v[0] for v in repeat.values())
            print("\ncompiles in the buffer: %d, distinct sources: %d"
                  % (len(comp), len(per)))
            print("  sources compiled more than once: %d" % len(repeat))
            print("  time that a within-run cache could have skipped: %.1f ms of %.1f (%.0f%%)"
                  % (repeat_us / 1000.0, total_us / 1000.0,
                     100.0 * repeat_us / total_us if total_us else 0))
            print("\n  the verdict this decides")
            if total_us and repeat_us / total_us > 0.4:
                print("    Most of the compile time is REPEATS. A program-binary")
                print("    cache pays off inside a single run; build that.")
            else:
                print("    Compile time is dominated by FIRST compiles. An in-run")
                print("    cache buys little -- the win has to be a binary cache")
                print("    persisted BETWEEN runs, or a prewarm before the player")
                print("    can see the stall.")
            top = sorted(per.items(), key=lambda kv: -kv[1][1])[:6]
            print("\n  slowest sources")
            for k, (n, us) in top:
                print("    %016x  x%-4d %8.1f ms" % (k, n, us / 1000.0))

        # Separable-stage links carry d=1 when the program came out of the
        # binary cache instead of being linked from source. Splitting on it is
        # what says whether the cache is working, and no rebuild is needed to
        # ask -- the field is already in the ring.
        sep = [e for e in events if e[1] == 8]
        if sep:
            hit = [e for e in sep if e[7] == 1]
            miss = [e for e in sep if e[7] != 1]
            hu = sum(e[3] for e in hit)
            mu = sum(e[3] for e in miss)
            print("\nseparable stage links: %d from the binary cache (%.1f ms, "
                  "%.1f ms each), %d linked from source (%.1f ms, %.1f ms each)"
                  % (len(hit), hu / 1000.0, hu / 1000.0 / len(hit) if hit else 0,
                     len(miss), mu / 1000.0, mu / 1000.0 / len(miss) if miss else 0))
            if hit and miss:
                print("  a cache hit costs %.0f%% of a source link here"
                      % (100.0 * (hu / len(hit)) / (mu / len(miss))))
            elif not hit:
                print("  NOTHING came from the cache. Either the key is unstable")
                print("  between runs, or the driver is rejecting the binaries.")

        links = [e for e in events if e[1] == 5]
        if links:
            lazy = sum(e[6] for e in links)
            tot = sum(e[3] for e in links)
            print("\nlinks: %d, %.1f ms; of that the LINK_STATUS query is %.1f ms (%.0f%%)"
                  % (len(links), tot / 1000.0, lazy / 1000.0,
                     100.0 * lazy / tot if tot else 0))
            print("  a high share there means the driver links lazily and the real")
            print("  cost lands on the first query, not inside glLinkProgram.")


if __name__ == "__main__":
    main()

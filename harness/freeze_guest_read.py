#!/usr/bin/env python3
"""Which GUEST code burns the long freezes.

perf says 67-79% of a long freeze is "[JIT] guest code" and stops there: the
translated blocks have no symbols. Box86's recorder closes that gap -- it appends
(native_start, native_size, x86_start, x86_size) for every block it compiles, so
a native IP can be walked back to the x86 address it came from, and that address
falls inside one of the guest modules listed in /proc/PID/maps.

The point is to find out whether the freeze is spread evenly over the game's code
-- in which case only faster emulation helps -- or concentrated in a few guest
functions, which this project can already replace with native ARM.

usage: freeze_guest_read.py <game log> <perf script w/ time> <guestmap.bin> <maps.txt>
"""
import argparse
import bisect
import re
import struct
from collections import Counter

HEADER = struct.Struct("<8s5I")
RECORD = struct.Struct("<4I")
# -F comm,pid,tid,time,ip,sym,dso
LINE = re.compile(r"^\s*(?P<comm>.*?)\s+(?P<pid>\d+)/(?P<tid>\d+)\s+"
                  r"(?P<t>[0-9.]+):\s+(?P<ip>[0-9a-f]+)\s+.*\((?P<dso>[^()]*)\)\s*$")


def map_invariants(recs):
    """Box86 reuses native code-cache ranges, so "the record whose native_start is
    nearest below this IP" is not automatically the block that was executing.

    The recorder appends one record per compiled block and never removes them, so
    a range that was ever reused carries two records that overlap. Counting those
    is what turns the resolution from an assumption into a measurement -- and the
    count has to be reported next to every attribution, not checked once.
    """
    dup = overlap = reused = 0
    seen = {}
    for st, sz, x86, _xsz in recs:
        if st in seen:
            dup += 1
            if seen[st] != x86:
                reused += 1
        seen[st] = x86
    s = sorted(recs)
    for i in range(len(s) - 1):
        if s[i][0] + s[i][1] > s[i + 1][0]:
            overlap += 1
    return dup, overlap, reused


def load_map(path):
    raw = open(path, "rb").read()
    magic, addr, count, overflow, rsize, cap = HEADER.unpack_from(raw)
    if magic != b"MGS2GM01":
        raise SystemExit("bad guest-map magic %r" % magic)
    recs = [RECORD.unpack_from(raw, HEADER.size + i * rsize)
            for i in range(min(count, cap))]
    # A block with no native size can never contain a sample, and the recorder
    # has a few zero/one entries from before it is fully armed.
    recs = [r for r in recs if r[1] and r[3] and r[0] > 0x1000]
    recs.sort()
    return recs, overflow


def load_modules(path):
    mods = []
    for line in open(path, errors="replace"):
        m = re.match(r"([0-9a-f]+)-([0-9a-f]+) (\S{4}) \S+ \S+ \S+\s*(.*)", line)
        if not m or "x" not in m.group(3):
            continue
        name = m.group(4).strip() or "[anon]"
        mods.append((int(m.group(1), 16), int(m.group(2), 16), name))
    mods.sort()
    return mods


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("script")
    ap.add_argument("guestmap")
    ap.add_argument("maps")
    ap.add_argument("--min-ms", type=int, default=3000)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--bucket", type=lambda s: int(s, 0), default=0x1000)
    a = ap.parse_args()

    recs, overflow = load_map(a.guestmap)
    starts = [r[0] for r in recs]
    mods = load_modules(a.maps)
    mstarts = [m[0] for m in mods]
    dup, overlap, reused = map_invariants(recs)
    print("guest map: %d usable blocks, overflow=%d; %d executable mappings"
          % (len(recs), overflow, len(mods)))
    print("  native-range reuse: %d duplicate starts (%d to a different guest "
          "block), %d overlapping neighbours" % (dup, reused, overlap))

    spans = []
    for line in open(a.log, errors="replace"):
        m = re.search(r"MGS2 STALL tick=(\d+) frame took (\d+) ms", line)
        if m and int(m.group(2)) >= a.min_ms:
            spans.append((int(m.group(1)) - int(m.group(2)), int(m.group(1))))
    print("long stalls (>= %d ms): %d" % (a.min_ms, len(spans)))

    def which(lo, hi, t):
        return lo <= t <= hi

    maxsz = max(r[1] for r in recs)

    def owners(ip):
        """Every block whose native range contains ip -- not just the nearest one.
        More than one means the range was recycled and this sample cannot be
        attributed from a snapshot that has no compile order."""
        out = []
        j = bisect.bisect_right(starts, ip) - 1
        while j >= 0 and starts[j] >= ip - maxsz:
            if recs[j][0] <= ip < recs[j][0] + recs[j][1]:
                out.append(recs[j][2])
            j -= 1
        return set(out)

    hit = Counter()
    mod_hit = Counter()
    total = unresolved = ambiguous = 0
    for line in open(a.script, errors="replace"):
        m = LINE.match(line)
        if not m or "perf-" not in m.group("dso"):
            continue
        t = float(m.group("t")) * 1000.0
        if not any(which(lo, hi, t) for lo, hi in spans):
            continue
        total += 1
        ip = int(m.group("ip"), 16)
        own = owners(ip)
        if not own:
            unresolved += 1
            continue
        if len(own) > 1:
            ambiguous += 1
            continue
        x86 = next(iter(own))
        hit[x86 & ~(a.bucket - 1)] += 1
        j = bisect.bisect_right(mstarts, x86) - 1
        mod_hit[mods[j][2] if j >= 0 and x86 < mods[j][1] else "(unmapped)"] += 1

    if not total:
        raise SystemExit("no JIT samples inside the long stalls")
    print("\nJIT samples inside long stalls: %d -- uniquely resolved %d (%.1f%%), "
          "ambiguous %d (%.2f%%), unresolved %d (%.2f%%)\n"
          % (total, total - unresolved - ambiguous,
             100.0 * (total - unresolved - ambiguous) / total,
             ambiguous, 100.0 * ambiguous / total,
             unresolved, 100.0 * unresolved / total))
    if ambiguous > total * 0.02:
        print("  WARNING: more than 2%% ambiguous. The shares below are not "
              "trustworthy; the recorder needs a compile sequence number.\n")

    print("by guest module")
    for name, n in mod_hit.most_common(10):
        print("  %-52s %6.2f%%" % (name[-52:], 100.0 * n / total))

    print("\nhottest guest code, %d-byte buckets" % a.bucket)
    print("  %-14s %-40s %8s" % ("x86 addr", "module + offset", "share"))
    for addr, n in hit.most_common(a.top):
        j = bisect.bisect_right(mstarts, addr) - 1
        if j >= 0 and addr < mods[j][1]:
            where = "%s+0x%x" % (mods[j][2].rsplit("/", 1)[-1], addr - mods[j][0])
        else:
            where = "(unmapped)"
        print("  0x%-12x %-40s %6.2f%%" % (addr, where[:40], 100.0 * n / total))


if __name__ == "__main__":
    main()

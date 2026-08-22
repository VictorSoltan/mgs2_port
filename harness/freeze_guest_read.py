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
    print("guest map: %d usable blocks, overflow=%d; %d executable mappings"
          % (len(recs), overflow, len(mods)))

    spans = []
    for line in open(a.log, errors="replace"):
        m = re.search(r"MGS2 STALL tick=(\d+) frame took (\d+) ms", line)
        if m and int(m.group(2)) >= a.min_ms:
            spans.append((int(m.group(1)) - int(m.group(2)), int(m.group(1))))
    print("long stalls (>= %d ms): %d" % (a.min_ms, len(spans)))

    def which(lo, hi, t):
        return lo <= t <= hi

    hit = Counter()
    mod_hit = Counter()
    total = unresolved = 0
    for line in open(a.script, errors="replace"):
        m = LINE.match(line)
        if not m or "perf-" not in m.group("dso"):
            continue
        t = float(m.group("t")) * 1000.0
        if not any(which(lo, hi, t) for lo, hi in spans):
            continue
        total += 1
        ip = int(m.group("ip"), 16)
        i = bisect.bisect_right(starts, ip) - 1
        if i < 0 or ip >= recs[i][0] + recs[i][1]:
            unresolved += 1
            continue
        x86 = recs[i][2]
        hit[x86 & ~(a.bucket - 1)] += 1
        j = bisect.bisect_right(mstarts, x86) - 1
        mod_hit[mods[j][2] if j >= 0 and x86 < mods[j][1] else "(unmapped)"] += 1

    if not total:
        raise SystemExit("no JIT samples inside the long stalls")
    print("\nJIT samples inside long stalls: %d, resolved %d (%.1f%%)\n"
          % (total, total - unresolved, 100.0 * (total - unresolved) / total))

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

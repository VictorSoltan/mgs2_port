#!/usr/bin/env python3
"""How much GL work does a scene ask for, per frame -- and how much more does combat.

The differential profile put 73% of combat's added cost in the GL-call pipeline
(libmali 29%, Box86 JIT 29%, box86 runtime 15%), and that is the price of MAKING
the calls, not of drawing: the GPU sits idle 88% of a combat frame. So the next
question is which calls, and the census in wined3d already counts them by family.

WHY THIS DOES NOT USE SYMBOLS

harness/p72_correctness_read.py wants the census RVA, which wants an unstripped
paired DLL or an i686 nm. Neither is needed: the record starts with a 4-word
self-identifying header -- magic 'CGL1', version, word count, and the magic
inverted -- so it can be found by scanning the process. That also solves the
duplication problem for free. The island links a second copy of the translation
unit, so a natively-routed phase increments ITS counters and not the guest's;
a reader that finds one copy silently under-reports. This finds every copy and
prints them separately as well as summed.

Counters are cumulative, so the tool samples twice and reports the difference,
normalised per displayed frame using the presenter's own frame counter in the
game log -- the only way two scenes with different frame rates compare.

usage:  gl_census_delta.py <pid> [--seconds 20] [--log <game log>]
"""
import argparse
import re
import struct
import sys
import time

MAGIC = 0x314C4743          # 'CGL1'
FIELDS = ("ext_calls draw_state_applies state_apply_callbacks uniform_loads "
          "program_selects texture_binds sampler_applies shader_resource_binds "
          "fbo_checks").split()
HEADER_WORDS = 4
NWORDS = HEADER_WORDS + len(FIELDS)


def readable_regions(pid):
    out = []
    with open("/proc/%d/maps" % pid) as fh:
        for line in fh:
            m = re.match(r"([0-9a-f]+)-([0-9a-f]+) (\S{4}) \S+ \S+ \S+\s*(.*)", line)
            if not m or "r" not in m.group(3):
                continue
            name = m.group(4)
            # Skip the obvious noise: device mappings and huge anonymous arenas
            # are not where a static struct lives, and walking them costs seconds.
            if name.startswith("/dev/") or name in ("[vvar]", "[vsyscall]"):
                continue
            lo, hi = int(m.group(1), 16), int(m.group(2), 16)
            # 2 GB, not 512 MB: the island's copy of the record is linked into
            # box86 itself, and clipping large regions was how the first version
            # of this tool found only the guest copy and reported zeros for every
            # counter a natively-routed phase increments.
            if hi - lo > 2 * 1024 * 1024 * 1024:
                continue
            out.append((lo, hi, name))
    return out


def find_records(pid):
    """Every self-identifying census record in the process, guest and island."""
    # Match the magic and its inverse three words apart, leaving version and
    # word count free: a copy built by a different compiler for the island must
    # still be found, and being strict about those two fields is how it would be
    # missed.
    head = struct.pack("<I", MAGIC)
    tail = struct.pack("<I", (~MAGIC) & 0xFFFFFFFF)
    hits = []
    with open("/proc/%d/mem" % pid, "rb", 0) as mem:
        for lo, hi, name in readable_regions(pid):
            try:
                mem.seek(lo)
                blob = mem.read(hi - lo)
            except (OSError, ValueError, OverflowError):
                continue
            start = 0
            while True:
                i = blob.find(head, start)
                if i < 0:
                    break
                start = i + 4
                if blob[i + 12:i + 16] != tail:
                    continue
                hits.append((lo + i, name))
    return hits


def sample(pid, addrs):
    vals = []
    with open("/proc/%d/mem" % pid, "rb", 0) as mem:
        for a, _ in addrs:
            mem.seek(a)
            w = struct.unpack("<%dI" % NWORDS, mem.read(NWORDS * 4))
            vals.append(dict(zip(FIELDS, w[HEADER_WORDS:])))
    return vals


def frames(log):
    """The presenter's own frame counter -- produced on the other side of the
    emulator from the census, so it is not a circular check."""
    n = 0
    try:
        with open(log, errors="replace") as fh:
            for line in fh:
                m = re.search(r"present stats: tick=[\d.]+ (\d+) frames", line)
                if m:
                    n += int(m.group(1))
    except OSError:
        return None
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pid", type=int)
    ap.add_argument("--seconds", type=float, default=20.0)
    ap.add_argument("--log", default=None, help="game log, for the frame count")
    a = ap.parse_args()

    addrs = find_records(a.pid)
    if not addrs:
        print("REFUSAL: no census record found. Wrong wined3d.dll -- the build "
              "must be one compiled with MGS2_GL_CENSUS.")
        return 2
    print("census records found: %d" % len(addrs))
    for addr, name in addrs:
        print("  %#x  %s" % (addr, name or "(anonymous)"))

    f0 = frames(a.log) if a.log else None
    before = sample(a.pid, addrs)
    time.sleep(a.seconds)
    after = sample(a.pid, addrs)
    f1 = frames(a.log) if a.log else None

    nframes = (f1 - f0) if (f0 is not None and f1 is not None and f1 > f0) else None
    print("\nwindow %.1f s, displayed frames %s"
          % (a.seconds, nframes if nframes else "UNKNOWN (no --log, or no stats lines)"))

    print("\n%-24s %12s %12s %10s" % ("counter", "delta", "per second",
                                      "per frame" if nframes else ""))
    total = {}
    for f in FIELDS:
        d = sum(after[i][f] - before[i][f] for i in range(len(addrs)))
        total[f] = d
        per_s = d / a.seconds
        per_f = ("%10.1f" % (d / nframes)) if nframes else ""
        print("%-24s %12d %12.0f %s" % (f, d, per_s, per_f))

    if len(addrs) > 1:
        print("\nper record (island copies are separate and MUST be summed):")
        for i, (addr, name) in enumerate(addrs):
            d = {f: after[i][f] - before[i][f] for f in FIELDS}
            live = {k: v for k, v in d.items() if v}
            print("  %#x %s" % (addr, live if live else "(idle)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

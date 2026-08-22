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

MAGIC = 0x314C4743          # 'CGL1' -- the family record
EXT_MAGIC = 0x314C4758      # 'XGL1' -- the per-function histogram
EXT_NAME = 40               # sizeof(mgs2_ext_site.name)
EXT_SITE = EXT_NAME + 4
SHADOW_MAGIC = 0x314C4753   # 'SGL1' -- the shadow simulator
SHADOW_NAME = 48
SHADOW_SITE = SHADOW_NAME + 8
ATTRIB_MAGIC = 0x31485341   # 'ASH1' -- the real vertex-attribute shadow (closed)
TXM_MAGIC = 0x314D5854      # 'TXM1' -- the FFP texture-matrix program cache
TXM_TEX = 8
ASP_MAGIC = 0x31505341      # 'ASP1' -- the separable stage selector
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


def find_ext_records(pid):
    """The per-function histogram. Its header is magic, version, capacity, used
    -- no inverted-magic tail -- so the match is on magic plus a version and a
    capacity that make sense, which is enough given the magic is 4 bytes."""
    head = struct.pack("<I", EXT_MAGIC)
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
                if len(blob) - i < 16:
                    continue
                ver, cap, used = struct.unpack("<III", blob[i + 4:i + 16])
                if ver != 1 or not (1 <= cap <= 4096) or used > cap:
                    continue
                hits.append((lo + i, name))
    return hits


def read_asp_stats(pid):
    """Sum every ASP1 record (guest DLL plus the island's copy)."""
    pat = struct.pack("<IIII", ASP_MAGIC, 1, 12, (~ASP_MAGIC) & 0xFFFFFFFF)
    keys = ("lazy separable_loads need_vs need_ps avoided_vs avoided_ps "
            "missed_vs missed_ps").split()
    out = []
    with open("/proc/%d/mem" % pid, "rb", 0) as mem:
        for lo, hi, name in readable_regions(pid):
            try:
                mem.seek(lo)
                blob = mem.read(hi - lo)
            except (OSError, ValueError, OverflowError):
                continue
            i = blob.find(pat)
            while i >= 0:
                w = struct.unpack("<12I", blob[i:i + 48])
                d = dict(zip(keys, w[4:]))
                d["where"] = (name or "(anon)").split("/")[-1]
                out.append(d)
                i = blob.find(pat, i + 4)
    return out


def read_txm_stats(pid):
    """Every TXM1 record: the guest wined3d.dll has one and the island links a
    second copy into Box86, so both must be summed -- and both must be flipped
    by the A/B, or an arm is only half applied."""
    pat = struct.pack("<I", TXM_MAGIC)
    inv = struct.pack("<I", (~TXM_MAGIC) & 0xFFFFFFFF)
    out = []
    with open("/proc/%d/mem" % pid, "rb", 0) as mem:
        for lo, hi, name in readable_regions(pid):
            try:
                mem.seek(lo)
                blob = mem.read(hi - lo)
            except (OSError, ValueError, OverflowError):
                continue
            start = 0
            while True:
                i = blob.find(pat, start)
                if i < 0:
                    break
                start = i + 4
                if blob[i + 12:i + 16] != inv:
                    continue
                n = 10 + 2 * TXM_TEX
                if len(blob) - i < n * 4:
                    continue
                w = struct.unpack("<%dI" % n, blob[i:i + n * 4])
                out.append({
                    "addr": lo + i, "where": name or "(anon)",
                    "enabled": w[4], "attempted": w[5], "skipped": w[6],
                    "executed": w[7], "cold_miss": w[8], "changed_miss": w[9],
                    "per_tex_attempted": list(w[10:10 + TXM_TEX]),
                    "per_tex_skipped": list(w[10 + TXM_TEX:10 + 2 * TXM_TEX]),
                })
    return out


def read_attrib_stats(pid):
    """The real shadow's own counters: enabled, attempted, skipped,
    invalidations. attempted - skipped is what still reached the driver."""
    pat = struct.pack("<IIII", ATTRIB_MAGIC, 1, 15, (~ATTRIB_MAGIC) & 0xFFFFFFFF)
    with open("/proc/%d/mem" % pid, "rb", 0) as mem:
        for lo, hi, name in readable_regions(pid):
            try:
                mem.seek(lo)
                blob = mem.read(hi - lo)
            except (OSError, ValueError, OverflowError):
                continue
            i = blob.find(pat)
            if i < 0:
                continue
            mem.seek(lo + i)
            w = struct.unpack("<15I", mem.read(60))
            d = {"addr": lo + i, "enabled": w[4], "attempted": w[5],
                 "skipped": w[6], "invalidations": w[7]}
            for n, k in enumerate(("invalid", "buffer", "size", "type",
                                   "norm", "stride", "pointer")):
                d["miss_" + k] = w[8 + n]
            return d
    return None


def find_shadow_records(pid):
    head = struct.pack("<I", SHADOW_MAGIC)
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
                if len(blob) - i < 16:
                    continue
                ver, cap, used = struct.unpack("<III", blob[i + 4:i + 16])
                if ver != 1 or not (1 <= cap <= 1024) or used > cap:
                    continue
                hits.append((lo + i, name))
    return hits


def sample_shadow(pid, addrs):
    out = {}
    with open("/proc/%d/mem" % pid, "rb", 0) as mem:
        for a, _ in addrs:
            mem.seek(a)
            _, _, _, used = struct.unpack("<IIII", mem.read(16))
            blob = mem.read(used * SHADOW_SITE)
            for i in range(used):
                rec = blob[i * SHADOW_SITE:(i + 1) * SHADOW_SITE]
                name = rec[:SHADOW_NAME].split(b"\0")[0].decode("ascii", "replace")
                att, red = struct.unpack("<II", rec[SHADOW_NAME:SHADOW_NAME + 8])
                a0, r0 = out.get(name, (0, 0))
                out[name] = (a0 + att, r0 + red)
    return out


def sample_ext(pid, addrs):
    """{function name: call count} summed over every record found."""
    out = {}
    with open("/proc/%d/mem" % pid, "rb", 0) as mem:
        for a, _ in addrs:
            mem.seek(a)
            _, _, _, used = struct.unpack("<IIII", mem.read(16))
            blob = mem.read(used * EXT_SITE)
            for i in range(used):
                rec = blob[i * EXT_SITE:(i + 1) * EXT_SITE]
                name = rec[:EXT_NAME].split(b"\0")[0].decode("ascii", "replace")
                calls = struct.unpack("<I", rec[EXT_NAME:EXT_NAME + 4])[0]
                out[name] = out.get(name, 0) + calls
    return out


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
    # The family census only exists in a MGS2_GL_CENSUS build. A production DLL
    # carries the texture-matrix record and nothing else, and that must still be
    # readable -- refusing here is how the first version of this tool made the
    # production A/B unreadable.
    print("census records found: %d" % len(addrs))
    for addr, name in addrs:
        print("  %#x  %s" % (addr, name or "(anonymous)"))

    eaddrs = find_ext_records(a.pid)
    saddrs = find_shadow_records(a.pid)
    print("per-function histogram records: %d, shadow simulator records: %d"
          % (len(eaddrs), len(saddrs)))

    f0 = frames(a.log) if a.log else None
    before = sample(a.pid, addrs)
    ebefore = sample_ext(a.pid, eaddrs) if eaddrs else {}
    sbefore = sample_shadow(a.pid, saddrs) if saddrs else {}
    a0 = read_attrib_stats(a.pid)
    t0 = read_txm_stats(a.pid)
    s0 = read_asp_stats(a.pid)
    time.sleep(a.seconds)
    after = sample(a.pid, addrs)
    eafter = sample_ext(a.pid, eaddrs) if eaddrs else {}
    safter = sample_shadow(a.pid, saddrs) if saddrs else {}
    a1 = read_attrib_stats(a.pid)
    t1 = read_txm_stats(a.pid)
    s1 = read_asp_stats(a.pid)
    f1 = frames(a.log) if a.log else None

    nframes = (f1 - f0) if (f0 is not None and f1 is not None and f1 > f0) else None
    print("\nwindow %.1f s, displayed frames %s"
          % (a.seconds, nframes if nframes else "UNKNOWN (no --log, or no stats lines)"))

    total = {}
    if addrs:
        print("\n%-24s %12s %12s %10s" % ("counter", "delta", "per second",
                                          "per frame" if nframes else ""))
    for f in FIELDS:
        d = sum(after[i][f] - before[i][f] for i in range(len(addrs)))
        total[f] = d
        if not addrs:
            continue
        per_s = d / a.seconds
        per_f = ("%10.1f" % (d / nframes)) if nframes else ""
        print("%-24s %12d %12.0f %s" % (f, d, per_s, per_f))

    if eaddrs:
        delta = {k: eafter.get(k, 0) - before_v
                 for k, before_v in ((k, ebefore.get(k, 0)) for k in eafter)}
        delta = {k: v for k, v in delta.items() if v > 0}
        tot = sum(delta.values())
        print("\nWHICH ext calls (%d distinct sites active, %d calls total)" %
              (len(delta), tot))
        print("  %-42s %10s %9s %7s" % ("function", "calls",
                                        "per frame" if nframes else "per sec", "share"))
        for k in sorted(delta, key=delta.get, reverse=True)[:22]:
            v = delta[k]
            rate = (v / nframes) if nframes else (v / a.seconds)
            print("  %-42s %10d %9.1f %6.1f%%" % (k, v, rate, 100.0 * v / tot))
        if tot and total.get("ext_calls"):
            print("  (family counter said %d; histogram sums to %d)"
                  % (total["ext_calls"], tot))

    if s1:
        def st(rs, k):
            return sum(r[k] for r in rs)
        loads = st(s1, "separable_loads") - st(s0, "separable_loads")
        nvs = st(s1, "need_vs") - st(s0, "need_vs")
        nps = st(s1, "need_ps") - st(s0, "need_ps")
        avs = st(s1, "avoided_vs") - st(s0, "avoided_vs")
        aps = st(s1, "avoided_ps") - st(s0, "avoided_ps")
        mvs = st(s1, "missed_vs") - st(s0, "missed_vs")
        print("\nSEPARABLE STAGE SELECTOR (%d record%s, lazy=%s)"
              % (len(s1), "" if len(s1) == 1 else "s",
                 "/".join(str(r["lazy"]) for r in s1)))
        print("  separable constant loads %d  -> selector calls without lazy: %d"
              % (loads, 2 * loads))
        print("  need VS %d (%.1f%%), need PS %d (%.1f%%)"
              % (nvs, 100.0 * nvs / loads if loads else 0,
                 nps, 100.0 * nps / loads if loads else 0))
        print("  avoidable: VS %d + PS %d = %d of %d (%.1f%%)"
              % (avs, aps, avs + aps, 2 * loads,
                 100.0 * (avs + aps) / (2 * loads) if loads else 0))
        if nframes:
            print("  per frame: selector calls %.1f -> %.1f, avoided %.1f"
                  % (2 * loads / nframes, (nvs + nps) / nframes,
                     (avs + aps) / nframes))
        print("  mirror self-check MISSED (must be 0): %d -- %s"
              % (mvs, "PASS" if mvs == 0 else "FAIL, run is void"))

    if t1:
        print("\nFFP TEXTURE-MATRIX PROGRAM CACHE (%d record%s: %s)"
              % (len(t1), "" if len(t1) == 1 else "s",
                 ", ".join("%s enabled=%d" % (r["where"].split("/")[-1], r["enabled"])
                           for r in t1)))
        def tot(rs, k):
            return sum(r[k] for r in rs)
        att = tot(t1, "attempted") - tot(t0, "attempted")
        skp = tot(t1, "skipped") - tot(t0, "skipped")
        exe = tot(t1, "executed") - tot(t0, "executed")
        cold = tot(t1, "cold_miss") - tot(t0, "cold_miss")
        chg = tot(t1, "changed_miss") - tot(t0, "changed_miss")
        print("  attempted %d | skipped %d (%.1f%%) | executed %d"
              % (att, skp, 100.0 * skp / att if att else 0.0, exe))
        print("  misses: cold %d, changed %d" % (cold, chg))
        if nframes:
            print("  per frame: attempted %.1f, skipped %.1f, executed %.1f"
                  % (att / nframes, skp / nframes, exe / nframes))
        print("  identity attempted == skipped + executed: %s"
              % ("PASS" if att == skp + exe else "FAIL"))
        pa = [sum(r["per_tex_attempted"][i] for r in t1)
              - sum(r["per_tex_attempted"][i] for r in t0) for i in range(TXM_TEX)]
        ps = [sum(r["per_tex_skipped"][i] for r in t1)
              - sum(r["per_tex_skipped"][i] for r in t0) for i in range(TXM_TEX)]
        live = [(i, pa[i], ps[i]) for i in range(TXM_TEX) if pa[i]]
        if live:
            print("  per texture stage: " + ", ".join(
                "%d: %d/%d" % (i, s, a) for i, a, s in live) + "  (skipped/attempted)")

    if a0 is not None and a1 is not None:
        att = a1["attempted"] - a0["attempted"]
        skp = a1["skipped"] - a0["skipped"]
        inv = a1["invalidations"] - a0["invalidations"]
        exe = att - skp
        print("\nREAL ATTRIBUTE SHADOW (enabled=%d)" % a1["enabled"])
        print("  attempted %d | skipped %d (%.1f%%) | executed %d | invalidations %d"
              % (att, skp, 100.0 * skp / att if att else 0.0, exe, inv))
        if nframes:
            print("  per frame: attempted %.1f, skipped %.1f, still executed %.1f"
                  % (att / nframes, skp / nframes, exe / nframes))
        print("  identity attempted == skipped + executed: %s"
              % ("PASS" if att == skp + exe else "FAIL"))
        misses = [(k[5:], a1[k] - a0[k]) for k in a1 if k.startswith("miss_")]
        misses = [(k, v) for k, v in misses if v]
        if misses:
            print("  what vetoed the skip: " + ", ".join(
                "%s %d (%.0f%%)" % (k, v, 100.0 * v / att) for k, v in
                sorted(misses, key=lambda kv: -kv[1])))

    if saddrs:
        print("\nSHADOW SIMULATOR -- what a real shadow WOULD have skipped")
        print("  %-34s %10s %10s %7s %10s"
              % ("site", "attempted", "redundant", "pct", "per frame"))
        tot_a = tot_r = 0
        for k in sorted(safter, key=lambda k: safter[k][1] - sbefore.get(k, (0, 0))[1],
                        reverse=True):
            att = safter[k][0] - sbefore.get(k, (0, 0))[0]
            red = safter[k][1] - sbefore.get(k, (0, 0))[1]
            if att <= 0:
                continue
            tot_a += att
            tot_r += red
            per_f = ("%10.1f" % (red / nframes)) if nframes else ""
            print("  %-34s %10d %10d %6.1f%% %s"
                  % (k[:34], att, red, 100.0 * red / att, per_f))
        if tot_a:
            print("  %-34s %10d %10d %6.1f%% %s"
                  % ("TOTAL instrumented", tot_a, tot_r, 100.0 * tot_r / tot_a,
                     ("%10.1f" % (tot_r / nframes)) if nframes else ""))
            if nframes and total.get("ext_calls"):
                print("  removable share of ALL ext calls: %.1f%%"
                      % (100.0 * tot_r / total["ext_calls"]))

    if len(addrs) > 1:
        print("\nper record (island copies are separate and MUST be summed):")
        for i, (addr, name) in enumerate(addrs):
            d = {f: after[i][f] - before[i][f] for f in FIELDS}
            live = {k: v for k, v in d.items() if v}
            print("  %#x %s" % (addr, live if live else "(idle)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

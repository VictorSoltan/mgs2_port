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
EXT_MAGIC = 0x314C4758      # 'XGL1' -- the old ext-only histogram
CALL_MAGIC = 0x324C4758     # 'XGL2' -- ext + core + project-local, by name
CALL_NAME = 48
CALL_SITE = CALL_NAME + 4
LGT_MAGIC = 0x3154474C      # 'LGT1' -- FFP light uniform redundancy simulator
LCA_MAGIC = 0x3141434C      # 'LCA1' -- the real FFP light-colour cache
UCT_MAGIC = 0x31544355      # 'UCT1' -- measured cost of one GL call on this stack
FRM_MAGIC = 0x314D5246      # 'FRM1' -- presented frames, counted in the presenter
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


def find_call_records(pid):
    """Every XGL2 record: the guest DLL and the island's copy. Both must be
    summed -- work routed natively increments the island's counters, and a
    reader that finds one copy silently under-reports exactly the paths the
    island exists to accelerate."""
    head = struct.pack("<I", CALL_MAGIC)
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
                if ver != 1 or not (1 <= cap <= 8192) or used > cap:
                    continue
                hits.append((lo + i, name))
    return hits


def sample_calls(pid, addrs):
    out = {}
    with open("/proc/%d/mem" % pid, "rb", 0) as mem:
        for a, _ in addrs:
            mem.seek(a)
            _, _, _, used = struct.unpack("<IIII", mem.read(16))
            blob = mem.read(used * CALL_SITE)
            for i in range(used):
                rec = blob[i * CALL_SITE:(i + 1) * CALL_SITE]
                name = rec[:CALL_NAME].split(b"\0")[0].decode("ascii", "replace")
                n = struct.unpack("<I", rec[CALL_NAME:CALL_NAME + 4])[0]
                out[name] = out.get(name, 0) + n
    return out


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


def read_frm_stats(pid):
    """FRM1: (presented_frames, arm, arm_frames[0], arm_frames[1], blocks)."""
    pat = struct.pack("<IIII", FRM_MAGIC, 1, 9, (~FRM_MAGIC) & 0xFFFFFFFF)
    out = []
    with open("/proc/%d/mem" % pid, "rb", 0) as mem:
        for lo, hi, nm in readable_regions(pid):
            try:
                mem.seek(lo)
                blob = mem.read(hi - lo)
            except (OSError, ValueError, OverflowError):
                continue
            i = blob.find(pat)
            while i >= 0:
                out.append(struct.unpack("<9I", blob[i:i + 36])[4:])
                i = blob.find(pat, i + 4)
    return out


def read_uct_stats(pid):
    """UCT1 v2: header, period, qpc_khz, samples[2], ticks[2] lo/hi, exec[2],
    then a 2 x 40 histogram of group durations in microseconds."""
    pat = struct.pack("<IIII", UCT_MAGIC, 2, 94, (~UCT_MAGIC) & 0xFFFFFFFF)
    out = []
    with open("/proc/%d/mem" % pid, "rb", 0) as mem:
        for lo, hi, nm in readable_regions(pid):
            try:
                mem.seek(lo)
                blob = mem.read(hi - lo)
            except (OSError, ValueError, OverflowError):
                continue
            i = blob.find(pat)
            while i >= 0:
                out.append(struct.unpack("<94I", blob[i:i + 376])[4:])
                i = blob.find(pat, i + 4)
    return out


def uct_bin_us(k):
    """Bin k covers [k, k+1) us below 32, then 32-us steps, then a tail."""
    if k < 32:
        return k + 0.5
    if k < 39:
        return 32 + (k - 32) * 32 + 16.0
    return 256.0


def uct_quantile(hist, q):
    total = sum(hist)
    if not total:
        return None
    want, seen = total * q, 0
    for k, n in enumerate(hist):
        seen += n
        if seen >= want:
            return uct_bin_us(k)
    return uct_bin_us(len(hist) - 1)


def read_lca_stats(pid):
    pat = struct.pack("<IIII", LCA_MAGIC, 1, 11, (~LCA_MAGIC) & 0xFFFFFFFF)
    out = []
    with open("/proc/%d/mem" % pid, "rb", 0) as mem:
        for lo, hi, nm in readable_regions(pid):
            try:
                mem.seek(lo)
                blob = mem.read(hi - lo)
            except (OSError, ValueError, OverflowError):
                continue
            i = blob.find(pat)
            while i >= 0:
                out.append(struct.unpack("<11I", blob[i:i + 44])[4:])
                i = blob.find(pat, i + 4)
    return out


def read_lgt_stats(pid):
    pat = struct.pack("<IIII", LGT_MAGIC, 1, 9, (~LGT_MAGIC) & 0xFFFFFFFF)
    out = []
    with open("/proc/%d/mem" % pid, "rb", 0) as mem:
        for lo, hi, nm in readable_regions(pid):
            try:
                mem.seek(lo)
                blob = mem.read(hi - lo)
            except (OSError, ValueError, OverflowError):
                continue
            i = blob.find(pat)
            while i >= 0:
                out.append(struct.unpack("<9I", blob[i:i + 36])[4:])
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
                # 4 header + enabled + attempted/skipped/executed
                # + cold/changed/resets + no_owner/owner_mismatch/location_mismatch
                # + per_tex_attempted[8] + per_tex_skipped[8].
                # The previous reader took 26 words and started per_tex at index
                # 10, which is program_cache_resets -- every per-slot figure it
                # printed was shifted by one.
                n = 14 + 2 * TXM_TEX
                if len(blob) - i < n * 4:
                    continue
                if struct.unpack_from("<I", blob, i + 8)[0] != n:
                    continue          # a record of a different vintage
                w = struct.unpack("<%dI" % n, blob[i:i + n * 4])
                out.append({
                    "addr": lo + i, "where": name or "(anon)",
                    "enabled": w[4], "attempted": w[5], "skipped": w[6],
                    "executed": w[7], "cold_miss": w[8], "changed_miss": w[9],
                    "resets": w[10], "no_owner": w[11],
                    "owner_mismatch": w[12], "location_mismatch": w[13],
                    "per_tex_attempted": list(w[14:14 + TXM_TEX]),
                    "per_tex_skipped": list(w[14 + TXM_TEX:14 + 2 * TXM_TEX]),
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

    caddrs = find_call_records(a.pid)
    eaddrs = find_ext_records(a.pid)
    saddrs = find_shadow_records(a.pid)
    print("per-function histogram records: %d, shadow simulator records: %d"
          % (len(eaddrs), len(saddrs)))

    f0 = frames(a.log) if a.log else None
    r0 = read_frm_stats(a.pid)
    before = sample(a.pid, addrs)
    ebefore = sample_ext(a.pid, eaddrs) if eaddrs else {}
    cbefore = sample_calls(a.pid, caddrs) if caddrs else {}
    sbefore = sample_shadow(a.pid, saddrs) if saddrs else {}
    a0 = read_attrib_stats(a.pid)
    t0 = read_txm_stats(a.pid)
    l0 = read_lgt_stats(a.pid)
    k0 = read_lca_stats(a.pid)
    u0 = read_uct_stats(a.pid)
    s0 = read_asp_stats(a.pid)
    time.sleep(a.seconds)
    after = sample(a.pid, addrs)
    eafter = sample_ext(a.pid, eaddrs) if eaddrs else {}
    cafter = sample_calls(a.pid, caddrs) if caddrs else {}
    safter = sample_shadow(a.pid, saddrs) if saddrs else {}
    a1 = read_attrib_stats(a.pid)
    t1 = read_txm_stats(a.pid)
    l1 = read_lgt_stats(a.pid)
    k1 = read_lca_stats(a.pid)
    u1 = read_uct_stats(a.pid)
    s1 = read_asp_stats(a.pid)
    f1 = frames(a.log) if a.log else None
    r1 = read_frm_stats(a.pid)

    # FRM1 first. The log-derived count is a step function -- the presenter emits
    # one line per N frames -- so a window that spans k lines always reports k*N
    # frames regardless of its real length. It stays only as a fallback, and says
    # so out loud when it is used.
    armf = None
    if r0 and r1:
        nframes = sum(x[0] for x in r1) - sum(x[0] for x in r0)
        armf = [sum(x[2 + i] for x in r1) - sum(x[2 + i] for x in r0) for i in (0, 1)]
        if nframes <= 0:
            nframes = None
        print("frame denominator: FRM1, %s frames presented (arm A %s / arm B %s)"
              % (nframes, armf[0] if armf else "-", armf[1] if armf else "-"))
    else:
        nframes = (f1 - f0) if (f0 is not None and f1 is not None and f1 > f0) else None
        if nframes:
            print("frame denominator: GAME LOG, %d frames -- APPROXIMATE, the log "
                  "counts in steps of the stats interval; rebuild with FRM1"
                  % nframes)
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

    if k0 and k1:
        f = lambda rs, i: sum(r[i] for r in rs)
        att = f(k1, 1) - f(k0, 1); skp = f(k1, 2) - f(k0, 2)
        exe = f(k1, 3) - f(k0, 3); cold = f(k1, 4) - f(k0, 4)
        chg = f(k1, 5) - f(k0, 5); noo = f(k1, 6) - f(k0, 6)
        print("\nREAL FFP LIGHT CACHE (%d records, enabled=%s)"
              % (len(k1), "/".join(str(r[0]) for r in k1)))
        print("  attempted %d | skipped %d (%.1f%%) | executed %d"
              % (att, skp, 100.0 * skp / att if att else 0, exe))
        print("  misses: cold %d, changed %d, no owner %d" % (cold, chg, noo))
        if nframes:
            # One skip = one glUniform4fv not made. It was three while the cache
            # was all-or-nothing per light; per-field counting makes it one.
            print("  per frame: attempted %.1f, skipped %.1f (= GL calls removed)"
                  % (att / nframes, skp / nframes))
        print("  identity attempted == skipped + executed: %s"
              % ("PASS" if att == skp + exe else "FAIL"))

    if u1:
        # EVERYTHING here is windowed, and it has to be: the histogram was
        # already windowed while samples/ticks/exec were not, so the median
        # difference (this window) was being divided by uploads-per-group that
        # could carry the whole life of the process. A mixed pair like that is
        # wrong even when the two happen to agree.
        khz = max(r[1] for r in u1) or 1
        per = max(r[0] for r in u1)

        def d32(i):
            return sum(r[i] for r in u1) - (sum(r[i] for r in u0) if u0 else 0)

        def d64(lo, hi):
            f = lambda rs: sum(r[lo] + (r[hi] << 32) for r in rs)
            return f(u1) - (f(u0) if u0 else 0)

        s_a, s_b = d32(2), d32(3)
        t_a, t_b = d64(4, 6), d64(5, 7)
        e_a, e_b = d32(8), d32(9)
        h_a = [d32(10 + k) for k in range(40)]
        h_b = [d32(50 + k) for k in range(40)]
        print("\nMEASURED GL CALL COST (%d records, 1 group in %d timed, this window)"
              % (len(u1), per))
        if s_a and s_b:
            us = lambda t, n: 1000.0 * t / khz / n     # ticks -> us per sample
            ca, cb = us(t_a, s_a), us(t_b, s_b)
            ea, eb = e_a / float(s_a), e_b / float(s_b)
            ma, mb = uct_quantile(h_a, 0.5), uct_quantile(h_b, 0.5)
            print("  arm A (cache off): %6d groups, median %s us, mean %7.3f us, "
                  "%.3f uploads/group"
                  % (s_a, "%.1f" % ma if ma is not None else "-", ca, ea))
            print("  arm B (cache on):  %6d groups, median %s us, mean %7.3f us, "
                  "%.3f uploads/group"
                  % (s_b, "%.1f" % mb if mb is not None else "-", cb, eb))
            if ma is not None and mb is not None and ea - eb > 0.01:
                cost = (ma - mb) / (ea - eb)
                mean_cost = (ca - cb) / (ea - eb)
                # Not "the cost of a GL call". It is the saving per skipped
                # upload for THIS uniform on THIS path: the difference also
                # carries the surrounding cache, branch and control-flow effect,
                # and another entry point -- glUniformMatrix4fv, glBindTexture,
                # glActiveShaderProgram -- can cost the driver something else
                # entirely. Do not carry this number to another candidate;
                # measure that candidate the same way.
                print("  => saving per skipped light glUniform4fv on this path: "
                      "%+.3f us (median)" % cost)
                print("     the mean says %+.3f us and is only diagnostic: one "
                      "preemption inside a 20 us group moves it by microseconds"
                      % mean_cost)
                if armf and armf[1] and k0 and k1:
                    skipped = sum(r[2] for r in k1) - sum(r[2] for r in k0)
                    # Only the enabled arm ever skips, so the steady-state rate is
                    # skips divided by the frames that arm actually ran -- from
                    # FRM1. Scaling by a ratio of TIMER SAMPLES was wrong: those
                    # count timed groups, not frames, and a fixed sampling period
                    # against a fixed A/B block length can sit at any phase.
                    sfr = skipped / float(armf[1])
                    print("  => %.0f calls/frame removed steady (%d skips over "
                          "%d arm-B frames) = %.2f ms/frame"
                          % (sfr, skipped, armf[1], sfr * cost / 1000.0))
                elif k0 and k1:
                    print("  (no FRM1 arm frame counts: cannot state a steady rate)")
            else:
                print("  arms uploaded the same amount: nothing to divide by")

    if l0 and l1:
        # Windowed, like every other counter here. Printing this one cumulatively
        # was how a two-minute simulator delta got compared against a twenty-second
        # histogram delta and produced an impossible ratio.
        att = sum(r[0] for r in l1) - sum(r[0] for r in l0)
        red = sum(r[1] for r in l1) - sum(r[1] for r in l0)
        cold = sum(r[2] for r in l1) - sum(r[2] for r in l0)
        chg = sum(r[3] for r in l1) - sum(r[3] for r in l0)
        full = sum(r[4] for r in l1) - sum(r[4] for r in l0)
        print("\nFFP LIGHT UNIFORM SIMULATOR (%d records, this window)" % len(l1))
        print("  attempted %d | redundant %d (%.1f%%) | cold %d | changed %d | table full %d"
              % (att, red, 100.0 * red / att if att else 0, cold, chg, full))
        if nframes:
            print("  per frame: attempted %.1f, removable %.1f"
                  % (att / nframes, red / nframes))
        print("  key is (vs_program_id, light, field) -- what GL attributes the")
        print("  state to. Covers the three unconditional colour uniforms per")
        print("  light (diffuse/specular/ambient), not the type-specific ones.")

    if caddrs:
        d = {k: cafter[k] - cbefore.get(k, 0) for k in cafter}
        d = {k: v for k, v in d.items() if v > 0}
        tot = sum(d.values())
        fam = {}
        for k, v in d.items():
            fam[k.split(":", 1)[0]] = fam.get(k.split(":", 1)[0], 0) + v
        print("\nALL GL CALLS BY NAME (%d records, %d live sites, %d calls)"
              % (len(caddrs), len(d), tot))
        print("  by family: " + ", ".join(
            "%s %d (%.1f%%)%s" % (k, v, 100.0 * v / tot,
                                  "  %.1f/frame" % (v / nframes) if nframes else "")
            for k, v in sorted(fam.items(), key=lambda kv: -kv[1])))
        print("  %-46s %10s %9s %6s" % ("call", "count",
                                        "per frame" if nframes else "per sec", "share"))
        for k in sorted(d, key=d.get, reverse=True)[:24]:
            v = d[k]
            rate = (v / nframes) if nframes else (v / a.seconds)
            print("  %-46s %10d %9.1f %5.1f%%" % (k, v, rate, 100.0 * v / tot))

    if s1:
        def st(rs, k):
            return sum(r[k] for r in rs)
        loads = st(s1, "separable_loads") - st(s0, "separable_loads")
        nvs = st(s1, "need_vs") - st(s0, "need_vs")
        nps = st(s1, "need_ps") - st(s0, "need_ps")
        avs = st(s1, "avoided_vs") - st(s0, "avoided_vs")
        aps = st(s1, "avoided_ps") - st(s0, "avoided_ps")
        mvs = st(s1, "missed_vs") - st(s0, "missed_vs")
        mps = st(s1, "missed_ps") - st(s0, "missed_ps")
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
        print("  mirror self-check MISSED (both must be 0): VS %d, PS %d -- %s"
              % (mvs, mps, "PASS" if not (mvs or mps) else "FAIL, run is void"))

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
        rst = tot(t1, "resets") - tot(t0, "resets")
        noo = tot(t1, "no_owner") - tot(t0, "no_owner")
        own = tot(t1, "owner_mismatch") - tot(t0, "owner_mismatch")
        loc = tot(t1, "location_mismatch") - tot(t0, "location_mismatch")
        # "resets" fires once per source on first touch, not on a relink: a
        # source is assigned a program exactly once and is freed with it.
        print("  misses: cold %d, changed %d, first-touch stamps %d" % (cold, chg, rst))
        # The vetoes are the correctness readout. P74A shipped a cache whose
        # owner was wrong and the only symptom was the picture jumping; here the
        # same mistake shows up as a number before anyone has to look at a frame.
        print("  vetoes: no owner %d, owner mismatch %d, location mismatch %d%s"
              % (noo, own, loc,
                 "" if not (own or loc) else "   <- INVESTIGATE, the cache is "
                 "being offered to programs it does not own"))
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

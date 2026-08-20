#!/usr/bin/env python3
"""Cycle-weighted Box86 guest profile. Reuses the archive's guest-map reader."""
import argparse, bisect, collections, pathlib, re, struct, sys
sys.path.insert(0, "harness")
import importlib.util
spec = importlib.util.spec_from_file_location("bgp", "harness/box86_guest_profile.py")
bgp = importlib.util.module_from_spec(spec); spec.loader.exec_module(bgp)

# perf on ROCKNIX normally prints ``comm tid ...`` but explicit field selection
# may produce ``comm pid/tid ...``. Keep this reader aligned with the sample
# reader: an offline capture must not depend on perf's display choice.
LINE = re.compile(
    r"^\s*(\S+)\s+(?:(\d+)/)?(\d+)\s+([0-9.]+):\s+(\d+)\s+"
    r"cycles:u:\s+([0-9a-fA-F]+)\s+(.*?)\s+\(([^)]*)\)\s*$"
)

ap = argparse.ArgumentParser()
ap.add_argument("--guest-map", required=True)
ap.add_argument("--script", required=True)
ap.add_argument("--maps", required=True)
ap.add_argument("--module", default=None, help="substring filter on resolved guest module")
ap.add_argument("--limit", type=int, default=30)
a = ap.parse_args()

records, meta = bgp.read_guest_map(a.guest_map)
mappings, pe_spans = bgp.read_process_maps(a.maps)
nstarts = [r[0] for r in records]
mstarts = [m[0] for m in mappings]
pstarts = [p[0] for p in pe_spans]

total_cycles = 0
jit_cycles = 0
blocks = collections.Counter(); bsmp = collections.Counter()
bthread = collections.defaultdict(collections.Counter)
modules = collections.Counter()
dsos = collections.Counter()
unres = 0
for l in pathlib.Path(a.script).read_text(errors="replace").splitlines():
    m = LINE.match(l)
    if not m: continue
    comm, _pid, tid, ts, per, ip, sym, dso = m.groups()
    per = int(per); total_cycles += per
    dsos[dso] += per
    if not dso.startswith("/tmp/perf-"): continue
    rec = bgp.containing(records, nstarts, int(ip, 16))
    if rec is None:
        unres += per; continue
    _ns, _nz, x86, xz = rec
    blocks[(x86, xz)] += per; bsmp[(x86, xz)] += 1
    bthread[(x86, xz)][f"{comm}:{tid}"] += per
    mod, _ = bgp.resolve_module(mappings, mstarts, pe_spans, pstarts, x86)
    modules[mod] += per
    jit_cycles += per

print(f"total_user_cycles={total_cycles:,}  jit_cycles={jit_cycles:,} "
      f"({100*jit_cycles/total_cycles:.2f}%)  unresolved_jit_cycles={unres:,}")
print("\nNative and JIT DSOs (cycle-weighted, % of ALL user cycles):")
for dso, c in dsos.most_common(20):
    print(f"  {100*c/total_cycles:6.2f}%  {c:>14,}  {dso}")
print("\nGuest modules (cycle-weighted, % of ALL user cycles):")
for mod, c in modules.most_common(20):
    print(f"  {100*c/total_cycles:6.2f}%  {c:>14,}  {mod}")

print(f"\nGuest blocks{' in '+a.module if a.module else ''} "
      f"(cycle-weighted, % of ALL user cycles):")
shown = 0
for (x86, xz), c in blocks.most_common():
    mod, rva = bgp.resolve_module(mappings, mstarts, pe_spans, pstarts, x86)
    if a.module and a.module not in mod: continue
    th = bthread[(x86, xz)].most_common(1)[0][0]
    print(f"  {100*c/total_cycles:6.3f}%  {c:>13,}  {bsmp[(x86,xz)]:5d} smp  "
          f"x86={x86:#010x}+{xz:#x} rva={rva:#x}  [{th}]  {mod.split('/')[-1]}")
    shown += 1
    if shown >= a.limit: break

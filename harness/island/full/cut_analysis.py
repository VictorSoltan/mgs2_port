#!/usr/bin/env python3
"""Which functions of the ARM WineD3D island touch which writable globals.

MUST be run on objects built with -fno-pic. With PIC, ARM addresses data through
PC-relative literal pools and the relocation names the *section* with the addend
buried in the literal word, so every data reference is invisible to this kind of
analysis. Two earlier versions of this script reported clean cuts that were
simply blind -- the tell was that mgs2_batch, which mgs2_batch_flush obviously
touches, appeared in no reference set at all.

Always check that control before trusting a result:
    functions referencing mgs2_batch -> draw_primitive, mgs2_batch_flush

Relocations must be attributed by address range, not by the last seen function
label. ARM addresses data through PC-relative literal pools, and the relocation
sits on the literal word at the end of the function body -- attributing it to
whatever label was seen last silently loses every data reference, which is how an
earlier version of this analysis reported five shared globals instead of the real
number."""
import subprocess, re, collections, pathlib, bisect, sys

objdir = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "armobj2")
refs = collections.defaultdict(set); funcs = set(); gvars = {}; owner = {}
for o in sorted(objdir.glob("*.o")):
    t = subprocess.run(["arm-linux-gnueabihf-objdump", "-t", str(o)],
                       capture_output=True, text=True).stdout
    ranges = []                      # (start, end, name) for functions
    for l in t.splitlines():
        m = re.match(r"^([0-9a-f]{8})\s+(\S+)\s+(\S+)\s+(\S+)\s+([0-9a-f]+)\s+(\S+)$", l)
        if not m: continue
        val, typ, sec, size, name = (int(m.group(1),16), m.group(3), m.group(4),
                                     int(m.group(5),16), m.group(6))
        if typ == "F" and sec.startswith(".text"):
            funcs.add(name); owner[name] = o.stem; ranges.append((val, val+max(size,1), name))
        elif typ == "O" and sec.startswith((".bss", ".data")):
            gvars[name] = (o.stem, size)
    ranges.sort(); starts = [r[0] for r in ranges]
    # relocations, with their own offsets, mapped into the enclosing function
    r = subprocess.run(["arm-linux-gnueabihf-objdump", "-r", str(o)],
                       capture_output=True, text=True).stdout
    sec = None
    for l in r.splitlines():
        m = re.match(r"^RELOCATION RECORDS FOR \[([^\]]+)\]", l)
        if m: sec = m.group(1); continue
        m = re.match(r"^([0-9a-f]{8})\s+(\S+)\s+([^\s+-]+)", l)
        if not m or not sec or not sec.startswith(".text"): continue
        off, tgt = int(m.group(1), 16), m.group(3)
        i = bisect.bisect_right(starts, off) - 1
        if i >= 0 and off < ranges[i][1]:
            refs[ranges[i][2]].add(tgt)
print(f"functions {len(funcs)}  writable globals {len(gvars)}  "
      f"functions with references {len(refs)}")
mb = [f for f in refs if "mgs2_batch" in refs[f]]
print(f"functions referencing mgs2_batch: {len(mb)}  {' '.join(sorted(mb)[:6])}")
def closure(roots):
    seen=set(roots); st=list(roots)
    while st:
        n=st.pop()
        for x in refs.get(n,()):
            if x in funcs and x not in seen: seen.add(x); st.append(x)
    return seen
HOT=[r for r in ["draw_primitive","mgs2_batch_flush","shader_glsl_apply_draw_state",
                 "shader_glsl_load_constants","wined3d_ffp_get_fs_settings",
                 "wined3d_cs_exec_draw_one"] if r in funcs]
N=closure(HOT)
G=sorted({g for n in N for g in refs.get(n,()) if g in gvars})
print(f"\ndraw-path closure {len(N)} functions, touches {len(G)} writable globals")
ext=set(pathlib.Path("stublist2.txt").read_text().split()) if pathlib.Path("stublist2.txt").exists() else set()
win={s for s in ext if not s.startswith(("gl","wgl","egl","vkd3d","vk","__wine_dbg"))}
hotwin=sorted({w for n in N for w in refs.get(n,()) if w in win})
print(f"Win32 reachable from the draw path: {len(hotwin)} of {len(win)}")
for w in hotwin[:15]: print(f"   {w}")

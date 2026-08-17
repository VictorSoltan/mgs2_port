#!/usr/bin/env python3
"""Do WineD3D's ops-table targets have ARM counterparts in the island?

island_reach.py counts indirect call sites but cannot say where they go, and a
review correctly pointed out that "indirect" was being read as "must re-enter
the emulator". Most of WineD3D's indirect dispatch is its own backend model:

    buffer->buffer_ops->buffer_prepare_location(...)
        -> wined3d_buffer_gl_prepare_location, in buffer.c
    texture->texture_ops->texture_load_location(...)
        -> texture_gl_load_location, in texture_gl.c

Both of those files are among the 32 the island already compiles for ARM, so
the target is not a foreign x86 callback -- it is a function the island has its
own native copy of. This enumerates every ops-table initialiser in the WineD3D
sources and checks each named target against the linked ARM binary's symbols.

This is a STATIC upper bound on what a runtime resolver could redirect without
entering the emulator. It does not prove any particular call site takes one of
these targets; only the runtime census can do that. It answers the narrower
question the review raised: is there an ARM counterpart to redirect *to*.

usage: island_ops_targets.py <unstripped box86 with the island> [wined3d src dir]
"""
import re
import subprocess
import sys

OPS_BLOCK = re.compile(
    r"static\s+const\s+struct\s+(\w*_ops)\s+(\w+)\s*=\s*\{(.*?)\n\};",
    re.S)
IDENT = re.compile(r"^\s*(?:\.\w+\s*=\s*)?(\w+)\s*,?\s*(?:/\*.*?\*/)?\s*$")


def arm_symbols(binary):
    out = subprocess.run(["readelf", "-sW", binary], capture_output=True, text=True).stdout
    names = set()
    for line in out.splitlines():
        f = line.split()
        if len(f) >= 8 and f[3] == "FUNC":
            names.add(f[7])
    return names


def main():
    binary = sys.argv[1]
    src = sys.argv[2] if len(sys.argv) > 2 else \
        "/mnt/data/holden/mgs/recovered-session/wine-11.0/dlls/wined3d"

    syms = arm_symbols(binary)
    import glob
    import os

    tables, present, missing = [], [], []
    for path in sorted(glob.glob(os.path.join(src, "*.c"))):
        text = open(path, encoding="utf-8", errors="replace").read()
        for kind, name, body in OPS_BLOCK.findall(text):
            targets = []
            for line in body.splitlines():
                m = IDENT.match(line)
                if m and not m.group(1).isdigit():
                    targets.append(m.group(1))
            if not targets:
                continue
            tables.append((os.path.basename(path), kind, name, targets))
            for t in targets:
                (present if t in syms else missing).append((name, t))

    print(f"{len(tables)} ops tables in {os.path.basename(src)}/*.c\n")
    for f, kind, name, targets in tables:
        hit = sum(1 for t in targets if t in syms)
        flag = "" if hit == len(targets) else "   <-- INCOMPLETE"
        print(f"  {f:<22} {name:<38} {hit}/{len(targets)} native{flag}")

    total = len(present) + len(missing)
    print(f"\ntargets named in ops tables      {total}")
    print(f"  present as ARM symbols         {len(present)}")
    print(f"  absent                         {len(missing)}")
    if missing:
        print("\nabsent targets (these would still need the emulator):")
        for name, t in sorted(set(missing)):
            print(f"  {name}: {t}")

    # Control check: buffer and texture GL dispatch is the case the review named,
    # so it must appear and must resolve. If it does not, the parser is not
    # finding the tables and the counts above mean nothing.
    named = {t for _, t in present} | {t for _, t in missing}
    control = {"wined3d_buffer_gl_prepare_location", "wined3d_buffer_gl_unload_location"}
    ok = control <= named and control <= syms
    print("\ncontrol check (buffer_gl ops found and native): "
          + ("PASS" if ok else "FAIL -- ops tables are not being parsed, ignore the counts"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

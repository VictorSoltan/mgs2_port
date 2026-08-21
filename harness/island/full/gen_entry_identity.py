#!/usr/bin/env python3
"""Emit the canonical identity of every island entry, from the shipped DLL.

WHY

Box86 used to decide "this address is island entry N" by scanning 64 bytes from
whatever address the dynarec was translating and taking the first marker it
found. That makes the marker the IDENTITY, and it is not sound: on 2026-08-19
production entry 22 was found bound to 0x7b919f23, which is 0xe3 bytes INSIDE the
function before it -- the window reached forward 54 bytes into the next
function's marker. The first match publishes, so the real entry point could never
route afterwards.

The invariant should be the other way round:

    identity  =  module base + the function's canonical RVA
    marker    =  a witness that the binary is the expected one

This tool provides the canonical half. For every marker in the DLL it reports the
function that contains it and the marker's offset inside that function, so Box86
can require the offset (and, once the class-B module base is known, the RVA) and
reject a mid-function or neighbouring-function match.

HOW, WITHOUT A SYMBOL TABLE

The shipped DLL is stripped, so function boundaries come from .eh_frame FDEs --
objdump --dwarf=frames prints `pc=lo..hi` for each. That is the same information
a symbol table would give for this purpose and it is present in the binary that
actually runs, which is the one that matters: an entry's RVA must come from the
DLL being mounted, not from a rebuild.

usage: gen_entry_identity.py <mounted wined3d.dll> [-o header] [--objdump CMD]
       [--require-id N ...]
"""
import argparse
import bisect
import collections
import os
import re
import struct
import subprocess
import sys

MARKER = bytes.fromhex("0f1f84004d4753")


def sections(path, objdump):
    out = subprocess.run([objdump, "-h", path], capture_output=True, text=True).stdout
    secs = []
    for line in out.splitlines():
        m = re.match(r"\s*\d+\s+(\S+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)", line)
        if m:
            secs.append(dict(name=m.group(1), size=int(m.group(2), 16),
                             vma=int(m.group(3), 16), foff=int(m.group(5), 16)))
    if not secs:
        sys.exit("no sections; is %s the right objdump for this file?" % objdump)
    return secs


def image_base(path):
    d = open(path, "rb").read(0x400)
    pe = struct.unpack_from("<I", d, 0x3c)[0]
    magic = struct.unpack_from("<H", d, pe + 24)[0]
    off = pe + 24 + (28 if magic == 0x10b else 24)
    return struct.unpack_from("<I", d, off)[0]


def fdes(path, objdump):
    out = subprocess.run([objdump, "--dwarf=frames", path],
                         capture_output=True, text=True).stdout
    got = sorted({(int(lo, 16), int(hi, 16)) for lo, hi in
                  re.findall(r"pc=([0-9a-f]+)\.\.([0-9a-f]+)", out)})
    if not got:
        sys.exit("no .eh_frame FDEs in %s -- function boundaries are unavailable,"
                 " and guessing them is not acceptable here" % path)
    return got


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dll")
    ap.add_argument("-o", "--out")
    ap.add_argument("--objdump", default="i686-w64-mingw32-objdump")
    ap.add_argument("--require-id", type=int, action="append", default=[],
                    help="limit the offset/coverage control to an armed id; repeatable")
    args = ap.parse_args()

    data = open(args.dll, "rb").read()
    secs = sections(args.dll, args.objdump)
    base = image_base(args.dll)
    text = next((s for s in secs if s["name"] == ".text"), None)
    if not text:
        sys.exit("no .text section")

    funcs = fdes(args.dll, args.objdump)
    starts = [f[0] for f in funcs]

    def owner(vma):
        i = bisect.bisect_right(starts, vma) - 1
        if i >= 0 and funcs[i][0] <= vma < funcs[i][1]:
            return funcs[i]
        return None

    occ = collections.defaultdict(list)
    i = data.find(MARKER, text["foff"])
    while i != -1 and i < text["foff"] + text["size"]:
        occ[data[i + 7]].append(text["vma"] + (i - text["foff"]))
        i = data.find(MARKER, i + 1)

    rows, notes = [], []
    for mid in sorted(occ):
        cands = []
        for vma in occ[mid]:
            f = owner(vma)
            if not f:
                notes.append("id %d: marker at %#x has no FDE -- skipped" % (mid, vma))
                continue
            cands.append((vma - f[0], f[0], vma))
        if not cands:
            continue
        # The canonical marker is the one nearest the top of its function: that is
        # the prologue copy the entry point actually reaches. A duplicate deeper in
        # (the compiler cloning the block) must never define identity.
        cands.sort()
        off, fstart, vma = cands[0]
        rows.append((mid, off, fstart - base, len(cands)))
        for off2, fstart2, vma2 in cands[1:]:
            notes.append("id %d: duplicate marker at %#x (offset %d of %#x)"
                         % (mid, vma2, off2, fstart2))

    print("image base %#x, .text at %#x, %d FDEs" % (base, text["vma"], len(funcs)))
    print("%4s %8s %10s %s" % ("id", "mrk_off", "func_rva", "note"))
    for mid, off, rva, n in rows:
        print("%4d %8d %#10x %s" % (mid, off, rva, "" if n == 1 else "%d markers" % n))
    for n in notes:
        print("  note: " + n)

    if args.out:
        with open(args.out, "w") as f:
            f.write("/* Generated by harness/island/full/gen_entry_identity.py from the\n"
                    " * MOUNTED wined3d.dll. Identity is module base + func_rva; the marker\n"
                    " * is only a witness, and it must sit at marker_off. A match at any\n"
                    " * other offset is a neighbouring or mid-function address -- see\n"
                    " * section 14 of docs/briefs/MGS2_ISLAND_ENTRY34_FAULT_2026-08-19.md,\n"
                    " * where production entry 22 was bound to one. Do not hand-edit. */\n")
            f.write("#ifndef MGS2_ISLAND_ENTRY_IDENTITY_H\n#define MGS2_ISLAND_ENTRY_IDENTITY_H\n\n")
            f.write("struct mgs2_entry_identity { unsigned short id;"
                    " unsigned short marker_off; unsigned int func_rva; };\n\n")
            f.write("static const struct mgs2_entry_identity mgs2_entry_identity[] = {\n")
            for mid, off, rva, n in rows:
                f.write("    { %3d, %3d, 0x%08x },\n" % (mid, off, rva))
            f.write("};\n")
            f.write("#define MGS2_ENTRY_IDENTITY_COUNT %d\n\n" % len(rows))
            f.write("#endif /* MGS2_ISLAND_ENTRY_IDENTITY_H */\n")
        print("\nwritten to %s" % args.out)

    # Control: the table must cover every id that has a bridge, and every offset
    # must be inside the window Box86 scans, or the entry could not have routed
    # even under the old rule. A silent empty table would read as "all clean".
    if not rows:
        print("\ncontrol check FAILED: no identities found")
        return 1
    checked = rows
    missing = []
    if args.require_id:
        by_id = {r[0]: r for r in rows}
        missing = sorted(set(args.require_id) - set(by_id))
        checked = [by_id[mid] for mid in sorted(set(args.require_id)) if mid in by_id]
    bad = [r for r in checked if r[1] > 64]
    scope = "required armed ids" if args.require_id else "identities"
    print("\ncontrol check: %d %s, %d missing, %d with marker offset beyond 64"
          % (len(checked), scope, len(missing), len(bad)))
    if missing:
        print("control check missing ids: " + ",".join(map(str, missing)))
    if bad:
        print("control check out-of-window ids: "
              + ",".join("%d(+%d)" % (r[0], r[1]) for r in bad))
    return 0 if not missing and not bad else 1


if __name__ == "__main__":
    sys.exit(main())

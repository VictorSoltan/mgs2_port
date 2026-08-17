#!/usr/bin/env python3
"""Are the island entry markers where Box86 will actually find them?

Counting marker occurrences was the old check, and it cannot tell the difference
between the case that is fatal and the case that is invisible:

  fatal      the same id appears in two DIFFERENT functions -- calling either
             routes it to the same native implementation, and one of them is the
             wrong function
  harmless   the same id appears twice in ONE function, because the compiler
             duplicated the basic block holding the inline asm. Box86 scans only
             the first 17 bytes from a call target, so it never sees the second

There is a third failure the count check misses entirely: a marker that sits
PAST byte 16 of its own function is outside the matcher's window, so that entry
silently never routes and the island quietly does less than it claims.

This checks all three, against the built i386 DLL's symbol table.

usage: island_marker_check.py <unstripped wined3d.dll>
"""
import re
import subprocess
import sys

PREFIX = bytes.fromhex("0f1f84004d4753")
WINDOW = 64  # Box86 scans offsets 0..64 inclusive; see MGS2_ISLAND_WINDOW in bridge.c
OBJDUMP = "i686-w64-mingw32-objdump"
NM = "i686-w64-mingw32-nm"


def sections(path):
    out = subprocess.run([OBJDUMP, "-h", path], capture_output=True, text=True).stdout
    secs = []
    for line in out.splitlines():
        m = re.match(r"\s*\d+\s+(\S+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)", line)
        if m:
            secs.append((m.group(1), int(m.group(3), 16), int(m.group(5), 16), int(m.group(2), 16)))
    return secs


def symbols(path):
    out = subprocess.run([NM, "-n", path], capture_output=True, text=True).stdout
    syms = []
    for line in out.splitlines():
        f = line.split()
        if len(f) == 3 and f[1] in "tT" and not f[2].startswith(".text$"):
            syms.append((int(f[0], 16), f[2]))
    return sorted(syms)


def main():
    path = sys.argv[1]
    data = open(path, "rb").read()
    secs = sections(path)
    syms = symbols(path)

    def to_vma(off):
        for _, vaddr, foff, size in secs:
            if foff <= off < foff + size:
                return vaddr + (off - foff)
        return None

    def owner(vma):
        lo = None
        for addr, name in syms:
            if addr <= vma:
                lo = (addr, name)
            else:
                break
        return lo

    found = {}
    i = 0
    while True:
        i = data.find(PREFIX, i)
        if i < 0:
            break
        eid = data[i + 7]
        vma = to_vma(i)
        own = owner(vma) if vma is not None else None
        found.setdefault(eid, []).append((vma, own))
        i += 1

    bad_function, bad_window, ok = [], [], []
    for eid, hits in sorted(found.items()):
        names = {o[1] for _, o in hits if o}
        first = min(hits, key=lambda h: h[0] - h[1][0] if h[1] else 1 << 30)
        offset = first[0] - first[1][0] if first[1] else None
        name = first[1][1] if first[1] else "?"
        if len(names) > 1:
            bad_function.append((eid, sorted(names)))
        elif offset is None or offset > WINDOW:
            bad_window.append((eid, name, offset))
        else:
            ok.append((eid, name, offset, len(hits)))

    print(f"{len(found)} distinct ids, {sum(len(v) for v in found.values())} occurrences\n")
    for eid, name, offset, n in ok:
        extra = f"  ({n} occurrences, only the first is in the window)" if n > 1 else ""
        print(f"  0x{eid:02x}  +{offset:<3} {name}{extra}")

    if bad_function:
        print("\nFATAL -- one id in more than one function, so a call to the wrong")
        print("one routes to the right island entry:")
        for eid, names in bad_function:
            print(f"  0x{eid:02x}: {', '.join(names)}")
    if bad_window:
        print(f"\nFATAL -- marker past byte {WINDOW}, so Box86 never matches this entry")
        print("and it silently stays emulated:")
        for eid, name, offset in bad_window:
            print(f"  0x{eid:02x}: {name} at +{offset}")

    bad = bool(bad_function or bad_window)
    print("\ncontrol check: " + ("FAIL" if bad else "PASS -- every id is in exactly one "
                                 "function and inside the matcher's window"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

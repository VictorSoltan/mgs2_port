#!/usr/bin/env python3
"""Are the island entry markers where Box86 will actually find them?

Counting marker occurrences was the old check, and it cannot tell the difference
between the case that is fatal and the case that is invisible:

  fatal      the same id appears in two DIFFERENT functions -- calling either
             routes it to the same native implementation, and one of them is the
             wrong function
  reported   a DIFFERENT function starts within the matcher's window ahead of a
             marker.  Box86 scans forward from the branch target, so calling
             that neighbour DOES match a marker it does not own -- this is what
             bound production entry 22 to a mid-function address on 2026-08-19.
             It is fatal only for an id with no canonical identity: with one,
             Box86 requires module base + func_rva and rejects the neighbour,
             so the pair is reported and the id is not disarmed
  harmless   the same id appears twice in ONE function, because the compiler
             duplicated the basic block holding the inline asm. Box86 scans only
             the first 17 bytes from a call target, so it never sees the second

There is a third failure the count check misses entirely: a marker that sits
PAST byte 16 of its own function is outside the matcher's window, so that entry
silently never routes and the island quietly does less than it claims.

This checks all three, against the built i386 DLL's symbol table.

SEVERITY DEPENDS ON THE CONFIGURATION BEING PREPARED

An id that no launcher arms cannot mis-route anything, and three such cases are
already recorded for this DLL family (id 20 duplicated across two functions, ids
11 and 34 with a marker past the window). Printing them as FATAL trains the
operator to read past FATAL, so pass --armed with the run's entry list: findings
for ids outside it are reported as IGNORED and do not affect the exit code.
Without --armed every finding stays fatal, which is the safe default for an
unknown configuration.

--target NAME asserts the invariant a symmetric A/B control arm needs: the guest
function the control arm calls must have NO marker in its own 64-byte window, so
its safety does not depend on the canonical-RVA identity being established yet.

usage: island_marker_check.py <unstripped wined3d.dll> [--identity HEADER]
                              [--armed 0,1,2,...] [--target SYMBOL ...]
"""
import argparse
import re
import subprocess
import sys

PREFIX = bytes.fromhex("0f1f84004d4753")
IDENTITY = "/mnt/data/holden/mgs/box86-src/src/mgs2_island_entry_identity.h"

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


def protected_ids(path):
    """Ids whose identity Box86 checks as module base + canonical RVA."""
    try:
        text = open(path).read()
    except OSError:
        return None
    return {int(m.group(1)) for m in re.finditer(r"\{\s*(\d+),\s*\d+,\s*0x[0-9a-fA-F]+\s*\}", text)}


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("dll")
    ap.add_argument("--identity", default=IDENTITY)
    ap.add_argument("--armed", help="comma-separated ids this configuration arms")
    ap.add_argument("--target", action="append", default=[],
                    help="symbol whose own window must contain no marker; repeatable")
    args = ap.parse_args()
    path = args.dll
    identity = protected_ids(args.identity)
    armed = ({int(part, 0) for part in args.armed.replace(",", " ").split()}
             if args.armed else None)
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

    # Neighbours: any other function whose own scan window reaches into a
    # marker.  This is not a property of the marker's owner, so the two checks
    # below cannot see it; it was found by building a p70b control arm that
    # linked 16 bytes ahead of entry 0x28's marker.
    sym_starts = [addr for addr, _name in syms]
    neighbours = []
    for eid, hits in sorted(found.items()):
        for vma, own in hits:
            if vma is None or not own:
                continue
            for addr, name in syms:
                # Only functions starting BEFORE the marker's own function can
                # reach it: owner() already picked the closest symbol at or
                # below the marker, so nothing starts in between.
                if addr >= own[0] or vma - addr > WINDOW:
                    continue
                neighbours.append((eid, name, own[1], vma - addr))

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

    def relevant(eid):
        """Is a finding for this id fatal for the configuration being checked?"""
        return armed is None or eid in armed

    # The control arm of a symmetric A/B must not sit in any marker's window.
    target_hits = []
    for name in args.target:
        matches = [addr for addr, sym in syms if sym in (name, "_" + name)]
        if not matches:
            target_hits.append((name, None, None))
            continue
        start = matches[0]
        inside = [(vma, eid) for eid, hits in found.items() for vma, _own in hits
                  if vma is not None and start <= vma <= start + WINDOW]
        target_hits.append((name, start, inside))

    print(f"{len(found)} distinct ids, {sum(len(v) for v in found.values())} occurrences\n")
    for eid, name, offset, n in ok:
        extra = f"  ({n} occurrences, only the first is in the window)" if n > 1 else ""
        print(f"  0x{eid:02x}  +{offset:<3} {name}{extra}")

    def label(eid):
        return "FATAL" if relevant(eid) else "IGNORED (id not armed here)"

    if bad_function:
        print("\nONE ID IN MORE THAN ONE FUNCTION -- a call to the wrong one routes to")
        print("the right island entry:")
        for eid, names in bad_function:
            print(f"  0x{eid:02x}: {', '.join(names)}  -- {label(eid)}")
    if bad_window:
        print(f"\nMARKER PAST BYTE {WINDOW} -- Box86 never matches this entry and it")
        print("silently stays emulated:")
        for eid, name, offset in bad_window:
            print(f"  0x{eid:02x}: {name} at +{offset}  -- {label(eid)}")

    unprotected = [n for n in neighbours
                   if identity is not None and n[0] not in identity and relevant(n[0])]
    if neighbours:
        print(f"\nREPORTED -- another function starts within {WINDOW} bytes ahead of a")
        print("marker, so calling it matches an id it does not own. Box86 rejects the")
        print("match when the id has a canonical identity:")
        for eid, name, own, distance in neighbours:
            if identity is None:
                state = "identity table unavailable"
            else:
                state = "protected by canonical RVA" if eid in identity else "NOT PROTECTED"
            print(f"  0x{eid:02x}: {name} is {distance} bytes ahead of {own}'s marker"
                  f"  -- {state}")
    if unprotected:
        print("\nFATAL -- a neighbour can claim these ids: they have no canonical")
        print("identity, so the first marker match publishes and wins:")
        for eid, name, own, _distance in unprotected:
            print(f"  0x{eid:02x}: {name} can claim {own}")

    if args.target:
        print("\nCONTROL-ARM TARGETS -- a marker inside one of these windows would")
        print("route the control arm as well:")
        for name, start, inside in target_hits:
            if start is None:
                print(f"  {name}: NOT FOUND in the symbol table -- FATAL")
            elif inside:
                hits = ", ".join(f"0x{eid:02x}@+{vma - start}" for vma, eid in inside)
                print(f"  {name} @ {start:#x}: {hits} -- FATAL")
            else:
                print(f"  {name} @ {start:#x}: no marker in +0..{WINDOW} -- PASS")

    bad_targets = [name for name, start, inside in target_hits if start is None or inside]
    bad = bool([e for e, _n in bad_function if relevant(e)]
               or [e for e, _n, _o in bad_window if relevant(e)]
               or unprotected or bad_targets)
    scope = "armed ids " + ",".join(str(e) for e in sorted(armed)) if armed else "every id"
    print(f"\ncontrol check ({scope}): " + ("FAIL" if bad else
          "PASS -- each checked id is in exactly one function, inside the matcher's "
          "window, identity-protected against any neighbour, and every named "
          "control-arm target has a marker-free window"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Which island entry points can reach an abort stub, and which make indirect calls.

The island links all 32 WineD3D objects into Box86 and arms 37 entry points.
Arming is all-or-nothing, so a single entry that reaches a Win32 abort stub
takes the whole run down and names only the stub. This walks the direct call
graph of the linked ARM binary from each entry and reports, per entry:

  stubs      abort stubs reachable through direct calls
  indirect   functions in the closure that call through a register

Both matter, and for different reasons. A reachable stub is a build-time fact:
that entry aborts as soon as the path is taken. An indirect call is a risk, not
a verdict -- WineD3D reaches GL and its object ops through pointers held in
guest structures, and those hold x86 addresses or Box86 bridges, which native
ARM code cannot call. This analysis cannot follow them, and says so rather than
implying the closure is complete.

Control check (printed): wined3d_release_dc must report WindowFromDC and
ReleaseDC. It is the entry that actually aborted on the device on 2026-08-15,
so if it comes back clean the graph is not being built.

usage: island_reach.py <unstripped box86 with the island linked in>
"""
import collections
import re
import subprocess
import sys

OBJDUMP = "arm-linux-gnueabihf-objdump"
READELF = "readelf"

# One disassembly line: address, the encoding column, mnemonic, operands. The
# encoding column is one 8-hex word in ARM state and one or two 4-hex halfwords
# in Thumb, so it cannot be matched with a fixed width -- an earlier version
# matched only the Thumb form, found no calls at all, and was caught by the
# control check rather than believed.
LINE = re.compile(r"^\s*([0-9a-f]+):\s+((?:[0-9a-f]{4,8}\s+)+)\t?\s*(\S+)\s*(.*)$")
# Branch-and-link and tail-call branches to an absolute target.
CALL_MNEMONIC = re.compile(r"^(bl|blx|b|bx)(\.[nw])?$")
TARGET = re.compile(r"^([0-9a-f]+)\b")
# Register forms: not followed, only counted. `bx lr` is a function return, not
# an indirect call, and counting it added a phantom call site to every leaf --
# enough to move the headline "entries free of indirect calls" number. Excluded.
REGISTER = re.compile(r"^(r\d+|ip|sl|fp|sb)\b")
# NtCurrentTeb(). On i386 this is fs:[0x18], Wine's TEB. Compiled for ARM it
# becomes a read of the native thread pointer, which under Box86 belongs to the
# host thread and has nothing to do with the guest TEB -- so wined3d_from_cs()
# and everything else that identifies the thread reads arbitrary memory.
# Measured: island entry 3 faulted reading TEB+0x24, the Win32 thread id.
TEB = re.compile(r"^mrc\b.*\bcr13\b.*\{2\}")


def symbols(binary):
    """addr -> name, plus name -> addr. Thumb symbols carry bit 0; mask it."""
    out = subprocess.run([READELF, "-sW", binary], capture_output=True, text=True).stdout
    by_addr, by_name = {}, {}
    for line in out.splitlines():
        f = line.split()
        if len(f) < 8 or f[3] != "FUNC":
            continue
        try:
            addr = int(f[1], 16) & ~1
        except ValueError:
            continue
        name = f[7]
        by_addr.setdefault(addr, name)
        by_name.setdefault(name, addr)
    return by_addr, by_name


def call_graph(binary, by_addr):
    """function -> (set of callees, count of indirect call sites)"""
    result = subprocess.run([OBJDUMP, "-d", binary], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("objdump failed for %s:\n%s"
                           % (binary, result.stderr[-2000:]))
    out = result.stdout
    calls = collections.defaultdict(set)
    indirect = collections.Counter()
    teb = set()
    cur = None
    header = re.compile(r"^([0-9a-f]+) <([^>]+)>:")
    for line in out.splitlines():
        h = header.match(line)
        if h:
            cur = h.group(2)
            continue
        if cur is None:
            continue
        m = LINE.match(line)
        if not m:
            continue
        mnemonic, operands = m.group(3), m.group(4)
        if TEB.match(mnemonic + " " + operands):
            teb.add(cur)
        if not CALL_MNEMONIC.match(mnemonic):
            continue
        t = TARGET.match(operands)
        if t:
            callee = by_addr.get(int(t.group(1), 16) & ~1)
            if callee and callee != cur:
                calls[cur].add(callee)
        elif REGISTER.match(operands) and mnemonic.startswith(("blx", "bx")):
            indirect[cur] += 1
    return calls, indirect, teb


def main():
    binary = sys.argv[1]
    entries_src = sys.argv[2] if len(sys.argv) > 2 else "mgs2_island_bridges.c"

    by_addr, by_name = symbols(binary)
    calls, indirect, teb = call_graph(binary, by_addr)

    # A stub is anything that calls the generated reporter.
    stubs = {f for f, cs in calls.items() if "mgs2_island_forbidden" in cs}

    entries = []
    for line in open(entries_src):
        m = re.match(r"\s*\{\s*(\d+),\s*\(void \*\)\S+,\s*\(void \*\)(\w+)\s*\}", line)
        if m:
            entries.append((int(m.group(1)), m.group(2)))
    if not entries:
        sys.exit(f"no entries parsed from {entries_src}")

    print(f"{len(stubs)} abort stubs, {len(entries)} island entries\n")
    clean, dirty = [], []
    for eid, name in entries:
        seen, stack = set(), [name]
        while stack:
            f = stack.pop()
            if f in seen:
                continue
            seen.add(f)
            stack.extend(calls.get(f, ()))
        hit = sorted(seen & stubs)
        ind = sum(indirect.get(f, 0) for f in seen)
        nteb = len(seen & teb)
        (dirty if hit else clean).append((eid, name, len(seen), ind, nteb, hit))

    print("entries that reach an abort stub -- arming any of these aborts the run")
    for eid, name, n, ind, nteb, hit in sorted(dirty):
        print(f"  {eid:2d} {name:<45} closure={n:<4} indirect={ind:<4} teb={nteb:<3} {' '.join(hit[:5])}"
              + (" ..." if len(hit) > 5 else ""))

    print("\nentries with no reachable abort stub")
    for eid, name, n, ind, nteb, hit in sorted(clean):
        print(f"  {eid:2d} {name:<45} closure={n:<4} indirect={ind:<4} teb={nteb}")

    # Safe to arm means all three: no abort stub, no NtCurrentTeb in the closure,
    # and no indirect call, because a guest-held function pointer holds an x86
    # address that native ARM cannot call.
    safe = [e for e in clean if e[3] == 0 and e[4] == 0]
    print(f"\nno stub, no TEB read, no indirect call -- {len(safe)} of {len(entries)} entries")
    print(f"MGS2_BOX86_ISLAND_ONLY={','.join(str(e[0]) for e in sorted(safe))}")

    # Control on the call graph itself, not on the entry table: wined3d_release_dc
    # stopped being an entry once it was dropped from the cut, and keying the
    # check on the entry list made it fail for a reason that had nothing to do
    # with the graph. It is still in the binary, and it still calls these two.
    seen, stack = set(), ["wined3d_release_dc"]
    while stack:
        f = stack.pop()
        if f in seen:
            continue
        seen.add(f)
        stack.extend(calls.get(f, ()))
    ok = {"WindowFromDC", "ReleaseDC"} <= seen
    print("\ncontrol check (wined3d_release_dc reaches WindowFromDC and ReleaseDC): "
          + ("PASS" if ok else "FAIL -- the call graph is not being built, ignore the numbers"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

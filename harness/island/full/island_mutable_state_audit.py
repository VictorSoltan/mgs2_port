#!/usr/bin/env python3
"""Writable ELF objects referenced by one native-island entry closure.

The ARM island links a second copy of WineD3D's translation units into Box86.
Any mutable file-scope object used by both guest and ARM may therefore diverge.
This audit starts at an island entry, builds the same direct/source/ops closure
as the indirect-call audit, then decodes absolute and PC-relative literals in a
link made with ``--emit-relocs`` to find the writable ``.data/.bss/.tbss``
objects referenced by that closure.  It does not yet parse the ELF relocation
tables themselves; a clean root result is therefore a review input, not proof
that no duplicated mutable state exists.

Zero-storage objects are labelled RUNTIME candidates.  That is deliberately a
review label, not a claim that every BSS object must be shared: counters, caches
owned wholly by the ARM closure, and immutable-after-init tables are harmless.

Control: an entry-37 run must find both ``wined3d_context_tls_idx`` and
``mgs2_batch_ptr``.  p67 proved that these copies exist, so missing either
invalidates the analyser.  A direct ``--root`` run deliberately does not apply
entry-37-specific mandatory symbols; run entry 37 separately as its self-test.
"""

import argparse
import collections
import functools
import os
import pathlib
import re
import struct
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import island_gl_reach
import island_icall_audit
import island_reach


CLONE = island_icall_audit.CLONE
HEADER = re.compile(r"^([0-9a-f]+) <([^>]+)>:")
INSN = re.compile(r"^\s*([0-9a-f]+):\s+((?:[0-9a-f]{4,8}\s+)+)\t?\s*(\S+)\s*(.*)$")
LITERAL = re.compile(r"^(r\d+|ip|sl|fp|sb),\s*\[pc[^]]*\].*@\s*\(([0-9a-f]+)\b")


def run(*argv):
    result = subprocess.run(argv, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("%s failed:\n%s" % (" ".join(argv), result.stderr[-2000:]))
    return result.stdout


def sections(binary):
    result = {}
    for line in run("readelf", "-SW", binary).splitlines():
        fields = line.replace("[", " ").replace("]", " ").split()
        if len(fields) < 8 or not fields[0].isdigit():
            continue
        try:
            result[int(fields[0])] = {
                "name": fields[1], "addr": int(fields[3], 16),
                "offset": int(fields[4], 16), "size": int(fields[5], 16),
                "flags": fields[7],
            }
        except (ValueError, IndexError):
            continue
    return result


def writable_objects(binary, sec):
    objects = []
    for line in run("readelf", "-sW", binary).splitlines():
        fields = line.split()
        if len(fields) < 8 or fields[3] != "OBJECT" or not fields[6].isdigit():
            continue
        section = sec.get(int(fields[6]))
        if not section or "W" not in section["flags"]:
            continue
        try:
            address, size = int(fields[1], 16), int(fields[2], 0)
        except ValueError:
            continue
        name = fields[7]
        # Duplicate SYMTAB/DYNSYM rows are harmless; key by identity.
        objects.append((address, max(size, 1), name, section["name"], fields[4]))
    return sorted(set(objects))


@functools.lru_cache(maxsize=4)
def source_graph(binary):
    """Return the reusable direct/source/ops adjacency for one ARM binary."""
    bodies = island_icall_audit.functions_by_file()
    by_addr, by_name = island_reach.symbols(binary)
    calls, _indirect, _teb = island_reach.call_graph(binary, by_addr)
    call_re = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
    src_calls = {}
    for fn, (_filename, _line, body) in bodies.items():
        src_calls[fn] = {m.group(1) for _n, text in body for m in call_re.finditer(text)
                         if m.group(1) in bodies}
    targets = island_gl_reach.ops_targets(island_icall_audit.SRC_DIR)
    member_call = re.compile(r"(?:->|\.)\s*(\w+)\s*(?:\(|\))")

    graph = collections.defaultdict(set)
    candidates = set(bodies) | set(calls)
    for fn in candidates:
        base = CLONE.sub("", fn)
        for callee in calls.get(fn, ()):
            normalized = CLONE.sub("", callee)
            if normalized in bodies:
                graph[fn].add(normalized)
        for callee in src_calls.get(base, ()):
            if callee in by_name or callee in bodies:
                graph[fn].add(callee)
        if base in bodies:
            for _n, text in bodies[base][2]:
                for match in member_call.finditer(text):
                    graph[fn].update(target for target in targets.get(match.group(1), ())
                                     if target in bodies)
    return {name: frozenset(edges) for name, edges in graph.items()}


def source_closure_roots(binary, roots):
    """Build one closure for one or more roots without reparsing the binary."""
    graph = source_graph(binary)
    closure, stack = set(), list(roots)
    while stack:
        fn = stack.pop()
        if fn in closure:
            continue
        closure.add(fn)
        stack.extend(graph.get(fn, ()))
    return closure


def source_closure(binary, entry, entries, requested_root=None):
    root = requested_root
    if not root:
        for line in open(entries):
            match = re.match(r"\s*\{\s*(\d+),\s*\(void \*\)\S+,\s*\(void \*\)(\w+)\s*\}", line)
            if match and int(match.group(1)) == entry:
                root = match.group(2)
                break
    if not root:
        raise RuntimeError("entry %d not found in %s" % (entry, entries))
    return root, source_closure_roots(binary, [root])


def disassembly(binary):
    functions = collections.defaultdict(list)
    current = None
    for line in run("arm-linux-gnueabihf-objdump", "-d", binary).splitlines():
        header = HEADER.match(line)
        if header:
            current = header.group(2)
            continue
        match = INSN.match(line)
        if current and match:
            encoding = "".join(match.group(2).split())
            functions[current].append((int(match.group(1), 16), len(encoding) // 2,
                                       match.group(3), match.group(4)))
    return functions


def read_word(image, sec, address):
    for section in sec.values():
        if section["addr"] <= address <= section["addr"] + section["size"] - 4:
            offset = section["offset"] + address - section["addr"]
            return struct.unpack_from("<I", image, offset)[0]
    return None


def containing_object(objects, address):
    hits = [obj for obj in objects if obj[0] <= address < obj[0] + obj[1]]
    if not hits:
        return None
    # Prefer the smallest named object over a covering aggregate.
    return min(hits, key=lambda obj: obj[1])


def referenced_objects(binary, closure, sec, objects):
    image = pathlib.Path(binary).read_bytes()
    functions = disassembly(binary)
    hits = collections.defaultdict(set)

    for fn, instructions in functions.items():
        if fn not in closure and CLONE.sub("", fn) not in closure:
            continue
        for index, (address, insn_size, mnemonic, operands) in enumerate(instructions):
            if not mnemonic.startswith("ldr"):
                continue
            match = LITERAL.match(operands)
            if not match:
                continue
            register, literal_address = match.group(1), int(match.group(2), 16)
            value = read_word(image, sec, literal_address)
            if value is None:
                continue

            # Absolute literal first (common for externally visible data).
            candidates = [(value, "absolute literal", None)]
            # For the local-static PIC form GCC emits ``ldr reg,[pc]; add reg,pc``.
            # ARM observes PC=instruction+8, Thumb observes instruction+4.
            for next_index in range(index + 1, min(index + 5, len(instructions))):
                next_address, next_size, next_mnemonic, next_operands = instructions[next_index]
                add = re.match(r"^%s,\s*(?:%s,\s*)?pc\b" % (register, register), next_operands)
                if next_mnemonic.startswith("add") and add:
                    bias = 4 if next_size == 2 else 8
                    candidates.append(((value + next_address + bias) & 0xffffffff,
                                       "PC-relative literal", next_index + 1))
                    break
            resolved = []
            for target, method, scan_start in candidates:
                obj = containing_object(objects, target)
                if obj:
                    hits[obj].add((fn, address, method))
                    if scan_start is not None:
                        resolved.append((target, register, scan_start, method))

            # GCC commonly anchors a cluster of local statics at the first one
            # and addresses its neighbours as ``[base, #offset]``.  Entry 37's
            # context_gl.o is the control: the literal names the TLS index while
            # ``mgs2_batch_ptr`` is the adjacent word at +4.  Looking only at the
            # literal target would silently miss exactly the duplicate-state
            # class this tool exists to find.
            for target, base_register, start, method in resolved:
                memory = re.compile(r"\[%s(?:,\s*#([+-]?(?:0x[0-9a-f]+|\d+)))?" % base_register)
                for use_address, _use_size, use_mnemonic, use_operands in instructions[start:start + 80]:
                    mem = memory.search(use_operands)
                    if mem:
                        offset = int(mem.group(1), 0) if mem.group(1) else 0
                        neighbor = containing_object(objects, (target + offset) & 0xffffffff)
                        if neighbor:
                            hits[neighbor].add((fn, use_address, method + " + member offset"))
                    first = re.match(r"^(r\d+|ip|sl|fp|sb)\s*,", use_operands)
                    if first and first.group(1) == base_register \
                            and not use_mnemonic.startswith(("str", "cmp", "tst", "teq")):
                        break
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("binary", help="unstripped ARM Box86 linked with --emit-relocs")
    ap.add_argument("--entry", type=int, default=37)
    ap.add_argument("--root", help="audit this symbol directly instead of resolving --entry")
    ap.add_argument("--entries", default="/mnt/data/holden/mgs/box86-src/src/mgs2_island_bridges.c")
    args = ap.parse_args()

    sec = sections(args.binary)
    objects = writable_objects(args.binary, sec)
    root, closure = source_closure(args.binary, args.entry, args.entries, args.root)
    hits = referenced_objects(args.binary, closure, sec, objects)

    rows = []
    for obj, sites in hits.items():
        address, size, name, section, binding = obj
        runtime = section in (".bss", ".tbss")
        rows.append((not runtime, name, address, size, section, binding, sites))
    rows.sort()

    print("entry %d root %s" % (args.entry, root) if not args.root else "root %s" % root)
    print("closure %d functions; %d referenced writable objects\n" % (len(closure), len(rows)))
    for _constant, name, address, size, section, binding, sites in rows:
        label = "RUNTIME" if section in (".bss", ".tbss") else "REVIEW"
        callers = sorted({fn for fn, _address, _method in sites})
        print("%-7s %-38s %s %6d bytes @ %#x  refs=%d" %
              (label, name, section, size, address, len(sites)))
        print("        " + ", ".join(callers[:8]) + (" ..." if len(callers) > 8 else ""))

    if args.root or args.entry != 37:
        print("\ncontrol: SKIP (entry-37 self-test is separate from this root)")
        return 0

    found = {name for _c, name, *_rest in rows}
    controls = {"wined3d_context_tls_idx", "mgs2_batch_ptr"}
    missing = controls - found
    print("\ncontrol (entry 37 reaches TLS index and adjacent shared batch pointer): "
          + ("PASS" if not missing else "FAIL, missing " + ", ".join(sorted(missing))))
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())

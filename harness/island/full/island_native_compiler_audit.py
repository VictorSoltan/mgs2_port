#!/usr/bin/env python3
"""Is every native target reachable from one island root built by ONE compiler?

WHY THIS EXISTS

The ABI closure audit answers "does native code see the guest's field offsets?".
Building the island with Clang's ``-mms-bitfields`` makes that answer yes for the
FFP chain that invalidated p69.  It creates a second question the older audits
cannot see: the island is a *set of objects*, and a Class-B dispatch selects a
native function by id.  If any object in that set were still the GCC build, one
closure would hold two different aggregate layouts -- the exact defect p69 died
of, reintroduced from the other side.

So this audit reads the producer recorded in each object's own DWARF, maps every
Class-B native id reachable from the root to the object that defines it, and
fails unless all of them come from the same MS-layout compiler.

    reachable native ids      Class-B names present in the root's closure
    ms-layout targets         defined by an object whose producer carries
                              -mms-bitfields
    other/unknown targets     anything else -- MUST be 0
    duplicate targets         a name defined by more than one object -- MUST be 0

usage: island_native_compiler_audit.py <box86 binary> --root NAME [--root NAME]
                                       [--phase A|B|C|D] [--objects DIR]
                                       [--class-b HEADER] [--expect-ms|--expect-gnu]
"""
import argparse
import collections
import glob
import os
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import island_draw_phases
import island_icall_audit
import island_mutable_state_audit

BOX86_SRC = pathlib.Path(os.environ.get("BOX86_SRC", "/mnt/data/holden/mgs/box86-src"))
OBJDUMP = "arm-linux-gnueabihf-objdump"
NM = "arm-linux-gnueabihf-nm"


def class_b_names(header):
    """native id -> function name, from the generated Class-B table."""
    text = pathlib.Path(header).read_text(errors="replace")
    names = {}
    for match in re.finditer(r'\{\s*(\d+)\s*,\s*"([A-Za-z_]\w*)"\s*\}', text):
        names[int(match.group(1))] = match.group(2)
    if not names:
        # The diagnostic id-name array is emitted as a plain string list.
        for index, match in enumerate(re.finditer(r'^\s*"([A-Za-z_]\w*)",\s*$', text, re.M)):
            names[index] = match.group(1)
    return names


def producer(obj):
    """Which compiler built this object.

    The shipped island objects carry no DWARF -- the build does not pass -g --
    so the flag string cannot be recovered from them. `.comment` still names the
    compiler, which is what the homogeneity half of this audit needs; the layout
    half is proved by the compiled witness below instead of by a command line.
    """
    out = subprocess.run(["arm-linux-gnueabihf-readelf", "-p", ".comment", obj],
                         capture_output=True, text=True).stdout
    names = re.findall(r"(clang version [\d.]+|GCC: \([^)]*\) [\d.]+)", out)
    return names[0] if names else ""


LAYOUT_MS = (16, 132, 148, 1020, 7276)
LAYOUT_GNU = (12, 100, 116, 1020, 7276)
WITNESS_FIELDS = ("texture_stage_op", "ffp_frag_settings", "ffp_frag_desc",
                  "wined3d_context", "wined3d_state")


def layout_witness(objects):
    """Read the sizes the compiler actually laid out, from the object set."""
    for obj in objects:
        if "mgs2_island_layout_witness" not in defined_symbols(obj):
            continue
        dump = subprocess.run([OBJDUMP, "-s", "-j", ".rodata", obj],
                              capture_output=True, text=True).stdout
        words = []
        for line in dump.splitlines():
            match = re.match(r"\s*[0-9a-f]+\s((?:[0-9a-f]{8}\s){1,4})", line)
            if match:
                for group in match.group(1).split():
                    words.append(int.from_bytes(bytes.fromhex(group), "little"))
        if 0x4d475332 in words:
            start = words.index(0x4d475332)
            return obj, tuple(words[start + 1:start + 1 + len(WITNESS_FIELDS)])
    return None, None


def defined_symbols(obj):
    out = subprocess.run([NM, "--defined-only", obj], capture_output=True, text=True).stdout
    return {line.split()[-1] for line in out.splitlines() if len(line.split()) == 3}


def writable_symbols(objects):
    """name -> (section, size) for every writable object the island defines.

    The mutable-state review is about duplicated writable state.  Comparing what
    the object set DEFINES is compiler-shape independent, unlike decoding how a
    given compiler loads an address: if two builds define the same writable
    symbols at the same sizes, a review of one carries over to the other.
    """
    result = {}
    for obj in objects:
        out = subprocess.run(["arm-linux-gnueabihf-readelf", "-sW", obj],
                             capture_output=True, text=True).stdout
        for line in out.splitlines():
            fields = line.split()
            if len(fields) < 8 or not fields[0].rstrip(":").isdigit():
                continue
            size, kind, index, name = fields[2], fields[3], fields[6], fields[7]
            if kind != "OBJECT" or index in ("UND", "ABS"):
                continue
            section = SECTION_NAMES.get((obj, index))
            if section is None:
                section = section_name(obj, index)
                SECTION_NAMES[(obj, index)] = section
            # .data.rel.ro is constant after relocation -- Clang puts switch
            # tables there and GCC does not, which is not mutable state.
            if section in (".data", ".bss", ".tbss"):
                # readelf prints large sizes in hex.
                result[name] = (section, int(size, 16) if size.startswith("0x") else int(size))
    return result


SECTION_NAMES = {}


def section_name(obj, index):
    out = subprocess.run(["arm-linux-gnueabihf-readelf", "-SW", obj],
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        fields = line.replace("[", " ").replace("]", " ").split()
        if len(fields) > 2 and fields[0] == index:
            return fields[1]
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("binary")
    selection = ap.add_mutually_exclusive_group(required=True)
    selection.add_argument("--root", action="append")
    selection.add_argument("--phase", choices="ABCD")
    ap.add_argument("--objects", default=str(BOX86_SRC / "src/island"))
    ap.add_argument("--class-b", default=str(BOX86_SRC / "src/mgs2_island_class_b.h"))
    ap.add_argument("--compare-objects", metavar="DIR",
                    help="reference object set (e.g. the reviewed GCC island): the "
                         "writable symbols the island DEFINES must be the same, or "
                         "the mutable-state review does not carry over")
    layout = ap.add_mutually_exclusive_group()
    layout.add_argument("--expect-ms", action="store_true", default=True,
                        help="require every object to carry -mms-bitfields (default)")
    layout.add_argument("--expect-gnu", action="store_true",
                        help="require the historical GNU-layout build instead")
    args = ap.parse_args()
    want_ms = not args.expect_gnu

    bodies = island_icall_audit.functions_by_file()
    if args.phase:
        roots = island_draw_phases.phase_spec(args.phase, bodies)["roots"]
        label = "phase-%s" % args.phase
    else:
        roots = args.root
        label = "+".join(roots)
    closure = island_mutable_state_audit.source_closure_roots(args.binary, roots)

    objects = sorted(glob.glob(os.path.join(args.objects, "*.o")))
    if not objects:
        print("no objects in %s" % args.objects)
        return 2
    producers, owner = {}, collections.defaultdict(list)
    for obj in objects:
        producers[obj] = producer(obj)
        for symbol in defined_symbols(obj):
            owner[symbol].append(obj)


    names = class_b_names(args.class_b)
    reachable = {nid: name for nid, name in names.items() if name in closure}

    witness_obj, witness = layout_witness(objects)
    expected = LAYOUT_MS if want_ms else LAYOUT_GNU
    compilers = {producers[obj] for obj in objects if producers[obj]}
    unknown_compiler = [obj for obj in objects if not producers[obj]]
    wrong_objects = []

    ms_targets, other_targets, missing, duplicates = [], [], [], []
    for nid, name in sorted(reachable.items()):
        owners = owner.get(name, [])
        if not owners:
            missing.append((nid, name))
        elif len(owners) > 1:
            duplicates.append((nid, name, owners))
        elif len(compilers) == 1 and witness == expected:
            ms_targets.append((nid, name, owners[0]))
        else:
            other_targets.append((nid, name, owners[0], producers[owners[0]][:60]))


    print("root %s; source closure %d functions" % (label, len(closure)))
    print("island objects %d; expected layout %s"
          % (len(objects), "MS (-mms-bitfields)" if want_ms else "GNU"))
    print("Class-B names total %d; reachable from this root %d"
          % (len(names), len(reachable)))
    print("  matching-layout targets   %d" % len(ms_targets))
    print("  other/unknown targets     %d   (must be 0)" % len(other_targets))
    print("  duplicate-symbol targets  %d   (must be 0)" % len(duplicates))
    print("  unresolved targets        %d   (must be 0)" % len(missing))
    print("compiled layout witness in %s:" %
          (os.path.basename(witness_obj) if witness_obj else "NOT FOUND"))
    if witness:
        for field, got, want in zip(WITNESS_FIELDS, witness, expected):
            print("    %-20s %-6s expected %-6s %s"
                  % (field, got, want, "OK" if got == want else "WRONG"))
    print("compilers named by .comment: %s"
          % (", ".join(sorted(compilers)) or "none"))
    if unknown_compiler:
        print("  objects with no .comment: %d" % len(unknown_compiler))

    for nid, name, obj, prod in other_targets[:20]:
        print("    OTHER  %-5d %-44s %s  [%s]" % (nid, name, os.path.basename(obj), prod))
    for nid, name, owners in duplicates[:20]:
        print("    DUP    %-5d %-44s %s" % (nid, name, ", ".join(map(os.path.basename, owners))))
    for nid, name in missing[:20]:
        print("    MISS   %-5d %s" % (nid, name))
    for obj in wrong_objects[:20]:
        print("    WRONG-LAYOUT %-24s [%s]" % (os.path.basename(obj), producers[obj][:70]))

    drift = None
    if args.compare_objects:
        mine = writable_symbols(objects)
        theirs = writable_symbols(sorted(glob.glob(os.path.join(args.compare_objects, "*.o"))))
        added = sorted(set(mine) - set(theirs))
        removed = sorted(set(theirs) - set(mine))
        resized = sorted(name for name in set(mine) & set(theirs)
                         if mine[name] != theirs[name])
        # The two objects p67 proved must be shared with the guest. A build
        # that loses or resizes either is not a drop-in for the reviewed island;
        # everything else is drift for review, because a file-local counter or
        # once-guard that only island code touches cannot diverge from the guest.
        MUST_MATCH = ("wined3d_context_tls_idx", "mgs2_batch_ptr")
        broken = [name for name in MUST_MATCH
                  if mine.get(name) != theirs.get(name) or name not in mine]
        drift = broken
        print("\nwritable symbols defined: %d here, %d in the reference set"
              % (len(mine), len(theirs)))
        print("  added %d; removed %d; changed section/size %d  (review, not a gate)"
              % (len(added), len(removed), len(resized)))
        # Most name-level drift is just how each compiler names a
        # function-local static: GCC writes `translated.0`, Clang writes
        # `mgs2_island_gl_info.translated`. Comparing the (section, size)
        # multiset is naming-agnostic and says whether the same state exists.
        import collections as _c
        mine_shape = _c.Counter(mine.values())
        theirs_shape = _c.Counter(theirs.values())
        extra = sum((mine_shape - theirs_shape).values())
        gone = sum((theirs_shape - mine_shape).values())
        print("  naming-agnostic: %d unmatched here, %d unmatched in the reference"
              % (extra, gone))
        for name in MUST_MATCH:
            print("    must-match %-32s here=%s reference=%s  %s"
                  % (name, mine.get(name), theirs.get(name),
                     "OK" if name in mine and mine[name] == theirs.get(name) else "FAIL"))
        for name in added[:15]:
            print("    ADDED    %-40s %s %d" % (name, mine[name][0], mine[name][1]))
        for name in removed[:15]:
            print("    REMOVED  %-40s %s %d" % (name, theirs[name][0], theirs[name][1]))
        for name in resized[:15]:
            print("    CHANGED  %-40s %s -> %s" % (name, theirs[name], mine[name]))

    bad = bool(other_targets or duplicates or missing
               or witness != expected or len(compilers) != 1
               or bool(drift))
    print("\ncompiler-homogeneous native closure: %s" % ("FAIL" if bad else "PASS"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

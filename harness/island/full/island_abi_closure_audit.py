#!/usr/bin/env python3
"""Compare i386/ARM aggregate layouts reachable from an island root.

The native island dereferences WineD3D objects allocated by the guest i386
module.  Equal top-level pointer sizes are not enough: a private cache node or
an embedded key with MS bitfields can move every field after it.  This tool:

* builds the source/direct/ops closure used by the other island audits;
* finds aggregate types named by those functions and follows embedded / array
  member layouts transitively;
* compares each type in the defining translation unit's i386 and ARM DWARF;
* keeps same-named private types TU-qualified; and
* exits non-zero when a type classified guest-owned or shared differs.

``--build-arm`` creates throw-away ``-g`` objects in ``--arm-dir`` with the
same island defines.  It does not replace the linked island objects or any
shipping artifact.

Ownership is deliberately conservative.  A short, reviewed table below marks
objects whose lifetime crosses the p69 boundary.  Everything else is UNKNOWN,
not silently declared safe.  Add a classification only with a source-level
ownership reason.
"""

import argparse
import collections
import os
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import island_icall_audit
import island_draw_phases
import island_mutable_state_audit


WINE_SRC = pathlib.Path(os.environ.get(
    "WINE_SRC", "/mnt/data/holden/mgs/recovered-session/wine-11.0"))
WINE_BUILD = pathlib.Path(os.environ.get(
    "WINE_BUILD", "/mnt/data/holden/mgs/recovered-session/build-wine-i386"))
BOX86_SRC = pathlib.Path(os.environ.get(
    "BOX86_SRC", "/mnt/data/holden/mgs/box86-src"))

# These objects are allocated or initialised by guest WineD3D and subsequently
# dereferenced by the native p69 closure.
GUEST_OWNED = {
    "wined3d_adapter", "wined3d_buffer", "wined3d_context",
    "wined3d_context_gl", "wined3d_device", "wined3d_resource",
    "wined3d_state", "wined3d_texture", "wined3d_texture_gl",
    "wined3d_view", "shader_glsl_priv", "glsl_context_data",
}

# These persist in caches / context backend data visible on both sides of the
# cut.  The FFP settings and stage op are included transitively in the cached
# ffp_frag_desc key; they are not merely native stack temporaries.
SHARED = {
    "texture_stage_op", "ffp_frag_settings", "ffp_frag_desc",
    "glsl_ffp_fragment_shader", "glsl_ffp_vertex_shader",
    "glsl_shader_prog_link",
}

ARM_OWNED = {
    "mgs2_ffp_ps_source", "mgs2_ffp_vs_source", "mgs2_vs_stage_cache",
}

DIE = re.compile(r"^\s*<(\d+)><([0-9a-f]+)>: Abbrev Number: \d+ \((DW_TAG_\w+)\)")
ATTR = re.compile(r"^\s*<[0-9a-f]+>\s+(DW_AT_\w+)\s*:\s*(.*)$")


def run(argv, **kwargs):
    result = subprocess.run(argv, capture_output=True, text=True, **kwargs)
    if result.returncode:
        raise RuntimeError("%s failed:\n%s" % (" ".join(map(str, argv)), result.stderr[-4000:]))
    return result.stdout


def name(die):
    value = (die["attrs"].get("DW_AT_name", "") or "").strip()
    match = re.search(r":\s*([A-Za-z_][A-Za-z0-9_]*)\s*$", value)
    if match:
        return match.group(1)
    return value if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value) else ""


def number(die, attr):
    value = die["attrs"].get(attr)
    if value is None:
        return None
    # Both GNU objdumps used here put the useful scalar first for these attrs.
    match = re.match(r"\s*(0x[0-9a-fA-F]+|-?\d+)", value)
    return int(match.group(1), 0) if match else None


def reference(dies, die, attr="DW_AT_type"):
    match = re.search(r"<0x([0-9a-f]+)>", die["attrs"].get(attr, "") or "")
    return dies.get(int(match.group(1), 16)) if match else None


def parse_dwarf(objdump, obj):
    text = run([objdump, "--dwarf=info", str(obj)])
    dies, order, current = {}, [], None
    for line in text.splitlines():
        match = DIE.match(line)
        if match:
            current = {"depth": int(match.group(1)), "offset": int(match.group(2), 16),
                       "tag": match.group(3), "attrs": {}, "children": []}
            dies[current["offset"]] = current
            order.append(current)
            continue
        match = ATTR.match(line)
        if match and current is not None:
            current["attrs"][match.group(1)] = match.group(2).strip()
    stack = {}
    for item in order:
        stack[item["depth"]] = item
        parent = stack.get(item["depth"] - 1)
        if parent is not None:
            parent["children"].append(item)
    return dies, order


def peel(dies, die):
    while die is not None and die["tag"] in {
            "DW_TAG_typedef", "DW_TAG_const_type", "DW_TAG_volatile_type",
            "DW_TAG_restrict_type", "DW_TAG_atomic_type"}:
        die = reference(dies, die)
    return die


def embedded_aggregate_target(dies, die):
    """Return a member type whose bytes are part of the containing object.

    Following every pointer pointee made a proven-safe entry-23 root inherit
    every layout reachable from teardown-only ops.  A pointer does not embed
    its pointee's layout.  Pointees actually dereferenced by the closure are
    seeded independently because their type names occur in those function
    bodies; embedded structs and array elements still propagate transitively.
    """
    die = peel(dies, die)
    if die is not None and die["tag"] == "DW_TAG_pointer_type":
        return None
    while die is not None and die["tag"] == "DW_TAG_array_type":
        die = peel(dies, reference(dies, die))
    if die is not None and die["tag"] in {"DW_TAG_structure_type", "DW_TAG_union_type"}:
        return name(die)
    return None


def inferred_align(dies, die, seen=None):
    die = peel(dies, die)
    if die is None:
        return 1
    explicit = number(die, "DW_AT_alignment")
    if explicit:
        return explicit
    if die["tag"] == "DW_TAG_pointer_type":
        return number(die, "DW_AT_byte_size") or 4
    if die["tag"] == "DW_TAG_array_type":
        return inferred_align(dies, reference(dies, die), seen)
    if die["tag"] in {"DW_TAG_base_type", "DW_TAG_enumeration_type"}:
        return min(number(die, "DW_AT_byte_size") or 1, 8)
    if die["tag"] not in {"DW_TAG_structure_type", "DW_TAG_union_type"}:
        return min(number(die, "DW_AT_byte_size") or 1, 8)
    seen = set() if seen is None else seen
    if die["offset"] in seen:
        return 1
    seen.add(die["offset"])
    values = [inferred_align(dies, reference(dies, child), seen)
              for child in die["children"] if child["tag"] == "DW_TAG_member"]
    return max(values, default=1)


def layouts(dies, order):
    result = {}
    for die in order:
        if die["tag"] not in {"DW_TAG_structure_type", "DW_TAG_union_type"}:
            continue
        type_name = name(die)
        size = number(die, "DW_AT_byte_size")
        if not type_name or size is None:
            continue
        members = []
        edges = set()
        for child in die["children"]:
            if child["tag"] != "DW_TAG_member":
                continue
            member_name = name(child) or "<anonymous>"
            offset = number(child, "DW_AT_data_member_location")
            bit_size = number(child, "DW_AT_bit_size")
            bit_offset = number(child, "DW_AT_bit_offset")
            data_bit_offset = number(child, "DW_AT_data_bit_offset")
            if bit_size is not None:
                if data_bit_offset is None and offset is not None:
                    unit = number(child, "DW_AT_byte_size")
                    member_type = peel(dies, reference(dies, child))
                    if unit is None and member_type is not None:
                        unit = number(member_type, "DW_AT_byte_size")
                    unit = unit or 4
                    data_bit_offset = offset * 8 + unit * 8 - (bit_offset or 0) - bit_size
                # GCC's DWARF5 uses absolute DW_AT_data_bit_offset while the
                # mingw DWARF2 producer uses storage-byte + MSB bit offset.
                # Compare one canonical absolute LSB position.
                members.append((member_name, "bit", data_bit_offset, bit_size))
            else:
                members.append((member_name, "byte", offset, None))
            target = embedded_aggregate_target(dies, reference(dies, child))
            if target:
                edges.add(target)
        candidate = {"size": size, "align": inferred_align(dies, die),
                     "members": tuple(members), "edges": edges}
        # Prefer a complete definition over a smaller declaration artefact.
        previous = result.get(type_name)
        if previous is None or len(candidate["members"]) > len(previous["members"]):
            result[type_name] = candidate
    return result


def classify(type_name):
    if type_name in SHARED:
        return "shared"
    if type_name in GUEST_OWNED:
        return "guest-owned"
    if type_name in ARM_OWNED:
        return "ARM-owned"
    return "UNKNOWN"


def build_arm_objects(tus, arm_dir):
    arm_dir.mkdir(parents=True, exist_ok=True)
    include = [
        WINE_BUILD / "dlls/wined3d", WINE_SRC / "dlls/wined3d", WINE_SRC / "include",
        WINE_SRC / "include/msvcrt", WINE_SRC / "libs/vkd3d/include",
        WINE_SRC / "libs/vkd3d/include/private", WINE_BUILD / "include",
    ]
    flags = ["-O2", "-g", "-fshort-wchar", "-Wno-builtin-declaration-mismatch", "-c",
             "-DMGS2_RELEASE", "-DMGS2_FINALPLAY", "-D_UCRT", "-D__WINESRC__",
             "-DMGS2_ISLAND_ARM", "-DWINE_NO_TRACE_MSGS", "-DWINE_NO_DEBUG_MSGS"]
    flags += ["-I" + str(path) for path in include]
    for tu in sorted(tus):
        source = WINE_SRC / "dlls/wined3d" / tu
        output = arm_dir / (pathlib.Path(tu).stem + ".o")
        subprocess.run(["arm-linux-gnueabihf-gcc", *flags, str(source), "-o", str(output)], check=True)


def changed(left, right):
    if left is None and right is None:
        return False
    if left is None or right is None:
        return True
    return (left["size"], left["align"], left["members"]) != \
           (right["size"], right["align"], right["members"])


def difference(left, right):
    if left is None:
        return "missing in i386 DWARF"
    if right is None:
        return "missing in ARM DWARF"
    parts = []
    if left["size"] != right["size"]:
        parts.append("size %d/%d" % (left["size"], right["size"]))
    if left["align"] != right["align"]:
        parts.append("align %d/%d" % (left["align"], right["align"]))
    lm = {m[0]: m[1:] for m in left["members"]}
    rm = {m[0]: m[1:] for m in right["members"]}
    moved = ["%s:%s/%s" % (n, lm.get(n), rm.get(n)) for n in sorted(lm.keys() | rm.keys())
             if lm.get(n) != rm.get(n)]
    if moved:
        parts.append("fields " + ", ".join(moved[:8]) + (" ..." if len(moved) > 8 else ""))
    return "; ".join(parts) or "equal"


def full_field_offsets(left, right):
    """Machine-readable-enough full member offset list for ``--all``."""
    lm = {m[0]: m[1:] for m in left["members"]} if left else {}
    rm = {m[0]: m[1:] for m in right["members"]} if right else {}
    values = []
    for member in sorted(lm.keys() | rm.keys()):
        def fmt(value):
            if value is None:
                return "-"
            kind, offset, width = value
            return ("b%d:%d" % (offset, width)) if kind == "bit" else str(offset)
        values.append("%s=%s/%s" % (member, fmt(lm.get(member)), fmt(rm.get(member))))
    return " ".join(values)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("binary", help="unstripped Box86 carrying the island")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--root", action="append",
                           help="direct root; repeat to audit a combined boundary")
    selection.add_argument("--phase", choices="ABCD", help="reviewed draw-state phase")
    parser.add_argument("--entries", default=str(BOX86_SRC / "src/mgs2_island_bridges.c"))
    parser.add_argument("--i386-dir", type=pathlib.Path,
                        default=WINE_BUILD / "dlls/wined3d/i386-windows")
    parser.add_argument("--arm-dir", type=pathlib.Path, default=pathlib.Path("/tmp/mgs2-island-abi-arm"))
    parser.add_argument("--build-arm", action="store_true")
    parser.add_argument("--all", action="store_true", help="print equal UNKNOWN rows too")
    parser.add_argument("--self-test", action="store_true",
                        help="require proven entries 10/23/38 to pass and p69 to fail")
    args = parser.parse_args()

    if args.self_test:
        controls = [
            ("entry10", "wined3d_buffer_load", 0),
            ("entry23", "wined3d_rendertarget_view_load_location", 0),
            ("entry38", "wined3d_context_gl_draw_primitive_arrays", 0),
            ("p69/D", "context_apply_draw_state", 1),
        ]
        ok = True
        for label, control_root, expected_rc in controls:
            command = [sys.executable, __file__, args.binary, "--root", control_root,
                       "--entries", args.entries, "--i386-dir", str(args.i386_dir),
                       "--arm-dir", str(args.arm_dir)]
            if args.build_arm:
                command.append("--build-arm")
            result = subprocess.run(command, capture_output=True, text=True)
            verdict = result.returncode == expected_rc
            print("%-8s %-49s %s (rc=%d, expected=%d)" %
                  (label, control_root, "PASS" if verdict else "FAIL",
                   result.returncode, expected_rc))
            if not verdict:
                print(result.stdout)
                print(result.stderr, file=sys.stderr)
                ok = False
        return 0 if ok else 2

    bodies = island_icall_audit.functions_by_file()
    phase = island_draw_phases.phase_spec(args.phase, bodies) if args.phase else None
    requested_roots = phase["roots"] if phase else (args.root or ["context_apply_draw_state"])
    closure = island_mutable_state_audit.source_closure_roots(args.binary, requested_roots)
    root = phase["label"] if phase else "+".join(requested_roots)
    functions_by_tu = collections.defaultdict(set)
    for function in closure:
        body = bodies.get(function)
        if body:
            functions_by_tu[body[0]].add(function)
    synthetic_bodies = {}
    if phase:
        synthetic = "phase_%s_control_flow" % phase["name"]
        functions_by_tu["context_gl.c"].add(synthetic)
        synthetic_bodies[synthetic] = phase["body"]
    tus = set(functions_by_tu)
    if args.build_arm:
        build_arm_objects(tus, args.arm_dir)

    records = []
    missing_objects = []
    for tu in sorted(tus):
        stem = pathlib.Path(tu).stem + ".o"
        i386_obj, arm_obj = args.i386_dir / stem, args.arm_dir / stem
        if not i386_obj.is_file() or not arm_obj.is_file():
            missing_objects.append((tu, i386_obj, arm_obj))
            continue
        i_dies, i_order = parse_dwarf(
            str(WINE_BUILD.parent / "mingw/bin/i686-w64-mingw32-objdump"), i386_obj)
        a_dies, a_order = parse_dwarf("arm-linux-gnueabihf-objdump", arm_obj)
        il, al = layouts(i_dies, i_order), layouts(a_dies, a_order)

        # Seed with aggregate names actually present in reachable function
        # source, then follow embedded and pointer-pointee aggregates.
        refs = collections.defaultdict(set)
        seeds = set()
        known = set(il) | set(al)
        for function in functions_by_tu[tu]:
            body = synthetic_bodies.get(function)
            if body is None:
                body = bodies[function][2]
            text = "\n".join(line for _line_no, line in body)
            words = set(re.findall(r"\b[A-Za-z_]\w*\b", text))
            for type_name in known & words:
                seeds.add(type_name)
                refs[type_name].add(function)
        reachable, stack = set(), list(seeds)
        while stack:
            type_name = stack.pop()
            if type_name in reachable:
                continue
            reachable.add(type_name)
            layout = il.get(type_name) or al.get(type_name)
            if layout:
                stack.extend(layout["edges"] - reachable)
        for type_name in sorted(reachable):
            left, right = il.get(type_name), al.get(type_name)
            if left is None and right is None:
                continue
            records.append({"tu": tu, "type": type_name, "class": classify(type_name),
                            "i386": left, "arm": right, "functions": refs[type_name],
                            "changed": changed(left, right)})

    if missing_objects:
        for tu, i386_obj, arm_obj in missing_objects:
            print("MISSING OBJECT %-18s i386=%s arm=%s" % (tu, i386_obj, arm_obj))
        return 2

    hard = [r for r in records if r["changed"] and r["class"] in {"guest-owned", "shared"}]
    mismatch = [r for r in records if r["changed"]]
    print("root %s; closure %d functions in %d translation units" % (root, len(closure), len(tus)))
    print("transitive aggregate rows %d; mismatches %d; hard failures %d\n" %
          (len(records), len(mismatch), len(hard)))
    for record in records:
        if not args.all and not record["changed"]:
            continue
        left, right = record["i386"], record["arm"]
        status = "FAIL" if record in hard else ("DIFF" if record["changed"] else "PASS")
        sizes = "%s/%s" % (left["size"] if left else "-", right["size"] if right else "-")
        aligns = "%s/%s" % (left["align"] if left else "-", right["align"] if right else "-")
        users = ",".join(sorted(record["functions"])[:5]) or "transitive"
        print("%-4s %-11s %-18s %-36s size=%-9s align=%-5s refs=%s" %
              (status, record["class"], record["tu"], record["type"], sizes, aligns, users))
        if record["changed"]:
            print("     " + difference(left, right))
        if args.all:
            print("     offsets i386/ARM: " + full_field_offsets(left, right))

    if requested_roots == ["context_apply_draw_state"]:
        print("\ncontrol: shader_glsl_apply_draw_state in closure: " +
              ("PASS" if "shader_glsl_apply_draw_state" in closure else "FAIL"))
        expected = {"texture_stage_op", "ffp_frag_settings", "ffp_frag_desc",
                    "glsl_ffp_fragment_shader"}
        seen_hard = {r["type"] for r in hard}
        print("control: known MS-bitfield propagation detected: " +
              ("PASS" if expected <= seen_hard else "FAIL, missing "
               + ", ".join(sorted(expected - seen_hard))))
        if "shader_glsl_apply_draw_state" not in closure or not expected <= seen_hard:
            return 2
    print("admission: %s" % ("FAIL" if hard else "PASS"))
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())

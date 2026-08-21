#!/usr/bin/env python3
"""Reattribute an existing Box86 cycle profile to draw-state phases A/B/C/D.

The exact profiled WineD3D is stripped, but its paired Box86 contains the
generated class-B ``guest RVA -> native ID`` table and the diagnostic ID-name
array.  PE ``.eh_frame`` supplies function extents.  This lets the reader name
only blocks whose FDE start is an exact class-B entry; unmapped functions remain
unresolved rather than being assigned to the nearest symbol.

Phase closures come from ``island_draw_phases.py``.  Functions shared by more
than one closure are reported as ambiguous.  Samples inside the parent
``context_apply_draw_state()`` cannot be split after the fact and remain other;
the report is a ranking tool, not an ms/frame conversion.
"""

import argparse
import bisect
import collections
import hashlib
import pathlib
import re
import struct
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
FULL = HERE / "island/full"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(FULL))
import box86_guest_profile as bgp
import island_draw_phases
import island_icall_audit
import island_mutable_state_audit


LINE = re.compile(
    r"^\s*(\S+)\s+(?:(\d+)/)?(\d+)\s+([0-9.]+):\s+(\d+)\s+"
    r"cycles:u:\s+([0-9a-fA-F]+)\s+(.*?)\s+\(([^)]*)\)\s*$")
FDE = re.compile(r"\bFDE\b.*\bpc=([0-9a-fA-F]+)\.\.([0-9a-fA-F]+)")
IMAGE_BASE = 0x10000000


def run(*argv):
    result = subprocess.run(argv, capture_output=True, text=True, check=True)
    return result.stdout


def elf_sections(path):
    sections = []
    for line in run("readelf", "-SW", str(path)).splitlines():
        fields = line.replace("[", " ").replace("]", " ").split()
        if len(fields) < 7 or not fields[0].isdigit():
            continue
        try:
            sections.append((fields[1], int(fields[3], 16), int(fields[4], 16),
                             int(fields[5], 16)))
        except ValueError:
            pass
    return sections


def va_to_offset(sections, address):
    for _name, start, offset, size in sections:
        if start <= address < start + size:
            return offset + address - start
    raise RuntimeError("ELF address %#x is outside file-backed sections" % address)


def c_string(data, offset):
    end = data.find(b"\0", offset)
    if end < 0:
        raise RuntimeError("unterminated string at file offset %#x" % offset)
    return data[offset:end].decode("ascii")


def embedded_class_b(box86):
    data = pathlib.Path(box86).read_bytes()
    sections = elf_sections(box86)
    data_rel = next((s for s in sections if s[0] == ".data.rel.ro"), None)
    rodata = next((s for s in sections if s[0] == ".rodata"), None)
    if not data_rel or not rodata:
        raise RuntimeError("Box86 lacks .data.rel.ro or .rodata")

    # Find the longest sorted run of {uint32 rva, uint16 id, uint16 pad}.
    # The immutable lookup table is in .rodata; only the diagnostic name
    # pointers live in .data.rel.ro.
    _name, _va, section_offset, section_size = rodata
    best = (0, 0)
    for alignment in range(8):
        start = None
        previous = -1
        for offset in range(section_offset + alignment, section_offset + section_size - 8, 8):
            rva, ident, pad = struct.unpack_from("<IHH", data, offset)
            valid = 0x1000 <= rva < 0x400000 and ident < 4096 and pad == 0 and rva > previous
            if valid:
                start = offset if start is None else start
                previous = rva
            else:
                if start is not None and offset - start > best[1]:
                    best = (start, offset - start)
                start, previous = None, -1
    table = [struct.unpack_from("<IHH", data, best[0] + i)[0:2]
             for i in range(0, best[1], 8)]
    if len(table) < 1000 or len({ident for _rva, ident in table}) != len(table):
        raise RuntimeError("could not identify the embedded class-B table")
    count = max(ident for _rva, ident in table) + 1

    first_name = b"adapter_adjust_mapped_memory\0"
    ro_start, ro_end = rodata[2], rodata[2] + rodata[3]
    string_offset = data.find(first_name, ro_start, ro_end)
    if string_offset < 0:
        raise RuntimeError("class-B diagnostic name anchor is absent")
    string_va = rodata[1] + string_offset - rodata[2]
    pointer = struct.pack("<I", string_va)
    pointer_offset = data.find(pointer, data_rel[2], data_rel[2] + data_rel[3])
    if pointer_offset < 0:
        raise RuntimeError("class-B diagnostic name pointer array is absent")
    names = []
    for index in range(count):
        address = struct.unpack_from("<I", data, pointer_offset + index * 4)[0]
        names.append(c_string(data, va_to_offset(sections, address)))
    if names[0] != first_name[:-1].decode() or any(not name for name in names):
        raise RuntimeError("invalid class-B diagnostic name array")
    return {rva: names[ident] for rva, ident in table}, len(table)


def fde_ranges(dll):
    objdump = pathlib.Path(
        "/mnt/data/holden/mgs/recovered-session/mingw/bin/i686-w64-mingw32-objdump")
    ranges = []
    for match in FDE.finditer(run(str(objdump), "--dwarf=frames", str(dll))):
        start, end = int(match.group(1), 16), int(match.group(2), 16)
        if start >= IMAGE_BASE:
            ranges.append((start - IMAGE_BASE, end - IMAGE_BASE))
    ranges.sort()
    return ranges


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=pathlib.Path)
    parser.add_argument("--box86", type=pathlib.Path, default=pathlib.Path("binaries/box86-island41"))
    parser.add_argument("--wined3d", type=pathlib.Path,
                        default=pathlib.Path("binaries/wined3d_p56_batch_state.dll"))
    parser.add_argument("--closure-binary", default="../box86-src/build/box86")
    args = parser.parse_args()

    records, metadata = bgp.read_guest_map(args.capture / "guest-map.bin")
    mappings, pe_spans = bgp.read_process_maps(args.capture / "maps")
    native_starts = [record[0] for record in records]
    mapping_starts = [mapping[0] for mapping in mappings]
    pe_starts = [span[0] for span in pe_spans]
    rva_names, class_b_count = embedded_class_b(args.box86)
    ranges = fde_ranges(args.wined3d)
    range_starts = [item[0] for item in ranges]

    bodies = island_icall_audit.functions_by_file()
    phase_closures = {}
    for phase_name in "ABCD":
        spec = island_draw_phases.phase_spec(phase_name, bodies)
        phase_closures[phase_name] = island_mutable_state_audit.source_closure_roots(
            args.closure_binary, spec["roots"])

    total_cycles = 0
    wined3d_cycles = 0
    buckets = collections.Counter()
    functions = collections.defaultdict(collections.Counter)
    unresolved_jit = 0
    for line in (args.capture / "perf.script").read_text(errors="replace").splitlines():
        match = LINE.match(line)
        if not match:
            continue
        period, native_ip, dso = int(match.group(5)), int(match.group(6), 16), match.group(8)
        total_cycles += period
        if not dso.startswith("/tmp/perf-"):
            continue
        record = bgp.containing(records, native_starts, native_ip)
        if record is None:
            unresolved_jit += period
            continue
        _native_start, _native_size, x86_start, _x86_size = record
        module, rva = bgp.resolve_module(mappings, mapping_starts, pe_spans, pe_starts, x86_start)
        if not module.endswith("/wined3d.dll"):
            continue
        wined3d_cycles += period
        index = bisect.bisect_right(range_starts, rva) - 1
        function = None
        if index >= 0 and rva < ranges[index][1]:
            function = rva_names.get(ranges[index][0])
        if function is None:
            function = rva_names.get(rva)
        if function is None:
            bucket = "unresolved/unmapped"
        else:
            memberships = [name for name, closure in phase_closures.items() if function in closure]
            bucket = memberships[0] if len(memberships) == 1 else (
                "shared/ambiguous" if memberships else "other")
        buckets[bucket] += period
        functions[bucket][function or "<unresolved>"] += period

    print("capture=%s" % args.capture)
    print("box86 sha256=%s  embedded class-B=%d" % (sha256(args.box86), class_b_count))
    print("wined3d sha256=%s  FDEs=%d" % (sha256(args.wined3d), len(ranges)))
    print("guest-map=%d/%d overflow=%d unresolved-jit-cycles=%d" %
          (metadata["count"], metadata["capacity"], metadata["overflow"], unresolved_jit))
    print("total user cycles=%d; guest wined3d cycles=%d\n" % (total_cycles, wined3d_cycles))
    order = ["A", "B", "C", "D", "shared/ambiguous", "other", "unresolved/unmapped"]
    for bucket in order:
        cycles = buckets[bucket]
        print("%-19s %14d  %6.3f%% all  %6.2f%% guest-wined3d" %
              (bucket, cycles, 100 * cycles / total_cycles,
               100 * cycles / wined3d_cycles if wined3d_cycles else 0))
        for function, value in functions[bucket].most_common(5):
            print("    %12d  %s" % (value, function))
    print("\nNOTE: phase D is ABI-unsafe and is reported only to explain the old capture;")
    print("parent/inlined context_apply_draw_state work cannot be split offline.")


if __name__ == "__main__":
    main()

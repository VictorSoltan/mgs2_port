#!/usr/bin/env python3
"""Resolve Linux perf samples in Box86 dynarec code back to guest x86 blocks.

The Box86 recorder is memory-only.  Its external snapshot starts with the
little-endian header ``MGS2GM01``, followed by the mapping address, record
count, overflow flag, record size and capacity, then 16-byte records:

    native_start, native_size, x86_start, x86_size

This reader performs no access to a live process and is safe to use after a
capture.  Input to --script is the output of ``perf script -F comm,pid,tid,ip,
sym,dso`` and --maps is the matching /proc/PID/maps snapshot.
"""

import argparse
import bisect
import collections
import pathlib
import re
import struct
import sys


HEADER = struct.Struct("<8s5I")
RECORD = struct.Struct("<4I")
SAMPLE = re.compile(
    r"^\s*(?P<comm>.*?)\s+(?P<pid>\d+)/(?P<tid>\d+)\s+"
    r"(?P<ip>[0-9a-fA-F]+)\s+.*\(/tmp/perf-[0-9]+\.map\)\s*$"
)


def read_guest_map(path):
    raw = pathlib.Path(path).read_bytes()
    if len(raw) < HEADER.size:
        raise RuntimeError("guest-map snapshot is shorter than its header")
    magic, address, count, overflow, record_size, capacity = HEADER.unpack_from(raw)
    if magic != b"MGS2GM01":
        raise RuntimeError(f"bad guest-map magic {magic!r}")
    if record_size != RECORD.size:
        raise RuntimeError(f"unsupported record size {record_size}")
    count = min(count, capacity)
    expected = HEADER.size + count * record_size
    if len(raw) < expected:
        raise RuntimeError(f"short guest-map snapshot: expected {expected}, got {len(raw)}")
    records = [RECORD.unpack_from(raw, HEADER.size + i * record_size) for i in range(count)]
    records.sort(key=lambda item: item[0])
    return records, {
        "mapping": address,
        "count": count,
        "capacity": capacity,
        "overflow": overflow,
    }


def read_process_maps(path):
    mappings = []
    for line in pathlib.Path(path).read_text(encoding="ascii").splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) < 5:
            continue
        start_text, end_text = fields[0].split("-", 1)
        pathname = fields[5] if len(fields) == 6 else "[anonymous]"
        mappings.append((
            int(start_text, 16),
            int(end_text, 16),
            int(fields[2], 16),
            pathname,
        ))
    mappings.sort()

    # Wine maps PE sections separately.  Executable gaps between the first and
    # last file-backed section often appear as anonymous mappings even though
    # their guest addresses are still RVAs in the same PE image.  Preserve a
    # module-span view so those hot blocks are not reported as anonymous.
    pe_sections = collections.defaultdict(list)
    for start, end, offset, pathname in mappings:
        if pathname.lower().endswith((".dll", ".exe")):
            pe_sections[pathname].append((start, end, offset))
    pe_spans = []
    for pathname, sections in pe_sections.items():
        image_bases = [start - offset for start, _end, offset in sections]
        image_base = min(image_bases)
        pe_spans.append((image_base, max(end for _start, end, _offset in sections), pathname))
    pe_spans.sort()
    return mappings, pe_spans


def containing(items, starts, address, size_index=1):
    index = bisect.bisect_right(starts, address) - 1
    if index < 0:
        return None
    item = items[index]
    end = item[0] + item[size_index]
    return item if address < end else None


def resolve_module(mappings, mapping_starts, pe_spans, pe_starts, address):
    pe_index = bisect.bisect_right(pe_starts, address) - 1
    if pe_index >= 0:
        image_base, image_end, pathname = pe_spans[pe_index]
        if address < image_end:
            return pathname, address - image_base
    index = bisect.bisect_right(mapping_starts, address) - 1
    if index < 0:
        return "[unmapped]", address
    start, end, offset, pathname = mappings[index]
    if address >= end:
        return "[unmapped]", address
    return pathname, address - start + offset


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--guest-map", required=True)
    parser.add_argument("--script", required=True)
    parser.add_argument("--maps", required=True)
    parser.add_argument("--limit", type=int, default=40)
    args = parser.parse_args()

    try:
        records, metadata = read_guest_map(args.guest_map)
        mappings, pe_spans = read_process_maps(args.maps)
    except (OSError, RuntimeError, struct.error) as error:
        print(f"box86_guest_profile: {error}", file=sys.stderr)
        raise SystemExit(1)

    native_starts = [item[0] for item in records]
    mapping_starts = [item[0] for item in mappings]
    pe_starts = [item[0] for item in pe_spans]
    blocks = collections.Counter()
    blocks_by_thread = collections.defaultdict(collections.Counter)
    modules = collections.Counter()
    jit_samples = 0
    unresolved = 0

    for line in pathlib.Path(args.script).read_text(encoding="utf-8", errors="replace").splitlines():
        match = SAMPLE.match(line)
        if not match:
            continue
        native_ip = int(match.group("ip"), 16)
        record = containing(records, native_starts, native_ip)
        if record is None:
            unresolved += 1
            continue
        _native_start, _native_size, x86_start, x86_size = record
        key = (x86_start, x86_size)
        blocks[key] += 1
        blocks_by_thread[key][f"{match.group('comm').strip()}:{match.group('tid')}"] += 1
        module, _rva = resolve_module(mappings, mapping_starts, pe_spans, pe_starts, x86_start)
        modules[module] += 1
        jit_samples += 1

    print(
        f"records={metadata['count']}/{metadata['capacity']} "
        f"overflow={metadata['overflow']} jit_samples={jit_samples} unresolved={unresolved}"
    )
    print("\nGuest modules:")
    for module, count in modules.most_common(args.limit):
        print(f"{count:7d}  {module}")

    print("\nGuest blocks:")
    for (x86_start, x86_size), count in blocks.most_common(args.limit):
        module, rva = resolve_module(mappings, mapping_starts, pe_spans, pe_starts, x86_start)
        thread = blocks_by_thread[(x86_start, x86_size)].most_common(1)[0]
        print(
            f"{count:7d}  x86={x86_start:#010x}+{x86_size:#x} "
            f"rva={rva:#x}  thread={thread[0]}:{thread[1]}  {module}"
        )


if __name__ == "__main__":
    main()

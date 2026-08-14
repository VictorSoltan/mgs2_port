#!/usr/bin/env python3
"""One-shot external reader for Box86's memory-only MGS2 memmove census.

Run this on the device.  Symbol addresses come from ``nm -g box86`` for the
exact diagnostic binary.  Capture once on arrival at the fixed spot and once
after a bounded interval; pass the first JSON to --baseline so startup traffic
is excluded without ever clearing or logging from the game thread.
"""

import argparse
import collections
import json
import os
import struct
import sys


ENTRY = struct.Struct("<4I")


def read_exact(fd, address, size):
    raw = os.pread(fd, size, address)
    if len(raw) != size:
        raise RuntimeError(f"short read at {address:#x}: expected {size}, got {len(raw)}")
    return raw


def read_u32(fd, address):
    return struct.unpack("<I", read_exact(fd, address, 4))[0]


def read_maps(pid):
    mappings = []
    with open(f"/proc/{pid}/maps", encoding="ascii") as stream:
        for line in stream:
            fields = line.split(maxsplit=5)
            if len(fields) < 5:
                continue
            start_text, end_text = fields[0].split("-", 1)
            mappings.append({
                "start": int(start_text, 16),
                "end": int(end_text, 16),
                "offset": int(fields[2], 16),
                "path": fields[5].strip() if len(fields) == 6 else "[anonymous]",
            })

    pe_sections = collections.defaultdict(list)
    for mapping in mappings:
        if mapping["path"].lower().endswith((".dll", ".exe")):
            pe_sections[mapping["path"]].append(mapping)
    pe_spans = []
    for path, sections in pe_sections.items():
        base = min(item["start"] - item["offset"] for item in sections)
        pe_spans.append((base, max(item["end"] for item in sections), path))
    return mappings, pe_spans


def resolve(address, mappings, pe_spans):
    for base, end, path in pe_spans:
        if base <= address < end:
            return path, address - base
    for mapping in mappings:
        if mapping["start"] <= address < mapping["end"]:
            return (
                mapping["path"],
                address - mapping["start"] + mapping["offset"],
            )
    return "[unmapped]", address


def snapshot(pid, pointer_address, capacity_address, overflow_address):
    fd = os.open(f"/proc/{pid}/mem", os.O_RDONLY)
    try:
        pointer = read_u32(fd, pointer_address)
        capacity = read_u32(fd, capacity_address)
        overflow = read_u32(fd, overflow_address)
        if not pointer:
            raise RuntimeError("memmove census is disabled (mapping pointer is null)")
        if not capacity or capacity > 1 << 20:
            raise RuntimeError(f"invalid census capacity {capacity}")
        raw = read_exact(fd, pointer, capacity * ENTRY.size)
    finally:
        os.close(fd)

    entries = {}
    for offset in range(0, len(raw), ENTRY.size):
        state, caller, size, count = ENTRY.unpack_from(raw, offset)
        if state == 2 and count:
            entries[f"{caller:08x}:{size}"] = count
    return {
        "pid": pid,
        "pointer": pointer,
        "capacity": capacity,
        "overflow": overflow,
        "entries": entries,
    }


def render(current, baseline, mappings, pe_spans, limit):
    before = baseline.get("entries", {}) if baseline else {}
    rows = []
    by_caller = collections.defaultdict(lambda: [0, 0])
    total_calls = 0
    total_bytes = 0

    for key, count in current["entries"].items():
        caller_text, size_text = key.split(":", 1)
        caller = int(caller_text, 16)
        size = int(size_text)
        delta = (count - before.get(key, 0)) & 0xFFFFFFFF
        if not delta:
            continue
        byte_count = delta * size
        path, rva = resolve(caller, mappings, pe_spans)
        rows.append((delta, byte_count, caller, size, path, rva))
        by_caller[(caller, path, rva)][0] += delta
        by_caller[(caller, path, rva)][1] += byte_count
        total_calls += delta
        total_bytes += byte_count

    print(
        f"entries={len(rows)} calls={total_calls} bytes={total_bytes} "
        f"overflow={current['overflow']}"
    )
    print("\nTop caller/size pairs by calls:")
    for calls, byte_count, caller, size, path, rva in sorted(rows, reverse=True)[:limit]:
        print(
            f"{calls:10d} calls {byte_count:12d} bytes  size={size:6d} "
            f"caller={caller:#010x} rva={rva:#x}  {path}"
        )
    print("\nTop callers by calls:")
    ordered = sorted(
        ((values[0], values[1], key) for key, values in by_caller.items()),
        reverse=True,
    )
    for calls, byte_count, (caller, path, rva) in ordered[:limit]:
        print(
            f"{calls:10d} calls {byte_count:12d} bytes  "
            f"caller={caller:#010x} rva={rva:#x}  {path}"
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    parser.add_argument("--pointer-address", required=True, type=lambda value: int(value, 0))
    parser.add_argument("--capacity-address", required=True, type=lambda value: int(value, 0))
    parser.add_argument("--overflow-address", required=True, type=lambda value: int(value, 0))
    parser.add_argument("--baseline")
    parser.add_argument("--output")
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()

    try:
        current = snapshot(
            args.pid,
            args.pointer_address,
            args.capacity_address,
            args.overflow_address,
        )
        baseline = None
        if args.baseline:
            with open(args.baseline, encoding="utf-8") as stream:
                baseline = json.load(stream)
        mappings, pe_spans = read_maps(args.pid)
        if args.output:
            temporary = args.output + ".tmp"
            with open(temporary, "w", encoding="utf-8") as stream:
                json.dump(current, stream, indent=2, sort_keys=True)
                stream.write("\n")
            os.replace(temporary, args.output)
        render(current, baseline, mappings, pe_spans, args.limit)
    except (OSError, RuntimeError, ValueError, struct.error, json.JSONDecodeError) as error:
        print(f"box86_memmove_stats: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()

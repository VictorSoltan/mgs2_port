#!/usr/bin/env python3
"""Read or diff the bounded MGS2 reinforcement submission census.

The diagnostic WineD3D build only updates counters in memory.  This reader
runs outside Wine and takes a coherent snapshot through /proc/<pid>/mem.
"""

import argparse
import json
import os
import struct
import sys


MAGIC = 0x31534352  # RCS1
VERSION = 1
IMAGE_BASE = 0x10000000
HEADER_NAMES = (
    "magic version size_words signature enabled publish_sequence"
).split()
PAYLOAD_NAMES = (
    "cs_presents source_draws source_nonindexed source_indexed "
    "source_direct_packets source_batch_packets "
    "indexed_trianglelist indexed_strip indexed_other "
    "indexed_adjacent_pairs indexed_mergeable_list_pairs "
    "indexed_candidate_strip_pairs break_after_other_draw break_state "
    "break_primitive break_ib break_format_offset break_base "
    "break_instanced break_gap break_unsupported "
    "final_draws final_arrays final_elements final_batch_elements "
    "final_instanced final_other"
).split()
HEADER = struct.Struct(f"<{len(HEADER_NAMES)}I")
PAYLOAD = struct.Struct(f"<{len(PAYLOAD_NAMES)}I")


def find_pid(comm):
    matches = []
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        try:
            with open(f"/proc/{name}/comm", encoding="ascii") as stream:
                if stream.read().strip() == comm:
                    matches.append(int(name))
        except OSError:
            pass
    if len(matches) != 1:
        raise RuntimeError(f"expected one {comm!r} process, found {matches}")
    return matches[0]


def module_base(pid, module):
    with open(f"/proc/{pid}/maps", encoding="ascii") as stream:
        for line in stream:
            fields = line.split()
            if len(fields) >= 6 and fields[2] == "00000000" and fields[-1].endswith(module):
                return int(fields[0].split("-", 1)[0], 16)
    raise RuntimeError(f"offset-zero mapping for {module!r} not found")


def read_exact(fd, address, size):
    data = os.pread(fd, size, address)
    if len(data) != size:
        raise RuntimeError(f"short read at {address:#x}: {len(data)} of {size}")
    return data


def snapshot(pid, module, symbol_vma, image_base):
    address = module_base(pid, module) + symbol_vma - image_base
    fd = os.open(f"/proc/{pid}/mem", os.O_RDONLY)
    try:
        for _ in range(20):
            first_raw = read_exact(fd, address, HEADER.size)
            first = dict(zip(HEADER_NAMES, HEADER.unpack(first_raw)))
            if first["magic"] != MAGIC or first["signature"] != ((~MAGIC) & 0xFFFFFFFF):
                raise RuntimeError(f"bad RCS1 signature at {address:#x}: {first}")
            expected_words = (HEADER.size + PAYLOAD.size) // 4
            if first["version"] != VERSION or first["size_words"] != expected_words:
                raise RuntimeError(f"unsupported RCS1 layout at {address:#x}: {first}")
            if first["publish_sequence"] & 1:
                continue
            payload_raw = read_exact(fd, address + HEADER.size, PAYLOAD.size)
            second_raw = read_exact(fd, address, HEADER.size)
            second = dict(zip(HEADER_NAMES, HEADER.unpack(second_raw)))
            if first["publish_sequence"] == second["publish_sequence"] and not (second["publish_sequence"] & 1):
                counters = dict(zip(PAYLOAD_NAMES, PAYLOAD.unpack(payload_raw)))
                return {
                    "pid": pid,
                    "module": module,
                    "address": hex(address),
                    "enabled": bool(second["enabled"]),
                    "publish_sequence": second["publish_sequence"],
                    "counters": counters,
                }
        raise RuntimeError("census changed during every snapshot attempt")
    finally:
        os.close(fd)


def load(path):
    with open(path, encoding="utf-8") as stream:
        result = json.load(stream)
    # p37's first reader called the raw counter "frames".  A stationary live
    # interval proved that MGS2 submits two CSMT Present commands per displayed
    # Wayland frame, so retain file compatibility while naming the denominator
    # accurately.
    counters = result["counters"]
    if "frames" in counters and "cs_presents" not in counters:
        counters["cs_presents"] = counters.pop("frames")
    return result


def diff(before, after, display_frames=None):
    result = {}
    for name in PAYLOAD_NAMES:
        old = before["counters"][name]
        new = after["counters"][name]
        result[name] = (new - old) & 0xFFFFFFFF
    presents = result["cs_presents"]
    derived = {
        "source_draws_per_cs_present": result["source_draws"] / presents if presents else None,
        "indexed_per_cs_present": result["source_indexed"] / presents if presents else None,
        "mergeable_indexed_list_per_cs_present": (
            result["indexed_mergeable_list_pairs"] / presents if presents else None),
        "final_draws_per_cs_present": result["final_draws"] / presents if presents else None,
    }
    if display_frames is not None:
        derived["display_frames"] = display_frames
        derived["source_draws_per_display_frame"] = (
            result["source_draws"] / display_frames if display_frames else None)
        derived["indexed_per_display_frame"] = (
            result["source_indexed"] / display_frames if display_frames else None)
        derived["final_draws_per_display_frame"] = (
            result["final_draws"] / display_frames if display_frames else None)
    return {"before": before, "after": after, "delta": result, "derived": derived}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int)
    parser.add_argument("--comm", default="mgs2_sse_rg353v")
    parser.add_argument("--module", default="wined3d.dll")
    parser.add_argument("--symbol-vma", type=lambda value: int(value, 0))
    parser.add_argument("--image-base", type=lambda value: int(value, 0), default=IMAGE_BASE)
    parser.add_argument("--output")
    parser.add_argument("--diff", nargs=2, metavar=("BEFORE", "AFTER"))
    parser.add_argument("--display-frames", type=int,
            help="real displayed-frame delta from the external frame log")
    args = parser.parse_args()

    try:
        if args.diff:
            result = diff(load(args.diff[0]), load(args.diff[1]), args.display_frames)
        else:
            if args.symbol_vma is None:
                parser.error("--symbol-vma is required when taking a live snapshot")
            pid = args.pid or find_pid(args.comm)
            result = snapshot(pid, args.module, args.symbol_vma, args.image_base)
        rendered = json.dumps(result, indent=2, sort_keys=True)
        if args.output:
            temporary = args.output + ".tmp"
            with open(temporary, "w", encoding="utf-8") as stream:
                stream.write(rendered + "\n")
            os.replace(temporary, args.output)
        else:
            print(rendered)
    except (OSError, RuntimeError, KeyError, ValueError, struct.error) as error:
        print(f"reinforcement_submit_census: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()

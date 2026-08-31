#!/usr/bin/env python3
"""Sample the research DXVK D3D9 present counter outside the game thread.

The paired D3D9 build exports one 32-bit counter and increments it once per
Present. This reader opens /proc/PID/mem read-only. It never writes or logs from
the renderer and deliberately reports short windows instead of averaging menu,
loading, gameplay and the death screen together.
"""

import argparse
import os
import struct
import time


COUNTER_EXPORT = b"MGS2DxvkPresentCount"


def module_base(pid):
    candidates = []
    with open(f"/proc/{pid}/maps", encoding="ascii") as stream:
        for line in stream:
            fields = line.split()
            if len(fields) < 6 or not fields[-1].lower().endswith("/d3d9.dll"):
                continue
            start = int(fields[0].split("-", 1)[0], 16)
            offset = int(fields[2], 16)
            # Wine maps PE sections at their virtual addresses; later section
            # mappings therefore cannot reconstruct the image base with
            # start-file_offset. The offset-zero mapping is authoritative.
            if offset == 0:
                candidates.append((start, fields[-1]))
    if not candidates:
        raise RuntimeError("no mapped d3d9.dll found")
    bases = {base for base, unused in candidates}
    if len(bases) != 1:
        raise RuntimeError(f"ambiguous d3d9.dll load bases: {sorted(bases)}")
    return candidates[0]


def exported_rva(path, wanted=COUNTER_EXPORT):
    """Resolve one PE32 export without loading the DLL or adding a dependency."""
    with open(path, "rb") as stream:
        image = stream.read()
    if image[:2] != b"MZ" or len(image) < 0x40:
        raise RuntimeError(f"not a PE image: {path}")
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    if image[pe:pe + 4] != b"PE\0\0":
        raise RuntimeError(f"bad PE signature: {path}")
    section_count = struct.unpack_from("<H", image, pe + 6)[0]
    optional_size = struct.unpack_from("<H", image, pe + 20)[0]
    optional = pe + 24
    if struct.unpack_from("<H", image, optional)[0] != 0x10B:
        raise RuntimeError(f"counter DLL is not PE32: {path}")
    export_rva = struct.unpack_from("<I", image, optional + 96)[0]
    section_table = optional + optional_size

    def file_offset(rva):
        for index in range(section_count):
            section = section_table + index * 40
            virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from(
                "<IIII", image, section + 8)
            if virtual_address <= rva < virtual_address + max(virtual_size, raw_size):
                offset = raw_offset + rva - virtual_address
                if offset >= len(image):
                    raise RuntimeError(f"PE RVA outside file: {rva:#x}")
                return offset
        raise RuntimeError(f"unmapped PE RVA: {rva:#x}")

    directory = file_offset(export_rva)
    name_count, functions_rva, names_rva, ordinals_rva = struct.unpack_from(
        "<IIII", image, directory + 24)
    functions = file_offset(functions_rva)
    names = file_offset(names_rva)
    ordinals = file_offset(ordinals_rva)
    for index in range(name_count):
        name_rva = struct.unpack_from("<I", image, names + index * 4)[0]
        name_offset = file_offset(name_rva)
        end = image.find(b"\0", name_offset)
        if image[name_offset:end] != wanted:
            continue
        ordinal = struct.unpack_from("<H", image, ordinals + index * 2)[0]
        return struct.unpack_from("<I", image, functions + ordinal * 4)[0]
    raise RuntimeError(f"PE export {wanted.decode()} not found in {path}")


def read_count(fd, address):
    raw = os.pread(fd, 4, address)
    if len(raw) != 4:
        raise RuntimeError(f"short /proc/PID/mem read at {address:#x}")
    return struct.unpack("<I", raw)[0]


def resolve_rva(path, explicit_rva=None):
    """Resolve the counter address, refusing to guess on a changed DLL."""
    if explicit_rva is not None:
        return explicit_rva, "argument"
    try:
        return exported_rva(path), "PE-export"
    except (OSError, RuntimeError, struct.error) as error:
        raise RuntimeError(
            f"cannot resolve {COUNTER_EXPORT.decode()} from {path}: {error}; "
            "pass an independently verified --rva only for a research build"
        ) from error


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    parser.add_argument("--rva", type=lambda value: int(value, 0),
                        help="counter RVA; default resolves the PE data export")
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--windows", type=int, default=10)
    args = parser.parse_args()
    if args.interval <= 0 or args.windows <= 0:
        parser.error("--interval and --windows must be positive")

    base, path = module_base(args.pid)
    try:
        rva, rva_source = resolve_rva(path, args.rva)
    except RuntimeError as error:
        parser.error(str(error))
    address = base + rva
    fd = os.open(f"/proc/{args.pid}/mem", os.O_RDONLY)
    try:
        previous_count = read_count(fd, address)
        previous_time = time.monotonic_ns()
        print(f"pid={args.pid} module={path} base={base:#x} "
              f"rva={rva:#x} rva_source={rva_source} start={previous_count} "
              f"start_tick_ms={previous_time // 1_000_000}", flush=True)
        print("window\ttick_ms\tframes\telapsed_ms\tfps\ttotal", flush=True)
        deadline = previous_time
        for window in range(1, args.windows + 1):
            deadline += int(args.interval * 1_000_000_000)
            delay = (deadline - time.monotonic_ns()) / 1_000_000_000
            if delay > 0:
                time.sleep(delay)
            now = time.monotonic_ns()
            current = read_count(fd, address)
            frames = (current - previous_count) & 0xFFFFFFFF
            elapsed_ms = (now - previous_time) / 1_000_000
            fps = frames * 1000.0 / elapsed_ms
            print(f"{window}\t{now // 1_000_000}\t{frames}\t{elapsed_ms:.3f}\t{fps:.3f}\t{current}",
                  flush=True)
            previous_count = current
            previous_time = now
    finally:
        os.close(fd)


if __name__ == "__main__":
    main()

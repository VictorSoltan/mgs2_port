#!/usr/bin/env python3
"""Snapshot the bounded Box86 guest/native JIT map from a live process.

The matching Box86 recorder only appends a 16-byte record when it compiles a
new dynablock.  This reader runs out of process, resolves the exported state
symbols from the exact Box86 ELF, and writes the format consumed by
``box86_guest_profile.py``.
"""

import argparse
import os
import pathlib
import struct
import subprocess
import sys


HEADER = struct.Struct("<8s5I")
RECORD_SIZE = 16
SYMBOLS = (
    "mgs2_guest_map",
    "mgs2_guest_map_count",
    "mgs2_guest_map_overflow",
    "mgs2_guest_map_capacity",
)


def symbol_addresses(path):
    result = subprocess.run(
        ["readelf", "-Ws", path],
        check=True,
        capture_output=True,
        text=True,
    )
    addresses = {}
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 8 and fields[-1] in SYMBOLS:
            addresses.setdefault(fields[-1], int(fields[1], 16))
    missing = [name for name in SYMBOLS if name not in addresses]
    if missing:
        raise RuntimeError("missing Box86 symbols: %s" % ", ".join(missing))
    return addresses


def read_exact(fd, address, size):
    data = os.pread(fd, size, address)
    if len(data) != size:
        raise RuntimeError(
            "short process-memory read at %#x: expected %d, got %d"
            % (address, size, len(data))
        )
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", required=True, type=int)
    parser.add_argument("--box86", default="/usr/bin/box86")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    try:
        symbols = symbol_addresses(args.box86)
        fd = os.open("/proc/%d/mem" % args.pid, os.O_RDONLY)
        try:
            pointer = struct.unpack(
                "<I", read_exact(fd, symbols["mgs2_guest_map"], 4)
            )[0]
            count = struct.unpack(
                "<I", read_exact(fd, symbols["mgs2_guest_map_count"], 4)
            )[0]
            overflow = struct.unpack(
                "<I", read_exact(fd, symbols["mgs2_guest_map_overflow"], 4)
            )[0]
            capacity = struct.unpack(
                "<I", read_exact(fd, symbols["mgs2_guest_map_capacity"], 4)
            )[0]
            if not pointer:
                raise RuntimeError(
                    "guest map is not allocated; launch with MGS2_BOX86_GUEST_MAP=1"
                )
            if not capacity or capacity > 1_048_576:
                raise RuntimeError("implausible guest-map capacity %d" % capacity)
            saved_count = min(count, capacity)
            records = read_exact(fd, pointer, saved_count * RECORD_SIZE)
        finally:
            os.close(fd)

        output = pathlib.Path(args.output)
        temporary = output.with_name(output.name + ".tmp")
        temporary.write_bytes(
            HEADER.pack(
                b"MGS2GM01", pointer, saved_count, overflow,
                RECORD_SIZE, capacity,
            )
            + records
        )
        temporary.replace(output)
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print("box86_guest_snapshot: %s" % error, file=sys.stderr)
        raise SystemExit(1)

    print(
        "pid=%d mapping=%#x records=%d/%d overflow=%d output=%s"
        % (args.pid, pointer, saved_count, capacity, overflow, output)
    )


if __name__ == "__main__":
    main()

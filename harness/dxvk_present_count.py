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


DEFAULT_RVA = 0x30F040


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


def read_count(fd, address):
    raw = os.pread(fd, 4, address)
    if len(raw) != 4:
        raise RuntimeError(f"short /proc/PID/mem read at {address:#x}")
    return struct.unpack("<I", raw)[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    parser.add_argument("--rva", type=lambda value: int(value, 0),
                        default=DEFAULT_RVA)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--windows", type=int, default=10)
    args = parser.parse_args()
    if args.interval <= 0 or args.windows <= 0:
        parser.error("--interval and --windows must be positive")

    base, path = module_base(args.pid)
    address = base + args.rva
    fd = os.open(f"/proc/{args.pid}/mem", os.O_RDONLY)
    try:
        previous_count = read_count(fd, address)
        previous_time = time.monotonic_ns()
        print(f"pid={args.pid} module={path} base={base:#x} "
              f"rva={args.rva:#x} start={previous_count}", flush=True)
        print("window\tframes\telapsed_ms\tfps\ttotal", flush=True)
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
            print(f"{window}\t{frames}\t{elapsed_ms:.3f}\t{fps:.3f}\t{current}",
                  flush=True)
            previous_count = current
            previous_time = now
    finally:
        os.close(fd)


if __name__ == "__main__":
    main()

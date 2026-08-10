#!/usr/bin/env python3
"""Temporarily switch the bounded dmsynth recorder in an existing process.

This is diagnostic-only and specific to dmsynth_se3_state1/se4_unmute1.  It
validates the exported state magic before touching the DLL's cached env flag.
"""

import argparse
import os
import struct
import sys


MAGIC = 0x31545344
STATE_RVA = 0x3BEA8
ENABLED_CACHE_RVA = 0x3A03C


def module_base(pid):
    with open(f"/proc/{pid}/maps", encoding="ascii") as stream:
        for line in stream:
            fields = line.split()
            if (
                len(fields) >= 6
                and fields[1].startswith("r-x")
                and fields[2] == "00000000"
                and "dmsynth.dll" in fields[-1]
            ):
                return int(fields[0].split("-", 1)[0], 16)
    raise RuntimeError("dmsynth.dll mapping not found")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    parser.add_argument("enabled", type=int, choices=(0, 1))
    args = parser.parse_args()

    try:
        base = module_base(args.pid)
        state = base + STATE_RVA
        cache = base + ENABLED_CACHE_RVA
        value = struct.pack("<I", args.enabled)
        fd = os.open(f"/proc/{args.pid}/mem", os.O_RDWR)
        try:
            magic = struct.unpack("<I", os.pread(fd, 4, state))[0]
            if magic != MAGIC:
                raise RuntimeError(f"bad state magic {magic:#x} at {state:#x}")
            os.pwrite(fd, value, cache)
            os.pwrite(fd, value, state + 6 * 4)
            cache_value = struct.unpack("<I", os.pread(fd, 4, cache))[0]
            state_value = struct.unpack("<I", os.pread(fd, 4, state + 6 * 4))[0]
        finally:
            os.close(fd)
        print(
            f"pid={args.pid} base={base:#x} cache={cache:#x}:{cache_value} "
            f"state={state + 6 * 4:#x}:{state_value}"
        )
    except (OSError, RuntimeError, struct.error) as error:
        print(f"dmsynth_state_control: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()

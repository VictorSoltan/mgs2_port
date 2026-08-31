#!/usr/bin/env python3
"""Read the exact MGS2 DG_WinApp.flag DWORD outside the game process.

The legal executable's startup code stores its completed flag word through
``a3 88 69 f8 00``.  Pin that surrounding FINALPLAY21 instruction sequence and
the image base before using its absolute address.  The recovered map belongs
to a different link and must not be used as a live-data address.  This is a
one-shot read and writes nothing to the game.
"""

import argparse
import os
import struct
import sys


IMAGE_BASE = 0x00400000
DG_WINAPP_FLAG = 0x00F86988
FLAG_STORE_CODE = 0x008A2938
FINALPLAY21_CODE = bytes.fromhex(
    "85c974050d004000008b0d841619010d0000000085c9a38869f800")
IMAGE_NAME = "mgs2_sse_rg353vs_port.exe"


def verify_image(pid):
    matches = []
    with open(f"/proc/{pid}/maps", encoding="ascii") as stream:
        for line in stream:
            fields = line.split()
            if len(fields) < 6 or os.path.basename(fields[5]).lower() != IMAGE_NAME:
                continue
            start = int(fields[0].split("-", 1)[0], 16)
            offset = int(fields[2], 16)
            if offset == 0:
                matches.append(start)
    if matches != [IMAGE_BASE]:
        rendered = ",".join(hex(value) for value in matches) or "none"
        raise RuntimeError(
            f"refusing unexpected {IMAGE_NAME} image base(s): {rendered}")


def read_exact(fd, size, address):
    raw = os.pread(fd, size, address)
    if len(raw) != size:
        raise RuntimeError(
            f"short read at {address:#x}: expected {size}, got {len(raw)}")
    return raw


def read_flag(pid):
    verify_image(pid)
    fd = os.open(f"/proc/{pid}/mem", os.O_RDONLY)
    try:
        code = read_exact(fd, len(FINALPLAY21_CODE), FLAG_STORE_CODE)
        if code != FINALPLAY21_CODE:
            raise RuntimeError(
                "refusing game image without the exact FINALPLAY21 flag-store code")
        raw = read_exact(fd, 4, DG_WINAPP_FLAG)
    finally:
        os.close(fd)
    return struct.unpack("<I", raw)[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    args = parser.parse_args()
    try:
        flag = read_flag(args.pid)
    except (OSError, RuntimeError, struct.error) as error:
        print(f"mgs2_winapp_flag: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(
        "DG_WinApp.flag=0x%08x use_vertexshader_bit8=%d "
        "patch_vertexshader_bit17=%d"
        % (flag, bool(flag & (1 << 8)), bool(flag & (1 << 17))))


if __name__ == "__main__":
    main()

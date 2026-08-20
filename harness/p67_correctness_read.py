#!/usr/bin/env python3
"""Read p67/p68 TLS, draw-census and frame-witness records from a live process."""

import argparse
import pathlib
import re
import struct
import subprocess


DRAW = struct.Struct("<18I")
FRAME_HEAD = struct.Struct("<8I")
FRAME_SAMPLE = struct.Struct("<6I")
FRAME_SLOTS = 64


def symbol_value(path, name):
    out = subprocess.check_output(["readelf", "-Ws", path], text=True)
    matches = []
    for line in out.splitlines():
        fields = line.split()
        if len(fields) >= 8 and fields[-1] == name and fields[6] != "UND":
            matches.append(int(fields[1], 16))
    if not matches:
        raise RuntimeError(f"symbol {name!r} not found in {path}")
    if len(set(matches)) != 1:
        raise RuntimeError(f"symbol {name!r} has conflicting values in {path}")
    return matches[0]


def elf_type(path):
    out = subprocess.check_output(["readelf", "-h", path], text=True)
    match = re.search(r"^\s*Type:\s+(\S+)", out, re.MULTILINE)
    if not match:
        raise RuntimeError(f"cannot read ELF type from {path}")
    return match.group(1)


def mapped_base(pid, path):
    resolved = str(pathlib.Path(path).resolve())
    candidates = []
    for line in pathlib.Path(f"/proc/{pid}/maps").read_text().splitlines():
        fields = line.split()
        if len(fields) < 6:
            continue
        mapped = fields[-1].removesuffix(" (deleted)")
        try:
            same = str(pathlib.Path(mapped).resolve()) == resolved
        except OSError:
            same = mapped == resolved
        if same:
            start = int(fields[0].split("-", 1)[0], 16)
            offset = int(fields[2], 16)
            candidates.append(start - offset)
    if not candidates:
        raise RuntimeError(f"{path} is not mapped in pid {pid}")
    if len(set(candidates)) != 1:
        raise RuntimeError(f"inconsistent load bases for {path}: {candidates}")
    return candidates[0]


def runtime_address(pid, path, symbol):
    value = symbol_value(path, symbol)
    if elf_type(path) == "EXEC":
        return value
    return mapped_base(pid, path) + value


def read_exact(mem, address, size):
    mem.seek(address)
    raw = mem.read(size)
    if len(raw) != size:
        raise RuntimeError(f"short /proc/PID/mem read at {address:#x}")
    return raw


def read_stable(mem, address, size, sequence_offset=None):
    for _ in range(8):
        raw1 = read_exact(mem, address, size)
        raw2 = read_exact(mem, address, size)
        if raw1 != raw2:
            continue
        if sequence_offset is not None:
            seq = struct.unpack_from("<I", raw1, sequence_offset)[0]
            if seq & 1:
                continue
        return raw1
    raise RuntimeError("record changed throughout the bounded read")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pid", type=int)
    ap.add_argument("--box86", default="/usr/bin/box86")
    ap.add_argument("--wayland", default="/usr/lib/wine/i386-unix/winewayland.so")
    a = ap.parse_args()

    draw_addr = runtime_address(a.pid, a.box86, "mgs2_p67_draw_correctness")
    frame_addr = runtime_address(a.pid, a.wayland, "mgs2_p67_frame_witness")
    with open(f"/proc/{a.pid}/mem", "rb", buffering=0) as mem:
        draw = DRAW.unpack(read_stable(mem, draw_addr, DRAW.size))
        frame_size = FRAME_HEAD.size + FRAME_SLOTS * FRAME_SAMPLE.size
        frame_raw = read_stable(mem, frame_addr, frame_size, 5 * 4)

    if draw[:4] != (0x31435244, 1, 18, 0xCEBCADBB):
        raise RuntimeError(f"bad DRAW record header: {draw[:4]}")
    head = FRAME_HEAD.unpack_from(frame_raw)
    if head[:4] != (0x3157464D, 1, 392, 0xCEA8B9B2):
        raise RuntimeError(f"bad frame record header: {head[:4]}")

    tls_state = {0: "WAITING", 1: "READY", 0xFFFFFFFF: "REFUSED"}.get(draw[5], str(draw[5]))
    print(f"draw record @ {draw_addr:#x}: enabled={draw[4]}")
    print(f"TLS {tls_state}: attempts={draw[6]} guest={draw[7]} "
          f"native_before={draw[8]} native_after={draw[9]}")
    print(f"draws: source={draw[10]} guest_fallback={draw[11]} final={draw[12]}")
    print(f"final kinds: arrays={draw[13]} elements={draw[14]} "
          f"batch={draw[15]} instanced={draw[16]} other={draw[17]}")

    samples = []
    for i in range(FRAME_SLOTS):
        sample = FRAME_SAMPLE.unpack_from(frame_raw, FRAME_HEAD.size + i * FRAME_SAMPLE.size)
        if sample[0]:
            samples.append(sample)
    samples.sort(key=lambda sample: sample[0])
    hashes = {sample[3] for sample in samples}
    print(f"frame witness @ {frame_addr:#x}: enabled={head[4]} frames={head[6]} "
          f"retained={len(samples)} unique_hashes={len(hashes)}")
    if samples:
        first, last = samples[0], samples[-1]
        min_lit = min(sample[4] for sample in samples)
        min_changed = min(sample[5] for sample in samples)
        print(f"retained frames {first[0]}..{last[0]}, {last[1]}x{last[2]}, "
              f"min_lit={min_lit}/256 min_changed={min_changed}/255 "
              f"last_hash={last[3]:08x}")


if __name__ == "__main__":
    main()

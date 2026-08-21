#!/usr/bin/env python3
"""Read p69 state-apply, final-draw and frame witnesses from a live process."""

import argparse
import pathlib
import struct

import p67_correctness_read as p67


P69 = struct.Struct("<8I")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pid", type=int)
    ap.add_argument("--box86", default="/usr/bin/box86")
    ap.add_argument("--wayland", default="/usr/lib/wine/i386-unix/winewayland.so")
    a = ap.parse_args()

    p69_addr = p67.runtime_address(a.pid, a.box86, "mgs2_p69_correctness")
    draw_addr = p67.runtime_address(a.pid, a.box86, "mgs2_p67_draw_correctness")
    frame_addr = p67.runtime_address(a.pid, a.wayland, "mgs2_p67_frame_witness")
    with open(f"/proc/{a.pid}/mem", "rb", buffering=0) as mem:
        # These counters change once per draw and often cannot produce two
        # byte-identical consecutive reads while the renderer is live. Bound
        # the draw snapshot between two p69 reads instead. A stopped process
        # produces equal endpoints; a live process reports the interval rather
        # than pretending that independently sampled counters are simultaneous.
        p69_before = P69.unpack(p67.read_exact(mem, p69_addr, P69.size))
        draw = p67.DRAW.unpack(p67.read_exact(mem, draw_addr, p67.DRAW.size))
        p69 = P69.unpack(p67.read_exact(mem, p69_addr, P69.size))
        frame_size = p67.FRAME_HEAD.size + p67.FRAME_SLOTS * p67.FRAME_SAMPLE.size
        frame_raw = p67.read_stable(mem, frame_addr, frame_size, 5 * 4)

    if p69_before[:4] != (0x31413950, 1, 8, 0xCEBEC6AF) or p69[:4] != p69_before[:4]:
        raise RuntimeError(f"bad p69 record header: {p69_before[:4]} / {p69[:4]}")
    if draw[:4] != (0x31435244, 1, 18, 0xCEBCADBB):
        raise RuntimeError(f"bad DRAW record header: {draw[:4]}")
    head = p67.FRAME_HEAD.unpack_from(frame_raw)
    if head[:4] != (0x3157464D, 1, 392, 0xCEA8B9B2):
        raise RuntimeError(f"bad frame record header: {head[:4]}")

    calls = str(p69[5]) if p69_before[5] == p69[5] else f"{p69_before[5]}..{p69[5]}"
    print(f"p69 record @ {p69_addr:#x}: enabled={p69[4]} calls={calls} "
          f"false={p69[6]} guest_fallback={p69[7]}")
    print(f"final draws @ {draw_addr:#x}: total={draw[12]} arrays={draw[13]} "
          f"elements={draw[14]} batch={draw[15]} instanced={draw[16]} other={draw[17]}")

    samples = []
    for i in range(p67.FRAME_SLOTS):
        sample = p67.FRAME_SAMPLE.unpack_from(
                frame_raw, p67.FRAME_HEAD.size + i * p67.FRAME_SAMPLE.size)
        if sample[0]:
            samples.append(sample)
    samples.sort(key=lambda sample: sample[0])
    hashes = {sample[3] for sample in samples}
    print(f"frame witness @ {frame_addr:#x}: enabled={head[4]} frames={head[6]} "
          f"retained={len(samples)} unique_hashes={len(hashes)}")
    if samples:
        first, last = samples[0], samples[-1]
        print(f"retained frames {first[0]}..{last[0]}, {last[1]}x{last[2]}, "
              f"min_lit={min(s[4] for s in samples)}/256 "
              f"min_changed={min(s[5] for s in samples)}/255 "
              f"last_hash={last[3]:08x}")


if __name__ == "__main__":
    main()

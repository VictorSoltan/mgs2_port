#!/usr/bin/env python3
"""Read p70 phase-A, final-draw and frame witnesses from a live process."""

import argparse
import struct

import p67_correctness_read as p67


PHASE_A = struct.Struct("<7I")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pid", type=int)
    ap.add_argument("--box86", default="/usr/bin/box86")
    ap.add_argument("--wayland", default="/usr/lib/wine/i386-unix/winewayland.so")
    a = ap.parse_args()

    phase_addr = p67.runtime_address(a.pid, a.box86, "mgs2_phase_a_correctness")
    draw_addr = p67.runtime_address(a.pid, a.box86, "mgs2_p67_draw_correctness")
    frame_addr = p67.runtime_address(a.pid, a.wayland, "mgs2_p67_frame_witness")
    with open(f"/proc/{a.pid}/mem", "rb", buffering=0) as mem:
        # Bound the independently changing final-draw snapshot between two
        # phase-A reads. A stopped process gives equal endpoints; a live one
        # reports the interval instead of inventing simultaneity.
        phase_before = PHASE_A.unpack(p67.read_exact(mem, phase_addr, PHASE_A.size))
        draw = p67.DRAW.unpack(p67.read_exact(mem, draw_addr, p67.DRAW.size))
        phase = PHASE_A.unpack(p67.read_exact(mem, phase_addr, PHASE_A.size))
        frame_size = p67.FRAME_HEAD.size + p67.FRAME_SLOTS * p67.FRAME_SAMPLE.size
        frame_raw = p67.read_stable(mem, frame_addr, frame_size, 5 * 4)

    expected = (0x31413050, 1, 7, 0xCEBECFAF)
    if phase_before[:4] != expected or phase[:4] != expected:
        raise RuntimeError(f"bad phase-A record header: {phase_before[:4]} / {phase[:4]}")
    if draw[:4] != (0x31435244, 1, 18, 0xCEBCADBB):
        raise RuntimeError(f"bad DRAW record header: {draw[:4]}")
    head = p67.FRAME_HEAD.unpack_from(frame_raw)
    if head[:4] != (0x3157464D, 1, 392, 0xCEA8B9B2):
        raise RuntimeError(f"bad frame record header: {head[:4]}")

    calls = str(phase[5]) if phase_before[5] == phase[5] else f"{phase_before[5]}..{phase[5]}"
    fallbacks = (str(phase[6]) if phase_before[6] == phase[6]
                 else f"{phase_before[6]}..{phase[6]}")
    print(f"phase A @ {phase_addr:#x}: enabled={phase[4]} calls={calls} "
          f"guest_fallback={fallbacks}")
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

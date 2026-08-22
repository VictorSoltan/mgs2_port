#!/usr/bin/env python3
"""Read p71's native draw-state witnesses from a live process.

Three records, all memory-only:

    p69 record       calls, FALSE returns, guest fallbacks for entry 39
    p71 witness      what the driver actually had bound, sampled every 4,096
                     native applications: current program, program pipeline,
                     draw framebuffer, glGetError, plus zero-program and
                     GL-error sample counts
    frame witness    the presenter's lit/changed/unique frame hashes

The p71 witness exists because p69's failure was a wrong shader program id read
32 bytes early from a shared FFP cache node.  A picture check alone cannot say
whether the right program was bound; this can.
"""

import argparse
import struct

import p67_correctness_read as p67


P69 = struct.Struct("<8I")
WITNESS = struct.Struct("<13I")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pid", type=int)
    ap.add_argument("--box86", default="/usr/bin/box86")
    ap.add_argument("--wayland", default="/usr/lib/wine/i386-unix/winewayland.so")
    a = ap.parse_args()

    p69_addr = p67.runtime_address(a.pid, a.box86, "mgs2_p69_correctness")
    witness_addr = p67.runtime_address(a.pid, a.box86, "mgs2_p71_witness")
    draw_addr = p67.runtime_address(a.pid, a.box86, "mgs2_p67_draw_correctness")
    frame_addr = p67.runtime_address(a.pid, a.wayland, "mgs2_p67_frame_witness")

    with open(f"/proc/{a.pid}/mem", "rb", buffering=0) as mem:
        before = P69.unpack(p67.read_exact(mem, p69_addr, P69.size))
        witness = WITNESS.unpack(p67.read_exact(mem, witness_addr, WITNESS.size))
        draw = p67.DRAW.unpack(p67.read_exact(mem, draw_addr, p67.DRAW.size))
        after = P69.unpack(p67.read_exact(mem, p69_addr, P69.size))
        frame_size = p67.FRAME_HEAD.size + p67.FRAME_SLOTS * p67.FRAME_SAMPLE.size
        frame_raw = p67.read_stable(mem, frame_addr, frame_size, 5 * 4)

    if before[0] != 0x31413950:   # 'P9A1', the entry-39 record
        raise RuntimeError(f"bad p69 record header: {before[:4]}")
    if witness[0] != 0x31375750:
        raise RuntimeError(f"bad p71 witness header: {witness[:4]}")

    def span(index):
        return (str(after[index]) if before[index] == after[index]
                else f"{before[index]}..{after[index]}")

    print(f"p71 calls @ {p69_addr:#x}: enabled={after[4]} calls={span(5)} "
          f"FALSE={span(6)} guest_fallback={span(7)}")
    print(f"shader witness @ {witness_addr:#x}: enabled={witness[4]} "
          f"samples={witness[5]} gl_resolved={witness[6]}")
    print(f"    last program={witness[7]} pipeline={witness[8]} "
          f"draw_fbo={witness[9]} gl_error={witness[10]:#x}")
    print(f"    zero-program samples={witness[11]}  gl-error samples={witness[12]}")
    print(f"final draws @ {draw_addr:#x}: total={draw[12]} arrays={draw[13]} "
          f"elements={draw[14]} batch={draw[15]}")

    head = p67.FRAME_HEAD.unpack_from(frame_raw)
    samples = []
    for i in range(p67.FRAME_SLOTS):
        sample = p67.FRAME_SAMPLE.unpack_from(
                frame_raw, p67.FRAME_HEAD.size + i * p67.FRAME_SAMPLE.size)
        if sample[0]:
            samples.append(sample)
    samples.sort(key=lambda sample: sample[0])
    hashes = {sample[3] for sample in samples}
    print(f"frame witness @ {frame_addr:#x}: frames={head[6]} "
          f"retained={len(samples)} unique={len(hashes)}")
    if samples:
        print(f"    frames {samples[0][0]}..{samples[-1][0]}, "
              f"min_lit={min(s[4] for s in samples)}/256 "
              f"min_changed={min(s[5] for s in samples)}/255 "
              f"last_hash={samples[-1][3]:08x}")


if __name__ == "__main__":
    main()

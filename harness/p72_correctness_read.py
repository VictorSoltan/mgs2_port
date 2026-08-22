#!/usr/bin/env python3
"""Read p72's fused-root correctness records and the GL-work census.

Two questions in one run:

    correctness   does the fused A+B+C native root produce the right picture,
                  with source calls, guest fallbacks and final submissions
                  agreeing?
    structure     what is the driver actually asked to do per frame?  The
                  renderer profile puts 42.5% of user cycles inside libmali,
                  which no amount of porting removes; the census counts the work
                  by family so the next root is chosen from data.

The census lives in the guest DLL, so its address comes from the mapped
wined3d.dll rather than from Box86.
"""

import argparse
import pathlib
import re
import struct
import subprocess

import p67_correctness_read as p67


P72 = struct.Struct("<7I")
CENSUS = struct.Struct("<13I")
CENSUS_FIELDS = ("ext_calls", "draw_state_applies", "state_apply_callbacks",
                 "uniform_loads", "program_selects", "texture_binds",
                 "sampler_applies", "shader_resource_binds", "fbo_checks")


def guest_symbol_rva(dll, name):
    """RVA of an exported/global symbol in the unstripped guest DLL."""
    out = subprocess.run(["i686-w64-mingw32-nm", dll], capture_output=True, text=True).stdout
    for line in out.splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[2] in (name, "_" + name):
            return int(fields[0], 16) - 0x10000000
    raise SystemExit(f"{name} not found in {dll}")


def mapped_dll_base(pid, needle="wined3d.dll"):
    lowest = None
    for line in pathlib.Path(f"/proc/{pid}/maps").read_text().splitlines():
        if needle in line:
            start = int(line.split("-", 1)[0], 16)
            lowest = start if lowest is None else min(lowest, start)
    if lowest is None:
        raise SystemExit(f"{needle} is not mapped in pid {pid}")
    return lowest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pid", type=int)
    ap.add_argument("--box86", default="/usr/bin/box86")
    ap.add_argument("--wayland", default="/usr/lib/wine/i386-unix/winewayland.so")
    ap.add_argument("--dll", help="unstripped paired wined3d.dll, for the census RVA")
    ap.add_argument("--census-rva", type=lambda v: int(v, 0),
                    help="RVA of mgs2_gl_census, when no i686 nm exists on this host")
    a = ap.parse_args()

    p72_addr = p67.runtime_address(a.pid, a.box86, "mgs2_p72_correctness")
    draw_addr = p67.runtime_address(a.pid, a.box86, "mgs2_p67_draw_correctness")
    # The candidate configuration runs the PRODUCTION presenter, which carries no
    # frame witness. That is deliberate, so its absence must not stop the read:
    # the routing and submission records are the point here.
    try:
        frame_addr = p67.runtime_address(a.pid, a.wayland, "mgs2_p67_frame_witness")
    except Exception:
        frame_addr = None
    census_addr = None
    if a.census_rva is not None:
        census_addr = mapped_dll_base(a.pid) + a.census_rva
    elif a.dll:
        census_addr = mapped_dll_base(a.pid) + guest_symbol_rva(a.dll, "mgs2_gl_census")

    with open(f"/proc/{a.pid}/mem", "rb", buffering=0) as mem:
        before = P72.unpack(p67.read_exact(mem, p72_addr, P72.size))
        draw = p67.DRAW.unpack(p67.read_exact(mem, draw_addr, p67.DRAW.size))
        after = P72.unpack(p67.read_exact(mem, p72_addr, P72.size))
        census = (CENSUS.unpack(p67.read_exact(mem, census_addr, CENSUS.size))
                  if census_addr else None)
        frame_raw = None
        if frame_addr is not None:
            frame_size = p67.FRAME_HEAD.size + p67.FRAME_SLOTS * p67.FRAME_SAMPLE.size
            frame_raw = p67.read_stable(mem, frame_addr, frame_size, 5 * 4)

    if before[0] != 0x32374350:
        raise SystemExit(f"bad p72 record header: {before[:4]}")

    def span(i):
        return str(after[i]) if before[i] == after[i] else f"{before[i]}..{after[i]}"

    print(f"p72 fused root @ {p72_addr:#x}: enabled={after[4]} calls={span(5)} "
          f"guest_fallback={span(6)}")
    print(f"final draws @ {draw_addr:#x}: total={draw[12]} arrays={draw[13]} "
          f"elements={draw[14]} batch={draw[15]}")

    if frame_raw is None:
        print("frame witness: not present (production presenter)")
        if census:
            if census[0] != 0x314c4743:
                raise SystemExit(f"bad census header: {census[:4]}")
            print(f"\nGL-work census @ {census_addr:#x}")
            for name, value in zip(CENSUS_FIELDS, census[4:]):
                print(f"    {name:<24} {value:>12}")
        return

    head = p67.FRAME_HEAD.unpack_from(frame_raw)
    samples = []
    for i in range(p67.FRAME_SLOTS):
        s = p67.FRAME_SAMPLE.unpack_from(
                frame_raw, p67.FRAME_HEAD.size + i * p67.FRAME_SAMPLE.size)
        if s[0]:
            samples.append(s)
    samples.sort(key=lambda s: s[0])
    frames = head[6]
    print(f"frame witness @ {frame_addr:#x}: frames={frames} retained={len(samples)} "
          f"unique={len({s[3] for s in samples})}")
    if samples:
        print(f"    frames {samples[0][0]}..{samples[-1][0]}, "
              f"min_lit={min(s[4] for s in samples)}/256 "
              f"min_changed={min(s[5] for s in samples)}/255")

    if census:
        if census[0] != 0x314c4743:
            raise SystemExit(f"bad census header: {census[:4]}")
        print(f"\nGL-work census @ {census_addr:#x}   (per frame over {frames} frames)")
        for name, value in zip(CENSUS_FIELDS, census[4:]):
            per_frame = value / frames if frames else 0.0
            print(f"    {name:<24} {value:>12}   {per_frame:>10.1f} /frame")
        draws = draw[12] or 1
        print(f"    {'ext GL calls per draw':<24} "
              f"{census[4] / draws:>12.1f}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Read or diff the bounded MGS2 packet-break census (patch 38).

Patch 37 answered how many source draws became how many GL submissions.  This
reader adds the p38 record: why each pending batch closed, and whether the two
real draws that each closure separates were issued under an identical effective
rendering state.

The diagnostic WineD3D build only updates counters in memory.  This reader runs
outside Wine and takes a coherent snapshot through /proc/<pid>/mem, exactly like
harness/reinforcement_submit_census.py.  It never writes to the process.
"""

import argparse
import json
import os
import struct
import sys

MAGIC = 0x38335250  # PR38
VERSION = 1
IMAGE_BASE = 0x10000000

HEADER_NAMES = "magic version size_words signature enabled publish_sequence".split()
HEADER = struct.Struct(f"<{len(HEADER_NAMES)}I")

BREAK_REASONS = (
    "cs_barrier", "state_dirty", "indexed", "topology",
    "context", "batch_limit", "present", "other",
)
DIRTY_CATS = (
    "render_state", "texture_stage", "sampler", "texture", "shader",
    "shader_constants", "vertex_decl", "stream_vb", "index_buffer",
    "viewport_scissor", "framebuffer", "blend_depth_raster", "transform", "other",
)
LEN_BUCKETS = ("1", "2", "3-4", "5-8", "9-16", "17-32", "33-63", "64+")
PRIMS = ("points", "lines", "linestrip", "trianglelist",
         "trianglestrip", "trianglefan", "other", "undefined")

# Mirrors enum wined3d_cs_op in dlls/wined3d/cs.c.  Slot 55 is the catch-all.
CS_OPS = [
    "NOP", "PRESENT", "CLEAR", "DISPATCH", "DRAW", "DRAW_BATCH", "FLUSH",
    "SET_PREDICATION", "SET_VIEWPORTS", "SET_SCISSOR_RECTS",
    "SET_RENDERTARGET_VIEWS", "SET_DEPTH_STENCIL_VIEW",
    "SET_VERTEX_DECLARATION", "SET_STREAM_SOURCES", "SET_STREAM_OUTPUTS",
    "SET_INDEX_BUFFER", "SET_CONSTANT_BUFFERS", "SET_TEXTURE",
    "SET_SHADER_RESOURCE_VIEWS", "SET_UNORDERED_ACCESS_VIEWS", "SET_SAMPLERS",
    "SET_SHADER", "SET_BLEND_STATE", "SET_DEPTH_STENCIL_STATE",
    "SET_RASTERIZER_STATE", "SET_DEPTH_BOUNDS", "SET_RENDER_STATE",
    "SET_TEXTURE_STATE", "SET_COLOR_KEY", "SET_LIGHT", "SET_LIGHT_ENABLE",
    "SET_EXTRA_VS_ARGS", "SET_EXTRA_PS_ARGS", "SET_FEATURE_LEVEL",
    "PUSH_CONSTANTS", "RESET_STATE", "CALLBACK", "QUERY_ISSUE",
    "PRELOAD_RESOURCE", "UNLOAD_RESOURCE", "MAP", "UNMAP", "MAP_BO_ADDRESS",
    "BLT_SUB_RESOURCE", "UPDATE_SUB_RESOURCE", "ADD_DIRTY_TEXTURE_REGION",
    "CLEAR_SYSMEM_TEXTURE", "CLEAR_UNORDERED_ACCESS_VIEW", "COPY_UAV_COUNTER",
    "GENERATE_MIPMAPS", "DECODE", "EXECUTE_COMMAND_LIST", "STOP",
]
CS_OPS += [f"op{i}" for i in range(len(CS_OPS), 55)] + ["other_or_unknown"]
assert len(CS_OPS) == 56

# struct mgs2_p38_payload, in declaration order.
LAYOUT = (
    ("close_total", 1),
    ("close_reason", len(BREAK_REASONS)),
    ("close_cs_opcode", 56),
    ("close_dirty_total", 1),
    ("close_dirty_mixed", 1),
    ("close_dirty_cat", len(DIRTY_CATS)),
    ("close_len_hist", len(LEN_BUCKETS)),
    ("boundary_state_equal", 1),
    ("boundary_state_different", 1),
    ("boundary_state_no_next_draw", 1),
    ("boundary_mergeable", 1),
    ("run_ops", 1),
    ("run_ops_comparable", 1),
    ("run_ops_redundant", 1),
    ("run_ops_by_opcode", 56),
    ("run_redundant_by_opcode", 56),
    ("verify_checked", 1),
    ("verify_agree", 1),
    ("verify_disagree", 1),
    ("verify_unavailable", 1),
    ("source_by_prim", len(PRIMS)),
    ("gl_arrays_by_prim", len(PRIMS)),
    ("gl_batch_by_prim", len(PRIMS)),
    ("gl_bypass_by_prim", len(PRIMS)),
    ("gl_bypass_total", 1),
)
PAYLOAD_WORDS = sum(n for _name, n in LAYOUT)
PAYLOAD = struct.Struct(f"<{PAYLOAD_WORDS}I")
LABELS = {
    "close_reason": BREAK_REASONS,
    "close_cs_opcode": CS_OPS,
    "close_dirty_cat": DIRTY_CATS,
    "close_len_hist": LEN_BUCKETS,
    "run_ops_by_opcode": CS_OPS,
    "run_redundant_by_opcode": CS_OPS,
    "source_by_prim": PRIMS,
    "gl_arrays_by_prim": PRIMS,
    "gl_batch_by_prim": PRIMS,
    "gl_bypass_by_prim": PRIMS,
}


def unpack_payload(raw):
    values = PAYLOAD.unpack(raw)
    out, pos = {}, 0
    for name, count in LAYOUT:
        if count == 1:
            out[name] = values[pos]
        else:
            out[name] = dict(zip(LABELS[name], values[pos:pos + count]))
        pos += count
    return out


def find_pid(comm):
    matches = []
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        try:
            with open(f"/proc/{name}/comm", encoding="ascii") as stream:
                if stream.read().strip() == comm:
                    matches.append(int(name))
        except OSError:
            pass
    if len(matches) != 1:
        raise RuntimeError(f"expected one {comm!r} process, found {matches}")
    return matches[0]


def module_base(pid, module):
    with open(f"/proc/{pid}/maps", encoding="ascii") as stream:
        for line in stream:
            fields = line.split()
            if len(fields) >= 6 and fields[2] == "00000000" and fields[-1].endswith(module):
                return int(fields[0].split("-", 1)[0], 16)
    raise RuntimeError(f"offset-zero mapping for {module!r} not found")


def read_exact(fd, address, size):
    data = os.pread(fd, size, address)
    if len(data) != size:
        raise RuntimeError(f"short read at {address:#x}: {len(data)} of {size}")
    return data


def snapshot(pid, module, symbol_vma, image_base):
    address = module_base(pid, module) + symbol_vma - image_base
    fd = os.open(f"/proc/{pid}/mem", os.O_RDONLY)
    try:
        for _ in range(20):
            first = dict(zip(HEADER_NAMES, HEADER.unpack(read_exact(fd, address, HEADER.size))))
            if first["magic"] != MAGIC or first["signature"] != ((~MAGIC) & 0xFFFFFFFF):
                raise RuntimeError(f"bad PR38 signature at {address:#x}: {first}")
            expected = (HEADER.size + PAYLOAD.size) // 4
            if first["version"] != VERSION or first["size_words"] != expected:
                raise RuntimeError(
                    f"unsupported PR38 layout at {address:#x}: {first} "
                    f"(reader expects size_words={expected})")
            if first["publish_sequence"] & 1:
                continue
            body = read_exact(fd, address + HEADER.size, PAYLOAD.size)
            second = dict(zip(HEADER_NAMES, HEADER.unpack(read_exact(fd, address, HEADER.size))))
            if second["publish_sequence"] == first["publish_sequence"]:
                return {
                    "pid": pid, "module": module, "address": hex(address),
                    "enabled": bool(first["enabled"]),
                    "publish_sequence": first["publish_sequence"],
                    "counters": unpack_payload(body),
                }
        raise RuntimeError("census never quiesced; the render thread is publishing")
    finally:
        os.close(fd)


def diff_counters(before, after):
    out = {}
    for name, count in LAYOUT:
        if count == 1:
            out[name] = after[name] - before[name]
        else:
            out[name] = {k: after[name][k] - before[name][k]
                         for k in after[name] if after[name][k] != before[name][k]}
    return out


def derive(delta, frames):
    """frames is the DISPLAYED frame count from the external frame log.

    WineD3D issues two CS Present commands per displayed frame on this route, so
    the census has no usable frame denominator of its own.  Rates are only
    emitted when the caller supplies the measured one.
    """
    closes = delta["close_total"]
    equal = delta["boundary_state_equal"]
    different = delta["boundary_state_different"]
    out = {
        "closures": closes,
        "boundary_state_equal": equal,
        "boundary_state_different": different,
        "boundary_mergeable": delta["boundary_mergeable"],
        "verify_checked": delta["verify_checked"],
        "verify_agree": delta["verify_agree"],
        "verify_disagree": delta["verify_disagree"],
        "verify_unavailable": delta["verify_unavailable"],
    }
    if delta["run_ops"]:
        out["run_ops_redundant_fraction"] = delta["run_ops_redundant"] / delta["run_ops"]
        out["run_ops_comparable_fraction"] = delta["run_ops_comparable"] / delta["run_ops"]
    if frames:
        out["displayed_frames"] = frames
        out["closures_per_frame"] = closes / frames
        out["boundary_state_equal_per_frame"] = equal / frames
        out["boundary_mergeable_per_frame"] = delta["boundary_mergeable"] / frames
        out["gl_bypass_per_frame"] = delta["gl_bypass_total"] / frames
    return out


def verdict(derived):
    """The decision rule fixed before the measurement was taken."""
    if derived.get("verify_disagree"):
        return ("VOID: the sampled full-state snapshot disagreed with the "
                "opcode model; the run cannot be used.")
    per_frame = derived.get("boundary_mergeable_per_frame")
    if per_frame is None:
        return "no displayed-frame count supplied; pass --frames to get a verdict"
    if per_frame < 50:
        return (f"NO-GO: {per_frame:.1f} safely mergeable GL submissions/frame "
                f"is below the 50/frame floor. Do not write a production patch.")
    if per_frame <= 100:
        return (f"SMALL: {per_frame:.1f}/frame. A bounded experiment with a "
                f"full A/B/A is allowed; nothing larger.")
    return (f"GO: {per_frame:.1f}/frame. An adjacent exact-state coalescer may "
            f"be designed; draw order must not change.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--comm", default="mgs2_sse_rg353v")
    parser.add_argument("--pid", type=int)
    parser.add_argument("--module", default="wined3d.dll")
    parser.add_argument("--symbol-vma", type=lambda v: int(v, 0), default=0x101d30c0)
    parser.add_argument("--image-base", type=lambda v: int(v, 0), default=IMAGE_BASE)
    parser.add_argument("--output")
    parser.add_argument("--diff", nargs=2, metavar=("BEFORE", "AFTER"))
    parser.add_argument("--frames", type=int,
                        help="displayed frames in the interval, from the external frame log")
    args = parser.parse_args()

    if args.diff:
        with open(args.diff[0], encoding="ascii") as stream:
            before = json.load(stream)
        with open(args.diff[1], encoding="ascii") as stream:
            after = json.load(stream)
        if before["pid"] != after["pid"]:
            raise SystemExit("before/after are different processes")
        delta = diff_counters(before["counters"], after["counters"])
        derived = derive(delta, args.frames)
        report = {"before": before, "after": after, "delta": delta,
                  "derived": derived, "verdict": verdict(derived)}
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    pid = args.pid or find_pid(args.comm)
    report = snapshot(pid, args.module, args.symbol_vma, args.image_base)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        with open(args.output, "w", encoding="ascii") as stream:
            stream.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()

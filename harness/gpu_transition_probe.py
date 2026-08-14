#!/usr/bin/env python3
"""Read/reset the bounded WineD3D transition probe through /proc/<pid>/mem.

The diagnostic WineD3D DLL exports the unstripped ``mgs2_gpu_probe`` symbol.
Pass its PE virtual address from ``nm``; the reader derives the live address
from the module's offset-zero mapping. No code runs in the game's hot thread.
"""

import argparse
import json
import os
import struct


MAGIC = 0x32555047
HEADER = struct.Struct("<IIII")
EVENT = struct.Struct("<iIIIIIIII")
OP_NAMES = {
    1: "delete_texture",
    2: "allocate_texture",
    3: "upload_texture",
    4: "generate_texture",
    5: "link_program",
    6: "compile_shader",
    7: "cs_dispatch",
    8: "link_separable_stage",
    9: "validate_program_pipeline",
}


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
        raise SystemExit(f"expected one {comm!r} process, found {matches}")
    return matches[0]


def module_base(pid, module):
    with open(f"/proc/{pid}/maps", encoding="ascii") as stream:
        for line in stream:
            fields = line.split()
            if len(fields) >= 6 and fields[2] == "00000000" and fields[-1].endswith(module):
                return int(fields[0].split("-", 1)[0], 16)
    raise SystemExit(f"offset-zero mapping for {module!r} not found")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int)
    parser.add_argument("--comm", default="mgs2_sse_rg353v")
    parser.add_argument("--module", default="wined3d.dll")
    parser.add_argument("--symbol-vma", type=lambda value: int(value, 0), required=True)
    parser.add_argument("--image-base", type=lambda value: int(value, 0), default=0x10000000)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--json")
    args = parser.parse_args()

    pid = args.pid or find_pid(args.comm)
    address = module_base(pid, args.module) + args.symbol_vma - args.image_base
    mode = "r+b" if args.reset else "rb"
    with open(f"/proc/{pid}/mem", mode, buffering=0) as memory:
        memory.seek(address)
        magic, version, capacity, next_sequence = HEADER.unpack(memory.read(HEADER.size))
        if magic != MAGIC or version != 1 or capacity > 4096:
            raise SystemExit(
                f"bad probe header at {address:#x}: "
                f"magic={magic:#x} version={version} capacity={capacity}"
            )
        if args.reset:
            memory.seek(address + 12)
            memory.write(struct.pack("<I", 0))
            print(json.dumps({"pid": pid, "address": hex(address), "reset": True}))
            return
        memory.seek(address + HEADER.size)
        raw_events = memory.read(capacity * EVENT.size)

    first = max(1, next_sequence - capacity + 1)
    records = []
    for slot in range(capacity):
        values = EVENT.unpack_from(raw_events, slot * EVENT.size)
        commit, op, tid, duration_us, a, b, c, d, obj = values
        if first <= commit <= next_sequence:
            records.append({
                "sequence": commit,
                "op": OP_NAMES.get(op, f"unknown_{op}"),
                "tid": tid,
                "duration_us": duration_us,
                "a": a,
                "b": b,
                "c": c,
                "d": d,
                "object": f"0x{obj:08x}",
            })
    records.sort(key=lambda item: item["sequence"])
    result = {
        "pid": pid,
        "address": hex(address),
        "next_sequence": next_sequence,
        "records": records,
    }
    rendered = json.dumps(result, indent=2)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as stream:
            stream.write(rendered + "\n")
    print(rendered)


if __name__ == "__main__":
    main()

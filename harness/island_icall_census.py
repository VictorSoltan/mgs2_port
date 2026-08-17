#!/usr/bin/env python3
"""Read the bounded MGS2 indirect-call target census (patch 50).

The question this answers: when the four functions that carry the frame dispatch
through a function pointer held in a WineD3D object, where does that pointer
actually point? A static analysis cannot say, and concluding "cannot be armed"
from not knowing was the mistake this instrument exists to correct.

The diagnostic WineD3D build only updates counters in memory. This reader runs
outside Wine and takes a coherent snapshot through /proc/<pid>/mem, the same way
the submission census does.

Classes, assigned once per distinct target inside the guest:

  1 box86-bridge   a CC 'S' 'C' thunk -- native code the island reaches by
                   unwrapping the bridge, no emulator involved
  2 wined3d-self   inside wined3d.dll, so the island has its own ARM copy
  3 other-module   somewhere else; needs identifying before it can be routed
  0 unknown        null or unreadable

Only class 3 can turn out to need a call back into the emulator. The number that
decides the branch is the share of calls per class, not the number of sites.
"""

import argparse
import json
import os
import struct
import sys

MAGIC = 0x30355250  # PR50
VERSION = 1
IMAGE_BASE = 0x10000000
SYMBOL_VMA = 0x101D40C0  # mgs2_island_icall_census in the patch-50 build
SITES = 32
TARGETS = 8

SITE_NAMES = [
    "buffer_ops->buffer_prepare_location",
    "buffer_ops->buffer_unload_location",
    "texture_ops->texture_load_location",
    "texture_ops->texture_unload_location",
    "texture_ops->texture_prepare_location",
    "texture_ops->texture_upload_data (blt)",
    "texture_ops->texture_download_data (blt)",
    "texture_ops->texture_upload_data (bo)",
    "resource_ops->resource_get_sub_resource_count",
    "resource_ops->resource_sub_resource_get_desc",
    "resource_ops->resource_unload",
    "parent_ops->wined3d_object_destroyed",
    "resource_ops->resource_incref",
    "resource_ops->resource_decref",
    "resource_ops->resource_sub_resource_get_map_pitch",
    "cs->c.ops->finish",
    "adapter_ops->adapter_acquire_context",
    "adapter_ops->adapter_release_context",
    "adapter_ops->adapter_map_bo_address",
    "adapter_ops->adapter_unmap_bo_address",
    "adapter_ops->adapter_copy_bo_address",
    "adapter_ops->adapter_flush_bo_address",
    "adapter_ops->adapter_destroy_bo",
] + [f"unused {i}" for i in range(23, SITES)]

CLASS_NAMES = {0: "unknown", 1: "box86-bridge", 2: "wined3d-self", 3: "other-module"}

HEADER = struct.Struct("<5I i 3I")  # magic version size_words signature enabled,
                                    # publish_sequence, presents, base, end
TARGET = struct.Struct("<3I")
SITE = struct.Struct("<3I" + "3I" * TARGETS)


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


def snapshot(pid, module, vma):
    """Two reads bracketed by the publish sequence, so a snapshot torn by a
    concurrent present is retried rather than reported."""
    address = module_base(pid, module) + vma - IMAGE_BASE
    size = HEADER.size + SITE.size * SITES
    fd = os.open(f"/proc/{pid}/mem", os.O_RDONLY)
    try:
        for _ in range(16):
            first = os.pread(fd, size, address)
            second = os.pread(fd, size, address)
            if first == second:
                return first
        raise RuntimeError("census kept changing under the reader")
    finally:
        os.close(fd)


def parse(blob):
    head = HEADER.unpack_from(blob, 0)
    magic, version, size_words, signature, enabled, sequence, presents, base, end = head
    if magic != MAGIC or signature != (~MAGIC & 0xFFFFFFFF):
        raise RuntimeError(f"census signature mismatch: magic={magic:#x} sig={signature:#x}"
                           " -- wrong DLL, or the symbol VMA moved (pass --vma)")
    if version != VERSION:
        raise RuntimeError(f"census version {version}, reader expects {VERSION}")
    sites = []
    off = HEADER.size
    for i in range(SITES):
        vals = SITE.unpack_from(blob, off)
        off += SITE.size
        calls, distinct, overflow = vals[0:3]
        targets = []
        for t in range(distinct):
            addr, cls, tcalls = vals[3 + t * 3: 6 + t * 3]
            targets.append({"addr": addr, "cls": cls, "calls": tcalls})
        sites.append({"id": i, "name": SITE_NAMES[i], "calls": calls,
                      "distinct": distinct, "overflow": overflow, "targets": targets})
    return {"enabled": enabled, "presents": presents, "sequence": sequence,
            "module_base": base, "module_end": end, "sites": sites}


def report(census):
    if not census["enabled"]:
        print("census never armed -- is MGS2_SUBMIT_CENSUS on for this run?")
        return 1
    presents = census["presents"] or 1
    print(f"presents {census['presents']}   wined3d.dll "
          f"{census['module_base']:#x}-{census['module_end']:#x}\n")

    per_class = {}
    total = 0
    for site in census["sites"]:
        if not site["calls"]:
            continue
        print(f"  [{site['id']:2d}] {site['name']}")
        print(f"       {site['calls']} calls, {site['calls']/presents:.1f}/frame,"
              f" {site['distinct']} distinct target(s)"
              + (f", OVERFLOW {site['overflow']}" if site["overflow"] else ""))
        for t in sorted(site["targets"], key=lambda x: -x["calls"]):
            share = 100.0 * t["calls"] / site["calls"]
            print(f"         {t['addr']:#010x}  {CLASS_NAMES.get(t['cls'], '?'):<13}"
                  f" {t['calls']:>9} ({share:5.1f}%)")
            per_class[t["cls"]] = per_class.get(t["cls"], 0) + t["calls"]
            total += t["calls"]
        print()

    if not total:
        print("no indirect calls recorded -- the instrumented paths did not run")
        return 1
    print("share of indirect calls by class:")
    for cls in sorted(per_class, key=lambda c: -per_class[c]):
        print(f"  {CLASS_NAMES.get(cls, '?'):<13} {100.0*per_class[cls]/total:5.1f}%"
              f"   {per_class[cls]}   {per_class[cls]/presents:8.1f}/frame")
    reachable = per_class.get(1, 0) + per_class.get(2, 0)
    print(f"\nnative-resolvable without entering the emulator: "
          f"{100.0*reachable/total:.1f}% of indirect calls")
    print("class 'other-module' is the only share that may require a guest callback;"
          "\nidentify those addresses before treating them as one.")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--comm", default="mgs2_sse_rg353v")
    parser.add_argument("--pid", type=int)
    parser.add_argument("--module", default="wined3d.dll")
    parser.add_argument("--vma", type=lambda s: int(s, 0), default=SYMBOL_VMA)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    pid = args.pid or find_pid(args.comm)
    census = parse(snapshot(pid, args.module, args.vma))
    if args.json:
        json.dump(census, sys.stdout, indent=2)
        print()
        return 0
    return report(census)


if __name__ == "__main__":
    sys.exit(main())

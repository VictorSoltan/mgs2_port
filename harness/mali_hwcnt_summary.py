#!/usr/bin/env python3
"""Summarize one-shot Mali-G52 raw hardware-counter output.

The counter indices below are the Bifrost primary-set layout exposed by the
RG353VS r54p2 kbase driver.  Refuse malformed or driver-error captures rather
than turning them into plausible-looking percentages.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import sys


def key_values(fields: list[str]) -> dict[str, int]:
    result: dict[str, int] = {}
    for field in fields:
        key, separator, value = field.partition("=")
        if separator:
            result[key] = int(value, 0)
    return result


def parse_capture(path: Path) -> tuple[dict[str, int], dict[str, list[dict[int, int]]]]:
    meta: dict[str, int] | None = None
    blocks: dict[str, list[dict[int, int]]] = defaultdict(list)
    for number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        fields = raw_line.split()
        if not fields:
            continue
        if fields[0] == "meta":
            if meta is not None:
                raise ValueError(f"line {number}: duplicate metadata")
            meta = key_values(fields[1:])
        elif fields[0] == "block" and len(fields) >= 2:
            values = key_values(fields[2:])
            if not values.pop("on", 0) or not values.pop("available", 0):
                continue
            values.pop("index", None)
            blocks[fields[1]].append({int(key): value for key, value in values.items()})
        else:
            raise ValueError(f"line {number}: unknown record")
    if meta is None:
        raise ValueError("metadata is missing")
    return meta, blocks


def sum_counter(blocks: dict[str, list[dict[int, int]]], name: str, index: int) -> int:
    return sum(block.get(index, 0) for block in blocks.get(name, []))


def ratio(value: int, denominator: int) -> str:
    return "n/a" if not denominator else f"{100.0 * value / denominator:.2f}%"


def rate(value: int, seconds: float) -> str:
    return "n/a" if not seconds else f"{value / seconds:,.0f}/s"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=Path)
    args = parser.parse_args()

    try:
        meta, blocks = parse_capture(args.capture)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if meta.get("error") or meta.get("stretched"):
        print("error: incomplete/stretched hardware-counter capture", file=sys.stderr)
        return 3
    begin_ns = meta.get("begin_ns", 0)
    end_ns = meta.get("end_ns", 0)
    seconds = (end_ns - begin_ns) / 1_000_000_000
    gpu_cycles = meta.get("gpu_cycle", 0)
    if seconds <= 0 or gpu_cycles <= 0:
        print("error: invalid duration or GPU cycle count", file=sys.stderr)
        return 4

    # Arm Bifrost primary performance-counter indices on this device.
    gpu_active = sum_counter(blocks, "jm", 6)
    irq_active = sum_counter(blocks, "jm", 7)
    fragment_queue = sum_counter(blocks, "jm", 10)
    nonfragment_queue = sum_counter(blocks, "jm", 18)
    tiler_active = sum_counter(blocks, "tiler", 4)
    triangles = sum_counter(blocks, "tiler", 6)
    visible = sum_counter(blocks, "tiler", 11)
    culled = sum_counter(blocks, "tiler", 12)
    clipped = sum_counter(blocks, "tiler", 13)
    frag_active = sum_counter(blocks, "shader", 4)
    compute_active = sum_counter(blocks, "shader", 22)
    exec_active = sum_counter(blocks, "shader", 26)
    frag_quads = sum_counter(blocks, "shader", 11)
    early_z_kills = sum_counter(blocks, "shader", 14)
    late_z_kills = sum_counter(blocks, "shader", 16)
    ext_read_beats = sum_counter(blocks, "memory", 32)
    ext_write_beats = sum_counter(blocks, "memory", 47)

    print(f"window_seconds             {seconds:.6f}")
    print(f"gpu_clock_average_mhz      {gpu_cycles / seconds / 1_000_000:.1f}")
    print(f"gpu_active                 {ratio(gpu_active, gpu_cycles)}")
    print(f"fragment_queue_active      {ratio(fragment_queue, gpu_cycles)}")
    print(f"nonfragment_queue_active   {ratio(nonfragment_queue, gpu_cycles)}")
    print(f"irq_pending                {ratio(irq_active, gpu_cycles)}")
    print(f"tiler_active               {ratio(tiler_active, gpu_cycles)}")
    print(f"shader_fragment_active     {ratio(frag_active, gpu_cycles)}")
    print(f"shader_compute_active      {ratio(compute_active, gpu_cycles)}")
    print(f"shader_exec_core_active    {ratio(exec_active, gpu_cycles)}")
    print(f"triangles                  {rate(triangles, seconds)}")
    print(f"triangles_visible          {rate(visible, seconds)}")
    print(f"triangles_culled           {rate(culled, seconds)}")
    print(f"triangles_clipped          {rate(clipped, seconds)}")
    print(f"fragment_quads             {rate(frag_quads, seconds)}")
    print(f"early_z_killed_quads       {rate(early_z_kills, seconds)}")
    print(f"late_z_killed_threads      {rate(late_z_kills, seconds)}")
    print(f"external_read_mib_s        {ext_read_beats * 16 / seconds / 1048576:.2f}")
    print(f"external_write_mib_s       {ext_write_beats * 16 / seconds / 1048576:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

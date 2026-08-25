#!/usr/bin/env python3
"""Read and summarize the bounded DXVK pipeline timeline from process memory.

The paired research D3D9 DLL writes fixed-size records only to a bounded RAM
array. This external reader runs after the controlled route, while the process
and its mapped DLL still exist.
"""

import argparse
import os
import struct
import time

import dxvk_present_count as pe


CAPACITY = 4096
EVENT = struct.Struct("<QIIIIIIII")
EXPORT_WRITE = b"MGS2DxvkPipelineTraceWriteCount"
EXPORT_DROPPED = b"MGS2DxvkPipelineTraceDropped"
EXPORT_EVENTS = b"MGS2DxvkPipelineTraceEvents"
KIND_NAMES = {
    1: "queue",
    2: "worker_begin",
    3: "cache_entry",
    4: "driver_begin",
    5: "driver_end",
    6: "draw_miss",
    7: "draw_ready",
    8: "worker_end",
}


def read_u32(fd, address):
    raw = os.pread(fd, 4, address)
    if len(raw) != 4:
        raise RuntimeError(f"short u32 read at {address:#x}")
    return struct.unpack("<I", raw)[0]


def boot_to_monotonic_offset_ms():
    if hasattr(time, "CLOCK_BOOTTIME"):
        boot_ms = time.clock_gettime_ns(time.CLOCK_BOOTTIME) / 1_000_000
    else:
        with open("/proc/uptime", encoding="ascii") as stream:
            boot_ms = float(stream.read().split()[0]) * 1000
    return time.monotonic_ns() / 1_000_000 - boot_ms


def event_key(event):
    return event["pipeline"], event["state"], event["aux"]


def pair_events(events, begin_kind, end_kind, key_function):
    pending = {}
    pairs = []
    for event in events:
        key = key_function(event)
        if event["kind"] == begin_kind:
            pending.setdefault(key, []).append(event)
        elif event["kind"] == end_kind and pending.get(key):
            begin = pending[key].pop(0)
            pairs.append((begin, event))
    return pairs


def duration_ms(pair):
    return pair[1]["tick"] - pair[0]["tick"]


def summarize(events):
    by_sequence = {}
    cache_entries = []
    for event in events:
        if event["sequence"]:
            by_sequence.setdefault(event["sequence"], {})[event["kind"]] = event
        if event["kind"] == 3:
            cache_entries.append(event)

    workers = []
    for sequence, kinds in by_sequence.items():
        queue = kinds.get(1)
        begin = kinds.get(2)
        end = kinds.get(8)
        if queue and begin:
            workers.append({
                "sequence": sequence,
                "tid": begin["tid"],
                "queue_ms": begin["tick"] - queue["tick"],
                "work_ms": end["tick"] - begin["tick"] if end else None,
            })

    drivers = pair_events(events, 4, 5, event_key)
    draws = pair_events(events, 6, 7, event_key)

    driver_rows = []
    for begin, end in drivers:
        matching_cache = [entry for entry in cache_entries
                          if event_key(entry) == event_key(begin)
                          and entry["tick"] <= begin["tick"]]
        sequence = matching_cache[-1]["sequence"] if matching_cache else 0
        driver_rows.append((duration_ms((begin, end)), begin, end, sequence))

    draw_rows = []
    for begin, end in draws:
        overlapping = [row for row in driver_rows
                       if event_key(row[1]) == event_key(begin)
                       and row[1]["tick"] <= end["tick"]
                       and row[2]["tick"] >= begin["tick"]]
        driver_ms = max((row[0] for row in overlapping), default=None)
        draw_rows.append((duration_ms((begin, end)), begin, end, driver_ms))

    complete_workers = [row for row in workers if row["work_ms"] is not None]
    print("SUMMARY "
          f"events={len(events)} workers={len(workers)} "
          f"queue_delay_max_ms={max((row['queue_ms'] for row in workers), default=0)} "
          f"worker_max_ms={max((row['work_ms'] for row in complete_workers), default=0)} "
          f"driver_calls={len(driver_rows)} "
          f"driver_max_ms={max((row[0] for row in driver_rows), default=0)} "
          f"draw_misses={len(draw_rows)} "
          f"draw_wait_max_ms={max((row[0] for row in draw_rows), default=0)}")

    for row in sorted(workers, key=lambda item: item["work_ms"] or 0,
                      reverse=True)[:20]:
        print(f"WORKER sequence={row['sequence']} tid={row['tid']} "
              f"queue_ms={row['queue_ms']} work_ms={row['work_ms']}")
    for elapsed, begin, unused_end, sequence in sorted(
            driver_rows, key=lambda item: item[0], reverse=True)[:30]:
        print(f"DRIVER tick_ms={begin['mono_tick']:.3f} tid={begin['tid']} "
              f"duration_ms={elapsed} sequence={sequence} "
              f"pipeline={begin['pipeline']:#x} state={begin['state']:#x} "
              f"renderpass={begin['aux']:#x}")
    for elapsed, begin, unused_end, driver_ms in sorted(
            draw_rows, key=lambda item: item[0], reverse=True)[:30]:
        print(f"DRAW tick_ms={begin['mono_tick']:.3f} tid={begin['tid']} "
              f"wait_ms={elapsed} overlapping_driver_ms={driver_ms} "
              f"pipeline={begin['pipeline']:#x} state={begin['state']:#x} "
              f"renderpass={begin['aux']:#x}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    args = parser.parse_args()

    base, module = pe.module_base(args.pid)
    write_rva = pe.exported_rva(module, EXPORT_WRITE)
    dropped_rva = pe.exported_rva(module, EXPORT_DROPPED)
    events_rva = pe.exported_rva(module, EXPORT_EVENTS)
    memory = os.open(f"/proc/{args.pid}/mem", os.O_RDONLY)
    try:
        attempted = read_u32(memory, base + write_rva)
        dropped = read_u32(memory, base + dropped_rva)
        count = min(attempted, CAPACITY)
        raw = os.pread(memory, count * EVENT.size, base + events_rva)
    finally:
        os.close(memory)
    if len(raw) != count * EVENT.size:
        raise RuntimeError(f"short event-array read: {len(raw)}/{count * EVENT.size}")

    offset_ms = boot_to_monotonic_offset_ms()
    events = []
    for index in range(count):
        values = EVENT.unpack_from(raw, index * EVENT.size)
        tick, tid, kind, sequence, pipeline, state, shader, aux, unused = values
        if kind not in KIND_NAMES:
            continue
        events.append({
            "index": index,
            "tick": tick,
            "mono_tick": tick + offset_ms,
            "tid": tid,
            "kind": kind,
            "sequence": sequence,
            "pipeline": pipeline,
            "state": state,
            "shader": shader,
            "aux": aux,
        })
    events.sort(key=lambda item: (item["tick"], item["index"]))

    print(f"pid={args.pid} module={module} base={base:#x} "
          f"write_rva={write_rva:#x} dropped_rva={dropped_rva:#x} "
          f"events_rva={events_rva:#x} attempted={attempted} "
          f"capacity={CAPACITY} dropped={dropped} complete={len(events)} "
          f"boot_to_monotonic_offset_ms={offset_ms:.3f}")
    summarize(events)
    print("EVENTS")
    print("index\ttick_ms\tmonotonic_tick_ms\ttid\tkind\tsequence\tpipeline\tstate\tshader\taux")
    for event in events:
        print(f"{event['index']}\t{event['tick']}\t{event['mono_tick']:.3f}\t"
              f"{event['tid']}\t{KIND_NAMES[event['kind']]}\t{event['sequence']}\t"
              f"{event['pipeline']:#x}\t{event['state']:#x}\t"
              f"{event['shader']:#x}\t{event['aux']:#x}")


if __name__ == "__main__":
    main()

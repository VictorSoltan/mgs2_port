#!/usr/bin/env python3
"""Read the bounded MGS2 dmsynth state recorder through /proc/PID/mem.

The recorder performs no file I/O and no formatted logging in Wine threads.
This reader is run once after a symptom and, optionally, once after a map
transition restores sound.  It needs no third-party Python modules.
"""

import argparse
import json
import os
import struct
import sys


MAGIC = 0x31545344  # DST1
VERSION = 1
STATE_RVA = 0x3BEA8
HEADER_WORDS = 20
EVENTS = 256
RECORD_WORDS = 16
RECORD_SIZE = RECORD_WORDS * 4
HEADER_FORMAT = "<20I"
RECORD_FORMAT = "<10Ii2I3i"

HEADER_NAMES = (
    "magic version size record_words event_count signature enabled "
    "write_sequence open_reset_count midi_reset_count noteon_count "
    "noteon_failed noteon_no_voice program_count bank_count active_voices "
    "max_active_voices last_render_synth last_tick reserved"
).split()

RECORD_NAMES = (
    "sequence tick type synth reset_serial group channel status data1 data2 "
    "result voices_before voices_after sfont bank program"
).split()

EVENT_NAMES = {
    1: "open_reset",
    2: "midi_reset",
    3: "note_on",
    4: "program",
    5: "bank",
    6: "note_unmute",
}

COUNTER_NAMES = (
    "write_sequence",
    "open_reset_count",
    "midi_reset_count",
    "noteon_count",
    "noteon_failed",
    "noteon_no_voice",
    "program_count",
    "bank_count",
)


def module_base(pid):
    with open(f"/proc/{pid}/maps", encoding="ascii") as stream:
        for line in stream:
            fields = line.split()
            if (
                len(fields) >= 6
                and fields[1].startswith("r-x")
                and fields[2] == "00000000"
                and "dmsynth.dll" in fields[-1]
            ):
                return int(fields[0].split("-", 1)[0], 16)
    raise RuntimeError("dmsynth.dll mapping not found")


def read_exact(fd, size, address):
    data = os.pread(fd, size, address)
    if len(data) != size:
        raise RuntimeError(
            f"short read at {address:#x}: expected {size}, got {len(data)}"
        )
    return data


def decode_header(raw, address):
    state = dict(zip(HEADER_NAMES, struct.unpack(HEADER_FORMAT, raw)))
    if state["magic"] != MAGIC:
        raise RuntimeError(f"bad magic {state['magic']:#x} at {address:#x}")
    if state["version"] != VERSION:
        raise RuntimeError(f"unsupported state version {state['version']}")
    if state["record_words"] != RECORD_WORDS or state["event_count"] != EVENTS:
        raise RuntimeError(
            "state layout mismatch: "
            f"record_words={state['record_words']} event_count={state['event_count']}"
        )
    if state["signature"] != ((~MAGIC) & 0xFFFFFFFF):
        raise RuntimeError(f"bad state signature {state['signature']:#x}")
    return state


def decode_records(raw, write_sequence):
    first_sequence = max(1, write_sequence - EVENTS + 1)
    records = []

    for slot in range(EVENTS):
        values = struct.unpack_from(RECORD_FORMAT, raw, slot * RECORD_SIZE)
        record = dict(zip(RECORD_NAMES, values))
        sequence = record["sequence"]
        if sequence < first_sequence or sequence > write_sequence:
            continue
        if (sequence - 1) % EVENTS != slot:
            continue
        record["event"] = EVENT_NAMES.get(record["type"], "unknown")
        record["synth"] = hex(record["synth"])
        record["status"] = hex(record["status"])
        records.append(record)

    records.sort(key=lambda item: item["sequence"])
    return records


def read_state(pid, rva, last):
    base = module_base(pid)
    address = base + rva
    fd = os.open(f"/proc/{pid}/mem", os.O_RDONLY)
    try:
        before = decode_header(
            read_exact(fd, HEADER_WORDS * 4, address), address
        )
        records_raw = read_exact(
            fd, EVENTS * RECORD_SIZE, address + HEADER_WORDS * 4
        )
        after = decode_header(
            read_exact(fd, HEADER_WORDS * 4, address), address
        )
        if before["write_sequence"] != after["write_sequence"]:
            records_raw = read_exact(
                fd, EVENTS * RECORD_SIZE, address + HEADER_WORDS * 4
            )
            after = decode_header(
                read_exact(fd, HEADER_WORDS * 4, address), address
            )
    finally:
        os.close(fd)

    records = decode_records(records_raw, after["write_sequence"])
    if last:
        records = records[-last:]

    state = {
        "pid": pid,
        "address": hex(address),
        "magic": "DST1",
        "version": after["version"],
        "enabled": bool(after["enabled"]),
        "counters": {name: after[name] for name in COUNTER_NAMES},
        "voices": {
            "last_render_active": after["active_voices"],
            "maximum_observed": after["max_active_voices"],
            "last_render_synth": hex(after["last_render_synth"]),
        },
        "last_tick": after["last_tick"],
        "records": records,
    }
    return state


def diff_states(before, after):
    counters_before = before["counters"]
    counters_after = after["counters"]
    sequence = counters_before["write_sequence"]
    return {
        "before_sequence": sequence,
        "after_sequence": counters_after["write_sequence"],
        "counter_delta": {
            name: counters_after[name] - counters_before[name]
            for name in COUNTER_NAMES
        },
        "voices_before": before["voices"],
        "voices_after": after["voices"],
        "new_records": [
            record for record in after.get("records", [])
            if record["sequence"] > sequence
        ],
    }


def load_json(path):
    with open(path, encoding="utf-8") as stream:
        return json.load(stream)


def emit(data, output):
    rendered = json.dumps(data, indent=2, sort_keys=False)
    if output:
        temporary = output + ".tmp"
        with open(temporary, "w", encoding="utf-8") as stream:
            stream.write(rendered)
            stream.write("\n")
        os.replace(temporary, output)
    else:
        print(rendered)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int, nargs="?")
    parser.add_argument("--rva", type=lambda value: int(value, 0), default=STATE_RVA)
    parser.add_argument(
        "--last", type=int, default=0,
        help="keep only the last N committed records (default: all 256)",
    )
    parser.add_argument("--output", help="atomically write JSON to this file")
    parser.add_argument(
        "--diff", nargs=2, metavar=("BEFORE", "AFTER"),
        help="compare two previously saved JSON snapshots",
    )
    args = parser.parse_args()

    try:
        if args.diff:
            emit(diff_states(load_json(args.diff[0]), load_json(args.diff[1])), args.output)
            return
        if args.pid is None:
            parser.error("PID is required unless --diff is used")
        if args.last < 0 or args.last > EVENTS:
            parser.error(f"--last must be between 0 and {EVENTS}")
        emit(read_state(args.pid, args.rva, args.last), args.output)
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        print(f"dmsynth_state: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()

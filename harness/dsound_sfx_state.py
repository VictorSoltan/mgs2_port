#!/usr/bin/env python3
"""Read the bounded MGS2 DirectSound gameplay-SFX control ring once."""

import argparse
import json
import os
import struct
import sys


MAGIC = 0x31534653  # SFS1
VERSION = 1
STATE_RVA = 0x21040
HEADER_WORDS = 12
RECORD_WORDS = 18
EVENTS = 4096

HEADER_NAMES = (
    "magic version header_words record_words event_count signature enabled "
    "write_sequence lock_count control_count last_tick flags"
).split()
RECORD_NAMES = (
    "sequence tick event object memory state playflags sec_mixpos writelead "
    "committed_mixpos committed_flags volume pan frequency arg0 arg1 arg2 result"
).split()
EVENT_NAMES = {
    1: "lock",
    2: "unlock",
    3: "position",
    4: "volume",
    5: "pan",
    6: "frequency",
    7: "play",
    8: "stop",
}


def module_base(pid):
    with open(f"/proc/{pid}/maps", encoding="ascii") as stream:
        for line in stream:
            fields = line.split()
            if len(fields) >= 6 and fields[1].startswith("r-x") and fields[2] == "00000000" and "dsound.dll" in fields[-1]:
                return int(fields[0].split("-", 1)[0], 16)
    raise RuntimeError("dsound.dll mapping not found")


def read_exact(fd, address, size):
    data = os.pread(fd, size, address)
    if len(data) != size:
        raise RuntimeError(f"short read at {address:#x}: {len(data)} of {size}")
    return data


def read_state(pid, rva, last):
    address = module_base(pid) + rva
    fd = os.open(f"/proc/{pid}/mem", os.O_RDONLY)
    try:
        header = dict(zip(HEADER_NAMES, struct.unpack("<12I", read_exact(fd, address, HEADER_WORDS * 4))))
        if header["magic"] != MAGIC or header["signature"] != ((~MAGIC) & 0xFFFFFFFF):
            raise RuntimeError(f"bad SFS1 signature at {address:#x}")
        if header["version"] != VERSION or header["record_words"] != RECORD_WORDS or header["event_count"] != EVENTS:
            raise RuntimeError(f"unsupported SFS1 layout: {header}")
        raw = read_exact(fd, address + HEADER_WORDS * 4, EVENTS * RECORD_WORDS * 4)
        final_header = dict(zip(HEADER_NAMES, struct.unpack("<12I", read_exact(fd, address, HEADER_WORDS * 4))))
        if final_header["write_sequence"] != header["write_sequence"]:
            raw = read_exact(fd, address + HEADER_WORDS * 4, EVENTS * RECORD_WORDS * 4)
            header = final_header
    finally:
        os.close(fd)

    first = max(1, header["write_sequence"] - EVENTS + 1)
    records = []
    for slot in range(EVENTS):
        record = dict(zip(RECORD_NAMES, struct.unpack_from("<18I", raw, slot * RECORD_WORDS * 4)))
        sequence = record["sequence"]
        if sequence < first or sequence > header["write_sequence"] or (sequence - 1) % EVENTS != slot:
            continue
        record["event_name"] = EVENT_NAMES.get(record["event"], "unknown")
        records.append(record)
    records.sort(key=lambda record: record["sequence"])
    if last:
        records = records[-last:]
    return {
        "pid": pid,
        "address": hex(address),
        "magic": "SFS1",
        "version": header["version"],
        "enabled": bool(header["enabled"]),
        "counters": {name: header[name] for name in HEADER_NAMES[7:]},
        "records": records,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    parser.add_argument("--rva", type=lambda value: int(value, 0), default=STATE_RVA)
    parser.add_argument("--last", type=int, default=0)
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        rendered = json.dumps(read_state(args.pid, args.rva, args.last), indent=2)
        if args.output:
            temporary = args.output + ".tmp"
            with open(temporary, "w", encoding="utf-8") as stream:
                stream.write(rendered + "\n")
            os.replace(temporary, args.output)
        else:
            print(rendered)
    except (OSError, RuntimeError, struct.error) as error:
        print(f"dsound_sfx_state: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()

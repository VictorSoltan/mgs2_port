#!/usr/bin/env python3
"""Read the bounded DirectMusic transition recorder through /proc/PID/mem.

The companion dmime_state1 DLL records PChannel routing and curve delivery in
memory only. This reader is deliberately one-shot: it must not become another
audio-thread logger while a symptom is being judged.
"""

import argparse
import json
import os
import struct
import sys


MAGIC = 0x31544D44  # DMT1
VERSION = 1
# The DLL is relinked as patches are carried forward, so a recorded RVA is not
# an identity.  None selects the bounded mapping scan below; --rva remains an
# explicit research override for a separately identified image.
STATE_RVA = None
HEADER_WORDS = 12
RECORD_WORDS = 12
EVENTS = 256
SCAN_CHUNK = 64 * 1024
MAX_SCAN_BYTES = 8 * 1024 * 1024

HEADER_NAMES = (
    "magic version header_words record_words event_count signature enabled "
    "write_sequence stamp_count pmsg_count midi_count path_count"
).split()
RECORD_NAMES = (
    "sequence tick event pmsg_type pchannel_before pchannel_after track_id "
    "flags value1 value2 value3 value4"
).split()
EVENTS_NAMES = {
    1: "stamp_in",
    2: "stamp_out",
    3: "stamp_fail",
    4: "pmsg",
    5: "midi_port",
    6: "midi_drop",
    7: "curve_start",
    8: "curve_end",
    9: "curve_reset",
    10: "path_activate",
    11: "path_volume",
    12: "path_convert",
    13: "play_segment",
}


def module_layout(pid):
    ranges = []
    bases = []
    with open(f"/proc/{pid}/maps", encoding="ascii") as stream:
        for line in stream:
            fields = line.split()
            if len(fields) < 6 or os.path.basename(fields[5]).lower() != "dmime.dll":
                continue
            start, end = (int(value, 16) for value in fields[0].split("-", 1))
            bases.append(start - int(fields[2], 16))
            if fields[1].startswith("r"):
                ranges.append((start, end))
    if not ranges:
        raise RuntimeError("readable dmime.dll mapping not found")
    return min(bases), ranges


def locate_state(fd, ranges):
    total = sum(end - start for start, end in ranges)
    if total > MAX_SCAN_BYTES:
        raise RuntimeError(
            f"refusing oversized dmime.dll scan: {total} bytes")

    signature = struct.pack(
        "<6I", MAGIC, VERSION, HEADER_WORDS, RECORD_WORDS, EVENTS,
        (~MAGIC) & 0xFFFFFFFF)
    matches = set()
    overlap = len(signature) - 1
    for start, end in ranges:
        carry = b""
        position = start
        while position < end:
            size = min(SCAN_CHUNK, end - position)
            data = read_exact(fd, size, position)
            window = carry + data
            window_address = position - len(carry)
            offset = window.find(signature)
            while offset >= 0:
                address = window_address + offset
                if address % 4 == 0:
                    matches.add(address)
                offset = window.find(signature, offset + 1)
            carry = window[-overlap:]
            position += size

    if not matches:
        raise RuntimeError("DMT1 state header not found in dmime.dll mappings")
    if len(matches) != 1:
        rendered = ", ".join(hex(address) for address in sorted(matches))
        raise RuntimeError(f"ambiguous DMT1 state headers: {rendered}")
    return matches.pop()


def read_exact(fd, size, address):
    raw = os.pread(fd, size, address)
    if len(raw) != size:
        raise RuntimeError(f"short read at {address:#x}: expected {size}, got {len(raw)}")
    return raw


def read_state(pid, rva, last):
    base, ranges = module_layout(pid)
    fd = os.open(f"/proc/{pid}/mem", os.O_RDONLY)
    try:
        address = base + rva if rva is not None else locate_state(fd, ranges)
        header = dict(zip(HEADER_NAMES, struct.unpack("<12I", read_exact(fd, HEADER_WORDS * 4, address))))
        if header["magic"] != MAGIC or header["signature"] != ((~MAGIC) & 0xFFFFFFFF):
            raise RuntimeError(f"bad dmime state signature at {address:#x}")
        if header["version"] != VERSION or header["record_words"] != RECORD_WORDS or header["event_count"] != EVENTS:
            raise RuntimeError(f"unsupported dmime state layout: {header}")
        records_raw = read_exact(fd, EVENTS * RECORD_WORDS * 4, address + HEADER_WORDS * 4)
        header_after = dict(zip(HEADER_NAMES, struct.unpack("<12I", read_exact(fd, HEADER_WORDS * 4, address))))
        if header_after["write_sequence"] != header["write_sequence"]:
            records_raw = read_exact(fd, EVENTS * RECORD_WORDS * 4, address + HEADER_WORDS * 4)
            header = header_after
    finally:
        os.close(fd)

    first = max(1, header["write_sequence"] - EVENTS + 1)
    records = []
    for slot in range(EVENTS):
        values = struct.unpack_from("<12I", records_raw, slot * RECORD_WORDS * 4)
        record = dict(zip(RECORD_NAMES, values))
        sequence = record["sequence"]
        if sequence < first or sequence > header["write_sequence"] or (sequence - 1) % EVENTS != slot:
            continue
        record["event_name"] = EVENTS_NAMES.get(record["event"], "unknown")
        records.append(record)
    records.sort(key=lambda item: item["sequence"])
    if last:
        records = records[-last:]
    return {
        "pid": pid,
        "address": hex(address),
        "rva": hex(address - base),
        "locator": "rva-override" if rva is not None else "bounded-header-scan",
        "magic": "DMT1",
        "version": header["version"],
        "enabled": bool(header["enabled"]),
        "counters": {name: header[name] for name in HEADER_NAMES[7:]},
        "records": records,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    parser.add_argument(
        "--rva", type=lambda value: int(value, 0), default=STATE_RVA,
        help="explicit research override; default scans only dmime.dll mappings")
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
        print(f"dmime_state: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()

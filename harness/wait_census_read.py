#!/usr/bin/env python3
"""Read the bounded Wine Win32 wait census outside the game process.

The research kernelbase records only calls whose immediate return address is
inside the main PE image.  It never timestamps or logs on a game thread.  This
reader locates the self-identifying WCT1 record in the mapped kernelbase data
section and samples its fixed-size counters through read-only /proc/PID/mem.
"""

import argparse
import os
import struct
import time


MAGIC = 0x31544357  # WCT1
VERSION = 1
CAPACITY = 128
HEADER_WORDS = 10
ENTRY_WORDS = 18
TOTAL_WORDS = HEADER_WORDS + CAPACITY * ENTRY_WORDS
RECORD_BYTES = TOTAL_WORDS * 4
HEADER = struct.Struct("<10I")
ENTRY = struct.Struct("<18I")

KINDS = {
    2: "Sleep",
    3: "SleepEx",
    4: "WaitSingle",
    5: "WaitSingleEx",
    6: "WaitMultiple",
    7: "WaitMultipleEx",
}


def kernelbase_ranges(pid):
    ranges = []
    with open(f"/proc/{pid}/maps", encoding="ascii") as stream:
        for line in stream:
            fields = line.split()
            if len(fields) < 6 or not fields[-1].lower().endswith("/kernelbase.dll"):
                continue
            if "r" not in fields[1]:
                continue
            start, end = (int(value, 16) for value in fields[0].split("-", 1))
            ranges.append((start, end, fields[1], fields[-1]))
    if not ranges:
        raise RuntimeError("no readable kernelbase.dll mapping found")
    return ranges


def locate_record(fd, ranges):
    needle = struct.pack("<I", MAGIC)
    for start, end, permissions, path in ranges:
        # The public structure is initialized data.  Prefer writable mappings,
        # but accept a differently-labelled PE mapping for portability.
        if end - start < HEADER.size:
            continue
        data = os.pread(fd, end - start, start)
        offset = data.find(needle)
        while offset >= 0:
            if offset + HEADER.size <= len(data):
                header = HEADER.unpack_from(data, offset)
                if (header[0] == MAGIC and header[1] == VERSION
                        and header[2] == TOTAL_WORDS
                        and header[3] == ((~MAGIC) & 0xFFFFFFFF)
                        and header[5] == CAPACITY):
                    address = start + offset
                    raw = os.pread(fd, RECORD_BYTES, address)
                    if len(raw) == RECORD_BYTES:
                        return address, permissions, path
            offset = data.find(needle, offset + 1)
    raise RuntimeError("WCT1 record not found; candidate DLL or MGS2_WAIT_CENSUS=1 is missing")


def read_record(fd, address):
    raw = os.pread(fd, RECORD_BYTES, address)
    if len(raw) != RECORD_BYTES:
        raise RuntimeError(f"short census read at {address:#x}: {len(raw)} bytes")
    header = HEADER.unpack_from(raw)
    if (header[0] != MAGIC or header[1] != VERSION or header[2] != TOTAL_WORDS
            or header[3] != ((~MAGIC) & 0xFFFFFFFF) or header[5] != CAPACITY):
        raise RuntimeError("WCT1 header changed while sampling")
    entries = []
    offset = HEADER.size
    for unused in range(CAPACITY):
        entry = ENTRY.unpack_from(raw, offset)
        offset += ENTRY.size
        if entry[0] == 2:
            entries.append(entry)
    return header, entries


def delta(current, previous):
    return (current - previous) & 0xFFFFFFFF


def key(entry):
    return entry[1], entry[2], entry[3]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    parser.add_argument("--interval", type=float, default=0.02)
    parser.add_argument("--windows", type=int, default=12000)
    args = parser.parse_args()
    if args.interval <= 0 or args.windows <= 0:
        parser.error("--interval and --windows must be positive")

    fd = os.open(f"/proc/{args.pid}/mem", os.O_RDONLY)
    try:
        ranges = kernelbase_ranges(args.pid)
        address, permissions, path = locate_record(fd, ranges)
        header, entries = read_record(fd, address)
        previous = {key(entry): entry for entry in entries}
        previous_time = time.monotonic_ns()
        print(f"pid={args.pid} module={path} record={address:#x} perms={permissions} "
              f"enabled={header[4]} exe={header[7]:#x}-{header[8]:#x} "
              f"used={header[9]} overflow={header[6]} "
              f"start_tick_ms={previous_time // 1_000_000}", flush=True)
        print("window\ttick_ms\telapsed_ms\tcaller\ttid\tkind\tcalls_delta\tactive\t"
              "last_handle\tlast_timeout\tlast_aux\tlast_result\treturn_ok_delta\t"
              "return_timeout_delta\treturn_failed_delta\treturn_other_delta\t"
              "requested_ms_delta\tmax_timeout\tfinite_delta\tinfinite_delta\t"
              "calls_total\tused\toverflow", flush=True)

        deadline = previous_time
        for window in range(1, args.windows + 1):
            deadline += int(args.interval * 1_000_000_000)
            delay = (deadline - time.monotonic_ns()) / 1_000_000_000
            if delay > 0:
                time.sleep(delay)
            now = time.monotonic_ns()
            header, entries = read_record(fd, address)
            current = {key(entry): entry for entry in entries}
            elapsed_ms = (now - previous_time) / 1_000_000
            for entry_key in sorted(current):
                entry = current[entry_key]
                old = previous.get(entry_key, (0,) * ENTRY_WORDS)
                calls_delta = delta(entry[4], old[4])
                return_ok_delta = delta(entry[10], old[10])
                return_timeout_delta = delta(entry[11], old[11])
                return_failed_delta = delta(entry[12], old[12])
                return_other_delta = delta(entry[13], old[13])
                requested_ms_delta = delta(entry[14], old[14])
                finite_delta = delta(entry[16], old[16])
                infinite_delta = delta(entry[17], old[17])
                # Emit changed counters and every sample of an active wait.  A
                # long blocked call therefore remains visible even though it
                # has not returned and its counters no longer change.
                if not (calls_delta or return_ok_delta or return_timeout_delta
                        or return_failed_delta or return_other_delta
                        or requested_ms_delta or finite_delta or infinite_delta
                        or entry[5]):
                    continue
                print(f"{window}\t{now // 1_000_000}\t{elapsed_ms:.3f}\t"
                      f"{entry[1]:#x}\t{entry[2]}\t{KINDS.get(entry[3], entry[3])}\t"
                      f"{calls_delta}\t{entry[5]}\t{entry[6]:#x}\t{entry[7]}\t"
                      f"{entry[8]:#x}\t{entry[9]:#x}\t{return_ok_delta}\t"
                      f"{return_timeout_delta}\t{return_failed_delta}\t"
                      f"{return_other_delta}\t{requested_ms_delta}\t{entry[15]}\t"
                      f"{finite_delta}\t{infinite_delta}\t{entry[4]}\t"
                      f"{header[9]}\t{header[6]}", flush=True)
            previous = current
            previous_time = now
    finally:
        os.close(fd)


if __name__ == "__main__":
    main()

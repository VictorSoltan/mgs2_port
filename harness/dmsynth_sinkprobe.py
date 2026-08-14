#!/usr/bin/env python3
"""Read or arm the bounded dmsynth render-to-DirectSound probe.

The DLL records into memory only.  This reader runs outside Wine after an
action, so observing the probe does not add file I/O to the render/audio
threads being diagnosed.
"""

import argparse
import json
import os
import struct
import time

MAGIC = 0x31505344
# `_dmsynth_sinkprobe_state` in dmsynth_sinkprobe_target1.dll.
STATE_RVA = 0x3A080
EVENTS = 64
EVENT_WORDS = 30
EVENT_SIZE = EVENT_WORDS * 4
HEADER_WORDS = 10

NAMES = (
    "tick sink synth buffer external_buffer render_position render_frames "
    "render_bytes render_peak_l render_peak_r render_checksum written_before "
    "write_offset play_before write_before lock_hr data1 size1 data2 size2 "
    "copied_peak_l copied_peak_r copied_checksum unlock_hr status volume "
    "frequency play_after write_after written_after"
).split()


def module_base(pid):
    with open("/proc/%d/maps" % pid, encoding="ascii") as stream:
        for line in stream:
            fields = line.split()
            if (len(fields) >= 6 and fields[1].startswith("r-x")
                    and fields[2] == "00000000"
                    and "dmsynth.dll" in fields[-1]):
                return int(fields[0].split("-", 1)[0], 16)
    raise RuntimeError("dmsynth.dll mapping not found")


def read_state(pid, rva=STATE_RVA):
    base = module_base(pid)
    fd = os.open("/proc/%d/mem" % pid, os.O_RDONLY)
    try:
        header = os.pread(fd, HEADER_WORDS * 4, base + rva)
        if len(header) != HEADER_WORDS * 4:
            raise RuntimeError("short sink-probe state header")
        words = struct.unpack("<10I", header)
        if words[0] != MAGIC:
            raise RuntimeError("bad sink-probe magic %#x at %#x" %
                               (words[0], base + rva))
        count = min(words[3], EVENTS)
        raw = os.pread(fd, count * EVENT_SIZE,
                       base + rva + HEADER_WORDS * 4)
    finally:
        os.close(fd)

    records = []
    for index in range(len(raw) // EVENT_SIZE):
        values = struct.unpack_from("<%dI" % EVENT_WORDS, raw,
                                    index * EVENT_SIZE)
        record = dict(zip(NAMES, values))
        for key in ("sink", "synth", "buffer", "data1", "data2"):
            record[key] = hex(record[key])
        for key in ("lock_hr", "unlock_hr"):
            record[key] = hex(record[key])
        records.append(record)

    return {
        "address": hex(base + rva),
        "magic": hex(words[0]),
        "version": words[1],
        "marker": words[2],
        "count": words[3],
        "marker_sink": hex(words[4]),
        "marker_synth": hex(words[5]),
        "marker_group": words[6],
        "marker_status": hex(words[7]),
        "marker_note": words[8],
        "marker_velocity": words[9],
        "records": records,
    }


def arm_state(pid, rva=STATE_RVA):
    """Clear a capture while preventing a target event during the reset."""
    base = module_base(pid)
    address = base + rva
    fd = os.open("/proc/%d/mem" % pid, os.O_RDWR)
    try:
        # A nonzero sentinel blocks the MIDI-side compare/exchange.
        os.pwrite(fd, struct.pack("<I", 0xFFFFFFFF), address + 8)
        # Reset count and marker metadata; old records are ignored once count
        # is zero and will be overwritten by the next bounded capture.
        os.pwrite(fd, struct.pack("<7I", 0, 0, 0, 0, 0, 0, 0), address + 12)
        # Marker is committed last, arming exactly the next target event.
        os.pwrite(fd, struct.pack("<I", 0), address + 8)
    finally:
        os.close(fd)
    return read_state(pid, rva)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    parser.add_argument("--rva", type=lambda value: int(value, 0),
                        default=STATE_RVA)
    parser.add_argument("--arm", action="store_true")
    parser.add_argument("--watch", type=float, default=0)
    args = parser.parse_args()

    if args.arm:
        state = arm_state(args.pid, args.rva)
        state.pop("records")
        print(json.dumps(state, indent=2))
        return
    if not args.watch:
        print(json.dumps(read_state(args.pid, args.rva), indent=2))
        return

    deadline = time.monotonic() + args.watch
    previous = -1
    while time.monotonic() < deadline:
        state = read_state(args.pid, args.rva)
        if state["count"] != previous:
            print(json.dumps(state, separators=(",", ":")), flush=True)
            previous = state["count"]
        time.sleep(0.25)


if __name__ == "__main__":
    main()

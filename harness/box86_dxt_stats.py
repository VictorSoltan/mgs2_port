#!/usr/bin/env python3
"""Read the bounded native-DXT differential counters from a live Box86.

The candidate updates only exported integers on the texture worker.  This
out-of-process reader resolves those integers from the exact mounted ELF and
reads /proc/PID/mem without writing to the game or logging from a hot thread.
"""

import argparse
import os
import struct
import subprocess


ARRAYS = ("mgs2_dxt_calls", "mgs2_dxt_compared", "mgs2_dxt_bad",
          "mgs2_dxt_skipped")
SCALARS = ("mgs2_dxt_armed", "mgs2_dxt_verify",
           "mgs2_dxt_first_bad_set", "mgs2_dxt_first_bad_id",
           "mgs2_dxt_first_bad_call", "mgs2_dxt_first_bad_byte",
           "mgs2_dxt_first_bad_guest", "mgs2_dxt_first_bad_native")
BYTE_ARRAYS = {
    "mgs2_dxt_first_bad_source": 16,
    "mgs2_dxt_first_bad_guest_output": 256,
    "mgs2_dxt_first_bad_native_output": 256,
}


def symbol_addresses(path):
    result = subprocess.run(
        ["readelf", "-Ws", path], check=True, capture_output=True, text=True)
    wanted = set(ARRAYS + SCALARS + tuple(BYTE_ARRAYS))
    addresses = {}
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 8 and fields[-1] in wanted:
            addresses.setdefault(fields[-1], int(fields[1], 16))
    missing = sorted(wanted - addresses.keys())
    if missing:
        raise RuntimeError("missing Box86 symbols: %s" % ", ".join(missing))
    return addresses


def read_words(fd, address, count):
    data = os.pread(fd, count * 4, address)
    if len(data) != count * 4:
        raise RuntimeError("short process-memory read at %#x" % address)
    return struct.unpack("<%dI" % count, data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", required=True, type=int)
    parser.add_argument("--box86", default="/proc/{pid}/exe")
    args = parser.parse_args()
    box86 = args.box86.format(pid=args.pid)
    symbols = symbol_addresses(box86)
    fd = os.open("/proc/%d/mem" % args.pid, os.O_RDONLY)
    try:
        arrays = {name: read_words(fd, symbols[name], 3) for name in ARRAYS}
        scalars = {name: read_words(fd, symbols[name], 1)[0]
                   for name in SCALARS}
        byte_arrays = {
            name: os.pread(fd, size, symbols[name])
            for name, size in BYTE_ARRAYS.items()
        }
    finally:
        os.close(fd)

    print("armed=%d verify=%d" %
          (scalars["mgs2_dxt_armed"], scalars["mgs2_dxt_verify"]))
    for index, label in enumerate(("DXT1", "DXT3", "DXT5")):
        print("%s calls=%d compared=%d mismatched=%d skipped=%d" % (
            label, arrays["mgs2_dxt_calls"][index],
            arrays["mgs2_dxt_compared"][index],
            arrays["mgs2_dxt_bad"][index],
            arrays["mgs2_dxt_skipped"][index]))
    if scalars["mgs2_dxt_first_bad_set"]:
        labels = ("DXT1", "DXT3", "DXT5")
        ident = scalars["mgs2_dxt_first_bad_id"]
        print("first_mismatch=%s call=%d byte=%d guest=%02x native=%02x" % (
            labels[ident] if ident < 3 else "unknown-%d" % ident,
            scalars["mgs2_dxt_first_bad_call"],
            scalars["mgs2_dxt_first_bad_byte"],
            scalars["mgs2_dxt_first_bad_guest"],
            scalars["mgs2_dxt_first_bad_native"]))
        source = byte_arrays["mgs2_dxt_first_bad_source"]
        guest = byte_arrays["mgs2_dxt_first_bad_guest_output"]
        native = byte_arrays["mgs2_dxt_first_bad_native_output"]
        print("source=" + source.hex())
        changed_words = sorted({index // 4 for index, (a, b)
                                in enumerate(zip(guest, native)) if a != b})
        for word in changed_words:
            offset = word * 4
            guest_bits = struct.unpack_from("<I", guest, offset)[0]
            native_bits = struct.unpack_from("<I", native, offset)[0]
            print("word=%d byte=%d guest_bits=%08x native_bits=%08x" %
                  (word, offset, guest_bits, native_bits))


if __name__ == "__main__":
    main()

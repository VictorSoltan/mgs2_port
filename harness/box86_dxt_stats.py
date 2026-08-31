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
SURFACE_SCALARS = (
    "mgs2_dxt_surface_armed", "mgs2_dxt_surface_verify",
    "mgs2_dxt_surface_calls", "mgs2_dxt_surface_native_calls",
    "mgs2_dxt_surface_guest_calls", "mgs2_dxt_surface_compared",
    "mgs2_dxt_surface_bad", "mgs2_dxt_surface_skipped",
    "mgs2_dxt_surface_cache_misses", "mgs2_dxt_surface_blocks",
    "mgs2_dxt_surface_pixels", "mgs2_dxt_surface_first_bad_set",
    "mgs2_dxt_surface_first_bad_kind", "mgs2_dxt_surface_first_bad_call",
    "mgs2_dxt_surface_first_bad_byte", "mgs2_dxt_surface_first_bad_guest",
    "mgs2_dxt_surface_first_bad_native",
)
SURFACE_ARRAYS = {"mgs2_dxt_surface_fallback": 5}
OPTIONAL_SURFACE_ARRAYS = {"mgs2_dxt_surface_witness": 6}

WITNESS_MAGIC = 0x31535744  # "DWS1"
WITNESS_STRONG_SELFTEST = 1 << 0
WITNESS_ARMED = 1 << 1
WITNESS_INTERCEPTED = 1 << 2
WITNESS_NATIVE_SEEN = 1 << 3
WITNESS_GUEST_SEEN = 1 << 4
WITNESS_GUEST_FAILED = 1 << 5
FALLBACK_NAMES = ("cache", "format", "colorkey", "layout", "guest", "none")


def symbol_addresses(path):
    result = subprocess.run(
        ["readelf", "-Ws", path], check=True, capture_output=True, text=True)
    wanted = set(ARRAYS + SCALARS + SURFACE_SCALARS
                 + tuple(BYTE_ARRAYS) + tuple(SURFACE_ARRAYS)
                 + tuple(OPTIONAL_SURFACE_ARRAYS))
    required = wanted - set(OPTIONAL_SURFACE_ARRAYS)
    addresses = {}
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 8 and fields[-1] in wanted:
            addresses.setdefault(fields[-1], int(fields[1], 16))
    missing = sorted(required - addresses.keys())
    if missing:
        raise RuntimeError("missing Box86 symbols: %s" % ", ".join(missing))
    return addresses


def witness_verdict(words):
    if words is None:
        return "UNAVAILABLE: this Box86 predates the bounded production witness"
    if (len(words) != 6 or words[0] != WITNESS_MAGIC or words[1] != 1
            or words[2] != 6 or words[3] != ((~WITNESS_MAGIC) & 0xFFFFFFFF)):
        return "REFUSED: malformed DXT-surface witness header"
    flags = words[4]
    if not (flags & WITNESS_STRONG_SELFTEST):
        return "REFUSED: strengthened DXT-surface self-test did not pass"
    if not (flags & WITNESS_ARMED):
        return "REFUSED: DXT-surface bridge was not armed"
    if not (flags & WITNESS_INTERCEPTED):
        return "NOT_REACHED: bridge armed but guest signature was never intercepted"
    if flags & WITNESS_GUEST_FAILED:
        return "REFUSED: guest fallback call failed"
    native = bool(flags & WITNESS_NATIVE_SEEN)
    guest = bool(flags & WITNESS_GUEST_SEEN)
    if native and guest:
        return "MIXED: native conversion and conservative guest fallback both observed"
    if native:
        return "NATIVE_CONFIRMED: live calls completed through the native conversion"
    if guest:
        return "FALLBACK_ONLY: intercepted calls used only the guest fallback"
    return "INCOMPLETE: interception observed but no completed conversion witnessed"


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
        surface = {name: read_words(fd, symbols[name], 1)[0]
                   for name in SURFACE_SCALARS}
        surface_arrays = {
            name: read_words(fd, symbols[name], size)
            for name, size in SURFACE_ARRAYS.items()
        }
        witness = (read_words(fd, symbols["mgs2_dxt_surface_witness"], 6)
                   if "mgs2_dxt_surface_witness" in symbols else None)
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

    fallback = surface_arrays["mgs2_dxt_surface_fallback"]
    if witness is None:
        print("surface_witness unavailable")
    elif witness_verdict(witness).startswith("REFUSED: malformed"):
        print("surface_witness malformed=" + " ".join("%08x" % word
                                                       for word in witness))
    else:
        flags = witness[4]
        first_fallback = witness[5]
        fallback_name = (FALLBACK_NAMES[first_fallback]
                         if first_fallback < len(FALLBACK_NAMES)
                         else "invalid-%d" % first_fallback)
        print("surface_witness strong_selftest=%d armed=%d intercepted=%d "
              "native_seen=%d guest_seen=%d guest_failed=%d first_fallback=%s" % (
                  bool(flags & WITNESS_STRONG_SELFTEST),
                  bool(flags & WITNESS_ARMED),
                  bool(flags & WITNESS_INTERCEPTED),
                  bool(flags & WITNESS_NATIVE_SEEN),
                  bool(flags & WITNESS_GUEST_SEEN),
                  bool(flags & WITNESS_GUEST_FAILED), fallback_name))
    print("surface_verdict " + witness_verdict(witness))
    print("surface armed=%d verify=%d calls=%d native=%d guest=%d "
          "compared=%d mismatched=%d skipped=%d" % (
              surface["mgs2_dxt_surface_armed"],
              surface["mgs2_dxt_surface_verify"],
              surface["mgs2_dxt_surface_calls"],
              surface["mgs2_dxt_surface_native_calls"],
              surface["mgs2_dxt_surface_guest_calls"],
              surface["mgs2_dxt_surface_compared"],
              surface["mgs2_dxt_surface_bad"],
              surface["mgs2_dxt_surface_skipped"]))
    print("surface cache_misses=%d blocks=%d pixels=%d "
          "fallback_cache=%d format=%d colorkey=%d layout=%d guest=%d" % (
              surface["mgs2_dxt_surface_cache_misses"],
              surface["mgs2_dxt_surface_blocks"],
              surface["mgs2_dxt_surface_pixels"],
              fallback[0], fallback[1], fallback[2], fallback[3], fallback[4]))
    if surface["mgs2_dxt_surface_first_bad_set"]:
        print("surface_first_mismatch=call=%d kind=%d byte=%d "
              "guest=%08x native=%08x" % (
                  surface["mgs2_dxt_surface_first_bad_call"],
                  surface["mgs2_dxt_surface_first_bad_kind"],
                  surface["mgs2_dxt_surface_first_bad_byte"],
                  surface["mgs2_dxt_surface_first_bad_guest"],
                  surface["mgs2_dxt_surface_first_bad_native"]))


if __name__ == "__main__":
    main()

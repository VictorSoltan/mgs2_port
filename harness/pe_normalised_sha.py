#!/usr/bin/env python3
"""SHA-256 of a PE image with the link timestamp and checksum zeroed.

Two builds of byte-identical WineD3D sources differ in exactly three bytes --
the COFF TimeDateStamp and two bytes of the optional-header CheckSum. So a raw
hash can never say "this binary came from that source", while a hash with those
fields blanked can. mingw's ld also has --no-insert-timestamp, which would make
the raw hashes match; this exists so the question can be answered about binaries
that were already built without it.

usage: pe_normalised_sha.py <file>...
"""
import hashlib
import struct
import sys


def normalise(data):
    if data[:2] != b"MZ":
        return data                      # not a PE: hash as-is (ELF, etc.)
    pe = struct.unpack_from("<I", data, 0x3c)[0]
    if data[pe:pe + 4] != b"PE\0\0":
        return data
    b = bytearray(data)
    struct.pack_into("<I", b, pe + 8, 0)             # COFF TimeDateStamp
    opt = pe + 24
    magic = struct.unpack_from("<H", b, opt)[0]
    if magic in (0x10b, 0x20b):
        struct.pack_into("<I", b, opt + 64, 0)       # OptionalHeader CheckSum
    return bytes(b)


def main():
    for path in sys.argv[1:]:
        with open(path, "rb") as fh:
            print("%s  %s" % (hashlib.sha256(normalise(fh.read())).hexdigest(), path))


if __name__ == "__main__":
    main()

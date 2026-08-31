#!/usr/bin/env python3
"""Regression checks for the fail-closed bounded DMT1 locator."""

import os
import struct
import tempfile

import dmime_state


HEADER = struct.pack(
    "<6I", dmime_state.MAGIC, dmime_state.VERSION,
    dmime_state.HEADER_WORDS, dmime_state.RECORD_WORDS, dmime_state.EVENTS,
    (~dmime_state.MAGIC) & 0xFFFFFFFF)


def expect_failure(fd, ranges, fragment):
    try:
        dmime_state.locate_state(fd, ranges)
    except RuntimeError as error:
        assert fragment in str(error), error
    else:
        raise AssertionError(f"locator accepted case requiring {fragment!r}")


def main():
    size = dmime_state.SCAN_CHUNK * 2 + 256
    with tempfile.TemporaryFile() as stream:
        stream.truncate(size)
        # Exercise the overlap path while keeping the header DWORD-aligned.
        address = dmime_state.SCAN_CHUNK - 8
        os.pwrite(stream.fileno(), HEADER, address)
        assert dmime_state.locate_state(stream.fileno(), [(0, size)]) == address

        os.pwrite(stream.fileno(), HEADER, dmime_state.SCAN_CHUNK + 64)
        expect_failure(stream.fileno(), [(0, size)], "ambiguous")

    with tempfile.TemporaryFile() as stream:
        stream.truncate(4096)
        expect_failure(stream.fileno(), [(0, 4096)], "not found")

    with tempfile.TemporaryFile() as stream:
        expect_failure(
            stream.fileno(), [(0, dmime_state.MAX_SCAN_BYTES + 1)],
            "oversized")

    print("ok     bounded dmime DMT1 locator refuses missing/ambiguous images")


if __name__ == "__main__":
    main()

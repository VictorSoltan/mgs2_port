#!/usr/bin/env python3
"""Bounded, event-driven file-open capture for transition stalls.

Unlike syscall tracing or /proc polling, inotify sleeps until the kernel reports
an open/close/access event.  Watch only explicitly supplied directories; it is
not recursive, so the caller controls the scope and event volume.
"""

import argparse
import ctypes
import errno
import os
import select
import struct
import time


IN_ACCESS = 0x00000001
IN_OPEN = 0x00000020
IN_CLOSE_WRITE = 0x00000008
IN_CLOSE_NOWRITE = 0x00000010
IN_CLOEXEC = 0x00080000
IN_NONBLOCK = 0x00000800
EVENT = struct.Struct("iIII")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directories", nargs="+")
    parser.add_argument("--duration", type=float, default=15.0)
    parser.add_argument("--access", action="store_true",
            help="include IN_ACCESS; normally open/close is enough and quieter")
    args = parser.parse_args()

    libc = ctypes.CDLL(None, use_errno=True)
    fd = libc.inotify_init1(IN_CLOEXEC | IN_NONBLOCK)
    if fd < 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))

    mask = IN_OPEN | IN_CLOSE_WRITE | IN_CLOSE_NOWRITE
    if args.access:
        mask |= IN_ACCESS
    watches = {}
    for directory in args.directories:
        encoded = os.fsencode(directory)
        wd = libc.inotify_add_watch(fd, ctypes.c_char_p(encoded), mask)
        if wd < 0:
            error = ctypes.get_errno()
            raise OSError(error, "%s: %s" % (directory, os.strerror(error)))
        watches[wd] = directory

    deadline = time.monotonic() + args.duration
    print("armed wall=%.6f mono=%.6f %s" %
            (time.time(), time.monotonic(), " ".join(args.directories)), flush=True)
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            readable, _, _ = select.select([fd], [], [], remaining)
            if not readable:
                break
            try:
                data = os.read(fd, 65536)
            except OSError as exc:
                if exc.errno == errno.EAGAIN:
                    continue
                raise
            offset = 0
            while offset + EVENT.size <= len(data):
                wd, event_mask, _cookie, length = EVENT.unpack_from(data, offset)
                offset += EVENT.size
                raw_name = data[offset:offset + length]
                offset += length
                name = os.fsdecode(raw_name.split(b"\0", 1)[0])
                kinds = []
                if event_mask & IN_OPEN:
                    kinds.append("OPEN")
                if event_mask & IN_ACCESS:
                    kinds.append("ACCESS")
                if event_mask & IN_CLOSE_WRITE:
                    kinds.append("CLOSE_WRITE")
                if event_mask & IN_CLOSE_NOWRITE:
                    kinds.append("CLOSE_READ")
                print("wall=%.6f mono=%.6f %s %s" %
                        (time.time(), time.monotonic(), "+".join(kinds),
                        os.path.join(watches.get(wd, "?"), name)), flush=True)
    finally:
        os.close(fd)
    print("done wall=%.6f mono=%.6f" % (time.time(), time.monotonic()), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

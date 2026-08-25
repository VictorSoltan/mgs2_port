#!/usr/bin/env python3
"""Bounded external mincore timeline for explicitly named regular files.

The mappings are private and never dereferenced.  mincore therefore observes
page-cache residency without faulting the target pages in.  Rows stay in RAM
until shutdown so the measurement does not write while the game is loading.
"""

import argparse
import ctypes
import mmap
import os
import signal
import stat
import time


STOP = False


def stop(unused_signum, unused_frame):
    global STOP
    STOP = True


class FileResidency:
    def __init__(self, path):
        self.path = path
        info = os.stat(path, follow_symlinks=True)
        if not stat.S_ISREG(info.st_mode) or info.st_size <= 0:
            raise RuntimeError("not a nonempty regular file: %s" % path)
        self.size = info.st_size
        self.page_size = os.sysconf("SC_PAGE_SIZE")
        self.pages = (self.size + self.page_size - 1) // self.page_size
        self.fd = os.open(path, os.O_RDONLY)
        self.mapping = mmap.mmap(self.fd, self.size, flags=mmap.MAP_PRIVATE,
                                 prot=mmap.PROT_READ | mmap.PROT_WRITE)
        self.address = ctypes.addressof(ctypes.c_char.from_buffer(self.mapping))
        self.vector = (ctypes.c_ubyte * self.pages)()

    def resident(self, mincore):
        result = mincore(ctypes.c_void_p(self.address),
                         ctypes.c_size_t(self.size), self.vector)
        if result:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error), self.path)
        return sum(1 for value in self.vector if value & 1)

    def close(self):
        self.mapping.close()
        os.close(self.fd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--paths", required=True,
                        help="os.pathsep-separated absolute paths")
    parser.add_argument("--interval", type=float, default=0.05)
    parser.add_argument("--windows", type=int, default=4800)
    parser.add_argument("--max-bytes", type=int, default=16 * 1024 * 1024)
    parser.add_argument("--max-files", type=int, default=8)
    args = parser.parse_args()
    paths = [path for path in args.paths.split(os.pathsep) if path]
    if args.interval <= 0 or args.windows <= 0:
        parser.error("interval and windows must be positive")
    if not paths or len(paths) > args.max_files:
        parser.error("path count is empty or exceeds max-files")
    if any(not os.path.isabs(path) for path in paths):
        parser.error("all paths must be absolute")

    files = [FileResidency(path) for path in paths]
    total_bytes = sum(item.size for item in files)
    if total_bytes > args.max_bytes:
        for item in files:
            item.close()
        parser.error("mapped files exceed max-bytes")

    libc = ctypes.CDLL(None, use_errno=True)
    mincore = libc.mincore
    mincore.argtypes = [ctypes.c_void_p, ctypes.c_size_t,
                        ctypes.POINTER(ctypes.c_ubyte)]
    mincore.restype = ctypes.c_int
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    started_ns = time.monotonic_ns()
    rows = []
    deadline = started_ns
    try:
        for unused_window in range(args.windows):
            if STOP:
                break
            deadline += int(args.interval * 1_000_000_000)
            delay = (deadline - time.monotonic_ns()) / 1_000_000_000
            if delay > 0:
                time.sleep(delay)
            tick_ms = time.monotonic_ns() // 1_000_000
            rows.append((tick_ms,
                         [item.resident(mincore) for item in files]))
    finally:
        for item in files:
            item.close()

    print("measurement=mincore snapshot without page dereference")
    print("start_tick_ms=%d interval=%.6f rows=%d files=%d bytes=%d" %
          (started_ns // 1_000_000, args.interval, len(rows), len(files),
           total_bytes))
    print("tick_ms\tfile\tresident_pages\ttotal_pages\tresident_pct")
    for tick_ms, counts in rows:
        for item, count in zip(files, counts):
            print("%d\t%s\t%d\t%d\t%.3f" %
                  (tick_ms, item.path, count, item.pages,
                   100.0 * count / item.pages))


if __name__ == "__main__":
    main()

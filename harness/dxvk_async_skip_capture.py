#!/usr/bin/env python3
"""Read the research DXVK async skipped-draw counter outside game threads.

The DXVK candidate only increments a 32-bit memory counter when it queues a
missing graphics pipeline instead of drawing. This process samples that export
through read-only /proc/PID/mem, keeps a bounded event list, and writes only
after capture stops.
"""

import argparse
import os
import signal
import time

from dxvk_present_count import exported_rva, module_base, read_count


COUNTER_EXPORT = b"MGS2DxvkAsyncSkippedDrawCount"
stop_requested = False


def request_stop(unused_signum, unused_frame):
    global stop_requested
    stop_requested = True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    parser.add_argument("--interval", type=float, default=0.01)
    parser.add_argument("--windows", type=int, default=24000)
    parser.add_argument("--max-events", type=int, default=4096)
    args = parser.parse_args()
    if args.interval <= 0 or args.windows <= 0 or args.max_events <= 0:
        parser.error("--interval, --windows and --max-events must be positive")

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    base, path = module_base(args.pid)
    rva = exported_rva(path, wanted=COUNTER_EXPORT)
    address = base + rva
    fd = os.open(f"/proc/{args.pid}/mem", os.O_RDONLY)
    events = []
    dropped_events = 0
    sampled_windows = 0
    try:
        start_count = read_count(fd, address)
        previous = start_count
        start_ns = time.monotonic_ns()
        deadline = start_ns
        for window in range(1, args.windows + 1):
            if stop_requested:
                break
            deadline += int(args.interval * 1_000_000_000)
            delay = (deadline - time.monotonic_ns()) / 1_000_000_000
            if delay > 0:
                time.sleep(delay)
            current = read_count(fd, address)
            sampled_windows = window
            delta = (current - previous) & 0xFFFFFFFF
            if delta:
                event = (window, time.monotonic_ns() // 1_000_000, delta, current)
                if len(events) < args.max_events:
                    events.append(event)
                else:
                    dropped_events += 1
            previous = current
        end_count = read_count(fd, address)
        end_ns = time.monotonic_ns()
    finally:
        os.close(fd)

    print(f"pid={args.pid} module={path} base={base:#x} rva={rva:#x} "
          f"export={COUNTER_EXPORT.decode()}")
    print(f"start_tick_ms={start_ns // 1_000_000} end_tick_ms={end_ns // 1_000_000} "
          f"windows={sampled_windows} interval_ms={args.interval * 1000:.3f}")
    print(f"start={start_count} end={end_count} "
          f"delta={(end_count - start_count) & 0xFFFFFFFF} "
          f"retained_events={len(events)} dropped_events={dropped_events}")
    print("window\ttick_ms\tdelta\ttotal")
    for window, tick_ms, delta, total in events:
        print(f"{window}\t{tick_ms}\t{delta}\t{total}")


if __name__ == "__main__":
    main()

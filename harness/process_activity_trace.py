#!/usr/bin/env python3
"""Sample one game's aggregate I/O, faults and CPU externally through /proc."""

import argparse
import time


def read_io(pid):
    # This ROCKNIX kernel omits /proc/PID/io. Keep the CPU/fault sampler useful,
    # but state the absence explicitly: zero deltas must never be presented as
    # evidence that the process performed no I/O.
    values = {"rchar": 0, "read_bytes": 0, "syscr": 0}
    try:
        with open(f"/proc/{pid}/io", encoding="ascii") as stream:
            for line in stream:
                name, value = line.split(":", 1)
                values[name] = int(value)
    except FileNotFoundError:
        return values, False
    return values, True


def read_stat(pid):
    with open(f"/proc/{pid}/stat", encoding="ascii") as stream:
        line = stream.read()
    # The comm field is parenthesized and may contain spaces. Fields after the
    # closing parenthesis start at process-state (field 3 in proc_pid_stat(5)).
    fields = line[line.rfind(")") + 2:].split()
    return {
        "minflt": int(fields[7]),
        "majflt": int(fields[9]),
        "utime": int(fields[11]),
        "stime": int(fields[12]),
    }


def snapshot(pid):
    values, io_available = read_io(pid)
    values.update(read_stat(pid))
    return values, io_available


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    parser.add_argument("--interval", type=float, default=0.02)
    parser.add_argument("--windows", type=int, default=10000)
    args = parser.parse_args()
    if args.interval <= 0 or args.windows <= 0:
        parser.error("--interval and --windows must be positive")

    previous, io_available = snapshot(args.pid)
    previous_time = time.monotonic_ns()
    print(f"pid={args.pid} start_tick_ms={previous_time // 1_000_000} "
          f"proc_io={'available' if io_available else 'unavailable'}",
          flush=True)
    print("window\ttick_ms\telapsed_ms\trchar\tread_bytes\tsyscr\t"
          "minflt\tmajflt\tutime_ticks\tstime_ticks", flush=True)
    deadline = previous_time
    keys = ("rchar", "read_bytes", "syscr", "minflt", "majflt", "utime", "stime")
    for window in range(1, args.windows + 1):
        deadline += int(args.interval * 1_000_000_000)
        delay = (deadline - time.monotonic_ns()) / 1_000_000_000
        if delay > 0:
            time.sleep(delay)
        now = time.monotonic_ns()
        try:
            current, current_io_available = snapshot(args.pid)
        except FileNotFoundError:
            print(f"process-exited tick_ms={time.monotonic_ns() // 1_000_000}",
                  flush=True)
            break
        if current_io_available != io_available:
            raise RuntimeError("/proc/PID/io availability changed during capture")
        deltas = [current[key] - previous[key] for key in keys]
        print(f"{window}\t{now // 1_000_000}\t"
              f"{(now - previous_time) / 1_000_000:.3f}\t"
              + "\t".join(str(delta) for delta in deltas), flush=True)
        previous = current
        previous_time = now


if __name__ == "__main__":
    main()

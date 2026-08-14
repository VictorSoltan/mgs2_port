#!/usr/bin/env python3
"""Record the translated gptokeyb keyboard stream without grabbing it.

The compositor continues receiving the same events.  JSONL is flushed after
each input batch so an abrupt game failure still leaves a replayable prefix.
"""

import argparse
import json
import os
import select
import signal
import struct
import time

EVENT = struct.Struct("llHHi")
stop = False


def request_stop(unused_signum, unused_frame):
    global stop
    stop = True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("device")
    parser.add_argument("output")
    args = parser.parse_args()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    fd = os.open(args.device, os.O_RDONLY | os.O_NONBLOCK)
    temporary = args.output + ".part"
    first_us = None
    count = 0
    started_ns = time.monotonic_ns()
    with open(temporary, "w", encoding="utf-8") as stream:
        stream.write(json.dumps({
            "format": "mgs2-input-v1",
            "device": args.device,
            "started_monotonic_ns": started_ns,
            "event_size": EVENT.size,
        }, separators=(",", ":")) + "\n")
        stream.flush()
        while not stop:
            readable, _, _ = select.select([fd], [], [], 0.5)
            if not readable:
                continue
            try:
                raw = os.read(fd, EVENT.size * 128)
            except BlockingIOError:
                continue
            observed_ns = time.monotonic_ns()
            for offset in range(0, len(raw) - EVENT.size + 1, EVENT.size):
                sec, usec, event_type, code, value = EVENT.unpack_from(raw, offset)
                event_us = sec * 1000000 + usec
                if first_us is None:
                    first_us = event_us
                stream.write(json.dumps({
                    "t_us": event_us - first_us,
                    "kernel_us": event_us,
                    "observed_monotonic_ns": observed_ns,
                    "type": event_type,
                    "code": code,
                    "value": value,
                }, separators=(",", ":")) + "\n")
                count += 1
            stream.flush()
        stream.write(json.dumps({
            "end": True,
            "events": count,
            "duration_monotonic_ns": time.monotonic_ns() - started_ns,
        }, separators=(",", ":")) + "\n")
        stream.flush()
    os.close(fd)
    os.replace(temporary, args.output)


if __name__ == "__main__":
    main()

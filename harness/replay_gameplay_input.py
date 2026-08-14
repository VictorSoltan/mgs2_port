#!/usr/bin/env python3
"""Replay one record_gameplay_input.py trace through one uinput keyboard."""

import argparse
import fcntl
import json
import os
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import send_key

EVENT = struct.Struct("llHHi")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("trace")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--lead", type=float, default=1.0)
    args = parser.parse_args()
    if args.speed <= 0:
        raise SystemExit("--speed must be positive")

    events = []
    with open(args.trace, encoding="utf-8") as stream:
        header = json.loads(next(stream))
        if header.get("format") != "mgs2-input-v1":
            raise SystemExit("unsupported trace format")
        for line in stream:
            item = json.loads(line)
            if not item.get("end"):
                events.append(item)
    if not events:
        raise SystemExit("trace contains no events")

    # Only the translated keyboard's EV_KEY and EV_SYN events are replayable.
    events = [item for item in events if item["type"] in
              (send_key.EV_KEY, send_key.EV_SYN)]
    fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
    fcntl.ioctl(fd, send_key.UI_SET_EVBIT, send_key.EV_KEY)
    for code in range(1, 128):
        fcntl.ioctl(fd, send_key.UI_SET_KEYBIT, code)
    os.write(fd, send_key.make_uidev("mgsdbg-recorded-replay"))
    fcntl.ioctl(fd, send_key.UI_DEV_CREATE)
    time.sleep(send_key.SETTLE_S)
    print("окно сфокусировано: %s" % send_key.focus_game(), flush=True)
    time.sleep(args.lead)

    first_us = events[0]["t_us"]
    started = time.monotonic()
    print("event_start_tick=%d" % (started * 1000), flush=True)
    for item in events:
        target = started + (item["t_us"] - first_us) / 1000000.0 / args.speed
        delay = target - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        os.write(fd, EVENT.pack(0, 0, item["type"], item["code"], item["value"]))

    time.sleep(0.25)
    print("event_end_tick=%d" % (time.monotonic() * 1000), flush=True)
    fcntl.ioctl(fd, send_key.UI_DEV_DESTROY)
    os.close(fd)
    print("воспроизведено событий: %d" % len(events), flush=True)


if __name__ == "__main__":
    main()

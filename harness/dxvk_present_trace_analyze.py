#!/usr/bin/env python3
"""Summarise no-PRESENT runs from dxvk_present_count.py high-rate samples.

This does not pretend that polling reconstructs exact frame times. It reports a
lower bound: the elapsed time of consecutive sampling windows in which the
memory counter did not advance. That is sufficient to distinguish ordinary
20-40 ms spacing from the reported 0.2-1+ second transition hitches without
putting logging in DXVK's Present path.
"""

import argparse
import bisect
import re
from dataclasses import dataclass


@dataclass
class Gap:
    start_tick_ms: int
    end_tick_ms: int
    duration_ms: float
    windows: int


def read_rows(path):
    rows = []
    with open(path, encoding="utf-8") as stream:
        for line in stream:
            fields = line.rstrip().split("\t")
            if len(fields) != 6 or not fields[0].isdigit():
                continue
            rows.append({
                "window": int(fields[0]),
                "tick_ms": int(fields[1]),
                "frames": int(fields[2]),
                "elapsed_ms": float(fields[3]),
                "total": int(fields[5]),
            })
    return rows


def find_gaps(rows):
    gaps = []
    start = None
    duration = 0.0
    windows = 0
    for row in rows:
        if row["frames"] == 0:
            if start is None:
                start = row["tick_ms"] - round(row["elapsed_ms"])
            duration += row["elapsed_ms"]
            windows += 1
        elif start is not None:
            gaps.append(Gap(start, row["tick_ms"], duration, windows))
            start = None
            duration = 0.0
            windows = 0
    if start is not None and rows:
        gaps.append(Gap(start, rows[-1]["tick_ms"], duration, windows))
    return gaps


def read_markers(path):
    if not path:
        return []
    markers = []
    patterns = (
        (re.compile(r"autoload-start tick=(\d+)"), "autoload-start"),
        (re.compile(r"== ([^:]+) : .* tick=(\d+) =="), "key"),
        (re.compile(r"снимок ([^ ]+) tick=(\d+)"), "shot"),
    )
    with open(path, encoding="utf-8") as stream:
        for line in stream:
            for pattern, kind in patterns:
                match = pattern.search(line)
                if not match:
                    continue
                if kind == "autoload-start":
                    label, tick = kind, int(match.group(1))
                else:
                    label = "%s:%s" % (kind, match.group(1))
                    tick = int(match.group(2))
                markers.append((tick, label))
                break
    # Keep file order for equal ticks. A screenshot marker is immediately
    # followed by the next key marker in the autoload log, and the key is the
    # useful phase boundary when both round to the same millisecond.
    return sorted(markers, key=lambda marker: marker[0])


def preceding_marker(markers, tick):
    if not markers:
        return "-", 0
    index = bisect.bisect_right([marker[0] for marker in markers], tick) - 1
    if index < 0:
        return "pre-automation", 0
    marker_tick, label = markers[index]
    return label, tick - marker_tick


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("trace")
    parser.add_argument("--markers", help="autoload log with monotonic ticks")
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()

    rows = read_rows(args.trace)
    if not rows:
        raise SystemExit("no trace rows found")
    gaps = find_gaps(rows)
    markers = read_markers(args.markers)
    elapsed = sum(row["elapsed_ms"] for row in rows)
    frames = sum(row["frames"] for row in rows)

    print("measurement=no-PRESENT polling lower bound")
    print(f"windows={len(rows)} elapsed_ms={elapsed:.3f} frames={frames} "
          f"avg_fps={frames * 1000.0 / elapsed:.3f}")
    for threshold in (50, 100, 200, 500, 1000):
        print(f"gaps_ge_{threshold}ms="
              f"{sum(gap.duration_ms >= threshold for gap in gaps)}")
    print("rank\tstart_tick_ms\tend_tick_ms\tlower_bound_ms\twindows\t"
          "preceding_marker\toffset_ms")
    for rank, gap in enumerate(
            sorted(gaps, key=lambda value: value.duration_ms, reverse=True)
            [:args.top], 1):
        marker, offset = preceding_marker(markers, gap.start_tick_ms)
        print(f"{rank}\t{gap.start_tick_ms}\t{gap.end_tick_ms}\t"
              f"{gap.duration_ms:.3f}\t{gap.windows}\t{marker}\t{offset}")


if __name__ == "__main__":
    main()

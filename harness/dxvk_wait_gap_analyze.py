#!/usr/bin/env python3
"""Join the external Wine wait census to DXVK no-PRESENT gaps.

The census rows contain counter deltas sampled every 20 ms.  This tool sums
calls, requested finite timeouts and returns inside each lower-bound PRESENT
gap.  Repeated samples of an already-active call are reported as an approximate
active duration; they are not miscounted as new calls.
"""

import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import dxvk_present_trace_analyze as present  # noqa: E402


INFINITE = 0xFFFFFFFF


def read_wait_rows(path):
    rows = []
    with open(path, encoding="utf-8") as stream:
        for line in stream:
            fields = line.rstrip().split("\t")
            if len(fields) != 23 or not fields[0].isdigit():
                continue
            rows.append({
                "tick_ms": int(fields[1]),
                "elapsed_ms": float(fields[2]),
                "caller": int(fields[3], 0),
                "tid": int(fields[4]),
                "kind": fields[5],
                "calls": int(fields[6]),
                "active": int(fields[7]),
                "last_timeout": int(fields[9]),
                "ok": int(fields[12]),
                "timeout": int(fields[13]),
                "failed": int(fields[14]),
                "other": int(fields[15]),
                "requested_ms": int(fields[16]),
                "finite": int(fields[18]),
                "infinite": int(fields[19]),
            })
    return rows


def aggregate(rows):
    result = collections.defaultdict(lambda: {
        "calls": 0,
        "active_ms": 0.0,
        "active_samples": 0,
        "ok": 0,
        "timeout": 0,
        "failed": 0,
        "other": 0,
        "requested_ms": 0,
        "finite": 0,
        "infinite": 0,
        "max_started_timeout": 0,
    })
    for row in rows:
        key = row["caller"], row["tid"], row["kind"]
        item = result[key]
        item["calls"] += row["calls"]
        item["ok"] += row["ok"]
        item["timeout"] += row["timeout"]
        item["failed"] += row["failed"]
        item["other"] += row["other"]
        item["requested_ms"] += row["requested_ms"]
        item["finite"] += row["finite"]
        item["infinite"] += row["infinite"]
        if row["active"]:
            item["active_samples"] += 1
            item["active_ms"] += row["elapsed_ms"]
        if row["calls"] and row["last_timeout"] != INFINITE:
            item["max_started_timeout"] = max(
                item["max_started_timeout"], row["last_timeout"])
    return result


def importance(item):
    # Requested timeout and observed active duration answer the causal question
    # before raw call volume (e.g. millions of Sleep(0) yields).
    return (item["requested_ms"], item["active_ms"], item["calls"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("present_trace")
    parser.add_argument("wait_trace")
    parser.add_argument("--markers")
    parser.add_argument("--min-ms", type=float, default=200.0)
    parser.add_argument("--top-gaps", type=int, default=20)
    parser.add_argument("--top-waits", type=int, default=12)
    args = parser.parse_args()

    gaps = [gap for gap in present.find_gaps(
        present.read_rows(args.present_trace))
            if gap.duration_ms >= args.min_ms]
    gaps.sort(key=lambda gap: gap.duration_ms, reverse=True)
    waits = read_wait_rows(args.wait_trace)
    markers = present.read_markers(args.markers)
    if not waits:
        raise SystemExit("no wait-census rows parsed")

    print("measurement=wait counter deltas inside no-PRESENT lower-bound gaps")
    print("wait_rows=%d gaps_ge_%.0fms=%d" %
          (len(waits), args.min_ms, len(gaps)))
    for rank, gap in enumerate(gaps[:args.top_gaps], 1):
        selected = [row for row in waits
                    if gap.start_tick_ms < row["tick_ms"] <= gap.end_tick_ms]
        grouped = aggregate(selected)
        marker, offset = present.preceding_marker(markers, gap.start_tick_ms)
        print("gap rank=%d start_tick_ms=%d lower_bound_ms=%.3f marker=%s "
              "offset_ms=%d wait_rows=%d" %
              (rank, gap.start_tick_ms, gap.duration_ms, marker, offset,
               len(selected)))
        ordered = sorted(grouped.items(), key=lambda pair: importance(pair[1]),
                         reverse=True)
        for (caller, tid, kind), item in ordered[:args.top_waits]:
            print("  caller=%#x tid=%d kind=%s calls=%d requested_ms=%d "
                  "active_ms=%.1f active_samples=%d returns=%d/%d/%d/%d "
                  "finite=%d infinite=%d max_started_timeout=%d" %
                  (caller, tid, kind, item["calls"], item["requested_ms"],
                   item["active_ms"], item["active_samples"], item["ok"],
                   item["timeout"], item["failed"], item["other"],
                   item["finite"], item["infinite"],
                   item["max_started_timeout"]))


if __name__ == "__main__":
    main()

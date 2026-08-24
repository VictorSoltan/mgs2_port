#!/usr/bin/env python3
"""Attribute perf samples to externally measured DXVK no-PRESENT gaps."""

import argparse
import collections
import os
import re

import dxvk_present_trace_analyze as present


# perf script -F comm,pid,tid,time,ip,sym,dso
LINE = re.compile(
    r"^\s*(?P<comm>.*?)\s+(?P<pid>\d+)/(?P<tid>\d+)\s+"
    r"(?P<time>[0-9.]+):\s+(?P<ip>[0-9a-f]+)\s+.*"
    r"\((?P<dso>[^()]*)\)\s*$"
)


def read_samples(path):
    samples = []
    with open(path, encoding="utf-8", errors="replace") as stream:
        for line in stream:
            match = LINE.match(line)
            if not match:
                continue
            samples.append({
                "tick_ms": int(float(match.group("time")) * 1000),
                "comm": match.group("comm").strip(),
                "tid": int(match.group("tid")),
                "dso": match.group("dso").strip(),
            })
    return samples


def compact_counter(counter, total, limit=5):
    if not total:
        return "none"
    return "; ".join(
        "%s=%d(%.1f%%)" % (name, count, 100.0 * count / total)
        for name, count in counter.most_common(limit)
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("present_trace")
    parser.add_argument("perf_script")
    parser.add_argument("--markers")
    parser.add_argument("--min-ms", type=float, default=200.0)
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()

    gaps = [gap for gap in present.find_gaps(
        present.read_rows(args.present_trace))
            if gap.duration_ms >= args.min_ms]
    gaps.sort(key=lambda gap: gap.duration_ms, reverse=True)
    samples = read_samples(args.perf_script)
    markers = present.read_markers(args.markers)
    if not samples:
        raise SystemExit("no perf samples parsed")

    print("measurement=perf samples inside no-PRESENT lower-bound gaps")
    print("perf_samples=%d gaps_ge_%.0fms=%d" %
          (len(samples), args.min_ms, len(gaps)))
    for rank, gap in enumerate(gaps[:args.top], 1):
        selected = [sample for sample in samples
                    if gap.start_tick_ms < sample["tick_ms"] <= gap.end_tick_ms]
        threads = collections.Counter(
            "%s/%d" % (sample["comm"], sample["tid"])
            for sample in selected)
        dsos = collections.Counter(
            os.path.basename(sample["dso"]) or sample["dso"]
            for sample in selected)
        marker, offset = present.preceding_marker(markers, gap.start_tick_ms)
        print("gap rank=%d start_tick_ms=%d lower_bound_ms=%.3f "
              "marker=%s offset_ms=%d samples=%d" %
              (rank, gap.start_tick_ms, gap.duration_ms, marker, offset,
               len(selected)))
        print("  threads " + compact_counter(threads, len(selected)))
        print("  dsos    " + compact_counter(dsos, len(selected)))


if __name__ == "__main__":
    main()

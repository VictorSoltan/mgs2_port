#!/usr/bin/env python3
"""Correlate external /proc activity with no-PRESENT lower-bound gaps."""

import argparse
import os

import dxvk_present_trace_analyze as present


def read_activity(path):
    rows = []
    proc_io = "unknown"
    with open(path, encoding="utf-8") as stream:
        for line in stream:
            if line.startswith("pid=") and "proc_io=" in line:
                proc_io = line.split("proc_io=", 1)[1].split()[0]
            fields = line.rstrip().split("\t")
            if len(fields) != 10 or not fields[0].isdigit():
                continue
            rows.append({
                "tick_ms": int(fields[1]),
                "elapsed_ms": float(fields[2]),
                "rchar": int(fields[3]),
                "read_bytes": int(fields[4]),
                "syscr": int(fields[5]),
                "minflt": int(fields[6]),
                "majflt": int(fields[7]),
                "utime": int(fields[8]),
                "stime": int(fields[9]),
            })
    return rows, proc_io


def sum_gap(rows, gap):
    selected = [row for row in rows
                if gap.start_tick_ms < row["tick_ms"] <= gap.end_tick_ms]
    totals = {key: sum(row[key] for row in selected)
              for key in ("rchar", "read_bytes", "syscr", "minflt", "majflt",
                          "utime", "stime")}
    totals["coverage_ms"] = sum(row["elapsed_ms"] for row in selected)
    return totals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("present_trace")
    parser.add_argument("activity_trace")
    parser.add_argument("--markers")
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()

    gaps = present.find_gaps(present.read_rows(args.present_trace))
    rows, proc_io = read_activity(args.activity_trace)
    markers = present.read_markers(args.markers)
    if not rows:
        raise SystemExit("no activity rows found")
    clock_ticks = os.sysconf("SC_CLK_TCK")
    print(f"clock_ticks_per_second={clock_ticks}")
    print(f"proc_io={proc_io}")
    print("rank\tstart_tick_ms\tlower_bound_ms\tmarker\toffset_ms\t"
          "activity_coverage_ms\tactivity_coverage_pct\t"
          "rchar\tread_bytes\tsyscr\tminflt\tmajflt\tcpu_ms\tcpu_one_core_pct")
    for rank, gap in enumerate(
            sorted(gaps, key=lambda value: value.duration_ms, reverse=True)
            [:args.top], 1):
        totals = sum_gap(rows, gap)
        cpu_ms = (totals["utime"] + totals["stime"]) * 1000.0 / clock_ticks
        cpu_pct = cpu_ms * 100.0 / gap.duration_ms
        marker, offset = present.preceding_marker(markers, gap.start_tick_ms)
        coverage_pct = 100.0 * totals["coverage_ms"] / gap.duration_ms
        covered = totals["coverage_ms"] > 0
        rchar = (str(totals["rchar"])
                 if proc_io == "available" and covered else "NA")
        read_bytes = (str(totals["read_bytes"])
                      if proc_io == "available" and covered else "NA")
        syscr = (str(totals["syscr"])
                 if proc_io == "available" and covered else "NA")
        minflt = str(totals["minflt"]) if covered else "NA"
        majflt = str(totals["majflt"]) if covered else "NA"
        cpu = "%.1f" % cpu_ms if covered else "NA"
        cpu_percent = "%.1f" % cpu_pct if covered else "NA"
        print(f"{rank}\t{gap.start_tick_ms}\t{gap.duration_ms:.3f}\t"
              f"{marker}\t{offset}\t{totals['coverage_ms']:.1f}\t"
              f"{coverage_pct:.1f}\t{rchar}\t{read_bytes}\t"
              f"{syscr}\t{minflt}\t{majflt}\t{cpu}\t{cpu_percent}")


if __name__ == "__main__":
    main()

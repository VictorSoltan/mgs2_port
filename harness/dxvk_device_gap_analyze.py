#!/usr/bin/env python3
"""Correlate RG353VS system pressure counters with no-PRESENT gaps."""

import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import dxvk_present_trace_analyze as present  # noqa: E402


def read_rows(path):
    with open(path, encoding="utf-8") as stream:
        metadata = stream.readline().strip()
        rows = []
        for raw in csv.DictReader(stream, delimiter="\t"):
            row = {}
            for key, value in raw.items():
                if key in ("elapsed_ms", "cpu_busy", "cpu0_busy", "cpu1_busy",
                           "cpu2_busy", "cpu3_busy"):
                    row[key] = float(value)
                else:
                    row[key] = int(value)
            rows.append(row)
    return metadata, rows


def total(rows, key):
    return sum(row[key] for row in rows)


def average(rows, key):
    return sum(row[key] for row in rows) / len(rows) if rows else 0.0


def pressure_percent(rows, key, duration_ms):
    return 0.0 if duration_ms <= 0 else total(rows, key) / (duration_ms * 10.0)


def mib(value):
    return value / (1024.0 * 1024.0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("present_trace")
    parser.add_argument("device_trace")
    parser.add_argument("--markers")
    parser.add_argument("--min-ms", type=float, default=200.0)
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()

    metadata, device_rows = read_rows(args.device_trace)
    gaps = [gap for gap in present.find_gaps(
        present.read_rows(args.present_trace))
            if gap.duration_ms >= args.min_ms]
    gaps.sort(key=lambda gap: gap.duration_ms, reverse=True)
    markers = present.read_markers(args.markers)
    if not device_rows:
        raise SystemExit("no device pressure rows parsed")

    print("measurement=external device pressure inside no-PRESENT lower-bound gaps")
    print(f"device_trace={metadata} gaps_ge_{args.min_ms:.0f}ms={len(gaps)}")
    for rank, gap in enumerate(gaps[:args.top], 1):
        rows = [row for row in device_rows
                if gap.start_tick_ms < row["tick_ms"] <= gap.end_tick_ms]
        marker, offset = present.preceding_marker(markers, gap.start_tick_ms)
        print("gap rank=%d start_tick_ms=%d lower_bound_ms=%.3f marker=%s "
              "offset_ms=%d samples=%d" %
              (rank, gap.start_tick_ms, gap.duration_ms, marker, offset, len(rows)))
        if not rows:
            continue
        print("  cpu avg=%.1f%% cores=%.1f/%.1f/%.1f/%.1f proc_ticks=%d+%d "
              "ctx=%d/%d" %
              (average(rows, "cpu_busy"), average(rows, "cpu0_busy"),
               average(rows, "cpu1_busy"), average(rows, "cpu2_busy"),
               average(rows, "cpu3_busy"), total(rows, "proc_utime"),
               total(rows, "proc_stime"), total(rows, "proc_voluntary"),
               total(rows, "proc_nonvoluntary")))
        print("  psi cpu_some=%.2f%% io_some/full=%.2f/%.2f%% "
              "mem_some/full=%.2f/%.2f%%" %
              (pressure_percent(rows, "psi_cpu_some_us", gap.duration_ms),
               pressure_percent(rows, "psi_io_some_us", gap.duration_ms),
               pressure_percent(rows, "psi_io_full_us", gap.duration_ms),
               pressure_percent(rows, "psi_mem_some_us", gap.duration_ms),
               pressure_percent(rows, "psi_mem_full_us", gap.duration_ms)))
        print("  faults minor=%d major=%d swap_in/out=%d/%d "
              "refault_anon/file=%d/%d oom=%d" %
              (total(rows, "proc_minflt"), total(rows, "proc_majflt"),
               total(rows, "vm_pswpin"), total(rows, "vm_pswpout"),
               total(rows, "vm_workingset_refault_anon"),
               total(rows, "vm_workingset_refault_file"),
               total(rows, "vm_oom_kill")))
        print("  proc_io rchar=%.3fMiB wchar=%.3fMiB read=%.3fMiB write=%.3fMiB "
              "rss_max=%dKiB swap_max=%dKiB" %
              (mib(total(rows, "proc_rchar")), mib(total(rows, "proc_wchar")),
               mib(total(rows, "proc_read_bytes")),
               mib(total(rows, "proc_write_bytes")),
               max(row["proc_rss_kb"] for row in rows),
               max(row["proc_vmswap_kb"] for row in rows)))
        print("  mmc read=%.3fMiB/%dms write=%.3fMiB/%dms io=%dms weighted=%dms "
              "in_flight_max=%d" %
              (total(rows, "block_read_sectors") / 2048.0,
               total(rows, "block_read_ms"),
               total(rows, "block_write_sectors") / 2048.0,
               total(rows, "block_write_ms"), total(rows, "block_io_ms"),
               total(rows, "block_weighted_ms"),
               max(row["block_in_flight"] for row in rows)))
        print("  memory available_min=%dKiB swap_free_min=%dKiB dirty_max=%dKiB "
              "writeback_max=%dKiB" %
              (min(row["mem_MemAvailable_kb"] for row in rows),
               min(row["mem_SwapFree_kb"] for row in rows),
               max(row["mem_Dirty_kb"] for row in rows),
               max(row["mem_Writeback_kb"] for row in rows)))
        print("  clocks cpu=%d..%dkHz gpu=%d..%dHz temp_max=%.1f/%.1fC" %
              (min(row["cpu_freq_khz"] for row in rows),
               max(row["cpu_freq_khz"] for row in rows),
               min(row["gpu_freq_hz"] for row in rows),
               max(row["gpu_freq_hz"] for row in rows),
               max(row["cpu_temp_mc"] for row in rows) / 1000.0,
               max(row["gpu_temp_mc"] for row in rows) / 1000.0))


if __name__ == "__main__":
    main()

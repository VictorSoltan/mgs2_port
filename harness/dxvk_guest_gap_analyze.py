#!/usr/bin/env python3
"""Resolve Box86 JIT samples inside measured DXVK frame gaps to x86 RVAs."""

import argparse
import bisect
import collections
import os

import dxvk_present_trace_analyze as present
import freeze_guest_read as guest


def read_jit_samples(path, tid=None):
    samples = []
    with open(path, encoding="utf-8", errors="replace") as stream:
        for line in stream:
            match = guest.LINE.match(line)
            if (not match or "perf-" not in match.group("dso")
                    or (tid is not None and int(match.group("tid")) != tid)):
                continue
            samples.append((int(float(match.group("t")) * 1000),
                            int(match.group("ip"), 16)))
    return samples


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("present_trace")
    parser.add_argument("perf_script")
    parser.add_argument("guest_map")
    parser.add_argument("maps")
    parser.add_argument("--markers")
    parser.add_argument("--min-ms", type=float, default=200.0)
    parser.add_argument("--top-gaps", type=int, default=20)
    parser.add_argument("--top-code", type=int, default=12)
    parser.add_argument("--bucket", type=lambda value: int(value, 0),
                        default=0x1000)
    parser.add_argument("--tid", type=int,
                        help="restrict JIT samples to one perf thread ID")
    args = parser.parse_args()

    records, overflow = guest.load_map(args.guest_map)
    starts = [record[0] for record in records]
    modules = guest.load_modules(args.maps)
    module_starts = [module[0] for module in modules]
    duplicate, overlap, reused = guest.map_invariants(records)
    maximum_size = max(record[1] for record in records)

    def owners(ip):
        found = []
        index = bisect.bisect_right(starts, ip) - 1
        while index >= 0 and starts[index] >= ip - maximum_size:
            record = records[index]
            if record[0] <= ip < record[0] + record[1]:
                found.append(record[2])
            index -= 1
        return set(found)

    def module_for(address):
        index = bisect.bisect_right(module_starts, address) - 1
        if index >= 0 and address < modules[index][1]:
            return modules[index]
        return None

    samples = read_jit_samples(args.perf_script, args.tid)
    gaps = [gap for gap in present.find_gaps(
        present.read_rows(args.present_trace))
            if gap.duration_ms >= args.min_ms]
    gaps.sort(key=lambda gap: gap.duration_ms, reverse=True)
    markers = present.read_markers(args.markers)

    print("guest_map_records=%d overflow=%d executable_mappings=%d" %
          (len(records), overflow, len(modules)))
    print("native_range_duplicate_starts=%d reused_for_different_guest=%d "
          "overlapping_neighbours=%d" % (duplicate, reused, overlap))
    print("jit_perf_samples=%d tid=%s gaps_ge_%.0fms=%d" %
          (len(samples), args.tid if args.tid is not None else "all",
           args.min_ms, len(gaps)))

    for rank, gap in enumerate(gaps[:args.top_gaps], 1):
        selected = [ip for tick, ip in samples
                    if gap.start_tick_ms < tick <= gap.end_tick_ms]
        hits = collections.Counter()
        module_hits = collections.Counter()
        unresolved = ambiguous = 0
        for ip in selected:
            owner = owners(ip)
            if not owner:
                unresolved += 1
                continue
            if len(owner) != 1:
                ambiguous += 1
                continue
            address = next(iter(owner))
            bucket = address & ~(args.bucket - 1)
            hits[bucket] += 1
            module = module_for(address)
            module_hits[module[2] if module else "(unmapped)"] += 1

        marker, offset = present.preceding_marker(markers, gap.start_tick_ms)
        resolved = len(selected) - unresolved - ambiguous
        print("gap rank=%d start_tick_ms=%d lower_bound_ms=%.3f "
              "marker=%s offset_ms=%d jit_samples=%d resolved=%d "
              "ambiguous=%d unresolved=%d" %
              (rank, gap.start_tick_ms, gap.duration_ms, marker, offset,
               len(selected), resolved, ambiguous, unresolved))
        if selected:
            print("  modules " + "; ".join(
                "%s=%d(%.1f%%)" %
                (os.path.basename(name), count, 100.0 * count / len(selected))
                for name, count in module_hits.most_common(5)))
            for address, count in hits.most_common(args.top_code):
                module = module_for(address)
                if module:
                    where = "%s+0x%x" % (
                        os.path.basename(module[2]), address - module[0])
                else:
                    where = "(unmapped)"
                print("  code 0x%08x %-44s %d(%.1f%%)" %
                      (address, where, count,
                       100.0 * count / len(selected)))


if __name__ == "__main__":
    main()

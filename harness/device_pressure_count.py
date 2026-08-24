#!/usr/bin/env python3
"""Bounded external RG353VS pressure sampler for PRESENT-gap correlation.

No game thread is instrumented.  Samples are retained in a fixed in-memory
list and written only when the reader finishes or receives TERM/INT, so the
sampler does not manufacture periodic storage writes while measuring I/O.
"""

import argparse
import os
import signal
import time


STOP = False
VMSTAT_KEYS = (
    "pgfault", "pgmajfault", "pswpin", "pswpout", "pgpgin", "pgpgout",
    "allocstall_dma", "allocstall_dma32", "allocstall_normal",
    "allocstall_movable", "workingset_refault_anon", "workingset_refault_file",
    "oom_kill",
)
MEMINFO_KEYS = ("MemAvailable", "SwapFree", "Dirty", "Writeback")


def stop(unused_signum, unused_frame):
    global STOP
    STOP = True


def read_text(path):
    with open(path, encoding="ascii") as stream:
        return stream.read()


def read_named_numbers(path):
    values = {}
    for line in read_text(path).splitlines():
        fields = line.split()
        if len(fields) >= 2:
            try:
                values[fields[0].rstrip(":")] = int(fields[1])
            except ValueError:
                pass
    return values


def read_pressure(kind):
    values = {}
    for line in read_text(f"/proc/pressure/{kind}").splitlines():
        fields = line.split()
        if not fields:
            continue
        for field in fields[1:]:
            if field.startswith("total="):
                values[fields[0]] = int(field.split("=", 1)[1])
    return values


def read_cpu():
    values = {}
    for line in read_text("/proc/stat").splitlines():
        fields = line.split()
        if not fields or fields[0] not in ("cpu", "cpu0", "cpu1", "cpu2", "cpu3"):
            continue
        ticks = [int(value) for value in fields[1:]]
        idle = ticks[3] + (ticks[4] if len(ticks) > 4 else 0)
        values[fields[0]] = (sum(ticks), idle)
    return values


def read_proc_stat(pid):
    text = read_text(f"/proc/{pid}/stat")
    fields = text[text.rfind(")") + 2:].split()
    return {
        "minflt": int(fields[7]),
        "majflt": int(fields[9]),
        "utime": int(fields[11]),
        "stime": int(fields[12]),
        "threads": int(fields[17]),
        "rss_kb": int(fields[21]) * (os.sysconf("SC_PAGE_SIZE") // 1024),
    }


def read_proc_status(pid):
    values = read_named_numbers(f"/proc/{pid}/status")
    return {
        "voluntary": values.get("voluntary_ctxt_switches", 0),
        "nonvoluntary": values.get("nonvoluntary_ctxt_switches", 0),
        "vmswap_kb": values.get("VmSwap", 0),
    }


def read_proc_io(pid):
    try:
        return read_named_numbers(f"/proc/{pid}/io")
    except FileNotFoundError:
        # ROCKNIX's kernel has no CONFIG_TASK_IO_ACCOUNTING /proc/PID/io.
        # Global mmc block counters below remain available and authoritative.
        return {key: 0 for key in ("rchar", "wchar", "read_bytes", "write_bytes")}


def read_block():
    fields = [int(value) for value in read_text("/sys/block/mmcblk0/stat").split()]
    return {
        "read_ios": fields[0],
        "read_sectors": fields[2],
        "read_ms": fields[3],
        "write_ios": fields[4],
        "write_sectors": fields[6],
        "write_ms": fields[7],
        "in_flight": fields[8],
        "io_ms": fields[9],
        "weighted_ms": fields[10],
    }


def read_int(path, default=-1):
    try:
        return int(read_text(path).strip())
    except (FileNotFoundError, ValueError):
        return default


def snapshot(pid):
    return {
        "cpu": read_cpu(),
        "psi_cpu": read_pressure("cpu"),
        "psi_io": read_pressure("io"),
        "psi_memory": read_pressure("memory"),
        "vmstat": read_named_numbers("/proc/vmstat"),
        "meminfo": read_named_numbers("/proc/meminfo"),
        "proc": read_proc_stat(pid),
        "status": read_proc_status(pid),
        "io": read_proc_io(pid),
        "block": read_block(),
        "cpu_freq": read_int("/sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq"),
        "gpu_freq": read_int("/sys/class/devfreq/fde60000.gpu/cur_freq"),
        "cpu_temp": read_int("/sys/class/thermal/thermal_zone0/temp"),
        "gpu_temp": read_int("/sys/class/thermal/thermal_zone1/temp"),
    }


def difference(current, previous, group, key):
    return current[group].get(key, 0) - previous[group].get(key, 0)


def cpu_percent(current, previous, name):
    current_total, current_idle = current["cpu"].get(name, (0, 0))
    previous_total, previous_idle = previous["cpu"].get(name, (0, 0))
    total = current_total - previous_total
    idle = current_idle - previous_idle
    return 0.0 if total <= 0 else 100.0 * (total - idle) / total


def make_row(window, tick_ns, elapsed_ms, current, previous):
    values = [window, tick_ns // 1_000_000, f"{elapsed_ms:.3f}"]
    values.extend(f"{cpu_percent(current, previous, name):.1f}"
                  for name in ("cpu", "cpu0", "cpu1", "cpu2", "cpu3"))
    for group, key in (
            ("psi_cpu", "some"),
            ("psi_io", "some"), ("psi_io", "full"),
            ("psi_memory", "some"), ("psi_memory", "full")):
        values.append(difference(current, previous, group, key))
    for key in ("minflt", "majflt", "utime", "stime"):
        values.append(difference(current, previous, "proc", key))
    values.extend((current["proc"]["rss_kb"], current["proc"]["threads"]))
    for key in ("voluntary", "nonvoluntary"):
        values.append(difference(current, previous, "status", key))
    values.append(current["status"]["vmswap_kb"])
    for key in ("rchar", "wchar", "read_bytes", "write_bytes"):
        values.append(difference(current, previous, "io", key))
    for key in ("read_ios", "read_sectors", "read_ms", "write_ios",
                "write_sectors", "write_ms", "io_ms", "weighted_ms"):
        values.append(difference(current, previous, "block", key))
    values.append(current["block"]["in_flight"])
    for key in VMSTAT_KEYS:
        values.append(difference(current, previous, "vmstat", key))
    for key in MEMINFO_KEYS:
        values.append(current["meminfo"].get(key, -1))
    values.extend((current["cpu_freq"], current["gpu_freq"],
                   current["cpu_temp"], current["gpu_temp"]))
    return values


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    parser.add_argument("--interval", type=float, default=0.1)
    parser.add_argument("--windows", type=int, default=2400)
    args = parser.parse_args()
    if args.interval <= 0 or args.windows <= 0:
        parser.error("--interval and --windows must be positive")

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    rows = []
    previous = snapshot(args.pid)
    previous_time = time.monotonic_ns()
    start_time = previous_time
    deadline = previous_time
    for window in range(1, args.windows + 1):
        if STOP:
            break
        deadline += int(args.interval * 1_000_000_000)
        delay = (deadline - time.monotonic_ns()) / 1_000_000_000
        if delay > 0:
            time.sleep(delay)
        now = time.monotonic_ns()
        try:
            current = snapshot(args.pid)
        except FileNotFoundError:
            break
        rows.append(make_row(window, now, (now - previous_time) / 1_000_000,
                             current, previous))
        previous = current
        previous_time = now

    columns = [
        "window", "tick_ms", "elapsed_ms", "cpu_busy", "cpu0_busy", "cpu1_busy",
        "cpu2_busy", "cpu3_busy", "psi_cpu_some_us", "psi_io_some_us",
        "psi_io_full_us", "psi_mem_some_us", "psi_mem_full_us", "proc_minflt",
        "proc_majflt", "proc_utime", "proc_stime", "proc_rss_kb", "proc_threads",
        "proc_voluntary", "proc_nonvoluntary", "proc_vmswap_kb", "proc_rchar",
        "proc_wchar", "proc_read_bytes", "proc_write_bytes", "block_read_ios",
        "block_read_sectors", "block_read_ms", "block_write_ios",
        "block_write_sectors", "block_write_ms", "block_io_ms", "block_weighted_ms",
        "block_in_flight",
    ]
    columns.extend("vm_" + key for key in VMSTAT_KEYS)
    columns.extend("mem_" + key + "_kb" for key in MEMINFO_KEYS)
    columns.extend(("cpu_freq_khz", "gpu_freq_hz", "cpu_temp_mc", "gpu_temp_mc"))
    print(f"pid={args.pid} interval={args.interval} rows={len(rows)} "
          f"start_tick_ms={start_time // 1_000_000}")
    print("\t".join(columns))
    for row in rows:
        print("\t".join(str(value) for value in row))


if __name__ == "__main__":
    main()

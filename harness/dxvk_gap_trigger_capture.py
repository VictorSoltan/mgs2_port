#!/usr/bin/env python3
"""Bounded, external thread snapshot when DXVK PRESENT stops advancing.

The game and Wine hot paths are untouched.  This reader polls the existing
memory-only D3D9 PRESENT counter and keeps all observations in RAM until it is
stopped.  For a long no-PRESENT interval it reads every thread's /proc stat
twice, then samples syscall/wchan only for the main thread and the few threads
which accumulated the most CPU ticks.  This avoids the broad wchan polling that
previously manufactured stalls.
"""

import argparse
import os
import signal
import struct
import time

import dxvk_present_count as present_count


STOP = False
NTSYNC_WAIT_ANY = 0xC0284E82
NTSYNC_WAIT_ALL = 0xC0284E83


def stop(unused_signum, unused_frame):
    global STOP
    STOP = True


def read_text(path):
    try:
        with open(path, encoding="ascii", errors="replace") as stream:
            return stream.read().strip()
    except OSError as error:
        return f"<{type(error).__name__}:{error.errno}>"


def task_stats(pid):
    result = {}
    try:
        tids = os.listdir(f"/proc/{pid}/task")
    except OSError:
        return result
    for name in tids:
        if not name.isdigit():
            continue
        raw = read_text(f"/proc/{pid}/task/{name}/stat")
        close = raw.rfind(")")
        if close < 0:
            continue
        fields = raw[close + 2:].split()
        try:
            result[int(name)] = {
                "comm": raw[raw.find("(") + 1:close],
                "state": fields[0],
                "minflt": int(fields[7]),
                "majflt": int(fields[9]),
                "utime": int(fields[11]),
                "stime": int(fields[12]),
            }
        except (IndexError, ValueError):
            continue
    return result


def stat_delta(current, previous, tid, key):
    if tid not in current or tid not in previous:
        return 0
    return current[tid][key] - previous[tid][key]


def ntsync_fds(pid):
    result = []
    try:
        names = sorted(os.listdir(f"/proc/{pid}/fd"), key=int)
    except OSError as error:
        return [f"unavailable:{type(error).__name__}:{error.errno}"]
    for name in names:
        try:
            target = os.readlink(f"/proc/{pid}/fd/{name}")
        except OSError:
            continue
        if "ntsync" in target.lower():
            result.append(f"{name}->{target}")
    return result


def decode_ntsync_wait(pid, syscall_text):
    try:
        fields = syscall_text.split()
        if len(fields) < 4 or int(fields[0], 0) != 54:  # compat ioctl
            return "not-ntsync-wait"
        request = int(fields[2], 0)
        if request not in (NTSYNC_WAIT_ANY, NTSYNC_WAIT_ALL):
            return f"ioctl={request:#x}"
        args_address = int(fields[3], 0)
        with open(f"/proc/{pid}/mem", "rb", buffering=0) as stream:
            stream.seek(args_address)
            raw = stream.read(40)
            timeout, objects_address, count, index, flags, owner, alert, unused = \
                struct.unpack("<QQIIIIII", raw)
            if count > 64:
                return f"invalid-count={count}"
            stream.seek(objects_address)
            objects_raw = stream.read(count * 4)
            objects = struct.unpack(f"<{count}I", objects_raw) if count else ()
        mapped = []
        for fd in objects:
            try:
                target = os.readlink(f"/proc/{pid}/fd/{fd}")
            except OSError as error:
                target = f"<{type(error).__name__}:{error.errno}>"
            mapped.append(f"{fd}:{target}")
        if timeout == 0xFFFFFFFFFFFFFFFF:
            timeout_text = "infinite"
        elif flags & 1:
            timeout_text = f"realtime_ns={timeout}"
        else:
            remaining_ms = timeout / 1_000_000 - time.monotonic_ns() / 1_000_000
            timeout_text = f"monotonic_ns={timeout},remaining_ms={remaining_ms:.3f}"
        kind = "WAIT_ANY" if request == NTSYNC_WAIT_ANY else "WAIT_ALL"
        return (f"{kind},timeout={timeout_text},count={count},index={index},"
                f"flags={flags:#x},owner={owner},alert={alert},"
                f"objects=[{','.join(mapped)}]")
    except (OSError, ValueError, IndexError, struct.error) as error:
        return f"decode-error:{type(error).__name__}:{getattr(error, 'errno', '')}"


def task_observation(pid, tid, current, previous):
    item = current.get(tid, {})
    syscall_text = read_text(f"/proc/{pid}/task/{tid}/syscall")
    return {
        "tid": tid,
        "comm": item.get("comm", "missing"),
        "state": item.get("state", "?"),
        "utime_delta": stat_delta(current, previous, tid, "utime"),
        "stime_delta": stat_delta(current, previous, tid, "stime"),
        "minflt_delta": stat_delta(current, previous, tid, "minflt"),
        "majflt_delta": stat_delta(current, previous, tid, "majflt"),
        "syscall": syscall_text,
        "wchan": read_text(f"/proc/{pid}/task/{tid}/wchan"),
        "ntsync": decode_ntsync_wait(pid, syscall_text),
    }


def probe_gap(pid, idle_ms, threshold_ms, probe_ms, top_threads):
    probe_start_ns = time.monotonic_ns()
    before = task_stats(pid)
    time.sleep(probe_ms / 1000.0)
    after = task_stats(pid)
    active = sorted(
        after,
        key=lambda tid: (
            stat_delta(after, before, tid, "utime")
            + stat_delta(after, before, tid, "stime"),
            -tid,
        ),
        reverse=True,
    )
    selected = [pid]
    selected.extend(tid for tid in active if tid != pid)
    selected = selected[:top_threads + 1]
    now_ns = time.monotonic_ns()
    return {
        "tick_ms": now_ns // 1_000_000,
        "idle_ms": idle_ms,
        "threshold_ms": threshold_ms,
        "probe_ms": (now_ns - probe_start_ns) / 1_000_000,
        "task_count": len(after),
        "tasks": [task_observation(pid, tid, after, before) for tid in selected],
    }


def print_results(metadata, fd_snapshot, gaps):
    print(metadata)
    print("ntsync_fds=" + (";".join(fd_snapshot) if fd_snapshot else "none"))
    for rank, gap in enumerate(gaps, 1):
        print(f"GAP rank={rank} start_tick_ms={gap['start_tick_ms']} "
              f"end_tick_ms={gap['end_tick_ms']} "
              f"lower_bound_ms={gap['duration_ms']:.3f} "
              f"present_delta={gap['present_delta']} probes={len(gap['probes'])}")
        for probe in gap["probes"]:
            print(f" PROBE tick_ms={probe['tick_ms']} idle_ms={probe['idle_ms']:.3f} "
                  f"threshold_ms={probe['threshold_ms']:.3f} "
                  f"probe_ms={probe['probe_ms']:.3f} tasks={probe['task_count']}")
            for task in probe["tasks"]:
                print(f"  TASK tid={task['tid']} comm={task['comm']} state={task['state']} "
                      f"cpu_ticks={task['utime_delta']}+{task['stime_delta']} "
                      f"faults={task['minflt_delta']}+{task['majflt_delta']} "
                      f"wchan={task['wchan']}")
                print(f"   syscall={task['syscall']}")
                print(f"   ntsync={task['ntsync']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    parser.add_argument("--interval", type=float, default=0.01)
    parser.add_argument("--windows", type=int, default=24000)
    parser.add_argument("--thresholds-ms", default="500,1200")
    parser.add_argument("--probe-ms", type=float, default=25.0)
    parser.add_argument("--top-threads", type=int, default=5)
    parser.add_argument("--max-gaps", type=int, default=12)
    args = parser.parse_args()
    if args.interval <= 0 or args.windows <= 0 or args.probe_ms <= 0:
        parser.error("interval, windows and probe-ms must be positive")
    if args.top_threads <= 0 or args.max_gaps <= 0:
        parser.error("top-threads and max-gaps must be positive")
    try:
        thresholds = sorted({float(value) for value in args.thresholds_ms.split(",")})
    except ValueError as error:
        raise SystemExit(f"invalid --thresholds-ms: {error}") from error
    if not thresholds or thresholds[0] <= 0:
        parser.error("thresholds must be positive")

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    base, module = present_count.module_base(args.pid)
    rva = present_count.exported_rva(module)
    address = base + rva
    memory = os.open(f"/proc/{args.pid}/mem", os.O_RDONLY)
    gaps = []
    active_gap = None
    fd_snapshot = ntsync_fds(args.pid)
    start_ns = time.monotonic_ns()
    metadata = (f"pid={args.pid} module={module} base={base:#x} rva={rva:#x} "
                f"interval={args.interval} thresholds_ms={args.thresholds_ms} "
                f"probe_ms={args.probe_ms} start_tick_ms={start_ns // 1_000_000}")
    try:
        previous = present_count.read_count(memory, address)
        last_present_ns = start_ns
        deadline = start_ns
        for unused_window in range(args.windows):
            if STOP:
                break
            deadline += int(args.interval * 1_000_000_000)
            delay = (deadline - time.monotonic_ns()) / 1_000_000_000
            if delay > 0:
                time.sleep(delay)
            now_ns = time.monotonic_ns()
            try:
                current = present_count.read_count(memory, address)
            except (OSError, RuntimeError):
                break
            delta = (current - previous) & 0xFFFFFFFF
            if delta:
                if active_gap is not None:
                    active_gap["end_tick_ms"] = now_ns // 1_000_000
                    active_gap["duration_ms"] = (now_ns - active_gap["start_ns"]) / 1_000_000
                    active_gap["present_delta"] = delta
                    gaps.append(active_gap)
                    active_gap = None
                previous = current
                last_present_ns = now_ns
                continue
            idle_ms = (now_ns - last_present_ns) / 1_000_000
            next_threshold = thresholds[0] if active_gap is None else active_gap["next_threshold"]
            if idle_ms < next_threshold or len(gaps) >= args.max_gaps:
                continue
            if active_gap is None:
                active_gap = {
                    "start_ns": last_present_ns,
                    "start_tick_ms": last_present_ns // 1_000_000,
                    "probes": [],
                    "threshold_index": 0,
                    "next_threshold": thresholds[0],
                }
            while (active_gap["threshold_index"] < len(thresholds)
                   and idle_ms >= thresholds[active_gap["threshold_index"]]):
                threshold = thresholds[active_gap["threshold_index"]]
                active_gap["probes"].append(probe_gap(
                    args.pid, idle_ms, threshold, args.probe_ms, args.top_threads))
                active_gap["threshold_index"] += 1
            if active_gap["threshold_index"] < len(thresholds):
                active_gap["next_threshold"] = thresholds[active_gap["threshold_index"]]
            else:
                active_gap["next_threshold"] = float("inf")
        if active_gap is not None:
            now_ns = time.monotonic_ns()
            active_gap["end_tick_ms"] = now_ns // 1_000_000
            active_gap["duration_ms"] = (now_ns - active_gap["start_ns"]) / 1_000_000
            active_gap["present_delta"] = 0
            gaps.append(active_gap)
    finally:
        os.close(memory)
    print_results(metadata, fd_snapshot, gaps[:args.max_gaps])


if __name__ == "__main__":
    main()

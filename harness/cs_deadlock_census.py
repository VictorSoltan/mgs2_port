#!/usr/bin/env python3
"""Diagnose a WineD3D CS freeze: published work with a sleeping consumer, or not.

The freeze leaves wined3d_cs asleep and the main thread on a timed wait. Two
different faults look identical at that level:

  A  work is published and the consumer is not running it
  B  the queues are empty and the consumer is asleep correctly, so the fault is
     somewhere else -- most likely whatever the main thread waits for in ntsync

WHY THIS IS NOT A ONE-SHOT TEST. An earlier version decided on `head != tail`
alone and would have declared A on a perfectly healthy game: a running consumer
routinely has a non-empty queue. Proof from this project's own handoff, taken
from a live, working process:

    DEFAULT head 0x59cbca0  tail 0x59c99e4   NOT EMPTY
    waiting_for_event 0

`head != tail` means "there is work", not "the consumer is stuck". Wine only
sleeps after setting waiting_for_event, re-checking both queues and cancelling
the sleep if it finds work, so a stuck consumer must show ALL of:

    the CS thread actually blocked in a futex wait
    waiting_for_event == 1
    head != tail
    head, tail, the execute counter and the event ring all unchanged
    across several samples

Anything less is INDETERMINATE, which is a better answer than a confident wrong
one. The census publishes the live cs pointer and the field offsets, so this
needs no debug info.

WHEN THE CS THREAD CANNOT BE NAMED. `comm` is "wined3d_cs" only while Wine has
set the thread name; a capture on 2026-08-19 found every task in the process
called `mgs2_sse_rg353v`, so the match failed, `wchan` came back None, and the
tool printed INDETERMINATE over a process that was demonstrably not running --
the queue was non-empty, nothing advanced, and the whole process consumed zero
CPU. Losing a capture to a naming heuristic is not acceptable, so there is now a
fallback witness: the summed CPU time of every task, read from /proc across the
same sample window. It is independent of the census -- different producer, other
side of the emulator -- which is what a control here has to be.

usage: cs_deadlock_census.py [--pid N] [--samples 5] [--interval 0.2]
"""
import argparse
import os
import struct
import sys
import time

MAGIC = 0x32355250  # PR52
IMAGE_BASE = 0x10000000
VERSION = 1
SIZE_WORDS = 0x214
RING = 64

EVENTS = {1: "SUBMIT", 2: "ALERT", 3: "WAIT_PREPARE",
          4: "WAIT_ABORT_NONEMPTY", 5: "WAIT_ENTER", 6: "WAIT_RETURN"}

HEAD = struct.Struct("<5I 7I 7I I")
ENTRY = struct.Struct("<8I")


def find_pid(comm="mgs2_sse_rg353v"):
    hits = [int(n) for n in os.listdir("/proc") if n.isdigit()
            and _comm(f"/proc/{n}") == comm]
    if len(hits) != 1:
        raise RuntimeError(f"expected one {comm!r}, found {hits}")
    return hits[0]


def _comm(path):
    try:
        with open(path + "/comm") as s:
            return s.read().strip()
    except OSError:
        return None


def cs_thread(pid):
    """The Linux tid of the CS thread, and whether it is blocked in futex.

    cs->thread_id is a Win32 id, not a tid, so match on comm instead."""
    base = f"/proc/{pid}/task"
    for tid in os.listdir(base):
        if _comm(f"{base}/{tid}") == "wined3d_cs":
            try:
                wchan = open(f"{base}/{tid}/wchan").read().strip()
                sc = open(f"{base}/{tid}/syscall").read().split()
            except OSError:
                return tid, None, None
            return tid, wchan, (sc[0] if sc else None)
    return None, None, None


def process_cpu(pid):
    """Summed utime+stime of every task, in clock ticks.

    The independent witness for "this process is not running". Reading it once
    before and once after the sample window is two reads of a counter, not the
    per-thread wchan sampling that amplified the freezes it was measuring in
    August -- see rule 2 in AGENTS.md.
    """
    total = 0
    base = f"/proc/{pid}/task"
    for tid in os.listdir(base):
        try:
            with open(f"{base}/{tid}/stat") as s:
                f = s.read().rsplit(") ", 1)[-1].split()
            total += int(f[11]) + int(f[12])   # utime, stime after the comm field
        except (OSError, IndexError, ValueError):
            continue
    return total


def task_table(pid):
    """comm and wchan for every task. Only for the already-stopped process."""
    rows = []
    base = f"/proc/{pid}/task"
    for tid in sorted(os.listdir(base), key=int):
        try:
            wchan = open(f"{base}/{tid}/wchan").read().strip()
        except OSError:
            wchan = "?"
        rows.append((tid, _comm(f"{base}/{tid}") or "?", wchan))
    return rows


def module_mappings(pid, module="wined3d.dll"):
    """Return readable mappings of the loaded WineD3D image.

    The census is a writable data object, so its RVA legitimately moves between
    production DLLs.  Searching the module mapping by its self-describing
    header is safer than preserving a VMA from an older build.
    """
    mappings = []
    with open(f"/proc/{pid}/maps") as s:
        for line in s:
            f = line.split()
            if len(f) >= 6 and "r" in f[1] and f[-1].endswith(module):
                start, end = (int(v, 16) for v in f[0].split("-", 1))
                mappings.append((start, end))
    if not mappings:
        raise RuntimeError(f"no readable mapping for {module}")
    return mappings


def module_base(pid, module="wined3d.dll"):
    """Return the PE image base for an explicit legacy --vma override."""
    with open(f"/proc/{pid}/maps") as s:
        for line in s:
            f = line.split()
            if len(f) >= 6 and f[2] == "00000000" and f[-1].endswith(module):
                return int(f[0].split("-", 1)[0], 16)
    raise RuntimeError(f"no offset-zero mapping for {module}")


def find_census(fd, mappings):
    """Find the unique PR52 v1 / 0x214-word public census header."""
    needle = struct.pack("<I", MAGIC)
    matches = []
    chunk_size = 64 * 1024

    for start, end in mappings:
        pos, tail = start, b""
        while pos < end:
            data = os.pread(fd, min(chunk_size, end - pos), pos)
            if not data:
                break
            window = tail + data
            scan = 0
            while True:
                found = window.find(needle, scan)
                if found < 0:
                    break
                addr = pos - len(tail) + found
                try:
                    head = HEAD.unpack(os.pread(fd, HEAD.size, addr))
                except struct.error:
                    scan = found + 1
                    continue
                magic, version, size_words, signature = head[:4]
                if (magic == MAGIC and version == VERSION and size_words == SIZE_WORDS
                        and signature == (~MAGIC & 0xffffffff)):
                    matches.append(addr)
                scan = found + 1
            tail = window[-3:]
            pos += len(data)

    if len(matches) != 1:
        raise RuntimeError(f"expected one PR52 census header, found {len(matches)}")
    return matches[0]


def sample(fd, addr):
    head = HEAD.unpack(os.pread(fd, HEAD.size, addr))
    (magic, version, size_words, signature, enabled) = head[0:5]
    if magic != MAGIC or signature != (~MAGIC & 0xFFFFFFFF):
        raise RuntimeError(f"census signature mismatch (magic={magic:#x})")
    (cs_ptr, off_dh, off_dt, off_mh, off_mt, off_wfe, off_tid) = head[5:12]
    counters = head[12:19]
    ring_write = head[19]

    def u32(a):
        return struct.unpack("<I", os.pread(fd, 4, a))[0]

    live = None
    if cs_ptr:
        live = dict(dh=u32(cs_ptr + off_dh), dt=u32(cs_ptr + off_dt),
                    mh=u32(cs_ptr + off_mh), mt=u32(cs_ptr + off_mt),
                    wfe=u32(cs_ptr + off_wfe), tid=u32(cs_ptr + off_tid))
    return dict(enabled=enabled, cs_ptr=cs_ptr, counters=counters,
                ring_write=ring_write, live=live, addr=addr, off=head[5:12])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pid", type=int)
    ap.add_argument("--vma", type=lambda s: int(s, 0),
                    help="legacy PE VMA override; normally auto-discovered")
    ap.add_argument("--samples", type=int, default=5)
    ap.add_argument("--interval", type=float, default=0.2)
    args = ap.parse_args()

    pid = args.pid or find_pid()
    fd = os.open(f"/proc/{pid}/mem", os.O_RDONLY)
    try:
        addr = (module_base(pid) + args.vma - IMAGE_BASE if args.vma is not None
                else find_census(fd, module_mappings(pid)))
    except Exception:
        os.close(fd)
        raise

    cpu_before = process_cpu(pid)
    shots = []
    for i in range(args.samples):
        shots.append(sample(fd, addr))
        if i + 1 < args.samples:
            time.sleep(args.interval)
    cpu_ticks = process_cpu(pid) - cpu_before

    first, last = shots[0], shots[-1]
    if not first["enabled"]:
        sys.exit("census never armed -- set MGS2_CS_DEADLOCK_CENSUS=1 for the run")
    if not first["cs_ptr"]:
        sys.exit("cs pointer not published -- the CS never ran")

    (submits, alerts, executes, wait_prep, wait_enter, wait_ret, wait_abort) = last["counters"]
    print(f"submits {submits}  alerts {alerts}  executes {executes}")
    print(f"wait: prepare {wait_prep}  enter {wait_enter}  return {wait_ret}"
          f"  abort-nonempty {wait_abort}")
    print(f"cs at {first['cs_ptr']:#x}\n")

    tid, wchan, syscall_no = cs_thread(pid)
    lv = last["live"]
    print(f"wined3d_cs tid {tid}  wchan {wchan}  syscall {syscall_no}")
    print(f"  DEFAULT head {lv['dh']:#x} tail {lv['dt']:#x}"
          f"   {'NOT EMPTY' if lv['dh'] != lv['dt'] else 'empty'}")
    print(f"  MAP     head {lv['mh']:#x} tail {lv['mt']:#x}"
          f"   {'NOT EMPTY' if lv['mh'] != lv['mt'] else 'empty'}")
    print(f"  waiting_for_event {lv['wfe']}\n")

    # stability across the whole sample set
    def stable(key):
        return len({s["live"][key] for s in shots}) == 1

    exec_stable = len({s["counters"][2] for s in shots}) == 1
    ring_stable = len({s["ring_write"] for s in shots}) == 1
    queue_stable = all(stable(k) for k in ("dh", "dt", "mh", "mt"))
    wfe_stable = stable("wfe")
    asleep = wchan is not None and wchan.startswith("__futex")
    no_cpu = cpu_ticks == 0

    span = args.interval * (args.samples - 1)
    print(f"stability over {args.samples} samples / {span:.1f}s:")
    print(f"  executes {'unchanged' if exec_stable else 'ADVANCING'}"
          f"   ring {'unchanged' if ring_stable else 'ADVANCING'}"
          f"   queue {'unchanged' if queue_stable else 'ADVANCING'}"
          f"   waiting_for_event {'unchanged' if wfe_stable else 'ADVANCING'}")
    print(f"  CS thread {'blocked in futex' if asleep else 'NOT blocked (wchan ' + str(wchan) + ')'}")
    print(f"  process CPU over the window: {cpu_ticks} ticks"
          f"   ({'no task ran at all' if no_cpu else 'something is running'})")
    if tid is None:
        # The comm heuristic missed. Say so, name every task once, and fall back
        # to the CPU witness rather than throwing the capture away.
        print("  CS thread not identified by comm; using the process CPU witness."
              " Tasks at this moment:")
        for t, comm, wc in task_table(pid):
            print(f"      {t:<8} {comm:<16} {wc}")
    print()

    print(f"last {min(last['ring_write'], RING)} sync events, oldest first:")
    start = max(0, last["ring_write"] - RING)
    for i in range(start, last["ring_write"]):
        e = ENTRY.unpack(os.pread(fd, ENTRY.size,
                                  addr + HEAD.size + (i % RING) * ENTRY.size))
        ev, thread, ex, edh, edt, emh, emt, ewfe = e
        print(f"  {EVENTS.get(ev, ev):<20} tid {thread:#7x} exec {ex:<9}"
              f" D {edh:#x}/{edt:#x} M {emh:#x}/{emt:#x} wfe {ewfe}")

    # Either witness will do for "nothing is advancing": the named CS thread
    # parked in a futex, or -- when the name is missing -- no task in the whole
    # process having consumed a single tick. The counter checks are required in
    # both cases, so a busy process still reads as INDETERMINATE.
    stopped = asleep or (tid is None and no_cpu)
    frozen = stopped and exec_stable and ring_stable and queue_stable and wfe_stable
    nonempty = lv["dh"] != lv["dt"] or lv["mh"] != lv["mt"]

    print()
    if not frozen:
        print("VERDICT INDETERMINATE: this process is still making progress, or")
        print("the CS thread is not blocked. A non-empty queue is NORMAL while the")
        print("consumer is running -- do not read it as a stuck consumer. Re-run")
        print("this while the game is actually frozen.")
        rc = 2
    elif not lv["wfe"] and nonempty:
        print("VERDICT C: nothing advances, the DEFAULT queue holds published work,")
        print("and waiting_for_event is 0 -- so the consumer did NOT stop in the")
        print("wined3d wait path, and with no task consuming CPU this is not a")
        print("livelock either. It stopped somewhere inside command execution.")
        print("Suspect whatever that run routed differently -- an armed island")
        print("entry first, since a native function holding a lock the guest half")
        print("of the process expects to release looks exactly like this.")
        rc = 3
    elif not lv["wfe"]:
        print("VERDICT INDETERMINATE: everything is stable and the CS thread is")
        print("blocked, but waiting_for_event is 0, so it did not stop in the")
        print("wined3d wait path. It is parked on something else; find out what")
        print("before blaming the CS handshake.")
        rc = 2
    elif nonempty:
        print("VERDICT A: stable non-empty queue with a sleeping consumer that")
        print("did set waiting_for_event. Work is published and not being run.")
        print("The submit/alert handshake is the suspect, and Box86's atomics on")
        print("that path with it.")
        rc = 0
    else:
        print("VERDICT B: both queues stably empty and the consumer asleep with")
        print("waiting_for_event set. The CS is behaving correctly and this is")
        print("NOT a missed publication. Move to what the main thread is waiting")
        print("for in ntsync.")
        rc = 1
    os.close(fd)
    return rc


if __name__ == "__main__":
    sys.exit(main())

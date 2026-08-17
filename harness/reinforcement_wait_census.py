#!/usr/bin/env python3
"""Read the bounded MGS2 renderer-wait census (patch 39).

Splits the CSMT consumer thread into exec / present / idle, so the 0.671-core
reading from frame_limit_probe.py can be separated into real work, GPU
round-trip, and spinning on an empty queue.  Memory-only in the process; this
reader takes a coherent snapshot through /proc/<pid>/mem and never writes.
"""

import argparse
import json
import os
import struct

MAGIC = 0x39335250  # PR39
VERSION = 1
IMAGE_BASE = 0x10000000
HEADER_NAMES = "magic version size_words signature enabled publish_sequence".split()
HEADER = struct.Struct(f"<{len(HEADER_NAMES)}I")
BUCKETS = ("<1ms", "1-2ms", "2-4ms", "4-8ms", "8-16ms", "16-32ms", "32-64ms", "64ms+")
LAYOUT = (
    ("presents", 1), ("idle_episodes", 1), ("spin_iterations", 1),
    ("wait_event_calls", 1), ("packets", 1),
    ("present_us", 1), ("idle_us", 1), ("exec_us", 1), ("wall_us", 1),
    ("present_hist", 8), ("idle_hist", 8),
)
PAYLOAD_WORDS = sum(n for _n, n in LAYOUT)
PAYLOAD = struct.Struct(f"<{PAYLOAD_WORDS}I")


def unpack(raw):
    v = PAYLOAD.unpack(raw)
    out, pos = {}, 0
    for name, count in LAYOUT:
        out[name] = v[pos] if count == 1 else dict(zip(BUCKETS, v[pos:pos + count]))
        pos += count
    return out


def find_pid(comm):
    # Processes come and go while /proc is being walked, so a disappearing pid
    # is normal and must not abort the read.
    m = []
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        try:
            with open(f"/proc/{name}/comm", encoding="ascii") as stream:
                if stream.read().strip() == comm:
                    m.append(int(name))
        except OSError:
            pass
    if len(m) != 1:
        raise SystemExit(f"expected one {comm!r}, found {m}")
    return m[0]


def module_base(pid, module):
    for line in open(f"/proc/{pid}/maps", encoding="ascii"):
        f = line.split()
        if len(f) >= 6 and f[2] == "00000000" and f[-1].endswith(module):
            return int(f[0].split("-", 1)[0], 16)
    raise SystemExit(f"offset-zero mapping for {module!r} not found")


def snapshot(pid, module, vma):
    addr = module_base(pid, module) + vma - IMAGE_BASE
    fd = os.open(f"/proc/{pid}/mem", os.O_RDONLY)
    try:
        for _ in range(20):
            h = dict(zip(HEADER_NAMES, HEADER.unpack(os.pread(fd, HEADER.size, addr))))
            if h["magic"] != MAGIC or h["signature"] != ((~MAGIC) & 0xFFFFFFFF):
                raise SystemExit(f"bad PR39 signature at {addr:#x}: {h}")
            want = (HEADER.size + PAYLOAD.size) // 4
            if h["version"] != VERSION or h["size_words"] != want:
                raise SystemExit(f"unsupported PR39 layout: {h}, reader wants {want}")
            if h["publish_sequence"] & 1:
                continue
            body = os.pread(fd, PAYLOAD.size, addr + HEADER.size)
            h2 = dict(zip(HEADER_NAMES, HEADER.unpack(os.pread(fd, HEADER.size, addr))))
            if h2["publish_sequence"] == h["publish_sequence"]:
                return {"pid": pid, "address": hex(addr), "enabled": bool(h["enabled"]),
                        "publish_sequence": h["publish_sequence"], "counters": unpack(body)}
        raise SystemExit("census never quiesced")
    finally:
        os.close(fd)


def report(delta):
    """Interpretation rule, fixed before the numbers are read."""
    f = delta["presents"] or 1
    wall = delta["wall_us"] or 1
    out = {
        "presents": delta["presents"],
        "frame_ms": round(wall / f / 1000, 2),
        "present_ms_per_frame": round(delta["present_us"] / f / 1000, 2),
        "idle_ms_per_frame": round(delta["idle_us"] / f / 1000, 2),
        "exec_ms_per_frame": round(delta["exec_us"] / f / 1000, 2),
        "present_share": round(delta["present_us"] / wall, 4),
        "idle_share": round(delta["idle_us"] / wall, 4),
        "exec_share": round(delta["exec_us"] / wall, 4),
        "spin_per_frame": round(delta["spin_iterations"] / f, 1),
        "idle_episodes_per_frame": round(delta["idle_episodes"] / f, 1),
        "wait_event_per_frame": round(delta["wait_event_calls"] / f, 2),
        "packets_per_frame": round(delta["packets"] / f, 1),
    }
    v = []
    if out["present_share"] > 0.25:
        v.append(f"GPU ROUND-TRIP: {out['present_ms_per_frame']} ms of a "
                 f"{out['frame_ms']} ms frame is inside the present handler. "
                 f"Overlapping it is the candidate; it costs no thermal budget.")
    if out["idle_share"] > 0.25:
        v.append(f"PRODUCER STARVATION: the renderer waits {out['idle_ms_per_frame']} ms "
                 f"per frame on an empty queue. The game thread, not the renderer, "
                 f"sets the frame. Renderer optimisation cannot help.")
    if out["exec_share"] > 0.6:
        v.append(f"RENDERER WORK: {out['exec_ms_per_frame']} ms/frame is real execution. "
                 f"A native ARM bridge for the hottest WineD3D path has a target.")
    if not v:
        v.append("no single account dominates; report the split as measured")
    out["verdict"] = v
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--comm", default="mgs2_sse_rg353v")
    ap.add_argument("--pid", type=int)
    ap.add_argument("--module", default="wined3d.dll")
    ap.add_argument("--symbol-vma", type=lambda v: int(v, 0), default=0x101d30c0)
    ap.add_argument("--output")
    ap.add_argument("--diff", nargs=2, metavar=("BEFORE", "AFTER"))
    a = ap.parse_args()

    if a.diff:
        before = json.load(open(a.diff[0]))
        after = json.load(open(a.diff[1]))
        if before["pid"] != after["pid"]:
            raise SystemExit("before/after are different processes")
        delta = {}
        for name, count in LAYOUT:
            if count == 1:
                delta[name] = after["counters"][name] - before["counters"][name]
            else:
                delta[name] = {k: after["counters"][name][k] - before["counters"][name][k]
                               for k in after["counters"][name]}
        print(json.dumps({"delta": delta, "derived": report(delta)},
                         indent=2, sort_keys=True))
        return

    pid = a.pid or find_pid(a.comm)
    rep = snapshot(pid, a.module, a.symbol_vma)
    text = json.dumps(rep, indent=2, sort_keys=True)
    if a.output:
        open(a.output, "w", encoding="ascii").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()

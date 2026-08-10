#!/usr/bin/env python3
"""Inspect Wine DirectSound buffers owned by the active DirectMusic synth.

This is an out-of-process, read-only snapshot.  It is intentionally specific to
the 32-bit diagnostic dsound/dmsynth builds shipped by this port; keeping all
offsets here makes the diagnosis reproducible without logging from audio
threads.
"""

import argparse
import json
import os
import struct
import sys


DMSYNTH_STATE_RVA = 0x3BEA8


def read_exact(fd, address, size):
    data = os.pread(fd, size, address)
    if len(data) != size:
        raise RuntimeError(f"short read at {address:#x}: {len(data)} of {size}")
    return data


def u32(fd, address):
    return struct.unpack("<I", read_exact(fd, address, 4))[0]


def s32(fd, address):
    return struct.unpack("<i", read_exact(fd, address, 4))[0]


def module_base(pid, needle):
    with open(f"/proc/{pid}/maps", encoding="ascii") as stream:
        for line in stream:
            fields = line.split()
            if (
                len(fields) >= 6
                and fields[1].startswith("r-x")
                and fields[2] == "00000000"
                and needle in fields[-1]
            ):
                return int(fields[0].split("-", 1)[0], 16)
    raise RuntimeError(f"module {needle!r} not found")


def pcm_stats(raw, bits, channels):
    if bits == 16:
        count = len(raw) // 2
        samples = struct.unpack(f"<{count}h", raw[: count * 2])
        absolute = [abs(value) for value in samples]
        return {
            "samples": count,
            "nonzero": sum(value != 0 for value in samples),
            "peak": max(absolute, default=0),
            "mean_abs": round(sum(absolute) / count, 2) if count else 0,
            "channels": channels,
        }
    if bits == 8:
        absolute = [abs(value - 128) for value in raw]
        return {
            "samples": len(raw),
            "nonzero": sum(value != 128 for value in raw),
            "peak": max(absolute, default=0),
            "mean_abs": round(sum(absolute) / len(raw), 2) if raw else 0,
            "channels": channels,
        }
    return {"bytes": len(raw), "unsupported_bits": bits, "channels": channels}


def inspect(pid):
    dmsynth_base = module_base(pid, "dmsynth.dll")
    fd = os.open(f"/proc/{pid}/mem", os.O_RDONLY)
    try:
        state = dmsynth_base + DMSYNTH_STATE_RVA
        if u32(fd, state) != 0x31545344:
            raise RuntimeError(f"dmsynth state signature missing at {state:#x}")
        synth = u32(fd, state + 17 * 4)
        sink = u32(fd, synth + 372)
        fluid = u32(fd, synth + 448)
        midi_channels = u32(fd, fluid + 64)
        channel_array = u32(fd, fluid + 152)
        dsound_iface = u32(fd, sink + 24)
        dsound_impl = dsound_iface - 4
        device = u32(fd, dsound_impl + 24)
        count = u32(fd, device + 164)
        array = u32(fd, device + 168)
        if count > 4096:
            raise RuntimeError(f"implausible DirectSound buffer count {count}")

        result = {
            "pid": pid,
            "dmsynth_base": hex(dmsynth_base),
            "synth": hex(synth),
            "fluid_synth": hex(fluid),
            "midi_channels": [],
            "sink": hex(sink),
            "sink_state": {
                "external_buffer": hex(u32(fd, sink + 28)),
                "active": bool(u32(fd, sink + 32)),
                # On i386 the 64-bit fields are eight-byte aligned.  The
                # release object's actual offsets are 88/92/112/132/140/144;
                # +68 reads the latency timestamp and +136 reads meter_tick.
                "play_pos": u32(fd, sink + 88),
                "write_pos": u32(fd, sink + 92),
                "written": u32(fd, sink + 112),
                "meter_peak": s32(fd, sink + 132),
                "meter_blocks": u32(fd, sink + 140),
                "meter_nonzero": u32(fd, sink + 144),
            },
            "dsound": {
                "interface": hex(dsound_iface),
                "device": hex(device),
                "device_stopped": bool(u32(fd, device + 160)),
                "buffer_count": count,
            },
            "buffers": [],
        }

        channel_pointers = struct.unpack(
            f"<{midi_channels}I", read_exact(fd, channel_array, midi_channels * 4)
        )
        for index, channel in enumerate(channel_pointers):
            cc = read_exact(fd, channel + 60, 128)
            result["midi_channels"].append({
                "channel": index,
                "volume": cc[7],
                "expression": cc[11],
                "bank_msb": cc[0],
                "bank_lsb": cc[32],
                "pan": cc[10],
            })

        pointers = struct.unpack(f"<{count}I", read_exact(fd, array, count * 4)) if count else ()
        for index, buffer in enumerate(pointers):
            try:
                pwfx = u32(fd, buffer + 48)
                memory_obj = u32(fd, buffer + 52)
                buflen = u32(fd, buffer + 72)
                fmt = read_exact(fd, pwfx, 18)
                tag, channels, rate, avg_bytes, align, bits, extra = struct.unpack("<HHIIHHH", fmt)
                memory = u32(fd, memory_obj + 368) if memory_obj else 0
                item = {
                    "index": index,
                    "address": hex(buffer),
                    "state": u32(fd, buffer + 60),
                    "playflags": hex(u32(fd, buffer + 56)),
                    "volume": s32(fd, buffer + 104),
                    "pan": s32(fd, buffer + 108),
                    "buflen": buflen,
                    "sec_mixpos": u32(fd, buffer + 184),
                    "format": {
                        "tag": tag,
                        "channels": channels,
                        "rate": rate,
                        "avg_bytes": avg_bytes,
                        "align": align,
                        "bits": bits,
                        "extra": extra,
                    },
                    "memory": hex(memory),
                }
                if memory and 0 < buflen <= 16 * 1024 * 1024:
                    item["pcm"] = pcm_stats(read_exact(fd, memory, buflen), bits, channels)
            except (OSError, RuntimeError, struct.error) as error:
                # The game's secondary-buffer pool changes while this external
                # reader runs. A stale entry must not discard the stable synth,
                # controller and other-buffer evidence from the same snapshot.
                item = {
                    "index": index,
                    "address": hex(buffer),
                    "error": str(error),
                }
            result["buffers"].append(item)
        return result
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    args = parser.parse_args()
    try:
        print(json.dumps(inspect(args.pid), indent=2))
    except (OSError, RuntimeError, struct.error) as error:
        print(f"dsound_live_state: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()

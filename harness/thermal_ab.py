#!/usr/bin/env python3
"""Thermal A/B sampler: battery vs charger, one fixed scene.

Answers the question left open by brief #29 and reframed by #30: on this unit the
kernel's own thermal governor trips at 83 C (thermal_zone0 trip_point_0, policy
step_wise, driving cooling_device0 = cpufreq-cpu0 through 7 states), which is
*below* the launcher guard's TEMP_DOWN of 84. So the frequency is limited by two
independent throttlers, and only one of them is ours. Recording scaling_max_freq
alone therefore reports the guard's opinion, not the clock the game actually got.

This samples both, plus the cooling state and the charger, once a second. It does
NOT walk per-thread stats and never reads wchan: an external sampler that read
wchan for fifty threads amplified the very freezes it was measuring, and a
per-second census from a hot thread has cost this project days more than once.
Reading eight sysfs files a second is the cheapest thing that answers this.

Frame rate is not sampled here -- it comes from the game's own presenter via
MGS2_GL_STATS, which is the designed channel. Run the game with:

    WINEDEBUG="-all,err+waylanddrv" MGS2_GL_STATS=300

and pass that log to --fps-log so the two streams line up by timestamp.

Do not pin the clock for this test. MGS2_FREQ_STEPS exists to make an A/B fair
when the *variable* is something else; here the cap is the thing being measured.

Usage, on the device, with the game already at the fixed spot and standing still:

    python3 thermal_ab.py --label battery --seconds 90 > battery.csv
"""

import argparse
import os
import sys
import time

ZONE0 = "/sys/class/thermal/thermal_zone0"
ZONE1 = "/sys/class/thermal/thermal_zone1"
CPU0 = "/sys/devices/system/cpu/cpu0/cpufreq"
COOL0 = "/sys/class/thermal/cooling_device0"
COOL1 = "/sys/class/thermal/cooling_device1"


def read(path, default=""):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return default


def read_int(path, default=0):
    v = read(path)
    try:
        return int(v)
    except ValueError:
        return default


def game_pid():
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        # comm, not the command line: the command line also matches gptokeyb and
        # the shell doing the matching. Wine truncates comm to 15 characters.
        if read("/proc/%s/comm" % entry) == "mgs2_sse_rg353v":
            return entry
    return None


def charger_online():
    for name in os.listdir("/sys/class/power_supply"):
        online = read("/sys/class/power_supply/%s/online" % name)
        if online in ("0", "1"):
            return online
    return "?"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, help="battery | charger | free text")
    ap.add_argument("--seconds", type=int, default=90)
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("--fps-log", default="", help="launcher log carrying MGS2_GL_STATS lines")
    args = ap.parse_args()

    pid = game_pid()
    if not pid:
        sys.stderr.write("no game process (comm=mgs2_sse_rg353v); start it first\n")
        return 1

    fps_fh = None
    if args.fps_log:
        try:
            fps_fh = open(args.fps_log, "r", errors="replace")
            fps_fh.seek(0, os.SEEK_END)  # only lines produced during this window
        except OSError as exc:
            sys.stderr.write("cannot follow fps log: %s\n" % exc)

    print("# label=%s pid=%s seconds=%d" % (args.label, pid, args.seconds))
    print("# cpu_max is the guard's cap; cool0 is the kernel's own limiter (0=off)")
    print("t,label,cpu_c,gpu_c,cpu_cur_khz,cpu_max_khz,cool0,cool0_max,cool1,charger,fps")

    start = time.time()
    while time.time() - start < args.seconds:
        # Drain any fps lines the presenter emitted since the last sample so the
        # frame rate lands on the row whose temperature produced it.
        fps = ""
        if fps_fh:
            for line in fps_fh:
                if "fps" in line.lower():
                    fps = line.strip().replace(",", ";")[:120]

        if not os.path.exists("/proc/%s" % pid):
            sys.stderr.write("game exited at t+%.0fs\n" % (time.time() - start))
            break

        print("%.1f,%s,%.1f,%.1f,%s,%s,%s,%s,%s,%s,%s" % (
            time.time() - start,
            args.label,
            read_int(ZONE0 + "/temp") / 1000.0,
            read_int(ZONE1 + "/temp") / 1000.0,
            read(CPU0 + "/scaling_cur_freq", "?"),
            read(CPU0 + "/scaling_max_freq", "?"),
            read(COOL0 + "/cur_state", "?"),
            read(COOL0 + "/max_state", "?"),
            read(COOL1 + "/cur_state", "?"),
            charger_online(),
            fps,
        ))
        sys.stdout.flush()
        time.sleep(args.interval)

    return 0


if __name__ == "__main__":
    sys.exit(main())

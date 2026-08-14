#!/usr/bin/env python3
"""Send a bounded live gameplay action roll with one uinput device.

This continues an already loaded game; it does not navigate menus or launch a
second instance.  Each optional state snapshot is an external /proc read of the
fixed memory rings, never logging from a game or audio thread.
"""
import os
import json
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import autoload_save
import send_key


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/mgs2-action-roll"
    key = sys.argv[2] if len(sys.argv) > 2 else "x"
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 24
    hold = float(os.environ.get("MGS2_ACTION_HOLD", "0.18"))
    gap = float(os.environ.get("MGS2_ACTION_GAP", "0.30"))
    capture_delay = float(os.environ.get("MGS2_ACTION_CAPTURE_DELAY", "0.02"))
    approach_key = os.environ.get("MGS2_ACTION_APPROACH_KEY", "")
    approach_hold = float(os.environ.get("MGS2_ACTION_APPROACH_HOLD", "0.0"))
    approach_gap = float(os.environ.get("MGS2_ACTION_APPROACH_GAP", "0.10"))
    capture_sinkprobe = os.environ.get("MGS2_ACTION_SINKPROBE", "0") != "0"
    sinkprobe_wait = float(os.environ.get("MGS2_ACTION_SINKPROBE_WAIT", "1.50"))
    capture_audio_each = os.environ.get("MGS2_ACTION_CAPTURE_AUDIO_EACH", "1") != "0"
    shot_interval = int(os.environ.get("MGS2_ACTION_SHOT_INTERVAL", "4"))
    if key not in send_key.KEYMAP:
        raise SystemExit("unknown action key %r" % key)
    for part in approach_key.split("+") if approach_key else ():
        if part not in send_key.KEYMAP:
            raise SystemExit("unknown approach key %r" % part)

    os.makedirs(out, exist_ok=True)
    os.environ.setdefault("XDG_RUNTIME_DIR", "/var/run/0-runtime-dir")
    os.environ.setdefault("WAYLAND_DISPLAY", "wayland-1")

    import fcntl
    fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
    fcntl.ioctl(fd, send_key.UI_SET_EVBIT, send_key.EV_KEY)
    for code in range(1, 128):
        fcntl.ioctl(fd, send_key.UI_SET_KEYBIT, code)
    os.write(fd, send_key.make_uidev("mgsdbg-action-roll"))
    fcntl.ioctl(fd, send_key.UI_DEV_CREATE)
    time.sleep(send_key.SETTLE_S)
    print("окно сфокусировано: %s" % send_key.focus_game(), flush=True)
    time.sleep(0.5)

    syn = struct.pack("<qqHHi", 0, 0, send_key.EV_SYN, send_key.SYN_REPORT, 0)
    code = send_key.KEYMAP[key]
    prefix = os.environ.get("MGS2_LIVE_PREFIX", "")
    for item in prefix.split(","):
        if not item.strip():
            continue
        fields = item.strip().split(":", 1)
        prefix_key = fields[0]
        prefix_hold = float(fields[1]) if len(fields) == 2 else 0.2
        if prefix_key == "wait":
            time.sleep(prefix_hold)
            print("prefix wait:%.2f tick=%d" %
                  (prefix_hold, int(time.monotonic() * 1000)), flush=True)
            continue
        prefix_keys = prefix_key.split("+")
        for name in prefix_keys:
            if name not in send_key.KEYMAP:
                raise SystemExit("unknown prefix key %r" % name)
        prefix_codes = [send_key.KEYMAP[name] for name in prefix_keys]
        for prefix_code in prefix_codes:
            os.write(fd, struct.pack("<qqHHi", 0, 0, send_key.EV_KEY, prefix_code, 1))
        os.write(fd, syn)
        time.sleep(prefix_hold)
        for prefix_code in reversed(prefix_codes):
            os.write(fd, struct.pack("<qqHHi", 0, 0, send_key.EV_KEY, prefix_code, 0))
        os.write(fd, syn)
        time.sleep(float(os.environ.get("MGS2_LIVE_PREFIX_GAP", "0.0")))
        print("prefix %s:%.2f tick=%d" %
              (prefix_key, prefix_hold, int(time.monotonic() * 1000)), flush=True)
    autoload_save.capture_audio_state("before", out)
    autoload_save.OUT = out
    autoload_save.shot("before-actions")
    for i in range(count):
        if approach_key and approach_hold > 0:
            approach_codes = [send_key.KEYMAP[name]
                              for name in approach_key.split("+")]
            for approach_code in approach_codes:
                os.write(fd, struct.pack("<qqHHi", 0, 0, send_key.EV_KEY,
                                         approach_code, 1))
            os.write(fd, syn)
            time.sleep(approach_hold)
            for approach_code in reversed(approach_codes):
                os.write(fd, struct.pack("<qqHHi", 0, 0, send_key.EV_KEY,
                                         approach_code, 0))
            os.write(fd, syn)
            time.sleep(approach_gap)
        if capture_sinkprobe:
            autoload_save.arm_action_sinkprobe()
        press_tick = int(time.monotonic() * 1000)
        os.write(fd, struct.pack("<qqHHi", 0, 0, send_key.EV_KEY, code, 1))
        os.write(fd, syn)
        time.sleep(hold)
        os.write(fd, struct.pack("<qqHHi", 0, 0, send_key.EV_KEY, code, 0))
        os.write(fd, syn)
        time.sleep(sinkprobe_wait if capture_sinkprobe else capture_delay)
        sink_state = None
        if capture_sinkprobe:
            sink_state = autoload_save.capture_action_sinkprobe(
                    "after-%02d" % (i + 1), out)
        if capture_audio_each:
            autoload_save.capture_audio_state("after-%02d" % (i + 1), out)
        with open(os.path.join(out, "actions.jsonl"), "a",
                  encoding="utf-8") as stream:
            json.dump({
                "action": i + 1,
                "key": key,
                "press_tick": press_tick,
                "capture_tick": int(time.monotonic() * 1000),
                "sink_marker": sink_state["marker"] if sink_state else None,
                "sink_count": sink_state["count"] if sink_state else None,
            }, stream, separators=(",", ":"))
            stream.write("\n")
        if shot_interval and (i + 1) % shot_interval == 0:
            autoload_save.OUT = out
            autoload_save.shot("action-%02d" % (i + 1))
        print("действие %d/%d tick=%d" %
              (i + 1, count, int(time.monotonic() * 1000)), flush=True)
        time.sleep(gap)

    if count and not capture_audio_each:
        autoload_save.capture_audio_state("after", out)

    fcntl.ioctl(fd, send_key.UI_DEV_DESTROY)
    os.close(fd)


if __name__ == "__main__":
    main()

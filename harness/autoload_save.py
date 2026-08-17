#!/usr/bin/env python3
"""Drive the game from a cold title screen into a loaded save, unattended.

Why this exists: the permanent freeze the player reports does not happen in the
attract-mode demo -- 8.4 hours on 2026-08-13 produced none -- so the freezes can
only be measured with a real save loaded.

Two things learned the hard way here, both visible in the screenshots this writes:

  * START does not advance the title screen. gptokeyb maps start=tab, but the
    game only reacts to the A button, which mgs2.gptk maps to `z`.
  * one uinput device per keypress loses keys. Creating and destroying the device
    around every step dropped roughly every other event, which shifted the whole
    route and landed on NEW GAME twice. The device is created ONCE here and the
    steps are timed inside its lifetime.

Route, as described by the player and confirmed by the screenshots:
    title      z            -> main menu
    main menu  down         -> "load game"
    main menu  z            -> save list
    save list  z            -> selects the save, opens the yes/no box
    yes/no     left         -> cursor onto "yes"
    yes/no     z            -> the save loads
"""
import os
import json
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import send_key  # constants, uinput plumbing and the sway focus helper

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/autoload"
CONFIRM = sys.argv[2] if len(sys.argv) > 2 else "z"

# The save list opens on the wrong entry. The save this project measures on --
# the heavy spot with the reinforcement encounter -- is two positions up, so the
# cursor has to be moved before confirming. Reported by the owner on
# 2026-08-15, after the first unattended runs kept loading a different save and
# quietly measuring the wrong scene. MGS2_SAVE_UP overrides the count for a
# different save; 0 keeps the old behaviour.
SAVE_UP = int(os.environ.get("MGS2_SAVE_UP", "2"))

# step name, key, seconds to wait AFTER it before the screenshot
ROUTE = [
    ("1-main-menu",    CONFIRM, 6),
    ("2-on-load-game", "down",  3),
    ("3-save-list",    CONFIRM, 7),
] + [
    ("3%s-save-up-%d" % (chr(ord("a") + i), i + 1), "up", 2)
    for i in range(SAVE_UP)
] + [
    ("4-confirm-box",  CONFIRM, 5),
    ("5-on-yes",       "left",  3),
    ("6-loaded",       CONFIRM, 50),
]


def shot(name):
    subprocess.run(["grim", os.path.join(OUT, name + ".png")],
                   capture_output=True, timeout=30)
    print("  снимок %s" % name, flush=True)


def game_pid():
    """Return the one exact game PID without matching gptokeyb's arguments."""
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            with open("/proc/%s/comm" % entry, encoding="ascii") as stream:
                if stream.read().strip() == "mgs2_sse_rg353v":
                    return int(entry)
        except OSError:
            pass
    raise RuntimeError("MGS2 process not found for action capture")


def capture_audio_state(label, outdir):
    """Read each bounded audio ring once, outside every game/audio thread."""
    pid = game_pid()
    os.makedirs(outdir, exist_ok=True)
    import dmime_state
    import dmsynth_state
    import dsound_sfx_state
    readers = (
        ("dmime", dmime_state),
        ("dmsynth", dmsynth_state),
        ("dsound", dsound_sfx_state),
    )
    for name, reader in readers:
        output = os.path.join(outdir, "%s-%s.json" % (label, name))
        temporary = output + ".tmp"
        state = reader.read_state(pid, reader.STATE_RVA, 0)
        with open(temporary, "w", encoding="utf-8") as stream:
            json.dump(state, stream, indent=2)
            stream.write("\n")
        os.replace(temporary, output)
    print("  audio-state %s tick=%d" %
          (label, int(time.monotonic() * 1000)), flush=True)


def arm_action_sinkprobe():
    """Arm the next filtered target event before one automated action."""
    import dmsynth_sinkprobe
    state = dmsynth_sinkprobe.arm_state(game_pid())
    if state["marker"] or state["count"]:
        raise RuntimeError("sink probe did not arm cleanly")
    print("  sink-probe armed tick=%d" %
          int(time.monotonic() * 1000), flush=True)
    return state


def capture_action_sinkprobe(label, outdir):
    """Persist one completed memory-only render/copy capture externally."""
    import dmsynth_sinkprobe
    os.makedirs(outdir, exist_ok=True)
    state = dmsynth_sinkprobe.read_state(game_pid())
    output = os.path.join(outdir, "%s-sinkprobe.json" % label)
    temporary = output + ".tmp"
    with open(temporary, "w", encoding="utf-8") as stream:
        json.dump(state, stream, indent=2)
        stream.write("\n")
    os.replace(temporary, output)
    print("  sink-probe %s marker=%d count=%d tick=%d" %
          (label, state["marker"], state["count"],
           int(time.monotonic() * 1000)), flush=True)
    return state


def main():
    os.makedirs(OUT, exist_ok=True)
    env = dict(os.environ)
    env.setdefault("XDG_RUNTIME_DIR", "/var/run/0-runtime-dir")
    env.setdefault("WAYLAND_DISPLAY", "wayland-1")
    os.environ.update(env)

    import fcntl
    import struct
    fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
    fcntl.ioctl(fd, send_key.UI_SET_EVBIT, send_key.EV_KEY)
    for code in range(1, 128):
        fcntl.ioctl(fd, send_key.UI_SET_KEYBIT, code)
    os.write(fd, send_key.make_uidev("mgsdbg-autoload"))
    fcntl.ioctl(fd, send_key.UI_DEV_CREATE)
    time.sleep(send_key.SETTLE_S)
    focused = send_key.focus_game()
    print("окно сфокусировано: %s" % focused, flush=True)
    time.sleep(1.0)

    syn = struct.pack("<qqHHi", 0, 0, send_key.EV_SYN, send_key.SYN_REPORT, 0)

    def press(name, hold=0.20):
        code = send_key.KEYMAP[name]
        os.write(fd, struct.pack("<qqHHi", 0, 0, send_key.EV_KEY, code, 1))
        os.write(fd, syn)
        time.sleep(hold)
        os.write(fd, struct.pack("<qqHHi", 0, 0, send_key.EV_KEY, code, 0))
        os.write(fd, syn)

    def press_chord(names, hold):
        keys = names.split("+")
        codes = [send_key.KEYMAP[key] for key in keys]
        for code in codes:
            os.write(fd, struct.pack("<qqHHi", 0, 0, send_key.EV_KEY, code, 1))
        os.write(fd, syn)
        time.sleep(hold)
        for code in reversed(codes):
            os.write(fd, struct.pack("<qqHHi", 0, 0, send_key.EV_KEY, code, 0))
        os.write(fd, syn)

    # The device is live but the compositor may still be routing the first event
    # of a fresh seat device; spend it on a key the title screen ignores.
    press("up")
    time.sleep(1.5)
    shot("0-title")

    for name, key, wait in ROUTE:
        print("== %s : %s ==" % (name, key), flush=True)
        press(key)
        time.sleep(wait)
        shot(name)

    # Walking is what the player described as the trigger: arriving in a new
    # scene stalls, seeing a new enemy stalls, then it settles. The saved game
    # starts Raiden against the upper door, so "up" only walks into the wall and
    # never exposes the guard in the room below. This was verified from the
    # per-step screenshots on 2026-08-13. Default to "down", while keeping an
    # override for a different save or route.
    bursts = int(os.environ.get("MGS2_WALK_BURSTS", "12"))
    walk_key = os.environ.get("MGS2_WALK_KEY", "down")
    walk_hold = float(os.environ.get("MGS2_WALK_HOLD", "2.5"))
    walk_gap = float(os.environ.get("MGS2_WALK_GAP", "1.5"))
    walk_sequence = os.environ.get("MGS2_WALK_SEQUENCE")
    if walk_sequence:
        walk_steps = []
        for item in walk_sequence.split(","):
            fields = item.strip().split(":", 1)
            key = fields[0]
            hold = float(fields[1]) if len(fields) == 2 else walk_hold
            walk_steps.append((key, hold))
    else:
        walk_steps = [(walk_key, walk_hold)] * bursts
    for key, unused in walk_steps:
        for part in key.split("+"):
            if part not in send_key.KEYMAP:
                raise SystemExit("unknown walk key %r" % part)
    for i, (key, hold) in enumerate(walk_steps):
        press_chord(key, hold)
        time.sleep(walk_gap)
        if i % 4 == 3:
            shot("7-walk-%d" % (i + 1))
            print("  прошёл %d бросков" % (i + 1), flush=True)

    # Optional bounded action sequence for sound diagnostics. A recording of
    # the user's translated keyboard stream established that `x` is the real
    # attack key. The earlier `z` automation performed rolls/throws even though
    # its historical helper called those actions punches. It is off by default,
    # so the freeze route is unchanged.
    action_count = int(os.environ.get("MGS2_ACTION_COUNT", "0"))
    action_key = os.environ.get("MGS2_ACTION_KEY", "x")
    action_gap = float(os.environ.get("MGS2_ACTION_GAP", "0.8"))
    action_hold = float(os.environ.get("MGS2_ACTION_HOLD", "0.15"))
    approach_key = os.environ.get("MGS2_ACTION_APPROACH_KEY", "")
    approach_hold = float(os.environ.get("MGS2_ACTION_APPROACH_HOLD", "0.0"))
    if action_key not in send_key.KEYMAP:
        raise SystemExit("unknown MGS2_ACTION_KEY %r" % action_key)
    for part in approach_key.split("+") if approach_key else ():
        if part not in send_key.KEYMAP:
            raise SystemExit("unknown MGS2_ACTION_APPROACH_KEY %r" % part)
    if action_count:
        print("== 8-actions : %s x %d tick=%d ==" %
              (action_key, action_count, int(time.monotonic() * 1000)), flush=True)
        if os.environ.get("MGS2_SFX_ARM_ACTIONS", "0") != "0":
            # dsound's producer probe notices this marker at the next Play and
            # removes it itself.  The probe is separately env-gated and bounded
            # to twelve Play calls; the normal route never creates the marker.
            with open("/tmp/mgs2-sfx-arm", "wb"):
                pass
            print("  producer marker armed", flush=True)
    capture_dir = os.environ.get("MGS2_ACTION_CAPTURE_DIR")
    capture_each = os.environ.get("MGS2_ACTION_CAPTURE_EACH", "0") != "0"
    capture_sinkprobe = (capture_dir
                         and os.environ.get("MGS2_ACTION_SINKPROBE", "0") != "0")
    sinkprobe_wait = float(os.environ.get("MGS2_ACTION_SINKPROBE_WAIT", "1.50"))
    shot_interval = int(os.environ.get("MGS2_ACTION_SHOT_INTERVAL", "0"))
    if (action_count and capture_dir
            and os.environ.get("MGS2_ACTION_CAPTURE_BEFORE", "1") != "0"):
        capture_audio_state("before", capture_dir)
    for i in range(action_count):
        if approach_key and approach_hold > 0:
            press_chord(approach_key, approach_hold)
            time.sleep(float(os.environ.get("MGS2_ACTION_APPROACH_GAP", "0.10")))
        if capture_sinkprobe:
            arm_action_sinkprobe()
        press_tick = int(time.monotonic() * 1000)
        press(action_key, action_hold)
        sink_state = None
        if capture_sinkprobe:
            time.sleep(sinkprobe_wait)
            sink_state = capture_action_sinkprobe("after-%02d" % (i + 1), capture_dir)
        if capture_dir and (capture_each or i + 1 == action_count):
            if not capture_sinkprobe:
                time.sleep(float(os.environ.get("MGS2_ACTION_CAPTURE_DELAY", "0.30")))
            label = "after-%02d" % (i + 1) if capture_each else "after"
            capture_audio_state(label, capture_dir)
        if capture_dir:
            with open(os.path.join(capture_dir, "actions.jsonl"), "a",
                      encoding="utf-8") as stream:
                json.dump({
                    "action": i + 1,
                    "key": action_key,
                    "press_tick": press_tick,
                    "capture_tick": int(time.monotonic() * 1000),
                    "sink_marker": sink_state["marker"] if sink_state else None,
                    "sink_count": sink_state["count"] if sink_state else None,
                }, stream, separators=(",", ":"))
                stream.write("\n")
        if shot_interval and (i + 1) % shot_interval == 0:
            shot("8-action-%02d" % (i + 1))
        time.sleep(action_gap)
        print("  действие %d/%d tick=%d" %
              (i + 1, action_count, int(time.monotonic() * 1000)), flush=True)
    if action_count:
        shot("8-actions-done")

    time.sleep(0.5)
    fcntl.ioctl(fd, send_key.UI_DEV_DESTROY)
    os.close(fd)


if __name__ == "__main__":
    main()

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
import ctypes
import json
import mmap
import stat
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

# Fixed 640x480 screen coordinates of the solid 18x10 selection marker.  The
# animated menu background changes every frame, so whole-image hashes are not a
# useful route gate; comparing the two marker cells is stable across runs.
MENU_NEW_GAME_MARKER = "18x10+37+65"
MENU_LOAD_GAME_MARKER = "18x10+37+92"
SAVE_MARKER_X = 37
SAVE_MARKER_FIRST_Y = 153
SAVE_MARKER_STEP_Y = 26


class LockedFileMapping:
    """One shared, read-only libc mapping kept alive until route completion."""
    def __init__(self, libc, address, size):
        self.libc = libc
        self.address = address
        self.size = size

    def close(self):
        if self.address is None:
            return
        if self.libc.munmap(ctypes.c_void_p(self.address),
                           ctypes.c_size_t(self.size)) != 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error))
        self.address = None


def shot(name):
    path = os.path.join(OUT, name + ".png")
    result = subprocess.run(["grim", path], capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError("grim failed for %s: %s" %
                           (name, result.stderr.decode(errors="replace")))
    print("  снимок %s tick=%d" %
          (name, int(time.monotonic() * 1000)), flush=True)
    return path


def image_geometry(path):
    result = subprocess.run(
        ["identify", "-format", "%wx%h", path], capture_output=True,
        text=True, timeout=30, check=True)
    return result.stdout.strip()


def image_metric(path, geometry, colorspace="Gray", channel=None):
    """Return a bounded ImageMagick crop mean for a fail-closed route gate."""
    command = ["convert", path, "-crop", geometry, "+repage",
               "-colorspace", colorspace]
    if channel:
        command += ["-channel", channel, "-separate"]
    command += ["-format", "%[fx:mean]", "info:"]
    result = subprocess.run(command, capture_output=True, text=True,
                            timeout=30, check=True)
    return float(result.stdout)


def menu_selection(path):
    if image_geometry(path) != "640x480":
        raise RuntimeError("route gate requires 640x480, got %s" %
                           image_geometry(path))
    new_game = image_metric(path, MENU_NEW_GAME_MARKER)
    load_game = image_metric(path, MENU_LOAD_GAME_MARKER)
    print("  menu-marker new=%.3f load=%.3f" %
          (new_game, load_game), flush=True)
    if new_game > load_game + 0.12 and new_game > 0.35:
        return "new-game"
    if load_game > new_game + 0.12 and load_game > 0.35:
        return "load-game"
    return None


def save_selection(path):
    means = [image_metric(
        path, "18x10+%d+%d" %
        (SAVE_MARKER_X, SAVE_MARKER_FIRST_Y + SAVE_MARKER_STEP_Y * index))
        for index in range(10)]
    order = sorted(range(len(means)), key=means.__getitem__, reverse=True)
    best, second = order[:2]
    print("  save-marker row=%02d mean=%.3f next=%.3f" %
          (best, means[best], means[second]), flush=True)
    if means[best] > 0.35 and means[best] > means[second] + 0.12:
        return best
    return None


def yes_no_selection(path):
    # Saturation distinguishes the orange selected word from the grey one. The
    # crops intentionally include no save-row cursor, so a dropped confirm key
    # remains ambiguous and fails closed instead of entering the wrong route.
    yes = image_metric(path, "80x30+450+400", "HSL", "G")
    no = image_metric(path, "80x30+530+400", "HSL", "G")
    print("  yes-no saturation yes=%.3f no=%.3f" % (yes, no), flush=True)
    if yes > no + 0.02 and yes > 0.06:
        return "yes"
    if no > yes + 0.02 and no > 0.04:
        return "no"
    return None


def screen_gray_mean(path):
    value = image_metric(path, "640x480+0+0")
    print("  screen-gray-mean=%.3f" % value, flush=True)
    return value


def prewarm_paths():
    """Synchronously page in an explicitly bounded, default-off file set.

    MGS2_PREWARM_MLOCK=1 keeps the private file mappings alive for the route.
    This is a diagnostic arm only: successful mlock both faults the file pages
    in and makes them unevictable until the mappings are closed.
    """
    raw = os.environ.get("MGS2_PREWARM_PATHS", "").strip()
    if not raw:
        return []
    paths = [path for path in raw.split(os.pathsep) if path]
    limit = int(os.environ.get("MGS2_PREWARM_MAX_BYTES", str(16 * 1024 * 1024)))
    max_files = int(os.environ.get("MGS2_PREWARM_MAX_FILES", "16"))
    lock_value = os.environ.get("MGS2_PREWARM_MLOCK", "0")
    if lock_value not in ("0", "1"):
        raise RuntimeError("MGS2_PREWARM_MLOCK must be 0 or 1")
    lock_pages = lock_value == "1"
    if (not paths or len(paths) > max_files or len(paths) != len(set(paths))
            or limit <= 0 or max_files <= 0):
        raise RuntimeError("invalid prewarm path list or byte limit")
    entries = []
    total_size = 0
    for path in paths:
        if not os.path.isabs(path):
            raise RuntimeError("prewarm path must be absolute: %s" % path)
        info = os.stat(path, follow_symlinks=True)
        if not stat.S_ISREG(info.st_mode):
            raise RuntimeError("prewarm path is not a regular file: %s" % path)
        total_size += info.st_size
        if total_size > limit:
            raise RuntimeError("prewarm files exceed bounded limit %d" % limit)
        entries.append((path, info.st_size))

    libc = None
    map_file = None
    unmap_file = None
    mlock = None
    if lock_pages:
        libc = ctypes.CDLL(None, use_errno=True)
        map_file = libc.mmap
        map_file.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int,
                             ctypes.c_int, ctypes.c_int, ctypes.c_long]
        map_file.restype = ctypes.c_void_p
        unmap_file = libc.munmap
        unmap_file.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        unmap_file.restype = ctypes.c_int
        mlock = libc.mlock
        mlock.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        mlock.restype = ctypes.c_int

    started = time.monotonic_ns()
    held_mappings = []
    try:
        for path, expected_size in entries:
            file_started = time.monotonic_ns()
            if lock_pages:
                file_fd = os.open(path, os.O_RDONLY)
                try:
                    address = map_file(
                        None, expected_size, mmap.PROT_READ, mmap.MAP_SHARED,
                        file_fd, 0)
                finally:
                    os.close(file_fd)
                if address == ctypes.c_void_p(-1).value:
                    error = ctypes.get_errno()
                    raise OSError(error, os.strerror(error), path)
                ctypes.set_errno(0)
                if mlock(ctypes.c_void_p(address),
                         ctypes.c_size_t(expected_size)) != 0:
                    error = ctypes.get_errno()
                    unmap_file(ctypes.c_void_p(address),
                               ctypes.c_size_t(expected_size))
                    raise OSError(error, os.strerror(error), path)
                held_mappings.append(
                    LockedFileMapping(libc, address, expected_size))
                count = expected_size
            else:
                count = 0
                file_fd = os.open(path, os.O_RDONLY)
                try:
                    if hasattr(os, "posix_fadvise"):
                        os.posix_fadvise(file_fd, 0, expected_size,
                                         os.POSIX_FADV_SEQUENTIAL)
                    while True:
                        chunk = os.read(file_fd, 1024 * 1024)
                        if not chunk:
                            break
                        count += len(chunk)
                finally:
                    os.close(file_fd)
            if count != expected_size:
                raise RuntimeError("short prewarm read for %s: %d/%d" %
                                   (path, count, expected_size))
            print("  prewarm mode=%s mapping=%s path=%s bytes=%d elapsed_ms=%.3f" %
                  ("mlock" if lock_pages else "read",
                   "shared-readonly" if lock_pages else "none", path, count,
                   (time.monotonic_ns() - file_started) / 1_000_000),
                  flush=True)
    except Exception:
        for mapping in reversed(held_mappings):
            mapping.close()
        raise

    locked_kib = 0
    if lock_pages:
        with open("/proc/self/status", encoding="ascii") as stream:
            for line in stream:
                if line.startswith("VmLck:"):
                    locked_kib = int(line.split()[1])
                    break
        if locked_kib * 1024 < total_size:
            for mapping in reversed(held_mappings):
                mapping.close()
            raise RuntimeError("VmLck did not cover the requested file set")
    print("  prewarm-complete mode=%s files=%d bytes=%d vmlck_kib=%d "
          "elapsed_ms=%.3f tick=%d" %
          ("mlock" if lock_pages else "read", len(entries), total_size,
           locked_kib, (time.monotonic_ns() - started) / 1_000_000,
           int(time.monotonic() * 1000)), flush=True)
    return held_mappings


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
    import dmsynth_state
    import dsound_sfx_state
    readers = [
        ("dmsynth", dmsynth_state),
        ("dsound", dsound_sfx_state),
    ]
    # FINALPLAY21's dmime_transition1.dll has no DMT1 recorder.  Read that ring
    # only on the explicit diagnostic route that requested it; otherwise an
    # absent optional instrument must not discard the independent DMSynth and
    # DirectSound snapshots or abort a visual soak.
    if os.environ.get("MGS2_DMIME_STATE", "0") != "0":
        import dmime_state
        readers.insert(0, ("dmime", dmime_state))
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
    print("autoload-start tick=%d" % int(time.monotonic() * 1000), flush=True)

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

    def route_step(name, key, wait):
        print("== %s : %s tick=%d ==" %
              (name, key, int(time.monotonic() * 1000)), flush=True)
        press(key)
        time.sleep(wait)
        return shot(name)

    # Every transition is checked from the actual framebuffer. uinput delivery
    # on this stack is not guaranteed; step names in a log are not evidence that
    # the game accepted the key.
    main_menu_path = None
    for attempt in range(3):
        suffix = "" if attempt == 0 else "-retry-%d" % attempt
        main_menu_path = route_step("1-main-menu" + suffix, CONFIRM, 6)
        if menu_selection(main_menu_path) == "new-game":
            break
        send_key.focus_game()
    else:
        raise RuntimeError("title -> main menu was not confirmed by pixels")

    load_menu_path = None
    for attempt in range(3):
        suffix = "" if attempt == 0 else "-retry-%d" % attempt
        load_menu_path = route_step("2-on-load-game" + suffix, "down", 3)
        selection = menu_selection(load_menu_path)
        if selection == "load-game":
            break
        if selection != "new-game":
            raise RuntimeError("main-menu selection became ambiguous")
        send_key.focus_game()
    else:
        raise RuntimeError("LOAD GAME was not selected; refusing NEW GAME")

    save_list_path = None
    for attempt in range(3):
        suffix = "" if attempt == 0 else "-retry-%d" % attempt
        save_list_path = route_step("3-save-list" + suffix, CONFIRM, 7)
        selected_save = save_selection(save_list_path)
        if selected_save is not None:
            break
        if menu_selection(save_list_path) != "load-game":
            raise RuntimeError("LOAD GAME -> save list became ambiguous")
        send_key.focus_game()
    else:
        raise RuntimeError("save list did not open")

    expected_save = selected_save
    for i in range(SAVE_UP):
        expected_save -= 1
        if expected_save < 0:
            raise RuntimeError("MGS2_SAVE_UP moves above the first save")
        for attempt in range(3):
            base = "3%s-save-up-%d" % (chr(ord("a") + i), i + 1)
            suffix = "" if attempt == 0 else "-retry-%d" % attempt
            save_path = route_step(base + suffix, "up", 2)
            actual_save = save_selection(save_path)
            if actual_save == expected_save:
                break
            if actual_save != expected_save + 1:
                raise RuntimeError("save cursor became ambiguous")
            send_key.focus_game()
        else:
            raise RuntimeError("save cursor did not move to row %02d" %
                               expected_save)

    confirm_path = None
    for attempt in range(3):
        suffix = "" if attempt == 0 else "-retry-%d" % attempt
        confirm_path = route_step("4-confirm-box" + suffix, CONFIRM, 5)
        selection = yes_no_selection(confirm_path)
        if selection == "no":
            break
        if save_selection(confirm_path) != expected_save:
            raise RuntimeError("save -> confirmation box became ambiguous")
        send_key.focus_game()
    else:
        raise RuntimeError("load confirmation box did not open")

    yes_path = None
    for attempt in range(3):
        suffix = "" if attempt == 0 else "-retry-%d" % attempt
        yes_path = route_step("5-on-yes" + suffix, "left", 3)
        selection = yes_no_selection(yes_path)
        if selection == "yes":
            break
        if selection != "no":
            raise RuntimeError("YES/NO selection became ambiguous")
        send_key.focus_game()
    else:
        raise RuntimeError("YES was not selected")

    locked_prewarm = prewarm_paths()
    loaded_path = route_step("6-loaded", CONFIRM, 50)
    if screen_gray_mean(loaded_path) < 0.15:
        if yes_no_selection(loaded_path) == "yes":
            loaded_path = route_step("6-loaded-retry-1", CONFIRM, 50)
        if screen_gray_mean(loaded_path) < 0.15:
            raise RuntimeError("fixed Strut D gameplay scene was not confirmed")

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

    for mapping in reversed(locked_prewarm):
        mapping.close()
    if locked_prewarm:
        print("  prewarm-unlocked files=%d tick=%d" %
              (len(locked_prewarm), int(time.monotonic() * 1000)), flush=True)
    time.sleep(0.5)
    fcntl.ioctl(fd, send_key.UI_DEV_DESTROY)
    os.close(fd)


if __name__ == "__main__":
    main()

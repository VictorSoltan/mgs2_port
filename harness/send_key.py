"""Synthetic keyboard for driving the game to a deterministic screen.

Three things the first version got wrong, all of which stop events reaching a
Wine client under sway:

  * it declared only the keys it was about to send.  libinput classifies a
    device by its capabilities, and a device advertising one or two keys is not
    reliably treated as a keyboard, so wlroots never routes it to the focused
    surface.  Declare the whole standard key range instead.
  * it slept 0.5 s after UI_DEV_CREATE.  udev + libinput enumeration on this
    device takes longer than that; events sent into the gap are simply dropped.
  * it held each key for 50 ms.  The game polls input once per frame and runs
    at 25-35 fps, so a 50 ms press can fall between two polls.

Usage:  python3 send_key.py [--hold MS] [--gap MS] key [key ...]
"""
import fcntl
import os
import struct
import subprocess
import sys
import time

UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502
EV_KEY = 0x01
EV_SYN = 0x00
SYN_REPORT = 0

UINPUT_MAX_NAME_SIZE = 80
ABS_CNT = 64

# The full set the gptokeyb profile (mgs2.gptk) can produce, so any control the
# game expects can be driven from here:
#   back=enter start=tab guide=esc a=z b=x x=s y=d l1=a l2=w r1=f r2=e r3=k
KEYMAP = {
    "esc": 1, "enter": 28, "space": 57, "tab": 15,
    "a": 30, "s": 31, "d": 32, "e": 18, "f": 33, "i": 23,
    "j": 36, "k": 37, "l": 38, "m": 50, "w": 17, "x": 45, "z": 44,
    "up": 103, "down": 108, "left": 105, "right": 106,
    "lctrl": 29, "lalt": 56, "lshift": 42, "f1": 59,
}

# Enumeration delay: udev must create the node, libinput must open it and sway
# must attach it to the seat before the first event is worth sending.
SETTLE_S = 1.8


def make_uidev(name):
    buf = bytearray(UINPUT_MAX_NAME_SIZE + 8 + 4 + ABS_CNT * 4 * 4)
    encoded = name.encode()[: UINPUT_MAX_NAME_SIZE - 1]
    buf[: len(encoded)] = encoded
    # bustype USB, vendor/product/version -- a plausible USB keyboard.
    struct.pack_into("<HHHH", buf, UINPUT_MAX_NAME_SIZE, 0x03, 0x1, 0x1, 1)
    return bytes(buf)


def focus_game():
    """Focus the Wine window; an unfocused surface receives no key events."""
    try:
        tree = subprocess.run(
            ["swaymsg", "-t", "get_tree", "-r"],
            capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return False
    import json

    def walk(node):
        yield node
        for child in node.get("nodes", []) + node.get("floating_nodes", []):
            yield from walk(child)

    try:
        root = json.loads(tree)
    except ValueError:
        return False
    for node in walk(root):
        name = (node.get("name") or "") + " " + (node.get("app_id") or "")
        if "METAL GEAR" in name.upper() or "MGS2" in name.upper():
            subprocess.run(["swaymsg", "[con_id=%d]" % node["id"], "focus"],
                           capture_output=True, timeout=10)
            return True
    return False


def send(keys, hold_ms, gap_ms, arm_path=None):
    fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
    fcntl.ioctl(fd, UI_SET_EVBIT, EV_KEY)
    # Advertise a full keyboard, not just the keys in this run.
    for code in range(1, 128):
        fcntl.ioctl(fd, UI_SET_KEYBIT, code)
    os.write(fd, make_uidev("mgsdbg-vkbd"))
    fcntl.ioctl(fd, UI_DEV_CREATE)
    time.sleep(SETTLE_S)

    focused = focus_game()
    time.sleep(0.3)

    if arm_path:
        with open(arm_path, "wb"):
            pass

    syn = struct.pack("<qqHHi", 0, 0, EV_SYN, SYN_REPORT, 0)
    for code in keys:
        os.write(fd, struct.pack("<qqHHi", 0, 0, EV_KEY, code, 1))
        os.write(fd, syn)
        time.sleep(hold_ms / 1000.0)
        os.write(fd, struct.pack("<qqHHi", 0, 0, EV_KEY, code, 0))
        os.write(fd, syn)
        time.sleep(gap_ms / 1000.0)

    time.sleep(0.3)
    fcntl.ioctl(fd, UI_DEV_DESTROY)
    os.close(fd)
    return focused


if __name__ == "__main__":
    argv = sys.argv[1:]
    hold, gap, arm_path = 150, 400, None
    while argv and argv[0].startswith("--"):
        opt = argv.pop(0)
        if opt == "--hold":
            hold = int(argv.pop(0))
        elif opt == "--gap":
            gap = int(argv.pop(0))
        elif opt == "--arm":
            arm_path = argv.pop(0)
        else:
            sys.exit("unknown option %s" % opt)
    names = argv or ["enter"]
    try:
        codes = [KEYMAP[n] for n in names]
    except KeyError as exc:
        sys.exit("unknown key %s; known: %s" % (exc, " ".join(sorted(KEYMAP))))
    ok = send(codes, hold, gap, arm_path)
    print("sent %s (hold=%dms gap=%dms, window focused: %s)"
          % (" ".join(names), hold, gap, ok))

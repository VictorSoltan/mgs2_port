#!/usr/bin/env python3
"""Current ABSOLUTE-AXIS values on an input device, straight from the kernel.

keystate.py reads EVIOCGKEY, which covers buttons only. A joypad's sticks and
d-pad hats are ABSOLUTE AXES, and a stuck or drifting axis is invisible to a
key-state check -- while being the most likely cause of "the character walks in
one direction on its own". This reads EVIOCGABS per axis, which is the value
the game is being handed, not an inference from event history.

An axis is suspect when its current value sits far from its resting point and
stays there. flat/fuzz are the driver's own deadzone hints, printed so the
reading can be judged against what the driver itself considers noise.
"""
import ctypes, fcntl, sys

ABS_MAX = 0x3f
AXES = {0: "X (левый стик, гориз.)", 1: "Y (левый стик, верт.)",
        2: "Z", 3: "RX (правый стик, гориз.)", 4: "RY (правый стик, верт.)",
        5: "RZ", 6: "THROTTLE", 16: "HAT0X (крестовина, гориз.)",
        17: "HAT0Y (крестовина, верт.)"}

class Info(ctypes.Structure):
    _fields_ = [("value", ctypes.c_int32), ("minimum", ctypes.c_int32),
                ("maximum", ctypes.c_int32), ("fuzz", ctypes.c_int32),
                ("flat", ctypes.c_int32), ("resolution", ctypes.c_int32)]

def evio_cgabs(a):
    return (2 << 30) | (ord('E') << 8) | (0x40 + a) | (ctypes.sizeof(Info) << 16)

for dev in sys.argv[1:]:
    print(dev)
    with open(dev, "rb") as fh:
        for a in range(ABS_MAX):
            info = Info()
            try:
                fcntl.ioctl(fh, evio_cgabs(a), info)
            except OSError:
                continue
            if info.minimum == 0 and info.maximum == 0:
                continue
            span = info.maximum - info.minimum
            centre = info.minimum + span / 2.0
            off = abs(info.value - centre) / (span / 2.0) if span else 0
            flag = "  <<< ОТКЛОНЕНА" if off > 0.5 else ""
            print("  %-28s value=%-7d [%d..%d] flat=%-4d отклонение %3.0f%%%s"
                  % (AXES.get(a, "ABS_%02x" % a), info.value, info.minimum,
                     info.maximum, info.flat, off * 100, flag))

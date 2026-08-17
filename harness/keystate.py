#!/usr/bin/env python3
"""Which keys are held down RIGHT NOW on an input device.

The symptom is "the character walks left on its own and nothing responds".
That has two very different causes and they need separating before anything is
restarted, because restarting destroys the evidence:

  a stuck key on the virtual keyboard   -> the input layer is at fault, the
                                           game is behaving correctly given
                                           what it is being told
  no key held                           -> the game itself stopped consuming
                                           input, and the input layer is fine

EVIOCGKEY returns the kernel's current pressed-key bitmap for the device, which
is the state the game is reading, not a guess from event history.
"""
import fcntl, sys, ctypes

KEY_MAX = 0x2FF
EVIOCGKEY = (2 << 30) | (ord('E') << 8) | 0x18 | (((KEY_MAX // 8) + 1) << 16)

NAMES = {105: "LEFT", 106: "RIGHT", 103: "UP", 108: "DOWN", 44: "z", 45: "x",
         28: "ENTER", 15: "TAB", 1: "ESC", 57: "SPACE", 29: "LCTRL", 42: "LSHIFT",
         56: "LALT", 30: "a", 31: "s", 32: "d", 17: "w", 16: "q", 18: "e"}

for dev in sys.argv[1:]:
    buf = ctypes.create_string_buffer((KEY_MAX // 8) + 1)
    with open(dev, "rb") as fh:
        fcntl.ioctl(fh, EVIOCGKEY, buf)
    held = [i for i in range(KEY_MAX) if buf.raw[i // 8] & (1 << (i % 8))]
    print("%s: %s" % (dev, ", ".join("%s(%d)" % (NAMES.get(k, "key"), k) for k in held)
                      if held else "ничего не нажато"))

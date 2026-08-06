#!/bin/bash
# sink_audible_test.sh TAG [ENV=VAL ...]
#
# One question, answered by a capture instead of by a human at the right moment:
# does PCM written by a dmsynth sink reach the output device?
#
# The run injects a continuous 1 kHz square into every sink render
# (MGS2_SINKTONE=1, no logging on the render path) and records the speaker sink
# monitor.  A Goertzel bin at 1 kHz separates the tone from the game's own music,
# which is the whole reason a plain peak was not enough last time.
set -u
G=/storage/roms/ports/MGS2-Substance
EXE=mgs2_sse_rg353vs_port.exe
COMM=$(printf '%.15s' "$EXE")
TAG="$1"; shift
CAP=/tmp/sinktone-$TAG.wav
LOG=/tmp/sinktone-$TAG.log
export XDG_RUNTIME_DIR=/var/run/0-runtime-dir WAYLAND_DISPLAY=wayland-1

pids() { local p; for p in /proc/[0-9]*; do [ "$(cat "$p/comm" 2>/dev/null)" = "$COMM" ] && basename "$p"; done; }

cleanup() {
    killall -9 launch.sh wine wine-preloader box86 box64 gptokeyb wineserver 2>/dev/null
    sleep 3
    rm -f /tmp/mgs2-substance.lock
    local m
    for m in /usr/lib/wine/i386-windows/wined3d.dll /usr/lib/wine/i386-windows/user32.dll \
             /usr/lib/wine/i386-windows/dmsynth.dll /usr/lib/wine/i386-windows/dsound.dll \
             /usr/lib/wine/i386-windows/dmime.dll /usr/lib/wine/i386-windows/dmusic.dll \
             /usr/lib/wine/i386-unix/winewayland.so /usr/lib/wine/i386-unix/win32u.so \
             /usr/lib/wine/i386-unix/opengl32.so /usr/lib/wine/i386-unix/ntdll.so \
             /usr/bin/box86; do
        while grep -q " $m " /proc/mounts; do umount "$m" 2>/dev/null || break; done
    done
}

cleanup
cp -f "$G/send_key.py" /tmp/send_key.py 2>/dev/null
echo "=== $TAG (env: $*) ==="
( cd "$G" && setsid nohup env WINEDEBUG=-all "$@" ./launch.sh > "$LOG" 2>&1 < /dev/null & )

for i in $(seq 1 40); do
    sleep 3
    [ -n "$(pids)" ] && [ "$i" -ge 16 ] && break
    [ "$i" -gt 8 ] && [ -z "$(pids)" ] && { echo "  DIED"; cleanup; exit 1; }
done
[ -n "$(pids)" ] || { echo "  NO PID"; cleanup; exit 1; }
echo "  running, instances $(pids | wc -l)"

# Leave the attract loop so the game is on the menu, where its own music plays;
# that music is the control signal proving the capture path works.
for k in 1 2 3 4 5 6; do
    python3 /tmp/send_key.py --hold 200 --gap 500 tab >/dev/null 2>&1
    sleep 2
done
sleep 5

# Resolve the speaker sink by name; its object id is not stable across boots
# and a hardcoded one silently records nothing.
SINK=$(pw-cli ls Node 2>/dev/null | awk '/^\tid [0-9]+,/ { id=$2; sub(",","",id) } /node.name = ".*Speaker__sink"/ { print id; exit }')
echo "  capturing sink monitor id ${SINK:-none}"
timeout 20 pw-record --target "${SINK:-34}" -P '{ stream.capture.sink=true }' \
    --rate 48000 --channels 2 --format s16 "$CAP" >/dev/null 2>&1 &
sleep 16
kill %1 2>/dev/null
sleep 2

python3 - "$CAP" <<'PYEOF'
import struct, sys, math
path = sys.argv[1]
try:
    raw = open(path, "rb").read()
except OSError:
    print("  capture MISSING"); raise SystemExit
data = raw[44:]
n = len(data) // 2
if n == 0:
    print("  capture EMPTY"); raise SystemExit
v = struct.unpack("<%dh" % n, data[:n * 2])
mono = v[0::2]
peak = max((abs(x) for x in mono), default=0)
rms = math.sqrt(sum(float(x) * x for x in mono) / len(mono))

# Goertzel: energy at 1 kHz (the injected tone) vs 300 Hz (music band control).
def goertzel(samples, freq, rate=48000.0):
    w = 2.0 * math.pi * freq / rate
    coeff = 2.0 * math.cos(w)
    s1 = s2 = 0.0
    for x in samples:
        s0 = x + coeff * s1 - s2
        s2, s1 = s1, s0
    power = s1 * s1 + s2 * s2 - coeff * s1 * s2
    return math.sqrt(max(power, 0.0)) / len(samples)

seg = mono[:48000 * 10]
print("  samples=%d peak=%d rms=%.0f" % (len(mono), peak, rms))
print("  goertzel 1kHz=%.1f  300Hz=%.1f  5kHz=%.1f" %
      (goertzel(seg, 1000.0), goertzel(seg, 300.0), goertzel(seg, 5000.0)))
PYEOF

cleanup
echo "=== done $TAG ==="

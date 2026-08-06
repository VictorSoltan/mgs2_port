#!/bin/bash
# Stage 1 from the research plan: does the upstream jitter reserve make the sink
# audible with the STOCK dsound?  No key presses -- the tone is continuous from
# startup, so the intro screen is enough, and the game's own music in the same
# capture is the control that the recording path works.
set -u
G=/storage/roms/ports/MGS2-Substance
COMM=mgs2_sse_rg353v
export XDG_RUNTIME_DIR=/var/run/0-runtime-dir WAYLAND_DISPLAY=wayland-1

pids() { local p; for p in /proc/[0-9]*; do [ "$(cat "$p/comm" 2>/dev/null)" = "$COMM" ] && basename "$p"; done; }
cleanup() {
    killall -9 launch.sh wine wine-preloader box86 box64 gptokeyb wineserver 2>/dev/null
    sleep 3; rm -f /tmp/mgs2-substance.lock
    local m
    for m in /usr/lib/wine/i386-windows/wined3d.dll /usr/lib/wine/i386-windows/user32.dll \
             /usr/lib/wine/i386-windows/dmsynth.dll /usr/lib/wine/i386-windows/dsound.dll \
             /usr/lib/wine/i386-windows/dmime.dll /usr/lib/wine/i386-windows/dmusic.dll \
             /usr/lib/wine/i386-unix/winewayland.so /usr/lib/wine/i386-unix/win32u.so \
             /usr/lib/wine/i386-unix/opengl32.so /usr/lib/wine/i386-unix/ntdll.so /usr/bin/box86; do
        while grep -q " $m " /proc/mounts; do umount "$m" 2>/dev/null || break; done
    done
}

for MS in 10 20 30; do
    cleanup
    LOG=/tmp/jitter-$MS.log; CAP=/tmp/jitter-$MS.wav
    echo "=== JITTER_MS=$MS (stock dsound, dmime_graphqi, dmsynth_jitter1, tone on) ==="
    ( cd "$G" && setsid nohup env WINEDEBUG=-all,err+dmsynth \
        MGS2_DMIME_DLL=dmime_graphqi.dll MGS2_DMSYNTH_DLL=dmsynth_jitter1.dll \
        MGS2_SINKTONE=1 MGS2_DMSYNTH_JITTER_MS=$MS \
        ./launch.sh > "$LOG" 2>&1 < /dev/null & )
    for i in $(seq 1 22); do sleep 3; [ -n "$(pids)" ] && [ "$i" -ge 18 ] && break; done
    [ -n "$(pids)" ] || { echo "  DIED"; continue; }
    cmp -s /usr/lib/wine/i386-windows/dmsynth.dll "$G/dmsynth_jitter1.dll" \
        && echo "  dmsynth=jitter1 mounted" || echo "  dmsynth=WRONG"
    SINK=$(pw-cli ls Node 2>/dev/null | awk '/^\tid [0-9]+,/ { id=$2; sub(",","",id) } /node.name = ".*Speaker__sink"/ { print id; exit }')
    timeout 18 pw-record --target "${SINK:-34}" -P '{ stream.capture.sink=true }' \
        --rate 48000 --channels 2 --format s16 "$CAP" >/dev/null 2>&1 &
    sleep 15; kill %1 2>/dev/null; sleep 2
    echo "  underruns=$(grep -c 'Underrun detected' "$LOG" 2>/dev/null) tone_writes=$(grep -c 'SINKTONE writing' "$LOG" 2>/dev/null)"
    python3 - "$CAP" <<'PY'
import struct, sys, math
try: raw = open(sys.argv[1], "rb").read()
except OSError: print("  capture MISSING"); raise SystemExit
d = raw[44:]; n = len(d)//2
if not n: print("  capture EMPTY"); raise SystemExit
v = struct.unpack("<%dh" % n, d[:n*2]); mono = v[0::2]
def g(s, f, r=48000.0):
    w = 2*math.pi*f/r; c = 2*math.cos(w); s1 = s2 = 0.0
    for x in s: s0 = x + c*s1 - s2; s2, s1 = s1, s0
    return math.sqrt(max(s1*s1 + s2*s2 - c*s1*s2, 0.0))/len(s)
seg = mono[:48000*10]
one = g(seg, 1000.0)
print("  peak=%d rms=%.0f goertzel1k=%.1f g300=%.1f -> %s" % (
    max(abs(x) for x in mono), math.sqrt(sum(float(x)*x for x in mono)/len(mono)),
    one, g(seg, 300.0), "TONE AUDIBLE" if one > 50 else "no tone"))
PY
    if python3 -c "
import struct,math,sys
raw=open('$CAP','rb').read()[44:]
n=len(raw)//2
v=struct.unpack('<%dh'%n,raw[:n*2])[0::2][:480000]
w=2*math.pi*1000/48000.0; c=2*math.cos(w); s1=s2=0.0
for x in v: s0=x+c*s1-s2; s2,s1=s1,s0
sys.exit(0 if math.sqrt(max(s1*s1+s2*s2-c*s1*s2,0))/len(v)>50 else 1)" 2>/dev/null; then
        echo "  >>> stopping ladder: tone detected at ${MS} ms"
        cleanup; exit 0
    fi
done
cleanup
echo "=== ladder done, no tone at 10/20/30 ==="

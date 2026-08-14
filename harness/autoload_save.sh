#!/bin/sh
# Drives the game from a cold start into a loaded save, unattended, so that the
# freezes the player sees in real gameplay can be measured instead of the
# attract-mode demo, where they do not occur (8.4 h without one on 2026-08-13).
#
# Route, as described by the player:
#   title screen        z                -> main menu (START/tab does NOT work)
#   main menu           DOWN once        -> "load game"
#   main menu           confirm          -> save list
#   save list           confirm          -> selects the save, opens a yes/no box
#   yes/no box          LEFT             -> moves the cursor onto "yes"
#   yes/no box          confirm          -> the save loads
#
# gptokeyb profile (mgs2.gptk) maps start=tab and a=z, so those are the keys.
# A screenshot is taken after every step into $OUT, because the only reliable way
# to know a menu accepted a key on this stack is to look.
#
# Gameplay walk defaults to "down": this save starts against the upper door, so
# "up" never leaves the wall or exposes the first guard. MGS2_WALK_KEY overrides
# the direction for a different save; MGS2_WALK_BURSTS controls its length and
# MGS2_WALK_HOLD / MGS2_WALK_GAP control each burst's timing.
# MGS2_WALK_SEQUENCE accepts comma-separated key:seconds steps and overrides
# the repeated-key form (for example down:2.3,right:1.4,right:1.4,up:1.0).
# MGS2_ACTION_COUNT enables a bounded post-walk action sequence; its key,
# press length and gap are controlled by MGS2_ACTION_KEY (default x / attack),
# MGS2_ACTION_HOLD and MGS2_ACTION_GAP.  It is disabled by default.
#
# Usage: autoload_save.sh [OUTDIR] [CONFIRM_KEY]
set -u
G=/storage/roms/ports/MGS2-Substance
OUT="${1:-/tmp/autoload}"
CONFIRM="${2:-z}"
LOG=/tmp/autoload-game.log
export XDG_RUNTIME_DIR=/var/run/0-runtime-dir WAYLAND_DISPLAY=wayland-1

mkdir -p "$OUT"
shot() { grim "$OUT/$1.png" 2>/dev/null; echo "  снимок $1"; }
key()  { python3 "$G/send_key.py" --hold 200 --gap 500 "$@" 2>&1 | tail -1; }

echo "== остановка и размотка =="
killall -9 launch-play.sh wine wine-preloader box86 box64 gptokeyb wineserver winedbg 2>/dev/null
sleep 4
rm -f /tmp/mgs2-substance.lock
for m in /usr/lib/wine/i386-windows/wined3d.dll /usr/lib/wine/i386-windows/user32.dll \
         /usr/lib/wine/i386-windows/d3d8.dll /usr/lib/wine/i386-windows/dmsynth.dll \
         /usr/lib/wine/i386-windows/dsound.dll /usr/lib/wine/i386-windows/dmime.dll \
         /usr/lib/wine/i386-windows/dmusic.dll /usr/lib/wine/i386-unix/winewayland.so \
         /usr/lib/wine/i386-unix/win32u.so /usr/lib/wine/i386-unix/opengl32.so \
         /usr/lib/wine/i386-unix/ntdll.so /usr/bin/box86; do
    while grep -q " $m " /proc/mounts; do umount "$m" || break; done
done

echo "== запуск =="
rm -f "$LOG"
cd /storage/roms/ports || exit 1
LAUNCHER="${MGS2_AUTOLOAD_LAUNCHER:-./MGS2-Substance.sh}"
echo "лаунчер: $LAUNCHER"
MGS2_GL_STATS=60 MGS2_PLAY_WINEDEBUG="-all,err+waylanddrv" \
    setsid nohup $LAUNCHER > "$LOG" 2>&1 < /dev/null &

# Wait for real frames rather than a fixed sleep: the driver prints a stats line
# every 60 frames, so two of them means the title screen is up and animating.
n=0
while [ "$n" -lt 150 ]; do
    frames=0
    [ -r "$LOG" ] && frames=$(grep -c 'present stats' "$LOG" 2>/dev/null || true)
    [ "${frames:-0}" -ge 2 ] && break
    n=$((n + 2)); sleep 2
done
echo "кадры пошли через ${n}c"
sleep 6
shot 0-title

echo "== ввод: одно uinput-устройство на всю последовательность =="
RECORD_PID=
if [ -n "${MGS2_CAPTURE_WAV:-}" ]; then
    RECORD_LOG="${MGS2_CAPTURE_WAV}.log"
    RECORD_TIMES="${MGS2_CAPTURE_WAV}.ticks"
    rm -f "$MGS2_CAPTURE_WAV" "$RECORD_LOG" "$RECORD_TIMES"
    pw-record --target "${MGS2_CAPTURE_SINK:-34}" \
        -P '{ stream.capture.sink=true }' --rate 48000 --channels 2 --format s16 \
        "$MGS2_CAPTURE_WAV" >"$RECORD_LOG" 2>&1 &
    RECORD_PID=$!
    python3 -c 'import time; print("start_tick=%d" % (time.monotonic() * 1000))' \
        >"$RECORD_TIMES"
    sleep 1
    echo "запись выхода: $MGS2_CAPTURE_WAV pid=$RECORD_PID"
fi
python3 "$G/autoload_save.py" "$OUT" "$CONFIRM"
if [ -n "$RECORD_PID" ]; then
    python3 -c 'import time; print("stop_tick=%d" % (time.monotonic() * 1000))' \
        >>"$RECORD_TIMES"
    kill -INT "$RECORD_PID" 2>/dev/null || true
    wait "$RECORD_PID" 2>/dev/null || true
    python3 -c 'import time; print("finalized_tick=%d" % (time.monotonic() * 1000))' \
        >>"$RECORD_TIMES"
fi

echo "== состояние =="
c=0; for p in /proc/[0-9]*; do
    [ "$(cat $p/comm 2>/dev/null)" = "mgs2_sse_rg353v" ] && c=$((c + 1)); done
echo "инстансов: $c"
grep -oE 'worst [0-9]+ ms' "$LOG" | awk '{print $2}' | sort -rn | head -3 | tr '\n' ' '
echo "(худшие кадры)"
echo "снимки в $OUT, лог игры $LOG"

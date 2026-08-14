#!/bin/sh
# Unattended freeze catcher. The 2026-08-12 capture showed the signature: every
# heavy thread stops accumulating CPU forever while the main thread keeps looping
# in an ntsync wait at a few ticks per second. So the detector sums utime+stime
# over ALL threads and fires when that sum barely moves.
#
# Normal running spends thousands of ticks per 20 s across four cores. The captured
# freeze left roughly 26 ticks per 20 s, all of it the main thread. The threshold
# below sits an order of magnitude away from both.
#
# On detection it runs freeze_capture.py, grabs a screenshot, and EXITS leaving the
# game frozen so the state survives for inspection. It never kills anything.
COMM=mgs2_sse_rg353v
GAME=/storage/roms/ports/MGS2-Substance
WINDOW="${1:-20}"          # seconds between comparisons
THRESHOLD="${2:-200}"      # ticks below which the process counts as stopped
OUT="${3:-/tmp/auto-freeze}"
LOG="${4:-/tmp/watchdog.log}"

find_pid() {
  for p in /proc/[0-9]*; do
    [ "$(cat $p/comm 2>/dev/null)" = "$COMM" ] && { echo "${p#/proc/}"; return; }
  done
}

total_ticks() {
  t=0
  for s in /proc/$1/task/*/stat; do
    set -- $(awk '{print $14, $15}' "$s" 2>/dev/null)
    [ -n "$1" ] && t=$((t + $1 + $2))
  done
  echo $t
}

P=""
while [ -z "$P" ]; do P=$(find_pid); [ -z "$P" ] && sleep 5; done
echo "$(date +%s) watchdog armed on pid $P, window ${WINDOW}s, threshold ${THRESHOLD} ticks" > "$LOG"

prev=$(total_ticks $P)
quiet=0
while [ -d "/proc/$P" ]; do
  sleep "$WINDOW"
  [ -d "/proc/$P" ] || break
  now=$(total_ticks $P)
  d=$((now - prev))
  prev=$now
  if [ "$d" -lt "$THRESHOLD" ]; then
    quiet=$((quiet + 1))
    echo "$(date +%s) QUIET window: $d ticks (strike $quiet)" >> "$LOG"
  else
    [ "$quiet" -gt 0 ] && echo "$(date +%s) recovered after $quiet strike(s), $d ticks" >> "$LOG"
    quiet=0
  fi
  # Two consecutive quiet windows: a recoverable multi-second stall cannot span
  # 40 s, so this is the permanent kind worth capturing.
  if [ "$quiet" -ge 2 ]; then
    stamp=$(date +%Y%m%d-%H%M%S)
    dir="${OUT}-${stamp}"
    echo "$(date +%s) FREEZE CONFIRMED, capturing into $dir" >> "$LOG"
    python3 "$GAME/freeze_capture.py" --pid "$P" --gap 6 --out "$dir" >> "$LOG" 2>&1
    XDG_RUNTIME_DIR=/var/run/0-runtime-dir WAYLAND_DISPLAY=wayland-1 \
        grim "$dir/screen.png" >> "$LOG" 2>&1
    cp /tmp/run.log "$dir/run.log" 2>/dev/null
    echo "$(date +%s) capture complete, watchdog exiting, game left frozen" >> "$LOG"
    exit 0
  fi
done
echo "$(date +%s) process gone (crash or exit) without a freeze signature" >> "$LOG"

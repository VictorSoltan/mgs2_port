#!/bin/sh
# Correlates per-thread CPU with the driver's own frame-time histogram inside ONE
# run, which the earlier pair of runs could not do. Each second it records the
# per-thread delta AND the newest "worst <N> ms" the driver has printed. When that
# number jumps, the surrounding samples are the stall, so the two measurements
# share a clock without needing to translate the driver's internal tick.
COMM=mgs2_sse_rg353v
OUT="${1:-/tmp/correlate.log}"
GAMELOG="${2:-/tmp/corr_game.log}"
P=""
while [ -z "$P" ]; do
  for p in /proc/[0-9]*; do
    [ "$(cat $p/comm 2>/dev/null)" = "$COMM" ] && P=${p#/proc/} && break
  done
  [ -z "$P" ] && sleep 3
done
echo "pid=$P start=$(date +%s)" > "$OUT"
echo "# ts total worstseen | per-thread deltas" >> "$OUT"
: > /tmp/.sc_prev
while [ -d "/proc/$P" ]; do
  : > /tmp/.sc_now
  for s in /proc/$P/task/*/stat; do
    tid=${s#/proc/$P/task/}; tid=${tid%/stat}
    set -- $(awk '{print $14, $15}' "$s" 2>/dev/null)
    [ -n "$1" ] && echo "$tid $(($1 + $2))" >> /tmp/.sc_now
  done
  line=""; tot=0
  while read tid cur; do
    prev=$(awk -v t="$tid" '$1==t{print $2}' /tmp/.sc_prev 2>/dev/null)
    [ -z "$prev" ] && prev=$cur
    d=$((cur - prev)); tot=$((tot + d))
    [ "$d" -gt 0 ] && line="$line ${tid}:$(cat /proc/$P/task/$tid/comm 2>/dev/null):${d}"
  done < /tmp/.sc_now
  # Monotonic count of frames over 500 ms. The per-window "worst" resets, so it
  # was always 0 by sampling time; a counter that only grows makes the exact
  # sample where a stall landed unambiguous.
  w=$(grep -oE 'over 50/100/200/500 ms: [0-9]+/[0-9]+/[0-9]+/[0-9]+' "$GAMELOG" 2>/dev/null \
        | awk -F'/' '{s+=$NF} END{print s+0}')
  echo "$(date +%s) $tot ${w:-0}$line" >> "$OUT"
  cp /tmp/.sc_now /tmp/.sc_prev
  sleep 1
done

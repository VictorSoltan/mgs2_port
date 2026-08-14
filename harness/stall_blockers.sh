#!/bin/sh
# Names what the render chain is blocked ON during the multi-second stalls.
# Measured first: during a stall the main thread, the hot game thread, wined3d_cs
# and mali-cmar-backe all stop accumulating CPU together while audio keeps
# running, so they are waiting, not computing. This records the pending syscall
# and wchan of exactly those four threads once a second.
#
# Deliberately four threads at 1 Hz, not fifty at 10 Hz: brief #28 records that
# unwinding kernel stacks for every thread ten times a second amplified the very
# freezes it measured. Four reads a second does not.
COMM=mgs2_sse_rg353v
OUT="${1:-/tmp/blockers.log}"
GAMELOG="${2:-/tmp/corr_game.log}"
P=""
while [ -z "$P" ]; do
  for p in /proc/[0-9]*; do
    [ "$(cat $p/comm 2>/dev/null)" = "$COMM" ] && P=${p#/proc/} && break
  done
  [ -z "$P" ] && sleep 3
done
# Pick the watched threads: the process main thread, wined3d_cs, mali-cmar-backe,
# and the busiest game thread by accumulated CPU.
sleep 45
MAIN=$P; CS=""; MALI=""; HOT=""; hotv=0
for t in /proc/$P/task/*; do
  tid=${t#/proc/$P/task/}
  c=$(cat $t/comm 2>/dev/null)
  [ "$c" = "wined3d_cs" ] && CS=$tid
  [ "$c" = "mali-cmar-backe" ] && MALI=$tid
  if [ "$c" = "$COMM" ] && [ "$tid" != "$P" ]; then
    v=$(awk '{print $14+$15}' $t/stat 2>/dev/null)
    [ -n "$v" ] && [ "$v" -gt "$hotv" ] && hotv=$v && HOT=$tid
  fi
done
echo "pid=$P main=$MAIN hot=$HOT cs=$CS mali=$MALI start=$(date +%s)" > "$OUT"
echo "# ts stalls total | tid=state:wchan:syscallnr:arg0" >> "$OUT"
prev_total=""
while [ -d "/proc/$P" ]; do
  tot=0
  for s in /proc/$P/task/*/stat; do
    set -- $(awk '{print $14, $15}' "$s" 2>/dev/null)
    [ -n "$1" ] && tot=$((tot + $1 + $2))
  done
  [ -z "$prev_total" ] && prev_total=$tot
  d=$((tot - prev_total)); prev_total=$tot
  st=$(grep -oE 'over 50/100/200/500 ms: [0-9]+/[0-9]+/[0-9]+/[0-9]+' "$GAMELOG" 2>/dev/null \
        | awk -F'/' '{s+=$NF} END{print s+0}')
  line=""
  for tid in $MAIN $HOT $CS $MALI; do
    [ -d "/proc/$P/task/$tid" ] || continue
    stt=$(awk '{print $3}' /proc/$P/task/$tid/stat 2>/dev/null)
    wc=$(cat /proc/$P/task/$tid/wchan 2>/dev/null)
    set -- $(cat /proc/$P/task/$tid/syscall 2>/dev/null)
    line="$line ${tid}=${stt}:${wc:-none}:${1:-?}:${2:-?}"
  done
  echo "$(date +%s) $st $d$line" >> "$OUT"
  sleep 1
done

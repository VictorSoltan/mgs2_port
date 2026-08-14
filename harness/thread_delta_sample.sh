#!/bin/sh
# Per-thread CPU deltas once a second, to answer one question about the
# multi-second stalls: during the stall, is some thread burning CPU (compute:
# box86 dynarec or guest code) or is nobody running (a wait)?
#
# One read of /proc/<pid>/task/*/stat per second. No wchan, no stack unwinding --
# brief #28 records that unwinding kernel stacks at 10 Hz amplified the very
# freezes it measured; this does not touch that path.
COMM=mgs2_sse_rg353v
OUT="${1:-/tmp/threads.log}"
P=""
while [ -z "$P" ]; do
  for p in /proc/[0-9]*; do
    [ "$(cat $p/comm 2>/dev/null)" = "$COMM" ] && P=${p#/proc/} && break
  done
  [ -z "$P" ] && sleep 3
done
echo "pid=$P start=$(date +%s)" > "$OUT"
echo "# ts total_delta  then per-thread: tid:comm:delta for every thread that moved" >> "$OUT"
: > /tmp/.td_prev
while [ -d "/proc/$P" ]; do
  : > /tmp/.td_now
  for s in /proc/$P/task/*/stat; do
    tid=${s#/proc/$P/task/}; tid=${tid%/stat}
    set -- $(awk '{print $14, $15}' "$s" 2>/dev/null)
    [ -n "$1" ] && echo "$tid $(($1 + $2))" >> /tmp/.td_now
  done
  line=""; tot=0
  while read tid cur; do
    prev=$(awk -v t="$tid" '$1==t{print $2}' /tmp/.td_prev 2>/dev/null)
    [ -z "$prev" ] && prev=$cur
    d=$((cur - prev))
    tot=$((tot + d))
    if [ "$d" -gt 0 ]; then
      c=$(cat /proc/$P/task/$tid/comm 2>/dev/null)
      line="$line ${tid}:${c}:${d}"
    fi
  done < /tmp/.td_now
  echo "$(date +%s) $tot$line" >> "$OUT"
  cp /tmp/.td_now /tmp/.td_prev
  sleep 1
done

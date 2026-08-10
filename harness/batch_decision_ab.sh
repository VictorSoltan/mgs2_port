#!/bin/bash
# One-process decision run for the final indexed-batcher questions.
#
# The DLL itself counts presents and prints once per second. This script only
# switches two files and parses exact new line ranges; it adds no hot-path
# timers, Wine debug channels or per-draw output.
set -u

LOG="${1:-/tmp/mgs2-batch10-launch.log}"
HASH_FILE=/tmp/mgs2-batch-hashcache
SKIP_FILE=/tmp/mgs2-batch-skip-draw
SETTLE="${SETTLE:-5}"
DWELL="${DWELL:-20}"
SKIP_DWELL="${SKIP_DWELL:-10}"
COMM=mgs2_sse_rg353v

alive() {
    for p in /proc/[0-9]*; do
        [ "$(cat "$p/comm" 2>/dev/null)" = "$COMM" ] && return 0
    done
    return 1
}

cleanup() {
    echo 0 > "$SKIP_FILE"
    echo 1 > "$HASH_FILE"
    rm -f "${WINDOW:-}"
}
trap cleanup EXIT INT TERM

[ -r "$LOG" ] || { echo "no readable log: $LOG" >&2; exit 1; }
alive || { echo "game not running" >&2; exit 1; }
WINDOW=$(mktemp /tmp/mgs2-decision-arm.XXXXXX)

echo "BATCH DECISION MANIFEST"
echo "  date       $(date -Is 2>/dev/null || date)"
echo "  log        $LOG"
echo "  wined3d    $(sha256sum /usr/lib/wine/i386-windows/wined3d.dll | cut -c1-16)"
echo "  d3d8       $(sha256sum /usr/lib/wine/i386-windows/d3d8.dll | cut -c1-16)"
echo "  cap        $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq)"
echo "  governor   $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)"
echo "  normal     ${DWELL}s after ${SETTLE}s settle"
echo "  no-draw    ${SKIP_DWELL}s after ${SETTLE}s settle"
echo
printf '%-9s %-7s %-9s %-8s %-8s %-9s %-10s %-8s %s\n' \
    arm fps frame_ms factor draws_s fast_s probes_s cap temp_c

capture_arm() {
    local label="$1" hash="$2" skip="$3" dwell="$4"
    local line0 line1 fps frame_ms factor draws fast probes cap temp

    echo "$hash" > "$HASH_FILE"
    echo "$skip" > "$SKIP_FILE"
    sleep "$SETTLE"
    line0=$(wc -l < "$LOG")
    sleep "$dwell"
    alive || { echo "game died during $label" >&2; return 1; }
    line1=$(wc -l < "$LOG")
    : > "$WINDOW"
    [ "$line1" -gt "$line0" ] && sed -n "$((line0 + 1)),${line1}p" "$LOG" > "$WINDOW"

    read -r fps factor draws <<<"$(grep 'MGS2BATCH:' "$WINDOW" | grep -v switched | awk '
        {rows++; for(i=1;i<=NF;i++){split($i,a,"=");
          if(a[1]=="fps")fps+=a[2]; if(a[1]=="draws")draws+=a[2];
          if(a[1]=="batches")batches+=a[2]}}
        END{if(rows && batches)printf "%.2f %.2f %d",fps/rows,draws/batches,draws/rows;
            else printf "- - -"}')"
    read -r fast probes <<<"$(grep 'MGS2CACHE:' "$WINDOW" | awk '
        {rows++; for(i=1;i<=NF;i++){split($i,a,"=");
          if(a[1]=="fast")fast+=a[2]; if(a[1]=="probes")probes+=a[2]}}
        END{if(rows)printf "%d %d",fast/rows,probes/rows;else printf "- -"}')"
    frame_ms="-"
    [ "$fps" != "-" ] && frame_ms=$(awk -v f="$fps" 'BEGIN{if(f>0)printf "%.2f",1000/f;else printf "-"}')
    cap=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq)
    temp=$(awk '{printf "%.1f",$1/1000}' /sys/class/thermal/thermal_zone0/temp)
    printf '%-9s %-7s %-9s %-8s %-8s %-9s %-10s %-8s %s\n' \
        "$label" "$fps" "$frame_ms" "$factor" "$draws" "$fast" "$probes" "$cap" "$temp"
}

echo 0 > "$SKIP_FILE"
for hash in 0 1 0 1; do
    capture_arm "hash${hash}" "$hash" 0 "$DWELL" || exit 1
done
capture_arm "no-draw" 1 1 "$SKIP_DWELL" || exit 1

echo 0 > "$SKIP_FILE"
sleep 2
echo
echo "normal drawing restored; hashcache left enabled"

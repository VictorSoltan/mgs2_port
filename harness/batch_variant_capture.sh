#!/bin/bash
# Capture one restart-time batch variant. Unlike batch_ab.sh this does not toggle
# anything: restart-hoist is fixed when Wine starts, so batch5 and batch6 require
# separate launches. All parsing is limited to the exact new log range produced
# during this window; stale telemetry from an earlier arm cannot leak in.
set -u

LABEL="${MGS2_CAPTURE_LABEL:-unknown}"
LOG="${1:-$(cat /tmp/mgs2-current-log 2>/dev/null)}"
DWELL="${DWELL:-25}"
SETTLE="${SETTLE:-5}"
COMM=mgs2_sse_rg353v

alive() { for p in /proc/[0-9]*; do [ "$(cat "$p/comm" 2>/dev/null)" = "$COMM" ] && return 0; done; return 1; }
[ -r "$LOG" ] || { echo "no readable log; pass it as \$1" >&2; exit 1; }
alive || { echo "game not running" >&2; exit 1; }

WINDOW=$(mktemp /tmp/mgs2-batch-variant.XXXXXX)
trap 'rm -f "$WINDOW"' EXIT

echo "BATCH VARIANT MANIFEST"
echo "  label      $LABEL"
echo "  date       $(date -Is 2>/dev/null || date)"
echo "  log        $LOG"
echo "  wined3d    $(sha256sum /usr/lib/wine/i386-windows/wined3d.dll | cut -c1-16)"
echo "  d3d8       $(sha256sum /usr/lib/wine/i386-windows/d3d8.dll | cut -c1-16)"
echo "  cap        $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq)"
echo "  governor   $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)"
echo "  dwell      ${DWELL}s after ${SETTLE}s settle"

sleep "$SETTLE"
line0=$(wc -l < "$LOG")
sleep "$DWELL"
alive || { echo "game died during capture" >&2; exit 1; }
line1=$(wc -l < "$LOG")
[ "$line1" -gt "$line0" ] && sed -n "$((line0 + 1)),${line1}p" "$LOG" > "$WINDOW"

fps=$(grep -E 'mgs_report_stats|MGS2FPS:' "$WINDOW" \
    | grep -oE '= [0-9.]+ fps' | grep -oE '[0-9.]+' \
    | awk '{n++;s+=$1} END{if(n)printf "%.2f",s/n; else printf "-"}')
frame_ms="-"
[ "$fps" != "-" ] && frame_ms=$(awk -v f="$fps" 'BEGIN{if(f>0)printf "%.2f",1000/f;else printf "-"}')

read -r factor draws_per_s <<<"$(grep 'MGS2BATCH:' "$WINDOW" | grep -v switched | awk '
    {rows++; for(i=1;i<=NF;i++){split($i,a,"="); if(a[1]=="draws")d+=a[2]; if(a[1]=="batches")b+=a[2]}}
    END{if(b>0)printf "%.2f %d",d/b,d/rows;else printf "- -"}')"

read -r build_ms upload_ms draw_ms <<<"$(grep 'MGS2BATCHPROFILE:' "$WINDOW" | awk '
    {rows++; for(i=1;i<=NF;i++){split($i,a,"="); gsub("ms","",a[2]);
      if(a[1]=="build")build+=a[2]; if(a[1]=="upload")upload+=a[2]; if(a[1]=="draw")draw+=a[2]}}
    END{if(rows)printf "%.2f %.2f %.2f",build/rows,upload/rows,draw/rows;else printf "- - -"}')"

printf 'RESULT label=%s fps=%s frame_ms=%s factor=%s draws_per_s=%s build_ms_s=%s upload_ms_s=%s draw_ms_s=%s temp_c=' \
    "$LABEL" "$fps" "$frame_ms" "$factor" "$draws_per_s" "$build_ms" "$upload_ms" "$draw_ms"
awk '{printf "%.1f",$1/1000}' /sys/class/thermal/thermal_zone0/temp
echo

#!/bin/bash
# Draw-batching A/B, ladder methodology: both arms in ONE process, on ONE spot, at
# ONE clock, interleaved so thermal drift cannot favour the same arm every time.
#
#   arm 1  consecutive non-indexed GL_TRIANGLE_STRIP draws merged into one
#          glDrawElements with GL_PRIMITIVE_RESTART_FIXED_INDEX separators
#   arm 0  identical binary, merging disabled -- so this measures the patch and
#          not the build
#
# Run it with the game already at the fixed spot (Game Data 02, open Plant) and
# the owner standing still. Milliseconds, not fps: only ms add up against the
# ~103 ms that heavy Plant has to shed.
set -u
FILE=/tmp/mgs2-batch
LOG="${1:-$(cat /tmp/mgs2-current-log 2>/dev/null)}"
DWELL="${DWELL:-25}"
SETTLE="${SETTLE:-5}"
COMM=mgs2_sse_rg353v

alive() { for p in /proc/[0-9]*; do [ "$(cat "$p/comm" 2>/dev/null)" = "$COMM" ] && return 0; done; return 1; }
[ -r "$LOG" ] || { echo "no readable log; pass it as \$1" >&2; exit 1; }
alive || { echo "game not running" >&2; exit 1; }

echo "A/B MANIFEST"
echo "  date       $(date -Is 2>/dev/null || date)"
echo "  log        $LOG"
echo "  wined3d    $(sha256sum /usr/lib/wine/i386-windows/wined3d.dll | cut -c1-16)"
echo "  d3d8       $(sha256sum /usr/lib/wine/i386-windows/d3d8.dll | cut -c1-16)"
echo "  cap        $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq)"
echo "  governor   $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)"
echo "  dwell      ${DWELL}s after ${SETTLE}s settle"
echo

printf '%-5s %-9s %-9s %-8s %-9s %-7s %s\n' arm fps ms d_vs_off factor temp draws/s
OFF_MS=""
for arm in ${ARMS:-0 1 1 0 0 1 1 0}; do
    echo "$arm" > "$FILE"
    sleep "$SETTLE"
    n0=$(grep -Ec 'mgs_report_stats|MGS2FPS:' "$LOG")
    sleep "$DWELL"
    alive || { echo "game died during arm $arm" >&2; break; }
    n1=$(grep -Ec 'mgs_report_stats|MGS2FPS:' "$LOG")

    read -r fps <<<"$(tail -n $(( (n1-n0)*40 + 200 )) "$LOG" \
        | grep -E 'mgs_report_stats|MGS2FPS:' \
        | grep -oE '= [0-9.]+ fps|= [0-9.]+ fps' | grep -oE '[0-9.]+' \
        | tail -n $((n1-n0)) | awk '{n++;s+=$1} END{if(n)printf "%.1f",s/n; else printf "-"}')"
    ms="-"; d="-"
    if [ "$fps" != "-" ]; then
        ms=$(awk -v f="$fps" 'BEGIN{printf "%.1f", 1000/f}')
        [ "$arm" = 0 ] && [ -z "$OFF_MS" ] && OFF_MS=$ms
        [ -n "$OFF_MS" ] && d=$(awk -v a="$ms" -v b="$OFF_MS" 'BEGIN{printf "%+.1f", a-b}')
    fi
    read -r fac dps <<<"$(grep MGS2BATCH "$LOG" | grep -v switched | tail -$((DWELL/1>8?8:DWELL)) | awk '
        {for(i=1;i<=NF;i++){split($i,a,"="); if(a[1]=="draws")d+=a[2]; if(a[1]=="batches")b+=a[2]}}
        END{if(b>0) printf "%.2fx %d", d/b, d/NR; else printf "- -"}')"
    printf '%-5s %-9s %-9s %-8s %-9s %-7s %s\n' "$arm" "$fps" "$ms" "$d" "$fac" \
        "$(awk '{printf "%.1f", $1/1000}' /sys/class/thermal/thermal_zone0/temp)" "$dps"
done
echo 1 > "$FILE"
echo
echo "Every arm-0 row must land near the other arm-0 rows. If they do not, the scene"
echo "or the temperature drifted and the run is void."

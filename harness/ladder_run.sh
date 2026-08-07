#!/bin/bash
# Walk the renderer no-op ladder in one run, on one scene.
#
# Run this on the device with the game ALREADY at the fixed spot and standing
# still. It does not launch or restart anything: the whole point of the rung file
# is that baseline, A, B and C are measured on one process, one scene and one
# thermal state, so nothing here may relaunch the game.
#
#   Reference spot: save slot "Game Data 02" is the open Plant area (the heavy
#   one, 6-17 fps). Load it, stand still, then run this.
#
# Prerequisites, all set by ladder_launch below or by hand:
#   MGS2_WINED3D_DLL=wined3d_ladder1.dll  MGS2_D3D8_DLL=d3d8_ladder1.dll
#   MGS2_FREQ_STEPS="1416000"     pin the clock or this measures temperature
#   MGS2_GL_STATS=60              fps from the presenter
#   WINEDEBUG="-all,err+waylanddrv,err+d3d8"
#
# Why rung C is not MGS2_SKIP_ALL_DRAWS: that gate is compiled to false in the
# release build, so using it would measure the diagnostic build instead, which
# carries ~30 extra calls per draw. See brief #30.
set -u

RUNG_FILE="${MGS2_LADDER_FILE_UNIX:-/tmp/mgs2-ladder}"
LOG="${1:-$(cat /tmp/mgs2-current-log 2>/dev/null)}"
DWELL="${DWELL:-90}"
SETTLE="${SETTLE:-12}"   # discard this many seconds after each flip

COMM=mgs2_sse_rg353v
alive() { for p in /proc/[0-9]*; do [ "$(cat "$p/comm" 2>/dev/null)" = "$COMM" ] && return 0; done; return 1; }

if [ -z "$LOG" ] || [ ! -r "$LOG" ]; then
    echo "no readable game log; pass it as \$1" >&2; exit 1
fi
if ! alive; then
    echo "game is not running: load Game Data 02, stand at the spot, then rerun" >&2; exit 1
fi

# Mean of the fps samples the presenter emitted during the window, ignoring the
# settle period. Median would be better but this has to run on busybox awk.
window_fps() {
    local since=$1
    awk -v since="$since" '
        /= [0-9.]+ fps/ {
            if (++n > since) { match($0, /= [0-9.]+ fps/); s=substr($0,RSTART+2,RLENGTH-6); sum+=s; c++
                               if (min=="" || s+0<min) min=s+0; if (s+0>max) max=s+0 }
        }
        END { if (c) printf "%.1f %.1f %.1f %d", sum/c, min, max, c; else printf "- - - 0" }
    ' "$LOG"
}

printf '%-9s %-8s %-8s %-8s %-6s %-7s %-6s %s\n' rung mean_fps min max samples temp_C cap draws_per_s
for rung in 0 A B C 0; do
    echo "$rung" > "$RUNG_FILE"
    base=$(grep -c "= [0-9.]* fps" "$LOG" 2>/dev/null || echo 0)
    sleep "$SETTLE"
    settled=$(grep -c "= [0-9.]* fps" "$LOG" 2>/dev/null || echo 0)
    sleep "$DWELL"
    alive || { echo "game died during rung $rung -- check the thermal guard log" >&2; break; }

    read -r mean min max n <<<"$(window_fps "$settled")"
    printf '%-9s %-8s %-8s %-8s %-6s %-7s %-6s %s\n' \
        "$rung" "$mean" "$min" "$max" "$n" \
        "$(awk '{printf "%.1f", $1/1000}' /sys/class/thermal/thermal_zone0/temp)" \
        "$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq)" \
        "$(grep -oE 'D3D8STAT tick=[0-9]+ draws=[0-9]+' "$LOG" | tail -1 | grep -oE '[0-9]+$')"
done
echo 0 > "$RUNG_FILE"

cat <<'NOTE'

Reading it, per the external review's own threshold:
  A gains < ~5% fps          stop looking for 25% in the renderer; the cost is
                             game logic under Box86. Go after that instead.
  A gains > 15-20% and B     the D3D8 -> CS producer path is worth optimising
    takes back much of it
  C close to baseline        the cost is producer-side, not GPU or driver
  C much faster than B       real GL state application and the driver are dear
The final 0 row must land near the first. If it does not, the scene or the
temperature drifted and the run is void -- fix that before believing any of it.
NOTE

#!/bin/bash
# Renderer decomposition ladder: how many milliseconds of the frame each layer
# between the game's DrawPrimitive and the real glDraw* actually costs.
#
# Run this on the device with the game ALREADY at the fixed spot and standing
# still. It never launches or restarts anything: the point of the rung file is
# that every rung is measured in one process, on one scene, at one temperature.
#
#   Reference spot: save slot "Game Data 02", the open Plant area (6-17 fps).
#
# Rung semantics, established from the source rather than assumed:
#
#   0   baseline, nothing disabled
#   A   d3d8 Draw* returns before the mutex, managed textures, sysmem upload,
#       set_primitive_type and apply_stateblock -- so no D3D8 work at all
#   B   all of that runs, apply_stateblock included, but
#       wined3d_device_context_draw is not called: no emit_draw, no resource
#       references, no CS packet
#   R   emit_draw runs and publishes the packet, but the resource walk
#       (reference_graphics_pipeline_resources) is skipped
#   C   packet is built, published and consumed; draw_primitive returns at once,
#       so consumer state application and all GL work are skipped
#
# The differences are the point, not the absolute numbers:
#
#   0 - C   consumer state application + GL + driver
#   C - R   the resource walk: slot scans and access_time stamps
#   R - B   packet allocation, queue publish, consumer dequeue
#   B - A   d3d8 producer preparation: mutex, managed scan, sysmem, stateblock
#   A       game logic + Box86 + audio + message loop + everything else
#
# A, B, R and C are all diagnostic. R in particular is unsafe by construction --
# the consumer may run against resources whose lifetime is no longer held. Fine
# for a 30 s window, never a shipping setting.
#
# Milliseconds, not fps. 26.6 -> 41.4 fps sounds like +56%; as frame time it is
# 37.6 -> 24.2 ms, i.e. 13.4 ms saved, and only milliseconds add up against the
# ~61 ms that heavy Plant needs to shed to reach 24 fps.
set -u

RUNG_FILE="${MGS2_LADDER_FILE_UNIX:-/tmp/mgs2-ladder}"
LOG="${1:-$(cat /tmp/mgs2-current-log 2>/dev/null)}"
DWELL="${DWELL:-25}"
SETTLE="${SETTLE:-5}"

COMM=mgs2_sse_rg353v
alive() { for p in /proc/[0-9]*; do [ "$(cat "$p/comm" 2>/dev/null)" = "$COMM" ] && return 0; done; return 1; }
gamepid() { for p in /proc/[0-9]*; do [ "$(cat "$p/comm" 2>/dev/null)" = "$COMM" ] && basename "$p"; done | head -1; }

if [ -z "$LOG" ] || [ ! -r "$LOG" ]; then
    echo "no readable game log; pass it as \$1" >&2; exit 1
fi
alive || { echo "game is not running: load Game Data 02, stand at the spot, then rerun" >&2; exit 1; }
PID=$(gamepid)

# Manifest first. A ladder whose rungs came from different binaries measures the
# binaries, so record exactly what is loaded before any number is produced.
echo "LADDER MANIFEST"
echo "  date        $(date -Is 2>/dev/null || date)"
echo "  pid         $PID"
echo "  log         $LOG"
echo "  cpu_max     $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq 2>/dev/null)"
echo "  governor    $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null)"
echo "  temp_start  $(awk '{printf "%.1f", $1/1000}' /sys/class/thermal/thermal_zone0/temp 2>/dev/null)"
echo "  WINEDEBUG   ${WINEDEBUG:-<unset>}"
echo "  dwell/settle ${DWELL}s / ${SETTLE}s"
for m in /usr/lib/wine/i386-windows/wined3d.dll /usr/lib/wine/i386-windows/d3d8.dll; do
    [ -r "$m" ] && echo "  $(basename "$m") $(sha256sum "$m" 2>/dev/null | cut -c1-16)"
done
echo

# Per-thread CPU, so a rung that moves work between threads is visible rather
# than hidden inside one total. schedstat also separates "computing" from "ready
# but not scheduled", which plain %CPU cannot.
thread_ticks() {
    local pid=$1 out=""
    for t in /proc/$pid/task/*; do
        local n u
        n=$(cat "$t/comm" 2>/dev/null) || continue
        u=$(awk '{print $14+$15}' "$t/stat" 2>/dev/null) || continue
        case "$n" in
            "$COMM"|wined3d_cs|wine_dsound_mix) out="$out $n:$u" ;;
        esac
    done
    echo "$out"
}
sched_wait() {
    local pid=$1 sum=0 v
    for t in /proc/$pid/task/*; do
        v=$(awk '{print $2}' "$t/schedstat" 2>/dev/null) || continue
        sum=$((sum + v))
    done
    echo "$sum"
}

# Frame times come from the presenter's own line; fall back to the facade's
# counter if this is a Hangover run.
frames_so_far() { grep -cE "MGS2 present stats|MGS2FPS:" "$LOG" 2>/dev/null; }
fps_window() {
    tail -n "$1" "$LOG" 2>/dev/null | grep -oE "= [0-9.]+ fps" | grep -oE "[0-9.]+" | awk '
        {n++; s+=$1; if (min=="" || $1<min) min=$1; if ($1>max) max=$1}
        END {if (n) printf "%.1f %.1f %.1f %d", s/n, min, max, n; else printf "- - - 0"}'
}

printf '%-6s %-9s %-9s %-8s %-7s %-6s %s\n' \
    rung mean_fps mean_ms d_ms_vs0 temp cap threads
BASE_MS=""

# Interleaved, and reversed, and shuffled: thermal and any slow system drift then
# cannot favour the same rung every time.
for rung in 0 A B R C  C R B A 0  B 0 C A R; do
    echo "$rung" > "$RUNG_FILE"
    sleep "$SETTLE"
    before=$(frames_so_far); t0=$(thread_ticks "$PID"); w0=$(sched_wait "$PID")
    sleep "$DWELL"
    alive || { echo "game died during rung $rung -- check the thermal guard log" >&2; break; }
    after=$(frames_so_far); t1=$(thread_ticks "$PID"); w1=$(sched_wait "$PID")

    read -r mean min max n <<<"$(fps_window $((after - before + 2)))"
    ms="-"; d="-"
    if [ "$mean" != "-" ]; then
        ms=$(awk -v f="$mean" 'BEGIN{if (f>0) printf "%.1f", 1000/f; else printf "-"}')
        [ "$rung" = "0" ] && [ -z "$BASE_MS" ] && BASE_MS=$ms
        [ -n "$BASE_MS" ] && d=$(awk -v a="$ms" -v b="$BASE_MS" 'BEGIN{printf "%+.1f", a-b}')
    fi
    printf '%-6s %-9s %-9s %-8s %-7s %-6s %s\n' \
        "$rung" "$mean" "$ms" "$d" \
        "$(awk '{printf "%.1f", $1/1000}' /sys/class/thermal/thermal_zone0/temp)" \
        "$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq)" \
        "$(echo "$t1" | tr ' ' '\n' | grep -c :)t wait+$(( (w1 - w0) / 1000000 ))ms"
done
echo 0 > "$RUNG_FILE"

cat <<'NOTE'

Read the differences, not the rows:

  0 - C   consumer state application + GL + driver
  C - R   the resource walk (slot scans, access_time stamps)
  R - B   packet allocation, queue publish, consumer dequeue
  B - A   d3d8 producer preparation (mutex, managed scan, sysmem, stateblock)
  A       game logic, Box86, audio, message loop

Heavy Plant is ~103 ms and needs ~61 ms removed for 24 fps, ~70 ms for 30. So:
   2 ms   interesting, does not solve the target
   5 ms   a good micro patch
  15 ms   a serious layer
  30 ms   a major bottleneck
  60 ms   a path to 24 fps actually exists

Every rung 0 must land near the others. If they do not, the scene or the
temperature drifted and the whole run is void -- fix that before believing any
of it. And do not use this run for a batchability census: telemetry has to be
proven free before its fps can be trusted.
NOTE

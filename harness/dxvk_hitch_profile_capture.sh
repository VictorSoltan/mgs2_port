#!/bin/sh
# Bounded all-thread perf capture of the visually gated DXVK hitch route.
# All game-thread instrumentation stays off. Frame gaps, perf samples and the
# optional Box86 guest/native map are read externally and use CLOCK_MONOTONIC.
set -u

G=/storage/roms/ports/MGS2-Substance
STAMP=$(date +%Y%m%d-%H%M%S)
OUT="${1:-/storage/roms/ports/ablogs/dxvk-hitch-profile-$STAMP}"
LAUNCHER="${MGS2_PROFILE_LAUNCHER:-./MGS2-Substance/launch-dxvk-sarek.sh}"
BOX86_BIN="${MGS2_PROFILE_BOX86:-box86-fp17-dxvk-quiet}"

if [ -e "$OUT" ]; then
    echo "refusing existing output directory: $OUT" >&2
    exit 2
fi
mkdir -p "$(dirname "$OUT")" || exit 1
mkdir "$OUT" || exit 1

AUTO_PID=
PRESENT_PID=
WAIT_PID=
PRESSURE_PID=
GAP_TRIGGER_PID=
ASYNC_SKIP_PID=
PERF_PID=
snapshot_processes() {
    output="$1"
    {
        echo 'pid\tcomm\tproc_stat'
        for process in /proc/[0-9]*; do
            [ -r "$process/stat" ] || continue
            pid=${process#/proc/}
            comm=$(cat "$process/comm" 2>/dev/null) || continue
            stat=$(cat "$process/stat" 2>/dev/null) || continue
            printf '%s\t%s\t%s\n' "$pid" "$comm" "$stat"
        done
    } >"$output"
}
snapshot_state_cache() {
    output="$1"
    cache_path="${DXVK_STATE_CACHE_PATH:-}"
    {
        printf 'DXVK_STATE_CACHE=%s\n' "${DXVK_STATE_CACHE:-0}"
        printf 'DXVK_STATE_CACHE_PATH=%s\n' "$cache_path"
        if [ -z "$cache_path" ]; then
            echo 'cache_snapshot=no-explicit-path'
        elif [ ! -d "$cache_path" ]; then
            echo 'cache_snapshot=directory-missing'
        else
            found=0
            for cache_file in "$cache_path"/*.dxvk-cache; do
                [ -f "$cache_file" ] || continue
                found=1
                stat -c 'file=%n size=%s mtime=%Y' "$cache_file"
                sha256sum "$cache_file"
            done
            [ "$found" -eq 1 ] || echo 'cache_snapshot=no-cache-files'
        fi
    } >"$output"
}
cleanup() {
    [ -n "$PERF_PID" ] && kill -INT "$PERF_PID" 2>/dev/null || true
    [ -n "$ASYNC_SKIP_PID" ] && kill "$ASYNC_SKIP_PID" 2>/dev/null || true
    [ -n "$GAP_TRIGGER_PID" ] && kill "$GAP_TRIGGER_PID" 2>/dev/null || true
    [ -n "$PRESSURE_PID" ] && kill "$PRESSURE_PID" 2>/dev/null || true
    [ -n "$WAIT_PID" ] && kill "$WAIT_PID" 2>/dev/null || true
    [ -n "$PRESENT_PID" ] && kill "$PRESENT_PID" 2>/dev/null || true
    [ -n "$AUTO_PID" ] && kill "$AUTO_PID" 2>/dev/null || true
}
snapshot_platform() {
    output="$1"
    {
        printf 'tick_ms='; awk '{printf "%.0f\n", $1 * 1000}' /proc/uptime
        uname -a
        printf 'dev_ntsync='; ls -l /dev/ntsync 2>&1
        for file in \
                /sys/devices/platform/fde60000.gpu/js_scheduling_period \
                /sys/devices/platform/fde60000.gpu/js_timeouts \
                /sys/devices/platform/fde60000.gpu/reset_timeout \
                /sys/devices/platform/fde60000.gpu/soft_job_timeout; do
            [ -r "$file" ] || continue
            printf '%s=' "$file"
            cat "$file"
        done
    } >"$output"
    dmesg 2>/dev/null | grep -Ei \
        'mali|kbase|soft.?stop|hard.?stop|gpu.*(fault|reset|timeout)|mmu.*fault|job slot|oom notifier|mmc.*(error|timeout)|sdhci.*(error|timeout)|I/O error' \
        >"${output%.txt}-kernel-events.txt" || true
}
trap cleanup INT TERM EXIT

if [ "${MGS2_PROFILE_PLATFORM:-0}" = 1 ]; then
    snapshot_platform "$OUT/platform-before.txt"
fi
snapshot_state_cache "$OUT/state-cache-before.txt"

MGS2_AUTOLOAD_LOG="$OUT/game.log" \
MGS2_AUTOLOAD_LAUNCHER="$LAUNCHER" \
MGS2_BOX86_BIN="$BOX86_BIN" \
MGS2_BOX86_GUEST_MAP=1 \
MGS2_WALK_BURSTS="${MGS2_WALK_BURSTS:-4}" \
MGS2_WALK_HOLD="${MGS2_WALK_HOLD:-2.5}" \
MGS2_WALK_GAP="${MGS2_WALK_GAP:-1.5}" \
DXVK_STATE_CACHE="${DXVK_STATE_CACHE:-0}" \
    setsid nohup sh "$G/autoload_save.sh" "$OUT/shots" z \
    >"$OUT/autoload.log" 2>&1 < /dev/null &
AUTO_PID=$!

# autoload kills the old process before this marker. Waiting for any matching
# comm would race against that corpse and attach perf to the wrong PID.
n=0
while [ "$n" -lt 120 ]; do
    grep -q 'renderer-ready=dxvk-d3d9' "$OUT/autoload.log" 2>/dev/null && break
    kill -0 "$AUTO_PID" 2>/dev/null || break
    n=$((n + 1))
    sleep 1
done

PID=
for process in /proc/[0-9]*; do
    [ "$(cat "$process/comm" 2>/dev/null)" = mgs2_sse_rg353v ] && \
        PID=${process#/proc/}
done
[ -n "$PID" ] || {
    echo "new game process did not become ready" >&2
    cat "$OUT/autoload.log" >&2
    exit 1
}
echo "pid=$PID renderer_ready_after=${n}s" | tee "$OUT/identity.txt"
readlink -f "/proc/$PID/exe" | tee -a "$OUT/identity.txt"
sha256sum "/proc/$PID/exe" | tee -a "$OUT/identity.txt"
tr '\0' '\n' <"/proc/$PID/environ" | \
    grep -E '^(MGS2_(PEEK_(HOT|WAIT|WAIT_MS)|WAIT_CENSUS|SLEEP0_WAIT_MS)|DXVK_(ASYNC|STATE_CACHE|STATE_CACHE_PATH|ALL_CORES|CONFIG|HUD)|ASYNC_DRAW_CALL_THRESHOLD)=' | sort | \
    tee -a "$OUT/identity.txt"
d3d9_path=$(awk '$NF ~ /\/d3d9\.dll$/ { print $NF; exit }' "/proc/$PID/maps")
if [ -n "$d3d9_path" ]; then
    echo "d3d9_path=$d3d9_path" | tee -a "$OUT/identity.txt"
    sha256sum "$d3d9_path" | tee -a "$OUT/identity.txt"
else
    echo "d3d9_path=missing" | tee -a "$OUT/identity.txt"
fi
user32_path=$(awk '$NF ~ /\/user32\.dll$/ { print $NF; exit }' "/proc/$PID/maps")
if [ -n "$user32_path" ]; then
    echo "user32_path=$user32_path" | tee -a "$OUT/identity.txt"
    sha256sum "$user32_path" | tee -a "$OUT/identity.txt"
else
    echo "user32_path=missing" | tee -a "$OUT/identity.txt"
fi
kernelbase_path=$(awk '$NF ~ /\/kernelbase\.dll$/ { print $NF; exit }' "/proc/$PID/maps")
if [ -n "$kernelbase_path" ]; then
    echo "kernelbase_path=$kernelbase_path" | tee -a "$OUT/identity.txt"
    sha256sum "$kernelbase_path" | tee -a "$OUT/identity.txt"
else
    echo "kernelbase_path=missing" | tee -a "$OUT/identity.txt"
fi
cp "/proc/$PID/maps" "$OUT/maps.before"
snapshot_processes "$OUT/processes-before.tsv"

python3 "$G/dxvk_present_count.py" "$PID" --interval 0.01 --windows 24000 \
    >"$OUT/present.tsv" 2>&1 &
PRESENT_PID=$!

if [ "${MGS2_PROFILE_WAIT_CENSUS:-${MGS2_WAIT_CENSUS:-0}}" = 1 ]; then
    python3 "$G/wait_census_read.py" "$PID" --interval 0.02 --windows 12000 \
        >"$OUT/wait-census.tsv" 2>&1 &
    WAIT_PID=$!
fi

python3 "$G/device_pressure_count.py" "$PID" --interval 0.1 --windows 2400 \
    >"$OUT/device-pressure.tsv" 2>&1 &
PRESSURE_PID=$!

if [ "${MGS2_PROFILE_GAP_TRIGGER:-0}" = 1 ]; then
    python3 "$G/dxvk_gap_trigger_capture.py" "$PID" --interval 0.01 \
        --windows 24000 --thresholds-ms "${MGS2_GAP_TRIGGER_THRESHOLDS_MS:-500,1200}" \
        --probe-ms "${MGS2_GAP_TRIGGER_PROBE_MS:-25}" \
        >"$OUT/gap-trigger.txt" 2>&1 &
    GAP_TRIGGER_PID=$!
fi

if [ "${MGS2_PROFILE_ASYNC_SKIP:-0}" = 1 ]; then
    python3 "$G/dxvk_async_skip_capture.py" "$PID" --interval 0.01 \
        --windows 24000 --max-events "${MGS2_ASYNC_SKIP_MAX_EVENTS:-4096}" \
        >"$OUT/async-skip.txt" 2>&1 &
    ASYNC_SKIP_PID=$!
fi

if [ "${MGS2_PROFILE_PERF:-1}" = 1 ]; then
    echo -1 > /proc/sys/kernel/perf_event_paranoid 2>/dev/null || true
    perf record -k mono -F 199 -e cycles -p "$PID" \
        --proc-map-timeout 10000 -o "$OUT/perf.data" -- sleep 240 \
        >"$OUT/perf-record.log" 2>&1 &
    PERF_PID=$!
fi

wait "$AUTO_PID"
AUTO_RC=$?
AUTO_PID=

if [ -n "$PERF_PID" ]; then
    kill -INT "$PERF_PID" 2>/dev/null || true
    wait "$PERF_PID" 2>/dev/null || true
    PERF_PID=
fi
kill "$PRESENT_PID" 2>/dev/null || true
wait "$PRESENT_PID" 2>/dev/null || true
PRESENT_PID=
if [ -n "$WAIT_PID" ]; then
    kill "$WAIT_PID" 2>/dev/null || true
    wait "$WAIT_PID" 2>/dev/null || true
    WAIT_PID=
fi
kill "$PRESSURE_PID" 2>/dev/null || true
wait "$PRESSURE_PID" 2>/dev/null || true
PRESSURE_PID=
if [ -n "$GAP_TRIGGER_PID" ]; then
    kill "$GAP_TRIGGER_PID" 2>/dev/null || true
    wait "$GAP_TRIGGER_PID" 2>/dev/null || true
    GAP_TRIGGER_PID=
fi
if [ -n "$ASYNC_SKIP_PID" ]; then
    kill "$ASYNC_SKIP_PID" 2>/dev/null || true
    wait "$ASYNC_SKIP_PID" 2>/dev/null || true
    ASYNC_SKIP_PID=
fi
snapshot_processes "$OUT/processes-after.tsv"
snapshot_state_cache "$OUT/state-cache-after.txt"
if [ "${MGS2_PROFILE_PLATFORM:-0}" = 1 ]; then
    snapshot_platform "$OUT/platform-after.txt"
fi

# Snapshot while the exact process and its JIT mappings still exist.
cp "/proc/$PID/maps" "$OUT/maps"
python3 "$G/box86_guest_snapshot.py" --pid "$PID" --box86 "/proc/$PID/exe" \
    --output "$OUT/guest-map.bin" >"$OUT/guest-map.txt" 2>&1 || true
# Candidate-only bounded state.  Older controls do not export these symbols;
# their read failure is retained in the artifact rather than changing the run.
python3 "$G/box86_dxt_stats.py" --pid "$PID" --box86 "/proc/$PID/exe" \
    >"$OUT/dxt-stats.txt" 2>&1 || true
python3 "$G/dxvk_present_trace_analyze.py" "$OUT/present.tsv" \
    --markers "$OUT/autoload.log" --top 20 >"$OUT/present-summary.txt"
python3 "$G/dxvk_device_gap_analyze.py" "$OUT/present.tsv" \
    "$OUT/device-pressure.tsv" --markers "$OUT/autoload.log" --top 20 \
    >"$OUT/device-gaps.txt"
if [ -r "$OUT/wait-census.tsv" ]; then
    python3 "$G/dxvk_wait_gap_analyze.py" "$OUT/present.tsv" \
        "$OUT/wait-census.tsv" --markers "$OUT/autoload.log" \
        --top-gaps 20 --top-waits 12 >"$OUT/wait-gaps.txt"
fi
if [ -r "$OUT/perf.data" ]; then
    perf script -i "$OUT/perf.data" -F comm,pid,tid,time,ip,sym,dso \
        >"$OUT/perf.script" 2>"$OUT/perf-script.log"
    python3 "$G/dxvk_perf_gap_analyze.py" "$OUT/present.tsv" "$OUT/perf.script" \
        --markers "$OUT/autoload.log" --top 20 >"$OUT/perf-gaps.txt"
fi

printf 'autoload_rc=%d\n' "$AUTO_RC" | tee -a "$OUT/identity.txt"
grep -E 'menu-marker|save-marker|yes-no saturation|screen-gray-mean|RuntimeError' \
    "$OUT/autoload.log" | tee "$OUT/route-gates.txt"
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq \
    >"$OUT/cpu-frequency-end.txt"
cat /sys/class/thermal/thermal_zone0/temp >"$OUT/temperature-end.txt"
echo "capture=$OUT"

trap - INT TERM EXIT
killall -9 wine wine-preloader box86 box64 gptokeyb wineserver winedbg \
    2>/dev/null || true
rm -f /tmp/mgs2-substance.lock
exit "$AUTO_RC"

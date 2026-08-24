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
PERF_PID=
cleanup() {
    [ -n "$PERF_PID" ] && kill -INT "$PERF_PID" 2>/dev/null || true
    [ -n "$PRESENT_PID" ] && kill "$PRESENT_PID" 2>/dev/null || true
    [ -n "$AUTO_PID" ] && kill "$AUTO_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

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
cp "/proc/$PID/maps" "$OUT/maps.before"

python3 "$G/dxvk_present_count.py" "$PID" --interval 0.01 --windows 24000 \
    >"$OUT/present.tsv" 2>&1 &
PRESENT_PID=$!

echo -1 > /proc/sys/kernel/perf_event_paranoid 2>/dev/null || true
perf record -k mono -F 199 -e cycles -p "$PID" \
    --proc-map-timeout 10000 -o "$OUT/perf.data" -- sleep 240 \
    >"$OUT/perf-record.log" 2>&1 &
PERF_PID=$!

wait "$AUTO_PID"
AUTO_RC=$?
AUTO_PID=

kill -INT "$PERF_PID" 2>/dev/null || true
wait "$PERF_PID" 2>/dev/null || true
PERF_PID=
kill "$PRESENT_PID" 2>/dev/null || true
wait "$PRESENT_PID" 2>/dev/null || true
PRESENT_PID=

# Snapshot while the exact process and its JIT mappings still exist.
cp "/proc/$PID/maps" "$OUT/maps"
python3 "$G/box86_guest_snapshot.py" --pid "$PID" --box86 "/proc/$PID/exe" \
    --output "$OUT/guest-map.bin" >"$OUT/guest-map.txt" 2>&1 || true
# Candidate-only bounded state.  Older controls do not export these symbols;
# their read failure is retained in the artifact rather than changing the run.
python3 "$G/box86_dxt_stats.py" --pid "$PID" --box86 "/proc/$PID/exe" \
    >"$OUT/dxt-stats.txt" 2>&1 || true
perf script -i "$OUT/perf.data" -F comm,pid,tid,time,ip,sym,dso \
    >"$OUT/perf.script" 2>"$OUT/perf-script.log"
python3 "$G/dxvk_present_trace_analyze.py" "$OUT/present.tsv" \
    --markers "$OUT/autoload.log" --top 20 >"$OUT/present-summary.txt"
python3 "$G/dxvk_perf_gap_analyze.py" "$OUT/present.tsv" "$OUT/perf.script" \
    --markers "$OUT/autoload.log" --top 20 >"$OUT/perf-gaps.txt"

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

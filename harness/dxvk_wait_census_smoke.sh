#!/bin/sh
# Short no-input device smoke test for the research wait-census kernelbase.
set -u

G=/storage/roms/ports/MGS2-Substance
OUT="${1:-/storage/roms/ports/ablogs/dxvk-wait-census-smoke}"
LAUNCHER="${MGS2_SMOKE_LAUNCHER:-$G/launch-dxvk-sarek-wait-census.sh}"
EXPECT_CENSUS="${MGS2_SMOKE_WAIT_CENSUS:-1}"
RUN_PID=
export XDG_RUNTIME_DIR=/var/run/0-runtime-dir
export WAYLAND_DISPLAY=wayland-1

cleanup() {
    if [ -n "$RUN_PID" ] && kill -0 "$RUN_PID" 2>/dev/null; then
        kill -TERM "$RUN_PID" 2>/dev/null || true
        n=0
        while kill -0 "$RUN_PID" 2>/dev/null && [ "$n" -lt 100 ]; do
            sleep 0.1
            n=$((n + 1))
        done
    fi
}
trap cleanup EXIT INT TERM

for process in /proc/[0-9]*; do
    if [ "$(cat "$process/comm" 2>/dev/null)" = mgs2_sse_rg353v ]; then
        echo "refusing smoke test while game pid ${process#/proc/} is running" >&2
        exit 2
    fi
done

if [ -e "$OUT" ]; then
    echo "refusing existing output path: $OUT" >&2
    exit 2
fi
mkdir -p "$OUT" || exit 1
rm -f /tmp/mgs2-substance.lock

cd /storage/roms/ports || exit 1
setsid nohup "$LAUNCHER" \
    >"$OUT/game.log" 2>&1 < /dev/null &
RUN_PID=$!

PID=
n=0
while [ "$n" -lt 60 ]; do
    for process in /proc/[0-9]*; do
        if [ "$(cat "$process/comm" 2>/dev/null)" = mgs2_sse_rg353v ]; then
            PID=${process#/proc/}
        fi
    done
    if [ -n "$PID" ] \
            && grep -qi '/d3d9.dll' "/proc/$PID/maps" 2>/dev/null \
            && grep -qi '/kernelbase.dll' "/proc/$PID/maps" 2>/dev/null; then
        break
    fi
    kill -0 "$RUN_PID" 2>/dev/null || break
    n=$((n + 1))
    sleep 1
done

if [ -z "$PID" ] || ! kill -0 "$PID" 2>/dev/null; then
    echo "game process did not survive startup" >&2
    tail -80 "$OUT/game.log" >&2
    exit 1
fi

echo "pid=$PID ready_after=${n}s" | tee "$OUT/identity.txt"
tr '\0' '\n' <"/proc/$PID/environ" | \
    grep -E '^MGS2_(WAIT_CENSUS|SLEEP0_WAIT_MS)=' | sort \
    | tee -a "$OUT/identity.txt"
kernelbase_path=$(awk '$NF ~ /\/kernelbase\.dll$/ { print $NF; exit }' "/proc/$PID/maps")
echo "kernelbase_path=$kernelbase_path" | tee -a "$OUT/identity.txt"
sha256sum "$kernelbase_path" | tee -a "$OUT/identity.txt"

reader_rc=0
if [ "$EXPECT_CENSUS" = 1 ]; then
    python3 "$G/wait_census_read.py" "$PID" --interval 0.05 --windows 8 \
        >"$OUT/wait-census.tsv" 2>&1
    reader_rc=$?
fi
sleep 8
grim "$OUT/title.png" 2>/dev/null || true
title_bytes=$(stat -c %s "$OUT/title.png" 2>/dev/null || echo 0)
echo "title_bytes=$title_bytes" | tee -a "$OUT/identity.txt"
if [ "$title_bytes" -lt 10000 ]; then
    echo "title screenshot did not pass the visible-frame size gate" >&2
    exit 1
fi

if [ "$reader_rc" != 0 ]; then
    cat "$OUT/wait-census.tsv" >&2
    exit "$reader_rc"
fi
if [ "$EXPECT_CENSUS" = 1 ]; then
    head -20 "$OUT/wait-census.tsv"
    grep -q 'enabled=1' "$OUT/wait-census.tsv" || {
        echo "census record is present but not enabled" >&2
        exit 1
    }
fi
echo "smoke=$OUT"

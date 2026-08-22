#!/bin/sh
# Differential profile: what work appears when the enemies do.
#
# WHY THIS EXISTS
#
# After the dmabuf presenter the frame is 70 ms and the presenter is 1% of it.
# The residual GPU wait is 9.2 ms of a 74.9 ms combat frame -- 12.3%, and LOWER
# than the 23.3% seen in ordinary play -- so the GPU has slack and the frame is
# CPU-bound. Nobody has ever decomposed those ~65 ms on the current stack.
#
# The old profile cannot be reused for this. It was taken with `-e cycles:u` on
# a single thread, which left 37.6% of that thread's wall clock -- kernel and
# sleep -- unprofiled, and it predates the batcher, the culler, the island, the
# governor fix and the whole present rework.
#
# WHAT MAKES IT DIFFERENTIAL
#
# One capture tells you what is hot. Two captures of the SAME scene in the same
# process, one quiet and one under fire, tell you what the enemies COST -- and
# that is the question, because the game only falls below 15 fps in a firefight.
# Read the two with harness/combat_profile_read.py, which normalises per frame
# and subtracts.
#
# Deliberately: no `:u` (kernel, kbase ioctls, futexes and faults are half the
# story), `-p` not `--tid` (audio, main worker and wineserver were invisible
# before), 199 Hz (prime, so it cannot beat against 60/30 Hz frame pacing).
#
# usage, on the device:   combat_profile_capture.sh <label> [seconds]
set -eu

LABEL="${1:?usage: combat_profile_capture.sh <label> [seconds]}"
SECS="${2:-20}"
OUT=/storage/roms/ports/ablogs/profile
mkdir -p "$OUT"

PID=""
for p in /proc/[0-9]*; do
    [ "$(cat "$p/comm" 2>/dev/null)" = "mgs2_sse_rg353v" ] || continue
    PID=${p#/proc/}
done
[ -n "$PID" ] || { echo "game is not running"; exit 1; }
echo "pid $PID, label $LABEL, ${SECS}s"

# The presenter's own frame counter brackets the window, so cycles can be
# normalised per frame instead of per second -- the only form in which the two
# phases are comparable when their frame rates differ by 3x.
GAMELOG=$(ls -t /storage/roms/ports/ablogs/*.log 2>/dev/null | head -1)
before=$(grep -c "present stats" "$GAMELOG" 2>/dev/null || echo 0)

perf stat -e cycles,instructions,cache-misses,branch-misses,page-faults,context-switches,cpu-migrations \
    -p "$PID" -o "$OUT/$LABEL.stat" -- sleep "$SECS" 2>/dev/null || true

perf record -F 199 -e cycles -p "$PID" -o "$OUT/$LABEL.data" -- sleep "$SECS" 2>/dev/null || true
perf script -i "$OUT/$LABEL.data" > "$OUT/$LABEL.script" 2>/dev/null || true

after=$(grep -c "present stats" "$GAMELOG" 2>/dev/null || echo 0)
{
    echo "label $LABEL"
    echo "pid $PID"
    echo "seconds $SECS"
    echo "gamelog $GAMELOG"
    echo "stats_windows $((after - before))"
    grep "present stats" "$GAMELOG" 2>/dev/null | tail -n $((after - before + 1)) | sed 's/.*MGS2 /MGS2 /'
} > "$OUT/$LABEL.meta"

echo "samples: $(wc -l < "$OUT/$LABEL.script")"
echo "written: $OUT/$LABEL.{stat,data,script,meta}"

#!/bin/sh
# Paired A/B for the native dither replacement, ABBA over whole autoload runs.
#
# The unit has to be a whole run: the freezes happen while a save loads, once,
# and the same save always loads the same content. Within-run alternation is
# impossible, and run-to-run spread is large -- three production runs gave
# 18.7 s, 17.1 s and 14.2 s of long stalls -- so the order is ABBA rather than
# ABAB, for the same reason every other A/B in this project is: it cancels a
# linear drift in machine state across the sequence.
#
# One binary, one DLL, one environment variable. The bridge is armed either way;
# with MGS2_BOX86_NATIVE_DITHER=0 it is not built at all, so the arms differ by
# the replacement and nothing else.
#
# Only the STALL lines and the screenshots are kept: /storage is nearly full and
# a full game log is 4.6 MB per run.
set -u
A="${1:-/storage/roms/ports/ablogs/ditherab}"
CYCLES="${2:-2}"
G=/storage/roms/ports/MGS2-Substance
mkdir -p "$A"

run() {
    arm=$1; idx=$2
    d="$A/$idx-$arm"
    rm -rf "$d"; mkdir -p "$d"
    MGS2_BOX86_BIN=box86-island62-dither \
    MGS2_WINED3D_DLL=wined3d_p78_frm1.dll \
    MGS2_BOX86_NATIVE_DITHER="$arm" \
    MGS2_AUTOLOAD_LOG="$d/game.log" \
        sh "$G/autoload_save.sh" "$d/shots" z > "$d/autoload.log" 2>&1
    grep -a 'MGS2 STALL' "$d/game.log" | sed 's/.*tick=//' > "$d/stalls.txt"
    grep -a 'native dither' "$d/game.log" > "$d/dither.txt"
    total=$(awk '{s+=$4} END {printf "%d", s}' "$d/stalls.txt" 2>/dev/null)
    echo "RESULT idx=$idx arm=$arm stalls=$(wc -l < "$d/stalls.txt") total_ms=${total:-0} matched=$(grep -c matched "$d/dither.txt")"
    rm -f "$d/game.log"
}

i=0
while [ "$i" -lt "$CYCLES" ]; do
    run 0 "$((i * 4 + 0))"
    run 1 "$((i * 4 + 1))"
    run 1 "$((i * 4 + 2))"
    run 0 "$((i * 4 + 3))"
    i=$((i + 1))
done
echo "ГОТОВО"

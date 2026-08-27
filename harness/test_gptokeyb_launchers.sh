#!/bin/sh
# Keep every active full launcher on PortMaster's explicit gptokeyb kill mode.
set -eu

REPO=$(cd "$(dirname "$0")/.." && pwd)
[ -s "$REPO/device/mgs2.gptk" ] || {
    echo "FAIL: tracked device/mgs2.gptk is missing or empty" >&2
    exit 1
}

launchers="
device/launch-play-dxvk-fp17.sh
device/launch-play-dxvk-fp16.sh
device/launch-play-wined3d-fp15.sh
device/launch-dxvk-play.sh
device/launch.sh
"

for rel in $launchers; do
    file="$REPO/$rel"
    grep -Fq '$GPTOKEYB "$EXE" -c "$GAMEDIR/mgs2.gptk"' "$file" || {
        echo "FAIL: $rel does not use the PortMaster GPTOKEYB command" >&2
        exit 1
    }
    grep -Fq '/usr/bin/gptokeyb -1 "$EXE" -c "$GAMEDIR/mgs2.gptk"' "$file" || {
        echo "FAIL: $rel fallback does not arm explicit kill mode" >&2
        exit 1
    }
    if grep -Fq '/usr/bin/gptokeyb "$EXE"' "$file"; then
        echo "FAIL: $rel still has the non-kill-mode positional invocation" >&2
        exit 1
    fi
    echo "ok     $rel"
done

grep -Fq 'scp -q "$REPO/device/mgs2.gptk" "$DEV:$GAMEDIR/mgs2.gptk"' \
    "$REPO/harness/make_release.sh" || {
    echo "FAIL: release deploy does not copy mgs2.gptk" >&2
    exit 1
}
echo "ok     release deploy includes device/mgs2.gptk"

# The MGS2-specific helper is selected only by complete candidate or production
# routes, never by an ambient environment override. Its source/base/hash and the
# Wine controller boundary must move together.
ENGINE="$REPO/device/launch-play-dxvk-fp17.sh"
CANDIDATE="$REPO/device/launch-input-immediate-candidate.sh"
MANIFEST="$REPO/device/BOX86_WAYLAND_TEXT_INPUT_CANDIDATE.manifest"
PATCH="$REPO/gptokeyb-patches/01-immediate-start-back-kill-chord.patch"
BUILD="$REPO/harness/build_gptokeyb_mgs2.sh"
HASH=49c782dad9da50cb0f5bb9e37821104e5089563feb24c7b0303117b75196b43a

grep -Fq 'MGS2_INPUT_ROUTE \' "$ENGINE"
grep -Fq 'MGS2_WINEDLLOVERRIDES="$MGS2_WINEDLLOVERRIDES;winebus.sys=d"' "$ENGINE"
grep -Fq 'MGS2_GPTOKEYB_SHA256='$HASH "$ENGINE"
grep -Fq 'MGS2_PRODUCTION_ROUTE=wayland-p26-candidate' "$CANDIDATE"
if grep -Fq 'MGS2_INPUT_ROUTE=' "$CANDIDATE"; then
    echo "FAIL: candidate wrapper assembles input through an environment override" >&2
    exit 1
fi
grep -Fq 'commit 5b1284e1502548d476aa38e5979b0a8f48cb7b94.' "$PATCH"
grep -Fq 'EXPECTED=${MGS2_GPTOKEYB_EXPECTED_SHA256:-'$HASH'}' "$BUILD"
awk -v hash="$HASH" '$1=="/storage/roms/ports/MGS2-Substance/gptokeyb-mgs2-immediate" {print $2}' \
    "$MANIFEST" | grep -Fxq "$HASH"
rows=$(awk '$1 !~ /^#/ && NF {n++} END {print n+0}' "$MANIFEST")
[ "$rows" = 19 ] || {
    echo "FAIL: input candidate manifest has $rows rows, expected 19" >&2
    exit 1
}
echo "ok     MGS2 closed routes pin helper source, bytes and Wine input boundary"

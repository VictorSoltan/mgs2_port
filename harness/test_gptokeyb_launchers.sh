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

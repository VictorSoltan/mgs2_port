#!/bin/sh
# Capture one bounded, offline-readable island41 profile on the RG353VS.
#
# Run this ON THE DEVICE after launch-play.sh has started island41, the target
# save is loaded and the owner has reached a stable heavy reinforcement window:
#
#   MGS2_BOX86_GUEST_MAP=1 MGS2_BOX86_BIN=box86-island41 ./launch-play.sh
#   /tmp/mgs2-profile-tools/island41_profile_capture.sh 45
#
# It samples only the existing wined3d_cs thread. It does not add Wine or game
# logging and reads Box86's bounded JIT map only after perf has stopped.
set -eu

SECONDS="${1:-45}"
OUTROOT="${2:-/storage/roms/ports/ablogs/island41-profile-$(date +%Y%m%d-%H%M%S)}"
TOOLS_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

case "$SECONDS" in
    ''|*[!0-9]*) echo "usage: $0 [seconds] [output-dir]" >&2; exit 2 ;;
esac
[ "$SECONDS" -gt 0 ] || { echo "seconds must be positive" >&2; exit 2; }
[ -x /usr/bin/perf ] || { echo "perf is unavailable" >&2; exit 1; }
[ -r "$TOOLS_DIR/box86_guest_snapshot.py" ] || {
    echo "missing box86_guest_snapshot.py beside this script" >&2; exit 1;
}

set -- /proc/[0-9]*/task/[0-9]*
CS_TID=""
for task in "$@"; do
    [ -r "$task/comm" ] || continue
    [ "$(cat "$task/comm")" = "wined3d_cs" ] || continue
    if [ -n "$CS_TID" ]; then
        echo "more than one wined3d_cs thread; enforce the one-instance rule" >&2
        exit 1
    fi
    CS_TID=${task##*/}
done
[ -n "$CS_TID" ] || { echo "no wined3d_cs thread: load the game first" >&2; exit 1; }

TGID=$(awk '/^Tgid:/ {print $2; exit}' "/proc/$CS_TID/status")
[ -n "$TGID" ] || { echo "cannot resolve Tgid for $CS_TID" >&2; exit 1; }
BOX86="/proc/$TGID/exe"
readelf -Ws "$BOX86" | grep -q 'mgs2_guest_map$' || {
    echo "the live Box86 has no guest-map recorder; use box86-island41" >&2; exit 1;
}

umask 077
mkdir -p "$OUTROOT"
printf '%s\n' "$CS_TID" > "$OUTROOT/wined3d_cs.tid"
printf '%s\n' "$TGID" > "$OUTROOT/box86.pid"
readlink -f "$BOX86" > "$OUTROOT/box86.path"
sha256sum "$BOX86" > "$OUTROOT/box86.sha256"
cp "/proc/$TGID/maps" "$OUTROOT/maps.before"

echo "capturing $SECONDS s: wined3d_cs tid=$CS_TID, Box86 tgid=$TGID" >&2
perf record --tid "$CS_TID" -e cycles:u -F 997 -o "$OUTROOT/perf.data" -- sleep "$SECONDS"

# Snapshot after sampling so the map includes every dynablock perf could see;
# maps is taken at the same point to resolve the guest image RVAs consistently.
cp "/proc/$TGID/maps" "$OUTROOT/maps"
python3 "$TOOLS_DIR/box86_guest_snapshot.py" --pid "$TGID" --box86 "$BOX86" \
    --output "$OUTROOT/guest-map.bin" | tee "$OUTROOT/guest-map.txt"
perf script -i "$OUTROOT/perf.data" > "$OUTROOT/perf.script"
printf '%s\n' "capture complete: $OUTROOT" >&2

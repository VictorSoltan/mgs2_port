#!/bin/sh
# Read an island41_profile_capture.sh directory on the host, after copying it
# back unchanged. Both reports are offline; no process is inspected here.
set -eu

DIR=${1:?usage: $0 /path/to/island41-profile-dir}
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
for f in guest-map.bin perf.script maps; do
    [ -r "$DIR/$f" ] || { echo "missing $DIR/$f" >&2; exit 1; }
done

python3 "$HERE/box86_cycle_profile.py" \
    --guest-map "$DIR/guest-map.bin" --script "$DIR/perf.script" \
    --maps "$DIR/maps" --module wined3d.dll --limit 15
printf '\nRaw guest-map sample census:\n'
python3 "$HERE/box86_guest_profile.py" \
    --guest-map "$DIR/guest-map.bin" --script "$DIR/perf.script" \
    --maps "$DIR/maps" --limit 15

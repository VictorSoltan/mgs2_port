#!/bin/sh
set -eu

REPO=$(cd "$(dirname "$0")/.." && pwd)
LOCK="$REPO/device/DXT_SURFACE_WITNESS_CANDIDATE.lock"
MANIFEST="$REPO/device/DXT_SURFACE_WITNESS_CANDIDATE.manifest"
PRODUCTION="$REPO/device/FINALPLAY21_WATER_WPATCH.manifest"
TMP=$(mktemp -d /tmp/mgs2-dxt-witness-gate.XXXXXX)
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT HUP INT TERM

lock_value() { awk -v key="$1" '$1 == key {print $2}' "$LOCK"; }
recorded_hash() { awk -v file="$1" '$3 == file {print $2}' "$MANIFEST"; }

[ "$(awk '$1 !~ /^#/ && NF {n++} END {print n+0}' "$MANIFEST")" = 21 ]
[ "$(recorded_hash box86-p27-dxt-witness-candidate)" = \
  "$(lock_value box86_candidate_sha256)" ]
awk '$1 !~ /^#/ && $1 != "/usr/bin/box86"' "$PRODUCTION" > "$TMP/prod-rest"
awk '$1 !~ /^#/ && $1 != "/usr/bin/box86"' "$MANIFEST" > "$TMP/candidate-rest"
cmp "$TMP/prod-rest" "$TMP/candidate-rest"

for key in box86_candidate_patch reader reader_regression launcher_engine \
        launcher_wrapper identity_manifest; do
    path=$(lock_value "$key")
    want=$(lock_value "${key}_sha256")
    got=$(sha256sum "$REPO/$path" | cut -d' ' -f1)
    [ "$got" = "$want" ] || {
        echo "FAIL: $path is $got, lock says $want" >&2
        exit 1
    }
done

PATCH="$REPO/$(lock_value box86_candidate_patch)"
grep -Fq 'MGS2_DXT_SURFACE_WITNESS_STRONG_SELFTEST' "$PATCH"
grep -Fq 'f[0x1050 / 4] = 64;' "$PATCH"
grep -Fq 'f[0x1054 / 4] = 128;' "$PATCH"
grep -Fq 'f[0x108c / 4] = 4;' "$PATCH"
grep -Fq 'f[0x1090 / 4] = 5;' "$PATCH"
grep -Fq 'f[0x10a4 / 4] = 2;' "$PATCH"
grep -Fq 'mgs2_dxt_surface_witness[6]' "$PATCH"
grep -Fq 'there is no per-call counter or logging' "$PATCH"

grep -Fq 'dxt-witness-candidate)' "$REPO/device/launch-play-dxvk-fp17.sh"
grep -Fq 'MGS2_PRODUCTION_ROUTE=dxt-witness-candidate' \
    "$REPO/device/launch-dxt-surface-witness-candidate.sh"
python3 "$REPO/harness/test_dxt_surface_witness.py"

echo "ok     p27 strong self-test and bounded witness are source-recorded"
echo "ok     candidate differs from FINALPLAY21 only at /usr/bin/box86"
echo "ok     exact 21-row identity, reader and fail-closed hashes are pinned"

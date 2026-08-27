#!/bin/sh
# Static fail-closed gate for the retained FINALPLAY18 rollback bundle.
set -eu

REPO=$(cd "$(dirname "$0")/.." && pwd)
SELECTOR="$REPO/device/launch-play.sh"
ENGINE="$REPO/device/launch-play-dxvk-fp17.sh"
WRAPPER="$REPO/device/launch-play-dxvk-fp18.sh"
MANIFEST18="$REPO/device/FINALPLAY18_WAYLAND_ABI.manifest"
MANIFEST17="$REPO/device/FINALPLAY17_DXVK_FREEZE.manifest"
LOCK="$REPO/device/FINALPLAY.lock"
PRODUCTION_HASHES="$REPO/device/FINALPLAY18_PRODUCTION.sha256"
TMP=$(mktemp -d /tmp/mgs2-finalplay18-gate.XXXXXX)
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT HUP INT TERM

lock_value() {
    awk -v key="$1" '$1 == key {print $2}' "$LOCK"
}

recorded_hash() {
    awk -v name="$1" '$2 == name {print $1}' "$PRODUCTION_HASHES"
}

grep -Fq 'dxvk18|fp18)' "$SELECTOR"
grep -Fq 'exec "$HERE/launch-play-dxvk-fp18.sh"' "$SELECTOR"
grep -Fq 'dxvk17|fp17)' "$SELECTOR"
grep -Fq 'exec "$HERE/launch-play-dxvk-fp17.sh"' "$SELECTOR"
grep -Fq 'export MGS2_PRODUCTION_ROUTE=finalplay18' "$WRAPPER"
grep -Fq 'MGS2_BOX86_BIN=box86-fp24-wayland-atomic-production' "$ENGINE"
grep -Fq 'PLAY_IDENTITY_MANIFEST=FINALPLAY18_WAYLAND_ABI.manifest' "$ENGINE"

rows=$(awk '$1 !~ /^#/ && NF {n++} END {print n+0}' "$MANIFEST18")
[ "$rows" = 18 ] || { echo "FAIL: FINALPLAY18 manifest has $rows rows, expected 18" >&2; exit 1; }
awk '$1=="/usr/bin/box86" {print $2, $3}' "$MANIFEST18" \
    | grep -Fxq 'd6cafba667d16f6227c0ffd5437e7ac52253dd46624c2edfcbbd36ca3843188b box86-fp24-wayland-atomic-production'
awk '$1 !~ /^#/ && $1!="/usr/bin/box86"' "$MANIFEST17" > "$TMP/fp17"
awk '$1 !~ /^#/ && $1!="/usr/bin/box86"' "$MANIFEST18" > "$TMP/fp18"
cmp "$TMP/fp17" "$TMP/fp18"

grep -Fq 'box86_production_patch_23 box86-patches/23-wayland-wine11-listener-abi-fix.patch' "$LOCK"
grep -Fq 'box86_production_patch_24 box86-patches/24-wayland-listener-atomic-publication.patch' "$LOCK"
grep -Fq 'finalplay18_box86_sha256 d6cafba667d16f6227c0ffd5437e7ac52253dd46624c2edfcbbd36ca3843188b' "$LOCK"

# The first three release artifacts are deliberately not stored in Git. Tie
# their release records to the rebuild lock; hash every tracked row byte for
# byte. The device-side gate separately hashed all eleven deployed files.
[ "$(awk 'NF == 2 {n++} END {print n+0}' "$PRODUCTION_HASHES")" = 11 ]
[ "$(recorded_hash box86-fp24-wayland-atomic-production)" = \
  "$(lock_value finalplay18_box86_sha256)" ]
[ "$(recorded_hash d3d8_dxvk_sarek_1.11.1_mali_wsiinit3.dll)" = \
  "$(lock_value finalplay17_d3d8_sha256)" ]
[ "$(recorded_hash d3d9_dxvk_sarek_1.11.1_mali_freeze1.dll)" = \
  "$(lock_value finalplay17_d3d9_sha256)" ]
( cd "$REPO/device" && sed -n '4,$p' "$PRODUCTION_HASHES" | sha256sum -c - >/dev/null )

echo "ok     FINALPLAY18 remains a fixed rollback route"
echo "ok     FINALPLAY18 differs from FINALPLAY17 only at /usr/bin/box86"
echo "ok     Box86 patches 23+24 and the p24 rollback hash remain locked"
echo "ok     tracked FINALPLAY18 launcher/manifest/config hashes match"

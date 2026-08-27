#!/bin/sh
# Static fail-closed gate for the FINALPLAY19 selector and fixed bundle split.
set -eu

REPO=$(cd "$(dirname "$0")/.." && pwd)
SELECTOR="$REPO/device/launch-play.sh"
ENGINE="$REPO/device/launch-play-dxvk-fp17.sh"
WRAPPER="$REPO/device/launch-play-dxvk-fp19.sh"
MANIFEST19="$REPO/device/FINALPLAY19_INPUT_WAYLAND.manifest"
MANIFEST18="$REPO/device/FINALPLAY18_WAYLAND_ABI.manifest"
LOCK="$REPO/device/FINALPLAY.lock"
PRODUCTION_HASHES="$REPO/device/FINALPLAY19_PRODUCTION.sha256"
TMP=$(mktemp -d /tmp/mgs2-finalplay19-gate.XXXXXX)
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT HUP INT TERM

BOX_HASH=b7e9530f6039335a37ee54d8d3a2974e25b71500b96b95a9dd899f1e20374d51
INPUT_HASH=49c782dad9da50cb0f5bb9e37821104e5089563feb24c7b0303117b75196b43a

lock_value() {
    awk -v key="$1" '$1 == key {print $2}' "$LOCK"
}

recorded_hash() {
    awk -v name="$1" '$2 == name {print $1}' "$PRODUCTION_HASHES"
}

grep -Fq 'dxvk|dxvk19|fp19)' "$SELECTOR"
grep -Fq 'exec "$HERE/launch-play-dxvk-fp19.sh"' "$SELECTOR"
grep -Fq 'dxvk18|fp18)' "$SELECTOR"
grep -Fq 'exec "$HERE/launch-play-dxvk-fp18.sh"' "$SELECTOR"
grep -Fq 'export MGS2_PRODUCTION_ROUTE=finalplay19' "$WRAPPER"
grep -Fq 'MGS2_BOX86_BIN=box86-fp26-wayland-text-input-production' "$ENGINE"
grep -Fq 'PLAY_IDENTITY_MANIFEST=FINALPLAY19_INPUT_WAYLAND.manifest' "$ENGINE"
grep -Fq 'INPUT_ROUTE=immediate-production' "$ENGINE"
grep -Fq 'winebus.sys=d' "$ENGINE"

rows=$(awk '$1 !~ /^#/ && NF {n++} END {print n+0}' "$MANIFEST19")
[ "$rows" = 19 ] || { echo "FAIL: FINALPLAY19 manifest has $rows rows, expected 19" >&2; exit 1; }
awk '$1=="/usr/bin/box86" {print $2, $3}' "$MANIFEST19" \
    | grep -Fxq "$BOX_HASH box86-fp26-wayland-text-input-production"
awk '$1=="/storage/roms/ports/MGS2-Substance/gptokeyb-mgs2-immediate" {print $2}' \
    "$MANIFEST19" | grep -Fxq "$INPUT_HASH"
awk '$1 !~ /^#/ && $1!="/usr/bin/box86"' "$MANIFEST18" > "$TMP/fp18-rest"
awk '$1 !~ /^#/ && $1!="/usr/bin/box86" && \
     $1!="/storage/roms/ports/MGS2-Substance/gptokeyb-mgs2-immediate"' \
    "$MANIFEST19" > "$TMP/fp19-rest"
cmp "$TMP/fp18-rest" "$TMP/fp19-rest"

grep -Fq 'box86_production_patch_25 box86-patches/25-wayland-text-input-listener-abi.patch' "$LOCK"
grep -Fq 'box86_production_patch_26 box86-patches/26-reproducible-git-revision.patch' "$LOCK"
[ "$(sha256sum "$REPO/$(lock_value box86_production_patch_25)" | cut -d' ' -f1)" = \
  "$(lock_value box86_patch_25_sha256)" ]
[ "$(sha256sum "$REPO/$(lock_value box86_production_patch_26)" | cut -d' ' -f1)" = \
  "$(lock_value box86_patch_26_sha256)" ]
[ "$(lock_value box86_production_sha256)" = "$BOX_HASH" ]
[ "$(lock_value gptokeyb_production_sha256)" = "$INPUT_HASH" ]
[ "$(sha256sum "$REPO/$(lock_value gptokeyb_production_patch_01)" | cut -d' ' -f1)" = \
  "$(lock_value gptokeyb_production_patch_01_sha256)" ]
if grep -q '^box86_candidate_patch_' "$LOCK"; then
    echo "FAIL: promoted FINALPLAY19 still has a candidate patch lock entry" >&2
    exit 1
fi

# The binary rows are distributed separately. Every tracked row is still
# verified byte for byte, while the device gate checks all 19 deployed bytes.
[ "$(awk 'NF == 2 {n++} END {print n+0}' "$PRODUCTION_HASHES")" = 13 ]
[ "$(recorded_hash box86-fp26-wayland-text-input-production)" = "$BOX_HASH" ]
[ "$(recorded_hash gptokeyb-mgs2-immediate)" = "$INPUT_HASH" ]
[ "$(recorded_hash d3d8_dxvk_sarek_1.11.1_mali_wsiinit3.dll)" = \
  "$(lock_value finalplay17_d3d8_sha256)" ]
[ "$(recorded_hash d3d9_dxvk_sarek_1.11.1_mali_freeze1.dll)" = \
  "$(lock_value finalplay17_d3d9_sha256)" ]
( cd "$REPO/device" && sed -n '5,$p' "$PRODUCTION_HASHES" | sha256sum -c - >/dev/null )

echo "ok     FINALPLAY19 is the fixed default and FINALPLAY18 remains rollback"
echo "ok     FINALPLAY19 adds p25/p26 Box86 and the immediate input helper"
echo "ok     p25/p26, helper source and exact binary hashes are production-locked"
echo "ok     tracked FINALPLAY19 launcher/manifest/config hashes match"

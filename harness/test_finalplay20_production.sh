#!/bin/sh
# Static fail-closed gate for the FINALPLAY20 selector and p37 audio bundle.
set -eu

REPO=$(cd "$(dirname "$0")/.." && pwd)
SELECTOR="$REPO/device/launch-play.sh"
ENGINE="$REPO/device/launch-play-dxvk-fp17.sh"
WRAPPER20="$REPO/device/launch-play-dxvk-fp20.sh"
MANIFEST20="$REPO/device/FINALPLAY20_DMSYNTH_RESUME.manifest"
MANIFEST19="$REPO/device/FINALPLAY19_INPUT_WAYLAND.manifest"
LOCK="$REPO/device/FINALPLAY.lock"
PRODUCTION_HASHES="$REPO/device/FINALPLAY20_PRODUCTION.sha256"
TMP=$(mktemp -d /tmp/mgs2-finalplay20-gate.XXXXXX)
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT HUP INT TERM

DMSYNTH_HASH=b11c9b6ba2f1d27fcdea822fff37f62187862aa7aeb5527d2efd2a159778ede8

lock_value() {
    awk -v key="$1" '$1 == key {print $2}' "$LOCK"
}

recorded_hash() {
    awk -v name="$1" '$2 == name {print $1}' "$PRODUCTION_HASHES"
}

grep -Fq 'dxvk|dxvk20|fp20)' "$SELECTOR"
grep -Fq 'exec "$HERE/launch-play-dxvk-fp20.sh"' "$SELECTOR"
grep -Fq 'dxvk19|fp19)' "$SELECTOR"
grep -Fq 'exec "$HERE/launch-play-dxvk-fp19.sh"' "$SELECTOR"
grep -Fq 'export MGS2_PRODUCTION_ROUTE=finalplay20' "$WRAPPER20"
grep -Fq 'finalplay20)' "$ENGINE"
grep -Fq 'PLAY_IDENTITY_MANIFEST=FINALPLAY20_DMSYNTH_RESUME.manifest' "$ENGINE"
grep -Fq 'MGS2_DMSYNTH_DLL=dmsynth_p37_resume_timeline.dll' "$ENGINE"
grep -Fq 'MGS2_DMSYNTH_WATCHDOG_MS=250' "$ENGINE"
grep -Fq 'MGS2_DMSYNTH_WATCHDOG_STALL=1' "$ENGINE"
grep -Fq 'MGS2_DMSYNTH_WATCHDOG_MS' "$ENGINE"
grep -Fq 'wine_(research|production)_patch_' "$REPO/harness/verify_rebuild.sh"

rows=$(awk '$1 !~ /^#/ && NF {n++} END {print n+0}' "$MANIFEST20")
[ "$rows" = 19 ] || { echo "FAIL: FINALPLAY20 manifest has $rows rows, expected 19" >&2; exit 1; }
awk '$1=="/usr/lib/wine/i386-windows/dmsynth.dll" {print $2, $3}' "$MANIFEST20" \
    | grep -Fxq "$DMSYNTH_HASH dmsynth_p37_resume_timeline.dll"
awk '$1 !~ /^#/ && $1!="/usr/lib/wine/i386-windows/dmsynth.dll"' \
    "$MANIFEST19" > "$TMP/fp19-rest"
awk '$1 !~ /^#/ && $1!="/usr/lib/wine/i386-windows/dmsynth.dll"' \
    "$MANIFEST20" > "$TMP/fp20-rest"
cmp "$TMP/fp19-rest" "$TMP/fp20-rest"

[ "$(lock_value dmsynth_production_sha256)" = "$DMSYNTH_HASH" ]
[ "$(sha256sum "$REPO/$(lock_value wine_history_patch_60)" | cut -d' ' -f1)" = \
  "$(lock_value wine_patch_60_sha256)" ]
[ "$(sha256sum "$REPO/$(lock_value wine_production_patch_83)" | cut -d' ' -f1)" = \
  "$(lock_value wine_patch_83_sha256)" ]

# Five separately distributed binaries precede the tracked device records.
[ "$(awk 'NF == 2 {n++} END {print n+0}' "$PRODUCTION_HASHES")" = 15 ]
[ "$(recorded_hash dmsynth_p37_resume_timeline.dll)" = "$DMSYNTH_HASH" ]
[ "$(recorded_hash box86-fp26-wayland-text-input-production)" = \
  "$(lock_value box86_production_sha256)" ]
[ "$(recorded_hash gptokeyb-mgs2-immediate)" = \
  "$(lock_value gptokeyb_production_sha256)" ]
[ "$(recorded_hash d3d8_dxvk_sarek_1.11.1_mali_wsiinit3.dll)" = \
  "$(lock_value finalplay17_d3d8_sha256)" ]
[ "$(recorded_hash d3d9_dxvk_sarek_1.11.1_mali_freeze1.dll)" = \
  "$(lock_value finalplay17_d3d9_sha256)" ]
( cd "$REPO/device" && sed -n '6,$p' "$PRODUCTION_HASHES" | sha256sum -c - >/dev/null )

echo "ok     FINALPLAY20 is the fixed default and FINALPLAY19 is exact rollback"
echo "ok     FINALPLAY20 differs from FINALPLAY19 only at dmsynth.dll and fixed watchdog state"
echo "ok     p35+p37 Wine source patches and exact p37 binary hash are production-locked"
echo "ok     tracked FINALPLAY20 launcher/manifest/config hashes match"

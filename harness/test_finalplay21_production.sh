#!/bin/sh
# Static fail-closed gate for the FINALPLAY21 water-path production bundle.
set -eu

REPO=$(cd "$(dirname "$0")/.." && pwd)
SELECTOR="$REPO/device/launch-play.sh"
ENGINE="$REPO/device/launch-play-dxvk-fp17.sh"
WRAPPER21="$REPO/device/launch-play-dxvk-fp21.sh"
PATCHER="$REPO/device/patch-mgs2-wpatch-novs.sh"
SOURCE_PATCH="$REPO/game-patches/01-wpatch-fixed-function-fallback.patch"
MANIFEST21="$REPO/device/FINALPLAY21_WATER_WPATCH.manifest"
MANIFEST20="$REPO/device/FINALPLAY20_DMSYNTH_RESUME.manifest"
LOCK="$REPO/device/FINALPLAY.lock"
PRODUCTION_HASHES="$REPO/device/FINALPLAY21_PRODUCTION.sha256"
TMP=$(mktemp -d /tmp/mgs2-finalplay21-gate.XXXXXX)
EXTERNAL_TMP=""
cleanup() {
    rm -rf "$TMP"
    [ -z "$EXTERNAL_TMP" ] || rm -f "$EXTERNAL_TMP"
}
trap cleanup EXIT HUP INT TERM

ORIGINAL_HASH=29759e6f06eaea4d61bb6aef5a5ef45a936eac1e76fa0c3471cf4f231349aaa0
PATCHED_HASH=6686b3fa6484a0609fbe65be46f34cbba941b18e252db7bbb83d457153ba31d6
PATCHER_HASH=ace82a30c96c2c52dddf920a2d45f878f916ee31900838eef5fb491f8f607325
INPUT_HASH=49c782dad9da50cb0f5bb9e37821104e5089563feb24c7b0303117b75196b43a
DMSYNTH_HASH=b11c9b6ba2f1d27fcdea822fff37f62187862aa7aeb5527d2efd2a159778ede8

lock_value() {
    awk -v key="$1" '$1 == key {print $2}' "$LOCK"
}

recorded_hash() {
    awk -v name="$1" '$2 == name {print $1}' "$PRODUCTION_HASHES"
}

grep -Fq 'dxvk21|fp21)' "$SELECTOR"
grep -Fq 'exec "$HERE/launch-play-dxvk-fp21.sh"' "$SELECTOR"
grep -Fq 'dxvk20|fp20)' "$SELECTOR"
grep -Fq 'exec "$HERE/launch-play-dxvk-fp20.sh"' "$SELECTOR"
grep -Fq 'export MGS2_PRODUCTION_ROUTE=finalplay21' "$WRAPPER21"
grep -Fq 'finalplay21)' "$ENGINE"
grep -Fq 'PLAY_IDENTITY_MANIFEST=FINALPLAY21_WATER_WPATCH.manifest' "$ENGINE"
grep -Fq 'GAME_EXE_PATCH=wpatch-fixed-function' "$ENGINE"
grep -Fq 'EXPECTED_BIND_MOUNTS=8' "$ENGINE"
grep -Fq 'EXPECTED_IDENTITY_ROWS=21' "$ENGINE"
grep -Fq "patcher_hash=$PATCHER_HASH" "$ENGINE"
grep -Fq "patched_hash=$PATCHED_HASH" "$ENGINE"
grep -Fq 'game patch helper is ${got:-missing}, refusing $route_name' "$ENGINE"
grep -Fq 'unmount_all "$GAME_EXE_TARGET"' "$ENGINE"
grep -Fq 'mount_bind "$PATCHED_GAME_EXE" "$GAME_EXE_TARGET"' "$ENGINE"
grep -Fq '/tmp/mgs2-wpatch-novs.*)' "$PATCHER"

rows=$(awk '$1 !~ /^#/ && NF {n++} END {print n+0}' "$MANIFEST21")
[ "$rows" = 21 ] || { echo "FAIL: FINALPLAY21 manifest has $rows rows, expected 21" >&2; exit 1; }
awk '$1=="/storage/roms/ports/MGS2-Substance/game/bin/mgs2_sse_rg353vs_port.exe" {print $2}' \
    "$MANIFEST21" | grep -Fxq "$PATCHED_HASH"
awk '$1=="/storage/roms/ports/MGS2-Substance/patch-mgs2-wpatch-novs.sh" {print $2}' \
    "$MANIFEST21" | grep -Fxq "$PATCHER_HASH"
awk '$1 !~ /^#/ && NF && $1!="/storage/roms/ports/MGS2-Substance/game/bin/mgs2_sse_rg353vs_port.exe" && \
     $1!="/storage/roms/ports/MGS2-Substance/patch-mgs2-wpatch-novs.sh"' \
    "$MANIFEST21" > "$TMP/fp21-rest"
awk '$1 !~ /^#/ && NF' "$MANIFEST20" > "$TMP/fp20"
cmp "$TMP/fp20" "$TMP/fp21-rest"

[ "$(lock_value game_exe_original_sha256)" = "$ORIGINAL_HASH" ]
[ "$(lock_value game_exe_wpatch_novs_sha256)" = "$PATCHED_HASH" ]
[ "$(lock_value game_exe_wpatch_novs_offset)" = 0x4a294a ]
[ "$(lock_value game_exe_wpatch_novs_original_byte)" = 02 ]
[ "$(sha256sum "$REPO/$(lock_value game_wpatch_novs_source_patch)" | cut -d' ' -f1)" = \
  "$(lock_value game_wpatch_novs_source_patch_sha256)" ]
[ "$(sha256sum "$PATCHER" | cut -d' ' -f1)" = "$PATCHER_HASH" ]

# A wrong game image must fail before producing a candidate.
: > "$TMP/wrong.exe"
EXTERNAL_TMP=$(mktemp /tmp/mgs2-wpatch-novs.wrong.XXXXXX)
if "$PATCHER" "$TMP/wrong.exe" "$EXTERNAL_TMP" >/dev/null 2>&1; then
    echo "FAIL: FINALPLAY21 patcher accepted an unknown game EXE" >&2
    exit 1
fi
[ ! -s "$EXTERNAL_TMP" ]
rm -f "$EXTERNAL_TMP"
EXTERNAL_TMP=""

# Exercise the exact one-byte transform when the owner's untracked legal image
# is present. Public/CI clones intentionally do not contain it.
LOCAL_EXE="$REPO/../recovered-session/binaries/mgs2_sse_rg353vs_port.exe"
[ -r "$LOCAL_EXE" ] || \
    LOCAL_EXE="$REPO/../recovered-session/local-reference/game/bin/mgs2_sse_rg353vs_port.exe"
TRANSFORM_GATE=hash-pinned
if [ -r "$LOCAL_EXE" ]; then
    # Even the exact original must never be accepted as its own output target.
    if "$PATCHER" "$LOCAL_EXE" "$LOCAL_EXE" >/dev/null 2>&1; then
        echo "FAIL: FINALPLAY21 patcher accepted an in-place game EXE edit" >&2
        exit 1
    fi
    EXTERNAL_TMP=$(mktemp /tmp/mgs2-wpatch-novs.gate.XXXXXX)
    "$PATCHER" "$LOCAL_EXE" "$EXTERNAL_TMP" >/dev/null
    [ "$(sha256sum "$EXTERNAL_TMP" | cut -d' ' -f1)" = "$PATCHED_HASH" ]
    [ "$(cmp -l "$LOCAL_EXE" "$EXTERNAL_TMP" | awk 'END {print NR+0}')" = 1 ]
    cmp -l "$LOCAL_EXE" "$EXTERNAL_TMP" | awk '$1==4860235 && $2==2 && $3==0 {ok=1} END {exit !ok}'
    rm -f "$EXTERNAL_TMP"
    EXTERNAL_TMP=""
    TRANSFORM_GATE=executed
fi

# The recovered source uses CRCRLF endings; --binary verifies the recorded diff
# without silently normalising those bytes.
SOURCE_WDGD="$REPO/../mgs_source/MGS2-Source-main/mgs2x/source/system/libdg/wdgd.c"
if [ -r "$SOURCE_WDGD" ]; then
    mkdir -p "$TMP/source/mgs2x/source/system/libdg"
    cp "$SOURCE_WDGD" "$TMP/source/mgs2x/source/system/libdg/wdgd.c"
    patch --binary --dry-run -d "$TMP/source" -p1 < "$SOURCE_PATCH" >/dev/null
fi

# Five separately distributed binaries precede the tracked device records.
[ "$(awk 'NF == 2 {n++} END {print n+0}' "$PRODUCTION_HASHES")" = 17 ]
[ "$(recorded_hash patch-mgs2-wpatch-novs.sh)" = "$PATCHER_HASH" ]
[ "$(recorded_hash gptokeyb-mgs2-immediate)" = "$INPUT_HASH" ]
[ "$(recorded_hash dmsynth_p37_resume_timeline.dll)" = "$DMSYNTH_HASH" ]
[ "$(recorded_hash box86-fp26-wayland-text-input-production)" = \
  "$(lock_value box86_production_sha256)" ]
[ "$(recorded_hash d3d8_dxvk_sarek_1.11.1_mali_wsiinit3.dll)" = \
  "$(lock_value finalplay17_d3d8_sha256)" ]
[ "$(recorded_hash d3d9_dxvk_sarek_1.11.1_mali_freeze1.dll)" = \
  "$(lock_value finalplay17_d3d9_sha256)" ]
( cd "$REPO/device" && sed -n '6,$p' "$PRODUCTION_HASHES" | sha256sum -c - >/dev/null )

echo "ok     FINALPLAY21 remains an exact fixed rollback to FINALPLAY22"
echo "ok     FINALPLAY21 differs from FINALPLAY20 only at the verified game EXE view"
echo "ok     one-byte transform ($TRANSFORM_GATE) and source-equivalent patch are locked"
echo "ok     tracked FINALPLAY21 rollback launcher/manifest/config hashes match"

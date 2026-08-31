#!/bin/sh
# Static, reconstruction and fail-closed gate for FINALPLAY22 production.
set -eu

REPO=$(cd "$(dirname "$0")/.." && pwd)
SELECTOR="$REPO/device/launch-play.sh"
ENGINE="$REPO/device/launch-play-dxvk-fp17.sh"
WRAPPER="$REPO/device/launch-play-dxvk-fp22.sh"
PATCHER="$REPO/device/patch-mgs2-wpatch-finalplay22.sh"
MANIFEST="$REPO/device/FINALPLAY22_AUDIT_FIXES.manifest"
ROLLBACK="$REPO/device/FINALPLAY21_WATER_WPATCH.manifest"
PRODUCTION="$REPO/device/FINALPLAY22_PRODUCTION.sha256"
LOCK="$REPO/device/FINALPLAY.lock"
RELEASE="$REPO/harness/make_release.sh"
CURRENT_RELEASE="$REPO/harness/make_current_release.sh"
BASE_PATCH="$REPO/game-patches/02-wpatch-consumer-and-state-isolation.patch"
STATE_PATCH="$REPO/game-patches/04-wpatch-texture-transform-ownership-candidate.patch"
SAFETY_PATCH="$REPO/game-patches/05-wpatch-latent-safety-corrections.patch"
PATCH84="$REPO/wine-patches/history/84-dmime-message-private-state-layout.patch"
PATCH85="$REPO/wine-patches/history/85-dmsynth-sink-lifetime-and-clock-state.patch"
TMP=$(mktemp -d /tmp/mgs2-finalplay22-gate.XXXXXX)
EXTERNAL_TMP=""
cleanup() {
    rm -rf "$TMP"
    [ -z "$EXTERNAL_TMP" ] || rm -f "$EXTERNAL_TMP"
}
trap cleanup EXIT HUP INT TERM

ORIGINAL_HASH=29759e6f06eaea4d61bb6aef5a5ef45a936eac1e76fa0c3471cf4f231349aaa0
GAME_HASH=d902ee4398b77653674943f097f79e103d1aa0bc93ce825c0cb0c3d3522b9f88
PATCHER_HASH=55f1714b68a0360829469439143923bc74356502be9164628e1a2dd9633464fa
DMIME_HASH=f23f08ed4c41f69baf4ac14a22f9fc5605b629123438fdf37714af6bdae5698e
DMSYNTH_HASH=22287685511486728cb7fc08ec6689b4213ad48cc01679b4bb6e91c02ddfdc1e
PATCH84_HASH=d1fa52593cb556de8aa6d32a74b02d7273d92bed634eea70f24d13a271790778
PATCH85_HASH=5ef57275503b7bd576944a7991afb76f560b4cf67d7af38b4dd15a22f6353d62

lock_value() { awk -v key="$1" '$1==key {print $2}' "$LOCK"; }
recorded_hash() { awk -v name="$1" '$2==name {print $1}' "$PRODUCTION"; }
manifest_hash() { awk -v path="$1" '$1==path {print $2}' "$MANIFEST"; }

bash -n "$ENGINE"
sh -n "$SELECTOR"
sh -n "$WRAPPER"
sh -n "$PATCHER"

grep -Fq 'dxvk22|fp22)' "$SELECTOR"
grep -Fq 'exec "$HERE/launch-play-dxvk-fp22.sh"' "$SELECTOR"
grep -Fq 'dxvk21|fp21)' "$SELECTOR"
grep -Fq 'exec "$HERE/launch-play-dxvk-fp21.sh"' "$SELECTOR"
grep -Fq 'export MGS2_PRODUCTION_ROUTE=finalplay22' "$WRAPPER"
grep -Fq 'finalplay22)' "$ENGINE"
grep -Fq 'PLAY_IDENTITY_MANIFEST=FINALPLAY22_AUDIT_FIXES.manifest' "$ENGINE"
grep -Fq 'MGS2_DMSYNTH_DLL=dmsynth_p38_sink_lifetime.dll' "$ENGINE"
grep -Fq 'MGS2_DMIME_DLL=dmime_p16_curve_state_layout.dll' "$ENGINE"
grep -Fq 'GAME_EXE_PATCH=wpatch-finalplay22' "$ENGINE"
grep -Fq 'EXPECTED_BIND_MOUNTS=8' "$ENGINE"
grep -Fq 'EXPECTED_IDENTITY_ROWS=21' "$ENGINE"
grep -Fq "patcher_hash=$PATCHER_HASH" "$ENGINE"
grep -Fq "patched_hash=$GAME_HASH" "$ENGINE"
grep -Fq '/tmp/mgs2-wpatch-finalplay22.*)' "$PATCHER"

rows=$(awk '$1 !~ /^#/ && NF {n++} END {print n+0}' "$MANIFEST")
[ "$rows" = 21 ] || { echo "FAIL: FINALPLAY22 manifest has $rows rows, expected 21" >&2; exit 1; }
[ "$(manifest_hash /storage/roms/ports/MGS2-Substance/game/bin/mgs2_sse_rg353vs_port.exe)" = "$GAME_HASH" ]
[ "$(manifest_hash /storage/roms/ports/MGS2-Substance/patch-mgs2-wpatch-finalplay22.sh)" = "$PATCHER_HASH" ]
[ "$(manifest_hash /usr/lib/wine/i386-windows/dmime.dll)" = "$DMIME_HASH" ]
[ "$(manifest_hash /usr/lib/wine/i386-windows/dmsynth.dll)" = "$DMSYNTH_HASH" ]

# FINALPLAY22 differs from exact FINALPLAY21 at only the helper/image and two
# Wine audio modules. All other live identity rows must remain byte-for-byte.
awk '$1 !~ /^#/ && NF && \
     $1!="/storage/roms/ports/MGS2-Substance/patch-mgs2-wpatch-finalplay22.sh" && \
     $1!="/storage/roms/ports/MGS2-Substance/game/bin/mgs2_sse_rg353vs_port.exe" && \
     $1!="/usr/lib/wine/i386-windows/dmime.dll" && \
     $1!="/usr/lib/wine/i386-windows/dmsynth.dll"' "$MANIFEST" > "$TMP/fp22-rest"
awk '$1 !~ /^#/ && NF && \
     $1!="/storage/roms/ports/MGS2-Substance/patch-mgs2-wpatch-novs.sh" && \
     $1!="/storage/roms/ports/MGS2-Substance/game/bin/mgs2_sse_rg353vs_port.exe" && \
     $1!="/usr/lib/wine/i386-windows/dmime.dll" && \
     $1!="/usr/lib/wine/i386-windows/dmsynth.dll"' "$ROLLBACK" > "$TMP/fp21-rest"
cmp "$TMP/fp21-rest" "$TMP/fp22-rest"

[ "$(lock_value game_exe_original_sha256)" = "$ORIGINAL_HASH" ]
[ "$(lock_value game_exe_finalplay22_sha256)" = "$GAME_HASH" ]
[ "$(sha256sum "$REPO/$(lock_value game_finalplay22_patcher)" | cut -d' ' -f1)" = "$PATCHER_HASH" ]
[ "$(sha256sum "$PATCH84" | cut -d' ' -f1)" = "$PATCH84_HASH" ]
[ "$(sha256sum "$PATCH85" | cut -d' ' -f1)" = "$PATCH85_HASH" ]
[ "$(lock_value finalplay22_dmime_sha256)" = "$DMIME_HASH" ]
[ "$(lock_value finalplay22_dmsynth_sha256)" = "$DMSYNTH_HASH" ]
[ "$(lock_value finalplay22_wine_source_date_epoch)" = 1787976000 ]
[ "$(sha256sum "$BASE_PATCH" | cut -d' ' -f1)" = \
  "$(lock_value game_finalplay22_base_source_patch_sha256)" ]
[ "$(sha256sum "$STATE_PATCH" | cut -d' ' -f1)" = \
  "$(lock_value game_finalplay22_state_source_patch_sha256)" ]
[ "$(sha256sum "$SAFETY_PATCH" | cut -d' ' -f1)" = \
  "$(lock_value game_finalplay22_safety_source_patch_sha256)" ]

: > "$TMP/wrong.exe"
EXTERNAL_TMP=$(mktemp /tmp/mgs2-wpatch-finalplay22.wrong.XXXXXX)
if "$PATCHER" "$TMP/wrong.exe" "$EXTERNAL_TMP" >/dev/null 2>&1; then
    echo "FAIL: FINALPLAY22 patcher accepted an unknown game EXE" >&2
    exit 1
fi
[ ! -s "$EXTERNAL_TMP" ]
rm -f "$EXTERNAL_TMP"
EXTERNAL_TMP=""

LOCAL_EXE="$REPO/../recovered-session/binaries/mgs2_sse_rg353vs_port.exe"
[ -r "$LOCAL_EXE" ] || \
    LOCAL_EXE="$REPO/../recovered-session/local-reference/game/bin/mgs2_sse_rg353vs_port.exe"
TRANSFORM_GATE=hash-pinned
if [ -r "$LOCAL_EXE" ]; then
    if "$PATCHER" "$LOCAL_EXE" "$LOCAL_EXE" >/dev/null 2>&1; then
        echo "FAIL: FINALPLAY22 patcher accepted an in-place edit" >&2
        exit 1
    fi
    if "$PATCHER" "$LOCAL_EXE" "$TMP/forbidden.exe" >/dev/null 2>&1; then
        echo "FAIL: FINALPLAY22 patcher accepted output outside private /tmp" >&2
        exit 1
    fi
    EXTERNAL_TMP=$(mktemp /tmp/mgs2-wpatch-finalplay22.gate.XXXXXX)
    "$PATCHER" "$LOCAL_EXE" "$EXTERNAL_TMP" >/dev/null
    [ "$(sha256sum "$EXTERNAL_TMP" | cut -d' ' -f1)" = "$GAME_HASH" ]
    [ "$(cmp -l "$LOCAL_EXE" "$EXTERNAL_TMP" | awk 'END {print NR+0}')" = 58 ]
    rm -f "$EXTERNAL_TMP"
    EXTERNAL_TMP=""
    TRANSFORM_GATE=executed
fi

SOURCE_ROOT="$REPO/../mgs_source/MGS2-Source-main/mgs2x/source"
if [ -r "$SOURCE_ROOT/system/libdg/wdgd.c" ] && \
   [ -r "$SOURCE_ROOT/system/libdg/wpatch.c" ] && \
   [ -r "$SOURCE_ROOT/user/takabe/object/ipupanel.c" ]; then
    mkdir -p "$TMP/game/mgs2x/source/system/libdg" \
        "$TMP/game/mgs2x/source/user/takabe/object"
    cp "$SOURCE_ROOT/system/libdg/wdgd.c" "$TMP/game/mgs2x/source/system/libdg/wdgd.c"
    cp "$SOURCE_ROOT/system/libdg/wpatch.c" "$TMP/game/mgs2x/source/system/libdg/wpatch.c"
    cp "$SOURCE_ROOT/user/takabe/object/ipupanel.c" \
        "$TMP/game/mgs2x/source/user/takabe/object/ipupanel.c"
    patch --binary --fuzz=0 -d "$TMP/game" -p1 < "$BASE_PATCH" >/dev/null
    patch --binary --fuzz=0 -d "$TMP/game" -p1 < "$STATE_PATCH" >/dev/null
    patch --binary --fuzz=0 --dry-run -d "$TMP/game" -p1 < "$SAFETY_PATCH" >/dev/null
fi

WINE_ROOT="$REPO/../recovered-session/wine-11.0"
if [ -r "$WINE_ROOT/dlls/dmime/performance.c" ] && \
   [ -r "$WINE_ROOT/dlls/dmsynth/synthsink.c" ]; then
    mkdir -p "$TMP/wine/dlls/dmime" "$TMP/wine/dlls/dmsynth"
    cp "$WINE_ROOT/dlls/dmime/performance.c" "$TMP/wine/dlls/dmime/performance.c"
    cp "$WINE_ROOT/dlls/dmsynth/synthsink.c" "$TMP/wine/dlls/dmsynth/synthsink.c"
    patch --fuzz=0 -R -p1 -d "$TMP/wine" < "$PATCH85" >/dev/null
    patch --fuzz=0 -R -p1 -d "$TMP/wine" < "$PATCH84" >/dev/null
    patch --fuzz=0 -p1 -d "$TMP/wine" < "$PATCH84" >/dev/null
    patch --fuzz=0 -p1 -d "$TMP/wine" < "$PATCH85" >/dev/null
fi

[ "$(awk 'NF == 2 {n++} END {print n+0}' "$PRODUCTION")" = 25 ]
[ "$(recorded_hash FINALPLAY22_AUDIT_FIXES.manifest)" = "$(sha256sum "$MANIFEST" | cut -d' ' -f1)" ]
[ "$(recorded_hash patch-mgs2-wpatch-finalplay22.sh)" = "$PATCHER_HASH" ]
[ "$(recorded_hash dmime_p16_curve_state_layout.dll)" = "$DMIME_HASH" ]
[ "$(recorded_hash dmsynth_p38_sink_lifetime.dll)" = "$DMSYNTH_HASH" ]
[ "$(recorded_hash FINALPLAY21_WATER_WPATCH.manifest)" = "$(sha256sum "$ROLLBACK" | cut -d' ' -f1)" ]
[ "$(recorded_hash patch-mgs2-wpatch-novs.sh)" = "$(sha256sum "$REPO/device/patch-mgs2-wpatch-novs.sh" | cut -d' ' -f1)" ]
[ "$(recorded_hash dmsynth_p37_resume_timeline.dll)" = b11c9b6ba2f1d27fcdea822fff37f62187862aa7aeb5527d2efd2a159778ede8 ]
[ "$(recorded_hash dmime_transition1.dll)" = ce3e3f14a62a190966183802c871a5a26a7a3a828c7f23b4d6f0ab9f90ace877 ]
while read -r want file extra; do
    [ -z "${extra:-}" ]
    [ ! -e "$REPO/device/$file" ] ||
        [ "$(sha256sum "$REPO/device/$file" | cut -d' ' -f1)" = "$want" ]
done < "$PRODUCTION"

# FINALPLAY23 is the default since 2026-08-31; FINALPLAY22 must stay packaged
# and one explicit launch away, and the release path must still gate on it.
grep -Fq 'RELEASE_ROUTE=${MGS2_RELEASE_ROUTE:-finalplay23}' "$RELEASE"
grep -Fq 'test_finalplay22_production.sh' "$CURRENT_RELEASE"
grep -Fq 'PRODUCTION="$REPO/device/FINALPLAY23_PRODUCTION.sha256"' "$CURRENT_RELEASE"
grep -Fq 'MANIFEST="$REPO/device/FINALPLAY23_MOVIE_GUARD.manifest"' "$CURRENT_RELEASE"
grep -Fq 'ssh -n -F /dev/null' "$CURRENT_RELEASE"
grep -Fq '[ "$deployed" = "$rows" ]' "$CURRENT_RELEASE"
grep -Fq 'refusing a release table that could contain the legal game image' "$CURRENT_RELEASE"
grep -Fq 'target="$PORTDIR/MGS2-Substance.sh"' "$CURRENT_RELEASE"

echo "ok     FINALPLAY22 is an exact selectable rollback and FINALPLAY21 behind it"
echo "ok     combined route changes only the state-owned game view and two audio DLLs"
echo "ok     fail-closed 58-byte transform ($TRANSFORM_GATE) and patches 84/85 are pinned"
echo "ok     exact 21-row live identity and 25-file rollback-complete bundle are closed"

#!/bin/sh
# Static and exact-transform gate for the bounded wpatch state owner candidate.
set -eu

REPO=$(cd "$(dirname "$0")/.." && pwd)
ENGINE="$REPO/device/launch-play-dxvk-fp17.sh"
WRAPPER="$REPO/device/launch-wpatch-state-ownership-candidate.sh"
PATCHER="$REPO/device/patch-mgs2-wpatch-state-owned.sh"
BASE_PATCH="$REPO/game-patches/02-wpatch-consumer-and-state-isolation.patch"
STATE_PATCH="$REPO/game-patches/04-wpatch-texture-transform-ownership-candidate.patch"
SAFETY_PATCH="$REPO/game-patches/05-wpatch-latent-safety-corrections.patch"
MANIFEST="$REPO/device/WPATCH_STATE_OWNERSHIP_CANDIDATE.manifest"
MANIFEST20="$REPO/device/FINALPLAY20_DMSYNTH_RESUME.manifest"
LOCK="$REPO/device/WPATCH_STATE_OWNERSHIP_CANDIDATE.lock"
TMP=$(mktemp -d /tmp/mgs2-wpatch-state-gate.XXXXXX)
WRONG_OUTPUT=""
CANDIDATE_OUTPUT=""
cleanup() {
    rm -rf "$TMP"
    [ -z "$WRONG_OUTPUT" ] || rm -f "$WRONG_OUTPUT"
    [ -z "$CANDIDATE_OUTPUT" ] || rm -f "$CANDIDATE_OUTPUT"
}
trap cleanup EXIT HUP INT TERM

ORIGINAL_HASH=29759e6f06eaea4d61bb6aef5a5ef45a936eac1e76fa0c3471cf4f231349aaa0
CANDIDATE_HASH=d902ee4398b77653674943f097f79e103d1aa0bc93ce825c0cb0c3d3522b9f88
PATCHER_HASH=0c75034daa9eaace2fcb45d7909a9c57f827d0e2ac2d67ca2602955c11d61e15
BASE_PATCH_HASH=fae7831938717b89aae4c056f553b68a8d21d02ed592420fad6f0f90bd3c5973
STATE_PATCH_HASH=1f4c41382cf411f2f90b57e0f5a207ba7f530e27d54a657fd584e3ecd3a985ab
SAFETY_PATCH_HASH=15bf5c0594145b2f69c87f3be22da75d14607dfc992b15bab79130a8c748b026

lock_value() { awk -v key="$1" '$1==key {print $2}' "$LOCK"; }

grep -Fq 'wpatch-state-ownership-candidate)' "$ENGINE"
grep -Fq 'PLAY_IDENTITY_MANIFEST=WPATCH_STATE_OWNERSHIP_CANDIDATE.manifest' "$ENGINE"
grep -Fq 'GAME_EXE_PATCH=wpatch-state-owned' "$ENGINE"
grep -Fq 'patch-mgs2-wpatch-state-owned.sh' "$ENGINE"
grep -Fq "patcher_hash=$PATCHER_HASH" "$ENGINE"
grep -Fq "patched_hash=$CANDIDATE_HASH" "$ENGINE"
grep -Fq 'export MGS2_PRODUCTION_ROUTE=wpatch-state-ownership-candidate' "$WRAPPER"

rows=$(awk '$1 !~ /^#/ && NF {n++} END {print n+0}' "$MANIFEST")
[ "$rows" = 21 ] || { echo "FAIL: candidate manifest has $rows rows, expected 21" >&2; exit 1; }
awk '$1=="/storage/roms/ports/MGS2-Substance/game/bin/mgs2_sse_rg353vs_port.exe" {print $2}' \
    "$MANIFEST" | grep -Fxq "$CANDIDATE_HASH"
awk '$1=="/storage/roms/ports/MGS2-Substance/patch-mgs2-wpatch-state-owned.sh" {print $2}' \
    "$MANIFEST" | grep -Fxq "$PATCHER_HASH"
awk '$1 !~ /^#/ && NF && $1!="/storage/roms/ports/MGS2-Substance/game/bin/mgs2_sse_rg353vs_port.exe" && \
     $1!="/storage/roms/ports/MGS2-Substance/patch-mgs2-wpatch-state-owned.sh"' \
    "$MANIFEST" > "$TMP/candidate-rest"
awk '$1 !~ /^#/ && NF' "$MANIFEST20" > "$TMP/fp20"
cmp "$TMP/fp20" "$TMP/candidate-rest"

[ "$(lock_value game_exe_original_sha256)" = "$ORIGINAL_HASH" ]
[ "$(lock_value game_exe_candidate_sha256)" = "$CANDIDATE_HASH" ]
[ "$(sha256sum "$REPO/$(lock_value game_exe_patcher)" | cut -d' ' -f1)" = "$PATCHER_HASH" ]
[ "$(sha256sum "$REPO/$(lock_value game_base_source_patch)" | cut -d' ' -f1)" = "$BASE_PATCH_HASH" ]
[ "$(sha256sum "$REPO/$(lock_value game_state_source_patch)" | cut -d' ' -f1)" = "$STATE_PATCH_HASH" ]
[ "$(sha256sum "$REPO/$(lock_value game_safety_source_patch)" | cut -d' ' -f1)" = "$SAFETY_PATCH_HASH" ]
[ "$(sha256sum "$REPO/$(lock_value launcher_engine)" | cut -d' ' -f1)" = \
  "$(lock_value launcher_engine_sha256)" ]
[ "$(sha256sum "$REPO/$(lock_value launcher_wrapper)" | cut -d' ' -f1)" = \
  "$(lock_value launcher_wrapper_sha256)" ]
[ "$(sha256sum "$REPO/$(lock_value identity_manifest)" | cut -d' ' -f1)" = \
  "$(lock_value identity_manifest_sha256)" ]

WRONG_OUTPUT=$(mktemp /tmp/mgs2-wpatch-state.wrong.XXXXXX)
if "$PATCHER" "$TMP/wrong.exe" "$WRONG_OUTPUT" >/dev/null 2>&1; then
    echo "FAIL: candidate patcher accepted an unknown game EXE" >&2
    exit 1
fi
[ ! -s "$WRONG_OUTPUT" ]

LOCAL_EXE="$REPO/../recovered-session/binaries/mgs2_sse_rg353vs_port.exe"
[ -r "$LOCAL_EXE" ] || \
    LOCAL_EXE="$REPO/../recovered-session/local-reference/game/bin/mgs2_sse_rg353vs_port.exe"
if [ -r "$LOCAL_EXE" ]; then
    if "$PATCHER" "$LOCAL_EXE" "$LOCAL_EXE" >/dev/null 2>&1; then
        echo "FAIL: candidate patcher accepted an in-place game EXE edit" >&2
        exit 1
    fi
    if "$PATCHER" "$LOCAL_EXE" "$TMP/forbidden.exe" >/dev/null 2>&1; then
        echo "FAIL: candidate patcher accepted output outside its private /tmp name" >&2
        exit 1
    fi
    CANDIDATE_OUTPUT=$(mktemp /tmp/mgs2-wpatch-state.gate.XXXXXX)
    "$PATCHER" "$LOCAL_EXE" "$CANDIDATE_OUTPUT" >/dev/null
    [ "$(sha256sum "$CANDIDATE_OUTPUT" | cut -d' ' -f1)" = "$CANDIDATE_HASH" ]
    [ "$(cmp -l "$LOCAL_EXE" "$CANDIDATE_OUTPUT" | awk 'END {print NR+0}')" = 58 ]
    [ "$(od -An -v -tx1 -j 4860090 -N 1 "$CANDIDATE_OUTPUT" | tr -d ' \n')" = 00 ]
    [ "$(od -An -v -tx1 -j 528 -N 4 "$CANDIDATE_OUTPUT" | tr -d ' \n')" = 40a65500 ]
    [ "$(od -An -v -tx1 -j 5009385 -N 5 "$CANDIDATE_OUTPUT" | tr -d ' \n')" = e832460900 ]
    [ "$(od -An -v -tx1 -j 5617184 -N 19 "$CANDIDATE_OUTPUT" | tr -d ' \n')" = \
      6a026a186a00e8c5a3f4ff83c40ce937a8faff ]
    rm -f "$CANDIDATE_OUTPUT"
    CANDIDATE_OUTPUT=""
fi

SOURCE_ROOT="$REPO/../mgs_source/MGS2-Source-main/mgs2x/source"
if [ -r "$SOURCE_ROOT/system/libdg/wdgd.c" ] && \
        [ -r "$SOURCE_ROOT/system/libdg/wpatch.c" ] && \
        [ -r "$SOURCE_ROOT/user/takabe/object/ipupanel.c" ]; then
    mkdir -p "$TMP/source/mgs2x/source/system/libdg" \
        "$TMP/source/mgs2x/source/user/takabe/object"
    cp "$SOURCE_ROOT/system/libdg/wdgd.c" "$TMP/source/mgs2x/source/system/libdg/wdgd.c"
    cp "$SOURCE_ROOT/system/libdg/wpatch.c" "$TMP/source/mgs2x/source/system/libdg/wpatch.c"
    cp "$SOURCE_ROOT/user/takabe/object/ipupanel.c" \
        "$TMP/source/mgs2x/source/user/takabe/object/ipupanel.c"
    patch --binary --fuzz=0 -d "$TMP/source" -p1 < "$BASE_PATCH" >/dev/null
    patch --binary --fuzz=0 -d "$TMP/source" -p1 < "$STATE_PATCH" >/dev/null
    patch --binary --fuzz=0 --dry-run -d "$TMP/source" -p1 < "$SAFETY_PATCH" >/dev/null
fi

echo "ok     candidate differs from FINALPLAY20 only by its temporary game-image view"
echo "ok     COUNT2 is source-recorded immediately before the non-VS UV matrix upload"
echo "ok     exact 21-row identity and fail-closed 58-byte transform are pinned"

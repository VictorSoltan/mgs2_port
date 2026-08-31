#!/bin/sh
# Static fail-closed gate for the bounded wpatch flicker candidate.
set -eu

REPO=$(cd "$(dirname "$0")/.." && pwd)
ENGINE="$REPO/device/launch-play-dxvk-fp17.sh"
WRAPPER="$REPO/device/launch-wpatch-isolation-candidate.sh"
PATCHER="$REPO/device/patch-mgs2-wpatch-isolated.sh"
SOURCE_PATCH="$REPO/game-patches/02-wpatch-consumer-and-state-isolation.patch"
MANIFEST="$REPO/device/WPATCH_ISOLATION_CANDIDATE.manifest"
MANIFEST20="$REPO/device/FINALPLAY20_DMSYNTH_RESUME.manifest"
LOCK="$REPO/device/WPATCH_ISOLATION_CANDIDATE.lock"
TMP=$(mktemp -d /tmp/mgs2-wpatch-isolation-gate.XXXXXX)
WRONG_OUTPUT=""
CANDIDATE_OUTPUT=""
cleanup() {
    rm -rf "$TMP"
    [ -z "$WRONG_OUTPUT" ] || rm -f "$WRONG_OUTPUT"
    [ -z "$CANDIDATE_OUTPUT" ] || rm -f "$CANDIDATE_OUTPUT"
}
trap cleanup EXIT HUP INT TERM

ORIGINAL_HASH=29759e6f06eaea4d61bb6aef5a5ef45a936eac1e76fa0c3471cf4f231349aaa0
CANDIDATE_HASH=e4a54598cefa2f7d19e02aa519e030b21a19424f163e3fdeebe32bb111cde1ce
PATCHER_HASH=5dcc4e1fd76df35e23539bec67a42fda680e1775422a52c6cc882c347026cbe0
SOURCE_PATCH_HASH=fae7831938717b89aae4c056f553b68a8d21d02ed592420fad6f0f90bd3c5973

lock_value() { awk -v key="$1" '$1==key {print $2}' "$LOCK"; }

grep -Fq 'wpatch-isolation-candidate)' "$ENGINE"
grep -Fq 'PLAY_IDENTITY_MANIFEST=WPATCH_ISOLATION_CANDIDATE.manifest' "$ENGINE"
grep -Fq 'GAME_EXE_PATCH=wpatch-isolated' "$ENGINE"
grep -Fq 'patch-mgs2-wpatch-isolated.sh' "$ENGINE"
grep -Fq "patcher_hash=$PATCHER_HASH" "$ENGINE"
grep -Fq "patched_hash=$CANDIDATE_HASH" "$ENGINE"
grep -Fq 'export MGS2_PRODUCTION_ROUTE=wpatch-isolation-candidate' "$WRAPPER"

rows=$(awk '$1 !~ /^#/ && NF {n++} END {print n+0}' "$MANIFEST")
[ "$rows" = 21 ] || { echo "FAIL: candidate manifest has $rows rows, expected 21" >&2; exit 1; }
awk '$1=="/storage/roms/ports/MGS2-Substance/game/bin/mgs2_sse_rg353vs_port.exe" {print $2}' \
    "$MANIFEST" | grep -Fxq "$CANDIDATE_HASH"
awk '$1=="/storage/roms/ports/MGS2-Substance/patch-mgs2-wpatch-isolated.sh" {print $2}' \
    "$MANIFEST" | grep -Fxq "$PATCHER_HASH"
awk '$1 !~ /^#/ && NF && $1!="/storage/roms/ports/MGS2-Substance/game/bin/mgs2_sse_rg353vs_port.exe" && \
     $1!="/storage/roms/ports/MGS2-Substance/patch-mgs2-wpatch-isolated.sh"' \
    "$MANIFEST" > "$TMP/candidate-rest"
awk '$1 !~ /^#/ && NF' "$MANIFEST20" > "$TMP/fp20"
cmp "$TMP/fp20" "$TMP/candidate-rest"

[ "$(lock_value game_exe_original_sha256)" = "$ORIGINAL_HASH" ]
[ "$(lock_value game_exe_candidate_sha256)" = "$CANDIDATE_HASH" ]
[ "$(sha256sum "$REPO/$(lock_value game_exe_patcher)" | cut -d' ' -f1)" = "$PATCHER_HASH" ]
[ "$(sha256sum "$REPO/$(lock_value game_source_patch)" | cut -d' ' -f1)" = "$SOURCE_PATCH_HASH" ]
[ "$(sha256sum "$REPO/$(lock_value launcher_engine)" | cut -d' ' -f1)" = \
  "$(lock_value launcher_engine_sha256)" ]
[ "$(sha256sum "$REPO/$(lock_value launcher_wrapper)" | cut -d' ' -f1)" = \
  "$(lock_value launcher_wrapper_sha256)" ]
[ "$(sha256sum "$REPO/$(lock_value identity_manifest)" | cut -d' ' -f1)" = \
  "$(lock_value identity_manifest_sha256)" ]

# Unknown input and any non-private output path must fail before a game image is
# written. This also locks the stronger no-in-place boundary absent from fp21.
WRONG_OUTPUT=$(mktemp /tmp/mgs2-wpatch-isolated.wrong.XXXXXX)
if "$PATCHER" "$TMP/wrong.exe" "$WRONG_OUTPUT" >/dev/null 2>&1; then
    echo "FAIL: candidate patcher accepted an unknown game EXE" >&2
    exit 1
fi
[ ! -s "$WRONG_OUTPUT" ]

LOCAL_EXE="$REPO/../recovered-session/local-reference/game/bin/mgs2_sse_rg353vs_port.exe"
if [ -r "$LOCAL_EXE" ]; then
    if "$PATCHER" "$LOCAL_EXE" "$TMP/forbidden.exe" >/dev/null 2>&1; then
        echo "FAIL: candidate patcher accepted output outside its private /tmp name" >&2
        exit 1
    fi
    CANDIDATE_OUTPUT=$(mktemp /tmp/mgs2-wpatch-isolated.gate.XXXXXX)
    "$PATCHER" "$LOCAL_EXE" "$CANDIDATE_OUTPUT" >/dev/null
    [ "$(sha256sum "$CANDIDATE_OUTPUT" | cut -d' ' -f1)" = "$CANDIDATE_HASH" ]
    [ "$(cmp -l "$LOCAL_EXE" "$CANDIDATE_OUTPUT" | awk 'END {print NR+0}')" = 36 ]
    [ "$(od -An -v -tx1 -j 528 -N 4 "$CANDIDATE_OUTPUT" | tr -d ' \n')" = 20a65500 ]
    [ "$(od -An -v -tx1 -j 5008401 -N 5 "$CANDIDATE_OUTPUT" | tr -d ' \n')" = e9ca490900 ]
    [ "$(od -An -v -tx1 -j 5008657 -N 5 "$CANDIDATE_OUTPUT" | tr -d ' \n')" = e8fa480900 ]
    rm -f "$CANDIDATE_OUTPUT"
    CANDIDATE_OUTPUT=""
fi

SOURCE_ROOT="$REPO/../mgs_source/MGS2-Source-main/mgs2x/source/system/libdg"
if [ -r "$SOURCE_ROOT/wdgd.c" ] && [ -r "$SOURCE_ROOT/wpatch.c" ]; then
    mkdir -p "$TMP/source/mgs2x/source/system/libdg"
    cp "$SOURCE_ROOT/wdgd.c" "$TMP/source/mgs2x/source/system/libdg/wdgd.c"
    cp "$SOURCE_ROOT/wpatch.c" "$TMP/source/mgs2x/source/system/libdg/wpatch.c"
    patch --binary --dry-run -d "$TMP/source" -p1 < "$SOURCE_PATCH" >/dev/null
fi

echo "ok     candidate differs from FINALPLAY20 only by its temporary game-image view"
echo "ok     water fallback, IPU shader isolation and lighting cleanup are source-recorded"
echo "ok     exact 21-row identity and fail-closed 36-byte transform are pinned"

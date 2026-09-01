#!/bin/sh
# Static, reconstruction and fail-closed gate for FINALPLAY23 production.
#
# FINALPLAY23 is FINALPLAY22 plus exactly two bytes in the temporary game view.
# This gate exists to keep that claim literal: it proves the two byte offsets,
# proves nothing else in the live identity moved, and proves the source-level
# record still applies to the recovered game source.
set -eu

REPO=$(cd "$(dirname "$0")/.." && pwd)
SELECTOR="$REPO/device/launch-play.sh"
ENGINE="$REPO/device/launch-play-dxvk-fp17.sh"
WRAPPER="$REPO/device/launch-play-dxvk-fp23.sh"
PATCHER="$REPO/device/patch-mgs2-wpatch-finalplay23.sh"
ROLLBACK_PATCHER="$REPO/device/patch-mgs2-wpatch-finalplay22.sh"
MANIFEST="$REPO/device/FINALPLAY23_MOVIE_GUARD.manifest"
X86LIBS_MANIFEST="$REPO/device/FINALPLAY_RUNTIME_X86LIBS.sha256"
ROLLBACK="$REPO/device/FINALPLAY22_AUDIT_FIXES.manifest"
PRODUCTION="$REPO/device/FINALPLAY23_PRODUCTION.sha256"
LOCK="$REPO/device/FINALPLAY.lock"
RELEASE="$REPO/harness/make_release.sh"
CURRENT_RELEASE="$REPO/harness/make_current_release.sh"
MOVIE_PATCH="$REPO/game-patches/06-movie-null-graph-guard.patch"
TMP=$(mktemp -d /tmp/mgs2-finalplay23-gate.XXXXXX)
EXTERNAL_TMP=""
cleanup() {
    rm -rf "$TMP"
    [ -z "$EXTERNAL_TMP" ] || rm -f "$EXTERNAL_TMP"
}
trap cleanup EXIT HUP INT TERM

ORIGINAL_HASH=29759e6f06eaea4d61bb6aef5a5ef45a936eac1e76fa0c3471cf4f231349aaa0
ROLLBACK_GAME_HASH=d902ee4398b77653674943f097f79e103d1aa0bc93ce825c0cb0c3d3522b9f88
GAME_HASH=d6b81257a82348299675adf863c9ad884c68c438b032fe20a75f18a094d29cd5
PATCHER_HASH=c607805bd2afc391d267364fe8d63891bcf89f03ca18736eb561e276445889a8
WRAPPER_OFFSET=4696000
CLOCK_OFFSET=4697600

lock_value() { awk -v key="$1" '$1==key {print $2}' "$LOCK"; }
recorded_hash() { awk -v name="$1" '$2==name {print $1}' "$PRODUCTION"; }
manifest_hash() { awk -v path="$1" '$1==path {print $2}' "$MANIFEST"; }

bash -n "$ENGINE"
sh -n "$SELECTOR"
sh -n "$WRAPPER"
sh -n "$PATCHER"

# FINALPLAY23 is the default and FINALPLAY22 must remain one explicit launch away.
grep -Fq 'dxvk|dxvk23|fp23)' "$SELECTOR"
grep -Fq 'exec "$HERE/launch-play-dxvk-fp23.sh"' "$SELECTOR"
grep -Fq 'dxvk22|fp22)' "$SELECTOR"
grep -Fq 'exec "$HERE/launch-play-dxvk-fp22.sh"' "$SELECTOR"
grep -Fq 'dxvk21|fp21)' "$SELECTOR"
grep -Fq 'export MGS2_PRODUCTION_ROUTE=finalplay23' "$WRAPPER"
grep -Fq 'finalplay23)' "$ENGINE"
grep -Fq 'finalplay22)' "$ENGINE"
grep -Fq 'PLAY_IDENTITY_MANIFEST=FINALPLAY23_MOVIE_GUARD.manifest' "$ENGINE"
grep -Fq 'GAME_EXE_PATCH=wpatch-finalplay23' "$ENGINE"
grep -Fq "patcher_hash=$PATCHER_HASH" "$ENGINE"
grep -Fq "patched_hash=$GAME_HASH" "$ENGINE"
grep -Fq '/tmp/mgs2-wpatch-finalplay23.*)' "$PATCHER"

# The audio, input, renderer and box86 route are inherited unchanged.
grep -Fq 'MGS2_BOX86_BIN=box86-fp26-wayland-text-input-production' "$ENGINE"
grep -Fq 'MGS2_DMSYNTH_DLL=dmsynth_p38_sink_lifetime.dll' "$ENGINE"
grep -Fq 'MGS2_DMIME_DLL=dmime_p16_curve_state_layout.dll' "$ENGINE"
grep -Fq 'INPUT_ROUTE=immediate-production' "$ENGINE"
grep -Fq 'EXPECTED_BIND_MOUNTS=8' "$ENGINE"
grep -Fq 'EXPECTED_IDENTITY_ROWS=21' "$ENGINE"
grep -Fq 'X86LIBS_MANIFEST="$HERE/FINALPLAY_RUNTIME_X86LIBS.sha256"' "$WRAPPER"
grep -Fq 'verify_x86libs' "$WRAPPER"

rows=$(awk '$1 !~ /^#/ && NF {n++} END {print n+0}' "$MANIFEST")
[ "$rows" = 21 ] || { echo "FAIL: FINALPLAY23 manifest has $rows rows, expected 21" >&2; exit 1; }
x86_rows=$(awk '$1 !~ /^#/ && NF == 2 {n++} END {print n+0}' "$X86LIBS_MANIFEST")
[ "$x86_rows" = 10 ] || { echo "FAIL: x86 runtime manifest has $x86_rows rows, expected 10" >&2; exit 1; }
[ "$(awk '$1 !~ /^#/ && NF == 2 {print $2}' "$X86LIBS_MANIFEST" | sort | uniq -d | wc -l)" = 0 ]
[ "$(awk '$1 !~ /^#/ && NF == 2 && $2 ~ /\// {n++} END {print n+0}' "$X86LIBS_MANIFEST")" = 0 ]

# The wrapper must stop before the shared engine if a clean bundle omitted its
# dependency directory. This is the exact packaging regression found on device.
mkdir -p "$TMP/x86-preflight"
cp "$WRAPPER" "$TMP/x86-preflight/launch-play-dxvk-fp23.sh"
cp "$X86LIBS_MANIFEST" "$TMP/x86-preflight/FINALPLAY_RUNTIME_X86LIBS.sha256"
printf '#!/bin/sh\ntouch "%s"\n' "$TMP/engine-ran" > \
    "$TMP/x86-preflight/launch-play-dxvk-fp17.sh"
chmod +x "$TMP/x86-preflight/launch-play-dxvk-fp17.sh"
if "$TMP/x86-preflight/launch-play-dxvk-fp23.sh" >/dev/null 2>&1; then
    echo "FAIL: FINALPLAY23 accepted a bundle with no x86libs directory" >&2
    exit 1
fi
[ ! -e "$TMP/engine-ran" ]
[ "$(manifest_hash /storage/roms/ports/MGS2-Substance/game/bin/mgs2_sse_rg353vs_port.exe)" = "$GAME_HASH" ]
[ "$(manifest_hash /storage/roms/ports/MGS2-Substance/patch-mgs2-wpatch-finalplay23.sh)" = "$PATCHER_HASH" ]

# FINALPLAY23 differs from exact FINALPLAY22 at the helper row and the game view
# row and nowhere else. Nineteen live identity rows must be byte-for-byte equal.
awk '$1 !~ /^#/ && NF && \
     $1!="/storage/roms/ports/MGS2-Substance/patch-mgs2-wpatch-finalplay23.sh" && \
     $1!="/storage/roms/ports/MGS2-Substance/game/bin/mgs2_sse_rg353vs_port.exe"' \
     "$MANIFEST" > "$TMP/fp23-rest"
awk '$1 !~ /^#/ && NF && \
     $1!="/storage/roms/ports/MGS2-Substance/patch-mgs2-wpatch-finalplay22.sh" && \
     $1!="/storage/roms/ports/MGS2-Substance/game/bin/mgs2_sse_rg353vs_port.exe"' \
     "$ROLLBACK" > "$TMP/fp22-rest"
cmp "$TMP/fp22-rest" "$TMP/fp23-rest"
[ "$(awk 'END {print NR}' "$TMP/fp23-rest")" = 19 ]

[ "$(lock_value game_exe_original_sha256)" = "$ORIGINAL_HASH" ]
[ "$(lock_value game_exe_finalplay22_sha256)" = "$ROLLBACK_GAME_HASH" ]
[ "$(lock_value game_exe_finalplay23_sha256)" = "$GAME_HASH" ]
[ "$(lock_value game_exe_finalplay23_wrapper_offset)" = "$WRAPPER_OFFSET" ]
[ "$(lock_value game_exe_finalplay23_clock_offset)" = "$CLOCK_OFFSET" ]
[ "$(lock_value game_exe_finalplay23_wrapper_original_byte)" = 53 ]
[ "$(lock_value game_exe_finalplay23_clock_original_byte)" = 51 ]
[ "$(sha256sum "$REPO/$(lock_value game_finalplay23_patcher)" | cut -d' ' -f1)" = "$PATCHER_HASH" ]
[ "$(sha256sum "$MOVIE_PATCH" | cut -d' ' -f1)" = \
  "$(lock_value game_finalplay23_movie_source_patch_sha256)" ]

# The patcher must refuse anything but the pinned original, an in-place edit and
# any output outside its private /tmp name.
: > "$TMP/wrong.exe"
EXTERNAL_TMP=$(mktemp /tmp/mgs2-wpatch-finalplay23.wrong.XXXXXX)
if "$PATCHER" "$TMP/wrong.exe" "$EXTERNAL_TMP" >/dev/null 2>&1; then
    echo "FAIL: FINALPLAY23 patcher accepted an unknown game EXE" >&2
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
        echo "FAIL: FINALPLAY23 patcher accepted an in-place edit" >&2
        exit 1
    fi
    if "$PATCHER" "$LOCAL_EXE" "$TMP/forbidden.exe" >/dev/null 2>&1; then
        echo "FAIL: FINALPLAY23 patcher accepted output outside private /tmp" >&2
        exit 1
    fi
    EXTERNAL_TMP=$(mktemp /tmp/mgs2-wpatch-finalplay23.gate.XXXXXX)
    "$PATCHER" "$LOCAL_EXE" "$EXTERNAL_TMP" >/dev/null
    [ "$(sha256sum "$EXTERNAL_TMP" | cut -d' ' -f1)" = "$GAME_HASH" ]
    [ "$(cmp -l "$LOCAL_EXE" "$EXTERNAL_TMP" | awk 'END {print NR+0}')" = 60 ]

    # And the difference against the exact FINALPLAY22 view is those two bytes,
    # both `ret` replacing a function entry push. cmp -l reports 1-based
    # offsets and octal values.
    ROLLBACK_TMP=$(mktemp /tmp/mgs2-wpatch-finalplay22.gate.XXXXXX)
    "$ROLLBACK_PATCHER" "$LOCAL_EXE" "$ROLLBACK_TMP" >/dev/null
    [ "$(sha256sum "$ROLLBACK_TMP" | cut -d' ' -f1)" = "$ROLLBACK_GAME_HASH" ]
    cmp -l "$ROLLBACK_TMP" "$EXTERNAL_TMP" > "$TMP/two-bytes" || true
    rm -f "$ROLLBACK_TMP"
    printf '%s 123 303\n%s 121 303\n' \
        "$((WRAPPER_OFFSET + 1))" "$((CLOCK_OFFSET + 1))" > "$TMP/two-bytes-want"
    awk '{print $1, $2, $3}' "$TMP/two-bytes" > "$TMP/two-bytes-got"
    cmp "$TMP/two-bytes-want" "$TMP/two-bytes-got"

    rm -f "$EXTERNAL_TMP"
    EXTERNAL_TMP=""
    TRANSFORM_GATE=executed
fi

# The source record must still apply to the recovered game source.
SOURCE_ROOT="$REPO/../mgs_source/MGS2-Source-main/mgs2x/source"
SOURCE_GATE=absent
if [ -r "$SOURCE_ROOT/game/windecode.cpp" ]; then
    mkdir -p "$TMP/game/mgs2x/source/game"
    cp "$SOURCE_ROOT/game/windecode.cpp" "$TMP/game/mgs2x/source/game/windecode.cpp"
    patch --binary --fuzz=0 -d "$TMP/game" -p1 < "$MOVIE_PATCH" >/dev/null
    patch --binary --fuzz=0 -R --dry-run -d "$TMP/game" -p1 < "$MOVIE_PATCH" >/dev/null
    SOURCE_GATE=applied
fi

[ "$(awk 'NF == 2 {n++} END {print n+0}' "$PRODUCTION")" = 39 ]
[ "$(recorded_hash FINALPLAY23_MOVIE_GUARD.manifest)" = "$(sha256sum "$MANIFEST" | cut -d' ' -f1)" ]
[ "$(recorded_hash FINALPLAY_RUNTIME_X86LIBS.sha256)" = "$(sha256sum "$X86LIBS_MANIFEST" | cut -d' ' -f1)" ]
while read -r want file extra; do
    case "$want" in ''|\#*) continue;; esac
    [ -z "${extra:-}" ]
    [ "$(recorded_hash "x86libs/$file")" = "$want" ]
done < "$X86LIBS_MANIFEST"
[ "$(recorded_hash patch-mgs2-wpatch-finalplay23.sh)" = "$PATCHER_HASH" ]
[ "$(recorded_hash launch-play-dxvk-fp23.sh)" = \
  "$(sha256sum "$REPO/device/launch-play-dxvk-fp23.sh" | cut -d' ' -f1)" ]
[ "$(recorded_hash FINALPLAY22_AUDIT_FIXES.manifest)" = "$(sha256sum "$ROLLBACK" | cut -d' ' -f1)" ]
[ "$(recorded_hash patch-mgs2-wpatch-finalplay22.sh)" = \
  "$(sha256sum "$ROLLBACK_PATCHER" | cut -d' ' -f1)" ]
[ "$(recorded_hash launch-play.sh)" = "$(sha256sum "$SELECTOR" | cut -d' ' -f1)" ]
[ "$(recorded_hash launch-play-dxvk-fp17.sh)" = "$(sha256sum "$ENGINE" | cut -d' ' -f1)" ]
while read -r want file extra; do
    [ -z "${extra:-}" ]
    [ ! -e "$REPO/device/$file" ] ||
        [ "$(sha256sum "$REPO/device/$file" | cut -d' ' -f1)" = "$want" ]
done < "$PRODUCTION"

grep -Fq 'RELEASE_ROUTE=${MGS2_RELEASE_ROUTE:-finalplay23}' "$RELEASE"
grep -Fq 'finalplay23)' "$RELEASE"
grep -Fq 'PRODUCTION="$REPO/device/FINALPLAY23_PRODUCTION.sha256"' "$CURRENT_RELEASE"
grep -Fq 'MANIFEST="$REPO/device/FINALPLAY23_MOVIE_GUARD.manifest"' "$CURRENT_RELEASE"
grep -Fq '[ "$rows" = 39 ]' "$CURRENT_RELEASE"

echo "ok     FINALPLAY23 is the fixed default and FINALPLAY22 is exact rollback"
echo "ok     the two movie-guard bytes are the only difference from FINALPLAY22"
echo "ok     fail-closed 60-byte transform ($TRANSFORM_GATE), source record $SOURCE_GATE"
echo "ok     exact 21-row live identity and 39-file clean-install bundle are closed"

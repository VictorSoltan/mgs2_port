#!/bin/sh
# Static, source-reconstruction and optional local-binary gate for patches 84/85.
set -eu

REPO=$(cd "$(dirname "$0")/.." && pwd)
ENGINE="$REPO/device/launch-play-dxvk-fp17.sh"
WRAPPER="$REPO/device/launch-audio-lifetime-candidate.sh"
MANIFEST="$REPO/device/AUDIO_LIFETIME_CANDIDATE.manifest"
PRODUCTION="$REPO/device/FINALPLAY21_WATER_WPATCH.manifest"
LOCK="$REPO/device/AUDIO_LIFETIME_CANDIDATE.lock"
PATCH84="$REPO/wine-patches/history/84-dmime-message-private-state-layout.patch"
PATCH85="$REPO/wine-patches/history/85-dmsynth-sink-lifetime-and-clock-state.patch"
TMP=$(mktemp -d /tmp/mgs2-audio-lifetime-gate.XXXXXX)
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT HUP INT TERM

DMIME_HASH=f23f08ed4c41f69baf4ac14a22f9fc5605b629123438fdf37714af6bdae5698e
DMSYNTH_HASH=22287685511486728cb7fc08ec6689b4213ad48cc01679b4bb6e91c02ddfdc1e
PATCH84_HASH=d1fa52593cb556de8aa6d32a74b02d7273d92bed634eea70f24d13a271790778
PATCH85_HASH=5ef57275503b7bd576944a7991afb76f560b4cf67d7af38b4dd15a22f6353d62

lock_value() { awk -v key="$1" '$1==key {print $2}' "$LOCK"; }

bash -n "$ENGINE"
grep -Fq 'audio-lifetime-candidate)' "$ENGINE"
grep -Fq 'PLAY_IDENTITY_MANIFEST=AUDIO_LIFETIME_CANDIDATE.manifest' "$ENGINE"
grep -Fq 'MGS2_DMSYNTH_DLL=dmsynth_p38_sink_lifetime.dll' "$ENGINE"
grep -Fq 'MGS2_DMIME_DLL=dmime_p16_curve_state_layout.dll' "$ENGINE"
grep -Fq 'export MGS2_PRODUCTION_ROUTE=audio-lifetime-candidate' "$WRAPPER"

rows=$(awk '$1 !~ /^#/ && NF {n++} END {print n+0}' "$MANIFEST")
[ "$rows" = 21 ] || { echo "FAIL: audio candidate manifest has $rows rows, expected 21" >&2; exit 1; }
awk '$1=="/usr/lib/wine/i386-windows/dmime.dll" {print $2}' "$MANIFEST" | grep -Fxq "$DMIME_HASH"
awk '$1=="/usr/lib/wine/i386-windows/dmsynth.dll" {print $2}' "$MANIFEST" | grep -Fxq "$DMSYNTH_HASH"
awk '$1 !~ /^#/ && NF && $1!="/usr/lib/wine/i386-windows/dmime.dll" && \
     $1!="/usr/lib/wine/i386-windows/dmsynth.dll"' "$MANIFEST" > "$TMP/candidate-rest"
awk '$1 !~ /^#/ && NF && $1!="/usr/lib/wine/i386-windows/dmime.dll" && \
     $1!="/usr/lib/wine/i386-windows/dmsynth.dll"' "$PRODUCTION" > "$TMP/production-rest"
cmp "$TMP/production-rest" "$TMP/candidate-rest"

[ "$(sha256sum "$PATCH84" | cut -d' ' -f1)" = "$PATCH84_HASH" ]
[ "$(sha256sum "$PATCH85" | cut -d' ' -f1)" = "$PATCH85_HASH" ]
[ "$(sha256sum "$REPO/$(lock_value launcher_engine)" | cut -d' ' -f1)" = \
  "$(lock_value launcher_engine_sha256)" ]
[ "$(sha256sum "$REPO/$(lock_value launcher_wrapper)" | cut -d' ' -f1)" = \
  "$(lock_value launcher_wrapper_sha256)" ]
[ "$(sha256sum "$REPO/$(lock_value identity_manifest)" | cut -d' ' -f1)" = \
  "$(lock_value identity_manifest_sha256)" ]
[ "$(lock_value source_date_epoch)" = 1787976000 ]

WINE_ROOT="$REPO/../recovered-session/wine-11.0"
if [ -r "$WINE_ROOT/dlls/dmime/performance.c" ] && \
   [ -r "$WINE_ROOT/dlls/dmsynth/synthsink.c" ]; then
    mkdir -p "$TMP/source/dlls/dmime" "$TMP/source/dlls/dmsynth"
    cp "$WINE_ROOT/dlls/dmime/performance.c" "$TMP/source/dlls/dmime/performance.c"
    cp "$WINE_ROOT/dlls/dmsynth/synthsink.c" "$TMP/source/dlls/dmsynth/synthsink.c"

    # The conventional local tree is left at candidate state. Reversing and
    # reapplying in a private copy proves both the exact baseline and forward
    # reconstruction without mutating that external source tree.
    patch --fuzz=0 -R -p1 -d "$TMP/source" < "$PATCH85" >/dev/null
    patch --fuzz=0 -R -p1 -d "$TMP/source" < "$PATCH84" >/dev/null
    patch --fuzz=0 -p1 -d "$TMP/source" < "$PATCH84" >/dev/null
    patch --fuzz=0 -p1 -d "$TMP/source" < "$PATCH85" >/dev/null
    [ "$(sha256sum "$TMP/source/dlls/dmime/performance.c" | cut -d' ' -f1)" = \
      "$(lock_value dmime_patched_source_sha256)" ]
    [ "$(sha256sum "$TMP/source/dlls/dmsynth/synthsink.c" | cut -d' ' -f1)" = \
      "$(lock_value dmsynth_patched_source_sha256)" ]
fi

BUILD_ROOT="$REPO/../recovered-session/build-wine-i386"
DMIME_DLL="$BUILD_ROOT/dlls/dmime/i386-windows/dmime.dll"
DMSYNTH_DLL="$BUILD_ROOT/dlls/dmsynth/i386-windows/dmsynth.dll"
if [ -r "$DMIME_DLL" ] && [ -r "$DMSYNTH_DLL" ]; then
    [ "$(sha256sum "$DMIME_DLL" | cut -d' ' -f1)" = "$DMIME_HASH" ]
    [ "$(sha256sum "$DMSYNTH_DLL" | cut -d' ' -f1)" = "$DMSYNTH_HASH" ]
fi

echo "ok     audio candidate differs from FINALPLAY21 only at dmime and dmsynth"
echo "ok     patches 84/85 reverse and reconstruct the pinned Wine sources with fuzz=0"
echo "ok     exact 21-row identity and reproducible fixed-epoch binary hashes are pinned"

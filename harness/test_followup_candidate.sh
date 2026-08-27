#!/bin/sh
# Static fail-closed gate for the combined p25 + immediate-input candidate.
set -eu

REPO=$(cd "$(dirname "$0")/.." && pwd)
ENGINE="$REPO/device/launch-play-dxvk-fp17.sh"
WRAPPER="$REPO/device/launch-input-immediate-candidate.sh"
MANIFEST="$REPO/device/BOX86_WAYLAND_TEXT_INPUT_CANDIDATE.manifest"
FP18="$REPO/device/FINALPLAY18_WAYLAND_ABI.manifest"
LOCK="$REPO/device/FOLLOWUP_CANDIDATE.lock"
BOX_HASH=1ff20d6d36dbbabd5a5aadd9ab677f0e02f6f06ab119f8a3c9952175db45e4cd
INPUT_HASH=49c782dad9da50cb0f5bb9e37821104e5089563feb24c7b0303117b75196b43a
TMP=$(mktemp -d /tmp/mgs2-followup-candidate.XXXXXX)
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT HUP INT TERM

grep -Fq 'wayland-p25-candidate)' "$ENGINE"
grep -Fq 'MGS2_BOX86_BIN=box86-fp25-wayland-text-input-candidate' "$ENGINE"
grep -Fq 'PLAY_IDENTITY_MANIFEST=BOX86_WAYLAND_TEXT_INPUT_CANDIDATE.manifest' "$ENGINE"
grep -Fq 'INPUT_ROUTE=immediate-candidate' "$ENGINE"
grep -Fq 'export MGS2_PRODUCTION_ROUTE=wayland-p25-candidate' "$WRAPPER"

rows=$(awk '$1 !~ /^#/ && NF {n++} END {print n+0}' "$MANIFEST")
[ "$rows" = 19 ] || { echo "FAIL: candidate manifest has $rows rows" >&2; exit 1; }
awk '$1=="/usr/bin/box86" {print $2}' "$MANIFEST" | grep -Fxq "$BOX_HASH"
awk '$1=="/storage/roms/ports/MGS2-Substance/gptokeyb-mgs2-immediate" {print $2}' \
    "$MANIFEST" | grep -Fxq "$INPUT_HASH"

awk '$1 !~ /^#/ && $1!="/usr/bin/box86"' "$FP18" > "$TMP/fp18-rest"
awk '$1 !~ /^#/ && $1!="/usr/bin/box86" && \
     $1!="/storage/roms/ports/MGS2-Substance/gptokeyb-mgs2-immediate"' \
    "$MANIFEST" > "$TMP/candidate-rest"
cmp "$TMP/fp18-rest" "$TMP/candidate-rest"

lock_value() { awk -v key="$1" '$1==key {print $2}' "$LOCK"; }
[ "$(lock_value box86_candidate_sha256)" = "$BOX_HASH" ]
[ "$(lock_value gptokeyb_candidate_sha256)" = "$INPUT_HASH" ]
[ "$(sha256sum "$REPO/$(lock_value box86_patch_25)" | cut -d' ' -f1)" = \
  "$(lock_value box86_patch_25_sha256)" ]
[ "$(sha256sum "$REPO/$(lock_value gptokeyb_patch_01)" | cut -d' ' -f1)" = \
  "$(lock_value gptokeyb_patch_01_sha256)" ]

echo "ok     candidate differs from FINALPLAY18 only by p25 Box86 and input helper"
echo "ok     exact 19-row candidate identity and both source patches are pinned"

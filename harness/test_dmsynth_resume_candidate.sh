#!/bin/sh
# Static fail-closed gate for the FINALPLAY19 + dmsynth p35 candidate.
set -eu

REPO=$(cd "$(dirname "$0")/.." && pwd)
ENGINE="$REPO/device/launch-play-dxvk-fp17.sh"
WRAPPER="$REPO/device/launch-dmsynth-resume-p35-candidate.sh"
CANDIDATE="$REPO/device/DMSYNTH_RESUME_P35_CANDIDATE.manifest"
WRAPPER_STALL1="$REPO/device/launch-dmsynth-resume-stall1-candidate.sh"
CANDIDATE_STALL1="$REPO/device/DMSYNTH_RESUME_STALL1_CANDIDATE.manifest"
WRAPPER_P37="$REPO/device/launch-dmsynth-resume-p37-candidate.sh"
CANDIDATE_P37="$REPO/device/DMSYNTH_RESUME_P37_CANDIDATE.manifest"
PRODUCTION="$REPO/device/FINALPLAY19_INPUT_WAYLAND.manifest"
PATCH35="$REPO/wine-patches/history/60-dmsynth-resume-recover.patch"
PATCH37="$REPO/wine-patches/history/83-dmsynth-resume-timeline-rebase.patch"
HASH35=f387ff2d2f0273deee4313442c03c51373dc1ecaae3134c33cafde1a56392d0c
HASH37=b11c9b6ba2f1d27fcdea822fff37f62187862aa7aeb5527d2efd2a159778ede8
TMP=$(mktemp -d /tmp/mgs2-dmsynth-resume-candidate.XXXXXX)
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT HUP INT TERM

grep -Fq 'dmsynth-resume-p35-candidate)' "$ENGINE"
grep -Fq 'MGS2_DMSYNTH_DLL=dmsynth_p35_resume_recover.dll' "$ENGINE"
grep -Fq 'PLAY_IDENTITY_MANIFEST=DMSYNTH_RESUME_P35_CANDIDATE.manifest' "$ENGINE"
grep -Fq 'MGS2_PRODUCTION_ROUTE=dmsynth-resume-p35-candidate' "$WRAPPER"
grep -Fq 'dmsynth-resume-stall1-candidate)' "$ENGINE"
grep -Fq 'MGS2_DMSYNTH_DLL=dmsynth_p35_resume_recover.dll' "$ENGINE"
grep -Fq 'MGS2_DMSYNTH_WATCHDOG_STALL=1' "$ENGINE"
grep -Fq 'PLAY_IDENTITY_MANIFEST=DMSYNTH_RESUME_STALL1_CANDIDATE.manifest' "$ENGINE"
grep -Fq 'MGS2_PRODUCTION_ROUTE=dmsynth-resume-stall1-candidate' "$WRAPPER_STALL1"
grep -Fq 'dmsynth-resume-p37-candidate)' "$ENGINE"
grep -Fq 'MGS2_DMSYNTH_DLL=dmsynth_p37_resume_timeline.dll' "$ENGINE"
grep -Fq 'PLAY_IDENTITY_MANIFEST=DMSYNTH_RESUME_P37_CANDIDATE.manifest' "$ENGINE"
grep -Fq 'MGS2_PRODUCTION_ROUTE=dmsynth-resume-p37-candidate' "$WRAPPER_P37"

[ -s "$PATCH35" ]
[ -s "$PATCH37" ]
grep -Fq 'b11c9b6ba2f1d27fcdea822fff37f62187862aa7aeb5527d2efd2a159778ede8' "$PATCH37"
rows=$(awk '$1 !~ /^#/ && NF {n++} END {print n+0}' "$CANDIDATE")
[ "$rows" = 19 ] || { echo "FAIL: p35 candidate has $rows rows" >&2; exit 1; }
awk '$1=="/usr/lib/wine/i386-windows/dmsynth.dll" {print $2, $3}' "$CANDIDATE" \
    | grep -Fxq "$HASH35 dmsynth_p35_resume_recover.dll"
rows_stall1=$(awk '$1 !~ /^#/ && NF {n++} END {print n+0}' "$CANDIDATE_STALL1")
[ "$rows_stall1" = 19 ] || { echo "FAIL: stall1 candidate has $rows_stall1 rows" >&2; exit 1; }
awk '$1=="/usr/lib/wine/i386-windows/dmsynth.dll" {print $2, $3}' "$CANDIDATE_STALL1" \
    | grep -Fxq "$HASH35 dmsynth_p35_resume_recover.dll"
rows_p37=$(awk '$1 !~ /^#/ && NF {n++} END {print n+0}' "$CANDIDATE_P37")
[ "$rows_p37" = 19 ] || { echo "FAIL: p37 candidate has $rows_p37 rows" >&2; exit 1; }
awk '$1=="/usr/lib/wine/i386-windows/dmsynth.dll" {print $2, $3}' "$CANDIDATE_P37" \
    | grep -Fxq "$HASH37 dmsynth_p37_resume_timeline.dll"
awk '$1 !~ /^#/ && $1!="/usr/lib/wine/i386-windows/dmsynth.dll"' \
    "$PRODUCTION" > "$TMP/production-rest"
awk '$1 !~ /^#/ && $1!="/usr/lib/wine/i386-windows/dmsynth.dll"' \
    "$CANDIDATE" > "$TMP/candidate-rest"
cmp "$TMP/production-rest" "$TMP/candidate-rest"
awk '$1 !~ /^#/ && $1!="/usr/lib/wine/i386-windows/dmsynth.dll"' \
    "$CANDIDATE_STALL1" > "$TMP/candidate-stall1-rest"
cmp "$TMP/production-rest" "$TMP/candidate-stall1-rest"
awk '$1 !~ /^#/ && $1!="/usr/lib/wine/i386-windows/dmsynth.dll"' \
    "$CANDIDATE_P37" > "$TMP/candidate-p37-rest"
cmp "$TMP/production-rest" "$TMP/candidate-p37-rest"

echo "ok     p35 candidate differs from FINALPLAY19 only at dmsynth.dll"
echo "ok     stall1 candidate differs from p35 only by the forced one-tick environment"
echo "ok     p37 candidate differs from FINALPLAY19 only at dmsynth.dll"
echo "ok     exact p35/p37 bytes, 19-row identities and source patches are present"

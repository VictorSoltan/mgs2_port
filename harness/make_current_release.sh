#!/bin/sh
# Assemble the exact current FINALPLAY23 distributable boundary.
#
# This does not store or fetch the legal game EXE and does not redistribute the
# ROCKNIX/Mali system rows in the live identity manifest.  It collects the
# named runtime artifacts, tracked launchers/manifests/config and the carried
# audio DLLs needed by a clean installation.  The exact FINALPLAY21 rollback
# objects are included too. Every byte is checked against the production record
# before it enters the bundle or the device.
set -eu

NAME=${1:?usage: make_current_release.sh <name> [--from-device|--deploy]}
MODE=${2:-}
case "$NAME" in
    ""|.|..|*[!A-Za-z0-9._-]*)
        echo "release name must contain only A-Z, a-z, 0-9, dot, underscore or dash" >&2
        exit 1
        ;;
esac
case "$MODE" in
    "") FETCH_DEVICE=0 ;;
    --from-device|--deploy) FETCH_DEVICE=1 ;;
    *) echo "unknown release mode: $MODE" >&2; exit 1 ;;
esac

REPO=$(cd "$(dirname "$0")/.." && pwd)
_device_set=${MGS2_DEVICE+x}; _device=${MGS2_DEVICE-}
_game_dir_set=${MGS2_GAME_DIR+x}; _game_dir=${MGS2_GAME_DIR-}
_artifact_dir_set=${MGS2_RELEASE_ARTIFACT_DIR+x}
_artifact_dir=${MGS2_RELEASE_ARTIFACT_DIR-}
if [ -r "$REPO/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$REPO/.env"
    set +a
fi
[ "$_device_set" = x ] && MGS2_DEVICE=$_device
[ "$_game_dir_set" = x ] && MGS2_GAME_DIR=$_game_dir
[ "$_artifact_dir_set" = x ] && MGS2_RELEASE_ARTIFACT_DIR=$_artifact_dir

DEV=${MGS2_DEVICE:-root@rg353vs}
GAMEDIR=${MGS2_GAME_DIR:-/storage/roms/ports/MGS2-Substance}
PORTDIR=$(dirname "$GAMEDIR")
ARTIFACT_DIR=${MGS2_RELEASE_ARTIFACT_DIR:-$REPO/binaries}
KNOWN_HOSTS=${MGS2_KNOWN_HOSTS_FILE:-}
OUT="$REPO/release/$NAME"
PRODUCTION="$REPO/device/FINALPLAY23_PRODUCTION.sha256"
MANIFEST="$REPO/device/FINALPLAY23_MOVIE_GUARD.manifest"
TMP=$(mktemp -d /tmp/mgs2-current-release.XXXXXX)
OUT_CREATED=0
BUNDLE_COMPLETE=0
cleanup() {
    rm -rf "$TMP"
    if [ "$OUT_CREATED" = 1 ] && [ "$BUNDLE_COMPLETE" = 0 ]; then
        rm -rf "$OUT"
    fi
}
trap cleanup EXIT HUP INT TERM

device_ssh() {
    if [ -n "$KNOWN_HOSTS" ]; then
        ssh -n -F /dev/null -o ConnectTimeout=8 -o BatchMode=yes \
            -o StrictHostKeyChecking=no -o UserKnownHostsFile="$KNOWN_HOSTS" "$@"
    else
        ssh -n -o ConnectTimeout=8 -o BatchMode=yes "$@"
    fi
}

device_scp() {
    if [ -n "$KNOWN_HOSTS" ]; then
        scp -F /dev/null -q -o ConnectTimeout=8 -o BatchMode=yes \
            -o StrictHostKeyChecking=no -o UserKnownHostsFile="$KNOWN_HOSTS" "$@"
    else
        scp -q -o ConnectTimeout=8 -o BatchMode=yes "$@"
    fi
}

echo "== 1. current production gates =="
for gate in \
    test_finalplay18_production.sh \
    test_finalplay19_production.sh \
    test_finalplay20_production.sh \
    test_finalplay21_production.sh \
    test_finalplay22_production.sh \
    test_finalplay23_production.sh \
    test_gptokeyb_launchers.sh; do
    sh "$REPO/harness/$gate" >/dev/null || {
        echo "$gate failed -- refusing to package FINALPLAY23" >&2
        exit 1
    }
done
echo "ok     FINALPLAY18--23 and input gates pass"

# FINALPLAY23_PRODUCTION.sha256 pins the independently distributed binaries,
# every tracked device record and the four objects exclusive to the immediate
# FINALPLAY21 rollback. Keep this table explicit: deriving carried files from a
# live manifest previously produced a bundle that could launch FINALPLAY23 but
# could not honour its advertised rollback on a clean installation.
cp "$PRODUCTION" "$TMP/files"

rows=$(awk 'NF == 2 && $1 !~ /^#/ {n++} END {print n+0}' "$TMP/files")
[ "$rows" = 28 ] || {
    echo "current distributable table has $rows rows, expected 28" >&2
    exit 1
}
[ "$(awk 'NF == 2 && $1 !~ /^#/ {print $2}' "$TMP/files" | sort | uniq -d | wc -l)" = 0 ] || {
    echo "current distributable table contains duplicate names" >&2
    exit 1
}
if awk 'NF == 2 && $1 !~ /^#/ {print $2}' "$TMP/files" | grep -Eiq '\.exe$|game/bin'; then
    echo "refusing a release table that could contain the legal game image" >&2
    exit 1
fi

echo "== 2. collect exact runtime and tracked bytes =="
[ ! -e "$OUT" ] || {
    echo "$OUT already exists; refusing to mix a release with stale files" >&2
    exit 1
}
mkdir -p "$OUT"
OUT_CREATED=1
while read -r want file extra; do
    case "$want" in ''|\#*) continue;; esac
    [ -z "${extra:-}" ] || {
        echo "malformed production row for $file" >&2
        exit 1
    }
    src=
    if [ -r "$REPO/device/$file" ]; then
        src="$REPO/device/$file"
    elif [ -r "$ARTIFACT_DIR/$file" ]; then
        src="$ARTIFACT_DIR/$file"
    elif [ "$FETCH_DEVICE" = 1 ]; then
        src="$TMP/$file"
        device_scp "$DEV:$GAMEDIR/$file" "$src" || {
            echo "cannot fetch missing exact artifact $file from $DEV:$GAMEDIR" >&2
            exit 1
        }
    else
        echo "missing exact artifact $file" >&2
        echo "put it in $ARTIFACT_DIR or use --from-device/--deploy" >&2
        exit 1
    fi
    got=$(sha256sum "$src" | cut -d' ' -f1)
    [ "$got" = "$want" ] || {
        echo "$file is $got, production requires $want" >&2
        exit 1
    }
    cp "$src" "$OUT/$file"
    printf '%s  %s\n' "$want" "$file" >> "$OUT/SHA256SUMS"
done < "$TMP/files"

cp "$REPO/THIRD_PARTY_NOTICES.md" "$OUT/THIRD_PARTY_NOTICES.md"
cp "$REPO/device/FINALPLAY.lock" "$OUT/FINALPLAY.lock"
for source in \
    game-patches/02-wpatch-consumer-and-state-isolation.patch \
    game-patches/04-wpatch-texture-transform-ownership-candidate.patch \
    game-patches/05-wpatch-latent-safety-corrections.patch \
    wine-patches/history/84-dmime-message-private-state-layout.patch \
    wine-patches/history/85-dmsynth-sink-lifetime-and-clock-state.patch; do
    cp "$REPO/$source" "$OUT/$(basename "$source")"
done
(cd "$OUT" && sha256sum THIRD_PARTY_NOTICES.md FINALPLAY.lock \
    02-wpatch-consumer-and-state-isolation.patch \
    04-wpatch-texture-transform-ownership-candidate.patch \
    05-wpatch-latent-safety-corrections.patch \
    84-dmime-message-private-state-layout.patch \
    85-dmsynth-sink-lifetime-and-clock-state.patch > SOURCE_RECORDS.sha256)
(cd "$OUT" && sha256sum -c SHA256SUMS >/dev/null)
(cd "$OUT" && sha256sum -c SOURCE_RECORDS.sha256 >/dev/null)
BUNDLE_COMPLETE=1
echo "ok     $rows exact distributable files; legal EXE and system libraries excluded"

if [ "$MODE" = --deploy ]; then
    echo "== 3. deploy exact FINALPLAY23 bundle =="
    deployed=0
    while read -r want file extra; do
        case "$want" in ''|\#*) continue;; esac
        if [ "$file" = MGS2-Substance.sh ]; then
            target="$PORTDIR/MGS2-Substance.sh"
        else
            target="$GAMEDIR/$file"
        fi
        staged="$target.finalplay22-new"
        device_scp "$OUT/$file" "$DEV:$staged"
        got=$(device_ssh "$DEV" "sha256sum '$staged'" 2>/dev/null | cut -d' ' -f1)
        [ "$got" = "$want" ] || {
            device_ssh "$DEV" "rm -f '$staged'" >/dev/null 2>&1 || true
            echo "staged $target is ${got:-missing}, expected $want" >&2
            exit 1
        }
        device_ssh "$DEV" "mv -f '$staged' '$target'"
        got=$(device_ssh "$DEV" "sha256sum '$target'" 2>/dev/null | cut -d' ' -f1)
        [ "$got" = "$want" ] || {
            echo "deployed $target is ${got:-missing}, expected $want" >&2
            exit 1
        }
        echo "       $file"
        deployed=$((deployed + 1))
    done < "$TMP/files"
    [ "$deployed" = "$rows" ] || {
        echo "deployed $deployed files, expected $rows" >&2
        exit 1
    }
    device_ssh "$DEV" \
        "chmod +x '$PORTDIR/MGS2-Substance.sh' '$GAMEDIR'/box86-fp26-wayland-text-input-production '$GAMEDIR'/gptokeyb-mgs2-immediate '$GAMEDIR'/*.sh"
    echo "ok     deployed and re-hashed $rows exact files"
fi

echo "release $NAME is in $OUT"

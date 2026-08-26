#!/bin/sh
# Build the i386 client, copy only temporary test helpers, and run the device gate.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
_device_set=${MGS2_DEVICE+x}; _device=${MGS2_DEVICE-}
_game_dir_set=${MGS2_GAME_DIR+x}; _game_dir=${MGS2_GAME_DIR-}
if [ -r "$REPO/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$REPO/.env"
    set +a
fi
[ "$_device_set" = x ] && MGS2_DEVICE=$_device
[ "$_game_dir_set" = x ] && MGS2_GAME_DIR=$_game_dir
DEVICE=${MGS2_DEVICE:-root@rg353vs}
GAME_DIR=${MGS2_GAME_DIR:-/storage/roms/ports/MGS2-Substance}
BOX86=${1:-box86-fp24-wayland-atomic-candidate}
KNOWN_HOSTS="$REPO/logs/rg353vs/known_hosts"
CLIENT=$(mktemp /tmp/mgs2-wayland-abi-client-i386.XXXXXX)

cleanup() { rm -f "$CLIENT"; }
trap cleanup EXIT HUP INT TERM
"$HERE/build_wayland_abi_client.sh" "$CLIENT"

SCP="scp -F /dev/null -o ConnectTimeout=8 -o StrictHostKeyChecking=no -o UserKnownHostsFile=$KNOWN_HOSTS"
SSH="ssh -F /dev/null -o ConnectTimeout=8 -o StrictHostKeyChecking=no -o UserKnownHostsFile=$KNOWN_HOSTS"
# shellcheck disable=SC2086
$SCP "$CLIENT" "$DEVICE:/tmp/mgs2-wayland-abi-client-i386"
# shellcheck disable=SC2086
$SCP "$REPO/harness/send_key.py" "$DEVICE:/tmp/mgs2-send-key.py"
# shellcheck disable=SC2086
$SCP "$HERE/device_wayland_abi_gate.sh" "$DEVICE:/tmp/mgs2-device-wayland-abi-gate.sh"
# shellcheck disable=SC2086
$SSH "$DEVICE" chmod +x /tmp/mgs2-wayland-abi-client-i386 \
    /tmp/mgs2-device-wayland-abi-gate.sh
# shellcheck disable=SC2086
$SSH "$DEVICE" /tmp/mgs2-device-wayland-abi-gate.sh "$GAME_DIR" "$BOX86"

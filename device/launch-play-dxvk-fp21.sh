#!/bin/sh
# FINALPLAY21 fixed production route: FINALPLAY20 plus the measured wpatch
# fixed-function fallback that restores the missing animated sea.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
export MGS2_PRODUCTION_ROUTE=finalplay21
exec "$HERE/launch-play-dxvk-fp17.sh"

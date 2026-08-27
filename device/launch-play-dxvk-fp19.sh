#!/bin/sh
# FINALPLAY19 fixed production route: p25 exact Wayland text-input listener ABI,
# p26 reproducible artifact boundary, immediate Start/Select edges and no
# duplicate Wine controller route.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
export MGS2_PRODUCTION_ROUTE=finalplay19
exec "$HERE/launch-play-dxvk-fp17.sh"

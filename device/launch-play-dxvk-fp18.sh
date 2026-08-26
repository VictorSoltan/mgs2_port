#!/bin/sh
# FINALPLAY18 fixed production route: FINALPLAY17 plus the Box86 patches 23+24
# Wayland-listener ABI fix. The shared engine accepts this closed route name,
# not an arbitrary binary or manifest override.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
export MGS2_PRODUCTION_ROUTE=finalplay18
exec "$HERE/launch-play-dxvk-fp17.sh"

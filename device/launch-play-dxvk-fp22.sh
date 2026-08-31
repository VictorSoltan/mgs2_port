#!/bin/sh
# FINALPLAY22 fixed production route: FINALPLAY21 plus wpatch state ownership
# and the dmime/dmsynth lifetime repairs promoted by owner directive.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
export MGS2_PRODUCTION_ROUTE=finalplay22
exec "$HERE/launch-play-dxvk-fp17.sh"

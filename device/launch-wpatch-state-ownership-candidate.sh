#!/bin/sh
# FINALPLAY21 plus consumer isolation, lighting cleanup and explicit ownership
# of the fixed-function stage-0 texture transform. This remains a candidate
# until the delayed RG353VS visual gate passes.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
export MGS2_PRODUCTION_ROUTE=wpatch-state-ownership-candidate
exec "$HERE/launch-play-dxvk-fp17.sh"

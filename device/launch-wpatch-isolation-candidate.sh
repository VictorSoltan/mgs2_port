#!/bin/sh
# FINALPLAY21 plus consumer-scoped wpatch selection and fixed-function lighting
# cleanup. This remains a candidate until the delayed RG353VS visual gate passes.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
export MGS2_PRODUCTION_ROUTE=wpatch-isolation-candidate
exec "$HERE/launch-play-dxvk-fp17.sh"

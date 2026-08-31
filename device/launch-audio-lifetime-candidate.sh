#!/bin/sh
# FINALPLAY21 plus the bounded dmime PMSG-layout and dmsynth sink-lifetime
# repairs. This remains a candidate until the RG353VS audio gates pass.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
export MGS2_PRODUCTION_ROUTE=audio-lifetime-candidate
exec "$HERE/launch-play-dxvk-fp17.sh"

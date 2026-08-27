#!/bin/sh
# Closed FINALPLAY19 audio candidate: p35 recovery after one 250 ms stall tick.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
export MGS2_PRODUCTION_ROUTE=dmsynth-resume-stall1-candidate
exec "$HERE/launch-play-dxvk-fp17.sh"

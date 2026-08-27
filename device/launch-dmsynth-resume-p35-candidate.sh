#!/bin/sh
# Closed FINALPLAY19 audio candidate: only dmsynth p34 -> p35 changes.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
export MGS2_PRODUCTION_ROUTE=dmsynth-resume-p35-candidate
exec "$HERE/launch-play-dxvk-fp17.sh"

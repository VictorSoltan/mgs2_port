#!/bin/sh
# Closed FINALPLAY19 audio candidate: p35 transport recovery plus p37 timeline rebase.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
export MGS2_PRODUCTION_ROUTE=dmsynth-resume-p37-candidate
exec "$HERE/launch-play-dxvk-fp17.sh"

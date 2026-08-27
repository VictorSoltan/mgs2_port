#!/bin/sh
# FINALPLAY20 fixed production route: FINALPLAY19 plus the measured p37
# DirectMusic transport/timeline resume repair.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
export MGS2_PRODUCTION_ROUTE=finalplay20
exec "$HERE/launch-play-dxvk-fp17.sh"

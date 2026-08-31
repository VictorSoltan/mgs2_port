#!/bin/sh
# FINALPLAY21 with only Box86 patch 27's strengthened DXT-surface self-test and
# bounded externally readable production witness. No hot-thread counter/log.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
export MGS2_PRODUCTION_ROUTE=dxt-witness-candidate
exec "$HERE/launch-play-dxvk-fp17.sh"

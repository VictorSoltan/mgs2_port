#!/bin/bash
# Closed RG353VS candidate: Box86 patch 25 plus the immediate one-process
# Start/Select helper and no physical controller exposed to Wine. Normal play
# stays on FINALPLAY18 until both candidates pass their device gates.
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export MGS2_PRODUCTION_ROUTE=wayland-p25-candidate
exec "$HERE/launch-play-dxvk-fp17.sh"

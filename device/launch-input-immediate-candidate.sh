#!/bin/bash
# Closed RG353VS candidate: Box86 patches 25+26 plus the immediate one-process
# Start/Select helper and no physical controller exposed to Wine. This preserves
# the pre-promotion test route; normal play now selects FINALPLAY19 production.
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export MGS2_PRODUCTION_ROUTE=wayland-p26-candidate
exec "$HERE/launch-play-dxvk-fp17.sh"

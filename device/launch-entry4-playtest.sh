#!/bin/sh
# Explicit FINALPLAY6 diagnostic launcher for the measured native
# mgs2_batch_flush cut. Production now uses the same island31 + p56 pair. This
# wrapper is retained so the exact entry-4 configuration can still be selected
# independently of an inherited environment; it uses no A/B switching.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)

# This launcher substitutes binaries, so it has to say so: launch-play.sh refuses
# to accept MGS2_BOX86_BIN and friends from a plain environment, because that used
# to switch off identity verification for every other mounted file at the same
# time. The run is still verified -- a mismatch is reported instead of ignored.
export MGS2_RESEARCH_RUN=1

unset MGS2_ISLAND_AB MGS2_ISLAND_AB_MEASURE
export MGS2_BOX86_BIN=box86-island31
export MGS2_WINED3D_DLL=wined3d_p56_batch_state.dll
export MGS2_D3D8_DLL=d3d8_finalplay3_nocullcache.dll
export MGS2_BOX86_ISLAND_FULL=1
export MGS2_BOX86_ISLAND_ONLY=0,1,2,3,4,5,6,9,10,14,18,19,22,28,29,32,33

exec "$HERE/launch-play.sh"

#!/bin/sh
# Correctness-only lower DRAW boundary after coarse entry 37 was closed.
# Guest x86 retains context acquisition, target loading, draw-state apply,
# barriers and release; only the final primitive-arrays tail is entry 38 / ARM.
# No A/B and no FPS claim until the bounded frame witness shows real content.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)

# This launcher substitutes binaries, so it has to say so: launch-play.sh refuses
# to accept MGS2_BOX86_BIN and friends from a plain environment, because that used
# to switch off identity verification for every other mounted file at the same
# time. The run is still verified -- a mismatch is reported instead of ignored.
export MGS2_RESEARCH_RUN=1

MGS2_BOX86_BIN="${MGS2_BOX86_BIN:-box86-island46-p68-tail}" \
MGS2_WINED3D_DLL="${MGS2_WINED3D_DLL:-wined3d_p68_draw_tail.dll}" \
MGS2_WAYLAND_SO="${MGS2_WAYLAND_SO:-winewayland_p67_frame_witness.so}" \
MGS2_BOX86_ISLAND_FULL=1 \
MGS2_BOX86_ISLAND_ONLY="0,1,2,3,4,5,6,9,10,14,18,19,22,23,28,29,32,33,38" \
MGS2_DRAW_CORRECTNESS=1 \
MGS2_FRAME_WITNESS=1 \
MGS2_REINFORCEMENT_CENSUS=1 \
MGS2_GL_STATS="${MGS2_GL_STATS:-300}" \
MGS2_PLAY_WINEDEBUG="${MGS2_PLAY_WINEDEBUG:--all,err+waylanddrv}" \
exec "$HERE/launch-play.sh"

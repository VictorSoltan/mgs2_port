#!/bin/sh
# Correctness-only p70 phase-A boundary. Guest x86 owns context activation,
# dirty-state apply, bindings/FBO, shader backend, final draw and release. ARM
# runs only the contiguous resource/stream preload phase selected after the
# transitive ABI audit and exact island41 profile attribution. Not for FPS.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)

# This launcher substitutes binaries, so it has to say so: launch-play.sh refuses
# to accept MGS2_BOX86_BIN and friends from a plain environment, because that used
# to switch off identity verification for every other mounted file at the same
# time. The run is still verified -- a mismatch is reported instead of ignored.
export MGS2_RESEARCH_RUN=1

MGS2_BOX86_BIN="${MGS2_BOX86_BIN:-box86-island49-p70-phase-a}" \
MGS2_WINED3D_DLL="${MGS2_WINED3D_DLL:-wined3d_p70_phase_a.dll}" \
MGS2_WAYLAND_SO="${MGS2_WAYLAND_SO:-winewayland_p67_frame_witness.so}" \
MGS2_BOX86_ISLAND_FULL=1 \
MGS2_BOX86_ISLAND_ONLY="0,1,2,3,4,5,6,9,10,14,18,19,22,23,28,29,32,33,40" \
MGS2_DRAW_CORRECTNESS=1 \
MGS2_PHASE_A_CORRECTNESS=1 \
MGS2_FRAME_WITNESS=1 \
MGS2_REINFORCEMENT_CENSUS=1 \
MGS2_DISPLAY_LOCK_HISTORY=1 \
MGS2_GL_STATS="${MGS2_GL_STATS:-300}" \
MGS2_PLAY_WINEDEBUG="${MGS2_PLAY_WINEDEBUG:--all,err+waylanddrv}" \
exec "$HERE/launch-play.sh"

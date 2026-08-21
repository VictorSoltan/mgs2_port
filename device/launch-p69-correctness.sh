#!/bin/sh
# Correctness-only p69 boundary. Guest x86 acquires and makes the GL context
# current, loads RT/depth and retains final draw/barriers/release. ARM runs only
# context_apply_draw_state(). This launcher is not valid for FPS measurement.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)

MGS2_BOX86_BIN="${MGS2_BOX86_BIN:-box86-island48-p69-state}" \
MGS2_WINED3D_DLL="${MGS2_WINED3D_DLL:-wined3d_p69_apply_state.dll}" \
MGS2_WAYLAND_SO="${MGS2_WAYLAND_SO:-winewayland_p67_frame_witness.so}" \
MGS2_BOX86_ISLAND_FULL=1 \
MGS2_BOX86_ISLAND_ONLY="0,1,2,3,4,5,6,9,10,14,18,19,22,23,28,29,32,33,39" \
MGS2_DRAW_CORRECTNESS=1 \
MGS2_P69_CORRECTNESS=1 \
MGS2_FRAME_WITNESS=1 \
MGS2_REINFORCEMENT_CENSUS=1 \
MGS2_DISPLAY_LOCK_HISTORY=1 \
MGS2_GL_STATS="${MGS2_GL_STATS:-300}" \
MGS2_PLAY_WINEDEBUG="${MGS2_PLAY_WINEDEBUG:--all,err+waylanddrv}" \
exec "$HERE/launch-play.sh"

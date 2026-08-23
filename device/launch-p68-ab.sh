#!/bin/sh
# Symmetric same-process A/B for the picture-correct p68 DRAW tail.
#
# Guest x86 owns the selector. Both arms execute the same branch, route read,
# settle read and call counter. The routed arm enters island entry 38; the guest
# arm calls wined3d_context_gl_draw_primitive_arrays() directly and therefore
# pays no RunFunctionFmt() trampoline. The passive display-lock history is left
# armed in memory so a reliability reproduction is not lost while FPS is tested.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)

# This launcher substitutes binaries, so it has to say so: launch-play.sh refuses
# to accept MGS2_BOX86_BIN and friends from a plain environment, because that used
# to switch off identity verification for every other mounted file at the same
# time. The run is still verified -- a mismatch is reported instead of ignored.
export MGS2_RESEARCH_RUN=1

MGS2_ISLAND_AB_MEASURE=38 \
MGS2_BOX86_BIN="${MGS2_BOX86_BIN:-box86-island47-p68-ab}" \
MGS2_WINED3D_DLL="${MGS2_WINED3D_DLL:-wined3d_p68b_draw_tail_ab.dll}" \
MGS2_WAYLAND_SO="${MGS2_WAYLAND_SO:-winewayland_p67_frame_witness.so}" \
MGS2_BOX86_ISLAND_FULL=1 \
MGS2_BOX86_ISLAND_ONLY="0,1,2,3,4,5,6,9,10,14,18,19,22,23,28,29,32,33,38" \
MGS2_DRAW_CORRECTNESS=1 \
MGS2_FRAME_WITNESS=1 \
MGS2_REINFORCEMENT_CENSUS=1 \
MGS2_DISPLAY_LOCK_HISTORY=1 \
MGS2_GL_STATS="${MGS2_GL_STATS:-300}" \
MGS2_PLAY_WINEDEBUG="${MGS2_PLAY_WINEDEBUG:--all,err+waylanddrv}" \
exec "$HERE/launch-play.sh"

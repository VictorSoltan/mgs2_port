#!/bin/sh
# STEP 0 compiler-path control: the already-proven p70 phase A, rebuilt with the
# Clang toolchain intended for p71.
#
# CORRECTNESS ONLY. NO TIMING MAY BE READ FROM THIS RUN: the Box86 binary is the
# diagnostics build, which prints dispatch lines, and that alone disqualifies it
# for frame timing. What it buys is the report of any unresolved dispatch -- the
# reason this control exists.
#
# The island is built by clang-18 --target=arm-linux-gnueabihf -mms-bitfields, so
# every WineD3D aggregate inside it carries the guest's MSVC field offsets. The
# guest DLL is the unchanged p70b build; with no MGS2_ISLAND_AB the guest selector
# stays disabled and entry 40 is always routed, which is exactly p70's behaviour.
#
# Why phase A and not p71 straight away: phase A is already correctness-proven and
# measured positive on the GCC island (-0.626 ms/frame overall, -0.944 on the
# plateau). If the same phase breaks under the new compiler, the fault is the
# compiler path, not the boundary -- and that is a much cheaper thing to debug
# than a new compiler path and a much larger native root at the same time.
#
# Class-B is 1,549 native IDs here, not 1,616: Clang inlined 67 functions that GCC
# kept as separate symbols. No target reachable from phase A or from
# context_apply_draw_state() is among them (audited, unresolved = 0), but the
# registry had to be regenerated, so a stale table would show up as unresolved
# dispatch in this very run.
#
# The display-lock recorder is armed again: the p70b timing run gave it up, and a
# correctness run is where a freeze reproduction costs nothing.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)

MGS2_BOX86_BIN="${MGS2_BOX86_BIN:-box86-island51-p70d-clangms}" \
MGS2_WINED3D_DLL="${MGS2_WINED3D_DLL:-wined3d_p70b_phase_a_ab.dll}" \
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

#!/bin/sh
# p71 correctness: the whole context_apply_draw_state() native again, this time on
# an island built with the guest's MSVC field offsets (clang-18 -mms-bitfields).
#
# CORRECTNESS ONLY -- NO TIMING. The Box86 binary is the diagnostics build and
# prints dispatch lines; that alone disqualifies it for frame timing. Its value
# here is that any unresolved dispatch is reported instead of guessed.
#
# The boundary is p69's, unchanged: guest x86 keeps context_acquire(), current-
# context ownership, render-target/depth preparation, the final draw, barriers
# and context_release(). Phase A's entry stays compiled inside the native root
# and is reached natively, without a second crossing.
#
# Why this is not simply "p69 again":
#   ABI      the nine hard layout failures p69 died of are gone -- the island's
#            texture_stage_op/ffp_frag_settings/ffp_frag_desc are 16/132/148 as
#            in the guest, proved by a witness compiled into the island itself
#   ROUTING  shader_generate_code() called the shader FRONTEND through a vtable
#            at four sites that nothing routed. Native ARM would have branched
#            to a guest x86 pointer whenever the FFP shader cache missed inside
#            the root. They now go through MGS2_P50_SHADER_FRONTEND
#   CLASS B  regenerated: clang inlines more, so the table is 1,547 ids, not
#            1,616. Every id reachable from this root resolves in the clang
#            object set -- 417 of them, with zero duplicates and zero misses
#
# MGS2_P71_WITNESS arms the bounded shader witness: one sample every 4,096 native
# applications reads GL_CURRENT_PROGRAM, GL_PROGRAM_PIPELINE_BINDING and
# GL_DRAW_FRAMEBUFFER_BINDING plus glGetError, and counts zero-program and
# GL-error samples. That is the exact class of defect p69 produced, so it is
# watched directly rather than inferred from the picture.
#
# Read with harness/p71_correctness_read.py; the frame witness and final-draw
# census come from the p67/p70 readers as before.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)

MGS2_BOX86_BIN="${MGS2_BOX86_BIN:-box86-island52-p71-clangms}" \
MGS2_WINED3D_DLL="${MGS2_WINED3D_DLL:-wined3d_p71_apply_state_clangms.dll}" \
MGS2_WAYLAND_SO="${MGS2_WAYLAND_SO:-winewayland_p67_frame_witness.so}" \
MGS2_BOX86_ISLAND_FULL=1 \
MGS2_BOX86_ISLAND_ONLY="0,1,2,3,4,5,6,9,10,14,18,19,22,23,28,29,32,33,39" \
MGS2_DRAW_CORRECTNESS=1 \
MGS2_P69_CORRECTNESS=1 \
MGS2_P71_WITNESS=1 \
MGS2_FRAME_WITNESS=1 \
MGS2_REINFORCEMENT_CENSUS=1 \
MGS2_DISPLAY_LOCK_HISTORY=1 \
MGS2_GL_STATS="${MGS2_GL_STATS:-300}" \
MGS2_PLAY_WINEDEBUG="${MGS2_PLAY_WINEDEBUG:--all,err+waylanddrv}" \
exec "$HERE/launch-play.sh"

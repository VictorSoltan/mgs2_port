#!/bin/sh
# Symmetric same-process A/B for the fused A+B+C native root (entry 41).
#
# TIMING RUN. The p72 correctness run already settled the picture: 79,777 calls
# against 79,777 final arrays, zero guest fallbacks, 64/64 unique frames at
# min_lit 256/256 and a real screenshot. So this build carries neither the GL
# census nor the diagnostics box86 -- both would tax the very thing being timed.
#
# Guest x86 owns the selector inside context_apply_draw_state(). Both arms are
# one guest call from the same site: the routed arm enters marked entry 41, the
# control arm calls the same transaction body directly, so neither pays a
# RunFunctionFmt() re-entry. Phase D, the final draw, barriers and release stay
# guest in both arms, and FINALPLAY7's production entries stay armed in both, so
# the number is the incremental effect over production.
#
# MGS2_GL_STATS stays at 300: `present stats` is one winewayland.drv ERR line per
# 300 displayed frames, paid identically by both arms, and it is the only
# non-circular check of the A/B tick rate.
#
# Reduce with harness/island_ab_read.py. Sign convention: negative means the ARM
# route is faster.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)

# This launcher substitutes binaries, so it has to say so: launch-play.sh refuses
# to accept MGS2_BOX86_BIN and friends from a plain environment, because that used
# to switch off identity verification for every other mounted file at the same
# time. The run is still verified -- a mismatch is reported instead of ignored.
export MGS2_RESEARCH_RUN=1

MGS2_ISLAND_AB_MEASURE=41 \
MGS2_BOX86_BIN="${MGS2_BOX86_BIN:-box86-island54-p72b-ab}" \
MGS2_WINED3D_DLL="${MGS2_WINED3D_DLL:-wined3d_p72b_fused_abc_ab.dll}" \
MGS2_BOX86_ISLAND_FULL=1 \
MGS2_BOX86_ISLAND_ONLY="0,1,2,3,4,5,6,9,10,14,18,19,22,23,28,29,32,33,41" \
MGS2_GL_STATS="${MGS2_GL_STATS:-300}" \
MGS2_PLAY_WINEDEBUG="${MGS2_PLAY_WINEDEBUG:--all,err+waylanddrv}" \
exec "$HERE/launch-play.sh"

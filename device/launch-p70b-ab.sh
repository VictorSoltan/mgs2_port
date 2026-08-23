#!/bin/sh
# Symmetric same-process A/B for the ABI-admitted p70 draw-state phase A.
#
# TIMING RUN. Correctness was already settled by the always-routed p70 gameplay
# capture -- 2,172,004 phase-A calls against 2,172,004 final arrays, zero guest
# fallbacks and faults, 64/64 changing lit frames and an independent screenshot
# of the real scene -- so this run pays for none of that instrumentation. It
# arms only the selector and the frame tick, over the production presenter.
#
# Guest x86 owns the selector inside context_apply_draw_state(). Both arms
# execute the same enabled/route/settle reads and the same per-arm counter; the
# routed arm calls the marked island entry 40 and the control arm calls the same
# transaction body directly, so neither arm pays a RunFunctionFmt() re-entry.
# Phases B/C/D, the final draw, barriers and context release stay guest in both
# arms, and the FINALPLAY7 production entries stay armed in both arms: the number
# this produces is the incremental effect on top of production, not the cost of
# the ARM body in isolation.
#
# Deliberately NOT set: MGS2_DRAW_CORRECTNESS, MGS2_PHASE_A_CORRECTNESS,
# MGS2_FRAME_WITNESS, MGS2_REINFORCEMENT_CENSUS, MGS2_DISPLAY_LOCK_HISTORY, and
# the p67 witness presenter. Per-arm call counts come from the guest selector's
# own counters, which Box86 reads when each ABBA cycle closes.
#
# MGS2_GL_STATS stays on at 300 frames and is not diagnostics: `present stats`
# is one ERR line per 300 displayed frames from winewayland.drv, produced by
# different code on the other side of the emulator, and it is the only
# independent check of the A/B tick rate -- comparing the ticks against the
# per-arm frame counts is circular, because the blocks are defined in ticks.
# That is why WINEDEBUG keeps exactly the waylanddrv err channel and nothing
# else. Reduce the run with harness/island_ab_read.py.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)

# This launcher substitutes binaries, so it has to say so: launch-play.sh refuses
# to accept MGS2_BOX86_BIN and friends from a plain environment, because that used
# to switch off identity verification for every other mounted file at the same
# time. The run is still verified -- a mismatch is reported instead of ignored.
export MGS2_RESEARCH_RUN=1

MGS2_ISLAND_AB_MEASURE=40 \
MGS2_BOX86_BIN="${MGS2_BOX86_BIN:-box86-island50-p70b-ab}" \
MGS2_WINED3D_DLL="${MGS2_WINED3D_DLL:-wined3d_p70b_phase_a_ab.dll}" \
MGS2_BOX86_ISLAND_FULL=1 \
MGS2_BOX86_ISLAND_ONLY="0,1,2,3,4,5,6,9,10,14,18,19,22,23,28,29,32,33,40" \
MGS2_GL_STATS="${MGS2_GL_STATS:-300}" \
MGS2_PLAY_WINEDEBUG="${MGS2_PLAY_WINEDEBUG:--all,err+waylanddrv}" \
exec "$HERE/launch-play.sh"

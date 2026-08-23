#!/bin/sh
# p72c: the fused A+B+C native root as a production-style candidate.
#
# Nothing measures itself here. No A/B selector, no GL census, no correctness
# records, no diagnostics build, no witness presenter -- the production presenter
# and the production entry list plus entry 41. This is what "playing on it" means.
#
# Boundary: guest x86 keeps context_acquire(), current-context ownership,
# render-target/depth preparation, the framebuffer-attachment check, shader phase
# D, the final draw, barriers and context_release(). ARM runs the contiguous
# resource/stream preload, the whole dirty-state loop with its bitmap clear, and
# the resource/UAV bindings with FBO validation.
#
# Evidence behind it, all recorded in
# docs/briefs/MGS2_PHASE_A_NATIVE_MEASURED_2026-08-21.md:
#   correctness   79,777 native applications against 79,777 final GL arrays,
#                 zero guest fallbacks, 64/64 unique frames at min_lit 256/256,
#                 an independent screenshot of the real scene, zero faults
#   direction     the routed arm was cheaper per application in 23 of 28 A/B
#                 cycles (exact two-sided sign test p=0.0009)
#   magnitude     NOT established by the pre-registered balanced-cycle median,
#                 which had 7 usable cycles and said nothing. A post-hoc
#                 work-normalised estimate puts it at -4.8 ms/frame with a 95%
#                 bootstrap CI of [-7.9, -2.6] under the assumption that frame
#                 time scales with application count
#
# MGS2_GL_STATS stays at 300 so ordinary play still logs `present stats`: one ERR
# line per 300 displayed frames is how this candidate is watched over time,
# instead of another measurement session.
#
# MGS2_P72_CORRECTNESS is armed deliberately, even though this is a candidate and
# not a measurement. Without it nothing in a non-diagnostic run proves the route
# is LIVE: Box86 logs that entry 41 was armed, but the "entry 41 matched" line
# only exists in the diagnostics build, and a marker that failed to match would
# leave the guest body running and the picture just as correct. The record is two
# memory increments per application, no output, so ordinary play can prove
# routing at any moment:
#     python3 p72_correctness_read.py <pid>
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)

# This launcher substitutes binaries, so it has to say so: launch-play.sh refuses
# to accept MGS2_BOX86_BIN and friends from a plain environment, because that used
# to switch off identity verification for every other mounted file at the same
# time. The run is still verified -- a mismatch is reported instead of ignored.
export MGS2_RESEARCH_RUN=1

MGS2_BOX86_BIN="${MGS2_BOX86_BIN:-box86-island55-p72c-candidate}" \
MGS2_WINED3D_DLL="${MGS2_WINED3D_DLL:-wined3d_p72c_fused_abc.dll}" \
MGS2_BOX86_ISLAND_FULL=1 \
MGS2_BOX86_ISLAND_ONLY="0,1,2,3,4,5,6,9,10,14,18,19,22,23,28,29,32,33,41" \
MGS2_P72_CORRECTNESS=1 \
MGS2_GL_STATS="${MGS2_GL_STATS:-300}" \
MGS2_PLAY_WINEDEBUG="${MGS2_PLAY_WINEDEBUG:--all,err+waylanddrv}" \
exec "$HERE/launch-play.sh"

#!/bin/sh
# P81: is the active-program selector that P75A left behind actually redundant?
#
# THE ARITHMETIC THIS IS BUILT ON, because it is the whole reason to look here
#
# P75A removed ~1380 of ~1572 glActiveShaderProgram calls per combat frame and
# that measured -14.80 ms/frame. So this call, on this driver and through this
# emulator, costs about 14.80 / 1380 = 10.7 us. ~192 survive per frame, because an
# upload genuinely follows them, which puts a hard ceiling of
#
#     192 x 10.7 us ~= 2.05 ms/frame
#
# on this candidate and makes any real redundancy inside those 192 worth taking.
# Unlike every other GL candidate here, the price is not estimated -- it is the
# same call P75A already priced directly.
#
# WHY IT IS SAFER THAN A UNIFORM CACHE
#
# glActiveShaderProgram(pipeline, program) only chooses which program subsequent
# glUniform* calls write into, and it is state OF THE PIPELINE OBJECT. Selecting
# the same program again is a semantic no-op. There is no cached value and no
# payload -- the two earlier shadow candidates were closed because they cached
# VALUES under the wrong key, and this caches a SELECTOR under the object GL
# itself scopes it to. pipeline_id is generated per entry by
# glGenProgramPipelines() and deleted with the entry, so the shadow field in
# glsl_shader_prog_link is a 1:1 key. A file-scope "last program" would be wrong.
#
# RUN 1 IS A CENSUS, AND IT IS WHAT THIS SCRIPT DOES BY DEFAULT
#
#   MGS2_GL_APS=0         count the redundancy, skip nothing. Behaviour is
#                         byte-identical to FINALPLAY14, so this run cannot cost
#                         a thing and cannot be blamed for anything either.
#   MGS2_GL_APS_VERIFY=1  every 4096th selection (and the first) reads GL's real
#                         GL_ACTIVE_PROGRAM back and compares it against the
#                         shadow. mismatch must be 0. A mismatch disables the
#                         skip for the rest of the run and marks it void, so the
#                         invariant is measured rather than argued from a source
#                         audit.
#
# Reduce with, while the game is running:
#
#   python3 gl_census_delta.py $(pgrep -f mgs2_sse_rg353vs) --seconds 30
#
# Read TWO things off it. The redundancy percentage, obviously. And WHICH RECORD
# the selections came from, because there are two copies of glsl_shader.c in this
# process -- the PE wined3d and box86's native island -- and only the PE one can
# follow the ABBA arm: mgs2_texmatrix_ab_present() writes the arm and the present
# path is not a routed island entry. If the island's record carries a large share
# of the selections, an unpinned ABBA measures half the work and can only
# UNDER-report, and the honest measurement is two pinned runs instead.
#
# RUN 2, once run 1 says the redundancy is real and mismatch is 0
#
#   MGS2_GL_APS=1 ./launch-p81-census.sh     one steady armed run, both copies
#   MGS2_GL_APS= ./launch-p81-census.sh      the in-process ABBA owns the arm,
#                                            12-frame blocks, A = off
#
# The ABBA is the better instrument when the PE copy does the work: same process,
# same scene, ABBA cancels linear drift. Note it cannot be switched off by
# environment in this build -- MGS2_PRESENT_AB below 2 falls back to 12 -- so
# MGS2_GL_APS is the only way to get one steady arm.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)

# This launcher substitutes binaries, so it has to say so: launch-play.sh refuses
# to accept MGS2_BOX86_BIN and friends from a plain environment, because that used
# to switch off identity verification for every other mounted file at the same
# time. The run is still verified -- a mismatch is reported instead of ignored.
export MGS2_RESEARCH_RUN=1

# The pair is fp14 plus P81 and nothing else. Keep them together: box86's class-B
# registry maps this exact DLL's RVAs.
MGS2_BOX86_BIN="${MGS2_BOX86_BIN:-box86-island56-p81-aps}" \
MGS2_WINED3D_DLL="${MGS2_WINED3D_DLL:-wined3d_p81_aps.dll}" \
MGS2_GL_APS="${MGS2_GL_APS-0}" \
MGS2_GL_APS_VERIFY="${MGS2_GL_APS_VERIFY:-1}" \
MGS2_BOX86_ISLAND_FULL=1 \
MGS2_BOX86_ISLAND_ONLY="0,1,2,3,4,5,6,9,10,14,18,19,22,23,28,29,32,33,41" \
MGS2_GL_STATS="${MGS2_GL_STATS:-300}" \
MGS2_PLAY_WINEDEBUG="${MGS2_PLAY_WINEDEBUG:--all}" \
exec "$HERE/launch-play.sh"

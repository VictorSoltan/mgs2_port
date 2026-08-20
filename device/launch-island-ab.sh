#!/bin/sh
# The A/B measurement run, kept OUT of the play launcher.
#
# device/launch-play.sh now clears MGS2_ISLAND_AB unconditionally, because the
# harness runs half of every cycle through the guest path on purpose: a value
# leaking into normal play would hand back about half of the measured 8.87
# ms/frame and look like the island regressing, with nothing failing to point
# at it. So the measurement lives here instead of behind a variable someone
# might leave set.
#
# What this measures: one island entry, switched between the native ARM route
# and the guest body every 64 displayed frames, ABBA, inside a single live
# process -- same Wine state, same shaders, same allocator, same temperature,
# same continuing fight. Eight separate playthroughs previously resolved
# nothing, because the scene moved between them by more than the effect.
#
#   usage: launch-island-ab.sh [entry-id]      (default 10, wined3d_buffer_load)
#
# Reading the result: take the "MGS2 A/B cycle" lines, keep only cycles whose
# two call counts agree within about 2%, and take the median of
# routed-unrouted. The call count is the covariate that makes the number
# readable -- filtering on it collapsed the spread from sd 8.67 to 2.39 without
# moving the median, so it removes noise rather than selecting a subset.
#
# Do not trust the per-arm frame count as a check that the tick is one per
# displayed frame: the blocks are DEFINED in ticks, so that comparison is
# circular and holds whatever the tick counts. Cross-check the printed tick
# total against the launcher's own MGS2_GL_STATS frame count instead; they
# agreed to 51.0 ms vs 51.1 ms over 51 cycles.
set -eu

ENTRY="${1:-10}"
HERE=$(cd "$(dirname "$0")" && pwd)
PRODUCTION_ONLY="0,1,2,3,4,5,6,9,10,14,18,19,22,23,28,29,32,33"

# A candidate outside the production set must still be armed before its A/B
# wrapper can switch it. Keep all production entries identical in both arms and
# append only the requested candidate; duplicating an existing id is avoided so
# the launch line remains an exact, readable record of the run.
case ",$PRODUCTION_ONLY," in
    *",$ENTRY,"*) MEASURE_ONLY="$PRODUCTION_ONLY" ;;
    *)            MEASURE_ONLY="$PRODUCTION_ONLY,$ENTRY" ;;
esac

# MGS2_ISLAND_AB_MEASURE, not MGS2_ISLAND_AB: the play launcher clears the
# latter and translates the former. The name that can leak from a shell is
# therefore not the name that arms the harness.
# The binary is pinned to whatever launch-play.sh selects by default, not to the
# island31 pair this file was written against. A candidate must be measured on
# the base that is actually played: the A/B is paired inside one process, so a
# different base does not invalidate the pairing, but it does answer a question
# about a stack nobody runs. FINALPLAY7 uses island41; it contains the canonical
# identity fix and the routing support required by production entry 23. Entry 34
# remains outside production and its RunFunctionFmt fallback still deadlocks.
MGS2_ISLAND_AB_MEASURE="$ENTRY" \
MGS2_BOX86_BIN="${MGS2_BOX86_BIN:-box86-island41}" \
MGS2_WINED3D_DLL="${MGS2_WINED3D_DLL:-wined3d_p56_batch_state.dll}" \
MGS2_D3D8_DLL=d3d8_finalplay3_nocullcache.dll \
MGS2_BOX86_ISLAND_FULL=1 \
MGS2_BOX86_ISLAND_ONLY="$MEASURE_ONLY" \
MGS2_GL_STATS="${MGS2_GL_STATS:-300}" \
MGS2_PLAY_WINEDEBUG="${MGS2_PLAY_WINEDEBUG:-err+all}" \
    exec "$HERE/launch-play.sh"

#!/bin/bash
#
# MGS2 Substance on RG353VS -- best measured configuration, 5 Aug 2026.
#
# Everything here is a measurement, not a preference. Numbers are from the same
# gameplay spot with MGS2_GL_STATS, and where a knob changed nothing it is named
# below anyway so it does not get retried.
#
# ---------------------------------------------------------------- performance
# CPU ceiling is the only confirmed win: cpuinfo_max_freq on this unit is
# 1992000 (overclocked) while the launcher used to cap at 1608000.
#   1608000 top step -> 13.3-13.9 fps      1992000 top step -> 17.7 fps  (+29%)
# The ladder lives in launch.sh (FREQ_STEPS) so every launch path gets it; the
# thermal guard steps it down at 84 C and back up at 76 C, and the temperature
# did not rise from the change.
#
# Measured and worthless, do NOT retry:
#   MGS2_GL_SHM_BUFFERS=3   24.7-34.4 vs 22.8-32.5 fps -- noise
#   MGS2_GL_PBO=1           10.7-12.5 fps -- Mali maps the pack buffer uncached
#   GPU pinned to 800 MHz   GPU wait halves, but the CPU cap falls to 816 MHz
#                           because both share one thermal budget -> net loss
#   GPU capped to 400 MHz   GPU wait grows, no gain
#   presenter rebuilt       identical to the shipped winewayland_pbo1.so
#   WINE_D3D_CONFIG=csmt=0  the game does not start (page fault at 0x3C), twice
#   suspending EmulationStation   ~1 fps, inside scene noise, and it risks
#                           leaving the menu frozen if the game is killed hard
#
# Where the frame actually goes, split with an explicit glFinish:
#   pixel transfer 0.75 ms/f, GPU wait 2.8-9.2 ms/f, game threads 108-117% of a
#   core, wined3d_cs 49-66%. So the limit is CPU plus the SoC thermal budget --
#   not memory bandwidth, and not the frame copy that earlier notes blamed.
#
# Charging matters more than any knob here: with the charger connected the guard
# was seen holding the cap at 1104 MHz, which is 45% below 1992. Play unplugged.
#
# ---------------------------------------------------------------------- audio
# All three DLLs are required together, each for a separately measured reason:
#   dsound_se1    PCM written by a dmsynth sink reaches the speaker at all. With
#                 the system dsound a continuous 1 kHz tone injected into every
#                 sink render was absent from a capture of the speaker monitor.
#   dmime_se1     delivers the SE note. Through the older dmime_graphqi.dll no
#                 note with a non-zero velocity ever reached the synthesiser.
#   dmsynth_se1   upstream 685c5b6 (write latency +10 ms, underruns 222 -> 15)
#                 plus skipping synthesis for blocks with no sounding voice.
# SHAREDGROUPS is what makes it playable rather than merely audible: one port
# per audio path meant fourteen 22050 Hz sink buffers for the DirectSound mixer
# to resample every period under box86. One shared port leaves a single sink.
# SE rides channel group 2, so the group count must stay above 2.
#
# Do not add diagnostic channels here. MGS2_MIXCENSUS logging from the mixer
# thread alone took it from 169 to 930 ticks per 10 s and was audible as
# stuttering; MGS2_GL_STATS needs err+waylanddrv and belongs in a test run only.

GAMEDIR="$(dirname "$0")/MGS2-Substance"

# Keep the tested sink-audible DLL as default, but respect an explicit
# diagnostic/rollback override.  The top-level menu wrapper is the first shell
# in the launch chain; an unconditional assignment here silently defeated
# MGS2_DSOUND_DLL before launch.sh could bind-mount it.
export MGS2_DSOUND_DLL="${MGS2_DSOUND_DLL:-dsound_se1.dll}"
# Transition-correct DirectMusic: PlaySegmentEx now honours its AudioPath and
# controller curves reach their end/reset values.  Keep the older se1 binary
# available for immediate A/B rollback via MGS2_DMIME_DLL.
export MGS2_DMIME_DLL="${MGS2_DMIME_DLL:-dmime_transition1.dll}"
export MGS2_DMUSIC_DLL="${MGS2_DMUSIC_DLL:-dmusic_shared_lifetime1.dll}"
export MGS2_DMSYNTH_DLL="${MGS2_DMSYNTH_DLL:-dmsynth_se4_unmute1.dll}"

export MGS2_DMIME_SHAREDGROUPS="${MGS2_DMIME_SHAREDGROUPS:-1}"
export MGS2_DMIME_SHAREDGROUP_COUNT=4
export MGS2_DMSYNTH_JITTER_MS=30
# A lost note is worse than the small idle cost of the one shared synth.  The
# rebuilt dmsynth also restores FluidSynth's status refresh before it releases
# waves, so either setting can be A/B tested without another build.
export MGS2_DMSYNTH_POLYPHONY="${MGS2_DMSYNTH_POLYPHONY:-48}"
export MGS2_DMSYNTH_IDLE_SKIP="${MGS2_DMSYNTH_IDLE_SKIP:-0}"
# Fixed-size memory recorder.  Keep it off during normal play; an explicit 1
# enables the 256-record ring for a regression without a rebuild.  Note that
# the 2026-08-10 se4 regression began with this off, so the failure itself was
# not captured even though a post-Start recovery snapshot was taken.
export MGS2_DMSYNTH_STATE="${MGS2_DMSYNTH_STATE:-0}"
# Patch 14 is a disproved diagnostic guard.  Leave its code path disabled; the
# transition DLL addresses curve and AudioPath semantics instead.  Setting 1
# remains available only for an explicit regression comparison.
export MGS2_DMSYNTH_UNMUTE_NOTES="${MGS2_DMSYNTH_UNMUTE_NOTES:-0}"

# The stock-user32 control reproduced the apparent freeze: main spent 94% of a
# core in win32u NtUserPeekMessage -> NtYieldExecution while wined3d_cs slept,
# even though the controller, gptokeyb, Fake Keyboard and sway focus were live.
# Restore the measured bounded wait at the one known game caller.  This removes
# that yield spin; it is not yet claimed to cure every input-loss incident.
export MGS2_USER32_DLL="${MGS2_USER32_DLL:-user32_peek1.dll}"
export MGS2_PEEK_WAIT="${MGS2_PEEK_WAIT:-1}"
export MGS2_PEEK_HOT="${MGS2_PEEK_HOT:-401176}"
export MGS2_PEEK_WAIT_MS="${MGS2_PEEK_WAIT_MS:-4}"

# Presentation: measured-best, and identical to launch.sh's own defaults. Pinned
# explicitly so a future change to those defaults cannot silently alter this.
export MGS2_GL_PBO=0
export MGS2_GL_SHM_BUFFERS=2

# Production renderer path: eviction-backed batching, proven direct hash lookup,
# producer aggregation, queue-owned uploads for MGS2's repeated GPU vertex
# buffer NOOVERWRITE locks, and conservative fixed-function frustum culling.
# The matched 1800 MHz A/B/A/B reduced frame time 49.43 -> 47.89 ms and
# WineD3D batches 166.58 -> 136.81 per frame. Visual validation passed on the
# measured heavy spot; MGS2_D3D8_VISIBILITY_CULL=0 is the immediate rollback.
# Diagnostic polling and counters stay off in the shipping launcher.
export MGS2_WINED3D_DLL="${MGS2_WINED3D_DLL:-wined3d_batch16_setcache.dll}"
export MGS2_BATCH="${MGS2_BATCH:-1}"
export MGS2_BATCH_RESTART_HOIST="${MGS2_BATCH_RESTART_HOIST:-1}"
export MGS2_BATCH_HASHCACHE="${MGS2_BATCH_HASHCACHE:-1}"
export MGS2_BATCH_TRIANGLES="${MGS2_BATCH_TRIANGLES:-0}"
export MGS2_BATCH_STATS="${MGS2_BATCH_STATS:-0}"
# Keep launch.sh's measured thermal ladder (1992 -> 1800 -> 1608 -> 1416).
export WINEDEBUG="${WINEDEBUG:--all}"
export MGS2_D3D8_DLL="${MGS2_D3D8_DLL:-d3d8_producer_batch20_visibilitycull.dll}"
export MGS2_D3D8_PRODUCER="${MGS2_D3D8_PRODUCER:-1}"
export MGS2_D3D8_VB_SNAPSHOT="${MGS2_D3D8_VB_SNAPSHOT:-1}"
export MGS2_D3D8_VB_DIRTY_AGGREGATE="${MGS2_D3D8_VB_DIRTY_AGGREGATE:-1}"
export MGS2_D3D8_VB_CENSUS="${MGS2_D3D8_VB_CENSUS:-0}"
export MGS2_D3D8_VISIBILITY_CULL="${MGS2_D3D8_VISIBILITY_CULL:-1}"
export MGS2_D3D8_VISIBILITY_CULL_LIVE="${MGS2_D3D8_VISIBILITY_CULL_LIVE:-0}"
export MGS2_D3D8_VISIBILITY_CULL_STATS="${MGS2_D3D8_VISIBILITY_CULL_STATS:-0}"
export MGS2_CSMT_PROFILE="${MGS2_CSMT_PROFILE:-0}"
export MGS2_D3D8_PROFILE="${MGS2_D3D8_PROFILE:-0}"
export MGS2_D3D8_STATS="${MGS2_D3D8_STATS:-0}"
export MGS2_GL_STATS="${MGS2_GL_STATS:-0}"

exec "$GAMEDIR/launch.sh" "$GAMEDIR"

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

export MGS2_DSOUND_DLL="dsound_se1.dll"
export MGS2_DMIME_DLL="dmime_se1.dll"
export MGS2_DMSYNTH_DLL="dmsynth_se1.dll"

export MGS2_DMIME_SHAREDGROUPS=1
export MGS2_DMIME_SHAREDGROUP_COUNT=4
export MGS2_DMSYNTH_JITTER_MS=30

# Presentation: measured-best, and identical to launch.sh's own defaults. Pinned
# explicitly so a future change to those defaults cannot silently alter this.
export MGS2_GL_PBO=0
export MGS2_GL_SHM_BUFFERS=2

exec "$GAMEDIR/launch.sh" "$GAMEDIR"

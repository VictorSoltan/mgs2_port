#!/bin/sh
# p72: phases A+B+C as ONE native root (entry 41), plus the GL-work census.
#
# CORRECTNESS AND STRUCTURE, NOT TIMING. Two independent reasons this run must
# not be timed: the Box86 binary is the diagnostics build, and the guest DLL is
# compiled with MGS2_GL_CENSUS, which adds a counter increment to every
# GL_EXTCALL. The A/B build will carry neither.
#
# Boundary: guest x86 keeps context_acquire(), current-context ownership,
# render-target/depth preparation, the framebuffer-attachment check, shader phase
# D, the final draw, barriers and context_release(). ARM runs the contiguous
# resource/stream preload, the whole dirty-state loop including its bitmap clear,
# and the resource/UAV bindings with FBO validation.
#
# Why D stays guest, and why this is not a smaller retry of p71: p71 moved D too
# and bound neither a program nor a pipeline, because the island links a second
# copy of glsl_shader.c holding its own nine separable-program entry pointers.
# Phases B and C reference none of them; the fused closure references exactly one
# -- mgs2_glBindProgramPipeline, through shader_glsl_disable -- which is the same
# one phase A has carried in every correct run so far.
#
# The census answers the other half of the FPS question. The profile puts 42.5%
# of all user cycles inside libmali: native driver time that porting WineD3D
# cannot remove, because it is paid per GL call. The counters break it down by
# family -- ext GL calls, draw-state applies, state-table callbacks, uniform
# loads, program selects, texture binds, sampler applies, shader-resource binds,
# FBO checks -- so the next root is chosen from data instead of a guess.
#
# Read with: harness/p72_correctness_read.py <pid> --census-rva 0x1d50c0
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)

# This launcher substitutes binaries, so it has to say so: launch-play.sh refuses
# to accept MGS2_BOX86_BIN and friends from a plain environment, because that used
# to switch off identity verification for every other mounted file at the same
# time. The run is still verified -- a mismatch is reported instead of ignored.
export MGS2_RESEARCH_RUN=1

MGS2_BOX86_BIN="${MGS2_BOX86_BIN:-box86-island53-p72-fused-abc}" \
MGS2_WINED3D_DLL="${MGS2_WINED3D_DLL:-wined3d_p72_fused_abc_census.dll}" \
MGS2_WAYLAND_SO="${MGS2_WAYLAND_SO:-winewayland_p67_frame_witness.so}" \
MGS2_BOX86_ISLAND_FULL=1 \
MGS2_BOX86_ISLAND_ONLY="0,1,2,3,4,5,6,9,10,14,18,19,22,23,28,29,32,33,41" \
MGS2_DRAW_CORRECTNESS=1 \
MGS2_P72_CORRECTNESS=1 \
MGS2_FRAME_WITNESS=1 \
MGS2_REINFORCEMENT_CENSUS=1 \
MGS2_DISPLAY_LOCK_HISTORY=1 \
MGS2_GL_STATS="${MGS2_GL_STATS:-300}" \
MGS2_PLAY_WINEDEBUG="${MGS2_PLAY_WINEDEBUG:--all,err+waylanddrv}" \
exec "$HERE/launch-play.sh"

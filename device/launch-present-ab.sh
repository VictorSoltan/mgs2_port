#!/bin/sh
# WHAT THIS FILE IS NOW, 2026-08-23
#
# The question below was ANSWERED and the header is kept as its record, not as
# instructions. Async collapsed the wait AND the paired frame time moved, so the
# dmabuf presenter was built, measured at -9.45 ms/frame on FINALPLAY8 and shipped
# as FINALPLAY9.
#
# The binary this defaulted to, winewayland_presentab1.so, no longer exists -- it
# was cleared off the device during the FINALPLAY14 cleanup and it is in no
# repository and on no build host, so it cannot come back. It does not need to:
# the ABBA machinery it carried is in the PRODUCTION presenter, which now supplies
# the default here. What changes is that MGS2_PRESENT_AB_MODE is no longer
# optional reading, because the arms differ per mode:
#
#   0 (default)  flips MGS2_GL_ASYNC          -- the original question, below.
#                Needs MGS2_GL_DMABUF=0 to mean anything: the code forces dmabuf
#                off for any nonzero mode but not for this one.
#   1            flips the dmabuf presenter against the shm one -- this is what
#                produced the -9.45 ms result, and the arm names in the log read
#                "async" for dmabuf and "sync" for shm.
#   2            flips wined3d's FFP texture-matrix uniform cache, via TXM1.
#
# MGS2_GL_READ_SPLIT and the MGS2_GL_PBO=0 requirement below apply to mode 0 only.
#
# Present gate: does removing the GPU wait from the frame make the frame shorter?
#
# WHY THIS RUN EXISTS
#
# Every proposal to replace the wl_shm presenter with a dmabuf one -- including
# the one that started this cycle -- prices it by subtracting the presenter's
# `readback` figure from the frame time. Two measurements in this repository say
# that subtraction is invalid:
#
#   brief 26  MGS2_GL_READ_SPLIT on the then-current scene: gpu_finish 4.32 ms,
#             pixel_transfer 0.75 ms. The copy is ~1.6 GB/s. "readback" is almost
#             entirely the CPU waiting for the GPU, not the cost of moving pixels
#   brief 28  MGS2_GL_ASYNC=1 removed that wait -- 10.5-31.7 ms down to 1.5-1.74 --
#             and fps did not move (9.5-17.2 either way)
#
# Brief 28 is the decisive one and it is weak in exactly one way: it was a
# cross-run fps comparison, taken 7 August, before the batcher, the culler, the
# island, the governor fix and the ABBA method. This run re-takes it the way the
# project now requires -- interleaved arms in ONE process on ONE fixed scene --
# so the answer stops resting on a measurement that would not be accepted today.
#
# THE GATE
#
#   async collapses the wait AND paired frame time does not move  -> the whole
#       present branch is closed, and no dmabuf presenter gets built
#   async collapses the wait AND paired frame time improves       -> the old zero
#       is overturned by a better measurement, and GBM -> dma-buf -> EGLImage ->
#       zwp_linux_dmabuf_v1 becomes the next project
#   the wait does NOT collapse on the async arm                   -> the run
#       measured nothing; it is void, not a null
#
# DESIGN
#
# MGS2_PRESENT_AB=<n> flips mgs_cfg.async every n displayed frames inside the
# live process, block%4 -> A B B A, and prints one line per block. Averaging the
# two A blocks against the two B blocks of each cycle cancels linear drift in
# scene and temperature, which a plain A/B/A/B cannot.
#
# MGS2_GL_READ_SPLIT=1 stays on the whole run. Note what it does and does not
# perturb: the extra glFinish lives only in the synchronous branch, so the async
# arm is untouched and arm A carries the whole diagnostic cost. glFinish before
# glReadPixels adds no work -- the read would have blocked on the same fence --
# but if it biases anything it biases AGAINST the sync arm, which makes a null
# result conservative and an async win suspect. Read it that way.
#
# MGS2_GL_PBO must stay 0: the PBO branch never consults mgs_cfg.async, so both
# arms would run identical code and produce a structural zero. The driver refuses
# the run rather than print one.
#
# EVERYTHING ELSE IS p72c. Same box86, same wined3d, same island list, so the
# baseline arm should reproduce the p72c soak's heavy-scene rate. If it does not,
# something else changed and the run is not comparable.
#
# Reduce with harness/present_ab_read.py. Sign convention: negative delta means
# ASYNC is faster.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)

# This launcher substitutes binaries, so it has to say so: launch-play.sh refuses
# to accept MGS2_BOX86_BIN and friends from a plain environment, because that used
# to switch off identity verification for every other mounted file at the same
# time. The run is still verified -- a mismatch is reported instead of ignored.
export MGS2_RESEARCH_RUN=1

MGS2_WAYLAND_SO="${MGS2_WAYLAND_SO:-winewayland_dmabuf_prod.so}" \
MGS2_PRESENT_AB="${MGS2_PRESENT_AB:-64}" \
MGS2_PRESENT_AB_SETTLE="${MGS2_PRESENT_AB_SETTLE:-2}" \
MGS2_GL_READ_SPLIT=1 \
MGS2_GL_PBO=0 \
MGS2_BOX86_BIN="${MGS2_BOX86_BIN:-box86-island55-p72c-candidate}" \
MGS2_WINED3D_DLL="${MGS2_WINED3D_DLL:-wined3d_p72c_fused_abc.dll}" \
MGS2_BOX86_ISLAND_FULL=1 \
MGS2_BOX86_ISLAND_ONLY="0,1,2,3,4,5,6,9,10,14,18,19,22,23,28,29,32,33,41" \
MGS2_GL_STATS="${MGS2_GL_STATS:-300}" \
MGS2_PLAY_WINEDEBUG="${MGS2_PLAY_WINEDEBUG:--all,err+waylanddrv}" \
exec "$HERE/launch-play.sh"

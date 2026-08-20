#!/bin/sh
# Correctness-only gate for native CS DRAW after the p66 black-frame result.
# No A/B and no FPS claim: synchronize the ARM context TLS index once, count
# source/final submissions in memory, and retain only 64 bounded frame hashes.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)

MGS2_BOX86_BIN="${MGS2_BOX86_BIN:-box86-island45-p67-tls}" \
MGS2_WINED3D_DLL="${MGS2_WINED3D_DLL:-wined3d_p66_cs_draw_clean.dll}" \
MGS2_WAYLAND_SO="${MGS2_WAYLAND_SO:-winewayland_p67_frame_witness.so}" \
MGS2_BOX86_ISLAND_FULL=1 \
MGS2_BOX86_ISLAND_ONLY="0,1,2,3,4,5,6,9,10,14,18,19,22,23,28,29,32,33,37" \
MGS2_DRAW_CORRECTNESS=1 \
MGS2_FRAME_WITNESS=1 \
MGS2_REINFORCEMENT_CENSUS=1 \
MGS2_GL_STATS="${MGS2_GL_STATS:-300}" \
# Box86 prints the one cold TLS line independently.  Keep WineD3D's hot ERR
# channel off: the first p67 run used err+all and repeated GL_INVALID_OPERATION
# lines, which cannot be allowed in any follow-up even though no timing was used.
MGS2_PLAY_WINEDEBUG="${MGS2_PLAY_WINEDEBUG:--all,err+waylanddrv}" \
exec "$HERE/launch-play.sh"

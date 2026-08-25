#!/bin/sh
# Research-only MGS2 D3D8 -> DXVK-Sarek -> proprietary Mali arm.
#
# This does not change FINALPLAY16 defaults. It selects a matched D3D8/D3D9
# pair from Sarek v1.11.1-mali-fix and the Box86 native Wayland/Vulkan bridge
# already proven by DMC3. Correctness comes before any frame-time comparison.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
LOGDIR="$HERE/logs/dxvk-sarek"
mkdir -p "$LOGDIR"

D3D8=d3d8_dxvk_sarek_1.11.1_mali_wsiinit3.dll
D3D9=d3d9_dxvk_sarek_1.11.1_mali_pipeline_normal1.dll
BOX86=box86-fp17-dxvk-quiet

verify_one() {
    want="$1"
    file="$2"
    got=$(sha256sum "$HERE/$file" 2>/dev/null | cut -d' ' -f1)
    if [ "$got" != "$want" ]; then
        echo "MGS2 DXVK: $file is ${got:-missing}, expected $want" >&2
        exit 1
    fi
}

verify_one 22e519d266b62bfa54d1d1f81e6314aab7b75890b342908f24d2b454e4af3baa "$D3D8"
verify_one debaef7a89da2c82b1232beff3ddf9ec31f6ec62a30d645b04b36c232563af53 "$D3D9"
verify_one 83f9349c6dc26f8f769e714a5ed57c4d76f3a523161ead31f75e52ccc1da7fba "$BOX86"

export MGS2_RESEARCH_RUN=dxvk-sarek-pipeline-normal
export MGS2_BOX86_BIN="$BOX86"
export MGS2_DXVK_D3D8_DLL="$D3D8"
export MGS2_DXVK_D3D9_DLL="$D3D9"
export MGS2_DXVK_WINE_MODE=direct32
export MGS2_IDENTITY_MANIFEST=FINALPLAY16_DXVK_PIPELINE_NORMAL.manifest

# DXVK needs Box86's native libwayland-client wrapper so native libmali receives
# native wl_display / wl_surface objects. Keep all other compatibility choices
# identical to production.
export MGS2_BOX86_EMULATED_LIBS='winewayland.so:winevulkan.so:libffi.so.8:libwayland-egl.so.1:libxkbcommon.so.0:libxkbregistry.so.0:libxml2.so.2:libicuuc.so.72:libicudata.so.72:liblzma.so.5:libstdc++.so.6'
export MGS2_WINEDLLOVERRIDES='mscoree=;mshtml=;winemenubuilder.exe=;winepulse.drv=d;d3d8=n,b;d3d9=n,b;dxgi=builtin'

# WineD3D's native island does not render this arm. Leave the non-renderer FP15
# bridges (memmove, DirectSound FIR, dither and mutex fixes) available in Box86.
export MGS2_BOX86_ISLAND_FULL=0

# The trace itself is always enabled in this research launcher. State cache is
# still explicit so cold and warm observations cannot be mixed accidentally.
export DXVK_STATE_CACHE="${MGS2_DXVK_STATE_CACHE:-0}"
export MGS2_DXVK_PIPELINE_TRACE=1
export DXVK_STATE_CACHE_PATH="${MGS2_DXVK_STATE_CACHE_PATH:-$HERE/cache/dxvk-state}"
if [ "$DXVK_STATE_CACHE" != 0 ]; then
    mkdir -p "$DXVK_STATE_CACHE_PATH"
fi
export DXVK_LOG_LEVEL="${MGS2_DXVK_LOG_LEVEL:-info}"
export DXVK_LOG_PATH="$LOGDIR"
export DXVK_HUD="${MGS2_DXVK_HUD:-fps}"
export MGS2_GL_STATS=0
# DXVK presents through Vulkan WSI. The WineD3D-specific DMABUF presenter must
# stay dormant; otherwise Wine's explorer initializes that second Vulkan path
# before it can signal desktop readiness to the game process.
export MGS2_GL_DMABUF=0

echo "MGS2 DXVK: PIPELINE NORMAL-PRIORITY A/B, state_cache=$DXVK_STATE_CACHE cache_path=$DXVK_STATE_CACHE_PATH" >&2
echo "MGS2 DXVK: d3d8=$D3D8 d3d9=$D3D9 box86=$BOX86" >&2
exec "$HERE/launch-dxvk-play.sh"

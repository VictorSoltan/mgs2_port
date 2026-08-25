#!/bin/sh
# Research-only FINALPLAY17 freeze candidate: fused DXT plus a deduplicated
# warm DXVK state cache with one compiler worker. This uses the uninstrumented
# D3D9 build and the Box86 production-mode bridge without hot-path counters.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
LOGDIR="$HERE/logs/dxvk-sarek-freeze-candidate"
mkdir -p "$LOGDIR"

D3D8=d3d8_dxvk_sarek_1.11.1_mali_wsiinit3.dll
D3D9=d3d9_dxvk_sarek_1.11.1_mali_freeze1.dll
BOX86=box86-fp21-dxvk-native-dxt-surface

verify_one() {
    want="$1"
    file="$2"
    got=$(sha256sum "$HERE/$file" 2>/dev/null | cut -d' ' -f1)
    if [ "$got" != "$want" ]; then
        echo "MGS2 freeze candidate: $file is ${got:-missing}, expected $want" >&2
        exit 1
    fi
}

verify_one 22e519d266b62bfa54d1d1f81e6314aab7b75890b342908f24d2b454e4af3baa "$D3D8"
verify_one 4918b0283329702116dc64fba2e7be992a8b67ef2534ccf5af919f334c690650 "$D3D9"
verify_one 51dfcc130b9760970189a67edd8cd78c777c5d69c8b9ec07cfbc5657821d9be9 "$BOX86"

export MGS2_RESEARCH_RUN=dxvk-sarek-freeze-candidate
export MGS2_BOX86_BIN="$BOX86"
export MGS2_DXVK_D3D8_DLL="$D3D8"
export MGS2_DXVK_D3D9_DLL="$D3D9"
export MGS2_DXVK_WINE_MODE=direct32
export MGS2_IDENTITY_MANIFEST=FINALPLAY17_DXVK_FREEZE.manifest

export MGS2_BOX86_NATIVE_DXT=0
export MGS2_BOX86_NATIVE_DXT_SURFACE="${MGS2_DXT_SURFACE_MODE:-1}"
unset MGS2_DXVK_STATE_CACHE_DEDUPE MGS2_DXVK_PIPELINE_TRACE

export MGS2_BOX86_EMULATED_LIBS='winewayland.so:winevulkan.so:libffi.so.8:libwayland-egl.so.1:libxkbcommon.so.0:libxkbregistry.so.0:libxml2.so.2:libicuuc.so.72:libicudata.so.72:liblzma.so.5:libstdc++.so.6'
export MGS2_WINEDLLOVERRIDES='mscoree=;mshtml=;winemenubuilder.exe=;winepulse.drv=d;d3d8=n,b;d3d9=n,b;dxgi=builtin'
export MGS2_BOX86_ISLAND_FULL=0

export DXVK_STATE_CACHE="${MGS2_DXVK_STATE_CACHE:-1}"
export DXVK_STATE_CACHE_PATH="${MGS2_DXVK_STATE_CACHE_PATH:-$HERE/cache/dxvk-state}"
mkdir -p "$DXVK_STATE_CACHE_PATH"
# In exact Sarek source this legacy switch is applied after numCompilerThreads
# and would silently replace the measured single worker with all four cores.
unset DXVK_ALL_CORES
export DXVK_CONFIG="${MGS2_DXVK_CONFIG:-dxvk.numCompilerThreads = 1}"
export DXVK_LOG_LEVEL="${MGS2_DXVK_LOG_LEVEL:-info}"
export DXVK_LOG_PATH="$LOGDIR"
export DXVK_HUD="${MGS2_DXVK_HUD:-fps}"
export MGS2_GL_STATS=0
export MGS2_GL_DMABUF=0

echo "MGS2 DXVK: RESEARCH freeze candidate cache=$DXVK_STATE_CACHE workers=1" >&2
echo "MGS2 DXVK: d3d8=$D3D8 d3d9=$D3D9 box86=$BOX86" >&2
exec "$HERE/launch-dxvk-play.sh"

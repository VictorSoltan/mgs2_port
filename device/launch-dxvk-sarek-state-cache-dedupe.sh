#!/bin/sh
# Research-only FINALPLAY16 + fused DXT + exact state-cache mapping dedupe.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
LOGDIR="$HERE/logs/dxvk-sarek-state-cache-dedupe"
mkdir -p "$LOGDIR"

D3D8=d3d8_dxvk_sarek_1.11.1_mali_wsiinit3.dll
D3D9=d3d9_dxvk_sarek_1.11.1_mali_state_cache_dedupe1.dll
BOX86=box86-fp19-dxvk-native-dxt-surface

verify_one() {
    want="$1"
    file="$2"
    got=$(sha256sum "$HERE/$file" 2>/dev/null | cut -d' ' -f1)
    if [ "$got" != "$want" ]; then
        echo "MGS2 state-cache dedupe: $file is ${got:-missing}, expected $want" >&2
        exit 1
    fi
}

verify_one 22e519d266b62bfa54d1d1f81e6314aab7b75890b342908f24d2b454e4af3baa "$D3D8"
verify_one 5a24bb386d5dd874791174b22addfb901b1b6301c950bd27e58a75404d08d677 "$D3D9"
verify_one bf0daac76f0af4e77bf0fdf668947bb12e0b44ace85ad91e85f6fc30bf53a40e "$BOX86"

export MGS2_RESEARCH_RUN=dxvk-sarek-state-cache-dedupe
export MGS2_BOX86_BIN="$BOX86"
export MGS2_DXVK_D3D8_DLL="$D3D8"
export MGS2_DXVK_D3D9_DLL="$D3D9"
export MGS2_DXVK_WINE_MODE=direct32
export MGS2_IDENTITY_MANIFEST=FINALPLAY16_DXVK_STATE_CACHE_DEDUPE.manifest
export MGS2_BOX86_NATIVE_DXT=0
export MGS2_BOX86_NATIVE_DXT_SURFACE="${MGS2_DXT_SURFACE_MODE:-2}"
export MGS2_DXVK_STATE_CACHE_DEDUPE="${MGS2_STATE_CACHE_DEDUPE:-1}"
export MGS2_DXVK_PIPELINE_TRACE=1

export MGS2_BOX86_EMULATED_LIBS='winewayland.so:winevulkan.so:libffi.so.8:libwayland-egl.so.1:libxkbcommon.so.0:libxkbregistry.so.0:libxml2.so.2:libicuuc.so.72:libicudata.so.72:liblzma.so.5:libstdc++.so.6'
export MGS2_WINEDLLOVERRIDES='mscoree=;mshtml=;winemenubuilder.exe=;winepulse.drv=d;d3d8=n,b;d3d9=n,b;dxgi=builtin'
export MGS2_BOX86_ISLAND_FULL=0

export DXVK_STATE_CACHE="${MGS2_DXVK_STATE_CACHE:-1}"
export DXVK_STATE_CACHE_PATH="${MGS2_DXVK_STATE_CACHE_PATH:-$HERE/cache/dxvk-state}"
mkdir -p "$DXVK_STATE_CACHE_PATH"
export DXVK_LOG_LEVEL="${MGS2_DXVK_LOG_LEVEL:-info}"
export DXVK_LOG_PATH="$LOGDIR"
export DXVK_HUD="${MGS2_DXVK_HUD:-fps}"
export MGS2_GL_STATS=0
export MGS2_GL_DMABUF=0

echo "MGS2 DXVK: RESEARCH state-cache-dedupe=$MGS2_DXVK_STATE_CACHE_DEDUPE DXT-surface=$MGS2_BOX86_NATIVE_DXT_SURFACE" >&2
echo "MGS2 DXVK: d3d8=$D3D8 d3d9=$D3D9 box86=$BOX86" >&2
exec "$HERE/launch-dxvk-play.sh"

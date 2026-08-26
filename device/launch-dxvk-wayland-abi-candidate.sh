#!/bin/sh
# Research-only FINALPLAY17 runtime with Box86 patch 23.  The renderer, cache,
# worker count, Wine prefix and every other mounted byte stay at FINALPLAY17.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
D3D8=d3d8_dxvk_sarek_1.11.1_mali_wsiinit3.dll
D3D9=d3d9_dxvk_sarek_1.11.1_mali_freeze1.dll
BOX86=box86-fp23-wayland-abi-candidate

verify_one() {
    want="$1"
    file="$2"
    got=$(sha256sum "$HERE/$file" 2>/dev/null | cut -d' ' -f1)
    if [ "$got" != "$want" ]; then
        echo "MGS2 Wayland ABI candidate: $file is ${got:-missing}, expected $want" >&2
        exit 1
    fi
}

verify_one 22e519d266b62bfa54d1d1f81e6314aab7b75890b342908f24d2b454e4af3baa "$D3D8"
verify_one 4918b0283329702116dc64fba2e7be992a8b67ef2534ccf5af919f334c690650 "$D3D9"
verify_one 750227508181a929a3973e6d65bb70d60b7c42b60542cb16b021e192815ccf24 "$BOX86"

export MGS2_RESEARCH_RUN=box86-wayland-abi-candidate
export MGS2_BOX86_BIN="$BOX86"
export MGS2_DXVK_D3D8_DLL="$D3D8"
export MGS2_DXVK_D3D9_DLL="$D3D9"
export MGS2_DXVK_WINE_MODE=direct32
export MGS2_IDENTITY_MANIFEST=BOX86_WAYLAND_ABI_CANDIDATE.manifest

export MGS2_BOX86_NATIVE_DXT=0
export MGS2_BOX86_NATIVE_DXT_SURFACE=1
unset MGS2_DXVK_STATE_CACHE_DEDUPE MGS2_DXVK_PIPELINE_TRACE DXVK_ALL_CORES

export MGS2_BOX86_EMULATED_LIBS='winewayland.so:winevulkan.so:libffi.so.8:libwayland-egl.so.1:libxkbcommon.so.0:libxkbregistry.so.0:libxml2.so.2:libicuuc.so.72:libicudata.so.72:liblzma.so.5:libstdc++.so.6'
export MGS2_WINEDLLOVERRIDES='mscoree=;mshtml=;winemenubuilder.exe=;winepulse.drv=d;d3d8=n,b;d3d9=n,b;dxgi=builtin'
export MGS2_BOX86_ISLAND_FULL=0

export DXVK_STATE_CACHE=1
export DXVK_STATE_CACHE_PATH="$HERE/cache/dxvk-state"
mkdir -p "$DXVK_STATE_CACHE_PATH"
export DXVK_CONFIG='dxvk.numCompilerThreads = 1'
export DXVK_LOG_LEVEL=none
export DXVK_HUD=0
export MGS2_GL_STATS=0
export MGS2_GL_DMABUF=0

echo "MGS2 DXVK: RESEARCH Box86 Wayland listener ABI candidate" >&2
echo "MGS2 DXVK: d3d8=$D3D8 d3d9=$D3D9 box86=$BOX86" >&2
exec "$HERE/launch-dxvk-play.sh"

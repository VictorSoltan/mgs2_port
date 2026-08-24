#!/bin/sh
# Research-only FINALPLAY16 + bounded Wine Win32 wait census.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
LOGDIR="$HERE/logs/dxvk-sarek-wait-census"
mkdir -p "$LOGDIR"

D3D8=d3d8_dxvk_sarek_1.11.1_mali_wsiinit3.dll
D3D9=d3d9_dxvk_sarek_1.11.1_mali_count1.dll
BOX86=box86-fp17-dxvk-quiet
KERNELBASE=kernelbase_wait_census3.dll

verify_one() {
    want="$1"
    file="$2"
    got=$(sha256sum "$HERE/$file" 2>/dev/null | cut -d' ' -f1)
    if [ "$got" != "$want" ]; then
        echo "MGS2 wait census: $file is ${got:-missing}, expected $want" >&2
        exit 1
    fi
}

verify_one 22e519d266b62bfa54d1d1f81e6314aab7b75890b342908f24d2b454e4af3baa "$D3D8"
verify_one cf67ce743ebe4c4e0ce909811193b3a90b234d74feec4649d018c9b956fe6b92 "$D3D9"
verify_one 83f9349c6dc26f8f769e714a5ed57c4d76f3a523161ead31f75e52ccc1da7fba "$BOX86"
verify_one 115247fb3a44b1d03122b2b0f2f649b0f95115b4c1a31c90286945dc56c6cda1 "$KERNELBASE"

export MGS2_RESEARCH_RUN=dxvk-sarek-wait-census
export MGS2_BOX86_BIN="$BOX86"
export MGS2_DXVK_D3D8_DLL="$D3D8"
export MGS2_DXVK_D3D9_DLL="$D3D9"
export MGS2_KERNELBASE_DLL="$KERNELBASE"
export MGS2_DXVK_WINE_MODE=direct32
export MGS2_IDENTITY_MANIFEST=FINALPLAY16_DXVK_WAIT_CENSUS.manifest
export MGS2_WAIT_CENSUS=1

export MGS2_BOX86_EMULATED_LIBS='winewayland.so:winevulkan.so:libffi.so.8:libwayland-egl.so.1:libxkbcommon.so.0:libxkbregistry.so.0:libxml2.so.2:libicuuc.so.72:libicudata.so.72:liblzma.so.5:libstdc++.so.6'
export MGS2_WINEDLLOVERRIDES='mscoree=;mshtml=;winemenubuilder.exe=;winepulse.drv=d;d3d8=n,b;d3d9=n,b;dxgi=builtin'
export MGS2_BOX86_ISLAND_FULL=0

export DXVK_STATE_CACHE="${MGS2_DXVK_STATE_CACHE:-0}"
export DXVK_STATE_CACHE_PATH="${MGS2_DXVK_STATE_CACHE_PATH:-$HERE/cache/dxvk-state}"
if [ "$DXVK_STATE_CACHE" != 0 ]; then mkdir -p "$DXVK_STATE_CACHE_PATH"; fi
export DXVK_LOG_LEVEL="${MGS2_DXVK_LOG_LEVEL:-info}"
export DXVK_LOG_PATH="$LOGDIR"
export DXVK_HUD="${MGS2_DXVK_HUD:-fps}"
export MGS2_GL_STATS=0
export MGS2_GL_DMABUF=0

echo "MGS2 DXVK: RESEARCH bounded Win32 wait census" >&2
echo "MGS2 DXVK: d3d8=$D3D8 d3d9=$D3D9 box86=$BOX86 kernelbase=$KERNELBASE" >&2
exec "$HERE/launch-dxvk-play.sh"

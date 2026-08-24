#!/bin/sh
# Research-only DXVK-Sarek async arm with an externally readable skipped-draw
# counter. Missing graphics pipelines may still make objects disappear until a
# background compiler finishes, so this must never become the default from a
# timing result alone.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
LOGDIR="$HERE/logs/dxvk-sarek-async-skip"
mkdir -p "$LOGDIR"

D3D8=d3d8_dxvk_sarek_1.11.0_async_mali_wsi1.dll
D3D9=d3d9_dxvk_sarek_1.11.0_async_mali_countskip1.dll
BOX86=box86-fp17-dxvk-quiet

verify_one() {
    want="$1"
    file="$2"
    got=$(sha256sum "$HERE/$file" 2>/dev/null | cut -d' ' -f1)
    if [ "$got" != "$want" ]; then
        echo "MGS2 DXVK async-skip: $file is ${got:-missing}, expected $want" >&2
        exit 1
    fi
}

verify_one 2b811cf2bf86309c44ccf9af0161d366289b1e1554e275010f96d26e40bb4131 "$D3D8"
verify_one a2304c52fdfbbb3792098f65458a7c6e4b018650c6b50f62aa9eb0e04b93be7c "$D3D9"
verify_one 83f9349c6dc26f8f769e714a5ed57c4d76f3a523161ead31f75e52ccc1da7fba "$BOX86"

export MGS2_RESEARCH_RUN=dxvk-sarek-async-skip-d3d8
export MGS2_BOX86_BIN="$BOX86"
export MGS2_DXVK_D3D8_DLL="$D3D8"
export MGS2_DXVK_D3D9_DLL="$D3D9"
export MGS2_DXVK_WINE_MODE=direct32
export MGS2_IDENTITY_MANIFEST=FINALPLAY16_DXVK_ASYNC_SKIP.manifest

export MGS2_BOX86_EMULATED_LIBS='winewayland.so:winevulkan.so:libffi.so.8:libwayland-egl.so.1:libxkbcommon.so.0:libxkbregistry.so.0:libxml2.so.2:libicuuc.so.72:libicudata.so.72:liblzma.so.5:libstdc++.so.6'
export MGS2_WINEDLLOVERRIDES='mscoree=;mshtml=;winemenubuilder.exe=;winepulse.drv=d;d3d8=n,b;d3d9=n,b;dxgi=builtin'
export MGS2_BOX86_ISLAND_FULL=0

export DXVK_ASYNC="${MGS2_DXVK_ASYNC:-1}"
export ASYNC_DRAW_CALL_THRESHOLD="${MGS2_ASYNC_DRAW_CALL_THRESHOLD:-5}"
export DXVK_STATE_CACHE="${MGS2_DXVK_STATE_CACHE:-0}"
export DXVK_STATE_CACHE_PATH="${MGS2_DXVK_STATE_CACHE_PATH:-$HERE/cache/dxvk-state-async-skip}"
if [ "$DXVK_STATE_CACHE" != 0 ]; then
    mkdir -p "$DXVK_STATE_CACHE_PATH"
fi
export DXVK_LOG_LEVEL="${MGS2_DXVK_LOG_LEVEL:-info}"
export DXVK_LOG_PATH="$LOGDIR"
export DXVK_HUD="${MGS2_DXVK_HUD:-fps}"
export MGS2_GL_STATS=0
export MGS2_GL_DMABUF=0

echo "MGS2 DXVK async-skip: RESEARCH arm, async=$DXVK_ASYNC threshold=$ASYNC_DRAW_CALL_THRESHOLD state_cache=$DXVK_STATE_CACHE" >&2
echo "MGS2 DXVK async-skip: d3d8=$D3D8 d3d9=$D3D9 box86=$BOX86" >&2
exec "$HERE/launch-dxvk-play.sh"

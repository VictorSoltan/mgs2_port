#!/bin/sh
# Reconstruct the two FINALPLAY17 DXVK DLLs from their distinct source stages.
# D3D8 is base+02 with libstdc++ assertions disabled; D3D9 is base+01+02+08.
# The difference is part of the shipped provenance, not an optimisation choice.
set -eu

REPO=$(cd "$(dirname "$0")/.." && pwd)
_mgs2_workspace_set=${MGS2_WORKSPACE+x}; _mgs2_workspace=${MGS2_WORKSPACE-}
_dxvk_src_set=${DXVK_SRC+x};             _dxvk_src=${DXVK_SRC-}
_dxvk_meson_set=${DXVK_MESON+x};         _dxvk_meson=${DXVK_MESON-}
_dxvk_ninja_set=${DXVK_NINJA+x};         _dxvk_ninja=${DXVK_NINJA-}
_dxvk_cross_set=${DXVK_CROSS_FILE+x};     _dxvk_cross=${DXVK_CROSS_FILE-}
if [ -r "$REPO/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$REPO/.env"
    set +a
fi
[ "$_mgs2_workspace_set" = x ] && MGS2_WORKSPACE=$_mgs2_workspace
[ "$_dxvk_src_set" = x ]       && DXVK_SRC=$_dxvk_src
[ "$_dxvk_meson_set" = x ]     && DXVK_MESON=$_dxvk_meson
[ "$_dxvk_ninja_set" = x ]     && DXVK_NINJA=$_dxvk_ninja
[ "$_dxvk_cross_set" = x ]     && DXVK_CROSS_FILE=$_dxvk_cross
WORKSPACE="${MGS2_WORKSPACE:-$(dirname "$REPO")}"
LOCK="$REPO/device/FINALPLAY.lock"
DXVK_SRC="${DXVK_SRC:-$WORKSPACE/DXVK-Sarek}"
MESON="${DXVK_MESON:-meson}"
NINJA="${DXVK_NINJA:-ninja}"
CROSS_FILE="${DXVK_CROSS_FILE:-}"
lock() { awk -v k="$1" '$1==k {print $2}' "$LOCK"; }

[ -d "$DXVK_SRC/.git" ] || {
    echo "DXVK source checkout missing: $DXVK_SRC" >&2
    echo "set DXVK_SRC to a clone with initialized Vulkan/SPIR-V submodules" >&2
    exit 1
}
[ -r "$CROSS_FILE" ] || {
    echo "set DXVK_CROSS_FILE to the local Meson i686-w64-mingw32 cross file" >&2
    exit 1
}
base=$(lock dxvk_base_commit)
git -C "$DXVK_SRC" cat-file -e "$base^{commit}" 2>/dev/null || {
    echo "DXVK base $base is absent from $DXVK_SRC" >&2
    exit 1
}

check_submodule() {
    name="$1"; want="$2"
    got=$(git -C "$DXVK_SRC/include/$name" rev-parse HEAD 2>/dev/null || true)
    [ "$got" = "$want" ] || {
        echo "DXVK $name headers are ${got:-missing}, expected $want" >&2
        exit 1
    }
}
check_submodule spirv "$(lock dxvk_spirv_headers_commit)"
check_submodule vulkan "$(lock dxvk_vulkan_headers_commit)"

meson_version=$($MESON --version 2>/dev/null || true)
ninja_version=$($NINJA --version 2>/dev/null || true)
glslang=$(command -v glslang 2>/dev/null || command -v glslangValidator 2>/dev/null || true)
glslang_version=$([ -n "$glslang" ] && "$glslang" --version 2>/dev/null \
    | awk '/^Glslang Version:/ {v=$3; sub(/^[0-9]+:/, "", v); print v; exit}' || true)
[ "$meson_version" = "$(lock dxvk_meson_version)" ] || {
    echo "Meson is ${meson_version:-missing}, lock requires $(lock dxvk_meson_version)" >&2
    exit 1
}
[ "$ninja_version" = "$(lock dxvk_ninja_version)" ] || {
    echo "Ninja is ${ninja_version:-missing}, lock requires $(lock dxvk_ninja_version)" >&2
    exit 1
}
[ "$glslang_version" = "$(lock dxvk_glslang_version)" ] || {
    echo "glslang is ${glslang_version:-missing}, lock requires $(lock dxvk_glslang_version)" >&2
    exit 1
}

WORK=$(mktemp -d /tmp/mgs2-dxvk-verify.XXXXXX)
cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT HUP INT TERM

unpack_source() {
    stage="$1"
    mkdir -p "$WORK/$stage/src/include/spirv" "$WORK/$stage/src/include/vulkan"
    git -C "$DXVK_SRC" archive "$base" | tar -x -C "$WORK/$stage/src"
    cp -a "$DXVK_SRC/include/spirv/." "$WORK/$stage/src/include/spirv/"
    cp -a "$DXVK_SRC/include/vulkan/." "$WORK/$stage/src/include/vulkan/"
}

apply_stage_patches() {
    stage="$1"; prefix="$2"
    for rel in $(awk -v p="$prefix" '$1 ~ ("^" p "_patch_") {print $2}' "$LOCK"); do
        patch -d "$WORK/$stage/src" -p1 -E --silent < "$REPO/$rel"
    done
}

build_stage() {
    stage="$1"; target="$2"; ndebug="$3"; epoch="$4"; want="$5"
    log="$WORK/$stage-build.log"
    if ! "$MESON" setup "$WORK/$stage/build" "$WORK/$stage/src" \
            --cross-file "$CROSS_FILE" --buildtype release -Dbuild_id=false \
            -Db_ndebug="$ndebug" >"$log" 2>&1; then
        echo "$stage Meson setup failed:" >&2; tail -20 "$log" >&2; exit 1
    fi
    if ! SOURCE_DATE_EPOCH="$epoch" "$NINJA" -C "$WORK/$stage/build" \
            "$target" >>"$log" 2>&1; then
        echo "$stage build failed:" >&2; tail -30 "$log" >&2; exit 1
    fi
    got=$(sha256sum "$WORK/$stage/build/$target" | cut -d' ' -f1)
    if [ "$got" != "$want" ]; then
        echo "FAIL   $stage rebuilt $got, production is $want" >&2
        exit 1
    fi
    echo "ok     $stage rebuilt byte for byte: $got"
}

unpack_source d3d8
apply_stage_patches d3d8 dxvk_d3d8
build_stage d3d8 src/d3d8/d3d8.dll "$(lock dxvk_d3d8_b_ndebug)" \
    "$(lock dxvk_d3d8_source_date_epoch)" "$(lock finalplay17_d3d8_sha256)"

unpack_source d3d9
apply_stage_patches d3d9 dxvk_d3d9
build_stage d3d9 src/d3d9/d3d9.dll "$(lock dxvk_d3d9_b_ndebug)" \
    "$(lock dxvk_d3d9_source_date_epoch)" "$(lock finalplay17_d3d9_sha256)"

echo "FINALPLAY17 DXVK binaries are reproducible from the pinned stages"

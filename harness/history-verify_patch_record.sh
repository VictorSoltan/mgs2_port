#!/bin/sh
# SUPERSEDED by verify_rebuild.sh -- kept only because its narrower question is
# still worth asking cheaply during development.
#
# What this script checks is that the two MOST RECENT patches match the two live
# trees. That is much weaker than it sounds, and it passed while the trees were
# not reproducible at all: the numbered wine series lands 53 of 67 patches on a
# pristine tree, the fourteen failures include the dmabuf presenter, the lazy
# stage selector and the light cache, and twenty-five files still differed. Run
# verify_rebuild.sh before cutting anything.
#
# Do the patch files in this repo still reconstruct the sources they claim to?
#
# This matters more here than in a normal project, because the code that ends up
# in the shipped binaries does not live in this repository:
#
#   mgs2-rg353vs-port  patch files, harness, manifest      -- git, committed
#   box86-src          native bridges, dynarec hooks       -- git, working tree
#   recovered-session/wine-11.0  wined3d                   -- NOT under git at all
#
# So for WineD3D the .patch file is the only record there is, and a record no one
# checks is a record no one can rely on. This reconstructs each one and compares
# it against the live tree.
#
# usage: verify_patch_record.sh
set -u
REPO=$(cd "$(dirname "$0")/.." && pwd)
WINE="${WINE_SRC:-/mnt/data/holden/mgs/recovered-session/wine-11.0}"
BOX86="${BOX86_SRC:-/mnt/data/holden/mgs/box86-src}"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
fail=0

check_wine() {
    patch_file="$1"; src="$2"
    base="$WINE/$src.orig"
    live="$WINE/$src"
    [ -r "$base" ] || { echo "MISSING baseline $base"; fail=1; return; }
    cp "$base" "$TMP/f"
    sed -n '/^--- /,$p' "$patch_file" > "$TMP/d"
    if ! patch -s -p0 "$TMP/f" < "$TMP/d" 2>/dev/null; then
        echo "FAIL   $(basename "$patch_file") does not apply to $src.orig"
        fail=1; return
    fi
    if cmp -s "$TMP/f" "$live"; then
        echo "ok     $(basename "$patch_file") reconstructs $src byte for byte"
    else
        echo "FAIL   $(basename "$patch_file") applies but differs from the live $src"
        fail=1
    fi
}

check_box86() {
    patch_file="$1"; shift
    sed -n '/^diff --git/,$p' "$patch_file" > "$TMP/recorded"
    ( cd "$BOX86" && git diff -- "$@" ) > "$TMP/live"
    if cmp -s "$TMP/recorded" "$TMP/live"; then
        echo "ok     $(basename "$patch_file") matches the box86-src working tree"
    else
        echo "FAIL   $(basename "$patch_file") is stale against box86-src"
        fail=1
    fi
}

check_wine "$REPO/wine-patches/79-light-cache-and-program-binary-probe.patch" \
        dlls/wined3d/glsl_shader.c
check_box86 "$REPO/box86-patches/16-native-x87-dither.patch" \
        src/box86context.c src/tools/bridge.c src/include/bridge.h src/dynarec/dynarec.c

echo
if [ "$fail" = 0 ]; then
    echo "the patch record is faithful to both source trees"
else
    echo "THE PATCH RECORD IS STALE -- regenerate before shipping anything else"
fi
exit "$fail"

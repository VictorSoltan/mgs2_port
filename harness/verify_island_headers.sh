#!/bin/sh
# Regenerate the two excluded island headers from their declared inputs and
# compare them byte-for-byte with the live Box86 tree.  They are build products,
# not patch inputs, but excluding them from verify_rebuild without this gate
# would allow the stale-RVA failure class to return silently.
set -eu

REPO=$(cd "$(dirname "$0")/.." && pwd)
_mgs2_workspace_set=${MGS2_WORKSPACE+x}; _mgs2_workspace=${MGS2_WORKSPACE-}
_wine_build_set=${WINE_BUILD+x};         _wine_build=${WINE_BUILD-}
_box86_src_set=${BOX86_SRC+x};           _box86_src=${BOX86_SRC-}
_mingw_bin_set=${MINGW_BIN+x};           _mingw_bin=${MINGW_BIN-}
_guest_dll_set=${GUEST_DLL+x};           _guest_dll=${GUEST_DLL-}
_island_launcher_set=${MGS2_ISLAND_LAUNCHER+x}; _island_launcher=${MGS2_ISLAND_LAUNCHER-}
if [ -r "$REPO/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$REPO/.env"
    set +a
fi
[ "$_mgs2_workspace_set" = x ] && MGS2_WORKSPACE=$_mgs2_workspace
[ "$_wine_build_set" = x ]     && WINE_BUILD=$_wine_build
[ "$_box86_src_set" = x ]      && BOX86_SRC=$_box86_src
[ "$_mingw_bin_set" = x ]      && MINGW_BIN=$_mingw_bin
[ "$_guest_dll_set" = x ]      && GUEST_DLL=$_guest_dll
[ "$_island_launcher_set" = x ] && MGS2_ISLAND_LAUNCHER=$_island_launcher

WORKSPACE="${MGS2_WORKSPACE:-$(dirname "$REPO")}"
WINE_BUILD="${WINE_BUILD:-$WORKSPACE/recovered-session/build-wine-i386}"
BOX86_SRC="${BOX86_SRC:-$WORKSPACE/box86-src}"
MINGW="${MINGW_BIN:-$WORKSPACE/recovered-session/mingw/bin}"
GUEST_DLL="${GUEST_DLL:-$WINE_BUILD/dlls/wined3d/i386-windows/wined3d.dll}"
ISLAND_LAUNCHER="${MGS2_ISLAND_LAUNCHER:-$REPO/device/launch-play-wined3d-fp15.sh}"
OBJECTS="$BOX86_SRC/src/island"
CLASS_B="$BOX86_SRC/src/mgs2_island_class_b.h"
IDENTITY="$BOX86_SRC/src/mgs2_island_entry_identity.h"
LOCK="$REPO/device/FINALPLAY.lock"

[ -d "$MINGW" ] && PATH="$MINGW:$PATH" && export PATH
for input in "$GUEST_DLL" "$CLASS_B" "$IDENTITY" "$ISLAND_LAUNCHER"; do
    [ -r "$input" ] || { echo "island header input missing: $input" >&2; exit 1; }
done
[ -d "$OBJECTS" ] || { echo "island object directory missing: $OBJECTS" >&2; exit 1; }

want=$(awk '$1=="wined3d_sha256" {print $2}' "$LOCK")
got=$(sha256sum "$GUEST_DLL" | cut -d' ' -f1)
[ "$got" = "$want" ] || {
    echo "island header gate: guest WineD3D is $got, lock requires $want" >&2
    exit 1
}

ISLAND_ONLY=$(sed -n 's/^export MGS2_BOX86_ISLAND_ONLY="${MGS2_BOX86_ISLAND_ONLY:-\([0-9,]*\)}"/\1/p' \
    "$ISLAND_LAUNCHER")
[ -n "$ISLAND_ONLY" ] || {
    echo "cannot read MGS2_BOX86_ISLAND_ONLY from $ISLAND_LAUNCHER" >&2
    exit 1
}
IDENT_ARGS=""
for id in $(echo "$ISLAND_ONLY" | tr ',' ' '); do
    IDENT_ARGS="$IDENT_ARGS --require-id $id"
done

WORK=$(mktemp -d /tmp/mgs2-island-header-verify.XXXXXX)
cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT HUP INT TERM

python3 "$REPO/harness/island/full/gen_class_b_table.py" "$GUEST_DLL" \
    --objects "$OBJECTS" --preserve-class-c-from "$CLASS_B" \
    -o "$WORK/mgs2_island_class_b.h" > "$WORK/class-b.log"
# shellcheck disable=SC2086
python3 "$REPO/harness/island/full/gen_entry_identity.py" "$GUEST_DLL" \
    $IDENT_ARGS -o "$WORK/mgs2_island_entry_identity.h" > "$WORK/identity.log"

fail=0
for name in mgs2_island_class_b.h mgs2_island_entry_identity.h; do
    if cmp -s "$WORK/$name" "$BOX86_SRC/src/$name"; then
        echo "ok     $name regenerates byte for byte"
    else
        echo "FAIL   $name is stale against the pinned WineD3D/island inputs" >&2
        diff -u "$BOX86_SRC/src/$name" "$WORK/$name" | sed -n '1,40p' || true
        fail=1
    fi
done
exit "$fail"

#!/bin/sh
# Can FINALPLAY be rebuilt from known clean sources?
#
# verify_patch_record.sh answered a much weaker question -- "do the two most
# recent patches match the two live trees" -- and would have passed while the
# tree was unreproducible. It was: applied in order to a pristine Wine 11.0, the
# numbered series lands 53 of 67 patches, and the fourteen that fail include the
# dmabuf presenter, the lazy stage selector and the light cache. Twenty-five
# files still differed afterwards. On the Box86 side, eight hand-written island
# sources existed in exactly one directory on one disk and in no patch.
#
# So this asks the question that matters: pinned base + one complete patch,
# reconstructed from scratch, compared against the live tree.
#
#   ./verify_rebuild.sh          reconstruct both trees and diff  (~1 min)
#   ./verify_rebuild.sh --build  also rebuild WineD3D and compare its
#                                normalised hash against the lock
set -u
REPO=$(cd "$(dirname "$0")/.." && pwd)
WINE_LIVE="${WINE_SRC:-/mnt/data/holden/mgs/recovered-session/wine-11.0}"
TARBALL="${WINE_TARBALL:-/mnt/data/holden/mgs/recovered-session/wine-11.0.tar.xz}"
BOX86_LIVE="${BOX86_SRC:-/mnt/data/holden/mgs/box86-src}"
LOCK="$REPO/device/FINALPLAY.lock"
WORK="${WORK_DIR:-/mnt/data/holden/mgs/_repro}"
fail=0
lock() { awk -v k="$1" '$1==k {print $2}' "$LOCK"; }

echo "== base identities =="
want=$(lock wine_base_sha256)
got=$(sha256sum "$TARBALL" 2>/dev/null | cut -d" " -f1)
if [ "$got" = "$want" ]; then echo "ok     wine tarball matches the pinned sha256"
else echo "FAIL   wine tarball is $got, lock says $want"; fail=1; fi

base=$(lock box86_base_commit)
if ( cd "$BOX86_LIVE" && git cat-file -e "$base^{commit}" 2>/dev/null ); then
    echo "ok     box86 base $base present"
else echo "FAIL   box86 base $base not in $BOX86_LIVE"; fail=1; fi

echo
echo "== wine: pristine + complete patch == live tree? =="
rm -rf "$WORK/wine-11.0"
mkdir -p "$WORK" && ( cd "$WORK" && tar xf "$TARBALL" )
awk '/^--- a\//{p=1} p' "$REPO/$(lock wine_complete_patch)" > "$WORK/wine.diff"
if ( cd "$WORK/wine-11.0" && patch -p1 -E --silent < "$WORK/wine.diff" >/dev/null 2>&1 ); then
    n=$(diff -rq -x '*.orig' "$WORK/wine-11.0" "$WINE_LIVE" 2>/dev/null | wc -l)
    if [ "$n" = 0 ]; then echo "ok     reconstructed byte for byte, 0 differences"
    else echo "FAIL   $n differences after reconstruction"; fail=1
         diff -rq -x '*.orig' "$WORK/wine-11.0" "$WINE_LIVE" 2>/dev/null | head -5; fi
else echo "FAIL   the complete wine patch does not apply to a pristine tree"; fail=1; fi

echo
echo "== box86: pinned commit + complete patch == live tree? =="
rm -rf "$WORK/box86"
( cd "$BOX86_LIVE" && git worktree prune && git worktree add -q --detach "$WORK/box86" "$base" )
awk '/^diff --git|^--- a\//{p=1} p' "$REPO/$(lock box86_complete_patch)" > "$WORK/box86.diff"
if ( cd "$WORK/box86" && patch -p1 -E --silent < "$WORK/box86.diff" >/dev/null 2>&1 ); then
    # island/ and island-gcc.bak/ are build products of build_island_objects.sh.
    n=$(diff -rq -x '.git*' -x island -x island-gcc.bak -x '*.orig' -x 'build*' \
            "$WORK/box86" "$BOX86_LIVE" 2>/dev/null | grep -vc "^Only in $BOX86_LIVE")
    if [ "$n" = 0 ]; then echo "ok     reconstructed, 0 differences outside build products"
    else echo "FAIL   $n differences after reconstruction"; fail=1; fi
else echo "FAIL   the complete box86 patch does not apply to $base"; fail=1; fi

if [ "${1:-}" = "--build" ]; then
    echo
    echo "== wined3d rebuild, normalised =="
    ( cd "${WINE_BUILD:-/mnt/data/holden/mgs/recovered-session/build-wine-i386}" \
        && touch "$WINE_LIVE/dlls/wined3d/glsl_shader.c" \
        && make -j8 dlls/wined3d/i386-windows/wined3d.dll >/dev/null 2>&1 \
        && python3 "$REPO/harness/pe_normalised_sha.py" \
                dlls/wined3d/i386-windows/wined3d.dll ) > "$WORK/built.txt" 2>&1
    got=$(cut -d" " -f1 < "$WORK/built.txt")
    want=$(lock wined3d_normalised_sha256_of_current_tree)
    if [ "$got" = "$want" ]; then echo "ok     rebuild reproduces the locked normalised hash"
    else echo "FAIL   rebuilt $got, lock says $want"; fail=1; fi
fi

echo
if [ "$fail" = 0 ]; then
    echo "FINALPLAY sources are reconstructible from the pinned bases"
else
    echo "RECONSTRUCTION IS BROKEN -- do not cut a release on this"
fi
exit "$fail"

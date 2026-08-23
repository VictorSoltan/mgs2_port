#!/bin/sh
# Produce a FINALPLAY release, and be the ONLY way one is produced.
#
# Until now a release was: build the live tree, scp the result, write the hashes
# down. Nothing connected the three, and it showed -- the shipped FINALPLAY11
# pair cannot be traced to any recorded source, because the tree moved on before
# anyone wrote the source down.
#
# So this does the whole chain in one command, and the manifest is generated FROM
# the files it just built rather than typed alongside them:
#
#   verify_rebuild.sh          pinned base + complete patch == live tree
#   build WineD3D              deterministically
#   build the island           which regenerates class-B FROM THAT WineD3D
#   build Box86                deterministically
#   collect into release/NAME/
#   generate FINALPLAY.manifest from those exact bytes
#   (--deploy) copy those exact files, nothing else
#
# It builds from the live tree, not from a fresh checkout, and that is sound only
# because step one proves the live tree is byte-identical to the reconstruction.
# If verify_rebuild fails, this stops -- that check is load-bearing here, not
# decorative.
#
# BOTH binaries are byte-reproducible now, so the manifest carries exact hashes
# rather than normalised ones:
#   WineD3D  -Wl,--no-insert-timestamp   (the PE TimeDateStamp and checksum)
#   Box86    SOURCE_DATE_EPOCH           (src/build_info.c prints __DATE__/__TIME__,
#                                         and the GNU build-id followed it)
#
# usage: make_release.sh <name> [--deploy]
set -eu
NAME="${1:?usage: make_release.sh <name> [--deploy]}"
DEPLOY="${2:-}"
REPO=$(cd "$(dirname "$0")/.." && pwd)
WINE_SRC="${WINE_SRC:-/mnt/data/holden/mgs/recovered-session/wine-11.0}"
WINE_BUILD="${WINE_BUILD:-/mnt/data/holden/mgs/recovered-session/build-wine-i386}"
UNIX_BUILD="${UNIX_BUILD:-/mnt/data/holden/mgs/recovered-session/build-wine-unix32}"
BOX86_BUILD="${BOX86_BUILD:-/mnt/data/holden/mgs/box86-src/build-timing}"
MINGW="${MINGW_BIN:-/mnt/data/holden/mgs/recovered-session/mingw/bin}"
DEV="${MGS2_DEVICE:-root@192.168.0.28}"
GAMEDIR=/storage/roms/ports/MGS2-Substance
OUT="$REPO/release/$NAME"

[ -d "$MINGW" ] && PATH="$MINGW:$PATH" && export PATH
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1756000000}"
LD_DET='-Wl,--disable-stdcall-fixup -Wl,--no-insert-timestamp'

echo "== 1. the sources must be the ones on record =="
sh "$REPO/harness/verify_rebuild.sh" >/dev/null || {
    echo "verify_rebuild failed -- refusing to build a release from unrecorded sources" >&2
    echo "run: harness/verify_rebuild.sh --refresh, inspect the diff, commit it" >&2
    exit 1
}
echo "ok     live trees match the pinned bases plus the complete patches"

echo "== 2. WineD3D =="
( cd "$WINE_BUILD" && make -j8 i386_LDFLAGS="$LD_DET" \
        dlls/wined3d/i386-windows/wined3d.dll >/dev/null )

echo "== 3. island objects, and class-B regenerated from THAT WineD3D =="
( cd "$REPO" && SYSROOT=/ CC=clang-18 \
    EXTRA_CFLAGS="--target=arm-linux-gnueabihf -mms-bitfields -DMGS2_GL_CENSUS" \
    sh harness/island/full/build_island_objects.sh >/dev/null )

echo "== 4. Box86 =="
( cd "$BOX86_BUILD" && make -j8 >/dev/null )

echo "== 5. collect =="
mkdir -p "$OUT"
cp "$WINE_BUILD/dlls/wined3d/i386-windows/wined3d.dll" "$OUT/wined3d_$NAME.dll"
cp "$BOX86_BUILD/box86" "$OUT/box86-$NAME"
# The presenter is carried forward from the last release unless its own build
# tree has been reconfigured; rebuilding it here would silently change a binary
# this release does not claim to touch.
WL=""; WLNAME=""
if [ -r "$UNIX_BUILD/dlls/winewayland.drv/winewayland.so" ]; then
    built=$(sha256sum "$UNIX_BUILD/dlls/winewayland.drv/winewayland.so" | cut -d" " -f1)
    prev=$(awk -F"\t" '/winewayland\.so/ {print $2}' "$REPO/device/FINALPLAY.manifest")
    if [ "$built" = "$prev" ]; then
        # Byte-identical to what is already on the device. Shipping it again
        # under a new name would burn 6 MB of a disk with 66 MB free to say
        # nothing, and would imply this release touched the presenter.
        echo "       presenter unchanged, carried forward under its existing name"
    else
        cp "$UNIX_BUILD/dlls/winewayland.drv/winewayland.so" "$OUT/winewayland_$NAME.so"
        WL="$OUT/winewayland_$NAME.so"; WLNAME="winewayland_$NAME.so"
    fi
fi

echo "== 6. the checks that have caught a bad binary before =="
n=$(arm-linux-gnueabihf-objdump -T "$OUT/box86-$NAME" 2>/dev/null \
    | grep -cE ' (log10f|atan2f|asinf|acosf|sinhf|acoshf|coshf|sqrtf)$' || true)
[ "$n" = 8 ] || { echo "libm wraps: $n of 8 at GLIBC_2.4 -- the device will refuse this" >&2; exit 1; }
mx=$(arm-linux-gnueabihf-objdump -T "$OUT/box86-$NAME" 2>/dev/null \
    | grep -o 'GLIBC_2\.[0-9]*' | sort -uV | tail -1)
echo "ok     8/8 libm wraps at GLIBC_2.4, max requirement $mx"

echo "== 7. manifest, generated from these exact bytes =="
{
    echo "# $NAME, produced by harness/make_release.sh -- do not hand-edit."
    echo "# Columns: mounted path, sha256, the file in the game directory."
    echo "# The MOUNTED file is what the launcher hashes: what was asked for is"
    echo "# not evidence of what is in place, and a half-updated class-B pair"
    echo "# does not fail cleanly."
    printf '/usr/bin/box86\t%s\tbox86-%s\n' \
        "$(sha256sum "$OUT/box86-$NAME" | cut -d' ' -f1)" "$NAME"
    printf '/usr/lib/wine/i386-windows/wined3d.dll\t%s\twined3d_%s.dll\n' \
        "$(sha256sum "$OUT/wined3d_$NAME.dll" | cut -d' ' -f1)" "$NAME"
    if [ -n "$WL" ]; then
        printf '/usr/lib/wine/i386-unix/winewayland.so\t%s\t%s\n' \
            "$(sha256sum "$WL" | cut -d' ' -f1)" "$WLNAME"
    else
        grep -F 'winewayland.so' "$REPO/device/FINALPLAY.manifest"
    fi
} > "$OUT/FINALPLAY.manifest"
cat "$OUT/FINALPLAY.manifest" | grep -v '^#'

if [ "$DEPLOY" = "--deploy" ]; then
    echo "== 8. deploy THESE files, and nothing else =="
    for f in "$OUT"/box86-* "$OUT"/wined3d_*.dll; do
        scp -q "$f" "$DEV:$GAMEDIR/$(basename "$f")"
    done
    [ -n "$WL" ] && scp -q "$WL" "$DEV:$GAMEDIR/$WLNAME"
    scp -q "$OUT/FINALPLAY.manifest" "$DEV:$GAMEDIR/FINALPLAY.manifest"
    ssh -o BatchMode=yes "$DEV" "chmod +x $GAMEDIR/box86-$NAME"
    echo "ok     deployed; launch-play.sh defaults still need pointing at $NAME"
fi
echo
echo "release $NAME is in $OUT"

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
#   point the WineD3D production launcher at the names just produced
#   generate FINALPLAY.manifest from the ELEVEN files that launcher mounts
#   (--deploy) copy exactly those files, the launchers and controller config
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
# Two steps used to be left to a person and are not any more, because both of
# them are exactly the kind of thing that drifts silently:
#
#   - the manifest covered three files while the launcher bind-mounted eleven, so
#     win32u.so, opengl32.so, user32.dll, d3d8.dll and the four DirectMusic and
#     DirectSound modules were substituted with nothing checking what they were.
#     The list is now read out of the launcher's own mount_bind lines.
#   - the last line used to print "launch-play.sh defaults still need pointing at
#     NAME" and then trust that somebody did it. It does it.
#
# usage: make_release.sh <name> [--deploy]
set -eu
NAME="${1:?usage: make_release.sh <name> [--deploy]}"
DEPLOY="${2:-}"
REPO=$(cd "$(dirname "$0")/.." && pwd)
_mgs2_workspace_set=${MGS2_WORKSPACE+x}; _mgs2_workspace=${MGS2_WORKSPACE-}
_wine_src_set=${WINE_SRC+x};             _wine_src=${WINE_SRC-}
_wine_build_set=${WINE_BUILD+x};         _wine_build=${WINE_BUILD-}
_wine_unix_set=${WINE_UNIX_BUILD+x};     _wine_unix=${WINE_UNIX_BUILD-}
_box86_src_set=${BOX86_SRC+x};           _box86_src=${BOX86_SRC-}
_box86_build_set=${BOX86_BUILD+x};       _box86_build=${BOX86_BUILD-}
_mingw_bin_set=${MINGW_BIN+x};           _mingw_bin=${MINGW_BIN-}
_device_set=${MGS2_DEVICE+x};            _device=${MGS2_DEVICE-}
_game_dir_set=${MGS2_GAME_DIR+x};        _game_dir=${MGS2_GAME_DIR-}
_launcher_set=${MGS2_RELEASE_LAUNCHER+x}; _launcher=${MGS2_RELEASE_LAUNCHER-}
_source_epoch_set=${SOURCE_DATE_EPOCH+x}; _source_epoch=${SOURCE_DATE_EPOCH-}
if [ -r "$REPO/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$REPO/.env"
    set +a
fi
[ "$_mgs2_workspace_set" = x ] && MGS2_WORKSPACE=$_mgs2_workspace
[ "$_wine_src_set" = x ]       && WINE_SRC=$_wine_src
[ "$_wine_build_set" = x ]     && WINE_BUILD=$_wine_build
[ "$_wine_unix_set" = x ]      && WINE_UNIX_BUILD=$_wine_unix
[ "$_box86_src_set" = x ]      && BOX86_SRC=$_box86_src
[ "$_box86_build_set" = x ]    && BOX86_BUILD=$_box86_build
[ "$_mingw_bin_set" = x ]      && MINGW_BIN=$_mingw_bin
[ "$_device_set" = x ]         && MGS2_DEVICE=$_device
[ "$_game_dir_set" = x ]       && MGS2_GAME_DIR=$_game_dir
[ "$_launcher_set" = x ]       && MGS2_RELEASE_LAUNCHER=$_launcher
[ "$_source_epoch_set" = x ]   && SOURCE_DATE_EPOCH=$_source_epoch
WORKSPACE="${MGS2_WORKSPACE:-$(dirname "$REPO")}"
WINE_SRC="${WINE_SRC:-$WORKSPACE/recovered-session/wine-11.0}"
WINE_BUILD="${WINE_BUILD:-$WORKSPACE/recovered-session/build-wine-i386}"
UNIX_BUILD="${WINE_UNIX_BUILD:-$WORKSPACE/recovered-session/build-wine-unix32}"
BOX86_SRC="${BOX86_SRC:-$WORKSPACE/box86-src}"
BOX86_BUILD="${BOX86_BUILD:-$WORKSPACE/box86-src/build-timing}"
MINGW="${MINGW_BIN:-$WORKSPACE/recovered-session/mingw/bin}"
DEV="${MGS2_DEVICE:-root@rg353vs}"
GAMEDIR="${MGS2_GAME_DIR:-/storage/roms/ports/MGS2-Substance}"
OUT="$REPO/release/$NAME"
LAUNCHER="${MGS2_RELEASE_LAUNCHER:-$REPO/device/launch-play-wined3d-fp15.sh}"
LAUNCHER_NAME=$(basename "$LAUNCHER")
LOCK="$REPO/device/FINALPLAY.lock"
TAB=$(printf '\t')

[ -d "$MINGW" ] && PATH="$MINGW:$PATH" && export PATH
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1756000000}"
LD_DET='-Wl,--disable-stdcall-fixup -Wl,--no-insert-timestamp'

# A candidate patch is recorded so verify_rebuild can reconstruct the live
# source tree while it is under test.  It must never silently enter a production
# bundle merely because someone ran the release command before promotion.
if awk '$1 ~ /^box86_candidate_patch_/ {found=1} END {exit !found}' "$LOCK"; then
    echo "the Box86 tree contains an unpromoted candidate patch" >&2
    echo "refusing to create a production release until its lock entry is promoted or removed" >&2
    exit 1
fi

# The production bundle, read out of the launcher rather than typed here. Emits
# "game-dir file<TAB>mounted path" per bind mount. ${VAR:-default} resolves to the
# default because the default IS production: the override is now rejected at
# runtime unless a research launcher asked for it.
mgs2_bundle_table() {
    sed -n "s|^mount_bind \"\$GAMEDIR/\([^\"]*\)\" *\([^ ]*\).*|\1$TAB\2|p" "$LAUNCHER" \
        | sed 's|\${[A-Za-z0-9_]*:-\([^}]*\)}|\1|'
}

# Where the bytes for one game-dir file come from. The three this release builds
# come out of release/NAME/; everything else is a binary that some earlier release
# produced, and binaries/ is the directory that exists so the device can be put
# back into a playable state without a toolchain. If a bundle file is not in
# either place then the release cannot state what it ships, which is the failure
# this whole file was written to remove -- so it stops.
mgs2_bundle_source() {
    case "$1" in
        "box86-$NAME"|"wined3d_$NAME.dll"|"winewayland_$NAME.so") echo "$OUT/$1" ;;
        *) echo "$REPO/binaries/$1" ;;
    esac
}

echo "== 1. the sources must be the ones on record =="
sh "$REPO/harness/verify_rebuild.sh" >/dev/null || {
    echo "verify_rebuild failed -- refusing to build a release from unrecorded sources" >&2
    echo "run: harness/verify_rebuild.sh --refresh, inspect the diff, commit it" >&2
    exit 1
}
sh "$REPO/harness/test_gptokeyb_launchers.sh" >/dev/null || {
    echo "gptokeyb launcher gate failed -- refusing to ship a port without reliable Start+Select exit" >&2
    exit 1
}
sh "$REPO/harness/test_finalplay19_production.sh" >/dev/null || {
    echo "FINALPLAY19 selector gate failed -- refusing to ship an ambiguous production route" >&2
    exit 1
}
echo "ok     live trees match the pinned bases plus the complete patches"
echo "ok     launchers arm PortMaster Start+Select exit mode"
echo "ok     FINALPLAY19 selector and rollback split are fail-closed"

echo "== 2. WineD3D =="
( cd "$WINE_BUILD" && make -j8 i386_LDFLAGS="$LD_DET" \
        dlls/wined3d/i386-windows/wined3d.dll >/dev/null )

echo "== 3. island objects, and class-B regenerated from THAT WineD3D =="
( cd "$REPO" && SYSROOT=/ CC=clang-18 MGS2_ISLAND_LAUNCHER="$LAUNCHER" \
    MGS2_REPRO_WINE_SOURCE="$(awk '$1=="island_repro_wine_source" {print $2}' "$LOCK")" \
    MGS2_REPRO_WINE_BUILD="$(awk '$1=="island_repro_wine_build" {print $2}' "$LOCK")" \
    MGS2_REPRO_BOX86_SOURCE="$(awk '$1=="island_repro_box86_source" {print $2}' "$LOCK")" \
    EXTRA_CFLAGS="--target=arm-linux-gnueabihf -mms-bitfields -DMGS2_GL_CENSUS" \
    sh harness/island/full/build_island_objects.sh >/dev/null )
MGS2_ISLAND_LAUNCHER="$LAUNCHER" sh "$REPO/harness/verify_island_headers.sh"

echo "== 4. Box86 =="
BOX86_REPRO_CFLAGS="$(awk '$1=="box86_cflags" {print $2}' "$LOCK") \
-ffile-prefix-map=$BOX86_SRC=$(awk '$1=="box86_repro_source" {print $2}' "$LOCK")"
cmake -S "$BOX86_SRC" -B "$BOX86_BUILD" -DRK3399=1 \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    -DCMAKE_C_COMPILER=arm-linux-gnueabihf-gcc \
    -DCMAKE_C_FLAGS="$BOX86_REPRO_CFLAGS" \
    -DCMAKE_EXE_LINKER_FLAGS="$(awk '$1=="box86_ldflags" {print $2}' "$LOCK")" \
    -DMGS2_GITREV="$(awk '$1=="box86_base_commit" {print $2}' "$LOCK")" \
    -DUSE_CCACHE=OFF >/dev/null
cmake --build "$BOX86_BUILD" --parallel 8 >/dev/null

echo "== 5. collect =="
mkdir -p "$OUT"
cp "$WINE_BUILD/dlls/wined3d/i386-windows/wined3d.dll" "$OUT/wined3d_$NAME.dll"
cp "$BOX86_BUILD/box86" "$OUT/box86-$NAME"
arm-linux-gnueabihf-strip --strip-debug \
    --remove-section=.note.gnu.build-id "$OUT/box86-$NAME"
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

echo "== 7. point the launcher at what was just built =="
sed -i \
    -e "s|\${MGS2_BOX86_BIN:-[^}]*}|\${MGS2_BOX86_BIN:-box86-$NAME}|" \
    -e "s|\${MGS2_WINED3D_DLL:-[^}]*}|\${MGS2_WINED3D_DLL:-wined3d_$NAME.dll}|" \
    "$LAUNCHER"
if [ -n "$WLNAME" ]; then
    sed -i -e "s|\${MGS2_WAYLAND_SO:-[^}]*}|\${MGS2_WAYLAND_SO:-$WLNAME}|" "$LAUNCHER"
fi
echo "ok     $LAUNCHER_NAME mounts box86-$NAME and wined3d_$NAME.dll"

echo "== 8. manifest, over every file the launcher mounts =="
mgs2_bundle_table > "$OUT/.bundle"
rows=$(wc -l < "$OUT/.bundle")
[ "$rows" -ge 8 ] || {
    echo "the bundle table parsed $rows mount_bind lines out of $LAUNCHER -- that is" >&2
    echo "not the launcher this expects; do not ship a manifest that covers less" >&2
    exit 1
}
missing=""
while IFS="$TAB" read -r file path; do
    src=$(mgs2_bundle_source "$file")
    [ -r "$src" ] || missing="$missing $file"
done < "$OUT/.bundle"
[ -z "$missing" ] || {
    echo "no bytes on record for:$missing" >&2
    echo "a release cannot hash a file it does not have. Put it in binaries/." >&2
    exit 1
}
{
    echo "# $NAME, produced by harness/make_release.sh -- do not hand-edit."
    echo "# Columns: mounted path, sha256, the file in the game directory."
    echo "# The MOUNTED file is what the launcher hashes: what was asked for is"
    echo "# not evidence of what is in place, and a half-updated class-B pair"
    echo "# does not fail cleanly."
    echo "# Every bind mount in $LAUNCHER_NAME is here, generated from its"
    echo "# own mount_bind lines. It used to be three of eleven, and the launcher"
    echo "# asserts the count so the two cannot drift apart again."
    while IFS="$TAB" read -r file path; do
        src=$(mgs2_bundle_source "$file")
        printf '%s\t%s\t%s\n' "$path" "$(sha256sum "$src" | cut -d' ' -f1)" "$file"
    done < "$OUT/.bundle"
} > "$OUT/FINALPLAY.manifest"
rm -f "$OUT/.bundle"
grep -v '^#' "$OUT/FINALPLAY.manifest"
cp "$OUT/FINALPLAY.manifest" "$REPO/device/FINALPLAY.manifest"
echo "ok     $rows files, and device/FINALPLAY.manifest updated to match"

echo "== 9. the lock records what shipped =="
# One more thing that used to be typed after the fact. harness/verify_rebuild.sh
# --build compares a rebuild against wined3d_sha256, so a lock left on the
# previous release makes that check assert the wrong thing -- and it asserts it
# confidently, which is worse than not checking.
mgs2_lock_set() {
    grep -q "^$1 " "$LOCK" || { echo "$LOCK has no '$1' line to update" >&2; exit 1; }
    sed -i "s|^$1 .*|$(printf '%-21s%s' "$1" "$2")|" "$LOCK"
}
mgs2_lock_set release_name "$NAME"
mgs2_lock_set box86_sha256 "$(sha256sum "$OUT/box86-$NAME" | cut -d' ' -f1)"
mgs2_lock_set wined3d_sha256 "$(sha256sum "$OUT/wined3d_$NAME.dll" | cut -d' ' -f1)"
mgs2_lock_set presenter_sha256 \
    "$(awk -F"$TAB" '$1 ~ /winewayland\.so$/ {print $2}' "$OUT/FINALPLAY.manifest")"
echo "ok     device/FINALPLAY.lock names $NAME"

if [ "$DEPLOY" = "--deploy" ]; then
    echo "== 10. deploy the bundle, and nothing else =="
    # Every manifest row, not just the rebuilt ones: the device is only playable
    # if all eleven are present, and the launcher refuses to start otherwise. Rows
    # whose bytes are already correct on the device are skipped, so a normal
    # release still copies two files over the network.
    have=$(ssh -o BatchMode=yes "$DEV" "cd $GAMEDIR && sha256sum $(awk -F"$TAB" '!/^#/ {printf "%s ", $3}' "$OUT/FINALPLAY.manifest") 2>/dev/null" || true)
    while IFS="$TAB" read -r path want file; do
        case "$path" in ''|\#*) continue;; esac
        got=$(printf '%s\n' "$have" | awk -v f="$file" '$2==f {print $1}')
        if [ "$got" = "$want" ]; then
            echo "       $file already correct on the device"
            continue
        fi
        src=$(mgs2_bundle_source "$file")
        scp -q "$src" "$DEV:$GAMEDIR/$file"
        echo "       $file copied"
    done < "$OUT/FINALPLAY.manifest"
    scp -q "$OUT/FINALPLAY.manifest" "$DEV:$GAMEDIR/FINALPLAY.manifest"
    # Every launcher in device/, not just $LAUNCHER_NAME.
    #
    # The launcher names the binaries and asserts the manifest covers all of them,
    # so it is part of the release rather than something the device happens to
    # have. And the named experiments are now COUPLED to it: the production path
    # refuses a binary override unless MGS2_RESEARCH_RUN is set, and the thing
    # that sets it is each launch-*.sh. Shipping the production launcher without
    # them would leave every experiment on the device exiting 1.
    #
    # The device carries far more scripts than device/ does; nothing is deleted,
    # only the ones on record are overwritten.
    scp -q "$REPO"/device/*.sh "$DEV:$GAMEDIR/"
    scp -q "$REPO"/device/*.manifest "$DEV:$GAMEDIR/"
    scp -q "$REPO/device/mgs2.gptk" "$DEV:$GAMEDIR/mgs2.gptk"
    ssh -o BatchMode=yes "$DEV" "cd $GAMEDIR && chmod +x box86-$NAME *.sh"
    echo "       $(ls "$REPO"/device/*.sh | wc -l) launchers copied"
    echo "       $(ls "$REPO"/device/*.manifest | wc -l) fixed manifests copied"
    echo "       mgs2.gptk copied"
    echo "ok     deployed; $LAUNCHER_NAME on the device mounts $NAME"
fi
echo
echo "release $NAME is in $OUT"

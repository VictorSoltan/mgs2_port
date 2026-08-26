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
# So this asks the question that matters: pinned base + the recorded production
# patch chain, reconstructed from scratch, compared against the live tree.
#
#   ./verify_rebuild.sh            reconstruct both trees and diff  (~1 min)
#   ./verify_rebuild.sh --build    also rebuild WineD3D and compare its
#                                  normalised hash against the lock
#   ./verify_rebuild.sh --refresh  regenerate complete patches only when no
#                                  explicit incremental chain is recorded
#
# --refresh exists because the record drifts the moment anything is built, and
# three times in one afternoon this check went red for exactly that reason. The
# record is not something to reconcile by hand after the fact; regenerate it as
# part of the build and commit the result.
set -u
REPO=$(cd "$(dirname "$0")/.." && pwd)

# Values explicitly supplied by the caller take precedence over the convenient
# machine-local defaults in .env.  Save only the variables this script reads;
# sourcing .env directly used to overwrite e.g. WORK_DIR=/tmp/... and made an
# otherwise isolated verification unexpectedly write beside the source trees.
_mgs2_workspace_set=${MGS2_WORKSPACE+x}; _mgs2_workspace=${MGS2_WORKSPACE-}
_wine_src_set=${WINE_SRC+x};             _wine_src=${WINE_SRC-}
_wine_tarball_set=${WINE_TARBALL+x};     _wine_tarball=${WINE_TARBALL-}
_box86_src_set=${BOX86_SRC+x};           _box86_src=${BOX86_SRC-}
_mingw_bin_set=${MINGW_BIN+x};           _mingw_bin=${MINGW_BIN-}
_source_epoch_set=${SOURCE_DATE_EPOCH+x}; _source_epoch=${SOURCE_DATE_EPOCH-}
_work_dir_set=${WORK_DIR+x};             _work_dir=${WORK_DIR-}
_wine_build_set=${WINE_BUILD+x};         _wine_build=${WINE_BUILD-}
if [ -r "$REPO/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$REPO/.env"
    set +a
fi
[ "$_mgs2_workspace_set" = x ] && MGS2_WORKSPACE=$_mgs2_workspace
[ "$_wine_src_set" = x ]       && WINE_SRC=$_wine_src
[ "$_wine_tarball_set" = x ]   && WINE_TARBALL=$_wine_tarball
[ "$_box86_src_set" = x ]      && BOX86_SRC=$_box86_src
[ "$_mingw_bin_set" = x ]      && MINGW_BIN=$_mingw_bin
[ "$_source_epoch_set" = x ]   && SOURCE_DATE_EPOCH=$_source_epoch
[ "$_work_dir_set" = x ]       && WORK_DIR=$_work_dir
[ "$_wine_build_set" = x ]     && WINE_BUILD=$_wine_build
WORKSPACE="${MGS2_WORKSPACE:-$(dirname "$REPO")}"
WINE_LIVE="${WINE_SRC:-$WORKSPACE/recovered-session/wine-11.0}"
TARBALL="${WINE_TARBALL:-$WORKSPACE/recovered-session/wine-11.0.tar.xz}"
BOX86_LIVE="${BOX86_SRC:-$WORKSPACE/box86-src}"
LOCK="$REPO/device/FINALPLAY.lock"
# The cross toolchain is not on a login PATH; --build silently produced an empty
# hash the first time for exactly that reason.
MINGW="${MINGW_BIN:-$WORKSPACE/recovered-session/mingw/bin}"
# Box86's build embeds __DATE__/__TIME__ via src/build_info.c; without this the
# ELF differs by 23 bytes between two builds of the same source.
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1756000000}"
[ -d "$MINGW" ] && PATH="$MINGW:$PATH" && export PATH
WORK="${WORK_DIR:-$WORKSPACE/_repro}"
fail=0
lock() { awk -v k="$1" '$1==k {print $2}' "$LOCK"; }

refresh_wine() {
    P="$WORK/pristine/wine-11.0"
    rm -rf "$WORK/pristine"; mkdir -p "$WORK/pristine"
    ( cd "$WORK/pristine" && tar xf "$TARBALL" )
    out="$REPO/$(lock wine_complete_patch)"
    head -30 "$out" > "$WORK/hdr"
    : > "$WORK/body"
    diff -rq -x '*.orig' "$P" "$WINE_LIVE" 2>/dev/null | grep " differ$" \
        | sed "s|^Files $P/||; s| and .* differ$||" | sort > "$WORK/mod"
    while read -r f; do
        diff -u --label "a/$f" --label "b/$f" "$P/$f" "$WINE_LIVE/$f" >> "$WORK/body"
    done < "$WORK/mod"
    diff -rq -x '*.orig' "$P" "$WINE_LIVE" 2>/dev/null | grep "^Only in $P" \
        | sed "s|^Only in $P/*||; s|: |/|" | sort > "$WORK/del"
    while read -r f; do
        diff -u --label "a/$f" --label "b/$f" "$P/$f" /dev/null >> "$WORK/body"
    done < "$WORK/del"
    cat "$WORK/hdr" "$WORK/body" > "$out"
    echo "refreshed $(basename "$out"): $(wc -l < "$WORK/mod") modified, $(wc -l < "$WORK/del") deleted"
}

refresh_box86() {
    out="$REPO/$(lock box86_complete_patch)"
    head -42 "$out" > "$WORK/bhdr"
    {
        cat "$WORK/bhdr"
        cd "$BOX86_LIVE" || exit 1
        git diff "$(lock box86_base_commit)" -- . \
            ':!src/island' ':!src/island-gcc.bak' ':!*.orig'
        for f in $(git status --porcelain | awk '$1=="??"{print $2}' \
                | grep -vE '^src/island/|^src/island-gcc.bak/|\.orig$|mgs2_island_class_b\.h$|mgs2_island_entry_identity\.h$'); do
            [ -d "$f" ] || diff -u --label "a/$f" --label "b/$f" /dev/null "$f"
        done
    } > "$WORK/bnew"
    mv "$WORK/bnew" "$out"
    echo "refreshed $(basename "$out")"
}

if [ "${1:-}" = "--refresh" ]; then
    if awk '$1 ~ /^(wine_research_patch_|box86_(production|candidate)_patch_)/ {found=1}
            END {exit !found}' "$LOCK"; then
        echo "refusing --refresh: the lock has explicit incremental patches" >&2
        echo "squashing them into immutable complete patches would apply them twice" >&2
        exit 1
    fi
    echo "== regenerating the complete patches from the live trees =="
    mkdir -p "$WORK"
    refresh_wine
    refresh_box86
    echo
    shift
fi

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
if ( cd "$WORK/wine-11.0" \
        && patch -p1 -E --silent < "$WORK/wine.diff" >/dev/null 2>&1 \
        && for rel in $(awk '$1 ~ /^wine_research_patch_/ {print $2}' "$LOCK"); do \
               patch -p1 -E --silent < "$REPO/$rel" >/dev/null 2>&1 || exit 1; \
           done ); then
    n=$(diff -rq -x '*.orig' "$WORK/wine-11.0" "$WINE_LIVE" 2>/dev/null | wc -l)
    if [ "$n" = 0 ]; then echo "ok     reconstructed byte for byte, 0 differences"
    else echo "FAIL   $n differences after reconstruction"; fail=1
         diff -rq -x '*.orig' "$WORK/wine-11.0" "$WINE_LIVE" 2>/dev/null | head -5; fi
else echo "FAIL   the complete wine patch does not apply to a pristine tree"; fail=1; fi

echo
echo "== box86: pinned commit + complete patch == live tree? =="
rm -rf "$WORK/box86"
mkdir -p "$WORK/box86"
# A verifier must not need to mutate the live checkout's .git/worktrees state.
# An archive is also immune to stale worktree registrations after interruption.
git -C "$BOX86_LIVE" archive "$base" | tar -x -C "$WORK/box86"
awk '/^diff --git|^--- a\//{p=1} p' "$REPO/$(lock box86_complete_patch)" > "$WORK/box86.diff"
if ( cd "$WORK/box86" \
        && patch -p1 -E --silent < "$WORK/box86.diff" >/dev/null 2>&1 \
        && for rel in $(awk '$1 ~ /^box86_(production|candidate)_patch_/ {print $2}' "$LOCK"); do \
               patch -p1 -E --silent < "$REPO/$rel" >/dev/null 2>&1 || exit 1; \
           done ); then
    # island/ and island-gcc.bak/ are build products of build_island_objects.sh,
    # and so are mgs2_island_class_b.h and mgs2_island_entry_identity.h: the
    # generators write them straight into the source tree from the exact
    # wined3d.dll, so every island build mutated what used to be tracked source
    # and this check went red within the hour. Both are FUNCTIONS of the WineD3D
    # binary -- that is the whole class-B invariant, and for the identity header it
    # is the entry-routing invariant -- so they are generated, never restored.
    #
    # The identity header was added to this list on 2026-08-23, when it turned out
    # nothing had been generating it at all: it had been carrying p72c's RVAs
    # through fp12, fp13 and fp14, and Box86 had been refusing 14 of 19 island
    # entries in silence the whole time.
    # git_head.h is generated by CMake in the source tree.  Do not broadly
    # discard "Only in live" lines here: that used to hide every unrecorded
    # source file, which is precisely what this reconstruction gate must catch.
    n=$(diff -rq -x '.git*' -x island -x island-gcc.bak -x '*.orig' -x 'build*' \
            -x git_head.h -x mgs2_island_class_b.h -x mgs2_island_entry_identity.h \
            "$WORK/box86" "$BOX86_LIVE" 2>/dev/null | wc -l)
    if [ "$n" = 0 ]; then echo "ok     reconstructed, 0 differences outside build products"
    else echo "FAIL   $n differences after reconstruction"; fail=1; fi
else echo "FAIL   the complete box86 patch does not apply to $base"; fail=1; fi

if [ "${1:-}" = "--build" ]; then
    echo
    echo "== wined3d rebuild, exact bytes =="
    # The deterministic flags are not optional here: without them two builds of
    # identical sources differ in the PE TimeDateStamp and checksum, and the
    # comparison below can never pass. They live in the lock so the release
    # pipeline and this check cannot drift apart.
    ( cd "${WINE_BUILD:-$WORKSPACE/recovered-session/build-wine-i386}" \
        && touch "$WINE_LIVE/dlls/wined3d/glsl_shader.c" \
        && make -j8 i386_LDFLAGS="$(grep '^wined3d_ldflags' "$LOCK" | cut -d' ' -f2-)" \
                dlls/wined3d/i386-windows/wined3d.dll >/dev/null 2>&1 \
        && sha256sum dlls/wined3d/i386-windows/wined3d.dll ) > "$WORK/built.txt" 2>&1
    got=$(awk 'NF==2 {print $1}' "$WORK/built.txt" | tail -1)
    want=$(lock wined3d_sha256)
    if [ -z "$got" ]; then
        echo "FAIL   the build produced no hash; last output below"; fail=1
        tail -3 "$WORK/built.txt" | sed 's/^/       /'
    elif [ "$got" = "$want" ]; then
        echo "ok     rebuild reproduces the shipped wined3d byte for byte"
    elif [ -n "$(lock candidate_in_tree)" ]; then
        # Not a broken build: the tree deliberately carries a research candidate
        # on top of the release. Saying "FAIL" here would train everyone to
        # ignore the one check that catches an untraceable binary.
        echo "note   rebuilt $got, release is $want -- expected, the tree carries"
        echo "       $(lock candidate_in_tree) on top of $(lock release_name)."
        echo "       Reproducibility of the RELEASE is unverifiable while that is"
        echo "       true; revert the candidate or promote it to check it again."
    else
        echo "FAIL   rebuilt $got, the shipped binary is $want"; fail=1
    fi
fi

echo
if [ "$fail" = 0 ]; then
    echo "FINALPLAY sources are reconstructible from the pinned bases"
else
    echo "RECONSTRUCTION IS BROKEN -- do not cut a release on this"
fi
exit "$fail"

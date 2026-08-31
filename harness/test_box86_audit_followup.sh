#!/bin/sh
# Static reconstruction gate for Box86 patch 28.
set -eu

REPO=$(cd "$(dirname "$0")/.." && pwd)
PATCH="$REPO/box86-patches/28-wayland-audit-and-reproducible-build-boundaries.patch"
SOURCE="$REPO/../box86-src"
TMP=$(mktemp -d /tmp/mgs2-box86-p28.XXXXXX)
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT HUP INT TERM

PATCH_HASH=6cd51d5a91a87eccd2447f80dddae677fd2d3af132e70f51af9a8c7003f686e0
[ "$(sha256sum "$PATCH" | cut -d' ' -f1)" = "$PATCH_HASH" ]
grep -Fq 'LISTENER_REF_PUBLISH(ref_wl_buffer_listener_##A, fct)' "$PATCH"
grep -Fq '"ppuupu", a, b, c, d, e, f' "$PATCH"
grep -Fq 'dmc3_dump_words("raster", x->pRasterizationState, 13)' "$PATCH"
grep -Fq 'file(GENERATE OUTPUT "${MGS2_GIT_HEAD}"' "$PATCH"

if [ -r "$SOURCE/CMakeLists.txt" ] && \
        [ -r "$SOURCE/src/build_info.c" ] && \
        [ -r "$SOURCE/src/wrapped/wrappedvulkan.c" ] && \
        [ -r "$SOURCE/src/wrapped/wrappedwaylandclient.c" ]; then
    mkdir -p "$TMP/tree/src/wrapped"
    cp "$SOURCE/CMakeLists.txt" "$TMP/tree/CMakeLists.txt"
    cp "$SOURCE/src/build_info.c" "$TMP/tree/src/build_info.c"
    cp "$SOURCE/src/wrapped/wrappedvulkan.c" "$TMP/tree/src/wrapped/wrappedvulkan.c"
    cp "$SOURCE/src/wrapped/wrappedwaylandclient.c" \
        "$TMP/tree/src/wrapped/wrappedwaylandclient.c"
    patch --fuzz=0 --batch -d "$TMP/tree" -p1 < "$PATCH" >/dev/null

    ! rg -q '\$\{BOX86_ROOT\}/src/git_head\.h' "$TMP/tree/CMakeLists.txt"
    grep -Fq '#include "mgs2_git_head.h"' "$TMP/tree/src/build_info.c"
    grep -Fq 'dmc3_dump_words("raster", x->pRasterizationState, 13)' \
        "$TMP/tree/src/wrapped/wrappedvulkan.c"
    PYTHONPATH="$REPO/harness" python3 - "$TMP/tree/src/wrapped/wrappedwaylandclient.c" <<'PY'
import sys
from pathlib import Path
from wayland.audit_listener_abi import box86_listeners

listeners = box86_listeners(Path(sys.argv[1]))
bad = [
    (listener, callback.name, callback.signature, callback.format_string)
    for listener, value in listeners.items()
    for callback in value.callbacks
    if callback.signature == "missing"
    or callback.format_string != callback.signature
]
if bad:
    raise SystemExit("listener parameter/RunFunctionFmt mismatch: %r" % (bad,))
PY
fi

echo "ok     Box86 p28 reconstructs with exact listener formats and bounded provenance"

#!/bin/sh
# Build the targeted client as Linux i386 for execution through Box86.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
WORKSPACE="${MGS2_WORKSPACE:-$(dirname "$REPO")}"
SYSROOT32="${MGS2_SYSROOT32:-$WORKSPACE/recovered-session/sysroot32}"
WINE_UNIX_BUILD="${WINE_UNIX_BUILD:-$WORKSPACE/recovered-session/build-wine-unix32}"
CC="${MGS2_I386_CC:-gcc}"
PROTO="$WINE_UNIX_BUILD/dlls/winewayland.drv"
GCC32="$SYSROOT32/.gcc32/usr/lib/gcc/x86_64-linux-gnu/15/32"
LIB32="$SYSROOT32/usr/lib/i386-linux-gnu"
LIB32_ALT="$SYSROOT32/usr/lib32"
OUT="${1:-$HERE/wayland-abi-client-i386}"
LIBC_DEV_DEB="${MGS2_LIBC6_DEV_I386_DEB:-$SYSROOT32/.debs/libc6-dev-i386_2.43-2ubuntu2.3_amd64.deb}"
MULTIARCH_INCLUDE="${MGS2_MULTIARCH_INCLUDE:-/usr/include/x86_64-linux-gnu}"

for input in "$SYSROOT32/usr/include/wayland-client.h" \
        "$PROTO/wlr-data-control-unstable-v1-client-protocol.h" \
        "$PROTO/wlr-data-control-unstable-v1-protocol.c" \
        "$PROTO/xdg-shell-client-protocol.h" "$PROTO/xdg-shell-protocol.c" \
        "$GCC32/libgcc.a" "$LIB32/libwayland-client.so" "$LIBC_DEV_DEB" \
        "$MULTIARCH_INCLUDE/bits/wordsize.h"; do
    [ -r "$input" ] || { echo "Wayland ABI build input missing: $input" >&2; exit 1; }
done

DEVROOT=$(mktemp -d /tmp/mgs2-libc6-dev-i386.XXXXXX)
cleanup() { rm -rf "$DEVROOT"; }
trap cleanup EXIT HUP INT TERM
dpkg-deb -x "$LIBC_DEV_DEB" "$DEVROOT"

"$CC" -m32 -std=gnu11 -O2 -Wall -Wextra -Werror -no-pie \
    -B"$GCC32/" -B"$LIB32/" -B"$LIB32_ALT/" \
    -I"$SYSROOT32/usr/include" -isystem"$DEVROOT/usr/include" \
    -isystem"$MULTIARCH_INCLUDE" -I"$PROTO" \
    "$HERE/wayland_abi_client.c" \
    "$PROTO/wlr-data-control-unstable-v1-protocol.c" \
    "$PROTO/xdg-shell-protocol.c" \
    -L"$LIB32" -L"$LIB32_ALT" -lwayland-client -o "$OUT"

file "$OUT"
sha256sum "$OUT"

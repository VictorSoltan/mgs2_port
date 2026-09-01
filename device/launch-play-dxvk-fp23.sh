#!/bin/sh
# FINALPLAY23 fixed production route: FINALPLAY22 plus the two-byte movie guard
# that closes the NULL DirectShow graph dereference measured on 2026-08-31.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
X86LIBS_MANIFEST="$HERE/FINALPLAY_RUNTIME_X86LIBS.sha256"

# winewayland.so is an i386 module under Box86, so the ARM system root cannot
# satisfy these dependencies. A dirty installation can inherit x86libs from a
# different port and hide an incomplete MGS2 bundle; fail before system mounts.
verify_x86libs() {
    checked=0
    bad=0
    [ -r "$X86LIBS_MANIFEST" ] || {
        echo "MGS2: missing x86 runtime manifest $X86LIBS_MANIFEST" >&2
        return 1
    }
    while read -r want file extra; do
        case "$want" in ''|\#*) continue;; esac
        case "$file" in ''|*/*) bad=$((bad + 1)); continue;; esac
        [ -z "${extra:-}" ] || { bad=$((bad + 1)); continue; }
        got=$(sha256sum "$HERE/x86libs/$file" 2>/dev/null | cut -d' ' -f1)
        [ "$got" = "$want" ] || {
            echo "MGS2: x86libs/$file is ${got:-missing}, expected $want" >&2
            bad=$((bad + 1))
        }
        checked=$((checked + 1))
    done < "$X86LIBS_MANIFEST"
    [ "$checked" = 10 ] || {
        echo "MGS2: x86 runtime manifest has $checked rows, expected 10" >&2
        return 1
    }
    [ "$bad" = 0 ] || {
        echo "MGS2: refusing to launch -- $bad x86 runtime dependencies differ" >&2
        return 1
    }
}

verify_x86libs
export MGS2_PRODUCTION_ROUTE=finalplay23
exec "$HERE/launch-play-dxvk-fp17.sh"

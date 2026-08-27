#!/bin/sh
# Rebuild the small AArch64 MGS2 gptokeyb helper from the pinned patched tree.
set -eu

REPO=$(cd "$(dirname "$0")/.." && pwd)
if [ -r "$REPO/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$REPO/.env"
    set +a
fi

SRC=${GPTOKEYB_SRC:?set GPTOKEYB_SRC to patched gptokeyb commit 5b1284e}
SDL_INCLUDE=${GPTOKEYB_SDL_INCLUDE:?set GPTOKEYB_SDL_INCLUDE}
SDL_CONFIG_INCLUDE=${GPTOKEYB_SDL_CONFIG_INCLUDE:?set GPTOKEYB_SDL_CONFIG_INCLUDE}
EVDEV_INCLUDE=${GPTOKEYB_LIBEVDEV_INCLUDE:?set GPTOKEYB_LIBEVDEV_INCLUDE}
TARGET_LIBS=${GPTOKEYB_DEVICE_LIBS:?set GPTOKEYB_DEVICE_LIBS}
OUT=${1:?usage: build_gptokeyb_mgs2.sh OUTPUT}
CXX=${AARCH64_CXX:-aarch64-linux-gnu-g++}
STRIP=${AARCH64_STRIP:-aarch64-linux-gnu-strip}
EXPECTED=${MGS2_GPTOKEYB_EXPECTED_SHA256:-49c782dad9da50cb0f5bb9e37821104e5089563feb24c7b0303117b75196b43a}
LOCK="$REPO/device/FOLLOWUP_CANDIDATE.lock"
lock_value() { awk -v key="$1" '$1==key {print $2}' "$LOCK"; }

[ "$(git -C "$SRC" rev-parse HEAD)" = 5b1284e1502548d476aa38e5979b0a8f48cb7b94 ] || {
    echo "gptokeyb source is not pinned commit 5b1284e" >&2
    exit 1
}
grep -Fq 'immediate_start_back && kill_mode' "$SRC/src/keyboard.cpp" || {
    echo "gptokeyb patch 01 is not applied" >&2
    exit 1
}
[ -r "$SDL_INCLUDE/SDL.h" ]
[ -r "$SDL_CONFIG_INCLUDE/SDL2/_real_SDL_config.h" ]
[ -r "$EVDEV_INCLUDE/libevdev-1.0/libevdev/libevdev.h" ]
[ -r "$TARGET_LIBS/libSDL2.so" ]
[ -r "$TARGET_LIBS/libstdc++.so" ]

case $("$CXX" --version | sed -n '1p') in
    *"$(lock_value gptokeyb_cxx_version)"*) ;;
    *) echo "unexpected AArch64 compiler version" >&2; exit 1 ;;
esac
case $("$STRIP" --version | sed -n '1p') in
    *"$(lock_value gptokeyb_strip_version)"*) ;;
    *) echo "unexpected AArch64 strip version" >&2; exit 1 ;;
esac
for item in \
    "libSDL2.so:gptokeyb_target_sdl2_sha256" \
    "libstdc++.so:gptokeyb_target_libstdcxx_sha256"; do
    file=${item%%:*}
    key=${item##*:}
    got=$(sha256sum "$TARGET_LIBS/$file" | cut -d' ' -f1)
    [ "$got" = "$(lock_value "$key")" ] || {
        echo "$file is $got, expected $(lock_value "$key")" >&2
        exit 1
    }
done

TMP=$(mktemp -d /tmp/mgs2-gptokeyb-build.XXXXXX)
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT HUP INT TERM

"$CXX" -O2 -fno-stack-protector -std=c++11 \
    -I"$SDL_INCLUDE" -I"$SDL_CONFIG_INCLUDE" \
    -I"$EVDEV_INCLUDE" -I"$EVDEV_INCLUDE/libevdev-1.0" \
    "$SRC/src/analog.cpp" \
    "$SRC/src/config.cpp" \
    "$SRC/src/input.cpp" \
    "$SRC/src/output_uinput.cpp" \
    "$SRC/src/xbox360.cpp" \
    "$SRC/src/keyboard.cpp" \
    "$SRC/src/util.cpp" \
    "$SRC/src/gptokeyb.cpp" \
    -L"$TARGET_LIBS" -Wl,--allow-shlib-undefined -lSDL2 \
    -o "$TMP/gptokeyb"
"$STRIP" --strip-unneeded -o "$OUT" "$TMP/gptokeyb"

got=$(sha256sum "$OUT" | cut -d' ' -f1)
if [ -n "$EXPECTED" ] && [ "$got" != "$EXPECTED" ]; then
    echo "gptokeyb rebuild is $got, expected $EXPECTED" >&2
    exit 1
fi
echo "$got  $OUT"

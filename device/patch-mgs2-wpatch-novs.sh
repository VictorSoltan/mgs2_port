#!/bin/sh
# Build the exact FINALPLAY21 game-image view from a legally installed copy.
# The source game executable is never overwritten; the launcher bind-mounts the
# verified temporary result and removes it during cleanup.
set -eu

INPUT=${1:?usage: patch-mgs2-wpatch-novs.sh INPUT OUTPUT}
OUTPUT=${2:?usage: patch-mgs2-wpatch-novs.sh INPUT OUTPUT}

ORIGINAL_SHA256=29759e6f06eaea4d61bb6aef5a5ef45a936eac1e76fa0c3471cf4f231349aaa0
PATCHED_SHA256=6686b3fa6484a0609fbe65be46f34cbba941b18e252db7bbb83d457153ba31d6
PATCH_OFFSET=4860234
ORIGINAL_BYTE=02

if [ "$INPUT" -ef "$OUTPUT" ]; then
    echo "MGS2: refusing to patch the installed game EXE in place" >&2
    exit 1
fi
case "$OUTPUT" in
    /tmp/mgs2-wpatch-novs.*) ;;
    *)
        echo "MGS2: refusing output outside the private /tmp launch name" >&2
        exit 1
        ;;
esac
if [ -L "$OUTPUT" ]; then
    echo "MGS2: refusing a symlink output" >&2
    exit 1
fi

got=$(sha256sum "$INPUT" 2>/dev/null | cut -d' ' -f1)
if [ "$got" != "$ORIGINAL_SHA256" ]; then
    echo "MGS2: game EXE is ${got:-missing}, FINALPLAY21 expects $ORIGINAL_SHA256" >&2
    exit 1
fi

got_byte=$(od -An -tx1 -j "$PATCH_OFFSET" -N 1 "$INPUT" 2>/dev/null | tr -d ' \n')
if [ "$got_byte" != "$ORIGINAL_BYTE" ]; then
    echo "MGS2: game EXE byte at 0x4a294a is ${got_byte:-missing}, expected $ORIGINAL_BYTE" >&2
    exit 1
fi

cp "$INPUT" "$OUTPUT"
printf '\000' | dd of="$OUTPUT" bs=1 seek="$PATCH_OFFSET" conv=notrunc 2>/dev/null
chmod 0755 "$OUTPUT"

got=$(sha256sum "$OUTPUT" 2>/dev/null | cut -d' ' -f1)
if [ "$got" != "$PATCHED_SHA256" ]; then
    echo "MGS2: generated game EXE is ${got:-missing}, expected $PATCHED_SHA256" >&2
    exit 1
fi

echo "MGS2: generated exact FINALPLAY21 water-path game EXE $got" >&2

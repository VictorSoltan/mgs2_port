#!/bin/sh
# Build the bounded wpatch candidate from a legally installed MGS2 copy.
#
# The original game image is never changed.  This helper accepts one locked
# input hash, writes only to the launcher's private /tmp name, verifies every
# original instruction/cave byte, and checks the complete generated image.
set -eu

INPUT=${1:?usage: patch-mgs2-wpatch-isolated.sh INPUT OUTPUT}
OUTPUT=${2:?usage: patch-mgs2-wpatch-isolated.sh INPUT OUTPUT}

ORIGINAL_SHA256=29759e6f06eaea4d61bb6aef5a5ef45a936eac1e76fa0c3471cf4f231349aaa0
PATCHED_SHA256=e4a54598cefa2f7d19e02aa519e030b21a19424f163e3fdeebe32bb111cde1ce

FLAG_OFFSET=4860234
TEXT_VSIZE_OFFSET=528
TAIL_JUMP_OFFSET=5008401
SELECT_CALL_OFFSET=5008657
TAIL_CAVE_OFFSET=5617120
SELECT_CAVE_OFFSET=5617168

expect_bytes() {
    offset=$1
    count=$2
    expected=$3
    got=$(od -An -v -tx1 -j "$offset" -N "$count" "$INPUT" 2>/dev/null | tr -d ' \n')
    if [ "$got" != "$expected" ]; then
        echo "MGS2: game EXE bytes at offset $offset are ${got:-missing}, expected $expected" >&2
        exit 1
    fi
}

if [ "$INPUT" -ef "$OUTPUT" ]; then
    echo "MGS2: refusing to patch the installed game EXE in place" >&2
    exit 1
fi
case "$OUTPUT" in
    /tmp/mgs2-wpatch-isolated.*) ;;
    *)
        echo "MGS2: refusing output outside the private /tmp candidate name" >&2
        exit 1
        ;;
esac
if [ -L "$OUTPUT" ]; then
    echo "MGS2: refusing a symlink output" >&2
    exit 1
fi

got=$(sha256sum "$INPUT" 2>/dev/null | cut -d' ' -f1)
if [ "$got" != "$ORIGINAL_SHA256" ]; then
    echo "MGS2: game EXE is ${got:-missing}, candidate expects $ORIGINAL_SHA256" >&2
    exit 1
fi

expect_bytes "$FLAG_OFFSET" 1 02
expect_bytes "$TEXT_VSIZE_OFFSET" 4 d3a55500
expect_bytes "$TAIL_JUMP_OFFSET" 5 e9fab1b3ff
expect_bytes "$SELECT_CALL_OFFSET" 5 a900000200
expect_bytes "$TAIL_CAVE_OFFSET" 20 0000000000000000000000000000000000000000
expect_bytes "$SELECT_CAVE_OFFSET" 12 000000000000000000000000

cp "$INPUT" "$OUTPUT"

# Keep FINALPLAY21's fixed-function water fallback.
printf '\000' | dd of="$OUTPUT" bs=1 seek="$FLAG_OFFSET" conv=notrunc 2>/dev/null

# Include the two checked trampolines in .text's executable virtual extent.  The
# new end remains below the section's locked 0x55b000-byte raw size and below
# the following .rdata RVA.
printf '\040\246\125\000' | \
    dd of="$OUTPUT" bs=1 seek="$TEXT_VSIZE_OFFSET" conv=notrunc 2>/dev/null

# Route the unconditional PluginActor tail jump through a trampoline that
# returns fixed-function lighting to the engine's disabled baseline and then
# preserves the original tail jump into DG_CloseDmaTask.  Do not attach this to
# the preceding texture-address helper: that call is state-cache conditional.
printf '\351\312\111\011\000' | \
    dd of="$OUTPUT" bs=1 seek="$TAIL_JUMP_OFFSET" conv=notrunc 2>/dev/null
printf '\152\000\150\211\000\000\000\350\364\265\364\377\203\304\010\351\034\150\252\377' | \
    dd of="$OUTPUT" bs=1 seek="$TAIL_CAVE_OFFSET" conv=notrunc 2>/dev/null

# Preserve the vertex-shader path for the sole non-water external wpatch
# consumer (the no-wrap IPU movie panel).  The helper returns flags to the
# existing conditional branch, so the original global shader flag still wins.
printf '\350\372\110\011\000' | \
    dd of="$OUTPUT" bs=1 seek="$SELECT_CALL_OFFSET" conv=notrunc 2>/dev/null
printf '\251\000\000\002\000\165\004\366\106\113\200\303' | \
    dd of="$OUTPUT" bs=1 seek="$SELECT_CAVE_OFFSET" conv=notrunc 2>/dev/null

chmod 0755 "$OUTPUT"

got=$(sha256sum "$OUTPUT" 2>/dev/null | cut -d' ' -f1)
if [ "$got" != "$PATCHED_SHA256" ]; then
    echo "MGS2: generated game EXE is ${got:-missing}, expected $PATCHED_SHA256" >&2
    exit 1
fi

echo "MGS2: generated exact isolated-wpatch candidate $got" >&2

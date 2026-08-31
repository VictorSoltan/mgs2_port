#!/bin/sh
# Build the bounded wpatch state-ownership candidate from a legal MGS2 copy.
#
# This retains candidate 02's water/IPU split and lighting cleanup, makes the
# fixed-function wpatch path select COUNT2 before uploading its UV matrix, and
# keeps that path selected if device creation falls back to software VP.
# The installed game image is never changed.
set -eu

INPUT=${1:?usage: patch-mgs2-wpatch-state-owned.sh INPUT OUTPUT}
OUTPUT=${2:?usage: patch-mgs2-wpatch-state-owned.sh INPUT OUTPUT}

ORIGINAL_SHA256=29759e6f06eaea4d61bb6aef5a5ef45a936eac1e76fa0c3471cf4f231349aaa0
PATCHED_SHA256=d902ee4398b77653674943f097f79e103d1aa0bc93ce825c0cb0c3d3522b9f88

SOFTWARE_FLAG_OFFSET=4860090
FLAG_OFFSET=4860234
TEXT_VSIZE_OFFSET=528
TAIL_JUMP_OFFSET=5008401
SELECT_CALL_OFFSET=5008657
STATE_CALL_OFFSET=5009385
TAIL_CAVE_OFFSET=5617120
SELECT_CAVE_OFFSET=5617168
STATE_CAVE_OFFSET=5617184

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
    /tmp/mgs2-wpatch-state.*) ;;
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

expect_bytes "$SOFTWARE_FLAG_OFFSET" 1 02
expect_bytes "$FLAG_OFFSET" 1 02
expect_bytes "$TEXT_VSIZE_OFFSET" 4 d3a55500
expect_bytes "$TAIL_JUMP_OFFSET" 5 e9fab1b3ff
expect_bytes "$SELECT_CALL_OFFSET" 5 a900000200
expect_bytes "$STATE_CALL_OFFSET" 5 e87cee0300
expect_bytes "$TAIL_CAVE_OFFSET" 20 0000000000000000000000000000000000000000
expect_bytes "$SELECT_CAVE_OFFSET" 12 000000000000000000000000
expect_bytes "$STATE_CAVE_OFFSET" 32 0000000000000000000000000000000000000000000000000000000000000000

cp "$INPUT" "$OUTPUT"

# Candidate 02: fixed-function water, shader path for the no-wrap IPU panel,
# and an unconditional lighting reset at the plugin tail. The second byte is
# the same patch-renderer flag in the software-VP startup branch.
printf '\000' | dd of="$OUTPUT" bs=1 seek="$SOFTWARE_FLAG_OFFSET" conv=notrunc 2>/dev/null
printf '\000' | dd of="$OUTPUT" bs=1 seek="$FLAG_OFFSET" conv=notrunc 2>/dev/null
printf '\100\246\125\000' | \
    dd of="$OUTPUT" bs=1 seek="$TEXT_VSIZE_OFFSET" conv=notrunc 2>/dev/null
printf '\351\312\111\011\000' | \
    dd of="$OUTPUT" bs=1 seek="$TAIL_JUMP_OFFSET" conv=notrunc 2>/dev/null
printf '\152\000\150\211\000\000\000\350\364\265\364\377\203\304\010\351\034\150\252\377' | \
    dd of="$OUTPUT" bs=1 seek="$TAIL_CAVE_OFFSET" conv=notrunc 2>/dev/null
printf '\350\372\110\011\000' | \
    dd of="$OUTPUT" bs=1 seek="$SELECT_CALL_OFFSET" conv=notrunc 2>/dev/null
printf '\251\000\000\002\000\165\004\366\106\113\200\303' | \
    dd of="$OUTPUT" bs=1 seek="$SELECT_CAVE_OFFSET" conv=notrunc 2>/dev/null

# Replace the non-VS branch's first matrix call with a call to a small tail
# trampoline. It latches stage 0 to D3DTTFF_COUNT2 through the game's cached
# wrapper, then jumps to the original matrix function with the original stack
# and return address intact.
printf '\350\062\106\011\000' | \
    dd of="$OUTPUT" bs=1 seek="$STATE_CALL_OFFSET" conv=notrunc 2>/dev/null
printf '\152\002\152\030\152\000\350\305\243\364\377\203\304\014\351\067\250\372\377' | \
    dd of="$OUTPUT" bs=1 seek="$STATE_CAVE_OFFSET" conv=notrunc 2>/dev/null

chmod 0755 "$OUTPUT"

got=$(sha256sum "$OUTPUT" 2>/dev/null | cut -d' ' -f1)
if [ "$got" != "$PATCHED_SHA256" ]; then
    echo "MGS2: generated game EXE is ${got:-missing}, expected $PATCHED_SHA256" >&2
    exit 1
fi

echo "MGS2: generated exact state-owned wpatch candidate $got" >&2

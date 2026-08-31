#!/bin/sh
# Build the exact FINALPLAY23 state-owned wpatch view from a legal MGS2 copy.
#
# This is FINALPLAY22 plus one closed defect. FINALPLAY22 and every earlier
# route inherit an EXE whose DirectShow COM initialisation at VA 0x00878FE0 was
# stubbed with `ret` (offset 4689888, `81` of `sub esp,0x4E0` replaced by `c3`),
# so `CoCreateInstance(CLSID_FilterGraph, IID_IGraphBuilder, &0x00A53A98)` never
# runs and every global in 0x00A53A7C..0x00A53AAC stays zero for the life of the
# process. The in-memory movie consumer at 0x00888803 is still reached, and its
# wrapper at 0x0087A7C0 dereferences that never-initialised state with no null
# check. Measured on device 2026-08-31 03:04: `wine: Unhandled page fault on
# read access to 00000000 at address 0087AE0F`, wine exit 5.
#
# The two edits below close the wrapper and the clock helper it calls. Both
# sites are unreachable-or-fatal while the init stub is in place, so this
# removes a guaranteed crash and changes nothing that ever worked: no movie
# played before this patch either.
#
# It otherwise retains the water/IPU split and lighting cleanup, makes the
# fixed-function wpatch path select COUNT2 before uploading its UV matrix, and
# keeps that path selected if device creation falls back to software VP. The
# installed game image is never changed.
set -eu

INPUT=${1:?usage: patch-mgs2-wpatch-finalplay23.sh INPUT OUTPUT}
OUTPUT=${2:?usage: patch-mgs2-wpatch-finalplay23.sh INPUT OUTPUT}

ORIGINAL_SHA256=29759e6f06eaea4d61bb6aef5a5ef45a936eac1e76fa0c3471cf4f231349aaa0
PATCHED_SHA256=d6b81257a82348299675adf863c9ad884c68c438b032fe20a75f18a094d29cd5

SOFTWARE_FLAG_OFFSET=4860090
FLAG_OFFSET=4860234
TEXT_VSIZE_OFFSET=528
TAIL_JUMP_OFFSET=5008401
SELECT_CALL_OFFSET=5008657
STATE_CALL_OFFSET=5009385
TAIL_CAVE_OFFSET=5617120
SELECT_CAVE_OFFSET=5617168
STATE_CAVE_OFFSET=5617184
MOVIE_WRAPPER_OFFSET=4696000
MOVIE_CLOCK_OFFSET=4697600

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
    /tmp/mgs2-wpatch-finalplay23.*) ;;
    *)
        echo "MGS2: refusing output outside the private /tmp FINALPLAY23 name" >&2
        exit 1
        ;;
esac
if [ -L "$OUTPUT" ]; then
    echo "MGS2: refusing a symlink output" >&2
    exit 1
fi

got=$(sha256sum "$INPUT" 2>/dev/null | cut -d' ' -f1)
if [ "$got" != "$ORIGINAL_SHA256" ]; then
    echo "MGS2: game EXE is ${got:-missing}, FINALPLAY23 expects $ORIGINAL_SHA256" >&2
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
expect_bytes "$MOVIE_WRAPPER_OFFSET" 1 53
expect_bytes "$MOVIE_CLOCK_OFFSET" 1 51

cp "$INPUT" "$OUTPUT"

# Fixed-function water, shader path for the no-wrap IPU panel, and an
# unconditional lighting reset at the plugin tail. The second byte is the same
# patch-renderer flag in the software-VP startup branch.
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

# Close the two unguarded dereferences of the never-initialised DirectShow
# state. `push ebx` -> `ret` at the movie play/update wrapper (VA 0x0087A7C0)
# and `push ecx` -> `ret` at the one-time SetSyncSource helper it calls
# (VA 0x0087AE00). Both are cdecl with no argument cleanup of their own and no
# push before the replaced byte, so returning at entry leaves the stack
# balanced and the caller's `add esp,0x1c` still correct. The wrapper's return
# value in eax is discarded at its only call site, 0x00888808.
printf '\303' | \
    dd of="$OUTPUT" bs=1 seek="$MOVIE_WRAPPER_OFFSET" conv=notrunc 2>/dev/null
printf '\303' | \
    dd of="$OUTPUT" bs=1 seek="$MOVIE_CLOCK_OFFSET" conv=notrunc 2>/dev/null

chmod 0755 "$OUTPUT"

got=$(sha256sum "$OUTPUT" 2>/dev/null | cut -d' ' -f1)
if [ "$got" != "$PATCHED_SHA256" ]; then
    echo "MGS2: generated game EXE is ${got:-missing}, expected $PATCHED_SHA256" >&2
    exit 1
fi

echo "MGS2: generated exact FINALPLAY23 game EXE $got" >&2

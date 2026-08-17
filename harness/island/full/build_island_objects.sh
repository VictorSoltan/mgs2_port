#!/bin/sh
# Build the 32 native ARM WineD3D island objects that Box86 links in, together
# with the per-translation-unit native-target registries.
#
# BUILD.md described this as a shell snippet and nothing checked it in, so the
# exact flags had to be reconstructed once. Keep the recipe here instead.
#
# The objects go straight into box86-src/src/island/, where patch 09's
# CMakeLists glob picks them up as prebuilt EXTERNAL_OBJECTs.
#
# -fshort-wchar is required: without it four files fail on L"..." literals,
# because Windows WCHAR is two bytes and Linux wchar_t is four.
#
# TWO PASSES, AND WHY IT IS NOT A FIXPOINT
# ========================================
#
# Pass 1 compiles the sources as-is, purely so the generator can read which
# names each translation unit defines. Pass 2 recompiles each source with its
# generated registry fragment appended, which takes the address of every
# mappable function -- 916 of them are `static` and are not reachable from any
# other TU, which is why the fragment has to be inside the TU rather than in one
# central file.
#
# This terminates by construction and must not be confused with the
# rebuild-until-stable loop it replaced. Symbol IDs depend on function NAMES
# only. Appending the registry adds data objects and changes no name, so pass 2
# cannot invalidate the input pass 1 produced. The old loop existed because the
# table stored ADDRESSES read back out of the linked binary, which every rebuild
# moved; nothing in this build reads an address any more.
set -eu

WINE_SRC="${WINE_SRC:-/mnt/data/holden/mgs/recovered-session/wine-11.0}"
WINE_BUILD="${WINE_BUILD:-/mnt/data/holden/mgs/recovered-session/build-wine-i386}"
BOX86_SRC="${BOX86_SRC:-/mnt/data/holden/mgs/box86-src}"
SYSROOT="${SYSROOT:?set SYSROOT to the extracted armhf cross sysroot}"
CC="${CC:-arm-linux-gnueabihf-gcc}"
OUT="$BOX86_SRC/src/island"
REG="$OUT/registry"
HERE=$(cd "$(dirname "$0")" && pwd)

# The i386 DLL supplies the guest RVAs. The opengl32 DLL must be the one MOUNTED
# ON THE DEVICE: the reference wineprefix copy shares an ImageBase and has
# different RVAs, which is what made the first class-C failure silent.
GUEST_DLL="${GUEST_DLL:-$WINE_BUILD/dlls/wined3d/i386-windows/wined3d.dll}"
GUEST_GL="${GUEST_GL:-}"

INC="-I$WINE_BUILD/dlls/wined3d -I$WINE_SRC/dlls/wined3d -I$WINE_SRC/include \
     -I$WINE_SRC/include/msvcrt -I$WINE_SRC/libs/vkd3d/include \
     -I$WINE_SRC/libs/vkd3d/include/private -I$WINE_BUILD/include"
DEF="-DMGS2_RELEASE -DMGS2_FINALPLAY -D_UCRT -D__WINESRC__ -DMGS2_ISLAND_ARM \
     -DWINE_NO_TRACE_MSGS -DWINE_NO_DEBUG_MSGS"

mkdir -p "$OUT" "$REG"

# ---- pass 1: names only -----------------------------------------------------
n=0
for f in "$WINE_SRC"/dlls/wined3d/*.c; do
    o="$OUT/$(basename "$f" .c).o"
    # shellcheck disable=SC2086
    "$CC" --sysroot="$SYSROOT" -O2 -fshort-wchar -c "$f" $INC $DEF -o "$o"
    n=$((n + 1))
done
echo "pass 1: built $n island objects (names only)"

# ---- generate the table and the per-TU registries ---------------------------
rm -f "$REG"/*.h
GEN_ARGS="$GUEST_DLL --objects $OUT --registry $REG -o $BOX86_SRC/src/mgs2_island_class_b.h"
[ -n "$GUEST_GL" ] && GEN_ARGS="$GEN_ARGS --opengl32 $GUEST_GL"
# shellcheck disable=SC2086
python3 "$HERE/gen_class_b_table.py" $GEN_ARGS

# ---- pass 2: same sources, with the registry appended -----------------------
# The wrapper includes the original source so the registry sees its statics.
# Nothing in the Wine tree is edited for this.
WRAP="$OUT/wrappers"
mkdir -p "$WRAP"
rm -f "$WRAP"/*.c
n=0
for f in "$WINE_SRC"/dlls/wined3d/*.c; do
    b=$(basename "$f" .c)
    w="$WRAP/$b.c"
    {
        printf '/* Generated wrapper: the source, then its native-target registry.\n'
        printf ' * The registry must be inside this TU -- most of its targets are static. */\n'
        printf '#include "%s"\n' "$f"
        [ -r "$REG/$b.h" ] && printf '#include "%s"\n' "$REG/$b.h"
    } > "$w"
    # shellcheck disable=SC2086
    "$CC" --sysroot="$SYSROOT" -O2 -fshort-wchar -c "$w" $INC $DEF -I"$OUT" -o "$OUT/$b.o"
    n=$((n + 1))
done
echo "pass 2: rebuilt $n island objects with registries"

# ---- control checks ---------------------------------------------------------
# The island entry marker is an x86 NOP; in the ARM build its bytes would sit in
# the instruction stream, where 0x474d decodes as `bx r9`. MGS2_ISLAND_MARK is
# #ifdef __i386__ so nothing should match here. If this fires, every marked
# function branches to a garbage address before running any of its own body --
# which is exactly what the 2026-08-15 crash was.
if grep -rlq $'\x0f\x1f\x84\x00\x4d\x47\x53' "$OUT"/*.o 2>/dev/null; then
    echo "FAIL: x86 island marker bytes present in the ARM objects" >&2
    exit 1
fi
echo "control check passed: no x86 marker bytes in the ARM objects"

# Every ID the generator emitted must actually be registered by an object, or
# the resolver would call through a null. Counting here rather than trusting the
# generator's own arithmetic: the section is what the linker will see.
want=$(sed -n 's/^#define MGS2_NATIVE_ID_COUNT \([0-9]*\)$/\1/p' \
    "$BOX86_SRC/src/mgs2_island_class_b.h")
got=$(python3 - "$OUT" <<'PYEOF'
import glob, os, subprocess, sys
# Section size / sizeof(struct mgs2_native_reg). Read from the objects rather
# than trusting the generator's own arithmetic: the section is what the linker
# will actually see. (awk's strtonum is a gawk extension; this box has mawk.)
total = 0
for obj in sorted(glob.glob(os.path.join(sys.argv[1], "*.o"))):
    out = subprocess.run(["readelf", "-SW", obj], capture_output=True, text=True).stdout
    for line in out.splitlines():
        f = line.replace("[", " ").replace("]", " ").split()
        if "mgs2_native_ids" in f:
            i = f.index("mgs2_native_ids")
            total += int(f[i + 4], 16)
print(total // 8)
PYEOF
)
if [ "$want" != "$got" ]; then
    echo "FAIL: $want native IDs generated but $got registered in the objects" >&2
    exit 1
fi
echo "control check passed: all $want native IDs registered by the objects"

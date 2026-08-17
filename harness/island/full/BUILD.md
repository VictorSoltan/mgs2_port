# Building the full native ARM WineD3D island

The slice-1 method -- extracting a function and its helpers by hand -- does not
scale and gave a badly wrong cost estimate (415 functions, 15,000 lines). The
compiler does the port instead. 28 of WineD3D's 32 source files build for armhf
essentially unmodified:

```sh
INC="-Idlls/wined3d -I../wine-11.0/dlls/wined3d -I../wine-11.0/include \
     -I../wine-11.0/include/msvcrt -I../wine-11.0/libs/vkd3d/include \
     -I../wine-11.0/libs/vkd3d/include/private -Iinclude"
DEF="-DMGS2_RELEASE -DMGS2_FINALPLAY -D_UCRT -D__WINESRC__ \
     -DWINE_NO_TRACE_MSGS -DWINE_NO_DEBUG_MSGS"
for f in ../wine-11.0/dlls/wined3d/*.c; do
    arm-linux-gnueabihf-gcc --sysroot="$SYSROOT" -O2 -c "$f" $INC $DEF \
        -o "armobj/$(basename "$f" .c).o"
done
arm-linux-gnueabihf-gcc --sysroot="$SYSROOT" -shared \
    -o libmgs2island.so armobj/*.o island_stubs.o -lm
```

Add `-fshort-wchar` and **all 32 build**. The four that first failed had one
error each, always the same: `L"..."` gives a four-byte `wchar_t` on Linux while
Windows `WCHAR` is two. Nothing was entangled with Win32 after all; that reading
came from not looking at the error text.

The recipe above now lives in `build_island_objects.sh`, with a control check.
Use it rather than retyping the snippet: the flags had to be reconstructed once
already, and the check it runs is not optional.

## The marker is an x86 instruction. Do not compile it for ARM

This is the trap that cost the branch its first live run. The entry marker Box86
matches in the guest prologue is an eight-byte x86 NOP written as a bare `.byte`
directive. `.byte` emits into whatever section it is in, so building these same
sources for armhf put those eight bytes in the **ARM instruction stream** of all
37 marked functions. As Thumb, `474d` is `bx r9`: every native island function
branched to whatever that register held, before running one instruction of its
own body. The symptom was an unhandled illegal instruction at a guest address
that belongs to a Box86 bridge, with no stub ever reached -- see section 17 of
`docs/briefs/MGS2_REINFORCEMENT_FRAME_BUDGET_2026-08-14.md`.

`MGS2_ISLAND_MARK()` (patch 48) emits the bytes only under `#ifdef __i386__`.
The i386 output is unchanged, verified by compiling both forms and comparing.
`build_island_objects.sh` greps the finished objects for the marker bytes and
fails if any survive; keep that check whenever the marker changes.

## NtCurrentTeb() is not portable to this island

The second trap, and it is the same shape as the first: an i386 idiom that still
compiles for ARM and means something else. `NtCurrentTeb()` is `mov fs:0x18` on
i386 -- Wine's TEB, in a segment Box86 maintains per guest thread. winnt.h's ARM
branch reads the coprocessor thread pointer instead, which belongs to the *host*
thread. `wined3d_from_cs()` identifies the caller that way, so every island
function that checks its thread read arbitrary memory; entry 3 faulted on the
Win32 thread id at TEB+0x24 with perfectly valid arguments.

Patch 49 adds an `MGS2_ISLAND_ARM` branch calling `mgs2_island_teb()`, which
Box86 implements as the current emu's FS base plus 0x18. The build script
defines `MGS2_ISLAND_ARM`; the i386 build never takes that branch. Check with
`objdump -d box86 | grep -c 'cr13, cr0, {2}'` -- it must be zero.

Assume the same class of problem for anything else that reads a register, a
segment or a thread-local by architecture convention.

## Which stubs are real code, and which must stay stubs

`mgs2_island_natives.c` implements the seven entry points the routed closure
actually reaches: `mgs2_island_teb`, `_assert`, `_fdclass`, the four
`__wine_dbg_*`/`__stdio_common_vsprintf` debug and formatting entries. ERR is
*not* compiled out of the island -- its channel test is a direct flags read --
so those are reached in normal operation, and with abort stubs no entry could be
measured at all.

`_recalloc` stays an abort stub on purpose. It would resize a block whose
allocator is unknown: a WineD3D structure reaching the island may have been
allocated by the guest msvcrt, and handing a guest heap pointer to the host
realloc corrupts both heaps. The same caution applies to any `free`/`realloc`
the island might reach; `harness/island/full/island_reach.py` reports allocator
symbols in an entry's closure.

Regenerating the stub file must exclude exactly the names `mgs2_island_natives.c`
defines, or the link fails on duplicate symbols. Both files carry the list.

`island_stubs.c` is generated from the undefined-symbol list: 226 Win32, GDI and
setup entry points the island links against but must never call. Each aborts with
its own name rather than returning a plausible value, so a mis-routed call fails
loudly. Regenerate it whenever the object set changes; do not hand-edit.

Result: 894 KB, containing `draw_primitive`, `shader_glsl_load_constants`,
`shader_glsl_apply_draw_state`, `mgs2_batch_flush` and
`wined3d_ffp_get_fs_settings` as native ARM code.

## Where the boundary has to be

Not where the hot functions are. The island duplicates 140 writable file-scope
variables, so any cut that leaves one of them reachable from both sides is
wrong -- two copies of `mgs2_batch` would diverge and corrupt the frame.

Taking the five hot functions and closing over both calls and shared globals to a
fixpoint gives 588 of 1422 functions and 146 internal entry points, and it drags
in the shader-generation machinery (`shader_addline` alone has 89 external
callers). That is a fault line through the middle of WineD3D, not an island.

The coherent cut is the module's own public API: `wined3d.spec` exports 329
`wined3d_*` functions and d3d8 uses about 146 of them. Same bridge count as the
internal cut, but a documented, stable boundary, and it puts *all* of WineD3D
native rather than part. The reverse direction is small: `wined3d_parent_ops` and
`wined3d_device_parent_ops` together are about seven callbacks back into x86.

```text
forward bridges   d3d8 -> native wined3d      ~146 exported functions
reverse callbacks native wined3d -> d3d8      ~7 vtable entries
abort stubs       Win32/GDI setup surface      226
removes                                        21.16 ms/frame of translated work
ceiling                                        +2.4 to +5.7 fps from 13.85
```

Every link in the chain is proven: the source compiles, the layouts match, live
guest pointers read identically, an in-process bridge produces byte-identical
results, routed work measurably leaves the emulated path, and native code sees
the same GL context. What is left is building 146 bridges with correct ABI, seven
reverse callbacks, and keeping context creation on the x86 side.

## External surface of the complete module

With all 32 objects, 3667 symbols are defined internally and 160 remain external:

```text
Win32 / GDI / NT     137
vkd3d (unused)        10   stub
GL / EGL / WGL         9   native, already in the process
Wine debug             4   stub
```

The 137 look fatal until you ask where they are reachable from. Closing over the
draw path -- `draw_primitive`, `shader_glsl_load_constants`,
`shader_glsl_apply_draw_state`, `mgs2_batch_flush`, `wined3d_cs_exec_draw_one`
and slice 1 -- gives 44 functions, and exactly **three** of the 137 are reachable:

```text
QueryPerformanceCounter   clock_gettime natively
_assert                   a native abort
_fdclass                  CRT float classification, native
```

All three are trivially provided natively. The other 134 sit in context creation,
swapchain, window and cursor code, which stays on the x86 side where it belongs.

So the hot path needs no reverse bridge into Wine per frame -- the property the
whole idea depends on, and the one that would have killed it. It is measured, not
assumed.

## The bridge table generates itself

The boundary is 146 exported functions, and hand-writing 146 ABI signatures is
how you get a crash six weeks later. `gen_bridge_table.py` derives them from the
prototypes in `include/wine/wined3d.h`: it reads `wined3d.spec` for the 372
exports, intersects with what d3d8 actually calls, and emits box86 `GO(name, sig)`
lines. All 146 resolve; none is missing, and the script exits non-zero if any
ever is.

```text
wined3d.spec exports          372
used by d3d8                  146
signatures derived            146
missing                         0
```

`wined3d_bridge_private.h` is the generated table. Regenerate it whenever Wine or
the d3d8 side changes; do not hand-edit.

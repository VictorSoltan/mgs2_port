# MGS2 RG353VS — reinforcement frame budget (2026-08-14)

Status: this is the 14 August accounting of the dense reinforcement fight. Its
batching and present conclusions remain current, but its native-island and
production-state conclusions are historical. The island follow-up first shipped
entry 10 and then entry 4; read
`MGS2_ISLAND_BATCH_STATE_MEASURED_2026-08-16d.md` for the current boundary.
Production is FINALPLAY6: island31 + p56, 17 entries armed, with entry 10
measured at about +2.1 fps and entry 4 at +0.899 fps median (+4.8%).

This brief supersedes the intermediate packet-break brief of the same date. It
also corrects four things in the earlier record, including one wrong reading
made during this same investigation, and one ceiling that was too low. Sections
6 and 10 are the important parts.

## 1. Result

| candidate | decision | evidence |
|---|---|---|
| Adjacent exact-state draw coalescing | **NO-GO** | 0.18 safely mergeable GL submissions/frame against a 50/frame floor fixed before the measurement |
| Indexed draw merging | **NO-GO** | `source_indexed = 0`, third independent capture |
| Non-indexed triangle-list batching | **NO-GO** | at most 6.3 submissions/frame; 98.0% of source draws are already strips |
| Native ARM replacement of a game function | **NO-GO** | whole game EXE is 12.60% of user cycles, largest single function 1.48% |
| Overlapping the present round-trip | **NO-GO** | already built as `MGS2_GL_ASYNC` and measured in brief 28: GPU wait 31.7 -> 1.6 ms, fps unchanged, one frame of added latency |
| Native ARM bridge for isolated WineD3D blocks | **SUPERSEDED** | later same-process A/B measured native entry 10 at -8.87 ms/frame and entry 4 at -2.680 ms/frame; the working island carries their complete native closures and explicit guest-held state/dispatch bridges |
| Coarse native ARM renderer executor | **PARTIALLY SHIPPED** | the full-thread port remains rejected, but the entry-routed island mechanism is production for 17 proved entries; see the 16 August island briefs |
| `GL_KHR_parallel_shader_compile` | absent | not in the deployed libmali blob |

That was the honest boundary on 14 August. The later island measurements moved
it by instrumenting one entry inside one continuing process; do not reuse the
older cross-run null as evidence against those measured gains.

## 2. The captures

Two live dense fights, driven manually by the player, who confirmed
reinforcements were entering before each interval began. One game process each,
mounted DLL byte-compared against the requested file.

```text
p38 capture     PID 31918   census interval 44.50 s   82.777 -> 82.222 C
                wined3d_p38_packet_break_census.dll
                sha256 3cae068327a0ae32c1e6260d99cb8820cd11f8dbb35886adce07c39d3e15c62c
                600 frames / 40.687 s = 14.75 fps
                clock caveat: the cap was held at 1104000-1608000 for the whole
                fight, NOT 1992000

p39 capture     PID 53416   40 s   81.36 C CPU / 75.70 C GPU
                wined3d_p39_wait_census.dll
                sha256 f0be65815ea13d294a44cf43c4471378e59d31577b79b7ecd1c6db5818add008
                72.22 ms/frame = 13.8 fps
                clock held: scaling_max_freq 1992000 for all 40 samples

both            BOX86_MUTEX_ALIGNED=1
                MGS2_BOX86_NATIVE_AABB=0
                MGS2_BOX86_NATIVE_DSOUND_FIR=1
                MGS2_REINFORCEMENT_CENSUS=1
                libmali.so.1.10.0
                sha256 2b39f4315eec0545e21e5c5498f9125d01e35d7cad4a49a447f002dd7b5e0cbb
```

Both are inside the known 11.9--19.5 fps reinforcement band, so this is the real
scene and not a quiet substitute.

## 3. Where the 72.22 ms frame goes

Patch 39 splits the CSMT consumer into exec / present / idle with two clock
reads per present and two per idle episode, none per command packet.

```text
frame                   72.22 ms          13.8 fps

  exec                  51.57 ms  71.4%   translated WineD3D work
  present               20.40 ms  28.2%   GPU round-trip, blocked
  idle                   0.25 ms   0.4%   empty queue
                        --------
                        71.97 ms  99.7% of the frame

spin iterations         42.8 / frame      negligible
wait_event calls        0.02 / frame
CS packets            1418.8 / frame
present duration      16-32 ms 414 | 8-16 ms 218 | 32-64 ms 61 | 4-8 ms 7
wined3d_cs occupancy    0.681 core        consistent with 51.57/72.22 = 0.714
game main worker        0.625 core
GPU frequency           800 MHz 24.5% | at or below 400 MHz 64.7%
```

Three things follow.

**The renderer thread is the critical path.** It owns 99.7% of the frame
wall-clock.

**There is no producer starvation.** The consumer waits 0.25 ms per frame on an
empty queue and blocks on the event 0.02 times per frame. The game thread keeps
the queue full, so no amount of game-side or Box86-side work removal can move
the frame.

**The 20.4 ms present is latency, not GPU throughput.** The GPU sits at its
maximum frequency for only 24.5% of the fight and at or below half of it for
64.7%. A throughput-bound GPU would be pinned high by its ondemand governor.

## 4. Why 911 source draws become 247 GL submissions

Patch 38 attributes every real closure of the pending batch to its immediate
cause, and decides at each closure whether the two adjacent real draws were
issued under an identical effective rendering state. Each non-draw CS opcode is
compared field by field against the state the consumer already holds; nothing is
hashed, so nothing can collide, and any opcode without an exact comparison plus
every resource mutation counts as a real change. The result can only
under-report opportunity, never over-report it.

```text
displayed frames                ~656 (frame log)
CS presents                      641
source draws                  597485      911.4 / displayed frame
source indexed                     0
producer batch packets        164045      250.1 / displayed frame
final GL submissions          162177      247.2 / displayed frame
  glDrawArrays                 68872      105.0 / displayed frame
  synthetic EBO                93305      142.2 / displayed frame
```

228.5 real closures per displayed frame. Every one of them is the CSMT hard
barrier in `mgs2_cs_dispatch()`; the draw-time dirty-state check closed **zero**
batches, because a state opcode always closes the batch before it can set a
dirty bit. Four closures in the whole interval hit the 256-strip limit.

```text
closure cause                       /frame    share
SET_STREAM_SOURCES                   133.3     58.4%
SET_BLEND_STATE                       43.0     18.8%
SET_RENDER_STATE                      19.3      8.5%
SET_EXTRA_PS_ARGS                     12.5      5.5%
UPDATE_SUB_RESOURCE                    8.4      3.7%
SET_RASTERIZER_STATE                   4.9      2.1%
SET_LIGHT                              4.5      2.0%
SET_VIEWPORTS                          1.2
batch limit (256 strips)               0.006

boundary_state_different       149781     228.32 / frame
boundary_state_equal              126       0.19 / frame
boundary_mergeable                117       0.18 / frame
```

`boundary_mergeable` additionally requires the next draw to be a non-indexed
triangle strip and the closed batch to be under the limit -- exactly what an
adjacent exact-state coalescer could remove without reordering or changing
geometry, shaders, depth or blending. **0.18 per frame against a 50/frame
floor.**

The dominant boundary is the vertex-buffer pointer change, and it is real: of
115,994 `SET_STREAM_SOURCES` commands, **zero** were redundant. The two known
ways of crossing it -- packed source VBO and the persistent arena with WORLD lift
-- were both built previously and both measured negative (brief 41 section 8:
slower plus a kernel OOM; brief 42 section 8: `projected_cross = 0`).

Batch lengths and primitive mix:

```text
closed batch length     /frame        source draws by primitive
1                        86.7         trianglestrip   584539   98.0%
2                        39.3         lines             7413    1.2%
3-4                      64.9         trianglelist      4110    0.7%
5-8                      23.2         trianglefan        357
9-16                      6.4         linestrip           26
17-32                     4.8
33-63                     3.0         batcher bypass    18.1 / frame
64+                       0.2
```

Two honest limits on the mergeable number:

- `PUSH_CONSTANTS` carries no payload by the time the consumer sees it, so it is
  counted as not comparable, i.e. always a real change. It occurs 196.3 times
  per frame and marks most runs different by construction. This does not rescue
  the conclusion: `SET_STREAM_SOURCES` alone closes 133.3 batches/frame, it *is*
  exactly comparable, and none of its occurrences were redundant.
- The independent full-snapshot cross-check did not run. `verify_checked = 2343`
  and all 2343 were `verify_unavailable`, because the FFP push-constant buffer is
  larger than the 1024-byte snapshot slot the build reserves and the code refused
  to compare a truncated buffer rather than claim completeness. A future p38b
  needs a larger slot; it cannot change a verdict sitting 280x below threshold.

One separate observation, recorded and not acted on: every `SET_SHADER` command
is a no-op, 32,912 of 32,912, because the fixed-function path pushes NULL over
NULL 50 times a frame. It closes no batch and removes no submission, so it is
not a frame-rate candidate.

## 5. The game worker is not the target

Re-analysed offline from the existing verified reinforcement capture
(`logs/rg353vs/reinforcement-guestmap-20260814/`, 12,271 samples, guest map
16,244/262,144 records, `overflow=0`). No new device time was needed.

The archive's `harness/box86_guest_profile.py` counts sample lines, and this
capture's periods span 1 to 1.19 million cycles, so the counts were recomputed
weighted by period with `harness/box86_cycle_profile.py`. The ordering is
unchanged. Shares are of total user cycles.

```text
1.481%  rva 0x4b9d30 +0x127f   SSE 4x4 matrix transform + min/max AABB accumulate
0.658%  rva 0x4b62d0 +0x329    mixed SSE/x87
0.594%  rva 0x4be790 +0xfc     grid -> 24-byte vertex + 16-bit strip index builder
0.577%  rva 0x524f64 +0x27     _ftol (fstcw/fistp/fldcw), leaf, called everywhere
0.419%  rva 0x4cc9e0 +0x1e6    mixed SSE/x87
0.412%  rva 0x4a1eaf +0x64     frame limiter: QueryPerformanceCounter -> Sleep()
0.387%  rva 0x4bb1e0 +0xb2     scene object list walk
0.318%  rva 0x4a1de1 +0x9d     frame limiter: elapsed-tick catch-up loop

whole game EXE = 12.60% of user cycles
```

A perfect, zero-cost replacement of the best candidate removes 1.48% of user
cycles. This is the "smeared over dozens of functions" case, so **NO-GO**.

Two of the top eight blocks are not work at all. `0x4a1dd0`, `0x4a1ea0` and
`0x4a311a` are the game's own frame limiter, identified from the import table:
`ds:0x95c09c` is `KERNEL32!QueryPerformanceCounter` and `ds:0x95c214` is
`KERNEL32!Sleep`. `0x4a311a` is its spin loop:

```asm
8a3110: call 0x8a1ea0        ; QPC, compute remainder, _ftol, Sleep(ms)
8a3115: call 0x8a1dd0        ; QPC, count elapsed fixed ticks
8a311a: mov  edx, ds:0xf8684c
8a3120: sub  edx, ds:0xf86850
8a3126: cmp  eax, edx
8a3128: jb   0x8a3110        ; spin until the tick target is reached
```

With its share of `_ftol` this cluster is roughly 1.3--1.8% of user cycles of the
game waiting, so earlier readings overstated how busy the game worker is.

A separate observation from the same profile: 34.0% of the game main worker's
cycles are inside `/usr/bin/box86` itself rather than translated code -- roughly
10.6% of all user cycles, split across `DynaRun`, `fpu_fxsave`, the `Run`/`Run64`
/`Run0F` interpreter and the `DBGetBlock`/`hasAlternate` block lookup. It is
seven times the biggest game function and it is real. Section 3 makes it moot as
a frame-rate target: the renderer consumer is starved for 0.25 ms per frame, so
the game thread is not setting the frame. It is recorded as a measurement, not a
candidate.

## 6. Four corrections to the record

**One CS Present per displayed frame, not two.** The submit-census and mutex
briefs of the same date normalised per-frame rates by assuming WineD3D emits two
CS Present commands per displayed frame. This capture counted 641 CS presents
against ~656 displayed frames over the same 44.50 s. The ratio is 1.0. **Every
per-frame figure derived from the 2:1 assumption is twice too large**: the
earlier "1905 source draws and 506 GL submissions per displayed frame" becomes
952 and 253, which is what section 4 measures directly at 911 and 247. Future
reports must take the denominator from the external frame log.

**The fixed 1992 MHz baseline was not held, and the launcher is not the reason.**
In the p38 fight the cap sat at 1416000 (4 s), 1608000 (22 s), 1800000 (18 s) and
1992000 (1 s) out of 45 samples, mean 1676267 kHz at 82.22 C. This was initially
attributed to the launcher's own thermal ladder; that attribution is wrong. With
no game and no launcher running, a write of 1992000 at 82.2 C still read back as
1416000, while at 78.1 C the same write held and the `cpufreq-cpu0` cooling
device reported `cur_state = 0`. The cap is stepped by the **kernel thermal
governor** through that cooling device, which has seven states. `MGS2_FREQ_STEPS`
and the launcher's emergency stop are separate mechanisms and were not the cause
here.

The consequence stands either way: same-session A/B comparisons survive, because
both arms drift together; absolute fps figures and cross-session comparisons do
not. The p39 fight did hold 1992000 for all 40 samples, so section 3 is clean.

**An intermediate reading in this investigation was wrong and is retracted.**
`harness/frame_limit_probe.py` measured `wined3d_cs` at 0.671 of a core and the
whole process at 1.94 of four, and the conclusion drawn was that nothing was
saturated and the frame was lost to unexplained waiting. That is wrong. The
probe measures CPU occupancy, and the present handler blocks rather than spins,
so 28% of the frame was invisible to it. Patch 39 shows the renderer thread
accounts for 99.7% of the frame. The probe itself is sound and its clock and
thermal readings stand; the inference did not.

**The present overlap was proposed here and it was already closed.** On the
arithmetic 72.22 - 20.40 = 51.6 ms it was recommended as a candidate worth about
+5.6 fps. That arithmetic assumes the present block is additive to execution. It
is not. The overlap already exists as `MGS2_GL_ASYNC`, implemented in the
presenter and off by default, and brief 28 measured it: GPU wait in the critical
path fell from 10.5--31.7 ms to 1.5--1.74 ms while fps stayed at 9.5--17.2, plus
one frame of added latency the owner could feel. The mechanism works completely
and the frame does not shrink. The candidate was closed before and stays closed;
the ceiling quoted here was produced by a wrong model, not by a measurement.

## 7. Shader prewarm

`GL_KHR_parallel_shader_compile` is **not present** in the deployed blob. A
string scan of `/usr/lib32/libmali.so.1.10.0` finds no
`GL_KHR_parallel_shader_compile`, no `glMaxShaderCompilerThreadsKHR` and no
`GL_COMPLETION_STATUS_KHR`, while 29 other `GL_KHR_*` names are present. A driver
cannot advertise an extension whose name string it does not contain, so this is
conclusive in the negative without a live context.

Plain same-context prewarm of exact known FFP sources is therefore the only
route, which the plan already allowed. It is independent of frame rate, is not
implemented here, and remains the one open renderer-adjacent item.

## 8. What is left

```text
reduce total work                closed; every census in this round is negative
overlap CPU and GPU              closed; built, measured, zero gain, one frame of latency
native ARM renderer executor     OPEN; the ABI objection is refuted, see section 10
raise the thermal ceiling        physical cooling, not code
```

There is a hard floor that no amount of removed x86 can cross:

```text
22.00 ms/frame   libmali inside exec -- already native ARM
20.40 ms/frame   present -- GPU round-trip
--------
42.40 ms of the 72.22 ms frame
```

30 fps is 33.3 ms per frame, which is below that floor. With this driver and this
present path, 30 fps in this scene is arithmetically unreachable regardless of
how much emulation is removed.

CPU and GPU share one thermal budget on this SoC. The existing dead-end entry
records it exactly: pinning the GPU governor to 800 MHz halves the GPU wait and
drops the CPU cap to 816 kHz, a net loss. Neither side can be given headroom
without taking it from the other at 82 C.

Anything materially larger requires relaxing a constraint that is currently
fixed -- render resolution, geometry or effects. That is a separate decision
about a visible trade, and this brief does not make it.

## 9. Artefacts

```text
wine-patches/38-reinforcement-packet-break-census.patch   applies on p37 with -F0, round-tripped
wine-patches/39-reinforcement-wait-census.patch           applies on p38 with -F0
binaries/wined3d_p38_packet_break_census.dll              3cae0683...3e15c62c, deterministic rebuild
binaries/wined3d_p39_wait_census.dll                      f0be6581...18add008
harness/reinforcement_break_census.py                     p38 reader, symbol VMA 0x101d30c0
harness/reinforcement_wait_census.py                      p39 reader, symbol VMA 0x101d30c0
harness/frame_limit_probe.py                              external 1 Hz clock/thermal/GPU/thread sampler
harness/box86_cycle_profile.py                            cycle-weighted guest profile
logs/rg353vs/manual-reinforcement-p38-20260814/           p38 before/after/diff, frame log
logs/rg353vs/p39-wait-census-20260814/                    p39 before/after, paired frame-limit probe
```

Both censuses are memory-only, allocate nothing, write no log from a render,
mixer or driver thread, and are off unless `MGS2_REINFORCEMENT_CENSUS=1`. Each is
read externally through `/proc/<pid>/mem`. `frame_limit_probe.py` never reads
`wchan` and never attaches to the process.

Note that each build moves the other censuses' symbols. In the p38 build
`mgs2_reinforcement_submit_census` is at VMA `0x101d34c0`, not `0x101d10c0`; pass
`--symbol-vma` explicitly to the p37 reader.

No frame-rate improvement is claimed or implied anywhere in this brief. Every
number is either from the device or labelled as a ceiling.

## 10. The native renderer island: NO-GO retracted

This section previously declared the island closed. That was wrong on two counts,
both found by review and then settled by measurement. The correction is recorded
in full because the wrong reasoning is the more instructive half.

### 10.1 The ceiling was too low

The +0.9 fps first quoted was the ceiling for replacing the top ten *named* guest
blocks, 17% of the renderer thread. The whole translated portion is 41%.
Decomposing the 51.57 ms exec by the verified per-thread module split:

```text
42.67%   22.00 ms/frame   libmali, already native ARM
41.04%   21.16 ms/frame   translated x86            <- the real target
14.91%    7.69 ms/frame   libc and unresolved
 1.38%    0.71 ms/frame   box86 runtime
```

Removing all 21.16 ms gives 51.06 ms = 19.6 fps; at a native cost of a third to a
half of dynarec, 17.2 to 16.2 fps, from 13.85. The correct ceiling is **+2.4 to
+5.7 fps**.

### 10.2 "Smeared across functions" was an artefact of a flat profile

The guest profiler attributes samples to the block containing the current guest
address, which is **self time**. Concluding from a flat self-time list that there
is no connected subgraph does not follow, and was the error.

Resolving *every* wined3d guest block to a symbol and summing the connected draw
tree gives the inclusive figure:

```text
3.49%  draw_primitive                            <- self time of the single function
1.31%  shader_glsl_load_constants
0.76%  wined3d_cs_exec_draw_one
0.53%  shader_glsl_apply_draw_state
0.48%  mgs2_resolve_separable
0.47%  wined3d_ffp_get_fs_settings
0.45%  mgs2_batch_flush
0.40%  wined3d_buffer_load
0.39%  context_gl_load_shader_resources
0.39%  wined3d_context_gl_activate
0.35%  ffp_blitter_clear_rendertargets
0.32%  wined3d_context_gl_acquire
0.31%  wined3d_buffer_gl_prepare_location
0.31%  set_glsl_shader_program
0.28%  wined3d_rendertarget_view_load_location
-----
10.23% of JIT samples: the connected draw subtree, 2.9x draw_primitive alone
```

Excluded as not part of the tree: `wined3d_cs_run` (1.07%, the spin loop),
`wined3d_device_apply_stateblock` and `wined3d_mutex_lock` (game thread), and
`mgs2_p38_state_op` (this brief's own census overhead). The subtree reconciles
with the fight capture's 41.04% translated share, i.e. the 21.16 ms above. It is
one connected tree, not scattered leaves. That is an argument *for* an island,
not against one.

### 10.3 The object-model objection is measured false

The stated reason for closing the branch was that the hot functions issue GL
calls and mutate live WineD3D objects, so a native helper would have to reproduce
WineD3D's object model. That is an assumption, not a measurement, and it is the
wrong one. Box86 already passes pointers from x86 code into native armhf
libraries; the real question is whether the two compilers lay the structures out
the same way.

Two independent checks say they do.

First, from the DWARF of the shipped i386 build, 19 of 21 hot-path structures --
including `wined3d_state` (7276 bytes), `wined3d_context`, `wined3d_device`,
`wined3d_buffer`, `wined3d_texture`, `wined3d_resource`, `wined3d_shader`,
`wined3d_stream_info` and `ffp_frag_settings` -- contain no 8-byte scalar at all,
so no alignment-driven divergence is possible. The two exceptions are
`wined3d_bo_gl.command_fence_id` (one `uint64_t`) and one apparent hit in
`wined3d_gl_info` that resolves to a function-pointer typedef, four bytes on both.

Second, and decisively, the same DWARF shows **40 bitfield members** across five
hot-path structures, and bitfield packing is exactly where i386 and AAPCS are
documented to be able to differ. `harness/wined3d_abi_layout_probe.c` carries the
bitfield sequences verbatim from `wined3d_private.h` plus a mixed 64-bit case,
and is compiled by both toolchains that matter -- `i686-w64-mingw32-gcc`, which
builds the DLL that runs today, and `arm-linux-gnueabihf-gcc`:

```text
field                               i386 PE    armhf
ctx_bits sizeof                          32       32
ctx_bits alignof                          4        4
ctx_bits .constant_update_mask           16       16
ctx_bits .numbered_array_mask            20       20
ctx_bits .viewport_count                 24       24
ctx_bits .scissor_rect_count             28       28
ffp_bits sizeof                          56       56
ffp_bits .fog                            48       48
si_bits  sizeof                          72       72
si_bits  .use_map                        64       64
mixed    sizeof                          40       40
mixed    alignof                          8        8
mixed    .q (uint64)                     24       24

mismatches: 0 of 17
```

**Zero mismatches, bitfields and the 64-bit case included**, for the shapes that
probe carries.

To remove the hand-copy caveat, `harness/wined3d_dwarf_struct_probe.py`
reconstructs the *real* structures mechanically from the shipped build's DWARF
and compiles them with both toolchains. It carries a self-check: a
`_Static_assert` that every reconstruction reproduces the shipped `sizeof`, so a
lossy probe fails the build instead of producing a confident wrong answer.

That self-check earned its place. The first two attempts failed it -- names
printed by objdump as `(indirect string, offset: 0x322): flags` were being
dropped, and, more seriously, the DWARF of six objects had been concatenated
into one dump while DIE offsets are numbered per compilation unit, so the type
map was silently cross-linked. Both attempts produced member-offset
"differences" that were artefacts of the reconstruction, not ABI divergence.
Generating from a single translation unit, with the assertions in place, both
faults disappear.

The final run reconstructs all eight structures exactly -- `wined3d_state` 7276
bytes, `wined3d_device` 4884, `wined3d_context` 1020, matching the shipped DWARF
-- and compares 175 sizes, alignments and member offsets between
`i686-w64-mingw32-gcc`, which builds the DLL running today, and
`arm-linux-gnueabihf-gcc`:

```text
struct                        i386 PE    armhf
wined3d_state sizeof             7276     7276
wined3d_context sizeof           1020     1020
wined3d_device sizeof            4884     4884
wined3d_buffer sizeof             216      216
wined3d_texture sizeof            292      292
wined3d_resource sizeof           168      168
wined3d_stream_info sizeof        908      908
all alignments                      4        4

MISMATCHES: 0 of 175
```

**Zero mismatches on the real structures, with the self-check passing.**

### 10.4 A real divergence does exist, and it is fixable

The "0 of 175" above is true but too narrow, and continuing past it found the
exception. Those 175 probes came from `cs.c`'s compilation unit, which has no
complete `ffp_frag_settings`. Generating from `utils.c`, which does, the two
toolchains disagree:

```text
struct                    i386 PE   armhf
color_fixup_desc                2       2
texture_stage_op               16      12   <<<
ffp_frag_settings             132     100   <<<
```

The cause is bitfield allocation, exactly where the ABIs are documented to be
free to differ. `texture_stage_op` places `unsigned` bitfields after a nested
two-byte struct; MS rules start a new allocation unit, GCC's ARM rules pack.
mingw builds the shipping DLL with `-mms-bitfields`, its default -- compiling the
same header with `-mno-ms-bitfields` reproduces armhf's 12 and 100 exactly. ARM
GCC cannot be told to match: `-mms-bitfields` does not exist there and
`__attribute__((ms_struct))` is accepted and ignored.

So the layout must not be left to either compiler.
`harness/wined3d_exact_layout_gen.py` places every member at the byte offset the
shipping build actually uses, with explicit padding, and turns each bitfield run
into a raw storage unit plus shift/mask accessors computed from the DWARF bit
positions -- which removes bitfield ABI from the question entirely. Every
placement is checked by a static assertion, so a wrong header fails the build.

Over the hot-path set -- 40 structures, 369 assertions on sizes and member
offsets, 164 generated bitfield accessors:

```text
armhf   assertion failures: 0
i386 PE assertion failures: 0
```

Both toolchains now produce the shipping layout, `texture_stage_op` at 16 and
`ffp_frag_settings` at 132 included.

A native armhf helper can therefore read and write the same live WineD3D objects
through raw pointers, using a generated header rather than a hand-written one.
It does not need a second object model, and the structural objection that closed
this branch is measured false -- with the qualification that the header must be
generated, because a naive recompilation of the real declarations would silently
lay two of these structures out differently.

### 10.5 What is and is not proved

Proved: the draw work is one connected subtree; its removal ceiling is +2.4 to
+5.7 fps; ARM reads a live `wined3d_state` identically to x86 in the running
process; and a generated layout-exact header gives both toolchains the shipping
layout across 369 assertions, including the two structures that diverge when the
declarations are compiled naively.

Not proved, and required before any port: that a live pointer
handed from x86 to armhf reads back identically in the running process, which
needs a Box86 patch and the Box86 source tree is not in this workspace; and that the 42.40 ms of `libmali` plus present is really an
independent floor rather than a dependency that relocates, which the
`MGS2_GL_ASYNC` result -- wait removed, frame unchanged -- says it may not be.

The next three steps, in order, are the live pointer checksum proof, the
async wait-relocation census, and only then a narrow island with a fallback.

Artefacts: `logs/rg353vs/renderer-symbol-profile-20260814/`,
`harness/wined3d_abi_layout_probe.c`.

Two related claims were checked and remain negative:

- **Generic Box86 to libmali bridge cost.** On `wined3d_cs` the whole of
  `/usr/bin/box86` is 1.38% of the thread, 0.71 ms/frame, and the marshalling
  thunks themselves are about 0.04 ms/frame. A specialised GLES fast bridge has
  nothing to recover.
- **`EGL_KHR_create_context_no_error` / `GL_KHR_no_error`.** Absent from both the
  32-bit and the 64-bit `libmali` blob.

## 11. The native ARM island runs

Slice 1 of the island exists, executes inside the game process on live WineD3D
objects, and reproduces the x86 result exactly.

```text
island calls   2760
  match        2760
  mismatch        0
```

`wined3d_ffp_get_fs_settings()` and its eight helpers are compiled by
`arm-linux-gnueabihf-gcc` **from the shipping WineD3D source, unmodified**, against
declarations generated from that same build's DWARF. Box86 recognises
`mgs2_island_ffp_target()` by an exact prologue whose eight-byte multi-byte NOP
spells "MGS2" -- link-address independent -- and routes it to the native code.
The renderer keeps calling the x86 function itself, so no pixel depends on the
island during validation; once per present both run into pre-zeroed buffers and
the 132 bytes are compared in process.

The first run reported 5 mismatches in 2071 calls, all at byte 26, which is the
alignment hole inside the second `texture_stage_op`. Neither implementation is
obliged to write it, and the x86 side was leaving stack residue there. Zeroing
both buffers before the call removed it; the fields themselves never disagreed.

Two things this does and does not show. It does show that a connected piece of
WineD3D can be compiled for ARM, handed live guest pointers, and produce
identical results -- the mechanism the whole island rests on. It does **not**
show a speed-up: with patch 42 both paths run, deliberately, so this slice costs
more than it saves. Slice 1 is 0.47% of the renderer thread; the point of it is
the mechanism, not the prize. Making it pay means routing the renderer through
the island and extending it to the connected draw subtree, which is where the
21.16 ms sits.

```text
box86-patches/07-native-island-ffp.patch     bridge, MGS2_BOX86_ISLAND_FFP=1, off by default
wine-patches/42-island-ffp-target.patch      target plus in-process differential validation
harness/island/island_slice1.c               the ARM slice, 1063 lines
harness/island/mgs2_island_ffp.c             as compiled into Box86
harness/island/island_read.py                counter reader
harness/wined3d_exact_layout_gen.py          layout-exact declaration generator
binaries/wined3d_p42_island_target.dll       c176e6fc...5827fd24
box86-island1 (device)                       d30dacc3...0dd37cb1
```

Production is untouched: the launcher still selects `box86-native-dsound-fir1`
and p32, and both island switches default to off.

## 12. The renderer now runs through the island

Patch 43 points `glsl_shader.c`'s fixed-function path at the island instead of
the x86 function. A/B on one scene, one build, only the switch changed:

```text
function                        island off   island on
wined3d_ffp_get_fs_settings         63            0     samples
                                  0.35%        0.00%    of translated work

draw_primitive                     552          540     unchanged within noise
shader_glsl_apply_draw_state        92          102
shader_glsl_load_constants         201          218
jit samples total                17789        17200
```

The function is **gone** from translated code: the renderer's calls land in
native ARM. Nothing around it moved, which is what a correct routing looks like.

The size is 0.35% of translated work, about 0.07 ms of a 72 ms frame -- far below
what a frame-rate measurement can resolve, and no frame-rate change is claimed.
What is established is the full chain: shipping source compiled for ARM,
layout-exact declarations, in-process bridge, byte-identical results on 2760 live
calls, and now measured removal of the work from the emulated path.

Extending the same chain across the connected draw subtree is where the 21.16 ms
sits, and it is the only remaining step between this and the +2.4 to +5.7 fps
ceiling. The pieces it needs -- generator, bridge, validation harness, A/B method
-- all exist and have been exercised.

Artefacts: `wine-patches/43-island-route-renderer.patch`,
`binaries/wined3d_p43_island_routed.dll`, `logs/rg353vs/island-ab-20260815/`.

## 13. Extending the island: what the profile allows, and the wall it hits

With slice 1 working, the question is which function goes next. The A/B profile
ranks the renderer thread's translated work:

```text
function                              samples   %jit   calls GL?
draw_primitive                            552   3.10%   yes
wined3d_cs_run                            262   1.47%   consumer loop, not a slice
shader_glsl_load_constants                201   1.13%   yes, 34 call sites
wined3d_device_apply_stateblock           167   0.94%   producer thread
shader_glsl_apply_draw_state               92   0.52%   yes
mgs2_batch_flush                           78   0.44%   yes
wined3d_context_gl_activate                69   0.39%   yes
ffp_blitter_clear_rendertargets            67   0.38%   yes
wined3d_context_gl_acquire                 66   0.37%   yes
wined3d_ffp_get_fs_settings                63   0.35%   no -- slice 1, already taken
set_glsl_shader_program                    63   0.35%   yes
mgs2_resolve_separable                     54   0.30%   no
```

Everything above slice 1's size issues GL calls. The pure functions left --
`wined3d_ffp_get_vs_settings`, `mgs2_resolve_separable` and similar -- are each
0.5% or less, so taking all of them would add roughly one percent of translated
work. That is not the 21.16 ms.

So the island cannot grow by picking pure leaves. It has to take functions that
call GL, and that turns on one question: where do WineD3D's GL entry points
actually go? Measured in the live process:

```text
glDrawArrays     0x7aed1de0   /usr/lib/wine/i386-windows/opengl32.dll +0x21de0
glDrawElements   0x7aed2e50   /usr/lib/wine/i386-windows/opengl32.dll +0x22e50
glUniform4fv     0x7af4a1b0   /usr/lib/wine/i386-windows/opengl32.dll +0x9a1b0
```

They are **x86 PE code inside Wine's opengl32**, not addresses in the native
driver. Native island code calling them would re-enter the emulator on every GL
call, which defeats the purpose.

There is a way through, and it is the interesting part. The island is compiled
into Box86, which already has `libmali` loaded natively in the same process, so
it can call the driver directly and skip the whole
`opengl32.dll -> unixlib -> opengl32.so -> Box86 bridge` chain -- a bigger saving
than removing translation alone. Wine's `opengl32` thunks look like plain
pass-throughs for the draw entry points (`thunks.c` contains no MGS2 conversion),
and the GLES conversions this port added live in `wined3d/context_gl.c`, above
the boundary, so they would still run.

That was a promising reading, not a proven one. It is now measured.

### 13.1 The GL gate passes

`mgs2_island_gl_probe_impl()` runs inside Box86, resolves the already-loaded
driver with `dlopen(..., RTLD_NOLOAD)` -- so it cannot pull in a second copy and
a different context -- and reads a handful of context values. WineD3D reads the
same values through its own `gl_ops`, on the same thread, in the same call, and
the two are compared in process.

```text
probe runs 4141   agree 4141   disagree 0   native unavailable 0

value              wine (opengl32)   native (libmali)
current program                  0                  0
array buffer                    66                 66
element buffer                   0                  0
active texture               33984              33984
viewport                 0 0 640 480        0 0 640 480
```

**Native island code observes exactly the GL context Wine observes.** The driver
is the same instance, the context is current on the same OS thread, and the
bindings agree on every one of 4141 probes. Calling GL directly from the island
is therefore viable, which is what unlocks the functions that hold the time:
`draw_primitive` at 3.10% and `shader_glsl_load_constants` at 1.13% both become
reachable, and calling the driver directly also skips
`opengl32.dll -> unixlib -> opengl32.so -> Box86 bridge` on every GL call.

One honest correction to the probe's own description. It was called read-only by
construction; `glGetError()` is not read-only, it *clears* the error queue. The
native side read 1282 (`GL_INVALID_OPERATION`) that had been left pending by the
frame, so the probe drained an error WineD3D's own `checkGLcall` might otherwise
have seen. That does not affect the gate -- the compared values are the context
bindings, read with `glGetIntegerv` -- but the error slot must not be used, and a
production island must not call `glGetError` speculatively.

### 13.2 Where this leaves the branch

The chain is now complete and every link measured: shipping source compiled for
ARM, layout-exact declarations, in-process bridge, byte-identical results on live
data, measured removal of translated work, and a native GL path that sees the
same context. What remains is engineering rather than unknowns.

### 13.3 What that engineering actually costs

"Port the subtree function by function" needed a number rather than a shrug, so
here is one. Transitive call closure over the WineD3D sources, counting every
function a slice would have to bring with it:

```text
slice                            functions   lines of body   share of jit
wined3d_ffp_get_fs_settings             10             268         0.35%   done
shader_glsl_load_constants             203            8181         1.13%
draw_primitive                         155            4113         3.10%
whole connected draw subtree           415           14981        10.20%
```

Slice 1 was ten functions and 268 lines. The next single slice is fifteen to
twenty times that for three to nine times the benefit, and the whole subtree --
which is what the +2.4 to +5.7 fps ceiling assumes -- is 415 functions and about
15,000 lines, forty times slice 1.

`shader_glsl_load_constants` is the clearest example of why the closure explodes:
the function itself issues no GL at all, but it calls `wined3d_buffer_load_sysmem`
thirteen times, and that pulls resource lifetime, mapping and locking into the
island.

**That estimate is withdrawn.** It measured the wrong thing: it counted what
slice 1's method -- extracting a function and its helpers by hand -- would cost if
repeated. The compiler does the port instead.

### 13.4 The whole renderer compiles for ARM

28 of WineD3D's 32 source files build for armhf essentially unmodified, with the
include paths and defines the shipping build already uses. `adapter_vk.c` is the
unused Vulkan path; `cs.c`, `directx.c` and `swapchain.c` are entangled with
Win32. The 28 objects link into one 894 KB shared object containing the whole
hot path -- `draw_primitive`, `shader_glsl_load_constants`,
`shader_glsl_apply_draw_state`, `mgs2_batch_flush` and slice 1 -- against 226
generated abort stubs for the Win32, GDI and setup entry points it links against
but must never call.

### 13.5 The boundary is a state cut, not a function list

The island duplicates 140 writable file-scope variables. Any cut that leaves one
reachable from both sides is wrong: two copies of `mgs2_batch` would diverge and
corrupt the frame, silently.

Closing over both calls and shared globals from the five hot functions reaches a
fixpoint at **588 of 1422 functions, 34 shared globals, zero leaks** -- and
146 internal entry points, dragging in the shader-generation machinery
(`shader_addline` alone has 89 external callers). That is a fault line through
the middle of WineD3D, not an island.

The coherent cut is the module's own public API. `wined3d.spec` exports 329
`wined3d_*` functions and d3d8 uses about 146 of them: the same bridge count as
the internal cut, but a documented, stable boundary, and it puts *all* of WineD3D
native rather than part of it. The reverse direction is small --
`wined3d_parent_ops` and `wined3d_device_parent_ops` are about seven callbacks.

```text
forward bridges   d3d8 -> native wined3d      ~146 exported functions
reverse callbacks native wined3d -> d3d8      ~7 vtable entries
abort stubs       Win32/GDI setup surface      226
native code       28 of 32 sources             894 KB
removes                                        21.16 ms/frame of translated work
ceiling                                        +2.4 to +5.7 fps from 13.85
```

Every link is proven: the source compiles, the layouts match, live guest pointers
read identically, an in-process bridge gives byte-identical results, routed work
measurably leaves the emulated path, and native code sees the same GL context.
What is left is building 146 bridges with correct ABI, seven reverse callbacks,
and keeping context creation on the x86 side.

### 13.6 All of it compiles, and the hot path is Win32-free

Two corrections to what is written above, both found by continuing instead of
stopping at the first reading.

`adapter_vk.c`, `cs.c`, `directx.c` and `swapchain.c` were described as entangled
with Win32. They were not. Each had exactly one error, always the same: `L"..."`
is a four-byte `wchar_t` on Linux against Windows' two-byte `WCHAR`. With
`-fshort-wchar`, **all 32 of 32 WineD3D sources compile for ARM.**

With the complete set linked, 3667 symbols resolve internally and 160 remain
external: 137 Win32/GDI/NT, 10 unused vkd3d, 9 GL/WGL, 4 Wine debug.

The 137 decide the branch, so they were traced rather than assumed. The draw-path
closure is 44 functions, and **three** of the 137 are reachable from it:
`QueryPerformanceCounter`, `_assert` and `_fdclass` -- all trivially provided
natively. The remaining 134 are context creation, swapchain, window and cursor
code, which stays x86.

**The hot path therefore needs no per-frame reverse bridge into Wine.** That is
the property the whole design depends on, and it is now measured.

### 13.7 The bridges generate themselves

The last piece was 146 forward bridges, and hand-writing 146 ABI signatures is a
reliable way to produce a crash weeks later. They are derived instead:
`harness/island/full/gen_bridge_table.py` reads `wined3d.spec` for the 372
exports, intersects with what d3d8 actually calls, and emits box86 `GO(name, sig)`
lines from the prototypes in `include/wine/wined3d.h`.

```text
wined3d.spec exports   372
used by d3d8           146
signatures derived     146
missing                  0
```

Recomputing the internal state cut with all 32 objects gives 759 functions and
197 entry points -- larger than the public API's 146 and undocumented besides, so
the API boundary is confirmed as the right one.

Method, generated stubs, external-symbol list and bridge table:
`harness/island/full/`.

Nothing here changes production. Both island switches remain off by default.

## 14. The cut, corrected -- and the analysis that produced the earlier numbers

Every cut figure in section 13 -- 588 functions, 759 functions, 146 and 197
internal entry points, "five globals on the draw path", and the one that mattered
most, "three of 137 Win32 entry points on the hot path" -- came from a reference
analysis with a blind spot, and is **withdrawn**.

The blind spot: with position-independent code, ARM addresses data through
PC-relative literal pools. The relocation names the *section*, `.bss`, and the
addend that identifies the variable sits in the literal word, which `objdump`
does not print alongside it. Two successive versions of the analysis therefore
saw no data references at all and reported clean cuts that were merely blind.

It was caught by checking a fact that had to be true: `mgs2_batch_flush`
obviously touches `mgs2_batch`, and `mgs2_batch` appeared in no reference set.
The fix is to build the objects with `-fno-pic`, which makes the relocations name
symbols directly, and to attribute each relocation to the enclosing function by
address range rather than by the last label seen. `harness/island/full/cut_analysis.py`
carries both, and the control check is written into its docstring.

With the analysis passing that control, the cut is far smaller than anything
reported before:

```text
functions in the cut        58 of 1774
shared writable globals      3
state leaks                  0
entry points to bridge      38
Win32 the cut needs         10 of 137
source files involved       14
```

Ten Win32 entry points, and most are the window and device-context calls of the
present path -- `GetDCEx`, `WindowFromDC`, `ReleaseDC`, `MapWindowPoints`,
`IntersectRect` -- plus `QueryPerformanceCounter`, `QueryPerformanceFrequency`,
`SetEvent`, `_assert` and `_fdclass`.

So the island's real boundary is **38 forward bridges and 10 reverse ones**, not
146 and 137. That is a different order of work from what section 13 concluded,
and it is the first cut figure in this brief that survived a control check.

Three separate false-clean results were caught this way in one investigation --
the lossy struct reconstruction, the cross-linked DWARF, and now the invisible
data references. Each looked like a clean answer and each would have been acted
on. The control checks, not the analyses, are what made the numbers usable.

## 15. The island work list, gated

With the cut analysis fixed and passing its control, the remaining work is
enumerated and each part has been gated by measurement rather than estimated.

**Shared state: nothing to do.** The three writable globals the cut touches --
`mgs2_batch` (4120 B), `mgs2_batch_cache` (196 kB) and this brief's own
`mgs2_p38` -- are referenced only from inside the cut. Routing those 58 functions
leaves the x86 copies dead rather than divergent, so no sharing mechanism is
needed. This was the objection that looked most likely to sink the design.

**Bridge cost: negligible.** Patch 46 counts calls to all 37 entry points in the
live game:

```text
calls/frame   entry point
      569.1   wined3d_buffer_load
      381.9   wined3d_texture_load_location
      378.9   wined3d_rendertarget_view_load_location
      215.6   wined3d_texture_from_resource
      201.1   wined3d_texture_invalidate_location
      197.1   wined3d_rendertarget_view_invalidate_location
       99.9   device_invalidate_state
       85.4   mgs2_batch_flush
       27.5   context_invalidate_state
      ~2300   total crossings per frame if every one is routed
```

Box86's bridge marshalling was measured at 0.04 ms/frame for roughly 1500 GL
crossings, about 27 ns each. 2300 crossings is therefore about **0.06 ms of a
72 ms frame** -- three orders of magnitude below the 21 ms the island targets.
Calls between functions inside the island cost nothing at all.

**What is left:**

```text
37 forward bridges       marker plus id in the prologue, generated
10 reverse Win32 bridges  GetDCEx, WindowFromDC, ReleaseDC, MapWindowPoints,
                          IntersectRect, QueryPerformanceCounter/Frequency,
                          SetEvent, _assert, _fdclass
shared state              none
integration               native wined3d alongside the x86 one, context creation
                          stays x86
validation                differential, per frame
A/B                       fixed scene, fixed clock
```

**Expected size, honestly.** This cut's roots are 5.5% of JIT samples against
about 10.2% for the whole draw subtree, so it covers roughly half of the 21.16 ms.
At best -- native code free -- that is about 10 ms, 72.22 to 62 ms, 16.1 fps. At a
realistic half-of-dynarec it is about 5 ms, 14.9 fps. From 13.85. So **+1.1 to
+2.3 fps for this cut**, not the +2.4 to +5.7 that assumed the whole subtree.

Nothing is claimed until an A/B on a fixed scene says so.

## 16. The full island is built; it does not run yet

All 37 bridges exist and both sides build. The island does **not** work: the
first live run dies before any entry point matches.

```text
markers injected            37/37, all unique in the DLL
box86 signatures derived    37, 23 distinct wrappers, generated
island objects in box86     32 WineD3D sources, prebuilt, linked
box86 with the island       links, starts, prints its banner
first live run              wine: Unhandled illegal instruction at 4002017B
                            no entry matched, no stub reached
```

Two integration bugs were found and fixed on the way, both worth recording
because both produced misleading symptoms:

- **Three markers were duplicated.** `wined3d_buffer_invalidate_location`,
  `wined3d_resource_free_sysmem` and `wined3d_texture_prepare_location` were
  inlined into their callers, carrying the marker with them, so the same id
  appeared six and seven times. Marking those three `noinline` restores
  uniqueness; they are routed to native code anyway.

- **The stub generator stubbed libc.** It excluded symbols box86 *defines* but
  not the ones it imports, so `memcpy`, `memset`, `strlen`, `strcmp`, `getenv`
  and the float maths were each given an `abort()` body. box86 died before
  printing its banner, which read exactly like "the island broke box86". The
  generator now excludes everything libc/libm/pthread provides, and takes box86's
  own symbols from its object files rather than from a linked binary that already
  contains the island -- that filter is circular and silently empties the list.

What remains is the illegal instruction. It is at a guest address in the region
box86 maps for its own use rather than in `wined3d.dll`, and it happens before
any marker matches, so it is not obviously the markers themselves. That is the
next thing to debug, and it is debugging rather than design.

Artefacts: `box86-patches/09-island-full-bridges.patch`,
`harness/island/full/` (build method, generated bridge table, wrappers, stubs,
entry list, cut analysis, call-frequency reader).

Production is untouched throughout: the launcher still selects
`box86-native-dsound-fir1` and p32, and every island switch defaults to off.

## 17. The illegal instruction: the marker was compiled into the ARM code

Section 16's crash is found, explained and fixed. It was not an integration
detail. The island's entry marker is an **x86 instruction**, and the island's
own ARM build put it in the ARM instruction stream.

The marker is an eight-byte multi-byte NOP whose displacement spells "MGS" plus
the entry id, written as a bare `.byte` directive in the WineD3D source so Box86
can match it in the guest prologue. Those same sources are compiled for armhf to
build the island. `.byte` does not care what it is emitting into. Every one of
the 37 marked functions therefore carried these eight bytes immediately after
its ARM prologue, where as Thumb they decode as:

```text
1f0f    subs r7, r1, #4
0084    lsls r4, r0, #2
474d    bx   r9          <- branch to whatever r9 holds
1553    never reached
```

Every native island function branched to a garbage address before executing one
instruction of its own body. Counted in the shipped `box86-island4`: **39 marker
occurrences in `.text`**, one per source site -- all 37 entry ids plus the two
older FFP and GL-probe markers, each appearing exactly once, so the earlier
inlining fix held. Three more sit in `.rodata`, and those are correct: they are
Box86's own matcher tables. The island could never have worked, in any
configuration.

### 17.1 Three readings in section 16 were wrong, and one of them mattered

```text
claimed 16                              measured 15 August
"no entry matched"                      entries 2 and 21 both matched
"no stub reached"                       true, but only because no body ran
"the address is in the region box86     true, and specifically: it is a bridge
 maps for itself, not in wined3d.dll"    slot, eleven bytes in
```

The first two were **artefacts of the log level**, not observations. The island
logged at `LOG_INFO`; `launch-play.sh` sets `BOX86_LOG=0`. Nothing it printed
could ever appear. Patch 10 moves those lines to `LOG_NONE`, and the same run
then names both matched entries.

`4002017B` decodes exactly. Bridge bricks are at `0x40000000 + k*0x10000`
(measured, `BOX86_DYNAREC_LOG=1`), a bridge slot is sixteen bytes, and byte 11
is its `ret`. Before calling a wrapper the dynarec stores that address as the
guest EIP. So the reported guest address is not where the fault happened -- it
is the bookmark Box86 left before entering native code. Confirmed in the dump:
`x86opcode=C3 00 00 00 00 CC 53 43`, a `ret` followed by the next slot's
`CC 'S' 'C'`. The bridge memory was never corrupt.

### 17.2 The instrument that settled it

`BOX86_SHOWSEGV=1` prints the crash dump at `LOG_NONE`, so it survives the
launcher pinning `BOX86_LOG=0`. It gives the native PC, the guest EIP, and the
bytes at both -- which is the whole diagnosis in one line. It should have been
the first thing tried, not the fifth.

```text
SIGILL @0x195f6fc (x86pc=0x4002017b) opcode=10 F9 95 01 67 33 8E 7B
                                     x86opcode=C3 00 00 00 00 CC 53 43
```

Native PC `0x195f6fc` is a guest stack address, and the "opcode" there is a
guest stack frame: a saved frame pointer and a return address into Wine. That is
`bx r9` having landed.

### 17.3 The A/B that proved it needed both halves

```text
arm  box86        wined3d     ISLAND_FULL   result
A    island4      p47         1             illegal instruction at 4002017B
B    island4      p47         0             ran the full 100 s window
C    island4      p32         1             ran the full 100 s window
```

Marker without an armed bridge is inert, and an armed bridge without a marker is
never reached. Only routing an actual call into native code triggers it, which
is why the crash looked like it happened before anything matched.

### 17.4 The fix, and what it exposed

Patch 48 wraps the marker in `MGS2_ISLAND_MARK()`, emitted under
`#ifdef __i386__` and nothing otherwise. The i386 code is semantically
unchanged, so `wined3d_p47_island_markers.dll` stays valid and was not rebuilt;
only the 32 ARM objects change.

"Unchanged" was first written as "byte-identical", and a rebuild from the
documented recipe shows that is not quite true: 67 of 2,917,716 bytes differ.
Three are the PE checksum. The other 64 are all in `.text`, all immediately
after a `mov [esp+N], imm32`, and all shifted by exactly +24 -- they are
`__LINE__` constants from `assert()` and the debug macros in static inline
functions in `wined3d_private.h`, and this patch adds exactly 24 lines of its
own comment to that header. No instruction, control-flow or marker changes. `harness/island/full/build_island_objects.sh` now carries
the object recipe, which existed only as a shell snippet in BUILD.md, and its
control check greps the built objects for the marker bytes.

Result on the device, same run, everything else fixed:

```text
before   wine: Unhandled illegal instruction at 4002017B
after    MGS2 island: forbidden call to WindowFromDC
```

That is an abort stub firing by name -- the designed behaviour, and the first
time native island code executed its own body on this device.

### 17.5 Three further walls, each measured

Fixing the marker does not make the island work. It makes the real problems
visible, and there are three. All were reached on the device.

**Win32 window and DC calls.** `wined3d_release_dc` (entry 21) reaches
`WindowFromDC` and `ReleaseDC`; `wined3d_swapchain_set_window` (entry 30)
reaches those plus `GetDCEx`. Both are window/DC code, which section 13.6 said
stays on the x86 side; the cut analysis routed them anyway. Dropping them is
free -- neither appears in the section 15 call-frequency table at all.

**`NtCurrentTeb()` reads the wrong thread pointer.** With entries 21 and 30
removed, the run dies in the island's own `device_invalidate_state` (entry 3),
reading address `0x24` with entirely valid arguments (`device=0x02b766d8`,
`state=0x171`, read off the guest stack by the wrapper exactly as intended).
The two builds disagree on one instruction:

```text
i386   64 8b 15 18 00 00 00   mov edx, fs:[0x18]      Wine's TEB
       39 42 24               cmp [edx+0x24], eax     the Win32 thread id
arm    ee1d 2f50              mrc 15,0,r2,cr13,cr0,{2}  the NATIVE thread pointer
       6a53                   ldr r3,[r2,#36]
```

`wined3d_from_cs()` identifies the calling thread through `NtCurrentTeb()`. On
i386 that is `fs:[0x18]`, which Box86 maintains. Compiled for ARM it becomes a
read of the host thread pointer, which has nothing to do with the guest TEB.
Every island function that checks which thread it is on reads arbitrary memory.

**Indirect calls through guest-held pointers.** With entries 21, 30 and 3 out of
the way, `wined3d_rendertarget_view_prepare_location` (entry 24) dies at native
PC `0x7b9330a4` with `opcode=56 53 83 EC 24 8B 45 14` -- `push esi; push ebx;
sub esp,0x24; mov eax,[ebp+0x14]`. That is **x86 code inside wined3d.dll, being
executed as ARM**. WineD3D reaches its objects through pointers held in guest
structures (`resource_ops`, `texture_ops`, `adapter_ops`, `parent_ops`,
`gl_ops`), and those hold x86 addresses or Box86 bridge addresses. Native ARM
code cannot call either.

This is the one that changes the assessment, and it lands on the claim the
design rests on. Section 13.6 concluded "the hot path therefore needs no
per-frame reverse bridge into Wine," and called it the property the whole design
depends on. That conclusion counted **undefined Win32 symbols**: it asked which
imports the closure needs. It could not have found this, because an ops-table
call needs no import at all -- the pointer is data, filled in at runtime by the
x86 side. Section 14's rewritten cut analysis has the same shape: it was fixed
to see data *references*, and its control check passes, but it counts direct
call edges. Neither analysis ever counted indirect calls, and WineD3D is built
on them.

So 13.6 is not retracted as far as it goes -- the hot path really is free of
Win32 *imports* -- but the sentence it was used for, that no reverse bridge is
needed, is withdrawn. A reverse bridge is needed, per guest-held function
pointer, and that is a larger surface than the 37 forward ones.

### 17.6 How much of the island survives all three conditions

`harness/island/full/island_reach.py` walks the direct call graph of the linked
ARM binary from each entry and reports reachable abort stubs, `NtCurrentTeb()`
reads, and indirect call sites. Its control check is that `wined3d_release_dc`
must report `WindowFromDC` and `ReleaseDC`; the first version failed it, because
its line regex matched only Thumb encodings and found no calls at all.

```text
entries                                    37
reach an abort stub                        23
reach a real Win32 window/DC call           2   entries 21, 30
reach an NtCurrentTeb() read                3   entries 3, 21, 30
no stub, no TEB read, no indirect call      7   entries 0, 2, 5, 6, 18, 29, 32
```

That last figure was **1** in the first version of this section, and it was
wrong. `bx lr` is how a leaf function returns on ARM, and the counter matched it
as an indirect call, giving almost every function a phantom call site. Fixing it
moved the number from 1 to 7 -- the same class of mistake as the three
false-clean results in section 14, caught the same way, by asking whether a
number that decides something can be checked against a fact that must be true.

Of the seven, only entry 32, `wined3d_texture_from_resource`, is hot. **The four
entries that carry most of the frame -- `wined3d_buffer_load` at 569 calls a
frame, `wined3d_texture_load_location` at 382, `wined3d_rendertarget_view_load_location`
at 379, `mgs2_batch_flush` at 85 -- all make indirect calls, and all pull a
closure of over 900 functions.**

The indirect-call criterion is conservative: a register call may target
something the island can reach, or sit on a path never taken. It has one
confirmed true positive on this device (entry 24) and no confirmed false
positive.

Arming one entry and nothing else is the positive control for the routing
mechanism, and it passes. Entry 5 was chosen because at the time it was the only
one the criteria left; section 18 raises that to 15 and runs eleven of them on
the live game.

```text
MGS2_BOX86_ISLAND_ONLY=5, 150 s window
  armed          1 of 37
  matched        entry 5 at guest 0x7b81f010 -> bridge 0x40020020
  faults         0 illegal instructions, 0 aborts, 0 forbidden calls
  outcome        ran the full window
```

So the mechanism works end to end: a marked guest function is recognised, routed
to native ARM, executed, and returned from, in the live game. What did not work
at this point was any of the WineD3D functions the cut was drawn around. That
distinction is what section 18 goes on to close, partly.

### 17.7 What it would actually take

```text
Win32 window/DC entries       drop 21 and 30; free, they are not hot
NtCurrentTeb()                a native NtCurrentTeb() returning the guest TEB
                              from Box86's per-thread FS base
Wine debug + CRT stubs        _assert, _fdclass, _recalloc, __wine_dbg_*,
                              __stdio_common_vsprintf -- all providable, and
                              they sit on ERR paths rather than the hot path
indirect calls                the open problem: every ops table and gl_ops
                              entry the island reaches would need a native
                              thunk that re-enters the emulator, which is the
                              reverse of the 37 forward bridges and costs an
                              emulator entry per call
```

The first three are bounded work, and section 17.9 does all three. The fourth is
not a detail -- it is a second bridge layer in the opposite direction, and the
section 15 estimate of +1.1 to +2.3 fps was costed without it. Nothing about
that estimate is retracted here, because nothing has been measured; it is simply
not yet reachable, and the cost side of it is now known to be larger than
section 15 assumed.

### 17.8 Artefacts

```text
wine-patches/48-island-marker-i386-only.patch    the fix
box86-patches/10-island-entry-selection.patch    MGS2_BOX86_ISLAND_ONLY, visible logs
harness/island/full/build_island_objects.sh      the ARM object recipe, with its
                                                 own marker control check
harness/island/full/island_reach.py              reachability, TEB and indirect
                                                 call census, with control check
```

The island Box86 builds are not versioned in `binaries/`, in keeping with how
`box86-island1..4` were handled: they are laboratory binaries selected by no
launcher. The fixed one is `box86-island6`, sha256
`869ddc0fa35b50461852676a602e717bbcca2d2c25b65f2900b50c4ccc5d5c08`, staged on
the console and rebuildable from `box86-patches/BUILD.md` plus patches 09 and 10
and `build_island_objects.sh`.

Production is untouched. The launcher still selects `box86-native-dsound-fir1`
and p32, every island switch still defaults to off, and the only device-side
addition is `launch-island-dbg.sh`, which differs from `launch-play.sh` by one
line: it lets `BOX86_LOG` be set from outside.

## 18. The island runs on the live game, and no frame-rate effect is measured

Section 17.7's first three items are done, and the island now executes native
ARM WineD3D inside real gameplay. What it does not have is a frame-rate result,
and this section says exactly why rather than leaving the gap implied.

### 18.1 The three fixes

**Win32 window/DC entries dropped.** Entries 21 `wined3d_release_dc` and 30
`wined3d_swapchain_set_window` leave the cut. Both are window and device-context
code that section 13.6 assigned to the x86 side; neither appears in the
calls/frame table. 37 entries become 35. Their markers stay in the guest DLL and
never match, so no DLL rebuild.

**`NtCurrentTeb()` (patch 49).** The ARM branch of `winnt.h` gets an
`MGS2_ISLAND_ARM` alternative calling `mgs2_island_teb()`, which Box86 resolves
as the current thread emu's FS base plus 0x18. Control check: the linked binary
must contain zero `mrc ..., cr13, cr0, {2}` instructions. It does.

**Six reached stubs become real code (Box86 patch 11).** `_assert`, `_fdclass`,
`__wine_dbg_header`, `__wine_dbg_output`, `__wine_dbg_strdup`,
`__wine_dbg_get_channel_flags` and `__stdio_common_vsprintf` move from abort
stubs to `src/mgs2_island_natives.c`. ERR is *not* compiled out of the island --
its channel test is a direct flags read -- so with stubs no entry could run at
all. The first 16 ERRs print in full and the rest are counted and suppressed,
because an ERR firing per draw would break rule 2 while measuring.

`_recalloc` deliberately stays an abort stub. It would resize a block whose
allocator is unknown: a WineD3D structure reaching the island may have been
allocated by the guest msvcrt, and handing a guest heap pointer to the host
realloc corrupts both heaps. No routed entry needs it.

With all three, the clean set goes from 7 of 37 to **15 of 35**.

### 18.2 The attract-mode A/B measured nothing, and that is a methodology error

Four interleaved 240 s arms, one binary, one DLL, one clock, differing only by
`MGS2_BOX86_ISLAND_FULL`:

```text
OFF   n=73 samples   median 60.10   mean 59.736
ON    n=74 samples   median 60.10   mean 59.708
difference of means  -0.028 fps (-0.05%)
```

That is not a null result, it is a **failed measurement**. The attract demo runs
at the 60 Hz ceiling: 29 of 37 samples sit at exactly 60.2, and the dips to 57.4
recur at the same positions in all four arms. There is no headroom, so the arms
cannot differ. The harness is sound -- the repeatability proves it -- the scene
is wrong.

The error was reading AGENTS.md's "the attract-mode demo is deterministic:
31/9/11/4 frames over 50/100/200/500 ms" as a frame-rate harness. Those are
stall buckets. Determinism is necessary for an A/B and is not sufficient; the
scene must also be below the cap. **Do not use the attract demo for a frame-rate
A/B.**

### 18.3 On the reinforcement scene the island runs, and the scene swamps it

The owner loaded the heavy save and played through an actual reinforcement
encounter with 15 entries armed. Two consecutive windows:

```text
window   wall    frames   fps    300-frame samples
1        60 s      900    15.0   19.0 12.7 14.4
2        90 s     1200    13.3   13.1 14.6 15.1 15.2

CPU 2.03 s per wall second (203% of one core), 1992 MHz held, 68 -> 70 C
armed 15   matched 11
island-routing faults 0   forbidden calls 0   assertions 0   ERRs 0
fatal faults 0
```

**"Faults 0" needs its scope stated, or it contradicts the raw log.** The run
contains 14 handled `SIGSEGV`s. They are not island faults: the OFF arm of the
attract A/B contains exactly 14 as well, at exactly the same address
(`0x62bb3d38`, inside Box86's own text), so this is baseline Box86 signal
handling and is identical with the island on and off. The counters above are
what the harness actually greps for -- `SIGILL`, `Unhandled`, `forbidden call`,
`assertion` -- and none of those fired. Written as a bare "zero faults" it read
as "no signals at all", which the log does not support.

Eleven WineD3D functions -- `device_invalidate_state`,
`context_invalidate_state`, `wined3d_texture_invalidate_location`,
`wined3d_rendertarget_view_invalidate_location`, `wined3d_texture_from_resource`,
`wined3d_buffer_invalidate_location`, `debug_d3dformat`, `wined3d_debug_location`,
`wined3d_stream_info_from_declaration`, `context_invalidate_compute_state` and
this brief's own census helper -- executed as native ARM through 2100 frames of
live combat without a single fault. That is the mechanism working end to end on
the target scene.

**No frame-rate claim follows.** 13.3--15.0 fps sits inside the 11.9--19.5 fps
band this brief already measured for reinforcements without any island, so the
run cannot distinguish a gain from its absence. There was no control arm: the
owner was under fire and could not stand still, let alone repeat the route.
Per rule 3 this is a scene measurement, not an arm measurement.

It was never going to show much. The armed set is 741 of ~2300 crossings a
frame, all of them short functions. The four entries that carry the frame --
`wined3d_buffer_load` at 569 calls/frame, `wined3d_texture_load_location` at 382,
`wined3d_rendertarget_view_load_location` at 379, `mgs2_batch_flush` at 85 --
are not armed, because each pulls a closure of over 900 functions containing
indirect calls whose targets this analysis cannot see. The weight of the frame
is untouched.

An earlier version of this paragraph said those four "cannot be armed" at all.
**That is withdrawn** -- section 19 explains why it did not follow from anything
measured.

### 18.4 Where this leaves it

```text
proved      the island executes native ARM WineD3D in live gameplay, on the
            target scene, without an island fault -- 15 armed, 11 exercised
not proved  any effect on frame rate, in either direction
not armed   the four hot entries, because their indirect targets are unknown
            to a static direct-call analysis -- NOT because they are known to
            be unreachable; see section 19
next        measure where those indirect calls actually go, then a control arm
            on the same route
```

One instrument bug found and fixed while measuring: the CPU sampler read
`$14`/`$15` from `/proc/PID/stat`, which POSIX sh parses as `${1}4`, so it
returned 0 every time. The first window's CPU figure was discarded; the second
is real.

Artefacts: `wine-patches/49-island-arm-guest-teb.patch`,
`box86-patches/11-island-natives-and-cut.patch`,
`harness/island/full/mgs2_island_natives.c`,
`logs/rg353vs/island-marker-20260815/`. The island Box86 with all of it is
`box86-island7`, sha256
`a6ba757549e9565212c413fb4aa2923d87923d0ce7e6b7c53c021e0c5fb7de5e`.

## 19. "Cannot be armed" was wrong, and the review that caught it

Section 18 concluded that the four hot entries "cannot be armed", from this
chain:

```text
hot entry -> closure has indirect calls -> the pointer lives in a WineD3D
object -> the target is an x86 address -> ARM cannot call it -> it needs a
reverse thunk into the emulator -> there are too many -> impossible
```

An external review pointed out that the last three steps do not follow from the
first four, and it is right. Every checkable claim in that review was verified
against the pinned Box86 and the Wine 11 sources before accepting it; all of
them hold.

### 19.1 What the analysis never established

`island_reach.py` counts `blx`/`bx` on a register. That is a **risk marker, not
a target**. The step from "this call goes through a register" to "the callee is
foreign x86 that only the emulator can run" was never measured -- it was
assumed, and then carried into a conclusion about feasibility.

The counts make the gap obvious in hindsight. After patch 11 the hot roots hold
16--25 static indirect sites each, not the 900-function closures that were being
quoted alongside them. The closure size measures how much *native* code runs;
the site count measures how many decisions are unresolved. Quoting the first as
though it were the second made the problem look an order of magnitude worse than
anything measured.

### 19.2 Box86 already resolves most of this, and it was not consulted

```text
GetNativeFncOrFnc()   src/tools/bridge.c:205
                      if (IsBridge(fnc)) return ((onebridge_t*)fnc)->f;
                      a bridge address unwraps to the native function pointer
RunFunctionFmt()      src/include/callback.h:10
DynaCall()            src/dynarec/dynarec.c:95
                      native -> guest, on a given emu, the mechanism Box86's
                      own wrapped libraries already use for callbacks
```

So a pointer that looks like x86-callable to Wine is **not automatically a trip
through the emulator**. Box86's own wrappers try the unwrap first and only build
a guest-calling thunk when the callback really is guest code.

### 19.3 WineD3D's indirect dispatch is mostly its own backend model

```c
buffer->buffer_ops->buffer_prepare_location(...)   /* buffer.c:266 */
    -> wined3d_buffer_gl_prepare_location          /* buffer.c:1124 */
texture->texture_ops->texture_load_location(...)
    -> texture_gl_ops                              /* texture_gl.c:2773 */
```

`buffer.c` and `texture_gl.c` are two of the 32 sources the island already
compiles for ARM. The target of that indirect call is not a foreign callback;
it is a function the island has its own native copy of.

`island_ops_targets.py` enumerates every ops-table initialiser in the WineD3D
sources and checks each named target against the linked ARM binary:

```text
ops tables                                  56
targets named in them                      270
present as ARM symbols                     268
absent                                       2   Vulkan state tables, not
                                                 functions, and unused here
```

Control check: the `buffer_gl` dispatch the review named must be found and must
resolve natively. It does.

This is a **static upper bound on what a resolver could redirect without
entering the emulator**, not proof that any given site takes one of these
targets. Only a runtime census can show that. But it settles the narrower
question: there is an ARM counterpart to redirect *to*.

Sizing the whole surface, across all of WineD3D:

```text
ops-table dispatch sites                    95
  of which parent_ops->wined3d_object_destroyed   17   genuine callback into d3d8
GL calls via gl_info->gl_ops.{gl,ext}.p_*  694   already-native driver entries
```

### 19.4 The corrected model

```text
indirect call
  -> classify the runtime target
     A  Box86 bridge          unwrap with GetNativeFncOrFnc -> direct ARM call
     B  internal WineD3D      map guest address -> the island's own ARM copy
     C  GL / gl_ops           the native libmali entry, which the GL gate
                              already proved is the same context
     D  genuine guest callback  typed RunFunctionFmt on the entry emu
     E  unknown               do not arm
```

Only D needs the emulator, and D is where `parent_ops` lives -- which BUILD.md
already sized at about seven callbacks into d3d8.

### 19.5 A real bug the review found in patch 49

`mgs2_island_teb()` resolved the guest TEB through `thread_get_emu()`. That
function does not report "no emu on this thread": it **creates** one, with a
fresh 2 MB stack, and publishes it into TLS (`src/libtools/threads.c:180`). So
the NULL check under it could never fire, and a call arriving on a thread Box86
had not set up would have been answered with the FS base of a brand-new,
unrelated emulator -- a plausible wrong TEB, which is the worst kind.

Fixed: every generated wrapper now brackets its native call with
`MGS2_ISLAND_ENTER`/`LEAVE`, saving and restoring a thread-local `x86emu_t *`
so nesting is safe, and `mgs2_island_teb()` uses that entry emu and aborts
diagnostically if there is none. The same saved emu is what a class-D reverse
callback must run on. 23 wrappers bracketed; the binary still contains zero
`mrc ..., cr13, cr0, {2}`.

### 19.6 What is withdrawn, and what replaces it

Withdrawn: *"the four hot entries cannot be armed."*

Replaces it: **the four hot entries cannot be armed by the current
direct-call-only resolver, because their closures contain indirect calls whose
runtime targets no static analysis here has determined.** The static evidence
now says most of those targets have native ARM counterparts. Whether the hot
paths actually take them is unmeasured, and that is the next measurement, not a
conclusion.

Section 18's "faults 0" is also corrected in place: the run contains 14 handled
`SIGSEGV`s, identical in count and address to the island-off arm, so they are
baseline Box86 behaviour -- but "zero faults" read as "no signals", which the
raw log does not support.

### 19.7 The next measurement

An indirect-target census, memory-only and bounded, over the four hot roots.
Not a log line per call -- 1380 indirect calls a frame would violate rule 2 while
measuring. A table keyed by call site, classifying each distinct target once and
counting thereafter:

```text
callsite_id  root  target  calls  class(A/B/C/D/E)
```

The number that decides the branch is not "21 indirect sites". It is the
per-frame distribution, e.g.:

```text
wined3d_buffer_load   indirect calls/frame 1380
  71% Box86/GL bridges        A/C  -> unwrap, no emulator
  24% internal WineD3D        B    -> the island's own ARM copy
   4% genuine guest callback  D    -> RunFunctionFmt
   1% unknown                 E
```

If it looks like that, the island is a live performance candidate again. If most
targets are arbitrary guest callbacks, it is not. Then one hot root -- whichever
census shows the fewest class-D targets -- armed alone, against a production
control on one save and one reinforcement route.

Not started. Nothing above is a performance claim.

Artefacts: `harness/island/full/island_ops_targets.py`,
`box86-src/src/mgs2_island_entry.h`, updated `mgs2_island_natives.c` and
generated wrappers. `box86-island8`, sha256
`ad25ffb620d49da3da9eda316cfb60d894d5c4270b81cd203b25285e95721260`, is the build
with the entry-emu bracket, exported as `box86-patches/12-island-entry-emu.patch`.

Validated on the device, 15 entries armed, 11 exercised, 140 s window: the
diagnostic abort never fires, so the bracket covers every path that reads
`NtCurrentTeb()`. Zero island faults, and the 14 handled `SIGSEGV`s match the
island-off baseline exactly.

## 20. The indirect-call census: every hot target is native-resolvable

Section 19 said the branch turned on one unmeasured number -- where the hot
paths' indirect calls actually go. Patch 50 measures it. The answer is not
marginal.

### 20.1 Why the census lives in the guest DLL

The four hot roots are not armed, so in the island they never execute and there
is nothing there to observe. In the x86 build they run every frame, against the
same objects, and therefore against the same pointer values the island would
see. So the instrument goes in `wined3d.dll`: twelve ops-dispatch sites on the
hot paths, each wrapped so the pointer is recorded and then called, unchanged.

```c
#define MGS2_P50_CALL(site, fp) (mgs2_p50_icall((site), (const void *)(fp)), (fp))
```

Bounded, memory-only, published at present like every other census here, read
externally by `harness/island_icall_census.py`. Each distinct target is
classified once, in the guest, and counted thereafter:

```text
1 box86-bridge   a CC 'S' 'C' thunk -- native code, reachable by unwrapping
2 wined3d-self   inside wined3d.dll, so the island has its own ARM copy
3 other-module   somewhere else, and the only class that may need the emulator
```

### 20.2 The result, on the reinforcement scene

Owner-loaded heavy save, real reinforcements, 6530 presents, island off so the
guest's own dispatch is what is measured:

```text
site                                          calls    per frame  targets  class
buffer_ops->buffer_prepare_location        5,171,486      792.0        1  wined3d-self
texture_ops->texture_prepare_location         26,310        4.0        1  wined3d-self
resource_ops->resource_sub_resource_get_desc   7,142        1.1        2  wined3d-self
texture_ops->texture_unload_location           1,170        0.2        1  wined3d-self
resource_ops->resource_unload                    234        0.0        1  wined3d-self
texture_ops->texture_load_location                39        0.0        1  wined3d-self
texture_ops->texture_upload_data                   1        0.0        1  wined3d-self
parent_ops->wined3d_object_destroyed             117        0.0        1  other-module

wined3d-self   100.0%   5,206,382   797.3/frame
other-module     0.0%         117     0.0/frame
```

The attract demo, measured separately, gives the same shape: 4,254,645 calls,
100.0% `wined3d-self`, the same single `other-module` target.

### 20.3 What it settles

**The hot indirect dispatch is single-target and internal.** Every site but one
resolves to exactly one address, every one of those addresses is inside
`wined3d.dll`, and all 32 WineD3D sources are already compiled for ARM -- so a
native counterpart exists by construction, and section 19.3's static check
already confirmed 268 of 270 ops-table targets have one.

The only genuine cross-module callback, `parent_ops->wined3d_object_destroyed`
into d3d8, ran **117 times in 6530 frames**: 0.0 per frame. The "second bridge
layer in the opposite direction" that section 17.7 priced as the blocking cost
is, on this path, essentially absent.

Single-target dispatch also makes the resolver cheap: a per-site cache of one
entry would hit 100% of the time here, so the classification cost need not be
paid per call.

This does not make the island fast. It removes the reason given for believing it
could not be made fast, and that reason was mine.

### 20.4 What is still unmeasured

```text
GL dispatch      694 call sites through gl_info->gl_ops are NOT instrumented.
                 They are expected to be class 1, Box86 bridges to the already
                 native driver, but expected is not measured.
resolver         not built. The table "guest wined3d address -> native ARM
                 symbol" must be generated from the exact i386 build and the
                 exact ARM object set, never by hand.
frame effect     still nothing. No hot root has been armed, and no A/B run.
```

Artefacts: `wine-patches/50-island-icall-census.patch`,
`harness/island_icall_census.py`, `binaries/wined3d_p50_icall_census.dll`,
`logs/rg353vs/island-marker-20260815/p50-*.json`.

## 21. The unattended route was loading the wrong save, and what the island fix is worth

### 21.1 A methodology defect in the autoload harness

The owner reported it: the save list does not open on the save this project
measures. `autoload_save.py` confirmed at once by confirming whatever entry the
cursor started on. **Every unattended run through that harness has been loading
a different save, and therefore measuring a different scene.**

Fixed with `MGS2_SAVE_UP`, default 2, which moves the cursor before confirming:

```text
1-main-menu  z      2-on-load-game  down    3-save-list  z
3a-save-up-1 up     3b-save-up-2    up
4-confirm-box z     5-on-yes  left          6-loaded  z
```

`MGS2_SAVE_UP=0` restores the old behaviour. This does not invalidate anything
in this brief -- every island measurement here was taken on an owner-loaded save
or on the attract demo -- but it does mean **any earlier number attributed to
"the autoload route" was taken on an unknown save**, and section 6l's warning
about that route was better founded than it knew.

### 21.2 Verifying the island fix, and what it did not fix

Box86 patch 12's `__thread` pair was withdrawn (section 18/19 record why): the
entry emu now comes from `thread_get_emu_nocreate()`, which returns the current
thread's emu or NULL and never manufactures one. The check that matters is
structural, not behavioural:

```text
box86-island7   TLS memsz 0x2bc   known good, played the heavy scene
box86-island8   TLS memsz 0x2c4   +8 bytes, the only build that has died there
box86-island9   TLS memsz 0x2bc   identical to island7 again
```

On the device, `box86-island9` on the owner's heavy save through a real
reinforcement encounter:

```text
"accessing segment NULL"   0   (island8 produced 262 before dying)
SIGILL 0   Unhandled 0   SIGSEGV 14   -- 14 is the baseline every build shows
process                    did not die
```

**But the game froze.** Not a crash -- a hang, and the capture names it:

```text
tid wined3d_cs        WAIT_PRIVATE  timeout=NONE  waits for non-zero  -> unchanged
tid main              WAIT_PRIVATE  timeout=NONE  mutex contention    -> unchanged
tid wine_dmime_mess   WAIT_PRIVATE  timeout=NONE  waits for non-zero  -> unchanged
14 threads unchanged between two samples, 0 progressed
futex words at 0x400f012c / 0x400f0140 / 0x400f0150 -- Box86's sync arena
```

That is the third freeze of `MGS2_SEPARABLE_FREEZE_CAPTURE_2026-08-12`:
untimed futex, waiting for non-zero, in the Box86 sync arena. It is open,
unattributed, and predates every line of the island work. A 5838 ms frame
preceded it; the run that died under island8 was preceded by a 5778 ms frame.
**The same event may have ended one run in a hang and the other in a death**, in
which case attributing that death to island8 was over-reading a single run.

The `__thread` removal stays -- it is the right semantics regardless -- but it
must not be written down as "fixed the crash". The mechanism was never
established, and the crash may not have been ours.

### 21.3 A startup hang, once

One unattended launch never reached its first frame: three threads, the main one
in an untimed futex wait on `0x63017fc8` -- inside Box86's own image, waiting on
a contended word. Not reproduced:

```text
box86-island9                 3 of 3 reached first frame (37, 38, 38 s)
box86-native-dsound-fir1      3 of 3 reached first frame (37, 33, 33 s)
```

So one occurrence in seven, on the build that also carries the census DLL, with
a signature that again points at Box86's own locking rather than the island.
Recorded rather than explained.

### 21.4 State of the branch

```text
proved     the island runs native ARM WineD3D on the target scene; 100% of the
           hot indirect calls resolve to functions the island already has
not proved anything about frame rate; no hot root armed yet
open       the Box86 sync-arena freeze, older than this work and now captured
           again on a repeatable route
next       the class-B resolver: guest wined3d address -> native ARM symbol,
           generated from the exact i386 build and the exact ARM object set
```

## 22. The patch series did not apply, and now does

Asked to make sure the patch works and not just the tree it came from, the
series was applied from scratch to the pinned Box86 commit. **Patches 07 through
12 all failed.**

```text
01-06   ok, zero fuzz            the production chain, previously verified
07      FAIL  CMakeLists 413, box86context 60, 557
08      FAIL  CMakeLists 328, box86context 61, 240
09      FAIL  CMakeLists 328, box86context 60
10      FAIL  box86context 610, bridge.c 486
11      FAIL  CMakeLists 330
12      FAIL  both hunks ignored
```

Two causes, both the same mistake in different places. Patch 01 already adds
`wrappedlibegl.c` to `CMakeLists.txt`, and 07, 08 and 09 each add it again.
Patches 02, 05 and 06 already add their MGS2 blocks to `box86context.c`, and 09
adds all of them again along with its own. Every island patch had been exported
as a **diff from pristine**, so each one silently contained its predecessors.
Individually each looked right. In sequence none of them could apply, and nobody
had tried -- BUILD.md's "all six apply with zero fuzz in order" was true, and was
about the six that predate the island.

The series is now `01-06` plus a single `07-native-island.patch`, incremental on
01-06, carrying what the old 07-13 described. Applied to the pinned commit it
takes zero fuzz, and it reproduces the deployed binary's code exactly:

```text
.text        byte-identical, 0x61a3a0 bytes
whole file   501 of 8,484,024 bytes differ
   20        .note.gnu.build-id
  481        .rodata: build timestamp, and the absolute source path that
              __FILE__ bakes into the dynarec log strings
```

That path dependency is worth knowing before anyone checks this project with a
hash. Built from a differently-named directory the same series produces ~99,000
differing bytes with `.text` unchanged in size and content -- the literal pools
all move because `.rodata` did. Compare sections, not files.

### 22.1 And the island still runs

Unattended through the corrected autoload route, on the save the project
actually measures, 15 entries armed:

```text
armed 15   matched 11   frames 4800   fps 15.1-17.1
island faults 0   forbidden calls 0   assertions 0   segmentNULL 0
process alive at the end
```

So the state at the close of this work: the series applies and reproduces the
binary, the island executes native ARM WineD3D on the real save without fault,
every hot indirect call is known to resolve to a function the island already
has, and no frame-rate claim is made anywhere.

## 23. The GPU governor, and the freeze is not a lost wakeup

### 23.1 The dead-end list was right, and is now out of date

`README.md` closed "GPU governor pinned to 800 MHz" with: GPU wait halves, the
CPU cap falls to 816 MHz because both share one thermal budget, net loss. The
owner pointed out that the cooling has since been fixed and the GPU was still
sitting on `simple_ondemand`, spending the reinforcement scene at 400-600 of its
800 MHz. Changed cooling is new data, so it was re-measured.

One process, one spot (the autoload save), governor switched **live**, arms
interleaved so nothing restarts between them:

```text
arm               n    median   mean    sd     GPU     CPU cap   CPU / GPU temp
A1 ondemand      17    15.20   15.21          600 MHz  1992000   75.6 / 70.0 C
B1 performance   20    16.90   16.85          800 MHz  1992000   76.3 / 71.7 C
A2 ondemand      18    15.20   15.21          400 MHz  1992000   76.3 / 71.1 C
B2 performance   19    16.80   16.85          800 MHz  1992000   78.1 / 73.3 C

ondemand      n=35   mean 15.209   sd 0.227
performance   n=39   mean 16.851   sd 0.088
                     +1.64 fps, +10.8%
```

The two ranges do not overlap: the best `ondemand` sample is 15.7, the worst
`performance` sample is 16.6. **The CPU cap stayed at 1992000 in every arm** --
the throttling the old measurement found did not recur, which is exactly what a
cooling fix would change. End temperatures are 78.1 C CPU and 73.3 C GPU against
the launcher's 88 C cutoff.

Promoted: `launch-play.sh` sets the GPU governor to `performance`, saves the
previous value and restores it on exit alongside the CPU state.
`MGS2_GPU_GOVERNOR=simple_ondemand` reverts it for one run.

This is the only frame-rate gain measured in this brief.

### 23.2 The freeze is a deadlock, not a lost wakeup

The freeze recurred immediately afterwards, in the production configuration, and
this time the futex words themselves were read:

```text
tid  wined3d_cs        FUTEX_WAIT_PRIVATE  0x400f012c  val 0   word 0 -> 0
tid  wine_dmime_mess   FUTEX_WAIT_PRIVATE  0x400f0140  val 0   word 0 -> 0
tid  mgs2_sse_rg353v   FUTEX_WAIT_PRIVATE  0x400f0150  val 0   word 0 -> 0
tid  mgs2_sse_rg353v   FUTEX_WAIT_PRIVATE  0x400f0158  val 0   word 0 -> 0
12 threads unchanged across two samples, 0 progressed. Island faults 0.
```

Every waiter is asleep *waiting for the word to become non-zero, and the word
really is zero*, twice, three seconds apart. That is the correct thing for a
waiter to do. **So this is not a lost wakeup** -- the 2026-08-12 brief's framing
is wrong, or at least is wrong for this occurrence. Nobody posted. The remaining
threads sit in `ntsync_schedule`, Wine's kernel-backed sync, so the head of the
cycle is on that side and not in the futexes we can see.

The same two addresses, `0x400f012c` and `0x400f0140`, appeared in the 15 August
capture, so this is one repeatable defect and not a family.

It predates all island work and reproduces with the island off. But it happened
here **with the island in production**, and whether the island changes how often
it occurs is unmeasured -- one occurrence proves nothing about frequency. That
is the honest state, and it is the reason to keep `MGS2_BOX86_ISLAND_FULL=0` as
a one-word rollback in the launcher.

Capture: `logs/rg353vs/island-marker-20260815/freeze-prod/`.


## 24. The weak-ordering explanation is withdrawn

Section 23.2 left the freeze as "a deadlock, nobody posted". The next step taken
was to name a mechanism: WineD3D publishes a CS command with plain stores and
then raises a flag, x86 gives TSO, ARM does not, and Box86 with
`BOX86_DYNAREC_STRONGMEM=0` emits no barriers around ordinary loads and stores.

**That is wrong, and it was asserted before it was checked against the code.**
Wine 11.0's `cs.c` does not do what it claims:

```c
/* publication -- interlocked, not a plain store */
InterlockedExchange((LONG *)&queue->head, queue->head + packet_size);
if (InterlockedCompareExchange(&cs->waiting_for_event, FALSE, TRUE))
    pNtAlertThreadByThreadId((HANDLE)(ULONG_PTR)cs->thread_id);

/* and the consumer already guards the exact race that was being proposed */
InterlockedExchange(&cs->waiting_for_event, TRUE);
/* "The main thread might have enqueued a command and blocked on it after the
 *  CS thread decided to enter wined3d_cs_wait_event(), but before
 *  waiting_for_event was set." */
if (!(wined3d_cs_queue_is_empty(...DEFAULT) && wined3d_cs_queue_is_empty(...MAP))
        && InterlockedCompareExchange(&cs->waiting_for_event, FALSE, TRUE))
    return;
```

Both sides are interlocked operations, and Box86 emits `SMDMB()` around
lock-prefixed instructions regardless of `STRONGMEM` -- which this brief had
already established in section 23 and then failed to apply.

### 24.1 And 0x400f012c is not the queue word

The stronger correction. `0x400f012c` is the **per-thread alert futex** behind
`NtWaitForAlertByThreadId`, not any part of the CS queue. The waiter zeroes it
and sleeps on zero; `NtAlertThreadByThreadId` sets it to one and wakes.

So `0x400f012c: 0 -> 0` proves exactly one thing:

```text
wined3d_cs has no pending alert right now
```

It does **not** prove that a command was published and the consumer missed it.
Section 23.2's reading of that measurement was an over-reach in the same
direction as the mechanism it was used to support.

### 24.2 What actually distinguishes the two failures

The queue state does, and it was never read:

```text
cs->queue[DEFAULT].head / .tail
cs->queue[MAP].head / .tail
cs->waiting_for_event
cs->thread_id

A   DEFAULT head != tail and wined3d_cs asleep
      -> published work with a sleeping consumer; the handshake really is broken
         and the Box86 atomics on that path become the suspect
B   both queues empty and wined3d_cs asleep
      -> the CS is behaving correctly, and the question moves entirely to what
         the main thread is waiting for in ntsync_schedule
```

On the evidence so far B is at least as likely as A, and nothing collected up to
now separates them.

### 24.3 The soak, sized honestly

Four cycles of 240 s per arm is about 16 minutes of exposure each. If the freeze
rate is one an hour, the expected result is 0 and 0, which would mean nothing at
all. It is left running for base-rate information only, and **must not** be
reported as evidence for or against `STRONGMEM` unless it first reproduces the
freeze at `STRONGMEM=0`, preferably more than once.

`STRONGMEM=1` is still worth testing, but its result must be read narrowly: it
would say "this depends on Box86 memory-ordering behaviour", not "the CS queue
publication races". Level 1 is documented as partial, so a null result at level 1
does not clear memory ordering either.

## 25. The accelerated soak did not reproduce the freeze

Six cycles, three per `STRONGMEM` arm, 300 s of play each after an autoload to
the measured save, with `MGS2_CS_SPIN_COUNT=1` so the CS crosses
queue-empty -> `waiting_for_event` -> alert wait on nearly every drain instead of
once per 2000 idle spins.

```text
sm=0 #1  OK 300s  18.4 fps      sm=1 #1  OK 300s  16.7 fps
sm=0 #2  OK 300s  19.1 fps      sm=1 #2  OK 300s  18.8 fps
sm=0 #3  OK 300s  18.2 fps      sm=1 #3  OK 300s  16.6 fps
```

**No freeze in either arm.** So this says nothing about `STRONGMEM`, and nothing
about the cause. It is 30 minutes of accelerated exposure against a fault that
has been seen three times in about six hours of running.

What it does weakly suggest: lowering the spin count by 2000x did not provoke it.
If the fault were on the submit/alert boundary, making that boundary constant
would be the cheapest way to hit it. Not hitting it is a small point in favour of
verdict B -- the CS is fine and the main thread is stuck on something else -- but
one null soak is not evidence, and it is recorded as a null.

A side observation, not a measurement: `STRONGMEM=1` averaged 17.37 fps against
18.57, about -6.5%. One sample per cycle on a route that walks, so the scene
moves between arms. If the hypothesis ever revives, that cost needs its own fixed
-scene A/B before anyone pays it.

### 25.1 What to do instead

The freeze has occurred three times, every one of them during real play rather
than under a harness. So stop trying to provoke it and instrument the thing that
does provoke it: put the patch-52 census DLL in the play configuration with
`MGS2_CS_DEADLOCK_CENSUS=1` and the stock spin count. The census only records
sync events -- submits, alerts, wait enter/return -- not draws, so the cost is
negligible, and the next natural freeze answers A or B by itself instead of
being one more capture that cannot distinguish them.

Two harness defects were fixed on the way here and are worth keeping fixed:
results are written to `/storage` because this console reboots and `/tmp` is
tmpfs (one whole soak was lost that way), and each cycle is written as it
finishes rather than at the end.

## 26. The class-B/C resolver works; arming `wined3d_buffer_load` does not, yet

### 26.1 What is now built and verified live

The §20 census said every hot indirect target inside the island's closure is a
function in wined3d.dll itself -- 21,433,346 of 21,433,463 calls. That makes the
translation a table rather than a bridge, and the table now exists and runs.

`harness/island/full/gen_class_b_table.py` reads the exact pair of builds and
emits `box86-src/src/mgs2_island_class_b.h`:

```text
i386 wined3d.dll functions      6983
defined by the WineD3D objects  1794
name-matched in both binaries   1737
  of those, from WineD3D        1721   <- the table
  rejected, not from WineD3D      16   (calloc, __popcountsi2, __wine_dbg_header, ...)
opengl32 GL entry points         379   <- class C
control check                   PASS
```

The 16 rejects matter. A name matching in both binaries proves nothing about
where the code came from; mapping `calloc` would hand a guest allocator call to
the host allocator, which is the trap that keeps `_recalloc` an abort stub. So a
name is mappable only if an island WineD3D object defines it.

Verified on the device with `box86-island18` + `wined3d_p55_glinfo.dll`:

```text
MGS2 class-B: armed, guest wined3d base 0x7b770000, 1721 mappable functions,
              agreed by wined3d_texture_from_resource and wined3d_buffer_invalidate_location
MGS2 island: site 0 0x7b8eaaf0 -> B wined3d -> 0x62b450b5
```

Two independent witnesses agreeing on one module base is the guard against a
mismatched DLL: without it the table would return plausible wrong addresses
silently, which is worse than not resolving at all.

Class C needed a separate fix. `GL_EXTCALL(f)` expands to
`(gl_info->gl_ops.ext.p_##f)` -- token pasting makes the macro argument the whole
call expression, so the pointer cannot be wrapped at the call site. The fix is
`mgs2_island_gl_info()`: copy the guest `wined3d_gl_info` once, walk `gl_ops` as
`void**`, resolve each non-NULL slot, cache on the guest pointer. Bulk
translation uses `mgs2_island_try_resolve()`, which returns NULL rather than
aborting -- `wglGetPixelFormat` is genuinely unresolvable and must not kill the
table.

### 26.2 The blocker, and what the diagnostic actually showed

With `MGS2_BOX86_ISLAND_ONLY=1,3,9,10,22,32,33` the run dies at:

```text
MGS2 island: assertion failed: cs->thread_id == GetCurrentThreadId(),
             dlls/wined3d/wined3d_private.h:4863
wine: Assertion failed at address 4002005B (thread 0130)
```

That is `wined3d_from_cs()`: the caller must be the CS thread. The TEB
diagnostic in `mgs2_island_teb()` printed, four times, identically:

```text
MGS2 teb: emu 0x7e390708 fs 0x3ffa2000 teb 0x3ffa2000 id 0x134 (host tid 1932521760)
```

**This diagnostic does not answer the question, and reading it as `0x134 != 0x130,
therefore the TEB is wrong` would be an error.** The printer is capped at
`shown < 4`, and all four prints carry the same `pthread_self()`. So the budget
was spent on one thread's first four calls, and the thread the assert fired on
(`0130`) was never sampled. The four prints are consistent with the TEB being
entirely correct.

Two structural checks that the prints *do* pass, and which should not be
re-derived:

* `fs == teb == 0x3ffa2000`. On Wine i386 the FS base *is* the TEB base and the
  self-pointer at `fs:0x18` points back at it. Equality is the correct result,
  not a symptom.
* `id` is read at `teb + 0x24`, which is `ClientId.UniqueThread` on the i386 TEB
  (`ClientId` at 0x20, `UniqueProcess` 0x20, `UniqueThread` 0x24). Correct offset.

So the live hypothesis is the plain one: a routed entry in the set above is
genuinely reachable from the main thread as well as the CS thread, and the
assertion is telling the truth. `wined3d_buffer_load` sits behind
`wined3d_from_cs()`, so it is exactly the kind of entry that would show this.

### 26.3 The next instrument, not the next guess

The diagnostic must be rekeyed before another run is spent: print **on mismatch**
rather than on a first-four budget -- i.e. record the entry id and both thread
ids at the point the island is entered, and print only when the entering thread
differs from a previously seen one for that entry. That distinguishes the two
readings in a single run:

* an entry entered from two distinct thread ids -> the assert is correct, and
  that entry must be dropped from the routed set (or routed only when the caller
  is the CS thread);
* one entry, one thread id, assert still firing -> the TEB path is at fault
  after all, and `thread_get_emu_nocreate()` is the place to look.

Until that run happens, **no claim is made about which it is.** The resolver
itself is not implicated by this failure: it armed, agreed on the module base,
and resolved a live dispatch correctly before the assert.

### 26.4 State left on the device

Production is unchanged and verified byte-wise after this work:
`box86-island10` + `wined3d_p52_cs_census.dll`, 14 island entries matched,
0 faults, GPU governor `performance` @ 800 MHz with save/restore on exit. The
class-B work lives in `box86-island18` + `wined3d_p55_glinfo.dll`, which are
**not** wired into the launcher and default to off.

No combat-performance number was produced by this line of work. The only
measured gain in this session remains the GPU governor, +10.8% (§23).

## 27. Two stale-table bugs, and the island reaches the game

§26 ended by refusing to guess which of two readings explained the failure. The
instrument was rekeyed and answered in one run -- then the answer turned out to
be neither, and the real cause was upstream of both.

### 27.1 The thread hypothesis is dead, and the first instrument was useless

Printing on each DISTINCT host thread rather than on the first four calls:

```text
MGS2 teb: host thread 1 of 8: pthread 732ff120 -> emu 0x7df96f38, teb 0x3ffa2000, guest id 0x12c
wine: Unhandled page fault on read access to 00000000 at address 4002005B (thread 012c)
```

One host thread, and its guest id `0x12c` is exactly the thread Wine names in
the fault. So `thread_get_emu_nocreate()` returns the calling thread's emu and
the TEB path is correct. Both §26.3 branches are closed.

Note the key had to be `pthread_self()`. Keying the dedup on the guest thread id
-- as the first rewrite did -- cannot distinguish "one thread enters" from "the
emu lookup is not per-thread", because the guest id is the value under test. It
reported "thread 1 of 8" either way. **An instrument keyed on the quantity it is
testing measures nothing.**

### 27.2 The class-B table was stale, and pointed at a real wrong function

The fault site is not `4002005B` -- that is the bridge return bookmark. The
crash frame is:

```text
MGS2 dispatch: site 0 0x7b8eaaf0 -> B wined3d -> 0x62b450b5
SIGSEGV @0x62b450c0 ... for accessing 0x1c7c
```

`0x62b450b5` is odd, so Thumb, function start `0x62b450b4`; the crash is 12
bytes in. But in the binary that actually ran, `wined3d_buffer_gl_prepare_location`
was at `0x62b45325`. `0x62b450b5` was 16 bytes inside `wined3d_buffer_destroy_object`.
The island called the destructor with `prepare_location`'s arguments.

Cause: **the generated table lists ARM addresses of functions in the very binary
it is compiled into.** Any source edit shifts them, so the table shipped in that
build is stale by construction. Generation must run to a fixpoint and nothing
enforced it -- which is why island19 and island20 crashed at different addresses.

Two things now prevent a silent recurrence:

* `harness/island/full/fixpoint_class_b.sh` regenerates and rebuilds until two
  successive tables agree. I predicted one iteration, reasoning that a
  fixed-size table cannot move `.text`. Measured: **three**. The loop caught my
  own wrong reasoning, which is the argument for having it.
* `mgs2_class_b_native_matches()` compares the table's ARM address for each
  witness against `mgs2_island_entries[].impl`, which Box86 holds independently.
  On disagreement it refuses to arm. Refusing costs the speedup; arming on a
  stale table corrupts memory and blames something else. Live: `MGS2 class-B:
  native side verified, 4 witness(es) agree with this binary`.

The witness check that already existed could never have caught this: it
validates the GUEST module base only, and the native half is the half that
rots.

The fixpoint script had its own false-fixpoint bug on the first run -- the
generator was piped to `tail`, so a crash left the header untouched and the loop
declared convergence. The exit status is now taken from the generator directly.
The same trap has now appeared twice in this project.

### 27.3 Class C was keyed on addresses, which cannot work

With the class-B table correct, the save loaded and the game played 12 steps,
then died reading address 0. Cause:

```text
MGS2 gl_ops translated: 3114 slots, 2621 null, 3 resolved, 490 UNRESOLVED
```

Unresolved slots were written back as NULL, so the first real `GL_EXTCALL`
through one dereferenced it. Two separate faults produced that 3:

* the class-C table was generated from the reference wineprefix's `opengl32.dll`,
  not the one **mounted on the device**. Same `ImageBase`, different build --
  1.8 MB vs 4.9 MB, 380 vs 391 exports. Regenerating from the device's DLL took
  it from 3 to 88. The identical class of error as the class-B table, found the
  same day.
* even against the right DLL, 88 is the ceiling: extension entry points are not
  exports at all. They are internal thunks Wine's opengl32 builds for
  `wglGetProcAddress`, so no export table can name them.

**Addresses were the wrong key.** `gl_ops` is generated from `ALL_WGL_FUNCS`,
`ALL_GL_FUNCS`, `ALL_WGL_EXT_FUNCS`, `ALL_GL_EXT_FUNCS` on both sides, so a
slot's POSITION already carries its name, by construction, with no table to go
stale. `mgs2_gl_slot_name[]` expands those lists in declaration order and
`mgs2_island_gl_by_name()` resolves via `dlsym` then `eglGetProcAddress` against
the already-loaded driver. A `C_ASSERT` ties the array length to
`sizeof(struct wined3d_gl_funcs) / sizeof(void *)`, so a future shift between
names and slots fails the build rather than aiming every GL call one slot off.

Result: 3 -> 88 -> **233 resolved**, 260 still unresolved and not reached on
this path.

### 27.4 The island now runs the game

`box86-island23` + `wined3d_p55_glinfo.dll`, entries `1,3,9,10,22,32,33`,
autoloaded to the measured heavy save:

```text
инстансов=1   реальных сбоев 0
медиана 17.10 fps   n=5   min 16.20   max 17.30
```

**`wined3d_buffer_load` is armed and survives real play.** This is the first
time the routed island has reached in-game frames at all.

No performance claim is attached to that 17.10 yet -- it is one arm. The A/B is
running as a controlled pair: same binary, same DLL, the only difference being
island entry 10, since the whole prize is the dispatch closure behind it.

A counting defect corrected on the way: the run script's fault grep matched
`fixme:dmime:...Unhandled message type`, inflating 1 real fault to 19. It now
matches `^wine:`, `forbidden instruction`, `assertion failed`, `STALE TABLE`.

## 28. The A/B on the routed buffer_load, and why three arms were not enough

Controlled pair: one binary (`box86-island23`), one DLL (`wined3d_p55_glinfo.dll`),
one autoloaded save. The ONLY difference between arms is island entry 10,
`wined3d_buffer_load` -- the entry whose closure carries the 4821.9 calls/frame
dispatch. Arms alternate inside one session; 180 s window each, medians over
whole `MGS2_GL_STATS` samples, taken after the save is loaded.

```text
order   arm            median   n    min     max
A1      with 10        18.60    11   17.60   18.80
B1      without 10     16.70    10   14.70   16.90
A2      with 10        16.75    10   15.80   16.90
B2      without 10     17.30    11   16.30   17.50
A3      with 10        18.90    12   16.70   19.10
```

### 28.1 A conclusion drawn at three arms, and withdrawn at five

After A1/B1/A2 the reading looked settled: A2 (16.75) sat on B1 (16.70), not on
A1 (18.60), so A1 was a cold-console outlier and the effect was drift --
+0.05 fps, nothing. That is what the first three points say, and it is what I
concluded.

Five points say something else. B2 came in at 17.30, ABOVE the "with" run A2,
and A3 at 18.90, the highest of all. Grouped:

```text
with 10      18.60  16.75  18.90
without 10   16.70  17.30
```

Two of three "with" arms are clearly above both "without" arms, which is not
what monotone thermal decay produces. **The three-arm conclusion was withdrawn.**

### 28.2 Nine arms: no measurable effect

Four more alternating arms were run. `A4` autoloaded but produced no samples in
its window and is recorded as lost, not dropped -- eight arms remain.

```text
with 10      18.60  16.75  18.90  16.45     median 17.68   range 16.45-18.90
without 10   16.70  17.30  18.80  17.05     median 17.18   range 16.70-18.80
```

**The ranges overlap almost exactly.** Median difference +0.50 fps, mean
difference +0.22 fps, against a within-arm spread of about 2.4 fps on BOTH
configurations. `B3`, with entry 10 disabled, produced 18.80 -- level with the
best routed arm.

Routing `wined3d_buffer_load` to native ARM therefore shows **no measurable
frame-rate effect on this route**. Recorded as a null with its numbers.

Two of my own readings along the way are superseded by this and should not be
quoted from the log:

* at three arms I called it drift and put the effect at +0.05 fps. The reasoning
  was monotone thermal decay, and `B3` at 18.80 refutes it. Right answer,
  wrong mechanism.
* at five arms I said two of three routed arms sat above both unrouted arms and
  that an effect looked likely. `B3` and `A5` removed that pattern entirely.

Both were drawn while the spread was already known to be larger than the effect.
The lesson is not about thermals: **do not read a direction out of a sample
whose within-group spread exceeds the difference being looked for**, however
suggestive the ordering looks.

### 28.2.1 The route cannot answer this question

The predicted prize for this cut was +1.1 to +2.3 fps (section 14). The route's
own run-to-run spread is 2.4 fps, so it cannot resolve the effect it was built
to measure, in either direction. This null does not say the island is worthless;
it says this instrument is too blunt to weigh it.

The cause is the scene, not the clock. `autoload_save.py` loads the save and then
walks, and where the walk ends differs per run; the route was chosen for being
heavy, not identical. Before this question is reopened, the measurement needs a
scene that does not move -- load, hold the camera fixed, measure a short window
before anything in the world reacts -- and enough arms to show the spread has
actually collapsed. Adding arms to the current route is not worth the battery.

### 28.3 What is settled regardless of the fps outcome

* The island runs the game. `wined3d_buffer_load` is routed to native ARM,
  reaches the reinforcement save, and plays with **zero faults** across five
  180 s in-game windows.
* The class-B and class-C tables are correct and self-checking: a stale table
  now refuses to arm instead of calling a wrong function, and slot names are
  tied to `sizeof(struct wined3d_gl_funcs)` by `C_ASSERT`.
* 233 of 493 non-null GL slots resolve by name; the remaining 260 are not
  reached on this path.

## 29. Identity is not an address, and the same-process A/B answers the question

Research reviewed §26-28 and changed the next two steps: do not go looking for a
better save first, and do not keep the class-B fixpoint. Both calls were right,
and following them in that order produced the first real number for the island.

### 29.1 The class-B fixpoint is gone, not made safer

§27 fixed the stale-table failure with a rebuild-until-stable loop and a runtime
guard. That treated the symptom. The disease was the self-reference:

```text
guest RVA -> absolute ARM address, read out of the linked binary
          -> compiled back into the binary it was read from
```

The table now maps **guest RVA -> symbol ID**, and the ARM addresses come from
the linker. Each island translation unit gets a generated fragment appended that
takes the address of every mappable function it defines and drops an
`(id, address)` pair into one section; the runtime walks the section once and
builds the array. 916 of the mapped names are `static`, which is why the
fragment has to live inside the TU -- a central file cannot name them.

`fixpoint_class_b.sh` is deleted. `build_island_objects.sh` does two passes, and
they are not a loop: pass 1 exists only so the generator can read which names
each TU defines, and appending a registry changes no name, so pass 2 cannot
invalidate pass 1. It terminates by construction.

Verified statically before any device run -- RVA `0x0017aaf0` -> id 757 ->
`0x62b51e45`, which is exactly where `readelf` puts
`wined3d_buffer_gl_prepare_location`; 0 unregistered IDs -- and then live:

```text
MGS2 class-B: 1614 native IDs registered by the linker
MGS2 class-B: armed, guest wined3d base 0x7b770000, 1614 mappable functions
MGS2 dispatch: site 0 0x7b8eaaf0 -> B wined3d -> 0x62b51e45
```

### 29.2 The old table had 110 unsound entries, and clones are the interesting ones

Rebuilding the mapping on names surfaced something the address version had been
carrying silently. Of 1721 matched names, **110 must not be mapped at all**:

```text
56   compiler clones      .isra.N  .part.N  .constprop.N
 3   several island TUs   wine_dbg_vprintf is defined in 31 of the 32
51   several guest addrs  the same statics, on the PE side
1614 MAPPED
```

The clones are the dangerous class and were not previously identified. They are
not the source-level function: GCC invents them per translation, with signatures
it chooses -- `.isra` replaces aggregate parameters with scalars, `.constprop`
deletes parameters it propagated, `.part` splits a body at a compiler-chosen
point. i386 mingw-GCC and armhf-GCC make those choices independently, so
`foo.isra.0` on the two sides are unrelated functions sharing a mangled name.
One of them, `wined3d_from_cs.part.0`, sits on a hot path.

### 29.3 The same-process A/B, and the answer

Research's main methodological point: stop running separate playthroughs and
switch the entry inside one live process, on displayed-frame boundaries, ABBA,
with both arms passing through the same gate.

Built as `MGS2_ISLAND_AB=<entry id>`. Entry 10 gets its own wrapper; both arms
enter the same bridge and read the same argument slots off the guest stack, and
only the last step differs -- native ARM function, or the guest's own body under
the emulator. Reaching the guest body is safe here, which was checked rather
than assumed: `DynaCall` sets `R_EIP` directly and `hasAlternate()` consults only
the alternates hash map, which marker-matched island entries were never added
to, so it does not re-enter the bridge.

The frame tick is **not** `eglSwapBuffers`. This port does not present by
swapping: winewayland's `wayland_drawable_swap()` reads the finished frame back
with `glReadPixels` into a wl_shm buffer, which is why the launcher's own line
reports `readback 7.2 ms/f`. Ticking on `eglSwapBuffers` produced zero ticks
across a whole 480 s run, and that is what pointed here.

51 cycles, of which 37 in-game and 30 with the two arms' `buffer_load` call
counts within 2% of each other:

```text
routed      60.6 ms/f
unrouted    69.4 ms/f
difference  median -8.87   mean -9.38   sd 2.39   -12.8%
range       -21.65 .. -7.69, and 30 of 30 cycles favour the routed arm
```

Standard error 2.39/sqrt(30) = **0.44 ms/frame**, against research's stated
requirement of paired sigma below about 1 ms. In frame-rate terms 14.4 -> 16.5
fps, **+2.1 fps**, inside the +1.1..+2.3 predicted in section 14.

**So routing `wined3d_buffer_load` natively is worth about 9 ms/frame, and the
§28 null was an instrument failure, not a result.** Eight separate playthroughs
could not see a 9 ms effect because the scene moved between them by more.

The call count turned out to be the covariate that matters. Cycles where the two
arms' call counts diverge show wild differences in both directions; filtering to
balanced cycles collapses the spread from sd 8.67 to 2.39 without moving the
median (-8.83 -> -8.87). Recording it per block, as research specified, is what
made the result readable.

### 29.4 A check of mine that proved nothing

The first version of the harness reported a "tick rate check": that the frames
counted per arm equalled `2 * (BLOCK - SETTLE)`. **That is circular** -- the
blocks are defined in ticks, so it holds no matter what the tick counts. It has
been removed rather than left to give false assurance.

The real check is external, and it passed: over 51 cycles the mean interval came
to 51.0 ms against 51.1 ms from the launcher's `MGS2_GL_STATS` counter, which is
produced by different code on the other side of the emulator. The cumulative
tick count is now printed so that comparison can be repeated from any log.

This is the third time in this project a check has been built out of the thing
it was meant to test -- after the guest-thread-id diagnostic key (§27.1) and the
witness that validated only the guest half of the mapping (§27.2). It is worth
stating as a standing rule: **a control must not be computed through the
mechanism it is controlling.**

### 29.5 Corrected in passing

Mid-analysis I read `16.670 ms/f` in an early cycle, compared it against the
~51 ms in-game frame time, and called the instrument broken by a factor of 3.6.
It was not: those early cycles are the title screen at the 60 Hz cap, where
16.7 ms is the correct answer. The external check above settled it.

## 30. The input stall is a page-fault storm, and box86's mitigation is single-threaded

Reported during play: the character walked left on its own, controls stopped
responding, sound was gone. Diagnosed live, without killing the process.

### 30.1 What it was not

Ruled out by measurement, in this order, and several of these were my own wrong
guesses before the data arrived:

```text
the CS deadlock freeze   no -- census: queues ADVANCING, CS thread not blocked
my harness left running  no -- no processes, no stray uinput device
a stuck key              no -- EVIOCGKEY on the fake keyboard: nothing held
a stuck analog axis      no -- EVIOCGABS: every axis centred
audio pipeline dead      no -- mixer accumulating CPU, box86 a live PipeWire
                                client, sink unmuted at 0.80
the frontend stole input no -- EmulationStation idle at 4.9%, nobody holds js0
lost window focus        no -- sway reports the game surface focused
input not delivered      no -- evtest: BTN_DPAD_LEFT -> KEY_LEFT, 534 events
```

A screenshot settled the framing in ten seconds and should have been the FIRST
step: the game was on its own MISSION FAILED screen with the cursor on CONTINUE.
The "walking left" was the death, the silence was the scene, and "unresponsive"
meant the menu ignored input. I spent an hour measuring threads before looking
at the screen.

One reading was worse than useless. An early `EVIOCGKEY` showed `BTN_MODE` held,
and I built a stuck-Home-button story on it. A later sample showed nothing held:
it was transient, and I had treated a single sample as a state. The user's
pushback -- "unlikely, and you are ignoring the audio" -- was correct on both
counts.

### 30.2 What it is

Synthetic keys delivered to the focused window did not move the menu cursor
either, so the game genuinely processed no input. `perf` on the one thread that
was busy:

```text
22.9%  rb_get
17.7%  FindDynablockFromNativeAddress
 5.7%  getProtection
 4.8%  getAlternate
 4.1%  Run                        (the interpreter)
```

All box86 internals; the `[unknown]` samples resolve into the armhf libc. The
thread was not executing guest code, it was thrashing block lookup. The cause:

```text
wine_dinput_wor   4373 page-faults / 4 s   (~1100/s)
wined3d_cs           0
main thread          0
```

Wine's DirectInput worker writes to a page that also holds translated code.
Box86 write-protects such pages to detect self-modifying code, so every write
faults, invalidates and re-translates. The thread stays alive and makes almost
no progress -- indistinguishable from a hang, and confined to one thread, which
is why rendering continued normally.

### 30.3 Why box86's own mitigation does not engage

Box86 has a hot-page mechanism for exactly this. It cannot work under this load:

```c
uintptr_t hotpage = 0;      /* one global address for the whole process */
int hotpage_cnt = 0;        /* one shared counter */

int isInHotPage(uintptr_t addr) {
    if (!hotpage_cnt) return 0;
    --hotpage_cnt;          /* decremented on EVERY call, from ANY thread */
    return (addr >= hotpage) && (addr < hotpage + box86_pagesize);
}
```

The budget is 64 calls and it is spent by every thread, including ones with no
interest in that page; the address itself is overwritten by the next unrelated
fault. With four active threads it drains immediately. The mechanism assumes a
single-threaded workload.

The fix direction is to make `hotpage`/`hotpage_cnt` thread-local and decrement
only on an address match. **Not done** -- that is box86 core surgery, and the
release is deliberately frozen.

### 30.4 One defect of mine, found on the way

In `getAlternate()` the island marker scan was **not gated**, unlike the two
blocks above it which test their own pointer first. A readability probe plus up
to 65 `memcmp` calls therefore ran on every branch target the dynarec
translated, on every thread, **even with the island switched off**. Gated on a
flag set when any island bridge registers, plus a first-byte reject so `memcmp`
is reached about once per 256 window positions instead of 65 times.

**Deployed as `box86-island29`.** I first held it out of production, reasoning
that the release was frozen and that 4.8% of a pathological profile does not
justify re-cutting a known-good set. That was the wrong call and the owner said
so: the freeze was about new optimisation and architectural change, not about a
defect I had introduced myself. Corrected -- launcher, manifest and
`FINAL_PRODUCTION.md` all moved to island29.

The gate carries an ordering hazard that had to be checked rather than reasoned
about: `mgs2_island_armed` is set when a bridge registers, so if
`getAlternate()` ran before registration no entry would ever match and the
island would silently do nothing -- quietly giving back the whole 8.87 ms. On
the device: 15 entries matched, entry 10 among them, 0 faults, 19.10 fps median.

### 30.5 State

Fixed and shipped: the ungated scan. Not fixed: the fault storm, and therefore
the stall itself -- island29 does **not** address it. If it recurs, the
experiment is ready and the measurement is already done; only the effect of a
thread-local hot page needs measuring.

Two tools added, both reading kernel state rather than inferring from event
history: `harness/keystate.py` (EVIOCGKEY) and `harness/axisstate.py`
(EVIOCGABS). Neither existed, which is why the first guesses were guesses.

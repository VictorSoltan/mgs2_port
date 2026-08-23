# MGS2 Substance on the Anbernic RG353VS — FINALPLAY11

Promoted 23 August 2026, replacing FINALPLAY9. FINALPLAY9's own record follows
below the FINALPLAY10 section and is unchanged: the presenter and the separable
stage selector are carried forward as they were, and this release adds the
native dither converter on top of them.

FINALPLAY9 was promoted 22 August 2026, replacing FINALPLAY6's `island41` /
`p56` pair. The owner authorised promotion after playing the exact binaries for 144
minutes, and the launcher was then exercised through the ordinary entry point
(`MGS2-Substance.sh`, no environment overrides) to prove the defaults, not a
hand-built command line.

```text
box86      box86-fp11                   (MGS2_BOX86_NATIVE_DITHER=1)
           ea3e367d71703039bd4a10b32e34b6c6f331b104f4316bc7180dfbf22052d120
wined3d    wined3d_fp11.dll
           b35529b0ba4570bac910763f4c0180bac61d3648ab3a4033e718de5e31d02706
presenter  winewayland_dmabuf_prod.so   (MGS2_GL_DMABUF=1, SYNC=3) -- unchanged
           51879e2d706d434e3bf140508e31493802d9506753a16b295be81df154f9f169
island     0,1,2,3,4,5,6,9,10,14,18,19,22,23,28,29,32,33,41
```

`launch-play.sh` now hashes the three MOUNTED files against those values before
it starts the game and refuses to run if any differs, saying which. Overrides
downgrade it to a notice, because that is how experiments are run. The class-B
registry made this worth automating: it maps guest WineD3D RVAs, so a mismatched
pair does not fail cleanly, and "almost FINALPLAY10" is the worst thing to
profile.

## What FINALPLAY11 adds

### The FFP light-colour cache, now on

Three colour uniforms per light -- diffuse, specular, ambient -- cached per field
in `mgs2_ffp_vs_source`, the object that owns `stage_program`. That owner is the
point: sharing it across separable entries is exactly what corrupted the picture
in P74A, and the key here is `(vs_program_id, light, field)`, which is what GL
attributes the state to.

It was held back in FINALPLAY10 for want of an ms/frame verdict. It has one now,
and getting it required fixing the instrument first:

* **The frame denominator.** `FRM1` counts presented frames inside
  `wined3d_swapchain_present()` and reports each A/B arm separately. The old
  denominator was scraped from the game log, which emits one line per N frames,
  so any window reported a multiple of N no matter how long it really was.
* **The statistic.** The first UCT reading said the cache arm was SLOWER while
  doing almost no work, and the second said the opposite. Both were means over a
  few hundred 20 us intervals, where one preemption moves the mean by
  microseconds. The record now carries a histogram and the reader takes a median.

```text
arm A (cache off)  median 19.5 us per three-field group, 3.000 uploads
arm B (cache on)   median 14.5 us per three-field group, 0.029 uploads
                => 1.68 us saved per glUniform4fv removed
```

That is ~0.04 ms/frame in a quiet scene, which is nothing, and ~0.7 ms/frame in
combat, where the same path attempts 552 uploads per frame at 87% redundancy. A
miss costs three 16-byte memcmps. The 1.68 us is also a reusable constant: it
converts "calls removed per frame" into ms/frame for every later candidate.

### The Mali shader freeze: measured, attacked, and CLOSED with proof

The 0.5-1.1 s freezes are real and the diagnosis held up -- but the census
changed what to build. In one run the probe recorded **12 separable-stage LINKS
costing 2.0 s against 16-88 ms for all the compiling**. The expensive thing is
linking, not compiling, and every source in a run is distinct, so a cache living
inside one run has nothing to hit. The only shape that could pay was persisting
linked binaries between runs.

That was built: `glGetProgramBinary`/`glProgramBinary` keyed on the GLSL text,
the stage, the bound attribute indices and a hash of GL_VENDOR/RENDERER/VERSION,
stored under `shadercache/`. It does not work here, and the reason is not a bug
in the cache:

```text
roundtrip_tried  1        in-memory: store the blob, hand it straight back
roundtrip_ok     0        to glProgramBinary on a fresh program, same context
roundtrip_err    0        no file, no key, no persistence involved
```

The driver reports a binary length, returns 12280 bytes in its own format
0x8f61, raises **no GL error** on reload, and leaves LINK_STATUS false. Twelve
file-backed loads behaved identically. **This Mali driver does not reload its own
program binaries.**

So the cache ships OFF (`MGS2_GL_PROGRAM_CACHE=1` to try it) with its accounting
record `PBC1` intact. Retesting after a driver update is one run: set the switch
and read `roundtrip_ok`. Nothing else about that branch is worth building until
that flips.

## What FINALPLAY10 added: the load freeze is 23% shorter

Everything here is about the multi-second freeze after a save loads, which four
unattended captures showed is not one problem but three. Full diagnosis in
`docs/briefs/` and in the project memory; the short version:

* **Long, 4-7 s** -- the game's own code on the main thread. `wined3d_cs` sleeps
  on a futex throughout and does no GL at all.
* **Short, 0.5-1.1 s** -- Mali shader compilation. Untouched by this release.
* **Rare hangs** -- a different thing again, and still open.

Measured NOT to be the cause, each of which looked plausible first: the
compositor (wait 0.01 ms/frame), the SD card (0.3 s of `mmc_blk_rw_wait` in
200 s), swap and zram (6 major faults per run), memory pressure (identical minor
fault rate in and out of freezes), and Box86's JIT compilation (2.76% of freeze
cycles). During a freeze only ~1.4 of 4 cores are busy: serialisation, not
saturation.

**The change.** 44.7% of the main thread's CPU during those freezes is a single
guest function, `mgs2_sse_rg353vs_port.exe+0x50dae1` -- float RGBA to packed
RGBA8 with a 4x4 ordered dither, one pixel at a time in scalar x87, which Box86
emulates instruction by instruction. It is now a native ARM routine, reached
through the bridge mechanism of box86-patches 05/06.

**What it is worth.** Two ABBA cycles, eight autoload runs, one binary and one
environment variable apart:

```text
converter off   18539  18035  21871  19083   mean 19382 ms of long stalls
converter on    16427  15839  11461  16143   mean 14968 ms
```

Every ON run is faster than every OFF run -- complete separation, exact p ~= 0.03
-- for **-4.4 s per load, about 23%**. That matches the 4.2 s the profile
predicted before the patch existed, which is the check that matters.

**Two things this release does not claim.** The remaining ~70% of the long
freeze is other guest work, untouched. And the short Mali-compile freezes are
untouched; they want a program-binary cache, which is a separate patch.

### Correctness, and the bug the oracle caught

The rewrite has to be bit-identical, not close. The guest sets x87 RC=11 before
the loop, and the first version read that as "FISTP truncates" -- but RC is in
the control word and governs *every* x87 rounding, including the FADDS and the
FSTPS that narrows to single precision. Rounding those to nearest puts
127.99999991 exactly on 128.0f and returns one more than the guest.

Two on-device differential attempts failed structurally: calling the original
from inside the bridge makes the dynarec own a block for that address, after
which indirect calls stop consulting the hook, so the run compares one call
instead of 16384. The answer was to leave the device: `harness/dither/x87_oracle.c`
runs the guest's exact instruction sequence on real x87 on the build host and
compares it against the rewrite. It found 24 mismatches in 8 million inputs, and
zero after the fix, at both 53-bit and 64-bit precision control.

The on-device self-test carries one probe -- 254.5/255 with dither 0.5 -- that
returns 254 under truncation and 255 under round-to-nearest, so it fails loudly
if the rounding mode ever stops being applied on ARM. It passes.

### Shipped dark

`mgs2_ffp_vs_source`'s three-field light-colour cache is built, holds identity
and uses the right key, but never got an ms/frame verdict -- the A/B that would
have given one was overtaken by the freeze work. It ships with `enabled = 0`.
Flip that and `mgs2_asp_ab_enabled` to finish the measurement.

The two halves must not be rebuilt independently: the class-B registry inside
box86 maps guest WineD3D RVAs, so it is valid only for this exact DLL. Rebuilding
one side alone produces `class-B: site 0 dispatches to ... not a mappable WineD3D
function` and an assert at startup.

## What this release adds, and what it is worth

**P75A, the lazy separable stage selector** (`wine-patches/75-separable-lazy-stage-selector.patch`).

With separable programs `shader_glsl_load_constants()` called
`mgs2_glActiveShaderProgram()` twice unconditionally -- once for the VS program,
once for the PS program -- whether or not either block uploaded anything. It is a
patch-27 function pointer rather than a `GL_EXTCALL` site, so no census in this
project had ever counted it. It now runs only when an upload actually follows.

```text
combat, same-process ABBA, 12-frame blocks
    selector calls   1571.8/frame -> 191.6, avoided 1380.3 (87.8%)
    frame time       71.54 ms -> 56.74 ms
    delta            -14.80 ms/frame, 95% CI [-19.49, -13.66]
    fps              13.98 -> 17.63   (+26%)
    p95/p99          -15.35 ms  (tails improve with the mean, not against it)
    sign test        14 of 14 cycles, p=0.0001
    negative control +0.000 ms, CI [-0.015, +0.018]
    mirror check     MISSED VS 0 / PS 0
```

The mirror check was weaker than it read at first and was corrected before this
record was written: the witness was raised in ONE helper and only the VS side was
compared, so "MISSED = 0" spoke for a fraction of the uploads. It now covers all
69 uniform-upload sites in glsl_shader.c and both stages, and reads VS 0 / PS 0.
The -14.80 ms is unaffected -- the instrumentation was symmetric across arms, so
the timing was never in question, only the strength of the correctness claim.

Entry 41, the fused A+B+C draw-state root (p72c), ships with it. It was a
candidate before today and is promoted here only because the validated session
ran with exactly this island list; its own magnitude remains the post-hoc
estimate of -4.8 ms and is NOT claimed as measured.

## The presenter, added on top of FINALPLAY8 the same evening

The frame is blitted GPU-to-GPU into a dma-buf from `/dev/dma_heap/linux,cma` and
handed to sway by file descriptor, instead of being read back through the CPU
into a wl_shm buffer. The GPU write fence is imported into the buffer with
`DMA_BUF_IOCTL_IMPORT_SYNC_FILE`, so the compositor waits for the blit and the
game does not -- sway advertises no explicit-synchronization protocol, and
without that import the picture tears like vsync off.

```text
measured on FINALPLAY8, same-process ABBA, 12-frame blocks, owner playing
    shm arm      71.03 ms (14.08 fps)
    delta        -9.45 ms/frame, 95% CI [-10.95, -8.29]
    fps          14.08 -> 16.24
    p95/p99      -9.65 ms
    sign test    19 of 20 cycles, p<0.0001
    negative control +0.020 ms
    fence fail create/dup/import 0/0/0
```

The win survived P75A and its interval halved against the pre-FINALPLAY8
measurement, so the present path and the selector path are independent.

`MGS2_GL_DMABUF=0` falls back to the shm presenter at runtime, and
`winewayland_stall1.so` is untouched on the device.

### Why this shipped with the stability question OPEN

Two hangs on 2026-08-22 were caught on dmabuf builds. A paired soak was run to
find out whether it hitches more than shm -- same session, interleaved arms,
startup excluded by a rule fixed in advance, and only the >200 ms and >500 ms
buckets compared, because at 15 fps every ordinary frame exceeds 50 ms and the
slower arm would otherwise look like it hitches constantly.

```text
7 complete cycles, arms balanced at 3528 frames each
per 1000 frames      >200 ms   >500 ms
    shm                 1.42      0.57
    dmabuf              0.57      0.28
    difference        -0.850    -0.283      (dmabuf hitches LESS)
no freeze during the soak
```

**The pre-declared gate of ten cycles was NOT met, and this is not a clean
bill.** Behind those rates are single-digit event counts -- 5 against 2, and 2
against 1 -- and five minutes of dmabuf arms cannot measure a hang rate of about
two per day. What the soak establishes is only that there is no evidence of harm
and that the direction favours dmabuf. It was promoted on the owner's decision
with that stated, because the win is large, the rollback is one line, and
ordinary play continues the soak.

## What is still open on this release

```text
STALL    a 144-minute session logged five frames over 500 ms: three at startup
         (normal) and two during play, 5816 ms and 784 ms. Whether that rate
         differs from production has NOT been measured -- it needs a paired soak
         counting stalls per hour, and until then the hitches are neither
         attributed to this patch nor cleared of it
counters the shipped DLL still carries the ASP1 counters and the witness. They
         are symmetric across the A/B arms, so the -14.80 ms stands, but stripping
         them is a small free gain that has not been taken
freezes  one hang was captured during the P75A A/B with cs_deadlock_census
         VERDICT B (queues empty, consumer correctly asleep, main thread waiting
         in ntsync) -- a different signature from the verdict-C hangs seen
         earlier the same day, and matching the project's long-standing class
```

## What is measured, and what is not

Only three things in this build have a number behind them. Everything else is here
because the game plays correctly, which is a different and weaker claim, and the
distinction is kept explicit so nobody later reads a correctness decision as a
performance one.

```text
GPU governor = performance      +10.8% fps, ranges non-overlapping
island entry 10                 -8.87 ms/frame, -12.8%, 30 of 30 paired
  (wined3d_buffer_load)         cycles, se 0.44 ms/f  ->  about +2.1 fps
island entry 4                  53.466 routed vs 56.050 guest ms/frame;
  (mgs2_batch_flush)            paired median -2.680 ms/f, +0.899 fps (+4.8%),
                                10 of 10 stable paired cycles, zero faults

the other 15 island entries     correctness-promoted. NO fps claim.
CS deadlock census              diagnostic only. No performance role.
everything else in the stack    earlier work, recorded in docs/briefs/
```

Both island figures came from same-process A/B runs: the selected entry is
switched between
the native ARM route and the guest body every 64 displayed frames, ABBA, inside
one live process. Eight separate playthroughs had previously measured nothing,
because the scene moved between runs by more than the effect did. Reproduce with
`device/launch-island-ab.sh`, never in play — half its frames run unrouted on
purpose. Entry 4 was measured only after two independent module witnesses
agreed on the authoritative guest batch state; the earlier duplicate native
state implementation crashed and is not part of this release.

## The binary set

Verified byte-wise through the real `/storage/roms/ports/MGS2-Substance.sh` on
the device after promotion: all manifest entries passed; the live bind targets
matched `box86-island31` and `wined3d_p56_batch_state.dll`; one game instance
loaded the target save and completed all 12 walk bursts. The island armed 17
entries, 16 were exercised on this route (entry 19 was not encountered), the
class-B resolver armed 1616 linker-supplied IDs, entry 4 shared guest batch state
`0x7ba40040`, and there were **0 island faults**.

`box86-island31` retains the `island29` marker-scan defect fix. The island's
marker scan in `getAlternate()` used to be ungated: a
readability probe plus up to 65 `memcmp` calls ran on every branch target the
dynarec translated, on every thread, **even with the island switched off**. It is
now gated on a flag set when an island bridge registers, with a first-byte
reject ahead of the `memcmp`.

The gate has an ordering hazard worth knowing about if this is ever touched: if
`getAlternate()` ran before the bridges registered, no entry would ever match and
the island would silently do nothing. Checked on the device rather than reasoned
about: 16 entries matched on the FINALPLAY6 smoke route, including entries 4 and
10, with 0 faults; armed entry 19 was simply not encountered.

This does NOT fix the input stall described in section 30 of the frame-budget
brief. That is a page-fault storm on Wine's DirectInput worker (~1100/s on one
thread, zero on all others) and it needs a thread-local hot page in box86, which
is core surgery and is not done.

```text
d1dcffac1f60a2d1c922cddac7ad1980dd316c05237029df187875fb67015c60  box86-island31
6a926918fd40ce2e883dce6465392f8cbe791d474a3822e0408ea907489a7471  wined3d_p56_batch_state.dll
841ff73c2b99fd6ca2ee00b0796abbb9e0d38b584cb298cb9860afbee9ea1de0  d3d8_finalplay3_nocullcache.dll
4f8b82c7a9dd0fab03b699aa8948f6c76852801f17a096cff22384dc2997fe4e  user32_peek1.dll
6acdbbaeb8b88ba64fc160a1faf865ae304108705c38bccadaf6bc538f2be63a  win32u_glfuncs3.so
0aa5dec7d014b17a3735ff713fd08b30effa0d63d7a3f71514d886e6b0051e09  winewayland_stall1.so
9340f708462a29debffec37fe493ad3044afc903ffb6466ddf1f30d46da628af  opengl32_finalplay_sso.so
b4ec2cd09f26a670eb8206d708f864597d2acde84ff1788732574c116b6baed2  dmsynth_p34_interp_reset.dll
302eff548429c6b87aed3931bb0bb1acd4c4c8a130a96ae7025612c2d7eb999c  dsound_p36_native_fir_target.dll
ce3e3f14a62a190966183802c871a5a26a7a3a828c7f23b4d6f0ab9f90ace877  dmime_transition1.dll
1fe0a571503bdd17166474838b83cf54c0f56fe5b44da371ffeb4123ebc8208e  dmusic_shared_lifetime1.dll
```

Launchers:

```text
af35e6a6eea15719534fa39b4657a3eb7b70fd2ac61a2536d5d1933919398a98  launch-play.sh
009bed38696305f4ee2ecfa8b8e1b5556211455b6ab8fee4b08872d17f0d8781  launch-island-ab.sh
1c13c2aa32d817d6f4795b527fc834e6a20881e0d8993477f8f44452f21e689e  MGS2-Substance.sh
```

The system GL stack this was measured against — not shipped, but the island
resolves GL entry points out of it by name, so a driver change invalidates the
measurement even though nothing above would change:

```text
605e3a5caf1be62bb48d97b1168434257355d56db5e3be9b515cfa742c173118  /usr/lib/libmali.so.1.10.0
69cfc7023acff84cac62a171363890a8409933d04eb3ddd0f351d3717383f606  /usr/lib/libEGL.so.1.1.0
aaa1927188636cc8ba30805781ce15f4001fc7b198dfd8a89931e1a2a1d67b55  /usr/lib/libGLESv2.so.2.1.0
```

Verify on the device with:

```sh
cd /storage/roms/ports/MGS2-Substance && sha256sum -c FINAL_PRODUCTION.sha256
```

Island entries armed: `0,1,2,3,4,5,6,9,10,14,18,19,22,28,29,32,33`.

## Two switches that matter

`MGS2_BOX86_ISLAND_FULL=0` turns the island off entirely. The exact pre-entry-4
rollback is:

```sh
MGS2_BOX86_BIN=box86-island29 \
MGS2_WINED3D_DLL=wined3d_p55_glinfo.dll \
MGS2_BOX86_ISLAND_ONLY=0,1,2,3,5,6,9,10,14,18,19,22,28,29,32,33 \
./MGS2-Substance.sh
```

Keep all three overrides together. `MGS2_BOX86_ISLAND_FULL=0` is still the
first diagnostic switch if any island behaviour is suspect.

`MGS2_ISLAND_AB` is cleared unconditionally by the play launcher, and a
measurement run opts in under a different name (`MGS2_ISLAND_AB_MEASURE`). The
reason is specific: the harness runs half of every cycle through the guest path
deliberately, so a value inherited from a shell would hand back about half of
the 8.87 ms and look like the island regressing, with nothing failing to point
at it. It is the only variable here whose accidental presence costs performance
instead of causing an obvious error, so the name that can leak is not the name
that arms it.

## The freeze

A permanent freeze has been seen three times in roughly six hours of play. It is
**not fixed**. The CS deadlock census is armed in this build precisely because
it has never been reproduced under a harness — 8.4 hours of attract mode and a
30-minute accelerated soak both produced nothing.

It costs a handful of counter writes per sync event and no draws are touched.
If a freeze happens, run `harness/cs_deadlock_census.py` against the live
process before killing it; it separates "work was published and the consumer
slept" from "the queues were empty and the fault is elsewhere", which no earlier
capture could do. If it never happens again, so much the better.

Do not attempt to fix the freeze by reasoning. One explanation — weak ordering
around the CSMT queue — was asserted and then withdrawn after checking the Wine
11 source; it was wrong.

## Closed on purpose

Not to be reopened without a specific reproducible bug:

* **No unproved island roots.** `batch_flush` is now routed only because its
  authoritative guest state and full native closure were established and the
  route was measured. `texture_load_location` and
  `rendertarget_view_load_location` remain unsafe: the GL-slot checker is a
  useful preflight, not semantic proof, and their remaining cut dependencies
  have not been closed.
* **No unifying class C with class B.** Class C resolves by name at runtime and
  has no staleness problem. Two mechanisms are inelegant; changing a working one
  before a release is worse.
* **No further profiling of why entry 10 is worth 9 ms.** The number is measured
  and reproducible. Explaining it does not improve it.
* **No further governor work**, no presentation-path changes, no attempts to
  find another few percent.

Long-form record: `docs/briefs/MGS2_REINFORCEMENT_FRAME_BUDGET_2026-08-14.md`.
Research handoffs: `docs/briefs/MGS2_ISLAND_*.md`, most recent last.

## If a rebuild is ever unavoidable

Two traps, both of which have already cost a day each:

1. **The class-B table must not contain addresses.** It maps guest RVA to a
   symbol ID; the ARM addresses come from the linker through per-TU registry
   fragments. The earlier address-based table was compiled into the binary it
   was read from, so a stale entry pointed at a real but *wrong* function rather
   than faulting. `harness/island/full/build_island_objects.sh` does two passes
   and needs no fixpoint loop.
2. **Class-C generation must use the `opengl32.dll` mounted on the device**, not
   the reference wineprefix copy. They share an ImageBase and differ in RVAs,
   which resolved 3 GL slots of 493 and wrote the other 490 back as NULL — a
   crash minutes later, in-game, far from the cause.

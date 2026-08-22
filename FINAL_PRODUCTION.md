# MGS2 Substance on the Anbernic RG353VS — FINALPLAY8

Promoted 22 August 2026, replacing FINALPLAY6's `island41` / `p56` pair. The
owner authorised promotion after playing the exact binaries below for 144
minutes, and the launcher was then exercised through the ordinary entry point
(`MGS2-Substance.sh`, no environment overrides) to prove the defaults, not a
hand-built command line.

```text
box86      box86-island58-p75a-steady
           2d7547b2671e16810ed31a7306aaea6b01a7dbe129f206468cf7d841a19dee4b
wined3d    wined3d_p75a_steady.dll
           382649257b754d88adb27af02a2b447a43a38adfea5b359ec55bbb874bfa9a0d
presenter  winewayland_stall1.so   (unchanged)
island     0,1,2,3,4,5,6,9,10,14,18,19,22,23,28,29,32,33,41
```

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

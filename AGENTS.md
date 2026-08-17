# AGENTS.md — read this first

This repo is a working port of Metal Gear Solid 2: Substance (2003, Direct3D 8)
to an Anbernic RG353VS handheld: RK3566, four Cortex-A55, Mali-G52, 1 GB RAM,
ROCKNIX, sway on Wayland, 32-bit Wine under Box86. Picture, sound and saves work.
The open work is frame rate plus intermittent gameplay SFX loss across
encounter/map transitions. Two no-render/input stalls have been captured: the
earlier empty-message spin and a distinct Box86 aligned-mutex first-use race;
the latter has a direct reproducer and is fixed in FINALPLAY3/FINALPLAY4.

The point of the repo is not the game. It is the Wine patches, the measurement
harness, and the briefs recording **which hypotheses turned out wrong**.

## Where to look, in order

```text
README.md                  what works, why, and the dead-end list
docs/briefs/MGS2_DSOUND_SFX_STATE_CAPTURE_2026-08-10.md
                           current diagnostic for a missing player attack: exact
                           persistent DirectSound-pool controls, bounded ring,
                           valid interpretations and corrected live reader
docs/briefs/MGS2_MANUAL_COMBAT_FREEZE_SOUND_CAPTURE_2026-08-13.md
                           latest user-driven combined report: sustained combat
                           slowdown measured, audio APIs healthy, but the exact
                           missing attack was not timestamp-correlated
docs/briefs/MGS2_REINFORCEMENT_ARM_TARGET_2026-08-14.md
                           valid reinforcements profile: 11.9--19.5 fps at
                           fixed 1992 MHz, exact JIT blocks, and why a whole
                           WineD3D/ARM port is not a candidate
docs/briefs/MGS2_REINFORCEMENT_SUBMIT_CENSUS_2026-08-14.md
                           bounded p37 source/final-draw census, zero indexed
                           draws on the automated ALERT route, GPU-link follow-up
                           and the exact remaining manual capture boundary
docs/briefs/MGS2_REINFORCEMENT_FRAME_BUDGET_2026-08-14.md
                           START HERE for the renderer: the whole reinforcement
                           frame accounted for. Batching, native game code and
                           the present overlap all closed by measurement; four
                           corrections to the earlier record, including one
                           wrong reading retracted in writing
docs/briefs/MGS2_REINFORCEMENT_MUTEX_DIRECT_2026-08-14.md
                           current handoff: dense manual census rejects indexed
                           batching; exact self-owned session-lock freeze,
                           recovery, direct compatible Box86 mutex production
                           path, and its no-FPS-win measurement
docs/briefs/MGS2_DMIME_STATE_CAPTURE_2026-08-10.md
                           current one-reproduction diagnostic: capture point,
                           exact interpretations, build verification and rollback
docs/briefs/MGS2_DMIME_TRANSITION1_2026-08-10.md
                           tested SFX-fix candidate: exact code scope, build
                           checks, rollback and the negative reproduction
docs/briefs/MGS2_INTERMITTENT_SFX_HANDOFF_2026-08-10.md
                           START HERE for the still-open intermittent SFX loss:
                           exact artefacts, retracted patch-14 CC hypothesis,
                           independent review, and the next bounded capture
docs/briefs/MGS2_RUNTIME_BUG_CAPTURE_2026-08-09.md
                           full chronological record of SFX work and the captured
                           PeekMessage no-render/input stall
docs/briefs/MGS2_RUNTIME_MUTEX_FREEZE_2026-08-11.md
                           START HERE for the later complete freeze: live mutex
                           owner proof, Box86 root cause, direct A/B and fix
docs/briefs/MGS2_SEPARABLE_FREEZE_CAPTURE_2026-08-12.md
                           START HERE for the third freeze: live thread capture,
                           untimed futex lost wakeup, what is ruled out, why it is
                           NOT the 08-11 mutex bug, and patch 27's rollback
docs/briefs/MGS2_TRANSITION_HITCH_RESEARCH_2026-08-12.md
                           first-use link hitches: cause measured, separable
                           stages measured at -42%, temporarily withdrawn during
                           freeze triage, then restored after the attribution failed
docs/briefs/MGS2_SHADER_FIRST_USE_RESEARCH_2026-08-13.md
                           START HERE for save/map/enemy hitches: corrected autoload
                           route, exact duplicate GLSL proof, patch 32 A/B and limits
docs/briefs/MGS2_NATIVE_DSOUND_FIR_2026-08-13.md
                           FINALPLAY4 native audio work: exact guest hotspot,
                           bridge ABI, fixed-clock A/B, production hashes and rollback
docs/briefs/MGS2_PERF_BRIEF_43.md   START HERE for performance: native Wine
                                    memmove, exact copy census, cached DISCARD
                                    shadow and measured 30 fps at the heavy spot
docs/briefs/MGS2_FINALPLAY_BRIEF_42.md
                                    clean FINALPLAY renderer baseline before #43
docs/briefs/MGS2_PERF_BRIEF_40.md   earlier performance state and next measured work
docs/briefs/MGS2_PERF_BRIEF_38.md   START HERE: real batchability is 8.49x, the merge
                                    mechanism works on this Mali, and the batcher is
                                    written and built but NOT yet measured
docs/briefs/MGS2_PERF_BRIEF_37.md   how that was scoped: the whole renderer cost is the
                                    glDraw calls themselves
docs/briefs/MGS2_PERF_BRIEF_36.md   the ladder that decomposed the frame
docs/briefs/MGS2_PERF_BRIEF_35.md   every open problem on both stacks, ranked
docs/briefs/MGS2_PERF_BRIEF_34.md   what blocked the game on Hangover; superseded by
                                    #35 now that it renders
docs/briefs/MGS2_PERF_BRIEF_33.md   how that was found: the EGL facade, and gates 1-4
                                    of H2 passing without patching Wine at all
docs/briefs/MGS2_PERF_BRIEF_32.md   H0/H1, and the disk-space traps. Its render 45
                                    reading is wrong; #33 corrects it
docs/briefs/MGS2_PERF_BRIEF_31.md   why the track changed, and the H0-H4 plan
docs/briefs/MGS2_PERF_BRIEF_29.md   the old track: self-contained perf handover
docs/briefs/MGS2_PERF_BRIEF_30.md   the game loop disassembled, and the instruments
                                    built for it (the ladder is deployed, unmeasured)
docs/briefs/MGS2_PERF_BRIEF_28.md   the measurements 29 is built on
docs/DEVICE.md             how to run, measure and not break the console
wine-patches/*.patch       the changes, one file per Wine module
device/launch.sh           every knob, each documented with the measurement
                           that set its default
                            The RG353VS has a second, external menu wrapper at
                            /storage/roms/ports/MGS2-Substance.sh. When deploying
                            device/MGS2-Substance.sh, update both it and the copy
                            inside the game directory or the external wrapper can
                            silently override DLL selections. Keep its defaults
                            in the `${VAR:-default}` form so an explicit
                            MGS2_DMIME_DLL or MGS2_DSOUND_DLL diagnostic launch
                            reaches `launch.sh`.
binaries/ + SHA256SUMS      complete custom production runtime selected by the
                            launchers. Verify all entries before deployment;
                            the proprietary game EXE and temporary recorders
                            are deliberately not versioned here.
```

## Shared workspace resources

The port repository is the record, deployment wrapper, and patch series.  The
source and configured i386 build deliberately live one level above it:

```text
../recovered-session/wine-11.0/
    Recovered Wine 11.0 source tree containing the current MGS2 DLL variants.
    Edit here when changing implementation, then export the reviewed diff into
    wine-patches/ in this repository.

../recovered-session/wine-11.0/dlls/dmusic/
../recovered-session/wine-11.0/dlls/dmime/
../recovered-session/wine-11.0/dlls/dmsynth/
    DirectMusic / AudioPath / synth lifetime and SFX pipeline.  Start here for
    missing gameplay audio; do not start in DirectSound unless evidence points
    there.

../recovered-session/wine-11.0/dlls/dmime/performance.c
../recovered-session/wine-11.0/dlls/dmime/segmentstate.c
../recovered-session/wine-11.0/dlls/dmime/audiopath.c
    The transition fix lives here. Preserve AudioPath ownership and PChannel
    remapping, and never turn the curve path into per-event stderr logging.
    Patch 16's memory-only ring is the only permitted capture at this boundary;
    use `harness/dmime_state.py` externally after the user reports a loss.

../recovered-session/wine-11.0/dlls/dsound/buffer.c
../recovered-session/wine-11.0/dlls/dsound/dsound_private.h
    Player attacks and steps use MGS2's persistent 32,576-byte deferred
    DirectSound SFX pool and may not produce a distinct DirectMusic event.
    Patch 17's `MGS2_SFX_STATE=1` ring records only this pool's lifecycle and
    controls. Capture it once with `harness/dsound_sfx_state.py` immediately
    after silence; do not add stderr logging or mixer polling.

../recovered-session/wine-11.0/dlls/user32/message.c
../recovered-session/wine-11.0/dlls/win32u/message.c
../recovered-session/wine-11.0/dlls/ntdll/thread.c
    Input/no-render stall path.  The captured call chain is documented in the
    runtime bug capture; inspect the caller-specific PeekMessage wait before
    changing controller or gptokeyb code.

box86-patches/03-aligned-mutex-publication.patch
    Apply the production Box86 patch chain to the exact upstream commit named
    in the runtime-mutex brief.
    Patch 03 serialises aligned-mutex first allocation and publication; preserve
    its acquire/release signature ordering and test it with
    `harness/box86_mutex_first_use_stress.c` before changing the bridge.

../recovered-session/wine-11.0/dlls/wined3d/context_gl.c
../recovered-session/wine-11.0/dlls/wined3d/glsl_shader.c
../recovered-session/wine-11.0/dlls/d3d8/device.c
../recovered-session/wine-11.0/dlls/d3d8/buffer.c
    Current MGS2 batch cache and D3D8 vertex-buffer dirty-range implementation.
    These contain the production MGS2BATCH/MGS2CACHE code. Patches 1-11 alone
    do not fully reproduce every current batch variant; apply patch 12 as well.

../recovered-session/build-wine-i386/
    Configured 32-bit Wine build tree.  Use it to rebuild the DLLs after a
    source edit; verify its generated files still correspond to wine-11.0
    before relying on it.

../recovered-session/mingw/bin/
    Cross-compilation toolchain retained with the recovered build.

../recovered-session/scripts/
    Earlier device and audio probes.  Useful as reference only: several sample
    hot paths, so apply rule 2 before running or adapting them.

../recovered-session/device-artifacts/
    Historical DLLs and launchers, not automatically the deployed production
    set.  Treat every file as an artifact and verify byte-wise before use.
```

`../crossover-android-sources-17.0.0.android21/source/wine/` is a separate,
older vendor source tree.  Do not mix it with the Wine 11.0 source or its build
artifacts.

Do not read every brief. Use the runtime capture for sound/input defects and the
latest numbered performance brief for renderer work; older conclusions were
often superseded or retracted **in writing** by later measurements.

## Rules that are not negotiable

1. **Measure on the device.** No conclusion in this project survived being
   reasoned from a desktop. If you cannot measure it here, say so instead of
   estimating.
2. **Never log from a hot thread while judging the thing you are logging.** One
   line per second per buffer from the DirectSound mixer took that thread from
   169 to 930 ticks per 10 s and was heard as stuttering audio; an external
   sampler reading `wchan` for fifty threads amplified the very freezes it was
   measuring. Both cost days.
3. **Frame rate here is scene-dominated.** Windows inside one run range 22 to 60
   fps. An A/B without a fixed spot measures the scene. Pin the clock as well
   (`MGS2_FREQ_STEPS="1416000"`) or it measures temperature.
4. **Verify what is loaded, byte-wise.** The launcher bind-mounts DLLs over
   Wine's. Compare with `cmp` against the mount target; never trust a filename.
5. **One instance.** A background launch outlives the ssh session that started
   it, and two copies of the game read exactly like terrible lag.
6. **Separate the claims.** "Sound works" is three observations: music, menu
   clicks, gameplay SFX. Conflating them produced a whole brief of wrong
   conclusions.
7. **Say what is measured and what is assumed.** Every number here is either
   from the device or labelled as an estimate. Keep it that way.

## The current picture

```text
the old frame was CPU-bound; FINALPLAY already reduces ~1299 source draws to ~151 GL calls
Box86 now bridges exact Wine _sse2_memmove to native ARM without changing semantics
D3D8 keeps DISCARD writes in cached shadow instead of reading mapped upload memory back
the former 20-fps fixed spot is measured at 30.0/30.0/30.1 fps at fixed 1992 MHz
the 2026-08-11 complete freeze was Box86's racy native backing-mutex publication
the direct old/fixed race test is FAIL versus 10/10 x 1,000 PASS; its fix remains deployed
a third freeze on 2026-08-12 is captured but NOT attributed: untimed futex lost
wakeup in the Box86 sync arena, waiting for non-zero, so not the 08-11 mutex bug
patch 27 (separable stages, -42% on link) was rolled back and then restored: the
freezes predate it, so it is production again and the trade is deliberate
the opengl32 facade and the win32u GLES bridge are both load-bearing, measured
ntdll_fastyield.so is no longer mounted: MGS2_YIELD was unset, so it was dead weight
the attract-mode demo is deterministic: 31/9/11/4 frames over 50/100/200/500 ms in
every arm, which makes it the cheapest valid A/B harness this project has
the attract-mode stall buckets are not shaders, paging, SD or dynarec knobs; that
claim does NOT transfer to a loaded save, where new enemies add measured links
the least-optimised stack has the WORST stalls, so the optimisation chain reduces
them; the freeze hypothesis about "some optimisation added them" is refuted
patch 28 removed the culler's dead AABB cache; the culler itself is worth +17.5%
BOX86_DYNAREC_SAFEFLAGS is back at its default 1: lowering it bought 0.9%
patch 29 cut rejected GL state from ~436 to ~48 calls a second and is production
patch 30 (separable for a programmable VS) is written, correct and OFF: measured to
change nothing, because gameplay has no such pairs -- 6k also retracts 6j
patch 31 measured +74% fps on an autoloaded corridor and was REVERTED the same day
when the player found the game barely playable: the route had no transitions, no
enemies, no cutscenes, and averaging fps over windows hid the cost. Read 6l before
trusting any fps number taken from autoload_save.sh alone.
the old autoload walk was invalid: up held Raiden against the upper closed door;
down reaches the first guard and is now the default, with MGS2_WALK_KEY override
patch 32 is production: an off-arm built 36 stages from 19 exact GLSL sources;
17 redundant links cost 2.04 s, while cache-on emitted no source duplicate
unique first-use links remain, so patch 32 reduces the hitch series rather than
claiming that every multi-second save/map transition is fixed
FINALPLAY4 is production: Wine's exact float DirectSound FIR target runs as native
ARM in Box86; at fixed 1416 MHz mixer CPU fell 12.97% -> 7.57% of one core and
guest dsound samples 717 -> 40. This is measured CPU relief, not a claimed FPS A/B
because the two automatic combat windows diverged. The player's initial combat
validation was normal; intermittent SFX loss remains open until a correlated repro
the valid 14 August reinforcement profile is 18.3--19.5 fps, later 11.9--14.8,
with one process, fixed 1992 MHz and 82.777 C: it is real scene cost, not a cap
wined3d_cs is split 1218 Box86/Wine samples versus 1208 already-native libmali;
whole-thread WineD3D-to-ARM is therefore rejected; p37 now provides the external,
memory-only source/final submission census. The exact dense manual reinforcement
capture is entirely non-indexed too: 323,788 source draws became 85,966 final
GL submissions, so the proposed indexed batch is rejected. WineD3D issues two
CS Present commands per displayed frame on this route; use the external frame
log as the rate denominator. The 14 August direct-mutex reliability path measured
15.22 fps here and must not be presented as a renderer improvement.
the native ARM WineD3D island's illegal instruction is found and fixed: the entry
marker is an x86 NOP, and the island's own ARM build put those bytes in the ARM
instruction stream, where 0x474d is `bx r9`. All 37 entries were corrupt at the
same offset, so the island had never executed one instruction of its own body.
Patch 48 emits the marker only under __i386__. That exposed three further walls:
Win32 window/DC stubs, NtCurrentTeb() reading the native ARM thread pointer
instead of Wine's TEB, and indirect calls through guest-held ops/gl_ops pointers
that native ARM cannot call. The first two are fixed -- entries 21 and 30 leave
the cut, patch 49 resolves the guest TEB from Box86's FS base, and six reached
stubs became real native code -- and 15 of 35 entries then route cleanly. On the
live reinforcement scene 15 armed, 11 exercised, 2100 frames, zero faults: the
mechanism works end to end. NO frame-rate effect is measured, in either
direction, and none is claimed: 13.3--15.0 fps is inside the 11.9--19.5 band this
scene already had, there was no control arm, and the four entries that carry the
frame cannot be armed at all. Read sections 17 and 18 before costing the island
again: the cut analysis counts direct call edges, and WineD3D is built on
indirect ones
FINALPLAY5 was the previous production baseline: the native ARM island routed
15 WineD3D entry points, and the GPU governor was pinned to performance. The island was promoted on the
owner's judgement that the game plays correctly, NOT on a number -- no frame-rate
effect is measured for it in either direction. The GPU governor is the one
measured gain: 15.21 -> 16.85 fps, +10.8%, interleaved arms in one process at one
spot, CPU cap holding 1992000 throughout. It supersedes a dead-end entry that was
correct before the cooling was fixed
FINALPLAY6 is production: island entry 10 remains the measured
`wined3d_buffer_load` win (-8.87 ms/frame, about +2.1 fps), and entry 4 now
routes native `mgs2_batch_flush`. Entry 4 uses the authoritative guest batch
object shared across the cut by the paired island31/p56 binaries; ten stable
same-process ABBA pairs measured 53.466 routed versus 56.050 guest ms/frame,
paired median -2.680 ms/frame and +0.899 fps (+4.8%), with zero faults. The
first duplicate-state implementation crashed and is closed. The production
allow-list has 17 entries. A real external-launcher smoke loaded the target save
and completed all 12 walk bursts with one process, 16 entries encountered,
class-B 1616 armed, byte-identical mount targets and zero island faults. The
owner explicitly authorised promotion on 2026-08-16; island29+p55 plus the old
allow-list is the exact rollback
the Box86 sync-arena freeze is still open and recurred in production. The futex
words are genuinely zero and stay zero -- but 0x400f012c is the per-thread alert
futex behind NtWaitForAlertByThreadId, NOT a CS queue word, so that proves only
"no pending alert" and not a missed publication. A weak-memory explanation was
asserted and is WITHDRAWN: Wine 11 publishes queue->head with InterlockedExchange
and guards the wait race with InterlockedCompareExchange, and Box86 barriers
lock-prefixed ops regardless of STRONGMEM. Read section 24 before theorising
again; the queue head/tail and waiting_for_event have never been read
the attract-mode demo is NOT a frame-rate A/B harness: it sits on the 60 Hz cap,
so four interleaved 240 s arms differed by -0.05%, which measures the display and
not the change. Its determinism is real but only useful for stall buckets
```

## Before proposing anything

Check the dead-end list in `README.md` and in brief #29. Fourteen approaches are
closed with evidence, including several that look obviously right: the async
presenter (works, gains nothing, the frame is CPU-bound), a persistent shader
binary cache (the blob rejects its own binaries across processes), redundant
state suppression (the game emits no redundant state), and `csmt=0` (the game
does not start).

## Workflow that works here

```text
1. form one hypothesis, and say what result would refute it
2. build the smallest instrument that answers it, env-gated, off by default
3. run it once on the device, fixed spot, fixed clock
4. write the number down in a brief, including the caveats
5. if it worked: persist it in device/launch.sh with the measurement in a comment
6. if it did not: add it to the dead-end list with the evidence
```

Step 6 is not bookkeeping. It is the main product.

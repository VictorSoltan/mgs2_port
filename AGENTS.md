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
docs/briefs/MGS2_DMSYNTH_RESUME_RECOVER_2026-08-19.md
                           START HERE for sound lost after suspend/resume: the
                           synth sink's one-shot transport and INFINITE wait,
                           dmsynth p35's watchdog, its same-binary control arm,
                           and why production p34 is not byte-reproducible
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
docs/briefs/MGS2_ISLAND_ENTRY34_FAULT_2026-08-19.md
                           START HERE before widening the native ARM island: the
                           two next roots already have A/B wrappers in every
                           shipped binary, entry 34 faults at its own bridge+0xB
                           when armed, the controls that prove the harness is not
                           at fault, why the attract route cannot measure this,
                           and the production Box86 patch record gap it exposed
docs/briefs/MGS2_NATIVE_CS_DRAW_BLACK_FRAME_2026-08-20.md
                           START HERE for the rejected generic CS DRAW boundary:
                           profile rationale, entry-37 closure work, A/B and
                           re-entry calibration, withdrawn FPS readings, clean
                           sound-with-black-picture proof, byte-checked rollback
                           and the only valid correctness-first follow-up
docs/briefs/MGS2_NATIVE_DRAW_TAIL_AND_DIRECT_MUTEX_2026-08-20.md
                           START HERE after p67: lower entry 38's exact ABI and
                           correctness proof, the separately captured direct
                           self-owned mutex freeze, debugger recovery, passive
                           mutex ring + immediate symmetric p68 A/B, and the
                           isolated native context_apply_draw_state() gate
docs/briefs/MGS2_ISLAND_MEASURED_2026-08-16c.md
                           the entry-10 measurement the ABBA harness exists for:
                           -8.87 ms/frame, and section 4 on the unfinished
                           fail-closed GL preflight
docs/briefs/MGS2_ISLAND_BATCH_STATE_MEASURED_2026-08-16d.md
                           entry 4 / mgs2_batch_flush: +0.899 fps once the guest
                           batch object is shared, and why the duplicate-state
                           implementation had to be closed
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
    As of 2026-08-19 `dmsynth/synthsink.c` is the exported patch record plus
    patch 60 (the p35 sink watchdog), reverted from an unexported startup /
    lifetime change set that shipped only in `dmsynth_audit_round3.dll`; that
    change set is kept as `wine-patches/UNAPPLIED-dmsynth-sink-startup-lifetime.diff`.
    Production `dmsynth_p34_interp_reset.dll` is NOT byte-reproducible from this
    build tree -- same functions, different codegen and fluidsynth lib -- so A/B
    the watchdog with its env knob inside one binary, not against p34.

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
FINALPLAY6 was the previous production baseline: island entry 10 remains the measured
`wined3d_buffer_load` win (-8.87 ms/frame, about +2.1 fps), and entry 4 now
routes native `mgs2_batch_flush`. Entry 4 uses the authoritative guest batch
object shared across the cut by the paired island31/p56 binaries; ten stable
same-process ABBA pairs measured 53.466 routed versus 56.050 guest ms/frame,
paired median -2.680 ms/frame and +0.899 fps (+4.8%), with zero faults. The
first duplicate-state implementation crashed and is closed. Its production
allow-list had 17 entries. A real external-launcher smoke loaded the target save
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
again. The queue head/tail and waiting_for_event have now been read once, on
2026-08-19, but on an island-entry-34 stall and NOT on the production freeze, so
that reading says nothing about this bug
FINALPLAY6's box86 was box86-island32-prod, and until 2026-08-19 no brief described
it and no patch recorded half of it: patch 08 carried the hot-page budget fix
only, while the deployed binary also makes `hotpage`/`hotpage_cnt` `__thread`.
Now split into patches 08 and 09, verified by PT_TLS growing 0x2bc -> 0x2cc
between island32-hotpage and island32-prod. BOTH changes are unmeasured, in
either direction; box86-island31 is the last binary without them
entry 23 (wined3d_rendertarget_view_load_location) is measured: a robust positive
direction, about -2 to -2.6 ms/frame in the scene played, 24 of 25 balanced cycles
favouring routed, zero faults in a live session on the owner's save. Do NOT quote a
sigma or a sign-test p for it -- 20 of those 25 cycles come from one deterministic
stretch with identical call counts and are not independent trials -- and note that
the +1.76 fps figure is the MEAN pair delta while the median is about +1.3 fps
FINALPLAY7 is production: box86-island41 with the unchanged
wined3d_p56_batch_state.dll, the old 17-entry allow-list plus entry 23, and no
entry 34 or 37. Its correctness soak ran one byte-checked process at fixed
1992 MHz for 21 complete 300-frame PRESENT windows (6300 frames), class-B armed
with 1616 functions, zero island/native faults, and the owner reported correct
play and picture. A following launch through the external PortMaster wrapper
selected the same live binaries and exact 18-entry list with no A/B variable.
This promotion claims only entry 23's already recorded about -2 to -2.6 ms/frame
direction; the soak FPS varied with the scene and is not a new measurement.
Immediate rollback is box86-island32-prod + p56 + the previous 17-entry list
the old renderer frame budget is RETIRED as a decision basis. It put 22.0 ms libmali
plus 20.4 ms present near a 42.4 ms/frame floor; the same kind of route now measures
37.2 ms/frame, so that floor described a capture, a governor state and a WineD3D
that no longer exist. What is unknown, and blocks the next decision, is how today's
37 ms splits between translated x86 WineD3D, native ARM island, libmali and
present/readback. One fresh profile of island41 on a heavy spot answers it; nothing
should be chosen from the old budget
the fresh island41 heavy-scene profile is now captured: one external 36,426-sample
cycles:u capture of wined3d_cs, CPU fixed 1992 MHz, both mounted binary targets
byte-checked, guest map 16,487/262,144 with overflow=0 and no unresolved JIT
samples. Of all user cycles, native libmali is 42.48%, Box86 JIT is 41.76%, and
resolved guest wined3d.dll alone is 26.47%; the leading block is draw_primitive at
RVA 0x59e20 (5.424%). These are CPU-cycle shares, NOT ms/frame -- the neighbouring
frame windows were not timestamp-correlated. They rule out the "only 2-3 ms left"
case and make a DRAW-first generic CS-handler boundary the next research patch;
they do not make a whole thread port or claim a libmali gain
the DRAW-first generic CS boundary (entry 37) is REJECTED in its p66 form. It
smoked and timed without a native fault, but the required A/B-disabled,
always-routed playtest produced sound and continuously advancing PRESENT with NO
PICTURE. The process stayed alive, 300-frame windows reported 58--60 fps and
0.84--1.15 ms/frame readback, proving those fast windows were presenting an
incorrect/empty frame rather than rendering the game. Therefore withdraw the
raw -61.732 and calibrated -58.860 ms/frame figures as optimisation results,
not merely as scene-attribution errors. Earlier exact windows may also have been
the later death/MISSION FAILED screen; the original entry-37 log was not retained.
Production never changed. Do not time or promote entry 37 again until a
correctness-only memory census proves equal source/final GL submissions and a
bounded frame-content witness proves the routed and guest pictures agree
p67 refutes context TLS as the entry-37 black-frame cause and closes coarse DRAW.
The duplicated state was real: guest `wined3d_context_tls_idx` was 21 while ARM
held 0; p67 copied it once after two class-B witnesses and verified ARM=21. With
zero guest fallbacks, source DRAW and final GL submissions matched exactly at
101,305, yet the bounded frame witness retained 64 identical black frames. The
single relocation-based writable-global audit then covered 605 functions, found
46 referenced writable objects / 12 runtime candidates, and passed controls for
both `mgs2_batch_ptr` and TLS. Batch is already synchronised by production entry
4; TLS was the only new authoritative guest/ARM object and p67 disproved it.
There is no honest second correction candidate. Do NOT time entry 37 again: the
generic post-batching cut is closed. Any next DRAW experiment must leave context
acquire/current-context ownership/release in guest x86 and enter ARM below them,
with source/final counts and frame content as correctness gates before any A/B
p68 proves the lower DRAW cut can render correctly: guest x86 keeps context
acquire/current-context ownership, draw-state application, barriers and release;
only `wined3d_context_gl_draw_primitive_arrays()` is native entry 38. On the live
heavy spot source/final counts were exactly 4,982,735/4,982,735, fallback 0, and
the last 64 of 17,832 bounded frame samples were all lit and unique; an external
screenshot showed correct gameplay. The later symmetric p68b A/B completed 46
cycles, 28 balanced within 2%: paired median +0.002 ms/frame, mean +0.109 and
13/28 favouring routed. The 17 balanced cycles on the 28k-call plateau give
median +0.046. This is inside the pre-registered <=0.3 ms/frame close gate, so
entry 38 is closed as a performance root and is not production. The session then froze for a
separate, named reason: with BOX86_MUTEX_ALIGNED=1, direct mutex 0x6040623c had
lock=2 and owner wine_dinput_worker TID 29633 while that owner, main and
wined3d_cs all waited on the same mutex. One debugger unlock returned 0, zeroed
the mutex and immediately resumed rendering/counts. Exact symbols in the
matching unstripped win32u identify 0x6040623c as `display_lock` (RVA 0x20623c),
not `session_lock` (RVA 0x226284, live 0x60426284). Bypassing Box86's shadow pool
did not close this display-lock self-deadlock. Do not attribute this occurrence
or its frequency to entry 38, and do not confuse it with the 0x400f alert-futex freeze. Full
standalone record and next gates:
`docs/briefs/MGS2_NATIVE_DRAW_TAIL_AND_DIRECT_MUTEX_2026-08-20.md`
p66/p67 moved current-context ownership and context_apply_draw_state into ARM
together; p68 moved both back together. They therefore did NOT prove that state
apply itself must stay guest. The passive bounded display-lock ring remains
available; the next renderer action is context_apply_draw_state alone in ARM,
correctness first, while acquire/current ownership/release stay guest. WINE_NO_TRACE_MSGS is
not another experiment: the documented production recipe already defines it
with WINE_NO_DEBUG_MSGS, and brief 29 records TRACE/debug removed
the first 2026-08-19 attempt to widen past 17 entries was blocked by entry 34
appearing to fault at its bridge +0xB. That interim diagnosis is superseded by
sections 11 onward of the same brief: the parked guest EIP hid native ARM calls
through guest pointers; patches 61--63 and box86 patch 10 closed those routing
classes. Entry 34 now survives gameplay but remains unmeasured because its guest
A/B fallback deadlocks; entry 23 is measured and promoted in FINALPLAY7
the armhf cross toolchain is installed again (Ubuntu gcc 15.2.0), so box86, the
island objects and island_gl_reach.py all work here; the tool now finishes in 25 s
rather than the 45 minutes at which it was abandoned. box86-island32-prod itself
is still not reproducible: it was built with a toolchain that lived in a deleted
scratch directory
patch 61 is the island's real GL defect and its fix: the translated gl_info was
consulted only by GL_EXTCALL(), so 315 plain gl_ops/fbo_ops call sites called
GUEST x86 pointers and native ARM branched into x86 bytes. 135 of them are now
routed through MGS2_GL_INFO() and the extra tables are translated; the shipping
i386 objects are byte-identical in .text/.rdata/.data across all 32 TUs. Entry 34
no longer raises an illegal instruction -- it now fails legibly on a NULL GL slot
production entry 22 WAS bound to the wrong guest address -- the 64-byte marker
window matched it from a mid-function address inside the preceding function, so
its real entry could never route. Fixed by box86 patch 10: identity is now the
address at which the id's marker sits at its CANONICAL offset, with the marker as
a witness and addr == base + rva(id) as a second witness once the class-B base is
known; verified on the device, entry 22 now matches 0x7b919f50, its own start
an unresolved GL slot now names itself: 4096 8-byte ARM stubs (movw r0,#N; b trap
-- a plain mov cannot encode 3113) installed instead of NULL in diagnostic builds,
and the handler prints the slot, its name and the caller from LR. It answered on
the first run: slot 90 glDrawBuffer, from wined3d_context_gl_apply_fbo_state+0x2a0.
libmali has glDrawBuffers and glReadBuffer but NO glDrawBuffer, and Wine's GLES
path does not fill it either, so patch 62 has the island implement it as
glDrawBuffers(1, &buffer) -- the mapping this tree already uses elsewhere for the
same reason. Entry 34 then reaches DirectMusic startup and stops on the NEXT
unrouted pointer: convert_b8g8r8a8_unorm_gles, a guest WineD3D format converter
called through a pointer no instrumented dispatch site covers
patch 63 closes that class by audit rather than by launches: harness/island/full/
island_icall_audit.py lists every call through a function-pointer field in one
entry's closure and splits routed from unrouted. Entry 34: 432 functions, 47
unrouted, 39 of them real calls, all now routed through the existing
MGS2_P50_CALL() with one site id per family. Guest .text/.rdata/.data byte-identical
across all 32 TUs. ENTRY 34 NOW RUNS: 4200+ frames through the attract demo, its
death and the MISSION FAILED menu, zero island faults, correct rendering, and the
same on box86-island41 with diagnostics off (timing-capable). Nothing is claimed
about frame rate -- attract mode cannot measure it. The measurement needs the
owner's save and ~20 minutes: device/launch-island-ab.sh 34 with
MGS2_BOX86_BIN=box86-island41, read with harness/island_ab_read.py
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

# AGENTS.md — read this first

This repo is a working port of Metal Gear Solid 2: Substance (2003, Direct3D 8)
to an Anbernic RG353VS handheld: RK3566, four Cortex-A55, Mali-G52, 1 GB RAM,
ROCKNIX, sway on Wayland, 32-bit Wine under Box86. Picture, sound and saves work.
The open work is frame rate plus two intermittent runtime defects: gameplay SFX
can disappear across encounter/map transitions, and the game can enter a
no-render/input stall in its empty-message loop.

The point of the repo is not the game. It is the Wine patches, the measurement
harness, and the briefs recording **which hypotheses turned out wrong**.

## Where to look, in order

```text
README.md                  what works, why, and the dead-end list
docs/briefs/MGS2_DSOUND_SFX_STATE_CAPTURE_2026-08-10.md
                           current diagnostic for a missing player attack: exact
                           persistent DirectSound-pool controls, bounded ring,
                           valid interpretations and corrected live reader
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
docs/briefs/MGS2_PERF_BRIEF_40.md   latest performance state and next measured work
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

../recovered-session/wine-11.0/dlls/wined3d/context_gl.c
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

## The current picture, in four lines

```text
the frame is CPU-bound: ~1000 draw calls and ~103 ms of CPU against 1.5 ms of GPU
everything removable from the GPU and presentation path has been removed already
the draws come in runs of 8.5 that can be merged; the batcher for that is unmeasured
the largest untapped lever is thermal: the guard drops the clock 1992 -> 1104 MHz
freezes are a wait inside Wine, not the SD card, not shaders, not throttling
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

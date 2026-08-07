# AGENTS.md — read this first

This repo is a working port of Metal Gear Solid 2: Substance (2003, Direct3D 8)
to an Anbernic RG353VS handheld: RK3566, four Cortex-A55, Mali-G52, 1 GB RAM,
ROCKNIX, sway on Wayland, 32-bit Wine under Box86. Picture, sound and saves work.
The open work is frame rate.

The point of the repo is not the game. It is the Wine patches, the measurement
harness, and 30 briefs recording **which hypotheses turned out wrong**.

## Where to look, in order

```text
README.md                  what works, why, and the dead-end list
docs/briefs/MGS2_PERF_BRIEF_34.md   START HERE: exactly what blocks the game on
                                    Hangover, self-contained, with what is ruled out
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
```

Do not read all 30 briefs. Numbers 24, 25, 28 and 29 carry the current facts;
everything earlier is superseded and several of those conclusions were later
retracted **in writing** by the later briefs.

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

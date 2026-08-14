# MGS2 manual combat slowdown / SFX report capture (2026-08-13)

## Result

The user manually played from the loaded save, reported that gameplay sounds
disappeared while the game was freezing, and then died. This run captured a
real severe combat slowdown, but not a multi-second no-render freeze: the last
combat windows fell progressively from about 30 fps to 12--15 fps, and no
`MGS2 STALL` record occurred between capture start and the report.

The audio capture contains no DirectSound HRESULT failure, no DirectMusic or
synth reset, no note allocation failure, no zero-voice failure, and no exact
mute. It therefore does not justify another Wine audio recovery patch. The
button recorder expired before combat and the report arrived on the
`MISSION FAILED` screen, so the exact missing attack cannot be correlated with
one API event in this run. The audio and renderer symptoms remain separate
until a capture establishes a common timestamp and mechanism.

Artefacts are retained under:

```text
logs/live-20260813/mgs2-manual-frieze-sound1/
```

The diagnostic process was PID 133192 and was the only MGS2 process.

## Timeline

```text
capture start                         tick 9487797
first retained gameplay-pool control  tick 9631459
last gameplay-pool control            tick 9649447
new panned DirectMusic sink pair       tick 9671627
that sink pair stopped                 tick 9679929
user report on MISSION FAILED          tick 9710398
```

The 22.147 s interval from the last gameplay-pool operation to the new
DirectMusic sink begins during the death/game-over sequence. Because the user
reported only after the final screen appeared, this interval cannot be called
the audible loss. Treating a normal post-death stop as the bug would be a false
positive.

## Renderer measurement

The diagnostic launcher emitted one presentation summary per 60 frames. Within
the report window there were 85 summaries:

```text
phase                                      median fps   minimum   median readback
before first gameplay-pool control              29.45      22.0            5.89 ms/f
while that pool was active                       19.55      17.4           11.26 ms/f
after it stopped, before game-over sink           14.4      12.0           19.64 ms/f
game-over sink through the report                 14.8      13.3           17.63 ms/f
```

The worst readback window was 23.91 ms/frame. The first summary was 23.1 fps
with 7.39 ms/frame readback; the final summary was 14.5 fps with 17.96
ms/frame. The degradation is sustained scene/render cost rather than one
blocked frame. This run does not identify which draw/effect raised the cost,
and it is not a fixed-scene production A/B.

At the post-report check the CPU was still fixed at 1.992 GHz, CPU temperature
was 82.222 C, GPU temperature 76.25 C, and both cooling states were zero.
Thermal throttling is excluded for that observation.

## DirectSound gameplay pool

The bounded recorder selected only deferred mono PCM16 44.1 kHz buffers of
32,576 bytes. Between the before/after snapshots it recorded:

```text
Lock + Unlock       600
other controls      262
Play                  7
Stop                  6
failed HRESULTs        0
```

The retained operations include normal position, volume, pan and frequency
state, and every call returned success. The last two records stop the panned
game-over sink pair at tick 9679929; neither reports a lost buffer or control
failure. The ring records control/state, not the mixed amplitude of the exact
missing punch, so success does not prove that the game's upstream SE mixer
provided that punch.

## DirectMusic / synth state

Over the capture interval:

```text
dmime PMsg records             +26,477
dmime MIDI deliveries          +22,215
dmime AudioPath volume records +56,511
dmsynth positive note-ons       +4,254
dmsynth failed note-ons              0
dmsynth no-voice events              0
dmsynth resets                       0
maximum observed voices             39 / 48
```

The final retained AudioPath volume values were -1147 through -848, not the
`-10000` mute value. DMSynth's render heartbeat advanced through tick 9713877,
after the user report. This proves that the DirectMusic synth thread remained
alive; it does not identify the player's missing gameplay effect.

PipeWire still showed the `mgs2-audio` client stream active with zero client
errors. The physical sink showed 29 cumulative errors, but no before baseline
was taken, so those errors cannot be attributed to this occurrence.

## Capture limits

The 74.73 s WAV covers only the beginning of the user window, before the
retained combat-pool activity. It contains no complete 100 ms silence window
(minimum RMS 69.68 in signed 16-bit sample units), but it does not cover the
reported loss.

The input recorder ran for 75.1 s and captured zero events. Consequently there
is no exact `x`-press timestamp. A separate earlier user-input trace established
that `x` is the attack key; the previous automation used `z` and therefore
performed rolls/throws. Any document calling bank 0 / program 8 / note 60 a
"punch signature" from those `z` controls is retracted.

## Disposition

No sound patch is promoted from this run. Existing evidence still places
ordinary gameplay SFX above Wine's DirectSound API when the game submits a
continuous Str4SpuTrans stream without the expected action impulse. This run
does not contradict that boundary and gives no divergent DirectSound semantic
to repair.

The renderer observation also does not support rolling back the optimisation
chain: the previous least-optimised whole-stack A/B had the worse stall profile,
while patches 27 and 32 remove measured first-use link work. The remaining
12--15 fps combat phase is the open frequent-heavy-scene problem documented in
the README. A later valid reinforcements profile (14 August) confirmed the same
class of slowdown at fixed 1992 MHz and separated WineD3D from native Mali
driver work; it did not add an audio timestamp or an SFX mechanism. Before an
image-quality tradeoff, it leaves one bounded renderer measurement: count which
draw paths still escape the existing batcher. It does not justify an unmeasured
rollback or an audio patch. See `MGS2_REINFORCEMENT_ARM_TARGET_2026-08-14.md`.

After the capture, the diagnostic process was stopped and a clean production
process was launched at the title screen. Exactly one MGS2 instance was live.
Its environment had `MGS2_GL_STATS=0`, `WINEDEBUG=-all`, and none of
`MGS2_DMIME_STATE`, `MGS2_DMSYNTH_STATE`, `MGS2_SFX_STATE`, or
`MGS2_SINKPROBE`. Box86, opengl32, wined3d, d3d8, dmsynth, dsound, dmime and
dmusic all compared byte-for-byte with the production files selected by
`launch-play.sh`. The clean launch log contained no frame, stall, batch, or
cache telemetry.

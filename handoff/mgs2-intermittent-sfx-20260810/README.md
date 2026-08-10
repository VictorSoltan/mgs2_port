# MGS2 RG353VS — intermittent gameplay-SFX handoff

Date: 10 August 2026. Scope: `mgs2-rg353vs-port` and the recovered Wine 11.0
source immediately above it. This document is deliberately self-contained for
a reviewer who did not participate in the live debugging.

## Executive status

The defect is still open. Gameplay sound effects intermittently disappear at
state transitions. Opening/closing the Start map and entering/leaving an enemy
alert can each either trigger the loss or restore sound. Music, enemy shots, or
other sound classes can remain audible, so "audio works" is not a sufficient
test.

The deployed patch-14 guard is disproved as a sufficient fix. The latest
reproduction occurred with the guard loaded and enabled:

```text
MGS2_DMSYNTH_DLL=dmsynth_se4_unmute1.dll
MGS2_DMSYNTH_UNMUTE_NOTES=1
MGS2_DMSYNTH_STATE=0
MGS2_DMIME_SHAREDGROUPS=1
WINEDEBUG=-all
```

The user met an enemy, gameplay SFX vanished, and opening/closing the map
restored them. The environment is preserved in
`logs/live-20260810/sfx-regression-post-start/mgs2-sfx-regression-20260810-125231/environment.txt`.

The exact failure was not recorded internally because the bounded recorder was
off. This is an important limitation, not a missing footnote: all valid live
object snapshots from that occurrence are post-Start, after sound had returned.

## User-observed behaviour

Observed repeatedly in normal play:

1. `Start -> map -> return` can remove gameplay SFX.
2. Encountering or attacking an enemy can remove them after the alert music
   begins or fades.
3. An enemy's alert/report can restore them without restarting the process.
4. `Start -> map -> return` can also restore them.
5. Some classes can survive while others are absent: enemy gunshots were heard
   while the player's own hit/attack effects were not.
6. The separate no-render/input stall has also occurred in battle, but it has a
   captured `PeekMessage -> NtYieldExecution` call site and must not be merged
   into the audio diagnosis.

This bidirectional transition behaviour is more precise than the old model
"Start causes silence". A later transition changes a stale or incomplete
audio state; it does not necessarily recreate the audio stack.

## What is measured

### Backend and thread lifetime

During reported SFX loss, PipeWire and Wine's DirectSound/DirectMusic threads
remained present. The process did not crash, the kernel showed no OOM/GPU/audio
fault, and other sound classes could remain audible. A complete device/backend
loss is therefore inconsistent with the captures.

### The best preserved synth interval

`mgs2-start-loss-with-roll.tar.gz` contains sixteen overlapping recorder
snapshots spanning about 136 seconds around a Start-loss occurrence. After
deduplicating ring sequence numbers, it contains:

```text
849 note-on records
843 DirectMusic group 1, 6 group 2
all effective FluidSynth channel 0
all result FLUID_OK
848 voice deltas +1, one voice delta +2
0 synth/MIDI reset records
maximum active voices 12; configured limit 48
```

This proves that many DirectMusic events continued to select DLS presets and
create voices. It does not prove that the particular missing player sound
reached the ring; effects must be correlated individually before an upstream
drop can be ruled out.

The shorter alert/report recovery capture contains 64 successful group-1,
effective-channel-0, note-60/velocity-127 events in its retained 13.6-second
window, with no resets or allocation failures. Again, this is a valid recovery
stream, not identification of the missing attack event.

### Post-recovery state from the latest regression

After the user used Start and sound returned, a one-second diagnostic enable
made the synth pointer available and an external reader captured:

```text
synth buffer: state PLAYING, looping, volume 0 dB, 22050 Hz stereo
effective channel 0: CC7 127, CC11 127, bank LSB 1
effective channel 1: CC7 127, CC11 127
remaining FluidSynth channels: normal defaults, mostly 100/127
```

The buffer's quiet PCM snapshot had peak 1 and mean absolute sample 0.25. That
is a quiet post-recovery instant, not proof about an effect during the silent
interval. The full JSON also shows unrelated secondary buffers and should not
be interpreted as a single all-audio amplitude measure.

## Negative tests and retractions

### Shared DirectMusic port

Setting `MGS2_DMIME_SHAREDGROUPS=0` did not prevent the map-triggered loss and
introduced audible lag. The shared-port choice is not the primary cause and
the multipath alternative is not suitable for production.

### Voice exhaustion, synth reset, and obvious DLS failure

The preserved Start-loss ring has successful note-ons with voice count far
below the configured ceiling and no reset. Those mechanisms do not explain the
849 recorded events. This does not cover an unrecorded, specific missing event.

### Patch 14 and the CC7/CC11 argument

Patch 14 restores CC7 or CC11 only when the exact current value is zero and a
positive-velocity note reaches that effective channel. The original rationale
was overstated for four reasons:

1. The silent-state controller snapshot cited in the live terminal was never
   preserved as an artefact.
2. Patch 13 does not record controller changes.
3. The cited zeros were mostly channels 2..15. Production does not set
   `MGS2_DMSYNTH_GROUPMAP`; `synth_event_channel()` therefore uses the low MIDI
   nibble, and every one of the 849 preserved Start-loss notes used effective
   channel 0. Zeros on 2..15 do not explain them.
4. The latest failure happened with the patch-14 DLL and guard active.

The post-recovery channel-0 value 127/127 does not rescue the hypothesis: Start
had already restored the symptom. It is only a baseline.

Patch 14 may still change an exact-zero controller in some run, but it is not a
fix for this defect. Do not broaden it to "low values"; intentional fades would
be changed without evidence.

## Source audit: strongest next candidate

The recovered Wine 11.0 implementation loses most DirectMusic curve semantics.

`../recovered-session/wine-11.0/dlls/dmime/seqtrack.c` constructs a full
`DMUS_CURVE_PMSG` containing:

```text
mtDuration, mtResetDuration
nStartValue, nEndValue, nResetValue
nOffset, bType, bCurveShape, bCCData, bFlags
```

But `../recovered-session/wine-11.0/dlls/dmime/performance.c`, in the
`DMUS_PMSGT_CURVE` case around line 2548, handles a CC curve by sending exactly
one MIDI CC with `nStartValue`. It ignores the end value, duration, reset value,
reset duration, shape, and reset/start-from-current flags.

That is a concrete mechanism capable of leaving a transition fade at its
starting attenuation until a later map or alert transition writes another
value. It matches the bidirectional symptom. It remains a hypothesis until a
real MGS2 loss is shown to contain the corresponding curve.

Microsoft's archived `DMUS_CURVE_PMSG` contract documents the duration,
start/end/reset values and reset/start-from-current semantics:
https://learn.microsoft.com/en-us/previous-versions/ms807617%28v%3Dmsdn.10%29

Nearby incomplete transition semantics are secondary candidates:

- `IDirectMusicAudioPath::SetVolume()` is a stub returning `S_OK`.
- `AudioPath::Activate(FALSE)` stops its DirectSound buffer, but the TRUE path
  does not explicitly restart it.
- `PlaySegmentEx()` logs but does not apply its `audio_path` argument.

These gaps make `dmime`/AudioPath the right layer to inspect. None is yet
correlated with a failing transition, and the known synth private buffer was
`PLAYING` in the post-recovery capture.

## Exact next experiment

Do not ship another recovery guard first. Build one env-gated, bounded,
memory-only recorder, off by default:

1. In `dmsynth`, record every CC7/CC11 write with DirectMusic group, effective
   FluidSynth channel, previous value, new value and event time.
2. Record CC7/CC11 immediately before and after each positive note-on, plus the
   exact voice delta. Fix `noteon_no_voice`: its current both-zero heuristic can
   miss a failed creation when another voice is already active.
3. In `dmime`, record every `DMUS_PMSGT_CURVE`: PChannel, CC, start/end/reset,
   duration/reset-duration, type, shape, flags and delivery/requeue action.
4. In the same small ring or a second bounded ring, record AudioPath
   `Activate()` and `SetVolume()` calls, including path pointer and parameters.
5. Keep the external reader ready. On the next audible loss, capture before
   pressing Start; capture again immediately after Start restores it.
6. Correlate one known player attack/shot with a note-on and measure fresh
   rendered samples for that voice/window, not the peak of an old circular
   buffer.

Refutation rule: if no controller/curve/AudioPath state differs across the
boundary and the expected player event never reaches `dmsynth`, move upstream
to the game's SE routing. If a curve begins near silence and has a non-zero
end/reset that Wine never delivers, implement the smallest endpoint/reset A/B
with a unit test and an env gate.

## Artefacts and checksums

Primary preserved artefacts:

| Artefact | Purpose | SHA-256 |
|---|---|---|
| `logs/live-20260810/sfx-transition-0216/mgs2-start-loss-with-roll.tar.gz` | 16 rolling synth snapshots around a Start loss | `4249067a022153bdb295ef4162feb58ed89a35c630d478bc05905a8c62376c32` |
| `logs/live-20260810/sfx-transition-0216/dmsynth-state-attack-loss-report-restored.json` | alert/report recovery interval | `b9ecdcc4c63d064573a61e4116d5cbb1a06c708729cd3af2fc3dbdf366d7efcc` |
| `logs/live-20260810/sfx-transition-0216/mgs2-sfx-loss-20260810-021602.tar.gz` | first user-reported loss snapshot; recorder off | `9b2e25a4dcc22725158aaca4cfc5e8c3fe14fc7eca5e9449467f2d19cd6bca6e` |
| `logs/live-20260810/sfx-transition-0216/mgs2-sfx-restored-20260810-021659.tar.gz` | matching restored snapshot; recorder off | `2f30df9ee92766c09158270e9c607c63047b1e0eccd953c10bf3fe10c701e3ae` |
| `logs/live-20260810/sfx-regression-post-start/mgs2-sfx-regression-20260810-125231.tar.gz` | latest patch-14 regression environment/system snapshot | `0f8d4ca37c8f1f217b8de3c47e22d6f23c6caadb480e8be47662c3f5523013b1` |
| `logs/live-20260810/sfx-regression-post-start/dmsynth-state-post-start-brief.json` | post-recovery synth baseline | `42d5a002ef2defd7362c1fc4617a5d1f578854978697eb5926381f5bde617227` |
| `logs/live-20260810/sfx-regression-post-start/dsound-live-post-start-brief.json` | post-recovery buffers/controllers | `77197a8f85c3fe5a406c89d702ad9fe156a90fc74302783c677c15d65147021c` |

The latest regression tar contains an empty first DirectSound JSON and a
recorder header with no synth pointer because `MGS2_DMSYNTH_STATE=0`; use the
separate `*-post-start-brief.json` files for the valid post-recovery baseline.

Relevant implementation and tooling:

```text
wine-patches/12-current-runtime.patch
wine-patches/13-dmsynth-state-recorder.patch
wine-patches/14-dmsynth-note-unmute.patch
harness/dmsynth_state.py
harness/dmsynth_state_control.py
harness/dsound_live_state.py
../recovered-session/wine-11.0/dlls/dmime/performance.c
../recovered-session/wine-11.0/dlls/dmime/seqtrack.c
../recovered-session/wine-11.0/dlls/dmime/audiopath.c
../recovered-session/wine-11.0/dlls/dmsynth/synth.c
```

## Current production caution

The wrapper still selects `dmsynth_se4_unmute1.dll` with the failed guard
enabled, because this handoff intentionally does not mutate the running console
or silently choose a new production policy. Treat it as an active experimental
setting, not a solved defect. The state recorder remains default-off to avoid
normal-play overhead; for the next deliberate capture it must be enabled before
the reproduction, not after it.

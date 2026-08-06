# MGS2 RG353VS — brief #20: SFX reaches MIDI sequence processing, remains silent

## Result of the clean three-shot run

The user fired three shots in gameplay.  No game SFX was audible.  The isolated
`sevoice6b` recorder was armed immediately before gameplay and explicitly
excluded the persistent `0x1DA` background effect, so the dump contains the
shots rather than the earlier background loop:

| Event | retail SE code | SE track | Result |
|---|---:|---:|---|
| Shot 1 | `0x0083F009` | 37 | `se_adrs_set` and `sound_sub` observed |
| Shot 2 | `0x0083F052` | 37 | `se_adrs_set` and `sound_sub` observed |
| Shot 3 | `0x0083F040` | 37 | `se_adrs_set` and `sound_sub` observed |

Raw dump: [`logs/rg353vs/mgs2-sevoice6b-shots.json`](logs/rg353vs/mgs2-sevoice6b-shots.json).

For each sound, `sound_sub` began with a valid mapped sequence pointer
(`0x017A90D4` or `0x017A96AC`), consumed sequence data, and returned normally.
For example, the first sound advances `mptr` from `0x017A90D4` to
`0x017A90E4`; it is not rejected, missing, or stuck before parsing.

This closes these causes for the actual shots:

- SE bank/header lookup;
- `SePlay` queueing and priority allocation;
- `se_adrs_set` request-to-playing transfer;
- a null/invalid sound sequence pointer;
- early `sound_sub` parser failure.

## Confirmed live module state

`/proc/16425/maps` for the same process contains:

```text
dmime.dll
dmsynth.dll
dmusic.dll
winealsa.drv / winealsa.so
dsound.dll
```

This only proves that the components are loaded. It does **not** prove that the
specific note-on from a shot reaches the DirectMusic port or is rendered by the
synthesizer.

## Exact remaining retail code path

The next boundary is now sharply defined by the retail binary:

```text
sound_sub() @ 0x008FF3B0
  -> keyon() callsite 0x008FF681, target 0x008F24E2
  -> per-track pending-key flag at spu_tr_wk[mtrack]+0x48
  -> voice-maintenance loop @ 0x008F1FB3
  -> callsite 0x008F2265, target 0x008F1EB8
  -> MIDI helpers 0x008FE2C4 / 0x008FE4E5
  -> MIDI submit helper 0x008FE343
  -> DirectMusic performance/object at 0x012116B8
  -> DirectMusic routing -> dmsynth -> Wine ALSA
```

Static evidence:

- `0x008F24E2` sets the pending per-track flag for the current `mtrack`.
- `0x008F2265` consumes that flag and invokes `0x008F1EB8` with the track.
- `0x008F1EB8` calls `0x008FE2C4` and then `0x008FE4E5`.
- `0x008FE4E5` constructs a MIDI `0x90` note-on and calls `0x008FE343`.
- `0x008FE343` allocates and sends a `DMUS_MIDI_PMSG` through a vtable on the
  object stored at `0x012116B8`.  This is not yet proof that the final call is
  `IDirectMusicPort::PlayBuffer()`; the recorder must identify the object and
  vtable target rather than assigning an interface name from the address.

## Required next recorder (not a DLL replacement)

Use one marker-armed EXE and capture only the three known shot codes. Hook:

1. `0x008FF681` (`keyon` call) to record `mtrack`, code, and
   `spu_tr_wk[mtrack]+0x48` before/after.
2. `0x008F2265` (the actual pending-key consumer) to record the same values
   before/after target `0x008F1EB8`.
3. The MIDI submission callsites which enter `0x008FE343`, so the wrapper can
   preserve the original call and record its returned HRESULT.  Correlate it
   with the currently pending target SE track; do not capture global BGM
   traffic unfiltered.

For every target message, record the object pointer, its vtable and the exact
called vtable method, plus the constructed `DMUS_MIDI_PMSG` fields (P-channel,
flags, type and MIDI bytes).  Record the rolling ~250 ms context for `CC 0`,
`CC 32`, `CC 7`, `CC 11`, program change, pitch bend, note-on and note-off.

`DMUS_EVENTHEADER` is deliberately a separate observation point: it is formed
later by DirectMusic when the PMsg is routed into an `IDirectMusicBuffer`.
An EXE-side successful submit therefore only proves accepted queueing, not
that a note was rendered.

The decisive outcomes are:

| Observation | Consequence |
|---|---|
| `keyon` not reached | Fault is within parsed track state / note setup. |
| `keyon` reached but `0x008F2265` not reached | Voice-maintenance scheduling defect. |
| `0x008F2265` reached but no `0x90` submission | Fault inside `0x008F1EB8` helper chain. |
| `0x90` is submitted with failure HRESULT | Repair the failing DirectMusic object/submission path. |
| `0x90` succeeds yet remains silent | It was accepted for queueing.  Continue in `dmsynth`; this does **not** prove rendering or ALSA delivery. |

## Confirmed Wine 11 candidate: channel-group loss

The local Wine 11 source makes a narrow, testable hypothesis available:

- `synth_Open()` defaults to two channel groups (`synth.c`, `dwChannelGroups =
  2`), while `synth_SetNumChannelGroups()` is still a stub.
- `synth_PlayBuffer()` receives `DMUS_EVENTHEADER`, but its queued `struct
  event` stores only time, sample position and three MIDI bytes.  It discards
  `head->dwChannelGroup`.
- `synth_Render()` derives the FluidSynth channel solely from `midi[0] &
  0x0f` and updates only channels 0--15.
- The return value of `fluid_synth_noteon()` is not checked.

Thus an `S_OK` chain can still end in `fluid_synth_noteon() == FLUID_FAILED`,
with no active voice and no sound.  If BGM uses group 1/channel 0 and SFX uses
group 2/channel 0, Wine currently collapses both onto FluidSynth channel 0.

Do **not** apply a channel-group patch yet.  First capture the real
`DMUS_EVENTHEADER.dwChannelGroup` for a shot.

## Stage 2, conditional dmsynth recorder

Only after the EXE recorder observes successful submission, use a bounded
diagnostic `dmsynth_seprobe7.dll` built from the clean Wine 11 source.  It must
not change mixing behaviour.  In `synth_PlayBuffer()` log `dwChannelGroup`,
`rtDelta`, sample position and MIDI bytes.  Around `fluid_synth_noteon()` log
the group, effective FluidSynth channel, bank/program, CC7/CC11, note,
velocity, return code, and active voice count before/after.

If a shot has `dwChannelGroup > 1` and is rendered on the first group, the
minimal eventual fix is to retain the group in `struct event`, select channel
`(group - 1) * 16 + (status & 0x0f)`, and configure/initialise at least
`group_count * 16` FluidSynth channels.  Other outcomes instead direct us to
missing instruments/regions or downstream synth delivery.

## Do not change

Do not reapply Creative ALchemy, DSOAL, DirectSound replacements, PipeWire
tuning, DirectMusic DLL substitutions, `dmime_graphqi.dll`, or
`dmsynth_wine112.dll`. None of those changes is justified by this run.

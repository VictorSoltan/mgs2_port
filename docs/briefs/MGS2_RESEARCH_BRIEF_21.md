# MGS2 RG353VS — brief #21: game emits SFX keyon/MIDI; resolve the exact DirectMusic group fix

## Question for research

Can the remaining DirectMusic failure be resolved from the supplied code and
runtime artefacts without another interactive probe?  In particular, determine
whether the shot MIDI reaches Wine `dmsynth` with `dwChannelGroup > 1`, and
propose the smallest correct patch if it does.

Do **not** recommend Creative ALchemy, DSOAL, PipeWire tuning, DirectSound
replacements, or generic Wine upgrades.  Those paths were already tested and
are outside the remaining fault boundary.

## Proven by two independent live recorders

For a real user weapon shot, these retail SE codes were observed:

```text
0x0083F009
0x0083F052
0x0083F040
```

`sevoice7` recorded all three on SE track 37.  Each one performs:

```text
se_adrs_set
  -> sound_sub first tick
  -> keyon() at retail callsite 0x008FF681
```

The keyon call is not inferred: it was instrumented directly.  Its pending
voice state is non-zero immediately before the call.  The compact raw result
is [`logs/rg353vs/mgs2-sevoice7-one-shot.json`](logs/rg353vs/mgs2-sevoice7-one-shot.json).

An earlier independent `midiout7` run on the same shot-code family recorded:

```text
keyon -> pending-key consumer -> MIDI 90 3c 7f -> DirectMusic PMsg submit
```

The submit helper returned its normal success result (`1`; this helper
normalises non-negative underlying HRESULTs to `1`).  The object/vtable is
live, and the PMsg has size 64 and `dwFlags=0x33`.  Raw artefact:
[`logs/rg353vs/mgs2-midiout7-shots.json`](logs/rg353vs/mgs2-midiout7-shots.json).

Consequently, do not pursue SE request allocation, sequence parsing, missing
bank files, `keyon`, or game-to-DirectMusic submission.  They are all live.

## Important distinctions in the recorded data

The game helper at `0x008FE343` builds a `DMUS_MIDI_PMSG`, not a
`DMUS_EVENTHEADER`.  The latter is created later by `dmime` when it routes the
PMsg through an `IDirectMusicBuffer`:

```text
PMsg.dwPChannel
  -> IDirectMusicPerformance::PChannelInfo()
  -> (port, midi_group, midi_channel)
  -> IDirectMusicBuffer::PackStructured(..., midi_group, ...)
  -> DMUS_EVENTHEADER.dwChannelGroup
  -> IDirectMusicPort::PlayBuffer()
  -> IDirectMusicSynth::PlayBuffer()
```

Most shot-linked PMsgs observed `dwPChannel=0`.  One later MIDI submission had
`dwPChannel=16`; it may be adjacent background traffic because the marker was
track-based.  Do **not** equate P-channel 16 with group 2 without proving the
actual `PChannelInfo()` result.

## Exact local Wine 11 code relevant to the hypothesis

The build source is `recovered-session/wine-11.0`.

In `dlls/dmime/performance.c`:

- `struct channel` holds `midi_group`, `midi_channel`, and a port.
- `channel_block_init()` assigns the supplied `midi_group` to all 16 channels.
- `perf_dmport_create()` creates channel blocks with `midi_group = i + 1` for
  every requested group.
- DirectMusic routing uses `PChannelInfo()` and then
  `IDirectMusicBuffer_PackStructured(buffer, ..., group, value)`.

In `dlls/dmsynth/synth.c`:

- `synth_PlayBuffer()` receives `DMUS_EVENTHEADER`, but queued `struct event`
  retains only `time`, `position`, and three MIDI bytes.  It drops
  `dwChannelGroup`.
- `synth_Render()` computes the FluidSynth channel only as
  `midi[0] & 0x0f`, updates only 0--15, and ignores the return of
  `fluid_synth_noteon()`.
- `synth_SetNumChannelGroups()` is a stub; default `synth_Open()` params use
  two channel groups.

This supports a concrete candidate: a shot on DirectMusic group 2/channel 0
can be collapsed into FluidSynth channel 0 instead of channel 16.

## A diagnostic run that must not be overinterpreted

`dmsynth_mgs2diag3.dll` was briefly loaded with `MGS2_TRACE=1`.  It confirmed
that instrumentation works, but it logged startup zero-velocity messages and
made gameplay unusably slow because Wine was writing a log on the render path.
It did **not** capture a user weapon shot.  Its observed `group=1`,
`noteon_result=-1`, `active_voices=0` entries therefore are not evidence about
the shot and must not be used as the fix basis.

## Research deliverables

1. Trace the MGS2 template/PMsg data (`0x0122E4D8`, `0x0122E614` in the live
   dump) through `dmime` and state whether their P-channels deterministically
   select a non-default MIDI group in this build.
2. State whether a static group-preserving `dmsynth` patch is justified now.
   If not, name the smallest runtime observation that is still necessary.
3. If a patch is justified, give a minimal Wine 11 diff that:

   - stores `DMUS_EVENTHEADER.dwChannelGroup` in queued `struct event`;
   - maps rendering to `(group - 1) * 16 + (status & 0x0f)`;
   - configures and initialises enough FluidSynth channels; and
   - preserves group-1 behaviour.

4. If a runtime observation remains necessary, design it as an in-memory,
   marker-bounded recorder.  It must not require `MGS2_TRACE=1` or per-render
   disk logging.  The user has already experienced severe lag from that form
   of trace.
5. Consider the existing `dmime` shared-audio-path-port changes.  Explain
   whether they could cause a P-channel map or instrument-download mismatch
   even when the final `dmsynth` group implementation is corrected.

## Constraints

- Current playable baseline is `mgs2_sse_rg353vs_port.exe` with
  `dmsynth_wine112.dll` and no trace.
- Do not alter the baseline merely to run a speculative audio fix.
- Any answer must distinguish a helper's normal return `1` from a raw COM
  `HRESULT`, and P-channel from DirectMusic channel group.

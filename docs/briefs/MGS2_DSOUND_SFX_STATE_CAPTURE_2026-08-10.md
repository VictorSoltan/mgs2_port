# MGS2 RG353VS — bounded DirectSound gameplay-SFX capture

Date: 10 August 2026. Status: diagnostic candidate, off by default. This is
the next instrument for a missing player attack/footstep; it is not another
audio "fix" and makes no mixer-policy change.

## Why this boundary

The latest user report was a silent player attack. The live `dmime_state1` and
`dmsynth_state1` capture made an important, limited observation: DirectMusic
continued to stamp and deliver retained MIDI records and FluidSynth continued
to create voices. That does not identify the attack. The DirectMusic ring is
only 256 events, and MGS2's ordinary gameplay effects are normally controlled
through a persistent DirectSound pool instead of a new `Play()`/MIDI sequence.

Source and earlier device captures identify that pool as deferred mono PCM
secondary buffers with `dwBufferBytes = 32576` and `nSamplesPerSec = 44100`.
The game changes a looping member via Lock/Unlock, position, volume, pan,
frequency, Play or Stop. A poll for a newly-created buffer or a generic synth
note is therefore the wrong measurement for a missing punch.

## Corrected earlier live-reader result

An earlier `dsound_live_state.py` version decoded the sink struct with incorrect
offsets. Its `device_stopped` reading is the primary-device status, which Wine
only uses on the `DSSCL_WRITEPRIMARY` path; it does not explain a normal
secondary-buffer mix. Its meter fields were also read from wrong offsets.

The corrected reader shows the DMSynth sink buffer playing with non-zero PCM.
That rules out neither a missing DirectSound gameplay effect nor a transient
pool-control error. Do not cite the old `device_stopped`/zero-meter output as
the cause of an SFX loss.

## Patch 17

`wine-patches/17-dsound-sfx-state-recorder.patch` adds a fixed 4,096-record
in-process ring to `dsound`. It is enabled only by `MGS2_SFX_STATE=1`; with the
variable absent it returns before inspecting a buffer. It selects only the
known gameplay-SFX pool and stores no text, file output, pipe writes, or
mixer-thread scan.

The exported `enabled` field is intentionally lazy: it changes from zero only
when the first selected pool operation reaches the recorder. Thus an empty
title-screen baseline with `enabled: false` is expected; verify the process
environment and loaded DLL hash, not that field, before the first effect.

Each record contains a monotonic sequence and tick, the operation, object and
backing-memory addresses, current state/play flags/mix positions, committed
state, volume/pan/frequency, three call arguments and HRESULT. The ring is
about 295 KiB. Sequence is committed last, so the external reader can discard
an incomplete concurrent record.

The recorded operations are:

```text
Lock  Unlock  SetCurrentPosition  SetVolume  SetPan  SetFrequency  Play  Stop
```

Files:

```text
wine-patches/17-dsound-sfx-state-recorder.patch
binaries/dsound_state1.dll
harness/dsound_sfx_state.py
```

`dsound_state1.dll` SHA-256:

```text
05760dfc21c62233e28e3c5a8fc3fa28ba25aa209a1931ae7219eee00a6a1451
```

## One-reproduction run

Start one diagnostic session with the established DirectMusic transition fix,
but leave its temporary recorder off so this capture has the smallest scope:

```sh
MGS2_DSOUND_DLL=dsound_state1.dll MGS2_SFX_STATE=1 \\
MGS2_DMIME_DLL=dmime_transition1.dll MGS2_DMIME_STATE=0 \\
MGS2_DMSYNTH_STATE=0 MGS2_DMSYNTH_UNMUTE_NOTES=0 \\
/storage/roms/ports/MGS2-Substance.sh
```

Before play, verify that Wine's bind-mounted `dsound.dll` has the exact SHA and
that the game environment contains those values. Immediately after an audible
loss — before using Start to restore it — run once:

```sh
python3 /tmp/dsound_sfx_state.py <game-pid> --output /tmp/dsound-sfx-loss.json
```

Copy the JSON out before another transition. The 4,096 records allow the user
to play normally between captures without a hot trace.

## Interpretation rule

| Capture around the attempted attack | Narrow next conclusion |
| --- | --- |
| Lock/Unlock plus position/volume/play operations occur | The game reached the known SFX pool. Compare its state, play flags, committed position and result with an audible attack; fix only the divergent DirectSound semantic. |
| The operation returns an error | Reproduce the precise API contract failure; do not add gain/cursor workarounds. |
| Operations occur but no pool state changes or output is audible | Inspect the normal secondary-buffer mix/commit lifecycle for that recorded buffer. |
| No record occurs | The action used a different buffer/path or did not reach MGS2's effect producer. Do not blame the current pool or DMSynth. |

This is deliberately a discriminating measurement. It does not turn a failed
capture into a speculative production change.

## Build verification and rollback

The release i386 DLL compiled cleanly. Patch 17 was regenerated from the
source tree after patches 1–16; it must apply with `patch -p1 -F0 --dry-run`
and reproduce `dlls/dsound/buffer.c` and `dsound_private.h` byte for byte.
`harness/dsound_sfx_state.py` is syntax-checked with Python before deployment.

Rollback is a normal wrapper launch without `MGS2_DSOUND_DLL` and
`MGS2_SFX_STATE`; `dsound_se1.dll` remains the production audio DLL. Never
leave this recorder enabled after the one needed reproduction.

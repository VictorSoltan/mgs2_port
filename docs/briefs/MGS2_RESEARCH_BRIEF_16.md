# MGS2 / RG353VS — DirectSound event recorder run

This is the bounded measurement proposed by the external review of brief #15.
It supersedes neither the stable audio baseline nor the DirectMusic decision:
the sole purpose is to identify how MGS2 triggers a short effect on an
already-looping DirectSound voice.

## Installed diagnostic build

`dsound_sfxevents2.dll` was built from the pristine
`recovered-session/wine-11.0.tar.xz` source archive. The only source changes
are the opt-in recorder in `dlls/dsound/buffer.c` and two diagnostic IDs in
`dsound_private.h`. No previous MGS2 probing code, PCM scan, byte swap, gain,
cursor reset, old-Wine compatibility change, DirectMusic change, or PipeWire
setting is present.

```text
dsound_sfxevents2.dll
SHA-256 6b0a32f66293ac0e62bc3df87ba9b2502b6c4f989504f531ffddc79791bc1c65
```

On the console it is in:

```text
/storage/roms/ports/MGS2-Substance/dsound_sfxevents2.dll
```

The current running process is not changed. For the **next** game launch,
`launch.sh` defaults to the recorder DLL and exports:

```sh
MGS2_DSOUND_DLL=dsound_sfxevents2.dll
MGS2_SFX_EVENTS=1
MGS2_SFX_EVENTS_DIR='Z:\tmp\mgs2-sfxevents'
```

The prior launcher is preserved verbatim on the device as
`launch.sh.before-sfxevents`. After the capture, restore that file rather than
leaving any diagnostic DLL selected.

## Exact recorder filter and cost

Only a secondary buffer matching all of the following is considered:

```text
buffer bytes = 32576
sample rate  = 44100 Hz
channels     = 1
format       = PCM16
caps         = DSBCAPS_LOCDEFER
```

It captures at most 256 fixed-size in-memory events. It does no PCM analysis
and performs no file write while an event is being recorded. The existing
mixer thread checks the marker at most once per 100 ms only so a capture with
zero API calls is still finalized; it neither inspects audio samples nor
changes mixing. One text file is written only when the marker is removed,
after three seconds, or when the 256-event capacity is reached.

The recorded calls are:

```text
Lock, Unlock, GetCurrentPosition, SetCurrentPosition,
SetVolume, SetPan, SetFrequency, Play, Stop,
GetStatus, AcquireResources
```

Each entry contains a relative timestamp, thread ID, caller return address,
per-interface object ID, shared BufferMemory ID, HRESULT, method inputs and
outputs, and Wine's immediate state snapshot:

```text
state, playflags, sec_mixpos, writelead,
use_committed, committed_mixpos, effective L/R amp factors
```

For `Lock`, `a..h` mean requested cursor, requested byte count, flags,
effective cursor, returned span-1 offset/size and span-2 offset/size. For
`Unlock` they are the two actual spans. `SetCurrentPosition` includes the
requested, aligned and previous positions. The header of the generated file
also states the remaining field mappings.

## One controlled gameplay run

1. Exit the currently open game and start it once normally. Do not enable
   `MGS2_TRACE`, and do not change PipeWire, DirectMusic, graphics, or input
   settings.
2. Reach a quiet gameplay spot and wait two seconds.
3. Create `/tmp/mgs2-sfx-arm` on the console.
4. Make exactly one punch (preferred over radio or an interaction).
5. Wait two seconds, then remove `/tmp/mgs2-sfx-arm`. The automatic three
   second deadline is also a fallback if removal is missed.
6. Leave the game running or exit normally. Collect
   `/tmp/mgs2-sfxevents/events-001.log` (or the newest `events-*.log`).

The result will distinguish the meaningful paths without another broad test:

* `Lock/Unlock → SetCurrentPosition → SetVolume` identifies a fresh write and
  exact playback position.
* `SetCurrentPosition → SetVolume` without a write identifies a preloaded
  waveform/cursor issue.
* `SetVolume` alone identifies a permanently rotating voice and focuses the
  next patch on position/rate/output queue timing.
* `AcquireResources` or `GetStatus` at the trigger identifies a narrow
  LOCDEFER contract to implement.

Repeated caller addresses can be mapped directly in Ghidra to the retail
voice-update and trigger paths. Do not infer a fix before this sequence is
visible.

## Result of the first attempt and v2 correction

The first v1 DLL was definitely mounted (the on-device mounted DLL hash was
`081d044d...d14c0ce`), and Wine drive `Z:` was confirmed to map to `/`, so its
marker path was correct. Yet no `events-001.log` was written during the marker
window around one punch. This means no selected pool method entered the v1
recorder after it armed, but v1 could not persist that zero-event result.

v2 changes only finalization: the existing DirectSound mixer thread polls the
marker at the existing 100 ms gate. The next one-punch run will therefore
produce a log even if the count is zero. A zero count would be positive
evidence that gameplay changes the persistent voice through another path
(for example a retained direct memory pointer), rather than any recorded
DirectSound API call.

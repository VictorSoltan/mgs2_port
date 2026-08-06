# MGS2 Substance on RG353VS — research brief #11

## Sound effects are silent while streamed audio plays

Music and ambience work. Everything else does not: footsteps, punches, weapon
handling, and the codec ring. This brief is a request for help identifying where the
effect audio is lost, and it deliberately includes two hypotheses of mine that the
measurements refuted, because the refutations are the most useful part.

Previous audio work is in brief #9 (which got the game from total silence to working
music) and §11–12 of `MGS2_PROJECT_STATE.md`.

## The stack, in one paragraph

Anbernic RG353VS, RockNIX. box64 runs 64-bit Wine 11.0, which re-execs the 32-bit
`wine` under box86; the whole 32-bit stack is emulated, only libmali, PipeWire and the
kernel are native. Audio reaches PipeWire through Wine's ALSA driver at 44.1 kHz.
Retail MGS2 data layout (`bgm.dat`, `vox.dat`, `codec.dat`, `demo.dat`, `stage/`), no
Bluepoint stream remapping. PE-side Wine DLLs can be rebuilt from the 11.0 tree and
bind-mounted over the shipping ones; Unix `.so` rebuilds do not work on this device.

## What the game actually does with audio

This was measured, not assumed. `WINEDEBUG=-all,trace+dsound` over a startup, then a
purpose-built per-buffer write census in `dsound`.

**MGS2 mixes its own audio and streams the result.** Over one startup: **16** `Play`
calls against **51900** `Unlock` calls. It is not using DirectSound as a voice mixer;
it fills a few buffers continuously.

Every `CreateSoundBuffer` at startup, 62 in total:

| count | bytes | flags | who creates it |
| --- | --- | --- | --- |
| 15 | 32576 | `0x000581e0` — LOCDEFER, GETCURRENTPOSITION2, GLOBALFOCUS, CTRLPOSITIONNOTIFY, CTRLVOLUME, CTRLPAN, CTRLFREQUENCY | the game |
| 4 | 65152 | `0x00058190` — same without CTRLPAN | the game |
| 1 | 0 | `0x00000f5f` | the game's primary |
| 14 | **4** | `0x000282b0` ×13, `0x000082e0` ×1 | **dmime**, `CreateStandardAudioPath` |
| 13 + 1 | 0 | `0x000280b1`, `0x000080e1` | dmime primaries |
| 14 | 176400 | `0x00018100` | dmsynth sinks, 22050 Hz stereo, 2 s |

DirectMusic side: 13 audio paths of type `DMUS_APATH_DYNAMIC_3D` with one pchannel
each, and 1 of type `DMUS_APATH_DYNAMIC_STEREO` with 21 pchannels.

Per-buffer write census at the main menu, peak scaled ×1e5:

```
buf  0..13   len=176400  22050 Hz 2ch/16bit   writes≈52/s   peak=3
buf 14       len= 65152  44100 Hz 2ch/16bit   writes≈8/s    peak=27868
```

So at the menu the game writes into **exactly one** of its own buffers, and that one
carries real signal — it is the music we hear. The fourteen dmsynth sinks are written
continuously with what is effectively silence.

Only `bgm.dat` is open in `/proc/<pid>/fd` during gameplay. Nothing else.

## Refuted hypothesis 1 — the positional voices could not get their port

`IDirectMusicAudioPathImpl_GetObjectInPath` had no `case DMUS_PATH_PORT`, so it fell
to `default` and returned `E_INVALIDARG`. The counts were seductive: each of the 13
dynamic-3D paths asks for its port with `GUID_All_Objects`, all 13 were refused, and
the one stereo path that never asks is the one we can hear.

Fixed — `perf_dmport_create` now hands the reference out, both path constructors keep
it, `GetObjectInPath` serves it. Verified: all 28 `GetObjectInPath` calls are now
served, zero unhandled. **The symptom did not change.**

The tell that this was the wrong target came from the user, not from me: the codec
ring is not positional, and it is silent too.

Worth noting, the `FIXME(...): stub` at the top of that function fired *before* the
switch, so 13 refused port requests logged identically to 14 buffer requests that were
being served correctly. That is why the first census was misread. The `FIXME` now
fires only on the fallback and names the stage and interface.

## Refuted hypothesis 2 — Wine drops DirectMusic wave segments

`performance_tool_ProcessPMsg` really does drop them:

```c
    case DMUS_PMSGT_WAVE:
    case DMUS_PMSGT_INTERNAL_SEGMENT_TICK:
    case DMUS_PMSGT_INTERNAL_SEGMENT_END:
    default:
        FIXME("Unhandled message type %#lx\n", msg->dwType);
```

`wavetrack.c` builds the message and `segmentstate.c` uses it for duration, but nothing
plays it. This is a genuine gap in Wine and would silence any game that plays wave
segments.

It is not this game's problem. A full gameplay session produced **zero** messages of
type `0xc`. The only unhandled type seen was `0x4` (tempo), 14 of them. MGS2 does not
play DirectMusic wave segments.

## What is still unexplained, and the suspects

The game manages DirectMusic audio paths actively during play:

```
   14  IDirectMusicAudioPathImpl_SetVolume   at startup
 6612  IDirectMusicAudioPathImpl_SetVolume   during ~2.5 min of gameplay
```

Roughly 40 calls a second, against 13 paths. The game is doing per-voice volume work
every frame — it believes it has voices playing. `SetVolume` is a stub that returns
`S_OK` and does nothing.

### Suspect A — the audio path buffers are four bytes

`performance_CreateStandardAudioPath` is a semi-stub and sizes every path's secondary
buffer with `desc.dwBufferBytes = DSBSIZE_MIN`, and `DSBSIZE_MIN` is **4**. Two samples.
The game asks each path for that buffer — `GetObjectInPath(DMUS_PATH_BUFFER,
IID_IDirectSoundBuffer8)`, 14 times, served — and caches the pointer.

If MGS2's voice pool writes effect PCM into those buffers, everything past two samples
is gone and no error is ever reported. The format is wrong too: the stub hardcodes
`44000` Hz mono, not 44100.

Against this: no writes to any 4-byte buffer appeared in the menu census. The gameplay
census that would settle it has not been captured yet — see the constraint below.

### Suspect B — the synth renders into the wrong buffer

`perf_dmport_create` calls `IDirectMusicPort_SetDirectSound(port, perf->dsound, NULL)`
— NULL buffer. So each port's synth renders into its own sink rather than into the
audio path's buffer, which means the path's volume, pan and 3D settings apply to
nothing. Fourteen sinks × 88 KB/s of silence are mixed every period regardless.

### Suspect C — the effects never become PCM at all

The game's own mixer may be producing silence because the effect samples were never
loaded or decoded. Against this: the `+file` channel was run during the earlier
disc-error work and proved that no file open or read fails. For it, only `bgm.dat` is
open, and `codec.dat` is never touched even when the codec rings.

## The measurement constraint

This is the reason the brief exists rather than more data.

The device is CPU-bound at ~37 fps and any instrumentation on a hot path is felt
immediately. The first per-buffer census computed a true peak over every sample of
every `Unlock` — about 1000 `Unlock` calls a second across 15 active buffers — and made
the game unplayable. Sampling at most 64 samples per write fixed the arithmetic, but
the session still ran badly, and part of that turned out to be two game instances
running at once because background launches survive the ssh session that started them.

Practical limits for anything proposed here: no full `WINEDEBUG` channels during
gameplay, counters must report at most once a second, and per-call work must be O(1),
not O(bytes).

## Questions

1. **How does MGS2's PC sound engine emit effects?** It clearly streams its own mix.
   Does it use the DirectMusic audio path buffers as voice sinks, or only as volume and
   3D handles while writing PCM into its own `CreateSoundBuffer` buffers? Anything from
   the MGSHDFix / Substance modding community on the audio path would shortcut all of
   this.
2. **Is `DSBSIZE_MIN` for the audio path buffer known to break other titles?** If some
   Wine bug or patch already addresses `CreateStandardAudioPath` buffer sizing, that is
   the first thing to try.
3. **What is the correct size and format** for a `DMUS_APATH_DYNAMIC_3D` path buffer on
   Windows? If an app can query it via `GetCaps` and adapt, the 4-byte buffer is
   survivable and suspect A is wrong.
4. **Does any Wine version implement `DMUS_PMSGT_WAVE` playback or a non-NULL
   `SetDirectSound` for the port?** Both are real gaps; a known upstream patch is worth
   backporting even though neither is this bug.
5. **Is there a cheap way to identify which game buffer a sound belongs to** — for
   instance, correlating `Play` calls with buffer contents — that does not scan PCM on
   the `Unlock` path?

## Current state

Everything below is in place and working; the port fix and the honest `FIXME` are kept
because both are correct, independent of this bug.

* `dmime_port.dll` — `DMUS_PATH_PORT` served, `GetObjectInPath` reports only genuinely
  unhandled cases. Default in `launch.sh`.
* `dsound_bufcensus.dll` — per-buffer write census behind `MGS2_DSOUND_PROBE=2`,
  sampled peaks. **Not** default; diagnostic only.
* Audio otherwise as brief #9 left it: 44.1 kHz, music and ambience correct.
* ~37 fps in gameplay.

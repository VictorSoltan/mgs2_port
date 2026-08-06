# MGS2 Substance on RG353VS — research brief #12

## Silent sound effects, round two: four hypotheses down

Supersedes brief #11. Music and ambience play; footsteps, punches, weapon handling and
the codec ring are silent. Since #11 an external review proposed a specific mechanism,
it was tested on the live game, and it turned out to be a real Wine defect that is not
the cause. Three others died the same way.

This brief exists because the remaining question is now a single binary one, and the
device makes it expensive to answer.

**Correction to brief #11.** It claimed "MGS2 mixes its own audio and streams the
result — 16 `Play` calls against 51900 `Unlock` calls." The ratio was real; the
inference was wrong. The per-buffer census shows the fourteen dmsynth sink buffers
account for roughly 728 `Unlock` calls a second between them, and the game's own
streaming buffer for four to eight. Almost all of that 51900 is Wine writing silence to
its own synth sinks, not the game mixing. Please disregard that conclusion.

## Refuted, with the evidence

**1. The positional voices could not get their port.** `GetObjectInPath` had no
`case DMUS_PATH_PORT`; all thirteen dynamic-3D paths were refused with `E_INVALIDARG`.
Fixed by keeping the port reference in the audio path. Verified: all 28 requests now
served, zero unhandled. Sound unchanged. The tell was the user's, not mine — the codec
ring is not a positional sound.

**2. Wine drops DirectMusic wave segments.** True — `performance_tool_ProcessPMsg` puts
`DMUS_PMSGT_WAVE` in its `default:` case. But a full gameplay session produced **zero**
messages of that type. MGS2 does not use them.

**3. The audio path `SetVolume` stub mutes the effects.** The game does call it — 14
times at startup, **6612** times during two and a half minutes of play — and it is a
stub. But the game also sets the DirectSound buffer volume directly, and correctly:
the one voice buffer it started was played at `-10000` and then raised to `0` by five
`IDirectSoundBuffer::SetVolume` calls. It is not relying on the audio path for level.

**4. Deferred voice allocation is unimplemented.** The game creates its voice buffers
with `DSBCAPS_LOCDEFER` and plays them with `DSBPLAY_TERMINATEBY_TIME |
DSBPLAY_TERMINATEBY_PRIORITY`. Wine mentions `DSBCAPS_LOCDEFER` in exactly two places,
neither of which allocates anything, and handles no `DSBPLAY_TERMINATEBY_*` flag at
all. Since Wine mixes everything in software there is no voice to allocate, so this
cannot silence a buffer — but it means the flags are silently ignored.

## The routing defect: real, confirmed live, and inert

The external review proposed that `perf_dmport_create` destroys the global PChannel map
on every audio path, so the last path created owns all routing. That is correct, and it
is worse than described: `channel_block_init(perf, i, port, i + 1)` starts at block **0**
for every path, so all fourteen claim the same channels — the `wine_rb_destroy` only
removes the higher blocks as well.

Instrumented and captured on the running game. Each line is one
`CreateStandardAudioPath`, showing which port owns PChannel 0 afterwards:

```
path 08651A78 type 8 pchannels 21 port 02B9A098; pchannel 0 -> port 02B9A098
path 08651E98 type 6 pchannels  1 port 02B9B368; pchannel 0 -> port 02B9B368
...
path 0C398818 type 6 pchannels  1 port 0BDF9718; pchannel 0 -> port 0BDF9718
```

The 21-channel stereo path is created **first** and is dispossessed immediately. Message
routing confirms the consequence — after startup every MIDI message goes to one port:

```
route types: midi=16 note=0 patch=0 curve=0 wave=0 notif=0 stop=0
route port 0BDF9718 got 16
```

`performance_PlaySegmentEx` also ignores its `audio_path` argument entirely, so nothing
downstream can know which path a segment belongs to.

**But fixing this would change nothing audible**, because DirectMusic is carrying no
sound at all:

| measured over a session | count |
| --- | --- |
| `DMUS_PMSGT_NOTE` | 0 |
| `DMUS_PMSGT_WAVE` | 0 |
| `DownloadInstrument` to any port | **0** |
| MIDI messages | 14–16 per second |

No instruments are downloaded to any of the fourteen ports, so no port could render a
note even if it received one. All fourteen synth sinks measure a peak of 3 parts in
100000 — silence. The MIDI traffic with zero notes is control data.

## What the buffers actually show

62 `CreateSoundBuffer` calls at startup:

| count | bytes | created by | flags |
| --- | --- | --- | --- |
| 15 | 32576 | the game | LOCDEFER, GETCURRENTPOSITION2, GLOBALFOCUS, CTRLPOSITIONNOTIFY, CTRLVOLUME, CTRLPAN, CTRLFREQUENCY |
| 4 | 65152 | the game | same without CTRLPAN |
| 14 | **4** | dmime `CreateStandardAudioPath` (`DSBSIZE_MIN`), 44000 Hz mono | CTRL3D, CTRLFX, CTRLVOLUME, … |
| 14 | 176400 | dmsynth sinks, 22050 Hz stereo | |
| 15 | 0 | primaries | |

Per-buffer write census at the main menu — the game writes into exactly one of its own
buffers, and only that one carries signal:

```
buf 0..13  len=176400  22050 Hz 2ch  writes≈52/s  peak=3
buf 14     len= 65152  44100 Hz 2ch  writes≈8/s   peak=27868
```

Every `Play` at the menu, with the volume in force at that moment:

```
14 x  len=176400 22050Hz/2ch vol=0      flags=0x1     (the synth sinks)
 1 x  len= 32576 44100Hz/1ch vol=-10000 flags=0x29    (a game voice buffer)
```

and that voice buffer, tracked across the session:

```
buf 1 08556BE0  writes=0  volset=5  vol=0
```

The game starts a voice at `DSBVOLUME_MIN`, raises it to maximum — and **never writes a
byte into it**.

Finally, file access. A poll of `/proc/<pid>/fd` across 2665 samples during active
gameplay found exactly one game data file open: `bgm.dat`. Not `codec.dat` (84 MB), not
`vox.dat` (1.1 GB), neither of which can plausibly be resident in memory. The caveat is
that stage assets are loaded and closed before steady-state play, so this does not rule
out effect samples having been read at stage load.

## The one open question

Either the played voice buffer is a duplicate created with `DuplicateSoundBuffer`, which
shares `BufferMemory` with an original the game does fill — in which case the audio
exists and Wine's mixer is losing it — or the game genuinely plays voices it never fills,
in which case the failure is upstream of the audio stack entirely.

The discriminator is whether `Play` fires on a 32576-byte buffer at full volume when the
player takes a step. That measurement has not been captured yet.

## Why the measurement is hard here

Worth stating plainly, because it has shaped every round.

The device is CPU-bound. Measured on the same scene: **25.88 fps clean, 20.05 fps with
the per-buffer census** — a 23% cost, which the user reported as unplayable. The first
version of that census computed a true peak over every sample of every `Unlock`, roughly
1000 calls a second, and was far worse. A `/proc` file-descriptor poller written without
a sleep in its loop cost real frame rate of its own.

Two harness failures compounded it: a game launched over ssh with `setsid nohup` survives
both the ssh session and the cancellation of the launching task, so a diagnostic instance
and a user-started instance ran simultaneously more than once; and `mgs_stop` failed to
kill one of them, so a session the user was told was clean was in fact the heavy census
build. Instance count is now verified by exact `comm` before and after every launch.

The probe now waiting to run logs one line per `Play` and nothing else — tens of lines a
minute rather than thousands a second.

## Questions

1. **How does MGS2's PC sound engine submit effect audio?** Everything measured says it
   is not DirectMusic: no notes, no waves, no instrument downloads. Does it write PCM
   into DirectSound secondary buffers and play duplicates from a voice pool of fifteen?
   Anything concrete from the MGSHDFix or Substance modding community would shortcut this.
2. **Is there a known interaction between `DSBCAPS_LOCDEFER` voice management and Wine?**
   Wine ignores the flag and the `DSBPLAY_TERMINATEBY_*` flags. Are there titles where
   this is known to matter?
3. **Could effect samples be loaded at stage load and never re-read?** If so, what file
   in the retail layout holds them — the `stage/<name>/*.sdx` archives, or something
   else? Knowing the filename makes the loading question answerable in one poll.
4. **`CreateStandardAudioPath` creates its path buffer with `DSBSIZE_MIN` (4 bytes) at
   44000 Hz mono.** Is this known to break other DirectMusic titles, and is there an
   upstream patch?
5. **Are the fourteen idle synth sinks worth disabling?** They mix 14 × 88 KB/s of
   silence every period on a device that cannot spare it — a performance question rather
   than a correctness one.

## Current state

* `dmime_port.dll` — `DMUS_PATH_PORT` served; `GetObjectInPath` now reports only
  genuinely unhandled cases instead of an unconditional "stub". Default.
* `dmime_route.dll`, `dmusic_route.dll` — path/port/message census behind
  `MGS2_DM_ROUTE=1`. Diagnostic only.
* `dsound_bufcensus.dll` — `MGS2_DSOUND_PROBE=2` logs `Play` only and is free;
  `=3` adds the per-buffer write census at ~23% frame rate. Not default.
* `dsound_sfxprobe2.dll` — deployed for the clean gameplay run. `MGS2_DSOUND_PROBE=2`
  is event-driven: it logs the byte
  count at each 32576-byte SFX `Play`, duplicate lineage, every actual SFX
  volume/pan change and the first targeted mix (raw/mixed sample peak plus gain).
  It performs no global mixer or `Unlock`-path scan. `MGS2_SFX_RESET=1` is a
  separate, opt-in A/B which clears only that voice's playback cursor, fractional
  resampler state and committed chunk immediately before `Play`; it is off by
  default. The next artifact additionally logs the full-buffer PCM peak at `Play`,
  which distinguishes quiet decoded samples from a normal signal with a quiet attack.
* `launch.sh` gained an `MGS2_DMUSIC_DLL` override hook.
* Audio otherwise as brief #9 left it. ~37 fps in gameplay.

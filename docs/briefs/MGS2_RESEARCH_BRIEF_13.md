# MGS2 Substance on RG353VS — research brief #13

> Superseded by [`MGS2_RESEARCH_BRIEF_14.md`](MGS2_RESEARCH_BRIEF_14.md). The live
> byteswap result disproved the active-fix conclusion below; do not use brief #13 as
> current guidance.

## Status after the DirectSound runs

Supersedes the audio conclusion in brief #12. The game is running with a narrow,
causal DirectSound compatibility fix: only freshly-written members of MGS2's known
SFX pool are converted from big-endian PCM16 byte order to the little-endian PCM16
order requested by their `WAVEFORMATEX`.

Music and ambience are present. Gameplay effects (locker, radio call, footsteps and
similar one-shots) require a live gameplay confirmation with this fix. The two prior
attempts are **rejected**, not promoted:

| change | exact scope | live result |
| --- | --- | --- |
| `MGS2_SFX_BOOST=1` | ×4 gain only for the 32576-byte, 44.1 kHz mono SFX pool | no game effects; only faint interrupted background sound and worse playability |
| `MGS2_SFX_RESET=1` | reset cursor, fractional resampler state and committed chunk on every pool `Play` | no recognisable game effects; gameplay still stutters |

The first was a workaround without a causal basis and must not be used again. The second
fixes a real Wine/MGS2 mismatch, but it is not sufficient to restore audio.

## What is proved

The clean event-only capture is
[`event-only-gameplay/trace.log`](logs/rg353vs/sfxprobe/event-only-gameplay/trace.log).
It contains the user-driven locker/radio gameplay moment.

1. MGS2 has a pool of 32576-byte, 44100 Hz, mono, 16-bit DirectSound secondary
   buffers. Their creation flags include frequency, pan and volume controls; they do
   **not** include `DSBCAPS_CTRL3D`.
2. The game fills those buffers: at gameplay `Play`, the buffers contain 4763 through
   29028 non-zero bytes out of 32576. Thus “the game never loaded a SFX” is false.
3. The game first mutes the voices (`-10000`), calls `Play`, then changes them to
   roughly `-1406` / `-1341` / `-1493` centibels. Wine calculates non-zero gain;
   `-1406` yields `0x3271` (about 0.197) on the intended channel.
4. Wine's mixer processes the pool. For example, after the second batch it reports
   raw/mixed peaks `1369/269`, `2732/408` and `895/161` (scale `1e5`) with
   `audible=1`. Therefore neither DirectMusic routing nor a permanently muted
   DirectSound voice explains the silence.
5. Wine does begin some voices before MGS2 raises their volume. The first four voices
   have already advanced to byte 3068 at `DSBVOLUME_MIN`. Later reuse is demonstrably
   stale: new `Play` calls arrive at byte 4152 and byte 32236. Resetting that state is
   semantically reasonable, but the live `MGS2_SFX_RESET=1` outcome above proves it is
   not the missing-audio fix by itself.
6. A one-shot 1 kHz PCM tone injected into the same SFX pool was audible before the
   first cutscene. This proves the downstream route (Wine's DirectSound mixer, host
   audio stack and device) can reproduce this exact buffer class.
7. The pre-tone, first non-zero effect dump is
   [`sfx_play_01.raw`](logs/rg353vs/sfxformat/sfx_play_01.raw). It has pairs such as
   `10 00`, `0f 00` and `ec ff`. If read as little-endian PCM those become tiny values
   `16`, `15` and `-20`, matching the measured peak of only 68. If read as big-endian
   PCM, the same bytes are ordinary samples `4096`, `3840` and `-4865`. This is direct
   evidence from the retail process, not an inference from source alone.

The global mixer probe also reached non-zero final device samples. It cannot identify
the pool individually because music and other buffers share that final mix, so it does
not prove the quality or full amplitude of an individual SFX waveform.

## Do not revisit

* **DirectMusic:** no `DMUS_PMSGT_NOTE`, no `DMUS_PMSGT_WAVE`, and no instrument
  download occurs in gameplay. Its known routing bugs are real but inert for these
  effects.
* **Force 3D:** false premise; the actual SFX descriptors do not request 3D control.
* **Generic DirectSound gain:** the boost result is negative.
* **Per-`Unlock` logging/census:** it costs about 23% of frame rate and produces an
  unplayable game. It is not a viable observation or shipping mode.

## Root cause and active fix

MGS2 writes decoded effect samples in big-endian order, while the DirectSound buffer it
creates declares standard 16-bit PCM, which is little-endian on the target. Wine
therefore interprets a sample like `0x1000` as `0x0010`: almost silent and with a
distorted waveform. The dump above establishes this directly in the retail run.

The recovered source corroborates the byte pattern: `BP_DecompressVAG()` in
[`BP_SoundSupport.cpp`](mgs_source/MGS2-Source-main/bp/shared/BP_SoundSupport.cpp)
emits the high byte and then low byte of every decoded sample. The source tree is not a
reproducible build of the retail executable, so it is supporting explanation only; the
retail buffer dump is the causal evidence.

`dsound_sfxbyteswap.dll` implements the smallest correction. Each matching effect
buffer is marked dirty on `Unlock`; on its next `Play` the DLL swaps the two bytes of
each 16-bit sample once. The dirty state belongs to the shared buffer memory, so a
duplicated DirectSound object cannot swap it back. There is no mixer-thread work, no
logging, no gain manipulation and no tone injection.

## Precise next places to inspect

Choose one of these; each answers a different remaining question.

1. **Live check.** Confirm locker, radio and footsteps in ordinary gameplay. This is a
   real fix run, not a measurement pass.
2. **Voice lifecycle, only if effects remain cut short.** In Wine 11,
   [`IDirectSoundBufferImpl_Play`](recovered-session/wine-11.0/dlls/dsound/buffer.c)
   ignores `DSBPLAY_TERMINATEBY_TIME` and `DSBPLAY_TERMINATEBY_PRIORITY`; the buffers
   carry both flags. A correct implementation of voice termination/stealing may prevent
   stale voices and stutter, but it needs an actual Windows-semantic reference before
   becoming a fix.
3. **Audio underrun independent of SFX, only if performance is still bad.** The reported
   faint interruptions plus gameplay
   stutter could be audio-thread starvation. Inspect the Wine ALSA/PipeWire stream period
   and underrun counters with all SFX changes disabled. This cannot explain valid music
   being present, but it can explain the audible interruptions and performance regression.

## Current operational state

* Console game process: running with `MGS2_DSOUND_DLL=dsound_sfxbyteswap.dll` and
  `MGS2_SFX_BYTESWAP=1`.
* This run has no `MGS2_TRACE`, probe, gain boost, reset, dump or tone option.
* `dsound_sfxboost.dll`: rejected; leave unused.
* `dsound_sfxformat.dll`: diagnostic tone/dump artifact only; do not mount for normal
  play.

# MGS2 Substance on RG353VS — research brief #14

## Executive status

This brief supersedes the active-fix conclusion in brief #13.

Gameplay SFX are still missing. Music/ambience reach the output, but the user hears
continuous background stuttering and no new recognisable locker, radio or gameplay
sounds. The `PCM16` byte-swap experiment is **rejected**: it was definitely loaded,
did not restore effects and made the audio experience severely broken.

The failed run has been stopped. Its temporary bind mount was removed, the lock is
free, and the console now has the stock Wine DirectSound DLL active again:

```text
/usr/lib/wine/i386-windows/dsound.dll
SHA-256 6d292d95c7f70b1101eec2bbff7caef154d0bea7cfd3177fc84813fcce2455e3
```

## Live byteswap result and deployment proof

The experimental artifact was `dsound_sfxbyteswap.dll`, SHA-256:

```text
5fbbf24e5aa2f0fca189c454acf0963abc0cfaa45dd50c90c3c7d625aaca1777
```

At runtime, process `mgs2_sse_rg353vs_port.exe` contained both intended variables:

```text
MGS2_DSOUND_DLL=dsound_sfxbyteswap.dll
MGS2_SFX_BYTESWAP=1
```

The mapped `/usr/lib/wine/i386-windows/dsound.dll` and the deployed experimental DLL
had the same SHA-256, device and inode while the game was running. The launcher had
therefore performed its bind mount correctly. This is a valid negative test of the
implementation, not a DLL-selection failure.

User-observed result:

* the game was running;
* sound stuttered severely by itself, with constant interruptions in the background;
* no recognisable new gameplay effect was audible.

Do not retry or ship byte swapping for this SFX pool.

## Correction to the dump interpretation

The diagnostic tone and dump remain useful, but the earlier conclusion drawn from the
dump was too strong.

* The injected 1 kHz tone was audible before the first cutscene. This proves that the
  downstream path can reproduce audio placed in this DirectSound buffer class.
* The first non-zero 32576-byte dump had a little-endian peak of only 68 and contained
  sequences such as `10 00`, `0f 00` and `ec ff`.
* Reading those pairs as big-endian produces much larger numbers, but this alone does
  not prove that they are big-endian PCM. The captured buffer may be a quiet waveform,
  a transition, an internal/non-gameplay voice, or incorrect data for another reason.
* The recovered-source `BP_DecompressVAG()` writes high byte then low byte, but that
  source tree is not a reproducible build of the 2003 retail executable. It cannot
  establish the retail path or representation.
* The correctly loaded byte-swap run failed audibly. That live result overrides the
  endian interpretation.

Relevant dump artifacts:

* [`sfx_play_01.raw`](logs/rg353vs/sfxformat/sfx_play_01.raw)
* [`sfx_play_01.txt`](logs/rg353vs/sfxformat/sfx_play_01.txt)
* [`as_pcm44100.wav`](logs/rg353vs/sfxformat/as_pcm44100.wav)

## Facts that remain established

The clean event-only gameplay capture is
[`event-only-gameplay/trace.log`](logs/rg353vs/sfxprobe/event-only-gameplay/trace.log).
It includes the user opening a locker and receiving a radio call.

1. MGS2 creates a pool of 32576-byte, 44100 Hz, mono, 16-bit DirectSound secondary
   buffers with frequency, pan and volume control, but no 3D-control flag.
2. The game writes non-zero bytes into members of that pool and calls `Play` during
   gameplay.
3. MGS2 uses a mute-then-play-then-unmute sequence. Typical final volumes are around
   `-1406`, `-1341` and `-1493` centibels; Wine calculates non-zero gain.
4. Wine processes these buffers in its mixer and can produce non-zero mixed samples.
5. Some voices start while muted and some later `Play` calls reuse stale playback
   positions. Resetting cursor/resampler/committed state did not restore recognisable
   effects in the live test.
6. The timing correlation does not identify which pool member contains the expected
   locker or radio waveform. A `Play` near the event is not proof of waveform identity.
7. Music/ambience being present and the injected tone being audible rule out a wholly
   dead device path. They do not rule out underruns or scheduling failure causing the
   repeated background stutter.

## Rejected paths

* **DirectMusic repair:** gameplay produces no relevant note, wave or instrument
  messages. Leave it alone.
* **Generic gain boost:** no recognisable SFX; worse playability.
* **Forced cursor/reset workaround:** fixes a real stale state, but not the missing
  effects.
* **PCM16 byte swap:** correctly deployed and directly rejected by the live result.
* **Force 3D:** the relevant buffers do not request `DSBCAPS_CTRL3D`.
* **Per-`Unlock` census or hot mixer logging:** previously cost roughly 23% frame rate
  and made gameplay unplayable.
* **More tone/dump runs of the same class:** the downstream question they answer is
  already settled.

## Exact remaining inspection targets

No further broad gameplay run is justified until one of these yields a concrete code
change or a narrow binary prediction.

### 1. Retail SFX producer — primary target

Statically trace the retail path that writes the 32576-byte pool:

* locate the call sites that create buffers with `(32576, 44100 Hz, mono, PCM16)`;
* follow each `Lock`/write/`Unlock` producer back to its stage asset and decoder;
* establish whether the written bytes are decoded PCM, silence/envelope data, or a
  different intermediate representation;
* derive expected sample scale and byte order from retail instructions, not the
  recovered-source implementation;
* identify which voice/asset should correspond to locker, radio and footsteps.

Retail executable:
[`mgs2_sse_rg353vs_port.exe`](recovered-session/binaries/mgs2_sse_rg353vs_port.exe),
SHA-256 `29759e6f06eaea4d61bb6aef5a5ef45a936eac1e76fa0c3471cf4f231349aaa0`.
Likely assets are under `cdrom.img/stage/<stage>/pk*.sdx`.

### 2. DirectSound voice lifecycle — secondary target

Wine 11's
[`IDirectSoundBufferImpl_Play`](recovered-session/wine-11.0/dlls/dsound/buffer.c)
ignores `DSBPLAY_TERMINATEBY_TIME` and `DSBPLAY_TERMINATEBY_PRIORITY`, while MGS2 passes
both flags. Determine native DirectSound semantics for deferred/managed voice stealing
and whether ignoring the flags can leave this pool exhausted or repeatedly playing
stale regions. Do not implement another unconditional reset; that exact experiment has
already failed.

### 3. Background stutter as a separate audio-stream problem

Use only host-side, low-overhead counters to establish whether the current stock run
has ALSA/PipeWire underruns, thread starvation or period misses. The repeated stutter
may be independent of the missing SFX. Any capture must avoid per-buffer logging and
must report a concrete underrun/scheduling counter rather than another large trace.

## Operational state

* Game process: stopped after the rejected byteswap run.
* `/tmp/mgs2-substance.lock`: free.
* System DirectSound: restored, hash recorded above.
* `dsound_sfxbyteswap.dll`: rejected diagnostic artifact; leave unused.
* `dsound_sfxformat.dll`: tone/dump diagnostic artifact; leave unused.
* `dsound_sfxboost.dll`: rejected; leave unused.


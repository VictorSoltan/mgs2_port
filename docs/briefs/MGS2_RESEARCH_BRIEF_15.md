# MGS2 / RG353VS — research brief #15

## Scope and current status

This brief supersedes the active DirectSound conclusions of briefs #13 and #14.
It is a targeted handoff for research into **missing gameplay effects**. Do not
reopen DirectMusic, PCM byte order, or PipeWire-period tuning without new,
specific evidence.

Latest user result, with the normal audio baseline restored:

* background music/ambience in gameplay no longer stutters;
* the game is smoother than with the late 44.1 kHz / 30 ms PipeWire setting;
* menu and gameplay effects (steps, punches, interactions) are still absent.

There are therefore two separate defects. The stream-stutter regression has a
known configuration rollback. The missing effects remain open.

## Stable baseline for all future work

`/storage/roms/ports/MGS2-Substance/launch.sh` has been restored for the next
launch to this state:

| component | active/default state |
| --- | --- |
| DirectSound | stock `/usr/lib/wine/i386-windows/dsound.dll`; no bind mount by default |
| DirectMusic audio path | `dmime_graphqi.dll` only |
| DirectMusic synth | `dmsynth_wine112.dll` |
| Wine audio backend | `winealsa`; `winepulse.drv` disabled because it cannot relocate under box86 |
| client rate / period | no forced `PIPEWIRE_ALSA` and no forced `PIPEWIRE_QUANTUM`; Wine/PipeWire choose the normal F32LE/48000 path |
| tracing | `WINEDEBUG=-all`, `MGS2_TRACE=0` |
| performance fix | `user32_peek1.dll`, `MGS2_PEEK_HOT=401176`, `MGS2_PEEK_WAIT=1`, `MGS2_PEEK_WAIT_MS=4` |

The configuration deliberately **does not** default to any `dsound_*.dll`.
Rejected DLLs remain on the device only as evidence; do not mount them.

## What was fixed by the baseline rollback

The later launcher forced these settings:

```sh
PIPEWIRE_ALSA='{ alsa.rate=44100 node.name=mgs2-audio }'
PIPEWIRE_QUANTUM=1440/48000
DMIME_DLL=dmime_port.dll
```

They were introduced for a CPU benchmark, but the user eventually reported
constant audible stutter, including in menus. Reverting to the brief-9 audio
baseline — stock PipeWire period/rate plus `dmime_graphqi.dll` — stopped the
background stutter in live gameplay. Keep this rollback while researching
effects; otherwise a performance regression masks the actual result.

## CrossOver Android 17: definitive result

The supplied source tree is:

```text
crossover-android-sources-17.0.0.android21/source/wine/
```

It is Wine 2.8 based. The official archive was compared directly with it:

```text
https://dl.winehq.org/wine/source/2.x/wine-2.8.tar.xz
```

`diff -qr` reported no differences for both:

```text
dlls/dsound/
dlls/winealsa.drv/
```

Thus CrossOver 17 contains **no separate CodeWeavers DirectSound or ALSA patch
to port**. The earlier successful CrossOver-derived work was the GLES capability
logic used by `wined3d_dbg150_cxcaps.dll`, not audio code.

The tree also contains `dlls/wineandroid.drv/mmdevdrv.c`, an Android OpenSL ES
driver. It is not applicable here: the running MGS2 process maps `winealsa.drv`
and `winealsa.so`, never `wineandroid.drv`.

### Old Wine 2.8 compatibility A/B tests

Two observable differences from old Wine were built as clean Wine 11 DLLs and
tested. Neither restored game effects.

| test | isolated change | result |
| --- | --- | --- |
| `dsound_cx17clean.dll` | do not preserve `writelead` bytes when an app locks across the live mix cursor (`commit_next_chunk`) | no gameplay effects; rejected |
| `dsound_poswrap_clean.dll` | change `SetCurrentPosition(pos >= buflen)` from `E_INVALIDARG` to `pos %= buflen`, as Wine 2.8 did | no gameplay effects; rejected |

Both DLLs were built from a clean Wine 11.0 archive with no old MGS probes,
byte swapping, gain changes, tone injection, or logging. The negative result
is therefore meaningful.

## What DirectSound is demonstrably doing

### Output chain is alive

1. A 200 ms, 1 kHz test tone injected into the 32,576-byte pool was audible
   before the first cutscene. Downstream DirectSound → Wine ALSA → host output
   is functional.
2. During the old targeted capture, Wine's own mixer reported non-zero raw,
   post-volume, and final mix peaks for the 32,576-byte voices. For example,
   `event-only-gameplay/trace.log` records `raw=1369`, `mixed=269` on an
   audible voice, followed by larger valid peaks on other fragments.
3. A 120-snapshot host `pw-top` capture during the stuttering configuration
   showed no growing error counter on the MGS2 PipeWire node (`ERR=0` in all
   snapshots). This does not prove perfect scheduling, but it rules out a
   PipeWire xrun avalanche as the explanation for missing effects.

Relevant host capture:

```text
logs/rg353vs/stutter/pw-top-live-producer-neutral.txt
SHA-256 fff3da7705cb11bc29ee99f9e71cba09d16df462728ae6748ba4316f82e7b029
```

### MGS2 keeps its effect voices alive

The DirectSound logs establish a lifecycle that invalidates the earlier
assumption “an effect equals a new Play call.”

* The game creates a pool of 32,576-byte, 44,100 Hz, mono, PCM16 secondary
  buffers carrying `DSBCAPS_LOCDEFER`.
* It starts them with `DSBPLAY_LOOPING` (`flags=0x1`; some initial voices use
  `0x29`) while the buffers are muted at `DSBVOLUME_MIN` (`-10000`).
* It subsequently changes volume. Captured examples move voices to `-1406`
  with amp factors `0x3271/0x3271`, then mute them again.
* Pan values at pool construction are `-10000`, `0`, and `10000`; the pool is
  a spatial/voice distribution, not a single ordinary one-shot buffer.

Existing logs:

```text
logs/rg353vs/sfxprobe/event-only-gameplay/trace.log
logs/rg353vs/sfxprobe/manual-gameplay/trace.log
```

### Important correction: the producer result

The marker-armed producer DLL watched only for a new `Play` on that exact pool.
While armed, the user performed two punches and one step. No matching `Play`
occurred, so it produced no capture.

This **does not** prove that the pool is unrelated to effects. It proves that
these actions do not start a fresh DirectSound buffer. The likely action path
is a control/write operation on an already-looping voice: `Lock`/`Unlock`,
`SetCurrentPosition`, `SetVolume`, frequency, and/or 3D state.

The previous producer design was therefore too late in the lifecycle: it only
emitted its history when `Play` occurred.

## DirectMusic: keep out of scope

The original complete-silence issue was real and fixed by
`dmime_graphqi.dll`: MGS2 requests `IID_IDirectMusicGraph` through an
`IDirectMusicAudioPath` QueryInterface, which stock Wine 11.0 returned as
`E_NOINTERFACE`.

Subsequent route/message work established that missing gameplay effects are
not explained by absent DirectMusic note/wave/instrument messages. The user
explicitly requested that DirectMusic remain untouched. Do not change
`dmime`, `dmusic`, or `dmsynth` as a proposed SFX repair.

## Rejected hypotheses and artifacts

| hypothesis / artifact | outcome |
| --- | --- |
| `MGS2_SFX_BOOST=1` / `dsound_sfxboost.dll` | no recognisable effects; worsened playability |
| per-Play cursor/fractional-resampler/committed reset | no effects |
| PCM16 byte swap / `dsound_sfxbyteswap.dll` | definitely loaded; no effects; severe stutter; rejected |
| `commit_next_chunk` compatibility / `dsound_cx17clean.dll` | no effects |
| old Wine position wrapping / `dsound_poswrap_clean.dll` | no effects |
| DirectMusic repair beyond Graph QI | not the SFX path; out of scope |
| PipeWire error growth | absent in the 120-snapshot capture |
| the 32,576-byte data being sent nowhere | false: test tone and non-zero mixer output prove the output chain works |

Useful artifact hashes:

```text
stock dsound.dll              6d292d95c7f70b1101eec2bbff7caef154d0bea7cfd3177fc84813fcce2455e3
dsound_cx17clean.dll          ed2173e1ae90e60dab5a891384c67beb1bfcc4865c848d67c02124e2ff872c70
dsound_poswrap_clean.dll      f434cb08774bebe536dcd4d10bdbe07e203586865ca0fa3c62dafe0071dc5ffb
```

## Concrete research questions

Please return a **small patch with native DirectSound semantics or an exact
reference**, not an unconditional gain/reset workaround. The useful questions
are:

1. **Deferred-location voice allocation and termination.** MGS2's pool uses
   `DSBCAPS_LOCDEFER`; it also uses `DSBPLAY_TERMINATEBY_TIME` and
   `DSBPLAY_TERMINATEBY_PRIORITY` (`0x29` includes looping plus terminate
   flags). Wine 11 ignores the termination/priority semantics. What must a
   native DirectSound implementation do for these flags on software/deferred
   voices: allocation, stealing order, stopping, cursor, and status?
2. **Persistent looping voice reuse.** With a looping voice muted at `-10000`,
   which sequence of `Lock`, `Unlock`, `SetCurrentPosition`, `SetVolume`, and
   `Play` is required to make freshly written data audible under native
   DirectSound? In particular, can a client safely rewrite data near the live
   cursor without an explicit new Play?
3. **LOCDEFER / AcquireResources contract.** Wine's
   `IDirectSoundBuffer8::AcquireResources` remains a FIXME that fakes success.
   Is MGS2 relying on a resource-state transition or failure/return value that
   Windows provides for these buffers?
4. **3D vs ordinary volume.** Establish whether these voices are truly
   `DSBCAPS_CTRL3D`, and whether a deferred 3D parameter update needs a
   listener `CommitDeferredSettings` to update the effective amp factors. A
   patch should name the exact faulty Wine function and preserve normal volume
   semantics.
5. **Buffer state/status after a looped voice is reused.** Does Wine 11 expose
   the same `GetStatus`, current position, and notification behavior as native
   DirectSound when `DSBPLAY_LOOPING` is combined with termination flags?

## Narrowest next measurement, if a reference is not enough

Do not repeat per-mix or per-Unlock scans: they made the RG353VS unplayable.
Build a **marker-armed, fixed-size event recorder** for only the 32,576-byte
44.1 kHz mono `DSBCAPS_LOCDEFER` pool. It should write one small record per
call after `/tmp/mgs2-sfx-arm` is created:

```text
tick, object/memory id, method,
Lock(cursor, bytes, returned spans), Unlock(spans),
SetCurrentPosition(value, HRESULT), SetVolume(value),
SetFrequency(value), Play(flags), Stop,
3D setter apply/deferred flag, listener CommitDeferredSettings,
state, sec_mixpos, writelead, committed state
```

The recorder must flush immediately on a bounded number of events (for
example 128) and must not wait for a new `Play`. A single marker followed by
one step or one punch is sufficient. This will identify the actual action
path without another performance-destroying trace.

## Source landmarks

| source | relevant area |
| --- | --- |
| `recovered-session/wine-11.0/dlls/dsound/buffer.c` | `Play`, `Lock`, `Unlock`, `SetCurrentPosition`, volume controls; this working tree also contains old diagnostic code, so use `wine-11.0.tar.xz` for clean upstream context |
| `recovered-session/wine-11.0/dlls/dsound/mixer.c` | persistent secondary-buffer mixing and committed-chunk behavior |
| `recovered-session/wine-11.0/dlls/dsound/sound3d.c` | deferred 3D buffer/listener updates and `CommitDeferredSettings` |
| `recovered-session/wine-11.0/dlls/dsound/primary.c` | primary-device 3D/listener initialization |
| `crossover-android-sources-17.0.0.android21/source/wine/dlls/dsound/` | exact vanilla Wine 2.8 comparison point, not a proprietary audio patch |
| `recovered-session/wine-11.0.tar.xz` | clean Wine 11.0 source archive for isolated builds |

## Operational rule

Any future proposed DLL must be built from the clean Wine 11.0 archive and
contain one named behavior change. Keep stock `dsound.dll` as default until a
test restores a recognisable gameplay effect **without reintroducing audio
stutter**.

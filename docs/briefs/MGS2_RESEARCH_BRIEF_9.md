# Research brief #9 — the audio investigation in full, written so someone can find my mistake

> **SOLVED, 2026-08-02.** The mistake was found, and it was the one flagged in §8.2: the
> amplitude probe was watching a buffer that was not the game's, and the conclusion "the
> application submits silence" was overstated. The game was never *submitting* anything —
> it could not finish building its audio path.
>
> ```
> warn:dmime:IDirectMusicAudioPathImpl_QueryInterface
>      (08650BB8, IID_IDirectMusicGraph, 0195FDCC): not found
> ```
>
> MGS2 asks its DirectMusic AudioPath for the tool graph with a plain `QueryInterface`.
> Windows supports that; Wine 11.0 offered the graph only through `GetObjectInPath` and
> returned `E_NOINTERFACE` here. The game treats it as fatal — it carries the string
> `IID_IDirectMusicGraph Refarence Error(%x)` — and stops setting up audio.
>
> Fix: handle `IID_IDirectMusicGraph` in `IDirectMusicAudioPathImpl_QueryInterface`,
> creating the tool graph on demand exactly as `GetObjectInPath` already does
> (`dlls/dmime/audiopath.c`). Built as a PE DLL, shipped as `dmime_graphqi.dll`.
>
> Result, measured on the speaker sink monitor: **peak 3305, 1 426 657 of 1 428 992 samples
> non-zero (99.8%)**, against peak 0 in every previous run — and audible to the user.
>
> What this retrospectively explains: the "active but silent" PipeWire stream, dmsynth
> rendering nothing, zero ACM calls, and why every fix aimed at the output path did nothing.
> The static evidence that led here was that the executable imports DSOUND, WINMM and
> MSACM32 but no DirectMusic — while containing DirectMusic 8 COM error strings, meaning it
> uses the API dynamically. Checking whether the game creates those objects at all was the
> decisive step.

Self-contained. Supersedes briefs #7 and #8 for audio. Performance is brief #6; project
history is `MGS2_PROJECT_STATE.md`.

The game produces no sound. After a very long session the audio path has been measured at
every layer, eleven hypotheses have been killed, two real faults have been fixed, and the
silence is unchanged. Four of my own conclusions were published and later withdrawn, all
four because the measuring harness lied rather than because the port changed.

This document is deliberately written to be falsifiable: every claim carries the
measurement behind it, and §8 lists the places I think I am most likely still wrong.

---

## 1. Setup

Anbernic RG353VS — RK3566, four Cortex-A55, Mali-G52, **libmali / GLES 3.2 only**, 975 MB
RAM, RockNIX. box64 runs Wine 11.0 in old-WoW64 mode; the game is a 32-bit PE, so **the
whole 32-bit stack — game, wined3d, opengl32, win32u, ntdll, dsound, dmsynth — is emulated
by box86**. Only libmali, PipeWire and the kernel are native. Wine is not built by RockNIX;
it unpacks Kron4ek's `wine-11.0-amd64` binaries. PipeWire 1.2.6, WirePlumber 1.2.6,
box86 v0.3.9, box64 v0.4.2.

Metal Gear Solid 2: Substance (PC, 2001, Direct3D 8). Playable: menus, codec with
portraits, Tanker gameplay, rain, cutscene visuals, ~20–24 fps unpinned, 60 fps in menus.

Two symptoms, possibly one fault:

1. **No audio at all** from the game.
2. **In-engine cutscenes render for a few seconds, freeze**, and the game shows *"There's a
   problem with the disc you're using."*

## 2. Two things that were genuinely broken and are now fixed

### 2a. The device's PulseAudio layer (system-wide, not game-specific)

`pipewire-pulse` serves `/run/pulse/native` and `tcp:127.0.0.1:4713`, but clients follow
`XDG_RUNTIME_DIR` to a stale `/var/run/0-runtime-dir/pulse/native` and block on it. `pactl`
hung indefinitely; EmulationStation, which runs `SDL_AUDIODRIVER=pulseaudio`, was silent.

`PULSE_SERVER=tcp:127.0.0.1:4713` makes `pactl info` answer immediately and gives
EmulationStation an active stream. Persisted in
`/storage/.config/autostart/60-pulse-server-env.sh` plus `profile.d`, because `/etc` is
read-only.

The accompanying log line — `Failed to acquire org.pulseaudio.Server ... AccessDenied` — is
a red herring; no D-Bus policy change was needed.

### 2b. dmsynth starvation

Wine 11.0 wakes the DirectMusic sink thread every ~10 ms (`BUFFER_SUBDIVISIONS 100`) to
query the play cursor and lock the buffer. This port cannot sustain it: **816 "Underrun
detected" in one run**. The Wine 11.2 series (7 commits over `dlls/dmsynth/`,
`BUFFER_SUBDIVISIONS` 100 → 10, fixed write latency, cursor query on its own thread) was
applied and built as a PE DLL. **Underruns dropped to 1.**

Real fix, no audible change. The symptom it removed was not the cause.

## 3. The decisive measurement: Wine delivers exactly what the game gives it

Four amplitude probes were compiled into `dsound`, each reporting a running peak once a
second as a multiple of 1e-5 of full scale:

| stage | what it measures | max over a whole run |
| --- | --- | --- |
| `unlock` | what the **application** wrote into a secondary buffer | 3 |
| `tmp` | after `cp_fields` — PCM → float and resampling | 5 |
| `vol` | after `DSOUND_MixerVol` — volume and 3D attenuation | 5 |
| `final` | the device buffer before `IAudioRenderClient_ReleaseBuffer` | 8 |

Read from the very first report on a clean single-instance run, not just at steady state
(an earlier reading only looked at steady state and could have missed a loud buffer written
once at load; it did not).

Nothing is zeroed anywhere. Signal enters at about one LSB of a 16-bit sample — roughly
−90 dBFS — and arrives intact. Independently, `pw-record` on the speaker sink monitor gives
**1 447 936 samples, peak 0, non-zero 0**.

**Conclusion drawn at the time: "the application submits silence; Wine faithfully delivers
silence."** That was too strong, and it is the error this document was written to expose.
What the probe actually established is narrower: *the one buffer it could see was nearly
empty*. It never established that a game buffer existed at all. The peaks above are dmsynth
idling. The game created no buffer, because it had already abandoned audio setup when its
AudioPath refused to hand over a tool graph — see the banner at the top.

And nothing is decoded: a full run with `warn+msacm` and `warn+dmusic` shows **no ACM
activity at all** and no dmusic reports. The only component touching a DirectSound buffer is
dmsynth, rendering near-silence because it has nothing to play.

In hindsight this was the loudest clue in the whole investigation and it was read backwards.
The executable statically imports `MSACM32`, so a game that decodes nothing is a game that
never got as far as decoding — not a game whose decoder is broken.

## 4. Every hypothesis tested, and what killed it

| hypothesis | verdict | evidence |
| --- | --- | --- |
| missing or corrupt assets | dead | `demo.dat` (1.48 GB), `movie.dat` (305 MB) verify at both ends; Wine's file channel logs **zero** genuine open/read failures |
| slow storage | dead | 56.8 MB/s sequential; 50 scattered 1 MB reads in 1523 ms; no `dmesg` errors |
| missing ACM codecs | dead | present in the Wine install and the prefix; `Drivers32` maps them; the 503 "not found" lines are ordinary search-path probing |
| muted / misrouted hardware | dead | Master 100%, unmuted, `Playback Mux = SPK`; `speaker-test` tone audible, user-confirmed |
| PipeWire down | dead | healthy throughout; `wpctl` works even while `pactl` hangs |
| winealsa opening a busy device | dead | `plughw:1,0 busy` is enumeration noise; the game does get an active `PipeWire ALSA [box86]` stream on both channels |
| DirectSound failing to initialise | dead | `CreateSoundBuffer`, `Lock`, `PerformMix` all run; `pw-top` shows the node RUNNING at F32LE/48000 with sane timings |
| the 11 kHz resampler path | dead | `quality=0/1/2` (11/22/44 kHz), three runs, sink capture peak **0** in all three |
| Wine 11.0's shared `DirectSoundDevice` | dead | a counter on the reuse branch reports **0 reuses**; MGS2 calls `DirectSoundCreate` once |
| dmsynth starvation | dead | fixed 816 → 1, silence unchanged |
| missing COM registration | dead | all 12 classes registered with the 32-bit `regsvr32`, rc=0; silence unchanged |
| **native DirectMusic** | **hangs the game** | see §5 |

## 5. Native DirectMusic: installed correctly, and it hangs the game

Lutris installs `directmusic dsdmo quartz` for this title. winetricks **cannot run here** —
it probes with `$WINE cmd.exe /c echo '%AppData%'`, reads an empty string under box64 and
gives up, while the identical command by hand returns the right path a second earlier. So
all 14 files were extracted by hand from the cached redistributables:

* 11 from `dxnt.cab` inside `directx_feb2010_redist.exe`
* `quartz.dll` from the Win7 SP1 DirectShow core package
* `dmusic32.dll` from `directx_apr2006_redist.exe` (it is not in the Feb 2010 cab)

All are PE32 i386, all registered with `C:\windows\syswow64\regsvr32.exe` (the 64-bit one
cannot load a 32-bit DLL — that produced the "Failed to load DLL" seen early on).

Measured under a proper harness — one instance, a lock preventing any other test from
interfering, and 120 s to produce a real frame:

| profile | native set | renders? | audio |
| --- | --- | --- | --- |
| A | `quartz` only | **yes**, 100 frames in 11.1 s | peak 0 |
| B | `quartz` + the whole DirectMusic group | **no frames in 120 s**, process alive, one instance | peak 0 |

So native DirectMusic is unusable on this stack, and `quartz` is fine and stays enabled —
which is also what the port needs for movie playback.

This conclusion was first reached from runs that my own harness had killed, withdrawn as
unsound, and then re-established properly. It survived; my prediction that it would not was
wrong.

## 6. Where this points

MGS2 keeps music and voice in `bgm.dat` and `vox.dat`, fed by the same streaming machinery
that stalls during cutscenes. Silence and the cutscene freeze are plausibly **two faces of
one failure: the game's stream subsystem never delivers data.** That fits the file-channel
result — the reads are not failing, they appear never to be issued.

`FS_DISC_ERROR` is numerically `CDBIOS_STATE_COMMAND_ERROR` (`0x00010000`); `gamed.c` shows
the disc text after ~5 s of sustained error, and in the shipped source that status is set on
a read failure **or a read timeout**.

## 7. The harness lied four times, and how

Recorded because it is the main reason this session took so long, and because a reviewer
should discount any earlier claim that rests on these.

* **`pgrep -f <exe>` matches `gptokeyb`**, whose command line carries the executable name.
  A 120 s poll of "the game's" descriptors was actually watching gptokeyb, producing the
  false finding *"the game never opens a data file"*.
* **`pgrep -f <exe>` also matches the diagnostic shell itself**, because the pattern sits in
  its own arguments. That produced the false alarm *"five game instances are running"* —
  four were my own ssh shells.
* **Two test scripts running at once.** Each starts by killing stray game processes, so the
  second kills the first one's run. The log then reads `Killed` with zero frames, which is
  indistinguishable from a hang. This produced the premature *"native DirectMusic hangs the
  game"* — a verdict that happened to be right, reached by a method that could not
  establish it.
* **Liveness read as success.** A hung game stays in `ps`. Success now requires an actual
  frame report.
* Also: **`MGS2_TRACE=1` was left on by default**, costing real frame rate for hours until
  the user noticed; and **`_moviestart.exe` was promoted as the default executable** on an
  unverified theory and made cutscenes worse before being reverted.

The harness now has one helper (`mgslib.sh`): pid lookup by exact `comm`, a shared lock, and
frame-based success. Profile switching went from ~10 minutes to ~1 by replacing 27 separate
`wine` invocations with a single `regedit` import.

## 8. Where I am most likely still wrong

Listed for a reviewer to attack.

1. **"The game never opens `bgm.dat`/`vox.dat`" has still not been tested correctly.** The
   one attempt watched the wrong process. It has not been repeated during a cutscene, which
   is where streaming must occur. This is the most important untested claim in the document.
2. **The amplitude probe may be watching the wrong buffers.** It fires in
   `IDirectSoundBufferImpl_Unlock`. A game that writes with `DSBLOCK_ENTIREBUFFER` once, or
   fills a static buffer at creation, or uses a path that does not go through `Unlock`,
   would not be seen. The ~1 LSB reading may therefore be dmsynth's buffer only, and the
   game's own buffers may never appear at all — which would mean something quite different
   from "the app writes silence".
3. **All measurements were taken at the title screen or early menus**, roughly 60 s after
   launch. If the game only starts streaming later, everything here measures a period when
   silence is correct.
4. **In-game volume settings were never checked.** `MGS2SSET.ini` has `quality`, `se` and
   `tdSound` but no master volume; the in-game options menu has sliders that nobody has
   looked at.
5. **`MGS2_AUDIO=alsa` was assumed correct** because winepulse cannot load. But the ALSA
   path reaching PipeWire was confirmed only by the stream appearing, never by hearing game
   audio through it.
6. **The `dsound` amplitude build and the `dmsynth` 11.2 build were sometimes both active
   and sometimes not** across the session; not every measurement was taken with an identical
   binary set.

## 9. Current state of the device

Launcher defaults: `mgs2_sse_rg353vs_port.exe`, trace **off**, `MGS2_AUDIO=alsa`,
`PULSE_SERVER=tcp:127.0.0.1:4713`, `wined3d_dbg150_cxcaps.dll`, `win32u_glfuncs3.so`,
`opengl32_glesver1.so`, `dmsynth_wine112.dll`, stock ntdll, stock dsound, stock user32.

Prefix overrides (verified by `reg query`, not by reading a possibly stale `user.reg`):
`d3d9=native`, `dxgi=native`, `quartz=native`.

Available but off: `MGS2_TRACE=1`; `MGS2_DSOUND_DLL=dsound_share1.dll` with
`MGS2_DSOUND_PROBE=1` (the four probes); `MGS2_USER32_DLL=user32_peek1.dll` with
`MGS2_PEEK_HOT=401176 MGS2_PEEK_WAIT=1` — the busy-loop fix from brief #6, measured at
+11% fps and half the frame-time jitter, **still not promoted**.

Backups: `prefix-backup-preDM/` (registry and the 12 replaced DLLs), `native-dm/` (all 14
extracted native components, inert unless an override names them).

Tooling on the device: `mgslib.sh`, `dm_profile.sh` (profiles A–E), `dm_retest.sh`,
`dll_mode.sh`, `install_dm2.sh`, `ab.sh`, `run_perf_matrix.sh`.

## 10. The questions

1. What starts MGS2's vox/bgm stream, and what port-side condition would leave it idle from
   the first frame while the engine renders and takes input normally?
2. Is native DirectMusic known to be unusable under box86, and is there a subset that works?
3. Does MGS2 PC use DirectMusic for BGM at all, or is dmsynth activity incidental — in which
   case the whole DirectMusic line of attack is beside the point?
4. What is the right way to see which files a Wine process opens, on a device with no
   `strace` and no `/proc/PID/io`?

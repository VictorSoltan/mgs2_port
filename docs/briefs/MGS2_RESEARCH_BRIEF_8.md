# Research brief #8 — audio: everything measurable is healthy and the game still emits silence

Self-contained. Supersedes the audio parts of brief #7. Performance is brief #6; project
history is `MGS2_PROJECT_STATE.md`.

This brief exists because a long session produced a lot of verified negative results, two
genuine fixes, one unsolved problem, and several changes that need recording before they are
forgotten. It is written to be read by someone who has not seen the session.

---

## 1. Setup

Anbernic RG353VS — RK3566, four Cortex-A55, Mali-G52, **libmali / GLES 3.2 only**, 975 MB
RAM, RockNIX. box64 runs Wine 11.0 (old WoW64); the game is a 32-bit PE, so **the entire
32-bit stack — game, wined3d, opengl32, win32u, ntdll, dsound — is emulated by box86**. Wine
is not built by RockNIX; it unpacks Kron4ek's `wine-11.0-amd64` binaries. PipeWire 1.2.6.

Metal Gear Solid 2: Substance (PC, 2001, D3D8). Playable: menus, codec with portraits,
Tanker gameplay, rain, cutscene visuals, ~20–24 fps unpinned.

**The problem: the game produces no audio whatsoever.** Related and possibly the same
fault: in-engine cutscenes render for a few seconds, freeze, and the game shows *"There's a
problem with the disc you're using."*

## 2. Fixed this session

### 2a. The device's Pulse layer was broken system-wide

`pipewire-pulse` serves `/run/pulse/native` and `tcp:127.0.0.1:4713`, but clients follow
`XDG_RUNTIME_DIR` to a stale `/var/run/0-runtime-dir/pulse/native` and block there. `pactl`
hung; EmulationStation, which runs with `SDL_AUDIODRIVER=pulseaudio`, was silent.

`PULSE_SERVER=tcp:127.0.0.1:4713` makes `pactl info` answer instantly and gives
EmulationStation a live stream. Persisted in `/storage/.config/autostart/60-pulse-server-env.sh`
and `profile.d`, since `/etc` is read-only. The accompanying
`Failed to acquire org.pulseaudio.Server ... AccessDenied` D-Bus warning is a red herring;
no policy change was needed.

### 2b. dmsynth was starving

Wine 11.0 wakes the DirectMusic sink thread every ~10 ms (`BUFFER_SUBDIVISIONS 100`) to
query the play position and lock the buffer. This port cannot sustain that: **816
"Underrun detected" in one run**. The upstream Wine 11.2 series (7 commits over
`dlls/dmsynth/`, `BUFFER_SUBDIVISIONS` 100 → 10, fixed write latency, position query moved
to its own thread) was applied to the tree and built as a PE DLL. **Underruns fell to 1.**

It changed nothing audible — the fix is real, the symptom it addressed was not the cause.

## 3. Disproven, with the measurement that killed each one

| hypothesis | how it died |
| --- | --- |
| missing/corrupt assets | `demo.dat` (1.48 GB) and `movie.dat` verify at both ends; Wine's file channel logs **zero** genuine open or read failures |
| slow storage | 56.8 MB/s sequential, 50 scattered 1 MB reads in 1523 ms, no `dmesg` errors |
| missing ACM codecs | present in the Wine install and the prefix, `Drivers32` maps them; the 503 "not found" lines are ordinary search-path probing |
| muted or misrouted hardware | Master 100%, unmuted, `Playback Mux = SPK`; a `speaker-test` tone is **audible** |
| PipeWire down | healthy; `wpctl` works throughout |
| winealsa opening the wrong device | `plughw:1,0 busy` was enumeration noise, not the output path |
| DirectSound failing to initialise | `CreateSoundBuffer`, `Lock` and `PerformMix` all run; `pw-top` shows `alsa_playback.box86` RUNNING at F32LE/48000 |
| the resampler / 11 kHz path | `quality=0/1/2` (11/22/44 kHz), three runs, sink capture peak **0** in all three |
| Wine 11.0's shared `DirectSoundDevice` | a counter on the reuse branch reports **0 reuses** — MGS2 calls `DirectSoundCreate` once |
| dmsynth starvation | fixed (816 → 1 underruns), silence unchanged |
| native DirectMusic | installed and loaded (`dmusic.dll`, `dmime.dll` load as native) — the game then **hangs** during audio init, and before that produced no signal either |

### 3a. The measurement that matters most

Four amplitude probes were compiled into `dsound`, reporting peaks once a second as
multiples of 1e-5 of full scale:

| stage | what it measures | peak |
| --- | --- | --- |
| `unlock` | what the **application** wrote into a secondary buffer | 3 |
| `tmp` | after `cp_fields` — PCM → float and resampling | 4 |
| `vol` | after `DSOUND_MixerVol` — volume and 3D attenuation | 4 |
| `final` | the device buffer before `IAudioRenderClient_ReleaseBuffer` | 7 |

Stable across 23 reports. **Nothing is zeroed anywhere.** Signal enters at roughly one LSB
of a 16-bit sample (~-90 dBFS) and arrives intact. Independently, `pw-record` on the speaker
sink monitor gives **1 083 904 samples, peak 0, non-zero 0.00%**.

So Wine's audio stack is exonerated end to end: **the application submits silence and Wine
delivers it faithfully.**

### 3b. And nothing is being decoded

A full run with `warn+msacm` and `warn+dmusic` armed produces **no msacm activity at all**
and no dmusic reports. The only component touching a DirectSound buffer is dmsynth,
rendering near-silence because it has nothing to play.

## 4. Where this points

MGS2 keeps music and voice in `bgm.dat` and `vox.dat`, fed by the same streaming machinery
that stalls during cutscenes. Silence and the cutscene freeze are therefore most likely
**not cause and effect but two faces of one failure: the game's stream subsystem never
delivers data.** That fits the file-channel result exactly — the reads are not failing,
they are never issued.

`FS_DISC_ERROR` is numerically `CDBIOS_STATE_COMMAND_ERROR` (`0x00010000`), and `gamed.c`
shows the disc text after ~5 s of sustained error. In the shipped source that status is set
on a read failure **or a read timeout**.

## 5. The questions

### 5.1 What starts MGS2's vox/bgm stream, and what would leave it idle from frame one?

Is there a port-side condition — a missing index or table, a "disc" path the engine expects,
a stage descriptor — that makes `FS_StreamGetData` return nothing while never attempting a
read? The engine renders, accepts input and runs its main loop 56 000 times a second, so it
is not stuck; it simply never asks for audio.

### 5.2 Why does native DirectMusic hang this stack?

`directmusic dsdmo quartz` is the documented set for this game (Lutris installs exactly
these). Installed manually — winetricks cannot run here, see §6 — `quartz` alone is fine and
the game starts and renders. Adding the DirectMusic set makes the game hang during audio
init: the load log ends right after native `dmusic.dll` and `dmime.dll`, no error, process
alive. A per-DLL bisection is running. Is native DirectMusic known to be unusable under
box86, and is there a known-good subset?

### 5.3 Is the cutscene stall really the same fault?

Unproven. The clean experiment is a cutscene with working audio versus `MGS2_AUDIO=none`,
but it cannot run until there is working audio.

### 5.4 box86 and winepulse

`winepulse.so` cannot load: `Symbol pthread_mutexattr_setrobust not found, cannot apply
R_386_JMP_SLOT`. A 32-bit ELF exporting the symbol via `BOX86_LD_PRELOAD` does **not**
satisfy the relocation — box86 resolves against its own wrapped libc. The fix is
`GO(pthread_mutexattr_setrobust, iFpi)` in `src/wrapped/wrappedlibpthread_private.h` plus a
rebuild. Given the ALSA path works and the Pulse layer is now reachable, is reviving
winepulse worth it at all?

## 6. Tooling traps specific to this device

* **`pactl` hangs** — its output is worthless here. Use `wpctl`, `pw-top`, `pw-record`.
* **winetricks cannot run.** It probes with `$WINE cmd.exe /c echo '%AppData%'` and reads an
  empty string under box64, then gives up — while the identical command by hand returns the
  right path a second earlier. Components must be extracted from the cached redistributables
  by hand (`install_dm2.sh`).
* **`wineboot` starts Wine's Mono installer**, which pins a core at 89% and blocks
  everything. Always set `WINEDLLOVERRIDES="mscoree=;mshtml="`.
* **The 64-bit `regsvr32` cannot register 32-bit DLLs** in a win64 prefix — that is the
  "Failed to load DLL" seen when registering. Use `C:\windows\syswow64\regsvr32.exe`.
* **Liveness is not success.** A hung game stays in `ps`; a launch only counts if it reaches
  a rendered frame.
* **Comparing DLL sizes while the game runs is unreliable** — the launcher bind-mounts
  variants over the Wine install, so "builtin" changes under you.

## 7. Mistakes made this session, recorded so they are not repeated

* **`MGS2_TRACE=1` was left on by default** to catch the cutscene fault during normal play.
  It enables a dozen Wine debug channels writing to the SD card and cost real frame rate;
  the user noticed before I did. Now off by default; 60 fps in menus confirmed restored.
* **`_moviestart.exe` was promoted as the default executable** on the theory that restoring
  the movie-start byte would clear the disc error. It made cutscenes worse and was reverted.
* **Three wrong audio conclusions were published and withdrawn**: that DirectSound
  initialisation was broken (it is not), that winealsa was opening the wrong device (it was
  not), and that the game created no playback stream (it does — that reading came from the
  hung `pactl`).
* **The whole native component set was installed at once**, so when the game hung there was
  no way to tell which DLL did it without a bisection.
* **`pkill -f` matched the invoking ssh command line twice more**, once because the pattern
  was literally in the command's own arguments.

## 8. Current configuration

Launcher defaults: `port.exe`, trace off, `MGS2_AUDIO=alsa`,
`PULSE_SERVER=tcp:127.0.0.1:4713`, `wined3d_dbg150_cxcaps.dll`, `win32u_glfuncs3.so`,
`opengl32_glesver1.so`, `dmsynth_wine112.dll`, stock ntdll, stock dsound, stock user32.

Prefix overrides: `d3d9=native`, `dxgi=native`, `quartz=native`.

Available but off by default: `MGS2_TRACE=1`, `MGS2_DSOUND_DLL=dsound_share1.dll` with
`MGS2_DSOUND_PROBE=1` (the four amplitude probes), `MGS2_USER32_DLL=user32_peek1.dll` with
`MGS2_PEEK_HOT=401176 MGS2_PEEK_WAIT=1` (the busy-loop fix from brief #6, measured at +11%
fps and half the frame-time jitter, not yet promoted).

Backups: `prefix-backup-preDM/` holds the registry and the twelve DLLs replaced;
`native-dm/` holds the extracted native components, inert until an override names them.

# Research brief #7 — no audio anywhere, and a cutscene stall that pretends to be a disc error

Self-contained. Project history: `MGS2_PROJECT_STATE.md`; performance is brief #6.

Two symptoms are under investigation together because they may share a cause:

1. **The device has no sound at all** — not in the game, not in the EmulationStation menu.
2. **In-engine cutscenes start, render a few seconds, then freeze**, and the game puts up
   *"There's a problem with the disc you're using. It may be dirty or damaged."* The same
   message also appears when entering the second location.

The hypothesis worth testing is that (2) is caused by (1): a demo stream carrying voice
that waits on an audio device which never accepts data would stall exactly this way.

---

## 1. Setup

Anbernic RG353VS — Rockchip RK3566, four Cortex-A55, Mali-G52, **libmali, GLES 3.2 only**,
975 MB RAM, RockNIX. box64 runs Wine 11.0 (old WoW64); the game is a 32-bit PE, so Wine
re-execs its 32-bit self and **the whole 32-bit stack runs emulated under box86**. Wine is
not built by RockNIX — it unpacks Kron4ek's `wine-11.0-amd64` binaries. box86 v0.3.9,
box64 v0.4.2, PipeWire 1.2.6, WirePlumber 1.2.6.

Metal Gear Solid 2: Substance (PC, 2001, Direct3D 8) is otherwise playable: menus, codec
with portraits, Tanker gameplay, rain, ~22 fps.

## 2. What is measured — audio

### 2a. The hardware and the ALSA→PipeWire route both work

```
speaker-test -c2 -t sine -f 440 -l1 -D default    → played, audibly confirmed by the user
amixer -c 1: Master 100%, not muted, Playback Mux = SPK
wpctl status: sink 51 "Built-in Audio Internal Speaker" is default, vol 1.00
```

The 32-bit bridge is present too: `/usr/lib32/alsa-lib/libasound_module_pcm_pipewire.so`,
plus `/etc/alsa/conf.d/50-pipewire.conf` and `99-pipewire-default.conf`. So a 32-bit ALSA
client asking for `default` reaches the speaker.

### 2b. PipeWire is healthy; nothing is playing

`wpctl status` responds normally and lists devices, sinks and sources — but **`Streams:` is
empty**. Nothing in the system has an active playback stream.

Note on tooling: `pactl` **hangs** on this device and its output must not be trusted. An
earlier conclusion here ("the game creates no playback stream") was drawn from `pactl` and
was only later confirmed with `wpctl`, which does work.

### 2c. Why the whole system is silent: pipewire-pulse cannot own its D-Bus name

```
pipewire-pulse[5669]: mod.protocol-pulse: Failed to acquire org.pulseaudio.Server:
  org.freedesktop.DBus.Error.AccessDenied: Connection ":1.27" is not allowed to own
  the service "org.pulseaudio.Server" due to security policies in the configuration file
```

Reproduced across restarts of `pipewire.service`, `pipewire-pulse.service` and
`wireplumber.service`. No file under `/etc/dbus-1/` or `/usr/share/dbus-1/` mentions
`org.pulseaudio.Server` at all, so the name is refused by the default policy rather than by
an explicit rule.

EmulationStation runs with `SDL_AUDIODRIVER=pulseaudio`, i.e. through exactly this broken
layer — which explains menu silence. The native PipeWire protocol is unaffected.

### 2d. Why the game is silent: both Wine backends are blocked, for different reasons

**winepulse cannot even load under box86:**

```
Error: Symbol pthread_mutexattr_setrobust not found, cannot apply R_386_JMP_SLOT
       0x65faa040 (0x1736) in /usr/lib/wine/i386-unix/winepulse.so
Error: relocating Plt symbols in elf winepulse.so
```

box86's wrapped 32-bit libc does not export `pthread_mutexattr_setrobust`, so the PLT
relocation fails and the driver never initialises. This is why the launcher carried
`winepulse.drv=d` — the disable was a symptom, not a choice.

**winealsa loads but hits a busy device:**

```
warn:alsa:alsa_try_open The device "plughw:1,0" failed to open: -16 (Device or resource busy)
```

PipeWire holds the card (`/proc/asound` shows card 1 with 0/1 free subdevices). The `default`
device — the one that routes through the PipeWire plugin and demonstrably works — is not
what Wine ends up using for output.

The game process does hold PipeWire descriptors (`memfd:pipewire-memfd` ×6), so a client
connection is established; but no stream is ever created.

## 3. What is measured — the cutscene stall

### 3a. The message means a failed read, and is shown after five seconds

`FS_GetDiscStatus()` returns `cdbios_get_status()`, and `FS_DISC_ERROR` is numerically the
same bit as `CDBIOS_STATE_COMMAND_ERROR` (`0x00010000`). `gamed.c` counts sustained error
and, past `DISC_ERROR_SHOW_COUNT` (~5 s), prints the text and pauses the actor system. In
the shipped source, that status is set both on a read failure **and on a read timeout**.

### 3b. But no file operation actually fails

A full run with Wine's file channel (`warn+file,err+file`) captured **zero genuine
failures**. The 503 ACM-related "not found" lines are ordinary search-path probing — the
codecs exist in `/usr/lib/wine/i386-windows/` and in the prefix, and `Drivers32` maps them
correctly. `wineoss.drv` / `winecoreaudio.drv` misses are expected on Linux.

### 3c. And storage is fast

```
demo.dat (1.48 GB) sequential, caches dropped:  56.8 MB/s
50 scattered 1 MB reads:                        1523 ms
```

`movie.dat` (305 MB) and `demo.dat` both verify at first and last megabyte. No ext4 or mmc
errors in `dmesg`. `/storage` has 1.4 GB free.

### 3d. The cutscene renders before it stalls

Screenshot at the moment of failure shows the Verrazano Bridge scene drawn correctly with
the error text overlaid — so initial data arrived and the renderer is fine. The game is at
224% CPU, not blocked; no thread is in uninterruptible I/O.

## 3b. Update after acting on the first round of advice

Three of the four suspected faults turned out to be real and two are now fixed. The
silence is not.

**Fixed — the Pulse endpoint.** `PULSE_SERVER=tcp:127.0.0.1:4713` makes `pactl info`
answer instantly. RockNIX's pipewire-pulse serves `/run/pulse/native` and that TCP port,
while clients follow `XDG_RUNTIME_DIR` to a stale
`/var/run/0-runtime-dir/pulse/native` and block there. The D-Bus name failure was a red
herring, exactly as suggested; no policy change was needed. EmulationStation now has an
active stream. Persisted via `/storage/.config/autostart/60-pulse-server-env.sh` and
`profile.d`, since `/etc` is read-only.

**Fixed — dmsynth starvation.** The Wine 11.2 series (7 commits, `wine-11.0..wine-11.2`
over `dlls/dmsynth/`, including `BUFFER_SUBDIVISIONS` 100 → 10) was applied to the tree and
built as a PE DLL. Underruns in a comparable run fell from **816 to 1**.

**Not fixed by a shim — the box86 symbol.** A 32-bit ELF exporting
`pthread_mutexattr_setrobust`, loaded through `BOX86_LD_PRELOAD`, did **not** satisfy the
relocation; the error is unchanged. box86 resolves `winepulse.so`'s imports against its own
wrapped native libraries, so only the wrapper-table entry plus a rebuild will do.

**Corrected — two of my own conclusions.** DirectSound initialisation is *not* broken: the
trace shows `DirectSoundDevice_CreateSoundBuffer`, `IDirectSoundBufferImpl_Lock` and
`DSOUND_PerformMix` all running, and `pw-top` shows `alsa_playback.box86` RUNNING at
F32LE/48000 with sane timings. And `plughw:1,0 busy` was indeed only enumeration noise.

**The remaining fact.** Recording the speaker sink monitor with `pw-record` while the game
runs gives **1 083 904 samples, peak 0, non-zero 0.0%**. The stream is live, routed and
unmuted, and it carries pure silence. A `speaker-test` tone through the same sink is
audible, so everything downstream works.

The game's own `MGS2SSET.ini` `[SOUND]` section reads `quality=0`, `se=3`, `tdSound=0`,
`driver=Primary Sound Driver`. `tdSound` is 3D sound (cf. `DVERR_NO3DSOUND` in the
executable), not a mute; nothing there is obviously silencing output.

## 3c. Second update: Wine's audio stack is exonerated, and the two symptoms merge

Acting on the second round of advice settled the audio question, though not in the
direction any of us expected.

**Sound quality is not it.** `quality=0/1/2` (11 / 22 / 44 kHz) with `se=9`, three runs,
sink monitor captured each time: peak **0** in all three. The resampler path is not the
cause.

**Shared DirectSoundDevice is not it.** A counter placed on Wine 11.0's device-reuse branch
reports **zero reuses** in an MGS2 run. The game calls `DirectSoundCreate` once; the
upstream May-2026 split would change nothing here. (`Primary Buffer already created` does
appear twice, but within the one device.)

**The four amplitude probes settle it.** Peaks, as multiples of 1e-5 of full scale,
sampled once a second and stable across 23 reports:

```
unlock=3   tmp=4   vol=4   final=7
```

Signal is present at every stage and is never zeroed: what the application writes arrives
at the device intact. But it is around one LSB of a 16-bit sample, roughly -90 dBFS —
inaudible. **The application is writing silence, and Wine is faithfully delivering it.**
That is the first row of the interpretation table, and it clears dsound, mmdevapi,
winealsa, the mixer, volume and 3D attenuation all at once.

**No decoding is happening either.** With `warn+msacm` and `warn+dmusic` armed, a full run
produces **no msacm activity at all** and no dmusic reports. The only thing touching a
DirectSound buffer is dmsynth, rendering near-silence because it has nothing to play.

### What this changes

MGS2 keeps music and voice in `bgm.dat` and `vox.dat`, fed by the same streaming machinery
that stalls during cutscenes. So silence and the cutscene freeze are most likely **not
cause and effect but two faces of one failure**: the game's stream subsystem is not
delivering data. That also fits the earlier findings that no file operation fails and the
storage is fast — the reads are never issued, rather than issued and failing.

The investigation should move from the audio stack to `FS_StreamGetData` and the demo/vox
stream feed.

## 4. The questions

### 4.0 Why does the game's stream subsystem deliver nothing?

Answered by §3c: not a Wine fault. The open question is now on the game side. MGS2 never
submits audio data and never invokes an ACM decoder, while the same streaming path stalls
during cutscenes. What starts the vox/bgm stream in this engine, what would leave it idle
from the very first frame, and is there a known port-side condition (a missing index file,
an unmounted "disc" path, a stage table) that makes `FS_StreamGetData` return nothing
without ever attempting a read?

### 4.1 The box86 missing symbol — is there prior art?

`pthread_mutexattr_setrobust` is absent from box86's wrapped libc symbol list, which stops
`winepulse.so` dead. This looks like a routine gap of the kind box86 fixes by adding the
symbol to its wrapper tables. Is there an upstream commit or a known patch? Is rebuilding
box86 at RockNIX's commit (`0579f8b9`) with the symbol added the accepted fix, or is there a
supported way to satisfy the relocation without rebuilding — a preloaded 32-bit stub via
`BOX86_LD_LIBRARY_PATH`, for instance?

Related: given that this device's pulse layer is broken anyway (§2c), is reviving winepulse
even worth it, or is ALSA the right target?

### 4.2 How do other Wine-on-box86 handheld ports get audio out under PipeWire?

This is the question with the best track record in this project — porting CrossOver
Android's GLES capability list produced the single largest improvement so far. Concretely:

* What do PortMaster / RockNIX Wine ports normally set so that `winealsa` uses `default`
  (the PipeWire plugin) rather than enumerating and opening raw `plughw:N,M`?
* Is there a standard `.asoundrc` / `ALSA_CONFIG_PATH` shape for a Wine prefix on a
  PipeWire system where the card is already claimed?
* Does Wine have a registry setting to pin winealsa's output device to `default`?

### 4.3 The D-Bus policy for pipewire-pulse

`org.pulseaudio.Server` is refused because no policy grants it. Is adding a
`/etc/dbus-1/system.d/` rule the correct fix on RockNIX, or is pipewire-pulse meant to run
as a user service on a session bus here and the system-bus attempt is itself the mistake?
Fixing this would restore menu sound and give Wine a working pulse target.

### 4.4 Is the cutscene stall actually audio-dependent?

Unproven either way. Facts: no file operation fails, storage is fast, the scene renders,
the game keeps running. The remaining candidates are an audio device that never accepts
data, or an internal timeout in the game's streaming state machine that the emulated CPU
misses. What is the known behaviour of MGS2 PC's demo stream when the sound device is
absent — does it block, or degrade to silence?

## 5. Ruled out — please do not re-investigate

* **A missing, corrupt or unreadable asset.** `demo.dat` and `movie.dat` verify; the file
  channel records no failed open or read; storage is fast and error-free.
* **Missing ACM codecs.** They exist in the Wine install and the prefix, and `Drivers32`
  registers them. The "not found" lines are search-path noise.
* **Muted or misrouted hardware.** Master 100%, unmuted, output on SPK; a test tone was
  heard.
* **PipeWire being down.** It is up and healthy; only the pulse protocol layer is broken.
* **The restored movie-start byte being the cure.** `_moviestart.exe` (byte `0x14210`
  `0xC3`→`0x68`) was tried as the default and made cutscenes *worse*, so it was reverted.

## 6. Reproducing

`MGS2_TRACE=1` (currently the launcher default) captures the game's output to
`MGS2-Substance/trace.log`, capped at 200 MB by a watchdog, with the audio channels armed:
`err+dsound,warn+dsound,err+winmm,warn+winmm,err+mmdevapi,warn+mmdevapi,err+alsa,warn+alsa,
err+dmsynth,warn+dmsynth`. `MGS2_AUDIO=pulse|alsa|none` selects the backend;
`alsa` is the default because pulse cannot load.

The automated harness is useless for this fault: it presses confirm repeatedly to reach
gameplay, which **skips the cutscenes**. Reproduction has to be done by hand.

Evidence bundle: `recovered-session/audio-logs/audio-evidence.txt` and `trace.log`.

# Research brief #10 — performance after audio: the profile has changed shape

Self-contained. Supersedes brief #6's profile, which was taken before two things that alter
it fundamentally: the busy-loop fix, and audio actually working. Audio history is brief #9;
project record is `MGS2_PROJECT_STATE.md`.

The game is now playable with sound at 22–23 fps, and the user's report is *"not awful, but
not comfortable either"*. This brief is about where the remaining time goes.

---

## 1. Setup

Anbernic RG353VS — RK3566, four Cortex-A55, Mali-G52, **libmali / GLES 3.2 only**, 975 MB
RAM, RockNIX. box64 runs Wine 11.0 in old-WoW64 mode; the game is a 32-bit PE, so **the
whole 32-bit stack is emulated by box86**. Only libmali, PipeWire and the kernel are native.
Wine is Kron4ek's `wine-11.0-amd64` binary build, not built by RockNIX.

Shipping configuration as measured: `mgs2_sse_rg353vs_port.exe`, `wined3d_dbg150_cxcaps.dll`,
`win32u_glfuncs3.so`, `opengl32_glesver1.so`, `winewayland_pbo1.so`, `dmsynth_wine112.dll`,
**`dmime_graphqi.dll`** (the audio fix), **`user32_peek1.dll`** with
`MGS2_PEEK_HOT=401176 MGS2_PEEK_WAIT=1` (the busy-loop fix), `quartz=native`,
`PULSE_SERVER=tcp:127.0.0.1:4713`, tracing off.

## 2. Startup is clean

A full run with `err+all,fixme+all` (minus the d3d channel, which our debug wined3d floods)
shows **no genuine errors**. Everything in `err` is benign: d3dcompiler disassembly
warnings, the compositor's missing `xdg_toplevel_icon_manager_v1`, `winediag` announcing the
OpenGL renderer, and our own frame counter.

The `fixme` list is entirely DirectMusic running on stubs:

```
28  dmime:IDirectMusicAudioPathImpl_Activate: semi-stub
14  dmusic:synth_port_SetDirectSound: semi-stub
14  dmime:performance_tool_ProcessPMsg  Unhandled message type 0x4
13  dmime:IDirectMusicAudioPathImpl_SetVolume: stub
13  dmime:GetObjectInPath ... IID_IDirectMusicPort: stub
```

Audio works anyway. Two of these are worth remembering: `SetVolume` being a stub means the
game cannot control its own output level, and `Unhandled message type 0x4` may be dropping
music events.

## 3. The new profile

`perf record -F 199 -g` over 25 s of live gameplay at 22.5–22.8 fps, 980 samples.

### By thread

| thread | share | note |
| --- | --- | --- |
| game main | 53% | |
| `wined3d_cs` | 23% | |
| **`wine_dmsynth_si`** | **9.3%** | new — DirectMusic synth |
| **`audio_client_ti`** | **6.3%** | new |
| **`wine_dsound_mix`** | **4.3%** | new |
| `mali-cmar-backe` | 3.6% | |

**Audio now costs about 20% of all CPU time.** Before the dmime fix it cost nothing, because
the game never built its audio path. That is the single biggest change since brief #6, and
it is the most likely explanation for gameplay feeling heavier than it did while silent.

### By shared object (leaf)

| | share |
| --- | --- |
| kernel | 47% |
| box86 JIT-translated code | 31% |
| libmali | 7.3% |
| box86 runtime | 7.2% |
| libc | 5.2% |

### Syscalls

| syscall | samples | who |
| --- | --- | --- |
| **`ioctl`** | **173** | dmsynth 81, game 60, dsound_mix 20, wined3d_cs 5, audio_client 5 |
| `poll` | 43 | game 22, mali-cmar 21 |
| `getrusage` | 43 | game 42 |
| `futex` | 37+5 | game 27, wined3d_cs 15 |
| `sched_yield` | 31 | game 25, audio_client 6 |
| `pselect6` | 23 | |
| `clock_gettime` | 19 | |

`__schedule` appears in **305 of 979 stacks (31%)**.

Of the audio threads' 142 sampled syscall entries, **106 are `ioctl`** — ALSA calls going
through the PipeWire plugin.

## 4. What the numbers suggest, in order of size

### 4a. Audio ioctl traffic — the largest new cost

dmsynth alone accounts for 81 `ioctl` samples. The Wine 11.2 dmsynth series already cut the
notification count from 100 per buffer to 10, and that removed the underruns (816 → 1), but
the remaining wake-up rate still dominates the syscall profile.

PipeWire is running the game's node at **quantum 480 @ 48 kHz — a 10 ms period**. Every
period costs a wake-up and ioctls in three separate threads. Raising the quantum should
reduce all of it proportionally and is a configuration change, not a code change.

Questions: what is the right way to give one Wine client a larger ALSA/PipeWire period on
this stack — `PIPEWIRE_QUANTUM`, `node.latency` via a rule, or Wine's own ALSA period
settings? What latency is acceptable before the game's audio sync visibly drifts, given
`SetVolume` and the message pump are already stubs?

### 4b. `NtYieldExecution` is still there, just smaller

`getrusage` 43 + `sched_yield` 31 ≈ **7.6% of samples, all from the game's main thread**.
The busy-loop fix intercepts one call site (`0x401176`, the empty-`PeekMessage` path) and
deliberately no other, so the remaining yields come from elsewhere — the second win32u yield
site, `NtDelayExecution`, or the game's own `SwitchToThread`.

Each of those yields is still three syscalls, two of which exist only to report
`STATUS_NO_YIELD_PERFORMED` (one consumer tree-wide). Brief #6 measured a global "cheap
yield" variant and got contradictory results — but that was on the old, unreliable harness,
before the pid lookup and the test lock were fixed. **It deserves a clean re-run.**

### 4c. `wined3d_cs` at 23%, GPU at 7.3%

Unchanged in shape from brief #6: the command-stream thread costs three times what the
actual GPU driver does, and both sides of the queue are emulated. `WINE_D3D_CONFIG=csmt=0`
has never been A/B'd properly — it was queued behind the audio work and then the harness
turned out to be untrustworthy. It is a free test.

### 4d. The emulation floor

31% in translated code plus 7.2% in the box86 runtime is the cost of running a 32-bit x86
game through a dynarec on an A55. `BOX86_DYNAREC_SAFEFLAGS=0 BIGBLOCK=2 FORWARD=512
CALLRET=1` are already set. Untried: `BOX86_DYNAREC_WAIT=0`, a `FORWARD` sweep, and building
box86 with `-mcpu=cortex-a55`.

The structural escape is Wine's new WoW64 under box64, which would remove the 32-bit
emulated Unix layer and the compat syscall path entirely. The prerequisite is confirmed
present: `/usr/lib/libmali.so.1.10.0` is ELF64 AArch64.

## 5. Ruled out — do not re-investigate

* **The GPU.** libmali is 7.3%; in brief #6, removing every draw call did not change the
  frame rate at all.
* **Storage.** 56.8 MB/s sequential; no I/O errors.
* **Thermal throttling as a primary cause.** It is real (1416 MHz sustained against a
  1608 MHz ladder top) but secondary; the frame rate is CPU-bound well below the cap.

## 6. Method notes for whoever runs the next measurement

The harness on the device (`recovered-session/scripts/mgslib.sh`) now provides the only
correct way to find the game process — exact `comm` match, never `pgrep -f`, which matches
both `gptokeyb` and the diagnostic shell itself — plus a lock that stops two tests running
at once, and success defined as a rendered frame rather than an elapsed sleep. Four
conclusions in the previous session were wrong because of those three traps.

Also: `pactl` hangs on this device; use `wpctl`, `pw-top`, `pw-record`. And
`MGS2_TRACE=1` costs real frame rate — never leave it on for a measurement of speed.

## 7. Suggested order

1. Raise the audio period / PipeWire quantum — largest single item, configuration only.
2. Re-run the cheap-yield A/B on the fixed harness.
3. `csmt=0` A/B.
4. Re-profile, then decide whether box86 tuning is worth it.
5. new WoW64 as a separate, expensive branch.

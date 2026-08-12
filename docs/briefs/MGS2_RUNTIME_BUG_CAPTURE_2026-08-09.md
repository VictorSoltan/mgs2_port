# MGS2 RG353VS — capture: gameplay SFX vanish and battle stalls

Captured 9 August 2026 from one live, user-driven session.  This is evidence for
two defects, not a claim that they already share a cause.

## User-visible sequence

1. The user opened the map with Start and returned to gameplay.  Gameplay SFX
   were absent afterwards.
2. In a battle shortly afterwards, gameplay SFX were again absent and the game
   became severely slow.

The live process was a single instance (`launch.sh` PID 4658, game PID 4774),
so this was not the known duplicate-launch failure.

## Snapshot while both symptoms were present

* CPU: 1992000 / 1992000 kHz; thermal zones 79.375 C and 72.222 C.  Thermal
  throttling is ruled out for this occurrence.
* The game main process consumed about 140% CPU.  `wined3d_cs` was waiting in
  `__futex_wait`; this is not the usual "the GPU is busy" signature.
* The PipeWire stream `mgs2-audio` (node 72) remained `running`, at 44.1 kHz,
  with its two output ports allocated.  Wine's `alsa-pipewire`, `wine_dsound_mix`
  and both `wine_dmsynth_si` threads were waiting, not faulted.
* Therefore the SFX disappearance is not a lost speaker, missing PipeWire node,
  duplicate game process, or CPU thermal cap.  It remains an SE / game-audio
  pipeline defect.  No conclusion is drawn here about its exact internal
  boundary because a hot audio trace would invalidate the frame-time capture.

## Renderer evidence from the same process

The production binary emits `MGS2BATCH` / `MGS2CACHE` lines to stderr even with
`WINEDEBUG=-all`.  That is itself a production defect: the wrapper's normal
stdout/stderr capture kept receiving per-second renderer telemetry.

Immediately before the heavy scene, the cache was stable at 40 entries / 11 KB
with `probes=0`.  It then progressed:

```text
entries / bytes / probes per second
  65 /   29 KB /   1,300
 162 /   67 KB /   4,515
 374 /  235 KB /  36,081
 741 /  928 KB /  80,417
 917 / 1124 KB / 147,113
1343 / 1422 KB /  80,987
```

During that interval the batch output contains several `fps=0.00` windows and
then low windows (0.96, 3.64, 6.17, 7.01 fps).  `evict=0` throughout.  This
correlates with the user's battle slowdown and the 140% main-thread CPU
snapshot.  It does **not** by itself prove the cache is the cause; the next
test must compare this exact heavy scene with batching disabled or a bounded
cache, while preserving the audio capture independently.

## Preserved artefacts

* `logs/live-20260809/mgs2-normal-launch.log` — the production-session stderr,
  including the cache-growth window.
* `logs/live-20260809/mgs2-sfx-map.log` — aborted audio trace.  It contains
  startup/instrument-download noise and is not evidence for the battle.
* `logs/live-20260809/mgs2-sfx-map-launch.log` and
  `logs/live-20260809/mgs2-sinkprobe-launch.log` — launcher output from the
  two controlled restarts.

## Follow-up, without distorting play

1. Remove unconditional `MGS2BATCH` / `MGS2CACHE` stderr output from the
   production binary, retaining an explicit bounded diagnostic switch.
2. Make the cache bounded/evicting in the production batcher, then reproduce
   the same battle with fixed CPU clock and verify that the growth/probe spike
   cannot recur.
3. Use the pre-existing `MGS2_SINKPROBE=1` in-memory marker around one action
   after the map transition.  Read its fixed-size record externally; do not
   enable `MGS2_TRACE`, `err+dmsynth`, mixer census, or a per-render logger.

## Implementation, 9 August 2026

The fixes are in the recovered Wine 11.0 source and are exported as
`wine-patches/12-current-runtime.patch`, after patches 1–11.

* `dmusic/instrument.c` now owns a DLS download and its waves per
  `IDirectMusicPortDownload`, with a reference count.  Releasing one logical
  AudioPath no longer unloads the shared physical port while another path uses
  it.
* `dmusic/port.c` revives an inactive synth immediately before a MIDI buffer
  only when `MGS2_DMIME_SHAREDGROUPS=1`.  This targets the map/AudioPath
  transition without changing normal multi-port behaviour.
* `dmsynth/synth.c` restores FluidSynth's active-voice refresh after rendering
  and raises the default voice ceiling to 48.  The production wrapper also uses
  `MGS2_DMSYNTH_IDLE_SKIP=0` as the conservative temporary runtime setting.
* `wined3d/context_gl.c` replaces the unbounded cold-miss scan with a fixed
  1024-set × 4-way cache.  A lookup now examines at most four entries, and
  `MGS2BATCH` / `MGS2CACHE` telemetry is off unless `MGS2_BATCH_STATS=1`.
* `d3d8/buffer.c` retains up to eight ordered dirty ranges, coalescing overlap
  or gaps of at most 256 bytes and merging the nearest pair only when full.
  It no longer uploads one inflated min..max range.

`dmusic.dll`, `dmsynth.dll`, `wined3d.dll`, and `d3d8.dll` compile successfully
with the recovered i386 build.  A fresh Wine 11.0 extraction with patches 1–12
was compared to the working source with `diff -qr` and had no source
differences.  The audio files are in `binaries/` and checksummed in
`binaries/SHA256SUMS`; all four staged variants are also in
`../recovered-session/device-artifacts/` under the names selected by
`device/MGS2-Substance.sh`.

## Deployment smoke test, RG353VS

After the console rebooted, the four variants were copied beside the old DLLs
and the top-level launcher was backed up on the device as
`MGS2-Substance.sh.pre-runtime-20260809-1553`.  The files loaded byte-for-byte
at Wine's mount targets.  The test process had these relevant settings:

```text
MGS2_DMUSIC_DLL=dmusic_shared_lifetime1.dll
MGS2_DMSYNTH_DLL=dmsynth_se2_lifetime.dll
MGS2_DMSYNTH_POLYPHONY=48
MGS2_DMSYNTH_IDLE_SKIP=0
MGS2_WINED3D_DLL=wined3d_batch16_setcache.dll
MGS2_D3D8_DLL=d3d8_producer_batch14_dirtyranges.dll
MGS2_BATCH=1
MGS2_BATCH_STATS=0
WINEDEBUG=-all
BOX86_LOG=0
```

MGS2 reached a live process with normal CPU activity and remained running.  The
new launch log contains zero `MGS2BATCH` or `MGS2CACHE` lines; it is preserved
as `logs/live-20260809/mgs2-runtime-smoke-20260809.log`.  This verifies loading
and the no-telemetry invariant, not the audible map transition or a battle. The
next user-driven map-and-battle pass remains the behavioural verification.

## First gameplay observation after deployment

During the live battle pass, enemy shots remained audible but the player's own
hit sound later stopped.  That rules out a complete loss of the audio device or
the final output sink, but still leaves a failing gameplay-SFX path (instrument,
AudioPath, or voice allocation/lifetime) to isolate.

The production stderr log for this run is fixed at 1,964 startup lines and has
no `dmusic`, `dmsynth`, or runtime audio diagnostics because `WINEDEBUG=-all` is
intentional.  It also has zero batch/cache telemetry.  Consequently it cannot
identify the exact failed player-hit note, and no conclusion about the specific
remaining audio path is drawn from it.  The next controlled run must start with
the memory-only `MGS2_SINKPROBE=1` marker, then read its fixed-size state after
the user reproduces the missing sound; do not turn on hot audio tracing during
play.

## Live log check, SE recorder launch

The subsequent `mgs2_sse_rg353vs_sevoice7.exe` launch was inspected while the
user reported that sound appeared normal.  At the check it had been alive for
6:24, used about 182% CPU, and the SoC temperature was 78.125 C.  The thermal
guard and input-helper logs were empty; the kernel reported no OOM, fault, or
runtime GPU event.

Its launcher log was still exactly the 1,964 startup lines (144,473 bytes),
with no `dmusic`, `dmsynth`, `dsound`, underrun, renderer-cache, or error
entries.  The only matches were the known XKB XML/DTD validation warnings and
Box86's startup EGL-wrapper messages.  This is a negative result: it shows no
runtime failure but cannot diagnose an intermittent SFX loss because production
logging is intentionally disabled.

## Apparent-freeze snapshot after console restart

On the next normal production launch, the user reported that the picture appeared
frozen.  The process was still live (PID 4970, about 109% CPU, 334 MB RSS) and
the SoC was cool at 62.777 C.  There were no thermal-guard, OOM, GPU, or kernel
fault records.

A single two-second thread snapshot showed the same pattern both times: the
primary game thread and `wined3d_cs` were waiting in `futex_wait`, while game
thread 5722 consumed about 94% of one core with no kernel wait channel.  The
DirectSound mixer remained schedulable and the audio threads were in their
normal waits.  This is evidence of a live user-space spin/wait stall rather
than a crash, disk wait, GPU fault, or thermal event.  It is not yet a call-site
attribution; do not add a continuous thread sampler while the user is playing.

## Reproduction after the stock-user32 input A/B

The input A/B removed only `user32_peek1.dll`; all current production audio and
renderer modules were verified byte-for-byte at their Wine mount targets.  In
that one-instance run, the user opened the in-game map with Start and then
reported that gameplay SFX disappeared.  This is a specific, user-driven
reproduction of the map transition and also proves that the input `PeekMessage`
variant is not the cause of the audio defect.

At capture time PipeWire, the DirectSound mixer, both dmsynth threads, and the
dmime message thread were live; the kernel contained no audio, OOM, thermal, or
GPU fault.  This excludes a total output-backend failure.  It does **not** by
itself attribute the lost SFX to DirectMusic: earlier captures establish more
than one relevant MGS2 sound path.  In particular, do not promote another
DirectMusic change solely from this observation.

The next controlled A/B is to disable only `MGS2_DMIME_SHAREDGROUPS` and repeat
the same Start-to-map transition.  It will distinguish the shared-port
lifecycle from an upstream game/SPU sound-state failure.  This needs a fresh
user-authorised restart; no hot-thread logger is to be enabled in the gameplay
run.

## Multipath DirectMusic A/B prepared (2026-08-10)

The required restart was performed.  The previous top-level wrapper on the
console was preserved as `MGS2-Substance.sh.before-dmime-ab-20260810`; the
replacement was SHA-256 verified before use.  This invocation changes exactly
one sound-routing choice from the prior stock-`user32` run:

```text
MGS2_DMIME_SHAREDGROUPS=0
MGS2_USER32_DLL=__stock__
MGS2_PEEK_WAIT=0
MGS2_PEEK_HOT=0
MGS2_PEEK_WAIT_MS=0
```

The shell wrapper defaults `MGS2_DMIME_SHAREDGROUPS` to `1`, but now preserves
an explicit `0` for this one launch.  Its current normal production default is
therefore unchanged.

Immediately after launch, one MGS2 process and one live `gptokeyb` process
were present.  `dmusic_shared_lifetime1.dll`, `dmsynth_se2_lifetime.dll`,
`dmime_se1.dll`, `dsound_se1.dll`, `wined3d_batch16_setcache.dll`, and
`d3d8_producer_batch14_dirtyranges.dll` each compared byte-for-byte with their
Wine mount targets.  `user32_peek1.dll` did *not* compare equal to the live
`user32.dll`, confirming the stock-user32 control.  No audio trace or
hot-thread sampler was enabled.

The outstanding observation is solely the user's result for the same
`Start -> map -> return to gameplay` sequence.  Do not interpret this setup
record as evidence for or against the shared-port hypothesis until that result
is recorded.

### Result

The user repeated the sequence: gameplay SFX still disappeared after opening
and closing the map.  They also heard added audio lag with shared groups
disabled.  Therefore `MGS2_DMIME_SHAREDGROUPS=0` is a **negative A/B**: it
does not cure the map-triggered SFX loss and is unsuitable as production
configuration.  This rules out the shared-port choice itself as the primary
cause; it does not rule out other DirectMusic code, nor an upstream MGS2
SE/SPU state failure.  Restore the normal `MGS2_DMIME_SHAREDGROUPS=1` route
before further gameplay.

## Later live observation: map can also restore the symptom

With the normal shared route restored, the user opened and closed the map
without an immediate SFX loss.  Later, after encountering an enemy, encounter
music began, subsequently stopped, and gameplay sound disappeared.  Opening
and closing the map at that point restored the sound.

This replaces the overly simple ``Start causes loss'' model.  The map
transition can move the fault in **both** directions, so it is evidence of a
transition-sensitive state/lifetime problem, not proof that opening the map is
the original cause.  It is consistent with an AudioPath or game SE/SPU state
being reset by that transition, but does not distinguish them.

The existing post-hit sink-probe capture is empty (`marker=0`, `count=0`).  It
only recognises group 2 note `0x3c` at velocity `0x7f`, so repeating it would
again fail to cover punches, arbitrary player effects, reset state, or voice
exhaustion.  It is no longer the next diagnostic.

## Bounded dmsynth state recorder

`wine-patches/13-dmsynth-state-recorder.patch` adds an env-gated 256-record
ring to `dmsynth` and keeps it adjacent to the established sink-probe state.
With `MGS2_DMSYNTH_STATE=1`, the synth records only in memory:

* open-time resets and MIDI system resets as separate counters/events;
* positive-velocity note-ons, their FluidSynth return value, voices before and
  after, and the selected soundfont/bank/program;
* bank and program changes;
* the last and maximum active voice count observed by the existing post-render
  status refresh.

There is no file I/O, allocation, or formatted logging in the recorder path.
Each ring record is committed by writing its sequence last, so an external
reader can reject a partially sampled entry.  The code default is off.

`harness/dmsynth_state.py` reads the state through `/proc/<pid>/mem` with only
Python's standard library and can diff two JSON snapshots.  One snapshot when
SFX are absent and one after the map restores them distinguishes:

1. a new MIDI reset or changed program/bank state;
2. failed note-on or a 48-voice ceiling;
3. no new note-on reaching `dmsynth`, which moves the fault upstream.

## Stock-user32 freeze captured with exact call site (2026-08-10)

The first live recorder run used stock `user32` as the outstanding input A/B.
After roughly four minutes the user reported that the game had frozen.  The
process was captured before restart:

* one game and one `gptokeyb` instance were running;
* the main thread used about 94% of one core while `wined3d_cs` slept in a
  futex and submitted no visible work;
* temperatures were 73.888 C / 68.125 C, with no OOM, GPU fault, thermal or
  audio error in the kernel log;
* `gptokeyb` still held physical `event4` and `/dev/uinput`, the Fake Keyboard
  existed, and sway reported the visible fullscreen MGS2 window focused;
* the dmsynth render state continued updating with zero active voices.  It had
  one open reset, zero MIDI resets, zero failed note-ons and a maximum of 13
  voices, far below the 48-voice ceiling.

A two-second, 49 Hz `perf record` captured 226 samples with none lost.  A batch
gdb attach exposed the Box86 guest state.  The main thread was in:

```text
win32u NtUserPeekMessage+0x1fa (0x602b74aa)
  -> ntdll NtYieldExecution (return at 0x60048206)
  -> libc sched_yield
```

The exact code is the empty-queue branch in `win32u/message.c`; disassembly of
the loaded, byte-verified `win32u_glfuncs3.so` places the call to
`NtYieldExecution` at file offset `0xb74aa`.  This is stronger than the earlier
generic ``live user-space spin'' snapshot: the no-render state is now tied to
the known MGS2 empty-PeekMessage hot loop.

Stock user32 is therefore a negative A/B: it does not prevent the apparent
freeze/input-loss class.  The next launch restored byte-verified
`user32_peek1.dll` with the measured caller-specific 4 ms wait
(`MGS2_PEEK_HOT=401176`, `MGS2_PEEK_WAIT=1`).  This removes the captured yield
spin but is not yet claimed to cure every historical input-loss occurrence.

Preserved one-shot artefacts:

```text
logs/live-20260810/dmsynth-state-freeze.json
logs/live-20260810/mgs2-freeze.perf
logs/live-20260810/mgs2-freeze-maps.txt
```

## Natural SFX loss and enemy-alert recovery (2026-08-10)

On the next normal production run (PID 2690), the user opened and closed the
map with Start and gameplay SFX disappeared again.  Roughly one minute later
the sound returned when an enemy completed the alert/report that Snake had
been found.  This is a second transition that can restore the fault, independent
of reopening the map.

One-shot snapshots were taken in both audible states without restarting the
game.  The thread populations and cumulative CPU shares were effectively
unchanged: `wined3d_cs`, `wine_dsound_mix`, `wine_dmime_mess`, both
`wine_dmsynth_si` threads and the PipeWire threads remained alive.  The process
environment did not change.  This reinforces the conclusion that the symptom
is an internal game/audio-state transition rather than a lost backend or dead
audio thread.

The normal wrapper had started this process with `MGS2_DMSYNTH_STATE=0`, so the
ring contains no evidence from the actual loss/recovery interval.  Do not infer
a MIDI reset or program change from these two snapshots.  After recovery, the
recorder's exact four-byte cached enable flag was switched from 0 to 1 in the
live, byte-verified DLL.  Within one second it recorded 9 successful note-ons,
zero failed/no-voice events, no resets, and four active voices using soundfont
1, bank 1, program 91.  The same process can therefore capture the next natural
occurrence without a restart.

Preserved artefacts:

```text
logs/live-20260810/sfx-transition-0216/mgs2-sfx-loss-20260810-021602.tar.gz
logs/live-20260810/sfx-transition-0216/mgs2-sfx-restored-20260810-021659.tar.gz
logs/live-20260810/sfx-transition-0216/dmsynth-state-baseline-enabled.json
```

### First fully recorded recovery interval

The user then attacked an enemy, lost gameplay sound, and heard it return when
the enemy completed the alert report.  The recorder was enabled throughout
this occurrence.  Its captured 256-record window spans 13.606 seconds and
contains 64 identical successful note-ons, each preceded by the game's repeated
bank/program selection:

```text
group=1 channel=0 note=60 velocity=127
soundfont=1 bank=1 program=91
note-on result=FLUID_OK
voices before/after: 1..3 -> 2..4
```

There were zero open/MIDI resets, zero failed note-ons, zero no-voice results,
and the session maximum was 12 voices.  The alert/report recovery therefore
does not recreate the synth, reset MIDI, or clear voice exhaustion.  Instead,
it coincides with a sustained stream of valid group-1 events reaching the same
synth and creating voices.  The player's missing attack event is absent from
this retained window; because the high-rate report sequence wraps 256 entries
in about 14 seconds, this is not yet proof that the attack was dropped upstream.

The exact JSON is preserved as:

```text
logs/live-20260810/sfx-transition-0216/dmsynth-state-attack-loss-report-restored.json
```

For the remainder of this live session, an external eight-second sampler keeps
48 rotating JSON snapshots under `/tmp/mgs2-dmsynth-roll`.  It reads one small
fixed memory region and does not inspect every thread or log from the audio
path.  This preserves several minutes across the next short loss/recovery pair.

### Start-loss boundary and the disproved CC recovery hypothesis (2026-08-10)

The next Start/map occurrence was archived before the old process was stopped:

```text
logs/live-20260810/sfx-transition-0216/mgs2-start-loss-with-roll.tar.gz
sha256 4249067ac41d4d86b28ef41948786185151876f3b304bf60fab32b6556457075
```

Sixteen rotating snapshots cover about 136 seconds. Across the merged ring
windows, 849 note-ons reached dmsynth, all returned `FLUID_OK`, all created
voices, and there were no synth resets or voice-limit failures. The final
silent-state sample had 2 active voices and a session maximum of 12. This rules
out those failures for the recorded events. It does not prove that the specific
missing player effect reached the ring because no event was correlated with
that effect.

`harness/dsound_live_state.py` then read the active Wine objects directly from
the same process. The private 22050 Hz synth buffer was still `PLAYING`, at
DirectSound volume 0 dB, with continuously updated non-zero PCM. The synth
master attenuation was only -6 dB. Restarting the buffer or changing port
master volume would therefore address the wrong layer.

One live read also appeared to expose FluidSynth per-channel controllers:
channels 2..15 were zero while other channels were non-zero. That terminal
snapshot was not preserved as an artefact, and patch 13 does not record CC.
More importantly, production does not enable `MGS2_DMSYNTH_GROUPMAP`, so all
849 note-ons in the preserved Start-loss interval used effective channel 0
(843 from group 1 and 6 from group 2). The zero values on channels 2..15 were
therefore not evidence for the recorded silent events. Treat the earlier CC
attribution as retracted.

Patch 14 added an opt-in, note-triggered guard. It does not reject or clamp a
fade to zero. When a later positive-velocity note arrives on that same channel,
it restores exact-zero CC7 to 100 and/or CC11 to 127 immediately before
creating the voice; existing non-zero values are unchanged. Every restoration
can also be stored as a `note_unmute` event when the recorder is enabled. The
deployed configuration selected:

```text
dmsynth_se4_unmute1.dll
sha256 10b17a1372def2bbea75ed5862ebfe9ce3055966ccbcfef8e6f8f537aa118ca3
MGS2_DMSYNTH_UNMUTE_NOTES=1
```

The device copy and live bind mount compared byte-for-byte after restart. This
verified deployment only; it did not verify the proposed cure. The previous
wrapper remains recoverable as
`/storage/roms/ports/MGS2-Substance.sh.before-unmute-20260810-0940`.

After the first successful gameplay check, the user noticed a small performance
drop. The live device was already at 81.111 C and the thermal guard had stepped
the CPU through 1800 and 1608 MHz to its 1416 MHz floor after three 84.444 C
samples. This is the known thermal ladder, not an audio failure: 1091 note-ons
had completed with zero failures and no more than 12 voices. The state recorder
was returned to production-default off; set `MGS2_DMSYNTH_STATE=1` only for a
bounded regression capture.

### Production regression of patch 14 (2026-08-10)

The user later reproduced the defect while the deployed process had both
`dmsynth_se4_unmute1.dll` and `MGS2_DMSYNTH_UNMUTE_NOTES=1`: gameplay SFX
vanished on an enemy encounter and returned after opening and closing the map.
This is a negative production test. Patch 14 is not a sufficient fix.

The process environment and immediate post-recovery system state were archived
as:

```text
logs/live-20260810/sfx-regression-post-start/
  mgs2-sfx-regression-20260810-125231.tar.gz
  dmsynth-state-post-start-brief.json
  dsound-live-post-start-brief.json
```

The regression began with `MGS2_DMSYNTH_STATE=0`, so neither the failing
interval nor any possible `note_unmute` event was recorded. The valid synth and
DirectSound snapshots were taken only after Start restored sound; they are a
post-recovery baseline, not a silent-state measurement. They show effective
channel 0 at CC7/CC11 127/127 and the synth buffer still `PLAYING`, but cannot
establish what changed at the failure boundary.

The strongest untested source-level candidate is now DirectMusic curve
delivery. `seqtrack.c` fills the complete `DMUS_CURVE_PMSG`, including duration,
end/reset values and flags, while `performance.c` translates a CC curve into
one MIDI controller message containing only `nStartValue`. It ignores
`nEndValue`, `mtDuration`, reset semantics and the curve shape. That can leave a
transition fade at its start value until a later map/alert transition writes a
new value. It matches the symptom, but is not yet proven to be exercised by
MGS2. The next capture must record curves and CC7/CC11 changes in bounded
memory before any further recovery patch is promoted.

The self-contained handoff and independent review are:

```text
docs/briefs/MGS2_INTERMITTENT_SFX_HANDOFF_2026-08-10.md
docs/briefs/MGS2_INDEPENDENT_AUDIO_REVIEW_2026-08-10.md
```

## Separate complete freeze captured on 2026-08-11

A later production freeze was not the stock-`user32` `PeekMessage` spin
documented above. Main, `wined3d_cs`, and `wine_dinput_worker` all waited on one
native mutex whose owner was the waiting input worker itself. Releasing that
exact mutex once resumed the live game. Source inspection and a direct old/new
A/B then identified Box86's non-atomic first-use publication of an x86 mutex's
native ARM backing object.

The evidence, fix, deterministic stress test and rollback are documented
separately so the two stall mechanisms are not conflated:

```text
docs/briefs/MGS2_RUNTIME_MUTEX_FREEZE_2026-08-11.md
```

# FINALPLAY20 DMSynth resume production — 2026-08-27

## Decision

Wine patches 60+83 and the one-tick recovery setting are promoted together as
FINALPLAY20. The normal PortMaster entry selects the exact 19-row bundle;
FINALPLAY19 remains an immediate byte-exact rollback. FINALPLAY20 changes only
the DMSynth DLL and its fixed watchdog state from FINALPLAY19. Box86, the input
helper, DXVK, the other audio modules, Wine Wayland/Vulkan and system driver
bytes are unchanged. This promotion makes no FPS claim.

## Proven cause

After deep suspend/resume, music remained current but player steps and attacks
were delayed by roughly ten seconds. The separation matters: gameplay SFX use
the Wine DMSynth sample timeline, while the music reaches PipeWire through a
different buffer. The live PipeWire graph remained running with 10 ms node
latency and a 30 ms quantum, so it cannot explain a ten-second delay limited to
two gameplay sound classes.

The p35 recovery route kept one game process alive and restored its DirectSound
transport, but a read-only observation of its `synth_sink` found the actual
timeline error:

```text
activate_time + written_samples_time - master_time = -18.302 seconds
```

At 22050 Hz, a new event stamped with the current reference time therefore
mapped about 18 seconds ahead of what DMSynth was rendering. The reported
roughly ten seconds is consistent with checking while the renderer was already
working through that gap. The initial address-locator scanned writable maps and
had measurable observer cost, so it is not retained as a recurring harness;
all p37 follow-up reads address one known object and copy exactly 152 bytes.
That cost can affect the exact magnitude but does not explain the already
reported selective delay or change the sign of the stale-clock result.

## Bounded fix

Wine patch 83 extends p35 in two places:

1. a successful stopped/lost/stalled DirectSound re-arm publishes one atomic
   `timeline_rebase_pending` marker;
2. the render thread, which already owns `sink->written`, consumes the marker
   and compares the sample mapping with the current DirectSound write lead.

Only a deficit greater than 250 ms is changed. The render thread moves
`activate_time` forward by the measured deficit and shifts every already queued
MIDI event backward by the equivalent sample count. `PlayBuffer` now holds the
synth queue lock across reference-time conversion and insertion, so an event
cannot race halfway across the rebase. Event order and relative timing are
preserved.

There is no new thread, import, wall-clock dependency, polling process or
hot-thread logging. A normal watchdog recovery with no stale sample clock is a
no-op. The exact source delta from p35 is
`wine-patches/history/83-dmsynth-resume-timeline-rebase.patch`.

Production identity:

```text
dmsynth_p37_resume_timeline.dll
b11c9b6ba2f1d27fcdea822fff37f62187862aa7aeb5527d2efd2a159778ede8
```

Pre-promotion closed route:

```text
launch-dmsynth-resume-p37-candidate.sh
DMSYNTH_RESUME_P37_CANDIDATE.manifest
MGS2_DMSYNTH_WATCHDOG_STALL=1
```

Its 19-row identity differs from FINALPLAY19 only at `dmsynth.dll`. The p37 PE
has the same imported DLL set as p35. Normalized disassembly changed only
`synth_PlayBuffer`, the render/recovery call paths, three queue helpers and the
compiler's bounded unsigned-division helper; other reported differences were
only relocated debug-string addresses.

## Device gates

- Exact p37 bytes were verified both in the game directory and at the live
  `/usr/lib/wine/i386-windows/dmsynth.dll` bind mount.
- The closed route had exactly one game process, PID `111654`, and the live
  environment contained the named p37 route plus
  `MGS2_DMSYNTH_WATCHDOG_STALL=1`.
- The pixel-gated autoloader selected LOAD GAME, moved from save row 09 through
  08 to the intended row 07, confirmed the gameplay frame, completed four
  movement bursts and four attacks.
- The cold run had no unhandled exception, page fault or recovery failure. The
  single `Unhandled render state 161` warning is an inherited DXVK D3D9 warning,
  not a process exception.
- One re-arm moved `activate_time` forward by `9.9144374 s`, proving that p37
  consumed the stale mapping rather than merely restarting DirectSound. The
  following exact-object reads had positive, not negative, synth latency.
- Two RTC-backed `PM: suspend entry (deep)` / `exit` cycles kept PID `111654`.
  During the second cycle, 16 reads over the first 1.5 seconds after resume
  copied 152 bytes each: rendering advanced continuously, latency stayed from
  `+3766.444` to `+3771.973 ms`, the rebase flag stayed clear, and no error was
  logged. Positive here means new current-time events are already due; it does
  not impose the former future-queue delay.

The player then used the console's ordinary sleep button. The kernel recorded
the suspend entry and exit, the same game PID survived, and exact-object reads
after resume placed the synth mapping at `+48.345` and `+47.018 ms` with the
rebase marker clear. `activate_time` moved forward by `17.2551524 s`. Steps and
attacks were audible immediately enough that the player confirmed the route
worked correctly; music had remained current throughout. This is a listening
correctness gate, not a sub-millisecond latency measurement.

A following active-game soak kept the same process through 180 short movement
cycles in `148.085 s`, with an attack every sixth cycle (30 attacks). It logged
no Wine/DXVK recovery error, kernel OOM kill, GPU reset or Vulkan device loss.

The normal external entry then passed nine fully cold starts. Every run
verified all `19/19` production identities and held the game process for 45
seconds before an exact-PID SIGTERM and normal launcher cleanup. The accepted
SEH logs contain only the handled cold-start `RPC_S_SERVER_UNAVAILABLE`
exceptions already seen in earlier production and the inherited one-shot DXVK
render-state-161 warning.

The device clocks exclude most of the externally observed suspended interval:
one roughly 20-second RTC cycle advanced immediate `CLOCK_REALTIME` by only
about 82 ms. This repeats the refutation of the p36 wall-clock detector and is
why p37 keys off actual transport recovery and sample mapping instead.

## Rejected alternatives

- p36's `GetSystemTimeAsFileTime` discontinuity is not a reliable resume
  witness on this device; retained as patch 82, never production.
- forcing p35 to one stalled-position tick restored transport sooner but left
  the sample mapping stale; its negative record is
  `MGS2_DMSYNTH_STALL1_RESUME_CANDIDATE_2026-08-27.md`.
- keeping the process alive is necessary for a seamless game session, but does
  not make an audio timing thread execute while the SoC is asleep and does not
  itself reconcile two clocks after resume.

## Cold-start boundary

One normal FINALPLAY20 launch before the nine-run series exited before the
renderer with a `c0000005` read at address `0x00000004`, instruction address
`0x79d9a004`, in the linked FluidSynth MIDI-file parser region. An earlier p36
candidate had shown the same instruction address. Normalized p35, p36 and p37
disassembly at that function is identical, and DMSynth does not intentionally
enter the MIDI-file parser on this game route. Three immediate warm controls
and all nine subsequent fully cold FINALPLAY20 starts passed. The observation
is real but does not attribute the fault to patch 83; no speculative parser,
Box86 or retry workaround is shipped. A future recurrence still needs its own
bounded exception capture.

## Production and rollback

The authoritative production files are listed below. The complete Wine patch
already contains patch 60; patch 83 is the incremental production delta.

```text
device/FINALPLAY20_DMSYNTH_RESUME.manifest
device/FINALPLAY20_PRODUCTION.sha256
device/FINALPLAY.lock
wine-patches/history/60-dmsynth-resume-recover.patch
wine-patches/history/83-dmsynth-resume-timeline-rebase.patch
```

Immediate one-launch rollback to the exact p34 DMSynth runtime in FINALPLAY19:

```sh
MGS2_RENDERER=fp19 /storage/roms/ports/MGS2-Substance.sh
```

The p35, stall1 and p37 candidate launchers remain only to reproduce the
measurement sequence. Patch 82 remains a rejected negative result and its p36
binary is not production.

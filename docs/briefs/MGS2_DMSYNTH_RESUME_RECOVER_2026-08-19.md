# MGS2 dmsynth p35 -- resume/stall recovery for the synth sink transport

**Date:** 2026-08-19
**Artifacts:** `binaries/dmsynth_p35_resume_recover.dll`
(`f387ff2d2f0273deee4313442c03c51373dc1ecaae3134c33cafde1a56392d0c`),
`wine-patches/60-dmsynth-resume-recover.patch`,
`wine-patches/UNAPPLIED-dmsynth-sink-startup-lifetime.diff`
**Status:** written, built, reviewed, semantically verified against the p34
source, and **not measured on the device**. Reviewed as the next production
candidate with its scope held to transport recovery; `launch-play.sh` still
defaults to p34 until a device run says otherwise. Nothing here claims the
intermittent SFX loss is fixed.

## 1. The report

The owner still loses gameplay sound. The clearest trigger is suspending the
console and continuing to play afterwards; it also happens after a death or
"some action in the game", and otherwise at random. Music and menu clicks are
not reported as lost in the same breath, so per rule 6 this is recorded as the
gameplay-SFX claim only.

## 2. The mechanism this patch addresses

`synth_sink_timing_thread()` in `dlls/dmsynth/synthsink.c`:

```text
Stop(buffer)
SetNotificationPositions(BUFFER_SUBDIVISIONS)
Play(buffer, 0, 0, DSBPLAY_LOOPING)      <- once, ever
for (;;)
    WaitForMultipleObjects(stop, notify, INFINITE)   <- no timeout
    GetCurrentPosition -> publish play_pos/write_pos/play_pos_time
```

Every position the render thread works from comes out of that one loop, and the
transport is started exactly once. If it stops, or the notifications stop
arriving, the thread is still alive and still blocked, `sink->play_pos` never
advances again, and the render thread goes on writing into a buffer nothing
plays. There is no code path back. That shape matches "suspend, resume, gameplay
sound gone until restart" exactly: a thread that cannot notice, and cannot
restart, its own dead transport.

Wine's ALSA path already recovers write errors with `snd_pcm_recover()`, which is
why this was addressed in dmsynth rather than in ALSA/PipeWire.

## 3. What patch 60 does

The wait gets a timeout, and the expiry is a watchdog tick. Two failures are
handled because DirectSound reports them differently:

```text
notifications arriving        -> woken by the event, timeout never expires,
                                 behaviour as before

no notification for 250 ms    -> GetStatus
   lost                       -> Restore, then Play(..., DSBPLAY_LOOPING)
   not playing                -> Play(..., DSBPLAY_LOOPING)
   playing, position moved    -> nothing but the usual position publish
   playing, position frozen
   for 4 consecutive ticks    -> Stop + Play(..., DSBPLAY_LOOPING) once
```

The second case is the load-bearing one. Wine keeps `DSBSTATUS_PLAYING` for the
secondary buffer itself whatever the mixer and the endpoint below it are doing,
so a device that stopped advancing across a suspend is **invisible** in the
status word; a status-only watchdog would tick forever and heal nothing. The
position-stall arm is therefore the half most likely to matter, and it is also
the half that is reasoned rather than measured.

After either an event or a timeout the loop always re-reads
`GetCurrentPosition` plus the master clock and publishes
`play_pos`/`write_pos`/`play_pos_time` as before.

`sink->written` is deliberately **not** touched from the timing thread. The
render thread's `synth_sink_wait_write()` already resynchronises it against the
published play position in its underrun branch, so a re-armed transport is
caught up by the thread that owns that field instead of racing it.

Two lifecycle details came out of review. The stop event is re-checked with a
zero timeout before the transport is touched, because a stop request can land
while the wait was timing out and the loop would otherwise restart a transport
the sink is already tearing down. And a successful re-arm clears both the stall
count and the last-seen position, so a recovery cannot trigger the next one from
the very position it was recovering from -- the first half of that was in the
original draft, the position baseline was not.

Costs, against rule 2: no logging per tick, and at most one `GetStatus` per tick
(four a second) and only while notifications are missing. A failed recovery is
not fatal -- only the first failure of an episode is reported, and the loop keeps
ticking, because ending the thread there would guarantee the silence the
watchdog exists to undo.

### Knobs, read once per process

| variable | default | meaning |
| --- | --- | --- |
| `MGS2_DMSYNTH_WATCHDOG_MS` | 250 | watchdog period; **0 restores the exact pre-patch `INFINITE` wait** |
| `MGS2_DMSYNTH_WATCHDOG_STALL` | 4 | consecutive stalled ticks before a re-arm; 0 keeps the watchdog, disables the re-arm |

`MGS2_DMSYNTH_WATCHDOG_MS=0` puts the control arm in the *same binary*, which is
the only clean A/B available here -- see section 5. Both knobs are read once per
process, so the arms are two runs of one binary, not two states inside one
session; binary identity is what the comparison needs, and that is preserved.

## 4. Verification done on the host

* Builds with no new warnings via
  `make -C ../recovered-session/build-wine-i386 dlls/dmsynth/i386-windows/dmsynth.dll`.
* `scripts/pefunc.py` over the p34-source build and the p35 build: 853 functions
  in both, none added or removed, and **exactly one** function changed --
  `synth_sink_timing_thread`, 458 -> 625 instructions. Every other function in
  `synthsink.o`, all of `synth.o` and all of fluidsynth are byte-identical after
  address normalisation.
* `wine-patches/60-dmsynth-resume-recover.patch` applies to the NO-ISLAND chain
  with `patch -p1 -F0 --batch`, zero fuzz.
* Nothing is measured: no device run, no capture of a resumed device, no A/B.

## 5. Build provenance: production p34 is not byte-reproducible from this tree

Attempting to rebase on production `dmsynth_p34_interp_reset.dll`
(`b4ec2cd0...`) turned up two things that matter more than the patch itself.

1. **The shared source tree had drifted past p34.**
   `../recovered-session/wine-11.0/dlls/dmsynth/synthsink.c` carried an
   unexported change set with mtime `2026-08-17 23:24`, i.e. after the 18:26 p34
   build and before the 23:34 `dmsynth_audit_round3.dll` build. It is in
   audit_round3, not in p34, and never reached `wine-patches/`. It propagates
   each sink thread's startup HRESULT back to `synth_sink_activate`, closes the
   thread handles, resets the stop events on deactivate and on every failure
   path, and frees the render buffer on early failures. To keep p35 = p34 +
   watchdog, the tree was reverted to the patch-chain source and that work is
   preserved as `wine-patches/UNAPPLIED-dmsynth-sink-startup-lifetime.diff`.
   The `.diff` suffix keeps it out of the `*.patch` chain glob on purpose. It and patch
   60 both rewrite the `if (!started)` startup-signal region, so stacking them
   needs one hunk merged by hand.
2. **p34 itself cannot be rebuilt byte for byte.** Rebuilding the patch-chain
   source with the tree's default flags gives 2,296,759 bytes against p34's
   2,333,760, `.text` `0x34eb0` against `0x36680`. The function *sets* are
   identical (same 853, same names, DWARF subprogram lists match), so this is
   codegen, not features: p34 was linked against an older `libfluidsynth.a`
   (the tree's was rebuilt 2026-08-17 23:34) and its objects came from partial
   rebuilds with different flag overrides -- audit-era objects, for instance,
   have TRACE compiled out, which p34's `synthsink.o` does not.

Consequence for testing: **do not treat a p34-versus-p35 device comparison as a
clean A/B for the watchdog.** The two binaries also differ by that codegen and
fluidsynth-lib difference. Use one binary and one variable instead -- same
fluidsynth, same codegen, same `synthsink.o`, same linker, one behavioural
difference -- across separate runs, since the knobs are read once per process:

```text
control     MGS2_DMSYNTH_DLL=dmsynth_p35_resume_recover.dll MGS2_DMSYNTH_WATCHDOG_MS=0
watchdog    MGS2_DMSYNTH_DLL=dmsynth_p35_resume_recover.dll
status-only MGS2_DMSYNTH_DLL=dmsynth_p35_resume_recover.dll MGS2_DMSYNTH_WATCHDOG_STALL=0
```

Patch 34's own audio-CPU claim (`interpolate_linear`, dmsynth samples 781 -> 514)
was measured against the p34-era build and is untouched by this work; nothing
here re-measures it.

## 6. How to test on the device

Production stays on p34: `device/launch-play.sh` still mounts
`dmsynth_p34_interp_reset.dll` by default, and nothing in this change promotes
p35. Select it explicitly:

```sh
# from the host, next to the other custom DLLs
scp binaries/dmsynth_p35_resume_recover.dll \
    "$MGS2_DEVICE:/storage/roms/ports/MGS2-Substance/"

# on the device, one instance only (rule 5)
cd /storage/roms/ports
XDG_RUNTIME_DIR=/var/run/0-runtime-dir WAYLAND_DISPLAY=wayland-1 \
MGS2_DMSYNTH_DLL=dmsynth_p35_resume_recover.dll \
    setsid nohup ./MGS2-Substance.sh > /tmp/run.log 2>&1 < /dev/null &
```

`MGS2-Substance.sh` `exec`s `launch-play.sh`, which takes the DLL from
`${MGS2_DMSYNTH_DLL:-dmsynth_p34_interp_reset.dll}`, so an exported variable
reaches it. Keep the external wrapper at
`/storage/roms/ports/MGS2-Substance.sh` in that `${VAR:-default}` form or it
silently overrides the selection.

Then verify byte-wise before believing the filename (rule 4):

```sh
cmp /usr/lib/wine/i386-windows/dmsynth.dll \
    "$GAMEDIR/dmsynth_p35_resume_recover.dll" && echo mounted
sha256sum "$GAMEDIR/dmsynth_p35_resume_recover.dll"
# expect f387ff2d2f0273deee4313442c03c51373dc1ecaae3134c33cafde1a56392d0c
```

The reproduction to run is the owner's own: reach gameplay with SFX confirmed
audible, suspend the console, resume, and listen for gameplay SFX specifically
-- separately from music and menu clicks. The watchdog, if it is the right
mechanism, heals within roughly `WATCHDOG_MS` for a stopped buffer and
`WATCHDOG_MS * (STALL + 1)` -- about one second at the defaults -- for a frozen
position. Anything that takes longer than a couple of seconds to come back, or
never comes back, is a different defect and should be reported as such.

The cheapest useful check is this and nothing more: run p35, confirm sound,
suspend, resume, wait about a second. Gameplay sound coming back on its own is a
strong result, because that trigger is already reproducible for the owner without
any harness. A long A/B campaign is not needed to learn that much; the control
run (`MGS2_DMSYNTH_WATCHDOG_MS=0`) is worth doing only if the result needs to be
defended, and if sound then stays lost, that is the first real evidence this
project has that the dmsynth transport is the thing dying.

Then simply play on p35. Two outcomes matter and they point in different
directions:

```text
suspend fixed, random loss after death/transition also gone
    -> p35 covered both; promote it and close the SFX track for now

suspend fixed, death/scene transition still kills sound sometimes
    -> do NOT extend p35.  That splits the defect in two and points the
       second one above dmsynth, at the dmime AudioPath lifecycle, where
       Activate(FALSE)/Activate(TRUE) is asymmetric -- section 7 becomes the
       next separate, targeted patch

suspend not fixed either
    -> dmsynth's transport is exonerated for that reproduction; the watchdog
       stays harmless but the cause is elsewhere
```

## 7. Deliberately not done

* **`dmime` AudioPath activation is still asymmetric.**
  `IDirectMusicAudioPathImpl_Activate()` in `dlls/dmime/audiopath.c` calls
  `IDirectSoundBuffer_Stop(This->pDSBuffer)` on deactivate and, on activate,
  only sets `fActive` -- it never restarts the buffer. That is a genuine gap,
  but the AudioPath's `pDSBuffer` is a different object from the synth sink's
  own transport, so restarting it could start a buffer unrelated to the missing
  SFX; `dmime_transition1` already failed to fix a transition defect this way.
  Left for a reproduction that points at it.
* **The recovered lifecycle change set stays out of p35.** Startup HRESULT
  propagation, thread handle cleanup, stop-event resets and the early-failure
  buffer release look defensible on their own, but folding them in now would mean
  a sound result -- better or worse -- with two candidate causes. They are a
  separate p36 if a read of them finds real bugs, not a rider on this patch.
* No new telemetry, no other audio DLL touched, no launcher default changed.

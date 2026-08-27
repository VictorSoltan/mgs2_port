# MGS2 dmsynth one-tick resume candidate -- rejected (2026-08-27)

Status: **rejected, never production**. FINALPLAY20 is now the default and the
promoted p37 timeline repair supersedes this experiment. FINALPLAY19 retains
`dmsynth_p34_interp_reset.dll` as the exact rollback.

## Problem and bounded change

The game and Wine process survive suspend; the verified test process kept PID
`87632` across `PM: suspend entry (deep)` and `PM: suspend exit`. The CPU cannot
execute the audio timing thread while the SoC is asleep, so keeping the process
alive does not by itself re-arm the DirectSound transport after resume.

Patch 60's p35 DLL already recovers a stopped, lost or position-stalled sink.
Its default is deliberately conservative: four unchanged-position watchdog
ticks at 250 ms each. The player heard the recovered gameplay SFX, but heard
them late. The new closed candidate changes no DLL byte. It loads the exact p35
DLL and forces:

```text
MGS2_DMSYNTH_WATCHDOG_STALL=1
```

Therefore the existing recovery is eligible on the first 250 ms watchdog
timeout with an unchanged play position. It adds no thread, import, hook,
polling process or hot-thread logging.

Exact p35 DLL:

```text
f387ff2d2f0273deee4313442c03c51373dc1ecaae3134c33cafde1a56392d0c
```

Route:

```text
launch-dmsynth-resume-stall1-candidate.sh
DMSYNTH_RESUME_STALL1_CANDIDATE.manifest
```

The 19-row manifest differs from FINALPLAY19 only at `dmsynth.dll`; its runtime
bytes are identical to the p35 candidate. The forced environment is verified
separately because a byte manifest cannot encode environment state.

## Rejected wall-clock p36 experiment

The p36 experiment attempted to identify resume from a greater-than-two-second
`GetSystemTimeAsFileTime` discontinuity. That premise is false on this device.
During an externally observed roughly 20-second RTC-wake test, the immediate
post-resume Linux `CLOCK_REALTIME` difference was only 345 ms even though the
kernel recorded a deep suspend entry and exit. The p36 event arm was therefore
not a reliable resume witness and the binary must not be promoted. Its source
diff is retained as the negative record in
`wine-patches/history/82-dmsynth-resume-gap-rearm-rejected.patch`.

The first p36 cold start also observed an unhandled `c0000005` in
`fluid_midi_file_read_event`, at DLL RVA `0xa004`. The p35 and p36 binaries have
the same FluidSynth instruction at that RVA. A p35 control then completed and
a p36 retry also completed. This is a real observed startup fault, but the
available evidence does not attribute it to the wall-clock change.

## Device gates completed

- p35 control: exact 19/19 identity, cold start, correct save load and 12 loaded
  gameplay movement bursts completed.
- p36 retry: exact 19/19 identity, cold start, correct save load and 12 movement
  bursts completed; retained only to avoid falsely attributing the earlier
  FluidSynth parser fault.
- stall1: exact 19/19 identity, cold start, correct save load and 12 movement
  bursts completed.
- Live stall1 identity: PID `87632`, exact p35 DLL hash above and
  `MGS2_DMSYNTH_WATCHDOG_STALL=1` read from `/proc/87632/environ`.
- Deep suspend/resume: the same PID survived; the speaker monitor contains
  gameplay-action energy after resume, and the game log has no recovery error.

The speaker recording is sufficient for sound-present correctness, not an
exact first-SFX latency claim: PipeWire capture start and the character's
footstep cadence are not synchronized tightly enough to distinguish a few
hundred milliseconds. The 250 ms bound is the configured watchdog eligibility
bound in the reviewed p35 code, not a waveform-derived latency measurement.

## Refuting result

The one-tick setting made transport re-arm eligible sooner, but did not repair
the DirectMusic sample clock. The player still heard roughly ten seconds of
delay on steps and attacks after resume while music stayed current. A live
read-only `synth_sink` observation found:

```text
activate_time + written_samples_time - master_time = -18.302 seconds
```

Thus the DirectSound transport was alive but new gameplay MIDI events mapped
many seconds ahead of the sample position being rendered. Lowering the stall
count only changes when `Stop + Play` occurs; p35 deliberately does not change
`sink->written`, `activate_time` or already queued events. That makes stall1 an
incomplete fix and rejects its promotion. See
`MGS2_FINALPLAY20_DMSYNTH_RESUME_PRODUCTION_2026-08-27.md` for the bounded p37
follow-up and promotion record.

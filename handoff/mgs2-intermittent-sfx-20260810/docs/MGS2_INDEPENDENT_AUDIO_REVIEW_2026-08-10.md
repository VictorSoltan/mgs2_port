# Independent review — MGS2 intermittent gameplay SFX

Date: 10 August 2026. The reviewer inspected the preserved artefacts and source
without editing the implementation.

## Conclusion

Patch 14 did not solve the defect, and the CC7/CC11 hypothesis was promoted
before its evidence supported it. The latest production reproduction with
`dmsynth_se4_unmute1.dll` and `MGS2_DMSYNTH_UNMUTE_NOTES=1` is a direct negative
test of the proposed cure.

## Evidence that survives review

- Map and enemy-alert transitions can both remove and restore gameplay SFX.
- The failure is selective; the backend and audio threads can remain alive and
  some audio classes can still be heard.
- `MGS2_DMIME_SHAREDGROUPS=0` did not fix it and added latency.
- The preserved Start-loss roll contains 849 successful note-ons: 843 group 1
  and 6 group 2, all effective channel 0. All created voices; the maximum was
  12 against a limit of 48; no MIDI reset was captured.
- That stream proves the synth worked for those events only. The missing player
  hit/attack was not individually identified in the ring.
- The new regression environment proves patch 14 was loaded and enabled.

## Why the controller argument fails

Production does not enable `MGS2_DMSYNTH_GROUPMAP`, so
`synth_event_channel()` collapses DirectMusic groups to the low MIDI channel
nibble. All 849 saved Start-loss note-ons used effective channel 0. The former
patch-14 rationale relied mainly on zeros seen on channels 2..15, which were not
the channels used by those saved notes.

The alleged silent-state CC snapshot was never saved, and patch 13 does not
record CC changes. Patch 14 also handles only exact zero; it would miss an
almost-silent low value, and a later CC at the same transition could overwrite
its restoration. Since the latest run began with `MGS2_DMSYNTH_STATE=0`, there
is no `note_unmute` record proving that the guard fired during the failure.

The valid controller/buffer JSON was collected after Start had already restored
sound. Channel 0 at 127/127 and a `PLAYING` synth buffer are therefore only a
post-recovery baseline.

## Strongest code candidate

`dmime/seqtrack.c` passes a complete DirectMusic curve message, but
`dmime/performance.c` reduces a controller curve to one CC at `nStartValue`.
It ignores `nEndValue`, `mtDuration`, reset value/duration, shape and flags. A
transition fade can consequently remain at the starting attenuation until a
later map/alert transition sends a new state.

This mechanism fits the observed bidirectional loss/recovery better than the
patch-14 guard, but it is not yet proven that the relevant MGS2 transition uses
such a curve.

Other incomplete semantics worth recording, not patching blindly:

- `IDirectMusicAudioPath::SetVolume()` is a no-op stub.
- `Activate(FALSE)` stops a path buffer; the TRUE path does not restart it.
- `PlaySegmentEx()` ignores its `audio_path` argument.

## Required next capture

Add bounded, memory-only history for:

1. every CC7/CC11 change, with group and effective channel;
2. CC7/CC11 before and after each note-on and its exact voice delta;
3. complete `DMUS_PMSGT_CURVE` fields and delivery/requeue action;
4. AudioPath `Activate()` and `SetVolume()` calls.

Capture once while silent before Start and once immediately after Start restores
sound. If a curve has a muted start and non-zero end/reset that Wine fails to
deliver, test correct endpoint/reset scheduling with a unit test and env gate.
Do not broaden patch 14 to arbitrary low controller values without that proof.

One recorder caveat also needs correction: `noteon_no_voice` increments only
when both pre- and post-note voice counts are zero. It can miss a failure when
some unrelated voice is already active. Per-record voice deltas avoided that
ambiguity in the preserved Start-loss analysis.

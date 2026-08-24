# Documentation index

The briefs are an append-only research record. Many older documents contain
conclusions that were later corrected, so choose the newest brief for the
problem rather than reading by filename alone.

## Current production

- [FINALPLAY16 production](briefs/MGS2_FINALPLAY16_DXVK_PRODUCTION_2026-08-24.md)
  — exact bundle, live identity gate, device witness and rollback.
- [First correct DXVK-Sarek gameplay](briefs/MGS2_DXVK_SAREK_FIRST_GAMEPLAY_2026-08-24.md)
  — bring-up sequence and failed loader/WSI paths.
- [DMC3 optimisation transfer](briefs/MGS2_DMC3_OPTIMIZATION_TRANSFER_2026-08-24.md)
  — why proprietary-libmali DXVK remained a candidate after PanVK failed.

## Performance

- [Next FPS research](briefs/MGS2_NEXT_FPS_RESEARCH_2026-08-22.md) — current
  decision boundary and the unprofiled part of the frame.
- [Combat differential profile](briefs/MGS2_COMBAT_PROFILE_2026-08-22.md).
- [Present gate](briefs/MGS2_PRESENT_GATE_2026-08-22.md).
- [Native phase A measurement](briefs/MGS2_PHASE_A_NATIVE_MEASURED_2026-08-21.md).
- [Native draw tail and direct mutex](briefs/MGS2_NATIVE_DRAW_TAIL_AND_DIRECT_MUTEX_2026-08-20.md).

The numbered `MGS2_PERF_BRIEF_*.md` sequence is historical. Brief 43 is the
last summary of the earlier WineD3D production line; later dated briefs
supersede it for current decisions.

## Audio

- [Intermittent SFX handoff](briefs/MGS2_INTERMITTENT_SFX_HANDOFF_2026-08-10.md)
  — current route for gameplay SFX loss.
- [DirectSound SFX state capture](briefs/MGS2_DSOUND_SFX_STATE_CAPTURE_2026-08-10.md)
  — persistent player-attack/step pool reader.
- [DirectMusic state capture](briefs/MGS2_DMIME_STATE_CAPTURE_2026-08-10.md).
- [DMSynth resume recovery](briefs/MGS2_DMSYNTH_RESUME_RECOVER_2026-08-19.md)
  — suspend/resume transport watchdog and valid A/B boundary.
- [Manual combat/freeze/sound capture](briefs/MGS2_MANUAL_COMBAT_FREEZE_SOUND_CAPTURE_2026-08-13.md).

## Runtime freezes

- [Native DXT hitch research](briefs/MGS2_DXVK_NATIVE_DXT_HITCH_RESEARCH_2026-08-24.md)
  — побитово проверенный нативный DXT снял работу с texture worker, но не
  сократил 1.62-секундный gameplay gap; production не изменён.
- [Freeze and provenance](briefs/MGS2_FREEZE_AND_PROVENANCE_2026-08-23.md).
- [Box86 first-use mutex race](briefs/MGS2_RUNTIME_MUTEX_FREEZE_2026-08-11.md).
- [Separable third freeze](briefs/MGS2_SEPARABLE_FREEZE_CAPTURE_2026-08-12.md).
- [Initial runtime capture](briefs/MGS2_RUNTIME_BUG_CAPTURE_2026-08-09.md).

These are distinct signatures. Do not merge them into one “the freeze” theory.

## Operating the device

- [DEVICE.md](DEVICE.md) — access, launching, stopping, identity checks,
  profiling and thermals.
- [MGS2_RG353VS_HANDOFF.md](MGS2_RG353VS_HANDOFF.md) — early historical
  bring-up record. It is not the current production guide.
- [MGS2_PROJECT_STATE.md](MGS2_PROJECT_STATE.md) — early project narrative,
  retained for provenance.

## Evidence policy

Raw `logs/` and profiler output are local and ignored. Only small evidence that
is necessary to support a public brief belongs in `docs/evidence/`. Evidence
must not contain game assets, saves, credentials, private host paths or an
unbounded hot-thread trace.

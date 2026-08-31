# Documentation index

The briefs are an append-only research record. Many older documents contain
conclusions that were later corrected, so choose the newest brief for the
problem rather than reading by filename alone.

## Open defect register

- [Repository bug audit and the FINALPLAY21 flicker report](briefs/MGS2_BUG_AUDIT_2026-08-28.md)
  — expanded defect register across the renderer, release gates, shared
  launcher, Wine audio, Box86 Wayland and measurement harness. P1's
  fail-closed state-ownership route had an exact device gameplay smoke and is
  now promoted in FINALPLAY22,
  P2 is refuted by a live flag read, L1--L5 are fixed and device-exercised,
  and W1--W6's reproducible two-DLL route is also promoted after its pre-resume
  gameplay gate passed. RTC wake completed, but the device did not restore networking,
  so post-resume SFX survival remains open. E7 is intentionally skipped. Read
  sections 3.8 and 5 for exact hashes and what is still not device-proven.

## Current production

- [FINALPLAY22 audit-fix promotion](briefs/MGS2_FINALPLAY22_AUDIT_FIXES_PRODUCTION_2026-08-29.md)
  — current production; combines the exact state-owned wpatch view with Wine
  patches 84/85. FINALPLAY21 is the immediate exact rollback. The owner
  explicitly accepted the delayed flicker A/B and post-resume SFX gates. The
  deployed combined normal entry passed independent `21/21` identity and a
  row-07 movement/action smoke.
- [FINALPLAY21 missing-sea repair](briefs/MGS2_FINALPLAY21_WATER_WPATCH_PRODUCTION_2026-08-27.md)
  — exact rollback; its one-byte game-image view selects the existing
  fixed-function wpatch path, restores animated water, passes `21/21` identity
  and retains FINALPLAY20 as the immediate rollback.
- [FINALPLAY20 DMSynth resume production](briefs/MGS2_FINALPLAY20_DMSYNTH_RESUME_PRODUCTION_2026-08-27.md)
  — retained p37 rollback, measured sample-clock repair after suspend,
  ordinary sleep/listening gate, active-game soak, nine cold starts, exact
  `19/19` identity and FINALPLAY19 rollback.
- [FINALPLAY19 input and Wayland production](briefs/MGS2_FINALPLAY19_INPUT_WAYLAND_PRODUCTION_2026-08-27.md)
  — retained p34 rollback, p25/p26 Wayland fixes, immediate Start/Select edges
  and direct exit.
- [Input latency and exit-status-40 follow-up](briefs/MGS2_INPUT_AND_EXIT40_FOLLOWUP_2026-08-27.md)
  — crash evidence, proved gptokeyb delay/double-input cause and the candidate
  record that preceded FINALPLAY19 promotion.
- [FINALPLAY18 Wayland ABI production](briefs/MGS2_FINALPLAY18_WAYLAND_ABI_PRODUCTION_2026-08-26.md)
  — retained p24 rollback, loaded-game soak, deep suspend/resume, exact live
  identity and FINALPLAY17 rollback.
- [Active patch audit and Box86 Wayland ABI candidate](briefs/MGS2_PATCH_AUDIT_AND_WAYLAND_ABI_2026-08-26.md)
  — audit that found the now-promoted listener-ABI defect, launcher crash
  attribution, clean-build fix and exact Wine/Box86/DXVK reconstruction gates.
- [FINALPLAY17 freeze-reduction production](briefs/MGS2_FINALPLAY17_FREEZE_REDUCTION_PRODUCTION_2026-08-25.md)
  — corrected symmetric A-B-A-B, deterministic bundle, 18/18 live identity,
  normal-entry witness and rollback.
- [FINALPLAY16 production](briefs/MGS2_FINALPLAY16_DXVK_PRODUCTION_2026-08-24.md)
  — previous DXVK production and current `dxvk16` rollback.
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

- [FINALPLAY20 DMSynth resume production](briefs/MGS2_FINALPLAY20_DMSYNTH_RESUME_PRODUCTION_2026-08-27.md)
  — promoted repair for the measured stale sample clock behind delayed
  post-resume steps and attacks.
- [Rejected one-tick resume candidate](briefs/MGS2_DMSYNTH_STALL1_RESUME_CANDIDATE_2026-08-27.md)
  — transport re-arm alone did not remove the future event-queue delay.
- [Intermittent SFX handoff](briefs/MGS2_INTERMITTENT_SFX_HANDOFF_2026-08-10.md)
  — current route for gameplay SFX loss.
- [DirectSound SFX state capture](briefs/MGS2_DSOUND_SFX_STATE_CAPTURE_2026-08-10.md)
  — persistent player-attack/step pool reader.
- [DirectMusic state capture](briefs/MGS2_DMIME_STATE_CAPTURE_2026-08-10.md).
- [DMSynth resume recovery](briefs/MGS2_DMSYNTH_RESUME_RECOVER_2026-08-19.md)
  — suspend/resume transport watchdog and valid A/B boundary.
- [Manual combat/freeze/sound capture](briefs/MGS2_MANUAL_COMBAT_FREEZE_SOUND_CAPTURE_2026-08-13.md).

## Runtime freezes

- [DXVK pipeline gap and state-cache A/B](briefs/MGS2_DXVK_PIPELINE_GAP_AND_STATE_CACHE_2026-08-25.md)
  — memory timeline доказал pipeline chain; точный control исправил ошибочную
  provenance-границу. Warm cache, один worker и нативный fused DXT дали `-20.1%`
  по controlled sum и promoted в FINALPLAY17. Независимые game/read stalls и
  shared-memory/I/O pressure остаются открыты.
- [Win32 waits and RG353VS pressure](briefs/MGS2_DXVK_WAIT_DEVICE_PRESSURE_2026-08-24.md)
  — правильный LOAD GAME route отверг game deadline и thermal/SD/RAM как
  общий источник повторяющегося 1.62-s gap; Sleep(0) A/B снизил CPU load, но
  оставил `1.59--1.60 s`, поэтому busy loop не является основным freeze cause.
- [PeekMessage wait hitch A/B/C](briefs/MGS2_DXVK_PEEK_WAIT_HITCH_AB_2026-08-24.md)
  — live provenance исправил ложную границу A/B: FINALPLAY16 использует
  системный user32 без caller-specific wait; последующий wait census и
  system-pressure result находятся в brief выше.
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

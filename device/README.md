# Device launchers

## Production

- `MGS2-Substance.sh` — PortMaster-facing entry point.
- `launch-play.sh` — renderer selector.
- `launch-play-dxvk-fp22.sh` — current FINALPLAY22 audit-fix route.
- `launch-play-dxvk-fp21.sh` — exact FINALPLAY21 rollback.
- `launch-play-dxvk-fp20.sh` — exact FINALPLAY20/pre-water-fix rollback.
- `launch-play-dxvk-fp19.sh` — exact FINALPLAY19/p34 rollback.
- `launch-play-dxvk-fp18.sh` — exact FINALPLAY18 rollback.
- `launch-play-dxvk-fp17.sh` — shared fixed engine and exact FINALPLAY17 rollback.
- `launch-play-dxvk-fp16.sh` — byte-exact previous-DXVK rollback.
- `launch-play-wined3d-fp15.sh` — byte-exact rollback runtime.
- `FINALPLAY22_AUDIT_FIXES.manifest`, `FINALPLAY21_WATER_WPATCH.manifest`,
  `FINALPLAY20_DMSYNTH_RESUME.manifest`,
  `FINALPLAY19_INPUT_WAYLAND.manifest`,
  `FINALPLAY18_WAYLAND_ABI.manifest`,
  `FINALPLAY17_DXVK_FREEZE.manifest`,
  `FINALPLAY16_DXVK.manifest` and
  `FINALPLAY.manifest` — fail-closed live identity gates.
- `mgs2.gptk` — tracked controller-to-keyboard mapping. Legacy fixed routes use
  PortMaster's `$GPTOKEYB` command for direct Start+Select exit. FINALPLAY19
  through FINALPLAY22 select the source-recorded immediate-edge helper and disable
  Wine's duplicate raw-controller route.

The fixed play launchers leave one bounded cold-path exit record in
`/tmp/mgs2-play-exit.log` with their route, Wine PID and real `wait` status.
They do not poll temperature and do not automatically signal the game. The
explicit `launch-dxvk-play.sh` research harness retains an emergency thermal
guard for unattended experiments; it is not reachable from the normal
PortMaster selector. Neither path logs from a render or audio thread.

The RG353VS also has an external wrapper at
`/storage/roms/ports/MGS2-Substance.sh`. When deploying a selector or launcher,
update the game-directory copy and the external entry together; otherwise the
wrapper can silently select an older runtime.

## Research

`launch-*.sh` files with an experiment name are explicit research entry points.
They set `MGS2_RESEARCH_RUN`, select a matched binary set and then delegate to
the appropriate full launcher. They are retained because the briefs reference
their exact controls and rollback boundaries.

`launch-dxvk-wayland-abi-candidate.sh` preserves the research form used to
validate the now-promoted Box86 patches 23+24 bytes. FINALPLAY18 rollback uses
`launch-play-dxvk-fp18.sh` and `FINALPLAY18_WAYLAND_ABI.manifest`. The exact
listener ABI gate is `harness/wayland/run_device_wayland_abi_gate.sh`.

`launch-input-immediate-candidate.sh` preserves the exact closed route used to
validate the p25 ABI fix, p26 reproducible artifact and immediate-edge helper.
FINALPLAY19 preserves the byte-identical promoted route through
`launch-play-dxvk-fp19.sh` and `FINALPLAY19_INPUT_WAYLAND.manifest`; FINALPLAY20
inherits it unchanged, as do FINALPLAY21 and FINALPLAY22.
`FOLLOWUP_CANDIDATE.lock` retains the pre-promotion
record; `FINALPLAY.lock` is the production reconstruction source.

The three `launch-dmsynth-resume-*-candidate.sh` routes preserve the p35,
one-tick and p37 measurement sequence. FINALPLAY20 preserves the promoted p37
bytes through `launch-play-dxvk-fp20.sh` and
`FINALPLAY20_DMSYNTH_RESUME.manifest`; FINALPLAY19 is the immediate p34 rollback.

FINALPLAY21 adds `patch-mgs2-wpatch-novs.sh`. It accepts only the locked legal
game EXE hash, creates and verifies a one-byte temporary image, and bind-mounts
that image for one launch. `launch-play-dxvk-fp21.sh` and
`FINALPLAY21_WATER_WPATCH.manifest` are the closed rollback route;
FINALPLAY20 is its immediate rollback.

FINALPLAY22 promotes the state-ownership game view and the two Wine audio
lifetime repairs. `patch-mgs2-wpatch-finalplay22.sh` accepts only the legal
original hash and generates only `d902ee43...` under its private `/tmp` name.
`FINALPLAY22_AUDIT_FIXES.manifest` pins that view plus exact `dmime_p16` and
`dmsynth_p38`; FINALPLAY21 is the immediate exact rollback.

`launch-wpatch-isolation-candidate.sh` is the bounded 2026-08-28 flicker
follow-up. It inherits FINALPLAY20, retains fixed-function water, keeps the
no-wrap IPU panel on the original vertex-shader path and disables leaked
fixed-function lighting at the wpatch plugin tail. Its legal-game transform,
source record and 21-row identity are pinned by
`WPATCH_ISOLATION_CANDIDATE.lock`, `WPATCH_ISOLATION_CANDIDATE.manifest` and
`harness/test_wpatch_isolation_candidate.sh`. FINALPLAY22 is the default; this
narrower candidate remains unexposed through `MGS2_RENDERER`.

`launch-dxt-surface-witness-candidate.sh` isolates Box86 patch 27 on top of
FINALPLAY21. It strengthens the native DXT-surface arming fixture and exports a
fixed six-word one-way witness for an external reader; it adds no hot-thread
log or per-call counter. `DXT_SURFACE_WITNESS_CANDIDATE.lock`, its 21-row
manifest and `harness/test_dxt_surface_witness_candidate.sh` pin the exact
candidate boundary. The route is research-only and is not exposed through
`MGS2_RENDERER`; normal FINALPLAY21 is its exact rollback.

`launch-wpatch-state-ownership-candidate.sh` preserves the pre-promotion
single-variable visual route. It retains the water/IPU split
and lighting cleanup, owns stage-0 `D3DTTFF_COUNT2` before the UV matrix,
and keeps the same fixed-function decision in the software-VP startup branch.
The exact 58-byte legal-image transform, source patches and 21-row identity are
pinned by `WPATCH_STATE_OWNERSHIP_CANDIDATE.lock` and its harness gate. The
final image passed exact device identity and a short loaded-save movement/action
smoke; the delayed fixed-scene flicker comparison remains an open observation
accepted for FINALPLAY22 promotion.

`launch-audio-lifetime-candidate.sh` preserves the pre-promotion Wine 84/85
single-variable route on top of FINALPLAY21. Only `dmime.dll` and
`dmsynth.dll` differ from that rollback; fixed-epoch hashes, patched-source
hashes and the 21-row identity
are pinned by `AUDIO_LIFETIME_CANDIDATE.lock`. Exact device identity, live DLL
hashes and a loaded-save pre-resume action smoke passed; the RTC-wake run lost
remote networking before post-resume actions. Those exact bytes are now part
of FINALPLAY22 by owner directive; this wrapper remains for attribution.

The shared launcher now treats HUP/INT/TERM as terminal, keeps a busy temporary
game image instead of deleting its mounted backing file, verifies every clock
write, and persists the original same-boot governor/frequency baseline in
`/tmp/mgs2-cpu-baseline.state`. A run following SIGKILL recovers that
baseline instead of accepting the previous performance cap as the new normal.

`launch.sh` is the older general laboratory harness. It is not production.

Compiled artifacts named by these scripts live in the ignored local
`binaries/` cache or in a separately distributed release bundle, never in Git.

`harness/make_release.sh NAME` now packages the current FINALPLAY22 boundary by
default. It requires every exact artifact in `binaries/` (or an overridden
`MGS2_RELEASE_ARTIFACT_DIR`); `--from-device` may fill only missing rows from an
explicitly configured device, and `--deploy` additionally installs and
re-hashes all 25 distributable rows, including the four objects exclusive to
the exact FINALPLAY21 rollback. The legal game image and the ROCKNIX/Mali
system rows are excluded. The old reproducible WineD3D builder is available
only with `MGS2_RELEASE_ROUTE=wined3d-fp15` and edits a staged launcher, never a
tracked production file.

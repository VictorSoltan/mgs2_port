# Device launchers

## Production

- `MGS2-Substance.sh` — PortMaster-facing entry point.
- `launch-play.sh` — renderer selector.
- `launch-play-dxvk-fp21.sh` — current FINALPLAY21 animated-water route.
- `launch-play-dxvk-fp20.sh` — exact FINALPLAY20/pre-water-fix rollback.
- `launch-play-dxvk-fp19.sh` — exact FINALPLAY19/p34 rollback.
- `launch-play-dxvk-fp18.sh` — exact FINALPLAY18 rollback.
- `launch-play-dxvk-fp17.sh` — shared fixed engine and exact FINALPLAY17 rollback.
- `launch-play-dxvk-fp16.sh` — byte-exact previous-DXVK rollback.
- `launch-play-wined3d-fp15.sh` — byte-exact rollback runtime.
- `FINALPLAY21_WATER_WPATCH.manifest`, `FINALPLAY20_DMSYNTH_RESUME.manifest`,
  `FINALPLAY19_INPUT_WAYLAND.manifest`,
  `FINALPLAY18_WAYLAND_ABI.manifest`,
  `FINALPLAY17_DXVK_FREEZE.manifest`,
  `FINALPLAY16_DXVK.manifest` and
  `FINALPLAY.manifest` — fail-closed live identity gates.
- `mgs2.gptk` — tracked controller-to-keyboard mapping. Legacy fixed routes use
  PortMaster's `$GPTOKEYB` command for direct Start+Select exit. FINALPLAY19
  through FINALPLAY21 select the source-recorded immediate-edge helper and disable
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
inherits it unchanged, as does FINALPLAY21. `FOLLOWUP_CANDIDATE.lock` retains the pre-promotion
record; `FINALPLAY.lock` is the production reconstruction source.

The three `launch-dmsynth-resume-*-candidate.sh` routes preserve the p35,
one-tick and p37 measurement sequence. Normal production uses the promoted p37
bytes through `launch-play-dxvk-fp20.sh` and
`FINALPLAY20_DMSYNTH_RESUME.manifest`; FINALPLAY19 is the immediate p34 rollback.

FINALPLAY21 adds `patch-mgs2-wpatch-novs.sh`. It accepts only the locked legal
game EXE hash, creates and verifies a one-byte temporary image, and bind-mounts
that image for one launch. `launch-play-dxvk-fp21.sh` and
`FINALPLAY21_WATER_WPATCH.manifest` are the closed production route;
FINALPLAY20 is its immediate rollback.

`launch.sh` is the older general laboratory harness. It is not production.

Compiled artifacts named by these scripts live in the ignored local
`binaries/` cache or in a separately distributed release bundle, never in Git.

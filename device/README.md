# Device launchers

## Production

- `MGS2-Substance.sh` — PortMaster-facing entry point.
- `launch-play.sh` — renderer selector.
- `launch-play-dxvk-fp18.sh` — current FINALPLAY18 route.
- `launch-play-dxvk-fp17.sh` — shared fixed engine and exact FINALPLAY17 rollback.
- `launch-play-dxvk-fp16.sh` — byte-exact previous-DXVK rollback.
- `launch-play-wined3d-fp15.sh` — byte-exact rollback runtime.
- `FINALPLAY18_WAYLAND_ABI.manifest`, `FINALPLAY17_DXVK_FREEZE.manifest`,
  `FINALPLAY16_DXVK.manifest` and
  `FINALPLAY.manifest` — fail-closed live identity gates.
- `mgs2.gptk` — tracked controller-to-keyboard mapping. The fixed launchers use
  PortMaster's `$GPTOKEYB` command, which arms the device-specific Start+Select
  exit mode; a bare-system fallback passes explicit `-1`.

The three fixed play launchers leave one bounded cold-path exit record in
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
validate the now-promoted Box86 patches 23+24 bytes. Normal production uses
`launch-play-dxvk-fp18.sh` and `FINALPLAY18_WAYLAND_ABI.manifest`. The exact
listener ABI gate is `harness/wayland/run_device_wayland_abi_gate.sh`.

`launch-input-immediate-candidate.sh` is the closed follow-up route. It selects
the reproducible Box86 p25 text-input ABI candidate, the patched immediate-edge
gptokeyb helper and `winebus.sys=d` as one bundle. Its 19-row identity is
`BOX86_WAYLAND_TEXT_INPUT_CANDIDATE.manifest`; it is not selected by the normal
PortMaster entry before its remaining device gates pass.
`FOLLOWUP_CANDIDATE.lock` records both upstream/patch boundaries and candidate
artifact hashes without changing the current production reconstruction lock.

`launch.sh` is the older general laboratory harness. It is not production.

Compiled artifacts named by these scripts live in the ignored local
`binaries/` cache or in a separately distributed release bundle, never in Git.

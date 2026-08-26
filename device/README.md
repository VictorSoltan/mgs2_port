# Device launchers

## Production

- `MGS2-Substance.sh` — PortMaster-facing entry point.
- `launch-play.sh` — renderer selector.
- `launch-play-dxvk-fp17.sh` — current FINALPLAY17 runtime.
- `launch-play-dxvk-fp16.sh` — byte-exact previous-DXVK rollback.
- `launch-play-wined3d-fp15.sh` — byte-exact rollback runtime.
- `FINALPLAY17_DXVK_FREEZE.manifest`, `FINALPLAY16_DXVK.manifest` and
  `FINALPLAY.manifest` — fail-closed live identity gates.

The play launchers leave one bounded cold-path exit record in
`/tmp/mgs2-play-exit.log`. It distinguishes an emergency thermal SIGTERM from
an ordinary process exit without logging from a render or audio thread.

The RG353VS also has an external wrapper at
`/storage/roms/ports/MGS2-Substance.sh`. When deploying a selector or launcher,
update the game-directory copy and the external entry together; otherwise the
wrapper can silently select an older runtime.

## Research

`launch-*.sh` files with an experiment name are explicit research entry points.
They set `MGS2_RESEARCH_RUN`, select a matched binary set and then delegate to
the appropriate full launcher. They are retained because the briefs reference
their exact controls and rollback boundaries.

`launch-dxvk-wayland-abi-candidate.sh` is the fail-closed Box86 patch-23 route.
It changes only Box86 and verifies `BOX86_WAYLAND_ABI_CANDIDATE.manifest`; it is
not selected by the normal PortMaster entry while the candidate remains under
soak.

`launch.sh` is the older general laboratory harness. It is not production.

Compiled artifacts named by these scripts live in the ignored local
`binaries/` cache or in a separately distributed release bundle, never in Git.

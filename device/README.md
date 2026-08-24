# Device launchers

## Production

- `MGS2-Substance.sh` — PortMaster-facing entry point.
- `launch-play.sh` — renderer selector.
- `launch-play-dxvk-fp16.sh` — current FINALPLAY16 runtime.
- `launch-play-wined3d-fp15.sh` — byte-exact rollback runtime.
- `FINALPLAY16_DXVK.manifest` and `FINALPLAY.manifest` — fail-closed live
  identity gates.

The RG353VS also has an external wrapper at
`/storage/roms/ports/MGS2-Substance.sh`. When deploying a selector or launcher,
update the game-directory copy and the external entry together; otherwise the
wrapper can silently select an older runtime.

## Research

`launch-*.sh` files with an experiment name are explicit research entry points.
They set `MGS2_RESEARCH_RUN`, select a matched binary set and then delegate to
the appropriate full launcher. They are retained because the briefs reference
their exact controls and rollback boundaries.

`launch.sh` is the older general laboratory harness. It is not production.

Compiled artifacts named by these scripts live in the ignored local
`binaries/` cache or in a separately distributed release bundle, never in Git.

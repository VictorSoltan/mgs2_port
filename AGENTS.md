# AGENTS.md

This repository is a measured compatibility port of Metal Gear Solid 2:
Substance (2003) to the Anbernic RG353VS. The product of the work is the patch
record, measurement harness and written record of disproved hypotheses.

## Read in this order

1. `README.md` — public overview and repository layout.
2. `FINAL_PRODUCTION.md` — current runtime, exact rollback and provenance.
3. `docs/DEVICE.md` — safe device operation and measurement.
4. `docs/README.md` — routing to the current brief for each problem.

Do not read every historical brief before acting. Older conclusions were often
superseded or explicitly retracted.

## Current production

FINALPLAY16 is current as of 2026-08-24:

```text
D3D8 -> DXVK-Sarek 1.11.1 -> WineVulkan/Wayland -> proprietary armhf libmali
```

It uses a direct 32-bit Wine prefix and `box86-fp16-dxvk`. Promotion followed a
correct gameplay witness and an 18/18 live identity check. There is no matched
FINALPLAY15 FPS claim.

Immediate rollback:

```sh
MGS2_RENDERER=wined3d /storage/roms/ports/MGS2-Substance.sh
```

Read `docs/briefs/MGS2_FINALPLAY16_DXVK_PRODUCTION_2026-08-24.md` before
changing renderer defaults.

## Non-negotiable rules

1. **Measure on the device.** If it was not measured on the RG353VS, call it an
   assumption or estimate.
2. **Do not log from hot threads.** Use bounded memory rings and external
   readers. DirectSound logging and broad `wchan` sampling both created the
   stalls they were meant to diagnose.
3. **Control the scene and clock.** Frame rate varies from 22 to 60 FPS inside
   one run. Use one process, one fixed spot and a pinned frequency.
4. **Verify loaded bytes.** The launchers bind-mount DLLs and shared objects.
   Compare the live mount target against the manifest; filenames prove nothing.
5. **One instance only.** A background launch can outlive SSH and imitate severe
   lag.
6. **Separate audio claims.** Music, menu clicks and gameplay SFX are three
   observations.
7. **Preserve negative results.** A rejected hypothesis belongs in a brief with
   the evidence that rejected it.

## Current research entry points

- Production/DXVK:
  `docs/briefs/MGS2_FINALPLAY16_DXVK_PRODUCTION_2026-08-24.md`
- DXVK transfer rationale:
  `docs/briefs/MGS2_DMC3_OPTIMIZATION_TRANSFER_2026-08-24.md`
- Intermittent gameplay SFX:
  `docs/briefs/MGS2_INTERMITTENT_SFX_HANDOFF_2026-08-10.md`
- Sound after suspend/resume:
  `docs/briefs/MGS2_DMSYNTH_RESUME_RECOVER_2026-08-19.md`
- Runtime freezes/provenance:
  `docs/briefs/MGS2_FREEZE_AND_PROVENANCE_2026-08-23.md`
- Next FPS decision:
  `docs/briefs/MGS2_NEXT_FPS_RESEARCH_2026-08-22.md`

For a missing player attack, use the bounded DirectSound pool capture described
in `MGS2_DSOUND_SFX_STATE_CAPTURE_2026-08-10.md`. Do not start by changing
DirectMusic or adding mixer polling.

## Source trees and local configuration

The source/build trees live outside this repository. The conventional layout is:

```text
../recovered-session/wine-11.0/
../recovered-session/build-wine-i386/
../recovered-session/build-wine-unix32/
../recovered-session/mingw/bin/
../box86-src/
```

Machine-specific paths and the device SSH target belong in the ignored `.env`.
Start from `.env.example`. Scripts must accept environment overrides and must
not add usernames, home directories or LAN addresses to tracked files.

Do not mix the Wine 11.0 tree with the older CrossOver Android source tree.

## Patch boundaries

- `wine-patches/FINALPLAY15-wine-complete.patch` is the complete Wine source
  record against pristine Wine 11.0.
- `box86-patches/FINALPLAY15-box86-complete.patch` is the complete Box86 record
  against commit `0579f8b9`.
- `box86-patches/17-native-wayland-vulkan-bridge.patch` adds the FINALPLAY16
  Vulkan/Wayland bridge.
- `dxvk-patches/` contains the DXVK-Sarek delta; the present counter is
  research-only.

When implementation changes are made in an external source tree, export the
reviewed diff back into this repository. Never treat an unrecorded binary as the
source of truth.

## Public-repository hygiene

Do not commit:

- game executables, saves, Wine prefixes or game assets;
- compiled DLLs, shared objects, Box86 binaries or release directories;
- raw logs/profiles unless deliberately curated under `docs/evidence/`;
- `.env`, tokens, SSH state, personal absolute paths or editor caches.

Keep artifact hashes and fail-closed manifests in Git. Publish distributable
binary bundles separately with source references and the notices in
`THIRD_PARTY_NOTICES.md`.

## Workflow

```text
1. State one hypothesis and its refuting result.
2. Build the smallest bounded, default-off instrument.
3. Run it once on the device at a fixed scene and clock.
4. Record the number, hashes, caveats and rollback in a brief.
5. Promote only after correctness and symmetric measurement gates pass.
6. If it fails, add the path to the written dead-end record.
```

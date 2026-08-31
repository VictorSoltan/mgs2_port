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

FINALPLAY23 is current as of 2026-08-31:

```text
D3D8 -> DXVK-Sarek 1.11.1 warm cache/one worker
     -> WineVulkan/Wayland -> proprietary armhf libmali
texture decode -> Box86 native fused DXT5 surface bridge
patch surfaces -> game state-owned fixed-function wpatch fallback
                  + DirectShow movie-path null guard
```

It retains FINALPLAY20's direct 32-bit Wine prefix,
`box86-fp26-wayland-text-input-production` and the FINALPLAY19 immediate-edge
input route. FINALPLAY20 replaced only DMSynth p34 with p37 and fixed the
measured stale sample timeline that delayed steps and attacks after resume.
FINALPLAY21 additionally cleared only the game's custom wpatch vertex-shader
flag, restoring the missing animated sea. FINALPLAY22 owns the non-VS texture
transform state, isolates the IPU consumer, closes fixed-function lighting and
keeps the fallback through software-VP startup. It also promotes Wine patches
84/85 and exact `dmime_p16`/`dmsynth_p38` lifetime-recovery DLLs. The legal game
EXE is never stored or overwritten: a hash-pinned 60-byte temporary view is
bind-mounted for the launch. The visual and audio routes separately passed
`21/21` device identity and loaded-save action smokes; the owner explicitly
accepted the delayed flicker A/B and post-resume SFX gates. The deployed
combined normal entry subsequently passed independent `21/21` live identity,
row-07 load, four movements and four attacks. FINALPLAY23 adds exactly two
bytes to that view -- `ret` at `WinstrmSendIPic` (offset 4696000) and at
`RCTInit` (offset 4697600) -- closing the unguarded dereference of DirectShow
state that `WindowsMpegInit()` never creates in this executable. Measured
2026-08-31: `wine: Unhandled page fault on read access to 00000000 at address
0087AE0F`, wine exit 5, about 2.5 minutes into ordinary play. It generated its
exact image and passed `21/21` live identity; the loaded-save action smoke has
not re-run to completion and the movie trigger has not been re-exercised.
FINALPLAY22 is the immediate exact rollback. FINALPLAY20 promotion followed
exact-object clock checks, ordinary-button sleep/listening, a
180-movement/30-attack soak, nine of nine fully cold starts and 19/19 live
identity. FINALPLAY19 remains the exact p34 rollback. The inherited
corrected symmetric FINALPLAY16 versus FINALPLAY17 A-B-A-B reduced the
controlled gap sum by 20.1% and the two
pipeline-gap clusters by 32.3%. This is not a global FPS claim and the
independent game/read stalls remain open.

Immediate rollback:

```sh
MGS2_RENDERER=fp22 /storage/roms/ports/MGS2-Substance.sh
MGS2_RENDERER=fp21 /storage/roms/ports/MGS2-Substance.sh
MGS2_RENDERER=fp20 /storage/roms/ports/MGS2-Substance.sh
MGS2_RENDERER=fp19 /storage/roms/ports/MGS2-Substance.sh
MGS2_RENDERER=fp18 /storage/roms/ports/MGS2-Substance.sh
MGS2_RENDERER=fp17 /storage/roms/ports/MGS2-Substance.sh
MGS2_RENDERER=dxvk16 /storage/roms/ports/MGS2-Substance.sh
MGS2_RENDERER=wined3d /storage/roms/ports/MGS2-Substance.sh
```

Read `docs/briefs/MGS2_FINALPLAY22_AUDIT_FIXES_PRODUCTION_2026-08-29.md`,
`docs/briefs/MGS2_FINALPLAY21_WATER_WPATCH_PRODUCTION_2026-08-27.md`,
`docs/briefs/MGS2_FINALPLAY20_DMSYNTH_RESUME_PRODUCTION_2026-08-27.md`,
`docs/briefs/MGS2_FINALPLAY19_INPUT_WAYLAND_PRODUCTION_2026-08-27.md` and
`docs/briefs/MGS2_FINALPLAY18_WAYLAND_ABI_PRODUCTION_2026-08-26.md` and
`docs/briefs/MGS2_FINALPLAY17_FREEZE_REDUCTION_PRODUCTION_2026-08-25.md` before
changing Box86 or renderer defaults.

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
  `docs/briefs/MGS2_FINALPLAY22_AUDIT_FIXES_PRODUCTION_2026-08-29.md`
- DXVK transfer rationale:
  `docs/briefs/MGS2_DMC3_OPTIMIZATION_TRANSFER_2026-08-24.md`
- Intermittent gameplay SFX:
  `docs/briefs/MGS2_INTERMITTENT_SFX_HANDOFF_2026-08-10.md`
- Sound after suspend/resume:
  `docs/briefs/MGS2_FINALPLAY20_DMSYNTH_RESUME_PRODUCTION_2026-08-27.md`
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
- The complete Wine boundary already contains retained patch 60's DMSynth
  transport recovery. FINALPLAY20 applies patch 83's stale-timeline rebase on
  top. FINALPLAY22 applies patches 84/85 for dmime private message state and
  dmsynth sink lifetime/recovery. Patch 82 is a rejected wall-clock witness and
  is never production.
- `box86-patches/FINALPLAY15-box86-complete.patch` is the complete Box86 record
  against commit `0579f8b9`.
- `box86-patches/17-native-wayland-vulkan-bridge.patch` adds the FINALPLAY16
  Vulkan/Wayland bridge; patches 18--21 record diagnostics, the verified fused
  DXT bridge and its counter-free FINALPLAY17 production entry. Patch 22 fixes
  the clean-build graph without changing those bytes; patches 23+24 are the
  promoted FINALPLAY18 Wayland listener ABI fix. Patch 25 corrects the remaining
  reachable text-input callback signature; patch 26 closes its build-directory
  dependent embedded-revision boundary for FINALPLAY19.
- Game patches 02, 04 and 05 record FINALPLAY22's state-owned wpatch path. The
  deployed helper accepts only the locked original EXE hash and produces only
  the locked 60-byte result; never commit or distribute either game image.
- FINALPLAY17 D3D8 is base+DXVK patch 02 with `b_ndebug=true`; D3D9 is
  base+patches 01, 02 and 08 with `b_ndebug=false`. Do not collapse the stages:
  only the split recorded in `device/FINALPLAY.lock` reproduces both DLLs.
  The present counter and pipeline timeline remain research-only.

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

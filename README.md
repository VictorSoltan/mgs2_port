# Metal Gear Solid 2: Substance on the RG353VS

An evidence-driven port of the 2003 Windows release to the Anbernic RG353VS:
RK3566, Mali-G52, 1 GB RAM, ROCKNIX, Wayland, 32-bit Wine and Box86.

The repository contains source patches, launchers, measurement tools and the
research record. It does **not** contain the game, extracted game assets, a Wine
prefix, the proprietary Mali driver or compiled runtime bundles. A few small
gameplay screenshots are retained only as diagnostic evidence. You need a
legally obtained copy of the game.

This is an independent compatibility project and is not affiliated with or
endorsed by Konami, Anbernic, WineHQ, Box86 or DXVK.

## Current status

Picture, music, menu sounds, gameplay sound effects, input and saves work.

The current production configuration is **FINALPLAY21**:

```text
MGS2 D3D8 / Box86 native fused DXT5 surface decode
  -> DXVK-Sarek 1.11.1 (warm cache, one compiler worker)
  -> WineVulkan/Wayland
  -> proprietary Mali Vulkan (armhf)
```

Against exact FINALPLAY16, a corrected symmetric A-B-A-B reduced the four
controlled load/location gaps by **20.1%** and the two pipeline-gap clusters by
**32.3%**. Promotion also passed the correct LOAD GAME route and 18/18 live
identity on the device. These are first-use-stall measurements, not a global FPS
claim; independent game/read stalls remain.

FINALPLAY20 retains FINALPLAY19's exact Wayland/input fixes and replaces only
the DMSynth DLL plus its fixed watchdog state. After suspend, the old transport
recovery could restart DirectSound while leaving the DMSynth sample mapping
18.302 seconds behind; newly queued steps and attacks then played many seconds
late while music remained current. Wine patches 60+83 re-arm that transport and
rebase the stale mapping together. The exact bundle passed ordinary-button
sleep/listening, a 180-movement/30-attack soak, nine of nine fully cold starts
and `19/19` live identity on the RG353VS.

FINALPLAY21 retains that exact bundle and fixes the missing Big Shell sea. The
game's custom `wpatch` vertex shader produced a solid background void on this
D3D8/DXVK/Mali route; selecting the existing fixed-function fallback restored
the animated water. The change is an exact one-byte, hash-pinned temporary view
of the user's installed EXE: the original file is never overwritten or
distributed. The verified candidate had moving water with no black squares,
and the normal entry cold-started with `21/21` live identity.

Open problems:

- the earlier status-40 exit has no captured exception frame. FINALPLAY19 fixes
  an independently proved reachable callback defect and exceeded that exit
  point without recurrence, but the numerical exit status alone does not prove
  they had the same cause;
- intermittent gameplay-SFX loss across some encounter/map transitions;
- a rare pre-renderer cold-start page fault remains unclassified. Its relevant
  FluidSynth instructions are unchanged across p35/p36/p37, and it did not
  recur in the nine-run FINALPLAY20 cold-start gate;
- residual game/read stalls, including pressure/I/O-correlated cases;
- frame rate in dense reinforcement scenes.

The exact production identity, source provenance and rollback are in
[FINAL_PRODUCTION.md](FINAL_PRODUCTION.md).

## Start here

1. Read [FINAL_PRODUCTION.md](FINAL_PRODUCTION.md) for the current runtime.
2. Read [docs/DEVICE.md](docs/DEVICE.md) before touching the console.
3. Use [docs/README.md](docs/README.md) to choose the current research brief.
4. Copy the local configuration template:

   ```sh
   cp .env.example .env
   ```

5. Edit `.env` with the device address and your local Wine, Box86 and toolchain
   paths. The file is ignored by Git.

The launchers assume the user's game files and the manifest-matched runtime are
already installed in `MGS2_GAME_DIR`. Runtime binaries are local/release
artifacts; see [binaries/README.md](binaries/README.md).

## Repository layout

| Path | Purpose |
|---|---|
| `device/` | Production selector, fixed launchers, manifests and device-side helpers |
| `wine-patches/` | Wine 11.0 patch record; `history/` preserves superseded experiments |
| `box86-patches/` | Box86 changes against the pinned upstream commit |
| `dxvk-patches/` | DXVK-Sarek compatibility patches and optional counters |
| `game-patches/` | Source-equivalent records for hash-pinned game compatibility edits |
| `harness/` | External readers, profilers, correctness gates and rebuild tools |
| `docs/briefs/` | Append-only measurement and diagnostic record |
| `docs/evidence/` | Small, deliberately curated public evidence |
| `binaries/` | Ignored local artifact cache; only hashes and its README are versioned |
| `release/` | Ignored output from release tooling |

Generated captures, profiler output, Python caches, credentials and compiled
objects do not belong in Git.

## Production and rollback

The normal PortMaster entry selects DXVK:

```sh
/storage/roms/ports/MGS2-Substance.sh
```

Immediate one-launch rollback to exact FINALPLAY20 without the water-path edit:

```sh
MGS2_RENDERER=fp20 /storage/roms/ports/MGS2-Substance.sh
```

One-launch rollback to exact FINALPLAY19 and its p34 DMSynth:

```sh
MGS2_RENDERER=fp19 /storage/roms/ports/MGS2-Substance.sh
```

Immediate one-launch rollback to exact FINALPLAY18:

```sh
MGS2_RENDERER=fp18 /storage/roms/ports/MGS2-Substance.sh
```

One-launch rollback to exact FINALPLAY17:

```sh
MGS2_RENDERER=fp17 /storage/roms/ports/MGS2-Substance.sh
```

One-launch rollback to the previous byte-exact FINALPLAY16 DXVK path:

```sh
MGS2_RENDERER=dxvk16 /storage/roms/ports/MGS2-Substance.sh
```

One-launch rollback to the byte-exact FINALPLAY15 WineD3D path:

```sh
MGS2_RENDERER=wined3d /storage/roms/ports/MGS2-Substance.sh
```

`device/launch-play.sh` is only the selector. The complete launchers are:

- `device/launch-play-dxvk-fp21.sh` — current production;
- `device/launch-play-dxvk-fp20.sh` — exact pre-water-fix rollback;
- `device/launch-play-dxvk-fp19.sh` — exact FINALPLAY19/p34 rollback;
- `device/launch-play-dxvk-fp18.sh` — exact FINALPLAY18 rollback;
- `device/launch-play-dxvk-fp17.sh` — exact FINALPLAY17 rollback/shared engine;
- `device/launch-play-dxvk-fp16.sh` — previous DXVK rollback;
- `device/launch-play-wined3d-fp15.sh` — immediate rollback;
- `device/launch.sh` — archival laboratory harness, not production.

All named fixed runtime paths fail closed when live file hashes differ from their
manifests. A filename is never accepted as proof of what is loaded.
`device/mgs2.gptk` is the tracked controller mapping. Legacy fixed routes use
PortMaster's `$GPTOKEYB` command (or an explicit `-1` bare-system fallback).
FINALPLAY19 through FINALPLAY21 use the exact patched helper recorded under
`gptokeyb-patches/` and disable Wine's duplicate physical-controller route.
These routes make
Start+Select terminate the game directly instead of relying on the OS-level
confirmation dialog.

## Rebuilding

Pinned inputs:

- Wine 11.0 tarball, SHA-256 recorded in `device/FINALPLAY.lock`;
- Box86 commit `0579f8b9c47d87d700724f4cce559b06cbd2b0f5`;
- DXVK-Sarek `https://github.com/zeyadadev/DXVK-Sarek`, tag
  `v1.11.1-mali-fix`, commit
  `617958fe1cf2b10e06fa751d3e40bd765dcf2cc6`.

The complete FINALPLAY15 Wine/Box86 patches are the reconstruction boundary.
FINALPLAY16 added `box86-patches/17-native-wayland-vulkan-bridge.patch`.
FINALPLAY17 additionally records the verified fused-DXT path in Box86 patches
18--21; patch 22 fixes its clean-build graph without changing production bytes.
Box86 patches 23+24 are the FINALPLAY18 Wine 11 Wayland-listener ABI fix;
patch 24 gives callback publication explicit release/acquire ordering. Patch 25
corrects the remaining reachable text-input listener signature and is promoted
in FINALPLAY19; patch 26 pins the embedded revision across build directories.
The complete Wine boundary already contains patch 60's bounded DMSynth
transport recovery. FINALPLAY20 adds patch 83's stale-timeline rebase on top;
rejected patch 82 records why the device wall clock cannot be used as the
resume witness.
FINALPLAY17--21 also use exact state-cache mapping dedupe in
DXVK patch 08. The memory-only
present counter and pipeline timeline are diagnostic and are not part of the
production D3D9 DLL.

After configuring `.env`, verify the pinned reconstruction:

```sh
./harness/verify_rebuild.sh
./harness/verify_dxvk_rebuild.sh
./harness/test_gptokeyb_launchers.sh
./harness/test_finalplay18_production.sh
./harness/test_finalplay19_production.sh
./harness/test_finalplay20_production.sh
./harness/test_finalplay21_production.sh
```

Use `./harness/verify_rebuild.sh --build` only with the required cross
toolchains installed. Release artifacts are byte-reproducible only with the
flags and `SOURCE_DATE_EPOCH` recorded in the lock file and briefs.

The promoted native-Wayland route retains its separate exact callback gate:

```sh
./harness/wayland/run_device_wayland_abi_gate.sh
```

## Measurement rules

These rules are part of the project, not suggestions:

1. Measure on the RG353VS. Desktop reasoning is not a performance result.
2. Never log from a hot thread while judging that thread.
3. Compare the same scene in one process and pin the clock.
4. Verify mounted bytes with `cmp`/SHA-256.
5. Run exactly one game instance.
6. Report music, menu clicks and gameplay SFX separately.
7. Label every number as measured or estimated.

Several attractive optimisations were disproved only after violating one of
these boundaries. The rejected paths are retained in the briefs so they are not
repeated.

## What is actually measured

Historical WineD3D work established, among other results:

- the former 20 FPS fixed spot reached the game's 30 FPS limit after native
  Wine `memmove` and cached DISCARD shadowing;
- conservative visibility culling measured +17.5%;
- the native DirectSound FIR bridge reduced mixer CPU from 12.97% to 7.57% of
  one core at fixed 1416 MHz;
- native island entry 10 measured -8.87 ms/frame;
- shared native batch flush measured a paired median -2.680 ms/frame;
- entry 23 measured a robust roughly -2 to -2.6 ms/frame direction;
- the dmabuf presenter measured -9.45 ms/frame on its valid route.

These numbers belong to their recorded scenes and runtime versions. They must
not be added together or presented as a FINALPLAY17 FPS claim.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). In short: keep diagnostics bounded and
off by default, retain negative results, and include the exact device scene,
clock, binary hashes and rollback with every performance claim.

## Licensing

There is no single project-wide license yet. Wine-derived files are
LGPL-2.1-or-later, Box86-derived patches are MIT, and DXVK-derived patches use
the zlib license. See [LICENSE.md](LICENSE.md) and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

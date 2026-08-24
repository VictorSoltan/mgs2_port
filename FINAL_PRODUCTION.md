# FINALPLAY16 production record

FINALPLAY16 was promoted on 24 August 2026. The normal PortMaster entry selects:

```text
MGS2 D3D8
  -> patched DXVK-Sarek 1.11.1 D3D8/D3D9 (x86)
  -> WineVulkan + Wine Wayland
  -> proprietary Mali g29p1 Vulkan (armhf)
```

The owner validated lit, moving gameplay and explicitly authorised promotion.
The external wrapper then selected the same bundle and the launcher verified all
18 live identities. This is a correctness/promotion record, **not** a claim that
a matched FINALPLAY15 FPS A/B proved a gain.

The complete device capture, source hashes and rollback proof are in
`docs/briefs/MGS2_FINALPLAY16_DXVK_PRODUCTION_2026-08-24.md`.

## Launch and rollback

Normal launch:

```sh
/storage/roms/ports/MGS2-Substance.sh
```

Immediate one-launch rollback to the byte-exact FINALPLAY15 WineD3D runtime:

```sh
MGS2_RENDERER=wined3d /storage/roms/ports/MGS2-Substance.sh
```

The selector is `device/launch-play.sh`; it dispatches to one of two immutable
launchers:

- `device/launch-play-dxvk-fp16.sh`;
- `device/launch-play-wined3d-fp15.sh`.

Unknown renderer names fail instead of falling through.

## Production identity

`device/FINALPLAY16_DXVK.manifest` is the authoritative 18-row identity gate.
It covers seven supplied/bind-mounted files plus the exact system Wine, Vulkan
loader and proprietary Mali files on which the route depends.

Supplied production artifacts:

| Role | Artifact | SHA-256 prefix |
|---|---|---|
| Box86 | `box86-fp16-dxvk` | `104c79bcc15b` |
| D3D8 | `d3d8_dxvk_sarek_1.11.1_mali_wsiinit3.dll` | `22e519d266b6` |
| D3D9 | `d3d9_dxvk_sarek_1.11.1_mali_nullfix1.dll` | `40ead250117c` |
| DirectMusic synth | `dmsynth_p34_interp_reset.dll` | `b4ec2cd09f26` |
| DirectSound | `dsound_p36_native_fir_target.dll` | `302eff548429` |
| DirectMusic performance | `dmime_transition1.dll` | `ce3e3f14a62a` |
| DirectMusic port | `dmusic_shared_lifetime1.dll` | `1fe0a571503b` |

Use the full hashes in the manifest. Prefixes above are for human recognition,
not verification.

Runtime binaries are intentionally not tracked in Git. The local cache policy
is documented in `binaries/README.md`; source patches, checksums and manifests
remain versioned.

## Source provenance

Box86:

- upstream repository: `https://github.com/ptitSeb/box86.git`;
- base commit: `0579f8b9c47d87d700724f4cce559b06cbd2b0f5`;
- complete FINALPLAY15 delta:
  `box86-patches/FINALPLAY15-box86-complete.patch`;
- FINALPLAY16 Wayland/Vulkan bridge:
  `box86-patches/17-native-wayland-vulkan-bridge.patch`.

DXVK-Sarek:

- source: `https://github.com/zeyadadev/DXVK-Sarek`;
- tag: `v1.11.1-mali-fix`;
- commit: `617958fe1cf2b10e06fa751d3e40bd765dcf2cc6`;
- production compatibility changes: `dxvk-patches/01-*.patch` and
  `dxvk-patches/02-*.patch`;
- `dxvk-patches/03-memory-only-present-counter.patch` is diagnostic-only.

Wine:

- base: pristine Wine 11.0, hash in `device/FINALPLAY.lock`;
- complete FINALPLAY15 source delta:
  `wine-patches/FINALPLAY15-wine-complete.patch`;
- the FINALPLAY16 audio DLLs are the same byte-identified components used by the
  prior production route.

## What remains open

- A matched, scene-controlled FINALPLAY15/FINALPLAY16 performance comparison has
  not been completed.
- Intermittent gameplay SFX loss still requires a timestamp-correlated bounded
  capture.
- Runtime freezes have multiple known signatures; new occurrences must be
  captured and named rather than attributed by resemblance.

## Historical production

FINALPLAY12–15 provenance, the semaphore backport, the dmabuf presenter, native
island measurements and the corrected entry identity table are preserved in:

- `docs/briefs/MGS2_FREEZE_AND_PROVENANCE_2026-08-23.md`;
- `docs/briefs/MGS2_PRESENT_GATE_2026-08-22.md`;
- `docs/briefs/MGS2_PHASE_A_NATIVE_MEASURED_2026-08-21.md`;
- Git history before this public-repository cleanup.

Historical measurements remain valid only for the scene, clock and binaries
recorded in their briefs.

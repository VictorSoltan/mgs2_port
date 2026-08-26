# FINALPLAY17 production record

FINALPLAY17 was promoted on 25 August 2026. The normal PortMaster entry selects:

```text
MGS2 D3D8
  -> patched DXVK-Sarek 1.11.1 D3D8/D3D9 (warm cache, one worker)
  -> WineVulkan + Wine Wayland
  -> proprietary Mali g29p1 Vulkan (armhf)
```

Box86 also replaces the verified fused DXT5 surface-row conversion with a native
ARM implementation while preserving conservative guest fallbacks. A corrected
symmetric device A-B-A-B against exact FINALPLAY16 reduced the four controlled
load/location gaps by `20.1%` and the two pipeline clusters by `32.3%`. The
external wrapper then selected the deterministic bundle, loaded the correct save,
walked the scene and verified all 18 live identities. This is a first-use-stall
result, not a global FPS claim; independent game/read stalls remain.

The complete device capture, source hashes and rollback proof are in
`docs/briefs/MGS2_FINALPLAY17_FREEZE_REDUCTION_PRODUCTION_2026-08-25.md`.

A post-promotion audit on 26 August fixed launcher crash attribution and a
Box86 clean-build dependency without changing the production runtime bytes. It
also found a critical Wine 11 Wayland-listener ABI defect in the Box86 wrapper.
That runtime fix is isolated as patches 23+24 and is **not production** pending a
longer soak. See
`docs/briefs/MGS2_PATCH_AUDIT_AND_WAYLAND_ABI_2026-08-26.md`.

## Launch and rollback

Normal launch:

```sh
/storage/roms/ports/MGS2-Substance.sh
```

Immediate one-launch rollback to the byte-exact FINALPLAY15 WineD3D runtime:

```sh
MGS2_RENDERER=wined3d /storage/roms/ports/MGS2-Substance.sh
```

One-launch rollback to the previous byte-exact FINALPLAY16 DXVK runtime:

```sh
MGS2_RENDERER=dxvk16 /storage/roms/ports/MGS2-Substance.sh
```

The `dxvk16` selector branch was live-tested after promotion and matched the
unchanged FINALPLAY16 manifest `18/18`.

The selector is `device/launch-play.sh`; it dispatches to one of three fixed
launchers:

- `device/launch-play-dxvk-fp17.sh`;
- `device/launch-play-dxvk-fp16.sh`;
- `device/launch-play-wined3d-fp15.sh`.

Unknown renderer names fail instead of falling through.

Each fixed runtime launcher writes one bounded post-exit record to
`/tmp/mgs2-play-exit.log` with the route, Wine PID and real `wait` status.
Production and both fixed rollback routes have no thermal polling and send no
automatic temperature-triggered signal. Teardown also no longer signals a PID
after reaping it. The explicit DXVK research harness retains its separate
emergency guard for unattended measurements.

## Production identity

`device/FINALPLAY17_DXVK_FREEZE.manifest` is the authoritative 18-row identity gate.
It covers seven supplied/bind-mounted files plus the exact system Wine, Vulkan
loader and proprietary Mali files on which the route depends.

Supplied production artifacts:

| Role | Artifact | SHA-256 prefix |
|---|---|---|
| Box86 | `box86-fp21-dxvk-native-dxt-surface` | `51dfcc130b97` |
| D3D8 | `d3d8_dxvk_sarek_1.11.1_mali_wsiinit3.dll` | `22e519d266b6` |
| D3D9 | `d3d9_dxvk_sarek_1.11.1_mali_freeze1.dll` | `4918b0283329` |
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
  `box86-patches/17-native-wayland-vulkan-bridge.patch`;
- FINALPLAY17 DXT record: patches 18--20 contain the default-off diagnostics and
  verified fused bridge; patch 21 selects its counter-free production entry;
- patch 22 fixes only the clean parallel-build dependency for generated
  `arm_printer.c` and reproduces the existing production hash;
- patch 23 completes the Wine 11 Wayland listener ABI; patch 24 publishes the
  affected callback slots with release/acquire ordering. They are recorded as a
  candidate, have a separate manifest/launcher and are not selected normally.

DXVK-Sarek:

- source: `https://github.com/zeyadadev/DXVK-Sarek`;
- tag: `v1.11.1-mali-fix`;
- commit: `617958fe1cf2b10e06fa751d3e40bd765dcf2cc6`;
- D3D8 production stage: base plus `dxvk-patches/02-*`, Meson
  `b_ndebug=true`;
- D3D9 production stage: base plus `dxvk-patches/01-*`, `02-*` and
  unconditional exact-pair dedupe patch 08, Meson `b_ndebug=false`;
- the per-DLL epochs, tool versions, submodule commits and exact hashes are in
  `device/FINALPLAY.lock`; `harness/verify_dxvk_rebuild.sh` reproduces both;
- `dxvk-patches/03-memory-only-present-counter.patch` is diagnostic-only.

Wine:

- base: pristine Wine 11.0, hash in `device/FINALPLAY.lock`;
- complete FINALPLAY15 source delta:
  `wine-patches/FINALPLAY15-wine-complete.patch`;
- patches 01--03 after that boundary are default-off research instrumentation
  and its audit cleanup; no audit-built Wine DLL was deployed;
- the FINALPLAY17 audio DLLs are the same byte-identified components used by the
  prior production route.

## What remains open

- The two independent game/read stalls remain after the pipeline/DXT work and
  must be captured separately from compiler gaps.
- New state-cache entries may still compile once when later gameplay first
  encounters them.
- Intermittent gameplay SFX loss still requires a timestamp-correlated bounded
  capture.
- Runtime freezes have multiple known signatures; new occurrences must be
  captured and named rather than attributed by resemblance.

## Historical production

FINALPLAY16 remains the exact `MGS2_RENDERER=dxvk16` rollback and is documented
in `docs/briefs/MGS2_FINALPLAY16_DXVK_PRODUCTION_2026-08-24.md`.

FINALPLAY12–15 provenance, the semaphore backport, the dmabuf presenter, native
island measurements and the corrected entry identity table are preserved in:

- `docs/briefs/MGS2_FREEZE_AND_PROVENANCE_2026-08-23.md`;
- `docs/briefs/MGS2_PRESENT_GATE_2026-08-22.md`;
- `docs/briefs/MGS2_PHASE_A_NATIVE_MEASURED_2026-08-21.md`;
- Git history before this public-repository cleanup.

Historical measurements remain valid only for the scene, clock and binaries
recorded in their briefs.

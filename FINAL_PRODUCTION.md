# FINALPLAY21 production record

FINALPLAY21 was promoted on 27 August 2026. The normal PortMaster entry selects:

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

FINALPLAY19 added two runtime fixes to FINALPLAY18. Box86 patch 25 corrects the
remaining reachable Wine 11 text-input listener signature and publishes its
callback table atomically; patch 26 and the release recipe make the artifact
independent of source/build paths. The source-recorded helper delivers Start
and Select on their real button edges while preserving the same-device
direct-exit chord; Wine's duplicate physical-controller route is disabled. The
exact bundle passed the callback, loaded-game, input-edge, soak, direct-exit
cleanup and normal-entry `19/19` identity gates. See
`docs/briefs/MGS2_FINALPLAY19_INPUT_WAYLAND_PRODUCTION_2026-08-27.md`.

FINALPLAY20 retains that exact Box86/input route and replaces only DMSynth p34
with p37 plus a fixed one-tick recovery setting. The preceding transport repair
could restart DirectSound after suspend while leaving DMSynth's sample mapping
`18.302 s` behind, delaying newly queued steps and attacks while music remained
current. Wine patches 60+83 re-arm the transport and rebase the stale timeline
as one bounded recovery. The player confirmed ordinary-button sleep/resume,
then the same process completed 180 movement cycles and 30 attacks. The normal
entry passed nine of nine fully cold starts with `19/19` identity. See
`docs/briefs/MGS2_FINALPLAY20_DMSYNTH_RESUME_PRODUCTION_2026-08-27.md`.

FINALPLAY21 retains the complete FINALPLAY20 runtime and changes only the game
patch-surface route. The custom `wpatch` vertex shader left the Big Shell sea
as a solid background void through D3D8/DXVK/Mali. Clearing only
`M_DG_WINAPP_PATCH_USE_VERTEXSHADER` selects libdg's existing fixed-function
fallback and restored moving water. The exact candidate had no observed black
squares and normal-feeling FPS; the normal entry then passed `21/21` live
identity. The installed EXE is never overwritten: a fail-closed helper accepts
only the locked original hash, creates an exact one-byte temporary image,
bind-mounts it for the launch and restores the original path on cleanup. See
`docs/briefs/MGS2_FINALPLAY21_WATER_WPATCH_PRODUCTION_2026-08-27.md`.

## Launch and rollback

Normal launch:

```sh
/storage/roms/ports/MGS2-Substance.sh
```

Immediate one-launch rollback to the exact FINALPLAY20 runtime without the
water-path edit:

```sh
MGS2_RENDERER=fp20 /storage/roms/ports/MGS2-Substance.sh
```

One-launch rollback to the exact FINALPLAY19 p34 runtime:

```sh
MGS2_RENDERER=fp19 /storage/roms/ports/MGS2-Substance.sh
```

One-launch rollback to the exact FINALPLAY18 DXVK runtime:

```sh
MGS2_RENDERER=fp18 /storage/roms/ports/MGS2-Substance.sh
```

One-launch rollback to the exact FINALPLAY17 DXVK runtime:

```sh
MGS2_RENDERER=fp17 /storage/roms/ports/MGS2-Substance.sh
```

One-launch rollback to the previous byte-exact FINALPLAY16 DXVK runtime:

```sh
MGS2_RENDERER=dxvk16 /storage/roms/ports/MGS2-Substance.sh
```

Older one-launch rollback to the byte-exact FINALPLAY15 WineD3D runtime:

```sh
MGS2_RENDERER=wined3d /storage/roms/ports/MGS2-Substance.sh
```

The `dxvk16` selector branch was live-tested after promotion and matched the
unchanged FINALPLAY16 manifest `18/18`.

The selector is `device/launch-play.sh`; it dispatches to the fixed production
route or a named rollback route:

- `device/launch-play-dxvk-fp21.sh` — current production route;
- `device/launch-play-dxvk-fp20.sh` — exact pre-water-fix rollback;
- `device/launch-play-dxvk-fp19.sh` — exact p34 rollback;
- `device/launch-play-dxvk-fp18.sh` — exact p24 rollback;
- `device/launch-play-dxvk-fp17.sh` — shared fixed engine and p21 rollback;
- `device/launch-play-dxvk-fp16.sh`;
- `device/launch-play-wined3d-fp15.sh`.

Unknown renderer names fail instead of falling through.

Each fixed runtime launcher writes one bounded post-exit record to
`/tmp/mgs2-play-exit.log` with the route, Wine PID and real `wait` status.
Production and all fixed rollback routes have no thermal polling and send no
automatic temperature-triggered signal. Teardown also no longer signals a PID
after reaping it. The explicit DXVK research harness retains its separate
emergency guard for unattended measurements.

The tracked `device/mgs2.gptk` mapping is executed by the exact patched helper
in FINALPLAY19 through FINALPLAY21. Its default-off `-immediate-start-back` mode
emits normal Start and Select mappings on the physical down/up edges without waiting for chord
resolution. The closed route also sets `winebus.sys=d`, so Wine cannot consume
the same physical input first as a raw joystick action. Same-device
Start+Select still sends SIGTERM directly. The final device gate exited with
status 143 and left no game/helper process or MGS2 bind mount; the launcher lock
was available and the CPU/GPU governors were restored.

## Production identity

`device/FINALPLAY21_WATER_WPATCH.manifest` is the authoritative 21-row identity
gate. It retains all 19 FINALPLAY20 rows and adds the exact temporary game image
plus the tracked patch helper. It covers eight bind mounts and the exact system
Wine, Vulkan loader and proprietary Mali files on which the route depends.

Supplied production artifacts:

| Role | Artifact | SHA-256 prefix |
|---|---|---|
| Box86 | `box86-fp26-wayland-text-input-production` | `b7e9530f6039` |
| input helper | `gptokeyb-mgs2-immediate` | `49c782dad9da` |
| D3D8 | `d3d8_dxvk_sarek_1.11.1_mali_wsiinit3.dll` | `22e519d266b6` |
| D3D9 | `d3d9_dxvk_sarek_1.11.1_mali_freeze1.dll` | `4918b0283329` |
| DirectMusic synth | `dmsynth_p37_resume_timeline.dll` | `b11c9b6ba2f1` |
| DirectSound | `dsound_p36_native_fir_target.dll` | `302eff548429` |
| DirectMusic performance | `dmime_transition1.dll` | `ce3e3f14a62a` |
| DirectMusic port | `dmusic_shared_lifetime1.dll` | `1fe0a571503b` |
| game patch helper | `patch-mgs2-wpatch-novs.sh` | `b7ba819816b1` |
| temporary game view | generated from installed legal EXE | `6686b3fa6484` |

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
- patch 23 completes the original Wine 11 Wayland listener ABI; patch 24
  publishes the affected callback slots with release/acquire ordering;
- patch 25 corrects `zwp_text_input_v3_listener.delete_surrounding_text` from
  the erroneous `pppuu` bridge to the generated Wine 11 `ppuu` ABI and applies
  atomic publication to that listener table;
- patch 26 pins the embedded Box86 revision independently of CMake's working
  directory. The release recipe also normalises source paths and removes debug
  sections plus the path-derived GNU build-id. Two different build directories
  reproduced the exact FINALPLAY19 runtime hash above.

gptokeyb:

- upstream commit: `5b1284e1502548d476aa38e5979b0a8f48cb7b94`;
- production delta:
  `gptokeyb-patches/01-immediate-start-back-kill-chord.patch`;
- compiler, target SDL/libstdc++ identities, patch and exact binary hashes are
  pinned in `device/FINALPLAY.lock`;
- `harness/build_gptokeyb_mgs2.sh` rebuilds the helper; its GPL-2.0 source and
  notice boundary are recorded in the repository.

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
- The complete Wine boundary already contains retained patch 60's bounded
  transport recovery; patch 83 adds the stale-timeline rebase on top. Both
  source records and the exact binary hash are pinned in `device/FINALPLAY.lock`;
  rejected patch 82 records the failed wall-clock resume witness and is not
  shipped.

Game compatibility patch:

- original game EXE SHA-256:
  `29759e6f06eaea4d61bb6aef5a5ef45a936eac1e76fa0c3471cf4f231349aaa0`;
- exact temporary view SHA-256:
  `6686b3fa6484a0609fbe65be46f34cbba941b18e252db7bbb83d457153ba31d6`;
- only changed byte: file offset `0x4a294a`, `02 -> 00`;
- source-equivalent record:
  `game-patches/01-wpatch-fixed-function-fallback.patch`;
- generator: `device/patch-mgs2-wpatch-novs.sh`, whose output and live mount
  are both hash-verified before the game starts.

## What remains open

- The two independent game/read stalls remain after the pipeline/DXT work and
  must be captured separately from compiler gaps.
- New state-cache entries may still compile once when later gameplay first
  encounters them.
- Intermittent gameplay SFX loss across encounter/map transitions still
  requires a timestamp-correlated bounded capture; it is separate from the
  now-fixed post-resume sample-clock delay.
- One pre-renderer cold start fault at the same linked FluidSynth instruction
  previously seen with p36 remains unclassified. The relevant p35/p36/p37 code
  is identical and the next nine fully cold FINALPLAY20 starts plus the
  FINALPLAY21 cold production start passed, so no speculative workaround is
  shipped.
- Runtime freezes have multiple known signatures; new occurrences must be
  captured and named rather than attributed by resemblance.
- The previous status-40 exit remains unclassified because no exception frame
  was captured. FINALPLAY19 repairs a reachable ABI defect and exceeded that
  run's elapsed point, but status 40 alone does not prove causation.

## Historical production

FINALPLAY20 remains the exact `MGS2_RENDERER=fp20` pre-water-fix rollback and is
documented in
`docs/briefs/MGS2_FINALPLAY20_DMSYNTH_RESUME_PRODUCTION_2026-08-27.md`.

FINALPLAY19 remains the exact `MGS2_RENDERER=fp19` p34 rollback and is
documented in
`docs/briefs/MGS2_FINALPLAY19_INPUT_WAYLAND_PRODUCTION_2026-08-27.md`.

FINALPLAY18 remains the exact `MGS2_RENDERER=fp18` rollback and is documented in
`docs/briefs/MGS2_FINALPLAY18_WAYLAND_ABI_PRODUCTION_2026-08-26.md`.

FINALPLAY17 remains the exact `MGS2_RENDERER=fp17` rollback and is documented in
`docs/briefs/MGS2_FINALPLAY17_FREEZE_REDUCTION_PRODUCTION_2026-08-25.md`.

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

# FINALPLAY17 freeze-reduction production record

FINALPLAY17 was promoted on the RG353VS on 25 August 2026. It keeps the
FINALPLAY16 renderer route and changes only bounded first-use work:

```text
MGS2 D3D8
  -> DXVK-Sarek 1.11.1, warm validated state cache, one compiler worker
  -> WineVulkan/Wayland
  -> proprietary armhf Mali g29p1

texture worker
  -> Box86 native fused DXT5 surface-row bridge
```

The corrected symmetric device comparison reduced the sum of four controlled
load/location gaps by `1370.960 ms` (`20.1%`). The two gaps proven to contain
Vulkan pipeline work fell by `829.384 ms` (`32.3%`). This is a measured
first-use-stall result for one save route, not a global FPS claim and not a
claim that all runtime freezes are gone.

## Why this is the production set

The preceding memory-only timeline established the causal chain for the two
location gaps:

```text
state-cache job -> worker -> cache entry -> vkCreateGraphicsPipelines
                 -> main-visible draw wait -> no-PRESENT gap
```

Three single-variable gates then separated useful changes from attractive
dead ends:

- exact shader-to-pipeline pair dedupe reduced state-cache jobs `44 -> 14` and
  queue-delay maximum by `65.7%`, but did not shorten the visible gap by itself;
- one compiler worker beat Sarek's two-worker automatic choice by `25.7%` for
  the pipeline-gap pair because the proprietary four-core path otherwise
  reached three concurrent `vkCreateGraphicsPipelines` calls;
- warm cache plus one worker beat cache-off by `27.4%` for the same pair.

The dedupe remains in production because it removes exact duplicate work and
is required to reproduce the measured one-worker queue. It is not credited as
an independent freeze improvement.

The fused DXT implementation was independently verified before timing:
`47,648` surface calls, `47,433` native, `215` conservative guest fallbacks,
`54` sampled guest/native comparisons and `0` mismatches. Production Box86
selects the same conversion and fallbacks through a separate entry with no
atomic research counters on the texture worker.

## Corrected FINALPLAY16 A-B-A-B

The first attempted final comparison is excluded. Its arms named
`*-production-*` used `/proc/<pid>/exe` SHA
`83f9349c6dc26f8f769e714a5ed57c4d76f3a523161ead31f75e52ccc1da7fba`,
not FINALPLAY16 Box86 SHA `104c79bc...`. Its `15.9%` combined direction remains
secondary replication only; it is not the production-control claim.

The corrected A-B-A-B used:

- A: exact FINALPLAY16 Box86 `104c79bc...`, cache off, D3D9 memory-only PRESENT
  counter `cf67ce74...`;
- B: verified fused-DXT Box86 `bf0daac...`, warm cache
  `d04158e8...`, exact-pair dedupe, one worker, trace disabled, D3D9
  `5a24bb38...`;
- one process, correct LOAD GAME route, the same save rows `09 -> 08 -> 07`,
  fixed `1992 MHz` CPU and `800 MHz` GPU;
- the same 13,151-byte cache before and after every arm.

```text
A1 /storage/roms/ports/ablogs/dxvk-freeze-candidate-fp16-ab-a1-control-20260825
B1 /storage/roms/ports/ablogs/dxvk-freeze-candidate-fp16-ab-b1-candidate-20260825
A2 /storage/roms/ports/ablogs/dxvk-freeze-candidate-fp16-ab-a2-control-20260825
B2 /storage/roms/ports/ablogs/dxvk-freeze-candidate-fp16-ab-b2-candidate-20260825
```

| controlled gap | A1 control | B1 candidate | A2 control | B2 candidate | control mean | candidate mean | delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| first game/read load | `2669.978` | `2339.982` | `2559.956` | `2307.109` | `2614.967` | `2323.546 ms` | `-11.1%` |
| first location pipeline | `1750.040` | `950.835` | `1640.495` | `969.547` | `1695.268` | `960.191 ms` | `-43.4%` |
| second location pipeline | `840.074` | `699.318` | `907.858` | `859.999` | `873.966` | `779.659 ms` | `-10.8%` |
| both pipeline gaps | `2590.114` | `1650.153` | `2548.353` | `1829.546` | `2569.234` | `1739.850 ms` | `-32.3%` |
| loaded game/read worker | `1630.000` | `1389.849` | `1649.832` | `1389.675` | `1639.916` | `1389.762 ms` | `-15.3%` |
| controlled sum | `6890.092` | `5379.984` | `6758.141` | `5526.330` | `6824.117` | `5453.157 ms` | `-20.1%` |

All four candidate component means improved. B2's second pipeline gap
(`859.999 ms`) was `19.925 ms` slower than A1's (`840.074 ms`), so the result
is not falsely described as every individual sample winning. Both complete B
arms nevertheless beat both A arms by more than `1.2 s` in the controlled sum.

## Clean production artifacts

The production D3D9 is the exact Sarek commit
`617958fe1cf2b10e06fa751d3e40bd765dcf2cc6` plus patches 01, 02 and 08. Patch
08 makes only exact `(shader key, pipeline key)` dedupe unconditional; PRESENT
counters and pipeline timelines are absent. Two independent build directories
with `SOURCE_DATE_EPOCH=1787659200` produced the same bytes:

```text
4918b0283329702116dc64fba2e7be992a8b67ef2534ccf5af919f334c690650
d3d9_dxvk_sarek_1.11.1_mali_freeze1.dll
```

Before fixing the epoch, the two DLLs differed at exactly four bytes: PE
TimeDateStamp, CheckSum and the repeated timestamp. Code and data were
identical. Those non-deterministic hashes are not shipped.

Production Box86 is the pinned commit `0579f8b9` plus the FINALPLAY15 complete
patch and patches 17--21. Patch 21 selects a counter-free production entry for
surface mode 1. Two rebuilds with the lock-file epoch `1756000000` were
byte-identical:

```text
51dfcc130b9760970189a67edd8cd78c777c5d69c8b9ec07cfbc5657821d9be9
box86-fp21-dxvk-native-dxt-surface
```

An earlier build `38aafbee...` embedded the wall-clock build time. It passed
the clean correctness route, but was replaced before the final gate and is not
the production identity.

The updated reconstruction verifier applies the pinned complete patches plus
the explicit default-off Wine 01/02 and Box86 17--21 chains. Its final run
reported zero Wine differences and zero Box86 differences outside generated
build products. An intermediate verifier failure exposed the previously
unlisted Wine research pair; it was recorded explicitly rather than folded
into the immutable FINALPLAY15 complete patch.

`device/FINALPLAY17_DXVK_FREEZE.manifest` is the authoritative 18-row live
identity gate. The full package hashes are in
`device/FINALPLAY17_PRODUCTION.sha256`. The warm cache used for the A-B and
promotion remained 13,151 bytes and SHA
`d04158e8e15cb457bd74b97986e750883680622ea9334f292b6ec4390b49f1e8`.
It is a seed/provenance value, not a fail-closed row: DXVK may validly append a
new state when later gameplay encounters one.

## Production correctness and live identity

The final gate used the ordinary external entry, not a research wrapper:

```text
/storage/roms/ports/MGS2-Substance.sh
  -> launch-play.sh
  -> launch-play-dxvk-fp17.sh
```

On the deterministic Box86 bytes it established:

- exactly one `mgs2_sse_rg353v` process;
- `18/18` live files matching `FINALPLAY17_DXVK_FREEZE.manifest`;
- live `DXVK_STATE_CACHE=1`,
  `DXVK_CONFIG=dxvk.numCompilerThreads = 1`, no `DXVK_ALL_CORES`, and
  `MGS2_BOX86_NATIVE_DXT_SURFACE=1`;
- CPU at `1992000 kHz` during the identity witness;
- correct title, LOAD GAME selection, save rows `09 -> 08 -> 07`, YES,
  loaded 3D scene and twelve controlled walking bursts;
- visually correct final screenshots with no research HUD;
- cache SHA unchanged after the run;
- after a graceful stop: zero game instances, zero relevant bind mounts and a
  free flock.

Ignored local witness directory:

```text
logs/rg353vs/finalplay17-deterministic-normal-entry-20260825
```

```text
afcdf659c9fce441b23652b6264ba79429e777dc1800a7886e0fb8cbb737df4c  0-title.png
b2821f76dd0b55b0606c2a6cdaa4208c306025026739491950a05e5698dc5e21  6-loaded.png
868486cfb57bb1bda4808459e0d5dc45d960653f19a835990b450a85207b983d  7-walk-12.png
3053c68f1af1f6cd5cc7ff4cf222925c093af71db5768cc41557efad6b554f05  game.log
```

The later exact hashes should be regenerated from the ignored directory when
auditing; screenshots remain local unless deliberately curated as evidence.

## What remains open

FINALPLAY17 substantially reduces the measured first-use stalls but does not
eliminate them. The independent game/read pauses remain and can correlate with
MMC I/O, page faults and one-gigabyte shared-memory pressure without any
pipeline event in the interval. New, previously unseen state-cache entries can
also compile once. Dense-scene steady-state FPS and intermittent gameplay SFX
are separate problems.

## Launch and rollback

Normal launch:

```sh
/storage/roms/ports/MGS2-Substance.sh
```

One-launch rollback to exact FINALPLAY16 DXVK:

```sh
MGS2_RENDERER=dxvk16 /storage/roms/ports/MGS2-Substance.sh
```

This new selector branch was live-tested through the external entry after
promotion: the process tree named `launch-play-dxvk-fp16.sh`, all `18/18`
FINALPLAY16 identities matched, and graceful stop again left no instance,
relevant mount or held lock.

Renderer-family rollback to exact FINALPLAY15 WineD3D:

```sh
MGS2_RENDERER=wined3d /storage/roms/ports/MGS2-Substance.sh
```

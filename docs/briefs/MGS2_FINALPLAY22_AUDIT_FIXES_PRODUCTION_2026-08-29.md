# FINALPLAY22 audit fixes and production promotion

Date: 29 August 2026  
Production: FINALPLAY22  
Immediate exact rollback: FINALPLAY21 (`MGS2_RENDERER=fp21`)  
Promotion basis: owner directive after code audit and bounded RG353VS smokes

## Result

FINALPLAY22 combines the two closed findings selected for production:

```text
FINALPLAY21 renderer/input/DXVK/Box86 boundary
  + state-owned fixed-function wpatch game view d902ee43...
  + dmime_p16 curve private-state layout f23f08ed...
  + dmsynth_p38 sink lifetime/recovery 22287685...
```

The default PortMaster selector now dispatches to
`device/launch-play-dxvk-fp22.sh`. FINALPLAY21 remains a complete named route,
not a reconstruction from mixed current files. The legal game executable is
still neither stored nor overwritten: the launcher accepts only original
SHA-256 `29759e6f...`, generates only temporary SHA-256 `d902ee43...`, checks
all 58 changed bytes through the complete output hash, bind-mounts the view for
one launch and removes it after unmount.

E7 was excluded by the owner's explicit instruction. Box86 patch 28 and DXVK
patches 09/10 are not included: they have no promoted, device-tested runtime
object and are not required by these gameplay fixes.

## Exact boundary

`device/FINALPLAY22_AUDIT_FIXES.manifest` is the authoritative 21-row live
identity. Relative to FINALPLAY21, exactly four rows change:

| Live object | FINALPLAY22 |
|---|---|
| game helper | `patch-mgs2-wpatch-finalplay22.sh`, `55f1714b...` |
| temporary game view | `d902ee43...` |
| `dmime.dll` | `dmime_p16_curve_state_layout.dll`, `f23f08ed...` |
| `dmsynth.dll` | `dmsynth_p38_sink_lifetime.dll`, `22287685...` |

Every other manifest row is byte-identical to FINALPLAY21. The distributable
record is `device/FINALPLAY22_PRODUCTION.sha256`; it contains 25 files: the 21
files required for the current install plus the four objects exclusive to the
exact FINALPLAY21 rollback. It excludes the legal game image and ROCKNIX/Mali
system libraries.

Source provenance is pinned in `device/FINALPLAY.lock`:

- game patches 02, 04 and 05;
- Wine patches 84 and 85 on the retained patch-60/83 boundary;
- fixed Wine build epoch `1787976000`;
- exact output hashes for both Wine DLLs and the temporary game view.

## Evidence and accepted risks

The final visual image `d902ee43...` passed exact `21/21` identity on the
RG353VS, loaded save row 07, completed four movement bursts and four attacks,
and produced normal loaded/post-action frames. The kernel logged no new GPU
fault in that successful run. A preceding attempt did trigger a real Mali job
hard-stop, fault `0x4002` and `VK_ERROR_DEVICE_LOST`; exact FINALPLAY21 then
passed the same path and the exact candidate passed on immediate repetition.
The reset is preserved as real but non-reproduced and unattributed.

The audio route separately passed exact `21/21` identity, live hashes for
`dmime`, `dmsynth` and unchanged `dsound`, save row 07, four movement bursts
and eight attacks. A PipeWire sink-monitor WAV finalised at 23,690,924 bytes.
This proves startup and pre-resume survival, not audibility of every gameplay
SFX. RTC suspend returned at the requested epoch after 20 seconds, but the
device then failed to restore IPv4 or IPv6 networking; post-resume attacks did
not run.

The combined FINALPLAY22 static gate reconstructs the exact 58-byte transform,
reverse/reapplies Wine patches 84/85 with fuzz zero, proves the four-row-only
manifest delta, validates the default selector and checks every tracked
production byte. The Wine and Box86 trees also reconstructed from their pinned
bases with zero differences.

After a clean console reboot, `finalplay22-20260829-r1` deployed and re-hashed
all 25 distributable files. The normal external entry, with no renderer or
candidate override, then generated exact game view `d902ee43...`; the launcher
reported `21 of 21`, and an independent pass over every live manifest path
reported `checked=21 mismatches=0`. The pixel-gated route selected save row 07,
confirmed the controlled gameplay frame at gray mean `0.209`, completed four
movement bursts and four `x` attacks, and produced a normal final frame. There
was no Mali job fault or `VK_ERROR_DEVICE_LOST` during this combined run. The
kernel emitted its OOM-notifier process census without killing the game; the
route continued through all actions. TERM cleanup left zero game/Wine/Box86
processes, zero relevant bind mounts, no temporary game view and no persisted
clock-baseline file.

The immediate `MGS2_RENDERER=fp21` rollback was launched once after deployment.
It generated exact view `6686b3fa...`, matched `21 of 21` against
`FINALPLAY21_WATER_WPATCH.manifest`, and its TERM cleanup likewise left zero
relevant processes or mounts and no temporary view or baseline file.

The first deploy attempt exposed a release-tool defect: `ssh` inside the input
redirected install loop consumed the remaining checksum rows after `box86`,
while the script incorrectly printed the precomputed total of 25. The selected
production entry had not yet been replaced, and the copied Box86 was already
byte-identical, so the device remained on an intact FINALPLAY21. The packager
now uses `ssh -n`, counts actual replacements and refuses any count other than
25. The corrected run printed and verified every file before installing the
new selector last.

The individual candidates and their exact combination are now device-measured.
Promotion still accepts the delayed fixed-scene flicker comparison and
post-resume SFX gate as open risks; the successful short combined smoke is not
evidence that either long-duration observation passed.

## Launch and rollback

Normal production:

```sh
/storage/roms/ports/MGS2-Substance.sh
```

Immediate exact rollback:

```sh
MGS2_RENDERER=fp21 /storage/roms/ports/MGS2-Substance.sh
```

Older exact rollbacks remain `fp20`, `fp19`, `fp18`, `fp17`, `dxvk16` and
`wined3d`.

## Gates

```sh
./harness/test_finalplay22_production.sh
./harness/test_finalplay21_production.sh
./harness/test_audio_lifetime_candidate.sh
./harness/test_wpatch_state_ownership_candidate.sh
./harness/test_launcher_cleanup_safety.sh
./harness/test_gptokeyb_launchers.sh
```

All passed locally. Device deployment, independent live `21/21` identity and
the normal-entry combined smoke passed on 29 August 2026. The delayed flicker
comparison and post-resume gameplay-SFX observation remain open.

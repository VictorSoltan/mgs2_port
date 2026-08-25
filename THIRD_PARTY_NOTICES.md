# Third-party notices

This file describes the upstream projects from which the patch sets and some
probe/island code are derived. It is an attribution map, not legal advice.

## Wine

- Upstream: https://gitlab.winehq.org/wine/wine
- Base: Wine 11.0
- License: GNU Lesser General Public License 2.1 or later
- License text: `LICENSES/Wine-LGPL-2.1-or-later.txt`

`wine-patches/` modifies Wine. The native WineD3D island/probe sources under
`harness/island/` include functions or declarations copied from Wine and are
treated as Wine-derived material under the same license.

The complete current Wine-side reconstruction boundary is
`wine-patches/FINALPLAY15-wine-complete.patch`; numbered patches preserve the
chronology and rejected variants.

## Box86

- Upstream: https://github.com/ptitSeb/box86
- Base commit: `0579f8b9c47d87d700724f4cce559b06cbd2b0f5`
- Copyright: Sebastien Chevalier (“ptitSeb”) and contributors
- License: MIT
- License text: `LICENSES/Box86-MIT.txt`

`box86-patches/` contains modifications to Box86. FINALPLAY17 applies the
complete FINALPLAY15 delta, the native Wayland/Vulkan bridge and the verified
fused DXT surface conversion with a counter-free production entry.

## DXVK / DXVK-Sarek

- Original upstream: https://github.com/doitsujin/dxvk
- Port source: https://github.com/zeyadadev/DXVK-Sarek
- Port base: tag `v1.11.1-mali-fix`, commit
  `617958fe1cf2b10e06fa751d3e40bd765dcf2cc6`
- License: zlib/libpng
- License text: `LICENSES/DXVK-Zlib.txt`

`dxvk-patches/` contains altered DXVK source patches. The files are plainly
identified as port-specific compatibility changes; they are not represented as
upstream DXVK.

## Components not distributed

ROCKNIX, the proprietary Arm Mali driver, Vulkan loader, the user's Wine prefix
and Metal Gear Solid 2 are referenced by manifests and documentation but are not
included. Their hashes describe the tested environment and do not imply a right
to redistribute those components.

## Diagnostic screenshots

`docs/evidence/` may contain small screenshots captured from Metal Gear Solid
2 solely to document rendering correctness. They are not covered by the source
licenses in this repository and are not offered for reuse. Game content and
trademarks remain the property of their respective owners.

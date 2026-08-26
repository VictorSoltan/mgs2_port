# FINALPLAY18 Wayland-listener ABI production — 2026-08-26

## Decision

Box86 patches 23+24 are promoted. The normal PortMaster entry now selects
FINALPLAY18. It is FINALPLAY17 with exactly one runtime byte change:

```text
/usr/bin/box86
  FINALPLAY17  51dfcc130b9760970189a67edd8cd78c777c5d69c8b9ec07cfbc5657821d9be9
  FINALPLAY18  d6cafba667d16f6227c0ffd5437e7ac52253dd46624c2edfcbbd36ca3843188b
```

The DXVK D3D8/D3D9 pair, Wine modules, audio DLLs, prefix, Mali driver, warm
cache policy and one-worker configuration are unchanged. This promotion makes
no FPS claim.

The production artifact is named `box86-fp24-wayland-atomic-production`.
`device/FINALPLAY18_WAYLAND_ABI.manifest` pins all 18 live dependencies and
differs from the FINALPLAY17 manifest only at `/usr/bin/box86`.

## Defects fixed

The native armhf libwayland route could install guest x86 callback tables
directly for four Wine 11 listener classes. It also copied two callback
signatures with too many arguments and published callback slots without an
explicit cross-thread ordering relation. A dispatched event could therefore
jump to an x86 address as though it were ARM code.

Patch 23 bridges the missing listener classes, corrects the two signatures,
uses public proxy class lookup and fails closed for unknown classes or exhausted
slots. Patch 24 publishes the affected callback references with release stores
and consumes them with acquire loads. The full implementation audit is in
`MGS2_PATCH_AUDIT_AND_WAYLAND_ABI_2026-08-26.md`.

## Device gates

The exact p24 hash first passed the purpose-built i386-to-native-armhf Wayland
gate on the RG353VS. Normal callback, clipboard source/offer/selection,
xdg-surface, keyboard and bounded slot-overflow cases all returned zero. The
only slot-exhaustion warnings belonged to the synthetic overflow arm.

The final production gate then used one exact process and the correct
`LOAD GAME` route through save rows 09, 08 and 07. It produced a lit 3D scene,
four walking bursts and four actions. The process stayed the same for more than
40 minutes. Twenty-four consecutive external one-minute records all had:

- exactly one game instance;
- increasing process CPU ticks;
- a new screenshot hash;
- zero page-fault, segfault, unknown-listener, slot-exhaustion, assertion or
  fatal match.

The SSH observation was interrupted after record 24, but the game process did
not restart or exit and its elapsed time reached 40:40. This is a completed
duration gate, not a claim of 40 consecutive monitor records.

Three Sway workspace focus-away/back cycles preserved the same process and a
valid frame. A real `deep` suspend was armed with an RTC wake and lasted about
26 seconds. Kernel records contain `PM: suspend entry (deep)` and
`PM: suspend exit`. After resume:

```text
PID                         66191 before and after
process ticks               614369 -> 623290
pre/post screenshot SHA     different
post screenshot bytes       198072
Wayland/crash fault matches 0
```

The first loaded-game suspend emitted one kernel regulator warning,
`unbalanced disables for vdd_gpu`, from the out-of-tree proprietary
`mali_kbase` suspend callback. It did not abort suspend or resume, and no later
GPU fault/reset followed. Three bounded controls were added rather than hiding
the warning: no-game deep suspend, exact FINALPLAY17 p21 with an active DXVK
process, and a second FINALPLAY18 active-DXVK suspend. All three resumed; none
repeated that regulator warning, and both game controls retained their PID and
valid post-resume image. The p21 control printed a separate one-shot GPU thermal
read `-11`. These are intermittent ROCKNIX/proprietary-driver power-management
warnings, not evidence of a p24-only regression or of a game exit. The port does
not install a global sleep hook or patch the proprietary kernel module.

The research run ended by explicit SIGTERM with status 143. Its EXIT trap then
left zero game/helper processes, zero MGS2 bind mounts, an available launcher
lock and restored `ondemand`/`simple_ondemand` CPU/GPU governors.

After deployment, the external normal entry repeated the visual title/menu/save
route, loaded the lit scene, walked and performed four actions. It reported
`18 of 18 runtime files match FINALPLAY18_WAYLAND_ABI.manifest`; an independent
live read matched all 18 hashes and `/usr/bin/box86` matched the production p24
file byte for byte. The process environment named `finalplay18` and contained no
research route.

## Negative results and boundaries

The bounded `display_lock` history remained enabled throughout the long p24 run
and recorded zero calls, including across focus transitions and suspend/resume.
The proved self-owner occurrence belongs to an older WineD3D/native-island
research route. There is no captured recursive chain in the current DXVK route,
so no speculative recursive-mutex or forced-unlock change is shipped. The
historical capture remains actionable if the WineD3D rollback reproduces it.

DXVK prints one startup warning for render state 161,
`D3DRS_MULTISAMPLEANTIALIAS`. The same one-shot warning was present in the first
successful DXVK gameplay run. It did not repeat or accompany a device loss,
fault or observed picture defect in the FINALPLAY18 gates. It is retained as a
known capability warning; changing multisample semantics without a failing
scene and supported Vulkan path is outside this crash fix.

This promotion closes the known reachable native-Wayland callback crash path.
It cannot prove that arbitrary future game, kernel, driver or storage faults do
not exist. New exits must still be classified from the bounded exit record,
Wine output and kernel log.

## Rollback

One-launch rollback to exact FINALPLAY17 p21:

```sh
MGS2_RENDERER=fp17 /storage/roms/ports/MGS2-Substance.sh
```

Older renderer rollbacks remain:

```sh
MGS2_RENDERER=dxvk16 /storage/roms/ports/MGS2-Substance.sh
MGS2_RENDERER=wined3d /storage/roms/ports/MGS2-Substance.sh
```

The console also retains the pre-promotion selector and FINALPLAY17 engine with
suffix `.bak-20260826-finalplay18`. Those files are recovery copies, not the
source of truth; Git plus `device/FINALPLAY18_PRODUCTION.sha256` is authoritative.

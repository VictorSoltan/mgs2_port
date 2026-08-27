# FINALPLAY19 input and Wayland production — 2026-08-27

## Decision

Box86 patches 25+26 and the immediate-edge gptokeyb route are promoted together
as FINALPLAY19. The normal PortMaster entry selects the exact 19-row bundle.
FINALPLAY18 remains an immediate byte-exact rollback.

FINALPLAY19 changes two runtime files from FINALPLAY18:

```text
/usr/bin/box86
  FINALPLAY18  d6cafba667d16f6227c0ffd5437e7ac52253dd46624c2edfcbbd36ca3843188b
  FINALPLAY19  b7e9530f6039335a37ee54d8d3a2974e25b71500b96b95a9dd899f1e20374d51

/storage/roms/ports/MGS2-Substance/gptokeyb-mgs2-immediate
  FINALPLAY19  49c782dad9da50cb0f5bb9e37821104e5089563feb24c7b0303117b75196b43a
```

The DXVK D3D8/D3D9 pair, Wine modules, audio DLLs, system Wine prefix, Mali
driver, warm cache and one-worker policy are unchanged. This promotion makes no
FPS claim.

## Defects fixed

Upstream gptokeyb's kill mode deferred ordinary Start and Back/Select mappings
until button release while deciding whether they formed the exit chord. Wine
also consumed the physical `retrogame_joypad` through `winebus.sys`. A Start
press therefore reached the game first as a raw controller action and only
later as translated Tab. This reproduced the brief first-person view before the
menu and the delayed Start/Select response.

The default-off `-immediate-start-back` patch emits those two ordinary mappings
on their real down/up edges while retaining the same-device chord state. The
closed FINALPLAY19 route also appends `winebus.sys=d`; host SDL still supplies
the controller to gptokeyb, but Wine cannot receive the duplicate raw action.

An exact generated-header audit also found a reachable error in the p24 native
Wayland wrapper. Wine 11 declares
`zwp_text_input_v3_listener.delete_surrounding_text` as `(data, object, before,
after)`, while Box86 used an extra pointer and the guest format `pppuu`. Patch 25
changes the bridge to the exact `ppuu` ABI and uses release/acquire publication
for the text-input callback table.

Five other differences reported by the audit are explicitly version-gated:
Wine binds `wl_surface` at version 4, `wl_seat` at version 5 and the wlr primary
selection manager at version 1, below the versions that can dispatch those
events. `harness/wayland/audit_listener_abi.py` fails p24 on the reachable
text-input mismatch and passes p25 with exactly those five allowlisted entries.

## Reproducibility and static gates

The first p25 device candidate passed the runtime gates below, but its
RelWithDebInfo ELF retained absolute source/build paths and CMake's working
directory controlled the embedded git revision. Patch 26 makes that revision a
pinned input. The release recipe maps Box86 and island source paths to stable
names and strips debug sections plus the path-derived GNU build-id. Two
different build directories, with `SOURCE_DATE_EPOCH=1756000000`, then produced
the exact FINALPLAY19 runtime hash above. The patched AArch64 gptokeyb helper
was also rebuilt repeatedly to its exact hash. Upstream commits, patches,
toolchain inputs and artifact hashes are pinned in `device/FINALPLAY.lock`.

The complete Wine and Box86 trees reconstructed from the pinned bases plus all
listed patches with zero differences outside declared build products. The
static production gate requires the closed FINALPLAY19 selector, exact p26 and
helper hashes, 19 manifest rows, all three source patch hashes and exact tracked
launcher/config bytes. It also proves that the other 17 manifest rows are
byte-identical to FINALPLAY18.

## Device gates

The exact final p26 binary repeated the purpose-built i386-to-native-armhf
Wayland gate on the RG353VS. Observer, clipboard source/receive/source2, window,
keyboard and xdg-surface cases returned zero. The bounded eleventh-slot
overflow failed closed as designed; `normal_bad_matches=0` and
`targeted_gate=PASS`.

The closed candidate then used the correct visual route: title, main menu,
`LOAD GAME`, save rows 09, 08 and 07, confirmation, then the lit gameplay scene.
It completed six initial walking bursts and two actions. Live identity
reported `19 of 19`; `/usr/bin/box86` matched the p26 candidate byte for byte,
the process environment named the closed route, and `/proc/<pid>/maps` contained
no `winebus` module.

An RG353VS-shaped uinput device used the console's exact SDL mapping and button
codes. In the live final p26 process, Start-down preceded emitted Tab-down by
`0.883 ms`; Start opened the map menu. Select-down preceded Enter-down by
`0.495 ms`; Select opened Codec. Because Wine had no `winebus`, those
physical-shaped events had no earlier raw joystick path.

The preceding exact p25 ABI candidate kept one PID in loaded gameplay for
37:58, beyond the prior FINALPLAY18 status-40 exit at roughly 16.7 minutes. A
bounded activity helper sent 20 walking bursts. Its accepted Wine log used
`-all,trace+seh`, stayed at 6,576 bytes and contained only two handled
cold-start `RPC_S_SERVER_UNAVAILABLE` exceptions. It recorded no later page
fault, stack fault or unhandled exception. An external one-second pressure
reader buffered 1,800 samples and wrote once at exit. The final p26 artifact,
whose semantic source change is only the revision-input fix and whose remaining
changes are source-path normalisation/debug post-processing, repeated the
callback, loaded-game, visual/input and bounded five-minute pressure/activity
gates. Its same PID reached 10:57, the SEH log stayed at 4,509 bytes and all 300
one-second pressure samples completed. No kernel OOM kill, Mali reset, Vulkan
device loss or sustained memory PSI accompanied either run.

A synthetic same-device Start+Select chord then terminated the game directly
with SIGTERM/status 143, without the ROCKNIX confirmation dialog. Teardown left
zero game/helper processes, zero MGS2 bind mounts, an available launcher lock
and restored `ondemand`/`simple_ondemand` CPU/GPU governors.

After deployment, the normal external entry repeated the visual title/menu/save
route and loaded the lit gameplay scene. It reported `19 of 19 runtime files
match FINALPLAY19_INPUT_WAYLAND.manifest`; an independent read matched all 19
hashes and `/usr/bin/box86` matched the production p26 file byte for byte. The
process environment named `finalplay19`, contained `winebus.sys=d` and no
research route. A final same-device chord repeated direct exit and complete
cleanup; `/tmp/mgs2-play-exit.log` recorded `launcher=finalplay19`, the live game
PID and `status=143`.

## Negative results and boundaries

The earlier FINALPLAY18 exit ended with Unix status 40, no core and no captured
exception frame. Wine may return the low byte of an NTSTATUS, making 40
compatible with `STATUS_BAD_STACK (0xc0000028)`, but the application may also
return 40 itself. Patch 25 fixes an independently proved reachable ABI defect
and the exact candidate exceeded the earlier exit point without recurrence;
that does not prove the old exit traversed this callback. Future exits still
need a bounded exception or reproducible path before they are attributed.

The Mali driver emits a short OOM-notifier allocation listing during cold
startup. It emitted no kernel OOM kill and the game continued well beyond that
burst. This is not evidence that the kernel terminated the prior process.

DXVK retains its one-shot startup warning for render state 161. It is unchanged
from earlier successful production runs and did not repeat or accompany a
picture defect, device loss or exit in this gate. No speculative Direct3D state
change is shipped.

Production performs no thermal polling and installs no automatic
temperature-triggered kill. The pressure reader and activity injection above
were external test-only processes and are not reachable from the PortMaster
entry.

## Rollback

Immediate one-launch rollback to exact FINALPLAY18 p24 and legacy input:

```sh
MGS2_RENDERER=fp18 /storage/roms/ports/MGS2-Substance.sh
```

Older fixed rollbacks remain:

```sh
MGS2_RENDERER=fp17 /storage/roms/ports/MGS2-Substance.sh
MGS2_RENDERER=dxvk16 /storage/roms/ports/MGS2-Substance.sh
MGS2_RENDERER=wined3d /storage/roms/ports/MGS2-Substance.sh
```

Git, `device/FINALPLAY.lock`, `device/FINALPLAY19_INPUT_WAYLAND.manifest` and
`device/FINALPLAY19_PRODUCTION.sha256` are authoritative. Device-side backup
files are recovery aids, not provenance.

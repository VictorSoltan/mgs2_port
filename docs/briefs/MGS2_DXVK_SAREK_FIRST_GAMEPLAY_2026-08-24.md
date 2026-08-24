# MGS2 DXVK-Sarek: первый правильный gameplay на RG353VS — 2026-08-24

## Результат

Изолированный MGS2 renderer arm впервые дошёл на устройстве до правильного
живого кадра:

```text
mgs2_sse_rg353vs_port.exe (D3D8)
  -> DXVK-Sarek x86 d3d8.dll
  -> patched DXVK-Sarek x86 d3d9.dll
  -> Wine Vulkan/Wayland
  -> /usr/lib32/libmali.so.1.10.0, Mali-G52 g29p1
  -> sway, 640x480
```

Пройдены cold boot, `DATA LOAD`, `MISSION FAILED -> CONTINUE` и вход в живую
сцену Strut A Pump Room. В gameplay видны персонаж, охранник, освещение,
геометрия, HUD/радар и субтитры; ввод `CONTINUE` и движение дошли до игры.
Это закрывает риск «живой PRESENT, но пустая/чёрная картинка», который уже
давал ложные 58--60 fps на entry 37.

**FPS gain пока не заявляется.** HUD показал 59.0 в загрузочном меню, 35.7 и
28.5/36.7 на экране смерти и 42.6 в одном коротком gameplay-моменте. Это разные
фазы, не frame windows и не A/B. Они являются только надписями на correctness
screenshots.

На момент этого первого witness production FINALPLAY15 не был изменён. Позже в
тот же день владелец явно разрешил promotion по игровой оценке; точная запись
FINALPLAY16 находится в `MGS2_FINALPLAY16_DXVK_PRODUCTION_2026-08-24.md`.

## Точный research arm

Source:

```text
DXVK-Sarek tag       v1.11.1-mali-fix
commit               617958fe1cf2b10e06fa751d3e40bd765dcf2cc6
Mali patch SHA-256   43cd0cc1790128a2674d8fda96d324bc86e86d3421d1217bafc754d78f69a77a
D3D8 WSI patch       8131048ac81e93911c678137bd44ef864c5fd21e0185ed4078a4fc62d015e4df
```

Selected binaries:

```text
22e519d266b62bfa54d1d1f81e6314aab7b75890b342908f24d2b454e4af3baa  d3d8_dxvk_sarek_1.11.1_mali_wsiinit3.dll
cf67ce743ebe4c4e0ce909811193b3a90b234d74feec4649d018c9b956fe6b92  d3d9_dxvk_sarek_1.11.1_mali_count1.dll
d0a6177c5ccfe09fdfdbc660c5db22c4a2fe99d0edfeecde1bf6e0b2979889ea  box86_dxvk_wayland_fix1
```

The D3D8 DLL has no static `d3d9.dll` import. It imports
`LoadLibraryW`/`GetProcAddress`, plus `CreateWindowExW`/`DestroyWindow`. The
matched D3D9 DLL keeps the DMC3-proven Mali fixes, including
`nullDescriptor=0` on vendor `0x13b5` and the `shaderClipDistance=0` path.

The selected measurement D3D9 adds patch 03: one 32-bit counter increment per
`Present`, exported at RVA `0x30f040`. `harness/dxvk_present_count.py` samples
it read-only through `/proc/<pid>/mem`; the render thread never formats or
writes a log line. The uninstrumented `mali_nullfix1` binary is retained as the
correctness control.

The arm uses a separate 32-bit prefix:

```text
/storage/roms/ports/MGS2-Substance/wineprefix11-x86-dxvk-test
source: /storage/roms/ports/Devil-May-Cry-3/wineprefix11-x86-test
copied system.reg SHA-256:
3847b991e3a1c6d7a7dbc563bd857361b04f341b6dd7246f8965b0fe28e5afe2
```

It does not modify the production `wineprefix64`.

## Почему понадобился ещё один D3D8 patch

MGS2 imports D3D8 before creating its own window. Unmodified DXVK D3D8 also
imports D3D9 statically, so D3D9 can construct the Vulkan instance while Wine's
Wayland user driver is still the null driver.

`dxvk-patches/02-d3d8-wine-user-driver-init.patch` makes two cold-path changes:

1. creates and destroys one hidden Wine window before constructing DXVK;
2. loads D3D9 lazily with `LoadLibraryW/GetProcAddress`, after that driver init.

Nothing here runs per draw or per frame. The patch is an init-order correction,
not a performance optimisation.

## Отрицательные результаты, которые не повторять

### Custom FINALPLAY OpenGL modules cannot host this Vulkan arm

The first arm retained `win32u_glfuncs3.so`, `opengl32_finalplay_sso.so` and
`wined3d_fp15.dll`. Wine then reported that Vulkan support / `VK_KHR_surface`
was unavailable. DXVK must leave those OpenGL-specific modules unmounted and
use the matching ROCKNIX Vulkan-capable system Wine modules.

### MGS2's app-local D3D8 wins module resolution

MGS2 contains:

```text
ab6bf7a9a9f4b3e66a75ca038d8d10289c88acbfe8d52c3b5a8a9a259cb26cd5
/storage/roms/ports/MGS2-Substance/game/bin/d3d8.dll
```

Mounting research D3D8 only over prefix/system D3D8 therefore did not select
it. The launcher now bind-mounts the selected DLL over this exact app-local
target and verifies it with `cmp`.

### WoW64 remained a loader failure

The 64-bit-loader/32-bit-game path repeatedly stopped at:

```text
get_builtin_unix_funcs: Cannot dlopen("/usr/lib/wine/i386-unix/winewayland.so")
```

It reproduced with the custom and system WineWayland Unix modules, matching
system `user32`/`win32u`, DMABUF off, explicit Box86 emulation and a bounded
desktop prewarm. This is not a renderer-performance result.

The successful route is the DMC3-proven direct 32-bit loader:

```text
box86 /usr/lib/wine/i386-unix/wine mgs2_sse_rg353vs_port.exe
WINEARCH=win32
```

For MGS2, `direct32` is now a proven DXVK boot enabler. It is still not a
measured FPS optimisation.

## Доказательства первого успешного запуска

The retained log is
`docs/evidence/MGS2_DXVK_DIRECT32_FIRST_BOOT_2026-08-24.log`, SHA-256:

```text
6272f4fb7dbf6e4ce527e43e03044a67075feebbcc22aea308080bfb91ff226f
```

It records:

```text
Enabled instance extensions: VK_KHR_surface, VK_KHR_win32_surface
device:                      Mali-G52
driver:                      29.1.0 / g29p1-12eac0
Vulkan:                      1.3.303
swapchain:                   640x480, three images
present:                     MAILBOX first, then FIFO
nullDescriptor:              0
shaderClipDistance:          0
```

The only DXVK warning in the run was:

```text
D3D9DeviceEx::SetRenderState: Unhandled render state 161
```

It did not prevent the lit gameplay frame, but effects/cutscenes still have to
be checked before declaring full compatibility.

Live `/proc/<game>/maps` contained the exact selected D3D8/D3D9 plus:

```text
/usr/lib/wine/i386-unix/winewayland.so
/usr/lib/wine/i386-unix/winevulkan.so
/usr/lib/wine/i386-windows/winewayland.drv
/usr/lib/wine/i386-windows/winevulkan.dll
/usr/lib32/libmali.so.1.10.0
/usr/lib32/libvulkan.so.1.4.347
```

Correctness images retained in `docs/evidence/`:

| File | What it proves | What its HUD does not prove |
|---|---|---|
| `MGS2_DXVK_DIRECT32_FIRST_BOOT_2026-08-24.png` | lit `DATA LOAD`, correct text/border/save | 59.0 is menu FPS |
| `MGS2_DXVK_DIRECT32_GAMEPLAY_PROBE_2026-08-24.png` | live 3D preview on `MISSION FAILED` | 35.7 is death-screen FPS |
| `MGS2_DXVK_DIRECT32_CONTINUE_2026-08-24.png` | lit gameplay, HUD, actor/enemy, text, input accepted | 42.6 is one HUD observation |
| `MGS2_DXVK_DIRECT32_GAMEPLAY_MOVE_A/B_2026-08-24.png` | state continued changing after input | both landed back on death screen |

The last two images are not a gameplay performance pair: Raiden died before
they were captured.

## Correctness boundary на момент первого witness

Passed in this first run:

- native Vulkan device/swapchain creation on proprietary Mali;
- lit menu, live 3D preview and lit gameplay instead of black PRESENT;
- HUD, radar, text, geometry and lighting at 640x480;
- synthetic controller-equivalent input reaches the game;
- clean process/mount teardown.

На момент записи не были пройдены:

- a bounded run of changing gameplay witnesses rather than three screenshots;
- codec/cutscene, map transition, fog/alpha and weapon effects;
- music, menu click and gameplay SFX as three separate observations;
- save write/read;
- 20-minute gameplay soak and memory/pipeline stability.

## Rollback proof первого research run

The research launchers are:

```text
device/launch-dxvk-sarek.sh
device/launch-dxvk-play.sh
device/DXVK_SAREK_RESEARCH.manifest
```

They use verified bind mounts and an EXIT/TERM cleanup. After the test:

```text
MGS2/DXVK/Wine processes      none
mounts below MGS2 game dir   none
game/bin/d3d8.dll            ab6bf7a9... (original restored)
production launch-play.sh    1d95c264d84c5173baac72b312724f3dd1415c0139e294acd1c58cbc70cbe329
```

The last hash equals the pre-test production hash. Это доказывает clean rollback
первого research run; текущий production позже стал FINALPLAY16.

## Следующий измерительный шаг после promotion

Do not rerun the old WineD3D optimisation ladder. First select the retained
production log/screenshot for this exact Pump Room combat state. Then measure
only the missing DXVK arm with a memory-only or compositor-external frame
counter; do not use one-second HUD screenshots as samples.

If exact scene identity with a retained production window cannot be proved,
the honest output is `no comparable FPS result`, not a comparison against the
nearby 9--15, 28--40 or 60 fps bands already present in this room.

Владелец позже осознанно отменил требование ждать этого gate перед promotion.
Измерение по-прежнему нужно, но теперь оно проверяет уже развёрнутый production,
а не блокирует его. Текущий state:

```text
DXVK feasibility:       YES, proven on device
DXVK correct gameplay:  first lit/input witness passed
DXVK performance gain:  UNKNOWN, not measured
production promotion:   YES, owner judgement; not an FPS claim
```

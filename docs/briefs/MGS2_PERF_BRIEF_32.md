# MGS2 RG353VS — бриф #32: перенос на Hangover, этапы H0–H1 сделаны, H2 упёрся в EGL-конфиги

Дата: 7 августа 2026. Продолжение #31, где принято решение сменить основной трек
на Hangover. Здесь — что реально установлено и работает, чем это подтверждено, и
единственная вещь, на которой всё встало.

Всё в этом брифе **проверено на устройстве**. Где вывод предположительный, это
сказано явно.

## Итог одной строкой

H0 и H1 пройдены: нативный ARM64 Wine работает, WowBox64 исполняет i386-код, окно
игры создаётся нативным `winewayland.drv`. H2 (первый кадр D3D8) блокирован ровно
одной причиной: **upstream `winewayland` перечисляет EGL-конфиги под desktop
OpenGL, а Mali даёт только GLES, поэтому wined3d получает ноль пиксельных
форматов**. Это та самая стена, ради которой существуют три ваших unix-патча.

Главное следствие для проекта: **ABI-стены больше нет.** В процессе игры нативно
загружены `libmali`, `libEGL` и `libwayland-egl` — то, что в старом стеке падало в
`wglMakeCurrent` с 0xc0000005.

## Что установлено

```text
/storage/hangover                       1.8 ГБ после обрезки
  bin/wine                              нативный aarch64 PIE, relocatable
                                        сообщает "wine-11.0 (Hangover)"
  lib/wine/aarch64-unix/winewayland.so   есть
  lib/wine/aarch64-windows/wowbox64.dll  есть
  lib/wine/i386-windows/                 32-битные PE Wine
  wined3d_release3.dll                   НАШ i386 PE, отложен для H2
  d3d8_mgs2fast1.dll                     НАШ i386 PE, отложен для H2
  backup-stock/                          stock wined3d.dll и d3d8.dll
```

Выбор сборки: **debian13_trixie**. ROCKNIX несёт glibc 2.41, у trixie тоже 2.41 —
точное совпадение. `ubuntu2510` это уже 2.42 и потребовал бы символов, которых на
системе нет; более старые сборки запустились бы, но смысла брать их нет.

Hangover 11.0, а не 11.9, — сознательно: наш Wine тоже 11.0, значит перенос
патчей идёт минимальным diff'ом. 11.9 (Box64 0.4.2) — второй эксперимент, после
появления baseline.

Preflight, снятый на консоли:

```text
uname -m     aarch64
PAGESIZE     4096        <- предупреждение форка Hangover про не-4 KiB не про нас
glibc        2.41
kernel       7.0.2
box64        0.4.2 (в системе; в Hangover свой WowBox64 v0.4.0)
```

## H0: изоляция от production

`device/launch-hangover.sh`. Ни одного bind-mount поверх `/usr/lib/wine`, свой
prefix, свой лог. Удаление скрипта возвращает всё как было.

```text
WINEPREFIX   $GAMEDIR/wineprefix-hangover     (НЕ wineprefix64: ARM64 WoW64 Wine
                                              перезаписал бы его без пути назад)
WINELOADER   /storage/hangover/bin/wine
WINEDLLPATH  /storage/hangover/lib/wine
D:           -> /storage    (иначе игра не сохраняется, см. launch.sh:63)
рабочий кат. $GAMEDIR/game/bin   (там лежит exe, как и в launch.sh:556)
```

Проверено после всех экспериментов: десять production-модулей, `launch.sh` и
`wineprefix64` (598 МБ) целы. Отсутствие bind-mount'ов в `/proc/mounts` при
незапущенной игре — норма, они живут только на время работы.

## H1: окно создаётся. Подтверждено объективно

prefix WoW64 собрался (второй раз, с первого не хватило места — см. ниже):

```text
drive_c/windows/system32   824 файла
drive_c/windows/syswow64   862 файла
system32/wow64.dll         есть
system32/wowbox64.dll      есть
syswow64/{ntdll,kernel32,user32,d3d8}.dll  есть
```

Запуск игры, из лога:

```text
[BOX64] WowBox64 arm64 v0.4.0 (Hangover 11.0) with Dynarec
[BOX64] Dynarec for ARM64, with extension: ASIMD AES CRC32 PMULL ATOMICS SHA1 SHA2
arm_release_ver: g29p1-12eac0, rk_so_ver: 5      <- баннер нативного Mali
```

Окно — не по догадке, а из самого компоновщика (`swaymsg -t get_tree`):

```text
"name":   "METAL GEAR SOLID 2:SUBSTANCE"
"app_id": "mgs2_sse_rg353vs_port.exe"
```

Нативные библиотеки, загруженные в процесс игры:

```text
libmali.so.1.10.0      libEGL.so.1.1.0
libwayland-client      libwayland-egl.so.1.23.1     <- путь zero-copy
winewayland.drv        winewayland.so
```

`libwayland-egl` нативно в процессе — это прямая отмена тупика из #29
(«zero-copy через wl_egl_window: стена ABI, x86-libwayland против нативного Mali
EGL, падает в wglMakeCurrent»). Стена была в ABI, а не в драйвере.

Оговорка: gptokeyb `launch-hangover.sh` не запускает, поэтому ввода в игре нет и
дальше титульного экрана она сама не уйдёт. Для H2 это надо добавить.

## H2: во что упёрлись, с точностью до причины

На экране владелец видит `Failed creating Direct3d8 object`. В логе:

```text
err:d3d:wined3d_caps_gl_ctx_create Failed to find a suitable pixel format.
err:d3d:wined3d_adapter_gl_init    Failed to get a GL context for adapter
```

Диагностика доведена до корня. EGL сам по себе **работает**:

```text
Initialized EGL library
Initialized EGL display, version 1.5
EGL client extensions:  EGL_KHR_platform_wayland  EGL_EXT_platform_wayland
                        EGL_KHR_platform_gbm  EGL_EXT_platform_base
EGL display extensions: EGL_KHR_image  EGL_KHR_image_base  EGL_KHR_fence_sync
                        EGL_EXT_image_dma_buf_import
                        EGL_EXT_image_dma_buf_import_modifiers
                        EGL_WL_bind_wayland_display  EGL_KHR_no_config_context
                        EGL_KHR_create_context  EGL_KHR_surfaceless_context
                        EGL_KHR_swap_buffers_with_damage
```

А пиксельных форматов wined3d предложено **ноль**. Причина: upstream
`winewayland` перечисляет EGL-конфиги, требуя desktop `EGL_OPENGL_BIT`, тогда как
Mali публикует только `EGL_OPENGL_ES2_BIT`/`ES3_BIT`. Подходящих конфигов не
находится → форматов ноль → контекста нет → объект D3D8 не создаётся.

Заодно этот же список расширений говорит, что нативный zero-copy позже реален:
`EGL_EXT_image_dma_buf_import` и `EGL_KHR_image` на месте.

### Проверенная и закрытая гипотеза: переиспользовать наши i386 PE

Из таблицы в #31: «`wined3d_release3.dll` — попробовать существующий i386 PE».
Проверено напрямую: обе наши DLL подменены в `lib/wine/i386-windows/`, ABI
совпадает (обе стороны Wine 11.0). **Ошибка не изменилась ни на строку.**

Причина понятна и делает результат окончательным для этого шага: список пиксельных
форматов формируется на **unix-стороне**, а она здесь stock ARM64. Наши
`winewayland_stall1.so`, `win32u_glfuncs3.so`, `opengl32_glesbinary1.so` — i386
ELF и в AArch64 Wine неприменимы в принципе.

Stock DLL возвращены на место, наши лежат рядом под своими именами, подмена — одна
команда.

### Что нужно для H2. ПОПРАВКА к первой редакции этого раздела

Первая редакция говорила «фильтр в `winewayland.drv`, перенести три патча».
Проверено по исходникам и на устройстве — **оба утверждения неверны**.

**Фильтр живёт в `win32u/opengl.c`, не в драйвере.** Wine 11.0, дословно:

```text
win32u/opengl.c:478   if (render & EGL_OPENGL_BIT) configs[j++] = configs[i];
win32u/opengl.c:777   if (attribs[1] & WGL_CONTEXT_ES2_PROFILE_BIT_EXT)
win32u/opengl.c:779       ERR( "OpenGL ES contexts are not supported\n" );
win32u/opengl.c:811   funcs->p_eglBindAPI( EGL_OPENGL_API );
win32u/opengl.c:1107  funcs->p_eglBindAPI( EGL_OPENGL_API );
```

**Stock `winewayland.drv` уже содержит нативный презентер**, тоже дословно:

```text
winewayland.drv/opengl.c:119  wl_egl_window_create( client->wl_surface, ... )
                        :120  eglCreateWindowSurface( egl->display, config, ... )
                        :160  eglSwapBuffers( egl->display, gl->base.surface )
```

**И главное: почему старый стек работает, хотя этот фильтр в нём не изменён.**
Наш production `win32u/opengl.c` несёт фильтр и отказ от ES-контекста в
неизменном виде, а `winewayland.drv` конфиги сам не выбирает вообще. Замер на
устройстве, production с `trace+wgl`:

```text
egldrv_init_pixel_formats: pixel_formats 34
config 0 id 1 type 405 visual 0 native 0 render 45 rgba 8,8,8,8 depth 0 stencil 0
```

`render 45` = `0b101101` = 1 + 4 + **8** + 32, где **8 это `EGL_OPENGL_BIT`**.
32-битный EGL, который подгружает Box86, **объявляет desktop OpenGL**, поэтому
неизменённый фильтр Wine находит 34 конфига и создаёт «desktop GL» контекст,
который в действительности GLES. Нативный 64-битный Mali этого бита не объявляет,
отсюда ноль конфигов под Hangover.

Отсюда состав H2 меняется. Все три наших патча лечат **последствия** того, что
контекст называется GL, а ведёт себя как GLES, и ни один не выбирает конфиг:

```text
06-opengl32   69 строк   разбор "OpenGL ES 3.2" (stock делает *major = atoi(ptr)
                         на unix_wgl.c:549 и получает 0), плюс OES-написания
                         glGetProgramBinary/glProgramBinary
08-win32u    271 строка  gles_depth_range/gles_clear_depth (double -> float),
                         pre-resolve список GL entry points, потому что
                         wglGetProcAddress здесь возвращает NULL с первого раза;
                         плюс PeekMessage yield в message.c
10-winewayland 895 строк ЦЕЛИКОМ presenter на pbuffer/readback/SHM/PBO:
                         mgs_present_shm, mgs_copy_to_shm, mgs_acquire_shm_buffer,
                         mgs_ensure_pbos, mgs_async_ensure, mgs_report_stats.
                         Категорий "EGL-конфиги" и "wl_egl_window" в нём НЕТ
```

Значит:

```text
H2 требует НОВОГО кода в win32u/opengl.c, а не переноса:
    принимать EGL_OPENGL_ES2_BIT / ES3_BIT, а не только EGL_OPENGL_BIT
    не отвергать WGL_CONTEXT_ES2_PROFILE_BIT_EXT
    привязывать EGL_OPENGL_ES_API вместо EGL_OPENGL_API
затем порт 08 и 06 — они закрывают всё, что ПОСЛЕ появления контекста
patch 10 НЕ переносить: это pbuffer+readback, существовавший только потому, что
    нативный wl_egl_window был недостижим. Перенос отнял бы главный выигрыш
```

wined3d и d3d8 остаются нашими i386 PE — подмена проверена, ABI совпадает. Это
по-прежнему предположение, проверяемое сразу после появления контекста.

Нужен кросс-тулчейн aarch64 и sysroot с заголовками wayland/EGL под ROCKNIX,
поверх дерева `AndreRH/wine` на теге `hangover-11.0`.

## Место на диске. Отдельная проблема, дважды доводившая до нуля

Это стоило больше времени, чем сама установка, и повторится у любого, кто пойдёт
этим путём.

```text
Hangover распакованный        2.0 ГБ  (после обрезки 1.8 ГБ)
prefix WoW64                  2.0 ГБ  <- не сотни мегабайт, а два гигабайта
итого на эксперимент          ~3.8 ГБ
```

Prefix Hangover большой потому, что в `system32` и `syswow64` попадают настоящие
DLL обеих архитектур, а не мелкие заглушки.

Диск был заполнен на 100% ещё до начала (160 КБ свободно). Освобождено:

```text
621 МБ  чужие логи отладки (dmc3, box86-wayland) от мая
168 МБ  варианты wined3d, на которые launch.sh не ссылается (все есть в
        recovered-session/device-artifacts)
1755 МБ игры с разрешения владельца: psx Alone in the Dark, dreamcast
        Resident Evil 3, остатки экспериментов dmc
1442 МБ игры с разрешения владельца: Legacy of Kain из psx и dreamcast
```

Сейвы (`.srm`, `.mcd`, `.state`) при удалении игр оставлены намеренно — мизерные, а
потеря необратима.

**Первая попытка собрать prefix провалилась именно из-за места:** диск дошёл до
нуля, `syswow64` остался пустой, 32-битная сторона не установилась. Ошибка выглядит
как проблема WoW64, а на деле это переполнение диска. Сломанный prefix пришлось
удалить и собрать заново.

## Моя ошибка в этой сессии

Обрезая дерево Hangover, я удалил `wininet` и `urlmon` как «игре не нужные».
`wineboot` требует `wininet`, и сборка prefix упала:

```text
wine: Call from ... to unimplemented function wininet.dll.InternetOpenW, aborting
```

Обе DLL восстановлены (11.7 МБ). Вывод на будущее: обрезать можно только то, что
не нужно **Wine**, а не только игре. Безопасно удалённое и проверенное:

```text
mshtml 64 МБ, winedbg 21 МБ, msxml3 29 МБ, windowscodecs 21 МБ,
jscript, vbscript, ieframe, d3dx11, gecko, mono     всего 171 МБ
```

## Времена, для планирования

```text
prefix WoW64 с нуля      ~6 минут (первая попытка 2м05с до падения по месту)
запуск до окна           ~5 секунд
передача 2.0 ГБ на SD    потоком через ssh, без промежуточного архива на устройстве
                         (иначе пик 2.45 ГБ из 2.52 ГБ доступных)
```

## Что дальше

```text
H2  собрать три unix-модуля под aarch64 с патчами 06/08/10 -> первый кадр D3D8
    плюс добавить gptokeyb в launch-hangover.sh, иначе ввода в игре нет
H3  СРАЗУ benchmark, до дальнейшего переноса. Критерий из #31 зафиксирован
    заранее: <5% отказ, 5-15% минимум, 15-25% продолжаем, >25% главный
    bottleneck найден, >40% Hangover становится основной платформой
H4  патчи по одному, каждый со своим A/B
```

Открытым остаётся и вопрос из #31: историческое «+29% от 1608 → 1992» против
защёлки сторожа, которая срезает потолок за четыре секунды. К Hangover это
отношения не имеет, но цифра до сих пор не сходится.

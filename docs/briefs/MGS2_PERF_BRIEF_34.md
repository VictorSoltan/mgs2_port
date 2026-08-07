# MGS2 RG353VS — бриф #34: что именно мешает запустить игру на Hangover

Дата: 7 августа 2026. Отдельный бриф на один вопрос. В #33 ответ размазан по
четырём дополнениям, потому что складывался по ходу; здесь он собран целиком и
самодостаточно.

Всё ниже измерено на устройстве. Где вывод предположительный, это сказано.

## Ответ одной строкой

**`Direct3DCreate8` не возвращается.** Игра зависает внутри инициализации адаптера
wined3d, вероятнее всего в `wined3d_adapter_find_polyoffset_scale`, потому что тот
вызывает `glClearDepth` — функцию, которой в GLES не существует. Всё остальное
(нет кадров, нет окна, 96% CPU) — следствия этого одного факта.

## Что УЖЕ работает

Это важно не меньше блокера: вся EGL-часть закрыта, и закрыта **без единой правки
Wine**, маленьким `libEGL.so.1`-façade поверх настоящего `libmali`.

```text
нативный ARM64 Wine (Hangover 11.0)          работает
WowBox64 исполняет i386-код игры              работает
prefix WoW64, syswow64 862 файла              собран
libmali + libEGL + libwayland-egl нативно     загружены в процесс игры
pixel formats                                 0 -> 34
eglCreateContext (GLES 3)                     успешно
eglMakeCurrent                                ret=1
eglCreateWindowSurface                        дважды, успешно
GL_CONTEXT_PROFILE_MASK                       обезврежен, GL_INVALID_ENUM пропал
probe GL 4.4                                  убран через MaxVersionGL
наши i386 PE wined3d/d3d8                     ABI-совместимы, работают
ошибок err:d3d / warn:d3d                     ноль
```

То есть графический стек до создания устройства D3D8 доведён до состояния «ошибок
нет». ABI-стена из #29 (`x86 libwayland` против нативного Mali EGL) снята — это
подтверждено загруженным нативным `libwayland-egl` в адресном пространстве игры.

## Где именно останавливается

Трассировка d3d8 за весь запуск даёт **одну строку**:

```text
trace:d3d8:Direct3DCreate8 sdk_version 0xdc
```

и ничего больше. Ни `GetAdapterModeCount`, ни `CreateDevice` — функция не
возвращает управление.

Трассировка wined3d (только на диагностической сборке, см. ловушки) показывает
последнее, что успевает выполниться:

```text
wined3d_init -> wined3d_output_init -> wined3d_parse_gl_version
             -> wined3d_adapter_init -> wined3d_adapter_init_gl_caps
             -> parse_extension_string   (125 строк = 125 разобранных расширений)
затем лог перестаёт расти, CPU 96%
```

125 строк `parse_extension_string` — это нормальный разбор расширений, **не** цикл.
Спин наступает после него, в участке `wined3d_adapter_init_gl_caps` без
TRACE-вызовов, поэтому в логе он невидим.

## Виновник, и почему именно он

`wined3d_adapter_find_polyoffset_scale`, `dlls/wined3d/utils.c:3880`:

```c
gl_info->gl_ops.gl.p_glClearColor(0.0f, 0.0f, 0.5f, 0.0f);
gl_info->gl_ops.gl.p_glClearDepth(0.5f);   /* desktop-only; GLES имеет glClearDepthf */
gl_info->gl_ops.gl.p_glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
```

вызывается из `for (;;)`, который подбирает масштаб polygon offset и выходит либо по
успеху, либо по счётчику попыток с сообщением об ошибке.

Доказательство не теоретическое, а сравнительное:

```text
production:  err:d3d:wined3d_adapter_find_polyoffset_scale PolygonOffset scale
             factor detection failed, using fallback value 2^23     (печатается)
hangover:    этого сообщения НЕТ вообще, при CPU 96%
```

То есть на production детекция не удаётся и срабатывает fallback, а под Hangover до
fallback дело не доходит.

`glClearDepth` в GLES отсутствует. Ровно этот мост есть в нашем
`08-win32u.patch`: `gles_clear_depth` -> `glClearDepthf` и `gles_depth_range` ->
`glDepthRangef`. Под Hangover он не применён, потому что `win32u` там stock ARM64.

Оговорка: что спин именно в этой функции, **не доказано напрямую** — доказано, что
он в `wined3d_adapter_init_gl_caps` после разбора расширений, и что эта функция
единственная там с `for(;;)` и с desktop-only вызовом, и что её сообщение об
ошибке под Hangover пропадает.

## Почему façade это не лечит

Façade перехватывает `eglGetProcAddress`, и через него Wine берёт расширения.
Добавленное правило 6 (`glClearDepth` -> `glClearDepthf`) **не сработало ни разу** —
события в логе не появились, поведение не изменилось.

По исходникам `win32u/opengl.c`:

```text
:874   dlopen( SONAME_LIBEGL, RTLD_NOW | RTLD_GLOBAL )
:881   dlsym( funcs->egl_handle, #name )        часть символов берётся напрямую
:908   ALL_EGL_FUNCS через p_eglGetProcAddress
:2497  ALL_GL_FUNCS через driver_funcs->p_get_proc_address
```

Практический вывод: **façade закрывает EGL и расширения, но core-GL функции им не
закрыть.** Это и есть граница подхода «не трогать Wine».

## Следствие для плана

`08-win32u.patch` для первого кадра **нужен** — конкретно его depth-мост. Раньше он
был отнесён к «вероятно не нужен сразу»; теперь под это есть основание, а не
предположение.

Нужна первая в этой ветке пересборка Wine:

```text
собрать win32u.so под aarch64 только с depth-мостом из 08-win32u.patch
    без pre-resolve списка из 102 функций
    без PeekMessage-части (она в message.c и к кадру не относится)
положить в /storage/hangover/lib/wine/aarch64-unix/
```

Тулчейн `aarch64-linux-gnu-gcc` на машине разработки есть; понадобится sysroot с
заголовками wayland/EGL под ROCKNIX.

Напоминание из #32/#33, которое здесь критично: развёрнутый production
`win32u_glfuncs3.so` содержит правки, которых **нет в дереве исходников** (приём
ES2/ES3-битов, `EGL_CONTEXT_MAJOR_VERSION 3`, pre-resolve список,
`EGL_DEFAULT_DISPLAY`), и пересборка их теряет. Для Hangover это не проблема —
правила 1-3 façade уже дают то же поведение — но собирать надо ARM64-модуль, не
пересобирать production.

## Симптомы, которые больше не надо объяснять заново

```text
96% CPU, один поток, wchan=0    пустой спин ВНУТРИ Direct3DCreate8, а не busy-wait
                                из #30: цикла сообщений игра не достигает вообще
                                (PeekMessageA ноль вызовов)
окна нет в sway                 окно создано (CreateWindowExA "MGS2", 0x280 x 0x1e0),
                                но сообщения никто не качает, поэтому оно не
                                становится видимым. eglDestroySurface ни разу
GPU 200 МГц                     до рендера дело не доходит, draw'ов ноль
0xbb6050 period = 0             инициализация таймера 0x8a2090 не выполняется,
                                потому что WinMain не проходит дальше D3D8
```

## Закрыто: то, что НЕ является причиной

```text
movie-протокол                _moviestart.exe (0x14210 = 68) ведёт себя ИДЕНТИЧНО:
                              draws 0, swap 0, CPU 95%. Ветка с CODEC_REQ_MOVIE_START
                              нужна против disc error, но к запуску не относится
EmulationStation               окно сначала появлялось; проект ES сознательно не
                              усыпляет (MGS2-Substance.sh:25), production с ней живёт
patch 10-winewayland           все 895 строк -- presenter на pbuffer/readback/SHM/PBO,
                              ни строки EGL-конфигов. Переносить нельзя: убьёт
                              нативный wl_egl_window, ради которого всё и делалось
patch 06-opengl32              разбор "OpenGL ES 3.2" снялся нашим wined3d
поддержка ES-профиля в Wine    не требуется: façade биндит ES API сам
переиспользование i386 PE      РАБОТАЕТ (в #32 было закрыто преждевременно)
MaxVersionGL                   помогает (убирает probe 4.4), но не блокер
gptokeyb                       к первому кадру не относится; под hangover-лаунчером
                              не удерживается -- отдельная мелочь
```

## Ловушки измерения, каждая стоила прогона

```text
wined3d_release3.dll -- release, TRACE/ERR вырезаны. "Ошибок нет" на нём НИЧЕГО не
    значит. Диагностировать только на wined3d_glslcache2.dll
grep -c QueryPerformanceFrequency по relay-логу даёт 10 и это ложь: совпадает строка
    конфигурации RelayInclude, которую печатает load_list. Считать
    "Call kernel32.QueryPerformanceFrequency" -- их ноль
MaxVersionGL -- DWORD, не строка. Строкой не действует, и probe 4.4 остаётся
трассировку wined3d писать на /storage, не в /tmp: там tmpfs, то есть ОЗУ
x86 EIP прочитать нельзя: под WowBox64 это эмулируемое состояние, в регистрах
    ARM64 его нет. Отсюда relay и /proc/PID/mem вместо отладчика
```

## Как воспроизвести текущее состояние

```bash
cd /storage/roms/ports/MGS2-Substance
cp /storage/hangover/wined3d_release3.dll /storage/hangover/lib/wine/i386-windows/wined3d.dll
cp /storage/hangover/d3d8_mgs2fast1.dll   /storage/hangover/lib/wine/i386-windows/d3d8.dll
LD_LIBRARY_PATH=/storage/mgs2-egl \
MGS2_D3D8_STATS=1 WINEDEBUG="-all,err+d3d8,err+d3d" \
./launch-hangover.sh
```

Ожидается: семь строк `MGS2EGL:`, ноль `D3D8STAT`, ноль `FIRST SWAP`, 96% CPU.
Вернуть stock: `cp /storage/hangover/backup-stock/*.dll /storage/hangover/lib/wine/i386-windows/`.

Production от всего этого не зависит и не затронут: свой prefix, никаких
bind-mount'ов поверх `/usr/lib/wine`.

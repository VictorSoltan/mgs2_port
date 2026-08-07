# MGS2 RG353VS — бриф #33: EGL-façade сработал, gates 1–4 пройдены, барьер сдвинулся в wined3d

Дата: 7 августа 2026. Продолжение #32. Здесь исправляется ошибка #32, описывается
маленький ARM64 EGL-façade и его результат: **ноль пиксельных форматов превратились
в 34, ошибка `Failed creating Direct3d8 object` исчезла, пересобирать Wine не
потребовалось.**

Всё измерено на устройстве.

## Исправление ошибки #32

В #32 было: `render 45` = десятичное 45 = 1+4+8+32, значит `EGL_OPENGL_BIT`
присутствует, и потому production работает. **Это неверно.** Wine печатает поле
через `%x` (`win32u/opengl.c:497`), то есть `45` — шестнадцатеричное:

```text
0x45 = 0x01 EGL_OPENGL_ES_BIT + 0x04 EGL_OPENGL_ES2_BIT + 0x40 EGL_OPENGL_ES3_BIT_KHR
       EGL_OPENGL_BIT (0x08) ОТСУТСТВУЕТ
```

Старый 32-битный Mali desktop GL не объявлял. Настоящая причина работоспособности
production записана в `MGS2_RG353VS_HANDOFF.md` и была прочитана невнимательно:

> `dlls/win32u/opengl.c` is still pristine upstream — the deployed
> `win32u_glfuncs3.so` works, but rebuilding it would silently lose several fixes
> that are binary-only today: the large pre-resolved GL entry-point list, the
> `EGL_DEFAULT_DISPLAY` override, **acceptance of `EGL_OPENGL_ES2/ES3` config
> bits**, and the **`EGL_CONTEXT_MAJOR_VERSION 3` default** in context creation
> (without which EGL hands back a GLES 1.1 context).

Там же: пересобранный `win32u.so` на 47 740 байт меньше развёрнутого, то есть
рабочий бинарник действительно содержит код, которого в дереве нет.

Вывод, важный для всей ветки: **правки, дающие GLES-контекст, никогда не были в
исходниках.** Ни `06`, ни `08`, ни `10` их не содержат — проверено grep'ом по всем
трём: совпадений с `EGL_OPENGL_BIT`, `ES2_PROFILE`, `eglBindAPI`,
`EGL_RENDERABLE_TYPE` — ноль.

## Решение: три правила в маленьком ARM64 façade, Wine не тронут

`device/mgs2_egl_facade.c`, 70 КБ собранного кода, `aarch64-linux-gnu-gcc`.
Подставляется как `libEGL.so.1` через `LD_LIBRARY_PATH`, `DT_NEEDED` указывает на
настоящий `libmali.so.1`.

Почему façade, а не патч Wine: он оставляет stock Hangover полностью нетронутым,
включая его `winewayland.drv`, который **уже** делает нативный
`wl_egl_window -> eglCreateWindowSurface -> eglSwapBuffers`. Это и есть главный
приз перехода; старый readback-презентер возвращать нельзя. И он обходит ровно ту
ловушку, на которой проект уже спотыкался: пересборку `win32u.so`, к которой
привязаны binary-only правки.

Устройство ответило на вопрос «куда грузиться»: `libmali` экспортирует все нужные
точки напрямую, frontend не нужен.

```text
/usr/lib/libEGL.so.1  -> libEGL.so.1.1.0    131 849 байт (обёртка)
/usr/lib/libmali.so.1 -> libmali.so.1.10.0   59 855 128 байт (реализация)
экспортирует eglGetProcAddress, eglGetConfigAttrib, eglBindAPI, eglCreateContext,
             eglQueryString, eglChooseConfig, eglGetConfigs, eglInitialize,
             eglGetDisplay, eglCreateWindowSurface
```

Три правила:

```text
1  eglGetConfigAttrib: если EGL_RENDERABLE_TYPE содержит ES2/ES3 и не содержит
   EGL_OPENGL_BIT — добавить его В ОТВЕТ Wine. Сам EGLConfig не меняется, поэтому
   eglCreateWindowSurface позже получает настоящий ES3-конфиг
2  eglBindAPI: EGL_OPENGL_API -> EGL_OPENGL_ES_API
3  eglCreateContext: если major version не запрошена — подставить GLES 3
   (именно 3, а не 3.2: это значение развёрнутый бинарник уже использовал, и
   этот Mali на него отвечает "OpenGL ES 3.2")
```

Устройство ELF-объекта, проверено `readelf`:

```text
DT_NEEDED libmali.so.1        <- без этого dlsym Wine не найдёт остальные egl*
SONAME    libEGL.so.1
экспортирует ровно четыре имени: eglGetConfigAttrib, eglBindAPI,
                                 eglCreateContext, eglGetProcAddress
НЕ определяет eglQueryString, eglInitialize, eglChooseConfig,
              eglCreateWindowSurface — они проходят сквозь в Mali
```

Тонкость реализации, которая сначала была сделана неправильно: объект определяет
те же имена, которые ему нужно вызывать, поэтому прямой вызов уходил бы в
рекурсию. Реальные адреса берутся через `dlsym(RTLD_NEXT, ...)`, с запасным
явным `dlopen`. Логирование — одна строка на событие, не на вызов.

## Результат: gates 1–4 пройдены

```text
MGS2EGL: config renderable real=0x45 -> wine=0x4d
MGS2EGL: eglBindAPI OPENGL -> OPENGL_ES
MGS2EGL: context without a major version -> GLES 3

pixel_formats 34                      (было 0)
"Failed to find a suitable pixel format"   ИСЧЕЗЛО
"Failed to get a GL context for adapter"   ИСЧЕЗЛО
```

То есть конфиги, форматы, создание контекста и его активация — всё прошло, без
единой правки Wine и без пересборки чего-либо.

## Барьер сдвинулся, и наши i386 PE его частично сняли

Со **stock** wined3d следующая ошибка была:

```text
err:d3d:wined3d_parse_gl_version Invalid OpenGL major version 0.
err:d3d:wined3d_parse_gl_version Invalid OpenGL version string
    "OpenGL ES 3.2 v1.g29p1-12eac0.d6e9c0f8499d70cc285f3f0ca2ede780"
err:d3d:wined3d_check_gl_call GL_INVALID_ENUM from extension detection @ adapter_gl.c:3695
```

Важно: парсер, который спотыкается, — **в wined3d**, а не в `opengl32/unix_wgl.c`.

После подмены на наши i386 PE (`wined3d_release3.dll` + `d3d8_mgs2fast1.dll`):

```text
ошибок parse_gl_version   НЕТ
ошибок err:d3d вообще     НЕТ
CPU игры                  1-3%  ->  95%
```

То есть наши DLL действительно ABI-совместимы с Hangover 11.0 и снимают разбор
версии GLES. Гипотеза «переиспользовать i386 PE» из #31 подтверждена — в #32 она
была объявлена закрытой преждевременно, потому что падение тогда происходило
раньше, на unix-стороне.

## Где стоим сейчас

Игра жива, грузит CPU на 95%, но **окна в sway больше нет**, GPU на минимуме
200 МГц, на экране EmulationStation. Спин односоставный:

```text
threads=10, state=R, только главный поток: ticks=18513, wchan=0
```

Это в точности форма busy-wait из #30 (`while (тиков < цель) { limiter(); }` при
недостижимом `Sleep`). Окно при этом **сначала появлялось** и пропало только когда
игра прошла стадию D3D8, поэтому забрал его не EmulationStation: проект её
сознательно не усыпляет (`MGS2-Substance.sh:25`), и production с ней сосуществует.

### Ловушка, стоившая часа: release-сборка молчит

`wined3d_release3.dll` — release, TRACE/ERR вырезаны (#29). «Ошибок нет» на нём не
значит «всё хорошо», это значит «ничего не сообщается». Диагностировать надо на
`wined3d_glslcache2.dll`, и он сразу показал скрытое:

```text
warn:d3d:context_create_wgl_attribs Failed to create a WGL context with
    wglCreateContextAttribsARB, last error 0
warn:d3d:wined3d_adapter_gl_init Couldn't create an OpenGL 4.4 context,
    trying fallback to a lower version
err:d3d:wined3d_check_gl_call GL_INVALID_ENUM from Querying context profile
    @ adapter_gl.c:3509
```

`GL_CONTEXT_PROFILE_MASK` — desktop-only запрос, в GLES его нет. Это следующий
класс работы: desktop-GL допущения в самом wined3d при создании версионного
контекста.

## Что дальше, по убыванию ценности

```text
1  почему исчезает окно после стадии D3D8. Прогон на glslcache2 с err+wgl и
   err+waylanddrv, смотреть создание/уничтожение поверхности, а не только d3d
2  ограничить wined3d версией 3.2, чтобы не пытался 4.4 (MaxVersionGL в реестре
   prefix'а) — уберёт бессмысленный probe и часть desktop-only запросов
3  профиль контекста: GL_INVALID_ENUM на adapter_gl.c:3509 и :3695
4  gptokeyb в launch-hangover.sh — нужен для H3, но не для первого кадра
5  когда кадр появится: СРАЗУ H3, критерий из #31 зафиксирован заранее
```

Патч `10-winewayland.drv` по-прежнему **не переносить**: разбор показал, что все
895 строк — presenter на pbuffer/readback/SHM/PBO плюс телеметрия, ни строки
EGL-конфигов. И `06`/`08` тоже пока не нужны: разбор версии GLES снялся нашим
wined3d, а не ими.

## Состояние устройства

Hangover возвращён к stock (наши DLL лежат рядом под своими именами), façade
остался в `/storage/mgs2-egl` и безвреден, пока `LD_LIBRARY_PATH` на него не
указывает. Production цел: десять модулей, `wineprefix64` 598 МБ, lock свободен,
экземпляров ноль, 270 МБ свободно, 70.6 °C.

---

# Дополнение: façade v2, и где именно теперь стоим

Добавлено к façade после первого результата, всё измерено:

```text
4  glGetIntegerv(GL_CONTEXT_PROFILE_MASK) -> GL_CONTEXT_CORE_PROFILE_BIT
5  glBindFragDataLocation -> no-op
+  телеметрия жизненного цикла: eglCreateWindowSurface, eglDestroySurface,
   eglMakeCurrent, eglSwapBuffers (каждое по одному разу)
```

Точка вмешательства проверена по исходникам, это не догадка:

```text
win32u/opengl.c:446   egldrv_get_proc_address -> display_funcs.p_eglGetProcAddress(name)
win32u/opengl.c:2497  USE_GL_FUNC(f) -> driver_funcs->p_get_proc_address(#f)  для ALL_GL_FUNCS
wined3d/adapter_gl.c:3409  p_glGetIntegerv(GL_CONTEXT_PROFILE_MASK, &context_profile)
```

То есть façade стоит между wined3d и GL-вызовами, и правило 4 достаётся до
нужного места без пересборки чего-либо.

Плюс `MaxVersionGL`. Важно: это **DWORD**, а не строка. Первая попытка записать
`"0x00030002"` строкой не подействовала, probe 4.4 остался. С
`dword:00030002` — подействовала.

## Результат прогонов

```text
GL_INVALID_ENUM / "Querying context profile"     было 1+  ->  0
"Couldn't create an OpenGL 4.4 context"          было 1   ->  0
err:d3d / warn:d3d на диагностической сборке     0
eglCreateWindowSurface                           дважды, успешно
eglMakeCurrent                                   ret=1
FIRST SWAP                                       НЕТ
D3D8STAT (счётчики draw'ов нашего d3d8)          НИ ОДНОЙ строки
окно в sway                                      отсутствует
GPU                                              200 МГц, простой
CPU игры                                         95-96%, только главный поток
```

## Что из этого следует

Графическая часть bring-up доведена до состояния «ошибок нет»: GLES-контекст
создаётся, становится текущим, поверхности создаются, desktop-only запросы
обезврежены, probe 4.4 убран. По классификации из плана это **Вариант B**:
`CreateWindowSurface` и `MakeCurrent` есть, `FIRST SWAP` нет.

Но нулевые счётчики d3d8 говорят больше: **игра не делает ни одного draw.**
Значит она не «рисует, но не показывает» — она до рендера не доходит. При этом:

```text
ошибок d3d8 нет (device creation молчит)
WM_QUIT не приходит: главный цикл (0x401167) выходит по ds:0xa14a50 == 0x12,
    а процесс не выходит, значит окно закрылось не через WM_QUIT
спин односоставный, wchan=0 — форма busy-wait из #30
glBindFragDataLocation ни разу не запрошен, то есть до линковки шейдеров
    wined3d тоже не доходит
```

Наиболее вероятная область — **игровая логика запуска, а не графика**: игра
крутится в своей стартовой машине состояний, ожидая события, которое не
происходит. Кандидат из документации самого лаунчера: `[[REQ]] Movie Start`
застаблен в `0x14210` на `0xC3`, и «movie state machine никогда не проходит
дальше состояния 3 — всё, что ждёт start-and-finish фильма, ждёт вечно»
(`launch.sh:22-27`). Почему то же самое не мешает production — не выяснено.

Это **предположение**, а не измерение. Проверяется дизассемблированием стартовой
машины состояний по адресам из #30 либо сравнением, на каком состоянии
(`ds:0xbb61b8`) стоят production и Hangover.

## Что делать дальше, по убыванию ценности

```text
1  сравнить состояние стартовой машины: читать ds:0xbb61b8 из /proc/PID/mem
   у production и у Hangover в один и тот же момент. Разойдутся -- сразу видно,
   на каком состоянии Hangover застревает
2  окно: eglDestroySurface в логе НЕ появлялся, значит поверхность не уничтожали,
   а окно из sway исчезло. Разбирать через swaymsg -t subscribe '["window"]'
   одновременно с прогоном
3  gptokeyb: без ввода игра не уйдёт с титульного экрана сама. Для первого кадра
   не нужен, но для выхода из стартового состояния может быть нужен
4  06/08 по-прежнему НЕ нужны: разбор версии GLES снялся нашим wined3d,
   а profile mask -- façade'ом
5  patch 10 не переносить никогда для этого пути
```

## Состояние устройства

Hangover возвращён к stock, наши DLL на полке в `/storage/hangover/`, façade v2 в
`/storage/mgs2-egl` (безвреден без `LD_LIBRARY_PATH`), `MaxVersionGL=0x30002`
остался в `wineprefix-hangover`. Production цел: `wineprefix64` 598 МБ, lock
свободен, экземпляров ноль, 270 МБ свободно, 69.4 °C.

---

# Дополнение 2: `_moviestart` не помог, и найдено точное расхождение с production

`mgs2_sse_rg353vs_moviestart.exe` (байт `0x14210 = 68`, то есть `[[REQ]] Movie
Start` восстановлен) запущен с façade v2, `MaxVersionGL=0x30002`, нашими
`wined3d_release3` + `d3d8_mgs2fast1` и с gptokeyb. **Результат тот же:**

```text
D3D8STAT (счётчики draw'ов)   0 строк
FIRST SWAP                    нет
окно в sway                   нет
CPU                           95.5%, GPU 200 МГц
```

Значит стартовый блокер не в movie-протоколе. Сработал заранее оговорённый
критерий перехода к чтению памяти.

## Измеренное расхождение

Образ в обоих случаях замаплен по предпочтительной базе `0x400000`, то есть адреса
из #30 валидны напрямую. Прочитано из `/proc/PID/mem`:

```text
адрес                   production   hangover   что это
0xbb6050 period         166666       0          QPF/60, ставит инициализация 0x8a2090
0xf8684c pace target    1            0          цель кадрового квантователя
0xf86a0c                0            0          не различает
0xbb61b8                0            0          не различает
```

`166666` — это ровно `10 000 000 / 60`, то есть QPF на этой машине 10 МГц и
таймер инициализирован. Под Hangover он **нулевой**.

**Вывод: под Hangover игра не доходит до инициализации таймера `0x8a2090`.** По
дизассемблированию из #30 у этой функции ровно один вызывающий, и она вызывает
`QueryPerformanceFrequency`, затем `__alldiv` на 0x3c, затем
`QueryPerformanceCounter`. Это стадия гораздо более ранняя, чем фильмы и чем D3D8.

Отсюда же объясняется и спин: главный цикл `0x401167` крутит
`PeekMessage -> 0x8a41d0 -> Sleep(0)`, а `0x8a41d0` при неинициализированном
состоянии выходит сразу, поэтому 95% CPU при нуле draw'ов — это пустой цикл, а не
зависание внутри игровой логики.

Оговорка: два из четырёх адресов нулевые и в production, поэтому моё истолкование
`0xf86a0c` как «running flag» и `0xbb61b8` как «номер состояния» этим замером **не
подтверждается**. Различают только `0xbb6050` и `0xf8684c`.

## Следующий шаг, узкий и конкретный

```text
1  найти вызывающего 0x8a2090 и то, что исполняется перед ним; выяснить, на чём
   инициализация обрывается под Hangover. Точка бисекции теперь одна, а не «где-то
   в графике»
2  gptokeyb под hangover-лаунчером не удержался (процесса нет, лог пуст) --
   отдельная мелочь, к первому кадру не относится
3  06/08/10 по-прежнему не нужны: графика ошибок не даёт
```

Что закрыто этим замером: версия «застабленный movie-протокол держит стартовую
машину» — **не подтвердилась**, `_moviestart.exe` ведёт себя идентично.

---

# Дополнение 3: точный диагноз стартового блокера

Инструмент — узкий relay (только таймерные и оконные импорты, `RelayInclude` в
реестре prefix'а), поэтому лог 197 КБ и горячий путь не затронут.

Осторожно: `grep -c QueryPerformanceFrequency` по такому логу даёт **10** и это
ложь — совпадает строка самой конфигурации `RelayInclude`, выводимая `load_list`.
Считать надо `"Call kernel32.QueryPerformanceFrequency"`.

## Реальных вызовов Win32 за весь запуск — два

```text
Call user32.CreateWindowExA(8, "MGS2", "Metal Gear Solid 2 : SUBSTANCE",
                            80000000,80000000,80000000, 0x280, 0x1e0, ...)
Call user32.CreateWindowExA(0, "WineD3D_OpenGL", "WineD3D fake window", ...)

Call kernel32.QueryPerformanceFrequency   0
Call kernel32.QueryPerformanceCounter     0
Call user32.PeekMessageA                  0
```

`0x280 x 0x1e0` = 640x480, то есть настоящее окно игры. Второе окно —
служебное окно wined3d, значит **инициализация адаптера wined3d состоялась.**

## Что из этого следует

Игра:

```text
создала своё окно 640x480
дала wined3d создать служебное окно (adapter init прошёл)
после этого НЕ вызвала ни одной функции Win32
и крутит 95% CPU
```

Главный цикл `0x401167` (`PeekMessage -> 0x8a41d0 -> Sleep(0)`) **не начинался**:
`PeekMessageA` ноль вызовов. Значит спин находится **до** цикла сообщений, в коде,
который не обращается к Win32 вообще — то есть это чистое ожидание в
пользовательском коде, не на объекте синхронизации Wine.

Это же объясняет исчезновение окна из sway без единого `eglDestroySurface`: окно
создано, но сообщения никто не качает, поэтому видимым оно не становится.

Заодно это отменяет две мои прежние формулировки: спин — **не** busy-wait из #30
(тот живёт внутри цикла сообщений, до которого дело не дошло), и «init формально
прошёл» тоже неверно.

## Единственный следующий шаг

Найти, что исполняется между созданием окна и первым `PeekMessage`, и на чём там
крутится ожидание. Точки привязки уже есть:

```text
0x8a6265   адрес возврата вызова CreateWindowExA игры (из relay)
0x401167   цикл сообщений, до которого дело не доходит
0x8a2050   init, где 0x8a205a -> 0x8a2090 ставит period; не выполняется
цепочка    WinMain 0x4010d4 -> 0x8780f0 -> 0x8781a5 -> 0x8a2050
```

Читать x86 EIP нельзя: под WowBox64 это эмулируемое состояние, в регистрах ARM64
его нет. Поэтому дальше либо дизассемблирование от `0x8a6265` вперёд, либо relay с
более широким фильтром на том участке, либо сравнение с production тем же relay —
у production `PeekMessageA` и `QueryPerformanceFrequency` вызываться обязаны, и
разница покажет последний общий вызов.

Последнее — самое дешёвое и его стоит сделать первым.

---

# Дополнение 4: спин найден внутри `Direct3DCreate8`, и предел возможностей façade

## Где именно крутится

Трассировка d3d8 (`trace+d3d8`) даёт **одну строку за весь запуск**:

```text
trace:d3d8:Direct3DCreate8 sdk_version 0xdc
```

и больше ничего. То есть `Direct3DCreate8` **не возвращается**. Отсюда и всё
остальное: ни одного draw, ни `PeekMessage`, ни `QueryPerformanceFrequency` —
игра просто не выходит из создания D3D8.

Трассировка wined3d (`trace+d3d`, диагностическая сборка) показывает последнее, что
успевает выполниться:

```text
последние события: wined3d_init -> wined3d_output_init -> wined3d_parse_gl_version
                   -> wined3d_adapter_init -> wined3d_adapter_init_gl_caps
                   -> parse_extension_string (125 строк, то есть 125 расширений)
далее лог перестаёт расти, CPU 96%
```

Поправка к промежуточному выводу: 125 строк `parse_extension_string` — это
нормальный разбор 125 расширений, **не** цикл. Спин наступает после него, в участке
`wined3d_adapter_init_gl_caps` без TRACE-вызовов.

## Наиболее вероятный виновник, с прямым основанием

`wined3d_adapter_find_polyoffset_scale` (`dlls/wined3d/utils.c:3880`) содержит
`for (;;)` и внутри:

```c
gl_info->gl_ops.gl.p_glClearColor(0.0f, 0.0f, 0.5f, 0.0f);
gl_info->gl_ops.gl.p_glClearDepth(0.5f);     /* desktop-only: GLES имеет glClearDepthf */
gl_info->gl_ops.gl.p_glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
```

Основание не только теоретическое: **на production эта функция печатает ошибку**
`PolygonOffset scale factor detection failed, using fallback value 2^23` (видно в
логе production-прогона), то есть там детекция не удаётся и срабатывает fallback.
Под Hangover этой ошибки нет вообще, а CPU 96% — то есть до fallback дело не
доходит.

`glClearDepth` в GLES отсутствует. Именно это и мостит наш `08-win32u.patch`
(`gles_clear_depth` -> `glClearDepthf`, `gles_depth_range` -> `glDepthRangef`).

## Предел façade: правило 6 не сработало

Добавлено правило 6 — подмена `glClearDepth`/`glDepthRange` на float-формы через
`eglGetProcAddress`. **В логе события не появились ни разу**, поведение не
изменилось (draws 0, swap 0, CPU 96%).

Значит core-GL функции до façade не доходят. По исходникам:

```text
win32u/opengl.c:874   dlopen( SONAME_LIBEGL, RTLD_NOW | RTLD_GLOBAL )
win32u/opengl.c:881   dlsym( funcs->egl_handle, #name )     <- часть символов напрямую
win32u/opengl.c:908   ALL_EGL_FUNCS через p_eglGetProcAddress
win32u/opengl.c:2497  ALL_GL_FUNCS через driver_funcs->p_get_proc_address
```

Расширения façade перехватывает, а `glClearDepth` в лог не попал — то есть этот
конкретный символ через `eglGetProcAddress` не запрашивается.

**Вывод, меняющий план: `08-win32u.patch` для первого кадра, по-видимому, всё-таки
нужен** — именно его depth-мост, который ранее был отнесён к «вероятно не нужен
сразу». Façade закрыл EGL-часть (правила 1-3) и profile mask (правило 4), но
core-GL мосты им не закрываются.

## Итог по цели

Цель «запустить и чтобы работало быстрее production» в этой сессии **не
достигнута**. Достигнуто: вся EGL/контекстная часть bring-up закрыта без правок
Wine, и блокер сведён с «где-то в графике» до одной функции с известным дефектом и
известным готовым исправлением в собственном патче проекта.

## Следующий шаг, один

Собрать `win32u.so` под aarch64 из `08-win32u.patch` — только depth-мост, без
pre-resolve списка и без PeekMessage-части, и подложить его в
`/storage/hangover/lib/wine/aarch64-unix/`. Это первая пересборка Wine в этой
ветке, и теперь для неё есть конкретное обоснование, а не предположение.

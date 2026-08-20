# MGS2 native CS DRAW: быстрый пустой кадр, кандидат отклонён

Дата: 2026-08-20  
Устройство: Anbernic RG353VS, RK3566 / Cortex-A55 / Mali-G52, ROCKNIX  
Стек: 32-bit Wine 11.0 под Box86, WineD3D / GLES / native libmali  
Статус: **исследование завершено отрицательным correctness-result; production не менялся**

## 1. Итог в одном абзаце

Свежий cycle-weighted профиль правильно показал, что в `wined3d_cs` остаётся
много translated x86 работы, и выбрал `draw_primitive()` как крупнейший guest
блок. Для проверки был построен минимальный post-batching boundary: оба DRAW
packet handler оставались x86, но сходились на одном ARM entry 37 перед
`wined3d_cs_exec_draw_one()`. Boundary удалось провести через indirect calls и
GL dispatch без SIGILL/abort. Same-process A/B затем показал routed-плечо гораздо
быстрее guest-плеча; отдельный entry 38 измерил стоимость гостевого re-entry.
Однако числа оказались не выигрышем: сначала пользователь сообщил, что точные
окна могли уже относиться к death / MISSION FAILED screen, а обязательный clean
always-routed playtest дал **работающий звук, живой PRESENT/readback и полностью
отсутствующее изображение**. Быстрые routed окна предъявляли неправильный или
пустой кадр. Поэтому raw `-61.732 ms/frame`, calibrated `-58.860 ms/frame` и
производные FPS полностью отозваны как результаты оптимизации. Entry 37/p66
отклонён; прежний production восстановлен побайтно и снова показывает картинку.

## 2. Что было исправлено в записи до начала эксперимента

Работа началась с двух необходимых поправок к прежним выводам:

1. Для island entry 23 были сняты `sign-test p ~ 1.6e-6` и `3.9 sigma`.
   Двадцать из 25 balanced cycles происходили из одного детерминированного
   участка с одинаковыми call counts и не являлись независимыми испытаниями.
   Оставлена только честная формулировка: устойчивое положительное направление,
   примерно `-2 ... -2.6 ms/frame` в сыгранной сцене.
2. Старый renderer frame budget был выведен из употребления. Его сумма
   `22.0 ms libmali + 20.4 ms present` описывала старую сборку, governor и
   capture, тогда как текущий стек уже показывал около 37 ms/frame. Выбирать
   следующую работу по старому «полу» было нельзя.

Эти исправления записаны в
`docs/briefs/MGS2_ISLAND_ENTRY34_FAULT_2026-08-19.md` и `AGENTS.md`.

## 3. Профиль, который выбрал DRAW

В тяжёлой пользовательской сцене был снят один внешний `perf cycles:u` профиль
потока `wined3d_cs`. Он не писал из горячего потока и не менял игру:

```text
samples             36,426
CPU                 fixed 1992000 kHz
guest map           16,487 / 262,144 records
overflow            0
unresolved JIT      0
native libmali      42.48% всех user cycles
Box86 JIT           41.76%
guest wined3d.dll   26.47%
largest guest block draw_primitive(), RVA 0x59e20, 5.424%
```

Артефакты профиля:
`logs/rg353vs/island41-profile-20260819-171556/`.

Это CPU-cycle shares, не ms/frame: perf interval не был синхронизирован с
соседними frame windows. Но профиль надёжно опроверг вариант «в translated
renderer осталось только 2--3 ms» и оправдал один минимальный DRAW-first
эксперимент. Он не оправдывал whole-thread port и ничего не обещал про libmali.

`harness/box86_cycle_profile.py` был дополнен cycle-weighted DSO split и
пониманием обоих форматов handheld `perf script`: `comm tid` и `comm pid/tid`.
Capture/read helpers были оформлены в
`harness/island41_profile_capture.sh` и `harness/island41_profile_read.sh`.

## 4. Предварительно выбранная граница и правило отказа

Направление было зафиксировано до реализации:

```text
generic CS-handler native boundary
          ↓
первым только DRAW
          ↓
smoke
          ↓
same-process A/B DRAW
```

Не входили в scope:

* `wined3d_cs_run` целиком;
* queue, waits, thread lifecycle и packet ownership;
* PRESENT, map/unmap, stop и command-list paths;
* починка A/B entry 34;
* runtime-aware GL preflight;
* расширение production allow-list.

Правило отказа: boundary должен сначала дать правильную картинку и пройти smoke.
Только затем A/B может говорить о скорости. Этот порядок фактически был нарушен:
ранний smoke проверял отсутствие fault и продолжение PRESENT, но не содержимое
кадра. Clean playtest позднее поймал эту ошибку контроля.

## 5. Реализация entry 37

В WineD3D `cs.c` появился глобальный shim:

```c
DECLSPEC_NOINLINE void mgs2_cs_exec_draw_one_island(
        struct wined3d_cs *cs,
        enum wined3d_primitive_type primitive_type,
        unsigned int patch_vertex_count,
        const struct wined3d_draw_parameters *parameters)
{
    MGS2_ISLAND_MARK(0x25);
    wined3d_cs_exec_draw_one(cs, primitive_type, patch_vertex_count, parameters);
}
```

Оба пути вызывают его после decode/batch expansion:

```text
WINED3D_CS_OP_DRAW       -> mgs2_cs_exec_draw_one_island()
WINED3D_CS_OP_DRAW_BATCH -> loop -> mgs2_cs_exec_draw_one_island()
```

Box86 получил entry 37 с ABI `vFpuup` и отдельным ABBA wrapper. Production 17
entries оставались одинаковыми в обоих плечах; переключался только 37.

Главные затронутые research-source области:

```text
../recovered-session/wine-11.0/dlls/wined3d/cs.c
../recovered-session/wine-11.0/dlls/wined3d/context_gl.c
../recovered-session/wine-11.0/dlls/wined3d/ffp_gl.c
../recovered-session/wine-11.0/dlls/wined3d/glsl_shader.c
../recovered-session/wine-11.0/dlls/wined3d/shader.c
../recovered-session/wine-11.0/dlls/wined3d/shader_spirv.c
../recovered-session/wine-11.0/dlls/wined3d/context_vk.c
../recovered-session/wine-11.0/dlls/wined3d/wined3d_private.h
../box86-src/src/mgs2_island_bridges.c
../box86-src/src/mgs2_island_entry_identity.h
../box86-src/src/mgs2_island_class_b.h
../box86-src/src/mgs2_island_natives.c
harness/island/full/island_bridge_table.h
harness/island/full/mgs2_island_bridges.c
harness/island/full/mgs2_island_natives.c
```

Research source остаётся в этом состоянии для диагностики. Это не означает, что
patch series воспроизводит кандидат: отдельные incremental Wine/Box86 patches для
этого эксперимента ещё не экспортированы. До решения correctness-дефекта нельзя
создавать из p66 production patch под видом законченной оптимизации.

## 6. Что пришлось исправить, чтобы ARM closure вообще выполнялся

### 6.1. Оставшиеся indirect callbacks

Статический direct-call closure был недостаточен. В draw path оставались четыре
семейства guest-held function pointers, для которых добавлены class-B sites:

```text
32  shader backend
33  vertex pipe
34  fragment pipe
35  state apply
```

Через site 35 проведены также `context_apply_state()` и callback arrays в
`multistate_apply_2/3`. Аналогичные вызовы были обёрнуты в GL, Vulkan, FFP и
shader paths.

### 6.2. Separable GL cache сохранял x86 pointer

Первый timing/A/B запуск дошёл до separable shader path и показал точную ошибку:
ARM-код вызывал `wglGetProcAddress()`, а локальный cache сохранял возвращённый
guest x86 address `glBindProgramPipeline`. Следующий ARM indirect branch входил
в x86 bytes.

Под `MGS2_ISLAND_ARM` `mgs2_get_gl_func()` теперь разрешает имена только через
переведённую native GL table острова. Диагностика после исправления показала
native addresses `0x77...`, а не guest `0x7a...`.

### 6.3. Точные GL/WGL substitutions

Сохранены уже доказанные special cases:

```text
wglGetPixelFormat     exact guest WGL target through Box86
glPolygonMode         exact guest opengl32 target through Box86
glDrawBuffer          glDrawBuffers(1, &buffer), потому что libmali экспортирует
                      glDrawBuffers, но не glDrawBuffer
```

После этих исправлений diagnostic entry-37 build прошёл более 3,600 frames, а
timing build более 3,000 frames без island fault, SIGILL или abort. Это доказало
работоспособность routing mechanism, но, как выяснилось позже, не корректность
изображения.

## 7. Первый same-process A/B entry 37

На пользовательском маршруте были прочитаны четыре последовательных exact pairs:

```text
cycle   routed ms/f   unrouted ms/f   calls per arm   delta
108        36.458          97.959          112,672     -61.501
109        36.459          97.969          112,672     -61.510
110        36.608          98.562          112,672     -61.953
111        36.310          98.401          112,672     -62.090
median     36.459          98.185                      -61.732
```

Пользователь одновременно сообщил, что игра местами тормозит чрезвычайно
сильно. Это соответствовало дизайну ABBA: routed и unrouted blocks чередовались,
а unrouted wrapper был намного медленнее.

Но raw `-61.732` нельзя было принять даже до black-screen результата. В
unrouted arm wrapper делал `RunFunctionFmt()` примерно 1,006 раз на кадр, тогда
как обычный guest path не платит такой re-entry. Нужна была калибровка.

Дополнительная проблема записи: исходный remote entry-37 log после live read не
был сохранён. Четыре строки выше были записаны из live output, но их нельзя
timestamp-correlate с состоянием игры.

## 8. Entry 38: калибровка A/B re-entry

Был добавлен empty function с тем же ABI и той же частотой вызова, что entry 37:

```text
entry 38  mgs2_cs_draw_ab_calibration(cs, primitive_type,
                                      patch_vertex_count, parameters)
```

Он ничего не делал кроме marker. `noinline, noclone, used` потребовались потому,
что первая сборка клонировала функцию и создала неоднозначный marker. В этом A/B
настоящий DRAW оставался guest в обоих плечах; toggling измерял только native
empty call против guest `RunFunctionFmt()` empty call.

Семь exact cycles 18--24:

```text
calls per arm: 128,912 = 1,151 calls/frame

-1.880  -3.285  -4.086  -2.850  -4.562  -4.452  -3.072 ms/frame
median: -3.285 ms/frame
median per re-entry: 2.854 us
```

Линейное масштабирование к 1,006 calls/frame давало `-2.871 ms/frame` overhead и
арифметически оставляло `-58.860 ms/frame`. Это вычисление корректно только как
оценка стоимости wrapper в неизвестном стабильном состоянии. Оно больше не
имеет смысла как renderer gain.

## 9. Первая отозванная интерпретация: окна могли быть death screen

После измерения пользователь уточнил: во время сессии была экстремальная
медлительность, затем наступил экран смерти. В A/B журнале нет semantic marker,
а exact repeated counts появились на позднем детерминированном участке.

Следовательно:

* exact calls не доказывают, что это был тяжёлый gameplay frame;
* стабильные окна могли уже относиться к death / MISSION FAILED screen;
* `36.459`, `98.185`, `-61.732` и `-58.860 ms/frame` нельзя было использовать
  как combat FPS или promotion evidence.

В этот момент gameplay attribution была письменно отозвана. Но оставалась ещё
возможность, что boundary корректен визуально и велик только в другом состоянии.
Её проверил clean p66 playtest.

## 10. Clean p66 без калибратора

Entry 38 и его вызовы были полностью удалены. Guest DLL был пересобран, identity
сгенерирована из самого shipped PE:

```text
entry 37 marker offset  27
entry 37 canonical RVA  0x000ba0e0
identity count          40
class-B native IDs      1,611
island entries          36
```

Clean diagnostic A/B в лёгком состоянии дал:

```text
cycle 4  routed 16.666, unrouted 28.185 ms/frame
cycle 5  routed 16.666, unrouted 28.409 ms/frame
cycle 6  routed 16.664, unrouted 28.621 ms/frame
cycle 7  routed 16.665, unrouted 28.858 ms/frame
cycle 8  routed 16.668, unrouted 28.495 ms/frame
```

Routed arm сидел на 60 Hz cap. Сначала это было принято только как smoke, не как
второе измерение. Clean playtest показал, что даже такое чтение было слишком
оптимистичным: cap соответствовал быстрому предъявлению пустого кадра.

## 11. Обязательный always-routed playtest и окончательное опровержение

Чистая пара была запущена отдельно, без изменения defaults:

```text
MGS2_BOX86_BIN=box86-island44-draw-clean
MGS2_WINED3D_DLL=wined3d_p66_cs_draw_clean.dll
MGS2_BOX86_ISLAND_FULL=1
MGS2_BOX86_ISLAND_ONLY=0,1,2,3,4,5,6,9,10,14,18,19,22,28,29,32,33,37
MGS2_FREQ_STEPS=1992000
MGS2_PLAY_WINEDEBUG=-all,err+waylanddrv
./launch-play.sh
```

Контроли:

```text
one process                    PASS
CPU current                    1992000 kHz
Box86 candidate vs /proc/PID/exe cmp=0
WineD3D candidate vs mounted target cmp=0
A/B                            absent
entry 38                       absent
entry 37                       armed continuously
class-B                        armed, 1,611 IDs, witnesses agree
native fault / SIGILL / abort  none
```

Наблюдение владельца:

```text
звук есть
изображения нет
```

При этом процесс не завис. Presenter продолжал считать окна:

```text
58.0--60.2 fps over repeated 300-frame windows
readback about 0.84--1.15 ms/frame
compositor wait approximately 0
```

Это решающий контроль. Present/readback loop жив, но содержимое кадра неверно.
Значит routed entry 37 пропускает либо портит rendering work до readback. Быстрое
плечо A/B не ускоряло эквивалентную работу.

## 12. Что именно теперь считается доказанным

### Измерено и остаётся валидным

* Fresh profile: 42.48% libmali, 41.76% Box86 JIT, 26.47% resolved guest
  WineD3D, `draw_primitive()` 5.424% всех user cycles.
* Generic entry-37 routing mechanism можно довести до исполнения без native
  fault; 1,611 class-B functions регистрируются и resolver witnesses сходятся.
* Entry-38 empty re-entry стоит медианно 2.854 us/call в записанном состоянии.
* Clean p66 выдаёт звук и непрерывный PRESENT/readback, но не изображение.
* Старый production после rollback снова показывает картинку.

### Вычислялось, но не является performance claim

* Raw `-61.732 ms/frame` для поздних exact A/B windows.
* Wrapper calibration `-2.871 ms/frame` после масштабирования.
* Разность `-58.860 ms/frame`, `95.314 -> 36.459 ms/frame` и
  `10.49 -> 27.43 fps`.

Эти числа описывают неэквивалентную работу и не должны цитироваться как выигрыш.

### Опровергнуто

* «Routed DRAW даёт большой gameplay FPS gain».
* «60 fps clean smoke означает корректный renderer».
* «Отсутствие SIGILL/abort достаточно для correctness smoke».
* «Exact repeated call counts сами по себе идентифицируют gameplay scene».
* «p66 можно продвигать в production».

## 13. Binaries и хэши

```text
raw timing Box86 / island42
  e486add49999b902759f673785f485080553ae9083b78f9ed6ef34bb55003850
raw DRAW guest DLL / p64
  e6e21882e7ce48d7397dec66c9c430fff39cbc3a55e3fc90522b3e28c492a718

calibration diagnostic Box86 / p65
  8ea84bf0d1b267b16de87b0456eeb5248df7cf5903b7ad0477f4c9a5196737f6
calibration timing Box86 / p65
  b34a987ebfb88c6109cff582aa9047018cb22a7a4acaf0aeded644ddf67f7e14
calibration guest DLL / p65
  3628a235274c94b19e36685bf6f114a9ab8f24cafbb61fb6fa208d1cf933be87

clean diagnostic Box86 / island44 p66
  ff8deaf2f777a4b6ed08b8fdd837584fc6cf43448025931364fe5038e27bcfb9
clean timing Box86 / island44 p66
  886f31378aba707a8aca5d22596421bb0283f2ec48802ad1551af39a672392c6
clean guest DLL / p66
  d63057cb05c3d3e17911c04ea585ce3d02976b6e8870fd27dd7eed83b5aa41
```

Все candidate files на устройстве имеют отдельные имена. Они не являются
production и не должны выбираться launcher defaults.

## 14. Артефакты

```text
logs/rg353vs/cs-draw-calibration-20260820/
  entry38-diagnostic.log
    SHA-256 55412da13e5c94a4d0c2cde69608929b46eeba1fa956ecc2c420b7056e7409f4
  entry38-timing.log
    SHA-256 673c547ccfb0d93f1f2e9d4fc68271e69558518d5c58f0467f1a791eba915053
  entry37-clean-diagnostic.log
    SHA-256 bcb5d1a87dff6ec3e3cbe9d5be27fdbe4402f7aa4161f769a488acfab3112aeb
  p66-clean-black-screen.log
    SHA-256 c8f6809f3fd3c6567dcf2954db0f622de6c10378512926437d14a8d98b2d301a
  production-rollback-picture-ok.log
    SHA-256 26624c28b8fb9259dd89925de20001fca6da524c3193168da3670a767604d4d3
```

Ограничение: raw entry-37 timing log не был сохранён. Его exact rows есть в
этом брифе как live transcription, но не как самостоятельный артефакт.

## 15. Rollback

Failed p66 process был остановлен. Затем запущены неизменённые defaults:

```text
Box86    box86-island32-prod
WineD3D  wined3d_p56_batch_state.dll
```

Оба фактически используемых файла были проверены `cmp`:

```text
production Box86 candidate vs /proc/PID/exe       cmp=0
production WineD3D vs /usr/lib/wine/.../wined3d.dll cmp=0
one process                                       PASS
native fault                                      none
owner observation                                 изображение снова есть
```

Production launcher defaults, `binaries/SHA256SUMS` и
`device/FINAL_PRODUCTION.sha256` для p66 не менялись.

## 16. Решение и единственный допустимый follow-up

Entry 37/p66 закрыт как correctness failure. Не измерять его FPS повторно и не
продвигать. Если boundary когда-либо открывать снова, следующий шаг должен быть
не timing, а bounded correctness census:

1. На guest и routed arms внешне прочитать memory-only counts source DRAW,
   final GL submissions и displayed frames.
2. Добавить bounded frame-content witness на уже существующей readback границе,
   без hot-thread stderr: например, редкий memory-only checksum/sequence,
   читаемый после capture.
3. Интерпретация заранее:
   * меньше final submissions в routed arm -> потерян indirect/state path;
   * counts равны, frame witness пуст/другой -> неверный GL state, context или
     guest/native shared state;
   * только равные counts **и** равная картинка разрешают новый clean playtest;
   * FPS A/B разрешён лишь после прохождения всех correctness gates.

Возможные причины вроде duplicate file-scope state или ещё одного незакрытого
indirect call пока являются гипотезами, не результатами. Black frame доказывает
не место дефекта, а только то, что текущая native closure семантически неполна.

## 17. Следующая correctness-гипотеза после promotion entry 23

Entry 23 отдельно прошёл production-candidate soak и был продвинут как
FINALPLAY7; это не меняет отрицательный результат p66. Следующая попытка DRAW
остаётся research-only и начинается не с timing, а с синхронизации current-context
TLS.

В гостевом `context_gl.c` индекс хранится в mutable file-scope переменной
`static DWORD wined3d_context_tls_idx`; DLL initialization вызывает
`TlsAlloc()` и `context_set_tls_idx()`. ARM island отдельно линкует тот же TU.
Проверка ARM object подтвердила отдельный writable symbol:

```text
00000000 00000004 b wined3d_context_tls_idx
00000058 0000000c T context_get_tls_idx
00000064 0000000c T context_set_tls_idx
```

Это конкретная и хорошо согласующаяся с black frame гипотеза, но пока не
установленная причина. p67 должен один раз после определения guest WineD3D base
прочитать guest `context_get_tls_idx()`, установить тот же индекс в ARM copy и
fail-closed не вооружать entry 37, если индекс равен `TLS_OUT_OF_INDEXES` или
повторное чтение не совпало. На hot path этого вызова быть не должно.

Первый p67 запуск разрешён только always-routed и только с correctness witnesses:
source DRAW, final GL submissions и bounded frame-content/readback checksum.
Никакого FPS A/B до совпадения картинки и submission counts. Если TLS sync не
возвращает изображение, допускается один relocation-based audit writable
`.data/.bss/.tbss` state и одна correction iteration; после второго black frame
coarse entry 37 закрывается и boundary опускается после guest context ownership.

## 18. p67: TLS действительно расходился, sync сработал, кадр остался чёрным

p67 реализовал ровно гипотезу раздела 17, без timing и без A/B. После двух
class-B witnesses Box86 один раз вызвал guest `context_get_tls_idx()`, установил
результат через нативный `context_set_tls_idx()` и повторно проверил значение.
До успешной проверки entry 37 fail-closed исполнял guest body.

Одновременно работали два bounded memory-only witness:

```text
Box86 / mgs2_p67_draw_correctness
    TLS before/after, source DRAW, guest fallback, final GL submissions

winewayland / mgs2_p67_frame_witness
    ring из 64 записей, 16x16 grid checksum уже прочитанного 640x480 кадра
```

Первое внешнее чтение живого процесса:

```text
TLS READY         attempts 1, guest 21, ARM before 0, ARM after 21
source DRAW       101,305
guest fallback    0
final GL submits  101,305, все arrays

presented frames  821
retained ring     frames 758..821
unique hashes     1
min lit           0 / 256
min changed       0 / 255
last checksum     e6a1d1c5
```

То есть гипотеза была фактически верна в первой половине: две копии TLS index
реально расходились (`21` против `0`). Но она была неверна как причина black
frame. После точной синхронизации ни один DRAW не ушёл в fallback, число source
и final calls совпало до единицы, а все 64 последних readback-кадра остались
одинаково пустыми. Это также отделяет дефект от «DRAW просто не вызывается».

В первом запуске по ошибке остался `err+all`, поэтому hot path напечатал много
`GL_INVALID_OPERATION` от `glBindFramebuffer()`. Никакое время из этого запуска
не используется; memory records и полностью чёрный readback сохраняют
correctness-смысл. Launcher после capture исправлен на
`-all,err+waylanddrv`, чтобы повторять эту ошибку было нельзя.

```text
box86-island45-p67-tls
  5cf2c7b46cb01865bf04025d81c5f42246e13fbfd4890c4826465a8bbc2f977d
winewayland_p67_frame_witness.so
  a1ee930a37f9e456e1d3205b154f345e11fb1e8e1fe8c8f8286c6bee706fe7db
p67-correctness.log
  a3c7137b587322173e17f50f2e9a0537ff93fbf976a962ff897f5ee3ec938c64
```

## 19. Единственный mutable-state audit и закрытие coarse DRAW

После чёрного p67 выполнен один предусмотренный review:
`harness/island/full/island_mutable_state_audit.py`. Для того же p67 Box86 была
сделана только анализ-копия с `--emit-relocs`; на устройство она не попадала.
Аудит объединил direct/source/ops closure entry 37 и разрешил PC-relative
ссылки в writable ELF objects. Его собственные контроли — уже доказанный
`wined3d_context_tls_idx` и соседний shared `mgs2_batch_ptr` — прошли.

```text
closure                         605 functions
referenced writable objects     46
zero-storage runtime candidates 12
```

Из этих 12 только два являются реальным общим состоянием guest/ARM:

* `mgs2_batch_ptr` уже устанавливается из authoritative guest batch object
  перед native entry 4; именно это ранее сделало production batch flush
  корректным;
* `wined3d_context_tls_idx` — единственная новая находка, и p67 уже доказал её
  синхронизацию `0 -> 21` без возврата изображения.

Остальные десять — ARM-owned translated GL table/cache и GLES substitution,
bounded p38/p67 counters, одноразовые WARN/FIXME flags, либо queue-init символ
из переоценённой статической ветви, которая остаётся на guest стороне. Ни один
не является ещё одним authoritative runtime object, который можно честно
«синхронизировать». Поэтому correction iteration отсутствует не из-за
пропуска шага, а из-за заранее заданного правила: исправлять только реальные
runtime-state candidates, не менять объект наугад.

**Итог:** generic post-batching entry 37 закрыт окончательно. TLS sync доказан,
source/final submission counts равны, а frame-content witness пуст. Следующая
граница должна оставить `context_acquire()`, current-context ownership и release
в guest x86 и входить в ARM ниже. Ни entry 37, ни его старый `RunFunctionFmt()`
A/B больше не измерять.

Устройство сразу возвращено на FINALPLAY7: один процесс, 18 production entries
с entry 23, class-B 1616, без 34/37.

## 20. p68: lower DRAW tail produces a real picture

The complete post-p67 record now has its own handoff:
`MGS2_NATIVE_DRAW_TAIL_AND_DIRECT_MUTEX_2026-08-20.md`. Sections 20--21 below
remain a short chronological summary; use the new brief for the exact ABI,
static audit, build hashes, freeze separation, recovery controls and next gates.

The next boundary followed section 19 literally. Guest x86 keeps
`context_acquire()`, render-target loading, `context_apply_draw_state()`, memory
barriers and `context_release()`. Only the final
`wined3d_context_gl_draw_primitive_arrays()` tail is entered as native ARM entry
38. The bridge ABI is one pointer to an argument object; the rejected
nine-argument draft never ran on the device.

This was correctness-only: no A/B variable and no performance claim. The live
targets and route were:

```text
Box86       box86-island46-p68-tail
             7af46e61f7c19c94b18ec9cef4846710caca2d816a9caad9d9754f8a175b3ef4
WineD3D     wined3d_p68_draw_tail.dll
             c1d605da5b2dbc4e6fe3da1b5e274d7170d21d655889df490dafd36dd7545173
frame SO    winewayland_p67_frame_witness.so
             a1ee930a37f9e456e1d3205b154f345e11fb1e8e1fe8c8f8286c6bee706fe7db
allow-list  FINALPLAY7's 18 entries plus 38; 34 and 37 absent
process     one mgs2_sse_rg353v, CPU fixed at 1992000 kHz
```

At the owner's heavy gameplay spot, before the freeze in section 21, an external
memory read and an independent Wayland screenshot showed actual game content:

```text
TLS                    guest 21, ARM before 0, ARM after 21, attempts 1
source tail calls      4,982,735
guest fallback         0
final GL submissions   4,982,735, all arrays
frame witness          17,832 frames; retained 17,769..17,832
retained content       64 unique hashes, min 252/256 lit, 253/255 changed
picture                correct gameplay, not an empty PRESENT loop
faults / traps         0
```

This refutes the p66/p67 black-frame failure for the lower cut: keeping context
ownership and draw-state application in guest x86 is sufficient for entry 38 to
submit changing, visible frames. It does **not** measure an FPS effect and it is
not a production promotion.

## 21. The p68 session froze on the old direct-mutex self-deadlock, then resumed

The owner reported a complete freeze after the p68 capture above. The process
was left alive. The CS census found stable published work, `waiting_for_event=0`
and no CS progress for 5.5 seconds:

```text
DEFAULT head 0xb7e8bfc tail 0xb7d0258   NOT EMPTY
MAP     head 0x2734    tail 0x2734      empty
executes 2,961,361, unchanged
wined3d_cs futex wait at 0x6040623c, expected value 2
```

The decisive record is the 24-byte direct pthread mutex itself. This run had
`BOX86_MUTEX_ALIGNED=1`, so `0x6040623c` is not a Box86 shadow-pool object and
not one of the `0x400f...` alert futexes:

```text
lock 2   count 0   owner 29633   kind 0   nusers 1
owner TID 29633 = wine_dinput_worker
owner syscall = FUTEX_WAIT_PRIVATE(0x6040623c, expected 2, no timeout)
main thread and wined3d_cs wait on the same mutex
```

The owner was therefore waiting on its own non-recursive direct mutex. This is
the same session-lock deadlock shape captured on 14 August, now proven to recur
after the direct compatible-mutex path replaced the shadow pool. The p68 DRAW
tail was not on the stopped boundary; the evidence does not attribute the
deadlock or its frequency to entry 38. It also corrects any reading that
`BOX86_MUTEX_ALIGNED=1` had closed the gameplay self-deadlock -- it only removed
the shadow-pool mechanism.

The already established one-time recovery was repeated on the owner thread:

```text
pthread_mutex_unlock((void *)0x6040623c) -> 0
mutex after                            24 zero bytes
source / final after 3 s               5,018,093 / 5,018,093
frames after 3 s                       17,861
guest fallback                         0
```

Main returned to `ntsync`, `wined3d_cs` became runnable, and the control
screenshot showed a correctly rendered `MISSION FAILED` screen. Thus the frozen
queue was a downstream victim of the direct mutex, not evidence that entry 38
stopped inside native DRAW. No timing number is taken across the freeze or the
debugger recovery. A later read in the same recovered process reached 7,752,647
equal source/final calls and 20,154 frames with the mutex still all zero; recovery
was sustained rather than a one-frame wakeup.

Artifacts:

```text
logs/rg353vs/cs-draw-p68-20260820/
  p68-freeze-census-20260820.txt
    bf08421f34f261cfe43a7fa9197ba261715ffc8355cde0b47b1f1ea169818f3f
  p68-freeze-recovery2-20260820.txt
    b4952649fb33acb0c203f80c7706ab806a01b5175210514f779a211e9b27d1c5
  p68-correctness-live-after-recovery.log
    d33b0e45568fdd3c911aaf81699d7c1bad2e1a69d63e404dc5b1efaa89f23411
  p68-gameplay.png
    c1e043643593d9563331e9948368ff690259d7ec58b85464b38b82a3b2eb4515
  p68-recovered.png
    55c100248a4b33b36a1a37e26d65291828223f59223834d09ec8ffd1ca3cdf2e
```

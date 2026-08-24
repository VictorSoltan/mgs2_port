# Что из оптимизации DMC3 переносить в MGS2 — 2026-08-24

## Короткий вывод

В DMC3 большой **измеренный** выигрыш дал один архитектурный переход:

```text
WineD3D/OpenGL, живой бой       2.2--2.5 fps
DXVK-Sarek/Vulkan libmali       15.6--15.7 fps
```

Это примерно 6--7x в той сцене DMC3 на устройстве. Это не same-process ABBA и
не прогноз для MGS2. MGS2 уже содержит много оптимизаций WineD3D, которых не
было у DMC3, поэтому переносить следует **маршрут и метод проверки**, а не
множитель.

Главный новый эксперимент для MGS2: отдельный research-arm
`D3D8 -> DXVK-Sarek d3d8+d3d9 -> Vulkan -> proprietary libmali`. Старый отказ
от `DXVK / PanVK` закрывал PanVK на Mali-G52, а не этот маршрут через
проприетарный g29p1 `libmali`.

### Статус после реализации 24 августа

Research-arm собран и впервые прошёл устройство до правильного живого кадра:

```text
MGS2 D3D8 -> DXVK-Sarek D3D8/D3D9 -> Vulkan 1.3.303 -> Mali-G52 g29p1
```

Меню загрузки, экран смерти с живым 3D preview и gameplay после `CONTINUE`
отрисованы; ввод принят. На момент первого witness production launcher и его
DLL не менялись. Позже владелец явно разрешил promotion: FINALPLAY16 теперь
выбирает этот DXVK arm по умолчанию, сохраняя FINALPLAY15 как byte-exact
rollback. Это **correctness boot и owner-authorised promotion**, а не
FPS-результат: `59.0`, `35.7` и `42.6` на HUD сняты в разных меню/фазах сцены и
не сравниваются ни между собой, ни с WineD3D.

Первый witness записан в `MGS2_DXVK_SAREK_FIRST_GAMEPLAY_2026-08-24.md`;
production hashes, device proof и rollback -- в
`MGS2_FINALPLAY16_DXVK_PRODUCTION_2026-08-24.md`.

Повторно прогонять уже измеренные WineD3D-оптимизации перед этим не требуется.
Для будущего сравнения сначала используются сохранённые production logs и
screenshots; новый device-time нужен только для отсутствующего DXVK arm и лишь
если выбранная архивная контрольная сцена совпадает byte/route-wise.

## Какой WineD3D control использовать

Текущий production -- **FINALPLAY16 DXVK**. Для будущего renderer A/B его
единственный честный WineD3D control -- **FINALPLAY15**, а не старая версия из
начала README. Его точный состав записан в `FINAL_PRODUCTION.md`:

```text
box86      box86-fp15
wined3d    wined3d_fp15.dll
presenter  winewayland_dmabuf_prod.so, MGS2_GL_DMABUF=1, SYNC=3
island     0,1,2,3,4,5,6,9,10,14,18,19,22,23,28,29,32,33,41
```

У FINALPLAY15 пока нет собственного frame-time замера после восстановления
island routing. Это обязательный control перед новым renderer A/B: иначе можно
случайно сравнить DXVK с одной из FINALPLAY12--14, где 14 из 19 native entries
были молча disarmed из-за устаревшей таблицы RVA.

Уже измеренные составляющие сохранённого OpenGL rollback-маршрута:

| Оптимизация MGS2 | Результат на устройстве |
|---|---:|
| GPU governor `performance` | 15.21 -> 16.85 fps, +10.8% |
| native island entry 10 | -8.87 ms/frame |
| native island entry 4 | median -2.680 ms/frame, +0.899 fps |
| native island entry 23 | median -1.944 ms/frame; направление около -2--2.6 ms |
| P75A lazy separable stage selector | 71.54 -> 56.74 ms/frame, -14.80 ms, +26% |
| dma-buf presenter поверх FINALPLAY8 | -9.45 ms/frame, 19/20 циклов |

Эти дельты измерялись разными валидными A/B, поэтому их нельзя просто сложить
в один обещанный FPS. DXVK тоже обязан победить **весь FINALPLAY15**, а не
непатченный WineD3D.

## Что именно доказал DMC3

| Изменение в DMC3 | Что измерено | Что из этого следует для MGS2 |
|---|---|---|
| DXVK-Sarek 1.11.1 + Vulkan `libmali` | бой 2.2--2.5 -> 15.6--15.7 fps | главный кандидат с большим upside; величина не переносится |
| native Wayland WSI bridge в Box86 | с ним DXVK получает легальные native Wayland objects | обязательный enabler, отдельного FPS A/B нет |
| Mali compatibility patch в DXVK | бывший mission-start crash закрыт native A/B | обязательный correctness patch, не оптимизация FPS |
| dma-buf presenter | title readback 3.15--3.75 -> 0.40--0.60 ms | механизм полезен, но MGS2 уже имеет собственный более сильный замер и production implementation |
| fixed CPU/GPU clocks | все финальные числа сняты при CPU 1992 MHz и GPU `performance` | это условие измерения; в MGS2 уже production |
| официальный DMC3 1.3 | восемь байтов EXE: LAA/checksum и keyboard map | никакого performance patch здесь нет |
| `direct32` после ROCKNIX update | валидного FPS результата DMC3 нет | в MGS2 оказался обязательным cold-start enabler; ввод и gameplay прошли, но это не FPS-оптимизация |
| `ForceMode0` / новый `snd.drv` | пока только кандидаты, A/B нет | не выдавать за выигрыш и не переносить в MGS2 |

В DMC3 dma-buf не мог исправить 400-ms боевой кадр: readback занимал только
7.53--8.57 ms. Поэтому именно смена renderer была следующим обоснованным
шагом. В MGS2 dma-buf уже сам измерен как -9.45 ms/frame и включён; повторять
эту работу под другим именем не нужно.

## Почему прежний отказ от DXVK не закрывает новый эксперимент

Строка в старом dead-end list объединяла `DXVK / PanVK`. Реально она доказывала
следующее:

```text
PanVK на Mali-G52: Vulkan 1.1 non-conformant -> этот маршрут закрыт.
```

DMC3 запущен по другому стеку:

```text
x86 DXVK-Sarek
  -> Box86 Vulkan bridge с native Wayland objects
  -> ARM proprietary /usr/lib32/libmali.so.1.10.0, g29p1
  -> sway/Wayland
```

Это не реабилитация PanVK. Это новая фактическая граница: тот же RG353VS уже
создаёт Vulkan pipelines и рисует правильный боевой кадр через proprietary
`libmali`.

MGS2 -- D3D8, но DXVK-Sarek содержит 32-bit `d3d8.dll`, который импортирует
`d3d9.dll`. Поэтому минимальный renderer arm требует **обоих** согласованных
patched DLL, а не только DMC3 `d3d9.dll`:

```text
mgs2_sse.exe
  -> DXVK-Sarek x32/d3d8.dll
  -> patched DXVK-Sarek x32/d3d9.dll
  -> native Vulkan libmali
```

## Обязательные части первого DXVK build

База, уже прошедшая DMC3: DXVK-Sarek tag `v1.11.1-mali-fix`, commit
`617958fe1cf2b10e06fa751d3e40bd765dcf2cc6`.

Патч `../dmc3-rg353vs-port/dxvk-patches/01-mali-d3d9-pipeline-compat.patch`
содержит три исправления, которые следует включить сразу:

1. fixed-function shader сообщает `m_pushConstSize`, а не offset как size;
2. D3D9/DXSO/DXBC эмитит `ClipDistance` только при поддержке
   `shaderClipDistance`;
3. D3D9 не включает `robustness2.nullDescriptor` на Mali vendor `0x13b5`.

Последний пункт доказан отдельным native Vulkan A/B: чистый `VkDevice` создаёт
pipeline, тот же device с `nullDescriptor=1` падает внутри g29p1 с status 139.
Это не предположение о DMC3 и не причина ожидать больше FPS; это причина не
повторять уже закрытый crash в MGS2.

Box86 из DMC3 нельзя без проверки целиком подменять вместо `box86-fp15`.
FINALPLAY15 несёт MGS2-specific mutex fixes, native DirectSound FIR, memmove и
актуальную identity/provenance цепочку. Правильный путь -- перенести маленький
native Wayland/Vulkan WSI bridge в точную базу FP15 либо доказать полный diff и
происхождение нового бинарника. Под DXVK native WineD3D island не рисует кадр,
но остальные runtime/reliability исправления всё ещё нужны.

## План эксперимента

### Gate 0 -- выбрать сохранённый production control

- Не перезапускать уже измеренные WineD3D оптимизации.
- Выбрать существующий лог с обычным save, тем же room/combat state, CPU
  1992000 и GPU `performance`.
- Привязать его к сохранённому lit screenshot и точным hashes arm.
- Если scene identity доказать нельзя, не выдавать соседний FPS за control.

Это индексирование уже сделанной работы, а не новый device run.

### Gate 1 -- research-only DXVK boot

- Не менять production launcher и prefix.
- Сохранить текущие input, save и audio DLL; заменить только renderer arm и
  необходимый Box86 WSI bridge.
- Смонтировать согласованную пару x32 `d3d8.dll` + patched `d3d9.dll`.
- До запуска записать SHA-256 sources и проверить mount targets byte-wise.
- Включить pipeline cache только после первого корректного cold run, чтобы не
  спутать корректность, first-use hitch и steady performance.

### Gate 2 -- корректность раньше FPS

Эксперимент прекращается без timing claim при любом failed пункте:

1. title/menu и не менее 300 меняющихся, не чёрных frame witnesses;
2. загрузка save, HUD, текстуры, тени, fog/alpha и корректный aspect;
3. cutscene/codec, смена карты и возврат в gameplay;
4. бой с врагами и reinforcements, эффекты оружия и damage overlays;
5. input, save, музыка, menu clicks и gameplay SFX как отдельные проверки;
6. 20-минутный soak без pipeline crash, OOM и нового hang.

Чёрный кадр при живом PRESENT уже давал в этом проекте ложные 58--60 fps.
Поэтому FPS counter без frame-content witness ничего не доказывает.

### Gate 3 -- renderer A/B

Renderer нельзя честно переключить внутри одного процесса, поэтому здесь нужен
cross-run ABBA, а не обычный island ABBA:

```text
A = точный FINALPLAY15 WineD3D
B = DXVK-Sarek/libmali research arm
порядок: A B B A, затем повторить на той же точке
```

Для каждого arm сохранять frame-time p50/p95/p99, число кадров, температуру,
RSS, pipeline-cache state и хэши всех mounted binaries. Не усреднять loading,
menu и gameplay.

Предлагаемый decision gate:

- `< 3 ms/frame` или `< 5%` устойчивой дельты: закрыть как слишком дорогой
  второй renderer stack;
- `>= 5 ms/frame` и `>= 10%` при всех correctness gates: продолжить
  playtest/soak и только потом обсуждать promotion;
- результат между ними: повторить именно плотный reinforcement spot.

Это заранее выбранный инженерный порог, а не уже измеренный результат.

## Дешёвые MGS2-оптимизации, которые закончить параллельно

### 1. P81 active-program shadow

P81 уже находится внутри `wined3d_fp15.dll`, но production держит
`APS1 enabled = 0`. P75A непосредственно оценил оставшийся call: около 192
`glActiveShaderProgram` на кадр дают абсолютный потолок кандидата примерно
2.05 ms/frame.

Первый запуск -- census через `device/launch-p81-census.sh`, ничего не skip'ает.
Нужны `mismatch=0`, доля `redundant` и подтверждение, что вызовы идут через PE
record, который следует ABBA arm. Затем -- same-process ABBA уже встроенным
runtime switch.

Если redundant-доля даёт меньше примерно 0.3 ms/frame, ветку закрыть. Около
1 ms и выше при нулевых mismatch -- разумный кандидат на production.

### 2. Убрать GL census из release после P81

FP15 island собран с `-DMGS2_GL_CENSUS`: в 30 секунд боя считается около
1.7 млн GL calls, по две memory operations на каждый. `MGS2_GL_STATS=0` это не
отключает, потому что ветка compile-time.

После решения по P81 сделать парную release-сборку без `MGS2_GL_CENSUS` и
измерить. Заранее величина не заявляется. `MGS2_CS_DEADLOCK_CENSUS` и bounded
mutex rings сюда не смешивать: они нужны для ещё открытых freeze defects.

### 3. Shader prewarm для переходов, не для steady FPS

На FINALPLAY15 save-load всё ещё тратит 4.2--4.8 секунды на shader linking.
Все 23 observed sources различны, поэтому ещё один exact-source cache этого не
решит. Валидный следующий вариант из
`MGS2_SEPARABLE_VS_AND_LINK_COST_2026-08-23.md` -- собрать MRU-рецепт 16--32
shader pairs с link time `>= 100 ms` и прогреть их во время настоящего loading /
fade boundary.

Эта работа может убрать hitch после save/map/enemy transition. Её нельзя
записать как рост боевого FPS.

### 4. Отдельный дешёвый audio A/B

В combat profile около 16% добавочной работы пришлось на audio threads, а
`MGS2_DMSYNTH_POLYPHONY` уже runtime-configurable и сейчас равен 48. Сравнение
48 против 24 на одном бою не требует сборки, но принимается только если музыка,
menu clicks и gameplay SFX по-прежнему звучат раздельно и нет пропавших атак.

Это MGS2-кандидат из собственного профиля, а не доказанный выигрыш DMC3.

## Что не делать

- Не обещать MGS2 6--7x или 30 fps из цифры DMC3.
- Не возвращаться к PanVK: новый кандидат использует proprietary `libmali`.
- Не копировать один `d3d9.dll`: D3D8 arm требует согласованной пары
  DXVK `d3d8+d3d9`.
- Не подменять FP15 бинарником Box86 из DMC3 без полного provenance/diff.
- Не считать native Wayland bridge и Mali crash fix отдельными FPS wins.
- Не считать `direct32` доказанной оптимизацией: в MGS2 он теперь доказанный
  enabler DXVK, но FPS для него не измерен.
- Не переносить DMC3 1.3, `ForceMode0` или `snd.drv` в план MGS2.
- Не логировать Vulkan/GL calls из горячего потока во время timing.
- СДЕЛАНО: production DXVK включён после gameplay witness и подготовки
  byte-exact FINALPLAY15 rollback bundle; это promotion по решению владельца,
  не измеренный FPS claim.

## Рекомендуемый порядок

```text
1  СДЕЛАНО: research-only DXVK-Sarek D3D8 arm с Mali fixes
2  СДЕЛАНО: first boot + lit gameplay correctness witness
3  СДЕЛАНО: owner-authorised FINALPLAY16 promotion с fail-closed manifest
4  после promotion: matched FPS arm и оставшиеся correctness/audio/soak gates
5  отдельно: P81/census, shader prewarm и audio polyphony A/B
```

Главная развилка теперь эксплуатационная: DXVK выбран production по игровой
оценке, а FINALPLAY15 сохранён как немедленный rollback. Только будущий matched
замер против точного FINALPLAY15 покажет, дал ли перенос измеримый throughput
win после всех уже сделанных MGS2-оптимизаций.

## Источники внутри workspace

- `FINAL_PRODUCTION.md` -- текущий FINALPLAY16 и исторический FINALPLAY15.
- `docs/briefs/MGS2_FINALPLAY16_DXVK_PRODUCTION_2026-08-24.md` -- точные
  production hashes, device proof и rollback.
- `docs/briefs/MGS2_COMBAT_PROFILE_2026-08-22.md` -- combat cost и audio доля.
- `docs/briefs/MGS2_SEPARABLE_VS_AND_LINK_COST_2026-08-23.md` -- 4.2--4.8 s
  link boundary и prewarm plan.
- `../dmc3-rg353vs-port/docs/briefs/DMC3_FIRST_BOOT_2026-08-23.md` -- DMC3
  WineD3D и dma-buf measurements.
- `../dmc3-rg353vs-port/docs/briefs/DMC3_DXVK_MALI_V13_AUDIO_2026-08-24.md` --
  DXVK combat result, native crash proof и точный patch scope.

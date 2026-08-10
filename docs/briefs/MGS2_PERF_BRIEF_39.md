# MGS2 RG353VS — бриф #39: первый live A/B батчера и цена synthetic EBO

Дата: 8 августа 2026. Продолжение #38. Здесь впервые проверен батчер на живой
сцене с рабочим hot-switch. Итог: склейка действительно выполняется, но текущая
реализация не ускоряет кадр; для следующего шага собрана профильная DLL.

## 1. Что было установлено на устройстве

Тестовый стек:

```text
RG353VS / RK3566 / proprietary libmali
тяжёлая сцена, пользователь подтвердил фиксированный спот
MGS2_FREQ_STEPS="1416000"
MGS2_GL_STATS=60
```

Сначала на устройстве была DLL `94361e4a34c3d236`. Она совпадала с текущей
сборкой исходника и содержала строку `MGS2BATCH: switched to ...`, то есть
поддерживала переключение через `/tmp/mgs2-batch`.

Артефакт `44e9b531ad84bae5` из #38 оказался более ранней статической версией:
в нём строки hot-switch нет. Поэтому первый прогон с этой DLL, где `BATCH=1`
не отличался от `BATCH=0`, признан недействительным и в результаты не входит.

Затем на устройстве восстановлена `94361e4a34c3d236`; mount проверен byte-wise.
Отдельно сохранена статическая версия:

```text
wined3d_batch1.dll                         94361e4a34c3d236
wined3d_batch1.dll.bak-20260808-static44e9 44e9b531ad84bae5
```

Последовательность записи `0 → 1 → 0` в `/tmp/mgs2-batch` дала в логе все три
перехода. Live-switch работает.

## 2. Валидный короткий A/B

Чередование: `0 → 1 → 1 → 0`, по 20 секунд, пауза settle 4 секунды.
Начальный cap был 1416 МГц; температура в окне была примерно 79–80 °C.

```text
arm   fps   frame ms   factor
 0    9.4    106.4       --
 1    8.9    112.4      10.18x
 1    8.5    117.6       7.50x
 0    8.5    117.6       7.50x  (строка factor из старого telemetry окна)
```

Последняя строка не годится как независимый baseline: harness брал последнюю
строку `MGS2BATCH` из общего лога, а не ограничивал её текущим arm. Кроме того,
два arm=0 разошлись на 11.2 мс, поэтому этот короткий прогон не является
финальным FPS-сравнением.

Что является фактом:

```text
hot-switch работает
батчер реально выдаёт synthetic restart draw
factor в telemetry был 7.2–10.3x (обычно около 8x)
dirty=0, incompat=0, full=0 в наблюдавшихся строках
в первом включённом окне 106.4 → 112.4 мс, то есть выигрыша нет
```

Геометрическая ошибка пользователем не отмечена; отдельный визуальный анализ
агентом после просьбы пользователя не выполнялся.

## 3. Почему результат не означает, что batching бесполезен

Количество draw calls действительно сокращается. Но текущий consumer-batcher на
каждый flush делает всё сразу:

```text
создание массива synthetic индексов на CPU
bind element buffer
glBufferData/glBufferSubData
glEnable(PRIMITIVE_RESTART_FIXED_INDEX)
glDrawElements
glDisable(PRIMITIVE_RESTART_FIXED_INDEX)
```

То есть factor около 8x не равен factor около 8x по времени. Dynamic EBO upload,
генерация индексов или сам indexed path Mali могут съедать выигрыш и даже делать
кадр дороже. Это ровно следующий эксперимент из плана #38.

## 4. Подготовленная профильная сборка

В `context_gl.c` добавлена выключенная по умолчанию телеметрия:

```text
MGS2_BATCH_PROFILE=1
```

Она печатает одной строкой в секунду три накопленных времени:

```text
MGS2BATCHPROFILE: build=...ms upload=...ms draw=...ms
```

Профилируются отдельно построение индексов, bind/upload EBO и restart плюс
`glDrawElements`. В обычном режиме дополнительный QPC-путь не выполняется.

Сборка сделана правильным способом:

```bash
source recovered-session/scripts/build-env-i386.sh
make -C recovered-session/build-wine-i386 \
  dlls/wined3d/i386-windows/wined3d.dll \
  i386_CC="i686-w64-mingw32-gcc -DMGS2_RELEASE"
```

Release-проверка:

```text
MGS2_FACESAMPLEQUERY  = 0
MGS2_SKIP_ALL_DRAWS   = 0
MGS2_BATCH_PROFILE    = 1
```

Профильная DLL уже скопирована на устройство отдельным файлом, но ещё не
загружалась и не измерялась:

```text
wined3d_batch2_profile.dll
sha256 f730effb5e8b3ea06bdc79451eaa6ff6af7318cd43197de547459062c9e97383
```

Текущая игра продолжает работать на `94361e…`; перезапуск для profile DLL был
отменён по просьбе пользователя. Следующий запуск потребует снова поставить
Снейка на спот.

## 5. Следующий патч: immutable EBO cache

По результату #39 следующий патч не оптимизирует `glBufferSubData`. Он заменяет
единый dynamic scratch EBO на bounded cache из 1024 immutable EBO, максимум 16 MiB.
Ключ включает mode, index type и полную последовательность `first/count`; после
hash hit выполняется полное сравнение, поэтому collision не меняет геометрию.

На cache hit выполняются только bind и indexed draw. На miss строится новый BO
одним `glBufferData(..., GL_STATIC_DRAW)`; после этого BO никогда не меняется.
При переполнении cache используется обычный `glDrawArrays` для сегментов, а не
возврат к dynamic upload.

Telemetry:

```text
MGS2CACHE: hits=... misses=... entries=... bytes=...KB fallback=...
```

Сборка static-cache была подготовлена и скопирована отдельным файлом на устройство:

```text
wined3d_batch3_staticcache.dll
sha256 64b694191f386ec3a4506046134ef2607ceefce3dccdc0b2f1b4f19ca21e9003
```

Она была загружена и проверена byte-wise на устройстве.

## 6. Результат static-cache на подтверждённом споте

После отключения зарядки выполнен A/B на том же споте, при cap 1416 МГц.
Скриншоты не использовались. Последовательность `0 → 1 → 0` завершилась, cap
остался 1416 МГц и температура около 79 °C.

Результат cache telemetry:

```text
entries=1024  bytes=689KB  fallback=622–752/с
hits=530–651/с
misses=622–752/с
build=0.00ms  upload=0.00ms  draw=27.95–36.96ms/с
```

Cache достигает лимита уже в этой сцене. Большая часть новых batch signatures
уходит в fallback `glDrawArrays`; поэтому это не чистый static-cache A/B и не
подтверждение FPS-выигрыша. Последние строки frame stats были примерно 9.0–11.0
fps, но без пригодного baseline для этой же короткой серии.

Вывод: абсолютный first-wins cache batch3 в текущем виде **не включать в
production**. Он заполняется уникальными `first/count` и после 1024 записей
вечно уходит в fallback; это опровергает политику кэша, а не саму идею
склейки. Production default оставлен `wined3d_release3.dll` и `MGS2_BATCH=0`.

Собран следующий экспериментальный вариант `batch4_eviction`: 4096 записей,
лимит 8 MiB, CLOCK/LRU-вытеснение только в текущем GL-контексте. На miss место
освобождается удалением старого immutable EBO, поэтому fallback теперь означает
только отсутствие безопасного места, а не постоянное переполнение. Нормализация
relative-index и OES base-vertex пока отложены: в текущем wined3d нет готового
пути вызова `GL_OES_draw_elements_base_vertex`.

```text
wined3d_batch4_eviction.dll
sha256 1e75598f0f7b01c9836af7230f65d86dfb5625e200f9f1d9686f0af584b47a8f
```

## 7. Следующий измерительный шаг

### Batch4: live cache-валидность

Batch4 был реально смонтирован (SHA `1e75598f...`) и проверен на подтверждённом
споте при 1416 МГц. Выполнено `0 → 1 → 0`; в конце режим возвращён в `1`.
В отличие от batch3, кэш не дошёл до лимита и не перешёл в fallback:

```text
entries=1727  bytes=1002KB  fallback=0  evict=0
steady-state hits=1186–1319/с  misses=0–2/с
factor=10.29–10.45x
build=0.00–0.07ms/с  upload=0.00–0.75ms/с  draw=63.97–70.75ms/с
```

Это подтверждает, что eviction-cache устранил конкретный дефект batch3
(`1024` first-wins → постоянный fallback). Однако финального FPS-вывода пока
нет: этот запуск не содержал строк frame/FPS telemetry, поэтому сравнение
`batch=0`/`batch=1` по времени кадра нужно повторить с работающим frame logger.

После перезапуска с `MGS2_WINED3D_DLL=wined3d_batch4_eviction.dll` выполнить
короткое чередование `0/1` на том же споте. Первые 5 секунд arm=1 считать
разогревом cache, затем измерить 20–30 секунд steady state. Профильную
телеметрию `MGS2_BATCH_PROFILE=1` можно включить одновременно.

```text
frame ms / fps
factor
build ms
upload ms
draw ms
```

Интерпретация:

```text
upload велико       → кэш synthetic EBO или ring/stream EBO
build велико        → оптимизировать построение индексов
draw велико         → проверять цену indexed restart path на Mali
все три малы        → искать дополнительную ошибку в границах или измерении
```

До этого замера не включать батчер в production defaults и не объявлять
renderer direction закрытым.

## 8. Открытые проблемы

Следующим шагом batch4 не меняется. Для перехода вверх собрана отдельная
профильная d3d8 DLL: она агрегирует за секунду стоимость четырёх участков
`DrawPrimitive` — managed scan/upload, sysmem VB upload, `apply_stateblock` и
submit. Профилирование включается только `MGS2_D3D8_PROFILE=1` и не меняет
поведение рендера.

```text
d3d8_producer_profile.dll
sha256 297f85247819b98cc080d731adac40d7f2451fbb806b303e622f79b42712254a
```

Она установлена на устройство вместе с batch4. После одного профильного окна
следующий патч будет строиться в d3d8 producer-слое, используя существующий
batch4 как backend.

### Producer batch1: первый live-результат

На том же подтверждённом споте, при 1416 МГц и с batch4 backend, загружена
`d3d8_producer_batch1.dll` (SHA `616972a545582ace...`). Включён только
консервативный dirty-bit: `apply_stateblock` пропускается между draw'ами, пока
игра не вызвала setter состояния. Indexed-путь не менялся; в этой сцене census
по-прежнему показывает `indexed=0`.

Профильные окна `MGS2 D3D8PROFILE` дали:

```text
producer batch1: managed=44.2–48.0ms/с  vb=35.1–39.0ms/с
                 apply=82.9–90.3ms/с  submit=87.5–96.1ms/с
до producer batch1: apply примерно 113–127ms/с, submit 85–94ms/с
```

То есть стоимость `apply_stateblock` снизилась примерно на 20–30ms/с, а
`submit` пока не изменился. Параллельно batch4 держит `factor=8.5–8.8x`,
`fallback=0`, `evict=0`, cache около 1290 записей. Это подтверждает пользу
первого producer-барьера, но не является ещё FPS-замером: frame logger в этом
запуске не напечатал пригодных строк. Следующий шаг — агрегировать совместимые
draw'ы до submit, сохранив сброс при изменении состояния.

### Producer batch2: подавление повторной topology-команды

Собрана и установлена отдельным файлом следующая экспериментальная DLL:

```text
d3d8_producer_batch2.dll
sha256 a8ebecc541af23f927747dae9034881ccfa1a7a2b5693544a3a0f88f5f84c4cd
```

Batch2 кэширует последнюю `primitive_type` на producer-стороне и не отправляет
повторный `set_primitive_type` в CSMT. При смене topology команда отправляется
снова; indexed и UP draw'ы проходят через тот же безопасный helper. Launcher на
консоли уже переключён на batch2, текущий процесс не перезапускался.

После перезапуска и подтверждения спота batch2 реально загружен. Окно telemetry
дало `factor=8.49–8.88x`, `dirty=0`, `incompat=0`, `full=0`; batch4 не ушёл в
fallback. Профиль producer batch2:

```text
managed=39.6–48.3ms/с  vb=33.4–36.7ms/с
apply=81.9–89.2ms/с    submit=83.1–96.5ms/с
```

Повторная topology-команда не является главным резервом: `submit` остался на
прежнем уровне. Следующий патч должен сокращать именно число producer
submit/CSMT draw-пакетов, а не только state-команды.

### REFSTAT: resource-hold как простой dedup закрыт

На подтверждённом споте снят отдельный профиль `MGS2_WINED3D_REFSTATS=1` с
`REFUNIQUE=1`:

```text
draws=14049–15347/с  refs=100034–109204/с
refs_per_draw=7.11–7.12  unique=141  probe_overflow=0
```

Числа показывают, что набор ресурсов действительно стабилен, но это не готовый
кэш для producer. В текущем Wine `wined3d_resource_reference()` не делает
обычный refcount: он записывает текущий `CS queue head` в `access_time`. Простое
dedup-подавление повторных записей может оставить старое время и позволить
уничтожению ресурса пройти до более позднего draw-пакета. Поэтому resource-hold
направление закрыто как небезопасное без отдельного lifetime-механизма в
consumer; `REFSTAT` убран из launcher после замера.

### Production decision

### Producer batch3: агрегация совместимых DrawPrimitive

Собран новый CSMT-пакет `WINED3D_CS_OP_DRAW_BATCH` максимум на 64
non-indexed draw'а. D3D8 producer накапливает подряд идущие совместимые
`DrawPrimitive` и публикует их одним packet-submit; смена state, topology,
indexed/UP draw, clear, present и другие барьеры сначала осушают накопитель.
Consumer исполняет исходные draw-параметры по одному, поэтому геометрический
путь остаётся тем же, а меняется только число producer/CSMT публикаций.

Артефакты batch5/batch3:

```text
wined3d_batch5_producer.dll  sha256 e66227946e0c556bf4b61f7a50fb79078a649f7c02569d6898d8f8425c5a53be
d3d8_producer_batch3.dll     sha256 2c02447f3883f40a68de65735643f614b86c9537e4d9d5520e7ca28d7f9b755f
```

Сборка прошла; обе DLL установлены на RG353VS, launcher исправлен на корневой
`MGS2-Substance.sh`, и процесс игры успешно запущен с ними. Live FPS/telemetry
сняты после подтверждения пользователем спота. В production-логе за несколько
последовательных секунд:

```text
draws=19518–23328/с  batches=2253–2700/с  factor=8.52–8.78x
dirty=0  incompat=0  full=0  fallback=0  evict=0
cache entries=1470–1489  bytes≈899–901KB
```

Это подтверждает, что consumer batch4 продолжает работать без геометрического
fallback и что новый producer-путь не ломает порядок пакетов на живой сцене.
Отдельного FPS A/B и producer profile в этом production-окне нет: diagnostics
остаются выключенными.

По решению пользователя экспериментальные оптимизации включены в production
launcher: `MGS2_BATCH=1`, `wined3d_batch5_producer.dll` и
`d3d8_producer_batch3.dll`. Диагностические `GL_STATS`, `D3D8_PROFILE`,
`D3D8_STATS`, `BATCH_PROFILE` и `REFSTAT` выключены. Частотная лестница launcher
оставлена штатной (`1992 → 1800 → 1608 → 1416 МГц`) с thermal guard.

После перезапуска обе DLL проверены byte-wise на консоли; текущий процесс
работает с production-переменными. Это осознанное включение без доказанного
FPS A/B: batch-фактор измерен, но итоговые 24–30 FPS ещё не подтверждены.

### Подготовка без консоли: стопы и Box86

Повторный статический разбор не дал новой причины стопов, но сузил следующую
безопасную проверку. Уже пойманные 3998/3661 ms не связаны с температурой или
частотой; старый тяжёлый watcher видел игровой поток на `anon_pipe_read` /
`ntsync_schedule`, а `wined3d_cs` на futex. Его `wchan`-опрос полусотни потоков
сам усиливал стопы, поэтому для следующего устройства подготовлен
`harness/stall_watch3.py`: он раз в 500 ms читает только CPU ticks game,
`wined3d_cs` и wineserver, disk sectors, cap и temperature — без `wchan` и без
обхода всех потоков. Это подготовка, не новый результат.

В production уже установлены Box86 `BIGBLOCK=2`, `FORWARD=512`, `CALLRET=1`;
они не являются нетестированными значениями. В `launch.sh` добавлен opt-in
`MGS2_BOX86_PROFILE=aggressive` (`BIGBLOCK=2`, `FORWARD=1024`, `CALLRET=1`),
а без этой переменной остаётся исходная production-конфигурация. В A/B меняется
только `FORWARD`; прежняя заготовка с одновременным `BIGBLOCK=3` исправлена как
методически невалидная. Рецепт и откат описаны в `harness/box86_ab.md`. Ни один
Box86-профиль пока не измерен на этой консоли.

### Batch6: production hoist primitive-restart

По следующему плану собран отдельный, выключенный по умолчанию эксперимент:
`wined3d_batch6_hoist.dll`.

```text
sha256 a3f92b869bb7d11477c5fb7c787ae207b3269c0c69953e2bd364b660dd9a006d
MGS2_BATCH_RESTART_HOIST=1
```

Обычный batch5 делает `glEnable(GL_PRIMITIVE_RESTART_FIXED_INDEX)` и
`glDisable()` вокруг каждого synthetic indexed draw. Batch6 при opt-in флаге
оставляет restart включённым в том же GL-контексте между batch flush'ами;
перед любым обычным indexed draw и при выключении batch он его снимает. Default
идентичен batch5.

Batch6 установлен на устройство, смонтирован byte-wise и включён в production
вместе с producer batch3. Пользователь подтвердил корректную картинку. В
15-секундном production-окне на подтверждённом споте, без горячего профайлера:

```text
cap=1608 МГц  temp=81.7 °C
draws=20872/с  batches=2540/с  factor=8.22x
dirty=0  incompat=0  full=0
cache hits=1731/с  misses=0.7/с  entries=1921  fallback=0  evict=0
```

Это проверка живости и безопасности, не FPS A/B: thermal guard уже опустил cap
до 1608 МГц, а frame logger был выключен. Попытка одновременно включить
`MGS2_TRACE=1`, `MGS2_BATCH_PROFILE=1` и frame logger признана невалидной:
пользователь сразу заметил сильные дополнительные лаги. Trace и горячие QPC
таймеры после этого сняты, игра возвращена в production (`WINEDEBUG=-all`,
`MGS2_GL_STATS=0`), и плавность восстановилась.

### Batch7, собран: общий EBO arena

Следующий opt-in заменяет тысячи отдельных cached EBO двумя ограниченными arena
по 4 MiB, максимум по одной на GL-контекст:

```text
MGS2_BATCH_EBO_ARENA=1
wined3d_batch7_arena.dll
sha256 591788769a30fa228d798688d746e7bc777b5fa6217f5fcf95178e518499ef45
```

Каждая signature хранит offset внутри общего EBO. На hit остаётся bind того же
объекта (который state cache может подавить) и `glDrawElements(..., offset)`.
Новая signature загружается `glBufferSubData`; при заполнении 4 MiB arena
orphan'ится одним `glBufferData`, а signatures только этого контекста удаляются.
Суммарная память arena ограничена 8 MiB. Флаг выключен по умолчанию, поэтому без
него DLL повторяет batch6. Release-сборка прошла; новых warning'ов нет.

Batch7 был установлен и запущен byte-wise с `MGS2_BATCH_EBO_ARENA=1`, без
профайлера и frame logger. Пользователь сразу отметил заметное падение FPS до
начала формального замера. Этого достаточно, чтобы закрыть arena как
production-кандидат: процесс остановлен, production batch6 восстановлен и снова
проверен byte-wise. Возможное объяснение — общий изменяемый storage с
`glBufferSubData` создаёт на этом Mali больше synchronization/validation work,
чем отдельные immutable EBO; это гипотеза, а не измеренный механизм.

Cached `TRIANGLE_STRIP → GL_TRIANGLES` способен сохранить один draw на batch,
однако увеличит число индексов примерно втрое; переходить к нему стоит после
проверки дешёвого arena-варианта.

### Batch8: triangle-list live

После регрессии arena собран отдельный вариант, который оставляет проверенные
immutable EBO, но разворачивает каждый strip в triangle list с тем же winding:

```text
0,1,2,3,4,5 → 0,1,2; 2,1,3; 2,3,4; 4,3,5
MGS2_BATCH_TRIANGLES=1
wined3d_batch8_triangles.dll
sha256 90ca40ec97067ccf26ee854151fdf4064c214470207c529c41f1be8177357e64
```

Batch8 установлен и проверен byte-wise. На подтверждённом споте пользователь не
увидел поломанной геометрии или явного ухудшения плавности (`«вроде всё ок»`).
Лёгкое 10-секундное окно без профайлера:

```text
cap=1608 МГц  temp=82.2 °C
draws=20633/с  batches=2399/с  factor=8.60x
idx=2165KB/с  cache entries=1455 bytes=2041KB
fallback=0  evict=0  dirty=0  incompat=0  full=0  GL errors=0
```

Механизм корректен, но FPS-выигрыш не доказан. Индексный поток вырос примерно в
2.5 раза относительно restart-варианта. PortMaster production остаётся batch6;
текущий ручной процесс работает на batch8.

### Batch9, собран: direct hash cache

В steady state batch8 держит около 1455 signatures, а старый lookup линейно
обходит весь массив до совпадения. Batch9 добавляет direct table на 16384 слота:
полное сравнение ключа остаётся обязательным, а collision безопасно падает в
старый linear lookup. Геометрия и GL-путь batch8 не меняются. Telemetry разделяет
`fast`, `slow` и число `probes`.

```text
wined3d_batch9_hashcache.dll
sha256 d401c31ef56a881dd3e0e1d7ab0ea1eb87458659d361be63b4d5613f9067f2de
```

Release-сборка прошла, новых warning'ов нет. Самостоятельный batch9 установлен
рядом с production, но решающий тест выполнен следующей decision-сборкой, где
тот же direct table переключается live.

### Batch10 decision: hash-cache доказан, draw-path больше не главный предел

Чтобы не включать разрушительную диагностику и не делать четыре перезапуска,
собрана одна DLL с тремя лёгкими механизмами:

```text
wined3d_batch10_decision.dll
sha256 fdf7efe3f5673a3c48133e5372a5846f43474daf6d11919cb79c0ac4575d8623
MGS2_BATCH_HASHCACHE=0/1       live: /tmp/mgs2-batch-hashcache
MGS2_BATCH_SKIP_DRAW=0/1       live: /tmp/mgs2-batch-skip-draw
frames/fps                     один integer increment на present
```

`skip-draw` сохраняет batch aggregation, cache lookup, build/upload и EBO bind,
но не вызывает batched `glDrawArrays/glDrawElements`. Telemetry печатается один
раз в секунду напрямую, без `WINEDEBUG`, `TRACE`, QPC и per-draw logging.

Один процесс, подтверждённый спот, фиксированные 1416 МГц, порядок
`hash0 → hash1 → hash0 → hash1 → no-draw`:

```text
arm       fps    frame ms   factor   draws/с   fast/с   probes/с   temp
hash0    13.62     73.42     8.64     18440         0     897533   81.1
hash1    14.54     68.78     8.54     19805      1604       9536   81.7
hash0    13.79     72.52     8.04     19050         0    1165976   82.8
hash1    15.67     63.82     9.69     20294      1471       1438   82.2
no-draw  19.93     50.18     9.07     25854      1963       3121   81.7
```

Hash-cache повторяемо убрал примерно 0.9–1.17 млн linear probes/с. Две пары дали
6.3% и 12.0% сокращения frame time; точную величину нельзя отделить от изменения
формы workload (`factor 8.04–9.69`), но знак и механизм подтверждены. После
прогона normal draw автоматически восстановлен (`skip=0`), steady telemetry снова
показывала 15–17 fps, fast hits и почти нулевые probes.

No-draw поднял потолок только до 19.93 fps: относительно предшествующего hash1
фактические batched GL draw'ы стоят около 13.6 ms/кадр; относительно среднего
hash1 — около 16 ms/кадр. Значит старые ~50 ms renderer estimate больше не
описывают текущий stack. Даже при полном удалении этих draw'ов остаётся
50.18 ms/кадр вне них. Основной постоянный предел теперь надо искать в
game/D3D8 producer/CSMT/waits/present, а не в следующем EBO allocator.

```text
многосекундные стопы остаются необъяснёнными
A/B harness исправлен: каждый arm читает только свой диапазон строк
батчер пока не даёт подтверждённого FPS-выигрыша
native Box86 draw timer не сделан: исходника Box86 в workspace нет
batch7 arena дал явный пользовательский FPS-регресс и оставлен выключенным
batch8 triangle-list геометрически корректен, но FPS-выигрыш не доказан
batch9 hash-cache доказан live и должен войти в следующий production renderer
no-draw ограничил выигрыш GL draw-path примерно 14–16 ms/кадр
следующий bottleneck: оставшиеся ~50 ms game/producer/CSMT/waits/present
```

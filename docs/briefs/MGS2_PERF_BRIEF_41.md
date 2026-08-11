# MGS2 RG353VS — бриф #41: результаты projected census и WORLD+STREAM

Дата: 10–11 августа 2026. Продолжение #40. Изначально этот бриф фиксировал две
реализованные, но ещё не измеренные ветки. Разделы 7–8 теперь содержат live-
результаты и закрытые отрицательные направления после актуального production-
стека `wined3d_batch16_setcache.dll + d3d8_producer_batch14_dirtyranges.dll`.
Production launcher и его defaults не менялись.

## 1. Цель следующего измерения

Последняя чистая пара normal/skip-draw даёт бюджет около `2.60 ms/frame` до
30 fps. При примерно 1299 source draw, factor около `8.6x` и 151 итоговом GL
draw на кадр это соответствует устранению примерно 39–40 driver submissions.
Точка принятия следующего изменения — не процент fps, а:

```text
actual GLES draws/frame <= 115
target with margin       95–105
no new spikes            >100–200 ms
fixed CPU cap            1800 MHz
```

Эти числа — расчёт из уже снятого budget, не результат новых измерений.

## 2. `d3d8_producer_batch15_projectedcensus.dll`

В `d3d8/device.c` перед существующим drain pending batch добавлен выключенный
по умолчанию `PROJECTED_BATCH_BREAK_CENSUS`. Он не меняет dirty/apply/flush
решения. На draw path выполняются только сравнения уже поддерживаемых integer
fingerprints и счётчики; две строки выводятся после ровно 300 `Present`.

Effective draw-state разделён на шесть независимых групп:

```text
WORLD
MATERIAL (material + tracked lights)
TEXTURE
RS/TSS/SAMPLER (включая viewport/scissor)
SHADER/CONSTANTS (shader, decl, transforms кроме world, clip planes)
STREAM/VB (streams + index buffer/base vertex)
```

Для каждого slot хранится 128-bit reversible fingerprint. Setter делает
`xor(old_slot_hash) ^ xor(new_slot_hash)`, поэтому последовательность
`A -> B -> A` между draw возвращает исходный effective fingerprint и попадает в
`NET_STATE_SAME`. StateBlock Apply делает полный resync. Свет отслеживается по
реально встреченным индексам, максимум 64; overflow отдельно печатается и делает
результат подозрительным.

Границы классифицируются как:

```text
NET_STATE_SAME      WORLD_ONLY          MATERIAL_ONLY
TEXTURE_ONLY        RS/TSS/SAMPLER      SHADER/CONSTANTS
STREAM/VB           RESOURCE_MUTATION   HARD_ORDER_BARRIER
MIXED_STATE
```

`MIXED_STATE` добавлен намеренно: изменение нескольких групп нельзя честно
приписать одной из требуемых категорий. Writable buffer/texture locks,
`CopyRects`, `UpdateTexture` и read/write framebuffer operations отмечаются как
resource barriers. Render-target changes, Begin/EndScene, Clear и Present — hard
barriers. Разная topology и пути, не поглощаемые текущим producer batcher, также
остаются hard.

Первая строка содержит реальный producer batch count и семь независимых
проекций: сколько GL draws осталось бы при разрешении только `NET_STATE_SAME`,
либо same плюс одна из шести state-групп. В проекции сохранён текущий предел 64
source draws на batch. Вторая строка содержит число границ каждого класса и
sanity counters `same_dirty`, `changed_clean`, `light_overflow`.

```text
MGS2_D3D8_PROJECTED_BREAK_CENSUS=1

MGS2PROJECTED: frames=300 source=... actual_batches=... projected_same=...
MGS2PROJECTED_BREAKS: same=... world=... ... resource=... hard=... mixed=...
```

Артефакт:

```text
d3d8_producer_batch15_projectedcensus.dll
sha256 3d8522fa0c35e7f8db951ac4f98df2a9af14d6e5839cd0aede2a15d0cbdc2e61
patch  wine-patches/18-d3d8-projected-break-census.patch
```

## 3. `wined3d_batch17_relative_range.dll`

Второй opt-in сохраняет текущий synthetic-EBO batcher, но нормализует каждый
batch относительно `min_index`:

```text
stored_index = absolute_index - min_index
span         = max_index - min_index
draw         = DrawRangeElementsBaseVertex(mode, 0, span, ..., min_index)
```

Тип индекса теперь выбирается по `span`. При primitive restart значение
`0xffff` остаётся зарезервированным; реальный relative span для ushort обязан
быть меньше `0xffff`. Для triangle/degenerate paths без restart допустим весь
ushort range. Restart token записывается без вычитания base и сравнивается GL до
прибавления base vertex, как требует OES semantics.

Cache hash и exact key сравнивают normalized `first[]`; абсолютный и relative
форматы разделены флагом, поэтому live-переключение не смешивает записи. В
`MGS2CACHE` добавлены `relative` и `rel16`.

В Unix-side `opengl32` thunk добавлен один узкий alias:
`glDrawRangeElementsBaseVertex -> glDrawRangeElementsBaseVertexOES`. Native
pointer остаётся внутри Wine WGL bridge. Binary-only production
`win32u_glfuncs3.so` не пересобирается. Общая capability
`ARB_DRAW_ELEMENTS_BASE_VERTEX` не включается: GLES deny-list WineD3D не
менялся, новый путь включается только собственным флагом и только при ненулевом
entry point.

```text
MGS2_BATCH_RELATIVE_RANGE=1

wined3d_batch17_relative_range.dll
sha256 2839ef5882335b9eb32d79c85a5b7466d6bd9b9d3126e667909e7fe2c78b44a4

opengl32_glesver2_basevertex.so
sha256 4da347edd88bf9248464ab030a9da74722c380dad4dd2e5201231fda4429f0c8

patch wine-patches/19-wined3d-relative-range.patch
```

Для чистого A/B состояние можно менять раз в секунду без перезапуска процесса:

```text
/tmp/mgs2-batch-relative-range   содержимое 0 или 1
```

Polling работает при `MGS2_BATCH_STATS=1`. Переходный интервал после записи
файла в выборку не включается.

## 4. Сборка и воспроизводимость

Обе PE DLL собраны как release с `i686-w64-mingw32-gcc -DMGS2_RELEASE`; новый
`opengl32.so` собран 32-bit Unix toolchain. Сборки завершились успешно. Warning в
WineD3D относятся к уже существующим выключенным diagnostic helper functions;
новых warning от relative-range кода нет.

Патчи 18 и 19 проверены на чистом Wine 11.0 после существующих патчей 01–17:

```text
patch -p1 -F0 --batch    PASS
8 modified source files byte-for-byte match the built working tree
artifact strings         PASS
```

Все три новых файла скопированы на RG353VS в
`/storage/roms/ports/MGS2-Substance/`; remote SHA совпадают с локальными.
Во время копирования игра не была запущена, launcher и bind mounts не менялись.

Первая ревизия ошибочно помещала alias в пересобранный
`win32u_glfuncs4_basevertex.so`. На устройстве она зависла до инициализации
WineD3D на `eglInitialize`: рабочий `win32u_glfuncs3.so` содержит утраченные
binary-only GLES config/context fixes, о чём предупреждает handoff. Процесс был
сразу остановлен, сломанный артефакт удалён, а alias перенесён в воспроизводимый
`opengl32` thunk. Исправленный стек с production win32u3 прошёл холодный запуск.

## 5. Первый live-протокол: census

Нужны три худшие заранее загруженные сцены, отдельное 300-frame окно на каждой,
один процесс, 1800 МГц, без charger/thermal transition внутри окна. Стек:

```text
MGS2_WINED3D_DLL=wined3d_batch16_setcache.dll
MGS2_D3D8_DLL=d3d8_producer_batch15_projectedcensus.dll
MGS2_WIN32U_SO=win32u_glfuncs3.so
MGS2_FREQ_STEPS="1800000"

MGS2_D3D8_PROJECTED_BREAK_CENSUS=1
MGS2_BATCH_STATS=0
MGS2_CSMT_PROFILE=0
MGS2_D3D8_PROFILE=0
MGS2_D3D8_STATS=0
MGS2_GL_STATS=0
WINEDEBUG=-all
```

Решение принимается по `actual_batches/f - projected_*/f`, а не только по
сырому числу boundaries:

```text
NET_STATE_SAME removes >=40/f       -> exact-checked fingerprint fast path
WORLD/MATERIAL opportunity >=40/f   -> state-lift UBO batching
TEXTURE opportunity dominates       -> compatibility census, then texture arrays
no branch removes about 30–40/f      -> do not build it
```

`light_overflow != 0` или заметный `changed_clean` требуют сначала исправить
полноту/ownership census; на таком окне нельзя принимать архитектурное решение.

## 6. Второй live-протокол: relative-range 0 -> 1 -> 0

Этот тест отдельный от census. Запуск:

```text
MGS2_WINED3D_DLL=wined3d_batch17_relative_range.dll
MGS2_D3D8_DLL=d3d8_producer_batch14_dirtyranges.dll
MGS2_WIN32U_SO=win32u_glfuncs3.so
MGS2_OPENGL32_SO=opengl32_glesver2_basevertex.so
MGS2_FREQ_STEPS="1800000"
MGS2_BATCH_STATS=1
MGS2_BATCH_RELATIVE_RANGE=0
```

На одном подтверждённом споте после прогрева выполнить три окна по 20–30 секунд:

```sh
echo 0 > /tmp/mgs2-batch-relative-range
echo 1 > /tmp/mgs2-batch-relative-range
echo 0 > /tmp/mgs2-batch-relative-range
```

Для каждого arm сохранить frame time/fps, `draws`, `batches`, `idx KB`, cache
hits/misses, `relative`, `rel16`, температуру, cap и spike histogram. Первые две
строки после переключения исключить. Кандидат сразу закрывается при выигрыше
меньше `0.3 ms/frame`, любом GL error, визуальной ошибке или новом long spike.
Production он заменяет только после повторяемого улучшения на всех трёх худших
сценах; до этого defaults остаются batch16/batch14/win32u3.

## 7. Live-результаты projected/relative веток

Relative-range прошёл короткую парную проверку на одном процессе и оказался
нейтрально-отрицательным:

```text
off   28.8870 fps   34.6177 ms/frame
on    28.8675 fps   34.6410 ms/frame
delta                +0.0233 ms/frame (медленнее)
```

Путь преобразовывал около 89 ranges/frame, но переводил часть cache fast hits в
slow hits. Ошибок GL и нового stall в этом тесте не было. Ветка закрыта: выигрыш
не просто меньше порога 0.3 ms/frame, его знак отрицательный.

Расширенный census (`d3d8_producer_batch16_mixedcensus.dll`, patch 20) на
подтверждённой игровой сцене дал 175–221 actual producer batches/frame. Самая
частая точная mixed-маска — `0x21`, то есть `WORLD + STREAM/VB`. Если разрешить
только эту маску, проекция удаляет 93–109 batches/frame и оставляет 81–113.
Sanity counters чистые: `same_dirty` около нуля, `changed_clean=0`,
`light_overflow=0`.

Следующий узкий census (`d3d8_producer_batch17_streamdetail.dll`, patch 21)
разложил STREAM/VB на buffer/offset/stride/frequency/index/base vertex. Во всех
наблюдавшихся WORLD+STREAM границах точная stream-маска была только `B`: менялся
указатель vertex buffer, но не offset, stride, frequency, index buffer или base
vertex. Частота buffer-only границ была 135–142/frame вообще и примерно
53–70/frame внутри WORLD+STREAM.

Логи:

```text
logs/rg353vs/mgs2-mixed-census-spot.log
logs/rg353vs/mgs2-stream-detail-spot.log
logs/rg353vs/mgs2-batch17-relative-ab.log
```

## 8. Packed source-VBO: отрицательный результат и kernel OOM

По buffer-only census был построен opt-in прототип: вершины каждого source strip
копировались без topology expansion в временный VBO, а смежные buffer-only
границы получали один producer draw-batch. Production defaults не менялись.

Первая версия использовала отдельный временный BO на batch. В коротких окнах без
fallback она копировала примерно 0.98–1.10 MB/frame и показывала 22–24 fps.
В более тяжёлом подучастке число batches превысило pool limit 256/frame:
fallback вырос до 2314–2670 за 13–15 frames, factor упал до 3.52, а скорость —
до 13–15 fps. Draws корректно возвращались на старый путь; это был не hang, но
экономика уже была неприемлемой.

Для устранения batch-count ceiling была проверена вторая версия: один 4 MB
suballocated dynamic VBO на каждый из четырёх in-flight frames. Контрольный
`pack=0` работал нормально. После live-перехода в `pack=1` kernel log зафиксировал
рост Mali allocation для процесса:

```text
03:46:36   477352 kB
03:46:40   501992 kB
03:46:48   526648 kB
03:46:49   530748 kB
03:46:49   global OOM: Killed process 88697 (mgs2_sse_rg353v)
```

То есть пользовательский «зависший» экран в этом arm был процессом, убитым
kernel OOM, а не прежним PeekMessage stall, thermal watchdog или обычным crash.
Наиболее вероятное объяснение — Mali/Wine переименовывает или сохраняет целую
4 MB dynamic allocation при каждом subresource update; это вывод из размера и
темпа GPU allocation, а не отдельно трассированный внутренний вызов драйвера.

Доказательство сохранено в:

```text
logs/rg353vs/packed-vbo/run-packedvbo-ring-ab.log
logs/rg353vs/packed-vbo/mgs2-packed-ring-oom.dmesg
logs/rg353vs/packed-vbo/pack-on-first.log
```

Решение: packed source-VBO закрыт. Большой frame ring повторно не запускать;
поэлементный BO pool безопасно откатывался, но был сильно медленнее. Production
восстановлен на
`wined3d_batch16_setcache.dll + d3d8_producer_batch14_dirtyranges.dll`; mounted
d3d8 SHA256 побайтно совпал с
`47cdfd68792257b8d47189d51a1e68aec79e8a839b6e5d3136fb74e7d9700ee4`.

## 9. Фактическая развилка после live-результатов

Исходная последовательность решений теперь сужена:

```text
NET_STATE_SAME fast path       закрыт: same_dirty около нуля
relative-range                закрыт: +0.0233 ms/frame
чистый WORLD state-lift       неприменим к доминирующей границе
packed source-VBO             закрыт: медленнее; frame ring вызвал kernel OOM
texture/visibility            не подтверждены как доминирующий источник
```

Доминирующая возможность — не `WORLD_ONLY`, а точная граница
`WORLD + STREAM/VB`, причём внутри STREAM меняется только указатель vertex
buffer. Поэтому UBO с world matrices сам по себе не может объединить такие
draw: один обычный GL draw не переключает привязанный vertex buffer между
сегментами. Копирование разных source VB в общий dynamic BO уже проверено и
оказалось как медленным, так и опасным для памяти на этом Mali stack.

Следующая безопасная диагностическая ветка — sampled repeated-geometry census.
Для каждой десятой frame-группы он должен сравнить байты соседних source strips
только на точной границе `WORLD + STREAM/VB(buffer-only)` и посчитать две
проекции: текущую и разрешающую объединение byte-identical geometry через
instancing. Shadow-байты допустимы к сравнению лишь после точного покрытия
записанными Lock ranges; `DISCARD` сбрасывает coverage, overflow делает draw
несравнимым. Census не меняет rendering и печатает один aggregate после 300
`Present`.

Реализация:

```text
MGS2_D3D8_DLL=d3d8_producer_batch18_geometryrepeatcensus.dll
MGS2_D3D8_GEOMETRY_REPEAT_CENSUS=1

d3d8_producer_batch18_geometryrepeatcensus.dll
sha256 015fd1f2c1809a494471ae1e6236dbf1fc6e0309213f89388dc279bfb54cbf84
patch wine-patches/22-d3d8-geometry-repeat-census.patch
```

Флаг census автоматически включает существующий producer snapshot и rolling
projected fingerprint. Production defaults при выключенном флаге не меняются.
В `MGS2GEOMETRY_REPEAT` значения `/f` нормализованы по 30 sampled frames из
300; `invalid` или `overflow` означают, что результат нельзя использовать без
сначала исправленного shadow coverage.

Точка принятия остаётся прежней:

```text
repeat projection removes >=40 batches/frame  -> строить instancing prototype
repeat projection removes <40 batches/frame   -> закрыть instancing
```

Если instancing не проходит этот порог, следующий большой архитектурный вариант
— только общий vertex arena без per-update rename (persistent mapping после
отдельной проверки fence/ownership semantics). Обычный `update_sub_resource`
большого ring buffer повторять нельзя.

## 10. Live-результат repeated-geometry census

На подтверждённом тяжёлом споте сняты три последовательных 300-frame окна при
1800 МГц. В каждом из них хешировались 30 sampled frames:

```text
window  current batches/f  repeat batches/f  removed/f  WORLD+VB/f  same shape/f  same bytes/f
1       243.17             241.73            1.43       90.53       4.40          1.43
2       263.10             261.57            1.53       91.70       4.53          1.53
3       348.37             346.43            1.93      100.73       6.03          1.93
```

Во всех окнах `valid=eligible`, `invalid=0`, `overflow=0`; результат не
объясняется неполным shadow coverage. Движущиеся персонажи меняли общий scene
load, но не вывод: из 90–101 подходящих `WORLD+VB` boundaries одинаковую форму
имели лишь 4–6, а byte-identical geometry — 1.4–1.9 на кадр.

Ветка instancing закрыта: её верхняя проекция меньше порога `40/f` более чем в
20 раз. Реализацию draw-пути для неё не строить.

Лог:

```text
logs/rg353vs/geometry-repeat/mgs2-geometry-repeat-spot.log
```

Следующая non-mutating развилка по исходному плану — visibility census. Его
метрика должна быть не количеством невидимых source strips, а числом целиком
исчезающих текущих producer/GL batches; порог для реализации culling остаётся
`20–25 batches/frame`.

## 11. Visibility census: реализация

Patch 23 добавляет выключенный по умолчанию sampled census. В 30 кадрах из
каждых 300 он читает только source ranges с точным shadow coverage. Fixed-
function `FLOAT3` positions последовательно трансформируются актуальными
WORLD, VIEW и PROJECTION matrices. Draw считается консервативно невидимым лишь
если все его вершины лежат за одной и той же D3D homogeneous clip plane.

Custom vertex shaders, vertex blending, неизвестные position declarations,
non-finite coordinates и неполный shadow всегда считаются видимыми. Rendering,
state, batching и uploads не меняются. Отдельно воспроизводятся текущие producer
batch boundaries; `removed_batches` увеличивается только когда невидимы все
source draw внутри итогового batch.

```text
MGS2_D3D8_DLL=d3d8_producer_batch19_visibilitycensus.dll
MGS2_D3D8_VISIBILITY_CENSUS=1

d3d8_producer_batch19_visibilitycensus.dll
sha256 41253ff070ec774817ba104a2eacefefd86825546609fc2480a647b4129f3504
patch wine-patches/23-d3d8-visibility-census.patch
```

Ветка проходит к culling prototype только при повторяемых
`removed_batches >=20–25/f`; большое число `culled` без целиком исчезающих
batches не является основанием писать draw-path.

## 12. Live visibility census и opt-in culling prototype

На подтверждённом тяжёлом споте четыре последовательных окна дали:

```text
window  source/f  current batches/f  culled source/f  removed batches/f
1       849.50    238.80             135.03           32.77
2       972.37    270.03             129.53           30.07
3       854.77    230.03             121.27           21.60
4       731.70    186.50             130.47           31.80
```

Во всех окнах `invalid=0`, `overflow=0`, `nonfinite=0`. Нагрузка сцены менялась
из-за движущихся персонажей, но все четыре окна проходят нижний порог 20, три из
четырёх — порог 25. Visibility поэтому единственная ветка после census, которая
дошла до реального draw-path prototype.

Patch 24 кэширует object-space AABB по уникальному VB identity, точному content
generation, declaration и source range. Generation увеличивается только после
writable Unlock; `DISCARD` сбрасывает exact shadow coverage. На cache miss AABB
строится по source positions, после чего восемь углов проверяются актуальными
WORLD/VIEW/PROJECTION. Неизвестные случаи всегда идут по старому пути.

При подтверждённом cull draw не попадает в producer batch. Предыдущий pending
batch осушается по прежним state/barrier правилам; dirty uploads и state apply
остаются отложены до первого реально видимого draw. Флаг `discarded` очищается
так же, как на обычном DrawPrimitive. Defaults выключены.

```text
MGS2_D3D8_DLL=d3d8_producer_batch20_visibilitycull.dll
MGS2_D3D8_VISIBILITY_CULL=0
MGS2_D3D8_VISIBILITY_CULL_LIVE=1
MGS2_D3D8_VISIBILITY_CULL_STATS=1

/tmp/mgs2-visibility-cull   содержимое 0 или 1

d3d8_producer_batch20_visibilitycull.dll
sha256 1324cfea65322e7da993050014b6db406eb520b1a0cad912e06ee09b1065c707
patch wine-patches/24-d3d8-visibility-cull.patch
```

Первый тест — один процесс, один спот, `0 -> 1 -> 0`, 1800 МГц. Немедленное
закрытие при визуальной ошибке, новом stall/GL error или отсутствии уменьшения
frame time. Первое 300-frame окно после каждого switch не смешивается с
предыдущим arm: switch сбрасывает cache и counters.

Лог census:

```text
logs/rg353vs/visibility/mgs2-visibility-spot.log
```

## 13. Live A/B/A/B результата visibility culling

Patch 24 проверен на том же подтверждённом тяжёлом споте, в одном процессе и
при фиксированных 1800 МГц. После длинного `0 -> 1 -> 0 -> 1` прогона была
снята короткая чередующаяся серия `0 -> 1 -> 0 -> 1`: по восемь секундовых
интервалов на arm после исключения первых двух строк после каждого switch.
Короткая серия нужна из-за заметного дрейфа нагрузки от движущихся персонажей.

```text
arm  cull  frames  fps      ms/frame  draws/f  batches/f
1    0     162     20.089   49.779    680.77   166.60
2    1     168     20.817   48.038    553.52   137.31
3    0     165     20.369   49.095    684.44   166.56
4    1     169     20.949   47.734    549.16   136.31

combined off   327 frames   20.2289 fps   49.4342 ms/frame
combined on    337 frames   20.8832 fps   47.8854 ms/frame
delta                                      -1.5488 ms/frame
```

Стабильное cull-окно удаляло `131.86 source draws/frame`. Поэтому исходная
нагрузка on-arm до culling была примерно `551.34 + 131.86 = 683.20 draws/f`,
практически совпадая с `682.62 draws/f` в control. Это делает короткую серию
сопоставимой, в отличие от длинных окон, где общий scene load менялся почти в
полтора раза.

Результат повторился в обеих парах: фактический WineD3D batch count уменьшился
примерно на `29.77/f`, frame time — на `1.55 ms`, fps вырос на 3.2%. Загруженный
`d3d8.dll` побайтно совпал с SHA patch 24, процесс остался жив, cap был
1800 МГц, `invalid=0`, `overflow=0`, `nonfinite=0`. В логе нет GL error; в
kernel log нет нового OOM или GPU fault (видны только старые записи packed-VBO
для PID 88697).

Таким образом, prototype проходит локальный performance-порог. Пользователь
подтвердил, что вся измеренная последовательность была визуально корректна, и
решил не проводить проверку двух остальных худших сцен. Это осознанно снимает
исходное условие трёх сцен, но не превращает отсутствующие измерения в
положительный результат.

Patch 24 принят как production default: launcher выбирает
`d3d8_producer_batch20_visibilitycull.dll` и
`MGS2_D3D8_VISIBILITY_CULL=1`. Диагностические live polling и stats по умолчанию
выключены. Немедленный rollback не требует замены DLL:

```text
MGS2_D3D8_VISIBILITY_CULL=0
```

Оба wrapper (`/storage/roms/ports/MGS2-Substance.sh` и его копия внутри
каталога игры) и внутренний `launch.sh` развернуты на устройстве. Их SHA256
совпадают с repository copies, все три проходят `sh -n`; DLL на устройстве
совпадает с SHA256 `1324cfea...c707`. Уже запущенный измерительный процесс не
перезапускался, поэтому production defaults начнут действовать со следующего
обычного запуска.

Лог:

```text
logs/rg353vs/visibility-cull/mgs2-visibility-cull-ab.log
```

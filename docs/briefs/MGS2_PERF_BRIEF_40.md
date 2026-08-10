# MGS2 RG353VS — бриф #40: предел после hash-cache и CSMT map waits

Дата: 9 августа 2026. Продолжение #39. Direct hash-cache убрал измеренный
линейный поиск, после чего perf и лёгкая CSMT-телеметрия локализовали следующий
постоянный резерв: тысячи синхронных Lock/Unlock GPU-only vertex buffers.

## 1. Что уже доказано batch10

На одном процессе, подтверждённом споте и фиксированных 1416 МГц direct table
повторяемо убрал примерно 0.9–1.17 млн linear probes/с. Две пары `hash0/hash1`
дали сокращение frame time на 6.3% и 12.0%. Механизм и знак выигрыша доказаны,
хотя точный процент зависит от формы workload.

`skip-draw` поднял потолок только до 19.93 fps / 50.18 ms. Следовательно,
фактические batched GL draw стоят примерно 14–16 ms/кадр, а около 50 ms остаётся
в game/D3D8 producer/CSMT/waits/present. Следующий EBO allocator не является
главным направлением.

## 2. Perf без горячего логгера

На том же стеке снят 20-секундный `perf record` без per-call telemetry:

```text
DSO:    JIT 62.45%  unknown 14.88%  box86 11.19%  libmali 9.91%
main:   50.99%
CSMT:   37.19%
sound:   9.73%

IPC≈0.53  context switches≈2647/с
```

Main и CSMT вместе заметно тяжелее `libmali`. Это подтверждает переход от
перебора GL/EBO форматов к producer/queue synchronization.

## 3. CSMT reason profile

В `wined3d_batch12_csreasons.dll` добавлена выключенная по умолчанию агрегатная
телеметрия `MGS2_CSMT_PROFILE=1`. Она разделяет present, queue-full, default
finish, map finish, map/unmap/map_bo/update и consumer idle. При выключенном
флаге QPC-путь не выполняется.

На подтверждённом споте:

```text
finish_default = 0
finish_map     = 12.3–13.2k/с, 232–287ms/с
map            = 6.15–6.62k/с
unmap          = 6.15–6.62k/с
map_bo/update  = 0
present wait   = 0
queue full     = 0
queue depth    = 10.3–10.9KB average, 46–52KB max из 4MB
```

Очередь не заполнена, present не ждёт. Измеренный барьер — примерно 6600
синхронных пар Lock/Unlock в секунду. На этом этапе источник ещё не был
классифицирован; версия про sysmem VB и queued BLT была рабочей гипотезой,
которую последующий census в разделе 6 опроверг.

Профильная DLL:

```text
wined3d_batch12_csreasons.dll
sha256 335e9ef743b34ac58e0b28a53d79351bae21c2bf20660f4bffbe61f1dd5ee309
```

## 4. Исправление повторного запуска PortMaster

Найден независимый launcher-дефект. `rpcss.exe` наследовал fd 9 на
`/tmp/mgs2-substance.lock`, но cleanup завершал другие Wine services и пропускал
`rpcss.exe`. После выхода игры новый запуск молча останавливался на `flock`.

`rpcss.exe` добавлен в точечный cleanup. Remote launcher сохранён как
`launch.sh.bak-20260809-rpcss`, исправленная версия прошла `sh -n` и установлена
с SHA:

```text
d651bd39f5f16a8fdac07a96270d1302976925553b11ee3f09aeae4a11d35e33
```

После завершения проверенного процесса lock освободился, следующий запуск игры
успешен.

## 5. Producer batch4: opt-in VB snapshot

Собран эксперимент `MGS2_D3D8_VB_SNAPSHOT=1`. Для system-memory vertex buffer
D3D8 хранит producer-owned shadow. Lock/Unlock работают с ним без CSMT. Перед
draw использованный диапазон передаётся через `update_sub_resource`, который
копирует байты в принадлежащую очереди upload memory до возврата producer.
Queued command больше не ссылается на изменяемый source VB.

Без флага путь идентичен producer batch3. При невозможности выделить shadow
конкретный buffer автоматически остаётся на штатном пути.

```text
d3d8_producer_batch4_vbsnapshot.dll
sha256 8a6868eb811a0625fc14a28f065d401033d1d4b30aaa4e25f2664745bfc0b3c2
```

Release-сборка прошла без новых warning. DLL установлена отдельно и проверена
byte-wise вместе с batch12. На тяжёлом споте snapshot не изменил главный поток:

```text
finish_map=13.1–14.1k/с, 232–305ms/с
map/unmap=6.59–7.06k/с
queue full=0
fps≈14.0–14.7 с включённым профилем
```

Таким образом, прежняя привязка всех map waits к D3D8 system-memory VB была
неточной. Snapshot не является production-кандидатом; ошибок рендера он не дал,
но измеренный барьер не устранил.

Для следующего единственного census-перезапуска собраны две классифицирующие
DLL. WineD3D делит map на `VB / IB / unbound buffer / texture / RT`, доступ на
`GPU / CPU / both` и режим на `read / write / read-write`. D3D8 одновременно
считает все VB Locks, Locks буферов с отдельным draw-buffer, snapshot Locks и IB
Locks.

```text
wined3d_batch13_mapclass.dll
sha256 16d5bb3d48ece3e2939d3c2d3c5e640b7ef156fb96d9c5062e021ba8135ea1bc

d3d8_producer_batch5_mapcensus.dll
sha256 aefc636e31aecf2d38f6e70cf5e49c0b5afae6acfcfa978ce34a2dcf8bb95d98
```

## 6. Census: настоящий источник map wait

На подтверждённом споте batch13/batch5 дал однозначный результат:

```text
map_bind VB/IB/unbound/texture/RT = 6576–7048 / 0 / 0 / 0 / 0
map_access GPU/CPU/both           = 6576–7048 / 0 / 0
map_rw read/write/both            = 0 / 6576–7048 / 0

D3D8 locks vb                     = 6577–7048/с
D3D8 locks drawbuf/snapshot/ib    = 0 / 0 / 0
sysmem VB/IB uploads              = 0 / 0
```

Все ожидания создают обычные GPU-only vertex buffers. После первого `DISCARD`
существующая D3D8-логика переписывает последующие locks буфера в `NOOVERWRITE`.
На этом GLES backend для них нет доступного mapped client BO, поэтому WineD3D
падает обратно в синхронные CS map/unmap.

## 7. Producer batch7: GPU VB shadow доказан live

Финальный opt-in сохраняет штатный WineD3D path для первого `DISCARD`, но plain
write и `NOOVERWRITE` обслуживает producer-owned shadow. Unlock публикует
`update_sub_resource`; данные копируются в queue-owned upload memory до возврата
приложению, а GL command order сохраняет порядок update и draw.

```text
d3d8_producer_batch7_nooverwrite_shadow.dll
sha256 a597f8db2c0b8493c4006ac2c1673423deb99fb90585f42af45bce11347b073a
MGS2_D3D8_VB_SNAPSHOT=1
```

Один тяжёлый спот, 1416 МГц, одинаковые batch13/hash-cache и диагностические
флаги до и после:

```text
                         baseline             GPU shadow
map/unmap                6576–7048/с           21–23/с
map wait                 237–292ms/с           4.4–6.4ms/с
snapshot locks           0                     9824–10761/с
queue full               0                     0
queue depth max          45–53KB               77–81KB из 4MB
fps                      13.65–14.49            20.83–21.93
```

Map round-trips уменьшились на 99.7%, измеренное ожидание — примерно на 98%.
Несмотря на выросший throughput и число Locks, очередь осталась далека от
лимита. FPS с тем же профилем вырос примерно на 50%. В логах нет GL errors,
page faults или failed updates. Пользователь подтвердил корректность картинки
именно на batch7.

## 8. Production decision

После live-проверки в PortMaster production включён следующий стек:

```text
MGS2_WINED3D_DLL=wined3d_batch13_mapclass.dll
MGS2_BATCH=1
MGS2_BATCH_RESTART_HOIST=1
MGS2_BATCH_HASHCACHE=1
MGS2_BATCH_TRIANGLES=0

MGS2_D3D8_DLL=d3d8_producer_batch7_nooverwrite_shadow.dll
MGS2_D3D8_PRODUCER=1
MGS2_D3D8_VB_SNAPSHOT=1

MGS2_CSMT_PROFILE=0
MGS2_D3D8_PROFILE=0
MGS2_D3D8_STATS=0
MGS2_GL_STATS=0
WINEDEBUG=-all
```

Production wrapper сохранён перед заменой как
`MGS2-Substance.sh.bak-20260809-pre-vbshadow`. Новый wrapper прошёл `sh -n` и
имеет SHA `69a5ed9a1ab52aaddb7a8134caaff91b419ad7b72133249c59a56bf9c117db4b`.

После production-перезапуска обе смонтированные DLL совпали byte-wise с
артефактами. Переменные процесса подтверждают hash-cache и VB shadow; все
диагностические флаги равны нулю. Игра запущена успешно, профильных строк и
runtime errors в production-логе нет. Частотная лестница и thermal guard не
изменялись.

## 9. Новый предел после GPU shadow

Старые skip-draw и perf из разделов 1–2 были сняты до устранения map waits,
поэтому на production batch7 они повторены без горячих профайлеров. Один процесс,
тот же спот, фиксированные 1416 МГц:

```text
normal       21.36 fps   46.82 ms
skip-draw    29.50 fps   33.90 ms
```

Normal draw после окна восстановлен автоматически. Текущие batched GL draws
стоят примерно 12.9 ms/кадр, а CPU-side путь без них почти достигает внутреннего
предела 30 fps. Новый 20-секундный perf:

```text
threads: main 56.28%  CSMT 33.76%  sound 7.77%
DSO:     JIT 53.75%   unknown 13.37%  box86 8.94%  libmali 9.42%
lost samples = 0
```

Фактическая release-команда отдельно проверена: и WineD3D, и D3D8 компилируются
с `-DMGS2_RELEASE -O2`.

## 10. EXT_buffer_storage: extension есть, entry point отсутствует

В `wined3d_batch14_storageprobe.dll` добавлен однократный opt-in probe:

```text
wined3d_batch14_storageprobe.dll
sha256 076c851a3632b939328c3d4f23526a5bb726ef5265ca111ee19e2aef1b4e7137

MGS2BUFFERSTORAGE: ext=1 core=00000000 extproc=00000000 usable=0
```

`GL_EXT_buffer_storage` рекламируется, но EGL-backed WGL dispatch возвращает
NULL и для `glBufferStorage`, и для `glBufferStorageEXT`. Поэтому persistent
mapped VB на этом libmali недоступен; насильно включать ветку нельзя.

Параллельно исправлена заготовка Box86 A/B: обе руки оставляют
`SAFEFLAGS=0`, `BIGBLOCK=2`, `CALLRET=1`, меняется только `FORWARD=512/1024`.
Текущий процесс byte-wise подтвердил production-параметры. Сборка Box86 —
`v0.3.9 0579f8b`; пользовательского `.box86rc`, меняющего MGS2, не найдено.

## 11. VB census и dirty-range aggregation

После закрытия persistent-map собран лёгкий census:

```text
d3d8_producer_batch8_vbcensus.dll
sha256 bd0ba692e8b71975ba690f63f37f1005969fa0e65ffa9d8799c01c493190997b
```

На подтверждённом споте он показал необычно сильную возможность агрегации:

```text
locks/unlocks       466.7–466.9/кадр
update commands     466.7–466.9/кадр
upload bytes        218.0KB/кадр
merged commands     1.0/кадр
merged bytes        218.0KB/кадр
overflow            0
```

Игра сначала заполняет один GPU VB сотнями маленьких Lock/Unlock, затем начинает
рисование. Поэтому можно оставить байты неизменными, но заменить примерно 467
CS update-публикаций одной.

`d3d8_producer_batch9_dirtyaggregate.dll` на Unlock только расширяет dirty-range
producer shadow. Перед первым draw, использующим VB, старые pending draws сначала
публикуются, затем один `update_sub_resource` копирует объединённый диапазон в
queue-owned storage. Это сохраняет исходный порядок update/draw.

```text
d3d8_producer_batch9_dirtyaggregate.dll
sha256 21d000313ea52413e75f6c910a2695732d0e6e09717f8ade4e689f09e4bb03de
MGS2_D3D8_VB_DIRTY_AGGREGATE=1
```

Одинаковый census, спот и 1416 МГц:

```text
                         batch7 baseline    dirty aggregate
update commands/frame          466.8              1.0
upload bytes/frame             218KB              218KB
factor                           8.60               8.63
fps                             21.18              22.72
frame ms                        47.22              44.02
```

Frame time сократился на 3.20 ms, или примерно 6.8%. В окне нет GL errors,
failed updates, fallback или cache eviction.

## 12. Обновлённый production

После live-проверки production D3D8 переключён на batch9:

```text
MGS2_D3D8_DLL=d3d8_producer_batch9_dirtyaggregate.dll
MGS2_D3D8_PRODUCER=1
MGS2_D3D8_VB_SNAPSHOT=1
MGS2_D3D8_VB_DIRTY_AGGREGATE=1
MGS2_D3D8_VB_CENSUS=0
```

WineD3D остаётся на проверенном batch13 с hash-cache и restart hoist. Все
профильные флаги выключены. Следующий измерительный шаг — production без census
на 1416/1608/1800 МГц после охлаждения устройства; форсировать верхние частоты
при температуре 81–83 °C нельзя.

## 13. Финальный batch OFF/ON на новом producer

Старый consumer A/B был снят до GPU shadow и dirty aggregation, поэтому на
актуальном producer batch9 выполнены две пары live-переключений. В первом окне
получено примерно `12.25 → 20.38 fps`, во втором `13.57 → 25.75 fps` при
`MGS2_BATCH=0 → 1`. Форма нагрузки заметно менялась между arm, поэтому эти
числа нельзя использовать как точную процентную оценку. Однако знак повторился
и велик: текущий indexed batcher остаётся обязательной частью production, а не
нейтральным историческим патчем.

## 14. Census и отрицательный expanded-VBO

Лёгкий census на тяжёлом споте подтвердил пригодность данных для single-stream
эксперимента:

```text
DrawPrimitive                 ≈1299/кадр
TRIANGLESTRIP                 ≈1296/кадр
active streams               0/1299/0/0
compatible                   ≈1296/кадр
reject state/stream/shadow    0/0/0
stride                       avg 35.8, min 16, max 40
source bytes                 ≈0.99MB/кадр
expanded bytes               ≈2.70MB/кадр
```

Артефакт `d3d8_producer_batch11_expandedvbo.dll` преобразует совместимые strip
в `TRIANGLELIST`, копирует вершины из producer shadow в один из четырёх
GPU-only ring buffer и выполняет один non-indexed draw на пакет до 64 исходных
draw. Production-путь при выключенном флаге не меняется.

```text
sha256 71284077f7c453e5f6cbbde07169b8da22b8bae7bb03d4b4136487080363904d
MGS2_D3D8_VBO_EXPAND=1
```

Live-проверка закрыла этот вариант как регрессию. На споте механизм работал без
fallback и overflow, factor был примерно `13–15x`, но present упал до `5–7/с`.
Наблюдавшийся upload составлял около `49–53KB/кадр`; значит уже сама комбинация
queue-owned update, временной смены stream/topology и draw этого пути слишком
дорога либо создаёт сериализацию. Точную внутреннюю составляющую не
профилировали: пользовательский результат достаточен, чтобы не продолжать этот
вариант и не включать его в production.

После теста процесс остановлен. PortMaster снова запущен с production batch9;
обе смонтированные DLL проверены byte-wise, expanded-VBO переменных в процессе
нет.

Первый вариант всё же содержал конкретный уже знакомый дефект: несколько
`update_sub_resource` записывали разные диапазоны одного BO между draw'ами того
же кадра. Исправленный `batch12_vbopool` выдаёт каждому batch отдельный BO из
четырёх покадровых пулов; BO повторно используется не раньше чем через четыре
кадра.

```text
d3d8_producer_batch12_vbopool.dll
sha256 60d264c70ec5f6f2a2d16dabc7e3434fb15e7967ed9f7558b1c00eec5593532a
```

На том же тяжёлом споте pool устранил большую часть катастрофической регрессии,
но не превзошёл production:

```text
present                    17–18/с
source draws               ≈1294/кадр
expanded batches           ≈155–157/кадр
factor                     8.29–8.36x
expanded upload            2.70MB/кадр
fallback / overflow        0 / 0
new BO after warmup         0
```

Это чистый отрицательный результат: same-BO synchronization была реальной
частью первой регрессии, однако даже без неё CPU-развёртка и передача 2.70MB
вершин на кадр дороже проверенного synthetic-index пути, который на этом стеке
давал около 22.7 fps. Expanded-VBO направление закрыто; pool не включён в
production.

## 15. Первый точный ntsync capture

`stall_watch4.py` поймал паузу main длиной `1511.4ms`. Главный поток находился
в compat `ioctl(fd=11, NTSYNC_IOC_WAIT_ANY)` и ожидал три ntsync object fd
`15/16/17`; kernel stack заканчивался в `ntsync_schedule`. Wineserver в это
время находился в `epoll`.

Это пока не объяснение игровых стопов: capture сделан в начале запуска, когда у
процесса был один поток и `wined3d_cs` ещё не существовал. Декодированный wait
имел realtime deadline ещё примерно через `8.44s`, то есть это нормальное
загрузочное ожидание с конечным timeout, а не зависший renderer.

Watcher исправлен: новый запуск с `--require-cs` армируется только после
появления CSMT, а decoded wait печатает deadline и оставшееся время. Следующий
полезный capture надо снимать после загрузки игры, отдельно от FPS-тестов.

## 16. Production frequency sweep: практический потолок 1800 МГц

На одном непрерывном production-процессе, на подтверждённом споте и без горячих
профайлеров снято по 20 секунд на каждом CPU cap. Между arms менялся только cap;
batcher оставался в штатном режиме с hash-cache, restart hoist и dirty-range
aggregation.

```text
cap MHz   fps    frame ms   temperature at window end
1416      23.20    43.10          72.78 °C
1608      26.26    38.07          73.33 °C
1800      26.96    37.10          74.44 °C
1992      27.01    37.03          76.25 °C
```

В этой сцене 1992 МГц не даёт измеримого выигрыша относительно 1800 МГц
(`+0.05 fps`, `-0.07 ms`), но добавляет нагрев. После прогона лимит live
возвращён на 1800 МГц. Это текущий практический sweet spot для длительного
теста; launcher пока не менялся — его штатная лестница и thermal guard остаются
страховкой до отдельного длительного soak-прогона.

## 17. Подготовлен STATE_BARRIER_CENSUS

Исходник подтвердил конкретную потерю агрегации: `SetRenderState` и
`SetTextureStageState` вызывают `d3d8_mgs2_mark_state_dirty()` до уже
существующего fast-path для идентичного значения. Поэтому setter возвращает
`D3D_OK`, но следующий `DrawPrimitive` всё равно осушает pending batch.

Собрана отдельная DLL без изменения поведения:

```text
d3d8_producer_batch13_barriercensus.dll
sha256 5a2eca6e1be85ff2e4ac9a5ae4a93bd09f5db64a885d218e06eed22b13048cbb
MGS2_D3D8_BARRIER_CENSUS=1
```

Один раз в секунду она печатает `MGS2BARRIER`. Для `rs`, texture-stage (`tss`)
и sampler (`samp`) формат полей — `calls / redundant / redundant_with_pending /
pending_source_draws`. Последнее поле непосредственно оценивает, сколько
исходных draw уже было в batch, который идентичный setter потенциально разрезал.
Флаг выключен по умолчанию; без него нет ни отчёта, ни счётчиков.

Первый запуск census исключён: его начальная ревизия после печати обнуляла
timestamp вместе со счётчиками и поэтому логировала на каждый `Present`. Процесс
сразу остановлен, таймер исправлен, и итоговая DLL выше печатает ровно одну
строку в секунду.

На подтверждённом споте, в 30-секундном окне при 1416 МГц и 72.78–73.33 °C:

```text
rs calls                  5.19–5.83k/с    redundant=0
tss calls                 220–276/с       redundant=0
sampler calls             176–192/с       redundant=0
redundant_with_pending    0 во всех трёх классах
pending_source_draws      0 во всех трёх классах
```

Итак, уже существующие bit-identical fast-path для render, texture-stage и
sampler state в этой сцене не срабатывают. Перенос `mark_state_dirty()` после
этих проверок был бы формально корректным, но не даёт измеримого выигрыша;
state-barrier dedup в этом направлении закрыт и в production не меняется.

После census экспериментальный процесс остановлен. Запущен обычный production
стек (`wined3d_batch13_mapclass.dll` +
`d3d8_producer_batch9_dirtyaggregate.dll`), byte-wise выбранные артефакты
проверены, все diagnostic flags равны нулю. Для этого запуска верхняя ступень
runtime-лестницы задана измеренным sweet spot `1800 → 1608 → 1416 МГц`; сам
launcher по-прежнему не редактировался.

## 18. `GL_EXT_buffer_storage`: WGL bridge подтверждён

Старый probe из раздела 10 правильно показывал отсутствие entry point в
тогдашнем WGL dispatch, но не отсутствие функции в самом Mali: активный
production использует `opengl32_glesver1.so`, а не старый EGL facade. В
`libmali.so.1.10.0` есть `glBufferStorageEXT`, и `GL_EXT_buffer_storage`
рекламируется.

В отдельном `opengl32_bufferstorage_bridge.so` в существующую таблицу GLES
spellings добавлено ABI-совместимое сопоставление
`glBufferStorage → glBufferStorageEXT`. Оно проходит через обычный Box86
WGL thunk, поэтому x86 приложению не передаётся ARM native pointer.

```text
opengl32_bufferstorage_bridge.so
sha256 d20902e03eb472c0b8768bcf0a15264797e7ddd5966dbe32a1b1df3a05f74db6

MGS2BUFFERSTORAGE: ext=1 core=798FD5D0 extproc=00000000 usable=0
```

`core` стал ненулевым на холодном запуске с `wined3d_batch14_storageprobe`:
доступная вызываемая точка входа подтверждена. Поле старого probe `usable`
смотрит только на literal `glBufferStorageEXT`, поэтому его `0` после bridge
не является отрицательным результатом. Запуск прошёл без renderer errors и
сразу завершён.

Persistent-map путь всё ещё не включён: ему нужен отдельный opt-in код,
проверка корректности и A/B на споте. Обычный production затем восстановлен
на `wined3d_batch13_mapclass.dll` +
`d3d8_producer_batch9_dirtyaggregate.dll`, с `opengl32_glesver1.so`,
выключенными diagnostics и runtime-лестницей `1800 → 1608 → 1416` МГц.

## 19. Новый normal / skip-draw на batch9 при 1800 МГц

После dirty-range aggregation старый skip-draw из раздела 9 больше нельзя
использовать как точный budget. На подтверждённом споте снята новая непрерывная
пара `normal → skip-draw → normal` без перезапуска процесса. Менялся только
live-файл `/tmp/mgs2-batch-skip-draw`; в конце он подтверждён равным `0`.
Температура во время пары была 71.67–73.89 °C.

Первый normal arm ещё прогревал cache и форму сцены, поэтому для расчёта взята
вторая, уже стабилизировавшаяся пара. Первый skip sample (`28.91 fps`) содержит
переходный кадр и исключён:

```text
mode                 samples      fps         frame ms
normal after restore 13           27.83       35.93
skip-draw steady     19           38.54       25.95
draw budget                                     9.98
```

Таким образом, на актуальном production batch9 batched GL draws всё ещё стоят
примерно 10 ms/кадр, или около 28% normal frame time. CPU-side путь без этих
draw имеет запас выше 30 fps; до 30 fps в normal не хватает порядка 2.6 ms.
Следующая ветка должна экономить именно цену GL draw / их формы, а не повторять
CPU state-dedup или expanded-VBO. Лог пары сохранён как
`logs/mgs2-skipdraw-1800/20260809-production-normal-skip-normal.log`
(sha256 `03313ed0df6313981dca9a94e0392dbe8ce3f9c55a97a627fcabf6bb8cae4029`).

## 20. Отрицательный degenerate-strip experiment

Как недорогая альтернатива expanded-VBO собран opt-in
`wined3d_batch15_degeneratestrips.dll`. Он не разворачивает вершины и не меняет
topology на `TRIANGLELIST`: вместо primitive restart между уже совместимыми
`TRIANGLESTRIP` добавляет только вырожденные индексы. Мост дублирует последний
индекс предыдущего strip и первый индекс следующего так, чтобы первый настоящий
треугольник следующего strip начинался с чётной глобальной parity; winding
сохраняется. Внутренний startup self-test перебирает длины обоих strip от 3 до 8
и проверяет отсутствие ненулевых bridge triangles и правильную parity.

```text
wined3d_batch15_degeneratestrips.dll
sha256 cd9037be814717035e625c979c833d944356a15e80ea13f16823445599dcaeee
MGS2_BATCH_DEGENERATE_STRIPS=1

MGS2DEGENERATE: bridge selftest PASS
MGS2CACHE: triangles=0 degen=1 hash=1 skip=0
```

На подтверждённом споте при 1800 МГц 25-секундное окно дало 25.00–28.94 fps.
Фактор batching остался 8.54–8.77, а число опубликованных batch не уменьшилось:
ветка устранила restart state, но не GL draw calls. В логе нет renderer errors,
failed updates, page faults, assert, fallback или arena overflow, однако даже
на стабилизировавшемся cache нет выигрыша над зафиксированным normal production
`27.83 fps`. При 78.13–78.75 °C продолжать прогрев ради точного A/B неразумно.

Итог отрицательный: primitive restart не является заметной ценой текущего
draw budget. `batch15` не включён в production; после теста обычный batch13 +
batch9 восстановлен.

## 21. Текущая runtime-лестница по явному запросу: верхняя ступень 1992 МГц

Раздел 16 по-прежнему показывает, что 1800 МГц — измеренный practical sweet
spot и 1992 МГц не добавляет заметной производительности на данном споте.
Однако по явному запросу пользователя production-процесс перезапущен с полной
верхней runtime-лестницей:

```text
MGS2_FREQ_STEPS="1992000 1800000 1608000 1416000"
```

`scaling_max_freq` подтвердил 1992000. Запущен обычный production-стек
`wined3d_batch13_mapclass.dll` (SHA
`16d5bb3d48ece3e2939d3c2d3c5e640b7ef156fb96d9c5062e021ba8135ea1bc`) +
`d3d8_producer_batch9_dirtyaggregate.dll` (SHA
`21d000313ea52413e75f6c910a2695732d0e6e09717f8ade4e689f09e4bb03de`).
`MGS2_BATCH_DEGENERATE_STRIPS=0`; все profile/census/probe flags равны нулю.
На подтверждении запуска температура была 79.38 °C, ошибок запуска нет.
Это изменение режима, а не новая рекомендация по efficiency: thermal guard и
нижние ступени сохранены, launcher не редактировался.

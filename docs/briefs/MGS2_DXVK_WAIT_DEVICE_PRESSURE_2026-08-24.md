# DXVK gameplay gap: Win32 waits и давление RG353VS (2026-08-24)

## Решение перед следующим фиксом

Повторяющийся gap около `1.62 s` нельзя больше называть чисто игровым или
чисто консольным. Триггер приходит из игры при загрузке/появлении объектов, но
две разные части задержки ведут себя по-разному:

- первый тяжёлый load-gap действительно усиливается 1 ГБ памяти, paging и SD;
- повторяющийся gameplay-gap не объясняется троттлингом, GPU downclock,
  memory pressure или ожиданием накопителя;
- в последнем случае консоль продолжает интенсивно выполнять CPU-работу через
  `Box86 -> Wine -> DXVK`, а игровой main loop делает десятки тысяч
  `PeekMessageA -> game tick -> Sleep(0)` проходов в секунду.

Поэтому был проведён ограниченный A/B не очередного asset decoder, а этого
CPU/scheduler amplification: caller-specific 1 ms wait только для `Sleep(0)`
после пустого `PeekMessageA`. Оба плеча использовали одинаковые bytes.

Результат разделил два эффекта. Wait заметно снизил CPU load и дал
исследовательское направление для steady throughput, но повторяющийся hitch
остался `1.59--1.60 s`. Гипотеза busy loop как основной причины фриза
отвергнута. `FINALPLAY16` не изменён; кандидат остаётся default-off.

## Почему предыдущая DXT-картина была недостаточна

Побитово проверенный native DXT сократил texture-worker samples с `287` до
`24`, но целевой gap изменился с `1619.763 ms` только до `1629.996 ms`. Значит
распаковка DXT через Box86 совпадала с остановкой по времени, но не находилась
на wall-clock critical path. Продолжать оптимизировать тот же decoder после
такого refuting result нельзя.

Статический разбор точного EXE затем нашёл два правдоподобных game-level wait:

- deadline-функция `0x8a1ea0`, QPC return `0x8a1eaf`, Sleep return
  `0x8a1f0e`;
- loading loop с `Sleep(96)` и return `0x8eecfa`.

Новый bounded census был нужен, чтобы проверить их во время того же gap, а не
считать найденный код активным по одному наличию в EXE.

## Прибор: три итерации и observer effect

Research-only Wine `kernelbase` записывает в фиксированную memory table только
прямые PE-calls игры к `Sleep[Ex]` и object waits. На hot threads нет времени и
I/O; внешний reader раз в 20 ms читает таблицу через `/proc/PID/mem` и
сопоставляет её с memory-only DXVK PRESENT counter.

| Версия | SHA-256 | Результат |
|---|---|---|
| v1 | `d44f47...` | перехватывала QPC; один старт выжил, последующие получили crash/black screen; отвергнута как слишком инвазивная |
| v2 | `f3e430dec19c...` | QPC оставлен штатным; полный правильный route, но считался hot `Sleep(0)` |
| v3 | `115247fb3a44...` | QPC штатный, `Sleep(0)` полностью исключён из counters; полный правильный route |

V2 насчитал `7,034,405` вызовов `Sleep(0)` с return `0x4011a8` за `129.37 s`,
то есть около `54.4k/s`. Сам counter write на каждом вызове увеличил два
повторяющихся gap до `1670.048/1690.018 ms`. V3 снял эту запись с hot path, и
gap вернулся к `1619.940/1622.912 ms`, совпав с прежним control
`1619.763 ms`. Это отдельный измеренный observer effect и причина не
использовать per-call counters в следующем A/B.

V3 patch record:

```text
7dd5f1907c59f6bbe1685dcb686f00598613cd9491584b9575fc6707683fc47e
wine-patches/01-wait-census-research-default-off.patch
```

## Правильность маршрута и live identity

Полный system-pressure run:

```text
/storage/roms/ports/ablogs/dxvk-device-pressure-v3-profile1-20260824
autoload_rc=0
CPU during capture=1992000 kHz
Box86=83f9349c6dc26f8f769e714a5ed57c4d76f3a523161ead31f75e52ccc1da7fba
user32=1635f4c6917dc54f6764e1fceddd39b4ce04692a93a88f473fa6cbcf03d83d84
kernelbase=115247fb3a44b1d03122b2b0f2f649b0f95115b4c1a31c90286945dc56c6cda1
```

Screenshot gates показали именно `LOAD GAME`, строки сохранений
`09 -> 08 -> 07`, правильный yes/no и loaded gameplay:

```text
menu new/load: 0.474/0.206, затем 0.199/0.474
save row 09/08/07: mean 0.686, next 0.115
screen gray mean: 0.206
```

После завершения не осталось экземпляров игры или bind mount; системный
`kernelbase.dll` восстановлен с SHA
`3c5e1ff7f9d82cfa62e28617aacc283155a07b15fe7639e4daf60ff1d6aa17c5`.

## Win32 wait census: что отвергнуто

Во всём 129-секундном route не было ни одного вызова deadline-Sleep с return
`0x8a1f0e`. Следовательно, аналог `ActorWait`, найденный около `0x8a1ea0`, не
создаёт этот gap.

В load-gap `2689.999 ms` caller `0x8eecfa` сделал только два `Sleep(96)`, всего
`192 ms`. Это реальный loading wait, но он не объясняет оставшиеся примерно
`2.5 s`.

В recurring gap `1622.912 ms` видны главным образом infinite object waits:

```text
0x8eb0ed tid 260: 336 calls, active samples across ~1640 ms
0x8a6a6a tid 216: 4 calls, active samples across ~1620 ms
0x8eb0ed tid 268: 12 calls, active samples across ~1460 ms
```

`0x8eb0ed` — общий wrapper `WaitForSingleObject(handle, INFINITE)`, который у
одного worker возвращается примерно 200 раз в секунду. Наличие active wait у
нескольких worker threads нормально и само по себе не доказывает, какой из них
удерживает main thread. Census отверг finite game deadline, но не даёт права
патчить произвольный infinite wait.

## Внешняя телеметрия консоли

`harness/device_pressure_count.py` читает систему раз в 100 ms, хранит не более
2400 строк в RAM и пишет TSV только при остановке. Он не создаёт периодические
записи на `/storage`. Сняты per-core CPU, process faults/RSS/swap, Linux PSI,
`vmstat`, `meminfo`, глобальные `mmcblk0` counters, CPU/GPU clocks и температуры.
ROCKNIX не предоставляет `/proc/PID/io`, поэтому byte counters процесса равны
нулю, а block I/O остаётся system-wide.

Linux PSI `some` измеряет долю времени, когда хотя бы часть задач stalled на
ресурсе, `full` — когда одновременно stalled все non-idle tasks. В block stat
`io_ticks` — время, когда у устройства были queued requests. Поэтому
`io_ticks=0` вместе с `io PSI=0` является более сильным отрицательным
результатом, чем просто малое число прочитанных байт.

### Первый load-gap: консоль участвует материально

Для `2689.999 ms`:

```text
process major faults: 1426
swap in/out:          1336 / 5171 pages
memory PSI some/full: 2.53% / 2.27%
I/O PSI some/full:    2.76% / 2.17%
mmc read:             19.848 MiB
mmc active:           336 ms
MemAvailable min:     218028 KiB
process VmSwap max:   73068 KiB
```

Ограничение памяти и paging на 1-GB RG353VS явно добавляют работу к первой
загрузке. Но даже здесь SD active только `336 ms` из `2690 ms`, поэтому один
накопитель не объясняет всю паузу.

### Повторяющийся 1.62-s gap: не SD, не RAM, не температура

| gap | CPU / hottest core | CPU PSI | I/O PSI | memory PSI | mmc active | clocks | max temp CPU/GPU |
|---:|---:|---:|---:|---:|---:|---|---:|
| `1622.912 ms` | `65.5% / 94.2%` | `8.39%` | `0.90/0.84%` | `0.12/0.10%` | `188 ms` | `1992/800 MHz` | `73.3/68.1 C` |
| `1619.940 ms` | `70.0% / 100%` | `10.85%` | `0.14/0.04%` | `0.76/0.58%` | `4 ms` | `1992/800 MHz` | `70.6/64.4 C` |
| `879.996 ms` | `70.2% / 99%` | `11.66%` | `0/0%` | `0/0%` | `0 ms` | `1992/800 MHz` | `70.0/64.4 C` |

Один exact-size gap имел почти нулевой I/O, следующий меньший gap — строго
нулевой. CPU и GPU не снижали частоту, температуры далеко от 84 C guard.
Следовательно, общий recurring механизм не является SD wait, global reclaim,
swap thrash или thermal throttling. Его подпись — CPU/scheduler contention в
compatibility stack при продолжающейся работе нескольких потоков.

### Caveat: посторонний процесс DMC3

На устройстве остался старый рекурсивный `grep` по каталогу DMC3 (`PID 29377`).
Он не относится к MGS2, поэтому system-wide I/O формально может включать его.
После прогона двухсекундный before/after показал идентичные CPU ticks
`448+890` и полностью неизменившиеся `mmcblk0` counters: в этот момент процесс
был неактивен. Его состояние не снималось в течение всего route, поэтому
положительные глобальные I/O числа сохраняют этот caveat. Отрицательные gaps с
`io PSI=0` и `mmc active=0`, а также per-process MGS2 counters этим не
опровергаются.

## Falsifiable hypothesis перед A/B

Точный main loop:

```text
0x401174  PeekMessageA(..., PM_NOREMOVE)
0x401178  если очередь пуста -> 0x40119b
0x40119b  один game tick через 0x8a41d0
0x4011a2  Sleep(0)
0x4011a8  следующий проход
```

Под Wine `Sleep(0)` доходит до `NtDelayExecution(0)`, который вызывает
`NtYieldExecution`; production не включает исторический fast-yield override.
Измерены примерно `54.4k` таких emulated loop iterations в секунду. Вместе с
`8-12% CPU PSI`, одним насыщенным core и отсутствием I/O pressure это даёт
конкретную гипотезу: во время first-use work главный busy loop забирает CPU и
усиливает scheduler/worker synchronization на четырёх Cortex-A55.

Кандидат меняет только `Sleep(0)` с immediate return `0x4011a8` на 1 ms
реального ожидания. Refuting result был заранее определён:

- если recurring gap остаётся около `1.62 s`, busy loop является нагрузкой, но
  не причиной hitch, и кандидат отклоняется;
- если gap сокращается при тех же live bytes, route и clocks, затем нужен
  обратный A/B и correctness witness до любой promotion;
- даже при выигрыше startup/load paging остаётся отдельной задачей и не должно
  приписываться этому фиксу.

## Sleep(0) A/B: итог перед паузой

Research kernelbase содержал wait census v3 и incremental patch
`02-sleep0-wait-research-default-off.patch`:

```text
5a30c4a0b9a0581c5e3bc7136225eed8dc4e62e7222b5733e5b7e16215674f59
kernelbase_wait_census_sleep0ab1.dll
```

Два no-input smoke-test прошли при `MGS2_SLEEP0_WAIT_MS=0` и `=1`: live SHA
совпал, title frame прошёл size gate, wait census сообщил `enabled=1` и
`overflow=0`. Затем на одном сохранении выполнены полные последовательные
control/candidate route. В обоих `autoload_rc=0`, визуальные LOAD GAME gates
совпали, CPU/GPU оставались `1992/800 MHz`, а DMC3 `grep` имел полностью
одинаковый `/proc/PID/stat` до и после каждого route.

| Метрика | control `0 ms` | candidate `1 ms` | разница |
|---|---:|---:|---:|
| full-route average FPS | `38.428` | `41.811` | `+8.8%` |
| first load gap | `2631.072 ms` | `2599.973 ms` | `-31.099 ms` |
| recurring gap после `key:6-loaded` | `1699.992 ms` | `1590.057 ms` | `-109.935 ms` |
| recurring gap после `shot:6-loaded` | `1639.651 ms` | `1601.360 ms` | `-38.291 ms` |
| следующий loaded gap | `1039.997 ms` | `868.867 ms` | `-171.130 ms` |
| gaps `>=50/500/1000 ms` | `95/6/6` | `45/6/4` | направление смешанное |

CPU-подпись доказывает, что ветка действительно сработала, а не повторила
ошибку no-op A/B:

| Интервал | CPU control -> candidate | process ticks | voluntary ctx |
|---|---:|---:|---:|
| `key:6-loaded` recurring | `70.4% -> 52.2%` | `385 -> 234` | `1 -> 1277` |
| `shot:6-loaded` recurring | `65.5% -> 41.6%` | `363 -> 196` | `3 -> 1330` |

Wait заменяет busy yield настоящим планируемым ожиданием и существенно
освобождает Cortex-A55. Это согласуется с прежним WineD3D-направлением около
`+11% FPS`, но сегодняшний full-route average не является fixed-spot ABBA и не
достаточен для production performance claim.

Главный заранее выбранный refuting result сработал: оба целевых gap всё ещё
около `1.6 s`, а object-wait подпись сохраняется на всю паузу. Следовательно:

1. hot Peek/Sleep(0) loop — реальная CPU-нагрузка совместимости;
2. он может усиливать hitch на десятки миллисекунд, но не задаёт его основную
   длительность;
3. продвигать этот patch как «freeze fix» нельзя;
4. перед возможным throughput promotion нужен обратный `1 -> 0` прогон и
   fixed-scene correctness/latency witness;
5. поиск владельца основного `~1.6 s` условия должен продолжиться только после
   нового research cycle, не в этой зафиксированной паузе.

## Артефакты, provenance и rollback

Tracked:

- `wine-patches/01-wait-census-research-default-off.patch`;
- `wine-patches/02-sleep0-wait-research-default-off.patch`;
- `harness/wait_census_read.py`;
- `harness/dxvk_wait_gap_analyze.py`;
- `harness/device_pressure_count.py`;
- `harness/dxvk_device_gap_analyze.py`;
- `harness/dxvk_hitch_profile_capture.sh`;
- `device/launch-dxvk-sarek-wait-census.sh` и его fail-closed manifest.
- `device/launch-dxvk-sarek-sleep0-wait.sh` и его fail-closed manifest.

Ignored raw trace hashes:

```text
cca442359c4af3b020100c83d46266dd5bef05fe000d5a9badc2901c4c72db05  device-pressure.tsv
3b23b33fd49e8cbbdbabdae20e0599c93c153cb1cade3e2935f7c17537a19327  present.tsv
1970c8b9ce7554c4db399805ca2f1cf247e3bed36c95ed81d514d03c0fed5b33  wait-census.tsv

0af0034e0bfedec3bb0f5afd83c9655ca0c2f573fb0a174db5f2306317544a4e  control present.tsv
4b67a4bfa5c0527130e1db3b4e417d0fdfa1a6c6c40e769282a0f2ee8daebaf0  control device-pressure.tsv
fadb9eb109414927ea246af33d620241fa297606c2a1c300cd351e7f3bbf7c1c  control wait-census.tsv

187019eebb31037249a078946565dcdc8aa6ac77c3bf722d79eca49f806f23d1  candidate present.tsv
940bd8c38cd68971d59c50c95d7c1d913996ef2ac3d5e5c1db607c856b9bc0b7  candidate device-pressure.tsv
f4eb186bfd7a2c67131aedab220d947fd9e6cb08d08e660dd6b4fed3153bdb14  candidate wait-census.tsv
```

Production rollback не менялся:

```sh
MGS2_RENDERER=wined3d /storage/roms/ports/MGS2-Substance.sh
```

Источники интерпретации kernel counters:

- <https://www.kernel.org/doc/html/latest/accounting/psi.html>
- <https://cdn.kernel.org/doc/html/latest/block/stat.html>

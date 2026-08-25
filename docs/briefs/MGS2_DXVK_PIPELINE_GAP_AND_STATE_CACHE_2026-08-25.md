# DXVK pipeline gap, Mali и state-cache A/B (2026-08-25)

> Status update: the initial decision below was superseded by the later
> corrected FINALPLAY16 A-B-A-B and clean normal-entry gate. FINALPLAY17 is now
> production; see the final sections of this brief and the linked production
> record.

## Initial decision before the later gates

На этом промежуточном этапе `FINALPLAY16` не был изменён. Тогда в production
оставалось:

```text
D3D8 -> DXVK-Sarek 1.11.1 -> WineVulkan/Wayland -> proprietary armhf libmali
DXVK_STATE_CACHE=0
```

Новый внешний trigger и повторный разбор старого perf разделили два похожих
по длительности gap, которые раньше ошибочно рассматривались как один общий
`~1.62 s` механизм:

1. gap примерно через 8 секунд после подтверждения `LOAD GAME` -- синхронная
   компиляция нового Vulkan graphics pipeline внутри нативного ARM
   `libmali`; в control её вызывает `dxvk-cs`;
2. gap примерно через 4 секунды после loaded screenshot -- отдельный игровой
   worker/read path; `dxvk-cs` не является его постоянным владельцем.

Штатный DXVK state cache прошёл correctness, создал стабильный файл и на warm
run действительно перенёс первую компиляцию на `dxvk-shader`, но не убрал
паузу. Первый warm gap стал `2289.905 ms` вместо cold `1590.021 ms`; в нём
одновременно работал `dxvk-shader`, а memory/I/O pressure был выше. Одной пары
недостаточно для количественного утверждения о регрессии, но заранее заданный
критерий «warm cache устраняет first-use gap» опровергнут. Cache нельзя
продвигать как freeze fix.

Research-only Sarek async также проверен и отвергнут. С default threshold `5`
он пропустил один draw, но практически дословно повторил cache-off control:
pipeline gap `1600.082 ms` против `1620.229 ms`, первый load gap `2618.433 ms`
против `2651.667 ms`, поздний worker gap `1619.914 ms` против `1630.088 ms`.
При минимальном допустимом threshold `1` он пропустил уже `2227` draw, но
оставил `2699.999 ms` load gap, кластер до `1410.357 ms` после него и
`1730.022 ms` worker gap. Статические screenshots после пауз корректны, но не
могут оправдать тысячи потенциально неполных промежуточных draw. Async не
promoted; production остаётся sync/cache-off.

Нативизация измеренного high-level DXT5 surface-row path дала первый
повторяемый, но частичный выигрыш. В симметричном A-B-A-B resource gap `w18a`
снизился в среднем с `2589.498` до `2370.518 ms` (`-8.5%`), а `w19a` -- с
`1649.907` до `1444.987 ms` (`-12.4%`). Differential verifier сравнил 54 live
вызова без единого байтового расхождения; оба timing arms выполнили по 47,433
нативных вызова. Многосекундные паузы всё равно остались, а независимая
DXVK/libmali-компиляция не исчезла. Кандидат поэтому сохранён как default-off
research record и не promoted в `FINALPLAY16`.

## Точная платформа вместо переноса r44p0-гипотезы

Предложенная извне гипотеза складывала `ZAP_TIMEOUT=1000 ms` и
`RESET_TIMEOUT=500 ms` из другой ревизии Mali DDK. На живом RG353VS она не
соответствует runtime:

```text
kernel       Linux RK3566 7.0.2 PREEMPT, build 2026-08-22
ROCKNIX      25a2ed02c47b0f0a2ff39479de46150d55b70609
kernel DDK   r54p2-02eac0
gpudriver    libmali
/dev/ntsync  present, CONFIG_NTSYNC=y

js_scheduling_period  100
js_timeouts           100 100 5000 5000 1500000 5500 5500 1502000
reset_timeout         3000
soft_job_timeout      3000
```

`js_timeouts` -- восемь millisecond-полей soft-stop/hard-stop/reset для
нормального и dumping context. Нормальные hard/reset окна здесь `5000/5500
ms`; `1500000` относится к dumping context, а не к обычному `1.5 s` reset.
До и после обоих правильных cache runs отфильтрованный kernel log имел один
SHA-256:

```text
ead41e5de5d7fc087f3437dc785d42f4dad494d0bef175fb43aa9980ccfefe3d
```

Новых Mali fault/reset/timeout и MMC error не было. Гипотеза о повторяющемся
Mali reset отвергнута для точного FINALPLAY16 route.

В public manifest тот же userspace blob исторически назван `g29p1`, тогда как
live kernel сообщает `r54p2-02eac0`. Эти две метки нельзя считать доказанной
единой DDK provenance без отдельного vendor record; проверяемым фактом для
userspace остаются bytes:

```text
2b39f4315eec0545e21e5c5498f9125d01e35d7cad4a49a447f002dd7b5e0cbb
Build ID 6cb0f8df9c0b24a2eb4f81be1fb54afdc5057e74
/usr/lib32/libmali.so.1.10.0
```

Описание sysfs-полей находится в исходнике Mali kernel module:
<https://android.googlesource.com/kernel/google-modules/gpu/+/refs/heads/android-gs-raviole-5.10-android13/mali_kbase/mali_kbase_core_linux.c>.

## Прибор без записей из hot threads

`harness/dxvk_gap_trigger_capture.py` внешне читает существующий memory-only
PRESENT counter каждые 10 ms. После `500/1200 ms` без нового PRESENT он:

- дважды читает `/proc/PID/task/*/stat`;
- выбирает main и не более пяти самых активных threads;
- только для них читает `syscall`/`wchan`;
- декодирует compat NTSync WAIT ioctl и его fd-массив через `/proc/PID/mem`;
- хранит не более 12 gap целиком в RAM и пишет результат только при остановке.

Широкого `wchan` polling нет: прежний такой reader сам создавал stalls.
`harness/dxvk_hitch_profile_capture.sh` включает trigger только при
`MGS2_PROFILE_GAP_TRIGGER=1`, а platform/kernel snapshots -- только при
`MGS2_PROFILE_PLATFORM=1`. Оба default-off.

Для async A/B добавлен ещё один default-off внешний reader
`harness/dxvk_async_skip_capture.py`. Он разрешает PE data export из живой
`d3d9.dll`, читает только `/proc/PID/mem`, хранит не более 4096 change-events и
пишет их лишь при остановке. В DXVK hot path находится только один 32-bit
memory increment при фактическом выборе skip; форматирования и файлового I/O
там нет. Patch и точная сборка записаны в
`device/DXVK_SAREK_ASYNC_SKIP_RESEARCH.manifest`.

Полный control route:

```text
/storage/roms/ports/ablogs/dxvk-gap-trigger-v1-full1-20260825
autoload_rc=0
Box86      83f9349c6dc26f8f769e714a5ed57c4d76f3a523161ead31f75e52ccc1da7fba
user32     1635f4c6917dc54f6764e1fceddd39b4ce04692a93a88f473fa6cbcf03d83d84
kernelbase 115247fb3a44b1d03122b2b0f2f649b0f95115b4c1a31c90286945dc56c6cda1
```

Correctness gates доказали `LOAD GAME`, save rows `09 -> 08 -> 07`, yes/no и
loaded gameplay. После run не осталось game instances или mounts; system
Box86/kernelbase восстановились до `706dfcc9...` / `3c5e1ff...`.

## NTSync живой, но main не ждёт его в целевом gap

В процессе были `/dev/ntsync` и 20+ `anon_inode:ntsync` fds. Значит Wine 11
реально использует kernel NTSync, а не только содержит собранный код. Однако в
обоих recurring gap на порогах 500 и 1200 ms:

```text
main tid  state=R  syscall=running  wchan=0  ntsync=not-ntsync-wait
```

Infinite NTSync waits с owners `212/216` принадлежали фоновым worker threads и
одинаково присутствовали в unrelated gaps. Полный handle-ownership ring и
NTSync ON/OFF поэтому больше не являются первым экспериментом: они следили бы
за постоянными worker waits, а не за командой, после которой возобновляется
PRESENT. NTSync остаётся проверенной частью runtime, но не владельцем этой
паузы. NTSync -- одна из основных функций Wine 11:
<https://www.winehq.org/news/2026011301>.

## Повторный разбор perf: первый gap компилирует pipeline

Новый trigger позволил правильно перечитать уже существующий 199 Hz perf, не
делая ещё один profiling run. В gap `1629.988 ms`:

```text
all samples       738
main              323 (43.8%)
dxvk-cs           293 (39.7%)
mali-compiler      48 ( 6.5%)
libmali           290 (39.3%)
```

Из 293 `dxvk-cs` samples 242 находились внутри `libmali`. Точный stripped
ARM32 blob всё же экспортирует достаточно C++/LLVM symbols, чтобы разрешить
адреса, например:

```text
libmali+0x19aaa7c  llvm::MachineFunction::print(...)
libmali+0x1ebe28a  llvm::Function::callsFunctionThatReturnsTwice() const
```

Вместе с отдельным активным thread `mali-compiler` это прямое доказательство
driver shader/pipeline compilation, а не вывод по одному имени процесса.

Точный source path закреплённой DXVK-Sarek:

```text
DxvkContext::updateGraphicsPipelineState
  -> DxvkGraphicsPipeline::getPipelineHandle
  -> createInstance / createPipeline
  -> vkCreateGraphicsPipelines
```

Это выполняется командой из `DxvkCsChunk::executeAll` на `dxvk-cs`. При первом
неизвестном state vector `getPipelineHandle` компилирует pipeline синхронно.
Исходник закреплён в
<https://github.com/zeyadadev/DXVK-Sarek/tree/617958fe1cf2b10e06fa751d3e40bd765dcf2cc6>.

В другом похожем gap `1619.763 ms` вместо `dxvk-cs` активен игровой worker
(`287` samples). Новый trigger повторил разделение: в одном gap main и
`dxvk-cs` были `R/running`, в другом main и guest worker были активны, а worker
переходил в `folio_wait_bit_common`/read. Поэтому один pipeline fix не имеет
права заявлять исправление всех загрузочных фризов.

## State-cache cold/warm

Использован штатный cache точной DXVK, а не новый patch. По её README cache
включён по умолчанию и должен заранее перекомпилировать известные state vectors
на следующих запусках; FINALPLAY16 раньше явно выключал его только потому, что
именно `0` прошёл correctness.

Оба arms использовали один изолированный path, одинаковые live bytes, save,
маршрут и `1992/800 MHz`; perf был выключен. Первый ошибочный старт, где
launcher переписал manipulation обратно в `0`, был немедленно остановлен и не
использован. Валидные captures:

```text
/storage/roms/ports/ablogs/dxvk-state-cache-v1-cold2-20260825
/storage/roms/ports/ablogs/dxvk-state-cache-v1-warm1-20260825
```

| | cold fill | warm read |
|---|---:|---:|
| manipulation | cache `1`, empty | cache `1`, existing |
| cache size | `12860` | `12860` bytes before/after |
| cache SHA | `d2d94dda...` | тот же SHA before/after |
| key/load recurring gap | `1590.021 ms` | `2289.905 ms` |
| loaded/worker gap | `1639.718 ms` | `1719.230 ms` |
| correctness | pass | pass |

В cold key-gap trigger видел `dxvk-cs R/running` и `mali-compiler`. В warm
key-gap на 500 и 1200 ms вместо него активно работал `dxvk-shader`. Это ровно
механизм state cache: worker вызывает `compilePipeline`, удерживая pipeline
mutex; первый draw, пришедший до окончания compile, всё равно не может получить
готовый handle. На RG353VS перенос работы в background не гарантирует, что она
закончится до первого use.

Warm key-gap также имел больше pressure (`memory PSI 15.43/13.60%`, `9.289
MiB` MMC read), чем cold (`2.37/1.75%`, `0.129 MiB`). Поэтому `+699.884 ms`
нельзя публиковать как чистую cache-регрессию. Доказанный отрицательный
результат уже: cache не устранил gap при правильном route и manipulation.

Для второго warm gap CPU опускался до `1416--1800 MHz` при температуре около
`82 C`, поэтому его отличие от cold не является matched timing claim. Его
важный результат качественный: trigger снова выбрал game/read worker, а не
`dxvk-shader`/`dxvk-cs`.

Raw ignored hashes:

```text
78d40dbf779ef0b199af3895c2cb5d54d929c00c856aaa4464ef87e84130b0a6  cold present.tsv
fd3b76e95cbb24ee1c0656189d78c192b63c0982679559a6982a5d3af089fdad  cold device-pressure.tsv
c47970d5ef6edf3241b522a50c0079f3a7df41075856ef07f1cac8ab54bbb28a  cold gap-trigger.txt
5697bf16f58bf4a100d27074dc3b83aa88b7c6814e82f588066b4b5d02773fd3  warm present.tsv
e7cf4f2eba6ad624ee965d4197902f0dcdcc4bed4c86f3ab694fe06e2b0946b0  warm device-pressure.tsv
0daee5be1e1023d20cf5a6e11419e44aa5dd6636cd011d5818400dfe22766d91  warm gap-trigger.txt
```

## Shared-memory pressure консоли -- реальный софактор

RG353VS имеет `999244 kB` RAM, общей для CPU и Mali. В правильных runs во
время первого load gap процесс доходил примерно до `439--455 MiB` RSS и
`78--106 MiB` swap, а block trace показывал `~19 MiB` MMC read. Полный
`dmesg`, который шире прежнего fault/reset filter, неоднократно содержит:

```text
systemd-journald: Under memory pressure, flushing caches.
```

Точное текущее swap-устройство:

```text
/dev/zram0       768 MiB, priority 10, 187504 KiB used after runs
/storage/swapfile 1 GiB, priority -1, 0 used after runs
zram algorithm   lz4
```

В threshold-1 run появился ещё и Mali OOM notifier:

```text
mali ... OOM notifier: dev mali0 270372 kB
mali ... OOM notifier: tsk mgs2_sse_rg353v ... 259080 kB
```

Это не был GPU reset и не OOM-kill: рядом нет `invoked oom-killer`, процесс
завершил route с `autoload_rc=0`. В публичном Rockchip-примере такая же строка
является перечислением Mali allocations внутри общего kernel OOM path, после
которого отдельно печатается `invoked oom-killer`:
<https://github.com/rockchip-linux/mpp/issues/542>.

Notifier произошёл в tick `39456.178`, тогда как первый measured async skip
был только в `39517.469`. Поэтому его нельзя причинно приписывать aggressive
async queue. Доказанный вывод уже: ограниченная shared-memory консоли и reclaim
участвуют в load path и способны усиливать паузу. Это не отменяет отдельно
доказанную нативную pipeline compilation: в её control gap MMC I/O мог быть
нулевым, а `dxvk-cs` проводил 242/293 samples в `libmali`.

## Что это говорит об удалении Box86

Для pipeline-gap дорогое LLVM-компилирование уже нативное ARM внутри
proprietary `libmali`. Нативная DXT также уже сняла почти всю конкретную
texture-worker работу без сокращения wall-clock gap. Поэтому полное удаление
Box86 может улучшить другие CPU paths, но не устраняет доказанную pipeline
компиляцию: новый Vulkan pipeline всё равно должен создать нативный driver.

Второй game/read gap всё ещё проходит через guest worker и может содержать
эмулированную работу, но его нельзя исправлять переносом случайного decoder:
native DXT был прямым refuting result. Следующее вмешательство обязано отдельно
показать его active guest RVA/read ownership.

## Fan patches и async A/B

Проверены официальные репозитории V's Fix и Community Bugfix Compilation. Они
исправляют renderer/config/audio/assets, но не документируют исправление этой
pipeline/worker подписи. Массовая установка меняет asset workload и ломает
контроль; поэтому эти пакеты не добавлены в measured arm:

- <https://github.com/VFansss/mgs2-v-s-fix>;
- <https://github.com/cipherxof/MGS2-Community-Bugfix-Compilation>.

На консоли установлен, но не promoted, research-only Sarek async arm из
`origin/async` commit `464513e3`. По точному коду он возвращает null pipeline и
пропускает draw, пока `dxvk-pcompiler` компилирует его в background. Новый DLL
добавил только memory counter этого решения:

```text
a2304c52fdfbbb3792098f65458a7c6e4b018650c6b50f62aa9eb0e04b93be7c
d3d9_dxvk_sarek_1.11.0_async_mali_countskip1.dll
```

Оба runs прошли LOAD GAME, rows `09 -> 08 -> 07`, yes/no, loaded gameplay,
18/18 identity и `autoload_rc=0`:

```text
/storage/roms/ports/ablogs/dxvk-async-skip-v1-full1-20260825
/storage/roms/ports/ablogs/dxvk-async-skip-v1-threshold1-20260825
```

| | cache-off control | async threshold 5 | async threshold 1 |
|---|---:|---:|---:|
| skipped draws | n/a | `1` | `2227` |
| first load gap | `2651.667 ms` | `2618.433 ms` | `2699.999 ms` |
| pipeline/next cluster | `1620.229 ms` | `1600.082 ms` | `309.972 + 179.758 + 1410.357 ms` |
| loaded/worker gap | `1630.088 ms` | `1619.914 ms` | `1730.022 ms` |
| correctness gates | pass | pass | pass |

Threshold `5` разрешает async только после пяти последовательных frames одного
render target, поэтому первый use продолжал идти синхронно. Threshold `1` --
минимум, разрешённый самой веткой -- создал два больших skip burst. Они
начинались в основном у выхода из уже произошедших gap; множество новых draw
не превратилось в устранение load/worker stalls. Поздняя часть threshold-1 run
также опускалась до `1608--1800 MHz` при `83.3 C`, поэтому небольшое изменение
одного gap не является matched performance win.

Static loaded/walk screenshots не имеют black frame и показывают игрока/сцену,
но были сделаны после burst и не доказывают целостность каждого пропущенного
draw. Поскольку timing benefit практически отсутствует уже при threshold `5`,
а `1` меняет 2227 draw и добавляет визуальный риск, отдельный perturbing
screenshot-on-every-skip run не оправдан. Готовая fan async-ветка отвергнута для
этой проблемы.

Raw ignored hashes:

```text
3170c21564c02e930240444cb960691f37c5f9a1461661908812aa1ff2e35f2e  threshold5 present.tsv
97719de126b1c907b25ed4149a0eeb74cb071576ddc4aef36098ade8500074fd  threshold5 device-pressure.tsv
35cc28346b0dccc3650803e8b7f0cf8c65132c914a2350da031fa9ece32a7a7d  threshold5 gap-trigger.txt
911455edb548148737ad5e1af74de660c28e2874e468cdbc1b7a8a9b4314fa22  threshold5 async-skip.txt
51d4dfd27a9cbd132ecb4869d131b573f80d3dfaea50717ef9b7d0d8f7aa5fd0  threshold1 present.tsv
2be40f2592e0126e4ff2e099e9182fdae806599a3909690a5f223113c9dfd3f0  threshold1 device-pressure.tsv
55b093c1fece484532c5be3b831956e94f68d3bda832aa8d308deaaf55152bb8  threshold1 gap-trigger.txt
32d1dfc9219dbb9e076408399107a8a58799d51e824278855711fba392cd0ca2  threshold1 async-skip.txt
```

Современная upstream DXVK использует `VK_EXT_graphics_pipeline_library`, чтобы
компилировать shaders раньше и уменьшать first-use stutter без такого старого
async skip-draw механизма:
<https://github.com/doitsujin/dxvk#graphics-pipeline-library>.
Переход на новую DXVK/Sarek -- отдельная большая совместимость-гипотеза; строки
extension внутри blob не доказывают feature support живого device.

Следующая узкая граница -- не ещё один async threshold. Нужно отдельно связать
game/read worker gap с его guest RVA, fd/read offset и reclaim, а затем сделать
один обратимый memory-working-set A/B на production. Остановка фоновых служб не
должна начинаться вслепую: после runs `emulationstation` имел лишь `15 MiB` RSS
(хотя `74 MiB` был вытеснен в swap), `sway` -- `10 MiB` RSS. Сначала прибор
должен показать, какая память или файл действительно возвращает PRESENT.

## Bounded pipeline timeline после warm-cache

После предыдущих результатов добавлен отдельный default-off прибор
`dxvk-patches/05-memory-only-pipeline-timeline.patch`. Он пишет не более 4096
записей по 40 bytes в RAM и никогда не форматирует/не пишет лог из DXVK или
driver thread. Внешний `harness/dxvk_pipeline_trace.py` после маршрута читает
PE data exports через `/proc/PID/mem`. События связывают:

```text
state-cache queue -> worker begin -> cache entry
-> vkCreateGraphicsPipelines begin/end -> first draw miss/ready -> worker end
```

Research DLL и точный source record:

```text
43c10d5a189cc72a672025d10e8e672ce28776afd26b66eb9983e17fde929b34
d3d9_dxvk_sarek_1.11.1_mali_pipeline_trace1.dll

f76a6e1e07da4ebb738e3383a5ea143551a00d58ccb3e422edcb9bc6dbedad2d
dxvk-patches/05-memory-only-pipeline-timeline.patch
```

Один post-instrument warm run использовал копию того же cache с SHA
`d2d94dda...`; файл остался `12860` bytes и с тем же SHA до/после. Route прошёл
LOAD GAME, save rows `09 -> 08 -> 07`, yes/no, gameplay и `autoload_rc=0`.
CPU/GPU всё время значимых gaps оставались `1992/800 MHz`; конец был `75.625 C`.

```text
/storage/roms/ports/ablogs/dxvk-pipeline-timeline-warm1-20260825
events=744 attempted=744 dropped=0
workers=44 driver_calls=46 draw_misses=16
queue_delay_max=2914 ms worker_max=2716 ms
driver_max=2099 ms draw_wait_max=392 ms
```

Timeline окончательно разделяет механизм, а не только имена threads:

| gap | lower bound | pipeline events | device evidence |
|---|---:|---|---|
| first load | `2559.957 ms` | ни одного | `19.238 MiB` MMC read, 156 major faults; позже active game worker |
| first pipeline cluster | `1260.573 ms` | workers/driver/draw `41287829..41289005` | `0.004 MiB` MMC read |
| second pipeline cluster | `729.989 ms` | workers/driver/draw `41290574..41291281` | `0` MMC read |
| loaded worker | `1649.947 ms` | ни одного | `10.504 MiB` MMC read; game worker `D/folio_wait_bit_common` |
| earlier autoload pipeline | `682.683 ms` | workers/driver/draw `41236053..41236681` | `0.125 MiB` MMC read |

В первом location pipeline cluster shader set ставится в очередь в tick
`41287829`, оба workers начинают в тот же tick, а первый draw miss приходит
через `12 ms`. В следующих sets queue, worker и draw часто имеют буквально
одинаковый millisecond. Поэтому старый state cache не может гарантировать
prewarm для этой игры: он получает shader почти одновременно с first use.
Внутри одного cluster draw действительно ждёт pipeline mutex/driver, например
`392`, `340` и `335 ms`; это не shader-cache догадка.

Также найден отдельный O(N^2) источник очереди. Cache содержит 44 state entries,
но они принадлежат лишь 14 уникальным shader-set hashes. `readCacheFile`
добавляет одинаковую пару `(shader key, pipeline key)` в `m_pipelineMap` для
каждого state entry; `registerShader` затем создаёт одинаковый `WorkerItem` для
каждого повторения, а каждый item снова обходит все states из `m_entryMap`.
Реальный trace:

```text
queue jobs       44
unique sets      14
cache_entry      488
largest duplicate group: 20 jobs for shader hash 0x31a87183
next group:              8 jobs for shader hash 0xb91d4a27
```

Pipeline mutex не даёт повторно вызвать driver для уже созданного state, но
второй worker ждёт первый, а поздние no-op jobs остаются в FIFO. Это объясняет
`2914 ms` queue delay, но не весь first-use gap: в location clusters первый
worker обычно начал сразу, и дорогим участком оставался driver/draw.

### Коррекция вывода о thread priority

Static reading локального Wine 11 tree сначала привёл к ошибочному ожиданию,
что `SetThreadPriority(LOWEST)` не дойдёт до Linux scheduler при имеющемся
`RLIMIT_NICE`. Live `/proc/TID/stat` это прямо опроверг:

```text
dxvk-shader   policy=SCHED_OTHER nice=6
dxvk-cs       policy=SCHED_OTHER nice=0
game main     policy=SCHED_OTHER nice=-2
mali-compiler policy=SCHED_OTHER nice=-2
```

Значит, installed Wine/Box86 route не равен сделанному по другому source tree
предположению; для этого устройства `ThreadPriority::Lowest` материален.
Исторический upstream commit `d49de734` прямо говорил, что в обычном Wine 2018
это ещё не имело эффекта, но было добавлено на будущее. Более новый upstream
не просто поднимает весь background pool: `f2f1f865` оставил один coordinator
state-cache thread и передал compilation общему worker pool, а `c978e62e`
ввёл отдельные high/normal/low очереди и ограничил число workers, имеющих право
брать low-priority optimization. Полный перенос этой архитектуры в Sarek 1.11.1
не является малым первым экспериментом.

Следующий допустимый A/B -- отдельная research DLL, где только два точных
state-cache workers меняются с `Lowest` на `Normal`. Timeline остаётся тем же и
должен показать одновременно driver, draw и общий Present gap. Критерий
отказа: если location pipeline clusters/draw waits не уменьшаются при
симметричном cache/route/clock, priority закрывается; O(N^2) dedupe проверяется
отдельно и не смешивается с этим run. Ни один из этих pipeline экспериментов не
имеет права заявлять исправление двух доказанно независимых game/read gaps.

Raw ignored hashes:

```text
eb42e626a5050baa1d321d95b4ddde6796c841b171f3ec10c86d9d48eebad920  present.tsv
b3cc5ca3050a3eb676bbc335ebe03cbff165a7ed13e8c548da73af27aa58aeb6  device-pressure.tsv
a17ac9f491fdadbb28bf394d41ff21c6466a301002947e0b95767debe957ba62  gap-trigger.txt
c7155a550efc4c630227dfce7bc092a033aff1b2bcbec9962dbdb094f3c97b06  pipeline-trace.txt
c482c4527b12aebd04405c4bfd2c7f24e3f8c1a6cb81f6f03379d242a0d45cff  autoload.log
```

## State-cache worker priority A/B: rejected

Проверен ровно выбранный single-variable A/B: в двух state-cache workers
`ThreadPriority::Lowest` заменён на `ThreadPriority::Normal`; memory-only
timeline и остальные DXVK changes не менялись. Отдельный launcher загрузил
research DLL, что подтверждено live SHA:

```text
debaef7a89da2c82b1232beff3ddf9ec31f6ec62a30d645b04b36c232563af53
d3d9_dxvk_sarek_1.11.1_mali_pipeline_normal1.dll

64d1243d028db2f6b25671d4512a02ab1d14d0f340dc5b24bce5be8cbf50ca0a
dxvk-patches/06-state-cache-workers-normal-priority.patch
```

Прогон использовал побитовую копию того же warm cache. Его размер и SHA
остались неизменны до/после; route снова прошёл LOAD GAME, rows
`09 -> 08 -> 07`, yes/no, gameplay и `autoload_rc=0`. CPU/GPU во всех
значимых gaps были `1992/800 MHz`. Манипуляция дошла до живого scheduler:
`dxvk-shader` работал как `SCHED_OTHER nice=0` вместо control `nice=6`.

```text
/storage/roms/ports/ablogs/dxvk-pipeline-normal-warm1-20260825
events=742 attempted=742 dropped=0
workers=44 driver_calls=46 draw_misses=15
queue_delay_max=1483 ms worker_max=1322 ms
driver_max=247 ms draw_wait_max=406 ms
```

Сравнивать глобальный `driver_max 2099 -> 247 ms` нельзя: control maximum
принадлежал ранней startup/order части, а Normal был вторым последовательным
запуском с иной внутренней driver/page-cache теплотой. В одинаковой location
части результат мал и смешан:

| location gap / wait | warm trace control | workers Normal |
|---|---:|---:|
| first game/read load | `2559.957 ms` | `2619.771 ms` |
| first pipeline cluster | `1260.573 ms` | `1249.996 ms` |
| second pipeline cluster | `729.989 ms` | `649.966 ms` |
| loaded game/read worker | `1649.947 ms` | `1640.043 ms` |
| relevant draw waits | `392, 340, 335 ms` | `406, 367, 311 ms` |

Первый pipeline cluster изменился лишь на `-10.577 ms`; второй -- на
`-80.023 ms`, но соответствующие draw/worker waits не получили одностороннего
улучшения. В Normal они включали `367`, `406`, `311` и `493 ms`, в control --
`347`, `392`, `340` и `477 ms`. Доказанные game/read gaps также остались
`2.62 s` и `1.64 s`; в них прочитано `19.953 MiB` и `10.523 MiB` с MMC.

Итог: низкий Linux priority state-cache workers был реальным фактором, но его
подъём до Normal не является исправлением наблюдаемых location stalls.
Гипотеза priority закрыта и production не меняется. Найденный O(N^2) duplicate
queue остаётся отдельной inefficiency, однако он не объясняет два больших
game/read gaps и не должен смешиваться со следующим экспериментом.

Следующий шаг после этого прогона возвращается к причинной границе game/read:
связать active worker TID с guest RVA, `fd -> path`, offset/length и I/O/reclaim
внутри одного no-PRESENT interval. Только после этого допустим один обратимый
working-set/page-cache A/B; останавливать службы или preload-ить все assets
вслепую нельзя.

Raw ignored hashes:

```text
142e3085b93058291ec2735605574995794fdd4bf59b09f757a27d6c3eb0ed17  present.tsv
6c374b0d8112dab3fb931b12f3806622289ca4f00f97e37181f8245213b7c9bf  device-pressure.tsv
4bfe3ad9f9b432673bd107be2562e8d08a314f4475e6b005b2c8818766d9e551  gap-trigger.txt
579096d11aaec35ee7208fdec310e6f72e159539d902b76d5e8bbe34084f50dc  pipeline-trace.txt
1e72d8d410fe0ad38dd8fc0bc238d59160e1e98684d01b69821bcd97d511a315  autoload.log
```

## Game/read causal trace

Следующий production-equivalent capture загрузил исходный FINALPLAY16 D3D9
`cf67ce74...`, `box86-fp16-dxvk` и `DXVK_STATE_CACHE=0`. Route, 18/18 identity,
fixed clock и `autoload_rc=0` прошли. Default-off gap reader был расширен только
внешним чтением `/proc/TID/syscall` и `fdinfo` для уже выбранных top-active
threads; perf guest map разрешён офлайн по точному TID и времени gap.

```text
/storage/roms/ports/ablogs/dxvk-read-causal-finalplay16-20260825
game exe SHA256=29759e6f06eaea4d61bb6aef5a5ef45a936eac1e76fa0c3471cf4f231349aaa0
```

Две независимые location reads теперь связаны до конкретных файлов:

| gap | active worker | syscall / file | device pressure |
|---|---|---|---|
| `2720.038 ms` | `TID 709954`, `D/folio_wait_bit_common` | compat `pread64`, `count=3034584`, `offset=0`, `stage/w18a/cache.qar` | `19.504 MiB` MMC, 358 major faults |
| `1650.016 ms` | тот же `TID 709954`, `D/folio_wait_bit_common` | compat `pread64`, `count=4314400`, `offset=0`, `stage/w19a/cache.qar` | `10.645 MiB` MMC, 98 major faults |

Live `stat` показал, что размеры файлов равны request count ровно:
`3034584` и `4314400` bytes. Игра читает каждый `cache.qar` целиком с нулевого
offset. `w18a` -- контролируемая Strut D Sediment Pool, `w19a` -- следующая DE
Connecting Bridge; QAR содержит stage texture cache.

Офлайн guest resolution внутри обоих exact intervals воспроизвёл один профиль:

```text
RVA 0x5115da
RVA 0x515473
RVA 0x5166fe
RVA 0x5168bf
```

Дизассемблирование exact live EXE связывает эти блоки с D3DX DXT decode/color
conversion. Это уточняет, но не отменяет прежний refuting result: native DXT
A/B почти убрал эту guest CPU работу, однако не сократил wall gap. Теперь видно,
почему повторять тот же фикс нельзя: один worker одновременно читает полный
texture archive, блокируется на folio и затем декодирует его.

Между reads снова прошёл отдельный `1660.638 ms` pipeline gap: `dxvk-cs` имел
308/734 perf samples, `libmali` -- 276, а MMC read и I/O time были нулевыми.
Это ещё одно воспроизведение двух механизмов в одном route.

Device kernel не предоставляет per-thread `io` ни как
`/proc/PID/task/TID/io`, ни как `/proc/TID/io`; reader сохранил это как
`FileNotFoundError`. Это ограничивает разделение cumulative logical/physical
bytes по TID, но не ставит под сомнение syscall: его fd, full-file count,
offset, path и блокирующий wchan сняты атомарно из живого task.

Post-run research оставляет один узкий A/B. Linux `POSIX_FADV_WILLNEED`
nonblocking и может уменьшать объём под memory load, поэтому диагностический
arm должен синхронно прочитать только два доказанных файла во внешнем процессе
после выбора Yes, но перед confirm-load. Их общий размер `7,348,984 bytes`;
default-off harness ставит fail-closed limit `16 MiB`. Он не preload-ит другие
assets, не останавливает службы и не меняет production/runtime. Критерий:
исчезновение или резкое сокращение именно двух read/MMC gaps при сохранении
pipeline gap. Если reads остаются `~2.7/~1.65 s`, page-cache prewarm отвергается.

Raw ignored hashes:

```text
ecae2879231b8b2da779f7262b20b1a06972eaec1862c888ebaa016d1fbefa7b  present.tsv
4fa91887d1ebb58849bdddb046bae9f89c2984a28758af11e34dbf93e85c4cb1  device-pressure.tsv
aee792651bc4e6cf75a57bceaad7f87fa234fbe0c563b2d269ee5e2a40ed22ff  gap-trigger.txt
4f2ceb7b3eb6e3ccedd1c7d07ef80a790f55950005884980532a3ac6e92119f4  perf-gaps.txt
8c3fe77fb05062a21303d8622eca39727becbb098bfb4527ced56e57e29c9de5  perf.script
a41b9cfa4e4317b5f684da8b681fd157477bb44d7e9240ff8c0f057699759189  guest-map.bin
0580c465e9520cff960b759d5026c502bf4849ed60e472196abbc573ace0351d  autoload.log
```

### Full-file page-cache prewarm A/B: rejected

Matched arm синхронно прочитал оба доказанных файла после framebuffer gate
`5-on-yes`, непосредственно перед `6-loaded` confirm:

```text
w18a/cache.qar  3034584 bytes  50.817 ms
w19a/cache.qar  4314400 bytes  70.744 ms
total            7348984 bytes 122.472 ms
```

Route, live FINALPLAY16 bytes, cache-off, clocks и correctness снова прошли.
Однако endpoints практически не изменились:

| endpoint | production control | full-file prewarm |
|---|---:|---:|
| w18a read gap | `2720.038 ms` | `2669.981 ms` |
| adjacent pipeline gap | `1660.638 ms` | `1630.046 ms` |
| w19a read gap | `1650.016 ms` | `1650.208 ms` |
| w18a MMC / major faults | `19.504 MiB / 358` | `20.285 MiB / 1546` |
| w19a MMC / major faults | `10.645 MiB / 98` | `10.566 MiB / 30` |

В обоих read gaps worker снова попал в `folio_wait_bit_common`, выполняя тот же
full-file compat `pread64`. Поэтому простой launcher pre-read не является
исправлением и не promoted. Разница `-50 ms` для первого gap меньше run noise,
второй совпал в пределах `0.2 ms`; средний FPS не используется как endpoint.

Flags живого QAR fd `02404000` декодируются как
`O_NONBLOCK | O_NOFOLLOW | O_CLOEXEC`; `O_DIRECT` отсутствует. Следующая
default-off диагностика должна использовать `mincore`, не разыменовывая file
mapping, чтобы снять resident pages от prewarm до игрового pread. Если страницы
становятся 100% resident и затем исчезают до gap, следующая гипотеза --
reclaim/eviction. Если остаются resident во время blocked pread, текущая связь
page-cache ошибочна и нужно искать другой folio/file внутри того же worker.

Raw ignored hashes:

```text
1be942cc0816df0bbc18e2630acc5844408bed127cb850eb96fc64883eba45de  present.tsv
b268cfed5e9cab943a7a6d2050f69030148d42e2e36d3bbb2011f379df0c7a18  device-pressure.tsv
fb35d3f61b27eb2bdc0e9fe15cf1ca377eea160fdcf30a28fa39490f04fb999c  gap-trigger.txt
d92e6140e9ffbb4a68e26e93399569b40f9810357cf0c1c034c5a25a0abc5c28  perf-gaps.txt
cdf85c338402f488e07c6c9bac8835d86d20de4f1a745fc5d8b6e27f5730e4bc  perf.script
aa09157b8cdf68871762faf87d20a7f735dea808a2c7a1ee7e0654cf6273fe59  guest-map.bin
33018b53aa0498fbc91cdcef208e3efd75a7393a7dffc3902a7c5d59cc2e9d67  autoload.log
```

### Mincore: QAR prewarm был немедленно reclaimed, load chain шире QAR

Повтор того же arm добавил только external `mincore` snapshot раз в `50 ms`;
file mappings не разыменовывались, а rows оставались в RAM до конца route.
Perf был отключён, потому что guest RVA уже воспроизведён дважды.

Реальный residency transition:

```text
before prewarm                    w18a QAR 0/741    w19a QAR 0/1054
43298693, reading w18a complete   w18a QAR 741/741 (100%)
43298743, 50 ms later             w18a QAR 0/741;  w19a QAR 260/1054
43298793                          w19a QAR 546/1054 (51.8%)
w18a load start 43304288          both QAR 0%
```

То есть pre-read действительно населял page cache, но страницы выбрасывались
даже пока external process последовательно читал второй файл. Успешный full-file
read w19a не означал 100% simultaneous residency. Это прямое подтверждение
reclaim на консоли, а не `O_DIRECT` или неверный inode.

Одновременно gap probes исправили неполную модель file chain:

```text
w18a load, +510 ms:
  stage/r_plt0/resident.dar, pread64 count=4426105, offset=0
w19a load, +1210 ms:
  stage/w19a/cache.dar, pread64 count=4459489, offset=0
```

Другие runs ловили w18a/w19a `cache.qar` на том же worker. Значит, каждый
визуальный gap -- последовательная загрузка нескольких resident/stage archives,
а QAR-only prewarm был заведомо неполон. `resident.dar` на диске ровно
`4426105` bytes, w19a `cache.dar` -- ровно `4459489`; full-file pattern снова
совпадает с syscall count.

Следующая bounded диагностика после research будет следовать только за уже
пойманным worker TID раз в `20 ms` и сохранять лишь смены read
`fd/path/count`, максимум 64 события на gap. Это нужно до любого `mlock` A/B:
root имеет `CAP_IPC_LOCK`, но pin случайного списка файлов может лишь усилить
anon swap. После точного списка допустим один locked-residency experiment;
production пока не меняется.

Raw ignored hashes:

```text
cb8a06e3047ea24960424e8e5d72365bb4eafcd7c23158e6b5f8e99e8f9066b1  present.tsv
72814148551207dad18a4a0565e66b25e5e674fd63c436092cf9ee64cad7b92e  device-pressure.tsv
4a0fad5265c3d649ce7ed2723cae6acad789c3c1b0f3931ed001a4d4d186e8fd  gap-trigger.txt
25e6a5647624c0d1fec4dd43dc5dcc98fd8e1f7cf5946b75306914bf945a9232  page-cache-residency.tsv
d297e913067e854feb5dfc8a0aad507041cda940093f4cbb1c965815ea96d9e8  autoload.log
```

### Read-chain follower control: invalid instrument, preserved

Первый control нового 20-ms follower не выполнил собственный causal gate:

```text
/storage/roms/ports/ablogs/dxvk-read-chain1-finalplay16-20260825
w18a game/read gap  2630 ms
w19a game/read gap  1610 ms
adjacent pipeline   1620 ms
```

Route и production identity были корректны, но probes застали resource worker
между syscalls. Follower назначал TID только после уже декодированного compat
read и поэтому начал следить слишком поздно, на `w19a/cache.dar`; получено
только одно READ event. Этот run ничего не говорит о составе более ранней
цепочки и не является основанием для `mlock` сам по себе. Reader исправлен
узко: на первом probe он может выбрать самый активный normal-priority игровой
worker, а затем всё так же читает syscall только одного TID раз в `20 ms`, с
лимитом 64 смены на gap.

Raw ignored hashes:

```text
d1b712984cd9880a8b2c3e0181210d1e50b91af6268f1d814c3b7ee8f8b40548  present.tsv
5e99c13a1d83a03ea71e67db496c24307f7167fb68167f0df4140f58039059a0  device-pressure.tsv
73f34ee872d0937f073e47c6d900477c0e0a6e9f6f8a6cd31fd986324e7b85a7  gap-trigger.txt
4d2f82444f40ed5b586927b306c2a62c3bf10d2405ed57062eab1b0e15f60ba9  autoload.log
```

### Exact data.cnf set and rejected wrong-root arm

Post-control research found a stronger source for the bounded file set than
another sampled syscall. The exact local and device `data.cnf` files declare
the non-streamed stage inputs. `.resident` persists between stages, while
`.cache` is renewed at each stage load. The format description and MGS2 samples
are preserved in the
[KCEJ Wiki](https://github.com/Joy-Division/KCEJ-Wiki/blob/master/Common/data.cnf/ReadMe.md).
For this fixed route the declared set is:

```text
r_plt0: resident.qar resident.dar cache.qar cache.dar scenerio.gcx
w18a:   cache.qar w18a.hzx cache.dar scenerio.gcx
w19a:   cache.qar w19a.hzx cache.dar scenerio.gcx
```

The 13 files total `24,046,326 bytes` (`22.932 MiB`). All three `data.cnf` and
all 13 payload SHA256 values match between the extracted workstation tree and
the RG353VS. This is small enough for one default-off diagnostic lock but is
not a production policy: kernel documentation warns that too much unevictable
memory can shrink the remaining working set and cause thrash/OOM. A successful
`mlock` guarantees residency until unlock according to
[Linux man-pages](https://man7.org/linux/man-pages/man2/mlock.2.html), while
the reclaim tradeoff is described by the official
[kernel unevictable-LRU documentation](https://www.kernel.org/doc/html/v6.10/mm/unevictable-lru.html).

The first attempted lock arm is explicitly invalid:

```text
/storage/roms/ports/ablogs/dxvk-read-mlock-datacnf1-20260825
```

It used the workstation-relative root `MGS2-Substance/cdrom.img`; the device
root is `MGS2-Substance/game/cdrom.img`. Both the prewarm process and mincore
reader failed with `ENOENT` before confirm-load, so the only captured 730-ms
gap belongs to the menu and must not be compared with gameplay. This also found
that `autoload_save.sh` discarded the Python exit status after printing its
final state, which made the outer capture falsely report `autoload_rc=0`.
The wrapper now preserves that status; no renderer or production default was
changed.

Invalid-run raw hashes:

```text
e1462a170b3b182cb961d3c5d024a3d841a2902f471d4a5a4960e25cfcfc56ae  present.tsv
0812a6224b1edd63f9299e25db368b0a77a566870fae8631db93b65086384270  device-pressure.tsv
62b698e07c4214651f1a3af0736539f07542c7c6a520b5586a71a35347854511  gap-trigger.txt
b8693b8e3cfc19003c29f5a4c13160b1add8824b7910cea137d7c1896f942f57  page-cache-residency.tsv
3215b61f001a1f8cc19156182cfc117dae31e76ccae021890b1aba6fb8ca6d86  autoload.log
```

### Locked exact data.cnf set: storage reduced, wall gaps remain

Corrected arm used the verified device root and passed route, loaded-screen,
fixed-clock, production D3D9/cache-off identity and `autoload_rc=0`:

```text
/storage/roms/ports/ablogs/dxvk-read-mlock-datacnf2-20260825
mlock files=13 bytes=24046326 VmLck=23508 KiB
```

External mincore independently verified the lock. From the completed mlock at
tick `44580178` through unlock at `44648582`, all 13 files were `100%` resident
in every snapshot: `17,784/17,784` file rows, zero non-resident rows.

| endpoint | production control | exact-set mlock |
|---|---:|---:|
| w18a game/worker gap | `2720.038 ms` | `2540.100 ms` |
| w18a MMC / major | `19.504 MiB / 358` | `5.887 MiB / 471` |
| adjacent pipeline gap | `1660.638 ms` | `1610.027 ms` |
| adjacent pipeline MMC | `0 MiB` | `0 MiB` |
| w19a game/worker gap | `1650.016 ms` | `1549.862 ms` |
| w19a MMC / major | `10.645 MiB / 98` | `1.586 MiB / 18` |

The large MMC reduction proves that console reclaim/storage was a real part of
the location-load workload. It does not make it the dominant wall-clock cause:
the two visible stops remain `2.54 s` and `1.55 s`, while the matched pipeline
gap remains `1.61 s`. The residual MMC includes swap and unrelated device I/O,
so it cannot be assigned to a particular unlisted asset. The `data.cnf` format
itself only claims the non-streamed stage list and must not be treated as a list
of all sound or streaming inputs.

The corrected follower selected resource worker `TID 767004` at the first
500-ms probe of both location gaps. At both 500 and 1200 ms it was `R/running`,
not blocked in a read syscall. Its reads were now too short for 20-ms polling to
observe, which agrees with mincore and the much smaller device I/O. Thus the
critical path changed from observable folio wait to CPU work in the same worker.

Conclusion: route-specific launcher `mlock` is rejected as a fix and remains
default-off. The result does justify one diagnostic factorial arm combining
the already verified native DXT decoder with exact-set mlock: the native-DXT
single-factor run left storage active, while this single-factor run leaves the
DXT/resource worker active. Only the combination can test whether the two paths
masked each other; it is not eligible for production even if it wins.

Raw ignored hashes:

```text
382d1c20a91e559907575c96779b4cc8902477d7c85deb3750e56c0f2e10b4b2  present.tsv
82b043a4a6441cd2b1847eba43e47b10a2cc3ff01badc3dab157fb1edc77a75f  device-pressure.tsv
88cbe842ffec647d31f04bbb281030f7c7d1ace61557e460045ce742557a3a12  gap-trigger.txt
82c4e2a2dff73fc7f5008ee72e8dae2cc8e8ea02d12296ea8096d439d381cb53  page-cache-residency.tsv
89e8f2279a605ab46806656b6505e8a0f59361844fe3c0d644ab03e62bf58d68  autoload.log
```

### Native DXT plus mlock factorial: no win, strict residency caveat

The combined arm passed the save/gameplay route, cache-off and exact native-DXT
identity. External counters prove the bridge was active:

```text
/storage/roms/ports/ablogs/dxvk-native-dxt-mlock-datacnf1-20260825
box86=d244919ea84ddba44782fd10a35609d2a6c561d47b15426b63dfc60e71960bcc
armed=1 verify=0
DXT5 calls=1425720
VmLck=23508 KiB
```

| endpoint | mlock only | native DXT + mlock |
|---|---:|---:|
| w18a game/worker gap | `2540.100 ms` | `2490.736 ms` |
| adjacent pipeline gap | `1610.027 ms` | `1668.830 ms` |
| next pipeline gap | `929.715 ms` | `880.008 ms` |
| w19a game/worker gap | `1549.862 ms` | `1640.179 ms` |

There is no directional performance win: one worker gap moves by `-49 ms`, the
other by `+90 ms`, and pipeline noise moves in both directions. At both 500 and
1200-ms probes of the late gap, the resource worker is still `R/running` even
though all 1,425,720 DXT5 calls used the native bridge. This rejects the idea
that DXT becomes critical merely after the declared files are resident.

The predeclared residency gate was not literally perfect, so this arm is not a
promotion-grade final A/B. Mincore recorded `17,809/17,810` in-lock file rows at
100%; one snapshot at tick `45030570` saw one missing 4-KiB page from the
previous stage's `w18a/cache.dar` (`1081/1082`). That page cannot plausibly
explain the `1.64 s` w19a stop, but the gate is preserved rather than relaxed.

Research found an avoidable ambiguity in the diagnostic implementation:
Python's writable buffer address required `MAP_PRIVATE|PROT_WRITE`, whereas the
experiment intends to lock shared read-only file-cache folios. The next causal
profile switches to a libc `MAP_SHARED|PROT_READ` mapping before `mlock`, as
described by the Linux
[mmap](https://github.com/torvalds/linux/blob/master/mm/mmap.c) and
[mlock](https://github.com/torvalds/linux/blob/master/mm/mlock.c) sources. It
will profile the residual worker; it is not another timing claim.

Raw ignored hashes:

```text
31c87462f362da6f0ed7d463cc26c4acd783b76a67b159a85fcf19f7a82777b9  present.tsv
79d2cd6ab5d27311b0c03032989c490711cfefe5fa2a3ed3f3497974d8cc05f9  device-pressure.tsv
648b49fd29433aeebb02baf98b8e86d87385f2357ff87cdfea54a025dd8fa487  gap-trigger.txt
3dbcbc381d8fe2686bf9804acc41baa8148fa0cfb670aa18bf8a914f00e6172f  page-cache-residency.tsv
554ed184abc500e69178bc3aab1b538e9264b91d7f34e819c719735c34bfd68e  autoload.log
33292896fa5bbb7379de1328e741790954410bedbe068050d1d33c7dfc24425a  dxt-stats.txt
```

### Residual worker profile: `VmLck` is not a residency proof

The follow-up profile used the intended libc `MAP_SHARED|PROT_READ` mappings.
It passed the save/gameplay route, exact candidate identity, native-DXT counter
and fixed-clock gates:

```text
/storage/roms/ports/ablogs/dxvk-native-dxt-mlock-shared-perf1-20260825
box86=d244919ea84ddba44782fd10a35609d2a6c561d47b15426b63dfc60e71960bcc
mapping=shared-readonly
DXT5 calls=1425720
VmLck=23508 KiB
```

However, it failed the independent residency gate. Between the logged lock and
unlock ticks, `8,219/17,810` per-file mincore rows were below 100%. Therefore
the successful `mlock` return and `VmLck` value on this vendor kernel/libc are
not proof that the shared file pages were populated and retained. This arm is
not storage-eliminated, and its `2520.013 / 1650.019 / 1010 / 1560.945 ms`
gaps are recorded only as run endpoints, not as a timing claim.

The failed lock still yielded a useful exact read observation. The bounded
follower caught complete HZX reads on the same resource worker:

```text
w18a.hzx  pread64 count=300976 offset=0
w19a.hzx  pread64 count=629744 offset=0
```

Thus HZX belongs to the live stage-load chain declared by `data.cnf`; it was
not merely an unused manifest entry.

At 199 Hz, both worker gaps split CPU nearly evenly between the main thread
and resource worker:

| gap | samples | main | worker |
|---|---:|---:|---:|
| w18a | `1074` | `488` (`45.4%`) | `470` (`43.8%`) |
| w19a | `689` | `304` (`44.1%`) | `300` (`43.5%`) |

The main samples resolve primarily to Wine `win32u`/`ntdll` message/yield
paths. The worker samples resolve through the bounded Box86 guest map to the
same exact game routine in both gaps:

```text
EXE RVA 0x5115da   w18a 31/119 mapped-JIT samples (26.1%)
EXE RVA 0x5115da   w19a 32/97  mapped-JIT samples (33.0%)
```

Exact disassembly corrects the earlier interpretation of that RVA. It is the
start of a higher-level DXT surface conversion routine, not a DXT5 leaf. The
object constructor selects DXT1/2/3/4/5 and stores a leaf pointer at
`this+0x1084`; for DXT5 that leaf is `RVA 0x5168bf`, the function already
replaced by the research bridge. At `RVA 0x5116be`, the outer routine invokes
that leaf indirectly inside its block traversal, then copies 16-byte float RGBA
vectors and enters a scalar x87 conversion/clamp path. Its mapped JIT block
starts at `0x5115da` and spans `0x178` bytes, ending exactly at the beginning of
the later scalar loop.

This explains why 1,425,720 native DXT5 leaf calls did not remove the worker
gap: the measured hot region includes allocation/cache setup, block traversal,
indirect-call overhead and output copying around the leaf. It now justifies
researching a fused high-level converter, but not implementing one blindly.
The next gate is to recover the exact three-argument `thiscall` contract,
object side effects and output semantics, then design a differential verifier
that cannot corrupt the converter's row cache. Production and the native-DXT
research bridge remain unchanged.

Raw ignored hashes:

```text
2531e51d877cceb4ca989402ddb6d75de1a4e96b863ad279ace08e483860ceaa  present.tsv
b20c0ab52fb1fb2c7b58c60ef477884a1044d05fda54ce42af1f60413c6af604  device-pressure.tsv
b285c67957540557341e6d82e52f96f97f87c6e2a7d0f813d40a59374938600c  gap-trigger.txt
4c29a1871b92dc1bdd62a16504c26dc05b7960c3631eefc1e6843cbff41567e8  page-cache-residency.tsv
639c536d3e87f8ddd224b820d8cf2fd452bb4558a6bfd8acdcda644eeb3f4c39  autoload.log
33292896fa5bbb7379de1328e741790954410bedbe068050d1d33c7dfc24425a  dxt-stats.txt
51192988bf4eb4f697fa403330b63636b437cfe237f38b3da2979f7b0ec9adc5  perf.script
5d1cb979fdb3d6b25b38a89f0f144cf37ec6ae0dd2585c7503e8436e636e67a4  guest-map.bin
```

## Fused DXT5 surface-row candidate: verified partial win, not a freeze fix

The residual-worker profile justified moving one level above the already-native
DXT5 leaf.  Exact live bytes were checked again before implementing anything:

```text
29759e6f06eaea4d61bb6aef5a5ef45a936eac1e76fa0c3471cf4f231349aaa0
/storage/roms/ports/MGS2-Substance/game/bin/mgs2_sse_rg353vs_port.exe
```

The same SHA is present in the workstation game tree.  The earlier apparent
disassembly mismatch was an address-space mistake, not a different executable:
the profile reports PE RVA `0x5115da`, while `objdump` displays VMA
`0x9115da` because the image base is `0x400000`.  At the correct VMA the live
signature matches, the method is `0x2a9` bytes long and ends in `ret $0xc`.
Its four relative calls are at offsets `0x005/0x03c/0x058/0x16e`.

`box86-patches/20-native-dxt-surface-research-default-off.patch` intercepts
that exact method only after its signature matches.  It fuses DXT5 block
decode, the converter's 16-float row-cache layout and output-row copy into one
native call.  Unsupported format, colorkey, layout and first-cache-allocation
cases retain the guest method.  The patch is inert unless
`MGS2_BOX86_NATIVE_DXT_SURFACE=1` or verifier mode `2` is explicitly selected.
The block-oriented implementation is consistent with Microsoft's
[DirectXTex decompression model](https://github.com/microsoft/DirectXTex/wiki/Decompress),
but the game-specific layout is accepted only because it was differentially
verified, not because a generic BC decoder has the same object semantics.

### Rebuild and verifier dead ends preserved

The first verifier build (`da09dc10...`) did not reach DXVK: after 120 seconds
`d3d9_path` was still missing and the pixel route failed.  It was discarded,
not counted as a correctness result.  The rebuild had omitted the generated
`my_wl_proxy_add_listener` symbol required by the native Wayland bridge.
Rebuilding after restoring the generated wrapper record produced a candidate
with that symbol; every later run also verified the live `d3d9.dll` SHA.

The second verifier build (`ff718f30...`) reached DXVK but crashed on its first
guest-reference fallback:

```text
/storage/roms/ports/ablogs/dxvk-dxt-surface-verify2-20260825
wine: Unhandled page fault on read access to FFFFFFFF at address 00000000
autoload_rc=1
```

The failure was in the verifier bridge, not a mismatch in decoded pixels.
`DynaCall` restores its pre-call ESP and `RunFunctionWithEmu` then removes the
argument slots itself.  The bridge additionally subtracted 12 bytes because
the guest ended in `ret $0xc`, corrupting the caller's return frame and leading
to EIP zero.  The exact Box86 implementation is visible in
[`src/tools/callback.c`](https://github.com/ptitSeb/box86/blob/0579f8b9c47d87d700724f4cce559b06cbd2b0f5/src/tools/callback.c).
Removing only that second adjustment produced the tested candidate:

```text
bf0daac76f0af4e77bf0fdf668947bb12e0b44ace85ad91e85f6fc30bf53a40e
box86-fp19-dxvk-native-dxt-surface
```

The corrected mode-2 run passed the full visual `LOAD GAME` route, rows
`09 -> 08 -> 07`, yes/no confirmation and loaded-scene gate:

```text
/storage/roms/ports/ablogs/dxvk-dxt-surface-verify3-20260825
autoload_rc=0
surface calls=47648 native=47433 guest=215
surface compared=54 mismatched=0 skipped=0
cache_misses=11697 blocks=1407568 pixels=22738912
fallback_cache=215 format=0 colorkey=0 layout=0 guest=0
```

Thus 54 live outputs and their row-cache state matched the relocated original
method byte-for-byte, while the bridge handled 47,433 calls.  Mode 2 executes
both implementations for sampled calls and is not a timing arm.

### Symmetric A-B-A-B timing

All four timing arms used the same fixed save route, clocks, state-cache `0`,
external bounded gap trigger, D3D9 SHA `cf67ce74...` and candidate Box86 SHA
`bf0daac...`.  Only `MGS2_BOX86_NATIVE_DXT_SURFACE=0/1` changed.  Perf and hot
thread logging were off.  No `drop_caches` was used: the official
[kernel VM documentation](https://docs.kernel.org/admin-guide/sysctl/vm.html#drop-caches)
describes it as a testing/debug aid and warns that rebuilding the discarded
cache can create significant I/O and CPU cost.  Alternating arms instead
controls natural cache warming without injecting a different workload.

```text
A1 /storage/roms/ports/ablogs/dxvk-dxt-surface-off-control3-20260825
B1 /storage/roms/ports/ablogs/dxvk-dxt-surface-native1-20260825
A2 /storage/roms/ports/ablogs/dxvk-dxt-surface-off-control4-20260825
B2 /storage/roms/ports/ablogs/dxvk-dxt-surface-native2-20260825
```

| external no-PRESENT gap | A1 off | B1 native | A2 off | B2 native | off mean | native mean |
|---|---:|---:|---:|---:|---:|---:|
| w18a resource worker | `2588.999` | `2401.419` | `2589.996` | `2339.616` | `2589.498` | `2370.518` ms |
| adjacent pipeline | `1590.728` | `1568.432` | `1972.257` | `1608.594` | -- | -- |
| next pipeline | `910.040` | `920.016` | `839.876` | `899.735` | -- | -- |
| w19a resource worker | `1609.920` | `1459.977` | `1689.893` | `1429.996` | `1649.907` | `1444.987` ms |

The fused native path reduced the two resource-worker means by `218.980 ms`
(`8.5%`) and `204.920 ms` (`12.4%`).  Both native arms executed exactly
47,433 native calls, 11,697 cache fills, 1,407,568 DXT blocks and 22,738,912
output pixels; only the same 215 first-cache calls fell back to the guest.
The result repeats after each return to control, so it is not explained by a
monotonic page-cache warm-up.

This is a real but partial improvement, not the requested freeze resolution.
The location pauses remain `2.34--2.40 s` and `1.43--1.46 s`.  The independent
DXVK/libmali pipeline pauses remain as large as `1.97 s`; the second pipeline
gap also moves in the opposite direction, so no pipeline claim is assigned to
the DXT change.  Resource-worker followers still catch complete `cache.dar`
reads in every arm, and the high-level native path cannot remove storage,
allocation or the remaining conversion work around it.

The research candidate therefore remains default-off and is not promoted to
FINALPLAY16.  A future step must target a separately measured remaining owner
(for example the post-row scalar conversion or resource scheduling) and must
repeat correctness plus symmetric timing; widening this bridge without a new
profile would again be guessing.

Raw ignored hashes:

```text
726dcf62a8417077a516eb5a3c3183365ed7f45dc33ae96d97a05703ca3ed973  verifier identity.txt
b7795dbb7ab41f1282ed62b5d1bd68b62a421ef36a2f737175a4658c56fdcb05  verifier dxt-stats.txt
b1c642d333fc1c5959506f749b84035d9b94f9d866691ad721830c80b41aa53e  verifier autoload.log
0d902d443f77ea893d167483e0a505399e6cb406c1ae17ad5f668d403b72dc84  A1 gap-trigger.txt
111bed164d4b7c608523f4511a8fdee958ce2bfe6da8269c11e90f203a635f29  B1 gap-trigger.txt
f9f71a1076dfac733195684620ea7af476c598edf3645303f7ca7a102aa8c401  A2 gap-trigger.txt
547e7ffa05f26a850d9991b73e4096441eea239f1cd73946bb14f3cadabe0139  B2 gap-trigger.txt
```

Patches 18, 19 and 20 were mechanically re-exported after the tested build.
Against pristine Box86 commit `0579f8b9`, the complete patch followed by
17/18/19/20 now applies with ordinary `git apply` and no `--recount`; the three
patch-20 source files have no difference from the tested build tree when
ignoring whitespace-only normalization.  The launcher and fail-closed manifest
are
`device/launch-dxvk-sarek-dxt-surface.sh` and
`device/FINALPLAY16_DXVK_DXT_SURFACE_VERIFY.manifest`.

## Exact state-cache mapping dedupe: queue fixed, freezes unchanged

The exact Sarek source at commit
`617958fe1cf2b10e06fa751d3e40bd765dcf2cc6` confirms the duplication seen in
the memory trace. `readCacheFile()` maps every stage of every cache entry;
`mapShaderToPipeline()` previously inserted an identical `(shader key,
pipeline key)` pair again for every state of the same pipeline. Later,
`registerShader()` created one `WorkerItem` per mapping even though
`compilePipelines()` already walks every state for the complete key.

`dxvk-patches/07-state-cache-mapping-dedupe-default-off.patch` rejects only an
exact existing pair and is inert unless
`MGS2_DXVK_STATE_CACHE_DEDUPE=1`. The reviewed patch series 01/02/03/05/07
applies normally to the exact source and reproduces the tested
`dxvk_state_cache.cpp`:

```text
8b6cc9c42ebc5123d338797f8b981e371ad14cce7aec8d4fa14e8ff0130afd53
dxvk-patches/07-state-cache-mapping-dedupe-default-off.patch

5a24bb386d5dd874791174b22addfb901b1b6301c950bd27e58a75404d08d677
d3d9_dxvk_sarek_1.11.1_mali_state_cache_dedupe1.dll
```

The verifier used fused-DXT mode 2, passed the correct LOAD GAME route, rows
`09 -> 08 -> 07`, yes/no, loaded scene and walk, and ended with
`autoload_rc=0`. Live D3D9 and Box86 hashes matched the fail-closed manifest.
The state-cache file was unchanged at `12860` bytes and SHA `d2d94dda...`.
All 46 real driver compile calls were retained while duplicate work was
removed:

```text
/storage/roms/ports/ablogs/dxvk-state-cache-dedupe-verify1-20260825
timeline events=210 attempted=210 dropped=0
workers=14 driver_calls=46 draw_misses=16
surface calls=47648 native=47433 guest=215
surface compared=54 mismatched=0 skipped=0
```

The timing gate was a symmetric A-B-A-B with the same new DLL, warm-cache SHA,
fixed save route, clocks, fused-DXT mode 1 and memory timeline. Only dedupe
`0/1` changed:

```text
A1 /storage/roms/ports/ablogs/dxvk-state-cache-dedupe-ab-a1-off-20260825
B1 /storage/roms/ports/ablogs/dxvk-state-cache-dedupe-ab-b1-on-20260825
A2 /storage/roms/ports/ablogs/dxvk-state-cache-dedupe-ab-a2-off-20260825
B2 /storage/roms/ports/ablogs/dxvk-state-cache-dedupe-ab-b2-on-20260825
```

| measurement | A1 off | B1 on | A2 off | B2 on | off mean | on mean |
|---|---:|---:|---:|---:|---:|---:|
| worker jobs | `44` | `14` | `44` | `14` | `44` | `14` |
| queue-delay max | `1509` | `574` | `1422` | `430` | `1465.5` | `502.0 ms` |
| first game/read load | `2320.046` | `2459.988` | `2330.009` | `2449.975` | `2325.028` | `2454.982 ms` |
| first location pipeline | `1220.418` | `1639.978` | `1259.989` | `1287.756` | `1240.204` | `1463.867 ms` |
| second location pipeline | `750.003` | `660.505` | `739.429` | `801.855` | `744.716` | `731.180 ms` |
| loaded game/read worker | `1399.980` | `1419.897` | `1420.519` | `1440.814` | `1410.250` | `1430.356 ms` |

The queue maximum fell by `963.5 ms` (`65.7%`) and worker jobs fell from 44 to
14, so the code-level inefficiency and its removal are both proven. However,
the two pipeline clusters did not become shorter as a pair (`1984.920` versus
`2195.047 ms` mean), and neither independent game/read pause improved. The
large B1 driver/draw values also show substantial Mali compilation variance,
so this is not assigned a firm regression; it is simply not a user-visible
win. Dedupe remains research-only and is rejected as a freeze fix.

Post-run source research points to the next bounded variable. Upstream DXVK
later added a better background-compile priority system specifically to reduce
the impact of many new pipelines and reduced how many workers may perform low
priority optimization:
<https://github.com/doitsujin/dxvk/commit/c978e62ec8616031a028f2ffa2b5bf3a6b3662cc6>.
This old Sarek already exposes the smaller first experiment as
`dxvk.numCompilerThreads`; automatic selection creates two workers on the
four-core RG353VS. A one-worker diagnostic therefore needs no source change.
Its refuting gate is strict: if it does not reduce the same two location
pipeline clusters without increasing first-use draw wait, compiler concurrency
is closed. This cannot affect the two separately proven game/read stalls, and
production remains `DXVK_STATE_CACHE=0`.

Raw ignored hashes:

```text
eea2a76eb4fde3ad3a94b845f20292567dce37cececdce5740fe9789697b4cca  verifier identity.txt
4397396556070eaee4a0a4efc416af4b68daeb857b8874404f4d5f68d6760948  verifier pipeline-trace.txt
01ae25f4aeae7ce11ee66fb40d3f0ee3c4d6415b590a8f611887f998e5814fd0  A1 pipeline-trace.txt
1c9c3562902ed67c39dd4ae02278037ddc2613db99471614aa2876418e7cce6e  B1 pipeline-trace.txt
9e9700847eaf316d02338258fd9e2e6a969999094b9b67b9c104838e815a40fd  A2 pipeline-trace.txt
7f10fd8ab499d34e6b11c5a537945b28687808b03f2aac7d40e76e1d8d8a5cbb  B2 pipeline-trace.txt
359f825cf2ff066a5e9b05103ac1a9b0c95f8e0dba26a888c98f06121eca3c29  all timing state-cache-after.txt
13e68070dac612ecacb8fe87809900f58769bd552f7f8afce0ff641adb72f2da  all timing dxt-stats.txt
```

## One state-cache worker: accepted for the research stack

The first one-worker diagnostic was deliberately excluded from timing. It
proved the live control twice -- identity contained
`DXVK_CONFIG=dxvk.numCompilerThreads = 1` and the DXVK log said
`Using 1 compiler threads` -- but it also grew the cache from `12860` to
`13151` bytes and added a 47th driver compile. Its correct route and visual
result remain useful correctness evidence, not a matched performance arm.

The resulting cache was then held fixed for a new A-B-A-B. All four runs used
the same D3D9/Box86 hashes, dedupe `1`, fused-DXT mode 1, exact save route,
fixed clocks and cache SHA
`d04158e8e15cb457bd74b97986e750883680622ea9334f292b6ec4390b49f1e8`.
The cache remained `13151` bytes and bit-identical before and after every arm.
Start temperatures were paired at approximately `57.2/57.2` and
`58.3/58.3 C`; all arms ended at `75.6--76.9 C` and `1992 MHz`.

```text
A1 /storage/roms/ports/ablogs/dxvk-state-cache-workers-ab-a1-two-20260825
B1 /storage/roms/ports/ablogs/dxvk-state-cache-workers-ab-b1-one-20260825
A2 /storage/roms/ports/ablogs/dxvk-state-cache-workers-ab-a2-two-20260825
B2 /storage/roms/ports/ablogs/dxvk-state-cache-workers-ab-b2-one-20260825
```

| measurement | A1 two | B1 one | A2 two | B2 one | two mean | one mean |
|---|---:|---:|---:|---:|---:|---:|
| first game/read load | `2339.841` | `2380.407` | `2489.982` | `2369.915` | `2414.912` | `2375.161 ms` |
| first location pipeline | `1389.198` | `969.967` | `1750.023` | `1217.573` | `1569.611` | `1093.770 ms` |
| second location pipeline | `839.943` | `649.960` | `809.984` | `720.345` | `824.964` | `685.153 ms` |
| both pipeline gaps | `2229.141` | `1619.927` | `2560.007` | `1937.918` | `2394.574` | `1778.923 ms` |
| loaded game/read worker | `1519.776` | `1469.696` | `1467.954` | `1401.062` | `1493.865` | `1435.379 ms` |
| driver-duration max | `270` | `231` | `648` | `247` | `459.0` | `239.0 ms` |
| draw-wait max | `422` | `385` | `713` | `373` | `567.5` | `379.0 ms` |
| background worker max | `724` | `1606` | `723` | `1278` | `723.5` | `1442.0 ms` |

One worker reduced the combined location pipeline pause by `615.652 ms`
(`25.7%`). Both individual clusters moved in the same direction, and the
return to two workers reproduced the slower arm. All four traces retained 14
deduplicated jobs and 47 actual driver calls. Stream overlap supplies the
mechanism: two-worker arms reached three simultaneous
`vkCreateGraphicsPipelines` calls (main/dxvk-cs plus both background workers),
while one-worker arms could reach only two. Serializing the background queue
roughly doubled its longest worker lifetime, but substantially shortened the
main-visible draw waits and no-PRESENT gaps. On this proprietary Mali driver,
less compile concurrency is better than draining the background queue sooner.

The post-run reading also narrows what upstream history does and does not
prove. Commit `c978e62e` added high/normal/low buckets and restricted workers
eligible for low-priority optimization, matching the general concern about a
burst of new pipelines. It did not directly prescribe one legacy state-cache
worker: on four cores its normal-priority pool is still two. The one-worker
claim here therefore rests on the matched RG353VS trace, not on extrapolation
from newer DXVK.

This result accepts `dxvk.numCompilerThreads = 1` for the state-cache research
stack, but it is not yet a production change. FINALPLAY16 has
`DXVK_STATE_CACHE=0`, so the knob alone creates no worker and cannot improve
production. The next single-variable gate is state-cache off versus the now
verified warm state-cache on with dedupe and one worker, using the same fused
DXT and D3D9 binaries in both arms. Only that comparison can show whether the
research stack beats the current no-cache pipeline behavior.

Raw ignored hashes:

```text
33736eda5cf88fe4e8e0da6d755b4d62bc4214a06c45c4a6dafa3e30ae51da8c  A1 pipeline-trace.txt
c3b210b466d518464ab239e125c719a521ce4bfa8783d4fedf92392786851693  B1 pipeline-trace.txt
17e6ad06940015b52a234e0710f2dd75ae11e26c92f9e2b996be701720e210b3  A2 pipeline-trace.txt
2f530ff859a082201637e2887b23c1903b587e067b8967e92f921c25900acb36  B2 pipeline-trace.txt
dd541898083901485a8c7f61d8c3aa336d541f955afa9fa5c48a218a0cb09d8e  all state-cache-after.txt
13e68070dac612ecacb8fe87809900f58769bd552f7f8afce0ff641adb72f2da  all dxt-stats.txt
```

## Warm state cache with one worker: pipeline candidate accepted

The production-facing gate kept the candidate D3D9, fused-DXT Box86, dedupe,
`DXVK_CONFIG=dxvk.numCompilerThreads = 1`, route and clocks identical. Only
`DXVK_STATE_CACHE=0/1` changed. The disabled arms proved isolation with zero
background jobs, 46 main-thread driver calls and 46 draw misses. Enabled arms
had 14 background jobs and 47 driver calls, including one cached state not
drawn by this route. Cache SHA `d04158e8...` and size `13151` bytes remained
identical before and after every arm.

```text
A1 /storage/roms/ports/ablogs/dxvk-state-cache-enable-ab-a1-off-20260825
B1 /storage/roms/ports/ablogs/dxvk-state-cache-enable-ab-b1-on-one-20260825
A2 /storage/roms/ports/ablogs/dxvk-state-cache-enable-ab-a2-off-20260825
B2 /storage/roms/ports/ablogs/dxvk-state-cache-enable-ab-b2-on-one-20260825
```

| measurement | A1 off | B1 on/one | A2 off | B2 on/one | off mean | on/one mean |
|---|---:|---:|---:|---:|---:|---:|
| first game/read load | `2480.737` | `2479.682` | `2319.988` | `2450.202` | `2400.363` | `2464.942 ms` |
| first location pipeline | `1550.009` | `1300.183` | `1720.044` | `930.008` | `1635.027` | `1115.096 ms` |
| second location pipeline | `939.992` | `820.021` | `939.951` | `689.985` | `939.972` | `755.003 ms` |
| both pipeline gaps | `2490.001` | `2120.204` | `2659.995` | `1619.993` | `2574.998` | `1870.099 ms` |
| loaded game/read worker | `1400.008` | `1951.001` | `1409.979` | `1440.157` | `1404.994` | `1695.579 ms` |

Enabling the warm cache with one worker reduced the two location pipeline gaps
by `704.900 ms` (`27.4%`). Both B arms beat both A arms as a pair, and each
individual cluster moved in the same direction. This directly establishes
that the cache-on/one-worker research stack beats the same binaries with the
current cache-off behavior for the measured pipeline freezes.

It does not improve asset loading. B1's later `1951 ms` game/read pause is
preserved rather than averaged away, but it is not a compiler regression:
there are no pipeline events anywhere in that interval, while device pressure
recorded `14.070 MiB` of MMC reads taking `2308 ms`, writes taking `4131 ms`,
and elevated I/O PSI. B2 returned to `1440 ms`. The two large resource stalls
remain an independent open problem.

Post-run Internet/source research agrees with the measured direction but is
not used as proof. The README at the exact Sarek commit says state-cache is
intended to recompile pipeline states ahead of time on later runs and generally
reduce stutter, while warning that using more cores for shader compilation can
make the game unresponsive:
<https://github.com/zeyadadev/DXVK-Sarek/blob/617958fe1cf2b10e06fa751d3e40bd765dcf2cc6/README.md#state-cache>.
The same exact tree documents positive `dxvk.numCompilerThreads` values as an
explicit thread-count override:
<https://github.com/zeyadadev/DXVK-Sarek/blob/617958fe1cf2b10e06fa751d3e40bd765dcf2cc6/dxvk.conf#L255-L261>.
The device A-B-A-B supplies the quantitative claim.

This accepts the combined pipeline settings as a production candidate, not as
production itself. A final gate must run with memory tracing disabled and
compare the complete candidate (fused DXT plus cache-on/dedupe/one-worker)
against exact FINALPLAY16, then repeat the correct visual route and live
identity check. Promotion is forbidden if that combined A-B loses the
component improvements or changes cache unexpectedly.

Raw ignored hashes:

```text
42b2304aa46dacc8431d3b990be4bb87f1372d3cbcfe0408bbee8f49496860da  A1 pipeline-trace.txt
7abaa2e7360a095eb5b79942cf9ea35e708c8e79a6992e5f5314669a6d5a7097  B1 pipeline-trace.txt
8810c659969032a5ab3661b5b280f50a8618ec45994362b303892468ba1867bc  A2 pipeline-trace.txt
b8ba47c7d835645e32aa0c4817d2e3e74413d61035224158c4f0805b243db7d0  B2 pipeline-trace.txt
76c57ffb64901696ba8fab4222802651dea23033380d5e56455fa6b69cca780a  both off state-cache-after.txt
dd541898083901485a8c7f61d8c3aa336d541f955afa9fa5c48a218a0cb09d8e  both on state-cache-after.txt
13e68070dac612ecacb8fe87809900f58769bd552f7f8afce0ff641adb72f2da  all dxt-stats.txt
```

## Corrected final gate against exact FINALPLAY16

The first combined A-B-A-B was invalid as a production comparison and is
preserved as such. Its `production` arms used Box86 `/proc/<pid>/exe` SHA
`83f9349c...`, not exact FINALPLAY16 SHA `104c79bc...`. Its `15.9%` direction
is secondary replication only and was not used to promote.

The corrected A-B-A-B used exact FINALPLAY16 Box86 in both controls, the same
memory-only PRESENT counter in both controls, the verified candidate pair in
both candidate arms, one process, fixed clocks, correct save rows and the
unchanged 13,151-byte cache:

| controlled gap | A1 control | B1 candidate | A2 control | B2 candidate | control mean | candidate mean | delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| first game/read load | `2669.978` | `2339.982` | `2559.956` | `2307.109` | `2614.967` | `2323.546 ms` | `-11.1%` |
| first location pipeline | `1750.040` | `950.835` | `1640.495` | `969.547` | `1695.268` | `960.191 ms` | `-43.4%` |
| second location pipeline | `840.074` | `699.318` | `907.858` | `859.999` | `873.966` | `779.659 ms` | `-10.8%` |
| both pipeline gaps | `2590.114` | `1650.153` | `2548.353` | `1829.546` | `2569.234` | `1739.850 ms` | `-32.3%` |
| loaded game/read worker | `1630.000` | `1389.849` | `1649.832` | `1389.675` | `1639.916` | `1389.762 ms` | `-15.3%` |
| controlled sum | `6890.092` | `5379.984` | `6758.141` | `5526.330` | `6824.117` | `5453.157 ms` | `-20.1%` |

Both complete candidate arms beat both exact controls. One individual value did
not: B2's second pipeline gap was `19.925 ms` above A1. The claim is therefore
the symmetric mean and complete controlled sum, not universal per-sample
dominance.

```text
logs/rg353vs/freeze-candidate-fp16-ab/
```

Selected ignored hashes:

```text
0d8a7221ae33ce3cf277e9ecd863e3224df314fc2517f32aa4b7832962273f94  A1 device-gaps.txt
82b46152c2092fca798c3a0f15b716b52c293403dcec879ea9c2662afbbb8e5f  B1 device-gaps.txt
30a159581a3ff68e2a3f32c15ab5d798e1c05b24ac0f37714bd4d0743d54087e  A2 device-gaps.txt
d874b8eb07ec26f4d28d67e7814d0a2e5cd64b7aff2c338efa7a749234dd18e1  B2 device-gaps.txt
15674f6a63826a4e7cbd9a908cefeef5811c5e94dbb5647f11ecfca6c586e4b6  A1 identity.txt
834eef0a373b031ef4ebb9ced865cae99c04027746b20721cee13b467d27b293  B1 identity.txt
b06be9a31b2377c940d91c6681e3baea426ab68306cbd7b1a31f06efc93f1932  A2 identity.txt
76c0ac00b54b1dcb811e9b8ab573c88b5fd727a7f8cb03e175a63a3b1f67ef7e  B2 identity.txt
```

## Post-run source audit and production separation

Reading the exact Sarek source after the gate found that `DXVK_ALL_CORES=1` is
applied after `dxvk.numCompilerThreads` and silently overrides it. The fixed
launcher therefore rejects inherited compiler/cache variables and explicitly
unsets `DXVK_ALL_CORES` before exporting the measured one-worker setting.

The clean D3D9 build contains patches 01, 02 and the unconditional exact-pair
production patch 08. PRESENT/timeline symbols are absent. Two independent
build directories initially differed only in PE timestamp/checksum bytes;
with `SOURCE_DATE_EPOCH=1787659200` both produced SHA
`4918b0283329702116dc64fba2e7be992a8b67ef2534ccf5af919f334c690650`.

Box86 patch 21 selects the verified fused conversion through a production entry
that does not update the research atomic counters. Two builds with lock-file
epoch `1756000000` produced SHA
`51dfcc130b9760970189a67edd8cd78c777c5d69c8b9ec07cfbc5657821d9be9`.
The earlier wall-clock build `38aafbee...` passed correctness but was replaced
and is not production.

The final ordinary-entry gate used those deterministic bytes, loaded the
correct save, walked twelve bursts, visually retained correct geometry and
textures, and verified `18/18` live identities. Cache SHA stayed `d04158e8...`;
graceful cleanup left zero instances, zero relevant mounts and a free lock.

FINALPLAY17 is therefore promoted. The full production decision, artifacts and
caveats are in
`MGS2_FINALPLAY17_FREEZE_REDUCTION_PRODUCTION_2026-08-25.md`.

## Rollback

FINALPLAY17 is now the default. Exact FINALPLAY16 DXVK remains available for
one launch:

```sh
MGS2_RENDERER=dxvk16 /storage/roms/ports/MGS2-Substance.sh
```

The renderer-family rollback remains:

```sh
MGS2_RENDERER=wined3d /storage/roms/ports/MGS2-Substance.sh
```

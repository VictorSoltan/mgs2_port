# DXVK pipeline gap, Mali и state-cache A/B (2026-08-25)

## Решение

`FINALPLAY16` не изменён. В production по-прежнему:

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

## Rollback

Ни один production файл или default не изменён. State-cache A/B работал только
через research launcher и отдельный каталог. Немедленный renderer rollback
остаётся:

```sh
MGS2_RENDERER=wined3d /storage/roms/ports/MGS2-Substance.sh
```

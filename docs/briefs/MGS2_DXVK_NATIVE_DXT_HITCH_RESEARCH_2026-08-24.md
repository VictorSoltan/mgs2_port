# Нативный DXT и DXVK first-use hitch (2026-08-24)

## Решение

`FINALPLAY16` не изменён. Нативные leaf-декодеры DXT1/DXT3/DXT5 корректны на
проверенной выборке реальных входов, но **не сокращают целевой gameplay hitch**.
Кандидат остаётся выключенным исследовательским артефактом и не должен
выбираться production launcher'ом.

Эксперимент также исправляет слишком сильную исходную формулировку. Первый
профиль доказал, что во время паузы texture worker занят DXT-путём. Он не
доказал, что именно этот worker задаёт длительность паузы. После устранения DXT
работа worker исчезла из интервала, а wall-clock интервал остался тем же.

Полностью удалить Box86 без нативного порта игры нельзя: исполняемый файл игры
и значительная часть её Win32 окружения остаются 32-битным x86-кодом. Узкие
нативные мосты для доказанных hot path возможны; этот brief фиксирует границу
одного такого моста.

## Контроль и маршрут

Все принимаемые числа получены на RG353VS с CPU `1992000`, одним процессом и
одним сохранением. Автоматика визуально доказала именно путь `LOAD GAME`, а не
`NEW GAME`:

```text
menu-marker new=0.474 load=0.210
menu-marker new=0.200 load=0.474
save rows: 09 -> 08 -> 07
yes/no gate: PASS
screen-gray-mean=0.206
```

PRESENT и `perf` читались внешними процессами. Горячий texture worker ничего не
писал в лог. Live `/proc/PID/exe` и manifest проверялись до измерения.

Контрольный Box86:

```text
box86-fp17-dxvk-quiet
83f9349c6dc26f8f769e714a5ed57c4d76f3a523161ead31f75e52ccc1da7fba
```

Целевой интервал после `shot:6-loaded`:

```text
baseline primary gap     1619.763 ms
baseline following gap    390.028 ms
main thread              317 / 725 samples  (43.7%)
texture worker           287 / 725 samples  (39.6%)
```

В worker самые горячие гостевые страницы были
`mgs2_sse_rg353vs_port.exe+0x516000`, `+0x511000`, `+0x515000`; нативный
RGBA-dither также занимал 85 из 287 worker samples. Это обосновало ограниченный
DXT-эксперимент, но ещё не причинный вывод о wall time.

## Кандидат

`box86-patches/19-native-dxt-research-default-off.patch` добавляет:

- три уникальные 48-байтные сигнатуры DXT1/DXT3/DXT5 точного EXE;
- `MGS2_BOX86_NATIVE_DXT=1` для нативного пути;
- `MGS2_BOX86_NATIVE_DXT=2` для bounded differential verify;
- внешне читаемые bounded counters без hot-thread logging;
- cold signature discovery и cached сравнение адреса на горячем пути.

Verifier вызывает перемещённую копию оригинальной guest-функции, сравнивает все
256 выходных байт блока с native результатом и при расхождении возвращает guest
bytes. Он сравнивает первые 1024 вызова и затем каждый 512-й, не более 4096 за
процесс. Это распределяет выборку по полной последовательности, а не только по
её началу.

### Почему арифметика гибридная

Две правдоподобные реализации были отвергнуты настоящим guest oracle:

1. Все промежуточные значения `double`: 4096 сравнений, 2 mismatch. Первый —
   DXT5 call 234, output byte 116, guest `0x3e6e643c`, native `0x3e6e643b`.
2. Все промежуточные значения `float`: 4096 сравнений, 13 mismatch. Первый —
   DXT5 call 26, alpha pixel 14, guest `0x3ebebec0`, native `0x3ebebec1`.

Причина находится в Box86 x87 cache model при
`BOX86_DYNAREC_X87DOUBLE=0`: `FLD float` начинает F32-цепочку, а `FILD m32`
начинает F64-цепочку и продвигает соседний операнд. Поэтому RGB interpolation
должна быть staged float32, а integer scale и alpha weighting — staged double с
финальным `FSTPS`. Два реальных mismatch-блока сохранены как self-test probes.

Финальный correctness gate:

```text
candidate hash d244919ea84ddba44782fd10a35609d2a6c561d47b15426b63dfc60e71960bcc
armed=1 verify=1
DXT5 calls=1425720
compared=3806 mismatched=0 skipped=0
route gates=PASS
```

Это сильная проверка выбранных входов, не доказательство корректности на всех
возможных DXT-блоках игры.

## Performance: отрицательный результат

Первая корректная performance-сборка `d45973...` делала cold signature checks
для ещё не встреченных DXT1/DXT3 перед каждым cached DXT5. Профиль показал
накладные расходы в `rb_get`, mutex, `memcmp` и matcher; интервал вырос до
`1780.018 ms`. Этот вариант отвергнут.

В `d244919...` cached адреса проверяются первым коротким циклом, а signature
discovery выполняется только если cached target не совпал. После повторного
correctness gate проведён симметричный performance run (`mode=1`, четыре
одинаковых walk bursts):

| | baseline | native DXT cached-first |
|---|---:|---:|
| primary gameplay gap | 1619.763 ms | 1629.996 ms |
| following gap | 390.028 ms | 438.852 ms |
| main samples в primary | 317 | 316 |
| texture-worker samples в primary | 287 | 24 |
| DXT calls | guest path | 1,425,720 native |

Нативизация сняла worker с критического интервала, но не ускорила предъявление
следующего кадра. Это не «маленький положительный эффект»: измеряемая цель
осталась неизменной, а значит promotion запрещён.

Thread-filtered guest resolution показывает одинаковое состояние главного
потока во всех трёх прогонах: Wine `win32u/ntdll` message/wait/yield path,
включая страницы около `NtUserWaitForInputIdle`, `peek_message`,
`NtYieldExecution`, и нативные `sched_yield`/`getrusage`. Flat samples не
доказывают, какой объект или поток удерживает условие, поэтому подменять эти API
или возвращать из wait немедленно нельзя.

## Следующая гипотеза и refuting result

Гипотеза: целевой no-PRESENT интервал задаёт отдельное условие главного
message/yield loop, а DXT либо выполняется раньше, либо является параллельной
работой, не лежащей на wall-clock critical path.

Следующий прибор должен оставаться внешним и bounded:

1. снять временной ряд DXT counters относительно уже существующих route markers,
   чтобы различить startup/preload, save load и первый walk;
2. локализовать ровно один main-thread wait/message path в целевом интервале,
   не возвращаясь к широкому `wchan` sampling;
3. только после идентификации владельца условия строить default-off A/B.

Гипотеза отвергается, если временной ряд показывает новую DXT-работу внутри
целевого интервала и её завершение совпадает с первым PRESENT, либо если
ограниченный wait capture не находит устойчивого main-thread условия.

До этого fused high-level texture converter и тем более глобальное изменение
Wine wait semantics не обоснованы.

## Артефакты и rollback

Tracked record:

- `box86-patches/19-native-dxt-research-default-off.patch`;
- `device/FINALPLAY16_DXVK_DXT_VERIFY.manifest`;
- `device/launch-dxvk-sarek-dxt.sh`;
- `harness/box86_dxt_stats.py`;
- `harness/dxvk_hitch_profile_capture.sh`;
- `harness/dxvk_guest_gap_analyze.py --tid`.

Локальные raw artifacts находятся под `logs/rg353vs/dxvk-hitch/` и намеренно
не публикуются. Production rollback не менялся:

```sh
MGS2_RENDERER=wined3d /storage/roms/ports/MGS2-Substance.sh
```

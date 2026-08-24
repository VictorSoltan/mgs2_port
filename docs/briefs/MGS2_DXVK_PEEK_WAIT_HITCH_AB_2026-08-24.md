# PeekMessage wait: provenance до A/B (2026-08-24)

## Исправленное решение

`FINALPLAY16` не загружает `user32_peek1.dll`. Он загружает системный
ROCKNIX `user32.dll`, в котором нет caller-specific четырёхмиллисекундного
ожидания. Поэтому значения

```text
MGS2_PEEK_HOT=401176
MGS2_PEEK_WAIT=1
MGS2_PEEK_WAIT_MS=4
```

остались в DXVK launcher как неиспользуемое окружение и **не могут создавать
1.62-секундный gameplay gap**.

Первоначально был проведён прогон `4 -> 1 -> off`, но проверка live bytes
показала, что это не A/B кода: во всех трёх условиях работал один системный
`user32.dll`, не читающий эти переменные. Числа сохранены как provenance
ошибочного experiment boundary, но не выдаются за измерение влияния wait.

`FINALPLAY16` не изменён. Временный measurement override удалён из
исследовательского launcher после обнаружения no-op. Профилировщик теперь
обязательно сохраняет путь и SHA live `user32.dll`, чтобы эта ошибка не
повторилась.

## Откуда появилась гипотеза

Интернет-исследование первичного исходного кода
[MGSHDFix BusyLoopFix](https://github.com/ShizCalev/MGSHDFix/blob/master/src/fixes/busy_loop_fix.cpp)
показало два anti-spin уровня в Master Collection:

1. после пустого `PeekMessageW` выполняется
   `MsgWaitForMultipleObjects(..., 1 ms, QS_ALLINPUT)`;
2. отдельный game-level `ActorWait` сравнивает deadline с игровым elapsed time и
   отдаёт часть ожидания ОС.

[PR #225](https://github.com/ShizCalev/MGSHDFix/pull/225) фиксирует мотивацию
вокруг дорогого QPC busy loop. Проверенный PR commit
`bf91e995bac78f2ec1a2297f9cfff0d531137a11` использовал повторный `Sleep(1)`
при остатке больше 3 ms. Один high-resolution wait, 1 ms spin margin и предел
50 ms находятся в более позднем master commit
`604e204d7e3d4a76f0f8dd2f1f393fb0ca3a5433`; это не свойства самого PR #225.

Это Master Collection x64, поэтому его адреса и сигнатуры неприменимы к
Substance 2003 x86. Переносима только гипотеза о механизме.

Локальный `user32_peek1.dll` действительно реализует первый уровень для guest
caller `0x401176`. Совпадение `1620 / 4 ~= 405` выглядело достаточным основанием
для дешёвого A/B — до проверки фактически загруженного DLL.

## Live provenance

Оба точных файла присутствуют на устройстве:

```text
1635f4c6917dc54f6764e1fceddd39b4ce04692a93a88f473fa6cbcf03d83d84  system user32.dll
4f8b82c7a9dd0fab03b699aa8948f6c76852801f17a096cff22384dc2997fe4e  user32_peek1.dll
```

Research launcher сначала снимает любой старый bind mount `user32.dll`. Затем
он монтирует `user32_peek1.dll` только в WineD3D-ветке:

```sh
if [ -z "${MGS2_DXVK_D3D8_DLL:-}" ]; then
    mount_bind .../user32_peek1.dll /usr/lib/wine/i386-windows/user32.dll
fi
```

Все три прогона использовали direct32 DXVK с непустым `MGS2_DXVK_D3D8_DLL`.
Их `maps.before` показывает `/usr/lib/wine/i386-windows/user32.dll`, а game log
для каждого содержит успешный `18 of 18` identity gate. Точный research
manifest требует именно системный SHA `1635f4...`; patched SHA `4f8b82...` этот
gate не прошёл бы.

Production manifest содержит ту же строку:

```text
/usr/lib/wine/i386-windows/user32.dll  1635f4...  ROCKNIX-20260822-system
```

Следовательно, наличие `MGS2_PEEK_WAIT_MS=4` в launcher не доказывало наличие
реализации, которая его читает. Это именно тот класс ошибки, от которого правило
«verify loaded bytes» должно защищать.

## Инертные контрольные прогоны

Маршрут каждого прогона был корректен: один процесс, CPU `1992000`, то же
сохранение, `LOAD GAME`, строки `09 -> 08 -> 07`, yes/no PASS, gray mean
`0.206` и четыре walk bursts.

| Run | запрошенное окружение | live user32 | primary gap | following gap |
|---|---:|---|---:|---:|
| A | every 1, 4 ms | system `1635f4...` | 1599.979 ms | 389.514 ms |
| B | every 1, 1 ms | system `1635f4...` | 1619.966 ms | 392.696 ms |
| C | disabled, 0 ms | system `1635f4...` | 1619.946 ms | 359.997 ms |

Одинаковый результат ожидаем для неиспользуемых переменных. Эти прогоны не
проверяют, что случилось бы при насильственном монтировании patched user32.
Такой тест не нужен для причинного вопроса о текущем production: код в нём уже
отсутствует. Кроме того, подмена системного user32 при системном DXVK win32u
создала бы новый несовпадающий Wine bundle.

## Что показал статический разбор Substance 2003

Точный `mgs2_sse_rg353vs_port.exe` импортирует Win32
`QueryPerformanceCounter`, `Sleep[Ex]`, `WaitForSingleObject`,
`WaitForMultipleObjects`, `PeekMessageA` и `MsgWaitForMultipleObjects` из
KERNEL32/USER32. Прямых игровых импортов `NtQueryPerformanceCounter`,
`NtDelayExecution` или `NtWait*` нет.

Найдена собственная deadline-функция игры около `0x8a1ea0`:

```text
0x8a1ea9  QueryPerformanceCounter
          compare current tick against game target/base
          convert positive remaining ticks to milliseconds
0x8a1f08  Sleep(remaining)
```

Её вызывают пять frame/timing paths около `0x8a2f91`, `0x8a2ff0`,
`0x8a3055`, `0x8a3090` и `0x8a3110`. Это гораздо ближе к роли MGSHDFix
`ActorWait`, чем общий empty-Peek loop, но статический код ещё не доказывает,
что функция вызывается внутри целевого gap или получает аномальный timeout.

## Следующая гипотеза и refuting result

Следующая гипотеза: целевой gap удерживается game-level deadline либо object
wait, видимым в небольшом наборе прямых импортных callsites.

Нужен default-off bounded census на 32-битных PE-entry points, где
`__builtin_return_address(0)` всё ещё является адресом EXE:

1. QPC counts по guest caller;
2. `Sleep[Ex]` с timeout;
3. single/multiple-object waits с handle/count, timeout и return class;
4. message waits отдельно в user32 только если первые три не объясняют gap.

Глобальный ntdll hook сейчас не обоснован: прямых игровых Nt-imports нет, а на
Unix-границе guest caller уже потерян. Горячий путь может обновлять только
bounded memory counters/ring; внешний reader синхронизирует deltas с PRESENT
gap и route markers. Никаких per-call logs.

Первый приоритет — caller `0x8a1eaf` (return после QPC) и timeout из
`0x8a1f08`. Гипотеза отвергается, если в целевом gap этот path не активен либо
его cumulative timeout слишком мал, чтобы объяснить wall time. Тогда census
должен указать object-wait caller/handle или отправить исследование к владельцу
worker condition.

## Артефакты и rollback

Tracked record:

- `harness/dxvk_hitch_profile_capture.sh` — effective environment плюс live
  `user32.dll` path/SHA;
- этот brief и ссылка из `docs/README.md`.

Raw captures остаются в игнорируемом
`logs/rg353vs/dxvk-hitch/dxvk-peek-{a4,b1,c0}-gated-20260824/`.

Production rollback не менялся:

```sh
MGS2_RENDERER=wined3d /storage/roms/ports/MGS2-Substance.sh
```

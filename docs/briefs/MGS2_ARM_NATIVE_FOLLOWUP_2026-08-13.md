# MGS2 RG353VS — точечные ARM-мосты после FINALPLAY

Дата: 13--14 августа 2026. Статус: звуковой CPU fix измерен и включён в
FINALPLAY4. Renderer AABB bridge остаётся архивным диагностическим кандидатом,
но снят с очереди: valid reinforcements profile не даёт ему достаточного
потенциала, а корректного scene-matched A/B для него нет.

## Короткий результат

Предположение «раньше большой прирост дал перенос модулей на ARM64» верно только
по направлению. Целый Wine на AArch64 (Hangover) запустил игру, но дал 0.4 fps.
Рабочий результат получился из трёх узких изменений:

```text
FINALPLAY batcher       ~1299 source draw -> ~151 GL call в тяжёлом кадре
Box86 native memmove    Wine _sse2_memmove -> overlap-safe ARM libc memmove
D3D8 DISCARD shadow     убраны два обратных чтения mapped upload по 512 KiB/кадр
```

До последних двух исправлений фиксированная тяжёлая точка была 23.6--24.9 fps;
после них три квалификационных окна дали 30.0/30.0/30.1 fps. Это не означает,
что любая битва теперь должна идти в 30: valid reinforcements profile 14 августа
держался около 18--19 fps и в плотной части дошёл до 11.9--14.8 fps.

## Что подтвердил research

- Box86 официально описывает native wrapping системных библиотек как один из
  основных механизмов ускорения. Это поддерживает узкие мосты для доказанных
  hot functions, но не произвольную замену гостевого кода:
  <https://github.com/ptitSeb/box86>.
- Arm рекомендует уменьшать число draw calls и группировать состояние/рисование;
  именно это уже делает FINALPLAY, поэтому повторять эту идею новым общим патчем
  нечего:
  <https://developer.arm.com/-/media/Files/pdf/graphics-and-multimedia/Guides/DUI0555C_mali_optimization_guide.pdf>
  и
  <https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/mali-performance-5-an-application-s-performance-responsibilities>.
- Официальная документация Panfrost подтверждает поддержку Mali-G52; вывод о
  скорости всё равно должен делаться при фиксированных частотах на самом
  RK3566: <https://docs.mesa3d.org/drivers/panfrost.html>.
- В актуальном FluidSynth не найден готовый NEON-патч, который можно безопасно
  перенести как решение этой игры: <https://github.com/FluidSynth/fluidsynth>.

Отдельный аудит предоставленного CrossOver Android 17 уже записан в
`MGS2_CROSSOVER_AUDIO_PERF_AUDIT_2026-08-13.md`: его `dsound`, `dmime`,
`dmusic`, `dmsynth` и `winealsa.drv` побайтно совпадают с Wine 2.8. Скрытого
Android-аудиофикса там нет. Полезная GLES-часть CrossOver уже перенесена в
текущий renderer.

## Новый профиль production

Добавлен внешний reader `harness/box86_guest_snapshot.py`; на hot path он не
пишет. Box86 лишь складывает соответствия JIT block в ограниченное memory map,
а `perf` и reader снимают их снаружи.

Контрольный 30-секундный профиль после автозагрузки:

```text
guest records       15887 / 262144, overflow=0
resolved JIT        4881, unresolved=0

guest module samples
game                1499
wined3d             1109
dsound               762
dmsynth              669
d3d8                 335
ucrtbase             108

top blocks
dsound  RVA 0x4960  622   DSOUND_MixToPrimary
d3d8   RVA 0x4011  197   DrawPrimitive / exact AABB culler path
wined3d RVA 0x5c760 189   draw_primitive
dmsynth RVA 0xf810  154   fluid_rvoice_dsp_interpolate_4th_order
```

Старый 744-sample `_sse2_memmove` исчез: прежний native bridge действительно
делает работу. Следовательно, новый перенос надо искать в оставшемся профиле, а
не переносить ещё один модуль целиком.

Артефакты: `logs/rg353vs/guestmap-current-20260813/`.

## Patch 34: ошибка порядка reset в dmsynth

В launcher и исходнике default уже был `MGS2_DMSYNTH_INTERP=1` (linear), но
профиль исполнял 4th-order. Причина точная:

```text
synth_Open
  fluid_synth_set_interp_method(... LINEAR)
  synth_reset_default_values
    fluid_synth_system_reset
      каждый канал снова получает FLUID_INTERP_DEFAULT (4th order)
```

MIDI system-reset во время игры повторял тот же сброс. Patch 34 применяет
выбранный interpolation сразу после каждого `fluid_synth_system_reset()`.

Измерение candidate относительно control:

```text
                         control       patch 34
all process samples        9345          12060   (candidate-сцена тяжелее)
main thread                4441           6044
wined3d_cs                 2834           4179
dmsynth thread              781            514   -34.2%
dmsynth guest module        669            410
4th-order block             154              0
linear block                  0             77
```

Это сильный результат именно для audio deadline: звуковой поток стал дешевле,
даже когда весь остальной кадр был тяжелее. Но FPS хвоста остался примерно
17.7--17.9, поэтому patch 34 не является способом получить 25--30 fps. Также
этот прогон не воспроизвёл исчезновение SFX, следовательно называть баг звука
исправленным нельзя.

```text
wine-patches/34-dmsynth-restore-interp-after-reset.patch
binaries/dmsynth_p34_interp_reset.dll
SHA256 b4ec2cd09f26a670eb8206d708f864597d2acde84ff1788732574c116b6baed2
```

Статус: включён в FINALPLAY4 вместе с exact DirectSound FIR bridge. Он остаётся
измеренным облегчением audio deadline, а не FPS fix: ручная проверка не
воспроизвела intermittent SFX loss, поэтому исчезновение gameplay SFX всё ещё
требует отдельного timestamp-correlated capture.

## Обнаруженный риск прежнего native memmove

Чтение patch 02 нашло две проблемы, не доказанную причину текущих фризов:

1. проверялась защита только первого байта, после чего native `memcmp` читал 20;
   у конца mapping это могло пересечь unmapped page;
2. 20 байт заканчивались до первой ветки и были слишком похожи на общий
   dst/src/length preamble.

Исправленный patch 04 проверяет весь диапазон, сравнивает 48 независимо
пересобранных exact bytes Wine `_sse2_memmove` и атомарно кэширует единственный
guest address. Этот proof теперь входит в Box86 FINALPLAY4, но не является
объяснением уже виденных фризов: для такой атрибуции нужен отдельный owner/wait
capture.

## Patch 35 + Box86 patch 05: архивный renderer-кандидат

Patch 31 заменял exact per-draw box одним консервативным box на запись и был
откачен после реальной игры. Новый вариант сохраняет исходный алгоритм побайтно:

- `d3d8_mgs2_scan_aabb()` только удерживается `noinline`;
- Box86 распознаёт exact 32-byte prologue;
- в native ARM уходит только цикл чтения position, `isfinite`, min/max;
- range validation, culling policy и итоговое решение остаются в Wine;
- перед публикацией bridge выполняется self-test;
- всё выключено без `MGS2_BOX86_NATIVE_AABB=1`.

```text
wine-patches/35-d3d8-native-aabb-target.patch
box86-patches/05-native-d3d8-aabb.patch
binaries/d3d8_p35_native_aabb_target.dll
SHA256 4ec1b13f30a8fb603d8f9b627739e81197b5170772afda6c73cc0994ea4ed619
binaries/box86-native-aabb1
SHA256 3ebf636423d39d6b3de29db8d8aedabd0837e1724cfa6d3c9f9eec5486ed553c
```

Box86 patch chain 01--05 и Wine patches 34--35 повторно применены с `-F0` и
дают проверенные target files. Box86 собран, его максимальная glibc requirement
остаётся 2.38, как у текущего production binary.

Статус: **не production и не следующий A/B**. Это именно чистый ARMv8 AArch32
мост, но 14 августа valid reinforcements profile показал 272 samples в целом
D3D8 visibility path, тогда как лишь его внутренний scan был bridge target;
остальные большие потребители -- `wined3d_cs`, `libmali` и game workers.
Следовательно, даже идеальное устранение scan не обещает заметного сдвига
11.9--14.8 fps. Кандидат не развёрнут и сохранён только как воспроизводимый
research artifact.

### Что изменило решение 14 августа

В подтверждённой сцене с подходящим подкреплением `wined3d_cs` имел 2,755
samples: 1,218 в Box86/Wine и 1,208 уже в нативном `libmali`. Верхний WineD3D
block -- `draw_primitive()` -- делает GL-вызовы и меняет live context/state;
его нельзя заменить чистой ARM-функцией. Это опровергает план «перенести
`wined3d_cs` / WineD3D целиком». Ближайший измеримый вопрос другой: какие пути
draw всё ещё обходят существующий batcher и создают driver submissions. Полный
capture, ограничения и артефакты: `MGS2_REINFORCEMENT_ARM_TARGET_2026-08-14.md`.

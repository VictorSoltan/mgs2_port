# MGS2 RG353VS — brief #23: звук возвращается только через pchannel2, но routing перегружает игру

Дата: 4 августа 2026.

## Короткий итог

Последний тест с принудительным тоном закрыл границу `dmsynth -> DirectSound`:
тон `1 kHz`, амплитуда `±8192`, длительность `50 ms` был записан в тот же
`samples`, который передаётся в `synth_sink_write_data()`. После ручного arm уже
в gameplay marker перешёл `2 -> 3`, но пользователь тон не услышал.

Следовательно, дальнейшие изменения FluidSynth gain, wave, group и
`Lock/Unlock` сами по себе не объяснят тишину.

## Что реально различает рабочий и нерабочий запуск

| Вариант | Результат | Примечание |
|---|---|---|
| `dmime_graphqi.dll` + `dmsynth_wine112.dll` | звука нет | штатный baseline |
| локальный `dmime_route.dll` | звука нет | только route census, без pchannel allocation |
| `dmime_pchannel2.dll` + `dmsynth_wine112.dll` | звук есть | меню подтверждено пользователем |
| `dmime_pchannel2.dll` + `dmsynth_sinkaudible14.dll` | звук есть | но очень тяжёлые лаги |
| `dmime_pathlimit2.dll`, limit=2 | звук есть | лаги меньше, но остаются |
| `dmime_pathlimit2.dll`, limit=1 | звук есть | лаги всё ещё заметны |

SHA-256 ключевых файлов:

```text
dmime_graphqi.dll       6154cc047b755fa9e388860edf873f78e0003440623cca652ff3144588044fa4
dmime_pchannel2.dll     3c047d8a1768bea72f0a0973c5d3fd9a6abe04e1ac5aae23f5abeecece992352
dmime_route.dll         95c91a3e1469e676df7bf9e0e275a067aefa26fee0f0cfdcfb30f795d32f17d0
dmsynth_wine112.dll     513be01718cf0d6f3e8a300e153c2094eac0694f1317c692e63e3437412ccb0b
dmime_pathlimit2.dll    191cf22f82a4eae14b32273e46e20ce03c389746f30b9d4fce21ef1dbbe89f61
```

## Что делает pchannel2

`dmime_pchannel2.dll` — это текущая сборка `performance.c` с disjoint
PChannel allocation:

```text
audio-path #0 -> PChannels 0..15  -> DirectMusic group 1
audio-path #1 -> PChannels 16..31 -> DirectMusic group 2
```

Каждый созданный audio-path получает собственный port и DirectSound buffer.
Именно эта маршрутизация позволяет целевому `group=2, MIDI 90 3c 7f` дойти до
слышимого output. `graphqi`/`route` оставляют PChannel namespace схлопнутым;
group 2 тогда не попадает в рабочий port.

Ограничение числа активных path уменьшает лаг, но не устраняет его. Значит,
стоимость находится не только в количестве активных sink threads: нужно
проверить распределение MIDI-сообщений, число созданных ports и CPU внутри
DirectMusic/FluidSynth при disjoint routing.

## Что доказано про sink и DirectSound

`dmsynth_sinkprobe11` на целевом event зафиксировал:

```text
group=2 status=0x90 note=0x3c velocity=0x7f
Render frames=441 bytes=1764, peak ненулевой
Lock hr=0, Unlock hr=0
copied peak/checksum == Render peak/checksum
status=5 (PLAYING | LOOPING), volume=0xffffffff, frequency=22050
```

Принудительный tone-тест исключил фоновую voice: marker был вооружён вручную
уже после входа в gameplay. Тон не дошёл до динамика.

При тяжёлом `MGS2_DSOUND_PROBE=1` stage peaks были ненулевыми на всех стадиях:

```text
unlock -> tmp -> vol -> final
22866 -> 27349 -> 2394 -> 3947   (x1e-5)
```

Но probe заметно тормозит игру и сам является timing side-effect. Его нельзя
оставлять production fix.

## Текущая граница дефекта

```text
MGS2 MIDI event
  -> dmime PChannel routing (group 2)
  -> dmsynth / FluidSynth voice
  -> Render PCM
  -> DirectSound Lock/Unlock
  -> primary mix / audio output
```

Functional regression находится на `dmime` routing: baseline `graphqi` тихий,
`pchannel2` слышен. Performance regression появляется после включения этого
routing, даже с быстрым `dmsynth_wine112`.

## Следующий research (один точечный hook)

Не менять DirectMusic gain, wave, PipeWire или DirectSound. Нужен лёгкий
in-memory recorder в `dmime/performance.c`, без per-render файлов:

```text
CreateAudioPath / CreateStandardAudioPath count
path pointer; pchannel_base; pchannel_count
port pointer; active flag
MIDI messages per port (group/status/note)
```

Параллельно в `dmsynth` — только счётчики Render frames/voice count/CPU time на
один sink. Цель: определить, что именно создаёт лаг:

1. duplicate active paths/ports;
2. одно MIDI-сообщение размножается на несколько ports;
3. FluidSynth получает лишние voices;
4. routing search/lock стал горячим путём.

После этого нужен production-патч, который оставляет один рабочий port для
group 1 и один для group 2, но не запускает дублирующие audio-path sinks и не
дублирует MIDI traffic.

## Не оставлять на консоли

```text
MGS2_SINKAUDIBLE=1
MGS2_SINKPROBE=1
MGS2_DSOUND_PROBE=1
MGS2_TRACE=1
dmime_pathlimit2.dll как default без подтверждения gameplay/performance
```

Диагностический запуск остановлен; production launcher должен вернуться к
штатным `dmime_graphqi.dll`, `dmsynth_wine112.dll`, stock `dsound.dll` до
появления нового routing/performance факта.

# MGS2 RG353VS — brief #22: DirectMusic group fix не восстановил SFX

Дата: 4 августа 2026.

## Итог

Последний точечный фикс сохранял `DMUS_EVENTHEADER.dwChannelGroup` и направлял
группу 2 на FluidSynth-канал 16 вместо канала 0. Пользователь сделал два
выстрела в gameplay — игровых звуков по-прежнему нет.

Гипотеза «SFX теряются из-за схлопывания DirectMusic-группы в dmsynth»
отвергнута. Production baseline восстановлен:

```text
dmime_graphqi.dll
dmsynth_wine112.dll
stock dsound.dll
winealsa -> PipeWire
без SHOTPROBE и без trace
```

## Что доказано на реальном выстреле

В диагностическом запуске `dmsynth_sfxprobe10.dll` был пойман настоящий MIDI
note-on (`90 3c 7f`):

```text
SHOTPROBE queued ... group=2 channel=0 note=60 velocity=127
SHOTPROBE lookup ... result=0
SHOTPROBE render ... noteon=0 voices=2->3
SHOTPROBE block ... frames=441 peak=138
```

Также фиксировались другие ненулевые блоки (`peak=530`, `458`, `332`, `2419`,
`3688`, `4577`). Это означает:

1. игровой note-on доходит до `dmsynth`;
2. `dwChannelGroup=2` реально присутствует;
3. instrument/region/wave находятся;
4. `fluid_synth_noteon()` возвращает успех;
5. `IDirectMusicSynth::Render()` создаёт ненулевой PCM.

Примечание: эти строки доказывают наличие PCM внутри dmsynth, но не доказывают,
что именно этот PCM попадает в слышимый игровой микс.

## Проверенный, но отвергнутый фикс

Собран `dmsynth_groupfix.dll` из:

```text
recovered-session/wine-11.0/dlls/dmsynth/synth.c
SHA-256: b9dc577e02e191bdb1031370e978dcb2ec5619570d84bb8d80b477f6f2aae8aa
```

Изменения:

- сохранение `channel_group` в queued event;
- отображение `(group - 1) * 16 + MIDI channel`;
- настройка FluidSynth на `groups * 16` каналов;
- инициализация volume/pan/RPN для всех каналов.

DLL была реально смонтирована в игру; inode смонтированного файла совпадал с
`dmsynth_groupfix.dll`. После двух выстрелов пользователь не услышал SFX.

Следствие: одно лишь сохранение MIDI-группы не является исправлением.

## Новый результат: `dmsynth_sinkprobe11`

Чтобы проверить границу `Render -> DirectSound`, был собран лёгкий in-memory
recorder без файлового trace и без изменений production launcher. В запуске с
`dmime_pchannel2.dll` он поймал целевой event:

```text
marker=1
group=2 status=0x90 note=0x3c velocity=0x7f
sink=0x2ba0018 synth=0x2b95bd8 buffer=0x2b9f2e0
external_buffer=0
```

На реальных блоках:

```text
frames=441 bytes=1764
Render peak L/R: 66..2684 (далее меняется по блокам)
Lock hr=0, Unlock hr=0
copied peak/checksum == Render peak/checksum
status=5, volume=0xffffffff (-0.01 dB), frequency=22050
write cursor после записи движется
```

Это доказывает не только наличие PCM внутри `dmsynth`, но и успешное
копирование того же PCM в его DirectSound buffer. Буфер создан самим sink
(`external_buffer=0`), поэтому проблема не в lookup/voice/group и не в
отсутствующем `Lock/Unlock`.

## Важный побочный результат

Во время dmsynth probe наблюдались частые:

```text
Underrun detected, sink ...
```

Но probe сам создавал дополнительную нагрузку и вызывал лаги. Это не следует
использовать как основание для нового изменения sink: baseline уже содержит
Wine 11.2 sink-вариант (`dmsynth_wine112.dll`), а group-fix не дал звука.

## Текущая граница дефекта (уточнена)

Нужно различать два аудиопотока:

```text
DirectMusic/dmsynth -> собственные synth sink buffers
MGS2 SE/SPU mixer   -> Str4SpuTrans -> игровые DirectSound buffers
```

Для DirectMusic-потока теперь подтверждено:

```text
MGS2 event
  -> dmsynth note-on / FluidSynth voice
  -> IDirectMusicSynth::Render (ненулевой PCM)
  -> DirectSound Lock/Unlock (тот же ненулевой PCM)
  -> [потеря слышимого результата после sink buffer]
```

Следующий объект исследования — DirectSound/Wine audio consumer после
`IDirectSoundBuffer::Unlock`: primary-buffer mixer, `winealsa` submission или
Android/PipeWire sink. SPU-hook для этого конкретного `0x90 3c 7f` теперь не
является первым приоритетом.

## Что нужно получить от следующего research

Нужен marker-armed in-memory recorder на следующей границе — после
`IDirectSoundBuffer::Unlock`, с одним коротким измерением на тот же sink:

```text
buffer pointer; status; volume; frequency;
play/write cursor; Lock/Unlock HRESULT;
first/second region peak and checksum;
primary/mixer submission result
```

Для альтернативного SPU-потока (если исследование докажет, что конкретный
эффект идёт через него) оставить marker-armed recorder кодов:

```text
0x0083F009
0x0083F052
0x0083F040
```

На post-`SePlay` consumer записать до/после:

```text
sound_code
track_index
track_state
bank_base
sample_pointer
sample_length/end
voice_index
active_voice_mask
volume_left/right
pitch_step
flags
result
```

Если voice валиден, но PCM ring остаётся без импульса — следующий hook ставить
на один SPU-mix block перед `Str4SpuTrans`, записывая только:

```text
active mask; frames; source voice; L/R peak; write cursor
```

Запись должна быть кольцевой в памяти процесса; запрещены per-render file logs и
`MGS2_TRACE=1`, поскольку они уже делали RG353VS неиграбельным.

## Не менять до появления нового факта

- Creative ALchemy / DSOAL;
- `winepulse`, PipeWire quantum/rate;
- DirectSound replacements и byte-swap/cursor hacks;
- новые dmsynth gain/group/sink патчи;
- `dmime_pchannel2.dll` как «исправление звука»;
- общий Wine upgrade.

Эти ветки либо уже проверены, либо не прошли решающий listening test. Следующий
фикс должен следовать конкретному неверному полю SPU voice или конкретному месту,
где ненулевой voice не попадает в PCM ring.

## Состояние консоли после теста

Group-fix и sinkprobe остановлены и откатаны. На консоли восстановлен launcher
с `dmsynth_wine112.dll`, `dmime_graphqi.dll`, stock `dsound.dll`; probe и
`MGS2_SINKPROBE` выключены. Файлы `dmsynth_groupfix.dll` и
`dmsynth_sinkprobe11.dll` оставлены отдельно как исследовательские артефакты и
не загружаются baseline.

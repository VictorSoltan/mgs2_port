# MGS2 / RG353VS — brief #19: SE queue works, voice-to-SPU stage is silent

Дата: 4 августа 2026.

## Вывод

Gameplay SFX не теряются в Wine, DirectSound, DirectMusic, SE queue, lookup банка, allocator priority или лимите SE tracks. Три реальных выстрела создали корректные SE requests: bank header найден, один track выделен и SePlay() вернул 0. Пользователь эффектов не слышит.

Дефект находится после успешного SePlay(): при переводе SE track в sample/voice внутреннего SPU mixer, до готового PCM ring Str4SpuTrans.

## База — не менять

- DirectSound: stock Wine
- DirectMusic audio path: dmime_graphqi.dll
- DirectMusic synth: dmsynth_wine112.dll
- Backend: winealsa -> PipeWire
- PipeWire overrides: отсутствуют

Не возвращать Creative ALchemy, DSOAL, другую dsound.dll, DirectMusic shared-port/gain fixes, PipeWire tuning, PCM byte swap или cursor/LOCDEFER патчи. Эти ветки уже дали отрицательный результат. Последний DirectMusic/gain эксперимент отменён как неверное направление.

## Установленная граница

Brief #18 доказал:

gameplay action -> internal MGS2 SE / SPU engine -> Str4SpuTrans (stereo PCM16, 44100 Hz, ring 65152 bytes) -> IDirectSoundBuffer Lock/Unlock -> Wine / winealsa / PipeWire / speaker.

Во время gameplay ring обновляется, но PCM не получает импульса SFX. Wine DirectSound получает уже готовый игровой mix и не является целью следующего фикса.

## Recorder v5

Проверен marker-armed hook вокруг retail SePlay:

- artifact: mgs2_sse_rg353vs_seevents5.exe
- SHA-256: 48ff1fe8f8e72140fbe1a397d463b8a46deb54157448074c25cc35672e2705e3
- patched call VA: 0x008ef1d5
- retail SePlay VA: 0x008f03ff
- source: recovered-session/seevents5/seevents5.S

Hook не пишет файлы и не выделяет память в game thread. Через /proc/PID/mem он отдаёт фиксированный ring с sound_code, результатом SePlay, bank-table pointers и состоянием 12 SE playing/request tracks до и после вызова.

## Три контролируемых выстрела

Получено 14 SE events: три одинаковые последовательности из четырёх кодов.

| sound code | source/index | priority | tracks | kind | sample offset | result |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 0x83f009 | JO / 9 | 48 | 1 | 1 | 180 | 0 |
| 0x83f052 | JO / 82 | 64 | 1 | 1 | 1676 | 0 |
| 0x83f1bf | SE / 182 | 48 | 1 | 1 | 4048 | 0 |
| 0x83f040 | JO / 64 | 48 | 1 | 1 | 1308 | 0 |

Дополнительная пара: 0x97f1da / 0x83f1da, SE header 195, priority 16, tracks 1, offset 4356, result 0.

Для каждого события: result == 0; header missing == false; header tracks == 1; post-request содержит этот sound code.

В части записей старый request уже находится в playing, а новый появляется в request. Нет признаков SECan'tPlay:LowPriority, TooManyTracks, missing bank или zero-track header.

## Следующий нужный hook: post-SePlay voice activation

Нужен маленький marker-armed EXE recorder ниже SePlay, в consumer-е SE_REQUEST либо функции, создающей SPU voice. Не логировать hot loop и не сохранять PCM. На каждый из кодов выше записать:

sound_code; track_index; track_state_before; track_state_after; bank_base; sample_offset; sample_pointer; sample_length_or_end; voice_index; active_voice_mask; volume_left; volume_right; pitch_step; flags; result.

Проверить:

1. Request становится SE_PLAYING?
2. sample_pointer не NULL и указывает внутрь загруженного stage bank?
3. sample length/end больше нуля?
4. voice index выделен и выставлен active bit?
5. L/R volume и pitch step не нулевые?
6. Voice не получает сразу ended/stopped flag?

## Ориентиры для статического анализа

SECan'tPlay:LowPriority(code=%x:pri=%x:j=%x)
SE:TooManyTracks(%x):sound_code=%x
***TooMuchSoundCode(%x)***
***TooMuchBGMSoundCode(%x)***
sd_cli.c
sd_3d.c
sd_int
sd_file
Str4SpuTrans

Не ставить hook лишь на error branches: успешный путь уже доказан. Искомая функция consumes SE_REQUEST, строит voice и передаёт её SPU mixer.

## Как выбрать фикс

- request не становится playing -> repair queue consumer/reset
- sample pointer NULL/вне bank -> repair sd_file bank base/offset registration
- length/end == 0 -> repair sample descriptor/offset
- voice не выделяется -> repair voice bitmap/allocation
- volume/pitch == 0 -> repair voice parameter initialisation
- voice immediately ended -> repair lifetime/end flag/sample boundary
- всё валидно, PCM пуст -> hook SPU mix block: active mask, frames, envelope

Не делать глобальное принудительное воспроизведение или увеличение лимитов: это может заполнить mixer шумом. Патч должен следовать подтверждённому неверному полю на успешном пути указанных sound codes.


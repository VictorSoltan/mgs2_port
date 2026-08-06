# MGS2 / RG353VS — brief #18: SFX теряются до DirectSound

Дата замера: **3 августа 2026 года**.

Этот документ закрывает ветки Creative ALchemy / DSOAL и выполняет
предложенный в brief #17 полный inventory-прогон DirectSound. Главный новый
результат: во время двух игровых действий MGS2 продолжает заполнять свой
готовый стереопоток `Str4SpuTrans`, но в записанном PCM не появляется никакого
звукового импульса. Следовательно, gameplay SFX пропадают **внутри игрового
sound/SPU-кода до передачи PCM в Wine DirectSound**.

DirectMusic, ALSA/PipeWire, byte order и поздние настройки period/rate в этом
замере не менялись.

## Состояние, подтверждённое пользователем

После полного удаления ALchemy/DSOAL, восстановления штатного launcher и
перезагрузки RG353VS игра была запущена со stock Wine DirectSound. Пользователь
сообщил:

```text
Сейчас звук был
```

Это подтверждает, что полный rollback вернул общий звук. В gameplay при этом
по-прежнему отсутствуют выстрелы/удары и другие игровые эффекты. Поэтому здесь
разделяются две вещи:

1. штатный output path Wine ALSA → PipeWire → устройство работает;
2. gameplay SFX не попадают в готовый игровой PCM.

## Стабильная база, которую нельзя снова менять без новых данных

```text
DirectSound: stock /usr/lib/wine/i386-windows/dsound.dll
DirectMusic audio path: dmime_graphqi.dll
DirectMusic synth: dmsynth_wine112.dll
Wine audio backend: winealsa
PipeWire overrides: не заданы
app-local dsound.dll / DSOAL / ALchemy: отсутствуют
```

Штатный launcher после всех тестов:

```text
/storage/roms/ports/MGS2-Substance/launch.sh
SHA-256 f36bd9f09cd2f690da2424ca77746cf2fbb06dc154ddf8f1a49e3786e253bff1
```

## Creative ALchemy из V's Fix: точный отрицательный результат

Использовался только audio payload из V's Fix v1.8.1, без установки всего
V's Fix поверх ARM/Box86-порта.

```text
V's Fix release archive
SHA-256 d896bdff9571fa20c5ea66a42c3e3363280f0a845394be3e6b9b6d4c5ecc3769

2_audio_fix.zip / dsound.dll
SHA-256 d8d9a42f29215496ba7d071ceb78287e5002617aaabe0678c10b7ad38ee8cd1b

2_audio_fix.zip / dsound.ini
SHA-256 d2b62270d2873689880a0f9756299a9d239f90a44b121a38f48a76caf499ec84
```

`dsound.dll` был реально выбран через проверенный bind mount/native path, а не
только скопирован рядом с EXE. `/proc/<pid>/maps` подтверждал отображение
app-local DLL. ALchemy записал:

```text
Failed to initialize Creative ALchemy, falling back to dsound.dll
Failed to load original dsound.dll
```

Добавление 32-битного `openal32.dll` из OpenAL Soft не изменило результат;
`openal32.dll` не отображался в процессе. Игра загрузилась, но звука не было
вообще. Логи сохранены в:

```text
logs/rg353vs/dsound-ab/vfix-alchemy/
```

Вывод: ALchemy wrapper в этой Wine/Box86-среде не инициализируется и не является
исправлением gameplay SFX.

## DSOAL: точный отрицательный результат

Проверена Win32-сборка DSOAL r694 + OpenAL Soft r10595.

```text
release ZIP
SHA-256 bdca287ee411c6968ce52b7dc49c8c8275bd9d35c2498ddfa62a2d0858bb4a80

dsound.dll
SHA-256 78c398d48f8acf47932eedaa7be939722ea8de38db2cad8c36ea0314e91973df

dsoal-aldrv.dll
SHA-256 ae110ad9f208da128bb75d22a5ada09e1f583e7b0f7277097805a2ebc306d5ca
```

### WASAPI backend

Обе DLL отображались в процессе. DSOAL/OpenAL успешно инициализировались и
открыли:

```text
OpenAL Soft on Out: default
```

DSOAL также увидел известный 32 576-байтный mono PCM16 / 44.1 kHz pool. Несмотря
на это, пользователь получил полностью немую игру — пропали и те звуки, которые
работали на stock DirectSound.

### Принудительный winmm backend

С `drivers = winmm` игра зависла около меню, после чего остался zombie/orphaned
Wine-сеанс. Этот вариант также отвергнут.

После удаления DSOAL/ALchemy, очистки Wine-служб и перезагрузки stock DirectSound
снова дал общий звук. Следовательно, эти замены не надо возвращать в следующих
тестах.

## Inventory recorder v3

Recorder был собран из чистого Wine 11 DirectSound с единственным
диагностическим изменением: inventory всех secondary buffers и ограниченная
трёхсекундная запись COM-вызовов после marker. Он не читал и не менял PCM, не
менял cursor, volume, формат или mixer semantics.

```text
recovered-session/device-artifacts/dsound_sfxinventory3.dll
SHA-256 b0150c73f0759d301964ae0948a62ef1507cc157a150bc61f707b848ff6e21d7
```

Автоматизация самостоятельно прошла меню до Tanker gameplay. Контрольный кадр:

```text
logs/rg353vs/sfxinventory3/auto-gameplay/mgs2-inventory3-gameplay.png
```

Затем marker был создан непосредственно перед движением и двумя действиями:

```text
right left z z
```

Полученный журнал:

```text
logs/rg353vs/sfxinventory3/auto-gameplay/events-001.log
SHA-256 b738ca4b72a6cde61d44ffa446401ebd233d05d93c51f6e91d99479ae70bbb80
```

Header:

```text
MGS2_SFX_INVENTORY v3 capture=1 start_tick=846896
events=1266 overflow=0 inventory=47 inventory_overflow=0
```

### Все созданные secondary buffers

| object IDs | количество | bytes | rate/channels/bits | flags |
| --- | ---: | ---: | --- | --- |
| 1 | 1 | 176400 | 22050 / stereo / 16 | `00018100` |
| 2 | 1 | 4 | 44000 / stereo / 16 | `000082e0` |
| 3–13 | 11 | 32576 | 44100 / mono / 16 | `000581e0` |
| 14–17 | 4 | 65152 | 44100 / stereo / 16 | `000581e0` |
| 18,20,…,42 | 13 | 176400 | 22050 / stereo / 16 | `00018100` |
| 19,21,…,43 | 13 | 4 | 44000 / mono / 16 | `000282b0` |
| 44–47 | 4 | 32576 | 44100 / mono / 16 | `00058190` |

### Что было активно в marker window

Из всех 47 объектов события получили только три:

```text
object 1   — 313 events
object 16  — 640 events
object 42  — 313 events
```

Все 1266 событий распределились так:

```text
Lock                 331
Unlock               331
GetCurrentPosition   317
GetStatus             287
```

За окно действий не было ни одного:

```text
Play, Stop, SetCurrentPosition, SetVolume, SetPan,
SetFrequency, AcquireResources
```

Это исключает все три оставшиеся после brief #17 гипотезы о другом
DirectSound-buffer API path. Gameplay action не запускает отдельный secondary
buffer и не меняет управление persistent voice через DirectSound API.

## Привязка активного 65 152-байтного потока к коду игры

Return addresses в журнале:

```text
0x008f4d81  GetStatus
0x008f4ea0  GetCurrentPosition
0x008f5c00  Lock
0x008f5c88  Unlock
```

Дизассемблирование `mgs2_sse_rg353vs_port.exe` показало, что это код игрового
потока `Str4SpuTrans`. Связанные строки в EXE:

```text
IID_IDirectSoundBuffer_Play err
ERROR:Str4SpuTrans/Play()
ERROR:Str4SpuTrans/GetStatus()
ERROR:Str4SpuTrans/GetCurrentPosition()
buffer lock failed...
```

Игра циклически заполняет 65 152-байтный stereo PCM16 / 44.1 kHz ring частями
по:

```text
0x3fa0 = 16288 bytes
0xfe80 = 65152 bytes total
```

Это не отдельный Wine voice для каждого выстрела. Это уже готовый внутренне
смешанный игровой стереопоток.

### Проверка старых правок EXE

Оригинальный `mgs2_sse.exe` и `mgs2_sse_rg353vs_port.exe` имеют одинаковые PE
sections и полностью идентичный код в исследованном диапазоне:

```text
VA 0x008f4000 .. 0x008f6000
```

Все 17 изменённых байтов port EXE сгруппированы в других местах:

```text
file 0x00014210 / VA 0x00414210
file 0x0017d82f / VA 0x0057d82f
file 0x00478fe0 / VA 0x00878fe0
file 0x0047926e / VA 0x0087926e
file 0x0047cd9b / VA 0x0087cd9b
file 0x004ebb2b / VA 0x008ebb2b
```

Следовательно, прежние binary patches не повредили `Str4SpuTrans` и их полный
rollback не является обоснованным SFX-фиксом.

## PCM recorder v4: контроль покоя против двух действий

Чтобы проверить уже готовые данные, v3 был расширен единственной функцией:
после marker `Unlock` пассивно сохраняет только bytes активного 65 152-байтного
stereo PCM16 / 44.1 kHz `Str4SpuTrans`. Данные не меняются.

```text
recovered-session/device-artifacts/dsound_str4pcm4.dll
SHA-256 8fdbded5aa68676351781d1febea461004a29bbc5d7efedba346d9374504ce95
```

Игра была автоматически доведена до gameplay. Пользователь отдельно сообщил,
что уже стрелял и игрового звука нет. После этого записаны два независимых
окна:

1. около трёх секунд без автоматического ввода;
2. marker непосредственно перед `z z`, `window focused: True`.

В этом запуске активный `Str4SpuTrans` получил object ID 14. ID отличается от
v3-прогона из-за порядка создания объектов, но descriptor и caller addresses
совпадают.

### Файлы и хеши

```text
logs/rg353vs/sfxinventory3/str4pcm4/events-001.log
SHA-256 98b7fab42a659ba0b8180f074504ea05a157c186e6ffbaafa370ab11fb9396d6

logs/rg353vs/sfxinventory3/str4pcm4/events-002.log
SHA-256 3b61438a8bf85faee47c04f3dc5a5f873195b222aaf04cf754287364f4a2a4bb

logs/rg353vs/sfxinventory3/str4pcm4/pcm-001-object-14.raw
SHA-256 0581381fbfc70b7100011ff322e9ae3072e6e763e2cf2e0803ccc6c9812486bf

logs/rg353vs/sfxinventory3/str4pcm4/pcm-002-object-14.raw
SHA-256 01bb2e821f3b5097ad10823a8ecd37d53a0642e55ec25e422c9367c1d1c4aead
```

Оба event logs имеют `overflow=0`, `inventory=47`,
`inventory_overflow=0`. И в покое, и при действиях активны только objects
1/14/42; набор методов снова ограничен `Lock`, `Unlock`, `GetStatus` и
`GetCurrentPosition`.

### Измерение готового PCM

| метрика | покой | два действия |
| --- | ---: | ---: |
| bytes | 521216 | 517324 |
| frames | 130304 | 129331 |
| duration | 2.954739 s | 2.932676 s |
| non-zero samples | 98.1804% | 96.5383% |
| peak L/R | 1293 / 1287 | 1317 / 1276 |
| peak dBFS L/R | −28.08 / −28.12 | −27.92 / −28.19 |
| RMS L/R | 260.140 / 257.463 | 262.253 / 250.495 |
| RMS dBFS L/R | −42.00 / −42.09 | −41.93 / −42.33 |
| L/R correlation | 0.003166 | −0.006935 |

В 100-ms окнах action capture RMS оставался между примерно −41.64 и
−42.86 dBFS. В момент двух действий не появилось характерного краткого пика,
подъёма RMS или иной смены режима. Покой и action capture содержат одинаково
низкоуровневый, почти стационарный поток.

## Итоговая локализация дефекта

Наблюдаемая цепочка теперь выглядит так:

```text
gameplay action
  -> внутренний MGS2 SE / sound-command / SPU mixer    <-- дефект находится здесь
  -> Str4SpuTrans, stereo PCM16 44.1 kHz
  -> IDirectSoundBuffer Lock/Unlock
  -> Wine DirectSound
  -> winealsa
  -> PipeWire / speaker
```

Wine получает рабочие `Lock/Unlock`, корректный формат, непрерывное движение
cursor и ненулевой PCM. Но готовый PCM не меняется при выстреле/ударе. Поэтому
не обоснованы новые изменения:

* `IDirectSoundBuffer::Play/Stop`;
* `SetCurrentPosition`, LOCDEFER или writelead;
* DirectSound volume/pan/frequency;
* byte swapping или PCM conversion;
* PipeWire rate/period/quantum;
* Creative ALchemy или DSOAL;
* `Str4SpuTrans` ring/cursor;
* полный rollback 17 EXE patches;
* новые DirectMusic изменения без независимого нового доказательства.

## Куда направить следующий research

Следующий фикс должен работать **выше** `Str4SpuTrans` в коде самой игры.
Нужен точечный поиск по следующим ориентирам из EXE:

```text
sd_cli.c
sd_3d.c
sd_int
sd_file
SECan'tPlay:LowPriority(code=%x:pri=%x:j=%x)
SE:TooManyTracks(%x):sound_code=%x
***TooMuchSoundCode(%x)***
***TooMuchBGMSoundCode(%x)***
Str4SpuTrans
```

Приоритетные вопросы для статического анализа или сравнения с рабочим Windows
запуском:

1. Доходит ли gameplay sound code до внутренней SE command queue?
2. Загружены ли SE banks/tables и не возвращает ли `sd_file` пустой/ошибочный
   ресурс?
3. Не отклоняются ли все effects как low-priority / too-many-tracks?
4. Какая функция непосредственно формирует 16 288-байтные блоки перед вызовом
   `Lock` по адресу `0x008f5c00`, и какие voice counters у неё равны нулю?
5. Отличается ли её входной voice/mix state между рабочим Windows и
   Wine/Box86, хотя выходной ring и DirectSound API одинаковы?

Наиболее полезная следующая диагностика — не ещё один Wine DLL, а минимальный
hook игрового EXE вокруг постановки SE command и функции, которая подготавливает
`0x3fa0` bytes для `Str4SpuTrans`. Он должен писать только sound code, результат
выделения voice/track и короткие counters, без PCM и без hot-loop logging.

## Состояние устройства после замера

Диагностический процесс мягко завершён. Осиротевший `rpcss.exe`, который
унаследовал lock descriptor, завершён обычным `TERM`. Проверено:

```text
MGS2 process: отсутствует
temporary dsound bind mount: отсутствует
/tmp/mgs2-substance.lock holder: отсутствует
app-local ALchemy/DSOAL files in game/bin: отсутствуют
launcher SHA-256: f36bd9f09cd2f690da2424ca77746cf2fbb06dc154ddf8f1a49e3786e253bff1
```

Следующий обычный запуск снова использует штатный DirectSound и стабильную
аудиобазу.

# MGS2 RG353VS — бриф #24: PCM из dmsynth-синка не доходит до выхода; постановка задачи из #23 была неверной

Дата: 5 августа 2026.

## Исходная рабочая аудиоконфигурация

Общий звук игры был восстановлен не через DirectMusic-патчи, а через рабочую связку:

```text
Wine 11
stock dsound.dll
winealsa.drv
PipeWire ALSA plugin
PipeWire hardware output
```

`winepulse.drv` на RG353VS не используется: под box86 он не загружается из-за отсутствующего символа `pthread_mutexattr_setrobust`. Поэтому launcher по умолчанию задаёт:

```sh
MGS2_AUDIO=alsa
```

и добавляет в `WINEDLLOVERRIDES`:

```text
winepulse.drv=d
```

Аудиоклиент Wine направляется в PipeWire через ALSA-конфигурацию:

```sh
PIPEWIRE_ALSA='{ alsa.rate=44100 node.name=mgs2-audio }'
PIPEWIRE_QUANTUM='1440/48000'
```

`PULSE_SERVER=tcp:127.0.0.1:4713` присутствует в launcher, но при штатном
`MGS2_AUDIO=alsa` не является активным путём вывода игры. Эти настройки находятся непосредственно в текущем `launch.sh`.

### Что слышно в этой конфигурации

```text
музыка меню       — слышна
музыка gameplay   — слышна
клики меню        — не слышны
шаги/выстрелы     — не слышны
```

То есть общий endpoint, Wine ALSA и PipeWire работают. Неработающая часть всегда была только классом SE/SFX.

### Production baseline

```text
dmime_graphqi.dll
dmsynth_wine112.dll
stock dsound.dll
winealsa.drv -> PipeWire ALSA
один экземпляр игры
без trace/probe
```

`dmime_graphqi.dll` нужен потому, что MGS2 запрашивает
`IID_IDirectMusicGraph` через `IDirectMusicAudioPath::QueryInterface`, а stock
Wine 11 возвращал `E_NOINTERFACE`.

`dmsynth_wine112.dll` содержит более новый вариант synth sink с меньшей
частотой wake-up и улучшенным отслеживанием позиции. Он снижает underrun/CPU,
но сам по себе не возвращает SFX.

### Как выбираются экспериментальные DLL

Launcher поддерживает переменные:

```sh
MGS2_DMIME_DLL
MGS2_DMSYNTH_DLL
MGS2_DSOUND_DLL
MGS2_DMUSIC_DLL
```

Выбранные файлы из:

```text
/storage/roms/ports/MGS2-Substance/
```

временно bind-mount’ятся поверх:

```text
/usr/lib/wine/i386-windows/dmime.dll
/usr/lib/wine/i386-windows/dmsynth.dll
/usr/lib/wine/i386-windows/dsound.dll
/usr/lib/wine/i386-windows/dmusic.dll
```

По завершении launcher размонтирует их.

Для запуска из меню переменные должны экспортироваться во внешнем:

```text
/storage/roms/ports/MGS2-Substance.sh
```

Например:

```sh
#!/bin/bash

GAMEDIR="$(dirname "$0")/MGS2-Substance"

export MGS2_DMIME_DLL="dmime_pchannel2.dll"
export MGS2_DMSYNTH_DLL="dmsynth_wine112.dll"

exec "$GAMEDIR/launch.sh" "$GAMEDIR"
```

Без этих export обычный запуск использует baseline DLL, даже если тестовые файлы лежат рядом.

### Как подтверждалась реальная загрузка DLL

Во время работы игры проверялось не только имя файла, а содержимое активного bind mount:

```sh
GAME=/storage/roms/ports/MGS2-Substance

cmp -s /usr/lib/wine/i386-windows/dmime.dll \
    "$GAME/$MGS2_DMIME_DLL"
echo "dmime=$?"

cmp -s /usr/lib/wine/i386-windows/dmsynth.dll \
    "$GAME/$MGS2_DMSYNTH_DLL"
echo "dmsynth=$?"
```

Ожидаемый результат:

```text
dmime=0
dmsynth=0
```

Также сравнивались inode, SHA-256 и `/proc/<pid>/maps`.

### Важное исправление истории

Ни один из следующих вариантов достоверно не восстановил menu clicks или
gameplay SFX:

```text
dmime_pchannel2.dll
dmime_sharedgroups1.dll
dmsynth_groupfix.dll
dmsynth_groupfix1.dll
```

Предыдущее сообщение «звук появился с pchannel2» было ошибочной
интерпретацией слышимой фоновой музыки. Музыка присутствует и на baseline.

## Главное: два предыдущих вывода отозваны

Брифы #22–#23 строились на утверждении «звук есть только через
`dmime_pchannel2.dll`, но эта маршрутизация перегружает игру». Сегодняшний
чистый запуск (один инстанс, без probe, без trace) этого не подтверждает.

`dmime_pchannel2.dll` + `dmsynth_wine112.dll`, слушал пользователь:

```text
фоновая музыка в меню      — есть
фоновая музыка в геймплее  — есть
клики меню (START, навигация) — НЕТ
игровые SFX (шаги, выстрелы)  — НЕТ
лаги                          — нет, обычный baseline
```

Отсюда два отзыва:

1. **`pchannel2` не восстанавливает SFX.** Раннее «звук есть» относилось к
   фоновой музыке, которая играет и на штатном `dmime_graphqi.dll`. Вся ветка
   «disjoint PChannel allocation восстановила SFX» отменяется.
2. **Лаги не создаются маршрутизацией.** Тяжёлые лаги наблюдались на
   диагностических сборках (`sinkprobe11`, `sinkaudible14`, `MGS2_DSOUND_PROBE`,
   `MGS2_TRACE`) и, вероятно, на дублирующихся инстансах — фоновый запуск
   переживает ssh-сессию, две копии игры читаются как жуткий лаг. На чистом
   одиночном запуске та же связка идёт как baseline.

Пользователь также подтвердил, что клики меню и геймплейные SFX — один класс
звука: «они связаны». То есть незакрытый дефект один, а не два.

## Новый измеренный факт: синк не слышен вообще

Сделан лёгкий диагностический режим `MGS2_SINKTONE=1`: непрерывный меандр 1 кГц,
амплитуда ±8192, вписывается в **каждый** рендер-блок **каждого** dmsynth-синка
в `synth_sink_render_data()`. Ни логов на кадр, ни marker-arm, ни зависимости от
того, дошла ли игра до конкретной ноты.

Запись монитора спикера (`pw-record`, sink id 34, 48 кГц s16, 16 с), детекция
Гёрцелем:

```text
samples=750240  peak=3898  rms=405
goertzel 1kHz = 0.7      <- вписанный тон
goertzel 300Hz = 1.7     <- своя музыка игры
goertzel 5kHz = 0.0
```

Музыка в записи есть (значит тракт записи рабочий), тона нет. Непрерывный тон
заполняет буфер целиком, поэтому рассинхрон play/write-курсора его скрыть не
может.

**Вывод: ничего из того, что dmsynth пишет в свой DirectSound-буфер, не попадает
в слышимый микс.** Это согласуется с ручным тон-тестом из #23 (тон не был
услышан), но теперь измерено, а не выведено из отсутствия слуховой реакции.

Контроль закрыт отдельным запуском (`dmsynth_sinktone2.dll`, `err+dmsynth`):

```text
20 x err:dmsynth:sinktone_add SINKTONE writing samples=08437090 frames=441 rate=22050 channels=2
222 x err:dmsynth:synth_sink_wait_write Underrun detected
других err в логе нет — буфер синка создаётся и стартует без ошибок
```

Тон писался; в записи выхода его нет (бин 1 кГц = 0.4 при музыке peak 7378).
«Тона нет» и «тон не писался» больше не путаются.

## Решающий факт: слышимость синка зависит от `dsound`, а не от маршрутизации

Тот же непрерывный тон, единственное отличие запуска — какой `dsound`
смонтирован:

| `dsound` | тон 1 кГц из синка |
|---|---|
| системный stock | не слышен; в записи бин 1 кГц = 0.4–0.7 |
| собранный из этого дерева (`dsound_mixcensus1.dll`) | **слышен** — пользователь описал как непрерывный писк с самого старта |

То есть отсутствующее звено находится в `dsound`, а не в PChannel/group/port
маршрутизации. Это независимо подтверждает отзыв ветки `pchannel2`/`groupfix`:
она правила не то место.

### Цензус микса (`MGS2_MIXCENSUS=1`, наш `dsound`)

Одна строка на устройство и на играющий буфер раз в секунду, без сканирования
сэмплов:

```text
MGS2 MIXCENSUS device=02B90708 buffers=34 playing=3 rate=44100 channels=2
```

Классификация играющих буферов за запуск:

```text
state=2 buflen=176400 rate=22050 freq=22050 channels=2 vol=0        <- синк dmsynth, таких 2
state=2 buflen=65152  rate=44100 freq=44100 channels=2 vol=-1406    <- своя музыка игры
```

Следствия:

1. DirectSound-устройство **одно** (`02B90708`), буферы игры и буферы синков
   лежат на нём же. Reuse-путь (`MGS2_DSOUND_SHARE`) не срабатывает ни разу,
   то есть `dmime` не создаёт второе устройство — игра отдаёт своё через
   `InitAudio`. Гипотезу «второе устройство без потока» можно закрыть.
2. Из ~14 синков в миксе играют только **два**. Остальные буферы синков в
   состоянии `state=0` и не микшируются вообще.

### Слышимый синк — условие необходимое, но не достаточное

Запуск: наш `dsound` + штатные `dmime_graphqi` + `dmsynth_wine112`, тон
выключен. Слушал пользователь:

```text
фоновая музыка   — есть
клики меню       — НЕТ
```

Значит одного слышимого синка мало. Следующие подозреваемые, в порядке
проверки:

1. SE рендерится в синк, чей DirectSound-буфер не играет (играют только два из
   четырнадцати).
2. Уровень SE-PCM: в #22 на реальном выстреле блок был `peak=138` при 32768
   полной шкалы, то есть около −47 dBFS, при музыке 3300–7400. В коде dmsynth
   зафиксировано «DLS-эффекты рендерятся примерно на 40 дБ ниже обычного микса»,
   под это есть `MGS2_DMSYNTH_BOOST_DB` с потолком 30 дБ — с новым `dsound`
   ещё не проверялось.

### Что теперь нужно от ресёрча дополнительно

6. Что именно в `dsound` этого дерева делает secondary buffer dmsynth-синка
   слышимым там, где системный stock `dsound` оставляет его беззвучным?
   Кандидаты в дереве: изменения семантики `Lock` (`MGS2_DSOUND_CX17_LOCK`),
   обёртка позиции курсора, обработка notification-позиций. Нужен точный
   ответ, какое изменение обязательно, чтобы отделить его от диагностического
   обвеса и вынести в production-патч.
7. Почему в миксе играют только два синка из четырнадцати, и обязан ли порт,
   получающий SE-ноты, иметь играющий буфер? Что в Wine активирует синк
   (`IDirectMusicSynthSink::Activate`) и может ли порт остаться неактивированным
   при живом `PlayBuffer`?

## Почему это меняет цель

Вся цепочка из #22 остаётся верной, но её последнее звено оказалось тупиком:

```text
MGS2 keyon (0x008FF681)
  -> MIDI 90 3c 7f -> DirectMusic PMsg submit        (доказано, #21)
  -> dmime PChannel routing -> dmsynth               (доказано, #22)
  -> FluidSynth voice, ненулевой Render PCM          (доказано, #22)
  -> IDirectSoundBuffer Lock/Unlock, тот же PCM      (доказано, #22)
  -> [этот буфер не слышен вообще]                   (измерено, #24)
```

Дальнейшая правка group-mapping, gain, PChannel-раскладки и числа портов не
может дать звук, пока буфер синка не слышен.

## Код, который надо оценить со стороны

`dlls/dmime/performance.c:661`:

```c
static HRESULT performance_init_dsound(struct performance *This, HWND hwnd)
{
    if (FAILED(hr = DirectSoundCreate(NULL, &dsound, NULL))) return hr;
    if (!hwnd) hwnd = GetForegroundWindow();
    hr = IDirectSound_SetCooperativeLevel(dsound, hwnd, DSSCL_PRIORITY);
```

`dmime` создаёт **собственное** DirectSound-устройство, и синки dmsynth создают
свои secondary buffers именно на нём (`dlls/dmsynth/synthsink.c:785`):

```c
desc.dwFlags = DSBCAPS_GLOBALFOCUS | DSBCAPS_GETCURRENTPOSITION2
             | DSBCAPS_CTRLPOSITIONNOTIFY;
IDirectSound8_CreateSoundBuffer(This->dsound, &desc, &render_params.buffer, NULL);
```

Слышимая музыка идёт через **свои** буферы игры (§12a: игра сама микширует и
стримит, 16 `Play` против 51900 `Unlock`).

Наблюдение с устройства: во время запуска в PipeWire виден ровно **один** узел
вывода (`mgs2-audio`, Stream/Output/Audio). Двух выходных потоков нет.

При этом в дереве уже есть диагностика переиспользования устройства
(`dlls/dsound/dsound.c:296`, `MGS2_DSOUND_SHARE`), и в записях проекта сказано,
что MGS2 «никогда не попадает в reuse-путь». Это противоречит тому, что `dmime`
делает свой `DirectSoundCreate(NULL)`: при том же endpoint GUID reuse должен был
срабатывать. Противоречие не разрешено и является ключевым.

## Вопросы к ресёрчу

1. В Wine 11.0: обязан ли secondary buffer, созданный dmsynth-синком на
   устройстве, которое `dmime` завёл своим `DirectSoundCreate(NULL)` +
   `DSSCL_PRIORITY`, попадать в тот же primary mix, что и буферы приложения?
   Есть ли известный путь, где микшер такого устройства работает, а его выход не
   доходит до endpoint (второй `IAudioClient`, не запущенный поток, монопольный
   захват endpoint, `GLOBALFOCUS` + фокус окна)?
2. Верно ли, что правильная архитектура DirectMusic — рендер порта **в буфер
   audio-path** (`DMUS_PATH_BUFFER`), а не в приватный буфер синка? В Wine
   `CreateStandardAudioPath` создаёт эти буферы размером `DSBSIZE_MIN` (4 байта)
   и с жёстко заданными 44000 Гц моно, а игра запрашивает и кэширует все 14.
   Это баг, который надо исправить, чтобы MGS2 услышала SFX
   (`SetDirectSound(port, dsound, path_buffer)`)?
3. Где на самом деле должен заканчиваться SE-звук MGS2 — в DirectMusic-синке или
   в собственном SPU→DirectSound потоке игры (`Str4SpuTrans`)? Учитывая, что
   MIDI submit и ненулевой PCM в dmsynth доказаны, но буфер синка не слышен:
   является ли DirectMusic вообще правильной целью, или SE обязан выходить
   через буферы игры?
4. Измеренный факт для оценки: **ни** disjoint-PChannel вариант (каждому path
   свой порт), **ни** общий порт на 4 channel group (все path на одном порту и
   одном синке) SFX не дают. Какая раскладка PChannel/group/port реально
   требуется, и может ли DLS download уходить в один синт, а note-on в другой?
5. Стоимость на этой платформе: FluidSynth-реверб обрабатывается на каждый блок
   независимо от числа голосов (`fluid_rvoice_mixer_process_fx`), и таких синков
   14, каждый под box86. Правильный ли это end-state — один порт с N группами,
   и допустимы ли reverb/chorus off, линейная интерполяция, ограничение
   полифонии как постоянная политика?

## Что уже собрано и лежит на консоли

| файл | что делает | ручки |
|---|---|---|
| `dmsynth_sinktone1.dll` | непрерывный тон 1 кГц во все синки | `MGS2_SINKTONE=1` |
| `dmsynth_sinktone2.dll` | то же + до 20 строк «SINKTONE writing» | `MGS2_SINKTONE=1` |
| `dmsynth_lowcpu1.dll` | reverb/chorus off, линейная интерполяция, полифония 24, кэш громкости каналов, group→channel mapping вкл. | `MGS2_DMSYNTH_FX`, `MGS2_DMSYNTH_INTERP`, `MGS2_DMSYNTH_POLYPHONY`, `MGS2_DMSYNTH_GROUPMAP` |
| `dmsynth_lowcpu2.dll` | то же, но group mapping по умолчанию выключен (семантика wine112) | те же |
| `dmime_shared2.dll` | один общий порт на все audio-path, число групп настраиваемое | `MGS2_DMIME_SHAREDGROUPS=1`, `MGS2_DMIME_SHAREDGROUP_COUNT` |

SHA-256:

```text
dmsynth_sinktone1.dll  26c89a14ab8d831cc5c987bdf4d1d402fdd0c5356e5251bc74bf6e37272f3431
dmsynth_sinktone2.dll  43a6b558d190b595a020981b053ba2c5a4d4701ea518574d6c600bade8ec30b8
dmsynth_lowcpu1.dll    af78f6fa3089bacaa6dfcfdee1246c3720e41d50208b732ba7bda4dd9d60d5de
dmsynth_lowcpu2.dll    6912e60545a3af5fae2cf01157c25f9e4632a76b8afcc2425ce94f0d1ea77cf1
dmime_shared2.dll      7097305345acf3932a2c46e23f1f67180c523ef5597e3878eafe89d2e882beaf
```

## Измерения, которые я делаю сам (ресёрч на них не нужен)

1. Контроль записи тона (`dmsynth_sinktone2.dll`, `err+dmsynth`) — закрывает
   единственную дыру в главном факте.
2. `MGS2 DSOUND reuse` из патченого `dsound`: сколько DirectSound-устройств
   реально создаётся и попадают ли буферы синков на то же устройство, что
   слышимая музыка.
3. Производительность: fps из презентера (`MGS2_GL_STATS`) + CPU по потокам из
   `/proc/<pid>/task/*/stat`, без внутрипроцессной инструментации.

## Ограничения (в силе)

- никакого per-render логирования и `MGS2_TRACE=1` — это уже делало консоль
  неиграбельной и само по себе меняет тайминги;
- не трогать Creative ALchemy / DSOAL, `winepulse`, quantum/rate PipeWire,
  замены `dsound`, byte-swap/cursor-хаки, общий апгрейд Wine;
- один инстанс на запуск, проверка по точному `comm`, успех считать только по
  отрендеренному кадру;
- production baseline остаётся `dmime_graphqi.dll` + `dmsynth_wine112.dll` +
  stock `dsound.dll`, пока новый факт не даст основания его менять.

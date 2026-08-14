# MGS2 RG353VS — бриф #43: native memmove и cached DISCARD shadow

Дата: 11 августа 2026. Продолжение #42. Цель этой итерации — вернуть
30 fps на подтверждённом тяжёлом споте Game Data 02 без draw-skip, снижения
разрешения, упрощения шейдеров или изменения игровых данных.

## 1. Результат

Цель на фиксированном споте достигнута. После перехода на `FINALPLAY2` три
последовательных чистых окна дали:

```text
frames  elapsed     fps    readback    worst frame   >50 ms
300     10006 ms    30.0   5.03 ms/f   54 ms         2
300      9997 ms    30.0   3.28 ms/f   55 ms         1
300      9969 ms    30.1   4.85 ms/f   47 ms         0
```

Совокупно это 900 кадров за 29.972 s, или 30.03 fps. Игра упёрлась в свой
30-fps gameplay limit. Во всём окне частота оставалась 1992000 Hz,
температура после окна была 81666 m°C, процесс остался жив. Raw log:

```text
logs/rg353vs/shadow-discard/fixed-spot.txt
sha256 54b1659c50ab9fea02d066450280bcfd5a5db9f8600bb7458dc4282416acabe4
```

До этой итерации тот же пользовательский спот на FINALPLAY + первом native
memmove держался примерно в диапазоне 23.6–24.9 fps, около 24.2 fps. Это
полезная граница масштаба улучшения, но не строгий paired A/B: предыдущий
процесс закончился до текущего запуска. Исторические 20.8832 fps patch24 были
измерены при 1800 МГц и напрямую с новым окном не сравниваются.

Граница утверждения остаётся прежней: 30 fps подтверждены на прежнем
20-fps споте. Из-за scene-dominated нагрузки это не является доказательством
30 fps в каждой сцене всей игры.

После qualification тест продолжал работать. Архивный диагностический launcher
затем начал менять CPU cap между 1608000 и 1800000 Hz своим старым thermal
ladder. В этих уже не fixed-clock окнах игра в основном оставалась у лимита,
но отдельные окна дали 29.4–29.5 fps. Это не опровергает fixed-clock результат,
но задаёт точную границу слову «гарантия»: патч устранил прежний bottleneck на
этом споте, а ровно 30 fps при искусственно сниженном CPU или во всех сценах не
доказаны. Production launcher не содержит ladder: он держит 1992000 Hz и имеет
только аварийное завершение при 88000 m°C.

## 2. Почему работа перешла из renderer в Box86 / D3D8

FINALPLAY уже содержит producer batching, synthetic-EBO batching, dirty-range
uploads, visibility culling, restart hoist и 4-way set cache. На типичном
тяжёлом кадре примерно 1299 исходных draw превращаются примерно в 151 GL call.
Relative-range, expanded VBO, degenerate bridges, arena/WORLD lift, instancing,
async PBO и draw-skip уже закрыты измерениями в #38–#42. Возвращать их означало
бы повторять отрицательные ветки либо менять изображение.

Memory-only guest-map профиль дал 3578 process samples, из них 2506 внутри
Box86 JIT blocks. Распределение JIT samples:

```text
ucrtbase     781
game EXE     645
wined3d      419
dsound       262
d3d8         127
```

Один Wine `ucrtbase` block, `_sse2_memmove` RVA `0x168f4`, получил 744
samples. После exact native bridge этот guest block исчез; в следующем профиле
верхним стал host libc `memcpy` с 13.52% samples. Следовательно, bridge работал,
но реальное копирование всё ещё оставалось частью кадра.

Guest-map recorder записывает только создание dynarec blocks в bounded mmap.
Он не пишет из горячего потока. Reader:

```text
harness/box86_guest_profile.py
```

## 3. Точный census копирований

В Box86 добавлен второй opt-in mmap census, ключ `(guest caller, size)`. Запись
ограничена 16384 entries, не использует stderr/file I/O и в production вообще
выбирается другой lean wrapper. Reader снимает baseline при входе на спот и
конечный snapshot снаружи процесса:

```text
harness/box86_memmove_stats.py
logs/rg353vs/box86-memmove/mgs2-memmove-baseline.json
logs/rg353vs/box86-memmove/mgs2-memmove-after20.json
```

За 20 s неподвижной сцены:

```text
entries             50
memmove calls        3,384,052
bytes                865,233,779
overflow             0

D3D8 caller b3d5     985 calls × 524288 bytes = 516,423,680 bytes
four D3D8 size-0     2,811,234 calls
all size-0           2,818,170 calls
```

985 полумегабайтных копий — 49.25/s. При прежних примерно 24–25 fps это
соответствует примерно двум копиям на кадр; это интерпретация сочетания census
и frame rate, а не отдельный frame counter внутри recorder.

Адрес `d3d8 + 0xb3d5` оказался возвратом из `memcpy` в
`d3d8_vertexbuffer_Unlock()`. Причина: первый `D3DLOCK_DISCARD` писал в mapped
WineD3D upload BO, после чего visibility culler требовал прочитать весь mapping
обратно в cached producer shadow. На Mali чтение mapped upload memory является
дорогим направлением; оно было добавлено не игрой, а нашим culling-shadow path.

Миллионы нулевых вызовов пришли из вставки/удаления последнего элемента в двух
маленьких sorted range arrays. Их удаление семантически точное, но отдельный
microbenchmark показал, что это только малый дополнительный выигрыш. 20 млн
нулевых bridge calls занимали 0.92–0.98 s user CPU в старом production Box86 и
0.61–0.68 s после direct-zero return; этого недостаточно как главного рычага.

## 4. Патч

### 4.1 Box86

Box86 основан на точном upstream commit:

```text
0579f8b9c47d87d700724f4cce559b06cbd2b0f5
```

Wine 11 `_sse2_memmove` распознаётся по exact 20-byte prologue, независимо от
PE load address, и переводится в overlap-safe host `memmove`. Для `size == 0`
wrapper сразу возвращает `dst`. Диагностический wrapper с mmap census выбирается
только при `MGS2_BOX86_MEMMOVE_STATS=1`; production wrapper не содержит census
call/branch. Exact-overlap synthetic test проходит.

```text
box86-patches/01-egl-facade.patch
box86-patches/02-mgs2-native-memmove-profile.patch
binaries/box86-native-memmove2
sha256 69c9132e5a831011cadf9f950989410d676d992806cc967d95c831eef5dc108b
```

Оба patch применяются с `-F0`. Свежая patch-chain source побайтно совпадает с
build source, кроме generated `git_head.h`.

### 4.2 D3D8

Если у vertex buffer есть producer shadow, теперь и `DISCARD`, и последующие
`NOOVERWRITE` locks возвращают указатель в этот cached shadow. На Unlock exact
written range помечается dirty. Перед первым draw уже существующий flush
копирует те же байты в queue-owned update и только после этого buffer
используется GPU.

Таким образом удалено направление:

```text
game -> mapped upload BO -> read whole BO back -> culling shadow
```

и оставлено:

```text
game -> cached culling shadow -> existing queue-owned dirty upload -> GPU
```

Пиксели, vertex bytes, transforms, culling rules, draw list и shader policy не
меняются. При невозможности выделить shadow остаётся старый WineD3D path, а
culler консервативно считает неизвестную геометрию видимой.

Четыре `memmove(..., 0)` в bookkeeping arrays дополнительно ограждены точными
условиями `source_count > 0`; порядок непустых диапазонов не изменён.

```text
wine-patches/26-cached-discard-shadow.patch
binaries/d3d8_finalplay2.dll
sha256 d7ecffd624e5f236982ee5994058c749e413eca0de74095ca3ef5d232100f350
```

Patch 26 применяется после patch 25 с `patch -p1 -F0 --batch`; результат
`buffer.c` побайтно совпадает с использованным build source.

## 5. Отсеянные варианты этой итерации

```text
Box86 Release/O3 + A55, no LTO   0.11–0.12 s на 1M × 128 B
текущий O2                       0.07–0.08 s

Box86 O2 + mtune=cortex-a55      без выигрыша относительно generic O2
Box86 O3 + LTO                   без microbench-выигрыша; build дал UB-risk warnings
custom exact 128-byte NEON       примерно 91.2 -> 90.9 ms; практически ноль
```

Поэтому production сохраняет generic `O2`, без LTO. `FORWARD=1024` и более
агрессивные correctness knobs не понадобились и в production не включены.

## 6. Deployment и rollback

Оба menu wrapper, `launch-play.sh` и новые artifacts развернуты. Production
launcher выбирает:

```text
box86-native-memmove2
d3d8_finalplay2.dll
wined3d_finalplay.dll
BOX86_DYNAREC_SAFEFLAGS=0
BOX86_DYNAREC_BIGBLOCK=2
BOX86_DYNAREC_FORWARD=512
BOX86_DYNAREC_CALLRET=1
MGS2_BOX86_NATIVE_MEMMOVE=1
CPU 1992000 Hz
```

На реально запущенном процессе mounted Box86 и D3D8 побайтно совпали с SHA
выше. Игра оставлена запущенной на подтверждённом 30-fps candidate; обычный
следующий запуск из меню уже использует те же production artifacts без frame
stats.

Rollback не требует пересборки: вернуть в `device/launch-play.sh`
`box86-native-memmove1` и `d3d8_finalplay.dll`. Старые binaries сохранены.

## 10. Последующее reliability-обновление FINALPLAY3

11 августа полный freeze был пойман как отдельная от renderer проблема:
неатомарная first-use публикация Box86 могла назначить одному x86 mutex два
разных native backing mutex. Исправление добавлено поверх ровно этого
production Box86 и не меняет native memmove bridge или D3D8:

```text
box86-patches/03-aligned-mutex-publication.patch
binaries/box86-native-memmove3
sha256 35da697774f627cd0d4272328aa21ae094620d683458b1d0b35fd8e8b0a6e98c
```

Старый binary падает на прямом конкурентном first-use тесте; новый прошёл
10/10 запусков по 1,000 новых mutex mappings. Это reliability A/B, не новый
FPS A/B. Измерение 30.0/30.0/30.1 выше остаётся квалификацией неизменённых
memmove и renderer путей FINALPLAY2. Полный захват, micro-cost и граница
утверждения находятся в
`MGS2_RUNTIME_MUTEX_FREEZE_2026-08-11.md`.

Актуальный rollback только этого исправления — `box86-native-memmove2`; прежняя
строка про `memmove1` описывает совместный rollback всей оптимизации #43.

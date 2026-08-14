# MGS2 RG353VS — бриф #42: FINALPLAY

Дата: 11 августа 2026. Продолжение #41. Исследовательская фаза renderer
закрыта. FINALPLAY не является patch25-экспериментом: он удаляет лабораторную
обвязку и фиксирует уже измеренное production-поведение.

## 1. Зафиксированная база

FINALPLAY сохраняет доказанный стек без изменения изображения:

```text
wined3d: synthetic-EBO batching + restart hoist + 4-way set cache
d3d8:    producer batching + dirty-range uploads + visibility culling
system:  ntdll_fastyield.so + user32_peek1.dll + win32u_glfuncs3.so
present: PBO off, two SHM buffers
audio:   ALSA through PipeWire, 44100 Hz, 30 ms quantum
CPU:     fixed 1992000 Hz target
```

Частота 1992 МГц выбрана пользователем после улучшения охлаждения. Это новый
PLAY target, а не исправление исторических A/B patch24: те измерения корректно
остаются помечены как 1800 МГц.

Закрытые ветки не возвращались: relative-range, triangles, degenerate bridge,
EBO arena, packed source-VBO, frame VBO ring, instancing, async PBO и draw-skip.

## 2. `d3d8_finalplay.dll`

Финальная D3D8 собирается из production-состояния до исследовательских patches
18–24, после чего в неё минимально перенесены exact VB shadow coverage и
проверенный AABB visibility culler. Projected, mixed, stream-detail,
repeated-geometry и visibility census, live polling, stats, histogram, profile
и их counters физически отсутствуют в production source.

Culling всегда включён. Неизвестный случай всегда считается видимым: custom
vertex shader, vertex blending, неизвестная declaration, неполный shadow,
range overflow или non-finite coordinate возвращают старый draw path.

Вместо восьми последовательностей WORLD → VIEW → PROJECTION теперь при первом
draw после изменения matrices строится одна WORLD×VIEW×PROJECTION matrix. Каждый
угол object-space AABB проходит один transform. `SetTransform`,
`MultiplyTransform`, `ApplyStateBlock` и `Reset` инвалидируют cache. На clip
plane используется scale-relative epsilon `1e-5`; пограничный объект остаётся
видимым.

```text
d3d8_finalplay.dll
sha256 4246693700fcf8664001bbe94f313ec9b9e1d67b097e8b813ce5a730741cc3f3
```

## 3. `wined3d_finalplay.dll`

Финальная WineD3D основана на batch16/set-cache. Compile-time policy:

```text
batching             ON
primitive restart    hoisted
4-way hash/set cache ON
triangles            OFF
degenerate bridges   OFF
skip draw            OFF
EBO arena            OFF
```

Из production source удалены `GetTickCount()` и чтение `/tmp` switches,
batch/cache reports, draw/cache/flush counters, CSMT profile,
resource/draw census, renderer rungs и старые file trace hooks. Также из FINAL
binary полностью исключены
shader compile/link timers, GLSL disk cache, link-twice, VB/texture/alpha/codec
probes и startup capability dumps. Проверенные GLES conversions и FBO readback
зафиксированы compile-time; core resource-lifetime walk и production GLES
depth/FBO fixes сохранены.

```text
wined3d_finalplay.dll
sha256 062252ffb24670485918384e62ce6257fa5828da53dabc14a53e6cc295e9d0cd
```

Binary string audit не находит названия census, live-toggle paths,
`MGS2BATCH`, `MGS2CACHE`, profile/stats env или лабораторные log paths.

## 4. Сборка и воспроизводимость

Patch 25 — только FINAL cleanup. Он применяется после patches 01–24 с нулевым
fuzz и переводит четырнадцать затронутых source files в чистое
FINALPLAY-состояние:

```text
wine-patches/25-finalplay-clean.patch
patch -p1 -F0 --batch    PASS
target files             byte-for-byte match build source
```

Обе PE DLL полностью пересобраны без старых renderer objects:

```text
-O2
-DWINE_NO_TRACE_MSGS
-DWINE_NO_DEBUG_MSGS
```

`MGS2_RELEASE` и `MGS2_FINALPLAY` больше не требуются: production policy
зафиксирована самим source. `-O3`, LTO и CPU-specific flags не использовались.
Linker timestamp выключен, debug sections удалены через MinGW
`SOURCE_DATE_EPOCH=0 strip --strip-unneeded`. Независимая повторная сборка из
заново применённой цепочки 01–25 дала byte-identical DLL и те же SHA256.

## 5. PLAY launcher

Обычный menu entry теперь вызывает `launch-play.sh`. Он жёстко монтирует две
FINAL DLL и проверенные system/audio modules, выставляет 1992000 Hz, PBO=0,
SHM=2, 44100/30 ms и `WINEDEBUG=-all`. Renderer census/profile/stats/live
variables в PLAY отсутствуют. Старый `launch.sh` остаётся только архивным
исследовательским harness и нормальным запуском не вызывается.

Даже с улучшенным охлаждением сохранён независимый emergency stop при 88 °C;
частотной лестницы в PLAY нет.

## 6. Граница результата

Последний сопоставимый patch24 A/B на тяжёлом споте дал `-1.5488 ms/frame` и
примерно `-29.77 batches/frame`, но после culling там всё ещё было
`47.8854 ms/frame` (`20.8832 fps`) при 1800 МГц. FINAL cleanup не объявляется
новым измеренным ускорением и не обещает 30 fps в этом месте. Для 30 fps там
нужно снять ещё около 14.55 ms, чего текущие данные без потери картинки не
подтверждают.

После холодного device smoke ниже фиксируется только запуск, реальные mounted
SHA, частота и отсутствие нового crash/OOM; новый performance A/B намеренно не
проводится.

## 7. Исходный Device smoke до production-refactor

Окончательные repository artifacts и PLAY launcher развернуты на RG353VS.
Оба wrapper и `launch-play.sh` совпадают по SHA256 с локальными копиями и
проходят `sh -n`. После остановки предыдущего smoke-процесса выполнен холодный
запуск обычным `/storage/roms/ports/MGS2-Substance.sh`.

Запущенный процесс остался жив после инициализации. Реально bind-mounted DLL
совпали с deployed artifacts побайтно:

```text
/usr/lib/wine/i386-windows/d3d8.dll
377664a3fa464a8f2dc4861a4df08d537c2a0bb18d38b332d37c36a703df0b86

/usr/lib/wine/i386-windows/wined3d.dll
58c7f3c1ac0d75d99281a47138b6f8f0302386c432e136e73eabde57accc32d6
```

Governor был `performance`; `scaling_max_freq` и `scaling_cur_freq` равнялись
`1992000`. Температура после cold init была `68125 m°C`. В process environment
подтверждены `PBO=0`, `SHM buffers=2`, `WINEDEBUG=-all`; renderer census,
profile, stats, live-toggle и A/B variables отсутствуют. В launch log нет
`MGS2CAPS`, multi-draw/buffer-storage, GLSL cache, batch/cache/profile/census
или stat output. Оставшийся одноразовый `BOX86DBG: my_eglGetProcAddress` dump
принадлежит существующему `box86-clean1`, а не FINAL renderer DLL, и
заканчивается на startup entry-point enumeration.

В kernel tail нет нового OOM, killed process или GPU fault. Игра оставлена
запущенной на FINALPLAY. Это smoke стабильности и конфигурации, не новый
performance A/B и не измерение самого тяжёлого спота при 1992 МГц.

## 8. Последняя проверка: persistent arena + WORLD lift

После сборки FINALPLAY отдельно реализован последний предложенный вариант без
потери изображения. Unix-side `opengl32` дал узкие aliases для
`glBufferStorageEXT` и sync API. WineD3D создал один 8 MiB immutable
`GL_ARRAY_BUFFER`, один раз persistently/coherently mapped его и управлял
stride-aligned slices с жёстким memory ceiling. Освобождение generation шло
только после `glFenceSync`; `glClientWaitSync(..., 0, 0)` никогда не ждал.
Заполнение arena выполнялось прямым `memcpy` из уже существующего exact VB
shadow. Mutable update большого BO, который ранее вызвал Mali OOM, не
использовался.

Для fixed-function strips был реализован WORLD lift до 16 сегментов: global
indices в synthetic EBO, выбор сохранённой WORLD×VIEW matrix по `gl_VertexID`,
немедленный fallback для custom VS, vertex blending и несовместимого state.
Отдельно проверены два режима при 1992 МГц на подтверждённом тяжёлом споте:

```text
visibility culling + arena
stable windows      19.12–19.87 fps
lift_batches        0 во всех окнах
cross_boundaries    0
alloc_fail          0

arena, culling compile-time OFF
stable windows      19.14–19.50 fps
lift_batches        0 во всех окнах
cross_boundaries    0
alloc_fail          0
```

Arena технически работала: native mapping был ненулевым, allocations были
bounded, частота оставалась 1992000 Hz, температура в финальных окнах была
примерно 74–76 °C, нового OOM/GPU fault не было. Но draw-path не сформировал ни
одного lifted submission.

Причина измерена, а не предположена. После visibility culling чистых текущих
`WORLD + STREAM(buffer-only)` границ осталось лишь 4.0–5.8/frame. Каждая из них
пришла после producer batch, уже содержащего хотя бы один draw, непригодный для
lift; `reject_not_candidate` точно равнялся числу таких границ. Большая часть
остальных границ между реально отправляемыми draw дополнительно несла
transform/render-state/texture/shader state. При выключенном culling число
чистых границ существенно не выросло: старый census считал соседние source
draw, а не совместимость целых уже сформированных producer batches.

Чтобы консервативный setter-dirty mask не мог дать ложный отрицательный вывод,
последним отдельным запуском добавлена non-mutating exact projection. Для
каждого целиком lift-eligible pending batch она сохраняла effective fixed-
function state: declaration/shaders, RS, textures, sampler/TSS, VIEW/PROJECTION
и texture transforms, clip planes, material и viewport/scissor. Light setter
сохранялся консервативным serial barrier; он не мог разрешить ложный merge.
На следующей реально видимой WORLD+VB границе выполнялось побайтное сравнение и
проверялись topology, stride/offset, другой arena slice и лимит 16 сегментов.
Rendering и flush policy эта проекция не меняла.

Результат `projected_cross=0` во всех последовательных 300-frame окнах, включая
два подтверждённых тяжёлых окна `19.964` и `19.782 fps`. Следовательно, нулевой
lift не является ошибкой грубого dirty gate: после culling нет ни одной пары
целых producer batches, которую реализованный WORLD lift может безопасно
заменить одним submission.

Следовательно, прежние `53–70 WORLD+VB boundaries/frame` нельзя умножать на
стоимость одного удалённого batch. Это был верхний census отдельных source
границ, не достижимое число arena merges после producer batching и culling.
Даже идеальное поглощение оставшихся 4–6 границ не проходит старый порог
`30–40/f`; фактическое поглощение равно нулю.

Ветка закрыта. Persistent arena, WORLD-lift shader и `opengl32` aliases не
включены в production и не добавлены в FINALPLAY. После теста снова запущен
`launch-play.sh`; mounted `d3d8.dll` и `wined3d.dll` побайтно совпали с
production SHA выше, `scaling_max_freq=1992000`.

Логи:

```text
logs/rg353vs/finalarena/cull-plus-arena-final.log
logs/rg353vs/finalarena/arena-without-culling-final.log
logs/rg353vs/finalarena/exact-effective-projection-final.log
```

Пользователь отдельно отметил, что участки около 20 fps встречаются часто и
такой уровень неприемлем. Технический вывод от этого не меняется: заметного
оставшегося renderer-ускорения без изменения изображения измерения больше не
показывают. Следующий существенный шаг требует отдельного решения о видимом
компромиссе — снижении render resolution либо более агрессивном отбрасывании
геометрии/effects. Это уже не продолжение FINALPLAY cleanup.

## 9. Production-refactor после закрытия arena

После отрицательного результата arena выполнена отдельная чистка без изменения
renderer policy. Предыдущий patch 25 исключал лабораторные ветки условной
компиляцией, но физически оставлял их рядом с production-кодом. Новый patch 25
выбирает уже подтверждённую сторону `MGS2_FINALPLAY` и `MGS2_RELEASE`, удаляет
неактивные ветки, затем упрощает оставшиеся константные условия и no-op hooks.
Историческая реализация полностью сохраняется состоянием после patch 24.

Затронуты 14 source files в `d3d8`, `wined3d` и узком `opengl32` bridge.
Относительно первой FINALPLAY-ревизии удалено 6112 строк source. Наиболее
крупные сокращения:

```text
d3d8/device.c          5259 -> 4306
wined3d/context_gl.c   8747 -> 5628
wined3d/cs.c           5404 -> 4866
wined3d/glsl_shader.c 13765 -> 13205
```

Обе DLL собираются без `MGS2_FINALPLAY` и `MGS2_RELEASE`. Строгая цепочка
01–25 применена повторно к чистому Wine 11.0; все 14 target files совпали с
build source побайтно. Независимая повторная сборка и детерминированный strip
дали те же SHA. Export tables старых и новых DLL совпадают; binary string audit
не находит research env, census/stats/live paths или `finalarena` markers.

После удаления debug sections размер уменьшился:

```text
d3d8_finalplay.dll      220723 -> 116169 bytes  (-47.4%)
wined3d_finalplay.dll  3509259 -> 2859860 bytes (-18.5%)
```

Новые DLL сначала загружены на устройство под отдельными staging-именами и
проверены по SHA. Работавший на исходной FINALPLAY-ревизии launcher получил
`TERM` и за одну секунду штатно выполнил trap cleanup: процесс завершился, все
bind mounts были сняты. После атомарной подмены выполнен холодный запуск обычным
menu wrapper.

Полный startup пройден. Новый process оставался активным после двух с половиной
минут CPU time; реально mounted и game-directory DLL совпали с repository:

```text
/usr/lib/wine/i386-windows/d3d8.dll
4246693700fcf8664001bbe94f313ec9b9e1d67b097e8b813ce5a730741cc3f3

/usr/lib/wine/i386-windows/wined3d.dll
062252ffb24670485918384e62ce6257fa5828da53dabc14a53e6cc295e9d0cd
```

Governor и current/max CPU равнялись `performance` и `1992000`; температура
после startup была `56666 m°C`. В environment подтверждены `MGS2_GL_PBO=0`,
`MGS2_GL_SHM_BUFFERS=2`, `WINEDEBUG=-all`; renderer research variables
отсутствуют. В новом launch log нет GL error, OOM, census/stats или arena
markers; в kernel tail после запуска нет нового OOM, killed process или GPU
fault. Это smoke рефакторинга, не performance A/B.

После успешного smoke с устройства удалены семь временных arena DLL/SO, пять
их remote-логов, старые arena/initial-FINALPLAY launch logs и две rollback-копии
FINALPLAY.
Текущие production-файлы и процесс не затронуты. Удалённые device-копии больше
не восстанавливаются с устройства; доказательные финальные логи arena сохранены
локально в `logs/rg353vs/finalarena/`, а новый smoke — в
`logs/rg353vs/finalplay/refactor-smoke.log`.

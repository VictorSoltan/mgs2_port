# MGS2 RG353VS — first-use transition hitch capture

Дата: 12 августа 2026. Статус: причина измерена; candidate собран, но ещё не
прошёл qualification на устройстве и **не является production**.

## 1. Наблюдение

FINALPLAY3 держит 30 fps на прежнем тяжёлом споте, но первый gameplay после
загрузки и новые radio/codec calls дают длинные остановки. Это отдельная
проблема first-use latency, а не средний renderer throughput.

Memory-only ring поставлен вокруг texture allocation/upload, shader compile,
program link и длинных WineD3D CS operations. Ring ограничен 512 записями;
горячий поток ничего не пишет в файл или stderr. Reader работает снаружи через
`/proc/<pid>/mem`:

```text
harness/gpu_transition_probe.py
logs/live-20260812/transition-hitches/
```

## 2. Результат на устройстве

### Первый gameplay после Game Data 02

```text
operation           count    total       maximum
glLinkProgram          25    5216.003 ms 329.566 ms
glCompileShader        30     167.554 ms  18.345 ms
texture upload         26      39.238 ms   3.828 ms
texture allocation     31      11.663 ms   4.033 ms
```

### Настоящий radio call, начатый пользователем

```text
operation           count    total       maximum
glLinkProgram           8    1633.386 ms 232.895 ms
glCompileShader         1       7.775 ms   7.775 ms
texture upload         17      11.999 ms   4.093 ms
texture allocation     15       2.999 ms   0.532 ms
```

Radio создал один новый vertex shader `56`, после чего Wine синхронно собрал
восемь монолитных программ с уже существующими pixel shaders:

```text
VS 56 + PS 10    206.592 ms
VS 56 + PS 4     193.591 ms
VS 56 + PS 16    195.741 ms
VS 56 + PS 12    196.421 ms
VS 56 + PS 6     200.562 ms
VS 56 + PS 42    198.132 ms
VS 56 + PS 2     209.452 ms
```

Восьмая программа (`VS 54 + PS 31`) заняла 232.895 ms. Texture work всего
около 15 ms и не объясняет наблюдавшуюся остановку. Предыдущий warm-I/O опыт
тоже оставлял 145-ms transition frame, поэтому дальнейший архивный prefetch не
является основным исправлением.

## 3. Почему старый GLSL binary cache не является ответом

Brief #29 уже закрыл persistent program binaries: Mali принимает полученный
binary внутри создавшего его процесса, но отвергает 4/4 бинарника в следующем
запуске. Повторная линковка тех же shader objects также стоила около 195 ms.
Новый результат не отменяет эти измерения.

## 4. Candidate: separable stage programs

OpenGL ES 3.2 позволяет пометить программу `GL_PROGRAM_SEPARABLE`, один раз
связать vertex и fragment stages отдельно, затем составлять пары через program
pipeline. Khronos определяет именно такое переиспользование стадий, а материал
Arm отдельно приводит случай «один vertex shader + несколько fragment
shaders» как устраняемую избыточность:

- https://registry.khronos.org/OpenGL/specs/es/3.2/GLSL_ES_Specification_3.20.html
- https://developer.arm.com/-/media/Files/pdf/graphics-and-multimedia/Sponsored%20Session%20-%20OPEN%20GL%20ES%203-x.pdf

Экспериментальный WineD3D path:

1. включается только `MGS2_GL_SEPARABLE=1`;
2. применяется только к сгенерированному WineD3D FFP `VS + PS` без других
   stages — программируемые D3D shaders остаются на старом пути;
3. сохраняет исходные GLSL objects и все uniforms;
4. кэширует stage program по `(GL shader type, shader object id)`;
5. кэширует pipeline по прежнему ключу пары;
6. валидирует pipeline и при любой ошибке отключает candidate и возвращается к
   прежней монолитной линковке;
7. выбирает правильный stage program перед загрузкой VS/PS uniforms.

Предсказание для зафиксированного radio call: вместо восьми полных links нужен
один новый VS-stage link; восемь старых PS-stage programs переиспользуются.
Это предсказание считается опровергнутым, если Mali переносит прежние
~200 ms в `glValidateProgramPipeline`/первый draw, если stage interfaces не
проходят validation, либо если screenshot отличается.

## 5. Обязательный qualification

До production нужны все пункты:

```text
1. byte-verify diagnostic DLL mounted на единственном процессе
2. clean Game Data 02 load: screenshot + memory ring
3. тот же настоящий radio call: stage-link/pipeline/CS durations
4. повторный radio call после reset ring
5. фиксированный тяжёлый spot, CPU 1992 MHz: три FPS окна
6. clean production rebuild без memory probe
7. deploy обоих menu wrappers и byte-verify mount target
```

На момент записи device qualification не выполнен: orchestration environment
отклонила новый SSH/deploy action из-за исчерпанного approval quota. Текущий
запущенный диагностический процесс не был остановлен или изменён.

## 6. Отдельная неудачная попытка восстановления (12 августа)

Позже candidate был восстановлен из `../recovered-session/wine-11.0`, но это
оказалось не тем полным FINALPLAY-деревом, из которого был собран предыдущий
diagnostic DLL. На консоли он стартовал, однако контрольный вывод отличался
артефактами изображения, поэтому тест radio не продолжался. Candidate был
остановлен и удалён; production DLL проверена byte-wise (`cmp=0`) и снова
запущена. Этот build не является доказательством ни выигрыша, ни regressions
separable path и не должен использоваться для production.

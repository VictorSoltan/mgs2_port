# MGS2 FINALPLAY16: DXVK-Sarek production — 2026-08-24

## Решение

FINALPLAY16 развёрнут на RG353VS и теперь по умолчанию использует:

```text
MGS2 D3D8
  -> DXVK-Sarek 1.11.1 D3D8/D3D9 (x86)
  -> Wine Vulkan/Wayland (direct 32-bit Wine loader)
  -> proprietary /usr/lib32/libmali.so.1.10.0
  -> Mali-G52 / sway
```

Промоушен сделан по явному решению владельца после правильного живого gameplay
witness. Это решение по игровой оценке, **не новый измеренный FPS claim**.
Сопоставимый DXVK против FINALPLAY15 A/B не получен: уже записанный 30.0/30.0/
30.1 fps spot оказался примерно тем же 28--30 fps capped band, а при переходе
карты у DXVK был один полный секундный интервал без PRESENT. Эти наблюдения не
доказывают ни выигрыш, ни регрессию throughput.

## Точный production bundle

```text
104c79bcc15bd9f36a78e95ce657be35de2f5bae6e6f63008831f3164bda1cde  box86-fp16-dxvk
22e519d266b62bfa54d1d1f81e6314aab7b75890b342908f24d2b454e4af3baa  d3d8_dxvk_sarek_1.11.1_mali_wsiinit3.dll
40ead250117c4a4517d389d7e6f09484c55a1e69ade725a115c8cbf2cb8a5352  d3d9_dxvk_sarek_1.11.1_mali_nullfix1.dll
da865b75737286be88a5faf6002ad5f7a8d4408bb22a451ee0e2ff8283027fab  FINALPLAY16_DXVK.manifest
28e3b23da8a7167225a6a85ced425f00fe085c8396aee75905bc9d28a515455e  launch-play.sh
3f4274b0a580b6d05f5091b695b7d1c67acc861ebcffbae483949ad81f8b28b9  launch-play-dxvk-fp16.sh
1d95c264d84c5173baac72b312724f3dd1415c0139e294acd1c58cbc70cbe329  launch-play-wined3d-fp15.sh
1c13c2aa32d817d6f4795b527fc834e6a20881e0d8993477f8f44452f21e689e  MGS2-Substance.sh
```

`d3d9_mali_count1.dll` с PRESENT counter остаётся только измерительным
артефактом. Production использует неинструментированный `mali_nullfix1` и
скрывает DXVK HUD. State cache оставлен выключенным: именно эта политика прошла
correctness runs; отдельного доказательства для смены политики нет.

Box86 собран два раза с `SOURCE_DATE_EPOCH=1756000000`; оба clean rebuild дали
один SHA выше и Build ID `1f206df48034b2f3196d8f076857af7b620e4ae7`.
Исходная граница — Box86 base
`0579f8b9c47d87d700724f4cce559b06cbd2b0f5` +
`box86-patches/FINALPLAY15-box86-complete.patch` +
`box86-patches/17-native-wayland-vulkan-bridge.patch`. Последний patch имеет
SHA-256 `82ba4d7d5f2d12555d5a28a95180ca70b858cd0eac1ef4580f8e70808db9a42b`;
его применение дало нулевой diff против использованного WSI source tree, если
исключить generated build/island artefacts.

DXVK source: tag `v1.11.1-mali-fix`, commit
`617958fe1cf2b10e06fa751d3e40bd765dcf2cc6`. Production changes:

```text
43cd0cc1790128a2674d8fda96d324bc86e86d3421d1217bafc754d78f69a77a  01-mali-d3d9-pipeline-compat.patch
8131048ac81e93911c678137bd44ef864c5fd21e0185ed4078a4fc62d015e4df  02-d3d8-wine-user-driver-init.patch
```

Patch 03 с memory-only PRESENT counter в production D3D9 не применён.

## Production preflight и live proof

`FINALPLAY16_DXVK.manifest` проверяет 18 live files после bind mounts: новый
Box86, D3D8, D3D9, четыре production audio DLL, системные Wine Wayland/Vulkan
модули и точные `libmali`/`libvulkan`. Любое отличие останавливает запуск до
игры. Первый smoke действительно остановился fail-closed из-за вручную
укороченного на два символа SHA dsound в новом manifest; строка исправлена на
реальный 64-символьный SHA, после чего проверка дала 18/18.

Проверенный candidate:

- запущен с новым воспроизводимым Box86;
- показал освещённое интерактивное меню;
- имел точные D3D8/D3D9 hashes и live mappings WineVulkan + libmali;
- завершился через launcher trap без процессов и bind mounts;
- восстановил app-local D3D8 до `ab6bf7a9...`.

Затем реальный внешний `/storage/roms/ports/MGS2-Substance.sh`, без renderer
override, выбрал FINALPLAY16. Live hashes были `104c79...` / `22e519...` /
`40ead2...`, identity `18/18`; после bounded smoke снова не осталось процессов
или mounts. Обе копии PortMaster wrapper имеют один SHA `1c13c2...`.

Финальная проверка также поймала отдельную launcher-lifetime дыру. Дочерний
`wineboot.exe` наследовал fd 9 с `flock`, переживал родительский launcher и
одновременно удерживал `/usr/bin/box86` busy. Следующий запуск поэтому тихо
выходил на `flock -n`, а cleanup не мог снять bind mount. Это не renderer fault.
В production runtime теперь:

- fd 9 закрывается во всех Wine/gptokeyb/thermal children;
- cleanup явно завершает `wineboot.exe`;
- unmount имеет bounded retry и пишет точную ошибку вместо немого `return 1`;
- ошибка source/bind mount также называет оба пути.

После исправления внешний wrapper снова дал game PID, identity 18/18 и точные
mounted hashes. `/proc/<game>/environ` подтвердил `DXVK_STATE_CACHE=0`, пустой
`DXVK_HUD`, `MGS2_BOX86_ISLAND_FULL=0` и `MGS2_GL_DMABUF=0`. После TERM не
осталось `wineboot`/Wine/MGS2 процессов или mounts; `/usr/bin/box86` восстановлен
до system SHA `706dfcc9...`, app-local D3D8 -- до `ab6bf7a9...`.

Снимок release build:

```text
52a1cdbfd697914a91623be40b0d054a1ceeeb8e6056fe8830850e06923452cb
docs/evidence/MGS2_FINALPLAY16_LIT_MENU_2026-08-24.png
```

Автопилот сообщил `window focus=False`, поэтому этот снимок доказывает только
lit/menu/present release smoke. Он не переименовывается в gameplay proof.
Правильный gameplay witness, input и moving state для того же DXVK/WSI code
зафиксированы отдельно в `MGS2_DXVK_SAREK_FIRST_GAMEPLAY_2026-08-24.md`.

## Rollback

Откат не требует копирования DLL или удаления файлов:

```bash
MGS2_RENDERER=wined3d /storage/roms/ports/MGS2-Substance.sh
```

Это выполняет byte-exact старый `launch-play.sh` FINALPLAY15 под именем
`launch-play-wined3d-fp15.sh` (SHA `1d95c264...`) с его прежним prefix64,
WineD3D, island и `FINALPLAY.manifest`.

Вернуть WineD3D как постоянный default можно изменением одной строки selector:
`MGS2_RENDERER=${MGS2_RENDERER:-wined3d}`. Текущий production default — `dxvk`.

## Что остаётся открытым

- нет сопоставимого fixed-scene FPS A/B против точного FINALPLAY15;
- не пройдены codec/cutscene, все weapon/fog/alpha effects, save write/read и
  20-минутный ручной soak;
- music, menu clicks и gameplay SFX ещё не подтверждены как три отдельные
  production observations;
- переход карты всё ещё может иметь секундный PRESENT hitch.

Это открытые validation пункты после осознанного промоушена, а не скрытые
утверждения о уже доказанном результате.

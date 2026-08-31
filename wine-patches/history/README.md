# Не серия сборки

Эти патчи объясняют, **почему** каждое изменение было сделано. Собрать из них
дерево нельзя, и это измерено, а не предположено: применённые по порядку к
чистому Wine 11.0 они дают

```text
применилось 53 из 67
не применились 14, среди них 71-dmabuf-presenter,
    75-separable-lazy-stage-selector и 79 — то есть весь продакшн-рендерер
после 53 применившихся 25 файлов всё ещё отличались от продакшна,
    включая glsl_shader.c, winewayland.drv/opengl.c, swapchain.c,
    context_gl.c, cs.c и device.c
```

Причина простая: каждый файл снимался с того состояния дерева, какое было на тот
момент, поэтому они не композируются.

Собирать надо из `wine-patches/FINALPLAY*-wine-complete.patch` поверх
закреплённого `wine-11.0.tar.xz`. Проверяет это `harness/verify_rebuild.sh`,
производит релиз `harness/make_release.sh`.

## Audit follow-up 84--85

`84-dmime-message-private-state-layout.patch` moves `curve_phase` before
the variable-size public `DMUS_PMSG` payload. This prevents curve messages
from overwriting the private phase field (and the private write from corrupting
`DMUS_CURVE_PMSG.mtDuration`).

`85-dmsynth-sink-lifetime-and-clock-state.patch` makes activation report
thread startup failures, keeps the renderer alive across a recoverable
`DSERR_BUFFERLOST`, releases every thread-owned object on all exits,
resets activation state, resynchronises the write cursor before rebasing the
timeline and serialises 64-bit clock reads on 32-bit ARM.

These records reconstruct the fixed-epoch `dmime_p16` and `dmsynth_p38` DLLs
pinned by `device/AUDIO_LIFETIME_CANDIDATE.lock` and promoted in FINALPLAY22.
They are not part of a sequential history build. Their pre-resume device smoke
passed; the owner accepted the open post-resume SFX gate for promotion.

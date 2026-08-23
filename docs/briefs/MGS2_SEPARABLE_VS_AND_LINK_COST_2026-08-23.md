# MGS2_GL_SEPARABLE_VS measured and left off, and the real size of the load freeze

23 August 2026, on FINALPLAY15, one `harness/autoload_save.sh` route per arm,
`MGS2_GPU_PROBE=1`, read with `harness/shader_compile_read.py`.

## The question

Patch 30 adds the separable-stage treatment to a **programmable** vertex shader
paired with an FFP pixel shader. It has always been off by default, and the
comment above the switch in `glsl_shader.c` justified that with a measurement
from 13 August:

> 27 program links costing 5765 ms, every one monolithic, because the gate
> requires an FFP vertex shader while MGS2 draws the world and its characters
> with a programmable one. That is about half of all stall time in the run.

So: is half the stall time still sitting there?

## The answer: no, and turning it on now costs time

```
                          arm A (off)              arm B (SEPARABLE_VS=1)
link program            3 x 149.95 =  449.9 ms   0 x    -   =      0 ms
link separable stage   19 x 196.79 = 3738.9 ms  23 x 210.44 = 4840.2 ms
                       ---------------------    ----------------------
linking, total                      4188.8 ms                4840.2 ms

compile shader         23 x   6.81 =  156.6 ms  23 x   7.75 =  178.2 ms
validate pipeline      15              2.1 ms   18              2.7 ms
slow bind              10             14.3 ms   17             26.5 ms
```

Arm B is **651 ms worse**, and the counters show the mechanism rather than
suggesting it: three monolithic links disappear (-449.9 ms) and four stage links
appear (+841.8 ms at arm B's mean). A program that cost ONE monolithic link at
~150 ms becomes stage links at ~200 ms each. There is nothing to make that back.

Honest bound on the number: one run per arm, and the mean per stage link drifted
196.79 -> 210.44 (+6.9%) between them, which by itself accounts for ~260 ms across
the 19 links both arms share. So the conversion itself costs about **+390 ms**,
not 651. The sign does not depend on that, and the per-link arithmetic explains
it without statistics.

## Why the 13 August premise expired

It was true when written. Since then patch 27 (separable stage programs) and
patch 32 (FFP source dedup) absorbed nearly all of it: **three** monolithic links
remain on this route, not 27. There is no longer half a run's stall time behind
this switch, because something else already took it.

This is worth remembering as a habit and not just a fact: a comment that carries
a measurement carries a DATE, and two later patches on the same path invalidated
this one without anybody touching the comment.

## Picture

Not broken on this route, and not proven safe either.

* the five screenshots that reproduce between runs at all (save list, two
  save-cursor steps, confirm box, on-yes) are **byte-identical** between arms
* the in-game shots were looked at directly: geometry, lighting, character
  skinning, decals and the HUD frame are correct in arm B
* zero `failed validation`, zero pipeline info logs, zero GL errors, zero island
  faults

But patch 30 touches the six places that each broke the picture at least once
while patch 27 was being written -- attribute bindings, `vs_c[]` locations, the
constant update mask, sampler resources, the stage cache, the pipeline builder --
and the autoload route contains no cutscene, no codec and no effects. "Not broken
here" is the whole claim.

**Left OFF.** Production defaults untouched; both arms were environment-only runs.

## The finding that matters more than the question

In **both** arms, loading a save spends **4.2-4.8 seconds in shader linking
alone** -- 19 to 23 stage links at ~200 ms each. That is the multi-second freeze
after a load, and choosing between monolithic and separable moves it by ~0.5 s in
the wrong direction.

Alongside it: `compile shader 23, distinct sources 23`. **Not one repeated
source.** An in-run compile cache buys nothing, which closes that from a second
direction after the program-binary branch was closed on the driver's process
scope.

So the win here is not linking more cheaply. It is **not linking at that moment**:
save the FFP generation recipe and re-link during a loading screen or fade, MRU
over the last 16-32 expensive shaders (link >= 100 ms). This measurement gives
that plan a size -- up to ~4.5 s per load -- instead of a hypothesis.

## Reproducing it

```sh
cd /storage/roms/ports/MGS2-Substance
MGS2_GPU_PROBE=1 [MGS2_GL_SEPARABLE_VS=1] \
    MGS2_AUTOLOAD_LOG=ablogs/arm-game.log \
    setsid nohup ./autoload_save.sh ablogs/arm-shots &
# once the walk bursts finish
python3 shader_compile_read.py $(pgrep -f mgs2_sse_rg353vs)
```

Neither variable is a binary override, so `launch-play.sh` accepts them and the
eleven-file identity check still runs in full: these are production runs with two
switches flipped, not research builds.

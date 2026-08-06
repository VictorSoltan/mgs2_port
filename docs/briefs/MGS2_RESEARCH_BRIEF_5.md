# Research brief #5 — the white rain effect: every layer measures correct

> **RESOLVED (mostly), 2026-08-02.** The round that followed this brief named the cause on
> its first suggestion: **the provoking-vertex convention**. Confirmed by measurement, see
> the box below. This document is kept for the evidence trail and for the residual
> question in §3.3, which is still open.
>
> ```
> glProvokingVertex     = 00000000   (no such entry point in GLES)
> ARB_PROVOKING_VERTEX  = 1          (wrongly credited by the desktop-3.2 promotion)
> EXT_PROVOKING_VERTEX  = 0
> emulated_flatshading  = 1          (flat varyings are emitted)
> ```
>
> Wine emits `flat` diffuse varyings and asks GL for `GL_FIRST_VERTEX_CONVENTION`, but that
> call is guarded on `glProvokingVertex` being non-NULL. On GLES it is NULL, so neither
> branch runs and the convention stays at GL's default **last** vertex, while D3D specifies
> the **first**. Correct vertex bytes, correct arithmetic, wrong vertex chosen for the whole
> triangle.
>
> A/B with `MGS2_NO_FLATSHADING=1` (forces smooth interpolation — a diagnostic, not a fix):
>
> | | saturated white | near-white |
> | --- | --- | --- |
> | control, flat shading on | **31.97%** | 33.90% |
> | forced Gouraud | **5.53%** | 6.38% |
>
> Caveat: camera position differed slightly between runs, so this is not a perfectly
> controlled pair — but earlier captures at this point were consistently ~30%, and a 5.8×
> drop is far outside that variation.
>
> **No cheap fix exists.** libmali advertises 107 extensions and **none** of them is a
> provoking-vertex selector, so the driver cannot be asked for first-vertex convention.
> The correct repair is to reorder primitives so D3D's first vertex lands where GL looks:
> rotate each triangle `[a,b,c] → [b,c,a]` (preserves winding), expanding strips and fans
> to lists first. Gate on `flat_shading && !ARB_PROVOKING_VERTEX && !EXT_PROVOKING_VERTEX`
> so it repairs the API semantic mismatch generally rather than patching one game.
>
> This is the **third** defect in this project from the same root: Wine promoting
> extensions by *desktop* GL version. `ARB_ES2_COMPATIBILITY` was missing where needed,
> `EXT_DRAW_BUFFERS2` was granted where harmful, and now `ARB_PROVOKING_VERTEX` is granted
> with no function behind it.


Self-contained. Supersedes the white-effect sections of earlier briefs. Project history:
`MGS2_PROJECT_STATE.md`.

The previous round's ranked hypotheses were all tested. **Three of the four are closed by
measurement**, and the fourth turned out to be measuring the wrong thing. What follows is
the complete evidence, then the one question that remains.

---

## 1. Setup, in one paragraph

Metal Gear Solid 2: Substance (PC, Direct3D 8, 2001) on an Anbernic RG353VS — Rockchip
RK3566, Mali-G52, **libmali, OpenGL ES 3.2 only**. box64 launches Wine 11.0; the 32-bit
game runs under box86. Path: D3D8 → local `d3d8.dll` proxy → d3d9 → WineD3D → GLES. The
game is playable: full menus, codec conversations with portraits, Tanker gameplay, zero
page faults over 60–70-step scripted runs.

**The defect:** in the rainy Tanker exterior, large irregular areas of the floor and
splash surfaces render as saturated white.

## 2. What is measured and correct

Every one of these is a direct runtime measurement on the device, not inference.

| layer | measurement | verdict |
| --- | --- | --- |
| draw class | skipping `SRC_ALPHA/INV_SRC_ALPHA` draws removes the defect and leaves scene geometry | causal class identified |
| stored texels | GPU readback of the gameplay atlases — alpha bytes equal the CPU upload bytes | correct |
| vertex data | mapped late VBOs — expected alpha, raw 0..4096 UVs | correct |
| GL blend state *at the draw* | `enabled=1`, `src=SRC_ALPHA`, `dst=ONE_MINUS_SRC_ALPHA`, `equation=FUNC_ADD`, write mask `1 1 1 1` | correct |
| render target | `GL_TEXTURE`, red 8 bits, alpha 8 bits, `COLOR_ENCODING = GL_LINEAR` (not sRGB) | correct |
| bound texture | `B8G8R8A8_UNORM`, 1024×1024, `levels=1`, `color_fixup = X,Y,Z,W` (identity) | correct |
| sampler | `min=GL_LINEAR_MIPMAP_NEAREST`, `mag=GL_LINEAR`, `base=0`, **`max=0`**, swizzle `R,G,B,A` | complete texture, identity swizzle |
| FFP descriptor | `cop=MODULATE` / `MODULATE_2X`, `aop=MODULATE_2X`, `aarg1=TEXTURE`, `aarg2=CURRENT` | as D3D asked |
| shader arithmetic | see below | correct |
| sampled colour | see below | white — and plausibly correct |

### 2a. The shader arithmetic is exact

A probe (`MGS2_ALPHA_PROBE=1`) encodes the *effective* alpha operands and the stage result
into the fragment colour: `R = operand 1`, `G = operand 2`, `B = computed alpha`, `A` forced
to 1 so the diagnostic passes through the normal blend equation untouched.

Checking `B == clamp(2*R*G, 0, 1)` per pixel: **0 mismatches in 34 240 sampled pixels**,
including non-trivial cases — `1.000 × 0.251 → 0.502`, `0.671 × 0.502 → 0.675`. So the
generated GLSL is right and Mali executes it correctly.

**Methodological note.** A whole-frame version of this probe showed 91.7% of pixels with
both operands at 1.0, which looks damning and means nothing: opaque geometry legitimately
has alpha 1. The measurement only becomes evidence once restricted to the implicated draw
class (`MGS2_ONLY_SRCALPHA_INVSRCALPHA=1`, the inverse of the skip switch). Restricted, the
picture inverts completely — **0.0%** of drawn pixels have both operands at 1.0, and the
typical values are `1.000 × 0.314 → 0.627`, `1.000 × 0.125 → 0.251`, `1.000 × 0.020 → 0.039`.

### 2b. The texture samples white with alpha 1 — and that may be correct

`R` in that probe is `WINED3DTA_TEXTURE`'s alpha, and it is exactly 1.000 everywhere. A
second probe (`MGS2_TEX_RGB_PROBE=1`) outputs the stage-0 sampled RGB directly:

```
(255,255,255)  97.2% of the drawn area
grey 88…129     soft edges
```

So the sampler returns **white, opaque**. For a rain/splash sheet that is a normal asset
design: a white texture whose translucency comes entirely from per-vertex alpha. `CURRENT`
at stage 0 is `DIFFUSE`, and its alpha does vary (0.02–0.5), consistent with fading
particles.

`MODULATE_2X` then doubles it — which is exactly what D3D specifies. Vertex alpha ≥ 0.5
therefore yields a fully opaque white fragment **by definition**, on any correct
implementation.

## 3. The question

Every layer in the GLES translation measures correct, and the arithmetic is provably
faithful to the D3D definition. So either:

1. **the same inputs produce the same image on desktop D3D**, in which case this is port or
   configuration behaviour and should not be "fixed" in WineD3D at all; or
2. something upstream of everything measured differs — the *number* or *coverage* of these
   draws, or the vertex alpha distribution actually submitted, rather than any per-draw
   state.

Concretely:

1. On a desktop reference of the **same executable, same V's/d3d8 proxy, same assets, same
   640×480 configuration**, does the rainy Tanker exterior show the same white saturation?
   (A local reference is staged at `recovered-session/local-reference/game` with a matching
   executable hash; an initial attempt failed on a host Wine WoW64/XWayland resize loop
   between 640×480 and 4096×2560 and produced no valid evidence.)
2. If desktop is clean: what upstream difference could change the *distribution* of vertex
   alpha or the draw count for a D3D8 FFP particle effect, given that per-draw state,
   texture, sampler, blend state and shader all match? Candidate areas: vertex declaration
   / D3DCOLOR normalisation on the diffuse attribute, `D3DRS_ALPHAREF` and the shader alpha
   test path, or the texture-stage chain of a *later* stage that the stage-0 probes do not
   cover.
3. Is there a way to count and visualise per-frame draw coverage for one blend class
   cheaply, so "the effect is drawn many more times than intended" can be separated from
   "each draw is too opaque"? Accumulated correct translucency and single-pass wrong
   translucency look identical in a screenshot.

## 4. Hypotheses closed by this round — please do not re-open

* **Mali miscompiling the whole-vector `op_equal` path.** 0 formula mismatches.
* **A Wine `MODULATE2X` semantics bug.** Same.
* **Blend enable / factors / render-target format.** Read back from GL at the draw itself;
  all correct, target is linear not sRGB.
* **Sample-time alpha differing from uploaded alpha because of mip levels, filtering or
  colour fixup.** `levels=1` with `MAX_LEVEL=0` is complete; swizzle and fixup are identity.
* **`specular.a` saturating the output.** `ps_out[0] = ffp_varying_specular * specular_enable + ret`
  is a `vec4` add, but `specular_enable` is `{1,1,1,0}` — alpha is deliberately zeroed.
* **Texture format handling.** The bound texture is plain `B8G8R8A8_UNORM` with an identity
  fixup, not one of the 16-bit or luminance formats fixed earlier in the project.

## 5. Reproducing the instrumentation

All switches are off by default and live in the WineD3D build:

| variable | effect |
| --- | --- |
| `MGS2_ALPHA_PROBE=1` | `R`/`G` = effective alpha operands, `B` = stage result, `A` = 1 |
| `MGS2_TEX_RGB_PROBE=1` | output the stage-0 sampled RGB directly |
| `MGS2_ONLY_SRCALPHA_INVSRCALPHA=1` | draw *only* the implicated class (inverse of the skip switch) |
| `MGS2_SKIP_SRCALPHA_INVSRCALPHA=1` | suppress the implicated class |

The descriptor, sampler parameters and real GL blend state are written to
`/tmp/mgsffp.log`, `/tmp/mgstexdraw.log` and `/tmp/mgsblend.log`.

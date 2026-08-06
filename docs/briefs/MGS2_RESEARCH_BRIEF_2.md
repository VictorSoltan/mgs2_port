# Research brief #2 — WineD3D on GLES renders wrong after the crashes were fixed

Self-contained; no prior context needed. Supersedes `MGS2_RESEARCH_BRIEF.md`, whose main
question ("why can't the tree be rebuilt?") is now **answered**. Full project history is in
`MGS2_RG353VS_HANDOFF.md`.

---

## 1. Setup

Metal Gear Solid 2: Substance (PC, **Direct3D 8**, 2001) on an Anbernic RG353VS handheld.

| | |
| --- | --- |
| SoC | Rockchip RK3566, 4× Cortex-A55, **Mali-G52** (Bifrost) |
| OS | ROCKNIX (Linux), sway/Wayland, EmulationStation |
| GPU driver | proprietary ARM **libmali** — **OpenGL ES 3.2 only**, no desktop GL, no 32-bit Vulkan ICD |
| Emulation | box64 launches Wine; the 32-bit game runs under **box86** (Wine old-WoW64) |
| Graphics path | D3D8 → local `d3d8.dll` proxy (V's Fix) → d3d9 → **WineD3D** → OpenGL |
| Wine | 11.0, built from source with MinGW (`i686-w64-mingw32`) |

**Hard constraint: libmali stays.** Panfrost/Mesa (real desktop GL), VirGL and gl4es were
each considered and rejected — libmali is materially faster and this port has no
performance margin. VirGL is absent from the device; the local gl4es build is destroyed.

The underlying difficulty is unchanged: **Wine upstream does not support OpenGL ES in
WineD3D**, and on this device **3144 of 5256 GL entry points resolve to NULL** (all of
desktop fixed-function and immediate mode). Calling one jumps to address zero.

## 2. What is now solved

Rebuilding WineD3D from source used to die before the title screen, which blocked every
code-level fix and forced binary patching. **That is fixed.** Three source changes make a
rebuild survive, all found by tracing rather than guesswork:

**(a) `adapter_gl.c` — a GLES context was being classified as "legacy".**
Core-vs-compatibility is a desktop concept; `GL_CONTEXT_PROFILE_MASK` yields nothing on
GLES, so the fall-through marked it legacy, which installs fixed-function state handlers
that call non-existent entry points.

```c
if (gl_info->is_gles)
    TRACE("GLES context, treating as core profile.\n");
else
{ /* original GL_CONTEXT_PROFILE_MASK logic, may set WINED3D_GL_LEGACY_CONTEXT */ }
```

**(b) `ffp_gl.c` — the viewport handler called desktop-only `glDepthRange`.**

```c
if (gl_info->gl_ops.ext.p_glDepthRangef)
    gl_info->gl_ops.ext.p_glDepthRangef(min_z, max_z);
/* else skip: GLES defaults to [0,1], which is also the D3D default */
```

**(c) `glsl_shader.c` — `glBindFragDataLocation` was called unguarded while linking every
program.** This was the fatal one. GLES has no such call; outputs are bound by
`layout(location=)` in the shader.

```c
if (!gl_info->is_gles) for (i = 0; i < WINED3D_MAX_RENDER_TARGETS; ++i)
{ ... GL_EXTCALL(glBindFragDataLocation(program_id, i, tmp_name->buffer)); }
```

Result: **0 page faults**, where every previous rebuild produced exactly one.

## 3. The problem now

**The rebuild runs but renders incorrectly, and worse than the binary-patched build it
should replace.** On the title screen:

- the logo is **scaled up roughly 1.6× and cropped** at both edges;
- the **background artwork is entirely absent** (solid black);
- **`PRESS START BUTTON` does not appear**.

For comparison, the same screen through the binary-patched build renders with correct
geometry and all elements present (screenshot ~105 KB PNG versus ~13 KB for the rebuild —
the size gap is itself a good proxy for how much content is missing).

Both builds are the same WineD3D otherwise; the rebuild adds (a), (b), (c) above plus the
texture conversions in §4.

### Both hypotheses were tested and are WRONG

**H1 (viewport/clip-control) is wrong.** Research confirmed, and a build agrees: the
`_cc` handlers are selected by `ARB_CLIP_CONTROL`, not by `WINED3D_GL_LEGACY_CONTEXT`.
Reverting the core-profile change entirely still renders wrong.

**H2 (alpha = 0) is wrong.** `X1R5G5B5` is a *separate* format ID from `A1R5G5B5`, so the
A1 converter was never applied to it. Dedicated converters were then added for
`B5G5R5X1`, `B4G4R4X4` and `B8G8R8X8` — the last one had a genuine bug worth recording
(it reused the A8 byte-swap, which carries the undefined X byte into alpha, so a zero X
gave a fully transparent texture) — and `GL_RGB5`/`GL_RGB4`, which are not GLES internal
formats, were replaced. **None of it changed the picture.**

### What the bisect actually shows

| build | title frame |
| --- | --- |
| crash fix only (fragdata) | 1 671 bytes — almost entirely black |
| + depth-range + texture conversions | 13 231 |
| + core-profile classification | 13 064 |
| `dbg42` binary-patched (reference) | **104 962 — correct** |

**Caveat on that table — frame size is a weak metric.** The title screen cycles through an
attract loop (logo, black transitions, demo footage), so a single screenshot's size depends
heavily on *when* it was taken. The same reference build later measured 13 414 on one
capture and 104 962 on another. Treat the numbers above as indicative only; the solid
evidence is the screenshot that was actually inspected, which showed a scaled-up cropped
logo over a black background with no `PRESS START BUTTON`.

With that caveat, the direction still holds: no combination of the fixes reproduces the
reference build's output, and removing them does not help either. dbg42 evidently contains
further GLES rendering work that the tree does not, and which is not visible in the symbol
table (which matched to one entry).

**A better metric is needed before the next round.** Frame-size sampling should be replaced
by either capturing several frames and comparing the *richest*, or by driving to a known
static screen (the WARNING dialog is deterministic — byte-identical across separate runs)
and comparing that.

The crash is genuinely fixed in source. The rendering gap is the original lost-source
problem, still unsolved, now isolated to rendering rather than stability.

### Superseded hypotheses (kept for the record)

**H1 — the viewport/projection path changed.** `ffp_gl.c` contains both
`viewport_miscpart` and `viewport_miscpart_cc` (clip-control) variants, and the state
table selects between them. Forcing the context to core profile in (a) plausibly changed
that selection. Related: `rasterizer()` carries the comment *"Rendering without
ARB_clip_control requires flipping position manually. This also means that all primitives
will be backwards, so we need to also swap which side is the front face."* — so
clip-control handling and winding are coupled here.

**H2 — the 16-bit conversion drives alpha to zero.** If the game's textures are really
`X1R5G5B5` rather than `A1R5G5B5`, the unused X bit is 0; rotating it into the alpha
position yields **alpha = 0**, i.e. fully transparent. That would make content disappear
rather than merely look wrong, matching the symptom better than a colour error would.

### Questions

1. Which viewport/clip-control state handlers does WineD3D select for a **core-profile**
   context versus a legacy one, and what exactly changes about the projection or the
   position fixup? Is `ARB_clip_control` expected to be present, and what is the correct
   behaviour when it is absent *and* the context is core profile?
2. Is forcing `WINED3D_GL_LEGACY_CONTEXT = FALSE` on GLES the right lever at all, or
   should GLES get its own flag so that it takes the shader-based fixed-function path
   without inheriting every other desktop core-profile assumption?
3. How should D3D `X1R5G5B5` / `X8R8G8B8` be distinguished from their alpha-bearing
   siblings during upload, so the X channel becomes 1.0 rather than 0? Does WineD3D
   already express this (a colour fixup, a format flag), and is the correct fix in the
   converter or in the format table?
4. `glDepthRangef` is not exposed to WineD3D here (win32u does not pre-resolve it), so
   fix (b) currently *skips* the call. Under what circumstances does a D3D8 title actually
   set a non-default depth range, and is skipping safe for this game?

## 4. Texture conversions — written, not yet validated

Implemented in `utils.c` next to the existing `convert_b8g8r8a8_unorm_gles`, following the
previous round of research. They cannot be evaluated until §3 is resolved.

| D3D format | GL format / type | conversion |
| --- | --- | --- |
| `B5G5R5A1_UNORM` | `GL_RGBA` / `GL_UNSIGNED_SHORT_5_5_5_1` | 16-bit rotate left by 1 (right on download) |
| `B4G4R4A4_UNORM` | `GL_RGBA` / `GL_UNSIGNED_SHORT_4_4_4_4` | 16-bit rotate left by 4 (right on download) |
| `B8G8R8X8_UNORM` | `GL_RGBA` / `GL_UNSIGNED_BYTE` | reuse the 8888 byte swap |

Rationale: `GL_BGRA` and the `_REV` packed types do not exist in GLES, so those uploads
previously failed outright and the textures kept undefined contents. Both rotations are
exact and keep two bytes per texel, so no expansion to RGBA8 is required.

Still unanswered from the previous round: whether libmali exposes
`GL_EXT_texture_format_BGRA8888` (which would help the 8888 cases only, not the packed
16-bit ones), and whether the game uses DXT1/3/5 at all — Mali does not normally expose
S3TC, and WineD3D's built-in BC decompressor appears wired only for 3D textures.

## 5. Secondary, still open

5. With the binary-patched build the game reaches a 3D scene and then exits **cleanly**
   after ~100 s — no page fault. Cause unknown.
6. Wine `MessageBox` dialogs draw the frame and icon but **no text**. 69 fonts were
   symlinked into the prefix with no effect; win32u's freetype support is byte-identical
   to the working build. Text is only readable via a relay trace (`RelayInclude` under
   `HKCU\Software\Wine\Debug` plus `WINEDEBUG=+relay`), which is how the string
   `"Failed creating Direct3D8 Object."` was captured during an earlier failed experiment.

## 6. Ruled out — please do not re-investigate

- **Presentation driver.** The Wayland presentation path was rebuilt from scratch; an A/B
  of the same frame through two different presentation drivers gives identical corruption.
  It is not the cause of any visual defect.
- **Fonts.** Installing the full Wine font set changed the blank MessageBox by literally
  zero bytes (byte-identical frame).
- **`ffp_hlsl`.** `WINE_D3D_CONFIG=ffp_hlsl=0x1` removes the per-frame FFP errors but
  crashes earlier: it only replaces FFP *shader generation*, leaving the `ffp_gl.c` state
  table installed.
- **`glAlphaFunc`.** Loud in the logs but resolves **non-NULL**; never the fatal call.
- **The fault address.** `returning to user mode ip=79d32476` appears for every failure,
  including ones where the offending call had provably been removed. It is a shared
  opengl32/win32u thunk that any NULL entry point lands on — it identifies *nothing*.

## 7. Methodological note that mattered more than any single fix

Wine's `ERR` output, routed through box86 into a redirected file, is buffered and **loses
its tail when the process dies**. For hours this made "the last line in the log" look like
"the last thing that executed", and several wrong conclusions followed. The give-away was
a pointer dump printing twice while the immediately following line printed once.

Replacing it with an unbuffered tracer — `fopen`/`vfprintf`/`fclose` per call, the pattern
already used by the project's presentation driver — turned a day of guessing into three
targeted steps. Any further debugging on this stack should use that, not `ERR`.

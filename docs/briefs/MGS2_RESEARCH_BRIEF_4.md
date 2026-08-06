# Research brief #4 — WineD3D on GLES: the entry-point gate is the blocker

> Update, 2026-08-02: this was an interim research brief. Its statement that codec
> conversations "render perfectly" applies to the UI/subtitles, not the previously
> missing portrait render targets. The current authoritative result is in
> `MGS2_PROJECT_STATE.md`: GLES-safe FBO probing plus a narrowly identified codec
> black-quad suppression restores and animates the portraits in a test build. The same
> document also replaces the old white-effect texture-census lead with measured alpha,
> UV and GL-state results.

Self-contained; no prior context needed. **Supersedes briefs #1–#3**, whose main questions
are now answered or disproven — several of them by measurements that contradicted what
those briefs asserted. Project history: `MGS2_RG353VS_HANDOFF.md`.

---

## 1. Setup

Metal Gear Solid 2: Substance (PC, **Direct3D 8**, 2001) on an Anbernic RG353VS handheld.

| | |
| --- | --- |
| SoC | Rockchip RK3566, Mali-G52 (Bifrost) |
| OS | ROCKNIX (Linux), sway/Wayland |
| GPU driver | proprietary **libmali** — **OpenGL ES 3.2 only**, no desktop GL, no 32-bit Vulkan ICD |
| Emulation | box64 launches Wine; the 32-bit game runs under **box86** (Wine old-WoW64) |
| Path | D3D8 → local `d3d8.dll` proxy (V's Fix) → d3d9 → **WineD3D** → OpenGL |
| Wine | 11.0, PE side built from source with MinGW `i686-w64-mingw32` |

**libmali is a hard constraint** — Panfrost/Mesa would give real desktop GL but is
materially slower, and this port has no performance margin. Wine upstream has no GLES
support in WineD3D.

**Buildable:** the PE side (`wined3d.dll`, and anything else under `dlls/*/i386-windows`).
**Not buildable:** the Unix side. `win32u.so` rebuilds all fail with
`Failed creating Direct3D8 Object.`; the working `win32u_glfuncs3.so` is a binary whose
source is lost. This distinction shapes everything below.

## 2. What is already fixed — please do not re-derive

The game now boots, navigates the whole menu tree, starts a new game, and reaches the
in-engine codec (radio) conversations, which **render perfectly** — frequency readout,
PTT meter, and full subtitle text, all crisp. Fixed this round:

| defect | fix |
| --- | --- |
| `glBindFragDataLocation` called unguarded on GLES while linking every program | skip on `is_gles` |
| `glDepthRange` (desktop-only) in the viewport handler | skip; GLES default `[0,1]` matches D3D's |
| **`glBlendEquation` is NULL**, and `blendop()` calls it in the *common* case (colour op == alpha op) | route through `glBlendEquationSeparate`, which *does* resolve, passing the same equation twice |
| `B4G4R4A4_UNORM` (a 1024×512 atlas) never uploaded | `query_internal_format()` had replaced `internal` with `GL_SRGB8_ALPHA8` while `type` stayed `GL_UNSIGNED_SHORT_4_4_4_4` — an illegal GLES pair. Pin `internal`/`srgb_internal` after that call |
| `EXT_DRAW_BUFFERS2` wrongly credited (desktop 3.0), selecting a `STATE_BLEND` handler needing NULL `glEnablei`/`glColorMaski` | clear the flag on GLES |
| prefix had **zero** ACM codecs and no `wavemapper` registered | write the standard `Drivers32` entries |

The `glBlendEquation` fix is the one that unlocked in-game content.

### Disproven — do not re-investigate

* **"The working binary contains lost source."** A full semantic diff (data symbols with
  pointers normalised to `symbol+offset`; 4 193 function bodies; per-function call sets)
  shows the tree and the reference binary are equivalent. The single difference was a
  cosmetic refactor emitting byte-identical GLSL. Rebuilds *looked* worse only because a
  debug tracer doing `fopen`/`fclose` per line sat on the per-draw path.
* **GLES-as-legacy-context.** Forcing core-profile classification changes nothing; A/B
  with the capability dump confirming the flag flipped.
* **`ARB_ES2_COMPATIBILITY` promotion.** Makes things *worse* — see §3.
* **`L8_UNORM` / luminance.** The active row is already `GL_R8`+`GL_RED` with an `XXX1`
  fixup; there is exactly **one** L8 texture and it is **16×16**, not a font atlas.
* **DXT/S3TC, X1R5G5B5, X4R4G4B4.** The game creates none.
* **Fonts.** Text renders fine (see the codec screen).

## 3. The structural blocker: entry points that exist but cannot be reached

Wine turns extensions into internal capability bits using a table keyed on **desktop** GL
version numbers:

```c
{ARB_TEXTURE_RG,        MAKEDWORD_VERSION(3, 0)},
{ARB_TEXTURE_SWIZZLE,   MAKEDWORD_VERSION(3, 3)},
{ARB_ES2_COMPATIBILITY, MAKEDWORD_VERSION(4, 1)},
```

A GLES 3.2 context parses as "3.2" and is scored against that scale, which is meaningless:
GLES 3.2 *has* all three, but lands between thresholds. Measured:

```
is_gles=1  ARB_TEXTURE_RG=1  ARB_TEXTURE_SWIZZLE=0  ARB_ES2_COMPATIBILITY=0
```

Setting `ARB_ES2_COMPATIBILITY` looks like the obvious fix — Wine already has the correct
code behind it (`glClearDepthf` instead of `glClearDepth`, `GL_RGB565` for `B5G6R5`).
**It was tried and it is worse**, because the ES entry points are not reachable:

```
PTR glClearDepthf   00000000     PTR glDrawBuffers      79D22630
PTR glDepthRangef   00000000     PTR glBindFramebuffer  79D08960
PTR glTexStorage2D  00000000     PTR glBlitFramebuffer  79D0C720
PTR glClearBufferfv 00000000     PTR glBlendEquationSeparate 79D0B6D0
PTR glBlendEquation 00000000
```

So the flag trades a working call for a NULL one. Probing `wglGetProcAddress` directly for
**eleven** spellings — `glClearDepthf`, `glClearDepthfOES`, `glClearDepthx(OES)`,
`glDepthRangef(OES)`, `glDepthRangex(OES)`, `glClearBufferfv`, `glClearBufferfi`,
`glInvalidateFramebuffer` — returns NULL for every one.

**The pointers exist.** box86 logs `eglGetProcAddress` results, and the same functions
resolve fine one layer down:

```
glClearBufferfv -> 0x40020e70    glClearDepthf -> 0x40020ec0    glDepthRangef -> 0x40020eb0
```

Wine's `opengl32!wglGetProcAddress` is a thin wrapper: it asks the Unix side for an *index*
and returns NULL on `-1`. So **win32u** is refusing them, evidently gating on desktop
extension strings a GLES context never advertises. `glDrawBuffers` passes because GLES
does advertise its extension. `opengl32.dll` exports only **361** names (the GL 1.1 set
plus wgl), so there is no way round via `GetProcAddress` either; that was tried.

### Questions — this is the highest-value area

1. **Is there a supported way to make `wglGetProcAddress` serve core-GLES entry points on
   a GLES context?** What exactly does Wine's Unix-side `wglGetProcAddress` check in
   Wine 11 (`dlls/opengl32/unix_wgl.c` / `dlls/win32u/opengl.c`), and is there a
   registry key, driver hook, or extension-string override that widens it — short of
   rebuilding win32u?
2. **Has anyone already solved WineD3D-on-GLES?** Box86/Termux/Wine-on-Android stacks run
   Wine over GLES routinely. Is there an existing patch set (wine-tkg, Termux-Wine,
   Box86 wrappers, the `wined3d` GLES work in any fork) that fixes this dispatch problem
   properly, and what shape is the fix?
3. The one successful workaround so far was finding a **synonym that resolves**
   (`glBlendEquationSeparate` for `glBlendEquation`). Is there a systematic list of such
   substitutions for the desktop-only calls WineD3D makes — or better, a way to enumerate
   at startup which of WineD3D's ~600 ext entry points are NULL, so they can be handled in
   bulk rather than one crash at a time?

## 4. Depth clear: currently emulated, is that right?

MGS2 clears depth to **0.0** every frame (measured: the fallback fired 3592 times in one
run), i.e. it uses a reversed depth test. With no way to set the clear value, an earlier
attempt simply skipped the call — and since GL's default is 1.0, the depth test then
rejected essentially all geometry and the scene rendered as a single flat colour.

Current fix: draw a full-screen triangle strip with colour writes masked off,
`glDepthFunc(GL_ALWAYS)`, depth writes on, at `z = 2d - 1` (NDC → window depth is
`(z+1)/2`). Scissor and depth mask are left as the caller set them so the emulated clear
is scissored exactly like a real one. Afterwards the touched states are invalidated
(`STATE_DEPTH_STENCIL`, `STATE_RASTERIZER`, `STATE_BLEND`, `STATE_VDECL`, `STATE_STREAMSRC`,
both `STATE_SHADER`s).

4. Is that the right approach, and is the state invalidation list complete? Concerns:
   multiple render targets, sRGB draw buffers, `glDepthRange` having been left at its
   default, and interaction with WineD3D's FBO/blitter state caching.
5. Is there a cheaper trick — e.g. can the depth buffer be cleared to an arbitrary value
   through `glBlitFramebuffer` from a scratch FBO, or by attaching a depth texture whose
   contents are set another way?

## 5. Two rendering defects with measurements

### 5a. Horizontal striping on animated backdrops

Not corrupted image data — a **uniform fill**. Per-row analysis of a title-screen capture:

* affected rows are exactly `(0, 16, 0)` for all 640 pixels;
* strict period of **4: two rows written, two rows filled**;
* the two filled rows of each group are byte-identical.

It appears only on screens with an animated backdrop (title, main menu, NEW GAME, RADAR),
never on static screens — the Konami logo, the "Konami Computer Entertainment Japan" card
and the legal disclaimer are pixel-perfect. The 16-bit texture converters make **no**
difference to it (same striped-row counts with them on and off).

The game's own PS2 source renders in FIELD mode
(`sceGsResetGraph(0, SCE_GS_INTERLACE, GS_DISP_MODE, SCE_GS_FIELD)`), and a half-height
field stretched 2× vertically gives exactly a 2-on/2-off pattern.

6. Is this a known artefact of the MGS2 PC/Xbox port's field-based rendering, and is there
   a known way to make it render progressive? Or is a 2-on/2-off uniform-fill pattern a
   recognisable signature of some *WineD3D* behaviour (a half-height render target, an
   interlaced blit, a mismatched viewport height)?

### 5b. Gameplay still renders as a flat colour

Once in the tanker scene the frame is a single colour `(71, 99, 92)` over 66% of the
image, 29% black letterbox bars, and under 1% anything else. The depth-clear fix above is
the current candidate and is awaiting confirmation.

7. If the depth clear turns out not to be the cause: what else makes *all* geometry vanish
   while 2D overlays (codec screen, menus, subtitles) still draw correctly on a GLES
   context? Candidates already excluded: blend state, legacy-context classification,
   texture formats.

## 6. Movies — cause known, route unclear

The shipping executable has PSS movie playback **patched out**: at file offset `0x17D82F`,
`7d 1d` → `90 90`, which forces `NewMpegPssMovieStr`/`GetResources` down its
resource-error path (confirmed against the leaked MGS2 source — the field at `+0x188` is
`work->top_pos`). The title-screen backdrop is a PSS movie too, so this is why there is no
picture behind the START prompt.

Reverting those two bytes is **not** sufficient — tested, nothing plays. Movie playback
goes through **DirectShow via COM** (`FilterGraph` ×9, `CoCreateInstance`,
`AMovieSetupRegisterFilter`, `CLSID_ActiveMovieCategories`, `rdr_movie.c`; no static
`quartz` import). The upstream PC-fix project has this open and unresolved
(VFansss/mgs2-v-s-fix issue #88, "Cutscenes go blackscreen and crash").

Everything needed appears present: `quartz.dll`, `devenum.dll`, `winegstreamer.dll`,
`msmpeg2vdec.dll` in the prefix, GStreamer with `libgstlibav` on the device. Assets are
intact (`movie.dat` 305 MB, `demo.dat` 1.48 GB, all read to their final block).

8. What is the practical way to get a DirectShow MPEG-1/2 graph working under Wine for a
   game that registers its own source filter? Does `winegstreamer` cover the video decoder
   here, or is a native filter set (LAV) required — and is software MPEG-2 decode inside
   box86 on a Cortex-A55 even going to be fast enough to be worth it?

## 7. Method notes that cost real time — reuse these

* **Frame size is not a quality metric.** Animated backdrops mean one screenshot's size
  depends on when it was taken. Anchor tests on a deterministic screen; the legal
  disclaimer renders byte-identically across runs and makes a good synchronisation point.
* **Time-based test sequences are invalid.** Identical sleeps put two runs on different
  screens, and their texture censuses were compared as if they meant the same thing.
* **A tracer on the per-draw path must not `fopen` per line.** ~13 file opens per draw call
  slowed the game so much it could not reach the crash being investigated.
* **`eglGetProcAddress` returning non-NULL does not mean WineD3D can call it.** Three
  separate wrong conclusions came from conflating the two layers.
* **`pkill -f` matches the invoking command line**, including environment assignments in
  an `ssh` command — the bracket trick does not save you.
* **The winning localisation loop:** log `debug_d3dstate(state_id)` at both
  `state_table[...].apply()` call sites, run to the crash, and read the last state; then
  dump that handler's entry points. This turned "crashes somewhere in 3D" into
  "`glBlendEquation` is NULL" in one iteration, after cross-referencing a 630-name NULL
  list against the source had produced 79 candidates and no answer.

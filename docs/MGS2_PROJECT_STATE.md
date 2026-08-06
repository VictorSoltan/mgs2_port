# MGS2 Substance on RG353VS — where the project stands and how it got here

Updated 2026-08-02. This is the consolidated record: what works, every fix with its
evidence, everything disproven, what is still broken, and how to reproduce all of it.

The 2026-08-02 update replaces the stale texture-census lead in §6a. It also records the
first reproducible codec-portrait fix, which is deliberately still a test build rather
than the production default.

Companion documents:
* `MGS2_RG353VS_HANDOFF.md` — the running log, more detail, some sections superseded.
* `MGS2_RESEARCH_BRIEF_4.md` — self-contained brief for outside review (supersedes #1–#3).
* `MGS2_RESEARCH_BRIEF_5.md` — the white rain effect; resolved, provoking-vertex convention.
* `MGS2_RESEARCH_BRIEF_6.md` — performance; the profile and the syscall finding in §10.
* `MGS2_EXTERNAL_RESEARCH_BRIEF_2026-08-02.md` — concise current brief for external
  research; separates confirmed facts from the remaining questions.

---

## 1. Bottom line

**The game is playable.** It boots, plays the intro, navigates the whole menu tree, starts
a new game, plays the codec conversations, and reaches the Tanker with the player able to
move around. A scripted 60-step run held sustained gameplay frames (200–290 KB PNG) with
**zero page faults** — the first run in the project's history that did not end in a crash.

| defect | status |
| --- | --- |
| white saturation over gameplay surfaces (the rain) | **fixed and promoted** in `wined3d_dbg150_cxcaps.dll`; user-confirmed correct |
| codec portraits absent | fixed and promoted after two 70-confirm, zero-fault RG353VS runs |
| cutscenes absent | **largely fixed** by the same build; user reports cutscenes now visible |
| horizontal striping on animated backdrops | open, characterised — §6c |
| title backdrop / movie playback | open, needs DirectShow work — §6d |
| second location: "problem with the disc you're using" | cause identified (§6e), fix built, untested |
| **frame rate, 15–23 fps** | **the main remaining defect** — see §10 |
| no audio at all | **fixed 2026-08-02** — `dmime_graphqi.dll`, see §11 |

Note on §6a: it analyses the white rain as unresolved because it was written before the
CrossOver capability port. The analysis there is still the correct account of *why* the
defect existed, and its provoking-vertex conclusion still stands as an unfixed API-semantics
mismatch; the visible rain defect itself is gone.

## 2. Shipping configuration

Everything is selected by `launch.sh`; each has an environment override so a variant can
be tried without editing the launcher.

| component | default | env override |
| --- | --- | --- |
| executable | `mgs2_sse_rg353vs_port.exe` | `MGS2_EXE` |
| Wayland presentation | `winewayland_pbo1.so` | `MGS2_WAYLAND_SO` |
| win32u | `win32u_glfuncs3.so` (prebuilt, source lost) | `MGS2_WIN32U_SO` |
| **Unix opengl32** | **`opengl32_glesver1.so`** (built from source) | `MGS2_OPENGL32_SO` |
| **WineD3D** | **`wined3d_dbg123_gles_fbo_readback.dll`** (built from source) | `MGS2_WINED3D_DLL` |

SHA-256 checksums of the deployed set (verified on the RG353VS after promotion):

```
ca147d1738874532794ec9e64ccdc074039e0b665cea47500fd476c92e49727f  launch.sh
23631920b4145190ae977b192606579769747ef1d0cb2191d248e31a05be0b4f  wined3d_dbg123_gles_fbo_readback.dll
b9a975657159abd72e37c9f7550a7a7684188ee39c7cd161edffdc3d713e19fe  opengl32_glesver1.so
6acdbbaeb8b88ba64fc160a1faf865ae304108705c38bccadaf6bc538f2be63a  win32u_glfuncs3.so
b09e66cce5d63b63301ecdd786529739fac1f71b89e0813540ba70c034a66ca1  winewayland_pbo1.so
```

Both graphics components are now **compiled from source**. Until this round the shipping
WineD3D was a binary-patched blob (`dbg42`) whose source was believed lost.

Diagnostic switches are off by default unless stated otherwise:

| variable | effect |
| --- | --- |
| `MGS2_MANIFEST=1` | one-shot dump of GLES capability bits, per-format records and entry-point pointers |
| `MGS2_TEXLOG=1` | one line per texture creation: format, size, usage, access |
| `MGS2_UPLOG=1` | one line per GL texture upload: update box, row pitch, destination size |
| `MGS2_TRACE=1` | per-draw state trace — names every `debug_d3dstate()` as it is applied |
| `MGS2_GLES_CONV=0` | disable the 16-bit / X-channel texture converters |
| `MGS2_GLES_CORE=1` | classify the GLES context as core profile (off: no measured benefit) |
| `MGS2_GLES_ES2COMPAT=1` | force `ARB_ES2_COMPATIBILITY` (off: measured harmful, see §4) |
| `MGS2_GLES_FBO_READBACK=1` | production default; use GLES-safe FBO `glReadPixels()` capability probing for codec targets (`=0` is the A/B) |
| `MGS2_SKIP_CODEC_BLACK_QUAD=1` | production default; skip the precisely identified codec composite black quad (`=0` is the A/B) |
| `MGS2_SKIP_SRCALPHA_INVSRCALPHA=1` | diagnostic only: suppress normal alpha-blended draws to localise the white-effect defect |

## 3. The fix that changed everything

`dlls/opengl32/unix_wgl.c`, `parse_gl_version()`:

```c
*major = atoi( ptr );          /* "OpenGL ES 3.2 ..." -> 0 */
if (*major <= 0)
    ERR( "Invalid OpenGL major version %d.\n", *major );
```

and its caller:

```c
if (!ctx->major_version) ctx->major_version = 1;   /* falls back to GL 1.x */
```

A GLES driver reports `GL_VERSION` as `"OpenGL ES 3.2 ..."`. `atoi()` on a string that
starts with a letter returns 0, so **Wine concludes the context is OpenGL 1.x**, and the
entry-point gate then refuses everything whose registry requirement is `GL_VERSION_3_x`:

```c
if (ctx->major_version > major || (ctx->major_version == major
        && ctx->minor_version >= minor)) return TRUE;
```

Two lines fix it:

```c
if (!strncmp( ptr, "OpenGL ES-CM ", 13 )) ptr += 13;
else if (!strncmp( ptr, "OpenGL ES ", 10 )) ptr += 10;
```

Measured with the same probe before and after:

| entry point | before | after |
| --- | --- | --- |
| `glClearBufferfv` | `00000000` | **`79D0E840`** |
| `glClearBufferfi` | `00000000` | **`79D0E730`** |
| `glBlendEquation` | `00000000` | **`79D0B490`** |
| `glBlendColor` | `00000000` | **`79D0B140`** |

**This was found by outside review, not by me**, and it corrected a wrong conclusion I had
committed to: I had localised the refusal to `win32u` — whose source is lost and which
cannot be rebuilt — and written the problem off as structurally blocked. The refusal is
actually in the Unix side of **opengl32**, and *that* builds from the tree we have
(`dlls/opengl32/opengl32.so`, in the same `build-wine-unix32` that already produced
`win32u.so` and `winewayland.so`).

Consequences: two workarounds I had written became unnecessary. Both remain as fallbacks
and only engage if the patched opengl32 is not mounted.

### Still refused, and why that is expected

`glClearDepthf`, `glDepthRangef`, `glTexStorage2D`, `glInvalidateFramebuffer` remain NULL.
They are core in GLES 2.0/3.0 but only reached **desktop** GL at 4.1/4.2, so a correctly
parsed 3.2 still fails their requirement. Closing that needs GLES-core command membership
added to the gate — generate the table from Khronos `gl.xml` rather than by hand.

## 3b. The CrossOver Android capability list — the largest single improvement

CodeWeavers shipped Direct3D over GLES in CrossOver Android 17 (Wine 2.8 base). With that
source tree available, two things became clear immediately.

**They solved the version problem the same way.** Their `wined3d_parse_gl_version()`:

```c
static const char gles_header[] = "OpenGL ES ";
if (!memcmp(ptr, gles_header, sizeof(gles_header) - 1))
{
    *gles = TRUE;
    ptr += sizeof(gles_header) - 1;
}
major = atoi(ptr);
```

— the same prefix skip this project arrived at independently in `opengl32`'s parser.

**And they set capability bits from the GLES version, not desktop thresholds.** A block
enables what GLES 2.0/3.0/3.1/3.2 genuinely provide, and a second block *removes* what a
GLES context must never be credited with. That removal list was ported into Wine 11
(`adapter_gl.c`, 20 flags). Three of its entries had already been rediscovered the hard way
here, one symptom at a time, which is good evidence for trusting the rest:

| flag | what it had caused |
| --- | --- |
| `ARB_PROVOKING_VERTEX` | flat shading silently used GL's last-vertex convention; D3D specifies first |
| `EXT_DRAW_BUFFERS2` | selected a `STATE_BLEND` handler needing NULL `glEnablei`/`glColorMaski` |
| `EXT_TEXTURE_SRGB_DECODE` | made `query_internal_format()` substitute the sRGB internal format |
| `ARB_VERTEX_ARRAY_BGRA` | already handled |

Also removed and not yet encountered as symptoms: `ARB_TEXTURE_STORAGE`,
`EXT_STENCIL_TWO_SIDE`, `ARB_DRAW_ELEMENTS_BASE_VERTEX`, `ARB_TEXTURE_BORDER_CLAMP`,
`ARB_MAP_BUFFER_ALIGNMENT`, `ARB_POINT_SPRITE`, `ARB_SHADER_BIT_ENCODING`,
`ARB_SHADER_TEXTURE_LOD`, `ARB_DEBUG_OUTPUT`, `ARB_VERTEX_PROGRAM`, `ARB_FRAGMENT_PROGRAM`,
the RGTC/3DC compression formats and `EXT_TEXTURE_SNORM`.

`ARB_UNIFORM_BUFFER_OBJECT` is deliberately **not** removed: CrossOver drops it, but Wine 11
depends on it more than Wine 2.8 did and this title is fixed-function.

**Measured effect.** `B8G8R8A8_UNORM` internal format changed from `0x8c43`
(`GL_SRGB8_ALPHA8`) to `0x8058` (`GL_RGBA8`) — textures are no longer stored as sRGB and
decoded on sample. User-verified outcome: menus render correctly, the white rain is gone,
and cutscenes appear that had never been visible before. Shipped as
`wined3d_dbg150_cxcaps.dll` and promoted to default after a clean 60-step run.

Worth recording honestly: **this exceeded the prediction.** The rain was expected to need
the separate provoking-vertex repair, since clearing `ARB_PROVOKING_VERTEX` only stops
wined3d *believing* it can select first-vertex convention — the call was already skipped on
a NULL pointer. The sRGB storage change is the likelier mechanism. CrossOver has the same
latent flat-shading gap and merely warns about it, so the provoking-vertex analysis in §6a
remains valid and unaddressed upstream.

## 4. Every other fix, with its evidence

| defect | evidence | fix |
| --- | --- | --- |
| `glBindFragDataLocation` called unguarded while linking every program; absent in GLES | crash on first draw | skip on `is_gles` |
| `glDepthRange` in the viewport handler | SEH trace, `ip=00000000` | use `glDepthRangef` if present, else skip — GLES defaults to `[0,1]`, same as D3D |
| **`glBlendEquation` NULL**, called in the *common* case (`op == op_alpha`) | state trace ended on `STATE_BLEND`; pointer dump showed it NULL while `glBlendEquationSeparate` resolved | pass the same equation twice through `glBlendEquationSeparate` |
| `B4G4R4A4_UNORM` (a 1024×512 atlas) never uploaded | manifest: `internal=GL_SRGB8_ALPHA8` with `type=GL_UNSIGNED_SHORT_4_4_4_4` — illegal in GLES | pin `internal`/`srgb_internal` *after* `query_internal_format()` |
| `EXT_DRAW_BUFFERS2` wrongly credited (desktop 3.0) → `STATE_BLEND` picked a handler needing NULL `glEnablei`/`glColorMaski` | capability manifest | clear the flag on GLES |
| `glGetTexImage` (absent in GLES) reachable from two startup probes and the texture-download path | NULL-function list | guard all four sites |
| depth clear could not be set at all | 11 spellings probed, all NULL | emulate with a full-screen depth-write quad (now superseded by the opengl32 fix) |
| prefix had **zero** ACM codecs and no `wavemapper` | `Drivers32` empty in both registry views | `scripts/reg_acm.py` writes the standard entries |
| `/storage` 100% full — 1.4 GB of it my own debug builds | user hit *"there is a problem with your disc"* | removed 70 files / 1326 MB; keep only what `launch.sh` references |

### The localisation loop that works

This is the reusable part. Cross-referencing a 630-name NULL list against the wined3d
sources produced 79 candidates and no answer. What works instead:

1. log `debug_d3dstate(state_id)` at both `state_table[...].apply()` sites in
   `context_gl.c`;
2. run to the crash — the last `STATE ...` line names the handler;
3. dump that handler's entry points via `MGS2_MANIFEST`;
4. the NULL one is the bug.

One iteration turned "crashes somewhere in 3D" into "`glBlendEquation` is NULL".

**The tracer must keep its log handle open and `fflush` per line.** The original
`fopen`/`fclose`-per-line form costs ~13 file opens per draw call and slowed the game so
much it never reached the crash — 182 515 lines of healthy draws and nothing else.

## 5. Disproven — do not re-investigate

Each of these was a plausible hypothesis, tested with a controlled A/B, and is wrong:

* **"The working binary `dbg42` contains source we lost."** A full semantic diff — data
  symbols with pointers normalised to `symbol+offset`, 4 193 function bodies, per-function
  call sets — shows the tree and the binary are equivalent. The only difference was a
  cosmetic refactor emitting byte-identical GLSL. Rebuilds looked worse solely because of
  the tracer described above. Tools: `scripts/pedata.py`, `pefunc.py`, `petab.py`.
* **GLES classified as a legacy context.** Forcing core-profile changes nothing; the
  capability dump confirmed the flag actually flipped.
* **Promoting `ARB_ES2_COMPATIBILITY`.** Makes it *worse* — it switches the depth clear
  from a working `glClearDepth` to a then-NULL `glClearDepthf`, moving the crash earlier.
  Correct only once the entry points resolve.
* **`L8_UNORM` / luminance formats.** The selected row is already `GL_R8`+`GL_RED` with an
  `XXX1` fixup; there is exactly **one** L8 texture and it is **16×16**, not a font atlas.
  I shipped a 4-byte patch for this — it was a **no-op on a row that is never selected**.
* **The depth clear as the cause of the crash.** Real defect, fixed, but not the crash.
* **DXT/S3TC, X1R5G5B5, X4R4G4B4.** The game creates none — measured, not assumed.
* **Fonts / text rendering.** Text is fine: the legal disclaimer, every menu label and the
  codec subtitles all render correctly.
* **The fault address `79d32476`.** A shared opengl32/win32u thunk; identifies nothing.

## 6. Still broken

### 6a. White saturation noise on gameplay surfaces

Measured on live Tanker captures: the defect is pure white `(255,255,255)` in irregular
runs over floor/splash surfaces. It is **not** now an unexamined texture-format lead.
The following A/Bs are conclusive:

| test | result | conclusion |
| --- | --- | --- |
| skip line/rain-style primitives | defect remains | not the line-effect path |
| skip `SRC_ALPHA / ONE` additive draws | defect remains | not additive blending |
| skip `SRC_ALPHA / INV_SRC_ALPHA` normal draws | defect completely disappears while scene geometry remains | causal draw class identified |
| GPU readback of both 512×1024 gameplay atlases | alpha bytes exactly equal CPU upload bytes | BGRA/RGBA upload and texture alpha are correct |
| mapped late VBOs | visible triangles have expected alpha and raw 0..4096-style UVs | vertex alpha and source UV data are correct |
| actual GL state at the draw | `GL_SRC_ALPHA/GL_ONE_MINUS_SRC_ALPHA`, `GL_FUNC_ADD`, clamp, `COUNT2`, UV matrix `1/4096`, normalised `GL_UNSIGNED_BYTE` diffuse and float UV attributes | fixed-function state translation is correct |

The A/B used `MGS2_SKIP_SRCALPHA_INVSRCALPHA=1`; its test DLL is
`wined3d_dbg125_skip_normal_alpha.dll` (`f06c606b…`). The unchanged control and clean
result are `logs/effect-research-20260802/play-effect-all-late/c60.png` and
`play-effect-skip-normal/c60.png`. The complete state-capture build is
`wined3d_dbg135_gpu_state_viewport.dll` (`b698fd05…`) and produced an alive 62-confirm
run with zero page faults.

This rules out changing texture formats, UV scaling, or alpha factors by eye.

#### The shader arithmetic is exonerated — measured, not argued

Outside review proposed a single discriminating experiment: encode the *effective* alpha
operands and the stage result into the fragment colour and read them off a screenshot.
Implemented as `MGS2_ALPHA_PROBE=1` in `shader_glsl_ffp_fragment_op()` —
`R = effective alpha operand 1`, `G = operand 2`, `B = the alpha the stage computed`,
`A` forced to 1 so the diagnostic survives the normal blend equation and no blend state has
to be disturbed for the capture. Test build `wined3d_dbg140_alphaprobe.dll` (`20cc3240…`).

Result from a live Tanker frame, checking `B == clamp(2 * R * G, 0, 1)` per pixel:

```
0 mismatches / 34 240 sampled pixels
R=1.000 G=0.251 -> B=0.502   OK
R=0.671 G=0.502 -> B=0.675   OK
R=0.898 G=0.502 -> B=0.902   OK
```

The fractional cases matter: they prove the formula is genuinely being evaluated, not
trivially saturating. So **the generated GLSL is correct and Mali executes it correctly** —
both the "whole-vector `op_equal` miscompile" and the "Wine `MODULATE2X` semantics bug"
hypotheses are closed.

91.7% of pixels have both operands already at 1.0, which points at the third branch of the
decision tree: the inputs saturate before the stage runs.

**A trap worth recording:** that percentage on its own proves nothing, because opaque
geometry *legitimately* has alpha 1, and a whole-frame probe cannot tell a correct 1 from
an incorrect one. The measurement only becomes evidence when restricted to the draw class
already implicated. `MGS2_ONLY_SRCALPHA_INVSRCALPHA=1` (the inverse of the existing skip
switch) suppresses every other draw so the probe reports operands for exactly those calls;
test build `wined3d_dbg141_onlynormal.dll` (`7a9dc07f…`).

Sampling was then measured too and is also correct: bound texture `B8G8R8A8_UNORM`
1024×1024, `levels=1`, identity `color_fixup`, sampler `min=LINEAR_MIPMAP_NEAREST`,
`mag=LINEAR`, `base=0`, `max=0` (so the texture is *complete*), identity swizzle. A colour
probe (`MGS2_TEX_RGB_PROBE=1`) shows the sampler returning white over 97.2% of the drawn
area — which for a rain sheet is normal asset design, translucency coming from vertex alpha.

#### Cause found: the provoking-vertex convention

Named by outside review, confirmed by measurement:

```
glProvokingVertex     = 00000000   (no such entry point in GLES)
ARB_PROVOKING_VERTEX  = 1          (wrongly credited by the desktop-3.2 promotion)
EXT_PROVOKING_VERTEX  = 0
emulated_flatshading  = 1          (flat varyings are emitted)
```

D3D flat shading takes the face colour from the **first** vertex. Wine emulates it with
`flat` varyings and asks GL for `GL_FIRST_VERTEX_CONVENTION` — but that call is guarded on
`glProvokingVertex` being non-NULL, and in GLES it is NULL. Neither branch runs, the
convention stays at GL's default **last** vertex, and every particle triangle takes its
alpha from the wrong corner. That reconciles every earlier measurement: correct texels,
correct UVs, correct vertex bytes, correct blend state, correct arithmetic — wrong vertex.

A/B with `MGS2_NO_FLATSHADING=1` (a diagnostic that forces smooth interpolation, **not** a
fix — it discards genuine D3D flat shading):

| | saturated white | near-white |
| --- | --- | --- |
| control, flat shading on | **31.97%** | 33.90% |
| forced Gouraud | **5.53%** | 6.38% |

The scene becomes readable — deck, winches, Snake, HUD — with a residual white cluster, so
this accounts for most but not all of the defect.

**The proper fix, and why it is not two lines.** libmali advertises 107 extensions and none
is a provoking-vertex selector, so the driver cannot be asked for first-vertex convention.
Primitives must be reordered instead: rotate each triangle `[a,b,c] → [b,c,a]`, which
preserves winding while moving D3D's first vertex into GL's provoking position; strips and
fans expand to lists first. Gate on
`flat_shading && !ARB_PROVOKING_VERTEX && !EXT_PROVOKING_VERTEX`.

**Third instance of one root cause.** `ARB_ES2_COMPATIBILITY` absent where needed,
`EXT_DRAW_BUFFERS2` granted where harmful, `ARB_PROVOKING_VERTEX` granted with no function
behind it — all from Wine scoring a GLES context against desktop GL version thresholds.
Auditing every capability bit against what libmali actually provides would likely be
cheaper than finding these one symptom at a time. The next discriminating experiment is a
desktop-OpenGL reference of the *same* executable, V's/d3d8 proxy, assets, and 640×480 / 512
configuration. If it is clean, compare its final shader/output against GLES; if it contains
the same splashes, treat them as port/configuration behaviour instead of suppressing them.

That reference has been staged at `recovered-session/local-reference/game`: it has the
device-matching executable hash `29759e6f…` and the copied device d3d8 proxy hash
`ab6bf7a9…`. This detail matters: the original local d3d8 proxy was a different binary
(`486f86cf…`). It is a diagnostic control, never a replacement for RG353VS testing.

An initial host attempt on 2026-08-02 initialized its isolated Wine prefix in
`recovered-session/local-reference/wineprefix` and did create the D3D device. It is **not**
a valid visual reference: the host Wine's experimental WoW64/XWayland path fed back between
the game-requested 640×480 and a 4096×2560 compositor size, then page-faulted. The process
was stopped and no screenshot/result from it is evidence. A future desktop retry must use a
windowed staged configuration (without changing the installed game); console runs remain the
authoritative automated tests.

### 6b. Codec portraits

The missing faces have a confirmed, narrow test fix. The fallback format-capability probe
used desktop-only `glGetTexImage`, which is unavailable in GLES. Consequently the codec
off-screen `B8G8R8X8` face render target was under-advertised. With
`MGS2_GLES_FBO_READBACK=1`, the probe reads an interior pixel from the already-bound FBO
using core GLES `glReadPixels(GL_RGBA, GL_UNSIGNED_BYTE)` instead; the relevant capability
record changes from `0xb372` to `0xb373` and blend support becomes available.

Independently, timeline/readback probes showed that one full black composite quad runs after
the face target has been populated and destroys the visible result. With both
`MGS2_GLES_FBO_READBACK=1` and `MGS2_SKIP_CODEC_BLACK_QUAD=1`, portraits render correctly
and animate throughout the codec conversation. The exact test artifact is
`wined3d_dbg123_gles_fbo_readback.dll` (`23631920…`). It was promoted on 2026-08-02 only
after the fresh `codec123-promotion` automated run: 70 confirms, full gameplay frames at
`c40`–`c70`, process alive, and zero page faults. The visual codec control at `c30.png`
shows both portraits. The production launcher was then changed only to default this DLL and
the two switches to `1`, with its old version saved on the device as
`launch.sh.dbg86-20260802.bak`. A second exact-default run,
`codec123-production-default`, also reached `c70` (275,733 bytes), stayed alive, and
reported zero page faults. Its preserved output is under
`recovered-session/logs/codec-production-default-20260802/`. Set either switch to `0` for
a reversible A/B.

### 6c. Horizontal striping on animated backdrops

Not corrupted data — a **uniform fill**: affected rows are exactly `(0, 16, 0)` across all
640 pixels, strict period of 4 (two rows written, two filled), the two filled rows
byte-identical. Only on screens with an animated backdrop; static screens are pixel
perfect. The texture converters make no difference either way.

The game's PS2 source renders in FIELD mode
(`sceGsResetGraph(0, SCE_GS_INTERLACE, GS_DISP_MODE, SCE_GS_FIELD)`).

Recommended test (from the outside review): clear the backdrop's intermediate render
target to magenta first. If the striped rows come out magenta they are never written —
look at viewport/scissor/coverage. If they stay `(0,16,0)` something writes the fill —
look for a clear or blit.

### 6d. Cutscenes and the title backdrop

The shipping executable has PSS movie playback **patched out**: file offset `0x17D82F`,
`7d 1d` → `90 90`, forcing `NewMpegPssMovieStr`/`GetResources` down its resource-error
path. Confirmed against the MGS2 source in `mgs_source/` — the field at `+0x188` is
`work->top_pos`, and `n_title.c` registers the movie actor, so the title backdrop is a
movie too.

Reverting those two bytes is **not** sufficient — tested, nothing plays. Playback goes
through **DirectShow via COM** (`FilterGraph` ×9, `CoCreateInstance`,
`AMovieSetupRegisterFilter`, `rdr_movie.c`; no static `quartz` import). Upstream has this
unresolved (VFansss/mgs2-v-s-fix #88).

Assets are intact — `movie.dat` 305 MB, `demo.dat` 1.48 GB, all read to their final block,
ext4, no large-offset problem. `quartz.dll`, `devenum.dll`, `winegstreamer.dll` and
GStreamer with `libgstlibav` are all present.

Next step: build a small 32-bit graph inspector that adds the game's source filter,
enumerates its output pins and logs every `AM_MEDIA_TYPE`, then calls `Render()` and logs
the first failing `Connect` HRESULT. MPEG-1 payload and MPEG-2 elementary video need
different answers. A movies-enabled executable is on the device as
`mgs2_sse_rg353vs_movies.exe`, selectable with `MGS2_EXE`.

## 7. Build and test

```sh
# WineD3D (PE, MinGW)
export PATH=recovered-session/mingw/bin:$PATH
cd recovered-session/build-wine-i386
make -j8 dlls/wined3d/i386-windows/wined3d.dll

# Unix opengl32 / win32u / winewayland (i386 Unix)
cd recovered-session && source scripts/build-env-i386.sh
cd build-wine-unix32
make dlls/opengl32/opengl32.so
```

Test harnesses in `recovered-session/scripts/`, all state-anchored rather than
time-anchored:

| script | purpose |
| --- | --- |
| `drive.sh` | launch, drive the menus to the legal disclaimer, capture each step |
| `scene.sh` | same, then push past the disclaimer into the first stage |
| `play.sh` | push all the way through the codec conversations into gameplay |
| `send_key.py` | synthetic keyboard (`--hold`, `--gap`), focuses the window first |
| `reg_acm.py` | register the ACM codecs in the prefix |
| `pedata.py` / `pefunc.py` / `petab.py` | semantic diff of two PE builds |

## 8. Measurement rules learned the hard way

Each of these produced a wrong conclusion before it was understood:

* **Frame size is not a quality metric.** Animated backdrops mean a screenshot's size
  depends on *when* it was taken; the same build measured 13 414 and 104 962 bytes.
  Anchor on a deterministic screen — the legal disclaimer is byte-identical across runs.
* **Time-based test sequences are invalid.** Identical sleeps put two runs on different
  screens, and I compared their texture censuses as though they meant the same thing.
* **`eglGetProcAddress` returning non-NULL does not mean WineD3D can call it.** Three
  separate wrong conclusions came from conflating those layers.
* **`gl_ops.gl.p_*` are never NULL** — they are opengl32 thunks. The NULL that kills the
  process is one level below. Guarding on the pointer does not work; guard on `is_gles`
  or on the *ext* pointer.
* **A `sed` range over a repeated pattern splices unrelated file regions.** I "found" a
  fog bug that did not exist this way. Read the file before editing on the strength of a
  grep.
* **`pkill -f` matches the invoking command line**, including environment assignments in
  an `ssh` command — the `[b]racket` trick does not save you.
* **Verify a fix's premise, not just its outcome.** I skipped the depth-clear call
  believing games clear to 1.0. MGS2 clears to **0.0**, 3 592 times in one run; the buffer
  stayed at 1.0, the depth test rejected everything, and the screen went flat grey. One
  `FIXME` counter would have caught it before shipping — and did, eventually.
* **Delete debug builds as they are superseded.** 25 MB each, on a device that ships
  nearly full; mine filled the disk and caused a user-visible error.

## 9. Next steps, in order

1. Keep RG353VS as the test target: run the automated `play.sh` baseline after each proposed
   WineD3D change and do not promote a result based only on the desktop host.
2. When an additional control is needed, retry the already-staged desktop reference in a
   windowed staged configuration, then capture the same Tanker splash scene before changing
   any alpha/shader code.
3. If the reference is clean, instrument the GLES fragment result only where it diverges;
   implement a narrow test fix and compare it with the automated RG353VS A/B harness.
4. Preserve the codec promotion with the same 70-confirm test after any WineD3D or launcher
   change; do not include the alpha-diagnostic skip in production.
5. Add GLES-core command membership to opengl32's entry-point gate, generated from
   `gl.xml`; that should recover `glClearDepthf`, `glDepthRangef`, `glTexStorage2D`.
6. Sentinel-colour test for the backdrop striping, then DirectShow graph inspector for
   movies/title backdrop.
7. Re-measure frame rate — all the performance work predates these fixes.

## 10. Performance — where the time actually goes

Frame rate is now the main defect. This section records what was measured, because almost
every intuition about it turned out to be wrong.

### 10a. It is not the GPU, and that is settled

| experiment | result |
| --- | --- |
| normal gameplay | 15.1, 15.2, 23.1 fps |
| **every draw and every state application skipped** (`MGS2_SKIP_ALL_DRAWS`) | 13.1, 18.5, 21.0, 23.4 fps |

Deleting the entire rendering path does not change the frame rate. A `perf` profile of 20 s
of live gameplay says the same thing:

| where CPU time goes | share |
| --- | --- |
| kernel, overwhelmingly the scheduler | **39%** |
| box86 JIT-translated code | 33% |
| box86 runtime (wrapper trampolines, `DBGetBlock`) | 7% |
| **libmali — the actual GPU driver** | **4.5%** |

By thread: game main thread 63%, `wined3d_cs` 21%, DirectMusic synth 5%, DirectSound mixer 3%.

**Presentation, zero-copy, shader and texture-format optimisation are therefore all dead
ends.** The GPU is idle. The whole 32-bit stack — game, wined3d, opengl32, win32u, ntdll —
is emulated x86 under box86; only libmali and the kernel are native.

### 10b. A third of a million syscalls a second, from one function

`NtYieldExecution` (`dlls/ntdll/unix/sync.c`) is three syscalls, not one: `getrusage`,
`sched_yield`, `getrusage`. The pair exists only to choose between `STATUS_SUCCESS` and
`STATUS_NO_YIELD_PERFORMED`, and that distinction has exactly one consumer tree-wide —
`SwitchToThread`. In the profile the leaf under `getrusage` is `__pi_memset_generic`: the
kernel zeroing `struct rusage`, twice per yield.

The caller is Wine's own message pump. `NtUserPeekMessage` yields on every empty queue poll
(`dlls/win32u/message.c`), a behaviour added in 2005 "for nicer behavior" — Wine policy, not
Windows semantics. MGS2's main loop polls thousands of times per rendered frame. Measured
directly: **~130 000 calls/second ⇒ ~390 000 syscalls/second**, all through the 32-bit
compat entry.

An earlier estimate of ~1 000/s, derived from involuntary context-switch counters, was wrong
by 130×. Most `sched_yield` calls return without switching to anything, so they never appear
in those counters; the cost is syscall entry/exit and the memsets, not rescheduling.

### 10c. The yield experiments — currently contradictory, conclusion withdrawn

> **Withdrawn 2026-08-02.** The "cheap yield nearly doubles the frame rate" result below
> was obtained entirely inside a *rebuilt* ntdll.so. A later run against the **shipping**
> ntdll, with the frequency pinned and the sampled scene verified byte-identical between
> configurations, inverted it:
>
> | build | mean fps | clock |
> | --- | --- | --- |
> | shipping ntdll, untouched | **12.18** | 1104 MHz pinned |
> | shipping ntdll, five-byte patch removing the `getrusage` pair | **8.07** | 1104 MHz pinned |
>
> Both sampled the same codec screen — the screenshots match — so scene variance is ruled
> out. The two experiments disagree, and the variable they do not share is the ntdll build
> itself. Since two independently rebuilt win32u.so from the same tree both hang the game
> at `eglInitialize` while the shipping binary plays fine, the tree demonstrably does not
> reproduce this device's Wine, and a rebuilt ntdll cannot be assumed equivalent either.
>
> **Nothing about the yield change should be promoted until this is resolved.** What
> survives unchallenged: the profile in §10a, the cost of `NtYieldExecution` and the
> ~130 000 calls/second in §10b, and that the GPU is not the bottleneck.
>
> A further methodological problem found at the same time: the harness samples during a
> **codec conversation**, not gameplay. Fine for comparing configurations against each
> other, useless as a measure of how the game actually plays. Unpinned, the game renders
> 20–24.5 fps.

120 s gameplay windows, cooled to 70 °C before each run, frequency ladder pinned:

| mode | mean fps | yield rate | clock in window |
| --- | --- | --- | --- |
| `full` — stock, three syscalls | 6.21 | 95–106k/s | 816 MHz |
| **`fast` — `sched_yield` only** | **11.82** | 211–267k/s | 816 → 1104 MHz |
| `none` — no syscall at all | 6.29 | 297–442k/s | mean 972 MHz |

**Removing the yield entirely buys nothing.** `none` eliminates all 390 000 syscalls and
lands on top of stock. The main thread then never gives the CPU up, and `wined3d_cs` plus
the wineserver round-trips starve by as much as the main thread gains. Making the yield
*cheap* nearly doubles the frame rate; making it *disappear* does not.

Caveat on the clock: the kernel's thermal governor throttles underneath the launcher's cap,
so the three windows did not run at identical frequencies. The spread is at most 35% and the
effect is 90%, so the direction is not in doubt, but an interleaved repeat with per-window
mean-clock recording is the honest confirmation.

Consequence for the production fix: **do not remove the yield from the empty-`PeekMessage`
path.** win32u is itself a Unix library, so it can call `sched_yield()` directly and skip
`NtYieldExecution` for this one call site, leaving that function's semantics intact
everywhere else. That is what `MGS2_EMPTY_PEEK_YIELD=fast` does.

### 10cc. The busy loop, located exactly

A caller histogram built into a rebuilt PE `user32` (`MGS2_PEEK_STATS=1`) names a single
address. Over five-second windows, in gameplay:

```
MGS2 peek caller 00401176: 280433 calls, 280433 empty (100%), longest empty run 4059196
MGS2 peek caller 00401176: 281066 calls, 281066 empty (100%), longest empty run 4340262
```

~56 000 calls/second, essentially all of them empty, and on the codec screen the
consecutive-empty run never resets at all — it climbed past four million. In live gameplay
it does reset occasionally, so real messages do arrive there.

`0x401176` disassembles to the main loop, right after `WinMain`:

```
401167:  push $0 ×4 ; push $0xa14a4c    ; &msg
401174:  call *%esi                     ; PeekMessage(&msg, NULL, 0, 0, PM_NOREMOVE)
401176:  test %eax,%eax                 ; <- the recorded return address
401178:  je   0x40119b                  ; queue empty ->
40117a:    ... GetMessage / Translate / Dispatch
40119b:  call 0x8a41d0                  ; ONE GAME ITERATION
4011a0:  push $0 ; call *0x95c214
4011a8:  cmpl $0x12,0xa14a50            ; run state
4011af:  jne  0x401167                  ; round again
```

**The empty poll is not idle work** — each one is followed by one call of `0x8a41d0`. The
game runs its main iteration ~56 000 times a second to produce ~20 rendered frames: about
3 500 iterations per frame. The frame limiter is therefore *inside* `0x8a41d0`, which
returns "not yet" almost every time, and the loop around it is the busy-wait. This matches
MGSHDFix's account of the same engine, where the extended fix hooks `ActorWait` and sleeps
until just short of the deadline; `0x8a41d0` is this build's equivalent entry point.

The remedy under test is a real wait rather than a cheaper yield: after N consecutive empty
polls **from this caller only**, `NtUserMsgWaitForMultipleObjectsEx(0, NULL, 1 ms,
QS_ALLINPUT, MWMO_INPUTAVAILABLE)`. That removes the poll, the window-surface flush, both
thunk-lock callbacks and the translated loop body, not merely the syscalls inside the yield.

It lives in the **PE** `user32`, deliberately: PE rebuilds from this tree work — the shipping
`wined3d_dbg150_cxcaps.dll` is one — while Unix `.so` rebuilds do not.

First result, 120 s windows, clock pinned at 1104 MHz with no variation in either run:

| configuration | mean fps | polls/second | mean temperature |
| --- | --- | --- | --- |
| instrumented, no wait | 7.31 | ~56 000 | 73.1 °C |
| **wait 1 ms after every empty poll** | **7.89** (+7.9%) | **~560** | 73.9 °C |

A hundredfold cut in polling for an 8% frame gain. The gain is small because the polling is
not free work being deleted — each poll carries a game iteration — so throttling the loop
throttles the game too. Input is unaffected: the empty fraction falls from 100% to 98-99%,
meaning the wait wakes on real messages rather than only on its timeout.

Pinning the clock, necessary to make the runs comparable, also hides the effect most likely
to matter in practice: 390 000 fewer syscalls a second should mean less heat and therefore a
higher sustained clock. That has to be confirmed unpinned, and this table does not measure
it.

### 10d. Thermal and clock

Governor `performance`. Observed 1416 MHz early in a session, 1104 MHz after sustained load,
and 816 MHz under the kernel's own throttling — against a ladder topping out at 1608 MHz and
a reported `cpuinfo_max_freq` of 1992 MHz that is not in the mainline RK3566 OPP table and
should not be treated as a safe sustained clock. Sequential benchmark runs measure
progressively slower silicon; the harness now cools to 70 °C between runs and records the
mean clock per window.

### 10e. Instrumentation

| variable | effect |
| --- | --- |
| `MGS2_SKIP_ALL_DRAWS=1` | return before state application and the draw |
| `MGS2_NTDLL_SO=ntdll_yield1.so` + `MGS2_YIELD=full\|fast\|none` | global yield cost |
| `MGS2_WIN32U_SO=win32u_peek1.so` + `MGS2_EMPTY_PEEK_YIELD=full\|fast\|none` | the local fix |
| `MGS2_EMPTY_PEEK_EVERY=N` | yield once per N empty polls, composable with the above |
| `MGS2_YIELD_STATS=1` / `MGS2_EMPTY_PEEK_STATS=1` | call rates |
| `MGS2_FREQ_STEPS=1104000` | pin the frequency ladder to one step |

`recovered-session/scripts/ab.sh` drives a run into gameplay and samples it;
`run_perf_matrix.sh` interleaves configurations round-robin so thermal drift is spread
across all of them instead of loaded onto whichever runs last.

### 10f. Measurement traps, all of which produced a confident wrong answer first

* **Profiled the wrong process.** `pgrep` returned `gptokeyb` ahead of the game; its 3% CPU
  was reported as the game's, briefly inverting the entire conclusion to "the game is idle
  and merely waiting".
* **A locally built `ntdll.so` makes `ps` show unprintable garbage instead of the exe name.**
  The harness identified the game by process name, so five runs were reported as "died
  before first frame" while the game was rendering normally. Match the command line — but
  not on a pattern `gptokeyb` also carries.
* **Two A/B loops ran concurrently.** `killall` removed the child scripts but not their
  parent shells, which marched on to the next mode; each run's cleanup unmounted the other's
  bind mounts, so the game silently ran on stock wined3d and win32u. The harness now takes a
  lock and reports how many overrides were mounted.
* **Thermal drift across sequential runs** measures each successive configuration on a
  slower CPU.
* **`WINEDEBUG=-all` silences the frame counter**, which is emitted on `err+waylanddrv`.

## 11. Audio — a single missing interface in Wine

The game was completely silent. The cause was one unimplemented `QueryInterface` branch.

MGS2 builds its sound through DirectMusic 8. It has no static import of `dmusic`/`dmime` —
the import table is `ADVAPI32, d3d8, DINPUT8, DSOUND, KERNEL32, MSACM32, ole32, OLEAUT32,
USER32, WINMM` — but the executable carries DirectMusic 8 COM error strings, so it uses the
API dynamically. Among them:

```
Can't create IID_IDirectMusicGraph8 object(%x)
IID_IDirectMusicAudioPath Refarence Error(%x)
IID_IDirectMusicGraph Refarence Error(%x)
IID_IDirectMusicTool8 Refarence Error(%x)
```

With `warn+dmime` the failure appears immediately at startup, twice:

```
warn:dmime:IDirectMusicAudioPathImpl_QueryInterface
     (08650BB8, IID_IDirectMusicGraph, 0195FDCC): not found
```

The game asks its AudioPath for the tool graph with a plain `QueryInterface`. Windows
supports that. Wine 11.0's `IDirectMusicAudioPathImpl_QueryInterface` accepts only
`IID_IDirectMusicAudioPath` and `IID_IUnknown`, so it returns `E_NOINTERFACE` — even though
the same object already owns a `pToolGraph` and `GetObjectInPath` will happily create and
hand out that very graph. The game takes the failure as fatal and never finishes setting up
audio.

The fix adds the missing branch in `dlls/dmime/audiopath.c`, creating the graph on demand
exactly as `GetObjectInPath` does. Built as a PE DLL and shipped as `dmime_graphqi.dll`
(`MGS2_DMIME_DLL` to A/B it).

Measured on the speaker sink monitor, same scene, same binaries otherwise:

| | samples | peak | non-zero |
| --- | --- | --- | --- |
| before | 1 447 936 | **0** | 0 |
| after | 1 428 992 | **3305** | 1 426 657 (99.8%) |

Audible to the user. Startup and frame rate are unaffected: 44 s to first frame, 15–24 fps.

### Why this took so long to find

Every measurement pointed at the output path, and the output path was healthy. Four
amplitude probes compiled into `dsound` showed signal passing from `Unlock` to the device
buffer without being zeroed — but at about one LSB, because the only thing writing was
dmsynth idling. The probe never saw a game buffer, because the game never created one. The
conclusion drawn at the time, "the application submits silence", was too strong: it should
have been "the one buffer we can see is nearly empty, and we have not established that the
game created any buffer at all".

Eleven other hypotheses were tested and killed on the way (§ in brief #9): assets, storage,
ACM codecs, hardware routing, PipeWire health, the ALSA device, DirectSound init, the 11 kHz
resampler, Wine's shared `DirectSoundDevice`, dmsynth starvation, and missing COM
registration. Two genuine but unrelated faults were fixed: the device's Pulse socket-path
mismatch (which had also silenced the EmulationStation menu) and dmsynth's 10 ms wake-up
period, backported from Wine 11.2.

Native DirectMusic from the DirectX redistributable — the documented `winetricks
directmusic` route — is **not** usable here: with the group enabled the game renders no
frames in 120 s. `quartz` from the same recipe is fine and stays enabled; it is also what
the port needs for movie playback.

### Harness lessons from the same session

Four conclusions were published and withdrawn, all because the test harness misidentified
things rather than because the port changed:

* `pgrep -f <exe>` matches `gptokeyb`, whose command line carries the executable name — a
  120 s descriptor poll was watching the wrong process entirely.
* `pgrep -f <exe>` also matches the diagnostic shell running it, because the pattern is in
  its own arguments — this produced a false "five instances are running".
* Two test scripts running concurrently kill each other's launches; the log then reads
  `Killed` with zero frames, which is indistinguishable from a hang.
* A hung game stays in `ps`, so liveness is not success; only a rendered frame is.

`recovered-session/scripts/mgslib.sh` now provides the single correct pid lookup (exact
`comm`), a shared lock, and frame-based success. Profile switching went from ~10 minutes to
~1 by replacing 27 `wine` invocations with one `regedit` import.

## 12. Audio, part two — the positional voices

With music and ambience working, one class of sound stayed silent: everything attached to a
character. Footsteps, punches, weapon handling — gone; seagulls, wind and music — fine. The
split is the whole clue, because it is not a volume problem, it is a routing problem.

MGS2 builds its sound sources as DirectMusic audio paths, and a single startup capture with
`WINEDEBUG=-all,fixme+dmime` shows exactly two kinds:

```
13 performance_CreateStandardAudioPath ->(6, 1, ...)     DMUS_APATH_DYNAMIC_3D, one channel
 1 performance_CreateStandardAudioPath ->(8, 21, ...)    DMUS_APATH_DYNAMIC_STEREO, 21 channels
```

Thirteen one-channel positional voices, and one wide stereo path. Each of the thirteen then
asks its path for three things, and the counts line up with nothing left over:

| stage | interface | calls | before the fix |
| --- | --- | --- | --- |
| `DMUS_PATH_BUFFER` (`0x6000`) | `IID_IDirectSoundBuffer8` | 14 | served |
| `DMUS_PATH_PORT` (`0x4000`) | `IID_IDirectMusicPort` | 13 | **`E_INVALIDARG`** |
| `DMUS_PATH_PRIMARY_BUFFER` (`0x8000`) | `IID_IDirectSound3DListener` | 1 | served |

`GetObjectInPath` had no `case DMUS_PATH_PORT` at all, so all thirteen fell through to the
default and got `E_INVALIDARG`. Thirteen failures, thirteen positional voices, and the one
path that never asks for a port is the one we could hear.

The port was never missing. `perf_dmport_create` builds it, hands it to the channel blocks,
then drops its own reference and returns nothing, so the audio path that was constructed
around that port had no way to name it again.

The fix keeps the reference:

* `perf_dmport_create` gained an optional `IDirectMusicPort **ret_port`; when supplied, the
  caller takes the reference instead of it being released.
* Both path constructors — `performance_CreateAudioPath` and
  `performance_CreateStandardAudioPath` — store it via a new `set_audiopath_port`, and
  release it in the audio path destructor. Their buffer-failure paths release it too.
* `GetObjectInPath` answers `DMUS_PATH_PORT` for `IID_IDirectMusicPort` and `IID_IUnknown`.

Shipping as `dmime_port.dll`, default in `launch.sh` as of 2026-08-03. It supersedes
`dmime_graphqi.dll` and contains that fix as well — same tree, both patches.

### A stub that was lying

`GetObjectInPath` opened with an unconditional `FIXME(...): stub`, printed before the switch.
That is why the first census was misread: thirteen "stub" lines for the port looked identical
to fourteen "stub" lines for the buffer, which were being served correctly all along. The
`FIXME` now fires only on the fallback path and names the stage and interface, so the census
reports what is genuinely unimplemented:

```
=== requests by stage ===   13 x 16384   14 x 24576   1 x 32768
=== unhandled ===           (none)
```

That is the mechanism confirmed. Whether it restores the sounds is a listening test.

### It did not — the port was the wrong target

The sounds stayed silent. The counts lined up perfectly and the conclusion was still
wrong, which is worth remembering: thirteen failures against thirteen positional voices
is a correlation, not a mechanism, and I never established that the game treats the
failure as fatal.

What broke the theory came from the user in one sentence — the codec ring is silent
too, and a ringing codec is not a positional sound. The fix is kept because the gap was
real, but it is not this bug.

A second theory died the same way. `performance_tool_ProcessPMsg` drops
`DMUS_PMSGT_WAVE` into its `default:` case, so Wine plays no DirectMusic wave segments
at all — a genuine gap. A full gameplay capture produced zero messages of that type.
MGS2 does not use them.

What the measurements did establish is the actual architecture, in §12a.

### 12a. How MGS2 really emits audio

**It mixes its own sound and streams the result.** One startup: 16 `Play` calls against
51900 `Unlock` calls. DirectSound is a pipe, not a mixer.

The 62 buffers created at startup split three ways: 19 belong to the game (15 × 32576
bytes, 4 × 65152), 14 are dmime's audio path buffers, and 14 are dmsynth sinks
(176400 bytes, 22050 Hz stereo). A per-buffer write census — `MGS2_DSOUND_PROBE=2` in
`dsound_bufcensus.dll` — shows that at the menu the game writes into exactly **one** of
its own buffers, 44100 Hz stereo, peak 0.28. That is the music. The fourteen synth
sinks are written continuously at peak 0.00003, which is silence.

Two defects fall out of this that are not yet fixed:

* `CreateStandardAudioPath` sizes every path buffer with `DSBSIZE_MIN`, which is **4
  bytes**, and hardcodes 44000 Hz mono. The game asks for and caches all fourteen.
* `perf_dmport_create` calls `SetDirectSound(port, dsound, NULL)`, so each port's synth
  renders into its own sink instead of the path's buffer — the path's volume, pan and
  3D apply to nothing, and 14 × 88 KB/s of silence is mixed every period for nothing.

`IDirectMusicAudioPathImpl_SetVolume` is called 14 times at startup and **6612** times
during two and a half minutes of play. The game is doing per-voice volume work forty
times a second; the function is a stub.

Open question, and the subject of brief #11: whether the game writes effect PCM into
those 4-byte buffers. The gameplay census that would settle it is not captured yet.

### Instrumenting a device this slow

The first per-buffer census computed a true peak over every sample of every `Unlock`,
about 1000 calls a second. Under box86 that is emulated code and it made the game
unplayable — the probe cost more than what it measured. Capping the scan at 64 sampled
points per write fixed the arithmetic.

The rest of the slowdown was not the probe at all: background launches survive the ssh
session that starts them, so a diagnostic run and a run the user started from the menu
were playing at once. Launch one instance, verify by exact `comm`, and never leave a
traced session running.

### Still stubbed on these paths

`IDirectMusicAudioPathImpl_SetVolume` is a stub and is called 14 times, once per path. It
cannot be the cause of silence — ignoring it leaves the DirectSound buffer at its default
0 dB, which is too loud rather than too quiet — but it means the in-game effects volume
slider does nothing. Left alone deliberately, so the port change could be tested by itself.

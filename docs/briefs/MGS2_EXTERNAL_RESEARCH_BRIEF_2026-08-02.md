# External research brief — MGS2 Substance on Anbernic RG353VS

**Status:** 2026-08-02. This is a self-contained request for technical review. It is
deliberately shorter than `MGS2_PROJECT_STATE.md`; that document remains the full project
record. Please start from the evidence below rather than re-testing disproven theories.

## 1. What we need help fixing

The primary unresolved visual defect is a **white, opaque splash/noise effect during Tanker
gameplay**. It appears as high-contrast white fragments and rectangular masks around the
player/environment, instead of translucent water/spray-style effects. It is severe enough to
obscure play.

Two separate, lower-priority problems are also open:

1. **PSS cutscenes and the animated title/main-menu backdrop do not play.** The reported
   protagonist visual around the Start screen is not a codec portrait; it may be layered with
   the missing movie backdrop, but that exact composition still needs confirmation.
2. **Animated backdrops have strict 2-written/2-filled horizontal striping.** Static screens
   are pixel-perfect.

Codec portraits are **not open anymore**: a tested production fix restored them. Do not spend
research time on their former invisibility unless it bears directly on another bug.

## 2. Target and runtime stack

| item | value |
| --- | --- |
| device | Anbernic RG353VS: RK3566 / Mali-G52 (Bifrost) |
| OS/display | RockNix, sway/Wayland |
| GPU API | proprietary libmali, OpenGL ES 3.2; no usable 32-bit Vulkan path |
| game | licensed GOG Metal Gear Solid 2: Substance, Direct3D 8 PC port |
| translation | D3D8 → local V's Fix `d3d8.dll` / d3d8-to-9 proxy → D3D9 → WineD3D → GLES |
| Wine | Wine 11.0 source tree; PE WineD3D built for i686 with MinGW; game under box86/box64 old-WoW64 |
| game settings | 640×480, internal resolution 512, low quality/effects as configured by the original port |

The production launcher and source tree are local to this workspace:

```text
recovered-session/device-artifacts/launch.sh
recovered-session/wine-11.0/dlls/wined3d/
recovered-session/build-wine-i386/
mgs_source/MGS2-Source-main/
```

Current production package (SHA-256):

```text
ca147d1738874532794ec9e64ccdc074039e0b665cea47500fd476c92e49727f  launch.sh
23631920b4145190ae977b192606579769747ef1d0cb2191d248e31a05be0b4f  wined3d_dbg123_gles_fbo_readback.dll
b9a975657159abd72e37c9f7550a7a7684188ee39c7cd161edffdc3d713e19fe  opengl32_glesver1.so
6acdbbaeb8b88ba64fc160a1faf865ae304108705c38bccadaf6bc538f2be63a  win32u_glfuncs3.so
b09e66cce5d63b63301ecdd786529739fac1f71b89e0813540ba70c034a66ca1  winewayland_pbo1.so
```

The console has limited free storage (~391 MB at the last check), so test DLLs should be
reused and obsolete large artifacts should not be copied blindly.

## 3. Reproducible current result

The production launcher has passed an automated run through the menus, codec conversations,
and into Tanker gameplay:

```text
70 confirms
status: ALIVE
faults: 0
```

Useful captured frames:

| file | meaning |
| --- | --- |
| `recovered-session/logs/codec-production-default-20260802/c70.png` | current production gameplay; white alpha artefacts remain visible |
| `recovered-session/logs/codec-promotion-20260802/c30.png` | codec portraits visibly correct after the promoted fix |
| `recovered-session/logs/effect-research-20260802/play-effect-all-late/c60.png` | white-effect control before diagnostic suppression |
| `recovered-session/logs/effect-research-20260802/play-effect-skip-normal/c60.png` | same class of scene with all normal-alpha draws suppressed; artefacts disappear, but this is not shippable |

The test harness lives in `recovered-session/scripts/play.sh`. Its standard form is:

```sh
MGS2_PLAY_CONFIRMS=70 MGS2_PLAY_CAPTURE_EVERY=10 /tmp/play.sh <tag>
```

It deliberately kills a prior game process, launches the port, drives input through the
menus, captures every tenth confirmation, then cleans up. Use it only when restarting the
game is acceptable.

## 4. Primary issue: white effects — established facts

### Observable behaviour

The bad pixels are saturated white `(255,255,255)`, with irregular small fragments/areas,
especially over water/splash/floor effects. This is not a simple flipped texture, a fixed
block grid, or a global colour-space error.

### Causal A/B result

WineD3D has a test-only gate in `dlls/wined3d/context_gl.c`:

```text
MGS2_SKIP_SRCALPHA_INVSRCALPHA=1
```

Suppressing only D3D draws with `SRC_ALPHA / INV_SRC_ALPHA` **completely removes the white
artefacts while the opaque scene remains**. This identifies the causal draw class, but it
also removes legitimate translucent content, so it is not a valid fix.

Two negative controls:

| test | result |
| --- | --- |
| suppress line/rain-style primitives | artefacts remain |
| suppress `SRC_ALPHA / ONE` additive draws | artefacts remain |

Do **not** propose deploying the normal-alpha suppression, globally scaling alpha, or
discarding alpha draws. It trades a conspicuous error for missing real effects.

### Inputs and GL state already verified correct

The relevant late gameplay draws were instrumented without changing their normal rendering:

* GPU `glReadPixels()` of both 512×1024 gameplay alpha atlases exactly matches the CPU upload
  bytes. BGRA→RGBA upload and texture alpha are therefore not the cause.
  Instrumentation: `dlls/wined3d/texture_gl.c:1818` (`mgs_probe_gpu_alpha`).
* Mapped VBO data shows sensible visible-triangle alpha values and raw 0..4096-style UVs.
* The actual shader input attributes are: diffuse `size=4`, `GL_UNSIGNED_BYTE`,
  `normalized=GL_TRUE`; UV `size=2`, `GL_FLOAT`, not normalized.
* The actual uniform UV matrix is exactly `1/4096` on x and y.
* The actual GL state is `GL_SRC_ALPHA / GL_ONE_MINUS_SRC_ALPHA`, `GL_FUNC_ADD` for RGB and
  alpha, texture coordinate transform `COUNT2`, and `GL_CLAMP` U/V.
* The state logger was limited to the full 512×480 gameplay viewport and 512×1024 atlas;
  256 targeted calls had the same correct state. Its test DLL is
  `wined3d_dbg135_gpu_state_viewport.dll` (`b698fd05…`).

Therefore, the evidence does **not** support another broad texture-format census, a UV
normalization fix, or a blend-factor substitution as a first move.

### Why the game legitimately uses this path

The available game source sets `D3DTOP_MODULATE2X` for colour and alpha texture stages;
see `mgs_source/MGS2-Source-main/mgs2x/source/system/libdg/xd3d.c:252-254`. It also documents
the intended normal compositing equation

```text
a * Cs + (1 - a) * Cd = SRCALPHA, INVSRCALPHA
```

at `xd3d.c:351-375`. Splash effects reference `splash05_alp` in
`mgs2x/source/user/mode/demo/effect/demoeffect.cnf`.

The source confirms the D3D state is intentional. The unresolved question is why the
GLES-resulting normal-alpha fragment output becomes white/opaque even though texture alpha,
vertex data, UV transformation, and GL blend state are correct.

### Focused research questions

1. Review Wine 11 WineD3D's fixed-function GLSL generation (`dlls/wined3d/glsl_shader.c`,
   `ffp_gl.c`, and the state path in `context_gl.c`) for GLES-specific divergence in the
   D3D8 texture-stage sequence used here: `D3DTOP_MODULATE2X`, alpha operand/current/diffuse
   handling, saturate/clamp behaviour, and the final `SRC_ALPHA/INV_SRC_ALPHA` output.
2. Is a Mali-G52/libmali GLES 3.2 compiler/driver issue plausible for this generated shader
   pattern? If so, recommend a *narrow* shader rewrite/workaround with a way to identify
   only the affected program/state, rather than changing all normal alpha draws.
3. Suggest the lowest-overhead next observation that distinguishes a wrong fragment colour
   from a correct fragment colour blended incorrectly (for example, a selected-draw FBO
   readback before and after blending, or a diagnostic colour-mask pass). It must use GLES
   entry points available in this build.
4. If a desktop/reference comparison is useful, specify the exact observation to compare.
   A first host run is invalid because Wine/XWayland created a 640×480↔4096×2560 resize loop;
   do not infer a rendering conclusion from that failure.

Relevant code hooks already present:

```text
dlls/wined3d/context_gl.c:4755  normal-alpha skip gate
dlls/wined3d/context_gl.c:5523  normal-alpha input/state logger
dlls/wined3d/context_gl.c:6642  logger call site in draw path
dlls/wined3d/texture_gl.c:1818  GPU texture-alpha readback
```

## 5. Completed issue: codec portraits (context only)

Portraits had been invisible because the fallback render-target capability probe tried the
desktop-only `glGetTexImage`. On GLES it under-advertised the codec off-screen
`B8G8R8X8` target. The production WineD3D now uses a gated GLES-safe FBO interior-pixel
readback (`glReadPixels(GL_RGBA, GL_UNSIGNED_BYTE)`) in `dlls/wined3d/utils.c:1253+`.

A separate timeline probe found a specifically matched full black codec composite quad after
the face target was filled. The production launcher enables both:

```text
MGS2_GLES_FBO_READBACK=1
MGS2_SKIP_CODEC_BLACK_QUAD=1
```

The matching code is `context_gl.c:4999`; it is intentionally codec-specific. This fix was
verified twice with 70-confirm, zero-fault runs and is already the default. It is evidence
that FBO readback can be used safely when narrowly gated, not evidence that the gameplay
alpha problem is another missing texture upload.

## 6. Open issue: title backdrop and PSS cutscenes

The port executable intentionally patches out PSS playback at file offset `0x17D82F`
(`7d 1d` → `90 90`) to avoid a blocking/crashing path. The title/main-menu animated
background uses the same movie path, so it is absent along with normal cutscenes. Any
remaining static protagonist layer should be inspected separately after playback works.

Merely reverting the bytes was tested and did not make movies play. The game uses DirectShow
through COM (`FilterGraph`, `CoCreateInstance`, `AMovieSetupRegisterFilter` and
`rdr_movie.c`); it has no simple static `quartz.dll` import. Movie assets are intact and
read fully. Wine's `quartz.dll`, `devenum.dll`, `winegstreamer.dll`, GStreamer and
`libgstlibav` are present.

**Useful research direction:** build a minimal 32-bit DirectShow graph inspector that uses
the game's source filter, enumerates output pins and `AM_MEDIA_TYPE`, calls `Render()`, then
logs the first failing `Connect` HRESULT. The important answer is whether the game's PSS
stream presents MPEG-1, MPEG-2 elementary video, or an unsupported custom media type. Do
not assume registering generic ACM audio codecs will solve it; that was already attempted.

## 7. Open issue: 2-on/2-off backdrop striping

On animated screens only, rows follow a strict periodic pattern: two correct rows followed
by two identical fill rows `(0,16,0)` across the full 640-pixel width. Static screens do
not exhibit it. The PS2 source uses field/interlaced rendering, which may be relevant.

**Focused next experiment:** clear the animated backdrop's intermediate render target to a
sentinel colour before its draw. Sentinel-coloured missing rows mean they were never written
(viewport/scissor/coverage); unchanged `(0,16,0)` rows mean another clear/blit wrote them.

## 8. Important constraints and prior dead ends

* Wine upstream is not designed as a first-class WineD3D-on-GLES stack. Do not enable random
  desktop-GL entry points or desktop-only APIs; many are NULL behind Wine's dispatch layer.
* `glBindFragDataLocation`, `glDepthRange`, `glBlendEquation`, illegal 16-bit GLES texture
  formats, and false `EXT_DRAW_BUFFERS2` capability promotion have already been fixed.
* Forcing `ARB_ES2_COMPATIBILITY` is harmful in this build: it selects GLES calls that the
  entry-point gate still refuses.
* L8/luminance, DXT/S3TC, X1R5G5B5/X4R4G4B4, fonts, and menu-only texture format theories
  are not explanations for the current gameplay white effects.
* The production image is the tested `dbg123` codec build. Keep it intact; build a new
  opt-in DLL for every alpha experiment and use `MGS2_WINED3D_DLL=<name>` for A/B.

## 9. What a useful research answer looks like

Please provide:

1. A ranked root-cause hypothesis tied to a specific WineD3D shader/state code path or a
   documented Mali GLES limitation.
2. A minimal diagnostic that can falsify the hypothesis on this device.
3. A narrow proposed patch, including why it avoids changing unrelated normal-alpha draws.
4. A verification plan using the 70-confirm RG353VS harness and the existing screenshots.

Avoid recommendations that merely hide the defect by turning off effects, globally clamping
alpha, skipping all normal alpha blends, switching to a much slower GPU driver, or assuming
that a desktop-Wine result is authoritative over the console.

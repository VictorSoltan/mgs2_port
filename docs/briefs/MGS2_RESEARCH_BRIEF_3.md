# Research brief #3 — two texture-format defects identified, rebuild still renders wrong

Self-contained; no prior context needed. Supersedes briefs #1 and #2, whose main questions
are answered or disproven. Project history: `MGS2_RG353VS_HANDOFF.md`.

---

## 1. Setup

Metal Gear Solid 2: Substance (PC, **Direct3D 8**, 2001) on an Anbernic RG353VS.

| | |
| --- | --- |
| SoC | Rockchip RK3566, Mali-G52 (Bifrost) |
| OS | ROCKNIX (Linux), sway/Wayland |
| GPU driver | proprietary **libmali** — **OpenGL ES 3.2 only**, no desktop GL, no 32-bit Vulkan ICD |
| Emulation | box64 launches Wine; the 32-bit game runs under **box86** |
| Path | D3D8 → local `d3d8.dll` proxy → d3d9 → **WineD3D** → OpenGL |
| Wine | 11.0, MinGW `i686-w64-mingw32` |

**libmali is a hard constraint** (Panfrost/VirGL/gl4es rejected: performance, and VirGL is
absent while the local gl4es build is destroyed). Wine upstream has no GLES support in
WineD3D; on this device **3144 of 5256 GL entry points are NULL**, and calling one jumps
to address zero.

## 2. Current state

The game boots, renders the title screen and menus at 23–35 fps, and is navigable. The
shipping build is `dbg42` plus **two binary patches applied to the working binary**,
because rebuilding from source does not reproduce its rendering (see §4):

1. **6 bytes** — the `ffp_gl.c` viewport handler's `call *0x56c(%ebx)` (`glDepthRange`,
   NULL on GLES) replaced by `add $0x10,%esp` + NOPs: skip the call and pop the two
   doubles the `__stdcall` callee would have popped. Fixes the crash on entering any 3D
   scene. Verified: 0 page faults where there was always exactly one.
2. **4 bytes** — see §3.

Two visible defects remain: **background artwork renders as horizontal striping**, and the
**WARNING dialog body text is missing**.

## 3. Measured: which texture formats the game actually uses

Earlier rounds reasoned about formats from the game's age. This is now measured, by logging
`debug_d3dformat(desc->format)` at every `wined3d_texture_init`:

| format | count |
| --- | --- |
| `B8G8R8A8_UNORM` | 127 |
| `B5G5R5A1_UNORM` | **10** |
| `B8G8R8X8_UNORM` | 3 |
| `L8_UNORM` | **2** |
| `D24_UNORM_S8_UINT` | 2 |
| `B4G4R4A4_UNORM` | 2 |

Notable: **no DXT/S3TC at all** (so Mali's lack of S3TC is a non-issue), and **no X1/X4
variants** (converters written for those were wasted effort).

### 3a. RETRACTED — `L8_UNORM` was never broken, and the patch was a no-op

This section previously argued that `L8_UNORM` mapped to `GL_LUMINANCE8` (invalid in GLES
3.0 core), that two such textures looked like a font atlas, and that a 4-byte patch to
that table row might restore the missing dialog text. **All three claims are wrong**, and
the correction is worth recording because the reasoning error is a reusable one.

Wine 11.0 carries **two** `L8_UNORM` rows and picks between them on capability bits:

```
L8 -> GL_LUMINANCE8 / GL_LUMINANCE   requires WINED3D_GL_LEGACY_CONTEXT
L8 -> GL_R8         / GL_RED         requires ARB_TEXTURE_RG      <- later row wins
```

The initialisation loop walks every row and *overwrites*, so the last supported row wins.
A runtime dump of the finalised state on this device gives:

```
CAP WINED3D_GL_LEGACY_CONTEXT 1     CAP ARB_TEXTURE_RG 1     CAP ARB_TEXTURE_SWIZZLE 0
FMT L8_UNORM  internal=0x8229 (GL_R8)  format=0x1903 (GL_RED)  fixup=XXX1
```

So the active row was already the modern one, the `(R,R,R,1)` fixup is already applied
(in the generated shader, since texture swizzle is unavailable), and **the row I patched
was never selected**. "No regression" was not weak evidence of a fix — it is exactly what
a no-op produces.

The texture census also kills the font-atlas premise outright: there is **one** L8
texture and it is **16×16**.

Lesson for anything similar: patch or edit only after dumping which row is *selected*.

### 3b. The 16-bit formats are almost certainly the striping

`B5G5R5A1` (10 textures) and `B4G4R4A4` (2) are still mapped to `GL_BGRA` +
`GL_UNSIGNED_SHORT_*_REV`. Neither token exists in GLES, so those uploads fail outright.
Ten textures is a plausible count for title/menu background artwork, matching the symptom
that 32-bit assets are crisp while the artwork behind them is corrupt.

Correct conversions are already written in source (16-bit rotate left by 1 and by 4, exact
and still two bytes per texel) but **cannot ship**, because they need a conversion function
— i.e. compiled code — and no rebuild renders correctly. This is the whole reason §4 is the
critical path.

### 3c. What the measured texture census actually contains

Sizes and usage, not just formats — this changes the reading of the table above:

| format | size | count | note |
| --- | --- | --- | --- |
| `B8G8R8A8_UNORM` | 128² … 1024×2048 | 127 | ordinary artwork, renders correctly |
| `B4G4R4A4_UNORM` | **1024×512** | 2 | large atlas; upload was **failing** — see below |
| `B5G5R5A1_UNORM` | 512×128 | 3 | banners |
| `B8G8R8X8_UNORM` | **640×480** | 3 | screen-sized; one is the render target, one is a `GPU|MAP_R|MAP_W` surface |
| `L8_UNORM` | **16×16** | 1 | not a font atlas |
| `D24_UNORM_S8_UINT` | 640×480, 512² | 2 | depth |

**A second, real defect found by dumping the finalised state.** libmali exposes
`EXT_texture_sRGB_decode`, so `query_internal_format()` takes its designed path and
replaces `internal` with the row's sRGB variant, expecting `GL_TEXTURE_SRGB_DECODE_EXT`
to control decoding at sample time. For the packed 16-bit rows that substitutes an
8-bit-per-channel internal format, and the measured result was:

```
FMT B4G4R4A4_UNORM  internal=0x8c43 (GL_SRGB8_ALPHA8)  type=0x8033 (GL_UNSIGNED_SHORT_4_4_4_4)
```

which is not a legal GLES pairing — so that 1024×512 atlas never uploaded at all, and the
conversion function written for it could not have helped. Fixed by pinning
`internal`/`srgb_internal` in the GLES branch (`GL_RGBA4`, `GL_RGB5_A1`, `GL_RGBA8`)
*after* `query_internal_format()` has run.

## 4. RESOLVED: the rebuild is identical to dbg42

**This section's premise was false and the question is closed.** A proper semantic diff
of the two PE binaries — never done before, only *text symbol names* had been compared —
shows dbg42 contains no rendering work the tree lacks. Method, in narrowing order:

1. **Data tables.** Dump every initialised data symbol with pointer words resolved to
   `symbol+offset`, so two different layouts become comparable. All ~4 655 match except
   GUIDs and string-pointer tables (normalisation noise). `format_texture_info` is
   byte-identical: 125 records × 12 fields.
2. **Function bodies.** 4 193 functions, 3 911 byte-identical after normalising addresses
   to symbols; only **19** change size.
3. **Call sets per function.** 14 differ, 13 of them my own instrumentation. The
   fourteenth: dbg42 keeps `shader_glsl_add_version_declaration` out of line as
   `.isra.0`, called from 10 sites; the rebuild inlines it to one `shader_addline`.
   Disassembling dbg42's copy and reading its `.rdata` operands gives
   `"#version 300 es\n"`, `"precision highp float;\n"`, `"precision highp int;\n"` — the
   same three strings the tree emits, merely split across three calls. Byte-identical
   generated GLSL.

The remaining 262 differing functions differ only in `__LINE__` constants shifted by my
own edits (`0x515` → `0x519`) and in register allocation.

**Why rebuilds looked worse:** my own unbuffered `fopen`/`fclose`-per-call tracer was
left on the per-draw path — about 13 file opens per draw call. Gating it off makes the
rebuild produce **byte-identical frames** to the reference at every sampled offset.

Everything below is retained for the method only.

Rebuilds used to *crash*; that is fixed. Three source changes make a rebuild survive, all
found by tracing:

- `adapter_gl.c` — classify a GLES context as core profile, not legacy (`GL_CONTEXT_PROFILE_MASK`
  yields nothing on GLES, so the fall-through marked it legacy and installed fixed-function
  state handlers that call non-existent entry points);
- `ffp_gl.c` — `glDepthRange` → `glDepthRangef`, else skip;
- `glsl_shader.c` — **skip `glBindFragDataLocation` on GLES**; it is called unguarded while
  linking every program, does not exist in GLES (outputs are bound by `layout(location=)`),
  and was the fatal one.

**But no rebuild reproduces dbg42's output.** With the crash fix alone the title screen is
almost entirely black; adding the other fixes improves it but never matches. Removing the
fixes does not help either. So the fixes are not the cause — the tree itself renders
differently, and dbg42 contains further GLES rendering work that is **not present in the
tree and not visible in the symbol table** (text-section symbols matched dbg42 to a single
entry, `_shader_glsl_add_version_declaration.isra.0`).

### Questions for §4 — this is the highest-value area

1. Two PE builds of the same Wine tree, same toolchain, whose **exported and internal
   symbol names match to one entry**, yet render differently. What classes of difference
   survive that comparison — inlined constants, data tables in `.rdata`, generated headers,
   per-file flags — and what is the most efficient way to find them in a 25 MB DLL?
2. Concretely: how would one diff two WineD3D builds *semantically*, e.g. compare the
   `format_texture_info` table, the state-entry templates, and the fragment/vertex pipe
   operation tables as **data**, rather than diffing instructions?
3. Wine's `wined3d_shader_backend_ops` / state-template machinery is built at runtime from
   arrays. Is there a supported way to dump the **selected** state handlers and format
   table at runtime, so two builds can be compared by behaviour instead of by bytes?

## 5. Correct long-term handling of the format issues

4. What is the right GLES 3.x mapping for D3D `L8_UNORM`? The binary patch uses unsized
   `GL_LUMINANCE`, which is legal but deprecated. The modern route is `GL_R8` + `GL_RED`
   plus `GL_TEXTURE_SWIZZLE_RGBA = (R,R,R,1)` — does WineD3D's existing `color_fixup_desc`
   already express exactly this, and is it wired for the GL backend?
5. Same question for `A8_UNORM` and any other legacy luminance/alpha formats, in case they
   appear later in the game even though the title/menu path does not use them.
6. `glDepthRangef` is not pre-resolved by win32u here, so the source fix currently *skips*
   the call rather than substituting it. It is core GLES, not an extension — what is the
   correct way to get it into Wine's GL dispatch for a GLES context?

## 6. Verification problem worth solving

Two measurement pitfalls have already cost real time, and a third now blocks progress:

- **Frame size is not a quality metric.** The title screen runs an attract loop, so a single
  screenshot's size depends on when it was taken; the same build measured 13 414 and
  104 962 on different captures. Sample several frames and take the richest, or drive to a
  deterministic screen.
- **Wine's `ERR` output is lossy.** Routed through box86 into a redirected file it is
  buffered and **loses its tail when the process dies**, so "last line in the log" is not
  "last thing executed". Use an unbuffered `fopen`/`vfprintf`/`fclose` tracer instead. This
  single change turned a day of guessing into three targeted steps.
- **Input injection no longer reaches the game.** Synthetic keys via `/dev/uinput`
  (`python3 send_key.py tab`) used to drive the menus and now do not — only the animated
  background changes. Consequently **the L8 fix in §3a is unverified**: reaching the WARNING
  dialog currently requires a human with the handheld.

7. What is a reliable way to inject input into a Wine/box86 game under sway on this device
   — is the problem focus, the gptokeyb mapping layer, or uinput device grabbing?

## 7. Ruled out — please do not re-investigate

- **Presentation driver.** Rebuilt from scratch; an A/B of the same frame through two
  different presentation drivers gives identical corruption.
- **Fonts.** Installing the full Wine font set changed the blank MessageBox by zero bytes.
- **DXT/S3TC.** The game creates none.
- **X1R5G5B5 / X4R4G4B4.** The game creates none.
- **`ffp_hlsl`.** Removes the per-frame FFP errors but crashes earlier — it only replaces
  FFP *shader generation*, leaving the `ffp_gl.c` state table installed.
- **`glAlphaFunc`.** Loud in logs, resolves **non-NULL**, never the fatal call.
- **Viewport/clip-control handler selection.** Chosen by `ARB_CLIP_CONTROL`, not by the
  legacy-context flag; reverting the core-profile change still renders wrong.
- **The fault address `79d32476`.** Appears for every failure, including ones where the
  offending call had provably been deleted. It is a shared opengl32/win32u thunk and
  identifies nothing.

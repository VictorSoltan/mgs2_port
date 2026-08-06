# Research brief — Direct3D 8 game on a GLES-only Mali via Wine + box86

This is a self-contained problem statement for research. No prior context needed.
Project state and history live separately in `MGS2_RG353VS_HANDOFF.md`; this document
only covers what is still unknown and what would unblock it.

---

## 1. The setup

Running the PC release of **Metal Gear Solid 2: Substance** (Direct3D 8, 2001) on an
**Anbernic RG353VS** handheld:

| | |
| --- | --- |
| SoC | Rockchip RK3566, 4× Cortex-A55, **Mali-G52** (Bifrost) |
| OS | ROCKNIX (Linux), Wayland compositor (sway), EmulationStation frontend |
| GPU driver | **proprietary ARM libmali blob — OpenGL ES 3.2 only, no desktop GL, no 32-bit Vulkan ICD** |
| Emulation | box64 launches Wine; the 32-bit game runs under **box86** (Wine old-WoW64) |
| Wine | 11.0, custom-built. D3D8 → local `d3d8.dll` proxy (V's Fix) → d3d9 → **WineD3D** → OpenGL |

**Hard constraint: the solution must stay on libmali.** Panfrost (Mesa, gives real desktop
GL) and VirGL were considered and deliberately rejected — libmali is substantially faster
and this port has no performance headroom to spare. VirGL is also absent from the device
and gl4es's local build is destroyed (0-byte `libGL.so.1`).

**The core difficulty:** WineD3D targets desktop OpenGL. Wine upstream does not support
OpenGL ES in WineD3D. Measured on the device, **3144 of 5256 GL entry points resolve to
NULL** — the entire fixed-function and immediate-mode API (`glBegin`, `glVertex*`,
`glTexCoord*`, `glOrtho`, `glLightModel*`, `glDepthRange`, `glAlphaFunc`, …). MGS2 is a
fixed-function D3D8 title, so it walks straight into them. Calling one does not fail
gracefully; it jumps to address zero and kills the process.

## 2. What currently works

The game boots, renders the title screen and all menus, and is navigable at **23–35 fps**.
A **six-byte binary patch** to the working WineD3D DLL removes the crash on entering a 3D
scene: the `ffp_gl.c` viewport handler's `call *0x56c(%ebx)` (`glDepthRange`) was replaced
with `add $0x10,%esp` + NOPs — skip the call and pop the two doubles the `__stdcall`
callee would have popped. With it: 0 page faults, all menu steps pass, 80+ s alive in the
scene where it previously died instantly.

## 3. Blocking problem A — a rebuild from source is not viable, cause unknown

The working DLL (`wined3d_dbg42_gles_present.dll`) was built in an earlier session whose
**source state is lost**. The tree on disk cannot reproduce it: every rebuild dies before
the title screen, while the prebuilt binary works.

Evidence gathered:

- The toolchain is faithful — building the tree unmodified reproduces a *different* known
  artifact (`dbg45_profile.dll`) at **byte-identical size** (25 162 749).
- Comparing text-section symbol tables, dbg42 has **4 193** function symbols and a rebuild
  **4 192**. The only entry dbg42 has that no rebuild produces is
  `_shader_glsl_add_version_declaration.isra.0`. Every other function matches by name.
- The `.isra.0` suffix is GCC cloning a function whose parameter became unused, implying
  dbg42's version of that function ignores its `gl_info` argument — i.e. emits the GLES
  shader header unconditionally rather than testing a flag. Both forms were built and
  tested; **both still die before the title**.
- String parity was reached (`#version 300 es` ×3, `precision highp` ×2 in both).
- Size still differs: dbg42 = 25 154 427, closest rebuild = 25 158 376.
- Ruled out as causes: leftover profiling instrumentation in `swapchain.c` (removed);
  configure differences (`vulkan`/`freetype`/`fontconfig` string counts identical);
  the depth-range fix itself; several speculative GLES shims (which were themselves wrong
  — they rerouted `glDrawBuffer` to `glDrawBuffers` when only `glDepthRange` is broken).

**Best remaining lead:** the last WineD3D message before a rebuild dies is consistently

```
GL_INVALID_OPERATION (0x502) from glAlphaFunc @ dlls/wined3d/glsl_shader.c / 12017
```

`glAlphaFunc` is desktop-only fixed-function alpha test; GLES has no such call.

**A methodological warning worth repeating**, because it cost hours: the fault address
`returning to user mode ip=79d32476` appears for *every* failure, including one where the
offending call had provably been deleted from the source. It is a shared opengl32/win32u
thunk that any NULL GL entry point lands on. Identical fault addresses mean "some missing
GL function", **not** "the same one". Do not use it to identify a call site.

### Questions for A

1. What mechanisms, other than source differences, can make two builds of the same Wine
   tree with the same toolchain behave differently — and how would one bisect a PE binary
   against a rebuild when the symbol tables already match to one entry?
2. How is fixed-function **alpha test** (`glAlphaFunc`/`GL_ALPHA_TEST`) normally handled
   when WineD3D runs against a context that lacks it? Is it folded into the generated
   fragment shader (a `discard`), and if so what enables that path?
3. Are there any published patchsets, forks or distro packages that make **WineD3D work
   against OpenGL ES** directly, without an intermediate desktop-GL translation layer?
   (Android/Termux/Winlator all appear to use VirGL or gl4es instead — is there prior art
   for the direct approach?)

## 4. Blocking problem B — texture formats are wrong on GLES

This is the visible defect and, judging by the symptoms, the more important one. On the
title screen the logo and menu text are crisp while the background artwork is broken up
with heavy horizontal striping. Proven **not** to be the presentation path: an A/B of the
same frame through two different Wayland presentation drivers produces identical
corruption.

`init_format_texture_info()` in `dlls/wined3d/utils.c` carries exactly one GLES fixup, for
`WINED3DFMT_B8G8R8A8_UNORM`. Reading the table against what GLES accepts:

| D3D format | GL format / type in the table | status on GLES |
| --- | --- | --- |
| `B8G8R8A8_UNORM` | `GL_BGRA` / `GL_UNSIGNED_INT_8_8_8_8_REV` | invalid — **already fixed** (converts to RGBA on upload) |
| `B5G5R5A1_UNORM` | `GL_BGRA` / `GL_UNSIGNED_SHORT_1_5_5_5_REV` | **invalid, unhandled** |
| `B4G4R4A4_UNORM` | `GL_BGRA` / `GL_UNSIGNED_SHORT_4_4_4_4_REV` | **invalid, unhandled** |
| `B8G8R8X8_UNORM` | `GL_RGBA` / `GL_UNSIGNED_BYTE` | accepted, but data is BGRX → **R/B swapped** |
| `B5G6R5_UNORM` | `GL_RGB` / `GL_UNSIGNED_SHORT_5_6_5` | fine |

`GL_BGRA` and the `_REV` packed types do not exist in GLES, so those uploads fail and the
texture keeps undefined contents. The two 16-bit formats are exactly what a 2001 PS2-era
port uses for background artwork, matching the symptom precisely.

A binary patch cannot fix this: swapping the tokens to `GL_RGBA` /
`GL_UNSIGNED_SHORT_5_5_5_1` makes the upload legal but wrong, because D3D puts alpha in the
**high** bit and GLES `5_5_5_1` puts it in the **low** bit. A correct fix needs a
conversion function on upload, mirroring the existing `convert_b8g8r8a8_unorm_gles`. That
means compiled code — which is why problem A blocks problem B.

### Questions for B

4. What is the correct GLES upload path for D3D `A1R5G5B5` and `A4R4G4B4`? Convert on the
   CPU to `GL_RGBA`/`GL_UNSIGNED_SHORT_5_5_5_1` and `_4_4_4_4` with the bit rotation, or
   expand to 32-bit RGBA8, or rely on an extension?
5. Is `GL_EXT_texture_format_BGRA8888` / `GL_APPLE_texture_format_BGRA8888` present on Mali
   libmali, and does either make `GL_BGRA` usable as an upload format (they historically
   differ on whether BGRA is allowed as *internalformat*)?
6. For `B8G8R8X8_UNORM`, is there a cheaper correct route than a CPU byte swap — e.g.
   `GL_EXT_texture_swizzle` / core GLES 3.0 `glTexParameteri(GL_TEXTURE_SWIZZLE_R/B)`?
7. Does MGS2/D3D8 also use DXT1/3/5? Mali does not usually expose S3TC; how does WineD3D
   decompress, and does that path work on a GLES context?

## 5. Also open, lower priority

8. After the binary patch the game survives the 3D scene for ~100 s and then exits
   **cleanly** — no page fault. Cause unknown.
9. Wine `MessageBox` dialogs render with **no text** on this setup (the icon and frame
   draw). 69 fonts were symlinked into the prefix with no effect, and win32u's freetype
   support is identical to the working build. Text is readable only via a relay trace:
   set `RelayInclude` under `HKCU\Software\Wine\Debug` and run `WINEDEBUG=+relay`.

## 6. What a useful answer looks like

Highest value first:

- **Anything that explains A** — a rebuild that reaches the title unblocks B and every
  future fix, and ends the reliance on binary patching.
- **A concrete conversion recipe for B** — exact GL format/type plus the byte/bit
  transformation for `A1R5G5B5`, `A4R4G4B4` and `X8R8G8B8` on GLES 3.x.
- Prior art on WineD3D against GLES on Mali specifically, since that is the configuration
  that cannot be changed.

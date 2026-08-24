# MGS2 Substance on Anbernic RG353VS / RockNix — handoff

> Status note, 2026-08-02: this is the chronological engineering log and contains
> superseded hypotheses. `MGS2_PROJECT_STATE.md` is the authoritative current state.
> In particular, codec portraits are now confirmed working in a gated test build, and
> the white Tanker artefact is no longer a texture-census hypothesis: normal alpha draws
> are causal while their texture alpha, UVs, vertex alpha and emitted GL blend state are
> measured correct. See §§6a–6b and §9 of the project-state document before continuing.

## Goal

Run the licensed DRM-free GOG release of **Metal Gear Solid 2: Substance** on an Anbernic RG353VS (RK3566, ARM64, Mali-G52) under RockNix with Wine + box86/box64, at a stable playable frame rate without console resets.

The game is not yet playable enough to call the project complete.  It reaches the title screen correctly, but the `WARNING`/menu transition is extremely slow and heavy loads have reset the console.

## Device and access

```sh
ssh "$MGS2_DEVICE"
# password: rocknix
```

Important paths on the device:

- game and deployed port: `/storage/roms/ports/MGS2-Substance`
- launcher selected by EmulationStation: `launch.sh` in that directory
- executable: `game/bin/mgs2_sse_rg353vs_port.exe`
- prefix: `wineprefix64`
- Sway IPC: `/run/0-runtime-dir/sway-ipc.0.sock`
- screenshot: `XDG_RUNTIME_DIR=/var/run/0-runtime-dir WAYLAND_DISPLAY=wayland-1 grim /tmp/frame.png`

The console often reboots under the heaviest test. A reboot removes `/tmp` scripts/logs and all bind mounts. Always re-check deployed file checksums before attributing a new result to a code change.

## Current production launcher

Local source of the deployed launcher: `recovered-session/device-artifacts/launch.sh`.

It does the following:

- uses old WoW64: `box64 /usr/bin/wine` launches the 32-bit x86 game under box86;
- sets `d3d8=native;d3d9=builtin`, so the game uses the local V's Fix/d3d8-to-d3d9 proxy;
- bind-mounts the required custom components only for the process lifetime;
- uses a lock (`/tmp/mgs2-substance.lock`) to prevent duplicate game instances;
- maps controls through `mgs2.gptk` (`Start=Tab`, `Select=Enter`, `A=Z`, `B=X`);
- cleans all stacked bind mounts on exit.

The launcher's thermal handling has been rewritten (built locally, **not yet deployed**). The old version polled every 2 s and did nothing but kill the game at 90 C — too late for a spike, and destructive when a small clock reduction would do.

It now caps the top frequency bin, pins the governor to `performance` *within* that cap so frame times stay even, and steps the cap up and down with temperature. Killing is the last resort, at a temperature below the observed reset point:

| Variable | Default | Meaning |
| --- | --- | --- |
| `MGS2_FREQ_STEPS` | `1608000 1416000 1200000 1008000` | cap ladder, starts at the first entry |
| `MGS2_TEMP_DOWN` | `84000` | step the cap down above this |
| `MGS2_TEMP_UP` | `76000` | allow stepping back up below this |
| `MGS2_TEMP_KILL` | `88000` | hard stop |
| `MGS2_TEMP_POLL` | `0.5` | seconds between samples |

Transitions are appended to `/tmp/mgs2-thermal-guard.log`. The previous governor and `scaling_max_freq` are saved at start and restored by the existing `cleanup` trap, so an abnormal exit does not leave the console clamped.

### Launching from the EmulationStation menu

EmulationStation runs `/storage/roms/ports/MGS2-Substance.sh`, a three-line wrapper that `exec`s `MGS2-Substance/launch.sh`. So the menu entry and a manual `./launch.sh` take exactly the same path, and every change to `launch.sh` applies to both.

One failure mode is silent and worth knowing: the game process can outlive both the launcher and wineserver. An orphan keeps `/tmp/mgs2-substance.lock` held, and the next menu launch then hits the `flock` guard and exits with no message at all — the menu simply appears to do nothing. `cleanup()` now kills the game explicitly. If it is ever seen again:

```sh
pkill -9 -f "[m]gs2_sse_rg353vs_port"   # bracket avoids matching the pkill itself
```

Note that plain `pkill -f <pattern>` matches its own command line; that has caused dropped SSH sessions in this project more than once. Prefer `killall` with an exact name, or the bracket form — and note the bracket form is **not** enough on its own; see "the `pkill -f` self-match trap has a second form" below.

### The default is now a source build

`wined3d_dbg77_safe.dll`, built from `recovered-session/build-wine-i386`. This is the
first time the shipping component is compiled from source rather than a binary-patched
`dbg42`, and it is what the rebuild investigation above unlocked. Contents:

* the crash fix in source (`glBindFragDataLocation` skipped on GLES) rather than as a
  6-byte patch;
* `glDepthRange` → `glDepthRangef`-or-skip in the viewport handler;
* the 16-bit / X-channel GLES texture converters, with their sized internal formats
  pinned after `query_internal_format()` (see the `B4G4R4A4` defect above);
* `glGetTexImage` guarded on GLES in all four call sites;
* every tracer gated off;
* the two GLES capability overrides present but **off**, because measurement said so.

Verified before promotion: full driven menu sequence, deterministic disclaimer frame
byte-identical to the reference (`a83d147fe562`), finalised format records confirmed by
manifest (`B4G4R4A4` `GL_RGBA4`, `B5G5R5A1` `GL_RGB5_A1`, `L8` `GL_R8`).

### Runtime switches added this round

`launch.sh` now honours `MGS2_EXE`, so an alternate executable can be tested without
editing the launcher. Everything else here is read by `wined3d` itself and is off or
neutral by default, so a shipping run does no extra work:

| Variable | Default | Effect |
| --- | --- | --- |
| `MGS2_EXE` | `mgs2_sse_rg353vs_port.exe` | which game executable to launch |
| `MGS2_TRACE` | off | per-draw unbuffered tracer — **crash hunting only**, ruins frame rate |
| `MGS2_TEXLOG` | off | one line per texture creation: format, size, usage, access |
| `MGS2_UPLOG` | off | one line per GL texture upload: update box, row pitch, destination size |
| `MGS2_MANIFEST` | off | one-shot dump of finalised GLES capability bits and per-format records |
| `MGS2_GLES_CONV` | on | the 16-bit / X-channel GLES converters; set to `0` to A/B them |

Do **not** confuse the separately created test launchers with the installed production launcher.

## Working graphics configuration

The only confirmed continuously updating, upright image is this combination:

| Component | Deployed file |
| --- | --- |
| box86 | `box86-clean1` |
| Wine win32u | `win32u_glfuncs3.so` |
| Wayland presentation | `winewayland_pbo1.so` (was `winewayland_gbmshm_directbgra1.so`) |
| WineD3D | `wined3d_dbg42_gles_present.dll` |

`winewayland_gbmshm_directbgra1.so` presents by reading Mali GLES output directly into a Wayland SHM buffer as BGRA. It removes the previous RGBA→BGRA per-pixel conversion and a second full-frame copy, but `glReadPixels()` remains synchronous and is still a significant cost.

`winewayland_pbo1.so` is the current default: same synchronous readback, rebuilt from restored source, with built-in timing and runtime switches. See "Presentation: measured results".

Known image variants:

- `dbg42`: correct orientation, updating image — use this.
- `dbg43`: upright, but freezes/black screen.
- `dbg44`: updating, but mirrored/diagonal — do not use.
- RockNix stock `winewayland`: created an EGL surface but `wglMakeCurrent` failed with `0xc0000005`.

## Wine / GLES fixes already made

Custom Wine 11.0 sources are under `recovered-session/wine-11.0`; the i686 PE build directory is `recovered-session/build-wine-i386`.

Confirmed fixes that enabled D3D initialisation and the title screen:

1. Pre-resolved a large set of lazy GL entry points in `dlls/win32u/opengl.c`; otherwise first `wglGetProcAddress()` calls from WineD3D returned `NULL`.
2. Added GLES fallback from desktop-only `glDrawBuffer` to `glDrawBuffers`.
3. Guarded unsupported GLES 1D/3D texture/FBO paths.
4. Added the GLES path for the WineD3D test quad (`#version 300 es`, precision qualifiers, no unavailable `glBindFragDataLocation`).
5. Kept the FBO presentation path used by `wined3d_dbg42_gles_present.dll`.

Game executable patches in `mgs2_sse_rg353vs_port.exe` skip or guard problematic DirectMusic/DirectShow/PSS/video and sound-wait paths. The game must still use the native `d3d8.dll` proxy.

## Game settings

Both game and V's Fix settings are reduced to 640×480 / low settings:

- `MGS2SSET.ini`: render size/detail/quality/clearness and effects disabled/low;
- `Configuration_file.ini`: 640×480, `RenderingSize=low`, `InternalResolution=512`, effects low/off, `CompatibilityWarningDisplayed=true`.

The UI text of Wine MessageBox windows is blank in this setup. A relay trace confirmed the built-in D3D8 test displays `Critical error`.

### The WARNING screen is not a hang

It looks like one and was reported as one, but it is not. After `PRESS START BUTTON` the game shows a red `WARNING` banner over an empty dialog body and appears frozen. Measured while it sat there:

- the presentation driver keeps reporting **20–24 fps**, so the render loop is healthy;
- the process burns ~257 % CPU with the main thread at `wchan=0`, i.e. spinning in emulated userspace, not blocked on a syscall;
- the framebuffer hash never changes, because it is drawing the same dialog over and over.

It is simply **waiting for the A button**, which `mgs2.gptk` maps to `Z`. Sending `Z` advances it instantly, and the game then reaches the DIFFICULTY LEVEL menu, which renders correctly. `Tab` also dismisses it.

The reason it reads as a hang is the second bug: the dialog body — including the "press a button" prompt — renders empty.

**The missing text is not a font problem.** That was the obvious hypothesis and it was tested and disproven:

- `drive_c/windows/Fonts` in the re-initialised prefix was completely empty, while `/usr/share/wine/fonts` holds 56 built-in faces;
- all 56, plus the 13 system TrueType faces, were symlinked into the prefix (`tahoma.ttf` included) and verified to resolve;
- after a restart the WARNING screen produced a **byte-identical frame** (md5 prefix `db9586cd`, 1738-byte PNG). No change whatsoever.

The fonts were left installed — an empty `windows/Fonts` is wrong regardless — but they are not the cause.

**Three more hypotheses were tested and eliminated:**

| Hypothesis | Test | Result |
| --- | --- | --- |
| Wine has no fonts | linked all 56 built-in + 13 system faces incl. `tahoma.ttf` | byte-identical frame, `db9586cd` |
| Fixed-function GL calls failing on GLES | `WINE_D3D_CONFIG=ffp_hlsl=0x1` | per-frame errors 6106 → 49, but the game **crashes** before the title (NULL deref); `ffp_gl.c` still issues legacy state anyway |
| Paletted/P8 or unsupported texture conversion | `WINEDEBUG=fixme+d3d` while on the screen | **zero** format/conversion complaints |
| V's Fix compatibility warning | checked `Configuration_file.ini` | `CompatibilityWarningDisplayed=true` is already set — this is the game's own screen |

On the GL errors specifically: the dominant ones were `glDisable(GL_LINE_SMOOTH)` and `depth clip`, 3699 each, i.e. once per frame. They are `GL_INVALID_ENUM` on enums GLES does not know, which is a harmless no-op — noise in the log, not the cause. `ffp_hlsl` silences them but is **not usable**: it only replaces FFP *shader generation*, leaves the `ffp_gl.c` state table installed, and crashed the game. Do not enable it.

**What the evidence now points at.** The frame is byte-identical (`db9586cd`) across separate launches, which argues against a stalled animation — a frozen timer would not land on the same pixel twice. The partial "L" outline is very likely MGS2's intended bracket-style frame, not a half-drawn box. So the screen is probably rendering exactly as the game asked, and the missing element is the text draw itself. Since the title screen and the DIFFICULTY LEVEL menu both render their text correctly through the same engine, this is specific to that one dialog rather than a systemic text failure.

**Recommended next step before spending more on it:** play far enough in to confirm HUD, codec and subtitle text render. If they do, this is one cosmetic screen and is not worth destabilising `dbg42`, where `dbg43`/`dbg44` show how easily regressions appear. If in-game text is also missing, it is systemic and justifies real WineD3D work.

## Root cause class, restated: Wine promotes extensions by *desktop* version number

This is the single most useful generalisation found so far, and it explains several
separate crashes at once.

`wined3d_adapter_init_gl_caps()` turns extensions into internal capability bits using a
table keyed on **desktop** GL versions:

```c
{ARB_TEXTURE_RG,          MAKEDWORD_VERSION(3, 0)},
{ARB_TEXTURE_SWIZZLE,     MAKEDWORD_VERSION(3, 3)},
{ARB_ES2_COMPATIBILITY,   MAKEDWORD_VERSION(4, 1)},
```

A GLES 3.2 context parses as version 3.2 and is then measured against that scale, which
is meaningless: GLES 3.2 *has* red/green textures, texture swizzles and the ES-style
float entry points, but scores 3.2 against thresholds meant for desktop GL. Measured on
this device before the fix:

```
is_gles=1  ARB_TEXTURE_RG=1  ARB_TEXTURE_SWIZZLE=0  ARB_ES2_COMPATIBILITY=0
```

The consequences are not cosmetic. Wine **already contains** the GLES-friendly code — it
is simply switched off:

```c
if (gl_info->supported[ARB_ES2_COMPATIBILITY])
    GL_EXTCALL(glClearDepthf(depth));      /* core GLES */
else
    gl_info->gl_ops.gl.p_glClearDepth(depth);   /* desktop only -- NULL here */
```

`glClearDepth` is confirmed NULL on this device, and clearing a depth buffer is precisely
what entering a 3D scene does. The same flag also selects `GL_RGB565` for `B5G6R5_UNORM`.

The obvious fix is to promote the capabilities GLES genuinely has, after the desktop
table has run. **It was implemented, measured, and it makes things worse — so it is off
by default.** Setting `ARB_ES2_COMPATIBILITY` switches the two depth-clear sites from
`glClearDepth()` to `GL_EXTCALL(glClearDepthf())`, and although `glClearDepthf` resolves
perfectly well through `eglGetProcAddress` (`0x40020eb0`, alongside `glDepthRangef` at
`0x40020ea0`), it is **not pre-resolved into wined3d's ext table** by the win32u build in
use — the same gap already documented for `glDepthRangef`. The flag therefore trades a
working call for a NULL one: the game dies *before the first frame* instead of in the
menus. Confirmed twice by A/B with the flag as the only variable and the manifest
verifying it flipped, the second time with `glGetTexImage` additionally guarded.

The switches (`MGS2_GLES_ES2COMPAT`, `MGS2_GLES_SWIZZLE`) are kept, default off. They
become correct only once win32u pre-resolves `glClearDepthf` / `glDepthRangef`, and that
is the actual prerequisite — the wined3d side is already right.

**How the NULL list was obtained** — reusable, and much better than guessing. box86 logs
every `eglGetProcAddress`, so a normal run's stdout already contains the complete
partition:

```sh
grep -oE 'my_eglGetProcAddress\("[a-zA-Z0-9_]+"\) RETURN = \(nil\)' stdout.log \
    | sed 's/.*("//; s/").*//' | sort -u        # 630 NULL
# ... RETURN = 0x ...                            # 321 resolved
```

Cross-referencing the 630 against `p_<name>` in the wined3d sources leaves **79**
reachable, and most of those fall away on inspection (immediate mode, the `*EXT`
framebuffer aliases, the P8 palette path — the game creates no P8 textures).

**Caveat on that list, learned the hard way.** "`eglGetProcAddress` returned nil" is *not*
the same as "win32u's `p_<name>` is NULL" — win32u pre-resolves a large list of its own
and can supply an implementation the EGL query never sees. Several functions on the NULL
list (`glGetTexImage` in the FBO-compat probe, `glClearDepth` in the new-drawable path)
are on code paths that run at startup in *every* configuration, and startup does not
crash — so those particular pointers cannot actually be NULL. Treat the list as a
*candidate set to be narrowed*, never as proof on its own. `glDepthRange` is the one
member proven fatal by experiment, not by inference.

## Root cause: the fixed-function pipeline does not exist on GLES

This is the most important finding of the session and it reframes the project.

Reaching actual gameplay was attempted by driving the menus blind. Everything up to the level load works and **renders its text correctly**: title screen, WARNING dialog (after `Z`), NEW GAME, DIFFICULTY LEVEL, SELECT RADAR TYPE. After confirming the radar the screen goes black, frame rate rises to ~56 fps with CPU dropping to ~3 % (nothing left to draw), and then the process dies:

```
wine: Unhandled page fault on read access to FFFFFFFF at address 00000000
```

That signature is a call through a NULL function pointer. The reason is visible directly in win32u's own resolution log:

```
GL entry points resolved : 5256
resolved to NULL         : 3144
```

The NULL set is not arbitrary. It is precisely desktop OpenGL's fixed-function and immediate-mode API — `glBegin`, `glEnd`, `glVertex*`, `glColor*`, `glTexCoord*`, `glNormal*`, `glOrtho`, `glFrustum`, `glLoadMatrixd`, `glPolygonMode`, `glLightModel*`, `glMaterial*`, `glTexGen*`, `glTexImage1D`, `glGetTexImage`, `glNewList`/`glCallList`, `glRasterPos*`, `glRect*` and so on. **None of these exist in OpenGL ES**, so no amount of pre-resolving will ever populate them.

MGS2 is a Direct3D 8 title built on the fixed-function pipeline. WineD3D translates that through `ffp_gl.c`, which is written against exactly those entry points. Menus survive because they do not exercise the paths that call them; a real 3D scene does, and the first NULL call kills the process.

This also unifies the two symptoms. The blank WARNING dialog body and the crash on entering gameplay are both consequences of the same thing — the fixed-function path is unavailable — rather than two separate bugs. It explains why fonts, texture formats and V's Fix all came back clean: nothing was wrong with them.

**What this means for the fix.** The game cannot work by patching individual call sites; there are hundreds. WineD3D has to stop using the fixed-function GL path entirely and render everything through shaders. Wine already has that: `ffp_hlsl`, which the Vulkan adapter enables unconditionally (`adapter_vk.c` sets `d3d_info->ffp_hlsl = true`) while the GL adapter leaves it to the setting.

A first attempt with `WINE_D3D_CONFIG=ffp_hlsl=0x1` is recorded above: it removed the per-frame FFP errors (6106 → 49) but crashed even earlier, because it only replaces FFP *shader generation* — the `ffp_gl.c` state table stays installed and still issues `glLightModeli`, `glDisable(GL_LINE_STIPPLE)` and friends, all of which are NULL here. Making this work means enabling `ffp_hlsl` **and** preventing the legacy FFP state table from being selected on a GLES context. That is real WineD3D work, but it is now a well-defined target rather than guesswork, and it is the only path to actual gameplay.

Worth noting: presentation, thermals and the launcher are no longer what stands between this port and playability. This is.

## The gameplay crash is fixed by binary-patching dbg42

Since neither component rebuilds from source, the fix was applied directly to the working binary. `wined3d_dbg52_depthrange_nop.dll` is `dbg42` with **six bytes changed**, and it is now the launcher default.

The call site was located through the DWARF line table (`ffp_gl.c:1082` → `0x1013dc2b`) and confirmed three independent ways: two doubles are stored to the stack immediately before it, `glViewport` follows shortly after (`call *0x9b0(%ebx)`), and dbg42's line numbers match the tree (visible in its own `ffp_gl.c / 1212` log lines).

```
before:  1013dc2b:  ff 93 6c 05 00 00   call *0x56c(%ebx)      ; glDepthRange
after:   1013dc2b:  83 c4 10 90 90 90   add $0x10,%esp ; nop×3
```

The stack correction is not optional. The disassembly shows the compiler re-issuing `sub $0x10,%esp` after each call, which proves the `__stdcall` callee pops its 16 bytes; simply NOPing the call would have left ESP 16 bytes low and the following `sub` would have compounded it. Verified after patching: exactly 6 bytes differ, file size unchanged, the instruction disassembles as intended.

**Result, with all five menu steps individually verified by frame-hash change:**

| | dbg42 | dbg52 |
| --- | --- | --- |
| page faults | 1 (dies entering 3D) | **0** |
| navigation START → WARNING → NEW GAME → difficulty → radar | crashes partway | all five confirmed |
| time alive past the old crash point | 0 s | 80+ s at 26–35 fps |

The game still exits after roughly 100 s, but **cleanly** — no page fault. That is a different, later failure, not the one that was fixed.

An equivalent and cleaner fix exists in source for whenever the rebuild problem is solved: bridge the core slot onto the GLES entry point in win32u (`p_glDepthRange = gles_depth_range`, double→float), which is already written into `dlls/win32u/opengl.c`.

## Rendering is visually wrong, and that is the real remaining problem

Flagged by the user looking at the actual screen: on the title screen Snake's artwork is broken up and the frame carries heavy horizontal striping. This had been mistaken for MGS2's deliberate CRT-noise styling — it is not.

### Measured shape of the striping (do not re-derive this by eye)

Taken from a real title-screen capture, per-row:

* the affected rows are **not corrupted image data — they are a uniform fill**, exactly
  `(0, 16, 0)` for every pixel across the full 640-pixel width;
* the pattern is a strict **period of 4: two written rows, two filled rows**;
* the two filled rows of each group are byte-identical to each other.

So half the rows are never written, in pairs. That is the signature of a **vertical
stride / half-height problem**, not of a wrong colour format — a mis-decoded 16-bit
texture would give wrong *colours* on every row, not perfect content on half of them.

**Where it appears is equally diagnostic.** The Konami logo, the "Konami Computer
Entertainment Japan" card and the legal disclaimer render *perfectly* — clean edges,
correct colours, fully legible text. Striping appears only on screens with an animated
background (title, main menu, NEW GAME, RADAR), i.e. exactly where MGS2 plays a
background movie. The menu text and side panels drawn over it stay crisp.

**And the 16-bit converters make no difference to it.** Driving the same sequence with
`MGS2_GLES_CONV=1` and `MGS2_GLES_CONV=0` gives the same striped-row counts on every
comparable screen (3/480, 100/480, 3/480, 42/480 either way), and the one deterministic
screen in the sequence — the disclaimer — is byte-identical between the two.

Both facts point away from the format table and towards the video-surface upload path.
The format diagnosis below is still correct as far as it goes, but it is **not** the
cause of the striping.

### The missing title-screen picture is a deliberate patch, not a bug

The production executable **has PSS movie playback disabled**, and this had dropped out of
view. Verified byte-for-byte against the stock SSE build (`cmp -l` — 17 bytes differ in
total), the documented pair among them being:

```
mgs2_sse_rg353vs_port.exe  0x17D82F:  7d 1d  ->  90 90
```

which is `scripts/patch-pss-movie-skip.py`'s first patch: *"NewMpegPssMovieStr/GetResources:
always take the existing resource-error path. It destroys the movie actor and invokes its
end_proc callback."* The second documented patch (`0x47CD9B`, the DirectMusic spin) is
present too.

MGS2's title screen background **is** a PSS movie, and so are the cutscenes. With that
call forced down the error path there is nothing to draw, which is exactly the reported
symptom — no picture where START is pressed, and no cutscenes. **This is not a GLES or
WineD3D defect**; it is an earlier workaround still in force.

Also relevant: a full run to the main menu performs only **12 texture uploads**, none of
them to the 640×480 surface, all with correct row pitches (`1024×1024` at `pitch=4096`,
`1024×512` B4G4R4A4 at `pitch=2048`). There is no per-frame video upload happening at all,
which independently confirms no movie is being decoded.

A movies-enabled variant (`mgs2_sse_rg353vs_movies.exe`, the two PSS bytes reverted to
`7d 1d`, everything else identical) is on the device for testing, and `launch.sh` now
honours `MGS2_EXE` so it can be selected without touching the default:

```sh
MGS2_EXE=mgs2_sse_rg353vs_movies.exe ./launch.sh
```

**Tested, and reverting those two bytes is not sufficient.** The game boots, the whole
menu sequence navigates, nothing hangs — and frames 03 through 08 of the driven sequence
are indistinguishable from the movies-disabled run (identical uniform-row counts, mean
brightness within 0.7). So the movie still does not play; the patch was suppressing a
failure that is still there rather than causing one.

The assets are present and intact, so that is not the reason either:

```
cdrom.img/movie.dat   305 387 520
cdrom.img/demo.dat  1 481 459 712
```

#### What the movie code actually needs

The executable imports **no DirectShow at all** — `d3d8`, `DSOUND`, `DINPUT8`,
`kernel32`, `user32`, `advapi32`, `ole32`, `oleaut32`, `WINMM`, `MSACM32`. So the PSS
video decoder is built in, and the only external decoding dependency is **ACM for the
movie's audio track**: `acmFormatSuggest`, `acmStreamOpen`, `acmStreamSize`,
`acmStreamPrepareHeader`, `acmStreamConvert`. The nearby string `mpegstrx.c` confirms the
translation unit.

Disassembling the patch site (file `0x17D82F` = VA `0x57D82F`):

```asm
57d824:  mov    0x188(%esi),%eax     ; result field of the preceding call
57d82a:  add    $0x38,%esp
57d82d:  cmp    %ebx,%eax            ; ebx = 0
57d82f:  jge    0x57d84e             ; PATCHED to nop;nop -> always fall through
57d831:  push   %esi
57d832:  call   0x8cea10             ; tear the movie actor down
...
57d84e:  mov    %esi,0xa18e34        ; both paths converge here
```

So the field at `+0x188` is a signed result: negative means "resources not acquired", and
the patch forces the teardown regardless.

#### Found: the prefix has no ACM codecs registered at all

`msacm32` enumerates its drivers from
`HKLM\Software\Microsoft\Windows NT\CurrentVersion\Drivers32` (and the `Wow6432Node`
view for a 32-bit process). **Both keys in this prefix are empty**, while the codec
binaries are all present:

```
imaadp32.acm  l3codeca.acm  msadp32.acm  msg711.acm  msgsm32.acm
```

With nothing registered, `acmFormatSuggest()` can find no decoder for any format, which
is exactly the kind of failure that would leave `+0x188` negative. `scripts/reg_acm.py`
writes the standard entries into both views (run with wineserver stopped; it backs the
file up to `system.reg.bak-acm` and refuses to run if wineserver is alive):

```
"msacm.imaadpcm"="imaadp32.acm"   "msacm.msadpcm"="msadp32.acm"
"msacm.msg711"="msg711.acm"       "msacm.msgsm610"="msgsm32.acm"
"msacm.l3acm"="l3codeca.acm"      "wavemapper"="msacm32.drv"
```

This is worth keeping regardless of the movie outcome — a prefix with no wave mapper and
no ACM codecs is broken for ordinary sound playback too.

**But it did not, on its own, bring the movie back.** With the codecs registered *and* the
movies-enabled executable, a driven run to the main menu produced a texture census
**byte-identical** to the baseline: 142 creations, identical shapes, no new surfaces.

There is a gap in that test worth naming, because it invalidates the conclusion rather
than the fix: **the driven sequence stops at the legal disclaimer, and the first real
cutscene comes after it.** So these runs may never have called `NewMpegPssMovieStr` at
all. Testing "movies enabled" without reaching a movie proves nothing either way. Use
`scripts/drive2.sh`, which continues past the disclaimer.

The same caveat applies to the title-screen background. Movies-on versus movies-off gives
statistically identical menu frames, but that is equally consistent with "the backdrop is
not a movie" and with "the movie fails" — the two have not yet been separated.

### Text rendering is not broken

Directly contradicted by measurement: the disclaimer screen renders its full sentence,
and every menu label ("NEW GAME", "SELECT RADAR TYPE", "SNAKE TALES") is legible. Any
explanation of missing dialog text that relies on a broken font atlas or a broken
luminance format has to account for this first.

**It is not caused by the presentation driver.** A direct A/B of the same screen through `winewayland_pbo1.so` and the older `winewayland_gbmshm_directbgra1.so` produces identical corruption, so the rebuilt presentation path is exonerated and the damage happens earlier, while the game draws.

### Diagnosis: three of the four formats MGS2 needs are unhandled on GLES

`init_format_texture_info()` in `utils.c` has exactly one GLES fixup, for `WINED3DFMT_B8G8R8A8_UNORM`. Reading the table rows against what GLES actually accepts:

| D3D format | GL format / type in the table | on GLES |
| --- | --- | --- |
| `B8G8R8A8_UNORM` | `GL_BGRA` / `GL_UNSIGNED_INT_8_8_8_8_REV` | invalid — **already fixed** by the `is_gles` branch |
| `B5G5R5A1_UNORM` | `GL_BGRA` / `GL_UNSIGNED_SHORT_1_5_5_5_REV` | **invalid, unhandled** |
| `B4G4R4A4_UNORM` | `GL_BGRA` / `GL_UNSIGNED_SHORT_4_4_4_4_REV` | **invalid, unhandled** |
| `B8G8R8X8_UNORM` | `GL_RGBA` / `GL_UNSIGNED_BYTE` | accepted, but the data is BGRX so **R and B are swapped** |
| `B5G6R5_UNORM` | `GL_RGB` / `GL_UNSIGNED_SHORT_5_6_5` | fine |

`GL_BGRA` and the `_REV` packed types do not exist in GLES at all, so those uploads fail and the texture keeps undefined contents. The two 16-bit formats are exactly what a 2001 PS2-era port uses for background artwork, which matches the symptom precisely: 32-bit assets (the logo, menu text) are crisp while the artwork behind them is garbage.

This also supports treating the blank WARNING body text and the corrupted artwork as **one defect rather than two**, and explains why fonts, format fixmes and V's Fix each came back clean when tested on their own — none of them was the layer at fault.

**A binary patch is not sufficient here.** Swapping the tokens in the static table to `GL_RGBA` / `GL_UNSIGNED_SHORT_5_5_5_1` would make the upload legal but wrong: D3D puts alpha in the high bit and GLES `5_5_5_1` puts it in the low bit, so the channels would be misordered. A correct fix needs a conversion function on upload, mirroring `convert_b8g8r8a8_unorm_gles`, which means compiled code.

### Partial breakthrough: GLES was being classified as a legacy context

External research identified the likely gap, and the source confirms it. `adapter_gl.c` had an asymmetry:

```c
d3d_info->ffp_alpha_test = !gl_info->is_gles && !!gl_info->supported[WINED3D_GL_LEGACY_CONTEXT];
...
if (context_profile & GL_CONTEXT_CORE_PROFILE_BIT) TRACE("Got a core profile context.\n");
else gl_info->supported[WINED3D_GL_LEGACY_CONTEXT] = TRUE;      /* GLES lands here */
```

Someone had already shielded `ffp_alpha_test` from GLES but not the classification itself. Core versus compatibility profile is a desktop-GL concept; GLES has neither, so `GL_CONTEXT_PROFILE_MASK` returns nothing and a GLES context gets marked **legacy**. That is not a cosmetic flag — the legacy path installs fixed-function state handlers that call desktop-only entry points which are NULL here. A GLES 3.x context behaves like a core profile, so it is now classified as one:

```c
if (gl_info->is_gles)
    TRACE("GLES context, treating as core profile.\n");
else
    { /* existing GL_CONTEXT_PROFILE_MASK logic */ }
```

This matches a patch the notes say existed in the original, lost tree, which makes it a strong candidate for part of what dbg42 contained.

**Measured effect (`dbg56`):** the per-frame fixed-function error flood is gone — total wined3d errors for a whole run dropped from ~6 100 to 97, and `glAlphaFunc` fell from a continuous stream to 2 calls during initialisation only. Also worth recording: `glAlphaFunc` itself resolves **non-NULL** (`0x400202e0`), so it was never the fatal call, only the loudest symptom.

**Still not enough.** The rebuild continues to die before the title. Execution now gets further: the `rasterizer` state handler completes in full (`glFrontFace`, `depthbias`, `fillmode`, `cullmode`, `depth_clip`, `scissor`, `line_antialias` all log), and the crash follows it. Remaining errors are all one-time capability probing (`draw quad`, post-pixelshader blending, framebuffer setup). Whatever NULL entry point is fatal now is called after rasterizer state is applied and produces no GL error first.

### Narrowing the remaining rebuild crash — and a tracing pitfall

Guessing which NULL entry point is fatal was replaced with measurement: instrument the
state-application loop in `context_gl.c` and log each `state_id` before and after its
handler runs, then bisect by whichever `enter` has no matching `ok`.

That worked and eliminated a whole class. Result:

- all 38 state handlers complete (`ok` for every `enter`), so **no state handler is fatal** —
  including every `ffp_gl.c` one;
- execution proceeds through `bind_shader_resources` 0–4 and `check_fbo_status`;
- the last marker is `shader_apply_draw_state enter`, i.e. the crash is at or inside
  `shader_glsl_apply_draw_state()`, on the very first draw.

Dumping the pointers at that call site shows they are **all valid** (`backend=7A4FC9E0`,
`fn=7A396A50`, `priv=02B89928`), so it is not a NULL vtable entry; the fault is inside the
function.

**Pitfall, and the reason the localisation stops there.** Markers placed inside
`shader_glsl_apply_draw_state` never appear at all, which would imply a crash before its
first statement — impossible. The give-away is that the pointer dump printed **twice**
while the immediately following `enter` printed **once**, although the two are adjacent
statements. Wine's `ERR` output through box86 into a redirected file is buffered and
**loses its tail when the process dies**, so "the last line in the log" is not "the last
thing that executed".

Anyone continuing must trace with something that flushes per line — the project already
has the right pattern in `mgsdbg_log()` (`fopen`/`vfprintf`/`fclose` per call, used by the
presentation driver). Slow, but it does not lie about where execution stopped.

### The rebuild blocker is SOLVED — but the rebuild renders wrong

Once tracing was switched to the unbuffered `mgs_trace()` pattern, localisation took three
steps and found it: `shader_glsl_update_graphics_program()` calls **`glBindFragDataLocation`
unguarded** while linking every program. GLES has no such entry point — fragment outputs
are bound with `layout(location=)` in the shader — so the pointer is NULL and the first
link jumps to zero. Skipping it on GLES (both call sites) gives **0 page faults** where
there was always exactly one, and execution runs on past the first draw.

Three source fixes together make a rebuild survive:

1. `adapter_gl.c` — classify a GLES context as core profile, not legacy.
2. `ffp_gl.c` — `glDepthRange` → `glDepthRangef`, else skip.
3. `glsl_shader.c` — skip `glBindFragDataLocation` on GLES.

**However the rebuild is still not usable as a replacement.** `dbg64` (all three fixes plus
the texture conversions below) runs and never crashes, but renders incorrectly: the title
logo is scaled up and cropped, the background artwork is missing entirely, and
`PRESS START BUTTON` does not appear. That is worse than the binary-patched `dbg52`, which
renders the screen correctly, so **dbg52 remains the launcher default**.

The scaling strongly suggests the viewport/projection path changed. `ffp_gl.c` has both
`viewport_miscpart` and `viewport_miscpart_cc` (clip-control) variants and the state table
picks between them; forcing the context to core profile plausibly selected a different one.
That is the first thing to check.

The disappearing elements have a separate plausible cause worth testing before anything
else: if the game's 16-bit textures are really `X1R5G5B5` rather than `A1R5G5B5`, the
unused X bit is zero, and rotating it into the alpha position yields **alpha = 0**, i.e.
fully transparent instead of striped. That would explain content vanishing rather than
improving.

### Texture format conversions (written, not yet validated)

Implemented in `utils.c` alongside the existing `convert_b8g8r8a8_unorm_gles`, following the
research recommendations:

| format | GL format / type | conversion |
| --- | --- | --- |
| `B5G5R5A1_UNORM` | `GL_RGBA` / `GL_UNSIGNED_SHORT_5_5_5_1` | 16-bit rotate left by 1 (right by 1 on download) |
| `B4G4R4A4_UNORM` | `GL_RGBA` / `GL_UNSIGNED_SHORT_4_4_4_4` | 16-bit rotate left by 4 (right by 4 on download) |
| `B8G8R8X8_UNORM` | `GL_RGBA` / `GL_UNSIGNED_BYTE` | reuse the 8888 byte swap |

Both rotations keep two bytes per texel and preserve precision, so no expansion to RGBA8 is
needed. They cannot be evaluated until the rendering regression above is resolved.

### Consequence: the rebuild blocker is now the critical path

Everything still outstanding — the three texture formats, and the clean source version of the depth-range fix — requires building wined3d, and no build from the tree is usable. Solving that is worth more than any further individual fix. What is known about it:

- the toolchain is faithful: the unmodified tree reproduces `dbg45_profile.dll`'s size exactly;
- `dbg51` (tree minus the profiling block, nothing else) is still 8 045 bytes larger than `dbg42` and dies before the title;
- the difference is **one single function**. Comparing text-section symbol tables, dbg42 has 4 193 and a rebuild has 4 192, and the only entry dbg42 has that no rebuild produces is `_shader_glsl_add_version_declaration.isra.0`. Every other function matches by name.

The `.isra.0` suffix is GCC cloning a function whose parameter became unused, which says dbg42's version of `shader_glsl_add_version_declaration()` ignores its `gl_info` argument — i.e. it emits the GLES header **unconditionally** rather than testing `is_gles`. That was tried (`dbg54`) and still dies before the title, as did the conditional form (`dbg53`), so matching that one function is necessary but not sufficient. Something outside the symbol table still differs.

**Do not use the fault address as an identifier.** `returning to user mode ip=79d32476` appears for the unpatched `dbg42` crash *and* for every failing rebuild, including one where the `glDepthRange` call had provably been removed from the source (the `depth clip` log line shifts from `ffp_gl.c / 1212` to `/ 1221`, so the patch was definitely compiled in). That address is a shared opengl32/win32u thunk that any NULL GL entry point lands on — identical addresses mean "some missing GL function", not "the same one". An hour was lost to reading it the other way.

The last d3d line before a rebuild dies is consistently `GL_INVALID_OPERATION from glAlphaFunc @ glsl_shader.c / 12017` — desktop-only alpha test, which GLES does not have. That is the best remaining lead on what dbg42 guards and the tree does not.

Attempts so far, all dying before the title: `dbg47`/`dbg48`/`dbg49` (tree + GLES shims), `dbg50` (tree as found), `dbg51` (tree minus profiling), `dbg53` (conditional GLES header only), `dbg54` (unconditional GLES header only). Worth noting for whoever continues: the shims in dbg47–49 were themselves wrong — they rerouted `glDrawBuffer` to `glDrawBuffers` on the assumption it was broken, when only `glDepthRange` is.

## RESOLVED: there is no lost dbg42 source — the tree already matches it

**The section below is superseded.** Its premise — that `dbg42` contains GLES rendering
work missing from the tree — was tested directly and is **false**. Read this first; the
next section is kept only for the method it records.

The test was a semantic diff of the two PE binaries, which had never been done properly
(only *text* symbol names had been compared). Three passes, each narrowing the space:

**1. Data tables — identical.** Every initialised data symbol was dumped with pointer
words resolved to `symbol+offset`, so the two different layouts become comparable. Of
~4 655 data symbols, the only content differences are GUIDs and tables of string pointers
(pure normalisation noise) — plus compiler-generated `CSWTCH`/`__func__` renumbering.
`format_texture_info` in particular is **byte-identical**: 125 records, all 12 fields.
So dbg42 carries no format-table work of any kind.

**2. Function bodies — 4 193 functions, 3 911 identical.** Of the 281 that differ, only
**19** change size at all.

**3. Call sets — 14 functions differ, and 13 of those are my own instrumentation.**
The fourteenth is the whole story:

| | dbg42 | rebuild |
| --- | --- | --- |
| `shader_glsl_add_version_declaration` | out-of-line `.isra.0`, called from 10 sites | inlined to one `shader_addline` |

Disassembling dbg42's copy and reading its string operands out of `.rdata` gives exactly:

```
"#version 300 es\n"  "precision highp float;\n"  "precision highp int;\n"
```

— the same three strings the tree emits today, merely as three `shader_addline` calls
gated on `is_gles` instead of one unconditional call. **The generated GLSL is byte-for-byte
the same.** That is the sole surviving difference, and it is cosmetic.

The remaining 262 differing functions differ only in immediate constants of the form
`0x515` → `0x519`, i.e. `__LINE__` shifted by my own edits, and in `.rdata` string offsets.
Register allocation accounts for the rest.

### So why did rebuilds look worse?

Almost certainly **my own tracer**. The unbuffered `fopen`/`vfprintf`/`fclose`-per-call
tracer that made the crash hunt possible was left in place, and it sits on the per-draw
path: 7 calls in `shader_glsl_apply_draw_state` and 7 in the context's draw-state apply,
so roughly **13 file opens per draw call**. That is enough to starve rendering into
something that looks exactly like a rendering bug — especially when judged by the
frame-size metric, which the previous round had already found unreliable.

All three tracers are now gated and off by default:

| switch | default | effect |
| --- | --- | --- |
| `MGS2_TRACE=1` | off | per-draw unbuffered trace (crash hunting only) |
| `MGS2_TEXLOG=1` | off | one line per texture creation (format census) |
| `MGS2_GLES_CONV=0` | on | disable the 16-bit / X-channel GLES converters |

The last one exists so a single build can A/B the unproven converters, rather than
shipping them as an untested default.

### Measured: the rebuild renders identically to the reference

`wined3d_dbg70_gated.dll` (the tree, tracers gated off) against
`wined3d_dbg52_depthrange_nop.dll` (the reference), nine captures each at the same
five-second offsets:

| offset | ref52 | new70 conv=0 | new70 conv=1 |
| --- | --- | --- | --- |
| t+5 … t+35 | `74cf8d90` | `74cf8d90` | `74cf8d90` |
| t+40 | `d342f7a1` 24 383 B | `d342f7a1` 24 383 B | `d342f7a1` 24 383 B |
| t+45 | `81094011` 13 414 B | `81094011` 13 414 B | (attract-loop phase) |

**Byte-identical MD5s at every offset.** The rebuild is a drop-in equal of the reference,
and the converters change nothing on this part of the sequence.

Two things worth knowing from those frames, both contradicting earlier assumptions:

* the Konami logo renders **perfectly** — clean edges, correct colours;
* the following title card, **"Konami Computer Entertainment Japan", renders as crisp
  white text with a red J**. Text rendering is therefore *not* systemically broken, which
  rules out the whole class of font-atlas explanations for the missing dialog text.

**Consequence:** the rebuild path is not blocked. Texture conversions — which need
compiled code and were the reason the striping could not be fixed — are deliverable.

## The wined3d source tree cannot rebuild dbg42 (superseded — see above)

The gameplay crash was pinpointed exactly, the fix is one line, and it still cannot be delivered — because **the source that produced the working `wined3d_dbg42_gles_present.dll` is lost**. This was established by control experiment, not inference:

| build | contents | size | result on device |
| --- | --- | --- | --- |
| `dbg42` (prebuilt, July) | unknown source | 25 154 427 | **works** — title, menus, 26–34 fps |
| `dbg50_control` | tree exactly as found | 25 162 749 | dies before title |
| `dbg51_noprof` | tree, profiling removed, **no other edits** | 25 162 472 | **dies before title** |
| `dbg47` / `dbg48` / `dbg49` | tree + my GLES fixes | ~25 170 000 | die before title |

The decisive row is `dbg51`: an unmodified rebuild crashes too, so none of the added fixes are at fault.

`dbg50_control` reproduced `wined3d_dbg45_profile.dll`'s size **exactly** (25 162 749), which proves two things: the MinGW toolchain builds this tree faithfully, and **the tree on disk is dbg45's source** — the build the handoff already marks as broken. dbg42 predates it, and whatever it contained was overwritten. `dbg51` is still 8 045 bytes larger than dbg42, so the divergence is more than the profiling block.

One genuinely missing piece was found and restored along the way: `shader_glsl_add_version_declaration()` in `glsl_shader.c` had been reverted to upstream, losing the GLES shader header. GLSL ES needs `#version 300 es` plus an explicit `precision highp float/int`, without which the Mali compiler rejects every generated shader. Restoring it brought string parity with dbg42 (`#version 300 es` ×3, `precision highp` ×2) but did not make the build viable, so more is still missing.

### win32u cannot be rebuilt either

The same attempt was made on the other side, because the NULL actually lives in win32u, and it failed the same way. Every rebuild produces `Failed creating Direct3D8 Object.` — captured from the otherwise-blank Wine MessageBox via the relay trick below.

| build | contents | D3D8 creation |
| --- | --- | --- |
| `win32u_glfuncs3.so` (prebuilt) | unknown source | **works** |
| `win32u_depthbridge1.so` | pre-resolve list + 3 EGL fixes + depth bridge | fails |
| `win32u_depthbridge2.so` | same, duplicate-attribute fix | fails |
| `win32u_minimal3.so` | pre-resolve list + depth bridge only | fails |

Ruled out along the way, each by measurement rather than reasoning: duplicate `EGL_CONTEXT_MAJOR_VERSION` attributes, the three EGL patches themselves, and a configure difference (`vulkan`, `freetype`, `fontconfig` string counts are identical between the prebuilt and the rebuild — 158/5/0 either way). The rebuild is 47 740 bytes smaller than the prebuilt, so the prebuilt genuinely contains more code that is not in the tree.

**One thing was fully recovered and is worth keeping.** The exact pre-resolve list — the patch whose loss the handoff already flagged — was reconstructed from the deployed win32u's own resolution log rather than from memory: subtract upstream `ALL_GL_FUNCS` (336 entries) from what the device logs as resolved (438 unique) and exactly **102** extra names remain. That list is now in `dlls/win32u/opengl.c`, along with the depth bridge:

```c
if (!display_funcs.p_glDepthRange && display_funcs.p_glDepthRangef)
    display_funcs.p_glDepthRange = gles_depth_range;   /* double -> float */
```

Both are correct and should survive whenever the rebuild problem is solved; they are simply not deliverable today.

### Reading the blank MessageBox

The dialog text is invisible on this setup, but it can be read with a relay trace. Add to `HKCU\Software\Wine\Debug` in the prefix:

```
"RelayInclude"="user32.MessageBoxA;user32.MessageBoxW;user32.MessageBoxExA;user32.MessageBoxExW"
```

then run with `WINEDEBUG=+relay` and grep for `MessageBox`. It prints the strings directly:

```
Call user32.MessageBoxExA(...,"Failed creating Direct3D8 Object.","METAL GEAR SOLID 2:SUBSTANCE",...)
```

Remove the key afterwards — `+relay` slows the game considerably.

### Where the crash actually is

Confirmed by SEH trace (`ip=00000000`, i.e. a jump to NULL) with `ffp_gl.c` as the last active code:

```
ffp_gl.c:1082   gl_info->gl_ops.gl.p_glDepthRange(min_z, max_z);
```

This is the single-viewport branch of the viewport state handler, so it runs the moment a 3D scene sets its viewport — which is exactly when the game dies. `glDepthRange` takes doubles and is desktop-core-only; GLES has `glDepthRangef`.

An important subtlety for whoever picks this up: **do not guard on the function pointer**. `gl_ops.gl.p_*` entries are opengl32 thunks and are always non-NULL, even here — the NULL lives one level down in win32u. `if (p_glDepthRange)` passes, calls the thunk, and still dies. The correct test is `gl_info->is_gles`, which this tree already provides.

### Options from here

1. **Binary-patch dbg42.** It is unstripped, so the indirect call in the viewport handler can be located and NOPed. Surgical, keeps the known-good base, no rebuild needed. Most promising.
2. **Recover dbg42's source.** Nothing on disk identifies what changed between dbg42 and dbg45 beyond the profiling block; would need bisecting against the binary.
3. **Avoid the FFP viewport path entirely** via `ffp_hlsl`. Tried: `WINE_D3D_CONFIG=ffp_hlsl=0x1` removes the per-frame FFP errors (6106 → 49) but crashes earlier, because `ffp_gl.c`'s state table stays installed regardless.

## Presentation: measured results

`winewayland_pbo1.so` is now built from restored source, deployed, and instrumented. It replaces `winewayland_gbmshm_directbgra1.so` as the default.

An asynchronous pixel-pack-buffer readback path was implemented to remove the `glReadPixels()` stall. **It was measured and rejected**, and is now off by default. Same scene, 300-frame samples:

| Setting | fps | readback | map + copy |
| --- | --- | --- | --- |
| `MGS2_GL_PBO=0` (synchronous, **default**) | 23.4–43.6 | 4.9–6.2 ms | 0.00 ms |
| `MGS2_GL_PBO=1` (async PBO) | 10.7–12.5 | 0.09 ms | 23.8 ms |

The PBO does exactly what it promises — the readback stops blocking and falls to 0.09 ms — but Mali hands back the mapped pack buffer as uncached memory, so reading 1.2 MB out of it costs far more than the 5–6 ms the direct read cost. The code is kept behind the flag: it is the right shape if a future driver maps cached, and it is how these numbers were produced. Do not enable it without re-measuring.

**Two earlier assumptions turned out to be wrong:**

1. The ~14.2 ms figure for presentation came from an unstable sample. The real synchronous readback is **4.9–6.2 ms**. At ~23 fps the frame is ~42 ms, so presentation is roughly **12 % of it**. Presentation was never the dominant cost, and further frame-rate work belongs in x86 emulation / game logic / WineD3D, not here.
2. The rotating wl_shm buffer pool gives no measurable benefit (25.0 fps with one buffer vs 23.5 with three — inside thermal drift). Default is 2, purely to avoid dropping a frame while the compositor holds one.

`MGS2_GL_FLIP=0` is correct and confirmed on the device: the WineD3D FBO path already delivers the image top-down, so flipping again mirrors it. This also explains the old `winewayland_gbmshm_noflip1.so` artifact name.

| Variable | Default | Meaning |
| --- | --- | --- |
| `MGS2_WAYLAND_SO` | `winewayland_pbo1.so` | driver to mount; falls back to `winewayland_gbmshm_directbgra1.so` if absent |
| `MGS2_GL_PBO` | `0` | `1` enables the async path (measured slower — see above) |
| `MGS2_GL_PBOS` | `2` | number of pixel-pack buffers (2–3) |
| `MGS2_GL_FLIP` | `0` | `1` flips vertically (mirrors the image on this stack) |
| `MGS2_GL_BGRA` | `1` | `0` reads RGBA and swizzles on the CPU |
| `MGS2_GL_SHM_BUFFERS` | `2` | size of the shm pool (1–4) |
| `MGS2_GL_STATS` | `0` | log fps / readback / copy every N frames |

Stats go through Wine's `err` channel, which the launcher's `WINEDEBUG=-all` suppresses. To measure:

```sh
WINEDEBUG=-all,err+waylanddrv MGS2_GL_STATS=300 ./launch.sh
```

This replaces the unstable `wined3d_dbg45_profile.dll`: it costs two `clock_gettime()` calls per frame and does not crash.

## Build capability restored

The i386 Unix-side sources for `win32u.so` and `winewayland.so` had been lost; only the binaries survived, so neither could be changed. That is fixed:

- `recovered-session/sysroot32/` — i386 sysroot rebuilt from `apt-get download` + `ar x`, no root required.
- `recovered-session/scripts/build-env-i386.sh` — the environment; documents the two non-obvious patches it needs (hand-written `libc.so` ld scripts with absolute sysroot paths, and the multilib headers living under `x86_64-linux-gnu` because `gcc -m32` looks for a non-existent `/usr/include/i386-linux-gnu`).
- `recovered-session/build-wine-unix32/` — configured with `--enable-archs=i386 --with-wayland --with-opengl`.

```sh
cd recovered-session && source scripts/build-env-i386.sh
cd build-wine-unix32 && make dlls/winewayland.drv/winewayland.so
```

The older `recovered-session/build-wine-i386/` is a **PE-only** tree (`--without-wayland --without-opengl`); it builds `wined3d.dll` through MinGW and cannot build the Unix `.so` files.

`dlls/winewayland.drv/opengl.c` is now reconstructed in source. **`dlls/win32u/opengl.c` is still pristine upstream** — the deployed `win32u_glfuncs3.so` works, but rebuilding it would silently lose several fixes that are binary-only today: the large pre-resolved GL entry-point list, the `EGL_DEFAULT_DISPLAY` override in `init_egl_platform`, acceptance of `EGL_OPENGL_ES2/ES3` config bits, and the `EGL_CONTEXT_MAJOR_VERSION 3` default in context creation (without which EGL hands back a GLES 1.1 context). Do not rebuild `win32u.so` before restoring those.

## Rejected or inconclusive experiments

| Experiment | Result |
| --- | --- |
| Rebuild box86 solely for missing GL symbols | Rejected. The symbols were already present; box86 was not the original NULL-proc cause. |
| `d3d8=builtin` (bypass V's Fix d3d8→d3d9) | Rejected. The game opens `Critical error` before rendering. Native local `d3d8.dll` is required. |
| Stock RockNix `winewayland` / direct EGL | Rejected for now: EGL surface exists, but `wglMakeCurrent` faults. Proper zero-copy EGL needs box86 Wayland ABI work. |
| Stock RockNix box86 | Rejected. It cannot relocate the emulated `libwayland-client.so.0` because `open_memstream` is missing. `box86-clean1` carries the necessary compatibility change. |
| `BOX86_DYNAREC_BIGBLOCK=3` | Rejected. Wine exits with code 255. Keep `BIGBLOCK=2`. |
| pthread shim | Rejected. It caused mapping failures after reboot and did not solve winepulse. |
| Instrumented rebuilt `wined3d_dbg45_profile.dll` | Rejected. It logged a first sample but crashed after five frames; never deploy it as production. |

## Performance evidence and thermal status

Measured with `MGS2_GL_STATS=300` on the current default configuration:

- Steady state ranges roughly **20–43 fps**, typically 23–25, with bursts to ~42 on light scenes.
- Readback is a stable **4.9–6.2 ms/frame** regardless of scene, i.e. ~12 % of a 42 ms frame. The remaining ~88 % is x86 emulation, game logic and WineD3D — that is where any further gain has to come from.
- A running game plus Wine processes can consume over two CPU cores.
- Hardware trip points observed: roughly 83 C, 88 C and 95 C. Duplicate launches previously caused temperatures above 92 C and the console has reset under load.

The progressive thermal policy has now been observed doing its job. During level loading the SoC reached 84.4 C and the guard stepped the cap down rather than killing anything:

```
Fri Jul 31 16:57:04 EDT 2026: 84444mC -> cap 1416000
```

Temperature then settled at ~82.8 C and the game kept running at ~20 fps. Under the old policy nothing would have happened until 90 C, at which point the game was simply killed. Across the whole session there was **no console reset**, which is the failure that previously blocked testing.

**The Wine prefix was lost and had to be re-initialised** at the start of this session (`wineboot --init` runs `setupapi InstallHinfSection wine.inf`, which takes several minutes under emulation). Game files were unaffected. The archived `recovered-session/device-artifacts/user.reg` still holds settings the fresh prefix does not — `[Software\Wine\Direct3D] "renderer"="gl"`, `[Software\KONAMI\MGS2S]`, and font/codepage entries that may be related to the blank MessageBox text. These have **not** been restored yet; do that if renderer selection or in-game text misbehaves.

## Test launchers (not production)

- `launch-builtin-d3d8-test.sh` — bypassed D3D8 proxy; known failure.
- `launch-stockegl-test.sh` — stock Wayland EGL trial; known failure.
- `launch-stockbox-test.sh` — stock box86 trial; known failure (`open_memstream`).
- `launch-profile-test.sh` — uses unstable `dbg45`; do not run.
- `launch-stable-test.sh` — stable dbg42 path with 1608 MHz / 80 C test guard; the only appropriate next test launcher.

## The three open problems, in the order they should be attacked

Everything else in this document is either fixed or disproven. What remains:

### Exactly which entry points wined3d holds (measured, `MGS2_MANIFEST=1`)

```
PTR glClearDepthf              00000000     PTR glDrawBuffers      79D22630
PTR glDepthRangef              00000000     PTR glBindFramebuffer  79D08960
PTR glTexStorage2D             00000000     PTR glBlitFramebuffer  79D0C720
PTR glReleaseShaderCompiler    00000000
PTR glGetShaderPrecisionFormat 00000000
PTR gl.glClearDepth  79D0F040   PTR gl.glGetTexImage  79D40950
PTR gl.glDepthRange  79D205D0   PTR gl.glPolygonMode  79D6BD60
```

Read this carefully, because it settles several arguments at once:

* ordinary **extension** functions resolve fine — the GL loader is not broken;
* every **ARB_ES2_compatibility** function is NULL, and they are all core GL 4.1;
* the `gl.*` entries are non-NULL, which means nothing — they are the opengl32 thunks,
  and the NULL that actually kills the process lives one level below them, in win32u.

Two candidate explanations were tested and eliminated:

1. *"opengl32 doesn't export them."* It does not export them as symbols (only the GL 1.1
   `glClearDepth` is an export), so wined3d was given a fallback to
   `GetProcAddress(opengl32, name)` — **measured, no change**, all still NULL.
2. *"opengl32 doesn't know the names."* It does: `glClearDepthf`, `glDepthRangef`,
   `glTexStorage2D`, `glDrawBuffers` are all present in its string table.

So `wglGetProcAddress` is returning NULL because **win32u below it never resolved those
entry points** — which is the pre-resolve-list gap, now confirmed from the wined3d side
rather than assumed.

## SOLVED: Wine's Unix opengl32 misparses a GLES version string

The single highest-value finding of the project, and it was in a module nobody had looked
at. `dlls/opengl32/unix_wgl.c`:

```c
static const char *parse_gl_version( const char *gl_version, int *major, int *minor )
{
    const char *ptr = gl_version;

    *major = atoi( ptr );              /* "OpenGL ES 3.2 ..." -> 0 */
    if (*major <= 0)
        ERR( "Invalid OpenGL major version %d.\n", *major );
```

and the caller:

```c
if (!ctx->major_version) ctx->major_version = 1;   /* falls back to GL 1.x */
```

A GLES driver reports `GL_VERSION` as `"OpenGL ES 3.2 ..."`. `atoi()` on a string starting
with a letter returns 0, so **Wine believes the context is OpenGL 1.x**. The extension gate
then refuses every entry point whose registry requirement is `GL_VERSION_3_x`:

```c
if (ctx->major_version > major || (ctx->major_version == major
        && ctx->minor_version >= minor)) return TRUE;
```

This explains three things that had looked unrelated: `glClearBufferfv` (core since GL 3.0)
refused, `glBlendEquation` refused, and `glDrawBuffers` accepted — the last because an
*extension* name vouches for it rather than a version.

**The earlier diagnosis in this document — "win32u gates on desktop extension strings" —
was half right and named the wrong module.** The refusal happens in the Unix side of
opengl32, and unlike win32u **that one builds**: `dlls/opengl32/opengl32.so` is a target in
the same `build-wine-unix32` tree that already produces `win32u.so` and `winewayland.so`.

Fix — skip the prefix so the real version is parsed:

```c
if (!strncmp( ptr, "OpenGL ES-CM ", 13 )) ptr += 13;
else if (!strncmp( ptr, "OpenGL ES ", 10 )) ptr += 10;
```

Measured effect, same probe before and after:

| entry point | before | after |
| --- | --- | --- |
| `glClearBufferfv` | `00000000` | **`79D0E840`** |
| `glClearBufferfi` | `00000000` | **`79D0E730`** |
| `glBlendEquation` | `00000000` | **`79D0B490`** |
| `glBlendColor` | `00000000` | **`79D0B140`** |
| `glClearDepthf` / `glDepthRangef` | `00000000` | `00000000` |
| `glTexStorage2D` | `00000000` | `00000000` |

The remainder stay NULL exactly as expected: they are core in GLES 2.0/3.0 but only reached
desktop GL at **4.1/4.2**, so a correctly-parsed 3.2 still fails their requirement. Closing
that gap needs GLES-core command membership in the gate (generate it from Khronos `gl.xml`)
rather than another parser tweak.

Deployed as `opengl32_glesver1.so`, selected with `MGS2_OPENGL32_SO` (empty = stock), bind
mounted and unmounted alongside the others.

Consequences worth acting on:

* the emulated depth-clear quad is no longer needed — the code already prefers
  `glClearBufferfv` when it resolves, so it now takes the real path;
* the `glBlendEquation` workaround becomes redundant (harmless, and still correct if the
  patched opengl32 is not mounted);
* `state_blend_factor()` currently returns early on `is_gles` because `glBlendColor` was
  NULL; that guard should become a pointer check now that it resolves.

### The depth clear cannot be set at all — every spelling is refused (superseded by the above)

Probed directly with `wglGetProcAddress` from inside wined3d, all eleven return NULL:

```
glClearDepthf   glClearDepthfOES   glClearDepthx   glClearDepthxOES
glDepthRangef   glDepthRangefOES   glDepthRangex   glDepthRangexOES
glClearBufferfv glClearBufferfi    glInvalidateFramebuffer
```

The pointers exist — `eglGetProcAddress` hands out `glClearBufferfv` at `0x40020e70`,
`glClearDepthf` at `0x40020ec0`, `glDepthRangef` at `0x40020eb0`. They are simply not
reachable from the PE side. `wglGetProcAddress` in opengl32 is a thin wrapper that asks
the unix side for an *index* and returns NULL on `-1`, so the refusal happens in win32u,
which gates names on the desktop extension strings a GLES context never advertises.
(`glDrawBuffers` passes, which is why MRT works — GLES does advertise its extension.)

Exports are not a way round it either: `opengl32.dll` exports **361** names, the GL 1.1
set plus wgl. Adding `USE_GL_FUNC(glClearBufferfv)` to wined3d's loader was tried and
changes nothing, because the gate is below.

### Workaround shipped for the depth clear

Waiting for a win32u rebuild is not necessary for this particular call. GL's default
clear depth is already `1.0`, which is what D3D content asks for essentially always, so
the call can simply be omitted at that value instead of jumping to NULL:

```c
if (gl_info->gl_ops.ext.p_glClearDepthf)
    GL_EXTCALL(glClearDepthf(depth));
else if (!gl_info->is_gles)
    gl_info->gl_ops.gl.p_glClearDepth(depth);
else if (depth != 1.0f)
    FIXME("Cannot set clear depth %.8e on GLES; using the default 1.0.\n", depth);
```

Applied at all three sites (`texture_gl.c` ×2, `context_gl.c` new-drawable path). The
non-default case is reported rather than silently wrong.

**It is not the crash, though.** A/B against the previous default, same state-anchored
sequence: both die at the same point. Keep the change — it removes a genuine NULL call —
but cross `glClearDepth` off the suspect list. That is now four disproven causes for this
one crash (lost dbg42 code, legacy-context classification, `ARB_ES2_COMPATIBILITY`, the
depth clear), which is why the next step was to stop guessing and instrument.

### Localising it properly: log the state, not the theory

The tracer was rebuilt for this. Two changes:

* it now keeps the log handle **open** and `fflush`es per line. The original
  fopen/fclose-per-line form costs ~13 file opens per draw call, and with it the game
  is too slow to even reach the crash — a first attempt at tracing produced 182 515
  lines of healthy draws and never got there;
* every state is named as it is applied, via `debug_d3dstate(state_id)`, at both
  `state_table[...].apply()` call sites in `context_gl.c`.

The last `STATE ...` line before the fault names the handler directly, and from the
handler the offending GL call is one grep away. This is the reusable way to find NULL
entry points on this stack; the earlier approach of cross-referencing the box86 NULL list
against wined3d call sites produced 79 candidates and no answer.

### First result of that loop: `glBlendEquation`

The trace ended on `STATE_BLEND`. Dumping the pointers that handler uses:

```
PTR glBlendEquation          00000000     <- NULL
PTR glBlendEquationSeparate  79D0B6D0
PTR glBlendFuncSeparate      79D0BE10
PTR glBlendColor             00000000
PTR glEnablei/glDisablei/glColorMaski  00000000
```

`blendop()` picks between them:

```c
if (b->desc.rt[0].op != b->desc.rt[0].op_alpha)
    GL_EXTCALL(glBlendEquationSeparate(...));   /* rare, and it works */
else
    GL_EXTCALL(glBlendEquation(...));           /* the common case -- NULL */
```

So the *common* path jumped to zero. Menus survived because they draw mostly with
blending off, and `blendop()` is only reached once blending is on — which is why this
looked like "crashes when entering a 3D scene".

Fix: pass the same equation to `glBlendEquationSeparate`, which is exactly equivalent.
**Measured effect: the driven sequence now dies at step 10 instead of step 7** — real
progress, and proof the call was genuinely fatal, but there is a further NULL behind it.

Two related items closed at the same time:

* `glBlendColor` is NULL too. That was already guarded in `state_blend_factor()` in an
  earlier session — the same pattern, spotted then, with `glBlendEquation` missed.
* `EXT_DRAW_BUFFERS2` is desktop 3.0, so GLES 3.2 is credited with it and the
  `STATE_BLEND` table selects `blend_db2()` instead of plain `blend()`. Its independent
  path needs `glEnablei`/`glDisablei`/`glColorMaski`, all NULL. D3D8 never requests
  independent blend so the path is not taken today, but the selection is wrong; the claim
  is now dropped on GLES, along with `ARB_DRAW_BUFFERS_BLEND`.

**1. The crash entering a 3D scene — blocked on win32u, not on wined3d.**
The wined3d side already contains the correct GLES code; it cannot be switched on because
`glClearDepthf` and `glDepthRangef` are absent from wined3d's ext table even though EGL
resolves them. So the task is not "find another wined3d bug", it is **extend win32u's
pre-resolve list and get win32u rebuilding**. The exact 102-entry list is already
reconstructed in `dlls/win32u/opengl.c`; the blocker is that every win32u rebuild fails
with `Failed creating Direct3D8 Object.` Solve that and the ES entry points, the
`MGS2_GLES_ES2COMPAT` switch, and probably this crash all fall together.

**2. The striping on animated backdrops.** Measured shape: uniform `(0,16,0)` fill,
strict period 4, two rows written and two filled, only on screens with an animated
backdrop. Independent of the texture converters. The game's own source renders in PS2
FIELD mode (`sceGsResetGraph(0, SCE_GS_INTERLACE, GS_DISP_MODE, SCE_GS_FIELD)`), and a
half-height field stretched 2× gives exactly a 2-on/2-off pattern — that is the most
promising line, and it is a *game-side* behaviour, not a WineD3D one.

**3. Movies.** Cause established; the remaining work is providing a DirectShow MPEG
decode path under Wine. Everything needed is on the device (`quartz.dll`, `devenum.dll`,
`winegstreamer.dll`, `msmpeg2vdec.dll`, GStreamer with `libgstlibav`), so the next step is
to check whether the game's own filter registers and what the graph fails to build.
Temper expectations on performance: software MPEG-2 decode inside box86 on a Cortex-A55
may not be playable even once it works.

## Operational: keep the device's disk clear

`/storage` filled to **100%** (273 MB free of 57 GB), and **1.4 GB of it was accumulated
debug output from this project** — 52 `wined3d_dbg*.dll` at ~25 MB each plus 20
`win32u_*.so` variants. The user hit an in-game error at that point,
*"there is a problem with your disc, it may be dirty or corrupted"*, which is the game's
reaction to a failed read or write; a full volume is a very plausible cause, since the
game writes savedata and Wine writes into the prefix.

Cleanup removed 70 files / 1326 MB and took free space to 1.6 GB. Everything removed
still exists in `recovered-session/device-artifacts/`, so any build can be restored with
a single `scp`. Keep only what `launch.sh` references plus a reference build:

```
wined3d_dbg83_blendeq.dll        (default)
wined3d_dbg42_gles_present.dll   (launcher fallback)
wined3d_dbg52_depthrange_nop.dll (reference for A/B)
win32u_glfuncs3.so  win32u_depthbridge1.so
winewayland_pbo1.so  winewayland_gbmshm_directbgra1.so
```

Data integrity was checked at the same time and is fine: ext4, and every large file
reads to its final block — `demo.dat` 1 481 459 712, `vox.dat` 1 152 811 008,
`movie.dat` 305 387 520, plus `bgm.dat`, `codec.dat`, `face.dat`. No large-offset seek
problem. (`stage.dat` does not exist; the GOG install ships the `stage/` directory
instead, which is normal.)

**Delete debug builds as they are superseded.** One 25 MB DLL per experiment adds up fast
on a device that ships nearly full.

## Safe continuation procedure

**The device was unreachable for this whole session (`No route to host`, no ping), so everything below is pending hardware verification.**

1. Check that SSH is back, inspect uptime, `thermal_zone0/temp`, and that no old Wine/MGS2 process remains.
2. Confirm `/storage` has space and all four production component checksums match expected files. The storage partition has previously been about 99% full with ~650 MB free.
3. Deploy the two new artifacts (both currently local-only):
   ```sh
   scp recovered-session/device-artifacts/winewayland_pbo1.so "$MGS2_DEVICE:/storage/roms/ports/MGS2-Substance/"
   scp recovered-session/device-artifacts/launch.sh          "$MGS2_DEVICE:/storage/roms/ports/MGS2-Substance/"
   ```
   `winewayland_pbo1.so` md5 `42a203de86dcaea37d233cff29792ad0`.
4. **Baseline first.** Launch with the old driver and stats on, and record the numbers:
   `MGS2_WAYLAND_SO=winewayland_gbmshm_directbgra1.so MGS2_GL_STATS=300 ./launch.sh`
5. Then the new one, otherwise identical: `MGS2_GL_STATS=300 ./launch.sh`. Compare the `MGS2 present stats` lines. Expect readback per frame to fall well below the ~14.2 ms baseline; if it does not, the PBO path silently fell back (look for `falling back to synchronous readback` in the log).
6. If the picture is upside down, retry with `MGS2_GL_FLIP=0`. If colours are swapped, `MGS2_GL_BGRA=0`. Neither needs a rebuild.
7. If it is stable, walk the frequency ladder by setting `MGS2_FREQ_STEPS` to a single value (1416000, 1608000, 1800000) and pick the highest that holds below `MGS2_TEMP_DOWN` and does not reset.
8. Only then profile a short single process interval; global `perf -a` adds load and coincided with a reset. Prefer `MGS2_GL_STATS` over the profiling DLL.
9. Do not replace `dbg42`, remove the D3D8 proxy, change `BIGBLOCK`, rebuild `win32u.so`, or install the experimental profiling DLL without an isolated A/B test.

## Useful commands

```sh
# Temperature and clocks
cat /sys/class/thermal/thermal_zone0/temp
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_{cur_freq,max_freq}
cat /sys/class/devfreq/fde60000.gpu/{cur_freq,max_freq}

# Focus the game window
export SWAYSOCK=/run/0-runtime-dir/sway-ipc.0.sock
swaymsg '[app_id="mgs2_sse_rg353vs_port.exe"] focus'

# Screenshots
XDG_RUNTIME_DIR=/var/run/0-runtime-dir WAYLAND_DISPLAY=wayland-1 grim /tmp/mgs2.png

# Debug keyboard injector (copy `recovered-session/scripts/send_key.py` to /tmp after every reboot)
python3 /tmp/send_key.py --hold 200 --gap 600 tab
python3 /tmp/send_key.py z
```

### The `pkill -f` self-match trap has a second form

Already recorded once (`pkill -f launch.sh` killing the SSH session). It reappeared in a
way the bracket trick does **not** protect against:

```sh
# the harness's own cleanup
pkill -9 -f "[m]gs2_sse_rg353vs"

# how it was invoked
ssh root@device 'MGS2_EXE=mgs2_sse_rg353vs_movies.exe /tmp/drive.sh ...'
```

The `[m]` bracket stops the *pattern literal* from matching itself, but the **environment
assignment on the invoking command line** contains the plain name, so the remote shell
matched and killed itself. Symptom: the script returned instantly, exit 0, no output, and
its output directory was never created.

Two fixes, both applied: match on something only the real process has
(`pkill -9 -f "[w]ine mgs2_sse"`), and pass the executable name through `/tmp/mgs2_exe`
instead of the command line.

### The injector stopped working, and why

Synthetic keys silently stopped reaching the game. Three separate causes, all in the
injector rather than in Wine or sway; it now works again and drives the whole menu
sequence unattended:

* **It declared only the keys it was about to send.** libinput classifies a device by
  its advertised capabilities, and a device offering one or two keys is not reliably
  treated as a keyboard, so wlroots never routes it to the focused surface. It now
  advertises the full standard key range (1–127).
* **It slept 0.5 s after `UI_DEV_CREATE`.** udev plus libinput enumeration takes longer
  than that here, and events sent into the gap are simply dropped. Now 1.8 s.
* **It held each key for 50 ms.** The game polls input once per frame at 25–35 fps, so a
  50 ms press can fall between two polls. Default is now 150 ms hold, 400 ms gap.

It also focuses the Wine window over the sway IPC first — an unfocused surface receives
no key events at all.

The gptokeyb profile (`mgs2.gptk`) maps: `start=tab`, `a=z`, `b=x`, `back=enter`,
`guide=esc`, `x=s`, `y=d`. `/tmp/drive.sh` uses these to reach the main menu, the
NEW GAME / difficulty / RADAR screens and the legal disclaimer without a human.

## Local source and artifact locations

- Launcher and compiled binaries: `recovered-session/device-artifacts/`
- Logs and screenshots: `recovered-session/logs/`
- Wine source: `recovered-session/wine-11.0/`
- Wine PE (mingw) build, wined3d.dll: `recovered-session/build-wine-i386/`
- Wine i386 Unix build, winewayland.so: `recovered-session/build-wine-unix32/`
- i386 sysroot: `recovered-session/sysroot32/`
- Build environment: `recovered-session/scripts/build-env-i386.sh`
- Game settings / original game tree: `Metal Gear Solid 2 SUBSTANCE/bin/`

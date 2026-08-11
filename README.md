# MGS2 Substance on the RG353VS — working port, patches and method

Metal Gear Solid 2: Substance (PC, 2003, Direct3D 8) running on an Anbernic
RG353VS: Rockchip RK3566, four Cortex-A55, Mali-G52, 1 GB RAM, ROCKNIX, sway on
Wayland, 32-bit Wine under Box86.

The value here is not the game. It is the set of Wine patches, the launcher, the
measurement harness, and a chronological brief archive recording **which
hypotheses were wrong** — that record is what makes the next port of a similar
game to a similar handheld cheap instead of another month of guessing.

## State: what works

```text
picture     640x480, 22-38 fps standing in gameplay, 13-18 in heavy movement
sound       music/menu clicks work; gameplay SFX are audible but can vanish
            after encounter/map state transitions and return after another map
input       works normally, but a rare no-render/input stall remains under
            investigation; stock user32 reproduced it in the PeekMessage loop
saves       work
```

Two performance wins, both measured, both persisted in `device/launch.sh`:

| change | effect |
|---|---|
| CPU ladder top step 1608000 → 1992000 (the unit is overclocked) | +29% fps |
| `d3d8=builtin` instead of the port's own d3d8→d3d9 wrapper | readback 7.0-7.7 → 3.8-4.2 ms/frame |

## The three things that took the longest to find

**1. Sound needed three separate fixes at once, and each was invisible alone.**
The system dsound silently dropped everything a dmsynth sink wrote — proven by
injecting a continuous 1 kHz tone into every sink render and finding it absent
from a capture of the speaker monitor, then loud with a locally built dsound.
Separately, an older dmime delivered no note with velocity above zero. And with
one DirectMusic port per audio path, fourteen 22050 Hz sink buffers went to the
DirectSound mixer every period under Box86, which made the game stutter as soon
as SE actually started sounding; one shared port with four channel groups leaves
a single sink. MGS2's SE rides channel group 2.

**2. "Insufficient free blocks on the hard disc" was not about free space.**
The game asks its own drive how many free blocks it has. It runs from `/storage`,
but the only drive covering that path was `Z: -> /`, a read-only squashfs that is
100% full, so the answer was zero and saving was impossible. `D: -> /storage`
fixes it; `/storage` had 852 MB free that the game never got to ask about.

**3. The frame is not lost where it looks like it is.** The presenter's
"readback" figure looked like a 60 MB/s copy pathology. Splitting the timer
(`MGS2_GL_READ_SPLIT=1`, an explicit `glFinish` before `glReadPixels`) showed the
copy itself costs **0.75 ms** for 1.2 MB — about 1.6 GB/s, entirely normal — and
the rest is the CPU waiting for the GPU to finish the frame. The limit is CPU
plus the shared SoC thermal budget, not memory bandwidth.

## Method, which matters more than any single patch

- **Measure on the device, never reason from the desktop.** Every number in the
  briefs came from `MGS2_GL_STATS`, `/proc/<pid>/task/*/stat`, or a `pw-record`
  capture of the speaker sink monitor.
- **Never log from a hot thread while judging the thing you are logging.** One
  line per second per buffer from the DirectSound mixer took that thread from 169
  to 930 ticks per 10 s and was audible as stuttering audio. Several test rounds
  chased that artefact.
- **Frame rate here is scene-dominated.** Within one run, windows range 22 → 60
  fps. An A/B without a fixed spot measures the scene. Pin the clock too
  (`MGS2_FREQ_STEPS="1416000"`), or the comparison measures temperature.
- **Verify what is actually loaded, byte-wise.** The launcher bind-mounts chosen
  DLLs over Wine's; `cmp` the mount target against the file, never trust a name.
- **"Sound works" is not one claim.** Background music, menu clicks and gameplay
  SFX are separate observations, and conflating them cost this project a whole
  brief's worth of wrong conclusions.
- **One instance.** A background launch outlives the ssh session that started it,
  and two copies of the game read exactly like terrible lag.

## Layout

```text
AGENTS.md                 entry point for anyone, human or model, picking this up
docs/DEVICE.md            how to run, measure and stop the console safely
device/launch.sh          the launcher: DLL bind-mounts, audio backend, thermal
                          guard, presenter tuning. Every knob is documented with
                          the measurement that set its default.
device/MGS2-Substance.sh  the menu entry: working audio config plus the
                          measured-best presentation settings.
harness/perf_sample.py    per-thread CPU, temperatures, GPU clock, CPU cap
harness/sink_audible_test.sh  tone injection plus speaker-monitor capture with a
                          Goertzel bin, i.e. "is this audible" without ears
harness/jitter_ladder.sh  ladder over MGS2_DMSYNTH_JITTER_MS with detection
harness/send_key.py       synthetic input, for harnesses only
harness/dmsynth_state.py  one-shot reader/diff for the bounded synth-state ring
harness/dsound_live_state.py  read-only DirectSound/FluidSynth memory snapshot
harness/dsound_sfx_state.py  one-shot reader for the bounded gameplay-SFX
                              DirectSound-control ring
harness/dmime_state.py    one-shot reader for the bounded DirectMusic transition ring
wine-patches/*.patch      the Wine 11.0 changes, one file per module
docs/briefs/              chronological research and performance briefs
docs/MGS2_PROJECT_STATE.md, docs/MGS2_RG353VS_HANDOFF.md
mgs2_collect_context.sh   read-only system dump from the console
```

## Wine patches

Against pristine Wine 11.0. Eleven modules: d3d8, dmime, dmsynth, dmusic,
dsound, ntdll, opengl32, user32, win32u, wined3d, winewayland.drv. Patch 12
reconciles the later production batch branches with the recovered source tree;
patch 13 adds the bounded, memory-only intermittent-audio recorder. Patch 14
is a retained but disproved note-triggered mute-recovery experiment. Patch 15
implements the DirectMusic transition semantics needed by MGS2: the selected
AudioPath, controller-curve end/reset messages, flushing, and targeted stop/
invalidation handling. Patch 16 is a diagnostic-only, bounded transition ring
for deciding whether the next loss occurs before `dmime`, at PChannel routing,
or after MIDI is handed to the port. Patch 17 adds the bounded DirectSound SFX
control ring. Patch 18 is the non-mutating projected batch-break census with a
rolling effective-state fingerprint. Patch 19 adds the opt-in relative EBO,
normalized cache key and GLES OES base-vertex bridge. Patch 20 projects all 64
effective-state masks, patch 21 decomposes STREAM/VB changes into exact
components, and patch 22 samples exact producer-shadow geometry bytes to project
the remaining byte-identical WORLD+VB instancing opportunity. Patch 23 performs
a conservative sampled clip-space visibility census and counts only wholly
removable current producer batches. Patch 24 adds the opt-in AABB-cached culling
prototype and a one-second-polled live A/B switch. Its first matched device
A/B/A/B reduced WineD3D batches from 166.58 to 136.81 per frame and frame time
from 49.43 to 47.89 ms. Visual validation passed. The user explicitly declined
the remaining two-scene qualification, so patch 24 is the production default
with an immediate `MGS2_D3D8_VISIBILITY_CULL=0` rollback.

```sh
tar xf wine-11.0.tar.xz && cd wine-11.0
for p in ../wine-patches/*.patch; do patch -p1 -F0 < "$p"; done
```

All twenty-four apply with zero fuzz and reproduce the working tree byte for byte;
`-F0` is deliberate, so a silent mismatch fails instead of being patched
approximately. Building needs the cross compiler that ships in the repo but is
not on PATH, and the release wined3d needs its define passed explicitly:

```sh
export PATH="$PWD/../recovered-session/mingw/bin:$PATH"
make -j4 i386_CFLAGS="-g -O2 -DMGS2_RELEASE" dlls/wined3d/i386-windows/wined3d.dll
```

Beware: the object files in the build tree are release builds and are *newer*
than the sources, so `make` will not rebuild them. A mixed release/diagnostic
build links silently and lies in measurements — `touch` every source that must
go into a variant.

Highlights, all env-gated so they can be A/B tested on the device without a
rebuild:

- **dmsynth / dmusic** — upstream `685c5b6` write-latency backport with the
  reserve made tunable (`MGS2_DMSYNTH_JITTER_MS`, underruns 222 → 15); cost
  policy for FluidSynth on this CPU (reverb/chorus off, linear interpolation,
  polyphony 48); refresh voice status after rendering; and retain each DLS
  download for its actual port until the last shared AudioPath releases it.
  `MGS2_DMSYNTH_STATE=1` adds a fixed 256-record memory ring for reset,
  program/bank, note-on result and active-voice state; it performs no logging.
  `MGS2_DMSYNTH_UNMUTE_NOTES=1` is the patch-14 experimental guard that
  restores exact-zero CC7/CC11 when a positive-velocity note arrives.  A
  production regression on 10 August proved that it does **not** prevent the
  intermittent map/encounter SFX loss; keep it only as a documented negative
  A/B until the transition/curve capture identifies the real state change.
- **dmime** — `IDirectMusicAudioPath::QueryInterface` answering
  `IID_IDirectMusicGraph`, which MGS2 treats as fatal when missing; one shared
  port for all audio paths (`MGS2_DMIME_SHAREDGROUPS`); and the staged
  `dmime_transition1.dll`, which honours selected AudioPaths and curve
  endpoints/resets instead of leaving a transition at its initial CC value.
  `MGS2_DMIME_STATE=1` selects `dmime_state1.dll`'s fixed 256-record
  memory-only capture for one reproduction; it is not a production fix. Patch
  17 is a separate 4,096-record ring at the persistent DirectSound gameplay
  SFX pool for player attacks and steps, which are not reliably identified by
  a DirectMusic event.
- **dsound** — the build whose sink buffers are actually audible, plus a mix
  census and amplitude probes. `dsound_state1.dll` adds `MGS2_SFX_STATE=1`, a
  memory-only history of Lock/Unlock, position, volume, pan, frequency, Play
  and Stop calls on the 32,576-byte gameplay-SFX pool. It is diagnostic only.
- **user32 / ntdll** — the `PeekMessage` busy-loop fix (+11% fps, frame-time
  jitter roughly halved) and a cheaper `NtYieldExecution` (+3.4%).
- **winewayland.drv** — the presenter for this ABI situation: rendering goes to
  an EGL pbuffer and is copied out, because the upstream zero-copy path cannot
  work here (see below).
- **wined3d / win32u / opengl32** — what a GLES-only Mali blob needs from a
  desktop-GL-shaped renderer.

### Build

```sh
# PE DLLs (dmime, dmsynth, dsound, dmusic, wined3d, user32)
../wine-11.0/configure --enable-archs=i386 --without-x --without-wayland \
    --without-vulkan --without-opengl --without-gstreamer --without-alsa \
    --without-pulse --without-dbus --without-cups --without-fontconfig \
    --without-freetype --without-gnutls --without-krb5 --without-ldap \
    --without-sane --without-oss --without-pcap --without-usb --without-v4l2
make dlls/<module>/i386-windows/<module>.dll

# Unix-side .so (winewayland.drv, ntdll, win32u, opengl32)
../wine-11.0/configure --enable-archs=i386 --with-wayland --with-opengl \
    --without-x --without-vulkan --without-freetype --without-fontconfig ...
make dlls/<module>/<module>.so
```

Note for anyone reusing this: rebuilt **PE** modules have always been
trustworthy here, while two independently rebuilt `win32u.so` hung the game — the
Unix side is where a local build can differ from what the distribution ships.

## Dead ends, do not spend device time on these again

```text
zero-copy via wl_egl_window + eglSwapBuffers
    ABI wall, not a config problem: the game runs under Box86 with
    libwayland-client/-egl in BOX86_EMULATED_LIBS (emulated x86) while EGL is the
    native ARM Mali blob. Handing an emulated-x86 struct wl_egl_window to the
    native eglCreateWindowSurface faults in wglMakeCurrent (0xc0000005). A dmabuf
    route stays possible because only an FD crosses the boundary: the blob has
    EGL_EXT_image_dma_buf_import and Box86 wraps eglCreateImageKHR, but it has no
    MESA export extension and no gbm_* wrappers.
async PBO readback        10.7-12.5 fps; Mali maps the pack buffer uncached
MGS2_GL_SHM_BUFFERS=3     inside noise against 2
packed source-VBO         per-batch BO pool hits 256 slots/frame and falls to
                          13-15 fps; one 4 MB frame ring makes Mali allocation
                          grow 477 -> 531 MB in ~13 s and kernel OOM-kills MGS2
byte-identical instancing exact WORLD+VB census finds only 1.43-1.93 removable
                          batches/frame against the required 40
rebuilding the presenter  identical to the shipped build
GPU governor pinned to 800 MHz   GPU wait halves, CPU cap falls to 816 MHz
                                 because both share one thermal budget: net loss
GPU capped to 400 MHz     no gain
WINE_D3D_CONFIG=csmt=0    the game does not start (page fault at 0x3C), twice
suspending EmulationStation      ~1 fps, and it can leave the menu frozen
PChannel disjoint allocation, group→channel remapping, DLS gain boost,
DirectSound committed-region      none of these restored SE
DXVK / PanVK              PanVK on G52 is Vulkan 1.1 non-conformant, and the GPU
                          is not the bottleneck anyway
lowering resolution       works, obviously, and the owner refused it
```

## Still open

1. **Re-measure off the charger.** Every thermal number here was taken while
   charging, and the guard was seen walking the CPU cap from 1992 down to 816 MHz.
   That is worth more than any remaining software change.
2. **A `wined3d` build with `-DWINE_NO_TRACE_MSGS -DWINE_NO_DEBUG_MSGS` and
   SSE2 codegen.** Feasible — the working `wined3d` does come from this tree.
   Estimated 2-8%.
3. **An aggregated D3D8/wined3d census** — draw calls, redundant state changes,
   managed-texture scans — to find whether `wined3d_cs`'s half core is work or
   churn. Counters only, one line per 300 frames.
4. **An asynchronous presenter**: shared EGL contexts, two or three final
   textures, a fence, and the same `glReadPixels` performed on another thread, so
   the game thread stops waiting for the GPU. 5-15%.

## Credits and licence

The patches are derivative of Wine and carry Wine's LGPL-2.1-or-later. Wine 11.0
is the base; `685c5b6f6312d55c948ee15315d858777af72408` (Anton Baskanov) is
backported in the dmsynth patch. Everything else here — launcher, harness, briefs
— was produced for this port.

## binaries/

The production set the game was verified playable on, plus explicitly named
diagnostic/candidate variants, so a device can be restored or measured without
a toolchain. Checksums in `binaries/SHA256SUMS`.

```text
box86-clean1                               exact Box86 runtime the port bind-mounts
d3d8_producer_batch14_dirtyranges.dll      bounded dirty-range aggregation for game VBs
d3d8_producer_batch15_projectedcensus.dll  300-frame projected break census; diagnostic only
d3d8_producer_batch16_mixedcensus.dll      top mixed-state masks plus 64-mask projections
d3d8_producer_batch17_streamdetail.dll     buffer/offset/stride/index detail for WORLD+STREAM
d3d8_producer_batch18_geometryrepeatcensus.dll  sampled byte-identical WORLD+VB projection
d3d8_producer_batch19_visibilitycensus.dll conservative whole-batch visibility projection
d3d8_producer_batch20_visibilitycull.dll   production cached conservative frustum culling
dmime_se1.dll                              DirectMusic graph and shared-port support
dmime_transition1.dll                      se1 plus AudioPath/curve transition recovery
dmime_state1.dll                           transition1 plus bounded diagnostic recorder
dmusic_shared_lifetime1.dll                per-port DLS lifetime and port self-heal
dmsynth_se1.dll                            earlier jitter/cost-policy fallback
dmsynth_se2_lifetime.dll                   current voice-refresh and 48-voice build
dmsynth_se3_state1.dll                     se2 plus bounded reset/note/voice recorder
dmsynth_se4_unmute1.dll                    se3 plus note-triggered stuck-mute recovery
dsound_se1.dll                             makes dmsynth sink output audible at all
dsound_state1.dll                           se1 plus bounded gameplay-SFX recorder
ntdll_fastyield.so                         measured Wine yield fast path
opengl32_glesver1.so                       GLES entry-point/version bridge
opengl32_glesver2_basevertex.so            OES base-vertex alias; batch17 candidate
user32_peek1.dll                           caller-specific PeekMessage wait
winewayland_pbo1.so                        earlier measured presenter variant
winewayland_stall1.so                      currently selected presentation driver
win32u_glfuncs3.so                         GLES function bridge required by the driver
wined3d_batch16_setcache.dll               bounded 4-way batch cache, no hot telemetry
wined3d_batch17_relative_range.dll          relative-index/range-draw candidate; off by default
```

The renderer DLL is intentionally included even though it is 25 MB, as are the
current Box86 and Unix-side Wine modules. Together this is the complete custom
runtime selected by the production launcher; a clone no longer depends on a
sibling build-artifact directory to restore it. The temporary `sevoice7`
diagnostic EXE is not versioned here: it is derived from the user's game binary
and is not part of the production launch.

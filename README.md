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
picture     640x480; FINALPLAY2 reaches the 30-fps gameplay limit at the former
            20-fps fixed spot: three qualification windows were 30.0/30.0/30.1
            fps. A valid reinforcements capture is still 18.3-19.5 fps and
            later 11.9-14.8 fps: 30 is not a whole-game claim
sound       music/menu clicks work; gameplay SFX are audible but can vanish
            after encounter/map state transitions and return after another map
input       works normally. Two distinct stalls were captured: a stock-user32
            PeekMessage spin and a Box86 first-use mutex race. FINALPLAY4 keeps
            both fixes and moves the hot DirectSound FIR loop to native ARM
saves       work
```

The final playable configuration is now `device/launch-play.sh`; the old
`device/launch.sh` remains an archival measurement harness. Measured wins kept
from FINALPLAY2, plus the FINALPLAY3 reliability fix and FINALPLAY4 audio-CPU
bridge, are:

| change | effect |
|---|---|
| CPU ladder top step 1608000 → 1992000 (the unit is overclocked) | +29% fps |
| `d3d8=builtin` instead of the port's own d3d8→d3d9 wrapper | readback 7.0-7.7 → 3.8-4.2 ms/frame |
| conservative visibility culling on the matched heavy spot | 49.43 → 47.89 ms/frame; 166.58 → 136.81 batches/frame |
| exact Wine `_sse2_memmove` → native ARM libc bridge | removes the former 744-sample top guest block without changing overlap semantics |
| cached `DISCARD` shadow instead of reading mapped upload memory back | fixed spot: three consecutive windows at 30.0, 30.0 and 30.1 fps |
| atomic Box86 aligned-mutex first-use publication | old bridge fails the direct race test; fixed bridge passes 10/10 × 1,000 mappings |
| exact-source FFP shader/stage cache | corrected save/enemy control: 36 stages from 19 sources; removes 17 duplicate links that cost 2.04 s |
| exact Wine DirectSound FIR → native ARM bridge | fixed 1416 MHz: mixer thread 12.97% → 7.57% of one core (-41.6%); guest `dsound` samples 717 → 40 |

FINALPLAY uses a fixed 1992000 Hz target after the cooling upgrade. The culling
A/B above remains a historical 1800 MHz measurement; it is not relabelled.

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
device/launch-play.sh     fixed FINALPLAY launcher: final DLL bind-mounts,
                          1992 MHz, audio, presentation and emergency guard
device/launch.sh          archival laboratory launcher and A/B harness
device/MGS2-Substance.sh  minimal menu entry for launch-play.sh
harness/box86_guest_profile.py  resolve Box86 JIT perf samples through a bounded
                          memory-only guest/native map
harness/box86_guest_snapshot.py take the external snapshot of that map after a
                          bounded profile; neither tool logs from a hot thread
harness/box86_memmove_stats.py  external reader/diff for the bounded memmove census
harness/box86_mutex_first_use_stress.c  direct A/B for Box86's aligned-mutex
                          first-use publication race
harness/box86_pthread_link_stub.c  link-only symbols for the freestanding i386
                          mutex stress executable; never deployed
harness/perf_sample.py    per-thread CPU, temperatures, GPU clock, CPU cap
harness/sink_audible_test.sh  tone injection plus speaker-monitor capture with a
                          Goertzel bin, i.e. "is this audible" without ears
harness/jitter_ladder.sh  ladder over MGS2_DMSYNTH_JITTER_MS with detection
harness/send_key.py       synthetic input, for harnesses only
harness/autoload_save.sh  real-frame-gated save loader; corrected gameplay walk
                          defaults to down and can be changed with MGS2_WALK_KEY
harness/dmsynth_state.py  one-shot reader/diff for the bounded synth-state ring
harness/dsound_live_state.py  read-only DirectSound/FluidSynth memory snapshot
harness/dsound_sfx_state.py  one-shot reader for the bounded gameplay-SFX
                              DirectSound-control ring
harness/dmime_state.py    one-shot reader for the bounded DirectMusic transition ring
wine-patches/*.patch      the Wine 11.0 changes, one file per module
box86-patches/*.patch     exact Box86 EGL facade, native memmove/profilers and
                          aligned-mutex publication fix
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
the remaining two-scene qualification. Patch 25 is not another renderer
experiment: it physically removes patches 18–24's laboratory paths from the
production sources, restores batch16 as the WineD3D base, hard-enables the
proven producer and culler, and caches one composed WVP for the eight AABB
corners. The historical implementations remain reproducible by stopping the
patch chain at patch 24. Patch 26 keeps `D3DLOCK_DISCARD` writes in the cached
producer shadow, removes the resulting whole-upload-mapping readback needed by
the culler, and skips four provably zero-length range moves. On the former
20-fps spot it reaches the game's 30-fps limit without changing vertex bytes.
Patch 27 attacks first-use transition hitches instead of throughput: it links FFP
vertex and pixel stages as separable stage programs joined by a pipeline object,
so repeated shaders are relinked once per stage rather than once per pair, and it
adds the nine `gles_spellings[]` entries without which the GLES driver never hands
Wine the separate-shader-objects functions. Measured: a pair costs 116 ms instead
of 201 ms, 17 stage links instead of 56. It reduces hitches and does not remove
them -- a genuinely new stage still costs ~191 ms.
Patch 28 deletes the visibility culler's AABB cache. Its own telemetry measured
`cache_hit=0` against `cache_miss=112800` over 300 frames, and it could not be
otherwise: the key includes `mgs2_geometry_generation`, which is bumped on every
writable `Unlock`, while MGS2 re-uploads its dynamic vertex buffers every frame.
The cache paid a hash plus up to four comparisons per tested draw (376 per frame)
and 73,760 bytes of BSS to return nothing. Removal cannot change a culling
decision, because every lookup already fell through to the same AABB loop.
Patch 29 stops issuing three GLES-invalid or meaningless state toggles; rejected
GL calls fell from roughly 436 to 48 per second without an fps change. Patch 30
is a retained, default-off programmable-VS separable-stage experiment; the real
gameplay route measured no eligible pairs. Patch 31's cull-box prototype remains
off after its corridor-only fps win failed the player's broader playability test.
Patch 32 canonicalises fixed-function GL shaders and separable stages by exact
generated GLSL. The corrected save/enemy control contained 17 duplicate links
costing 2.04 s; cache-on emitted no duplicate. Hash, length and full `memcmp`
guard equality, and `MGS2_GL_SOURCE_DEDUP=0` is the rollback switch. See
`docs/briefs/MGS2_SHADER_FIRST_USE_RESEARCH_2026-08-13.md`.

```sh
tar xf wine-11.0.tar.xz && cd wine-11.0
for p in ../wine-patches/*.patch; do patch -p1 -F0 < "$p"; done
```

Patches 1-26 apply with zero fuzz and reproduce the FINALPLAY2 source byte for
byte; patches 27-30 and 32 reproduce the deployed WineD3D source (patch 30 is
compiled in but remains off by default), while patch 31 is the separate reverted
D3D8 experiment. `-F0` is deliberate, so a silent mismatch fails instead of
being patched approximately. Building needs the cross compiler that ships in
the repo but is not on PATH. The exact deployed objects use `MGS2_RELEASE` and
`MGS2_FINALPLAY`; these select the compile-time production policy and remove
the env-gated laboratory branches from the linked binaries.

```sh
export PATH="$PWD/../recovered-session/mingw/bin:$PATH"
make -j4 \
  i386_CC="i686-w64-mingw32-gcc -DMGS2_RELEASE" \
  i386_CFLAGS="-g -O2 -DMGS2_RELEASE -DMGS2_FINALPLAY -DWINE_NO_TRACE_MSGS -DWINE_NO_DEBUG_MSGS" \
  i386_LDFLAGS="-Wl,--disable-stdcall-fixup -Wl,--no-insert-timestamp" \
  dlls/wined3d/i386-windows/wined3d.dll dlls/d3d8/i386-windows/d3d8.dll

SOURCE_DATE_EPOCH=0 i686-w64-mingw32-strip --strip-unneeded \
  dlls/wined3d/i386-windows/wined3d.dll \
  dlls/d3d8/i386-windows/d3d8.dll
```

Beware: the object files in the build tree are release builds and are *newer*
than the sources, so `make` will not rebuild them. A mixed release/diagnostic
build links silently and lies in measurements — `touch` every source that must
go into a variant.

Research binaries remain env-gated for archived A/B work. The two FINALPLAY2
renderer binaries deliberately are not: batching, restart hoist, set cache,
producer dirty ranges, cached DISCARD shadow and visibility culling are
unconditional production code.

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
persistent shared VBO + WORLD lift
                          bounded 8 MiB coherent arena maps and fences safely,
                          but produces zero lifted batches both with and without
                          visibility culling; an exact effective-state projection
                          also finds zero safely mergeable whole producer batches
byte-identical instancing exact WORLD+VB census finds only 1.43-1.93 removable
                          batches/frame against the required 40
rebuilding the presenter  identical to the shipped build
GPU governor pinned to 800 MHz   GPU wait halves, CPU cap falls to 816 MHz
                                 because both share one thermal budget: net loss
GPU capped to 400 MHz     no gain
Mali shader LTO / pilot-shader disable
                          driver confirmed both config files; neither changed
                          per-stage link cost enough to keep
whole `wined3d_cs` / WineD3D ARM port
                          valid reinforcement profile splits its cost about half
                          Box86/Wine, half already-native Mali driver; it would
                          retain GL side effects and cannot remove driver work
WINE_D3D_CONFIG=csmt=0    the game does not start (page fault at 0x3C), twice
suspending EmulationStation      ~1 fps, and it can leave the menu frozen
PChannel disjoint allocation, group→channel remapping, DLS gain boost,
DirectSound committed-region      none of these restored SE
DXVK / PanVK              PanVK on G52 is Vulkan 1.1 non-conformant, and the GPU
                          is not the bottleneck anyway
lowering resolution       works, obviously, and the owner refused it
```

## Still open

1. **Frequent 12--20 fps combat scenes.** A valid 14 August reinforcement
   capture at fixed 1992 MHz and one process confirms this is real scene cost,
   not thermal throttling. `wined3d_cs` splits almost evenly between translated
   Wine and already-native `libmali`; replacing the whole WineD3D thread cannot
   reach 25 fps. Before an image-quality trade-off, the one remaining bounded
   renderer experiment is a memory-only census of draw paths that still escape
   the existing batcher, then a candidate that demonstrably reduces driver
   submissions. See `MGS2_REINFORCEMENT_ARM_TARGET_2026-08-14.md`.
2. **Intermittent gameplay-SFX loss.** Use the bounded DirectSound/DirectMusic
   state captures documented in the current audio handoff; do not add hot-thread
   logging. The 13 August manual combat report captured successful DirectSound,
   DirectMusic and synth activity but arrived after death without an exact attack
   timestamp, so it did not justify a new Wine audio patch. Also note the corrected
   control mapping: player attack is `x`; earlier `z` automation performed
   rolls/throws, so its bank 0 / program 8 event is not a punch signature.
3. **Soak the runtime fixes.** The earlier caller-specific empty-message spin
   and the later Box86 mutex-mapping deadlock are separate captures. FINALPLAY3
   keeps the measured bounded PeekMessage wait and removes the exact Box86
   first-use race; a future stall needs a new owner/wait capture, not an assumed
   attribution to either old incident.
4. **Unique first-use shader stages.** Patch 32 removes exact duplicates, not the
   first 200-320 ms link of a genuinely new source. Any next candidate must move
   measured stages earlier in the same GL context; the cross-process program
   binary cache is already disproved.

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
box86-clean1                               archived Box86 baseline
box86-native-memmove2                      previous production Box86 rollback
box86-native-memmove3                      previous FINALPLAY3 rollback
box86-native-dsound-fir1                   production memmove/mutex fixes + native dsound FIR
d3d8_producer_batch14_dirtyranges.dll      bounded dirty-range aggregation for game VBs
d3d8_producer_batch15_projectedcensus.dll  300-frame projected break census; diagnostic only
d3d8_producer_batch16_mixedcensus.dll      top mixed-state masks plus 64-mask projections
d3d8_producer_batch17_streamdetail.dll     buffer/offset/stride/index detail for WORLD+STREAM
d3d8_producer_batch18_geometryrepeatcensus.dll  sampled byte-identical WORLD+VB projection
d3d8_producer_batch19_visibilitycensus.dll conservative whole-batch visibility projection
d3d8_producer_batch20_visibilitycull.dll   production cached conservative frustum culling
d3d8_finalplay.dll                         clean production producer + cached visibility culling
dmime_se1.dll                              DirectMusic graph and shared-port support
dmime_transition1.dll                      se1 plus AudioPath/curve transition recovery
dmime_state1.dll                           transition1 plus bounded diagnostic recorder
dmusic_shared_lifetime1.dll                per-port DLS lifetime and port self-heal
dmsynth_se1.dll                            earlier jitter/cost-policy fallback
dmsynth_se2_lifetime.dll                   current voice-refresh and 48-voice build
dmsynth_se3_state1.dll                     se2 plus bounded reset/note/voice recorder
dmsynth_se4_unmute1.dll                    se3 plus note-triggered stuck-mute recovery
dmsynth_p34_interp_reset.dll                production interpolation-reset CPU fix
dsound_se1.dll                             previous production audio fallback
dsound_p36_native_fir_target.dll            production bridgeable FIR target
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
wined3d_finalplay.dll                       clean production batch16/set-cache policy
wined3d_p32_ffp_source_dedup.dll            production exact-source shader/stage cache
```

The archived research renderer DLLs are intentionally included even though each
is about 25 MB; the stripped production `wined3d_finalplay.dll` is only 2.73
MiB after the source cleanup. Current Box86 and Unix-side Wine modules are also
included. Together this is the complete custom
runtime selected by the production launcher; a clone no longer depends on a
sibling build-artifact directory to restore it. The temporary `sevoice7`
diagnostic EXE is not versioned here: it is derived from the user's game binary
and is not part of the production launch.

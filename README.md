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
            both fixes and moves the hot DirectSound FIR loop to native ARM.
            A later self-owned shadow-mutex freeze was captured on 14 August;
            production now bypasses that Box86 pool with direct compatible
            mutexes (`BOX86_MUTEX_ALIGNED=1`), with no FPS claim. On 20 August
            the same self-owned lock shape recurred on the direct mutex itself;
            bypassing the shadow pool did not close the gameplay deadlock
saves       work
```

The FINALPLAY7 configuration is `device/launch-play.sh`; the old
`device/launch.sh` remains an archival measurement harness. Measured wins kept
from the earlier releases plus the native WineD3D routes are:

| change | effect |
|---|---|
| CPU ladder top step 1608000 → 1992000 (the unit is overclocked) | +29% fps |
| `d3d8=builtin` instead of the port's own d3d8→d3d9 wrapper | readback 7.0-7.7 → 3.8-4.2 ms/frame |
| conservative visibility culling on the matched heavy spot | 49.43 → 47.89 ms/frame; 166.58 → 136.81 batches/frame |
| exact Wine `_sse2_memmove` → native ARM libc bridge | removes the former 744-sample top guest block without changing overlap semantics |
| cached `DISCARD` shadow instead of reading mapped upload memory back | fixed spot: three consecutive windows at 30.0, 30.0 and 30.1 fps |
| atomic Box86 aligned-mutex first-use publication | old bridge fails the direct race test; fixed bridge passes 10/10 × 1,000 mappings |
| direct compatible Box86 mutexes | bypasses the shadow pool, but a later live capture proved the direct guest mutex can still become self-owned; mechanism change, not a closed fix or FPS claim |
| exact-source FFP shader/stage cache | corrected save/enemy control: 36 stages from 19 sources; removes 17 duplicate links that cost 2.04 s |
| exact Wine DirectSound FIR → native ARM bridge | fixed 1416 MHz: mixer thread 12.97% → 7.57% of one core (-41.6%); guest `dsound` samples 717 → 40 |
| GPU governor `simple_ondemand` → `performance` after the cooling fix | same-process interleaved arms: 15.21 → 16.85 fps (+10.8%), CPU held 1992 MHz |
| native ARM `wined3d_buffer_load` (island entry 10) | same-process ABBA: -8.87 ms/frame (-12.8%), about +2.1 fps |
| native ARM `mgs2_batch_flush` with shared guest state (entry 4) | 10 stable same-process pairs: -2.680 ms/frame, +0.899 fps median (+4.8%), zero faults |
| native ARM `wined3d_rendertarget_view_load_location` (entry 23) | robust direction about -2 to -2.6 ms/frame in the measured scene; paired median about +1.3 fps; do not quote the withdrawn sigma/p-value |

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
                          1992 MHz, audio, presentation and emergency guard.
                          Rejects binary overrides and hashes every one of the
                          eleven files it mounts against FINALPLAY.manifest
device/launch-research.sh the deliberate opt-in for a run that substitutes a
                          binary, since launch-play.sh now refuses to
device/launch.sh          archival laboratory launcher and A/B harness
device/MGS2-Substance.sh  minimal menu entry for launch-play.sh
harness/box86_guest_profile.py  resolve Box86 JIT perf samples through a bounded
                          memory-only guest/native map
harness/box86_guest_snapshot.py take the external snapshot of that map after a
                          bounded profile; neither tool logs from a hot thread
harness/box86_memmove_stats.py  external reader/diff for the bounded memmove census
harness/reinforcement_submit_census.py  external reader/diff for the bounded
                          source-draw and final-GL-submission census
harness/box86_mutex_first_use_stress.c  direct A/B for Box86's aligned-mutex
                          first-use publication race
harness/box86_pthread_link_stub.c  link-only symbols for the freestanding i386
                          mutex stress executable; never deployed
harness/box86_mutex_signal_stress.c, box86_signal_link_stub.c
                          unvalidated signal/mutex diagnostic; never deployed
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
```

The default `wine-patches/*.patch` directory also contains the historical
native-island experiments.  For the reproducible renderer correctness build,
use the explicitly documented [NO-ISLAND chain](wine-patches/NO-ISLAND.md)
instead.

That chain applies every correctness patch with `patch -p1 -F0 --batch` while
skipping only the island track (42, 43, 48, 49, 50, 52, 53 and 54).  Do not
silently omit those patches from an all-island experiment; the two tracks have
different source prerequisites and the old island31 must not be loaded with
the NO-ISLAND build.

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
GPU governor pinned to 800 MHz   SUPERSEDED 2026-08-16, and it is now production.
                                 The old reading was real: GPU wait halved but the
                                 CPU cap fell to 816 MHz on a shared thermal budget.
                                 After the cooling fix that no longer happens. Re-
                                 measured in one process at one spot with the
                                 governor switched live and arms interleaved:
                                 ondemand n=35 mean 15.21 fps, performance n=39
                                 mean 16.85, +10.8%, ranges not overlapping, and
                                 the CPU held 1992000 in every arm. Cooling changed,
                                 so the dead end was worth re-opening; nothing else
                                 on this list has new data behind it
GPU capped to 400 MHz     no gain
Mali shader LTO / pilot-shader disable
                          driver confirmed both config files; neither changed
                          per-stage link cost enough to keep
whole `wined3d_cs` / WineD3D ARM port
                          valid reinforcement profile splits its cost about half
                          Box86/Wine, half already-native Mali driver; it would
                          retain GL side effects and cannot remove driver work
native ARM WineD3D island, routed entry point by entry point
                          FINALPLAY6 production, but do not re-cost it the old way. The
                          2026-08-15 illegal instruction was the x86 entry marker
                          being compiled into the ARM instruction stream, where
                          0x474d is `bx r9`; patch 48 fixes it and the mechanism
                          then works end to end on a live entry. What the fix
                          exposed is the real constraint: of 37 entries, 23 reach
                          an abort stub, 3 read `NtCurrentTeb()` (which on ARM is
                          the host thread pointer, not Wine's TEB), and most make
                          indirect calls through function pointers held in guest
                          structures -- x86 addresses native ARM cannot call.
                          Patches 48/49 and native replacements for the debug and
                          CRT stubs cleared the first two, after which a class-B
                          resolver made entry 10 measurable at -8.87 ms/frame
                          (about +2.1 fps). Entry 4 required one more correction:
                          native WineD3D had a duplicate file-scope batch object,
                          so the first candidate crashed. The island31/p56 pair
                          instead shares the authoritative guest batch state;
                          ten stable same-process pairs measured -2.680 ms/frame,
                          +0.899 fps (+4.8%), zero faults. Production now arms 17
                          entries. The GL-slot preflight is not semantic proof;
                          texture/rendertarget roots remain closed until their
                          state and indirect-call cuts are proved. See the latest
                          `MGS2_ISLAND_*` brief before extending the allow-list.
                          2026-08-19: entry 34 (`wined3d_texture_load_location`)
                          was tried and it does not get as far as its own body --
                          armed, it dies within the first frames with an illegal
                          instruction at its own bridge + 0xB, which is the
                          routing mechanism, not the cut. Production's 17 entries
                          and entry 10 through the same launcher both run, so the
                          harness and the base are exonerated. This is NOT a
                          closed dead end: it is an unfixed fault with a named
                          next check (`island_marker_check.py` against an
                          unstripped p56). Nothing about frame rate was measured
                          for entry 34 or entry 23. See
                          `MGS2_ISLAND_ENTRY34_FAULT_2026-08-19.md`
                          2026-08-20: the broader post-batching CS DRAW boundary
                          (entry 37, clean p66) is a closed correctness failure.
                          An A/B-disabled always-routed playtest had working sound
                          and a live 58--60 fps PRESENT/readback loop but no picture.
                          Thus the apparently fast routed windows were presenting
                          an incorrect/empty frame, not accelerating gameplay; the
                          raw -61.732 and calibrated -58.860 ms/frame readings are
                          withdrawn as optimisation results. p67 then proved that
                          the guest/ARM context TLS split was real (21 versus 0)
                          and synchronised ARM to 21, but 101,305 source DRAWs
                          still became 101,305 final GL submissions while all 64
                          retained frame-content samples stayed black. The one
                          relocation audit found no other authoritative shared
                          state beyond the already-synchronised batch pointer and
                          TLS. The coarse entry-37 boundary is therefore closed,
                          not awaiting another timing run. A future cut must stay
                          below guest context acquisition and prove equal picture
                          content before any FPS A/B.
                          p68 did exactly that: guest x86 retained context and
                          draw-state ownership while only the final primitive-
                          arrays tail became entry 38. At the heavy spot,
                          4,982,735 source calls equalled 4,982,735 final GL
                          submissions, fallback stayed zero, and the last 64 of
                          17,832 frame samples were all non-empty and unique.
                          This fixes the black picture for the lower cut. Its
                          later symmetric p68b A/B completed 46 cycles: 28 were
                          call-count balanced, with paired median +0.002 ms/frame,
                          mean +0.109 and only 13/28 favouring ARM. The independent
                          28k-call plateau gives median +0.046. Entry 38 is closed
                          as a performance root under its pre-registered <=0.3
                          ms/frame gate and is not a production candidate. The same
                          session later froze on direct mutex 0x6040623c:
                          lock=2, owner=wine_dinput_worker, while that owner,
                          main and wined3d_cs all waited on the same mutex. A
                          one-time unlock returned zero and rendering resumed.
                          Exact symbols in the matching unstripped win32u name
                          this address as `display_lock` (RVA 0x20623c), not
                          `session_lock` (RVA 0x226284, live 0x60426284). It is
                          separate from entry 38 and the 0x400f alert-futex
                          family; BOX86_MUTEX_ALIGNED=1 did not close it.
                          The standalone p68 record, exact ABI, hashes, recovery
                          and revised queue are in
                          `MGS2_NATIVE_DRAW_TAIL_AND_DIRECT_MUTEX_2026-08-20.md`.
                          The passive `display_lock` ring remains available.
                          p69 then attempted to isolate the remaining half: only
                          `context_apply_draw_state()` became native entry 39,
                          while acquire/current ownership, RT/depth preparation,
                          final draw and release stayed guest. At the stopped
                          correctness capture 1,357,984 calls had zero FALSE and
                          zero fallback and final array submissions were still
                          advancing at 1,357,983, but the last 64 of 6,921 frame
                          witnesses were identical and 0/256 lit; an independent
                          grim screenshot was all black. No FPS A/B was run.
                          The concrete p69 artifact is rejected, but the run is
                          not an ABI-valid rejection of native state apply. A
                          new transitive ABI audit found the shared-heap wall:
                          embedded
                          `ffp_frag_settings` is 132 bytes in i386 and 100 in ARM,
                          making `glsl_ffp_fragment_shader` 164 versus 132 bytes
                          and moving its `id` / `linked_programs` / `source` from
                          148/152/160 to 116/120/128. The corrected closure is 733
                          functions; the old 526-function mutable audit had lost
                          the GLSL backend by counting braces in shader strings.
                          ARM can also insert a 132-byte node into the guest's
                          164-byte cache, so correctness phases require clean
                          processes. The admission self-test now passes measured
                          entries 10/23 and correct entry 38, while p69/D fails;
                          phases A resource/preload, B dirty-state and C
                          bindings/FBO pass, D fails. Offline attribution of the
                          exact existing island41/p56 profile ranks unique safe
                          work A 2.878%, B 2.596%, C 0.514% of all user cycles.
                          These are not ms/frame. Contiguous phase A is now p70
                          entry 40: 548 functions, 1,096 aggregate rows with zero
                          ABI mismatch, and 53 routed versus zero unrouted
                          indirect calls. Its heavy-save device gate reached
                          2,172,004 calls and exactly 2,172,004 final array
                          submissions with zero fallback/faults; the retained
                          64 frames were all unique, lit and changing, and an
                          independent CAUTION gameplay capture was correct.
                          P70 therefore passes correctness and may proceed to a
                          symmetric same-process A/B. No FPS effect is claimed;
                          production is unchanged.
WINE_D3D_CONFIG=csmt=0    the game does not start (page fault at 0x3C), twice
suspending EmulationStation      ~1 fps, and it can leave the menu frozen
PChannel disjoint allocation, group→channel remapping, DLS gain boost,
DirectSound committed-region      none of these restored SE
DXVK / PanVK              PanVK on G52 is Vulkan 1.1 non-conformant, and the GPU
                          is not the bottleneck anyway
lowering resolution       works, obviously, and the owner refused it
indexed-draw reinforcement batch
                          the p37 memory-only census saw zero indexed source draws
                          through save load, ALERT, the guard response, visible
                          arriving enemies and the connecting-bridge transition;
                          the proposed indexed
                          merger would remove exactly zero submissions on that
                          route. The earlier dense manual 12--15 fps interval still
                          needs one p37 snapshot before generalising the zero
```

## Still open

1. **Frequent 12--20 fps combat scenes.** A valid 14 August reinforcement
   capture at fixed 1992 MHz and one process confirms this is real scene cost,
   not thermal throttling. `wined3d_cs` splits almost evenly between translated
   Wine and already-native `libmali`; replacing the whole WineD3D thread cannot
   reach 25 fps. The p37 memory-only census is now built. On the automated
   ALERT/guard-call route it measured zero indexed draws throughout; the proposed
   indexed batch is thus rejected for that route. A stationary 20-second follow-up
   measured about 740 source draws and 205 final GL draws per displayed frame
   (WineD3D submitted two CS Present commands per displayed frame). Take one
   manually verified dense reinforcement scene also had zero indexed draws:
   323,788 source non-indexed draws became 85,966 final GL submissions over the
   capture interval. The direct mutex reliability path measured 15.22 fps over
   300 frames there; it is not a renderer gain. See
   `MGS2_REINFORCEMENT_MUTEX_DIRECT_2026-08-14.md`.
2. **Intermittent gameplay-SFX loss.** Use the bounded DirectSound/DirectMusic
   state captures documented in the current audio handoff; do not add hot-thread
   logging. The 13 August manual combat report captured successful DirectSound,
   DirectMusic and synth activity but arrived after death without an exact attack
   timestamp, so it did not justify a new Wine audio patch. Also note the corrected
   control mapping: player attack is `x`; earlier `z` automation performed
   rolls/throws, so its bank 0 / program 8 event is not a punch signature.
3. **Soak the runtime fixes.** The earlier caller-specific empty-message spin
   and the Box86 session-lock stalls are separate captures. The 14 August
   self-owner reproduction occurred after the first-use publication fix, so
   production bypasses Box86's shadow pool with `BOX86_MUTEX_ALIGNED=1`. A future
   stall needs a new owner/wait capture, not an assumed attribution to either
   old incident. See `MGS2_REINFORCEMENT_MUTEX_DIRECT_2026-08-14.md`.
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
box86-island31                             FINALPLAY6 native WineD3D island + shared batch state
box86-island41                             FINALPLAY7 production island: canonical identity, indirect/GL routing fixes and entry 23
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
dmsynth_p35_resume_recover.dll              p34 source plus the sink transport watchdog;
                                           unmeasured, MGS2_DMSYNTH_WATCHDOG_MS=0 is its control arm
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
wined3d_p37_reinforcement_census.dll         p32 plus bounded submission census; diagnostic only
wined3d_p56_batch_state.dll                  FINALPLAY7 guest half: island markers, class-B/GL plumbing and guest batch accessor
```

The archived research renderer DLLs are intentionally included even though each
is about 25 MB; the stripped production `wined3d_finalplay.dll` is only 2.73
MiB after the source cleanup. Current Box86 and Unix-side Wine modules are also
included. Together this is the complete custom
runtime selected by the production launcher; a clone no longer depends on a
sibling build-artifact directory to restore it. The temporary `sevoice7`
diagnostic EXE is not versioned here: it is derived from the user's game binary
and is not part of the production launch.

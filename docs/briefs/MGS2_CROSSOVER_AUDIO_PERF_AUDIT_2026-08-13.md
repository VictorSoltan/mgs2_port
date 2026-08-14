# MGS2 RG353VS — CrossOver Android 17 audio/performance audit

Date: 13 August 2026. Scope: the supplied
`../crossover-android-sources-17.0.0.android21/source/wine/` tree, the current
Wine 11.0 MGS2 runtime, and the automated combat capture made on the RG353VS.

## Result

There is no additional CrossOver sound patch to port. CrossOver Android 17 is
based on Wine 2.8, and all five audio directories relevant to the running MGS2
stack are byte-for-byte source-identical to official Wine 2.8:

```text
dlls/dsound/
dlls/dmime/
dlls/dmusic/
dlls/dmsynth/
dlls/winealsa.drv/
```

The large useful CrossOver contribution is its GLES capability/correctness
work in `wined3d`. That work is already represented in the production Wine 11
renderer; it is the capability-removal port documented in
`docs/MGS2_PROJECT_STATE.md` section 3b and `wine-patches/09-wined3d.patch`.

No new production DLL was made from this audit. Copying an old path merely
because it is Android-specific would regress newer Wine semantics without a
measured mechanism.

The intermittent combat-SFX defect is still open. The automated battle route
worked and reached ALERT, but the loss did not occur in the retained control
runs. A later recording of the user's translated keyboard stream established
that the attack key is `x`, not `z`. The actions in these automated controls
were therefore rolls/throws, not punches. Their successful DirectMusic events
are useful healthy action-correlated controls, but they say nothing specific
about a missing player punch.

## Exact source comparison

The CrossOver tree declares `Wine version 2.8` in `source/wine/VERSION`.
Official Wine tag `wine-2.8`, commit
`4eaaf06ce4e5d7424eec2cf303c8256610544b39`, was fetched directly and compared
with `git diff --no-index`.

```text
directory       CrossOver versus official Wine 2.8
dsound          identical
dmime           identical
dmusic          identical
dmsynth         identical
winealsa.drv    identical
d3d8            8 insertions / 8 deletions in two files
wined3d         6,487 insertions / 1,147 deletions in 25 files
```

The `d3d8` differences are formatting, the added argument required by the
modified old wined3d API, and two `todo_wine` test annotations. They contain no
draw batching, upload cache, shader cache, ARM routine, or MGS2 optimisation.

Brief #15 had already established the exact `dsound` and `winealsa` result.
This audit extends the exact comparison through the entire DirectMusic chain:
`dmime`, `dmusic`, and `dmsynth` are also pristine Wine 2.8.

## Why the Android audio driver is not the answer

CrossOver contains `dlls/wineandroid.drv/mmdevdrv.c`, an OpenSL ES endpoint
backend. It has its own buffer queue/timer implementation and advertises a
10 ms default / 5 ms minimum period.

MGS2 on ROCKNIX does not load this driver. It maps `winealsa.drv` and reaches
PipeWire through ALSA. Replacing that backend would be an audio-stack port, not
a DirectSound/DirectMusic semantic fix, and the tree provides no evidence that
it repairs MGS2's intermittent effect handoff.

The old DirectMusic implementation is also not a native-behaviour reference:

- `PlaySegmentEx()` and `StopEx()` are stubs;
- `AudioPath::SetVolume()` and `ConvertPChannel()` are stubs;
- `AudioPath::Activate(TRUE)` stops its buffer, an obviously questionable old
  behaviour rather than a fix to preserve.

Wine 11 plus the MGS2 patches implements substantially more of this path.

## Performance candidates and disposition

### Already ported

CrossOver's GLES context/version handling and capability list were the valuable
find. The production renderer already uses that logic, with the Wine 11-specific
exception that `ARB_UNIFORM_BUFFER_OBJECT` is retained. It fixed the rendering
symptoms that originally motivated use of this tree.

### Superseded by Wine 11 or current MGS2 patches

The old `wined3d/buffer.c` has buffer orphaning and DISCARD/map policy. Current
Wine 11 already has upload BO mapping, BO renaming and copy-on-write machinery.
For this title, patch 26 additionally keeps DISCARD writes in the cached producer
shadow and removed two measured 512 KiB mapped-upload readbacks per frame. The
fixed heavy spot then reached 30.0/30.0/30.1 fps. Porting Wine 2.8's older map
path would remove newer ownership/synchronisation semantics.

The old `ntdll` heap uses size-bucket free lists. Wine 11 has its newer LFH/bin
implementation. CrossOver's ARM server/process additions are compatibility code
for running Wine on ARM; they do not replace the x86 game code that Box86 runs,
and no bespoke NEON/memcpy/render hot path was found. The measured hot copy is
already redirected by the exact Wine `_sse2_memmove` Box86 bridge.

### Not present

The CrossOver renderer still synchronously calls `glCompileShader()` and
`glLinkProgram()`. It contains no persistent program cache, parallel compiler,
prewarm list, or first-use staging mechanism. Its generated GLES shaders choose
`highp` when supported and even retain a TODO to lower precision selectively;
there is no hidden safe `mediump` policy to copy.

Registry hacks such as `SafeVsConsts`, `fixed_vs_constants_limit`,
`DisabledExtensions`, `pow_abs`, `NoINTZ`, `AllowGlMapBuffer`, and `GLSL130SM4`
are compatibility overrides, not a measured MGS2 fast path. Applying them
without an observed failing capability would repeat the class of false fixes
already closed in the performance briefs.

## Current transition-hitch patch and measured difference

Patch 32 is already production. On the corrected save-load/enemy route, the
control created 36 fixed-function stages from only 19 byte-distinct GLSL
sources. Seventeen duplicate stage links cost 2,036,500 us. Exact-source
deduplication removed all 17 duplicate compile/link events in the enabled arm.

Patch 27 is also production and changes repeated fixed-function program pairs
from about 201 ms to 116 ms (-42%) by sharing separable stages. Neither patch
removes the first 200--320 ms link for a genuinely new shader. This is why they
materially reduce transitions but do not make every load, location, or new enemy
hitch-free.

The earlier whole-stack A/B also made the least-optimised renderer worse: its
longest stall was 8,679 ms against 6,591 ms for the full stack. The claim that
the optimisation chain introduced the transition stalls is therefore refuted;
patch 31's separate playability regression remains the reason that patch is off.

## Automated combat control

The corrected save route is `down:3.0,right:1.6`. Keyboard `x` performs the
player attack; `z`, which the first automation used, performs a roll/throw.
`harness/autoload_save.py` supports a bounded action sequence and reads all
three memory-only state rings after an action. It keeps one uinput device for
the complete route. `harness/live_action_roll.py` continues an already loaded
game without launching a second instance.

Two useful control captures were retained:

```text
sfx-combatpunch1   8 z actions, enemy detection and ALERT
                   271 unique note-ons retained, 8 candidate signatures
sfx-live-roll1     24 z actions through ALERT, low life and mission fail
                   844 unique note-ons retained, 15 candidate signatures
```

The action-correlated candidate in both captures is bank 0, program 8, note 60,
velocity 127. It must not be called a punch signature. Every retained note-on
returned success and increased the active voice count; there were no synth
resets. Maximum observed voices were 38 and 47 of the configured 48
respectively, but no note allocation failed.

Across the rolling DirectSound snapshots in `sfx-live-roll1`, 1,327 unique
persistent-pool control records were retained: 402 Lock, 402 Unlock, 481 volume,
9 Play and 6 Stop records, all with successful HRESULTs. The concurrent dmime
snapshots retained 2,987 AudioPath volume records ranging from -3608 to -96,
with no `-10000` mute and no failure. This is a healthy combat control, not a
capture of the user's audible loss.

The route screenshots independently show enemy report, ALERT, low life and
mission failure, so the capture is not another corridor/wall false positive.

## AudioPath/shared-port hypothesis closed by source

`AudioPath::Activate(FALSE)` stops the path's own `pDSBuffer`. The shared
DirectMusic port is configured with `SetDirectSound(port, dsound, NULL)`, so its
dmsynth sink creates and renders into a different DirectSound buffer. The
AudioPath method neither calls `IDirectMusicPort_Activate(FALSE)` nor stops the
synth sink buffer.

Therefore guarding/removing that `Stop()` is not a valid shared-port repair.
The separate real inactive-port case is already covered in `dmusic/port.c`: with
`MGS2_DMIME_SHAREDGROUPS=1`, `PlayBuffer()` reactivates the synth port before
submitting MIDI. A multi-port A/B has already reproduced the loss and added
audible lag, so the shared-port selection itself is not the primary cause.

## Artefacts

```text
docs/briefs/MGS2_RESEARCH_BRIEF_15.md
docs/MGS2_PROJECT_STATE.md
docs/briefs/MGS2_SHADER_FIRST_USE_RESEARCH_2026-08-13.md
harness/autoload_save.py
harness/autoload_save.sh
harness/live_action_roll.py
logs/live-20260813/sfx-combatpunch1/
logs/live-20260813/sfx-live-roll1/
```

Representative hashes:

```text
cd0172dff87bc512ba990a4fddd2b1eeb3dc1ca2dd2117bd9522d141092e3835
    sfx-combatpunch1/state/before-dmsynth.json
ec17c2e44b33f52322fa9837aaeb902e0b2a1f2df7312d693158a3384688363e
    sfx-combatpunch1/state/after-08-dmsynth.json
1032b540d46284baed0b74a61acc455afe144cfcdcd67e75fef8c47e5df4f5c0
    sfx-live-roll1/state/before-dmsynth.json
a920de873a2bc6de1e2d18da091ac0d3b2f4f16d3e3ba6dcc7f171708920e5a1
    sfx-live-roll1/state/after-24-dmsynth.json
```

## Next bounded sound experiment

Do not ship a CrossOver-derived audio DLL: there is none. Keep the three rings
armed only for deliberate reproduction and capture immediately when the player
attack becomes inaudible, before opening Start or allowing another encounter to
restore it.

Do not target bank 0 / program 8 from the `z` controls as if it identified a
punch. A future punch capture must first correlate the real `x` action with its
event or persistent-pool operation. If the exact missing punch then appears as
a successful dmsynth note with a new voice, use the bounded synth-sink output
marker for only that event/window. If it is absent, move upstream to MGS2's SE
scheduling rather than changing DirectSound globally.

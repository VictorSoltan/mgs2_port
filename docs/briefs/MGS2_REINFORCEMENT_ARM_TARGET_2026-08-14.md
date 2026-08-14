# MGS2 RG353VS — reinforcement capture: what is actually worth an ARM target

Date: 14 August 2026. Status: observation only; no candidate was built or
deployed from this capture.

## Result

The player loaded the normal FINALPLAY4 production build and called
reinforcements. A follow-up 20-second external `cycles:u` profile began only
after the player explicitly reported that the reinforcements were entering. Its
surrounding real-frame windows stayed around **18.3--19.5 fps** and later reached
**11.9--14.8 fps**. This is the reported combat/reinforcement problem, unlike
the earlier quiet outdoor spot at 34--37 fps.

The immediate consequence is negative but useful: another audio ARM bridge is
not the path to combat FPS.  The large CPU consumers are WineD3D submission,
the native Mali userspace driver it invokes, and game workers.

## Preliminary external profile

The first 30-second profile used the ordinary external production wrapper, with
`MGS2_WALK_BURSTS=0` only to return control promptly after the save was loaded.
It selected deployed FINALPLAY4 files; no experimental D3D8 or Box86 AABB bridge
was enabled. `perf` attached to the one live game process (`PID 2384`) and wrote
no log from a Wine, mixer, or driver hot thread.

The player subsequently warned that this first interval could have begun after
death. It remains useful as a scene-level distribution, but is **not** the basis
for choosing an ARM target. The verified interval below is the basis for every
decision in this brief.

Artefacts:

```text
logs/rg353vs/reinforcement-production-20260814/
  reinforcement.script       external perf samples
  maps-before, maps-after    process maps around the interval
  threads-before, threads-after
  frame-tail.log             driver frame-time report surrounding the interval
```

The temporary `perf-2384.map` disappeared when `perf` exited.  It is a
short-lived host-JIT symbol map, not the persistent Box86 guest-map recorder,
so this capture cannot safely assign its JIT samples to individual x86 source
blocks after the fact.

## Preliminary CPU sample distribution

`reinforcement.script` contains 11,784 `cycles:u` samples.  The counts are
samples, not a claim that the threads ran serially; the RK3566 has four cores.

| Thread / mapped part | Samples | Reading |
| --- | ---: | --- |
| `wined3d_cs` | 4,063 | Largest individual worker: rendering command stream. |
| `mgs2_sse_rg353v:3271` | 3,849 | Largest game worker. |
| other game workers | 2,255 | More game simulation / queue work. |
| `wine_dmsynth_si` (both) | 915 | Synth work, not the dominant combat cost. |
| `wine_dsound_mix` | 393 | Mixer is smaller still. |

Within `wined3d_cs`:

```text
1,802  /usr/lib32/libmali.so.1.10.0
1,607  /tmp/perf-2384.map       (Box86-generated host code)
  599  [unknown]
   55  /usr/bin/box86
```

`libmali.so` is already native ARM userspace driver code.  Rebuilding WineD3D
or the driver as a whole "for ARM" therefore cannot remove this part of the
cost.  It can only be reduced by giving the driver less work: fewer submitted
draws/state transitions or avoiding an expensive WineD3D path.  FINALPLAY has
already removed the bulk of the source draws, so the next change must be based
on an exact block-level capture rather than another global batcher.

## What this rules in and out

* Do not spend the next iteration on more DirectSound or dmsynth ARM bridges
  for FPS.  The production DirectSound FIR bridge remains useful for the audio
  deadline, but the mixer is 393 samples here.
* Do not deploy the old native-AABB candidate.  It replaces only an inner
  vertex scan, while this event is dominated by WineD3D and game workers.  Its
  launch behaviour was also not qualified.
* Do not try to replace whole `wined3d.dll` or `libmali.so`.  That combines GL
  side effects, driver ABI and Wine state and is not a narrow, reversible ARM
  target.

## Why the follow-up used the bounded guest map

The follow-up cold-started the same production files with
`MGS2_BOX86_GUEST_MAP=1` only. The recorder is a bounded in-memory map and is
read externally after the interval, so it identifies guest RVAs without output
from a Wine, mixer, or driver hot thread. That is the smallest capture that can
rule a narrow ARM bridge in or out.

## Verified 20-second reinforcement interval

The follow-up was cold-started from the same production files with only
`MGS2_BOX86_GUEST_MAP=1`, then the player explicitly reported that
reinforcements were entering before the capture began.  The CPU was pinned at
1,992,000 Hz (both current and maximum), temperature was 82,777 mC, and there
was exactly one game process.  Thus neither a second instance nor frequency
throttling explains the event.

The bounded map held 16,523 of 262,144 records with `overflow=0`.  Of 5,331
resolved JIT samples, the principal modules were:

```text
game EXE                         1713
wined3d.dll                      1109
dmsynth.dll                       648
d3d8.dll                          430
```

The relevant raw thread samples were `wined3d_cs` 2,755, the main game worker
2,618, and `wine_dsound_mix` 435.  Within `wined3d_cs`, the sample objects
split almost exactly in half:

```text
1218  Box86 generated Wine code (/tmp/perf-6840.map)
1208  native /usr/lib32/libmali.so.1.10.0
 288  unresolved userspace address
  41  Box86 runtime
```

The exact leading WineD3D guest block is `draw_primitive()` in `context_gl.c`
(RVA `0x5c760`, 156 samples).  Its surrounding hot functions include GLSL
constant upload, stream declaration/setup, and the existing MGS2 batch flush.
They make GL calls or manipulate live Wine objects; none is a safe whole-thread
ARM bridge.  The leading D3D8 block remains the visibility path at RVA
`0x4011` (272 samples), not the small AABB scan alone.

The immediately following frame reports stayed around 18.3--19.5 fps in the
reinforcement scene, with later dense windows reaching 11.9--14.8 fps.  The
logs are in `logs/rg353vs/reinforcement-verified-20260814/`.

## Tooling correction

The handheld's default `perf script` format uses `comm tid timestamp cycles:u
ip`, whereas an older reader only accepted `comm pid/tid ip`. The external
`harness/box86_guest_profile.py` now accepts both formats. It was checked against
the old explicit-format capture and this handheld-format capture; it performs no
live-process access or instrumentation itself.

### Updated decision

This **rules out a whole `wined3d_cs` ARM port** as the next patch.  Roughly
half of the worker's observed cost is already native ARM Mali driver work, so
such a port cannot remove it and would have to reproduce GL side effects,
context ownership and Wine state exactly.  The next performance candidate must
reduce the number or cost of submissions sent to `libmali`, not translate the
thread around them.  A renderer-side census of remaining unmerged draw paths is
the smallest measurement that can choose that candidate.

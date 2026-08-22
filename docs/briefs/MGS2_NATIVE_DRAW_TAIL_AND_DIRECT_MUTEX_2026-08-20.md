# MGS2 RG353VS — lower native DRAW tail renders; win32u display_lock self-deadlocks (2026-08-20)

Handoff for research. Continues
`MGS2_NATIVE_CS_DRAW_BLACK_FRAME_2026-08-20.md`, which closes the generic
post-batching DRAW boundary after p66 and p67 both produced an empty picture.
This brief begins after that decision. It records the lower p68 boundary, its
successful picture-correctness gate, the separate direct-mutex freeze exposed
during the same session, its exact `win32u` object identity, the debugger
recovery, the symmetric p68 A/B result, and p69's black-frame result under a
guest-owned current context. The final passes show that the concrete p69 build
was never ABI-safe, validate the new admission gate against three proven native
roots, use the existing FINALPLAY7 profile to select one safe next phase, and
record p70's completed gameplay correctness gate.

```text
CORRECTNESS       p68 entry 38 runs only the final
                  wined3d_context_gl_draw_primitive_arrays() tail in ARM.
                  Guest x86 retains context acquisition/current-context
                  ownership, render-target loads, draw-state apply, barriers
                  and release. At the owner's heavy spot, 4,982,735 source
                  tail calls became 4,982,735 final GL submissions, fallback
                  stayed zero, and the last 64 frame witnesses were lit and
                  unique. The owner screenshot shows correct gameplay
MEASURED          p68b's symmetric guest-side A/B is now complete: 46 cycles,
                  28 call-count balanced within 2%, paired median
                  +0.002 ms/frame (ARM routed minus guest), mean +0.109,
                  13/28 favouring routed. The 17 balanced cycles on the main
                  28k-call plateau independently give median +0.046. Entry 38
                  is therefore closed as a performance root under the
                  pre-registered <=0.3 ms/frame rule
FREEZE            the same process later froze on direct pthread mutex
                  0x6040623c. lock=2, owner=wine_dinput_worker TID 29633, while
                  that owner, main and wined3d_cs all waited on the same mutex
IDENTITY          the exact unstripped production win32u_glfuncs3.so names
                  display_lock at RVA 0x20623c and session_lock at 0x226284.
                  0x6040623c - 0x20623c = mapped base 0x60200000 exactly;
                  session_lock would have been 0x60426284. The earlier
                  session_lock attribution is refuted, not merely unproven
SEPARATION        source/final counts were equal and the retained picture was
                  correct up to the stop. The stopped native DRAW tail was not
                  the owner or waiter boundary. One p68 occurrence does not
                  attribute the freeze or its frequency to entry 38
RECOVERY          pthread_mutex_unlock(0x6040623c) on the recorded owner thread
                  returned 0, zeroed the mutex and resumed the same process.
                  Source/final counts and frames advanced together afterward
PRODUCTION        unchanged: FINALPLAY7, box86-island41 + unchanged p56, the
                  previous 17 entries plus measured entry 23. Entry 38 is
                  closed; entry 37 and the concrete ABI-invalid p69 artifact
                  are rejected. Native state apply as an architecture is not
                  closed by that invalid experiment
P69               entry 39 isolated context_apply_draw_state() while guest x86
                  retained acquire/current ownership/RT-depth/final draw/release.
                  At the stopped capture, 1,357,984 p69 calls produced zero
                  FALSE and zero fallback; 1,357,983 final array submissions
                  had advanced. Yet the last 64 of 6,921 frames were identical
                  and 0/256 lit, and an independent grim capture was all black.
                  No timing was attempted
ABI                the transitive p69 shared-heap audit now finds the concrete
                  blind spot: glsl_ffp_fragment_shader is 164 bytes in i386
                  and 132 in ARM. Its id / linked_programs / source fields move
                  from 148/152/160 to 116/120/128 because embedded
                  ffp_frag_settings is 132 versus 100 bytes. The root is not
                  ABI-safe even though its top-level objects match. ARM can
                  also allocate a 132-byte node into the guest's 164-byte
                  shared cache, so phases may never share a correctness process
ADMISSION          self-test passes: measured entries 10 and 23 and correct
                  entry 38 are ABI-safe; p69 / shader phase D fails. Separate
                  phase audits admit A resource/preload, B dirty-state and C
                  bindings/FBO, and reject D
PROFILE            the existing exact island41/p56 capture ranks unique safe
                  work A 2.878%, B 2.596%, C 0.514% of all user cycles. These
                  are attribution shares, not ms/frame; D's 4.176% is excluded
P70               contiguous phase A is now entry 40: ABI PASS (1,096 rows,
                  zero mismatch), zero unrouted indirect calls, marker +29 at
                  RVA 0xb9410, and 1,616 class-B IDs. The clean gameplay run
                  reached 2,172,004 phase-A calls and exactly 2,172,004 final
                  array submissions with zero fallback; its last 64 of 5,087
                  frames were unique, lit and changing. An independent capture
                  shows correct live CAUTION gameplay with enemies and HUD.
                  Fault/unresolved lines: zero. This completes correctness;
                  the run was not A/B and makes no FPS claim
NEXT              build a symmetric guest-side A/B for phase A and measure one
                  process at the owner's fixed heavy spot. Do not run D or
                  repair the FFP ABI before safe-phase results
```

## 1. Why the boundary moved below entry 37

Entry 37 crossed into ARM immediately after CS batch decoding and carried the
whole `wined3d_cs_exec_draw_one()` closure. Its p66 always-routed playtest kept
sound and PRESENT alive but produced no picture. p67 then tested the only real
duplicated authoritative state found by the relocation audit:

```text
guest wined3d_context_tls_idx       21
ARM copy before sync                0
ARM copy after sync                 21
source DRAW / final submissions     101,305 / 101,305
guest fallback                      0
last 64 retained frames             identical and black
```

The p67 relocation audit covered 605 functions, 46 referenced writable objects
and 12 zero-storage runtime candidates. It found both controls:
`mgs2_batch_ptr`, already shared by production entry 4, and
`wined3d_context_tls_idx`, synchronised by p67 without restoring the picture.
The remaining candidates were ARM-owned translation/cache state, bounded
counters, one-shot flags or closure overreach. There was no honest second
guest/ARM state object to copy.

The justified architectural conclusion is narrower than the first version of
this brief said. Entry 37 moved current-context ownership **and** draw-state
application into ARM together; p68 moved both back to guest together. Those two
experiments do not isolate which half caused the black frame. Current-context
ownership must stay guest in the next experiment as the controlled half; this
does not identify it independently as the cause. The later p69 run tested that
combination, but its transitive shared-heap layout was incompatible. It rejects
that concrete artifact, not the concept of native state application. Entry 37
remains closed, and none of its raw or calibrated timing deltas is an
optimisation result.

## 2. Exact p68 cut and ABI

The p68 call sits inside guest `draw_primitive()` after all of the following:

```text
guest x86   context_acquire()
guest x86   context validity and current-context ownership
guest x86   render-target and depth/stencil load/prepare
guest x86   pending-batch flush decision
guest x86   context_apply_draw_state()
guest x86   depth/stencil location bookkeeping
guest x86   transform-feedback and texture-barrier setup
ARM entry   wined3d_context_gl_draw_primitive_arrays() only
guest x86   UAV memory barrier, rasterizer-discard cleanup and context_release()
```

Indirect draws do not cross this entry. The route exercised by the device was
entirely the primitive-arrays tail, including indexed parameters passed to the
existing helper; the final-submission census reported every reached GL call as
the arrays family.

The island entry is:

```text
id             38
guest symbol   mgs2_draw_primitive_arrays_island
ABI            vFp -- one pointer, no return value
canonical RVA  0x000b9a20
marker offset  +15
wrapper        mgs2_island_w38_vFp
```

The one pointer names a guest-stack argument object:

```c
struct mgs2_draw_primitive_arrays_args
{
    struct wined3d_context_gl *context_gl;
    const struct wined3d_state *state;
    const void *idx_data;
    unsigned int idx_size;
    int base_vertex_idx;
    unsigned int start_idx, count, start_instance, instance_count;
};
```

An earlier nine-argument draft put the i386 marker at +81, outside the canonical
64-byte witness window. It was rejected before deployment and never ran on the
device. Passing one pointer moved the marker to +15, and
`gen_entry_identity.py` derived RVA `0xb9a20` and that offset from the mounted
p68 DLL rather than from a hand-entered symbol.

The wrapper retains the p67 TLS guard because reachable native code can consult
the current context. It increments the source counter only after routing and
after guest TLS index 21 has been installed in the ARM copy. The fallback is
fail-closed through the recorded guest entry. No A/B variable was enabled in the
p68 run, so the observed path was native after the one successful TLS sync.

The existing fallback is not a valid performance control at this frequency:
it calls `RunFunctionFmt(guest, "p", args)` once per tail call, whereas the
normal guest path does not. The earlier empty-entry calibration measured this
kind of re-entry at about 2.854 microseconds per call. The p68 correctness run
recorded 4,982,735 calls over 17,832 displayed frames, or 279.43 calls/frame;
linear scaling therefore estimates about 0.797 ms/frame of asymmetric fallback
cost here, not the several-ms entry-37 cost carried by roughly 1,000 calls/frame.
That is still larger than p68's later measured zero and invalidates the old
wrapper as its control; section 10 uses the symmetric guest selector instead.

## 3. Static checks before device time

`island_mutable_state_audit.py` gained `--root` so the new boundary could be
audited directly before entry identity existed. The entry-38 closure contained
78 functions and 15 writable references. Review found only the already-known
shared state (`mgs2_batch_ptr` and `wined3d_context_tls_idx`) plus ARM-owned GL
translation/census state. It did not expose another authoritative guest object
whose ownership crossed this lower cut.

The generated identity table records:

```text
{ 38, 15, 0x000b9a20 }
```

The bridge table, source manifest and mirrored Box86 bridge source all use the
same `vFp` signature. The device launcher arms exactly:

```text
0,1,2,3,4,5,6,9,10,14,18,19,22,23,28,29,32,33,38
```

That is FINALPLAY7's 18 entries plus 38. Entries 34 and 37 are absent. The
launcher enables only memory correctness witnesses and the existing 300-frame
present record:

```text
MGS2_DRAW_CORRECTNESS=1
MGS2_FRAME_WITNESS=1
MGS2_REINFORCEMENT_CENSUS=1
MGS2_GL_STATS=300
MGS2_PLAY_WINEDEBUG=-all,err+waylanddrv
```

No hot-thread stderr counter was added.

## 4. Exact p68 build and launch

The live targets were byte-checked against these named artifacts:

```text
box86-island46-p68-tail
  7af46e61f7c19c94b18ec9cef4846710caca2d816a9caad9d9754f8a175b3ef4
wined3d_p68_draw_tail.dll
  c1d605da5b2dbc4e6fe3da1b5e274d7170d21d655889df490dafd36dd7545173
winewayland_p67_frame_witness.so
  a1ee930a37f9e456e1d3205b154f345e11fb1e8e1fe8c8f8286c6bee706fe7db
device/launch-p68-correctness.sh
  82859ff680da94f18194ad9bcf34f97929df46b0879d518d96edb148e0c6c5f0
```

One process ran, PID 28879. The CPU policy was `performance`, with current and
maximum both 1992000 kHz at validation; a recorded temperature point was
78.125 C. Runtime registration and identity also passed:

```text
19 of 37 island entries armed
class-B  1,612 native IDs registered and mappable
base     guest wined3d 0x7a280000
witness  wined3d_texture_from_resource and context_invalidate_state agree
entry 38 canonical match, no neighbouring or mid-function match
```

This was an always-routed correctness session. It was not interleaved, did not
have a guest control arm, and was not authorised to produce an FPS claim.

## 5. Correctness result at the heavy spot

The owner loaded the target save and brought the process to the heavy gameplay
spot. The external memory reader and the independent Wayland screenshot agreed:

```text
TLS sync attempts                  1
TLS guest / ARM before / after     21 / 0 / 21
source entry-38 tail calls         4,982,735
guest fallbacks                    0
final GL submissions               4,982,735
final submission kind              all arrays
frame witness total                17,832
retained range                     17,769..17,832
unique retained hashes             64 / 64
minimum lit samples                252 / 256
minimum changed samples            253 / 255
last retained hash                 a3f57103
island faults / unresolved traps   0 / 0
owner screenshot                   correct gameplay picture
```

This is the positive result entry 37 never reached. Source and final counts are
equal, so the tail is not silently dropping DRAWs; the bounded witness is lit
and changing, so equal calls are not merely submitting the same empty image.
The screenshot supplies the independent semantic control that the hashes alone
cannot.

The log contains long runs near 35 fps as well as lighter and much heavier
windows. They are scene observations from one configuration. The later freeze
also contaminates one aggregate window with a 281,783 ms stall. None of those
lines is a p68 performance measurement.

## 6. The later freeze was captured separately

After the correctness capture, the user reported a complete freeze and left the
process alive. At the stop, the memory witnesses still showed the last valid
state above: source and final remained equal, fallback remained zero, and the
retained frames immediately before the stop were real changing content.

The CS census recorded:

```text
submits / alerts / executes         2,963,031 / 5,224 / 2,961,361
wait prepare/enter/return/abort     5,226 / 5,224 / 5,224 / 2
wined3d_cs TID                      29,585
wined3d_cs wait                     __futex_wait, syscall 240
DEFAULT head / tail                 0x0b7e8bfc / 0x0b7d0258, NOT EMPTY
MAP head / tail                     0x2734 / 0x2734, empty
waiting_for_event                   0
sample window                       12 samples / 5.5 s
executes/ring/queue/wfe             all unchanged
whole-process CPU                   91 ticks; other work still ran
```

The stable non-empty DEFAULT queue makes the CS thread a downstream waiter; it
does not by itself identify the owner. The census's stock verdict text says
"no task consuming CPU", but that sentence is not valid for this capture:
the independent process witness measured 91 ticks. The narrower statement is
the one supported here: the CS consumer did not advance, published work stayed
pending, and it was not stopped in WineD3D's `waiting_for_event` path.

## 7. The direct mutex names its own self-deadlock

All decisive waiters used futex address `0x6040623c`, operation
`FUTEX_WAIT_PRIVATE`, expected value 2, with no timeout. Its 24 bytes were:

```text
0200000000000000c1730000000000000100000000000000
```

Decoded as the live 32-bit pthread mutex:

```text
lock      2
count     0
owner     29633
kind      0        regular, non-recursive
nusers    1
tail      0
```

TID 29633 was `wine_dinput_worker`. That same owner thread was itself in the
untimed wait on `0x6040623c`; main and `wined3d_cs` waited on it too. The owner
was therefore waiting for its own non-recursive mutex.

`BOX86_MUTEX_ALIGNED=1` was active. This matters: the futex address is the
direct guest pthread mutex, not a Box86 shadow-pool backing object. It is also
not the `0x400f...` per-thread alert futex behind
`NtWaitForAlertByThreadId`. The capture therefore proves a narrower correction
to the old reliability claim:

```text
direct compatible mutexes remove the shadow-pool mechanism;
they do not close the gameplay self-owned mutex deadlock itself
```

The old wording called this the same `session_lock` shape as the 14 August
capture. That comparison was useful only at the mutex-state level and was wrong
as an object identity. No reliable guest stack was recovered from this frozen
owner, but the exact unstripped production artifact makes the object identity
decidable without one. One occurrence in a p68 research session still says
nothing about relative frequency and does not make entry 38 causal.

## 8. Exact artifact identity: this is display_lock, not session_lock

The unstripped file matching the shipping Unix-side module is
`binaries/win32u_glfuncs3.so`. Its ELF symbols are:

```text
display_lock    RVA 0x0020623c
session_lock    RVA 0x00226284
frozen futex        0x6040623c
```

The frozen address gives one exact module base:

```text
0x6040623c - 0x0020623c = 0x60200000
0x60200000 + 0x00226284 = 0x60426284   expected session_lock address
```

Therefore the captured object is `win32u/sysparams.c`'s `display_lock` and
`session_lock` is excluded. This also fits the older records rather than
rewriting them: their `session_lock` address was `0x60426284`, exactly the second
line above with the same module base.

`lock_display_devices()` calls `pthread_mutex_lock(&display_lock)` at shipping
RVA `0xfa4a3`; the guest return address is RVA `0xfa4a8`. The following bytes
begin:

```text
c7 84 24 40 09 00 00 00 00 00 00 c7 84 24 44 09
```

That exact post-call signature is now the first identity witness in Box86's
pthread wrapper. Once seen, the wrapper records only attempts, acquisitions and
releases for the discovered mutex pointer. The ring header retains both the
pointer and guest return address so an external reader can compare them against
the live mapped `display_lock` and refuse a mismatch.

The first version proposed instrumenting `session_lock` inside a rebuilt
`win32u.so`. That would have observed the wrong object, and two local Unix-side
win32u rebuilds are already documented to hang the game. The corrected witness
therefore observes the real byte-verified shipping module from Box86, writes no
hot-thread log, and requires no win32u substitution.

## 9. Recovery proves the mutex is the blocking condition

The first debugger attempt used an unavailable `pthread_mutex_t` typedef. It
made no function call and left the mutex unchanged. The second attempt attached
to the recorded owner TID and used the raw address:

```text
pthread_mutex_unlock((void *)0x6040623c) -> 0
mutex after unlock                       24 zero bytes
```

Three seconds later, in the same process:

```text
source / final GL calls       5,018,093 / 5,018,093
guest fallback                0
frame witness                 17,861
main                          back in ntsync
wined3d_cs                    runnable
```

The recovery screenshot showed a correctly rendered `MISSION FAILED` screen.
A later read reached 7,752,647 equal source/final calls and 20,154 frames with
the mutex still zero. Its last 64 hashes collapsed to one because the screen was
now static, but all 256 brightness samples were lit and 43 of 255 comparison
samples still differed. That is a static menu, not a return to the p67 black
frame.

The one-time unlock is evidence, not a production fix. It establishes that this
mutex was the blocking condition and that the queued renderer resumed after it
was released. No timing number can be taken across the freeze, GDB attachment or
recovery.

## 10. Revised next queue

The mutex investigation and renderer measurement do not have to serialize. The
freeze happened after a long correct p68 run, entry 38 was not the owner/waiter
boundary, and the capture does not make p68 causal. The reliability witness is
now built and was passively armed in the completed p68b run. That run did not
freeze, although its final ring read was lost as recorded in section 10.2. The
renderer result closes entry 38. The p69 gate below has now also completed and
failed picture correctness; section 10.5 is the active renderer branch.

### 10.1 Built and passively armed: bounded display-lock history

`MGS2_DISPLAY_LOCK_HISTORY=1` now enables a 256-record memory ring in Box86's
pthread wrapper. Each target record is fixed-size and contains:

```text
sequence, TID, event ATTEMPT/ACQUIRED/RELEASE, mutex
guest EIP and ESP, lock word, owner TID, result, 16 guest-stack words
ring header: discovered mutex and exact guest return address
```

Before the target is discovered, the wrapper compares the current guest return
bytes with the exact `lock_display_devices()` callsite in the shipping module.
After discovery, unrelated mutexes pay only the env/target comparison. There is
no stderr output. ATTEMPT is committed before `pthread_mutex_lock()`, so a
self-waiting owner leaves a durable last record even though the call never
returns.

`harness/display_lock_history.py` reads the ring through `/proc/PID/mem`, derives
the live Box86 and win32u bases from `/proc/PID/maps`, resolves both mutex
symbols from the exact mapped files and refuses unless the captured target is
the live `display_lock`. It marks an ATTEMPT with `lock=2` and `owner=TID` as a
SELF-WAIT and symbolises retained guest addresses.

The correction gate is now specific: if a freeze contains an unmatched
ACQUIRED followed by a same-owner ATTEMPT, inspect the captured display-update
call chain and shorten or split that lock scope. If the address or history does
not agree, do not change `display_lock` and do not make it recursive. Do not
wait for reproduction before section 10.2.

### 10.2 Complete: p68 has no measurable performance value

The old entry-38 A/B fallback was invalid for a magnitude claim because only
the guest arm paid one high-frequency `RunFunctionFmt()` call. p68b moves the
selector to a validated guest control block:

```text
both arms   execute the same guest-side branch, route/settle reads and counter
routed arm call the entry-38 bridge
guest arm  call wined3d_context_gl_draw_primitive_arrays() directly
switch     shared word updated at displayed-frame boundaries
run        one process, owner heavy save, fixed 1992 MHz, stop before death
accept     source-call counts balanced and picture witnesses valid in both arms
```

The block is registered only after all four magic/version/size/signature
witnesses agree. The existing frame tick publishes the next arm only at the
displayed-frame boundary and reads cumulative per-arm guest counters when an
ABBA cycle closes. Until registration, or if the TLS correctness guard fails,
the wrapper remains fail-closed; a valid timing run therefore also requires zero
guest fallbacks. The normal log format and `island_ab_read.py` stay unchanged.

The paired build was deployed byte-for-byte and run on the handheld:

```text
entry 38 identity       marker +11, canonical RVA 0x000b9aa0, generated from p68b
class B / class C       1,613 / 379; all native IDs registered
class C source          preserved from the verified generated header because the
                        exact mounted opengl32.dll was offline; no substitute DLL
                        was used
ARM marker control      no x86 island marker bytes in the ARM objects
Box86 ring symbol       GLOBAL after strip; 25,640-byte bounded public record
launcher               FINALPLAY7's 18 entries plus 38; entries 34/37 absent
production defaults     untouched
```

The decision policy was registered before reading the run:

```text
robust paired delta <= about 0.3 ms/frame   close entry 38 as a performance root
about 0.3--1.0 ms/frame                    keep the record; spend no more research time
robust paired delta >= about 1.0 ms/frame  production candidate after a normal soak
```

These are project-priority gates, not significance thresholds. The run produced
46 complete cycles and passed its tick control, 11,776 harness ticks against
11,700 whole launcher frames. The normal reader reports:

```text
all cycles             n=46  median -0.115  mean -3.347  sd 16.26 ms/frame
balanced within 2%     n=28  median +0.002  mean +0.109  sd  1.10 ms/frame
sign                         13 of 28 balanced cycles favour routed
arms                    routed 40.6 ms/f; guest 40.5 ms/f  -> -0.07 fps
```

The large negative unfiltered mean is scene imbalance, visibly concentrated in
cycles 36--38 as the route became heavy. The balance filter moves the median by
only +0.116 ms/frame and removes that contamination. The result is not carried
by a light or static state: the 17 balanced cycles on the repeated 28k-call
plateau give median +0.046 ms/frame, mean -0.076 and only 8/17 favour routed.
The six balanced high-call cycles 39--46 give median +0.007. The owner reported
death immediately after cycle 46, but the log has no semantic scene marker, so
none of cycles 36--46 is relabelled as combat or MISSION FAILED performance.
Their inclusion or exclusion does not change the zero result.

An early external correctness read, after 2,571 displayed frames, found TLS
READY, zero guest fallbacks and 64/64 unique retained frame hashes. In this
symmetric design the source counter covers the routed arm only while final GL
submissions cover both arms, so source/final equality is neither expected nor
claimed. The run log contains no island fault, unresolved GL trap, SIGILL,
SIGSEGV or unhandled exception and continued through cycle 46 until explicitly
stopped after the owner's death report.

The requested final memory read was lost to an operator error: the first stop
command looked up the process by an exact name and got no PID; the corrected
command used PID 2694 but invoked both readers from a nonexistent `harness/`
subdirectory before sending TERM. The earlier correctness read and complete A/B
log survive, but no final post-death frame or display-lock ring state is claimed.
The process stopped after TERM, no second game process remained, and the research
bind mounts were gone. This capture error does not affect the paired timing
records already emitted by the guest control block.

**Decision:** entry 38 is correct but has no useful frame-rate effect. It falls
inside the pre-registered <=0.3 ms/frame gate and is closed as a performance
root. It is not a production candidate and receives no further timing work.

### 10.3 Complete but inadmissible: the concrete p69 state-apply build

The highest-value untested combination is not another coarse CS handler. Keep
context acquisition, activation/current-context ownership and release in guest
x86, but route only `context_apply_draw_state()` to ARM. The source explicitly
documents this boundary with `/* Context activation is done by the caller. */`.
The function receives the already-selected `context` and does not choose or make
the WGL context current itself.

Provisional cut:

```text
guest x86   context_acquire() and current-context establishment
guest x86   render-target and depth/stencil load/prepare
ARM p69     context_apply_draw_state(context, device, state, indexed)
guest x86   remaining bookkeeping and final DRAW tail
guest x86   barriers, cleanup and context_release()
```

The built entry is 39 and uses the one-pointer argument/result ABI. Its identity
was generated from the paired DLL rather than entered by hand:

```text
ABI                  vFp: context, device, state, indexed, BOOL result in object
marker / RVA         +9 / 0x000b8ae0
armed identities     all 19 required ids present and within the 64-byte witness
class B              1,614 native IDs; registration control passed
ARM marker control   no x86 island marker bytes in the ARM objects
```

This boundary is materially larger than entry 38. It contains resource preload,
shader-resource and UAV loads, stream-output and stream-buffer loads,
stream-info maintenance, dirty-state callbacks, resource bindings, FBO
validation and `shader_apply_draw_state()`. It also begins only after guest code
has established the current context, separating the two halves that p66/p67
changed together.

The first run was always-routed correctness only, not FPS. It reused the existing
TLS sync, translated GL table, unresolved-slot trap, class-B state/backend
callbacks, mutable-state audit, final-submission census and frame witness. The
direct-root mutable-state audit ran before the device launch.

```text
capture     p69 calls and FALSE returns, final submissions, fallback/faults,
            bounded frame content and an external screenshot
refute      black/wrong frame, native fault, unresolved dispatch, or lost work
success     correct changing picture, zero fallback/fault and final submissions
            advancing consistently with the guest path
```

The corrected mutable-global audit procedure passed before deployment: entry 37
separately found both mandatory controls, TLS and `mgs2_batch_ptr`; the direct
p69 root then ran without importing that entry-37-only requirement. It found a
526-function closure and 45 referenced writable objects. Review found the
already synchronised TLS/batch state plus ARM-owned GL translation/census/cache
state, not another authoritative guest object to copy.

That count is superseded by section 10.5. The source-extent parser counted
braces inside GLSL strings and silently lost `shader_glsl_apply_draw_state()`
and later functions. After literal/comment masking, the closure is 733 functions
and the writable-object census is 63. It adds the expected shader-side native
GL/cache/census objects but still does not identify another authoritative guest
global. More importantly, that audit never answered whether ARM and i386 assign
the same offsets inside guest-owned heap objects.

The exact live Box86, WineD3D and Wayland targets were `cmp`-identical. One
process armed FINALPLAY7's 18 entries plus 39, excluding 34/37/38; both class-B
witnesses agreed on guest base `0x7a280000`, and entry 39 canonically matched
`0x7a338ae0`. The stopped bounded capture was:

```text
p69 calls / FALSE / fallback       1,357,984 / 0 / 0
final GL submissions               1,357,983, all arrays
frame witness                      6,921 frames; retained 6,858..6,921
retained content                   1 unique hash, 0/256 lit, 0/255 changed
independent grim screenshot        640x480, all black
fault / unresolved-call trap       none
CPU                                performance, current=max=1992000 kHz
```

The one-call source/final difference is expected from stopping the process
between the entry counter and its final submission; it is evidence that work
was still advancing, not a lost draw. More importantly, advancing final GL
submissions did not produce picture content. The log contains 23 complete
300-frame PRESENT windows and the stopped witness is already at frame 6,921, so
this is not a brief black transition. The independent screenshot confirms the
memory witness rather than relying on counters alone.

**Decision:** the concrete p69 artifact is rejected and has no FPS A/B or
performance claim. Its black picture remains valid observation, but section
10.5 shows that this build was not an ABI-valid test of native draw-state apply;
it cannot close that architecture. The diagnostic build also emits dispatch
lines, which independently forbids timing this run. The process was stopped,
all research mounts were removed, and the byte-checked FINALPLAY7 files remained
unchanged.

### 10.4 No timing or fused draw core follows the invalid p69 artifact

The concrete build has no positive branch: a symmetric A/B cannot rescue a wrong
picture, and combining it with the zero-value p68 tail would only widen an
ABI-invalid boundary. This does not forbid a future state-apply design whose
guest-owned heap layouts pass admission. The next design leaves guest x86 in
control and moves only separately admitted phases.

### 10.5 Complete: the shared-heap ABI audit finds the exact 32-byte shift

The p69 run plus the ABI audit establish a narrower result than the first
version of this section claimed:

```text
concrete p69 ARM artifact           not ABI-safe and picture-incorrect
native final arrays tail            safe
```

`harness/island/full/island_abi_closure_audit.py` now starts at
`context_apply_draw_state()`, uses the corrected 733-function direct/source/ops
closure, finds aggregate types named by those functions, follows their member
types transitively and compares the matching i386 and ARM DWARF per translation
unit. Private types remain TU-qualified. It reports size, inferred alignment,
all member byte/bit offsets, referencing functions and a conservative ownership
classification. UNKNOWN is not treated as safe; a mismatch classified
guest-owned or shared is a hard failure.
The default output is the bounded mismatch report; `--all` emits every
TU-qualified row and every member offset as `i386/ARM`.

The audit's controls both pass: `shader_glsl_apply_draw_state()` is in the
closure, and all four known MS-bitfield propagation points are detected. The
result is 3,967 TU-qualified aggregate rows, nine mismatches and nine hard
failures. The decisive `glsl_shader.c` chain is:

```text
type                              i386   ARM    decisive later fields
texture_stage_op                    16    12
ffp_frag_settings                  132   100
ffp_frag_desc                      148   116
glsl_ffp_fragment_shader           164   132    id              148 / 116
                                                linked_programs 152 / 120
                                                source          160 / 128
```

This is the exact 32-byte displacement proposed by review, verified against the
configured i386 objects and fresh ARM objects built with the island flags. The
top-level controls still agree -- `shader_glsl_priv` 144/144,
`glsl_shader_prog_link` 2968/2968, `glsl_context_data` 20/20,
`wined3d_context` 1020/1020 and `wined3d_state` 7276/7276 -- so checking only
those types would have missed it.

The static result does not alone prove which wrong value p69 read at runtime,
but it proves the root is not ABI-safe: native code interprets a shared FFP
cache node's `id` 32 bytes before the guest field. Worse, on a cache miss ARM
allocates a 132-byte `glsl_ffp_fragment_shader` and can insert it into the same
tree where guest x86 expects 164-byte nodes. One process can therefore acquire
mixed-layout cache nodes. That fits the observed shape without requiring a
fault or a missing draw, and it makes a clean process mandatory for every
correctness phase. It does **not** prove that an ABI-safe native state-apply
design would be picture-incorrect.

### 10.6 Complete admission and offline ranking; phase A is next

The new audit is now a pre-device gate rather than a post-mortem. Its first
control is deliberately positive: stopping pointer-pointee expansion was needed
because the earlier conservative graph falsely pulled teardown-only FFP types
into measured entry 23. Embedded structs and arrays still propagate
transitively; a pointee actually dereferenced by native code is independently
seeded by the type named in that function body. The mandatory self-test is:

```text
entry 10   wined3d_buffer_load                         PASS
entry 23   wined3d_rendertarget_view_load_location     PASS
entry 38   wined3d_context_gl_draw_primitive_arrays    PASS
p69 / D    context_apply_draw_state                    FAIL
```

The four phase descriptions are one source of truth shared by ABI admission and
profile attribution. Each is a contiguous original control-flow span, including
its bookkeeping:

```text
A  native resource/stream preload
   tex-unit map; shader resources; textures/constant buffers/UAVs;
   stream-output, vertex/index buffers; stream-info maintenance
B  native dirty-state apply only
   the whole dirty-state loop, every GL state-table callback and bitmap clear
C  native resource bindings and FBO validation only
D  native shader_apply_draw_state() only
   known ABI-unsafe shader/cache phase; excluded from FPS work
```

Against the same configured i386 DWARF and fresh ARM objects, the phase matrix
is:

```text
phase   closure functions   aggregate rows   mismatches / hard   admission
A              548              1,096               0 / 0          PASS
B              167                372               0 / 0          PASS
C               21                171               0 / 0          PASS
D              235                468               9 / 9          FAIL
```

No new device profile was needed. `harness/island_phase_profile.py` reads the
existing exact island41/p56 capture, recovers its embedded 1,616-entry class-B
RVA/name table from the byte-checked Box86, uses 4,315 FDEs from the exact
stripped p56 to name only exact function starts, and applies the same phase
closures. Unique cycle-weighted attribution is:

```text
bucket              cycles        % all user   % guest WineD3D
A                 1,681,154,014       2.878          10.87
B                 1,516,423,719       2.596           9.81
C                   300,105,357       0.514           1.94
D                 2,439,081,450       4.176          15.78   ABI-unsafe; excluded
shared/ambiguous    981,425,107       1.680           6.35
other             6,974,836,149      11.941          45.11
unresolved        1,568,189,974       2.685          10.14
```

The denominator is the profile's 58,409,426,072 user cycles; guest WineD3D is
15,461,215,770. These are CPU-cycle shares, not ms/frame. The large parent
`draw_primitive()` block and work inlined into `context_apply_draw_state()`
cannot be divided offline, while functions reachable from several phases stay
`shared/ambiguous`. The report is nevertheless sufficient to rank the three
admitted candidates: A first, B close behind, C distant.

This ranking selected only contiguous phase A as the next research entry. Guest
x86 keeps `context_apply_draw_state()` control flow, acquire/current ownership,
phases B/C/D, final draw and release. Section 10.7 records its implementation
and completed gameplay correctness gate. That result permits a symmetric
same-process A/B and the existing roughly 1 ms/frame priority gate. Only a
useful phase-A result justifies phase B or a later fused ABI-safe pre-shader
root. D receives no FPS run; its optional program witness is causality work
only. Entry 34 remains unmeasured and is not reclassified.

### 10.7 Complete: p70 phase A passes the gameplay correctness gate

Wine patch 67 makes entry 40 the whole original resource/stream preload
transaction, including stream-info and index-buffer bookkeeping. It restores
`draw_primitive()` to the direct guest `context_apply_draw_state()` path; the
historical p69 entry remains compiled but is not armed. The exact device list is
FINALPLAY7's 18 entries plus 40, excluding 34/37/38/39.

Static admission completed before deployment:

```text
entry 40 identity       marker +29, canonical RVA 0x000b9410
class B                 1,616 native IDs, all registered
ABI closure             548 functions / 27 TUs / 1,096 aggregate rows
ABI mismatch / hard     0 / 0 -- PASS
indirect calls          53 routed, 0 unrouted -- PASS
ARM marker control      no x86 island marker bytes in ARM objects
```

The first final Box86 link accidentally omitted the saved libm compatibility
wrap flags and requested `GLIBC_2.43`; the device rejected it before Wine or the
game started. No game process or mount survived that failed start. The rebuilt
artifact retains `MGS2_GLIBC24_COMPAT` and the eight established libm wrappers;
its newest libm requirement is `GLIBC_2.4`, and `box86 -v` runs on the device.

The compatible p70 pair was deployed only under separate research filenames
and verified byte-for-byte. The first process armed 19 of 39 entries, both
class-B witnesses agreed on guest base `0x7a280000`, entry 40 matched
canonically, TLS became READY and PRESENT advanced. Its title-screen read was
the early non-gameplay gate.

The requested manual run then started from a clean process with the same exact
pair and entry list. After the owner loaded and exercised the gameplay scene,
the final bounded snapshot was:

```text
phase-A calls / guest fallback     2,172,004 / 0
final GL submissions               2,172,004, all arrays
frame witness                      5,087 frames
retained range                     5,024..5,087
retained content                   64 / 64 unique
minimum lit / changed              252 / 256; 255 / 255
last retained hash                 c1d485b0
fault / unresolved-call lines      0
CPU                                performance, current=max=1992000 kHz
temperature                        62.777 C at the final capture
```

The independent 640x480 capture shows the real game scene: Raiden, several
guards, lit geometry, the CAUTION/radar HUD and dialogue. It is neither the
title/attract route nor a black/static presenter. Source and final counts agree
exactly, so the native phase does not drop work; the 64 unique witnesses and
the screenshot prove that equal calls are not submitting an empty image.

All three live targets were `cmp`-identical to their named files: p70 Box86,
p70 WineD3D and the p67 Wayland frame witness. The display-lock recorder was
enabled but its exact target callsite did not execute (`writes=0`); this run
therefore says nothing new about the intermittent mutex deadlock. No freeze was
reported or captured.

The log contains scene-dependent 300-frame windows, including the later heavy
7.4--7.6 fps stretch. They are one always-routed correctness configuration,
not timestamp-paired against guest WineD3D. They must not be quoted as a p70
performance effect in either direction. Correctness PASS only authorises the
next symmetric same-process A/B.

After every memory read, screenshot and map/hash capture had completed, only
the recorded PID 2911 was sent TERM. The process and wineserver exited and no
p70/Wayland research bind mount remained. Production defaults were never
changed.

Exact research artifacts:

```text
box86-island49-p70-phase-a      ceee8c9118e9db6dd96ac912cef264973340b9ade5f6423cc162d584e1b5ee7b
wined3d_p70_phase_a.dll         198f4d04bca5b2132ae8c2c4e924487831b6a1370b479e63c617223085094486
launch-p70-phase-a-correctness  8a4cbf3649c2eba07549dcd39f4933208749ec24d7a578ef076db87d05481513
p70 correctness reader          f2c282576691fabb1f620e149010adaec20fa07eed1ceee264d886e65a1ccb00
```

Production launch defaults and the byte-checked FINALPLAY7 files were not
changed.

### 10.8 Do not schedule a `WINE_NO_TRACE_MSGS` A/B

That proposed cheap experiment is already the documented build state, not a new
arm. The production recipe in `README.md` defines both
`WINE_NO_TRACE_MSGS` and `WINE_NO_DEBUG_MSGS`, and performance brief 29 records
the release WineD3D build with TRACE/debug removed and 30 `draw_primitive()`
hooks reduced to zero. Rebuilding a nominal p56-equivalent with the same define
would not create an independent hypothesis.

### 10.9 Built, not yet run: p70b symmetric A/B for phase A

The p70 correctness configuration always routes, so its frame windows are
scene-dominated and carry no performance claim. Wine patch 68 and Box86 patch 14
add the measurement arm with the design that made entry 38's number honest:
guest WineD3D keeps the selector, and each arm is one guest call from the same
call site inside `context_apply_draw_state()`.

```text
routed arm     call marked mgs2_draw_state_phase_a_island() -> Box86 bridge
               -> ARM thunk -> ARM mgs2_draw_state_phase_a_body()
control arm    call guest mgs2_draw_state_phase_a_body() directly
both arms      same enabled/route/settle reads and the same per-arm counter;
               phases B/C/D, final draw, barriers and release stay guest
```

Neither arm pays a `RunFunctionFmt()` re-entry. The control block is
byte-identical to the p68 draw-tail control, so Box86 validates and publishes
into it through one path; `mgs2_island_ab.c` no longer hard-codes entry 38 in the
registration and selector test but asks one `mgs2_ab_guest_capable()` predicate.

The first draft of the patch put the control arm in its own unmarked guest twin
of the entry point. The linker placed that twin **22 bytes ahead of entry 0x28's
marker**, inside the 64-byte window Box86 scans forward from a branch target, so
calling the twin matches an id it does not own. The canonical-RVA identity added
after the 2026-08-19 entry-22 defect would have rejected it, so this was not a
picture risk -- but the layout is avoidable, and the class is now checked
statically rather than trusted at runtime:

```text
harness/island/full/island_marker_check.py
  --target SYMBOL   the control arm's call target must have NO marker in its own
                    64-byte window, so its safety does not rest on the
                    canonical-RVA identity having been established yet
  --armed LIST      severity follows the configuration: a finding for an id this
                    run does not arm is IGNORED and does not affect the exit code
  neighbours        every function starting within 64 bytes ahead of a marker,
                    with whether that id is identity-protected; fatal only for an
                    unprotected armed id
```

The `--target` invariant is the one that must hold before the device, because
the canonical-RVA check is a second witness that only becomes decisive once the
guest module base is known. On the shipped p70b DLL it holds outright:

```text
mgs2_draw_state_phase_a_body   @ 0x100b8350   no marker in +0..64 -- PASS
                                              nearest marker is 0x28 at +2038
mgs2_draw_state_phase_a_island @ 0x100b8b40   0x28 at +6, its own
```

So the control arm is marker-free by layout, not by rejection, and no physical
separation is needed.

With the armed list of this configuration the whole check now exits zero. It
still reports four neighbours -- ids 0x11, 0x27 twice and 0x33, all
identity-protected, matching the five the one-off 2026-08-19 scan found on the
mounted p56 DLL -- and the three legacy cases (id 0x14 in two functions; ids
0x0b and 0x22 with markers past the window) are printed as IGNORED because no
launcher arms 11, 20 or 34. Feeding those three ids to `--armed` returns exit 1,
so the tool still fails on them for a configuration that would arm them.

Static admission for the built pair:

```text
entry 40 identity       marker +6, canonical RVA 0x000b8b40 (moved by the split)
identity control        19 required armed ids, 0 missing, 0 beyond the window
marker control          exit 0 for the armed list; entry 0x28 in exactly one
                        function, no neighbour, and the control arm's target has
                        a marker-free window
ABI closure phase A     548 functions / 27 TUs / 1,096 aggregate rows
ABI mismatch / hard     0 / 0 -- PASS
ABI direct root         549 functions, same 1,096 rows, 0 / 0 -- PASS
indirect calls          53 routed, 0 unrouted -- PASS
class B                 1,616 native IDs, all registered by the ARM objects
ARM marker control      no x86 island marker bytes in the ARM objects
mutable state           46 writable objects; the only new one is the ARM copy of
                        mgs2_phase_a_ab, which no native closure function
                        touches -- the selector is read and written by guest code
                        and by Box86 through the pointer in the argument object,
                        exactly as mgs2_draw_tail_ab was for p68b
libm compatibility      the eight wrapped libm symbols are GLIBC_2.4, identical
                        to the accepted p70 binary; no diagnostics build flag
```

The tooling reruns that back the phase choice were repeated on the current tree
and reproduce: the ABI self-test is entry 10/23/38 PASS and p69/D FAIL; the phase
matrix is A 548/1,096/0 PASS, B 167/372/0 PASS, C 21/171/0 PASS, D 235/468/9
FAIL with the same `texture_stage_op -> ffp_frag_settings -> ffp_frag_desc ->
glsl_ffp_fragment_shader` chain; offline attribution of the island41 capture is
again A 2.878%, B 2.596%, C 0.514%, D 4.176% of all user cycles. Phase A's
closure counts 549 rather than 548 when the audit is seeded from the direct root
instead of the phase span, because the split added the thunk itself.

The launcher is a timing configuration, not a second correctness run. It arms
the selector, the production entries and the frame tick, and nothing else:

```text
armed        FINALPLAY7 entries + 40, guest selector, ABBA/tick machinery,
             per-arm counters inside the guest control block
not armed    MGS2_DRAW_CORRECTNESS, MGS2_PHASE_A_CORRECTNESS, MGS2_FRAME_WITNESS,
             MGS2_REINFORCEMENT_CENSUS, MGS2_DISPLAY_LOCK_HISTORY, the p67
             witness presenter, and any diagnostics build flag
kept          MGS2_GL_STATS=300 with WINEDEBUG -all,err+waylanddrv
```

`MGS2_GL_STATS` is kept deliberately against the otherwise-strict rule: `present
stats` is one `winewayland.drv` ERR line per 300 displayed frames, produced on
the other side of the emulator, and it is the only non-circular check of the A/B
tick rate -- ticks against per-arm frame counts is circular, because the blocks
are defined in ticks. Everything correctness-related is dropped because the
always-routed p70 capture already settled the picture.

**Not run.** There is no device result and no FPS number for p70b.

#### The stop rule, corrected: phase B is not judged by phase A

The first version of this rule said a phase-A median under roughly 1 ms/frame
closes the whole pre-shader idea. That does not follow, and the reason is in this
brief's own numbers. The guest arm of p70b is FINALPLAY7, which already routes
entries 10 and 23; phase A's closure *contains* those families, so part of
phase A's offline weight is cost the production build has already removed.
Routing phase A merely absorbs those closures into the ARM phase. Therefore:

```text
offline phase weight  !=  incremental opportunity over production
```

Phase B is dirty-state apply, at an independent 2.596% of all user cycles --
almost the same weight as A -- and its overlap with the existing production
entries is a different, unmeasured quantity. So it earns its own measurement
whatever A does:

```text
A >= 1.0 ms/f       production candidate; B still worth measuring for more
A 0.3 .. 1.0        A not promoted on its own; B still measured
A <= 0.3            A closed as a root; B still gets ONE bounded correctness +
                    A/B shot, on its own ~2.6% independent weight
A and B both ~0     then, and only then, close the native pre-shader branch
C                   not measured standalone at 0.514%; absorb it later into a
                    fused ABI-safe root, where it is nearly free
D                   untouched until the FFP ABI question is decided; no FPS run
```

#### Pre-registered before the p70b run

Recorded here before any device data exists, so the classification cannot be
chosen after seeing the number.

```text
sign convention   delta = median(routed - guest); NEGATIVE means ARM is faster
primary result    median over cycles balanced to <=2% call count, both arms
                  non-zero; target at least 25-30 balanced cycles, p68b scale
secondary         sign count, plateau subset, high-call subset, per-arm means,
                  harness ticks against the MGS2_GL_STATS displayed-frame count
outliers          the all-cycles mean must NOT override the balanced median when
                  death or scene-transition outliers reappear; p68b showed why
                  (all cycles median -0.115 mean -3.347 sd 16.26; balanced
                  median +0.002 mean +0.109 sd 1.10)

delta <= -1.0 ms/f     A is a production candidate; correctness soak, then FPS;
                       B investigated separately afterwards
-1.0 < delta <= -0.3   effect is real but A is not promoted alone; B proceeds
|delta| < ~0.3         A closed as a performance root; move to B
delta > +0.3           A actively costs performance; closed with more
                       confidence; B remains its own hypothesis
```

No pretty win rate is required: a delta near -1.5 ms/frame with the plateau
subset agreeing in sign and the variance explained by the scene is enough, and a
-0.15 ms/frame does not become useful because the sign count looks good.

One conditional follow-up: if the result lands right on a boundary -- roughly
-0.25 to -0.4 ms/frame -- run one short additional A/B with `MGS2_GL_STATS`
unset before classifying A, so the decision is not argued over a tenth of a
millisecond of presenter-side logging. At -1 ms or beyond it is unnecessary; the
line is one ERR per 300 frames and is paid identically by both arms.

The staged device copies were verified byte-for-byte after upload:

```text
box86-island50-p70b-ab       3aeb7c73...3051541
wined3d_p70b_phase_a_ab.dll  23fe29ac...0a3ca76a1
launch-p70b-ab.sh            fe8fc1b9...a5cc97ae
```

`/storage` had 561 MB free at that point, which is enough for this log but not
for another pair of research artifacts; prune older ones before the next build.
Production launch defaults and the FINALPLAY7 files were not touched, no process
was started, and `/proc/mounts` held no research bind mount.

One further caution on the ranking that chose A: `island_phase_profile.py`
attributes a sample by whether the sampled function is a member of a phase
closure, not by proving the call chain that sample came from. Shared helpers can
therefore inflate a phase. The 2.878% is a ranking signal and an upper bound on
what phase A could be worth, never a prediction of the A/B result.

### 10.10 Measured: p70b phase A is a real negative delta, band 2 by the rule

Superseded as the entry point by
`MGS2_PHASE_A_NATIVE_MEASURED_2026-08-21.md`, which is the standalone record of
the p70b build, its controls and this measurement. This section stays as the
in-place result so the p69 -> p70 -> p70b thread reads in one place.

One clean process, the exact staged pair, gameplay driven by the owner. The run
ended after cycle 49; the reduction below is the whole log.

```text
all cycles             n=49   median -0.759   mean -1.642   sd 10.79
balanced (<=2%)        n=27   median -0.626   mean +0.280   sd  6.29   PRIMARY
sign                          20 of 27 balanced cycles favour routed
plateau 66,528 calls   n=10   median -0.944   mean -0.915   sd  0.55   10/10 routed
high-call >=66,528     n=16   median -1.081   mean -1.378   sd  2.64   14/16 routed
arms                   routed 48.3 ms/f, guest 48.0 ms/f  ->  -0.12 fps
filter moved median    +0.133 ms/frame (noise removed, does not change the answer)
tick control           12,544 harness ticks against 12,300 GL_STATS frames
                       (102.0%, inside the one-block lag of 256)
```

Sign convention as pre-registered: negative means the ARM route is faster.

The pre-registered count target was 25--30 balanced cycles and 27 were obtained,
so the run is complete on its own terms. Applying the table to the primary
metric, -0.626 ms/frame falls in `-1.0 < delta <= -0.3`: **the effect is real,
phase A is not promoted on its own from this data, and phase B proceeds
regardless.**

The homogeneous evidence is stronger than the session median and is what makes
the effect real rather than noise: ten balanced cycles at exactly 66,528 calls
per arm give -0.944 ms/frame with sd 0.55 and all ten favouring routed. The
session median is diluted by lighter scenes and menus where the entry is cold.
The high-call half gives -1.081 with 14 of 16 favouring routed.

Two things are reported against the result, not around it. The balanced *mean* is
+0.280 while its median is -0.626, and the per-arm means make routed look 0.12
fps slower; both are the death and scene-transition outliers the rule
pre-committed to excluding from the primary read -- cycle 38 is +19.0 and cycle
41 is +11.0, at 20% and 15% call imbalance. And the largest single balanced
cycle, 49, is -9.762 ms/frame at 128,980 calls in a 114 ms/f scene: it hints
that the gain scales with draw-state load, but it is one cycle and carries no
weight on its own.

There is a second, smaller plateau at 76,272 calls -- cycles 43--45 give
+2.832, -1.102, -1.245 -- which is why promotion should rest on a longer
plateau-dominated soak rather than on this session's median.

#### How the run ended, and what it does not say

The owner reported the game freezing. The evidence is an exit, not a live
deadlock: no box86 process remained, `/proc/mounts` held no research bind mount
(so `launch-play.sh`'s EXIT trap ran), the log ends on a complete cycle-49 line
with no SIGILL, SIGSEGV, island fault or unresolved-dispatch line anywhere, and
`dmesg` shows no OOM kill. Frame times just before the end were 9.5 fps with 223
frames over 100 ms, which is what a player reads as a freeze. A stale
`wineserver` survived and was left alone.

This run therefore says **nothing** about the intermittent `display_lock`
deadlock: the timing configuration deliberately disarmed
`MGS2_DISPLAY_LOCK_HISTORY`, so the one instrument that could have identified it
was not recording. That is the price of the clean timing launcher, and it was
paid knowingly; a freeze reproduction needs the correctness configuration.

```text
logs/rg353vs/p70b-ab-20260821/p70b-ab-20260821.log
  b11fa7426247677bc516b5931baa54adf2c58f2d99663cbfdf3f1591b4f757e4
harness/island_ab_read.py   plateau and high-call subsets added for this read
```

## 11. What is and is not decided

```text
decided       entry 38's lower boundary can produce the correct changing picture
decided       coarse entry 37 remains closed; p68 does not rehabilitate it
decided       direct-mutex mode did not close the self-owned gameplay deadlock
decided       unlocking the captured owner mutex releases the stopped process
decided       the frozen mutex is win32u display_lock; exact symbols exclude
              session_lock, whose address in the same mapping is 0x60426284
decided       p66/p67 did not isolate draw-state apply from context ownership
decided       WINE_NO_TRACE_MSGS is already in the production build recipe
observed      concrete p69 produces an advancing all-black frame even though
              acquire/current ownership/final draw stay guest; because its ABI
              is invalid, this does not reject native state apply as a concept
decided       p69 is not ABI-safe: shared glsl_ffp_fragment_shader.id and its
              following fields are 32 bytes earlier in ARM than in guest i386
implemented   bounded display_lock history and symmetric p68b guest selector
implemented   transitive TU-qualified shared-heap ABI audit; corrected source
              closure is 733 functions, not the earlier incomplete 526
validated     ABI admission self-test: proven entries 10/23/38 PASS; p69/D FAIL
admitted      phases A/B/C have zero layout mismatch; shader phase D has nine
              hard failures and is excluded from device FPS work
profiled      existing FINALPLAY7 capture: unique A/B/C shares are 2.878% /
              2.596% / 0.514% of all user cycles; A is the next candidate
implemented   p70 entry 40: contiguous phase A, generated identity, 1,616
              class-B IDs, zero ABI mismatches and zero unrouted indirect calls
validated     p70 gameplay correctness: 2,172,004 calls equal 2,172,004 final
              arrays, fallback/faults zero, 64/64 lit unique retained frames
              and an independent correct gameplay capture
measured      p68b symmetric A/B: balanced median +0.002 ms/frame; entry 38 is
              closed as a performance root by its pre-registered <=0.3 gate
rejected      concrete ABI-invalid p69 entry-39 artifact; no timing or
              performance claim exists, but an ABI-safe split remains open
not decided   whether the 32-byte shader-cache misread is the sole runtime cause
              of p69's black frame; phase D + bounded program witness can prove it
measured      p70b phase A: balanced median -0.626 ms/frame over 27 cycles,
              20/27 favouring routed; the 66,528-call plateau gives -0.944
              (sd 0.55, 10/10) and the high-call half -1.081 (14/16). Real
              negative delta, band 2: not promoted alone, phase B proceeds
not decided   whether phase A alone reaches the >=1.0 ms/frame promotion band;
              that needs a longer plateau-dominated soak, and the second 76,272
              plateau (+2.832, -1.102, -1.245) is why
not decided   whether the p70b run's ending was the display_lock freeze: the
              timing launcher had the recorder disarmed, and the process had
              already exited cleanly with no fault line and no OOM
implemented   p70b entry 40 symmetric guest selector: one guest call per arm,
              no RunFunctionFmt() in either, identity regenerated at +6 /
              0x000b8b40, and every static control passed -- built, NOT run
implemented   island_marker_check.py now reports functions starting inside the
              64-byte window ahead of a marker, takes the run's armed list so a
              real defect is not lost among known unarmed ones, and asserts that
              a named control-arm target has a marker-free window
validated     p70b's control-arm target is marker-free by layout: the nearest
              marker is entry 0x28's own, 2,038 bytes ahead, so this does not
              depend on the canonical-RVA identity being established yet
decided       a phase-A median below 1 ms/frame does NOT close phase B: the p70b
              guest arm already contains production entries 10/23, so phase A's
              offline weight overstates its incremental opportunity, while phase
              B's 2.596% overlap with production is a separate unmeasured
              quantity. B gets one bounded shot regardless of A's result
not decided   whether p68 changes freeze frequency or caused this occurrence
not decided   the exact recursive call chain into display_lock
not decided   a production mutex fix; the debugger unlock is recovery only
production    FINALPLAY7 remains unchanged; entry 37 and concrete p69 are
              rejected; entry 38 is closed as a zero-value performance root
```

## 12. Artifacts

```text
device/launch-p68-correctness.sh
binaries/box86-island46-p68-tail
binaries/wined3d_p68_draw_tail.dll
binaries/winewayland_p67_frame_witness.so
harness/p67_correctness_read.py
harness/island/full/island_mutable_state_audit.py   --root support
harness/island/full/island_abi_closure_audit.py
  transitive TU-qualified i386/ARM layout admission + proven-root self-test
  5a05a92389fae331db2173f8b0bb04d98605d91daed40fe81c14e83b3d8fec04
harness/island/full/island_draw_phases.py
  one reviewed definition of contiguous A/B/C/D spans and callback families
  66056a03960a20becc4d18769857ef360fcc44e1b275822f1246fd54253e4371
harness/island_phase_profile.py
  exact embedded class-B + p56 FDE offline phase attribution
  4a51c72c1984d0e845cac51c047a63363d02a3867fb694794bc27644f64a4d24
harness/island/full/island_mutable_state_audit.py
  reusable multi-root source graph for phase closures
  07c5d18e4d0f6d61c91a9bffd12a8758af92ebb17ce7cf41f2470a3a6abc1e31

device/launch-p68-ab.sh
  3c61679eef9cd3903a8fa9c4a1614ac602b670a7ae0095fec08aa99e67c7a123
binaries/box86-island47-p68-ab
  17d4b06880d55cb9cf411af30103e0df591518b548275864058197f53691a455
binaries/wined3d_p68b_draw_tail_ab.dll
  e463f682846e548aef801f5ba5bd8c158b6e96c1fcbb6567929a901c63ad6b48
harness/display_lock_history.py
  e8d2669c4a8e68164d568cc170fbaa7784f3028d0af5e7a8ed7b99ad15cd8fc8
binaries/win32u_glfuncs3.so        exact symbols used for mutex identity
harness/island/full/gen_class_b_table.py
harness/island/full/build_island_objects.sh
  preserve the verified class-C table when the exact mounted opengl32 DLL is
  unavailable; refusing to substitute a different local DLL
wine-patches/64-p68-symmetric-guest-ab.patch
box86-patches/11-p68-symmetric-ab-and-display-lock-history.patch

device/launch-p69-correctness.sh
  a946e81ac6df67b1ca1b8a7f3a8c0ef35c69517cfc476f52ac590c3df49213fd
binaries/box86-island48-p69-state
  4fcfa4ac8f14c38f7633be9b7199204b074183bffc38ea284ad5476d1b684902
binaries/wined3d_p69_apply_state.dll
  d8bb5f42eb6fb4455b39c6eb8f1c7d6f74e552f5d63d82ca683af57c553b39c6
harness/p69_correctness_read.py
  a3818b635f95459f5e161237992c6211e2ad62beeaadaa1a720edf61d6c9525e
wine-patches/65-island-draw-state-dispatch-base.patch
wine-patches/66-p69-context-apply-draw-state.patch
box86-patches/12-p69-context-apply-correctness.patch

device/launch-p70-phase-a-correctness.sh
  8a4cbf3649c2eba07549dcd39f4933208749ec24d7a578ef076db87d05481513
binaries/box86-island49-p70-phase-a
  ceee8c9118e9db6dd96ac912cef264973340b9ade5f6423cc162d584e1b5ee7b
binaries/wined3d_p70_phase_a.dll
  198f4d04bca5b2132ae8c2c4e924487831b6a1370b479e63c617223085094486
harness/p70_phase_a_correctness_read.py
  f2c282576691fabb1f620e149010adaec20fa07eed1ceee264d886e65a1ccb00
wine-patches/67-p70-phase-a-correctness.patch
  cb44a6beaf815115fcc34588b114fe76345dfb738c285d6d2e106ec2daa59852
box86-patches/13-p70-phase-a-correctness.patch
  2ed07174d0f5cd48b03b2badf6a849b389fbf4baa843d00e4446094cd022bb0a

device/launch-p70b-ab.sh
  fe8fc1b9020300f32dee09b419b79e8c8bb2c95f4d7ebee113747fc5a56c97ae
  timing configuration: selector + production entries + frame tick only
binaries/box86-island50-p70b-ab
  3aeb7c733dd896694bbf7ee2a581807a32991ff44907a3fa9e7e5c3df3051541
binaries/wined3d_p70b_phase_a_ab.dll
  23fe29aca711c8e9a0ace560cd4ef681fa2c195c85319e9100f02480a3ca76a1
wine-patches/68-p70b-phase-a-symmetric-ab.patch
  cddb5a485b394ff45a6c56498daabc416c6cfcb0129543c4cd5279d58f59f425
box86-patches/14-p70b-phase-a-symmetric-ab.patch
  40f3dd0ce6c43464e62a977c942dda33d0a7e32b4f8c8dc7e2df15084c513be8
  read the p70b run with harness/island_ab_read.py and
  harness/p70_phase_a_correctness_read.py; no new reader was needed

logs/rg353vs/p70-phase-a-20260821/
  p70-phase-a-heavy-20260821.png
    b70f3d02540cf206d61b5c5080459ad4899e50f0987229512c70926c2ddb1035
  p70-phase-a-heavy-20260821.correctness.txt
    1ce9a8eb2dc5f192be83a0cd8074d945dbce0fce68df06eb511111e84968901a
  p70-phase-a-heavy-20260821.maps
    fe676ba968e113f5ea8f07f9c1ba527a6299f6e44134ee7cc52ef037537ce989
  p70-phase-a-heavy-20260821.status.txt
    2f6c8a1f0925344cc8b400152fbca4c2ca70e1c21a51a327d150d871a9059b65
  p70-phase-a-heavy-20260821.display-lock.txt
    d6d2e93ee4406585f83eae5a61b20ea5e79e416a341d81ebaf21becc1b6c73cb
  p70-phase-a-heavy-20260821.faults.txt
    e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  p70-phase-a-manual-20260821.log
    8eed19b94e66b34326b171c76f78c8cec9ffb7b00acff857d08c4383f626481f
  p70-phase-a-live.png / p70-phase-a-live2.png / p70-phase-a-live3.png
    earlier independent title-screen captures; non-gameplay controls

logs/rg353vs/p69-context-apply-20260820/
  p69-correctness-20260820.log
    7d7d47f8bb5bc5d3a2fa68fb76fbb45588d7b0eb82ba45cdddf3b3431d22d7bc
  p69-live.png
    441da7236f6ffdd8fb4cdfa2d9ce7b8d8df8cf2f7a8e82c530714d92266ce613

logs/rg353vs/cs-draw-p68-20260820/
  p68-correctness-3.log
    9de6b638335d2813d5760bae049565dcde1889a494ba4ee1d4943c533fd88238
  p68-correctness-live-after-recovery.log
    d33b0e45568fdd3c911aaf81699d7c1bad2e1a69d63e404dc5b1efaa89f23411
  p68-freeze-census-20260820.txt
    bf08421f34f261cfe43a7fa9197ba261715ffc8355cde0b47b1f1ea169818f3f
  p68-freeze-recovery-20260820.txt
    02c1c726f53e7668ac4beefda066f549047852052688d33c25339a26d292531d
  p68-freeze-recovery2-20260820.txt
    b4952649fb33acb0c203f80c7706ab806a01b5175210514f779a211e9b27d1c5
  p68-gameplay.png
    c1e043643593d9563331e9948368ff690259d7ec58b85464b38b82a3b2eb4515
  p68-recovered.png
    55c100248a4b33b36a1a37e26d65291828223f59223834d09ec8ffd1ca3cdf2e
  screen.png
    4ffaffc5e151d2b9d42f463f533ba898509940ef7db15b6230862c9e607309da

logs/rg353vs/p68b-ab-20260820/
  p68b-ab-20260820.log
    1c180c05bd768233f40a8e7e4c2ac74fb180503f5a9216c9721983d81f22d637
  p68b-final-maps.txt
    24231882644b139937e844ec35f310a659df3ef8bb115c69744ecbb7217c4758
  p68b-final-correctness.txt / p68b-final-display-lock.txt
    contain the reader-path errors described in section 10.2; the two earlier
    `p68b-ab-*-final.txt` redirections are empty and carry no evidence
```

Source-of-record edits live in the shared trees:

```text
../recovered-session/wine-11.0/dlls/wined3d/context_gl.c
../box86-src/src/mgs2_island_bridges.c
../box86-src/src/mgs2_island_ab.c
../box86-src/src/mgs2_island_entry_identity.h
../box86-src/src/libtools/threads.c
```

Production defaults were not changed by any p68/p68b/p69 artifact, the passive
ring, the A/B run, the offline audit/profile work or the debugger recovery. The
p68b result closes entry 38 as a performance root. The concrete p69 artifact is
ABI-invalid and rejected, but does not close an ABI-safe split of state apply.
P70 phase A passes its gameplay correctness gate, but every performance question
remains open until a symmetric same-process A/B. Nothing is promoted.

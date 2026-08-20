# MGS2 RG353VS — lower native DRAW tail renders; win32u display_lock self-deadlocks (2026-08-20)

Handoff for research. Continues
`MGS2_NATIVE_CS_DRAW_BLACK_FRAME_2026-08-20.md`, which closes the generic
post-batching DRAW boundary after p66 and p67 both produced an empty picture.
This brief begins after that decision. It records the lower p68 boundary, its
successful picture-correctness gate, the separate direct-mutex freeze exposed
during the same session, its exact `win32u` object identity, the debugger
recovery, the symmetric p68 A/B implementation, and the revised bounded queue.

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
                  research-only; entry 37 remains closed
NEXT              p69 correctness only: test native context_apply_draw_state()
                  separately while context acquisition/current ownership and
                  release remain guest. Keep the passive display_lock ring, but
                  do not wait for another freeze and do not spend more timing
                  work on entry 38
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
does not identify it independently as the cause. The status of
`context_apply_draw_state()` is still undecided and should be tested separately.
Entry 37 remains closed, and none of its raw or calibrated timing deltas is an
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
kind of re-entry at about 2.854 microseconds per call, already several
milliseconds per frame at this route's call rate. Section 10 therefore does not
propose timing the current wrapper.

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
renderer result closes entry 38; the next implementation gate is p69 correctness.

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

### 10.3 p69 correctness only: native state apply under guest-owned context

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

Use a new entry, provisionally 39. Prefer the same one-pointer argument-object
ABI as p68, including a result field, unless the generated mounted-DLL identity
proves a direct four-argument/return ABI keeps its marker inside the canonical
witness. Do not hand-assign its RVA or marker offset.

This boundary is materially larger than entry 38. It contains resource preload,
shader-resource and UAV loads, stream-output and stream-buffer loads,
stream-info maintenance, dirty-state callbacks, resource bindings, FBO
validation and `shader_apply_draw_state()`. It also begins only after guest code
has established the current context, separating the two halves that p66/p67
changed together.

The first run is always-routed correctness only, not FPS. Reuse the existing
TLS sync, translated GL table, unresolved-slot trap, class-B state/backend
callbacks, mutable-state audit, final-submission census and frame witness. Run
the direct-root mutable-state audit before the device launch.

```text
capture     p69 calls and FALSE returns, final submissions, fallback/faults,
            bounded frame content and an external screenshot
refute      black/wrong frame, native fault, unresolved dispatch, or lost work
success     correct changing picture, zero fallback/fault and final submissions
            advancing consistently with the guest path
```

Do not hard-code source calls == final GL submissions as a universal invariant
for this higher boundary: state apply may fail a draw and the existing batcher
may change the submission ratio. Record both counts and compare their behaviour
with the guest control. If the observed route remains one-to-one, equality is a
useful additional witness.

### 10.4 If p69 is correct, measure it and then test one fused draw core

After a correct p69 smoke, build the same guest-side symmetric selector: both
arms take the same branch/tick path, the routed arm calls the island entry and
the guest arm calls `context_apply_draw_state()` directly. Only a same-process
heavy-save A/B can decide its magnitude.

If p69 is useful, combine it with p68 in one post-acquire native boundary so the
game does not pay two x86/ARM crossings per DRAW:

```text
guest x86   acquire and establish the current GL context; prepare RT/depth
ARM p70     apply draw state; prepare/submit the final draw; post-draw cleanup
guest x86   context_release()
```

p70 starts again at correctness: source/final accounting, valid changing frame
witness and screenshot before any timing. It does not reopen entry 37 because
context acquisition/current ownership and release remain guest.

### 10.5 If p69 is black, close that boundary and profile inside it

A black or wrong p69 frame establishes the useful boundary that p66/p68 could
not:

```text
native context_apply_draw_state()   unsafe
native final arrays tail            safe
```

Do not iterate another guessed shared-state correction. Profile the guest
subfunctions inside `context_apply_draw_state()` and move only the heaviest
bounded subroot, for example shader constants, shader-resource loads,
shader-backend apply paths, or remaining buffer/texture helpers. Choose from the
profile rather than from source size.

The p69 closure already naturally reaches resource, texture and buffer loads.
That makes repair of entry 34's asymmetric A/B a lower priority: p69 can answer
the larger architectural question first. Entry 34 is not reclassified as
measured or closed.

### 10.6 Do not schedule a `WINE_NO_TRACE_MSGS` A/B

That proposed cheap experiment is already the documented build state, not a new
arm. The production recipe in `README.md` defines both
`WINE_NO_TRACE_MSGS` and `WINE_NO_DEBUG_MSGS`, and performance brief 29 records
the release WineD3D build with TRACE/debug removed and 30 `draw_primitive()`
hooks reduced to zero. Rebuilding a nominal p56-equivalent with the same define
would not create an independent hypothesis.

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
implemented   bounded display_lock history and symmetric p68b guest selector
measured      p68b symmetric A/B: balanced median +0.002 ms/frame; entry 38 is
              closed as a performance root by its pre-registered <=0.3 gate
not decided   whether context_apply_draw_state() is safe or useful in ARM when
              context acquisition/current ownership/release remain guest
not decided   whether p68 changes freeze frequency or caused this occurrence
not decided   the exact recursive call chain into display_lock
not decided   a production mutex fix; the debugger unlock is recovery only
production    FINALPLAY7 remains unchanged; p68 is closed and p69 is not
              production yet
```

## 12. Artifacts

```text
device/launch-p68-correctness.sh
binaries/box86-island46-p68-tail
binaries/wined3d_p68_draw_tail.dll
binaries/winewayland_p67_frame_witness.so
harness/p67_correctness_read.py
harness/island/full/island_mutable_state_audit.py   --root support

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

Production defaults were not changed by any p68/p68b artifact, the passive
ring, the A/B run or the debugger recovery. The p68b result closes entry 38 as a
performance root; it does not promote it.

# MGS2 RG353VS — native draw-state phase A measures a real negative delta (2026-08-21)

Handoff for research. Continues
`MGS2_NATIVE_DRAW_TAIL_AND_DIRECT_MUTEX_2026-08-20.md`, which rejected the
concrete ABI-invalid p69 boundary, admitted phases A/B/C, excluded shader phase
D, and closed p70's always-routed gameplay correctness gate. This brief begins
after that gate. It records the symmetric p70b measurement build, a marker-match
trap found and closed while building it, the clean timing configuration, the
acceptance rule as it stood before any data existed, and the first FPS result for
a native pre-shader phase.

```text
MEASURED          p70b entry 40 symmetric same-process A/B, one clean process,
                  owner-driven gameplay, 49 cycles. 27 cycles balanced within 2%
                  give paired median -0.626 ms/frame (routed minus guest, so
                  negative = ARM faster), mean +0.280, 20/27 favouring routed.
                  Ten balanced cycles on the 66,528-call plateau give -0.944
                  with sd 0.55 and 10/10 favouring routed; the high-call half
                  gives -1.081 with 14/16
CLASSIFIED        band 2 of the pre-registered table: the effect is real, phase A
                  is NOT promoted on its own from this data, and phase B proceeds
                  regardless of A. This is the first non-zero native renderer
                  delta since entry 23; entry 38 measured +0.002 and was closed
SYMMETRY          each arm is one guest call from the same site inside
                  context_apply_draw_state(). The routed arm calls the marked
                  island entry, which Box86 replaces with the ARM build; the
                  control arm calls the same transaction body directly. Neither
                  arm pays a RunFunctionFmt() re-entry, and FINALPLAY7's
                  production entries stay armed in both arms, so the number is
                  the incremental effect over production, not the cost of the
                  ARM body in isolation
MARKER TRAP       the first draft put the control arm in its own unmarked guest
                  twin, which the linker placed 22 bytes ahead of entry 0x28's
                  marker -- inside the 64-byte window Box86 scans forward from a
                  branch target. Canonical-RVA identity would have rejected it,
                  but that witness only becomes decisive once the guest module
                  base is known, so the layout was removed rather than trusted
INSTRUMENT        island_marker_check.py now reports every function starting
                  inside a marker's window, takes the run's armed list so a real
                  defect is not lost among three known unarmed ones, and asserts
                  that a named control-arm target has a marker-free window.
                  island_ab_read.py gained the plateau and high-call subsets the
                  acceptance rule required but the tool could not produce
NOT SAID          this run says nothing about the intermittent display_lock
                  freeze. The timing configuration deliberately disarmed the
                  recorder, and the process had already exited cleanly -- no
                  fault line, no research mount left, no OOM
PRODUCTION        unchanged. FINALPLAY7 and its launch defaults were not touched;
                  p70b is staged under separate research filenames only
```

## 1. What was reproduced before building anything

The phase choice rests on work recorded in the previous brief. All of it was
re-run on the current tree first, because a measurement that follows an
unverified selection is not worth making:

```text
ABI admission self-test    entry10 PASS  entry23 PASS  entry38 PASS  p69/D FAIL
phase matrix               A 548 fn / 1,096 rows / 0 hard  PASS
                           B 167 fn /   372 rows / 0 hard  PASS
                           C  21 fn /   171 rows / 0 hard  PASS
                           D 235 fn /   468 rows / 9 hard  FAIL
D's chain                  texture_stage_op 16/12 -> ffp_frag_settings 132/100
                           -> ffp_frag_desc 148/116
                           -> glsl_ffp_fragment_shader 164/132
offline attribution        A 2.878%  B 2.596%  C 0.514%  D 4.176% of all user
                           cycles, over the existing island41/p56 capture
```

`island_draw_phases.py` was updated so phase A's contiguous span follows the
transaction body after the p70b split; the closure it produces is unchanged
except for the thunk itself, which is why the audit reports 548 functions from
the phase span and 549 from the direct root.

## 2. What p70b changes in the guest

```text
static mgs2_draw_state_phase_a_body()      the whole contiguous transaction,
                                           unchanged from p70
mgs2_draw_state_phase_a_island()           marked entry, tail-calls the body;
                                           this is what Box86 replaces
context_apply_draw_state()                 selector: enabled/route/settled reads
                                           and one per-arm counter, then either
                                           the marked entry or the body
```

The control block is byte-identical in layout to the p68 draw-tail control, so
Box86 validates and publishes into it with one path; `mgs2_island_ab.c` no longer
hard-codes entry 38 but asks one `mgs2_ab_guest_capable()` predicate. When the
A/B is not armed, `enabled` stays zero and the guest always calls the marked
entry, which is exactly p70's behaviour.

Both compiled arms are the same thunk shape:

```text
100b8b40 <mgs2_draw_state_phase_a_island>  push/mov/mov, 8-byte marker NOP,
                                           pop, jmp mgs2_draw_state_phase_a_body
control arm                                call mgs2_draw_state_phase_a_body
```

## 3. The marker window is a property of the caller, not of the marked function

Box86 matches an island marker anywhere in the first 64 bytes from a branch
target. The identity rule added after the 2026-08-19 entry-22 defect makes the
canonical RVA the identity and the marker only a witness, which is what stops a
neighbouring function from claiming an id. But that check needs the guest module
base, so before it is established the marker is all there is. A control arm whose
own window contains a marker is therefore the wrong shape even when it is safe in
practice.

On the shipped p70b DLL the invariant holds outright:

```text
mgs2_draw_state_phase_a_body   @ 0x100b8350   no marker in +0..64 -- PASS
                                              nearest marker is 0x28 at +2038
mgs2_draw_state_phase_a_island @ 0x100b8b40   0x28 at +6, its own
```

`island_marker_check.py` now carries this as `--target SYMBOL`, and `--armed
LIST` makes severity follow the configuration. With this run's 19 armed ids the
whole check exits zero while still printing what it found:

```text
REPORTED   0x11 wined3d_ffp_frag_program_key_compare  57 bytes ahead, protected
           0x27 mgs2_batch_present                    59 bytes ahead, protected
           0x27 mgs2_batch_state                      27 bytes ahead, protected
           0x33 mgs2_island_ffp_target                54 bytes ahead, protected
IGNORED    0x14 one id in two functions; 0x0b at +66; 0x22 at +99 -- ids 20, 11
           and 34 are armed by no launcher; passing them to --armed exits 1
```

The four neighbours match the five a one-off scan found on the mounted p56 DLL on
2026-08-19; the difference is that the check is now part of the standing gate
instead of a memory of one investigation.

## 4. Static admission of the built pair

```text
entry 40 identity       marker +6, canonical RVA 0x000b8b40 (moved by the split);
                        regenerated from the shipped DLL and byte-compared
identity control        19 required armed ids, 0 missing, 0 beyond the window
marker control          exit 0 for the armed list, control-arm target clean
ABI closure phase A     548 functions / 27 TUs / 1,096 aggregate rows, 0 / 0 PASS
ABI direct root         549 functions, same rows, 0 / 0 PASS
indirect calls          53 routed, 0 unrouted PASS
class B                 1,616 native IDs, all registered by the ARM objects
ARM marker control      no x86 marker bytes in the ARM objects
mutable state           46 writable objects; the only new one is the ARM copy of
                        mgs2_phase_a_ab, which no native closure function
                        touches -- the selector is read and written by guest code
                        and by Box86 through the argument object, as
                        mgs2_draw_tail_ab was for p68b
libm compatibility      the eight wrapped libm symbols are GLIBC_2.4, identical
                        to the accepted p70 binary; built without diagnostics
patch series            both patches apply to the p70 tree with -F0, zero fuzz
```

## 5. The timing configuration, and the one instrument kept

Correctness was settled by p70's always-routed gameplay capture, so this run pays
for none of it:

```text
armed        FINALPLAY7 entries + 40, guest selector, ABBA/tick machinery,
             per-arm counters inside the guest control block
not armed    MGS2_DRAW_CORRECTNESS, MGS2_PHASE_A_CORRECTNESS, MGS2_FRAME_WITNESS,
             MGS2_REINFORCEMENT_CENSUS, MGS2_DISPLAY_LOCK_HISTORY, the p67
             witness presenter, any diagnostics build flag
kept         MGS2_GL_STATS=300 with WINEDEBUG -all,err+waylanddrv
```

`present stats` is one `winewayland.drv` ERR line per 300 displayed frames,
produced on the other side of the emulator and paid identically by both arms. It
is the only non-circular check of the A/B tick rate: comparing ticks against the
per-arm frame counts is circular, because the blocks are defined in ticks. A
short confirmation run without it was pre-agreed only for a result landing in
-0.25 to -0.4 ms/frame; the result did not land there.

## 6. Pre-registered before the run

```text
sign convention   delta = median(routed - guest); NEGATIVE means ARM is faster
primary result    median over cycles balanced to <=2% call count, both arms
                  non-zero; target 25-30 balanced cycles
secondary         sign count, plateau subset, high-call subset, per-arm means,
                  harness ticks against the MGS2_GL_STATS frame count
outliers          the all-cycles mean must NOT override the balanced median

delta <= -1.0 ms/f     production candidate; soak, then FPS; B separately
-1.0 < delta <= -0.3   effect real, A not promoted alone; B proceeds
|delta| < ~0.3         A closed as a performance root; move to B
delta > +0.3           A costs performance; closed; B remains its own hypothesis
```

No win rate is required: -1.5 ms/frame with the plateau agreeing in sign and the
variance explained by the scene is enough, and -0.15 ms/frame does not become
useful because the sign count looks good.

## 7. The result

```text
all cycles             n=49   median -0.759   mean -1.642   sd 10.79
balanced (<=2%)        n=27   median -0.626   mean +0.280   sd  6.29   PRIMARY
sign                          20 of 27 balanced cycles favour routed
plateau 66,528 calls   n=10   median -0.944   mean -0.915   sd  0.55   10/10
high-call >=66,528     n=16   median -1.081   mean -1.378   sd  2.64   14/16
arms                   routed 48.3 ms/f, guest 48.0 ms/f  ->  -0.12 fps
filter moved median    +0.133 ms/frame -- noise removed, answer unchanged
tick control           12,544 harness ticks against 12,300 GL_STATS frames
                       (102.0%, inside the one-block lag of 256)
```

27 balanced cycles meet the pre-registered target, so the run is complete on its
own terms, and -0.626 ms/frame is band 2: real, not promoted alone, B proceeds.

The homogeneous evidence is what makes the effect real rather than noise. Ten
balanced cycles at exactly 66,528 calls per arm give -0.944 ms/frame at sd 0.55
with all ten favouring routed. The session median is lower in magnitude because
the sample includes menus and light scenes where the entry is cold.

Reported against the result, not around it:

```text
balanced mean +0.280 against median -0.626, and per-arm means that make routed
look 0.12 fps slower, are the death and scene-transition outliers the rule
pre-committed to excluding: cycle 38 is +19.002 at 20% call imbalance, cycle 41
is +11.040 at 15%

cycle 49 is -9.762 ms/frame at 128,980 calls in a 114 ms/f scene, balanced to
0.07%. It hints the gain scales with draw-state load, but it is one cycle

a second, smaller plateau at 76,272 calls gives +2.832, -1.102, -1.245. This is
the reason promotion needs a longer plateau-dominated soak, not this median
```

## 8. How the run ended

The owner reported a freeze. The evidence is an exit, not a live deadlock:

```text
no box86 process remained; a stale wineserver survived and was left alone
/proc/mounts held no research bind mount, so launch-play.sh's EXIT trap ran
the log ends on a complete cycle-49 line
no SIGILL, SIGSEGV, island fault or unresolved-dispatch line anywhere in the log
dmesg shows no OOM kill of the game
frame times just before the end were 9.5 fps with 223 frames over 100 ms
```

That last line is what a player reads as a freeze. Because the timing
configuration disarmed `MGS2_DISPLAY_LOCK_HISTORY`, this run cannot say whether
the intermittent `display_lock` deadlock occurred; a freeze reproduction needs
the correctness configuration. The price was paid knowingly.

## 9. Phase B is not judged by phase A

The earlier version of the stop rule closed the whole pre-shader idea on a
phase-A median under 1 ms/frame. That does not follow. The guest arm of p70b is
FINALPLAY7, which already routes entries 10 and 23, and phase A's closure
contains those families -- so part of phase A's offline weight is cost production
has already removed, and routing phase A merely absorbs those closures into the
ARM phase:

```text
offline phase weight  !=  incremental opportunity over production
```

Phase B is dirty-state apply at an independent 2.596% of all user cycles, almost
phase A's weight, and its overlap with the existing production entries is a
different, unmeasured quantity. Phase C at 0.514% is not worth measuring
standalone and should be absorbed later into a fused ABI-safe root. Phase D stays
untouched until the FFP ABI question is decided.

One caution on the ranking that chose A: `island_phase_profile.py` attributes a
sample by closure membership, not by proving the call chain it came from, so
shared helpers can inflate a phase. The 2.878% was a ranking signal and an upper
bound, and the measured -0.626 to -1.081 ms/frame is the first number that is not.

## 10. What is and is not decided

```text
measured      p70b phase A: balanced median -0.626 ms/frame over 27 cycles,
              20/27 favouring routed; 66,528-call plateau -0.944 (sd 0.55,
              10/10); high-call half -1.081 (14/16). Band 2 by the rule
decided       the native pre-shader boundary is not dead: phase A produces a
              real, consistently signed negative delta under a symmetric A/B
              where both arms are one guest call and production stays armed
decided       phase A alone is not promoted from this session, and phase B is
              measured regardless of A's result
decided       a control arm must not sit inside a marker's 64-byte window, and
              the check is now part of the standing pre-device gate
implemented   p70b: wine patch 68, box86 patch 14, identity at +6 / 0x000b8b40,
              1,616 class-B ids, ABI 0/0, indirect calls 53/0
implemented   island_marker_check.py --target/--armed; island_ab_read.py plateau
              and high-call subsets
not decided   whether phase A can reach the >=1.0 ms/frame promotion band; the
              66,528 plateau says -0.944 but the 76,272 plateau disagrees in
              sign on 1 of 3 cycles. A longer plateau-dominated soak would settle
              it and is optional, since B proceeds either way
not decided   any phase-B effect; nothing about phase B has been built or run
not decided   whether this run's ending was the display_lock freeze; the
              recorder was disarmed and the process had exited cleanly
not decided   whether the gain scales with draw-state load, as cycle 49 hints
production    unchanged: FINALPLAY7, its launch defaults and its byte-checked
              files. p70b exists only as separate research filenames
```

## 11. Artifacts

```text
wine-patches/68-p70b-phase-a-symmetric-ab.patch
  cddb5a485b394ff45a6c56498daabc416c6cfcb0129543c4cd5279d58f59f425
box86-patches/14-p70b-phase-a-symmetric-ab.patch
  40f3dd0ce6c43464e62a977c942dda33d0a7e32b4f8c8dc7e2df15084c513be8
binaries/box86-island50-p70b-ab
  3aeb7c733dd896694bbf7ee2a581807a32991ff44907a3fa9e7e5c3df3051541
binaries/wined3d_p70b_phase_a_ab.dll
  23fe29aca711c8e9a0ace560cd4ef681fa2c195c85319e9100f02480a3ca76a1
device/launch-p70b-ab.sh
  fe8fc1b9020300f32dee09b419b79e8c8bb2c95f4d7ebee113747fc5a56c97ae
  timing configuration: selector + production entries + frame tick only
logs/rg353vs/p70b-ab-20260821/p70b-ab-20260821.log
  b11fa7426247677bc516b5931baa54adf2c58f2d99663cbfdf3f1591b4f757e4

harness/island_ab_read.py                       plateau + high-call subsets
  7a40d560db42996a2fa1e1e5bc1ae9f0ab752ac07899c286a560d2c5627056dc
harness/island/full/island_marker_check.py      --target / --armed severity
  545397b2a2a6f5ce19fe7c73912e01c5b89bd08d6e6476c99c4f0d313180dab3
harness/island/full/island_draw_phases.py       phase A follows the body
  d37750619fa55f9a14dc917a8249ce1ac726764823b639eebaede258ecb919aa
harness/island/full/island_abi_closure_audit.py unchanged, re-run this session
  5a05a92389fae331db2173f8b0bb04d98605d91daed40fe81c14e83b3d8fec04
harness/island_phase_profile.py                 unchanged, re-run this session
  4a51c72c1984d0e845cac51c047a63363d02a3867fb694794bc27644f64a4d24
```

Source-of-record edits live in the shared trees:

```text
../recovered-session/wine-11.0/dlls/wined3d/context_gl.c
../box86-src/src/mgs2_island_bridges.c
../box86-src/src/mgs2_island_ab.c
```

Device staging was verified byte-for-byte after upload and `/storage` had 561 MB
free at that point -- enough for this log, not for another research pair.

## 12. Next step

```text
1. Build phase B: the whole dirty-state transaction including the bitmap clear,
   as one contiguous span, entry 41. Its admission is already PASS (167
   functions, 372 rows, 0 hard), so only the identity, class-B and indirect-call
   audits are new work.
2. One bounded correctness run in the correctness configuration -- which also
   re-arms the display-lock recorder that this timing run gave up.
3. One symmetric A/B with the same pre-registered rule and the same reader.
4. Optional and independent: a longer plateau-dominated soak of p70b, if the
   question of promoting phase A on its own is worth settling before B.
```

## 13. Clang-MS makes the layout right, and the boundary still renders black

Two device runs after the phase-A measurement above, in the order a compiler
change deserves: first the proven phase A on the new toolchain, then the boundary
the toolchain was for.

### 13.1 STEP 0 -- the clang-MS execution path is admitted

The island was rebuilt in full by `clang-18 --target=arm-linux-gnueabihf
-mms-bitfields`; nothing else changed, and the guest DLL was the unchanged p70b
build with the A/B selector disabled, so entry 40 is always routed exactly as in
p70. Static gates first:

```text
layout witness compiled INTO the island   texture_stage_op 16, ffp_frag_settings
                                          132, ffp_frag_desc 148, context 1020,
                                          state 7276 -- the guest's own sizes
compilers named by .comment               one: clang version 18.1.8
Class-B reachable from phase A            352, all in the clang object set,
                                          0 other / 0 duplicate / 0 unresolved
Class-B total                             1,549 ids, not 1,616: clang inlines 67
                                          functions GCC kept as symbols. None is
                                          reachable from phase A or from
                                          context_apply_draw_state()
must-match shared globals                 wined3d_context_tls_idx and
                                          mgs2_batch_ptr identical to the
                                          reviewed GCC island (.bss, 4 bytes)
link                                      bcmp GLIBC_2.4, exp2f GLIBC_2.27, zero
                                          compiler-rt symbols, the eight libm
                                          wraps still GLIBC_2.4, VFP/FP_arch
                                          identical to the accepted build
```

Device result, one clean process, title screen:

```text
phase-A calls / guest fallback   328,564 / 0
final GL submissions             328,564, all arrays -- source == final exactly
frame witness                    1,881 frames; retained 64 / 64 unique
                                 min_lit 254/256, min_changed 162/255
faults / unresolved dispatch     0 / 0
independent screenshot           the real title screen, 286 KB
```

**PASS.** A compiler that assigns MSVC field offsets on ARM Linux runs this
island correctly. That is the result the rest of this section rests on.

### 13.2 A latent trap that had nothing to do with layout

Before p71 could be built, the indirect-call audit on the entry-39 closure
reported something the p69 build never had checked against this boundary:

```text
UNROUTED indirect calls: 4     shader.c shader_generate_code()
  fe->shader_read_header      fe->shader_is_end      fe->shader_read_instruction
  device->shader_backend->shader_handle_instruction
```

Unrouted means native ARM would branch to a guest x86 function pointer. The path
is reached whenever the FFP shader cache misses inside the native root, so p69
carried the same mine and simply never stepped on it. All four now dispatch
through `mgs2_island_dispatch()` (new site `MGS2_P50_SHADER_FRONTEND`, sites
36 -> 37), and the audit reports 0 unrouted / 64 routed.

### 13.3 p71: ABI-correct, routed, and still an all-black frame

Wine patch: `draw_primitive()` calls the entry-39 island wrapper again, so the
whole of `context_apply_draw_state()` is native. Guest x86 keeps
`context_acquire()`, current-context ownership, render-target/depth preparation,
the final draw, barriers and `context_release()`, exactly as p69 did.

Static admission all passed: ABI closure 731 functions / 1,379 rows / 0 hard with
both controls PASS, compiler-homogeneous 417 reachable Class-B targets with 0
other/duplicate/unresolved, 0 unrouted indirect calls, identity at entry 39
canonical, class B 1,547 ids all registered.

```text
p71 calls / FALSE / guest fallback   702,038 / 0 / 0
final GL submissions                 702,037, all arrays
frame witness                        3,941 frames; retained 64 with ONE unique
                                     hash; min_lit 0/256, min_changed 0/255
independent screenshot               972 bytes, uniform black -- byte-identical
                                     hash to p69-live.png (441da723...)
faults / unresolved dispatch         0 / 0
presented                            900 frames at 57.7-60.2 fps, readback
                                     0.83 ms/f: the cost profile of an empty frame
```

The bounded shader witness is what makes this run worth more than p69's:

```text
samples                    171, GL resolved
current program            0 at EVERY sample
program pipeline           0
draw framebuffer           8
glGetError                 0x502 GL_INVALID_OPERATION at EVERY sample
zero-program samples       171 / 171
gl-error samples           171 / 171
```

So the native root advances work, submits draws and never leaves a program
bound: every sampled draw is invalid, which is why 3,941 frames contain one
unique all-black hash. This is no longer a 32-byte field shift -- that defect is
gone, proved by the witness compiled into the island and by 1,379 audited
aggregate rows with zero hard failures. Something else in draw-state application
does not survive being moved wholesale, and it is in the shader/program part:
phase A alone, on the same island, renders the correct title screen.

**Decision, per the rule fixed before the run: the whole
`context_apply_draw_state()` boundary is closed.** No shared-state guessing loop
follows. It has now failed twice, and the second failure removes its only
remaining excuse; what it produced instead is a precise mechanism -- program 0
and GL_INVALID_OPERATION on every sample -- for whoever revisits it with a
different design.

```text
closed        native whole-draw-state boundary (entry 37, 39 and p71 alike)
open          fused ABI-safe A+B+C, which excludes the shader phase entirely
next          phase B as entry 41: the whole dirty-state transaction including
              the bitmap clear, admitted at 167 functions / 372 rows / 0 hard
```

Entry 37 stays where the previous brief put it: its rejection lost its ABI
excuse, but p71 does not rehabilitate it -- p71 never moved ownership/context
work, and p71 itself is now closed.

## 14. The fused A+B+C root renders, and it is not zero

p71 closed the whole-draw-state boundary; this is the other half of that decision
being taken up, not a smaller retry of it. The shader phase stays guest, which
matters for one measured reason: the nine separable-program entry pointers the
island duplicates are referenced by phase D's program-binding path and by nothing
in B or C.

```text
separable-pointer statics referenced, by phase (mutable-state audit)
    phase A   46 writable objects, 1 of the nine (shader_glsl_disable)
    phase B   15 writable objects, 0 of the nine
    phase C   10 writable objects, 0 of the nine
    phase D   35 writable objects, ALL NINE
```

### 14.1 Entry 41: static admission

```text
identity              marker 0x29 at its canonical RVA; 19 armed ids, 0 missing
ABI closure clang-MS  557 functions / 27 TUs / 1,130 rows; 0 hard failures PASS
compiler-homogeneous  357 reachable Class-B targets, 0 other / 0 duplicate /
                      0 unresolved; one compiler (clang 18.1.8); layout witness
                      16/132/148 with context 1020 and state 7276
indirect calls        0 unrouted / 53 routed
marker control        exit 0 for the armed list; the fused body -- the control
                      arm's target -- has no marker in its own 64-byte window
class B               1,549 ids, all registered by the objects
```

### 14.2 Correctness: PASS

One clean process, entry 41 matched canonically at 0x7a43d510:

```text
native applications / guest fallback   79,777 / 0
final GL submissions                   79,777, all arrays -- source == final
frame witness                          889 frames; retained 64 / 64 unique
                                       min_lit 256/256, min_changed 254/255
faults / unresolved dispatch           0 / 0
independent screenshot                 286 KB of real scene
```

### 14.3 The A/B, and why its headline number is not the pre-registered one

The pre-registered primary metric could not be evaluated. It needs cycles whose
two arms did the same amount of work, and this session's scene drifted faster
than a 64-frame block: 7 of 28 cycles balanced within 2%, with sd 12.47 among
those seven. Their median is -0.005 ms/frame, which is not evidence of zero --
it is an empty sample.

```text
pre-registered primary   balanced n=7   median -0.005  sd 12.47   NOT USABLE
all cycles               n=28           median -1.450  sd 20.86
```

So the run was reduced a second way, and this estimator is post-hoc: divide each
arm's frame time by that arm's applications per frame, so scene weight cancels
rather than disqualifying the cycle.

```text
routed cheaper per application   23 of 28 cycles
exact two-sided sign test        p = 0.0009
effect at 1,109 applications/f   median -4.82 ms/frame
95% bootstrap CI                 [-7.86, -2.58] ms/frame
bootstrap medians below -1 ms    100%
```

What each of those supports, stated separately because they are not equally
strong:

```text
DIRECTION   established. The sign test uses only "was the routed arm cheaper per
            application in this cycle", which no normalisation choice can flip.
            23 of 28 at p=0.0009 is not scene drift
MAGNITUDE   estimated, not measured. The estimator assumes frame time scales with
            application count -- reasonable for a draw-bound renderer, and the
            confidence interval covers sampling noise only, NOT that assumption.
            It was also chosen after seeing that the primary metric was unusable
```

`harness/island_ab_read.py` now computes all of it, so the claim is reproducible
from the log rather than from this text.

### 14.4 What follows

```text
promoted to candidate   p72c: fused A+B+C always routed, no selector, no census,
                        no diagnostics, production presenter and entry list.
                        Watched by ordinary play through `present stats`, not by
                        another measurement session
not promoted to default FINALPLAY7 stays the default until candidate play backs
                        the estimate up
open                    the magnitude verdict. One short A/B with 32-frame blocks
                        would close it: the cycle drops from 20-40 s to ~10 s, so
                        far less scene drift lands inside a block. The block
                        length is a compile-time constant today
open                    the GL-work census. Its record is duplicated by the
                        island exactly like the separable pointers, which is why
                        the p72 run read zero state-callbacks: the native phases
                        increment the island's copy. The record is now exported
                        from the island so a future reader can sum both copies
```

The first census numbers, guest-side only and on a light scene, are still worth
recording because they set the scale of the driver-side question:

```text
draw-state applies   89.7 /frame        uniform loads     89.7 /frame
ext GL calls        112.2 /frame        program selects     5.8 /frame
FBO checks            4.4 /frame        ext GL per draw     1.3
```

One uniform load per application, and roughly one ext GL call per draw, on a
title screen. The heavy-scene numbers -- where 42.5% of user cycles sit inside
libmali -- remain unmeasured.

### 14.5 Artifacts of the fused root

```text
wine source        one fused span in context_gl.c: mgs2_draw_state_abc_body()
                   with the marked mgs2_draw_state_abc_island() entry; the p72b
                   selector sits behind MGS2_FUSED_ABC_AB and the census behind
                   MGS2_GL_CENSUS, so the candidate build carries neither
box86              entry 41 wrapper with the p72 correctness record, and
                   mgs2_ab_guest_capable() extended to entry 41
new dispatch site  MGS2_P50_SHADER_FRONTEND, sites 36 -> 37: shader_generate_code()
                   called the shader frontend vtable unrouted at four sites

binaries/box86-island53-p72-fused-abc      3d3d470de1725f6101bfac83802e3374cc1fc03edc25264357f51880c3fd4ecf
binaries/wined3d_p72_fused_abc_census.dll  4bec8319464293faf85e46e6a3dcc972d4ab42320c88651b784b3dd3b755aba6
binaries/box86-island54-p72b-ab            11a5b18a91d758c16d50c69cc6bcb925a05db2f7fc34d51d97d1782bf2e393ef
binaries/wined3d_p72b_fused_abc_ab.dll     e998e74ba0fbb910d1bb825ae7ae862b38330bc4d8ce31fce62c97534905d477
binaries/box86-island55-p72c-candidate     66cdba2226c21b89d58b2c46da087d53c1ccf93250777f7d151480be3ea4f1d2
binaries/wined3d_p72c_fused_abc.dll        04fcb46d5d8ad503576042da061611067c5b9c3eed9185a0f6ca74a8f48e9ddb
device/launch-p72-fused-census.sh          961d71319eae657b2e151c61c3aaf575c5385913a519eba28d69d476863acaf5
device/launch-p72b-ab.sh                   e7a93576879e0bc929b1dcd670136b66a999d883e591d7a38d51b0bc22c0f0b1
device/launch-p72c-candidate.sh            1a25d4547decb1b609497363486beaa2224caaf31a8c382bad90db12c3d4c7f0
harness/p72_correctness_read.py            correctness + GL census, --census-rva
harness/island_ab_read.py                  now also work-normalised + sign test
                                           + bootstrap CI over every cycle

logs/rg353vs/p72-fused-20260822/p72b-ab-20260822.log      the 28-cycle A/B
logs/rg353vs/p72-fused-20260822/p72-fused-census-20260822.log
logs/rg353vs/p72-fused-20260822/p72-fused.png             correct scene, 286 KB
logs/rg353vs/p71-clangms-20260821/p71-correctness.png     the closed boundary's
                                                          black frame, 972 bytes
```

Production defaults were not changed at any point in this session. FINALPLAY7
remains the default; p72c exists as a separate launcher and separate filenames.

### 14.6 Candidate soak: stable, and fps-blind by construction

One ordinary play session on `launch-p72c-candidate.sh`, production presenter and
production entry list plus entry 41, no A/B, no census, no diagnostics:

```text
native applications routed   1,823,100, still advancing when read
guest fallbacks              0
faults / SIGILL / SIGSEGV    0
present windows              13 (3,900 displayed frames)
fps  min 7.7 | q1 18.5 | median 38.5 | q3 46.1 | max 60.2
readback                     median 6.40 ms/f
frames over 50 ms per window median 1, worst 300 (one sustained heavy stretch)
SoC temperature at the read  75.6 C
```

The routing witness matters here: without `MGS2_P72_CORRECTNESS` armed, nothing
in a non-diagnostic run proves the route is live -- Box86 logs that entry 41 was
armed, the "matched" line exists only in the diagnostics build, and a marker that
failed to match would leave the guest body running with an equally correct
picture. 1,823,100 applications with zero fallbacks is that proof.

What this session does NOT do is measure the effect. Its fps envelope -- 60 at
menus, 18-46 in rooms, three windows below 20 with a median of 8.7 -- sits inside
the production envelope recorded in perf brief 35 (60 / 22-38 / 6.5-17). It has
to: at 115 ms/frame a 3 ms effect is 2.6%, far under the scene-to-scene and
thermal spread of session-level windows. Only the within-process A/B can resolve
it, which is why that instrument exists.

```text
established by the soak    correctness holds over 1.8M applications; the route is
                           live; no fault, no fallback, no thermal anomaly
still open                 the magnitude verdict. One A/B with 32-frame blocks
                           would close it in 5-7 minutes of ordinary play, since
                           the cycle drops from 20-40 s to ~10 s and far less
                           scene drift lands inside a block
```

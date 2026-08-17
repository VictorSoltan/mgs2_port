# MGS2 RG353VS — the island is worth 9 ms/frame, and it is in production (2026-08-16, third)

Handoff for research. Continues `MGS2_ISLAND_ARMED_2026-08-16b.md`, which closed
on a null: eight separate playthroughs could not resolve whether routing
`wined3d_buffer_load` natively helped. Research replied with a prioritised plan;
this is what following it produced. Written to be read on its own; long-form
record is section 29 of `MGS2_REINFORCEMENT_FRAME_BUDGET_2026-08-14.md`.

```text
measured      routing wined3d_buffer_load natively saves 8.87 ms/frame, -12.8%,
              30 of 30 paired cycles, se 0.44 ms/f  ->  about +2.1 fps
promoted      box86-island29 + wined3d_p55_glinfo.dll, entry 10 included,
              verified byte-wise through the real launcher, 0 faults
removed       the class-B fixpoint, and with it the whole stale-address failure
found         110 of 1721 class-B entries were unsound, 56 of them compiler
              clones that cannot be mapped across compilers at all
follow-up     `MGS2_ISLAND_BATCH_STATE_MEASURED_2026-08-16d.md`: entry 4 is a
              measured +0.9 fps win after sharing its guest batch state;
              it is now production in FINALPLAY6 as island31 + p56
```

The headline correction: **the previous null was an instrument failure, not a
result.** The effect was always there. Eight playthroughs could not see 9 ms
because the scene moved between runs by more than that.

## 1. Same-process ABBA, which was research's main point

The instruction was to stop looking for a better save and instead switch the
entry inside one live process, on displayed-frame boundaries, ABBA, with both
arms passing through the same gate. Built as `MGS2_ISLAND_AB=<entry id>`.

Both arms enter the same bridge and read the same argument slots off the guest
stack; only the last step differs — the native ARM function, or the guest's own
body under the emulator. So the gate's own cost is in both arms and cancels.

Reaching the guest body is safe, and this was checked rather than assumed:
`DynaCall` sets `R_EIP` directly, and `hasAlternate()` consults only the
alternates hash map, which marker-matched island entries were never added to. So
calling the guest address does not re-enter the island bridge.

### 1.1 The frame tick is glReadPixels, not eglSwapBuffers

Worth knowing before anyone reuses the harness. **This port does not present by
swapping.** winewayland's `wayland_drawable_swap()` reads the finished frame back
with `glReadPixels` into a `wl_shm` buffer — which is why the launcher's own line
has always reported `readback 7.2 ms/f`. Ticking on `eglSwapBuffers` produced
**zero ticks across a whole 480 s run**, and that is what pointed here.

### 1.2 The result

51 cycles; 37 in-game; 30 with the two arms' `buffer_load` call counts within 2%
of each other:

```text
routed      60.6 ms/f
unrouted    69.4 ms/f
difference  median -8.87   mean -9.38   sd 2.39   -12.8%
range       -21.65 .. -7.69, and 30 of 30 cycles favour routed
```

Standard error 2.39/sqrt(30) = **0.44 ms/frame**, against the stated requirement
of paired sigma below about 1 ms. In frame-rate terms 14.4 -> 16.5 fps.

### 1.3 The call count is the covariate that makes it readable

Recording per-block aggregates, as specified, turned out to matter more than
expected. Cycles where the two arms' call counts diverge swing wildly in both
directions — one showed -67 ms/f during loading, another -6.5 ms/f with 34% more
calls in the unrouted arm. Filtering to balanced cycles collapses the spread
from sd 8.67 to 2.39 **without moving the median** (-8.83 -> -8.87). So the
filter removes noise rather than selecting a favourable subset, and the
correlation between call imbalance and the difference is weak (r = -0.20).

### 1.4 A check of ours that proved nothing

The first version of the harness reported a "tick rate check": that frames
counted per arm equalled `2 * (BLOCK - SETTLE)`. **That is circular** — the
blocks are defined in ticks, so it holds no matter what the tick counts. Removed
rather than left to give false assurance.

The real check is external and passed: over 51 cycles the mean interval came to
51.0 ms against 51.1 ms from the launcher's `MGS2_GL_STATS` counter, produced by
different code on the other side of the emulator. The cumulative tick count is
now printed so the comparison can be repeated from any log.

This is the **third** time in this project a control has been built out of the
thing it was meant to test — after the guest-thread-id diagnostic key and the
witness that validated only the guest half of a mapping. Adopted as a standing
rule: *a control must not be computed through the mechanism it is controlling.*

## 2. The class-B fixpoint is gone, not made safer

Research's second point: the previous fix treated a symptom and left a
self-referential design. Agreed and done.

The table now maps **guest RVA -> symbol ID**; the ARM addresses come from the
linker. Each island translation unit gets a generated fragment appended that
takes the address of every mappable function it defines and drops an
`(id, address)` pair into one section; the runtime walks it once. 916 of the
mapped names are `static`, which is exactly why the fragment must live inside
the TU — a central file cannot name them.

`fixpoint_class_b.sh` is deleted. The build does two passes and they are **not**
a loop: pass 1 exists only so the generator can read which names each TU
defines, and appending a registry changes no name, so pass 2 cannot invalidate
pass 1. It terminates by construction.

Verified statically before any device run — RVA `0x0017aaf0` -> id 757 ->
`0x62b51e45`, exactly where `readelf` puts
`wined3d_buffer_gl_prepare_location`; zero unregistered IDs — then live:

```text
MGS2 class-B: 1614 native IDs registered by the linker
MGS2 dispatch: site 0 0x7b8eaaf0 -> B wined3d -> 0x62b51e45
```

### 2.1 What rebuilding on names exposed

Of 1721 matched names, **110 must not be mapped at all**, and they had all been
in the shipped table:

```text
  56  compiler clones      .isra.N  .part.N  .constprop.N
   3  several island TUs   wine_dbg_vprintf is defined in 31 of the 32
  51  several guest addrs  the same statics, on the PE side
1614  MAPPED
```

The clones are the dangerous class and had not been identified before. They are
not the source-level function: GCC invents them per translation with signatures
it chooses — `.isra` replaces aggregate parameters with scalars, `.constprop`
deletes parameters it propagated, `.part` splits a body at a compiler-chosen
point. i386 mingw-GCC and armhf-GCC make those choices independently, so
`foo.isra.0` on the two sides are unrelated functions sharing a mangled name.
One of them, `wined3d_from_cs.part.0`, sits on a hot path.

The generator now rejects all three categories and says how many of each.

## 3. Production

`box86-island29` + `wined3d_p55_glinfo.dll`, entries
`0,1,2,3,5,6,9,10,14,18,19,22,28,29,32,33`. Verified through the real
`MGS2-Substance.sh`, mounts compared byte-wise: 15 entries matched, entry 10
among them, resolver armed on 1614 IDs, **0 faults**, GPU governor `performance`.

Two things checked rather than assumed:

* **p55 keeps the CS deadlock census.** It is p52 plus 8538 bytes. Losing it
  would silently have ended the freeze investigation that is still waiting on a
  natural occurrence.
* **entry 10 alongside the other 15** had never been run together before
  promotion. It was, on the combat save, before the launcher changed.

`MGS2_ISLAND_AB` is now **cleared unconditionally** by the play launcher, and a
measurement run opts in under a different name, `MGS2_ISLAND_AB_MEASURE`
(`device/launch-island-ab.sh`). Setting the harness variable halves the benefit
by construction, since half the frames run unrouted, and it is the only variable
here whose accidental presence costs performance instead of causing a visible
failure -- so the name that can leak from a shell is not the name that arms it.

Entry 10 is the only entry in this launcher carried by a measurement. The other
15 remain promoted on the owner's judgement, and the launcher says so.

## 4. Not finished

`island_gl_reach.py` — the static required-GL-slot analysis research asked for —
is written and runs, but never produced output. It was stopped after ~45 minutes
and is left as an unfinished research tool, on the owner's instruction not to
delay the release for it (objdump over a 27 MB binary plus preprocessing 32
sources; one O(n^2) in the brace scanner was already removed and did not make it
finish). **The fail-closed preflight is NOT a production guard.**

So the current basis for believing the 260 unresolved GL slots do not matter is
still empirical — the armed entries have not reached one across every run to
date — exactly the crash-driven evidence research objected to. The design is
unchanged from your description: required = union over the closure of every
`gl_ops` member referenced, and `required & ~resolved != 0` refuses to arm.
Slot indices come from expanding the same four macro lists the struct is built
from, so the index-to-name mapping cannot drift; that part is verified (3114
slots, matching `sizeof(gl_ops)/sizeof(void*)` exactly as the runtime reports).

## 5. What would help most from research now

1. **Whether to widen the cut, and in what order.** Entry 10's closure carries
   the 4821.9 calls/frame dispatch and is worth 9 ms. The obvious next roots are
   the other three frame-carrying functions. The harness can now measure each in
   about 20 minutes, so the question is which order maximises information rather
   than whether it is measurable.
2. **A sanity check on 60.6 vs 69.4 ms.** That is a 12.8% frame-time saving from
   one routed function. It is consistent across 30 cycles and survives the
   call-count filter, but it is larger than section 14 predicted for this cut
   alone, and we would rather have it questioned now than build on it.
3. **Whether the ID scheme should extend to class C.** Class C currently resolves
   by name at runtime through `dlsym`/`eglGetProcAddress`. That has no staleness
   problem, but it is a different mechanism from class B, and one scheme would be
   easier to reason about than two.

## 6. Artefacts

```text
docs/briefs/MGS2_ISLAND_MEASURED_2026-08-16c.md   this document
docs/briefs/MGS2_REINFORCEMENT_FRAME_BUDGET_2026-08-14.md   section 29 is new
box86-patches/07-native-island.patch              island, ID registry, A/B harness
wine-patches/53-island-gl-by-name.patch           name-keyed GL slots
device/launch-play.sh                             production, with the numbers
harness/island/full/gen_class_b_table.py          ID generator, three rejections
harness/island/full/build_island_objects.sh       two passes, not a loop
harness/island/full/island_gl_reach.py            conservative GL-slot gate;
                                                   not a writable-global proof
```

Deleted: `harness/island/full/fixpoint_class_b.sh` — the design it worked around
no longer exists.

How to reproduce the measurement:

```sh
MGS2_ISLAND_AB_MEASURE=10 MGS2_BOX86_BIN=box86-island29 \
MGS2_WINED3D_DLL=wined3d_p55_glinfo.dll ./launch-play.sh
# then read the "MGS2 A/B cycle" lines; filter to cycles whose two call counts
# agree within 2%, and take the median of routed-unrouted.
```

Class-C generation must use the `opengl32.dll` **mounted on the device**. The
reference wineprefix copy shares an ImageBase and has different RVAs, which is
what made an earlier failure silent.

## 6.5 After the release: an input stall, and one defect of ours

Reported during play a few hours after promotion: the character walked left on
its own, controls stopped responding, sound was gone. Full record in section 30
of the frame-budget brief; the parts research may care about:

**It is not the CS freeze.** The census armed in production answered
immediately and correctly -- queues advancing, CS thread not blocked. First real
use of that instrument, and it gave a clean negative rather than a shrug.

**It is a page-fault storm, confined to one thread.**

```text
wine_dinput_wor   ~1100 page-faults/s     perf: 22.9% rb_get,
wined3d_cs        0                       17.7% FindDynablockFromNativeAddress,
main thread       0                        5.7% getProtection
```

Wine's DirectInput worker writes to a page that also holds translated code;
box86 write-protects such pages to detect self-modifying code, so every write
faults and re-translates. The thread stays alive and makes almost no progress,
which is why rendering continued and only input died.

**Box86's own mitigation cannot engage.** `hotpage`/`hotpage_cnt` are single
globals; `isInHotPage()` decrements the shared 64-call budget on every call from
any thread, and the address is overwritten by the next unrelated fault. With
four active threads it drains instantly. The mechanism assumes a single-threaded
workload. Fix direction: thread-local, decrement only on an address match. **Not
done** -- core surgery, and the owner had frozen the release.

**One defect of ours, now shipped as `box86-island29`.** The island's marker
scan in `getAlternate()` was ungated, unlike the two blocks beside it: a
readability probe plus up to 65 `memcmp` calls ran on every branch target the
dynarec translated, on every thread, *even with the island switched off*. Gated,
plus a first-byte reject. It is 4.8% of a pathological profile against the 46%
the fault storm costs, so it does **not** fix the stall.

The gate has an ordering hazard that was checked on the device rather than
reasoned about: if `getAlternate()` ran before the bridges registered, no entry
would match and the island would silently give back the whole 8.87 ms. 15
entries matched, 0 faults.

Two tools added, both reading kernel state instead of inferring from event
history: `harness/keystate.py` (EVIOCGKEY) and `harness/axisstate.py`
(EVIOCGABS). Their absence is why the first several hypotheses were guesses --
including a stuck-Home-button story built on a single transient sample, which
the owner correctly rejected.

## 7. Corrections this document makes

* the §28 null is withdrawn. Routing `wined3d_buffer_load` is worth about
  9 ms/frame; the earlier measurement could not see it.
* the "tick rate check" in the first A/B build was circular and is removed
  (section 1.4).
* the earlier statement that the island fix was held out of production is
  superseded: it shipped as `box86-island29`. Holding it back was the wrong
  call -- the freeze was about new optimisation, not about a defect we had
  introduced ourselves.
* mid-analysis we read `16.670 ms/f` in an early cycle, compared it to the ~51 ms
  in-game frame time, and called the instrument broken by a factor of 3.6. It was
  not: those cycles are the title screen at the 60 Hz cap, where 16.7 ms is
  correct. The external check settled it.

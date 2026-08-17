# MGS2 RG353VS — the routed island runs the game, and measures nothing (2026-08-16, later)

> **SUPERSEDED IN PART.** `fixpoint_class_b.sh`, described below as the fix for
> the stale class-B table, no longer exists. The design that needed it was
> replaced: the table now maps guest RVA to a symbol ID and the linker supplies
> the ARM addresses, so there is nothing self-referential left to iterate to a
> fixpoint. See `MGS2_ISLAND_MEASURED_2026-08-16c.md` section 2. Everything else
> here still stands; this document is kept as the record of how the stale-table
> failure was found.

Handoff for research. Continues `MGS2_ISLAND_PRODUCTION_2026-08-16.md`, which
closed at "island promoted on judgement, not on a number". Written to be read on
its own; long-form record is sections 26-28 of
`MGS2_REINFORCEMENT_FRAME_BUDGET_2026-08-14.md`.

Short version:

```text
achieved      wined3d_buffer_load routed to native ARM, reaches the combat save,
              plays with 0 faults across eight 180 s in-game windows
measured      no frame-rate effect: routed 16.45-18.90 fps, unrouted 16.70-18.80,
              n=8 arms, ranges overlap
blocked by    the measurement route itself -- within-arm spread 2.4 fps against a
              predicted prize of 1.1-2.3 fps
fixed         three silent defects, two of them the same class of error
open          the Box86 sync-arena freeze, still armed and waiting
```

## 1. Three defects, and the shape they share

All three were silent. None produced a diagnostic pointing at itself, and two
are the same mistake made twice in different places.

### 1.1 The class-B table was stale by construction

The table maps a guest WineD3D function pointer to the island's own ARM
function. It is **generated from the binary it is then compiled into**, so any
source edit shifts every ARM address and the table shipped in that build is
stale. Nothing enforced regeneration to a fixpoint.

The failure mode is the dangerous one. A stale entry is not a wild pointer — it
lands on a real, wrong function:

```text
MGS2 dispatch: site 0 0x7b8eaaf0 -> B wined3d -> 0x62b450b5
SIGSEGV @0x62b450c0 ... for accessing 0x1c7c
```

`0x62b450b5` is odd, so Thumb; function start `0x62b450b4`; crash 12 bytes in.
In the binary that actually ran, `wined3d_buffer_gl_prepare_location` was at
`0x62b45325`. `0x62b450b5` was 16 bytes inside `wined3d_buffer_destroy_object`.
The island called the destructor with `prepare_location`'s arguments — which is
why two consecutive builds crashed at different addresses.

Two guards now:

* `harness/island/full/fixpoint_class_b.sh` — regenerate and rebuild until two
  successive tables agree. I predicted convergence in one iteration, reasoning
  that a fixed-size table cannot move `.text`. Measured: three. The loop caught
  my own wrong reasoning; that is the argument for having it rather than a
  single regenerate-and-build.
* `mgs2_class_b_native_matches()` — compares the table's ARM address for each
  witness against `mgs2_island_entries[].impl`, which Box86 holds independently,
  and refuses to arm on disagreement. Live: `native side verified, 4 witness(es)
  agree with this binary`.

**The pre-existing witness check could never have caught this.** It validates
the guest module base only; the native half is the half that rots. Worth
carrying as a general point: a build-pairing check that only validates one side
of a mapping is not a build-pairing check.

### 1.2 Class C was keyed on addresses, which cannot work

With class B correct, the save loaded and the game played, then died reading
address 0:

```text
MGS2 gl_ops translated: 3114 slots, 2621 null, 3 resolved, 490 UNRESOLVED
```

Unresolved slots were written back as NULL, so the first genuine `GL_EXTCALL`
through one dereferenced it — in-game, minutes after load, far from the cause.
Two independent faults produced that 3:

* the RVA table came from the reference wineprefix's `opengl32.dll`, not the one
  **mounted on the device**. Same ImageBase, different build: 1.8 MB vs 4.9 MB,
  380 vs 391 exports. Regenerating from the device's DLL: 3 → 88. *This is the
  same class of error as 1.1, found the same day in a different table.*
* 88 is the ceiling regardless. Extension entry points are not exports at all —
  they are internal thunks Wine's opengl32 builds for `wglGetProcAddress`, so no
  export table can name them.

**The address was the wrong key.** `gl_ops` is generated on both sides from the
same macro lists (`ALL_WGL_FUNCS`, `ALL_GL_FUNCS`, `ALL_WGL_EXT_FUNCS`,
`ALL_GL_EXT_FUNCS`), so a slot's *position* already carries its name — by
construction, with nothing to look up and nothing to go stale.
`mgs2_gl_slot_name[]` expands those lists in declaration order;
`mgs2_island_gl_by_name()` resolves via `dlsym` then `eglGetProcAddress` against
the already-loaded driver. A `C_ASSERT` ties the array length to
`sizeof(struct wined3d_gl_funcs) / sizeof(void *)`, so a future shift between
names and slots fails the build rather than aiming every GL call one slot off.

Result: 3 → 88 → **233** of 493 non-null slots. The remaining 260 are not
reached on this path and stay NULL with a report.

### 1.3 The diagnostic instrument was keyed on the quantity under test

The prior session ended on `assertion failed: cs->thread_id ==
GetCurrentThreadId()`, with a TEB print showing guest thread id `0x134` while
Wine named the faulting thread `0130`. That print was capped at the first four
calls, all of which landed on one thread — so it said nothing about the thread
that failed.

Rekeyed to print once per *distinct* guest thread id, it reported one thread.
**That was still useless**: the guest id is derived from the emu, so "one id" is
equally consistent with "one thread enters" and with "the emu lookup is not
per-thread". Keyed on `pthread_self()` — ground truth, independent of the thing
being tested — it answered immediately:

```text
MGS2 teb: host thread 1 of 8: pthread 732ff120 -> emu 0x7df96f38, teb 0x3ffa2000, guest id 0x12c
wine: Unhandled page fault ... (thread 012c)
```

One host thread; its guest id matches the faulting thread exactly. The TEB path
is correct and the thread hypothesis is dead. Both readings from the earlier
brief's §26.3 are closed.

Two structural facts worth not re-deriving: on Wine i386 the FS base *is* the
TEB base, so `fs == teb` is correct rather than a symptom; and `teb + 0x24` is
`ClientId.UniqueThread`.

## 2. The island runs the game

`box86-island23` + `wined3d_p55_glinfo.dll`, island entries
`1,3,9,10,22,32,33`, autoloaded to the reinforcement save.

**`wined3d_buffer_load` is routed to native ARM and survives real play** —
eight 180 s in-game windows, **zero faults**. This is the first time the routed
island has reached in-game frames at all.

## 3. The A/B measures nothing, and the route is why

Controlled pair: one binary, one DLL, one save. The only difference between arms
is island entry 10 — the entry whose closure carries the 4821.9 calls/frame
dispatch. Arms alternated within one session; 180 s windows; medians over whole
`MGS2_GL_STATS` samples taken after load.

```text
with 10      18.60  16.75  18.90  16.45     median 17.68   range 16.45-18.90
without 10   16.70  17.30  18.80  17.05     median 17.18   range 16.70-18.80
```

Ranges overlap almost exactly. Median difference +0.50 fps, mean +0.22, against
a within-arm spread of ~2.4 fps on **both** configurations. `B3`, with the entry
disabled, produced 18.80 — level with the best routed arm. A ninth arm (`A4`)
autoloaded but produced no samples; recorded as lost, not dropped.

**Recorded as a null with its numbers.** Routing `wined3d_buffer_load` shows no
measurable frame-rate effect on this route.

### 3.1 The instrument cannot answer the question

Predicted prize for this cut was +1.1 to +2.3 fps. The route's own run-to-run
spread is 2.4 fps. **It cannot resolve the effect it was built to measure, in
either direction.** This null does not say the island is worthless; it says the
instrument is too blunt to weigh it.

Cause is the scene, not the clock: `autoload_save.py` loads and then walks, and
where the walk ends differs per run. The route was chosen for being heavy, not
identical.

### 3.2 Two of my own readings, superseded

Both are flagged here because the log contains them:

* **at three arms** I called the difference drift and put it at +0.05 fps. The
  reasoning was monotone thermal decay; `B3` at 18.80 refutes it. Right answer,
  wrong mechanism.
* **at five arms** I said two of three routed arms sat above both unrouted arms
  and an effect looked likely. `B3` and `A5` removed the pattern entirely.

Both were drawn while the within-group spread was already known to exceed the
difference being looked for. The generalisable lesson is not about thermals:
**do not read a direction out of a sample whose within-group spread exceeds the
effect**, however suggestive the ordering looks.

## 4. What would help most from research

1. **A fixed measurement scene.** This is now the binding constraint on the
   whole performance line, ahead of any further island work. Requirements: load,
   hold the camera fixed, measure a short window before the world reacts, and
   demonstrate the spread has collapsed below ~0.5 fps before any A/B is run on
   it. Without this, nothing in the +1-2 fps range is measurable on this device
   and further island entries are unfalsifiable.
2. **Whether the remaining 260 unresolved GL slots matter.** They are not
   reached by the current seven-entry cut. Widening the cut will reach some.
   Question: is there a principled way to enumerate which slots a given entry's
   closure can reach, rather than discovering it by crash?
3. **Sanity check on the fixpoint requirement.** Three iterations to converge
   surprised me and I do not have a clean explanation for why a fixed-size table
   moves `.text` at all. If the mechanism is obvious to someone, it may indicate
   something else shifting that ought not to.

## 5. Artefacts

Send these; they are self-contained against the previous handoff.

```text
docs/briefs/MGS2_ISLAND_ARMED_2026-08-16b.md      this document
docs/briefs/MGS2_REINFORCEMENT_FRAME_BUDGET_2026-08-14.md
                                                  sections 26-28 are new
box86-patches/07-native-island.patch              island + both guards
wine-patches/53-island-gl-by-name.patch           name-keyed GL slots
harness/island/full/fixpoint_class_b.sh           fixpoint loop
harness/island/full/gen_class_b_table.py          table generator
```

How to check the two guards actually fire:

* stale table — build without running the fixpoint loop; the run must print
  `MGS2 class-B: STALE TABLE` and refuse to arm, not crash.
* slot/name shift — add an entry to `mgs2_gl_slot_name[]`; the build must fail
  on the `C_ASSERT`, not the run.

Class-C generation must use the `opengl32.dll` **mounted on the device**, not
the reference wineprefix copy. The two share an ImageBase and differ in RVAs,
which is what made the first failure silent.

## 6. State on the device

Production unchanged and verified byte-wise: `box86-island10` +
`wined3d_p52_cs_census.dll`, 14 island entries matched, 0 faults, GPU governor
`performance` with save/restore on exit. The class-B/C work lives in
`box86-island23` + `wined3d_p55_glinfo.dll`, not wired into the launcher,
default off.

The CS deadlock census remains armed in production, waiting on a natural freeze.
Nothing in this session touched it.

Only measured gain to date is still the GPU governor, +10.8%.

## 7. Corrections this document makes

* the earlier "no fps effect" reading at three arms, and the "effect likely"
  reading at five — both superseded by section 3.
* a run-script fault counter matched `fixme:dmime:...Unhandled message type` and
  inflated 1 real fault to 19. Now matches `^wine:`, `forbidden instruction`,
  `assertion failed`, `STALE TABLE`.
* the fixpoint script's first version piped the generator to `tail`, so a
  generator crash left the header untouched and the loop declared convergence.
  Exit status is now taken from the generator directly. **This same
  false-fixpoint trap has now occurred twice in this project.**

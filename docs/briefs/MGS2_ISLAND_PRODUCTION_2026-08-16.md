# MGS2 RG353VS — island in production, and the CS deadlock census (2026-08-16)

Handoff for research. It follows the review of the 15 August delta and is
written to be read on its own; the long-form record is sections 17-25 of
`MGS2_REINFORCEMENT_FRAME_BUDGET_2026-08-14.md`.

Historical boundary: this records the first island promotion. Its production
state is superseded by `MGS2_ISLAND_MEASURED_2026-08-16c.md` and then
`MGS2_ISLAND_BATCH_STATE_MEASURED_2026-08-16d.md`; FINALPLAY6 now ships
island31 + p56 with measured entries 10 and 4.

Short version:

```text
measured gain      GPU governor, +10.8% fps, ranges non-overlapping
promoted           the native ARM island, 15 entries, on the owner's judgement
                   and explicitly NOT on a number
settled            all but 117 of 21,433,463 hot indirect calls resolve to a
                   function the island already has natively -- 99.9995%
withdrawn          the weak-ordering explanation for the freeze, in writing
open               the freeze, now instrumented so the next one self-diagnoses
```

## 1. The review's three corrections, all applied

Every checkable claim in the review was verified against the sources before
being accepted. All three held.

**"Cannot be armed in principle" was withdrawn.** The chain from "indirect call"
to "impossible" never followed from anything measured. `island_reach.py` counts
a register call as a *risk marker*; it cannot name a target. Two further errors
were found in the same analysis: it counted `bx lr` — a function return — as an
indirect call, which moved "entries free of indirect calls" from 1 to 7 when
fixed; and its control check keyed on the entry table rather than the call
graph, so it failed for a reason unrelated to the graph as soon as an entry was
dropped from the cut.

**`GetNativeFncOrFnc` does unwrap a bridge**, `bridge.c:205`:

```c
if (IsBridge((void*)fnc)) return (void*)((onebridge_t*)fnc)->f;
```

and `RunFunctionFmt` / `DynaCall` exist for the genuine-callback case. So a
guest-looking pointer is not automatically a trip through the emulator.

**WineD3D's indirect dispatch is its own backend model.** Static enumeration of
every ops-table initialiser against the linked ARM binary:

```text
ops tables                        56
targets named in them            270
present as ARM symbols           268
absent                             2   Vulkan state tables, not functions
```

Tool: `harness/island/full/island_ops_targets.py`, control check on the
`buffer_gl` dispatch the review named.

## 2. The runtime census settles it

Patch 50 instruments twelve ops-dispatch sites on the hot paths. It lives in the
**guest** DLL deliberately: the hot roots are not armed, so in the island they
never execute, while in the x86 build they run every frame against the same
objects and therefore the same pointer values. Each distinct target is
classified once, in the guest, and counted thereafter.

Owner-loaded heavy save, a real reinforcement encounter:

```text
site                                       calls     per frame  targets  class
buffer_ops->buffer_prepare_location   21,433,464       4821.9        1  wined3d-self
texture_ops->texture_prepare_location     18,008          4.1        1  wined3d-self
resource_ops->..._sub_resource_get_desc    5,371          1.2        2  wined3d-self
texture_ops->texture_unload_location       1,090          0.2        1  wined3d-self
resource_ops->resource_unload                234          0.0        1  wined3d-self
texture_ops->texture_load_location            51          0.0        1  wined3d-self
parent_ops->wined3d_object_destroyed         117          0.0        1  other-module

wined3d-self  21,433,346 of 21,433,463 calls = 99.99945%
other-module            117 calls = 0.00055%   (d3d8)
```

Written as "100.0%" earlier, which flattered it: it is 99.9995%, and the
difference is 117 genuine cross-module callbacks. The attract demo gives the
same shape independently (4.25M calls, one `other-module` target, 109 calls).

**The hot dispatch is single-target and internal.** One address per site, all
inside `wined3d.dll`, and all 32 WineD3D sources are already compiled for ARM,
so a native counterpart exists by construction. The only genuine cross-module
callback ran 117 times in 6530 frames. The reverse bridge layer that had been
priced as the blocking cost is, on this path, essentially absent. Single-target
dispatch also means a per-site cache of one entry would hit 100%.

This does not make the island fast. It removes the reason given for believing it
could not be made fast.

## 3. Two silent defects found while promoting

**Nine markers were outside Box86's matching window.** The matcher scanned the
first 16 bytes of a call target; nine of the 37 markers sit further in, up to
+60. Those entries could never match. Runs had been reporting "15 armed, 11
matched" and that was read as "four were not called" — three of the four were
unreachable by construction. The window is now 64, and
`harness/island/full/island_marker_check.py` checks every id against it, and
against appearing in more than one function. With it fixed: 15 armed, **14
matched**.

**The patch series did not apply.** Applied from scratch to the pinned Box86
commit, patches 07-12 all failed. Each had been exported as a diff from
pristine, so each silently contained its predecessors — patch 01 already adds
`wrappedlibegl.c`, patches 02/05/06 already add their `box86context.c` blocks.
Individually each looked right; in sequence none could apply, and nobody had
tried. Now one incremental `07-native-island.patch`, zero fuzz, reproducing the
deployed binary's `.text` byte for byte (501 of 8,484,024 bytes differ: the
build-id, the build timestamp, and the absolute source path `__FILE__` bakes
into the dynarec log strings — build it from a differently named directory and
that becomes ~99,000 with `.text` unchanged, so compare sections, not files).

## 4. Production state

```text
box86-island10                  island, 15 entries armed, 14 matched
wined3d_p52_cs_census.dll       island markers, lab counters compiled out,
                                CS census on; sha256
                                200aa9bea336e604089ad4ef862e288fd146ea353b64b5bed125cf435ec064a6
d3d8_finalplay3_nocullcache.dll unchanged
GPU governor                    performance (800 MHz)
rollback                        MGS2_BOX86_ISLAND_FULL=0
                                MGS2_GPU_GOVERNOR=simple_ondemand
                                MGS2_CS_DEADLOCK_CENSUS=0
```

**The GPU governor is the only measured gain.** The dead-end list had closed it:
pinning to 800 MHz halved GPU wait but dropped the CPU cap to 816 MHz on a
shared thermal budget. That was measured before the cooling was fixed. Re-tested
in one process at one spot with the governor switched live and arms interleaved:

```text
simple_ondemand   n=35   median 15.20   mean 15.209   sd 0.227
performance       n=39   median 16.90   mean 16.851   sd 0.088
                         +1.64 fps, +10.8%
```

Ranges do not overlap (best ondemand 15.7, worst performance 16.6), and the CPU
held 1992000 in every arm — the old throttling did not recur. Ended at 78.1 C
CPU / 73.3 C GPU against an 88 C cutoff. A long multi-spot thermal soak has NOT
been done.

**The island is promoted on the owner's judgement that the game plays
correctly, not on a number.** No frame-rate effect is measured for it in either
direction: on the reinforcement scene it gave 13.3-15.0 fps, inside the
11.9-19.5 band that scene already had, with no control arm. The four entries
that carry the frame are still not routed.

## 5. The freeze: what was wrong, and what is now instrumented

A weak-ordering explanation was asserted — WineD3D publishes with plain stores,
x86 has TSO, ARM does not, `STRONGMEM=0` adds no barriers — and it is
**withdrawn**. Wine 11.0 does not do that:

```c
InterlockedExchange((LONG *)&queue->head, queue->head + packet_size);
if (InterlockedCompareExchange(&cs->waiting_for_event, FALSE, TRUE))
    pNtAlertThreadByThreadId(...);
/* and the consumer guards the exact race, with a comment saying so */
InterlockedExchange(&cs->waiting_for_event, TRUE);
if (!(queue_is_empty(DEFAULT) && queue_is_empty(MAP))
        && InterlockedCompareExchange(&cs->waiting_for_event, FALSE, TRUE))
    return;
```

Both sides are interlocked, and Box86 emits `SMDMB()` around lock-prefixed
instructions regardless of `STRONGMEM` — which this project had already
established and then failed to apply to its own reasoning.

The second correction matters more: `0x400f012c` is the **per-thread alert
futex** behind `NtWaitForAlertByThreadId`, not a queue word. `0 -> 0` proves
"no pending alert", not "a publication was missed".

**Patch 52** implements the census the review asked for. Memory only, no
logging; it records the sync events and publishes the live `cs` pointer plus the
field offsets from `FIELD_OFFSET`, so `harness/cs_deadlock_census.py` follows
them through `/proc/pid/mem` and needs no debug info. Executes are counted but
never ringed — thousands a frame would flush the history that matters.

Live on a running game, so the instrument is known to work:

```text
submits 1508295  alerts 12598  executes 1508159
wait: prepare 12605  enter 12598  return 12598  abort-nonempty 7
cs at 0x5860020
DEFAULT head 0x59cbca0 tail 0x59c99e4  NOT EMPTY
MAP     empty        waiting_for_event 0
```

`abort-nonempty 7` is Wine's own guard against that race firing and being seen.

**The reader's verdict needs more than `head != tail`, and an earlier version of
it did not have more.** A running consumer routinely has a non-empty queue --
the live capture above is proof, and that reader would have declared A on a
healthy game. Wine only sleeps after setting `waiting_for_event`, re-checking
both queues and cancelling the sleep if it finds work, so a stuck consumer must
show all of:

```text
the CS thread actually blocked in a futex wait
waiting_for_event == 1
head != tail
head, tail, the execute counter and the event ring all unchanged
across several samples (default 5 at 200 ms)
```

`harness/cs_deadlock_census.py` now samples repeatedly and returns one of three
answers, with INDETERMINATE preferred over a confident wrong one:

```text
A   stable non-empty queue, waiting_for_event set, consumer blocked
      -> published work is not being run; the handshake and Box86's atomics
B   stable empty queues, waiting_for_event set, consumer blocked
      -> the CS is correct; move to what the main thread waits for in ntsync
INDETERMINATE  anything still advancing, or blocked with waiting_for_event 0
```

### 5.1 The accelerated soak was null

Six cycles, three per `STRONGMEM` arm, 300 s each, with `MGS2_CS_SPIN_COUNT=1`
so the CS crosses queue-empty → `waiting_for_event` → alert wait on nearly every
drain instead of once per 2000 idle spins:

```text
sm=0  OK 18.4, 19.1, 18.2 fps        sm=1  OK 16.7, 18.8, 16.6 fps
```

No freeze in either arm, so this says nothing about `STRONGMEM` and nothing
about the cause. A weak point in favour of B: lowering the spin count 2000x did
not provoke it, and if the fault were on that boundary, that is the cheapest way
to hit it. One null soak is not evidence and is recorded as a null.

Side observation, not a measurement: `STRONGMEM=1` averaged 17.37 against 18.57
fps, about -6.5%, one sample per cycle on a route that walks.

All three freezes so far happened in real play, none under a harness. So the
census now ships in the play configuration and the next natural freeze
self-diagnoses.

## 5.2 Priority, after the review

Two independent lines, and the performance one now looks the stronger:

```text
performance   class-B resolver -> arm wined3d_buffer_load ALONE -> A/B/A on the
              reinforcement route. Its closure holds the 4821.9/frame
              buffer_prepare_location dispatch, so it is the single root most
              likely to move whole subgraphs out of the dynarec.
              NOT a hash map: 4822 lookups a frame needs a per-call-site cache
              of one entry, or a generated direct comparison. Single-target
              dispatch measured, so a one-entry cache hits 100%.
reliability   census stays armed in production until the next natural freeze,
              and the reader now answers A / B / INDETERMINATE.
```

## 6. What would help most from research

1. **Sanity-check the A/B criterion.** Is `head != tail` at capture time
   sufficient to conclude "published work with a sleeping consumer", or can the
   consumer legitimately be asleep with a non-empty queue in Wine 11 — for
   example between `wined3d_cs_execute_next` and the tail update?
2. **The ntsync side.** In verdict B the question becomes what the main thread
   waits for. Is there a comparable memory-readable state for Wine 11's ntsync
   objects, so a frozen process can be interrogated the same way?
3. **The class-B resolver.** The mapping "guest wined3d address → native ARM
   symbol" must be generated from the exact i386 build and the exact ARM object
   set. Any prior art on doing this safely across a PE/ELF boundary, and on
   where such a resolver should sit — in the island's dispatch macro, or in
   Box86 next to `GetNativeFncOrFnc`?

## 7. Artefacts and how to check them

```text
box86-patches/07-native-island.patch     whole island, incremental on 01-06
box86-patches/BUILD.md                   series, and the path caveat on hashes
wine-patches/48-island-marker-i386-only.patch
wine-patches/49-island-arm-guest-teb.patch
wine-patches/50-island-icall-census.patch
wine-patches/52-cs-deadlock-census.patch
harness/island/full/island_reach.py      reachability, TEB, indirect calls
harness/island/full/island_ops_targets.py ops targets vs ARM symbols
harness/island/full/island_marker_check.py markers vs Box86's window
harness/island_icall_census.py           indirect-target reader
harness/cs_deadlock_census.py            CS deadlock reader, prints A or B
harness/island_freeze_soak.sh            soak, results on /storage not tmpfs
logs/rg353vs/island-marker-20260815/     every capture behind the numbers above
```

Every analysis tool prints its own control check and exits non-zero when it
fails. Three of them failed at least once and were fixed because of it; that is
the only reason the numbers here are usable.

## 8. Corrections this document makes to earlier claims

```text
"the four hot entries cannot be armed"          withdrawn, section 1
"1 of 37 entries is free of indirect calls"     was 7; bx lr counted as a call
"no entry matched, no stub reached" (16 Aug)    was the log level, not a fact
"the i386 output is byte-identical"             67 bytes differ, all __LINE__
"zero faults" on the heavy run                  14 handled SIGSEGV, = baseline
"weak ordering explains the freeze"             withdrawn, section 5
```

Six retractions in two days. Each was caught by a control check or by review,
never by the analysis that produced it, which is the argument for keeping both.

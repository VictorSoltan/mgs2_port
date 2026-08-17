# The native ARM WineD3D island: marker fix, guest TEB, and the first live run

Evidence for sections 17 and 18 of
`docs/briefs/MGS2_REINFORCEMENT_FRAME_BUDGET_2026-08-14.md`.

All runs use `launch-island-dbg.sh`, which differs from production
`launch-play.sh` by one line: it lets `BOX86_LOG` be set from outside. The guest
DLL is `wined3d_p47_island_markers.dll`, byte-identical in every arm, and never
rebuilt -- patches 48 and 49 change only the ARM objects.

## The illegal instruction, before and after

```text
isl-R-before.log   box86-island4   wine: Unhandled illegal instruction at 4002017B
isl-R-after.log    box86-island6   MGS2 island: forbidden call to WindowFromDC
isl-R-only5.log    box86-island6, ISLAND_ONLY=5     full window, no fault
isl-S1-smoke.log   box86-island7, ISLAND_ONLY=1,3,22,32,33
                                   5 armed, 5 matched, 130 s, no fault
```

`box86-island6` differs from `island4` only in the rebuilt ARM objects (patch 48:
the x86 entry marker is emitted under `#ifdef __i386__`) plus Box86 patch 10.
`box86-island7` adds patch 49 (guest TEB), Box86 patch 11 (native replacements
for the six reached stubs) and drops entries 21 and 30 from the cut.

## attract-ab/ -- a failed measurement, kept deliberately

Four interleaved 240 s arms, one binary, one DLL, one clock, differing only by
`MGS2_BOX86_ISLAND_FULL`:

```text
OFF   73 samples   median 60.10   mean 59.736
ON    74 samples   median 60.10   mean 59.708
                                  -0.028 fps (-0.05%)
```

The attract demo sits on the 60 Hz ceiling -- 29 of 37 samples at exactly 60.2,
and the dips to 57.4 recur at identical positions in all four arms. The harness
is sound and the scene is wrong. Do not use the attract demo for a frame-rate
A/B; AGENTS.md's "31/9/11/4 frames" figures are stall buckets, not fps.

## heavy-on1.log -- the island on the target scene

The owner loaded the heavy save and played a real reinforcement encounter,
15 entries armed:

```text
window 1   60 s    900 frames   15.0 fps   19.0 12.7 14.4
window 2   90 s   1200 frames   13.3 fps   13.1 14.6 15.1 15.2
CPU 2.03 s per wall second, 1992 MHz held, 68 -> 70 C
armed 15   matched 11   faults 0   forbidden 0   assertions 0   ERRs 0
```

Eleven WineD3D functions ran as native ARM through 2100 frames of live combat
without a fault. No frame-rate conclusion: 13.3-15.0 fps is inside the
11.9-19.5 band this scene already had, and there was no control arm -- the owner
was under fire and could not stand still or repeat the route.

The first window's CPU figure was discarded: the sampler read `$14`/`$15` from
`/proc/PID/stat`, which POSIX sh parses as `${1}4`. Fixed before window 2.

## island_reach*.txt

`harness/island/full/island_reach.py` over the linked binary: reachable abort
stubs, `NtCurrentTeb()` reads and indirect call sites per entry, with its control
check passing.

```text
island_reach.txt                 box86-island6:  7 of 37 entries clean
island_reach_after_natives.txt   box86-island7: 15 of 35 entries clean
```

The `.log` files are gitignored by repo policy and kept here for the working
tree; NOTES.md and the two `island_reach` files are the committed record.

## The reinforcement-scene census, and a freeze caught on the way

`oneshot/` -- production Box86 with the patch-50 census DLL, owner-loaded heavy
save, a real reinforcement encounter. This is the run that exonerated the census
DLL: it played the fight through where box86-island8 had died.

```text
21,433,464 buffer_ops->buffer_prepare_location   4821.9/frame   ONE target
wined3d-self 100.0%   other-module 0.0% (d3d8, 117 calls in the whole run)
segmentNULL 0   SIGILL 0   Unhandled 0   SIGSEGV 14 (baseline)
peak RSS 439 MB, min MemAvailable 192 MB, 1992 MHz held, 70 C, dmesg empty
```

`freeze9/` -- box86-island9 (the __thread pair withdrawn) on the same save. No
segment warnings and no death, but the game froze, and the capture names it:
wined3d_cs, the main thread and wine_dmime_mess all in untimed futex waits on
Box86 sync-arena words (0x400f012c / 0x400f0140 / 0x400f0150), 14 threads
unchanged across two samples, 0 progressed. That is the open freeze of
2026-08-12, which predates all island work. A 5838 ms frame preceded it; the run
that died under island8 was preceded by a 5778 ms frame, so the two may be the
same event with different endings.

`verify9/` -- the same run's game log and 0.5 Hz monitor (RSS, MemAvailable,
temperature, frequency, alive).

# Research brief #6 — performance: the game is CPU-bound, and a third of the CPU is syscall overhead

Self-contained. Project history: `MGS2_PROJECT_STATE.md`. Previous briefs covered rendering
correctness; this one is entirely about frame rate, which is now the main complaint.

> **Update after the first round of experiments.** §2a and §2b below stand. The yield
> *remedy* does not: measurements of it are mutually contradictory and no fix is being
> promoted. See §7 for what was tried, what inverted, and the two questions that now matter
> most. The single most useful thing an outside reviewer could resolve is §7.3 — why a
> locally rebuilt Wine library behaves differently from the shipping one on this device.

---

## 1. Setup, in one paragraph

Metal Gear Solid 2: Substance (PC, Direct3D 8, 2001) on an Anbernic RG353VS — Rockchip
RK3566, four Cortex-A55 cores, Mali-G52, **libmali, OpenGL ES 3.2 only**, 975 MB RAM,
RockNIX. box64 launches Wine 11.0 (old WoW64); because the game is a 32-bit PE, Wine
re-execs its own `i386-unix/wine` and **the entire 32-bit stack — the game, wined3d,
opengl32, win32u, ntdll — runs as emulated x86 under box86**. Only libmali and the kernel
are native. Path: D3D8 → local `d3d8.dll` proxy → d3d9 → WineD3D → GLES.

The game is playable end to end: menus, codec conversations with portraits, Tanker
gameplay, rain, cutscenes. **It runs at roughly 15–23 fps** at 640×480, and that is now the
limiting defect.

## 2. What has been measured

Every number below is a runtime measurement on the device, not an estimate.

### 2a. Graphics is not the bottleneck — this is settled

| experiment | result |
| --- | --- |
| normal gameplay | 15.1, 15.2, 23.1 fps |
| **all draws and all state application skipped** (`MGS2_SKIP_ALL_DRAWS`) | 13.1, 18.5, 21.0, 23.4 fps |

Removing the entire rendering path does not change the frame rate; the ranges overlap
completely. A `perf` profile of 20 s of live gameplay agrees:

| where CPU time goes | share |
| --- | --- |
| kernel (`[kernel.kallsyms]`), overwhelmingly the scheduler | **39%** |
| box86 JIT-translated code (anonymous exec pages) | 33% |
| box86 runtime itself (wrapper trampolines, `DBGetBlock`) | 7% |
| **libmali — the actual GPU driver** | **4.5%** |

By thread: game main thread 63%, `wined3d_cs` 21%, DirectMusic synth 5%, DirectSound mixer
3%, the rest smaller.

**Consequence: presentation, zero-copy, shader and texture-format optimisation are all
dead ends.** The GPU is idle. Do not propose them.

### 2b. The process is CPU-saturated

`top` during gameplay: the game process at **187–264% CPU** (of 400% available), system 90%
busy across all four cores, `56.7% us / 36.7% sy`. That system-time share is the anomaly.

### 2c. One third of a million syscalls per second, from one function

Wine's `NtYieldExecution` (`dlls/ntdll/unix/sync.c`) is **three syscalls, not one**:

```c
ret = getrusage( RUSAGE_THREAD, &u1 );
sched_yield();
if (!ret) ret = getrusage( RUSAGE_THREAD, &u2 );
if (!ret && u1.ru_nvcsw == u2.ru_nvcsw && u1.ru_nivcsw == u2.ru_nivcsw)
    return STATUS_NO_YIELD_PERFORMED;
```

The `getrusage` pair exists **only** to decide between `STATUS_SUCCESS` and
`STATUS_NO_YIELD_PERFORMED`. That distinction has exactly one consumer in the entire Wine
tree: `SwitchToThread` in `dlls/kernelbase/thread.c`.

In the profile, `getrusage` and `sched_yield` appear in equal numbers (57 and 57 samples,
5.6% each), both exclusively on the game's main thread, and the leaf symbol under
`getrusage` is `__pi_memset_generic` — the kernel zeroing `struct rusage`, twice per yield.

An instrumented build counted the calls directly:

```
MGS2 yield: 50000 calls in 357 ms = 140056/s
MGS2 yield: 50000 calls in 367 ms = 136239/s
MGS2 yield: 50000 calls in 391 ms = 127877/s
```

**~130 000 calls/second ⇒ ~390 000 syscalls/second**, every one crossing the 32-bit compat
entry (`el0t_32_sync` → `do_el0_svc_compat`). At ~18 fps that is roughly **7 000 yields per
rendered frame**.

The caller is Wine's own message pump — `NtUserPeekMessage` in `dlls/win32u/message.c`:

```c
if ((ret = peek_message( &msg, &filter )) <= 0)
{
    if (!ret)
    {
        flush_window_surfaces( TRUE );
        KeUserDispatchCallback( ... );       /* thunk lock */
        NtYieldExecution();
        KeUserDispatchCallback( ... );
    }
    return FALSE;
}
```

So every `PeekMessage` that finds an empty queue costs a window-surface flush, two user-mode
callbacks and three syscalls. MGS2's main loop polls the queue thousands of times per frame.

A subtlety worth stating: process context-switch counters show only ~1 000 **involuntary**
switches/s, not 130 000. Most `sched_yield` calls therefore return immediately without
switching to anything — the cost is the syscall entry/exit and the kernel memsets, not
rescheduling. An earlier estimate of "~1 000 yields/s" derived from those counters was wrong
by a factor of 130.

### 2d. Thermal and clock state

Governor `performance`. The launcher's thermal guard steps a frequency ladder down as
temperature rises; **1416 MHz observed early in a session, 1104 MHz after sustained load**,
against a hardware ladder whose top is 1608 MHz and `cpuinfo_max_freq` of 1992 MHz.
Sequential benchmark runs therefore measure progressively slower silicon — the A/B protocol
now pins a single frequency step and cools to 70 °C between runs.

### 2e. box86 configuration

Already aggressive: `BOX86_DYNAREC_SAFEFLAGS=0 BOX86_DYNAREC_BIGBLOCK=2
BOX86_DYNAREC_FORWARD=512 BOX86_DYNAREC_CALLRET=1`. box86 v0.3.9, box64 v0.4.2.
`perf` and `gdb` are both present on the device.

## 3. The questions

### 3.1 Is the yield elimination worth anything, and what is the game actually waiting for?

An A/B is in flight (`MGS2_YIELD=full|fast|none`, where `fast` drops the `getrusage` pair
and `none` removes the syscall entirely). But the deeper question is upstream:

**Why does a 2001 engine poll `PeekMessage` ~7 000 times per frame?** If this is a
deliberate busy-wait — a frame limiter, a spin on a present/vsync completion, a wait on an
audio or streaming event — then making the spin cheaper frees CPU for other threads but may
not raise the frame rate at all. If instead the loop is bounded by *work* the game thinks it
still has to do, the yields are pure loss.

Concretely: is there a known pattern in Konami's PC engine of this era (or in the
`MGS2-Source-main` tree, which we have) for `while (PeekMessage(...)) ...` used as a timing
loop? What is the standard fix in other Wine/Proton ports of games with this behaviour?

### 3.2 Should the fix live in Wine, and where?

Candidates, from least to most invasive:

1. Drop the `getrusage` pair in `NtYieldExecution` — 3 syscalls → 1, semantics change only
   for `SwitchToThread`'s return value. Is any real application known to depend on
   `STATUS_NO_YIELD_PERFORMED`?
2. Skip or rate-limit the `NtYieldExecution()` in the empty-`PeekMessage` path. Risk: on a
   loaded system this yield is what keeps a spinning app from starving other threads. On a
   4-core device with ~2 busy threads, is that risk real?
3. Cache the `flush_window_surfaces(TRUE)` / thunk-lock callbacks on the empty path, which
   also run thousands of times per frame.

Has upstream Wine, Proton, CrossOver or any Android Wine fork already addressed the cost of
this path? CrossOver Android 17 sources are available locally and were the source of the
single biggest win in this project so far, so a precedent there would be especially useful.

### 3.3 Where else does the emulated stack lose time?

33% of samples are in box86-translated code and 7% in the box86 runtime, with
`DBGetBlock` (dynarec block lookup) visible among the hot symbols. Given the dynarec flags
are already at their aggressive settings:

* Are there box86 tuning options for this workload beyond `SAFEFLAGS`/`BIGBLOCK`/`FORWARD`/
  `CALLRET` that are known to matter for Wine specifically?
* `wined3d_cs` is 21% of the profile. Wine's CSMT packs every command into a queue for a
  second thread; under emulation both sides are translated. Is disabling CSMT
  (`WINE_D3D_CONFIG=csmt=0`) known to be a win on emulated/low-core targets, or does the
  loss of overlap dominate? (This A/B is cheap and is queued next.)
* DirectMusic software synthesis costs ~5% and issues more ioctls than anything else in the
  profile, with continuous `synth_sink_write_data Underrun detected`. Is there a cheaper
  DirectMusic path (a real MIDI sink, or disabling the software synth) for a game that may
  not need it?

### 3.4 Thermal headroom

The device throttles to 1104 MHz under sustained load while the ladder offers 1608 MHz and
the hardware reports 1992 MHz. Given the console has previously reset near 92 °C, is there a
safe way to hold a higher sustained clock — a different governor, a fan-less duty-cycle
strategy, or an undervolt — on RK3566 under RockNIX?

## 4. Hypotheses already closed — please do not re-open

* **GPU/driver bound.** libmali is 4.5% of the profile and removing all rendering changes
  nothing. Presentation, PBO/zero-copy, shader and texture-format work are all ruled out.
* **The game is idle and merely waiting on a timer.** It is not: 187–264% CPU, 90% system
  busy. (This was briefly and wrongly concluded from a CPU sample accidentally taken on
  `gptokeyb` rather than the game process.)
* **~1 000 yields/second.** Wrong by 130×; measured directly at ~130 000/s.
* **box86 dynarec left at defaults.** It is not; the aggressive flags are already set.

## 5. Reproducing the instrumentation

| variable | effect |
| --- | --- |
| `MGS2_SKIP_ALL_DRAWS=1` | return before state application and the draw (bounds the graphics share) |
| `MGS2_GL_STATS=N` | log `N frames in X ms` plus readback timing from the presentation path |
| `MGS2_NTDLL_SO=ntdll_yield1.so` | mount the instrumented ntdll |
| `MGS2_YIELD=full\|fast\|none` | stock / no `getrusage` pair / no syscall |
| `MGS2_YIELD_STATS=1` | log the yield call rate |
| `MGS2_FREQ_STEPS=1104000` | pin the frequency ladder to one step so runs are comparable |

`recovered-session/scripts/ab.sh` drives a run into gameplay and samples it; it refuses to
start concurrently with another instance and reports how many library overrides were
mounted, both after silent failures of exactly those kinds.

## 6. Measurement traps hit while producing this brief

Recorded because each one produced a confident wrong answer first:

* **Profiling the wrong process.** `pgrep` returned `gptokeyb` before the game; its 3% CPU
  was reported as the game's, briefly inverting the entire conclusion.
* **A locally built `ntdll.so` makes `ps` show unprintable garbage instead of the exe name.**
  The harness identified the game by process name, so five runs were reported as "died
  before first frame" while the game was rendering normally. Match the command line.
* **Two A/B loops ran concurrently** after `killall` removed the child scripts but not their
  parent shells. Each run's cleanup unmounted the other's bind mounts, so the game silently
  ran on stock wined3d and win32u. The harness now reports the mount count per run.
* **Thermal drift across sequential runs** measures each successive configuration on a
  slower CPU.
* **`WINEDEBUG=-all` silences the frame counter**, which is emitted on `err+waylanddrv`.
* **Identifying the game process has failed four separate ways** — by `comm` (garbage with a
  rebuilt ntdll), by two different command-line forms (Wine rewrites `argv[0]` with the
  stock ntdll but not with ours), by a pattern that also matches `gptokeyb`, and by a
  hardcoded executable name when `MGS2_EXE` selected a variant. Every one of them reported
  a healthy, rendering game as dead.
* **`pkill -f` matched the invoking ssh command line again**, because that command line
  contained `MGS2_EXE=mgs2_sse_rg353vs_moviestart.exe`. The `[b]racket` trick does not help
  when the pattern is genuinely present in your own arguments. Use `killall` with exact
  process names.

## 7. The yield remedy: three experiments, mutually contradictory

### 7.1 What was measured

All windows 120 s, cooled to 70 °C before each run, launcher frequency ladder pinned.

**Experiment A — all modes inside a locally rebuilt `ntdll.so`:**

| mode | mean fps | yield rate | clock in window |
| --- | --- | --- | --- |
| `full` — stock behaviour, three syscalls | 6.21 | 95–106k/s | 816 MHz |
| `fast` — `sched_yield` only | **11.82** | 211–267k/s | 816 → 1104 MHz |
| `none` — no syscall at all | 6.29 | 297–442k/s | mean 972 MHz |

**Experiment B — the shipping `ntdll.so`, with and without a five-byte patch** that makes
the first `getrusage` call return non-zero so both `getrusage` calls are skipped and
`sched_yield` still runs:

| build | mean fps | clock |
| --- | --- | --- |
| shipping, untouched | **12.18** | 1104 MHz, no variation |
| shipping, patched | 8.07 | 1104 MHz, no variation |

Experiment B sampled a **byte-identical scene** in both configurations — the same codec
conversation, the same line of dialogue, verified by screenshot — so scene variance is
excluded there.

### 7.2 Why this is not yet a conclusion

* A says the cheap yield nearly doubles the frame rate. B says it costs a third.
* A's three modes share a rebuilt ntdll; B's two share the shipping one. The variable the
  two experiments do not hold constant is **the ntdll build itself**.
* Independently: two separately built `win32u.so` from the same tree (one from a previous
  session, one fresh) both hang the game at `eglInitialize`, while the shipping
  `win32u_glfuncs3.so` plays fine. So the tree provably does not reproduce this device's
  Wine binaries, and "our rebuilt ntdll is equivalent to the shipping one" is an assumption
  with direct counter-evidence next door.
* A's windows also ran at genuinely different clocks (816 vs 972 vs 816→1104), which B's
  did not.

Also worth knowing before interpreting any of these numbers: the harness samples during a
**codec conversation**, not gameplay. Unpinned, in actual gameplay, the game renders
**21.9–23.8 fps**, and 60 fps in menus.

### 7.3 The question that would unblock this

**Why would a Wine 11.0 library built from the matching source tree behave differently from
the one shipped on the device?** Candidates we cannot distinguish from here: a different
configure line (the shipping `ntdll.so` is 709 KB, ours 3.3 MB), a distro patch set, a
different compiler or libc, or a PE/Unix interface version skew. Is there a reliable way to
recover the exact build configuration from a Wine `.so` — beyond `BuildID`, which we have —
or a known list of downstream patches for the Wine that ships in RockNIX?

Until that is answered, every conclusion drawn by swapping in a rebuilt library is
confounded, and only binary patches to the shipping files are trustworthy.

### 7.4 The narrower technical question

Given `none` (no yield at all) measured no better than stock in experiment A, the yield
appears to be load-bearing: the main thread must give the CPU up or `wined3d_cs` and the
wineserver round-trips starve. If that is right, the interesting variable is not "yield or
not" but **how often** — and the useful range is small (every 2nd, 4th, 8th empty poll),
not the 128–512 that seemed reasonable before `none` was measured. Is there prior art on
tuning yield frequency in a Wine message pump under emulation?

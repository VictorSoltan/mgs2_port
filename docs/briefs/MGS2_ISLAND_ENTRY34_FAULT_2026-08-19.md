# MGS2 RG353VS — island entry 34 faults on arming, so the next two roots are not measurable yet (2026-08-19)

Handoff for research. Continues `MGS2_ISLAND_MEASURED_2026-08-16c.md` (entry 10,
−8.87 ms/frame) and `MGS2_ISLAND_BATCH_STATE_MEASURED_2026-08-16d.md` (entry 4,
+0.899 fps). Research's reply to 16c section 5.1 asked for the remaining
frame-carrying roots in this order: `wined3d_texture_load_location`, then
`wined3d_rendertarget_view_load_location`, then a coarse
`wined3d_cs_exec_draw_one`. This is what came back from trying the first one.

Sections 1-10 are the first half of the day, when the fault had been reproduced
but not explained. **Sections 11 onwards close it**: the cause is found, fixed,
and the fix is verified not to touch the shipping DLL. Read 11-16 first if you
only want the answer.

```text
measured      nothing about frame rate. No A/B number was obtained and none is
              claimed
ROOT CAUSE    the island's translated gl_info was consulted by GL_EXTCALL() and a
              few hand-converted sites, and nothing else.
              315 plain `gl_info->gl_ops...` / `fbo_ops` call sites read the
              GUEST table, so native ARM branched into x86 bytes. Fixed by
              patch 61; the illegal instruction is gone and entry 34 now fails
              legibly on a NULL GL slot instead (sections 11-13)
found         arming island entry 34 (wined3d_texture_load_location) kills the
              renderer within the first frames. Without the A/B gate:
              "Unhandled illegal instruction at 4002013B", which is entry 34's
              OWN bridge + 0xB -- an artefact: the dynarec parks the guest EIP
              there before calling the wrapper, so any host fault in native ARM
              code reports at that address. With the gate the process survives
              but the CS consumer stops with published work pending
found         entry 22 IS IN PRODUCTION and is bound to the wrong address: the
              64-byte marker window matched it from a mid-function address in
              the PRECEDING function (section 14)
found         the fail-closed preflight now runs in 25 s and refuses entry 34,
              entry 23 -- and also entry 10, which is measured production and
              demonstrably fine. Fail-closed on this analysis alone would
              disarm a measured win (section 15)
controls      the production 17-entry allow-list runs; entry 10 through the same
              launcher, same base, same err+all logging runs and produces nine
              A/B cycles. The harness, the base, the logging and the launcher are
              therefore not the cause
found         the patch record did not reproduce the production Box86: patch 08
              recorded the hot-page budget fix only, while box86-island32-prod
              also carries __thread hotpage. Split into patches 08 and 09 and
              verified against .tbss without an ARM disassembler
route         the attract/menu route cannot measure these entries: 3 of 9 cycles
              were call-count balanced, all inside the capped low-load window.
              The owner's save and real gameplay is required, as 16c already said
toolchain     the armhf cross toolchain was missing for the whole first half --
              which is why box86-island32-prod is not reproducible -- and was
              reinstalled for the second. Everything from section 11 needed it
```

## 1. What was verified before anything ran

Byte-wise, per rule 4 — the device copies against the repository and against
`device/FINAL_PRODUCTION.sha256`:

```text
box86-island32-prod              c75e87a4e244b7a4e098af5a440ead0dd3338e49af1c40d6afe00fba957e82de
wined3d_p56_batch_state.dll      6a926918fd40ce2e883dce6465392f8cbe791d474a3822e0408ea907489a7471
d3d8_finalplay3_nocullcache.dll  841ff73c2b99fd6ca2ee00b0796abbb9e0d38b584cb298cb9860afbee9ea1de0
launch-play.sh                   22a80b9d19d91018c59986bcc858e27051a4a384cb3492a059ed5f1529852c79
```

**The A/B instruments for both candidate roots already existed.** No code had to
be written to measure them. `wined3d_texture_load_location` is island entry 34
and `wined3d_rendertarget_view_load_location` is entry 23, and both have
dedicated ABBA wrappers — `mgs2_island_w_ab34_uFpupu`, `mgs2_island_w_ab23_vFppu`
— in `mgs2_island_bridges.c`. They are present in **all three** shipped island
binaries, established by locating the `mgs2_island_entries` array in each file
(35 records of `{id, wrapper, impl}`, ids 0-20, 22-29, 31-36) and resolving the
wrapper addresses against the unstripped `box86-island32-hotpage` symbol table:

```text
entry 23 wrapper 0x628b0158 = mgs2_island_w_ab23_vFppu    (entry 24 uses 0x628afc74)
entry 34 wrapper 0x628b00ac = mgs2_island_w_ab34_uFpupu   (entry 35 uses 0x628afdf8)
```

Neither entry is in the production allow-list, so both run as emulated x86 in
normal play.

One launcher defect fixed first: `device/launch-island-ab.sh` pinned
`MGS2_BOX86_BIN=box86-island31`, while `launch-play.sh` now defaults to
`box86-island32-prod`. A candidate has to be measured on the base that is
actually played, so the pin now follows production and the file says why.

## 2. Entry 34 with the A/B gate: the process survives and stops rendering

`./launch-island-ab.sh 34`, twice, production base, 18 of 35 entries armed
(the production 17 plus the candidate), class-B armed with both witnesses
agreeing:

```text
MGS2 island: 18 of 35 entries armed (only="0,...,33,34")
MGS2 class-B: 1616 native IDs registered by the linker
MGS2 class-B: armed, guest wined3d base 0x7b760000, agreed by
              wined3d_texture_from_resource and context_invalidate_state
```

Both runs reached the first present — `wayland_drawable_swap` printed its
one-time capability lines, 640x480 — and then stopped. No further frames, no
`present stats` line, and **zero CPU ticks across the whole process** over a 4 s
window. Run 1 was left alone for about five minutes and never advanced.

The CS deadlock census, armed in production, on run 1:

```text
submits 52  alerts 3  executes 48
DEFAULT head 0x728 tail 0x5f0   NOT EMPTY
MAP     head 0x0   tail 0x0     empty
waiting_for_event 0
executes unchanged   ring unchanged   queue unchanged   wfe unchanged
last 20 ring events: all SUBMIT from tid 0x24, tail frozen at 0x1e0
```

Read that with the counters: the ring's last entry is a SUBMIT taken when
`executes` was 17, the header says `executes` reached 48, and the live tail is
0x5f0 against a ring tail of 0x1e0. So the consumer went on past the last
recorded sync event, advanced the tail to 0x5f0, and stopped there with the
producer's head at 0x728. `waiting_for_event` is 0, so it did not stop in
WineD3D's wait path, and no task in the process is running, so it is not a
livelock either.

That is a consumer that died inside command execution, which section 3 confirms
directly.

## 3. Entry 34 without the gate: an illegal instruction in its own bridge

To separate the native route from the A/B gate's guest-body path, the same 18
entries were armed with **no** `MGS2_ISLAND_AB`, so every call to entry 34 goes
native. The process did not hang — it died:

```text
MGS2 island: armed entry 34 -> bridge 0x40020130
...
0130:err:waylanddrv:wayland_drawable_swap MGS2 framebuffer: samples=0 ...
0130:err:waylanddrv:wayland_drawable_swap MGS2 read format: ...
wine: Unhandled illegal instruction at address 4002013B (thread 0130)
```

`0x4002013B` is `0x40020130 + 0xB`: **entry 34's own bridge, eleven bytes in.**
Box86's `onebridge_t` is packed and sixteen bytes:

```text
+0x0  CC            int3, the trap the emulator recognises
+0x1  'S' 'C'       signature
+0x3  wrapper       host function pointer
+0x7  f             the native function
+0xB  C3 / C2 N     the return
```

So execution entered the bridge somewhere other than its first byte, where the
trap is. Two mechanisms can do that and this capture does not yet separate them:

1. **A marker matched at the wrong address.** `getAlternate()` scans a 64-byte
   window from every branch and call target the dynarec translates and returns
   the bridge if the marker is anywhere in it. A jump into the middle of
   `wined3d_texture_load_location`, or a small function starting within 64 bytes
   before its marker, therefore also routes to entry 34 — and the first such
   address wins, because the id publishes the address it matched and refuses
   every other one afterwards. Section 3 of `MGS2_ISLAND_PRODUCTION_2026-08-16.md`
   is the precedent: nine of 37 markers sat up to +60 into their functions, which
   is why the window was widened to 64 in the first place. Widening it is also
   what makes this failure reachable.
2. **The emulator fell through the trap and decoded the bridge payload.** Bytes
   +0x3..+0xA are two host pointers; decoded as x86 they are arbitrary, and an
   undecodable byte at +0xB is exactly what would be reported.

Either way the fault is in **routing**, not in anything the native function's
body does with WineD3D state. Nothing here says native
`wined3d_texture_load_location` is semantically wrong; it says it is not being
entered as a function.

This is the same shape as the failure in section 17 of the frame-budget brief —
"an unhandled illegal instruction at a guest address that belongs to a Box86
bridge" — which turned out to be the x86 NOP marker compiled into the ARM
instruction stream and was fixed by patch 48. It is not the same cause: patch 48
is in every binary here, and 17 other entries are armed in the same process
without faulting.

## 4. The controls, run before the conclusion

```text
production, 17 entries, no candidate, no A/B
    reaches the attract-mode demo, 863 CPU ticks / 4 s, screenshot shows the
    demo rendering at 640x480. The base is healthy

entry 10 through launch-island-ab.sh, same base, same err+all, same GL_STATS
    runs, 2100+ frames, 18.5 fps in the stats line, nine completed A/B cycles.
    The launcher, the A/B gate, the guest-body path through RunFunctionFmt and
    the production base are all exonerated
```

The entry-10 control matters twice over: it is also the documented reproduction
from 16c, so the harness itself is known good in this session.

## 5. This route cannot measure either candidate

The nine entry-10 cycles, through the new reader:

```text
cycle  routed ms/f  unrouted ms/f     diff   routed calls  unrouted calls  bal
    1       12.296         81.417  -69.121            504             978  .
    2       16.675         16.654   +0.021           1005            1008  y
    3       16.938         25.016   -8.077          43047           53721  .
    4       21.651         21.409   +0.242          91431           92697  y
    5       23.551         21.766   +1.785         106782          108234  y
    6      102.354         20.182  +82.172         220796          101781  .
    7       55.588         57.027   -1.440         555129          598025  .
    8       60.395         61.024   -0.629         695951          607729  .
    9       72.783         83.093  -10.309         902978          933320  .

balanced (<=2%)   n=3   median +0.242   sd 0.96
```

Three balanced cycles, all in the low-load window where the frame time is 16-23
ms — the capped menu and early attract, not a scene that loads textures. The
heavy cycles are exactly the ones whose call counts diverge by 20-100%. So an
unattended attract-mode run produces no usable pairing, which is 16c's finding
about this route reproduced from the other direction: **the measurement needs the
owner's save and real gameplay**, about twenty minutes per entry.

The tick control passes: 2304 harness ticks against 2100 frames from
`MGS2_GL_STATS`, which reports in whole 300-frame blocks and therefore lags by up
to one block.

## 6. The patch record did not reproduce the production Box86

Found while establishing what "the current production base" even is.
`launch-play.sh` selects `box86-island32-prod` and
`device/FINAL_PRODUCTION.sha256` lists it, but no brief described it, and
`box86-patches/08-hotpage-budget.patch` recorded only one of the two changes in
the Box86 source tree. The second change makes `hotpage` and `hotpage_cnt`
`__thread`.

Which binary carries which is decidable from the ELF alone — two 4-byte globals
becoming thread-local grows the TLS image by sixteen bytes:

```text
box86-island31            .tbss 0x294   PT_TLS memsz 0x2bc   neither change
box86-island32-hotpage    .tbss 0x294   PT_TLS memsz 0x2bc   budget fix only
box86-island32-prod       .tbss 0x2a4   PT_TLS memsz 0x2cc   both   <- production
```

`box86-island31` and `box86-island32-hotpage` also still have `hotpage` as a
plain `OBJECT` in their symbol tables, at the same address in the same section.

The record is now two incremental patches, 08 (budget) and 09 (per-thread), each
applying with zero fuzz, and the pair reproduces the deployed `custommem.c`
exactly — checked by applying them to the pristine file and diffing. Both patches
say in their own text that **neither is measured**, in either direction, on frame
rate or on the open sync-arena freeze.

## 7. One instrument defect, found by it losing a capture

`harness/cs_deadlock_census.py` identified the CS thread by `comm == "wined3d_cs"`.
In this process every task is called `mgs2_sse_rg353v`, so the match failed,
`wchan` came back `None`, and the tool printed INDETERMINATE — "this process is
still making progress" — over a process that had consumed zero CPU for minutes
with a non-empty queue. The capture was only saved by reading the queue numbers
by hand.

Fixed: the summed CPU time of every task, read from `/proc` across the same
sample window, is now a second witness for "nothing is advancing", and the tool
names every task when the `comm` match misses. The counter-stability checks are
unchanged, so a busy process still reads INDETERMINATE. The new witness comes
from `/proc`, not from the census, which is the standing rule from 16c — a
control must not be computed through the mechanism it is controlling.

The signature this run produced now has its own verdict, C: nothing advances,
work published, `waiting_for_event` 0, no CPU anywhere — a consumer that stopped
inside command execution, with the armed island entry named as the first suspect.

## 8. What would settle the fault, and what blocks it

```text
run harness/island/full/island_marker_check.py against the mounted p56 DLL
    It checks exactly the three marker failures section 3 suspects: the same id
    in two different functions, a marker past the matcher's window, and the
    harmless duplicate inside one function. It needs an UNSTRIPPED p56, and the
    build tree no longer holds one -- the wined3d.dll there hashes
    fc9ae5aa... against the recorded unstripped p56 e0779dda...
    The i386 mingw toolchain is intact, so rebuilding p56 is bounded work

then check every armed id, not just 34
    Entries 22, 32 and 33 are in the production allow-list and have the same
    window exposure. The reason production is fine is currently empirical

then, if the marker is clean, instrument the bridge entry itself
    A one-shot log of the guest address that matched id 34 (the diagnostics
    build already prints it) separates mechanism 1 from mechanism 2 directly
```

Both remaining items in research's plan are blocked on the same missing thing.
The workstation has **no** `arm-linux-gnueabihf-gcc`, no
`arm-linux-gnueabihf-objdump` and no armhf sysroot (`sysroot32` is i386, for
Wine), and the device is aarch64 with no compiler. So Box86 and the island cannot
be rebuilt here, and `island_reach.py` / `island_gl_reach.py` cannot run at all —
both shell out to `arm-linux-gnueabihf-objdump`. The `box86-island32-*` binaries
were built in `/tmp/box86-hotpage-src`, which no longer exists.

The fail-closed GL preflight research asked for is also further from done than
16c section 4 implies. `island_gl_reach.py` can emit the per-entry required-slot
bitset, but **there is no consumer**: no `mgs2_entry_gl_need` or
`MGS2_GL_SLOT_WORDS` exists anywhere in the Box86 tree, so nothing can refuse to
arm. Its input is also gated — `MGS2 gl_ops: slot N unresolved` prints only under
`MGS2_ISLAND_DIAGNOSTICS`, which the production build compiles out.

## 9. What is NOT claimed

```text
not claimed   any frame-rate effect for entry 34 or entry 23, in either direction
not claimed   that native wined3d_texture_load_location is semantically wrong.
              The evidence says it is not being entered as a function
not claimed   that entry 23 shares the defect. It was never run: entry 34 came
              first and closed the session's device budget
not claimed   anything about box86-island32-prod's hot-page changes. They are
              deployed and unmeasured, which is now written down in two patches
not claimed   that the device reboot below was caused by the island
```

**The device rebooted itself once**, during the entry-10 control, and came back
after about five minutes with `up 0 min`. No crash record survives; ROCKNIX keeps
no persistent journal. It is not attributed. Two consequences worth keeping:
`/tmp` is tmpfs, so it took three logs with it — run logs now go to
`/storage/roms/ports/ablogs` — and `err+all` produced 7 MB in 95 s on a card with
1.3 GB free, so trim or delete after each run.

## 10. Artefacts

```text
docs/briefs/MGS2_ISLAND_ENTRY34_FAULT_2026-08-19.md   this document
harness/island_ab_read.py                  new: A/B cycle reader, the balanced
                                           filter, and a refusal when both arms
                                           record zero calls
harness/cs_deadlock_census.py              CPU witness, task table, verdict C
box86-patches/08-hotpage-budget.patch      rewritten, budget hunk only
box86-patches/09-hotpage-per-thread.patch  new, the __thread hunk
device/launch-island-ab.sh                 pinned to the played base
device/FINAL_PRODUCTION.sha256             launcher hash updated
```

Reproduce, on a device with the owner's save loaded:

```sh
cd /storage/roms/ports/MGS2-Substance
setsid nohup ./launch-island-ab.sh 34 > /storage/roms/ports/ablogs/ab34.log 2>&1 &
# fails within the first frames; without the gate the same set faults at
# bridge+0xB:
MGS2_BOX86_ISLAND_ONLY="0,1,2,3,4,5,6,9,10,14,18,19,22,28,29,32,33,34" \
MGS2_BOX86_ISLAND_FULL=1 MGS2_PLAY_WINEDEBUG=err+all ./launch-play.sh
# the working control, same everything, different entry:
./launch-island-ab.sh 10
python3 harness/island_ab_read.py <log> --all
```

---

# Second half: the cause, the fix, and two further defects

The armhf cross toolchain was reinstalled between the two halves
(`gcc-arm-linux-gnueabihf`, `binutils-arm-linux-gnueabihf`; the previous one had
lived in a deleted scratch directory, which is why `box86-island32-*` was not
reproducible). Everything below needed it.

## 11. What the fault actually was

Box86's `onebridge_t` is sixteen packed bytes: `CC` at +0 (the trap), `'S' 'C'`,
the wrapper pointer, the native function, and the return at +0xB. The dynarec's
0xCC case does `MOV32(xEIP, addr)` -- **addr is bridge+0xB -- before** calling
the wrapper (`dynarec_arm_00.c`). So while native ARM code runs, the emulated
guest EIP is parked on the bridge's `ret`, and any host fault inside that native
code is delivered to Wine as a guest exception **at that address**. The first
capture therefore looked like bridge corruption. It was not: box86 prints
`x86opcode=C3`, so the `ret` was intact all along.

`BOX86_SHOWSEGV=1` prints the host side even when the guest has a handler:

```text
SIGILL @0x7aeccdf0 ... (x86pc=0x4002013b) ...
  opcode=55 64 8B 0D 18 00 00 00     <- push ebp; mov ecx, fs:0x18   (i386!)
  x86opcode=C3 00 00 00 00 CC 53 43  <- the bridge's ret, intact
```

`0x7aeccdf0` is inside the **mounted** `opengl32.dll` (mapped 0x7aea0000, so RVA
0x2cdf0), in the unnamed thunk region -- the nearest export is `glFrustum`
+0xac0, and Wine builds extension entries as internal `wglGetProcAddress` thunks
that no export table names. Native ARM had called a guest x86 function pointer.

Two candidate mechanisms from section 3 were checked and **both refuted**:

```text
markers   entry 34's marker sits at +15 of its function, and the runtime matched
          the function START exactly: "MGS2 island: entry 34 matched 0x7b92c6c0",
          which is the .eh_frame FDE start for wined3d_texture_load_location.
          Its duplicate at +68 is outside the 64-byte window and never matches
layouts   every structure on the path is byte-identical between the shipping
          i386 build and the island's armhf build: wined3d_texture 292,
          wined3d_texture_sub_resource 52, wined3d_texture_gl 468,
          wined3d_context 1020, wined3d_context_gl 1684, wined3d_resource 168,
          wined3d_rendertarget_view 68, wined3d_state 7276, wined3d_gl_info
          13592 -- 472 structures over three translation units, zero differences
```

The layout check is only worth anything with a control that trips, so it has one:
the two structures the repository already documents as differing come back
differing -- `texture_stage_op` 16 against 12, `ffp_frag_settings` 132 against
100, both from MS bitfield rules that no ARM GCC option reproduces.

## 12. The cause: the translated table was barely used

Patch 53 translates a guest `wined3d_gl_info` once per device and hands it back
from `MGS2_GL_INFO()`. **`GL_EXTCALL(f)` went through that macro, and patch 55 had
converted a handful of sites by hand -- but only those.** Every other GL call
written as a plain member access read the guest table:

```text
utils.c        62      gl_info->gl_ops.gl.p_glFoo(...)
adapter_gl.c  219      (init code, x86 side -- see below)
context_gl.c   26
gl_compat.c    53      wined3d_context_gl_get_current()->gl_info->gl_ops...
texture_gl.c   25      <- entry 34's closure lives here
view.c          1
```

And `mgs2_island_gl_info()` translated only `gl_ops`: `translated = *guest`
copies the whole structure, so `fbo_ops`, `ffp_attrib_ops`, `p_glDisableWINE`,
`p_glEnableWINE` and `p_wglCreateContextAttribsARB` kept guest pointers too.

That is why the currently armed 17 entries are fine and entry 34 is not: none of
their closures makes a direct GL call, and `texture_gl.c` does.

## 13. Patch 61, and the fix verified against the shipping DLL

`wine-patches/61-island-gl-info-everywhere.patch`:

```text
utils.c     translate fbo_ops by name (21 slots, position is the name), then
            ffp_attrib_ops and the two glXxxWINE pointers through the class
            A/B/C ladder, and CLEAR p_wglCreateContextAttribsARB -- context
            creation stays x86-side, so a call through it must fail loudly
5 files     135 sites routed through MGS2_GL_INFO(): utils.c 62, context_gl.c 26,
            texture_gl.c 25, gl_compat.c 21, view.c 1
adapter_gl.c   deliberately untouched. Its 180 sites are adapter and extension
            table initialisation, x86-side, and several ASSIGN to gl_ops through
            token-pasting macros -- the const-returning accessor makes those a
            compile error, which is how they were found
```

`MGS2_GL_INFO(gi)` is `(gi)` in the i386 build, so the shipping DLL must be
unaffected. Checked, not assumed: all **32** wined3d translation units compiled
for i386 before and after, from the same source path so `__FILE__` cannot
differ. `.text`, `.rdata` and `.data` are byte-identical in every one. Four
objects differ in the file as a whole, in DWARF only, because the rewritten
expressions moved source columns.

On the device, with 18 entries armed and no A/B gate:

```text
before patch 61   wine: Unhandled illegal instruction at 4002013B
                  SIGILL @0x7aeccdf0, i386 bytes, in opengl32.dll
after  patch 61   wine: Unhandled page fault on read access to 00000000
                  SIGSEGV @(nil), for accessing (nil)
```

The illegal-instruction class is **gone**. What is left is the failure the design
asks for: a call through a GL slot that could not be resolved and was left NULL,
which faults at once instead of entering x86 bytes. Entry 34 still cannot be
armed -- but for a reason that is one line of log rather than a day of
archaeology.

Diagnostic binaries, on the device, not in production and not in `binaries/`:

```text
box86-island33-diag  f7cf2f031d3d8a49f82bdf328f6c49a241ed685629d3515b5ef86c93fc8cc5e5
                     island32-prod sources + MGS2_ISLAND_DIAGNOSTICS=1
box86-island34-diag  6d8ed745eca6fda04b2e5d6ee1a7b96dce798cd43c15b102d06003e0a93d8edb
                     plus the table half of patch 61 (fbo_ops et al) -- still faulted
box86-island35-diag  0eca106c1007b395781396831875001fd4ad0e46440416ab20b729a06dc60bdb
                     plus the 135 call sites -- SIGILL gone
```

None of the three may be used for a timing claim: `MGS2_ISLAND_DIAGNOSTICS=1`
adds counter increments on the dispatch path.

## 14. A production entry is bound to the wrong address

Found while checking markers, and independent of entry 34. Box86's
`getAlternate()` scans a 64-byte window from **every** branch and call target the
dynarec translates, and the first address whose window contains a marker is
published for that id forever (`matched != addr -> break`). The published
address does not have to be a function entry:

```text
entry 22 matched 0x7b919f23   ->  RVA 0x101b9f23, which is offset 0xe3 INSIDE the
                                  function 0x101b9e40..0x101b9f4d
id 22 marker at  RVA 0x101b9f59   in the NEXT function, 0x101b9f50..0x101b9f6d
```

So entry 22, `wined3d_rendertarget_view_invalidate_location`, **which is in the
production allow-list**, is bound to a mid-function address in the preceding
function, 54 bytes before its marker -- and its real entry point 0x101b9f50 can
never route, because the id is already taken. If that address is ever reached as
a call target, native ARM runs `rendertarget_view_invalidate_location` on the
wrong frame.

Production is stable, so either that block is never reached as a call target or
the effect happens to be benign. **Nothing here says it caused any observed
defect.** It is a live defect in the matching rule, not an explanation of
anything, and it is exactly the class `island_marker_check.py` was written for --
except that tool checks function starts, and this one is a mid-function address,
which it cannot see.

The static check over the mounted p56 DLL, using `.eh_frame` FDEs for function
boundaries (the DLL is stripped, so symbols were not available):

```text
41 marker occurrences, 39 distinct ids
1 marker past the 64-byte window   id 34's duplicate at +68 -- harmless, and it
                                   is why id 34 appears twice
5 markers reachable from ANOTHER function's entry   ids 17, 24, 27, 35, 51
                                   none of them is in the production allow-list
```

**The fix is not a wider or narrower window.** The class-B generator already
knows every mappable function's guest RVA, and the resolver already establishes
the module base with two independent witnesses. Box86 should therefore require
`addr == base + rva(id)` and stop scanning windows at all. That removes the whole
mis-match class -- adjacent functions, mid-function targets and duplicated
markers together -- rather than trading one for another.

## 15. The fail-closed preflight now runs, and it would disarm a measured win

With the toolchain back, `island_gl_reach.py` completes in **25 seconds**, not
the 45 minutes at which it was abandoned on 2026-08-16, and its control check
passes. Fed the 271 unresolved slots this session's diagnostic run reported:

```text
entry 34  wined3d_texture_load_location            closure 336, needs 86 slots
entry 23  wined3d_rendertarget_view_load_location  closure 346, needs 86 slots
          8 unresolved in both: p_wglGetPixelFormat, p_glBegin, p_glDrawBuffer,
          p_glEnd, p_glGetTexImage, p_glTexSubImage1D, p_wglSetPixelFormatWINE,
          p_glBufferStorage                        -> DO NOT ARM

entry 10  wined3d_buffer_load                      closure 44, needs 5 slots
          1 unresolved: p_glBufferStorage          -> DO NOT ARM
```

Entry 10 is **production**, is the measured -8.87 ms/frame win, and has run for
days without touching that slot. So the guard as specified would refuse the one
entry we have a number for. That is the tool's own limit 3 -- a slot referenced
on a branch that never executes still counts -- and it is not a bug in the tool;
it is a reason the verdict cannot be wired straight into arming.

What the guard needs is the second half of the condition WineD3D itself uses:
these legacy and desktop-only entries (`glBegin`, `glEnd`, `glGetTexImage`,
`glTexSubImage1D`, `glBufferStorage`) sit behind `gl_info->supported[...]` tests,
and on this GLES driver those extensions are absent, so the branches are dead.
A required-slot bitset ANDed with "the driver reports this extension supported"
would refuse entry 34 and pass entry 10 -- but that mapping has to be built and
checked before anything is armed on it, not asserted here.

Meanwhile the preflight is usable as an advisory today, and the generated header
exists:

```sh
python3 harness/island/full/island_gl_reach.py <unstripped box86 with the island> \
    --resolved <log with 'gl_ops: slot N unresolved'> --entry 34 --entry 23 \
    --out mgs2_entry_gl_need.h
```

## 16. What to do next, in order

```text
1  name the NULL slot entry 34 actually calls. One generated ARM stub per
   gl_ops slot -- `mov r0, #N; b trap` is 8 bytes, 3114 of them is 25 KB --
   installed instead of NULL, turns the SIGSEGV into "island called unresolved
   GL slot N (name)". Without it we are guessing which of the 8 it is
2  fix the matcher to require addr == base + rva(id) (section 14), which also
   un-breaks production entry 22
3  then decide the arming guard: required-slots AND driver-supported (section 15)
4  only then try entry 23, and only then a coarse cs_exec_draw_one
```

Entry 23 was never run. Its marker placement is clean and its closure is the
same shape as entry 34's, including the same 8 unresolved slots, so it is likely
to fail the same way -- which is a reason to do step 1 before spending device
time on it.

## 17. Artefacts, second half

```text
wine-patches/61-island-gl-info-everywhere.patch   the fix, with its verification
harness/island_ab_read.py                         A/B reader (first half)
harness/cs_deadlock_census.py                     CPU witness + verdict C
box86-patches/08, 09                              the production Box86 record
../recovered-session/wine-11.0/dlls/wined3d/      utils.c, texture_gl.c,
                                                  context_gl.c, gl_compat.c,
                                                  view.c carry patch 61
../box86-src/build-diag/                          diagnostics build tree,
                                                  MGS2_ISLAND_DIAGNOSTICS=1
/storage/roms/ports/abrun.sh                      device-side start/stop/status
/storage/roms/ports/ablogs/                       run logs, on persistent storage
```

---

# Third pass: the trap, canonical identity, and two more layers peeled

Research reviewed the second half and asked for two things before any further
device time: a `movw`-based unresolved-slot trap table, and identity by canonical
RVA rather than by marker window. Both are done, both are verified on the device,
and the trap answered its question on the first run.

## 18. The trap, and what it named

`box86-patches/10-island-identity-and-gl-trap.patch`. One 8-byte ARM stub per
slot, `movw r0, #N; b mgs2_unresolved_gl_trap`, 4096 of them for 32 KB, installed
in place of NULL in diagnostic builds only.

`movw` rather than `mov` is not a detail: the ARM data-processing immediate is an
8-bit value rotated by an even amount, so 3113 is not encodable and a plain `mov`
would either be refused or grow the stub and break `base + 8 * slot`. Verified in
the linked binary:

```text
slot     0 @ 0x628afa64: movw r0, #0    ; b 628b9abc <mgs2_unresolved_gl_trap>
slot  3113 @ 0x628b5bac: movw r0, #3113 ; b 628b9abc
slot  4095 @ 0x628b7a5c: movw r0, #4095 ; b 628b9abc
```

The handler also names the CALLER: the stub arrives with `b`, not `bl`, so LR
still holds the island caller's return address and `__builtin_return_address(0)`
is exactly it. First run:

```text
MGS2 island: called UNRESOLVED GL slot 90 (glDrawBuffer) from 0x62b61525
```

0x62b61525 resolves in the unstripped build to
`wined3d_context_gl_apply_fbo_state+0x2a0` -- the inlined
`wined3d_context_gl_set_draw_buffer(context_gl, GL_NONE)` on the FBO attach path,
which the source comments as being there "to satisfy pedantic pre-ES2_compatibility
GL contexts requirements".

**No guessing among the eight candidates was needed, and the guess would have been
wrong**: the eight were `glBegin`, `glEnd`, `glDrawBuffer`, `glGetTexImage`,
`glTexSubImage1D`, `glBufferStorage` and two wgl entries, and the reachable one is
not the one a reader would bet on.

## 19. glDrawBuffer does not exist on this stack, so the island implements it

Checked on the device rather than assumed:

```text
libmali-bifrost-g52-g29p1.so   glDrawBuffers  yes (FUNC GLOBAL)
                               glReadBuffer   yes
                               glDrawBuffer   ABSENT
win32u (Wine's GLES path)      no USE_GL_FUNC(glDrawBuffer), so the unix half of
                               the guest's own slot is not filled either
```

So this is not a resolution that was missed; the scalar entry point is nowhere.
`wine-patches/62-island-gl-slot-trap-and-drawbuffer.patch` therefore has the
island implement it as `glDrawBuffers(1, &buffer)` -- which is the documented GLES
equivalent and, more usefully, **the mapping this tree already applies for the
same reason** in `wined3d_context_gl_apply_draw_buffers()`. It is installed only
when `glDrawBuffers` itself resolved, and it is reported as a substitution rather
than a resolution:

```text
MGS2 island: GL slot 90 (glDrawBuffer) substituted natively: glDrawBuffers(1, &buffer)
```

No no-op and no faked success anywhere near it: an unimplementable call still has
to fail.

**A correction to how this was first written.** The first version put the mapping
at the call site in `context_gl.c`, and its comment shifted every later
`checkGLcall()` line number, so the guest `.text` changed in the `__LINE__`
immediates. Harmless, and still wrong to accept: it would have spent the
"island-only patches leave the shipping DLL byte-identical" invariant on nothing.
Moved into the trailing `#ifdef MGS2_ISLAND_ARM` block of `utils.c`, after which
the guest `utils.o` is byte-identical as a whole object, DWARF included.

**Left open, and stated rather than resolved:** whether the guest ever executes
that line. If it does it would call through a null unix pointer, which production
demonstrably does not do, so either the early return above it always fires or
something outside this tree fills the pointer. A memory-only counter on the guest
side settles it; nothing here depends on the answer.

## 20. Identity is now the canonical offset, and production entry 22 is fixed

The rule Box86 used -- "the first address whose 64-byte window contains a marker
IS that entry" -- is replaced by:

```text
identity   the address at which this id's marker sits at ITS canonical offset
witness 1  the marker bytes themselves, unchanged
witness 2  addr == module_base + canonical RVA, checked once the class-B resolver
           has established the base from two independently agreeing RVAs
```

Both canonical values come from `harness/island/full/gen_entry_identity.py`,
which reads the MOUNTED DLL: markers by byte pattern, function boundaries from
`.eh_frame` FDEs because the shipped DLL is stripped. 39 ids, every marker offset
inside the window, and the two duplicate markers (ids 11 and 34) reported rather
than silently picked from.

Witness 2 is skipped while the base is unknown instead of failing, because entries
are matched at translation time, which can precede the first class-B dispatch.
That is why the offset carries the decision and the base only confirms it -- an
"exact RVA only" rule would have refused to arm anything at all.

Measured effect on the device, with the same 18 entries armed:

```text
before   MGS2 island: entry 22 matched 0x7b919f23   (mid-function, wrong function)
after    MGS2 island: entry 22 matched 0x7b919f50   (its own function start)
```

An id with no canonical identity is not armed at all.

## 21. Where entry 34 stops now

With the GL layer fixed, entry 34 reaches DirectMusic startup -- much further than
before -- and then hits the next layer:

```text
SIGILL @0x7b77d624   opcode=56 53 83 EC 10 8B 45 28   (i386: push esi; push ebx; ...)
```

0x7b77d624 is guest wined3d RVA 0x1d624, and the class-B table names it exactly:
`convert_b8g8r8a8_unorm_gles` at RVA 0x1d620, id 159, entered 4 bytes in. So the
island called a GUEST WineD3D function through a pointer that no instrumented
dispatch site covers -- the format-converter pointer in the texture upload path.

This is the same shape as the GL problem and has the same fix: the pointer has to
go through `mgs2_island_dispatch()`, which already resolves class A, B and C. It
is a WineD3D-internal target, so class B maps it by name; the table already has
it, with an id. Nothing new is needed except routing that call site.

Note what this says about the overall direction: each layer peeled so far has
been an unrouted pointer, not a semantic incompatibility, and each one has been
named exactly by an instrument rather than guessed. The remaining work looks like
the same kind again.

## 22. What is next, unchanged in order

```text
1  route the format-converter call sites through mgs2_island_dispatch()
   (section 21). Same mechanism as patch 61, WineD3D-internal instead of GL
2  re-run entry 34 until it reaches gameplay with no fault
3  only then measure it, on the owner's save, with the ABBA harness
4  then entry 23, whose closure is the same shape
5  then the runtime-aware GL preflight (section 15), which still cannot be wired
   into arming as it stands: it refuses entry 10, which is measured production
6  then coarse cs_exec_draw_one
```

Diagnostic binaries added this pass, on the device, not production:

```text
box86-island36-diag  6f566df7f786f1503b495aed645b2d8758433be73e38230846a9827d38ed3748
                     trap table + canonical identity
box86-island37-diag  fba9899d7aa33765...  trap also names its caller
box86-island38-diag  82a3930df8029845...  plus the glDrawBuffer substitution
```

## 23. Artefacts, third pass

```text
box86-patches/10-island-identity-and-gl-trap.patch    identity + trap table
wine-patches/62-island-gl-slot-trap-and-drawbuffer.patch   island side
harness/island/full/gen_entry_identity.py             canonical identity generator
```

---

# Fourth pass: entry 34 runs

## 24. The audit, and what it found before the next launch

Research's instruction was to fix the converter through the existing dispatcher and
then audit the whole closure statically, so the next launch is not another
one-pointer-at-a-time round. `harness/island/full/island_icall_audit.py` does that:
for one entry's closure it lists every call through a function-pointer FIELD --
field names taken from the module's own headers -- and splits routed from unrouted.

```text
entry 34   closure 432 functions, 117 known field names
           UNROUTED indirect calls  47
             real calls             39
             pointer tests / declarations  8
```

**Two of the audit's own bugs were caught by its control check before any of its
output was believed**, which is the only reason the numbers above mean anything:

```text
__attribute__((noinline)) was taken for a function definition, and then swallowed
the real definition below it -- which hid wined3d_texture_load_location itself,
the whole point of the audit
the member-call pattern required `->name(`, which never matches a site already
wrapped as MGS2_P50_CALL(site, x->name)(...) -- so both the routed sites and every
ops target behind them were invisible, and the closure came back as 14 functions
```

The first version printed "UNROUTED: 0" and a control-check FAIL. Without that
check it would have read as "nothing left to fix".

Among the 39 was `format->decompress` -- the third member of the
upload/download/decompress triple, one line away from the converter the device
fault had named, and it would have cost another launch to find.

## 25. Patch 63, and entry 34 running

`wine-patches/63-island-route-indirect-calls.patch` routes all 39 through the
existing `MGS2_P50_CALL()`, one site id per family (7 new ids, declared at the END
of `wined3d_private.h` so no `assert()` line number in the shipping DLL moves; no
call site gained a line either). Fail-closed is inherited: `mgs2_island_dispatch()`
aborts on an unmappable pointer in every build.

Guest build unaffected, verified the same way as patch 61: all 32 TUs compiled for
i386 before and after from the same path, `.text`/`.rdata`/`.data` byte-identical
in every one; 11 objects differ in DWARF only.

On the device, entry 34 armed with the production DLL pair:

```text
box86-island40-diag   4200+ frames: the whole attract demo, its death, and the
                      MISSION FAILED menu, with a screenshot showing correct
                      rendering. Zero island faults, zero traps, zero unresolved
                      dispatches. The only SIGSEGV lines are the 13 that
                      production shows too
box86-island41        the same with MGS2_ISLAND_DIAGNOSTICS OFF -- timing-capable,
                      no dispatch counters, no trap installation: 1800 frames,
                      18 entries armed, no faults
                      02294e0fc53298e9fc02c50ff5a5aa10392e44e78619358359fb6a172d104b71
```

**Entry 34 is therefore armed, native, and stable for the first time.** Nothing is
claimed about frame rate: attract mode cannot measure it, as section 5 established
with its own numbers.

## 26. The shape of what was actually wrong

Four walls, one kind of defect:

```text
identity      the marker window bound an entry to a mid-function address
GL pointers   the translated gl_info was consulted at a minority of call sites
GL function   glDrawBuffer exists nowhere on this stack; the island implements it
callbacks     39 WineD3D function-pointer fields called as guest addresses
```

Not one of them was "this WineD3D function cannot run natively on ARM". That does
not promise frame rate, and it does not promise that `cs_exec_draw_one` will work.
It does remove the argument that the coarse native renderer is blocked by
something structural: the blockers found so far are all routing, all fixable, and
each was located by an instrument rather than guessed.

## 27. Next, and the line not to cross

```text
1  MEASURE entry 34 on the owner's save with device/launch-island-ab.sh 34,
   ~20 minutes, box86-island41 (diagnostics off). Read it with
   harness/island_ab_read.py; the balanced-cycle filter and the zero-call refusal
   are already in it
2  only then entry 23, whose closure is the same shape and whose 8 unresolved
   slots are the same 8
3  then the runtime-aware GL preflight, which still cannot be wired into arming as
   it stands: it refuses entry 10, which is measured production (section 15)
4  then coarse cs_exec_draw_one
```

Nothing else gets widened before that measurement.

---

# Fifth pass: the gameplay smoke passes, the A/B harness does not

## 28. Entry 34 survives a real reinforcement fight

Owner at the console, `box86-island41` (diagnostics off, timing-capable),
production DLL pair, 18 entries armed including 34, no A/B:

```text
loaded the target save, reached the reinforcements, fought and won them
zero island faults, zero traps, zero unresolved dispatches
screenshot after the fight: textures, decals, shadows, radar and HUD all correct
CPU pinned at 1992000 throughout, 76.2 C after play
```

This is the smoke the promotion decision needs, and entry 34 passes it. It is not
a frame-rate result and no number is taken from it: the scene is not fixed and
there is no control arm.

One instrument mistake, mine: this run was launched WITHOUT
`MGS2_PLAY_WINEDEBUG=err+all`, and `MGS2_GL_STATS` prints through `ERR`, so the
launcher's own frame counter is absent from the log -- the same trap already
written down in section 10 of this brief. Box86's island lines are unaffected
(`printf_log`, not WINEDEBUG), so the zero-fault reading stands; the missing fps
lines would have been unusable anyway.

## 29. The ABBA harness deadlocks on entry 34's UNROUTED arm

`launch-island-ab.sh 34` with the same binary stalls on the first frame. The
capture (`ablogs/ab34-stall-capture.log`, `ablogs/ab34-stall-census.txt`):

```text
VERDICT C: nothing advances, the DEFAULT queue holds published work, and
waiting_for_event is 0 ... It stopped somewhere inside command execution.

DEFAULT head 0x728 tail 0x19c   NOT EMPTY      waiting_for_event 0
process CPU over the window: 0 ticks   (no task ran at all)
all four Wine threads in ntsync_schedule / do_sys_poll
zero faults, zero traps, zero unresolved dispatches
```

The routed arm of the same entry, in the same binary, runs 4200 frames and a live
fight. So the fault is in the arm that does NOT route: `mgs2_island_w_ab34_uFpupu`
calls the guest body through `RunFunctionFmt(guest, "pupu", a, b, c, d)`.

Note what this is NOT: not the pre-patch-61 SIGILL (no faults at all now), and not
the open Box86 sync-arena freeze (that one is a futex wait; every thread here is in
ntsync, waiting on NT objects).

Entries 4, 10 and 23 use the same `RunFunctionFmt` mechanism and entry 10 produced
30 usable cycles with it. The one structural difference is that **entry 34 returns
a value** and the other three are `void`. That is a suspicion, not a diagnosis --
all four threads waiting in ntsync with published work pending would also fit the
CS thread waiting on itself, which is what `wined3d_from_cs()` mis-identification
looks like. It needs an instrumented run, and it is cheap to iterate on because it
reproduces within the first frames every time.

**Consequence: entry 34 cannot be measured with the paired harness until this is
fixed.** Two separate playthroughs are not an alternative -- that is exactly the
method that resolved nothing for entry 10, where the within-configuration spread
was 2.4 fps against a 1-2 fps effect.

## 30. Next

```text
1  instrument the unrouted arm (entry/exit log, first N calls, diagnostics build)
   and find what the CS thread waits on. Reproduces in the first frames, so a
   build-and-attract-run cycle is a couple of minutes
2  then the paired measurement of entry 34, owner's save, ~20 minutes
3  entry 23 only after that
```

Not to be done before that measurement: widening the island further, or promoting
entry 34 on the smoke alone. The smoke says it is correct, not that it is worth
anything.

---

# Sixth pass: entry 23 measured, entry 34 still not measurable

## 31. Entry 23 measured: a robust positive direction, about -2 to -2.6 ms/frame

Entry 34's A/B arm deadlocks (section 29), but entry 23's does not, so entry 23 --
the second of the two roots research asked for -- was measured instead, with the
owner playing the target save across two continuous stretches in ONE process.
`box86-island41`, diagnostics OFF, 18 entries armed, mounted binary verified
byte-identical to the timing build, CPU pinned 1992000, 82.2 C at the end,
**zero faults, traps or unresolved dispatches**.

42 cycles, 25 of them call-count balanced within 2%:

```text
balanced (n=25)    median -1.944   mean -2.614   sd 2.48   se 0.50   ms/frame
all cycles (n=42)  median -1.974   mean -5.991   sd 17.82  se 2.75   ms/frame
filter moved the median by +0.030 ms/frame -- the balance filter is NOT doing the
work; the unfiltered median says the same thing
sign               24 of 25 balanced cycles favour routed
arms               routed 37.2 ms/f = 26.8 fps, unrouted 39.9 ms/f = 25.1 fps
tick control       10752 harness ticks against 10500 launcher frames (102.4%),
                   inside one 300-frame block -- passes
```

So routing `wined3d_rendertarget_view_load_location` natively is worth **about
2 to 2.6 ms/frame in this scene**, roughly twice entry 4's win and a quarter of
entry 10's.

**Two corrections to the first version of this section, both from research's
review and both accepted:**

1. **The significance was overstated and is withdrawn.** Twenty of the 25 balanced
   cycles (17-36) come from ONE deterministic stretch with identical call counts.
   Those are not independent trials, so the sign test over 25 "cycles"
   (p ~ 1.6e-6) and the "effect / se = 3.9 sigma" both flatter the result. Neither
   number should be quoted again. What survives is direction and magnitude: 24 of
   25 balanced cycles favour routed, the five balanced cycles from moving play
   agree in sign and range, and four of the six heaviest unbalanced cycles agree.
2. **The fps figure came from the mean, not the median.** Against a 39.9 ms/frame
   baseline, the median -1.944 ms is 25.1 -> 26.35 fps = +1.3 fps, while the mean
   -2.614 ms is 25.1 -> 26.8 fps = +1.76 fps. The +1.76 above is the mean's, and
   the two should not be presented as one number.

**The one caveat that matters, stated rather than buried.** Twenty of the 25
balanced cycles (17-36) carry *identical* call counts -- 191,072 in both arms,
1706 calls/frame -- which means the game sat in a deterministic state for that
stretch rather than in moving combat. That is the cleanest pairing this harness can
get, and per rule 3 a fixed spot is exactly what an A/B wants; it is also not
active gameplay, so the effect could differ under load. Two things reduce that
worry: the five balanced cycles from moving play (2, 5, 9, 12, 14) sit in the same
direction and range, and among the six heaviest cycles (37-42, 68-84 ms/frame,
call counts too divergent to be balanced) four of six also favour routed. Nothing
here needs the static stretch to carry the sign.

Entry 23 also got its first gameplay exposure in this session -- a live fight on
the owner's save with no fault of any kind. That is the smoke for 23, obtained
free with the measurement.

## 32. What is now decidable, and what is not

```text
measured          entry 23: robust positive direction, about -2 to -2.6 ms/frame
                  in this scene; do not quote a sigma or sign-test p (section 31)
smoke-passed      entry 34: native, a whole reinforcement fight, zero faults --
                  but UNMEASURED, because its A/B arm deadlocks
fixed on the way  production entry 22 was bound to a mid-function address in the
                  preceding function; canonical identity (box86 patch 10) fixes it
not decidable yet whether the island41 stack should become production: that is one
                  decision covering patches 61-63 and box86 patch 10 together, and
                  it is the owner's call, not a number's
```

## 33. Revised next decision: profile current island41 before widening it

Section 30 is superseded as a priority order. The entry-34 guest fallback is a
real harness defect, but repairing it can only make a single-entry A/B possible;
it cannot improve the routed game. The old renderer frame budget is also retired:
its 22.0 ms libmali plus 20.4 ms present reading cannot be a floor when the current
route has already shown 37.2 ms/frame.

The next experiment is therefore exactly one fresh, production-like profile of
`box86-island41`, diagnostics off, on the owner's heavy reinforcement save. It
answers the decision that the older profile cannot: how much current `wined3d_cs`
time remains translated guest WineD3D, versus native ARM (including libmali), and
which 15 guest blocks still carry it.

```text
launch             MGS2_BOX86_GUEST_MAP=1, MGS2_BOX86_BIN=box86-island41,
                   normal production DLL pair, diagnostics off
capture            45 s of the one live wined3d_cs thread at a stable heavy spot
recorder           Box86 bounded guest map; snapshot only after perf stops
outputs            perf.data, perf.script, /proc/Tgid/maps, guest-map.bin,
                   live Box86 path and SHA-256
reader             harness/island41_profile_read.sh <capture-directory>
validity           one instance; guest-map overflow=0; wined3d_cs only;
                   fixed 1992 MHz and the played route recorded alongside it
```

`harness/island41_profile_capture.sh` makes that capture without Wine/game
instrumentation or hot-thread logging. `box86_cycle_profile.py` reports the
cycle-weighted DSO split as well as resolved guest blocks; it accepts both the
handheld's `comm tid` and perf's `comm pid/tid` presentation.

**Decision rule, set before seeing the number.** If translated WineD3D is only
roughly 2--3 ms/frame, do not start a coarse native CS project: the emulation
margin is already too small. If it is materially larger (roughly 8--12+ ms/frame),
the next implementation experiment is one generic CS-handler boundary with only
the post-batching DRAW handler routed first. The x86 CS queue, waits and thread
lifecycle stay x86; PRESENT, callbacks, map/unmap, stop and command-list paths do
not enter the first allow-list. Only a correct smoke followed by same-process A/B
of DRAW can justify widening to further profiled handlers.

This does not promote island41 and it does not claim an entry-34 frame-rate
effect. The existing production pair remains the rollback while the profile and
the DRAW-boundary experiment are researched.

## 34. Fresh island41 heavy-scene profile: translated WineD3D remains material

On 2026-08-19 the owner brought the running game to the heavy reinforcement
scene and one external capture was taken from the live `wined3d_cs` thread. This
is the measurement section 33 prescribed, not an A/B and not a Wine build.

```text
runtime            box86-island41, SHA-256 02294e0fc53298e9fc02c50ff5a5aa10392e44e78619358359fb6a172d104b71
mounted binaries   box86-island41 and wined3d_p56_batch_state.dll both cmp-identical
CPU                policy0 performance, current=max=1992000 kHz at validation
capture            perf cycles:u, 36,426 samples, one wined3d_cs tid 121700
guest map          16,487 / 262,144 records, overflow=0
resolved JIT       15,244 samples, unresolved=0
artefacts          logs/rg353vs/island41-profile-20260819-171556/
```

Cycle-weighted shares of all samples from that one thread:

```text
42.48%  native /usr/lib32/libmali.so.1.10.0
41.76%  Box86 JIT map
 9.28%  native libc
 6.38%  Box86 runtime

26.47%  resolved guest wined3d.dll          (a subset of the 41.76% JIT share)
 3.51%  guest opengl32.so
 2.55%  guest opengl32.dll
```

The leading resolved WineD3D block is RVA `0x59e20`, 5.424% of all user cycles
(1,968 samples). Its configured-build source location is `draw_primitive()` in
`context_gl.c`; the following hot blocks include GLSL raw-structured load,
buffer-map unlock, GL-context selection, texture dirty-region processing and
shader allocation. Thus the current profile confirms the architecture decision:
there is still much more than a 2--3 ms-equivalent sliver of translated renderer
work, while libmali is independently large and cannot be removed by translating
WineD3D.

Do **not** convert the 26.47% CPU-cycle share directly into ms/frame. The
launcher's adjacent 300-frame windows ranged from 13.6 to 19.0 fps and were not
timestamp-correlated with the perf interval. The valid conclusion is qualitative
but decisive: a DRAW-first CS-handler bridge is justified; more isolated roots
are not the highest-ROI next experiment.

## 35. Native CS DRAW runs; the claimed gameplay magnitude is withdrawn

The experiment prescribed above is now complete.  It did not move
`wined3d_cs_run`, the queue, waits, packet lifetime or PRESENT into ARM.  Both
`WINED3D_CS_OP_DRAW` forms converge on one new global entry, ID 37,
`mgs2_cs_exec_draw_one_island()`, immediately after batch decoding; that shim
calls the existing static `wined3d_cs_exec_draw_one()`.  Thus the tested cut is
exactly the post-batching DRAW closure, not a whole-thread port.

**Refutation rule set before the run.**  Reject this boundary if the closure
could not smoke cleanly, if DRAW did not materially leave guest execution, or if
same-process A/B became small after measuring the high-frequency guest re-entry
cost.  The implementation/smoke part passed.  The gameplay-performance part is
not answered, because the measured stable windows were not correlated with the
scene transition described below.

Making the closure native exposed two boundary defects rather than game defects:

* four still-unrouted backend/state callback families needed class-B sites 32--35,
  including `context_apply_state()` and the two multistate callback arrays;
* the separable-shader local GL cache used `wglGetProcAddress()` from ARM and
  cached the returned **guest x86** `glBindProgramPipeline` pointer.  Under
  `MGS2_ISLAND_ARM`, `mgs2_get_gl_func()` now resolves only through the island's
  translated native GL table.  `wglGetPixelFormat`, `glPolygonMode` and the GLES
  `glDrawBuffer -> glDrawBuffers(1, &buffer)` compatibility path keep their exact
  already-proven substitutions.

After those fixes the diagnostic build ran beyond 3,600 frames and the timing
build beyond 3,000 frames with entry 37 matched, 1,612 class-B IDs, correct
rendering and no island fault, SIGILL or abort.  During the user-driven run, four
consecutive balanced cycles had exactly 112,672 DRAW calls in each arm
(1,006 calls/frame):

```text
cycle   routed ms/f   unrouted ms/f   routed-unrouted
108        36.458          97.959            -61.501
109        36.459          97.969            -61.510
110        36.608          98.562            -61.953
111        36.310          98.401            -62.090
median     36.459          98.185            -61.732
```

**Correction after the run, from the owner.**  Gameplay became extremely slow
and was followed by the death / MISSION FAILED screen.  The A/B log contains no
semantic scene marker, and the original entry-37 remote log was not retained.
The perfectly repeated call counts are therefore not proof of a fixed heavy
gameplay frame; they may be the later death screen.  The `36.459`, `98.185` and
`-61.732 ms/frame` rows must not be quoted as combat/gameplay performance or as
grounds for promotion.  This retracts the first wording of this section.

Independently, the `-61.732` is **not** the native-body delta by itself.  The unrouted A/B arm
uses `RunFunctionFmt()` once per DRAW while the normal guest path does not, so it
contains both the real guest work and a high-frequency measurement trampoline.
These four exact lines are retained only as measurements of an unidentified
deterministic state, not silently relabelled as the requested heavy scene.

Entry 38 was therefore built as an empty function with the exact entry-37 ABI
and called once beside every DRAW.  With real DRAW left guest in both arms, seven
consecutive stable cycles 18--24 had exactly 128,912 calls per arm:

```text
-1.880  -3.285  -4.086  -2.850  -4.562  -4.452  -3.072 ms/frame
median -3.285 ms/frame at 1,151 calls/frame = 2.854 us per re-entry
```

Scaling that measured per-call cost to 1,006 calls/frame gives `-2.871 ms/frame`
for the trampoline component of the raw DRAW A/B.  For the unidentified state
only, the arithmetic is:

```text
raw entry-37 median                         -61.732 ms/frame
entry-38 re-entry component at 1006 calls   -2.871 ms/frame
native DRAW body minus direct guest body    -58.860 ms/frame

estimated direct-guest arm                  95.314 ms/frame = 10.49 fps
native DRAW arm                              36.459 ms/frame = 27.43 fps
```

These rows are derived estimates, not separately observed arms: the
calibrator was recorded later at 1,151 rather than 1,006 calls/frame, and assumes
the empty `RunFunctionFmt()` cost scales linearly with call count.  They do show
that the re-entry trampoline was a small part of that unidentified state's raw
delta.  They do **not** establish a gameplay FPS gain, because arithmetic cannot
repair missing scene attribution.  No sigma, p-value or promotion claim is made.

The calibration-only entry 38 was then removed.  The clean entry-37 pair rebuilt
with 1,611 class-B IDs and passed a fresh diagnostic A/B smoke.  In the stable
light section, cycles 4--7 had nearly equal call counts; routed was display-capped
at 16.66 ms/frame while unrouted was 28.19--28.86 ms/frame, with no fault.  Those
cap-limited values are a smoke observation, not a second magnitude measurement.

```text
raw timing Box86 (island42)       e486add49999b902759f673785f485080553ae9083b78f9ed6ef34bb55003850
raw DRAW guest DLL p64            e6e21882e7ce48d7397dec66c9c430fff39cbc3a55e3fc90522b3e28c492a718
calibration timing Box86 p65      b34a987ebfb88c6109cff582aa9047018cb22a7a4acaf0aeded644ddf67f7e14
calibration guest DLL p65         3628a235274c94b19e36685bf6f114a9ab8f24cafbb61fb6fa208d1cf933be87
clean timing Box86 p66            886f31378aba707a8aca5d22596421bb0283f2ec48802ad1551af39a672392c6
clean diagnostic Box86 p66        ff8deaf2f777a4b6ed08b8fdd837584fc6cf43448025931364fe5038e27bcfb9
clean guest DLL p66               d63057cb05c3d3d3e17911c04ea585ce3d02976b6e8870fd27dd7eed83b5aa41
```

Calibration and clean-smoke artefacts are in
`logs/rg353vs/cs-draw-calibration-20260820/`.  All candidates remain under
separate device filenames.  Production launch defaults are unchanged.  The next
valid gate is a continuous, A/B-disabled, always-routed p66 playtest on the
owner's save, followed only if correct by a newly timestamp-correlated gameplay
A/B that is stopped before death.  Until then p66 is research, not a promotion
candidate.

## 36. Clean always-routed p66 playtest: sound, PRESENT, black picture

The required correctness gate was run immediately, without A/B or the
calibration entry.  It is a decisive negative result:

```text
process             one mgs2_sse_rg353v
CPU                 fixed 1992000 kHz
Box86               box86-island44-draw-clean, cmp-identical, SHA-256 886f3137...
WineD3D             wined3d_p66_cs_draw_clean.dll, mounted target cmp-identical,
                    SHA-256 d63057cb...
allow-list          production 17 entries plus entry 37, always routed
A/B / entry 38      absent
owner observation   sound works; no picture
runtime             alive, no island fault, SIGILL, SIGSEGV or abort
PRESENT             repeated 300-frame windows at 58.0--60.2 fps
readback             about 0.84--1.15 ms/frame
```

This is not a presenter freeze: frames continue to be presented and read back,
but their contents are not the game image.  The display-capped routed windows in
the earlier smoke, and the fast routed arm in the A/B, therefore cannot be
interpreted as renderer acceleration.  They are consistent with entry 37
skipping or corrupting rendering work.  The `-58.860 ms/frame` arithmetic is
withdrawn as an optimisation result, not merely as a scene-labelled result.

**Decision:** the generic post-batching DRAW closure as implemented in p66 is
rejected for production.  Production was never changed and the failed process
was stopped.  If this boundary is revisited, the next instrument is correctness
only: the existing memory-only source/final GL-submission census plus a bounded
frame-content witness, comparing guest and routed execution before any FPS A/B.
Do not time entry 37 again until it produces the same picture.

The complete standalone record of this experiment is
`docs/briefs/MGS2_NATIVE_CS_DRAW_BLACK_FRAME_2026-08-20.md`.

## 37. Entry 23 promoted as FINALPLAY7

After p66 was rejected and the previous picture-producing production stack was
restored, research changed the priority: take the already measured entry 23
before doing more DRAW work. The production candidate was deliberately narrow:

```text
Box86       box86-island41
WineD3D     wined3d_p56_batch_state.dll
allow-list  previous 17 entries + 23
excluded    entry 34, entry 37, every A/B variable
CPU         performance, current=max=1992000 kHz
```

Both live mount targets were `cmp`-identical to their named files. One process
ran 21 complete 300-frame PRESENT windows, 6300 frames total. Class-B armed with
1616 mappable functions, the log contained zero `SIGILL`, `SIGSEGV`, unhandled
exceptions, island faults, unresolved GL traps or dispatch aborts, and the owner
reported normal play and correct picture: "все гуд". The soak's FPS ranged with
the played scene and is **not** used as a performance measurement.

The candidate was then installed as the launcher default and started again via
the external `/storage/roms/ports/MGS2-Substance.sh`, not the laboratory command.
That external smoke produced one process, selected the exact same two live
binaries, armed exactly 18 entries including 23 and excluding 34/37, cleared
A/B, fixed 1992 MHz and established the class-B base with both witnesses.

```text
box86-island41                    02294e0fc53298e9fc02c50ff5a5aa10392e44e78619358359fb6a172d104b71
wined3d_p56_batch_state.dll       6a926918fd40ce2e883dce6465392f8cbe791d474a3822e0408ea907489a7471
launch-play.sh                    381f2350e555e1569ffc9006266e293715b8793c57200b41db36a31e2afd5ad2
launch-island-ab.sh               186a09874db02c54bf9c3f1bb58b74591ffdf0ffccd63dacc1bf58880d1dca4a
soak.log                          4e4848bee48a521a2cbbbc4c1f2b623c4f9cfb4d7ed070c3034ebf6124170110
```

**Production claim:** only the already measured robust direction for entry 23,
about -2 to -2.6 ms/frame in that scene (paired median about +1.3 fps). The
withdrawn sigma and sign-test p remain withdrawn. Immediate rollback is
`box86-island32-prod` with p56 and the previous 17-entry allow-list.

## 38. p67 refutes context TLS as the black-frame cause; coarse DRAW is closed

The one correctness hypothesis permitted after p66 was tested without timing or
A/B. Guest WineD3D had initialised `wined3d_context_tls_idx` to 21 while the
separately linked ARM copy was still 0. p67 read the guest value after two
class-B witnesses, copied it through the native setter and verified 21 again
before allowing entry 37 to route. Until that check passed, the wrapper failed
closed to the guest body.

The hypothesis was real state divergence and still not the cause:

```text
TLS                    guest 21, ARM before 0, ARM after 21, attempts 1
source DRAW            101,305
guest fallback         0
final GL submissions   101,305, all arrays
frame witness          821 frames; retained 758..821
retained content       1 unique hash, 0/256 lit, 0/255 changed -- all black
```

Thus every routed source DRAW reached a final GL submission, but the submitted
state still produced an empty image. No FPS number is taken from this run. It
accidentally used `err+all` and printed hot `GL_INVALID_OPERATION` lines; that
does not invalidate the memory-only correctness records, but independently
forbids timing it.

The single pre-authorised relocation audit was then run against an analysis-only
`--emit-relocs` p67 link. `island_mutable_state_audit.py` found a 605-function
closure, 46 referenced writable objects and 12 zero-storage runtime candidates.
Its controls found both known shared objects: `mgs2_batch_ptr` and
`wined3d_context_tls_idx`. The batch pointer is already synchronised by the
production entry-4 wrapper; TLS was the only new authoritative guest/ARM state
and p67 just disproved it as the cause. The other candidates are ARM-owned GL
translation/cache state, bounded counters, one-shot logging flags or static
closure overreach, not another guest object that can honestly be copied.

**Decision:** there is no justified correction iteration. Generic post-batching
entry 37 is closed, including its old high-frequency `RunFunctionFmt()` A/B.
The next boundary must leave `context_acquire()`, current-context ownership and
`context_release()` in guest x86 and enter ARM below them. It remains a
correctness experiment until guest and routed frame-content witnesses agree.

Full evidence is in sections 18--19 of
`MGS2_NATIVE_CS_DRAW_BLACK_FRAME_2026-08-20.md`; the captured log is under
`logs/rg353vs/cs-draw-p67-20260820/`. The device was immediately restored to
FINALPLAY7: one process, 18 production entries including 23, excluding 34/37.

## 39. Lower entry 38 renders; its session exposed the direct-mutex freeze again

The correctness-only p68 boundary left context acquire, current-context
ownership, draw-state application, barriers and release in guest x86 and routed
only `wined3d_context_gl_draw_primitive_arrays()` to ARM. It produced a real,
changing picture at the heavy spot:

```text
source / final GL calls  4,982,735 / 4,982,735, all arrays
guest fallback           0
frame witness            17,832 frames; last 64 all unique
retained content         min 252/256 lit, 253/255 changed
owner screenshot         correct gameplay
```

So lowering the cut below guest context ownership refutes the p66/p67 black
frame. No FPS effect is measured and p68 is not production.

The same live session then froze, but the capture separates it from entry 38.
`BOX86_MUTEX_ALIGNED=1` was active. Main, `wined3d_cs` and
`wine_dinput_worker` all waited on direct mutex `0x6040623c` with expected value
2. Its bytes named `wine_dinput_worker` TID 29633 as owner, while that same TID
was itself in the untimed futex wait:

```text
lock 2   owner 29633   kind 0   nusers 1
DEFAULT queue non-empty   waiting_for_event 0   CS counters stable
```

This is the old self-owned session-lock shape, not the `0x400f...` Box86 alert
futex and not a native DRAW-tail stop. One occurrence under p68 says nothing
about relative frequency, but it proves that direct compatible mutexes removed
the shadow-pool mechanism without closing the gameplay self-deadlock itself.

The known one-time debugger recovery returned 0 from
`pthread_mutex_unlock(0x6040623c)`. The mutex became all zero, rendering resumed,
source/final advanced together to 5,018,093 and the frame witness advanced to
17,861 with a correct `MISSION FAILED` picture. A later same-process read reached
7,752,647 equal calls and 20,154 frames with the mutex still zero. The complete
post-p67 handoff is
`MGS2_NATIVE_DRAW_TAIL_AND_DIRECT_MUTEX_2026-08-20.md`; raw captures remain under
`logs/rg353vs/cs-draw-p68-20260820/`.

# Input latency and exit-status-40 follow-up — 2026-08-27

## Current decision

The input defect is reproduced, explained and fixed in a closed candidate. The
candidate keeps one gptokeyb process, delivers ordinary Start/Select mappings on
the physical button edges and preserves same-device Start+Select termination.
Wine is not allowed to consume the physical controller in this route, removing
the raw joystick action that preceded the translated Start key.

The most recent game exit is not yet attributed to one proved instruction or
callback. A separate audit found one additional Box86 native-Wayland callback
ABI error and patch 25 corrects it, but no captured exception ties that event to
the exit. The p25 binary remains a candidate until its exact device callback
and loaded-game gates pass. FINALPLAY18 is therefore still the public production
boundary at the time of this note.

## Fresh exit record

The normal FINALPLAY18 launch ended at `2026-08-27T06:09:26-0400` with launcher
status 40 after roughly 16.7 minutes. There was no second game process, kernel
OOM kill, Mali reset, Vulkan device-loss record or core file. Core capture was
disabled on the image, so those negatives do not identify the faulting frame.

Wine returns the low byte of an NTSTATUS to Unix. `STATUS_BAD_STACK` is
`0xc0000028`, so status 40 is compatible with that exception, but the game may
also return 40 deliberately. This remains an inference, not a crash signature.
No production patch is justified solely by that numerical resemblance.

## Why Start and Select were delayed

Upstream gptokeyb commit
`5b1284e1502548d476aa38e5979b0a8f48cb7b94` deliberately withholds both Start
and Back/Select while kill mode decides whether the pair is a chord. An ordinary
mapping is emitted only on release. At the same time, Wine's `winebus.sys` saw
the RG353VS controller directly. One physical Start press therefore reached the
game first as a joystick action and later as translated Tab, producing the
short first-person view before the menu and the apparent input lag.

`gptokeyb-patches/01-immediate-start-back-kill-chord.patch` adds a default-off
`-immediate-start-back` mode. It emits only those two ordinary mappings on the
real edge while retaining gptokeyb's same-device chord state and kill path. The
closed launcher route also appends `winebus.sys=d`; keyboard input still reaches
Wine through Wayland, but the physical controller no longer reaches the game a
second time.

The AArch64 helper rebuilt twice to the same SHA-256:

```text
49c782dad9da50cb0f5bb9e37821104e5089563feb24c7b0303117b75196b43a
```

Its upstream source, patch, GPL-2.0 license and rebuild command are recorded in
`gptokeyb-patches/`, `LICENSES/` and `harness/build_gptokeyb_mgs2.sh`.

## Input and soak gates already passed

An RG353VS-shaped uinput controller used the console's exact SDL mapping and
button codes. Start-down produced Tab-down and Select-down produced Enter-down
about 3 ms after their raw events. Start opened the expected map menu on the
button edge. The live game process maps contained no `winebus` module, so the
raw controller was not exposed to Wine in this route.

The FINALPLAY18 renderer plus this input candidate then loaded the exact save
route and remained in a lit gameplay scene for 31:07, including twelve bounded
walking bursts. This exceeds the fresh exit's elapsed time by more than 14
minutes but is not a proof that an intermittent crash cannot recur. A bounded
SEH-only log stayed at 4,816 bytes and contained one handled startup
`RPC_S_SERVER_UNAVAILABLE`; it recorded no later exception. An external
one-second pressure reader retained 1,569 rows in memory and wrote only at exit.
No kernel OOM or sustained memory PSI accompanied the run.

A synthetic same-device chord placed Select-down 201 ms after Start-down. The
game terminated directly with SIGTERM/status 143; no confirmation dialog was
involved. Teardown left zero game/helper processes, zero MGS2 bind mounts, an
available launcher lock and restored `ondemand`/`simple_ondemand` CPU/GPU
governors.

One earlier diagnostic launch accidentally used `WINEDEBUG=+seh,+tid`, which
also enabled Wine's default noisy channels and produced a 9.7 MB audio-error
log. That run was invalidated and its temporary log removed. The accepted run
used `-all,trace+seh` and the bounded external reader above.

## Additional Wayland ABI defect

An exact callback signature audit compared the current Box86 wrapper with the
generated headers from the Wine 11 build. The promoted p24 source had six
differences. Five are deliberately version-gated: Wine binds `wl_surface` at
version 4, `wl_seat` at version 5 and the wlr data-control manager at version 1,
so the newer events cannot be dispatched on those objects.

The sixth difference is reachable. The protocol declares
`zwp_text_input_v3_listener.delete_surrounding_text` as `(data, object,
uint32_t before, uint32_t after)`, while Box86 used an extra pointer and guest
format `pppuu`. Patch 25 changes it to the exact `ppuu` ABI and gives the whole
text-input listener the release/acquire publication used by patches 23+24.

`harness/wayland/audit_listener_abi.py` fails p24 on that mismatch and passes
p25 with exactly the five version-gated omissions. The p25 Box86 build was made
twice with the pinned `SOURCE_DATE_EPOCH=1756000000` and produced the same
unstripped production-style hash both times:

```text
1ff20d6d36dbbabd5a5aadd9ab677f0e02f6f06ab119f8a3c9952175db45e4cd
```

An earlier p25 build that embedded the current date was rejected before a gate
or promotion. `device/BOX86_WAYLAND_TEXT_INPUT_CANDIDATE.manifest` pins the
reproducible p25 and helper hashes plus the unchanged 18 FINALPLAY18 runtime
dependencies.

## Remaining gates

Before promotion, replace the rejected dated p25 device candidate with the
reproducible hash above, then run:

1. the targeted native-Wayland i386 callback gate;
2. the exact manifest and live-mount identity gate;
3. the correct `LOAD GAME` route, physical Start and Select edge checks and a
   same-device physical Start+Select exit;
4. a loaded-game soak beyond the prior exit point with bounded exception and
   pressure observation.

If p25 fails, promote the independently verified immediate-input route over
exact FINALPLAY18 and retain p24. If it passes, the combined fixed bundle may be
promoted with FINALPLAY18 as the immediate rollback. In either case, status 40
remains unclassified until an exception record or reproducible game path names
its cause.

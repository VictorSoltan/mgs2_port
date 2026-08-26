# Active patch audit and Box86 Wayland ABI candidate — 2026-08-26

## Result

The active FINALPLAY17 source and release chain was audited from its pinned
bases through the bytes selected by the device launchers. Five defects were
proved and fixed, and one critical runtime fix was deliberately left as a
fail-closed candidate:

| Area | Finding | Resolution | Production effect |
|---|---|---|---|
| Box86 Wayland wrapper | guest x86 callback tables could be installed directly in native armhf libwayland; four Wine 11 listener classes were missing, two callback signatures were wrong and slot publication had no explicit cross-thread ordering | patch 23 bridges and fails closed; patch 24 adds release/acquire publication for the affected callback slots | separate candidate; not selected by the normal entry |
| Box86 build graph | clean parallel builds raced `arm_printer.c` generation | patch 22 adds the missing `dynarec_arm -> PRINTER` dependency | build-order-only; reproduced the existing production Box86 hash |
| launcher teardown | thermal SIGTERM and a crash were indistinguishable; cleanup could signal a reaped/reused PID; FIFO creation used `mktemp -u` | thermal polling removed from the three fixed runtimes; bounded real exit status and cleared PID after reap; race-safe guard retained only by the research launcher | production no longer polls temperature or automatically signals the game |
| controller exit | launchers called `gptokeyb` with a positional executable name but no kill-mode option, so Start+Select depended on the intermittent OS confirmation handler | use PortMaster's `$GPTOKEYB` command prefix; explicit `-1` fallback; track and release-gate `mgs2.gptk` | Start+Select terminates the game directly on the RG353VS |
| provenance gates | DXVK was not rebuilt by the verifier; Box86 comparison hid every live-only file; `.env` overrode explicit caller variables | exact two-stage DXVK verifier, strict Box86 comparison, caller-over-`.env` precedence | release gates hardened |
| DirectSound probe | the default-off write probe calculated the first segment peak but discarded it | Wine patch 03 folds both segments into the maximum | research source only; no production DLL changed |

No additional proved correctness defect was found in the active DXVK patches
01, 02 and 08, the Box86 fused DXT surface bridge, or the active Wine runtime
delta. This is not a claim that every superseded historical experiment was
re-audited; the scope was the complete reconstruction boundary plus every
incremental patch that can reach FINALPLAY17 or its current research candidate.

## The crash that triggered the audit

The original unexpected exit could not be assigned a unique cause after the
fact. The game had started at about 14:25 and was gone at about 14:31, with no
remaining Wine/Box86 process or bind mount. The contemporaneous kernel log had
a Mali memory-pressure notification at 14:25:53 and PipeWire reported an xrun,
but there was no kernel segfault, system OOM kill or coredump. Neither message
proves the later exit.

The old thermal guard silently sent SIGTERM at 88 C and discarded `wait`'s
status, so a deliberate emergency stop became observationally identical to an
application exit after cleanup. It is now absent from FINALPLAY17 and both fixed
rollback launchers: production does not poll a thermal zone and does not send an
automatic temperature-triggered signal. Those launchers write exactly one
cold-path record to `/tmp/mgs2-play-exit.log` after the game has exited:

```text
timestamp launcher=<route> pid=<pid> status=<wait-status>
```

Cleanup clears the Wine PID immediately after `wait`, so it cannot signal a
reaped and possibly reused PID. This adds no render/audio-thread logging. Before
the thermal code was removed, a production smoke reached the renderer, passed
`18/18` live identity, stayed alive for 30 seconds and preserved an externally
requested SIGTERM as status 143; teardown left zero game processes and zero MGS2
bind mounts. Shell/reconstruction gates cover the final no-monitor launcher
revision. After deploy, its normal device smoke passed the `18/18` live identity
gate, reached the renderer and exited cleanly through the controller test below.

`device/launch-dxvk-play.sh` is an explicit research harness and retains the
88 C emergency guard for unattended experiments. There the reason file is
per-Wine PID, the monitor is joined before reading it and the record says
`requested_stop` rather than claiming a proved cause. It cannot be selected by
the normal PortMaster entry.

## Start+Select exit defect

The launchers used this form:

```sh
/usr/bin/gptokeyb "$EXE" -c "$GAMEDIR/mgs2.gptk"
```

That starts keyboard/controller mapping, but the current parser does not treat
the positional executable name as permission to terminate it. Kill mode
requires `-1 <application>` (or its `-k` equivalent). Consequently the apparent
Start+Select behavior came from ROCKNIX's global `Ending game?` handler, not from
the port, and could appear intermittent depending on which handler received the
combination.

The PortMaster control environment already exposes the correct platform command
prefix. On the tested image, `$GPTOKEYB` expands to the PortMaster binary plus
`-1`. All five full launchers now prefer the documented form:

```sh
$GPTOKEYB "$EXE" -c "$GAMEDIR/mgs2.gptk"
```

If that environment variable is unavailable, the `/usr/bin/gptokeyb` fallback
passes `-1` explicitly. `device/mgs2.gptk` is now tracked, and
`harness/test_gptokeyb_launchers.sh` prevents an active launcher or release
deploy from silently dropping kill mode or the config.

The executable's long name was tested as a possible `killall` mismatch and
rejected: the full `mgs2_sse_rg353vs_port.exe` target resolved successfully on
the device, while the truncated Linux `comm` name did not. No executable rename
was needed.

The deployed FINALPLAY17 command line was observed as:

```text
/roms/ports/PortMaster/gptokeyb -1 mgs2_sse_rg353vs_port.exe -c /storage/roms/ports/MGS2-Substance/mgs2.gptk
```

A bounded, non-grabbing `evtest` observation saw `BTN_SELECT=1` and
`BTN_START=1` in the same input report. Pressing the combination then closed the
game immediately, with no confirmation dialog. The launcher recorded status
143. Afterwards there were zero game, Wine, Box86 or gptokeyb processes, zero
MGS2 bind mounts, the `flock` lock was immediately available, and CPU/GPU
governors were restored to `ondemand`/`simple_ondemand`. The device-side
pre-change files remain available with suffix
`.bak-20260826-gptokeyb-killmode`; Git revert is the source rollback.

## Critical Wayland listener ABI defect

Patch 17 imported a native Wayland wrapper design, but this route does not
emulate `libwayland-client.so.0`: Wine's x86 callbacks cross into the native
armhf library. Its unknown-proxy path passed the guest callback table through
unchanged and logged that a crash would follow. An event dispatched through
that table would therefore treat an x86 address as an ARM function pointer.

The Wine 11 source and a live registry trace showed four reachable listener
classes absent from the wrapper:

- `zwlr_data_control_source_v1`;
- `zwlr_data_control_offer_v1`;
- `zwlr_data_control_device_v1`;
- `wl_data_source`.

The copied `xdg_surface.configure` and `wl_keyboard.key` callbacks also had too
many arguments. Patch 23 now:

- bridges all four missing listener structs with their protocol-version-accurate
  signatures;
- corrects the two existing signatures;
- obtains the class through public `wl_proxy_get_class()` instead of private
  `wl_proxy` layout dereferencing;
- serializes the fixed callback-slot registry during cold listener setup;
- returns `-1` for an unknown proxy or exhausted callback table rather than
  installing an invalid/NULL native listener.

Wine uses a blocking Wayland event-dispatch loop while clipboard and surface
paths can install listeners elsewhere. The patch-23 mutex excluded concurrent
slot writers, but its ARM callback stubs still loaded plain global pointers.
Patch 24 makes the six corrected/added listener references C11 atomics: a release
store publishes the guest callback table and each native callback uses an
acquire load. Lookup remains relaxed under the patch-23 mutex, so callbacks do
not take a lock.

The rebuilt candidate is:

```text
box86-fp24-wayland-atomic-candidate
sha256 d6cafba667d16f6227c0ffd5437e7ac52253dd46624c2edfcbbd36ca3843188b
```

`device/BOX86_WAYLAND_ABI_CANDIDATE.manifest` differs from the 18-row
FINALPLAY17 identity only at `/usr/bin/box86`. The research launcher is
`device/launch-dxvk-wayland-abi-candidate.sh`.

An intermediate candidate, before the final mutex and fail-closed handling,
had one Wine page fault reading `0x00000004` and exited with status 5. The exact
FINALPLAY17 control passed, and that fault did not repeat in the immediate
candidate repeat or three subsequent runs. The final hash above then passed:

- a 45-second identity/renderer smoke;
- the title and exact `LOAD GAME` route through save rows 09, 08 and 07;
- confirmation and a visually correct 3D scene;
- eight walking bursts and four actions;
- more than six minutes alive, with 12 non-empty witness screenshots;
- exactly one game instance, no page fault/segfault, no unknown listener or
  slot-exhaustion message, and no thermal stop;
- clean status-143 external termination, zero remaining processes and mounts.

That visual witness used the patch-23 hash. It is evidence for patch 23, not for
the later atomic-publication binary. The private on-device witness remains under
`/storage/roms/ports/ablogs/box86-wayland-abi-autoload-20260825`; it is ignored
because it contains game imagery.

The final patch-24 hash passed a purpose-built Linux i386 client through Box86's
native armhf libwayland wrapper on the RG353VS. This is a callback test, not a
normal game smoke. `harness/wayland/run_device_wayland_abi_gate.sh` produced:

```text
observer: data_offer=2 offer=2 selection=4
source:   source_send=1 source_cancelled=1
receive:  rc=0 data_offer=1 offer=1 selection=1
exhaust:  first_ten=10 eleventh=-1
window:   xdg_configure=2 keyboard_keymap=1 keyboard_key=2
normal callbacks: 0 unknown-listener, slot-exhaustion or crash matches
targeted_gate=PASS
```

The two exhaustion warnings are expected only in the synthetic overflow mode;
all seven probe processes returned zero and none remained. The standard
`wl_data_source` fallback was registration/overflow tested even though Sway's
advertised wlr-data-control route handles the live clipboard events. The p24
binary was rebuilt twice with the pinned epoch and reproduced its hash byte for
byte. It is still not production: `harness/make_release.sh` refuses a production
bundle while either `box86_candidate_patch_23` or `box86_candidate_patch_24`
remains in the lock.

The same final p24 hash also passed a normal-game witness through the explicit
research launcher: correct `LOAD GAME` route through rows 09, 08 and 07, a
visually correct scene, four walking bursts, four actions, 14 non-empty
screenshots, `18/18` live identity and exactly one game instance. Replacing and
reading the clipboard while the game stayed live exercised the source send and
cancel callbacks successfully. Eighteen consecutive 50-second observations
reached process elapsed time 1101 seconds with the same PID and no crash,
unknown-listener or slot-exhaustion line. The intended 30-minute observation was
interrupted at that point, so this is not recorded as a completed 30-minute soak;
suspend/resume also remains untested.

## Build and provenance defects

### Box86 clean-build race

`make clean && make -j4` failed because `dynarec_arm` compiled generated
`src/dynarec/arm_printer.c` before the `PRINTER` target ran. A stale generated
copy had hidden the missing dependency. Patch 22 adds the dependency to the
consumer. Repeated clean `make -j8` builds then passed. With
`SOURCE_DATE_EPOCH=1756000000`, the patch-22 build reproduced the currently
shipped Box86 byte for byte:

```text
51dfcc130b9760970189a67edd8cd78c777c5d69c8b9ec07cfbc5657821d9be9
```

The `-fshort-wchar` island warning was also checked. The island is deliberately
compiled with Windows 16-bit `wchar_t` and does not cross into libc `wcs*` or
`wmem*`; no runtime defect was established there.

### DXVK has two source stages

The old lock implied that D3D8 and D3D9 came from the same 01+02+08 source
state. They do not. The exact shipped files require:

| DLL | Source stage | Meson `b_ndebug` | epoch | SHA-256 |
|---|---|---:|---:|---|
| D3D8 | base + patch 02 | `true` | `1787578049` | `22e519d266b62bfa54d1d1f81e6314aab7b75890b342908f24d2b454e4af3baa` |
| D3D9 | base + patches 01, 02, 08 | `false` | `1787659200` | `4918b0283329702116dc64fba2e7be992a8b67ef2534ccf5af919f334c690650` |

With Meson 1.10.1, omitting the explicit D3D8 `b_ndebug=true` also introduces
`_GLIBCXX_ASSERTIONS` code and cannot reproduce the carried-forward binary.
`harness/verify_dxvk_rebuild.sh` reconstructs both stages from commit
`617958fe...`, pins the Vulkan/SPIR-V header commits and tool versions, and
compares the output bytes. Both hashes above were reproduced exactly.

### Reconstruction and release gates

The Box86 comparison formerly removed every line beginning `Only in <live>`,
which made unrecorded source files invisible to the check. It now excludes only
named generated products. Reconstruction uses `git archive`, so verification
does not modify the live checkout's Git worktree metadata.

The first hardening still piped `diff` into `wc`, which allowed a status greater
than one to be replaced by `wc`'s success. `harness/fail_closed_diff.sh` now
captures stdout and stderr and preserves all three `diff` outcomes: identical,
different and comparison failure. Its regression proves an equal tree returns
0, a live-only `.c` returns 1 and names the file, and a missing input tree
returns 2 with a diagnostic. The island's two generated identity headers now
have a separate exact regeneration gate; this also exposed and fixed a stale
launcher parser in `build_island_objects.sh` after the renderer selector split.

The first clean p24 Box86 build also exposed an unrecorded CMake-cache input: it
omitted the ROCKNIX compatibility define and eight legacy-libm linker wraps, then
required `GLIBC_2.43` and could not start on the device. The bad test binary was
replaced. `box86_cflags` and `box86_ldflags` are now pinned in
`device/FINALPLAY.lock`; both `verify_rebuild.sh --build` and `make_release.sh`
reconfigure CMake with those exact values and require all 8/8 wraps. Two manual
canonical rebuilds reproduced the p24 candidate hash. The final integrated
`verify_rebuild.sh --build` gate also passed: exact WineD3D bytes, both generated
island headers, exact candidate Box86 bytes and all 8/8 ROCKNIX-compatible libm
wraps.

Explicit environment variables now take precedence over `.env` in the Wine,
Box86 and DXVK verifier/release paths. This was tested by forcing `WORK_DIR` to
an isolated `/tmp` directory while `.env` named a different location.

Final reconstruction result:

```text
wine:  reconstructed byte for byte, 0 differences
box86: reconstructed, 0 differences outside named build products
FINALPLAY sources are reconstructible from the pinned bases
```

## Wine build audit

A broad Wine build compiled the audited runtime for a substantial portion of
the tree, then stopped while linking user32 tests because the host data volume
had no free space. This is an infrastructure limit, not evidence of a source
failure. The following relevant targets were built separately and passed:

- PE: D3D8, DirectMusic (`dmime`, `dmusic`, `dmsynth`), DirectSound,
  kernelbase, user32 and WineD3D;
- Unix: ntdll, opengl32, win32u and winewayland.

The warnings in D3D8 and DirectSound led to Wine research patch 03. Its only
semantic change repairs the bounded probe's first-segment peak calculation; the
probe remains disabled unless `MGS2_DSOUND_PROBE>=3`. No rebuilt Wine DLL from
this audit was deployed.

## Static negative results

- DXVK patch 01's Mali capability gates and push-constant handling showed no
  unsupported lifetime or bounds path in the active configuration.
- DXVK patch 02's hidden static window and dynamic D3D9 load keep the module
  alive for the required process lifetime; no use-after-free was found.
- DXVK patch 08 executes under the caller's state-cache lock and deduplicates
  only an exact mapping pair; no independent race was found.
- The Box86 fused DXT5 surface bridge retains guest fallback on unsupported
  shapes and its cache/row arithmetic was checked for caps, bounds and integer
  overflow; no proved defect was found.

These are static conclusions. Performance and runtime correctness claims still
require the RG353VS gates described in `docs/DEVICE.md`.

## Critical open item: display_lock

The direct native-mutex mode remains production because it closed the measured
shadow-pool publication failure for `session_lock`. It did **not** prove that the
separate `display_lock` self-owner deadlock is fixed. That signature remains
critical-open at the exact object/RVA and bounded capture described in
`MGS2_NATIVE_DRAW_TAIL_AND_DIRECT_MUTEX_2026-08-20.md`. No new broad `wchan`
sampler or hot-thread logger was added, and no speculative mutex change was
promoted without the missing captured call chain.

## Current decision and rollback

Normal production remains FINALPLAY17 with the original Box86 hash
`51dfcc...`. Patch 22 records a build dependency without changing those bytes;
patches 23+24 remain opt-in. The rollback commands are unchanged:

```sh
MGS2_RENDERER=dxvk16 /storage/roms/ports/MGS2-Substance.sh
MGS2_RENDERER=wined3d /storage/roms/ports/MGS2-Substance.sh
```

The targeted callback/slot gate for patches 23+24 is complete, and the normal
p24 witness covered load, movement, live identity and a clipboard replacement.
The remaining promotion gate is a completed longer normal-entry soak including
focus transitions and suspend/resume, followed by final live identity and
teardown checks. A new crash should be classified first from
`/tmp/mgs2-play-exit.log`, the Wine output and the kernel log; the earlier Mali
notification alone must not be reused as a diagnosis.

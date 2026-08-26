# Active patch audit and Box86 Wayland ABI candidate — 2026-08-26

## Result

The active FINALPLAY17 source and release chain was audited from its pinned
bases through the bytes selected by the device launchers. Four defects were
proved and fixed, and one critical runtime fix was deliberately left as a
fail-closed candidate:

| Area | Finding | Resolution | Production effect |
|---|---|---|---|
| Box86 Wayland wrapper | guest x86 callback tables could be installed directly in native armhf libwayland; four Wine 11 listener classes were missing and two callback signatures were wrong | patch 23 bridges the exact Wine 11 listeners, serializes slot allocation and rejects unknown/exhausted registrations | separate candidate; not selected by the normal entry |
| Box86 build graph | clean parallel builds raced `arm_printer.c` generation | patch 22 adds the missing `dynarec_arm -> PRINTER` dependency | build-order-only; reproduced the existing production Box86 hash |
| launcher teardown | thermal SIGTERM and a crash were indistinguishable; cleanup could signal a reaped/reused PID; FIFO creation used `mktemp -u` | bounded exit record, cleared PID after reap, private temporary FIFO directory | deployed to all three fixed runtime paths |
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
application exit after cleanup. The fixed launchers write exactly one cold-path
record to `/tmp/mgs2-play-exit.log`:

```text
timestamp launcher=<route> pid=<pid> status=<wait-status> reason=process_exit
timestamp launcher=<route> pid=<pid> status=<wait-status> reason=thermal_guard temp_mc=<temperature>
```

They do not add render/audio-thread logging. A production smoke run reached the
renderer, passed `18/18` live identity, stayed alive for 30 seconds and recorded
the externally requested SIGTERM as status 143. Teardown left zero game
processes and zero MGS2 bind mounts. The same behavior was observed after the
full candidate gameplay witness.

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

The rebuilt candidate is:

```text
box86-fp23-wayland-abi-candidate
sha256 750227508181a929a3973e6d65bb70d60b7c42b60542cb16b021e192815ccf24
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

The private on-device witness remains under
`/storage/roms/ports/ablogs/box86-wayland-abi-autoload-20260825`; it is ignored
because it contains game imagery. Patch 23 is not promoted from this one visual
session. `harness/make_release.sh` refuses to produce a production bundle while
the lock contains `box86_candidate_patch_23`.

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

## Current decision and rollback

Normal production remains FINALPLAY17 with the original Box86 hash
`51dfcc...`. Patch 22 records a build dependency without changing those bytes;
patch 23 remains opt-in. The rollback commands are unchanged:

```sh
MGS2_RENDERER=dxvk16 /storage/roms/ports/MGS2-Substance.sh
MGS2_RENDERER=wined3d /storage/roms/ports/MGS2-Substance.sh
```

The next promotion gate for patch 23 is a longer normal-entry soak covering
clipboard/focus transitions and suspend/resume, followed by live 18/18 identity
and teardown checks. A new crash should be classified first from
`/tmp/mgs2-play-exit.log`, the Wine output and the kernel log; the earlier Mali
notification alone must not be reused as a diagnosis.

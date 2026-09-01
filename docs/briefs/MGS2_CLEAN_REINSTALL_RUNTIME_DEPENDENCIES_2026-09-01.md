# MGS2 clean reinstall: missing i386 Wayland runtime dependencies

Date: 2026-09-01\
Device: RG353VS, ROCKNIX 20260822\
Result: clean FINALPLAY23 launch restored; packaging omission closed

## Scope and preserved state

The owner requested a destructive reinstall of MGS2 while preserving progress.
Ten save slots were copied twice plus a compressed archive before removal. Each
slot is 29,102 bytes. After reinstall, all ten device paths and SHA-256 hashes
matched both independent copies. The installed legal EXE retained the locked
original hash `29759e6f06eaea4d61bb6aef5a5ef45a936eac1e76fa0c3471cf4f231349aaa0`.

The old installation occupied about 9.2 GiB. The rebuilt installation occupied
about 8.1 GiB before the 36.4 MiB dependency repair. The difference was mainly
an unused 64-bit prefix and accumulated runtime experiments, not missing game
content. The final allocated total reports about 8.4 GiB: 7.8 GiB of game data,
273.4 MiB for the active direct32 prefix, 36.4 MiB for `x86libs`, plus the other
runtime objects and filesystem allocation/rounding. The complete local 39-file
bundle is 67 MiB including `x86libs`. The clean overhead over the 7.8 GiB legal
base is therefore expected and substantially below the old installation's
accumulated overhead.

An unexpected DMC3 check was a stale diagnostic process, not a scheduled or
boot-persistent launcher. DMC3 files and configuration were left unchanged.

## Failure after the requested cold delay

After more than the requested five-hour pause and a device reboot, the clean
FINALPLAY23 process reached Wine but aborted in Vulkan surface creation:

```text
Assertion failed: !status && "vkCreateWin32SurfaceKHR"
```

A bounded D3D8 probe observed that the user-driver priming `CreateWindowExW`
returned NULL. A Wine startup trace then showed the real boundary:

```text
get_builtin_unix_funcs failed to load
"/usr/lib/wine/i386-unix/winewayland.so": Cannot dlopen
```

Box86 dependency diagnostics named the missing objects:

```text
libwayland-egl.so.1
libxkbcommon.so.0
libxkbregistry.so.0
```

Their transitive closure was also absent. The pre-reinstall game directory had
hidden this because it already contained an `x86libs` directory; the clean base
copy and the 28-file FINALPLAY23 release record did not provide one.

## Rejected detours

A diagnostic Wine `win32u` build unlinked a NULL-HWND client surface before
freeing it and removed the immediate assertion, but DXVK then reported four
failed swap-chain creations. This demonstrated a reachable cleanup defect, not
the primary clean-install repair, and the binary was not promoted.

Increasing the shared engine's `explorer` wait from 10 to 60 seconds was also
not required. With the dependency set present, the unchanged production engine
started the real game in about 5.8 seconds and remained live through the
35-second gate. The historical FINALPLAY17--22 engine therefore stays
byte-identical.

## Promoted clean-install boundary

`device/FINALPLAY_RUNTIME_X86LIBS.sha256` pins these ten i386 files under
`MGS2-Substance/x86libs/`:

- `libstdc++.so.6`, `libffi.so.8`;
- `libwayland-client.so.0`, `libwayland-egl.so.1`;
- `libxkbcommon.so.0`, `libxkbregistry.so.0`;
- `libxml2.so.2`, `libicuuc.so.72`, `libicudata.so.72`, `liblzma.so.5`.

The FINALPLAY23 wrapper verifies exactly ten simple filenames and exact hashes
before entering the shared engine. The current release record grows from 28 to
39 files: the earlier bundle, the dependency manifest and ten libraries. The
legal game EXE, saves, prefix and ARM system libraries remain excluded.

## Device evidence

The unchanged normal entry, with production D3D8 and gptokeyb enabled, measured:

```text
generated exact FINALPLAY23 game EXE d6b81257...
identity verified, 21 of 21 runtime files match
game process live after 35 seconds
gptokeyb-mgs2-immediate -immediate-start-back live
```

The captured 640x480 frame showed the animated MGS2 Substance title screen and
`PRESS START BUTTON`. Controlled SIGTERM returned status 143, restored the CPU
state, removed every MGS2 bind mount and left no game, explorer or input-helper
process.

After deploying the final 39-file bundle, a second normal-entry test used the
repository's pixel-gated automation. It selected LOAD GAME, moved two entries
to the established row-07 target, confirmed YES, and accepted the loaded scene
at gray mean `0.242` against the required `0.15`. It then completed four
movement bursts and four `x` attacks. The loaded and post-action 640x480 frames
were visually normal, the game remained the sole live instance, and there was
no new kernel GPU/OOM/fault record during this run. Final cleanup recorded
`launcher=finalplay23 status=143`, no relevant process or bind mount, an
available launcher lock, restored `ondemand`/1.8 GHz CPU state and no stale CPU
baseline file.

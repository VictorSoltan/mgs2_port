# FINALPLAY21 missing-sea repair and production promotion

Date: 27 August 2026
Device: Anbernic RG353VS, RK3566/Mali-G52, ROCKNIX 20260822
Production: FINALPLAY21
Rollback: `MGS2_RENDERER=fp20`

## Result

FINALPLAY20 could draw the Big Shell bridge and distant background while the
sea surface itself was absent. Three frames from one fixed camera had an
exactly solid `(220, 237, 198)` rectangle at `x=565..639, y=155..279`, with no
changed pixels. This was missing geometry/rendering, not a static-water
animation issue.

FINALPLAY21 keeps the complete FINALPLAY20 Wine, Box86, DXVK, input and audio
bundle. It changes one game flag at startup so libdg's existing fixed-function
`wpatch` path is used instead of its custom patch vertex shader. The owner
confirmed that the sea returned, animated, had no black squares and felt normal
in frame rate. Three one-second frames changed `96.6827%` and `97.9413%` of the
clean sea region. The normal production entry subsequently cold-started the
same exact patched image and passed `21/21` live identity.

## Diagnosis

The first hypothesis was that a FINALPLAY17--20 change had broken the sea:
state-cache handling, compiler-worker selection, the native fused DXT surface
bridge, Wayland ABI work or the later input/audio changes. Exact FINALPLAY16
showed the same empty sea, refuting that boundary.

A WineD3D family control was attempted and is a negative result, not an A/B:
the preserved old WineD3D Wayland driver cannot load against the current
Wine/ROCKNIX ABI and exited before creating a window. Replacing it with current
system glue also exited before a valid scene. Neither run says whether WineD3D
would draw the water.

The recovered game source identifies the surface actor in
`mgs2x/source/user/takabe/object/wave5.c` (`NewSeaSurfaceSet`) and its renderer
in `mgs2x/source/system/libdg/wpatch.c`. `wdgd.c` unconditionally sets
`M_DG_WINAPP_PATCH_USE_VERTEXSHADER` in the hardware-processing branch even
though `wpatch.c` retains a complete non-vertex-shader path. On the shipped port
executable, that flag set is:

```text
virtual address  0x008a2947
file instruction 0x004a2947: or eax,0x00020000
immediate byte   0x004a294a: 02
```

Changing only that immediate byte to `00` leaves every other patch/object
vertex-shader flag intact and turns this operation into `or eax,0`. The
candidate then drew the animated sea. That is the refuting result for the
broader renderer/DXT hypotheses and the positive witness for this boundary.

## Exact objects

The legally installed game image is never committed or distributed:

```text
original EXE SHA-256
29759e6f06eaea4d61bb6aef5a5ef45a936eac1e76fa0c3471cf4f231349aaa0

patched temporary view SHA-256
6686b3fa6484a0609fbe65be46f34cbba941b18e252db7bbb83d457153ba31d6

only cmp -l difference (one-based)
4860235   2   0
```

`device/patch-mgs2-wpatch-novs.sh` refuses any other input hash, checks the
original byte, writes a temporary file, verifies the complete output hash and
never overwrites the installed image. `device/launch-play-dxvk-fp17.sh`
bind-mounts that temporary file only for FINALPLAY21, verifies it again through
`device/FINALPLAY21_WATER_WPATCH.manifest`, and removes the mount/file during
cleanup. A stale mount after power loss is removed before the original hash is
read. The source-equivalent change is retained in
`game-patches/01-wpatch-fixed-function-fallback.patch`.

## Evidence and gates

Local capture hashes:

```text
FINALPLAY20 missing-sea frame
ef82fc91513b03dc083ec86e52c1210be8af203e6b3ea66f5ff49a18e8fa3556
logs/rg353vs/missing-sea-20260827/live.png

exact candidate water frame
ff0ed1b8216e54d96f26965010f659e8132bf2e19ade2bbf732236a98ce4d916
logs/rg353vs/missing-sea-20260827/wpatch-novs-water.png

motion frames
bfa1485210a7237368e342084898c0869576182ac41973a89a22817d37e16090
d20c8dd3e08e17c814d40a65d78e94554f06339be93367f026f6e9e68e6ec3f2
56d42ac1d8ae63c3d797f5760711c03ef769060d23f5e2f1895487dd14c2ec58

FINALPLAY21 cold-start frame
abceb72468f6cfaac1335c92803ddd692439182e5cffe72a8c4b66e6f17cb03d
```

Promotion gates:

- the helper generated the exact patched hash from the exact original hash;
- `cmp -l` reported one changed byte, at the recorded offset;
- the source patch applies to the recovered source with its original CRCRLF
  line endings using `patch --binary`;
- the owner observed animated water, no black squares and normal-feeling FPS;
- the normal device entry reported
  `identity verified, 21 of 21 runtime files match`;
- the live process exported `MGS2_PRODUCTION_ROUTE=finalplay21` and the mounted
  game path hashed to the exact candidate object;
- a status-143 termination removed the game/helper processes, temporary file
  and game-EXE bind, restored the original `29759...` path and released the
  one-instance lock;
- a second fully cold start with the final pre-execution helper-hash guard again
  passed `21/21`, with helper `b7ba8198...` and mounted EXE `6686b3fa...`;
- the FINALPLAY18, FINALPLAY19, FINALPLAY20 and FINALPLAY21 static gates all
  passed after the selector change.

An external frame-counter read on the candidate covered `10.02 s` at about
`29.64 FPS`, but the CPU was thermally capped to 1608 MHz and there was no
interleaved control. It is deliberately not a performance result. FINALPLAY21
makes no FPS improvement or no-regression claim; its promotion claim is the
restored, moving sea with exact-byte containment.

## Rollback

FINALPLAY20 is unchanged as a named route and omits the game-image bind:

```sh
MGS2_RENDERER=fp20 /storage/roms/ports/MGS2-Substance.sh
```

Older exact routes remain available as `fp19`, `fp18`, `fp17`, `dxvk16` and
`wined3d`. FINALPLAY20 is the immediate diagnostic control for this change.

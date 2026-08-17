# MGS2 native batch flush: shared-state repair and same-process measurement

Date: 2026-08-16  
Device: RG353VS / RK3566 / Mali-G52 / ROCKNIX 20260722  
Status: **production in FINALPLAY6: island31 + p56, entry 4 enabled**

## Result

`mgs2_batch_flush` (island entry 4) is worth a median **-2.680 ms/frame**
at the stable post-walk reinforcement spot. The equivalent paired FPS gain is
**+0.899 fps median** (range +0.628 to +1.372); FPS computed from the two arm
medians is 18.70 versus 17.84, **+0.862 fps / +4.8%**.

This is a real measured improvement. It is not the requested +10 fps and must
not be described as one.

The first implementation was wrong and crashed. Its failure exposed a boundary
condition the GL-slot analysis did not test: the ARM-linked WineD3D island has a
second copy of every file-scope variable. Native `mgs2_batch_flush()` therefore
read an empty ARM `mgs2_batch`, while the guest draw producer continued filling
the real guest object. Flush became a no-op until guest state was corrupted.

Patch 54 shares only the authoritative pending-batch object across the cut. The
Box86 wrapper waits until two existing guest-DLL witnesses agree on the module
base, resolves the cold `mgs2_batch_state` accessor by name/RVA, calls it once,
and installs the returned guest pointer in the ARM body. Calls made before that
proof remain on the guest path. The EBO cache remains private to each arm.

## The failed run is part of the result

Configuration:

```text
box86-island30  b95feec0ce78b48723b1d5618fb6614ad8cf894e0e730453b4ecc0fd0ed517b9
wined3d p55     15239ba163c87a9cc759e7d4f8a7bd89f5e829f86018f783fa422798c0b0987c
entry 4         armed, same-process ABBA
```

It reached two title/menu cycles and then failed during the save-load route:

```text
wine: Unhandled page fault on read access to 00000004 at address 00000004
```

This candidate is closed. Its apparent first-cycle `-7.089 ms/frame` was on a
changing capped menu, with 2625 versus 4794 calls, and is not a performance
result.

The repository already warned in `harness/island/full/BUILD.md` that a partial
cut through duplicated `mgs2_batch` state is invalid. Treating the newer
`island_gl_reach.py` result as a complete arming verdict was therefore an error.
The tool now says `GL-SLOTS OK (other cut checks still required)` and documents
writable globals as an explicit fourth limit.

## Corrected implementation

```text
box86-island31                 d1dcffac1f60a2d1c922cddac7ad1980dd316c05237029df187875fb67015c60
wined3d_p56_batch_state.dll    6a926918fd40ce2e883dce6465392f8cbe791d474a3822e0408ea907489a7471
measured unstripped p56        e0779dda62e8c06d67821531c9edb547ff08305bab9d3d0f27199ebf84367421
shared .text in both p56 files d46592405063ec75c8d7123af2b1a64c465aa396b1c796fb39ce61b514691579
```

Stripping removed only debug/COFF data. The complete `.text` section of the
measured device DLL and the final 2.97 MB repository DLL is byte-identical.

Build controls:

```text
native IDs generated / registered     1616 / 1616
x86 marker bytes in ARM objects        0
entry-4 source closure                 12 functions
entry-4 required GL slots               7
required but unresolved GL slots        0
fresh Box86 patch chain 01..07          PASS, -F0
patch-07 output versus source           54/54 files byte-identical
Wine patch 54 reverse/forward roundtrip PASS, -F0
```

## Measurement boundary

One live process, entry 4 switched every 64 displayed frames in ABBA order;
eight settle frames discarded from every block. CPU cap held at 1992 MHz and
the production launcher selected the GPU performance governor. The route loaded
the reinforcement save and completed twelve automated walk bursts.

Cycles 1--11 are title/menu. Cycle 12 is the save transition. Cycles 13--20 are
load/walk and move the scene within a pair. They are excluded. The measurement
window begins only after the driver printed route completion, then retains
cycles whose two call counts agree within 2%. Cycles 21--30 all pass, with only
zero or one call difference out of about 128,802 per arm.

```text
cycle  routed ms/f  guest ms/f  delta ms/f  routed/guest calls
21        53.313       56.136       -2.822   128802 / 128802
22        53.138       56.882       -3.744   128802 / 128802
23        52.976       55.612       -2.636   128802 / 128802
24        53.371       57.589       -4.217   128803 / 128802
25        53.561       56.284       -2.723   128802 / 128803
26        53.632       56.001       -2.369   128802 / 128803
27        53.836       55.781       -1.945   128802 / 128802
28        53.078       56.099       -3.021   128802 / 128803
29        53.945       55.966       -2.022   128803 / 128802
30        53.952       55.845       -1.893   128802 / 128802
```

```text
n                                      10 paired cycles
median routed                          53.466 ms/frame
median guest                           56.050 ms/frame
median paired routed - guest           -2.6795 ms/frame
mean paired routed - guest             -2.7393 ms/frame
paired delta range                     -4.218 .. -1.893 ms/frame
faults through all 30 cycles            0
```

The first cycle after load and every moving-scene cycle are recorded but not
used. In particular, cycle 20 has similar call counts but precedes route
completion; its `-12.639 ms/frame` is scene motion, not the claimed effect.

## Promotion boundary

The owner authorised production promotion on 2026-08-16. The production
defaults are now the inseparable `box86-island31` +
`wined3d_p56_batch_state.dll` pair, with entry 4 added to the allow-list.

After deployment, `FINAL_PRODUCTION.sha256` passed completely on the device.
The real external `/storage/roms/ports/MGS2-Substance.sh` then cold-started one
game instance, loaded the target reinforcement save and completed all 12 walk
bursts. Live `cmp` checks proved that `/usr/bin/box86` and the mounted
`wined3d.dll` were the two promoted files. The run reported:

```text
17 / 35 island entries armed
16 entries encountered (armed entry 19 was not used on this route)
1616 linker-supplied native IDs registered and armed
entry 4 shared guest batch state 0x7ba40040
island faults 0
game instances at route completion 1
```

This is a bounded automated correctness smoke, not a claim that arbitrary long
manual play is proven. `device/launch-entry4-playtest.sh` remains as an explicit
diagnostic selector for the same production pair.

Exact rollback keeps all three old selections together:

```text
MGS2_BOX86_BIN=box86-island29
MGS2_WINED3D_DLL=wined3d_p55_glinfo.dll
MGS2_BOX86_ISLAND_ONLY=0,1,2,3,5,6,9,10,14,18,19,22,28,29,32,33
```

## Artefacts

```text
wine-patches/54-island-batch-state.patch
box86-patches/07-native-island.patch
binaries/box86-island31
binaries/wined3d_p56_batch_state.dll
device/launch-entry4-playtest.sh
device/launch-island-ab.sh
harness/island/full/island_gl_reach.py
harness/island/full/island_reach.py
```

# MGS2 native DirectSound FIR bridge — 2026-08-13

## Status

Promoted to production as FINALPLAY4 after the player exercised the candidate
in combat and reported that it looked normal. A subsequent launch through the
ordinary external `/storage/roms/ports/MGS2-Substance.sh` loaded the save with
one instance; the live Box86, dsound and dmsynth mounts matched the production
files by SHA256, and the game environment contained
`MGS2_BOX86_NATIVE_DSOUND_FIR=1`.

This work removes one measured x86-emulation cost. It does not change the
DirectSound API, buffer lifetime, sound controls, Wine scheduling, or the game.
Wine patch 36 isolates the float-output FIR convolution behind a fixed 32-bit
job ABI; Box86 patch 06 recognises only that exact helper and executes the same
loop as native ARM code when `MGS2_BOX86_NATIVE_DSOUND_FIR=1`.

The device's Box86 process is an ELF32 ARM hard-float process. Consequently the
in-process replacement is ARMv8 AArch32/VFP code running natively on the
Cortex-A55, not an AArch64 function. Calling AArch64 directly would require a
different process/ABI boundary and would add a layer. The useful claim here is
that the FIR loop no longer goes through the x86 decoder/dynarec.

## Hypothesis and refutation

Hypothesis: Wine's DirectSound FIR convolution is large enough in the mixer
thread that translating it from x86 wastes a meaningful fraction of a core.

Refute it if any of these occurs:

- the isolated x86 function is not the dominant `dsound` guest block;
- enabling the bridge leaves that guest block present;
- fixed-clock mixer CPU does not fall;
- combat sound is distorted, missing, or unstable.

The first three tests passed. The fourth requires real play because the known
SFX loss is intermittent and the automatic route does not reliably reproduce
the same combat state.

## What was changed

`wine-patches/36-dsound-native-fir-target.patch`:

- retains Wine's original committed/current buffer collection;
- retains phase advancement and returned source position;
- uses the new helper only for `putieee32`, the format selected by MGS2;
- leaves all other output converters on the original callback path;
- remains valid x86 code when the Box86 switch is off.

`box86-patches/06-native-dsound-fir.patch`:

- consumes one guest job pointer from EAX, matching Wine i386 `regparm`;
- copies the 17-DWORD job descriptor before use;
- runs a bounded native FIR self-test before publishing the bridge;
- matches the exact 48-byte helper prologue and caches one guest address;
- is gated by `MGS2_BOX86_NATIVE_DSOUND_FIR=1`; Box86 itself defaults off, while
  the exact FINALPLAY4 launcher/DLL pair now selects it by default.

The native compiler contracts a multiply/add in the dot product to VFP FMA.
This preserves the resampler calculation but is not claimed to be sample-bit
identical to Wine's x87 accumulation. Audible correctness is therefore an
explicit promotion gate.

## Build and byte verification

Production artifacts:

```text
302eff548429c6b87aed3931bb0bb1acd4c4c8a130a96ae7025612c2d7eb999c  dsound_p36_native_fir_target.dll
89ca26c512489ed18b3605ca195fa7dd45d3a9f8cc3fefafac8b1ebd9b86a252  box86-native-dsound-fir1
```

Both game-directory files matched their live bind targets byte-for-byte:

```text
/usr/lib/wine/i386-windows/dsound.dll
/usr/bin/box86
```

The Box86 binary is ARM EABI5 hard-float, ARMv8 AArch32, and exports
`mgs2_native_dsound_fir_impl`. The Wine helper RVA is `0x1be30`; its candidate
prologue matches patch 06's 48-byte signature.

## Device measurements

The fixed-clock runs used:

```text
MGS2_FREQ_STEPS=1416000
MGS2_BOX86_NATIVE_AABB=0
MGS2_BOX86_NATIVE_DSOUND_FIR=0 or 1
MGS2_WALK_SEQUENCE=down:3.0,right:1.6
MGS2_ACTION_COUNT=20
MGS2_ACTION_KEY=x
```

Exactly one game instance existed in each run. `/proc/<pid>/task/*/stat` was
read before and after a 30-second window; nothing logged from the mixer thread.

```text
control, native FIR off: wine_dsound_mix 12.97% of one core
candidate, native FIR on: wine_dsound_mix  7.57% of one core
change:                                      -41.6%
```

An independent 199 Hz userspace `perf`/Box86 guest-map profile showed:

```text
control:   dsound.dll guest samples 717
control:   helper RVA 0x1be30        647
candidate: dsound.dll guest samples  40
candidate: native FIR kernel         260 host samples
```

Thus the old helper vanished from translated guest execution, total guest
`dsound` samples fell 94.4%, and samples resolved in the native implementation.
This is direct evidence that the intended emulation layer was removed.

## What the numbers do not prove

Do not use these two autoload runs as an FPS A/B. The control screenshot ended
in evasion with several guards and later fell to roughly 14-16 fps, while the
candidate screenshot ended in a different fight state and stayed mostly around
24-26 fps. The dmsynth thread likewise differed (20.10% versus 1.57% in the CPU
windows). The scene, not only the patch, changed. The observed frame-rate gap is
therefore not attributed to patch 36/06.

The candidate may reduce the probability of SFX starvation because it gives the
mixer more CPU headroom. It does not yet explain or fix the persistent-buffer
control/lifetime defect if that remains reproducible.

## Evidence

```text
logs/rg353vs/dsound-native-fir-20260813/control/
logs/rg353vs/dsound-native-fir-20260813/control-fixed/
logs/rg353vs/dsound-native-fir-20260813/native-fixed/
logs/rg353vs/dsound-split-20260813/
```

The first automatic launch accidentally used `launch-p30.sh`, which ignored the
requested DLL. Hash verification detected the mismatch, and that run was
discarded before any conclusion. The retained runs use `launch-play.sh` and
verified mounted hashes.

## Promotion and rollback

Promoted on 2026-08-13 after the player confirmed the candidate looked normal
in play. FINALPLAY4 selects:

```text
MGS2_BOX86_BIN=box86-native-dsound-fir1
MGS2_DSOUND_DLL=dsound_p36_native_fir_target.dll
MGS2_DMSYNTH_DLL=dmsynth_p34_interp_reset.dll
MGS2_BOX86_NATIVE_DSOUND_FIR=1
```

Rollback is immediate: set `MGS2_BOX86_NATIVE_DSOUND_FIR=0`, or select the
previous FINALPLAY3 pair `box86-native-memmove3` plus `dsound_se1.dll`.

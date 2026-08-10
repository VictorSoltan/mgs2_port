# MGS2 RG353VS — `dmime_transition1` candidate

Date: 10 August 2026. Status: built, deployed and exercised through the
regression sequence; it did **not** prevent a later battle/Start SFX loss. This
remains a semantic correction, but is not the sufficient gameplay fix.

## Why this replaces patch 14

The user repeatedly observed two-way state changes: Start/map and enemy-alert
transitions can either remove gameplay effects or restore them. Patch 14
(`dmsynth_se4_unmute1.dll` with `MGS2_DMSYNTH_UNMUTE_NOTES=1`) was loaded and
enabled during a reproduction that still became silent. It is therefore
disabled by default in the new wrapper configuration.

The surviving code path is more direct. `seqtrack.c` supplies full
`DMUS_CURVE_PMSG` objects, but the old `performance.c` emitted only one
controller change at `nStartValue`. It ignored the target, duration and reset.
`PlaySegmentEx()` also discarded the caller's `AudioPath`, even though the port
already implements the PChannel conversion that path owns.

## Patch 15 scope

`wine-patches/15-dmime-transition-recovery.patch` changes only `dmime`:

1. Retains the selected `IDirectMusicAudioPath` in each segment state; remaps
   MIDI, note, curve and patch PChannels before the performance graph; and uses
   the same path for automatic download/unload.
2. Delivers each CC curve as start → endpoint → optional reset. Curves are not
   interpolated sample-by-sample: Wine's MIDI backend accepts discrete CC
   events, so this is the safe semantic minimum that stops a transition from
   remaining at its initial attenuation.
3. Emits the reset when a pending reset-curve is flushed, implements the
   built-in tool's `Flush`, and makes `Invalidate`, `StopEx`, and `pFrom`
   participate in segment/path cleanup.
4. Implements `IDirectMusicAudioPath::SetVolume()` only for immediate
   (`dwDuration == 0`) volume updates. Timed DirectSound fades remain explicitly
   unsupported rather than silently succeeding.

`Activate(TRUE)` is intentionally unchanged. Its observed behaviour needs a
separate reproduction; this patch does not introduce a buffer restart.

## Artefacts and verification

* `binaries/dmime_transition1.dll`
  SHA-256: `ce3e3f14a62a190966183802c871a5a26a7a3a828c7f23b4d6f0ab9f90ace877`
* Patch SHA-256:
  `d3cf39095a70f6ea5c0fa39898b1187023c1e4cc6b1b637eca288be9653cb5fa`
* The release i386 DLL and the `dmime` test executable both compile cleanly.
  The full test runner cannot run in this workspace because its Unix Wine
  server (`build-wine-i386/server/wineserver`) was not built.
* The patch applies to a fresh Wine 11.0 archive after patches 1–14 with
  `patch -p1 -F0 --dry-run` and zero fuzz.

## Console test and rollback

The menu wrapper now selects `dmime_transition1.dll` and leaves
`MGS2_DMSYNTH_UNMUTE_NOTES=0`. It was deployed to both copies of the menu
wrapper:

```text
/storage/roms/ports/MGS2-Substance.sh
/storage/roms/ports/MGS2-Substance/MGS2-Substance.sh
```

The external copy had still explicitly exported `dmime_se1.dll` and patch 14;
that initial restart correctly launched MGS2 but loaded the old DLL. Both files
are now byte-identical to the staged wrapper. The old files are retained as
`*.before-dmime-transition1` beside each target.

The final restart has exactly one game process (PID 22710 at verification),
the live `/usr/lib/wine/i386-windows/dmime.dll` SHA-256 matches
`dmime_transition1.dll`, and the game environment contains:

```text
MGS2_DMIME_DLL=dmime_transition1.dll
MGS2_DMSYNTH_UNMUTE_NOTES=0
```

The first follow-up battle loss and a later Start/map/return loss both remained
silent with this DLL verified as loaded. The subsequent DMSynth/DirectSound
snapshot found no exact-zero CC7/CC11 mute, and the pre-existing synth recorder
saw no new event during that later Start action. The next experiment is the
bounded `dmime` capture in `MGS2_DMIME_STATE_CAPTURE_2026-08-10.md`, not a
broader controller workaround.

To revert only this candidate, start with:

```sh
MGS2_DMIME_DLL=dmime_se1.dll MGS2_DMSYNTH_UNMUTE_NOTES=0
```

If silence recurs, enable the bounded recorder before reproducing once; do not
turn on a hot per-message trace.

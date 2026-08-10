# MGS2 RG353VS — bounded `dmime` capture

Date: 10 August 2026. Status: diagnostic candidate, built but not yet measured
on the console. It is a single-reproduction instrument, not a gameplay fix and
not the production default.

## Why a new boundary is needed

The latest live loss survived patch 15 (`dmime_transition1.dll`). The available
snapshot makes two earlier explanations inapplicable to that observation:

* DMSynth channels 0 and 1 had CC7/CC11 values 126/127 and 127/127. An exact
  zero controller is therefore not muting that state.
* The bounded DMSynth ring was enabled after the preceding battle loss. During
  the later Start/map/return action it received no new MIDI, note, program or
  bank entry. This is useful only for the Start action; it cannot reconstruct
  the battle that happened before the recorder was enabled.

The unresolved question is now where a newly requested effect stops: before
DirectMusic stamps its PChannel, while it resolves that channel/port, or after
it hands MIDI to the port. The recorder sits at exactly those boundaries and
does not write stderr, files, or PipeWire data from a hot thread.

## Patch 16 and artefacts

`wine-patches/16-dmime-state-recorder.patch` adds a fixed 256-record, process
memory-only ring to `dmime`. It is enabled only when the process starts with
`MGS2_DMIME_STATE=1`.

* `binaries/dmime_state1.dll`
  SHA-256: `a4d3c87901c733f6849fe93e76875d0dea8aed35d20a92f2936d0ae08c8edae3`
* Patch SHA-256:
  `c54ea9647d0ca0307204b2bce9fa186bf7c05ea2d2b0d36c72a40dedb3b831b3`
* `harness/dmime_state.py` reads it once through `/proc/<pid>/mem`; it does not
  attach, trace, or poll the game.

The release i386 DLL compiled cleanly. The patch was regenerated against a
fresh Wine 11.0 tree with patches 1–15 applied, then `patch -p1 -F0 --dry-run`
accepted it with zero fuzz. The workspace lacks a built Unix Wine server, so
the normal Wine test runner cannot be executed here.

## What each outcome means

| Ring observation during a new SFX attempt | Narrow conclusion |
| --- | --- |
| No `stamp_in` / `play_segment` change | The action did not reach the captured DirectMusic segment path. Inspect the game's transition/track scheduling next. |
| `stamp_fail` or `path_convert` failure | The selected AudioPath/PChannel route is rejected; fix that path before touching synthesis. |
| `stamp_out` but `midi_drop` | DirectMusic accepted the event but cannot resolve its port/channel. |
| `midi_port`, then no new DMSynth entry | The hand-off between the DirectMusic port and synth is the next boundary. |
| `midi_port` and DMSynth entries while silent | MIDI reaches synthesis; compare voices and DirectSound mixer state, not controller-zero folklore. |

The last 256 events are intentionally all that is retained. Capture immediately
after the user reports silence so normal menu/background traffic cannot overwrite
the triggering transition.

## Device run and rollback

For exactly one session, start the normal menu wrapper with:

```sh
MGS2_DMIME_DLL=dmime_state1.dll MGS2_DMIME_STATE=1 \\
MGS2_DMSYNTH_UNMUTE_NOTES=0 /storage/roms/ports/MGS2-Substance.sh
```

The outer wrapper honours supplied values, so neither menu wrapper needs an
edit. Verify the bind-mounted `dmime.dll` hash and the game environment before
playing. Immediately after a loss, save `dmime_state.py` and the existing
`dmsynth_state.py` / `dsound_live_state.py` outputs together.

Rollback is simply the normal wrapper launch with no overrides (currently
`dmime_transition1.dll`, recorder off). Do not leave `MGS2_DMIME_STATE=1`
enabled for normal performance play.

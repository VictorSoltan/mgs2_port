# Game compatibility patch records

This directory contains source-equivalent, reviewable records for compatibility
changes applied to a legally installed copy of the game. It does not contain a
game executable, assets or redistributed game code.

FINALPLAY21 uses `01-wpatch-fixed-function-fallback.patch`. The recovered source
file has CRCRLF endings, so verify/apply that record with `patch --binary`. The
device launcher performs the shipped-image equivalent through
`device/patch-mgs2-wpatch-novs.sh`: it accepts only the SHA-256-pinned original,
changes one recorded byte in a temporary copy, verifies the complete output
hash and bind-mounts it only for that launch.

The 2026-08-28 flicker follow-up, promoted in FINALPLAY22, is recorded as
`02-wpatch-consumer-and-state-isolation.patch`. It keeps FINALPLAY21's water
fallback, preserves the original shader path for the only non-water external
wpatch consumer, and closes fixed-function lighting at the plugin tail. The
candidate helper validates the original instructions and executable cave,
changes only a temporary hash-pinned game view and has its own exact rollback.
The owner accepted the still-open delayed visual witness for promotion.

`03-render-state-shadow-nop-candidate.patch` corrects both source definitions
of the unused `DG_NopRenderState` helper so its shadow records `Value`, not the
state enum. No caller exists in the recovered source or map, so it deliberately
has no executable transform and is not a gameplay candidate.

`04-wpatch-texture-transform-ownership-candidate.patch` adds the missing local
ownership rule to the non-vertex-shader patch renderer: stage 0 is latched to
`D3DTTFF_COUNT2` immediately before each UV matrix upload. This prevents EVM,
shadow and CMF renderers from deciding whether the water transform is enabled.
The matching helper retains candidate 02's consumer isolation and lighting
cleanup, validates every overwritten instruction and executable-code cave, and
produces a separate exact temporary image. FINALPLAY22 promotes that image;
FINALPLAY21 remains its exact one-byte-view rollback.

`05-wpatch-latent-safety-corrections.patch` closes the remaining source-level
wpatch findings. It keeps the fallback selected if device creation drops to
software vertex processing, gives the unreachable bump-map dispatch a defined
function, and checks the IPU-panel allocation before dereferencing it. The
FINALPLAY22's state-ownership helper includes the software-VP flag as a second fail-closed
one-byte change; the unreachable dispatch and OOM guard remain source-only.

`06-movie-null-graph-guard.patch` is independent of the wpatch records and is
the only one here that closes a crash reproduced in ordinary play.
`WindowsMpegInit()` logs a failed `CoCreateInstance(CLSID_FilterGraph)` and
returns, `MpegDecFirstRend()` calls `RCTInit()` before it checks
`WindowsMpegInitFlag`, and `WinstrmSendIPic()` never checks at all. In the
shipping port executable `WindowsMpegInit()` is stubbed with `ret`, so the graph
pointer is NULL for the whole process and the first movie trigger faults at
VA `0x0087AE0F`. The record moves the existing flag test above `RCTInit()`, adds
the missing test to `WinstrmSendIPic()` and makes both clock helpers check the
graph. FINALPLAY23 applies the bounded equivalent: `ret` at offsets 4696000 and
4697600 of the hash-pinned temporary view. Movie playback was already disabled
before this and remains so -- see `docs/MGS2_PROJECT_STATE.md` section 6d.

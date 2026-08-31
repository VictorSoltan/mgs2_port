# Repository bug audit and the FINALPLAY21 flicker report

Date: 28--29 August 2026
Production at audit time: FINALPLAY21 (git `50c6cd4`)
Status: **actionable findings implemented; selected fixes promoted as FINALPLAY22 by owner directive.**
FINALPLAY22 is current production; FINALPLAY21 is the exact rollback. The
shared launcher fixes L1--L5 were exercised
on the RG353VS. The final P1/P3 state-ownership image `d902ee43...` now passed
exact `21/21` identity, a pixel-gated save load, four movement bursts and four
attacks. The Wine audio candidate also passed exact `21/21` identity, a loaded
save, four movement bursts and eight attacks with its exact live DLL mappings.
The deployed combined FINALPLAY22 then independently matched all 21 live rows,
loaded save row 07 through the normal external entry and completed four
movement bursts and four attacks without a new GPU fault.
An RTC wake completed after 20 seconds, but the device did not restore either
IPv4 or IPv6 networking, so post-resume automated attacks and the SFX-survival
gate could not be run. E7 remains explicitly skipped at the owner's request.

## 1. Why this brief exists

The owner reported a new visual defect on FINALPLAY21 and asked for the
project's defects to be written down before any of them are acted on:

> Objects start to flicker. The picture itself flickers slightly, as if some
> stray objects appear in the frame. Possibly because of the recent fix that
> brought the water back, but that is not certain.

This is the register. Section 2 handles the reported flicker. Section 3 is the
audit of everything else. Section 5 states what was **not** audited, because the
audit was cut short.

The visual candidate did not pass every original promotion gate before the
owner directed its FINALPLAY22 promotion. Individual
audit findings carry a provenance tag:

- **measured** — reproduced on this workstation by running the check;
- **device-measured** — run on the RG353VS with the route and loaded bytes
  verified;
- **read** — established by reading the code, no execution;
- **unverified** — asserted by an audit agent, not independently checked.

The original multi-agent audit was not adversarially verified. The direct
follow-up below independently re-read the relevant source and executable bytes,
ran the static gates and exercised the candidate on the device; its remaining
visual caveat is stated explicitly.

## 2. The flicker report

### 2.0 Direct follow-up on 28--29 August

The owner's extra observation is that the artefact begins only after some time
in gameplay. Static and device work produced these results:

- The original H1 below is **refuted**. The recovered Windows implementation of
  `__RSQRT` returns `0.0f` when the square root is at or below `FLT_EPSILON`;
  `_sceVu0Normalize` therefore maps a zero vector to a zero vector, not NaN or
  Inf. The original audit had not found this body. **read**
- The dynamic vertex-buffer wrap is not an accumulating fault: when the bounded
  buffer fills, `DG_SetDynamicVertexBuffer` rewinds to offset zero with
  `D3DLOCK_DISCARD`; wpatch LOD and local vertex counts remain bounded. Both VS
  and non-VS wpatch paths upload the same vertex count. **read**
- The external consumer census is small and decisive. Water is created by
  `huge_sea.c` and `wave2.c` through `wave6.c`; the only non-water external
  consumer is `ipupanel.c`, the no-wrap IPU movie/display panel. FINALPLAY21's
  global flag therefore changed that panel as well as water. **read**
- The non-VS path enables fixed-function lighting and installs patch-local
  matrices/lights, while the plugin tail restores neither lighting nor those
  lights. This is a genuine state leak. A later actor or a newly activated IPU
  panel gives the reported delay a scene/draw-order mechanism; it need not be a
  timer or an ever-growing buffer. **read**

The bounded candidate consists of two source-equivalent changes in
`game-patches/02-wpatch-consumer-and-state-isolation.patch`:

```c
if (DG_CheckPatchUseVertexShader() || (patch->flag & DG_PATCH_NO_WRAP))
    /* original vertex-shader path */

/* wpatch plugin tail */
DG_SetRenderState(D3DRS_LIGHTING, FALSE);
```

The legal game EXE is still never stored or overwritten. The fail-closed helper
accepts only original SHA-256 `29759e6f...`, validates every replaced
instruction and the unused executable tail, generates temporary SHA-256
`e4a54598...`, and changes 36 bytes total including `.text`'s bounded virtual
extent. `WPATCH_ISOLATION_CANDIDATE.manifest` verified `21/21` live objects.
FINALPLAY21 (`6686b3fa...`) and FINALPLAY20 remain exact rollbacks. **measured**

The first device attempt used temporary image `9684c1cd...`. It survived about
eight minutes of movement, but its late screenshot phase was stopped by the
external reader's stale dmime state address (`bad dmime state signature at
0x1fa96160`). Subsequent disassembly review also found that its lighting reset
was attached to the preceding texture-address helper, whose call is conditional
on the game's state cache. That image is withdrawn: a reset skipped when the
address was already clamped did not implement the recorded unconditional C
tail. Preserve both failures; neither is evidence for or against the visual
symptom. **device-measured/read, rejected candidate**

The corrected `e4a54598...` image instead routes the unconditional tail jump
through the lighting reset and then preserves the original jump into
`DG_CloseDmaTask`. On battery, one exact process used the pixel-gated loader to
select save row 07, confirmed a gameplay mean of `0.209`, completed 160
2.5-second direction holds over about eight minutes and performed 12 attacks.
Forty periodic frames and a following dense 48-frame late burst showed no stray
geometry on direct review. Across the 47 consecutive late-frame pairs,
normalised RMSE stayed between `0.00147662` and `0.00340060`, with no isolated
frame outlier. The late frame-set hash is `78bc76ca...`; the ignored local
evidence is under `logs/rg353vs/wpatch-isolation-e4a-20260828/`.
**device-measured**

This run started through the launcher's 1992 MHz path, but ended at 85.6 C with
the system cap reduced to 1608 MHz. Charger state remained `0`. It is a
correctness/visual survival result, not a controlled-clock performance result.
The separate exact row-09 save loaded `Shell 1-2 connecting bridge`. In a clean
`220x60` sea crop, each adjacent one-second frame changed `82.4%` to `85.5%` of
the pixels; the six-frame set hashes to `53dd2f60...`. Thus the corrected
candidate retains visible animated water. The active IPU display panel was not
triggered. The owner-reported artefact still was not reproduced on FINALPLAY21,
so this does not meet the promotion gate. **device-measured**

### 2.1 What FINALPLAY21 actually changed, restated exactly

FINALPLAY21 clears one immediate byte so that

```text
wdgd.c:1462   DG_WinApp.flag |= M_DG_WINAPP_PATCH_USE_VERTEXSHADER    (1 << 17)
```

becomes `or eax,0`. The flag is read only through
`DG_CheckPatchUseVertexShader()`, and that macro is consumed at exactly four
sites, all in `system/libdg/wpatch.c`: lines 201, 1127, 1482 (commented out)
and 1514. **read**

So the blast radius is confined to libdg's Bezier-patch renderer. Nothing
outside `wpatch.c` changes behaviour. `wdgd.c:1422` sets the same flag a second
time, but only inside the `D3DCREATE_SOFTWARE_VERTEXPROCESSING` branch, which
the port does not take; that byte was deliberately left alone. **read**

### 2.2 Hypothesis H1 — CPU normal normalisation in the fixed-function patch path

**Refuted by the implementation the original audit missed.**

The executable statement difference between `DrawPatch` and
`DrawPatchNVS_Normal` is real, but the inferred zero-division is not. In
`include/mgs_type.h`, `__RSQRT` computes the square root and returns its
reciprocal only when it is greater than `FLT_EPSILON`; otherwise it returns
zero. `_sceVu0Normalize` scales by that result. A zero cross product therefore
stays zero. This cannot create the proposed Inf/NaN normal and is not the chosen
fix. Preserve this rejection so the same guard is not proposed again. **read**

### 2.3 Hypothesis H2 — render state the fixed-function patch path leaves behind

**Confirmed code defect and basis of the bounded candidate; its late-frame
exercise passed, while symptom attribution still awaits an exact baseline
reproduction.**

The non-VS branch of `ChainObj` (wpatch.c:1252-1264) sets and never restores:
the FVF via `DG_SetVertexShader(D3DFVF_PATCHVERTEX)`, `D3DRS_LIGHTING = TRUE`,
`D3DRS_VERTEXBLEND = D3DVBF_DISABLE`, `D3DTS_WORLDMATRIX(0) = patch->world`,
and the D3D directional lights via
`DG_SetLightMatrix2Direct3D(&patch->light[0], &patch->light[1])`.
`PluginActor` (wpatch.c:1516-1517) additionally sets `D3DTS_VIEW` and
`D3DTS_PROJECTION` in the non-VS branch only, and the function's tail restores
nothing but `D3DRS_STENCILENABLE`. **read**

This matters more than it normally would, because `DG_SetRenderState` and
`DG_SetTransform` are shadow-deduped: they skip the D3D call whenever the new
value equals the game's own cached value (`wd3d.c:912-925` and `wd3d.c:941-995`,
with `__STATECHK_SETTRANSFORM__` = TRUE at `wd3d.c:38`). Leaked state therefore
persists until something explicitly sets it to a different value. **read**

Most other renderers in libdg set fog, lighting, view and projection at their
own entry, choosing the
0..1 or the world-space fog range from *its own* vertex-shader flag
(`wchain.c:330-344`, `wchain2.c:343-378`, `wprim2.c:2265/2576-2582`,
`wopt_cmf.c:938-985`, `wshdwchn.c:399-431`, `wcomdl.c:491-514`,
`wevmobjs.c:349-384`). That narrows the affected draw orders, but does not make
the leak safe: a consumer that does not reassert lighting can inherit it, and a
scene-activated patch consumer explains why the defect need not appear at
startup. The candidate closes lighting through the game's own cached wrapper,
so the D3D state and the shadow remain synchronised. **read**

One thing checked and **refuted**: the commented-out `scrpad->cp_eye` write at
wpatch.c:1482 is not a stale-read bug. The `cp_eye` field itself is commented
out of the scratchpad struct at wpatch.c:267 and has no readers. **read**

### 2.4 Hypothesis H3 — the flicker is not FINALPLAY21's

Two independent reasons to hold this open.

- **A charger-dependent flicker is already on record.** From
  `MGS2_TRANSITION_HITCH_RESEARCH_2026-08-12.md` §8: the flicker observed on
  12 August "reproduced only with the charger connected and disappeared on the
  same DLLs". That is a documented false positive for exactly this symptom,
  against an unchanged binary.
- The production DXT bridge remains intentionally silent, but the isolated B1/B4
  candidate has now passed its strengthened non-zero-stride self-test and
  externally witnessed both native conversion and a conservative guest
  fallback in live play. Direct disassembly also found that the B2/B3 address
  formula and lack of a source-window bound mirror the legal guest function.
  None of this supplies an independent bad-input or visual witness. See §3.2.
  **device-measured/read**

### 2.5 Completed and remaining gates

1. **Charger control:** the baseline and candidate exercises were run with
   charger state `0`. This excludes the known charger condition from those
   captures, but the owner-reported artefact itself was not reproduced in the
   controlled scene. **device-measured**
2. **FINALPLAY21 baseline:** an exact `21/21` launch and a 48-frame external
   burst after roughly eight minutes idle were clean. This is not a refutation
   of a symptom reported only after active play. **device-measured**
3. **Candidate correctness:** exact `e4a54598...` helper output, 36 changed
   bytes, source patch dry-run, `21/21` live identity, cold load, gameplay, 160
   movement holds, 12 actions, 40 periodic frames and a clean 48-frame late
   burst passed. A second cold row-09 load showed animated water, with
   `82.4--85.5%` changed pixels per second in a clean sea crop. The final
   thermal caps make these no performance results. **device-measured**
4. **Still required for promotion:** reproduce the owner's late artefact on
   FINALPLAY21 at one fixed scene for one-variable attribution, then repeat that
   exact scene on the candidate. Trigger and check the IPU/movie panel; animated
   water has passed. FINALPLAY20 remains the missing-sea control.

Do not merge this with any previously named freeze or artefact signature.
AGENTS.md rule: new occurrences are captured and named, not attributed by
resemblance.

## 3. Findings register

36 findings. Severity is the auditor's, not a measured impact.

### 3.1 Rendering — the FINALPLAY21 patch path (3)

| # | Sev | Finding | Where | Prov |
|---|-----|---------|-------|------|
| A1 | rejected | Zero-normal-to-NaN mechanism is false: `__RSQRT` returns zero at/below `FLT_EPSILON`, so a zero normal remains zero. See §2.2. | `mgs_type.h:__RSQRT` | read |
| A2 | medium | Non-VS patch branch sets FVF, `D3DRS_LIGHTING`, `VERTEXBLEND`, `WORLDMATRIX(0)`, the D3D lights, `D3DTS_VIEW` and `D3DTS_PROJECTION` and restores none of them. The corrected isolated candidate closes lighting on the unconditional plugin tail and preserves the shader path for the sole non-water consumer; its active late frames were clean, while attribution remains open. | `wpatch.c:1252-1264`, `wpatch.c:1516-1613` | device-measured candidate |
| A3 | source candidate | `DG_NopRenderState` wrote the *state enum* into the shadow instead of the value. Patch 03 changes both the out-of-line and inline definitions to store `Value`; it applies exactly to the recovered source. The source and map contain no caller, so no legal-image transform was created and this is not a gameplay or flicker candidate. | `game-patches/03-render-state-shadow-nop-candidate.patch` | read; exact dry-run |

### 3.2 Box86 native DXT surface bridge (5) — production, silent

This is the fused DXT5 decode in `box86-fp26-...-production`. In FINALPLAY21 it
runs with verification off and hot counters removed.

| # | Sev | Finding | Where | Prov |
|---|-----|---------|-------|------|
| B1 | candidate fixed | Patch 27 replaces the degenerate arming fixture with two DXT5 blocks, non-zero source/destination strides, non-zero block offsets and a non-identity slot. It exercises all three source-offset multipliers, the `f[0x1090]` anchor, cache reuse/interleave and colour-key fallback before arming. | `box86-patches/27-dxt-surface-selftest-witness-candidate.patch` | measured regression; device-measured arming |
| B2 | reclassified | The differing block/sub-row anchors are real, but direct disassembly shows the native formula is byte-for-byte equivalent to the legal guest converter. This is not a bridge divergence; an invalid unaligned-input effect remains unproven. | same patch:186; legal guest disassembly | read |
| B3 | reclassified | The native path has no independent source-window bound, but neither does the legal guest converter whose address arithmetic it reproduces. This is not a native regression without a separate out-of-range-input witness. | same patch:205; legal guest disassembly | read |
| B4 | candidate fixed | Production remains counter-free. Patch 27 instead exports a fixed six-word, one-way witness: strong self-test, armed, intercepted, native-seen, guest-seen/failed and first fallback reason. The hot path performs no logging and no per-call counter; each flag and the first fallback value can latch only once. The external reader refuses malformed, unarmed and guest-failed states. | patch 27; `harness/box86_dxt_stats.py` | measured regression; device-measured |
| B5 | reclassified | Exact legal-EXE disassembly proves the copied function is precisely `0x2a9` bytes, from VA `0x9115da` to the next function at `0x911883`. Its only four external direct relative calls are at offsets `0x005`, `0x03c`, `0x058`, `0x16e`; all other relative transfers stay inside the copied window and preserve their displacement. The current route is therefore safe. A generic signature match against an unpinned different build remains outside this closed route. | legal guest disassembly; locked original EXE | read/executable |

Patch 27 (`47556e55...`) produced candidate Box86 `6522542c...`; its 21-row
manifest passed `21/21` live identity. One cold device run loaded save row 07,
completed 20 movement bursts and four actions, then the external reader
reported `strong_selftest=1`, `armed=1`, `intercepted=1`, `native_seen=1`,
`guest_seen=1`, `guest_failed=0`, first fallback `cache`, verdict `MIXED`.
The old research counters remained zero by design. This is a correctness and
route-observability result, not a performance result and not evidence that a
particular frame used bad texture data. Shutdown left zero game processes and
zero game-image mounts; normal FINALPLAY21 is the exact rollback.
**device-measured**

The FINALPLAY21 and wpatch-candidate transforms do not change the converter
window: their fail-closed helpers verify exact input/output images and the
complete changed-byte sets are one byte at `0x4a294a`, or 36 bytes at the
recorded wpatch flag/calls/caves and PE section-size field. The bridge's content
signature is therefore unchanged. Together with the exact function-boundary
disassembly, this closes B5 for every currently locked game-image route.

### 3.3 DXVK production patches (4)

None of these is reachable as a cause of the reported flicker; recorded for
completeness.

| # | Sev | Finding | Where | Prov |
|---|-----|---------|-------|------|
| C1 | source candidate | Clip/cull *capability* was gated on output plane counts while the builtin declaration was gated on the feature option. Patch 10 enables the module capability directly from the enabled Vulkan feature for VS/HS/DS/GS and PS, covering input-only use. The DXBC path is unreachable by this D3D8 game. | `dxvk-patches/10-dxbc-feature-caps-candidate.patch` | read; exact dry-run |
| C2 | source candidate | Patch 01 drops unsupported D3D9 user clip planes without changing caps. Patch 10 reports `MaxUserClipPlanes=0` when `shaderClipDistance` is absent. The RG353VS lacks that feature, but MGS2 contains no `SetClipPlane` or `D3DRS_CLIPPLANEENABLE` call. | patch 10 | read; exact dry-run/device feature read |
| C3 | source candidate | Patch 09 checks a null result from `Direct3DCreate9` and raises the same cold-path `DxvkError` boundary as missing `d3d9.dll`/export, instead of constructing `D3D8Interface` around null. | `dxvk-patches/09-d3d8-init-failure-diagnostics-candidate.patch` | read; exact dry-run |
| C4 | source candidate | Patch 09 keeps the hidden user-driver priming window non-fatal but emits one existing cold-start logger warning when its creation fails, so the failure is attributable. | patch 09 | read; exact dry-run |

Both candidates apply with fuzz disabled after their declared production patch
against pinned DXVK-Sarek commit `617958fe...`. Patch 09 hashes to
`0231a814...`; patch 10 hashes to `094d6cc9...`. The exact cross-build setup is
not present locally, so neither was compiled, device-run or added to
`device/FINALPLAY.lock`; the production DLLs and rollback are unchanged.

Patch 08 was also re-read against that exact source. It scans only the
`equal_range(shader)` entries and suppresses insertion only when the complete
pipeline key compares equal. It cannot return or bind a pipeline for a
different state vector; no defect was found in this scope. **read**

### 3.4 Release identity and gates (9)

| # | Sev | Finding | Where | Prov |
|---|-----|---------|-------|------|
| D1 | fixed | The three stale FINALPLAY16 launcher rows and four stale FINALPLAY17 rows were regenerated from the present tracked files. FINALPLAY18-21 engine rows were updated after adding the closed candidate case; all four current production gates pass. | `device/FINALPLAY16_PRODUCTION.sha256`, `FINALPLAY17_PRODUCTION.sha256` | **measured** |
| D2 | fixed | The legacy WineD3D mode now copies its launcher into the ignored release directory and applies substitutions only to that staged copy; deploy installs the staged copy last. No tracked hashed launcher is edited after its gates. | `harness/make_release.sh` | **measured** static gates |
| D3 | implemented; E2E pending | Normal `make_release.sh` now dispatches to a FINALPLAY21 packager. It derives 17 current rows plus the three carried audio DLLs, rejects game-EXE/system rows, verifies every SHA-256, handles the parent PortMaster entry separately and can re-hash all 20 deployed files. Local fail-closed/static gates pass. A device-backed E2E attempt was stopped before execution by the environment's transfer policy: copying the 20 proprietary/runtime objects into an ignored workstation bundle requires the owner's explicit, payload-specific approval. No release directory was produced. | `harness/make_current_release.sh`, `harness/make_release.sh` | **measured** fail-closed/static; policy-blocked E2E |
| D4 | fixed | Each closed route now declares its exact manifest row count (18/19/21); the launcher requires equality and still separately requires at least one row per bind. Deleting or adding rows fails closed. | `device/launch-play-dxvk-fp17.sh` | **measured** |
| D5 | fixed | Both game-image helpers accept output only under their private top-level `/tmp/mgs2-wpatch-*` pattern and reject symlinks/in-place edits. The production gate exercises the restriction. | `device/patch-mgs2-wpatch-novs.sh` | **measured** |
| D6 | clarified | Source-patch and helper hashes are always pinned. The gate now reports whether the legal-image transform was actually executed (`executed`) or only hash-pinned; on this workstation it executed and verified the exact one-byte diff. | `harness/test_finalplay21_production.sh` | **measured** |
| D7 | fixed | The gate now asserts the engine's embedded helper hash and mounted output hash against its constants. | `harness/test_finalplay21_production.sh` | **measured** |
| D8 | fixed | FINALPLAY21 again cross-checks the recorded gptokeyb and dmsynth hashes. | `harness/test_finalplay21_production.sh` | **measured** |
| D9 | fixed | Both sides of the manifest difference filter comments and blank lines. | `harness/test_finalplay21_production.sh` | **measured** |

All four `test_finalplay{18,19,20,21}_production.sh` gates pass on the current
tree. **measured**

### 3.5 Launcher and documented device operation (7)

| # | Sev | Finding | Where | Prov |
|---|-----|---------|-------|------|
| E1 | fixed | The stop procedure now terminates the real shared launcher first and explicitly forbids deleting the lock name while a launcher may own its inode. | `docs/DEVICE.md` | read |
| E2 | fixed | The fallback unwind includes app-local D3D8, prefix D3D9, the temporary game-image bind and both bounded backing-file patterns. | `docs/DEVICE.md` | read |
| E3 | fixed | The stop procedure matches the real truncated `gptokeyb-mgs2-i` comm. | `docs/DEVICE.md` | read |
| E4 | fixed | Live verification now hashes every path in the selected 21-row manifest; it no longer recommends obsolete WineD3D/island files for a DXVK route. | `docs/DEVICE.md` | read |
| E5 | fixed | Save repair now points at the production direct32 prefix, `wineprefix11-x86-dxvk-test`. | `docs/DEVICE.md` | read |
| E6 | fixed | Lock contention now exits nonzero with an explicit second-instance diagnostic. | `device/launch-play-dxvk-fp17.sh` | **measured** static gate |
| E7 | medium | Start+Select has no hold gate. `mgs2.gptk` maps `back = enter` and `start = tab`, and the immediate patch removes the release-deferral while leaving `doKillMode()` armed, so the chord injects a confirm keystroke and then SIGKILLs the game on the next edge — including mid-save. Explicitly deferred at the owner's request; no code or route was changed. | `device/mgs2.gptk:3` | unverified; owner-deferred |

### 3.6 Harness and measurement tooling (8)

These do not affect gameplay. They affect whether this project's numbers mean
anything, which is why they are recorded rather than dropped.

| # | Sev | Finding | Where | Prov |
|---|-----|---------|-------|------|
| F1 | fixed | The present-counter reader now refuses an export-lookup failure. A manually supplied RVA remains possible only through the explicit `--rva` research override; there is no hardcoded fallback. | `harness/dxvk_present_count.py` | **measured** regression |
| F2 | fixed | `--refresh` now builds the Wine patch body from the complete old/new trees, including files added under new directories. It refuses empty one-sided files and non-text differences that a traditional patch cannot reproduce. | `harness/fail_closed_diff.sh`, `harness/verify_rebuild.sh` | **measured** reconstruct regression |
| F3 | fixed | Base identity requires two nonempty equal hashes; empty output can no longer equal an absent lock value. | `harness/fail_closed_diff.sh`, `harness/verify_rebuild.sh` | **measured** regression |
| F4 | fixed | A wined3d byte mismatch now fails `--build` even when `candidate_in_tree` explains it; the explanation remains, but no longer changes the exit gate. | `harness/verify_rebuild.sh` | **measured** static regression |
| F5 | fixed | The work-normalised sign test now uses the smaller of the two exact binomial tails, drops ties, and gives the same p-value for equally strong improvements and regressions. | `harness/island_ab_read.py` | **measured** regression |
| F6 | fixed | A zero routed or unrouted frame count now refuses the run before work normalisation. | `harness/island_ab_read.py` | **measured** regression |
| F7 | fixed | `.env` parsing preserves embedded `#`, quoted/escaped repeated spaces and shell-style trailing comments. Ambiguous unquoted multiword values fail instead of being silently collapsed. | `harness/repo_env.py` | **measured** regression |
| F8 | fixed | The dmime state reader no longer assumes stale RVA `0x26160`. By default it scans at most 8 MiB across readable mappings whose basename is exactly `dmime.dll`, requires one exact 24-byte DMT1 header and refuses no match, multiple matches and oversized scans; `--rva` remains an explicit research override. Production autoload invokes it only when `MGS2_DMIME_STATE` is opted in, because the shipped transition DLL has no DMT1 recorder. | `harness/dmime_state.py`, `harness/autoload_save.py` | **measured** regression; device-measured locator |

The shared regression is `harness/test_audit_tooling.sh`. It reconstructs a
synthetic tree with modified, deleted and newly added nested files, proves the
empty-file refusal, and exercises the Python failure boundaries above. These
are workstation tooling checks and make no device-performance claim.

`harness/test_dmime_state_locator.py` covers a header split across read chunks,
missing and duplicate headers, and the 8 MiB refusal. On a normal FINALPLAY21
process the reader correctly refused the production DLL as having no DMT1
header. A bounded read-only device mapping of diagnostic DLL SHA-256
`2b9f1263...` was then found at RVA `0x150c0` with a valid zeroed recorder; the
temporary mapping and file were removed. **measured/device-measured**

### 3.7 Scopes closed by the 29 August gap audit

A second workflow ran the six scopes §5 had listed as unaudited. Seven of nine
agents completed; only two adversarial verifiers died on the spend limit, so
these began as one-pass findings unless a row says otherwise. The direct
follow-up statuses below supersede that original provenance; candidate work is
still not a production claim.

#### 3.7.1 wpatch fixed-function path, remaining (5)

The two flicker-direct rows below are **not** addressed by the isolated
candidate in §2.0, which changes only the IPU-panel consumer and the lighting
tail.

| # | Sev | Finding | Where | Prov |
|---|-----|---------|-------|------|
| P1 | candidate fixed | The non-VS branch did not own `D3DTSS_TEXTURETRANSFORMFLAGS`, so EVM/shadow/CMF draw order could disable or project the water UV matrix. Patch 04 now selects stage-0 `COUNT2` immediately before the matrix upload. Final image `d902ee43...` passed exact 21/21 device identity and a loaded-save movement/action run. | `game-patches/04-wpatch-texture-transform-ownership-candidate.patch` | measured transform; device-measured smoke |
| P2 | refuted current route | A fail-closed live read found `DG_WinApp.flag=0x0019e003`: bit 8 (`USE_VERTEXSHADER`) is clear and bit 17 is clear. Therefore global fixed-function material/colour-source setup executes on this route. This does not remove P1's later inter-renderer state pollution. | `harness/mgs2_winapp_flag.py`; `wd3d.c:331-360` | device-measured |
| P3 | candidate fixed | The software-VP startup branch re-enabled the patch shader. Patch 05 removes it in source; the current helper additionally clears the exact immediate byte at file offset `0x4a28ba`. | `game-patches/05-wpatch-latent-safety-corrections.patch`; `device/patch-mgs2-wpatch-state-owned.sh` | measured exact 58-byte transform; device-measured smoke |
| P4 | source fixed | The unreachable bump-map case had an uninitialised indirect draw target. Patch 05 gives the non-VS branch a safe normal default and mirrors the VS branch's assertion. Both game assignments remain commented out, so no executable transform or gameplay claim was made. | `game-patches/05-wpatch-latent-safety-corrections.patch` | read; exact dry-run |
| P5 | source fixed | The IPU panel now checks `DG_MakePatch` before dereferencing the result. This is an OOM-boundary source correction, not a reproduced device failure. | same | read; exact dry-run |

Two rows were **refuted** while checking and are recorded so they are not
re-proposed: the `wevmobjs` variant of P1 (the two flags make the pairing
self-consistent, and any leak would be sticky rather than per-frame —
adversarially verified, high confidence), and `D3DRS_FOGCOLOR`, which the sea's
`DG_PATCH_FOGBLACK` path sets at `wpatch.c:1355` and restores at
`wpatch.c:1439`. **read**

The consumer census also corrects the promotion brief's scope claim. Six
registered actors build `DG_PATCH`es, so the flag change reroutes roughly 32
non-sea instances as well: `huge_sea.c` (NORMAL, 8 stages), `wave2.c` stormy
river (two NORMAL meshes, 7 stages), `wave4.c` reflection water 2
(`REFLECTPLANE` → `DrawPatchNVS_EMap2`, 3 stages), `wave6.c` passage water
(NORMAL, 10 stages), `wave5.c` sea (`REFLECTPLANE2` → `DrawPatchNVS_EMap`, 48
stages) and `ipupanel.c`. All but the last are water, which is why the §2.0
census reached the same practical answer. Separately, the device-reset state
machine never calls `CreateDevice` and never touches `DG_WinApp.flag`, so the
"flag re-set after a device reset" theory for the delay is **refuted**.

#### 3.7.2 Launcher deep audit (6)

| # | Sev | Finding | Where | Prov |
|---|-----|---------|-------|------|
| L1 | fixed | HUP/INT/TERM now disarm the traps, run idempotent cleanup and exit with 129/130/143. TERM on-device left no fallback game, Wine or Box86 process and no mounted candidate. | `device/launch-play-dxvk-fp17.sh` | device-measured |
| L2 | fixed | Cleanup removes the temporary game image only after the game bind is gone; a busy image is preserved and reported. | same | measured regression; device-measured clean path |
| L3 | fixed | The original boot ID, CPU governors/caps and GPU governor are persisted mode 0600 in `/tmp/mgs2-cpu-baseline.state`. A SIGKILL test left it intact and the next run recovered the pre-launch `ondemand/1800000/simple_ondemand` baseline instead of latching performance. | same | device-measured |
| L4 | fixed | Clock writes now require write success and exact readback both when applying and restoring the controlled cap. Restore failure preserves the baseline for recovery. | same | measured regression; device-measured |
| L5 | fixed | Both inherited research controls are rejected before route selection and AABB is forced off in the closed engine. The island measurement arm is no longer reachable there. | same | measured regression |
| L6 | clarified | `MGS2_PRODUCTION_ROUTE` remains the intentional complete-bundle selector used by tracked wrappers. Comments now distinguish it from refused component overrides; every case still pins its own manifest and row count. | same | read |

#### 3.7.3 Wine audio runtime (6)

This scope was never audited before, and it produced the register's only other
critical. Two rows are a concrete mechanism for the long-open intermittent
gameplay-SFX bug in `MGS2_INTERMITTENT_SFX_HANDOFF_2026-08-10.md`.

| # | Sev | Finding | Where | Prov |
|---|-----|---------|-------|------|
| W1 | candidate fixed | Patch 84 moves private `curve_phase` before the variable-size public message and allocates from `offsetof(struct message, msg) + size`. i386 DWARF confirms `entry=0, curve_phase=8, msg=16`. | `wine-patches/history/84-dmime-message-private-state-layout.patch` | built/reconstructed; device smoke passed, fault-specific gate pending |
| W2 | candidate fixed | Patch 85 funnels every render-thread exit through cleanup and treats runtime `DSERR_BUFFERLOST` as a bounded recover/retry condition instead of killing the renderer. | `wine-patches/history/85-dmsynth-sink-lifetime-and-clock-state.patch` | built/reconstructed; device pre-resume smoke passed, post-resume gate blocked |
| W3 | candidate fixed | Both worker parameter blocks carry an explicit startup result; activation returns the real `Play`/`GetCaps`/allocation failure and never publishes false `active=TRUE`. Handles and thread-owned references are closed on every branch. | same | built/reconstructed; device activation smoke passed |
| W4 | candidate fixed | Write-position resync is factored and executed before patch-83 timeline rebase, so the new `activate_time` observes the post-underrun cursor. | same | built/reconstructed; device pre-resume smoke passed, post-resume gate blocked |
| W5 | candidate fixed | Activation resets written/play cursors, latency, rebase state and stop events; deactivate/reactivate recreates clean thread state. | same | built/reconstructed; device initial activation passed, reactivation gate blocked |
| W6 | candidate fixed | Both 64-bit `activate_time` readers now run under the sink critical section on i386/ARM32. | same | built/reconstructed; device smoke passed, race not forced |

With `SOURCE_DATE_EPOCH=1787976000`, two rebuilds produced identical
`dmime_p16` SHA-256 `f23f08ed...` and `dmsynth_p38` SHA-256
`22287685...`. Imports are unchanged and patches 84/85 reverse/reapply
with zero fuzz to the pinned Wine sources. The split host build has no runnable
`server/wineserver`, so the Wine unit executables were built but not run; do
not turn that infrastructure absence into a passing test claim. On device the
route verified all 21 manifest objects and loaded the FINALPLAY21 game image.
The live process namespace hashed `dmime.dll` to `f23f08ed...`, `dmsynth.dll`
to `22287685...` and the unchanged `dsound.dll` to `302eff54...`. The
pixel-gated row-07 save then completed four movement bursts and eight attacks
while `pw-record` captured the real PipeWire sink monitor into a finalised
23,690,924-byte WAV. This establishes startup and pre-resume survival, not that
the recorded mix audibly contains each gameplay SFX.

The same process entered `mem` suspend with an RTC alarm at epoch 1787995716
and printed `resumed_epoch=1787995716` after exactly 20 seconds. Immediately
after that response the RG353VS stopped answering IPv4 ARP; both recorded IPv6
addresses for its exact Wi-Fi MAC also remained unreachable. The post-resume
capture/action command therefore never ran. Preserve this as a platform
resume/network blocker, not a pass or failure of W2.

#### 3.7.4 Box86 Wayland bridge — audited, and largely a negative result (6)

§5 called this "the largest unaudited hole relevant to the report". It is now
audited and **it is not the flicker source.** The agent mechanically checked all
18 listener classes Wine 11.0 actually installs against the shipped protocol
XMLs and the bound versions: every table length, field order, initializer order
and all 120 thunk arities/format strings match, so no argument shift exists.
Production Wine 11 winewayland contains no `wl_surface.frame`/`wl_callback` use
at all, and the Vulkan swapchain's attach/release/frame traffic stays inside
native armhf libmali and never enters the bridge. `_Atomic(T*)` on ARMv7 is a
lock-free word with real `dmb`-backed ordering, and every listener is a
compile-time-initialised static, so patch 24 has no half-built-table window.
Guest thunk pointers belong to a driver that is never unloaded. **read/static —
not device proof that every Wayland failure mode is absent.**

The reachable Wine/MGS bridge remains clean. Strengthening the auditor did find
one real Box86 callback-format defect outside that reachable set (Y7), now
recorded in source patch 28:

| # | Sev | Finding | Where | Prov |
|---|-----|---------|-------|------|
| Y1 | fixed | The auditor now preserves protocol field order, compares Box86 struct-field order and separately compares the thunk-table initializer order. | `harness/wayland/audit_listener_abi.py` | measured regressions |
| Y2 | fixed | It requires the exact 18 listener classes Wine 11 installs, independently of the supplied header intersection; omitting one protocol header fails closed. | same | measured regressions |
| Y3 | fixed | Every wrapper's parsed C parameter signature is now compared with the actual `RunFunctionFmt` string. | same | measured regressions |
| Y4 | source candidate fixed | Patch 28 applies patch-24 release/acquire publication to `wl_buffer_listener` as well. The current Wine path had already been shown to register/dispatch each buffer on one private queue; this is a general race boundary, not a flicker attribution. | `box86-patches/28-wayland-audit-and-reproducible-build-boundaries.patch` | exact reconstruction; not built |
| Y5 | refuted current route | `primary_selection` is explicitly `since=2`, while Wine binds `zwlr_data_control_device_v1` version 1. The three-entry table is the exact v1 ABI and is retained as a declared omission. | Wine XML; auditor allow-list | read/measured audit |
| Y6 | source candidate fixed | Patch 28 generates a uniquely named revision header in each build directory and bounds the default-off raster dump to the structure's 13 32-bit words. | patch 28 | exact reconstruction; not built |
| Y7 | source candidate fixed | The strengthened format audit found `zwp_pointer_gesture_pinch_v1.begin` used `ppuuup` for C parameters `ppuupu`, treating the surface pointer as an integer and finger count as a pointer. Patch 28 corrects it. Wine 11/MGS installs no pinch listener, so this was not the flicker source. | patch 28; `wrappedwaylandclient.c` | measured parser/reconstruction; not built |

#### 3.7.5 DXVK state-cache dedupe (2)

No DXVK or Sarek source exists on this box, so the dedupe key, collision and
lock semantics remain judged from the hunk only — §3.3's exact-source result
stands, but this specific question is still not closed against real code.

| # | Sev | Finding | Where | Prov |
|---|-----|---------|-------|------|
| S1 | fixed | The untrustworthy copied blob-index line was removed from patch 07. The content/line-context patch can no longer ask `git apply --3way` to resolve against patch 08's unrelated preimage. | `dxvk-patches/07-state-cache-mapping-dedupe-default-off.patch` | read |
| S2 | refuted | Production patch 08 is intentionally unconditional, but the preserved A/B launcher does **not** use that DLL: it hash-pins `d3d9_..._state_cache_dedupe1.dll` built from patch 07, whose environment gate remains live. The production engine rejects the stale variable and the Wayland/freeze scripts merely clear it. The claimed on-vs-on A/B path is therefore absent. | `device/launch-dxvk-sarek-state-cache-dedupe.sh`; research manifest | read |

### 3.8 Direct fix boundary on 29 August

The current local wpatch state candidate accepts only legal original SHA-256
`29759e6f...` and produces only `d902ee43...`. Its 58 changed bytes
cover the hardware and software-VP flag immediates plus the already reviewed
IPU/lighting/COUNT2 trampolines. The source series 02 + 04 + 05 applies with
zero fuzz, and `harness/test_wpatch_state_ownership_candidate.sh`
reconstructs the exact image. The final `d902ee43...` image generated on the
RG353VS, verified all 21 manifest objects and completed the pixel-gated row-07
save load, four movement bursts and four attacks. Its loaded and post-action
screenshots were 373,907 and 203,855 bytes and the kernel logged no new GPU
fault during that successful run. This closes the final-hash identity/smoke
gate; it is not the delayed fixed-scene flicker comparison needed to promote.

Preserve one failed attempt before that pass. The candidate reached a visible
title frame, then DXVK reported `VK_ERROR_DEVICE_LOST`; the kernel recorded a
Mali job hard-stop, soft reset and fault `0x4002`, and subsequent screenshots
were 972-byte black frames. Thermals were low and external power was online.
After complete launcher cleanup, exact FINALPLAY21 passed the same save,
movement and action path with no new GPU event, and the exact candidate then
passed on immediate repetition. The GPU reset is therefore real but presently
non-reproduced and not attributed to the candidate.

The promoted shared launcher engine now hashes to `b35953e3...`. Local gates
for FINALPLAY18--22 and all retained candidates pass with that engine.
On-device
TERM and SIGKILL recovery tests were completed before the final comment/P3
hash refresh; the final engine was then deployed and its candidate route
verified exact 21/21 identity. A TERM after the failed GPU run again left no
game/Wine/Box86 process, bind mount or temporary game image and restored the
CPU governor to `ondemand`.

The audio and visual candidates were kept separate through their device smokes,
preserving single-variable attribution. The owner then explicitly directed
their combination as FINALPLAY22 while accepting the delayed visual and
post-resume SFX gaps. After deployment, the combined normal entry independently
matched `21/21`, loaded row 07 and completed four movement bursts and four
attacks. FINALPLAY21 preserves the pre-combination exact rollback.

The current release packager completed its device end-to-end gate with 25 exact
files, including the four FINALPLAY21-only rollback objects. Its first deploy
attempt found an stdin-drain bug after the unchanged Box86 row; the selector was
not reached. `ssh -n` plus an actual-deployment counter now makes that condition
fail closed, and the corrected run installed and re-hashed all 25 rows with the
new selector last.

## 4. Ranked next actions

1. Repeat post-resume attacks through a console path that remains reachable
   during suspend. Music, menu
   clicks and gameplay SFX remain three observations; waveform evidence may
   support, but cannot replace, an owner listening claim.
2. For flicker attribution, capture the delayed artefact on exact FINALPLAY21
   during active play and repeat the same fixed scene on the state-ownership
   candidate. Include an active IPU/movie panel; animated water has passed.
3. Build Box86 patch 28 only if its general non-MGS fixes are wanted. Its
   source reconstruction and format audit pass, but it is deliberately outside
   the visual/audio candidates.
E7 is excluded from this work by owner request. The stale dmime locator and
B1/B4 actions from the previous ranking are complete. DXVK patches 09/10 remain
optional source candidates, not blockers for this bug-fix route.

## 5. What was NOT audited

The audit was cut short by an agent budget limit. The later direct follow-up
closed the formerly listed Wayland and DXVK-patch-08 holes: the exact listener
ABI audit compared 24 listeners with exactly five declared version-gated
omissions and zero unexpected differences; code review found each reachable
`wl_buffer` listener registered and dispatched on its same private queue, and
the Wine path registers no `wl_surface_frame` callback to lose. The MGS OpenGL
presenter likewise registers and dispatches its buffers on `gl->wl_event_queue`.
Patch 08's exact-source result is in §3.3. These are negative read/static gates,
not device proof that every Wayland failure mode is absent.

The 29 August gap audit (§3.7) then ran the remaining scopes. The two
formerly listed here are now closed and their results are in §3.7.2 and §3.7.3 —
including the answer to the open `UNAPPLIED-dmsynth-sink-startup-lifetime.diff`
question, which is that the lifetime bug **is** still reachable in the shipped
dmsynth (W3). The Wayland scope came back a substantive negative (§3.7.4).

What is still not closed:

- **Adversarial verification.** Only a small subset of the findings in this
  register have
  been through a refutation pass: one survived, two were refuted. Everything
  tagged one-pass or unverified is a single agent's reading. The rows marked
  **read**, **measured** or **device-measured** are the exception and say how
  far they go.
- **Delayed final-candidate visual comparison.** Final image `d902ee43...`
  passed exact identity and a short loaded-game smoke, but not the delayed
  fixed-scene FINALPLAY21/candidate comparison or an active IPU panel.
- **Wine audio post-resume behaviour.** Patches 84/85 build and reconstruct and
  the exact candidate completed loaded gameplay and pre-resume attacks. RTC
  wake returned at the requested time, but the device did not restore network
  reachability, so post-resume attacks and SFX survival remain unmeasured. The
  owner accepted this open gate for FINALPLAY22 promotion.
- **Box86 patch 28 build/device gate.** Its exact source reconstruction passes;
  no ARM binary was built or run.
- **DXVK patch 08's key, collision and lock semantics**, for lack of a Sarek
  tree on this box (§3.7.5).
- **Wider Box86 x87 behaviour** outside the refuted H1 mechanism.

## 6. Method, and its limits

One workflow, twelve scoped finder agents over the FINALPLAY21 production path,
each with a bounded reading list, followed by two adversarial verifiers per
finding (one refuting, one judging symptom fit).

It did not complete. 29 of 76 agents finished; 47 failed on an org spend limit,
including six of the twelve finders and **every single verifier**. So:

- the six dimensions in §3.2-§3.6 are single-pass findings with no adversarial
  check — hence the **unverified** tag, which means "one agent said so";
- the workflow's own summary labelled findings `CONFIRMED`. That label is
  wrong and is not used in this brief: the scoring treated zero surviving
  verifier votes as zero refutations. No verification occurred;
- §2 and the **measured**/**read** rows are my own work, done directly, and
  say exactly how far they go.

A second workflow on 29 August ran the six scopes §5 had left open, with tighter
per-agent reading lists and verification restricted to flicker-direct findings.
Seven of nine agents completed and only two verifiers died on the same spend
limit, so §3.7 is one-pass rather than unverified-by-collapse. Its two headline
rows are worth separating: P1 was found **independently by two agents that did
not see each other's output**, and its two load-bearing facts (that `wpatch.c`
never writes `D3DTSS_TEXTURETRANSFORMFLAGS`, and that `wd3d.c:477` gates the
default on bit 8 rather than bit 17) were then confirmed directly. §3.7.4 is the
opposite case: a scope that was expected to yield a flicker mechanism and
instead came back clean on a mechanical check of all 18 reachable listeners.

The original audit ran nothing on the RG353VS. Section 2.0 and the rows marked
**device-measured** are later direct follow-up. That work also ran the patch-27
route witness, dmime locator boundary, live `DG_WinApp.flag` read, P1
predecessor and final identities, final short gameplay smoke, and launcher
TERM/SIGKILL recovery. Patches 84/85 additionally have exact device identity,
live-mapping and pre-resume gameplay evidence; their post-resume SFX gate is
blocked as stated in §3.7.3. Box86 patch 28 has workstation
reconstruction/build evidence only. Any device-facing claim not explicitly
tagged remains an assumption or estimate under AGENTS.md rule 1.

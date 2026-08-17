# MGS2 RG353VS — reinforcement submission census (2026-08-14)

Status: diagnostic p37 built and verified. The proposed indexed-draw batch is
refuted on the automated ALERT / guard-response route. The earlier manually
verified dense 11.9--14.8 fps reinforcement scene still needs one p37 snapshot
before this zero can be generalized to that exact interval. Production remains
FINALPLAY4 / p32.

## Result

The missing measurement from
`MGS2_REINFORCEMENT_ARM_TARGET_2026-08-14.md` now has a bounded, memory-only
instrument. It counts source D3D/WineD3D draws on the CSMT consumer and the GL
draws actually issued by `context_gl.c`. It performs no I/O, allocation, clock
query or stderr logging on the render thread. An external reader obtains one
coherent snapshot through `/proc/<pid>/mem`.

The automated save / movement / action route produced a visible `ALERT`, the
guard response subtitle `Understood.`, a connecting-bridge transition and then
`EVASION`. A second run stopped immediately after `Understood.`; twenty seconds
later its `MISSION FAILED` inset visibly contained two soldiers at Raiden's
position, confirming that enemies had entered rather than the input merely
opening a door. Between the post-confirm baseline and the end of the longer
route p37 saw:

```text
CS Present commands             3190
source draws                1434610       449.72/CS Present
source indexed                    0         0.00/CS Present
source non-indexed          1434610
indexed triangle list/strip       0 / 0
indexed mergeable pairs           0

final GL draws               191296        59.97/CS Present
  glDrawArrays                85656        26.85/CS Present
  synthetic batch elements  105640        33.12/CS Present
  ordinary elements              0
  instanced / other               0 / 0
```

The accounting invariants are exact:

```text
source indexed + source non-indexed == source draws
final arrays + final batch elements == final GL draws
```

An earlier 16-walk ALERT/transition interval independently reported zero indexed
draws. A cold title/save smoke run also reported zero indexed draws. Thus the
proposed `DrawIndexedPrimitive` merger would remove exactly zero GL submissions
on every p37 route measured so far.

The first reader called the raw Present counter `frames`. A stationary live
interval proved that MGS2 sends two CSMT Present commands per frame reported by
the Wayland presenter: p37 advanced by 1184 while the frame log stayed around
30.4 displayed fps. The corrected reader therefore calls it `cs_presents` and
does not silently use it as a displayed-frame denominator. In that stationary
post-ALERT interval the raw delta was:

```text
CS Present commands         1184
source draws              438089       370.01/CS Present
final GL draws            121421       102.55/CS Present
source indexed                 0
```

Using the observed two-to-one relation, this is approximately 740 source draws
and 205 final GL draws per displayed frame. Future exact rate reports must pass
the real displayed-frame delta from the external frame log to the reader; the
indexed zero itself does not depend on any denominator.

This does **not** relabel the automated route as the earlier valid dense
reinforcement interval. Reinforcements visibly arrived, but Raiden died before
the prolonged 11.9--14.8 fps phase could be reproduced; the route's sustained
windows were mostly 24--41 fps, with a 2.645 s transition stall producing one
13.2 fps aggregate window. The valid manual capture remains the only basis for
the sustained 11.9--14.8 fps claim. Run p37 during that exact scene once before
closing indexed draws globally.

## What the numbers mean

The current producer and synthetic-EBO batchers are already doing substantial
work on this route:

```text
about 740 source draws/displayed frame -> about 205 real GL draws/displayed frame
```

The remaining `glDrawArrays` are principally singleton runs separated by real
effective-state / resource boundaries. Earlier projected-state, packed-VBO,
WORLD+VB, repeated-geometry and instancing captures already tested the ways of
crossing those boundaries without reordering. Their results are recorded in
briefs 40 and 41: redundant-state boundaries were zero, common-VBO packing was
slower or OOM, and byte-identical instancing removed only 1.43--1.93 batches per
frame against the required 40.

Arm's recommendation to reduce CPU driver overhead with large batches is still
correct, but it is not a new implementation here; FINALPLAY has already applied
it. `GL_EXT_multi_draw_arrays` remains absent on the live libmali context, and a
multi-draw call could not cross state changes anyway.

The bounded result therefore rejects building an indexed batch blindly. It does
not prove a new sustained-combat optimization. In the valid dense profile the
game worker was approximately as busy as `wined3d_cs`, while about half of the
renderer worker's samples were already inside native libmali. Under the fixed
constraints (same game logic, same pixels/shaders and this libmali) there is no
measured patch that can honestly be promised to restore 30 fps in that scene.

## p37 implementation and verification

Artifacts:

```text
wine-patches/37-reinforcement-submit-census.patch
harness/reinforcement_submit_census.py
binaries/wined3d_p37_reinforcement_census.dll
logs/rg353vs/reinforcement-submit-census-20260814/
```

Binary:

```text
sha256 44e9a2ae5462e339156c7fbb609c936de01c65167d76c45aaa50f0a8a3419767
symbol mgs2_reinforcement_submit_census VMA 0x101d10c0
```

The patch applies to the current p32 Wine source with `-F0`. The i386 PE build
and Python reader passed their local checks. On the device the mounted target
`/usr/lib/wine/i386-windows/wined3d.dll` compared byte-for-byte equal to p37,
the clock cap was 1992000 Hz, and there was exactly one game process.

The first attempted A/B uncovered an independent launcher defect: the current
`launch-play.sh` documented `MGS2_WINED3D_DLL`, but hard-coded the p32 filename.
The launcher now uses:

```sh
${MGS2_WINED3D_DLL:-wined3d_p32_ffp_source_dedup.dll}
```

The production default is unchanged; the selector only makes the documented
diagnostic override work. This was caught by comparing the mounted target rather
than trusting the requested filename.

Run one snapshot or a before/after pair with:

```sh
MGS2_WINED3D_DLL=wined3d_p37_reinforcement_census.dll \
MGS2_REINFORCEMENT_CENSUS=1 ./MGS2-Substance.sh

python3 /tmp/reinforcement_submit_census.py \
    --symbol-vma 0x101d10c0 --output /tmp/reinforcement.json

python3 /tmp/reinforcement_submit_census.py \
    --diff /tmp/before.json /tmp/after.json
```

Start the 20-second interval only after the player confirms that the dense
reinforcements are entering. Keep one process and 1992000 Hz, and byte-compare
the mounted DLL first.

## First-use stall captured in the same work

The same automated route was repeated with the existing bounded `MGS2_GPU_PROBE`
ring. It recorded:

```text
compile_shader              24 calls      185479 us total    14665 us max
link_separable_stage        21 calls     4618321 us total   356093 us max
link_program                 2 calls      309708 us total   164394 us max
validate_program_pipeline   17 calls        1855 us total     1045 us max
```

All 24 compile records had distinct exact-source hashes; p32 had already removed
the duplicates. The remaining hitch is therefore dominated by the first link of
genuinely new stages, not shader text generation, validation, paging or a repeat
that p32 missed.

A safe candidate is a bounded **same-context object prewarm**: externally capture
the exact source whitelist, create and link those exact shader/stage objects once
after the production GL context exists, and retain them in p32's source-owner
cache. This moves their measured cost to an existing loading/startup interval and
must be accepted only if the later route shows cache hits and no corresponding
link calls. Merely linking identical source and deleting the object does not help;
that was already measured. `GL_KHR_parallel_shader_compile` is only an optional
thread-count hint plus completion query, and the implementation is not required
to obey the requested count, so it is not a guaranteed replacement for prewarm.

The claim boundary is narrow: a verified whitelist can remove its own later
first-use links. It cannot explain or remove every multi-second load, and it is
unrelated to the separately captured untimed futex lost wakeup.

## Audio decision

No production audio code changed. The prior valid combat capture had zero failed
DirectSound calls, no dmsynth note-on failure, no voice exhaustion (39/48), a
live mixer and no PipeWire client error, but lacked the timestamp of the exact
missing attack. The expected player attack also uses the persistent 32576-byte
DirectSound SFX pool and may have no distinct DirectMusic event.

An official Wine 11.0-to-current-master comparison found no matching dmime,
dmusic or persistent-DS-buffer lifecycle fix. Newer dmsynth commits improve sink
timing; for example Wine commit `685c5b6f` adds 10 ms write latency against
scheduler delay. That cannot be treated as the MGS2 fix because the missing
player attack is on the persistent DirectSound path and the current capture did
not show a synth underrun.

The next audio action remains one correlated capture of the exact `x` press:

```text
input timestamp -> persistent pool Lock/Unlock/Play -> mixer input -> PCM envelope
```

Only the first missing boundary in that chain justifies a patch. Backporting the
new dsound resampler or dmsynth timing series without that evidence would replace
the measured FINALPLAY4 native FIR target and mix several unrelated variables.

## External references

- Arm, *Mali Performance 5: An Application's Performance Responsibilities*:
  <https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/mali-performance-5-an-application-s-performance-responsibilities>
- Khronos, `GL_EXT_multi_draw_arrays`:
  <https://registry.khronos.org/OpenGL/extensions/EXT/EXT_multi_draw_arrays.txt>
- Khronos, `GL_KHR_parallel_shader_compile`:
  <https://registry.khronos.org/OpenGL/extensions/KHR/KHR_parallel_shader_compile.txt>
- Box86 configuration documentation:
  <https://github.com/ptitSeb/box86/blob/master/docs/USAGE.md>
- Wine dmsynth scheduler-latency commit:
  <https://gitlab.winehq.org/wine/wine/-/commit/685c5b6f6312d55c948ee15315d858777af72408>

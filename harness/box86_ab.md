# Box86 A/B: prepared arms

Production remains unchanged when `MGS2_BOX86_PROFILE` is unset:

```text
SAFEFLAGS=0  BIGBLOCK=2  FORWARD=512  CALLRET=1
```

The one experimental arm is selected only for its launch:

```sh
MGS2_BOX86_PROFILE=aggressive /storage/roms/ports/MGS2-Substance.sh
```

It changes only these Box86 startup parameters:

```text
SAFEFLAGS=0  BIGBLOCK=2  FORWARD=1024  CALLRET=1
```

Only `FORWARD` differs from production. `BIGBLOCK=3` is deliberately excluded
from this A/B because changing two dynarec controls at once would make the
result uninterpretable.

Run the two arms in separate launches at the same fixed spot and pinned clock.
Do not add `STRONGMEM`, `FASTNAN`, `X87DOUBLE`, or a newer Box86 at the same
time: they have different correctness risks, so combining them would make a
failure or gain uninterpretable. Returning to the menu launcher, or launching
without `MGS2_BOX86_PROFILE`, is the rollback.

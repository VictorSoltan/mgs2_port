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

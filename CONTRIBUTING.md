# Contributing

Contributions are welcome when they preserve the project's measurement and
licensing boundaries.

## Local setup

Copy `.env.example` to `.env` and configure your device and external source
trees. Do not commit the resulting file, credentials, Wine prefixes, game files,
compiled binaries or raw device logs.

## Before changing code

Read `AGENTS.md`, `docs/DEVICE.md` and the newest brief for the problem.
Search the written dead ends before reopening an attractive hypothesis.

For an optimisation, state:

- the exact hypothesis;
- what result would refute it;
- the fixed device scene and clock;
- the correctness witness;
- the rollback.

For a runtime defect, identify the captured signature before proposing a shared
cause. Music, menu sounds and gameplay SFX must be reported separately.

## Patch and harness policy

- Keep upstream bases and commits explicit.
- Add source changes as reviewable patches under the matching upstream
  directory.
- Diagnostics must be bounded, memory-only where practical, off by default and
  externally readable.
- Never add per-event output to the render, mixer or message hot paths.
- Generated output and local binaries stay out of Git.
- Record negative results; do not delete them because the idea failed.

## Verification

Run syntax/compile checks appropriate to the files changed. Device performance
and correctness claims require a real RG353VS run, one process, pinned clocks
and byte-verified live modules. If that run was not possible, say so.

## Licensing

Wine-derived changes are LGPL-2.1-or-later, Box86-derived changes are MIT and
DXVK-derived changes use the zlib license. Preserve upstream notices and update
`THIRD_PARTY_NOTICES.md` if a new third-party component is added.

The repository's original launchers, harnesses and documentation do not yet
have an owner-selected project-wide license. Do not add a global SPDX identifier
until that choice is made.

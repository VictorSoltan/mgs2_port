# Local runtime artifacts

This directory is a local artifact cache, not a source directory. Compiled DLLs,
shared objects and Box86 executables are intentionally ignored by Git.

The public, reproducible record consists of:

- `SHA256SUMS`, the historical artifact hash catalogue;
- `device/FINALPLAY23_MOVIE_GUARD.manifest`, the current live identity gate;
- `device/FINALPLAY_RUNTIME_X86LIBS.sha256`, the clean-install i386 dependency
  gate;
- `device/FINALPLAY17_DXVK_FREEZE.manifest`, the older DXVK rollback gate;
- `device/FINALPLAY16_DXVK.manifest`, the previous DXVK rollback gate;
- `device/FINALPLAY.manifest`, the FINALPLAY15 rollback identity gate;
- `wine-patches/`, `box86-patches/` and `dxvk-patches/`, the source changes;
- the pinned bases and build instructions in `device/FINALPLAY.lock` and the
  production briefs.

Place locally built or separately downloaded release artifacts here when a
harness expects `binaries/<name>`. Do not add them back to Git. A distributable
bundle should be attached to a release together with its source references,
license notices and manifest.

The current packager expects the ten ignored dependency objects under
`binaries/x86libs/`, or fetches the exact pinned copies from the device with
`--from-device`/`--deploy`.

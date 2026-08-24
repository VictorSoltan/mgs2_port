# Local runtime artifacts

This directory is a local artifact cache, not a source directory. Compiled DLLs,
shared objects and Box86 executables are intentionally ignored by Git.

The public, reproducible record consists of:

- `SHA256SUMS`, the historical artifact hash catalogue;
- `device/FINALPLAY16_DXVK.manifest`, the current live identity gate;
- `device/FINALPLAY.manifest`, the FINALPLAY15 rollback identity gate;
- `wine-patches/`, `box86-patches/` and `dxvk-patches/`, the source changes;
- the pinned bases and build instructions in `device/FINALPLAY.lock` and the
  production briefs.

Place locally built or separately downloaded release artifacts here when a
harness expects `binaries/<name>`. Do not add them back to Git. A distributable
bundle should be attached to a release together with its source references,
license notices and manifest.

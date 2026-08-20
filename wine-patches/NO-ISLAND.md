# Clean NO-ISLAND chain

The recovered island work in patches 42, 43, 48, 49, 50, 52, 53 and 54 is a
separate experimental binary/source track. It is not part of the renderer
correctness build and must not be silently applied to the NO-ISLAND tree.

Apply the reproducible correctness chain with `-F0`:

```sh
tar xf wine-11.0.tar.xz
cd wine-11.0
for p in /path/to/wine-patches/*.patch; do
    case "$p" in
        */42-*|*/43-*|*/48-*|*/49-*|*/50-*|*/52-*|*/53-*|*/54-*) continue ;;
    esac
    patch -p1 -F0 --batch < "$p" || exit 1
done
```

This chain includes the renderer ordering fixups 55, the WineWayland fixup 56,
the audit-round3 GLES readback export 57, the NO-ISLAND GL-info helper 58, the
missing production texture lifecycle export 59, and the dmsynth sink transport
watchdog 60 (dmsynth p35, on by default in the built DLL and switched off with
`MGS2_DMSYNTH_WATCHDOG_MS=0`). The native island is intentionally
not built or loaded from this tree.

Patch 61 is deliberately NOT part of this chain. It routes the island's GL calls
through its translated `gl_info`, and `MGS2_GL_INFO()` is the identity macro
unless `MGS2_ISLAND_ARM` is defined, so it changes nothing in a NO-ISLAND build
-- verified: all 32 wined3d translation units compile to byte-identical
`.text`/`.rdata`/`.data` with and without it. Applying it here is harmless but
pointless; leaving it out keeps this chain about the guest DLL only.

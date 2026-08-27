#!/bin/sh
# FINALPLAY20 production selector.
#
# DXVK-Sarek over proprietary libmali is the normal renderer. FINALPLAY19 and
# the older fixed bundles remain one-launch rollback paths.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
if [ -n "${MGS2_RENDERER:-}" ]; then
    RENDERER=$MGS2_RENDERER
elif [ -n "${MGS2_RESEARCH_RUN:-}" ]; then
    # Existing named WineD3D experiments set this opt-in and then exec the
    # production entry. Preserve that interface after changing the play default.
    RENDERER=wined3d
else
    RENDERER=dxvk
fi

case "$RENDERER" in
    dxvk|dxvk20|fp20)
        exec "$HERE/launch-play-dxvk-fp20.sh"
        ;;
    dxvk19|fp19)
        exec "$HERE/launch-play-dxvk-fp19.sh"
        ;;
    dxvk18|fp18)
        exec "$HERE/launch-play-dxvk-fp18.sh"
        ;;
    dxvk17|fp17)
        exec "$HERE/launch-play-dxvk-fp17.sh"
        ;;
    dxvk16|fp16)
        exec "$HERE/launch-play-dxvk-fp16.sh"
        ;;
    wined3d|fp15)
        exec "$HERE/launch-play-wined3d-fp15.sh"
        ;;
    *)
        echo "MGS2: unknown MGS2_RENDERER=$RENDERER (use dxvk, fp20, fp19, fp18, fp17, dxvk16 or wined3d)" >&2
        exit 1
        ;;
esac

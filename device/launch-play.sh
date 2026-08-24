#!/bin/sh
# FINALPLAY16 production selector.
#
# DXVK-Sarek over proprietary libmali is the normal renderer. The previous
# byte-exact FINALPLAY15 WineD3D launcher remains beside it as the immediate
# rollback and can be selected for one launch with MGS2_RENDERER=wined3d.
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
    dxvk)
        exec "$HERE/launch-play-dxvk-fp16.sh"
        ;;
    wined3d|fp15)
        exec "$HERE/launch-play-wined3d-fp15.sh"
        ;;
    *)
        echo "MGS2: unknown MGS2_RENDERER=$RENDERER (use dxvk or wined3d)" >&2
        exit 1
        ;;
esac

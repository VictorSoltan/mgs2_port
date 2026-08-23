#!/bin/sh
# The ad-hoc entry point for a run that is NOT the production bundle.
#
# launch-play.sh now refuses to start when MGS2_BOX86_BIN, MGS2_WINED3D_DLL,
# MGS2_WAYLAND_SO, MGS2_D3D8_DLL or the three audio DLL variables are set. That is
# not tidiness. Accepting them used to also switch off the identity check for
# every other mounted file, so a single value left over in a shell produced a run
# with an unrecorded mixture -- box86's class-B registry mapping the RVAs of a
# WineD3D that was no longer mounted -- and reported frame times for it.
#
# So the override path is still here, it just has to be asked for out loud:
#
#   ./launch-research.sh MGS2_WINED3D_DLL=wined3d_p72c_fused_abc.dll \
#                        MGS2_BOX86_BIN=box86-island55-p72c-candidate
#
# Assignments are arguments rather than exports, so a shell cannot carry them into
# the next run by accident -- which is the whole failure this exists to prevent.
# Named experiments keep their own launch-*.sh; those set MGS2_RESEARCH_RUN
# themselves and do not need this wrapper.
#
# The identity check still runs and still hashes all eleven mounted files. On a
# research run it reports the mismatches instead of refusing, so the log says
# exactly which bundle produced the numbers.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)

if [ "$#" = 0 ]; then
    echo "usage: launch-research.sh MGS2_NAME=value [MGS2_NAME=value ...]" >&2
    echo "  nothing to override means this is a production run: use launch-play.sh" >&2
    exit 2
fi

for assignment in "$@"; do
    case "$assignment" in
        MGS2_*=*)
            export "$assignment"
            ;;
        *)
            echo "launch-research.sh: expected MGS2_NAME=value, got '$assignment'" >&2
            exit 2
            ;;
    esac
done

echo "MGS2: RESEARCH RUN -- $*" >&2
echo "MGS2: this is not FINALPLAY; anything measured here belongs to the bundle" \
     "selected above, not to the release" >&2

export MGS2_RESEARCH_RUN=1
exec "$HERE/launch-play.sh"

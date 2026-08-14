#!/bin/bash
# FINALPLAY entry point. The laboratory launcher remains in the repository but
# normal play always enters the fixed, instrumentation-free configuration.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -x "$SCRIPT_DIR/launch-play.sh" ]; then
    GAMEDIR="$SCRIPT_DIR"
else
    GAMEDIR="$SCRIPT_DIR/MGS2-Substance"
fi

exec "$GAMEDIR/launch-play.sh"

#!/bin/bash
# MGS2 on Hangover 11.0 -- the H0/H1 experiment, deliberately separate from the
# working Box86/Wine stack.
#
# Nothing here touches production. No bind mounts over /usr/lib/wine, its own
# prefix, its own log. If this script is deleted the working setup is unchanged.
#
#   current stack:  MGS2 i386 -> Wine i386 PE -> Wine/Unix -> Box86/Box64 -> ARM64
#   here:           MGS2 i386 -> WowBox64 -> Wine WoW64 -> native AArch64 -> ARM64
#
# Why Hangover 11.0 and not 11.9: our own Wine is 11.0, so the eleven patches in
# wine-patches/ apply with the smallest diff. 11.9 is the second experiment, once
# this one has a baseline.
#
# Build chosen: debian13_trixie. ROCKNIX has glibc 2.41 and trixie is also 2.41;
# ubuntu2510 is 2.42 and would demand symbols this system does not have.
#
# H1 goal is NOT frame rate. It is: prefix builds, the exe is recognised as Win32,
# the launcher/menu runs, and winewayland creates a window. No performance patches
# are installed on purpose -- several of them exist only because of Box86, and the
# point is to find out which are still needed. See brief #31.
#
# H1 is done: sway reports a window titled "METAL GEAR SOLID 2:SUBSTANCE", and
# libmali, libEGL and libwayland-egl are loaded natively in the process.
#
# Known gaps, both needed before H2 can produce a frame:
#   - gptokeyb is NOT started here, so the game gets no controller input and stays
#     on the title screen. Add it once there is a picture worth navigating to.
#   - D3D8 creation fails: upstream winewayland enumerates EGL configs demanding
#     desktop EGL_OPENGL_BIT, Mali offers only ES2/ES3, so wined3d is handed zero
#     pixel formats. Fixing that needs patches 06-opengl32, 08-win32u and
#     10-winewayland.drv rebuilt for aarch64. Swapping in our i386 PE wined3d and
#     d3d8 does NOT help and has been tried -- see brief #32.
set -u

HANGOVER="${MGS2_HANGOVER_DIR:-/storage/hangover}"
GAMEDIR="${1:-/storage/roms/ports/MGS2-Substance}"
EXE="${MGS2_EXE:-mgs2_sse_rg353vs_port.exe}"
# The game lives in game/bin and must be started from there, exactly as
# launch.sh does (it cds to $GAMEDIR/game/bin before exec'ing wine).
BINDIR="$GAMEDIR/game/bin"

[ -x "$HANGOVER/bin/wine" ] || { echo "no hangover wine at $HANGOVER/bin/wine" >&2; exit 1; }
[ -r "$BINDIR/$EXE" ]       || { echo "no game exe at $BINDIR/$EXE" >&2; exit 1; }

# Its own prefix. Never the production wineprefix64: a WoW64 ARM64 Wine would
# rewrite it and there would be no way back to the working stack.
export WINEPREFIX="${MGS2_HANGOVER_PREFIX:-$GAMEDIR/wineprefix-hangover}"

# Hangover's loader is relocatable, so pointing these at /storage is enough; the
# deb was built for /usr but resolves its dll dir from the binary's own path.
export WINELOADER="$HANGOVER/bin/wine"
export WINESERVER="$HANGOVER/bin/wineserver"
export WINEDLLPATH="$HANGOVER/lib/wine"
export LD_LIBRARY_PATH="$HANGOVER/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PATH="$HANGOVER/bin:$PATH"

# Same display environment the working launcher uses. ROCKNIX runs sway, there is
# no X server, so winewayland.drv is the only usable driver.
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/var/run/0-runtime-dir}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
export DISPLAY=""
export WINEDLLOVERRIDES="${WINEDLLOVERRIDES:-mscoree=;mshtml=;winemenubuilder.exe=}"

# Quiet by default. H1 is about whether it runs at all, and a debug channel on
# this device has repeatedly cost more than it measured.
export WINEDEBUG="${WINEDEBUG:--all}"

LOG="${MGS2_HANGOVER_LOG:-/tmp/hangover-$(date +%H%M%S).log}"
echo "$LOG" > /tmp/hangover-current-log

{
    echo "=== hangover run $(date -Is 2>/dev/null || date)"
    echo "wine:     $("$WINELOADER" --version 2>&1 | head -1)"
    echo "prefix:   $WINEPREFIX"
    echo "exe:      $BINDIR/$EXE"
    echo "wayland:  $XDG_RUNTIME_DIR/$WAYLAND_DISPLAY"
    echo
} > "$LOG" 2>&1

if [ "${MGS2_HANGOVER_BOOT:-0}" = 1 ]; then
    echo "creating prefix (first run takes a while on this hardware)" | tee -a "$LOG"
    "$WINELOADER" wineboot -u >>"$LOG" 2>&1
    "$WINESERVER" -w
    # MGS2 asks the drive it runs from for its free block count and refuses to
    # save when the answer is zero. Z: is the read-only, 100%-full squashfs, so
    # the game must see a drive whose free space is real. Same mapping as
    # launch.sh:63.
    if [ -d "$WINEPREFIX/dosdevices" ]; then
        ln -sfn /storage "$WINEPREFIX/dosdevices/d:" 2>/dev/null
        echo "mapped D: -> /storage" | tee -a "$LOG"
    fi
    echo "prefix built" | tee -a "$LOG"
    exit 0
fi

cd "$BINDIR" || exit 1

# Controller input, exactly as launch.sh:557-559 does it. Needed from H2 onwards:
# without it the game cannot be taken off the title screen, so "no draws" and "no
# input" would be indistinguishable.
if [ -x /usr/bin/gptokeyb ] && [ -r "$GAMEDIR/mgs2.gptk" ]; then
    /usr/bin/gptokeyb "$EXE" -c "$GAMEDIR/mgs2.gptk" >/tmp/hangover-gptokeyb.log 2>&1 &
    GPTOKEYB_PID=$!
    echo "gptokeyb pid $GPTOKEYB_PID" >> "$LOG"
fi

"$WINELOADER" "$EXE" >>"$LOG" 2>&1 &
WINE_PID=$!
echo "wine pid $WINE_PID, log $LOG"
wait "$WINE_PID"
[ -n "${GPTOKEYB_PID:-}" ] && kill "$GPTOKEYB_PID" 2>/dev/null || true

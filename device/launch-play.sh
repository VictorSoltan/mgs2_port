#!/bin/bash
# MGS2 Substance RG353VS FINALPLAY4.
# Fixed production stack only: no census, profile, stats, live switches or A/B
# overrides. The renderer fast paths are compile-time policy in the FINAL DLLs.

XDG_DATA_HOME=${XDG_DATA_HOME:-$HOME/.local/share}
if [ -d "/opt/system/Tools/PortMaster" ]; then
    controlfolder="/opt/system/Tools/PortMaster"
elif [ -d "/opt/tools/PortMaster" ]; then
    controlfolder="/opt/tools/PortMaster"
elif [ -d "$XDG_DATA_HOME/PortMaster" ]; then
    controlfolder="$XDG_DATA_HOME/PortMaster"
else
    controlfolder="/storage/roms/ports/PortMaster"
fi
[ -r "$controlfolder/control.txt" ] && source "$controlfolder/control.txt"
[ -r "$controlfolder/tasksetter" ] && source "$controlfolder/tasksetter"
[ -r "$controlfolder/device_info.txt" ] && source "$controlfolder/device_info.txt"
type get_controls >/dev/null 2>&1 && get_controls

GAMEDIR="/storage/roms/ports/MGS2-Substance"
EXE="mgs2_sse_rg353vs_port.exe"

exec 9>/tmp/mgs2-substance.lock
flock -n 9 || exit 0

export WINEPREFIX="$GAMEDIR/wineprefix64"
if [ -d "$WINEPREFIX/dosdevices" ]; then
    ln -sfn /storage "$WINEPREFIX/dosdevices/d:" 2>/dev/null
fi

# Quiet fixed audio path: ALSA through PipeWire, 44.1 kHz, 30 ms quantum.
export WINEDEBUG="${MGS2_PLAY_WINEDEBUG:--all}"
export MGS2_GL_STATS="${MGS2_GL_STATS:-0}"
export PULSE_SERVER=tcp:127.0.0.1:4713
export PIPEWIRE_ALSA='{ alsa.rate=44100 node.name=mgs2-audio }'
export PIPEWIRE_QUANTUM=1440/48000
export MGS2_DMIME_SHAREDGROUPS=1
export MGS2_DMIME_SHAREDGROUP_COUNT=4
export MGS2_DMSYNTH_JITTER_MS=30
export MGS2_DMSYNTH_POLYPHONY=48
export MGS2_DMSYNTH_IDLE_SKIP=0
export MGS2_DMSYNTH_UNMUTE_NOTES=0

export WINEDLLOVERRIDES='mscoree=;mshtml=;winemenubuilder.exe=;winepulse.drv=d;d3d8=builtin;d3d9=builtin;dxgi=builtin'
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/var/run/0-runtime-dir}
export WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-wayland-1}
export BOX64_LD_LIBRARY_PATH="/usr/share/box64/lib:$GAMEDIR/x64libs"
export BOX64_EMULATED_LIBS='libwayland-client.so.0:libffi.so.8:libwayland-egl.so.1'
export BOX64_LOG=0 BOX64_NOBANNER=1
export BOX86_LD_LIBRARY_PATH="/usr/share/box86/lib:$GAMEDIR/x86libs"
export BOX86_EMULATED_LIBS='libwayland-client.so.0:libffi.so.8:libwayland-egl.so.1:libxkbcommon.so.0:libxkbregistry.so.0:libxml2.so.2:libicuuc.so.72:libicudata.so.72:liblzma.so.5:libstdc++.so.6'
export BOX86_LOG=0 BOX86_NOBANNER=1
# SAFEFLAGS is box86's own default, 1. Production used to lower it to 0, which
# relaxes x86 flag accuracy for speed. Measured 2026-08-12 over two 450 s demo
# windows with everything else fixed: 58.9 fps at 0 against 58.4 fps at 1, and
# medians 4993 ms against 5005 ms -- 0.9% and 0.2%, i.e. noise. The stall profile
# was byte-identical (31/9/11/4 frames over 50/100/200/500 ms). Not worth a
# correctness relaxation, so it is back at the default.
export BOX86_DYNAREC_SAFEFLAGS=1
# Kept, and both measured over the same 450 s window: CALLRET=1 is worth 58.9
# against 55.5 fps (+6.1%), which is real. BIGBLOCK=2 was only measured bundled
# with the other two and is left alone.
export BOX86_DYNAREC_BIGBLOCK=2
export BOX86_DYNAREC_FORWARD=512
export BOX86_DYNAREC_CALLRET=1
# Device profile at the fixed Game Data 02 spot attributes 31% of main-thread
# samples to Wine's guest _sse2_memmove.  The patched Box86 recognises that
# exact Wine 11 prologue and executes the same overlap-safe operation in native
# ARM libc; zero-length copies return directly. No pixels, game state, or copy
# semantics are removed.
export MGS2_BOX86_NATIVE_MEMMOVE=1
# Diagnostic-only exact AABB bridge.  Production remains off unless a caller
# explicitly selects the matching Box86 + D3D8 pair and enables this switch.
export MGS2_BOX86_NATIVE_AABB="${MGS2_BOX86_NATIVE_AABB:-0}"
# Patch 36/Box86 patch 06 moves the exact Wine DirectSound FIR convolution out
# of translated x86 and into native ARM. At fixed 1416 MHz the mixer thread fell
# from 12.97% to 7.57% of one core (-41.6%); guest dsound samples fell 717 -> 40.
# The player validated normal combat sound before production promotion. Override
# to 0 only when pairing this launcher with an older Box86 for diagnostics.
export MGS2_BOX86_NATIVE_DSOUND_FIR="${MGS2_BOX86_NATIVE_DSOUND_FIR:-1}"

# Measured presentation and the two retained non-renderer fixes.
export MGS2_GL_PBO=0
export MGS2_GL_FLIP=0
export MGS2_GL_BGRA=1
export MGS2_GL_SHM_BUFFERS=2
export MGS2_PEEK_HOT=401176
export MGS2_PEEK_WAIT=1
export MGS2_PEEK_WAIT_MS=4

mount_bind() {
    local src="$1" dst="$2"
    [ -r "$src" ] || return 1
    while grep -q " $dst " /proc/mounts; do
        if [ -f "$src" ] && [ -f "$dst" ] && cmp -s "$src" "$dst"; then
            return 0
        fi
        umount "$dst" 2>/dev/null || return 1
    done
    mount --bind "$src" "$dst"
}

unmount_all() {
    local dst="$1"
    while grep -q " $dst " /proc/mounts; do
        umount "$dst" 2>/dev/null || return
    done
}

CPU_POLICIES=$(ls -d /sys/devices/system/cpu/cpufreq/policy* 2>/dev/null)
SAVED_GOV=""
SAVED_MAX=""

save_cpu_state() {
    local p
    for p in $CPU_POLICIES; do
        SAVED_GOV="$SAVED_GOV $p:$(cat "$p/scaling_governor" 2>/dev/null)"
        SAVED_MAX="$SAVED_MAX $p:$(cat "$p/scaling_max_freq" 2>/dev/null)"
    done
}

set_final_cpu_cap() {
    local p
    for p in $CPU_POLICIES; do
        echo performance > "$p/scaling_governor" 2>/dev/null
        echo 1992000 > "$p/scaling_max_freq" 2>/dev/null
    done
}

restore_cpu_state() {
    local e p v
    for e in $SAVED_MAX; do
        p="${e%%:*}"; v="${e##*:}"
        [ -n "$v" ] && echo "$v" > "$p/scaling_max_freq" 2>/dev/null
    done
    for e in $SAVED_GOV; do
        p="${e%%:*}"; v="${e##*:}"
        [ -n "$v" ] && echo "$v" > "$p/scaling_governor" 2>/dev/null
    done
}

# FINALPLAY3 also serialises Box86's first-use allocation and publication of
# an x86 mutex's native ARM backing mutex.  The old two-stage publication was
# captured leaving Wine's shared-session lock owned forever when concurrent
# first users selected different native mutexes.  This changes no Wine lock
# semantics and retains the measured native memmove path from FINALPLAY2.
mount_bind "$GAMEDIR/${MGS2_BOX86_BIN:-box86-native-dsound-fir1}" /usr/bin/box86 || exit 1
mount_bind "$GAMEDIR/win32u_glfuncs3.so" /usr/lib/wine/i386-unix/win32u.so || exit 1
mount_bind "$GAMEDIR/winewayland_stall1.so" /usr/lib/wine/i386-unix/winewayland.so || exit 1
mount_bind "$GAMEDIR/opengl32_finalplay_sso.so" /usr/lib/wine/i386-unix/opengl32.so || exit 1
# ntdll_fastyield.so is deliberately NOT mounted. Patch 05 consists solely of an
# NtYieldExecution switch gated on MGS2_YIELD, which production never sets, so the
# module ran stock while still placing a custom rebuild of a core Wine module over
# the system one: no benefit, real risk surface. Removed 2026-08-12; the module
# stays in binaries/ and one mount_bind line brings it back if MGS2_YIELD=fast is
# ever worth measuring. See MGS2_SEPARABLE_FREEZE_CAPTURE_2026-08-12.md section 8.
# Patch 27: separable stage programs. Measured on the device -- a program pair
# costs 116 ms instead of 201 ms (-42%), about 2.4 s of pauses removed per
# session, concentrated where shaders repeat (codec, transitions). Per-frame
# throughput is untouched: the path only builds programs, it does not draw.
# Restored to production 2026-08-12 after the day's freeze turned out to predate
# it; see MGS2_SEPARABLE_FREEZE_CAPTURE_2026-08-12.md section 4.
# Patch 29 rides along: ARB_DEPTH_CLAMP is no longer credited on a GLES driver and
# the two GLES-meaningless toggles are guarded. Measured on the device: rejected GL
# calls fall from 52,365 per two minutes to 10,183 per three and a half, i.e. ~436
# per second down to ~48, with no fps change. These were invisible in production
# because ERR sits behind a channel check, but the calls were made every frame.
# Patch 32 canonicalises FFP shaders by their exact generated GLSL source. On the
# corrected save-load/enemy route, the control created 36 stages, 17 of them
# byte-identical duplicates costing 2.04 s; the cache-on run created no duplicate.
# It changes first-use work only, not drawing. MGS2_GL_SOURCE_DEDUP=0 is the A/B
# escape hatch. See MGS2_SHADER_FIRST_USE_RESEARCH_2026-08-13.md.
mount_bind "$GAMEDIR/wined3d_p32_ffp_source_dedup.dll" /usr/lib/wine/i386-windows/wined3d.dll || exit 1
mount_bind "$GAMEDIR/user32_peek1.dll" /usr/lib/wine/i386-windows/user32.dll || exit 1
# FINALPLAY2 keeps DISCARD writes in the cached producer shadow. This removes
# two 512 KiB readbacks per frame from WineD3D's mapped upload memory while the
# existing dirty flush publishes the identical bytes before drawing. Measured
# at the fixed heavy spot: three consecutive windows at 30.0/30.0/30.1 fps.
# Patch 28 removes the visibility culler's AABB cache, measured dead: cache_hit=0
# against cache_miss=112800 over 300 frames, because the key includes a geometry
# generation the game bumps every frame. Frees 73,760 bytes of BSS and 848 bytes
# of code, and cannot change a culling decision. The culler itself stays: measured
# 44.3 fps with it against 37.7 without, over two 400 s windows.
mount_bind "$GAMEDIR/${MGS2_D3D8_DLL:-d3d8_finalplay3_nocullcache.dll}" /usr/lib/wine/i386-windows/d3d8.dll || exit 1
# Patch 31 is OFF. It replaces the culler's per-draw AABB scan -- 349 vertex walks
# a frame in emulated x86 -- with one conservative box per buffer write. Measured
# +74% on an autoloaded corridor route (48.68/48.39 against 27.92) with identical
# screenshots, and then REVERTED on 2026-08-13: the player reported the game barely
# working. That route had no scene transitions, no enemies and no cutscenes, and an
# average of fps over windows hid whatever it costs elsewhere. Set to 1 for one run
# to try it on a specific scene; judge it by frame-time bands, not average fps.
export MGS2_D3D8_CULL_BOX=0
# Patch 34 restores the synth interpolation mode after Reset: measured synth
# worker CPU -34.2% with no FPS regression. Patch 36 is the matching bridgeable
# DirectSound FIR target selected by the native Box86 default above.
mount_bind "$GAMEDIR/${MGS2_DMSYNTH_DLL:-dmsynth_p34_interp_reset.dll}" /usr/lib/wine/i386-windows/dmsynth.dll || exit 1
mount_bind "$GAMEDIR/${MGS2_DSOUND_DLL:-dsound_p36_native_fir_target.dll}" /usr/lib/wine/i386-windows/dsound.dll || exit 1
mount_bind "$GAMEDIR/${MGS2_DMIME_DLL:-dmime_transition1.dll}" /usr/lib/wine/i386-windows/dmime.dll || exit 1
mount_bind "$GAMEDIR/dmusic_shared_lifetime1.dll" /usr/lib/wine/i386-windows/dmusic.dll || exit 1

cleanup() {
    [ -n "${THERMAL_PID:-}" ] && kill "$THERMAL_PID" 2>/dev/null || true
    [ -n "${WINE_PID:-}" ] && kill "$WINE_PID" 2>/dev/null || true
    [ -n "${GPTOKEYB_PID:-}" ] && kill "$GPTOKEYB_PID" 2>/dev/null || true
    killall -9 wineserver services.exe explorer.exe winedevice.exe plugplay.exe svchost.exe rpcss.exe 2>/dev/null || true
    pkill -9 -f '[m]gs2_sse_rg353vs_port.exe' 2>/dev/null || true
    restore_cpu_state
    unmount_all /usr/lib/wine/i386-windows/wined3d.dll
    unmount_all /usr/lib/wine/i386-windows/d3d8.dll
    unmount_all /usr/lib/wine/i386-unix/winewayland.so
    unmount_all /usr/lib/wine/i386-unix/win32u.so
    unmount_all /usr/lib/wine/i386-unix/opengl32.so
    unmount_all /usr/lib/wine/i386-windows/user32.dll
    unmount_all /usr/lib/wine/i386-windows/dmsynth.dll
    unmount_all /usr/lib/wine/i386-windows/dsound.dll
    unmount_all /usr/lib/wine/i386-windows/dmime.dll
    unmount_all /usr/lib/wine/i386-windows/dmusic.dll
    unmount_all /usr/lib/wine/i386-unix/ntdll.so
    unmount_all /usr/bin/box86
    [ -n "${ESUDO:-}" ] && $ESUDO systemctl restart oga_events >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

save_cpu_state
set_final_cpu_cap

cd "$GAMEDIR/game/bin" || exit 1
if [ -x /usr/bin/gptokeyb ] && [ -r "$GAMEDIR/mgs2.gptk" ]; then
    /usr/bin/gptokeyb "$EXE" -c "$GAMEDIR/mgs2.gptk" >/tmp/mgs2-gptokeyb.log 2>&1 &
    GPTOKEYB_PID=$!
fi

if type taskset >/dev/null 2>&1; then
    taskset -c 0-3 box64 /usr/bin/wine "$EXE" &
else
    box64 /usr/bin/wine "$EXE" &
fi
WINE_PID=$!

# Improved cooling permits a fixed 1992 MHz target. Keep only the independent
# emergency cutoff below the observed reset region; there is no frequency
# ladder in PLAY.
thermal_guard() {
    local temp fifo
    fifo=$(mktemp -u /tmp/mgs2-play-guard.XXXXXX)
    if mkfifo "$fifo" 2>/dev/null; then
        exec 8<>"$fifo"
        rm -f "$fifo"
    fi
    while kill -0 "$WINE_PID" 2>/dev/null; do
        temp=0
        read -r temp < /sys/class/thermal/thermal_zone0/temp 2>/dev/null || temp=0
        [ -n "$temp" ] || temp=0
        if [ "$temp" -ge 88000 ]; then
            kill "$WINE_PID" 2>/dev/null || true
            return
        fi
        if [ -e /proc/self/fd/8 ]; then
            read -r -t 0.5 -u 8 _ 2>/dev/null || true
        else
            sleep 0.5
        fi
    done
}
thermal_guard &
THERMAL_PID=$!
wait "$WINE_PID"

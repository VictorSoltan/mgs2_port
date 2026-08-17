#!/bin/bash
# MGS2 Substance RG353VS -- PROBE run, dynarec knobs overridable from env, (patch 27 + memory ring). MIN30 base: the smallest stack measured at 30 fps.
# Keeps exactly what buys frame rate: the GLES foundation, Box86's native memmove
# bridge and mutex fix, and the FINALPLAY2 renderer pair (patches 12+25+26) that
# brief #43 measured at 30.0/30.0/30.1 fps on the former 20-fps spot.
# Dropped: patch 27 (separable stages -- hitches only, no per-frame effect) and
# patch 05 (ntdll yield -- inert, its MGS2_YIELD switch is never set).
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
export BOX86_DYNAREC_SAFEFLAGS="${BOX86_DYNAREC_SAFEFLAGS:-0}"
export BOX86_DYNAREC_BIGBLOCK="${BOX86_DYNAREC_BIGBLOCK:-2}"
export BOX86_DYNAREC_FORWARD="${BOX86_DYNAREC_FORWARD:-512}"
export BOX86_DYNAREC_CALLRET="${BOX86_DYNAREC_CALLRET:-1}"
# Device profile at the fixed Game Data 02 spot attributes 31% of main-thread
# samples to Wine's guest _sse2_memmove.  The patched Box86 recognises that
# exact Wine 11 prologue and executes the same overlap-safe operation in native
# ARM libc; zero-length copies return directly. No pixels, game state, or copy
# semantics are removed.
export MGS2_BOX86_NATIVE_MEMMOVE=1

# Measured presentation and the two retained non-renderer fixes.
export MGS2_GL_PBO=0
export MGS2_GL_FLIP=0
export MGS2_GL_BGRA=1

# Diagnostic run. v9_probe is an unstripped non-FINAL build, so it reads the env
# knobs the FINAL DLLs have compiled in -- omitting them broke the codec portrait
# once already. The ring is memory-only; nothing is written from a hot thread.
export MGS2_GLES_FBO_READBACK=1
export MGS2_SKIP_CODEC_BLACK_QUAD=0
export MGS2_GPU_PROBE=1
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
mount_bind "$GAMEDIR/box86-native-memmove3" /usr/bin/box86 || exit 1
mount_bind "$GAMEDIR/win32u_glfuncs3.so" /usr/lib/wine/i386-unix/win32u.so || exit 1
mount_bind "$GAMEDIR/winewayland_stall1.so" /usr/lib/wine/i386-unix/winewayland.so || exit 1
mount_bind "$GAMEDIR/opengl32_finalplay_sso.so" /usr/lib/wine/i386-unix/opengl32.so || exit 1
# ntdll_fastyield.so is deliberately NOT mounted. Patch 05 consists solely of an
# NtYieldExecution switch gated on MGS2_YIELD, which production never sets, so the
# module ran stock while still placing a custom rebuild of a core Wine module over
# the system one: no benefit, real risk surface. Removed 2026-08-12; the module
# stays in binaries/ and one mount_bind line brings it back if MGS2_YIELD=fast is
# ever worth measuring. See MGS2_SEPARABLE_FREEZE_CAPTURE_2026-08-12.md section 8.
mount_bind "$GAMEDIR/wined3d_separable_v9_probe.dll" /usr/lib/wine/i386-windows/wined3d.dll || exit 1
mount_bind "$GAMEDIR/user32_peek1.dll" /usr/lib/wine/i386-windows/user32.dll || exit 1
# FINALPLAY2 keeps DISCARD writes in the cached producer shadow. This removes
# two 512 KiB readbacks per frame from WineD3D's mapped upload memory while the
# existing dirty flush publishes the identical bytes before drawing. Measured
# at the fixed heavy spot: three consecutive windows at 30.0/30.0/30.1 fps.
mount_bind "$GAMEDIR/d3d8_finalplay2.dll" /usr/lib/wine/i386-windows/d3d8.dll || exit 1
mount_bind "$GAMEDIR/dmsynth_se4_unmute1.dll" /usr/lib/wine/i386-windows/dmsynth.dll || exit 1
mount_bind "$GAMEDIR/dsound_se1.dll" /usr/lib/wine/i386-windows/dsound.dll || exit 1
mount_bind "$GAMEDIR/dmime_transition1.dll" /usr/lib/wine/i386-windows/dmime.dll || exit 1
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

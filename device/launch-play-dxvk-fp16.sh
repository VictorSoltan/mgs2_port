#!/bin/bash
# FINALPLAY16: MGS2 D3D8 -> DXVK-Sarek -> proprietary Mali Vulkan.
# Promoted on the owner's gameplay judgement on 2026-08-24. The previous
# FINALPLAY15 WineD3D runtime remains byte-exact in launch-play-wined3d-fp15.sh.

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

# Production runs exactly one bundle, and it is not selectable from the
# environment.
#
# Each of these variables used to do two things: pick a different binary, and
# switch off the identity check for all the OTHER mounted files. So one stale
# exported value from an earlier measurement -- MGS2_WINED3D_DLL left in a shell,
# a sourced profile line -- silently produced frame times, screenshots and crash
# reports for a build nobody had assembled on purpose, with box86's class-B
# registry mapping the RVAs of a DLL that was no longer mounted.
#
# Named research launchers use their own runtime or the preserved FINALPLAY15
# launcher. This production runtime never accepts a binary-selection override.
mgs2_reject_research_overrides() {
    found=""
    for v in MGS2_BOX86_BIN MGS2_WINED3D_DLL MGS2_WAYLAND_SO MGS2_D3D8_DLL \
             MGS2_DXVK_D3D8_DLL MGS2_DXVK_D3D9_DLL \
             MGS2_DMSYNTH_DLL MGS2_DSOUND_DLL MGS2_DMIME_DLL \
             MGS2_WINEDLLOVERRIDES MGS2_BOX86_EMULATED_LIBS; do
        eval "value=\${$v:-}"
        [ -n "$value" ] && found="$found $v=$value"
    done
    [ -n "$found" ] || return 0
    echo "MGS2: refusing to launch -- a research binary override reached the" \
         "production launcher:$found" >&2
    echo "MGS2: run it deliberately with device/launch-research.sh, or use the" \
         "named launch-*.sh for that experiment" >&2
    exit 1
}
mgs2_reject_research_overrides

# This is one fixed production bundle, not the research selector. Keep these
# assignments after the stale-override check so inherited experiment variables
# cannot assemble an accidental hybrid.
MGS2_BOX86_BIN=box86-fp16-dxvk
MGS2_DXVK_D3D8_DLL=d3d8_dxvk_sarek_1.11.1_mali_wsiinit3.dll
MGS2_DXVK_D3D9_DLL=d3d9_dxvk_sarek_1.11.1_mali_nullfix1.dll
MGS2_DXVK_WINE_MODE=direct32
MGS2_BOX86_EMULATED_LIBS='winewayland.so:winevulkan.so:libffi.so.8:libwayland-egl.so.1:libxkbcommon.so.0:libxkbregistry.so.0:libxml2.so.2:libicuuc.so.72:libicudata.so.72:liblzma.so.5:libstdc++.so.6'
MGS2_WINEDLLOVERRIDES='mscoree=;mshtml=;winemenubuilder.exe=;winepulse.drv=d;d3d8=n,b;d3d9=n,b;dxgi=builtin'
export MGS2_BOX86_BIN MGS2_DXVK_D3D8_DLL MGS2_DXVK_D3D9_DLL
export MGS2_DXVK_WINE_MODE MGS2_BOX86_EMULATED_LIBS MGS2_WINEDLLOVERRIDES

exec 9>/tmp/mgs2-substance.lock
flock -n 9 || exit 0

DXVK_WINE_MODE=${MGS2_DXVK_WINE_MODE:-wow64}
if [ -n "${MGS2_DXVK_D3D8_DLL:-}" ] && [ "$DXVK_WINE_MODE" = direct32 ]; then
    export WINEPREFIX="$GAMEDIR/wineprefix11-x86-dxvk-test"
    export WINEARCH=win32
    export WINELOADER=/usr/lib/wine/i386-unix/wine
else
    export WINEPREFIX="$GAMEDIR/wineprefix64"
    unset WINEARCH WINELOADER
fi
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
export MGS2_DMSYNTH_POLYPHONY=${MGS2_DMSYNTH_POLYPHONY:-48}
export MGS2_DMSYNTH_IDLE_SKIP=0
export MGS2_DMSYNTH_UNMUTE_NOTES=0

# The production arm deliberately keeps the cold state-cache policy and hides
# the research HUD. None of these variables writes from a render hot path.
export DXVK_STATE_CACHE=0
export DXVK_LOG_LEVEL=warn
export DXVK_LOG_PATH="$GAMEDIR/logs/dxvk-sarek"
export DXVK_HUD=
mkdir -p "$DXVK_LOG_PATH"

export WINEDLLOVERRIDES="${MGS2_WINEDLLOVERRIDES:-mscoree=;mshtml=;winemenubuilder.exe=;winepulse.drv=d;d3d8=builtin;d3d9=builtin;dxgi=builtin}"
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/var/run/0-runtime-dir}
export WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-wayland-1}
export BOX64_LD_LIBRARY_PATH="/usr/share/box64/lib:$GAMEDIR/x64libs"
export BOX64_EMULATED_LIBS='libwayland-client.so.0:libffi.so.8:libwayland-egl.so.1'
export BOX64_LOG=0 BOX64_NOBANNER=1
if [ "$DXVK_WINE_MODE" = direct32 ]; then
    export BOX86_LD_LIBRARY_PATH="/usr/share/box86/lib:/usr/lib/wine/i386-unix:$GAMEDIR/x86libs"
else
    export BOX86_LD_LIBRARY_PATH="/usr/share/box86/lib:$GAMEDIR/x86libs"
fi
export BOX86_EMULATED_LIBS="${MGS2_BOX86_EMULATED_LIBS:-libwayland-client.so.0:libffi.so.8:libwayland-egl.so.1:libxkbcommon.so.0:libxkbregistry.so.0:libxml2.so.2:libicuuc.so.72:libicudata.so.72:liblzma.so.5:libstdc++.so.6}"
export BOX86_LOG="${MGS2_BOX86_LOG:-0}" BOX86_NOBANNER=1
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
# The 2026-08-14 live freeze captured wine_dinput_worker waiting on Wine's
# session_lock while the backing ARM mutex named that same thread as owner.
# Box86 patch 03 made first publication safe, but this second occurrence proves
# that its shadow mutex pool is still not a safe production boundary here.
# ROCKNIX armhf and this Wine i386 build both use a 24-byte, 4-byte-aligned
# pthread_mutex_t with lock/count/owner/kind/nusers at identical offsets, so use
# Box86's upstream direct-mutex mode and bypass the shadow pool completely.
# This does not alter Wine locking semantics; set 0 only for rollback diagnosis.
export BOX86_MUTEX_ALIGNED="${BOX86_MUTEX_ALIGNED:-1}"
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
    if [ ! -r "$src" ]; then
        echo "MGS2: cannot bind $src over $dst -- source is unreadable" >&2
        return 1
    fi
    while grep -q " $dst " /proc/mounts; do
        if [ -f "$src" ] && [ -f "$dst" ] && cmp -s "$src" "$dst"; then
            return 0
        fi
        if ! umount "$dst" 2>/dev/null; then
            echo "MGS2: cannot replace busy bind mount $dst" >&2
            return 1
        fi
    done
    if ! mount --bind "$src" "$dst"; then
        echo "MGS2: bind mount failed: $src -> $dst" >&2
        return 1
    fi
}

unmount_all() {
    local dst="$1" tries
    while grep -q " $dst " /proc/mounts; do
        tries=0
        while ! umount "$dst" 2>/dev/null; do
            tries=$((tries + 1))
            if [ "$tries" -ge 20 ]; then
                echo "MGS2: cleanup could not unmount busy $dst" >&2
                return 1
            fi
            sleep 0.1
        done
    done
}

CPU_POLICIES=$(ls -d /sys/devices/system/cpu/cpufreq/policy* 2>/dev/null)
SAVED_GOV=""
SAVED_MAX=""

GPU_DEVFREQ=/sys/class/devfreq/fde60000.gpu
SAVED_GPU_GOV=""

save_cpu_state() {
    local p
    for p in $CPU_POLICIES; do
        SAVED_GOV="$SAVED_GOV $p:$(cat "$p/scaling_governor" 2>/dev/null)"
        SAVED_MAX="$SAVED_MAX $p:$(cat "$p/scaling_max_freq" 2>/dev/null)"
    done
    SAVED_GPU_GOV="$(cat "$GPU_DEVFREQ/governor" 2>/dev/null)"
}

set_final_cpu_cap() {
    local p
    for p in $CPU_POLICIES; do
        echo performance > "$p/scaling_governor" 2>/dev/null
        echo 1992000 > "$p/scaling_max_freq" 2>/dev/null
    done
    # The GPU sat on simple_ondemand and spent the reinforcement scene at
    # 400-600 of its 800 MHz. The dead-end list said pinning it to 800 was a net
    # loss because the CPU cap then fell to 816 MHz on a shared thermal budget --
    # that was measured before the cooling was fixed, and it no longer holds.
    #
    # Re-measured 2026-08-16, one process, one spot (the autoload save), governor
    # switched live, arms interleaved ondemand/performance/ondemand/performance:
    #
    #   simple_ondemand   n=35  median 15.20 fps  mean 15.21  sd 0.23
    #   performance       n=39  median 16.90 fps  mean 16.85  sd 0.09
    #   +1.64 fps, +10.8%, and the two ranges do not overlap at all
    #
    # The CPU stayed at 1992000 in every arm -- the old throttling did not
    # recur -- ending at 78.1 C CPU / 73.3 C GPU, well under the 88 C cutoff.
    # MGS2_GPU_GOVERNOR=simple_ondemand reverts it for one run.
    echo "${MGS2_GPU_GOVERNOR:-performance}" > "$GPU_DEVFREQ/governor" 2>/dev/null
}

restore_cpu_state() {
    local e p v
    [ -n "$SAVED_GPU_GOV" ] && echo "$SAVED_GPU_GOV" > "$GPU_DEVFREQ/governor" 2>/dev/null
    for e in $SAVED_MAX; do
        p="${e%%:*}"; v="${e##*:}"
        [ -n "$v" ] && echo "$v" > "$p/scaling_max_freq" 2>/dev/null
    done
    for e in $SAVED_GOV; do
        p="${e%%:*}"; v="${e##*:}"
        [ -n "$v" ] && echo "$v" > "$p/scaling_governor" 2>/dev/null
    done
}

# Arm cleanup before the first bind mount.  A missing or unreadable selected
# runtime must not leave the earlier mounts active for the next launch.
cleanup() {
    [ -n "${WINE_PID:-}" ] && kill "$WINE_PID" 2>/dev/null || true
    [ -n "${EXPLORER_PID:-}" ] && kill "$EXPLORER_PID" 2>/dev/null || true
    [ -n "${GPTOKEYB_PID:-}" ] && kill "$GPTOKEYB_PID" 2>/dev/null || true
    killall -9 wineserver wineboot.exe services.exe explorer.exe winedevice.exe plugplay.exe svchost.exe rpcss.exe 2>/dev/null || true
    pkill -9 -f '[m]gs2_sse_rg353vs_port.exe' 2>/dev/null || true
    # A Wine child can remain visible briefly after SIGKILL and keep a bind
    # mount busy. Wait only in teardown, before attempting to restore targets.
    i=0
    while pgrep -f '[w]ineboot.exe|[e]xplorer.exe|[m]gs2_sse_rg353vs_port.exe' >/dev/null 2>&1 \
          && [ "$i" -lt 20 ]; do
        sleep 0.1
        i=$((i + 1))
    done
    restore_cpu_state
    unmount_all /usr/lib/wine/i386-windows/wined3d.dll
    unmount_all /usr/lib/wine/i386-windows/d3d8.dll
    [ -n "${DXVK_D3D8_TARGET:-}" ] && unmount_all "$DXVK_D3D8_TARGET"
    [ -n "${DXVK_D3D9_TARGET:-}" ] && unmount_all "$DXVK_D3D9_TARGET"
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

# FINALPLAY3 also serialises Box86's first-use allocation and publication of
# an x86 mutex's native ARM backing mutex.  The old two-stage publication was
# captured leaving Wine's shared-session lock owned forever when concurrent
# first users selected different native mutexes.  This changes no Wine lock
# semantics and retains the measured native memmove path from FINALPLAY2.
# FINALPLAY6 promoted the native ARM WineD3D island. FINALPLAY8 keeps that pair's
# WineD3D DLL and promotes island41 with one additional measured route. 32
# WineD3D sources are compiled for armhf and linked into Box86; 18 entry points
# are routed to them,
# recognised by a marker in the guest prologue. Read this before trusting it:
#
#   Entry 10, wined3d_buffer_load, IS routed, and it is the one entry here
#   carried by a measurement rather than by judgement:
#
#       routed      60.6 ms/frame
#       unrouted    69.4 ms/frame
#       difference  median -8.87 ms/f, -12.8%, 30 of 30 cycles, se 0.44 ms
#
#   That is about +2.1 fps on the reinforcement scene. It was measured with
#   MGS2_ISLAND_AB=10, which switches that one entry between the native ARM
#   route and the guest body every 64 displayed frames, ABBA, inside ONE live
#   process. Eight separate playthroughs had previously measured nothing at
#   all, because the scene moves between runs by more than 9 ms/frame.
#
#   Routing it required the class-B resolver: the dispatch inside its closure
#   goes through pointers held in guest structures, and 21,433,346 of
#   21,433,463 of those calls target a function the island already has natively.
#
#   Entry 4, mgs2_batch_flush, is the second performance-promoted route. In ten
#   stable same-process ABBA pairs at the fixed reinforcement spot it measured
#   53.466 ms/frame routed against 56.050 guest: paired median -2.680 ms/frame,
#   +0.899 fps (+4.8%), with 10/10 stable pairs and zero island faults. The
#   island31/p56 pair shares the authoritative guest batch state; do not mix
#   island31 with an older WineD3D DLL.
#
#   Entry 23, wined3d_rendertarget_view_load_location, is the third
#   performance-promoted route. In the owner's heavy scene its balanced-pair
#   median was -1.944 ms/frame (about +1.3 fps); the paired mean was -2.614
#   ms/frame. Do not quote the withdrawn sigma or sign-test p: 20 of the 25
#   balanced cycles were one deterministic stretch, not independent trials.
#   A later production-candidate soak presented 6300 frames across normal play,
#   with correct picture reported by the owner and zero island faults.
#
#   The other 15 remain promoted on the owner's judgement, not on a number.
#   They are exactly those with no reachable abort stub, no NtCurrentTeb read
#   and no indirect call, from harness/island/full/island_reach.py. Anything
#   else must not be added without re-running it.
#
#   MGS2_ISLAND_AB is CLEARED here, not merely left unset, and this is not
#   defensive tidiness. The A/B harness deliberately runs half the frames
#   through the guest path, so a value leaking in from a parent shell -- an
#   exported measurement variable, a stale profile line -- would silently give
#   back about half of the 8.87 ms and look like the island regressing. It is
#   the one variable in this launcher whose accidental presence costs
#   performance rather than causing an obvious failure, so it is cleared here.
#
#   A measurement run opts in under a DIFFERENT name, which is the point: the
#   variable that can leak is not the variable that arms the harness, so an
#   inherited environment cannot turn play into a measurement.
#   device/launch-island-ab.sh sets MGS2_ISLAND_AB_MEASURE.
unset MGS2_ISLAND_AB
if [ -n "${MGS2_ISLAND_AB_MEASURE:-}" ]; then
    export MGS2_ISLAND_AB="$MGS2_ISLAND_AB_MEASURE"
    echo "MGS2: A/B harness armed on island entry $MGS2_ISLAND_AB -- this is a" \
         "MEASUREMENT run, half the frames deliberately run unrouted" >&2
fi
#
# The native island contains WineD3D code and is not part of the DXVK renderer.
export MGS2_BOX86_ISLAND_FULL=0
# Entry 41 is the fused A+B+C draw-state root (p72c). It ships here because
# the 144-minute session that validated the p75a selector ran with exactly
# this list; promoting a different one would ship something unplayed.
export MGS2_BOX86_ISLAND_ONLY="${MGS2_BOX86_ISLAND_ONLY:-0,1,2,3,4,5,6,9,10,14,18,19,22,23,28,29,32,33,41}"
# The x87 float-RGBA -> RGBA8 dither converter at mgs2_sse_rg353vs_port.exe
# +0x50dae1, replaced by a native ARM one. It is 44.7% of the main thread's CPU
# during the multi-second freeze after a save loads. Still a switch, so the A/B
# can be rerun without rebuilding: MGS2_BOX86_NATIVE_DITHER=0 restores the guest.
export MGS2_BOX86_NATIVE_DITHER="${MGS2_BOX86_NATIVE_DITHER:-1}"

# DXVK needs the system Vulkan-capable Wine modules. A power-loss can prevent a
# previous WineD3D launcher's EXIT trap from removing its bind mounts, so clear
# every mutually-exclusive renderer mount before installing the DXVK bundle.
unmount_all /usr/lib/wine/i386-unix/win32u.so
unmount_all /usr/lib/wine/i386-unix/winewayland.so
unmount_all /usr/lib/wine/i386-unix/opengl32.so
unmount_all /usr/lib/wine/i386-windows/wined3d.dll
unmount_all /usr/lib/wine/i386-windows/user32.dll
unmount_all /usr/lib/wine/i386-windows/d3d8.dll
mount_bind "$GAMEDIR/${MGS2_BOX86_BIN:-box86-fp15}" /usr/bin/box86 || exit 1
if [ -z "${MGS2_DXVK_D3D8_DLL:-}" ]; then
    mount_bind "$GAMEDIR/win32u_glfuncs3.so" /usr/lib/wine/i386-unix/win32u.so || exit 1
fi
# Diagnostics may select a separate presenter build, but normal play keeps the
# measured production driver.  This is used by p67 only for a bounded,
# memory-only frame-content witness; it does not change the production default.
# DXVK presents through Vulkan WSI. The WineD3D-specific custom dmabuf presenter
# is not mounted in this arm and its control must remain dormant.
export MGS2_GL_DMABUF=0
export MGS2_GL_DMABUF_SYNC="${MGS2_GL_DMABUF_SYNC:-3}"
if [ -z "${MGS2_DXVK_D3D8_DLL:-}" ]; then
    mount_bind "$GAMEDIR/${MGS2_WAYLAND_SO:-winewayland_dmabuf_prod.so}" /usr/lib/wine/i386-unix/winewayland.so || exit 1
fi
if [ -z "${MGS2_DXVK_D3D8_DLL:-}" ]; then
    mount_bind "$GAMEDIR/opengl32_finalplay_sso.so" /usr/lib/wine/i386-unix/opengl32.so || exit 1
fi
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
# Patch 51 is p32 plus the island entry markers, with the laboratory counters
# (p46 entry census, p50 indirect-call census) compiled out. The markers are not
# instrumentation -- Box86 needs them to recognise an entry at all.
# harness/island/full/island_marker_check.py verifies every id appears in exactly
# one function AND inside Box86's matching window; nine of them used to sit past
# the old 16-byte window and could never match, which read as "armed but not
# called" until the check was written.
# Patch 52 rides along: a memory-only census of the WineD3D CS synchronisation
# events. The freeze that is still open has been captured three times, every one
# of them in real play and never under a harness -- an accelerated soak with the
# spin count at 1 could not provoke it in 30 minutes. So instrument what does
# provoke it. The census records submits, alerts and wait enter/return, never
# draws, and publishes the live cs pointer and field offsets so that
# harness/cs_deadlock_census.py can answer the question no previous capture
# could: were commands published while the consumer slept (A), or were the
# queues empty and the fault elsewhere (B)?
#
# Cost is a handful of counter writes per sync event. MGS2_CS_DEADLOCK_CENSUS=0
# turns it off; the DLL is otherwise identical to p51.
#
# p55 supersedes p52 and KEEPS that census -- it is p52 plus 8538 bytes: the
# class-B/C plumbing entry 10 needs. Checked byte-wise rather than assumed,
# because losing the census here would silently end the freeze investigation
# that has been waiting for a natural occurrence.
#
# The rest of p55 is the GL side of routing: gl_ops is translated once per
# device, keyed on each slot's POSITION in the struct rather than on the address
# it holds. Both sides generate that struct from the same four macro lists, so
# the position already carries the name. The address-keyed version resolved 3
# slots of 493 and wrote the other 490 back as NULL, which then faulted in-game
# minutes later; by name it resolves 233, and the 260 still unresolved are not
# reached by any armed entry.
#
# p56 adds the cold guest-batch accessor required by the island. Keep it paired
# with island41. box86-island32-prod + this same p56 DLL + the old 17-entry
# allow-list is the immediate rollback; p55 + island29 remains the older exact
# pre-FINALPLAY6 rollback.
export MGS2_CS_DEADLOCK_CENSUS="${MGS2_CS_DEADLOCK_CENSUS:-1}"
if [ -z "${MGS2_DXVK_D3D8_DLL:-}" ]; then
    mount_bind "$GAMEDIR/${MGS2_WINED3D_DLL:-wined3d_fp15.dll}" /usr/lib/wine/i386-windows/wined3d.dll || exit 1
    # This user32 and the production win32u were built as one Wine patch set.
    # DXVK deliberately uses ROCKNIX's Vulkan-capable win32u, so keep its
    # matching system user32 as well.
    mount_bind "$GAMEDIR/user32_peek1.dll" /usr/lib/wine/i386-windows/user32.dll || exit 1
fi
# FINALPLAY2 keeps DISCARD writes in the cached producer shadow. This removes
# two 512 KiB readbacks per frame from WineD3D's mapped upload memory while the
# existing dirty flush publishes the identical bytes before drawing. Measured
# at the fixed heavy spot: three consecutive windows at 30.0/30.0/30.1 fps.
# Patch 28 removes the visibility culler's AABB cache, measured dead: cache_hit=0
# against cache_miss=112800 over 300 frames, because the key includes a geometry
# generation the game bumps every frame. Frees 73,760 bytes of BSS and 848 bytes
# of code, and cannot change a culling decision. The culler itself stays: measured
# 44.3 fps with it against 37.7 without, over two 400 s windows.
if [ -z "${MGS2_DXVK_D3D8_DLL:-}" ]; then
    mount_bind "$GAMEDIR/${MGS2_D3D8_DLL:-d3d8_finalplay3_nocullcache.dll}" /usr/lib/wine/i386-windows/d3d8.dll || exit 1
fi

# FINALPLAY16 native renderer pair. MGS2 ships an app-local d3d8.dll, which
# has priority over the prefix for a native override, so D3D8 must replace that
# exact target. D3D9 lives in the prefix. Both are bind mounts and are verified
# without overwriting either original file.
if [ -n "${MGS2_DXVK_D3D8_DLL:-}" ] || [ -n "${MGS2_DXVK_D3D9_DLL:-}" ]; then
    [ -n "${MGS2_DXVK_D3D8_DLL:-}" ] && [ -n "${MGS2_DXVK_D3D9_DLL:-}" ] || exit 1
    DXVK_D3D8_TARGET="$GAMEDIR/game/bin/d3d8.dll"
    if [ "$DXVK_WINE_MODE" = direct32 ]; then
        DXVK_D3D9_TARGET="$WINEPREFIX/drive_c/windows/system32/d3d9.dll"
    else
        DXVK_D3D9_TARGET="$WINEPREFIX/drive_c/windows/syswow64/d3d9.dll"
    fi
    mount_bind "$GAMEDIR/$MGS2_DXVK_D3D8_DLL" "$DXVK_D3D8_TARGET" || exit 1
    mount_bind "$GAMEDIR/$MGS2_DXVK_D3D9_DLL" "$DXVK_D3D9_TARGET" || exit 1
    cmp -s "$GAMEDIR/$MGS2_DXVK_D3D8_DLL" "$DXVK_D3D8_TARGET" || exit 1
    cmp -s "$GAMEDIR/$MGS2_DXVK_D3D9_DLL" "$DXVK_D3D9_TARGET" || exit 1
fi

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

# FINALPLAY14 identity check, on the MOUNTED files rather than on what was asked
# for, and on ALL of them.
#
# It used to name three: box86, wined3d and the presenter -- the files
# make_release.sh happened to build. The launcher also replaces win32u.so,
# opengl32.so, user32.dll, d3d8.dll and four DirectMusic/DirectSound modules, so
# eight of the eleven substitutions were never verified, and four of them were
# mounted after the check even ran. harness/make_release.sh now generates the
# manifest FROM the mount_bind lines below, and the coverage assertion here reads
# the same lines back, so the two cannot drift apart again without failing.
#
# There is no off switch. Binary-selection overrides are rejected at the top and
# every manifest mismatch remains fatal.
mgs2_verify_identity() {
    manifest="$GAMEDIR/FINALPLAY16_DXVK.manifest"
    if [ ! -r "$manifest" ]; then
        echo "MGS2: no $manifest, cannot verify identity" >&2
        return 1
    fi
    # Seven bind-mounted production files: Box86, D3D8, D3D9 and four audio
    # modules. The same manifest also pins the unmounted Vulkan/Wine/libmali
    # dependencies, so checked may legitimately be greater than mounts.
    mounts=7
    checked=0
    bad=0
    while read -r path want src; do
        case "$path" in ''|\#*) continue;; esac
        checked=$((checked + 1))
        got=$(sha256sum "$path" 2>/dev/null | cut -d" " -f1)
        if [ "$got" != "$want" ]; then
            echo "MGS2: $path is ${got:-missing}, manifest expects $want ($src)" >&2
            bad=$((bad + 1))
        fi
    done < "$manifest"
    if [ "$checked" -lt "$mounts" ]; then
        echo "MGS2: refusing to launch -- the manifest covers $checked files and this" \
             "launcher binds $mounts; regenerate it with harness/make_release.sh" >&2
        return 1
    fi
    if [ "$bad" != 0 ]; then
        echo "MGS2: refusing to launch -- $bad of $checked runtime files do not" \
             "match the manifest" >&2
        return 1
    fi
    echo "MGS2: identity verified, $checked of $checked runtime files match" \
         "FINALPLAY16_DXVK.manifest" >&2
}

mgs2_verify_identity || exit 1

save_cpu_state
set_final_cpu_cap

cd "$GAMEDIR/game/bin" || exit 1

# MGS2 imports D3D8 before it creates its own window. On the Vulkan arm, let
# Wine's Wayland desktop finish its cold driver startup first; otherwise the
# game process can reach winevulkan while win32u still exposes the null driver.
if [ -n "${MGS2_DXVK_D3D8_DLL:-}" ]; then
    if [ "$DXVK_WINE_MODE" = direct32 ]; then
        box86 /usr/lib/wine/i386-unix/wine explorer /desktop 9>&- >/tmp/mgs2-dxvk-explorer.log 2>&1 &
    else
        box64 /usr/bin/wine explorer /desktop 9>&- >/tmp/mgs2-dxvk-explorer.log 2>&1 &
    fi
    EXPLORER_PID=$!
    i=0
    while [ "$i" -lt 40 ] && ! pgrep -f '[e]xplorer.exe.*/desktop' >/dev/null 2>&1; do
        sleep 0.25
        i=$((i + 1))
    done
    # Process creation precedes Wayland registry enumeration and the desktop
    # ready signal. This is a bounded cold-start wait, not a render-path delay.
    sleep 3
fi

if [ -x /usr/bin/gptokeyb ] && [ -r "$GAMEDIR/mgs2.gptk" ]; then
    /usr/bin/gptokeyb "$EXE" -c "$GAMEDIR/mgs2.gptk" 9>&- >/tmp/mgs2-gptokeyb.log 2>&1 &
    GPTOKEYB_PID=$!
fi

if [ "$DXVK_WINE_MODE" = direct32 ] && type taskset >/dev/null 2>&1; then
    taskset -c 0-3 box86 /usr/lib/wine/i386-unix/wine "$EXE" 9>&- &
elif [ "$DXVK_WINE_MODE" = direct32 ]; then
    box86 /usr/lib/wine/i386-unix/wine "$EXE" 9>&- &
elif type taskset >/dev/null 2>&1; then
    taskset -c 0-3 box64 /usr/bin/wine "$EXE" 9>&- &
else
    box64 /usr/bin/wine "$EXE" 9>&- &
fi
WINE_PID=$!
PLAY_WINE_PID=$WINE_PID
PLAY_EXIT_LOG=/tmp/mgs2-play-exit.log
if wait "$WINE_PID"; then
    PLAY_EXIT_STATUS=0
else
    PLAY_EXIT_STATUS=$?
fi
WINE_PID=
printf '%s launcher=finalplay16 pid=%s status=%s\n' \
    "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$PLAY_WINE_PID" \
    "$PLAY_EXIT_STATUS" > "$PLAY_EXIT_LOG"
exit "$PLAY_EXIT_STATUS"

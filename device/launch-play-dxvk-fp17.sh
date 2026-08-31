#!/bin/bash
# Shared fixed-bundle engine for FINALPLAY17 through FINALPLAY22 and bounded
# follow-up candidates. Direct execution selects the exact FINALPLAY17 rollback.
# The newer wrappers select complete closed routes; arbitrary renderer/input
# combinations are rejected.

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
GAME_EXE_TARGET="$GAMEDIR/game/bin/$EXE"
PATCHED_GAME_EXE=""

# The tracked wrappers intentionally select one complete named bundle through
# MGS2_PRODUCTION_ROUTE. Individual binary/input/timing overrides are refused.
#
# Each of these variables used to do two things: pick a different binary, and
# switch off the identity check for all the OTHER mounted files. So one stale
# exported value from an earlier measurement -- MGS2_WINED3D_DLL left in a shell,
# a sourced profile line -- silently produced frame times, screenshots and crash
# reports for a build nobody had assembled on purpose, with box86's class-B
# registry mapping the RVAs of a DLL that was no longer mounted.
#
# Named research launchers use their own runtime or the preserved FINALPLAY15
# launcher. This shared runtime accepts its closed bundle selector, but never a
# component-level binary-selection override.
mgs2_reject_research_overrides() {
    found=""
    for v in MGS2_BOX86_BIN MGS2_WINED3D_DLL MGS2_WAYLAND_SO MGS2_D3D8_DLL \
             MGS2_DXVK_D3D8_DLL MGS2_DXVK_D3D9_DLL \
             MGS2_DMSYNTH_DLL MGS2_DSOUND_DLL MGS2_DMIME_DLL \
             MGS2_WINEDLLOVERRIDES MGS2_BOX86_EMULATED_LIBS \
             MGS2_INPUT_ROUTE \
             MGS2_DMSYNTH_WATCHDOG_MS MGS2_DMSYNTH_WATCHDOG_STALL \
             MGS2_BOX86_NATIVE_DXT MGS2_BOX86_NATIVE_DXT_SURFACE \
             MGS2_BOX86_NATIVE_AABB MGS2_ISLAND_AB_MEASURE \
             MGS2_DXVK_STATE_CACHE_DEDUPE MGS2_DXVK_PIPELINE_TRACE \
             DXVK_STATE_CACHE DXVK_STATE_CACHE_PATH DXVK_CONFIG \
             DXVK_ALL_CORES; do
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

# These are complete, named production/rollback bundles, not binary selectors. Keep
# this closed case after the stale-override check so inherited experiment
# variables cannot assemble an accidental hybrid. FINALPLAY17 remains the exact
# p21 rollback; FINALPLAY18 changes only Box86 to the verified p24 ABI fix;
# FINALPLAY19 adds the p25 text-input ABI fix, the p26 reproducible-build
# boundary and immediate input; FINALPLAY20 adds the p37 DMSynth transport and
# stale-timeline resume repair; FINALPLAY21 selects the game's existing
# fixed-function wpatch renderer for the sea surface; FINALPLAY22 additionally
# owns the wpatch state and repairs dmime/dmsynth lifetime failures.
PRODUCTION_ROUTE=${MGS2_PRODUCTION_ROUTE:-finalplay17}
GAME_EXE_PATCH=none
EXPECTED_BIND_MOUNTS=7
EXPECTED_IDENTITY_ROWS=
case "$PRODUCTION_ROUTE" in
    finalplay17)
        MGS2_BOX86_BIN=box86-fp21-dxvk-native-dxt-surface
        PLAY_IDENTITY_MANIFEST=FINALPLAY17_DXVK_FREEZE.manifest
        EXPECTED_IDENTITY_ROWS=18
        INPUT_ROUTE=legacy
        ;;
    finalplay18)
        MGS2_BOX86_BIN=box86-fp24-wayland-atomic-production
        PLAY_IDENTITY_MANIFEST=FINALPLAY18_WAYLAND_ABI.manifest
        EXPECTED_IDENTITY_ROWS=18
        INPUT_ROUTE=legacy
        ;;
    finalplay19)
        MGS2_BOX86_BIN=box86-fp26-wayland-text-input-production
        PLAY_IDENTITY_MANIFEST=FINALPLAY19_INPUT_WAYLAND.manifest
        EXPECTED_IDENTITY_ROWS=19
        INPUT_ROUTE=immediate-production
        ;;
    finalplay20)
        MGS2_BOX86_BIN=box86-fp26-wayland-text-input-production
        PLAY_IDENTITY_MANIFEST=FINALPLAY20_DMSYNTH_RESUME.manifest
        EXPECTED_IDENTITY_ROWS=19
        INPUT_ROUTE=immediate-production
        MGS2_DMSYNTH_DLL=dmsynth_p37_resume_timeline.dll
        MGS2_DMSYNTH_WATCHDOG_MS=250
        MGS2_DMSYNTH_WATCHDOG_STALL=1
        export MGS2_DMSYNTH_WATCHDOG_MS MGS2_DMSYNTH_WATCHDOG_STALL
        ;;
    finalplay23)
        MGS2_BOX86_BIN=box86-fp26-wayland-text-input-production
        PLAY_IDENTITY_MANIFEST=FINALPLAY23_MOVIE_GUARD.manifest
        EXPECTED_IDENTITY_ROWS=21
        INPUT_ROUTE=immediate-production
        MGS2_DMSYNTH_DLL=dmsynth_p38_sink_lifetime.dll
        MGS2_DMIME_DLL=dmime_p16_curve_state_layout.dll
        MGS2_DMSYNTH_WATCHDOG_MS=250
        MGS2_DMSYNTH_WATCHDOG_STALL=1
        GAME_EXE_PATCH=wpatch-finalplay23
        EXPECTED_BIND_MOUNTS=8
        export MGS2_DMSYNTH_WATCHDOG_MS MGS2_DMSYNTH_WATCHDOG_STALL
        ;;
    finalplay22)
        MGS2_BOX86_BIN=box86-fp26-wayland-text-input-production
        PLAY_IDENTITY_MANIFEST=FINALPLAY22_AUDIT_FIXES.manifest
        EXPECTED_IDENTITY_ROWS=21
        INPUT_ROUTE=immediate-production
        MGS2_DMSYNTH_DLL=dmsynth_p38_sink_lifetime.dll
        MGS2_DMIME_DLL=dmime_p16_curve_state_layout.dll
        MGS2_DMSYNTH_WATCHDOG_MS=250
        MGS2_DMSYNTH_WATCHDOG_STALL=1
        GAME_EXE_PATCH=wpatch-finalplay22
        EXPECTED_BIND_MOUNTS=8
        export MGS2_DMSYNTH_WATCHDOG_MS MGS2_DMSYNTH_WATCHDOG_STALL
        ;;
    finalplay21)
        MGS2_BOX86_BIN=box86-fp26-wayland-text-input-production
        PLAY_IDENTITY_MANIFEST=FINALPLAY21_WATER_WPATCH.manifest
        EXPECTED_IDENTITY_ROWS=21
        INPUT_ROUTE=immediate-production
        MGS2_DMSYNTH_DLL=dmsynth_p37_resume_timeline.dll
        MGS2_DMSYNTH_WATCHDOG_MS=250
        MGS2_DMSYNTH_WATCHDOG_STALL=1
        GAME_EXE_PATCH=wpatch-fixed-function
        EXPECTED_BIND_MOUNTS=8
        export MGS2_DMSYNTH_WATCHDOG_MS MGS2_DMSYNTH_WATCHDOG_STALL
        ;;
    wpatch-isolation-candidate)
        MGS2_BOX86_BIN=box86-fp26-wayland-text-input-production
        PLAY_IDENTITY_MANIFEST=WPATCH_ISOLATION_CANDIDATE.manifest
        EXPECTED_IDENTITY_ROWS=21
        INPUT_ROUTE=immediate-production
        MGS2_DMSYNTH_DLL=dmsynth_p37_resume_timeline.dll
        MGS2_DMSYNTH_WATCHDOG_MS=250
        MGS2_DMSYNTH_WATCHDOG_STALL=1
        GAME_EXE_PATCH=wpatch-isolated
        EXPECTED_BIND_MOUNTS=8
        export MGS2_DMSYNTH_WATCHDOG_MS MGS2_DMSYNTH_WATCHDOG_STALL
        ;;
    wpatch-state-ownership-candidate)
        MGS2_BOX86_BIN=box86-fp26-wayland-text-input-production
        PLAY_IDENTITY_MANIFEST=WPATCH_STATE_OWNERSHIP_CANDIDATE.manifest
        EXPECTED_IDENTITY_ROWS=21
        INPUT_ROUTE=immediate-production
        MGS2_DMSYNTH_DLL=dmsynth_p37_resume_timeline.dll
        MGS2_DMSYNTH_WATCHDOG_MS=250
        MGS2_DMSYNTH_WATCHDOG_STALL=1
        GAME_EXE_PATCH=wpatch-state-owned
        EXPECTED_BIND_MOUNTS=8
        export MGS2_DMSYNTH_WATCHDOG_MS MGS2_DMSYNTH_WATCHDOG_STALL
        ;;
    audio-lifetime-candidate)
        MGS2_BOX86_BIN=box86-fp26-wayland-text-input-production
        PLAY_IDENTITY_MANIFEST=AUDIO_LIFETIME_CANDIDATE.manifest
        EXPECTED_IDENTITY_ROWS=21
        INPUT_ROUTE=immediate-production
        MGS2_DMSYNTH_DLL=dmsynth_p38_sink_lifetime.dll
        MGS2_DMIME_DLL=dmime_p16_curve_state_layout.dll
        MGS2_DMSYNTH_WATCHDOG_MS=250
        MGS2_DMSYNTH_WATCHDOG_STALL=1
        GAME_EXE_PATCH=wpatch-fixed-function
        EXPECTED_BIND_MOUNTS=8
        export MGS2_DMSYNTH_WATCHDOG_MS MGS2_DMSYNTH_WATCHDOG_STALL
        ;;
    dxt-witness-candidate)
        MGS2_BOX86_BIN=box86-p27-dxt-witness-candidate
        PLAY_IDENTITY_MANIFEST=DXT_SURFACE_WITNESS_CANDIDATE.manifest
        EXPECTED_IDENTITY_ROWS=21
        INPUT_ROUTE=immediate-production
        MGS2_DMSYNTH_DLL=dmsynth_p37_resume_timeline.dll
        MGS2_DMSYNTH_WATCHDOG_MS=250
        MGS2_DMSYNTH_WATCHDOG_STALL=1
        GAME_EXE_PATCH=wpatch-fixed-function
        EXPECTED_BIND_MOUNTS=8
        export MGS2_DMSYNTH_WATCHDOG_MS MGS2_DMSYNTH_WATCHDOG_STALL
        ;;
    dmsynth-resume-p35-candidate)
        MGS2_BOX86_BIN=box86-fp26-wayland-text-input-production
        PLAY_IDENTITY_MANIFEST=DMSYNTH_RESUME_P35_CANDIDATE.manifest
        EXPECTED_IDENTITY_ROWS=19
        INPUT_ROUTE=immediate-production
        MGS2_DMSYNTH_DLL=dmsynth_p35_resume_recover.dll
        ;;
    dmsynth-resume-stall1-candidate)
        MGS2_BOX86_BIN=box86-fp26-wayland-text-input-production
        PLAY_IDENTITY_MANIFEST=DMSYNTH_RESUME_STALL1_CANDIDATE.manifest
        EXPECTED_IDENTITY_ROWS=19
        INPUT_ROUTE=immediate-production
        MGS2_DMSYNTH_DLL=dmsynth_p35_resume_recover.dll
        MGS2_DMSYNTH_WATCHDOG_STALL=1
        export MGS2_DMSYNTH_WATCHDOG_STALL
        ;;
    dmsynth-resume-p37-candidate)
        MGS2_BOX86_BIN=box86-fp26-wayland-text-input-production
        PLAY_IDENTITY_MANIFEST=DMSYNTH_RESUME_P37_CANDIDATE.manifest
        EXPECTED_IDENTITY_ROWS=19
        INPUT_ROUTE=immediate-production
        MGS2_DMSYNTH_DLL=dmsynth_p37_resume_timeline.dll
        MGS2_DMSYNTH_WATCHDOG_STALL=1
        export MGS2_DMSYNTH_WATCHDOG_STALL
        ;;
    wayland-p26-candidate)
        MGS2_BOX86_BIN=box86-fp26-wayland-text-input-candidate
        PLAY_IDENTITY_MANIFEST=BOX86_WAYLAND_TEXT_INPUT_CANDIDATE.manifest
        EXPECTED_IDENTITY_ROWS=19
        INPUT_ROUTE=immediate-candidate
        ;;
    *)
        echo "MGS2: unknown fixed production route $PRODUCTION_ROUTE" >&2
        exit 1
        ;;
esac
MGS2_DXVK_D3D8_DLL=d3d8_dxvk_sarek_1.11.1_mali_wsiinit3.dll
MGS2_DXVK_D3D9_DLL=d3d9_dxvk_sarek_1.11.1_mali_freeze1.dll
MGS2_DXVK_WINE_MODE=direct32
MGS2_BOX86_EMULATED_LIBS='winewayland.so:winevulkan.so:libffi.so.8:libwayland-egl.so.1:libxkbcommon.so.0:libxkbregistry.so.0:libxml2.so.2:libicuuc.so.72:libicudata.so.72:liblzma.so.5:libstdc++.so.6'
MGS2_WINEDLLOVERRIDES='mscoree=;mshtml=;winemenubuilder.exe=;winepulse.drv=d;d3d8=n,b;d3d9=n,b;dxgi=builtin'

# Closed gate for the one-process immediate Start/Select input route. Candidate
# and production names select complete exact bundles. Environment selection is
# rejected so an accidental hybrid cannot bypass either manifest.
case "$INPUT_ROUTE" in
    legacy)
        ;;
    immediate-candidate|immediate-production)
        MGS2_GPTOKEYB_BIN="$GAMEDIR/gptokeyb-mgs2-immediate"
        MGS2_GPTOKEYB_SHA256=49c782dad9da50cb0f5bb9e37821104e5089563feb24c7b0303117b75196b43a
        MGS2_WINEDLLOVERRIDES="$MGS2_WINEDLLOVERRIDES;winebus.sys=d"
        ;;
    *)
        echo "MGS2: unknown fixed input route $INPUT_ROUTE" >&2
        exit 1
        ;;
esac
export MGS2_BOX86_BIN MGS2_DXVK_D3D8_DLL MGS2_DXVK_D3D9_DLL
export MGS2_DXVK_WINE_MODE MGS2_BOX86_EMULATED_LIBS MGS2_WINEDLLOVERRIDES

# Value 1 selects the verified fused DXT5 surface-row implementation. Box86
# patch 21 routes it through the production entry, which has no atomic research
# counters on the texture worker. Unsupported layouts keep the guest fallback.
export MGS2_BOX86_NATIVE_DXT=0
export MGS2_BOX86_NATIVE_DXT_SURFACE=1

exec 9>/tmp/mgs2-substance.lock
if ! flock -n 9; then
    echo "MGS2: another launch owns /tmp/mgs2-substance.lock; refusing a second instance" >&2
    exit 1
fi

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

# The stable warm cache moved pipeline creation off the main-visible critical
# path. One compiler worker beat Sarek's two-worker default on this four-core
# device; DXVK_ALL_CORES has later precedence in this Sarek tree, so clear it.
export DXVK_STATE_CACHE=1
export DXVK_STATE_CACHE_PATH="$GAMEDIR/cache/dxvk-state"
unset DXVK_ALL_CORES
export DXVK_CONFIG='dxvk.numCompilerThreads = 1'
export DXVK_LOG_LEVEL=warn
export DXVK_LOG_PATH="$GAMEDIR/logs/dxvk-sarek"
export DXVK_HUD=
mkdir -p "$DXVK_LOG_PATH" "$DXVK_STATE_CACHE_PATH"

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
export MGS2_BOX86_NATIVE_AABB=0
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
CPU_STATE_FILE=/tmp/mgs2-cpu-baseline.state
CPU_STATE_READY=0

valid_governor() {
    case "$1" in
        ''|*[!A-Za-z0-9_-]*) return 1 ;;
        *) return 0 ;;
    esac
}

known_cpu_policy() {
    local candidate="$1" p
    for p in $CPU_POLICIES; do
        [ "$candidate" = "$p" ] && return 0
    done
    return 1
}

load_cpu_state() {
    local kind a b c extra boot_id expected_boot policies seen_gpu seen_policies
    [ -f "$CPU_STATE_FILE" ] && [ ! -L "$CPU_STATE_FILE" ] || return 1
    expected_boot=$(cat /proc/sys/kernel/random/boot_id 2>/dev/null) || return 1
    boot_id=""
    policies=0
    seen_gpu=0
    seen_policies=""
    SAVED_GOV=""
    SAVED_MAX=""
    SAVED_GPU_GOV=""
    while read -r kind a b c extra; do
        [ -z "$extra" ] || return 1
        case "$kind" in
            boot)
                [ -z "$b$c" ] && [ -z "$boot_id" ] || return 1
                boot_id=$a
                ;;
            cpu)
                [ -n "$a" ] && known_cpu_policy "$a" || return 1
                case " $seen_policies " in *" $a "*) return 1 ;; esac
                valid_governor "$b" || return 1
                case "$c" in ''|*[!0-9]*) return 1 ;; esac
                SAVED_GOV="$SAVED_GOV $a:$b"
                SAVED_MAX="$SAVED_MAX $a:$c"
                seen_policies="$seen_policies $a"
                policies=$((policies + 1))
                ;;
            gpu)
                [ "$a" = "$GPU_DEVFREQ" ] && valid_governor "$b" && \
                    [ -z "$c" ] && [ "$seen_gpu" = 0 ] || return 1
                SAVED_GPU_GOV=$b
                seen_gpu=1
                ;;
            *) return 1 ;;
        esac
    done < "$CPU_STATE_FILE"
    set -- $CPU_POLICIES
    [ "$boot_id" = "$expected_boot" ] && [ "$policies" = "$#" ] && \
        [ "$seen_gpu" = 1 ] || return 1
    CPU_STATE_READY=1
}

save_cpu_state() {
    local p gov max gpu boot_id tmp
    if [ -e "$CPU_STATE_FILE" ] || [ -L "$CPU_STATE_FILE" ]; then
        if load_cpu_state; then
            echo "MGS2: recovered pre-launch clock baseline after an interrupted run" >&2
            return 0
        fi
        boot_id=$(cat /proc/sys/kernel/random/boot_id 2>/dev/null) || return 1
        if grep -Fqx "boot $boot_id" "$CPU_STATE_FILE" 2>/dev/null; then
            echo "MGS2: refusing corrupt same-boot clock baseline $CPU_STATE_FILE" >&2
            return 1
        fi
        rm -f "$CPU_STATE_FILE" || return 1
    fi
    [ -n "$CPU_POLICIES" ] || {
        echo "MGS2: no CPU frequency policies found; controlled-clock launch refused" >&2
        return 1
    }
    boot_id=$(cat /proc/sys/kernel/random/boot_id 2>/dev/null) || return 1
    tmp=$(mktemp /tmp/mgs2-cpu-baseline.XXXXXX) || return 1
    chmod 0600 "$tmp" || { rm -f "$tmp"; return 1; }
    printf 'boot %s\n' "$boot_id" > "$tmp" || { rm -f "$tmp"; return 1; }
    for p in $CPU_POLICIES; do
        gov=$(cat "$p/scaling_governor" 2>/dev/null) || { rm -f "$tmp"; return 1; }
        max=$(cat "$p/scaling_max_freq" 2>/dev/null) || { rm -f "$tmp"; return 1; }
        valid_governor "$gov" || { rm -f "$tmp"; return 1; }
        case "$max" in ''|*[!0-9]*) rm -f "$tmp"; return 1 ;; esac
        printf 'cpu %s %s %s\n' "$p" "$gov" "$max" >> "$tmp" || {
            rm -f "$tmp"
            return 1
        }
        SAVED_GOV="$SAVED_GOV $p:$gov"
        SAVED_MAX="$SAVED_MAX $p:$max"
    done
    gpu=$(cat "$GPU_DEVFREQ/governor" 2>/dev/null) || { rm -f "$tmp"; return 1; }
    valid_governor "$gpu" || { rm -f "$tmp"; return 1; }
    printf 'gpu %s %s\n' "$GPU_DEVFREQ" "$gpu" >> "$tmp" || {
        rm -f "$tmp"
        return 1
    }
    mv "$tmp" "$CPU_STATE_FILE" || { rm -f "$tmp"; return 1; }
    load_cpu_state || {
        echo "MGS2: persisted clock baseline failed validation" >&2
        rm -f "$CPU_STATE_FILE"
        return 1
    }
}

write_sysfs_exact() {
    local path="$1" value="$2" got
    if ! printf '%s\n' "$value" > "$path" 2>/dev/null; then
        echo "MGS2: cannot write $value to $path; controlled-clock launch refused" >&2
        return 1
    fi
    got=$(cat "$path" 2>/dev/null) || got=""
    if [ "$got" != "$value" ]; then
        echo "MGS2: $path read back ${got:-missing}, expected $value; controlled-clock launch refused" >&2
        return 1
    fi
}

set_final_cpu_cap() {
    local p failed
    failed=0
    for p in $CPU_POLICIES; do
        write_sysfs_exact "$p/scaling_governor" performance || failed=1
        write_sysfs_exact "$p/scaling_max_freq" 1992000 || failed=1
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
    write_sysfs_exact "$GPU_DEVFREQ/governor" "${MGS2_GPU_GOVERNOR:-performance}" || failed=1
    [ "$failed" = 0 ]
}

restore_cpu_state() {
    local e p v failed
    [ "$CPU_STATE_READY" = 1 ] || return 0
    failed=0
    [ -z "$SAVED_GPU_GOV" ] || \
        write_sysfs_exact "$GPU_DEVFREQ/governor" "$SAVED_GPU_GOV" || failed=1
    for e in $SAVED_MAX; do
        p="${e%%:*}"; v="${e##*:}"
        [ -z "$v" ] || write_sysfs_exact "$p/scaling_max_freq" "$v" || failed=1
    done
    for e in $SAVED_GOV; do
        p="${e%%:*}"; v="${e##*:}"
        [ -z "$v" ] || write_sysfs_exact "$p/scaling_governor" "$v" || failed=1
    done
    if [ "$failed" = 0 ]; then
        rm -f "$CPU_STATE_FILE" || return 1
        CPU_STATE_READY=0
        return 0
    fi
    echo "MGS2: clock restore incomplete; preserving $CPU_STATE_FILE for recovery" >&2
    return 1
}

# Arm cleanup before the first bind mount.  A missing or unreadable selected
# runtime must not leave the earlier mounts active for the next launch.
cleanup() {
    local cleanup_failed game_image_unmounted
    [ "${CLEANUP_ACTIVE:-0}" = 0 ] || return 0
    CLEANUP_ACTIVE=1
    trap - HUP INT TERM
    cleanup_failed=0
    [ -n "${WINE_PID:-}" ] && kill "$WINE_PID" 2>/dev/null || true
    [ -n "${EXPLORER_PID:-}" ] && kill "$EXPLORER_PID" 2>/dev/null || true
    [ -n "${GPTOKEYB_PID:-}" ] && kill "$GPTOKEYB_PID" 2>/dev/null || true
    killall -9 wineserver wineboot.exe services.exe start.exe explorer.exe winedevice.exe plugplay.exe svchost.exe rpcss.exe 2>/dev/null || true
    pkill -9 -f '[m]gs2_sse_rg353vs_port.exe' 2>/dev/null || true
    # A Wine child can remain visible briefly after SIGKILL and keep a bind
    # mount busy. Wait only in teardown, before attempting to restore targets.
    i=0
    while pgrep -f '[w]ineboot.exe|[s]tart.exe|[e]xplorer.exe|[m]gs2_sse_rg353vs_port.exe' >/dev/null 2>&1 \
          && [ "$i" -lt 20 ]; do
        sleep 0.1
        i=$((i + 1))
    done
    restore_cpu_state || cleanup_failed=1
    unmount_all /usr/lib/wine/i386-windows/wined3d.dll || cleanup_failed=1
    unmount_all /usr/lib/wine/i386-windows/d3d8.dll || cleanup_failed=1
    [ -z "${DXVK_D3D8_TARGET:-}" ] || unmount_all "$DXVK_D3D8_TARGET" || cleanup_failed=1
    [ -z "${DXVK_D3D9_TARGET:-}" ] || unmount_all "$DXVK_D3D9_TARGET" || cleanup_failed=1
    unmount_all /usr/lib/wine/i386-unix/winewayland.so || cleanup_failed=1
    unmount_all /usr/lib/wine/i386-unix/win32u.so || cleanup_failed=1
    unmount_all /usr/lib/wine/i386-unix/opengl32.so || cleanup_failed=1
    unmount_all /usr/lib/wine/i386-windows/user32.dll || cleanup_failed=1
    unmount_all /usr/lib/wine/i386-windows/dmsynth.dll || cleanup_failed=1
    unmount_all /usr/lib/wine/i386-windows/dsound.dll || cleanup_failed=1
    unmount_all /usr/lib/wine/i386-windows/dmime.dll || cleanup_failed=1
    unmount_all /usr/lib/wine/i386-windows/dmusic.dll || cleanup_failed=1
    unmount_all /usr/lib/wine/i386-unix/ntdll.so || cleanup_failed=1
    unmount_all /usr/bin/box86 || cleanup_failed=1
    game_image_unmounted=1
    unmount_all "$GAME_EXE_TARGET" || {
        cleanup_failed=1
        game_image_unmounted=0
    }
    if [ -n "$PATCHED_GAME_EXE" ]; then
        if [ "$game_image_unmounted" = 1 ]; then
            rm -f "$PATCHED_GAME_EXE" || cleanup_failed=1
        else
            echo "MGS2: preserving busy mounted temporary game image $PATCHED_GAME_EXE" >&2
        fi
    fi
    [ -n "${ESUDO:-}" ] && $ESUDO systemctl restart oga_events >/dev/null 2>&1 || true
    [ "$cleanup_failed" = 0 ] || \
        echo "MGS2: cleanup finished with one or more reported failures" >&2
}

cleanup_signal() {
    local status="$1"
    trap - EXIT HUP INT TERM
    cleanup
    exit "$status"
}

trap cleanup EXIT
trap 'cleanup_signal 129' HUP
trap 'cleanup_signal 130' INT
trap 'cleanup_signal 143' TERM

# A power loss can leave the temporary game-image bind in place. Always expose
# the legally installed original first; old routes stop here, while FINALPLAY21
# and FINALPLAY22 build and verify a temporary view. The installed EXE is never
# overwritten.
prepare_game_exe() {
    unmount_all "$GAME_EXE_TARGET" || return 1
    [ "$GAME_EXE_PATCH" = none ] && return 0
    case "$GAME_EXE_PATCH" in
        wpatch-finalplay23)
            patcher="$GAMEDIR/patch-mgs2-wpatch-finalplay23.sh"
            patcher_hash=c607805bd2afc391d267364fe8d63891bcf89f03ca18736eb561e276445889a8
            patched_hash=d6b81257a82348299675adf863c9ad884c68c438b032fe20a75f18a094d29cd5
            tmp_template=/tmp/mgs2-wpatch-finalplay23.XXXXXX
            route_name=FINALPLAY23
            ;;
        wpatch-finalplay22)
            patcher="$GAMEDIR/patch-mgs2-wpatch-finalplay22.sh"
            patcher_hash=55f1714b68a0360829469439143923bc74356502be9164628e1a2dd9633464fa
            patched_hash=d902ee4398b77653674943f097f79e103d1aa0bc93ce825c0cb0c3d3522b9f88
            tmp_template=/tmp/mgs2-wpatch-finalplay22.XXXXXX
            route_name=FINALPLAY22
            ;;
        wpatch-fixed-function)
            patcher="$GAMEDIR/patch-mgs2-wpatch-novs.sh"
            patcher_hash=ace82a30c96c2c52dddf920a2d45f878f916ee31900838eef5fb491f8f607325
            patched_hash=6686b3fa6484a0609fbe65be46f34cbba941b18e252db7bbb83d457153ba31d6
            tmp_template=/tmp/mgs2-wpatch-novs.XXXXXX
            route_name=FINALPLAY21
            ;;
        wpatch-isolated)
            patcher="$GAMEDIR/patch-mgs2-wpatch-isolated.sh"
            patcher_hash=5dcc4e1fd76df35e23539bec67a42fda680e1775422a52c6cc882c347026cbe0
            patched_hash=e4a54598cefa2f7d19e02aa519e030b21a19424f163e3fdeebe32bb111cde1ce
            tmp_template=/tmp/mgs2-wpatch-isolated.XXXXXX
            route_name=wpatch-isolation-candidate
            ;;
        wpatch-state-owned)
            patcher="$GAMEDIR/patch-mgs2-wpatch-state-owned.sh"
            patcher_hash=0c75034daa9eaace2fcb45d7909a9c57f827d0e2ac2d67ca2602955c11d61e15
            patched_hash=d902ee4398b77653674943f097f79e103d1aa0bc93ce825c0cb0c3d3522b9f88
            tmp_template=/tmp/mgs2-wpatch-state.XXXXXX
            route_name=wpatch-state-ownership-candidate
            ;;
        *)
            echo "MGS2: unknown fixed game EXE patch $GAME_EXE_PATCH" >&2
            return 1
            ;;
    esac
    got=$(sha256sum "$patcher" 2>/dev/null | cut -d' ' -f1)
    if [ "$got" != "$patcher_hash" ]; then
        echo "MGS2: game patch helper is ${got:-missing}, refusing $route_name" >&2
        return 1
    fi
    PATCHED_GAME_EXE=$(mktemp "$tmp_template") || return 1
    "$patcher" "$GAME_EXE_TARGET" "$PATCHED_GAME_EXE" || return 1
    mount_bind "$PATCHED_GAME_EXE" "$GAME_EXE_TARGET" || return 1
    got=$(sha256sum "$GAME_EXE_TARGET" 2>/dev/null | cut -d' ' -f1)
    if [ "$got" != "$patched_hash" ]; then
        echo "MGS2: mounted game EXE is ${got:-missing}, refusing $route_name" >&2
        return 1
    fi
}
prepare_game_exe || exit 1

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
# The FINALPLAY engine is a closed production/candidate bundle. Historical
# island A/B wrappers route through the separate WineD3D research launcher;
# an inherited measurement arm is rejected before this point.
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

# FINALPLAY17 native renderer pair. MGS2 ships an app-local d3d8.dll, which
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
# It used to name three: box86, wined3d and the presenter -- the files the old
# release path happened to build. The launcher also replaces win32u.so,
# opengl32.so, user32.dll, d3d8.dll and four DirectMusic/DirectSound modules, so
# eight of the eleven substitutions were never verified, and four of them were
# mounted after the check even ran. Each closed route now pins an exact row
# count in addition to checking every listed live path and the bind-mount floor.
#
# There is no off switch. Binary-selection overrides are rejected at the top and
# every manifest mismatch remains fatal.
mgs2_verify_identity() {
    manifest="$GAMEDIR/$PLAY_IDENTITY_MANIFEST"
    if [ ! -r "$manifest" ]; then
        echo "MGS2: no $manifest, cannot verify identity" >&2
        return 1
    fi
    # Seven bind-mounted production files in FINALPLAY17--20: Box86, D3D8,
    # D3D9 and four audio modules. FINALPLAY21, FINALPLAY22 and the wpatch
    # candidates add the temporary verified game EXE view. Manifests also pin unmounted
    # dependencies, so the exact row count is greater than the mount count.
    mounts=$EXPECTED_BIND_MOUNTS
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
    if [ -z "$EXPECTED_IDENTITY_ROWS" ] || [ "$checked" -ne "$EXPECTED_IDENTITY_ROWS" ]; then
        echo "MGS2: refusing to launch -- $PLAY_IDENTITY_MANIFEST has $checked rows," \
             "the closed route requires exactly ${EXPECTED_IDENTITY_ROWS:-an unset count}" >&2
        return 1
    fi
    if [ "$checked" -lt "$mounts" ]; then
        echo "MGS2: refusing to launch -- the exact manifest has fewer rows than" \
             "the $mounts bind mounts" >&2
        return 1
    fi
    if [ "$bad" != 0 ]; then
        echo "MGS2: refusing to launch -- $bad of $checked runtime files do not" \
             "match the manifest" >&2
        return 1
    fi
    echo "MGS2: identity verified, $checked of $checked runtime files match" \
        "$PLAY_IDENTITY_MANIFEST" >&2
}

mgs2_verify_identity || exit 1

save_cpu_state || exit 1
set_final_cpu_cap || exit 1

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

start_gptokeyb() {
    if [ "$INPUT_ROUTE" != legacy ]; then
        if [ ! -r "$GAMEDIR/mgs2.gptk" ]; then
            echo "MGS2: immediate input route requires $GAMEDIR/mgs2.gptk" >&2
            return 1
        fi
        got=$(sha256sum "$MGS2_GPTOKEYB_BIN" 2>/dev/null | cut -d" " -f1)
        if [ "$got" != "$MGS2_GPTOKEYB_SHA256" ]; then
            echo "MGS2: input helper is ${got:-missing}, expected $MGS2_GPTOKEYB_SHA256" >&2
            return 1
        fi
        "$MGS2_GPTOKEYB_BIN" -immediate-start-back -1 "$EXE" \
            -c "$GAMEDIR/mgs2.gptk" 9>&- >/tmp/mgs2-gptokeyb.log 2>&1 &
        GPTOKEYB_PID=$!
        sleep 0.1
        if ! kill -0 "$GPTOKEYB_PID" 2>/dev/null; then
            wait "$GPTOKEYB_PID" 2>/dev/null || true
            GPTOKEYB_PID=
            echo "MGS2: immediate input helper failed during startup" >&2
            return 1
        fi
        return 0
    fi
    [ -r "$GAMEDIR/mgs2.gptk" ] || return 0
    if [ -n "${GPTOKEYB:-}" ]; then
        # PortMaster supplies a command prefix including the device/OS-specific
        # kill-mode option (on ROCKNIX: .../gptokeyb -1). Word splitting here
        # is intentional and is the documented PortMaster calling convention.
        # shellcheck disable=SC2086
        $GPTOKEYB "$EXE" -c "$GAMEDIR/mgs2.gptk" 9>&- >/tmp/mgs2-gptokeyb.log 2>&1 &
    elif [ -x /usr/bin/gptokeyb ]; then
        # The positional application name alone does not arm kill mode in the
        # current gptokeyb parser. Keep an explicit fallback for bare systems.
        /usr/bin/gptokeyb -1 "$EXE" -c "$GAMEDIR/mgs2.gptk" 9>&- >/tmp/mgs2-gptokeyb.log 2>&1 &
    else
        echo "MGS2: gptokeyb unavailable; Start+Select exit is disabled" >&2
        return 0
    fi
    GPTOKEYB_PID=$!
}
start_gptokeyb || exit 1

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
# Do not let EXIT cleanup signal a reaped PID which the kernel may already have
# reused.  Preserve the original PID in the bounded exit record instead.
WINE_PID=
printf '%s launcher=%s pid=%s status=%s\n' \
    "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$PRODUCTION_ROUTE" \
    "$PLAY_WINE_PID" "$PLAY_EXIT_STATUS" > "$PLAY_EXIT_LOG"
exit "$PLAY_EXIT_STATUS"

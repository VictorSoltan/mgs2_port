#!/bin/bash
# PORTMASTER: MGS2-Substance.zip, MGS2-Substance.sh
# PortMaster's device_info.txt contains optional unset variables; do not use
# nounset here, otherwise the wrapper exits before starting the game.

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
# mgs2_sse_rg353vs_port.exe has byte 0x14210 stubbed to 0xC3, which turns the
# "[[REQ]] Movie Start" request into a bare `ret`. The request never runs and,
# more importantly, the movie state machine never advances past state 3 -- so
# anything waiting for a movie to start-and-finish waits forever. That is the
# second-location hang that surfaces as "There's a problem with the disc you're
# using": the actor system stalls on a demo-stream read that never completes.
#
# _moviestart.exe restores that one byte to 0x68 (`push`) and leaves the PSS
# resource path patched out, which is the *designed* graceful failure: the
# request runs, PSS reports no resources, the actor is destroyed, end_proc
# fires, and the state machine moves on. Verified to boot and play at 21.9-23.8
# fps in gameplay and 60 fps in menus; whether it clears the disc message needs
# a run into the second location.
#
# REVERTED 2026-08-02: with _moviestart.exe the user reports cutscenes raising the
# disc error, which they did not with _port.exe. Restoring the movie-start request
# while PSS stays patched out evidently leaves the movie path issuing reads it
# cannot satisfy -- FS_DISC_ERROR is CDBIOS_STATE_COMMAND_ERROR, i.e. a failed
# read, not a missing file: movie.dat is present and reads fine end to end.
# Try MGS2_EXE=mgs2_sse_rg353vs_moviestart.exe to reproduce, or _moviefull.exe
# which also restores the PSS resource path.
EXE="${MGS2_EXE:-mgs2_sse_rg353vs_port.exe}"

# Keep the lock descriptor open in Wine and the game as well. This prevents a
# second EmulationStation launch from piling another CPU-heavy instance on top
# of an orphaned or still-running one.
exec 9>/tmp/mgs2-substance.lock
if ! flock -n 9; then
    exit 0
fi

export WINEPREFIX="$GAMEDIR/wineprefix64"

# MGS2 asks the drive it runs from how many free blocks it has, and refuses to
# save when the answer is zero. The game lives under /storage, but the only drive
# covering that path was Z: -> /, a read-only squashfs that is 100% full, so the
# game was told zero and showed "There are insufficient free blocks on the hard
# disc" right after START. The free space on /storage was never asked about.
# Mapping D: -> /storage gives the path a drive whose free space is real.
# Idempotent, so it survives a prefix rebuild.
if [ -d "$WINEPREFIX/dosdevices" ]; then
    ln -sfn /storage "$WINEPREFIX/dosdevices/d:" 2>/dev/null
fi
# MGS2_TRACE=1 turns on the file channel so a failed open or read is named.
# Off by default. It was defaulted on while the cutscene fault was being
# captured, and that cost real frame rate: every Wine debug channel below is
# formatted and written to the SD card for the whole session. Turn it on
# explicitly when diagnosing.
if [ "${MGS2_TRACE:-0}" = 1 ]; then
    # The file channel did its job -- it proved no file open or read fails, so
    # the disc error is not a missing or unreadable asset. Now aimed at the audio
    # stack: the game connects to PipeWire but never creates a playback stream
    # (pactl reports no sink-inputs), so the failure is in DirectSound/winmm
    # initialisation rather than in the device.
    export WINEDEBUG="${WINEDEBUG:--all,err+dsound,warn+dsound,err+winmm,warn+winmm,err+mmdevapi,warn+mmdevapi,err+alsa,warn+alsa,err+dmsynth,warn+dmsynth,err+waylanddrv}"
else
    export WINEDEBUG="${WINEDEBUG:--all}"
fi
# Audio backend. winepulse.drv was disabled here, which left Wine with no usable
# output at all: PipeWire holds the ALSA device (rk817_int reports 0/1 free
# subdevices), so winealsa cannot open it either, and the game runs silent. But
# pipewire-pulse *is* running and its socket is present, so winepulse is exactly
# the driver that should work.
#
# This matters beyond sound: the cutscene stall that surfaces as "There's a
# problem with the disc you're using" happens where the demo stream carries
# voice, and a stream waiting on an audio device that never opens would stall
# the same way.
#
#   MGS2_AUDIO=pulse   let winepulse load (default)
#   MGS2_AUDIO=alsa    disable winepulse, force winealsa
#   MGS2_AUDIO=none    disable both, silent
# Default is alsa, not pulse: winepulse.so cannot even load under box86 --
#   Symbol pthread_mutexattr_setrobust not found, cannot apply R_386_JMP_SLOT
#   in /usr/lib/wine/i386-unix/winepulse.so
# box86's wrapped 32-bit libc does not export that symbol, so the relocation
# fails and the driver never initialises. That is why it was disabled here in
# the first place. winealsa does load; whether it produces sound depends on
# ALSA routing through the PipeWire plugin rather than raw hardware, since
# PipeWire holds the card (plughw:1,0 -> -16 Device or resource busy).
# RockNIX's pipewire-pulse listens on both /run/pulse/native and
# tcp:127.0.0.1:4713, but clients follow XDG_RUNTIME_DIR to
# /var/run/0-runtime-dir/pulse/native, where a stale socket makes them hang --
# which is why pactl blocks and EmulationStation is silent. Going straight to
# the TCP endpoint sidesteps the path mismatch without touching a read-only
# rootfs. Verified: PULSE_SERVER=tcp:127.0.0.1:4713 pactl info answers at once.
export PULSE_SERVER="${PULSE_SERVER:-tcp:127.0.0.1:4713}"

# Audio rate and period, promoted 2026-08-03.
#
# dmsynth renders 22050 Hz; winealsa was picking 48000 because the endpoint
# offers it, so a non-integer 22050 -> 48000 resample ran inside emulated x86.
# Offering the client 44100 makes that ratio exactly 2:1 and leaves the
# 44100 -> 48000 step to native PipeWire. Measured, five interleaved modes:
#
#   baseline            30.78 fps   audio threads 28.0% of a core   604 ctxt/s
#   44100               30.20       13.7%                            583
#   20 ms period        31.39       27.8%                            577
#   44100 + 20 ms       31.93       13.7%                            525
#   44100 + 30 ms       33.10       13.6%                            508   <- this
#
# The rate change halves audio CPU on its own; the longer period adds a smaller
# gain by cutting wake-ups, and ioctl was the top syscall in the profile at 18%.
# Verified afterwards in pw-top: the node reports "F32LE 2 44100" on a
# 1440/48000 graph, and the output signal is unchanged (peak 3306).
#
# Longer periods mean more latency. 30 ms was fine here; go back with
# MGS2_AUDIO_QUANTUM=960/48000 (20 ms) or unset both to restore stock.
export PIPEWIRE_ALSA="${PIPEWIRE_ALSA:-{ alsa.rate=44100 node.name=mgs2-audio \}}"
export PIPEWIRE_QUANTUM="${PIPEWIRE_QUANTUM:-${MGS2_AUDIO_QUANTUM:-1440/48000}}"

# winepulse.so fails its PLT relocation under box86 because the wrapped 32-bit
# libc lacks pthread_mutexattr_setrobust, which Wine 11 calls when setting up
# its pulse mutex. This preload supplies the symbol so the pulse backend can be
# evaluated; the real fix is one line in box86's wrapper table
# (GO(pthread_mutexattr_setrobust, iFpi)) plus a rebuild.
ROBUST_SHIM="$GAMEDIR/libmgs2-robust-shim.so"
# Default off: the preload does not actually satisfy the relocation (box86
# resolves winepulse.so against its own wrapped libc), so it is dead weight.
if [ "${MGS2_ROBUST_SHIM:-0}" = 1 ] && [ -r "$ROBUST_SHIM" ]; then
    export BOX86_LD_PRELOAD="${BOX86_LD_PRELOAD:+$BOX86_LD_PRELOAD:}$ROBUST_SHIM"
fi

case "${MGS2_AUDIO:-alsa}" in
    alsa) AUDIO_OVERRIDE="winepulse.drv=d;" ;;
    none) AUDIO_OVERRIDE="winepulse.drv=d;winealsa.drv=d;" ;;
    *)    AUDIO_OVERRIDE="" ;;
esac
# Which d3d8 the game gets.
#
# The port ships its own game/bin/d3d8.dll (124 KB, imports Direct3DCreate9) --
# a d3d8-to-d3d9 wrapper. With d3d8=native the chain was
#   MGS2 -> wrapper -> d3d9 -> wined3d -> GLES -> Mali
# and Wine's own d3d8 sits directly on wined3d, one COM translation layer fewer.
# Every layer is x86 code under box86, and the per-draw cost is what wined3d_cs
# spends its half core on. Measured in one session, same gameplay area:
#   d3d8=native    24.5-26.2 fps, readback 7.0-7.7 ms/f
#   d3d8=builtin   31.6-31.8 fps, readback 4.1 ms/f
#
# Caveat worth knowing: game/bin/dxcfg.ini configures that wrapper, so with
# builtin it no longer applies (scaling, gamma, forced AA/aniso). At 640x480 on a
# 640x480 panel none of it was doing anything, but that is why it is a knob:
#   MGS2_D3D8=native   restores the wrapper if anything renders wrong.
D3D8_MODE="${MGS2_D3D8:-builtin}"
export WINEDLLOVERRIDES="mscoree=;mshtml=;winemenubuilder.exe=;${AUDIO_OVERRIDE}d3d8=${D3D8_MODE};d3d9=builtin;dxgi=builtin"
# MGS2_TRIAGE=1 turns on every aggregate counter at once: frame-time distribution
# and the compositor wait from the presenter, shader compile/link time from
# wined3d, and draw/state/managed-texture counts from d3d8. All are one line per
# second or per 300 frames -- never per call, which on this device has already
# cost more than it measured. Timestamps line the three streams up.
# Linking one GLSL program costs about 195 ms on this Mali blob, and it happens
# inside the frame that first needs that state combination -- measured against a
# 236 ms frame in the same second, which is the freeze reported on entering an
# open area or a cutscene. wined3d_glslcache1.dll keeps each linked program's
# binary here and hands it back with glProgramBinary instead of linking again, so
# the cost is paid once per state combination per driver version instead of once
# per session. A DOS path, because wined3d is PE code and D: is mapped to
# /storage further up.
#   MGS2_GLSL_CACHE=          disable
#   MGS2_GLSL_CACHE_STATS=1   log every hit, store and reject
export MGS2_GLSL_CACHE="${MGS2_GLSL_CACHE-D:\\roms\\ports\\MGS2-Substance\\cache}"

if [ "${MGS2_TRIAGE:-0}" = 1 ]; then
    export MGS2_GLSL_CACHE_STATS=1
    export MGS2_GL_STATS="${MGS2_GL_STATS:-300}"
    export MGS2_WINED3D_STATS=1
    export MGS2_D3D8_STATS=1
    export WINEDEBUG="-all,err+waylanddrv,err+d3d_shader,err+d3d8"
fi
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/var/run/0-runtime-dir}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
export BOX64_LD_LIBRARY_PATH="/usr/share/box64/lib:$GAMEDIR/x64libs"
export BOX64_EMULATED_LIBS="libwayland-client.so.0:libffi.so.8:libwayland-egl.so.1"
export BOX64_LOG=0 BOX64_NOBANNER=1
export BOX86_LD_LIBRARY_PATH="/usr/share/box86/lib:$GAMEDIR/x86libs"
export BOX86_EMULATED_LIBS="libwayland-client.so.0:libffi.so.8:libwayland-egl.so.1:libxkbcommon.so.0:libxkbregistry.so.0:libxml2.so.2:libicuuc.so.72:libicudata.so.72:liblzma.so.5:libstdc++.so.6"
export BOX86_LOG=0 BOX86_NOBANNER=1
export BOX86_DYNAREC_SAFEFLAGS=0 BOX86_DYNAREC_BIGBLOCK=2 BOX86_DYNAREC_FORWARD=512 BOX86_DYNAREC_CALLRET=1

# ---------------------------------------------------------------------------
# Presentation tuning, read by winewayland_pbo1.so.
#
# These defaults are the measured-fastest combination, not guesses.  Measured
# on the same scene in 300-frame samples:
#   MGS2_GL_PBO=0  23.4-43.6 fps, readback 4.9-6.2 ms/frame   <- default
#   MGS2_GL_PBO=1  10.7-12.5 fps, readback 0.09 ms but map+copy 23.8 ms
# The async pixel-pack path removes the readback stall exactly as intended, but
# Mali maps the pack buffer uncached and reading it back costs far more than
# was saved.  MGS2_GL_FLIP=0 because the WineD3D FBO path already delivers the
# image top-down; flipping again mirrors it.
#
# MGS2_GL_STATS=300 makes the driver log fps / readback / copy every 300
# frames.  It needs the err channel, which WINEDEBUG=-all suppresses, so use:
#   WINEDEBUG=-all,err+waylanddrv MGS2_GL_STATS=300 ./launch.sh
# ---------------------------------------------------------------------------
export MGS2_GL_PBO="${MGS2_GL_PBO:-0}"
export MGS2_GL_PBOS="${MGS2_GL_PBOS:-2}"
export MGS2_GL_FLIP="${MGS2_GL_FLIP:-0}"
export MGS2_GL_BGRA="${MGS2_GL_BGRA:-1}"
export MGS2_GL_SHM_BUFFERS="${MGS2_GL_SHM_BUFFERS:-2}"
export MGS2_GL_STATS="${MGS2_GL_STATS:-0}"

# Which Wayland presentation driver to mount.  winewayland_pbo1.so is the
# rebuilt-from-source driver (synchronous by default, instrumented, with the
# async path behind MGS2_GL_PBO); winewayland_gbmshm_directbgra1.so is the
# older binary-only build, kept as a fallback.
# winewayland_mali1.so adds two things to pbo1: depth/stencil invalidation after
# the frame (Mali is tile-based, so attachments still live at end of pass get
# written out to memory for nothing -- MGS2_GL_INVALIDATE_DS=0 disables), and
# frame-time distribution in the stats line, because a mean over 300 frames hides
# exactly the hitches this port is judged on.
WAYLAND_SO="${MGS2_WAYLAND_SO:-winewayland_mali1.so}"
[ -r "$GAMEDIR/$WAYLAND_SO" ] || WAYLAND_SO="winewayland_gbmshm_directbgra1.so"

# Which WineD3D build to mount. dbg52 is dbg42 with a six-byte binary patch:
# the ffp_gl.c viewport handler's call to the desktop-only glDepthRange (which
# lands on a NULL win32u pointer and killed the game on entering any 3D scene)
# is replaced by "add $0x10,%esp" + nops, i.e. skip the call and pop the two
# doubles the __stdcall callee would have popped. Depth range then stays at the
# GLES default [0,1], which is also the Direct3D default.
# Rebuilds from source are NOT usable -- the tree is not dbg42's source and any
# rebuild regresses before the title. Set MGS2_WINED3D_DLL to A/B.
# Which win32u to mount. win32u_depthbridge1.so is rebuilt from source with the
# recovered pre-resolve list plus a bridge from the desktop double-precision
# glDepthRange/glClearDepth onto the GLES float entry points, which is what the
# 3D scene needs. win32u_glfuncs3.so is the older binary-only build.
WIN32U_SO="${MGS2_WIN32U_SO:-win32u_glfuncs3.so}"
[ -r "$GAMEDIR/$WIN32U_SO" ] || WIN32U_SO="win32u_glfuncs3.so"

# Unix-side opengl32. Empty means "use the stock one". The rebuilt variant fixes
# parse_gl_version(), which atoi()s "OpenGL ES 3.2" to 0 and then treats the
# context as GL 1.x -- which is why wglGetProcAddress refuses every entry point
# gated on GL_VERSION_3_x even though the driver resolves them fine.
OPENGL32_SO="${MGS2_OPENGL32_SO:-opengl32_glesver1.so}"
[ -n "$OPENGL32_SO" ] && [ ! -r "$GAMEDIR/$OPENGL32_SO" ] && OPENGL32_SO=""

# The codec portrait target needs a GLES-safe FBO capability probe. The paired
# black-quad guard is deliberately narrow (codec composite only) and was
# validated through a 70-confirm gameplay run with zero page faults.
export MGS2_GLES_FBO_READBACK="${MGS2_GLES_FBO_READBACK:-1}"
export MGS2_SKIP_CODEC_BLACK_QUAD="${MGS2_SKIP_CODEC_BLACK_QUAD:-1}"

# Unix-side ntdll. Empty means "use the stock one". The rebuilt variant makes
# NtYieldExecution's cost switchable: stock is getrusage + sched_yield +
# getrusage, three syscalls, where the getrusage pair exists only to report
# STATUS_NO_YIELD_PERFORMED (one consumer tree-wide, SwitchToThread). The game's
# message loop drives roughly a thousand of these a second.
#   MGS2_YIELD=full|fast|none   MGS2_YIELD_STATS=1 logs the call rate
# Unix ntdll with a five-byte patch, promoted 2026-08-03.
#
# NtYieldExecution is three syscalls: getrusage, sched_yield, getrusage. The
# pair exists only so the function can report STATUS_NO_YIELD_PERFORMED, which
# has exactly one consumer in the whole Wine tree (SwitchToThread). Profiling
# the game's heaviest thread -- 92% of a core, eight times the message loop --
# showed getrusage as its single most frequent syscall, so that thread is a spin
# loop paying two thirds of every yield for nothing.
#
# The patch replaces the first `call getrusage@plt` at 0x481fa with
# `or $-1,%eax`: the result is non-zero, so the second call is unreachable and
# the function returns STATUS_SUCCESS. sched_yield still runs, which matters --
# an earlier experiment removing the yield entirely was worth nothing, because
# other threads then starve by as much as the spinner gains.
#
# Measured, two interleaved rounds: 36.36/36.51 -> 37.73/37.60 fps (+3.4%),
# involuntary context switches 164/165 -> 150/147 per second.
#
# This patches the *shipping* binary rather than substituting a rebuilt one, on
# purpose: two independently rebuilt win32u.so from this tree hang the game, so
# a local build is not a safe stand-in for what RockNIX ships.
#
# Set MGS2_NTDLL_SO= for stock behaviour.
NTDLL_SO="${MGS2_NTDLL_SO:-ntdll_fastyield.so}"
[ -n "$NTDLL_SO" ] && [ ! -r "$GAMEDIR/$NTDLL_SO" ] && NTDLL_SO=""

# PE user32 carrying the PeekMessage busy-loop instrumentation. Empty means the
# stock one. PE rebuilds from the tree are trustworthy here -- the shipping
# wined3d is one -- unlike the Unix .so rebuilds, which hang the game.
#   MGS2_PEEK_STATS=1        histogram callers (needs WINEDEBUG=...,err+msg)
#   MGS2_PEEK_HOT=<hex>      restrict the wait to one return address
#   MGS2_PEEK_WAIT=<N>       wait after N consecutive empty polls
#   MGS2_PEEK_WAIT_MS=<ms>   wait length, default 1
# PE user32 carrying the busy-loop fix, promoted 2026-08-02.
#
# MGS2's main loop polls PeekMessage ~56 000 times a second -- one empty poll
# per game iteration, about 3 500 iterations per rendered frame -- and Wine
# yields on every empty poll, at three syscalls a time. Waiting for a message
# instead, after each empty poll from the one hot caller, cuts polling ~60x and
# measured +11% mean fps with the frame-time jitter roughly halved (12.9% ->
# 4.9-7.8% standard deviation, worst-window 5.6 -> 6.4-7.0 fps) across three
# interleaved pairs at a pinned clock. Brief #6 has the numbers.
#
# MGS2_PEEK_HOT is an address in *this* executable (the call site at 0x401176
# in mgs2_sse_rg353vs_port.exe). It is deliberately caller-specific so the wait
# cannot affect any other PeekMessage user; with a different MGS2_EXE the
# address must be re-derived with MGS2_PEEK_STATS=1, or the wait simply never
# triggers and behaviour falls back to stock.
#
# Set MGS2_USER32_DLL= to go back to the stock user32.
USER32_DLL="${MGS2_USER32_DLL:-user32_peek1.dll}"
if [ -n "$USER32_DLL" ]; then
    export MGS2_PEEK_HOT="${MGS2_PEEK_HOT:-401176}"
    export MGS2_PEEK_WAIT="${MGS2_PEEK_WAIT:-1}"
    # 4 ms rather than 1: the wait length A/B showed the main thread dropping
    # from 12% of a core to 4% with no change in frame rate (36.43 -> 36.69) and
    # no change in wined3d_cs, which stays at 62% throughout. The reclaimed CPU
    # does not become frames -- the renderer is not CPU-starved -- but it is
    # free, and it is heat and battery not spent. 8 ms reclaims a little more;
    # 4 ms is the conservative pick since the wait also gates input latency,
    # bounded in practice by QS_ALLINPUT waking it on the first message.
    export MGS2_PEEK_WAIT_MS="${MGS2_PEEK_WAIT_MS:-4}"
fi
[ -n "$USER32_DLL" ] && [ ! -r "$GAMEDIR/$USER32_DLL" ] && USER32_DLL=""

# PE dmsynth carrying Wine 11.2's DirectMusic sink series (Anton Baskanov):
# fixed write latency, GetCurrentPosition moved to its own thread, a
# continuously-estimated buffer position, and BUFFER_SUBDIVISIONS lowered from
# 100 to 10. Wine 11.0 woke the synth thread every ~10 ms to query the position
# and lock the buffer, which this port cannot sustain -- 816 "Underrun detected"
# in one run, and a capture of the speaker sink monitor is all zeros while the
# game is supposedly playing music.
# PE dsound with a counter on Wine 11.0's shared-DirectSoundDevice path. Every
# DirectSoundCreate() for one endpoint is handed the same device and primary
# buffer; upstream split them in May 2026 after a game whose cutscene engine was
# silently given the main engine's incompatible primary buffer and went mute.
# MGS2_DSOUND_SHARE=0 disables the sharing.
# Default: stock. dsound_share1.dll only adds diagnostics (a device-reuse
# counter, and amplitude probes behind MGS2_DSOUND_PROBE), and MGS2 turned out
# never to hit the reuse path, so it buys nothing in normal play.
# PE dmime with IDirectMusicAudioPath::QueryInterface answering
# IID_IDirectMusicGraph. The game asks its audio path for the tool graph that
# way -- Windows supports it, Wine 11.0 only offered the graph through
# GetObjectInPath and returned E_NOINTERFACE, which the game reports as
# "IID_IDirectMusicGraph Refarence Error" and treats as fatal. The trace shows
# exactly that QI failing twice at startup.
# MGS2 builds many dynamic DirectMusic audio paths.  Wine 11.0 used one
# dmsynth per path, but MGS2 downloads DLS instruments into one of them and
# plays SFX notes through another.  This build gives all paths one shared port;
# it restores game SFX and removes the duplicate synth workers.  Set
# Keep DirectMusic on the established baseline.  It is not in the gameplay
# SFX path and is left independently overridable for diagnostics.
DMIME_DLL="${MGS2_DMIME_DLL:-dmime_graphqi.dll}"
[ -n "$DMIME_DLL" ] && [ ! -r "$GAMEDIR/$DMIME_DLL" ] && DMIME_DLL=""

DSOUND_DLL="${MGS2_DSOUND_DLL:-}"
[ -n "$DSOUND_DLL" ] && [ ! -r "$GAMEDIR/$DSOUND_DLL" ] && DSOUND_DLL=""

# dmusic holds the ports. Overridable so the download/PlayBuffer census can be
# swapped in without touching the shipping library.
DMUSIC_DLL="${MGS2_DMUSIC_DLL:-}"
[ -n "$DMUSIC_DLL" ] && [ ! -r "$GAMEDIR/$DMUSIC_DLL" ] && DMUSIC_DLL=""

DMSYNTH_DLL="${MGS2_DMSYNTH_DLL:-dmsynth_wine112.dll}"
[ -n "$DMSYNTH_DLL" ] && [ ! -r "$GAMEDIR/$DMSYNTH_DLL" ] && DMSYNTH_DLL=""

# Which d3d8 to mount. Only meaningful because d3d8=builtin (see WINEDLLOVERRIDES
# above) put Wine's own module back in the chain. d3d8_mgs2fast1.dll carries two
# MGS2-specific fast paths, both switchable:
#   MGS2_D3D8_STATEFAST=0       stop dropping redundant SetRenderState /
#                               SetTextureStageState / SetSamplerState calls.
#                               Each redundant call otherwise takes the global
#                               wined3d mutex and walks into the stateblock.
#   MGS2_D3D8_MANAGED_DIRTY=0   go back to re-uploading every bound managed
#                               texture on every draw. The fast path only uploads
#                               after Unlock, AddDirtyRect, UpdateTexture,
#                               CopyRects or creation, which are the only ways a
#                               managed texture's content can change.
# If textures ever look stale, MGS2_D3D8_MANAGED_DIRTY=0 is the first thing to try.
D3D8_DLL="${MGS2_D3D8_DLL:-d3d8_mgs2fast1.dll}"
[ -n "$D3D8_DLL" ] && [ ! -r "$GAMEDIR/$D3D8_DLL" ] && D3D8_DLL=""

WINED3D_DLL="${MGS2_WINED3D_DLL:-wined3d_glslcache2.dll}"
[ -r "$GAMEDIR/$WINED3D_DLL" ] || WINED3D_DLL="wined3d_dbg42_gles_present.dll"

# ---------------------------------------------------------------------------
# Thermal / clock policy
#
# The console has reset during heavy loads; observed hardware trip points are
# ~83 C, ~88 C and ~95 C, and duplicate launches previously pushed it past
# 92 C.  The old guard polled only every 2 s and did nothing but kill the game
# at 90 C, which is both too late for a spike and needlessly destructive.
#
# Instead: cap the top frequency bin, pin the governor to performance *within*
# that cap so frame times stay even, then step the cap down as temperature
# climbs and back up as it recovers.  Killing is the last resort, at a
# temperature still below the observed reset point.
# ---------------------------------------------------------------------------
# Measured 5 Aug 2026, same gameplay scene, only this list changed:
#   top step 1608000 -> 13.3-13.9 fps, readback 20.3-20.7 ms/f, CPU 81.7-82.8 C
#   top step 1992000 -> 17.7 fps      (+29%), readback 15.2-15.6 ms/f, 81.1-82.8 C
# Temperature did not rise and the 88 C stop was never approached, because the
# guard below does its job: the cap oscillates 1992 <-> 1800 <-> 1608 as heat
# builds, and even with those step-downs the frame rate is a third higher.
# readback scales with the clock, which is the evidence that it is CPU work.
#
# cpuinfo_max_freq on this unit is 1992000 (overclocked); the old 1608000 top
# step was leaving a quarter of the CPU unused. scaling_available_frequencies
# lists only up to 1800000 and cpufreq "boost" reads 0, yet 1992000 is
# accepted and reached.
FREQ_STEPS="${MGS2_FREQ_STEPS:-1992000 1800000 1608000 1416000}"
TEMP_DOWN="${MGS2_TEMP_DOWN:-84000}"   # step the cap down above this
TEMP_UP="${MGS2_TEMP_UP:-76000}"       # allow stepping back up below this
TEMP_KILL="${MGS2_TEMP_KILL:-88000}"   # hard stop, below the ~92 C reset point
POLL="${MGS2_TEMP_POLL:-0.5}"

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

set_cpu_cap() {
    local freq="$1" p
    for p in $CPU_POLICIES; do
        echo performance > "$p/scaling_governor" 2>/dev/null
        echo "$freq"     > "$p/scaling_max_freq" 2>/dev/null
    done
}

mount_bind() {
    local src="$1" dst="$2"
    [ -r "$src" ] || return 1
    while grep -q " $dst " /proc/mounts; do
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

mount_bind "$GAMEDIR/box86-clean1" /usr/bin/box86 || exit 1
mount_bind "$GAMEDIR/$WIN32U_SO" /usr/lib/wine/i386-unix/win32u.so || exit 1
mount_bind "$GAMEDIR/$WAYLAND_SO" /usr/lib/wine/i386-unix/winewayland.so || exit 1
[ -n "$OPENGL32_SO" ] && { mount_bind "$GAMEDIR/$OPENGL32_SO" /usr/lib/wine/i386-unix/opengl32.so || exit 1; }
[ -n "$NTDLL_SO" ] && { mount_bind "$GAMEDIR/$NTDLL_SO" /usr/lib/wine/i386-unix/ntdll.so || exit 1; }
# dbg42 keeps the reliable, continuously updating FBO presentation path.
mount_bind "$GAMEDIR/$WINED3D_DLL" /usr/lib/wine/i386-windows/wined3d.dll || exit 1
[ -n "$USER32_DLL" ] && { mount_bind "$GAMEDIR/$USER32_DLL" /usr/lib/wine/i386-windows/user32.dll || exit 1; }
[ -n "$D3D8_DLL" ] && { mount_bind "$GAMEDIR/$D3D8_DLL" /usr/lib/wine/i386-windows/d3d8.dll || exit 1; }
[ -n "$DMSYNTH_DLL" ] && { mount_bind "$GAMEDIR/$DMSYNTH_DLL" /usr/lib/wine/i386-windows/dmsynth.dll || exit 1; }
[ -n "$DSOUND_DLL" ] && { mount_bind "$GAMEDIR/$DSOUND_DLL" /usr/lib/wine/i386-windows/dsound.dll || exit 1; }
[ -n "$DMIME_DLL" ] && { mount_bind "$GAMEDIR/$DMIME_DLL" /usr/lib/wine/i386-windows/dmime.dll || exit 1; }
[ -n "$DMUSIC_DLL" ] && { mount_bind "$GAMEDIR/$DMUSIC_DLL" /usr/lib/wine/i386-windows/dmusic.dll || exit 1; }

cleanup() {
    [ -n "${THERMAL_PID:-}" ] && kill "$THERMAL_PID" 2>/dev/null || true
    [ -n "${TRACE_GUARD_PID:-}" ] && kill "$TRACE_GUARD_PID" 2>/dev/null || true
    [ -n "${WINE_PID:-}" ] && kill "$WINE_PID" 2>/dev/null || true
    [ -n "${GPTOKEYB_PID:-}" ] && kill "$GPTOKEYB_PID" 2>/dev/null || true
    killall -9 wineserver services.exe explorer.exe winedevice.exe plugplay.exe svchost.exe 2>/dev/null || true
    # The game itself can outlive both the launcher and wineserver. An orphan
    # keeps /tmp/mgs2-substance.lock held, and the next launch from the
    # EmulationStation menu then exits silently with no visible reason.
    # The bracket makes the pattern not match this script's own command line
    # (plain `pkill -f` matching itself has bitten this project before).
    pkill -9 -f "[${EXE:0:1}]${EXE:1}" 2>/dev/null || true
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
    unmount_all /usr/lib/wine/i386-unix/ntdll.so
    unmount_all /usr/bin/box86
    [ -n "${ESUDO:-}" ] && $ESUDO systemctl restart oga_events >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

save_cpu_state
FREQ_ARR=($FREQ_STEPS)
set_cpu_cap "${FREQ_ARR[0]}"

cd "$GAMEDIR/game/bin" || exit 1
if [ -x /usr/bin/gptokeyb ] && [ -r "$GAMEDIR/mgs2.gptk" ]; then
    /usr/bin/gptokeyb "$EXE" -c "$GAMEDIR/mgs2.gptk" >/tmp/mgs2-gptokeyb.log 2>&1 &
    GPTOKEYB_PID=$!
fi
# MGS2_TRACE=1 captures the game's own output to a file so a fault seen while
# playing normally can be diagnosed afterwards. The automated harness cannot be
# used for this: it mashes the confirm button to reach gameplay quickly, which
# skips the cutscenes -- the very thing under investigation.
#
# The log is capped and lives on /storage, not the 488 MB tmpfs, and the cap is
# enforced by a watchdog rather than trusted to stay small: an unbounded debug
# channel filling the disk has already caused a user-visible failure once.
TRACE_LOG="${MGS2_TRACE_LOG:-$GAMEDIR/trace.log}"
TRACE_MAX_MB="${MGS2_TRACE_MAX_MB:-200}"
if [ "${MGS2_TRACE:-0}" = 1 ]; then
    : > "$TRACE_LOG"
    ( while [ -e "$TRACE_LOG" ]; do
          sz=$(stat -c %s "$TRACE_LOG" 2>/dev/null || echo 0)
          [ "$sz" -gt $((TRACE_MAX_MB * 1048576)) ] && { echo "--- trace capped at ${TRACE_MAX_MB} MB ---" >> "$TRACE_LOG"; break; }
          sleep 5
      done ) &
    TRACE_GUARD_PID=$!
    if type taskset >/dev/null 2>&1; then
        taskset -c 0-3 box64 /usr/bin/wine "$EXE" >>"$TRACE_LOG" 2>&1 &
    else
        box64 /usr/bin/wine "$EXE" >>"$TRACE_LOG" 2>&1 &
    fi
elif type taskset >/dev/null 2>&1; then
    taskset -c 0-3 box64 /usr/bin/wine "$EXE" &
else
    box64 /usr/bin/wine "$EXE" &
fi
WINE_PID=$!

thermal_guard() {
    local temp idx n cur fifo
    n=${#FREQ_ARR[@]}
    idx=0
    # Poll without forking.  The old loop ran `cat` and `sleep` twice a second and
    # measured about 3% of a core; on a device whose frame rate is limited by heat,
    # the guard should not spend the budget it exists to protect.  bash reads the
    # thermal zone itself, and a timed read on an idle fifo replaces sleep, so a
    # poll costs no process at all.  The cadence and every threshold are unchanged:
    # reaction time is what keeps the console below its reset point.
    #
    # fd 8, not 9 -- fd 9 is the instance lock this script holds through flock.
    fifo=$(mktemp -u /tmp/mgs2-guard.XXXXXX)
    if mkfifo "$fifo" 2>/dev/null; then
        exec 8<>"$fifo"
        rm -f "$fifo"
    fi
    while kill -0 "$WINE_PID" 2>/dev/null; do
        temp=0
        read -r temp < /sys/class/thermal/thermal_zone0/temp 2>/dev/null || temp=0
        [ -n "$temp" ] || temp=0
        if [ "$temp" -ge "$TEMP_KILL" ]; then
            echo "$(date): thermal kill at ${temp}mC" >> /tmp/mgs2-thermal-guard.log
            kill "$WINE_PID" 2>/dev/null || true
            sleep 2
            kill -9 "$WINE_PID" 2>/dev/null || true
            return
        elif [ "$temp" -ge "$TEMP_DOWN" ] && [ "$idx" -lt "$((n - 1))" ]; then
            idx=$((idx + 1))
            cur=${FREQ_ARR[$idx]}
            set_cpu_cap "$cur"
            echo "$(date): ${temp}mC -> cap ${cur}" >> /tmp/mgs2-thermal-guard.log
        elif [ "$temp" -le "$TEMP_UP" ] && [ "$idx" -gt 0 ]; then
            idx=$((idx - 1))
            cur=${FREQ_ARR[$idx]}
            set_cpu_cap "$cur"
            echo "$(date): ${temp}mC -> cap ${cur}" >> /tmp/mgs2-thermal-guard.log
        fi
        if [ -e /proc/self/fd/8 ]; then
            read -r -t "$POLL" -u 8 _ 2>/dev/null || true
        else
            sleep "$POLL"
        fi
    done
}
thermal_guard &
THERMAL_PID=$!
wait "$WINE_PID"

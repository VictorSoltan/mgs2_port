#!/usr/bin/env bash
#
# Read-only context dump from the console. Nothing here starts, stops or
# reconfigures anything; safe to run while the game is not running.
#
#   ./mgs2_collect_context.sh /storage/roms/ports/MGS2-Substance
#
# By default this collects the *system* state only and records binaries as
# sha256 + file type, without copying them. The modules themselves are already
# in the repo (recovered-session/device-artifacts, binaries/) and copying
# ~32 MB off the SD card adds minutes and nothing else. Pass --with-binaries
# if a specific module on the device is suspected of differing from the repo
# copy -- the sha256 in the manifest is what tells you whether it does.
set -u

WITH_BINARIES=0
ARGS=()
for a in "$@"; do
  case "$a" in
    --with-binaries) WITH_BINARIES=1 ;;
    *) ARGS+=("$a") ;;
  esac
done
set -- ${ARGS+"${ARGS[@]}"}

GAME_DIR="${1:-$PWD}"
STAMP="$(date +%Y%m%d-%H%M%S 2>/dev/null || echo unknown)"
OUT="mgs2-perf-context-${STAMP}"
mkdir -p "$OUT/system" "$OUT/runtime"

# This has already gone wrong once: the collector was run on the development PC,
# the tarball looked plausible, and a whole round of analysis was done against
# Ubuntu/x86_64/NVIDIA instead of ROCKNIX/aarch64/Mali. Fail loudly, in the
# output as well as on the terminal, so a wrong-host run cannot be mistaken for
# a console run again.
ARCH="$(uname -m 2>/dev/null || echo unknown)"
if [ "$ARCH" != "aarch64" ]; then
    {
        echo "########################################################"
        echo "## WRONG HOST: uname -m = $ARCH, expected aarch64"
        echo "## This is NOT the RG353VS. Run it on the console:"
        echo "##   ./mgs2_collect_context.sh /storage/roms/ports/MGS2-Substance"
        echo "## Everything below describes the wrong machine."
        echo "########################################################"
    } | tee "$OUT/system/00-WRONG-HOST.txt" >&2
    OUT="mgs2-perf-context-${STAMP}-WRONG-HOST-${ARCH}"
    mv "mgs2-perf-context-${STAMP}" "$OUT" 2>/dev/null || true
fi

# Hangover preflight. Page size first: the Hangover Wine fork warns explicitly on
# anything other than 4 KiB, so this decides whether the port is viable at all.
{
    echo "## uname -a";  uname -a 2>&1
    echo "## uname -m";  uname -m 2>&1
    echo "## PAGESIZE";  getconf PAGESIZE 2>&1
    echo "## glibc";     ldd --version 2>&1 | head -1
} > "$OUT/system/hangover-preflight.txt" 2>&1

run() {
  local name="$1"; shift
  {
    echo "> $*"
    "$@"
  } >"$OUT/system/$name.txt" 2>&1 || true
}

{
  echo "date: $(date -Is 2>/dev/null || date)"
  echo "game_dir: $GAME_DIR"
  echo
  uname -a 2>&1 || true
  echo
  cat /etc/os-release 2>/dev/null || true
} > "$OUT/system/basic.txt"

{
  echo "=== box86 ==="
  command -v box86 || true
  box86 --version 2>&1 || true
  echo
  echo "=== box64 ==="
  command -v box64 || true
  box64 --version 2>&1 || true
  echo
  echo "=== wine ==="
  command -v wine || true
  wine --version 2>&1 || true
} > "$OUT/system/versions.txt"

{
  echo "=== ~/.box86rc ==="
  cat "$HOME/.box86rc" 2>/dev/null || echo "(missing)"
  echo
  echo "=== /etc/box86.box86rc ==="
  cat /etc/box86.box86rc 2>/dev/null || echo "(missing)"
  echo
  echo "=== ~/.box64rc ==="
  cat "$HOME/.box64rc" 2>/dev/null || echo "(missing)"
  echo
  echo "=== /etc/box64.box64rc ==="
  cat /etc/box64.box64rc 2>/dev/null || echo "(missing)"
} > "$OUT/system/box-rc.txt"

{
  echo "=== /proc/cmdline ==="
  cat /proc/cmdline 2>/dev/null || true
  echo
  echo "=== ntsync ==="
  ls -l /dev/ntsync 2>&1 || true
  echo
  echo "=== kernel config: NTSYNC/FUTEX ==="
  if [ -r /proc/config.gz ]; then
    zcat /proc/config.gz 2>/dev/null | grep -Ei 'NTSYNC|FUTEX' || true
  elif [ -r "/boot/config-$(uname -r)" ]; then
    grep -Ei 'NTSYNC|FUTEX' "/boot/config-$(uname -r)" || true
  else
    echo "kernel config not readable"
  fi
  echo
  echo "=== perf ==="
  command -v perf || true
  perf --version 2>&1 || true
  cat /proc/sys/kernel/perf_event_paranoid 2>/dev/null || true
} > "$OUT/system/kernel-sync-perf.txt"

{
  for c in /sys/devices/system/cpu/cpu[0-9]*; do
    [ -d "$c/cpufreq" ] || continue
    echo "### $(basename "$c")"
    for f in scaling_driver scaling_governor scaling_cur_freq scaling_min_freq scaling_max_freq cpuinfo_cur_freq cpuinfo_min_freq cpuinfo_max_freq scaling_available_frequencies scaling_available_governors; do
      [ -r "$c/cpufreq/$f" ] && printf '%s: ' "$f" && cat "$c/cpufreq/$f"
    done
    echo
  done
} > "$OUT/system/cpufreq.txt" 2>&1

{
  for z in /sys/class/thermal/thermal_zone*; do
    [ -d "$z" ] || continue
    printf '%s type=' "$z"; cat "$z/type" 2>/dev/null || true
    printf 'temp='; cat "$z/temp" 2>/dev/null || true
    for t in "$z"/trip_point_*_temp; do
      [ -r "$t" ] && printf '%s=' "$(basename "$t")" && cat "$t"
    done
    echo
  done
} > "$OUT/system/thermal.txt" 2>&1

{
  for d in /sys/class/devfreq/*; do
    [ -d "$d" ] || continue
    echo "### $d"
    for f in name governor cur_freq min_freq max_freq available_frequencies available_governors; do
      [ -r "$d/$f" ] && printf '%s: ' "$f" && cat "$d/$f"
    done
    echo
  done
} > "$OUT/system/devfreq.txt" 2>&1

{
  echo "=== eglinfo -B ==="
  if command -v eglinfo >/dev/null 2>&1; then
    timeout 10 eglinfo -B 2>&1 || true
  else
    echo "eglinfo not installed"
  fi
  echo
  echo "=== es2_info ==="
  if command -v es2_info >/dev/null 2>&1; then
    timeout 10 es2_info 2>&1 || true
  else
    echo "es2_info not installed"
  fi
  echo
  # eglinfo/es2_info are usually absent on ROCKNIX, and the batching decision
  # needs a definite answer on the multi-draw entry points rather than an
  # assumption. The blob carries its extension string and its exported symbols,
  # both of which can be read without a context.
  # ROCKNIX has no nm and no objdump, and the first version of this check piped
  # nm into grep: every symbol came back "absent", including glDrawElementsInstanced,
  # which is core GLES 3.0 on a GLES 3.2 device. A missing tool must never read as
  # a missing symbol, so grep the file directly -- exported names live in .dynstr
  # and this needs no binutils at all. readelf is used only to corroborate.
  echo "=== libmali: multi-draw and instancing symbols ==="
  echo "tools: nm=$(command -v nm || echo MISSING) readelf=$(command -v readelf || echo MISSING)"
  for lib in /usr/lib/libmali*.so* /usr/lib/aarch64-linux-gnu/libmali*.so*; do
    [ -e "$lib" ] || continue
    # Resolve symlinks so the size reported is the real object, not the link.
    real=$(readlink -f "$lib" 2>/dev/null || echo "$lib")
    echo "--- $lib -> $real ($(stat -c %s "$real" 2>/dev/null) bytes)"
    for sym in glMultiDrawArrays glMultiDrawArraysEXT glMultiDrawElements \
               glMultiDrawElementsEXT glMultiDrawElementsBaseVertexEXT \
               glDrawArraysInstanced glDrawElementsInstanced \
               glMultiDrawArraysIndirect glDrawElementsInstancedBaseVertex \
               glTexStorage2D eglCreateWindowSurface eglCreateImageKHR \
               glEGLImageTargetTexture2DOES; do
      if grep -qa "$sym" "$real" 2>/dev/null; then
        echo "  PRESENT $sym"
      else
        echo "  absent  $sym"
      fi
    done
  done
  echo
  echo "=== libmali: advertised GL_EXT/OES extension strings ==="
  for lib in /usr/lib/libmali*.so* /usr/lib/aarch64-linux-gnu/libmali*.so*; do
    [ -e "$lib" ] || continue
    echo "--- $lib"
    strings "$lib" 2>/dev/null \
      | grep -oE 'GL_(EXT|OES|ARM|KHR)_[A-Za-z0-9_]+' | sort -u
  done
} > "$OUT/system/gles.txt"

# Box86 configuration precedence. Box86 reads ~/.box86rc and
# /etc/box86.box86rc *over* the environment, so the values launch.sh exports are
# not necessarily the ones in effect. BOX86_NORCFILES=1 is the only way to be
# sure for a controlled benchmark; record whether this build honours it.
{
  echo "=== box86 binary ==="
  command -v box86 || true
  for b in $(command -v box86 2>/dev/null) /usr/bin/box86 /usr/local/bin/box86; do
    [ -x "$b" ] || continue
    echo "--- $b"
    sha256sum "$b" 2>/dev/null || true
    echo
    echo "known env knobs compiled in:"
    strings "$b" 2>/dev/null | grep -E '^BOX86_[A-Z_]+$' | sort -u
    echo
    echo "futex support referenced by the binary:"
    for s in futex_waitv SYS_futex_waitv __NR_futex_waitv futex; do
      printf '  %-18s %s\n' "$s" "$(strings "$b" 2>/dev/null | grep -cw "$s")"
    done
    break
  done
  echo
  echo "=== kernel futex_waitv availability ==="
  grep -w futex_waitv /proc/kallsyms 2>/dev/null | head -3 || echo "(kallsyms unreadable or symbol absent)"
} > "$OUT/system/box86-config.txt" 2>&1

{
  echo "=== /proc/meminfo ==="
  cat /proc/meminfo 2>/dev/null | head -20 || true
  echo
  echo "=== swap ==="
  cat /proc/swaps 2>/dev/null || true
  echo
  echo "=== loadavg ==="
  cat /proc/loadavg 2>/dev/null || true
} > "$OUT/system/memory.txt" 2>&1

RUNTIME_FILES=(
  "mgs2_sse_rg353vs_port.exe"
  "wined3d_release3.dll"
  "d3d8_mgs2fast1.dll"
  "box86-clean1"
  "winewayland_stall1.so"
  "winewayland_async1.so"
  "win32u_glfuncs3.so"
  "opengl32_glesver1.so"
  "ntdll_fastyield.so"
  "user32_peek1.dll"
  "dsound_se1.dll"
  "dmime_se1.dll"
  "dmsynth_se1.dll"
  "launch.sh"
  "MGS2-Substance.sh"
)

{
  echo "GAME_DIR=$GAME_DIR"
  echo
  for f in "${RUNTIME_FILES[@]}"; do
    p="$GAME_DIR/$f"
    if [ -e "$p" ]; then
      echo "=== $f ==="
      ls -lh "$p" 2>&1 || true
      sha256sum "$p" 2>&1 || true
      file "$p" 2>&1 || true
      echo
      [ "$WITH_BINARIES" = 1 ] && cp -a "$p" "$OUT/runtime/" 2>/dev/null || true
    else
      echo "MISSING: $f"
    fi
  done
} > "$OUT/system/runtime-manifest.txt" 2>&1

# Also preserve the exact launcher/config scripts if they live one level above/below.
for extra in "$GAME_DIR/device/launch.sh" "$GAME_DIR/device/MGS2-Substance.sh"; do
  [ -f "$extra" ] && cp -a "$extra" "$OUT/runtime/$(basename "$extra")" 2>/dev/null || true
done

if command -v tar >/dev/null 2>&1; then
  tar -czf "$OUT.tar.gz" "$OUT"
  echo "Created: $OUT.tar.gz"
else
  echo "Created directory: $OUT (tar not available)"
fi

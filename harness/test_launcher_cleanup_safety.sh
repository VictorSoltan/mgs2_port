#!/bin/sh
# Regression gate for launcher cleanup, clock recovery and research leakage.
set -eu

REPO=$(cd "$(dirname "$0")/.." && pwd)
ENGINE="$REPO/device/launch-play-dxvk-fp17.sh"

bash -n "$ENGINE"

# Signal traps must terminate after cleanup rather than resume the launch.
! grep -Fq 'trap cleanup EXIT INT TERM' "$ENGINE"
grep -Fq 'trap cleanup EXIT' "$ENGINE"
grep -Fq "trap 'cleanup_signal 130' INT" "$ENGINE"
grep -Fq "trap 'cleanup_signal 143' TERM" "$ENGINE"
grep -A6 '^cleanup_signal()' "$ENGINE" | grep -Fq 'trap - EXIT HUP INT TERM'
grep -A6 '^cleanup_signal()' "$ENGINE" | grep -Fq 'exit "$status"'

# A temporary image remains present if its bind could not be removed.
grep -A65 '^cleanup()' "$ENGINE" | grep -Fq 'game_image_unmounted=0'
grep -A65 '^cleanup()' "$ENGINE" | grep -Fq 'preserving busy mounted temporary game image'
grep -A65 '^cleanup()' "$ENGINE" | grep -Fq 'services.exe start.exe explorer.exe'
grep -A65 '^cleanup()' "$ENGINE" | grep -Fq '[s]tart.exe|[e]xplorer.exe'

# Interrupted runs retain an exact same-boot baseline, while every clock write
# is read back and a failed cap aborts before the game starts.
grep -Fq 'CPU_STATE_FILE=/tmp/mgs2-cpu-baseline.state' "$ENGINE"
grep -Fq 'recovered pre-launch clock baseline after an interrupted run' "$ENGINE"
grep -Fq 'write_sysfs_exact()' "$ENGINE"
grep -Fq 'save_cpu_state || exit 1' "$ENGINE"
grep -Fq 'set_final_cpu_cap || exit 1' "$ENGINE"

# Both values that could turn play into a research run are rejected before the
# closed route is selected; the AABB path is also fixed off in this engine.
grep -A20 '^mgs2_reject_research_overrides()' "$ENGINE" | \
    grep -Fq 'MGS2_BOX86_NATIVE_AABB MGS2_ISLAND_AB_MEASURE'
grep -Fq 'export MGS2_BOX86_NATIVE_AABB=0' "$ENGINE"
! grep -Fq 'export MGS2_ISLAND_AB="$MGS2_ISLAND_AB_MEASURE"' "$ENGINE"

echo "ok     signal cleanup terminates, busy images are retained, and clock state is fail-closed"

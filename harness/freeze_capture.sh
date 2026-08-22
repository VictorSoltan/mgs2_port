#!/bin/sh
# One unattended run that captures a freeze from three angles at once.
#
# The player reports freezes after a save loads and when enemies enter. A first
# run established what they are NOT: the probe kept sampling every 50 ms right
# through them, so nothing global stalled, and the process burned ~13 s of CPU
# across threads inside an 8.8 s window. The freeze is computation, not waiting.
#
# What it does not yet say is WHICH computation, and the three plausible answers
# want different fixes: Box86 translating newly reached guest code, the game's
# own main-thread work, or driver/GL work. perf separates them directly --
# [JIT] is translated guest code, box86 is the emulator's own text (dynarec
# included), libmali is the driver.
#
# Everything here is stamped with CLOCK_MONOTONIC: the presenter's `tick=`,
# perf's -k mono, and the probe. /proc/uptime is deliberately NOT used -- it
# counts suspend and this handheld sleeps on its own.
set -u
A="${1:-/storage/roms/ports/ablogs/freeze2}"
SECS="${FREEZE_SECS:-200}"
G=/storage/roms/ports/MGS2-Substance
mkdir -p "$A"
rm -f "$A"/game.log "$A"/stall.csv "$A"/perf.data "$A"/perf.script "$A"/autoload.log

# Kernel samples, and enough time to read a 25-thread map without truncating it.
echo -1 > /proc/sys/kernel/perf_event_paranoid 2>/dev/null

echo "== autoload =="
# The guest map is what turns "[JIT] guest code, 70% of the freeze" into named
# guest functions. It costs a 4 MB buffer and one 16-byte append per compiled
# block, so it is only switched on for a capture, never in production.
MGS2_AUTOLOAD_LOG="$A/game.log" \
MGS2_BOX86_BIN="${MGS2_BOX86_BIN:-box86-island58-p75a-steady}" \
MGS2_WINED3D_DLL="${MGS2_WINED3D_DLL:-wined3d_p75a_steady.dll}" \
MGS2_BOX86_GUEST_MAP="${MGS2_BOX86_GUEST_MAP:-}" \
    setsid nohup sh "$G/autoload_save.sh" "$A/shots" z \
    > "$A/autoload.log" 2>&1 < /dev/null &

# Wait for the NEW process. autoload kills the old one first, so waiting for
# "frames started" in its log rather than for any process at all is what keeps
# perf from attaching to the corpse of the previous run.
n=0
while [ "$n" -lt 200 ]; do
    grep -q 'кадры пошли' "$A/autoload.log" 2>/dev/null && break
    n=$((n + 2)); sleep 2
done
PID=
for p in /proc/[0-9]*; do
    [ "$(cat "$p/comm" 2>/dev/null)" = mgs2_sse_rg353v ] && PID=${p#/proc/}
done
[ -n "$PID" ] || { echo "игра не поднялась"; exit 1; }
echo "игра pid=$PID через ${n}c, снимаю ${SECS}c"

setsid nohup python3 "$A/../stall_probe.py" --out "$A/stall.csv" \
    --period 50 --seconds "$SECS" --wait 20 > "$A/probe.log" 2>&1 < /dev/null &

perf record -k mono -F 199 -e cycles -p "$PID" --proc-map-timeout 10000 \
    -o "$A/perf.data" -- sleep "$SECS" 2>&1 | tail -2

# All of this has to happen while the process is still alive: its maps, and
# Box86's guest map, live in that process and vanish with it.
cp "/proc/$PID/maps" "$A/maps.txt" 2>/dev/null
if [ -n "${MGS2_BOX86_GUEST_MAP:-}" ]; then
    python3 "$A/../box86_guest_snapshot.py" --pid "$PID" \
        --box86 "/storage/roms/ports/MGS2-Substance/${MGS2_BOX86_BIN:-box86-island58-p75a-steady}" \
        --output "$A/guestmap.bin" 2>&1 | tail -2
fi
perf script -i "$A/perf.data" > "$A/perf.script" 2>/dev/null
perf script -i "$A/perf.data" -F comm,pid,tid,ip,sym,dso > "$A/perf.guest.script" 2>/dev/null
echo "семплов: $(wc -l < "$A/perf.script")"
echo "худшие кадры: $(grep -oaE 'worst [0-9]+ ms' "$A/game.log" | awk '{print $2}' | sort -rn | head -3 | tr '\n' ' ')"
echo "готово: $A"

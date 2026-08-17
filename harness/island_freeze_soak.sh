#!/bin/sh
# Accelerated freeze soak.
#
# Two harness defects fixed after the first attempt lost everything:
#
#   1. results went to /tmp, which is tmpfs. The console drained its battery and
#      rebooted mid-run, and every result went with it. They go to /storage now,
#      and each cycle is written as it finishes rather than at the end.
#   2. no power check. A multi-hour unattended run on battery ends exactly one
#      way. Refuse to start off charger or below the threshold, and stop if the
#      charger goes away mid-run.
#
# What it measures: MGS2_CS_SPIN_COUNT lowers WINED3D_CS_SPIN_COUNT from 2000 to
# 1, so the CS crosses queue-empty -> waiting_for_event -> alert wait on nearly
# every drain instead of rarely. Patch 52's census then answers, on a freeze,
# whether work was published (verdict A) or the queues were empty (verdict B).
set -u
G=/storage/roms/ports/MGS2-Substance
LOG=/tmp/autoload-game.log
OUT=/storage/mgs2-soak            # NOT /tmp: this console reboots
mkdir -p $OUT
RESULT=$OUT/results.txt
CYCLES="${CYCLES:-3}"
PLAY="${PLAY:-300}"
MIN_BATTERY="${MIN_BATTERY:-55}"

battery()  { cat /sys/class/power_supply/battery/capacity 2>/dev/null || echo 100; }
charging() { [ "$(cat /sys/class/power_supply/charger/online 2>/dev/null || echo 1)" = "1" ]; }

if ! charging; then
    echo "ОТКАЗ: зарядка не подключена. Прогон на батарее заканчивается разрядом." | tee -a $RESULT
    exit 1
fi
if [ "$(battery)" -lt "$MIN_BATTERY" ]; then
    echo "ОТКАЗ: заряд $(battery)%, нужно >= ${MIN_BATTERY}%." | tee -a $RESULT
    exit 1
fi
echo "== старт $(date) заряд $(battery)% ==" | tee -a $RESULT

cycle() {
    sm="$1"; n="$2"
    if ! charging; then echo "ОСТАНОВ: зарядка пропала на sm=$sm #$n" | tee -a $RESULT; exit 1; fi
    sh /tmp/cleanup.sh >/dev/null 2>&1
    env MGS2_AUTOLOAD_LAUNCHER="$G/launch-island-dbg.sh" MGS2_SAVE_UP=2 \
        MGS2_WINED3D_DLL=wined3d_p52_cs_census.dll \
        MGS2_CS_DEADLOCK_CENSUS=1 MGS2_CS_SPIN_COUNT="${SPIN:-1}" \
        MGS2_GL_STATS=300 MGS2_PLAY_WINEDEBUG=-all,err+waylanddrv \
        BOX86_DYNAREC_STRONGMEM="$sm" BOX86_SHOWSEGV=1 \
        timeout 420 sh $G/autoload_save.sh /tmp/soak2-shots z >/dev/null 2>&1
    PID=""
    for p in /proc/[0-9]*; do [ "$(cat $p/comm 2>/dev/null)" = "mgs2_sse_rg353v" ] && PID=$(basename $p); done
    [ -n "$PID" ] || { echo "sm=$sm #$n: НЕ ЗАПУСТИЛАСЬ (заряд $(battery)%)" | tee -a $RESULT; return; }
    last=$(grep -c "present stats" $LOG); stuck=0; t=0
    while [ $t -lt $PLAY ]; do
        sleep 15; t=$((t+15))
        [ -d "/proc/$PID" ] || { echo "sm=$sm #$n: процесс исчез на ${t}с (заряд $(battery)%)" | tee -a $RESULT; return; }
        now=$(grep -c "present stats" $LOG)
        if [ "$now" = "$last" ]; then
            stuck=$((stuck+15))
            if [ $stuck -ge 45 ]; then
                echo "sm=$sm #$n: ЗАВИСЛА на ${t}с" | tee -a $RESULT
                python3 /tmp/cs_deadlock_census.py --pid $PID > $OUT/freeze-sm$sm-$n.census 2>&1
                python3 /tmp/deadlock.py $PID > $OUT/freeze-sm$sm-$n.futex 2>&1
                cp $LOG $OUT/freeze-sm$sm-$n.log 2>/dev/null
                grep -E "VERDICT" $OUT/freeze-sm$sm-$n.census | tee -a $RESULT
                return
            fi
        else
            stuck=0
        fi
        last=$now
    done
    echo "sm=$sm #$n: OK ${PLAY}с $(grep -o '= [0-9.]* fps' $LOG | tail -1) заряд $(battery)%" | tee -a $RESULT
}

n=1
while [ $n -le $CYCLES ]; do
    cycle 0 $n
    cycle 1 $n
    n=$((n+1))
done
sh /tmp/cleanup.sh >/dev/null 2>&1
echo "== ЗАВЕРШЕНО $(date) заряд $(battery)% ==" | tee -a $RESULT

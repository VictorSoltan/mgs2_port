#!/bin/sh
# Device half of the targeted Box86 native-Wayland listener ABI gate.
set -eu

GAME_DIR=${1:?usage: device_wayland_abi_gate.sh GAME_DIR BOX86}
BOX86=${2:?usage: device_wayland_abi_gate.sh GAME_DIR BOX86}
CLIENT=/tmp/mgs2-wayland-abi-client-i386
KEY_HELPER=/tmp/mgs2-send-key.py
PREFIX=/tmp/mgs2-wayland-abi-gate

for input in "$GAME_DIR/$BOX86" "$CLIENT" "$KEY_HELPER"; do
    [ -x "$input" ] || [ "$input" = "$KEY_HELPER" ] && [ -r "$input" ] || {
        echo "Wayland ABI gate input missing: $input" >&2
        exit 66
    }
done

# Never turn a diagnostic into the second game instance.
for proc in /proc/[0-9]*; do
    comm=$(cat "$proc/comm" 2>/dev/null || true)
    case "$comm" in
        wine|wine-preloader|wineserver|mgs2_sse_rg353v)
            echo "refusing Wayland ABI gate: active runtime process $proc ($comm)" >&2
            exit 70
            ;;
    esac
done

observer_pid= source1_pid= window_pid=
cleanup()
{
    for pid in $observer_pid $source1_pid $window_pid; do
        kill "$pid" 2>/dev/null || true
        wait "$pid" 2>/dev/null || true
    done
}
trap cleanup EXIT HUP INT TERM

run_probe()
{
    XDG_RUNTIME_DIR=/var/run/0-runtime-dir WAYLAND_DISPLAY=wayland-1 \
        BOX86_LOG=0 BOX86_NOBANNER=1 "$GAME_DIR/$BOX86" "$CLIENT" "$@"
}

rm -f "$PREFIX"-observer.log "$PREFIX"-source1.log \
    "$PREFIX"-receive.log "$PREFIX"-source2.log "$PREFIX"-exhaust.log \
    "$PREFIX"-window.log "$PREFIX"-key.log

run_probe observer 12 >"$PREFIX-observer.log" 2>&1 & observer_pid=$!
run_probe source 12 >"$PREFIX-source1.log" 2>&1 & source1_pid=$!
sleep 3

if run_probe receive >"$PREFIX-receive.log" 2>&1; then receive_rc=0; else receive_rc=$?; fi
if run_probe source 3 >"$PREFIX-source2.log" 2>&1; then source2_rc=0; else source2_rc=$?; fi
if wait "$observer_pid"; then observer_rc=0; else observer_rc=$?; fi
observer_pid=
if wait "$source1_pid"; then source1_rc=0; else source1_rc=$?; fi
source1_pid=
if run_probe exhaust >"$PREFIX-exhaust.log" 2>&1; then exhaust_rc=0; else exhaust_rc=$?; fi

run_probe window 9 >"$PREFIX-window.log" 2>&1 & window_pid=$!
sleep 3
if MGS2_FOCUS_MATCH="WAYLAND ABI PROBE" python3 "$KEY_HELPER" \
        --hold 180 --gap 250 enter >"$PREFIX-key.log" 2>&1; then
    key_rc=0
else
    key_rc=$?
fi
if wait "$window_pid"; then window_rc=0; else window_rc=$?; fi
window_pid=

for name in observer source1 receive source2 exhaust window key; do
    echo "=== $name ==="
    cat "$PREFIX-$name.log"
done
echo "process_rcs observer=$observer_rc source1=$source1_rc receive=$receive_rc source2=$source2_rc exhaust=$exhaust_rc window=$window_rc key=$key_rc"

normal_bad=$(awk 'BEGIN { IGNORECASE=1 }
    /unknown listener|no more slot|page fault|segmentation fault|segfault/ { n++ }
    END { print n + 0 }' \
    "$PREFIX-observer.log" "$PREFIX-source1.log" "$PREFIX-receive.log" \
    "$PREFIX-source2.log" "$PREFIX-window.log")

ok=1
for rc in "$observer_rc" "$source1_rc" "$receive_rc" "$source2_rc" \
        "$exhaust_rc" "$window_rc" "$key_rc"; do
    [ "$rc" -eq 0 ] || ok=0
done
[ "$normal_bad" -eq 0 ] || ok=0
grep -Eq 'source_send=[1-9]' "$PREFIX-source1.log" || ok=0
grep -Eq 'source_cancelled=[1-9]' "$PREFIX-source1.log" || ok=0
grep -Eq 'first_ten=10 eleventh=-1' "$PREFIX-exhaust.log" || ok=0
grep -Eq 'xdg_configure=[1-9].*keyboard_keymap=[1-9].*keyboard_key=[1-9]' \
    "$PREFIX-window.log" || ok=0

echo "normal_bad_matches=$normal_bad targeted_gate=$([ "$ok" -eq 1 ] && echo PASS || echo FAIL)"
[ "$ok" -eq 1 ]

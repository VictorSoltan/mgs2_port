# Catch what the game is doing during a multi-second freeze -- version 2.
#
# Version 1 only noticed stalls where the process went idle or blocked on I/O, and
# saw nothing in 300 s. That blind spot is the interesting case: if a ten-second
# frame is spent *burning* CPU somewhere -- inside the driver, or in the game's
# own loop -- a CPU-based detector never fires.
#
# So take the signal from the game itself. The presenter now prints one line the
# instant a frame exceeds 500 ms; this watcher keeps a rolling window of thread
# samples and, when that line appears, prints what every thread was doing across
# the stall. That distinguishes the three candidates directly:
#
#   threads in D with wchan in mmc/io   the SD card
#   one thread burning ticks            computation (driver, shader, game loop)
#   everything idle, no I/O             waiting on something else entirely
import glob, sys, time
from collections import deque

COMM = "mgs2_sse_rg353v"
POLL = 0.1
WINDOW = 150        # 15 s of history, enough to cover the worst frame seen


def read(path, default=""):
    try:
        return open(path).read().strip()
    except OSError:
        return default


def game_pid():
    for p in glob.glob("/proc/[0-9]*"):
        if read(p + "/comm") == COMM:
            return p.split("/")[-1]


def sample(pid):
    out = {}
    for t in glob.glob("/proc/%s/task/*" % pid):
        stat = read(t + "/stat")
        if not stat:
            continue
        f = stat[stat.rfind(")") + 2:].split()
        out[t.split("/")[-1]] = (read(t + "/comm"), f[0], int(f[11]) + int(f[12]),
                                 read(t + "/wchan", "-"))
    return out


def disk():
    try:
        return int(open("/sys/block/mmcblk0/stat").read().split()[2])
    except (OSError, IndexError):
        return 0


log_path = sys.argv[1]
duration = int(sys.argv[2]) if len(sys.argv) > 2 else 300
pid = game_pid()
if not pid:
    print("game not running")
    sys.exit(1)
print("watching pid %s for %ds, reacting to STALL lines in %s" % (pid, duration, log_path))

log = open(log_path, "r", errors="ignore")
log.seek(0, 2)
history = deque(maxlen=WINDOW)
deadline = time.time() + duration
seen = 0

while time.time() < deadline:
    time.sleep(POLL)
    history.append((time.time(), sample(pid), disk(),
                    read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq"),
                    read("/sys/class/thermal/thermal_zone0/temp")))

    for line in log.readlines():
        if "MGS2 STALL" not in line:
            continue
        seen += 1
        ms = line.split("frame took")[-1].strip()
        span = min(len(history), int(float(ms.split()[0]) / 1000.0 / POLL) + 6) if ms else 20
        window = list(history)[-span:]
        first, last = window[0], window[-1]
        print("\n=== stall %d: %s | covering %.1fs of samples | disk read %d KB"
              % (seen, ms, last[0] - first[0], (last[2] - first[2]) // 2))
        print("    cpu_cap %s -> %s, temp %s -> %s"
              % (first[3], last[3], first[4][:2], last[4][:2]))
        busiest = []
        for tid, (name, _, cpu, _) in last[1].items():
            if tid in first[1]:
                busiest.append((cpu - first[1][tid][2], name, tid))
        busiest.sort(reverse=True)
        for ticks, name, tid in busiest[:6]:
            states = "".join(s[1].get(tid, ("", "?", 0, ""))[1] for s in window)[-40:]
            wchans = {s[1].get(tid, ("", "", 0, "-"))[3] for s in window}
            wchans.discard("0")
            print("    %-18s ticks=%-5d states=%s" % (name, ticks, states))
            if wchans - {"-", ""}:
                print("    %-18s blocked on: %s" % ("", ", ".join(sorted(wchans - {"-", ""}))[:90]))

print("\ndone, %d stalls captured" % seen)

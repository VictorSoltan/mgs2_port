# Samples the running game: per-thread CPU, GPU load and clock, temperatures,
# the CPU frequency cap the thermal guard has settled on, and memory.
# Read-only; no logging inside the game's own threads.
import glob, time, sys

def game_pid():
    for p in glob.glob("/proc/[0-9]*"):
        try:
            if open(p + "/comm").read().strip() == "mgs2_sse_rg353v":
                return p.split("/")[-1]
        except OSError:
            pass

def read(path, default="?"):
    try:
        return open(path).read().strip()
    except OSError:
        return default

def threads(pid):
    out = {}
    for t in glob.glob("/proc/%s/task/*" % pid):
        try:
            s = open(t + "/stat").read()
            n = open(t + "/comm").read().strip()
        except OSError:
            continue
        f = s[s.rfind(")") + 2:].split()
        out[t.split("/")[-1]] = (n, int(f[11]) + int(f[12]))
    return out

pid = game_pid()
if not pid:
    print("game not running"); sys.exit(1)
dur = int(sys.argv[1]) if len(sys.argv) > 1 else 90
step = 10
print("pid=%s sampling %ds in %ds windows" % (pid, dur, step))
print("%5s %6s %6s %6s %8s %9s" % ("t", "cpuC", "gpuC", "gpuMHz", "cpu_cap", "mem_avail"))
prev = threads(pid)
acc = {}
for i in range(dur // step):
    time.sleep(step)
    cur = threads(pid)
    for k in cur:
        if k in prev:
            name, d = cur[k][0], cur[k][1] - prev[k][1]
            acc[name] = acc.get(name, 0) + d
    prev = cur
    print("%5d %6.1f %6.1f %6d %8s %9s" % (
        (i + 1) * step,
        int(read("/sys/class/thermal/thermal_zone0/temp", "0")) / 1000.0,
        int(read("/sys/class/thermal/thermal_zone1/temp", "0")) / 1000.0,
        int(read("/sys/class/devfreq/fde60000.gpu/cur_freq", "0")) // 1000000,
        read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq"),
        read("/proc/meminfo").split("MemAvailable:")[1].split()[0] if "MemAvailable" in read("/proc/meminfo") else "?"))
print("--- CPU by thread name, total ticks over %ds (100 ticks = 1 core-second):" % dur)
for name, d in sorted(acc.items(), key=lambda x: -x[1])[:10]:
    if d:
        print("  %7d  %5.0f%% of one core  %s" % (d, d * 100.0 / (dur * 100), name))
print("  sum %d ticks = %.0f%% of the 4-core machine" % (
    sum(acc.values()), sum(acc.values()) * 100.0 / (dur * 400)))

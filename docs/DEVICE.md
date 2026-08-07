# Working with the console

Practical manual for the RG353VS side of this project: how to launch, measure,
verify and stop without leaving the device in a bad state. Everything here was
learned by getting it wrong at least once.

## Access

```sh
ssh root@192.168.0.28
# ROCKNIX ships with the password "rocknix"
```

The game lives in `/storage/roms/ports/MGS2-Substance/`, the menu entry is
`/storage/roms/ports/MGS2-Substance.sh`. `/storage` is the SD card, and `/` is a
read-only squashfs that is 100% full — that difference matters, see "Saves" below.

Every backup this project made is next to the file it backs up, named
`.bak-<date>-<reason>`. Keep that habit.

## Launching

From the menu on the device, or over ssh:

```sh
cd /storage/roms/ports
XDG_RUNTIME_DIR=/var/run/0-runtime-dir WAYLAND_DISPLAY=wayland-1 \
    setsid nohup ./MGS2-Substance.sh > /tmp/run.log 2>&1 < /dev/null &
```

`setsid nohup` matters: **the game outlives the ssh session**. Closing the
terminal does not stop it, and starting a second copy is the single easiest way
to produce "the console is suddenly terrible" — two instances read exactly like
lag.

First frame appears around 45-60 seconds in. Write logs to `/tmp`, which is
tmpfs; writing them to `/storage` puts diagnostic I/O on the same SD card the
game streams from.

## Stopping, properly

```sh
killall -9 launch.sh wine wine-preloader box86 box64 gptokeyb wineserver
sleep 3
rm -f /tmp/mgs2-substance.lock
for m in /usr/lib/wine/i386-windows/{wined3d,user32,d3d8,dmsynth,dsound,dmime,dmusic}.dll \
         /usr/lib/wine/i386-unix/{winewayland,win32u,opengl32,ntdll}.so /usr/bin/box86; do
    while grep -q " $m " /proc/mounts; do umount "$m" || break; done
done
```

Two traps in that block:

- The launcher **bind-mounts** its DLL choices over Wine's. A hard kill skips the
  launcher's own cleanup, so the mounts stay and the next run inherits whatever
  was mounted last. Always unwind them, and loop: they can stack.
- `launch.sh` restores the CPU governor and frequency cap on exit through a trap,
  which `kill -9` also skips. After a hard kill, check and restore:

```sh
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq   # expect 1992000
for p in /sys/devices/system/cpu/cpufreq/policy*; do echo 1992000 > $p/scaling_max_freq; done
```

## Verifying what is actually running

Never trust the filename you passed. Compare the mount target byte for byte:

```sh
G=/storage/roms/ports/MGS2-Substance
cmp -s /usr/lib/wine/i386-windows/wined3d.dll $G/wined3d_release3.dll && echo ok
cmp -s /usr/lib/wine/i386-unix/winewayland.so $G/winewayland_stall1.so && echo ok
```

And confirm exactly one instance, matching on the exact `comm` (it is truncated
to 15 characters, so `pgrep` patterns can mislead):

```sh
c=0; for p in /proc/[0-9]*; do
    [ "$(cat $p/comm 2>/dev/null)" = "mgs2_sse_rg353v" ] && c=$((c+1)); done; echo $c
```

## Choosing what to load, without rebuilding

```text
MGS2_WINED3D_DLL   MGS2_D3D8_DLL   MGS2_DMIME_DLL   MGS2_DMSYNTH_DLL
MGS2_DSOUND_DLL    MGS2_WAYLAND_SO  MGS2_OPENGL32_SO MGS2_WIN32U_SO
MGS2_NTDLL_SO      MGS2_USER32_DLL
```

Each names a file in the game directory; the launcher bind-mounts it over the
Wine module of that name and unmounts it on exit. This is how every A/B in this
project was done — no rebuild, no reinstall.

## Measuring

```text
MGS2_TRIAGE=1            everything at once: frame-time histogram, shader
                         compile/link times, d3d8 draw and state counters.
                         One line per second or per 300 frames, never per call.
MGS2_GL_STATS=N          fps and frame breakdown every N frames
MGS2_GL_READ_SPLIT=1     glFinish timed apart from glReadPixels (diagnostic only)
MGS2_FREQ_STEPS="1416000"  pin the clock so an A/B compares variants, not heat
```

Harness scripts, all read-only against the game:

```text
harness/perf_sample.py <seconds>     per-thread CPU, temperatures, GPU clock, cap
harness/stall_watch2.py <log> <sec>  what threads were doing during a freeze
harness/sink_audible_test.sh         is anything audible, judged by capture not ears
```

Read the caveat in brief #28 before using `stall_watch2.py`: it reads `wchan` for
every thread ten times a second, which unwinds kernel stacks and measurably
amplifies the stalls it is there to catch.

## Judging a change

- Same spot in the game, both runs. Scene variation inside a single run spans 22
  to 60 fps and will swamp anything you are trying to see.
- Pin the clock on both runs.
- 300-600 frames per sample, and look at the histogram of frames over
  50/100/200/500 ms, not only the mean. A ten-second stall is invisible in a mean.
- The owner judges picture and feel; the harness judges numbers. Ask separately
  about music, menu clicks and gameplay SFX — they are three different systems.
- Say up front when a run drives itself, and never drive the game automatically
  while the owner is watching: it looks like someone else is playing.

## Thermals

```text
guard: cap steps down at 84 C, back up at 76 C, hard stop at 88 C
hardware trip points observed around 83, 88 and 95 C; the console has reset
ladder: 1992 / 1800 / 1608 / 1416 kHz-steps, top step is the overclocked maximum
```

The cap moves during play. Any measurement that ignores it is measuring
temperature. On the charger the cap has been seen sitting at 1104 MHz for a whole
session — roughly half the available CPU — so note charger state in every result.

## Saves

The game asks its own drive how many free blocks it has. It runs from `/storage`,
but the only drive covering that path used to be `Z: -> /`, a read-only squashfs
that is 100% full, so the answer was zero and saving was impossible. `launch.sh`
now creates `D: -> /storage` in the prefix on every start. If saving ever breaks
again, check that symlink first:

```sh
ls -la /storage/roms/ports/MGS2-Substance/wineprefix64/dosdevices/
```

## Sound

Three DLLs are required together and each for a separately measured reason; the
launcher defaults to them. If sound regresses, the fastest bisect is
`MGS2_DMIME_SHAREDGROUPS=0` (back to one port per audio path — expect stutter but
audible SFX) before touching the DLL choices. SE rides DirectMusic channel group
2, so `MGS2_DMIME_SHAREDGROUP_COUNT` must stay above 2.

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

  1992000 is the correct value even though `scaling_available_frequencies` stops
  at 1800000. That list omits the top OPP; `cpuinfo_max_freq` reports 1992000 and
  the write above takes (verified on OS_VERSION 20260722, 2026-08-12). Do not
  conclude from the shorter list that the fixed-clock baseline of the performance
  briefs is unreachable — it is. There is one shared policy, `policy0`, for all
  four A55 cores, so the loop writes a single file.

## Verifying what is actually running

Never trust the filename you passed. Compare the mount target byte for byte:

```sh
G=/storage/roms/ports/MGS2-Substance
cmp -s /usr/lib/wine/i386-windows/wined3d.dll $G/wined3d_p32_ffp_source_dedup.dll && echo ok
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

FINALPLAY4 production defaults are `box86-native-dsound-fir1`,
`dsound_p36_native_fir_target.dll`, `dmsynth_p34_interp_reset.dll`, and
`MGS2_BOX86_NATIVE_DSOUND_FIR=1`. The native FIR switch is valid only with that
exact Box86/dsound pair. Set it to `0`, or select the previous FINALPLAY3
`box86-native-memmove3` + `dsound_se1.dll` pair, for rollback.

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
harness/box86_guest_snapshot.py      external snapshot of Box86's bounded JIT map
harness/box86_guest_profile.py       resolve an external perf trace using that map
harness/freeze_capture.py --out DIR  one-shot capture AT a freeze, before killing
harness/freeze_watchdog.sh           unattended: detects a freeze and captures it
harness/autoload_save.sh [DIR]       cold start -> loaded save, no hands
harness/stall_watch2.py <log> <sec>  what threads were doing during a freeze
harness/sink_audible_test.sh         is anything audible, judged by capture not ears
```

## Profiling a reported reinforcements slowdown

Use production files plus only `MGS2_BOX86_GUEST_MAP=1`: it records bounded JIT
block mappings in memory and makes no per-frame or per-draw output.  Once the
player says reinforcements are entering, take one short external `perf` interval
and snapshot the map immediately afterwards.  Do not enable `MGS2_TRACE`, batch
profiles, or hot Wine debug output together with this run; those have changed the
very frame bands being investigated.

The 14 August valid capture had one process, fixed 1992 MHz and 82.777 C, yet
showed 18.3--19.5 fps and later 11.9--14.8 fps.  It is the reference control for
any future combat change; details and the exact external-reader interpretation
are in `MGS2_REINFORCEMENT_ARM_TARGET_2026-08-14.md`.

## Getting into real gameplay without hands

The attract-mode demo is **not** a valid stand-in for gameplay, and both halves of
that matter. It is frame-capped at 60, so an fps A/B inside it measures nothing:
dropping the clock from 1992 to 1416 MHz left the average at 58.9 against 58.83.
And the permanent freeze does not occur there — 8.4 hours on 2026-08-13 produced
none.

```sh
./MGS2-Substance/autoload_save.sh /tmp/autoload
```

Cold start to a loaded save, writing a screenshot after every step so a wrong key
is visible rather than mysterious. Gameplay walking now defaults to `down` and
can be changed with `MGS2_WALK_KEY`. The old `up` route held Raiden against the
upper closed door and never exposed the first guard. Its earlier 26.3 fps / six
frames-over-500-ms result therefore describes a loaded but transition-free wall
route and must not qualify enemy or map hitches. Use the corrected route, not the
demo or that old number, for anything about gameplay stalls.

Two things it cost to learn, both now encoded in the script:

- **START does not advance the title screen.** `mgs2.gptk` maps `start=tab`, but
  the game only reacts to the A button, which the same profile maps to `z`.
- **One uinput device per keypress loses keys.** Creating and destroying the
  device around each step dropped roughly every other event, which shifted the
  whole route and confirmed NEW GAME twice, landing on the difficulty screen.
  `autoload_save.py` creates the device once and times the steps inside its
  lifetime; `send_key.py` remains correct for single keys.

For a rare freeze, arm the watchdog instead of watching by hand and leave the game
running:

```sh
setsid nohup ./MGS2-Substance/freeze_watchdog.sh 20 200 /tmp/auto-freeze \
    /tmp/watchdog.log >/dev/null 2>&1 </dev/null &
```

It sums utime+stime over every thread each 20 s and fires after two consecutive
windows below 200 ticks, then captures and exits, leaving the game frozen. The
thresholds are calibrated, not guessed: normal running measured 4329 ticks per
20 s on 2026-08-12, and the captured freeze left about 26. A recoverable
multi-second stall cannot span two windows, so this only catches the permanent
kind. It never kills anything.

At a freeze, run `freeze_capture.py` first and kill the game only afterwards. It
samples each thread exactly twice and reads nothing else, so it does not amplify
the freeze the way the `stall_watch*` scripts do. It answers, in one pass, whether
any thread is running, which threads stopped moving, whether their waits carry a
timeout, whether the futex word can still be signalled, and what is mounted. Read
its caveat: an untimed wait on an unchanged word is normal for an idle worker, so
what matters is whether the *high-utime* threads stopped. That distinction is what
produced the 2026-08-12 diagnosis.

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

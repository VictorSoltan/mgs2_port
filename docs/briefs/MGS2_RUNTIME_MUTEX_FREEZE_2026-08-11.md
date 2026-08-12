# MGS2 RG353VS — Box86 mutex freeze capture and fix (2026-08-11)

This brief covers the complete no-render/input freeze captured from the live
production process on 11 August. It is a different failure from the earlier
stock-`user32` `PeekMessage` spin in
`MGS2_RUNTIME_BUG_CAPTURE_2026-08-09.md`.

## 1. What the device proved

There was exactly one game instance: launcher PID 8575, game PID 8704 and
`gptokeyb` PID 8703. The mounted production Box86, Wine modules and renderer
DLLs matched their repository artifacts byte for byte. CPU was still capped at
1992 MHz, temperature was about 70 C during the capture, and the kernel had no
OOM, GPU reset or thermal fault.

The game main thread, `wined3d_cs`, and `wine_dinput_worker` were all in a
native futex wait on the same host mutex at `0x64446778`. The mutex owner field
was TID 9377, which was the same `wine_dinput_worker` already waiting on it:
the owner had become a self-waiter, so no remaining thread could release the
lock.

Box86 guest register and stack recovery resolved all three calls through the
bridge at `0x4006008b` to guest mutex `0x60426284`. Its return address
`0x6033b97a` resolves to Wine 11 `win32u/winstation.c`, the
`pthread_mutex_lock(&session_lock)` in `find_shared_session_block()`. The input
worker's deeper guest stack was:

```text
find_shared_session_object
get_shared_window
DPI coordinate mapping
process_rawinput_message
process_hardware_message / PeekMessage path
```

There was no second `find_shared_session_block()` in 16 KiB of its guest stack,
so this was not recursive Wine acquisition visible in the caller.

As a one-time causality test, GDB was attached to the recorded owner TID and
called `pthread_mutex_unlock()` on `0x64446778`. It returned zero. Immediately:

* the main thread left that futex;
* `wined3d_cs` returned to its normal command-stream wait;
* `wine_dinput_worker` returned to its normal ntsync wait;
* the mutex owner bytes cleared and the game resumed rendering and input.

This rules out the renderer, controller, SD card, shader compilation and
thermal throttling as the cause of this occurrence. The complete, cold-read
artifacts are under:

```text
logs/live-20260811/freeze-session-lock/
  mgs2-freeze-20260811.perf
  mgs2-freeze-20260811.maps
  mgs2-freeze-20260811.gdb.txt
  mgs2-freeze-20260811.guest.txt
  mgs2-freeze-20260811-unlock.txt
```

## 2. Root cause in Box86

The production Box86 is based on upstream commit
`0579f8b9c47d87d700724f4cce559b06cbd2b0f5`. On ARM, Box86 represents an
unaligned x86 `pthread_mutex_t` with an `aligned_mutex_t` marker pointing to a
native mutex from a process-wide pool.

The old `getAlignedMutexWithInit()` implementation did this on first use:

```text
thread A                         thread B
NewMutex(): allocate slot A
global allocator lock released
                                 NewMutex(): allocate slot B
                                 global allocator lock released
publish slot A into guest mutex
                                 publish slot B into guest mutex
```

Pool allocation was serialized, but publication to the shared guest mutex was
not. Two simultaneous first users could therefore lock different native
mutexes while the final published mapping named only one of them. A later
unlock followed the overwritten mapping, leaving the other native mutex owned
forever. The old code also wrote its recognition signature before the native
pointer, which is not a safe publication order on weakly ordered ARM.

Wine's static `session_lock` is ordinary and still has the same lock/use/unlock
shape in current upstream Wine. Patching Wine around it would hide one caller
of the bridge bug while leaving every other first-use mutex exposed.

## 3. Small fix

`box86-patches/03-aligned-mutex-publication.patch` makes allocation plus guest
mapping publication one critical section:

1. acquire-load the signature for the fast path;
2. take Box86's existing global mutex-pool lock;
3. repeat the initialized check;
4. allocate one pool entry and fill `k`, `m`, and `self` while still locked;
5. release-store the signature last, then release the pool lock.

This neither removes a Wine lock nor changes its semantics. It changes only
Box86's one-time mapping of that lock to its ARM backing object. The memmove
optimization from performance brief #43 is unchanged.

```text
patch   box86-patches/03-aligned-mutex-publication.patch
sha256  1c270d2784059320cfebf4ac30b537a9d1745beccf0c24b9b11a20f0fbc942e2
binary  binaries/box86-native-memmove3
sha256  35da697774f627cd0d4272328aa21ae094620d683458b1d0b35fd8e8b0a6e98c
```

All three Box86 patches apply with `-F0`; the resulting `threads.c` was compared
byte for byte with the source used for the binary.

## 4. Direct A/B test

`harness/box86_mutex_first_use_stress.c` is a freestanding i386 test. Four
threads are released together onto a new zero-initialized mutex in every round.
An overlap, pthread error, incomplete round, or timeout is failure. It targets
the exact first-use race instead of waiting for a rare game transition.

The same 1,000-round i386 executable was run on the RG353VS:

```text
old production Box86     FAIL, rc=1, elapsed 1 s
fixed Box86              PASS in 10/10 independent runs
fixed total              10,000 new mutex mappings
```

It can be rebuilt on a host with GCC multilib without an i386 libc development
package. The stub supplies link-time symbols only; Box86 substitutes its native
wrapped `libpthread` on the device:

```sh
mkdir -p /tmp/mgs2-mutex-stress-build
gcc -m32 -nostdlib -fPIC -shared \
  -Wl,-soname,libpthread.so.0 \
  -o /tmp/mgs2-mutex-stress-build/libpthread.so \
  harness/box86_pthread_link_stub.c
gcc -m32 -O2 -nostdlib -fno-pie -no-pie -fno-stack-protector \
  -DROUNDS=1000 -Wl,-e,_start -Wl,--no-as-needed \
  -L/tmp/mgs2-mutex-stress-build \
  -o /tmp/mgs2-mutex-stress-build/box86_mutex_first_use_stress \
  harness/box86_mutex_first_use_stress.c -lpthread
```

A separate hot-mutex test of 10 million lock/unlock pairs gave these device
wall times:

```text
old    1.92 / 2.08 / 2.02 s
fixed  2.16 / 2.23 / 2.09 s
```

That synthetic delta is roughly 13–16 ns per hot lock/unlock pair. It is not a
game FPS measurement and is recorded only as the upper-bound micro-cost seen by
this test.

## 5. Production deployment and boundary of the claim

`device/launch-play.sh` now selects `box86-native-memmove3`; all Wine, D3D8,
WineD3D, presentation and audio choices remain unchanged. After a graceful
stop of the recovered old process, the new production launch had one game
instance, rendered the title screen, and byte checks matched the new Box86 and
all eleven unchanged Wine/D3D/audio mount targets. A six-minute live smoke kept
one instance; `wine_dinput_worker` was in its normal ntsync wait rather than the
captured shared futex deadlock. The device had heated to 83.333 C and its active
CPU cap had fallen to 1608 MHz by the end, so this title-screen smoke is not
presented as a new fixed-spot FPS qualification. The existing 30.0/30.0/30.1
measurement remains the unchanged renderer/memmove qualification from brief
#43; the lock-only micro-cost is reported separately above.

The instrumented smoke process was then stopped normally and replaced with the
actual menu configuration. The process left for play had `MGS2_GL_STATS=0`,
one game instance, the expected Box86 dynarec settings and native memmove path,
the exact `box86-native-memmove3` SHA, a non-empty rendered frame, and the input
worker in its normal ntsync wait.

No finite soak can prove that the game will never freeze for any other reason.
The precise captured failure mechanism, however, is removed and its old/new
A/B is deterministic. If an unrelated future stall occurs, capture its owner
and wait address before attributing it to this incident. Rollback is one
launcher line to `box86-native-memmove2`; it is retained in `binaries/`, but the
direct stress test is the reason not to roll this fix back.

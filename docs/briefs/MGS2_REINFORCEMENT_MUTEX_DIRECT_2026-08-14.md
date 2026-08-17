# MGS2 RG353VS — reinforcement result and direct Box86 mutex path (2026-08-14)

This brief records the complete 14 August follow-up after the manual reinforcement run: the renderer decision, the live complete freeze, its non-destructive recovery, and the production reliability change that followed. It deliberately separates the freeze fix from FPS: the latter was measured and did **not** improve from this change.

## 1. Result

| item | result |
|---|---|
| Indexed reinforcement batch | rejected: exact dense manual capture had `source_indexed = 0` |
| Complete freeze | captured as a self-owned native mutex, not a GPU / thermal / audio failure |
| Recovery | the live game resumed after one debugger `pthread_mutex_unlock()` on the captured mutex; no restart or rollback was used for the capture |
| Persistent change | production launcher now selects upstream Box86 `BOX86_MUTEX_ALIGNED=1`, bypassing its shadow native-mutex pool |
| Pixels, shaders, game logic, audio policy, libmali | unchanged |
| Direct-path reinforcement FPS | 300 displayed frames / 19.714 s = **15.22 fps**; not a performance win |

## 2. Dense manual reinforcement census

The first live manual run used p37's bounded, memory-only WineD3D submission census, paired with the diagnostic p35 native-AABB candidate (`MGS2_BOX86_NATIVE_AABB=1`). It was a normal dense reinforcement fight, with one game process and a 1992 MHz CPU cap. The accounting interval was uptime `5911.72` through `5933.45` seconds.

The five complete 60-frame presenter windows were 18.4, 18.8, 16.8, 13.6 and 16.5 fps. Combined: 300 frames / 18.070 s = **16.60 fps**. This is a scene measurement, not an A/B against another location. The AABB candidate was active in this capture but appeared in only 0.53% of all perf samples; it is not claimed as an FPS improvement and is off in production.

Artifacts:

```text
logs/rg353vs/manual-reinforcement-freeze-20260814/
  manual-reinforcement-before.json
  manual-reinforcement-after.json
  manual-reinforcement-diff.json
```

Exact p37 delta:

```text
CS Present commands       340
source draws          323788
source indexed             0
source non-indexed    323788
source batch packets   87137
final GL draws         85966
  glDrawArrays         34769
  synthetic EBO        51197
```

WineD3D emits two CS Present commands per displayed frame on this route. The interval is therefore about 1,905 source draws and 506 final GL submissions per displayed frame. The existing non-indexed strip batcher removes about 73% of source submissions, but the proposed `DrawIndexedPrimitive` merger would remove **zero**: there were no indexed source draws. This closes the candidate for the actual dense manual scene, not merely the automatic ALERT route.

The diagnostic build is `binaries/wined3d_p37_reinforcement_census.dll`. `device/launch-play.sh` was corrected to use `${MGS2_WINED3D_DLL:-wined3d_p32_ffp_source_dedup.dll}`, so the documented p37 override really selects the diagnostic DLL. Normal production remains p32.

## 3. Complete freeze: proven boundary

The same live process, PID 52726, subsequently stopped rendering and accepting input. It was deliberately left alive while evidence was collected.

The game main thread, `wined3d_cs`, and `wine_dinput_worker` were all blocked on the same untimed private futex at native address `0x63c7a898`. The native glibc mutex had:

```text
lock   = 2
owner  = 53492
kind   = 0
nusers = 1
```

TID 53492 was `wine_dinput_worker`, and that same thread was waiting on this mutex. No thread capable of releasing it remained. Box86 guest-register and stack recovery resolved every waiter to guest mutex `0x60426284`, return address `0x6033b97a`, and Wine 11's `win32u/winstation.c:find_shared_session_block()`:

```c
pthread_mutex_lock( &session_lock );
```

This has the same guest lock and input/renderer/main waiter shape as the 11 August capture, but the published `03-aligned-mutex-publication.patch` binary was already mounted. The guest marker was complete and stable:

```text
self = 0x60426284, k = 4, native m = 0x63c7a898, sign = "MUTX"
```

A process-memory scan found exactly one live marker for that native mutex and the pool slot was still marked taken. This is not evidence that the old first-publication race simply recurred. The precise cause before the first acquisition was not caught; the unsafe end state of the shadow native-mutex layer is proven.

The one-time recovery selected the owner thread in GDB and called `pthread_mutex_unlock((pthread_mutex_t *)0x63c7a898)`. It returned zero. Immediately afterward the mutex bytes were zero, the main and renderer threads became runnable, and `wine_dinput_worker` returned to normal `ntsync` waiting. No game file changed and the game continued from the same session.

Cold artifacts, including two futex slices, guest stacks, marker bytes, pool state and recovery result:

```text
logs/rg353vs/manual-reinforcement-freeze-20260814/
```

## 4. Production mutex path

Box86 upstream supports:

```text
BOX86_MUTEX_ALIGNED=1
```

This uses the guest mutex directly instead of replacing it with an `aligned_mutex_t` marker and native pool entry. Before enabling it, the actual ARM libc and i386 Wine definitions were inspected. Both `pthread_mutex_t` values are 24 bytes, 4-byte aligned, with identical offsets:

```text
0 lock, 4 count, 8 owner, 12 kind, 16 nusers, 20 spin/list
```

The production launcher now contains:

```sh
export BOX86_MUTEX_ALIGNED="${BOX86_MUTEX_ALIGNED:-1}"
```

It bypasses the captured shadow pool without changing Wine lock calls, game code, renderer policy, textures, shader sources, resolution, audio path or `libmali`. `BOX86_MUTEX_ALIGNED=0` is the one-variable rollback diagnostic.

The direct-path production launch was verified as:

```text
BOX86_MUTEX_ALIGNED=1
MGS2_BOX86_NATIVE_AABB=0
MGS2_BOX86_NATIVE_DSOUND_FIR=1
MGS2_GL_STATS=60                 # only for this measurement launch
/usr/bin/box86                   89ca26c512489ed18b3605ca195fa7dd45d3a9f8cc3fefafac8b1ebd9b86a252
libmali                           active
one game process                  PID 13442
```

`MGS2_GL_STATS=60` was temporary measurement telemetry; the launcher's normal default remains zero.

Two freestanding sources were prepared but are deliberately not production:

```text
harness/box86_mutex_signal_stress.c
harness/box86_signal_link_stub.c
```

They aim to stress guest signal delivery around mutex calls. The user stopped synthetic testing before a valid result was obtained. They are unvalidated diagnostic material, not evidence for the direct-path decision.

## 5. Direct-path reinforcement FPS

After the direct-path restart, the player again reported reinforcements entering. The five first complete reporter windows after that marker were:

```text
60 / 4347 ms = 13.8 fps
60 / 3785 ms = 15.9 fps
60 / 4142 ms = 14.5 fps
60 / 3804 ms = 15.8 fps
60 / 3636 ms = 16.5 fps
```

Summing time instead of averaging rounded rates gives:

```text
300 frames / 19714 ms = 15.22 fps
```

The CPU cap was 1992000 kHz and CPU temperature 82.222 C. This is inside the known 11.9--19.5 fps reinforcement range and does **not** show an FPS win from the mutex change. It is a reliability change only.

The launch log and local artifact hashes are retained at:

```text
logs/rg353vs/mutex-direct-reinforcement-20260814/
  mgs2-fps-reinforcement.log
  sha256-local.txt
```

## 6. Decision

Keep the direct mutex path as the production reliability candidate and soak it through normal play. A future freeze requires a new owner/wait capture; it must not be assumed to be any prior mechanism.

Do not build the indexed reinforcement merger: the measured target contains no indexed draws. The remaining dense-fight cost is divided between game work, translated WineD3D, and native `libmali`; the existing non-indexed batcher already removes most source submissions. There is no measured renderer patch that can honestly be promised to raise this fight to 30 fps without changing prohibited constraints.

The independent work remains unchanged: bounded same-context prewarm of exact known FFP sources is the candidate for first-use map/enemy hitches; one missing player attack must be captured through persistent DirectSound buffer and PCM before changing audio code.

## External source

`BOX86_MUTEX_ALIGNED` is documented by the exact upstream line used by this port: [Box86 usage documentation](https://github.com/ptitSeb/box86/blob/0579f8b9c47d87d700724f4cce559b06cbd2b0f5/docs/USAGE.md).

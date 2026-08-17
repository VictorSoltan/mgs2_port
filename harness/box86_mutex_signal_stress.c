/*
 * Stress Box86's pthread mutex bridge while guest signal delivery repeatedly
 * interrupts the locking threads.  This is aimed at a rarer failure than the
 * first-use publication race: a native normal mutex was captured owned by the
 * same Wine input thread that was blocked trying to lock it, while only one
 * guest acquisition was present on that thread's stack.
 *
 * The executable is deliberately freestanding.  Build it against the link-only
 * libc/libpthread stubs in this directory, then run it through the exact Box86
 * under an external timeout.  A timeout, pthread error, missing signal delivery,
 * or incomplete critical-section count is failure.
 */

#ifndef WORKERS
#define WORKERS 4
#endif
#ifndef ITERATIONS
#define ITERATIONS 2000000
#endif
#ifndef SIGNALS
#define SIGNALS 200000
#endif

#define SIGUSR1 10

typedef unsigned long pthread_t;
typedef union
{
    char bytes[24];
    long align;
} pthread_mutex_t;

extern int pthread_create(pthread_t *, const void *, void *(*)(void *), void *);
extern int pthread_join(pthread_t, void **);
extern int pthread_kill(pthread_t, int);
extern int pthread_mutex_lock(pthread_mutex_t *);
extern int pthread_mutex_unlock(pthread_mutex_t *);
extern void (*signal(int, void (*)(int)))(int);

static pthread_mutex_t target;
static pthread_t workers[WORKERS];
static volatile unsigned int start;
static volatile unsigned int ready;
static volatile unsigned int critical_count;
static volatile unsigned int failures;
static volatile unsigned int handled;

static void sys_yield(void)
{
    unsigned int syscall_number = 158;

    __asm__ volatile("int $0x80" : "+a"(syscall_number) : : "memory", "cc");
}

__attribute__((noreturn)) static void sys_exit(unsigned int status)
{
    __asm__ volatile("int $0x80" : : "a"(1), "b"(status) : "memory", "cc");
    __builtin_unreachable();
}

static void sys_write(const char *text, unsigned int length)
{
    unsigned int syscall_number = 4;

    __asm__ volatile("int $0x80" : "+a"(syscall_number)
            : "b"(1), "c"(text), "d"(length) : "memory", "cc");
}

static void on_signal(int sig)
{
    (void)sig;
    __atomic_add_fetch(&handled, 1, __ATOMIC_RELAXED);
}

static void spin_until(volatile unsigned int *value, unsigned int expected)
{
    unsigned int spins = 0;

    while (__atomic_load_n(value, __ATOMIC_ACQUIRE) != expected)
        if (!(++spins & 0xfff)) sys_yield();
}

static void *worker(void *arg)
{
    unsigned int i;

    (void)arg;
    __atomic_add_fetch(&ready, 1, __ATOMIC_ACQ_REL);
    spin_until(&start, 1);

    for (i = 0; i < ITERATIONS; ++i)
    {
        if (pthread_mutex_lock(&target))
            __atomic_add_fetch(&failures, 1, __ATOMIC_RELAXED);
        ++critical_count;
        if (pthread_mutex_unlock(&target))
            __atomic_add_fetch(&failures, 1, __ATOMIC_RELAXED);
    }
    return 0;
}

static unsigned int run(void)
{
    unsigned int i;

    if (signal(SIGUSR1, on_signal) == (void *)-1) return 2;
    for (i = 0; i < WORKERS; ++i)
        if (pthread_create(&workers[i], 0, worker, 0)) return 3;

    spin_until(&ready, WORKERS);
    __atomic_store_n(&start, 1, __ATOMIC_RELEASE);
    for (i = 0; i < SIGNALS; ++i)
    {
        if (pthread_kill(workers[i % WORKERS], SIGUSR1))
            __atomic_add_fetch(&failures, 1, __ATOMIC_RELAXED);
        if (!(i & 0x3f)) sys_yield();
    }

    for (i = 0; i < WORKERS; ++i) pthread_join(workers[i], 0);

    if (critical_count != WORKERS * ITERATIONS) return 4;
    if (!handled || failures) return 5;
    return 0;
}

__attribute__((noreturn)) void _start(void)
{
    unsigned int status = run();

    if (status) sys_write("FAIL\n", 5);
    else sys_write("PASS\n", 5);
    sys_exit(status);
}

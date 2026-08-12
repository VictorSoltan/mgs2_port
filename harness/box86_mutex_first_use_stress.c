/*
 * Exercise Box86's first-use mapping of an x86 pthread_mutex_t to its native
 * ARM pthread_mutex_t.  Each round presents a different zero-initialised
 * mutex to all workers at once.  A correct bridge admits exactly one worker
 * into the critical section and all workers complete the round.
 *
 * This is deliberately freestanding so it can be linked without a local i386
 * libc development package.  Link it against a throw-away libpthread import
 * stub; Box86 substitutes its wrapped native libpthread at run time.
 *
 * Run on the ARM device through Box86 and bound it with timeout.  A timeout,
 * non-zero overlap count, or incomplete round refutes the implementation.
 */

#ifndef WORKERS
#define WORKERS 4
#endif
#ifndef ROUNDS
#define ROUNDS 20000
#endif

typedef unsigned long pthread_t;
typedef union
{
    char bytes[24];
    long align;
} pthread_mutex_t;

extern int pthread_create(pthread_t *, const void *, void *(*)(void *), void *);
extern int pthread_join(pthread_t, void **);
extern int pthread_mutex_lock(pthread_mutex_t *);
extern int pthread_mutex_unlock(pthread_mutex_t *);

static pthread_mutex_t targets[ROUNDS];
static pthread_t workers[WORKERS];
static volatile unsigned int round_id;
static volatile unsigned int ready;
static volatile unsigned int start_id;
static volatile unsigned int done;
static volatile unsigned int departed;
static volatile unsigned int inside;
static volatile unsigned int overlaps;
static volatile unsigned int failures;

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

static void spin_until(volatile unsigned int *value, unsigned int expected)
{
    unsigned int spins = 0;

    while (__atomic_load_n(value, __ATOMIC_ACQUIRE) != expected)
    {
        if (!(++spins & 0xfff)) sys_yield();
    }
}

static void *worker(void *arg)
{
    unsigned int round;

    (void)arg;
    for (round = 1; round <= ROUNDS; ++round)
    {
        spin_until(&round_id, round);
        __atomic_add_fetch(&ready, 1, __ATOMIC_ACQ_REL);
        spin_until(&start_id, round);

        if (pthread_mutex_lock(&targets[round - 1]))
            __atomic_add_fetch(&failures, 1, __ATOMIC_RELAXED);
        if (__atomic_add_fetch(&inside, 1, __ATOMIC_ACQ_REL) != 1)
            __atomic_add_fetch(&overlaps, 1, __ATOMIC_RELAXED);
        sys_yield();
        __atomic_sub_fetch(&inside, 1, __ATOMIC_ACQ_REL);
        if (pthread_mutex_unlock(&targets[round - 1]))
            __atomic_add_fetch(&failures, 1, __ATOMIC_RELAXED);

        __atomic_add_fetch(&done, 1, __ATOMIC_ACQ_REL);
        spin_until(&round_id, 0);
        __atomic_add_fetch(&departed, 1, __ATOMIC_ACQ_REL);
    }
    return 0;
}

static unsigned int run(void)
{
    unsigned int i, round;

    for (i = 0; i < WORKERS; ++i)
        if (pthread_create(&workers[i], 0, worker, 0)) return 2;

    for (round = 1; round <= ROUNDS; ++round)
    {
        __atomic_store_n(&ready, 0, __ATOMIC_RELEASE);
        __atomic_store_n(&done, 0, __ATOMIC_RELEASE);
        __atomic_store_n(&departed, 0, __ATOMIC_RELEASE);
        __atomic_store_n(&round_id, round, __ATOMIC_RELEASE);
        spin_until(&ready, WORKERS);
        __atomic_store_n(&start_id, round, __ATOMIC_RELEASE);
        spin_until(&done, WORKERS);
        __atomic_store_n(&round_id, 0, __ATOMIC_RELEASE);
        spin_until(&departed, WORKERS);
    }

    for (i = 0; i < WORKERS; ++i) pthread_join(workers[i], 0);

    return overlaps != 0 || inside != 0 || failures != 0;
}

__attribute__((noreturn)) void _start(void)
{
    unsigned int status = run();

    if (status) sys_write("FAIL\n", 5);
    else sys_write("PASS\n", 5);
    sys_exit(status);
}

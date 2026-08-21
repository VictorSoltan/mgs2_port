/* Generated island bridge wrappers.
 *
 * Entries 21 (wined3d_release_dc) and 30 (wined3d_swapchain_set_window) are
 * deliberately absent. They are window and device-context code, which section
 * 13.6 of the reinforcement frame-budget brief put on the x86 side, and the cut
 * analysis routed them anyway; entry 21 is what aborted on WindowFromDC on the
 * device. Neither appears in the calls/frame table, so dropping them costs
 * nothing. Their markers stay in the guest DLL and simply never match.
 */
/* Generated island bridge wrappers. One per distinct signature; arguments are
 * cdecl, read from the guest stack. Do not hand-edit -- regenerate with the
 * table in harness/island/full/. */
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include "debug.h"
#include "wrapper.h"
#include "x86emu.h"
#include "callback.h"
#include "emu/x86emu_private.h"
#include "bridge.h"

static void mgs2_island_w_iFpi(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    int32_t r = ((int32_t (*)(void *, int32_t))fnc)(*(void * *)(esp + 4), *(int32_t *)(esp + 8));
    SetEAX(emu, (uint32_t)(uintptr_t)r);
}

static void mgs2_island_w_iFppuppupupi(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    int32_t r = ((int32_t (*)(void *, void *, uint32_t, void *, void *, uint32_t, void *, uint32_t, void *, int32_t))fnc)(*(void * *)(esp + 4), *(void * *)(esp + 8), *(uint32_t *)(esp + 12), *(void * *)(esp + 16), *(void * *)(esp + 20), *(uint32_t *)(esp + 24), *(void * *)(esp + 28), *(uint32_t *)(esp + 32), *(void * *)(esp + 36), *(int32_t *)(esp + 40));
    SetEAX(emu, (uint32_t)(uintptr_t)r);
}

static void mgs2_island_w_iFpup(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    int32_t r = ((int32_t (*)(void *, uint32_t, void *))fnc)(*(void * *)(esp + 4), *(uint32_t *)(esp + 8), *(void * *)(esp + 12));
    SetEAX(emu, (uint32_t)(uintptr_t)r);
}

static void mgs2_island_w_pFi(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    void * r = ((void * (*)(int32_t))fnc)(*(int32_t *)(esp + 4));
    SetEAX(emu, (uint32_t)(uintptr_t)r);
}

static void mgs2_island_w_pFp(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    void * r = ((void * (*)(void *))fnc)(*(void * *)(esp + 4));
    SetEAX(emu, (uint32_t)(uintptr_t)r);
}

static void mgs2_island_w_pFpp(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    void * r = ((void * (*)(void *, void *))fnc)(*(void * *)(esp + 4), *(void * *)(esp + 8));
    SetEAX(emu, (uint32_t)(uintptr_t)r);
}

static void mgs2_island_w_pFpu(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    void * r = ((void * (*)(void *, uint32_t))fnc)(*(void * *)(esp + 4), *(uint32_t *)(esp + 8));
    SetEAX(emu, (uint32_t)(uintptr_t)r);
}

static void mgs2_island_w_pFu(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    void * r = ((void * (*)(uint32_t))fnc)(*(uint32_t *)(esp + 4));
    SetEAX(emu, (uint32_t)(uintptr_t)r);
}

static void mgs2_island_w_uFppp(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    uint32_t r = ((uint32_t (*)(void *, void *, void *))fnc)(*(void * *)(esp + 4), *(void * *)(esp + 8), *(void * *)(esp + 12));
    SetEAX(emu, (uint32_t)(uintptr_t)r);
}

static void mgs2_island_w_uFppu(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    uint32_t r = ((uint32_t (*)(void *, void *, uint32_t))fnc)(*(void * *)(esp + 4), *(void * *)(esp + 8), *(uint32_t *)(esp + 12));
    SetEAX(emu, (uint32_t)(uintptr_t)r);
}

static void mgs2_island_w_uFpupu(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    uint32_t r = ((uint32_t (*)(void *, uint32_t, void *, uint32_t))fnc)(*(void * *)(esp + 4), *(uint32_t *)(esp + 8), *(void * *)(esp + 12), *(uint32_t *)(esp + 16));
    SetEAX(emu, (uint32_t)(uintptr_t)r);
}

static void mgs2_island_w_vF(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    ((void (*)(void))fnc)();
}

static void mgs2_island_w_vFii(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    ((void (*)(int32_t, int32_t))fnc)(*(int32_t *)(esp + 4), *(int32_t *)(esp + 8));
}

static void mgs2_island_w_vFp(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    ((void (*)(void *))fnc)(*(void * *)(esp + 4));
}

static void mgs2_island_w_vFpp(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    ((void (*)(void *, void *))fnc)(*(void * *)(esp + 4), *(void * *)(esp + 8));
}

static void mgs2_island_w_vFppp(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    ((void (*)(void *, void *, void *))fnc)(*(void * *)(esp + 4), *(void * *)(esp + 8), *(void * *)(esp + 12));
}

/*
 * Candidate entries get the same wrapper signature with an A/B gate.
 *
 * Both arms come through here, read the same three argument slots off the guest
 * stack, and pay for this wrapper. Only the final step differs, so the gate's
 * own cost is in both arms and cancels out of the paired difference. A separate
 * wrapper rather than a flag inside mgs2_island_w_vFppp, because that one is
 * shared with other entries that must not be touched.
 *
 * The unrouted arm runs the guest's own body. That is safe here: DynaCall sets
 * R_EIP directly and hasAlternate() consults only the alternates hash map,
 * which marker-matched island entries were never added to, so this does not
 * re-enter the bridge.
 */
int mgs2_island_ab_route(unsigned int entry);
void mgs2_island_ab_register_guest(unsigned int entry, void *ptr);
int mgs2_island_ab_guest_selector(unsigned int entry);
uintptr_t mgs2_island_entry_guest(unsigned int id);
uintptr_t mgs2_island_guest_symbol(const char *name);
void mgs2_island_set_batch_state(void *state);

/* p67 correctness-only state. This lives in Box86 rather than either linked
 * WineD3D copy, so the entry wrapper and native final-draw callback publish to
 * one bounded memory record. */
#define MGS2_DRAW_CORRECTNESS_MAGIC 0x31435244u /* DRC1 */

struct mgs2_draw_correctness_public
{
    uint32_t magic, version, size_words, signature;
    uint32_t enabled;
    uint32_t tls_state, tls_attempts;
    uint32_t guest_tls_idx, native_tls_before, native_tls_after;
    uint32_t source_draws, guest_fallback_draws, final_draws;
    uint32_t final_arrays, final_elements, final_batch_elements;
    uint32_t final_instanced, final_other;
};

__attribute__((visibility("default")))
struct mgs2_draw_correctness_public mgs2_p67_draw_correctness =
{
    MGS2_DRAW_CORRECTNESS_MAGIC, 1,
    sizeof(struct mgs2_draw_correctness_public) / sizeof(uint32_t),
    ~MGS2_DRAW_CORRECTNESS_MAGIC,
};

#define MGS2_P69_CORRECTNESS_MAGIC 0x31413950u /* P9A1 */

struct mgs2_p69_correctness_public
{
    uint32_t magic, version, size_words, signature;
    uint32_t enabled, calls, false_returns, guest_fallbacks;
};

__attribute__((visibility("default")))
struct mgs2_p69_correctness_public mgs2_p69_correctness =
{
    MGS2_P69_CORRECTNESS_MAGIC, 1,
    sizeof(struct mgs2_p69_correctness_public) / sizeof(uint32_t),
    ~MGS2_P69_CORRECTNESS_MAGIC,
};

static int mgs2_p69_correctness_on(void)
{
    static int enabled = -1;

    if (enabled == -1)
    {
        const char *value = getenv("MGS2_P69_CORRECTNESS");

        enabled = value && strcmp(value, "0");
        mgs2_p69_correctness.enabled = enabled;
    }
    return enabled;
}

#define MGS2_PHASE_A_CORRECTNESS_MAGIC 0x31413050u /* P0A1 */

struct mgs2_phase_a_correctness_public
{
    uint32_t magic, version, size_words, signature;
    uint32_t enabled, calls, guest_fallbacks;
};

__attribute__((visibility("default")))
struct mgs2_phase_a_correctness_public mgs2_phase_a_correctness =
{
    MGS2_PHASE_A_CORRECTNESS_MAGIC, 1,
    sizeof(struct mgs2_phase_a_correctness_public) / sizeof(uint32_t),
    ~MGS2_PHASE_A_CORRECTNESS_MAGIC,
};

static int mgs2_phase_a_correctness_on(void)
{
    static int enabled = -1;

    if (enabled == -1)
    {
        const char *value = getenv("MGS2_PHASE_A_CORRECTNESS");

        enabled = value && strcmp(value, "0");
        mgs2_phase_a_correctness.enabled = enabled;
    }
    return enabled;
}

static int mgs2_draw_correctness_on(void)
{
    static int enabled = -1;

    if (enabled == -1)
    {
        const char *value = getenv("MGS2_DRAW_CORRECTNESS");

        enabled = value && strcmp(value, "0");
        mgs2_p67_draw_correctness.enabled = enabled;
    }
    return enabled;
}

static void mgs2_island_draw_source(void)
{
    if (mgs2_draw_correctness_on())
        ++mgs2_p67_draw_correctness.source_draws;
}

static void mgs2_island_draw_guest_fallback(void)
{
    if (mgs2_draw_correctness_on())
        ++mgs2_p67_draw_correctness.guest_fallback_draws;
}

void mgs2_island_draw_final(unsigned int kind, unsigned int count)
{
    if (!mgs2_draw_correctness_on() || !count)
        return;
    mgs2_p67_draw_correctness.final_draws += count;
    switch (kind)
    {
        case 1: mgs2_p67_draw_correctness.final_arrays += count; break;
        case 2: mgs2_p67_draw_correctness.final_elements += count; break;
        case 3: mgs2_p67_draw_correctness.final_batch_elements += count; break;
        case 4: mgs2_p67_draw_correctness.final_instanced += count; break;
        default: mgs2_p67_draw_correctness.final_other += count; break;
    }
}

uint32_t context_get_tls_idx(void);
void context_set_tls_idx(uint32_t idx);

static int mgs2_island_context_tls_sync(void)
{
    static int status;
    static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
    static const unsigned int witness[] = {32, 9, 1, 3};
    unsigned int i, matched = 0;
    int current = __atomic_load_n(&status, __ATOMIC_ACQUIRE);

    if (current)
        return current;
    for (i = 0; i < sizeof(witness) / sizeof(witness[0]); ++i)
        if (mgs2_island_entry_guest(witness[i]))
            ++matched;
    if (matched < 2)
        return 0;

    pthread_mutex_lock(&lock);
    current = __atomic_load_n(&status, __ATOMIC_RELAXED);
    if (!current)
    {
        uintptr_t getter = mgs2_island_guest_symbol("context_get_tls_idx");
        uint32_t guest_idx = getter ? RunFunctionFmt(getter, "") : UINT32_MAX;
        uint32_t native_before = context_get_tls_idx();
        uint32_t native_after = native_before;

        if (guest_idx != UINT32_MAX)
        {
            context_set_tls_idx(guest_idx);
            native_after = context_get_tls_idx();
        }
        current = guest_idx != UINT32_MAX && native_after == guest_idx ? 1 : -1;
        mgs2_p67_draw_correctness.tls_state = current;
        ++mgs2_p67_draw_correctness.tls_attempts;
        mgs2_p67_draw_correctness.guest_tls_idx = guest_idx;
        mgs2_p67_draw_correctness.native_tls_before = native_before;
        mgs2_p67_draw_correctness.native_tls_after = native_after;
        printf_log(LOG_NONE, "MGS2 p67 TLS: guest %u, native before %u, after %u"
                " -- entry 37 %s\n", guest_idx, native_before, native_after,
                current == 1 ? "READY" : "REFUSED");
        __atomic_store_n(&status, current, __ATOMIC_RELEASE);
    }
    pthread_mutex_unlock(&lock);
    return current;
}

static void mgs2_island_w_ab10_vFppp(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    void *a = *(void **)(esp + 4), *b = *(void **)(esp + 8), *c = *(void **)(esp + 12);

    if (mgs2_island_ab_route(10))
        ((void (*)(void *, void *, void *))fnc)(a, b, c);
    else
    {
        uintptr_t guest = mgs2_island_entry_guest(10);

        if (guest)
            RunFunctionFmt(guest, "ppp", a, b, c);
        else
            ((void (*)(void *, void *, void *))fnc)(a, b, c);
    }
}

static void mgs2_island_w_ab4_vF(x86emu_t *emu, uintptr_t fnc)
{
    static int state_status; /* 0 waiting for witnesses, 1 ready, -1 failed */
    int routed = mgs2_island_ab_route(4);

    if (!state_status)
    {
        /* The name/RVA table may arm only after two independently matched
         * guest functions establish the DLL base.  Entry 4 itself appears
         * earlier during startup, so keep the guest path until that invariant
         * is true instead of poisoning class-B with a premature arm attempt. */
        static const unsigned int witness[] = {32, 9, 1, 3};
        unsigned int i, matched = 0;

        for (i = 0; i < sizeof(witness) / sizeof(witness[0]); ++i)
            if (mgs2_island_entry_guest(witness[i]))
                ++matched;
        if (matched >= 2)
        {
            uintptr_t getter = mgs2_island_guest_symbol("mgs2_batch_state");
            void *state = getter ? (void *)RunFunctionFmt(getter, "") : NULL;

            if (state)
            {
                mgs2_island_set_batch_state(state);
                state_status = 1;
                printf_log(LOG_NONE, "MGS2 island: entry 4 shares guest batch state %p\n", state);
            }
            else
            {
                state_status = -1;
                printf_log(LOG_NONE, "MGS2 island: entry 4 cannot resolve guest batch state;"
                        " keeping guest path\n");
            }
        }
    }

    if (routed && state_status == 1)
        ((void (*)(void))fnc)();
    else
    {
        uintptr_t guest = mgs2_island_entry_guest(4);

        if (guest)
            RunFunctionFmt(guest, "");
        else
            ((void (*)(void))fnc)();
    }
}

static void mgs2_island_w_ab23_vFppu(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    void *a = *(void **)(esp + 4), *b = *(void **)(esp + 8);
    uint32_t c = *(uint32_t *)(esp + 12);

    if (mgs2_island_ab_route(23))
        ((void (*)(void *, void *, uint32_t))fnc)(a, b, c);
    else
    {
        uintptr_t guest = mgs2_island_entry_guest(23);

        if (guest)
            RunFunctionFmt(guest, "ppu", a, b, c);
        else
            ((void (*)(void *, void *, uint32_t))fnc)(a, b, c);
    }
}

static void mgs2_island_w_ab34_uFpupu(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    void *a = *(void **)(esp + 4), *c = *(void **)(esp + 12);
    uint32_t b = *(uint32_t *)(esp + 8), d = *(uint32_t *)(esp + 16), r;

    if (mgs2_island_ab_route(34))
        r = ((uint32_t (*)(void *, uint32_t, void *, uint32_t))fnc)(a, b, c, d);
    else
    {
        uintptr_t guest = mgs2_island_entry_guest(34);

        if (guest)
            r = RunFunctionFmt(guest, "pupu", a, b, c, d);
        else
            r = ((uint32_t (*)(void *, uint32_t, void *, uint32_t))fnc)(a, b, c, d);
    }
    SetEAX(emu, r);
}

/* The post-batching DRAW boundary. Both DRAW packet forms converge here; only
 * the final call switches under A/B, while the queue stays guest x86. */
static void mgs2_island_w_ab37_vFpuup(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    void *a = *(void **)(esp + 4), *d = *(void **)(esp + 16);
    uint32_t b = *(uint32_t *)(esp + 8), c = *(uint32_t *)(esp + 12);
    int routed = mgs2_island_ab_route(37);

    if (routed && mgs2_island_context_tls_sync() == 1)
    {
        mgs2_island_draw_source();
        ((void (*)(void *, uint32_t, uint32_t, void *))fnc)(a, b, c, d);
    }
    else
    {
        uintptr_t guest = mgs2_island_entry_guest(37);

        if (routed)
            mgs2_island_draw_guest_fallback();
        if (guest)
            RunFunctionFmt(guest, "puup", a, b, c, d);
        else
            ((void (*)(void *, uint32_t, uint32_t, void *))fnc)(a, b, c, d);
    }
}

/* p68 lowers the cut below guest context acquisition and draw-state apply.
 * Only the final primitive-arrays tail crosses into ARM.  Keep the p67 TLS
 * guard because the shared batch flush reachable from this tail consults the
 * current context, and fail closed until the exact guest index is installed. */
static void mgs2_island_w38_vFp(x86emu_t *emu, uintptr_t fnc)
{
    struct mgs2_draw_tail_args32
    {
        uint32_t context_gl, state, idx_data, idx_size, base_vertex_idx;
        uint32_t start_idx, count, start_instance, instance_count;
        uint32_t ab_control;
    };
    uint32_t esp = GetESP(emu);
    void *a = *(void **)(esp + 4);
    int routed;

    if (a)
        mgs2_island_ab_register_guest(38,
                (void *)(uintptr_t)((const struct mgs2_draw_tail_args32 *)a)->ab_control);
    /* Once registered, guest x86 calls this bridge only for the routed arm.
     * The guest arm calls the original tail directly and never pays a
     * RunFunctionFmt() trampoline. */
    routed = mgs2_island_ab_guest_selector(38) ? 1 : mgs2_island_ab_route(38);

    if (routed && mgs2_island_context_tls_sync() == 1)
    {
        mgs2_island_draw_source();
        ((void (*)(void *))fnc)(a);
    }
    else
    {
        uintptr_t guest = mgs2_island_entry_guest(38);

        mgs2_island_draw_guest_fallback();
        if (guest)
            RunFunctionFmt(guest, "p", a);
        else
            ((void (*)(void *))fnc)(a);
    }
}

/* p69 moves only context_apply_draw_state() below an already current guest GL
 * context. The argument/result object is guest memory and has the same 32-bit
 * layout on i386 and armhf. Keep this correctness wrapper free of A/B logic. */
static void mgs2_island_w39_vFp(x86emu_t *emu, uintptr_t fnc)
{
    struct mgs2_apply_draw_state_args32
    {
        uint32_t context, device, state, indexed, result;
    };
    uint32_t esp = GetESP(emu);
    struct mgs2_apply_draw_state_args32 *a = *(void **)(esp + 4);

    if (mgs2_island_context_tls_sync() == 1)
    {
        if (mgs2_p69_correctness_on())
            ++mgs2_p69_correctness.calls;
        ((void (*)(void *))fnc)(a);
        if (mgs2_p69_correctness_on() && a && !a->result)
            ++mgs2_p69_correctness.false_returns;
    }
    else
    {
        uintptr_t guest = mgs2_island_entry_guest(39);

        if (mgs2_p69_correctness_on())
            ++mgs2_p69_correctness.guest_fallbacks;
        if (guest)
            RunFunctionFmt(guest, "p", a);
    }
}

static void mgs2_island_w40_vFp(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    void *a = *(void **)(esp + 4);

    if (mgs2_island_context_tls_sync() == 1)
    {
        if (mgs2_phase_a_correctness_on())
            ++mgs2_phase_a_correctness.calls;
        ((void (*)(void *))fnc)(a);
    }
    else
    {
        uintptr_t guest = mgs2_island_entry_guest(40);

        if (mgs2_phase_a_correctness_on())
            ++mgs2_phase_a_correctness.guest_fallbacks;
        if (guest)
            RunFunctionFmt(guest, "p", a);
    }
}

static void mgs2_island_w_vFppppi(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    ((void (*)(void *, void *, void *, void *, int32_t))fnc)(*(void * *)(esp + 4), *(void * *)(esp + 8), *(void * *)(esp + 12), *(void * *)(esp + 16), *(int32_t *)(esp + 20));
}

static void mgs2_island_w_vFppu(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    ((void (*)(void *, void *, uint32_t))fnc)(*(void * *)(esp + 4), *(void * *)(esp + 8), *(uint32_t *)(esp + 12));
}

static void mgs2_island_w_vFppuppupupi(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    ((void (*)(void *, void *, uint32_t, void *, void *, uint32_t, void *, uint32_t, void *, int32_t))fnc)(*(void * *)(esp + 4), *(void * *)(esp + 8), *(uint32_t *)(esp + 12), *(void * *)(esp + 16), *(void * *)(esp + 20), *(uint32_t *)(esp + 24), *(void * *)(esp + 28), *(uint32_t *)(esp + 32), *(void * *)(esp + 36), *(int32_t *)(esp + 40));
}

static void mgs2_island_w_vFpu(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    ((void (*)(void *, uint32_t))fnc)(*(void * *)(esp + 4), *(uint32_t *)(esp + 8));
}

static void mgs2_island_w_vFpuu(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    ((void (*)(void *, uint32_t, uint32_t))fnc)(*(void * *)(esp + 4), *(uint32_t *)(esp + 8), *(uint32_t *)(esp + 12));
}

static void mgs2_island_w_vFpuuupp(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    ((void (*)(void *, uint32_t, uint32_t, uint32_t, void *, void *))fnc)(*(void * *)(esp + 4), *(uint32_t *)(esp + 8), *(uint32_t *)(esp + 12), *(uint32_t *)(esp + 16), *(void * *)(esp + 20), *(void * *)(esp + 24));
}

static void mgs2_island_w_vFuu(x86emu_t *emu, uintptr_t fnc)
{
    uint32_t esp = GetESP(emu);
    ((void (*)(uint32_t, uint32_t))fnc)(*(uint32_t *)(esp + 4), *(uint32_t *)(esp + 8));
}

extern void context_invalidate_compute_state(void);
extern void context_invalidate_state(void);
extern void debug_d3dformat(void);
extern void device_invalidate_state(void);
extern void mgs2_batch_flush(void);
extern void mgs2_submit_census_gl_draw(void);
extern void multiply_matrix(void);
extern void wined3d_buffer_acquire_bo_for_write(void);
extern void wined3d_buffer_get_memory(void);
extern void wined3d_buffer_invalidate_location(void);
extern void wined3d_buffer_load(void);
extern void wined3d_buffer_load_location(void);
extern void wined3d_buffer_load_sysmem(void);
extern void wined3d_context_gl_enable_clip_distances(void);
extern void wined3d_debug_location(void);
extern void wined3d_device_context_blt(void);
extern void wined3d_device_context_emit_blt_sub_resource(void);
extern void wined3d_ffp_get_fs_settings(void);
extern void wined3d_format_calculate_pitch(void);
extern void wined3d_format_convert_from_float(void);
extern void wined3d_light_state_get_light(void);
extern void wined3d_rendertarget_view_invalidate_location(void);
extern void wined3d_rendertarget_view_load_location(void);
extern void wined3d_rendertarget_view_prepare_location(void);
extern void wined3d_rendertarget_view_validate_location(void);
extern void wined3d_resource_check_box_dimensions(void);
extern void wined3d_resource_free_sysmem(void);
extern void wined3d_resource_memory_colour_fill(void);
extern void wined3d_stream_info_from_declaration(void);
extern void wined3d_texture_add_dirty_region(void);
extern void wined3d_texture_from_resource(void);
extern void wined3d_texture_invalidate_location(void);
extern void wined3d_texture_load_location(void);
extern void wined3d_texture_prepare_location(void);
extern void wined3d_texture_validate_location(void);
extern void mgs2_cs_exec_draw_one_island(void);
extern void mgs2_draw_primitive_arrays_island(void);
extern void mgs2_context_apply_draw_state_island(void);
extern void mgs2_draw_state_phase_a_island(void);

const struct mgs2_island_entry mgs2_island_entries[] = {
    { 0, (void *)mgs2_island_w_vFpu, (void *)context_invalidate_compute_state },
    { 1, (void *)mgs2_island_w_vFpu, (void *)context_invalidate_state },
    { 2, (void *)mgs2_island_w_pFi, (void *)debug_d3dformat },
    { 3, (void *)mgs2_island_w_vFpu, (void *)device_invalidate_state },
    { 4, (void *)mgs2_island_w_ab4_vF, (void *)mgs2_batch_flush },
    { 5, (void *)mgs2_island_w_vFuu, (void *)mgs2_submit_census_gl_draw },
    { 6, (void *)mgs2_island_w_vFppp, (void *)multiply_matrix },
    { 7, (void *)mgs2_island_w_vFpp, (void *)wined3d_buffer_acquire_bo_for_write },
    { 8, (void *)mgs2_island_w_uFppp, (void *)wined3d_buffer_get_memory },
    { 9, (void *)mgs2_island_w_vFpu, (void *)wined3d_buffer_invalidate_location },
    { 10, (void *)mgs2_island_w_ab10_vFppp, (void *)wined3d_buffer_load },
    { 11, (void *)mgs2_island_w_uFppu, (void *)wined3d_buffer_load_location },
    { 12, (void *)mgs2_island_w_pFpp, (void *)wined3d_buffer_load_sysmem },
    { 13, (void *)mgs2_island_w_vFpu, (void *)wined3d_context_gl_enable_clip_distances },
    { 14, (void *)mgs2_island_w_pFu, (void *)wined3d_debug_location },
    { 15, (void *)mgs2_island_w_iFppuppupupi, (void *)wined3d_device_context_blt },
    { 16, (void *)mgs2_island_w_vFppuppupupi, (void *)wined3d_device_context_emit_blt_sub_resource },
    { 17, (void *)mgs2_island_w_vFppp, (void *)wined3d_ffp_get_fs_settings },
    { 18, (void *)mgs2_island_w_vFpuuupp, (void *)wined3d_format_calculate_pitch },
    { 19, (void *)mgs2_island_w_vFppp, (void *)wined3d_format_convert_from_float },
    { 20, (void *)mgs2_island_w_pFpu, (void *)wined3d_light_state_get_light },
    { 22, (void *)mgs2_island_w_vFpu, (void *)wined3d_rendertarget_view_invalidate_location },
    { 23, (void *)mgs2_island_w_ab23_vFppu, (void *)wined3d_rendertarget_view_load_location },
    { 24, (void *)mgs2_island_w_vFppu, (void *)wined3d_rendertarget_view_prepare_location },
    { 25, (void *)mgs2_island_w_vFpu, (void *)wined3d_rendertarget_view_validate_location },
    { 26, (void *)mgs2_island_w_iFpup, (void *)wined3d_resource_check_box_dimensions },
    { 27, (void *)mgs2_island_w_vFp, (void *)wined3d_resource_free_sysmem },
    { 28, (void *)mgs2_island_w_vFppppi, (void *)wined3d_resource_memory_colour_fill },
    { 29, (void *)mgs2_island_w_vFppp, (void *)wined3d_stream_info_from_declaration },
    { 31, (void *)mgs2_island_w_iFpup, (void *)wined3d_texture_add_dirty_region },
    { 32, (void *)mgs2_island_w_pFp, (void *)wined3d_texture_from_resource },
    { 33, (void *)mgs2_island_w_vFpuu, (void *)wined3d_texture_invalidate_location },
    { 34, (void *)mgs2_island_w_ab34_uFpupu, (void *)wined3d_texture_load_location },
    { 35, (void *)mgs2_island_w_uFpupu, (void *)wined3d_texture_prepare_location },
    { 36, (void *)mgs2_island_w_vFpuu, (void *)wined3d_texture_validate_location },
    { 37, (void *)mgs2_island_w_ab37_vFpuup, (void *)mgs2_cs_exec_draw_one_island },
    { 38, (void *)mgs2_island_w38_vFp, (void *)mgs2_draw_primitive_arrays_island },
    { 39, (void *)mgs2_island_w39_vFp, (void *)mgs2_context_apply_draw_state_island },
    { 40, (void *)mgs2_island_w40_vFp, (void *)mgs2_draw_state_phase_a_island },
};
const unsigned int mgs2_island_entry_count = 39;

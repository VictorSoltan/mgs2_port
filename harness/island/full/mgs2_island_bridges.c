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
uintptr_t mgs2_island_entry_guest(unsigned int id);
uintptr_t mgs2_island_guest_symbol(const char *name);
void mgs2_island_set_batch_state(void *state);

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
};
const unsigned int mgs2_island_entry_count = 35;

/*
 * Native ARM implementations of the non-WineD3D entry points that the island's
 * routed closure actually reaches.
 *
 * These were abort stubs. That is the right default -- a mis-routed call must
 * fail loudly -- but six of them sit on paths the hot entries genuinely take,
 * so with stubs those entries can never be measured at all. Each one here is a
 * real implementation, not a silencer, and anything still unimplemented stays
 * an abort stub in mgs2_island_stubs.c.
 *
 * Regenerating mgs2_island_stubs.c must exclude exactly the names defined here,
 * or the link fails on duplicate symbols. The list is at the bottom of this
 * file so the generator input and this file cannot drift apart silently.
 */
#define _GNU_SOURCE
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "debug.h"
#include "box86context.h"
#include "callback.h"
#include "x86emu.h"
#include "emu/x86emu_private.h"
#include "emu/x86run_private.h"

/*
 * The guest TEB.
 *
 * On i386 NtCurrentTeb() is `mov fs:0x18` -- Wine's TEB self-pointer, in a
 * segment Box86 maintains per guest thread. Compiled for ARM the same inline
 * becomes a read of the host thread pointer, which is unrelated. Patch 49
 * redirects the ARM branch of winnt.h here when MGS2_ISLAND_ARM is defined.
 *
 * This must be the emu of the thread that entered the island, and must never be
 * a freshly manufactured one -- see thread_get_emu_nocreate(). An earlier
 * version used thread_get_emu(), which creates an emu rather than reporting
 * that there is none, so its NULL check could never fire.
 *
 * The fix for that first carried a pair of __thread variables in Box86 to hold
 * an entry emu across a save/restore bracket in all 23 wrappers. Those were
 * withdrawn: the only build that ever carried them, box86-island8, is also the
 * only build that has died on the reinforcement scene, with 262 "accessing
 * segment NULL" warnings that no other build has produced -- while the same
 * census DLL on production Box86 played the same fight through with none. The
 * mechanism is not established, and the TLS was not needed: the current thread's
 * emu already IS the entry emu for every call the island makes today, because
 * reverse guest callbacks measured 0.0 per frame. Reintroduce a bracket only
 * when one is actually needed, and not with new thread-local storage.
 */
void *mgs2_island_teb(void)
{
    x86emu_t *emu = thread_get_emu_nocreate();
    uintptr_t fs;

    if (!emu)
    {
        printf_log(LOG_NONE, "MGS2 island: NtCurrentTeb() with no emu on this thread\n");
        abort();
    }
    fs = GetFSBaseEmu(emu);
    if (!fs)
    {
        printf_log(LOG_NONE, "MGS2 island: NtCurrentTeb() with a null guest FS base\n");
        abort();
    }
    return *(void **)(fs + 0x18);
}

/* Win32 TLS must use the guest TEB, not host pthread TLS. Wine i386 keeps
 * LastErrorValue at 0x34, 64 inline TLS cells at 0xe10, and the expansion-array
 * pointer at 0xf94. A missing expansion array cannot be allocated with host
 * malloc: guest HeapFree would later receive the wrong allocator's pointer. */
#define MGS2_TEB_LAST_ERROR          0x034
#define MGS2_TEB_TLS_SLOTS           0xe10
#define MGS2_TEB_TLS_EXPANSION       0xf94
#define MGS2_TLS_INLINE_SLOTS        64
#define MGS2_TLS_EXPANSION_SLOTS     1024
#define MGS2_ERROR_SUCCESS           0
#define MGS2_ERROR_INVALID_PARAMETER 87

void *TlsGetValue(uint32_t index)
{
    unsigned char *teb = mgs2_island_teb();
    uint32_t value;

    *(uint32_t *)(teb + MGS2_TEB_LAST_ERROR) = MGS2_ERROR_SUCCESS;
    if (index < MGS2_TLS_INLINE_SLOTS)
        value = *(uint32_t *)(teb + MGS2_TEB_TLS_SLOTS + index * sizeof(uint32_t));
    else
    {
        uint32_t expansion;

        index -= MGS2_TLS_INLINE_SLOTS;
        if (index >= MGS2_TLS_EXPANSION_SLOTS)
        {
            *(uint32_t *)(teb + MGS2_TEB_LAST_ERROR) = MGS2_ERROR_INVALID_PARAMETER;
            return NULL;
        }
        expansion = *(uint32_t *)(teb + MGS2_TEB_TLS_EXPANSION);
        if (!expansion)
            return NULL;
        value = ((uint32_t *)(uintptr_t)expansion)[index];
    }
    return (void *)(uintptr_t)value;
}

int TlsSetValue(uint32_t index, void *value)
{
    unsigned char *teb = mgs2_island_teb();

    if (index < MGS2_TLS_INLINE_SLOTS)
        *(uint32_t *)(teb + MGS2_TEB_TLS_SLOTS + index * sizeof(uint32_t)) = (uintptr_t)value;
    else
    {
        uint32_t expansion;

        index -= MGS2_TLS_INLINE_SLOTS;
        if (index >= MGS2_TLS_EXPANSION_SLOTS)
        {
            *(uint32_t *)(teb + MGS2_TEB_LAST_ERROR) = MGS2_ERROR_INVALID_PARAMETER;
            return 0;
        }
        expansion = *(uint32_t *)(teb + MGS2_TEB_TLS_EXPANSION);
        if (!expansion)
        {
            printf_log(LOG_NONE, "MGS2 island: TlsSetValue expansion array is absent;"
                    " refusing host-heap substitution\n");
            abort();
        }
        ((uint32_t *)(uintptr_t)expansion)[index] = (uintptr_t)value;
    }
    return 1;
}

static uintptr_t mgs2_guest_import(const char *name, uintptr_t *cached);

/* DCE ownership is mutable guest win32u state. Resolve Wine's real export once
 * and execute it under Box86 instead of manufacturing a second native cache. */
void *WindowFromDC(void *dc)
{
    static uintptr_t fn;
    static volatile unsigned int diagnostic_calls;
    uint32_t result;

    if (!__atomic_load_n(&fn, __ATOMIC_ACQUIRE))
    {
        mgs2_guest_import("WindowFromDC", &fn);
#if MGS2_ISLAND_DIAGNOSTICS
        printf_log(LOG_NONE, "MGS2 island: guest WindowFromDC resolved to %p\n", (void *)fn);
#endif
    }
#if MGS2_ISLAND_DIAGNOSTICS
    if (diagnostic_calls < 4)
        printf_log(LOG_NONE, "MGS2 island: guest WindowFromDC enter dc %p\n", dc);
#endif
    result = RunFunctionFmt(fn, "p", dc);
#if MGS2_ISLAND_DIAGNOSTICS
    if (diagnostic_calls++ < 4)
        printf_log(LOG_NONE, "MGS2 island: guest WindowFromDC return %#x\n", result);
#endif
    return (void *)(uintptr_t)result;
}

static uintptr_t mgs2_guest_wgl_get_pixel_format;

static int mgs2_island_wgl_get_pixel_format(void *dc)
{
    uintptr_t fn = __atomic_load_n(&mgs2_guest_wgl_get_pixel_format, __ATOMIC_ACQUIRE);

    if (!fn)
    {
        printf_log(LOG_NONE, "MGS2 island: wglGetPixelFormat thunk called before install\n");
        abort();
    }
    return (int)RunFunctionFmt(fn, "p", dc);
}

void *mgs2_island_wrap_wgl_get_pixel_format(void *guest)
{
    uintptr_t expected = 0;
    uintptr_t fn = (uintptr_t)guest;

    if (!fn)
        return NULL;
    if (!__atomic_compare_exchange_n(&mgs2_guest_wgl_get_pixel_format,
            &expected, fn, 0, __ATOMIC_RELEASE, __ATOMIC_ACQUIRE)
            && expected != fn)
    {
        printf_log(LOG_NONE, "MGS2 island: wglGetPixelFormat target changed"
                " from %p to %p -- refusing stale thunk\n", (void *)expected, guest);
        abort();
    }
    return (void *)mgs2_island_wgl_get_pixel_format;
}

/* Desktop polygon mode has no GLES entry point on this driver. The guest
 * opengl32 thunk is still authoritative: it performs Wine's Unix-call and
 * returns STATUS_NOT_IMPLEMENTED when the GLES facade cannot provide the
 * operation. Preserve that exact behaviour instead of inventing a no-op. */
static uintptr_t mgs2_guest_gl_polygon_mode;

static void mgs2_island_gl_polygon_mode(unsigned int face, unsigned int mode)
{
    uintptr_t fn = __atomic_load_n(&mgs2_guest_gl_polygon_mode, __ATOMIC_ACQUIRE);

    if (!fn)
    {
        printf_log(LOG_NONE, "MGS2 island: glPolygonMode thunk called before install\n");
        abort();
    }
    RunFunctionFmt(fn, "uu", face, mode);
}

void *mgs2_island_wrap_gl_polygon_mode(void *guest)
{
    uintptr_t expected = 0;
    uintptr_t fn = (uintptr_t)guest;

    if (!fn)
        return NULL;
    if (!__atomic_compare_exchange_n(&mgs2_guest_gl_polygon_mode,
            &expected, fn, 0, __ATOMIC_RELEASE, __ATOMIC_ACQUIRE)
            && expected != fn)
    {
        printf_log(LOG_NONE, "MGS2 island: glPolygonMode target changed"
                " from %p to %p -- refusing stale thunk\n", (void *)expected, guest);
        abort();
    }
    return (void *)mgs2_island_gl_polygon_mode;
}

uintptr_t mgs2_island_module_base(void);

static uintptr_t mgs2_guest_import(const char *name, uintptr_t *cached)
{
    uintptr_t fn = __atomic_load_n(cached, __ATOMIC_ACQUIRE);

    if (!fn)
    {
        unsigned char *image = (unsigned char *)mgs2_island_module_base();
        uint32_t pe_offset, import_rva, import_size, descriptor_count, d;
        uintptr_t found = 0;
        uintptr_t expected = 0;

        if (!image || *(uint16_t *)image != 0x5a4d)
            goto not_found;
        pe_offset = *(uint32_t *)(image + 0x3c);
        if (*(uint32_t *)(image + pe_offset) != 0x00004550
                || *(uint16_t *)(image + pe_offset + 24) != 0x10b)
            goto not_found;
        import_rva = *(uint32_t *)(image + pe_offset + 24 + 104);
        import_size = *(uint32_t *)(image + pe_offset + 24 + 108);
        if (!import_rva || import_size < 20)
            goto not_found;
        descriptor_count = import_size / 20;
        for (d = 0; d < descriptor_count && !found; ++d)
        {
            uint32_t *descriptor = (uint32_t *)(image + import_rva + d * 20);
            uint32_t lookup_rva = descriptor[0], iat_rva = descriptor[4], i;
            uint32_t *lookup, *iat;

            if (!lookup_rva && !iat_rva)
                break;
            if (!lookup_rva || !iat_rva)
                continue;
            lookup = (uint32_t *)(image + lookup_rva);
            iat = (uint32_t *)(image + iat_rva);
            for (i = 0; lookup[i]; ++i)
            {
                const char *import_name;

                if (lookup[i] & 0x80000000u)
                    continue;
                import_name = (const char *)(image + lookup[i] + 2);
                if (!strcmp(import_name, name))
                {
                    found = iat[i];
                    break;
                }
            }
        }
not_found:
        if (!found)
        {
            printf_log(LOG_NONE, "MGS2 island: cannot resolve guest import %s"
                    " from wined3d IAT\n", name);
            abort();
        }
#if MGS2_ISLAND_DIAGNOSTICS
        printf_log(LOG_NONE, "MGS2 island: guest import %s resolved to %p\n",
                name, (void *)found);
#endif
        __atomic_compare_exchange_n(cached, &expected, found, 0,
                __ATOMIC_RELEASE, __ATOMIC_ACQUIRE);
        fn = expected ? expected : found;
    }
    return fn;
}

void *wglCreateContext(void *dc)
{
    static uintptr_t fn;
    return (void *)(uintptr_t)RunFunctionFmt(mgs2_guest_import("wglCreateContext", &fn), "p", dc);
}

int wglDeleteContext(void *context)
{
    static uintptr_t fn;
    return (int)RunFunctionFmt(mgs2_guest_import("wglDeleteContext", &fn), "p", context);
}

void *wglGetCurrentContext(void)
{
    static uintptr_t fn;
    return (void *)(uintptr_t)RunFunctionFmt(mgs2_guest_import("wglGetCurrentContext", &fn), "");
}

void *wglGetCurrentDC(void)
{
    static uintptr_t fn;
    return (void *)(uintptr_t)RunFunctionFmt(mgs2_guest_import("wglGetCurrentDC", &fn), "");
}

void *wglGetProcAddress(const char *name)
{
    static uintptr_t fn;
    return (void *)(uintptr_t)RunFunctionFmt(mgs2_guest_import("wglGetProcAddress", &fn), "p", name);
}

int wglMakeCurrent(void *dc, void *context)
{
    static uintptr_t fn;
    return (int)RunFunctionFmt(mgs2_guest_import("wglMakeCurrent", &fn), "pp", dc, context);
}

int wglShareLists(void *context1, void *context2)
{
    static uintptr_t fn;
    return (int)RunFunctionFmt(mgs2_guest_import("wglShareLists", &fn), "pp", context1, context2);
}

/* MSVCRT assert. Reaching one means a WineD3D invariant failed inside native
 * code, which is exactly the kind of thing this island must not paper over. */
void _assert(const char *expression, const char *file, unsigned int line)
{
    printf_log(LOG_NONE, "MGS2 island: assertion failed: %s, %s:%u\n",
            expression ? expression : "?", file ? file : "?", line);
    abort();
}

/* MSVCRT float classification. Wine's msvcrt values, from include/msvcrt/math.h:
 * FP_INFINITE 1, FP_NAN 2, FP_NORMAL -1, FP_SUBNORMAL -2, FP_ZERO 0. They are
 * not the host libc's, so the constants are written out rather than forwarded. */
short _fdclass(float x)
{
    union { float f; uint32_t u; } v = { .f = x };
    uint32_t exponent = (v.u >> 23) & 0xff;
    uint32_t mantissa = v.u & 0x7fffff;

    if (exponent == 0xff)
        return mantissa ? 2 : 1;
    if (!exponent)
        return mantissa ? -2 : 0;
    return -1;
}

/*
 * Wine's debug plumbing.
 *
 * TRACE and WARN are compiled out of the island (WINE_NO_TRACE_MSGS,
 * WINE_NO_DEBUG_MSGS) but ERR is not, by design: its channel test is a direct
 * read of the channel's flags, so an ERR inside routed code does reach here.
 *
 * Rule 2 of this project forbids logging from a hot thread while measuring it,
 * and an ERR that fires per draw would do exactly that. So the first few are
 * printed in full and the rest are counted and suppressed. The count is
 * exported: a run that suppressed nothing is a run in which no ERR fired, and
 * that distinction is worth keeping.
 */
#define MGS2_ISLAND_ERR_LIMIT 16

struct mgs2_wine_debug_channel
{
    unsigned char flags;
    char name[15];
};

__attribute__((visibility("default")))
volatile unsigned int mgs2_island_err_count;

unsigned char __wine_dbg_get_channel_flags(struct mgs2_wine_debug_channel *channel)
{
    return channel ? channel->flags : 0;
}

int __wine_dbg_header(int cls, struct mgs2_wine_debug_channel *channel, const char *function)
{
    static const char *const class_name[] = { "fixme", "err", "warn", "trace" };
    unsigned int n = __atomic_fetch_add(&mgs2_island_err_count, 1, __ATOMIC_RELAXED);

    if (n >= MGS2_ISLAND_ERR_LIMIT)
        return -1;      /* suppressed: never log per-draw from the routed thread */
    printf_log(LOG_NONE, "MGS2 island: %s:%s:%s ",
            (cls >= 0 && cls < 4) ? class_name[cls] : "?",
            channel ? channel->name : "?", function ? function : "?");
    return 0;
}

int __wine_dbg_output(const char *str)
{
    if (!str)
        return 0;
    printf_log(LOG_NONE, "%s", str);
    return (int)strlen(str);
}

/* debugstr_*() results outlive the call that built them but not the frame that
 * printed them. Wine uses a per-thread ring; this is the same idea, one shared
 * ring, which is sufficient because the only consumers left are the bounded
 * ERR headers above. */
const char *__wine_dbg_strdup(const char *str)
{
    static char ring[16][256];
    static volatile unsigned int slot;
    unsigned int i = __atomic_fetch_add(&slot, 1, __ATOMIC_RELAXED) & 15;

    if (!str)
        return NULL;
    snprintf(ring[i], sizeof(ring[i]), "%s", str);
    return ring[i];
}

/* MSVCRT's formatting core, which every wine_dbg_sprintf() and snprintf() in
 * the island bottoms out in -- including island entry 2, debug_d3dformat().
 * Mapped onto the host vsnprintf; the options word selects truncation
 * behaviour, and the standard-snprintf case is the one Wine's headers use. */
int __stdio_common_vsprintf(unsigned long long options, char *str, size_t len,
        const char *format, void *locale, va_list args)
{
    int ret;

    (void)options;
    (void)locale;
    if (!str || !len)
        return 0;
    ret = vsnprintf(str, len, format, args);
    if (ret < 0 || (size_t)ret >= len)
    {
        str[len - 1] = 0;
        return -1;      /* truncated, as _CRT_INTERNAL_PRINTF_STANDARD_SNPRINTF */
    }
    return ret;
}

/*
 * Names defined above. mgs2_island_stubs.c must not also define them.
 *
 *   _assert  _fdclass  __wine_dbg_get_channel_flags  __wine_dbg_header
 *   __wine_dbg_output  __wine_dbg_strdup  __stdio_common_vsprintf
 *   TlsGetValue  TlsSetValue  WindowFromDC
 *   wglCreateContext  wglDeleteContext  wglGetCurrentContext  wglGetCurrentDC
 *   wglGetProcAddress  wglMakeCurrent  wglShareLists
 *
 * _recalloc is deliberately NOT here and stays an abort stub. It would have to
 * resize a block whose allocator is unknown: WineD3D structures reaching the
 * island may have been allocated by the guest msvcrt, and handing a guest heap
 * pointer to the host realloc corrupts both heaps. No routed entry needs it.
 */

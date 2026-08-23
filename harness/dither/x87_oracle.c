/* Is the C rewrite bit-identical to the guest's x87 sequence?
 *
 * Nothing on the handheld can answer this. The only x87 there is Box86's own
 * emulation, so comparing against it would test the emulator rather than the
 * rewrite -- and the two on-device attempts at a differential test both failed
 * for a structural reason: calling the original from inside the bridge makes
 * the dynarec own a block for that address, after which indirect calls stop
 * consulting the hook, and the run compares one call instead of 16384.
 *
 * This host has real x87. So run the guest's exact instruction sequence for
 * real, and compare against the replacement over millions of inputs.
 *
 * The sequence, from mgs2_sse_rg353vs_port.exe+0x50dae1:
 *      fldcw   RC=11        <- set by the helper at +0x50d5b3 (or $0xc00)
 *      flds    src
 *      fmuls   255.0f
 *      fadds   dither
 *      fstps   tmp32        <- forced through single precision
 *      flds    tmp32
 *      fistpl  out
 *
 * The trap this caught: RC is not "truncate on FISTP". It is in the control
 * word and governs EVERY x87 rounding, so the FADDS and the narrowing FSTPS
 * truncate toward zero too. A rewrite that rounds those to nearest -- the C
 * default -- puts 127.99999991 exactly on 128.0f and returns 128 where the
 * guest returns 127. This found 24 such cases in 8 million before the fix.
 *
 * build: gcc -O2 -frounding-math -o x87_oracle x87_oracle.c -lm
 */
#include <stdio.h>
#include <stdint.h>
#include <math.h>
#include <fenv.h>

static int32_t x87_reference(float s, float d, unsigned short pc_bits)
{
    unsigned short cw, saved;
    float k = 255.0f, tmp;
    int32_t out;

    __asm__ volatile ("fnstcw %0" : "=m"(saved));
    cw = (unsigned short)((saved & ~0x0f00) | 0x0c00 | pc_bits);   /* RC=11 + PC */
    __asm__ volatile (
        "fldcw  %[cw]\n\t"
        "flds   %[s]\n\t"
        "fmuls  %[k]\n\t"
        "fadds  %[d]\n\t"
        "fstps  %[tmp]\n\t"
        "flds   %[tmp]\n\t"
        "fistpl %[out]\n\t"
        "fldcw  %[saved]\n\t"
        : [tmp] "=m"(tmp), [out] "=m"(out)
        : [cw] "m"(cw), [s] "m"(s), [k] "m"(k), [d] "m"(d), [saved] "m"(saved)
        : "st");
    return out;
}

/* Exactly what mgs2_native_dither_kernel() computes, with the caller having set
 * FE_TOWARDZERO once around the loop the way the guest sets its control word.
 * s * 255.0 is exact in double (24-bit significand times an 8-bit integer), so
 * only the add and the narrowing to float are rounded, and contraction into an
 * FMA cannot change the result. */
static inline int32_t candidate(float s, float d)
{
    float t = (float)((double)s * 255.0 + (double)d);

    if (!(t > -2147483649.0f && t < 2147483648.0f))
        return (int32_t)0x80000000;
    return (int32_t)t;
}

static long long compare(float s, float d, unsigned short pc, const char *name,
        long long *shown)
{
    int32_t r, c;

    r = x87_reference(s, d, pc);
    fesetround(FE_TOWARDZERO);
    c = candidate(s, d);
    fesetround(FE_TONEAREST);
    if (r == c)
        return 0;
    if ((*shown)++ < 8)
        printf("  %s  s=%.9g d=%.9g  x87=%d  rewrite=%d\n", name, s, d, r, c);
    return 1;
}

int main(void)
{
    static const unsigned short pcs[2] = { 0x0200, 0x0300 };
    static const char *pcname[2] = { "PC=53 (Windows default)", "PC=64 (extended)" };
    static const float probes[] = {
        0.0f, -0.0f, 1.0f, 0.5f / 255.0f, 1.0f / 255.0f, 127.5f / 255.0f,
        254.5f / 255.0f, 255.5f / 255.0f, -0.001f, 1.001f, 1e-30f, -1e-30f,
        0.99999994f, 1.00000012f, NAN, INFINITY, -INFINITY, 1e30f, -1e30f,
    };
    static const float dithers[] = {
        0.0f, 0.5f, 0.25f, 0.75f, 1.0f, -0.5f, 0.4999999f, 0.9999999f,
    };
    long long n = 0, bad[2] = { 0, 0 }, shown = 0;
    int p;

    for (p = 0; p < 2; ++p)
    {
        size_t a, b;
        long long i;
        uint32_t state = 0x12345678;

        for (a = 0; a < sizeof(probes) / sizeof(probes[0]); ++a)
            for (b = 0; b < sizeof(dithers) / sizeof(dithers[0]); ++b, ++n)
                bad[p] += compare(probes[a], dithers[b], pcs[p], pcname[p], &shown);

        for (i = 0; i < 4000000; ++i, ++n)
        {
            float s, d;

            state = state * 1664525u + 1013904223u;
            s = (float)(state >> 8) / (float)(1 << 24);
            state = state * 1664525u + 1013904223u;
            d = (float)(state >> 8) / (float)(1 << 24);
            if ((state & 0xf) == 0) s = s * 1.05f - 0.025f;   /* a little outside 0..1 */
            bad[p] += compare(s, d, pcs[p], pcname[p], &shown);
        }
    }
    printf("\nсравнений: %lld\n", n);
    for (p = 0; p < 2; ++p)
        printf("  %-26s расхождений: %lld\n", pcname[p], bad[p]);
    return (bad[0] || bad[1]) ? 1 : 0;
}

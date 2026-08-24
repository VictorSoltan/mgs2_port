/* Standalone ARM cost/correctness probe for the MGS2 dither kernel candidate.
 * It does not load the game or Box86. Build with the same hard-float compiler:
 *
 * arm-linux-gnueabihf-gcc -O2 -frounding-math -ffp-contract=off \
 *   -o arm_hybrid_bench arm_hybrid_bench.c -lm
 */
#include <fenv.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define PIXELS 512u
#define CALLS 32768u

static inline int32_t exact_channel(float s, float d)
{
    float t = (float)((double)s * 255.0 + (double)d);
    if (!(t > -2147483649.0f && t < 2147483648.0f))
        return (int32_t)0x80000000;
    return (int32_t)t;
}

static inline int32_t hybrid_channel(float s, float d, uint64_t *slow)
{
    double t;
    union { float f; uint32_t u; } source, dithering;

    source.f = s;
    dithering.f = d;
    if ((source.u | dithering.u) & 0x80000000u
            || (source.u & 0x7f800000u) == 0x7f800000u
            || (dithering.u & 0x7f800000u) == 0x7f800000u)
        goto exact;
    t = (double)s * 255.0 + (double)d;
    if (!(t < 2147483648.0))
        goto exact;
    return (int32_t)t;
exact:
    ++*slow;
    return exact_channel(s, d);
}

static inline uint32_t pack(const int32_t channel[4])
{
    uint32_t a = (uint32_t)channel[3];
    uint32_t r = (uint32_t)channel[0];
    uint32_t g = (uint32_t)channel[1];
    uint32_t b = (uint32_t)channel[2];
    return ((((a << 8) | r) << 8) | g) << 8 | b;
}

__attribute__((noinline))
static void exact_kernel(uint32_t *dst, const float *src, const float *dither,
                         uint32_t count)
{
    int saved = fegetround();
    uint32_t i;
    fesetround(FE_TOWARDZERO);
    for (i = 0; i < count; ++i)
    {
        int32_t channel[4];
        const float d = dither[i & 3];
        int k;
        for (k = 0; k < 4; ++k)
            channel[k] = exact_channel(src[i * 4 + k], d);
        dst[i] = pack(channel);
    }
    fesetround(saved);
}

__attribute__((noinline))
static void hybrid_kernel(uint32_t *dst, const float *src, const float *dither,
                          uint32_t count, uint64_t *slow)
{
    int saved = fegetround();
    uint32_t i;
    fesetround(FE_TOWARDZERO);
    for (i = 0; i < count; ++i)
    {
        int32_t channel[4];
        const float d = dither[i & 3];
        int k;
        for (k = 0; k < 4; ++k)
            channel[k] = hybrid_channel(src[i * 4 + k], d, slow);
        dst[i] = pack(channel);
    }
    fesetround(saved);
}

static uint64_t nanoseconds(void)
{
    struct timespec now;
    clock_gettime(CLOCK_MONOTONIC_RAW, &now);
    return (uint64_t)now.tv_sec * 1000000000ull + (uint64_t)now.tv_nsec;
}

static double run(int hybrid, uint32_t *dst, const float *src,
                  const float *dither, uint64_t *slow, uint32_t *checksum)
{
    uint64_t start = nanoseconds();
    uint32_t call, i;
    for (call = 0; call < CALLS; ++call)
        if (hybrid)
            hybrid_kernel(dst, src, dither + (call & 3), PIXELS, slow);
        else
            exact_kernel(dst, src, dither + (call & 3), PIXELS);
    for (i = 0; i < PIXELS; ++i)
        *checksum = (*checksum << 5) ^ (*checksum >> 2) ^ dst[i];
    return (double)(nanoseconds() - start) / 1000000.0;
}

int main(void)
{
    static const float dither[7] =
        {0.0f, 0.5f, 0.25f, 0.75f, 0.0f, 0.5f, 0.25f};
    float *src = malloc(sizeof(float) * PIXELS * 4);
    uint32_t *exact = malloc(sizeof(uint32_t) * PIXELS);
    uint32_t *hybrid = malloc(sizeof(uint32_t) * PIXELS);
    uint32_t state = 0x12345678u, checksum = 0;
    uint64_t slow = 0;
    double result[4];
    uint32_t i, mismatches = 0;

    if (!src || !exact || !hybrid)
        return 2;
    for (i = 0; i < PIXELS * 4; ++i)
    {
        state = state * 1664525u + 1013904223u;
        src[i] = (float)(state >> 8) / (float)(1u << 24);
    }
    exact_kernel(exact, src, dither, PIXELS);
    hybrid_kernel(hybrid, src, dither, PIXELS, &slow);
    for (i = 0; i < PIXELS; ++i)
        mismatches += exact[i] != hybrid[i];
    printf("verification pixels=%u channels=%u mismatches=%u slow=%llu\n",
           PIXELS, PIXELS * 4, mismatches, (unsigned long long)slow);

    slow = 0;
    result[0] = run(0, exact, src, dither, &slow, &checksum);
    result[1] = run(1, hybrid, src, dither, &slow, &checksum);
    result[2] = run(1, hybrid, src, dither, &slow, &checksum);
    result[3] = run(0, exact, src, dither, &slow, &checksum);
    printf("pixels_per_arm=%u exact_ms=%.3f,%.3f direct_ms=%.3f,%.3f "
           "direct_slow=%llu checksum=%08x\n",
           PIXELS * CALLS, result[0], result[3], result[1], result[2],
           (unsigned long long)slow, checksum);
    free(hybrid); free(exact); free(src);
    return mismatches ? 1 : 0;
}

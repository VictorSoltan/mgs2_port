/*
 * Go/no-go for the dmabuf presenter, run on the device before any of it is built.
 *
 * The question this answers, and nothing else: can a dma-buf allocated from a
 * kernel heap be imported by the proprietary Mali blob as an EGLImage, bound as
 * a colour attachment, and rendered into? If it cannot, the whole presenter is
 * dead and no winewayland code should be written.
 *
 * Why heaps rather than GBM, against the advice this project was given: probing
 * the device found no render node (only card0, driver rockchip-drm, and sway
 * holds DRM master), the armhf libgbm is a 12 KB shim over libmali-hook, and
 * box86 exports zero gbm_* wrappers. A dma-heap is open/ioctl/mmap -- plain
 * syscalls that the emulator passes straight through -- so this route needs no
 * new wrapper at all. Both CMA heaps and the system heap are tried because CMA
 * is physically contiguous, which is what the rockchip display controller wants
 * for direct scanout, while the system heap is cacheable and may import but
 * present incoherently.
 *
 * Everything is loaded with dlopen and declared locally, so this builds with a
 * bare cross-compiler and needs no EGL, GLES, DRM or kernel headers:
 *     arm-linux-gnueabihf-gcc -O1 -o dmabuf_import_probe dmabuf_import_probe.c -ldl
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <errno.h>

/* linux/dma-heap.h, inlined so no kernel headers are needed. The layout is
 * identical for 32- and 64-bit userspace, which is the reason this route
 * survives the emulator at all. */
struct dma_heap_allocation_data {
    uint64_t len;
    uint32_t fd;
    uint32_t fd_flags;
    uint64_t heap_flags;
};
#define DMA_HEAP_IOCTL_ALLOC _IOWR('H', 0x0, struct dma_heap_allocation_data)

typedef void *EGLDisplay, *EGLContext, *EGLImageKHR, *EGLConfig, *EGLClientBuffer;
typedef unsigned int EGLenum, EGLBoolean, GLenum, GLuint;
typedef int EGLint;

#define EGL_NO_CONTEXT          ((EGLContext)0)
#define EGL_NO_DISPLAY          ((EGLDisplay)0)
#define EGL_NO_IMAGE_KHR        ((EGLImageKHR)0)
#define EGL_DEFAULT_DISPLAY     ((void *)0)
#define EGL_NONE                0x3038
#define EGL_WIDTH               0x3057
#define EGL_HEIGHT              0x3056
#define EGL_OPENGL_ES_API       0x30A0
#define EGL_CONTEXT_CLIENT_VERSION 0x3098
#define EGL_LINUX_DMA_BUF_EXT   0x3270
#define EGL_LINUX_DRM_FOURCC_EXT 0x3271
#define EGL_DMA_BUF_PLANE0_FD_EXT     0x3272
#define EGL_DMA_BUF_PLANE0_OFFSET_EXT 0x3273
#define EGL_DMA_BUF_PLANE0_PITCH_EXT  0x3274
#define EGL_NO_CONFIG_KHR       ((EGLConfig)0)

#define GL_TEXTURE_2D           0x0DE1
#define GL_FRAMEBUFFER          0x8D40
#define GL_COLOR_ATTACHMENT0    0x8CE0
#define GL_FRAMEBUFFER_COMPLETE 0x8CD5
#define GL_COLOR_BUFFER_BIT     0x00004000
#define GL_RGBA                 0x1908
#define GL_UNSIGNED_BYTE        0x1401
#define GL_TEXTURE_MIN_FILTER   0x2801
#define GL_TEXTURE_MAG_FILTER   0x2800
#define GL_NEAREST              0x2600

#define FOURCC(a,b,c,d) ((uint32_t)(a) | ((uint32_t)(b) << 8) | \
                         ((uint32_t)(c) << 16) | ((uint32_t)(d) << 24))
#define DRM_FORMAT_XRGB8888 FOURCC('X','R','2','4')

#define W 640
#define H 480

static EGLDisplay (*p_eglGetDisplay)(void *);
static EGLBoolean (*p_eglInitialize)(EGLDisplay, EGLint *, EGLint *);
static EGLBoolean (*p_eglBindAPI)(EGLenum);
static EGLContext (*p_eglCreateContext)(EGLDisplay, EGLConfig, EGLContext, const EGLint *);
static EGLBoolean (*p_eglMakeCurrent)(EGLDisplay, void *, void *, EGLContext);
static const char *(*p_eglQueryString)(EGLDisplay, EGLint);
static EGLint (*p_eglGetError)(void);
static void *(*p_eglGetProcAddress)(const char *);
static EGLImageKHR (*p_eglCreateImageKHR)(EGLDisplay, EGLContext, EGLenum,
                                          EGLClientBuffer, const EGLint *);
static EGLBoolean (*p_eglDestroyImageKHR)(EGLDisplay, EGLImageKHR);
static void (*p_glEGLImageTargetTexture2DOES)(GLenum, EGLImageKHR);

static void (*p_glGenTextures)(int, GLuint *);
static void (*p_glBindTexture)(GLenum, GLuint);
static void (*p_glTexParameteri)(GLenum, GLenum, int);
static void (*p_glGenFramebuffers)(int, GLuint *);
static void (*p_glBindFramebuffer)(GLenum, GLuint);
static void (*p_glFramebufferTexture2D)(GLenum, GLenum, GLenum, GLuint, int);
static GLenum (*p_glCheckFramebufferStatus)(GLenum);
static void (*p_glClearColor)(float, float, float, float);
static void (*p_glClear)(unsigned int);
static void (*p_glFinish)(void);
static void (*p_glReadPixels)(int, int, int, int, GLenum, GLenum, void *);
static GLenum (*p_glGetError)(void);

static int load(void)
{
    void *egl = dlopen("libEGL.so.1", RTLD_NOW | RTLD_GLOBAL);
    void *gles = dlopen("libGLESv2.so.2", RTLD_NOW | RTLD_GLOBAL);
    if (!egl || !gles) { printf("dlopen failed: %s\n", dlerror()); return 0; }
#define G(h, n) do { p_##n = dlsym(h, #n); if (!p_##n) { \
        printf("missing symbol %s\n", #n); return 0; } } while (0)
    G(egl, eglGetDisplay); G(egl, eglInitialize); G(egl, eglBindAPI);
    G(egl, eglCreateContext); G(egl, eglMakeCurrent); G(egl, eglQueryString);
    G(egl, eglGetError); G(egl, eglGetProcAddress);
    G(gles, glGenTextures); G(gles, glBindTexture); G(gles, glTexParameteri);
    G(gles, glGenFramebuffers); G(gles, glBindFramebuffer);
    G(gles, glFramebufferTexture2D); G(gles, glCheckFramebufferStatus);
    G(gles, glClearColor); G(gles, glClear); G(gles, glFinish);
    G(gles, glReadPixels); G(gles, glGetError);
#undef G
    return 1;
}

/* Returns the dma-buf fd, or -1. */
static int heap_alloc(const char *heap, size_t len)
{
    struct dma_heap_allocation_data req;
    char path[128];
    int hfd, r;

    snprintf(path, sizeof(path), "/dev/dma_heap/%s", heap);
    if ((hfd = open(path, O_RDWR | O_CLOEXEC)) < 0) {
        printf("  %-20s open failed (%s)\n", heap, strerror(errno));
        return -1;
    }
    memset(&req, 0, sizeof(req));
    req.len = len;
    req.fd_flags = O_RDWR | O_CLOEXEC;
    r = ioctl(hfd, DMA_HEAP_IOCTL_ALLOC, &req);
    close(hfd);
    if (r < 0) { printf("  %-20s ALLOC ioctl failed\n", heap); return -1; }
    return (int)req.fd;
}

static int try_import(EGLDisplay dpy, const char *heap)
{
    EGLint attrs[] = {
        EGL_WIDTH, W, EGL_HEIGHT, H,
        EGL_LINUX_DRM_FOURCC_EXT, (EGLint)DRM_FORMAT_XRGB8888,
        EGL_DMA_BUF_PLANE0_FD_EXT, 0,
        EGL_DMA_BUF_PLANE0_OFFSET_EXT, 0,
        EGL_DMA_BUF_PLANE0_PITCH_EXT, W * 4,
        EGL_NONE
    };
    EGLImageKHR img;
    GLuint tex = 0, fbo = 0;
    GLenum status;
    unsigned char px[16];
    int fd = heap_alloc(heap, (size_t)W * H * 4);

    if (fd < 0) return 0;
    attrs[7] = fd;

    img = p_eglCreateImageKHR(dpy, EGL_NO_CONTEXT, EGL_LINUX_DMA_BUF_EXT, NULL, attrs);
    if (img == EGL_NO_IMAGE_KHR) {
        printf("  %-20s eglCreateImageKHR FAILED, egl error %#x\n", heap, p_eglGetError());
        close(fd);
        return 0;
    }

    p_glGenTextures(1, &tex);
    p_glBindTexture(GL_TEXTURE_2D, tex);
    p_glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    p_glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    p_glEGLImageTargetTexture2DOES(GL_TEXTURE_2D, img);
    if (p_glGetError() != 0) {
        printf("  %-20s glEGLImageTargetTexture2DOES FAILED\n", heap);
        p_eglDestroyImageKHR(dpy, img); close(fd); return 0;
    }

    p_glGenFramebuffers(1, &fbo);
    p_glBindFramebuffer(GL_FRAMEBUFFER, fbo);
    p_glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0);
    status = p_glCheckFramebufferStatus(GL_FRAMEBUFFER);
    if (status != GL_FRAMEBUFFER_COMPLETE) {
        printf("  %-20s FBO INCOMPLETE (%#x) -- importable but not renderable\n",
               heap, status);
        p_eglDestroyImageKHR(dpy, img); close(fd); return 0;
    }

    /* Render into it and read it back through GL. Proves the attachment is live;
     * it does NOT prove the CPU mapping is coherent, which is a separate check
     * the presenter does not need because nothing will read this on the CPU. */
    p_glClearColor(0.25f, 0.5f, 0.75f, 1.0f);
    p_glClear(GL_COLOR_BUFFER_BIT);
    p_glFinish();
    memset(px, 0, sizeof(px));
    p_glReadPixels(0, 0, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE, px);

    printf("  %-20s PASS  fd=%d  FBO complete, cleared, readback %02x %02x %02x %02x\n",
           heap, fd, px[0], px[1], px[2], px[3]);
    p_eglDestroyImageKHR(dpy, img);
    close(fd);
    return 1;
}



int main(void)
{
    static const char *heaps[] = { "linux,cma", "default_cma_region", "system" };
    EGLDisplay dpy;
    EGLContext ctx;
    EGLint major = 0, minor = 0;
    const char *exts;
    EGLint cattr[] = { EGL_CONTEXT_CLIENT_VERSION, 2, EGL_NONE };
    unsigned int i, pass = 0;

    if (!load()) return 2;

    dpy = p_eglGetDisplay(EGL_DEFAULT_DISPLAY);
    if (dpy == EGL_NO_DISPLAY || !p_eglInitialize(dpy, &major, &minor)) {
        printf("eglInitialize failed\n"); return 2;
    }
    printf("EGL %d.%d\n", major, minor);

    exts = p_eglQueryString(dpy, 0x3055 /* EGL_EXTENSIONS */);
    printf("dma_buf_import          %s\n",
           exts && strstr(exts, "EGL_EXT_image_dma_buf_import") ? "present" : "ABSENT");
    printf("dma_buf_import_modifiers %s\n",
           exts && strstr(exts, "EGL_EXT_image_dma_buf_import_modifiers") ? "present" : "ABSENT");
    printf("surfaceless_context     %s\n",
           exts && strstr(exts, "EGL_KHR_surfaceless_context") ? "present" : "ABSENT");
    printf("no_config_context       %s\n",
           exts && strstr(exts, "EGL_KHR_no_config_context") ? "present" : "ABSENT");

    p_eglCreateImageKHR = p_eglGetProcAddress("eglCreateImageKHR");
    p_eglDestroyImageKHR = p_eglGetProcAddress("eglDestroyImageKHR");
    p_glEGLImageTargetTexture2DOES = p_eglGetProcAddress("glEGLImageTargetTexture2DOES");
    if (!p_eglCreateImageKHR || !p_glEGLImageTargetTexture2DOES) {
        printf("entry points missing: create=%p target=%p\n",
               (void *)p_eglCreateImageKHR, (void *)p_glEGLImageTargetTexture2DOES);
        return 2;
    }

    p_eglBindAPI(EGL_OPENGL_ES_API);
    ctx = p_eglCreateContext(dpy, EGL_NO_CONFIG_KHR, EGL_NO_CONTEXT, cattr);
    if (ctx == EGL_NO_CONTEXT) {
        printf("eglCreateContext(no config) failed %#x -- retrying is the caller's "
               "job; the presenter always has a real config\n", p_eglGetError());
        return 2;
    }
    if (!p_eglMakeCurrent(dpy, NULL, NULL, ctx)) {
        printf("surfaceless eglMakeCurrent failed %#x\n", p_eglGetError());
        return 2;
    }

    printf("\nheap                 result\n");
    for (i = 0; i < sizeof(heaps) / sizeof(heaps[0]); i++)
        pass += try_import(dpy, heaps[i]);

    printf("\n%u of %u heaps import and render.\n", pass,
           (unsigned)(sizeof(heaps) / sizeof(heaps[0])));
    return pass ? 0 : 1;
}

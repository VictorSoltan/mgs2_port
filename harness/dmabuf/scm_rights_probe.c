/*
 * The one unproven step of the dmabuf presenter: does a dma-buf FD survive the
 * trip through the EMULATED x86 libwayland-client to sway?
 *
 * Everything else in the route is already proved. dmabuf_import_probe.c showed
 * the native blob imports a dma-heap FD as an EGLImage, makes a complete FBO out
 * of it and renders into it. box86 already wraps eglCreateImageKHR,
 * eglDestroyImageKHR and glEGLImageTargetTexture2DOES. sway/wlroots 0.19 speaks
 * zwp_linux_dmabuf_v1. What nothing has shown is that wl_proxy_marshal_flags
 * with an 'h' argument -- which becomes sendmsg with SCM_RIGHTS -- carries a
 * real kernel FD across when libwayland-client is running as translated x86
 * under Box86, the way the game runs it. If that fails, the presenter cannot be
 * built at all and no further work is justified.
 *
 * So this is built i386 and run under Box86 with libwayland-client in
 * BOX86_EMULATED_LIBS, exactly as the game has it. It:
 *
 *   1. allocates 640x480x4 from /dev/dma_heap/linux,cma  (plain ioctl)
 *   2. binds zwp_linux_dmabuf_v1 from the registry
 *   3. zwp_linux_buffer_params_v1.add(fd, ...) -- the SCM_RIGHTS crossing
 *   4. .create(...) and waits for `created` or `failed`
 *
 * `created` means the compositor received a usable FD, imported it into its own
 * renderer and handed back a wl_buffer. That is the whole question.
 *
 * The protocol glue is hand-written: this host has neither wayland-scanner nor
 * the wayland-protocols XML, and the two interfaces involved are small enough
 * that generating them is not worth a build dependency. The tables below are the
 * same shape wayland-scanner emits.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <wayland-client.h>
#include <wayland-client-protocol.h>

struct dma_heap_allocation_data {
    uint64_t len;
    uint32_t fd;
    uint32_t fd_flags;
    uint64_t heap_flags;
};
#define DMA_HEAP_IOCTL_ALLOC _IOWR('H', 0x0, struct dma_heap_allocation_data)

#define FOURCC(a,b,c,d) ((uint32_t)(a) | ((uint32_t)(b) << 8) | \
                         ((uint32_t)(c) << 16) | ((uint32_t)(d) << 24))
#define DRM_FORMAT_XRGB8888 FOURCC('X','R','2','4')
#define DRM_FORMAT_MOD_LINEAR 0ull
#define DRM_FORMAT_MOD_INVALID ((1ull << 56) - 1)

#define W 640
#define H 480

/* ------------------------------------------------------------------ */
/* zwp_linux_dmabuf_v1 / zwp_linux_buffer_params_v1, hand-rolled       */

extern const struct wl_interface zwp_linux_buffer_params_v1_interface;
extern const struct wl_interface zwp_linux_dmabuf_v1_interface;

static const struct wl_interface *dmabuf_types[] = {
    NULL, NULL, NULL,
    &zwp_linux_buffer_params_v1_interface,   /* create_params -> params */
    &wl_buffer_interface,                    /* created -> wl_buffer    */
};

static const struct wl_message dmabuf_requests[] = {
    { "destroy",       "",  dmabuf_types + 0 },
    { "create_params", "n", dmabuf_types + 3 },
};
static const struct wl_message dmabuf_events[] = {
    { "format",   "u",   dmabuf_types + 0 },
    { "modifier", "3uuu", dmabuf_types + 0 },
};
const struct wl_interface zwp_linux_dmabuf_v1_interface = {
    "zwp_linux_dmabuf_v1", 3,
    2, dmabuf_requests,
    2, dmabuf_events,
};

static const struct wl_message params_requests[] = {
    { "destroy",      "",       dmabuf_types + 0 },
    { "add",          "huuuuu", dmabuf_types + 0 },
    { "create",       "iiuu",   dmabuf_types + 0 },
    { "create_immed", "2niiuu", dmabuf_types + 4 },
};
static const struct wl_message params_events[] = {
    { "created", "n", dmabuf_types + 4 },
    { "failed",  "",  dmabuf_types + 0 },
};
const struct wl_interface zwp_linux_buffer_params_v1_interface = {
    "zwp_linux_buffer_params_v1", 3,
    4, params_requests,
    2, params_events,
};

struct params_listener {
    void (*created)(void *, struct wl_proxy *, struct wl_buffer *);
    void (*failed)(void *, struct wl_proxy *);
};

/* ------------------------------------------------------------------ */

static struct wl_proxy *g_dmabuf;
static int g_done, g_created, g_formats, g_xrgb_seen;

static void on_format(void *d, struct wl_proxy *p, uint32_t fmt)
{
    (void)d; (void)p;
    g_formats++;
    if (fmt == DRM_FORMAT_XRGB8888) g_xrgb_seen = 1;
}
static void on_modifier(void *d, struct wl_proxy *p, uint32_t fmt,
                        uint32_t hi, uint32_t lo)
{
    (void)d; (void)p; (void)hi; (void)lo;
    g_formats++;
    if (fmt == DRM_FORMAT_XRGB8888) g_xrgb_seen = 1;
}
static const struct { void *f[2]; } dmabuf_listener = { { on_format, on_modifier } };

static void on_created(void *d, struct wl_proxy *p, struct wl_buffer *buf)
{
    (void)d; (void)p;
    printf("  <- created, wl_buffer %p\n", (void *)buf);
    g_created = 1; g_done = 1;
}
static void on_failed(void *d, struct wl_proxy *p)
{
    (void)d; (void)p;
    printf("  <- FAILED: the compositor refused the buffer\n");
    g_done = 1;
}
static const struct params_listener params_listener = { on_created, on_failed };

static void reg_global(void *data, struct wl_registry *reg, uint32_t name,
                       const char *iface, uint32_t version)
{
    (void)data;
    printf("  global %-44s v%u\n", iface, version);
    if (strcmp(iface, "zwp_linux_dmabuf_v1")) return;
    printf("registry: zwp_linux_dmabuf_v1 version %u\n", version);
    g_dmabuf = wl_registry_bind(reg, name, &zwp_linux_dmabuf_v1_interface,
                                version < 3 ? version : 3);
}
static void reg_remove(void *d, struct wl_registry *r, uint32_t n)
{ (void)d; (void)r; (void)n; }
static const struct wl_registry_listener reg_listener = { reg_global, reg_remove };

static int heap_alloc(const char *heap, size_t len)
{
    struct dma_heap_allocation_data req;
    char path[128];
    int hfd, r;

    snprintf(path, sizeof(path), "/dev/dma_heap/%s", heap);
    if ((hfd = open(path, O_RDWR | O_CLOEXEC)) < 0) {
        printf("open %s: %s\n", path, strerror(errno));
        return -1;
    }
    memset(&req, 0, sizeof(req));
    req.len = len;
    req.fd_flags = O_RDWR | O_CLOEXEC;
    r = ioctl(hfd, DMA_HEAP_IOCTL_ALLOC, &req);
    close(hfd);
    if (r < 0) { printf("DMA_HEAP_IOCTL_ALLOC on %s: %s\n", heap, strerror(errno)); return -1; }
    return (int)req.fd;
}

int main(int argc, char **argv)
{
    const char *heap = argc > 1 ? argv[1] : "linux,cma";
    struct wl_display *dpy;
    struct wl_registry *reg;
    struct wl_proxy *params;
    int fd, i;

    printf("build: %d-bit\n", (int)(sizeof(void *) * 8));

    if (!(dpy = wl_display_connect(NULL))) {
        printf("wl_display_connect failed: %s\n", strerror(errno));
        return 2;
    }
    reg = wl_display_get_registry(dpy);
    wl_registry_add_listener(reg, &reg_listener, NULL);
    wl_display_roundtrip(dpy);
    if (!g_dmabuf) { printf("no zwp_linux_dmabuf_v1 in the registry\n"); return 2; }

    wl_proxy_add_listener(g_dmabuf, (void (**)(void))&dmabuf_listener, NULL);
    wl_display_roundtrip(dpy);
    printf("advertised format/modifier entries: %d, XRGB8888 present: %s\n",
           g_formats, g_xrgb_seen ? "yes" : "NO");

    if ((fd = heap_alloc(heap, (size_t)W * H * 4)) < 0) return 2;
    printf("allocated from %s, fd=%d, %d bytes\n", heap, fd, W * H * 4);

    params = wl_proxy_marshal_flags(g_dmabuf, 1, &zwp_linux_buffer_params_v1_interface,
                                    wl_proxy_get_version(g_dmabuf), 0, NULL);
    if (!params) { printf("create_params returned NULL\n"); return 2; }
    wl_proxy_add_listener(params, (void (**)(void))&params_listener, NULL);

    /* THE crossing: 'h' marshals as sendmsg + SCM_RIGHTS. */
    wl_proxy_marshal_flags(params, 1, NULL, wl_proxy_get_version(params), 0,
                           fd, 0u, 0u, (uint32_t)(W * 4),
                           (uint32_t)(DRM_FORMAT_MOD_LINEAR >> 32),
                           (uint32_t)(DRM_FORMAT_MOD_LINEAR & 0xffffffffu));
    wl_proxy_marshal_flags(params, 2, NULL, wl_proxy_get_version(params), 0,
                           W, H, (uint32_t)DRM_FORMAT_XRGB8888, 0u);
    wl_display_flush(dpy);

    for (i = 0; i < 50 && !g_done; i++) {
        if (wl_display_roundtrip(dpy) < 0) {
            printf("protocol error: %s\n", strerror(errno));
            return 2;
        }
    }

    close(fd);
    if (!g_done) { printf("no reply after 50 roundtrips\n"); return 2; }
    printf("\n%s\n", g_created
        ? "PASS -- the FD crossed SCM_RIGHTS and sway made a wl_buffer from it."
        : "FAIL -- sway rejected the buffer. Check format/modifier before blaming the FD.");
    return g_created ? 0 : 1;
}

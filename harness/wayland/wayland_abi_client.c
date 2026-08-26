/* Targeted i386 client for Box86's native libwayland listener bridge.
 *
 * This intentionally exercises protocol callbacks, not rendering performance.
 * Build it as Linux i386, run it through the candidate Box86 on the RG353VS,
 * and drive the source/receiver/window modes from separate processes.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#include <wayland-client.h>
#include "wlr-data-control-unstable-v1-client-protocol.h"
#include "xdg-shell-client-protocol.h"

struct counts
{
    unsigned data_offer, offer, selection, finished;
    unsigned source_send, source_cancelled;
    unsigned xdg_configure, keyboard_key, keyboard_keymap;
};

struct app
{
    struct wl_display *display;
    struct wl_registry *registry;
    struct wl_compositor *compositor;
    struct wl_shm *shm;
    struct wl_seat *seat;
    struct wl_keyboard *keyboard;
    struct wl_data_device_manager *wl_data_manager;
    struct zwlr_data_control_manager_v1 *data_manager;
    struct zwlr_data_control_device_v1 *data_device;
    struct zwlr_data_control_source_v1 *data_source;
    struct zwlr_data_control_offer_v1 *selection_offer;
    struct xdg_wm_base *xdg_wm_base;
    struct wl_surface *surface;
    struct xdg_surface *xdg_surface;
    struct xdg_toplevel *xdg_toplevel;
    struct wl_buffer *buffer;
    struct counts count;
    int offered_text;
    int configured;
};

static uint32_t bounded_version(uint32_t advertised, uint32_t wanted)
{
    return advertised < wanted ? advertised : wanted;
}

static void registry_global(void *data, struct wl_registry *registry, uint32_t name,
                            const char *interface, uint32_t version)
{
    struct app *app = data;

    if (!strcmp(interface, wl_compositor_interface.name))
        app->compositor = wl_registry_bind(registry, name, &wl_compositor_interface,
                                           bounded_version(version, 4));
    else if (!strcmp(interface, wl_shm_interface.name))
        app->shm = wl_registry_bind(registry, name, &wl_shm_interface, 1);
    else if (!strcmp(interface, wl_seat_interface.name))
        app->seat = wl_registry_bind(registry, name, &wl_seat_interface,
                                     bounded_version(version, 7));
    else if (!strcmp(interface, wl_data_device_manager_interface.name))
        app->wl_data_manager = wl_registry_bind(registry, name,
                &wl_data_device_manager_interface, bounded_version(version, 3));
    else if (!strcmp(interface, zwlr_data_control_manager_v1_interface.name))
        app->data_manager = wl_registry_bind(registry, name,
                &zwlr_data_control_manager_v1_interface, 1);
    else if (!strcmp(interface, xdg_wm_base_interface.name))
        app->xdg_wm_base = wl_registry_bind(registry, name,
                &xdg_wm_base_interface, bounded_version(version, 4));
}

static void registry_remove(void *data, struct wl_registry *registry, uint32_t name)
{
    (void)data; (void)registry; (void)name;
}

static const struct wl_registry_listener registry_listener =
{
    registry_global,
    registry_remove,
};

static void xdg_ping(void *data, struct xdg_wm_base *base, uint32_t serial)
{
    (void)data;
    xdg_wm_base_pong(base, serial);
}

static const struct xdg_wm_base_listener xdg_wm_base_listener = { xdg_ping };

static void offer_mime(void *data, struct zwlr_data_control_offer_v1 *offer,
                       const char *mime)
{
    struct app *app = data;
    (void)offer;
    app->count.offer++;
    if (mime && !strcmp(mime, "text/plain;charset=utf-8")) app->offered_text = 1;
}

static const struct zwlr_data_control_offer_v1_listener offer_listener =
{
    offer_mime,
};

static void device_data_offer(void *data, struct zwlr_data_control_device_v1 *device,
                              struct zwlr_data_control_offer_v1 *offer)
{
    struct app *app = data;
    (void)device;
    app->count.data_offer++;
    if (zwlr_data_control_offer_v1_add_listener(offer, &offer_listener, app) < 0)
        fprintf(stderr, "offer listener registration failed\n");
}

static void device_selection(void *data, struct zwlr_data_control_device_v1 *device,
                             struct zwlr_data_control_offer_v1 *offer)
{
    struct app *app = data;
    (void)device;
    app->count.selection++;
    app->selection_offer = offer;
}

static void device_finished(void *data, struct zwlr_data_control_device_v1 *device)
{
    struct app *app = data;
    (void)device;
    app->count.finished++;
}

static const struct zwlr_data_control_device_v1_listener device_listener =
{
    device_data_offer,
    device_selection,
    device_finished,
    NULL,
};

static void source_send(void *data, struct zwlr_data_control_source_v1 *source,
                        const char *mime, int32_t fd)
{
    static const char payload[] = "mgs2-wayland-abi\n";
    struct app *app = data;
    (void)source; (void)mime;
    app->count.source_send++;
    if (fd >= 0)
    {
        ssize_t ignored = write(fd, payload, sizeof(payload) - 1);
        (void)ignored;
        close(fd);
    }
}

static void source_cancelled(void *data, struct zwlr_data_control_source_v1 *source)
{
    struct app *app = data;
    (void)source;
    app->count.source_cancelled++;
}

static const struct zwlr_data_control_source_v1_listener source_listener =
{
    source_send,
    source_cancelled,
};

static void keyboard_keymap(void *data, struct wl_keyboard *keyboard, uint32_t format,
                            int32_t fd, uint32_t size)
{
    struct app *app = data;
    (void)keyboard; (void)format; (void)size;
    app->count.keyboard_keymap++;
    if (fd >= 0) close(fd);
}

static void keyboard_enter(void *data, struct wl_keyboard *keyboard, uint32_t serial,
                           struct wl_surface *surface, struct wl_array *keys)
{
    (void)data; (void)keyboard; (void)serial; (void)surface; (void)keys;
}

static void keyboard_leave(void *data, struct wl_keyboard *keyboard, uint32_t serial,
                           struct wl_surface *surface)
{
    (void)data; (void)keyboard; (void)serial; (void)surface;
}

static void keyboard_key(void *data, struct wl_keyboard *keyboard, uint32_t serial,
                         uint32_t time, uint32_t key, uint32_t state)
{
    struct app *app = data;
    (void)keyboard; (void)serial; (void)time; (void)key; (void)state;
    app->count.keyboard_key++;
}

static void keyboard_modifiers(void *data, struct wl_keyboard *keyboard, uint32_t serial,
                               uint32_t depressed, uint32_t latched, uint32_t locked,
                               uint32_t group)
{
    (void)data; (void)keyboard; (void)serial; (void)depressed;
    (void)latched; (void)locked; (void)group;
}

static void keyboard_repeat(void *data, struct wl_keyboard *keyboard, int32_t rate,
                            int32_t delay)
{
    (void)data; (void)keyboard; (void)rate; (void)delay;
}

static const struct wl_keyboard_listener keyboard_listener =
{
    keyboard_keymap,
    keyboard_enter,
    keyboard_leave,
    keyboard_key,
    keyboard_modifiers,
    keyboard_repeat,
};

static void seat_capabilities(void *data, struct wl_seat *seat, uint32_t capabilities)
{
    struct app *app = data;
    if ((capabilities & WL_SEAT_CAPABILITY_KEYBOARD) && !app->keyboard)
    {
        app->keyboard = wl_seat_get_keyboard(seat);
        if (wl_keyboard_add_listener(app->keyboard, &keyboard_listener, app) < 0)
            fprintf(stderr, "keyboard listener registration failed\n");
    }
}

static void seat_name(void *data, struct wl_seat *seat, const char *name)
{
    (void)data; (void)seat; (void)name;
}

static const struct wl_seat_listener seat_listener =
{
    seat_capabilities,
    seat_name,
};

static void xdg_surface_configure(void *data, struct xdg_surface *surface, uint32_t serial)
{
    struct app *app = data;
    app->count.xdg_configure++;
    xdg_surface_ack_configure(surface, serial);
    app->configured = 1;
    if (app->buffer)
    {
        wl_surface_attach(app->surface, app->buffer, 0, 0);
        wl_surface_damage(app->surface, 0, 0, 64, 64);
        wl_surface_commit(app->surface);
    }
}

static const struct xdg_surface_listener xdg_surface_listener =
{
    xdg_surface_configure,
};

static void toplevel_configure(void *data, struct xdg_toplevel *toplevel,
                               int32_t width, int32_t height, struct wl_array *states)
{
    (void)data; (void)toplevel; (void)width; (void)height; (void)states;
}

static void toplevel_close(void *data, struct xdg_toplevel *toplevel)
{
    (void)data; (void)toplevel;
}

static const struct xdg_toplevel_listener toplevel_listener =
{
    toplevel_configure,
    toplevel_close,
    NULL,
    NULL,
};

static struct wl_buffer *make_buffer(struct app *app)
{
    char name[64];
    struct wl_shm_pool *pool;
    struct wl_buffer *buffer;
    uint32_t *pixels;
    int fd;
    const int width = 64, height = 64, stride = width * 4, size = stride * height;

    snprintf(name, sizeof(name), "/mgs2-wayland-abi-%ld", (long)getpid());
    fd = shm_open(name, O_RDWR | O_CREAT | O_EXCL, 0600);
    if (fd < 0) return NULL;
    shm_unlink(name);
    if (ftruncate(fd, size) < 0) { close(fd); return NULL; }
    pixels = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (pixels == MAP_FAILED) { close(fd); return NULL; }
    for (int i = 0; i < width * height; ++i) pixels[i] = 0xff204060u;
    munmap(pixels, size);
    pool = wl_shm_create_pool(app->shm, fd, size);
    close(fd);
    if (!pool) return NULL;
    buffer = wl_shm_pool_create_buffer(pool, 0, width, height, stride,
                                       WL_SHM_FORMAT_XRGB8888);
    wl_shm_pool_destroy(pool);
    return buffer;
}

static int app_init(struct app *app)
{
    memset(app, 0, sizeof(*app));
    app->display = wl_display_connect(NULL);
    if (!app->display) return -1;
    app->registry = wl_display_get_registry(app->display);
    if (!app->registry || wl_registry_add_listener(app->registry, &registry_listener, app) < 0)
        return -1;
    if (wl_display_roundtrip(app->display) < 0) return -1;
    if (app->xdg_wm_base)
        xdg_wm_base_add_listener(app->xdg_wm_base, &xdg_wm_base_listener, app);
    if (app->seat)
        wl_seat_add_listener(app->seat, &seat_listener, app);
    if (wl_display_roundtrip(app->display) < 0) return -1;
    return 0;
}

static int dispatch_for(struct app *app, int seconds)
{
    struct timespec start, now;
    int fd = wl_display_get_fd(app->display);
    clock_gettime(CLOCK_MONOTONIC, &start);
    for (;;)
    {
        struct pollfd pfd = { fd, POLLIN, 0 };
        long elapsed;
        while (wl_display_prepare_read(app->display) != 0)
            if (wl_display_dispatch_pending(app->display) < 0) return -1;
        if (wl_display_flush(app->display) < 0 && errno != EAGAIN)
        {
            wl_display_cancel_read(app->display);
            return -1;
        }
        if (poll(&pfd, 1, 100) > 0 && (pfd.revents & POLLIN))
        {
            if (wl_display_read_events(app->display) < 0) return -1;
            if (wl_display_dispatch_pending(app->display) < 0) return -1;
        }
        else wl_display_cancel_read(app->display);
        clock_gettime(CLOCK_MONOTONIC, &now);
        elapsed = now.tv_sec - start.tv_sec;
        if (elapsed >= seconds) return 0;
    }
}

static void print_result(const char *mode, const struct app *app, int rc,
                         int first_ten, int eleventh)
{
    printf("RESULT mode=%s rc=%d data_offer=%u offer=%u selection=%u finished=%u "
           "source_send=%u source_cancelled=%u xdg_configure=%u keyboard_keymap=%u "
           "keyboard_key=%u first_ten=%d eleventh=%d\n",
           mode, rc, app->count.data_offer, app->count.offer, app->count.selection,
           app->count.finished, app->count.source_send, app->count.source_cancelled,
           app->count.xdg_configure, app->count.keyboard_keymap,
           app->count.keyboard_key, first_ten, eleventh);
    fflush(stdout);
}

static int run_observer(struct app *app, int seconds)
{
    if (!app->data_manager || !app->seat) return 2;
    app->data_device = zwlr_data_control_manager_v1_get_data_device(app->data_manager,
                                                                    app->seat);
    if (!app->data_device || zwlr_data_control_device_v1_add_listener(
            app->data_device, &device_listener, app) < 0) return 3;
    return dispatch_for(app, seconds);
}

static int run_source(struct app *app, int seconds)
{
    if (!app->data_manager || !app->seat) return 2;
    app->data_device = zwlr_data_control_manager_v1_get_data_device(app->data_manager,
                                                                    app->seat);
    if (!app->data_device || zwlr_data_control_device_v1_add_listener(
            app->data_device, &device_listener, app) < 0) return 3;
    app->data_source = zwlr_data_control_manager_v1_create_data_source(app->data_manager);
    if (!app->data_source || zwlr_data_control_source_v1_add_listener(
            app->data_source, &source_listener, app) < 0) return 4;
    zwlr_data_control_source_v1_offer(app->data_source, "text/plain;charset=utf-8");
    zwlr_data_control_device_v1_set_selection(app->data_device, app->data_source);
    return dispatch_for(app, seconds);
}

static int run_receive(struct app *app)
{
    int pipefd[2], rc;
    char buffer[128];
    ssize_t got;

    rc = run_observer(app, 1);
    if (rc || !app->selection_offer || !app->offered_text) return rc ? rc : 5;
    if (pipe(pipefd) < 0) return 6;
    zwlr_data_control_offer_v1_receive(app->selection_offer,
                                      "text/plain;charset=utf-8", pipefd[1]);
    close(pipefd[1]);
    if (wl_display_flush(app->display) < 0) { close(pipefd[0]); return 7; }
    got = read(pipefd[0], buffer, sizeof(buffer));
    close(pipefd[0]);
    return got > 0 ? 0 : 8;
}

static int run_window(struct app *app, int seconds)
{
    if (!app->compositor || !app->shm || !app->xdg_wm_base) return 2;
    app->buffer = make_buffer(app);
    app->surface = wl_compositor_create_surface(app->compositor);
    if (!app->buffer || !app->surface) return 3;
    app->xdg_surface = xdg_wm_base_get_xdg_surface(app->xdg_wm_base, app->surface);
    app->xdg_toplevel = xdg_surface_get_toplevel(app->xdg_surface);
    if (!app->xdg_surface || !app->xdg_toplevel) return 4;
    if (xdg_surface_add_listener(app->xdg_surface, &xdg_surface_listener, app) < 0)
        return 5;
    xdg_toplevel_add_listener(app->xdg_toplevel, &toplevel_listener, app);
    xdg_toplevel_set_title(app->xdg_toplevel, "MGS2 Wayland ABI probe");
    wl_surface_commit(app->surface);
    return dispatch_for(app, seconds);
}

static void exhaust_device_data_offer(void *data, struct zwlr_data_control_device_v1 *d,
                                      struct zwlr_data_control_offer_v1 *offer)
{
    struct app *app = data;
    (void)d;
    app->count.data_offer++;
    zwlr_data_control_offer_v1_add_listener(offer, &offer_listener, app);
}

static const struct zwlr_data_control_device_v1_listener exhaust_device_listener[11] =
{
    { exhaust_device_data_offer, device_selection, device_finished, NULL },
    { exhaust_device_data_offer, device_selection, device_finished, NULL },
    { exhaust_device_data_offer, device_selection, device_finished, NULL },
    { exhaust_device_data_offer, device_selection, device_finished, NULL },
    { exhaust_device_data_offer, device_selection, device_finished, NULL },
    { exhaust_device_data_offer, device_selection, device_finished, NULL },
    { exhaust_device_data_offer, device_selection, device_finished, NULL },
    { exhaust_device_data_offer, device_selection, device_finished, NULL },
    { exhaust_device_data_offer, device_selection, device_finished, NULL },
    { exhaust_device_data_offer, device_selection, device_finished, NULL },
    { exhaust_device_data_offer, device_selection, device_finished, NULL },
};

static void wl_source_target(void *data, struct wl_data_source *source, const char *mime)
{ (void)data; (void)source; (void)mime; }
static void wl_source_send(void *data, struct wl_data_source *source, const char *mime, int32_t fd)
{ (void)data; (void)source; (void)mime; if (fd >= 0) close(fd); }
static void wl_source_cancelled(void *data, struct wl_data_source *source)
{ (void)data; (void)source; }
static void wl_source_drop(void *data, struct wl_data_source *source)
{ (void)data; (void)source; }
static void wl_source_finished(void *data, struct wl_data_source *source)
{ (void)data; (void)source; }
static void wl_source_action(void *data, struct wl_data_source *source, uint32_t action)
{ (void)data; (void)source; (void)action; }

static const struct wl_data_source_listener exhaust_wl_source_listener[11] =
{
#define SOURCE_LISTENER { wl_source_target, wl_source_send, wl_source_cancelled, \
                          wl_source_drop, wl_source_finished, wl_source_action }
    SOURCE_LISTENER, SOURCE_LISTENER, SOURCE_LISTENER, SOURCE_LISTENER,
    SOURCE_LISTENER, SOURCE_LISTENER, SOURCE_LISTENER, SOURCE_LISTENER,
    SOURCE_LISTENER, SOURCE_LISTENER, SOURCE_LISTENER,
#undef SOURCE_LISTENER
};

static int run_exhaust(struct app *app, int *first_ten, int *eleventh)
{
    struct zwlr_data_control_device_v1 *devices[11] = {0};
    struct wl_data_source *sources[11] = {0};
    int i, rc, ok = 1;

    *first_ten = 0;
    *eleventh = 0;
    if (!app->data_manager || !app->seat || !app->wl_data_manager) return 2;
    for (i = 0; i < 11; ++i)
    {
        devices[i] = zwlr_data_control_manager_v1_get_data_device(app->data_manager,
                                                                  app->seat);
        rc = zwlr_data_control_device_v1_add_listener(devices[i],
                &exhaust_device_listener[i], app);
        if (i < 10 && rc == 0) (*first_ten)++;
        if (i == 10) *eleventh = rc;
    }
    if (*first_ten != 10 || *eleventh != -1) ok = 0;

    /* A separate listener class gets its own ten slots. This covers Wine's
     * standard wl_data_source fallback even though Sway selects wlr-data-control. */
    *first_ten = 0;
    *eleventh = 0;
    for (i = 0; i < 11; ++i)
    {
        sources[i] = wl_data_device_manager_create_data_source(app->wl_data_manager);
        rc = wl_data_source_add_listener(sources[i], &exhaust_wl_source_listener[i], app);
        if (i < 10 && rc == 0) (*first_ten)++;
        if (i == 10) *eleventh = rc;
    }
    if (*first_ten != 10 || *eleventh != -1) ok = 0;
    wl_display_flush(app->display);
    return ok ? 0 : 9;
}

int main(int argc, char **argv)
{
    struct app app;
    const char *mode;
    int seconds = 4, rc, first_ten = -1, eleventh = 0;

    if (argc < 2)
    {
        fprintf(stderr, "usage: %s observer|source|receive|window|exhaust [seconds]\n", argv[0]);
        return 64;
    }
    mode = argv[1];
    if (argc > 2) seconds = atoi(argv[2]);
    if (seconds < 1) seconds = 1;
    if (app_init(&app) < 0)
    {
        fprintf(stderr, "Wayland initialization failed\n");
        return 65;
    }

    if (!strcmp(mode, "observer")) rc = run_observer(&app, seconds);
    else if (!strcmp(mode, "source")) rc = run_source(&app, seconds);
    else if (!strcmp(mode, "receive")) rc = run_receive(&app);
    else if (!strcmp(mode, "window")) rc = run_window(&app, seconds);
    else if (!strcmp(mode, "exhaust")) rc = run_exhaust(&app, &first_ten, &eleventh);
    else rc = 64;

    print_result(mode, &app, rc, first_ten, eleventh);
    return rc;
}

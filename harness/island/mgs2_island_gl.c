/* mgs2 island: is the GL context reachable from native code?
 *
 * The island runs inside Box86, on the same OS thread as the renderer, in a
 * process where libmali is already loaded natively. If an EGL context is
 * current on that thread, native code should observe exactly the GL state the
 * emulated Wine side observes. This probe reads a handful of context values
 * through the native driver so the two views can be compared.
 *
 * Read-only by construction: only glGetIntegerv and glGetError are used, so a
 * negative result cannot damage the frame. */
#include <dlfcn.h>
#include <stddef.h>

#define GL_NO_ERROR                     0
#define GL_CURRENT_PROGRAM              0x8B8D
#define GL_ARRAY_BUFFER_BINDING         0x8894
#define GL_ELEMENT_ARRAY_BUFFER_BINDING 0x8895
#define GL_VIEWPORT                     0x0BA2
#define GL_ACTIVE_TEXTURE               0x84E0

typedef unsigned int GLenum;
typedef int GLint;

static void (*p_glGetIntegerv)(GLenum, GLint *);
static GLenum (*p_glGetError)(void);
static int resolved;

static void mgs2_island_gl_resolve(void)
{
    static const char *names[] = { "libGLESv2.so.2", "libGLESv2.so",
                                   "libmali.so.1", "libmali.so", NULL };
    int i;

    if (resolved)
        return;
    resolved = 1;
    /* RTLD_NOLOAD first: the driver is already in the process, and pulling in a
     * second copy would be a different context. */
    for (i = 0; names[i]; ++i)
    {
        void *h = dlopen(names[i], RTLD_LAZY | RTLD_NOLOAD);

        if (!h)
            continue;
        if (!p_glGetIntegerv)
            p_glGetIntegerv = dlsym(h, "glGetIntegerv");
        if (!p_glGetError)
            p_glGetError = dlsym(h, "glGetError");
        if (p_glGetIntegerv && p_glGetError)
            return;
    }
}

/* out[0] resolved flag, [1] program, [2] array buffer, [3] element buffer,
 * [4] active texture, [5..8] viewport, [9] glGetError result. */
void mgs2_island_gl_probe_impl(unsigned int *out)
{
    GLint v[4] = { 0, 0, 0, 0 };

    if (!out)
        return;
    mgs2_island_gl_resolve();
    out[0] = p_glGetIntegerv && p_glGetError;
    if (!out[0])
        return;

    p_glGetIntegerv(GL_CURRENT_PROGRAM, v);              out[1] = (unsigned)v[0];
    p_glGetIntegerv(GL_ARRAY_BUFFER_BINDING, v);         out[2] = (unsigned)v[0];
    p_glGetIntegerv(GL_ELEMENT_ARRAY_BUFFER_BINDING, v); out[3] = (unsigned)v[0];
    p_glGetIntegerv(GL_ACTIVE_TEXTURE, v);               out[4] = (unsigned)v[0];
    p_glGetIntegerv(GL_VIEWPORT, v);
    out[5] = (unsigned)v[0]; out[6] = (unsigned)v[1];
    out[7] = (unsigned)v[2]; out[8] = (unsigned)v[3];
    out[9] = (unsigned)p_glGetError();
}

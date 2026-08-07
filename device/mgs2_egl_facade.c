/*
 * mgs2_egl_facade -- a three-rule EGL shim for bringing MGS2 up on Hangover.
 *
 * The problem it solves, measured on the device (brief #32):
 *
 *   Wine 11.0's generic EGL backend, win32u/opengl.c:478, keeps only configs
 *   whose EGL_RENDERABLE_TYPE has EGL_OPENGL_BIT:
 *       if (render & EGL_OPENGL_BIT) configs[j++] = configs[i];
 *   Mali on this unit reports render = 0x45, i.e. ES | ES2 | ES3 and no desktop
 *   GL bit at all, so every config is dropped, ChoosePixelFormat has nothing to
 *   return, wined3d cannot get a context and Direct3DCreate8 fails.
 *
 *   The old Box86 stack never hit this because its deployed win32u_glfuncs3.so
 *   carried the fix as a binary-only change that was never in the source tree --
 *   the handoff warns in writing that rebuilding it silently loses ES2/ES3 config
 *   acceptance and the EGL_CONTEXT_MAJOR_VERSION 3 default. This shim reproduces
 *   exactly those two behaviours plus the API binding, without touching Wine, so
 *   bring-up does not depend on rebuilding the module that trap is attached to.
 *
 * Why a shim and not a Wine patch, for now: it keeps stock Hangover completely
 * intact, including its winewayland.drv, which already does the native
 * wl_egl_window -> eglCreateWindowSurface -> eglSwapBuffers path. That path is
 * the whole point of moving to Hangover; the old readback presenter must not come
 * back. Once a frame exists, these three rules belong in win32u/opengl.c and the
 * shim can go away.
 *
 * Design: this object DT_NEEDEDs the real libmali, and defines only the three
 * entry points it changes. dlsym() on a dlopen handle searches the object's
 * dependencies too, so every other egl* and gl* symbol resolves straight through
 * to Mali with no forwarding code and no list to maintain.
 *
 *   aarch64-linux-gnu-gcc -shared -fPIC -O2 -o libEGL.so.1 mgs2_egl_facade.c \
 *       -L/path/to/mali -l:libmali.so.1 -ldl
 *
 *   LD_LIBRARY_PATH=<dir with this libEGL.so.1>:$LD_LIBRARY_PATH wine ...
 *
 * MGS2_EGL_FACADE_LOG=0 silences it. It logs one line per distinct event, never
 * per call: on this device per-call logging has repeatedly cost more than it
 * measured.
 */

#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Declared locally so the shim needs no EGL headers or target sysroot. */
typedef int            EGLint;
typedef unsigned int   EGLBoolean;
typedef void          *EGLDisplay;
typedef void          *EGLConfig;
typedef void          *EGLContext;

#define EGL_RENDERABLE_TYPE        0x3040
#define EGL_NONE                   0x3038
#define EGL_OPENGL_ES_BIT          0x0001
#define EGL_OPENGL_ES2_BIT         0x0004
#define EGL_OPENGL_BIT             0x0008
#define EGL_OPENGL_ES3_BIT_KHR     0x0040
#define EGL_OPENGL_ES_API          0x30A0
#define EGL_OPENGL_API             0x30A2
#define EGL_CONTEXT_MAJOR_VERSION  0x3098   /* == EGL_CONTEXT_CLIENT_VERSION */

/* The real implementations.
 *
 * These cannot be plain extern declarations: this object *defines* the same four
 * names so that it wins the lookup, and a direct call would then resolve to
 * itself and recurse forever. RTLD_NEXT is the way out -- it starts the search
 * after this object, which is exactly where libmali sits, since libmali is this
 * object's own DT_NEEDED dependency. That dependency is also what lets every
 * other egl* and gl* symbol resolve straight through with no forwarding code.
 *
 * MGS2_EGL_FACADE_REAL can name the real library explicitly if RTLD_NEXT ever
 * comes up empty.
 */
typedef EGLBoolean (*fn_get_config_attrib)( EGLDisplay, EGLConfig, EGLint, EGLint * );
typedef EGLBoolean (*fn_bind_api)( EGLint );
typedef EGLContext (*fn_create_context)( EGLDisplay, EGLConfig, EGLContext, const EGLint * );
typedef void      *(*fn_get_proc_address)( const char * );

static void *real_symbol( const char *name )
{
    void *fn = dlsym( RTLD_NEXT, name );

    if (!fn)
    {
        static void *handle;
        const char *path = getenv( "MGS2_EGL_FACADE_REAL" );

        if (!handle) handle = dlopen( path ? path : "libmali.so.1", RTLD_LAZY | RTLD_GLOBAL );
        if (handle) fn = dlsym( handle, name );
    }
    if (!fn) fprintf( stderr, "MGS2EGL: cannot resolve real %s\n", name );
    return fn;
}

#define REAL( var, type, name )                                  \
    static type var;                                             \
    if (!var) var = (type)real_symbol( name );                   \
    if (!var) return 0;

static int facade_logging( void )
{
    static int on = -1;

    if (on < 0)
    {
        const char *e = getenv( "MGS2_EGL_FACADE_LOG" );
        on = !e || *e != '0';
    }
    return on;
}

/* One line per distinct event. The `seen` flag is what keeps a per-call hook from
 * turning into a per-call log. */
#define FACADE_ONCE( flag, ... )                            \
    do {                                                    \
        static int flag##_seen;                             \
        if (facade_logging() && !flag##_seen)                \
        {                                                   \
            flag##_seen = 1;                                \
            fprintf( stderr, "MGS2EGL: " __VA_ARGS__ );     \
            fflush( stderr );                               \
        }                                                   \
    } while (0)

/* Rule 1. Tell Wine a GLES-capable config is also desktop-GL capable, so its
 * filter keeps it. The EGLConfig handle itself is untouched and still the real
 * Mali one, so eglCreateWindowSurface later gets a genuinely ES3-capable config.
 * Only what Wine is told changes, and only for this one attribute. */
EGLBoolean mgs2_facade_eglGetConfigAttrib( EGLDisplay dpy, EGLConfig config,
        EGLint attribute, EGLint *value )
{
    REAL( real, fn_get_config_attrib, "eglGetConfigAttrib" );
    EGLBoolean ret = real( dpy, config, attribute, value );

    if (ret && value && attribute == EGL_RENDERABLE_TYPE
            && (*value & (EGL_OPENGL_ES3_BIT_KHR | EGL_OPENGL_ES2_BIT))
            && !(*value & EGL_OPENGL_BIT))
    {
        EGLint was = *value;

        *value |= EGL_OPENGL_BIT;
        FACADE_ONCE( cfg, "config renderable real=0x%x -> wine=0x%x\n", was, *value );
    }
    return ret;
}

/* Rule 2. Wine binds EGL_OPENGL_API because it believes it has a desktop GL
 * config. Creating a GLES context requires the ES API to be bound first. */
EGLBoolean mgs2_facade_eglBindAPI( EGLint api )
{
    if (api == EGL_OPENGL_API)
    {
        FACADE_ONCE( api, "eglBindAPI OPENGL -> OPENGL_ES\n" );
        api = EGL_OPENGL_ES_API;
    }
    REAL( real, fn_bind_api, "eglBindAPI" );
    return real( api );
}

/* Rule 3. With the ES API bound and no version asked for, EGL is entitled to
 * hand back a GLES 1.1 context, and then everything above it degrades to the
 * legacy path. The old working binary defaulted to major 3 for exactly this
 * reason; 3 rather than 3.2 on purpose -- that is the value this Mali was already
 * proven to answer with "OpenGL ES 3.2". An explicit request from the caller is
 * always left alone. */
EGLContext mgs2_facade_eglCreateContext( EGLDisplay dpy, EGLConfig config,
        EGLContext share, const EGLint *attrib_list )
{
    static const EGLint gles3[] = { EGL_CONTEXT_MAJOR_VERSION, 3, EGL_NONE };
    int has_version = 0;

    if (attrib_list)
    {
        EGLint i;

        for (i = 0; attrib_list[i] != EGL_NONE; i += 2)
            if (attrib_list[i] == EGL_CONTEXT_MAJOR_VERSION) has_version = 1;
    }

    if (!has_version)
    {
        FACADE_ONCE( ctx, "context without a major version -> GLES 3\n" );
        attrib_list = gles3;
    }
    REAL( real, fn_create_context, "eglCreateContext" );
    return real( dpy, config, share, attrib_list );
}

/* Wine takes only a couple of symbols by dlsym and asks eglGetProcAddress for the
 * rest, so the three rules have to be reachable through both routes. */
void *mgs2_facade_eglGetProcAddress( const char *name )
{
    if (name)
    {
        if (!strcmp( name, "eglGetConfigAttrib" )) return (void *)mgs2_facade_eglGetConfigAttrib;
        if (!strcmp( name, "eglBindAPI" ))         return (void *)mgs2_facade_eglBindAPI;
        if (!strcmp( name, "eglCreateContext" ))   return (void *)mgs2_facade_eglCreateContext;
    }
    REAL( real, fn_get_proc_address, "eglGetProcAddress" );
    return real( name );
}

/* Export the four under their real names, overriding Mali's because this object
 * comes first in the lookup order. */
EGLBoolean eglGetConfigAttrib( EGLDisplay dpy, EGLConfig config, EGLint attribute, EGLint *value )
    __attribute__((alias("mgs2_facade_eglGetConfigAttrib")));
EGLBoolean eglBindAPI( EGLint api )
    __attribute__((alias("mgs2_facade_eglBindAPI")));
EGLContext eglCreateContext( EGLDisplay dpy, EGLConfig config, EGLContext share, const EGLint *attrib_list )
    __attribute__((alias("mgs2_facade_eglCreateContext")));
void *eglGetProcAddress( const char *name )
    __attribute__((alias("mgs2_facade_eglGetProcAddress")));

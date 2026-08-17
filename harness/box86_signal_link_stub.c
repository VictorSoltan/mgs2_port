/*
 * Link-only libc symbols for box86_mutex_signal_stress.c.  Box86 substitutes
 * its wrapped native libc on the device; this file is never deployed.
 */

void (*signal(int sig, void (*handler)(int)))(int)
{
    (void)sig;
    return handler;
}

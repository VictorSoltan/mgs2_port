/*
 * Link-only symbols for box86_mutex_first_use_stress.c.  The resulting i386
 * executable names libpthread.so.0 in DT_NEEDED; on the device Box86 replaces
 * it with its wrapped native pthread implementation.  Do not deploy this stub.
 */

int pthread_create(void) { return 0; }
int pthread_join(void) { return 0; }
int pthread_mutex_lock(void) { return 0; }
int pthread_mutex_unlock(void) { return 0; }

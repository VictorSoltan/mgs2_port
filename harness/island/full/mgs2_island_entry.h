/* Island entry/leave bracket.
 *
 * Native island code must run against the emu it was entered with -- for the
 * guest TEB now, and for reverse guest callbacks once the indirect-target
 * resolver needs one. Nesting is real: an island function can route back out
 * and in again, so this saves and restores rather than assigning. */
#ifndef __MGS2_ISLAND_ENTRY_H_
#define __MGS2_ISLAND_ENTRY_H_

#include "x86emu.h"

extern __thread x86emu_t *mgs2_island_emu;
extern __thread unsigned int mgs2_island_depth;

#define MGS2_ISLAND_ENTER(emu) \
    x86emu_t *mgs2_saved_emu = mgs2_island_emu; \
    mgs2_island_emu = (emu); \
    ++mgs2_island_depth

#define MGS2_ISLAND_LEAVE() \
    --mgs2_island_depth; \
    mgs2_island_emu = mgs2_saved_emu

#endif //__MGS2_ISLAND_ENTRY_H_

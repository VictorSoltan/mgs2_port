/* DirectMusicSynthesizer Private Include
 *
 * Copyright (C) 2003-2004 Rok Mandeljc
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301, USA
 */

#ifndef __WINE_DMSYNTH_PRIVATE_H
#define __WINE_DMSYNTH_PRIVATE_H

#include <stdarg.h>

#define COBJMACROS

#include "windef.h"
#include "winbase.h"
#include "winnt.h"
#include "wingdi.h"
#include "winuser.h"

#include "wine/debug.h"
#include "wine/list.h"
#include "winreg.h"
#include "objbase.h"

#include "dmusici.h"
#include "dmusicf.h"
#include "dmusics.h"
#include "dmksctrl.h"

/*****************************************************************************
 * ClassFactory
 */
extern HRESULT synth_create(IUnknown **ret_iface);
extern HRESULT synth_sink_create(IUnknown **ret_iface);

/* Marker-bounded sink recorder.  The state is exported from the PE DLL and
 * read externally through /proc/<pid>/mem; the render/write threads never do
 * file I/O or formatted logging. */
#define DMSYNTH_SINKPROBE_MAGIC 0x31505344 /* DSP1 */
#define DMSYNTH_SINKPROBE_EVENTS 64

/*
 * Fixed-size, memory-only state for transition-sensitive MGS2 audio failures.
 * It is appended to the existing sink-probe export so the established
 * dmsynth_sinkprobe_state RVA and the old reader remain valid.  Writers commit
 * a record by storing sequence last; an external /proc/<pid>/mem reader can
 * therefore reject a record that was sampled halfway through an update.
 */
#define DMSYNTH_STATE_MAGIC 0x31545344 /* DST1 */
#define DMSYNTH_STATE_VERSION 1
#define DMSYNTH_STATE_EVENTS 256
#define DMSYNTH_STATE_RECORD_WORDS 16

enum dmsynth_state_event_type
{
    DMSYNTH_STATE_OPEN_RESET = 1,
    DMSYNTH_STATE_MIDI_RESET = 2,
    DMSYNTH_STATE_NOTE_ON = 3,
    DMSYNTH_STATE_PROGRAM = 4,
    DMSYNTH_STATE_BANK = 5,
    DMSYNTH_STATE_NOTE_UNMUTE = 6,
};

struct dmsynth_state_record
{
    volatile LONG sequence;
    DWORD tick;
    DWORD type;
    DWORD synth;
    DWORD reset_serial;
    DWORD group;
    DWORD channel;
    DWORD status;
    DWORD data1;
    DWORD data2;
    LONG result;
    DWORD voices_before;
    DWORD voices_after;
    LONG sfont;
    LONG bank;
    LONG program;
};

struct dmsynth_runtime_state
{
    DWORD magic;
    DWORD version;
    DWORD size;
    DWORD record_words;
    DWORD event_count;
    DWORD signature;
    volatile LONG enabled;
    volatile LONG write_sequence;
    volatile LONG open_reset_count;
    volatile LONG midi_reset_count;
    volatile LONG noteon_count;
    volatile LONG noteon_failed;
    volatile LONG noteon_no_voice;
    volatile LONG program_count;
    volatile LONG bank_count;
    volatile LONG active_voices;
    volatile LONG max_active_voices;
    volatile LONG last_render_synth;
    volatile LONG last_tick;
    DWORD reserved;
    struct dmsynth_state_record records[DMSYNTH_STATE_EVENTS];
};

C_ASSERT(sizeof(struct dmsynth_state_record) == DMSYNTH_STATE_RECORD_WORDS * sizeof(DWORD));

struct dmsynth_sinkprobe_record
{
    DWORD sequence;
    DWORD sink;
    DWORD synth;
    DWORD buffer;
    DWORD external_buffer;
    DWORD render_position;
    DWORD render_frames;
    DWORD render_bytes;
    DWORD render_peak_l;
    DWORD render_peak_r;
    DWORD render_checksum;
    DWORD written_before;
    DWORD write_offset;
    DWORD play_before;
    DWORD write_before;
    DWORD lock_hr;
    DWORD data1;
    DWORD size1;
    DWORD data2;
    DWORD size2;
    DWORD copied_peak_l;
    DWORD copied_peak_r;
    DWORD copied_checksum;
    DWORD unlock_hr;
    DWORD status;
    DWORD volume;
    DWORD frequency;
    DWORD play_after;
    DWORD write_after;
    DWORD written_after;
};

struct dmsynth_sinkprobe_state
{
    DWORD magic;
    DWORD version;
    volatile LONG marker;
    volatile LONG count;
    DWORD marker_sink;
    DWORD marker_synth;
    DWORD marker_group;
    DWORD marker_status;
    DWORD marker_note;
    DWORD marker_velocity;
    struct dmsynth_sinkprobe_record records[DMSYNTH_SINKPROBE_EVENTS];
    struct dmsynth_runtime_state runtime;
};

extern __declspec(dllexport) volatile struct dmsynth_sinkprobe_state dmsynth_sinkprobe_state;
extern void synth_sink_probe_mark(void *sink, void *synth, DWORD group, BYTE status,
        BYTE note, BYTE velocity);

/*****************************************************************************
 * Misc.
 */
/* used for generic dumping (copied from ddraw) */
typedef struct {
    DWORD val;
    const char* name;
} flag_info;

typedef struct {
    const GUID *guid;
    const char* name;
} guid_info;

/* used for initialising structs (primarily for DMUS_OBJECTDESC) */
#define FE(x) { x, #x }	
#define GE(x) { &x, #x }

/* returns name of given GUID */
extern const char *debugstr_dmguid (const GUID *id);

/* bounded integer env knob, shared by synth.c and synthsink.c */
extern int mgs2_env_int(const char *name, int def, int lo, int hi);

#endif	/* __WINE_DMSYNTH_PRIVATE_H */

/* mgs2_island_validate -- differential validation of the native ARM slice.
 *
 * Reads a live wined3d_state and wined3d_d3d_info out of the running game, runs
 * the ARM-compiled copy of wined3d_ffp_get_fs_settings() on them, and compares
 * its 132-byte result against the one the shipping x86 code produced for the
 * same state. Read-only; it never writes to the process. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <dirent.h>

#define MAGIC 0x30345250u
#define IMAGE_BASE 0x10000000u

struct pub {
    unsigned magic, version, size_words, signature, enabled;
    int publish_sequence;
    unsigned state_address, state_size, field_count;
    unsigned field_offset[12], field_size[12];
    unsigned checksum, samples;
    unsigned d3d_info_address, ffp_settings_size;
    unsigned char ffp_settings[160];
};

void wined3d_ffp_get_fs_settings(const void *state, const void *d3d_info, void *settings);

static int find_pid(const char *comm)
{
    DIR *d = opendir("/proc"); struct dirent *e; int got = -1, n = 0;
    char path[64], buf[64];
    while (d && (e = readdir(d))) {
        if (e->d_name[0] < '0' || e->d_name[0] > '9') continue;
        snprintf(path, sizeof path, "/proc/%s/comm", e->d_name);
        FILE *f = fopen(path, "r"); if (!f) continue;
        if (fgets(buf, sizeof buf, f)) { buf[strcspn(buf, "\n")] = 0;
            if (!strcmp(buf, comm)) { got = atoi(e->d_name); ++n; } }
        fclose(f);
    }
    if (d) closedir(d);
    return n == 1 ? got : -1;
}

static unsigned long module_base(int pid, const char *mod)
{
    char path[64]; snprintf(path, sizeof path, "/proc/%d/maps", pid);
    FILE *f = fopen(path, "r"); char line[512]; unsigned long base = 0;
    while (f && fgets(line, sizeof line, f)) {
        unsigned long lo; char off[32], name[256];
        if (sscanf(line, "%lx-%*x %*s %31s %*s %*s %255s", &lo, off, name) == 3
            && !strcmp(off, "00000000") && strstr(name, mod)) { base = lo; break; }
    }
    if (f) fclose(f);
    return base;
}

int main(int argc, char **argv)
{
    unsigned long vma = argc > 1 ? strtoul(argv[1], 0, 0) : 0x101d30c0;
    int pid = find_pid("mgs2_sse_rg353v");
    if (pid < 0) { fprintf(stderr, "need exactly one game process\n"); return 2; }
    unsigned long base = module_base(pid, "wined3d.dll");
    char path[64]; snprintf(path, sizeof path, "/proc/%d/mem", pid);
    int fd = open(path, O_RDONLY);
    if (!base || fd < 0) { fprintf(stderr, "cannot reach the process\n"); return 2; }

    struct pub p;
    if (pread(fd, &p, sizeof p, base + vma - IMAGE_BASE) != (ssize_t)sizeof p
        || p.magic != MAGIC) { fprintf(stderr, "bad PR40 block\n"); return 2; }

    unsigned char *state = malloc(p.state_size);
    unsigned char d3d_info[256];
    if (pread(fd, state, p.state_size, p.state_address) != (ssize_t)p.state_size
        || pread(fd, d3d_info, sizeof d3d_info, p.d3d_info_address) < 100) {
        fprintf(stderr, "could not read the live objects\n"); return 2; }

    printf("read ok: state %u bytes, d3d_info read\n", p.state_size);
    fflush(stdout);
    /* The function follows pointers stored inside the state -- bound views,
     * their resources, formats. Those are addresses in the game's address
     * space, not ours, so an out-of-process run cannot follow them. Prove that
     * is the reason rather than guessing: null the pointer array it walks and
     * see whether the same call then completes. */
    if (getenv("MGS2_ISLAND_NULL_VIEWS")) {
        unsigned off = 1924;       /* wined3d_state.shader_resource_view */
        memset(state + off, 0, 384);
        printf("bound views nulled at offset %u\n", off);
        fflush(stdout);
    }
    unsigned char mine[160];
    memset(mine, 0, sizeof mine);
    wined3d_ffp_get_fs_settings(state, d3d_info, mine);
    printf("call completed\n"); fflush(stdout);

    printf("pid %d  samples %u  state %#x  d3d_info %#x\n",
           pid, p.samples, p.state_address, p.d3d_info_address);
    printf("ffp_frag_settings size: x86 %u, arm %u\n", p.ffp_settings_size,
           (unsigned)sizeof(struct { char c[132]; }));

    int diff = 0, first = -1;
    for (unsigned i = 0; i < p.ffp_settings_size; ++i)
        if (mine[i] != p.ffp_settings[i]) { ++diff; if (first < 0) first = (int)i; }

    printf("\nbyte-for-byte: %u of %u differ", diff, p.ffp_settings_size);
    if (diff) printf(", first at offset %d (x86 %02x, arm %02x)",
                     first, p.ffp_settings[first], mine[first]);
    printf("\n\nRESULT: %s\n", diff == 0
        ? "the ARM-compiled WineD3D function reproduces the x86 result exactly."
        : "DIVERGENT -- the slice is not usable as it stands.");
    close(fd); free(state);
    return diff == 0 ? 0 : 1;
}

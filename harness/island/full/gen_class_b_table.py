#!/usr/bin/env python3
"""Generate the class-B mapping: guest WineD3D RVA -> native symbol ID.

The indirect-call census showed that essentially every hot dispatch inside the
island's closure targets a function in wined3d.dll itself -- 21,433,346 of
21,433,463 calls, one target per site. Those functions all have ARM counterparts
by construction, because the island compiles the same 32 sources. So the
translation is a table.

WHAT CHANGED, AND WHY IT MATTERS
================================

The first version of this table mapped a guest RVA to an absolute ARM address
read out of the linked box86 binary. That address then got compiled back INTO
the binary it was read from, so the table described a build that no longer
existed the moment anything changed. It needed a rebuild-until-stable loop, and
when it was stale it did not crash on a wild pointer -- it landed inside a real,
wrong function. Observed once: buffer_prepare_location resolved 16 bytes into
wined3d_buffer_destroy_object.

The fix is the one class C already taught this project: an address is not an
identity. This generator now emits

    guest RVA -> small integer ID

and the ARM side resolves that ID through a table the LINKER fills, from
per-translation-unit registry fragments that take each function's address in the
translation unit where it is visible. No addresses are read from a binary, so
nothing is self-referential and there is no fixpoint to run.

WHAT IS DELIBERATELY NOT MAPPED
===============================

A name matching on both sides is not sufficient, and three separate rejections
apply. Each one silently produced a wrong mapping before it was added.

1. Not from WineD3D. The island links libc and its own native replacements, so
   `calloc`, `__popcountsi2` and `__wine_dbg_header` all match by name. Mapping
   those hands a guest allocator call to the host allocator -- the same trap
   that keeps `_recalloc` an abort stub.

2. Compiler-invented clones: `.isra.N`, `.part.N`, `.constprop.N`, `.cold`,
   `.lto_priv.N`, `.localalias`. These are NOT the source-level function. GCC
   invents them per translation, with signatures it chooses itself -- `.isra`
   replaces aggregate parameters with scalars, `.constprop` deletes parameters
   it propagated, `.part` splits a body at a point the compiler picked. i386
   mingw-GCC and armhf-GCC make those decisions independently, so `foo.isra.0`
   on one side and `foo.isra.0` on the other are unrelated functions that happen
   to share a mangled name. 56 such entries were in the shipped table, including
   `wined3d_from_cs.part.0`, which sits on a hot path.

3. Ambiguous names: defined in more than one island TU, or present at more than
   one address in the guest PE. Both sides are `static` functions from different
   sources sharing a name -- `wine_dbg_vprintf` is defined in 31 of the 32 TUs.
   The old generator kept whichever it saw first on each side, so a guest static
   from one file could map to the ARM copy from another.

Control check: the ops-table targets the census actually observed must survive
all of that. If they do not, the table is useless however many entries it has.

usage: gen_class_b_table.py <i386 wined3d.dll, unstripped> --objects DIR
                            [--opengl32 DLL] [-o HEADER] [--registry DIR]
"""
import argparse
import collections
import glob
import os
import re
import subprocess
import sys

IMAGE_BASE = 0x10000000
OPENGL32_BASE = 0x7A800000

# Suffixes GCC appends to clones it invented. Never mappable across compilers.
CLONE_MARKERS = (".isra.", ".part.", ".constprop.", ".cold",
                 ".lto_priv.", ".localalias", ".omp_fn.", ".resolver")

# Island entry functions whose runtime guest address Box86 already knows,
# because their marker matched. Two must agree on one module base before the
# resolver may run, or the table is from a different DLL.
WITNESS = (("wined3d_texture_from_resource", 32),
           ("wined3d_buffer_invalidate_location", 9),
           ("context_invalidate_state", 1),
           ("device_invalidate_state", 3))

# The dispatch targets the p50 census recorded on the live reinforcement run.
# They are the reason this table exists, so they are also its control check.
CONTROL = ["wined3d_buffer_gl_prepare_location",
           "wined3d_buffer_gl_unload_location",
           "wined3d_texture_gl_prepare_location",
           "wined3d_texture_gl_load_location",
           "wined3d_texture_gl_unload_location",
           "wined3d_texture_gl_upload_data"]


def is_clone(name):
    return any(m in name for m in CLONE_MARKERS)


def pe_symbols(path):
    """name -> RVA from the i386 PE, and the set of names seen more than once.

    Local `t` symbols matter: the backend ops are static, and without them the
    table would miss exactly what it exists for. But a name at two addresses
    cannot be mapped, so those are collected and rejected rather than resolved
    by taking whichever came first."""
    out = subprocess.run(["i686-w64-mingw32-nm", "-n", path],
                         capture_output=True, text=True, check=True).stdout
    addrs = collections.defaultdict(set)
    for line in out.splitlines():
        f = line.split()
        if len(f) != 3 or f[1] not in "tT" or f[2].startswith(".text$"):
            continue
        name = f[2][1:] if f[2].startswith("_") else f[2]
        addrs[name].add(int(f[0], 16) - IMAGE_BASE)
    syms = {n: sorted(a)[0] for n, a in addrs.items() if len(a) == 1}
    ambiguous = {n for n, a in addrs.items() if len(a) > 1}
    return syms, ambiguous


def island_tu_symbols(objdir):
    """name -> [translation units defining it], over the island's own WineD3D
    objects only. This is the filter that keeps libc and the native
    replacements out: a name that merely matches between two binaries proves
    nothing about where the code came from."""
    owner = collections.defaultdict(list)
    for obj in sorted(glob.glob(os.path.join(objdir, "*.o"))):
        out = subprocess.run(["readelf", "-sW", obj],
                             capture_output=True, text=True, check=True).stdout
        tu = os.path.basename(obj)[:-2]
        for line in out.splitlines():
            f = line.split()
            if len(f) >= 8 and f[3] == "FUNC" and f[6] != "UND":
                if tu not in owner[f[7]]:
                    owner[f[7]].append(tu)
    return owner


def gl_exports(path):
    """opengl32 export RVA -> name. Only a fallback now: the primary class-C key
    is the slot's position in gl_ops, because the extension entry points are
    internal wglGetProcAddress thunks that no export table can name.

    Must be the DLL MOUNTED ON THE DEVICE. The reference wineprefix copy shares
    an ImageBase and has different RVAs, which is what made the first failure
    silent -- 3 of 493 slots resolved, the rest written back as NULL."""
    out = subprocess.run(["i686-w64-mingw32-nm", "--defined-only", path],
                         capture_output=True, text=True, check=True).stdout
    gl = {}
    for line in out.splitlines():
        f = line.split()
        if len(f) != 3 or f[1] != "T":
            continue
        name = f[2].lstrip("_").split("@")[0]
        if name.startswith(("gl", "wgl")):
            gl.setdefault(name, int(f[0], 16) - OPENGL32_BASE)
    return gl


def preserved_gl_entries(path):
    """Read the already-verified class-C fallback from a generated header.

    The mounted opengl32.dll is not retained in this repository. Regenerating
    WineD3D must not silently replace its table with zero entries merely because
    that independent input is offline. The names/RVAs remain tied to the same
    unchanged mounted opengl32 artifact and are copied exactly, with the count
    checked against the header's own witness."""
    text = open(path).read()
    start = text.index("static const struct mgs2_class_c_entry mgs2_class_c_table[]")
    end = text.index("#define MGS2_CLASS_C_COUNT", start)
    block = text[start:end]
    entries = {name: int(rva, 16) for rva, name in
               re.findall(r'\{\s*0x([0-9a-fA-F]+),\s*"([^"]+)"\s*\}', block)}
    match = re.search(r"#define MGS2_CLASS_C_COUNT\s+(\d+)", text[end:])
    if not match or int(match.group(1)) != len(entries):
        raise RuntimeError(f"class-C count mismatch in {path}")
    return entries


def c_ident(name):
    return re.sub(r"[^0-9A-Za-z_]", "_", name)


def write_registries(directory, mapped, owner):
    """One fragment per translation unit, appended to that TU by the build.

    The address is taken here, where the function is visible -- 916 of the
    mapped names are `static` and cannot be referenced from anywhere else. The
    linker gathers every fragment into one section, so the runtime reads a table
    of (id, address) pairs that no generator ever had to know the addresses of.
    """
    os.makedirs(directory, exist_ok=True)
    per_tu = collections.defaultdict(list)
    for name, ident in mapped.items():
        per_tu[owner[name][0]].append((name, ident))
    written = 0
    for tu in sorted(set(owner[n][0] for n in mapped)):
        entries = sorted(per_tu[tu], key=lambda p: p[1])
        with open(os.path.join(directory, tu + ".h"), "w") as f:
            f.write("/* Generated by gen_class_b_table.py -- do not hand-edit.\n"
                    " * Appended to %s.c by build_island_objects.sh so each\n"
                    " * address is taken where the function is visible.\n"
                    " * The linker fills the section; nothing here is an address. */\n"
                    % tu)
            f.write('#include "mgs2_island_registry.h"\n')
            for name, ident in entries:
                f.write("MGS2_NATIVE_REG(%u, %s)\n" % (ident, name))
        written += len(entries)
    return written


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dll")
    ap.add_argument("--objects", default="/mnt/data/holden/mgs/box86-src/src/island")
    ap.add_argument("--opengl32", help="the guest opengl32.dll AS MOUNTED ON THE DEVICE")
    ap.add_argument("--preserve-class-c-from",
                    help="copy the verified class-C table from this generated header")
    ap.add_argument("--registry", help="directory for the per-TU registry fragments")
    ap.add_argument("-o", "--out")
    args = ap.parse_args()

    guest, guest_ambiguous = pe_symbols(args.dll)
    owner = island_tu_symbols(args.objects)

    # Account against the FULL matched set, not the already-filtered one, or the
    # categories lie about why a name was dropped: wine_dbg_vprintf is defined
    # in 31 island TUs AND at several guest addresses, and reporting 0 multi-TU
    # rejections because the guest filter got there first hides that entirely.
    both = (set(guest) | guest_ambiguous) & set(owner)
    rejected_clone = sorted(n for n in both if is_clone(n))
    rejected_multi = sorted(n for n in both if not is_clone(n) and len(owner[n]) > 1)
    rejected_guest = sorted(n for n in both if not is_clone(n) and n in guest_ambiguous)
    good = sorted(n for n in both
                  if not is_clone(n) and len(owner[n]) == 1 and n not in guest_ambiguous)

    ids = {n: i for i, n in enumerate(good)}

    print("i386 wined3d.dll functions, unambiguous  %d" % len(guest))
    print("names defined by the island's TUs        %d" % len(owner))
    print("matched in both                          %d" % len(both))
    print("  rejected, compiler clone               %d" % len(rejected_clone))
    print("  rejected, several island TUs           %d" % len(rejected_multi))
    print("  rejected, several guest addresses      %d" % len(rejected_guest))
    print("  MAPPED                                 %d" % len(good))
    if rejected_clone:
        print("    clones e.g. %s" % ", ".join(rejected_clone[:4]))
    if rejected_multi:
        print("    multi-TU e.g. %s" % ", ".join(rejected_multi[:4]))

    missing = [n for n in CONTROL if n not in ids]
    for n in CONTROL:
        where = ("mapped" if n in ids else
                 "REJECTED" if n in both else
                 "guest only" if n in guest else
                 "ARM only" if n in owner else "neither")
        print("  %-44s %s%s" % (n, where, "" if n in ids else "   <-- "))

    witness = [(n, e) for n, e in WITNESS if n in ids]
    if len(witness) < 2:
        print("\nFAIL: fewer than two witnesses are mappable; the resolver could "
              "not establish the guest module base")
        return 1

    if args.opengl32 and args.preserve_class_c_from:
        ap.error("--opengl32 and --preserve-class-c-from are mutually exclusive")
    gl = (gl_exports(args.opengl32) if args.opengl32 else
          preserved_gl_entries(args.preserve_class_c_from) if args.preserve_class_c_from else {})
    if gl:
        origin = "preserved verified table" if args.preserve_class_c_from else "mounted DLL"
        print("opengl32 export entry points             %d  (class-C fallback, %s)"
              % (len(gl), origin))

    registered = 0
    if args.registry:
        registered = write_registries(args.registry, ids, owner)
        print("registry fragments written for %d TUs, %d entries"
              % (len(set(owner[n][0] for n in ids)), registered))
        if registered != len(ids):
            print("FAIL: %d mapped names but %d registered" % (len(ids), registered))
            return 1

    if args.out:
        with open(args.out, "w") as f:
            f.write("/* Generated by harness/island/full/gen_class_b_table.py.\n"
                    " * guest wined3d RVA -> native symbol ID, sorted by RVA.\n"
                    " * IDs, not addresses: the ARM addresses are supplied by the\n"
                    " * linker through the per-TU registry fragments, so this file\n"
                    " * never describes a binary and can never go stale against one.\n"
                    " * Do not hand-edit; regenerate from the exact i386 DLL. */\n")
            f.write("struct mgs2_class_b_entry { unsigned int rva; unsigned short id; };\n")
            f.write("static const struct mgs2_class_b_entry mgs2_class_b_table[] = {\n")
            for n in sorted(ids, key=lambda n: guest[n]):
                f.write("    { 0x%08x, %5u },  /* %s */\n" % (guest[n], ids[n], n))
            f.write("};\n")
            f.write("#define MGS2_CLASS_B_COUNT %d\n" % len(ids))
            f.write("#define MGS2_NATIVE_ID_COUNT %d\n\n" % len(ids))

            f.write("/* Diagnostics only: names an ID may be reported under. */\n")
            f.write("static const char *const mgs2_native_id_name[] = {\n")
            for n in sorted(ids, key=lambda n: ids[n]):
                f.write('    "%s",\n' % n)
            f.write("};\n\n")

            gl_sorted = sorted(gl, key=lambda n: gl[n])
            f.write("/* Class C fallback: opengl32 export RVA -> name. The primary\n"
                    " * key is the slot position in gl_ops; see patch 53. */\n")
            f.write("struct mgs2_class_c_entry { unsigned int rva; const char *name; };\n")
            f.write("static const struct mgs2_class_c_entry mgs2_class_c_table[] = {\n")
            for n in gl_sorted:
                f.write('    { 0x%08x, "%s" },\n' % (gl[n], n))
            f.write("};\n")
            f.write("#define MGS2_CLASS_C_COUNT %d\n\n" % len(gl_sorted))

            f.write("/* Build-pairing witness: guest RVA of functions Box86 already\n"
                    " * knows the runtime address of, because their island entry\n"
                    " * matched. Two must agree on one module base. */\n")
            f.write("struct mgs2_class_b_witness { const char *name; unsigned int id;"
                    " unsigned int rva; };\n")
            f.write("static const struct mgs2_class_b_witness mgs2_class_b_witness[] = {\n")
            for name, entry_id in witness:
                f.write('    { "%s", %u, 0x%08x },\n' % (name, entry_id, guest[name]))
            f.write("};\n")
        print("\nwritten to %s" % args.out)

    ok = not missing
    print("\ncontrol check (every observed dispatch target is mappable): "
          + ("PASS" if ok else "FAIL -- missing %s" % missing))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Which gl_ops slots can an island entry's closure actually reach?

The island resolves gl_ops once per device and leaves whatever it cannot resolve
as NULL. Today that is 260 of 493 live slots. Whether that matters has so far
been answered by playing the game and seeing whether it crashes -- which is
crash-driven, covers only the states the route happened to enter, and cannot
say anything about the states it did not.

It is answerable statically. `struct wined3d_gl_funcs` is generated from four
macro lists, and `GL_EXTCALL(f)` expands to a plain member access, so after
preprocessing every GL call site names its slot literally. Combined with the
direct call graph of the linked ARM binary, that gives, per entry:

    required slots  =  union over the closure of every gl_ops member referenced

and the GL-slot safety gate becomes

    required & ~resolved != 0   ->   do not arm this entry

which is a build-time fact rather than a survived playthrough.

FOUR LIMITS, STATED RATHER THAN PAPERED OVER
============================================

1. The call graph unions linked ARM direct edges with preprocessed source-call
   edges (so calls inlined by the ARM compiler do not disappear), and follows
   every WineD3D ops-table target assigned to a referenced member. A genuine
   guest callback is not followed; the census measured those at 0.0 per frame,
   which is a reason to proceed, not a proof of absence.

2. Compiler clones (`foo.isra.0`, `foo.part.0`) appear in the binary's call
   graph but not in the source. Their GL references are attributed to the
   parent name. This is an approximation: `.part` clones hold a SUBSET of the
   parent's body, so attributing the parent's full slot set to them can only
   OVER-estimate what is required. Over-estimating refuses to arm something that
   might have been safe; under-estimating arms something that faults. The bias
   is deliberately on the safe side.

3. A slot referenced on a branch that never executes still counts. Same bias.

4. This does not analyse writable file-scope state. The live entry-4 trial is
   the counterexample that makes the distinction non-negotiable: every required
   GL slot resolved, but native mgs2_batch_flush initially read the island's
   duplicate mgs2_batch rather than the guest producer's object and corrupted
   the run. "GL-SLOTS OK" below means exactly that, never "safe to arm".

usage: island_gl_reach.py <unstripped box86 with the island> [--entry N]...
"""
import argparse
import collections
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import island_reach

WINE_SRC = os.environ.get("WINE_SRC", "/mnt/data/holden/mgs/recovered-session/wine-11.0")
WINE_BUILD = os.environ.get("WINE_BUILD", "/mnt/data/holden/mgs/recovered-session/build-wine-i386")
CC = os.environ.get("CC", "arm-linux-gnueabihf-gcc")
SYSROOT = os.environ.get("SYSROOT", "")

INC = ["-I%s/dlls/wined3d" % WINE_BUILD, "-I%s/dlls/wined3d" % WINE_SRC,
       "-I%s/include" % WINE_SRC, "-I%s/include/msvcrt" % WINE_SRC,
       "-I%s/libs/vkd3d/include" % WINE_SRC,
       "-I%s/libs/vkd3d/include/private" % WINE_SRC, "-I%s/include" % WINE_BUILD]
DEF = ["-DMGS2_RELEASE", "-DMGS2_FINALPLAY", "-D_UCRT", "-D__WINESRC__",
       "-DMGS2_ISLAND_ARM", "-DWINE_NO_TRACE_MSGS", "-DWINE_NO_DEBUG_MSGS"]

# gl_ops.<group>.p_<name>, and the separate fbo_ops table.
GL_REF = re.compile(r"gl_ops\s*\.\s*(wgl|gl|ext)\s*\.\s*(p_\w+)")
FBO_REF = re.compile(r"fbo_ops\s*\.\s*(gl\w+)")
CLONE = re.compile(r"\.(isra|part|constprop|cold|lto_priv|localalias)\.?\d*$")
OPS_STRUCT = re.compile(r"struct\s+(\w+_ops)\s*\{(.*?)\};", re.S)
OPS_FIELD = re.compile(r"\(\s*\*\s*(\w+)\s*\)")
OPS_TABLE = re.compile(
    r"(?:static\s+)?const\s+struct\s+(\w+_ops)\s+\w+\s*=\s*\{(.*?)\n\};",
    re.S)
OPS_ENTRY = re.compile(r"^\s*(?:\.(\w+)\s*=\s*)?(\w+)\s*,?\s*$")
OPS_MEMBER_REF = re.compile(r"->\s*(\w+)\s*(?:\(|\))")
SOURCE_CALL = re.compile(r"\b([A-Za-z_]\w*)\s*\(")


def preprocess(path, extra=()):
    cmd = [CC]
    if SYSROOT:
        cmd.append("--sysroot=" + SYSROOT)
    cmd += ["-E", "-P", "-fshort-wchar", path] + INC + DEF + list(extra)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("preprocess failed for %s:\n%s" % (path, r.stderr[-2000:]))
    return r.stdout


def slot_order(tmpdir):
    """Slot index -> member name, from the SAME macro lists the struct is built
    from. Not a hand-written list and not derived from the binary: this is the
    one source of truth both the runtime array and this analysis come from."""
    probe = os.path.join(tmpdir, "mgs2_slot_probe.c")
    with open(probe, "w") as f:
        # wined3d_private.h alone is not enough: the four lists live in
        # wine/wgl.h and are not re-exported, so the probe expanded to nothing
        # and the control check caught it.
        f.write('#include "wined3d_private.h"\n'
                "#include <wine/wgl.h>\n"
                "#define USE_GL_FUNC(x) \"p_\" #x,\n"
                "const char *const mgs2_slot_probe[] = {\n"
                "ALL_WGL_FUNCS ALL_GL_FUNCS ALL_WGL_EXT_FUNCS ALL_GL_EXT_FUNCS\n"
                "};\n"
                "#undef USE_GL_FUNC\n")
    out = preprocess(probe)
    body = out[out.index("mgs2_slot_probe[]"):]
    body = body[body.index("{") + 1:body.index("}")]
    names = re.findall(r'"p_"\s*"(\w+)"|"(p_\w+)"', body)
    flat = ["p_" + a if a else b for a, b in names]
    if not flat:
        raise RuntimeError("slot list came back empty -- the macro lists did not expand")
    return flat


def ops_targets(srcdir):
    """ops member -> every WineD3D function assigned to that member.

    This is deliberately an over-approximation across GL, no-3D and Vulkan
    tables.  Which concrete table a live object uses is runtime state; following
    every source initializer may reject a safe entry, but cannot omit a GL slot
    required by one of the declared backends.
    """
    paths = [os.path.join(srcdir, p) for p in os.listdir(srcdir) if p.endswith(".c")]
    paths.append(os.path.join(srcdir, "wined3d_private.h"))
    texts = []
    fields = {}
    for path in paths:
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        texts.append(text)
        for kind, body in OPS_STRUCT.findall(text):
            names = OPS_FIELD.findall(body)
            if names:
                fields.setdefault(kind, names)

    targets = collections.defaultdict(set)
    for text in texts:
        for kind, body in OPS_TABLE.findall(text):
            order = fields.get(kind, ())
            position = 0
            body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
            for raw in body.splitlines():
                line = raw.split("//", 1)[0].strip()
                if not line or line.startswith("#"):
                    continue
                m = OPS_ENTRY.match(line)
                if not m:
                    continue
                designated, target = m.groups()
                if designated:
                    member = designated
                    if member in order:
                        position = order.index(member) + 1
                elif position < len(order):
                    member = order[position]
                    position += 1
                else:
                    continue
                if target not in ("NULL", "0"):
                    targets[member].add(target)
    return targets


def scan_functions(text, ops_members=()):
    """Return GL refs, ops refs, source-call candidates and definitions.

    Brace tracking on preprocessed C. A depth 0 -> 1 transition is a function
    body only when the previous non-space character is ')' -- otherwise it is an
    aggregate initialiser, which is the one construct that would otherwise be
    mistaken for a definition."""
    refs = collections.defaultdict(set)
    indirect = collections.defaultdict(set)
    source_calls = collections.defaultdict(set)
    definitions = set()
    ops_members = set(ops_members)
    depth = 0
    current = None
    start = 0
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == '"' or c == "'":
            quote = c
            i += 1
            while i < n and text[i] != quote:
                i += 2 if text[i] == "\\" else 1
            i += 1
            continue
        if c == "{":
            if depth == 0:
                j = i - 1
                while j >= 0 and text[j].isspace():
                    j -= 1
                if j >= 0 and text[j] == ")":
                    # walk back to the matching '(' then take the identifier
                    k, d = j, 0
                    while k >= 0:
                        if text[k] == ")":
                            d += 1
                        elif text[k] == "(":
                            d -= 1
                            if d == 0:
                                break
                        k -= 1
                    # Do not slice the whole preprocessed prefix here.  This
                    # runs once per function, and text[:k] made the scanner
                    # quadratic in translation-unit size (large WineD3D files
                    # then took tens of minutes before the call graph was even
                    # examined).  The function identifier is immediately to
                    # the left of the matching '(', apart from whitespace.
                    q = k - 1
                    while q >= 0 and text[q].isspace():
                        q -= 1
                    end = q + 1
                    while q >= 0 and (text[q].isalnum() or text[q] == "_"):
                        q -= 1
                    current = text[q + 1:end] or None
                    start = i
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0 and current:
                body = text[start:i]
                definitions.add(current)
                for group, member in GL_REF.findall(body):
                    refs[current].add(member)
                for member in FBO_REF.findall(body):
                    # fbo_ops is populated from the same GL macro-list slots;
                    # its source members omit the p_ prefix used by gl_ops.
                    refs[current].add("p_" + member)
                for member in OPS_MEMBER_REF.findall(body):
                    if member in ops_members:
                        indirect[current].add(member)
                source_calls[current].update(SOURCE_CALL.findall(body))
                current = None
        i += 1
    return refs, indirect, source_calls, definitions


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("binary")
    ap.add_argument("--entry", type=int, action="append", default=[],
                    help="island entry id; repeat. Default: all known entries.")
    ap.add_argument("--resolved", help="device log carrying 'gl_ops: slot N unresolved'"
                                       " lines, to turn required into a verdict")
    ap.add_argument("--out", help="write the per-entry required-slot header here")
    ap.add_argument("--entries", default="/mnt/data/holden/mgs/box86-src/src/mgs2_island_bridges.c",
                    help="the island entry table Box86 itself compiles")
    args = ap.parse_args()

    tmpdir = os.environ.get("TMPDIR", "/tmp")
    order = slot_order(tmpdir)
    index_of = {}
    for i, name in enumerate(order):
        index_of.setdefault(name, i)
    print("gl_ops slots declared by the macro lists   %d" % len(order))

    target_by_member = ops_targets(os.path.join(WINE_SRC, "dlls/wined3d"))
    if not target_by_member.get("buffer_prepare_location") or not target_by_member.get("texture_load_location"):
        raise RuntimeError("ops-table parser missed the buffer/texture controls")
    print("ops members with source targets             %d" % len(target_by_member))

    refs = {}
    indirect_refs = {}
    source_calls = {}
    source_functions = set()
    for path in sorted(os.listdir(os.path.join(WINE_SRC, "dlls/wined3d"))):
        if not path.endswith(".c"):
            continue
        text = preprocess(os.path.join(WINE_SRC, "dlls/wined3d", path))
        file_refs, file_indirect, file_calls, file_functions = scan_functions(text, target_by_member)
        source_functions.update(file_functions)
        for fn, members in file_refs.items():
            refs.setdefault(fn, set()).update(members)
        for fn, members in file_indirect.items():
            indirect_refs.setdefault(fn, set()).update(members)
        for fn, callees in file_calls.items():
            source_calls.setdefault(fn, set()).update(callees)
    touching = {f: m for f, m in refs.items() if m}
    print("functions referencing a GL slot            %d" % len(touching))
    print("functions dispatching through an ops table %d" % len(indirect_refs))

    by_addr, by_name = island_reach.symbols(args.binary)
    calls, _indirect, _teb = island_reach.call_graph(args.binary, by_addr)

    # Island entries come from the same file Box86 compiles, parsed the same way
    # island_reach.py parses it, so the two analyses cannot drift apart.
    entries_src = args.entries
    parsed = []
    for line in open(entries_src):
        m = re.match(r"\s*\{\s*(\d+),\s*\(void \*\)\S+,\s*\(void \*\)(\w+)\s*\}", line)
        if m:
            parsed.append((int(m.group(1)), m.group(2)))
    if not parsed:
        sys.exit("no island entries parsed from %s" % entries_src)
    entry_name = dict(parsed)

    unresolved = set()
    if args.resolved:
        with open(args.resolved, errors="replace") as fh:
            for line in fh:
                m = re.search(r"gl_ops: slot (\d+) unresolved", line)
                if m:
                    unresolved.add(int(m.group(1)))
        print("slots reported unresolved on the device    %d" % len(unresolved))

    wanted = args.entry or sorted(entry_name)
    results = {}
    for eid in wanted:
        root = entry_name.get(eid)
        if not root or root not in by_name:
            print("entry %d (%s): not in this binary, skipped" % (eid, root))
            continue
        closure, stack = set(), [root]
        while stack:
            f = stack.pop()
            if f in closure:
                continue
            closure.add(f)
            for callee in calls.get(f, ()):
                base = CLONE.sub("", callee)
                if callee in source_functions or base in source_functions:
                    stack.append(callee)
            base = CLONE.sub("", f)
            # The linked graph alone loses calls the ARM compiler inlined.  The
            # preprocessed source edge keeps those callees (and their GL refs)
            # in the conservative closure.
            for callee in source_calls.get(f, ()) or source_calls.get(base, ()):
                if callee in source_functions and callee in by_name:
                    stack.append(callee)
            for member in indirect_refs.get(f, ()) or indirect_refs.get(base, ()):
                for target in target_by_member.get(member, ()):
                    if target in by_name:
                        stack.append(target)
        need = set()
        for fn in closure:
            base = CLONE.sub("", fn)
            for member in refs.get(fn, ()) or refs.get(base, ()):
                if member in index_of:
                    need.add(index_of[member])
        missing = sorted(need & unresolved) if unresolved else []
        results[eid] = (root, closure, need, missing)
        verdict = ("GL-SLOTS OK (other cut checks still required)" if not missing
                   else "DO NOT ARM: unresolved GL slot")
        print("\nentry %-3d %s" % (eid, root))
        print("  closure %d functions, requires %d GL slots" % (len(closure), len(need)))
        if unresolved:
            print("  unresolved among them: %d   %s" % (len(missing), verdict))
            for s in missing[:8]:
                print("      slot %-4d %s" % (s, order[s]))

    if args.out and results:
        with open(args.out, "w") as f:
            f.write("/* Generated by harness/island/full/island_gl_reach.py.\n"
                    " * Per-entry required gl_ops slots, as a bitset. The island\n"
                    " * refuses to arm an entry whose required slots did not all\n"
                    " * resolve -- a build-time fact, not a survived playthrough. */\n")
            words = (len(order) + 31) // 32
            f.write("#define MGS2_GL_SLOT_WORDS %d\n" % words)
            f.write("struct mgs2_entry_gl_need { unsigned int id;"
                    " unsigned int need[MGS2_GL_SLOT_WORDS]; };\n")
            f.write("static const struct mgs2_entry_gl_need mgs2_entry_gl_need[] = {\n")
            for eid in sorted(results):
                need = results[eid][2]
                bits = [0] * words
                for s in need:
                    bits[s // 32] |= 1 << (s % 32)
                f.write("    { %d, { %s } },  /* %s: %d slots */\n"
                        % (eid, ", ".join("0x%08x" % b for b in bits),
                           results[eid][0], len(need)))
            f.write("};\n")
            f.write("#define MGS2_ENTRY_GL_NEED_COUNT %d\n" % len(results))
        print("\nwritten to %s" % args.out)

    # Control check: an entry that plainly does GL work must require slots. If
    # the join between the call graph and the source scan silently produced
    # nothing, every entry would come back "GL-SLOTS OK" with 0 required slots --
    # which is the failure this check exists to make loud.
    nonzero = [e for e in results if results[e][2]]
    ok = bool(nonzero)
    print("\ncontrol check (at least one entry requires GL slots): "
          + ("PASS, %d of %d entries do" % (len(nonzero), len(results)) if ok
             else "FAIL -- the graph/source join produced nothing"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Which indirect calls in one island entry's closure are NOT routed?

WHY THIS EXISTS

Every wall the island has hit so far has been the same thing: a function pointer
read out of a GUEST WineD3D object and called directly, so native ARM branched
into i386 bytes. They were found one device run at a time --

    2026-08-19  fbo_ops / plain gl_ops calls   SIGILL in opengl32 thunks   patch 61
    2026-08-19  glDrawBuffer, not on this stack at all                     patch 62
    2026-08-19  format->upload / ->download    SIGILL in convert_*_gles    patch 63

-- which costs a launch, a fault and an address lookup each time. They are all
visible statically, so find the rest before the next launch rather than after it.

WHAT IT REPORTS

For the closure of one entry, every call through a function-pointer FIELD, split
into routed and unrouted:

    routed     the line goes through MGS2_P50_CALL(), MGS2_GL_INFO() or
               mgs2_island_dispatch() -- class A/B/C translate it
    unrouted   the line calls the guest pointer directly. In the island that is
               an i386 address, and the ARM core will execute i386 bytes

HOW, AND WHAT IT DOES NOT KNOW

The function-pointer field names come from the headers: every `type (*name)(...)`
member declaration. A call is then any `->name(` or `.name(` for one of those
names, or an explicit `(*name)(`. The closure comes from the linked ARM binary's
direct call graph unioned with same-name source call edges, so calls the ARM
compiler inlined do not disappear.

Three limits, stated rather than papered over:

1. Field names are matched by NAME, not by type, so a field and an ordinary
   function that share a name are conflated. That over-reports, which is the safe
   direction here.
2. A call on a branch that never executes still counts. Also over-reporting.
3. It cannot see a pointer stored in a local, passed as an argument and called
   there. Those exist; `(*name)(` catches some, not all. This is an audit, not a
   proof of absence -- the abort in mgs2_island_dispatch() remains the backstop.

usage: island_icall_audit.py <unstripped box86 with the island> [--entry 34]
"""
import argparse
import collections
import os
import pathlib
import re
import sys

HARNESS = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HARNESS))
import repo_env

repo_env.load()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import island_reach
import island_gl_reach

WINE_SRC = str(repo_env.workspace_path("WINE_SRC", "recovered-session/wine-11.0"))
BOX86_SRC = repo_env.workspace_path("BOX86_SRC", "box86-src")
SRC_DIR = os.path.join(WINE_SRC, "dlls/wined3d")

FUNC_PTR_FIELD = re.compile(r"\(\s*\*\s*(\w+)\s*\)\s*\(")
FUNC_DEF = re.compile(r"^(?:static\s+)?(?:const\s+)?[A-Za-z_][\w \t\*]*?(\w+)\s*\([^;]*$")
ROUTED = ("MGS2_P50_CALL(", "MGS2_GL_INFO(", "mgs2_island_dispatch(")
CLONE = re.compile(r"\.(isra|part|constprop|cold|lto_priv|localalias)\.?\d*$")
KEYWORDS = {"if", "for", "while", "switch", "return", "sizeof", "do", "else"}


def mask_c_lines(lines):
    """Remove comments and literals while preserving line/column positions.

    Function extents used to count braces in raw source.  GLSL source strings
    in ``glsl_shader.c`` contain many literal ``{`` / ``}`` characters; one of
    those made the parser keep an earlier function open and silently lose
    ``shader_glsl_apply_draw_state()`` and the functions after it.  Replace
    non-newline comment/string contents with spaces before counting braces.
    """
    block = False
    quote = None
    escaped = False
    for raw in lines:
        out = list(raw)
        i = 0
        while i < len(raw):
            c = raw[i]
            n = raw[i + 1] if i + 1 < len(raw) else ""
            if block:
                out[i] = " "
                if c == "*" and n == "/":
                    out[i + 1] = " "
                    block = False
                    i += 2
                else:
                    i += 1
                continue
            if quote:
                out[i] = " "
                if escaped:
                    escaped = False
                elif c == "\\":
                    escaped = True
                elif c == quote:
                    quote = None
                i += 1
                continue
            if c == "/" and n == "*":
                out[i] = out[i + 1] = " "
                block = True
                i += 2
            elif c == "/" and n == "/":
                for j in range(i, len(raw)):
                    out[j] = " "
                break
            elif c in ('"', "'"):
                out[i] = " "
                quote = c
                escaped = False
                i += 1
            else:
                i += 1
        yield "".join(out)


def field_names():
    """Function-pointer member names, from every header in the module."""
    names = set()
    for name in sorted(os.listdir(SRC_DIR)):
        if not name.endswith(".h"):
            continue
        for line in open(os.path.join(SRC_DIR, name), errors="replace"):
            for m in FUNC_PTR_FIELD.finditer(line):
                names.add(m.group(1))
    # These are the module's own typedef'd callbacks and ops tables; a couple of
    # generic words would otherwise match ordinary calls.
    names.discard("void")
    return names


def functions_by_file():
    """Crude function extents per .c file: name -> (file, first line, body)."""
    out = {}
    for name in sorted(os.listdir(SRC_DIR)):
        if not name.endswith(".c"):
            continue
        path = os.path.join(SRC_DIR, name)
        lines = open(path, errors="replace").read().splitlines()
        masked = list(mask_c_lines(lines))
        cur, start, body, depth, seen = None, 0, [], 0, False
        for i, (line, syntax) in enumerate(zip(lines, masked), 1):
            m = FUNC_DEF.match(syntax)
            cand = (m.group(1) if m and not syntax.lstrip().startswith("#")
                    and not m.group(1).startswith("__")
                    and m.group(1) not in KEYWORDS else None)
            if cur is None:
                if cand:
                    cur, start, body, depth, seen = cand, i, [], 0, False
                    body.append((i, line))
                continue
            if not seen:
                # Still in the signature. An `__attribute__((noinline))` line used
                # to be taken for a definition, which then swallowed the real one
                # below it -- that is why wined3d_texture_load_location, the whole
                # point of this audit, was missing from the map. A new candidate
                # here means the previous line was decoration; a `;` means it was
                # a declaration.
                if cand:
                    cur, start, body, depth = cand, i, [(i, line)], 0
                    continue
                if syntax.rstrip().endswith(";"):
                    cur = None
                    continue
            body.append((i, line))
            depth += syntax.count("{") - syntax.count("}")
            if "{" in syntax:
                seen = True
            if seen and depth <= 0:
                out.setdefault(cur, (name, start, body))
                cur = None
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("binary")
    ap.add_argument("--entry", type=int, default=34)
    ap.add_argument("--entries",
                    default=str(BOX86_SRC / "src/mgs2_island_bridges.c"))
    ap.add_argument("--all-hits", action="store_true",
                    help="print routed hits too, not just unrouted ones")
    args = ap.parse_args()

    fields = field_names()
    bodies = functions_by_file()
    by_addr, by_name = island_reach.symbols(args.binary)
    calls, _ind, _teb = island_reach.call_graph(args.binary, by_addr)

    root = None
    for line in open(args.entries):
        m = re.match(r"\s*\{\s*(\d+),\s*\(void \*\)\S+,\s*\(void \*\)(\w+)\s*\}", line)
        if m and int(m.group(1)) == args.entry:
            root = m.group(2)
    if not root:
        sys.exit("entry %d not found in %s" % (args.entry, args.entries))
    if root not in by_name:
        sys.exit("%s is not in this binary" % root)

    # Source call edges keep the callees the ARM compiler inlined.
    src_calls = {}
    call_re = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
    for fn, (_f, _l, body) in bodies.items():
        seen = set()
        for _i, line in body:
            for m in call_re.finditer(line):
                if m.group(1) in bodies:
                    seen.add(m.group(1))
        src_calls[fn] = seen

    # Ops-table targets, from island_gl_reach's parser: a closure that stops at
    # `texture_ops->texture_load_location(...)` would miss the GL implementation
    # behind it, which is where the interesting pointers live.
    targets = island_gl_reach.ops_targets(SRC_DIR)
    member_call = re.compile(r"(?:->|\.)\s*(\w+)\s*(?:\(|\))")

    closure, stack = set(), [root]
    while stack:
        fn = stack.pop()
        if fn in closure:
            continue
        closure.add(fn)
        base = CLONE.sub("", fn)
        for callee in calls.get(fn, ()):
            c = CLONE.sub("", callee)
            if c in bodies:
                stack.append(c)
        for callee in src_calls.get(base, ()):
            if callee in by_name or callee in bodies:
                stack.append(callee)
        if base in bodies:
            for _i, line in bodies[base][2]:
                for m in member_call.finditer(line):
                    for target in targets.get(m.group(1), ()):
                        if target in bodies:
                            stack.append(target)

    print("entry %d root %s" % (args.entry, root))
    print("closure %d functions (%d of them have source bodies here)"
          % (len(closure), sum(1 for f in closure if CLONE.sub("", f) in bodies)))
    print("function-pointer field names known from the headers: %d\n" % len(fields))

    # A direct call has ``->field(``; a MGS2_P50_CALL-wrapped call has
    # ``->field)(``.  Do not accept a bare closing parenthesis here: that made
    # boolean tests like ``!format->decompress)))`` look like calls.
    member_re = re.compile(r"(?:->|\.)\s*(\w+)\s*(?:\(|\)\s*\()")
    deref_re = re.compile(r"\(\s*\*\s*(\w+)\s*\)\s*\(")
    unrouted, routed = [], []
    for fn in sorted(closure):
        base = CLONE.sub("", fn)
        if base not in bodies:
            continue
        f, _start, body = bodies[base]
        # Function-pointer parameters have the same spelling as an explicit
        # ``(*callback)(...)`` call.  Signatures are part of ``body`` for the
        # extent parser, so begin only after the function's opening brace.
        brace_lineno = next((i for i, text in body if "{" in text), _start)
        for body_idx, (lineno, line) in enumerate(body):
            if lineno <= brace_lineno:
                continue
            if line.lstrip().startswith(("*", "//", "/*")):
                continue
            hits = {m.group(1) for m in member_re.finditer(line)} \
                 | {m.group(1) for m in deref_re.finditer(line)}
            hits &= fields
            if not hits:
                continue
            # Calls are commonly formatted with MGS2_P50_CALL() on the line
            # immediately before the member expression.  Inspect the current
            # statement, not just the physical line containing the field.
            statement = [line]
            for prev_idx in range(body_idx - 1, max(-1, body_idx - 8), -1):
                prev = body[prev_idx][1]
                if any(c in prev for c in ";{}"):
                    break
                statement.append(prev)
            statement_text = "\n".join(reversed(statement))
            rec = (f, lineno, base, sorted(hits), line.strip()[:96])
            (routed if any(r in statement_text for r in ROUTED) else unrouted).append(rec)

    def show(title, rows):
        print("%s: %d" % (title, len(rows)))
        for f, lineno, fn, names, text in rows:
            print("  %s:%d  %s  via %s" % (f, lineno, fn, ",".join(names)))
            print("      %s" % text)

    show("UNROUTED indirect calls in this closure", unrouted)
    if args.all_hits:
        print()
        show("routed (through MGS2_P50_CALL / MGS2_GL_INFO / dispatch)", routed)
    else:
        print("\nrouted, not listed: %d (pass --all-hits)" % len(routed))

    # Control: this audit is worthless if the join produced nothing. The closure
    # of a texture entry must contain routed calls -- patches 61-63 put them there.
    print("\ncontrol check (the closure contains at least one ROUTED call): "
          + ("PASS, %d" % len(routed) if routed else "FAIL -- graph/source join broken"))
    return 0 if routed else 1


if __name__ == "__main__":
    sys.exit(main())

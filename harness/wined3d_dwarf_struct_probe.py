#!/usr/bin/env python3
"""Emit ARM-compilable declarations of the real WineD3D hot-path structures,
mechanically, from the DWARF of the i386 build that actually ships.

Hand-copied "faithful shapes" leave a gap: the copy might be wrong. This closes
it. Every member, array extent and bitfield width comes from the shipped
binary's debug info, so the declaration cannot drift from the real one."""
import re, sys, pathlib, collections

txt = pathlib.Path(sys.argv[1]).read_text(errors="replace").splitlines()
die = re.compile(r"^\s*<(\d+)><([0-9a-f]+)>: Abbrev Number: \d+ \((DW_TAG_\w+)\)")
att = re.compile(r"^\s*<[0-9a-f]+>\s+(DW_AT_\w+)\s*:\s*(.*)$")
dies, order, cur = {}, [], None
for l in txt:
    m = die.match(l)
    if m:
        cur = {"d": int(m.group(1)), "off": int(m.group(2), 16), "tag": m.group(3),
               "a": {}, "kids": []}
        dies[cur["off"]] = cur; order.append(cur); continue
    m = att.match(l)
    if m and cur is not None: cur["a"][m.group(1)] = m.group(2).strip()
stack = {}
for d in order:
    stack[d["d"]] = d
    p = stack.get(d["d"] - 1)
    if p is not None and p is not d: p["kids"].append(d)

def nm(d):
    """objdump prints some names as "(indirect string, offset: 0x322): flags".
    The identifier is the tail; dropping the whole attribute loses the member."""
    v = (d["a"].get("DW_AT_name", "") or "").strip()
    m = re.search(r":\s*([A-Za-z_][A-Za-z0-9_]*)\s*$", v)
    if m: return m.group(1)
    return v if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", v) else ""
def num(d, k):
    v = d["a"].get(k)
    if not v: return None
    m = re.match(r"(\d+)", v)
    return int(m.group(1)) if m else None
def ref(d, k="DW_AT_type"):
    m = re.search(r"<0x([0-9a-f]+)>", d["a"].get(k, "") or "")
    return dies.get(int(m.group(1), 16)) if m else None
def strip(t):
    while t is not None and t["tag"] in ("DW_TAG_typedef", "DW_TAG_const_type",
                                         "DW_TAG_volatile_type"):
        t = ref(t)
    return t

emitted, order_out, anon = {}, [], [0]
fwd = set()

def base_name(t):
    """A stand-in scalar with the same size and float-ness."""
    n = nm(t); sz = num(t, "DW_AT_byte_size") or 4
    enc = t["a"].get("DW_AT_encoding", "")
    if "float" in enc or n in ("float", "double"):
        return "float" if sz == 4 else "double"
    signed = "signed" in enc and "unsigned" not in enc
    return {1: "signed char" if signed else "unsigned char",
            2: "short" if signed else "unsigned short",
            4: "int" if signed else "unsigned int",
            8: "long long" if signed else "unsigned long long"}.get(sz, "unsigned int")

def type_of(t, depth=0):
    """Returns (prefix, suffix) so that '<prefix> name <suffix>;' declares it."""
    t = strip(t)
    if t is None: return ("void *", "")
    tag = t["tag"]
    if tag == "DW_TAG_pointer_type":
        # A pointer is four bytes either way, but the island dereferences these,
        # so keep the pointee type when it is a named struct or union.
        pt = strip(ref(t))
        if pt is not None and pt["tag"] in ("DW_TAG_structure_type", "DW_TAG_union_type"):
            pn = nm(pt)
            if pn:
                kw = "union" if pt["tag"] == "DW_TAG_union_type" else "struct"
                fwd.add(f"{kw} g_{pn};")
                return (f"{kw} g_{pn} *", "")
        return ("void *", "")
    if tag == "DW_TAG_base_type": return (base_name(t), "")
    if tag == "DW_TAG_enumeration_type":
        return ("int" if (num(t, "DW_AT_byte_size") or 4) == 4 else "unsigned char", "")
    if tag == "DW_TAG_array_type":
        el, _ = type_of(ref(t), depth + 1)
        dims = []
        for k in t["kids"]:
            if k["tag"] == "DW_TAG_subrange_type":
                ub = num(k, "DW_AT_upper_bound")
                cnt = num(k, "DW_AT_count")
                dims.append(cnt if cnt is not None else (ub + 1 if ub is not None else 1))
        if not dims:
            # A missing extent silently shrinks the struct and would produce a
            # confident wrong answer; fail the build instead.
            print(f"#error array with no extent near {nm(t)!r}")
            dims = [1]
        return (el, "".join(f"[{d}]" for d in dims))
    if tag in ("DW_TAG_structure_type", "DW_TAG_union_type"):
        return (emit(t, depth + 1), "")
    return ("unsigned int", "")

def emit(t, depth=0):
    """Emit a struct/union definition, returning its C name."""
    if t["off"] in emitted: return emitted[t["off"]]
    kw = "union" if t["tag"] == "DW_TAG_union_type" else "struct"
    n = nm(t)
    if not n:
        anon[0] += 1; n = f"anon_{anon[0]}"
    cname = f"{kw} g_{n}"
    emitted[t["off"]] = cname
    body = []
    for k in t["kids"]:
        if k["tag"] != "DW_TAG_member": continue
        mn = nm(k)
        if not mn or "(" in mn:                      # indirect-string artefacts
            mn = f"pad_{len(body)}"
        pre, suf = type_of(ref(k), depth)
        bits = num(k, "DW_AT_bit_size")
        if bits is not None:
            # The storage unit, not the narrowest type that fits, decides
            # packing. DWARF puts it on the member for bitfields.
            unit = num(k, "DW_AT_byte_size")
            t = strip(ref(k))
            if unit is None and t is not None:
                unit = num(t, "DW_AT_byte_size")
            unit = unit or 4
            while unit * 8 < bits: unit *= 2
            signed = bool(t) and "unsigned" not in (t["a"].get("DW_AT_encoding", "") or "")
            pre = {1: "signed char" if signed else "unsigned char",
                   2: "short" if signed else "unsigned short",
                   4: "int" if signed else "unsigned int",
                   8: "long long" if signed else "unsigned long long"}[unit]
            body.append(f"    {pre} {mn} : {bits};")
        else:
            body.append(f"    {pre} {mn}{suf};")
    order_out.append(f"{cname} {{\n" + "\n".join(body) + "\n};")
    return cname

# Enumerators become plain #defines: the island needs the *values*, and
# reproducing enum types would add an ABI question the values do not have.
def emit_enums():
    seen, out = {}, []
    for d in order:
        if d["tag"] != "DW_TAG_enumerator": continue
        n = nm(d); v = d["a"].get("DW_AT_const_value")
        if not n or v is None: continue
        m = re.match(r"(-?\d+)", v.strip())
        if not m: continue
        val = int(m.group(1))
        if n in seen and seen[n] != val:
            out.append(f"/* conflicting values for {n}: {seen[n]} and {val} */")
            continue
        if n in seen: continue
        seen[n] = val
        out.append(f"#define {n} {val}")
    return out

TARGETS = sys.argv[2:]
structs = {}
for d in order:
    if d["tag"] == "DW_TAG_structure_type" and nm(d) and num(d, "DW_AT_byte_size") is not None:
        structs.setdefault(nm(d), d)

checks = []
for tn in TARGETS:
    d = structs.get(tn)
    if d is None:
        print(f"/* {tn}: not present in these CUs */", file=sys.stderr); continue
    cname = emit(d)
    checks.append((tn, cname, num(d, "DW_AT_byte_size"), d))

print("/* generated from the shipped i386 build's DWARF -- do not edit */")
for line in emit_enums(): print(line)
print("/* Self-check: a reconstruction that does not reproduce the shipped")
print("   sizeof is lossy, and any comparison built on it is void. The static")
print("   assertions below fail the build rather than produce a false result. */")
print("#define offsetof(t,m) __builtin_offsetof(t,m)")
for f in sorted(fwd): print(f)
for s in order_out: print(s)
for tn, cname, sz, d in checks:
    print(f"_Static_assert(sizeof({cname}) == {sz}, "
          f"\"lossy reconstruction of {tn}\");")
print("\nconst unsigned int probe_table[] = {")
names = []
for tn, cname, sz, d in checks:
    print(f"    sizeof({cname}), _Alignof({cname}),")
    names += [f"{tn} sizeof", f"{tn} alignof"]
    for k in d["kids"]:
        if k["tag"] != "DW_TAG_member": continue
        mn = nm(k)
        if not mn or "(" in mn or num(k, "DW_AT_bit_size") is not None: continue
        print(f"    offsetof({cname}, {mn}),")
        names.append(f"{tn}.{mn}")
print("};")
pathlib.Path("probe_names.txt").write_text("\n".join(names))
print(f"/* {len(names)} probes */", file=sys.stderr)

#!/usr/bin/env python3
"""Emit layout-exact ARM declarations of WineD3D structures.

The earlier generator reproduced the *declaration* and let each compiler lay it
out. That works until it doesn't: mingw builds the shipping DLL with MS bitfield
rules (`-mms-bitfields`, its default), and no ARM GCC option reproduces them --
`-mms-bitfields` does not exist there and `__attribute__((ms_struct))` is
ignored. `struct texture_stage_op` is 16 bytes in the shipping build and 12 on
armhf; `ffp_frag_settings` is 132 against 100.

So the layout is not left to the compiler. Every member is placed at the byte
offset the shipping build actually uses, with explicit padding, and every
placement is checked by a static assertion. Bitfields become a raw storage unit
plus shift/mask accessors computed from the DWARF bit positions, which sidesteps
bitfield ABI entirely.
"""
import re, sys, pathlib, collections

txt = pathlib.Path(sys.argv[1]).read_text(errors="replace").splitlines()
die = re.compile(r"^\s*<(\d+)><([0-9a-f]+)>: Abbrev Number: \d+ \((DW_TAG_\w+)\)")
att = re.compile(r"^\s*<[0-9a-f]+>\s+(DW_AT_\w+)\s*:\s*(.*)$")
dies, order, cur = {}, [], None
for l in txt:
    m = die.match(l)
    if m:
        cur = {"d": int(m.group(1)), "off": int(m.group(2), 16), "tag": m.group(3), "a": {}, "kids": []}
        dies[cur["off"]] = cur; order.append(cur); continue
    m = att.match(l)
    if m and cur is not None: cur["a"][m.group(1)] = m.group(2).strip()
stack = {}
for d in order:
    stack[d["d"]] = d
    p = stack.get(d["d"] - 1)
    if p is not None and p is not d: p["kids"].append(d)

def nm(d):
    v = (d["a"].get("DW_AT_name", "") or "").strip()
    m = re.search(r":\s*([A-Za-z_][A-Za-z0-9_]*)\s*$", v)
    if m: return m.group(1)
    return v if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", v) else ""
def num(d, k):
    v = d["a"].get(k)
    if v is None: return None
    m = re.match(r"(-?\d+)", v.strip())
    return int(m.group(1)) if m else None
def ref(d, k="DW_AT_type"):
    m = re.search(r"<0x([0-9a-f]+)>", d["a"].get(k, "") or "")
    return dies.get(int(m.group(1), 16)) if m else None
def strip_t(t):
    while t is not None and t["tag"] in ("DW_TAG_typedef", "DW_TAG_const_type", "DW_TAG_volatile_type"):
        t = ref(t)
    return t

emitted, out, anon = {}, [], [0]

def scalar(t):
    sz = num(t, "DW_AT_byte_size") or 4
    enc = t["a"].get("DW_AT_encoding", "")
    if "float" in enc: return "float" if sz == 4 else "double"
    sgn = "signed" in enc and "unsigned" not in enc
    return {1: "signed char" if sgn else "unsigned char",
            2: "short" if sgn else "unsigned short",
            4: "int" if sgn else "unsigned int",
            8: "long long" if sgn else "unsigned long long"}.get(sz, "unsigned int")

def sizeof_t(t):
    """Byte size of a type. Arrays often carry no DW_AT_byte_size, so it is
    computed from the element and the extents; defaulting to 4 silently
    shortened every array-bearing struct."""
    t = strip_t(t)
    if t is None: return 4
    if t["tag"] == "DW_TAG_pointer_type": return 4
    n = num(t, "DW_AT_byte_size")
    if n is not None: return n
    if t["tag"] == "DW_TAG_array_type":
        el = sizeof_t(ref(t)); total = el
        for k in t["kids"]:
            if k["tag"] == "DW_TAG_subrange_type":
                ub, c = num(k, "DW_AT_upper_bound"), num(k, "DW_AT_count")
                total *= (c if c is not None else (ub + 1 if ub is not None else 1))
        return total
    return 4

def type_of(t):
    t = strip_t(t)
    if t is None: return ("void *", "")
    g = t["tag"]
    if g == "DW_TAG_pointer_type": return ("void *", "")
    if g == "DW_TAG_base_type": return (scalar(t), "")
    if g == "DW_TAG_enumeration_type":
        return ({1: "unsigned char", 2: "unsigned short", 4: "unsigned int"}.get(
            num(t, "DW_AT_byte_size") or 4, "unsigned int"), "")
    if g == "DW_TAG_array_type":
        el, _ = type_of(ref(t)); dims = []
        for k in t["kids"]:
            if k["tag"] == "DW_TAG_subrange_type":
                ub, c = num(k, "DW_AT_upper_bound"), num(k, "DW_AT_count")
                dims.append(c if c is not None else (ub + 1 if ub is not None else 0))
        if not dims or 0 in dims:
            sz = num(t, "DW_AT_byte_size")
            return ("unsigned char", f"[{sz}]") if sz else (el, "[1]")
        return (el, "".join(f"[{d}]" for d in dims))
    if g in ("DW_TAG_structure_type", "DW_TAG_union_type"): return (emit(t), "")
    return ("unsigned int", "")

def emit(t):
    global out
    if t["off"] in emitted: return emitted[t["off"]]
    kw = "union" if t["tag"] == "DW_TAG_union_type" else "struct"
    n = nm(t)
    if not n: anon[0] += 1; n = f"anon_%d" % anon[0]
    cname = f"{kw} {n}"
    emitted[t["off"]] = cname
    size = num(t, "DW_AT_byte_size") or 0

    members, bits = [], collections.OrderedDict()
    for k in t["kids"]:
        if k["tag"] != "DW_TAG_member": continue
        loc = num(k, "DW_AT_data_member_location") or 0
        bs = num(k, "DW_AT_bit_size")
        if bs is None:
            members.append((loc, nm(k) or f"pad_{loc}", k))
        else:
            unit = num(k, "DW_AT_byte_size") or 4
            bo = num(k, "DW_AT_bit_offset")
            lsb = (unit * 8 - bo - bs) if bo is not None else 0
            bits.setdefault((loc, unit), []).append((nm(k), lsb, bs))

    body, checks, acc, cursor = [], [], [], 0
    slots = sorted([(l, "M", nm_, k) for l, nm_, k in members]
                   + [(l, "B", u, v) for (l, u), v in bits.items()], key=lambda x: x[0])
    for loc, kind, a, b in slots:
        if loc < cursor: continue                 # union overlay; skip
        if loc > cursor:
            body.append(f"    unsigned char _pad{cursor}[{loc - cursor}];")
            cursor = loc
        if kind == "M":
            pre, suf = type_of(ref(b))
            body.append(f"    {pre} {a}{suf};")
            checks.append(f"_Static_assert(__builtin_offsetof({cname}, {a}) == {loc}, "
                          f'"{n}.{a} moved");')
            cursor = loc + sizeof_t(ref(b))
        else:
            unit = a
            fld = f"_bits{loc}"
            storage = {1: "unsigned char", 2: "unsigned short",
                       4: "unsigned int", 8: "unsigned long long"}[unit]
            body.append(f"    {storage} {fld};")
            checks.append(f"_Static_assert(__builtin_offsetof({cname}, {fld}) == {loc}, "
                          f'"{n}.{fld} moved");')
            for bname, lsb, bsz in b:
                if not bname: continue
                mask = (1 << bsz) - 1
                acc.append(f"#define {n}_get_{bname}(p)  ((((p)->{fld}) >> {lsb}) & 0x{mask:x}u)")
                acc.append(f"#define {n}_set_{bname}(p,v) ((p)->{fld} = "
                           f"(((p)->{fld} & ~(0x{mask:x}u << {lsb})) | "
                           f"(((v) & 0x{mask:x}u) << {lsb})))")
            cursor = loc + unit
    if size > cursor:
        body.append(f"    unsigned char _pad{cursor}[{size - cursor}];")
    out.append(f"{cname} {{\n" + "\n".join(body) + "\n};")
    out.append(f"_Static_assert(sizeof({cname}) == {size}, \"{n} size\");")
    out += checks + acc
    return cname

structs = {}
for d in order:
    if d["tag"] == "DW_TAG_structure_type" and nm(d) and num(d, "DW_AT_byte_size") is not None:
        prev = structs.get(nm(d))
        if prev is None or (num(d, "DW_AT_byte_size") or 0) > (num(prev, "DW_AT_byte_size") or 0):
            structs[nm(d)] = d
print("/* layout-exact, generated from the shipping i386 DWARF -- do not edit */")
for tn in sys.argv[2:]:
    d = structs.get(tn)
    if d is None: print(f"/* {tn}: absent from this CU */", file=sys.stderr); continue
    emit(d)
for s in out: print(s)

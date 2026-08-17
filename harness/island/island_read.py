#!/usr/bin/env python3
"""Read the in-process island differential counters (patch 42)."""
import os, struct, sys
MAGIC=0x30345250; IMAGE_BASE=0x10000000
FMT="<6I"+"3I"+"12I"+"12I"+"2I"+"2I"+"160B"+"4I"+"160B"+"160B"
def pid_of(comm="mgs2_sse_rg353v"):
    m=[int(n) for n in os.listdir("/proc") if n.isdigit()
       and (lambda p: p and p.strip()==comm)(open(f"/proc/{n}/comm").read() if os.path.exists(f"/proc/{n}/comm") else None)]
    if len(m)!=1: raise SystemExit(f"expected one process, found {m}")
    return m[0]
def base(pid, mod="wined3d.dll"):
    for l in open(f"/proc/{pid}/maps"):
        f=l.split()
        if len(f)>=6 and f[2]=="00000000" and f[-1].endswith(mod): return int(f[0].split("-")[0],16)
    raise SystemExit("wined3d.dll not mapped")
pid=pid_of(); vma=int(sys.argv[1],0) if len(sys.argv)>1 else 0x101d30c0
addr=base(pid)+vma-IMAGE_BASE
fd=os.open(f"/proc/{pid}/mem", os.O_RDONLY)
raw=os.pread(fd, struct.calcsize(FMT), addr)
v=struct.unpack(FMT, raw)
if v[0]!=MAGIC: raise SystemExit(f"bad magic {v[0]:#x}")
i=6+3+12+12
checksum, samples = v[i], v[i+1]; i+=2
d3d_addr, ffp_size = v[i], v[i+1]; i+=2
ref=v[i:i+160]; i+=160
calls, match, mismatch, firstdiff = v[i], v[i+1], v[i+2], v[i+3]; i+=4
isl_ref=v[i:i+160]; i+=160
isl_nat=v[i:i+160]
print(f"pid {pid}  presents sampled {samples}  ffp_frag_settings {ffp_size} bytes")
print(f"island calls   {calls}")
print(f"  match        {match}")
print(f"  mismatch     {mismatch}")
if mismatch:
    print(f"  first differing byte at offset {firstdiff}")
    print(f"  x86 : {' '.join(f'{b:02x}' for b in isl_ref[:32])}")
    print(f"  arm : {' '.join(f'{b:02x}' for b in isl_nat[:32])}")
print()
if not calls: print("RESULT: the target was never called")
elif mismatch==0: print("RESULT: native ARM slice agrees with x86 on every call.")
else: print(f"RESULT: DIVERGENT on {mismatch} of {calls} calls.")

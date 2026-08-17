#!/usr/bin/env python3
"""Call frequency of the island's bridge entry points, per displayed frame."""
import os,struct,sys
MAGIC=0x36345250; IMAGE_BASE=0x10000000; SLOTS=40
NAMES=open("/tmp/island_entries.txt").read().split()
def pid_of(c="mgs2_sse_rg353v"):
    m=[]
    for n in os.listdir("/proc"):
        if not n.isdigit(): continue
        try:
            if open(f"/proc/{n}/comm").read().strip()==c: m.append(int(n))
        except OSError: pass
    if len(m)!=1: raise SystemExit(f"expected one process, found {m}")
    return m[0]
def base(pid,mod="wined3d.dll"):
    for l in open(f"/proc/{pid}/maps"):
        f=l.split()
        if len(f)>=6 and f[2]=="00000000" and f[-1].endswith(mod): return int(f[0].split("-")[0],16)
    raise SystemExit("not mapped")
pid=pid_of(); vma=int(sys.argv[1],0) if len(sys.argv)>1 else 0x101d30c0
addr=base(pid)+vma-IMAGE_BASE
fd=os.open(f"/proc/{pid}/mem",os.O_RDONLY)
h=struct.unpack("<6I", os.pread(fd,24,addr))
if h[0]!=MAGIC: raise SystemExit(f"bad magic {h[0]:#x}")
presents=struct.unpack("<I", os.pread(fd,4,addr+24))[0]
calls=struct.unpack(f"<{SLOTS}I", os.pread(fd,SLOTS*4,addr+28))
f=max(presents,1)
rows=sorted(((calls[i], NAMES[i] if i<len(NAMES) else f"slot{i}") for i in range(SLOTS)), reverse=True)
print(f"presents {presents}\n{'calls/frame':>12}  {'total':>10}  entry point")
for c,n in rows:
    if c: print(f"{c/f:12.1f}  {c:>10}  {n}")
tot=sum(calls)
print(f"\ntotal crossings/frame if all routed: {tot/f:.0f}")

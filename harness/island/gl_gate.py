#!/usr/bin/env python3
"""Read the GL context gate: Wine's view against native island code's view."""
import os, struct, sys
MAGIC=0x30345250; IMAGE_BASE=0x10000000
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
    raise SystemExit("wined3d.dll not mapped")
pid=pid_of(); vma=int(sys.argv[1],0) if len(sys.argv)>1 else 0x101d30c0
addr=base(pid)+vma-IMAGE_BASE
fd=os.open(f"/proc/{pid}/mem", os.O_RDONLY)
if struct.unpack("<I", os.pread(fd,4,addr))[0]!=MAGIC: raise SystemExit("bad magic")
# header 6 + 3 + 12 + 12 + 2 + 2 words, then 160B, then 4 words, then 160B + 160B,
# then 3 gl ptr words, then 4 counters, then 10+10
# struct order: ... ffp_settings[160], four island counters, three GL pointers,
# four probe counters, wine[10], native[10], island_ref[160], island_native[160]
off=(6+3+12+12+2+2)*4 + 160 + 4*4
gl=struct.unpack("<3I", os.pread(fd,12,addr+off)); off+=12
runs,agree,disagree,unavail = struct.unpack("<4I", os.pread(fd,16,addr+off)); off+=16
wine=struct.unpack("<10I", os.pread(fd,40,addr+off)); off+=40
nat =struct.unpack("<10I", os.pread(fd,40,addr+off))
names=["resolved","program","array_buf","elem_buf","active_tex","vp_x","vp_y","vp_w","vp_h","gl_error"]
print(f"probe runs {runs}   agree {agree}   disagree {disagree}   native unavailable {unavail}\n")
print(f"{'value':<14}{'wine (opengl32)':>18}{'native (libmali)':>18}")
for i,n in enumerate(names):
    mark = "" if i in (0,9) or wine[i]==nat[i] else "  <<<"
    print(f"{n:<14}{wine[i]:>18}{nat[i]:>18}{mark}")
print()
if unavail and not agree and not disagree:
    print("RESULT: island code could not reach the native driver.")
elif disagree==0 and agree:
    print("RESULT: native island code observes the same GL context as Wine.")
    print("        Calling GL directly from the island is viable.")
else:
    print(f"RESULT: DISAGREEMENT on {disagree} of {runs} probes -- do not call GL from the island.")

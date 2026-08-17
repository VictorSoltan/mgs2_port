# Building Box86 for this port

Reproduced 15 August 2026 on a machine with no armhf toolchain installed and no
root: the cross compiler and sysroot are extracted from `.deb` files into a
directory, which is enough to build and link.

```sh
git clone https://github.com/ptitSeb/box86.git box86-src
cd box86-src && git checkout 0579f8b9c47d87d700724f4cce559b06cbd2b0f5
for p in ../mgs2-rg353vs-port/box86-patches/0*.patch; do patch -p1 -F0 --batch < "$p"; done
```

All seven apply with zero fuzz **in order**; a dry run of 04-06 against the
pristine tree fails, because they depend on 01-03.

Patch 07 is the whole native ARM island. It replaces a former 07-13, which did
not apply at all: each had been exported from a pristine tree independently, so
they re-added what patch 01 and patches 02/05/06 had already added, and the
series broke from 07 onward the first time it was applied in order. Nobody had
tried. Check the series, not just the tree it came from.

Patch 07 needs the prebuilt ARM objects in `src/island/`, from
`harness/island/full/build_island_objects.sh`, and Wine patches 48 and 49.

### Reproducibility has a path caveat

`__FILE__` bakes the absolute source path into the dynarec's log strings, so
`.rodata` -- and every literal-pool reference into it -- depends on where the
tree lives. Building the series at a path of the same length as the reference
reproduces `.text` byte for byte and leaves 501 differing bytes: the build-id and
the build timestamp. Building it somewhere else leaves ~99,000, with `.text`
still the same size and the same code. Compare sections before concluding
anything from a whole-file hash.

Toolchain without root:

```sh
apt-get download gcc-15-arm-linux-gnueabihf cpp-15-arm-linux-gnueabihf \
    gcc-15-cross-base-ports libgcc-15-dev-armhf-cross libgcc-s1-armhf-cross \
    binutils-arm-linux-gnueabihf libc6-dev-armhf-cross libc6-armhf-cross \
    linux-libc-dev-armhf-cross
for d in *.deb; do dpkg -x "$d" root/; done
export PATH="$PWD/root/usr/bin:$PATH"
export LD_LIBRARY_PATH="$PWD/root/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
```

`LD_LIBRARY_PATH` is required: the extracted `as` and `ld.bfd` load
`libbfd-*-armhf.so` from that directory. The sysroot must be the extraction root
itself, not `root/usr/arm-linux-gnueabihf`, or the libc linker scripts resolve
their absolute paths outside it.

Configure and build. The `MGS2_GLIBC24_COMPAT` block from patch 05 is required
with an Ubuntu cross sysroot, whose libm defaults would otherwise raise the
binary's requirement to `GLIBC_2.43` and fail to start on the handheld:

```sh
cmake .. -DRK3399=1 -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_SYSTEM_NAME=Linux -DCMAKE_SYSTEM_PROCESSOR=arm \
  -DCMAKE_C_COMPILER=arm-linux-gnueabihf-gcc -DCMAKE_SYSROOT="$SYSROOT" \
  -DCMAKE_C_FLAGS="-DMGS2_GLIBC24_COMPAT" \
  -DCMAKE_EXE_LINKER_FLAGS="-Wl,--wrap=log10f,--wrap=atan2f,--wrap=asinf,--wrap=acosf,--wrap=sinhf,--wrap=acoshf,--wrap=coshf,--wrap=sqrtf"
make -j8
arm-linux-gnueabihf-strip --strip-unneeded -o box86.compat box86
```

Verify on the device before anything else; the banner carries the commit:

```text
Box86 with Dynarec v0.3.9 0579f8b9 built on Aug 15 2026
```

`box86-mgs2-rebuild1`, sha256
`7c802221e767f70e7f3ee86b44c9455753a0f383001e9c0d9a9804584257ed19`, is that
build. It is **not** production and is not selected by any launcher; the
production binary remains `box86-native-dsound-fir1`. It exists so the native
bridge work has a Box86 that can be rebuilt from source on this workstation.

Note the SD card runs at or near 100% full. A 26 MB unstripped binary will not
copy; strip first, and stage through `/tmp`, which is tmpfs.

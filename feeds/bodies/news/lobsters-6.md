Many<sup>[[1]](https://stoppels.ch/2026/11/12/paths-in-pieces.html#fn1)[[2]](https://stoppels.ch/2026/11/12/paths-in-pieces.html#fn2)[[3]](https://stoppels.ch/2026/11/12/paths-in-pieces.html#fn3)[[4]](https://stoppels.ch/2026/11/12/paths-in-pieces.html#fn4)[[5]](https://stoppels.ch/2026/11/12/paths-in-pieces.html#fn5)[[6]](https://stoppels.ch/2026/11/12/paths-in-pieces.html#fn6)[[7]](https://stoppels.ch/2026/11/12/paths-in-pieces.html#fn7)[[8]](https://stoppels.ch/2026/11/12/paths-in-pieces.html#fn8)[[9]](https://stoppels.ch/2026/11/12/paths-in-pieces.html#fn9)</sup> Linux distributions and package managers audit just-built binaries for non-relocatable absolute paths. If a binary contains a path `/path/from/build/machine`, it might not run on the end-user's machine.

Now, a basic `grep` on the binary, or a slightly more sophisticated

```
$ strings bin/app | grep /path/from/build/machine
```

using GNU binutils's `strings` will detect these paths, right?

The answer is *no*, at least when using GCC and targeting `x86-64`: you should *not* assume that string constants end up literally in the binary.

## Basic example

In this C++ source we create a `std::string` from a string constant:

```
#include <iostream>
#include <string>

#define PREFIX "/home/linuxbrew/.linuxbrew"

int main() {
  std::string prefix{PREFIX};
  std::cout << prefix << '\n';
}
```

Compile with GCC 12 or later and run, which prints the path:

```
$ g++ -O2 main.cpp -o main
$ ./main
/home/linuxbrew/.linuxbrew
```

But the path occurs precisely 0 times in the binary itself:

```
$ grep -acF /home/linuxbrew/.linuxbrew main
0
$ strings ./main | grep -cF /home/linuxbrew/.linuxbrew
0
```

Surely these bytes must be part of the binary *somewhere*? Let's run `strings` on it and grep just for the `/home` prefix:

```
$ strings ./main | grep /home
/home/linuxbrew/xbrew/.linuxbrew
```

Wait, did GCC just turn

```
/home/linuxbrew/.linuxbrew
```

into an entirely *different* path

```
/home/linuxbrew/xbrew/.linuxbrew
```

with a made-up subdirectory `xbrew`? How?

## Store by pieces

The answer is that GCC optimizes our `std::string{PREFIX}`. The fact that we see something that looks like the prefix is merely a coincidence.

GCC splits our string up into two (overlapping) pieces of 16 bytes, like so

```
/home/linuxbrew/.linuxbrew
|--------------|..........  - constant 1
..........|--------------|  - constant 2
```

which fit exactly in `xmm` registers, so that it can copy our string to the `std::string` buffer using vectorized move instructions.

Filtering the relevant bits from `g++ -O2 -S -masm=intel`, we get

```
movdqa  xmm0, XMMWORD PTR .LC0[rip]
movups  XMMWORD PTR [rax], xmm0
movdqa  xmm0, XMMWORD PTR .LC1[rip]
movups  XMMWORD PTR 10[rax], xmm0
```

and our string is stored at `.LC0` and `.LC1` as constants, which just happen to be next to each other in the binary:

```
.LC0:
.quad 7596498784141404207
.quad 3420313983963919726
.LC1:
.quad 7795220194874516088
.quad 8603408430414524009
```

In general, this happens when a string constant is copied into a buffer, as with `std::string`, `strcpy` or `memcpy`; strings that are only passed around as pointers, like in `fopen(PREFIX "/x", "r")`, stay intact.

## Deduplication

Some package managers like Conda and Spack install packages into a padded prefix during their builds, with the idea that they can be “relocated” to a shorter prefix of the user's choice: the binaries are patched in-place. Conda uses a repeated string `_placehold` in a directory name to make the prefix long enough.

Now, even if we pick a 256-byte path (a convenient multiple of all x86-64 register widths) by padding the path Conda-style

```
#define PREFIX "/home/conda/feedstock_root/build_artifacts/" \
               "foo_1699999999999/_h_env" \
               "_placehold_placehold_placehold_placehold_placehold" \
               "_placehold_placehold_placehold_placehold_placehold" \
               "_placehold_placehold_placehold_placehold_placehold" \
               "_placehold_placehold_placehold_placeho/"
```

and keep our fingers crossed that GCC puts the pieces of the path contiguously in the binary, we do *not* see our prefix back in the binary. What we get instead is a much shorter string of only 176 bytes (that is 11 times 16):

```
$ strings main | grep /home
/home/conda/feedstock_root/build_artifacts/foo_1699999999999/_h_env_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placeho/
```

This is thanks to a further optimization: since the string `_placehold` repeats every 10 bytes, the 16-byte pieces repeat every `lcm(10, 16) = 80` bytes, and GCC needs to store only 5 distinct 16-byte constants for the padding:

```
/home/conda/feed
stock_root/build
_artifacts/foo_1
699999999999/_h_
env_placehold_pl
acehold_placehol  # note
d_placehold_plac  # that
ehold_placehold_  # this
placehold_placeh  # is
old_placehold_pl  # cyclic
acehold_placeho/
```

## Is this optimization helpful?

For string literals, I don't think so. Clang does not split strings into constants, yet it generates essentially the same instructions. For example, take a longer path, and target AVX2 with `-march=x86-64-v3`:

```
#define PREFIX "/home/linuxbrew/.linuxbrew/Cellar/foo/1.2.3/share/foo"
```

Clang simply puts the string in a section dedicated to strings, `.rodata.str1.1`:

```
.L.str:
.asciz "/home/linuxbrew/.linuxbrew/Cellar/foo/1.2.3/share/foo"
```

and copies its 53 bytes with two overlapping 32-byte `ymm` loads and stores, at offsets 21 and 0:

```
vmovups ymm0, ymmword ptr [rip + .L.str+21]
vmovups ymmword ptr [rax + 21], ymm0
vmovups ymm0, ymmword ptr [rip + .L.str]
vmovups ymmword ptr [rax], ymm0
```

That isn't particularly different from GCC's version, which loads the same two pieces from constants in `.rodata.cst32` instead:

```
vmovdqa ymm0, YMMWORD PTR .LC0[rip]
vmovdqu YMMWORD PTR [rax], ymm0
vmovdqa ymm0, YMMWORD PTR .LC1[rip]
vmovdqu YMMWORD PTR 21[rax], ymm0
```

So what does GCC gain? In terms of performance, probably nothing measurable: both do the same loads and stores. With repeated pieces, GCC might have a slight edge, because a repeated piece is loaded once and stored multiple times (11 loads for 16 stores in the earlier example). It also uses aligned reads, but that matters only for ancient CPUs.

In terms of size, GCC's pieces can take more space than the string itself: overlapping bytes are stored twice, and the pieces are aligned to 16, 32 or 64 bytes. The 53-byte path above takes 64 bytes as two pieces, against 54 bytes as a string. It only pays off if it results in deduplication, for example when many strings share a prefix of at least 16 bytes for SSE2, 32 bytes for AVX2, and 64 bytes for AVX-512. Presumably deduplication does not save much in practice, especially now that some distributions use AVX2 as their baseline.

## Can I disable this optimization?

Other than compiling with `-Os`, not really. From GCC 10 onwards (maybe older versions too?) the split-into-pieces optimization triggers for strings up to 256 bytes even without specifying `-march`. From GCC 12 it is relative to the target's vector width, so longer strings get split too: up to 512 bytes for AVX2 and 1024 bytes for AVX-512.

I believe the only control you have over this is setting the maximum vector width to 128 bits (forcing `xmm` operations), by passing `-mstore-max=128`. But this merely restores old defaults, and means strings of up to 256 bytes are still stored in pieces.

## Maybe post-hoc scanning is bad practice?

These post-build audits for absolute paths are popular, but you could argue that they are too brittle to start with, so why expect them to work at all?

Indeed, Debian goes much further than a bad-path scan. Their audit asserts that a package can be rebuilt bit for bit in different circumstances: on a different machine, with a different user, time and date, hostname, locale, etc. That is a much more reliable way to keep machine-specific details out of binaries.<sup>[[10]](https://stoppels.ch/2026/11/12/paths-in-pieces.html#fn10)</sup>

I would argue that, despite that, it is *still* useful to keep string constants literally in the binary, even on Debian, because it improves interpretability of binaries. Running `strings ./binary` is such a simple and convenient way to get insight into an opaque binary blob, that it outweighs the marginal savings that come with splitting and deduplication. It is reminiscent of Fedora and Ubuntu turning frame pointers back on by default, despite the small overhead, just to make profilers and tracing tools work more reliably.

Other than that, there is the argument of binary patching, which — despite being considered somewhat brittle — is common practice in Conda and Spack: upon install to a user-specified location, the absolute paths are patched in-place accordingly, through what can be seen as a glorified `sed` invocation. This only works if the path is stored in one piece.

If you'd like to discuss this, a good place is the [gcc-patches thread](https://gcc.gnu.org/pipermail/gcc-patches/2026-November/738364.html) that I started recently, with an initial attempt at a patch that adds a way to opt out.

[[1]](https://stoppels.ch/2026/11/12/paths-in-pieces.html#fnref1) [RPM (Fedora, RHEL, openSUSE)](https://github.com/rpm-software-management/rpm/blob/4187d693cfd4704e3ffdf6483ea91a0d56134333/scripts/check-buildroot#L30-L42): `check-buildroot` greps every installed file for the build root.

[[2]](https://stoppels.ch/2026/11/12/paths-in-pieces.html#fnref2) [Arch Linux](https://gitlab.archlinux.org/pacman/pacman/-/blob/a6f7467d8c7c4d7e9cc846884e74c0ab7215c48d/scripts/libmakepkg/lint_package/build_references.sh.in#L30-L41): `makepkg` warns about references to `$srcdir` and `$pkgdir`.

[[3]](https://stoppels.ch/2026/11/12/paths-in-pieces.html#fnref3) [Yocto / OpenEmbedded](https://git.openembedded.org/openembedded-core/tree/meta/classes-global/insane.bbclass?id=c2ea9568b768de7c479aba22f15520793a7dace4#n427): the `buildpaths` QA check.

[[4]](https://stoppels.ch/2026/11/12/paths-in-pieces.html#fnref4) [FreeBSD ports](https://github.com/freebsd/freebsd-ports/blob/7ea5a0ba45376d1ca480b274157370705d3d01b2/Mk/Scripts/qa.sh#L201-L223): the stage QA greps for the staging directory.

[[5]](https://stoppels.ch/2026/11/12/paths-in-pieces.html#fnref5) [pkgsrc](https://github.com/NetBSD/pkgsrc/blob/e9b59cbd05f2c2ab1c37f8a8524bd38b1e256de8/mk/check/check-wrkref.mk#L90-L113): `CHECK_WRKREF`, off unless a package developer turns it on.

[[6]](https://stoppels.ch/2026/11/12/paths-in-pieces.html#fnref6) [Homebrew](https://github.com/Homebrew/brew/blob/8679d30f156018b0b184c64ab21a784f64b1d880/Library/Homebrew/keg_relocate.rb#L702-L775): `brew bottle` scans for the prefix to decide whether a bottle is relocatable.

[[7]](https://stoppels.ch/2026/11/12/paths-in-pieces.html#fnref7) [conda-build](https://github.com/conda/conda-build/blob/7dd6a86caf822254aac3217c5fded17cb915e004/conda_build/build.py#L1014-L1080): files containing the build prefix are listed in `info/has_prefix`, to be rewritten on install.

[[8]](https://stoppels.ch/2026/11/12/paths-in-pieces.html#fnref8) [rattler-build](https://github.com/prefix-dev/rattler-build/blob/0252f9ca2c5f8a9ab039b96ef09dc1d52d17de7d/crates/rattler_build_package/src/prefix/detector.rs#L15-L24): the same scheme as conda-build, with `memmem`.

[[9]](https://stoppels.ch/2026/11/12/paths-in-pieces.html#fnref9) [Julia's BinaryBuilder](https://github.com/JuliaPackaging/BinaryBuilder.jl/blob/d2b11c267ef8029af0f46a88b767246d7b9df1d1/src/auditor/filesystems.jl#L25-L45): `check_absolute_paths` warns about the build prefix in any file.

[[10]](https://stoppels.ch/2026/11/12/paths-in-pieces.html#fnref10) Even Debian keeps one path fixed: since early 2024 both builds use the [same build directory](https://tests.reproducible-builds.org/debian/index_variations.html), because it is recorded in the `.buildinfo` file and reused when rebuilding. So a build path embedded in a binary goes unnoticed there too.
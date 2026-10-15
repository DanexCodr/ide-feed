ZXC is a lossless data compression library written in C, distributed as **libzxc**. It is designed for data that is compressed once and read many times: firmware images, game assets, application bundles, and content delivered to many devices. The encoder spends extra time up front so that decompression runs at several gigabytes per second on ARM and x86. At every compression level ZXC decodes faster than LZ4, and produces output of equal or smaller size.

ZXC is free software, released under the [BSD 3-Clause License](https://opensource.org/license/bsd-3-clause). It has no dependencies, and official bindings exist for Rust, Python, Node.js and Go.

Development happens on [GitHub](https://github.com/hellobertrand/zxc).

**The current release is ZXC 0.15.0**, released on 2026-10-13.
  See the [changelog](https://libzxc.org/docs/changelog/) for what changed, and [Downloading ZXC](https://libzxc.org/#download) below.

## Specifications

| Parameter | Value | Notes |
| --- | --- | --- |
| Compression levels | 1 to 7 | Default 3 |
| Block size | 4 KB to 2 MB, powers of two | Default 512 KB; 256 KB for streaming |
| Decompression context | ≈ 512 KB | At the default block size |
| Compression context | ≈ 1.78 MB | ≈ 1.03 MB with 256 KB blocks |
| In-place decompression margin | ≈ 1 % of the archive | Use `zxc_decompress_inplace_bound()` |
| Random access | O(1) per block | Requires a seek table (`-S`) |
| Integrity | Optional per-block checksum | rapidhash |
| Dictionaries | External `.zxd` file | Referenced by a 32-bit ID |
| Threading | Multi-threaded streaming | Thread count detected automatically |
| Architectures | x86_64, ARM64, ARMv7, ARMv6, RISC-V, POWER, s390x, i386 | Tested in CI |
| Wire format | Version 9 | [Specification](https://libzxc.org/docs/format/) |
| Library name | libzxc | pkg-config `libzxc`; CMake `zxc::zxc_lib`; Debian `libzxc-dev` |
| Language, dependencies | C17, none | Bindings for Rust, Python, Node.js, Go |
| License | BSD 3-Clause |  |

## Why ZXC?

LZ4 is symmetric: it compresses about as fast as it decompresses. That suits logs and swap, but not data that is shipped. A firmware image is compressed once on a build server and decompressed on every device that installs it, so time saved during compression helps nobody.

ZXC moves the work to the encoder. Match selection, optimal parsing and statistics tuning are done once, and the bitstream is laid out for the pipelines and branch predictors of modern processors. The decoder stays short, has few branches, and uses SIMD where it is available.

Typical uses:

- Firmware and over-the-air updates. In-place decompression keeps peak memory close to the decompressed size.
- Game assets and application start-up, where load time and battery use matter.
- Packaged artefacts and content delivery, where more original data is delivered per byte read from disk or network.
- Read-heavy storage. Seekable archives can decode any block without reading the blocks before it.

## Features

- Seekable archives. An optional seek table gives O(1) random access to any block.
- In-place decompression. Decode inside a single buffer with about 1 % overhead instead of a second allocation.
- Trained dictionaries. zxc --train builds a dictionary for small, similar payloads such as JSON documents, log lines or RPC messages.
- Multi-threaded streaming. The file and stream interfaces split work across processor cores.
- Hand-written SIMD. SSE2, AVX2 and AVX-512 with run-time selection on x86; NEON on ARMv8 and later.
- Portable. Tested on x86_64, ARM64, ARMv7, ARMv6, RISC-V, POWER, s390x and i386.
- Careful interface. Every call takes an explicit output capacity. The library is thread-safe, with reusable contexts for tight loops and static contexts for targets without a heap.
- Optional checksums. Per-block integrity checks based on rapidhash.
- Documented format. The wire format (version 9) is specified in full, and public conformance vectors let others write independent decoders.

## Compression levels

Seven levels trade compression time for size. Decompression stays in the multi-GB/s range at every level. Level 3 is the default.

| Level | Name | Suited for | Size % | Decode MB/s | Encode MB/s |
| --- | --- | --- | --- | --- | --- |
| 1 | Fastest | Real-time assets, games, UI | 61.76 | 13,513 | 886 |
| 2 | Fast | Real-time assets, games, UI | 53.86 | 11,320 | 588 |
| 3 | Default | General use; smaller and faster to decode than LZ4 | 46.65 | 9,707 | 267 |
| 4 | Balanced | General use, a little denser | 43.43 | 8,790 | 194 |
| 5 | Compact | Embedded and firmware | 40.83 | 8,118 | 114 |
| 6 | Density | Archives and read-mostly data; beats LZ4HC on both axes | 36.28 | 6,884 | 14.5 |
| 7 | Ultra | When size dominates; smaller than zstd -1, decodes about 2× faster | 33.09 | 5,054 | 9.71 |

Size is the compressed size as a percentage of `silesia.tar`. Speeds are single-threaded on Apple M2 with lzbench 2.4.1. Blocks are 512 KB by default; use `-B 256K` for streaming or memory-constrained targets.

## Benchmarks

ZXC is included in the two main open-source compression benchmark suites, [lzbench](https://github.com/inikep/lzbench) and [TurboBench](https://github.com/powturbo/TurboBench), so the figures below can be reproduced with either tool alongside more than 70 other codecs. Benchmarks also run on every commit on x86_64 and ARM64 machines; see the [latest results](https://github.com/hellobertrand/zxc/actions/workflows/benchmark.yml).

The decoder's speed is paid for at compression time, and on this axis LZ4 and Zstandard are ahead. Levels 1 and 2 still compress at several hundred MB/s; levels 6 and 7 run at about 10 MB/s, slower than `lz4hc -9`, and are meant for data that is compressed once and read many times.

Raw decode speed leaves out half of the picture. When the decoder is fed from a disk, a network or another core, the compressed bytes are what is scarce, and what matters is how much original data each compressed megabyte yields. Effective throughput combines both: decode speed × 100 / ratio (%). On this measure every ZXC level is ahead of LZ4, on all four processors.

Dividing the clock frequency by the decompression speed gives the cost of each decompressed byte in processor cycles, which compares processors running at different frequencies. ZXC spends less than one cycle per byte at every level.

Apple M2, macOS 26, Clang 21, -march=native. Single thread, lzbench 2.4.1, `silesia.tar`. Speeds in MB/s; size as a percentage of the input.

| Codec and level | Compression | Decompression | Size % |
| --- | --- | --- | --- |
| zxc -1 | 886 | 13,513 | 61.76 |
| zxc -2 | 588 | 11,320 | 53.86 |
| zxc -3 | 267 | 9,707 | 46.65 |
| zxc -4 | 194 | 8,790 | 43.43 |
| zxc -5 | 114 | 8,118 | 40.83 |
| zxc -6 | 14.5 | 6,884 | 36.28 |
| zxc -7 | 9.71 | 5,054 | 33.09 |
| lz4 | 814 | 4,774 | 47.60 |
| lz4 --fast -17 | 1,347 | 5,609 | 62.15 |
| lz4hc -9 | 48.4 | 4,522 | 36.75 |
| lzav -1 | 686 | 3,876 | 39.91 |
| snappy | 661 | 3,258 | 47.85 |
| zstd --fast --1 | 723 | 2,538 | 41.01 |
| zstd -1 | 645 | 1,803 | 34.53 |
| zstd -3 | 375 | 1,680 | 31.20 |
| zlib -1 | 135 | 378 | 36.45 |

Google Axion (Neoverse V2), GCP C4A, GCC 14.4, -march=native. Single thread, lzbench 2.4.1, `silesia.tar`. Speeds in MB/s; size as a percentage of the input.

| Codec and level | Compression | Decompression | Size % |
| --- | --- | --- | --- |
| zxc -1 | 885 | 9,564 | 61.76 |
| zxc -2 | 593 | 7,895 | 53.86 |
| zxc -3 | 256 | 6,571 | 46.65 |
| zxc -4 | 186 | 6,105 | 43.43 |
| zxc -5 | 109 | 5,683 | 40.83 |
| zxc -6 | 13.5 | 4,950 | 36.28 |
| zxc -7 | 8.82 | 3,563 | 33.09 |
| lz4 | 730 | 4,258 | 47.60 |
| lz4 --fast -17 | 1,278 | 4,954 | 62.15 |
| lz4hc -9 | 43.2 | 3,850 | 36.75 |
| lzav -1 | 576 | 2,949 | 39.91 |
| snappy | 566 | 2,295 | 47.85 |
| zstd --fast --1 | 302 | 2,291 | 41.01 |
| zstd -1 | 523 | 1,642 | 34.53 |
| zstd -3 | 329 | 1,525 | 31.20 |
| zlib -1 | 115 | 389 | 36.45 |

AMD EPYC 9B45 (Zen 5), GCP C4D, GCC 14.4, -march=native. Single thread, lzbench 2.4.1, `silesia.tar`. Speeds in MB/s; size as a percentage of the input.

| Codec and level | Compression | Decompression | Size % |
| --- | --- | --- | --- |
| zxc -1 | 868 | 11,609 | 61.76 |
| zxc -2 | 585 | 10,332 | 53.86 |
| zxc -3 | 253 | 8,335 | 46.65 |
| zxc -4 | 183 | 7,508 | 43.43 |
| zxc -5 | 110 | 7,014 | 40.83 |
| zxc -6 | 15.3 | 6,045 | 36.28 |
| zxc -7 | 10.2 | 4,724 | 33.09 |
| lz4 | 766 | 5,052 | 47.60 |
| lz4 --fast -17 | 1,284 | 5,305 | 62.15 |
| lz4hc -9 | 45.4 | 4,861 | 36.75 |
| lzav -1 | 699 | 3,603 | 39.91 |
| snappy | 564 | 2,420 | 47.89 |
| zstd --fast --1 | 664 | 2,451 | 41.01 |
| zstd -1 | 606 | 1,898 | 34.53 |
| zstd -3 | 369 | 1,733 | 31.20 |
| zlib -1 | 134 | 392 | 36.45 |

AMD EPYC 7B13 (Zen 3), GCP C2D, GCC 14.4, -march=native. Single thread, lzbench 2.4.1, `silesia.tar`. Speeds in MB/s; size as a percentage of the input.

| Codec and level | Compression | Decompression | Size % |
| --- | --- | --- | --- |
| zxc -1 | 724 | 8,155 | 61.76 |
| zxc -2 | 481 | 6,807 | 53.86 |
| zxc -3 | 214 | 5,252 | 46.65 |
| zxc -4 | 157 | 4,952 | 43.43 |
| zxc -5 | 93.3 | 4,779 | 40.83 |
| zxc -6 | 11.9 | 4,290 | 36.28 |
| zxc -7 | 7.97 | 3,188 | 33.09 |
| lz4 | 638 | 3,883 | 47.60 |
| lz4 --fast -17 | 1,108 | 4,485 | 62.15 |
| lz4hc -9 | 37.1 | 3,731 | 36.75 |
| lzav -1 | 459 | 2,955 | 39.91 |
| snappy | 507 | 1,837 | 47.89 |
| zstd --fast --1 | 486 | 1,784 | 41.01 |
| zstd -1 | 444 | 1,339 | 34.53 |
| zstd -3 | 232 | 1,178 | 31.20 |
| zlib -1 | 106 | 358 | 36.45 |

## Downloading ZXC

Source and binary archives for Linux, macOS and Windows are published on the [releases page](https://github.com/hellobertrand/zxc/releases). Each archive carries SLSA build provenance, which you can check with:

```
gh attestation verify zxc-0.15.0-linux-x86_64.tar.gz --repo hellobertrand/zxc
```

ZXC is also packaged by distributions and package managers:

```
sudo apt install zxc libzxc-dev
```

```
brew install zxc
```

```
vcpkg install zxc
```

```
conan install -r conancenter --requires="zxc/[*]" --build=missing
```

```
winget install hellobertrand.zxc
```

Which version each distribution currently ships is tracked by [Repology](https://repology.org/project/zxc/versions):

[![Packaging status of ZXC across distributions and package managers, from Repology.](https://repology.org/badge/vertical-allrepos/zxc.svg)](https://repology.org/project/zxc/versions)

To build from source you need CMake 3.14 or later and a C17 compiler (GCC, Clang or MSVC):

```
git clone https://github.com/hellobertrand/zxc.git
cd zxc
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
sudo cmake --install build
```

The installation provides CMake (`find_package(zxc)`, target `zxc::zxc_lib`) and pkg-config (`libzxc`) files. Meson users can include ZXC as a subproject; see the [integration guide](https://libzxc.org/docs/install/).

## Quick start

The `zxc` command reads and writes files or pipes, and can be used as a compressor by `tar`:

```
# Compress (level 3 by default), then decompress
zxc -5 assets.tar assets.tar.zxc
zxc -d assets.tar.zxc assets.tar

# Seekable archive, for random access
zxc -S big.bin big.bin.zxc

# As a compressor for tar
tar -I 'zxc -5' -cf data.tar.zxc data/

# Measure speed on your own machine
zxc -b input_file
```

From C, the buffer interface compresses and decompresses in one call each:

```
#include "zxc.h"

uint64_t bound = zxc_compress_bound(src_size);
zxc_compress_opts_t c = {
    .level            = ZXC_LEVEL_DEFAULT,
    .checksum_enabled = 1,
};
int64_t csize = zxc_compress(src, src_size, dst, bound, &c);

zxc_decompress_opts_t d = { .checksum_enabled = 1 };
int64_t n = zxc_decompress(dst, csize, out, out_cap, &d);
if (n < 0)
    fprintf(stderr, "zxc: %s\n", zxc_error_name((int)n));
```

See the [examples](https://libzxc.org/docs/examples/) for the streaming, context, seekable and dictionary interfaces, the [API reference](https://libzxc.org/docs/api/) for every function, and the [manual page](https://libzxc.org/docs/cli/) for all command options.

## Language bindings

The official bindings are maintained in the main repository and released with the library. They are published as `zxc-compress`, because the name `zxc` is taken on some registries.

| Language | Installation | Package |
| --- | --- | --- |
| Rust | `cargo add zxc-compress` | [crates.io](https://crates.io/crates/zxc-compress) |
| Python | `pip install zxc-compress` | [PyPI](https://pypi.org/project/zxc-compress) |
| Node.js | `npm install zxc-compress` | [npm](https://www.npmjs.com/package/zxc-compress) |
| Go | `go get github.com/hellobertrand/zxc/wrappers/go` | [source](https://github.com/hellobertrand/zxc/tree/main/wrappers/go) |
| WebAssembly | build with Emscripten | [source](https://github.com/hellobertrand/zxc/tree/main/wrappers/wasm) |

Bindings maintained by others: [go-zxc](https://github.com/meysam81/go-zxc) (Go), [zxc-nim](https://github.com/openpeeps/zxc-nim) (Nim), and a [Free Pascal port](https://github.com/Xelitan/Free-Pascal-port-of-ZXC-compressor-decompressor).

## Testing

- Fuzzed around the clock by Google OSS-Fuzz, with eight harnesses covering compression, decompression, the block API, in-place decoding, streaming, seekable archives and dictionaries; they reach over 80 % of the library's lines (coverage history).
- The same harnesses run under ClusterFuzzLite on every pull request.
- AddressSanitizer, UndefinedBehaviorSanitizer and Valgrind in continuous integration; Cppcheck, the Clang Static Analyzer and CodeQL on every change; continuous security analysis of the code and its dependencies by Snyk.
- Decoder conformance vectors and byte-exact tests of the encoder output, so that the wire format cannot change by accident.
- Builds and tests across several operating systems, compilers and eight processor architectures.
- Pinned CI dependencies, tracked by the OpenSSF Scorecard.

## Getting help and contributing

Questions and ideas are welcome in [GitHub Discussions](https://github.com/hellobertrand/zxc/discussions). Please report bugs on the [issue tracker](https://github.com/hellobertrand/zxc/issues), and security problems privately as described in the [security policy](https://github.com/hellobertrand/zxc/security/policy).

Contributions are welcome; read the [contribution guidelines](https://github.com/hellobertrand/zxc/blob/main/.github/CONTRIBUTING.md) first. You can also support the project through [GitHub Sponsors](https://github.com/sponsors/hellobertrand).
How can we parse an IPv4 address with a throughput of 75 instructions in 15 CPU cycles, taking as low as ~3ns on an M6 processor?

## Table Of Contents

## Is This Post ...?

I know what you're trying to figure out. No. This blog post is not AI generated.

With that out of the way ...

## What Happened?

As of writing this article, Swift doesn't have a unified or high quality platform-independent stack of basic networking types, with implementations being scattered across Apple's proprietary [Network framework](https://developer.apple.com/documentation/network) and the open-source [swift-nio](https://github.com/apple/swift-nio).

That’s why lately I've been working on [swift-endpoint](https://github.com/swift-dns/swift-endpoint), parts of which are going to make it to Swift’s new [swift-networking-types](https://github.com/swiftlang/swift-networking-types).  

At a minimum [swift-networking-types](https://github.com/swiftlang/swift-networking-types) will provide similar functionality to [Go's net/netip](https://pkg.go.dev/net/netip), parts of [Rust's std::net](https://doc.rust-lang.org/std/net/index.html), and parts of [Boost's Asio](https://www.boost.org/doc/libs/latest/doc/html/boost_asio/reference.html) APIs.

As part of my work on swift-endpoint, I've been looking for elegant API shapes as well as performant implementations for IP address parsing and serializations, results of which are visible in the [Performance section](https://github.com/swift-dns/swift-endpoint#performance) of swift-endpoint's README, where the APIs are compared to Darwin and glibc's inet APIs as reference points.

## Yet Another IPv4 Parser

There are already lots of high-performance implementations in this space. Many people have contributed to these implementations over the years, be it in form of research, smart bit hacks, or completely new implementations. Most of the research can be attributed to [Daniel Lemire](https://github.com/lemire) and [Wojciech Muła](https://github.com/WojciechMula), although many more have also been involved.

The majority of the existing IPv4 parsing implementations are pretty clever and have implemented different kinds of tricks, bit hacks, and vectorizations to achieve high performance.  

This new algorithm would not be possible without their prior art.

However, the bulk of the top-performing implementations make assumptions and decisions that don't fit Swift:

- An IPv4 address can be as short as 7 bytes (for 1.1.1.1) and as long as 15 bytes (for 255.255.255.255).
  - Lots of the other implementations rely on the existence of an 8th null byte, or they need padding, or they require 16 bytes upfront as a contract.
  - In context of the Swift language, this would be very unexpected. Contracts need to be enforced at API level. Null byte is not a thing outside interoperability with C/C++.
- Some of the top-performing implementations use lookup tables.
  - Benchmark results of implementations that use lookup tables assume that the L1 cache is already populated with the hot cache lines of those lookup tables. That's not always the case.
  - In reality, the preference is to achieve maximum performance without lookup tables, hopefully matching or beating an implementation that uses lookup tables.
  - Not using lookup tables typically means less binary size, less memory bandwidth usage, less reliance on memory latency or CPU cache statuses, thus more predictable performance.
  - However, it's still hard to come up with metrics about when and where and how much to use lookup tables.
    - In a lot of cases table lookups are actually worth it and can result in big performance wins.
- SIMD instructions can differ a lot on different CPUs.
  - In contrast, scalar implementations tend to be better supported by compilers and require little to no manual intrinsic function calls while being highly portable.
  - This is not true about the highest performing vectorized codes which tend to use the latest and greatest instructions provided by a given CPU generation, therefore taking hits on portability.
  - On the bright side it's also possible to write code that optimizers such as LLVM can typically resolve to well-performing auto-vectorized code, without getting deep into Instruction Set Architectures (ISAs) of different CPU generations or having to write multiple implementations to support different CPU generations.
  - A good example of auto-vectorized code's performance wins is this PR to increase performance of swift-foundation's Base64 encoding by ~3 times. I plan to share my experience with auto-vectorization in another post.

Knowing all those, I was still in search of some better-fitting IP address parsing/serializing implementations.  

That's how I ended up thinking more about them, and eventually came up with a new idea for a new IPv4 parsing algorithm. One that also performs well.

## A New IPv4 Parsing Algorithm

Here are some IPv4 addresses that a correct algorithm would need to successfully parse, each containing *4 segments* separated by dots:

- 1.1.1.1
- 192.168.1.1
- 255.255.255.255
- 127.0.0.1
- 203.0.113.5

The keys to the algorithm are to enable high parallelism for the CPU so it can perform multiple calculations at once.
In this implementation, we use the following 2 major techniques:

The first key is unlocked by the fact that although we’re not sure about where exactly each segment is, we still know their whereabouts.  

For example, in any correct IPv4 text, the first segment and its following dot must be in the first 4 characters. Be it a `1.` or a `192.` or a `127.`.  

So theoretically, if we fetch the first 4 bytes, we already have the first IPv4 segment, just that it’s neither validated nor as a number just yet.

The second key is unlocked by clever bit hacks.  

We won't dive into SWAR in this post, but the bottom line is that today's processors usually come in 64-bit architectures.  

This means they have general-purpose registers that are 64 bits wide.  

One implication of such wide registers is that it makes little difference to the CPU if you're for example adding 2 `UInt8` (unsigned 8-bit integer) together, or 2 `UInt64`s.  

So as an example, via SWAR techniques you can cram 8 `UInt8`s into one `UInt64` so next operations are performed only once on 1 `UInt64`, instead of 8 times on each of the `UInt8`s.  

SWAR typically adds some overhead to the operation to ensure that, as an example the values don't overflow into each other. However it often results in noticeable performance wins anyways.

We also know that a valid IPv4 text cannot be smaller than 7 characters.

With those in mind, we admit the following facts about a valid IPv4 text:

1. The 1st IP segment must be present in indices 0…2.
2. The 4th IP segment must be present in indices 0…2 when reading backwards, from the end.
3. The 2nd IP segment must be present in indices 2…6.
4. The 3rd IP segment must be present in indices 2…6 when reading backwards.

We'll implement the algorithm similar to the following code, exploiting the fact that numbers `0…9` correspond to ASCII codes `0x30` to `0x39`.

- For implementation detail reasons, we're also intentionally fetching some dots instead of only caring about the digits.
- We also XOR each window with a mask of 0x30 for each lane (here, a byte) which drops the 3 from numbers like 0x39.
  - This has the effect of making it obvious that 0x39 is a 0x09 == 9, which will help in the parsing process.
- loadUInt32(from:at:) loads 4 bytes of the from span into a 32-bit unsigned integer, starting from the index provided by at.
  - Loading multiple bytes at once is typically more performant than loading bytes one by one.

```
/// The amount of bytes that we've received to parse an IPv4 from.
let count = span.count
/// The shortest possible IPv4 address is "0.0.0.0" with 7 bytes.
guard count >= 7 else { return false }

/// `0x30` == ASCII `0`
let m30: UInt64 = 0x3030_3030_3030_3030
let m30_u32: UInt32 = 0x3030_3030

/// Read 1 window per segment, each also covering some dots around each segment.
///
/// XORing with `m30` turns the ASCII codes of `0`...`9` into the numbers `0x00`...`0x09`, and
/// the ASCII code of `.` (`0x2E`) into `0x1E`. So among digits and dots, only the dots have
/// their 5th bit (`0x10`) set. Invalid bytes are rejected later on.
///
/// Example for "192.168.1.98" (Notice little-endian byte-order):
/// `window1`: bytes 0...3 ("192.") -> `0x1E_02_09_01`.
/// `window2`: bytes 2...7 ("2.168.") -> `0x30_30_1E_08_06_01_1E_02` (in lanes 0...5).
/// `window3`: bytes 5...11 ("68.1.98") -> `0x08_09_1E_01_1E_08_06_30` (in lanes 1...7).
/// `window4`: bytes 8...11 ("1.98") -> `0x08_09_1E_01`.

/// Reads the "192." part.
/// We know `count >= 7` so this won't be an out-of-bounds read.
let w1 = loadUInt32(from: span, at: 0)
let window1 = w1 ^ m30_u32
/// Reads the "2.168." part.
/// With `count == 7` a read at byte 4 would go out of bounds, so it starts at byte 3.
/// "2." from `w1` | "168." << 16 == "2.168.".
let w2_p2 = loadUInt32(from: span, at: min(4, count &- 4))
let window2 = (UInt64(w1 >> 16) | (UInt64(w2_p2) << 16)) ^ m30
/// Similar to the `window1`, but read from the end.
/// Reads the "1.98" part.
let w4 = loadUInt32(from: span, at: count &- 4)
let window4 = w4 ^ m30_u32
/// Similar to the `window2`, but read from the end.
/// Reads the "68.1" part, and `w4` adds the "1.98" part, so `window3` is "68.1.98".
let w3_p1 = loadUInt32(from: span, at: count &- 7)
let window3 = (UInt64(w3_p1) << 8) | (UInt64(w4) << 32) ^ m30

/// ...

/// Reads 4 bytes at `offset` as a `UInt32` with the byte at `offset` in the lowest lane.
func loadUInt32(from span: Span<UInt8>, at offset: Int) -> UInt32 {
    unsafe span.bytes.unsafeLoadUnaligned(
        fromUncheckedByteOffset: offset,
        as: UInt32.self
    ).littleEndian
}
```

Now hold on a second. Allow me to not lose you. We will not dive too deep into the algorithm in this post.

However, I'll continue to explain the algorithm a little bit more as well as the optimizations that were made.

With the 4 windows above, what we'll need to do next is to find the position of the dots, strip the dots, and keep the digits.

However, in an IP address, there are only 3 dots (think: `1.1.1.1`).  

The matter of fact is, we don't need to parse 4 windows to find 3 dots. We only need 3 windows for that.  

So an optimization that was made was to ignore `window3` and parse the other 3 windows and find all the 3 dots, and later simply load a more-restricted `window3` from memory considering we know it's before the 3rd dot (and after the 2nd):

```
let count = span.count
let m30: UInt64 = 0x3030_3030_3030_3030
let m30_u32: UInt32 = 0x3030_3030

/// Example for "192.168.1.98" (Notice little-endian byte-order):
/// `window1`: bytes 0...3 ("192.") -> `0x1E_02_09_01`.
/// `window2`: bytes 2...7 ("2.168.") -> `0x30_30_1E_08_06_01_1E_02` (in lanes 0...5).
/// `window4`: bytes 8...11 ("1.98") -> `0x08_09_1E_01`.

let w1 = loadUInt32(from: span, at: 0)
let window1 = w1 ^ m30_u32
let w2_p2 = loadUInt32(from: span, at: min(4, count &- 4))
let window2 = (UInt64(w1 >> 16) | (UInt64(w2_p2) << 16)) ^ m30
let w4 = loadUInt32(from: span, at: count &- 4)
let window4 = w4 ^ m30_u32

/// ...

/// The 3rd and last segment is between the 2nd and 3rd dots, which are both found by now.
/// `thirdDotBitCount` is 4, 12 or 20, so this only reads within bytes `count - 7`...`count - 2`.
/// `thirdDotBitCount >> 3` == `thirdDotBitCount / 8`.
let w3_idx = count &- 7 &+ (thirdDotBitCount >> 3)
/// Example for "192.168.1.98": bytes 6...9 ("8.1.") -> `0x1E_01_1E_08`.
let w3 = loadUInt32(from: span, at: w3_idx)
let window3 = w3 ^ m30_u32

/// Later strip the remaining garbage from window3.
```

This helped the performance by a few cycles. However this was not the end.

After more trials and back and forth with my LLM of choice, I settled on the following selection of window-finding algorithm as it resulted in the most performant implementation:

```
let count = span.count
let m30: UInt64 = 0x3030_3030_3030_3030
let m30_u32: UInt32 = 0x3030_3030

/// Example for "192.168.1.98" (Notice little-endian byte-order):
/// `window1`: bytes 0...3 ("192.") -> `0x1E_02_09_01`.
/// `window12`: bytes 0...7 ("192.168.") -> `0x1E_08_06_01_1E_02_09_01`.
/// `window4`: bytes 8...11 ("1.98") -> `0x08_09_1E_01`.
let w1 = loadUInt32(from: span, at: 0)
let window1 = w1 ^ m30_u32
let w2 = loadUInt32(from: span, at: (count >> 1) & 4)
/// "192." | "168." << 32 == "192.168.".
let window12 = (UInt64(w1) | (UInt64(w2) << 32)) ^ m30
let w4 = loadUInt32(from: span, at: count &- 4)
let window4 = w4 ^ m30_u32

/// Parse the 3rd segment from window3 later.
```

This brought the whole implementation down to around 75 instructions and 15 cycles for a valid IPv4 text on an M6 processor.

For the curious reader, the [final implementation is available here](https://github.com/swift-dns/swift-endpoint/blob/c030b6588540d577fbf86de19d4930008bd654b3/Sources/IPAddress/IPv4Address/String+IPv4Address.swift#L285-L490) and it contains enough documentation comments to be able to hopefully decipher it.  

The implementation passes swift-endpoint's truly extensive test suite, as well as passing some fuzz-tests I've run on it.

## How So Fast?

Having 3 or 4 different windows that can be operated on simultaneously is of great importance to performance of the algorithm.  

Modern processors have CPU cores where each core contains multiple Arithmetic Logic Units (ALUs). This means they can execute multiple arithmetic operations in a single cycle when given the opportunity. You can see where this is going.

By having multiple different windows and having little sequential dependency between them, we enable our CPU cores to perform multiple calculations in each clock cycle, in what is called "Instruction-level parallelism". This is crucial to achieving maximum performance.  

As mentioned, on my M6 processor this algorithm’s throughput is 75 instructions per 15 cycles for a single IP address. That's an average of 5 instructions in each cycle. A small part of that comes from the CPU executing multiple iterations of the benchmark loop simultaneously.

As discussed in the previous section, SWAR techniques also help a ton in lowering the number of instructions required to parse an IPv4.  

This is thanks to the fact that each digit in an IP segment's text is only 1 ASCII byte, but we know we can handle up to 8 ASCII bytes at once on a 64-bit processor.

## Benchmark Results

- The shapes columns refer to running the benchmarks against 4 million random valid IP addresses.
  - 4 million is big enough that branch predictors of neither M6 nor AMD processors can keep up with, which would skew the results.
- The real32 columns refer to running the benchmarks against a pre-determined set of 32 popular IPs.
  - To confuse branch predictors the order is randomly driven using George Marsaglia's xorshift algorithms via a constant seed. Specifically 13/7/17 variant of xorshift64 as defined on the Wikipedia page.
  - The RNG overhead is low and has not been deducted from the numbers.
- While the performance can differ with different corpora of IPv4s, the top 5 rankings are not affected.

```text
127.0.0.1
1.1.1.1
8.8.8.8
9.9.9.9
255.255.255.255
192.168.1.1
10.0.0.1
172.16.0.1
100.64.0.1
208.67.222.222
185.199.108.153
151.101.1.140
104.16.132.229
142.250.185.78
13.107.42.14
23.185.0.2
0.0.0.0
224.0.0.1
169.254.169.254
8.8.4.4
1.0.0.1
149.112.112.112
208.67.220.220
172.217.16.142
140.82.121.4
198.41.0.4
192.33.4.12
193.0.14.129
199.7.83.42
93.184.215.14
20.190.160.14
34.107.221.82
```

Here are the specifications of the benchmarking environments:

| Hardware, OS | Toolchains |
| --- | --- |
| Apple M6, macOS 27 | Swift 6.4, Apple clang 21.0.0, libc++ 22.1.6, Rust 1.98.1, Go 1.27.2 |
| AMD Zen 5, Ubuntu 24.04 | Swift 6.4, clang 21.0.0, glibc 2.39, libstdc++ 13.3; Rust 1.98.1, Zig 0.17.0, Go 1.27.2 |

### Apple M6

The implementations that use SSE were run using [sse2neon](https://github.com/DLTcollab/sse2neon). They are indicated in the table via `→ NEON`.

Ratios are compared to swift-endpoint.

| # | Implementation | shapes | ratio | # real32 | real32 | ratio |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | [simdzone sse_inet_aton](https://github.com/NLnetLabs/simdzone/blob/7f62ebcc77a67ad399f6eeb05865c33d1de65cc2/src/westmere/ip4.h#L118-L180) → NEON | 2.84 ns | 0.84x | 1 | 3.61 ns | 0.78x |
| **2** | **[swift-endpoint](https://github.com/swift-dns/swift-endpoint/blob/c030b6588540d577fbf86de19d4930008bd654b3/Sources/IPAddress/IPv4Address/String+IPv4Address.swift#L285-L490)** | **3.36 ns** | **1.00x** | **2** | **4.62 ns** | **1.00x** |
| 3 | [Muła v7](https://github.com/WojciechMula/toys/blob/15ba0102e17aece7a0e948a7f74171d293cd9d25/parseip4/sse_v7.cpp.inl) → NEON | 5.00 ns | 1.49x | 3 | 6.16 ns | 1.33x |
| 4 | [Muła v5](https://github.com/WojciechMula/toys/blob/15ba0102e17aece7a0e948a7f74171d293cd9d25/parseip4/sse_v5.cpp.inl) → NEON | 5.47 ns | 1.63x | 4 | 6.88 ns | 1.49x |
| 5 | [simdzone generic](https://github.com/NLnetLabs/simdzone/blob/7f62ebcc77a67ad399f6eeb05865c33d1de65cc2/src/generic/ip4.h#L12-L44) (arm64 path) | 6.24 ns | 1.86x | 5 | 7.99 ns | 1.73x |
| 6 | [Muła v6](https://github.com/WojciechMula/toys/blob/15ba0102e17aece7a0e948a7f74171d293cd9d25/parseip4/sse_v6.cpp.inl) → NEON | 6.45 ns | 1.92x | 6 | 8.09 ns | 1.75x |
| 7 | [Muła v8](https://github.com/WojciechMula/toys/blob/15ba0102e17aece7a0e948a7f74171d293cd9d25/parseip4/sse_v8.cpp.inl) → NEON | 7.18 ns | 2.13x | 7 | 8.94 ns | 1.94x |
| 8 | [fast_float v8.3.2](https://github.com/fastfloat/fast_float/blob/v8.3.2/include/fast_float/ascii_number.h#L634-L765) ([Lemire 2025](https://github.com/lemire/Code-used-on-Daniel-Lemire-s-blog/blob/b50dc28111726ad342e9c20dbe5f9a0fef48c161/2025/12/27/benchmark_ip_parsing/benchmarks/benchmark.cpp#L134-L162)) | 13.09 ns | 3.89x | 17 | 15.04 ns | 3.26x |
| 9 | [Muła v4](https://github.com/WojciechMula/toys/blob/15ba0102e17aece7a0e948a7f74171d293cd9d25/parseip4/sse_v4.cpp.inl) → NEON | 14.28 ns | 4.24x | 8 | 11.40 ns | 2.47x |
| 10 | [Muła v3](https://github.com/WojciechMula/toys/blob/15ba0102e17aece7a0e948a7f74171d293cd9d25/parseip4/sse_v3.cpp.inl) → NEON | 14.78 ns | 4.39x | 9 | 12.12 ns | 2.62x |
| 11 | [Lemire manual](https://github.com/lemire/Code-used-on-Daniel-Lemire-s-blog/blob/b50dc28111726ad342e9c20dbe5f9a0fef48c161/2025/12/27/benchmark_ip_parsing/benchmarks/benchmark.cpp#L98-L130) (unrolled) | 15.60 ns | 4.64x | 12 | 12.91 ns | 2.79x |
| 12 | [ada try_parse_ipv4_fast](https://github.com/ada-url/ada/blob/473c293ee19accd1f1223d669d3285b9131408ef/include/ada/checkers-inl.h#L234-L248) (scalar path) | 15.64 ns | 4.65x | 10 | 12.85 ns | 2.78x |
| 13 | [ada scalar](https://github.com/ada-url/ada/blob/473c293ee19accd1f1223d669d3285b9131408ef/include/ada/checkers-inl.h#L75-L125) | 15.68 ns | 4.66x | 11 | 12.87 ns | 2.79x |
| 14 | [Muła v2](https://github.com/WojciechMula/toys/blob/15ba0102e17aece7a0e948a7f74171d293cd9d25/parseip4/sse_v2.cpp.inl) → NEON | 16.96 ns | 5.04x | 19 | 18.75 ns | 4.06x |
| 15 | [Rust std](https://github.com/rust-lang/rust/blob/1.98.1/library/core/src/net/parser.rs#L152-L166) ([entry](https://github.com/rust-lang/rust/blob/1.98.1/library/core/src/net/parser.rs#L314-L343)) | 17.08 ns | 5.08x | 13 | 13.87 ns | 3.00x |
| 16 | [Muła SWAR](https://github.com/WojciechMula/toys/blob/15ba0102e17aece7a0e948a7f74171d293cd9d25/parseip4/swar.cpp#L14-L274) | 17.85 ns | 5.31x | 14 | 13.94 ns | 3.02x |
| 17 | [Lemire manual](https://github.com/lemire/Code-used-on-Daniel-Lemire-s-blog/blob/b50dc28111726ad342e9c20dbe5f9a0fef48c161/2025/12/27/benchmark_ip_parsing/benchmarks/benchmark.cpp#L69-L96) | 18.10 ns | 5.38x | 15 | 14.55 ns | 3.15x |
| 18 | [Muła naive](https://github.com/WojciechMula/toys/blob/15ba0102e17aece7a0e948a7f74171d293cd9d25/parseip4/naive.cpp#L3-L122) | 18.34 ns | 5.45x | 16 | 14.94 ns | 3.23x |
| 19 | [Muła v1](https://github.com/WojciechMula/toys/blob/15ba0102e17aece7a0e948a7f74171d293cd9d25/parseip4/sse.cpp#L5-L122) → NEON | 18.87 ns | 5.61x | 18 | 16.17 ns | 3.50x |
| 20 | [Go net/netip](https://github.com/golang/go/blob/go1.27.2/src/net/netip/netip.go#L114-L202) | 22.82 ns | 6.78x | 20 | 19.45 ns | 4.21x |
| 21 | [std::from_chars](https://github.com/llvm/llvm-project/blob/llvmorg-22.1.6/libcxx/include/__charconv/from_chars_integral.h#L97-L147) ([loop](https://github.com/lemire/Code-used-on-Daniel-Lemire-s-blog/blob/b50dc28111726ad342e9c20dbe5f9a0fef48c161/2025/12/27/benchmark_ip_parsing/benchmarks/benchmark.cpp#L134-L162)) | 25.61 ns | 7.61x | 21 | 19.46 ns | 4.21x |
| 22 | [Apple inet_pton](https://github.com/apple-oss-distributions/Libc/blob/Libc-1752.120.2/net/inet_pton.c#L64-L170) | 33.99 ns | 10.10x | 22 | 27.29 ns | 5.91x |

### AMD Zen 5

Ratios are compared to swift-endpoint.

| # | Implementation | shapes | ratio | # real32 | real32 | ratio |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | [simdzone sse_inet_aton](https://github.com/NLnetLabs/simdzone/blob/7f62ebcc77a67ad399f6eeb05865c33d1de65cc2/src/westmere/ip4.h#L118-L180) | 3.74 ns | 0.61x | 1 | 4.70 ns | 0.54x |
| 2 | [Cesarano BMI2](https://github.com/GiuseppeCesarano/extractingcycles/blob/613bcea67f8ae568ddc6b1690a9b6e4f9a969fc7/content/blog/the-ipv4-parser-ai-couldnt-have-written/bmiParseIPV4.zig#L4-L193) (Zig) | 5.69 ns | 0.93x | 2 | 8.01 ns | 0.91x |
| **3** | **[swift-endpoint](https://github.com/swift-dns/swift-endpoint/blob/c030b6588540d577fbf86de19d4930008bd654b3/Sources/IPAddress/IPv4Address/String+IPv4Address.swift#L285-L490)** | **6.12 ns** | **1.00x** | **3** | **8.77 ns** | **1.00x** |
| 4 | [Muła v7](https://github.com/WojciechMula/toys/blob/15ba0102e17aece7a0e948a7f74171d293cd9d25/parseip4/sse_v7.cpp.inl) (SSE) | 6.60 ns | 1.08x | 4 | 9.01 ns | 1.03x |
| 5 | [Muła v5](https://github.com/WojciechMula/toys/blob/15ba0102e17aece7a0e948a7f74171d293cd9d25/parseip4/sse_v5.cpp.inl) (SSE) | 7.33 ns | 1.20x | 5 | 10.05 ns | 1.15x |
| 6 | [Muła v6](https://github.com/WojciechMula/toys/blob/15ba0102e17aece7a0e948a7f74171d293cd9d25/parseip4/sse_v6.cpp.inl) (SSE) | 8.45 ns | 1.38x | 6 | 11.67 ns | 1.33x |
| 7 | [Muła v8](https://github.com/WojciechMula/toys/blob/15ba0102e17aece7a0e948a7f74171d293cd9d25/parseip4/sse_v8.cpp.inl) (SSE) | 9.39 ns | 1.53x | 7 | 12.95 ns | 1.48x |
| 8 | [fast_float v8.3.2](https://github.com/fastfloat/fast_float/blob/v8.3.2/include/fast_float/ascii_number.h#L634-L765) ([Lemire 2025](https://github.com/lemire/Code-used-on-Daniel-Lemire-s-blog/blob/b50dc28111726ad342e9c20dbe5f9a0fef48c161/2025/12/27/benchmark_ip_parsing/benchmarks/benchmark.cpp#L134-L162)) | 21.51 ns | 3.51x | 18 | 26.08 ns | 2.97x |
| 9 | [Muła v2](https://github.com/WojciechMula/toys/blob/15ba0102e17aece7a0e948a7f74171d293cd9d25/parseip4/sse_v2.cpp.inl) (SSE) | 22.69 ns | 3.71x | 17 | 25.91 ns | 2.95x |
| 10 | [Muła v4](https://github.com/WojciechMula/toys/blob/15ba0102e17aece7a0e948a7f74171d293cd9d25/parseip4/sse_v4.cpp.inl) (SSE) | 23.26 ns | 3.80x | 8 | 19.82 ns | 2.26x |
| 11 | [Muła v3](https://github.com/WojciechMula/toys/blob/15ba0102e17aece7a0e948a7f74171d293cd9d25/parseip4/sse_v3.cpp.inl) (SSE) | 24.93 ns | 4.07x | 9 | 21.43 ns | 2.44x |
| 12 | [Lemire manual](https://github.com/lemire/Code-used-on-Daniel-Lemire-s-blog/blob/b50dc28111726ad342e9c20dbe5f9a0fef48c161/2025/12/27/benchmark_ip_parsing/benchmarks/benchmark.cpp#L98-L130) (unrolled) | 28.57 ns | 4.67x | 10 | 22.06 ns | 2.52x |
| 13 | [ada scalar](https://github.com/ada-url/ada/blob/473c293ee19accd1f1223d669d3285b9131408ef/include/ada/checkers-inl.h#L75-L125) | 28.79 ns | 4.70x | 11 | 22.36 ns | 2.55x |
| 14 | [ada try_parse_ipv4_fast](https://github.com/ada-url/ada/blob/473c293ee19accd1f1223d669d3285b9131408ef/include/ada/checkers-inl.h#L234-L248) (scalar path) | 29.11 ns | 4.75x | 12 | 22.46 ns | 2.56x |
| 15 | [Rust std](https://github.com/rust-lang/rust/blob/1.98.1/library/core/src/net/parser.rs#L152-L166) ([entry](https://github.com/rust-lang/rust/blob/1.98.1/library/core/src/net/parser.rs#L314-L343)) | 29.33 ns | 4.79x | 14 | 24.61 ns | 2.81x |
| 16 | [simdzone generic](https://github.com/NLnetLabs/simdzone/blob/7f62ebcc77a67ad399f6eeb05865c33d1de65cc2/src/generic/ip4.h#L12-L44) | 30.82 ns | 5.03x | 15 | 24.67 ns | 2.81x |
| 17 | [Lemire manual](https://github.com/lemire/Code-used-on-Daniel-Lemire-s-blog/blob/b50dc28111726ad342e9c20dbe5f9a0fef48c161/2025/12/27/benchmark_ip_parsing/benchmarks/benchmark.cpp#L69-L96) | 31.27 ns | 5.11x | 13 | 24.14 ns | 2.75x |
| 18 | [Muła SWAR](https://github.com/WojciechMula/toys/blob/15ba0102e17aece7a0e948a7f74171d293cd9d25/parseip4/swar.cpp#L14-L274) | 31.32 ns | 5.11x | 20 | 26.39 ns | 3.01x |
| 19 | [Muła naive](https://github.com/WojciechMula/toys/blob/15ba0102e17aece7a0e948a7f74171d293cd9d25/parseip4/naive.cpp#L3-L122) | 32.12 ns | 5.25x | 16 | 24.83 ns | 2.83x |
| 20 | [std::from_chars](https://github.com/gcc-mirror/gcc/blob/releases/gcc-13.3.0/libstdc++-v3/include/std/charconv#L523-L632) ([loop](https://github.com/lemire/Code-used-on-Daniel-Lemire-s-blog/blob/b50dc28111726ad342e9c20dbe5f9a0fef48c161/2025/12/27/benchmark_ip_parsing/benchmarks/benchmark.cpp#L134-L162)) | 32.23 ns | 5.26x | 19 | 26.12 ns | 2.98x |
| 21 | [glibc 2.39 inet_pton](https://github.com/bminor/glibc/blob/glibc-2.39/resolv/inet_pton.c#L48-L122) | 35.25 ns | 5.76x | 21 | 27.04 ns | 3.08x |
| 22 | [Muła v1](https://github.com/WojciechMula/toys/blob/15ba0102e17aece7a0e948a7f74171d293cd9d25/parseip4/sse.cpp#L5-L122) (SSE) | 35.84 ns | 5.85x | 22 | 29.78 ns | 3.40x |
| 23 | [Go net/netip](https://github.com/golang/go/blob/go1.27.2/src/net/netip/netip.go#L114-L202) | 39.19 ns | 6.40x | 23 | 32.44 ns | 3.70x |

### Conclusions

- Daniel Lemire's sse_inet_aton implementation is very fast. But keep in mind it makes significant use of lookup tables and requires wide inputs by contract.
- swift-endpoint's parser ranks 2nd on M6, and 3rd on AMD Zen 5.

## That's It?

This is the first post on my blog. I do realize there are some shortcomings.  

Please let me know if you've noticed any ways to improve the blog, be it technical or non-technical.

Currently I plan to take a shot at the following:

- Publish a clean version of the source code of the benchmarks. Likely starting from some future post.
- Run the x86_64 benchmarks on more modern processors.
  - The benchmarking machines are not free so I'll have to find a cost-effective way to achieve that.
- Provide easy "one-click" ways to run the benchmarks on your own AWS account on an ephemeral EC2 instance.
- Make more improvements to the blog's UX without making it too complicated or unnecessarily shiny.
  - Likely open-source the blog as well, including the infrastructure-related code.
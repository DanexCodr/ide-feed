Probabilistic data structures give you approximate answers to questions about the data they handle. Does the set contain a certain item? How many unique items are in the collection? What is the 99th percentile in a stream of numbers? How similar are two sets? Unlike deterministic structures, the answers might not be exact, but in return, you can save a lot of memory.

Previously, we reviewed the following [data structures](https://antonz.org/probabilistic-data-structures): Bloom filter (for checking if an item is in a set), Count-min sketch (for counting items), HyperLogLog (for counting unique items), T-digest (for finding quantiles), and Top-k (for finding the most frequent items).

In this post, we'll talk about other probabilistic structures and compare them to the ones we've already covered. We'll look at how they work and what kinds of guarantees they provide.

All examples use [unsure](https://github.com/nalgeon/unsure) — a package that implements these structures in Go.

[Binary fuse filter](https://antonz.org/probabilistic-data-structures-2/#binary-fuse-filter) •
[UltraLogLog](https://antonz.org/probabilistic-data-structures-2/#ultraloglog) •
[Log-linear histogram](https://antonz.org/probabilistic-data-structures-2/#log-linear-histogram) •
[MinHash](https://antonz.org/probabilistic-data-structures-2/#minhash)

## Binary fuse filter

A binary fuse filter is a set that trades certainty for space, like a Bloom filter<sup>[1](https://antonz.org/probabilistic-data-structures-2/#fn:1)</sup>. It can tell you that an item is *definitely not* in the set, or that it *probably is* (which might be a false positive). The filter doesn't store the items, so it's much more compact than a regular set.

Unlike a Bloom filter, a binary fuse filter is static: you build it once from all the items, and you can't add more later. In exchange, it uses less memory than a Bloom filter with the same false positive rate. For example, a fuse filter for 1,000,000 items with a 0.39% false positive rate takes 1.13 MB (9 bits per item), while a Bloom filter takes 1.51 MB (12 bits per item).

This makes binary fuse filters a good fit for data that is written once and read many times, like the key set of an immutable file in a database (to skip files that don't have the key), or a list of known bad items, such as leaked passwords or malicious URLs.

```go
items := [][]byte{[]byte("alice"), []byte("bob")}

// An 8-bit filter: 0.39% false positive rate.
filter := fuse.New[uint8](slices.Values(items), len(items))

filter.Contains([]byte("alice")) // true
filter.Contains([]byte("carol")) // false (or, rarely, true)
```

The fingerprint type (`T` in `New[T]`) determines the false positive rate and the memory use:

| Type | False positive rate | Bits per item |
| --- | --- | --- |
| `uint8` | 0.39% | 9 |
| `uint16` | 0.0015% | 18 |
| `uint32` | 2.3e-10 | 36 |

The constructor takes an iterator of items to add to the filter and the expected number of items (0 if unknown). The number is only used to preallocate memory, so a good estimate makes the build faster.

You can check if an item is in the filter, but you cannot add or delete an item, count the number of items, or iterate over them.

### How it works

The filter<sup>[2](https://antonz.org/probabilistic-data-structures-2/#fn:2)</sup> is an array of *b*-bit fingerprints (for example, b = 8 for `uint8`). Each item is hashed to a 64-bit value *h*, which gives the item's fingerprint *f* (b bits computed from h) and three positions in the array (cells). The array is filled so that for every item, the XOR of its cells equals f.

```text
        ┌──────┐               ┌──► f  (b bits)
item ──►│ hash │──► h ─────────┤
        └──────┘               └──► i0, i1, i2

           i0          i1          i2
┌───┬───┬──▼──┬───┬───┬──▼──┬───┬──▼──┬───┐
│   │   │ F0  │   │   │ F1  │   │ F2  │   │   F0 ^ F1 ^ F2 == f
└───┴───┴─────┴───┴───┴─────┴───┴─────┴───┘
```

To check an item, you compute h, look up its three cells, and compare their XOR with f. For an item in the set, they always match. For any other item, the XOR is a random b-bit value, which matches f with probability 2^-b.

Each check reads three cells, so for large filters it's three cache misses, against one for a blocked Bloom filter. However, since the reads are independent, the CPU can do them concurrently, so the checks are about as fast as with a Bloom filter.

The filter uses the local *wyhash*<sup>[3](https://antonz.org/probabilistic-data-structures-2/#fn:3)</sup> implementation for hashing. It performs roughly the same as *xxh3*<sup>[4](https://antonz.org/probabilistic-data-structures-2/#fn:4)</sup> but has a much simpler implementation, without SIMD or assembly.

### Benchmarks

Here's an excerpt from the full benchmarks<sup>[5](https://antonz.org/probabilistic-data-structures-2/#fn:5)</sup>, comparing *unsure* to *xorfilter*<sup>[6](https://antonz.org/probabilistic-data-structures-2/#fn:6)</sup> (binary fuse by the authors of the paper) and *bloom* (*unsure*'s own Bloom filter) with 8-bit fingerprints (ns/op, lower is better):

| Operation | Items | unsure | xorfilter | bloom |
| --- | --- | --- | --- | --- |
| Build (per item) | 10K | 23 | 25 | **13** |
|  | 1M | 30 | 31 | **12** |
| Contains | 10K | **6.2** | 8.0 | 9.3 |
|  | 1M | **7.0** | 9.3 | 10.2 |
|  | 50M | 39 | 42 | 40 |

Memory, bits per item (lower is better):

| Items | Fingerprint | unsure | xorfilter | bloom |
| --- | --- | --- | --- | --- |
| 100K | 8-bit | **9.50** | **9.50** | 12.45 |
| 10M | 8-bit | **9.02** | **9.02** | 12.10 |
| 10M | 16-bit | **18.04** | **18.04** | 27.99 |

*Unsure* is the same size as *xorfilter* (same layout) with up to 25% faster checks. Compared to the Bloom filter, it uses up to 36% less memory, with checks as fast or faster, but up to 2.5× slower builds.

1. [Bloom filter overview](https://antonz.org/probabilistic-data-structures#bloom-filter) and how it works. [↩︎](https://antonz.org/probabilistic-data-structures-2/#fnref:1)
2. [Binary Fuse Filters paper](https://doi.org/10.1145/3510449) by Thomas Mueller Graf and Daniel Lemire, 2022. [↩︎](https://antonz.org/probabilistic-data-structures-2/#fnref:2)
3. [Reference wyhash implementation](https://github.com/wangyi-fudan/wyhash) by Wang Yi. [↩︎](https://antonz.org/probabilistic-data-structures-2/#fnref:3)
4. [Reference xxHash implementation](https://github.com/Cyan4973/xxHash) by Yann Collet. [↩︎](https://antonz.org/probabilistic-data-structures-2/#fnref:4)
5. [Binary fuse filter benchmarks](https://github.com/nalgeon/unsure/tree/main/fuse#benchmarks). [↩︎](https://antonz.org/probabilistic-data-structures-2/#fnref:5)
6. [FastFilter/xorfilter](https://github.com/FastFilter/xorfilter) by Daniel Lemire. [↩︎](https://antonz.org/probabilistic-data-structures-2/#fnref:6)

## UltraLogLog

UltraLogLog is a unique items counter that trades accuracy for space, like HyperLogLog<sup>[7](https://antonz.org/probabilistic-data-structures-2/#fn:7)</sup>. It tells you approximately how many *distinct items* it has seen, no matter how many times each one appeared. UltraLogLog doesn't store the items, so it's much more compact than a regular set.

UltraLogLog is a newer design (Otmar Ertl, 2024) that uses the space more efficiently: for the same error, it needs about 43% less memory than HyperLogLog. For example, a HyperLogLog sketch with 0.81% standard error takes 16 KB, while an UltraLogLog sketch with 0.86% error takes 8 KB. However, adding, counting, and merging are slower than with HyperLogLog.

UltraLogLog is useful in the same places as HyperLogLog: counting unique visitors, unique search queries, or distinct values in a database column, possibly across many machines or segments.

```go
// Standard error about 0.9% of the true count.
sketch := ull.New()

sketch.Add([]byte("alice"))
sketch.Add([]byte("bob"))
sketch.Add([]byte("alice"))
sketch.Add([]byte("carol"))

sketch.Count() // 3 (approximately)
```

You can merge sketches to get the total number of unique items from all of them, without counting shared items twice.

```go
home := ull.New() // visitors to the home page
docs := ull.New() // visitors to the docs
// ...
home.Merge(docs)
home.Count() // visitors to either page
```

The sketch has one setting: the precision *p*, which gives a relative standard error of 0.782/√(2^p). The default is p=13 with 0.86% error in 8 KB, close to the common HyperLogLog default (0.81% in 16 KB).

You can add items to a sketch, get the estimated count, and merge sketches. You cannot check if a specific item was added, remove items, or list them.

### How it works

**HyperLogLog** hashes each item and uses the first *p* bits of the hash to pick one of m = 2^p *registers*. It calculates the *rank* (the number of leading zeros in the rest of the hash, plus one) and keeps the highest rank it has seen in the register. Seeing a rank of *k* suggests there were about 2^k items in the register. The count is estimated from all the registers together.

```text
                      p bits
        ┌──────┐   ┌──────────┬────────────────────────┐
item ──►│ hash │──►│ 01101001 │ 0001101...             │
        └──────┘   └────┬─────┴───────────┬────────────┘
                        │ register i      └ rank = 3 zeros + 1 = 4
          ┌───┬───┬───┬─▼─┬───┬───┬───┬───┬───┬───┐
registers │ 3 │ 0 │ 5 │ 2 │ 1 │ 0 │ 4 │ 2 │ 0 │ 1 │  2 → 4
          └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
```

A HyperLogLog register loses some information: it only keeps track of the highest value, not whether any slightly lower values were seen. These lower values show up at least as often as the highest one, so they can tell a lot about the count.

**UltraLogLog**<sup>[8](https://antonz.org/probabilistic-data-structures-2/#fn:8)</sup> uses the registers more efficiently. Each register is still one byte, but it stores the highest rank *k* in the upper 6 bits, and whether *k−1* and *k−2* were seen in the lower 2 bits:

```text
              k = 5        k-1 k-2
          ┌───────────────┬───┬───┐
register  │ 0 0 0 1 0 1   │ 1 │ 0 │  saw 5 and 4, but not 3
          └───────────────┴───┴───┘
          ┌───────────────┬───┬───┐
add k=6:  │ 0 0 0 1 1 0   │ 1 │ 1 │  saw 6, 5, 4
          └───────────────┴───┴───┘
```

The count estimate uses the FGRA estimator from the UltraLogLog paper. Each register adds a weight based on its value, and the count is calculated as a power of the sum of the weights. Nearly empty and nearly full sketches get special handling, so the estimate stays accurate from zero to billions of items, without bias tables or a separate formula for small counts.

**Unsure** keeps a histogram of register values (256 four-byte counters, 1 KB) updated as the registers change. This way, `Count` reads the histogram instead of scanning all the registers. `Merge` checks 8 registers at a time using a few bitwise operations to find which ones the other sketch would change, and only updates those.

The item is hashed once with *wyhash*, and the 64-bit hash is split into the register index and the rank.

### Benchmarks

Here's an excerpt from the full benchmarks<sup>[9](https://antonz.org/probabilistic-data-structures-2/#fn:9)</sup>, comparing UltraLogLog to *unsure*'s own HyperLogLog and *axiom*<sup>[10](https://antonz.org/probabilistic-data-structures-2/#fn:10)</sup> (HyperLogLog with LogLog-Beta estimator and sparse mode) (ns/op, lower is better):

| Operation | p | Size | ull | hll | axiom |
| --- | --- | --- | --- | --- | --- |
| Add | 10 | 1 KB | 8.1 | **5.5** | 7.6 |
|  | 14 | 16 KB | 8.0 | **5.7** | 7.7 |
|  | 18 | 256 KB | 9.4 | 8.3 | **8.0** |
| Count | 10 | 1 KB | 165 | **68** | 17,700 |
|  | 14 | 16 KB | 161 | **63** | 348,000 |
|  | 18 | 256 KB | 173 | **57** | 4,650,000 |
| Merge | 10 | 1 KB | 2,900 | **720** | 1,740 |
|  | 14 | 16 KB | 51,200 | **20,200** | 58,500 |
|  | 18 | 256 KB | 818,000 | **341,000** | 955,000 |

Accuracy and memory, relative RMSE over 1,000 sketches (lower is better):

| Distinct items | ull p=13 | hll p=14 | axiom p=14 |
| --- | --- | --- | --- |
| 1,000 | 0.66% | 0.54% | **0.01%** |
| 40,000 | 0.73% | **0.68%** | 0.69% |
| 1,000,000 | 0.86% | **0.79%** | 0.82% |
| Memory | **9.1 KB** | 16.3 KB | 16.1 KB |

UltraLogLog provides the same accuracy as HyperLogLog with almost half the memory. However, adding, counting, and merging are noticeably slower.

1. [HyperLogLog overview](https://antonz.org/probabilistic-data-structures#hyperloglog) and how it works. [↩︎](https://antonz.org/probabilistic-data-structures-2/#fnref:7)
2. [UltraLogLog paper](https://arxiv.org/abs/2308.16862) by Otmar Ertl, 2024. [↩︎](https://antonz.org/probabilistic-data-structures-2/#fnref:8)
3. [UltraLogLog benchmarks](https://github.com/nalgeon/unsure/tree/main/ull#benchmarks). [↩︎](https://antonz.org/probabilistic-data-structures-2/#fnref:9)
4. [axiomhq/hyperloglog](https://github.com/axiomhq/hyperloglog) by Axiom. [↩︎](https://antonz.org/probabilistic-data-structures-2/#fnref:10)

## Log-linear histogram

A log-linear histogram is a summary of a stream of numbers that trades accuracy for space. It can give you an approximate median, 99th percentile, or any other *quantile* of the data. It can also estimate what fraction of the numbers are below a certain value (the CDF). The histogram doesn't store the numbers, so it's much more compact than a sorted list.

For example, to find the exact 99th percentile of 1,000,000 response times, you'd have to keep all of them. With 64-bit floats, that takes 8 MB. A log-linear histogram estimates the same percentile within 0.39% of its true value using about 14 KB — almost 600 times less.

The error is relative to the value: if the true 99th percentile is 200 ms, the histogram returns a value between 199.2 and 200.8 ms. This guarantee applies to every quantile, from the median to the most extreme outliers. The size of the histogram doesn't depend on the number of values, only on the accuracy you choose and on how wide the range of the values is.

A log-linear histogram is useful when you need percentiles for positive values that cover a wide range, like latencies, file sizes, or prices.

```go
// Response times in milliseconds.
hist := loghist.New()

hist.Add(12.5)
hist.Add(8.1)
hist.Add(130.0)
// ...

hist.Quantile(0.5)  // median
hist.Quantile(0.99) // 99th percentile
hist.CDF(100)       // fraction of responses faster than 100 ms
```

You can merge histograms to gather data from multiple machines or segments (like by hour, endpoint, or region). Merging is exact: a merged histogram is the same as if it had received all the values directly.

```go
east := loghist.New() // latencies on one server
west := loghist.New() // latencies on another
// ...
east.Merge(west)
east.Quantile(0.99) // 99th percentile across both servers
```

The histogram has two settings: relative error and value range. By default, the error is 0.0039 (0.39%) and the range is from 1e-9 to 1e18. Lowering the error or increasing the range uses more memory.

You can add numbers to a histogram, estimate quantiles and the CDF, and merge histograms. You cannot remove numbers or list them.

### How it works

A **histogram** splits the range of values into *buckets* and counts how many values are in each one. To estimate a quantile, it adds up the counts starting from the lowest bucket until it reaches the requested rank, then returns a value from that bucket. The accuracy of the estimate depends on how wide the bucket is.

With buckets that have equal widths, like 0–10, 10–20, and so on, every estimate has the same absolute error of ±5 around the bucket's midpoint. So the relative error is very large for small values and unnecessarily small for large values:

```text
0       10      20      30     970     980     990     1000
├───────┼───────┼───────┼─ ··· ─┼───────┼───────┼───────┤
    └ 5 ± 5: ±100%                   995 ± 5: ±0.5% ┘
```

A **logarithmic histogram** solves this by making each bucket's width proportional to its value. For example, if the bucket boundaries are powers of 1.02 (1, 1.02, 1.0404, ...), the end of each bucket is 2% larger than its start, so any value in the bucket is within about 1% of the bucket's midpoint. *DDSketch*<sup>[11](https://antonz.org/probabilistic-data-structures-2/#fn:11)</sup> uses this method. The downside is that finding the right bucket for a value means you have to calculate a logarithm, which is relatively slow.

A **log-linear histogram** gets almost the same result with cheaper math. First, it splits the values into ranges between powers of two: 1–2, 2–4, 4–8, and so on (these are called *octaves*). Then it splits every octave into the same number of equal-width buckets. For example, here are three octaves with 4 buckets each:

```text
1       2               4                               8
├─┬─┬─┬─┼───┬───┬───┬───┼───────┬───────┬───────┬───────┤
4 buckets   4 buckets               4 buckets
```

Each octave is twice as long as the previous one, so its buckets are twice as wide, and the bucket width grows with the values, as in a logarithmic histogram. Finding the right bucket only takes a few bit operations instead of calculating a logarithm.

*HdrHistogram*<sup>[12](https://antonz.org/probabilistic-data-structures-2/#fn:12)</sup> is the best-known log-linear histogram. It records integers: the position of the highest 1 bit of a number determines its octave, and the next few bits determine the bucket within the octave.

**Unsure** works with float64 numbers and finds the bucket in a similar way to HdrHistogram.

**IEEE 754 double-precision format**

A float64 in Go (and most other languages) is made up of three parts:

- a sign bit,
- an 11-bit exponent e (stored as 1023 + e to avoid negative values),
- and a 52-bit mantissa f.

The number's value is 1.f × 2^e, where 1.f is a binary fraction between 1 and 2.

The exponent determines the octave, from 2^e to 2^(e+1). The top *m* bits of the mantissa determine one of the 2^m equal buckets within the octave.

For example, here's the number 5.25 with m=3 (8 buckets per octave). In binary, 5.25 = 1.0101₂ × 2², so the exponent is 2 (stored as 1025), and the mantissa starts with 0101:

```text
5.25 = 1.0101₂ × 2²

sign   exponent     top m   rest of the mantissa
┌───┬─────────────┬─────┬─────────────────────────┐
│ 0 │ 10000000001 │ 010 │ 1000000000 ... 00000000 │
└───┴──────┬──────┴──┬──┴──┬──────────────────────┘
           │         │     └── ignored
           │         └── bucket 2 of 8
           └── 1025 = 2 + 1023: octave [4, 8)

4                               8
├───┬───┬───┬───┬───┬───┬───┬───┤
  0   1   2   3   4   5   6   7
          └ 5.25 lands in bucket 2: [5, 5.5)
```

`Add` finds the bucket for the given number and increases the count. `Merge` adds the counts bucket by bucket. `Quantile` adds up the counts from the closer end (the leftmost bucket for q ≤ 0.5, the rightmost bucket otherwise) until it reaches the rank.

The number of mantissa bits m comes from the requested error: the constructor picks the smallest m for which the maximum error doesn't exceed the requested one. The default is m=7: 128 buckets per octave and an error of 0.39%.

### Log-linear histogram vs. t-digest

A t-digest<sup>[13](https://antonz.org/probabilistic-data-structures-2/#fn:13)</sup> also estimates quantiles, but it limits the error in *ranks*: `Quantile(0.99)` returns a value whose rank is close to 99%. A log-linear histogram limits the error in *values*: `Quantile(0.99)` returns a value close to the true 99th percentile.

In the middle of the data, the two are pretty similar. But in a long tail, values at nearby ranks can be very different, so even a small error in rank can lead to a big difference in value. Here is the mean relative error of an 8.5 KB t-digest (δ=100) on 1M values from three distributions: lognormal (as in the benchmarks), Pareto with α=1.5 (a longer tail), and uniform between 1,000,000 and 2,000,000 (no tail):

| Quantile | Lognormal | Pareto | Uniform |
| --- | --- | --- | --- |
| 0.5 | 0.12% | 0.09% | 0.009% |
| 0.99 | 1.7% | 5.6% | 0.015% |
| 0.999 | 8.7% | 67% | 0.009% |
| 0.9999 | 83% | 868% | 0.004% |

A log-linear histogram of about the same size (1% error, 8 KB) has an error below 0.78% for all these cases.

So a log-linear histogram is better for latencies, sizes, and other positive measurements with long tails. A t-digest is better when you need a fixed size no matter what the values are, or when the values can be arbitrarily close to zero.

### Benchmarks

| Operation | Error | unsure | hdr | dd |
| --- | --- | --- | --- | --- |
| Add | 1% | **4** | **4** | 19 |
|  | 0.4% | **4** | **4** | 19 |
|  | 0.1% | **4** | **4** | 19 |
| Quantile | 1% | **48** | 283 | 1,750 |
|  | 0.4% | **90** | 1,708 | 3,100 |
|  | 0.1% | **337** | 1,712 | 11,967 |
| Merge | 1% | **334** | 16,369 | **302** |
|  | 0.4% | **657** | 115,052 | 808 |
|  | 0.1% | 3,249 | 115,018 | **2,862** |

Mean relative error at the requested 0.1%, over 1M values (lower is better):

| Quantile | unsure | hdr | dd |
| --- | --- | --- | --- |
| 0.5 | **0.033%** | **0.033%** | 0.050% |
| 0.99 | **0.038%** | **0.037%** | 0.048% |
| 0.999 | 0.027% | **0.019%** | 0.039% |
| 0.9999 | 0.016% | **0.002%** | 0.025% |

Memory after adding 1M values (lower is better):

| Error | unsure | hdr | dd |
| --- | --- | --- | --- |
| 1% | 8 KB | 40 KB | **6 KB** |
| 0.4% | 14 KB | 264 KB | **13 KB** |
| 0.1% | 56 KB | 264 KB | **40 KB** |

*Unsure* adds values as fast as *hdr* and 5× faster than *dd*, queries 5–19× faster than *hdr* and about 35× faster than *dd*, and merges about as fast as *dd* and 35–175× faster than *hdr*. It's slightly less accurate than *hdr* (using 5× less memory), and more accurate than *dd* (using 1.4× more memory).

1. [DDSketch paper](https://arxiv.org/abs/1908.10693) by Charles Masson et al., 2019. [↩︎](https://antonz.org/probabilistic-data-structures-2/#fnref:11)
2. [HdrHistogram](https://github.com/HdrHistogram) by Gil Tene. [↩︎](https://antonz.org/probabilistic-data-structures-2/#fnref:12)
3. [T-digest overview](https://antonz.org/probabilistic-data-structures#t-digest) and how it works. [↩︎](https://antonz.org/probabilistic-data-structures-2/#fnref:13)
4. [Log-linear histogram benchmarks](https://github.com/nalgeon/unsure/tree/main/loghist#benchmarks). [↩︎](https://antonz.org/probabilistic-data-structures-2/#fnref:14)
5. [HdrHistogram/hdrhistogram-go](https://github.com/HdrHistogram/hdrhistogram-go) by Coda Hale. [↩︎](https://antonz.org/probabilistic-data-structures-2/#fnref:15)
6. [DataDog/sketches-go](https://github.com/DataDog/sketches-go) by Datadog. [↩︎](https://antonz.org/probabilistic-data-structures-2/#fnref:16)

## MinHash

MinHash estimates how similar two sets are. It summarizes each set in a short fixed-size *signature* (for example, 256 numbers). Comparing two signatures gives the approximate *Jaccard similarity* of the sets: |A∩B| / |A∪B|, the proportion of unique items that both sets share.

The size of a signature doesn't depend on the size of the set, so you can compare two sets of a million items each just by comparing 256 pairs of numbers instead of checking every item. Plus, each set's signature is only calculated once, so comparing lots of sets to each other is relatively cheap.

MinHash is useful for finding near-duplicate documents, like web pages or essays (represented as sets of words or 3-word phrases). It's also useful for finding similar user profiles (as sets of liked items) or overlapping datasets (as sets of keys).

```go
// Two documents as sets of words.
strA := "the quick brown fox jumps over the lazy dog"
docA := minhash.New(256)
for w := range strings.FieldsSeq(strA) {
    docA.Add([]byte(w))
}

strB := "the quick brown cat jumps over the lazy dog"
docB := minhash.New(256)
for w := range strings.FieldsSeq(strB) {
    docB.Add([]byte(w))
}

sigA, sigB := docA.Signature(), docB.Signature()
sigA.Similarity(sigB) // 0.75 (true value 7/9 = 0.78)
```

The MinHash sketch has one setting: the signature size *k*, which gives a standard error of √(J(1−J)/k) for true similarity J. For example, with k=256 and J=0.5:

- 68% of estimates are within ±3.1 pp of J (0.47–0.53),
- 95% within ±6.2 pp (2·stdErr),
- 99.7% within ±9.4 pp (3·stdErr).

You can add items to a sketch, merge sketches, and get and compare signatures. You cannot check if a specific item was added, count the items, remove them, or list them.

### How it works

**Classic MinHash**<sup>[17](https://antonz.org/probabilistic-data-structures-2/#fn:17)</sup> hashes every item with *k* different hash functions. Here are two sets, A = {fox, cat, dog, owl} and B = {fox, dog, emu}, and their item hashes for k=4:

```text
item   h1     h2     h3     h4     in A   in B
fox    0.07   0.52   0.66   0.38    ✓      ✓
cat    0.21   0.15   0.80   0.91    ✓
dog    0.48   0.33   0.09   0.74    ✓      ✓
emu    0.63   0.27   0.44   0.12           ✓
owl    0.90   0.71   0.58   0.29    ✓
```

For each hash function, the set keeps only the smallest hash value among its items. These k minimums are the set's *signature*. To estimate the similarity of two sets, compare their signatures position by position, count the number of equal values, and divide by k:

```text
             h1     h2     h3     h4
A signature  0.07   0.15   0.09   0.29
B signature  0.07   0.27   0.09   0.12
equal        ✓             ✓
             → 2 of 4 = 0.5
```

The estimated similarity (0.5) is different from the actual value (2 shared items / 5 distinct items = 0.4). To get a more accurate estimate, k is usually much larger than in this example.

**One permutation hashing**<sup>[18](https://antonz.org/probabilistic-data-structures-2/#fn:18)</sup> hashes every item once, with a single hash function, and splits the range of hash values into k equal buckets. Each bucket keeps the smallest hash value among its items. Here are the same sets with k=4, using h1 from above:

```text
bucket       0            1            2            3
range        0.00–0.25    0.25–0.50    0.50–0.75    0.75–1.00

A items      fox 0.07     dog 0.48                  owl 0.90
             cat 0.21
B items      fox 0.07     dog 0.48     emu 0.63

A minimums   0.07         0.48         ·            0.90
B minimums   0.07         0.48         0.63         ·
```

Each bucket works like a separate MinHash over the items in its range. So the bucket minimums form a signature, and comparing two signatures works the same way. But there is a catch: when a set isn't much larger than k, some buckets end up empty (shown as · above), so there's nothing to compare in them.

**Optimal densification**<sup>[19](https://antonz.org/probabilistic-data-structures-2/#fn:19)</sup> solves this by filling each empty bucket with the value from another bucket in the same set. Each empty bucket tries other buckets in a pseudo-random order and copies the value of the first non-empty one:

```text
bucket       0         1         2         3
A minimums   0.07      0.48      ·         0.90
B minimums   0.07      0.48      0.63      ·

A signature  0.07      0.48      0.90 (3)  0.90
B signature  0.07      0.48      0.63  │   0.07 (0)
equal        ✓         ✓               │         │
             → 2 of 4 = 0.5            │         │
                                       │         │
             which bucket the value was copied from
```

This order depends only on the empty bucket's position, so two similar sets tend to fill empty spots with the same values. This makes the estimate work for sets of any size, with about the same error as classic MinHash.

**Unsure** keeps the k bucket minimums in the sketch. `Add` and `Merge` use the original buckets. Densification only happens in `Signature`, and it makes a copy of the buckets without modifying the sketch.

Each item is hashed once with 64-bit *wyhash*. Multiplying the hash by k once gives both the bucket and the value to store:

```text
┌─────────────────┬─────────────────┬─────────────────┐
│ high 64 bits:   │ next 32 bits:   │ rest:           │
│ bucket in [0,k) │ value           │ unused          │
└─────────────────┴─────────────────┴─────────────────┘
127              64                32                 0
```

Densification fills empty buckets in a coordinated way, spreading the copies evenly across the non-empty buckets. This keeps the error close to classic MinHash, and makes densification fast even for small sets.

### Benchmarks

| Operation | k | unsure | dgryski |
| --- | --- | --- | --- |
| Add | 64 | **5** | 30 |
|  | 256 | **5** | 115 |
|  | 1024 | **5** | 358 |
| Similarity | 64 | 25 | 24 |
|  | 256 | 104 | 103 |
|  | 1024 | 378 | 376 |

RMSE of the similarity estimate at k=256 and J=0.5 (lower is better):

| Distinct items | unsure | dgryski |
| --- | --- | --- |
| 256 | **2.89%** | 3.07% |
| 1,024 | **2.84%** | 3.12% |
| 4,096 | **2.99%** | 3.09% |
| 16,384 | 3.11% | **3.07%** |
| Memory | **1.0 KB** | 2.0 KB |

*Unsure* adds items 6–70× faster than *dgryski*, compares signatures at the same speed, has roughly the same accuracy, and uses half the memory.

1. [Classic MinHash paper](https://www.cs.princeton.edu/courses/archive/spring13/cos598C/broder97resemblance.pdf) by Andrei Broder, 1997. [↩︎](https://antonz.org/probabilistic-data-structures-2/#fnref:17)
2. [One permutation hashing](https://papers.nips.cc/paper/2012/hash/eaa32c96f620053cf442ad32258076b9-Abstract.html) by Ping Li et al., 2012. [↩︎](https://antonz.org/probabilistic-data-structures-2/#fnref:18)
3. [Optimal densification paper](https://arxiv.org/abs/1703.04664) by Anshumali Shrivastava, 2017. [↩︎](https://antonz.org/probabilistic-data-structures-2/#fnref:19)
4. [MinHash benchmarks](https://github.com/nalgeon/unsure/tree/main/minhash#benchmarks). [↩︎](https://antonz.org/probabilistic-data-structures-2/#fnref:20)
5. [dgryski/go-minhash](https://github.com/dgryski/go-minhash) by Damian Gryski. [↩︎](https://antonz.org/probabilistic-data-structures-2/#fnref:21)

Bloom filter and HyperLogLog are everyone's favorites, but they're not the only useful probabilistic data structures out there. In some situations, you might find these helpful:

- Binary fuse filter is a more compact alternative to a Bloom filter when you know all the items in advance.
- UltraLogLog is a more compact (but slower) alternative to HyperLogLog.
- Log-linear histogram is a much more accurate alternative to t-digest (with a variable size).
- MinHash compares large sets for similarity using a tiny fixed-size signature.
**What is signed integer floor division?**  
*Signed integer floor division* is where you do `a/b` and get a result that rounds towards `−∞`,  
whereas standard (*“truncated”*) signed division rounds towards `0`.  
As stated in Hacker's Delight: *“[I suspect that] floor division more often gives the result you want”*.

This article is about floor division where the **divisor is known at compile time**.

Despite the usefulness of this function, the world of *integer floor division* is in shambles:

This blog post aims to not only shine light on the fast algorithms, but will also **introduce a new fast approach** which, with ideal compilation:

The [benchmark](https://www.benjoffe.com/fast-floordiv#benchmarks) section has a detailed overview showing per-divisor results over many platforms, for throughput and latency.

It works in all bit-widths, and may find use on some 32-bit or SIMD applications, but the biggest benefit is in 64-bit.  
It also can be used for faster positive-modulus, and faster "Euclidean" division *(differs to floor division for negative divisors)*.

**Floor division can be much faster than you probably realise.**  
Below is a snapshot *throughput* benchmark for division **by 86400** *(the number of seconds in one day)*, the kind of performance you can expect using most languages' built-in methods, vs fast alternatives outlined in this blog.

Note: in the bar chart: lower = faster.

***Floor Div 86400 throughput - ARM64 Chips***As tested on MacBook Pro M4 Pro  
and Snapdragon X1-26-100

***Floor Div 86400 throughput  - X86 Chips***As tested on AMD Ryzen 9 9950X3D  
and Intel Core i7 (MacBook Pro 2016)

*<small>*Rust provides "div_euclid", which matches floor-div for positive divisors.  
See the [benchmark section](https://www.benjoffe.com/fast-floordiv#benchmarks) for a deeper comparison across over 40 divisors.</small>*

Since some people visiting this page will be just looking to copy/paste code, I'll start with this function builder on the right:

1. // MIT License Click to show
2. //
3. // Copyright (c) 2026 - Ben Joffe <https://www.benjoffe.com/>
4. //
5. // Permission is hereby granted, free of charge, to any person obtaining a copy
6. // of this software and associated documentation files (the "Software"), to deal
7. // in the Software without restriction, including without limitation the rights
8. // to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
9. // copies of the Software, and to permit persons to whom the Software is
10. // furnished to do so, subject to the following conditions:
11. //
12. // The above copyright notice and this permission notice shall be included in
13. // all copies or substantial portions of the Software.
14. //
15. // THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
16. // IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
17. // FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
18. // AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
19. // LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
20. // OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
21. // SOFTWARE.
22. 
23. // Fast floor division by 86400.
24. // (rounds towards negative infinity).
25. // Accurate over the full signed 64-bit range.
26. // Sign-selected multiplier variant.
27. // Optional ref:
28. // [https://www.benjoffe.com/fast-floordiv#fn=i64_86400](https://www.benjoffe.com/fast-floordiv#fn=i64_86400)
29. inline int64_t fast_i64_floordiv_86400(int64_t *x*) {
30. const int64_t *M* = ((__int128(1) << 79) / 86400 + 1);
31. const int64_t *m* = *M* + (*x* >> 63);
32. **return** (__int128) *x* * *m* >> 79;
33. }

<small>For the avoidance of doubt, the license only applies if you copy/paste the comment and code verbatim. No license is required if you re-write the same logic in your code.</small>

**Testing**  
A set of 65535 divisors from -32768 to 32767 for 64-bit can be generated into a single self-contained C++ file. It includes a boundary test in the same file.  
See the comment at the top of the download for how to build and run it.

Using this form, you can choose any bit-width and any divisor to get a copy/paste function ready to go.

There is also [reference algorithm ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://github.com/benjoffe/fastdiv/blob/main/algorithms/benjoffe.hpp) *(a reusable C++ template with additional microarchitectural performance tweaks)*.

*As you can see, the technique is so simple that I'd expect that *somebody* has done this before, but I've looked around and not found it documented anywhere. If it turns out to have been done before, at least this page will make it discoverable.*

For the rest of us, I'll cover a narrative about floor division, which matches my process of discovery... And if you want to create a fast library or compiler/language implementation, this will be your one-stop shop.

If you want to skip the history lesson, you can [jump straight to the new stuff](https://www.benjoffe.com/fast-floordiv#new).

**Article Sections:**

Let's suppose you want to convert a Unix timestamp measured in seconds, to *rata-die* (a day count). And let's also suppose you forgot how to do this properly, and you use standard *("truncated")* division.

We need to divide by `86400` *(60×60×24)*. We'll use a 64-bit timestamp, since a 32-bit timestamp can only hold about ±68 years.

You'll be very happy with this implementation on the right until somebody hands you a timestamp before 1970!

1. const int64_t *rd* = *x* / 86400;
2. **return** *rd*;

<small>The above function returns incorrect results for most negative values.</small>

Of course, you should be using *floor division*, the type of division that's useful for tracking repeating patterns like timestamps, angle rotations, tile positions etc. This is the type of division where the associated `"%"` operation is a proper *positive modulus*, not that fake modulus that "`%`" provides in C++, JavaScript etc.

Nonetheless, it's useful to understand what is going on under the hood when doing standard division like this. The pseudocode below shows what the compiled assembly is actually doing. It's essentially a mul‑shift and bump-by-1 for negatives.

1. const i64 *M* = (i128(1) << 77) / 86400 + 1 // Precomputed
2. const i128 *wide* = i128(*x*) * *M*
3. const i64 *tbit* = *wide* >> 77 // high64(wide) >> 13
4. const i64 *sign* = u64(*x*) >> 63 // ts < 0 ? 1 : 0
5. **return** *tbit* + *sign*

| x86-64 Latency Steps |  |  |
| --- | --- | --- |
| Step | Computation 1 | Computation 2 |
| 1 | `wide = ts * M` |  |
| 2 | *mul-latency* | `sign = u64(ts) >> 63` |
| 3 | *mul-latency* |  |
| 4 | `high64bits(wide) >> 13` |  |
| 5 | `... + sign` |  |

If you haven't bit twiddled much, the step `u64(ts) >> 63` might seem odd. This is just moving the highest-bit down to the bottom. Since the top bit is the sign-bit on 2's complement computers, this leaves a 1 for negative numbers and a 0 for positive numbers.

Btw, if you're new to all this, you might think: *"Great! I now understand how signed division works at the compiler level!"*  
Sorry to burst the bubble, but here's what the same thing looks like for 64-bit division by 100:

1. **return** *x* / 100;

1. const i64 *M* = (i128(1) << 70) / 100 + 1
2. const i128 *wide* = i128(*x*) * *M*
3. const i64 *tbit* = ((*wide* >> 64) + *x*) >> 6
4. const i64 *sign* = u64(*x*) >> 63
5. **return** *tbit* + *sign*

You should notice we now have some extra junk in there: `((wide >> 64) + x) >> 6`.  
This is required because the magic multiplier for `100` happens to require all 64-bits for `M`.This causes the top bit to be `1`, making `M` a negative number, and as computed, the value of `M` ends up`2^64` lower than it should be. Since we compute `x * M`, the value of `wide` is thus `2^64 * x` lower than it should be. By adding `x` to the upper-register of the wide double-register result, we correct for it perfectly.  
Divisors that require these corrections are referred to by some authors as *uncooperative divisors*.

| x86-64 Latency Steps |  |  |
| --- | --- | --- |
| Step | Computation 1 | Computation 2 |
| 1 | `wide = x * M` |  |
| 2 | *mul-latency* | `sign = u64(x) >> 63` |
| 3 | *mul-latency* |  |
| 4 | `high64bits(wide) + x` |  |
| 5 | `... >> 6` |  |
| 6 | `... + sign` |  |

The main takeaway here is that regular division is usually the cost of around 1 multiplication + 2-3 cycles.

Okay, *back to div 86400*; you get bitten by the bug, and decide to patch it. It's pretty clear that the bug can occur when `x < 0`, but not always. If it's negative *and* divisible by 86400, it still works.  
So therefore, it needs adjusting when `rem < 0`, like so:

1. const int64_t *div* = *x* / 86400;
2. const int64_t *rem* = *x* % 86400;
3. **return** *div* - (*rem* < 0);

But you think to yourself, surely there must be a faster way? Computing the modulus is almost as expensive as the division itself, and it gets thrown away after the bump in our theoretical use-case.

The 2nd example below is perhaps the first simplification that may come to mind, but it's actually slower! You can visit the Godbolt link to see that it produces more assembly lines...

Okay, screw this unintuitive nonsense, let's Google *"fast floor division in c++"*, and get an [AI summary like this ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://www.benjoffe.com/resources/FastDivision-GoogleAISummary.pdf) *(cached PDF export)*.

**This AI summary is very misleading**, as it falsely claims *"Here are the fastest, branchless methods for each scenario."*, before presenting a constant floor division routine that is no better than our attempt here, despite faster ways being known for 30 years+ *(although it handles negative divisors at least)*.

In any case, the code to the right is what it suggests.

At least now we can have a flexible utility function, and it seems GCC and Clang can compile this into the same assembly as our previous version when the divisor is hard-coded *([see on Godbolt ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://godbolt.org/z/jvqv4b74a))*.

This is basically the same function used by [Java Math.floorDiv ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://github.com/openjdk/jdk/blob/2365ecc5fd83cf27c6c55aaca5aa6bad6ae9dbbf/src/java.base/share/classes/java/lang/Math.java#L1475), [Python's numpy ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://github.com/numpy/numpy/blob/2f1eca306857b641fb0fef0ab854a2d4137e1581/numpy/_core/src/umath/loops_arithmetic.dispatch.c.src#L346-L369), [Zig ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://codeberg.org/ziglang/zig/src/tag/0.17.0/src/codegen/llvm/FuncGen.zig#L3535), [Ruby ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://github.com/ruby/ruby/blob/v4.0.7/internal/fixnum.h#L122) and many other libraries.

1. const int64_t *div* = *x* / *y*;
2. const int64_t *rem* = *x* % *y*;
3. **return** *div* - (*rem* != 0 && (*x* ^ *y*) < 0);

Hacker's Delight, 2nd Edition, has a section listed in the table of contents: *"10–12 Applicability to Modulus and Floor Division"*. That sounds promising!

It comes immediately after *dozens* of awesome pages with fancy tricks for other types of division (signed, unsigned etc.).

> *“* It might seem that turning modulus or floor division by a constant into multiplication would be simpler, in that the “add 1 if the dividend is negative” step could be omitted. This is not the case. The methods given above do not apply in any obvious way to modulus and floor division. Perhaps something could be worked out; it might involve altering the multiplier m slightly, depending upon the sign of the dividend. *”*— Henry S. Warren, Jr.,   Hacker's Delight, 2nd Edition

That's the whole section...

Normally, it might be copyright infringement to duplicate an entire section from a book, but in this case it's so short I think I'm covered by fair use.

Although Warren doesn't offer any solutions, the section highlighted in yellow perfectly predicts the new approach I'll introduce later.

At this point, you would be forgiven in thinking this can't be optimised any further; maybe it can't for runtime divisors (I have not investigated, since I've focused mainly on compile-time). Looking further, the first Google Search result: the archaeological remains of the once bustling Stack Overflow. The title looks promising: [Fast floor of a signed integer division in C / C++ ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://stackoverflow.com/questions/46265403/fast-floor-of-a-signed-integer-division-in-c-c).

The post is from 2017, and has 6 answers. The OP and the top five up-voted results all use variations of the above technique.

Finally, if you scroll to the bottom, you see after seven years, user *ufoguy* finally posts an answer that is notably faster for compile-time divisors:  
 *"[Not] sure why this one wasn't mentioned; just one division, no modulo, branch-less:"*

1. int floor_div(int *a*, int *b*) {
2. **return** (*a* + (*a* < 0)) / *b* - (*a* < 0);
3. }

By my benchmarks this gives a neat improvement, it runs **around 50% greater throughput** on most devices.

What does *ufoguy* get for adding this?  
No thanks, no up-vote, just a comment pointing out that this does not account for negative divisors.  
A fair caveat. If we're going to make a fast general purpose lib, it might as well be flexible.

Luckily, the general case was solved at least as far back as the 90s.  
It is documented clearly on page 6 of *[Division by Invariant Integers using Multiplication ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://gmplib.org/~tege/divcnst-pldi94.pdf) - Granlund, Montgomery, 1994*.

Using the technique from that paper, we can create a simple flexible template function (non-zero divisor known at compile time).  
I've prepared an example using that technique which can be called like this in C++: `floor_div<int64_t(86400)>(timestamp);`.

Note that the paper demonstrates a fully branchless version, but I prefer the one above for division by constants, as it's just blindly clear what's going on, and also given the branch is compile-time, it's guaranteed to simplify. Compilers readily recognise the repeated comparison eg. `(x < 0)` and reuse the result. However see a [Godbolt ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://godbolt.org/z/K56YedWGe) comparison of the fully branchless version to see how MSVC struggles to simplify it.

Seems like floor-div is solved right?  
We're only just getting started...

1. #include <type_traits>
2. 
3. template <auto *D*>
4. constexpr decltype(*D*) floor_div(decltype(*D*) *x*) {
5. **static_assert**(std::is_integral_v<decltype(*D*)> &&
6. std::is_signed_v<decltype(*D*)> && *D* != 0,
7. "divisor must be a signed non-zero integer");
8. 
9. **if constexpr** (*D* > 0)
10. **return** (*x* + (*x* < 0)) / *D* - (*x* < 0);
11. **else**
12. **return** (*x* - (*x* > 0)) / *D* - (*x* > 0);
13. }

<small>*Code highlighted in green is compile-time only and has no runtime impact.*</small>

The division in the previous section was, at best, a mul-shift plus 5-6 cycles.  
Why so many?

Luckily for us, *Granlund and Montgomery* have another trick up their sleeve, but it's only specified for positive divisors:

1. i64 *s* = *x* >> 63 // x < 0 ? -1 : 0
2. u64 *a* = *x* ^ *s*
3. u64 *b* = (u128) *a* * *M* >> *S*
4. i64 *c* = *b* ^ *s*
5. **return** c;

The diagram to the right is my attempt at visualising this.  
It's a bit crazy!

The operation `x ^ s` moves negative inputs to the non-negative domain, specifically negative values become `-1 - x`;   *(now `>= 0`)*.

This is the same as reflection around `-0.5`, hence the pivot point of the arcs all lie along this vertical dashed line.

The big saving here comes from the fact that `a` is not only unsigned, but also only has a range of `0..2^63-1` (half of the usual range). This means that a mul-shift will work in all cases, even for *uncooperative divisors*.

I've found one library in the wild that uses this technique, [PyPy ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://github.com/pypy/pypy/blob/release-pypy3.12-v8.0.1/rpython/jit/metainterp/optimizeopt/intdiv.py#L53), but it falls back to div/mod algorithm for negative divisors.

If you're counting along, this looks like a **mul-shift plus 3 cycles**, a clear improvement.  
On ARM it could theoretically be a mul-shift plus 2 cycles, as the right-shifts can fuse with the XORs, but in practice on the machines I've tested, these fused operations don't result in the speed gain that raw cycle-counting would suggest.

The next really great paper on floor division seems to be: [N-Bit Unsigned Division Via N-Bit Multiply-Add ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](http://www.acsel-lab.com/arithmetic/arith17/papers/ARITH17_Robison.pdf), 2005, by Arch D. **Robison**. The paper is primarily about unsigned division, but *Section 4.3* covers floor division.

The idea presented in the paper is amazing, it almost seems like a magic bullet. There's no branch or ternary, it's a simple mul-add-shift in many cases.

You can use the form to the right to configure any division you like.  
Below is an example of the simplicity of it in the best of cases:

1. i32 *A* = 1374389535
2. i32 *B* = 0x28F50000 // 687144960
3. **return** (i64(*x*) * *A* + *B*) >> 37;

Note that in that example above, I'm using an additive value of `0x28F50000`, which is different to the paper, which uses `A/2`.  
This is the same hex-value with the bottom 2-bytes zeroed out, which makes for more compact ARM assembly. Not all divisors can have this optimisation applied, it must be made carefully.

1. // MIT License Click to show
2. //
3. // Copyright (c) 2026 - Ben Joffe <https://www.benjoffe.com/>
4. //
5. // Permission is hereby granted, free of charge, to any person obtaining a copy
6. // of this software and associated documentation files (the "Software"), to deal
7. // in the Software without restriction, including without limitation the rights
8. // to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
9. // copies of the Software, and to permit persons to whom the Software is
10. // furnished to do so, subject to the following conditions:
11. //
12. // The above copyright notice and this permission notice shall be included in
13. // all copies or substantial portions of the Software.
14. //
15. // THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
16. // IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
17. // FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
18. // AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
19. // LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
20. // OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
21. // SOFTWARE.
22. 
23. // Fast floor division by 100.
24. // (rounds towards negative infinity).
25. // Accurate over the full signed 32-bit range.
26. // Robison's N-bit multiply-add method.
27. // Cooperative divisor (`A` fits in bit-width).
28. // Optional ref:
29. // [https://www.benjoffe.com/fast-floordiv#robison=i32_100](https://www.benjoffe.com/fast-floordiv#robison=i32_100)
30. inline int32_t robison_i32_floordiv_100(int32_t *x*) {
31. int32_t *A* = ((1ll << 37) / 100 + 1); // 1374389535
32. int32_t *B* = (*A* / 2) & ~0xFFFF; // 687144960
33. **return** (int32_t) (((int64_t)*x* * *A* + *B*) >> 37);
34. }

<small>For the avoidance of doubt, the license only applies if you copy/paste the comment and code verbatim. No license is required if you re-write the same logic in your code.</small>

**Testing**  
A set of 65535 divisors from -32768 to 32767 for 32-bit can be generated into a single self-contained C++ file. It includes a simple exhaustive test in the same file.  
See the comment at the top of the download for how to build and run it.

On ARM devices, this compiles to a single fused "multiply-accumulate" operation, followed by right-shift. Even on ARM32, it can use the `smlal` operation to multiply, add the constant, and obtain the upper 32-bit result, without ever needing any 64-bit emulation.

Of course, x86-64 devices can run this fine: mul, add, shift.  
32-bit x86 is where it becomes less clean (but not terrible). On this platform, the addition is performed on the lower 32-bit result, followed by `adc` to the upper 32-bit result (adds the "carry flag", which holds a `1` or `0` depending on whether the lower register overflowed or not).

So, what's the problem with this formula? Well, there's **two problems**...

**Problem #1: It often requires a wider multiply.**  
To the right is how things change for division by `101`.  
*There's a big difference here, see if you can spot it...*

Notice that `A` is no longer `i32` but `i64`?  
This is an instance of *this formula's* uncooperative divisor; a case where the number of bits required in the multiplier is just one-too-many.

**Problem #2: Wider multiplication gets clunky at 64-bit**  
In the previous examples we talked of using wider types. This doesn't really work in 64-bit, you can use a type of "128-bit" in code, but it will be "emulated" using pairs of 64-bit registers. The below is how the Robison formula works out for our usecase `86400`:

1. i64 *A* = -4454547087429121353 // 2^80 / 86400 + 1 - 2^64
2. i64 *B* = 0x6117 << 48
3. i128 *w* = i128(*x*) * *A* // Compute high-64 and low-64
4. i64 *h* = (*w* + *B*) >> 64 // 128-bit + 64-bit wide addition
5. // "add back" *x* below: a correction for negative *A*.
6. **return** (*h* + *x*) >> 16

You can visit the Godbolt link to see that this compiles fairly reasonably on x86, the main hindrance is the "add back": it's only a couple of operations on x86 (`adc`), but on ARM64 it's a double-whammy: there's two multiplication operations (`mul` and `smulh`).  
This is because ARM64 requires a separate multiplication for each high and low 64-bit half-result.

The "add back" is needed for the same reason as noted in the *[“Aside on Uncooperative Divisors”](https://www.benjoffe.com/fast-floordiv#uncooperative-aside)* earlier.

These "issues" aren't terrible, this is still a *really fast* floor division function. It just leaves more left on the table to optimise.

*Note: in case you haven't realised yet, problem #1 and #2 are really the same.*

There's a second way to write the same math, which spells out the carry by hand instead of leaving it to a 128-bit addition. An example is in the code block below.

In theory the compiler should emit equivalent assembly for either form; in practice the two shapes don't always compile the same, so it's useful to know both and swap in whichever your compiler handles better. The ideal output for the carry form is an `add` followed by a carry-consuming instruction *(`adc` on x86, `cmp` + `cinc` on ARM64)*; the failure mode is a longer dependent chain on the critical path.

1. i64 *A* = -4454547087429121353 // 2^80 / 86400 + 1 - 2^64
2. u64 *B* = 0x6117 << 48
3. i128 *w* = i128(*x*) * *A* // Compute high-64 and low-64
4. u64 *lo* = u64(*w*)
5. i64 *hi* = i64(*w* >> 64) + *x* // "add back" *x*
6. *hi* += (*lo* + *B* < *lo*) // Carry from adding *B* to the low half
7. **return** *hi* >> 16

You can see the assembly for each approach on [Godbolt here ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://godbolt.org/z/4onK1P1q9). GCC and Clang each produce tighter assembly for a different variant.  
Since compilers treat these differently, both of them are included in the benchmarks for a more thorough comparison.

There's one more compiler quirk worth knowing about: when the multiplier *A* is a compile-time constant, clang will rewrite `smulh(x, A)` into` umulh(x, A) + (x >> 63) * A`, adding two instructions to every divide. A one-line inline-asm barrier that holds *A* in a register but hides its value from the optimiser is enough to shut this down — the constant still gets materialised once and hoisted out of the loop.

Nonetheless, where widening is possible, Robison's approach is great. This includes 32-bit floor division on ARM (even SIMD in this case).  
It's ideal in all 8-bit scenarios, as all mainstream chips seem to require doubling width anyway for 8-bit multiplication.  
It can also lead to some really cool special cases, such as:  
`fast_i8_floordiv_51 => (x * 5 + 2) >> 8`  
That function above can compile to just 2 assembly operations on x86! *(`LEA` + arithmetic right-shift).*

> “These computer division algorithms are all just fancy mul-shifts at the end of the day.”  
> — Sun Tzu, The Art of War

Let's try to go down to bare metal, and see what we get if we do a plain mul-shift for division by 3.  
No corrections, no nothing.

We choose `3`, because it's the first non-trivial divisor *(power-of-2 divisors are solved with a simple arithmetic right-shift).*

1. i64 *M* = u64(-1) / 3 + 1 // *u64(-1) = 2^64-1*
2. i64 ***y*** = (i128) *x* * *M* >> 64

The round-up multiplier gives a perfect sequence of sets-of-3 in the positive direction, and just one discontinuity in the negative direction with a set of -1 and -2 *(everything negative is shifted right)*.

| x: | -10 | -9 | -8 | -7 | -6 | -5 | -4 | -3 | -2 | -1 | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| y: | -4 | -4 | -3 | -3 | -3 | -2 | -2 | -2 | -1 | -1 | 0 | 0 | 0 | 1 | 1 | 1 | 2 | 2 | 2 | 3 | 3 |

Note: visualising this makes clear why *standard truncated* division is implemented for cooperative divisors like this with a simple mul shift, with a +1 bump for negatives, that gives five values of zero centred around the origin.

But, we are not here for truncated division...  
**— forget about that chart below!**

Anyway, if we use the round-down multiplier:

...we get the opposite result: the negative direction has a perfect sequence, and the positive direction has a broken quadruple set at 0-3 *(everything positive is shifted right)*:

| x: | -10 | -9 | -8 | -7 | -6 | -5 | -4 | -3 | -2 | -1 | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| y: | -4 | -3 | -3 | -3 | -2 | -2 | -2 | -1 | -1 | -1 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 2 | 2 | 2 | 3 |

It turns out that `3` is a very flexible divisor, and for now you'll just need to take my word for it that in 64-bit, the neat half of each continues over the entire signed-64 bit range.  
So the answer here is simple, we can just use a different multiplier for positives and negatives:

1. i64 *M* = MAX_U64 / 3 + 1
2. i64 *m* = *M* + (*x* >> 63) // = x < 0 ? M - 1 : M
3. i64 ***y*** = (i128)*x* * *m* >> 64

| x: | -10 | -9 | -8 | -7 | -6 | -5 | -4 | -3 | -2 | -1 | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| y: | -4 | -3 | -3 | -3 | -2 | -2 | -2 | -1 | -1 | -1 | 0 | 0 | 0 | 1 | 1 | 1 | 2 | 2 | 2 | 3 | 3 |

Now it's clean in both directions.

This is the ideal scenario, as the value `M + (x >> 63)` can be computed very cleanly. It involves no extra constant materialisation, no flag-to-register conversion, and on ARM64 chips it can be computed with a single shift-add assembly operation (`add x0, x1, x2, asr #63`).

GCC compiles this well, however in my benchmark loops Clang seems to bungle it a little. One can force better compilation on Clang in C++ by writing `asm("" : "+r"(m));`after the 2nd line, which stops the compiler from proving that `m >= 0`, which fixes the bungled optimisation.  
*Note: similar asm-hacks were required in the benchmark to get the best out of the Robison algorithm.*

However, it's not the only way we can implement it. Two other options are available in the case of floor division by 3:

1. i64 *M* = MAX_U64 / 3 + 1 // Round up M
2. i64 *t* = *x* + (*x* < -1)
3. i64 ***y*** = (i128)*t* * *M* >> 64

1. i64 *M* = MAX_U64 / 3 // Round down M
2. i64 *t* = *x* + (u64(*x*) < 0x7FFFFFFFFFFFFFFF)
3. i64 ***y*** = (i128)*t* * *M* >> 64

In the first case, we don't want to bump `x = -1` because that will give an incorrect result of `y = 0`.  
In the second case, we don't want to bump `x = MAX_INT64` because that will overflow.  
The reason we don't *need* to bump`x = MAX_INT64` *`(x = 2^63-1)`*, is because `(2^63-1) FLOOR_DIV d = (2^63) FLOOR_DIV d` for any divisor `d`that is not a power‑of‑2. These would only differ if `2^63` was divisible `d`, but it's clearly not since the prime factors of `2^63` are all just `2`.  
That identity is about exact division though, and the round-down multiplier is only approximate. If `d` divided `2^63-1`, then skipping the bump would leave `INT_MAX` an exact multiple nudged slightly downward, and the result would be one too low. Those divisors are safe to ignore here only because the `INT_MIN` check *(see Implementation)* already rules them out at register-sized shifts.  
This is the same reason a saturating increment is used in fast *unsigned* division of certain divisors *(see ridiculousfish / libdivide)*.

It is fortunate that the two bounds for the latter approach can be implemented with a sign cast and single comparison. Both constants of `-1` and `0x7FFFFFFFFFFFFFFF` can also materialise in a single ARM assembly operation due to their repeating bit-patterns. In a tight loop, such constants would typically be materialised once outside of the loop.

Anyway, why talk about all this when the case of `3` was already solved?  
Well it turns out that not all divisors are as flexible as `3`.

All non-power-of-2 integer divisors come in two overlapping sets:

Divisors that can use both, are eligible for the *Sign-Selected-Multiplier* version.

Below you can see the first 100 divisors, and what method is selected. The pattern is quite chaotic, but easily computed at compile-time:

The number under this denotes the shift-size, highlighted when it's a clean register-sized shift.

*Whoops, the above widget lets you select "Negative" divisors, but I haven't talked about those yet...*

### Negative Divisors

Everything we have gone through works the same with negative divisors. We just have to be careful with signs, comparisons etc.  
I'll refer to "round down" multipliers as those that round towards zero, and "round up" multipliers as those that round away from zero.

The divisor `-3` happens to not be flexible, it requires "round down", but `-5` works both ways with bit-shift of 65:

1. i64 *M* = -((i128(1) << 65) / 5)
2. i64 *m* = *M* + (*x* >> 63) // = x < 0 ? M - 1 : M
3. i64 ***y*** = (i128)*x* * *m* >> 65

Below are the two alternative approaches for `-5`:

1. i64 *M* = -((i128(1) << 65) / 5 + 1) // Round "up" M
2. i64 *t* = *x* - (*x* > 1)
3. i64 ***y*** = (i128)*t* * *M* >> 65

1. i64 *M* = -(MAX_U64 / 5) // Round "down" M
2. i64 *t* = *x* - (u64(*x*) > (1 << 63))
3. i64 ***y*** = (i128)*t* * *M* >> 64

<small>*Note: This variant works with a clean 64-bit shift*</small>

*<small>The term `(1 << 63)` can alternatively be written `0x8000000000000000`.</small>*

*Floor modulus* flows naturally from floor-division, and is a *"positive modulus"* function for positive divisors:

1. const int64_t *pos_mod* = *x* - fast_floor_div<*Divisor*>(*x*) * *Divisor*

For certain divisors of the form 2N−2K, I have a faster alternative that uses an add-shift-mask:

*See the [day-of-week article](https://www.benjoffe.com/fast-day-of-week) and [time-of-day article](https://www.benjoffe.com/fast-time-of-day) for more details about this identity.*

Euclidean division is the same as floor division for positive divisors.  
For divisors less than `-1`, we can use the following identity which results in just one extra cycle for the subsequent negation (the first negation for the `floor_div` call is performed at compile-time).  
The second runtime negation can in some cases be absorbed for "free" in subsequent operations, such as in obtaining Euclidean modulus:

1. const i64 *floor_div* = fast_floor_div<*-Divisor*>(*x*) // Negate divisor
2. const i64 *euc_div* = -*floor_div*
3. const u64 *euc_mod* = *x* + *floor_div* * *Divisor*

### Implementation

The simplicity of these functions above comes with extra compile-time complexity to solve the constants and variant, but it builds fast.

Basically it boils down to iteratively testing the worst-case scenario for both the round-up and round-down versions, starting with an ideal register-sized shift W. A solution is valid if it passes the worst-case numerator. Eg:

One detail matters here: the worst case for round-down is `INT_MIN`, and its product must not land exactly on an integer, or the result comes out one too high. That happens exactly when D divides 2W−1−1 *(in 64-bit: 7, 49, 73, 127, 337, 511, …)*.  
For these divisors, writing r=2SmodD, r=2S−(W−1) at every register-sized shift, so round-down never passes and they are **forced to round-up**. <small>*(For negative divisors it's the other way around: round-up is the one that can land on an integer, for |D| dividing 2W−1+1, in 64-bit: 3, 9, 19, 27, 43, 57, …)*</small>

If solutions are found for both, then the sign-selected variant will also work, at a shift equal to the greater of the two solutions found.

My benchmarking (in 64-bit) suggests it is fastest to choose sign-selected when possible, except for some rare cases:

On x86, round-up loses to sign-selected because its bias is a signed compare `(x < -1)`. The result of a signed compare isn't left in the carry flag, so the compiler needs `cmp → setl → add`, one more instruction than round-down's `cmp → adc`, and that extra cycle cancels the saving from skipping the extra shift. On an Intel Mac I got equal performance between them, but on an AMD processor I saw the sign-selected version run faster. As such, my benchmarks and the [reference implementation ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://github.com/benjoffe/fastdiv/blob/main/algorithms/benjoffe.hpp) alter the choice here for x86.

These exceptions noted above (register-sized shifts) are somewhat common for small divisors, eg `5`, `6`, `9`, `14` etc., however, over the full set of possible 64-bit divisors, it is a vanishingly small set.  
The Venn diagram below shows the distribution of divisors, and this tiny set is noted in the lower right.

The problem of finding out which variant works for a given divisor boils down to the same problem as finding an unsigned divisor in a bit-width one-size smaller than usual, i.e.: `63`, `31`, `15`, or `7`; and others have written at length about this, hence I'd like to keep this section brief. The more important thing is the proof that the negative side works given the positive side is well studied *(see [Annexure A - Proof](https://www.benjoffe.com/fast-floordiv#proof)).*

> “When it comes to signed floor division, there are no cooperative divisors, or uncooperative divisors, just **these united divisors**.”  
> — Barack Obama, 2004 Democratic National Convention

Well, by all means feel free to, but make sure to test it thoroughly, otherwise you might end up with a bug like in Google's TensorFlow.

If you're interested, you can [view the source ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://github.com/tensorflow/tensorflow/blob/v2.5.3/tensorflow/core/kernels/cwise_ops.h#L391) to try to figure out yourself what was wrong with it.

The source uses templates, but I've written a simpler 64-bit pseudocode version to the right.

There's two reasons this implementation is not great for division by constants known at compile-time. One is a bug, one is a performance issue.

1. On performance: since the if/else statement is branching on both x and y, and the formulas in both branches are quite different, the compiler won't typically reduce this to a branchless form for a given divisor's sign.
2. But more importantly, it has an overflow bug!The term abs_x + abs_y - 1 specifically will overflow the signed 64-bit range for many extreme-valued inputs.

1. if ((*x* < 0) != (*y* < 0)) {
2. const i64 *abs_x* = abs(*x*)
3. const i64 *abs_y* = abs(*y*)
4. **return** -(*abs_x* + *abs_y* - 1) / *abs_y*
5. } else {
6. **return** *x* / *y*
7. }

The buggy implementation of this floordiv function was present in the [1.0 release ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://github.com/tensorflow/tensorflow/blob/r1.0/tensorflow/core/kernels/cwise_ops.h#L241) in Feb 2017.  
**This bug then remained in place for over 4 years** until it was [fixed in May 2021 ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://github.com/tensorflow/tensorflow/commit/b47be308c4b5ac7babd6400a8fb40c3d8bf163d6).

No shade to the author, this is fiddly to get right. The main reason I wanted to highlight this was to show how easy it is to get wrong, even in a mature, heavily-reviewed codebase. **This is all the more reason for languages and standard libraries to provide this function outright.**

A fix to avoid the overflow could be [to do what CPython does ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://github.com/python/cpython/blob/3.14/Objects/longobject.c#L4297), by using unsigned integers, and factoring out the `abs_y` term. This might still cause issues at `INT_MIN` though.

This mostly solves the bug, but given you've read this far you probably know a few faster ways to do it by now.

1. *// Note: CPython only calls this when x, y both non-zero,*
2. *// extra x != 0 check added for this example.*
3. if (*x* != 0 && (*x* < 0) != (*y* < 0)) {
4. const u64 *abs_x* = abs(*x*)
5. const u64 *abs_y* = abs(*y*)
6. **return** -1 - (*abs_x* - 1) / *abs_y*
7. } else {
8. **return** *x* / *y*
9. }

Tests used for validating the functions in this article can be found in the testcase code: [https://github.com/benjoffe/fastdiv ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://github.com/benjoffe/fastdiv).

The same repository is used for benchmarking, and you can run them yourself like this:

```
git clone https://github.com/benjoffe/fast-floordiv.git
cd fast-floordiv
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
./build/bin/div_bench -batch=8
./build/bin/div_bench -latency
```

The benchmarks run for all non-power-of-2 divisors between `-2^4` and `2^5`, as well as a handful of *cherry-picked* larger positive divisors (100, 360, 86400, 10<sup>5</sup>, 10<sup>7</sup>, 86400000, 10<sup>8</sup>). The reason is detailed in the x86 section below.

In the charts, the x-axis represents these various divisors, and the y-axis is the *nanoseconds-per-division* (lower = faster).

All results were obtained by running the benchmark with `-repeat=10` and recording the *median* results.  
The `-batch=8` command runs each divisor 8 times before loading the next entry from memory. This ensures that the processor is not bottlenecked by memory access.  
Latency results use the same command but replace the batch flag with `-latency`. This mode feeds the result of each computation into the next division, so there is no parallelisation.

To avoid making this page huge, I have grouped the benchmarks by chip type (ARM, x86) and benchmark type (throughput, latency).

On Clang, the `New` algorithm has highest throughput for all divisors, and occasionally tied with `gm-v2`.  
The fastest alternatives are `gm-v2` for positive divisors and `Robison` for negatives.  
MSVC appears to produce sub-optimal assembly for negative divisors for a few of the algorithms.

(pinch to zoom)

**Device and Compiler:** MacBook Pro M4 Pro - macOS 15.6.1 - Apple Clang 17.0.0

(pinch to zoom)

**Device and Compiler:** Lenovo IdeaPad Slim 5 (Windows 11 25H2) - Snapdragon X1-26-100 @ 2.956 GHz - Clang 23.1.3

(pinch to zoom)

**Device and Compiler:** Lenovo IdeaPad Slim 5 (Windows 11 25H2) - Snapdragon X1-26-100 @ 2.956 GHz - MSVC 19.51.36260

We get similar results for latency, with the `New` algorithm performing best, or tied-best.

(pinch to zoom)

**Device and Compiler:** MacBook Pro M4 Pro - macOS 15.6.1 - Apple Clang 17.0.0

(pinch to zoom)

**Device and Compiler:** Lenovo IdeaPad Slim 5 (Windows 11 25H2) - Snapdragon X1-26-100 @ 2.956 GHz - Clang 23.1.3

(pinch to zoom)

**Device and Compiler:** Lenovo IdeaPad Slim 5 (Windows 11 25H2) - Snapdragon X1-26-100 @ 2.956 GHz - MSVC 19.51.36260

x86 processors are where we have more of a mixed bag.  
For throughput, the fastest algorithm seems to fluctuate between `Robison` and the `New` algorithm.  
Sometimes `gm-v2` comes out tied as fastest (eg. divisors `6` and `9`).  
You can see now why some larger divisors were cherry-picked: they demonstrate that *some* useful divisors perform well in the `New` algorithm.

The cases where the `New` algorithm does *not* win follow a clear pattern:

- Positive: 7, 11, 13, 22, 26, 29. These are all round-up-only divisors (~20% of all 64-bit positive divisors)
- Negative: -3, -5, -9, -11, -13, -15. These are divisors that don't use sign-selected where Robison is cooperative (~40% of all 64-bit negative divisors)

(pinch to zoom)

**Device and Compiler:** AMD Ryzen 9 9950X3D - Ubuntu 24.04.1 - Clang 18.1.3

(pinch to zoom)

**Device and Compiler:** AMD Ryzen 9 9950X3D - Ubuntu 24.04.1 - GCC 13.3.0

(pinch to zoom)

**Device and Compiler:** 2016 MacBook Pro - macOS 12.7.6 - Apple Clang 14.0.0

Latency benchmarks are where we start to see a clearer winner on x86.  
While there was a lot of fluctuation before, now `Robison` wins for nearly all divisors.  
Rarely, the `New` algorithm seems to win on both throughput and latency, as seen for `14, -7, -14` *(round-down with 64-bit shift)*.

(pinch to zoom)

**Device and Compiler:** AMD Ryzen 9 9950X3D - Ubuntu 24.04.1 - Clang 18.1.3

(pinch to zoom)

**Device and Compiler:** AMD Ryzen 9 9950X3D - Ubuntu 24.04.1 - GCC 13.3.0

(pinch to zoom)

**Device and Compiler:** 2016 MacBook Pro - macOS 12.7.6 - Apple Clang 14.0.0

Finally, I note that if you need the modulus, the gap between "traditional" and the faster algorithms will close, but they still remain faster. I would like to actually finish this blog post one day so I'll skip these benchmarks.

The points below may be worth considering for anyone looking to make a fast floor division library or language/compiler feature:

Two further points worth noting are:

If you found this interesting, you might also like to see the below two recent blog posts.  
They both discuss a new trick for faster positive-modulus for divisors of the form `2^A - 2^B` *(eg. 12, 24, 60 etc.)*, which might be worth including in any library that does both floor division and positive-modulus.

You should [follow me on X ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://x.com/benjoffe) to get notified when I publish more optimisation articles.

<small>Revision history:</small>

These inequalities are strict (not ≤), and this is a requirement rather than a free fact. That D isn't a power of 2 only tells us neither multiplier is exactly 2S/D. For round-up the strictness then follows from the bound. For round-down, the product at n+1=2N lands exactly on q when D∣2N−1, since for those divisors 2S=2N⋅r at every register-sized shift. The solver rejects round-down for them, which forces them to round-up.

In simple terms, these mul-shifts slowly "drift" away from the true ratio. Apart from at x=0, the non-rounded terms are never an integer *(the check above ensures this)*.  
The reason to point this out is that we will use the below identity which relies on that fact:

**Sign-selected.** This uses round-up's unbumped half and round-down's unbumped half, so it works at any shift where both roundings work. A rounding that works at some shift keeps working at larger shifts, so it's enough that each works somewhere within the N-bit multiplier limit.

**Negative divisors.**

So this is the positive-divisor problem applied to −x. The one difference is the range: −x runs from −(2W−1−1) up to 2W−1. The non-negative side holds one value more than W−1 bits allow (the image of INT_MIN), and the negative side holds one value less. That extra value is where round-up can land on an integer, which it does for |D|∣2N+1, so those divisors can't use round-up. The missing value on the other side is the one that ruled out round-down for D∣2N−1, so for negative divisors that exclusion goes away. That's why the reference implementation adjusts the bounds based on the divisor's sign.
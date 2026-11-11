This post is a fun little side quest to kickstart my journey optimising *regional* calendars.

Computing the date of Easter faster is not going to matter in any real application. Even in places where it might seem to matter, like high frequency trading applications, it is probably better to just use an in-memory lookup table for holiday dates...  
However, no "Fast Date" series would be complete without some mention of this classic problem.

The rules for Easter were broadly decided at the First Council of Nicaea, organised by Emperor Constantine in 325 AD, ultimately landing on *the first Sunday after the first full moon, on or after March 21*. Later, for operational efficiency, the church defined *"full moon"* according to a formula, which was eventually modified by Pope Gregory XIII in 1582 *("Gregorian Easter")*, with the first Easter under the new rules applying in most Catholic countries the following year.  
The Church of England first observed the new date of Easter in 1753, but Eastern / Orthodox churches continue to follow the old rules.

This article is about the new "Gregorian" Easter, because it is much more complex and slow to compute. For more details on the underlying algorithm, you can see [Gauss's Algorithm on Wikipedia ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://en.wikipedia.org/wiki/Date_of_Easter#Gauss's_Easter_algorithm) *(the first known self-contained function, which basically all later algorithms build on)*.

### The Function

The code below runs really fast.  
It's around twice as fast as a standard  easter function that you might find in a typical date library, and I suspect it may be the fastest one made so far 🤷.  
Part of that speed is attributable to using **only 5 multiplications** *(whereas typical reference algorithms have 10 or more multiplications)*.

The accuracy range of around `-11m → +16m` years might seem a bit of overkill, but the reason I targeted this range is so that any date library that expresses dates via a signed or unsigned 32‑bit "rata die", is covered by this function. This means that if you decide to not clamp the logic to years after 1582, at least it will return something resembling the correct rules, rather than garbage.

1. u32 constexpr *SHIFT* = 400 * 19 * (25 * 30 * 2 - 39)
2. u64 constexpr *M19* = (1 << 32) / 19 + 1 + (11 << 32)
3. u32 constexpr *M1C* = (1 << 32) / 100 + 1
4. u32 constexpr *M25* = (1 << 32) * 8 / 25 + 1
5. u32 constexpr *M30* = (1 << 32) / 30 + 1
6. u32 constexpr *M67* = (1 << 32) * 6 / 7
7. 
8. u32 *y* = *year* + *SHIFT* // Constant fold
9. u32 *c* = (u64) *y* * *M1C* >> 32 // y / 100
10. u32 *a* = (u64) *c* * *M25* >> 32 // c * 8 / 25
11. u64 *b* = (u64) *y* * *M19* // Hi & lo bits
12. u32 *d* = (u32) *b* > 0x90000000 // (y % 19) > 10
13. u32 *e* = *b* >> 32 // Metonic cycle
14. u32 *f* = *c* - (*c* >> 2) // Julian map
15. u32 *g* = *a* - *f* + *e* // Epact
16. u32 *h* = (u64) *g* * *M30* >> 32 // g / 30
17. u32 *i* = (*g* + (*h* << 1)) & 31 // g % 30
18. u32 *j* = 31 - *i* - (*d* >= *i*) // Epact adjust
19. u32 *k* = *y* + (*y* >> 2) + *j* - *f* // Weekday input
20. u32 *m* = *k* * *M67* >> 29 // 7 - (k % 7)
21. u32 *v* = *j* + *m* + 115 // Bit prep
22. u32 ***month*** = *v* >> 5
23. u32 ***day*** = (*v* & 31) + (*v* >> 7)

1. u32 constexpr *SHIFT* = 400 * 19 * (25 * 30 * 2 - 39)
2. u64 constexpr *M19* = (1 << 32) / 19 + 1 + (11 << 32)
3. u32 constexpr *M1C* = (1 << 32) / 100 + 1
4. u32 constexpr *M25* = (1 << 32) * 8 / 25 + 1
5. u32 constexpr *M30* = (1 << 32) / 30 + 1
6. u32 constexpr *M67* = (1 << 32) * 6 / 7
7. 
8. u32 *y* = *year* + *SHIFT* // Constant fold
9. u32 *c* = (u64) *y* * *M1C* >> 32 // y / 100
10. u32 *a* = (u64) *c* * *M25* >> 32 // c * 8 / 25
11. u64 *b* = (u64) *y* * *M19* // Hi & lo bits
12. u32 *d* = (u32) *b* > 0x90000000 // (y % 19) > 10
13. u32 *e* = *b* >> 32 // Metonic cycle
14. u32 *f* = *c* - (*c* >> 2) // Julian map
15. u32 *g* = *a* - *f* + *e* // Epact
16. u32 *h* = (u64) *g* * *M30* >> 32 // g / 30
17. u32 *i* = (*g* + (*h* << 1)) & 31 // g % 30
18. u32 *j* = 31 - *i* - (*d* >= *i*) // Epact adjust
19. u32 *k* = *y* + (*y* >> 2) + *j* - *f* // Weekday input
20. u32 *m* = *k* * *M67* >> 29 // 7 - (k % 7)
21. **return** *j* + *m* - 3

Note that this function contains more terms than traditional Easter functions, but bear in mind that the compiled assembly will be a lot smaller. So if you don't care about the speed, but want a tiny impact on binary size, that could be a reason to consider this function.

The rest of this post will briefly explain the tricks used in this function:

*See also [benchmark results](https://www.benjoffe.com/fast-easter#benchmarks).*

1. u32 constexpr SHIFT = 400 * 19 * (25 * 30 * 2 - 39)

You'll notice that the very first thing we do is add a strange value `SHIFT` to the input value. This is done for two reasons:

For example, most Easter algorithms have a term like `(5 + 8 * c) / 25`, where `c` is the century (`year / 100 + 1`). The term `25` in the calculation of shift is responsible for aligning the century such that the constant `5` can be removed, resulting in `c * 8 / 25`, which is then approximated in the final algorithm with a single mul-shift: `(u64) c * M25 >> 32`.

Other terms in `SHIFT`: `19, 400, 30` are all doing similar things related to the 19-year-cycle, 400-year-cycle, and mod-30 steps.  
The term `* 2` is different. Without this term, the range of coverage would be -5,403,600 → +22,363,835; which doesn't quite cover the range we wanted, which for signed 32-bit rata die, is ±5.88m years. Including `* 2` increases the value of shift by exactly 5,700,000, which is how many years it takes for the Easter pattern to repeat, and gets the range we are after.

If you like this type of optimisation, but are not a fan of the low-level bit-shifting and so on, then you might prefer to use this function here below. It is a much more readable version of the function, which only has these higher-level optimisations applied.

Note that unlike in the main function presented earlier, `MOD 30` needs to be a positive-modulus function (even for positive dates), and that the `nextSunday` helper is anchored to the internal logic of the function, not related to Unix day-counting.

1. u32 getEpact(u32 *y*, u32 *c*, u32 *f*) {
2. u32 *n* = *y* % 19
3. u32 *i* = i32(11 * *n* - *f* + *c* * 8 / 25) MOD 30
4. **return** 31 - *i* - ((*n* > 10) >= *i*)
5. }
6. 
7. u32 nextSunday = (u32 *k*) => 7 - (*k* % 7)
8. 
9. // Returns days since March 22:
10. u32 simpleEaster(i32 *year*) {
11. u32 constexpr SHIFT = 400 * 19 * (25 * 30 * 2 - 39)
12. u32 *y* = *year* + SHIFT
13. u32 *c* = *y* / 100
14. u32 *f* = *c* - *c* / 4
15. u32 *j* = getEpact(*y*, *c*, *f*)
16. u32 *m* = nextSunday(*y* + *y* / 4 + *j* - *f*)
17. **return** *j* + *m* - 3
18. }

<small>*Note: a [variant ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://github.com/benjoffe/fast-world-calendars/blob/main/easter/algorithms/benjoffe.hpp#L101) in the C++ repo has some small optimisations not shown here (fast day-of-week and fast mod 30), and a range of [-73,803,600 .. 70,208,581].*</small>

Computing `year % 19` is a staple of Easter algorithms.  
It's related to the *Metonic cycle*, where every 19 years there are nearly exactly 235 full moons.

It is traditionally used in Easter algorithms in two ways:

We are going to compute these same things using a single multiplication.  
These steps seem unavoidable at first, but they can be eliminated. We'll begin by expanding the first one:

`(11 * (year % 19) + ... ) MOD 30`  
`(11 * (year - year / 19 * 19) + ... ) MOD 30`  
`(11 * year - year / 19 * 209 + ... ) MOD 30`  
`(11 * year + year / 19 + ... ) MOD 30`

The last step there might be the least obvious. It works because we can add any multiple of `30` to the multiplier and get the same result (a property of `MOD`), so add `30 × 7 = 210`, which means we can remove the multiplication by `209` and just invert the sign.

This leaves us with only two terms related to *year* which can be computed efficiently in parallel, however using a 64‑bit multiplier, we can actually merge these into one (fixed-point multiplication by `11 1/19`):

`u64 constexpr M19 = (1 << 32) / 19 + 1 + (11 << 32)`  
`((year * M19 >> 32) + ... ) MOD 30`

*<small>This is the only 64‑bit multiplication in the function, and a 32-bit compiler should have no trouble turning that back into the previous pair of multiplications.</small>*

The algebra above relies on `MOD 30`, which is different to `% 30` in C for negative numbers.  
The value being computed does not go negative over our range, so the substitutions remain valid.

Now on to the other term: `(year % 19) > 10`. It is a well known trick to use the low bits from the mul-shift of division by `19` as a comparison cutoff, and the version used in my function is `u32(b) > 0x90000000`. The extra term in our multiplier (`11 << 32`) has no effect in the lower 32‑bits, so this still works. Cassio Neri has written about things like this, if you want to read more you can start with this [Overload Edition 154 ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://accu.org/journals/overload/27/154/overload154.pdf).

So, this is just one multiplication plus the `MOD 30`, which is usually an additional two multiplications, but we'll eliminate those later in *[Trick #4](https://www.benjoffe.com/fast-easter#trick4)*.

There's always a `% 7` term in these Easter functions, which is then *subtracted* from a final result. This is because Easter is on the “*first Sunday after [...]*”.

Clearly we are going to use the fast-mod-7 trick from the [weekday article](https://www.benjoffe.com/fast-day-of-week). If you haven't read that article, you should. You won't understand this section otherwise, and frankly, it's a better article than this one.

1. u32 const *M67* = (1 << 32) * 6 / 7
2. u32 *y* = *x* * *M67* >> 29

The same mod-7 trick as before, but notice that the mapping is reversed? (The numbers track anti-clockwise)

So why not just subtract the result of `% 7` like everybody else? Well, that would make the final line be: `j - m + C` (for some constant `C`). This does not fit the pattern of a single-operation `LEA` instruction on x86.

Instead, we adapt the fast-mod-7 code to use a fixed-point multiplier of `6 / 7` (rather than `1 / 7`) before the right-shift-29, which means this line actually counts mod-7 backwards for us! This means the final line can be `j + m + C`, which fits `LEA` and saves... one cycle  😀 <small>*(depending on the compiler and CPU...)*.</small>

1. u32 constexpr *M30* = (1 << 32) / 30 + 1 ···
2. u32 *h* = (u64) *g* * *M30* >> 32
3. u32 *i* = (*g* + (*h* << 1)) & 31

This one is pretty obvious if you've been following this blog series.  
`MOD 30` can be calculated faster by using our favourite identity:

This was introduced and proven in the [weekday](https://www.benjoffe.com/fast-day-of-week) article, and utilised more notably in the [time-of-day](https://www.benjoffe.com/fast-time-of-day) article.  
Here setting `D = 30, c = 2` gives us the useful version where we can apply `MOD 32` *(same as `& 31`)*.

This final bit, I'm not sure if it's been done before exactly like this.

Easter can only ever be in March or April (month 3 or 4), and luckily March is 31 days long, which means we can use `% 32` to truncate dates there. A straightforward modulus would cause March 32 to overflow to April `0`, a non-existent date, so we add the term `v >> 7` which increments the date when it overflows *(a lucky coincidence relying on April, month `4`, being a power-of-2)*.

I have seen similar things done before using `% 31`, but I have not seen this with the clean bit-mask approach.

So, that's it. A bunch of fussing about to make a simple streamlined function that is next to impossible to read... but fast.

This article was prompted by Twitter/X user [Dirk Loss ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://x.com/dloss/status/2090496142173692232) replying to one of my posts with a link to a ChatGPT thread, where he used AI to compute Easter faster. [See ChatGPT thread. ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://chatgpt.com/share/6a873ce2-6d24-83eb-9fbe-1e4a1fd46c9f)

The AI actually did a pretty good job.  It used learnings from my prior blog posts to apply various optimisations, but also came up with new twists on these ideas. It produced a function that is *really fast*, and that is accurate over the range 1498–14,544. The range is a fairly reasonable choice given that the modern rules for Easter took effect after 1582, and nobody really needs Easter further into the future.

In a serious case of *"Not Invented Here"* syndrome <small>(on behalf of human kind)</small>, I had to see if I could beat the AI. I clearly did, otherwise there wouldn't be this blog post. The wider-range algorithm presented in this article has around 5-15% higher throughput across tested platforms, and similar latency (despite the wider range).

My algorithm was adapted from the one presented in Calendrical Calculations (Reingold and Dershowitz).  
I did not apply any learnings from the ChatGPT one, though we settled on several similar steps.

I suspect this function could be optimised more, as it still has the same overarching structure of existing algorithms going back a *very* long time.  
I tried for a little while to find a shortcut solution using the Python "Z3 Theorem Prover", which found an alternative which is a further 15-20% faster than my main one, however it's only accurate over a micro range [1894 .. 2199]. [It is available in the testcase repo ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://github.com/benjoffe/fast-world-calendars/blob/main/easter/algorithms/benjoffe.hpp#L115). If you can find a function of similar or faster speed with a wider range, feel free to let me know and I will update the repo and this page!

Although I beat the AI in this case, it’s a pretty mild victory as it was just a basic model with a moderate amount of compute. It’s sad to know that if frontier models were pointed at the problems I’ve been tackling in this blog series, they would probably unearth every last jewel of optimisation left in the blink of an eye. I hope that I have time to explore this space more before it becomes barren.

If you enjoyed this post, you should [follow me on X ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://x.com/benjoffe) to get notified when I publish more date and algorithm related articles.

Exhaustive tests of the ranges asserted in this article can be verified via the testcase code: [https://github.com/benjoffe/fast-world-calendars  ![](https://www.benjoffe.com/static/media/link-external.f2d3f5e2e0517a859106527b07648224.svg)](https://github.com/benjoffe/fast-world-calendars).

The same repository is used for benchmarking, where a large set of random years are loaded into memory and tested.

All results were obtained by running the benchmark with `-repeat=10` and recording the *median* results.  
The `-batch` flag runs each computation 3 times before loading the next entry from memory. This ensures that the processor is not bottlenecked by memory access.  
Latency results use the same command but replace the batch flag with `-latency`. This mode feeds the result of each computation into the next, so there is no parallelisation.

```
git clone https://github.com/benjoffe/fast-world-calendars.git
cd fast-world-calendars
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
./build/bin/easter_test
./build/bin/easter_bench -batch
./build/bin/easter_bench -latency
```

The number in a small font size represents the number of nanoseconds per year computation.  
The larger number is the ratio of these results compared to the `New` function as a baseline.

**Note:** the benchmarks compute *"Days since 22 March"* (not day and month), as some of the reference algorithms only return this value.  
If my optimisation of the day/month step is novel, then the speedup would be larger than presented here.
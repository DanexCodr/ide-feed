A friend recently pointed out a new Word Ladder game variant:
Find a path of mutations from a start word to an end word,
where mutations can be single letter changes, single letter
deletions or additions, or anagramming the word. It annoyed me
(the paths involving anagrams can be wickedly hard to spot),
so, naturally, I wrote a solver for it. And when the solver
took over a second to run, I of course had to optimize it. Along the way, I
found a fun trick for anagram indexing—fitting a collision-free
prime-product identifier for every word in the dictionary into a
single 64-bit integer—that I hadn't seen before (though the history
of computing is long and Knuth probably noticed it in 1965).

For completeness, I should note that what I was interested in
was finding all anagrams in a dictionary---if you just want
to find anagrams of a specific word you can probably get away
with a much simpler hash table design! We'll use all of the
anagrams in the next post talking about solving the whole word
ladder.

## Finding anagrams

The two usual tricks for finding anagrams are to use
either a letter-sorted permutation or a letter-count vector
as a
unique identifier for the letters in the word in an
order-independent way:

```
letter_sort("spot") -> "opst"
```

or

```
letter_count("spot") -> "[... o:1, p: 1, s: 1, t:1 ...]"
```

and then run through the dictionary and insert items
into a hash table based upon their letter count. In python-ish pseudocode:

which creates a table with entries like:

```
"opst" : ["spot", "post", "tops", "stop"]
```

### Baseline: Sorting strings

Because I'd been feeling a little, uh, rusty in my coding lately, I
decided to implement this all myself in Rust instead of yelling at an LLM
to do it (this is a leetcode-like problem so it would have done it trivially).
That code looked like:

Using the Scrabble(tm) dictionary pre-read into memory, this function
produces the anagram dictionary in:

**Result: 31ms (173ns / word)**

That seems fine. Oh wait, just kidding, that's INSANELY SLOW. The
dictionary has 178,690 entries in it, which means we're spending 173
nanoseconds per word to build up this dictionary. In 173 nanoseconds
you could execute roughly 4400 instructions on my Macbook Pro M1.
Who has time to wait for that??

### Eliminating `Vec` allocations

When optimizing, one of the first places to be suspicious is
allocations, and this one has them in droves. Every word results
in either the allocation of a Vec or an append to a Vec, which
sometimes needs an allocation. Practically, there are about
161019 keys in the table, so that's 161k allocations (!!).
Let's improve those by using a slightly more clever data structure,
noting two things:

- With 161k entries in the hash table and only 178k dictionary items, most of those hash table entries will be singletons.
- We have the original word list stored in memory and it can be indexed by a u32 given its size.

So we'll do two things: We'll find a way to store singleton
items without needing a dynamic-length data structure at all,
and we'll implement the equivalent of a linked list for appending
items to the lists, since they're append-only and we only scan them
once at the end. To do this, we'll use a structure like this:

Where heads is indexed by the anagram-identifying-key (e.g.,
the character-sorted string). We'll overload that u32 by
using the high bit (we only have 170k or so words) to let
it represent
*either* an actual data value (the index of
an element in the list) OR an index into the next+word arrays.
The next array is our linked list - it stores pointers to
another entry in the next array. The word array stores the
associated data. It looks like this:

**Result: 31ms -> 20ms (112ns / word)**

### Packing letter counts into a `u128`

Much better, but we can do better yet. The time to sort
that string and create a new string allocation is non-trivial
and we're doing 178k of them. That's going to be another
big chunk of nanoseconds.

Let's try a letter count vector instead, and pack it tightly into an integer.
With only 26 characters, if we assume that no word has more than 15
repetitions of the same character, we could use 4 bits per character
for 26 x 4=104 bits. That fits comfortably in a u128, and while
that's not tiny, it's at least a nice fixed size 16 byte thing
we can use as a fast hash table key.

(Note that we've done something else here - we're only returning
the list of anagrams, not a full dictionary containing all of the
words that don't have anagrams.)

Avoiding the string manipulation and sorting gives a big win:

**Result: 20ms -> 5.6ms (31ns / word)**

### A faster hash table

At this point, we might ask a question like "how much does
the slow default Rust hash table cost us?"

So we'll switch to the [`rustc_hash`](https://crates.io/crates/rustc-hash) `FxHashMap`, which is much faster
if you don't have to worry about adversarial inputs to your hash table.

**Result: 5.6ms -> 4.1ms (23ns / word)**

That seems much better. But are we done yet?

### 64-bit Gödel numbering with tuned primes

Of course we're not done!

Storing the letter count as a u128 is also a little slower
than necessary, because it'll be split across two 64 bit
registers and requires the compiler to carry that addition
across them and do twice as much work for equality testing.
But if we tried lettercounting in 64 bits, we would only be
able to store 2 bits, and many words have more than 3 of
the same letter ("MISSISSIPPI", for example, already has 4 S's).

Instead, we'll use an approach based on
[Gödel numbering](https://en.wikipedia.org/wiki/G%C3%B6del_numbering):
we'll create a small
table associating one distinct prime number with each letter, and identify
each word by the product of the letter-primes. This guarantees a
unique identifier for each mix of letters. Naively, one might
assign "a -> 2, b -> 3, c -> 5" and so on. But this is a practical
blog post, and we'd like to fit the result in 64 bits; if
we use the naive assignment, we overflow at the 365th word in our
dictionary, "ABORTIVENESSES". And that's only 14 characters long,
we have 3157 15-character words as well!
If we let it wrap,
we'll have just implemented a hash function, and there's no guarantee
that two words won't accidentally collide, so then we'd need to add
some machinery to check that...

So here's the trick: Find an optimized assignment of primes to
letters in the alphabet such that none of the words in our
Scrabble dictionary overflow a 64 bit number. I started out
thinking about the standard English letter frequency
(ETAOINSHRDLU, etc.), but that turns out to be a little
wrong: We don't care much about words like "the", we care about
words like "WRONGHEADEDNESS". So instead, we need to go
based on the patterns found in the 3157 15-character words. In particular,
while "E" remains assigned to 2, the common "T" is assigned 29,
and we use 3 for "I". Our friend "J" is assigned 101, since
the longest word with two or more J's in it is only 12 characters
long: JEJUNENESSES. Looking at that, those E's and N's and S's better
have low values, and they do: 2, 19, 17. We could handle 15 N's in
a row in 64 bits still.

To solve this, I had a small program start with the letter-frequency
ordering (which does a lot better than alphabetical but isn't good enough),
loop finding the first word that overflowed and switch out some of its primes
for lower valued primes. This would have also been fun to throw at a
solver.

which doesn't overflow for any word in the Scrabble dictionary.
We've found a collision-free canonical 64-bit identifier for the bag of letters in a
(Scrabble) word, which looks like this in code:

In this representation, the largest product word is

```
PSYCHOPATHOLOGY = 17763551150644031915
```

which in log2 is 63.945; it's about 96.2% of the way through the 64 bit
number space. Close, but it fits.

**Result: 4.1ms -> 2.6ms (14.7ns / word — 12x faster than baseline)**

### Using a u128 packed word representation

And then there's a final optimization you can do: Instead of reading
the dictionary into strings, read them into a packed u128 representation
using 5 bits per character, and then add some instruction-level parallelism
for our CPU (ILP) by doing the product accumulation using two independent
accumulators. This u128 representation is useful for speeding up other
parts of the word ladder solver later. That code looks like this:

**Result: 2.6ms -> 2.3ms (13 ns/word - 13x faster than baseline)**

### Low-level optimizations: branches and auto-vectorization

This is looking pretty good. The only last optimization I have to add
is to address some branch mispredictions in that rest != 0 loop. We
can instead just treat all words as if they're 16 characters long and
ignore the 0's at the end by mapping them to 1 in our primes table
(i.e., they have no effect on the product). Using a fixed length of 16
also permits more auto-vectorization by our friendly compiler.
To support that, we also separate the computation of the prime product
from the insertion into the hash table, allowing more ILP from our
now-vectorized multiplication loop.

That code ends up looking like this:

**Result: 2.3 ms -> 1.96ms (10.9ns/word, 15x faster than baseline)**

We're finally pretty close to what I think a single core on my machine
can get without explicit vectorization. That 1.96ms is about 1.23ns per
byte, which could theoretically be about 3.2 x 8 x 1.23 = 31 instructions
(but realistically fewer), which doesn't leave a *ton* of
room for optimization---though I could be wrong! There's some space
in there for an even faster hash table implementation but I'd rather
stick with common, off-the-shelf things there.

### Summary of optimizations

| Step | Optimization | Total Time | Time / Word | Speedup vs. Baseline |
| --- | --- | --- | --- | --- |
| 0 | Baseline (`HashMap<String, Vec<String>>`, sorted string keys) | 31.0 ms | 173 ns | 1.0x |
| 1 | `KeyGroups` flat arrays & inline singletons | 20.0 ms | 112 ns | 1.6x |
| 2 | 4-bit letter counts packed into `u128` | 5.6 ms | 31 ns | 5.5x |
| 3 | Switch to `rustc_hash::FxHashMap` | 4.1 ms | 23 ns | 7.6x |
| 4 | 64-bit Gödel numbering (corpus-tuned prime products) | 2.6 ms | 14.7 ns | 11.9x |
| 5 | 5-bit packed `u128` input words + dual-accumulator ILP | 2.3 ms | 13.0 ns | 13.5x |
| 6 | Branchless fixed-length loop + auto-vectorized product pass | **1.96 ms** | **10.9 ns** | **15.8x** |

In the next post I'll show how we solve the entire word ladder problem,
using the anagrams we've found as a part of it.
Are generative (randomized) tests significantly more effective than example-based
unit-tests at discovering bugs? There’s
[an interesting discussion about this on lobste.rs](https://lobste.rs/s/mkv2pl/unit_tests_mark_territory_more_than#c_5nimhl).
One argument in favor of unit tests is, paraphrasing

To me, it seems that generative testing should shake out that particular
creature, so I wrote [a lil fuzzer](https://github.com/matklad/regex-fuzz)
of my own, and it indeed discovered *another* bug in that version of `regex`,
and then the one I was after. I didn’t find anything in the latest version. I
like to do a write up about the process, as it is a good case study for how one
approaches a problem like this.

I want to be extra clear that my argument is very weak here, as I know exactly
the bug I am after, and I even know that fuzzers can find it. My primary goal is
to teach you the techniques, leaving it to your judgment just how effective they
are. That being said, I think finding a *second* bug validates the approach
somewhat.

I also want to emphasize that writing fuzzers to find known bugs is far from an
idle amusement. While I believe that generative testing is very powerful,
relative to its cost, it’s always a question whether a particular test is
thorough enough. And it never is, you *will* find more bugs elsewhere (that’s
why defense in depth and *runtime* mitigations are critical). And, whenever you
have a pest that dodged your fuzzers, your first order of business is to treat
this event as a bug in the *fuzzer*, and change it so that it can find this and
related bugs. Only then you are allowed to add a fix and a unit test!

## [The Bug](https://matklad.github.io/2026/09/19/finding-bugs.html#The-Bug)

For `".abb|b"` regex and `"zabb"` input, an older version of `regex` crate
returned `b` as the first match, which is incorrect, because the entire `zabb`
matches:

How do we find this, or something *like* this?

Regular expression engines are one of the easiest things to apply generative
testing to, they are pure algorithms. While few large systems are *just* an
algorithm, algorithms are everywhere inside components of interesting systems,
so this is a hands-on knowledge.

And by far the most important technique for testing algorithms is to compare
with the known right answer, with an oracle. Implement both `O(N log N)` and
`O(N^2)` versions of the algorithm, and match the answers.

To be fair, the original comment mentioned that the their fuzzer didn’t find the
issue because they didn’t have access to an oracle. However, if you are
designing a reliable system, it’s part of your job to ensure it has an oracle!
One of the first things we did for our
[Jepsen test](https://jepsen.io/analyses/tigerbeetle-0.16.11) at TigerBeetle was to
[expose internal timestamps](https://github.com/tigerbeetle/tigerbeetle/pull/2481)
via API, to make it easier for Jepsen to find bugs (TigerBeetle is
[co-designed](https://tigerbeetle.com/blog/2026-08-20-protocol-aware-dst/) with
its internal simulator
[VOPR](https://github.com/tigerbeetle/tigerbeetle/blob/47aeb2212a255273dda508288412e537d11e4b7c/docs/internals/vopr.md)
which naturally has access to timestamps and anything else). And for, a regex
engine, coming up with an oracle shouldn’t be hard, as they typically already
come with multiple specialized implementations under a single facade, and the
implementations can be cross-checked against each other.

But the `regex` case is even simpler (which makes it an excellent case study).
There’s `regex_lite` crate that provides the same API.

So here’s a plan: generate a regular expression, an input text, and check that
`regex` and `regex_lite` give identical answers.

## [Generating a String](https://matklad.github.io/2026/09/19/finding-bugs.html#Generating-a-String)

I’ll start with code that generates a random string, as it is simpler, but still
shows some non-trivial ideas. First, we’ll need a random number generator:

There are fancier techniques, which can give you
[test-case minimization](https://matklad.github.io/2026/04/20/test-case-minimization.html),
[exhaustive search](https://matklad.github.io/2021/11/07/generate-all-the-things.html), or
[coverage guided exploration](https://llvm.org/docs/LibFuzzer.html), but the
insight is that even a humble PRNG is brutally effective, if you put it to good use.

When you start with randomized testing, the instinct is to generate something
big, no, HUGE! Surely regex will choke on 5 GiBs of input? This is usually a
wrong call. Bugs *usually* involve small, but tricky examples, weaponizing
interactions between a few features. A string where all characters are the same
is more likely to trigger a bug than a purely random string where every
character is unique.

So my default approach to generating strings is this. *First*, I fix the
alphabet of possible characters. A nice way to get one is to `sort | unique` all
the unit tests. Then, for each particular string, I pick a *subset* of that
alphabet. I want strings that use all the characters, but I also want long
strings with only `a` and `b`! Then I generate a string using the given subset
of the alphabet, where the length of the string is also picked at random.

To make fuzzing efficient, I want to keep each iteration as fast as possible, so
I make sure to re-use the memory across iterations,
[static allocation](https://github.com/tigerbeetle/tigerbeetle/blob/47aeb2212a255273dda508288412e537d11e4b7c/docs/ARCHITECTURE.md#static-memory-allocation)
in the small:

There’s a nice way to think about this two step process, generating alphabet
first, and then generating a string. To generate a string, you need a
distribution of characters. You *can* use the same distribution for each of the
million iterations. But an easy way to spice things up is to make the
distribution *itself* random. I file this “randomize distributions themselves” idea under
[swarm testing](https://tigerbeetle.com/blog/2025-04-23-swarm-testing-data-structures/).

## [Generating a Regex Distribution](https://matklad.github.io/2026/09/19/finding-bugs.html#Generating-a-Regex-Distribution)

Let’s apply the same tricks when generating a regex:

- pick a subset of active regex features,
- pick size at random,
- re-use memory.

Let’s start with the first one:

Regexes have alternation `r1|r2`, repetition `r*`, wildcard `.`, and literals
`a`. Rather then binary enabling or disabling a particular feature, I assign
each feature a weight between 0 and 100, which is a bit more general. The `sum`
is the total of all weights. To select a feature at random, we need to generate
a number in `0..sum` and find which segment it falls into.

In anything more serious, I’d introduce explicit types for probabilities and
distributions, but just a two-digit number is perfectly serviceable in the
small.

This is how I generate `ReOptions`, making sure that literals always have
non-zero weight, and also selecting an alphabet for them:

## [Generating a Regex](https://matklad.github.io/2026/09/19/finding-bugs.html#Generating-a-Regex)

So now we can generate a regular expression. This is convenient to do
recursively. To avoid allocations, an output buffer is passed through. To
control regex length, a `size` parameter is also threaded, and “branching”
recursive invocations divide the `size` between the children:

## [Search Loop](https://matklad.github.io/2026/09/19/finding-bugs.html#Search-Loop)

Given that compiling regular expressions is somewhat slow, it seems like a good
idea to try multiple strings for the same pair of regular expressions, which
gives the following code:

It produces examples similar to those in the issue, with a common suffix:

but also examples which somewhat different, without the shared suffix:

All together:

Takeaways:

- Fuzzing against an oracle is effective, which is a strong motivation to build an oracle!
- Go for small, tricky examples, rather than large uniform ones.
- Real fuzzers are cool, but, if you know something, even xoroshiro can be dangerous.
- Black box testing is cool, but co-designing system and its testing harness is a point of leverage (build an oracle!).
- This stuff is not rocket science, you don’t need a Haskell PhD to apply these ideas.
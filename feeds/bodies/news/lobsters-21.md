At [Goatmire Elixir](https://goatmire.com/talk/millions-of-packets-zero-panic-observability-without-killing-the-patient) this year, I gave a talk about observing a name server that handles millions of packets. Performance came up as a guilty pleasure of mine, and I hinted at some numbers. Afterwards, in the corridors, attendees kept asking the same question: what did you actually do to bring average CPU down so much? This post is the long answer for one big piece of that work: making our DNS library cheaper to run.

First, some context on where this code runs. DNSimple's managed [DNS hosting](https://dnsimple.com/products/dns-hosting) has two layers. Queries for your domains first reach our [cache edge](https://blog.dnsimple.com/2026/08/building-our-fully-independent-dns-edge/), a global anycast network we build and operate ourselves, which answers whatever it already has cached. Everything else goes to the origin: the authoritative [name servers](https://support.dnsimple.com/articles/dnsimple-nameservers/) that hold every zone and build every answer. The origin runs [`erldns`](https://github.com/dnsimple/erldns), our open-source DNS server written in Erlang, and since it does the real work behind every cache miss, every query it answers has to be as cheap as possible.

Like many other protocols (HTTP for example), DNS is a request-response system where payloads need to be encoded and decoded as they travel through the wire. So just like a JSON parser is hot code in a JSON API, a DNS parser is hot code for us: every DNS query that reaches a DNSimple nameserver goes through [`dns_erlang`](https://github.com/dnsimple/dns_erlang) twice: once to decode the request, and once to encode the response. At a few queries per second, nobody cares how long that takes, but as queries per second scale, under attack, every nanosecond spent turning bytes into terms and back is a nanosecond not spent answering the next query.

So over the last several months we've rewritten most of the hot paths of `dns_erlang`, the open-source DNS library that powers `erldns` and our authoritative name servers. The result: on a production-shaped workload, our nameserver now spends **12% less CPU per query** and serves **14% more queries per second** before saturating, from library changes alone.

None of it required NIFs, C, or exotic tooling. It came from understanding how the BEAM handles binaries, and writing code that the compiler and the JIT can turn into something fast. If you write Elixir or Erlang, and especially if you parse or produce binary protocols, these patterns apply to your code too. Many of them are not well known, even among experienced Elixir developers, so let's dive into it.

## BEAM binaries in five minutes

Before looking at the optimisations, we need a mental model of what a binary is on the BEAM. The [Erlang efficiency guide](https://www.erlang.org/doc/system/binaryhandling.html) has the full details; here is the short version.

**Everything is immutable, at least in principle.** On the BEAM, data never changes once it's created: "updating" a tuple, a map or a binary produces a new one, and anyone holding the old one still sees it unchanged. That's a big part of what makes processes and concurrency so easy to reason about, but taken literally it would mean copying on every change. In practice the compiler, the JIT and the runtime cheat whenever they can prove that nobody could notice, that is, when the semantics of the language can be respected: they reuse memory, write in place, or skip the copy entirely. Most of the tricks in this post are about writing code that makes that proof easy.

**Slicing and matching are cheap.** Binaries up to 64 bytes live on the process heap, and bigger ones live outside any process, shared by reference. Matching `<<Header:12/binary, Rest/binary>>` copies nothing: `Rest` is a *sub-binary*, a small term pointing into the original. Better still, when a function recursively matches the rest of a binary, the compiler keeps a *match context*, a cursor that walks the bytes, and only materialises a sub-binary if you let `Rest` escape, for example by returning it or storing it in a tuple.

**Appending can be (almost) free too.** This is the one that surprises people. Consider:

```
loop(<<C, Rest/binary>>, Acc) -> loop(Rest, <<Acc/binary, C>>);
loop(<<>>, Acc) -> Acc.
```

Naively, each iteration copies `Acc` into a new, one-byte-longer binary, making the loop quadratic. It doesn't, because the runtime can prove that `Acc` came from an append and nobody else is looking at it, so writing in place can't break immutability for anyone. The first append allocates spare capacity, and later appends write into it:

```
<<Acc/binary, C>> on a binary only this loop holds

  +---------------------------+-----------------------+
  |  bytes written so far     |   spare capacity      |
  +---------------------------+-----------------------+
                              ^ next append writes here, no copy
```

So an append-only accumulator costs amortised O(1) per append, like pushing onto a `std::vector` in C++. The catch: if the binary escapes, if you build pieces separately and glue them together, or if you append the *accumulator* onto something else, you're back to copying.

**Integers have a size limit you can feel.** To know each term's type at runtime, the BEAM tags it: a few low bits of every word say what the term is. On a 64-bit BEAM a small integer's tag takes 4 bits, so integers that fit in the remaining 60 (59 bits of magnitude plus a sign) are *small integers*: immediate values that never touch the heap. Anything larger becomes a *bignum*, allocated on the heap. This will matter a lot when we get to SWAR.

**Work is counted in reductions.** The scheduler gives each process a budget of reductions (roughly, function calls) before switching to another, so fewer reductions for the same work means more throughput.

Tip

You can ask the compiler where binary optimisations apply, and where they don't. Compile with `erlc +bin_opt_info`, or `ERL_COMPILER_OPTIONS=bin_opt_info mix compile --force` in Elixir, and it will report every match context it keeps and every place it has to give one up.

Every number below comes from [Benchee](https://github.com/bencheeorg/benchee) on two very different machines (an Apple M4 Pro and an AMD Ryzen 9 9950X3D), on OTP 29 with the JIT, measuring time, memory and reductions. Every change also went through a *parity harness* proving the new code byte-for-byte identical to the old, down to the errors raised on malformed input: 26,434 cases for name decoding alone. And we kept the experiments that lost, with their numbers; we'll get to them.

## Pattern 1: one accumulator, appended all the way

Encoding a DNS response means writing a header, the question, and then every record in the answer, authority and additional sections. The old encoder built each section as its own binary and then copied it onto the message. Each record's data (its RDATA) was also built as a separate binary, measured to write its length, and copied in.

Each of those intermediate binaries is allocated, filled, copied and thrown away. The append optimisation can't help, because we keep starting new binaries instead of extending one.

In [#100](https://github.com/dnsimple/dns_erlang/pull/100) and [#139](https://github.com/dnsimple/dns_erlang/pull/139) we turned the whole encoder around: a single accumulator flows through every section, and each record appends itself straight onto it. Even the RDATA length is computed from the parts and written in the same append as the data:

```
%% Before: the RDATA is built on its own, measured, then copied in.
encode_rr(Acc, RR) ->
    Data = encode_rrdata(RR),
    <<Acc/binary, (byte_size(Data)):16, Data/binary>>.

%% After: the length and the data go onto the message in one append.
encode_mx(Acc, Pref, Exchange) ->
    <<Acc/binary, (2 + byte_size(Exchange)):16, Pref:16, Exchange/binary>>.
```

There was one more wrinkle. A DNS message starts with a 12-byte header whose counters (how many answers, how many authority records, and so on) we only know at the end. So the accumulator starts with 12 zero bytes as a placeholder. Every section is appended after it, and because the placeholder is already there, the accumulator's size is always the current position in the final message, which is exactly what name compression pointers need. When the message is complete, the real header is built and placed in front of the body, in the only copy of the body the whole encoding makes.

On the UDP response path, measured on the M4 Pro, a simple response went from 708 ns to 583 ns and from 1.89 KB to 1.23 KB allocated, and a typical DNSSEC response from 1.33 µs to 1.13 µs.

## Pattern 2: stay in the match context

Decoding has the mirror-image problem: it's easy to accidentally force the BEAM to materialise terms it never needed.

A good example is TXT records, which carry a list of length-prefixed strings. The old code delegated each string to a helper that returned a `{Rest, String}` tuple. That's one tuple allocation per string, and because `Rest` escapes inside the tuple, the compiler must create a real sub-binary for it. In [#135](https://github.com/dnsimple/dns_erlang/pull/135) we match the string directly in the loop's head, so the match context survives:

```
%% Before: a helper returns a tuple, and Rest escapes inside it.
decode_text(<<>>) ->
    [];
decode_text(Bin) ->
    {Rest, Str} = decode_string(Bin),
    [Str | decode_text(Rest)].

decode_string(<<Len, Str:Len/binary, Rest/binary>>) ->
    {Rest, Str}.

%% After: match the string in the loop's own head.
decode_text(<<Len, Str:Len/binary, Rest/binary>>) ->
    [Str | decode_text(Rest)];
decode_text(<<>>) ->
    [].
```

The same pull request found a less obvious copy: the decoder stored each section into the `#dns_message{}` record as soon as it was decoded. Records are immutable tuples, so every update copies the whole thing, and this record is 19 words. Updating it four times per message (questions, answers, authority, additional) meant four copies. Passing the sections along as function arguments and building the record once at the end cut 11% of the reductions and 10% of the allocation for decoding a query, which is exactly what every incoming packet goes through.

## Pattern 3: match in big chunks, and read the assembly

Domain names are case-insensitive, so `dns_erlang` lowercases them a lot. The old `to_lower/1` used binary comprehensions over 8, 7, 6, … 2-byte chunks, picking the largest chunk size that evenly divided the input:

```
to_lower_chunk(Data) when byte_size(Data) rem 8 =:= 0 -> ...;
to_lower_chunk(Data) when byte_size(Data) rem 7 =:= 0 -> ...;
to_lower_chunk(Data) when byte_size(Data) rem 6 =:= 0 -> ...;
%% ... down to rem 2, then one byte at a time
```

It looks reasonable. Then we looked at what the JIT actually generates for it. On x86-64, `rem 8`, `rem 4` and `rem 2` compile to cheap bit masks, but `rem 7`, `rem 6`, `rem 5` and `rem 3` each compile to an `idiv` instruction, which costs somewhere between 20 and 90 cycles. A name whose length isn't a multiple of 8 (most of them) paid for up to four divisions just to choose a strategy, and a prime length paid for all four and then went byte by byte anyway.

The rewrite in [#114](https://github.com/dnsimple/dns_erlang/pull/114) uses plain function clauses that match large chunks first and fall back to smaller ones. A clause like `<<B0, ..., B7, Rest/binary>>` compiles to a single size comparison, with no division anywhere:

```
lower(<<A, B, C, D, E, F, G, H, Rest/binary>>, Acc) ->
    lower(Rest, <<Acc/binary, (l(A)), (l(B)), (l(C)), (l(D)),
                              (l(E)), (l(F)), (l(G)), (l(H))>>);
lower(<<A, Rest/binary>>, Acc) ->
    lower(Rest, <<Acc/binary, (l(A))>>);
lower(<<>>, Acc) ->
    Acc.
```

Funnily enough, this wasn't the first time that dispatch had shipped. Years ago I contributed the very same trick to OTP's hex encoding in [erlang/otp#4690](https://github.com/erlang/otp/pull/4690), where it made `binary:encode_hex/1` two to three times faster than the [original implementation](https://github.com/erlang/otp/pull/3014). It survived the addition of `binary:encode_hex/2` in [erlang/otp#6297](https://github.com/erlang/otp/pull/6297), until Björn Gustavsson replaced it in [erlang/otp#6869](https://github.com/erlang/otp/pull/6869): a size not divisible by anything from 2 to 7 took about three times longer than the best case, so the new code encodes the largest multiple of 8 bytes in one comprehension and finishes the last few bytes one at a time. The same pull request made `binary:decode_hex/1` almost ten times faster. In other words, the OTP team had already found and fixed this exact pattern in my own code, three years before I found it again in dns_erlang.

The lesson isn't really about `rem`. It's that the BEAM JIT is now good enough that the generated machine code is worth reading. Start Erlang with `+JDdump true` (or `ERL_FLAGS="+JDdump true"` for Elixir) and it writes the assembly of every loaded module to disk. Ten minutes in those files can explain a benchmark that hours of guessing can't.

## Pattern 4: SWAR, from a blog post to OTP, Elixir and our nameserver

This one started with Daniel Lemire's post on [detecting special characters with SWAR](https://lemire.me/blog/2025/04/13/detect-control-characters-quotes-and-backslashes-efficiently-using-swar/), and a simple question: can we do that on the BEAM?

SWAR stands for *SIMD Within A Register*. Instead of looking at bytes one at a time, you load several bytes into one integer and use ordinary arithmetic and bitwise operations to test all of them at once. The classic trick answers "does this word contain a zero byte?" without looking at any byte individually:

```
has_zero(V) = (V - 0x0101...01) band (bnot V) band 0x8080...80
```

Subtracting 1 from each byte only borrows into a byte's high bit when that byte was zero, so the result is non-zero exactly when some byte of `V` is zero. To ask whether a word contains a *specific* byte, say `.`, XOR the word with that byte repeated in every lane first: matching bytes become zero.

On most platforms you'd use a 64-bit word. On the BEAM that would be a mistake, because a 64-bit value doesn't fit in a small integer: the arithmetic would allocate bignums on the heap, and the JIT can't emit plain machine instructions for it. The largest whole number of bytes that fits is 7, so we use **56-bit words**. All the intermediate values stay small integers, and every `band`, `bxor`, `+` and `-` compiles to a bare instruction with no type checks.

Best of all, the whole test is legal in a guard. Here's how `dns_erlang` escapes a label while decoding a name: seven bytes at a time when they contain neither `.` nor `\`, byte by byte only around the ones that need escaping.

```
-define(ONES, 16#01010101010101).
-define(HIGHS, 16#80808080808080).
-define(HAS_ZERO(V), ((((V) - ?ONES) band bnot (V)) band ?HIGHS)).
-define(CLEAN(W),
    (0 =:= (?HAS_ZERO((W) bxor (?ONES * $.)) bor ?HAS_ZERO((W) bxor (?ONES * $\\))))).

escape_label(<<W:56, Rest/binary>>, Acc) when ?CLEAN(W) ->
    escape_label(Rest, <<Acc/binary, W:56>>);
escape_label(<<$., Rest/binary>>, Acc) ->
    escape_label(Rest, <<Acc/binary, "\\.">>);
escape_label(<<$\\, Rest/binary>>, Acc) ->
    escape_label(Rest, <<Acc/binary, "\\\\">>);
escape_label(<<C, Rest/binary>>, Acc) ->
    escape_label(Rest, <<Acc/binary, C>>);
escape_label(<<>>, Acc) ->
    Acc.
```

In Elixir, `defguardp` plays the role of those macros, so the same guard reads just as naturally there.

Notice how all the previous patterns are in there too: the label is only ever matched, so it stays a match context; the output is a single append-only accumulator; and the clauses go from the biggest chunk to the smallest.

The same idea makes case conversion branch-free. With a couple more subtractions you can find every byte between `A` and `Z` in the word, and flip their `0x20` bit in one go. That's how `to_lower/1`, `to_upper/1` and the case-insensitive comparisons in `dns_erlang` work today ([#124](https://github.com/dnsimple/dns_erlang/pull/124)).

The fun part is that this didn't stay in our library. The same week it landed in `dns_erlang`, we took the trick upstream, to Erlang/OTP and Elixir themselves:

- erlang/otp#10938 applies it to the json module's string scanning. The JIT output for the hot loop shrank from about 1,750 lines of assembly to about 100, and 768 jump-table entries disappeared. Benchmarks borrowed from Jason improved by 3% to 55%.
- erlang/otp#10948 brings it to the string module, making string:length/1 and string:slice/3 up to twice as fast on ASCII input.
- elixir-lang/elixir#15255 does the same for Elixir's String.length/1 and String.slice/3: String.length/1 got 2 to 5 times faster on ASCII strings.

All three shipped in OTP 29 and Elixir 1.20. If you're on those versions, you're already running this code.

And then the community ran with it. Over the following months, other people brought SWAR to more corners of the ecosystem:

- elixir-lang/elixir#15357 applies it to the validation functions in Elixir's Base module, making Base.valid16?/2 and Base.valid32?/2 about 25% faster.
- elixir-plug/plug#1311 adds a 56-bit SWAR guard to the ASCII fast path of Plug's UTF-8 validation.
- elixir-mint/mint#513 rewrites Mint's HTTP/1 header parser to read 7 bytes at a time, using SWAR to find the colon and the end of the line while validating the bytes.
- erlang/otp#11473, José Valim's proposal to support byte ranges directly in binary patterns, measures itself against SWAR guards.

It's a nice reminder of how an idea travels in an open ecosystem: from a blog post about C, to a DNS library, to the standard libraries, and from there to code that most Elixir applications run on every request.

## Pattern 5: pick keys the VM can compare cheaply

DNS has its own compression scheme: when a name, or the tail of a name, already appears earlier in the message, you write a 2-byte pointer to it instead of the name. The encoder keeps a map from every name suffix it has written to its position in the message.

The old map was keyed on lists of lowercased labels: `[<<"www">>, <<"example">>, <<"com">>]`. Every lookup had to hash or compare a deep term, and a name couldn't be looked up at all until it had been split, validated and lowercased, even when the answer was going to be "use this 2-byte pointer".

Two rounds of work changed that. In [#133](https://github.com/dnsimple/dns_erlang/pull/133) the encoder stopped splitting every name twice, and stopped growing the map one key at a time. Inserting into a small map copies it, so inserting a key per label meant one copy per label; the encoder now collects a name's suffixes and inserts them in one batch. For a name with 50 one-character labels, encoding went from 211 µs to 9.4 µs, 22 times faster. More importantly, an ordinary 8-label name went from 1.51 µs to 0.54 µs.

Then in the [next round](https://github.com/dnsimple/dns_erlang/commit/f673eb4) the keys themselves changed: each suffix is now the lowercased name as a *binary*, and each one is a sub-binary of the same name, so they cost nothing to produce and a single `memcmp` to compare. As a result, the raw input name is its own first key, and a name that's already in the map is answered before any splitting or lowercasing happens. That's the common case in a real response: every record in a set repeats the owner name, the answer repeats the question, and glue records repeat the nameserver names. Whole-message encoding got between 1.1 and 8.9 times faster, depending on how much the message repeats itself.

## What didn't work

Some of our favourite ideas lost, and the numbers were very clear about it:

- Scanning a label first, then appending it whole. It sounds faster than escaping byte by byte, but it forces the BEAM to materialise a sub-binary for every label. That added 15% to 20% more allocation and erased the win completely.
- `binary:match/2` with several patterns to check a label for special characters. It's implemented in C, so it must be fast, right? For short labels like the ones in DNS names, the setup cost made it 1.4 to 2.4 times slower than the inline scan.
- Building NSEC type bitmaps a byte at a time. Decoding them a byte at a time instead of a bit at a time halved the reductions. Doing the mirror image on the encoding side allocated 25% more with no speedup, because appending bits to a bitstring is already efficient on the BEAM.

The lesson: the BEAM is often smarter than you'd expect, and the only way to know is to measure.

## The bigger picture

Micro-benchmarks are nice, but what we care about is the nameserver. So we built a test that looks like production:

- 20,000 synthetic zones, 10% of them DNSSEC-signed, with the record mix our customers actually use.
- About 19 million queries matching the shape of our real traffic over a week: the same mix of query types and response codes, the same name lengths and label counts, the same skew towards popular names, and the same share of queries asking for DNSSEC (83%).
- erldns built three times, changing nothing but the dns_erlang version, pinned to dedicated cores on the same OTP version we run in production, five interleaved rounds each.

| `dns_erlang` | CPU per query | Max queries per second |
| --- | --- | --- |
| 5.0.5 (February) | 24.7 µs | 253k |
| 5.0.13 (July) | 24.9 µs | 250k |
| 5.0.21 (October) | **21.8 µs** | **285k** |

The summer work (the single accumulator, the decoder changes, the compression keys and SWAR in name decoding) shows up clearly: 12% less CPU per query, 14% more capacity, and lower latency at the same load. The round-to-round variation was below 1%. Profiling the same runs shows that the share of CPU spent inside `dns_erlang` dropped from 33% to 23%, and the share spent encoding responses halved, from 22% to 11%.

![Share of busy CPU samples with each dns_erlang module on the stack, 5.0.13 versus 5.0.21: all of dns_erlang 33.0% to 22.6%, dns_domain 23.5% to 13.3%, dns_encode 22.2% to 10.9%, dns_decode 3.7% to 4.0%.](https://blog.dnsimple.com/files/2026/dns-erlang-cpu-profile.png)

On production-class hardware (two Intel Xeon Silver 4215 sockets, with erldns and the load generator on separate NUMA nodes), the same test showed the same picture: 13% more queries per second at saturation, with 16% lower latency.

![End-to-end results by dns_erlang release. On the Ryzen 9 9950X3D, CPU per query was 24.7, 24.9 and 21.8 microseconds for 5.0.5, 5.0.13 and 5.0.21, and the maximum was 253k, 250k and 285k queries per second. On two Xeon Silver 4215 sockets, the maximum was 67.4k, 66.5k and 75.1k queries per second.](https://blog.dnsimple.com/files/2026/dns-erlang-end-to-end.png)

Just as interesting is what *didn't* move: the spring releases, with the faster `to_lower/1` and the first SWAR work, made those functions up to 30% faster in isolation, but end-to-end they're flat. Those functions simply weren't where a nameserver spends its time. A 2x speedup on 1% of the work is still 0.5%.

On a profile of one of our production nameservers, which also does things this test leaves out (ALIAS resolution, query analytics and telemetry), `dns_erlang` now accounts for about 9% of the busy CPU time. Which tells us where to look next: the biggest single piece today is the zone cache lookup in `erldns`, at about a third. That's a story for another time.

## What this means for DNSimple customers

Every percent of CPU we save per query is headroom we get back. It means more room to absorb traffic spikes and attacks before the [load-shedding mechanisms in erldns](https://blog.dnsimple.com/2026/02/erldns-v10-release/) have to kick in, and lower latency for the queries we answer along the way. Combined with our [fully independent DNS edge](https://blog.dnsimple.com/2026/08/building-our-fully-independent-dns-edge/), it all adds up to faster, more resilient DNS for your domains.

`dns_erlang` is open source and [available on Hex](https://hex.pm/packages/dns_erlang). If you build anything that speaks DNS on the BEAM, you get all of this for free. And if you just write Elixir or Erlang that handles binaries, we hope some of these patterns find their way into your code.

If you have questions about `dns_erlang`, `erldns` or DNSimple's infrastructure, [get in touch](https://dnsimple.com/contact). We love talking about this stuff.

Not using DNSimple yet? If you build on the BEAM, every query for your domains would go through the code in this post. [Give us a try free for 30 days](https://dnsimple.com/signup).

#### Nelson Vides

Nameserver Sensei

**We think domain management should be easy.**   
That's why we continue building DNSimple.
As I wrote previously, [we have proof automation now](https://www.imperialviolet.org/2026/07/26/zstd-lean.html). Given that fact, I think a very timely question is: how can we use it to improve software quality? The same machines that can write these proofs can also write large amounts of code. So an adjacent question is: how can we use them to improve software *understandability*?

It would be a mistake to start off afresh on those problems because there have been a *lot* of ideas in programming language design over the decades. The viability of ideas shifts as the underlying cost structures change, so things that didn't take off at the time might suddenly make a lot more sense. Still, language design involves a lot of tradeoffs, and features sometimes interact in surprising ways, so a lot of the work involves mixing some interesting-seeming ingredients together, baking, and asking “what is this? Is this a cake?”.

So I wanted to give a taste of some of the ingredients that I'm thinking about at the moment, and of the result.

### Ingredients

#### Mutable Value Semantics

Value semantics roughly says that you can't observe mutations to one variable through a different name. Value semantics are great for reasoning locally about code as, without them, you're constantly unsure what non-local effects might be happening.

When you work in a language, you instinctively know when it's using value semantics and when it's using reference semantics. Take Python:

```
x = [1]
y = x
y[0] = 2
print(x)
```

You likely know that that prints <kbd>[2]</kbd>. (Although if you write the same program in C++ with <kbd>std::vector</kbd> it prints <kbd>[1]</kbd>! There's no cross-language norm for this.)

Over the span of four lines of code, this is irrelevant. But as the scope of the sharing increases, so does the mental complexity. If you want to be able to jump into a bit of code and understand what it's doing, knowing that there is no such aliasing is a huge boon.

Functional programming resolves this by eliminating mutation: if there's no mutation then you certainly can't observe mutations via a different variable name. But mutation is important for efficiency and a lot of work is then required to get the efficiency back. Lean, for example, will do in-place mutations if there's only a single reference to an object. That's great! But it has the sharp edge that innocent-looking changes can mean that there's now a hidden reference kept somewhere and performance crashes.

Rust claims to fix both issues by restricting references so that you can't ever have both a mutable reference to something, and an active alias to it. (We'll ignore <kbd>Rc<RefCell<T>></kbd> and friends.)

Certainly Rust's restrictions help a great deal, but Mutable Value Semantics says that Rust goes too far by making references first-class, i.e. something that you can return and store in structures. First-class references lead to the borrow checker, which has undergone several deep rewrites (original to NLL, next to Polonius) to try and perfect it, and they lead to lifetimes, <kbd>DerefMut</kbd> etc., and much more complexity in the type system in general.

So an MVS system avoids all that by further restricting references and not allowing them in the type system. These ideas started [in Swift](https://forums.swift.org/t/valuesemantic-protocol/41686/58?page=3) and are currently championed in [Hylo](https://hylo-lang.org/). The best introduction I've found is [this talk](https://www.youtube.com/watch?v=op51SyyPJmw).

In an MVS system, functions can *take* three sorts of arguments: immutable, mutable, and owned. Immutable arguments might be a reference or a copy; the semantics are the same. Mutable arguments are conceptually copied in at call time and copied back out when a function returns, but of course that's semantically the same as taking a pointer. Lastly, owned arguments transfer ownership to the function and make it unusable in the caller afterwards.

But there are no references in the type system, so a function can't return or store them. But the inability to return references implies so much copying that MVS systems need to provide an alternative.

Hylo has a very cute system of [scoped coroutines](https://hylo-lang.org/docs/user/language-tour/subscripts/), inspired by Swift. These coroutines yield a value and, at the call site, all their arguments are locked for the duration of that value's span. At the end of the span, the coroutine continues running.

One of the common examples is that a coroutine can return a mutable bool for a vector of bits that have been packed into bytes. Then, when the coroutine continues once the return value is no longer used, it can write the new value of that bool back into the array of bytes. This wouldn't be possible without a coroutine because the function would have to return a pointer to a bool that exists nowhere in memory.

Having just lionised this feature, I should note that in my experiments I haven't actually included it because it makes the semantics more complex and I'm spending a lot of complexity budget on verification instead. Which brings us to another idea that combines with MVS…

#### Reference restrictions sidestep separation logics

If you want to do formal verification on a language like C, then you need to model the heap and you immediately hit the aliasing issues above. Then you end up with a [separation logic](https://en.wikipedia.org/wiki/Separation_logic) which lets you model disjoint areas of the heap (i.e. areas with no aliasing between them). Once you can speak about independent heaps, you can reason about a function that operates on one heap and hold the remainder constant.

This can work. The example that I'm (passingly) familiar with is the [Verified Software Toolchain](https://vst.cs.princeton.edu/) which connects to CompCert's semantics and allows you to state properties about C programs (with a separation logic) and thus verify C code all the way to machine code. But it's complex.

However! If you have restricted references then you can drop a huge amount of complexity from such systems! [Aeneas/Charon](https://github.com/AeneasVerif/aeneas) is the current canonical example of this which can translate a subset of Rust code into Lean (and other languages) where things can then be proved about it. Because of Rust's restrictions, the translation doesn't need a separation logic.

But by being more restrictive than Rust, MVS languages are even more amenable to such translation, and thus to formal verification, without going all the way to being functional languages and banning mutation completely.

#### Design by Contract

[Eiffel](https://www.eiffel.com/values/design-by-contract/introduction/) is the standard reference here. It introduced preconditions, postconditions, and invariants for functions/classes:

```
class DICTIONARY [ELEMENT]
feature
    put (x: ELEMENT; key: STRING) is
            -- Insert x so that it will be retrievable
            -- through key.
        require
            count <= capacity
            not key.empty
        ensure
            has (x)
            item (key) = x
            count = old count + 1
        end

    ... Interface specifications of other features ...

invariant
    0 <= count
    count <= capacity
end
```

While you've probably never used Eiffel, these notions are quite widespread now, although in common programming languages they are at best encoded in assertions if simple, comments if not, but mostly remain only in the author's head.

Eiffel did all its checks at run-time. There has been a *lot* of work on the balance between run-time and compile-time for these assertions, and on how to discharge assertions statically. Briefly, some work in this space that I'm aware of:

[Dafny](https://dafny.org/) allows a mixture of run-time and static assertions, and discharges the static ones via SMT solvers. [F*](https://fstar-lang.org/) does everything statically, again using SMT solvers, but with a functional language. [SPARK](https://www.adacore.com/languages/spark) has a mixture of run-time and static checks, using SMT solvers or (albeit very challenging to use) provers via [Why3](https://why3.org/). I've never touched [Verus](https://verus-lang.github.io/verus/guide/) but it's worth a mention because it's the most recent entry in this lineage and is Rust-based.

The problem with these systems is that the compile-time checking is much more powerful, because it can cover all possible values of the arguments, but the proof burden is significant. SMT solvers help a lot, but they can quickly hit (effective) non-termination for non-trivial cases. I did an F* summer school in Paris once, and the experienced people there had developed a sixth sense about what would displease the SMT solver and would instinctively code around it. It was an impressive skill! But not reassuring.

This is the key cost that has changed: SMT solvers were inadequate for more complex cases, and dropping into a proof assistant overwhelmed you with lots of inscrutable proof states. All this can be largely handled by models now.

Also, I claim that there are some interesting synergies between MVS and design-by-contract. In Rust, and more so in an MVS system, you end up using indices into arenas of objects to replace arbitrary pointers. (Which [can be faster](https://drops.dagstuhl.de/storage/01oasics/oasics-vol134-programming2025/OASIcs.Programming.2025.25/OASIcs.Programming.2025.25.pdf) due to cache locality.)

Given that one has all these indices flying around, wouldn't it be nice to have explicit invariants about them? Hopefully proven?

#### Refinement types

When writing code I will fairly often have some structure which has invariants that update as processing progresses. At some early part of the pipeline, the structure may be relatively arbitrary, perhaps freshly parsed from a file, and then as various checks and transforms are applied we know more and more about the value.

But in traditional languages, the structure has one type: its structural type. Even with Eiffel-style Design by Contract, invariants on a type are fixed.

The idea of being able to attach more invariants to a structure without duplicating most of it showed up as [Subtypes](https://lean-lang.org/doc/reference/latest/Basic-Types/Subtypes/) in proof systems, and [refinement types](https://www.cs.cmu.edu/~fp/papers/pldi91.pdf) in ML. You'll also see Rust code do this (mostly at run-time) with checked constructors like <kbd>NonZero</kbd> and <kbd>NonNull</kbd>. But those are run-time checks that the type system carries a certificate of. Similar to the evolution of Eiffel-style conditions, we can hope to make them static checks now, discharged via our new proof automation.

#### Literate programming

[Literate programming](https://en.wikipedia.org/wiki/Literate_programming) was the title of a paper by Knuth in the 80s, and [WEB](https://en.wikipedia.org/wiki/Web_(programming_system)) was the original implementation. The idea is that code should be written to be read and thus that it should be ordered for human, not machine, consumption, and that exposition should be at least as important as the code, and not relegated to comments.

Nearly twenty years ago I wanted to understand critbit trees and so wrote [an implementation](https://github.com/agl/critbit/blob/master/critbit.pdf) using CWEB to explore both ideas.

Relatedly, in my mind code has a graph structure deriving from which functions call which other functions. Source files are groups of strongly connected functions and I generally have little memory for what order functions have in a given source file. With the widespread use of LSPs and thus code indexing, we are edging slowly towards being less file orientated but I still feel that we could do much more.

There was a burst of such ideas in the 80s: Knuth's work, also Smalltalk & Lisp systems which kept code in databases rather than text files. Given the ecosystem of version control that assumes text-based files, code databases might be too awkward now, but I still feel the itch of dissatisfaction here.

### Baking them together

At the top of this post I also set a goal for code to be more understandable and, to that end, the easiest code to understand is the code that you didn't have to read because the contract says all that you need to know about it.

But let's work up to that a little.

Here's a function that looks like Rust (because I don't have better syntax ideas) but which doesn't verify.

```
fn add(a: u32, b: u32) -> u32 {
  return a + b;
}
```

When I'm reading code, I'm always trying to track the invariants and think about integer overflows. Sometimes the codebase aims to be overflow-clean and so I'm following bounds precisely. Most of the time I just have to ignore them unless the overflow is especially egregious. Now that we have proof automation, I shouldn't have to do that. So, as in SPARK, Verus, and others, <kbd>+</kbd> must statically not overflow and compiling the above gets you:

```
FAIL (refuted) vc_add_arith_1  arith    test:3  -  [smt z3 6ms, sat]
countermodel (z3, 6 ms; exact: the VC is false for these values):
  a = 1
  b = 4294967295 (2^32-1)
  goal a + b < 4294967296
    becomes 1 + 4294967295 < 4294967296
    1 + 4294967295 = 4294967296 (2^32)
```

That's the SMT solver giving you a counterexample that overflows. (<kbd>+%</kbd>, as in Zig, exists if you really want wrapping operations.)

If the values are bounded such that overflow can't happen, then obviously everything will be fine, automatically:

```
fn add(bytes: Vec<u8>) -> Option<u32> {
  if bytes.len() < 4 {
    return None;
  }

  let a = u32::from(bytes[0]) << 8 | u32::from(bytes[1]);
  let b = u32::from(bytes[2]) << 8 | u32::from(bytes[3]);
  return Some(a + b);
}
```

Casts are similar: <kbd>u32::from</kbd> is safe because it must be widening. For narrowing, <kbd>u32::exact_from</kbd> statically requires that the cast not truncate and, if you really need the machine operation, <kbd>u32::wrap_from</kbd> gives it to you.

And, of course, all vector indices must be statically valid.

Let me try and convince you of the benefits of contracts in terms of code understandability. For this, we're going to discuss a tiny bit of DER, the most common ASN.1 encoding.

DER is a tag-length-value format. We're just going to talk about the encoding of tags. Firstly, tags are in one of four *classes* which have integer values on the wire:

```
pub ghost fn class_num(c: Class) -> Int {
  match c {
    Class::Universal => 0,
    Class::Application => 1,
    Class::ContextSpecific => 2,
    Class::Private => 3,
  }
}
```

A DER tag is then a class and a tag number, plus a flag which tells you whether the value contains more DER values nested inside it. In theory, tag numbers are unbounded integers. In practice, everyone limits them; here we'll bound them below 2<sup>28</sup> because, as you'll see, that limits the tags to five bytes and the next byte would exceed 2<sup>32</sup>. The (class, tag number) combination of (Universal, 0) is banned in DER as it's the [BER](https://en.wikipedia.org/wiki/X.690#BER_encoding) end-of-contents value:

```
pub struct Tag {
  pub(read) class: Class,
  pub(read) num: u32,
  pub(read) constructed: bool,
} pub invariant @no_universal_zero {
  self.class == Class::Universal ==> self.num != 0
}
```

A tag can be encoded as one or more bytes. The first byte has two bits of class, one bit for the <kbd>constructed</kbd> flag, and five bits of tag number. If the tag number is ≥ 0x1f (the maximum 5-bit value) then it's encoded as 0x1f and more bytes of tag follow:

```
pub ghost fn tag_enc(t: Tag) -> Seq<u8> {
  let id = class_num(t.class) * 0x40 + if t.constructed { 0x20 } else { 0 };
  if t.num < 0x1f {
    seq![u8::exact_from(id + t.num)]
  } else {
    seq![u8::exact_from(id + 0x1f)] ++ b128_enc(t.num, false)
  }
}
```

The tag numbers that need more bytes are big-endian, base-128 encoded, with the high bit set each time if another byte follows:

```
pub ghost fn b128_enc(v: Int, cont: bool) -> Seq<u8>
    decreases { v }
{
  let last = seq![u8::exact_from(if cont { 0x80 } else { 0 } + v % 0x80)];
  if v < 0x80 { last } else { b128_enc(v / 0x80, true) ++ last }
}
```

Now, here's an encoding function for DER tags:

```
pub fn format_tag(t: Tag, out: mut Vec<u8>)
  requires @range { t.num < 0x1000_0000 }
  ensures @encodes { seq_of(out) == seq_of(old(out)) ++ tag_enc(t) }
{
  …
}
```

The body of the function is missing—but you don't need it! The contract requires that it encodes exactly as <kbd>tag_enc</kbd> specifies so you don't need to know more. This isn't saving you too much because the code isn't that complicated. You would have to think about the shifts and masks that it's using for the base-128 encoding (rather than recursion), but that's only a few seconds.

But here's a more substantial saving:

```
pub fn parse_tag(reader: mut bytes::Reader, in: [u8]) ->
        Tag ! (Error | bytes::BytesError)
  ensures @decodes {
    result.num < 0x1000_0000
    && seq_of(in).slice(old(reader).pos, reader.pos) == tag_enc(result)
  }
  ensures_err @no_encoding {
    forall t: Tag :: t.num < 0x1000_0000
      && old(reader).pos + tag_enc(t).len() <= old(reader).end
      ==> seq_of(in).slice(old(reader).pos, old(reader).pos + tag_enc(t).len())
        != tag_enc(t)
  }
  …
{
  …
}
```

This is saying that:

1. If it decodes a value then the given bytes start with the encoding of that value.
2. If it returns an error then there is no valid Tag value which encodes to the bytes at the beginning of the input.

This enforces not just the baseline of memory safety, no run-time panics etc., but that the parser is fully strict: it never parses anything other than the canonical encoding of a value, as defined above. This is not a trivial thing to code review, and here you don't have to.

Also you see signs of MVS: a <kbd>Reader</kbd> can't hold a reference to <kbd>in</kbd> because references can't be stored. Thus <kbd>in</kbd> is passed separately (and the indices are proven to be valid). This is part of the tradeoff for local reasoning and strong contracts.

I've not mentioned linear types, views in return values, or Zig-style error unions, and I'll only touch on refinement types in the lightest sense by noting the pleasing definition of the <kbd>String</kbd> type in this experiment:

```
pub form String of Vec<u8> { utf8::valid_from(self, 0) }
```

Lastly, nodding towards literate programming, I'll note that this blog post itself is a valid source file for this language: the language consumes Markdown files and only compiles lines in annotated code blocks. The Lean proofs are kept in separate files, not for human consumption. There's already a tool for showing a source file with only the public definitions, and with the bodies of functions elided, and there's still more I want to explore here in terms of viewing source files as a graph.

### Is the cake a lie?

It's worth discussing the more bitter flavours in this cake too.

The front end of the compiler emits lots of verification conditions for the code to be correct. Every arithmetic operation emits overflow checks, every indexing operation emits range checks, every invariant and postcondition results in checks, every loop must be shown to be terminating, etc.

The little DER tag example above results in 149 of them. Each is first sent to Z3 and then, if Z3 times out (after a couple of seconds), to cvc5. But the solvers are never trusted. If they believe that a condition holds they output the [unsat core](https://en.wikipedia.org/wiki/Unsatisfiable_core) which is used to trim the hypotheses which are fed into Lean. Lean automation chews on the problem for a while and, if that times out, an LLM comes to write a manual proof in Lean.

There's a cache of proven conditions, of course, and the Lean proofs are saved in a different file. But overall even reasonably simple examples type-check at about 10 lines per second. If you invalidate the cache then medium-sized programs can take multiple hours to recheck on a fast machine. (Not *reprove*, just to check the proofs that already exist!) So modularity of code is important to keep the scaling line flatter.

LLM compute is needed too: after I laid out the spec for the DER tag example above, a model took about 30 minutes to get it working. But if you ask a modern model to write the same thing in Go, it will do it in under 10 seconds. (Although the result doesn't hit nearly the same quality bar and the lax parsing would cause security problems in sensitive contexts.)

Overall, this language was an experiment in how we can convert compute into high-quality and understandable code. I'll claim that it's making interesting steps towards that goal, but you do need a *lot* of compute.

Also, there is a considerable trusted base involved here. While you don't have to trust the SMT solvers, you do have to trust that the front end is correctly translating the code into verification conditions for Lean, and you have to trust that it is correctly translating it into LLVM IR. I think that's fine: the comparison here is with regular languages like C++ and Rust. This is not an attempt at a minimal TCB language with extremely strong guarantees like [CakeML](https://github.com/CakeML/cakeml).

Still, the language does have significant aspects of delight. Being able to write the spec for DER encoding, and then have the *correct* code for it generated, does make me reflect on the amount of time [and suffering](https://www.imperialviolet.org/2014/09/26/pkcs1.html) that I've put into DER over the years that could now be avoided.
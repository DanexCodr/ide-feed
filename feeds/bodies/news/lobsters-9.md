We are pleased to announce the release of version 0.14.0 of [Creusot](https://creusot.rs),
our formal verification tool for Rust.

In this post, we highlight a small selection of new features.
See the full [changelog](https://github.com/creusot-rs/creusot/blob/master/CHANGELOG.md#0140---2026-10-09)
for the rest.

# What's new in Creusot?

## Partial orders

Previously, Creusot restricted its specification of `PartialOrd` to total
orders. Since version 0.13.0, we have relaxed it to allow partial orders.
(We skipped a devlog entry for 0.13.0 so let's talk about this here.)

Our previous definition of total order (`OrdLogic`) relied on the
comparison function `cmp_log` (the logic counterpart to `cmp`), which returns an `Ordering`.

```
// Old definition of total order
pub trait OrdLogic {
    #[logic]
    fn cmp_log(self, other: Self) -> Ordering;

    // ... (laws and other comparison operators)
}
```

That had the benefit of making totality an implicit consequence of the type of the function:
any two elements must compare either `Less` , `Equal`, or `Greater`.

With the switch to partial orders, a traditional formulation based on a
boolean comparison function ("`<`", aka. `lt_log`) becomes more natural.
A strict partial order (`PartialOrdLogic`) consists of a comparison function `lt_log` which
is irreflexive and transitive. Totality becomes another law: for all `x`, `y`,
the trijunction `x < y || x == y || y < x` must hold.

```
// (New) definition of partial order
pub trait PartialOrdLogic {
    /// `self < other` in logic
    #[logic]
    fn lt_log(self, other: Self) -> bool;

    // ... (laws (irreflexivity, transitivity) and other comparison operators)
}

// New definition of total order
pub trait OrdLogic {
    /// The order is total
    #[logic(law)]
    #[ensures(self < other || self == other || other < self)]
    fn lt_log_total(self, other: Self);
}
```

Interestingly, none of our existing proofs were affected by this change.
Our automated provers just took it in stride.

## Logic VC gen

Creusot now generates verification conditions (VCs) for snapshots,
which are logic expressions embedded in Rust programs.
In particular, this enhances the use of "lemma functions",
a common idiom in verification tools similar to Creusot.

For example, you can encode a lemma as a logic function such as this,
which logically amounts to the proposition `forall<x> hyp(x) -> concl(x)`:

```
#[logic]
#[requires(hyp(x))]
#[ensures(concl(x))]
fn lemma(x: usize) {}
```

Then, inside a program function you can call `lemma` inside a `snapshot!`:

```
fn f(n: usize) {
   snapshot!(lemma(n));
}
```

Creusot now translates this call to an assertion that `hyp(n)` (the precondition of `lemma`) is true
and an assumption that `concl(n)` (its postcondition) is true. Notably, these statements
are specialized to `n`, the argument of `lemma`, so we avoid relying on provers to
instantiate the universal quantifier in `forall<x> hyp(x) -> concl(x)`.

It should be said that this new feature specifically enables *logic* functions to be
used as lemma functions.
Before, you could already do something similar with program functions:

```
#[requires(hyp(x))]
#[ensures(concl(x))]
fn lemma(x: usize) {}

fn f(n: usize) {
    lemma(n);
}
```

The difference is that (1) this version introduces a Rust function call, however
trivial it may be, and (2) it must pass the borrow checker, which may require
boilerplate to work around when all you wanted is to state some facts.
In contrast, snapshots are entirely erased, so it is clear that
they are there only for the sake of formal proof.
Thus, these newly generated VCs for snapshots let us draw clearer boundaries
between the worlds of programs and proofs.

It may seem surprising that Creusot did not already do this. This comes down to
the fact that programs and specifications are written in two separate languages,
with their own semantics, and thus with different mechanisms and motivations for generating VCs.
Without going into too much details, VCs were originally not generated for `snapshot!`
because it isn't necessary for soundness, but it turns out to help catch mistakes
in specifications quicker (such as out-of-bounds indexing), on top of enabling
new techniques such as that described above.

## rust-analyzer integration

It is finally possible to use Go-to-definition in Pearlite specifications.

![Screenshot of go-to-definition working in the middle of a Creusot specification](https://devlog.creusot.rs/creusot-go-to-definition.png)

To start, we needed to make rust-analyzer expand the code of specifications.
In normal compilation, specification macros (`#[requires]`, `#[ensures]`,
`proof_assert!`, `snapshot!`, etc.) erase themselves, discarding their contents.
We just needed to pass options to rust-analyzer for it to expand those macros the same way Creusot does
(see [our guide for the relevant rust-analyzer settings](https://guide.creusot.rs/quickstart/editor_config.html)).

One worry we had was that Pearlite macros expand to not quite valid Rust code,
not meant to be compiled by rustc:
it passes the type checker, but not the borrow checker.
Luckily for us, rust-analyzer does not do borrow checking,
so it doesn't see any problem with the expanded code.

With that done, Go-to-definition did start to work, but it returned numerous irrelevant results.
The problem was that the tokens produced by Pearlite macros carried spans that were
too coarse-grained.

To explain it very roughly, when you activate Go-to-definition,
rust-analyzer looks for identifiers in the final AST whose span ranges over your cursor.
For example, `a + b` in Pearlite expands to a method call
`::creusot_std::logic::ops::AddLogic::add_logic(a, b)`,
where every generated token carries the span of the whole expression `a + b`.
Hence, Go-to-definition from anywhere in that expression ends up looking up the definitions
of all of `creusot_std`, `logic`, `ops`, `AddLogic`, and `add_logic`.

In this case, we'd like to only look up `add_logic`, and only when the cursor is right next to `+`.
The fix is to make the token `add_logic` have the span of `+`, and
to make the other identifiers have a zero-width span,
which seems to be enough for rust-analyzer to ignore them.

Many thanks to Sarah Quiñones for figuring all this out.
This fix makes navigating specifications in Creusot much more pleasant.

Thanks for tuning in. If you have any questions about Creusot, you are welcome to join
[our Zulip channel](https://why3.zulipchat.com/#narrow/channel/341707-creusot),
or to open a [discussion](https://github.com/creusot-rs/creusot/discussions)
or an [issue](https://github.com/creusot-rs/creusot/issues) on the Creusot repository.
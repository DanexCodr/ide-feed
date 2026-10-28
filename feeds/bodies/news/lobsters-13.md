It seems inevitable that compile-time dependent types will come to systems programming.  
C++ has templates and `constexpr`. Rust has const generics. Zig has `comptime`. Even C has `_Generic`.
However, these features tend to be highly restricted, lack a proper type system, or both.

I’m working on [Syl](https://syl.dev/), a language which aims to encode compile-time computation in a modal type system.
Syl is primarily inspired by András Kovács’ work on [two-level](https://andraskovacs.github.io/pdfs/2ltt.pdf) [type theory](https://andraskovacs.github.io/pdfs/2ltt_icfp24.pdf), as well as plans for [OxCaml](https://oxcaml.org/).

*The Syl compiler may be found on [GitHub](https://github.com/TheNumbat/Syl).*

## Modes

In Syl, all values have a *mode* along with a type.
Modes describe properties of values independent of their types.
For example, [OxCaml uses modes](https://oxcaml.org/documentation/modes/intro/) to indicate whether a value is uniquely owned, may be written to, may be sent to another thread, etc.<sup>[1](https://thenumb.at/Syl-Intro/#fn:1)</sup>

Syl has two mode axes: *staticity* and *erasure*.
On the staticity axis, a value may be either `static` or `dynamic`.
On erasure, either `erased` or `unerased`.

- A static value is knowable at compile time; a dynamic value may not be.
- An unerased value is knowable at runtime; an erased value may not be.

For example, literals are `static unerased`, since they are clearly knowable at both compile time and runtime.
You can check by writing a mode annotation:

```text
let x = 0 @ static unerased;;
```

Each mode axis has a sub-moding relation.
If you have a `static` value, it’s safe to forget that it is knowable at compile time and hence treat it as `dynamic`.
Similarly, an `unerased` value may be treated as `erased`.
Mode annotations may “weaken” the mode, but not “strengthen” it:

```text
let x = 0 @ dynamic;;

let y = x @ static;;
        ^^^^^^^^^^
Error: Expected a static expression, but got dynamic.
```

As you might expect, branching on a `dynamic` value causes the result to be `dynamic`.

```text
let x = 0 @ dynamic;;

let y = (if x == 0 then 1 else 2) @ static;;
        ^^^^^^^^^^^^^^^^^^^^^^^^
Error: Expected a static expression, but got dynamic.
```

As long as they don’t capture or branch on `dynamic` values, functions preserve staticity.<sup>[2](https://thenumb.at/Syl-Intro/#fn:2)</sup>

```text
let f = fn (x : int) -> x;;

let x = (f 0) @ static;;

let y = (f (1 @ dynamic)) @ static;;
        ^^^^^^^^^^^^^^^^^
Error: Expected a static expression, but got dynamic.
```

Functions that return `erased` values are themselves `erased`, so cannot be applied at runtime.

```text
let f = fn (x : unit) -> 1 @ erased;;

let g = f @ unerased;;
        ^
Error: Expected an unerased expression, but got erased.
```

Now, what can we do with this information?
When a value is knowable at compile time, surrounding code can be *monomorphized*.
Functions of `static` parameters take advantage of this fact:

```text
let f = fn (static x : bool) -> print_bool x;;
```

Whenever we call `f x`, the compiler requires that both `f` and `x` have mode `static`.
If they do, it selects a particular implementation of `f` specialized to the value of `x`.
Concretely, `f true` would call a function that hard-codes `print_bool true`, and likewise for `f false`.

In this example, we’re printing the value of `x` at runtime, so it needs to be `unerased`.
That’s often unnecessary: if `x` only determines how to compile the body of `f`, it can be `erased`.

```text
let f = fn (erased x : bool) -> if erased x then print_int 0 else print_int 1;;
```

Here, `erased` also implies `static`, so `f` will be specialized on `x`.
The `if erased` expression accepts a `static erased` condition and is guaranteed to resolve at compile time.
Therefore, `f true` refers to a thunk with the body `print_int 0`, and likewise for `f false`.

## Dependent Types

On their own, the `static` and `erased` modes let us explicitly request specialization-based optimizations,
but they don’t give us dependent types. Functions of `static` arguments do.

```text
let f = fn (erased x : bool) -> if erased x then 0 else true;;
```

Here, `if erased` allows us to return an integer if `x` is true and a boolean otherwise.
Hence, `f` has a dependent function type, which encodes how the result type depends on the *value* of the input.

```text
f : erased bool as x -> if erased x then int else bool
```

Note `ty as name` gives the argument a name for use in the result.

Applications can then determine the correct result type by evaluating `f`’s type.

```text
let x = (f true) : int;;

let y = (f false) : bool;;
```

There is no distinct type grammar: type formers like `->` and type annotations are normal expressions.
`int` and `bool` are just `erased` values of type `type`, and abstracting over them gives us polymorphism.

```text
let id = fn (erased t : type) -> fn (x : t) -> x;;

let x = id int 0;;

let y = id bool true;;
```

As we saw above, functions of `static` arguments are monomorphized.
At runtime, `id int` refers to an identity function that directly operates on integers, and likewise for `id bool`.

That is, Syl is **dependently typed at compile time and simply typed at runtime.**<sup>[3](https://thenumb.at/Syl-Intro/#fn:3)</sup>

- Constructs that determine the shape of the runtime program require `static` information.
- Types are always `erased`, so the runtime program cannot inspect types.

Syl implements dependent typechecking similarly to existing languages, so we won’t discuss it in detail.
However, the relationship between types and propositions in Syl differs from that of languages like Lean, Rocq, and Agda.

### Proofs

In particular, Syl supports general recursion in compile time computations and gives `type` type `type`.
Allowing either of these features implies that constructing an expression of type `t` does **not** prove the proposition corresponding to `t`.

For example, we can implement a function that ostensibly returns a value of any type:

```text
let magic =
  fn (erased t : type) ->
    fun loop (_ : unit) : t = loop () in
    loop ()
;;
```

Note `magic` could also be implemented using `type : type` via [Girard’s paradox](https://ncatlab.org/nlab/show/Burali-Forti%27s+paradox).

Despite having type `erased type as t -> t`, this function never actually produces a value—it’s an infinite loop.
The type describes what `magic t` would produce if it completed, but does not guarantee that it does.

Although this type system would not be suitable for a theorem proving language, it does *not* rule out type safety or even useful proofs.
It has two practical consequences:

- Functions used in type-level computations may diverge, so typechecking is not decidable.
- Functions don’t discharge universally quantified claims, so the compiler must evaluate all applications that produce proofs before relying on their results.<sup>[4](https://thenumb.at/Syl-Intro/#fn:4)</sup><sup>[5](https://thenumb.at/Syl-Intro/#fn:5)</sup>

In return, we don’t need a totality checker (all `static` expressions may be used in types) or universe machinery (type-level programming is intuitive).

### Totality

Because Syl is a *programming language*, the point of compilation is to produce a runtime artifact satisfying the invariants enforced by the type system.
Therefore, we only care about invocations of dependent functions that actually occur during compilation—it’s fine for others to diverge.

Still, typechecking getting stuck during development is a poor user experience, so Syl also implements fuel limits.
Given competent compile-time debugging tools, I think this is reasonable.

```text
fun f (erased _ : unit) : erased type = f ();;
                                        ^
Error: Recursion limit reached.

let x = 1 : f ();;
```

Eschewing totality also means Syl can support explicitly partial functions at little additional cost.
For example, here’s a division function that statically checks the divisor is non-zero:

```text
let safe_div =
  fn (static d : int) ->
    if erased d != 0
    then fn (x : int) -> x / d
    else unreachable
;;
```

The `unreachable` keyword asserts that a branch does not appear in the runtime program.
During dependent typechecking, the `else` branch is treated as a bottom value, so imposes no restrictions on the `then` branch.
However, if `else` is reached while instantiating `safe_div`, we get an error:

```text
    ...
    else unreachable
         ^^^^^^^^^^^
Error: Unreachable reached.
;;

let x = safe_div 0 1;;
```

Allowing partial functions reopens the door to inscrutable C++-style template instantiation errors.
Luckily, explicit partiality means we can require users to provide error messages in unsupported cases, and combined with the lack of duck-typing at compile time, I think Syl can avoid most of the downsides.

## Examples

### Typed Interpreter

The following program does not require the full power of dependent types—it’s often used as a motivating example for GADTs in OCaml or Haskell—but I think the comparison is illustrative.

We’ll start by defining a variant to use as an index.

```text
let sort = variant { int, bool };;
```

*Notes: Both `sort` and its constructors `sort.int`/`sort.bool` are normal values. Variants are unboxed.*

Then a function to convert a `sort` to the corresponding type.

```text
fun value (erased s : sort) : erased type =
  match erased s {
    .int -> int,
    .bool -> bool,
  }
;;
```

*Note: like `if erased`, `match erased` allows an `erased` scrutinee and is resolved at compile time.*

Next, an indexed expression type.
The type is literally a recursive function with a `sort` argument:

```text
fun expr (erased s : sort) : erased type =
  match erased s {
    .int ->
      variant {
        lit : int,
        add : &(expr sort.int ^ expr sort.int),
        if_ : &(expr sort.bool ^ expr sort.int ^ expr sort.int),
      },
    .bool ->
      variant {
        lit : bool,
        eq : &(expr sort.int ^ expr sort.int),
      },
  }
;;
```

*Notes: `&` represents an indirection. `^` is the tuple type former.*

Finally, the interpreter.
In the `.int` branch, the compiler knows that only the `int`-returning constructors appear, and likewise for `.bool`.

```text
fun eval (erased s : sort) : expr s -> value s =
  fn (e : expr s) ->
    match erased s {
      .int ->
        match e {
          .lit n -> n,
          .add &(left, right) -> eval sort.int left + eval sort.int right,
          .if_ &(condition, yes, no) ->
            if eval sort.bool condition then eval sort.int yes else eval sort.int no,
        },
      .bool ->
        match e {
          .lit b -> b,
          .eq &(left, right) -> eval sort.int left == eval sort.int right,
        },
    }
;;
```

Functions of `static` arguments are monomorphized and `erased` branches are eliminated, so the interpreter compiles to the same structure you’d expect from template specialization in C++.<sup>[6](https://thenumb.at/Syl-Intro/#fn:6)</sup>

### Length-Indexed Vector

*Warning: the syntax here needs a lot of work.*

Proper dependent types enable us to encode the length of lists in the type system.
Let’s write an `append` function whose type shows that the output length is the sum of the input lengths.

While we could index our list by an `int`, Syl lacks tools for reasoning about signed, fixed-width integers.
Instead, let’s define our own Peano `nat` type.

```text
let nat =
  fun nat (erased _ : unit) : erased type =
    variant { zero, succ : &(nat ()) }
  in
  nat ()
;;
```

*Note: there’s no `let rec`, so we define `nat` via a recursive function.*

```text
fun add (static nm : nat ^ nat) : nat =
  match static nm {
    (.zero, m) -> m,
    (.succ &n, m) -> nat.succ box (add (n, m)),
  }
;;
```

*Notes: `match static` is like `match erased` but does not erase the contents of the scrutinee. We should use `erased` everywhere, but variant constructors are not yet mode-polymorphic. If all `nat`s were erased, the `box` indirection also wouldn’t be necessary.*

Now the unboxed, length-indexed list.
Note the lack of indirection.

```text
fun vec (erased t : type) : erased (erased nat -> erased type) =
  fn (erased n : nat) ->
    match erased n {
      .zero -> variant { nil },
      .succ &n -> variant { cons : t ^ vec t n },
    }
;;
```

Finally, the `append` function.
Crucially, the compiler is able to infer that the `.cons` case has the correct return type by unfolding `add` and `vec`.

```text
fun append
  (erased t : type) : (static nat as n
                         -> static nat as m
                         -> vec t n
                         -> vec t m
                         -> vec t (add (n, m))) =
  fn (static n : nat) ->
    fn (static m : nat) ->
      fn (v1 : vec t n) ->
        fn (v2 : vec t m) ->
          match static n {
            .zero -> v2,
            .succ &n_minus_1 ->
              match v1 {
                .cons (x, xs) -> (vec t (add (n, m))).cons (x, append t n_minus_1 m xs v2),
              },
          }
;;
```

*Notes: this is rather verbose since we don’t have n-ary function syntax. We also have to fully qualify the `vec` type `.cons` comes from because it’s not inferred yet.*

As above, all lengths are known at compile time, so the runtime program has semantics akin to a `constexpr` length computation in C++ (though the `unerased` lengths may be materialized).

## Extensions

Many useful language features can be defined in user code using compile-time dependent types.
Here are few promising (partially implemented) examples.

### Higher-Kinded Types

Higher-kinded types are just `erased` functions on types.
You can abstract over them like anything else.

```text
singleton :
    erased (erased type -> erased type) as container ->
    erased type as element ->
    element ->
    container element
```

This example already works, but as written, all you can do with `container` is apply it.
We also need the ability to specify interfaces that connect types and values, leading to…

### Modules and Functors

Once Syl has [OxCaml-style modalities](https://oxcaml.org/documentation/modes/reference/#modalities)<sup>[7](https://thenumb.at/Syl-Intro/#fn:7)</sup>, you’ll be able to nest `erased`/`dynamic` values inside `unerased`/`static` values.
Then dependent records can take the place of ML-style modules:

```text
let container = record {
  ty : erased type -> erased type @@ erased,
  create : erased type as element -> element -> ty element,
};;
```

Note `@@ erased` implies that all uses of `container.ty` see an `erased` value regardless of the erasure of `container`.
Now we can give `singleton` an implementable type:

```text
singleton :
    static container as container ->
    erased type as element ->
    element ->
    container.ty element
```

Similarly, ML-style functors can be implemented as dependent functions:

```text
fun pair (static c : container) : container = {
  ty = (fn (erased element : type) ->
         c.ty element ^ c.ty element),
  create = (fn (erased element : type) ->
             fn (e : element) ->
               c.create element e, c.create element e),
};;
```

Finally, with inferred arguments, records could provide most of the affordances of typeclasses or traits.

### Imports

We can even use static computation to describe how multi-file programs are built.
The compiler just has to provide the following functions:

```text
import_sig : erased string -> erased type
import : erased string as path -> import_sig path
```

If we treat file-level definitions as record fields, `import_sig` can infer a record type for a file and `import` can produce a value of that type.
In fact, these functions could just as easily take code strings, letting us generate code at compile time!

### Reflection

Syl already has rudimentary reflection via the built-in `repr` function, which returns metadata for a type.

```text
fun print_ty (erased t : type) : unit =
  match erased repr t {
    .unit -> print "unit",
    .bool -> print "bool",
    .int -> print "int",
    _ -> unreachable,
  }
;;
```

This facility could be straightforwardly extended to allow inspecting the structure of types, which could then be used to implement typed Rust or OCaml-style derivers.

### User-Defined Layouts

While fairly speculative, I think we should be able to define and manipulate types’ runtime layouts at compile time.
With such a feature, users could safely describe interoperable niche optimizations, possibly in the style of [*Bit-Stealing Made Legal*](https://inria.hal.science/hal-04165615v1/document).
This would also require some notion of “unaddressable” fields that do not allow creating pointers to them.

## Everything Else

Syl’s design is far from complete.
In particular, it needs stories for mode polymorphism, lifetimes, linearity, implicit parameters, and proofs.
The compiler needs incremental compilation, useful error traces, and an LLVM backend.
I hope to share more thoughts on these areas in the future.

# Footnotes

1. In the literature, modal type systems are presented in terms of modalities. We will describe modes as they appear in OxCaml, but you can translate by thinking of all values as `static unerased` until captured under a `dynamic` or `erased` modality. [↩︎](https://thenumb.at/Syl-Intro/#fnref:1)
2. Currently, staticity has modal axiom K, which allows staticity-preserving functions to operate on dynamic arguments. I plan to replace the implicit application rule with mode polymorphism, which can also handle erasure. [↩︎](https://thenumb.at/Syl-Intro/#fnref:2)
3. This is the core idea of [*Staged Compilation with Two-Level Type Theory*](https://andraskovacs.github.io/pdfs/2ltt.pdf), though it’s not presented as a modal type system. [↩︎](https://thenumb.at/Syl-Intro/#fnref:3)
4. This idea is formally explored in [*Irrelevance, Heterogeneous Equality, and Call-by-value Dependent Type Systems*](https://www.cis.upenn.edu/~sweirich/papers/msfp12prog.pdf). Thanks to Chris for proofreading this post! [↩︎](https://thenumb.at/Syl-Intro/#fnref:4)
5. Syl does not yet have equality types, but once it does, erasure will provide a natural mechanism for forcing proof-producing computations when their results are needed. For example, `assert erased b` could establish `b = true` in the proof context by checking it reduces to `true`. [↩︎](https://thenumb.at/Syl-Intro/#fnref:5)
6. This isn’t a fair comparison, but it’s better! [C++](https://godbolt.org/z/zP3Y9PjMG) / [Syl](https://pastebin.com/BNrfcP8B). [↩︎](https://thenumb.at/Syl-Intro/#fnref:6)
7. There exist ideas on how to make such modalities inferrable, but I don’t understand them yet. [↩︎](https://thenumb.at/Syl-Intro/#fnref:7)
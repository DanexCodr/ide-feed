TIL (or this week-ish I learned) why big-sigma and big-pi turn up in
the notation of dependent type theory.

I’ve long been aware of the zoo of more obscure Greek letters that
turn up in papers about type system features of functional programming
languages, `μ`, `Λ`, `Π`, `Σ`. Their meaning is usually clear from context
but the reason for the choice of notation is usually not explained.

I recently stumbled on an explanation for `Π` (dependent functions)
and `Σ` (dependent pairs) which turn out to be nicer than I expected,
and closely related to every-day algebraic data types.

## [sizes of types](https://dotat.at/@/2025-05-28-types.html#sizes-of-types)

The easiest way to understand algebraic data types is by counting the
inhabitants of a type. For example:

- the unit type `()` has one inhabitant, `()`, and the number 1 is why it’s called the unit type;
- the `bool` type hass two inhabitants, `false` and `true`.

I have even seen these types called **`1`** and **`2`** (cruelly,
without explanation) in occasional papers.

## [product types](https://dotat.at/@/2025-05-28-types.html#product-types)

Or pairs or (more generally) tuples or records. Usually written,

```
    (A, B)
```

The pair contains an *A* and a *B*, so the number of possible values is
the number of possible *A* values multiplied by the number of possible
*B* values.

So it is spelled in type theory (and in Standard ML) like,

```
    A * B
```

## [sum types](https://dotat.at/@/2025-05-28-types.html#sum-types)

Or disjoint union, or variant record. Declared in Haskell like,

```hs
        data Either a b
            = Left a
            | Right b
```

Or in Rust like,

```rust
        enum Either<A, B> {
            Left(A),
            Right(B),
        }
```

A value of the type is either an *A* or a *B*, so the number of
possible values is the number of *A* values plus the number of *B*
values.

So it is spelled in type theory like,

```
    A + B
```

## [dependent pairs](https://dotat.at/@/2025-05-28-types.html#dependent-pairs)

In a dependent pair, the *type* of the second element depends on the
*value* of the first. The classic example is a slice, roughly,

```rust
        struct IntSlice {
            len: usize,
            elem: &[i64; len],
        }
```

(This might look a bit circular, but the idea is that an array `[i64; N]` must be told how big it is – its size is an explicit part of its
type – but an `IntSlice` knows its own size. The traditional
dependent “vector” type is a sized linked list, more like my array
type than my slice type.)

The classic way to write a dependent pair in type theory is like,

Σ len: usize . Array(Int, len)

The big sigma binds a variable that has a type annotation, with a
scope covering the expression after the dot – similar syntax to a
typed lambda expression.

We can expand a simple example like this into a many-armed sum type:
either an array of length zero, or an array of length 1, or an array
of length 2, … but in a sigma type the discriminant is user-defined
instead of hidden.

The number of possible values of the type comes from adding up all the
alternatives, a summation just like the big sigma summation we were
taught in school.

When the second element doesn’t depend on the first element, we can
count the inhabitants like,

And the sigma type simplifies to a product type.

### [telescopes](https://dotat.at/@/2025-05-28-types.html#telescopes)

An aside from the main topic of these notes, I also recently
encountered the name “telescope” for a multi-part dependent tuple or
record.

The name “telescope” comes from de Bruijn’s AUTOMATH, one of the first
computerized proof assistants. (I first encountered de Bruijn as the
inventor of numbered lambda bindings.)

## [dependent functions](https://dotat.at/@/2025-05-28-types.html#dependent-functions)

The return type of a dependent function can vary according to the
argument it is passed.

For example, to construct an array we might write something like,

```rust
        fn repeat_zero(len: usize) -> [i64; len] {
            [0; len]
        }
```

The classic way to write the type of `repeat_zero()` is very similar
to the `IntSlice` dependent pair, but with a big pi instead of a big
sigma:

Π len: usize . Array(Int, len)

Mmm, pie.

To count the number of possible (pure, total) functions *A* ➞ *B*, we
can think of each function as a big lookup table with *A* entries each
containing a *B*. That is, a big tuple (*B*, *B*, … *B*), that is,
*B* * *B* * … * *B*, that is, *B*<sup>*A*</sup>. Functions are
exponential types.

We can count a dependent function, where the number of possible
*B*s depends on which *A* we are passed,

## [danger](https://dotat.at/@/2025-05-28-types.html#danger)

I have avoided the terms “dependent sum” and “dependent product”,
because they seem perfectly designed to cause confusion over whether I
am talking about variants, records, or functions.

It kind of makes me want to avoid algebraic data type jargon, except
that there isn’t a good alternative for “sum type”. Hmf.
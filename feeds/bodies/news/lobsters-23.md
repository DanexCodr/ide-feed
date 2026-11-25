This post will describe an algorithm for constructing an ANF/similar IR from a functional-like base language with no closure usage,
and with no related excess space requirements. This algorithm is as far as I know not new, and has apparently been known in
imperative compilation for a while. However, I admittedly have no source for this, nor
have I seen it described for functional-like languages.

Thanks to Ryan Brewer and rpjohnst for their inspiration on this.

If you are only interested in code, please skip to Implementation.

First, let us describe our input and output languages. Our input language will look like this:

```
type ml =
  | Let of string * ml * ml
  | Name of string
  | Int of int
  | Add of ml * ml
  | Print of ml
```

This is meant to echo some simple functional programming language, and contains all the elements needed to demonstrate the algorithm.

Our output language will look like a lexically-scoped flat ANF-style construction, with all lets at the toplevel.
The goal is to convert from our input `ml` to this language.

```
type base =
  | Name of string
  | Add of string * string
  | Int of int
  | Print of string

type anf =
  | Let of string * base * anf
  | Done of string
  | Hole of anf option ref
```

The notable addition is the `Hole` constructor in `anf`, the purpose of which will be described now.

Imagine we are trying to convert the term

```
let x =
  let y = 2 in
  y + 1
in
x + 2
```

When we arrive at the body of `x`, we have a conundrum. We need to put the conversion of `y` before `x`,
so that using `y` is well-scoped. Hence, we must convert `y` before we can continue. How do we use this conversion, though?
`x`'s content needs to be put in the `anf` field of `y`'s `Let`, so it's not clear how to both convert `y` before `x` and
to use `x`'s finished conversion in `y`.

One "traditional" method of solving this is via continuations, where `y` is passed a closure representing "what to do next", after it
converts its body. We can then put `x`'s content in that closure, which will be invoked later. This has two main flaws:

This method resolves these.

## The algorithm

Recall that we left a `Hole of anf option ref` field in our `anf` type. I will denote a hole like this: `[·]`.
The central idea is that our conversion of any given `ml` fragment will return:

```
val convert : ml -> (anf * string * anf option ref)
```

Consider this simplified example:

```
let x =
  let y = 2 in y + 2
in x
```

When we convert `x`, this signals for the conversion of `y`. There are two steps to converting a `let` - we
must first convert the "head" (`2`), and then the "body" (`y`).

Converting the `head` will result in something of form

```
let y = 2 in 
[·]
```

Note that the hole is left to be filled later. This way, the conversion of `y`'s head need know nothing about its environment.
We represent this in code via the `Hole` constructor, which contains a reference to a fragment that either may be empty (`None`)
or filled (`Some ...`).
The conversion of the body can then proceed by first generating the expected addition, binding it to `nm` so it may be referenced later:

```
let nm = y + 2 in
[·]
```

We now need to get this fragment into the proper lexical scope. We can do this by plugging it into the hole left by the conversion of the head:

```
let y = 2 in
[
  let nm = y + 2 in
  [·]
]
```

Then, returning this fragment, the name bound (`y`), and the reference to the inner hole, we can continue converting `x`;
First, convert the head, using the name returned by the conversion of `y`:

```
let x = nm in
[·]
```

Then, the body:

```
let nm2 = x in
[·]
```

Plug:

```
let x = nm in
[
  let nm2 = x in
  [·]
]
```

And finally plug it into the hole returned by `y`.

```
let y = 2 in
[
  let nm = y + 2 in
  [
    let x = nm in
    [
      let nm2 = x in
      [·]
    ]
  ]
]
```

We are left with a final hole we can plug with `Done` to be explicit about the end of a control flow path.
One disadvantage of this strategy is that it does generate many unneeded names. Most of these can be avoided by carefully special
casing certain `lets`, and the rest can be eliminated via a simple folding pass.

## Implementation

Below is a sample implementation of this algorithm, in OCaml.

```
type ml =
  | Let of string * ml * ml
  | Name of string
  | Int of int
  | Add of ml * ml
  | Print of ml

(* Suffix with ' to dodge OCaml annoyances. *)
type base =
  | Name' of string
  | Add' of string * string
  | Int' of int
  | Print' of string

type anf =
  | Let' of string * base * anf
  | Done' of string
  | Hole' of anf option ref

let fresh_name =
  let counter = ref 0 in
  fun () ->
    incr counter;
    "nm" ^ string_of_int !counter

(* A helper to make an anf fragment of form

   let new_name = base in
   [·]
 *)
let make_let_hole (base : base) : (anf * string * anf option ref) =
  let name = fresh_name () in
  let r = ref None in
  (Let' (name, base, Hole' r), name, r)

let rec convert (ml : ml) : (anf * string * anf option ref) =
  match ml with
  | Name nm ->
                (* Bind to a new name, and return.
                   A case that can be eliminated in most cases.
                   *)
    make_let_hole (Name' nm)
  | Int i ->
    make_let_hole (Int' i)
  | Add (a, b) ->
    (* First, we convert `a` and `b` *)
    let (a_anf, a_name, a_hole) = convert a in
    let (b_anf, b_name, b_hole) = convert b in
    (* We chose a left-to-right evaluation order, so we
       want to put `a` before `b`. Hence, plug `b`'s fragment
       into the hole provided by `a`.
       *)
    a_hole := Some b_anf;
    (* Then, we need a fragment for the addition itself. *)
    let (add_anf, add_name, add_hole) =
      make_let_hole (Add' (a_name, b_name))
    in
    (* We put this in `b`'s hole. *)
    b_hole := Some add_anf;
    (* Finally, we return the whole expression.
       Everything is contained within `a_anf`.
       If the user wishes to refer to the result of this conversion,
       they should use add_name.
       If they wish to plug something into it,
       they should use add_hole.
       *)
    (a_anf, add_name, add_hole)
  | Print body ->
    (* Print is similar. *)
    let (body_anf, body_name, body_hole) = convert body in
    let (print_anf, print_name, print_hole) =
      make_let_hole (Print' body_name)
    in
    body_hole := Some print_anf;
    (body_anf, print_name, print_hole)
  | Let (name, head, body) ->
    let (head_anf, head_name, head_hole) = convert head in
    let (body_anf, body_name, body_hole) = convert body in
    (* We need to bind this let before body to ensure it is
       properly lexically scoped.
       *)
    let let_anf = Let' (name, Name' head_name, body_anf) in
    (* Then fill it as expected. *)
    head_hole := Some let_anf;
    (head_anf, body_name, body_hole)
```

I recommend toying with the conversion yourself, using `utop` or similar.
In the following, I will "clean up" the output slightly, as to not make it unreadable.

If we use our first example term:

```
utop # let term = Let("x", Let("y", Int 2, Add (Name "y", Int 1)), Add (Name "x", Int 3));;
val term : ml =
  Let ("x", Let ("y", Int 2, Add (Name "y", Int 1)), Add (Name "x", Int 3))

utop # convert term;;
(* Cleaned up: *)
(let nm1 = 2 in
let y = nm1 in
let nm2 = y in
let nm3 = 1 in
let nm4 = nm2 + nm3 in
let x = nm4 in
let nm5 = x in
let nm6 = 3 in
let nm7 = nm5 + nm6 in
Hole [·]
, "nm7"
, <empty reference>
)
```

We can then plug the returned hole, as described.
Via some inspection, we can verify this is indeed correct, and conforms to our ANF-like form, as expected.

As mentioned earlier, the large amount of duplicate names can be mitigated through strategies such as
special casing `let _ = <direct base>` and folding passes.

Clearly, the algorithm does not use closures, or any indirect jumps. It does not allocate any more than needed for the representation of
the output program; there is no excessive closure allocation. I do not currently have a good way to test performance on real-world large inputs,
but I have no reason to believe it would not perform better than an equivalent higher-order version.

I believe this method should be extendable to CPS as well, although I have not tried as of the moment. The "usual" higher-order CPS
conversion described in e.g. "Compiling with continuations, continued" looks quite similar to the higher-order presentation
of ANF conversion, so I would be interested in whether it can be similarly massaged into a mutable form.
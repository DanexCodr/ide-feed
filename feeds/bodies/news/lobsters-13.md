Decisions, decisions.  
As I write this, I juggle a handful of nested decisions just to live my life in the next 10 minutes. I am privileged in that the decisions laid out in front of me are ones that support my comfort, each mundane but carrying complex side-effects. It's getting sunny; do I bother to reach into my bag and pull out my hat? If yes, shall I also grab my notebook and draw something? If I'm going to draw something, what should I draw of the infinite possibilities of the beautiful city laid out in front of me?  
I simultaneously risk sunburn and rob the world of a little doodle, by instead writing this.  
One of the primary jobs of a computer is to make decisions, and our subject today involves tracing the steps a compiler can take to determine validity of the choices a program wants to handle. Gleam's compiler is a wonderful and vast piece of craftsmanship, and I would like to take us on a mental stroll through one small avenue of Gleam City: its logic regarding case exhaustiveness.

In the programming language called [Gleam](https://gleam.run), we are able to specify [case expressions](https://tour.gleam.run/flow-control/case-expressions). Within this subset of the language, the purpose of `compiler-core/src/exhaustiveness.rs` is to determine that every pattern presented in a `case` covers every value that the subject could possibly be, and conversely whether there exists a clause that can't ever be exercised because a previous clause already matches the same situation. What a superb piece of User Experience that this is figured out for us at the time a Gleam program is compiled, instead of an unhandled value crashing our program at the time it runs!

```
pub fn to_string(is_cool: Bool) -> String {
  case is_cool {
    True -> "cool"
    False -> "uncool"
  }
}
```

There's the fact of this snippet not compiling if one removes the `False` clause; what's special to me about the logic in `exhaustiveness.rs` is that it will strive to let the user know exactly *what* case is missing, if it can. `"The missing patterns are: False"`, it politely informs me. Providing such a message is no easy feat to achieve, thus exemplifying to me Gleam's commitment to user-friendliness.

Though typed functional languages started growing like weeds in the 1970s, the theory significant to our file starts (at least for me) in ~1984-5, from papers like [Lennart Augustsson](https://en.wikipedia.org/wiki/Lennart_Augustsson)'s on compilation of pattern matching, titled ["Compiling Pattern Matching"](https://www.cs.tufts.edu/~nr/cs257/archive/lennart-augustsson/patmatch.djvu).

> Sidenote: if you read the paper maybe you, like me, will wonder whether Mr Augustsson made a typo with "mathing" instead of "matching", since it occurs multiple times. It is quite a "mathy" topic, after all. Surely there's a joke in here somewhere about our brains' pattern matching.

Augustsson delivers a framework that I find to be the foundation of subsequent work: one should group the clauses of a case expression by a leading constructor, then introduce fresh variables for sub-parts, then for those sub-parts, repeat! It's a great, though somewhat dense read. The latter half of the paper goes into detail on methodology of turning the sub-parts into actual [LML](https://foldoc.org/LML) instructions, such as literal jumps (GOTOs?) for default entries in the nested case maze when a sub-part didn't match anything. In other words, each default would force a retry, and that'd happen at runtime until the top-level default (meaning failure) is reached; the nest had been fully recursed.

> Sidenote: using one's own variant of ML is a massive flex...

I feel the ghostly presence of Augustsson's *jump in case sub-parts didn't match with anything*, when observing behavior of our Gleam `Decision::Switch`. In contrast to ancient history, Gleam is compiled, thus the `Switch` default is a node in actual statically-typed data structure (as opposed to runtime rules). They also de-coupled the two jobs that Augustsson's jumps did in one: `Switch` (retrying, keep matching elsewhere in the nested soup) and `Decision::Fail` as a type instead of implicitly happening once we're out of all other options. The wombo-combo is finding a `Fail` *at compile-time* after the tree is built, which is proof that our initial case expression is inexhaustive. Knowing precisely where a `Fail` happens leads us to `missing_patterns.rs`, which reverses back through the tree to find the specific situation that will never match, in order to bubble it up to the user. Such giant-shoulders to stand on, this concept of a (runtime) assertion of finding out which jumps would eventually fail!

The name of that specific situation which'll never match is what the kids call a "witness", [Luc Maranget](https://pauillac.inria.fr/~maranget/) (click link for cat jumpscare) calling a "counter-example" in his 2007 paper ["Warnings for pattern matching"](http://moscova.inria.fr/~maranget/papers/warn/warn.pdf). We'll come back to witnesses in a second.

> "Programmers sometimes are quite upset in front of “non-exhaustive match” warnings. An example of a “non-matching value” helps a lot not only in convincing them that they indeed wrote a non-exhaustive match, but also in correcting their code." -- Luc Maranget, 2007

From what I can tell when LARPing as some sort of naive functional programming anthropologist, I detect that the 1990s were a functional boom: Augustsson's LML goes on to become part of Haskell [HBC](https://github.com/haskell-implementations/hbc); we got [Clean](https://en.wikipedia.org/wiki/Clean_%28programming_language%29) ('95), [OCaml](https://ocaml.org) ('96), [Erlang](https://www.erlang.org) (open-sourced in '98) to name a few. At the turn of the 21st century it seems to me that we topped-out research on the tree-size aspect of case expressions (that I've barely gone into on purpose), to how ergonomic we can make diagnostics, and how rich we can make our patterns that we match. Leading us to Maranget's paper! The methodology proposed for going about finding the witness is (and I'm sorry for this tangent but it is very interesting):

1. arrange a matrix of subjects as columns and clauses as rows.
2. focus on a given column. (I say "given" and not "the first" because we naturally recurse, just setting that up mentally for later.)
3. do the constructors of the column cover every case that type can be?
  - if not, we're missing a constructor! Turn to step 4 with the missing constructor (or well, oldtypes like numbers and strings usually have too many constructors to put down, so we'll need an "everything else" clause for those. Imagine a stringy case expression that goes `{ "a" -> "my answer 1", "aa" -> "my answer 2", ..ad nauseam}`).
  - if so, that's good at least! For each of the constructors, do step 4.
  - if there's literally nothing in the column, skip the column and back to step 2 for the next column.
4. punch in a layer on a given constructor, specialize it, enter it. `MyType(r), rest...` to `r, rest...`. We're actually now on a new matrix!
5. 
  - if this inner matrix is out of clauses: we've tentatively found a witness, so let's store it and continue. (...with all the other constructors that have to go through step 4).
  - if this inner matrix has clauses but no columns, then we've completed this!
  - anything else: back to step 2 with you.
6. repeat! (Halters put down your pitchforks; every iteration will in fact consume something, the patterns *will* run out.) If we are left with witnesses, voila we have our missing patterns. If we have no witnesses then this case is closed. (Get it?)

> Sidenote: a freaky term.

"Such a joyous carnival ride. How does Gleam go about this matrix?" the reader wonders aloud. First of all okay lollipop-toting spinny-hat-wearing energy, second of all that's the neat part! It doesn't. Instead, Gleam represents clauses as a list of branches, each branch being itself a list of checks literally like `[variable] is [pattern]`, a la [Jules Jacobs' notes](https://julesjacobs.com/notes/patternmatching/patternmatching.pdf) and [Yorick Peterse's implementation](https://github.com/yorickpeterse/pattern-matching-in-rust).

Speaking of tree-building and Maranget, another paper of his is more relevant, as such it is in fact cited (twice!) in today's Gleam code. ["Compiling Pattern Matching to good Decision Trees"](https://www.cs.tufts.edu/~nr/cs257/archive/luc-maranget/jun08.pdf) (Maranget, 2008, a year after the paper just-discussed) deals with, you guessed it, *compiling* trees in such a way as to keep up with the performance of [OCaml's backtracking compiler](http://moscova.inria.fr/~maranget/papers/opt-pat.ps.gz) (which is just the Augustsson nested-jumpy-case-maze?). Backtracking pro: "linear guarantee for code size". Backtracking con: "may scan sub-terms more than once". Maranget shows us the wise ways that we can choose the order in which the clauses are built out into a tree, we can reduce its depth.

Try to favor columns:

- where the first row has a constructor pattern ("pattern" instead of just constructor because I mean not just `True` or `Circle` types but `Ok(x)` and `Ok(False)` etc.)
- with the least wildcards in the column.
- with least amount of children on the switch-node we would create.
- with smallest count of struct fields.
- where we count the maximum rows that must be tested for this given column in general. Like, if we're gonna have to test it eventually, might as well get it over with.
- where the given column is needed sooner in the clause-list rather than later.
- where the given column peters out of being actual constructors later rather than sooner.

As an example of the last column-favoring-method, what we do in practice is, for a given column, look down cell by cell. For each cell, it'll have either a constructor (like a `[]` / `[x, ..rest]`) or that the cell doesn't specifically care (_, r). We'll count down to the first instance of not-caring, and voila, rank columns by their count and order the tree that way!

While Gleam doesn't build the decision-making in the form of a table because it builds whole tree instead (it seems to me that doing the matrix thing would work just fine, but then this way we get diagnostics *and* the base for a JavaScript backend for free), the engine of which test to test next seems to be a combination of two of Maranget's/Jacobs' strategies: choose a variable whose type has fewest constructors (i.e. a list having 2, and an int having infinite), and in case of tie, choose whichever var that more of the remaining checks involve.  
Choosing wisely will ensure the tree is smaller, since the natural state on something like

```
case a, b {
  Some(x), 1 -> "one"
  None, 2    -> "two"
  _, _       -> "buckle my shoe"
}
```

is that our last clause there is going to be copied a bunch times, like so:

(assuming we split out the tree on `a` first)

```
- Some: clause 1, & a copy of clause 3
- None: clause 2, & a copy of clause 3
```

then

```
- Some:
  - b is 1: clause 1, copy of clause 3
  - b is anything: copy of clause 3
- None:
  - b is 2: clause 2, copy of clause 3
  - b is anything: copy of clause 3
```

so 4 copies of our "buckle my shoe" clause, even though some are naturally gonna be useless after the fact anyway, such as the case where `a` and `b` are `Some, 1` wherein clause 1 matches, therefore we know for a fact that the copy of clause 3 can't be exercised. The smaller the tree, the easier it is to go through and find a dead end at compile time that serves as proof not just that there's *an* unhandled pattern, but that traversing back up to trunk will yield our particular missing thing.

The most fun I've had reading the `exhaustiveness.rs` is when going through the functionality that I can't find in any papers (note that I'm not exhaustively saying that they're not in any papers, just hedging my own potential skill issue for not being able to find them). Let's look at a couple of such:

```
case s {
  "lewis" <> rest -> ...
}
```

which introduces a whole new class of situations that can happen, because strings can be subsets of other strings! We're used to dealing with one situation being true in a case expression, right? On top of that, we have these [inline guards](https://tour.gleam.run/flow-control/guards), that make the tree construction quite difficult

```
case s {
 "lewis" <> rest if rest == " likes" -> "lewis likes gleam"
 "lew" <> rest -> "lew-" <> rest
 _ -> "idk"
}
```

where it's not possible to retrace our steps while traversing this as a tree.

- does s start with "lewis"?
  - why yes it does
    - clause 1: guard is true: "lewis likes gleam"
    - guard is false: *uh oh!*
  - no it does not
    - does s start with "lew"?
      - yes: clause 2
      - no: clause 3

Notice the "uh oh". We still *must* try the clause 2 because we know that "lew" is a subset of "lewis". "How do we know that?", you ask. What Gleam does is go through, on that same level, and remember the string prefixes it's seen so far so that it can add any given other shorter prefix into the "uh oh" section of every longer one, to allow it to be tested when we're already deep traversing.

- does s start with "lewis"?
  - why yes it does
    - clause 1: guard is true: "lewis likes gleam"
    - guard is false: *copy clause 2 in here!! Now we can check it.*
  - no it does not
    - does s start with "lew"?
      - yes: clause 2
      - no: clause 3

For reference in `compiler-core/src/exhaustiveness.rs` please check out the `overlap_candidates` and `descendant_candidates` specifically.  
When I look in the commit history, I would say that this string-prefix novelty shines through in the ways it's been massaged to its current happy state, and I'll bet money there's more to explore here before it's done-done. If I'm mistaken in that there is in fact a paper that covers matching based on guards & prefixes/subsets, let me know! Doesn't make this functionality any less cool.

Bit array logic: while ["Efficient Manipulation of Binary Data"](https://user.it.uu.se/~kostis/Papers/JFP_06.pdf) dealt with matching on bit arrays with variable segment sizes, Gleam seems to take it some steps further in accordance with the exhaustiveness of other types. The compiler checks if the pattern is impossible, and remembers if a test has already been performed earlier during traversal. It also decides whether or not to bother emitting generated code that massages/unifies JS and BEAM behavior--for example if it detects the possibility that a given bit array length variable *could be negative* (rather, that it can't be sure that it's *not ever* going to be negative), emitting code to just fall through instead of `raise`ing, and similarly that `NaN`/`Infinity` won't actually match a float segment.

Type-narrowing: take this for example

```
pub fn area(s: Shape) -> Float {
  let shape = Circle(67.0)
  case shape {
    Circle(r) -> 3.14 *. r *. r
  }
}
```

should our compiler complain here due to missing every other shape that a Shape could be? Square, Rhombus, these just a few of the shapes my powerful mind can name. (Applause.)  
Gleam's compiler remembers the specific instantiation of the Shape named `shape` and knows for a fact that it's only ever a Circle, so is happy with this expression. Not only that, but it would duly let us know that we've added a dead branch if we *did* handle cases such as Square here. This also applies to a situation such as

```
pub fn describe(s: Shape) -> String {
  case s {
    Circle(r) -> {
      case s {
        Circle(_) -> "round and awesome"
      }
    }
    Square(side) -> "four sides and boring"
    // ... for my other shapes
  }
}
```

there won't be a warning that the inner case of `s` doesn't handle a Square situation.  
Isn't that neat! The compiler seems to thoroughly make use of practical information it learns as it goes.

Printing specific instances in errors: back to that witness, when a dead-end is found in a tree and we traverse all the way back up to find the root. Gleam doesn't just print that path and call it a day, but the compiler knows the distinct namings that I import my functions, so instead of reporting back to me that I'm missing `farm.Unmilkable(_)`,

```
import farm.{Milkable, Unmilkable}              // it will tell me I'm missing `Unmilkable(_)`
import farm.{Milkable, Unmilkable as TooSkinny} // I'm missing `TooSkinny(_)`
import farm as barn                             // `barn.Unmilkable(_)`
import farm                                     // `farm.Unmilkable(_)`
```

It seems that the actual mechanism for translating into the exact used state is re-used from the type-printer, you know, over on the live LSP side! It has lots of other logic for quality of life such as comma separation for multi-subject cases, shortening label fields, and the printer not printing internal types from other modules (wait hang on actually that's maybe not "quality" and more just some mysterious security model, but I think it's cool).

I must end it here; it's too beautiful of a day to be staring at a computer. I get up: let's follow that warm and fragrant sea breeze. This has been the ways in which Gleam's case exhaustiveness checker amazes me, in how it implements and supersedes the literature it's born out of, and ensures a level of care for the user that I've rarely seen in code. This is just a drop in the Gleam codebase ocean; I could write about almost every file I've encountered so far. I encourage you to study it well too, dear reader, and hopefully take some of its sauce to heart for your own programs!
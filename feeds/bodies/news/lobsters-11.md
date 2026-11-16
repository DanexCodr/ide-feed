I’ve just released [hegel-clj](https://github.com/aphyr/hegel-clj), a Clojure interface for the [Hegel](https://hegel.dev) generative testing library. You can jump right to [the docs](https://cljdoc.org/d/com.aphyr/hegel-clj/0.1.1/doc/readme), but I thought it might be interesting to explain why I want another testing library.

I do a lot of generative testing in Clojure with the excellent [test.check](https://github.com/clojure/test.check). However, using test.check can be frustrating! In particular, complex generators can get stuck during shrinking, leaving me trying to prune down a complex data structure by hand. The culprit is usually `bind`. If you’re not familiar with test.check, Quickcheck, or other libraries in this family, `bind` is a generator which draws some random value, then uses that to construct a *new* generator, which in turn is used to draw some other value.

```
(require '[clojure.test.check :as tc]
         '[clojure.test.check.generators :as tcg]
         '[clojure.test.check.properties :as tcp])
(tcg/bind ; Take a number from `nat`, a generator of small positive
          ; integers.
          tcg/nat
          ; Now with that number, construct a generator of vectors, each
          ; with that many elements.
          (fn [size]
            (tcg/vector tcg/large-integer size)))
```

We can also write this using test.check’s `let` macro, which expands to a series of nested `bind`s under the hood.

```
(tcg/let [size tcg/nat]
  (tcg/vector tcg/large-integer size))
```

This leads to the [canonical example](https://github.com/clojure/test.check/blob/master/doc/growth-and-shrinking.md#gotchas-1) of poor shrinking in test.check. Let’s try to find a vector containing `42`:

```
(-> (tc/quick-check 1000
      (tcp/for-all [xs (tcg/let [size tcg/nat]
                         (tcg/vector tcg/large-integer size))]
                   (not-any? #{42} xs))
      {:seed 1777986545686})
  :shrunk :smallest first)

[0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 42 0]
```

That *does* contain 42, but this vector is *enormous*. Why are there all these zeroes? Once test.check found this vector, surely it could have shrunk it to just `[42]`, right?

The answer has to do with shrink trees. Test.check generators don’t actually return values like `64`. Instead they return a lazily evaluated tree of values: the root might be `64`, and its children might be `[32 48 ... 63]`, and each of *those* children has further children: `32` has children `[16, 24, ... 31]`, and so on. Simplifying a bit, here’s how the tree for large integers [is defined](https://github.com/clojure/test.check/blob/5ba3a25b60cf66ff531db8f44d89145abfacfa5c/src/main/clojure/clojure/test/check/generators.cljc#L228-L237):

```
(defn- shrink-long
  "Given a number x, returns a coll of (x-x, x-x/2, x-x/4, x-x/8, ..., x-1)"
  [^long x]
  (core/let [size (- 64 (Long/numberOfLeadingZeros (Math/abs x)))
             ^longs vals (long-array size)]
    (loop [i 0 n x]
      (if (zero? n)
        vals
        (do
          (aset vals i (- x n))
          (recur (inc i) (quot n 2))))))))
```

So, if test.check finds that `64` violates some property we’re testing, it tries the first child of `64`, `32`. Let’s say that passes the test, so test.check tries the next child of `64`: `48`. If `48` fails, test.check tries its first child `24`, and so on. By performing this depth-first search of the tree, and choosing the branches cleverly, test.check can often quickly shrink an integer to a smaller one that still fails the test.

A similar strategy applies to fixed-size vectors. The tree for a vector like `[2 2]` has children like `[1 2]` and `[2 1]`, based on the trees for each individual element of the vector. This explains why test.check produced a vector like `[0 0 0 ... 42 0]`: it found something like `[91 23 1034543 ... 42 15]`, then shrank the first element to zero, then the second, and so on. The only element it couldn’t shrink was the one that caused our property to fail: `42`. Because our generator `(tcg/vector tcg/large-integer size)` always used a fixed `size`, the tree for that vector always contained `size` elements—in this case, 39.

Hang on! We didn’t just generate fixed-size vectors. We used `bind` to draw a size, then built a vector of that size:

```
(tcg/bind tcg/nat
          (fn [size]
            (tcg/vector tcg/large-integer size)))
```

What kind of trees does `bind` produce? The [code](https://github.com/clojure/test.check/blob/5ba3a25b60cf66ff531db8f44d89145abfacfa5c/src/main/clojure/clojure/test/check/generators.cljc#L125-L142) involves some gnarly higher-order functions, but in essence `bind`’s trees can shrink in two ways. They can shrink the outer value (the `size` returned by `tcg/nat`), or they can shrink the inner value (the vector returned by `(tcg/vector ...)`.

Now imagine `bind` draws a size of `100`, then generates a vector of a hundred elements like `[15 32 42 ...]`. This contains `42`, so test.check begins hunting through the shrink tree. One of the branches it can take shrinks the `size` parameter, starting with `[50, 75, ... 99]`. But if `bind` picks any of those sizes, the vector `[15 32 42 ...]` is useless—it’s the wrong size! So `bind` calls our function with `50` to construct a generator of 50-element vectors, and generates a single vector from that generator. This vector will have *different* random elements, like `[69, 45, 1, ...]`.

If there’s no `42` in the vector of 50 elements, then test.check abandons that branch and moves on to size `75`. It draws a new vector of 75 elements like `[8 7 42 ...]`, and since that contains `42`, it can continue shrinking. But since `42` is an uncommon integer, and test.check draws new elements for each `size`, it is very likely that most sizes will not produce a vector with `42`, and test.check will get stuck with, say, 39 elements. From there it can shrink each element, producing the comically oversized…

```
[0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 42 0]
```

For this vector it’s fairly obvious what’s wrong. But for [nontrivial test.check generators](https://github.com/jepsen-io/particledb/blob/4e911c2d6ebf5ed97becba08c12d754cbbd4da53/src/jepsen/particledb/gen/tc.clj), there might be a dozen nested levels of `bind` with complex downstream consequences. Every one of them offers a place for test.check to get stuck, and the smallest failing case can be devilishly tricky to understand. Experienced test.check users try to avoid `bind` and `let`—but they’re fundamentally inescapable for many problems.

Over in the Python world, the [Hypothesis](https://hypothesis.works/) team took a very different approach to shrinking. Test.check is fundamentally a two-phase system: first it asks a generator to produce a shrink tree. Then, if the root of that tree looks “bad”, it explores the rest of that tree. Instead, Hypothesis generators produce a single value, and if that value looks bad, they re-run the generator and [ask it to produce something similar, but smaller](https://drmaciver.github.io/papers/reduction-via-generation-preview.pdf). This approach, called *internal test-case-reduction*, is the foundation of [Hegel](https://hegel.dev/).

## [Hegel-clj](https://aphyr.com/posts/428-announcing-hegel-clj#hegel-clj)

Hegel is a new cross-platform library for generative testing. It provides deterministic generators which draw random values from an imperative, structured RNG, as well as a rich family of special values and shrinking tactics. Writing these generators and shrinkers is hard. The idea is that Hegel’s core library will do this hard work once, and simpler wrapper libraries will extend the benefits of that hard work across many languages.

I’ve been working for a few months on [hegel-clj](https://github.com/aphyr/hegel-clj), which offers Clojure bindings for Hegel, and I think it’s ready for the folks to try it out. To test something, you call `hegel-clj/test!`, draw some values from generators, and throw an exception if the test fails. Hegel searches for values that make that body throw, then shrinks them.

```
(require '[hegel-clj [core :as h] [generator :as g]])
(h/test! {:seed 4}
  (assert (even? (h/draw! (g/integer)))))

{:passed? false
 :status :failed
 :statistics {:total 34
              :valid 5
              :invalid 0
              :overrun 18
              :interesting 11}
 :health-check-failed? false
 :failures ({:draws {"draw_1" 1}
             :exception
             #error {:cause "Assert failed: (even? (h/draw! (g/integer)))"
                     ...}})
 :reproduce-blob "AAEAAAAACgEAAAAB", :caveat nil}
```

The smallest case Hegel found involved a single draw of the number `1`, which caused the assertion `(even? 1)` to throw.

Generators are pure, composable structures, just like in test.check. Here’s a vector of booleans:

```
(h/sample 5 (g/boolean))

[false false true true false]
```

Or a map representing a person, with a name generated by a regular expression and an integer age:

```
(h/sample 5 (g/hmap {:name (g/regex-str #"[A-Z][a-z]+")
                     :age  (g/integer 0 101)}))

[{:name "Aa", :age 0}
 {:name "Iyjdklppzxhqdnwmd", :age 89}
 {:name "Kslvqorm", :age 64}
 {:name "Fvyybe", :age 45}
 {:name "Puwppxqag", :age 4}]
```

The higher-order combinators are all there too. You can transform generated values with `fmap`:

```
(h/sample 5 (g/fmap keyword (g/string)))

[: :R :👍🏻 :True :çç¦ç¦򜝉ÏÏ򜝉¦¦Ï¦¦ç򜝉Ï¦ç򜝉çÏ򜝉çç¦]
```

Or build one generator out of another using `bind`:

```
(h/sample 2 (g/bind (fn [size]
                      (g/tuple (g/vector size (g/integer))
                               (g/vector size (g/boolean))))
                    (g/integer 0 3)))

[[[] []]
 [[144229 531621 -364 -1569883 8194954 -913 16 -745]
 [false true false true]]]
```

Like test.check, we offer a `let` macro which lets you bind both regular values or generators to variables; if the right-hand side is a generator, it draws a random value from it. And unlike test.check, these generators shrink well. Instead of thirty-nine elements, Hegel can find the much-shorter “bad” vector, `[42]`.

```
(-> (h/test! {:test-cases 1000
              :seed       1777986545686}
      (h/let [size (g/integer {:min 0, :max 128})
              xs   (g/vector {:size size} (g/integer))]
        (assert (not-any? #{42} xs))))
    :failures first :draws (get "xs"))

[42]
```

With `test.check`, if you want to thread multiple values through `bind` or `fmap`, you have to build and destructure maps or tuples. Hegel-clj lets you lift arbitrary code into a generator using `composite`, which makes it easier to build complex generators:

```
(h/sample 2
  (g/composite
    (h/let [name      (g/string)
            cat-count (g/integer 0 2)
            cats      (g/vector {:size cat-count, :unique? true} (g/string))]
      {:name name     
       :cats cats})))

[{:name "",
  :cats []}
 {:name "𝐓𝐡𝐞 𝐪𝐮𝐢𝐜𝐤 𝐛𝐫𝐨𝐰𝐧 𝐟𝐨𝐱 𝐣𝐮𝐦𝐩𝐬 𝐨𝐯𝐞𝐫 𝐭𝐡𝐞 𝐥𝐚𝐳𝐲 𝐝𝐨𝐠",
  :cats ["🇺🇸" "👍🏻"]}]
```

You can build recursive generators with a promise-style API. The `deferred` generator provides a blank space for a generator, which can be filled in later:

```
(let [leaf (g/integer 0 9)
      tree (g/deferred)]
  (g/set-deferred! tree (g/one-of [leaf (g/vector tree)]))
  (mapv prn (h/sample 5 tree)))

0
[[1] 8 [2 []] 5 [] [[4 6 []]]]
[[1] 2]
3
0
```

And best of all, `hegel-clj` ships with easy-to-use integration for clojure.test, making generative tests as easy as example-based ones:

```
(require '[clojure.test :refer :all] '[hegel-clj.clojure-test :refer [with]])

(defn bad-add
  "Adds two integers via floating-point"
  [x y]
  (long (+ (float x) (float y))))

(deftest bad-add-test
  (with {:test-cases 100}
        [x (g/integer)
         y (g/integer)]
    (h/fprn :x x, :y y)
    (is (= (+ x y) (bad-add x y)))))

(bad-add-test)

:x 0 :y 16777217

FAIL in (bad-add-test) (form-init7301103820420620476.clj:6)
expected: (= (+ x y) (bad-add x y))
  actual: (not (= 16777217 16777216))
```

It’s hard to log debugging output with test.check—you’ll have to sift through thousands of test runs with complex inputs, and many of those runs won’t actually trigger the bug you’re searching for. Hegel has the notion of a “final” test case: after it’s found a counterexample, and shrunk it to a smaller version, it comes back and re-runs that case as a part of the final phase. We can use `(when (h/final?) ...)` to execute some debugging code only during these final cases, or `fprn` and `finfo`, which wrap `clojure.core/prn` and `clojure.tools.logging/info` respectively. I think there’s a [bug in Hegel](https://github.com/hegeldev/hegel-java/issues/32) that causes it to run more final cases than it should, but it’s still a big step up.

Finally, test.check has been around for a while, and like many Clojure projects it has an exceptionally stable API. That’s great for compatibility, but it means some early choices are now fossilized. It’s `(fmap gen f)`, but `(bind f gen)`. If you want an integer you have to remember the difference between `nat`, `int`, `pos-int`, `s-pos-int`, `small-integer`, `large-integer`, `large-integer*`, etc. Common generators require keyword arguments, like `(large-integer* {:min 0, :max 10})`. Some generators like `hash-map` are only callable with varargs, which makes composition tricky. The [properties API](https://clojure.github.io/test.check/clojure.test.check.properties.html) feels a tad fussy. And many of the ergonomic features you want, like generating strings from a regular expression, or integration with clojure.test, require an extra library like [test.chuck](https://github.com/gfredericks/test.chuck). Test.check is *really good*, but with the benefit of hindsight and a fresh canvas, I’ve tried to design a more streamlined, consistent, and approachable API.

I’ve used test.check for over a decade now and it’s one of my favorite things about Clojure. I want to thank Reid Draper, Gary Fredericks, Alex Miller, and everyone else who’s contributed to the library. I’m also indebted to David MacIver, Liam DeVoe, and Esau Rodriguez from the Hegel team at [Antithesis](https://antithesis.com/). They took time to talk me through Hegel’s design, answered endless questions about the protocol, and helped fix a whole slew of issues that we found. Y’all rock.

I’m pleased to announce [hegel-clj 0.1.1](https://github.com/aphyr/hegel-clj), and I’m starting to use it to test my own projects. I hope it will be useful for you too. ❤️
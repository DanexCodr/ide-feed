I learned this as part of my work on [Yabu](https://dziban.net/posts/yabu/). There I need to work
recompile, regenerate code and type-check at interactive speeds.

The implementation is based on [Salsa](https://salsa-rs.netlify.app/)

### Main Ideas

You have two main things in the algorithm:

- Inputs, mutable, the only source of external change. The system sets these and then consumes from:
- Computations, pure functions of inputs or other computations, these are memoized and invalidated by the red-green walk.

For example, in the case of Yabu an input would be the function definition.
Let’s say you already have an image and you redefine a function.

```lisp
(defun some-func ((a int) (b int)) int 
  (+ a b))
```

The source string of this function would become an input and then from there you
have defined several pure computations.

For example we can have a parse function, it depends on the source input and
returns the AST of the source. Because this is a pure function, if the input
hasn’t changed we can just return the memoized AST without having to re-parse it.

```lisp
(define-computation parse (source)
  (yabu:parse source))
```

Now this gets interesting once you start composing computations, this looks very
similar to regular functions calls except these internally keep track of which
computations you are calling. Creating a runtime-graph of dependent computations.
We’ll use this graph later to invalidate computations once inputs change.

```lisp
(define-computation compile (source)
  (let* ((typecheck-result (typecheck source)))
    (if (errorp typecheck-result)
        typecheck-result
        (yabu:compile ast))))
```

> *NOTE:* This is not a correct compile function for Yabu, because you are only
> checking if this function typechecks against the rest of the functions not if
> the rest of the functions typecheck against this function. We are also skipping
> around some complications around the staging system.
>
> You can check the real algorithm at [Yabu Incremental
> Typesystem](https://dziban.net/posts/yabu-incremental-type-system/)

Here `parse`, `typecheck` and `compile` are all computations. These create a
runtime graph where we see that compile `<source>` depends on `typecheck`, which
will in turn probably depend on `parse` and it will probably depend on another
computation `type-signature` for all of the functions the AST calls.

```
                   compile(source) ----.
                                       |
                                       v
           parse(source) <------ typecheck(ast)
                                       |
              .------------------------+------------------------.
              v                        v                        v
      type-signature(f_1)      type-signature(f_2)   ...   type-signature(f_N)
```

Now if `f_1` changes type signature, automatically the typecheck of this
function will get invalidated! This invalidation is key to make the Yabu
typechecker very fast for interactive use even in large programs.

### Red-green walk

Each memoization entry stores several things:

- The return value (the memoized value)
- The verified-at revision, when was this memoization last-confirmed valid
- The changed-at revision, when was this memoization value last changed
- The dependency list, basically the dependency graph. In the case of compile above it would be typecheck(source). In the case of typecheck(source) it would be parse(source), and type-signature(f_1)..type-signature(f_N) for example.

For each dependency we track also what was the `changed-at` revision of the
*dependency* when we depended on it.

So let’s see an example, we just redefined `some-func` as above and we call
`(compile "<source>")`, this is a new source so there is no memoization for
this, we execute the computation function. We call `typecheck`, since this is a
new `source` this doesn’t exist either, that depends on `parse` which also
doesn’t exist, that creates one memoization entry:

```lisp
(:key '(parse source) 
 :return <ast> 
 :verified-at :R7 
 :changed-at :R7 
 :dependency-list '((:input source)))
```

We then check `type-signature` for `+` with is `(-> (int int) int)` with a
`:verified-at` and `:changed-at` of `R1` (this is stdlib, so it was populated at
the start of the session). Since `R1` is less than `R7`, it may be outdated and
we need to check the dependencies of `(type-signature +)`. That depends on the
source of `+` which also has a revision of `R1`. Since the revision of the
memoization and the revision of its dependency are equal we consider it fresh
and we update the `:verified-at` for `(type-signature +)` to the current
revision of `R7`.

The typecheck passes so we memoize that as well and create an entry like

```lisp
(:key '(typecheck source)
 :return <pass|fail>
 :verified-at :R7
 :changed-at :R7
 :dependency-list '((parse source) (type-signature +))')
```

It’s important here to note when we consider something fresh:

- It’s either when :verified-at == current-revision
- Or, when the dependencies are inputs where :changed-at < current-revision

You always need to walk the dependency chain until you bottom out at the inputs
or you have already validated the subtree this revision.

During the walk as you come up the recursion you update all `:verified-at` to
`current-revision` so any other computation in this revision short-circuits.

Next time, if we reevaluate `typecheck` over the same source we’ll recurse
through the graph, arrive at the same input, check that it hasn’t changed, go
upwards the computation tree, updated `:validated-at` and skip typechecking and
compiling altogether.
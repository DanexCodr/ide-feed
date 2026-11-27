I recently finished adding support for idempotency tokens to
`amazonka` (the unofficial Haskell AWS SDK), using the [client
token support provided by AWS](https://docs.aws.amazon.com/ec2/latest/devguide/ec2-api-idempotency.html). Implementing this required making
some fairly substantial changes to the generator, the bespoke Haskell
program that turns the service definitions in [`botocore`](https://github.com/boto/botocore/) into
cabal packages. `amazonka` is over a decade old, and the
generator has evolved as AWS have added new styles of APIs for their
different services. Some services return XML, some return JSON, some
return raw bytes, some return additional information in HTTP response
headers, and so on. As a result, the generator’s logic had been extended
each time and had grown gnarly.

To untangle things, I resolved to make one of my favourite
programming moves, “make the plan a value” or “decide what to do, and
then do it”. This move decouples two parts of a program by introducing
an intermediate data structure (a “plan”, or a value of a “plan type”)
describing *what* is to be done before any action is taken.

I really like this pattern because the “deciding what to do” part of
a program is often more complicated than the “doing” part. Separating
the two often turns the “deciding” part into a pure function that
produces a plan, making test cases simpler to write. And then if the
“doing” phase is also complicated (because of remote API calls,
rollbacks, parallel execution, or whatever else), it’s more manageable
because those complications are not entangled with the planning logic.
You also get to add a `--dry-run` flag almost for free, which
is [really
useful for testing](https://henrikwarne.com/2026/01/31/in-praise-of-dry-run/). (Henrik observes that testing for a
`dryRun` variable everywhere pollutes the code somewhat. I
think if he split his code into a planning phase and consumed that plan
with either a “dry run” printer or a “real” executor, the inline checks
that he dislikes would disappear.)

This technique isn’t subtle or obscure. I’ve seen it called [the plan-execute
pattern](https://mmapped.blog/posts/29-plan-execute), and the [“routing
slip” enterprise integration pattern](https://www.enterpriseintegrationpatterns.com/patterns/messaging/RoutingTable.html) is literally about centralising
the decision logic before execution. I’ve previously called it a [“tiny DSL”](https://jackkelly.name/blog/archives/2020/04/03/the_power_of_tiny_dsls/),
and Matt Parsons sells its benefits in his [Three
Layer Haskell Cake](https://www.parsonsmatt.org/2018/03/22/three_layer_haskell_cake.html) article:

> Often times, a simple non-recursive sum type “command” suffices as an
> interface between a pure function and an effectful one. A list of
> commands adds a lot of flexibility without dramatically complicating
> things.

Having resolved to introduce a plan type, how do we work it into a
venerable program like the Amazonka generator? For this part of the
generator, it means separating the analysis of the loaded service
definitions from the generation of the `instance AWSRequest`
declarations. I did this by introducing a `Config` record of
simple data and a function
`instanceD :: Config -> Decl ()` that builds Haskell code
from that config record.

I found the generator’s logic too difficult to understand and replace
in a single change, so I replaced it incrementally using the [strangler
fig pattern](https://martinfowler.com/bliki/StranglerFigApplication.html). The most complicated part of this change was response
parsing, so I added to the `Config` record an enumeration of
ported response parsers, and a fall back to “do things the old way” for
everything else:

```
-- | How to generate the parser for AWS's response to an API call.
data ResponseParser
  = -- | Perform no parsing and return an empty response. The response
    -- constructor in 'responseType' must take no arguments.
    ParseNull
  | -- | Parse the entire response as JSON.
    ParseAllJSON
  | -- | Parse the entire response as XML, with an optional wrapper.
    ParseAllXML (Maybe Text)
  | DoItTheOldWay
```

One thing that makes Amazonka’s generator rewarding to hack on is
that the service bindings act as an extensive and automatic [golden test](https://cs-syd.eu/posts/2023-12-21-golden-tests)
suite. Any changes to the generated bindings show up in diffs, and so if
there are no diffs and the generator doesn’t crash, the change probably
didn’t break anything. This makes the process of replacing the entangled
code relatively simple (not easy):

The end result [worked
well](https://github.com/brendanhay/amazonka/blob/546b030e38b12972bef6c39c68c439cd3e64c4aa/gen/src/Gen/Output/Operation/AWSRequest.hs#L33-L163) and kept the individual commits readable (example: [factoring
out status code parsing](https://github.com/brendanhay/amazonka/commit/6638af1f9d15994c600086c16b3187ccb4a651b5)). Adding the idempotency machinery was then
[straightforward](https://github.com/brendanhay/amazonka/commit/fd0d2cff0b479132a76e8c56453907837cb436ca).

The data types in the Amazonka example represent parameters to a
Haskell code template, but this refactoring also works for more
expressive plan types, such as “tiny DSLs”, “lists of commands”, or
“free structures”. The trick is to keep a “do it the old way”
constructor in your plan type until the “old way” has been refactored
away.

A well-chosen plan type introduces a [narrow
waist](https://www.oilshell.org/blog/2022/02/diagrams.html) that decouples producers and consumers of your plan type, and
the most obvious wins come from introducing alternate consumers of the
plan: things like testability, `--dry-run`, and simpler
executors all follow from that. A less obvious benefit is that you can
also analyse and transform the plan itself. This is a great place to add
pre-execution sanity checks or access controls. I regret that [my tiny DSLs
post](https://jackkelly.name/blog/archives/2020/04/03/the_power_of_tiny_dsls/) inverted a transformation by interpreting it as matrix
multiplications and inverting the result; it would have been simpler to
provide an `invert :: [Transform] -> [Transform]`
function.

Introducing alternate producers of the plan type can also pay off,
but needs a bit more imagination:

“Making the plan a value” works well in any language, but Haskell’s
laziness makes it especially nice. Lazy evaluation can avoid
materialising the whole plan in memory if it is consumed right away.
Even in strict languages, the decoupling benefits are great enough that
the extra memory use is often worth it.
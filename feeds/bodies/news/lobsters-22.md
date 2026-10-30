In async Rust the `Future::poll` method is called to progress the state of the future, which reports its progress via the `Poll` enum. This enum contains two variants:

- Poll::Pending: means that the future is not yet ready to produce a value, and poll will need to be invoked again later.
- Poll::Ready(T): means the future is ready to yield some value T.

Futures are called that because they will eventually resolve to a value, *in the future*. But that’s value singular, not values plural. The stdlib documentation does not clearly make this guarantee (though it should), and the ecosystem doesn’t always implement this correctly (though it also should). But the intent is clear: one future should only ever yield one value.

Now what should happen when you try and call `Future::poll` again after it has already yielded a value? The `Future` trait docs have the following to say:

> Once a future has completed (returned `Ready` from `poll`), calling its `poll` method again may panic, block forever, or cause other kinds of problems; the `Future` trait places no requirements on the effects of such a call. However, as the `poll` method is not marked `unsafe`, Rust’s usual rules apply […].

The docs state here that if you call `Future::poll` again after it’s yielded
`Poll::Ready`, that’s unsupported and there aren’t many limits on the future’s
behavior. The most common behavior here is to `panic!`, which is the behavior
for all `async` blocks and functions. Which is a shame, since being able to call
`Future::poll` again after it’s yielded `Ready` before is actually quite useful
and something I frequently wish I was able to do.

## MaybeDone

Not everyone writing Rust writes async Rust, and not everyone writing async Rust will write async concurrency primitives. But those who do will be familiar with the `MaybeDone` type. It’s a simple wrapper around some `Future` whose only job it is to either hold a `Future` or if it's completed hold its `Future::Output`. While not simple, assuming you're familiar enough with async Rust it should be easy enough to follow:

```rust
use pin_project::pin_project;
use std::future::Future;
use std::pin::Pin;
use std::task::{Context, Poll};

#[pin_project(project = DoneState)]
enum MaybeDone<F: Future> {
    Future(#[pin] F),
    Done(Option<F::Output>),
}

impl<F: Future> MaybeDone<F> {
    pub fn take(self: Pin<&mut Self>) -> Option<F::Output> {
        match self.project() {
            DoneState::Done(output) => output.take(),
            DoneState::Future(_) => None,
        }
    }
}

impl<F: Future> Future for MaybeDone<F> {
    type Output = ();

    fn poll(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<()> {
        match self.as_mut().project() {
            DoneState::Future(future) => match future.poll(cx) {
                Poll::Pending => Poll::Pending,
                Poll::Ready(output) => {
                    self.set(Self::Done(Some(output)));
                    Poll::Ready(())
                }
            },
            DoneState::Done(_) => Poll::Ready(()),
        }
    }
}
```

In essence what this provides is a slot that holds either a future, or its final resolved value. And in doing so it also performs another trick: it replaces the output of the future with the unit type and adds a new method `take` to actually extract the value of the future.

When attempting to call `Future::poll` again after it has returned `Poll::Ready(())` once before, it will always continue to return `Poll::Ready(())`. And if you call the `take` method again after having received `Some(Future::Output)` before, it will keep returning `None` forever after.

What is a relatively straightforward way of creating a slot that holds either a future or its output value has an interesting side effect of actually being able to communicate the state of the future even after it has yielded a value once. If a caller observes `Poll::Ready(())` + `None`, that means the future is done and will not be yielding a value again.

## Fixing Poll

`MaybeDone` isn’t the only API in the `futures` crate which tracks the done state of a
future. The `FusedFuture` trait provides an `is_terminated` method, and its `Fuse`
adapter keeps returning `Poll::Pending` once the inner future has returned
`Poll::Ready`. However this unfortunately abuses `Poll::Pending`, whose docs state:

> When a function returns `Pending`, the function *must* also ensure that the current task is scheduled to be awoken when progress can be made.

This definition is incompatible with how `Fuse` uses `Pending`, and so bringing
it into the stdlib would require redefining `Pending` to mean both “pending” and
“done”. This feels bad, because if you forget to call `is_terminated` first, the
future will hang forever. There are other hacky schemes we could apply instead,
but the right way to fix this would be by making the `Done` state a part of
`Poll` itself:

```rust
pub enum Poll<T> {
    Ready(T),
    Pending,
    Done,    // ← new
}
```

Unfortunately we can’t make this change since `Poll` is not marked
`#[non_exhaustive]`. Which is a shame since instead of panicking or hanging,
futures would actually have an opportunity to share that they have nothing more
to report. This would change the responsibility of what to do with that
information from the callee to the caller. The caller might still choose to
panic, but it could also forward the `Done` state, or in concurrency operations
like `join` it could now be used to track which futures have completed, without
needing `MaybeDone`.

This would also have the benefit that it removes the implicit dependency of the
async effect on the panic effect. The compiler can guarantee that calling
`.await` never polls after getting `Ready`, and so it doesn’t need to handle the
`Done` state. With this in place, `async` functions and blocks would no longer
need to inject unwinding support on every path, reducing the codegen size which
especially benefits embedded targets. It would also work well with the
`no_panic` crate on crates.io, or an eventual function/block-level no-panic
annotation.

## Fixing CoroutineState

The `CoroutineState` enum has the same problems as the `Poll` enum, in that it cannot express a final `Done` state. But unlike `Poll`, the `Coroutine` trait and `CoroutineState` enum aren't stable and so can be fixed without any breakage.

Since `Coroutine` is used internally in compiler desugarings, these changes might still not be easy. But at least we don’t have to repeat the same mistakes we've made for async with iteration as well.

To better illustrate the problem with `CoroutineState`, here is how it is defined today:

```rust
pub enum CoroutineState<Y, R> {
    Yielded(Y),
    Complete(R),
}
```

[The documentation](https://doc.rust-lang.org/std/ops/enum.CoroutineState.html) has the following to say about the `Complete` variant:

> Once a coroutine has returned `Complete` it is considered a programmer error to call `resume` again.

`resume` here refers to `Coroutine::resume`, which drives the progress of the coroutine similar to `Iterator::next` and `Future::poll`. But just like with futures (and unlike iterators<sup>[1](https://blog.yoshuawuyts.com/the-future-trait-has-a-missing-state#unlike)</sup>), coroutines are unable to express a “done” state.

Technically `Iterator::next` returning `None` is no guarantee that `None` will keep being returned. But at the very least returning `None` repeatedly is fine and expected, and so it’s a valid way of encoding a “Done” state, which is what `FusedIterator` does.

This means that we cannot define a generic `FusedCoroutine` trait like we have with [`FusedIterator`](https://doc.rust-lang.org/std/iter/trait.FusedIterator.html). Since `Complete(R)` takes a generic param we could of course require that `Complete(Option<R>)`, but that would again be dancing around the problem. This is a problem we know we have, we know how to solve, and so we should solve:

```rust
pub enum CoroutineState<Y, R> {
    Yielded(Y),
    Complete(R),
    Done,         // ← new
}
```

This does leave us with some confusing names. `Complete` here is not the same as `Done`. So I would propose we name the variants after the operations they represent, just like we’ve done with `ControlFlow` (`Break|Continue`):

```rust
pub enum CoroutineState<Y, R> {
    Yield(Y),   // ← renamed 
    Return(R),  // ← renamed
    Done,    
}
```

## Even more states

So far we’ve covered the three future states: `Ready`, `Pending`, and `Done`.
These are the three states we communicate *externally*. But internally there
is one more state: `Start` or `Init`. This is the state a future is in *before*
it is first polled. But since we never yield that state, it’s internal-only.

Another state we haven’t covered here is the state *before* the future or
coroutine is initialized. In async Rust `.await` calls the
`IntoFuture::into_future` method before polling the future, just like when
iterating the `for..in` notation calls `IntoIterator::into_iter` before calling
`Iterator::next`.

I’m not sure what to call this pre-state, but its purpose is to capture inputs
without needing to instantiate locals. Unfortunately `async {}` currently
returns `impl Future` rather than `impl IntoFuture`. In [the gen auto-trait
problem](https://blog.yoshuawuyts.com/gen-auto-trait-problem) I explained how
that would help us create more precise bounds and solve a number of `Send`/`Sync`
interactions. While changing the desugaring of `async {}` is tricky, `gen {}` is
still unstable and is much easier to change.

Finally, in [Never Snooze a Future](https://jacko.io/snooze.html) Jack O’Connor
describes what ought to be an invalid future state: “Snoozed”. A future is
snoozed when it is ready to make progress, but it’s not polled. I think of this as
a way of translating the [“bbbs”
scenario](https://rust-lang.github.io/wg-async/vision/submitted_stories/status_quo/barbara_battles_buffered_streams.html)<sup>[1](https://blog.yoshuawuyts.com/the-future-trait-has-a-missing-state#bbbs)</sup>
into a liveness property.

Barbara Battles Buffered Streams

Futures [naturally form
trees](https://blog.yoshuawuyts.com/tree-structured-concurrency). The
“snoozed” state applies when some child future’s waker is called, and its parent is
polled but the child isn’t. This leads to a rule that we can apply recursively
to every future: *“When a future is polled, it must also poll all child futures
that have had their waker called.”* If every future follows this rule, no future
will ever be snoozed.

## Conclusion

The fact that futures are unable to signal being done is a problem, and one
which has no good workarounds. Types like `MaybeDone` can work around this
limitation on use, but do so by introducing redundant bookkeeping.

Tracking the completion status of futures is necessary for the implementation of
nearly all async concurrency operations. Instead `async {}` blocks desugar to
futures which panic when polled again after completion. This creates problems in
constrained environments like embedded and web where code size matters.

We cannot fix the `Future` trait without deprecating the existing `Future::poll`
method. This post is the fourth entry in my series analyzing problems with the
`Future` trait, and even so I don’t think that’s enough yet to warrant replacing
what we have. What we can do however is make sure we don’t repeat the mistakes
we made in `Future`, for example by fixing the `Coroutine` trait and `gen`
keyword.
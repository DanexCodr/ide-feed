*In which I express frustration at the widespread FUD caused by ambiguous errors in the software we write and consume.*

Have you ever written or encountered something you think would be an “ambiguous error”? No? How about `HTTP 500 Internal Server Error`? `-EINVAL`? `Status.INTERNAL`? Or even a `{"status": "error"}`?

Ambiguous errors, that is errors that are represented opaquely, are quite literally *everywhere*. Compared to happy-path return values, errors have long been second-class citizens across all software. I always felt that this was some abstractly “bad” thing, but it wasn’t until recently that I was able to put substance behind these feelings.

Software has boundaries, whether that be between my application and the libraries it consumes, the operating system it runs atop, or the remote services it calls out to. Boundaries are powerful! They let us hide immense complexity behind simple contracts — AWS S3 being the canonical example. But across a boundary, the only information I have to act on is exactly what you return to me.

So I’m left with two bad options. I can reverse-engineer your errors, in the process becoming a hated [Hyrum’s Law](https://www.hyrumslaw.com/) perpetuator. Or I can throw up my hands and treat every `catch` or `?` as if I were passing around a bomb. We consume tons of high quality, rigorously tested software, but can’t take advantage of it, because we don’t understand how it fails.

Worse, ambiguous errors are viral. Once you’ve consumed one, re-establishing what actually went wrong is far more work than just passing it forward. So you don’t try, and now *your* callers have the same problem.

Even Rust, with great support for strongly typed errors, isn’t immune. `io::Error` wraps the OS’s `errno`, itself a “god error” kept in line by the Linux kernel’s (very good!) docs. A `NotFound` from `fs::remove_file` is something most callers would consider a success, yet most code just `?`s it upwards alongside everything else.

The usual Rust advice is `anyhow` for applications and `thiserror` for libraries, but every application can become somebody else’s library! Typed errors should become part of your API. Adding new error variants *should* be considered breaking changes. How your software fails *is* part of its contract.

Software can fail in countless ways, but a caller can only do a handful of things about it: retry, fix its input, give up, or blame someone else. Errors should encode enough meaning to fill in those gaps.

More concretely, at [[-1] Modal](https://modal.com)  we encounter an amusing variation of this. Running rollouts for Reinforcement Learning involves constructing sandboxed working environments, and when one fails, the trainer should be aware of *how*. Infrastructure failures should be thrown away, lest they bias training. But a reward-hacking model may simply learn to crash its sandbox if it thinks things are going sideways, in an attempt to escape penalization. Adding an error contract to this model allows the trainer to understand and account for these errors.

Writing the contract forces you to answer questions like “How exactly does my software fail?” and “How might someone want to react to those failures?“. You may find that your application *can’t* fail in a way your interface hinted was possible, or that you yourself can be more resilient to upstream failures. With agentic coding assistants, it’s more and more possible to actually do this exercise. List out every error from the leaves of your execution graph upwards, eliminate the ones that don’t make sense, and add stronger types to the rest.
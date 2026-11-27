There’s recently been some discussion about the benefits and downsides of lock (mutex) poisoning in Rust, spurred by [a recent proposal](https://github.com/rust-lang/rust/issues/149359) to make the default mutex non-poisoned, i.e. **silently unlock on panic** (see also, [recent discussion on Hacker News](https://news.ycombinator.com/item?id=46036883)). As a passionate defender of lock poisoning, I thought I’d gather and write about my thoughts on this matter.

To summarize, I believe:

- Unexpected cancellations in critical sections cause real harm to system correctness.
- Lock poisoning is an important part of ensuring the correctness of critical sections in Rust.
- Poisoning applies more generally than mutexes, and providing an easy way to track that (via e.g. a Poison<T> wrapper) is valuable.
- While there is conceptual elegance in separating out locking from poisoning on panic, the importance of lock poisoning overrides these concerns.

## What is poisoning?[#](https://sunshowers.io/posts/on-poisoning/#what-is-poisoning)

Rust, like most multithreaded languages, has [mutexes](https://doc.rust-lang.org/std/sync/struct.Mutex.html): a construct to ensure that a particular piece of data can only be accessed by one thread at a time. The way mutexes work in Rust is particularly well-considered:

- Rust uses a single-ownership model, and the notion of shared (&) and exclusive (&mut) references to some data. Most data structures are written such that mutations always require a &mut reference to it.
- In Rust, the data guarded by a mutex is owned by the mutex. (In many other languages, you have to track the mutex and data separately, and it’s easy to get it wrong.)
- When you lock a mutex, you start from a shared reference: a &Mutex<T>. Once you have obtained the lock, you get back a `MutexGuard<T>`, which indicates that you now have exclusive access to the guarded data.
- The MutexGuard can give you a &mut T, so you have exclusive access to it.
- When the MutexGuard is dropped, the lock is released. The period during which the lock is held is called the critical section (generally, not just in Rust).

This is all quite reasonable! Let’s look at an example that processes incoming messages for a set of tracked operations. Let’s assume that multiple threads could be processing messages, so we have to guard the internal state with a mutex. (We’ll discuss alternative approaches to this problem later.)

A simple implementation:

```rust
use std::{collections::HashMap, sync::Mutex};

struct OperationId(/* ... */);

enum OperationState {
    InProgress { /* ... */ },
    Completed { /* ... */ },
}

impl OperationState {
    // Here, `process_message` consumes self and returns self. In practice this
    // is often because the state has some internal data that requires
    // processing by ownership.
    fn process_message(self, message: Message) -> Self {
        match self { /* ... */ }
    }
}

struct Operations {
    ops: Mutex<HashMap<OperationId, OperationState>>,
}

impl Operations {
    /// Process a message, updating the internal operation state appropriately.
    pub fn process(&self, id: &OperationId, message: Message) {
        // Obtain a lock on the HashMap.
        let mut lock = self.ops.lock().unwrap();

        // Once the lock has been acquired, it's guaranteed that no other
        // threads have any kind of access to the data. So a `&mut` reference
        // can safely be handed to us.
        // 
        // This step is shown for pedagogical reasons. Generally, `ops` is not
        // obtained explicitly. Instead, lock.remove and lock.insert are used
        // directly as `lock` dereferences to the underlying HashMap.
        let ops: &mut HashMap<_, _> = &mut *lock;

        // Retrieve the element from the map to process it.
        let Some(state) = ops.remove(id) else {
            // (return a not-found error here)
        }
        let next_state = state.process_message(message);
        ops.insert(id.clone(), next_state);

        // At this point, lock is dropped, and the mutex is available to other
        // threads.
    }
}
```

This is a very typical use of mutexes: to guard one or more *invariants* or *properties* of some kind. These invariants are upheld while the mutex is unlocked. In this case, the invariant being guarded is that `Operations::ops` has complete and up-to-date tracking of all in-progress and completed operations.

Of equal importance is the fact that, while the mutex is held, the invariant is *temporarily violated*. In order to process the message, we have to remove the state from the map, create a new state, then put it back into the map. During this period, `Operations::ops` is missing this one operation, so it no longer tracks all operations. But this temporary violation is okay, because no other threads see this in-between state. Before the mutex is released, this code is responsible for putting the operation back into the map.

Is it always true that the operation is put back into the map? Unfortunately not always, in the presence of what I think of as *unexpected errors*. Many practitioners draw a separation between two different kinds of errors that a system can have. The terms *recoverable* and *unrecoverable* are sometimes used for them, but I tend to prefer the following terms (see also [some discussion by Andrew Gallant](https://burntsushi.net/unwrap/#what-about-recoverable-vs-unrecoverable-errors)):

- An expected error is one that can occur in normal operation. For example, if a user specifies a directory to write a file to, and that directory is not writable, then that’s in the realm of expectations (maybe the user mistyped the directory, for example).
- An unexpected error is one that cannot occur in normal operation. Andrew presents the example of a fixed string literal that is processed as a regex. A fixed literal baked into the program really ought to be valid as a regex, so any issues are unexpected.

Generally, in Rust, expected errors are handled via the `Result` type, and unexpected errors are handled by [panicking](https://doc.rust-lang.org/book/ch09-01-unrecoverable-errors-with-panic.html). Now, there isn’t a firm requirement that things be this way.

- For example, some high-availability systems may choose to model unexpected errors via a Result-like type (see the `woah` crate as an example).
- Quick-and-dirty scripts may choose to handle both expected and unexpected errors as panics.
- Panics can also be used for other purposes, e.g. to cancel in-progress work in synchronous Rust.

But in typical production-grade Rust, expected errors are `Result`s while unexpected errors (and only unexpected errors) are panics. Lock poisoning is built around this assumption.

### What if a panic occurs?[#](https://sunshowers.io/posts/on-poisoning/#what-if-a-panic-occurs)

Consider what happens if a panic occurs in `OperationState::process_message`. This depends in part on the build flags and surrounding code, so let’s look closely at all the possibilities. In Rust, there are two ways to configure build flags on panic:

- The default is to unwind, or to walk up the stack and run cleanup code. With unwinding, panics can also be caught at a higher level: in the same thread with `catch_unwind`, or in another thread via `JoinHandle::join`.
- The alternative is to abort, which causes the whole process to crash without performing any cleanup.

Some real-world applications (such as most of what we ship at [Oxide](https://oxide.computer)) abort on panic, but most of this post is actually moot for aborts. So in the rest of this post, we’re going to focus on the default unwind behavior.

What do programs do on unwind?

- If a panic is invoked in the context of a [`catch_unwind`](https://doc.rust-lang.org/std/panic/fn.catch_unwind.html), an `Err(E)` is returned, where [the value `E`](https://doc.rust-lang.org/std/thread/type.Result.html) is whatever message or other payload the panic occurred with.
- If there’s no `catch_unwind`, and the panic occurs on the main thread, then a message is printed out and the program exits with an error.Click to expand exampleConsider this simple program:`use std::{thread, time::Duration}; fn main() { panic!("This is a panic message"); } `This program prints out:`thread 'main' (502586) panicked at src/main.rs:2:5: This is a panic message note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace `and the program exits with a non-success exit code.
- If there’s no `catch_unwind`, and the panic occurs on a different thread, then a message is printed out, and the panic message is returned as the result of [`JoinHandle::join`](https://doc.rust-lang.org/std/thread/struct.JoinHandle.html#method.join).Click to expand exampleIf you run this slightly more complex program:`use std::thread; fn main() { let join_handle = thread::spawn(|| { panic!("This is a panic message"); }); join_handle.join().expect("child thread succeeded"); } `Then it prints out:`thread '<unnamed>' (517242) panicked at src/main.rs:5:9: This is a panic message note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace thread 'main' (516882) panicked at src/main.rs:7:24: child thread succeeded: Any { .. } `and the program exits with a non-success exit code.An interesting thing to note here is that there were *two* panics: one in the spawned child thread with the `panic!` message, and one in the main thread when the `expect` was called. The panic responsible for producing the non-success exit code was the one that occurred in the main thread, not the child thread.
- This raises the question: what if a non-main thread panics and the thread is *not* joined? With this program:`use std::{thread, time::Duration}; fn main() { thread::spawn(|| { panic!("This is a panic message"); }); thread::sleep(Duration::from_secs(5)); } `What gets printed out is:`thread '<unnamed>' (543640) panicked at src/main.rs:5:9: This is a panic message note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace `And the program exits with a successful exit code! There’s no indication that a panic occurred other than the message printed out, which can easily be missed.

The upshot of all this is that panics in non-main threads are not magic. In order for the system to make decisions based on whether a panic occurred, it must process that, either with `catch_unwind` or via `JoinHandle::join`, and it’s all too easy to just ignore panics.

Coming back to our `Operations` example above, what does that mean for our mutex’s critical section?

- If the Rust binary is configured to unwind on panic; and
- if a non-main thread panics in a critical section; and
- if there’s no catch_unwind to catch the panic; and
- if the child thread is not explicitly joined on, or a join does happen but the error is ignored—
- then, the mutex invariant is permanently violated. The data guarded by the mutex is logically corrupted. The in-progress operation is lost!

This might look like a lot of ifs, but they’re more common than you might think: they’re all either the default in Rust or a very common way to write code.

Rust’s designers had the foresight to see this issue, and introduce *lock poisoning* as a detection mechanism for this failure mode. The way poisoning works is that:

- At the time a lock is released, there’s a check for whether the thread is currently panicking. If it is, the mutex is marked poisoned.
- Then, the next time a lock is acquired, rather than a MutexGuard, a `PoisonError` is returned.

Almost all code immediately panics on seeing a `PoisonError` via `.lock().unwrap()`: this is often called *propagating panics*. But `PoisonError` can be handled more explicitly than that. Note that `PoisonError`, and poisoning more generally, is purely advisory: you can [retrieve the data underneath](https://doc.rust-lang.org/std/sync/struct.PoisonError.html#method.into_inner), and even [clear the poison bit](https://doc.rust-lang.org/std/sync/struct.Mutex.html#method.clear_poison) in Rust 1.77 and above.

The fact is, though, that anything other than `.lock().unwrap()` is rare in practice. This is emphatically *not* a reason to remove poisoning, and in fact is a strong argument to *retain poisoning* while making the ergonomics better ([see below](https://sunshowers.io/posts/on-poisoning/#typing-in-lockunwrap-is-annoying)). What is important is *detection*, not *recovery*.

So, putting it all together: if a child thread panics in a critical section, then it is quite possible that the data is in an inconsistent or logically corrupt state. To indicate this, the mutex is marked poisoned. If the child thread is not waited on by the parent, this might be the *only indication* that a panic previously occurred in a critical section!

It is precisely this confluence of factors that makes lock poisoning such an important feature.

## Unexpected cancellations[#](https://sunshowers.io/posts/on-poisoning/#unexpected-cancellations)

Is the problem of inconsistent mutex-guarded state limited to panic unwinding? I’d argue that it is a property of *unexpected cancellations* more generally: you start executing a critical section thinking that it will be run to completion, but something causes that process to be interrupted.

In Rust, there are two sources of unexpected cancellations, with strong parallels between them:

- Panics, as discussed above.
- In async Rust, future cancellations at an await point.

As documented in Oxide [RFD 397](https://rfd.shared.oxide.computer/rfd/397#_example_with_mutexes) and [RFD 400](https://rfd.shared.oxide.computer/rfd/400#no_mutex), unexpected future cancellations have resulted in so many mutex invariant violations that we now avoid Tokio mutexes *entirely*<sup>[1](https://sunshowers.io/posts/on-poisoning/#fn:1)</sup>. My perspective here comes from much pain dealing with this issue in async Rust, and wanting very much for this footgun to not make its way to synchronous Rust.

See [the appendix](https://sunshowers.io/posts/on-poisoning/#appendix-mutexes-and-future-cancellations) for more details.

## Do panics in critical sections always cause invariant violations?[#](https://sunshowers.io/posts/on-poisoning/#do-panics-in-critical-sections-always-cause-invariant-violations)

In other words, is poisoning often too conservative? My answer to this is that panics do not always cause invariant violations, but they’re so common, and the downsides of corrupt state so unbounded, that it is still valuable to have lock poisoning as a strong heuristic.

Firstly, if all you’re doing is reading data that just happens to be guarded by a mutex (maybe because some other function writes to that data), a panic in the critical section can’t cause invariant violations. (But also, you may wish to use an [`RwLock`](https://doc.rust-lang.org/std/sync/struct.RwLock.html).)

Secondly, some simple kinds of writes can also avoid causing invariant violations. For example if all you’re doing is updating some counters<sup>[2](https://sunshowers.io/posts/on-poisoning/#fn:2)</sup>:

```rust
#[derive(Default)]
struct Counters {
    read_count: u64,
    write_count: u64,
}

let mutex = Mutex::new(Counters::default());
// On read:
*mutex.lock().unwrap().read_count += 1;
// On write:
*mutex.lock().unwrap().write_count += 1;
```

Finally, it is sometimes possible to carefully architect code to be [unwind safe](https://doc.rust-lang.org/std/panic/trait.UnwindSafe.html), such that if a panic occurs, either:

- internal invariants are not violated; or
- the violation can easily be detected (effectively tracking the poison bit internally rather than in the Mutex wrapper).

For example, the standard library’s `HashMap` and `BTreeMap` are architected this way. In our `Operations` example, we could, rather than removing the operation from the map entirely, replace it with an `Invalid` sentinel state.

In these cases, it is true that a panic in a critical section is not harmful, and that the typical `.lock().unwrap()` approach will reduce system availability. But the important thing to keep in mind is that **code changes over time**. One of the things I like about Rust is how resilient it is to changes over time: by encoding properties like mutable access into the type system, Rust makes it that much harder for new team members (or even yourself six months from now) to screw up. However, [like async cancel safety](https://sunshowers.io/posts/cancelling-async-rust/#systematic-solutions), unwind safety is not encoded in Rust’s type system<sup>[3](https://sunshowers.io/posts/on-poisoning/#fn:3)</sup>, so it’s easy for code that’s fine today to be wrong tomorrow.

The main downside to a `.lock().unwrap()` that misfires is reduced availability and denial of service. But the downsides to an undetected panic are unbounded, and can range from denial of service all the way to “(part of) an HTTP request ending up [sent to a party it should not have been sent to](https://github.com/rust-lang/rust/issues/134645#issuecomment-3584117188),” or in other words personal information leakage.

A downside that (while [potentially serious](https://blog.cloudflare.com/18-november-2025-outage/)) is bounded, versus the kind of flaw that can kill an organization—I know which default I want.

**What about writing panic-free code?** You can carefully write your critical sections to not have panics. But that is a property that’s especially hard to maintain as code changes over time. Even something as simple as a `println!` can panic. Also, if the critical section can’t panic, then it doesn’t matter whether the mutex poisons or not.

## Where else can panics cause invariant violations?[#](https://sunshowers.io/posts/on-poisoning/#where-else-can-panics-cause-invariant-violations)

A bit of history here: in Rust 1.0, panics could only be detected at thread boundaries via [`JoinHandle::join`](https://doc.rust-lang.org/std/thread/struct.JoinHandle.html#method.join). This meant that back then, the only way for panics to cause invariant violations was for:

- shared data to be guarded by a mutex
- a thread to panic in the middle of a critical section

Since then, two Rust features were added:

- `catch_unwind` in Rust 1.9.
- Scoped threads in Rust 1.63.

With both of these, you can operate on arbitrary data (i.e. not just data guarded by a mutex) and leave it in an inconsistent state. To see how, let’s rewrite the `Operations` example above to not have a mutex inside of it, and to require exclusive access to make any modifications to it.

```rust
#[derive(Default)]
struct Operations {
    ops: HashMap<OperationId, OperationState>,
}

impl Operations {
    /// Process a message, updating the internal operation state appropriately.
    /// 
    /// Note: this now requires &mut self, not just &self.
    pub fn process(&mut self, id: &OperationId, message: Message) {
        // Retrieve the element from the map to process it.
        let Some(state) = self.ops.remove(id) else {
            // (return a not-found error here)
        }
        let next_state = state.process_message(message);
        self.ops.insert(id.clone(), next_state);
    }
}
```

Since there are no mutexes involved any more, this is no longer a critical section in the classical sense. But note that we still have the invariant that `ops` tracks all operations. This invariant *is* temporarily violated, with the idea that it’ll be restored before the function returns. Since `&mut` means nothing else has any kind of access (read or write) to this data, we know that this in-between state is not seen by anybody else.

But just like with mutexes, this breaks down with unwinding. With `catch_unwind`, you can do:

```rust
use std::panic;

let mut operations = Operations::default();
// ...

let result = panic::catch_unwind(|| {
    operations.process(id, message);
});
```

And with scoped threads, you can do:

```rust
use std::thread;

let mut operations = Operations::default();
// ...

thread::scope(|s| {
    let join_handle = s.spawn(|| {
        operations.process(id, message);
    });
});
```

If a panic occurs in `process_message`, `Operations` is logically corrupted. This failure mode has resulted in a proposal to have a `Poison<T>` wrapper that poisons on panicking. That *absolutely* makes sense and is worth pursuing.

## Separating mutexes from poisoning?[#](https://sunshowers.io/posts/on-poisoning/#separating-mutexes-from-poisoning)

But, along with the `Poison<T>` wrapper, there are [some suggestions](https://github.com/rust-lang/rust/issues/134645#issuecomment-3590942770) to go further and suggest that the current `std::sync::Mutex` type should be changed in the next Rust edition to, instead of poisoning on panic, **silently unlock**. (And also, as a followup, that the current `Mutex<T>` should instead become `Mutex<Poison<T>>`.)

(It’s worth noting that there’s another non-poisoning option: the mutex stays locked forever, as C programmers might expect. This option is somewhat appealing because it is safe by default, in a sense. But once a thread is stuck waiting on the mutex, there’s [no easy way to recover](https://sunshowers.io/posts/nextest-process-per-test/#appendix). So it’s not panics that propagate, it’s stuck threads. This seems strictly worse than a poisoning mutex to me, so I’ll assume the proposal means silent unlocking.)

I first want to give credit to this proposal: it is quite beautiful.

- It’s more composable. The Poison wrapper can be used with arbitrary mutexes, so you can use it with mutexes such as `parking_lot` that silently unlock on panic today. Single-threaded mutex equivalents like `RefCell` can also benefit from poisoning.
- With Rust’s philosophy of zero-cost abstractions, only users who need poisoning pay for it.
- As observed above, not all mutexes need poisoning, and poisoning is useful without mutexes, so the two are seemingly independent of each other.

While all of these are true, I keep coming back to how unbounded the downside of an undetected panic is, and how easy it is to get wedged in this state. Mutexes and poisoning have value separate from each other, but I don’t think they are as independent as they seem at first. My understanding from writing Rust code over many years is that almost all uses of mutexes benefit from poisoning, and almost all instances of poisoning one needs to care about are with mutex-guarded data.

**Why are mutexes special?** As we’ve established above, poisoning can make sense in non-mutex contexts too. What makes mutexes a particularly valuable place to have it? The reason has to do with what I like to call the [*cancellation blast radius*](https://rfd.shared.oxide.computer/rfd/0400#_cancel_correctness). Corrupted data only matters if it is shared mutable state: changed in a way that resulted in an invariant violation, and visible outside of where the failure occurred. If a typical `&mut` reference panics in the middle of an operation, it’s likely that the data it is referring to will also be torn down, in which case those invariant violations don’t matter<sup>[4](https://sunshowers.io/posts/on-poisoning/#fn:4)</sup>. But the whole *point* of mutexes is that they’re shared across threads! So data corruption is almost certain to be externally visible.

There are some use cases that would benefit from non-poisoning mutexes, like metrics and best-effort logging, but those cases shouldn’t drive the *default*.

More specifically, I am worried that a common complaint about lock poisoning ([see below](https://sunshowers.io/posts/on-poisoning/#typing-in-lockunwrap-is-annoying)) is that it has too much friction. Having to use `Mutex<Poison<T>>` instead of `Mutex<T>` *adds even more friction*, so people are going to opt for non-poisoning mutexes more of the time. This is going to lead to grave mistakes in production.

This is a spot where zero-cost abstractions and safety by default are seemingly at odds with each other. I would like to see performance numbers to quantify this better, but if I may hazard a guess, the incremental cost of checking the poison flag (a single [atomic load](https://github.com/rust-lang/rust/blob/1d60f9e070c1039b263e0f035c0f03dfcc610d0f/library/std/src/sync/poison.rs#L141) with relaxed ordering) is minimal compared to the cost of acquiring the lock in the first place.

## What about `parking_lot` mutexes?[#](https://sunshowers.io/posts/on-poisoning/#what-about-parking_lot-mutexes)

I mentioned earlier that `parking_lot`’s mutexes silently unlock on panic. A large chunk of the Rust ecosystem uses `parking_lot` today, often for performance reasons. Does that mean that code using `parking_lot` has these unbounded downsides?

The answer depends on a bunch of things, but in general (and especially in library code) that is indeed what I’m suggesting. For instance, [this critical section in `parity-db`](https://github.com/paritytech/parity-db/blob/a9c0e8517868ed513a50754940cd0ebc40a4a34d/src/db.rs#L679-L732) is quite large. Reasoning about whether it’s unwind-safe seems very difficult to me; this is exactly the kind of code that mutex poisoning does well to guard against.

In this case, the binary [is configured](https://github.com/paritytech/parity-db/blob/a9c0e8517868ed513a50754940cd0ebc40a4a34d/Cargo.toml#L42-L43) to abort on panic, so it’s fine. But reusable Rust libraries *cannot* require `panic = 'abort'`, and if this code were in a library on `crates.io`, it would be a real cause for concern.

## Just ship with `panic = 'abort'`?[#](https://sunshowers.io/posts/on-poisoning/#just-ship-with-panic--abort)

A common response to this class of issue is to not bother with any of this unwinding stuff, and always abort on panic. This comes back to the idea of the cancellation blast radius described above: aborting the process on panic guarantees that in-memory state is torn down.

I have a lot of sympathy for this idea! This is what we do at Oxide. (Why am I writing this post if it doesn’t affect my workplace? Well, first, I care about the health of Rust more generally. Second, libraries must work with unwinds. But most importantly, we *have* seen the pain of unexpected async cancellations at Oxide, so we *know* how bad it can be.)

But also, that works *fine* with the current approach: `.lock().unwrap()` always succeeds. Whether mutexes poison or not only matters with `panic = 'unwind'`.

This leads to what I think is driving a lot of discussion here:

## Typing in `.lock().unwrap()` is annoying[#](https://sunshowers.io/posts/on-poisoning/#typing-in-lockunwrap-is-annoying)

I get this complaint. I really do. Having to write `.lock().unwrap()` everywhere sucks. It’s extra characters in a language already filled with syntax noise. It can cause `rustfmt` to format your line of code across multiple lines.

These are all valid points. But there is a much better solution for them, one that doesn’t give up the very important benefits of poisoning: in the next Rust edition, make `lock()` automatically panic if the mutex is poisoned! (And add a `lock_or_poison` method for the current behavior<sup>[5](https://sunshowers.io/posts/on-poisoning/#fn:5)</sup>).

It’s worth comparing the different options here:

| Aspect | `lock().unwrap()` | Auto-panic | Removing poison |
| --- | --- | --- | --- |
| **Syntax noise** | Medium: `.unwrap()` everywhere | Low: just `lock()` | Low by default, high with `Poison<T>` |
| **Safety by default** | ✅ Panics propagate | ✅ Panics propagate | ❌ Silent corruption possible |
| **Opt-out available** | ✅ `lock().unwrap_or_else()` | ✅ `lock_or_poison()` | ❌ Must opt *in* via `Poison<T>` |
| **Works with `panic = 'abort'`** | ✅ | ✅ | ✅ |
| **Ergonomics** | Poor | Good | Good without poison, poor with |
| **Backwards compatibility** | Current behavior | Requires new edition | Requires new edition |

Based on this table, I believe the answer is clear: if a breaking change is going to happen, it’s much better to make `lock` automatically panic than to make panics silently unlock.

## Conclusion[#](https://sunshowers.io/posts/on-poisoning/#conclusion)

Concurrent programming is very difficult. Rust makes it easier than most other languages, and lock poisoning is an important part of the story. Let’s avoid introducing any regressions here.

Providing a `Poison<T>` wrapper makes a lot of sense. Making the default `std::sync::Mutex` silently unlock on panic would, however, be a mistake.

Should Rust’s standard library even provide non-poisoning mutexes? That’s a harder question. I’m worried that their mere presence in the standard library will lower the barrier to people doing the wrong thing, particularly in libraries where `panic = 'abort'` cannot be assumed. But I think non-poisoning mutexes have some legitimate uses, so I don’t object too strenuously if the tradeoffs are carefully documented.

Writing all this out was very helpful to me in getting my thoughts straight, and I hope it’s helpful to you too.

*Cover photo by [Karen Rustad Tolva](https://wandering.shop/@aldeka/109301243634789356), used with permission. Thanks to [Fiona](https://infosec.exchange/@munin) and several of my colleagues at Oxide for reviewing drafts of this post. Any errors in it are my own.*

*Discuss on [Hacker News](https://news.ycombinator.com/item?id=46125903), [Lobsters](https://lobste.rs/s/vkyrtf/defense_lock_poisoning_rust), and [/r/rust](https://www.reddit.com/r/rust/comments/1pck69k/in_defense_of_lock_poisoning_in_rust_by_sunshowers/).*

*Updated 2025-12-06: Added a section to* [Separating mutexes from poisoning](https://sunshowers.io/posts/on-poisoning/#separating-mutexes-from-poisoning) *on what makes poisoning particularly valuable for mutexes, more than in other contexts.*

## Appendix: Mutexes and future cancellations[#](https://sunshowers.io/posts/on-poisoning/#appendix-mutexes-and-future-cancellations)

Unlike panics, the standard library’s mutex does not poison on future cancellations. (I believe it’s not possible to poison on future cancellations with the RAII pattern.)

- There is a saving grace here: most people use the Tokio executor, which typically requires spawned tasks to be `Send`: transferable between OS threads while suspended at an await point.
- The standard library’s MutexGuard is not transferable between OS threads, which prevents await points in a critical section.

But wait! Tokio provides its own [`Mutex` type](https://docs.rs/tokio/1/tokio/sync/struct.Mutex.html), which *is* sendable to another thread. This means that it *is* possible to put an await point in a critical section, and so the issue of unexpected cancellations within a critical section rears its ugly head with Tokio mutexes.

1. Tokio mutexes also do not poison if the critical section panics. At Oxide we abort on panic so this matters less as a reason to avoid them, but is yet another asterisk that pushes me away from them. [↩︎](https://sunshowers.io/posts/on-poisoning/#fnref:1)
2. A more typical way to manage simple counters is with [an atomic](https://doc.rust-lang.org/std/sync/atomic/struct.AtomicU64.html), but if the data is more complex than just an integer, a mutex may be necessary. [↩︎](https://sunshowers.io/posts/on-poisoning/#fnref:2)
3. Rust does have some [rudimentary support for unwind safety](https://doc.rust-lang.org/std/panic/trait.UnwindSafe.html) in the type system, but it is more of a suggestion that most users [ignore](https://doc.rust-lang.org/std/panic/struct.AssertUnwindSafe.html), and because of that there’s [a proposal](https://github.com/rust-lang/rfcs/pull/3260) to remove it from Rust. [↩︎](https://sunshowers.io/posts/on-poisoning/#fnref:3)
4. The exception is `Drop` implementations, which may have to be written robustly to guard against temporary invariant violations. [↩︎](https://sunshowers.io/posts/on-poisoning/#fnref:4)
5. The more obvious `try_lock` is [already taken](https://doc.rust-lang.org/std/sync/struct.Mutex.html#method.try_lock). [↩︎](https://sunshowers.io/posts/on-poisoning/#fnref:5)
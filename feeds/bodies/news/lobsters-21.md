After some [recent discussion](https://github.com/rust-lang/rust/issues/149359) on the topic of mutex poisoning and notably a [blog post](https://sunshowers.io/posts/on-poisoning/) that I
thought was interesting, thoughtful, exhaustive, yet completely disagreed with, I wanted to comment
on the debate myself. To me, poisoning-by-default is one of biggest mistakes that were made in the
language, next to some others that are a story for a different time.

In short, I believe that Mutex poisoning is the wrong choice for most applications, as

- it significantly pessimises code performance in the general case
- in addition to hampering readability
- while encouraging bad code patterns to deal with its weirdness
- in order to solve a niche problem
- that doesn’t even solve the general problem.

## What is poisoning?

In theory, a mutex guards a critical section of the code. That code changes the state of a piece of
data free from interference of concurrent threads, then releases the lock. That code might then
encounter an error, and release the lock in the middle of doing its important work. For example:

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
fn important(always_even: Arc<Mutex<i32>>) -> i32 {
    // Invariant: always_even must always be even
    let mut handle = always_even.lock().unwrap();

    *handle += 1;

    risky_operation();

    *handle += 1;

    *handle
}

fn risky_operation() {
    if rng().next_u32() % 42 == 0 {
        panic!();
    }
}
```

The following code will work fine most of the time, but if the dice roll doesn’t go our way, the
`always_even` mutex gets unlocked in an invalid state. In Rust, today, poisoning exists to handle
this. If a guard is released abnormally (while panicking), it records that this happened in a
boolean. Any future calls to `lock()` will return `Err(PoisonError)`, which will trigger a panic
when we unwrap it. The bad state is never observed and all is well.

You might have felt that the example I made up was somewhat contrived. That’s because it is. Real
cases of this pattern can and do happen, but most of the use cases that involve mutexes are much
simpler. Many critical sections are no longer than a variable assignment, or doesn’t have an invalid
in-between state. There are cases in lower level programming where a mutex guards a piece of data
that is not directly inside it, or is outside the view of the program entirely. In fact, I’ve
written a wrapper for a C library that worked like that. Though I disagree with the notion that this
is the common case.

I do recommend anyone [Rain’s blog](https://sunshowers.io/posts/on-poisoning/) on the matter, as she has some good examples of how
you can cause violations of these critical sections (even without mutexes) and I wholeheartedly
support the idea of a `Poison` wrapper for the use cases that need it. I suspect the domains she
works on lend themselves more towards these issues compared to mine. Rust’s default behaviour should
make the common case easy and the rare case possible.

## Side-note: how mutexes work

This section is only tangentially related to the topic at hand, but I already wrote it and wasn’t
ready to kill my darlings.<sup>[1](https://bertptrs.nl/2026/11/16/mutex-poisoning-is-not-for-everyone.html#fn:mutexes)</sup> Skip to [the next
section](https://bertptrs.nl/2026/11/16/mutex-poisoning-is-not-for-everyone.html#how-poisoning-harms-every-single-piece-of-code) to continue the discussion on poisoning.

In Rust, for most platforms, mutexes are implemented using the `futex`<sup>[2](https://bertptrs.nl/2026/11/16/mutex-poisoning-is-not-for-everyone.html#fn:futex)</sup> system call. It
allows for operations to remain purely in user-space as long as the mutex in question isn’t
contended, which is nice for performance reasons.

Under the hood, a mutex is a simple 32-bit integer on most platforms even though it only holds three
unique values:

- If it’s zero, the mutex is free and can be claimed by any thread by a simple atomic compare-exchange.
- If it’s one, the mutex is held but there are no waiting threads. This is useful to know, as it means there are no threads that we need to wake up when releasing the mutex, and we can yet again remain in userspace.
- If it’s two, the mutex is held and some other thread is waiting for it. This means some additional care should be taken when unlocking.

Rust implements this with a few atomic operations and the `futex_wait` call. Crucially, the path for
locking a mutex that *isn’t* contended is a single atomic operation. The only operation that
requires a context switch is `futex_wait`.

Unlocking is even simpler. The thread that holds the mutex first releases the lock, then optionally,
if there was an indication that the lock was contended, wakes any sleeping threads so they can try
to acquire the lock.

## How poisoning harms every single piece of code

As discussed in too much detail above, (un)locking mutexes is cheap as long as they’re not
contended, and when contended, they are at least cheap instruction wise. This is where poisoning
mutexes get you.

In short, being able to poison is a cost that is always paid, but seldom used. To start, poisoning
is essentially implemented by adding an `AtomicBool` field to every `Mutex`. Due to alignment, this
grows the size of every mutex by anywhere from zero bytes to an additional pointer. This isn’t
terrible but for use cases where you have many mutexes guarding small objects, this can add up.

The real issue to me however is in code size. Let’s start with another contrived example, a function
that reads its argument, copies it, and returns it. An idealised version of that would be the
following.

```
1
2
3
pub fn get_contents(val: &i32) -> i32 {
    *val
}
```

This compiles down to 2 instructions and a label. Copy the data into the register then return.

```
1
2
3
example::check_contents::h197b180b47e24703:
        mov     eax, dword ptr [rdi]
        ret
```

Of course, this doesn’t work for any context that needs shared mutation, but we can consider it our
baseline. Perfection would look like this. So, let’s ignore that atomic integers exist and add a
mutex to this story. We will go over the generated assembly code for each, and you can compare the
code in its entirety in [this Compiler Explorer overview](https://rust.godbolt.org/z/1jEP5MEGz).

### Base case: Locking and unwrapping

We can update the code above to actually use mutexes, and simply lock-then-unwrap the mutex.

```
1
2
3
4
5
use std::sync::Mutex;

pub fn check_contents(mutex: &Mutex<i32>) -> i32 {
    *mutex.lock().unwrap()
}
```

This compiles to a total of *147* lines of assembly which I’m not going to reproduce here in full.

- 75 of those are specifically inlined to this particular function and cannot be reused.
- About 45 those are monomorphised[3](https://bertptrs.nl/2026/11/16/mutex-poisoning-is-not-for-everyone.html#fn:monomorphised) for mutexes guarding an i32
- The remainder is global program information and might be reused for other locks.

To divide that up a different way, we have

- code checking the poison status
- code doing the mutex manipulation
- code to initiate a poison in case of a panic
- code for preparing to panic should we need to
- code for displaying a panic
- some dyn drop glue

Most of this is inlined into the function. This in turn affects performance, as this limits how much
of your “real” code fits in the CPU’s instruction cache. The laptop I’m writing this on has a paltry
32KiB of instruction cache. Luckily we can do better.

### Removing the panic

Most of the code generated in the previous example had to do with setting up the panic, and checking
the conditions. But we don’t care about panicking. We can simply acknowledge the `PoisonError` and
continue. That looks as follows:

```
1
2
3
4
5
6
use std::sync::Mutex;
use std::sync::PoisonError;

pub fn check_contents(mutex: &Mutex<i32>) -> i32 {
    *mutex.lock().unwrap_or_else(PoisonError::into_inner)
}
```

This results in only 68 lines of assembly, which is much better, though all of it is inlined to our
function. Compared to before, we’ve lost all panic related code. There’s still some unnecessary
branching related to whether the mutex is poisoned, as well as a little dance to track poisoning in
our function. Our function can never panic, but compiler optimisations currently do not remove the
atomic loads and stores involved here. Nevertheless, if you want to target stable Rust *and* you
don’t care about panics, this is what you should do at the moment.

### The ideal: no poison handling at all

In the current nightly builds of Rust, there are non-poisoning mutexes that can don’t have any of
the overhead. We can optimise our code from above to make use of them.

```
1
2
3
4
5
6
7
#![feature(nonpoison_mutex)]
#![feature(sync_nonpoison)]
use std::sync::nonpoison::Mutex;

pub fn check_contents(mutex: &Mutex<i32>) -> i32 {
    *mutex.lock()
}
```

No unwrapping, and it only results in 34 lines of assembly code. This is short enough for me to walk
through it.

```
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
example[da70a55c1c00d324]::check_contents:
        push    rbp
        push    rbx
        push    rax
        xor     ebp, ebp
        mov     ecx, 1
        xor     eax, eax
        lock    cmpxchg dword ptr [rdi], ecx ; (1) check if mutex is held, and if not, claim it
        jne     .contended ; (2) mutex was not zero, jump to contended case
        mov     eax, dword ptr [rdi + 4] ;  (4) if not, load the value
        xchg    dword ptr [rdi], ebp ; (5) unlock the mutex
        cmp     ebp, 2 ; (6) check if there are other threads waiting
        je      .exit_with_threads_waiting
.fast_exit:
        add     rsp, 8
        pop     rbx
        pop     rbp
        ret
.contended:
        mov     rbx, rdi
        call    qword ptr [rip + <std[3ebc094a278a8d54]::sys::sync::mutex::futex::Mutex>::lock_contended@GOTPCREL] ; (3) Perform the spin/futex_wait loop
        mov     rdi, rbx ;
        mov     eax, dword ptr [rdi + 4] ; (4) load the value
        xchg    dword ptr [rdi], ebp ; (5) unlock the mutex
        cmp     ebp, 2 ; (6) check if there are other threads waiting
        jne     .fast_exit
.exit_with_threads_waiting:
        mov     ebx, eax
        call    qword ptr [rip + <std[3ebc094a278a8d54]::sys::sync::mutex::futex::Mutex>::wake@GOTPCREL] ; (7) wake sleeping threads
        mov     eax, ebx
        add     rsp, 8
        pop     rbx
        pop     rbp
        ret
```

I’ve added comments and labels to the assembly so the steps from the (un)locking flow charts become
visible. As far as assembly code goes, it’s very readable and simple. Which, of course, is exactly
what you want from fundamental library code.

The additional logic checking the poison state, adding a destructor for the mutex guard, and, if you
choose ergonomics, even panic machinery, significantly bloats the code of a rather fundamental
operation.

## Readability and good habits

Besides the purely technical argument that poisoning makes all code larger and slower than it needs
to be, there is a different one. [As discussed previously](https://bertptrs.nl/2026/11/16/mutex-poisoning-is-not-for-everyone.html#removing-the-panic), code that doesn’t
care about mutex poisoning should generally write:

```
1
my_mutex.lock().unwrap_or_else(PoisonError::into_inner)
```

It’s reasonably efficient and available on stable Rust. But that whole `unwrap_or_else` part takes
up more than half the line. No worry, you might say, we can make it shorter:

```
1
my_mutex.lock().unwrap()
```

This works well enough. It’s less efficient than the previous example, but it’s nice and short. If
your code never panics, it’s even perfectly safe. You might have spotted a load-bearing “if”
already. It’s kind of hard to guarantee your code does not panic. Array indexing, integer division,
and a whole host of other features might panic unexpectedly.

This is hard for experienced developers, but for those learning it’s even worse. It also trains bad
habits. Every time a beginner Rust developer writes `unwrap()` instead of handling their errors, a
puppy steps on a Lego brick. Or [causes a widespread internet outage](https://blog.cloudflare.com/18-november-2025-outage/). One of the
two, I forget which.

We should not want to include APIs into the standard library that return a `Result` that is
“expected” to be unwrapped. Infallible operations should not fail.

## Inconsistency

Poisoning protects against a task panicking in the middle of an invariant violation. But why must
this be specific to mutexes? The example from before works just as well with a simple mutable
borrow. Panics may still happen, and you may still [catch](https://doc.rust-lang.org/std/panic/fn.catch_unwind.html) them.

```
1
2
3
4
5
6
7
8
9
10
fn important2(always_even: &mut i32) -> i32 {
    // Invariant: always_even must always be even
    *always_even += 1;

    risky_operation();

    *always_even += 1;

    *always_even
}
```

This is actually a fairly common problem. In a more recent blog post, [researchers at Microsoft
highlight various places they’ve found where even the standard library gets this
wrong](https://forge-blog.github.io/posts/rust-std-memory-safety/#pattern-1-trusting-code-not-to-panic).

In most cases however, this is fine, as it is with the mutex example given in the beginning. You
don’t need to poison this reference. But for applications where you do, it’s kinda nice to be able
to.

It’s not hard to imagine a wrapper that adds poisoning behaviour when you want to have it.
Crucially, this needs to be an additive wrapper. You can add a poisoning system to something. You
cannot strip out the poisoning system from a primitive that has it. Poison safety is important for
the specific use cases that need it, but most do not.

I don’t believe it’s worth it to saddle mutexes in particular with this overhead when the problem is
near universal with any mutable state. State invariants are just hard that way.

## Comparison to bounds checking

One might draw a comparison between poison safety and buffer safety. In Rust, we always do bounds
checking, relying on the compiler to optimise it out in cases it can be proven redundant. Can’t
poison safety be the same? And the answer, it turns out, is no.

The compiler cannot optimise poisoning away. It requires any mutex carry additional data to track
it. *Maybe* the compiler can figure out one particular critical section cannot panic, and therefore
it can leave out the setup and clean-up, but in general it cannot avoid checking the state. This is
overhead that always applies, and hurts, especially in environments where code size is more
restricted.

## De facto standard workarounds

In C++, there are a few choices in the standard that make certain containers less efficient than
they could be<sup>[4](https://bertptrs.nl/2026/11/16/mutex-poisoning-is-not-for-everyone.html#fn:unordered_map)</sup>. Because of how standardisation works, the containers can never be
“fixed”. This causes third party implementations, such as Abseil and Boost, to become the de facto
standard.

Mutexes in Rust suffer from the same problem. The standard library has poisoning, but people don’t
want poisoning, so instead they opt for crates like [`parking_lot`](https://docs.rs/parking_lot/latest/parking_lot/). I believe this is
bad for the ecosystem as a whole. When the standard library offers a feature, it should be an
uncontroversially good choice, unless you are doing something hyper specific. We don’t have to be
“batteries included” but the parts that are there should be a good fit.

## In conclusion

I started out writing this blog in response to a movement to change the default mutex behaviour in
Rust. It seems to me there are three camps:

1. Keep the status quo. std::sync::Mutex and friends will have poisoning.
2. Make std::sync::Mutex propagate panics when poisoned.
3. Add a non-poisoning variant std::sync::nonpoison::Mutex
4. Replace std::sync::Mutex with std::sync::nonpoison::Mutex. Poisoning becomes opt-in.

Rain’s blog argued for option 1. I believe we both agree that option 2 is a terrible idea. I think
we should do at least option 3. Option 4 would be a good edition improvement, but it is also a
significant compatibility issue, and even I find it hard to argue that it’s really worth it.

Which is a roundabout way of saying that we really should stabilise `std::sync::nonpoison` and
definitely should not make `std::sync::Mutex` panic by default.

1. It is becoming apparent to me that I just like explaining mutexes and I don’t know what to do about that. [↩︎](https://bertptrs.nl/2026/11/16/mutex-poisoning-is-not-for-everyone.html#fnref:mutexes)
2. Fast Userspace muTEX. See [`futex(2)`](https://man.archlinux.org/man/futex.2) for more on the system call and [`futex(7)`](https://man.archlinux.org/man/futex.7) for its semantics [↩︎](https://bertptrs.nl/2026/11/16/mutex-poisoning-is-not-for-everyone.html#fnref:futex)
3. For generic definitions (e.g. `Mutex<T>`) the compiler must generate code for every unique `T` that gets used, and for loads of reasons often more than once per `T`. The compiler development docs have [a deeper explanation of monomorphisation](https://rustc-dev-guide.rust-lang.org/backend/monomorph.html). [↩︎](https://bertptrs.nl/2026/11/16/mutex-poisoning-is-not-for-everyone.html#fnref:monomorphised)
4. A famous example is `std::unordered_map`, which [suffers from being over-specified and that prevents more efficient implementations](https://bannalia.blogspot.com/2022/06/advancing-state-of-art-for.html). [↩︎](https://bertptrs.nl/2026/11/16/mutex-poisoning-is-not-for-everyone.html#fnref:unordered_map)
The Go programming language was instrumental in bringing the Communicating Sequential Processes (CSP) concurrency model
into widespread use. In the CSP model, channels are usually *unbuffered* and act not just as a means of communication,
but also for synchronization. That is, sending or receiving blocks until the other side is ready, and then the value is moved from one thread to another atomically.

In addition, the [`select`](https://go.dev/ref/spec#Select_statements) statement guarantees that out of all the channel
operations in its clauses, only one is selected and the others remain unprocessed. This allows several
messaging patterns to be expressed succinctly.

CSP is an [old idea](https://web.archive.org/web/20260922190027/https://www.cs.cmu.edu/~crary/819-f09/Hoare78.pdf) (from the 1970s), and while Go sticks relatively closely to that model, other languages have taken it
further. In my opinion, the most interesting one is Concurrent ML (CML). Introduced in the mid-1990s, CML still has much to teach modern language designers.

In this post, I want to argue that Concurrent ML’s developments on top of CSP offer compelling advantages for implementing concurrent systems, fixing several of Go’s deficiencies.

**CML’s key idea is to promote a communication operation from an executable statement to a *value* describing the operation. The execution of that description can be done separately.** Don’t worry if this isn’t clear right away, this whole essay is an elaboration of that idea.

This unlocks several powerful improvements over Go/CSP:

1. It unifies the concepts of choice (what select does) and cancellation into a unified, general abstraction.
2. This abstraction enables composition and encapsulation of concurrency, which is impossible in Go.

Separately, CML fixes one of Go’s biggest concurrency footguns – goroutines leak unless properly shutdown – via straightforward garbage collection.

While the ideas come from CML, today [Racket](https://racket-lang.org) is the programming language that best espouses them.
Racket is actively developed, and the CML model is comprehensively supported and used within it. With that in mind, I will be demonstrating all examples in Racket and will interchangeably
use the terms CML or Racket based on context.

Similarly, I will use the words *goroutine* and *thread* interchangeably. Their semantics are identical, at least for the
purposes of this article.

This article does not propose anything new. It is meant to introduce practitioners to a model that has generally
remained in the academic community. This article assumes that you are reasonably familiar with Go
syntax and the behavior of its channels. It does not assume familiarity directly with Racket, but you should be able to
follow basic ideas about function calls and recursion in a Scheme-like language.

To try out the Racket code snippets, [download Racket](https://download.racket-lang.org/), fire up the DrRacket editor, and paste the examples in the main window. Press the Run button to execute.

## events: communication operations as values

In Go, if `ch` is a channel, the following two operations are used to send or receive messages on the channel.

These channel operation statements [take effect immediately when reached](https://go.dev/tour/concurrency/2).

When used with the [`select`](https://go.dev/ref/spec#Select_statements) statement, these expressions can be combined in `case` clauses to express
potential choices that the runtime can select between. When execution reaches a [`select`](https://go.dev/ref/spec#Select_statements) statement, all channel operations are
polled to see which ones are ready to execute. One operation is picked from those that are ready. It is
guaranteed that no other channel operation will be completed within this execution.

Within the select, channel operations act as *descriptions*, which the `select` statement uses to determine which channels to poll, and for what operation. That is, hitting the first case does not immediately block the entirety of the `select`. However, in Go, this descriptive form cannot be decoupled from the [`select`](https://go.dev/ref/spec#Select_statements) statement and stand on its own. As soon as you try that, it becomes the previous example, and the statement tries to execute immediately. This prohibits composition and encapsulation. A function cannot return a description which you can choose to `select` on later. Nor can you stash the description within a struct for carrying around.

Channels in Racket start of the same way and provide direct analogs of the blocking send and receive operations.

```scheme
1; ch := make(chan int)
2(define ch (make-channel))
3; ch <- 5
4(channel-put ch 5)
5; x := <-ch
6(define x (channel-get ch))
```

However, they also offer a standalone way to describe the operation.

```scheme
1; sort of like `case ch1 <- 5`.
2(channel-put-evt ch 5)
3
4; There is no channel-get-evt.
5; Instead a channel itself can directly be used as a description of the ability
6; to receive from it.
```

**This is an expression returning a value *NOT* a statement of action!**

`channel-put-event` **returns a value, which is called an *event*** in CML. It does not immediately send the value 5 on the channel.

The event can be executed later to actually apply its effect. Because it is a value, just like the number 5, we can do a lot of useful things with it, which are not possible in Go:

- assign it to a variable,
- return it from a function,
- put it into a struct,
- abstract the fact that we are performing a channel operation behind a regular function, and
- wrap it with additional concurrency combinators to express patterns

In addition, events are more general than channel operations, being able to express I/O operations that are commonly exposed by “event loops” from other languages.

The event’s actual effects are put into motion by the [`sync`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28quote._~23~25kernel%29._sync%29%29) function

```scheme
1(sync (channel-put-evt ch 5))
```

Using [`sync`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28quote._~23~25kernel%29._sync%29%29) *attempts to synchronize* a set of events. Just like `select`, all events passed to it are polled. An event that is *ready* is selected, and `sync` returns the *synchronization result* of the selected event, which is something each event can define. For sending on channels, this result is the event itself. When receiving from a channel it is the value received from the channel.

When multiple events are ready, one is chosen randomly, just like Go.

For example, here is a Racket thread that calculates the sum of a list of numbers and responds on a channel.

```scheme
 1#lang racket/base
 2(define (sum items resp-ch)
 3  (define total (apply + items))
 4  (channel-put resp-ch total))
 5
 6(define ch (make-channel))
 7(define the-numbers (list 7 2 8 -9 4 0))
 8
 9(thread (λ () (sum the-numbers ch)))
10
11(define total (sync ch))
12(printf "Sum of ~a is ~a" the-numbers total)
```

Note that this separation of description and execution can easily be recombined. [`channel-put`](https://docs.racket-lang.org/reference/channel.html#%28def._%28%28lib._racket%2Fprivate%2Fmisc..rkt%29._channel-put%29%29) can be defined as:

```scheme
1(define (channel-put ch val)
2  (sync (channel-put-evt ch val)))
```

### Wrapping events

> Throughout these essay, we will be using lots of anonymous functions. In Go, they are created with `func`. In Racket, the [`lambda`](https://docs.racket-lang.org/reference/lambda.html#%28form._%28%28lib._racket%2Fprivate%2Fbase..rkt%29._lambda%29%29) form, or literally [`λ`](https://docs.racket-lang.org/reference/lambda.html#%28form._%28%28lib._racket%2Fprivate%2Fbase..rkt%29._lambda%29%29) is used.  If you want to refresh your knowledge of these, see [this](https://go.dev/doc/codewalk/functions/) for Go or [this](https://docs.racket-lang.org/guide/syntax-overview.html#%28part._.Anonymous_.Functions_with_lambda%29) for Racket.

The [first](https://go.dev/tour/concurrency/5) example of the [`select`](https://go.dev/ref/spec#Select_statements) statement in the Tour of Go uses a goroutine to compute Fibonacci numbers, and relays the response using a channel. It also uses an additional channel to tell the goroutine to quit. This is the Racket translation:

```scheme
 1#lang racket/base
 2(define (fibonacci out-ch quit-ch)
 3  (let loop ([x 0]
 4             [y 1])
 5    (sync
 6     (handle-evt (channel-put-evt out-ch x) (λ (_) (loop y (+ x y))))
 7     (handle-evt quit-ch (λ (_) (displayln "quit"))))))
 8
 9(module+ main
10  (define c (make-channel))
11  (define quit-ch (make-channel))
12  (thread
13   (λ ()
14     (for ([i (in-range 10)])
15       (displayln (channel-get c)))
16     (channel-put quit-ch #f)))
17  (fibonacci c quit-ch))
```

There are some functional-language-specific forms like the use of a named
`let` to recursively express the `for {}` infinite loop. `in-range` is Racket’s number iteration form, so the `for` loops 10 times, retreiving the first 10 Fibonacci numbers. Just like [`select`](https://go.dev/ref/spec#Select_statements) accepts several channel operations,
[`sync`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28quote._~23~25kernel%29._sync%29%29) accepts
multiple events, and then blocks until at least one of them is ready for synchronization.

This first example introduces a new function [`handle-evt`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28quote._~23~25kernel%29._handle-evt%29%29). This is an *event combinator* - a function that augments events, and itself return an event.

In Go’s [`select`](https://go.dev/ref/spec#Select_statements), a `case` clause can be followed by a series of statements, which are executed iff that clause was selected and the operation executed. You can think of the [`select`](https://go.dev/ref/spec#Select_statements) clauses as being *commit points* where a specific communication operation gets committed to, and others are abandoned.

With this mental model, we can do things before a commit point (*setup*) or after a commit point (*post-commitment*).

Once we start composing events, it no longer makes sense to associate setup and post-commitment actions with
the [`sync`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28quote._~23~25kernel%29._sync%29%29), otherwise, whenever you returned an event from a function, you would also need to return the
setup actions separately. Instead, we can attach such steps to the event itself. This is done through a wrapper
function that takes an event and a function. Each wrapper augments the event in a specific way. These are also called *event combinators*.

Our first wrapper is [`handle-evt`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28quote._~23~25kernel%29._handle-evt%29%29), which associates *post-commitment* actions with an event. It returns a new, wrapped event. When the wrapped event
gets selected by a [`sync`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28quote._~23~25kernel%29._sync%29%29) (i.e. it wins the race), the associated function is run with the synchronization result of the event. In the example above, we use these actions to decide whether to continue looping or quit.

Note that these wrappers are taking advantage of the general nature of events to put many common actions within that framework. All wrappers are encapsulating their input events, augmenting them, and returning output events. Users of those events *cannot* and *need not* figure out what is hiding behind the event.

As another example of encapsulation, the quit *pattern* can be pulled into a `quit-evt`. Nothing outside the implementation needs to know that the quit is actually implemented by channels.

```scheme
 1#lang racket/base
 2; returns a quit-evt, and a function to trigger the quit.
 3(define (make-quit-evt)
 4  (define my-quit-ch (make-channel))
 5  ; our quit-evt in this case is just a channel, but nobody needs to know that.
 6  ; values is how a function returns multiple values in Racket.
 7  (values my-quit-ch (λ () (channel-put my-quit-ch #f))))
 8
 9(define (fibonacci out-ch quit-evt)
10  (let loop ([x 0]
11             [y 1])
12    ; It can later be used here.
13    (sync (handle-evt (channel-put-evt out-ch x) (λ (_) (loop y (+ x y))))
14          quit-evt)))
15
16(module+ main
17  (define c (make-channel))
18  ; define-values is an "unpacking" operation for a function returning multiple values.
19  ; Similar to how result, err := Func() is used in Go.
20  (define-values ( quit-evt quit-fn) (make-quit-evt))
21  (thread (λ ()
22            (for ([i (in-range 10)])
23              (displayln (channel-get c)))
24            (quit-fn)))
25  (fibonacci c quit-evt))
```

I hope it has become clear that treating channel operations as descriptive values has unlocked composition!

### Composing choice

The ability to return events means that Racket code often builds up a list of events from various sources and then calls [`sync`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28quote._~23~25kernel%29._sync%29%29) on all of them. [`sync`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28quote._~23~25kernel%29._sync%29%29) is actually performing a *choice* operation between those events, and Racket allows that concept to also be separated into a wrapper event.

The combinator is [`choice-evt`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28quote._~23~25kernel%29._choice-evt%29%29).

Here is a common pattern of “fetch data from 2 different sources, and accept whichever one returns the fastest”.
We can easily compose it with timeouts. There isn’t a [`context.Context`](https://pkg.go.dev/context#Context) in sight!

```scheme
 1#lang racket/base
 2
 3; This timeout-evt is used throughout the rest of the essay.
 4; It translates a relative time to absolute time and uses it with the built-in alarm-evt.
 5(define (timeout-evt msec)
 6  (alarm-evt (+ (current-inexact-monotonic-milliseconds) msec) #t))
 7
 8; APIs are made-up
 9(define (http-get-evt url)
10    ...)
11
12(define (fetch-from-fastest-url url1 url2)
13  (choice-evt (http-get-evt url1)
14              (http-get-evt url2)))
15
16; Perform 2 http requests, returning the result of whichever responded fastest, but also capped with a timeout.
17(sync (fetch-from-fastest-url url1 url2)
18      (timeout-evt 5))
```

This sort of composition is *impossible* to express in Go, because it is not possible to wrap base operations or choices over them into re-usable functions. Spawning goroutines that return channels *is not the same*. In Racket, the *actual fetch operation does not start before `sync` is called*!

I again want to stress that this composition of concurrency is a *really big deal*. Library code can assemble local concerns like choosing between two events, but let callers decide when to execute the operations, and callers themselves can impose their own rules, like timeouts, with neither needing to accomodate the other.

## Building on events

For the rest of this post, we will use a single running example to see how CML builds on the basic primitive of events to represent various patterns. We will discover how this system lends itself to a slightly different style of writing programs. It is *almost* an inversion of the way Go programs are written:

1. In CML, it is common to spawn threads within library APIs. In contrast, idiomatic Go libraries generally recommends asking callers to spawn a goroutine if they want concurrency.
2. Cancellation is built into the system instead of layered on top with `context.Context`. `sync` is aware of the cancellation APIs and actively participates in them.

In both languages, it is common to model a service that mediates access to a singleton
resource [using a dedicated goroutine](https://gobyexample.com/stateful-goroutines). Say a *print service*, powering a [hardware printer](https://en.wikipedia.org/wiki/Printer_(computing)). Channels are used to send requests to the goroutine,
which loops indefinitely. If the service accepts the channel request, then it *will* eventually
send the appropriate commands to the machine. It can perform queuing, and handle paper running out and so on, while keeping track of pending jobs. Obviously, in our examples, we will just `print` out to stdout.

We also want to abstract the fact that the service is running in another thread, or even that it communicates via
channels. Obviously, this is ridiculous in such a tiny example, but bear with me here. Here is the simplest translation of these requirements to Go:

```golang
 1package main
 2
 3import (
 4	"fmt"
 5	"time"
 6)
 7
 8type PrintService struct {
 9	printCh chan string
10}
11
12func MakePrintService() PrintService {
13	printCh := make(chan string)
14	go func() {
15		var req string
16		for {
17			req = <-printCh
18			fmt.Printf("Got print request: \"%s\"\n", req)
19			// Uncomment this to simulate a slow service.
20			// time.Sleep(3 * time.Second)
21		}
22
23	}()
24	return PrintService{
25		printCh: printCh,
26	}
27}
28
29func (ps *PrintService) Print(msg string) {
30	ps.printCh <- msg
31}
32
33func main() {
34	service := MakePrintService()
35	for _ = range 2 {
36		service.Print("Hello World")
37		time.Sleep(100 * time.Millisecond)
38	}
39}
```

Racket `struct`ures are similar to Go, just with different syntax:

```scheme
1; A struct is defined like this.
2(struct person (name age))
3
4; Instances are constructed like this
5(define nikhil (person "Nikhil" 2))
6
7; Fields are accessed using getters of the form <struct name>-<field name>
8(printf "Hello, ~a!" (person-name nikhil))
```

and the service:

```scheme
 1#lang racket/base
 2
 3(struct print-service (print-ch))
 4
 5(define (make-print-service)
 6  (define (server-loop print-ch)
 7    (let loop ()
 8      (define req (channel-get print-ch))
 9      (printf "Got print request: ~a~n" req)
10      ; (sleep 3)
11      (loop)))
12
13  (define print-ch (make-channel))
14  (thread (λ () (server-loop print-ch)))
15
16  (print-service print-ch))
17
18(define (print-evt service msg)
19  (channel-put-evt (print-service-print-ch service) msg))
20
21(module+ main
22  (define service (make-print-service))
23  (for ([i (in-range 2)])
24    (sync (print-evt service "Hello World"))))
```

### Guard events

A new requirement comes in that we should show the user whether the print succeeded. We need a way for the service to
respond to each print request. In both languages, [we can make a new channel per request to relay the response](https://go.dev/doc/effective_go#chan_of_chan). The
channel is sent to the service along with the request. Here is the Go code, with relevant changes highlighted:

```golang
 1package main
 2
 3
 4import (
 5	"fmt"
 6	"time"
 7)
 8
 9type PrintRequest struct {
10	msg    string
11	respCh chan string
12}
13
14type PrintService struct {
15	printCh chan PrintRequest
16}
17
18func MakePrintService() PrintService {
19	printCh := make(chan PrintRequest)
20	go func() {
21		var req PrintRequest
22		for {
23			req = <-printCh
24			fmt.Printf("Got print request: \"%s\"\n", req.msg)
25			// Uncomment this to simulate a slow service.
26			// time.Sleep(3 * time.Second)
27			time.Sleep(500 * time.Millisecond)
28			req.respCh <- "success"
29		}
30
31	}()
32	return PrintService{
33		printCh: printCh,
34	}
35}
36
37func (ps *PrintService) Print(msg string) string {
38	respCh := make(chan string, 1)
39	ps.printCh <- PrintRequest{msg: msg, respCh: respCh}
40	return <-respCh
41}
42
43func main() {
44	service := MakePrintService()
45
46	for _ = range 2 {
47		resp := service.Print("Hello World")
48		fmt.Printf("PrintService response: %s\n", resp)
49	}
50}
```

This `Print()` does three different things. First, it mints a new response channel. This is the *setup* phase. Then,
it sends the request and awaits the response.

Turning to Racket, how would we achieve this? Where [`handle-evt`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28quote._~23~25kernel%29._handle-evt%29%29) was an event combinator to express *post-commitment* actions, there is a dual combinator [`guard-evt`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28lib._racket%2Fprivate%2Fmisc..rkt%29._guard-evt%29%29) for expressing *setup* actions.

[`guard-evt`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28lib._racket%2Fprivate%2Fmisc..rkt%29._guard-evt%29%29) is an event *maker*. It is a function that accepts a function, stores it somewhere, and returns an event. We will call this returned event a *guard event* to distinguish it clearly. When the guard event is *actually used* in
a [`sync`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28quote._~23~25kernel%29._sync%29%29), it does something special: It invokes the stored function, and expects the function to return an
event<sup>[1](https://nikhilism.com/post/2026/golang-racket-concurrency/#fn:1)</sup>. Then, the guard event “replaces” itself with the returned event. This naturally expresses
the setup phase.

```scheme
 1#lang racket/base
 2
 3(define my-evt
 4  (guard-evt
 5   (lambda ()
 6     (println "I will be printed only when used in a sync")
 7     ; A special built-in event that is never ready for synchronization.
 8     never-evt)))
 9
10(define my-evt2
11  (guard-evt
12   (lambda ()
13     (println "I will be printed only when used in a sync")
14     (timeout-evt 200))))
15
16; no output yet.
17
18(sync my-evt my-evt2)
19; Prints "I will be printed only when used in a sync" **twice**!
```

Coming back to our print-service, here is how we can use [`guard-evt`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28lib._racket%2Fprivate%2Fmisc..rkt%29._guard-evt%29%29) to create the response channel:

```scheme
 1#lang racket/base
 2(require racket/async-channel)
 3
 4(struct print-service (print-ch))
 5(struct print-req (msg resp-ch))
 6
 7(define (make-print-service)
 8  (define (server-loop print-ch)
 9    (let loop ()
10      (define req (channel-get print-ch))
11      (printf "Got print request: ~a~n" (print-req-msg req))
12      (sleep 0.5)
13      (async-channel-put (print-req-resp-ch req) 'success)
14      (loop)))
15
16  (define print-ch (make-channel))
17  (thread (λ () (server-loop print-ch)))
18  (print-service print-ch))
19
20(define (print-evt service msg)
21  (guard-evt (λ ()
22               (define resp-ch (make-async-channel 1))
23               (channel-put (print-service-print-ch service)
24                            (print-req msg resp-ch))
25               resp-ch)))
26
27(module+ main
28  (define service (make-print-service))
29  (for ([i (in-range 2)])
30    (sync (handle-evt (print-evt service "Hello World")
31                      (λ (resp) (printf "Printer response: ~a~n" resp))))))
```

We introduce the struct `print-req` that will hold the request details. `print-evt` returns a *guard* event obtained from `guard-evt`.
When called as a function, the lambda passed to `guard-evt` is not immediately invoked. Once `sync` starts executing at line 30, the lambda is invoked, and the set of events the `sync` is monitoring now contains `resp-ch`.

### Handling cancellation

So far we have demonstrated:

1. How events are descriptions of actions, and their effects only execute when used in `sync`.
2. How the CML model uses various combinators to frame setup and post-commitment actions.

We will now see how these features are combined to tackle the problem of cancellation/abandonment. In
concurrent systems, we often want to cancel some action because doing so will save resources or avoid some side effect. <sup>[2](https://nikhilism.com/post/2026/golang-racket-concurrency/#fn:2)</sup>

Common reasons are:

1. We are doing an action that could take unbounded time and we want to abandon it on timeout, or
2. The user or client is no longer interested in the result of the action, possibly because some other action succeeded.

In Go, the cancellation mechanism is established by convention. Functions that perform cancellable actions accept a
[`context.Context`](https://pkg.go.dev/context#Context), and monitor its [`Done()`](https://pkg.go.dev/context#Context.Done) channel concurrently with other actions (via [`select`](https://go.dev/ref/spec#Select_statements)). On the caller side,
helpers like [`WithTimeout`](https://pkg.go.dev/context#WithTimeout) or [`WithCancel`](https://pkg.go.dev/context#WithCancel) are used to close the channel backing [`Done()`](https://pkg.go.dev/context#Context.Done).

CML sees the hammer of events, and finds nails everywhere! Cancellation is expressed through *negative acknowledgement events* (*nack* events). *Unlike Go, this system is baked into the runtime.*

*The rest of this section may seem complicated or hard to follow, so it will help to remember that cancellation is the aspect in which CML is closest to Go.* In both, there is an event (`ctx.Done()` in Go) that must be monitored to detect cancellation. It is only a conventional difference in where and how the event is created. In Go, `Context` is created at the top-level, and threaded through every function. CML sticks to the compositional advantages of events and event-combinators. Cancellation is opted into by individual events, by using a special guard combinator, and callers are none-the-wiser.

As a quick refresher, here is how cancellation is expressed in Go using `Context`. Each function in the call heirarchy can add its own cancellation conditions, with custom timeouts, or direct calls to `cancel()`.

```go
 1func DoMoreStuff(ctx context.Context) {
 2  ...
 3}
 4
 5func DoStuff(ctx context.Context) {
 6  ctx, cancel := context.WithTimeout(ctx, 1*time.Second)
 7  defer cancel()  // Don't forget this.
 8  select {
 9        op1:
10            // do things
11        op2:
12            // do other things
13  }
14  // Whichever op is not selected can cancel based on monitoring Done()
15}
```

In Racket, [`nack-guard-evt`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28quote._~23~25kernel%29._nack-guard-evt%29%29) is the combinator that manufactures a negative acknowledgement (henceforth, *nack*) event. True to its name, it is [`guard-evt`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28lib._racket%2Fprivate%2Fmisc..rkt%29._guard-evt%29%29) with a slight twist. The maker function receives a special event as the first argument, like so:

```scheme
1#lang racket/base
2(nack-guard-evt (lambda (nack-evt)
3  ...))
```

Just like `guard-evt`, the maker function should return the actual event to be used in a `sync`. [`nack-guard-evt`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28quote._~23~25kernel%29._nack-guard-evt%29%29) establishes a one-to-one association between the nack event and the event returned from the maker function. Note that there are 3 different events to keep track of here, so let’s name them:

1. The event returned by nack-guard-event itself, which we will call the guard event.
2. The original event that the maker function will return, which will be a channel or similar.
3. The nack-evt that was created by nack-guard-evt and passed to the maker function.

The guard event is acting as a proxy for the original event, so, when used in a [`sync`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28quote._~23~25kernel%29._sync%29%29), three things can happen:

1. The original event is ready and gets picked by `sync`. In this case, nack-evt will never become ready.
2. The original event does not get picked by sync. In this case, nack-evt will become ready.
3. The sync is interrupted, the thread is killed or something throws an exception. nack-evt becomes ready in this case too!

Now, something else in the program needs to monitor the `nack-evt`’s readiness. This is conventionally done by spawning a separate thread to `sync` on that and *the actual operation that will lead to original event becoming ready*.

Here is a quick example to make things clear.

```scheme
1#lang racket/base
2(define ch (make-channel))
3
4(sync (nack-guard-evt (lambda (nack-evt)
5                        (thread (lambda ()
6                                  (sync nack-evt)
7                                  (println "nack-evt became ready!")))
8                        (channel-put-evt ch "hello")))
9      (timeout-evt 2000))
```

We wrap a `channel-put-evt` with `nack-guard-evt`. That is synchronized along with a `timeout-evt`.
When execution reaches the `sync` then `nack-guard-evt` is polled and executes its function.
The function spawns a new thread to monitor the `nack-evt`, and then returns the actual event on which `sync` should try to synchronize.
In this case, we are returning a `channel-put-evt` that will *never* become ready because nothing is trying to read from the channel.
After 2 seconds, this will print `nack-evt became ready!`.

### Cancellation in the print service

To demonstrate a detailed example of nack events, we will make two minor improvements to our print service. When the
print service is handling a request but the user cancels it, we would like to handle this gracefully. There are
two points at which we want to behave differently based on cancellation:

1. If the operation is cancelled when submitting the request to the service, we can avoid submitting a request entirely.
2. When the print service finishes the print and wants to respond, we want to respond only if the client is still listening. Previously, we solved this by using buffered channels. We can achieve the same result using nack events.

Here is the Go version.

```go
 1package main
 2
 3import (
 4	"context"
 5	"fmt"
 6	"time"
 7)
 8
 9type PrintRequest struct {
10	msg    string
11	respCh chan string
12	ctx    context.Context
13}
14
15type PrintService struct {
16	printCh chan PrintRequest
17}
18
19func MakePrintService() PrintService {
20	printCh := make(chan PrintRequest)
21	go func() {
22		var req PrintRequest
23		for {
24			req = <-printCh
25			fmt.Printf("Got print request: \"%s\"\n", req.msg)
26			time.Sleep(1 * time.Second)
27			select {
28			case req.respCh <- "success":
29			case <-req.ctx.Done():
30				fmt.Printf("Unable to respond to client who requested printing %s\n", req.msg)
31			}
32		}
33	}()
34	return PrintService{
35		printCh: printCh,
36	}
37}
38
39func (ps *PrintService) Print(ctx context.Context, msg string) (string, error) {
40	respCh := make(chan string, 1)
41	select {
42	case ps.printCh <- PrintRequest{msg: msg, respCh: respCh, ctx: ctx}:
43	case <-ctx.Done():
44		return "", fmt.Errorf("Printer did not accept request %s!", msg)
45	}
46	select {
47	case resp := <-respCh:
48		return resp, nil
49	case <-ctx.Done():
50		return "", fmt.Errorf("Timeout waiting for response")
51	}
52}
53
54func main() {
55	service := MakePrintService()
56
57	for i := range 2 {
58		ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
59		defer cancel()
60		resp, err := service.Print(ctx, fmt.Sprintf("Hello %d", i))
61		if err != nil {
62			fmt.Printf("PrintService response error: %s\n", err)
63		} else {
64			fmt.Printf("PrintService: %s\n", resp)
65		}
66	}
67	// Wait a bit to see prints from the service
68	time.Sleep(5 * time.Second)
69}
```

Now Racket. First, let’s put the `nack-evt` in the `print-req` struct.

```scheme
1(struct print-req (msg resp-ch abandoned-evt))
```

`print-evt` will send that to the service, and the service can [`sync`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28quote._~23~25kernel%29._sync%29%29) on it while attempting to put the result in
`resp-ch`.

```scheme
 1(define (make-print-service)
 2  (define (server-loop print-ch)
 3    (let loop ()
 4      (define req (channel-get print-ch))
 5      (define abandoned-evt (print-req-abandoned-evt req))
 6      (printf "Got print request: ~a~n" (print-req-msg req))
 7      (sleep 1)
 8      (sync (channel-put-evt (print-req-resp-ch req) 'success)
 9            abandoned-evt)
10      (loop)))
11
12  (define print-ch (make-channel))
13  (thread (λ () (server-loop print-ch)))
14  (print-service print-ch))
```

Here is the event construction. Rather than send the request to the service with a blocking put, we spawn a thread, and immediately return the response channel. When `print-evt` is used in a `sync`, if that `sync` selects another event, then `nack-evt` becomes ready. We never put the request into the print service channel.

```scheme
1(define (print-evt service msg)
2  (nack-guard-evt
3   (λ (nack-evt)
4     (define resp-ch (make-channel))
5     (thread (λ ()
6               (sync nack-evt
7                     (channel-put-evt (print-service-print-ch service)
8                                      (print-req msg resp-ch nack-evt)))))
9     resp-ch)))
```

Here is the full code sample, with an intentionally short timeout and prints that show the nacks in action.

```scheme
 1#lang racket/base
 2
 3(define (timeout-evt msec)
 4  ; alarm-evt is roughly equivalent to WithDeadline. Translate a relative timeout to a deadline.
 5  (alarm-evt (+ (current-inexact-monotonic-milliseconds) msec) #t))
 6
 7(struct print-service (print-ch))
 8(struct print-req (msg resp-ch abandoned-evt))
 9
10(define (make-print-service)
11  (define (server-loop print-ch)
12    (let loop ()
13      (define req (channel-get print-ch))
14      (define abandoned-evt (print-req-abandoned-evt req))
15      (printf "Got print request: ~a~n" (print-req-msg req))
16      (sleep 1)
17      (sync (channel-put-evt (print-req-resp-ch req) 'success)
18            (handle-evt
19             abandoned-evt
20             (λ (_)
21               (printf "Unable to respond to client who requested printing ~v~n"
22                       (print-req-msg req)))))
23      (loop)))
24
25  (define print-ch (make-channel))
26  (thread (λ () (server-loop print-ch)))
27  (print-service print-ch))
28
29(define (print-evt service msg)
30  (nack-guard-evt
31   (λ (nack-evt)
32     (define resp-ch (make-channel))
33     (thread (λ ()
34               (sync (handle-evt nack-evt
35                                 (λ (_) (printf "Abandoning request ~v~n" msg)))
36                     (channel-put-evt (print-service-print-ch service)
37                                      (print-req msg resp-ch nack-evt)))))
38     resp-ch)))
39
40(module+ main
41  (define service (make-print-service))
42  (for ([i (in-range 2)])
43    (sync (handle-evt (print-evt service (format "Hello ~a" i))
44                      (λ (resp) (printf "Printer response: ~a~n" resp)))
45          (handle-evt
46           (timeout-evt 200)
47           (λ (_)
48             (printf "Printer did not respond within 200ms on attempt ~v!~n"
49                     i))))))
```

```
Got print request: Hello 0
Printer did not respond within 200ms on attempt 0!
Printer did not respond within 200ms on attempt 1!
Abandoning request "Hello 1"
Unable to respond to client who requested printing "Hello 0"
```

The first attempt to sync on the `print-evt` at line 42 gets abandoned on the response, while the second one never even submits the
request.

Revisiting this block from the printing thread

```scheme
1(sync (channel-put-evt (print-req-resp-ch req) 'success)
2      abandoned-evt)
```

One may wonder: this synchronizes on a nack event and the channel put, but could neither be ready for a while? Would the print service be blocked from servicing requests in that case? This won’t happen. By construction, the two events are associated with each other. Either the client has lost interest in the `resp-ch`, in which case the `abandoned-evt` is ready, or it is in a [`sync`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28quote._~23~25kernel%29._sync%29%29) where `resp-ch` is one of the contenders for selection. Given that this print thread is now able to offer a value to the `resp-ch`, the two sides can immediately rendezvous and proceed, as long as the system is not otherwise CPU starved.

*Negative acknowledgement events are a really neat way to express cancellation, because they take the idea of events and cheap threads and apply it to the problem of cancellation, instead of introducing any new primitives.*

I hope that this journey through the print service gave you a glimpse of why the CML model is powerful and expressive:

1. We were able to use the event combinators to encapsulate event operations, such that the `print-evt` API never really changed, even as we layered on new capabilities.
2. To handle cancellation, we didn’t have to deal with a new concept of Context, nor did any other part of the program need to know that `print-evt` needed to do something on cancellation.
3. If the caller wanted to queue up multiple print jobs, they could easily do so, keep the events in a list, then wait for all of them to finish.

## Wrapping up loose threads

One of the things we have done with abandon in our Racket code is spawning threads and not worrying about shutting them down. Several of these threads seem to block on actions that may *never* unblock. In Go, this is a major source of bugs. The blocked goroutine never makes progress, and leaks its memory as well as any values it keeps alive. See the [go1.26 release
notes](https://go.dev/doc/go1.26#goroutineleak-profiles) for an example. Such leaks often have no side effects except slowly
increasing memory usage.

If the intent of Go is to
make goroutines too cheap to meter (an idea CML shares), then it should make them easier to use without requiring programmers to always consider how best to shut them down so that they don’t leak.

CML addresses this, which is why we have been so care-free. **If a thread is waiting only on a blocking operation on events and there are no other
live references to either the thread or the events involved in the selection, then the thread is eligible for garbage
collection and eventual termination.**

This is a key ability that makes the CML concurrency model easier to use. The *Concurrent Programming in ML* book specifically calls it out:

> In CML, however, these blocked threads are not a problem because they will be automatically garbage collected. When a
> thread is blocked waiting for a synchronous operation to be enabled, its state is only reachable through the data
> structures associated with the operation (e.g., through the channel waiting queue, when the thread is sending a
> message). If those data structures are not reachable from some active thread, then both they, and the blocked thread,
> will be garbage collected. […] This style of speculatively spawning threads to send communication that might never
> be accepted is an important CML programming technique.

Racket [retains these semantics](https://docs.racket-lang.org/reference/threads.html#:~:text=A%20thread%20that%20has%20not%20terminated%20can%20be%20garbage%20collected), even being careful with
[`thread-dead-evt`](https://docs.racket-lang.org/reference/threads.html#%28def._%28%28quote._~23~25kernel%29._thread-dead-evt%29%29).
[Here](https://gist.github.com/nikhilm/126757fd5b37f6b02451c96c26dcf4c1) is a slight variant of the above program
demonstrating the Racket service thread getting garbage collected when the service is no longer referenced.

Notably, there is an [issue](https://github.com/golang/go/issues/19702) from March 2017, proposing similar semantics for
goroutines. In Go 1.27, a [leak detector](https://go.dev/doc/go1.27#goroutineleak-profiles) was shipped that uses
similar semantics. Neither the proposal nor the [paper](https://users-cs.au.dk/~amoeller/papers/golf/paper.pdf) mentions
that this capability is available in another ecosystem, suggesting that not many people are aware of it.

Retrofitting CML’s event system onto Go is not realistic at all. However, *allowing goroutines to be collected seems something Go should seriously consider in later language versions*.

The central idea behind Concurrent ML is simple - represent communication operations as values independently of their execution. Its effects are far-reaching. The separation allows composing and encapsulating these operations in a way Go cannot. The same abstraction can model choice (Go’s [`select`](https://go.dev/ref/spec#Select_statements)) and cancellation. Choice can have reasonably strong guarantees that *only one operation makes progress*, which allows expressing many mutual-exclusion requirements. It can express setup and post-commitment actions in a uniform way. There is truly a lot of elegance in this idea.

Thread-aware GC then allows ergonomic use of the event mechanism, without worrying about leaks or needing to layer accidental complexity.

This makes CML an interesting alternative to Go’s channels-and-select approach, as well as the `async/await` minima<sup>[3](https://nikhilism.com/post/2026/golang-racket-concurrency/#fn:3)</sup> that lots of other languages have settled on.

The CML model is worth studying even if you never intend to use it in production. If you’re reaching for Go for your next side project, consider reaching for Racket instead!

*Thanks to Michael Dresser for feedback and discussion.*

## References

1. Go Channels are bad and you should feel bad—an old post outlining some of the pitfalls of Go channels, and suggesting, even back then, that goroutines and channels should opt-in to garbage collection.
2. Concurrent Programming in ML by John H. Reppy—the canonical book on CML, which collects information from the various Concurrent ML papers and presents several sophisticated examples of applying it to real software. This is out of print and hard to get, but worth it. It lays out the CML philosophy in a coherent narrative instead of working through the various papers.
3. Andy Wingo has travelled some of this path across 3 posts, but with fewer examples:
  1. concurrent ml versus go — wingolog
  2. is go an acceptable cml? — wingolog
  3. An incomplete history of language facilities for concurrency — wingolog
4. *Kill-Safe Synchronization Abstractions* by Matthew Flatt and Robert Bruce Findler—introduces the CML primitives in Racket, then adds some more Racket-specific magic to create concurrent abstractions that are not only atomic with respect to multiple threads but also remain atomic in the presence of thread termination.
5. *A Design Space Exploration of Async/Await* by Gray, Krishnamurthi and Crichton—a fantastic recent paper teasing out the various aspects of async/await implementations and giving names to each aspect.

## Appendix A: Events beyond channels

Since Go sticks to CSP’s original model <sup>[4](https://nikhilism.com/post/2026/golang-racket-concurrency/#fn:4)</sup>, it allows selection only on channels.
In this essay, we have been using channels to highlight the improvements CML makes over Go, and describe the event model. However, it is important to remember that events *are a general purpose abstraction* over any communication operation, being able to describe:

- Network socket operations
- Arbitrary file descriptors
- Several in-language APIs, such as semaphores, threads and subprocesses

The original CML code and the Racket standard library provide event-based mechanisms for all of these. File descriptors from third-party libraries can be opted into the system, as can be custom, polling-based mechanisms. Here is a simple example of watching for changes to a file to demonstrate the versatility:

```scheme
1#lang racket/base
2(sync
3 (handle-evt
4  (filesystem-change-evt "<path to a file>")
5  (λ (_) (printf "File changed!~n"))))
```

This ability is not just a convenience wrapper. The Go equivalent cannot *just* spawn a goroutine to do the operation and then respond back on a channel that then gets used in a [`select`](https://go.dev/ref/spec#Select_statements). For example, Racket provides [`write-bytes-avail-evt`](https://docs.racket-lang.org/reference/Byte_and_String_Output.html#%28def._%28%28quote._~23~25kernel%29._write-bytes-avail-evt%29%29), which attempts to write bytes to a port (stream/[`io.Writer`](https://pkg.go.dev/io#Writer) equivalent). It can be directly used in a [`sync`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28quote._~23~25kernel%29._sync%29%29). It *guarantees* that:

1. Either the event was selected, and at least some of the bytes were written to the port, or
2. The event did not get selected, and so no bytes were written.

As far as I know, it is not possible to provide such an API in Go. With a separate goroutine, the *commit point* ends up becoming the channel operation to relay the result, and not the I/O operation itself.

Rust Futures are the closest to CML events in several ways. They use polling-based readiness checks, which are a prerequisite for the CML model. `tokio::select!` is a macro that presents semantics similar to Go. However, Rust Futures differ in other ways that prevent building the CML model on top of them.

## Appendix B: A small aside on the maker function

Both [`guard-evt`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28lib._racket%2Fprivate%2Fmisc..rkt%29._guard-evt%29%29) and [`nack-guard-evt`](https://docs.racket-lang.org/reference/sync.html#%28def._%28%28quote._~23~25kernel%29._nack-guard-evt%29%29) have relied on *maker functions* being passed to them. In this explainer I’ve assumed that the maker function is *always* called when used in `sync`. This is not actually the case. If one of the other events passed to `sync` is already *ready for synchronization*, then, based on pseudo-randomness, there is a possibility that it will immediately get selected, and no other event will even be polled. In such cases, the maker function will *NOT* be called. This is generally fine, since it is identical to the operation never being attempted. In our print example, this would mean the print request is never sent.

1. It doesn’t strictly have to return an event, it can also return a value, but that value will be swallowed and the returned event will be immediately ready, which is not very valuable. [↩︎](https://nikhilism.com/post/2026/golang-racket-concurrency/#fnref:1)
2. Cancellation is one of the hardest parts of designing a good concurrency model. A good model is important, but it also often requires users to be aware of and take great care about their own usage of the model. Take a look at the references for an exploration of the design space. [↩︎](https://nikhilism.com/post/2026/golang-racket-concurrency/#fnref:2)
3. I think async-await was a bad model for most languages, apart from Rust. You are welcome to reach out to me for further discussion or wait for a subsequent essay. I am extremely happy that Java followed in Go’s footsteps rather than C#, JavaScript and Python. [↩︎](https://nikhilism.com/post/2026/golang-racket-concurrency/#fnref:3)
4. The original CSP from 1978 did not have named channels. They were introduced in 1985, and this is the model Go uses. [↩︎](https://nikhilism.com/post/2026/golang-racket-concurrency/#fnref:4)
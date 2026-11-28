Good exception handling is difficult in any language, but all the more so in
Haskell, where asynchronous exceptions mean that code can be interrupted at
almost any point. In this blog post we will discuss a series of recommendations,
focusing on three goals:

1. Ensure that allocated resources will be deallocated (avoid leaks)
2. Ensure that code can always make progress (avoid getting stuck)
3. Ensure that failures reach the code that can deal with them (don’t catch what you can’t handle)

As we will see, satisfying all three of these goals together can be tricky, and
sometimes they are in direct tension.

> This is part one of our series on exceptions.
>
> **Part 1: Exception best practices (this blog post)**
>
> Part 2: “When an `interruptible` call isn’t interruptible”, which will be
> published soon, discusses interruptible foreign calls: how they are meant to
> work, why they do not always work, and how to address that.
>
> Part 3: “(Some) Exceptions in Haskell are resumable”, also to be published
> soon, discusses asynchronous exceptions in pure code, resulting in resumable
> exceptions, and how we might generalize that to IO code.
>
> We’re also still planning two further parts: one on composing masking
> operations, and one exploring how the problems discussed in part 3 can be
> resolved.

## Baseline

In this first section we recap the most important concepts that we will need
to understand before we can discuss best practices.

### Throwing and catching exceptions

An exception is thrown with [`throwIO`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Control-Exception.html#v:throwIO) and caught with
[`catch`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Control-Exception.html#v:catch); in both cases the type of the value that is thrown must be
an instance of the `Exception` class:

```
data MyException = MyException
  deriving stock (Show)
  deriving anyclass (Exception)

baseline :: IO ()
baseline = action `catch` handler
  where
    action :: IO ()
    action = throwIO MyException

    handler :: MyException -> IO ()
    handler = print
```

It is often more convenient to use [`handle`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Control-Exception.html#v:handle), which is just
`catch` with its arguments flipped:

```
baseline :: IO ()
baseline = handle handler $ action
```

Before `throwIO` can throw the exception, it must first wrap it in the
`SomeException` envelope, which carries dynamic typing information and
[exception annotations](https://www.well-typed.com/blog/2026/05/lay-annotation-land/):

```
data SomeException = forall e. (..) => SomeException e
```

This dynamic typing information is used by `catch` to ensure that only
exceptions of the desired type are caught (that is, determined by the type of
the exception handler).

### Asynchronous exceptions

*Synchronous* exceptions are exceptions that are raised as a direct consequence
of executing the program itself. Haskell also supports *asynchronous*
exceptions, which instead can occur at any point during execution[<sup>1</sup>](https://www.well-typed.com/blog/2026/11/exception-best-practices/#fn1). Consider the following example:

```
asyncExample :: IO ()
asyncExample = action `catch` handler
  where
    action :: IO ()
    action = threadDelay 10_000_000

    handler :: MyException -> IO ()
    handler = print
```

It might seem that the handler should never run, but that is not necessarily
the case:

```
main :: IO ()
main = do
    me <- myThreadId
    _  <- forkIO $ do
      threadDelay 5_000_000
      throwTo me MyException
    asyncExample
```

If `throwIO` is the prototypical way to throw a synchronous exception,
[`throwTo`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Control-Exception.html#v:throwTo) is its asynchronous sibling, and throws an exception
to an arbitrary thread, although in practice it is rarely called directly;
instead, it is a building block for other abstractions:

- `timeout` throws a `Timeout` exception to the thread when the time is up
- `killThread` throws `ThreadKilled`
- Pressing CTRL-C results in a `UserInterrupt` exception in the main thread
- The async library uses throwTo to cancel threads whose result is no longer needed (for example, the losing thread in a `race`)

Without asynchronous exceptions, none of this would be possible in general: the
code being cancelled would have to check, at regular intervals, whether it
should stop.

### Async exception safety

Consider this code that attempts to read the first line of a file; it tries to
make sure that the file handle is closed again if an exception is raised during
reading:

```
readFirstLineBROKEN :: IO String
readFirstLineBROKEN = do
    h <- openFile "example.txt" ReadMode
    {- what if an exception is raised here? -}
    action h `catch` handler h
  where
    action :: Handle -> IO String
    action h = do
        line <- hGetLine h
        hClose h
        return line

    handler :: Handle -> SomeException -> IO a
    handler h e = do
        hClose h
        throwIO e
```

The problem in this code is *in between the lines*; specifically, after the
`openFile` and before the `catch`. The solution is to temporarily prevent
asynchronous exceptions from being raised using [`mask`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Control-Exception.html#v:mask), and only
enable them again once we are safely in the scope of an exception handler:

```
readFirstLineLOWLEVEL :: IO String
readFirstLineLOWLEVEL =
    mask $ \unmask -> do
      h <- openFile "example.txt" ReadMode
      unmask (action h) `catch` handler h
```

## Catching exceptions

### Bracket

The pattern in `readFirstLineLOWLEVEL` is so common in Haskell that it has its
own combinator, called [`bracket`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Control-Exception.html#v:bracket); it takes three arguments,
one to acquire a resource, one to release it again, and then the body that
uses the resource. This means that the recommended, and idiomatic, way to
write `readFirstLine` is

```
readFirstLine :: IO String
readFirstLine =
    bracket (openFile "example.txt" ReadMode) hClose $ \h ->
      hGetLine h
```

One downside of this idiom is that the exception handler no longer gets access
to the exception. For example, if we wanted to log any exceptions that occurred
while we were reading the file, along with the position in the file when the
exception was thrown, we would not be able to do so with the standard `bracket`.
It is of course always possible to drop back down to the low-level `mask`
combinator, but in most cases it is probably better to instead use
[`generalBracket`](https://hackage-content.haskell.org/package/exceptions-0.10.12/docs/Control-Monad-Catch.html#v:generalBracket) from the
[exceptions](https://hackage.haskell.org/package/exceptions) package. When using `generalBracket`, the
handler is told how the body terminated, and can also produce a result of its
own (returned only on successful termination[<sup>2</sup>](https://www.well-typed.com/blog/2026/11/exception-best-practices/#fn2)).

```
readFirstLineLOGGING :: IO String
readFirstLineLOGGING = fmap fst $
    Exceptions.generalBracket (openFile "example.txt" ReadMode) handler $ \h -> do
      hGetLine h
  where
    handler :: Handle -> Exceptions.ExitCase String -> IO ()
    handler h exitCase = do
        case exitCase of
          Exceptions.ExitCaseException e -> do
            pos <- hTell h
            putStrLn $ "Exception at position " ++ show pos
                    ++ ": " ++ displayException e
          _otherwise ->
            return ()
        hClose h
```

(The reason for the `fmap` is that `generalBracket` allows the deallocation
callback to return an additional value; here we just ignore it.)

### Catching “all” exceptions

Consider this version of `readFirstLine` that tries again when an exception
happens; perhaps the file we’re trying to read might be locked by another
process, and we just want to keep trying until we succeed:

```
keepTryingBAD :: IO String
keepTryingBAD = do
    mLine <- (Just <$> readFirstLine) `catch` handler
    case mLine of
      Just line -> return line
      Nothing   -> keepTryingBAD
  where
    handler :: SomeException -> IO (Maybe String)
    handler e = do
        putStrLn $ "Got " ++ displayException e ++ " while reading. Trying again"
        threadDelay 10_000
        return Nothing
```

Code like this with a blanket exception handler that catches *all* exceptions
(by catching exceptions of type `SomeException`) is problematic. The obvious
problem is that while some synchronous exceptions might be transient (“file
locked”), others might not (“invalid path”); you probably don’t want to retry on
the latter. The less obvious problem is that you almost certainly don’t want to
retry on asynchronous exceptions at all: exceptions such as a
[Timeout](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/System-Timeout.html#t:Timeout) or [`UserInterrupt`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Control-Exception.html#t:AsyncException)
(CTRL-C) should almost certainly be honoured.

My advice therefore is as follows:

1. In general, do not catch all exceptions (SomeException) unless you are doing so for the purposes of resource reclamation, and you will rethrow the exception after (in which case you’d typically use bracket and friends).
2. Prefer to catch specific exceptions; that is, exceptions of a specific type (see `catches` to catch exceptions of multiple types), or preferably even specific values (see `catchJust`).
3. If you must catch exceptions of unknown type, carefully consider whether you want to catch asynchronous exceptions also.

### Avoid unbounded handler nesting

Consider this variation of `keepTrying`; unlike in the previous section, we’re
now specifically only re-trying if the file is
[locked](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/System-IO-Error.html#v:isAlreadyInUseError), but we have a different error:

```
keepTryingALSOBAD :: IO String
keepTryingALSOBAD = do
    readFirstLine `catch` \e ->
      if isAlreadyInUseError e then do
        putStrLn $ "Got " ++ displayException e ++ " while reading. Trying again"
        threadDelay 10_000
        keepTryingALSOBAD
      else
        throwIO e
```

The problem with this version is that since the recursion happens *inside of*
the exception handler, we might end up with an unbounded number of handlers,
each next recursive call running under all of the exception handlers installed
so far. In the previous section `keepTryingBAD` did get this aspect right:
return a value that indicates whether or not we should retry, so that we can
retry outside the scope of the exception handler.

### Distinguishing sync and async exceptions

Consider the following code, which spawns an auxiliary thread which catches all
exceptions, and then shows that exception using
[`anythingToString`](https://hackage-content.haskell.org/package/recover-rtti-0.6.1/docs/Debug-RecoverRTTI.html#v:anythingToString) from my
[`recover-rtti`](https://hackage-content.haskell.org/package/recover-rtti) package, which bypasses any kind of
`Show` instance (indeed, any type class instance at all) and shows the exact
structure of the exception:

When we run this, we see (slightly cleaned up for readability, and some details
omitted):

```
SomeException (C:Exception (TrTyCon ..) ..) (ExceptionContext []) (
    SomeAsyncException (C:Exception (TrTyCon ..) ..) (
       ThreadKilled
     )
  )
```

The outermost wrapper is `SomeException`, with the dynamic typing information
`(TrTyCon ..)` and the (empty) list of exception annotations `(ExceptionContext [])`, which we already mentioned [above](https://www.well-typed.com/blog/2026/11/exception-best-practices/#baseline), and the innermost
constructor [`ThreadKilled`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Control-Exception.html#t:AsyncException) is the exception itself.
However, we additionally have *another* wrapper in between:
[`SomeAsyncException`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Control-Exception.html#t:SomeAsyncException).

This wrapper serves as a marker for async exceptions. It is *not* an indication
of how the exception was delivered (synchronously or asynchronously), and this
is as it should be: the marker indicates *intent* (“this exception was raised
because of external circumstances, rather than the code itself”). Asynchronous
exceptions are often caught and then rethrown synchronously (for example, see
the [section about `bracket`](https://www.well-typed.com/blog/2026/11/exception-best-practices/#bracket)), which changes the delivery mechanism
but not the intent.[<sup>3</sup>](https://www.well-typed.com/blog/2026/11/exception-best-practices/#fn3)

This does however mean that this intent must be stated explicitly. For example,
in our [first example of asynchronous exceptions](https://www.well-typed.com/blog/2026/11/exception-best-practices/#asynchronous-exceptions) we
asynchronously threw `MyException` to another thread, without ever wrapping
`MyException` in `SomeAsyncException`. If `MyException` was *intended* to be
used asynchronously, we should use a custom `Exception` instance:[<sup>4</sup>](https://www.well-typed.com/blog/2026/11/exception-best-practices/#fn4)

```
instance Exception MyException where
  toException   = asyncExceptionToException
  fromException = asyncExceptionFromException
```

Conversely, we can *test* if something is an async exception by checking for
the wrapper:

```
case fromException e of
  Just (SomeAsyncException e') -> putStrLn $ "Async: " ++ displayException e'
  Nothing -> putStrLn $ "Not an async exception"
```

## Cancellation

In general, it is good practice to ensure that code that might wait for an
unbounded amount of time, such as when acquiring a lock, can always be
*cancelled*, for example through a [`timeout`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/System-Timeout.html#v:timeout) or through
CTRL-C ([`UserInterrupt`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Control-Exception.html#t:AsyncException)). I’m intentionally using
cancellability instead of “interruptibility”, since the latter has a very
specific technical meaning in Haskell, as we shall discuss now.

*Note*. Foreign calls in Haskell (`safe` or `unsafe`) are not cancellable.
Alongside `safe` and `unsafe` there are also `interruptible` foreign calls,
which we will discuss in part 2 of this blog post series on exceptions. The term
`interruptible`, when applied to foreign calls, is related to, but not the same
as, the “interruptible operations” we discuss here.

### Interruptibility

When we discussed [`bracket`](https://www.well-typed.com/blog/2026/11/exception-best-practices/#bracket), we glossed over one detail: it does not
unmask exceptions when it invokes the `acquire` callback to acquire the resource,
nor when it invokes the `release` callback to release it again. This is a thorny
subject that we have written about before ([Dealing with Asynchronous Exceptions
during Resource Acquisition](https://www.well-typed.com/blog/97/)); here we highlight the
two most important concepts only.

First, even with async exceptions masked, *interruptible* operations can still
receive exceptions; paraphrasing [the paper](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/07/asynch-exns.pdf) slightly: “Any
operation which may need to wait indefinitely for a resource may receive
asynchronous exceptions even within an enclosing `mask`, but only while the
resource is unavailable”. The canonical example is `takeMVar`, which can receive
exceptions as long as it hasn’t managed to take the `MVar` yet, making a
pattern such as this safe:

```
withLock :: MVar () -> IO a -> IO a
withLock mvar criticalSection =
    bracket (takeMVar mvar) (putMVar mvar) $ \() ->
      criticalSection
```

For example, the `timeout` in

will still be able to interrupt the `takeMVar`. Unfortunately, interruptibility
is not visible from a function’s type, and is typically not even documented; for
example, `putStrLn` is interruptible (because deep down its bowels it calls
`takeMVar` somewhere on the `MVar` buried inside a `Handle`), which means that
this variation on `withLock` is broken:

```
withLockBROKEN :: MVar () -> IO a -> IO a
withLockBROKEN mvar criticalSection =
    bracket (takeMVar mvar >> putStrLn "Acquired!") (putMVar mvar) $ \() ->
      criticalSection
```

The presence of `putStrLn` essentially pokes a hole in the careful masked state
that `bracket` provides: if an asynchronous exception arrives after the
`takeMVar` succeeds but before the `putStrLn`, the exception *can* be thrown (if
there is contention for that handle `MVar`), and the `putMVar` will never run,
leaving the lock forever unusable. A good intuition is to keep `acquire` and
`release` as simple as possible; in the next few sections we will study some more
involved cases.

### Acquiring multiple resources

When acquiring multiple resources, it is important that we either acquire all of
them or none of them (atomicity). This means we need to worry about previously
acquired resources when we get (synchronous or asynchronous) exceptions while
acquiring more. The easiest option is to nest `bracket`:

```
withMVars :: MVar a -> MVar b -> (a -> b -> IO c) -> IO c
withMVars ma mb k =
    bracket (takeMVar ma) (putMVar ma) $ \a ->
    bracket (takeMVar mb) (putMVar mb) $ \b ->
      k a b
```

Sometimes however the specific way that resources must be acquired and released
does not allow for simple lexical scoping like this; or perhaps only offering a
“with” (`bracket`) style API is too limiting at call sites. If you need to
provide an API that *acquires* multiple resources, you have to think about how
to deal with the presence of interruptible operations; for example, you might do
something like

```
-- | Take both MVars
--
-- Intended to be run with async exceptions masked.
takeMVars :: MVar a -> MVar b -> IO (a, b)
takeMVars ma mb = do
    a <- takeMVar ma
    b <- takeMVar mb `onException` putMVar ma a
    return (a, b)
```

There is no point calling `mask` *inside of* `takeMVars`, because if the
enclosing context does not have exceptions masked, then leaving the scope of
that inner `mask` could result in an async exception being delivered at that
point.

In general this can be quite tricky to get right, and it is often better to try
and avoid solving this problem at all. For the case of `MVar`-like resources,
the obvious alternative is to use `TMVar`s instead, and just take both `TMVar`s
inside a single transaction.

### Releasing multiple resources

If you must release multiple resources, you should ensure that if one
resource fails to release cleanly and throws an exception, you still release
the remainder; one option is to chain using `finally`:

```
releaseA `finally` releaseB `finally` ..
```

In the standard `bracket acquire release body` pattern, if `release` fails with
an exception, but it itself was invoked because of an exception in `body`, it’s
debatable which exception should be propagated. For current GHC versions the
exception from `release` is propagated, but starting with GHC 10.0, the choice
is dissolved entirely: the exception from `release` [will be propagated with a
`WhileHandling` annotation of the original exception](https://www.well-typed.com/blog/2026/05/lay-annotation-land/#ghc-10.0).

We will consider [*async* exceptions during
`release`](https://www.well-typed.com/blog/2026/11/exception-best-practices/#async-exceptions-during-release) a bit further down.

### Non-interruptible operations

It is also possible to mask exceptions so that even interruptible operations can
no longer receive exceptions by using
[`uninterruptibleMask`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Control-Exception.html#v:uninterruptibleMask) instead of `mask`:

```
uninterruptibleMask $ \unmask -> do
    a <- takeMVar ma
    b <- takeMVar mb
    ..
```

This is safer in the sense that the `takeMVar mb` cannot throw an exception, but
*less safe* because this code is now no longer cancellable: timeouts,
user-interrupts (CTRL-C) etc. will not have any effect. To solve that you’d have
to *poll:* explicitly check whether any async exceptions are waiting to be
delivered, for example using [`unsafeUnmask`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/GHC-IO.html#v:unsafeUnmask)
([`allowInterrupt`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Control-Exception.html#v:allowInterrupt), which does exactly this under `mask`,
has no effect under `uninterruptibleMask`).

Another, possibly simpler, option to create an uninterruptible operation is to
fork an auxiliary thread to do the resource acquisition. Since this thread is
private, it is essentially immune to async exceptions.[<sup>5</sup>](https://www.well-typed.com/blog/2026/11/exception-best-practices/#fn5)
However, this will then still require some kind of communication protocol that
allows the child thread to clean up when it realizes the parent is no longer
interested; see also the discussion of [Threads](https://www.well-typed.com/blog/2026/11/exception-best-practices/#threads), below.

### Async exceptions during `release`

The ability to cancel code is often more important during resource acquisition
than it is during release; acquiring a lock can take an unbounded amount of
time, but releasing the lock does not. However, sometimes releasing a resource
can take an unbounded amount of time also. Perhaps releasing the resource
literally *is* acquiring a lock, perhaps to modify some kind of worker pool:

```
releaseWorker :: Pool -> Worker -> IO ()
releaseWorker pool _ = withLock pool.lock $ ..
```

Or perhaps the resource is a connection to a server and disconnecting requires
some kind of closing handshake to ensure an orderly closure
(e.g. [TLS uses closure alerts to avoid truncation attacks](https://www.rfc-editor.org/info/rfc9846/#section-6)):

```
bracket (connectToServer ..) (closeConnection ..) $ \conn -> ..
```

In this case, all the same considerations apply as during resource acquisition:
the release callback is invoked with async exceptions masked, but interruptible
operations can still receive exceptions.

In some cases you may want to vary what the resource release function does,
depending on whether or not the body terminated with an exception, and depending
on the nature of that exception (see also [discussion of
`generalBracket`](https://www.well-typed.com/blog/2026/11/exception-best-practices/#bracket)). For example, you may (or may not) opt for an
[abortive closure of a TLS connection](https://www.rfc-editor.org/info/rfc9846/#section-6) after a timeout; or you may
(or may not) opt to close a file handle without flushing the buffer. Such
decisions are of course highly application specific; a timeout may simply mean
that the main action should be terminated, but the resource should still be
closed cleanly!

## Threads

Threads are a microcosm of the three goals that we set up at the start of this
blog post: we must avoid leaking threads, communication between threads can get
stuck, and exceptions thrown in threads often need to be dealt with outside of
those threads.

### Exception handler

New threads run with an exception handler that [silently
swallows](https://hackage-content.haskell.org/package/ghc-internal-9.1401.0/docs/src/GHC.Internal.Conc.Sync.html#real_handler) the asynchronous
[`ThreadKilled`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Control-Exception.html#t:AsyncException), as well as synchronous
[`BlockedIndefinitelyOnMVar`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Control-Exception.html#t:BlockedIndefinitelyOnMVar) and
[`BlockedIndefinitelyOnSTM`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Control-Exception.html#t:BlockedIndefinitelyOnSTM), which we will
revisit shortly. Any other exception is handled by the uncaught
exception handler, which [by default](https://hackage-content.haskell.org/package/ghc-internal-9.1401.0/docs/src/GHC.Internal.Conc.Sync.html#uncaughtExceptionHandler) simply
prints it (though [this can be changed](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/GHC-Conc.html#v:setUncaughtExceptionHandler)).

In general it is good practice to ensure no exception is ever uncaught.[<sup>6</sup>](https://www.well-typed.com/blog/2026/11/exception-best-practices/#fn6) In almost all cases you should therefore install an exception
handler in the new thread; what this handler should do will be application
specific, but we will consider one important class of problems in the next
section.

### Buffered interfaces

Consider a producer and consumer thread that communicate through a buffered
interface such as an `MVar`:

```
producer, consumer :: MVar Chunk -> IO ()
```

The `MVar` provides back-pressure, which is good: the producer can’t race ahead
and produce an unbounded number of chunks if the consumer is not consuming them.
However, if the producer aborts with an exception, the consumer will be left
waiting for the next chunk which will never arrive.

There are a number of ways to deal with this. Probably my favourite is to record
the exception in the buffer *itself*; this means that the consumer is forced to
consider what to do when the producer fails:

```
producer :: MVar (Either SomeException Chunk) -> IO ()
producer buffer = .. `catch` (putMVar buffer . Left)
```

Note that catching *all* exceptions here is correct: the consumer wants to know
if the producer disappeared, even if that was because of an async exception.

Another option, arguably more compositional, is to use STM, and record the
health of the producer separately from the consumer:

```
data Interface = Interface{
      health :: TVar (Maybe SomeException)
    , buffer :: TMVar Chunk
    }

producer :: Interface -> IO ()
producer iface = .. `catch` (atomically . writeTVar iface.health . Just)

getChunk :: Interface -> IO Chunk
getChunk iface = atomically $ do
    hasFailed <- readTVar iface.health
    case hasFailed of
      Nothing -> takeTMVar iface.buffer
      Just e  -> throwSTM e
```

If you choose this route, it is important to read both variables in a *single*
`atomically` block, to ensure that when the transaction is blocked waiting for
a chunk, it will be retried *either* when a new chunk becomes available *or*
when the health of the producer changes.

If you don’t signal failure in the producer in any way to the consumer, the
consumer *may* fail with a “blocked indefinitely on MVar” or “blocked
indefinitely on STM” exception. You should regard this strictly as a debugging
tool only, in the same category as [`Debug.Trace`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Debug-Trace.html). Do **not**
rely on it for your program logic: false negatives are common (where the
exception is not raised even though code might be blocked indefinitely), and
*if* you ever catch it, then [false positives are possible](https://well-typed.com/blog/2024/01/when-blocked-indefinitely-is-not-indefinite/)
(where code is *not* blocked indefinitely and yet the exception is raised).

### Masking state is inherited

New threads are spawned with [`forkIO`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Control-Concurrent.html#v:forkIO), and inherit the masking
state from their parent. We can take advantage of this fact to start a thread
which *starts* with exceptions already masked.

Consider the [`producer` thread example](https://www.well-typed.com/blog/2026/11/exception-best-practices/#buffered-interfaces) we saw earlier.
A naive attempt to spawn a new producer might look like this:

```
newProducerBROKEN :: IO (Interface, ThreadId)
newProducerBROKEN = do
    iface    <- Interface <$> newTVarIO Nothing <*> newEmptyTMVarIO
    producer <- forkIO $ do
                  {- what if an exception is raised here? -}
                  (..) `catch` (atomically . writeTVar iface.health . Just)
    return (iface, producer)
```

If the producer is spawned in this manner, but is killed before it installs the
exception handler, the consumer will be left waiting forever. For example, the
caller of `newProducerBROKEN` is given the `ThreadId`, so it may kill the
producer before the forked thread is ever scheduled. Masking asynchronous
exceptions from within the thread cannot help here: the exception might arrive
before we get a chance to call `mask`. Instead we must fork the thread *with
exceptions already masked*, by masking them in the *parent* thread.

However, we cannot use the normal `mask` function; the `restore` function that
it gives us will restore the masking state to what it was prior to the call to
`mask`; we instead want to ensure that the new thread really runs with
exceptions unmasked, independent of what the masking state in the parent was.
Function [`forkIOWithUnmask`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Control-Concurrent.html#v:forkIOWithUnmask) gives us precisely this:

```
newProducer :: IO (Interface, ThreadId)
newProducer = do
    iface    <- Interface <$> newTVarIO Nothing <*> newEmptyTMVarIO
    producer <- mask_ $ forkIOWithUnmask $ \unmask ->
                  unmask (..) `catch` (atomically . writeTVar iface.health . Just)
    return (iface, producer)
```

Note that there is a function in `base` that captures *nearly* this pattern:
[`forkFinally`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Control-Concurrent.html#v:forkFinally). However, `forkFinally` does not use
`forkIOWithUnmask`, but uses a regular `mask`, making it more sensitive to the
masking state of the thread in which it is invoked; in particular, you almost
certainly don’t want to call `forkFinally` inside the `acquire` callback of
`bracket` (see also [Bracketing thread creation](https://www.well-typed.com/blog/2026/11/exception-best-practices/#bracketing-thread-creation)
below).

### `throwTo` is synchronous

To kill a thread, you use `throwTo` to throw a
[`ThreadKilled`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Control-Exception.html#t:AsyncException) to the target thread; this is such a
common idiom, `base` provides [`killThread`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Control-Concurrent.html#v:killThread) that does exactly
this.

An important aspect of `throwTo` is that it is *synchronous*: it does not return
until the exception has been raised in the target thread. This can be convenient;
for example, consider a networking context in which we want to send a timeout
message after a certain period:

```
let sendTimeout :: IO ()
    sendTimeout = do
      threadDelay 10_000_000
      (..)
timer <- forkIO sendTimeout

(..)
killThread timer -- timeout no longer needed
(..)
```

The parent thread is guaranteed that the child thread won’t send the
notification anymore after the `killThread`, without the need for any explicit
synchronization with the child thread. It also has some downsides, however, as
we shall see in the next section.

### Bracketing thread creation

Threads are a resource like any other, and we should ensure that they get
cleaned up. It is tempting to write

```
bracket (forkIO ..) killThread $ \tid -> .. -- WRONG x 2
```

Both the `acquire` and the `release` of this example are wrong. First, as we saw
above, when we fork a new thread [it inherits the masking state from its
parent](https://www.well-typed.com/blog/2026/11/exception-best-practices/#masking-state-is-inherited). Since `bracket` runs the `acquire`
callback with exceptions masked, this means that the new thread will now run
with async exceptions masked at all times (modulo
[`unsafeUnmask`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/GHC-IO.html#v:unsafeUnmask)). However, even if we fix this by using
`forkIOWithUnmask` instead, there is still a problem:

```
bracket (forkIOWithUnmask $ \unmask -> ..) killThread $ \tid -> .. -- STILL WRONG
```

We saw above that [`throwTo` is synchronous](https://www.well-typed.com/blog/2026/11/exception-best-practices/#throwto-is-synchronous): it waits
until the exception is delivered to the child thread, which means it must wait
until the child thread can receive async exceptions. Because it might have to
wait, it is *interruptible*; and unlike `takeMVar`, which is interruptible only
if the `MVar` is not available, `throwTo` is *always* interruptible. This means
that if this `bracket` *itself* is executed by a thread that is killed, we might
not clean up the auxiliary thread. This is therefore an example of where the use
of `uninterruptibleMask_` is really justified:

```
bracket (forkIOWithUnmask ..) (uninterruptibleMask_ . killThread) $ \tid -> ..
```

This does mean that the parent thread (the one running this `bracket`) will be
cancellable only if the child thread is too; an *unjustified* use of
`uninterruptibleMask_` in the child thread (the [orderly closure
example](https://www.well-typed.com/blog/2026/11/exception-best-practices/#async-exceptions-during-release) we discussed above), resulting in
uncancellable child threads, propagates and results in uncancellable parent
threads.

## Library ecosystem

In this blog post we focused mostly on principles, not the larger ecosystem. We
cannot possibly give an exhaustive overview here, but there are a few packages
that we should briefly discuss. Two I can unreservedly recommend: `exceptions`
and `async`. The third, `safe-exceptions`, takes an opinionated stance on async
exceptions which you may or may not want to adopt; here we will only point out
some aspects to be aware of.

### `exceptions`

The `exceptions` package provides polymorphic versions of the standard exception
handling functions through a stack of type classes: `MonadThrow` for monads in
which we can throw exceptions, `MonadCatch` in which we can catch them, and
finally `MonadMask` in which we have `bracket` available. It’s mostly a
straight-forward generalization of the functions in `base`, with the exception
of `generalBracket`, [which we discussed already](https://www.well-typed.com/blog/2026/11/exception-best-practices/#bracket).

### `async`

As we saw [when we discussed threads](https://www.well-typed.com/blog/2026/11/exception-best-practices/#threads), dealing correctly with threads
is non-trivial, and `async` aims to make this better. It takes care of the
following things:

- It provides essentially a simplified form of the buffered interface we discussed above, albeit for threads that produce a single result; `wait` or `waitCatch` provide a way for the “consumer” to wait for the thread result.
- `withAsync` takes care of spawning new threads, ensuring that exceptions are masked when the new thread starts, and that the cancellation is uninterruptible.

Be aware, however, that cancelling a thread (implicitly through leaving the
scope of `withAsync`, or explicitly through [`cancel`](https://hackage-content.haskell.org/package/async-2.2.6/docs/Control-Concurrent-Async.html#v:cancel)),
doesn’t just kill the child thread, but waits for it to terminate. That can be
important: if the parent and the child thread shared any resources, the parent
can be sure that the child will not need them anymore. However, there are also
cases where the parent does not need to, or perhaps even *should* not, wait for
the child.

If you don’t want to use `withAsync`, some of the old problems come back:

- If you use async inside bracket, it creates a thread that will run with exceptions forever masked; use `asyncWithUnmask` instead.
- Similarly, you may need to use uninterruptibleCancel; see Bracketing thread creation.
- If you never wait on the new async at all, and it throws an exception, it won’t be handled at all, not even by the default exception handler (that is, it won’t even be printed). One option here is to use `link`, which will re-raise most exceptions thrown by the child in the parent thread, albeit wrapped in `ExceptionInLinkedThread`, which may be problematic for exception handlers on specific types.

### `safe-exceptions`

As mentioned, [`safe-exceptions`](https://hackage.haskell.org/package/safe-exceptions) takes an opinionated
stance on async exceptions, which is provided through a series of alternative
implementations of standard `base` functions: `catch`, `bracket`, `throwTo` and
others all behave subtly differently in `safe-exceptions` than they do
elsewhere. As such, *if* you choose to use this package, my strong
recommendation is to import the package qualified, so that use sites
(`Safe.catch`) are clearly distinguished from the standard functions.

The use of `safe-exceptions` should be a deliberate choice: **it is not a
drop-in replacement**. Refactoring existing code to import from
`Control.Exception.Safe` instead of `Control.Exception`, without making
additional changes, is unlikely to be correct.

The first important difference is that
[`Safe.catch`](https://hackage.haskell.org/package/safe-exceptions-0.1.7.4/docs/Control-Exception-Safe.html#v:catch) and related functions do not allow
you to catch async exceptions at all. This means that you don’t have to worry
about catching async exceptions in handlers that catch “all” exceptions, though
[you probably should not do that anyway](https://www.well-typed.com/blog/2026/11/exception-best-practices/#catching-all-exceptions). If you *do*
try to catch an async exception, the code will compile just fine, but the
handler will never run.

In the section on distinguishing sync and async exceptions, we discussed that
the difference is about [intent, not delivery
mechanism](https://www.well-typed.com/blog/2026/11/exception-best-practices/#distinguishing-sync-and-async-exceptions). We implied, though did
not spell it out, that this intent is stated statically, through the `Exception`
instance. However, in the implementation of `throwTo` in `safe-exceptions` this
intent is stated *dynamically:* `throwTo` will add an `AsyncExceptionWrapper`
around the exception being thrown if `toException` does not already add the
`SomeAsyncException` wrapper. This gives a catcher the ability to still see that
it was “intended to be asynchronous”, but it also means that even if that
catcher is defined using standard `catch`, and it has a handler for that exact
exception, it *won’t be able to catch it anymore* because the type match will
fail.[<sup>7</sup>](https://www.well-typed.com/blog/2026/11/exception-best-practices/#fn7)

The behaviour of `Safe.bracket` is also subtly different from standard
`bracket`. The most important difference is that it wraps the release callback
in `uninterruptibleMask_`. This means that the release callback does not need to
worry about async exceptions, but as we saw in the section on [async exceptions
during `release`](https://www.well-typed.com/blog/2026/11/exception-best-practices/#async-exceptions-during-release), this may not always be
safer: in the network example, `uninterruptibleMask_` around an orderly closure
could mean that the code will wait indefinitely for the network peer to respond,
and cannot be timed out or interrupted with CTRL-C.

The other difference in `bracket` is what happens when the release callback was
called because of an exception in the `body`: depending on the exact nature of
the two exceptions (sync or async), exceptions thrown by the release may be
silently swallowed, making it all the more important to [be careful if you’re
releasing multiple resources](https://www.well-typed.com/blog/2026/11/exception-best-practices/#releasing-multiple-resources).

## Conclusions

Writing code that does the right thing even when things go wrong can be quite
difficult; this is inherent, not accidental, complexity. Asynchronous exceptions
make this significantly more difficult still, but of course also come with a lot
of benefits; for example, without asynchronous exceptions a general combinator
such as `timeout` would not be possible. Exceptions also tend to be
non-deterministic, so leaked resources, stuck code, or unhandled failures may
not be noticed during testing. Nonetheless, with some good code hygiene many
problems can be avoided; hopefully the guidelines in this blog post can assist.

There are a few topics that we have not covered in this blog post:

- We have ignored pure exceptions. The (slightly but not entirely tongue-in-cheek) TL;DR is: avoid pure exceptions, but we will come back to this in much more detail in part 3 of this series.
- We have not discussed exception annotations at all, or how to preserve them; we covered this in detail in a previous blog post Exception Annotations: Lay of the Land, as well as in Unfolder episode 29: exceptions, annotations and backtraces.
- We have not discussed finalizers (for example on a ForeignPtr, or using System.Mem.Weak). Finalizers run at some point after an object has become unreachable, but there is no guarantee of when, or indeed whether, they run; they are therefore no substitute for bracket for resources that must be released promptly, such as locks or file handles.
- We have not discussed `ResourceT`, which is useful when resource lifetimes do not nest lexically: resources are registered with an enclosing scope, and released when that scope is exited.

Many thanks to [Anduril](https://www.anduril.com/) for sponsoring this
work.

1. The main reference here is [Asynchronous Exceptions in Haskell](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/07/asynch-exns.pdf) by Marlow et al.[↩︎](https://www.well-typed.com/blog/2026/11/exception-best-practices/#fnref1)
2. In addition to successful termination and abnormal termination with an exception, `generalBracket` also has a case for abnormal termination in monad stacks such as `ExceptT`. Since these are not strictly speaking exceptions, we will not discuss this any further in this blog post.[↩︎](https://www.well-typed.com/blog/2026/11/exception-best-practices/#fnref2)
3. There are reasons to avoid synchronously rethrowing asynchronous exceptions; see GHC [#2558](https://gitlab.haskell.org/ghc/ghc/-/work_items/2558), [#24189](https://gitlab.haskell.org/ghc/ghc/-/work_items/24189) and [#26368](https://gitlab.haskell.org/ghc/ghc/-/work_items/26368); however, those reasons are mostly orthogonal to our discussion here.[↩︎](https://www.well-typed.com/blog/2026/11/exception-best-practices/#fnref3)
4. For the general mechanism at work here, see [An Extensible Dynamically-Typed Hierarchy of Exceptions](https://simonmar.github.io/bib/papers/ext-exceptions.pdf).[↩︎](https://www.well-typed.com/blog/2026/11/exception-best-practices/#fnref4)
5. It would not be immune to async exceptions such as heap overflow, of course, but they are generally irrecoverable anyway. Strictly speaking it is not truly private either, as [`listThreads`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/GHC-Conc.html#v:listThreads) can be used to enumerate all threads.[↩︎](https://www.well-typed.com/blog/2026/11/exception-best-practices/#fnref5)
6. The only technical exception to this is [`exitFailure`](https://hackage-content.haskell.org/package/base-4.22.0.0/docs/System-Exit.html#v:exitFailure), which should only be called from the main thread, and will throw an `ExitCode` exception.[↩︎](https://www.well-typed.com/blog/2026/11/exception-best-practices/#fnref6)
7. Arguably, asynchronously throwing an exception with an `Exception` instance that does not use `asyncExceptionToException` and `asyncExceptionFromException` is a bug, but it’s probably a common one: simply `deriving Exception` is an easy mistake to make.[↩︎](https://www.well-typed.com/blog/2026/11/exception-best-practices/#fnref7)
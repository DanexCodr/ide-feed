Here is a program that, until July, never finished in Bun or Safari.

never.mjs

```
const p = Promise.resolve(1);
p.constructor = {
	get [Symbol.species]() {
		throw new Error("boom");
	},
};

console.log("before");
await p;
console.log("done");
```

Don't worry if this looks confusing. The JavaScript spec says that because the getter throws an error, then `await p` should also throw, and so the program should crash. Node.js does, but Safari 26 and Bun 1.3.14 print `'before'`, report the error, and then hang.

Safari 26 fails the same way as Bun:

![](https://alistair.sh/_next/static/immutable/media/traffic-lights-light.076k7um4vfh1l.png)

Bun and Safari both embed JavaScriptCore so the behaviour is the same - the promise is never settled! It is neither fulfilled nor rejected, so it stays pending forever. This was  [WebKit bug 318399](https://bugs.webkit.org/show_bug.cgi?id=318399). I fixed it in  [WebKit/WebKit#68749](https://github.com/WebKit/WebKit/pull/68749), and the fix was only +16 lines!

What went wrong?

## What `resolve` does

Let's quickly brush up on promises.

When you construct a new promise in JavaScript, the engine creates two functions,  `resolve` and `reject`, and passes them to the callback you pass to the promise constructor.

new-promise.js

```
new Promise((resolve, reject) => {
	console.log("I got my resolve function!", resolve);
	console.log("I got my reject function!", reject);
	resolve(42);
});

// In V8 this logs:
//		I got my resolve function! ƒ () { [native code] }
//		I got my reject function! ƒ () { [native code] }
```

The builtin helper function `Promise.resolve(value)` does the same thing by constructing a promise and immediately calling `resolve` with the value you passed (with the exception that if `value` is a promise, and has a  `.constructor` property equal to `Promise`, it is returned as is). A simple userland implementation would look like this:

promise-resolve.js

```
function PromiseDotResolve(value) {
	if (value instanceof Promise && value.constructor === Promise) {
		return value;
	}

	return new Promise(resolve => resolve(value));
}
```

The same is also true for literally writing `await 42`. The engine creates a promise and immediately calls `resolve(42)`, just like  `Promise.resolve()` does, and the same exception applies.

Many folks think of a promise as a value that can end in two ways - fulfilled with a value or rejected with a reason. This is a reasonable approximation since it maps pretty closely to how using promises actually feels when writing JavaScript day-to-day. Therefore, a naive implementation of a promise might look like this:

mediocre-promise.ts

```
type PromiseState<T> =
	| {type: 'pending'}
	| {type: 'resolved', value: T}
	| {type: 'rejected', value: unknown};

class MediocrePromise<T> {
	private state: PromiseState<T> = {type: 'pending'};
	private callbacks: Array<() => void> = []; // registered by .then()

	private resolve(value: T) {
		this.settle({type: 'resolved', value});
	}

	private reject(reason: unknown) {
		this.settle({type: 'rejected', value: reason});
	}

	private settle(state: PromiseState<T>) {
		this.state = state;
		for (const callback of this.callbacks) callback();
	}

	// For example's sake this is missing `constructor`, `then`, etc.
}
```

I've called it MediocrePromise. It has a pending state, a way to resolve with a value, and a way to reject with a reason. It even has a list of callbacks to run, just like a real promise! Is this a good implementation?

Sadly, no. It is not a good implementation. MediocrePromise misses an important difference between how resolving and rejecting work.

Let's start with rejections. Rejecting a promise is simple! Calling  `reject(reason)` marks the promise as rejected, with `reason` as the rejected value. Excellent! MediocrePromise implements rejections correctly!

Resolving is more complex. Calling `resolve(value)` does *not* store  `value` straight away. First, it checks whether `value` has a  `.then()` method. If it **doesn't** (e.g. a number, a string, an object without one, ..) the promise is **fulfilled** with `value` and we are done. Otherwise, if it **does** have a `.then()` method, `value` is treated like *another* promise. Our original promise is *not* settled yet and instead, `resolve` passes itself and the reject function to  `value.then(resolve, reject)`. Whichever of those functions  `value.then()` *eventually* calls is what settles the promise. Sorry, that was a mouthful. There's a diagram in a sec to explain. Bear with me.

The `resolve` function  [is defined in the spec](https://tc39.es/ecma262/#sec-promise-resolve-functions)  as the **resolve procedure**. To find out whether `value` has a  `.then`, it reads `value.then`, and a property read can run a getter, and a getter can throw (just like in our program at the beginning). So, looking for a `.then()` method on some value can result in three possible outcomes:

Our MediocrePromise is missing the extra check and additional behaviour!

This asymmetry exists because  ***a failure is not a pending operation***. When something fails, you **already** have the reason in your code (presumably an error)! So you can call `reject(reason)` immediately. This is not the case for the happy path of resolving, where a useful value might arrive later:

```
reject(new Error("bad request")); // the reason is right here
resolve(response.json());         // the body is still arriving
```

This is why the extra behaviour is only implemented in `resolve`.

In the path where `value.then` *is* a function, the spec considers  `value` to be a **thenable**. Promises are thenables, since they have a  `.then()` method. Any other object with a `.then()` method is a thenable too. Thenables work everywhere a promise would.

Simply put: a **thenable** is any value with a `.then()` method. Therefore, any promise is also a thenable.

For example:

```
// `thenable` is not a promise!
const thenable = {
	// resolve(thenable) calls this with the outer promise's resolve and reject
	then(resolve, _reject) {
		resolve(42);
	},
};

// resolve() called with the thenable
await new Promise(resolve => resolve(thenable)); // 42

// a .then callback returning the thenable
await Promise.resolve().then(() => thenable); // 42

// await on the thenable directly
await thenable; // 42
```

The spec calls the aforementioned process of passing the resolve/reject functions to a thenable's `.then()` **assimilation**. But, perhaps a friendlier word is  **flattening**: instead of holding the inner thenable as its value, the outer promise waits for it, so two layers become one.

Lastly, note that "resolved" isn't a real promise state. MediocrePromise also got this one wrong! Once `resolve` has been called the promise is **locked-in** to an outcome, but it can absolutely still be pending:

```
const inner = new Promise(() => {}); // never settles
const outer = new Promise(resolve => resolve(inner));
```

Here, `outer` was resolved, but it stays pending forever because  `inner` never settles. MediocrePromise's `resolved` state was actually the spec's definition of fulfilled.

## Railways

Let's go down a quick tangent.

Scott Wlaschin's article  [Railway Oriented Programming](https://fsharpforfunandprofit.com/rop/)  draws fallible code as a piece of track with one input and two outputs: a success track and a failure track.

Once a request hits the failure track it stays there, skipping every later step, until something at the end deals with the result. Wlaschin calls joining two pieces of the railway *binding* - not to be confused with JavaScript's `fn.bind()`. Rust folks might know binding as `and_then`, or maybe the `?` operator. They all mean the same thing: run the next bit of code only if the previous bit succeeded, otherwise pass the failure straight through.

Look at how the last step is skipped because the `update()` failed:

You can think of each piece of the railway as a function returning a `Result`. In statically typed programming languages, implementations of a `Result` type will usually accept **two type parameters**, the success type and the failure type, one per track. For example in Rust you could imagine a `validate` function's signature being:

```
fn validate(request: Request) -> Result<Request, ValidationError>
```

To chain `validate()` with the other steps using `and_then`, every piece has to fail with the *same* type. So instead of `ValidationError`, lets make each function return an `AppError`, an enum of every way a request can fail:

```
enum AppError {
	Validation(ValidationError),
	Database(DatabaseError),
	Network(NetworkError),
}

fn validate(request: Request) -> Result<Request, AppError> { /* ... */ }
fn update(request: Request) -> Result<Record, AppError> { /* ... */ }
fn send(record: Record) -> Result<Receipt, AppError> { /* ... */ }

validate(request).and_then(update).and_then(send) // Result<Receipt, AppError>
```

Promises in JavaScript kinda look a lot like this! There's a fulfilled track and a rejected track, and `.then(onFulfilled, onRejected)` is a switch between them.

## The job

As a reminder, here's that **resolve procedure** diagram again:

In the path on the right, where `value.then` is a function, the engine does not call the `.then()` immediately. Instead, the engine queues a job, which we call a microtask. The spec names this particular job a  [`NewPromiseResolveThenableJob`](https://tc39.es/ecma262/#sec-newpromiseresolvethenablejob)  and it is defined as follows:

> a. Let *resolvingFunctions* be CreateResolvingFunctions(*promiseToResolve*).
>
> b. Let *thenCallResult* be Completion(HostCallJobCallback(*then*,  *thenable*, « *resolvingFunctions*.[[Resolve]], *resolvingFunctions*.[[Reject]] »)).
>
> c. If *thenCallResult* is an abrupt completion, return ? Call(*resolvingFunctions*.[[Reject]], undefined, « *thenCallResult*.[[Value]] »).

Sorry, that's another mouthful. Let me translate:

1. Create a new resolve/reject function pair
2. Call the thenable's .then(resolve, reject) function (with the newly created resolve/reject functions)
3. If calling .then() throws, reject the promise with whatever was thrown

Remember that `.then` is simply whatever is defined on the thenable. If the thenable is a real promise, the method being called is the one on the prototype,  `Promise.prototype.then`.

Here's the important line of our program again:

```
p.constructor = {
	get [Symbol.species]() {
		throw new Error("boom");
	},
};
```

We only changed `p` here, so the global `Promise` is untouched.

Remember the exception from earlier? When you `await` a real promise whose  `constructor` is `Promise` (which, by default, is true for all promises), the engine takes a shortcut and waits on that promise directly. We just replaced `p.constructor`, meaning we cannot take the shortcut. Instead, the engine treats `p` in `await p` like any other value: it makes a fresh promise and calls `resolve(p)` on it.

`p` has a `.then()`, so it is a thenable, so `resolve(p)`  calls `p.then(resolve, reject)`. Now, we saw our program crash, so  `Promise.prototype.then` must somehow eventually be accessing  `p.constructor[Symbol.species]`, right? But why on earth would  `.then()` care about a `Symbol.species` getter?

It cares because `.then()` returns a *new* promise, which is what lets you chain `.then().then()`. If you subclass `Promise`, you'd expect  `.then()` to return an instance of your subclass, not a plain  `Promise`:

```
class MyPromise extends Promise {}
MyPromise.resolve(1).then(x => x) instanceof MyPromise; // true
```

So before a real promise's `then` does anything with its arguments, it works out which constructor to build the *new* promise with. It does this by first reading  `this.constructor` and then by reading `constructor[Symbol.species]`  (the spec calls this step  [`SpeciesConstructor`](https://tc39.es/ecma262/#sec-speciesconstructor)). Both are ordinary property reads and, as we found out, property reads can run getters, and getters can throw!

This is precisely what our original program at the beginning does! We made  `p.constructor` have a `Symbol.species` getter that throws, so  `p.then(resolve, reject)` throws during the species lookup, before it has stored `resolve` and `reject` as callbacks. Recall that Step C of  `NewPromiseResolveThenableJob` makes the engine reject the promise if calling  `.then()` throws - this is the spec-correct behaviour we saw in V8/Node.js.

So why do Safari and Bun hang instead of rejecting the promise?

JavaScriptCore had a fast path for the most-common case where the thenable is a real, normal promise, and that fast path did the species lookup *first*, only creating the resolve/reject functions afterwards. When the lookup threw (like how our program does), the resolving functions didn't exist yet, so there was nothing to reject with. The exception escaped the job entirely (that's the red `Error: boom` in the inspector) and our promise stayed pending forever.

Here's that as a railway:

Our train had effectively derailed! We didn't even get the chance to finish our journey on either track and so the original program hung because the train never even arrived at the station!

Luckily, the fix is simple, and might already be obvious to you! We must create our resolve/reject functions before calling `.then()`, so that we actually have the ability to reject the promise if calling `.then()` throws. Creating the resolving functions is just an allocation and allocations can't throw, and once the functions exist, the existing error handling rejects the promise just like any other failure would.

With the two steps in the right order, Bun 1.4 and Safari 27 now behave like the spec, and like Node:

Bug fixed! But it left me with a question. Earlier I drew promises as railways, with a fulfilled track and a rejected track. However, we just watched the engine put an error on the rejected track that no line of our code ever passed to `reject()`. So does that mean we can't actually ever know what's on that track?

## So is a promise a railway?

In TypeScript, the `Promise<T>` interface has only one type parameter and offers no way for a developer to express ways in which the promise might reject:

```
declare const p: Promise<number>;
```

TypeScript users have asked for a `Promise<T, E>` to exist since 2015 - see this issue:  [microsoft/TypeScript#6283](https://github.com/microsoft/TypeScript/issues/6283)! Ron Buckton, who used to work on TypeScript at Microsoft, closed this issue, stating:

> we cannot guarantee the correct type of the exception at design time.

Which we have now learnt is true! Earlier, we saw the runtime reject a promise with  `boom`: `p.then()` read a `Symbol.species` getter that threw the error, and Step C of the job rejected the promise with it, very far away from any userland `reject()` call! If the spec itself can put values on the reject track, then even code that only ever calls `reject()` with one type cannot be given an `E`. The failure track has to be `any` (okay, yes, it could technically be `unknown`, but adoption and backwards compatibility are also important things for a project of TypeScript's scope and size to care about!).

Here's that represented as a railway:

Look - we have no control over that failure track! This means we *can* draw promises as railways but it's a bit less useful than a real result type, like Rust's.

## What did we learn?

Let's summarise!

- resolve(value) does not immediately fulfil a promise. It reads value.then first, and if that is a function the promise follows value instead.
- "Resolved" is not a state because a resolved promise can still be pending.
- Reading value.then, and reading constructor[Symbol.species] inside Promise.prototype.then, are ordinary property reads. Getters can throw, and the spec puts whatever they throw on the rejected track.
- JavaScriptCore did the species read before creating the resolving functions, so when it threw there was nothing to reject with. The fix (WebKit/WebKit#68749) was to create the functions first and call them when the getter throws.
- A promise has the shape of a railway, but its failure track can't be labelled, because the engine shares it with you. That is why TypeScript's Promise<T> has no E.

If you read all the way to the end, then I am glad you are as excited about promises as I am. Thank you very much for reading!
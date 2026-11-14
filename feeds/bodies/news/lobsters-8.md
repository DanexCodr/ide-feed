I think everyone can agree code needs to be modular.
Modularity lets us reason locally about our code no matter how big it grows.
However, no one seems to agree on *how* code should be modular.
There are a bunch of different approaches and each new language seems to bring their own spin on it.

Today we’re going to talk about a pretty old spin: ML Modules.
ML here stands for Meta Language, as seen in SML and OCaml (and not machine learning).
Despite SML first appearing in 1983, ML Modules have not caught on.
OCaml is the sole production language you’ll find with an ML module system, and at the height of its popularity it’s niche.

This is a shame because ML modules have a lot to offer.
We’re going to talk about what ML modules are and then touch a little on why ML modules are.
Who better after all to explain modules, than the guy who doesn’t know [what’s in a module
**](https://thunderseethe.dev/posts/whats-in-a-module/)?  
…On second thought, don’t answer that.  
…I already wrote the blog post.

Modules exist to make our code modular, duh, but what does that mean in practice?
I think most programmers have some intuitive sense of modularity:

- Bundle up related logic as one “thing”
- Encapsulate invariants
- Decouple from dependencies

Most languages have a way to do this, and if they don’t, one gets created for them (looking at you JavaScript).

## Modules Bundle Functions
[**
Link to heading](https://thunderseethe.dev/posts/ml-modules-for-mere-mortals/intro/#modules-bundle-functions)

ML modules achieves this with, you guessed it, the Module.
ML modules, however, are a little different from the modules we know and love.
To explain their differences, we’ll lean on a made-up Rust-inspired syntax.
It will start off looking a little weird and gradually, as we introduce concepts, end up looking really weird (but hopefully more familiar than SML syntax).
We’ll start by defining a module with just functions:

```rust
mod AModule {
  fn add(a: i32, b: i32) -> i32 {
    a + b
  }

  fn sub(a: i32, b: i32) -> i32 {
    a - b
  }

  // mult, div, etc...
}
```

`AModule` bundles together related arithmetic functions as one thing we can reason about.
Each function can see every other function in the module.
This is useful, but any language with namespaces offers this.

## Modules (also) Bundle Types
[**
Link to heading](https://thunderseethe.dev/posts/ml-modules-for-mere-mortals/intro/#modules-also-bundle-types)

A little more unique is that ML modules will let us put not only function definitions in modules, but also type definitions:

```rust
mod Set {
  type Set = Vec<i32>;

  fn new() -> Set {
    vec![]
  }

  fn index_of(this: &Set, ele: &i32) -> Result<usize, usize> {
    this.binary_search(ele)
  }

  fn insert(this: Set, ele: i32) -> Set {
    match index_of(&ele) {
      Ok(_) => {} // we're done the element is already present
      Err(indx) => {
        this.insert(indx, ele);
      }
    }
    this
  }

  fn contains(this: &Set, ele: &i32) -> bool {
    index_of(this, ele).is_ok()
  }

  fn remove(this: Set, ele: &i32) -> Set {
    match index_of(this, ele) {
      Err(_) => {}, // we're done the element is already removed
      Ok(indx) => {
        this.remove(indx)
      }
    }
    this
  }
}
```

Here we have a `Set` module with a `Set` type, which is a sorted `Vec<i32>`.
Our module’s functions can refer to the type definitions much the same way they can refer to their module’s function definitions.
Okay but that’s not that crazy, still well within the realm of Rust modules.

## The Type of a Module is a Signature
[**
Link to heading](https://thunderseethe.dev/posts/ml-modules-for-mere-mortals/intro/#the-type-of-a-module-is-a-signature)

Not only can modules contain type definitions.
Modules themselves have types.
A module type is called a signature (so we don’t get it confused with “normal” types).
The signature of our `Set` module is:

```rust
sig FullSetSig {
  type Set = Vec<i32>;

  fn new() -> Set;
  fn index_of(&Set, &i32) -> Result<usize, usize>;
  fn insert(Set, i32) -> Set;
  fn contains(&Set, &i32) -> bool;
  fn remove(&Set, &i32) -> Set
}
```

A module signature declares every definition of a module alongside its type.
This might look similar to the way we define a trait in Rust.
That’s because much like traits act as interfaces in Rust, signatures act as interfaces in ML Modules.
Modules having signatures is the single most important thing to understand about ML Modules.
All the complexity and expressiveness of modules results from them having signatures and the wonderful wacky things that enables.

# Signatures Support Encapsulation
[**
Link to heading](https://thunderseethe.dev/posts/ml-modules-for-mere-mortals/intro/#signatures-support-encapsulation)

Signatures resemble the way a C/C++ implementation file conforms to its header.
Modules, unlike `.cc` files, aren’t in a 1:1 relationship with signatures.
Our `Set` module can conform to *any* signature that it matches.
A module matches a signature when it defines every declaration in the signature and they agree on type.

Matching a signature provides [Encapsulation
**](https://en.wikipedia.org/wiki/Encapsulation_%28computer_programming%29), hiding internal details of our module from our public API.
Take a look at `FullSetSig`.
Do callers of `Set` really need to know about `index_of`?
Encapsulation advocates shout a resounding no: `index_of` is an implementation detail of `Set.Set` being a `Vec<i32>` and not integral to our `Set` API.

We can encapsulate `index_of` by matching our `Set` module to a new signature:

```rust
sig SetSig {
  type Set = Vec<i32>;

  fn new() -> Set;
  // index_of is missing.
  fn insert(Set, i32) -> Set;
  fn contains(&Set, &i32) -> bool;
  fn remove(&Set, &i32) -> Set
}
```

`SetSig` removes `index_of`, hiding the implementation detail.
We can then ascribe our signature to our `Set` module:

```rust
mod Set : SetSig {
    // Our module implementation stays unchanged...
}
```

Now the rest of our code sees `Set` as `SetSig` without `index_of`.
Importantly, our `Set` module hasn’t changed.
`index_of` is still available inside the module.
Ascribing the signature only changes the public view of the module, similar to a private function in Rust.

A module’s definition isn’t the only place we can ascribe a signature.
We can also make a “new” module by matching an old module to a new signature.
Let’s say we want an `InsertOnlySet` (never you mind why I need that):

```rust
sig InsertOnlySetSig {
  type Set = Vec<i32>;

  fn new() -> Set;
  fn insert(Set, i32) -> Set;
}
```

We can create that from our `Set` module purely by matching the signature:

```rust
mod InsertOnlySet: InsertOnlySetSig = Set;
```

Now `InsertOnlySet` is effectively a whole new module, despite the underlying implementation being shared with `Set`.
This is what’s cool about modules.
We can repurpose modules “for free” simply by giving them a different signature.
If we want to do this in an OO language, we’d have to add a new interface in our class definitiion.
But we can slap one of these bad boys anywhere in our codebase.

## Sealed Types Seal Encapsulation
[**
Link to heading](https://thunderseethe.dev/posts/ml-modules-for-mere-mortals/intro/#sealed-types-seal-encapsulation)

Ascribing a signature to a module lets us hide implementation details, but there’s a bit of a glaring hole here.
Sure we’ve hidden away `index_of`, but our module broadcasts to the world that `type Set` is a `Vec<i32>`!
Set relies on our vector being kept in sorted order, but anybody is free to write a function:

```rust
fn whoops() {
    let mut set = Set::new();
    // teehee
    set.extend([3, 2, 1]);
    // 💥
    let uh_oh = Set::insert(set, 1);
    // Now our set is [1, 3, 2, 1]
}
```

Nothing but a small flesh wound in our encapsulation.
Fortunately, ML modules foresaw this problem and provided a solution using signatures.

Much the same way a signature lets us hide functions, it also lets us hide types.
ML Modules call this an abstract type.
If we update `SetSig` to be:

```rust
sig SetSig {
  type Set;

  fn new() -> Set;
  fn insert(Set, i32) -> Set;
  fn contains(&Set, &i32) -> bool;
  fn remove(&Set, &i32) -> Set
}
```

Our signature no longer broadcasts that `type Set` is `Vec<i32>`.
Within the `Set` module we’re free to use `type Set` as `Vec<i32>`, but everywhere outside the module `type Set` is now some unknown type.
Because callers know nothing about our newly abstract `Set` type, all they can do is pass it to and from the methods provided by the `Set` module.
As long as we keep our underlying `Vec<i32>` sorted within `Set`, we know no one else is able to mess with it.
They simply don’t know enough about the type!

## Module’s Version of Generics
[**
Link to heading](https://thunderseethe.dev/posts/ml-modules-for-mere-mortals/intro/#modules-version-of-generics)

Our Set module is nearing perfection, but it still leaves a little to be desired: it only works for `i32`.
Now we could of course write a new module `SetU64`, `SetString`, on and on everytime we need one, but c’mon there’s gotta be a better way.
This isn’t Go.

Generics is the go-to solution for this problem.
Heck we’ve even used it ourselves with `Vec<i32>`.
ML Modules, however, have a more *modular* solution.
You can parameterize a module by another a module.

Think of a parameterized module as a function that takes a module and returns another module.
To make our `Set` accept any type and not just `i32`, we parameterize it by a module that provides the type of our Set’s elements:

```rust
mod Set: SetSig (sig Elem {
  type T
}) {
  type Set = Vec<Elem.T>;

  fn new() -> Set {
    vec![]
  }

  fn index_of(this: &Set, ele: &Elem.T) -> Result<usize, usize> {
    // ...
  }

  fn insert(this: Set, ele: &Elem.T) -> Set {
    // ...
  }

  fn contains(this: &Set, ele: &Elem.T) -> bool {
    index_of(this, ele).is_ok()
  }

  fn remove(this: Set, ele: &Elem.T) -> Set {
    // ...
  }
}
```

Our newly parameterized `Set` accepts any module that conforms to `Elem`.
Any module can match `Elem` as long as it has at least a `T` definition.

## A Teensy Problem
[**
Link to heading](https://thunderseethe.dev/posts/ml-modules-for-mere-mortals/intro/#a-teensy-problem)

With that our `Set` module supports any type.
Except for one teensy detail.
I’ve deceived you with some tactical `// ...`s.
If we actually try to implement `index_of`, we quickly encounter a problem:

```rust
fn index_of(this: &Set, ele: &Elem.T) -> Result<usize, usize> {
  this.binary_search_by(|a| ele ??? a)
}
```

We don’t know how to compare `T`’s.
Rust’s `Ord` would solve this, of course, but ML modules have modules not traits.
`Set` doesn’t take in just a type, however, it takes in a full module.
If we need to know how to compare `T`’s, we can just ask our `Elem` module:

```rust
mod Set: SetSig (sig Elem {
  type T;
  fn cmp(&T, &T) -> Ordering;
}) {
  // ...
}
```

Now it’s clear how to implement `index_of`:

```rust
fn index_of(this: &Set, ele: &Elem.T) -> Result<usize, usize> {
  this.binary_search_by(|a| Elem::cmp(ele, a))
}
```

With our parameterized module implemented, we can create new `Set` modules by applying them to new argument modules:

```rust
mod SetU32 = Set(mod U32 {
  type T = u32;
  fn cmp(a: &T, b: &T) { a < b }
});
```

`SetU32.Set` is a `Vec<u32>` and provides an interface that takes and returns `u32` instead of `i32`.
We can do it again as easy as:

```rust
mod SetString = Set(mod String {
  type T = String;
  fn cmp(a: &T, b: &T) { /* lexographic ordering probably... */ }
});
```

Just like that, a whole new module.
This time a set of Strings.
I could do this all day.

Because we accept a module, we can request anything a module can hold (even a whole other submodule or parameterized module!).
The downside is that we have to specify the whole module every time.
We *have* to specify `cmp` every time we apply our `Set` module.
Rust traits let us write `Ord` for a type once and use it everywhere implicitly.

## Include Keeps Modules Small
[**
Link to heading](https://thunderseethe.dev/posts/ml-modules-for-mere-mortals/intro/#include-keeps-modules-small)

In practice, we don’t actually repeat how to order our type every time we want a `Set`.
Recall that a signature will match *any* module that provides what it needs.
If we make a big module called `U64`:

```rust
mod U64 {
  type T = u64;

  fn cmp(a: &u64, b: &u64) { a < b }

  fn add(a: u64, b: u64) -> u64 { a + b }
  fn sub(a: u64, b: u64) -> u64 { a - b }
  // ...
}
```

Then we can use that as our argument to Set:

```rust
mod SetU64 = Set(U64);
```

But hang on, we got into this whole Module business to break up our code.
Now we’ve got to dump everything into one module just in case we need it later?
That’s not very cash modular of us.

ML modules have a final feature to get us the best of both worlds: `include`.
`include` expands a module inline within another module.
We’re free to split up our `U64` module into various submodules: `U64Order`, `U64Arithmetic`, etc.
Our final `U64` module only has to include these submodules:

```rust
mod U64 {
  type T = u64;

  include U64Order;
  include U64Arithmetic;
  // ...
}
```

Modules can be organized into logical components and then combined later to provide convenience (wow!).
We’re free to cut up and reassemble modules at the whims’ of the wind.
We can even apply a module and include it inline:

```rust
mod ABunchOfSetForSomeReason {
  mod SetU64 = Set(U64);
  include SetU64;

  mod SetString = Set(String);
  include SetString;
}
```

Why do you need one module that’s a bunch of overlapping Sets?
I don’t know!
I’m not your supervisor.
Either way, modules will happily let you do it.

## Putting It All Together
[**
Link to heading](https://thunderseethe.dev/posts/ml-modules-for-mere-mortals/intro/#putting-it-all-together)

We’ve covered the basics of modules.
Let’s take a look at a more involved examples to get a sense of what modules can offer.
We’re gonna use modules to assemble a little build executor.
Out build step will be a parameterized module:

```rust
mod BuildStep(sig Env {
  mod Cache: CacheSig;
  mod Runner: RunnerSig;
}) {
  // ...
}
```

Where `CacheSig` represents a cache of build steps and `RunnerSig` represents running some command:

```rust
sig CacheSig {
  fn is_cached(inputs: &[String], output: &Path) -> bool;
  fn store(inputes: &[String], output: &Path);
}

sig RunnerSig {
  fn run(inputs: &[String], output: &Path);
}
```

For brevity we’ll keep these pretty simple, but hopefully you can imagine how these might expand.
We can then implement `BuildSet` in terms of our input modules:

```rust
mod BuildSet(...) {
  fn run_cached(inputs: &[String], output: &Path) {
    if !Env::Cache::is_cached(inputs, output) {
      Env::Runner::run(inputs, output);
      Env::Cache::store(inputs, output);
    }
  }

  fn compile(src: String) -> String {
    let obj = PathBuf::from(format!("{src}.o"));
    run_cached(&[src], &obj);
    obj.display().to_string()
  }

  fn build(srcs: &[String], output: &Path) {
    let objs: Vec<String> = srcs.iter().map(compile).collect();
    run_cached(objs, output)
  }
}
```

Our `build` functions takes a list of source files, compiles them, and then links the object files into a final binary.
How does `run` tell when it’s compiling and when it’s linking?
Don’t worry about it!
Now that we’ve set that up we can toggle the functionality of our build by controlling what modules we pass to `BuildStep`.
For a real build, we’ll want something like an in-memory cache:

```rust
mod MemCache {
  // Pretend this works without locking for multithreading
  static ENTRIES: Vec<(Vec<String>, PathBuf)> = vec![];

  fn is_cached(inputs: &[String], output: &Path) {
    ENTRIES.iter().any(|(cached_inputs, cached_outputs)| {
      inputs == cached_inputs && output == cached_outputs
    })
  }

  fn store(inputs: &[String], output: &Path) {
    ENTRIES.push((inputs.to_vec(), PathBuf::from(output)))
  }
}
```

Next we’ll want something that runs our commands:

```rust
mod ShellRunner {
  fn run(inputs: &[String], output: &Path) {
    let cmd = // magically pick between `cc` and `lld`;
    let output = format!("-o {}", output.display());
    Command::new(cmd)
      .args(inputs)
      .args(output)
      .output()
      .expect("All our commands work first try");
  }
}
```

We can then assemble our build system via:

```rust
mod CachedBuild = BuildStep(mod Env {
  mod Cache = MemCache;
  mod Runner = ShellRunner;
});
```

But maybe we don’t always want caching.
Maybe we want a build that always reruns actions for local testing.
We simply swap out our cache module:

```rust
mod NoCache {
  fn is_cached(inputs: &[String], outputs: &Path) -> bool {
    false
  }

  fn store(inputs: &[String], outputs: &Path) {
    // nothing to do here
  }
}

mod LocalBuild = BuildStep(mod Env {
  mod Cache = NoCache;
  mod Runner = ShellRunner;
});
```

Our build system works first try.
We wouldn’t write the code bad, of course, but just in case we might want to test it.
A `FakeRunner` will let us do just that:

```rust
mod FakeRunner() {
  static COMMANDS: Vec<(Vec<String>, PathBuf)> = vec![];

  fn run(inputs: &[String], output: &Path) {
    COMMANDS.push((inputs.to_vec(), PathBuf::from(output)));
  }

  // A test only helper.
  fn contains_command(inputs: &[String], output: &Path) -> bool {
    // ...
  }
}
```

Because `FakeRunner` is a parameterize module, we can create a new module (and a new empty `COMMANDS`) every time we apply it:

```rust
mod Tests {
  mod TestRunner = FakeRunner();
  mod TestBuild = BuildStep(mod Env {
    mod Cache = MemCache;
    mod Runner = TestRunner
  });

  // Write tests against TestBuild using `TestRunner::contains_command`...
}
```

If we want to check that caching works we can extend our tests with a new fake runner and compare their commands:

```rust
mod Tests {
  // TestBuild setup...

  mod UncachedTestRunner = FakeRunner();
  mod UncachedTestBuild = BuildStep(mod Env {
    mod Cache = NoCache;
    mod Runner = UncachedTestRunner;
  })

  // Compare the results of `TestRunner::contains_command` and `UncachedTestRunner::contains_command`...
}
```

This isn’t earth shattering stuff.
If we wanted to replicate this setup in an OO language, however, we would need runtime objects or, heaven forbid, a DI framework.
Here we can do it all by wiring up modules statically.

Hopefully this has helped you see what’s cool about modules.
Module’s power lies in their signatures.
What would require a newtype wrapper or a visibility change in other languages can be accomplished by simply changing the signature a module is viewed at.

With abstract types, this allows for constructing webs of encapsulation where each piece knows precisely what it needs to about its neighbor and no more.
Signatures act as this encapsulation boundary, freeing us to reason about our code modularly.
As long as our module conforms to the expected signature we can contort and refactor it to our wildest whims and trust that it will continue to integrate into our system as expected.
ML Modules are neat and I think they deserve more love and exploration in programming languages.
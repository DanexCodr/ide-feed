I recently discovered a handy way to make Go tests more readable and less repetitive.

Suppose I have a constructor that can fail:

```go
func NewUsername(raw string) (Username, error) { ... }
```

And I have another function that takes a `Username` as an argument:

```go
func (ds Datastore) ReadUser(username Username) (User, error) { ... }
```

When I write tests for `ReadUser`, I call `NewUsername` with a value I know is valid, but I still have to include a lot of verbose error-checking code to convince the compiler that everything is okay:

```go
username, err := NewUsername("joe123")

// This is silly because *I* know joe123 is a valid username, so this should
// never happen.
if err != nil {
  t.Fatalf("failed to create username: %v", err)
}

// Perform the test assertion I actually care about.
user, err := store.ReadUser(username)
if got, want := user.Name.String(), "joe123"; got != want {
  t.Errorf("username=%v, want=%v", got, want)
}
```

## My old solution: one new helper function per type[🔗︎](https://mtlynch.io/notes/go-must-create-pattern/#my-old-solution-one-new-helper-function-per-type)

Until a few months ago, I avoided the verbose error checking by writing a helper function like `MustCreateUsername` that wraps `NewUsername` with the expectation that it never returns a non-`nil` `error` value:

```go
user, err := store.ReadUser(MustCreateUsername(t, "joe123"))
if got, want := user.Name.String(), "joe123"; got != want {
  t.Errorf("username=%v, want=%v", got, want)
}
```

The implementation of `MustCreateUsername` looks how you’d expect:

```go
func MustCreateUsername(t testing.TB, raw string) Username {
  t.Helper()
  username, err := NewUsername(raw)
  if err != nil {
    t.Fatalf("invalid username: %s", raw)
  }
}
```

The helper function strategy worked fine, but it scales poorly. Eventually, my repos become littered with `MustCreateFoo` and `MustCreateBar` for every type in my app.

## New solution: A single, generic `MustCreate` helper[🔗︎](https://mtlynch.io/notes/go-must-create-pattern/#new-solution-a-single-generic-mustcreate-helper)

In 2022, Go 1.18 [added support for generics](https://go.dev/doc/go1.18#generics). I like the idea of generics, but I rarely encounter problems where generics are the solution.

I recently realized that generics are the better way to solve my sprawling `MustCreateX` problem. Instead of defining a helper `MustCreateX` for every type, I defined a single, generic `MustCreate` test helper, so my test becomes:

```go
user, err := store.ReadUser(testutil.MustCreate(t, NewUsername, "joe123"))
if got, want := user.Name.String(), "joe123"; got != want {
  t.Errorf("username=%v, want=%v", got, want)
}
```

The magic is the generic `MustCreate` function:

```go
func MustCreate[RawInput, CreatedValue any](
  t testing.TB,
  create func(RawInput) (CreatedValue, error),
  rawInput RawInput,
) CreatedValue {
  t.Helper()
  createdValue, err := create(rawInput)
  if err != nil {
    t.Fatalf("failed to create test value: %v", err)
  }
  return createdValue
}
```

I have trouble reasoning about generics, so I’ll walk through the function implementation. I invoke `MustCreate` like this in my tests:

```go
testutil.MustCreate(t, NewUsername, "joe123")
```

The above call is equivalent to this more explicit version:

```go
testutil.MustCreate[string, Username](t, NewUsername, "joe123")
```

When I call `MustCreate` here, `RawInput` is `string` (the type of the raw username value), and `CreatedValue` is `Username` (the return type). It’s equivalent to an implementation that looks like this:

```go
func MustCreate(
  t testing.TB,
  create func(string) (Username, error),
  rawInput string,
) CreatedValue {
  t.Helper()
  createdValue, err := create(rawInput)
  if err != nil {
    t.Fatalf("failed to create test value: %v", err)
  }
  return createdValue
}
```

### Extending to multi-param constructors[🔗︎](https://mtlynch.io/notes/go-must-create-pattern/#extending-to-multi-param-constructors)

What about constructors that have more than one parameter?

```go
func NewRange(start int, end int) (Range, error) { ... }
```

In those cases, I write an additional helper called `MustCreate2`:

```go
range := testutil.MustCreate2(t, models.NewRange, 0, 5)
```

The implementation of `MustCreate2` looks just like `MustCreate` but with an additional type for the second parameter:

```go
func MustCreate2[RawInput1, RawInput2, CreatedValue any](
  t testing.TB,
  create func(RawInput1, RawInput2) (CreatedValue, error),
  rawInput1 RawInput1,
  rawInput2 RawInput2,
) CreatedValue {
  t.Helper()
  createdValue, err := create(rawInput1, rawInput2)
  if err != nil {
    t.Fatalf("failed to create test value: %v", err)
  }
  return createdValue
}
```

## Conclusion[🔗︎](https://mtlynch.io/notes/go-must-create-pattern/#conclusion)

The `MustCreate` pattern is nothing revolutionary, but it’s a technique that improved my Go tests and reduced some mindless toil from my dev work.

## Read My Book

I wrote a book about simple techniques to help developers improve their
writing.

My book will teach you how to:

- Create clear and pleasant software tutorials
- Attract readers and customers through blogging
- Write effective emails
- Minimize pain in writing design documents

### Be the first to know when I post cool stuff

Subscribe to get my latest posts by email.
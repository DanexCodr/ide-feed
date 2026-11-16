Six months ago, I wrote an [SQLite-backed cache](https://alexwlchan.net/2026/sqlite-cache/) to speed up the build system for this site. A static site generator is an ideal candidate for [caching](https://en.wikipedia.org/wiki/Caching), because there are lots of steps that have deterministic behaviour and no side effects. On a site with hundreds of pages, even a few milliseconds per step adds up to a meaningful improvement.

That first cache was fairly basic. It supported getting and setting strings, with a namespace for different functions, and not much else:

```
from mosaic.cache import SQLiteCache

cache = SQLiteCache("example.db")

cache.set(namespace="fibonacci", key="10", value="55")
print(cache.get(namespace="fibonacci", key="10"))
```

This showed the value of a cache, but it provided cache *storage*, not cache *logic*. If I wanted to cache a function, I had to write per-function logic for saving values to the cache and retrieving them later. A lot of that code was tricky to test, and broken in subtle ways. I was so unsure of this code that I deleted the cache whenever I built the site for publication.

I wanted something better, so last week I wrote [funkycache](https://alexwlchan.net/projects/funkycache/), a new library that encapsulates all of my caching logic, and is much easier to use and test. It can store arbitrary Python objects as both inputs and outputs, and the interface is much simpler for the caller.

To cache a function, you create a `FunkyCache` instance and add a decorator to your function:

```
from funkycache import FunkyCache

cache = FunkyCache(storage="sqlite")

@cache.register
def expensive_function(arg1: str, arg2: int, arg3: date) -> tuple[str, date]:
    ...
```

This is modelled after [`functools.cache`](https://docs.python.org/3/library/functools.html#functools.cache) in the standard library. The output of the expensive function is written to an SQLite database, so it’s available after the Python process exits.

The cache tries to be smart about invalidations. If the source file containing `expensive_function` changes, the cache for that function is invalidated and will be rebuilt on the next call.

You can also specify a dependency on other files and static values, changes to which will also trigger a cache invalidation:

```
from funkycache import FunkyCache

cache = FunkyCache(storage="sqlite")

@cache.register(
    files=["data/input.yml", "templates/example.html"],
    values=[pygments.__version__],
)
def expensive_function(arg1: str, arg2: int, arg3: datetime) -> tuple[str, datetime]:
    ...
```

When writing funkycache, I wanted to spend a week thinking hard about caching logic, test it thoroughly, then not think about it again for months. You should be able to use funkycache without understanding how it works – but if you’d like to, that’s what I’ll explain in the rest of this post.

If you’d like to try it yourself, funkycache is [on PyPI](https://pypi.org/project/funkycache/), and the source code is [on this website](https://alexwlchan.net/projects/funkycache/).

## Cache keys are function arguments, hashed and JSON-encoded

### Getting a complete set of arguments for a function

The cache is meant for functions which always produce the same output for a given input, so the inputs are the cache key. When we [decorate a function](https://docs.python.org/3/library/functools.html#functools.wraps), we can see the arguments passed on each call:

```
from functools import wraps

def my_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print({"args": args, "kwargs": kwargs})
        return func(*args, **kwargs)
    return wrapper
```

This doesn’t account for different styles of calling the same function – for example, positional versus keyword arguments, or omitting or overriding default arguments.

To get a complete, consistent set of arguments, I use the `inspect` module:

```
import inspect

sig = inspect.signature(func)
bound = sig.bind(*args, **kwargs)
bound.apply_defaults()
cache_key = bound.arguments  # {"arg1": val1, "arg2": val2, ...}
```

This gives me a Python dictionary of the complete set of arguments to the function, which is the same regardless of the calling style.

### Converting the arguments to JSON

Python dictionaries aren’t hashable, so they can’t be used as the keys in dictionaries, nor can they be used as keys in SQLite databases. We need to serialise them as a string or byte sequence.

I considered two options for this serialisation: [pickle](https://docs.python.org/3/library/pickle.html) and [JSON](https://docs.python.org/32/library/json.html). In my limited testing, JSON was faster than pickle, so that’s what I chose. Using JSON also gave me more flexibility for speeding up the serialisation.

My initial serialisation was a naive `json.dumps` call, with a couple of options to ensure consistent ordering and handle types that the standard library doesn’t know how to encode:

```
json_key = json.dumps(cache_key, sort_keys=True, default=str)
```

When I started using funkycache, this encoding step quickly emerged as the slowest part, so I started “reducing” the arguments to make this step faster. This reduction included:

- Recursively walking the function arguments and hashing large strings
- Using Pydantic to convert Pydantic models and dataclasses into Python objects, rather than doing a string conversion
- Refactoring my code so each function only takes a minimal set of required data

These are all lossy transformations, but that’s fine for a cache *key* – we never need to retrieve the original value. It’s theoretically possible for different values to get a colliding hash key, but at my scale it’s unlikely. (A clean build of my site only uses 32,000 keys.)

### Hashing for smaller keys

The functions in my static site generator are processing things like the content of articles, so individual function arguments might be kilobytes in size. You can use multi-kilobytes keys with SQLite, but you probably shouldn’t – you take a performance hit for larger keys.

I wrote [a small benchmark](https://alexwlchan.net/projects/funkycache/files/tests/bench_sqlite_storage.py) to compare three approaches: storing the JSON-encoded arguments directly, hashing them with MD5, and hashing them with [XXH64](https://xxhash.com/). The results are a wash for small key sizes, but for larger keys XXH64 is significantly faster, and MD5 is slower than storing the keys directly in SQLite:

Based on this benchmark, funkycache hashes the JSON cache key with XXH64 before inserting it into SQLite.

The xxHash class of hashing algorithms was a pleasant discovery for me during this project. They are explicitly designed to be fast, not cryptographically secure. Previously I’d used MD5 for this purpose, because it’s widely available and I conflated “weak” with “fast”. Actually running a benchmark revealed my mistake.

## Cache values are JSON-encoded

Serialising cache keys can be a one-way operation, but cached values need to be retrievable. For this, I’m using the `inspect` module to get the return type from the cached function, then handing the serialisation to Pydantic.

```
import inspect
import pydantic

# Get the return type of the function.
sig = inspect.signature(func)
return_type = sig.ret_annotation

# Create a Pydantic type adapter
adapter = TypeAdapter(return_type)

# Serialise as JSON
json_str = adapter.dumper_json(value)

# Deserialise from JSON
retrieved_value = adapter.validate_json(stored_value)
```

I use type hints and type annotations for all of my Python, so this information is guaranteed to be present. This wouldn’t work with untyped Python, but it’s good enough for me.

The alternative is using pickle, which can store arbitrary Python objects. I wouldn’t have to worry about the [security risks](https://docs.python.org/3/library/pickle.html#:~:text=The%20pickle%20module%20is%20not%20secure) because I’d only ever be pickling and unpickling trusted data, but I continued with JSON because I’m already using it for cache keys, and it’s easier to debug.

### Caching lazy generators

One of the functions I wanted to cache is a lazy generator, which was a little trickier.

Using `functools.cache` will cache the generator *object*, so every call gets the same generator instance, and they all step together. This strikes me as potentially confusing:

```
import functools

@functools.cache
def even_numbers():
    for i in range(10):
        yield i * 2

n1 = even_numbers()
n2 = even_numbers()
print(next(n1))  # 0
print(next(n1))  # 2
print(next(n2))  # 4
```

funkycache takes a different approach: it materialises the generator into a list, and stores that list. When it’s retrieved, the list is converted back into a generator by wrapping it with [`iter`](https://docs.python.org/3/builtins/functions.html#iter).

To protect against unbounded memory use from a large or infinite generator, there’s a soft memory budget. If the materialised list exceeds this budget, I stop gathering the output in the list and don’t save anything to the cache. The list and any subsequently generated items are passed directly from the original function to the caller.

## Tracking dependencies

### Tracking dependent files

Some of the functions in my static site generator depend on the contents of template files. When those files change, I want to invalidate the cache and rebuild the pages that use those templates.

When you register a function with funkycache, you can specify a list of files or folders that it depends on:

```
@cache.register(files=["mosaic/text", "templates"])
def render_html(content: str, content_vars: dict[str, Any],) -> str:
    ...
```

funkycache will read the contents of each of those files, and include them in the cache key. When a file changes, it re-evaluates the list of files and decides whether to keep or invalidate the cache.

I decided not to put any file change tracking in funkycache itself. I already [have code for that](https://alexwlchan.net/2026/watch-files-on-macos/), and I wanted to keep this project small and focused.

### Tracking dependent values

A function’s cache can also be based on static values. I use this to include the version of important libraries, so the cache gets invalidated when I update the library. Here’s a short example:

```
import pygments

@cache.register(values=[pygments.__version__])
def apply_syntax_highlighting(src: str, lang: str) -> str:
    ...
```

## Reactive aspirations

This project started because I was thinking about [reactive programming](https://en.wikipedia.org/wiki/Reactive_programming).

Reactive programming is a bit like using a spreadsheet. You have input cells where you enter data, and other cells that read that data and automatically update when the inputs change. Those cells can be inputs to other cells, and so on.

Imagine building a static site: your Markdown files act as input cells, and your rendered HTML pages are the dependent cells. Your tasks form a [directed acyclic graph (DAG)](https://en.wikipedia.org/wiki/Directed_acyclic_graph), and updates propagate through the graph.

For example, in the diagram above, when `article1.md` changes, the system knows it needs to rebuild `article1.html` and ripples that update to `list_of_articles.html`. But because there’s been no change in their inputs, the tasks to render articles 2 and 3 don’t run at all.

When done correctly, this can be a very efficient style of programming, because steps only ever run if there’s been a change in their inputs.

There are tools that will do this for you, like [Apache Airflow](https://airflow.apache.org/), but I wanted to build my own. My website is a sandbox where I like building things myself as a learning exercise, rather than using somebody else’s library.

I spent several weeks trying to design an API, but I couldn’t come up with something satisfactory. However, I experimented with a decorator-based API, and that led me to build funkycache, which delivers a lot of the benefits with less fo the complexity.

Building my website with a warm cache now takes about half a second, and a significant chunk of that time is spent traversing the file system for Markdown files. I have ideas for speeding up that step as well, but that’s a task for another day.

funkycache is only [a few hundred lines of code](https://alexwlchan.net/projects/funkycache/), including tests. If this problem sounds interesting, I encourage you to read it, even if it’s not a library you expect to use.
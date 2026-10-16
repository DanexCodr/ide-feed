I have always been frustrated about C not having a proper `String` type that most modern
languages have nowadays. I love the simplicity of C, but there are some features that I
would really like to have in it, and this is one of them.

Since I made a small library (just one `.c` file) that you can use to make the experience
of working with strings in C just a little better, I would like to show it to you here.

For the impatient, this is the general idea:

```
struct str_view {
    const u8       *data;
    usize           len;
};

struct str_owned {
    u8             *data;
    usize           len;
};
```

But before getting into the library itself, I will go over how “strings” work in C and why
I find them annoying, what the issues are with this model, and then it will be easier
to explain why I decided to take the route that I took.

If you only care about the actual implementation details,
you can [click here](https://eliasebner.com/blog/guides/fixing-strings-in-c/#the-solution).

## How Strings Work in C

As many might already know, strings in C are NUL-terminated. NUL is an ASCII character
which, in the context of ASCII encoding, literally corresponds to the value 0.
In C, this character is represented by `'\0'`. Inside a text, it generally does not
carry any semantic meaning, so it will never be used inside the text for the sake
of carrying information (as opposed to letters like `'a'` or `'y'`).

C does not really have “strings” per se. It only has arrays. These arrays are simply
chunks of data where you can put things. To understand where the array ends,
one has two options:

- Store the length of the data somewhere
- Put something at the end of the array to signify its end

C went with the second option.

Since “strings” (which are not really strings) in C are simply arrays of characters,
each string has a NUL-terminator at the end of it.

C is a very old language and back then - when it was first created - this seemed like a good
idea.

Storing the length of the data separately required more memory than a
NUL-character at the end. A NUL-character in ASCII encoding is 8 bits (or 1 byte).
If you tried to store the length of the data in only 8 bits, you could only have
strings that are up to 255 characters in length, which is obviously too short.
Bigger numbers require more data to store, so we’re talking about around 4 to 8 bytes instead
of 1.

But this is not even the main reason - the main reason is because of simplicity.
Back when C was created, there existed some languages that already had strings with a
separately stored length. C just wanted to be as simple as possible, and having NUL-terminated
character arrays seemed like a sane decision.

## The Problems With This Approach

There are multiple issues with this.

### First Issue

First of all, if you want to find out the length of a string, with a NUL-terminated string
you have to start at index `0` and start counting until you reach the end of the data.
This process has a time complexity of O(n)O(n)O(n), as opposed to O(1)O(1)O(1) for just reading the
separately stored length.

This is fine for short character arrays, but imagine you had to figure out the length of a
1,000,0001,000,0001,000,000 character text. That would take a considerable amount of CPU cycles  that
could have been used for something else.

This bothers me especially in a language like C, since it is supposed to give you
some of the best performance that programming languages have to offer (without
counting assembly and certain exceptions in some specific scenarios).
C is often the baseline when comparing languages to gauge their relative performance.
Why, if C focuses so much on performance, would you settle for this?

### Second Issue

Let us assume that we have some C-string `some_str`:

```
char *some_str = "Hello World";
```

This is great, but now I would like to work with the second word specifically (`World`).
I do not care about changing the data, just about reading. Maybe I want to pass it to a
function or something.
Well, I could do something like this:

```
char *only_world = some_str + 6;
```

By doing this, we are reusing the NUL-terminator that `some_str` was using to terminate
itself.

Fine, what if I want to access the first word only, though? Now we have a problem.
We somehow have to end the string at the fifth index. To do that, we would have to
insert a NUL-character at index `6`. By doing so, we are changing the data that `some_str`
is pointing to, and we can therefore not use that variable anymore.

So, what do we do? We have to copy the string. That’s slow, since it involves memory lookups.
We have to allocate to memory, and then copy it. We can also use the stack if we know
the size of the data at compile time, but that is often not the case.
That would look like this:

```
char *only_hello = malloc(6);
memcpy(only_hello, some_str, 5);
only_hello[5] = 0;
```

In this simple example, the stack would have been fine, but in most realistic scenarios,
we have to use heap allocations.

This problem is solved by so-called “string views”, which are basically immutable data and a
length. You can just give the string view the same pointer as `some_str` and decrease the
length to whatever you need, `5` in this case.

### Third Issue

God forbid you forget to NUL-terminate a string. If you pass a pointer to a non-NUL-terminated
string to a function in `string.h`, like `strlen`, the computer will just keep counting
characters until it either randomly finds a NUL-character or - alternatively - until it
tries to access a region of memory that it should not touch and the operating system
kills the process.

This generally does not happen with actual strings (or string views), since you will use
functions to interact with them, and they always keep the length of the string in sync
with the data. In that case you always know when the string stops, you do not have to rely on
remembering to NUL-terminate all your strings.

### Other Issues

There are probably more issues, but these are hopefully enough to convince you.
In general, I find strings with a separately stored length more intuitive and easier
to work with.

## The Solution

Luckily, strings are not particularly hard to implement in C.
Here is how I did it.

### Types

Just so you are aware when reading the code, I `typedef` some basic types in C before I
start coding. In this case we will only need a few of them, but this is what I paste at
the start of every project of mine.

```
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

typedef uint8_t     u8;
typedef uint16_t    u16;
typedef uint32_t    u32;
typedef uint64_t    u64;

typedef int8_t      i8;
typedef int16_t     i16;
typedef int32_t     i32;
typedef int64_t     i64;

typedef float       f32;
typedef double      f64;

typedef size_t      usize;
```

This makes it more convenient to use the integer types with a fixed size instead
of the older `int`, `long`, `long long`, etc.

I generally prefer this since `int` is not the same size on all platforms.
`int32_t` on the other hand is guaranteed to be exactly 32 bits.

### Arena Allocator

For your information, I have adapted this library to be compatible with my arena implementation.
It can be found in the same repository as this string library. I have an article about it
[here](https://eliasebner.com/blog/guides/arena-allocators-in-c/) if you would like to read up on that.

What you need to know is that each function that needs to allocate some memory receives
a `struct arena *` as its first argument. Instead of `malloc` and `realloc` I use
`arena_alloc` and `arena_realloc` respectively.

### Structs

First, let’s define our string types. I don’t prefer not to `typedef` structs, but
if you want to you can do so. If you do decide to `typedef` these structs,
I would advise you to use `PascalCase` as a naming convention (to better differentiate them
from built-in types).

```
struct str_view {
    const u8       *data;
    usize           len;
};

struct str_owned {
    u8             *data;
    usize           len;
};
```

As you can see, we have two string types: `struct str_view` and `struct str_owned`.
The difference is that `struct str_owned` owns the data, and the data can also be
changed. Ideally, you should try to only have one `str_owned` pointing at any given
region in memory.

On the other hand, `struct str_view` should be used as read-only views of a
given region of data. It should not be used to modify the data.

Separating these two concerns is nice for multiple reasons.
Who owns the data becomes clear immediately. This is especially useful
when returning string structs from functions. By using this model, it is easier to
understand whether we need to concern ourselves with freeing data or something similar.

As a general rule of thumb, `struct str_owned` are heap-allocated.
If you have a `struct str_view` viewing some region in memory owned by
a `struct str_owned`, that string view is only valid as long as the underlying
owned string is still valid. That means that you have to be careful about
not freeing the `struct str_owned` and after that still using string views
that view that data.

Also, you might have noticed that I am using `u8`s (a.k.a. `uint8_t`s) instead of
`char`s. That is because, technically - even though in almost all cases it does not matter -
`char`s are not guaranteed to have a size of exactly 8 bits.
On certain embedded systems, a `char` is sometimes 16 or 32 bits large.
On very old systems, they used to be 9 bits. This has historical reasons.
A `char` is simply guaranteed to have a size of one byte, but the exact size of a byte
is not clearly defined as a definitive size in bits. Knowing all that, using `u8` is more
consistent across platforms.

> As a side note, this is also the reason why the `CHAR_BIT` macro exists. It tells you
> how many bits are in a `char` on the system that the code is run. That is because the
> size of a `char` depends on the system that you are currently on.

Also, I do not really like using a redundant type. A `u8` holds all the semantic
information I need, so `u8` it is.

### Macros

Next, we create some macros. I try to minimize the use of macros, but in certain
cases they are just perfect for the job. I believe that this is one of them.

Mainly I care about the `STR` macro, that I use to easily create a `struct str_view`
out of a `char *` literal.

```
#define LENGTHOF(s) (sizeof(s) / sizeof(*s))
#define STR(s) (struct str_view){(const u8 *)s, LENGTHOF(s) - 1}
#define STR_PRINT(s) (i32) s.len, s.data
```

`STR_PRINT` is used to print a `struct str_view`. You can use the `%.*s` format specifier
to manually give it the length of the string to be printed (since string views
are not guaranteed to be NUL-terminated, since they can view a region of memory
in the middle of a `struct str_owned`). This can be done as follows:

```
printf("Here is my string: %.*s\n", STR_PRINT(STR("some_string")));
```

Here you can also see the `STR` macro in action, which creates a `struct str_view` on the fly
from a `char *` literal.

### Freeing Memory

Since my implementation uses memory arenas, there is no need to free an owned string
specifically, but if you would like to move away from arenas you can always create
a simple wrapper function that calls `free` on the `data` field of an owned string.

### Conversion Functions

We need some way to convert between `struct str_view` and `struct str_owned` and back.
Converting an owned string to a string view is trivial; you simply use the same pointer
and length of the owned string in a `struct str_view`:

```
[[nodiscard]]
struct str_view str_owned_to_str_view(struct str_owned s) {
    struct str_view str_out = {0};
    str_out.data = s.data;
    str_out.len = s.len;
    return str_out;
}
```

Also, as you might have noticed, I like using `[[nodiscard]]`. This is a compiler
directive which makes the compiler issue a warning if the return value of the function
flagged with this directive is disregarded.
In scenarios like this one I find it to be very useful, since it is completely useless
to call this function if you are not going to do anything with the result.

We also need to convert string views to owned strings. This is a bit more tricky and
should not be done unless strictly necessary, since it requires memory allocation.
An owned string can be mutated, which means that we have to give it its own region in
memory to avoid damaging other owned strings that might be using the same memory
(recall when I said that we should try to avoid having multiple owned strings on the
same chunk of memory).

```
struct str_view_to_str_owned_out {
    struct str_owned str;
    bool success;
};
[[nodiscard]]
struct str_view_to_str_owned_out str_view_to_str_owned(
    struct arena *arena,
    struct str_view s
) {
    struct str_view_to_str_owned_out out = {0};
    struct arena_alloc_out alloc_out = arena_alloc(arena, s.len + 1);
    if (!alloc_out.success)
        return out;
    out.str.data = alloc_out.ptr;
    memcpy(out.str.data, s.data, s.len);
    out.str.len = s.len;
    out.str.data[out.str.len] = 0;
    out.success = true;
    return out;
}
```

As a small side note, whenever I need to return multiple values from a function I don’t
like using output parameters (which is a technique often used in C programs).
I prefer to return a struct. Also, it does not allow the caller of the function
to use the return value directly, which makes it more likely that the programmer
will remember to check for errors.

It makes code very verbose but more consistent in my opinion, as opposed to output
parameters. If you don’t like it, moving away from this system and adapting the code
to your own needs should be trivial.

### Utility Functions

I also wrote a bunch of functions that implement common string operations and hopefully
make the experience of working with strings much more ergonomic than the standard library.

#### Checking Whether a String Starts With a Substring

```
[[nodiscard]]
bool str_starts_with(struct str_view s, struct str_view start) {
    if (s.len < start.len)
        return false;
    return 0 == memcmp(s.data, start.data, start.len);
}
```

#### Slicing Strings

This should behave similarly to the `String.slice` function in JavaScript.

```
struct str_slice {
    i32 start;
    bool has_start;
    i32 end;
    bool has_end;
};
struct str_view str_slice(struct str_view s, struct str_slice slice) {
    struct str_view out = {0};
    if (slice.has_start) {
        if (slice.start < 0) {
            slice.start = s.len + slice.start;
        }
    } else {
        slice.start = 0;
    }
    if (slice.has_end) {
        if (slice.end < 0) {
            slice.end = s.len + slice.end;
        }
    } else {
        slice.end = s.len;
    }
    out.data = s.data + slice.start;
    i32 out_len = slice.end - slice.start;
    out.len = out_len >= 0 ? out_len : 0;
    return out;
}
```

I decided to use a `struct` for the input parameter, because this makes it
easier to support optional arguments. You can simply initialize it like this

```
struct str_slice slice = {0};
```

And then, by default, both boolean fields are false. You can then set whatever fields
you want. If you do not provide a `start`, the default is `0`. If you do not
provide an `end`, the default is the length of the string view.

`start` is inclusive, while `end` is exclusive.
I could not use negative values for representing “unset” values. For one, I really dislike
this practice, and also I wanted to give the user the option of passing negative
values which reference the end of the string.

What I mean is that if you pass `-1` as `start`, the function will start slicing at
the last character of the string. `-2` would be second to last.

This is really ergonomic whenever you only want to shave off some characters at the end
(for example, the `\r\n\r\n` at the end of the head of an HTTP string).

#### Finding a Substring in a String

I loop keep slicing away one character at a time from a string
and check if the resulting string starts with the desired substring.

```
struct str_find_substr_out {
    usize idx;
    bool found;
};
[[nodiscard]]
struct str_find_substr_out str_find_substr(
    struct str_view s,
    struct str_view sub_s
) {
    struct str_find_substr_out out = {0};
    if (s.len < sub_s.len)
        return out;
    usize match_index = 0;
    for (usize i = 0; i < s.len; i++) {
        struct str_slice slice = {0};
        slice.has_start = true;
        slice.start = i;
        struct str_view s_slice = str_slice(s, slice);
        if (str_starts_with(s_slice, sub_s)) {
            out.found = true;
            out.idx = i;
            return out;
        }
    }
    return out;
}
```

#### Determining Whether a String Contains a Substring

For this, I simply use the `str_find_substr` function defined above and extract the `found`
field from the `struct str_find_out` output.

```
[[nodiscard]]
bool str_contains_substr(struct str_view s, struct str_view sub_s) {
    return str_find_substr(s, sub_s).found;
}
```

#### Determining Whether Two Strings Are Equal

This is straight forward. Check the lengths and compare the memory.

```
[[nodiscard]]
bool str_eq(struct str_view s1, struct str_view s2) {
    if (s1.len != s2.len)
        return false;
    return 0 == memcmp(s1.data, s2.data, s1.len);
}
```

Here is the same thing, but it ignores the casing. Adding `32` to an uppercase letter
character converts it to the lowercase equivalent. This, of course, only works
with ASCII encodings.

```
[[nodiscard]]
bool str_eq_ignore_case(struct str_view s1, struct str_view s2) {
    if (s1.len != s2.len)
        return false;
    for (usize i = 0; i < s1.len; i++) {
        u8 c1 = s1.data[i];
        u8 c2 = s2.data[i];
        if (c1 >= 65 && c1 <= 90)
            c1 += 32;
        if (c2 >= 65 && c2 <= 90)
            c2 += 32;
        if (c1 != c2)
            return false;
    }
    return true;
}
```

#### Splitting Strings

This one is a bit more complicated, since it involves heap allocations.
At first, I implemented it in a way that required a memory allocation for each
new split that was found. I later changed it and created this helper function:

```
u32 str_count_substr(struct str_view s, struct str_view sub_s) {
    u32 out = 0;
    usize sub_s_index = 0;
    for (usize i = 0; i < s.len; i++) {
        struct str_slice slice = {0};
        slice.has_start = true;
        slice.start = i;
        struct str_view sliced_s = str_slice(s, slice);
        if (str_starts_with(sliced_s, sub_s))
            out++;
    }
    return out;
}
```

This counts the number of occurrences of a substring before splitting, which is useful for allocating
all the required memory upfront. The number of splits will be the number of occurrences of the
delimiter plus one.

The actual splitting happens here:

```
struct str_split_out {
    struct str_view *splits;
    usize n_splits;
    bool success;
};
// empty delimiter does not split, it returns one split
// which contains the whole string
[[nodiscard]]
struct str_split_out str_split(
    struct arena *arena, struct str_view s,
    struct str_view delim
) {
    struct str_split_out out = {0};
    if (delim.len == 0) {
        out.n_splits = 1;
        struct arena_alloc_out alloc_out =
            arena_alloc(arena, sizeof(struct str_view));
        if (!alloc_out.success) {
            return out;
        }
        out.splits = alloc_out.ptr;
        *out.splits = s;
        out.success = true;
        return out;
    }
    out.n_splits = str_count_substr(s, delim) + 1;
    struct arena_alloc_out alloc_out =
        arena_alloc(arena, out.n_splits * sizeof(struct str_view));
    if (!alloc_out.success) {
        return out;
    }
    out.splits = alloc_out.ptr;
    usize current_split_index = 0;
    // last split index always points right after the previous delimiter,
    // i.e. (splitting at " ")
    // "abc abc"
    //      ^ last_split_index
    //
    // " abc abc"
    //   ^ last_split_index
    //
    // or, before any split has been done:
    // "abc"
    //  ^ last_split_index
    usize last_split_index = 0;
    for (usize i = 0; i < s.len; i++) {
        struct str_slice slice = {0};
        slice.has_start = true;
        slice.start = i;
        struct str_view sliced_s = str_slice(s, slice);

        if (!str_starts_with(sliced_s, delim))
            continue;

        i += delim.len;
        struct str_view split = {0};
        split.data = s.data + last_split_index;
        split.len = i - last_split_index - delim.len;
        out.splits[current_split_index] = split;
        current_split_index++;
        last_split_index = i;
    }
    struct str_view split = {0};
    split.data = s.data + last_split_index;
    split.len = s.len - last_split_index;
    out.splits[out.n_splits - 1] = split;
    out.success = true;
    return out;
}
```

An empty delimiter does not split the string at all, it returns one split which contains
the entire string.
The delimiter can also be made of multiple characters (which is why I used a
`struct str_view` instead of a `char`).

### A Final Remark

Another thing to note is that `struct str_owned` are usually NUL-terminated. The `len`
field does not include the NUL-character, but it is there. This is a natural
consequence of creating a `struct str_owned` from a `struct str_view` created with the
`STR` macro. Also, I try to keep this convention in my utility functions.

This makes it very nice to work with functions in the standard library that require
you to use NUL-terminated strings. Just pass the `data` field of the `struct str_owned`,
and it acts as a normal C-string.

Also, some things are missing in this article that are actually implemented in my
string implementation that you can find in the repository. For example, one function
that is quite long I did not feel like pasting here was a `str_replace` function which

- as the name suggests - replaces all occurrences of a substring in a string with something else.

## Conclusions

All the code is available on
[my codeberg repository](https://codeberg.org/eliasebner/c_libraries).

I plan to add more utilities to this repository as time goes on, which is why the name
has nothing to do with strings, but with libraries in general.

I also wrote some tests for the string functions.

The idea is that you can simply copy the code that you need and put it in your own projects.
Feel free to use it however you please.

Also, I have recently started to employ so-called “unity builds” for my projects.
Basically, I do not use header files for my own code. Everything lives in `.c` files and I
`#include` them directly.

For very large scale projects, this is not good practice, but for personal the scale of
almost all personal projects this is completely fine and has the nice benefit of significantly
speeding up compilation times, since it completely skips the linking step, which takes the
most time.

If you do not like unity builds, you can create your own header file to hide the
API of the string library.
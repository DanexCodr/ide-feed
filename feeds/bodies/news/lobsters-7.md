I recently started writing C again for the first time since 2018, and handling errors has been an especially difficult adjustment coming from languages like Go and Zig that coddle me with their wonderful `defer` and `errdefer`. Then I read some [emails from John Carmack on inlined code](https://cbarrete.com/carmack.html) that gave me an epiphany on writing cleaner error handling code, and now I want to share it with the world.

# But First Let’s Defer

I write Go all day at my dayjob, and error handling is pretty trivial. When there’s an error we wrap it and bubble it up, and let some top dog up the call stack figure out what they want to do with it. If there is resource cleanup involved, it’s made easy with `defer`:

```
type Doer interface {
    MightError(int) error
    Lock()
    Unlock()
}

func SomeFunc(d Doer) error {
    d.Lock()
    defer d.Unlock()

    if err := d.MightError(3); err != nil {
        return errors.Wrap(err, "Doer.MightError()")
    }

    // the rest of this very important function has been hidden from you for esoteric reasons
}
```

Sometimes there’s more complicated handling, but in 99% of scenarios it’s that simple because Go doesn’t have manual memory allocation and you don’t need to worry about cleaning it up when there’s an error.

Zig on the other hand does require you to manually manage memory, which I find a little more difficult because I’m not experienced enough for it to be second nature like it is when I write Go. Here’s a snippet from my toy multiplexer that uses `errdefer`:

```
fn init(allocator: std.mem.Allocator, env_map: *std.process.Environ.Map, cfg: Config) !Model {
    const sh = env_map.get("SHELL") orelse "/bin/sh";
    const shell_z = try std.fmt.allocPrintSentinel(allocator, "{s}", .{sh}, 0);
    errdefer allocator.free(shell_z);

    const posix_block = try env_map.createPosixBlock(allocator, .{});
    errdefer posix_block.deinit(allocator);

    const tabs: []Tab = try allocator.alloc(Tab, cfg.commands.len);
    errdefer allocator.free(tabs);

    const pipes: []Pipe = try allocator.alloc(Pipe, cfg.commands.len);
    errdefer allocator.free(pipes);

    // all done with allocations (and errors)
    errdefer comptime unreachable;

    // the rest of this function has been stolen by bilgerats
}
```

I’m allocating memory for several types, and because any one of the allocations can fail I need to handle freeing up each succesful memory allocation that preceded the failure. Zig’s `errdefer` makes this easy, there’s no manual tracking of what needs to be freed at any point, because the deferred statements will execute in reverse order if the function returns an error. Also I’m following the [Reserve First](https://matklad.github.io/2025/08/16/reserve-first.html) pattern, which is where I learned `errdefer comptime unreachable` from.

# This is the C Part

Now, enter C. There’s no `defer` or `errdefer`. I’ve painted myself into a corner with some ugly code a few times because I’m so used to those tools that I don’t regularly plan ahead for what my error handling control flow will look like. Until recently I’ve been writing code that looks like this:

```
struct S {
    int foo;
};

S** some_func(const char** paths, const size_t n) {
    struct S** s = calloc(n, sizeof(S*));
    if (s == NULL) {
        return NULL;
    }

    for (int i = 0; i < n; i++) {
        s[i] = malloc(sizeof(S));
        if (s[i] == NULL) {
            for (int j = 0; j < i; j++) {
                free(s[j]);
            }
            free(s);

            return NULL;
        }

        int fd = open(paths[i], O_RDONLY);
        if (fd == -1) {
            for (int j = 0; j <= i; j++) { // note the <= instead of <
                free(s[j]);
            }
            free(s);

            return NULL;
        }

        struct stat buffer;
        if (fstat(fd, &buffer) == -1) {
            for (int j = 0; j <= i; j++) {
                free(s[j]);
            }
            free(s);
            close(fd);

            return NULL;
        }
        *(s[i]) = (struct S){ .foo = buffer.st_size };

        close(fd);
    }

    return s;
}
```

Do you see how resource cleanup is slightly different across each error handling if-block? Yuck! Yeah yeah yeah, I know it’s a terrible, contrived example, and nobody would ever write C like this. Except me like 3 weeks ago. I knew something was wrong when I wrote code like this, but I was hopelessly `defer`-brained in a world where `defer` hadn’t been born yet. Some classmates had mentioned using `goto` but I couldn’t really wrap my head around it. (We can’t share code with eachother otherwise the university would have us killed).

Then when I read those [John Carmack emails](https://cbarrete.com/carmack.html) something clicked. Carmack doesn’t mention `goto` explicitly, but these two thoughts in particular were the special sauce I needed to help me understand (emphasis mine):

A quote from Henry Spencer describing control flow in some flight software:

> It disallowed both subroutine calls and backward branches, except for the one at the bottom of the main loop. **Control flow went forward only**. Sometimes one piece of code had to leave a note for a later piece telling it what to do, but this worked out well for testing: all data was allocated statically, and monitoring those variables gave a clear picture of most everything the software was doing.

And Carmack on moving code out of large conditional blocks (emphasis mine):

> Enclosing pages of code inside a conditional or loop statement does have readability and awareness drawbacks, so leaving that code in a separate function may still be justified, but in some cases it is still possible to **move the code to another place where its execution wouldn’t be conditional**, or just **execute it at all times** and inhibit the results in some way with a very small conditional block.

Ohmygodigetitnow. Instead of having multiple exit points scattered throughout my function, each performing their own resource cleanup, I can put all resource cleanup behind a single exit point at the very end of the function. Guarding cleanup behind the default return, only reachable using a `goto`, is kinda like a psuedo-`errdefer`. Hooray! Hooray for John Carmack and Henry Spencer!! Now let’s rewrite the function above using this brand new discovery:

```
struct S {
    int foo;
};

S** some_func(const char** paths, const size_t n) {
    struct S** s = calloc(n, sizeof(S*));
    if (s == NULL) {
        return NULL;
    }

    for (int i = 0; i < n; i++) {
        s[i] = NULL;
    }

    for (int i = 0; i < n; i++) {
        int fd = open(paths[i], O_RDONLY);
        if (fd == -1) {
            goto free_mem;
        }

        struct stat buffer;
        int fstat_ok = fstat(fd, &buffer);
        close(fd);
        if (fstat_ok == -1) {
            goto free_mem;
        }

        s[i] = malloc(sizeof(S));
        if (s[i] == NULL) {
            goto free_mem;
        }

        *(s[i]) = (struct S){ .foo = buffer.st_size };
    }

    return s;

free_mem:
    for (int i = 0; i < n; i++) {
        free(s[i]);
    }
    free(s);

    return NULL;
}
```

I’d say that’s much simpler to read! And it should be less prone to bugs from expanded responsibilities over time, because there’s only one spot where resource cleanup needs to be modified. You could also use multiple labels to split cleanup into sections, if you only wanted to cleanup a subset of resources. I’m sure this is an obvious concept to most seasoned C programmers, but I’m real happy I learned something new that’ll help me write better code.

**Update**: after sharing this post on IRC, I got some helpful feedback about using `calloc` instead of `malloc` when doing allocations that might overflow (i.e. `n * sizeof(T)`), and some restructuring of the for loop in the second C example that makes the code even simpler.

This pattern is also mentioned in the [Linux kernel coding style guide](https://www.kernel.org/doc/html/v7.3/process/coding-style.html#centralized-exiting-of-functions).
It’s been a while since the latest blog post in the series but we have been
working very hard behind the scenes <sup>[1](https://ekaitz.elenq.tech/fasterMes10.html#fn:why)</sup>. This means I’ll probably forget a
few things from all we did, but there’s a good reason for that: we were making
a release.

### Background

This is the first official and serious release I make as a (co-)maintainer, and
the whole thing makes me uncomfortable. Even though people treat me as an
expert programmer sometimes, there are many things in programming that I
struggle a lot with. The first one, that I think I improved on in the last few
years, is writing software from scratch. The second is delivering things to people.

This is normal, as all my career has been focused on R&D and that’s the way
I’ve been trained to work. In the case of this specific release, something
inside me still thinks my most valuable contribution was that: the idea and
demonstration that this attempt could work.

Most of my career has been based on learning in a short time period the right
amount of information so I can achieve a reasonable result. Then I normally
move on to the next project.

Thinking about that, trying to read through my feelings, I started to realize
more and more that whatever that drives me is pushing me to somewhere else,
maybe to those parts I struggle more with…

#### Releases

Releasing code is important. It’s the only way to make people actually enjoy
the result of your work. I have no problem to admit I struggle with this.

As an R&D guy I’ve always considered myself an “enabler”. I do something, I
show how it is done and let people learn from it and actually implement it.
That’s fine in some contexts but it has been driving me to some level of
frustration recently, as the size of the projects I take part in grow.

An example of this is the RISC-V bootstrap on Guix. I spent a couple of years
of my life working on it. We made a working bootstrap for `live-bootstrap`. But
it’s not yet included in Guix because I delegated the final step. Now, even
after the years I spent on that, all the sleepless nights and everything, it’s
something I cannot enjoy fully<sup>[2](https://ekaitz.elenq.tech/fasterMes10.html#fn:fully)</sup>, and you cannot enjoy at all.

This *“my job here is done”* mentality is not enough for me anymore.

The kind of projects I do now deserve something else. I deserve better.

You deserve better.

### GNU Mes

In Mes I had like 300 commits in a branch, pretty ugly, doing, undoing and
redoing some stuff over and over again. The whole codebase was upside down, the
commit messages were sometimes good and sometimes lacking, I had fixup commits
that fixed things that were changed so much the amount of conflicts the
reordering produced was overwhelming… It was a mess. It was me trying new
things, learning and cleaning things up as I went. My arborescent thought
process at its fullest.

In my usual way of doing things, I decided to promise NlNet a release,
something I’ve never done before <sup>[3](https://ekaitz.elenq.tech/fasterMes10.html#fn:never)</sup>.

Once the bytecode adventure was done, showing some good performance improvement
was possible and that Janneke made me a co-maintainer, it was the only
acceptable thing to do.<sup>[4](https://ekaitz.elenq.tech/fasterMes10.html#fn:only)</sup>

But, if I wanted to do it, I would need to slow down.

#### Thankfully, Tim is with me

In the last part of the bytecode adventures, you remember how we included
Popsyntax, and we reworked the whole macro expansion game. That wasn’t me, but
[Tim Sample](https://ngyro.com/).

I don’t remember very well how he joined my efforts here but I guess I bothered
him with questions because he’s a long term Mes contributor and he’s also the
author of Popsyntax, the Germ scheme implementation and many interesting things more.

He decided to start over. Chose a Mes release and walked through my steps.
Removed the macro expander from the internals and wrote one in Scheme. From
there, the direction was set.

I worked through the huge branch that I had, removing the stuff that turned out
to be unnecessary, and he took over the git history, and made sure that every
single commit was working.

I cannot imagine how many conflicts the guy has been resolving. But damn [this
looks good now](https://codeberg.org/mes/mes/commits/branch/master).

### GNU Mes 0.28

This week, I released GNU Mes 0.28. The first release that I do as a GNU maintainer.

Janneke has been guiding me through the whole process — including the part of
publishing the website to GNU using CVS<sup>[5](https://ekaitz.elenq.tech/fasterMes10.html#fn:release)</sup>. I’m sure I would’ve never
been able to figure out everything on my own. What a ride it has been!

But after more than a year of work, I’m very happy that most of the comments on
the release have been positive, specially the ones from people that I worked
with and I have a huge respect for.<sup>[6](https://ekaitz.elenq.tech/fasterMes10.html#fn:rms)</sup>

But, what will you find in GNU Mes 0.28 that we didn’t mention in the blog yet?

### M2-Planet, MesCC and GCC

First of all, the main difference from the earlier blogpost is now Mes can be
compiled with both M2-Planet and MesCC, and also with GCC as before.

It’s a tricky process, because the error reporting is very limited (I’m being
benevolent here), and I was being a very nasty boy with some `goto`s inside
`switch` statements. After some wrestling with allowed C syntax, I figured it out.

M2-Planet is limited, and we had to leave some things out. When Mes is compiled
with M2-Planet it doesn’t have support for errors (aka exceptions) and those
abort the interpreter, this is because M2-Planet’s C library doesn’t include
`setjmp`. The stack operations had also to be rewritten as functions for
M2-Planet, as the macros with array access were too complex for it. With that,
Mes is a little bit slower when compiled with M2-Planet.

None of those are a big deal because that’s only the starting point of the
bootstrap process and Mes is rebuilt with MesCC right after it.

##### Mes C lib

The 0.28 release has been tested on real RISC-V hardware that I have access
to,<sup>[7](https://ekaitz.elenq.tech/fasterMes10.html#fn:zital)</sup> uncovering a few issues here and there in the Mes C Library.

First, the assembly parts that take care of program initialization in RISC-V
(written by myself a few years ago, when I was working on the bootstrap) were broken.

`setjmp` and `longjmp` that we use for error handling in Mes, and were not used
before, are also faulty. Because of this, the RISC-V version of Mes in the
bootstrap, when built with MesCC that is, does not support errors until the
issue is fixed.

I also found some extra stuff because GCC 14 decided that [implicit function
declaration warnings should become errors](https://gcc.gnu.org/gcc-14/porting_to.html#implicit-function-declaration), breaking the bootstrap
that we didn’t test in a very long time in RISC-V, first, because hardware
unavailability and, second, because Qemu is also faulty for RISC-V.

There is still a known issue with M2-Planet-built Mes that explodes when it calls `strcpy`, this can be triggered running `(procedure-disassemble map)` in
the REPL. We didn’t manage to fix this yet.

#### Macro expansion

Tim reworked the macro expansion and made a simple and understandable initial
macro expander in Scheme.

With that ready, many things started to fall off naturally.

Most of our driving issues simply disappeared. The macro expander takes the
steering wheel from the start, giving us zero garbage collection issues during boot.

The earlier macro expander I wrote in C had to also drive execution, which
could possibly call the garbage collector, killing all the C pointers that we
had. The new macro expander does everything from Scheme, so no pointers are lost: `gc_preserve` and `gc_release` are gone. The `boot-done!` mark is gone, too.

As Tim started from scratch, all the API is way cleaner, and our initial driver
is as simple as:

```clike
  /* Kickstart the initial boot file doing the bare minimum: eval one by one.
   * It will evaluate the bootstrapping macro expander and drive from there.
   */
  struct scm *result;
  struct scm *cur;
  for (cur = program; cur != cell_nil; cur = cur->cdr)
    {
      stack_push (cur);   /* Preserve from garbage collection */
      result = apply (compile_top_level_exp (cur->car, current_module ()), cell_nil);
      cur = stack_pop (); /* Recover pointer just in case it was moved */
    }
```

We can now use the stack for preservation, as it doesn’t happen that often, and
the initial driver is a minimal loop that iterates through the few top-level
expressions the initial boot file has (the macro expander). The rest of the
program is run from Scheme.

##### No Popsyntax yet

Continuing with macro expansion, even if in previous posts we talked about
Popsyntax integration, we decided to leave that out the release for now. We
focused on having a faster interpreter with a new VM.

We’ll probably release Popsyntax soon.

#### Faster than ever

Keeping macro expansion simple, we are faster than ever.

These are the updated numbers from the 0.28 release comparing with the previous
0.27.2 bugfix release, released a week before.

This is running in my Tuxedo laptop from 2020:

| Wall time (s) | Arch | fib | mescc-hello | mescc-mes |
| --- | --- | --- | --- | --- |
| mes-0.28 | amd64 | 8.66 | 2.92 | 60.93 |
| mes-0.27.2 | amd64 | 21.39 | 1.38 | 103.39 |

And this is in a VisionFive2:

| Wall time (s) | Arch | fib | mescc-hello | mescc-mes |
| --- | --- | --- | --- | --- |
| mes-0.28 | riscv64 | 78.28 | 39.08 | 529.50 |
| mes-0.27.2 | riscv64 | 175.64 | 10.21 | 926.30 |

You can see the times are similar to the `nosyntax` (it’s basically the same)
branch we described in the previous post.

Take in account the numbers are tricky because `mescc-mes` means Mes building
itself running MesCC. From one version to the other Mes changed, making it a
little bit larger (+200 LoC), which means it should take longer to compile. The
new version overcomes that, and even achieves a 40% reduction on execution time.

The `fib` benchmark is the most savage to me. There you can easily see how
running has become way cheaper. On the other hand, `mescc-hello` shows how
building a small hello-world program is more expensive, as Mes now needs to
compile the whole MesCC to bytecode. When running MesCC for longer, like in a
real program (`mescc-mes`), shows the startup time is compensated by far by the
execution speed.

In summary, we got exactly what we were aiming for: a change so big the
benchmarks don’t need to be precise. An improvement you can just *feel* by
running Mes.

##### Don’t work twice! — A funny story

When I wrote the bytecode compiler I added a very annoying warning that
complained about possibly unbound variables when you did something like:

```scheme
(define (f) (+ a 1)) ;; Possibly unbound `a`

(define a 10)

(f)
```

This was later removed because the amount of warnings it was producing was
really overwhelming and they didn’t really give us any useful information.

But! When I tested the bootstrapping process during development I realized they
appeared twice. This led me to find the build scripts were compiling each file
twice by accident.

So now, we are not just x2 faster in Mes. The bootstrapping is also x2 faster
thanks to the annoying warnings!

#### Marks and Values

Comparing to the code in the earlier post in the series, the released code has
proper support for `values` and `call-with-values` that I thought I did right
but I didn’t, really.

Consider this Guile REPL session:

```x
scheme@(guile-user)> (values 1 2 3)
$1 = 1
$2 = 2
$3 = 3
scheme@(guile-user)> (call-with-values (lambda () (values 1 2 3))
... (lambda (a b c) (+ a b c)))
$4 = 6
scheme@(guile-user)> (+ 1 (values 1 2 3))
$5 = 2
```

Versus this one in Chibi Scheme:

```x
> (values 1 2 3)
((values) 1 2 3)
> (call-with-values (lambda () (values 1 2 3)) (lambda (a b c) (+ a b c)))
6
> (+ 1 (values 1 2 3))
ERROR on line 3: invalid type, expected Number: ((values) 1 2 3)
```

According to R7RS standard, the `values` procedure returns its arguments as
values to the current continuation. If the continuation only accepts one value,
only the first value is sent to the continuation. That’s what a regular
continuation would do. With `call-with-values` the producer is called in a
continuation that accepts multiple values that go directly to the consumer procedure.

If you take a look to the Guile case, that’s exactly how it works. Chibi takes
the pragmatic approach not implementing the value discard and uses `values`
just as a container. That’s what I implemented in the previous blogpost, but in
the release I managed to do the standards compliant case, and make a REPL that
now supports multiple return values, like Guile does:

```x
GNU Mes comes with ABSOLUTELY NO WARRANTY; for details type `,show w'.
This program is free software, and you are welcome to redistribute it
under certain conditions; type `,show c' for details.

Enter `,help' for help.
mes@(guile-user)> (values 1 2 3)
[sexp=(values 1 2 3)]
$0 = 1
$1 = 2
$2 = 3
mes@(guile-user)> (call-with-values (lambda () (values 1 2 3)) (lambda (a b c) (+ a b c)))
[sexp=(call-with-values (lambda () (values 1 2 3)) (lambda (a b c) (+ a b c)))]
$3 = 6
mes@(guile-user)> (+ 1 (values 1 2 3))
[sexp=(+ 1 (values 1 2 3))]
$4 = 2
```

##### Continuation marks

The tricky part of `values` is solved with a very primitive support for
continuation marks.

When `call-with-values` is called, the current frame is labeled with a mark,
saying it accepts multiple values. When `values` is called, it checks the
current mark in order to decide if it should keep or discard its arguments. It
looks like this:

```scheme
(define (values . x)
  (if (eq? 'values (core:ref-mark)) ;; <-- marks used
    (apply %values x)   ;; The %values builtin wraps them in a container
    (car x)))

(define (call-with-mark m f)
  (core:set-mark! m) ;; <-- marks used
  (f))

(define (call-with-values producer consumer)
  (let ((vals (call-with-mark 'values producer)))
    (if (values? vals)
      (apply consumer (core:cdr vals)) ;; core:cdr extracts them
      (consumer vals))))
```

This whole thing works very well thanks to proper tail-calls, which reuse the
frames so the marks are right in the current frame all the time. It’s clean and simple.

It also uses the simplest approach possible. The `%values` builtin wraps values
in a list, adding an special `car` to it. `core:cdr` can be used to extract the
list of values back from the wrapper.

Of course, we could do this “better” just putting the values raw in the stack,
but this is good enough for now. If Chibi can get away with doing less, we
should be fine with this.

##### Delimited continuations

I would never solve this issue if it wasn’t because some random research I did,
encouraged by Tim and all the knowledge he has about Scheme implementations.

I was looking at a few papers on delimited continuations, like “Final Shift for
Call/cc: Direct Implementation of Shift and Reset” by Martin Gasbichler and
Michael Sperber, when Tim told me about his approach in Germ using continuation marks.

With that in mind, I made a very fast sketch on how would continuation marks
look like and I realized that was more than enough for the `values`
implementation I was struggling with when I saw the Mes tests (which I didn’t
bother to run during the research time) started to fail for the value discard case.

I ended up using only the most minimal thing for it, but I hope to take it a
little bit further in the future and make a proper continuation marks based
Delimited Continuation support for Mes.

### Future work

There are many things happening in this release. The diff is huge. But mostly
you have been following the effort during the latest blogposts so there’s no
need to go deeply in detail.

You saw me re-write the garbage collector, the macro expander, the driver, the
builtin implementation, vectors and structs, values, continuations … Some of
the code is gone (gc, macro expander and driver, the first implementation of
continuations) but the knowledge stays. I basically visited every single corner
in this interpreter.

I’m used to hop from one thing to the next. That’s the R&D me again. Now that I
know this software the best, I don’t want to just go do anything else. Now I’m
the best position to improve it further.

My goal for the future is to improve Mes in all those areas that I found it
could be improved but I couldn’t focus on.

**Delimited continuations** are the best way to represent continuations in an
stack based VM like the one I added to Mes. They are more lightweight, better
for the GC, and they are *composable*, allowing for more sophisticated control.
Guile supports them, so it would also help us get a step closer to Guile.

**Pointer tagging** could be a huge deal for speed and reduced memory usage in
contrast to the tagged union approach Mes has. To give you an example, in a 64
bit machine each value is at least 24 bytes, including characters. This means
if you `(string->list "Hello")` the result takes 24 bytes per cons cell, i.e
per element, plus 24 bytes per character. Pointer tagging would put the bytes
for the characters inside the pointers the cons cells have, reducing the total
memory to just what the list needs (half of the previous case) and removing the
need to access memory again to get the value of the characters.

With some **type punning** we could also revisit a few data structures we had
some trouble with (mostly frames and templates) and make them flat and easy for
the CPU to cache and access with no indirection.

In the case of the **Scheme to bytecode compiler**, just making it slightly
better than the dumbest thing possible can make Scheme code fly: builtin
inlining, avoiding boxing of non-mutated values… There are many things we can
do while keeping complexity under control.

Some **GC improvement** is also needed, maybe with a simple generational-style
garbage collector (does that exist?), at least for a few things like symbols
and globals that are never collected it could improve the performance. Even if
it doesn’t, we could always use some cleanup in the GC, which is very error
prone now.

Those are low-hanging fruits that the new architecture made more accessible. If
I just stop here they could be lost.

On the mid term, with all this together and all the improvements Janneke is
doing, we could bring MesCC to the next level as a C99 compiler written in
Guile that can be incidentally run in Mes.

On the long term, the GNU Mes project would become a very powerful
bootstrapping toolchain for languages of any kind.

### Other news

The GNU Mes development repository is now hosted in Codeberg, under the
**Mes** organization<sup>[8](https://ekaitz.elenq.tech/fasterMes10.html#fn:my)</sup>:

And we have opened an IRC channel at libera.chat: `#mes`

It looks like this is getting serious.

### Conclusion

I tend to listen to my heart, my curiosity, gut feeling, or whatever you want
to call it. That has pushed me to do uncomfortable things.

It is daunting, but it has been really rewarding.

The same way Free Software has made me learn how to program, GNU Mes has been
an amazing training camp for the skills I was lacking: reading CS papers,
preparing a release, writing code from scratch…

The project made me understand slowing down is sometimes the best way to go
forward, and that I have to be more comfortable switching gears.

This is not just programming advice, but a general approach to life that I’m
starting to understand as I get older —and hopefully wiser.<sup>[9](https://ekaitz.elenq.tech/fasterMes10.html#fn:em)</sup>

Of course, *it’s always people*.

Thankfully I’m surrounded by people I can learn from, and they bring the best
version of me. All the crazy things that I attempt would have been impossible
without the people I find in the process.

In this specific case of Mes, I’m very happy with the team we have. They
supported me throughout the whole process, but specially during the release,
when I was more insecure. I’m sure the next time I’ll be more comfortable
slowing down and doing things right.

Thanks to them for the help, inspiration and support.

Thanks to NlNet and NGI for the trust and the chance to work in important but
not-very-popular projects. Without funding, none of this is possible.

I hope we can continue to work all together for some time more.

We closed this one well. There’s no reason to stop here, though.

### Funding

The [“GNU Mes speedup effort”](https://nlnet.nl/project/GNUMes-speedup) project
has been funded through [NGI Zero Core](https://nlnet.nl/core), a fund
established by [NLnet](https://nlnet.nl) with financial support from the
European Commission’s [Next Generation Internet](https://ngi.eu) program.

1. Well, that’s *why* it’s been a while. [↩](https://ekaitz.elenq.tech/fasterMes10.html#fnref:why)
2. I have mixed feelings with it, really. From time to time I come back to it and I cannot figure out how to do it. Then something else comes and I have to leave it. It’s a shame. [↩](https://ekaitz.elenq.tech/fasterMes10.html#fnref:fully)
3. Of something I’ve never did before (an optimization work) in something that I never worked before (a scheme interpreter). [↩](https://ekaitz.elenq.tech/fasterMes10.html#fnref:never)
4. The other possibility was to chicken out, give Janneke the branch and disappear. [↩](https://ekaitz.elenq.tech/fasterMes10.html#fnref:only)
5. Yes. You read that right. [↩](https://ekaitz.elenq.tech/fasterMes10.html#fnref:release)
6. Also, getting an email by RMS himself congratulating me for the release has made me a little bit emotional. Not gonna lie. I’m sure he does that for every release, but I’m a *weak man*. [↩](https://ekaitz.elenq.tech/fasterMes10.html#fnref:rms)
7. Thanks to my friend Iban for the SSH access. Siuuuh! [↩](https://ekaitz.elenq.tech/fasterMes10.html#fnref:zital)
8. My repository has been transferred to Mes. [↩](https://ekaitz.elenq.tech/fasterMes10.html#fnref:my)
9. I can’t wait to hear people say this post is written by AI because of the em-dashes. I’m putting them here and there just to mess with them. [↩](https://ekaitz.elenq.tech/fasterMes10.html#fnref:em)
LLMs are growing alarmingly capable at finding and exploiting bugs in
production software, with increasing reports of AI-assisted hacks
in the wild.
Fortunately, LLMs are advancing quickly in their ability to write
*verified software*: programs that come with mathematical proofs,
checked by a computer, that rule out entire classes of bugs.
In April, our agents [built a JavaScript-to-WebAssembly
compiler](https://www.basis.ai/blog/verified-compiler/) but could not prove that it preserved
program behaviour. Months later, our agents [verified Linux’s nftables
compiler](https://www.basis.ai/blog/verified-nftables/), which translates firewall rules
into instructions the kernel executes. In September, MIT researchers
Frans Kaashoek and Nickolai Zeldovich used AI agents to [verify the xv6
operating-system kernel](https://arxiv.org/abs/2609.04043) down to its
machine code.

Our goal at Basis is to develop verification methods that could plausibly scale to all software, so that the systems powering critical infrastructure are secure by design and keep pace with attackers’ growing capabilities.
As LLMs advance in capability, the bottleneck is shifting away from theorem proving and towards the problem of specification: how can we be sure that the statements we prove capture the behaviour we actually care about?

To prove anything about a program, we first need a mathematical description of what it does.
This starts with describing the programming language it is written in: what every statement, loop, and function call means when it runs.
These descriptions are called a *formal semantics*, and can be written with pen and paper, but are increasingly expressed in a proof assistant such as Lean.
A handful of languages have one (Standard ML, WebAssembly, and C via CompCert), as does the RISC-V instruction set that a growing number of processors execute.
Developing each of these semantics took years of expert effort.

Most programs, however, are written in languages that do not have a formal semantics, presenting a major bottleneck for deploying verified software at scale: without a semantics, there is nothing precise to prove against.
A natural solution is to use LLMs to write semantics, but LLMs make mistakes, and a broken semantics undermines every proof built on it.
Testing helps, but as we show below, a semantics can pass every test and still be wrong. What is needed is a means to verify the semantics itself.

Languages without a formal semantics still have interpreters or compilers, which in practice define what their programs mean.
Here we consider a radical idea: make the LLM prove that its semantics agrees with the real interpreter on every program, treating the interpreter as ground truth. To do this, we compile the interpreter to RISC-V, whose meaning is already formally defined. That gives an exact, if unreadable, description of what the interpreter does with any program. The LLM then writes readable rules for the language and proves in Lean that, for every possible program, those rules predict exactly what the compiled interpreter prints. If a rule is wrong, the proof gets stuck.

We report on an experiment where we had LLMs develop a semantics and
its proof together for a small language. We used Lean to prove that the interpreter, the
program that runs code written in that language, follows those rules
even after being compiled into low-level machine instructions. The
whole development, semantics and proof, is
[on GitHub](https://github.com/BasisResearch/ship-your-interpreter).
The rest of this post walks through this
experiment, explaining first why semantics are the bottleneck for
larger verification efforts and why tests aren’t sufficient to build
trust in them. We then show how the proof process refined the semantics,
how we handled the memory reasoning, and what tools we built on the result.

# Every verified program starts from a semantics

Before you can prove a program does anything, you have to define how
each operation transforms its state, that is, define its *semantics*.
Most languages describe their semantics informally in prose, in a
reference manual, and leave the concrete details to the compiler or
interpreter implementation. A *formal*
semantics writes the rules down in mathematics, precisely enough for a
proof checker like Lean 4 to use them. Notable examples include
CompCert’s semantics for C, CakeML’s for ML, and JSCert’s for JavaScript.
Each one took years of expert effort, and often covers only a restricted
subset of its language.

For this experiment we used an extended version of WHILE, the small
imperative language used in textbooks such as Nielson and Nielson’s
[*Semantics with Applications*](https://orbit.dtu.dk/en/publications/semantics-with-applications-a-formal-introduction/).
Our version has integers, strings, first-class functions with closures, `if`, `while`
and `for` loops, and runtime errors. Its interpreter is 1,855 lines of
C, and a WHILE program looks like this (it prints 55):

```text
var i = 0;
var sum = 0;
while (i < 10) {
    i = i + 1;
    sum = sum + i;
}
println(sum);
```

The semantics an LLM wrote for WHILE is a set of rules, one for each
kind of expression and statement. These rules describe how to evaluate
an expression in terms of its subexpressions. For integer addition,
the rule is:

```rule
st, env ⊢ l ⇓ a, st'    st', env ⊢ r ⇓ b, st''    a + b = c
──────────────────────────────────────────────────────────
                 st, env ⊢ l + r ⇓ c, st''
```

A rule reads from the bottom up. The line at the bottom is its
conclusion. Starting from state `st` in environment `env`, the
expression `l + r` evaluates (`⇓`) to `c` and leaves state `st''`.
The state holds variable values, closures and everything printed so
far; the environment says which variables are in scope. The premises
above the line explain how the result follows from the subexpressions.
First `l` evaluates to `a`, leaving state `st'`. Then `r` evaluates to
`b` in that state, leaving `st''`. The final premise, `a + b = c`,
adds the two integer values using WHILE’s 64-bit wrapping arithmetic.

Take `(1 + 1) + x`, with state `[x ↦ 5]` and environment `{x}`:
`x` holds 5 and is in scope. Applying the rule gives:

```rule
[x ↦ 5], {x} ⊢ (1 + 1) ⇓ 2, [x ↦ 5]    [x ↦ 5], {x} ⊢ x ⇓ 5, [x ↦ 5]
                              2 + 5 = 7
─────────────────────────────────────────────────────────────────────
              [x ↦ 5], {x} ⊢ (1 + 1) + x ⇓ 7, [x ↦ 5]
```

That is, to evaluate `(1 + 1) + x`, we first evaluate `(1 + 1)` to get
2, then look up `x` to get 5, and add the two values to get 7. Neither
subexpression changes the state, so `[x ↦ 5]` remains unchanged.

To justify the first premise, we apply the addition rule again:

```rule
[x ↦ 5], {x} ⊢ 1 ⇓ 1, [x ↦ 5]    [x ↦ 5], {x} ⊢ 1 ⇓ 1, [x ↦ 5]
                           1 + 1 = 2
───────────────────────────────────────────────────────────────
              [x ↦ 5], {x} ⊢ 1 + 1 ⇓ 2, [x ↦ 5]
```

These rule applications form a tree that derives the value of the
whole expression from the values of its parts.

The LLM wrote about 400 lines of rules like these, in Lean ([the full
semantics](https://github.com/BasisResearch/ship-your-interpreter/blob/fb07094cff916318c34b07494a7d739f1e53989b/Vsa/While/Semantics.lean)).
Each rule looks reasonable on its own, but an end user has no rigorous
way to tell whether they faithfully describe how WHILE programs behave
when they are actually run.

# A semantics can pass every test and still be wrong

The usual way to check a semantics is to run it. Take a test suite,
run each program under the semantics and under the real interpreter,
and compare what they print. Unfortunately, in practice, this process
is insufficient to build trust in the generated semantics.

For example, an early version of our semantics passed the test suite
generated for the WHILE interpreter, but disagreed with the binary
when a function’s name reached 59 characters:

```text
fn aaa…aaa() {}           // a name of 59 a's
println("" + aaa…aaa);

semantics:  <fn aaa…aaa>
binary:     <fn aaa…aaa
```

The semantics said that concatenating a function with a string would
include its full name between `<fn `and `>`. The binary dropped the
closing `>`, and for longer names it dropped part of the name too.
No test in the suite tried functions with names this long.

The reason is in the [C
interpreter](https://github.com/BasisResearch/ship-your-interpreter/blob/fb07094cff916318c34b07494a7d739f1e53989b/c/src/interp.c#L80)
that turns a value into a string when you concatenate it with `+`:

```c
static char *stringify(Value v) {
    ...
    char buf[64];
    switch (v.kind) {
    ...
    case VAL_FN: {
        const char *name = v.as.fn->fn_expr->as.fn.name;
        if (name)
            snprintf(buf, sizeof buf, "<fn %s>", name);
        else strcpy(buf, "<fn>");
        break;
    }
    default: strcpy(buf, "<native fn>"); break;
    }
    ...
}
```

`stringify` returns a string value as it is. Any other value is first
printed into a 64-byte buffer on the stack and then copied into a
freshly allocated string. A named closure is printed with `snprintf` as
`<fn name>`, an anonymous one as `<fn>`, and the built-ins fall through
to the default case, `<native fn>`.

`snprintf` writes at most 63 characters into the 64-byte buffer. The
initial semantics used the same rendering rule for concatenation and
printing, and missed this limit. To prove agreement with the binary,
the LLM had to give concatenation its own renderer. The
[corrected
semantics](https://github.com/BasisResearch/ship-your-interpreter/commit/d0d2609425f0024a0b8a2ad0570f14723b391a8d)
cuts a closure’s rendering to its first 63 bytes:

```rule
"" + f        ⇓  take 63 ("<fn " ++ f ++ ">")
```

This is the kind of detail an
implementation accumulates internally but nobody writes down
explicitly, which is precisely why a semantics transcribed by hand, or
written by an LLM, can miss it. Nor is it a detail no program would
notice: code in dynamic languages routinely relies on the string form
of a function, for logging, for dispatch keyed on a name, or for
comparing serialised values. Even simple violations like
this undermine any verification effort built
on top of the semantics, and can leave holes that hide security
vulnerabilities. To build secure and scalable semantics, we need to go
beyond tests, since a test suite only checks the programs someone (or
an agent) thought to write.

# Ship your interpreter

Shipping your interpreter means checking the semantics against the
implementation people actually run. Compile the interpreter the
language already has, and make the LLM prove that the binary
*refines* the semantics, that is, that the two agree on what every
program prints.

The theorem we
[proved](https://github.com/BasisResearch/ship-your-interpreter/blob/fb07094cff916318c34b07494a7d739f1e53989b/VsaIris/Interp/EndToEnd.lean#L159)
is this one:

```lean
theorem endToEnd_refinement :
  ∀ p c, Loaded interpRunLayout p (fillZero c) →
    (∀ out, BigStep p out ↔ Halts c out 0) ∧
    (Diverges c → ¬ ∃ out, BigStep p out)
```

The theorem says for any WHILE program `p`, and *any* machine
configuration `c`, if the machine configuration satisfies a property
`Loaded`, then the semantics match what the compiled binary will
do. `Loaded interpRunLayout p (fillZero c)` here says that `c` is a
machine about to run `p` through the interpreter binary. The first
conclusion, `(∀ out, BigStep p out ↔ Halts c out 0)`, says that the
semantics derives output `out` if and only if the machine halts with
exit code `0` having printed `out`, i.e. for successfully terminating
programs the predicted outputs are equivalent. The second says that any program
`p` on which the machine runs forever (`Diverges c`), is a program the
semantics derives no terminating output for.

We can visualise this theorem as a *commuting square*, showing how the
semantics and the binary agree on a program’s output. In the diagram
below, the top arrow relates a program `p` to the output
`out` predicted by the semantics. The bottom arrow relates a machine
state `c` to the output printed when the binary halts successfully.
The dashed line on the left is the `Loaded` condition connecting the
program to that machine state. Under this condition, the theorem says
the two outputs agree, shown by the double line on the right. The
orange arrow shows how a failed attempt to prove that agreement sends
the LLM back to revise a rule of the semantics.

The theorem catches a wrong semantics in both directions. If the
semantics is too permissive, it derives an output the binary never
prints, and the left-to-right half fails. If it is too strict, it has
no rule for something the binary does, and the right-to-left half
fails. Either way the LLM gets a proof obligation it cannot discharge.
In our experience, that obligation usually points at the rule that is
wrong.

RISC-V is an open processor design. We use its formal model, written
in [Sail](https://github.com/riscv/sail-riscv) and translated into Lean,
to define how each machine instruction executes. The binary is the
actual ELF executable: 1,855
lines of interpreter C compiled by gcc, linked against dlmalloc and
newlib, 25,336 instructions in all. For comparison, the xv6 kernel
verified with MachCSL is 8,697 RISC-V instructions, built from 6,593
lines of C and assembly, although its proof also covers concurrency,
which ours does not need. The C compiler’s output, the C library and
the memory allocator are all inside our theorem. A person
who wants to trust the result reads the statement above, the hypothesis
`Loaded`, and the two short definitions of `Halts` and `Diverges`. They
do not need to trust `BigStep`, because the proof checks it against the
binary.

# Developing the semantics and proof together

Developing the proof forced the LLMs to account for four details in
the semantics:

- integer arithmetic had to wrap at 64 bits, because negating the smallest integer was unsatisfiable against the machine;
- a for loop’s initialiser had to ignore an abrupt status, because the C does;
- built-ins had to render differently in print and in concatenation;
- long closure names had to be cut at 63 bytes.

Each correction started either as an obligation that would not close
or as a run of the binary that disagreed with the semantics.

The 63-byte cut is a representative example. The proof of the
concatenation case needed the semantics’ rendering to equal the
binary’s, and for long names it didn’t, so the obligation could not be
discharged until the rule changed.

The proof also caught mistakes in the LLM-generated lemmas about the C
library. The LLMs stated what each function does and then proved
that statement against the machine code. An allocator reserve that no
heap satisfied after a single `malloc(24)`, a `realloc` lemma that was
false for sizes that wrap, and an `exit` routine that writes `errno`
without its lemma saying so all showed up the same way, as obligations
that would not close.

# Separation logic makes the binary proof tractable

LLMs wrote all of the proof. Most of the difficulty lay in reasoning
about memory. We needed a specification for `malloc`, the function
that allocates memory, which would let us prove that allocating a new
block preserves the data already held by the interpreter. Even
`println("n = " + x)` allocates three strings and frees two of them.
Throughout those calls, the program’s variables and the half-built
result must remain intact.

The textbook way to do this is to give each function a Hoare triple
together with a *footprint*, a set of bytes the function may write.
Facts about memory outside the footprint carry across a call
unchanged. A triple `{ P } code { Q }` reads as “if `P` holds before
`code` runs, then `Q` holds after it”. For `malloc`, such a
specification reads roughly as follows, where `F` is a fixed set of
addresses:

```text
{ heap H }
  p := malloc(n)
{ heap ((p, n) :: H)  and  p is fresh }
modifies F
```

Unfortunately, no such `F` exists. From the same heap, `malloc(32)`
writes the header of the new top chunk at address `0x82000238`, so `F`
must contain that address. `malloc(64)` instead returns the block
`[0x82000210, 0x82000250)`, which contains it. Once the caller owns
that block, facts about its bytes have to survive later calls, so `F`
must also exclude `0x82000238`. The LLMs [proved in
Lean](https://github.com/BasisResearch/ship-your-interpreter/blob/92470bdbbfe24c8c25b5be44128aa6395e6acce8/VsaIris/DlHeap.lean#L515)
that no fixed set of addresses can satisfy both requirements, after a
first attempt that worked around the problem one fact at a
time had stalled for three weeks.

Separation logic solves this by making the footprint depend on the
heap. We ported [MachCSL](https://arxiv.org/abs/2609.04043), the logic
behind the xv6 proof, to the newly released
[iris-lean](https://arxiv.org/abs/2609.24252).<sup>[1](https://www.basis.ai/blog/ship-your-interpreters/#fn:1)</sup> In separation
logic the allocator *owns* the free bytes of its arena, and `malloc`’s
[specification](https://github.com/BasisResearch/ship-your-interpreter/blob/fb07094cff916318c34b07494a7d739f1e53989b/VsaIris/DlHeap.lean#L209)
hands part of them to the caller:

```text
{ isHeap H }
  p := malloc(n)
{ (p = 0 ∗ isHeap H)
  ∨ (isHeap ((p, n) :: H) ∗ blockOwn p n) }
```

Here `∗` is the *separating conjunction*, which says that its two
halves hold of disjoint parts of memory, and the result `p` is either
null or a fresh block. `isHeap H` owns every byte of the arena outside
the live blocks `H`. Initially, the allocator owns `0x82000238`, so
`malloc(32)` may write it. If the caller instead requests `malloc(64)`,
that byte passes to the caller through `blockOwn`, and later calls
cannot touch it. Anything else the caller owns is not
mentioned in the specification, and the frame rule carries it across
the call in one step. After the port, the rest of the proof closed in a
few days.

At its peak the proof was about a million lines of Lean, two thirds of
it generated by 35 scripts the LLMs wrote, which read the binary and
emit a proof rule for each of about 11,800 instructions. A later pass
replaced the generated proof families with abstractions proved once,
such as a symbolic executor for machine code, and brought the proof
under 200,000 lines. It uses no axioms beyond Lean’s standard
ones (`propext`, `Classical.choice` and `Quot.sound`).

# The theorem applies to real programs

A theorem with a hypothesis is only useful if that hypothesis can be
satisfied. If `Loaded` described a machine state that never occurs,
our theorem would hold vacuously and tell us nothing about the binary.

We had the LLMs [prove in Lean that `Loaded` holds for ten
programs](https://github.com/BasisResearch/ship-your-interpreter/tree/fb07094cff916318c34b07494a7d739f1e53989b/Vsa/Sim/Boot/Gen).
For each one, they constructed a machine state at the interpreter’s
entry, with the program in memory alongside the binary, the runtime
and the allocator. Lean checked that each state met the theorem’s
precondition.<sup>[2](https://www.basis.ai/blog/ship-your-interpreters/#fn:2)</sup>

We also replayed 85,483 machine steps from the executable and checked
that the resulting memory matched the constructed state byte for
byte. The link from the executable file and its boot trace to that
state was checked by scripts; Lean checked the precondition and the
execution from that state onwards. For the full [loop test
program](https://github.com/BasisResearch/ship-your-interpreter/blob/fb07094cff916318c34b07494a7d739f1e53989b/c/tests/while.wl),
which extends the earlier example with two more sums, the binary
provably halts after printing `55`, `2500` and `36` on separate lines.

The precondition includes enough heap and stack space for the program.
A [later
theorem](https://github.com/BasisResearch/ship-your-interpreter/blob/fb07094cff916318c34b07494a7d739f1e53989b/VsaIris/Interp/EndToEndChecked.lean#L12)
replaces these two assumptions with checkers that run on the program.

# Once you trust the semantics, the tools are cheap

A validated semantics also works as an interface. Anything you prove
sound against `BigStep` is sound for the binary, by composing it with
the refinement theorem, and that composition is a few lines of
Lean. So we had LLMs build four tools on top of it.

The refinement proof took about a month and is about 140,000 lines of
Lean. The four tools below were opened as pull requests over three
days, and come to about 33,000 lines between them, most of it the
compiler.

The first tool is a [type
checker](https://github.com/BasisResearch/ship-your-interpreter/pull/5).
It catches invalid operations before a program runs. For example,
these two programs are rejected:

```text
"a" - 1;               // subtracting an integer from a string
```

```text
var x = 1;
x = "s";               // assigning a string to an integer variable
```

The [proofs for these
examples](https://github.com/BasisResearch/ship-your-interpreter/blob/fb07094cff916318c34b07494a7d739f1e53989b/Vsa/While/TypeExamples.lean)
show that neither program can pass the checker. Its soundness theorem
rules out type errors in accepted programs, including when they run
through the interpreter binary. Division by zero, a failed `assert`
and the interpreter’s call-depth limit remain possible; those require
reasoning about values as well as types.

The second tool is a [program
logic](https://github.com/BasisResearch/ship-your-interpreter/pull/2),
which lets us prove what a particular program computes. The loop near
the start of this post adds the integers from 1 to 10. The full [test
program](https://github.com/BasisResearch/ship-your-interpreter/blob/fb07094cff916318c34b07494a7d739f1e53989b/c/tests/while.wl)
also adds the odd integers from 1 to 100, using `break` and `continue`,
and computes a third sum with nested loops. The LLMs used the logic
to prove that running this program through the interpreter binary
terminates and prints exactly:

```text
55
2500
36
```

The third tool is an [abstract
interpreter](https://github.com/BasisResearch/ship-your-interpreter/pull/3),
an analysis that tracks possible values through a program and raises
alarms for potential runtime errors. It analyses that same test
program with [no
alarms](https://github.com/BasisResearch/ship-your-interpreter/blob/fb07094cff916318c34b07494a7d739f1e53989b/Vsa/AbsInt/Examples.lean),
proving it free of runtime errors. It also establishes that the final
values of `sum`, `total` and `acc` are 55, 2500 and 36. The analysis
computes these results automatically, and its soundness proof connects
them to execution of the binary.

The fourth tool does without the interpreter entirely. In April, our
agents built a compiler but could not prove it correct. Here the
semantics came first, and the LLMs built a [verified
compiler](https://github.com/BasisResearch/ship-your-interpreter/pull/9)
from all of WHILE (strings, closures, calls, `for`, `return` and
`assert`) straight to RISC-V. Compile the sum program above, and the
resulting machine code prints the same three numbers. The correctness
theorem establishes agreement for every program meeting its
preconditions. A [checked
version](https://github.com/BasisResearch/ship-your-interpreter/pull/10)
analyses allocation cost, so its theorem needs no assumption about
available heap space.

Dropping the interpreter also makes WHILE programs faster. We ran
every program in the interpreter’s test suite both ways on the
[spike](https://github.com/riscv-software-src/riscv-isa-sim) RISC-V
simulator. Counting the interpreter from the moment it starts evaluating, so that
parsing is not charged against it, compiled code retires between 2.7
and 8.2 times fewer instructions, and both routes print the same
output. These are instruction counts on a simulator rather than timings
on hardware.

Once the semantics is trusted, it *is* the language, and the binary we
started from is no longer needed to run WHILE programs.

# What’s next: Lua, OCaml and, one day, CPython

Our experiment with WHILE targeted a toy language. LLMs developed its
formal semantics, proved that the compiled interpreter follows it,
and built verified tools on top. We are now scaling this approach up
to real languages.

[Ship your Lua](https://github.com/BasisResearch/ship-your-lua)
targets Lua 5.4.7 compiled to bare-metal RISC-V. The binary already
runs on the Sail model and agrees with native Lua, and the plan cuts
the proof at the VM: first the bytecode interpreter against a bytecode
semantics, fragment by fragment over opcodes, then the source language
against the bytecode.

[Ship your OCaml](https://github.com/BasisResearch/ship-your-ocaml)
takes advantage of the way OCaml bootstraps itself. OCaml’s bootstrap compiler is checked
into its repository as bytecode, `boot/ocamlc`, and runs on `ocamlrun`.
We have `ocamlrun` running on the Sail model, compiling programs with the
real `boot/ocamlc`. The plan there ends in a fixpoint: if the source
semantics says the compiler compiles its own sources to exactly the bytes
of `boot/ocamlc`, and the compiler’s back end is proved correct, then
those bytes get a meaning without verifying their 412,000 bytecode
instructions one at a time.

For both projects, we have already stated the headline theorems in
Lean. What remains is to close their proofs.

The north star is CPython. We believe that current agents make an
LLM-written, machine-validated semantics for Python feasible, given
enough compute. Tools like the ones in the previous section could then
be built on it, with guarantees that reach the CPython binary.
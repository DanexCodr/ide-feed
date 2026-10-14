The "optimized" builds were actually slower. Now, my compiler doesn't implement
many optimizations at the moment so I wouldn't expect a huge improvement, but
being 1.4x slower should definitely not happen.<sup>[[1]](https://386s.org/w/lua-antcc-pessimization/#fn-1)</sup> One of the optimizations
that antcc *does* have is inlining, which generally speaking is one of the most
impactful compiler optimizations and it usually improves benchmarks all around.

# Inlining?

So my first thought was, okay my inlining heuristics and thresholds are very simple
and not really tuned, so perhaps it's being too aggressive and blowing up the code
size, leading to very bad instruction cache thrashing. If I disabled inlining, the pessimization
seemed to go away, which could support that theory. That's not a very satisfactory
explanation though, and I would like to fix it, so I looked into it more.

The main culprit was in the function `luaV_execute`, whose code blew up to
~43KB with -O2, **~2.4x** bigger than the -O1 build. Now, [this function](https://github.com/lua/lua/blob/c33b1728aeb7dfeec4013562660e07d32697aa6b/lvm.c#L1127)
is the main bytecode interpreter loop for the Lua VM, and these are one of the
worst kinds of functions for a compiler to deal with: it's a huge function with
a hot loop, many cases/control flow branches, distinct hot/cold paths nested in
the graph where a wrong optimizer or register-allocation decision can pessimize
the whole loop, etc...<sup>[[2]](https://386s.org/w/lua-antcc-pessimization/#fn-2)</sup> So the baseline function is a tricky one, but it
doesn't explain this.

Tweaking the inlining thresholds didn't seem to help: either few things got
inlined (like -O1) and binary size & performance stayed roughly the same, or
small functions start getting inlined and the pessimization happens. In
particular, these functions were getting inlined (some in multiple instances):
`floatforloop`, `lessequalothers`, `lessthanothers`, `luaV_idiv`, `luaV_mod`,
`luaV_modf`, `luaV_shiftl`, `luaV_tointegerns`, plus some of their respective
callees.  In the Lua source code link above you can see those are all pretty
small simple functions.

Looking at the final codegen is not that helpful, but examining the IR<sup>[[3]](https://386s.org/w/lua-antcc-pessimization/#fn-3)</sup>
revealed something interesting: after all optimizations, the -O2 IR was **only
11% bigger** than -O1. How could that be amplified to a **2.4x** difference in
the binary?

# Code generation?

The final passes that run after optimizations and before code generation are
[instruction selection](https://en.wikipedia.org/wiki/Instruction_selection) and [register allocation](https://en.wikipedia.org/wiki/Register_allocation). Instruction selection
mostly concerns itself with ensuring instruction operands are ready to be
lowered into machine code, but keeps temporaries as virtual registers. For
example, for x86-64, it models memory operands and will turn a sequence of IR
instructions like:

```
;; int *ptr, res;
i64 %t2 = shl %index, 2
ptr %t3 = add %ptr, %t2
;; res = ptr[index]
i32 %res = loads32 %t3
```

into

```
i32 %res = loads32 addr [%ptr + %index * 4]
```

It does other things like introducing register constraints for certain operations, but anyway
because it only expands into small sequences of instructions like this, it couldn't be the
cause.

## Register allocation

Register allocation is the process of mapping virtual temporaries to the target architecture's
physical registers. For the previous snippet, that might result in

```
i32 RAX = loads32 addr [RSI + RDX * 4]
```

which is compiled to the x86 instruction `mov eax, DWORD PTR [rsi + rdx * 4]`.

The problem is that there are infinite virtual temporaries but a small number of registers,
so you have to choose which variables get which registers and when there are not enough
registers for all of them, some of them have to go on the stack, which is called *spilling*.

Most operations require values to be in registers, so spilled variables
often have to be moved back and forth between registers. Or even worse, they might have
to be moved between two different stack slots in some situations.

antcc has a basic implementation of [linear scan regalloc](https://c9x.me/compile/bib/Wimmer10a.pdf). If there is
a lot of register pressure and many temporaries get spilled, potentially a lot
of instructions can be created just to shuffle values between stack and
registers.

And indeed, comparing relative IR size increase before and after regalloc at -O2, the +11%
difference was turning into +70% blowup after regalloc... looking at the disassembly,
**>40%** of instructions in `luaV_execute` were just stack⇄register `mov`s. That's really bad,
something being inlined must be resulting in this dreadful register pressure and spilling,
but it's not obvious what.

So let's examine the pre-regalloc IR:

```
<< Before regalloc >>
function luaV_execute : void(struct lua_State *, struct CallInfo *)
abi: (RDI, RSI)
   ....
    ptr %4613 = add %0, 56
    ptr %5340 = add %0, 40
    b @2
  @2:   ; preds: @1, @892       ; loop depth: 1
    i64 %4489 = phi @1 undef, @892 %3124
    i64 %3030 = phi @1 undef, @892 %3065
    i64 %4636 = phi @1 undef, @892 %2287
    i64 %4764 = phi @1 undef, @892 %3869
    i64 %2874 = phi @1 undef, @892 %3929
    i64 %2694 = phi @1 undef, @892 %3981
    i64 %4872 = phi @1 undef, @892 %3804
    i64 %2297 = phi @1 undef, @892 %3497
    i64 %5062 = phi @1 undef, @892 %3158
    i64 %2208 = phi @1 undef, @892 %3145
    i64 %2161 = phi @1 undef, @892 %4191
    i64 %5275 = phi @1 undef, @892 %4225
    i64 %5290 = phi @1 undef, @892 %4252
    i64 %1791 = phi @1 undef, @892 %4370
    i64 %3813 = phi @1 undef, @892 %3195
    i64 %3807 = phi @1 undef, @892 %4403
  ....
```

Oh. That looks strange.

My compiler like most modern backends uses a [Static Single-Assignment](https://en.wikipedia.org/wiki/Static_single-assignment_form) representation.
In this form, straight-line code such as (I'm using C-like pseudocode to simplify):

```
x = a + b
x = x + y    # reassigning x
use(x)
```

Becomes:

```
x1 = a + b
x2 = x1 + y  # fresh definition
use(x2)
```

That is, there are no variable mutation instructions. The reason this
representation is great for compilers is that it simplifies all kinds of
data-flow analysis and permits some more powerful optimizations than the
non-SSA counterpart.

With control flow, data flow merges are explicit in the IR:

```
if (cond) {
    x = a + 1
} else {
    x = b - 1
}
use(x)
```

In SSA form is represented as:

```
if (cond) B0: {
    x1 = a + 1
} else B1: {
    x2 = b - 1
}
x3 = phi(B0: x1, B1: x2)
use(x3)
```

This magic "phi" instruction<sup>[[4]](https://386s.org/w/lua-antcc-pessimization/#fn-4)</sup> has as its result the value of `x1` or `x2` depending on which
control flow branch was taken. Same approach can be applied for variables modified in loops:

```
i = 0
while (cond) {
    use(i)
    i += 1
}
```

in SSA:

```
i0 = 0
Entry: while (cond) {
  LoopBegin:
    i_l = phi(Entry: i0, LoopEnd: i_n)
    use(i_l)
    i_n = i_l + 1
  LoopEnd:
}
```

Textually, it looks like the `phi` function references `i_n` before its definition, but
importantly that value is only taken in the loop back-edge (`LoopEnd -> LoopBegin`),
and at that point the value of `i_n` is available.

A key thing to realize here is that this `i_l` temporary, being a loop phi, is live
across the whole loop, since its value is used to compute the next iteration.

Going back to that IR dump from Lua:

```
@2:   ; preds: @1, @892       ; loop depth: 1
  i64 %4489 = phi @1 undef, @892 %3124
  i64 %3030 = phi @1 undef, @892 %3065
  ...
```

Ignore the undefs for now, and notice the `; preds` line indicating the
predecessors of that block: `@1`, the beginning of the function, and `@892`,
hundreds of blocks later: the end of the main interpreter loop. Meaning, we
have 16 phis that are live across the whole loop. This is what is creating a
lot of register pressure, wrecking register allocation and resulting in that
big code size blowup from stack spilling traffic. So, what are these phis,
where do they come from, and why the `undef`s...

# mem2reg

C programs don't start in SSA form, so they have to go through a transformation
pass. I borrowed the terminology and design from clang/LLVM in my compiler:

So C code like:

```
int x;
x = foo();
...
if (x < 0) { x = -x; }
return x;
```

Initially generates an IR that looks like:

```
@1:
  ptr %x = alloca 4 bytes
  i32 %t1 = call foo()
  store i32 %x, %t1
  ...
  i32 %t2 = load i32 %x
  bool %cond = lth %t2, 0
  br %cond, true -> @2, false -> @3
@2:
  i32 %t3 = load i32 %x
  i32 %t4 = neg %t3
  store i32 %x, %t4
  b @3
@3:
  i32 %t5 = load i32 %x
  ret %t5
```

And mem2reg turns it to:

```
@1:
  i32 %x1 = call foo()
  ...
  bool %cond = lth %x1, 0
  br %cond, true -> @2, false -> @3
@2:
  i32 %x2 = neg %x1
  b @3
@3:
  i32 %x3 = phi @1 %x1, @2 %x2
  ret %x3
```

I'm glossing over the trickiest part of this, which is knowing when and where
to insert these phi instructions in the general case. There's basically two
algorithms to do it, and the one I'm using is from the paper ["Simple and
Efficient Construction of SSA Form (Braun et al, 2013)"](https://pp.ipd.kit.edu/uploads/publikationen/braun13cc.pdf).  The gist of
it is: walk the control-flow graph (CFG) in reverse post-order (RPO); when you
see a write, memoize the current definition keyed by the block; when you see a read,
look for that definition or query the predecessors' definitions recursively and
insert phis when that lookup finds distinct definitions. Loops are trickier:
because the back-edge predecessors haven't been visited yet, you have to insert
a provisional phi and resolve it later.

Something about C that almost every language that came after it removed as a Bad Idea is
the ability to leave variables uninitialized. For example:

```
int x;
if (foo()) {
    int y = bar();
    x = y;
}
use(x);
```

After the control flow merge, `x` is `phi(uninitialized, y)`. That is what
the `undef` in my IR is. The way it's introduced in my mem2reg is that if the
recursive "read current definition" function reaches all the way to the
beginning of the function without finding a definition, it gives it `undef`.
(Later on, moves and operations on `undef` can be effectively optimized away.)

So was the Lua interpreter reading uninitialized variables? Well, no. Look at
some of the affected code from the interpreter function:

```
  vmcase(OP_SHRI) {
    TValue *rb = vRB(i);
    int ic = GETARG_sC(i);
    lua_Integer ib;
    if (tointegerns(rb, &ib)) {
      pc++; setivalue(s2v(ra), luaV_shiftl(ib, -ic));
    }
    vmbreak;
  }
  // several other instructions follow that same template
```

The key is the `tointegerns` macro, which in turn calls the function `luaV_tointegerns`:

```
int luaV_tointegerns (const TValue *obj, lua_Integer *p, F2Imod mode) {
  if (ttisfloat(obj))
    return luaV_flttointeger(fltvalue(obj), p, mode); // <- this gets inlined
  else if (ttisinteger(obj)) {
    *p = ivalue(obj);
    return 1;
  }
  else
    return 0;
}
```

In -O2, this function and `luaV_flttointeger` get inlined, resulting in an
expansion like this (simplified):

```
  vmcase(OP_SHRI) {
    ...
    lua_Integer ib;   // <--- declaration
    int tointegerns_ret;
    if (ttisinteger(rb)) {
      ib = ivalue(rb);   // <--- write
      tointegerns_ret = 1;
    } else if (ttisfloat(rb)) {
      ...
      ib = (lua_Integer)fvalue(f);    // <--- write
      tointegerns_ret = 1;
    } else {
      tointegerns_ret = 0;
    }
    if (tointegerns_ret) {
      ... (use ib)
    }
    vmbreak;
  }
```

`mem2reg` is always ran after every inlining pass. The `undef` in question
comes from the variable `ib` which I've marked. You can see that the local
variable is initialized in every path where the inlined function returns `1`,
but `mem2reg` cannot correlate that with the later `if (tointegerns_ret)` guard,
so it sees a possibly uninitialized read.

But that does *not* tell the whole story! It explains the `undef`, but not why
the phi is live across the whole loop. After all, this local is scoped to a
block inside a branch of the loop, it does not live across loop iterations...

## The problem

Eventually I figured out the root cause: I was treating the idea of "variables
start as uninitialized" *too* literally in mem2reg. When it encountered an
`alloca`, it didn't give it a definition for the current block. This sounds
correct, and the recursive lookup in the algorithm terminates at the function
entry with an `undef`. But recall the catch with loops being that when you
encounter a backedge, you don't know if there's a later definition, because you
haven't visited the whole loop yet, so you insert a provisional phi...

In essence, my mem2reg was behaving as if code like:

```
int foo() {
  while (...) {
    int x;
    if (...) {
      x = bar();
    }
    use(x);
  }
}
```

was actually

```
int foo() {
  int x;
  while (...) {
    if (...) {
      x = bar();
    }
    use(x);
  }
}
```

In the 2nd function, the value of `x` is kept across iterations, whereas in the
1st, the value of `x` is a 'fresh' uninitialized every time the `if` branch is
not taken...  This is not a miscompilation: as far as C is concerned, this is
fine because uninitialized variables' values are not legally usable anyway. And
if you frame it in terms of stack-allocated variables, it's a sensible
approach: the slot for x is fixed for the whole function and doesn't get
reset between loop iterations, so it keeps the previous iteration's whatever
it was and it doesn't matter. But the problem is that in the context of SSA
form, this generates something like:

```
while (...) {
  %x = phi(undef, %x2)
  if (...) {
    %x1 = bar();
  }
  %x2 = phi(%x, %x1)
  use(%x2);
}
```

And it is these loop phis that result in the pathological register allocation.
The fix was one line:

```
--- a/src/ir_mem2reg.c
+++ b/src/ir_mem2reg.c
@@ -244,6 +244,8 @@ mem2reg(Function *fn) {
             v->cls = k;
             v->i = var;
             sb.vars[var] = v;
+            v->curdefs[blk->id] = UNDREF;
          } else {
             sb.vars[var] = DEAD;
          }
```

Initializing the var as undefined (a nice oxymoron) at the place of the
`alloca` ensures that the recursive lookup doesn't cross loop backedges and
insert phis in the loop header. This is enough to fix this case, and that
change made the mysterious pessimization disappear.

This problem can still bite for C code that is old-style declaring all
variables at the top of the function. It's possible to fix this general case by
using [Tarjan's algorithm](https://en.wikipedia.org/wiki/Tarjan's_strongly_connected_components_algorithm) to find the graph SCCs of the phi data-flow to
detect cycles, and making use of these undef semantics when classifying
phis as redundant; but I haven't implemented that yet.

Jump threading an inlined function used directly as a branch condition, or more
generally SSA-aware phi jump threading, could've also fixed the branch
correlation issue that led to `mem2reg` not seeing the dominating write of
those variables and introducing undefs.

I made use of AI agents to help debug this issue. It saved me a lot of time in
investigating, filtering through disassemblies and IR dumps, running the compiler
with different inlining thresholds and measuring, etc; but it was not good at
trying to find the root cause. It proposed probably around 10 convoluted
"fixes" before I eventually arrived at the conclusion myself. Still <$1 well
spent for the sake of reducing tedium.

## Benchmarks

Lua 5.4.7, [bench.lua](https://386s.org/asset/202610-antcc-bench.lua), AMD Ryzen 5 5600G. Take
these with a grain of salt.

Pre-fix:

![lua runtime benchmarks #1](https://386s.org/asset/antcc-lua-bench-1.png)

antcc was worse than even tcc, but that's mainly because my frontend was
lowering switch statements to linear if-else chains. I implemented a simple
binary search codegen, which was one of those things that I just hadn't gotten
around to yet; and a few other minor optimizations; after this fix.

Current numbers:

![lua runtime benchmarks #2](https://386s.org/asset/antcc-lua-bench-2.png)

Do note that antcc performs `mem2reg` by default when passed no optimization
flags, unlike gcc. It might seem counterintuitive, but from my testing, running
`mem2reg` improves compile times too; presumably due to the reduced number of
stack store/load instructions for the backend to churn through.

And compile times:

![lua compilation benchmarks](https://386s.org/asset/antcc-lua-compiletime.png)

I omitted the bars for clang because they are all very similar to gcc.

1. The only difference between -O1 and -O2 is in inlining thresholds and -O2 running some optimization passes more than once. [↩](https://386s.org/w/lua-antcc-pessimization/#fr-1-1)
2. This is why LuaJIT's interpreter in hand-written assembly beats almost every other bytecode interpreter, [and it's not just about the while-switch loop](http://lua-users.org/lists/lua-l/2011-02/msg00742.html) [↩](https://386s.org/w/lua-antcc-pessimization/#fr-2-1)
3. Intermediate representation [↩](https://386s.org/w/lua-antcc-pessimization/#fr-3-1)
4. variously known as phi function, φ, /faɪ/, /fi/, phony instruction [↩](https://386s.org/w/lua-antcc-pessimization/#fr-4-1)
5. Not to be confused with the dynamic `alloca()` function. [↩](https://386s.org/w/lua-antcc-pessimization/#fr-5-1)
6. The `register` storage class exists, but it doesn't really matter in modern architectures so you (almost) never see it used. [↩](https://386s.org/w/lua-antcc-pessimization/#fr-6-1)
Take a really boring loop: walk two `[]float32` slices and add them together, element by element. Written the normal way in Go, the CPU handles one pair per step. The funny thing is that the same CPU has hardware that could handle eight pairs at once, and a plain Go loop never uses it.

That hardware is **SIMD**. Until recently, the only way to use it from Go was hand-written assembly. Now Go has an experimental `simd/archsimd` package (Go 1.26) and a portable `simd` package on top of it (Go 1.27), so you can write normal Go that turns into SIMD instructions.

We’ll start with how SIMD works inside the CPU and meet Go’s two SIMD packages. Then we’ll go through the most common SIMD operations, with Go code for each one, peek at how the compiler makes it all work, and finally put everything together in a small, real example.

> **📌 A note on scope**
>
> Everything here is based on **Go 1.27.0** with `GOEXPERIMENT=simd`. The package is experimental, so names may change between releases. I’ll stick to **amd64** (Intel and AMD CPUs) and skip a lot of the instruction set to keep the core ideas clear.

Before we write any Go, though, let’s see what that “eight pairs at once” hardware actually does.

## What SIMD Actually Means

SIMD stands for **Single Instruction, Multiple Data**. But what does that actually mean? Let’s put the same operation side by side, once without SIMD and once with it.

![Side-by-side comparison. On the left, labeled “scalar”, eight separate ADD instructions stacked vertically, each adding one pair of numbers (1 + 10, 2 + 9, … 8 + 3) into a result of 11, with a clock next to every row and “8 instructions” at the bottom. On the right, labeled “SIMD”, a row a = [1 2 3 4 5 6 7 8\] plus a row b = [10 9 8 7 6 5 4 3\] produce a row of eight 11s at once, with a single clock and “1 instruction”.](https://internals-for-interns.com/images/go-simd-scalar-vs-simd.webp)

The scalar version is a normal loop: one instruction adds one pair of numbers, then the next instruction adds the next pair, eight times in a row. The SIMD version works differently: instead of adding the pairs one at a time, a single CPU instruction takes all eight numbers from `a` and all eight from `b` and adds them in one go. One instruction instead of eight, so the whole thing finishes much faster.

There’s a catch, though: all eight additions have to be *the same operation*. You can’t add in one slot and multiply in the next. SIMD shines when you have lots of independent data that all needs the same treatment, which is very common in things like image processing, audio or machine learning.

But notice that in the SIMD version, all eight numbers had to sit together *somewhere* before the add. That somewhere is a special kind of register.

A normal register holds a single 64-bit value, so eight floats don’t fit. SIMD has its own, much wider **vector registers**: 128, 256 or 512 bits, depending on your CPU. In this post we’ll mostly use 256-bit ones, which hold exactly eight `float32` values.

But 256 bits of *what*? Floats? Bytes? Let’s look at one of those registers a bit closer.

![One 256-bit YMM register drawn four times, stacked vertically, each time sliced differently. Top: 32 thin slices labeled “32 × int8”. Second: 16 slices labeled “16 × int16”. Third: 8 slices labeled “8 × int32 / float32”. Bottom: 4 wide slices labeled “4 × int64 / float64”. Lane 0 is marked at the left end of every row.](https://internals-for-interns.com/images/go-simd-lanes.webp)

A vector register is just a bunch of bits, and as you can see in the diagram, we can split it into slots of different sizes, called **lanes**, like 32 lanes of 8-bit integers or 4 lanes of `float64`. The register doesn’t care; each instruction decides how to split it. Most of our examples use 8 lanes of `float32`.

So now we have big registers split into lanes. How do we actually use them?

## The SIMD Cycle: Load, Operate, Store

Almost every piece of SIMD code follows the same three steps: get the data into a register, do some math on it, and get the result back out. Let’s go through them one by one.

The first step is filling the register, and that’s the job of a **vector load**.

![A row of memory cells on top, labeled “memory: a [\]float32”, holding the values 1 2 3 4 5 6 7 8 9 10, with “addresses increase” pointing to the right. A brace under the first eight cells is labeled “32 contiguous bytes”, and a smaller grey brace under 9 and 10 says “left for next time”. A single arrow goes down from the first brace into a register Y0 drawn below, whose lanes, numbered 0 to 7, now contain 1 to 8, lane 0 holding a[0\].](https://internals-for-interns.com/images/go-simd-load.webp)

The load grabs eight `float32` values from our slice in one go and drops them into the eight lanes of the register: `a[0]` goes to lane 0, `a[1]` to lane 1, and so on. One instruction, one full register. The `9` and `10` at the end don’t fit, so they’ll have to wait for the next load. We’ll see later how to deal with leftovers like that.

With `a` in one register and `b` in another, we can do the math.

![Two registers drawn one above the other: a = [1 2 3 4 5 6 7 8\] and b = [10 9 8 7 6 5 4 3\]. Between each pair of lanes is a small plus sign, and a straight vertical arrow runs from each lane pair down into a third register labeled a + b, holding [11 11 11 11 11 11 11 11\]. Red vertical lines run through all three registers between every lane, walls that no value crosses.](https://internals-for-interns.com/images/go-simd-vertical-add.webp)

Look at any single lane: lane 3 of `a` plus lane 3 of `b` goes into lane 3 of the result. Each lane only talks to the same lane in the other register. That’s called a **vertical** operation, and most SIMD instructions work like this. You can think of each lane as its own little calculator, with walls between them, so nothing leaks from one lane into the next. And the result doesn’t go back to memory: it lands in another register, ready for the next instruction.

Once we’re done with the math, we have to get the results out of the register. There are two ways out. The first one is a **vector store**, the opposite of a load.

![A register at the bottom with eight lanes, labeled lane 0 to lane 7, each holding 11. A thick arrow goes up from it into an output slice labeled “out [\]float32”, eight contiguous memory cells indexed [0\] to [7\], each now holding 11.](https://internals-for-interns.com/images/go-simd-store.webp)

All eight lanes go back to memory in one go: lane 0 lands in `out[0]`, lane 1 in `out[1]`, and so on. That’s what you want if your result is another slice.

The second one is **extracting a lane**.

![A register with eight lanes, labeled lane 0 to lane 7, each holding 220, with lane 0 highlighted in red. A curved red arrow labeled GetElem(0) goes from lane 0 to a small box on the right labeled “a normal float32”, holding 220.](https://internals-for-interns.com/images/go-simd-extract.webp)

Here we pull a single lane out into a normal variable, lane 0 in this case. That’s fine for one value, but doing it eight times in a row would throw away all the speed we just gained.

That’s the whole cycle, at the hardware level. Now let’s see how we write it in Go.

## SIMD in Go: Two Packages

Before we look at more operations, let’s meet the Go packages we’ll use, so the code examples in the rest of the post make sense right away. Go has two of them, and both only exist when you build with `GOEXPERIMENT=simd`.

### simd/archsimd: One Type per Register

The low-level package is `simd/archsimd`. It’s tied to your CPU’s architecture ([package docs](https://pkg.go.dev/simd/archsimd@go1.27.0)), and it maps almost one to one onto the registers and lanes we just saw. Types are named after the lane type and the number of lanes: `Float32x8` is a register with eight `float32` lanes (256 bits), `Float32x4` has four (128 bits), and `Float32x16` has sixteen (512 bits). And using them follows the same cycle we just saw: you load your data with `LoadFloat32x8`, run operations like `Add` on it, and finally get the data out again with `Store` or `GetElem`.

Here’s what that looks like for adding two slices, eight floats at a time (we’ll deal with the leftover elements later):

```go
func add(a, b, out []float32) {
	for i := 0; i+8 <= len(a); i += 8 {
		x := archsimd.LoadFloat32x8(a[i:])
		y := archsimd.LoadFloat32x8(b[i:])
		x.Add(y).Store(out[i:])
	}
}
```

### simd: The Portable One

`archsimd` gives you full control, but there’s a catch: you have to pick the register size yourself. Code written with `Float32x8` uses 256 bits even on a CPU that could do 512, and it doesn’t even compile on ARM, which has no 256-bit registers. Go 1.27 fixes this with a second package: `simd`.

Its types don’t have a size in their names: `Float32s`, `Int8s`, `Mask32s` ([package docs](https://pkg.go.dev/simd@go1.27.0)). The size is chosen *when the program starts*, based on your CPU, and `v.Len()` tells you how many lanes you got. Other than that, the methods are the same ones: `Add`, `MulAdd`, `Store`, and so on.

Here’s the same function with `simd`:

```go
func add(a, b, out []float32) {
	var v simd.Float32s
	n := v.Len() // 4, 8 or 16, depending on the CPU
	for i := 0; i+n <= len(a); i += n {
		x := simd.LoadFloat32s(a[i:])
		y := simd.LoadFloat32s(b[i:])
		x.Add(y).Store(out[i:])
	}
}
```

The loop is the same. The only difference is that the step isn’t a hardcoded `8` anymore: we ask the vector how many lanes it has.

In the rest of the post I’ll use `archsimd` for the examples, because its types match the pictures exactly: one `Float32x8`, eight lanes.

With the packages in hand, let’s see what else we can do with those lanes besides adding them.

## A Gallery of Common Operations

Loads, vertical math and stores get you a long way. But real code has constants, running totals, `if`s and data in the wrong order, and every lane still has to run the same instruction. Here are the tools SIMD uses for that.

For each one, I’ll also show what it looks like in Go with `simd/archsimd`.

Let’s start with the simplest one.

### Broadcast: One Value Everywhere

Lots of code mixes a vector with a single number: multiply everything by `0.5`, compare everything with `5`. But vertical instructions need two full registers. So where does the second one come from?

![A single small box labeled “a float32” holding the value 5, with eight red arrows fanning out from it into all eight lanes of a register, numbered 0 to 7, which becomes [5 5 5 5 5 5 5 5\]. The register is labeled BroadcastFloat32x8(5).](https://internals-for-interns.com/images/go-simd-broadcast.webp)

You just copy the number into every lane. That’s a **broadcast**: one scalar in, a full register out. It’s cheap, and you usually do it once, before the loop.

```go
five := archsimd.BroadcastFloat32x8(5) // [5 5 5 5 5 5 5 5]
```

With constants sorted out, let’s get more out of each math instruction.

### Fused Multiply-Add: Two Operations in One

A lot of number crunching boils down to “multiply these, then add the result to a running total”. Do we really need two instructions for that?

![Two fused multiply-add steps stacked top to bottom, every register drawn as a row of eight lanes. Step 1, “acc = x1 · y1 + acc”: x1 = [1 2 3 4 5 6 7 8\], y1 = [2 2 2 2 2 2 2 2\] and acc = [0 0 0 0 0 0 0 0\] flow down, lane by lane, into acc = [2 4 6 8 10 12 14 16\], with the side note “1 × 2 + 0 = 2”. A red arrow labeled “reused” carries that result into the acc input of step 2, “acc = x2 · y2 + acc”: x2 = [8 7 6 5 4 3 2 1\], y2 = [3 3 3 3 3 3 3 3\] and acc = [2 4 6 8 10 12 14 16\] flow down into acc = [26 25 24 23 22 21 20 19\], with the side note “8 × 3 + 2 = 26”.](https://internals-for-interns.com/images/go-simd-fma.webp)

Start with step 1 and follow lane 0: `1 × 2`, plus the `0` already sitting in `acc`, gives `2`. Every lane does the same thing at the same time, all in one instruction. That’s a **fused multiply-add**, or **FMA**, and it’s usually as fast as a plain multiply. Now follow the red arrow: the result of step 1 becomes the `acc` input of step 2, so lane 0 computes `8 × 3 + 2 = 26` and builds on what was already there. Chain enough of these steps and each lane keeps its own running total, which is exactly what you need for something like a [dot product](https://en.wikipedia.org/wiki/Dot_product)
.

In Go, that’s the [`MulAdd`](https://pkg.go.dev/simd/archsimd@go1.27.0#Float32x8.MulAdd) method, which computes `x*y + z`:

```go
x1 := archsimd.LoadFloat32x8([]float32{1, 2, 3, 4, 5, 6, 7, 8})
x2 := archsimd.LoadFloat32x8([]float32{8, 7, 6, 5, 4, 3, 2, 1})

var acc archsimd.Float32x8                           // all lanes 0
acc = x1.MulAdd(archsimd.BroadcastFloat32x8(2), acc) // [2 4 6 8 10 12 14 16]
acc = x2.MulAdd(archsimd.BroadcastFloat32x8(3), acc) // [26 25 24 23 22 21 20 19]
```

So far, every lane computes a number. Next, let’s make the lanes answer questions.

### Comparisons Produce Masks

In normal code you’d write `if a[i] > 5 { ... }`. In SIMD you can’t do that, because all eight lanes run the same instruction, so you can’t jump somewhere for some lanes and not for others. So what does a comparison give you back?

![Two registers a = [1 7 3 9 5 8 2 6\] and a broadcast register [5 5 5 5 5 5 5 5\] feed into a comparison labeled “a > 5”. The output is shown in two forms. On the AVX2 side, a full vector register whose lanes are either 0xFFFFFFFF (true, shaded) or 0x00000000 (false). On the AVX-512 side, a small k register holding just eight bits, 0 1 0 1 0 1 0 1 read from lane 0, one bit per lane.](https://internals-for-interns.com/images/go-simd-compare-mask.webp)

It gives you a **mask**: one true/false answer per lane. Here we compared `a` against our broadcast `5`, and lanes 1, 3, 5 and 7 came out true. The picture shows the two ways the hardware stores that answer. For a 256-bit register like ours, it’s a normal vector register where “true” lanes are all ones and “false” lanes are all zeros. With 512-bit vectors, which need AVX-512, it goes into a small, dedicated **mask register** instead (`k0` to `k7`), using just one bit per lane. In Go you don’t have to care which one you get: a mask is just a `Mask32x8`.

```go
a := archsimd.LoadFloat32x8([]float32{1, 7, 3, 9, 5, 8, 2, 6})
five := archsimd.BroadcastFloat32x8(5)

mask := a.Greater(five) // true in lanes 1, 3, 5 and 7
bits := mask.ToBits()   // 0b10101010, one bit per lane (lane 0 is the lowest bit)
```

And that brings us to the SIMD version of `if`.

### Masking and Blending: The SIMD “if”

A mask on its own doesn’t do anything, though. How do we use it?

![Three registers stacked on top: x = [1 7 3 9 5 8 2 6\], y = [0 0 0 0 0 0 0 0\] and mask = [F T F T F T F T\], with the T lanes in red. Below them, a result register labeled x.IfElse(mask, y) holding [0 7 0 9 0 8 0 6\]. In the T lanes a solid red line comes down from x, past y and through the mask, into the result; in the F lanes a dashed black arrow comes down from y instead.](https://internals-for-interns.com/images/go-simd-blend.webp)

Go lane by lane through the result: where the mask is true, the value comes from `x`, and where it’s false, from `y`. That’s a **blend**, and it’s how SIMD does `if/else`: compute *both* answers for every lane, then use the mask to pick one per lane. Blending with zeros, like the `y` here, is so common it has its own name, **masking**: “keep the lanes that passed, zero the rest”.

```go
x := archsimd.LoadFloat32x8([]float32{1, 7, 3, 9, 5, 8, 2, 6})
var y archsimd.Float32x8                          // all lanes 0
mask := x.Greater(archsimd.BroadcastFloat32x8(5)) // [F T F T F T F T]

r := x.IfElse(mask, y) // [0 7 0 9 0 8 0 6]
r = x.Masked(mask)     // same thing, shorter
```

Now let’s leave the math aside for a moment and move data around.

### Permutes: Moving Lanes Around

Everything so far keeps lane *i* in lane *i*. But sometimes the data is in the right register and the wrong lanes, and you need to reverse it or reorder it.

![On top, a source register x = [a b c d e f g h\] with lanes numbered 0 to 7. In the middle, an index register [7 6 5 4 3 2 1 0\]. On the bottom, a result register [h g f e d c b a\]. Curved red arrows cross from the source lanes, through the index register, into the result lanes, reversing the order.](https://internals-for-interns.com/images/go-simd-permute.webp)

Each lane of the result looks at its own index and copies that lane of `x`. Result lane 0 has index `7`, so it gets `x`’s lane 7, `h`. Result lane 1 has index `6`, so it gets `g`. And so on, until the last lane, which has index `0` and gets `a`. That’s a **permute**: the values don’t change, the indices just decide where each one ends up. Here they reverse the register, but any order works, and you can even pick the same lane more than once. That flexibility is the secret sauce behind tricks like super-fast JSON parsers.

```go
x := archsimd.LoadFloat32x8([]float32{1, 2, 3, 4, 5, 6, 7, 8})
idx := archsimd.LoadUint32x8([]uint32{7, 6, 5, 4, 3, 2, 1, 0})
r := x.Permute(idx) // [8 7 6 5 4 3 2 1]
```

Moving lanes around isn’t always enough, though.

### Horizontal Operations: Across the Lanes

Permutes move values between lanes, but every value still ends up in exactly one lane. Sometimes we want the opposite: combine lanes of the *same* register, like adding up partial sums into a total. That’s a **horizontal** operation.

![Two four-lane registers, x = [1 2 3 4\] and y = [5 6 7 8\]. Red braces join neighboring lanes, 1 and 2, 3 and 4 in x, 5 and 6, 7 and 8 in y, and a red arrow with a plus sign goes from each pair into one result register [3 7 11 15\]. The first two result lanes are marked “from x” and the last two “from y”.](https://internals-for-interns.com/images/go-simd-concat-add-pairs.webp)

Each pair of neighboring lanes gets added together: `1+2`, `3+4` from `x`, then `5+6`, `7+8` from `y`, and the four sums go one after the other into the result, `[3 7 11 15]`. That’s [`ConcatAddPairs`](https://pkg.go.dev/simd/archsimd@go1.27.0#Float32x4.ConcatAddPairs): `x.ConcatAddPairs(y)` gives `[x0+x1, x2+x3, y0+y1, y2+y3]`.

```go
x := archsimd.LoadFloat32x4([]float32{1, 2, 3, 4})
y := archsimd.LoadFloat32x4([]float32{5, 6, 7, 8})
r := x.ConcatAddPairs(y) // [3 7 11 15]
```

There’s one last problem we’ve been ignoring since the very first load.

### Handling the Tail: Partial Loads

Now back to the leftovers from the load picture: our slice has 10 elements, and a register takes 8. After one full chunk, 2 are left. That leftover bit at the end is called the **tail**.

![A memory row with the last two elements of a slice, 9 and 10, followed by cells marked with a question mark labeled “not ours: past the end of the slice”. A mask [T T F F F F F F\] sits under it. Arrows show 9 and 10 going into lanes 0 and 1 of a register, while lanes 2 to 7 are filled with zeros. Labeled “partial load: 2 loaded, 6 zeroed”.](https://internals-for-interns.com/images/go-simd-partial-load.webp)

The question marks are the danger: the memory after our slice isn’t ours, and a normal 8-lane load would read it anyway. A **partial load** solves it: you get back a register where only the lanes that exist hold your data, and the rest are zeros. If you’re adding things up, zeros are the perfect filler, because they don’t change the result.

One honest warning, though: in Go 1.27.0, the amd64 version still reads the full 32 bytes under the hood and zeroes the extra lanes afterwards. The result is correct, but it does touch that memory. That’s already been [fixed upstream](https://github.com/golang/go/commit/beaf715aaab14ba306c447f03ee4e972b2e5514a), so it should be gone in a future release.

```go
s := []float32{1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
x, n := archsimd.LoadFloat32x8Part(s[8:]) // x = [9 10 0 0 0 0 0 0], n = 2
```

Those are some of the most common tools SIMD gives us. Time to look at the Go side again.

## How Go Makes It Work

We’ve been calling methods like `x.Add(y)` all along. But how does a method call end up as a single CPU instruction? And how can the `simd` package work without knowing the register size in advance? Let’s take a look under the hood.

### archsimd: Methods Without Bodies

If you look at how `Add` is declared, you’ll find something odd: `func (x Float32x8) Add(y Float32x8) Float32x8`, and no body at all. That’s because `Add` is a **compiler intrinsic**: the compiler recognizes it by name and puts the instruction right there, instead of calling a function.

![A top-to-bottom pipeline of five boxes connected by downward arrows. Box 1, “Go source”: x.Add(y) with x, y : Float32x8, and a side note “no function body, no call”. Box 2, “intrinsic table (ssagen)”: Float32x8.Add → OpAddFloat32x8, Vec256. Box 3, “generic SSA”: v3 = AddFloat32x8 v1 v2. Box 4, “lowering rule (simdAMD64.rules)”: AddFloat32x8 => VADDPS256. Box 5, “register allocation + codegen”: the final instruction VADDPS Y2, Y1, Y0 in red. A side box connected to boxes 4 and 5, “register classes”, lists X0–X14: vectors (X15 is always zero), X16–X31: only with AVX-512, and K1–K7: masks (K0 means no mask).](https://internals-for-interns.com/images/go-simd-compiler-pipeline.webp)

Follow that pipeline step by step. First, the compiler finds `x.Add(y)` in its table of intrinsics ([`simdAMD64intrinsics.go:40`](https://github.com/golang/go/blob/go1.27.0/src/cmd/compile/internal/ssagen/simdAMD64intrinsics.go#L40)) and turns it into an SSA operation, just like we saw in the [SSA article](https://internals-for-interns.com/posts/the-go-ssa/)
. A rewrite rule then turns that into the amd64 `VADDPS` instruction ([`simdAMD64.rules:30`](https://github.com/golang/go/blob/go1.27.0/src/cmd/compile/internal/ssa/_gen/simdAMD64.rules#L30)), and the register allocator picks the registers. One method call, one instruction.

The types get special treatment too. `Float32x8` is a struct with a small marker field inside ([`types_amd64.go`](https://github.com/golang/go/blob/go1.27.0/src/simd/archsimd/types_amd64.go#L319)) that tells the compiler: “keep this whole thing in one vector register”.

That works for `archsimd` because the size is right there in the type name. The portable `simd` package doesn’t have that luxury.

### simd: Compiling Your Code Several Times

If the register size is only known when the program starts, how does the compiler know which registers and instructions to use?

![A box “your code: func dot(a, b [\]float32) float32, uses simd.Float32s”. A thick arrow labeled “midway rewrite (compiler, after type checking)” leads down to a box “dot (dispatcher, same name)”. A small box “at startup: CPU features + GODEBUG=simd” points into the dispatcher. From the dispatcher, arrows go to four boxes in a two-by-two grid: dot@128 → Float32x4, dot@256 → Float32x8, dot@512 → Float32x16 and dot@emulated → pure Go. The arrow to dot@256 is thick and red, labeled “chosen on an AVX2 machine”.](https://internals-for-interns.com/images/go-simd-midway.webp)

It doesn’t have to pick: it **compiles your code several times**. You write one `dot` function using `simd.Float32s`. A compiler pass called **midway** ([`rewrite.go`](https://github.com/golang/go/blob/go1.27.0/src/cmd/compile/internal/midway/rewrite.go#L16)) makes a copy of it for each width, `dot@simd128`, `dot@simd256` and `dot@simd512`, plus a pure-Go fallback, `dot@simd0`. It also adds a small dispatcher that keeps the original name `dot`, so the rest of your code calls it as usual. At startup, Go checks the CPU and the dispatcher sends every call to the right copy. On an AVX2 machine, that’s `dot@simd256`.

If you want to choose yourself, you can: `GODEBUG=simd=0` forces the pure-Go version, and `GODEBUG=simd=256` (or `128`, `512`) forces a width ([`midway_common.go:22`](https://github.com/golang/go/blob/go1.27.0/src/simd/midway_common.go#L22)). And if you ever see a name like `dot@simd256` in a stack trace, now you know where it came from.

So far we’ve looked at each piece on its own. Time to put them all together.

## Walking Through an Example

Now we have everything we need to follow a real example from Go source to silicon. Let’s use a **dot product**: multiply two `[]float32` slices pair by pair and add everything up. It shows up everywhere, from vector search to machine learning, and it uses almost everything we’ve seen so far. Here’s the `archsimd` version, which is small enough to read in one go and runs with `GOEXPERIMENT=simd go run .` on Go 1.27:

```go
package main

import (
	"fmt"
	"simd/archsimd"
)

func dotSIMD(a, b []float32) float32 {
	var acc archsimd.Float32x8 // eight running sums, all zero
	i := 0
	for ; i+8 <= len(a); i += 8 {
		x := archsimd.LoadFloat32x8(a[i:])
		y := archsimd.LoadFloat32x8(b[i:])
		acc = x.MulAdd(y, acc) // acc = x*y + acc, lane by lane
	}
	// The tail: fewer than 8 elements left, the missing lanes load as zero.
	x, _ := archsimd.LoadFloat32x8Part(a[i:])
	y, _ := archsimd.LoadFloat32x8Part(b[i:])
	acc = x.MulAdd(y, acc)

	// Fold the eight lanes down to one number.
	s := acc.GetLo().Add(acc.GetHi()) // 8 lanes -> 4
	s = s.ConcatAddPairs(s)           // 4 -> 2
	s = s.ConcatAddPairs(s)           // 2 -> 1
	return s.GetElem(0)
}

func main() {
	if !archsimd.X86.AVX2() || !archsimd.X86.FMA() {
		fmt.Println("this CPU lacks AVX2/FMA")
		return
	}
	a := []float32{1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
	b := []float32{10, 9, 8, 7, 6, 5, 4, 3, 2, 1}
	fmt.Println(dotSIMD(a, b)) // 220
}
```

Let’s walk through it step by step. `main` first checks that the CPU supports AVX2 and FMA, because `archsimd` won’t check for you: if the CPU doesn’t have an instruction, running it doesn’t fall back to anything slower, it just crashes the program with an **illegal instruction** error. Then `acc` starts as a zero vector, and we enter the loop with 10 elements.

![Step 1, “full chunk (a[0:8\], b[0:8\])”: x = [1 2 3 4 5 6 7 8\] and y = [10 9 8 7 6 5 4 3\] go through MulAdd into acc = [10 18 24 28 30 30 28 24\].](https://internals-for-interns.com/images/go-simd-dot-step1.webp)

**Stage 1, the full chunk.** `i+8 <= 10`, so we load `a[0:8]` and `b[0:8]` into two registers with one load each, just like in the load diagram. `MulAdd` multiplies them lane by lane and adds `acc`, which is still all zeros, so `acc` becomes the eight products `[10 18 24 28 30 30 28 24]`. Next time around, `i` is 8 and `16 <= 10` fails, so the loop ends.

![Step 2, “tail (a[8:\], b[8:\])”: x = [9 10 0 0 0 0 0 0\] and y = [2 1 0 0 0 0 0 0\], with the six zero lanes shaded and labeled “six zero lanes (masked off)”. MulAdd updates acc to [28 28 24 28 30 30 28 24\], with +18 and +10 marked over lanes 0 and 1.](https://internals-for-interns.com/images/go-simd-dot-step2.webp)

**Stage 2, the tail.** Two elements are left. `LoadFloat32x8Part` loads `9` and `10` into lanes 0 and 1 and zeros into the other six (and the same for `b`). One more `MulAdd`: lane 0 gains `9*2 = 18`, lane 1 gains `10*1 = 10`, and the zero lanes add nothing. `acc` is now `[28 28 24 28 30 30 28 24]`.

![Step 3, “fold”: acc = [28 28 24 28 30 30 28 24\] is split into [28 28 24 28\] and [30 30 28 24\], which are added element-wise into [58 58 52 52\]. ConcatAddPairs turns that into [116 104 116 104\], and a second ConcatAddPairs into [220 220 220 220\].](https://internals-for-interns.com/images/go-simd-dot-step3.webp)

**Stage 3, the fold.** Each lane of `acc` has its own running total, so we have eight numbers, and the answer we want is all eight added together. We could take them out one by one and add them, but that means seven normal additions, one after another. Instead, we let SIMD do it in a few big steps, cutting the number of values in half each time. That works because when you add numbers, the order doesn’t matter: `1 + 2 + 3 + 4` is the same as `(1 + 3) + (2 + 4)`.

First, we cut the register in two. `GetLo` gives us the first four lanes, `[28 28 24 28]`, and `GetHi` the last four, `[30 30 28 24]`. Then we add those two halves lane by lane, like any other vertical add, and get `[58 58 52 52]`. We haven’t lost anything: `58` is just `28 + 30`, so these four numbers still add up to the same answer as the original eight.

Next, `ConcatAddPairs` adds each lane to its neighbor: `58 + 58 = 116` and `52 + 52 = 104`. We only have one register, so we pass `s` as both arguments, and that’s why the result shows the same two sums twice, `[116 104 116 104]`. The repeated half is harmless, we just ignore it. Now the whole answer is in two numbers, `116` and `104`. One more `ConcatAddPairs` adds them together, and every lane ends up holding `220`.

![Step 4, “out”: the register [220 220 220 220\] with lane 0 marked, and an arrow labeled “GetElem(0) — same as the scalar loop” pulling out a single 220, in red.](https://internals-for-interns.com/images/go-simd-dot-step4.webp)

**Stage 4, out.** `GetElem(0)` pulls lane 0 into a normal `float32`: **220**, the same answer as the scalar loop.

And here’s the nicest part. If you build it and disassemble `dotSIMD` with `go tool objdump`, the heart of the loop is exactly the three instructions our diagrams promised, two loads and one fused multiply-add:

```text
VMOVDQU 0(DX), Y2
VMOVDQU 0(R11), Y3
VFMADD213PS Y1, Y3, Y2
```

and the end of the function is the fold, instruction for instruction: two `VEXTRACTF128` for `GetLo`/`GetHi`, a `VADDPS`, two `VHADDPS`, and a `VPEXTRD` to pull out lane 0. No calls, no allocations, the data never leaves the vector registers.

Is it worth it? On my machine (an AMD Ryzen AI Max+ 395), with two slices of 4096 floats, the scalar loop takes about **3.9 µs** and the SIMD version about **0.41 µs**, roughly 9 times faster. But it isn’t free. The scalar version is a tiny loop that anyone can read, while the SIMD one needs a tail, a fold and a CPU check, and it’s much harder to follow and maintain. And the gains depend a lot on the problem: a dot product over long, contiguous slices is close to the best case, while code with lots of branches, scattered memory access or short inputs may get much less, or nothing at all. So measure first, and keep SIMD for the hot loops where it really pays off.

## Summary

Let’s look back at what we’ve seen. **SIMD** lets one instruction do the same operation on many values at once, using wide **vector registers** (128, 256 or 512 bits, depending on your CPU) split into **lanes**. Almost every SIMD loop follows the same cycle: **load** data into a register, do the math lane by lane, and **store** the results back (or pull out a single lane). A few extra tools, like **broadcast**, **fused multiply-add**, **masks**, **blends**, **permutes**, **horizontal adds** and **partial loads**, cover what real code needs.

On the Go side, `simd/archsimd` maps all of this almost one to one: `Float32x8` is a register with eight `float32` lanes, and methods like `Add` are **intrinsics** that turn into a single instruction. Checking that your CPU supports them is your job. And if you don’t want to pick a register size at all, the portable `simd` package compiles one copy of your code per size and picks the right one at startup.

Putting it all together, our **dot product** ran about 9 times faster than the plain loop on my machine. But that speed has a price: SIMD code is harder to read and maintain, and how much you gain depends a lot on the problem and the data. So measure first, and keep it for the hot loops where it really pays off.

It’s all still experimental, so names may change, but the ideas underneath won’t. Once you can picture the lanes, reading SIMD code in Go gets a lot easier.

In the next article, we’ll look at another way to make Go code faster without rewriting it: **profile-guided optimization** (PGO). We’ll see how you can hand the compiler a CPU profile from your real program, and how it uses that profile to decide where to try harder, like inlining the functions that actually matter and turning hot interface calls into direct ones.
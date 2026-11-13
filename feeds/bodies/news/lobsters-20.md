Write Futhark code inline in your J programs and get automatic
parallel execution on all CPU cores.

**Download:** [futhark.ijs](https://chen.cat/j/futhark/futhark.ijs)
(v1.7.0)

The Futhark-J Bridge lets you write [Futhark](https://futhark-lang.org/) code directly in your J
source files. Futhark is a purely functional data-parallel programming
language that compiles to highly efficient parallel code. This bridge
handles compilation, caching, and FFI calls automatically.

```
NB. Define a Futhark function inline
double =: 'entry f (xs: []f64) : []f64 = map (*2) xs' fut

NB. Use it like any J verb
double 1 2 3 4 5
   2 4 6 8 10
```

J is already excellent at array programming, but some workloads
benefit from parallel execution across multiple CPU cores. Futhark
excels at:

The library includes benchmarks comparing native J to Futhark. Here
are some highlights:

| Workload | Max Speedup | Notes |
| --- | --- | --- |
| Mandelbrot escape | **1525x** | Variable iteration count per element |
| Logistic map (1000 iters) | **14x** | High compute per element |
| Standard deviation | **2x** | Multiple passes over data |
| Dot product | 0.3x | Memory-bound; J wins |

**Key insight**: Futhark shines when computation
dominates memory access. For simple operations like dot product, native
J is faster due to FFI overhead.

```
NB. Load the library
load 'futhark.ijs'

NB. Array transformations
square =: 'entry f (xs: []f64) : []f64 = map (\x -> x * x) xs' fut
square 1 2 3 4 5
   1 4 9 16 25

NB. Reductions to scalar
total =: 'entry f (xs: []f64) : f64 = reduce (+) 0 xs' fut
total 1 2 3 4 5
   15

NB. Two-input (dyadic) functions
dot =: 'entry f (xs: []f64) (ys: []f64) : f64 = reduce (+) 0 (map2 (*) xs ys)' fut
(1 2 3) dot (4 5 6)
   32

NB. Scalar input functions (v1.6.0) - use 0 : 0 for multiline Futhark
factors_src =: 0 : 0
  entry f (n: i64) : []i64 =
    let (_, _, result) =
      loop (x, i, acc) = (n, 2i64, ([] : []i64))
      while x > 1 do
        if x % i == 0
        then (x / i, i, acc ++ [i])
        else (x, i + 1, acc)
    in result
)
factors =: factors_src fut

factors 12
   2 2 3
factors 100
   2 2 5 5

NB. Fixed-size array dimensions (v1.7.0)
NB. Output has fixed inner dimension [3]
triple =: 'entry f (ns: []i64) : [][3]i64 = map (\n -> [n, n*2, n*3]) ns' fut
triple 1 2 3 4 5
   1  2  3
   2  4  6
   3  6  9
   4  8 12
   5 10 15
```

Futhark entry points follow this pattern:

```
entry <name> (<param>: <type>) : <return_type> = <body>
```

Common operations:

| Futhark | J Equivalent | Description |
| --- | --- | --- |
| `map (*2) xs` | `2 * xs` | Element-wise transform |
| `reduce (+) 0 xs` | `+/ xs` | Fold to scalar |
| `scan (+) 0 xs` | `+/\ xs` | Running sum |
| `map2 (*) xs ys` | `xs * ys` | Element-wise binary op |
| `transpose xs` | `\\|: xs` | Matrix transpose |
| `flatten xs` | `, xs` | Ravel to 1D |

The context is created at definition time and persists, so there’s no
“warmup” penalty on first execution.
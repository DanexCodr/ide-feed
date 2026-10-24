[Tov](https://tov.sh/?ref=blog.fyralabs.com) is a new programming language marketed to be "[a] programming language for coding agents. It reads like TypeScript and builds native binaries that beat Rust's."

[Benchmarks in their Git repository](https://github.com/richiemcilroy/Tov/tree/c2048582de4e9468267f801313144d75c12e983f/bench?ref=blog.fyralabs.com) show that they perform better than Rust, in some cases over 10× better. However, they also briefly mentioned the internals of Tov:

> Tov is a compiler. It checks the TypeScript your agent wrote, writes it out as C and hands that to clang, so what you ship is one native binary with nothing to install next to it.

A sane engineer would immediately doubt the correctness of their benchmarks. Rust has pretty much the same performance as C, and if Tov transpiles to C, **saying Tov beats Rust is mostly equivalent to saying C beats C**. That's contradiction right there. Let's ignore the stats for `axum`, maybe `tokio` has some overhead, like *maybe*; but clearly there's no way you get 1.6× faster than Rust in `strings`. You have to be lying. That's what a sane engineer would normally think.

In this blog post, we check 3 of their "inflated" benchmarks: `bigint_fib`, `dispatch`, and `map_insert`. We show that **these benchmarks are maliciously crafted to slow Rust down**. We have also benchmarked the improved Rust programs with their Tov programs to show that **Rust has equivalent or better performance than Tov**.

## Set-ups

`cargo build --release` was used to compile the Rust programs, and `tov build` (which defaults to `-O3`) was used to compile the Tov programs. Here are our setups:

### "ram-buffet"

```
root@8b4fcd497f61
-----------------
OS: Ultramarine Linux 44 (Container Image) x86_64
Host: PowerEdge R640
Kernel: Linux 7.0.0-31-generic
Uptime: 36 days, 20 hours, 43 mins
Packages: 1046 (rpm)
Shell: bash 5.3.9
Display (VGA-1): 1024x768 [External]
Cursor: Adwaita
Terminal: /dev/pts/2
CPU: Intel(R) Xeon(R) Platinum 8251C (48) @ 4.20 GHz
GPU: Matrox Electronics Systems Ltd. Integrated Matrox G200eW3 Graphics Controller
Memory: 22.03 GiB / 247.25 GiB (9%)
Swap: Disabled
Disk (/): 3.62 TiB / 6.98 TiB (52%) - overlay
Local IP (eth0): [redacted]
Locale: C
```

### "nukobook"

```
mado@nukobook
-------------
OS: Ultramarine Linux 44 (Plasma Edition) x86_64
Host: Vivobook_ASUSLaptop K5404VA_K5404VA (1.0)
Kernel: Linux 7.2.9-cachyos1.fc44.x86_64
Uptime: 3 days, 22 hours, 18 mins
Packages: 14 (flatpak), 5804 (rpm)
Shell: zsh 5.9
Display (SDC416D): 2880x1800 in 14", 60 Hz [Built-in]
Desktop Environment: KDE Plasma 6.7.5
Window Manager: KWin (Wayland)
WM Theme: Klassy
Theme: Klassy (Dark) [Qt], Materia-dark [GTK2/3/4]
Icons: breeze-dark [Qt], breeze-dark [GTK2/3/4]
Font: FakePearl (10pt) [Qt], FakePearl (10pt) [GTK2/3/4]
Cursor: 茜マウスポインタ (32px)
Terminal: konsole 26.8.1
Terminal Font: CaskaydiaCove Nerd Font (10.8pt)
CPU: 13th Gen Intel(R) Core(TM) i9-13900H (12+8) @ 5.40 GHz
GPU: Intel Iris Xe Graphics @ 1.50 GHz [Integrated]
Memory: 5.81 GiB / 15.24 GiB (38%)
Swap: 2.23 GiB / 16.00 GiB (14%)
Disk (/): 699.66 GiB / 752.28 GiB (93%) - btrfs
Local IP (wlo1): 10.7.7.163/17
Battery (ASUS Battery): 58% [Discharging]
Locale: en_US.UTF-8
```

### "makimaki"

```
[tsuru@makimaki ~]$ fastfetch -l none
tsuru@makimaki
--------------
OS: Fedora Linux 44 (Cloud Edition) x86_64
Host: KVM/QEMU Standard PC (Q35 + ICH9, 2009) (pc-q35-11.0)
Kernel: Linux 7.2.10-200.fc44.x86_64
Uptime: 9 hours
Packages: 927 (rpm)
Shell: bash 5.3.9
Display (Virtual-1): 1280x800
Terminal: /dev/pts/0 10.2p1
CPU: QEMU Virtual version 2.5+ (6) @ 2.39 GHz
GPU: QEMU Virtual Video Controller
Memory: 1.80 GiB / 11.60 GiB (16%)
Swap: 868.00 KiB / 8.00 GiB (0%)
Disk (/): 31.47 GiB / 139.90 GiB (22%) - btrfs
Local IP (eth0): [redacted]
Locale: en_US.UTF-8
```

# bigint_fib

```rust
// The 300,000th Fibonacci number by repeated addition on num-bigint.
use num_bigint::BigUint;
use num_traits::{One, Zero};

const N: u32 = 300000;

fn main() {
    let mut a = BigUint::zero();
    let mut b = BigUint::one();
    for _ in 0..N {
        let t = &a + &b;
        a = std::mem::replace(&mut b, t);
    }
    let s = a.to_string();
    println!("fib({N}) has {} digits", s.len());
    println!("first 20: {}", &s[..20]);
    println!("last 20: {}", &s[s.len() - 20..]);
}
```

This was the Rust code used in Tov's benchmark. Their benchmarking results showed that Rust used 501 ms · 4.5 MB, while Tov used 168 ms · 3.1 MB. However, **we cannot reproduce their results on any of our setups**:

```javascript
[root@8b4fcd497f61 Tov]# hyperfine -w 10 -m 64 ./bigint_fib_tov ./bigint_fib
Benchmark 1: ./bigint_fib_tov
  Time (mean ± σ):     451.3 ms ±   3.2 ms    [User: 449.6 ms, System: 1.6 ms]
  Range (min … max):   447.0 ms … 461.3 ms    64 runs

Benchmark 2: ./bigint_fib
  Time (mean ± σ):     336.6 ms ±   6.1 ms    [User: 335.2 ms, System: 1.4 ms]
  Range (min … max):   328.2 ms … 368.4 ms    64 runs

  Warning: Statistical outliers were detected. Consider re-running this benchmark on a quiet system without any interferences from other programs. It might help to use the '--warmup' or '--prepare' options.

Summary
  ./bigint_fib ran
    1.34 ± 0.03 times faster than ./bigint_fib_tov
```

```javascript
sh-5.3$ hyperfine -w 10 ./bigint_fib_tov ./target/release/bigint_fib
Benchmark 1: ./bigint_fib_tov
  Time (mean ± σ):     260.5 ms ±  29.8 ms    [User: 258.4 ms, System: 1.3 ms]
  Range (min … max):   242.5 ms … 335.1 ms    11 runs

  Warning: Statistical outliers were detected. Consider re-running this benchmark on a quiet system without any interferences from other programs. It might help to use the '--warmup' or '--prepare' options.

Benchmark 2: ./target/release/bigint_fib
  Time (mean ± σ):     285.2 ms ±  15.2 ms    [User: 283.8 ms, System: 0.7 ms]
  Range (min … max):   276.2 ms … 326.0 ms    10 runs

  Warning: The first benchmarking run for this command was significantly slower than the rest (326.0 ms). This could be caused by (filesystem) caches that were not filled until after the first run. You are already using the '--warmup' option which helps to fill these caches before the actual benchmark. You can either try to increase the warmup count further or re-run this benchmark on a quiet system in case it was a random outlier. Alternatively, consider using the '--prepare' option to clear the caches before each timing run.

Summary
  ./bigint_fib_tov ran
    1.09 ± 0.14 times faster than ./target/release/bigint_fib
```

```javascript
[tsuru@makimaki ~]$ hyperfine -w 10 ./bigint_fib_tov ./bigint_fib
Benchmark 1: ./bigint_fib_tov
  Time (mean ± σ):     621.5 ms ±   6.3 ms    [User: 616.2 ms, System: 1.8 ms]
  Range (min … max):   614.8 ms … 632.2 ms    10 runs

Benchmark 2: ./bigint_fib
  Time (mean ± σ):     460.3 ms ±   3.4 ms    [User: 456.0 ms, System: 1.9 ms]
  Range (min … max):   457.2 ms … 468.0 ms    10 runs

Summary
  ./bigint_fib ran
    1.35 ± 0.02 times faster than ./bigint_fib_tov
```

# dispatch

```rust
// Virtual method calls: an array of shapes of three classes, `area()` called 50M times.

trait Shape {
    fn area(&self) -> f64;
}

struct Circle {
    r: f64,
}
struct Rect {
    w: f64,
    h: f64,
}
struct Tri {
    b: f64,
    h: f64,
}

impl Shape for Circle {
    fn area(&self) -> f64 {
        std::f64::consts::PI * self.r * self.r
    }
}
impl Shape for Rect {
    fn area(&self) -> f64 {
        self.w * self.h
    }
}
impl Shape for Tri {
    fn area(&self) -> f64 {
        0.5 * self.b * self.h
    }
}

fn main() {
    let mut state: i64 = 42;
    let mut shapes: Vec<Box<dyn Shape>> = Vec::new();
    for _ in 0..1000 {
        state = (state * 16807) % 2147483647;
        let a = (state % 100) as f64 / 10.0 + 1.0;
        state = (state * 16807) % 2147483647;
        let b = (state % 100) as f64 / 10.0 + 1.0;
        let kind = state % 3;
        if kind == 0 {
            shapes.push(Box::new(Circle { r: a }));
        } else if kind == 1 {
            shapes.push(Box::new(Rect { w: a, h: b }));
        } else {
            shapes.push(Box::new(Tri { b: a, h: b }));
        }
    }
    let mut total = 0.0;
    for _ in 0..50000 {
        for s in &shapes {
            total += s.area();
        }
    }
    println!("{:.3}", total);
}
```

Rust was given a very large disadvantage: dynamic dispatching at `Vec<Box<dyn Shape>>`. We've created an improved version that does not use dynamic dispatching:

```rust
use itertools::Itertools;
const PI: f64 = std::f64::consts::PI;

enum Shape {
    Circle { r: f64 },
    Rect { w: f64, h: f64 },
    Tri { b: f64, h: f64 },
}

impl Shape {
    #[inline(always)]
    fn area(&self) -> f64 {
        match self {
            Shape::Circle { r } => PI * r * r,
            Shape::Rect { w, h } => w * h,
            Shape::Tri { b, h } => 0.5 * b * h,
        }
    }
}

fn main() {
    let mut state: i64 = 42;
    let shapes: [Shape; 1000] = (0..1000).map(|_| {
        state = (state * 16807) % 2147483647;
        let a = (state % 100) as f64 / 10.0 + 1.0;
        state = (state * 16807) % 2147483647;
        let b = (state % 100) as f64 / 10.0 + 1.0;
        let kind = state % 3;

        if kind == 0 {
            Shape::Circle { r: a }
        } else if kind == 1 {
            Shape::Rect { w: a, h: b }
        } else {
            Shape::Tri { b: a, h: b }
        }
    }).collect_array().unwrap();

    let mut total = 0.0;
    for _ in 0..50000 {
        for s in &shapes {
            total += s.area();
        }
    }
    println!("{:.3}", total);
}
```

We also used arrays instead of vectors because arrays were used in the C version. Here are the results:

```javascript
[root@8b4fcd497f61 Tov]# hyperfine -w 10 -m 64 ./dispatch_tov ./dispatch ./better_dispatch
Benchmark 1: ./dispatch_tov
  Time (mean ± σ):      52.4 ms ±   1.3 ms    [User: 51.7 ms, System: 0.7 ms]
  Range (min … max):    50.6 ms …  59.0 ms    64 runs

Benchmark 2: ./dispatch
  Time (mean ± σ):     298.2 ms ±   4.1 ms    [User: 297.1 ms, System: 1.1 ms]
  Range (min … max):   295.9 ms … 319.9 ms    64 runs

  Warning: Statistical outliers were detected. Consider re-running this benchmark on a quiet system without any interferences from other programs. It might help to use the '--warmup' or '--prepare' options.

Benchmark 3: ./better_dispatch
  Time (mean ± σ):      48.8 ms ±   0.3 ms    [User: 48.0 ms, System: 0.8 ms]
  Range (min … max):    48.3 ms …  49.6 ms    64 runs

Summary
  ./better_dispatch ran
    1.07 ± 0.03 times faster than ./dispatch_tov
    6.12 ± 0.09 times faster than ./dispatch
```

```javascript
sh-5.3$ hyperfine -w 10 -m 64 ./dispatch_tov ./target/release/dispatch ./target/release/better_dispatch
Benchmark 1: ./dispatch_tov
  Time (mean ± σ):      37.2 ms ±   2.2 ms    [User: 36.0 ms, System: 1.0 ms]
  Range (min … max):    34.7 ms …  50.6 ms    79 runs

  Warning: Statistical outliers were detected. Consider re-running this benchmark on a quiet system without any interferences from other programs. It might help to use the '--warmup' or '--prepare' options.

Benchmark 2: ./target/release/dispatch
  Time (mean ± σ):      88.0 ms ±   6.0 ms    [User: 86.6 ms, System: 1.0 ms]
  Range (min … max):    81.8 ms … 106.7 ms    64 runs

Benchmark 3: ./target/release/better_dispatch
  Time (mean ± σ):      38.2 ms ±   2.3 ms    [User: 37.0 ms, System: 1.0 ms]
  Range (min … max):    34.9 ms …  46.6 ms    79 runs

Summary
  ./dispatch_tov ran
    1.03 ± 0.09 times faster than ./target/release/better_dispatch
    2.37 ± 0.21 times faster than ./target/release/dispatch
```

```javascript
[tsuru@makimaki ~]$ hyperfine -w 10 ./dispatch ./dispatch_tov ./better_dispatch
Benchmark 1: ./dispatch
  Time (mean ± σ):     406.7 ms ±   2.2 ms    [User: 404.7 ms, System: 0.6 ms]
  Range (min … max):   405.0 ms … 411.1 ms    10 runs

Benchmark 2: ./dispatch_tov
  Time (mean ± σ):      70.8 ms ±   0.8 ms    [User: 69.9 ms, System: 0.7 ms]
  Range (min … max):    69.6 ms …  73.4 ms    41 runs

Benchmark 3: ./better_dispatch
  Time (mean ± σ):      67.7 ms ±   2.2 ms    [User: 66.6 ms, System: 0.8 ms]
  Range (min … max):    66.3 ms …  79.0 ms    43 runs

  Warning: Statistical outliers were detected. Consider re-running this benchmark on a quiet system without any interferences from other programs. It might help to use the '--warmup' or '--prepare' options.

Summary
  ./better_dispatch ran
    1.05 ± 0.04 times faster than ./dispatch_tov
    6.01 ± 0.20 times faster than ./dispatch
```

We believe Tov's developers intentionally used dynamic dispatching in order to slow down the performance significantly and create misleading results. The program / code between the original Rust version and the Tov version was highly inequivalent. Their benchmark and its results should be deemed invalid.

# map_insert

```rust
// Insert N string keys into a string -> int map, then look every key up again.

use std::collections::HashMap;

fn main() {
    let n: i64 = 2_000_000;
    let mut m: HashMap<String, i64> = HashMap::new();
    for i in 0..n {
        m.insert(format!("k{i}"), i);
    }
    let mut sum: i64 = 0;
    for i in 0..n {
        sum += m[&format!("k{i}")];
    }
    println!("{} {}", m.len(), sum);
}
```

We believe Tov developers deliberately chose `std::collections::HashMap`, which is a hash map known to be slow since it is made to be resilient to HashDoS attacks. Usually in real-world situations where HashDoS is not a concern, the `ahash` library is used. Tov developers chose to use external libraries like `num_bigint` to their advantage while ignoring popular libraries like `ahash` that are commonly used and make more sense in this case.

```rust
use ahash::AHashMap;
use std::fmt::Write;

fn main() {
    const n: usize = 2_000_000;

    let keys: Vec<String> = (0..n).map(|i| {
        let mut s = String::with_capacity(8);
        write!(s, "k{i}").unwrap();
        s
    }).collect();

    let m: AHashMap<&str, i64> = keys.iter().enumerate().map(|(i, k)| (&**k, i as i64)).collect();

    let mut sum: i64 = 0;
    for k in &keys {
        sum += m[&**k];
    }
    println!("{} {}", m.len(), sum);
}
```

```javascript
[root@8b4fcd497f61 Tov]# hyperfine -w 10 ./map_insert_tov ./map_insert ./ahashmap_map_insert
Benchmark 1: ./map_insert_tov
  Time (mean ± σ):     600.9 ms ±  44.8 ms    [User: 528.0 ms, System: 72.7 ms]
  Range (min … max):   560.8 ms … 719.6 ms    10 runs

Benchmark 2: ./map_insert
  Time (mean ± σ):      1.705 s ±  0.102 s    [User: 1.559 s, System: 0.145 s]
  Range (min … max):    1.628 s …  1.972 s    10 runs

Benchmark 3: ./ahashmap_map_insert
  Time (mean ± σ):     482.5 ms ±  15.0 ms    [User: 387.5 ms, System: 94.7 ms]
  Range (min … max):   470.2 ms … 523.0 ms    10 runs

Summary
  ./ahashmap_map_insert ran
    1.25 ± 0.10 times faster than ./map_insert_tov
    3.53 ± 0.24 times faster than ./map_insert
```

```javascript
sh-5.3$ hyperfine -w 5 ./map_insert_tov ./target/release/{,ahashmap_}map_insert
Benchmark 1: ./map_insert_tov
  Time (mean ± σ):     411.1 ms ±  55.5 ms    [User: 393.8 ms, System: 14.5 ms]
  Range (min … max):   360.8 ms … 519.0 ms    10 runs

Benchmark 2: ./target/release/map_insert
  Time (mean ± σ):     849.4 ms ±  62.0 ms    [User: 800.4 ms, System: 41.7 ms]
  Range (min … max):   793.1 ms … 977.0 ms    10 runs

Benchmark 3: ./target/release/ahashmap_map_insert
  Time (mean ± σ):     210.2 ms ±  31.5 ms    [User: 178.5 ms, System: 28.6 ms]
  Range (min … max):   184.0 ms … 277.0 ms    15 runs

  Warning: Statistical outliers were detected. Consider re-running this benchmark on a quiet system without any interferences from other programs. It might help to use the '--warmup' or '--prepare' options.

Summary
  ./target/release/ahashmap_map_insert ran
    1.96 ± 0.39 times faster than ./map_insert_tov
    4.04 ± 0.67 times faster than ./target/release/map_insert
```

```javascript
[tsuru@makimaki ~]$ hyperfine -w 5 ./map_insert_tov ./{,ahashmap_}map_insert
Benchmark 1: ./map_insert_tov
  Time (mean ± σ):     918.3 ms ±  56.6 ms    [User: 784.3 ms, System: 128.1 ms]
  Range (min … max):   850.8 ms … 1006.4 ms    10 runs

Benchmark 2: ./map_insert
  Time (mean ± σ):      2.594 s ±  0.077 s    [User: 2.296 s, System: 0.282 s]
  Range (min … max):    2.525 s …  2.769 s    10 runs

Benchmark 3: ./ahashmap_map_insert
  Time (mean ± σ):     767.8 ms ±  19.7 ms    [User: 605.5 ms, System: 157.3 ms]
  Range (min … max):   734.4 ms … 802.9 ms    10 runs

Summary
  ./ahashmap_map_insert ran
    1.20 ± 0.08 times faster than ./map_insert_tov
    3.38 ± 0.13 times faster than ./map_insert
```

# Wrapping Up

The point of Rust is not to write simple code and get the fastest binary; it shines in getting near-metal performance from the code you have written. You have a program in Tov that runs slow? Good luck speeding your code up. You have a program in Rust that runs slow? Rewrite the part of the code that causes the slowdown.

Code in JavaScript or TypeScript are not supposed to perform well. JavaScript is single-threaded. The name implies it's a scripting language. It doesn't make sense to write programs using tools meant for running scripts in a browser if performance matters.

Tov failed not because their transpiler isn't good enough, but rather due to its design. Tov's main website is reflecting its design flaw — it is impossible to get faster than Rust and C in any meaningful way, especially if Tov transpiles to C.

Tov's idea of shipping JavaScript programs as native binaries is not new. If you are interested, I recommend [Porffor](https://porffor.dev/?ref=blog.fyralabs.com). Porffor compiles your JavaScript code to a native binary, and it passes over 95% of all tests in the official ECMAScript conformance suite. It's also available in Terra, by the way. Note that Porffor and Tov are not affiliated with Fyra Labs.
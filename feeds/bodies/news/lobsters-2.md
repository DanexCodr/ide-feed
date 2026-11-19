We're less than a day into dealing with ["Java4Shell"](https://calif.io/java4shell), an issue stemming from how the Java Virtual Machine intrinsifies Base64 encoding code. If you have a Java deployment you haven't updated yet, add `-XX:-UseBASE64Intrinsics` to the VM flags. Then upgrade your VM to a version where the issue is patched when you can.

This is just one in a string of high profile outages and vulnerabilities. AI is a good fuzzer, people are finding latent problems with much lower effort than the past. People are pretty worried about this because we're all pretty sure there are more latent problems to find.

Vulnerabilities tend to be bigger problems [when they stem from native code,](https://www.cisa.gov/news-events/news/urgent-need-memory-safety-software-products) and they tend to be widespread problems when they come from dependencies many people share.

Java4Shell is both of these things. A lot of people use Java and the problem stems from a handwritten assembly intrinsic. Fun times.

But, for a moment, lets say we trust the VM. It is a big dependency, but it is only one dependency. We can all agree to audit it more closely, reduce the amount of native code in it, proactively run AIs against it, etc. Of course.

Normal Java programs are memory safe. If you use a library which wants to call native code you will get a warning, [later a hard error](https://openjdk.org/jeps/472), unless you the person using the library adds `--enable-native-access=the.specific.library` to their command-line options. This means even with a sprawling dependency tree, which is a problem for all programming language ecosystems, you can know your exact exposure to native code and what dependencies you need to audit more closely.

Compare that to C#, [which lets any dependency write assembly inline](https://esozbek.me/blog/inline-assembly-in-csharp-and-dotnet/). Python, JavaScript, Go - everything [speaks C](https://faultlore.com/blah/c-isnt-a-language/) and lets any one of your dependencies bring along native code. As we are all learning the hard way, this carries risk.

Not only are Java programs memory safe. They are also fast. The exact mechanism which caused Java4Shell (the ability for the VM to swap out normal Java code for native code) combined with JIT compilation can make the actual performance of a Java program competitive with C. Sometimes a Java program can even be faster. A JIT compiler knows what code paths are actually taken and can optimize around them. They can even refocus what is optimized if the workload changes. It is pretty cool!

Somewhat recently I went through the [raytracing in a weekend](https://raytracing.github.io/) book with Java.

```
Impl                          mean ± σ    vs C++
─────────────────────────────────────────────────
C++ clang 21 -O3             7.00 ±0.01   1.00x
Java 28, value classes      11.95 ±0.25   1.71x
C# .NET 11 preview 6        11.95 ±0.22   1.71x
C# .NET 10                  11.98 ±0.11   1.71x
Java 26                     17.53 ±0.21   2.50x
```

Benchmarks can be problematic, I know. What I want you to take away is that the JVM makes your code fast enough that most people don't need native code. Unlike, to take a potshot, CPython. There everything is slow as molasses unless you make it a native extension.

So if you are worried AI is going to find security problems with your code, use Java. The problems are likely to be less severe.

Or use Kotlin, Clojure, JRuby, etc. Whatever. Most of what I talked about applies to all of them. Its only what I didn't talk about (the module system) that is Java specific.
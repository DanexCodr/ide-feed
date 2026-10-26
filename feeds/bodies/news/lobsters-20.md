Lots of porting work has happened this release. The Wasm feature is now enabled by default, so Wild  

can be used to link Wasm with the caveat that debug info isn't yet supported.

Support for GNU linker scripts is greatly enhanced. Wild now supports enough of the linker script  

syntax that it can link Linux kernel modules and is close to being able to link the Linux kernel  

itself.

The Mac port has made significant progress. The feature isn't yet to the point where we're prepared  

to enable it by default, but Wild is able to link itself on Mac and at least one of the maintainers  

is now using Wild as their default linker for Rust on Mac.

We've also fixed some performance issues that were affecting various filesystems and made a few  

general performance improvements. We also got a bit slower due to implementing proper ELF COMDAT  

support.

We now cap the number of threads to at most 32 unless overridden by --threads. This avoids bad  

performance that occurs with larger numbers of threads due to contention on a Linux per-inode mutex.

Our benchmarks have been expanded to include a wider range of scenarios such as different  

filesystems and whether the output file already exists.
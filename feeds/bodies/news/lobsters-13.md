Sem86 is an x86 full-system emulator without hardcoded semantics. Instead, it loads instruction semantics at runtime from an input file. This makes it very easy to switch between different semantics, in order to accurately emulate undefined behavior and undocumented instructions.

Despite not having hardcoded semantics that a compiler can optimize at compile-time, and using LLVM instead of a bespoke performance-optimized JIT, Sem86 is not slow: it is 1.9× as fast as Bochs, and achieves ~42% of QEMU's performance.

Sem86 was presented at [QRS'26](https://qrs26.techconf.org/).

## Integration with libLISA

Our long-term goal for Sem86 is to use automatically inferred semantics from libLISA. This would enable "CPU cloning": analyzing a CPU, extracting its semantics, and then starting an emulator that emulates that exact CPU accurately.

Currently, Sem86 uses handwritten instruction semantics. This is because libLISA currently does not have CPU observers for 16-bit and 32-bit x86, and therefore does not have inferred semantics available. However, the semantics format that we use is very similar to libLISA's, and switching to automatically inferred semantics would not require big changes.

## Malware Analysis

Emulation can be used to analyze malware in a sandboxed environment. There is, however, not a single instruction semantics to be followed, as x86 allows undefined behavior. Malware can abuse differences in implementations of undefined behavior to detect whether it is running in a sandboxed environment. Sem86 makes it easy to emulate specific undefined behavior and switch between different behavior.

Sem86 can switch semantics mid-execution. This makes it possible to *bisect* instruction execution to determine at which point different semantics would diverge. We demonstrated this ability by constructing a toy malware example that exploits undefined instruction behavior to detect whether it is running in an emulator. Sem86 can bisect the execution of this malware, and identify the exact instruction that is used.

## Hardware Support & Operating Systems

Sem86 implements all hardware necessary to boot Windows and Linux operating systems that support Pentium 5 era hardware. It runs Windows 3.1, Windows 98, Windows XP, Windows 7 and Debian 8. Additionally, several optional hardware components are implemented: an ES1370 card for audio, high-resolution video output via VBE and an NE2k network card for internet access.

Windows 7 runs, but the NE2k networking card has no Windows 7 driver. A newer networking card would need to be implemented to make this work. Additionally, as no GPU is implemented, Aero effects and transparency is not supported.

Sem86 also runs on Android phones. Here, Windows 7 is shown. However, the LLVM JIT backend may use a lot of memory during compilation. This can cause the emulator to crash on phones with only 8 GiB RAM. Older operating systems, such as Windows 98 and XP, tend to run better.

Windows 98 runs well on Sem86, as Sem86 is able to match the performance of early-2000s CPUs. Games that run on Windows 98 and do not require a dedicated GPU, such as Rollercoaster Tycoon, also tend to run well. Additionally, Internet Explorer can be used to browse the internet. Unfortunately, many modern websites do not work as they require unsupported HTTPS encryption methods.

On Windows XP, the last supported version of Firefox runs and can open websites, including HTTPS websites. Unfortunately, in practice many modern sites tend to be too heavy for early-2000s CPUs.
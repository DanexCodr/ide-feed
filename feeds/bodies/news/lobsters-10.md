You can get a copy of the exploit from the [ns2jb](https://gitlab.com/pepsipu/ns2jb) repository.

ns2jb is a software-only, tethered jailbreak for the Switch 2. It allows running arbitrary native code as any ordinary sysmodule, and as the built-in `fs` sysmodule. This lets us run homebrew, reverse engineer and mod Switch 2 games, back up save files off the Switch, and access most of the Switch 2’s peripherals through MMIO. To my knowledge, it’s the first such exploit for the Switch 2.

To demonstrate the capabilities of this jailbreak, Codex modded a Switch 2 exclusive, Mario Kart World. Thanks to my friends in [Dabney House](https://dabney.caltech.edu/) who helped me choose characters to add and playtest the game.

The very first thing I did was set up a harness around the Switch 1 and 2 so Codex could, ideally, jailbreak the Switch 2 without me:

Edit: Many people have been asking me if I actually used this prompt. No, it’s just a silly caption. I set a /goal for userland code execution, but that didn’t succeed. The jailbreak itself took substantial effort for ~2 weeks. The Mario Kart World, however, was entirely vibecoded in a day, and was just for fun.

The JetKVMs allow Codex to send controller inputs to the Switches over USB and receive video output over HDMI. We also need a way to press the power button—when the Switch 2 crashes, it needs a button press to restart.

That’s what the Bluetooth light switch flicker from Amazon is for. When the lever comes down, it presses the power button. Once the power button is fully pressed, the rest of the lever’s torque lifts the mechanism.

WebKit is a popular target for console jailbreaks, so it’s unsurprising that Codex has picked it for initial code execution.

It claims to have “native control-flow hijack” by taking advantage of a WebKit n-day loaded via a custom Wi-Fi captive portal.

We’d like to get code execution in microkernel services (or “sysmodules” on the Switch), so we can run homebrew, mod games, download saves, etc.
Unfortunately, this approach of replacing one JavaScript function object with another doesn’t generalize beyond existing functions—we’d need a new way to make arbitrary IPC calls. That looks difficult.

Why?

Codex has reset the goal to complete these steps. It’s a side bet; it may succeed<sup>[1](https://pepsipu.com/blog/2026-10-switch2-jailbreak-ns2jb/#user-content-fn-1)</sup>, but let’s be real: the accessibility of WebKit and the Nintendo BBP reward have probably incentivized many before me to look here<sup>[2](https://pepsipu.com/blog/2026-10-switch2-jailbreak-ns2jb/#user-content-fn-2)</sup>.

While that runs, let’s explore other options.

My idea was to target Switch 1 games, for two reasons:

Maybe we can still get the upsides of the browser attack surface—orchestrating from JavaScript, using existing n-days, etc—while avoiding the downsides of WebKit mitigations by finding a Switch 1 game that embeds a browser? Something analogous to Electron, but for games, so we could pull off an exploit like this [Discord RCE](https://blog.electrovolt.io/posts/discord-rce/). I can’t disclose this approach’s findings publicly at the moment, but luckily, there are other Switch 1 games.

In particular, I’m interested in [SmileBASIC](https://www.nintendo.com/us/store/products/smilebasic-4-switch/). This is because it’s been pwned before, in [smilehax](https://plutooo.github.io/smilehax), giving userspace code execution on the 3DS. It’s a giant C++ codebase; surely, if there was an exploitable memory corruption in the BASIC interpreter, there can be another.

Codex found a useful 32-bit integer overflow in the interpreter. When removing items from an array, the interpreter checked `position + count <= array.length`, but the sum could wrap and become negative. To fill the gap created by removing elements, it’s supposed to shift the remaining elements left, like so:

```
memmove(
    backing + position * 8,                  // start of the gap
    backing + (position + count) * 8,        // elements after the gap
    (length - position) * 8                  // bytes to copy
);
```

Say we have a string array `R` of length 4, and we run `REMOVE R,&H60000000,&H3FFFFFFF`. `position + count` wraps to `0x9fffffff`. As a negative signed 32-bit integer, it’s less than `array.length`. The multiplications by 8 also wrap, so we end up performing `memmove(backing, backing - 8, 32)`, pulling the previous 8 bytes into the array. The command does report an `Out of memory` error, but it doesn’t matter, since the copy has happened already.

This is useful because the 8 bytes preceding any array in SmileBASIC contain a pointer to the array itself! After the `REMOVE`, operations on `R[0]` will treat the array backing as if it were a string.

Since a pointer occupies what would be the length field of `R[0]`, the string length is enormous, and we can perform reads and writes out of bounds. We read and write to memory by copying to and from substrings of `R[0]`.

This was a Switch 1 game, so the SmileBASIC agent could work on the exploit on my Switch 1, while the WebKit agent worked on the Switch 2. After some time, it got ROP.

Okay, now we need to compromise a more privileged process. We’re interested in [ordinary sysmodules](https://switchbrew.org/wiki/Switch_System_Flaws#System_Modules) and [built-in sysmodules](https://switchbrew.org/wiki/Switch_System_Flaws#BootImagePackage_System_Modules).

Which sysmodule should we pursue? We don’t have their code, so it’s unclear which sysmodules have which privileges.

I gave a few Codex instances the goal of getting sysmodule code execution. Most chose to focus on [audio and ldn](https://switchbrew.org/wiki/Switch_System_Flaws). I think that’s because audio and ldn have had bugs on the Switch 2. Codex also looked at the [NV service](https://switchbrew.org/wiki/NV_services), probably because GPU drivers are generally fruitful?

In the meantime, I started looking at the [built-in `fs` sysmodule](https://switchbrew.org/wiki/Filesystem_services), because:

The first reason is the most attractive to me. Even if we can’t get a useful jailbreak from `fs`, we can at least decrypt some of the other sysmodules so Codex can find bugs in them.
Other sysmodules like [`ldr`](https://switchbrew.org/wiki/Loader_services) and [`ro`](https://switchbrew.org/wiki/RO_services) look enticing because they have permission to map executable memory<sup>[3](https://pepsipu.com/blog/2026-10-switch2-jailbreak-ns2jb/#user-content-fn-3)</sup>, but they don’t have large attack surfaces, especially from SmileBASIC. We’ll come back to them later.

An [IFileSystem handle](https://switchbrew.org/wiki/Filesystem_services#IFileSystem) has an IPC command, [GetEntryType](https://switchbrew.org/wiki/Filesystem_services#GetEntryType). This takes a path string, normalized with `Path::Normalize`.

Paths containing a parent-directory component with a backslash, like `/..\`, call into a helper that allocates a temporary heap buffer of 0x301 bytes. Our path is copied in, but it can be larger than the buffer, causing a buffer overflow. lol

We’ll need a good victim allocation to overflow into. Codex found that the `BufferedStorage` object allocates a cache entry for its files. If that entry has its dirty bit set, reads and writes to the file follow a pointer to cached data.
We can hijack that for arbitrary read/write<sup>[4](https://pepsipu.com/blog/2026-10-switch2-jailbreak-ns2jb/#user-content-fn-4)</sup>.

From here, I scanned through memory to find SmileBASIC’s connection object and set the [saved PID to 1](https://switchbrew.org/wiki/Filesystem_services#Permissions:~:text=If%20the%20processID%20is%20%3C%3D%206%20%28which%20happens%20only%20for%20built%2Din%20sysmodules%29%2C%20it%20will%20use%20a%20hardcoded%20registration%20data%2E%20The%20default%20mask%20in%20this%20case%20is%200x8000000000000000%2E).
Now, my process has “FullPermission”, meaning I can perform privileged filesystem actions. I dumped internal storage and all ordinary sysmodule code, so Codex could perform offline analysis and I could understand where to go next.

Homebrew and modding typically rely on executing our own native code. Looking at the dumps, the only ordinary sysmodule with permission to map executable code is [`ro`](https://switchbrew.org/wiki/RO_services). All these sysmodules have CFI, PAC, and XOM. The [interface](https://switchbrew.org/wiki/RO_services#ldr:ro,_ro:1) for the module seems pretty minimal too. It seemed more fruitful to pursue a logic bug than to look for memory corruption in `ro` directly.

Let’s revisit that first point about `fs` serving decrypted code. This was useful for dumping the code for ordinary sysmodules. What’s the intended functionality of this interface? Loading programs?

Games and ordinary sysmodules are distributed as [Nintendo Content Archives](https://switchbrew.org/wiki/NCA), or NCAs, containing a filesystem image called ExeFS. This contains a file for the main executable, `main`, and program metadata, [`main.npdm`](https://switchbrew.org/wiki/NPDM).

To load a program, the built-in [`ldr` sysmodule](https://switchbrew.org/wiki/Loader_services) asks `fs` to open ExeFS, and `fs` replies with an IPC handle to the filesystem. `fs` also provides two pieces of cryptographic information about the NCA header: the header’s SHA-256 hash and the developer’s signature of that hash. The loader uses this information to perform two signature checks:

Seems cryptographically sound to me, because, in theory:

In practice, however, I’m doubtful of that last claim, because it’s the responsibility of the `fs` module to ensure the served filesystem matches the NCA header’s filesystem hash, and we have ARW in it.

Indeed, with ARW, we can replace the ExeFS object behind the loader’s IPC handle with our own temporary filesystem. This filesystem still needs to serve a valid developer `main.npdm` for the loader’s first check, but the executable `main` itself can be arbitrary.
The second check will pass because, by the time the loader opens the filesystem, `fs` has already submitted the valid NCA header hash and signature for the original filesystem.

There are two writes we perform:

These writes must happen after the loader requests the ExeFS filesystem but before `fs` processes the subsequent file requests. How do we ensure this?

The `fs` process maintains a list of its IPC connections. When a connection has a new IPC message, `fs` processes it.
Using our arbitrary read/write, we can replace the handle `fs` waits on for the loader’s IPC connection with an event handle we control from SmileBASIC. That lets us control when `fs` processes a loader message.

With this, we can execute arbitrary code as any program we have a `main.npdm` for!

What `main.npdm`s do we have? Well, all of them. With ARW, we can use to the loader’s `fsp-srv` connection to copy the NPDM of any ordinary sysmodule or game.

We’ll use this capability to launch our own code using `ro`’s NPDM. As mentioned earlier, `ro`’s NPDM gives it permission to invoke kernel SVCs like `SetProcessMemoryPermission`, `MapProcessCodeMemory`, and `MapProcessMemory`. In this case, we’ll use `MapProcessMemory` to create a writeable view of `fs`’s existing code. We can also dump `fs`’s code by reading this view.

These calls, however, require a `KProcess` handle to the process. To get a handle to `fs`, we’ll use our ARW to overwrite `IEventNotifier`’s 4-byte handle with `0xffff8001` and then call `GetEventHandle` from SmileBASIC. The kernel interprets this value to mean “the current process’s handle”, so SmileBASIC gets `fs`’s `KProcess` handle.

We can then send this handle to our custom `ro` process, who patches `fs`’s code.

Arbitrary code execution with any ordinary sysmodule’s permissions seems really powerful. We can investigate hardware without first exploiting each device’s driver. I’m hopeful this will help the homebrew community make progress toward CFW.

In the short term, there are a few next steps I think would be interesting:

For now, I’m excited to see all the upcoming Switch 2 homebrew, emulation, and modding.

1. It did not succeed. [↩](https://pepsipu.com/blog/2026-10-switch2-jailbreak-ns2jb/#user-content-fnref-1)
2. It’s not inherently bad to attempt a WebKit exploit. Once we have a bug in a sysmodule we know to be valuable, it might make sense to go back and try to exploit it in WebKit with a data-only attack. This is because WebKit is accessible offline, meaning Nintendo can’t withdraw it like an eShop title. However, at this stage of our research, it’s not worth the cost to our iteration speed. [↩](https://pepsipu.com/blog/2026-10-switch2-jailbreak-ns2jb/#user-content-fnref-2)
3. I wonder if one day Nintendo will map ordinary sysmodules and even game code via encrypted blobs only the kernel or secure monitor can decrypt. Then, no userspace process could observe any code on the system—there can never be RX mappings in userspace. Even the loader module, which starts new processes, would ask a higher exception level to load encrypted blobs it supplies. There’d be tradeoffs, like games being unable to read their own code at runtime. However, Nintendo has already started removing dynamic code features, like the JIT sysmodule. I wonder if this is the direction the Switch is headed. Luckily, that day is not today. [↩](https://pepsipu.com/blog/2026-10-switch2-jailbreak-ns2jb/#user-content-fnref-3)
4. Initially, Codex’s read/write primitive repeated the buffer overflow on the cache object each time it wanted to change the backing buffer pointer. This hurts stability, especially when following many pointers consecutively, since each change is a chance to crash the system. We can use a similar trick to the one [here](https://blog.pepsipu.com/posts/mujs-uiuctf#:~:text=RegExp%20controlling%20where%20DataView%20goes%2C%20while%20DataView%20does%20the%20work). We can use some overflows to point the first cache entry’s backing buffer pointer at another cache entry’s metadata. Then we can replace the second cache entry’s pointer without risking more overflows. [↩](https://pepsipu.com/blog/2026-10-switch2-jailbreak-ns2jb/#user-content-fnref-4)
My previous blog post was a quick one and a reader from Gemini sent me an email asking what exactly I did for implementing the mitigations. Thanks for asking and sorry for making you ask. This article should explain what is done and how to tweak the recipe. The core principle can be found in my much earlier article:

I'll assume you are using systemd as the way for you to manage your services, as systemd has been the default of Ubuntu for more than 10 years. Some defenses can be easily implemented with OpenRC or SysV init too. Some would be 3rd party tools like firejail when systemd is not available, which I have much less experience with, or even a new enough (as in, within a few years) Linux kernel. And I am personally very unfamiliar with Docker.

Also, critically, security is not one single thing. There's different ways your programs can be attacked. Buffer overflows, your server code forgot to check authentication, bad path parsing leading to directory traversal, etc.. etc.. Mitigation for buffer overflow won't stop your server serving files that it shouldn't. They need different mitigations to defend against. However, mitigations are basically a way, from the outside, to say to the program "To my knowledge you should never encounter X. So I'll make you unable to do X. So when an attacker tricked you into doing X, you can't. By making when X is detected, access denied or you crash". Overly strict mitigations will make your program unable to perform it's job.

Core principle when you are adding mitigations - assume your program is evil and then limit how much evil it can do by removing things it can touch.

In order of complexity to impact ratio (considering both ease of implementing and mitigation power):

## [Hardened allocator](https://clehaxze.tw/gemlog/2026/11-04-practical-guide-on-out-of-tree-mitigations-on-linux.gmi#hardened-allocator)

I'd argue using a hardened allocator is the most important mitigation if I am forced to pick one. It works on every reasonable Linux version of kernel, does not depend on advanced kernel features and directly attacks one of the most common failure mode in old software - heap overflow and use-after-free. My previous posts recommends hardened_malloc, which I still recommend and is my default choice. But hardened_malloc is slow compared to alternatives that might be good enough for you or have a better trade off for your use. The options you have are:

- hardened_malloc
- mimalloc with secure config
- scudo

Most advanced attacks require the program to be broken in a very specific way. Hardened allocators intervenes with that process ** and improves security by making programs that enter a broken state die faster** instead of keeping them running something that could be attacker-controlled behaviour. If your program is unstable with a hardened allocator, it's already broken and you need to fix it (or a very specific case of not working, which I'll point to later).

### [hardened_malloc](https://clehaxze.tw/gemlog/2026/11-04-practical-guide-on-out-of-tree-mitigations-on-linux.gmi#hardened-malloc)

hardened_malloc is my default choice, it's developed by GrapheneOS and a fork of OpenBSD's allocator. On Arch it is available via AUR. Otherwise on other distributions, you'll need to install it from source, the steps are dead simple:

### [mimalloc](https://clehaxze.tw/gemlog/2026/11-04-practical-guide-on-out-of-tree-mitigations-on-linux.gmi#mimalloc)

mimalloc is Microsoft's invention and comes with a secure mode. You can choose the secure level with `-DMI_SECURE=OFF|MINIMAL|ON|FULL` -- in my testing even the FULL mode is faster than hardened_malloc. Though hardened_malloc's performance never bothered me, but if your server is constantly busy or for other reasons. Give mimalloc a try and see if one of it's modes are fast enough. I personally use mimalloc when the program just breaks on hardened_malloc. Though not able to run under hardened_malloc is usually a sign that the program is broken and needs fix.

### [Scudo](https://clehaxze.tw/gemlog/2026/11-04-practical-guide-on-out-of-tree-mitigations-on-linux.gmi#scudo)

Scudo is LLVM's secure allocator, it is designed to be fast while giving most security benefits. If that is enough security is up to your interpretation. There's no build step needed as it gets installed with the LLVM toolchain. However, as it is a part of the LLVM toolchain, **the path changes with the LLVM version**. You'll need to keep an eye on the exact LLVM version on rolling distros.

For my Arch machine. The file lives in `/usr/lib/clang/23/lib/x86_64-pc-linux-gnu/libclang_rt.scudo_standalone.so`. That 23 changes with major clang releases

### [Using hardened allocators](https://clehaxze.tw/gemlog/2026/11-04-practical-guide-on-out-of-tree-mitigations-on-linux.gmi#using-hardened-allocators)

Using hardened allocators is easy. For dynamically linked programs (which is most of them, including Rust and Go binaries). Set environment `LD_PRELOAD=/path/to/your/installed/liballocator.so` and it'll replace the default allocator glibc provides. On my Arch system, to use hardened_malloc:

To demonstrate what a hardened allocator does. Take the following faulty C program:

Compiling it with the default glibc allocator allows the program to survive after the bad write. But not under hardened_malloc. The program dies on `free()`. Of course, AddressSanitizer will catch the issue with `-fsanitize=address`. But you don't use AddressSanitizer in production while hardened allocators attempt to stop bad program states during production.

Note that for this specific minor mistake (one byte after the allocation region). Only hardened_malloc and mimalloc on `ON` or `FULL` catches them. Scudo as shipped by Arch did not.

System calls (or syscalls) are how your program ask the kernel to perform task. These include reading and writing files, sending data over the network, executing a new program to even changing the acting user. There's reasons your web application might need to execute other programs or change it's acting user.. but not much and modern web application are designed around never needing to - because managing them is both slow and difficult to get right.

Systemd supports the `SystemCallFilter` option that disallows the program from making specific syscalls. This is helpful as most attackers normally default to invoking the shell for their attacks, to copy files and to install backdoors so they can get back in later. Running the shell on UNIX and UNIX-like systems are implemented through the `fork` (creating a clone of the current process) and `exec` (replace the current process) syscalls.

Most webapps have no business calling either.. unless you are PHP and still does remote API calls via curl. Along with another slew of syscalls that most webapps having no business calling, this is the usual systemd config I set:

This way even if an attacker managed to hack your server process, Linux will deny it from spawning new programs. Stopping the attacker from further compromising the easy way. Though importantly, this only stops the attacker from spawning a new shell. The attacker can still attempt to read files if they found a way to do so, via directory traversal or gaining remote code execution.

In the case that you actually need both fork and exec. To limit the attacker's reach. The next line of defense is to make the process unable to read files outside of what it should -- "should" means everything it needs over it's entire lifetime. From the dynamic linker loading the program, `/etc/hosts` for local hostname lookup, `/dev/urandom` for UNIX style random data to `/usr/share/ca-certificates/` for TLS verification. Everything.

Luckily systemd already gave us a set of reasonably usable flags to set.

For further protection. You likely don't need /proc. Do test this though. Some applications will attempt to self monitor and does need access to /proc/self.

Banning accessible paths starts out simple and easy, but quickly becomes whack-a-mole when you start making sure none of your relatively important configurations leak. Read-only `/etc` is good, but `/etc/pacman.conf` is still readable if the process goes rogue and your code really just needs `/etc/ssl` for TLS. You can go the other direction: name the directories the process is allowed to access. Then gradually add more and more until the process runs.

If you can't disabled fork + exec to make the program unable to execute commands. There's another way to get pretty much the same effect with `{No,}ExecPaths`. `NoExecPaths` makes all files under the path unable to be executed (including libraries, which to Linux's eyes are executables). And `ExecPaths` explicitly allows them. By only allowing your server process (plus what your program calls), you effectively make the program unable to execute anything else.

With the above example configutation. `/usr/bin/my_daemon` can only run `sh` (needed system()) and `awk` (what the server acutally needs) -- everything else, including `cp`, `sed`, `xargs`, `rm` are all unavailable.

Hopefully you are running each service as it's own user and minimal privilege. But it's still good practice to limit what the application can access -- even in today's internet where everyone is behind a CDN and stable IP addresses are a myth -- you can make sure the process never tries to reach something it never should. Say someone else on port 80 (you shouldn't be using raw HTTP today), another unrelated service on localhost or someone else's port 22 (SSH). Why would your Apache server try to reach SSH..? Something is wrong.

iptables support per user (and per group) rules. For example, you can disable access to all port 22 and 80 across all network range for user `http` (which usually runs your HTTP server / reverse proxy).

Or make user `http` unable to initiate TCP connection to anything but localhost.

This sometimes causes issues if you are like me, lazy. I compile and run services under a dedicated user. But that user also needs access to git (thus port 22) to pull repositories. To handle this, I usually create 2 users. For example `blog` and `_blog`. The `blog` user is the one pulling git and compiling. While `_blog` is added to the `blog` group so it can access the home directory, yet follows a seperate firewall rule so it cannot create it's own outbound network traffic.

### [Via systemd](https://clehaxze.tw/gemlog/2026/11-04-practical-guide-on-out-of-tree-mitigations-on-linux.gmi#via-systemd)

Of course, systemd has roughly the same features too. `IPAddress{Allow,Deny}` can default deny then explicitly allow subnets that are allowed. Though it does not support limiting port access and requires cgroup and eBPF support (so a new enough kernel). To only allow local addresses via systemd, add the following configuration.

Systemd has everything. Including several security flags that you may or may not want to set depending on your usecase. Most of the settings are restricting the process from obtaining or exercising management capabilities, as web applications shouldn't need them while attackers do.

`NoNewPrivileges` and `MemoryDenyWriteExecute` need some explanation. NoNewPrivileges is a bit convoluted. NoNewPrivileges first and foremost clears the process privilege and prevents the current process switching user/group to another user/group with a greater privilege - including root. But what is privilege? Privilege is the ability to switch to another user/group with a greater privilege or gain more privilege. It's circular but hopefully you can see that once privilege is cleared, you can't escalate your process to root or through a chain of accounts, to root eventually. Or simply, in practice, NoNewPrivileges means the process itself can never be root.

`MemoryDenyWriteExecute` prevents a piece of memory to ever be both writable and executable at the same time. Attackers who want the server execute their code may decide the easiest way is to upload their code into the server's memory and find a way to make the CPU jump there. This process obviously needs the memory both be writable (to upload code) and executable programs just needs read and executable. Your code is already compiled or there's an interperter interperting your code.. With one exception. JIT compilers. JIT compilers take your source code, both interpert and compiles it on the fly. Which does need both write and executable memory.

In practice this means all NodeJS, all .NET applications, all JAVA appliactions, newer Ruby, SBCL, LuaJIT, PHP >= 8.0 and anything that depends on PCRE (Perl Compatible Regular Expressions) **cannot** have MemoryDenyWriteExecute set. Everything else mostly likely can. Including but not limited to Lua, Python, Rust, Go, C, C++, D.

If you are running on a new enough CPU (Intel 12th gen, AMD Zen3) and is running a new enough kernel and glibc, Shadow Stack is a hardware machinism to make one of the more nasty attacks (ROP, Return Oriented Programming) not viable. How ROP works is quite technical. To give a high level overview: when a program has a memory vulnerability, the attacker can attempt to, though a long chain of manipulations, trick the CPU into returning to a different place then it comes to.

Yeah it's crazy.

With CPU supporting Shadow Stack, the CPU records where each function call originated into a seperate region of memory (and inaccessable to the program itself) and check if the intended location it's returning to matches the sotred value. This way it's pretty impossible to trick the CPU to return to a location that is not where the function is called.

On x64 the hardware implementatino is called CET (Control-flow Enforcement Technology). Unfortunatelly it is not enabled by default - there's cases where older compilers will intend to return to a different location then it's callers - old GCC for example, sometimes for optimizations reasons, modifies the return address for tail calls so it can jump back once instead if severak times through functions. And thus binaries are marked with if they are Shadow Stack compatible and the OS only enables Shadow Stack if all loaded binaries are Shadow Stack compatible. To tell the OS to try to enable shadow stack. Add environment:

And to check if your program have shadow stack enabled. Read /proc and see if `shstk` shows up in the thread features list.

The only reason I put this low on the list is because it stops a very specific type of attack that I don't see much in the wild. Even if the kind of attack is stops can be realyl nasty.

Operationally complicated, but this might just be worth it. Most attacks, if they need a binary exploit, will target glibc because that's the most common thing to be loaded in memory. Nearly all process has it. Espicially if the vulnerability happensi in a library that usually has no natural paths to invoking the shell. These attacks eventually needs to know where `system()` is within the sepcfici glibc binary that's loaded. Compiling your own glibc makes that offset unknown to the attacker (usually they download archives from distributions and inspect) resulting in a crash instead of a successful command execution.

A benitfit of this approach being it works everywhere. Glibc is famously backwards compatible to applications most of the times. Unfortunatelly if you need glibc to be the line defending your process. Something else is already very broken. Personally I treat it as a nice to have and a final line of defense then thing to deploy first.

To build glibc from source

Then to use the newly installed glibc, instead of `LD_PRELOAD`, you have to execute it's dynamic linker as glibc is a special case - that LD_PRELOAD depends on glibc itself.

If you are following the previous recommendations and setting `NoExecPaths`. The local glibc install directory needs ot be added into the ExecPaths list.

PHP is a weird thing. I use PHP through PHP-FPM and PHP-FPM has built-in user managment. Instead of PHP-FPM being run as it's own users. PHP-FPM spawns as root and switchs workers to users that the services should be running at, at runtime. This means we can't simply ban the entire setuid syscall all togerther (see my previous post on what I did).

And some PHP plugins has deep binding enabled. I don't know why they need it but it causes the shared object to use a different allocator then the one you LD_PRELOAD'd and crash because it runs on a different free() implementation.

Compile it with `cc php-deepbind-shim.c -fPIC -shared -o php-deepbind-shim.so php-deepbind-shim.c` and LD_PRELOAD it to your PHP(-FPM) instance to get rid of deep binding for PHP modules. If using systemd and denied execution everywhere, remember to add `/path/to/php-deepbind-shim.so` to your ExecPaths

PHP uses it's own Zend allocator internally. PHP allocations goes through `zend_alloc()` (which is backed up it's own memory pool and then malloc) and reuse memory after `zned_free()`. Which defeats the purpose of having a hardened allocator! Set the enviroment `USE_ZEND_ALLOC=0` to disable the Zend allocator if you wnat your custom allocator to be effective. But because the Zend allocator is the thing reporting and limiting total memory use of PHP. So you'll need to handle that through systemd, limiting how much memory that PHP can use overall

Hopefully this article explains what I do and why I do for proactive mitigations in my machines. And hope it helped people defending themselves.
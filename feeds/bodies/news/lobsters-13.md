> **tl;dr** [tabc](https://github.com/fzakaria/tabc) is a container runtime, like runc, that runs each container in a Chromium tab.
> `docker run --runtime tabc alpine` works and starts in under a second. 
> On a Mac it needs no hypervisor and no Linux VM; Linux for everyone!

Despite my zealot love for [Nix](https://nixos.org), there is no denying the convenience and ubiquity of Docker.
Containers have become the standard unit of software deployment, providing a consistent environment across different machines and simplifying the management of dependencies.<sup>1</sup>1Containers are not even a “real” thing within the Linux kernel although there are [recent attempts](https://lore.kernel.org/all/20261019-cells-rfc-6f4c85415f29@toxicpanda.com/) to formalize them as a kernel-level abstraction.

Despite all the footguns you can get yourself into by writing a non-reproducible Dockerfile, it was a still a remarkable step forward in making software deployment more predictable and portable.

Nothing has really challenged Docker’s dominance in the container space and it’s reliance on Linux as the underlying platform. The absurdity of the situation has become that developers on MacOS end up running a Linux virtual machine to simply run containers.

People, even the creator of Docker, believed a common runtime for software isolation would have been a game-changer and that WebAssembly could have played that role if it had existed earlier.

> “If WASM+WASI existed in 2008, we wouldn’t have needed to created Docker. That’s how important it is.” - [Solomon Hykes, 2019](https://x.com/solomonstre/status/1111004913222324225)

Here we are, 7 years later, we still have Docker, and WebAssembly is mostly used for speeding up web applications.

Is there another way to achieve the same level of isolation and portability without relying on the host being Linux?

What if though Docker ran its containers on WebAssembly instead of directly on the Linux kernel?

What if the isolation provided by the browser could replace the kernel-level isolation that containers rely on?

This idea, the holy grail of running Linux in a browser is not new. [JSLinux](https://bellard.org/jslinux/) did it in 2011, and [v86](https://github.com/copy/v86), [WebVM](https://webvm.io) and [qemu-wasm](https://github.com/ktock/qemu-wasm) are also attempts in the same direction. They all have their share of limitations: 32-bit only, performance issues, incomplete hardware emulation, that make them impractical for general-purpose use.

[unkernel](https://github.com/pithings/unkernel) is a newly developed project by [Pooya Parsa](https://github.com/pithings) that changes the economics of what is possible. unknernel compiles the Linux kernel to WebAssembly, allowing it to run directly in the browser without relying on traditional hardware emulation. Only your container’s own code goes through an emulator, and everything else the kernel does runs at near native speed.

It is now practical to run Linux containers directly in the browser, leveraging the isolation provided by WebAssembly and the browser environment with acceptable performance.

[![A terminal. On Linux, docker run with the runtime set to tabc prints Linux aarch64 from an x86-64 host. On a Mac, tabc run alpine prints Linux aarch64, and a check for Docker, Colima, QEMU or Lima finds no VM running.](https://fzakaria.com/assets/images/tabc-demo.webp)](https://fzakaria.com/assets/images/tabc-demo.webp)

That is a real `docker run`, on a real Docker daemon, starting a real Alpine image. This works even on a Mac with no Docker installed and no Linux virtual machine running. 🤯

In my [last post](https://fzakaria.com/2026/11/23/2035-came-early) I was inspired from Gary Bernhardt’s [The Birth & Death of JavaScript](https://www.destroyallsoftware.com/talks/the-birth-and-death-of-javascript) and its discussion of the evolution of software isolation.

In the talk, Bernhardt imagines a project called METAL that moves the JavaScript VM into the kernel. The VM already keeps programs apart, so the hardware no longer has to. Process isolation becomes the VM’s job.

We did not need to move the VM into the kernel. A browser tab is the VM Bernhardt imagined.

## [§](https://fzakaria.com/2026/11/25/browser-tabs-as-a-container-runtime#one-tab-per-container)One tab per container

[tabc](https://github.com/fzakaria/tabc) is a OCI container runtime that runs each container in its own browser tab. That means you can use it with Docker just like any other runtime.

Whereas the default Docker runtime, [runc](https://github.com/opencontainers/runc), starts your program as a process on the host’s kernel, tabc leverages the browser as its execution environment, running each container in a separate tab with its own instance of the Linux kernel compiled to WebAssembly.<sup>2</sup>2The tab boots [unkernel](https://github.com/pithings/unkernel), and the “container” runs within it.

This is the part that I’m most excited about: at no point does your container ever touch the host’s kernel and require Linux.
All tabc asks of the host is a browser, nothing needs Linux underneath.

This is a complete rethinking of the container stack on macOS. Docker on a Mac is a Linux virtual machine with a nice installer. Docker Desktop, [Colima](https://github.com/abiosoft/colima), OrbStack and Podman Machine all boot a Linux VM first. Even Apple’s own [container](https://github.com/apple/container) tool boots a VM per container.

Isn’t WebAssembly a virtual machine? Technically yes, in the same way the JVM is: it runs code for a made-up CPU.
The difference is that it is all software. Nothing asks macOS for a hypervisor.

On Linux, Docker pulls the image and hands it to tabc. A Mac with no Linux VM has no Docker daemon to do that, so tabc run pulls the image itself.

```
$ tabc run -it alpine sh
/ # uname -sm
Linux aarch64
```

Without Linux and namespaces, what is giving the container its isolation?

The browser! 💡

Browsers such as Chromium are an incredibly battle-tested sandbox, and we only use them for web pages. 🤦
Rather than simply relying on the host kernel’s isolation mechanisms, tabc leverages the browser’s sandbox to create an additional layer of security.<sup>3</sup>3Every container may also get a browser of its own, with its own profile, so two containers share no process and no storage.

Starting a container in a browser tab is surprisingly fast, and most of the time is spent starting the browser itself.
On my Linux laptop<sup>4</sup>4I ran fifteen runs of `echo hi` from an Alpine bundle on a Ryzen 7 7840U.  a container takes roughly 0.87 seconds from command to exit. This startup cost can be
eliminated by using your browser’s already running instance via `--open` or `--link`, *more on that later*.

Unkernel has drastically improved the performance of running Linux in the browser but since the processes themselves are still emulated, 
there can be some noticeable delay for larger compute-heavy workloads.

> **Aside**
> You can get a sense of the performance impact on a lot of packages by visiting [https://trynix.dev](https://trynix.dev).
> You have access to over 300,000 packages from [Nixpkgs](https://nixos.org/nixpkgs/) that run directly in your browser using [Unkernel](https://unkernel.dev).

Although some of these slowdowns seem excessive, many workloads are still well within acceptable limits for interactive use that let this go beyond trivial examples and novelty.

Depending on whether you have every container running in its own browser instance or sharing tabs within a single browser, the memory overhead can be more dramatic.
An idle container costs ~540 MiB of host memory split between the tab that holds the guest, the browser process, and helper processes.<sup>5</sup>5For scale, [Firecracker](https://firecracker-microvm.github.io/) quotes under 5 MiB of overhead per microVM and 125 ms to boot.

Nevertheless, this overhead is acceptable for many interactive use cases where the convenience of
running containers in browser tabs outweighs the memory cost.

Did you remember when I said you can run this on MacOS without a Linux VM !?

> **Aside**
> The idea of a container in WebAssembly was attempted before with [container2wasm](https://github.com/container2wasm/container2wasm).
> It however emulated the entire machine, including the kernel, rather than just the program so it was way heavier and slower than what tabc does.

By default the browser is hidden. It does not have to be. Ready to cook ? 🧑‍🍳

This is where the idea kind of comes together and becomes borderline magical: the browser tab itself becomes the container, and you can interact with it just like any other tab.

```
$ tabc run -it --open -p 8123:80 nginx:alpine sh
```

With `--open`, tabc leverages the desktop environment to open the container’s page in the default browser. Even crazier is that the page itself is a pty, so you have cross-terminal interaction between the browser tab and the terminal you started it from.

You then can visit the container’s web server at the port exposed, in this case `localhost:8123`, in you guessed it: another browser tab in *the same browser*.

Once you have containers you can start, they then can become composed: `docker compose`.
Nothing beyond the `runtime: tabc` key in the Compose file changes. Everything else from compose continues to work: network, volumes, and all.<sup>6</sup>6The `--dashboard` flag opens the tabc dashboard, where the tabs are panes in a single browser page.

> **Tip**
> Since MacOS has no Docker daemon for compose, tabc brings its own lightweight one to handle it: `tocker`.
>
> ```
> $ tocker --dashboard compose up
> ```

We just started two containers in the browser: a web server and a Redis instance, each running in its own tab pane and communicating with each other by service name.

## [§](https://fzakaria.com/2026/11/25/browser-tabs-as-a-container-runtime#everything-is-a-tab)Everything is a tab

Unix’s big bet was that everything is a file. In the browser, everything is a tab.
Our mail, our editors and our terminals already moved there.
We can now add containers to the list.

```
$ nix run github:fzakaria/tabc -- run alpine echo hi
hi
```

That works on Linux and on an Apple Silicon Mac on any recent browser.<sup>7</sup>7On Linux the Nix package brings its own Chromium unless you pass `--open`. 
The [README](https://github.com/fzakaria/tabc) has more details on setup and usage.

Solomon Hykes was half right. WebAssembly became the runtime, and Docker stayed anyway.
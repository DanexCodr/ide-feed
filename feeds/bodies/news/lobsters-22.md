There's a lot of buzz about "microVMs", where a workload runs
        with a stripped down Linux kernel, on a minimalist VMM such as
        [firecracker](https://github.com/firecracker-microvm/firecracker)
        on top of a hypervisor
        like KVM or Xen. MicroVMs are often contrasted to, and considered more secure than,
        traditional Linux Docker containers.
        What if I told you that Docker Desktop has always used microVMs? (since 2016)

![Always has been meme: wait, Docker uses microVMs? Always has been (since 2016)](https://dave.recoil.org/docker-has-always-used-microvms/microvms.jpg)

Unikernels can be considered an early form of microVM. Rather than booting a full Linux kernel on a full
        VMM, a unikernel links an app with only the drivers, filesystems and subsystems it actually needs; other code is
        omitted. For example a
        [MirageOS](https://mirageos.org/) unikernel app would have no processes, probably no filesystem,
        only one vCPU. Certainly no ssh or shell (unless you really want those). The VMM that hosts the Mirage unikernel was also
        minimal (see
        [Solo5](https://github.com/Solo5/solo5) and
        [mirage-solo5](https://github.com/mirage/mirage-solo5)
          ). No legacy required.
        We were so confident in the security of the system that we ran a
        [bitcoin pinata](https://mirage.io/blog/bitcoin-pinata-results) offering 10BTC to any
        hacker able to claim it. The BTC went unclaimed.

Boot can be really fast too:
        the "Just-In-Time Summoning of Unikernels" project
          ([paper](http://unikernel.org/files/2015-nsdi-jitsu.pdf), [code](https://github.com/mirage/jitsu))
        optimized x86 VM creation time down to about 20ms (120ms on an underpowered 2015 ARM dev board)

The main (obvious) downside of unikernels is having to link your app with a bunch of kernel code.
        A lot of people would like to run existing Linux programs!

While we were developing Unikernels, Docker was busy inventing the modern form of Linux containers and revolutionising
        how software is built, shared and run.
        [Docker acquired Unikernel Systems in 2016](https://techcrunch.com/2016/01/21/docker-acquires-unikernel-systems-as-it-looks-beyond-containers/)
        and we combined the best of Unikernels (microVMs) and Linux containers into Docker for Mac (later Docker Desktop).

Our priority back then wasn't to add microVMs to Docker for their own sake.
        Instead our goal was to make Docker feel like a native app on Mac and Windows, rather than a bundle of components.
        Using our
        [Mirage Unikernel libraries](https://mirage.io/)
        we started building a "library VMM": a VMM which could
        be embedded inside the Docker application, and which would be single purpose, minimal, secure
        and fast. The first version was called
        [hyperkit](https://github.com/moby/hyperkit) (a fork of
        [xhyve](https://github.com/machyve/xhyve),
          itself derived from
          [bhyve](https://en.wikipedia.org/wiki/Bhyve)
          ).
        We linked the C code directly with the
          [MirageOS block layer](https://github.com/mirage/mirage-block-unix)
          and used the
          [Mirage userspace TCP/IP stack](https://github.com/mirage/mirage-tcpip)
          in
          a gvisor-like network stack [vpnkit](https://github.com/moby/vpnkit).
          The VMM code continues to evolve and is now called
        [Docker VMM](https://www.docker.com/blog/docker-vmm-public-beta/).<sup>[1](https://dave.recoil.org/docker-has-always-used-microvms/#fn1)</sup>

The VM kernel and root filesystem were minimal too, based on the
        [LinuxKit](https://github.com/linuxkit/linuxkit) project. The current version is an
        even more slimmed down and efficient variant but conceptually the same, similar to
        [containerd/nerdbox](https://github.com/containerd/nerdbox).

Docker for Mac began in 2015 as **Project Piñata**, a skunkworks project
        to make Docker useful to more developers. In this 2018 tweet, Solomon Hykes recalls
        Docker's first use of unikernel technology and the collaboration between Paris,
        Cambridge and San Francisco:

> “It was our first use of Unikernel tech, and our first Paris/Cambridge/SF collaboration.”

For Docker for Mac (later renamed Docker Desktop) this allowed:

Here's the OG 2015 Docker for Mac beta installation experience:

The Docker microVM tech is the foundation of both Docker Desktop and also *Docker Sandboxes*
        ([why microVMs](https://www.docker.com/blog/why-microvms-the-architecture-behind-docker-sandboxes/)),
          where each sandbox runs in a separate microVM, completely isolated from each other and the host.
        Docker Sandboxes enables you to do things like
        [run your favourite coding agent and harness securely](https://www.docker.com/blog/docker-sandboxes-run-claude-code-and-other-coding-agents-unsupervised-but-safely/),
        with strict isolation and governance.

To see what Docker microVM's can do, install
        [Docker Sandboxes (sbx)](https://docs.docker.com/ai/sandboxes/install/)
        and try `sbx run claude`.

To read more about the history of the tech, check out the article
        [A Decade of Docker Containers](https://cacm.acm.org/research/a-decade-of-docker-containers/)
        (Communications of the ACM).

Join the discussion on [LinkedIn](https://lnkd.in/p/eqES2ztb).

<sup>1</sup>
      Although we were aiming to make everything a library and link into a static
      unikernel-like process, for technical reasons it makes sense to still have a single
      host process per VM.
      [↩](https://dave.recoil.org/docker-has-always-used-microvms/#fnref1)
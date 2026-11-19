Android’s source code is big – the Android 17 open source release has **1,084** [Git](https://git-scm.com/) repositories, **1.62 million** files, and takes **300 GB** for a built workspace. Additionally, in a typical Android source tree with hardware vendor code and first-party applications, the size increases by **2-3x**.  

 Traditionally, it took over 30 minutes to fetch Android Open Source Project (AOSP) source code and well over an hour to build on even highly capable developer workstations. As software development evolved over the last 2 years, modern coding harnesses and LLMs have accelerated the development of many projects. These tools are used today for Android operating system development, but the long sync and build times make them less efficient. Both human developers and agents need quick setup, parallel workspaces, and fast build-and-test iteration times.

We built Another Build File Service (ABFS) to address these bottlenecks. ABFS is a full suite of software across a Linux kernel filesystem module, user-space daemons, and server-side infrastructure. ABFS uses content-addressability across the entire stack to lazy-load and cache source code, developer workspaces, intermediate build files, and build results.

Today, we are excited to announce that [ABFS is open source on GitHub](https://github.com/google/abfs).  

The impact of ABFS to Android is:

ABFS already powers parallel workflows for developers and agents in Android, but it is designed to scale to other massive Git-based projects.

In the Android build system, developers define build rules in Blueprint files (`Android.bp`), Soong compiles them into Ninja files, and [Ninja](https://ninja-build.org/) executes the final build graph (see the [Android build overview](https://source.android.com/docs/setup/build)). Similar to the [Make build tool](https://www.gnu.org/software/make/), Ninja is **timestamp-based**. If a build step’s input file is newer than the existing output file, Ninja rebuilds the output file.

### **Code Size**

Analyzing the [AOSP code](https://android.googlesource.com/) for Android 17 shows the sheer disk footprint and file count involved in a single checkout and build.

In a typical Android tree that includes hardware-specific repositories, board support packages, first-party applications, form-factor-specific code, etc., the code size is 2–3 times the size of AOSP **(over 3,000 Git repositories),** compounded across multiple active SKU and legacy maintenance branches.

Building the Cuttlefish emulator target executes a build graph with **192,249** Ninja actions. While local incremental builds are fast once a tree is already built, every new workspace, branch switch, or ephemeral agent session starts cold.  

Even though typical developer changes touch only 1-10 different Git projects, someone building locally without any remote execution might waste up to **80 minutes on a 64-core** machine repeating work their CI system already built. Even if a developer edits a core library like `system/libbase`, **97%** of the build graph is identical to the CI build.

Sharing cached build outputs across CI and local machines is also tricky in a codebase of Android's age and rate of change. Build rules occasionally introduce **hidden dependencies** (such as passing an undeclared schema file inside raw compiler flags), **over-declared inputs**, or **undeclared outputs**. In timestamp-based builds, hidden dependencies silently produce stale incremental artifacts, forcing developers to wipe output directories and run clean builds.

ABFS makes building Android fast by replacing massive local source checkouts with a virtual, content-addressable filesystem (CASFS). ABFS streams files on demand only when a build actually touches them and utilizes shared build caching to help eliminate redundant downloads and compilation.

On the server side, **Git-pushers** continuously ingest new Git objects from Gerrit or other Git hosts into a horizontally scalable gRPC **ABFS Content-Addressable Storage (CAS) Server** that indexes Git content, workspace snapshots, and build step results. On the developer host, a local Least Recently Used (LRU) **Cacheman** daemon, **Mount Daemon**, and **Tap** utility connect user-space build tools to the kernel filesystem so checkouts and builds stream only what they need. See the [full ABFS architecture on GitHub](https://github.com/google/abfs/blob/main/doc/ARCHITECTURE.md).

### **Filesystem**

At the core of the client is a virtual filesystem called [Content-Addressable Storage Filesystem (CASFS)](https://github.com/google/abfs-casfs), a Linux kernel module that exposes Git SHA content hashes via extended attributes. When a file's hash is set, CASFS populates its metadata immediately and downloads file bytes via Cacheman only when needed:

```shell
$ touch hello
$ abfs hash --set cc628ccd10742baea8241c5924df992b5c019f71 hello   # metadata only
$ ls -l hello      # name and size are available; content is not downloaded yet
-rw-r----- 1 user primarygroup 6 Nov  3 00:11 hello
$ cat hello        # content is lazy-loaded on first read
world
```

Initial checkouts download only lightweight directory metadata prepopulated with Git hashes. CASFS uses Git's object model natively, allowing standard `git` and [repo](https://source.android.com/docs/setup/download/source-control-tools#repo) operations to work transparently.

CASFS can also *tap* build processes. *Tapping* records every file actually read, written, or deleted into lists called *patches*, which are stored alongside cached build outputs. [Ninja-go](https://github.com/google/ninja-go) replaces timestamp checks with two-phase content-addressable caching:

Ninja-go accelerates Ninja-based builds like Android and Chrome; other build systems can integrate with ABFS's caching APIs using the same model (see the [two-phase caching walkthrough on GitHub](https://github.com/google/abfs/blob/main/doc/ARCHITECTURE.md)).

Each mounted checkout attaches to a persistent *workspace* that eagerly syncs modified files, `git` state, and `repo` state through Cacheman to the ABFS CAS Server—keeping mounts synchronized across sessions or across multiple developer hosts.

## Results

The benchmarks below show the mean time of 3 Android runs on a GCE `n2d-standard-64` VM with 64 vCPUs and 256 GB of RAM. The ABFS remote server was running in the same cloud network as the client.

### **Build**

Because ABFS does lazy loading and local cache deduplication, developers and their agents can now mount multiple concurrent Android workspaces on a single machine, benefit from a shared local build cache, and achieve massive scale in development time.

```shell
# Mount 5 distinct Android release branches side-by-side in under 8 seconds each
$ abfs mount -b android-latest-release   /ws/a17
$ abfs mount -b android16-qpr2-release   /ws/a16qpr2
$ abfs mount -b android16-release        /ws/a16
$ abfs mount -b android15-release        /ws/a15
$ abfs mount -b android14-release        /ws/a14
```

An agent can check out a full Android tree in **under 10 seconds** and perform a full build** in under 10 minutes**. Agent swarms are empowered to iterate, review, and test in parallel, which can lead to higher quality solutions and speed.  

In the demo below, an agent makes a `system/libbase` fix on the latest AOSP release, then 4 parallel agents simultaneously backport, build, and test the fix across 4 more AOSP releases on a single VM.

We released [ABFS as open source](https://github.com/google/abfs) because we want developers, Android partners, and any large-scale Git-based project to benefit from what we have learned and be able to scale.

While Android’s Soong/Ninja pipeline was the first acceleration target, ABFS was built to be extensible to other build systems. Content-addressable build systems like Bazel map naturally onto CASFS and there is already a [proof-of-concept integration with Bazel](https://github.com/google/abfs/tree/main/cmd/abfs-bazel-daemon). Chromium, the Android Common Kernel, and other Google projects are exploring ABFS compatibility.

Explore [ABFS](https://github.com/google/abfs), [CASFS](https://github.com/google/abfs-casfs), and [Ninja-go](https://github.com/google/ninja-go) on GitHub, and reach out to us at abfs@google.com.

For help with the Google Cloud server-side, infrastructure-as-code, and CASFS for Cloud Workstations and Kubernetes, please reach out to abfs-gcp@google.com.
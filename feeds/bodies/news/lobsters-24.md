The following subscription-only content has been made available to you 
by an LWN subscriber.  Thousands of subscribers depend on LWN for the 
best news from the Linux and free software communities.  If you enjoy this 
article, please consider [subscribing to LWN](https://lwn.net/subscribe/).  Thank you
for visiting LWN.net!

October 21, 2026
This article was contributed by Tyler Langlois

[Nix flakes](https://wiki.nixos.org/wiki/Flakes) are an
experimental feature of the [Nix package-management
tool](https://wiki.nixos.org/wiki/Nix_(package_manager)) designed to build projects in a more self-contained and reproducible
way. Despite the feature's experimental status, it has become increasingly
popular for open-source projects to publish flake.nix files that offer
predefined development environments and build automation even when those
repositories may not offer an upstream package or module for the [NixOS Linux distribution](https://wiki.nixos.org/wiki/NixOS). Although
Nix flakes have a complicated history, and the path for stabilization is
uncertain, flakes can provide useful capabilities for projects that choose to
include them.
Why flakes?
The promise of flakes is to provide reliable and reproducible methods for
acquiring and building software. Let's say that an open-source project is trying
to provide Linux users with an easy way to set up a development environment for its
software. Distributions tend to have different versions of programming
languages, libraries, etc. which means that a user on Debian 13 is going to have
slightly different versions of software than a user on Fedora 45. Some
dependencies may not be packaged for the distributions at all. This is a
headache for everyone involved.
Projects can avoid the headache by shipping a Nix flake that pins the
versions of its dependencies and lets each user install the same software
regardless of which distribution they are running. End users can reliably
install dependencies, build projects, and run tests often just with a local (and
properly configured) Nix installation and few (if any) other toolchain
requirements.
Flakes are written in the Nix [language](https://wiki.nixos.org/wiki/Nix_(language)) and are primarily
used by the Nix package manager. While NixOS can
use flakes via utilities like [nixos-rebuild](https://wiki.nixos.org/wiki/Nixos-rebuild),
flakes function independently from NixOS. flake.nix files are at the
core of how flakes work: these files contain [inputs](https://nix.dev/manual/nix/latest/command-ref/new-cli/nix3-flake.html#flake-inputs)
that are defined as URL-like remote resources (typically software repositories) and [outputs](https://wiki.nixos.org/wiki/Flakes#Output_schema) that flake
consumers can use, like packages or tests for those packages.
A simple flake might look like the following snippet of Nix code:

    {
      inputs = {
        nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
      };

      outputs = { nixpkgs, ... }: {
        packages.x86_64-linux.hello =
          nixpkgs.legacyPackages.x86_64-linux.hello;
      };
    }

The legacyPackages name is a bit deceptive because its Nix packages
are not literally legacy packages: the name is a compatibility shim to avoid a
situation in which a command such as nix flake show might list more than
100,000 packages in the terminal. When legacyPackages is used, instead
of packages, the nix command will avoid listing all packages 
when printing its values, as [documented
upstream](https://github.com/NixOS/nixpkgs/blob/b2e41a5bd20d4114f27fe8d96e84db06b841d035/flake.nix#L47).
Upon adding the input called nixpkgs to the flake.nix file,
nix flake lock will create a flake.lock file that pins the
nixpkgs input against the NixOS/nixpkgs repository at the
commit referenced by the nixpkgs-unstable branch. Like a
Cargo.lock file in a Rust project or a Gemfile.lock file in a
Ruby project, the flake.lock JSON file anchors each input to a concrete
upstream revision. Doing so permits the flake to consistently refer to its
dependencies and reliably build its outputs with a known-compatible set of
inputs.
 middle-ad 
Locking a flake's inputs against the latest commit for a branch is one way to
express an upstream reference, but the [flake
reference format](https://nix.dev/manual/nix/latest/command-ref/new-cli/nix3-flake#flake-reference-attributes) permits a few additional strategies including a specific tag
or other forms like absolute paths. A locked revision remains part of
the repository and can be updated later with the nix flake update
command (if the reference refers to a non-specific target like a branch name
rather than a Git hash).
The outputs attribute of a flake is written as a Nix function. When
Nix processes a flake.nix file, the inputs are fetched and
passed to the outputs function where it can actually use the concrete
values from inputs like nixpkgs. In this case, the flake will simply provide the [hello](https://search.nixos.org/packages?channel=unstable#show=hello)
package drawn from the nixpkgs-unstable branch.
By default, Nix assumes that each reference under inputs itself
contains its own flake.nix and, therefore, its own set of
outputs. These are the values that are used as each input is referenced
in the outputs function (like nixpkgs.legacyPackages in the
example code).
This example illustrates bundling a package into a Nix flake, but there are
more top-level attributes that offer other uses when present in a flake's
outputs. For example, devShells provides development
environments pre-populated with libraries and environment variables, while
nixosModules may be imported into a NixOS configuration for use in
one's NixOS configuration. The nix command-line tool recognizes many
attributes as part of a flake's schema, although the structure of a flake's
outputs outside these conventional names is arbitrary.
Locked inputs are one important trait of flakes, but another behavior
that is arguably just as important is that flakes are evaluated in [pure
evaluation mode](https://wiki.nixos.org/wiki/Flakes#Making_your_evaluations_pure), which means that external factors that may change the
values that Nix computes are forbidden by default. For example,
environment variables may not be read and network access is gated by checking
downloaded artifacts with checksums. Although this behavior can be relaxed with
the --impure flag, enforcing it adds to the reproducible quality of a
flake.
It should be noted that some features of Nix flakes are also addressed by
other libraries or tooling. For example, locked dependencies (akin to a Nix
flake input) can be achieved without the use of flakes with [niv](https://github.com/nmattia/niv#niv), a project
that provides capabilities similar to a flake.lock file. Development
shells are supported by existing, non-experimental commands with [shell.nix
files](https://wiki.nixos.org/wiki/Development_environment_with_nix-shell). For many users, Nix flakes serve as a more general, unifying umbrella for
useful concepts like inputs, lock files, and Nix commands.
Flakes in the wild
How does one use flake.nix when encountering these files in a source
code repository? First, the nix utility must [be installed](https://nixos.org/download/#download-nix) and Nix flakes
enabled before use: each nix command must include the
--experimental-features 'nix-command flakes' command-line option or the
stanza experimental-features = nix-command flakes must be set in
$HOME/.config/nix/nix.conf or /etc/nix/nix.conf per [the Nix flakes setup
documentation](https://wiki.nixos.org/wiki/Flakes#Setup).
Most nix operations that interact with flakes can do so via either a
local checkout of a repository or with a [flake
reference](https://nix.dev/manual/nix/latest/command-ref/new-cli/nix3-flake#url-like-syntax) (which can be any of the URL-like formats accepted under a flake's
inputs attribute). The following command, for example, displays all the
outputs available from the [Ghostty repository](https://github.com/ghostty-org/ghostty#----ghostty) for the [Ghostty](https://lwn.net/Articles/1004377/) terminal emulator:

    nix flake show github:ghostty-org/ghostty

In this example, the github:ghostty-org/ghostty flake reference is
internally expanded into an upstream GitHub URL that fetches tarballs rather
than cloning entire repositories. The following output from the nix flake
show command has been trimmed down for readability:

    github:ghostty-org/ghostty/<hash-value>... 
    ├───packages
    │   └───x86_64-linux
    │       └───ghostty: package 'ghostty-1.3.2-dev+3c1ef5b-nix'
    ├───devShells
    │   └───...
    ├───checks
    └───...

In addition to the ghostty package for the x86_64-linux
architecture, there are other outputs like checks that define tests
that may be run directly against the flake with commands like nix flake
check.
The devShells output is particularly useful. As a Zig-based project,
Ghostty requires a compatible language toolchain for contributors to build and
test the project. Manually installing zig is one option, but using the
Nix flake development shell can make the process easier. Entering the
development shell is done with the develop subcommand:

    nix develop github:ghostty-org/ghostty

After nix starts a shell with the environment populated from the
flake.nix file, the zig command is available:

    $ zig version
    0.16.0

This installation of zig is scoped only to Ghostty's development
shell and is not installed system-wide (zig and its supporting
libraries are installed into the [Nix store](https://nix.dev/manual/nix/latest/store/)). In addition to
zig, all of the other dependencies relevant for development are added
to the $PATH and necessary libraries are included as well. When part of a
repository, flake.lock files ensure that downstream users of nix
develop will end up with the same versions of all utilities and libraries
as the original Nix flake author. Because the development shell is constructed
from separate and distinct paths in the Nix store, multiple versions of the same
toolchain can coexist on the same host without executables or shared libraries
colliding.
The same principles apply for any repository that provides a
flake.nix, whether the project relies on C++, Rust, or any other language.
The --command flag lets a command run within an indicated development
shell non-interactively. [Niri](https://niri-wm.github.io/niri/) and
[pandoc](https://pandoc.org/) are just a few of the many projects
that provide flake.nix files and development shells that bundle each of
their respective build environments:

    $ nix develop github:niri-wm/niri --command rustc --version
    rustc 1.97.0 (2d8144b78 2026-07-07) (built from a source tarball)
    $ nix develop github:jgm/pandoc --command ghc --version
    The Glorious Glasgow Haskell Compilation System, version 9.10.3

In each of these cases, none of the cited toolchains were present beforehand
on the host system. Each command and its associated libraries necessary for
project compilation are provided entirely through the Nix flake development
shell.
A tumultuous history
Shipping around locked dependencies and development shells are useful
capabilities, so why do flakes remain an experimental feature gated behind
additional configuration steps?
Flakes were first introduced in July 2019 in [NixOS RFC 49](https://github.com/NixOS/rfcs/pull/49) by Eelco Dolstra,
the original author of Nix. Throughout the year-long RFC process, development of
the underlying plumbing for what would ultimately become Nix flakes continued in
the [Nix GitHub repository](https://github.com/NixOS/nix).
After a period of extended discussion, the proposal PR was closed [and the RFC
withdrawn in July 2020](https://github.com/NixOS/rfcs/pull/49#event-3552993451) because of a failure to reach consensus for adoption. Concerns
about scope, design, and other considerations remain visible in the (large)
discussion thread attached to RFC 49 that eventually led to its closure.
Since RFC 49 failed to pass, flakes were included in the [Nix 2.4
release in 2021](https://nix.dev/manual/nix/latest/release-notes/rl-2.4.html) as an experimental feature. Nix flakes remained accessible
only when explicitly enabled, and that requirement remains in place for the
upstream Nix project. As we'll see later, this is one aspect of flake
usage that has splintered across different implementations.
Adoption
In the years following the initial release, Nix flakes have been widely
adopted. In the [2025 NixOS Community
Survey](https://nixos.org/surveys/community/2025/), which drew input from nearly 3,400 Nix users, [78.9% of
respondents reported using flakes](https://nixos.org/surveys/community/2025/#experimental_features). A [smaller
random sampling of 300 repositories](https://gist.github.com/Mic92/48d72945d4c236e3a3403b9168312568), conducted by Nix maintainer Jörg
Thalheim, across GitHub repositories with shell.nix or
flake.nix files present found significant adoption over the traditional
development shell method using shell.nix files.
Community growth around Nix flakes without a formal plan laid out by an RFC
has become somewhat of a sore spot in the Nix community. Contributors eager for
the features within Nix flakes are frustrated at the ongoing
experimental label, while some involved in the original RFC process
remain dissatisfied with the expansive scope and design of Nix flakes that has
arguably escaped the limited scope intended by attaching the
experimental label.
Contributor Graham Christensen [wrote](https://grahamc.com/blog/flakes-are-an-obviously-good-thing/) in
2021: "I believe Flakes are astonishingly important and will be very
powerful, but the RFC experience has turned so many people against it on
principle." Jade, a contributor to the [Lix](https://lix.systems/) alternative to Nix
[reflected on
flakes](https://jade.fyi/blog/flakes-arent-real/) with a more hesitant tone: "Even assuming that flakes are good at
macro-level composition, they often are accompanied by poor use of micro-level
composition, which still is best done by using the old primitives.". Former
contributor Samuel Dionne-Riel [opined](https://samuel.dionne-riel.com/blog/2023/09/06/flakes-is-an-experiment-that-did-too-much-at-once.html)
that Nix flakes was an experiment that did too much at once, "and it sucks
because so much of it is good, or are good [but] undercooked ideas".
Despite these and other concerns, the use of flakes is widespread at this
point; many third-party utilities work as expected with flakes regardless. In
practice, the ways to use flakes via Nix have remained consistent in terms of
their commands and configuration settings although there are no guarantees
without the removal of the experimental label by maintainers.
A future for flakes?
The rift within the Nix community on the subject of flakes has become so wide
that alternative implementations have cited their stance on flakes as a
distinguishing characteristic. The Nix package manager (usually referred to as
[CppNix](https://github.com/NixOS/nix) in reflection of its C++ code
base) still marks the feature as experimental, but Lix has designated flakes as [a
frozen feature slated for future extraction into a plugin](https://wiki.lix.systems/books/development/page/flakes-feature-freeze), while [Determinate Nix](https://determinate.systems/products/nix/) (a
downstream distribution of CppNix) expressly [supports
flakes](https://determinate.systems/blog/experimental-does-not-mean-unstable/) and has marked them as a stable feature enabled by default.
As for Nix itself, [RFC
136](https://github.com/NixOS/rfcs/blob/32c871cae67fec997c9af2bf15f4a9e41d885109/rfcs/0136-stabilize-incrementally.md#L60-L66) ("A plan to stabilize the new CLI and Flakes incrementally") lays out a
path forward for Nix flakes to become a stable feature. It was [proposed](https://github.com/NixOS/rfcs/pull/136) in October 2022,
and ultimately accepted in August 2023. There is a [flakes stabilization
milestone](https://github.com/NixOS/nix/milestone/27) to track the work needed to remove the "experimental" label from
flakes.

Some work heralds potential breaking changes for flakes (such as [changing lock attributes](https://github.com/NixOS/nix/issues/8940)),
while other plans offer less-visible but significant performance improvements
such as "[lazy trees](https://github.com/NixOS/nix/pull/15711)" (to
avoid spurious file copies to the Nix store). In addition to work on the flakes
feature, the design of the newer command-line interface for nix
will have to be stabilized before moving on to complete the implementation of
flakes and mark them as a stable feature. There will need to be an additional
RFC for the final design of flakes once that happens.
The need to address command-line design stems from the fact that
flake-related commands are often conflated with other Nix commands. For example,
the experimental feature that provides alternative commands like [nix
env shell](https://nix.dev/manual/nix/latest/command-ref/new-cli/nix3-env-shell) in contrast to [nix-shell](https://nix.dev/manual/nix/latest/command-ref/nix-shell.html)
that often rely on flake-like semantics. As noted in the text of the RFC:

There are many criticisms about Flakes. But one of them especially relevant to
stabilizing is a perception that Flakes have encroached on other new features,
in the sense that it ought to be possible to use those other features without
Flakes but isn't in practice. For example, there is no reason in theory that
pure evaluation of Nix expressions requires Flakes.

Despite its criticisms, [the
RFC expresses optimism](https://github.com/NixOS/rfcs/blob/32c871cae67fec997c9af2bf15f4a9e41d885109/rfcs/0136-stabilize-incrementally.md#alternatives) about the future of flakes:

We could, of course, just "rip off the band-aid" and stabilize everything at
once. The argument for that would be that enough time has passed and the
concerns of (less numerous) long-time users are not important. But we think the
plan here has little downsides; we can instead make everyone happy with only
some delay. If that is true, why not do that instead!

Flakes remain an experimental feature of the nix command-line
utility but development continues. There is no concrete target completion date
for the stabilization effort, so when (or if) flakes will finally graduate into
stable status remains unclear, but with a plan in place and their adoption still
growing, Nix flakes are likely to appear more often across the software
landscape.
[NixOS](https://nixos.org) is the evolution & natural outcome of Nix — where if you can build
software reliably, reproducibly, & across different machines, but instead
stopping at standalone software, a collection of software + a bootstraping
process can build an operating system — with the same guarantees like rolling
back from bad states.

One issue beginners struggle with is the `nix-channel` command[[*]](https://nixtamal.toast.al/cookbook/nixos-using-nixtamal/#footnote-1) which is
usually not recommended long term as it is stateful to the machine in question
leading to drift that either makes it hard to reproduce on this specific
machine, but later becomes next to impossible when talking about building
multiple machines, working with teams, & deployments. But recommended to where?
The solution goes back to the dawn of Nixpkgs: [input pinning](https://nix.dev/reference/pinning-nixpkgs.html). While pinning
can be done with something as simple as builtins.fetchTarball — which
doesn’t even require Nixpkgs, let alone special features — it becomes tedious to
update the pin + hash over time. This explain the reasoning behind a category of
Nix software known as ‘input pinners’ which automate updating the pin + hash.
The input pinner demonstrated in this post will be [Nixtamal](https://nixtamal.toast.al/), which offer a
[unique feature set](https://nixtamal.toast.al/#key-features) compared to the alternatives, & does not require *any*
experimental, unsound features so you can rely on it[[†]](https://nixtamal.toast.al/cookbook/nixos-using-nixtamal/#footnote-2).

We will introduce the new entry point, `system.nix` with a series of projects
with overlays, modules, & input kinds that showcase both Nixtamal & stable
NixOS setups.

The code mentioned here reflects a specific to the point in time that this
post is written. We can expect things to be slightly different in the future
as well as slight differences to the Nixtamal APIs.

## NixOS 26.05 brings us `system.nix`

In the [Nix 26.05 release notes](https://nixos.org/manual/nixos/stable/release-notes#sec-release-26.05), `system.nix` is introduced as

This is just the sort of thing that anyone looking for a simple setup would need
to make our their system entrypoint!

There were other ways to achieve similar end outcomes prior to `system.nix`,
but `system.nix` is the better supported, thought-out, shipped-with-nixpkgs,
recommended way to do this.

## The non-trivial NixOS install

For this build, we want a VM that includes

| Program/service | Description | Why? |
| --- | --- | --- |
| [nixpkgs](https://github.com/NixOS/nixpkgs) `nixos-unstable` | The core monorepo of Nix expressions | Has the most packages of any package manager |
| [home-manager](https://nix-community.github.io/home-manager/) | managing user-level program + services | Common project, enables home-manager modules |
| [Nixtamal](https://nixtamal.toast.al/) `next` | Nix input pinner with unstable features (recommend `stable` for most users) | Shows Darcs fetching (impossible with current alternative input pinners) |
| [LFM2.5-350M](https://huggingface.co/LiquidAI/LFM2.5-350M) | compact, locally-run language model (can’t be bothered to care more than that for this demo) | Just a file, shows off `fresh-cmd` to avoid refetching `GGUF` files `fresh-cmd` |
| [zerostack](https://gi-dellav.github.io/zerostack/) | minimal coding agent TUI | Not in Nixpkgs, contains an overlay + a home-manager module, can be used to ‘test’ the LLM |

## Setting up Nixtamal

Let’s start with picking a VCS (many may be surprised to learn that are
many options *besides* Git). I will go with [Pijul](https://pijul.org) for this project.

```
$ pijul init
Repository created at $XDG_PROJECTS_DIR/nixcfg
$ cd nixcfg
```

To start on a base we can rely on not changing across time & system, we will set
up Nixtamal @ `nixos-unstable` channel using mirrors & the pinned to a
specific Hydra build.

```
$ nixtamal set-up --use-mirrors --nixpkgs-channel nixos-unstable
Fetching fresh value for 「nixpkgs」 …
Prefetching input 「nixpkgs」 … (this may take a while)
Prefetched 「nixpkgs」.
Making manifest file @ version:1.5.0
```

## A basic VM setup

With just `nixpkgs` we can already have the power to build many types of
outputs. Of course there is actual system setups, ISO images, netboot, but also
many types of images for various cloud platform. Let’s start by building a
QEMU image on our host machine for a new host called `"vm"`.

```
$ mkdir -p host/vm
$ touch host/vm/{configuration,hardware-configuration,system}.nix
```

Let’s start with our `system.nix` which is used as our entrypoint

```
# host/vm/system.nix
{
   system ? builtins.currentSystem,
   specialArgs ? { },
}:

let
   inputs = import ../../nix/tamal { };
in
import "${inputs.nixpkgs}/nixos" {
   inherit system;

   configuration = {
      imports = [
         ./configuration.nix
      ];

      # To get a nice nixos-rebuild experience from anywhere
      # https://discourse.nixos.org/t/curious-about-system-nix/77977/9
      nix.nixPath = [
         "nixos-config=${./configuration.nix}"
         "nixos-system=${./system.nix}"
         "nixpkgs=/run/current-system/nixpkgs"
      ];
      system.systemBuilderCommands = ''ln -s "${inputs.nixpkgs}" "$out/nixpkgs"'';
   };
}
```

Our `configuration.nix` is where we put our main configuration for our system.
In our case, we will set the default keyboard layout & shell + allow SSH
access to the VM.

```
# host/vm/configuration.nix
{ pkgs, lib, ... }:

{
   imports = [
      ./hardware-configuration.nix
   ];

   system.stateVersion = "26.11";

   networking.hostName = "nixtamal-system";

   # QWERTY is for non-nerds 😎
   console.keyMap = "dvorak";

   programs.fish.enable = true;

   users.users.toastal = {
      isNormalUser = true;
      createHome = true;
      extraGroups = [
         "power"
         "wheel"
      ];
      initialPassword = "pa$$word";
      shell = pkgs.fish;
      openssh.authorizedKeys.keyFiles = [
         (pkgs.fetchurl {
            url = "https://codeberg.org/toastal.keys";
            hash = "sha256-DAir5keAHM13XDi2dKe5rS97DSeTSnqmOZODsTgUgvw=";
         }).outPath
      ];
   };

   services.openssh = {
      enable = true;
      openFirewall = true;
      settings = {
         PasswordAuthentication = false;
         KbdInteractiveAuthentication = false;
         PermitRootLogin = "no";
      };
   };

   # Settings for the VM only
   virtualisation.vmVariant = {
      virtualisation.forwardPorts = [
         {
            from = "host";
            host.address = "127.0.0.1";
            host.port = 2222;
            guest.port = 22;
         }
      ];

      security.sudo.wheelNeedsPassword = false;
   };
}
```

As a stand in for what would normally be the NixOS hardware scan, we will put
virtualization constraints…

```
# host/vm/hardware-configuration.nix
{ ... }:

{
   virtualisation.vmVariant = {
      virtualisation = {
         memorySize = 8192;
         cores = 8;
         diskSize = 4096;
      };
   };
}
```

Lastly, we build + run the VM

```
$ nixos-rebuild build-vm --file host/vm
building the system configuration...
Done. The virtual machine can be started by running /nix/store/xb37cz4naf8m2skxa3qa2gf7579zbgjd-nixos-vm/bin/run-nixtamal-system-vm
$ /result/bin/run-nixtamal-system-vm
Starting virtiofs daemons...
$ kitty +kitten ssh -p 2222 toastal@localhost uname -a
Linux nixtamal-system 6.18.59 x86_64
```

Whose output is different than the host:

```
$ uname -srmn
Linux manju 7.2.13 x86_64
```

## Adding Home Manager + Nixtamal

Home Manager is a common tool in in the Nix community which

In the `next` repository for Nixtamal there is now a module for Home Manager.
All it does now is enable `programs.nixtamal.{enable,package}`, but it will be
built on in the future. Let’s test it now by pulling the Darcs source
repository

1. Adding inputs for Home Manager & Nixtamal
2. Wiring them up as `imports` + `overlays`
3. Create the Nixtamal demo project from the `release` blueprint

### Adding new inputs

```
$ nixtamal tweak
```

This will open our `manifest.kdl` with `$EDITOR`, your environment-configured editor

The reason we *prefer* a text file is that over time, it’s always best to
*bet on text* which is easier to tweak than remembering & query a ton of
CLI incantations to all of the possible configuration options.

```
// ┏┓╻+╻ ╱┏┳┓┏┓┏┳┓┏┓╻
// ┃┃┃┃┗━┓╹┃╹┣┫┃┃┃┣┫┃   Read the manpage:
// ╹┗┛╹╱ ╹ ╹ ╹╹╹ ╹╹╹┗┛  $ man nixtamal-manifest
version "1.5.0"
inputs {
	nixpkgs {
		archive {
			url "https://releases.nixos.org/nixpkgs/{{fresh_value}}/nixexprs.tar.zst"
			mirrors "https://mirrors.ustc.edu.cn/nix-channels/releases/nixpkgs-unstable%40{{fresh_value}}/nixexprs.tar.zst" "https://mirrors.tuna.tsinghua.edu.cn/nix-channels/nixpkgs-unstable/nixexprs.tar.zst"
			extension tar.zst
		}
		hash algorithm=SHA-256
		fresh-cmd {
			$ curl -Ls --http2 --compressed -o "/dev/null" -w "%{url_effective}" "https://channels.nixos.org/nixpkgs-unstable"
			| awk "-F/" "{print $NF}"
		}
	}
	home-manager {
		archive {
			url "https://github.com/nix-community/home-manager/archive/{{fresh_value}}.tar.gz"
		}
		fresh-cmd {
			$ git ls-remote --heads "https://github.com/nix-community/home-manager.git" --refs "refs/heads/master"
			| cut -f1
		}
	}
	nixtamal {
		// IMPORTANT: other pinning tools can’t support the Darcs kind!
		darcs {
			// next isn’t mirrored, & we will be using the latest code
			repository "https://darcs.toastal.in.th/nixtamal/next/"
		}
		fresh-cmd {
			$ curl -sL --insecure "https://darcs.toastal.in.th/nixtamal/next/_darcs/weak_hash"
		}
	}
}
```

Which after saving + quitting, requires locking…

```
$ nixtamal lock
INPUTS
✓ nixpkgs (Archive)                        Fresh
✓ home-manager (Archive)              Prefetched
✓ nixtamal (Darcs)                    Prefetched
```

### The wiring

Home Manager ships us a module. Nixtamal ships us an overlay + Home Manager
module.

```
# host/vm/system.nix
{
   system ? builtins.currentSystem,
   specialArgs ? { },
}:

let
   inputs = import ../../nix/tamal { };
in
import "${inputs.nixpkgs}/nixos" {
   # OMITTING configuration the same as the prior section

   configuration = {
      imports = [
         (import "${inputs.home-manager}/nixos")
      ];

      nixpkgs.overlays = [
         (import "${inputs.nixtamal}/nix/overlay")
      ];

      home-manager = {
         useGlobalPkgs = true;
         useUserPackages = true;
         sharedModules = [
            (_: { home.stateVersion = "26.11"; })
            (import "${inputs.nixtamal}/nix/module/home-manager.nix")
         ];
      };
   };
}
```

With Nixtamal + Home Manager ready to ro, we can enable `nixtamal` thru the
newly-added module

```
# host/vm/configuration.nix
{ pkgs, lib, ... }:

{
   # OMITTING configuration the same as the prior section

   home-manager.users.toastal = {
      programs = {
         nixtamal.enable = true;
      };
   };
}
```

### Testing it out

```
$ nixos-rebuild build-vm --file host/vm
building the system configuration...
Done. The virtual machine can be started by running /nix/store/b8lzbmrhyxk9259mb8nmiyib3f2njlav-nixos-vm/bin/run-nixtamal-system-vm
$ ./result/bin/run-nixtamal-system-vm
Starting virtiofs daemons...
```

## Setting up a local LLM

I have some complicated feelings towards LLMs (many of which not
positive — particulary around the topics of society, education, capital, &
labor) but since we can’t put Pandora back in the Box, one step in better
direction it to at least self-host & run them locally to stop sharing data with
**Big Tech**.

To do this we will need some new abilities

1. Adding a new, patched input for zerostack
2. Adding a file input with a `fresh-cmd` to avoid needless refetching of a large file, the GGUF
3. Threading `inputs` thru a system config
4. Creating a new module who sets settings for both system & home configuration

### Adding zerostack + a small LLM

```
$ nixtamal tweak
```

```
version "1.5.0"
// OMITTING configuration the same as the prior sections
inputs {
	zerostack {
		archive {
			url "https://github.com/gi-dellav/zerostack/archive/{{fresh_value}}.tar.gz"
		}
		// Our patch
		patches zerostack-hm
		// This gets the latest stable release (doesn’t match: rc, beta, alpha)
		fresh-cmd {
			$ git ls-remote --tags "--sort=v:refname" "https://github.com/gi-dellav/zerostack.git"
			| grep -oP "refs/tags/\\Kv([0-9]+\\.)+[0-9]+(?:\\^{})?$"
			| tail -n1
			| sed "s/\\^{}//"
		}
	}
	LFM2.5-350M-Q4_0 name=LFM2.5-350M-Q4_0.gguf {
		file {
			url "https://huggingface.co/LiquidAI/LFM2.5-350M-GGUF/resolve/{{fresh_value}}/LFM2.5-350M-Q4_0.gguf"
		}
		fresh-cmd {
			$ curl -fsL "https://huggingface.co/api/models/LiquidAI/LFM2.5-350M-GGUF/commits/main?path=LFM2.5-350M-Q4_0.gguf"
			| jq -r ".[0].id"
		}
	}
}
patches {
	// Open pull request to add a home-manager module
	zerostack-hm "https://patch-diff.githubusercontent.com/raw/gi-dellav/zerostack/pull/326.patch"
}
```

```
$ nixtamal lock
INPUTS
✓ nixpkgs (Archive)                        Fresh
✓ LFM2.5-350M-Q4_0 (File)             Prefetched
✓ home-manager (Archive)                   Fresh
✓ nixtamal (Darcs)                         Fresh
✓ zerostack (Archive)                    Patched

PATCHES
✓ zerostack-hm                        Prefetched
$ touch host/vm/local-llm-stuff.nix
```

### Wiring it all up

Adding zerostack’s overlay + Home Manager module is a start, but we must also
thread `inputs` thru `specialArgs` + `extraSpecialArgs` (as a final output,
these variables are fine if not preferred way of doing this) so that our new
modules can refer to our `LFM2.5-350M-Q4_0` GGUF in llama-cpp.

```
# host/vm/system.nix
{
   system ? builtins.currentSystem,
   specialArgs ? { },
}:

let
   inputs = import ../../nix/tamal { };
in
import "${inputs.nixpkgs}/nixos" {
   # OMITTING configuration the same as the prior section

   specialArgs = specialArgs // {
      inherit inputs;
   };

   configuration = {
      nixpkgs.overlays = [
         (import "${inputs.zerostack}/nix/overlay")
      ];

      home-manager = {
         extraSpecialArgs = { inherit inputs; };
         sharedModules = [
            (import "${inputs.zerostack}/nix/module/home-manager.nix")
         ];
      };
   };
}
```

Then making our new `local-llm-stuff.nix` file…

```
# host/vm/local-llm-stuff.nix
{
   config,
   lib,
   inputs,
   ...
}:

let
   cfg = config.services.llama-cpp;
in
{
   services.llama-cpp = {
      enable = true;
      settings = {
         # ↓ GGUF goes here
         model = "${inputs."LFM2.5-350M-Q4_0"}";
         alias = "lfm2.5-350m";
         host = "127.0.0.1";
         port = 8550;
         ctx-size = 8192;
         jinja = true;
         temp = 0.1;
         top-k = 50;
         repeat-penalty = 1.05;
         threads = 8;
      };
   };

   home-manager.sharedModules = [
      # Use a module to set default values for all users
      (_: {
         programs.zerostack.settings = {
            api_keys.openai = lib.mkDefault "sk-no-key-required";
            custom_providers.lfm-local = {
               model = cfg.settings.alias;
               provider_type = "openai";
               base_url = "http://${cfg.settings.host}:${toString cfg.settings.port}/v1";
               api_style = "completions";
            };
         };
      })
   ];
}
```

```
# host/vm/configuration.nix
{ pkgs, lib, ... }:

{
   # OMITTING configuration the same as the prior section

   imports = [
      ./local-llm-stuff.nix
   ];

   home-manager.users.toastal = {
      programs = {
         zerostack = {
            enable = true;
            settings = {
               provider = "lfm-local";
               model = "lfm2.5-350m";
               default_prompt = "ask";
               context_window = 8192;
               max_tokens = 512;
               no_tools = true;
               no_context_files = true;
               show_reasoning = true;
               compact_enabled = false;
               enable-exa-mcp = false;
            };
         };
      };
   };
}
```

### Testing out LLM queries

Refire up the VM…

```
$ build-vm --file host/vm
building the system configuration...
Done. The virtual machine can be started by running /nix/store/kbb433aprga2qwn85r8phvbfi5lb1srb-nixos-vm/bin/run-nixtamal-system-vm
```

## Our final basic project layout

The file structure now looks like this

```
$ tree .
.
├── host
│   └── vm
│       ├── configuration.nix
│       ├── hardware-configuration.nix
│       ├── local-llm-stuff.nix
│       └── system.nix
└─── nix
     └── tamal
         ├── darcs_context
         │   └── nixtamal.txt
         ├── default.nix
         ├── lock.json
         └── manifest.kdl

5 directories, 8 files
```

With the effictive Nixtamal config looking like:

```
$ nixtamal show
nixpkgs: (archive)
        name: nixpkgs-src
        fetch-time: build
        url: https://releases.nixos.org/nixos/unstable/nixos-26.11pre1103272.31ecbaca1bde/nixexprs.tar.zst
        mirror: https://mirrors.ustc.edu.cn/nix-channels/releases/nixos-unstable%40nixos-26.11pre1103272.31ecbaca1bde/nixexprs.tar.zst
        mirror: https://mirrors.tuna.tsinghua.edu.cn/nix-channels/nixos-unstable/nixexprs.tar.zst
        fresh-cmd: $ curl -Ls --http2 --compressed -o /dev/null -w %{url_effective} https://channels.nixos.org/nixos-unstable | awk -F/ {print $NF}
        fresh-value: nixos-26.11pre1103272.31ecbaca1bde
        hash-algorithm: SHA-256
        hash-value: sha256-yXRSdZdZZqccEL+j11lc1gFG1f7V5j8N7oPBTHwf7n4=
        frozen: false

LFM2.5-350M-Q4_0: (file)
        name: LFM2.5-350M-Q4_0.gguf
        fetch-time: build
        url: https://huggingface.co/LiquidAI/LFM2.5-350M-GGUF/resolve/657e078c94084481950a2d555a941481f715536b/LFM2.5-350M-Q4_0.gguf
        fresh-cmd: $ curl -fsL https://huggingface.co/api/models/LiquidAI/LFM2.5-350M-GGUF/commits/main?path=LFM2.5-350M-Q4_0.gguf | jq -r .[0].id
        fresh-value: 657e078c94084481950a2d555a941481f715536b
        hash-algorithm: SHA-256
        hash-value: sha256-heMoWNqvrVW3vNa5ehND7gZhGI6ANvmGLRTWtWMUL1A=
        frozen: false

home-manager: (archive)
        name: home-manager-src
        fetch-time: build
        url: https://github.com/nix-community/home-manager/archive/095fef2f265c3c0da4fe315efba8f8a04495ab34.tar.gz
        fresh-cmd: $ git ls-remote --heads https://github.com/nix-community/home-manager.git --refs refs/heads/master | cut -f1
        fresh-value: 095fef2f265c3c0da4fe315efba8f8a04495ab34
        hash-algorithm: SHA-256
        hash-value: sha256-X6xa6sGA7RnJQuZGbFMC+K+KToWAlBDCCjJXfTwEPsw=
        frozen: false

nixtamal: (darcs)
        name: nixtamal-src
        repository: https://darcs.toastal.in.th/nixtamal/next/
        context (assumed): ./darcs_context/nixtamal.txt
        datetime: 2026-10-29T12:56:50Z
        latest-weak-hash: 23c3f3ccb2177fb464d8c5a496e24b6d6d7305d6
        fresh-cmd: $ curl -sL --insecure https://darcs.toastal.in.th/nixtamal/next/_darcs/weak_hash
        fresh-value: 23c3f3ccb2177fb464d8c5a496e24b6d6d7305d6
        hash-algorithm: SHA-256
        hash-value: sha256-SnWUpHAdID/tm0YK9+kzM/KZXu2i/111TbqGpCaGS+w=
        frozen: false

zerostack: (archive)
        name: zerostack-src
        fetch-time: build
        url: https://github.com/gi-dellav/zerostack/archive/v1.8.5.tar.gz
        fresh-cmd: $ git ls-remote --tags --sort=v:refname https://github.com/gi-dellav/zerostack.git | grep -oP refs/tags/\Kv([0-9]+\.)+[0-9]+(?:\^{})?$ | tail -n1 | sed s/\^{}//
        fresh-value: v1.8.5
        hash-algorithm: SHA-256
        hash-value: sha256-i6J+7OxXa3tD0Yq/yfHmMPf5kMn51tWvaXYzgRj6YS8=
        frozen: false
        patches: zerostack-hm
```

## Yes, VM, but how to build *my* NixOS system

Well, `nixos-rebuild` works just fine for systems too!

```
$ nixos-rebuild --sudo switch --file host/vm
```

& once it’s set up, the new `$NIX_PATH` values laid out with [rnhmjoj’s
suggested setup](https://discourse.nixos.org/t/curious-about-system-nix/77977/9),

```
$ echo $NIX_PATH
nixos-config=/nix/store/g58y4fhliajxmmz8mvrrpg1zs3g502d9-configuration.nix nixos-system=/nix/store/zp9q1sw5ai6yxxaif7mgnia41qp5m6kw-system.nix nixpkgs=/run/current-system/nixpkgs
```

we now only need to run

```
$ nixos-rebuild --sudo switch
```

## Version control / source control

Now that we have a working configuration, Nix’s declarative configuration means
we can get one of great windfalls of software, [version control](https://en.wikipedia.org/wiki/Version_control), where we can
track our changes easily over time. Now that we have Nixtamal, we can be
trust in using more alternatives VCSs — not limited to only Git. If
you recall, we set up Pijul earlier, but if not, let’s set it up & add our
files (+ some other project-related files)…

```
$ pijul init
Repository created at $XDG_PROJECTS_DIR/nixcfg
$ pijul add README.rst LICENSE.txt .editorconfig .ignore
Tracked 4 path(s)
$ pijul record -m "project onset"
Hash: IOHNVGAOGSGW5G3V3F27JPKRA4JTGMB4Y23BXBMOGBNLNUYUN2TQC
$ pijul add -r nix/ host/
Tracked 2 path(s)
$ pijul record -m "nixtamal + nixos onset"
Hash: KGAXBEPVEXRM6JCKGH32SBRRNWVON573DGCKIKUQFIY7KGJZ4XIQC
$ pijul push toastal@nest.pijul.com:toastal/nixtamal-nixos-demo
●
●  project onset
●  nixtamal + nixos onset
```

Now we can continue to iterate & look back at our changes over time.

### The final project

Check it out the full Nix expressions for this NixOS VM at Nest:
[https://nest.pijul.com/toastal/nixtamal-nixos-demo](https://nest.pijul.com/toastal/nixtamal-nixos-demo) …either by visiting or `pijul
pull`ing the remote.

## Takeaway / Flakes aren’t necessary

One way to look at this is we just proved [Nixmap](https://vimjoyer.com/nixmap/), with its heart in the right
place, wrong[[‡]](https://nixtamal.toast.al/cookbook/nixos-using-nixtamal/#footnote-3). The [Put it in Git](https://vimjoyer.com/nixmap/#route=sim-git-flake) route for getting reproducible systems
under version control, aside from this task not requiring Git, can totally
skip the section for “Experimental features”[[§]](https://nixtamal.toast.al/cookbook/nixos-using-nixtamal/#footnote-4) + “Flakes” + “Turn it into a
Flake” path. I frequently see this listed as *the* route to go in more casual or
non-Nix-specific spaces which ends up being one of the primary reason folks
first get into flakes (often before understanding Nix fundamentals):

1. I want input pinning to make my system reproducible & Nixpkgs to remain at a stable point
2. I want my configuration in version control so I can go back to a prior patch when things were working, centralize my Nix configurations to more easily share code/thought, and/or use the VCS to share/deploy my systems

There is an alternative that uses more capable tools & simpler foundations:

1. [Nixtamal](https://nixtamal.toast.al/) can pin our inputs with a ton of features, without *requiring* experimental ones from Nix
2. `system.nix` is an stable-friendly entry point for NixOS
3. Use overlays + modules for composition

### …But I maintain a project with a `flake.nix`

You can do that, but you can also easily architect your code to be accessible to
**both**. All you need to do is move from a flake-driven design to an
overlay-driven design — this is going to afford you greater flexibility in the
future too! Your modules should all be proper modules — composed thru `options`,
*avoiding* curried values before modules at all costs. Now your flake is just
responsible for re-exporting packages from the overlays & plain `import`s from
files. Naturally at this point, the flake becomes irrelevant to stable Nix users
& without having to make everyone download a shim like `flake-compat` (which has
its own issues) — but the `flake.nix` might start to look more irrelevant to you
too (wouldn’t it be nice to stop thinking about `system`?).
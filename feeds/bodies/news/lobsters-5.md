I’ve created a new little tool to help run and manage scripts in a folder tree, called
            [scriptura](https://git.alin.ovh/scriptura). It is based on the idea behind
            [sd](https://github.com/ianthehenry/sd)
            and is made for fish users.

Given a script folder like so:

```console
$ set -x SCRIPTURA_ROOT ~/scripts
$ tree ~/scripts
~/scripts
├── os
│   └── update
│       ├── linde
│       └── r5 -> linde
└── scriptura
    └── tree
```

If I type in
            `scriptura run os update linde`, it will run the script at
            `~/scripts/os/update/linde`, whilst providing tab completion for each element. Pressing tab after a script has been resolved will first add
            `--`
            to clearly show the end of the script part of the command line, then use the default shell filename completion.

```console
$ scriptura run os update linde -- <tab>
bin/        flake.nix  LICENSES/  private/    scripts/  system/
flake.lock  lib/       packages/  REUSE.toml  secrets/  user/
```

The usage information gives more detail on what can be done.

```console
$ scriptura
Usage: scriptura <subcommand> <script_name>
SCRIPTURA_ROOT: ~/scripts

Subcommands:

  run          Run a script
  help         Display help information
  new          Create new script
  edit         Edit existing script
  which        Display script path
  cat          Display script content
  cmd          Execute shell command from target directory

User Subcommands:

  tree         print a tree of files under $SCRIPTURA_ROOT

Scripts:

os ...       -- os commands
```

## Typing shortcuts

To reduce the amount of typing required, I have set the following aliases.

```fish
alias sfm="scriptura"
alias sf="scriptura run"
```

The fish completion system handles these well:
            `sf <tab>`
            will show me scripts to be run, whereas
            `sfm`
            will show me the subcommands of the tool.

## Documenting scripts

To aid documentation,
            `scriptura`
            will look in a couple of places:

1. an adjacent file with the .help extension
2. comments inside the script (currently only supports one comment syntax #) Additionally, folders can be documented by adding a file called help. This information is then provided during tab completion, via the help subcommand or when listing scripts (the default action if a the command line does not resolve to a script).

## Language support

Whilst scriptura is written in fish, scripts don’t have to be; it’s just the default.
            `scriptura new`
            will create scripts with a fish shebang, which can be freely edited. I also plan to add a command-line option to set a different interpreter.

## Changes from sd

The
            [blog post version of
              `sd`](https://ianthehenry.com/posts/sd-my-script-directory/)
            and the version
            [published to Github](https://github.com/ianthehenry/sd)
            already differ in that the blog post version uses subcommands like
            `sd new`, whereas the Github version uses flags for actions that don’t involve running a script (e.g.
            `sd --new`). I prefer the subcommand style, at least when there is a short alias to the
            `run`
            subcommand.

Additionally, I’ve added some new features.

## New features

### Tab completion after
            `new`

The
            `new`
            subcommand invokes the underlying command’s tab-completion after a script name is given:

```console
$ scriptura new mac svc restart -- launchctl k<tab>
kickstart  (Forces an existing service to start)
kill    (Sends a signal to the service instance)
```

### Run ad-hoc commands in the script root

```console
$ scriptura cmd tree
```

will run the
            `tree`
            command with the working directory set to
            `$SCRIPTURA_ROOT`.

### Custom subcommands

One thing that I thought would be useful is a
            `tree`
            subcommand. However, I don’t want to force that on any other potential users. Whilst I could have settled with the
            `cmd`
            subcommand mentioned in the previous section, I decided I wanted it to be even easier.
Scripts under the special
            *scriptura*
            subdirectory are exposed as subcommands, which pass flags to the underlying command and interpret positional arguments as script path components:

```console
# create a new script at ~/scripts/scriptura/tree which just calls tree
$ scriptura new scriptura tree -- tree
$ scriptura tree
.
├── os
│   └── update
│       ├── linde
│       └── r5 -> linde
└── scriptura
    └── tree

4 directories, 3 files
$ scriptura tree -L1 os
os
└── update

2 directories, 0 files
```

## Motivation

Recently, I found
            [sd](https://github.com/ianthehenry/sd), which is designed to help run and manage scripts under a specific directory tree.

There are two reasons I’m not using this tool directly:

- It’s called sd, which is a name that’s already taken on my system by another tool: sd (sed alternative).
- It doesn’t ship with completions for the fish shell. There was a gist with these, but it seems to have disappeared. The completions are, in my opinion, the biggest feature.

Also, I expected a fish implementation to be easier to read and write, as well as not requiring so many external command calls.

In the introductory
            [blog post](https://ianthehenry.com/posts/sd-my-script-directory/), Ian writes
            It’s not really a thing. It’s more of an idea. You can implement it yourself in one sitting, if you want..

It took me more than one sitting, but I enjoyed it.
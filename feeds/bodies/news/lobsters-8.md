In the theme of [NixOS enabling fearlessness](https://entropicthoughts.com/nixos-is-making-me-less-afraid), here’s a way I use Nix on *other*
Linux distributions to sleep better at night: managing dependencies of simple
scripts.

This way of using Nix is for everyone, not just those willing to try NixOS.
We’ll look at it first for a Python script, and then see how it can be adapted
to any other language.

I wanted to create a script that would read the verbatim content of my articles
out loud to me with a synthesised voice.1<sup>1</sup> This is entirely separate from the
recent ai narration experiment. Reading the article out loud is one of my
self-editing steps, to detect flow problems and awkward phrasings. I’ve
discovered that hearing someone else read the article is slightly more effective
than reading it out loud myself, though both are useful. When I read it out loud
myself, I tend to read what I intended to say, not the words that are actually
on the page. One of the more convenient ways to do this is with Python, where
I’ve heard good things about [Trafilatura](https://trafilatura.readthedocs.io/en/latest/) for extracting the contents out of a
web page, filtering on types of content, etc.

But Trafilatura is a third-party Python dependency. Those suck because they
break your scripts when you so much as glance sideways at `pip`. The code also
ended up depending on `aplay`, which is a system dependency, making it two
different sources of future breakage. A couple of years ago, I would probably
have judged that to be too much maintenance, so I wouldn’t have created the
script. Fortunately, now I know about Nix.

We have a Python script, and we want to make it trivially runnable anywhere,
without having to worry about dependencies. To get to that position, we first
create a file called `flake.nix` in the same directory as the Python script, and
we start to fill it in:

```
{
  # Pick the package versions of the most recent NixOS.
  # Change these numbers to upgrade later if desired.
  # If the upgrade breaks, it can be rolled back by
  # decrementing these numbers again.
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

  outputs = { nixpkgs, ... }:
    let
      # Generate outputs for both Intel and ARM. In this
      # case, I do not include macOS among the supported
      # systems because aplay is linux-only.
      #
      # This references "legacyPackages" which might sound
      # odd, but in Nix flake contexts, the entire nixpkgs
      # package set is called "legacy" because it uses an
      # older structure for organisation.
      forAllSystems = f: nixpkgs.lib.genAttrs
        [ "x86_64-linux" "aarch64-linux" ]
        (system: f nixpkgs.legacyPackages.${system});
    in {
      # The default entry point of a Nix flake are the
      # derivations named "packages.<system>.default". Here
      # they are defined for the two Linux architectures.
      packages = forAllSystems (pkgs: {
        default =
          # Default package definition to be filled in!
      });
    };
}
```

This outline is the same every time we use Nix to manage the dependencies of a
program, regardless of language, choice of dependencies, etc. The specifics that
differ are those in the definition of the `default` package.

Since we have a Python script, we’ll use the `writePython3Bin` helper function
to turn that into an executable with Nix-managed dependencies. It takes two
arguments we need:

- makeWrapperArgs replaces the main script with a small wrapper script that sets up the right environment and then execves into the main script. We will use it to set up the PATH variable to point at Nix-managed versions of system dependencies.2<sup>2</sup> This may be the most common way to use it, but it can be used to fix up the environment in any number of other ways. This means the Python script doesn’t have to be written with Nix-managed dependencies in mind. As far as the script cares, it thinks it’s running in a normal environment. But the commands it runs come from the Nix store, and are of the specific versions we requested.
- libraries lets us specify which Python dependencies should be available to the Python interpreter when it runs our script.

Filling in the right values for these arguments, our `flake.nix` will look
something like the following.

```
{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

  outputs = { nixpkgs, ... }:
    let
      forAllSystems = f: nixpkgs.lib.genAttrs
        [ "x86_64-linux" "aarch64-linux" ]
        (system: f nixpkgs.legacyPackages.${system});
    in {
      packages = forAllSystems (pkgs: {
        # Create executable from Python script.
        default = pkgs.writers.writePython3Bin "readarticle" {
          # Make system dependencies available.
          makeWrapperArgs = [
            "--prefix" "PATH" ":" (pkgs.lib.makeBinPath [
              pkgs.alsa-utils
            ])
          ];
          # Make libraries available.
          libraries = [
            pkgs.python3Packages.requests
            pkgs.python3Packages.trafilatura
          ];
        } (builtins.readFile ./main.py);
      });
    };
}
```

And that’s it. After this, we can run the script with `nix run .` and the first
time we do it, Nix is going to set up all the dependencies and then run the
script. On subsequent runs, Nix recognises that everything is in place and runs
the script right away.3<sup>3</sup> Actually, the `writePython3Bin` function does one
more thing: it runs the script through a linting pass. This can be disabled, but
I generally like keeping the default behaviour. The corresponding writeBashBin
it runs the script through ShellCheck and fails the build before running the
script if it doesn’t ShellCheck cleanly. *That* is very valuable!

If we copy this script to another computer, it will continue to work exactly the
same as on the first computer, because Nix will set up all the same dependencies
the same way before running the script. If we forget about it and run it a year
later, it will continue to run just the same as before, because the executable
created by Nix refers to the exact same set of dependencies regardless of what
else has changed on the system.

I imagine that of those reading this article, a small crowd starts murmuring
about `uv`. From what I understand, `uv` does take a lot of the headache out of
managing Python dependencies.4<sup>4</sup> I don’t know, honestly. It came around after I
stopped working professionally with Python, so learning and understanding it
would happen in my limited spare time, and now that I have Nix, I think I have
better things to learn and understand. But it is only for Python. *Nix works
for any dependency, with any language.* If we have an R script we want to manage
the dependencies for, we’d do the exact same thing and use `writeRscriptBin`
instead.

The way to find the right helper function is by knowing that they are called
*writers*, and then [searching Noogle for them](https://noogle.dev/q/?term=writers+python). By excluding the language from
that search, we can see there are writers for other languages too, like C,
JavaScript, Shell, Haskell, Perl, and more.

But there’s no writer helper function specifically for Emacs Lisp. What if we
have an Emacs Lisp script we want Nix to manage the dependencies of? Then we
can still use the lower level `makeScriptWriter` function. Here’s a generic
example of that:

```
default = pkgs.writers.makeScriptWriter
  {
    # System dependencies work the same as before.
    makeWrapperArgs = [
      "--prefix" "PATH" ":" (pkgs.lib.makeBinPath [
        pkgs.some-package-with-executable
      ])
    ];

    # Make sure the interpreter is produced with the
    # necessary run-time dependencies. Most packaged
    # scripting languages support the "withPackages"
    # convention for this.
    interpreter = "${(pkgs.interpreter.withPackages (ps: [
      ps.dependency-1
      ps.dependency-2
    ]))}/bin/interpreter-binary";
  }
  "/bin/our-executable-name"
  (builtins.readFile ./source-file-path);
```

For Emacs Lisp, the interpreter package we’d use would be Emacs. The output path
(`/bin/our-executable-name`) is package relative, so we don’t have to worry
about it clobbering the file system.

Of course, we also have compiled languages, like Ada. Ada also doesn’t have a
ready-made writer function, so we’d use the generic `makeBinWriter` helper,
which takes a `compileScript` argument where we specify how to compile.

```
default = pkgs.writers.makeBinWriter
  {
    # System dependencies work the same again.
    makeWrapperArgs = [
      "--prefix" "PATH" ":" (pkgs.lib.makeBinPath [
        pkgs.some-package-with-executable
      ])
    ];

    # The compilation script can reference any compiler and
    # any libraries in nixpkgs, and they will be managed by
    # Nix during the build. Any runtime dependencies will be
    # managed by Nix automatically too.
    #
    # The file we read with readFile is called $contentPath
    # in this script, and the output must be written to the
    # path in the $out variable.
    compileScript = ''
      ${pkgs.some-compiler}/bin/compiler-binary \
        -o $out $contentPath
    '';
  }
  "/bin/our-binary-name"
  (builtins.readFile ./source-file-path);
```

Although this looks like deep, black magic, it’s not. What’s so neat about Nix
is that it uses regular Unix paths, regular Unix environment variables, and
content hashing to figure out what depends on what and whether an input has
changed, necessitating rebuilding.

The important question I haven’t yet answered is “How do you know all this?”

I wish I could answer “I have read the documentation” but that’s not it. There
are two parts to the knowledge, and the learning paths are different for them:

- At its core, Nix-the-system is a simple machine that can be grasped in few hours of reading. Similarly, Nix-the-language is small enough to be learned in a day or two. Both of these can be learned from Eelco Dolstra’s PhD thesis, which is a pleasant read and highly recommended, even if you end up not using Nix.5<sup>5</sup> Though I have a hard time imagining how anyone could read the thesis and not end up with a desire to use Nix.
- Then there’s the huge library of code called nixpkgs. That’s where we find the writers we’ve used in this article, and it’s not well documented anywhere. The way to learn how e.g. writers work is to read their source code. A lot of what’s in nixpkgs is only learnable by reading the code. That might not sound like a big deal, since Nix is a small and easy language. Unfortunately, plenty of what’s in nixpkgs depends on other things in nixpkgs, and it is common to pass named arguments implicitly through attribute sets (key–value dictionaries), so it’s not always obvious which things are actually passed down intentionally and which are not, nor how they are used. It’s easy to end up reading a lot of code.

But as long as the scripts you write are in languages that already have writers
in nixpkgs, you can mostly use the same template for all of them except replace
the specific writer you use.

This is entirely separate from the
recent ai narration experiment. Reading the article out loud is one of my
self-editing steps, to detect flow problems and awkward phrasings. I’ve
discovered that hearing someone else read the article is slightly more effective
than reading it out loud myself, though both are useful. When I read it out loud
myself, I tend to read what I intended to say, not the words that are actually
on the page.

This may be the most common way to use it, but it can
be used to fix up the environment in any number of other ways.

Actually, the `writePython3Bin` function does one
more thing: it runs the script through a linting pass. This can be disabled, but
I generally like keeping the default behaviour. The corresponding writeBashBin
it runs the script through ShellCheck and fails the build before running the
script if it doesn’t ShellCheck cleanly. *That* is very valuable!

I don’t know, honestly. It came around after I
stopped working professionally with Python, so learning and understanding it
would happen in my limited spare time, and now that I have Nix, I think I have
better things to learn and understand.

Though I have a hard time imagining how anyone could read the thesis
and not end up with a desire to use Nix.
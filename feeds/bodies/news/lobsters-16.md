Have you heard about [dynamic derivations](https://fzakaria.com/2025/03/11/nix-dynamic-derivations-a-practical-application)?

They are an experimental-feature in Nix that lets a derivation produce other derivations as its output. Why ? This lets you dynamically create your build graph, instead of having to know it all at evaluation time. It’s Nix’s answer to try and match the build speed of other build systems like [Bazel](https://bazel.build/) or [buck2](https://buck2.build/).

[![So hot right now meme: Mugatu from Zoolander under the caption "Dynamic derivations", above "So hot right now"](https://fzakaria.com/assets/images/derived/dyn_drv_so_hot_meme-748w.webp)](https://fzakaria.com/assets/images/dyn_drv_so_hot_meme.png)

There is not much written about dynamic derivations, and the documentation is sparse. I have [written](https://fzakaria.com/2025/03/10/an-early-look-at-nix-dynamic-derivations) [a](https://fzakaria.com/2025/03/11/nix-dynamic-derivations-a-practical-application) [few](https://fzakaria.com/2025/03/12/nix-dynamic-derivations-a-lang2nix-practicum) [posts](https://fzakaria.com/2026/09/20/a-build-graph-that-rolls-dice) about them, so I sometimes get questions about them.

Recently, I got a DM from [Evan Porter](https://www.linkedin.com/in/evanwp/) over [LinkedIn](https://www.linkedin.com/), the ultimate bug triaging network, about whether it is possible to query the deriver of a dynamic derivation to get the initial derivation.

> For dynamic derivations let’s say I have a .drv.drv file. This file outputs a derivation.
> Is it usually possible to query deriver the output derivation to obtain the initial derivation?

They had tried it and got this:

```
$ nix-store --query --deriver \
    $(nix-store --query --deriver ./result)
unknown-deriver
```

That should work. 🤨 Every path a build registers carries a `deriver`, the `.drv` that produced it, and a `.drv` that came out of a build is still a path a build registered.

When I tried it, it worked. 🤷

You will need `extra-experimental-features = dynamic-derivations ca-derivations recursive-nix` in your `nix.conf` to drive the samples in this post.

```
$ nix build -f default.nix \
    --print-out-paths
/nix/store/v4hkwn8y4m083gsap6523c0m5r985ygr-result

$ nix-store --query --deriver \
    /nix/store/v4hkwn8y4m083gsap6523c0m5r985ygr-result
/nix/store/6pniymfhwcyrmkns0np7ap1argjziqq2-result.drv

$ nix-store --query --deriver \
    /nix/store/6pniymfhwcyrmkns0np7ap1argjziqq2-result.drv
/nix/store/m5x261fv29jkn0rvznqj2fzkaql01xiy-result.drv.drv
```

Turns out, there is a case where you do get `unknown-deriver` if you set `__contentAddressed = true` on the producer. If the producer is content-addressed, its output path is not known until after the build, and Nix does not fill in the `deriver` of a path that already exists.
I filed [NixOS/nix#16823](https://github.com/NixOS/nix/issues/16823).

The question though made me wonder how far back you can walk the chain of dynamic derivations. I had to try it. 😈

Let’s pick a fun example to see how far we can go. Here is a derivation that imitates the classic song *99 bottles of beer* by producing a chain of derivations, each one outputting the next verse.<sup>1</sup>1The builder writes the next derivation by hand in [ATerm](https://fzakaria.com/2025/03/23/nix-derivations-by-hand), so there is no recursive Nix and no `nix-instantiate` involved.

```
export PATH=$busybox/bin

# A content-addressed derivation does not know its output path, so its
# "out" variable holds this placeholder and Nix swaps in the real path at
# build time. It is "/" + nix32(sha256("nix-output:out")), the same for
# every derivation with an output named "out".
OUT_PLACEHOLDER=/1rz4g4znpzjwh1xymhjpm42vipw92pr73vdgl6xs1hycac8kf2n9

bottles() {
  case $1 in
    0) echo "no more bottles" ;;
    1) echo "1 bottle" ;;
    *) echo "$1 bottles" ;;
  esac
}

# The last derivation in the chain writes the punchline instead of a .drv.
if [ "$n" -eq 0 ]; then
  echo "No more bottles of beer on the wall, no more bottles of beer." >&2
  echo "Go to the store and buy some more." > $out
  exit 0
fi

next=$((n - 1))
echo "$(bottles $n) of beer on the wall, $(bottles $n) of beer." >&2
echo "Take one down, pass it around, $(bottles $next) of beer on the wall." >&2

# Input sources must be sorted.
srcs=$(printf '"%s"\n' "$busybox" "$script" | sort | paste -sd, -)

# Write the derivation for the next verse. A .drv is a single line of
# ATerm, so strip the spaces and newlines that are only here for reading.
# Nix takes a derivation's name from its store path, so the next name is
# ours minus one ".drv".
tr -d ' \n' > $out <<EOF
Derive(
  [("out", "", "text:sha256", "")],
  [],
  [$srcs],
  "$system",
  "$busybox/bin/sh",
  ["$script"],
  [
    ("builder", "$busybox/bin/sh"),
    ("busybox", "$busybox"),
    ("n", "$next"),
    ("name", "${name%.drv}"),
    ("out", "$OUT_PLACEHOLDER"),
    ("outputHashAlgo", "sha256"),
    ("outputHashMode", "text"),
    ("script", "$script"),
    ("system", "$system")
  ]
)
EOF
```

> **Tip**
> A derivation whose output is a `.drv` must set `outputHashMode = "text"`.

In our example we are using a content-addressed derivation, but the same idea works with an input-addressed one, but it’s more work to compute the output path in the shell, unless you are using `nix-instantiate` to do it for you with recursive Nix.

The Nix side builds the first derivation and then follows `builtins.outputOf` once per bottle.

```
let
  pkgs = import (fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/6dadaf4375be35033e1c84395adbd53ff5fded96.tar.gz";
  }) { };
  inherit (pkgs) lib;

  # maximum bottles of beer on the wall,
  # 50 is the most that fits in a store path!?
  bottles = 50;

  top = derivation {
    name = "beer" + lib.concatStrings (lib.replicate bottles ".drv");
    system = builtins.currentSystem;
    builder = "${pkgs.busybox}/bin/sh";
    args = [ ./bottles.sh ];
    script = ./bottles.sh;
    busybox = pkgs.busybox;
    n = bottles;
    __contentAddressed = true;
    outputHashMode = "text";
    outputHashAlgo = "sha256";
  };
in
# Follow the chain of outputs down to the last derivation.
lib.foldl' (drv: _: builtins.outputOf drv "out") top.outPath (lib.range 1 bottles)
```

While working through this example, I hit a bug in Nix that made me set `__contentAddressed = true` on the top derivation. That is not necessary for a derivation that outputs a `.drv`, but it works around the bug. I filed [NixOS/nix#16830](https://github.com/NixOS/nix/issues/16830).

You might notice that we limit the number of beers to 50. Why 50 and not 99?

Well, 50 is the most that fits in a store path.

```
error: path '…-beer.drv.drv.drv…' is not a valid store path:
  name 'beer.drv.drv.drv…' must be no longer than 211 characters
```

The maximum length of a store path is [211 characters](https://github.com/NixOS/nix/blob/7f1ff3fec92f9d60327e4ca9e51acd565a91cc6c/src/libstore/include/nix/store/path.hh#L48). A derivation’s store path must include the `.drv` suffix, and every `.drv` in a chain adds four characters. The top derivation is named `beer` and if you add 51 `.drv`s we get 208 characters. No room for any more beer. 🍻

Let’s <del>build</del> sing it.

```
$ nix build -f beer.nix \
    --print-out-paths \
    --print-build-logs
building '/nix/store/di5x9yrhh6pfn214c41bnpxh1avya51c-beer.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv'...
beer.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv> 50 bottles of beer on the wall, 50 bottles of beer.
beer.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv> Take one down, pass it around, 49 bottles of beer on the wall.
building '/nix/store/zg35ykl6qvh6gasy6q4pc6d4kyqcq0sd-beer.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv'...
beer.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv> 49 bottles of beer on the wall, 49 bottles of beer.
beer.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv> Take one down, pass it around, 48 bottles of beer on the wall.
building '/nix/store/g07drgnkmwkbyccwk8vzzibbfdznpqjd-beer.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv'...
beer.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv> 48 bottles of beer on the wall, 48 bottles of beer.
beer.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv.drv> Take one down, pass it around, 47 bottles of beer on the wall.
...
building '/nix/store/0vr55qvmaswc2vkjvy4i2blcgc6phv85-beer.drv.drv'...
beer.drv> 1 bottle of beer on the wall, 1 bottle of beer.
beer.drv> Take one down, pass it around, no more bottles of beer on the wall.
building '/nix/store/kb16larpavss7y26ivyib5mgc23gicn6-beer.drv'...
beer> No more bottles of beer on the wall, no more bottles of beer.
/nix/store/kp2aln1pr2cy4gn9qs8vzkq850blj60i-beer

$ cat result
Go to the store and buy some more.
```

Fifty-one builds, one after another<sup>2</sup>2A single trivial build takes about 1.5 seconds on my laptop, so the cost of building 51 derivations is about 75 seconds largely due to substituter lookups. If you disable substituters `--option substituters ''`, the builds take about 1.3 seconds in total. . Evaluation knows about only the first one. Nix discovers each of the other 50 by building the one before it. 🍺

> **Aside**
> Hey, didn’t an [earlier post](https://fzakaria.com/2026/09/20/a-build-graph-that-rolls-dice) have dynamic derivation chains 500 deep?!
>
> Yes! The difference is whether a derivation *outputs* the next one or *depends* on it. A derivation whose output is another derivation gets one more `.drv` appended to the name. The dice chain linked each step to the next as a dependency, and a dependency keeps its own name, so no name ever had more than two `.drv`s in it.

Back to the original question: can we query the deriver of the output derivation to get the initial derivation? Yes, we can.

Let’s put `nix-store --query --deriver` in a loop that walks from the result all the way back to the top.

```
$ p=$(readlink result)
$ while [ "$p" != unknown-deriver ]; do
    echo "$p"
    p=$(nix-store --query --deriver "$p")
  done > chain.txt

$ wc -l < chain.txt
52

$ head -4 chain.txt
/nix/store/kp2aln1pr2cy4gn9qs8vzkq850blj60i-beer
/nix/store/kb16larpavss7y26ivyib5mgc23gicn6-beer.drv
/nix/store/0vr55qvmaswc2vkjvy4i2blcgc6phv85-beer.drv.drv
/nix/store/flj05chf2yyn5bxsjq41if7mihcjjqkp-beer.drv.drv.drv
```

We have the result plus 51 derivations. 💪

Since every derivation in the chain was built, every one has a build log, and you can ask any of them to sing its verse again.

```
$ nix log "$(sed -n 26p chain.txt)"
24 bottles of beer on the wall, 24 bottles of beer.
Take one down, pass it around, 23 bottles of beer on the wall.
```

I’m very excited for the future of dynamic derivations. [tomberek](https://github.com/tomberek) is [leading a working-group](https://discourse.nixos.org/t/dynamic-derivations-dynamic-build-graphs-next-steps/79409/) to finalize the feature and are currently meeting weekly. With dynamic derivations, Nix will be able to compete with other build systems in terms of speed and flexibility and *take over the world*.
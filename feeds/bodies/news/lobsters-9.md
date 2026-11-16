Nix evaluator supports [evaluation](https://nix.dev/manual/nix/2.35/language/evaluation)
[profiling](https://en.wikipedia.org/wiki/Profiling_(computer_programming))
compatible with `flamegraph.pl`. The profiler samples the nix
function call stack at regular intervals. It can be enabled with the
[`eval-profiler`](https://nix.dev/manual/nix/2.35/command-ref/conf-file#conf-eval-profiler)
setting:

```console
$ nix-instantiate "<nixpkgs>" -A hello --eval-profiler flamegraph
```

Stack sampling frequency and the output file path can be configured with
[`eval-profile-file`](https://nix.dev/manual/nix/2.35/command-ref/conf-file#conf-eval-profile-file)
and [`eval-profiler-frequency`](https://nix.dev/manual/nix/2.35/command-ref/conf-file#conf-eval-profiler-frequency).
By default the collected profile is saved to `nix.profile` file in the current working directory.

The collected profile can be directly consumed by `flamegraph.pl`:

```console
$ flamegraph.pl nix.profile > flamegraph.svg
```

The line information in the profile contains the location of the [call
site](https://en.wikipedia.org/wiki/Call_site) position and the name of the
function being called (when available). For example:
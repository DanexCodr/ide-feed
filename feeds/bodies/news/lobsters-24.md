We are excited to announce the release of [Hoot](https://spritely.institute/hoot) 0.10.0!  Hoot
is a Scheme to WebAssembly compiler backend for
[Guile](https://gnu.org/software/guile), as well as a general purpose
WebAssembly toolchain.  In other words, *Scheme in the browser!*

This release contains new features and bug fixes and since the [0.9.0
release](https://spritely.institute/news/hoot-0-9-0-released.html) back in May.

## Use Hoot in the upcoming Lisp Game Jam!

On Friday (October 30th 2026), the [autumn edition of the Lisp Game
Jam](https://itch.io/jam/autumn-lisp-game-jam-2026) will begin!  It's
a 10-day long game jam where participants make games using their
favorite flavor of Lisp.

Does making a small web game in Scheme using Hoot sound appealing to
you?  Well, then we have just the thing to get you started: the [Hoot
game jam
template!](https://codeberg.org/spritely/hoot-game-jam-template) This
template project has everything you need to start making an HTML5 game
with Hoot quickly.

The template repository includes:

- Bindings to the necessary web APIs to make an interactive game with HTML5 canvas
- A Makefile for compiling, running a development web server, and generating a .zip bundle for uploading to itch.io
- A very simple Breakout-like example game that demonstrates how to put all the pieces together

For more inspiration, here are some games made with Hoot for past
jams:

Now, onto the release notes!

## Compiler changes

- Added module name to contextualize duplicate import errors.
- Added support for library versioning for R6RS compatibility.
- Fixed default version for define-module libraries.
- Fixed locate-library not respecting configured load extensions. Previously, we were using Guile's load extension parameter instead of Hoot's own.

## Runtime changes

- Added %struct-ref and %struct-set! primitives for accessing record types defined using the interpreter.
- Stopped raising errors when importing an undefined symbol in the runtime module system. Guile is lax about this so Hoot being strict caused compatibility issues.
- Fixed optional argument parsing in primitive-eval.
- Fixed keyword argument parsing for procedures with both optional and keyword arguments in primitive-eval.
- Fixed error messages regarding runtime module registry to include the correct CLI flag: -fruntime-modules.

## Scheme changes

- Added partial implementation of SRFI-13: String Libraries. It's just a set of re-exports, very similar to Guile, but Guile's SRFI-13 module is not declarative and is thus rejected by Hoot's compiler.
- Added partial implementation of SRFI-60: Integers as Bits.
- Added define-macro, defmacro, delete, list->symbol, and symbol to (guile).
- Exported define-syntax-parameter and syntax-parameterize, symbol-append, integer-length, and gensym from (guile).
- Added list->bitvector and bitvector to (hoot bitvectors) and re-exported them in (guile).
- Implemented get-bytevector-all in (rnrs io ports).
- Made bytevector=? a publicly exported procedure from (hoot bytevectors) and (rnrs bytevectors).
- Added define-syntax-parameter and syntax-parameterize primitives.
- Improved (ice-9 exceptions) exports to more closely match Guile.
- Added (rnrs) module.
- Added (rnrs base) module.
- Added (rnrs syntax-case) module.
- Added (rnrs r5rs) module.
- Added (rnrs hashtables) module.
- Added (rnrs files) module.
- Added (rnrs enums) module.
- Added (rnrs exceptions) module.
- Added (rnrs arithmetic fixnums) module.
- Added (rnrs records inspection) module.
- Added (rnrs records procedural) module.
- Added (rnrs records syntactic) module.
- Added (rnrs io simple) module.
- Added (rnrs io ports) module.
- Added port-has-position? to (hoot ports) for R6RS compatibility.
- Added stubs for centered division to (hoot numbers) and a stub for integer-length to (hoot bitwise) for R6RS compatibility (eventually).
- Rewrote (rnrs bytevectors) as an R6RS module with version (6).
- Fixed number->string to round floating point decimal part to an even digit.
- Fixed number->string for floating point numbers ±2^N, where 52 <= N <= 1023.
- Fixed incorrect bytevector copy in number->string floating point conversion algorithm.
- Fixed min/max macros not working when given zero arguments.
- Fixed the parameters to the log procedure in (guile).
- Fixed the implementation of negate in guile. It was doing entirely the wrong thing.

## CLI changes

- Port numbers are now validated to be exact integers in the range [1, 65535].
- Actually complain about invalid option or unknown subcommand. Previously, the code that was supposed to do this was unreachable.
- Add --experimental-wasm-exnref feature flag when running hoot compile --run=node for continued compatibility with supported NodeJS versions that don't have the new Wasm exnref feature enabled by default.
- Fixed build-time disabling of hoot server. In past releases, the hoot CLI script would still attempt to load should-be-optional libraries that ./configure had already determined to be missing. Thanks to mcc for discovering this blunder.

## Documentation changes

- Improved instructions in "Building from source" section of the manual.
- Dependencies are now mentioned in the "Advanced path" section of the README.
- Updated project template README to say Guix is not required (though it's still the easiest option).

## Browser compatibility

- Compatible with Safari 26 or later.
- Compatible with Firefox 121 or later.
- Compatible with Chrome 119 or later.

## Get Hoot

Hoot is available in GNU Guix:

```
$ guix pull
$ guix install guile guile-hoot
```

Also, Hoot is now available in
[Debian](https://tracker.debian.org/pkg/guile-hoot), though it will
take awhile for this release to make it there.

Otherwise, Hoot can be built from source via our release tarball.  See
the [Hoot homepage](https://spritely.institute/hoot) for a download link and GPG signature.

Documentation for Hoot 0.10.0, including build instructions, can be
found
[here](https://spritely.institute/files/docs/guile-hoot/0.10.0/index.html).

## Get in touch

For bug reports, pull requests, or just to follow along with
development, check out the [Hoot project on
Codeberg](https://codeberg.org/spritely/hoot).

If you build something cool with Hoot, let us know on our [community
forum](https://community.spritely.institute)!

Thanks to Z572, stdh, Walter Lewis, and Jelle Licht for their
contributions to this release.

Until next time, happy hooting! 🦉

## Thanks to our supporters

Your support makes our work possible!  If you like what we do, please
consider [becoming a Spritely supporter today](https://spritely.institute/donate)!
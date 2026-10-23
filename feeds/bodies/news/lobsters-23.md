During the Zig 0.17 development cycle, the [separation of maker process and configurer process](https://ziglang.org/download/0.17.0/release-notes.html#Separate-the-Maker-Process-from-the-Configurer-Process) has broken critical build system integration features in ZLS. Most of them have since been restored using the [build system protocol](https://ziglang.org/download/0.17.0/release-notes.html#Build-Server-Protocol) but various regressions remain that are anticipated to be resolved during the next release cycle.

On the positive side, the new protocol lays the foundation for future improvements in ZLS and related tooling. Especially editors could utilize it to integrate unit testing, fuzzing, code coverage reports or debugging capabilities that are fully aware of the Zig build system.

All known regressions are tracked in [#3277](https://github.com/zigtools/zls/issues/3277) and listed below:

Type resolution for package imports in `build.zig` files have regressed.

Upstream Zig Issue: [ziglang/zig#36387](https://codeberg.org/ziglang/zig/issues/36387)

### Module `@import`s to exported modules without a compile step

Type resolution for modules that are only exported using `b.addModule` but aren’t tied to a compile step have regressed.

An `build.zig` file that would be affected:

```
const std = @import("std");
pub fn build(b: *std.Build) void {
    _ = b.addModule("foo", .{
        .root_source_file = b.path("root.zig"),
        .imports = &.{
            .{ .name = "bar", .module = b.createModule(.{ .root_source_file = b.path("bar.zig") }) },
        },
    });
}
```

In the above example, `@import("bar")` will not be resolved.

Upstream Zig Issue: [ziglang/zig#36388](https://codeberg.org/ziglang/zig/issues/36388)

### Build system protocol file watching doesn’t work on windows

File watching has regressed on windows due to a bug in the build system protocol. This does not affect the CLI when running `zig build --watch`.

ZLS does work around this issue by receiving file save events through the LSP protocol. File changes through external programs (e.g. version control) will not be detected.

Upstream Zig Issue: [ziglang/zig#37236](https://codeberg.org/ziglang/zig/issues/37236)

## Contributors

Here is a list of everyone who has made at least one contribution to this release of ZLS:

- Techatrix
- FnControlOption
- psznm
- xdBronch
- Khang Nguyen Duy
- Akhilesh Arora
- James
- Jassiel Ovando
- fomgleb
- l1yefeng

## Sponsors

We’d like to take a second to thank all our awesome [contributors](https://github.com/zigtools/zls/graphs/contributors) and donators/backers/sponsors; if you have time or money to spare, consider partaking in either of these options - they help keep ZLS awesome for everyone!
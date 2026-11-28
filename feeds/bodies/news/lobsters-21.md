### Not sure how to structure your Go web application?

My new book guides you through the start-to-finish build of a real world web application in Go — covering topics like how to structure your code, manage dependencies, create
                    dynamic database-driven pages, and how to authenticate and authorize users securely.

<mark>Black Friday sale: 30% off until the 1st December!</mark>

Way back in 2019, I wrote the blog post
  [An Overview of Go's Tooling](https://www.alexedwards.net/blog/an-overview-of-go-tooling).
  It was a popular article and IIRC, ended up being one of the most-read items in the
  [Go Weekly](https://golangweekly.com/) newsletter that year. It's also one that I personally still come
  back to
  fairly
  often, when I want to remind myself of a specific command that I can't remember.

But a lot has changed in the past 7 years, and some of the information in that original post is now
  painfully out-of-date. So this is a version 2 of that post... fully updated for the module-enabled, gopls-integrated,
  token-fuelled
  world that we now live in 😊

## Installing and using third-party tools

One of the biggest improvements to Go's tooling has been the introduction of new ways to run third-party tools. We
  now have three options — `go install`, `go run`, and `go tool` — each
  suited to slightly different use cases.

### With go install

The first option is to install the tool on your local machine using the `go install` command. You can run
  this command from anywhere on your machine, and it will download the necessary source code for the tool and create an
  executable binary in your `GOBIN` directory. So long as your `GOBIN` directory is on your
  system path, you can then run the tool whenever you need it.

For example, to install the latest version of `govulncheck`, check its install location, and run it, you
  can do this:

Using `go install` tends to be a good option for general-purpose tools that happen to be written in Go,
  where you don't need to pin a specific version for use within a project or necessarily keep up with the latest
  release. Personally, I tend to use it for installing tools like
  [`hey`](https://github.com/rakyll/hey), which I often use for things
  *outside of Go development*.

### With go run

The second option is to use `go run` to execute a specific version of a tool without installing it. For
  example, to run the latest version of `govulncheck` you can use the following command:

I've written in detail about using `go run` to execute tools previously in
  [this post](https://www.alexedwards.net/blog/using-go-run-to-manage-tool-dependencies), but this option
  is really useful when there is a tool you want to quickly run on an ad hoc basis.

Personally, I often use `go run` in this way during code reviews, when I want to do a one-time run of a
  specific
  static analysis tool using the latest version.

I also find this approach useful in small solo projects where I don't have to worry about tool version differences
  with other developers. I'll often create a `Makefile` which uses `go run` to execute the latest
  version of code-quality tools —
  [similar to this](https://www.alexedwards.net/blog/a-time-saving-makefile-for-your-go-projects).

### With go tool

Lastly, there is now the option to add a tool as a *module tool dependency* to your `go.mod` file.
  At a very high level, you can use the `go get -tool` command to add the tool as a module dependency, and
  the necessary version information and checksums will be added to the `go.mod` and `go.sum`
  files. For example:

And then you can run the specific version of the tool listed in the `go.mod` file with the
  `go tool` command, like so:

This is a great option when you are working with a team of people, where for consistency and reproducibility you want
  to make sure that everyone is using exactly the same version of a tool.

I've previously written a much more detailed tutorial about how to use the `go tool` functionality, and I
  recommend
  [checking that out](https://www.alexedwards.net/blog/how-to-manage-tool-dependencies-in-go-1.24-plus)
  for more information.

## Development

### Using Gopls

Another major development in recent years has been [gopls](https://go.dev/gopls/). This is the official
  *language server* for Go, which you can use with any text editor or IDE that supports the
  [Language Server Protocol](https://microsoft.github.io/language-server-protocol/) (LSP).

If you're not already familiar with LSP, it's essentially a protocol that allows text editors to communicate with
  external programs called language servers, which act as the "brain" behind smart editor features.

The Go language server supports a [wide range](https://go.dev/gopls/features/) of smart editor features,
  including:

- Autocompletion
- Syntax highlighting
- Documentation on hover
- Comment and function collapsing
- Diagnostic checks that highlight invalid or bad-practice code
- Code navigation tools — including jump to definition, finding references, and finding implementations of a type
- Refactoring and formatting tools — including smart renaming, import statement organization, moving function parameter positions, and generating skeleton unit tests for a function

To use `gopls`, the first thing you need to do is install it on your computer using the
  `go install` command, like so:

Once `gopls` is installed, you then need to configure your editor to use it.

- If you're using **Zed** or **Helix**, they should automatically detect `gopls` on your machine and start using it without any additional setup.
- If you're using **VS Code**, you'll need to install the official Go extension. To do this, open the Extensions Panel, search for `golang.go`, and install this extension. After you restart and open a `.go` file, you should see a lightning bolt next to the Go version in the status bar at the bottom of your editor. This indicates that the language server is running.
- For other editors, the steps are a little more complicated. Please see the official setup steps for [Vim and Neovim](https://go.dev/gopls/editor/vim), [Emacs](https://go.dev/gopls/editor/emacs) and [Sublime Text](https://go.dev/gopls/editor/sublime).

Once your editor is configured, you should see smart editor features become available. For example, here's a
  screenshot of documentation when hovering over the `http.Error()` function in VS Code.

![](https://www.alexedwards.net/static/img/tooling/1.png)

### Viewing documentation and environment information

The `go doc` tool remains the de facto way to view the documentation for standard library packages in your
  terminal. You can use it to view the documentation for an entire package, or for a specific type, function or method.
  For example:

You can also use the `-src` flag to view the relevant source code:

Since Go 1.25, you can also use the `-http` flag to start a documentation server and browse the
  documentation locally in your web browser. For example, to view documentation for the `bytes` package in
  your browser you can run the following command:

To display information about your current Go operating environment, you can use the `go env` command. This
  can be particularly useful if you're working on an unfamiliar machine.

If there are specific values that you're interested in, you can pass them as arguments to `go env`. For
  example:

To show documentation for all `go env` variables and values you can run:

### Tidying and formatting code

If you have your text editor setup to use `gopls`, there is a good chance that your `.go` files
  will automatically be formatted according to the Go conventions each time they are saved, as well as having their
  `import` lines automatically added, removed and sorted as necessary.

If you're not using `gopls`, or you want to format files outside of your text editor (for example, as part
  of a pre-commit hook or CI pipeline), you can use the `gofmt` tool to format them. For example:

In these commands, the `-w` flag instructs the tool to rewrite files in place, the `-s`
  instructs the tool to apply certain
  [simplifications](https://pkg.go.dev/cmd/gofmt#hdr-The_simplify_command) to the code, and the
  `-d` flag instructs the tool to output diffs of the changes. If you want to only display the names of
  changed files, instead of diffs, you can swap this for the `-l` flag instead. Note that
  `gofmt` works recursively, so if you pass it a directory like `.` or `./cmd/foo`
  it'll format all `.go` files within that directory tree.

Alternatively, you can run the `go fmt` command — which is essentially a wrapper around
  `gofmt -l -w` — like so:

`
$ go fmt ./...
`

Often, as part of a quality audit check in a CI pipeline, I want to check that `.go` files are formatted
  correctly, without actually changing anything. To do this, I usually run `gofmt -l .` and check that the
  output from this command is empty. There's an example of this in the `audit` check in
  [this Makefile](https://www.alexedwards.net/blog/a-time-saving-makefile-for-your-go-projects).

It's also worth mentioning the
  [`goimports`](https://pkg.go.dev/golang.org/x/tools/cmd/goimports) tool, which formats your
  `.go` files in the same way as `gofmt`, but also updates your `import` lines —
  adding, removing and sorting the lines as necessary. You can run it like so:

### Tidying and formatting modfiles

You can use the `go mod tidy` command to automatically add missing dependencies to, and prune unused
  dependencies from, your `go.mod` and `go.sum` modfiles based on the imports in your
  `.go` files.

`
$ go mod tidy
`

It's a good idea to run this periodically to keep your modfiles synchronized with your code. Personally, I try to run
  this before each commit to make it easier to see exactly which code changes were responsible for adding or removing a
  dependency when looking through the version control history.

If you want to check if the modfiles are synchronized *without actually changing them*, you can use the
  `-diff` flag like so:

This is a really useful command to use in audit checks and CI pipelines, because when you run it with
  `-diff` it will print out any changes and then exit *with a non-zero code*. If no changes are
  needed, it will exit with code 0.

It's also worth mentioning that running `go mod tidy` ensures your modfiles include the dependencies
  needed across all possible build tag, OS and architecture combinations. Commands like `go run`,
  `go test` and `go build` are more selective, and only require dependencies for the current build
  configuration. This is why you might sometimes see additional lines appear in your modfiles unexpectedly when running
  `go mod tidy`.

### Debugging code

For debugging Go applications, the standard tool to use is [Delve](https://github.com/go-delve/delve). It
  allows you to set breakpoints, step through your code line by line, and do things like inspecting the values of
  variables and viewing the current call stack.

You can install Delve by running:

Nowadays, the easiest way to use Delve is generally via the debugger integration in your text editor. For example, in
  VS Code you set breakpoints by clicking in the gutter next to a line of code, start a debugging session by opening
  the 'Run and Debug' panel, and use the debugging toolbar to step through your application and inspect what's
  happening as it runs.

It's also possible to use Delve outside of a text editor and start an interactive debugging session in your terminal.
  For example, assuming you installed Delve using the `go install` command above, you could start debugging
  an application in the `./cmd/web` directory by running:

You can then use Delve's commands to set breakpoints, continue execution, step through your code, and inspect
  variables, in much the same way as in a text editor.

There is a nice introduction on how to use the terminal-based debugger
  [in this post](https://www.jamessturtevant.com/posts/Using-the-Go-Delve-Debugger-from-the-command-line/),
  and more information about debugging with Delve can be found in the
  [official Delve documentation](https://github.com/go-delve/delve/tree/master/Documentation).

### Modernizing code

Go 1.26 made major changes to the `go fix` command, updating it so that it now automatically 'modernizes'
  your code to use the latest Go idioms and standard library APIs. When you run it, it will do things like replacing
  `interface{}` with `any`, and rewrite code to use functions like
  `slices.Contains()` rather than manual loops.

You can see a complete list of the analyzers that `go fix` supports, and what they do, by running
  `go tool fix help`:

At its most basic, you can use `go fix` like this:

`
$ go fix ./...
`

However, it's important to be aware that `go fix` will silently rewrite your `.go` files in
  place. If you want to know in advance what changes it will make *without actually applying them* you can use
  the `-diff` flag like so:

Sometimes, when looking at the diff, you might decide that you want to make some, but not all, of the changes. For
  example, there have been times when I've decided that my original code was clearer without the modernizations applied
  by the `embedlit` and `mapsloop` analyzers. You can disable specific analyzers individually like
  so:

### Refactoring code

Since the release of `gopls`, the simplest, safest and most flexible way to refactor your code is by using
  its *code transformation features* in your text editor. For example, you can inline function calls, extract
  code into a function, rename identifiers, and move or remove parameters across your codebase, all in a few clicks.

For example, in VS Code you can use the 'Rename' and 'Refactor' options in the right-click menu to refactor code like
  so:

More information, including a description of all supported refactoring features, can be found in the official
  `gopls` [documentation](https://go.dev/gopls/features/transformation).

However, if you don't want to use `gopls`, or are using a text editor that doesn't support it, you can
  still use `gofmt` with the `-r` flag to implement a *rewrite rule* that can assist with
  certain refactoring tasks. I've written more about this in my 2019 blog post on Go tooling
  [here](https://www.alexedwards.net/blog/an-overview-of-go-tooling#refactoring-code).

### Live reloading

There are a few [live reloading](https://awesome-go.com/#build-automation) tools available for Go, which
  you can use to automatically rebuild and restart an application whenever certain files change. These are especially
  useful when developing web services, because they let you make changes to your code or template markup and then check
  the results in a browser without having to manually restart the application each time.

The most mature and popular live reloading tool for Go is
  [`air-verse/air`](https://github.com/air-verse/air). You can run it using settings in a TOML
  [configuration file](https://github.com/air-verse/air/blob/master/air_example.toml), like so:

Or you can configure it using command-line flags. For example, to watch all directories and rebuild the
  `./cmd/web` application whenever a file with an extension in the set `.go`,
  `.tmpl`, `.css`, `.js` or `.sql` changes, you could use the following
  command:

Here's a video illustrating the `air` live reloading functionality when developing a web application:

### AI coding assistants and MCP

Go's language server, `gopls`, includes an experimental MCP (Model Context Protocol) server that exposes
  some of its functionality to AI coding assistants (such as Claude Code or OpenAI Codex). This effectively allows the
  assistants to leverage the same "smart features" that your text editor has access to, rather than just relying on
  reading your files.

Assuming that you have `gopls` installed, you can configure your AI coding assistant to use the
  `gopls` MCP server by following the instructions in the
  [official Go MCP documentation](https://go.dev/gopls/features/mcp#coding-assistant-setup).

You can also run the `gopls mcp -instructions` command to get guidance for using the MCP server, which you
  can then provide to your coding assistant. For example:

Another MCP server worth mentioning is
  [`mrjoshuak/godoc-mcp`](https://github.com/mrjoshuak/godoc-mcp). This allows AI coding
  assistants to look up Go package documentation directly, which can be more token-efficient than reading through
  source files. You may wish to try this if you're using AI assistants heavily and want to reduce token usage.

## Code quality

### Security

In late 2022 the Go team released
  [`govulncheck`](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck), which checks your
  codebase against the [Go vulnerability database](https://vuln.go.dev/) to find known vulnerabilities in
  any standard library packages or third-party dependencies that you're using.

Unlike many other vulnerability scanners, it only flags vulnerabilities that actually affect you... meaning that a
  vulnerability in a part of a package that your code doesn't use won't be flagged.

It's an excellent tool, and I recommend running it routinely before you deploy a new version of your application to
  production.

Long term, the plan is for `govulncheck` to become part of the main `go` command, but for now
  you can run it like so:

Another really helpful tool is [`gosec`](https://github.com/securego/gosec), a static analyzer
  that looks for potential security problems in your code. You can run it like so:

In my experience it's not uncommon for `gosec` to flag issues which on further inspection are false
  positives in the context of your specific codebase, or where you are deliberately using something insecure. When this
  happens, you can annotate the specific code with a `#nosec` comment to instruct `gosec` to omit
  it from future reports. For example:

### Code correctness

#### go vet

The venerable `go vet` command should still be your first port of call when it comes to static code
  analysis. It runs a relatively small set of checks, but the checks have a high signal-to-noise ratio and if
  `go vet` reports an issue, then it's very likely to be a problem you should address.

It's normally best to run `go vet` with its default settings, like so:

`
$ go vet ./...
`

You can see a complete list of the checks that `go vet` runs in the 'Registered analyzers' section of the
  help documentation:

And you can also disable specific analyzers if you don't want their checks to run. For example, to disable the
  `composites` analyzer, which checks for unkeyed composite literals, you can run `go vet` like
  so:

#### Staticcheck

The [`staticcheck`](https://staticcheck.dev/) tool is kind of like `go vet` on
  steroids. It carries out around 160 different checks on your code — the vast majority of which are related to
  code correctness and performance, although it also includes a handful of checks for for 'stylistic' issues like comment
  formatting too.

The complete list of checks, along with their respective ID codes and descriptions, can be
  [found here](https://staticcheck.dev/docs/checks).

It's important to note that `staticcheck` does not run *all* checks by default — only a
  subset of them. But you can configure exactly which checks are run using either the `-checks`
  command-line flag or a [config file](https://staticcheck.dev/docs/configuration/). For example:

#### Nilaway

The [`nilaway`](https://github.com/uber-go/nilaway) tool is really useful for finding
  potential `nil`-pointer panics in your code. It's similar to the older
  [nilness](https://pkg.go.dev/golang.org/x/tools/go/analysis/passes/nilness) tool in what it aims to do,
  but is more comprehensive in its checks.

You can run it like so:

If you're not worried about `nil`-pointer panics in your test code, and only want to check your production
  code, you can also run it with the `-exclude-test-files` flag enabled. Like so:

#### Errcheck

The [`errcheck`](https://github.com/kisielk/errcheck) tool has been around for a long time (14
  years!), and it remains a great way to check for unhandled errors in your code.

You can run it with its default settings like so:

It's worth mentioning that, by default, `errcheck` only reports errors which are
  *completely unhandled*. It doesn't report errors that are handled by ignoring them and assigning them to the
  blank identifier `_`.

To include these errors in the report, you can run it with the `-blank` flag enabled, like so:

It's worth noting that not every error always needs to be handled. For example, it's conventional to ignore
  errors returned by `http.ResponseWriter.Write()`, or errors from `fmt.Fprint()` when writing to
  standard streams. Or you might deliberately choose to ignore errors from nice-to-have non-critical cleanup
  operations, where you decide that handling errors would add more complexity to your codebase than it's worth.

So it's possible to exclude specific functions from the `errcheck` report by creating an
  [exclude file](https://github.com/kisielk/errcheck#excluding-functions) and passing it via the
  `-exclude` flag like so:

#### Shadow

It's also worth mentioning the
  [`shadow`](https://pkg.go.dev/golang.org/x/tools/go/analysis/passes/shadow) tool, which
  identifies instances of variable shadowing in your code.

This tool was also built by the Go team and has been around for a very long time, but has never been included in the
  default `go vet` analyzers or the `go` command because it is
  [notoriously noisy](https://github.com/golang/go/issues/75342) and reports a lot of instances of variable
  shadowing that aren't actually problematic.

Nonetheless, it's still worth knowing that it exists. Personally, I do use `shadow` occasionally when I'm
  doing a code review of a large codebase, and skim through the results to see if anything jumps out as looking
  unexpected or out of place.

You can run `shadow` like so:

### Code hygiene

#### Revive

The `revive` tool is a *code linter*, and is kind of the spiritual successor to the now frozen and
  deprecated [`golang/lint`](https://github.com/golang/lint) package.

There is some overlap between `revive` and the `staticcheck` tool that we talked about earlier,
  but `revive` focuses *more* on checking code style and conventions, whereas
  `staticcheck` focuses *more* on finding bugs and performance issues.

Generally, `revive` is good to use on projects where you have multiple contributors and you want to
  maintain common standards in terms of code and comment style.

You can run it with its default settings like so:

Normally though, I prefer to run it using the `-formatter=stylish` flag, which groups failures by file and
  includes links to the specific documentation for each failure.

You can also disable and customize specific checks by creating a TOML
  [configuration file](https://revive.run/docs/#configuration) and passing it via the
  `-config` flag, like so:

#### Deadcode

[`Deadcode`](https://go.dev/blog/deadcode) is an excellent tool for finding functions in your
  code that aren't being used, which you can potentially delete or comment out. Similar to
  `govulncheck`, the `deadcode` tool is officially maintained by the Go team, but isn't
  currently part of the `go` command.

You can run `deadcode` with the default settings like this:

But it's important to note that by default, `deadcode` does not consider code in `_test.go`
  files when checking if something is used or not. This means that functions which are only used by your tests can
  incorrectly be reported as dead code. So to make sure test files are included in the check, I almost always run
  `deadcode` with the `-test` flag enabled, like so:

Another neat way to use `deadcode` is when you are looking at a function and can't figure out why it
  exists, or you're struggling to fully trace where it is being called from.

If you run `deadcode` with the `-whylive` flag, you'll get a report showing the shortest path
  from a `main()` function in your program to the code in question. For example, let's say you have the
  module `example.com`, and you wanted to trace where the
  `internal/response.HTMLRenderer.Render()` method is being called from, you can run a command like this:

#### Wrapcheck

If you've made the decision in your codebase to wrap errors before returning them to the caller (which is generally a
  good idea to help with debugging), the `wrapcheck` tool helps you find any instances where you've
  forgotten to do this.

You can run it with:

### Running multiple tools

If you are running a lot of tools as part of your code quality checks, you might want to consider
  [`Golangci-lint`](https://golangci-lint.run) to help with this. It acts as a wrapper around
  many of the tools we've talked about above, running them in parallel and outputting the results in a single
  consistent format.

Alternatively, and slightly more simply, I often use a Makefile with a single `audit` task that runs the
  tools I want, similar
  [to this](https://www.alexedwards.net/blog/a-time-saving-makefile-for-your-go-projects).

## Dependency management

### Managing Go versions

Personally, when I want to upgrade to a new version of Go on my primary development machine, I have a simple Bash
  script that I run to download and install the new version. The script and instructions are
  [available here](https://x.com/ajmedwards/status/1727342272856080433) if you'd like to take a similar
  approach. I then run it like:

Sometimes it's useful to have multiple versions of Go installed on your machine. For example, you might want to test
  your code against different Go releases, or try out a new version without replacing your existing one.

You can do this using the `go install golang.org/dl/...` command. For example, to install Go 1.26.0
  alongside your existing Go installation, you can run:

You can then use this alternative version by running the versioned executable instead of `go`. For
  example:

It's important to note, though, that Go 1.21 and newer support automatic toolchain switching. So running a versioned
  Go command *inside a module that requires a newer toolchain* may cause Go to
  [automatically download and use](https://go.dev/doc/go1.21#tools) that newer version instead. If you want
  to disable this, you can set the `GOTOOLCHAIN` environment variable to `local`, like so:

### Checking for dependency updates

To check for dependency updates, the best tool around is probably
  [`oligot/go-mod-upgrade`](https://github.com/oligot/go-mod-upgrade). You can run it like so:

This launches an interactive tool which lists all dependencies that have upgrades available. You can then select the ones
  you want, and they'll be upgraded to the latest available version.

### Using local dependencies and workspaces

In the past, if you want to use a modified version of a dependency (for example, you temporarily want to use a local
  fork until a patch is merged upstream), you would use the `go mod edit` command to add a
  `replace` rule to your `go.mod` file pointing to the modified version, as
  [described here](https://www.alexedwards.net/blog/an-overview-of-go-tooling#managing-dependencies).

Although this approach does still work, an alternative option is to create a
  [Go workspace](https://go.dev/doc/tutorial/workspaces) and a `go.work` file in your module
  root.

For example, assuming that you are in the root of your module, and the modified dependency you want to use is located
  in the directory `/local/code/mydep`, you can create a workspace and a `go.work` file that
  references the current module and modified dependency like so:

The `go.work` file that is created should then look like this:

And when you run the code in your module, the modified dependency should be picked up and used, rather than
  resolving the dependency from the module cache in the normal way. Note that the dependency still needs its own
  `go.mod` file, and that the dependency's module path must match the import path your code uses.

Go workspaces are also really useful in the scenario where you are developing two modules at the same time which rely
  on each other. When you want to do this, you can create a `go.work` file in the *parent directory*
  of the two modules, which points to the two module directories. For example, if you have two modules located at
  `/local/code/a` and `/local/code/b`, you could create a `go.work` file in
  `/local/code` that references them both like so:

For more information about Go workspaces and `go.work` files, please see the
  [official tutorial](https://go.dev/doc/tutorial/workspaces).

### Tracing and visualizing dependencies

If you ever look at your `go.mod` or `go.sum` files and wonder "why is *that* listed as
  a dependency?", you can find out by running the `go mod why` command. This will show you the shortest path
  from a package in your main module to a given dependency. For example, to see why `golang.org/x/sys` is
  listed as a dependency you can run:

It's also worth knowing about the `go mod graph` command, which prints a plain-text module requirement
  graph.

`
$ go mod graph
`

The output from this tool is just a plain text listing, not a visual graph, but I've had some success with dumping
  the output from `go mod graph` into AI tools and asking them to generate a visualization. Alternatively, if
  you want something more reliable and reproducible, you might want to consider trying the
  [`samber/go-mod-graph`](https://github.com/samber/go-mod-graph) and
  [`bayraktugrul/modview`](https://github.com/bayraktugrul/modview) tools, which will generate
  visualizations for you.

### Clearing downloaded dependencies

Downloaded dependencies are stored in the *module cache* on your computer. If you're not sure where your
  module cache is located, you can check by running the `go env GOMODCACHE` command.

If you ever want to clear the module cache — which can be useful if your cache has become corrupted or want to
  rule it out as the source of a bug — you can use the `go clean` tool like so:

But be aware that this is a blunt instrument — it will remove the downloaded dependencies for
  *all* projects on your machine.

## Testing

### Running tests

You can use the `go test` tool to run the tests in your project like so:

If the code you’re testing leverages concurrency, or you’re running
  [tests in parallel](https://medium.com/@bjlee72/go-test-parallelism-cf230fc44a78), then you may want to
  use the `-race` flag to enable Go's [race detector](https://go.dev/doc/articles/race_detector)
  during the tests. This will increase the running time of the tests, but it's an easy tweak that can help find data
  races that occur while the tests are running.

`
$ go test -race ./...
`

If any of your tests need access to VCS information in `debug.BuildInfo`, you should also make sure to use
  the `-buildvcs` flag when running tests, like so:

If you want to only run some specific tests, rather than all the tests in a package, there are a few ways to do this.

If you're using VS Code or GoLand as your text editor, the simplest way is via the testing functionality built into
  your editor. For example:

If you're not using an editor that supports this kind of functionality, you can also use `go test` with
  the `-run` flag to run specific tests. This accepts a regular expression, and only tests which have names
  that match the regular expression will be run. When using this, I normally also use the `-v` flag to
  enable verbose output, so I can make sure that the tests I expect are actually being run 🙂

It's also worth mentioning that Go caches test results at the package-level. If a package hasn't changed between test
  runs, then the cached test result will be displayed with a `"(cached)"` annotation next to it. If you want
  to force your tests to run in full, you can use the `-count=1` flag, or mark cached test results as
  expired by using the `go clean` tool.

A final flag that I sometimes use is `-failfast`, which will stop further tests
  *in a package* from running after the first failure.

Note that if you're running tests in multiple packages (for example by using `go test ./...` ), then the
  tests in the other packages which didn't have the failure will continue to run.

As an alternative to `go test`, you may also want to consider using the
  [`gotestyourself/gotestsum`](https://github.com/gotestyourself/gotestsum) tool. This is
  effectively a wrapper around `go test` which prints the test output in a nice way, similar to this:

![](https://www.alexedwards.net/static/img/tooling/8.png)

### Profiling test coverage

It's also possible to enable test coverage analysis when running tests by using the `-cover` flag. This
  will display the percentage of code covered by the tests in the output for each package, similar to this:

Alternatively, you can use the `-coverprofile` flag to generate a *coverage profile* and view it in
  your browser by using the `go tool cover -html` command like so:

![](https://www.alexedwards.net/static/img/tooling/9.png)

This will give you a navigable listing of all the test files, with code covered by the tests displayed in green, and
  uncovered code in red.

If you want you can go a step further and set the `-covermode=atomic` flag to make the coverage profile
  record the exact number of times that each statement is executed during the tests.

When viewed in the browser, statements which are executed more frequently are shown in a more saturated shade of
  green, similar to this:

![](https://www.alexedwards.net/static/img/tooling/10.png)

If you don't have a web browser available to view a coverage profile, you can see a breakdown of test coverage by
  function/method in your terminal with the command:

### Load testing

For quick and simple load testing of a web application or API, one of the best tools around is
  [`rakyll/hey`](https://github.com/rakyll/hey). For example, if you want to load test the
  `http://localhost:5051` endpoint by sending 10,000 requests with up to 100 concurrently, you can do so
  like this:

The output includes useful information such as the number of requests per second, response-time distributions, and
  summary counts of HTTP response status codes.

`hey` supports a bunch of configuration options, which you can find by running:

Alternatively, if you want a more sophisticated general-purpose load testing tool, you may want to consider
  [`tsenart/vegeta`](https://github.com/tsenart/vegeta) or
  [`grafana/k6`](https://github.com/grafana/k6), both of which are written in Go (although k6
  test scenarios are typically written in JavaScript).

### Stress testing

Occasionally you might want to stress test something in your application by running a test multiple times in
  succession. This can be useful for checking for sporadic or intermittent failures, or when you're trying to reproduce
  an intermittent bug that you've been seeing.

There are a couple of ways to do this, but the simplest is by using the `go test` flag
  `-count`. For example, to run the `TestFooBar` test 500 times, you could run:

It's important to note that `-count` repeats test executions in serial. Tests containing a
  `t.Parallel()` instruction can still run concurrently with other parallel tests within each execution, but
  the repeated executions themselves won't overlap.

If you want to repeat the same test multiple times in parallel, you can use the
  [`stress`](https://pkg.go.dev/golang.org/x/tools/cmd/stress) tool.

To use the `stress` tool, you'll first need to compile a test binary for the specific package you want to
  test. You can do this using the `go test -c` command. For example, to create a test binary for the
  package in your current directory:

In this example, the test binary will be output to `/tmp/foo.test`. You can then use the
  `stress` tool to execute a specific test in the test binary like so:

Note: In the example above I've used the `-p` flag to restrict the number of parallel processes used by
  `stress` to 4. Without this flag, the tool defaults to using a number of processes equal to
  `runtime.NumCPU()`.

### Fuzz testing

Go 1.18 introduced support for fuzz testing, which makes it possible to run tests with randomly generated inputs in
  an attempt to find bugs and unhandled edge cases.

For example, let's say that you have a `Slugify()` function which takes input text like
  `"An example string"` and turns it into a slug like `"an-example-string"`.

You could create a `FuzzSlugify` fuzz test for it like so:

In this example, the calls to `f.Add()` provide some *seed corpus* values for the fuzz test, which
  give Go a starting point for generating additional inputs. You don't *need* to provide seed values, but it's
  generally a good idea to include a few representative examples.

When you run `go test ./...` in the normal way, the `FuzzSlugify` test will be run, but only
  using the seed corpus values.

To actually trigger fuzzing, you need to run it with the `-fuzz` flag. This takes a regular expression
  matching the name of the specific fuzz test you want to run. It's only possible to run one fuzz test at a time, and
  if multiple fuzz tests match the regular expression you'll get an error saying
  `-fuzz matches more than one fuzz test`.

You also need to pass in the path to the package that contains the fuzz test — you cannot use
  `./...`.

So, for example, to execute the `FuzzSlugify` fuzz test in the `./cmd/web` package, you would
  run the following command:

In this example, the fuzz test found a problem with the `Slugify()` function — specifically, when the
  input text is
  `"0\t0"`, the whitespace `\t` character is not removed. It's also important to note that, in
  this example,
  a file has been created at
  `testdata/fuzz/FuzzSlugify/dde7a120ccdf11af` containing the failing input. This input will be included in
  the seed corpus every time you run `go test` in the future (even when not using the `-fuzz`
  flag), so that the bug doesn't accidentally get reintroduced.

Fuzzing will continue indefinitely until either a failure is found or you terminate the run manually (e.g. with
  `Ctrl+C`). If there are no problems found, you'll see output which looks similar to this:

The "new interesting" count is the number of inputs discovered that increase the code coverage observed by
  the fuzzer. When the number of "new
  interesting" inputs starts to plateau, it can be a sign that you're not getting much additional coverage from
  continuing the test and you may want to terminate it.

Alternatively, you can set a fixed runtime for the fuzz test using the `-fuzztime` flag. For example, to
  run it for 30 seconds:

For more information, I'd recommend checking out the official
  [Go fuzzing documentation](https://go.dev/doc/security/fuzz/) and the
  [getting started tutorial](https://go.dev/doc/tutorial/fuzz).

## Building and working with binaries

### Verifying dependencies

Before compiling your application, it's sensible to run `go mod verify` to check that the dependencies in
  your module cache haven't been modified since they were downloaded.

`$ go mod verify
`

I normally run `go mod verify` immediately before running `go build`, as part of an automated
  build process in a CI workflow or Makefile task. This helps to make sure that builds are reproducible, and you're not
  using an accidentally modified dependency during compilation.

### Building a binary

To compile a `main` package and create an executable binary you can use the `go build` tool.
  Typically I use it in conjunction with the `-o` flag, which lets you explicitly set the output directory
  and name of the binary like so:

In these examples, `go build` will compile the specified package (and any dependent packages), then
  invoke the linker to generate an executable binary, then output this to `/tmp/foo`.

It's important to note that the `go build` tool caches build output in the
  [build cache](https://pkg.go.dev/cmd/go#hdr-Build_and_test_caching). This cached output will be reused
  again in future builds where appropriate, which can significantly speed up the overall build time.

Using the build cache comes with one important caveat — it does not detect changes to C libraries imported
  with `cgo`. So if your code imports a C library via `cgo` and you've made changes to it since
  the last build, you'll need to use the `-a` flag which forces all packages to be rebuilt. Alternatively,
  you could use `go clean` to purge the cache:

If you ever want detailed output explaining precisely what `go build` is doing behind the scenes, you can
  use the `-v` flag to print package names as they are being compiled, or the `-x` flag to print
  the detailed commands that are being run. You'll probably want to use these in conjunction with the `-a`
  flag, because otherwise you might not see much output as Go reuses packages from the build cache rather than
  recompiling them.

Finally, if you run `go build` on a non-`main` package, it will be compiled in a temporary
  location and again, the result will be stored in the build cache. No executable binary will be produced.

### Cross-compilation

By default, `go build` will output a binary suitable for use on your current operating system and
  architecture. But it also supports cross-compilation, so you can generate a binary suitable for use on a different
  machine. This is particularly useful if you're developing on one operating system and deploying on another.

You can specify the operating system and architecture that you want to create the binary for by setting the
  `GOOS` and `GOARCH` environment variables respectively. For example:

To see a list of all supported OS/architecture combinations you can run go tool dist list:

For more information about cross compilation, I recommend reading
  [this post](https://rakyll.org/cross-compilation/).

### Compiler and linker flags

When building your executable, you can use the `-gcflags` and `-ldflags` flags to change the
  behavior of the compiler and linker and see more information about what it's doing. You can see a complete list of
  available compiler and linker flags by running:

Probably the most well-known and commonly-used of these is the linker `-X` flag, which allows you to
  "burn in" a (string) value to a specific variable in your application. For example, to burn in the value "bar" into
  the `main` package's global `foo` variable you can use it like so:

For more information about the `-X` flag and some sample code see [this Stack Overflow
    question](https://stackoverflow.com/questions/11354518/golang-application-auto-build-versioning).

### Stripping debug information and reducing binary size

It's possible to reduce the binary size — typically by around 25% — by instructing the linker to strip
  [symbol
    tables](https://medium.com/a-journey-with-go/go-how-to-take-advantage-of-the-symbols-table-360dd52269e5) and [DWARF](https://golang.org/pkg/debug/dwarf/) debugging information from the binary. We
  can do this by using the `-s` linker flag, like so:

It's not a Go-specific tool, but you can also use a tool like [`upx`](https://upx.github.io/)
  to compress the binary size further if you want. Please see
  [this post](https://words.filippo.io/shrink-your-go-binaries-with-this-one-weird-trick/) for more
  information.

### Inspecting binaries and reproducible builds

Once you have generated a binary, you can use the `go tool buildid` command to inspect its *build
    ID*. This
  is an identifier embedded in the binary by Go, representing the inputs to the build (code, compiler
  version, flags, etc.) and the resulting output. It acts as a "fingerprint" for the build, and is also used
  internally by Go's build cache.

For example, to check the build ID for the binary at `/tmp/foo`, you can run:

Looking at the build ID can be useful when checking for reproducible builds, as identical builds should produce the
  same ID. If two builds produce different IDs, it suggests that something about them is different.

For more information about Go build IDs and reproducibility, please see
  [this post](https://alexanderobregon.substack.com/p/go-build-id-and-reproducibility).

Another useful tool is the `go version -m` command, which lets you inspect a binary's build information —
  including the Go version, the module it was built from, its dependencies and VCS information. To inspect the binary
  at `/tmp/foo`, you can use it like so:

## Diagnosing problems and making optimizations

### Running and analyzing benchmarks

A nice feature of Go is that it makes it easy to benchmark your code. If you're not familiar with the general process
  for writing benchmarks there's a good guide
  [here](https://dave.cheney.net/2013/06/30/how-to-write-benchmarks-in-go).

To run benchmarks you need to use the `go test` tool, with the `-bench` flag set to a regular
  expression that matches the benchmarks you want to execute. If you don't want to run regular non-benchmark tests,
  you should omit them by using the `-run=^$` flag. For example:

I almost always run benchmarks using the `-benchmem` flag, which includes memory allocation statistics in
  the output.

By default, each benchmark test will be run for a minimum of 1 second, once only. You can control this with the
  `-benchtime` and `-count` flags:

If the code that you're benchmarking uses concurrency, you can use the `-cpu` flag to see the performance
  impact of changing your `GOMAXPROCS` value (essentially, the number of OS threads that can execute your Go
  code simultaneously). For example, to run benchmarks with `GOMAXPROCS` set to 1, 4 and 8:

To help analyze the results of the benchmarks, you can use the
  [`benchstat`](https://pkg.go.dev/golang.org/x/perf/cmd/benchstat) tool. This replaces the
  older [`benchcmp`](https://pkg.go.dev/golang.org/x/tools/cmd/benchcmp) tool, which is now
  deprecated.

When you are using the `-count` flag to run benchmarks multiple times, you can use
  `benchstat` to easily see the median value and confidence interval across all the runs. For
  example:

You can also use it to compare benchmarks before and after a specific change. For example:

### CPU, memory and goroutine profiling

Go makes it possible to create diagnostic profiles for CPU use, memory use, goroutine blocking and mutex contention.
  You can use these to dig a bit deeper and see exactly how your application is using (or waiting on) resources.

There are three ways to generate profiles:

- If you have a web application you can import the `net/http/pprof` package. This registers handlers with http.DefaultServeMux, which you can then use to access profiling data from your running application. If you're using a different mux, you'll need to register the handlers with it yourself. This post provides a good explanation and some sample code.
- For other types of applications, you can profile your running application using the pprof.StartCPUProfile() and pprof.WriteHeapProfile() functions. See the `runtime/pprof` documentation for sample code.
- Or you can generate profiles while running benchmarks or tests by using the various -***profile flags. For example:

Using the `-***profile` flags when running benchmarks or tests will result in a test binary being
  outputted to your current directory. If you want to output this to an alternative location you should use the
  `-o` flag like so:

My favourite way to inspect a profile is to use the `go tool pprof -http` command to open it in a web
  browser. For example:

![](https://www.alexedwards.net/static/img/tooling/11.png)

This will default to displaying a flame graph visually showing where your application is spending its resources, with
  wide boxes being the 'hot spots'.

You can also navigate to other views of the profile including top usage by function and source code:

![](https://www.alexedwards.net/static/img/tooling/12.png)

And also a graph showing the execution tree for your application, like this:

![](https://www.alexedwards.net/static/img/tooling/13.png)

If the amount of information is overwhelming, for CPU profiles you might want to use the
  `-nodefraction` flag to ignore nodes that account for less than a certain percentage of samples. For
  example, to ignore nodes that appear in less than 10% of samples you can run `pprof` like so:

And finally, if you're analyzing profiles for a web application created via `net/http/pprof`, you can also
  fetch the
  profile from the application and open the visualization in one step. For example, if your web application is running
  on `http://localhost:4000` you could generate a 30-second CPU profile and view it like so:

For more information about profiling and `pprof`, please see the official
  [README](https://github.com/google/pprof/blob/main/doc/README.md).

### Profile-guided optimization

Go also supports profile-guided optimization (PGO), which allows the compiler to use information gathered from
  profiling your application to make better decisions when compiling your code.

Normally, when compiling your code, the compiler has to make educated guesses about which functions are likely to be
  called frequently, which code paths are more common, and where it should make optimizations. PGO allows
  you to provide a CPU profile from a representative run of your application so that the compiler can make
  better-informed decisions.

For example, it may use this information to more aggressively inline frequently called functions, or optimize common
  code paths.

The good news is that using PGO is relatively straightforward. First you need to generate a CPU profile using one of
  the
  techniques described in the previous section. Then you need to pass it to `go build` via the
  `-pgo` flag when building your application. For example, if your CPU profile is saved as
  `/tmp/cpuprofile.out`, you can use it like so:

Alternatively, you can rename your profile to `default.pgo` and place it in the directory containing your
  `main` package. Go will automatically detect this file and use it when building your application, so you
  don't need to specify the `-pgo` flag explicitly.

In practice, the recommended workflow is to collect a representative profile from your production application, use
  that profile when building your next release, and periodically collect new profiles as your application evolves.

For more information, see the official [PGO
    documentation](https://go.dev/doc/pgo) and the [Go blog post introducing PGO](https://go.dev/blog/pgo).

### Execution tracing

Sometimes profiling isn't enough to understand what's happening in your application. For example, a CPU profile can
  show you which functions are consuming the most CPU time, but it won't necessarily help you understand why a goroutine
  is
  blocked, why your application isn't making progress, or why a request is taking so long.

For these situations, Go has a built-in execution tracer, which has been improved significantly in recent Go
  versions. It records runtime events such as goroutine scheduling, system calls, garbage collection, and other
  activity over a period of time. You can then use the `go tool trace` command to visualize and explore what
  happened.

You can generate a trace from your tests or benchmarks, use `net/http/pprof` to create and download a
  trace for your web application, or use the `runtime/trace` package to generate traces from a running
  application. You can then use `go tool trace` to view the output in your web browser. For example:

This will open an interactive visualization that lets you explore what was happening during the trace.

![](https://www.alexedwards.net/static/img/tooling/14.png)

For more information, please see the [Go blog post on tracing](https://go.dev/blog/execution-traces-2024),
  the [`runtime/trace`](https://pkg.go.dev/runtime/trace) documentation, as well as this
  [dotGo conference talk](https://www.youtube.com/watch?v=mmqDlbWk_XA) by Rhys Hiltner.

### Race detection

I talked earlier about enabling Go's race detector during tests by using `go test -race`. But you can
  also enable it for running programs when building an executable, like so:

It's critical to note that race-detector-enabled binaries will use more CPU and memory than normal, so you shouldn't
  use the `-race` flag when building binaries for production under normal circumstances.

But you may want to deploy a race-detector-enabled binary on one server within a pool of many. Or use it to help
  track down a suspected race condition by using a load-test tool to throw traffic concurrently at a
  race-detector-enabled binary.

By default, if any races are detected while the binary is running, a report will be written to `os.Stderr`.
  You can
  change this by using the [`GORACE`](https://go.dev/doc/articles/race_detector#Options)
  environment variable if necessary. For example, to run the binary located at `/tmp/foo` and output any race
  reports to
  `/tmp/race.<pid>` you can use:

Another complementary tool for helping to track down race conditions is
  [`amit-davidson/Chronos`](https://github.com/amit-davidson/Chronos). This uses static analysis
  of your code to try to identify race conditions, rather than using real-time detection like Go's race detector. This
  means it can be a good option to try if there is a suspected race condition that you are struggling to
  replicate.

## Reporting bugs

If you're confident that you've found an unreported issue with Go's standard library, tooling or documentation, you
  can use the `go bug` command to create a new GitHub issue.

`
$ go bug
`

This will open a browser window containing a GitHub issue pre-filled with your system information and reporting
  template.

##### If you enjoyed this post...

You might like to check out my [other Go tutorials](https://www.alexedwards.net/blog/topic) on this site, or if you're after
            something more structured, my books [Let's Go](https://lets-go.alexedwards.net?as=bb) and [Let's Go Further](https://lets-go-further.alexedwards.net) cover how to build complete,
            production-ready, web apps and APIS with Go.
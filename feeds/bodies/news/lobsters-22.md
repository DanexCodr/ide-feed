gohawk is an industrial-grade static analyzer that finds resource
    management and concurrency issues in Go code. It has been used to find and fix bugs in
    [Docker](https://github.com/moby/moby/pull/53517), [Kubernetes](https://github.com/kubernetes/kubernetes/pull/142429), and [Caddy](https://github.com/caddyserver/caddy/pull/7968).

### Better together

gohawk complements your existing analyzers such as `go vet`, Staticcheck, and
    go-critic; it does not try to replace them.

### Easy to drop in

gohawk runs as a standalone tool or as a `go vet` tool. No configuration file,
    and every check is a command-line flag.

### Analysis features

gohawk analyzers are primarily focused on enforcing reliability around resource management,
    concurrency, and error handling.

### Rich diagnostics

Each finding pinpoints the offending code with a precise source span, shows the evidence
    behind it, such as the return that leaks a file, and says how to fix it.
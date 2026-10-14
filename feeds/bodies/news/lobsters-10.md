I’m very pleased to announce the release of
[Factor](https://factorcode.org) 0.102!

| OS/CPU | Windows | macOS | Linux |
| --- | --- | --- | --- |
| ARM64 |  | [0.102](https://downloads.factorcode.org/releases/0.102/factor-macos-arm-64-0.102.dmg) |  |
| x86 | [0.102](https://downloads.factorcode.org/releases/0.102/factor-windows-x86-32-0.102.zip) |  | [0.102](https://downloads.factorcode.org/releases/0.102/factor-linux-x86-32-0.102.tar.gz) |
| x86-64 | [0.102](https://downloads.factorcode.org/releases/0.102/factor-windows-x86-64-0.102.zip) | [0.102](https://downloads.factorcode.org/releases/0.102/factor-macos-x86-64-0.102.dmg) | [0.102](https://downloads.factorcode.org/releases/0.102/factor-linux-x86-64-0.102.tar.gz) |

**Source code**: [0.102](https://downloads.factorcode.org/releases/0.102/factor-src-0.102.zip)

This release includes 1,068 commits from the following contributors:

> Aleksander Sabak, Andrii Puhachenko, Chris Double,
> Dmitry Matveyev, Doug Coleman, Eric Willigers, Giftpflanze,
> John Benediktsson, Leo Mehraban, Rudi Grinberg, Sebastiaan Speck,
> Zoltán Kéri, [@knottio](https://github.com/knottio),
> [@ronnie-w](https://github.com/ronnie-w)

Highlights of this release include:

- Working native ARM64 support on macOS, Linux, and Windows!
- A new GTK4 UI backend, now the default on 64-bit Linux; 32-bit Linux continues to use GTK3, which remains a build option on other supported Linux architectures.
- New 32-bit and 64-bit RISC-V Linux ports, with optimizing compiler backends, foreign calls and callbacks, and support in both the C++ and Zig VMs.
- DirectWrite text rendering on Windows, including color glyphs, typography controls, and better support for large output and complex scripts.
- More responsive rendering and selection of large text across platforms, with fixes for display scaling, listener scrolling, and adjacent text backgrounds.
- Experimental register allocators and optional compiler optimizations, alongside fixes to stack inference, generated code, and GC root tracking.
- Updated Unicode data to 18.0.0 and timezone data to 2026c, with bindings for SQLite 3.53.4, Raylib 6.0, and Lua 5.5.
- Faster process launching and native process-exit notifications on Linux, macOS, BSD, and Windows, with polling as a fallback.
- Extensive fixes to HTTP parsing, TLS identity checks, cooperative waits, resource cleanup, signal handling, and VM memory safety.

### Compatibility notes

- 64-bit Linux builds now select GTK4 by default; use -ui-backend=gtk3 when bootstrapping if GTK3 is required. 32-bit Linux uses GTK3 and does not support GTK4.
- Windows UI text now uses DirectWrite by default, so text metrics and appearance may differ from the previous Uniscribe backend.
- callable is now a mixin that includes words; code that assumes all callables support the sequence protocol should use quotation-like instead.
- Fixed-array struct fields now validate input buffer lengths, and stricter HTTP and multipart parsing rejects malformed or incomplete input previously accepted.
- PEG repetition and list parsers now omit ignore values. Minimum counts refer to successful matches, so repeat1 and list-of-many can return empty output when all matched items are hidden.
- The buffered HTTP client now decompresses gzip responses before character decoding and rejects unsupported content codings. with-http-request still provides bytes before content decompression.
- Ambiguous Objective-C selectors now require a class-qualified name such as Class.selector when imported signatures differ.
- Tuple literals reject duplicate slot names, and minimum and maximum now throw for empty iota and repetition instead of returning a value.
- Command-line option names and aliases must now be unique, including the default --help option. Exact names take precedence over no- negation.
- SQLite connections now use persistent WAL mode, which requires a local filesystem. with-transaction uses BEGIN IMMEDIATE and acquires the write lock at transaction start, including for read-only work. Write serialization is per process; wrap raw SQL and DDL writes in with-transaction or serialize-transaction to participate.

### What is Factor?

Factor is a [concatenative](https://www.concatenative.org/), stack-based
programming language with [high-level
features](https://concatenative.org/wiki/view/Factor/Features/The%20language)
including dynamic types, extensible syntax, macros, and garbage
collection. Factor has a [full-featured
library](https://docs.factorcode.org/content/article-vocab-index.html),
supports many platforms, and has extensive documentation.

The implementation is [fully
compiled](https://concatenative.org/wiki/view/Factor/Optimizing%20compiler)
for performance, while still supporting [interactive
development](https://concatenative.org/wiki/view/Factor/Interactive%20development).
Factor applications are portable across supported platforms and can be
[deployed as standalone
applications](https://concatenative.org/wiki/view/Factor/Deployment). Full source code for the Factor project is available
under a BSD license.

### New libraries

- alien.c-types.varargs: added ABI-aware argument promotion and type support for C variadic calls.
- alien.varargs: added ARM64 variadic callbacks and native argument-list access through va-arg, va-copy, and va_list.
- benchmark.neon: added benchmarks for ARM64 SIMD and optional NEON extensions.
- benchmark.spawn-cat: added a subprocess-launch benchmark with a Bun comparison.
- bootstrap.compat: added compatibility support for refreshing older images, including upgrades to ARM64 callback templates.
- checksums.cityhash: added pure Factor implementations of non-cryptographic CityHash32, CityHash64, and CityHash128, with seeded 64-bit and 128-bit variants.
- checksums.farmhash: added portable FarmHash checksums with stable 32-bit, 64-bit, and 128-bit fingerprints and seeded variants.
- compiler.cfg.linear-scan.checker: added checks for register assignments and preservation of live values during linear-scan allocation.
- compiler.cfg.loop-optimization: added optional loop preheaders and conservative integer loop-invariant code motion.
- compiler.cfg.memory-optimization: added optional reuse of managed-object slot loads across basic blocks.
- compiler.cfg.metrics: added compiler pass timings, allocation statistics, and register-allocator comparison tools.
- compiler.cfg.multiply-negate: added a compiler pass that combines a multiply followed by negation when its result has a single use.
- compiler.cfg.register-allocation: added a common interface for selecting register allocators while retaining linear scan as the default.
- compiler.cfg.register-allocation.backtracking: added an experimental allocator using bundle splitting, eviction, and affinity-based spill decisions.
- compiler.cfg.register-allocation.chordal: added an experimental SSA graph-coloring allocator with chordality checks and spill repair.
- compiler.cfg.register-allocation.greedy: added an experimental allocator using eviction, recoloring, and loop-aware region splitting.
- compiler.cfg.register-allocation.rematerialization: added optional regeneration of inexpensive integer constants instead of loading them from spill slots.
- compiler.cfg.register-allocation.verifier: added an optional final allocation verifier for value flow, operand constraints, spills, and GC roots.
- compiler.cfg.slp: added optional packing of independent integer expression trees into SIMD operations.
- compiler.cfg.value-numbering.global: added optional global value numbering using the production compiler’s rewrite rules.
- compression.deflate: added raw DEFLATE compression and decompression in Factor, including stored, fixed-Huffman, and dynamic-Huffman block decoding and malformed-input checks.
- cpu.arm.64.abi: added shared ARM64 ABI classification for aggregates, callbacks, and variadic arguments.
- cpu.arm.64.features: added runtime ARM64 feature detection with Linux, macOS, and Windows implementations.
- cpu.riscv.32: added an RV32GC optimizing compiler backend, assembler, and ILP32D foreign-call ABI support.
- cpu.riscv.64: added an RV64GC optimizing compiler backend, assembler, and LP64D foreign-call ABI support.
- crypto.chacha20: added the IETF ChaCha20 stream cipher with byte-array and string encryption helpers.
- crypto.poly1305: added RFC 8439 Poly1305 authentication tags and verification with 32-byte one-time keys and constant-time tag comparison.
- crypto.utils: added cryptographic helpers for byte-sequence comparison, zero testing, and masked integer selection.
- demos.smoke-test: added configurable smoke tests that open demos, check rendering and errors, and clean up each demo before continuing.
- editors.athas: added Athas editor integration with source-line navigation and a configurable executable path.
- editors.codeedit: added integration with the CodeEdit editor.
- file-picker.linux.gtk4: added native file dialogs for the GTK4 backend.
- fonts.shaping: added font direction, tab width, OpenType feature, locale, and color-glyph options for the Windows text backends.
- foogle: added searches for loaded words by stack effect and documented types, with clickable results.
- game.input.gtk3: added GTK3-specific game input support backed by shared GTK and Linux input handling.
- game.input.gtk4: added GTK4 game input support, including event-driven keyboard and mouse handling.
- gdk3: added bindings for GTK3 windowing, display, and input handling.
- gdk4: added bindings for GTK4 displays, surfaces, input events, and graphics contexts.
- graphene: added bindings for Graphene geometry types and vector, matrix, and transformation operations.
- gsk4: added bindings for the GTK4 scene graph and rendering API.
- gtk3: added bindings for GTK3 widgets, application windows, and OpenGL areas.
- gtk4: added bindings for GTK4 widgets, application windows, and event controllers.
- gtk4-samples.opengl: added an example of rendering OpenGL in a GTK4 application window.
- math.floats.small: added IEEE binary16 and bfloat16 conversions, with related vocabularies for arithmetic support and C memory types.
- math.vectors.simd.extensions: added half-precision and bfloat16 vector operations, dot products, and small matrix kernels with portable fallbacks and optional ARM64 acceleration.
- models.clock: added a singleton ticking clock model.
- opengl.gl.epoxy: added shared libepoxy function loading for the GTK OpenGL backends.
- opengl.gl.gtk3: provided GTK3 compatibility entry points for OpenGL function loading through the shared libepoxy resolver.
- pbrt: added support for the PBRT file formats.
- python.lifecycle: added shared lazy interpreter initialization and shutdown handling.
- raylib.live-coding.contexts: added native OpenGL context save/restore helpers for live coding on macOS, Unix, and Windows.
- regexp.captures: added numbered and named capture results, including matched text and capture bounds.
- shell.unix: added Unix foreground-process handling so terminal interrupts reach shell children.
- shlex: added shell-like string splitting modeled on Python’s shlex, with configurable comments and POSIX parsing, plus POSIX argument quoting and joining.
- sqids: added reversible encoding of non-negative integer sequences into short IDs, with a URL-safe default alphabet, configurable alphabets, minimum lengths, and blocklists.
- syntax.inferred: added optional ?: definitions that infer their stack effects from their bodies.
- terrain.smoke-test: added rendering and input checks for the Terrain demo.
- tools.disassembler.zydis: added an optional x86 and x86-64 disassembler backend using Zydis 4.1, with Intel-syntax output.
- tools.test.ffi: added shared helpers for native FFI regression fixtures.
- ui-demo: added interactive layout playgrounds, searchable tables, combo boxes, split panes, visible action results, and richer Unicode examples.
- ui.backend.gtk3: improved native dialogs, text input, game input, and OpenGL backend handling, avoided yielding during render and resize callbacks so windows cannot close midway through painting, and deferred rendering until the framebuffer is complete.
- ui.backend.gtk4: added a GTK4 UI backend with input-method integration and native window handling, checked framebuffer completeness, and deferred drawing until windows are mapped and have a positive size; handled focus callbacks after window removal and initialized older GTK4 versions without unsupported debug options.
- ui.backend.input-state: added shared tracking and cleanup of keyboard and mouse state for UI backends.
- ui.text.directwrite: added a DirectWrite UI text backend with tiled rendering for large text layouts; kept cached layouts in the global disposable registry so temporary scopes cannot dispose them prematurely.
- ui.text.index-maps: added shared text-index mappings for Unicode caret and selection handling.
- ui.text.pango.indexed: added indexed Pango text handling for large output rows.
- windows.directwrite: added DirectWrite bindings and text layout support, with related vocabularies for indexed drawing and rasterization.

### Improved libraries

- alien: improved callback handling and added the primitive interface for ARM64 variadic callbacks.
- alien.enums: used table lookups for large enums and rebuilt conversion code when its generator changes.
- alien.libraries.finder.freebsd: fixed shared-library lookup on FreeBSD.
- alien.libraries.finder.linux: improved runtime library discovery without requiring development symlinks, a linker, or a working ldconfig cache; recognized versioned basenames such as libSDL-1.2.so.0 while preferring exact basename matches.
- alien.libraries.finder.macos: improved matching of dyld library names on modern macOS.
- alien.syntax: added explicit variadic argument markers to foreign function and callback declarations.
- arrays.shaped: added trailing-axis broadcasting, scalar arrays, reshape, writable slice and transpose views, axis reductions, and batched matrix multiplication; corrected indexing, dimension queries, and empty shapes; made cloning copy storage and shape metadata and materialize views.
- assocs: corrected stack-effect names for zip-index; avoided allocating closures during cache lookups.
- bit-arrays: rejected negative and oversized lengths before allocating or resizing backing storage.
- bootstrap.compiler: reordered early compilation to prepare frequently used compiler and hashtable helpers before the main bootstrap sweep.
- bootstrap.image: improved image serialization and preserved mutable lexical words while retaining image format version 5.
- calendar.parser: accepted legacy cookie dates without an explicit timezone.
- checksums.openssl: fixed ownership and cleanup of OpenSSL digest resources.
- classes.algebra: avoided unnecessary cache work for identical named classes and reflexive class comparisons.
- classes.struct: validated buffer lengths assigned to fixed-array fields while preserving encoded-string pointer handling.
- classes.tuple.parser: rejected duplicate slot names in tuple literals.
- cocoa: corrected Objective-C runtime declarations and callback signatures and rejected ambiguous unqualified selectors.
- combinators.smart: preserved captured values when inferring the effects of composed callables.
- combinators.syntax: adjusted the definitions of &&[ and ||[ and added documentation.
- command-line: accepted vocabulary-root files with a byte-order mark.
- command-line.parser: added option aliases and attached values such as --host=localhost, including empty values and values beginning with a dash; preferred exact names over no- negation and rejected duplicate names and aliases.
- compression.gzip: corrected gzip output for interoperability with other implementations.
- compression.huffman: assigned a one-bit code to a lone Huffman symbol.
- compression.inflate: decoded concatenated gzip members and validated headers, checksums, and uncompressed sizes; fixed transitions from stored to compressed blocks and accepted zero padding after the final gzip member.
- compression.zstd.ffi: corrected the native names for compression bounds, compressed-frame sizes, and decompression contexts, with direct FFI regression tests.
- concurrency.combinators: preserved input order in parallel-filter and honored the requested output sequence type in parallel-map-as; reduced per-task allocation by sharing completion wrappers across parallel iteration stages.
- concurrency.conditions: fixed cooperative wait races and preserved timeout deadlines across wakeups.
- concurrency.flags: fixed waiting and wakeup behavior when flag state changes.
- concurrency.futures: documented and tested inherited dynamic scope; released completed worker contexts before scheduling more futures.
- concurrency.locks: rechecked lock availability after wakeups and preserved deadlines for ordinary and reader/writer locks.
- concurrency.mailboxes: preserved receive deadlines across wakeups and handled empty mailbox checks safely; released linked worker contexts before yielding after error delivery.
- concurrency.promises: ignored late linked-thread errors after a promise has already been fulfilled.
- concurrency.semaphores: fixed waiting for permits across wakeups.
- core-foundation.run-loop: reduced the latency of yield on macOS.
- core-text: improved large-line rasterization, Unicode selection, and caching, and stopped text backgrounds from painting over neighboring lines.
- cpu.arm.64: expanded SIMD lowering and corrected large offsets, immediate operands, structure returns, and foreign-call ABI handling.
- cpu.x86: fixed unsigned callback arguments and SIMD shift, shuffle, and extraction edge cases.
- cuckoo-filters: preserved existing entries when an insertion fails.
- curl.ffi: corrected variadic declarations and Linux runtime library discovery.
- curses.ffi: corrected variadic formatting calls and native argument-list declarations.
- db: added the db-write-lock backend hook and serialize-transaction combinator, preserving quotation stack effects and leaving other backends unchanged.
- db.pools: limited each database pool to 16 idle connections.
- db.sqlite: updated the SQLite bindings to 3.53.4, serialized transactions and tuple writes with reentrant per-file locks to prevent same-process write contention, enabled WAL mode and BEGIN IMMEDIATE transactions, and cleaned up native handles and result sets after failures, including failed WAL initialization.
- db.sqlite.ffi: updated declarations for SQLite 3.53.4 and corrected variadic formatting, pointer ownership, and VFS filename handling.
- db.types: reported abstract primary-key policies early, requiring a concrete primary-key policy.
- disjoint-sets: avoided redundant parent updates during lookup.
- dns: added support for DNS LOC records.
- editors.vim: corrected the documented Vim plugin location.
- file-picker.linux: improved native open/save dialogs and selected the implementation appropriate to the active GTK backend.
- fluids: loaded image decoders for the bundled PGM and PPM textures.
- fonts: preserved inherited shaping options when deriving fonts.
- fry: preserved source syntax and stepping boundaries and allowed quotation templates to remain unexpanded until needed.
- functors: preserved fried quotations in generated definitions.
- furnace.asides: stopped logging aside input values that may contain sensitive request data.
- furnace.auth: rejected deleted users and handled unknown usernames without corrupting the data stack.
- furnace.auth.basic: handled malformed Basic authentication input safely.
- furnace.auth.login: stopped logging user objects and permit-cookie values during login.
- furnace.auth.login.permits: corrected permit expiry checks.
- furnace.auth.providers: rejected empty claim tickets and corrected success handling when adding users.
- furnace.cache: corrected cache expiry handling.
- game.input: improved backend selection and keyboard, mouse, and Linux device handling across GTK versions; added event-driven macOS input state, including modifier keys and mouse motion, and removed hardware-dependent initialization tests.
- game.input.x11: reported a missing X display cleanly.
- generic: cached static method resolution and preserved next-method dependencies through macro expansion.
- gir: updated the bundled GIR files.
- gml.runtime: passed the method word through EXEC:: parsing correctly.
- gobject-introspection: added support for newer GIR files; preserved manually defined FFI bindings when introspection data is reloaded.
- gpu.framebuffers: handled the default framebuffer used by GTK4 rendering.
- gpu.shaders: preserved shader objects while assembling GPU programs.
- graphviz.render: selected preview formats through the registered image loaders.
- grid-meshes: corrected mesh generation used by Terrain rendering.
- hashtables: avoided scanning the backing array when clearing an already empty table.
- help: displayed numeric enum values, honored documented constant output names, and fixed help rendering for parsing-word values.
- help.html: generated pages for vocabulary prefixes that have no source file of their own; skipped empty vocabulary prefixes.
- help.markup: removed duplicate and self-referential related-word links.
- hints: added array and string specializations for index searches.
- html.templates.chloe: corrected the list of HTML void elements.
- html5: built nested document trees, decoded character references, and recorded recoverable parse errors; added SVG and MathML foreign content, template fragments, framesets, table and select handling, and recovery for misnested formatting elements, forms, and late head elements.
- http.client: decoded gzip response bodies before character decoding, including stacked encodings and concatenated members, and reported unsupported content codings; combined repeated Content-Encoding headers and reported unsuccessful HTTP status codes before attempting body decoding.
- http.server: rejected TLS input on plain HTTP connections and suppressed response bodies when HTTP semantics forbid them.
- http.server.requests: rejected incomplete requests and invalid header or body framing.
- http.server.static: handled malformed conditional-date headers.
- images.loader.cocoa: implemented image>stream for ns-image.
- images.loader.gdiplus: preserved image pixel formats and orientation and released native images and retained COM streams.
- images.loader.gtk: fixed GdkPixbuf library registration and encoded image-buffer lengths.
- images.tga: kept optional footer parsers out of line to reduce compiler expansion.
- inverse: preserved captured lexical values during expansion.
- io: avoided temporary chunk arrays when reading delimited input.
- io.backend.unix: preserved descriptor flags when enabling nonblocking I/O and cleaned up descriptors after cancellation failures.
- io.backend.unix.multiplexers.epoll: preserved simultaneous read/write registrations and corrected event and cleanup handling.
- io.backend.unix.multiplexers.kqueue: handled interrupted changelist submissions without losing applied changes.
- io.encodings.iana: matched charset names without regard to case.
- io.files: preserved line endings in change-file-lines and improved cleanup after file-construction failures.
- io.files.info.windows: limited fallback file-information lookup to access and sharing failures, preserving other Windows errors; made link-info inspect the link itself.
- io.launcher: improved Windows batch argument and environment handling and Unix child-process signal behavior, and cleaned up partially constructed pipelines after setup failures; streamlined Unix spawn setup and PATH lookup, added native exit notifications through kqueue, Linux pidfds, and Windows completion packets with polling fallback, and handled Windows waits beyond the native per-call handle limit; used posix_spawn on Linux to avoid copying large image page tables during process creation.
- io.mmap: cleaned up failed mappings and associated file handles.
- io.monitors: fixed monitor initialization, cancellation, and recursive-directory cleanup.
- io.pipes: cleaned up failed pipe construction and opened Unix FIFOs without blocking the VM, including cleanup when port initialization fails.
- io.pools: bounded idle resource pools and disposed resources returned after a pool has closed.
- io.ports: disposed native handles when port setup fails.
- io.servers: avoided accepting new connections after a server listener has stopped.
- io.sockets: fixed socket-construction cleanup, Unix-domain path padding, datagram handling, and Windows socket-set initialization; updated Windows connect and accept contexts and preserved accepted address storage.
- io.sockets.secure: preserved the intended certificate identity through address resolution and cleaned up failed secure connections.
- io.sockets.secure.openssl: corrected certificate identity checks, callback lifetimes, and OpenSSL resource ownership, including compatibility with older OpenSSL identity APIs.
- io.standard-paths: checked executable files and honored Windows PATHEXT during program discovery.
- io.timeouts: preserved timeout deadlines across cooperative waits.
- libclang: expanded C API bindings, avoided repeated declaration generation and unnecessary function-body parsing in the importer, and corrected token handling and native resource cleanup; fell back to the library search path when LLVM directories contain no libclang; discovered versioned libclang shared libraries inside LLVM installations.
- libudev: checked availability before calling optional legacy interfaces.
- lint: reported unnecessary recursive annotations conservatively.
- linux.input-events: corrected event-mask decoding, ioctl arguments, and multitouch slot counts.
- locals: fixed interactions with fry, typed tuple construction, and next-method dependency tracking.
- logging.analysis: bounded file-report reads and combined multiline log entries.
- logging.insomniac: rotated oversized logs even when report generation fails.
- lua: updated the bindings from Lua 5.1 to Lua 5.5, including the public C API, auxiliary and standard libraries, variadic formatting, and native argument-list access; requires Lua 5.5 with its default numeric configuration.
- mason: preserved fatal errors and test context in bounded crash reports and printed native backtraces; preserved partial test results in failed build reports.
- math: normalized integer arithmetic results and corrected floating-point comparison and conversion edge cases.
- math.blas.config: selected the GNU Fortran return ABI for bundled 32-bit Windows OpenBLAS libraries.
- math.floats.env: decoded floating-point errors before testing exception flags.
- math.functions: corrected indeterminate powers and floating-point zero exponents.
- math.integers: validated shift counts and preserved large bit indices; corrected bit? for fixnum bit indices outside the native range.
- math.libm: added fexp1- (C’s expm1); reported underflow for finite powers rounded to zero on the Windows Universal CRT.
- math.matrices.elimination: corrected nullspace calculation and handled empty matrices.
- math.order: preserved the caller’s stack row while computing comparison keys.
- math.parser: fixed floating-point formatting boundaries and added rectangular complex literals with a j suffix.
- math.statistics: validated data types before returning degenerate variance results.
- math.transforms.fft: reduced temporary allocations and used radix-2 decomposition for even lengths, including lengths that are not powers of two.
- math.vectors: added fused multiply-add, rounding, bit operations, and dot-product and small matrix accumulation protocols.
- math.vectors.conversion: preserved unsigned numeric conversion semantics.
- math.vectors.simd: aligned native and fallback behavior for shifts, shuffles, overflow, rounding, NaNs, and integer dot products, and corrected numeric coercion in half-precision and bfloat16 constructors; preserved all bits in boolean SIMD masks.
- metar: expanded METAR and TAF parsing, including runway state, wind shear, sea conditions, variable visibility, forecast change groups, and remarks; improved date rollover handling and added abbreviation lookup helpers.
- mime.multipart: validated multipart framing and handled malformed input without leaking resources.
- models: added model-deactivated.
- modern: stopped colon forms at enclosing sequence delimiters.
- openal.alut: used native OpenAL context management and audio loading on macOS without requiring an external ALUT library.
- opengl: improved GTK extension loading and cached function pointers by symbol name and context.
- opengl.textures: fixed texture wrapping on OpenGL 1.1 renderers.
- openssl: corrected native declarations, variadic BIO calls, and resource ownership.
- papier: updated shaders for core OpenGL contexts and fixed GTK4 rendering and keyboard movement, including A/D controls.
- pcre2: added the features previously available in the deprecated pcre vocabulary.
- peg: omitted hidden results from repetition and list parsers and added optional* to distinguish a missing match from a successful match whose AST is f.
- ping: added support for Linux ICMP datagram sockets.
- python: initialized high-level imports, object constructors, and conversions on first use; finalized the interpreter at shutdown only after it has been used. Raw python.ffi calls still require explicit py-initialize.
- python.ffi: searched Python 3.15 libraries and used versioned DLL names on Windows.
- quotations: made words callable while retaining a separate quotation-like class for sequence-like quotation objects.
- ranges: tested membership in integer ranges without enumerating their elements.
- raylib: updated to Raylib 6.0 and corrected variadic callbacks and allocation ownership; restored native OpenGL contexts across live-coding yields and cleanup.
- redis: updated bindings to Redis 8.8.0.
- regexp: added numbered and named captures and fixed assertion boundaries in lookbehind expressions.
- rocksdb.ffi: corrected the registered library name so foreign calls resolve against RocksDB.
- see: preserved deeply nested definitions and their imports and honored without-limits when displaying full definitions; normal output remains bounded.
- sequences: improved array/string comparisons and small integer-pair hashing, preserved callback stack rows in binary reductions, and rejected empty iotas and repetitions in minimum and maximum.
- shell: allowed foreground Unix child processes to receive terminal interrupts.
- smtp: redacted authentication commands from diagnostic output.
- stomp: fixed namespace update order when adjusting protocol versions.
- system: flushed output streams before exiting.
- system-info.linux: added system-code-name support for Ubuntu.
- system-info.windows: allocated correctly sized UTF-16 buffers for user and computer names to prevent buffer overruns.
- terrain: added core-profile shaders and rendering, corrected mesh and texture handling, and restored native macOS keyboard and mouse controls.
- threads: allocated thread-local namespaces lazily, avoiding a hashtable allocation for threads that never use local variables.
- timers: cleared running and thread state when timer callbacks exit exceptionally.
- toml: parsed empty and dotted-key inline tables and simplified the update-toml stack effect.
- tools.annotations: avoided double-counting recursive elapsed time.
- tools.completion: completed bare filename prefixes from the current directory.
- tools.continuations: improved stepping into fried quotations and retained the current instruction when displaying long quotations.
- tools.coverage: counted generic methods consistently in coverage reports.
- tools.crossref: tracked word references inside fried quotations, vectors, wrapped hashtables, other literal collections, and uninterned words; recorded method-word references directly.
- tools.disassembler: documented the Capstone backend on other supported architectures and how to select the optional Zydis backend on x86; released temporary code-heap snapshots after failures to prevent retained error continuations from accumulating snapshots.
- tools.disassembler.capstone: handled empty disassembly results.
- tools.image: updated image tooling for format version 5 and rejected stale formats before decoding heaps.
- tools.profiler.sampling: displayed total-time shares and allowed small branches to be filtered from reports.
- tools.ps: anchored Linux process inspection to an open process directory.
- tools.test: isolated prettyprinter settings during tests and help-lint examples.
- typed: preserved termination and recursive annotations in generated implementations and wrappers.
- ui.backend.cocoa: refreshed window resources when display scale changes and ignored inappropriate control characters in text input; corrected cursor hiding during captured input, cleared input state on focus changes, and improved native OpenGL context setup for demos.
- ui.backend.windows: used each window’s monitor DPI for text and input and returned pointer-sized results from window callbacks; fixed paint reentrancy, clipboard ownership, per-window surrogate-pair input, modifier keys, fullscreen handling, and tray tooltip encoding.
- ui.backend.x11.keys: normalized printable keypad symbols for text input.
- ui.debugger: avoided opening modal alerts inside native callbacks.
- ui.gadgets.editors: improved caret, selection, and rendering behavior for large and complex Unicode text, and submitted action fields with keypad Enter.
- ui.gadgets.panes: avoided quadratic copying of large strings, improved selection and copy behavior, and fixed following output at the bottom of a scroller.
- ui.gadgets.sliders: corrected the <slider> documentation.
- ui.gadgets.tables: validated the required model argument when constructing a table, before grafting.
- ui.gadgets.worlds: skipped drawing until the window framebuffer is complete, avoiding OpenGL errors while the drawing surface is being initialized.
- ui.render: supported GLSL 1.30, reduced repeated drawing work, and kept OpenGL renderer state with its owning window; reset legacy rendering hooks when switching from core-profile demos.
- ui.text.pango: improved rendering and selection of large text rows and preserved native antialiasing when drawing overlapping glyphs; read legacy glyph-item layouts without reading past native buffers.
- ui.theme.switching: refreshed open worlds when switching themes; improved dark-mode contrast in several demos.
- ui.tools.listener: accepted folders dropped from Finder and echoed source for quotation commands.
- ui.tools.operations: offered Reset for annotated generic methods.
- ui.traverse: bounded stale pane selection paths.
- unicode: updated Unicode and collation data to 18.0.0 and corrected identical-level collation ordering.
- unix: corrected native structure layouts, scalar and pointer types, large file offsets, and variadic declarations, including libc-specific timeval fields and 32-bit statvfs padding.
- unix.groups: handled lookup errors and owned group-result storage safely; treated platform-specific missing-group errno responses as unsuccessful lookups.
- unix.signals: used platform-specific signal numbers and corrected dispatch and handler sentinel handling.
- urls: improved IPv6 handling.
- vocabs.hierarchy: fixed handling of symlinked vocabularies.
- vocabs.loader: waited for prerequisite vocabularies to finish loading before activating require-when extensions.
- webapps.mason: validated request parameters before opening database connections to prevent leaks during validation exits; handled builders that have not uploaded results yet.
- webapps.planet: kept periodic maintenance running after recoverable failures.
- webapps.wiki: corrected the wiki icon resource path.
- wikipedia: used rendered pages and updated historical-event, birth, and death parsing for Wikipedia markup changes.
- windows.com: corrected the by-value size argument to IStream::SetSize.
- windows.com.syntax: tracked interface typedefs correctly across reloads.
- windows.dropfiles: released drag-and-drop handles even when filename decoding fails.
- windows.offscreen: restored and released offscreen GDI bitmaps on both success and failure.
- windows.streams: bounded COM stream copies, used 64-bit byte totals, and detected short writes.
- windows.uniscribe: improved cluster hit testing, bidirectional text, font fallback, glyph overhangs, selection compositing, and native layout lifetime handling.
- windows.version: passed UTF-16 query strings to VerQueryValueW.
- x11: corrected variadic declarations and preserved full-width native pointers.
- xml: fixed a file descriptor leak.
- xml.tokenize: bounded stack use when the optimizing compiler is disabled.
- xmode.marker: preserved regular-expression capture state while fixing up end patterns.
- yenc: computed file CRC32 from file contents, preserved filenames containing spaces or equals signs, validated envelope sizes and checksums, and decoded individual multipart envelopes with range and part-checksum checks.
- zoneinfo: updated bundled timezone data to 2026c.

### Compiler improvements

- Improved stack inference and error reporting for recursion, branches, locals, fry, and composed callables; checked annotated quotation calls and rejected known incompatible call effects.
- Fixed dependency tracking and recompilation after macro expansion, nested compilation, custom inlining, and struct redefinition.
- Improved constant folding and lookup-table optimization while preserving tuple identities, integer overflow behavior, and floating-point semantics.
- Corrected ARM64 code generation and foreign-call handling, added RISC-V foreign calls and callbacks, and fixed x86 callback and aggregate argument handling.
- Preserved GC roots and derived-pointer bases through compiler transformations and register allocation, and reported oversized stack frames as compiler errors.
- Reduced temporary allocation and repeated work during compiler analysis and bootstrap compilation.
- Added experimental backtracking, chordal, and greedy register allocators; linear scan remains the default.
- Added optional global value numbering, constant rematerialization, loop-invariant code motion, slot-load reuse, representation-cost improvements, and integer SIMD vectorization; these optimizations remain disabled by default.
- Added compiler-pass measurement tools and checks for SSA, register allocation, and GC roots.

### VM improvements

- Improved GC root tracking for native allocations, code snapshots, displaced aliens, and derived pointers, and corrected recovery after interrupted or failed collections.
- Strengthened memory safety with bounds checks for object initialization, code heaps, stack frames, and debugger reads; kept identity hashes stable and invalidated stale string hashes after resizing.
- Corrected bignum shifts, mixed-sign XOR, division, and integer conversions, and preserved NaN encodings and ordered/unordered floating-point comparisons.
- Improved signal handling, thread registration, and sampling-profiler reliability across platforms, including macOS interrupted-stack recovery and forward progress when recording samples is slow.
- Fixed callback-heap fragmentation, ARM64 relocations, and Windows ARM64 exception dispatch and native unwinding; added stack reserves and probing for native calls.
- Improved Windows startup diagnostics, worker-thread cleanup, JIT unwind metadata, large file offsets, and partial native I/O; validated code-heap updates and reset JIT state after errors.

### Zig VM improvements

- Improved parity with the C++ VM for GC roots, ARM64 signal recovery, stack and code-heap bounds, identity hashes, and JIT error cleanup.
- Fixed resource cleanup during allocation failures, image loading, VM shutdown, and native I/O, and preserved expired aliens and resized-object state.
- Reused JIT buffers, corrected relocation and unwind handling, and improved profiler timing, safepoint placement, and fatal-error handling.
- Removed hard-coded 64-bit assumptions from object layouts, arithmetic, foreign integer conversions, file offsets, GC, and relocations, improving 32-bit portability.

### Build and platform improvements

- Updated bundled SQLite to 3.54.0 and OpenSSL to 4.0.3 on both 32-bit and 64-bit Windows, and updated DLL names for Cairo, GLib, FreeType, and OpenAL to match bundled libraries.
- Building the experimental Zig VM now requires Zig 0.17.0; fixed Windows builds and used dynamic linking when targeting musl.
- Added headless Debian/Ubuntu build dependencies and optional vocabulary-test dependencies.
- Checked Linux runtime library sonames rather than requiring development linker names, and tolerated missing optional library directories.
- Corrected 32-bit x86 compilation and linking flags across C++, C, assembly, and FFI test builds, and preserved architecture flags when invoking make.
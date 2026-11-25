cgo does syntactic transformations unaware of Go types, allowing almost unnoticeable changes in source code to turn a 48ns call into a 76µs call. And its correctness checks can panic on legal code, while being exhaustive and expensive in some cases and lax in others.

You are getting early access to this article as a subscriber. Your support makes articles like this possible. Thank you.In this article, we recap some of the basics of [Go](https://theconsensus.dev/project/go.html)'s Foreign Function Interface (FFI), [cgo](https://pkg.go.dev/cmd/cgo?utm_source=theconsensus.dev&utm_medium=referral), and take a look at example programs that explain its behavior and limits. In particular we'll show how passing the same pointer to C can panic on code that the docs allow, how it can be about 1600x slower depending on how the C call is written, and when the cgo argument checker just gives up.Grab dependencies (clang, Go 1.27.0 and Go debugger, delve) and let's get started.`sudo apt-get install -y clang
curl -LO https://go.dev/dl/go1.27.0.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.27.0.linux-amd64.tar.gz
export PATH=/usr/local/go/bin:$HOME/go/bin:$PATH
export CC=clang
go install github.com/go-delve/delve/cmd/dlv@latest
`Writing C code in Go: how?[#](https://theconsensus.dev/p/2026/11/15/cgos-pointer-check.html#writing-c-code-in-go-how)cgo provides specific syntax we can use to write C code in Go. It has primitives to write pure C code, include statements, build-time flags, reference C code in Go code, and allows us to call Go code from C as well!Consider this program.`package main

/*
#include <stdio.h>
#include <stdlib.h>

static int add(int a, int b) {
	return a + b;
}
*/
import "C"

import (
	"fmt"
)

func main() {
	sum := C.add(C.int(3), C.int(4))
	fmt.Println("sum (calculated by C code in Go):", int(sum))
}
`main.goLet's walk through each element that cgo introduces:`import "C"`: This is used as a [signal](https://theconsensus.dev/project/go/source/go1.27.0/src/go/build/build.go#L-996) to the Go build toolchain that this Go file contains foreign C code. It is not an actual package in Go.Preamble: A special comment block immediately preceding `import "C"`. This is where we can write C code that we want to invoke from Go. It can have two different kinds of content:normal C codeC include statementsC references: We can call C functions and types inside Go code as if they are imported from the C package. e.g. `C.add()`, `C.int`We can build this Go package the same way we would any, using `go build`.`$ go build main.go
$ ./main
sum (calculated by C code in Go): 7
`It works! We were able to successfully invoke the C function `add` from Go's `main` function and get the correct output. But it's not clear exactly what role cgo plays. Time to dive deeper!cmd/cgo: the build-time utility[#](https://theconsensus.dev/p/2026/11/15/cgos-pointer-check.html#cmdcgo-the-build-time-utility)`go build` first [identifies](https://theconsensus.dev/project/go/source/go1.27.0/src/go/build/build.go#L-996) if a Go package has any C code in it. If yes, `go build` [invokes](https://theconsensus.dev/project/go/source/go1.27.0/src/cmd/go/internal/work/exec.go#L-3088) `cmd/cgo`, a command line tool.`cmd/cgo` [parses](https://theconsensus.dev/project/go/source/go1.27.0/src/cmd/cgo/ast.go#L-88) the C code out of the Go code, [invokes](https://theconsensus.dev/project/go/source/go1.27.0/src/cmd/cgo/gcc.go#L-213) the C compiler a few times to understand what each C reference is, its size and alignment (described in a [comment](https://theconsensus.dev/project/go/source/go1.27.0/src/cmd/cgo/doc.go#L-601) in cgo's source) and finally [generates](https://theconsensus.dev/project/go/source/go1.27.0/src/cmd/cgo/out.go#L-34) pure Go and C files. Finally, `go build` takes over, [compiles](https://theconsensus.dev/project/go/source/go1.27.0/src/cmd/go/internal/work/exec.go#L-933) the files and links them into the final binary.Let's look at the file generation step in detail.cgo needs to generate pure Go and C files that can be compiled by the Go and C compilers respectively. cgo will substitute all C references with pure Go references and generate bridge code between the Go and C code.For all referenced C types, cgo generates equivalent Go types. For example, cgo generates `type _Ctype_int int32` for `C.int`. In generated Go files, cgo substitutes all references to `C.int` with `_Ctype_int`. Running `go tool cgo` by hand writes these files to an `_obj` directory.`$ go tool cgo main.go
$ grep '^type _Ctype_int ' _obj/_cgo_gotypes.go
type _Ctype_int int32
$ grep '_Ctype_int' _obj/main.cgo1.go | sed -E 's| ?/\*line [^*]*\*/||g'
	sum := (_Cfunc_add)(_Ctype_int(3), _Ctype_int(4))
`For functions, it is a little more involved since we need to take care of calling conventions. Instead of translating the calling convention between Go and C, which comes with the overhead of dealing with CPU registers and stack locations across different C compilers and CPU architectures, cgo side steps this completely.Go runtime calls a C function of only one shape: a function that [takes](https://theconsensus.dev/project/go/source/go1.27.0/src/cmd/cgo/out.go#L-781) one pointer argument and returns nothing. It is the one function shape Go's runtime knows how to call on every platform. But in our example, the C function `add` takes two `int` arguments and returns an `int`, so what gives?cgo generates wrapper code in Go and C to bridge this.The original invocation from Go looked like:`sum := C.add(C.int(3), C.int(4))
`The generated wrapper Go function looks like this:`$ grep -B1 -A7 '^func _Cfunc_add' _obj/_cgo_gotypes.go
//go:cgo_unsafe_args
func _Cfunc_add(p0 _Ctype_int, p1 _Ctype_int) (r1 _Ctype_int) {
	_cgo_runtime_cgocall(_cgo_5211584c62cb_Cfunc_add, uintptr(unsafe.Pointer(&p0)))
	if _Cgo_always_false {
		_Cgo_use(p0)
		_Cgo_use(p1)
	}
	return
}
``//go:cgo_unsafe_args` [tells](https://theconsensus.dev/project/go/source/go1.27.0/src/cmd/cgo/out.go#L-648) the Go compiler to place the arguments and return variables consecutively on the stack instead of the standard register based calling convention. With that, a single pointer can be used to reference the arguments since they are all in consecutive memory, which in this case is `&p0`.`_cgo_runtime_cgocall` (i.e. `runtime.cgocall`) takes a pointer to the C function to invoke (which is another wrapper function, here `_cgo_5211584c62cb_Cfunc_add`) and a single pointer to where the arguments reside in memory (here `&p0`). `runtime.cgocall` does some more nifty things and finally invokes the cross-language call.While the packaged arguments bit is solved for Go, our `add` function in C still expects 2 arguments and a return value. To handle the C side of this transition, cgo also [generates](https://theconsensus.dev/project/go/source/go1.27.0/src/cmd/cgo/out.go#L-791) a C wrapper function. For our `add` function it looks like this:`$ grep -B2 -A16 'Cfunc_add(void \*v)' _obj/main.cgo2.c
CGO_NO_SANITIZE_THREAD
void
_cgo_5211584c62cb_Cfunc_add(void *v)
{
	struct {
		int p0;
		int p1;
		int r;
		char __pad12[4];
	} __attribute__((__packed__)) *_cgo_a = v;
	char *_cgo_stktop = _cgo_topofstack();
	__typeof__(_cgo_a->r) _cgo_r;
	_cgo_tsan_acquire();
	_cgo_r = add(_cgo_a->p0, _cgo_a->p1);
	_cgo_tsan_release();
	_cgo_a = (void*)((char*)_cgo_a + (_cgo_topofstack() - _cgo_stktop));
	_cgo_a->r = _cgo_r;
	_cgo_msan_write(&_cgo_a->r, sizeof(_cgo_a->r));
}
`This wrapper function resolves the pointer received from the cross-language call into a struct with the C function's input and output values. Then it calls the C function `add` normally with the arguments and writes the result back into the expected place in memory.Finally, `C.add` in the generated Go file is replaced with `_Cfunc_add`, as the `sum :=` line in the first listing showed.At this point, `cmd/cgo` has generated files which contain pure Go and pure C code. It does some final validation checks and ensures there are no errors. Finally, control is handed back to `go build`.`go build` invokes the Go compiler to compile the Go files and the C compiler handles the C files. The result is object files from each compilation which need to be linked together, along with other C libraries if needed. For packages like ours, the C linker [handles](https://theconsensus.dev/project/go/source/go1.27.0/src/cmd/link/internal/ld/config.go#L-208) the linking. In some cases, Go handles linking itself.Afterwards, we have a single binary.Pointer safety checks[#](https://theconsensus.dev/p/2026/11/15/cgos-pointer-check.html#pointer-safety-checks)In the above example, we were passing scalar arguments from Go to C. But things get a little tricky when we pass pointers across the language boundary.When pointers to memory allocated by Go are passed to C, the garbage collector can no longer track every copy. While Go keeps the memory an argument points to directly, ie top level pointers, safe for the duration of the cgo call, any memory reachable from such a pointer, ie nested pointers, do not get such guarantee. There is also a possibility that C can hold references to Go-owned memory beyond the cgo call.To handle issues like this, Go has [two rules](https://pkg.go.dev/cmd/cgo?utm_source=theconsensus.dev&utm_medium=referral#:~:text=Go%20code%20may%20pass%20a%20Go%20pointer%20to%20C%20provided,stored%20in%20C%20memory.) for passing memory between Go and C:The memory a Go pointer passed to C points to must not contain an unpinned Go pointer.C must not keep a copy of an unpinned Go pointer beyond the cgo call.Go cannot control what C does, so it's not possible to add checks for the second rule. For the first rule, cgo handles this in two steps: at build time and at runtime.During build time, if cgo cannot rule out the possibility of a nested pointer, it [adds](https://theconsensus.dev/project/go/source/go1.27.0/src/cmd/cgo/gcc.go#L-1057) a runtime check [enforced](https://theconsensus.dev/project/go/source/go1.27.0/src/runtime/cgocall.go#L-572) by the function `runtime.cgoCheckPointer`. (This check can be disabled by [setting](https://pkg.go.dev/cmd/cgo?utm_source=theconsensus.dev&utm_medium=referral#:~:text=These%20rules%20are,at%20build%20time.) `GODEBUG=cgocheck=0`.)Consider the following example where we pass a double pointer to `int` from Go to C:`package main

/*
static void take(void *p) {}
*/
import "C"

import (
	"fmt"
	"unsafe"
)

type S struct {
	other *int
	small [8]byte
}

func main() {
	s := &S{other: new(int)}
	C.take(unsafe.Pointer(&s.other))
	fmt.Println("ok")
}
`main.goLet's see the Go code that cgo generates for this:`$ go tool cgo main.go
$ sed -n '/^func main/,/^}/p' _obj/main.cgo1.go | sed -E 's| ?/\*line [^*]*\*/||g' | tr ';' '\n' | gofmt
func main() {
	s := &S{other: new(int)}
	func() {
		_cgoBase0 := &s.other
		_cgo0 := unsafe.Pointer(_cgoBase0)
		_cgoCheckPointer(_cgoBase0, 0 == 0)
		_Cfunc_take(_cgo0)
	}()
	fmt.Println("ok")
}
`The cgo build-time CLI adds a `_cgoCheckPointer` check for the double pointer argument, `&s.other`. `runtime.cgoCheckPointer` is responsible for checking the parameters and panicking if any nested pointer is unpinned. Our current example will panic at runtime:`$ go run main.go 2>&1 | head -1
panic: runtime error: argument of cgo function has Go pointer to unpinned Go pointer
`It is the programmer's job to make sure the memory backing nested pointers remains safe for the duration of the cgo call. This can be done with `runtime.Pinner`, ensuring the memory backing the pointer is neither moved nor freed by the garbage collector until it is explicitly unpinned.Modifying the above example, such that `s.other` is pinned:`package main

/*
static void take(void *p) {}
*/
import "C"

import (
	"fmt"
	"runtime"
	"unsafe"
)

type S struct {
	other *int
	small [8]byte
}

func main() {
	s := &S{other: new(int)}

	var pinner runtime.Pinner
	pinner.Pin(s.other)
	defer pinner.Unpin()

	C.take(unsafe.Pointer(&s.other))
	fmt.Println("ok")
}
`main.goGive it a run.`$ go run main.go
ok
`This time when `runtime.cgoCheckPointer` runs, it sees the nested pointer, `s.other`, is pinned. No panic needed.Sidenote: until [Go 1.21](https://go.dev/doc/go1.21?utm_source=theconsensus.dev&utm_medium=referral#:~:text=A%20new%20type,for%20more%20details.) we just couldn't pass C a pointer to memory containing Go pointers at all. Go 1.21 is when `runtime.Pinner` was released.But cgo does these transformations at the syntax level *without* knowledge of the Go types of the arguments. This has some interesting ramifications.Panicking on legal code[#](https://theconsensus.dev/p/2026/11/15/cgos-pointer-check.html#panicking-on-legal-code)cgo can only handle and transform very simple patterns in syntax. And when it can't handle a pattern things get weird.Consider the following example where we are passing a pointer to a byte array from Go to C:`package main

/*
static void take(void *p) {}
*/
import "C"

import "unsafe"

type S struct {
	other *int
	small [8]byte
}

func main() {
	s := &S{other: new(int)}
	C.take(unsafe.Pointer(&s.small)) // passes
}
`main.goIn this program, cgo saw the pointer to the byte array, `&s.small`, directly being passed to the C function. The check will look only at the memory of the byte array, `s.small`, and see it contains no pointers. This matches the [docs](https://pkg.go.dev/cmd/cgo?utm_source=theconsensus.dev&utm_medium=referral#:~:text=When%20passing%20a%20pointer%20to%20a%20field%20in%20a%20struct,not%20the%20entire%20struct.): when passing a pointer to a field in a struct, "the Go memory in question is the memory occupied by the field, not the entire struct." It builds and runs just fine.`$ go run main.go
$ echo $?
0
`But we can write that same exact program with a pattern cgo can not handle: assigning the unsafe pointer to a variable and passing that to `C.take`.The following example has only one change, instead of invoking the C function with `unsafe.Pointer(&s.small)`, the argument is a variable holding the unsafe pointer:`package main

/*
static void take(void *p) {}
*/
import "C"

import "unsafe"

type S struct {
	other *int
	small [8]byte
}

func main() {
	s := &S{other: new(int)}
	p := unsafe.Pointer(&s.small)
	C.take(p) // panics
}
`main.goGiving it a run, we see that it panics.`$ go run main.go 2>&1 | head -1
panic: runtime error: argument of cgo function has Go pointer to unpinned Go pointer
`That's weird! Let's print out the addresses we're operating on to prove they're really the address of `s.small`.`package main

/*
#include <stdio.h>
static void take(void *p) { printf("C got    %p\n", p); fflush(stdout); }
*/
import "C"

import (
	"fmt"
	"unsafe"
)

type S struct {
	other *int
	small [8]byte
}

func main() {
	s := &S{other: new(int)}
	fmt.Printf("s        %p\n", s)
	fmt.Printf("&s.small %p\n", &s.small)

	C.take(unsafe.Pointer(&s.small))

	p := unsafe.Pointer(&s.small)
	fmt.Printf("p        %p\n", p)
	C.take(p)
}
`main.goRunning it, we see both the arguments have the same address:`$ go run main.go 2>&1 | head -5
s        0x2fbb87ede080
&s.small 0x2fbb87ede088
C got    0x2fbb87ede088
p        0x2fbb87ede088
panic: runtime error: argument of cgo function has Go pointer to unpinned Go pointer
`So we're definitely looking at the same address the whole time. Why on earth is the program panicking with the variable and successfully executing when passing the pointer directly?Let's look at the traceback to find out where is the panic coming from:`$ go build -o demo main.go
$ GOTRACEBACK=system ./demo 2>&1 | sed -n '/^panic:/,/^$/p;/^goroutine 1 /,/^$/p'
panic: runtime error: argument of cgo function has Go pointer to unpinned Go pointer

goroutine 1 gp=0x34af3ed561e0 m=0 mp=0x57d3e0 [running]:
panic({0x5629f8?, 0x34af3ee1a030?})
	/usr/local/go/src/runtime/panic.go:878 +0x159 fp=0x34af3ed9dd18 sp=0x34af3ed9dc70 pc=0x47b7b9
runtime.cgoCheckUnknownPointer(0x34af3ee1a028, 0x0)
	/usr/local/go/src/runtime/cgocall.go:773 +0x12a fp=0x34af3ed9dd88 sp=0x34af3ed9dd18 pc=0x414eea
runtime.cgoCheckArg(0x5617a8, 0x34af3ee1a028, 0x0?, 0x1, 0x0)
	/usr/local/go/src/runtime/cgocall.go:750 +0x25c fp=0x34af3ed9ddf0 sp=0x34af3ed9dd88 pc=0x414b1c
runtime.cgoCheckPointer({0x5617a8, 0x34af3ee1a028}, {0x0, 0x0})
	/usr/local/go/src/runtime/cgocall.go:626 +0x146 fp=0x34af3ed9de30 sp=0x34af3ed9ddf0 pc=0x47a1c6
main.main.func2(...)
	/root/pointer-check/main.go:28
main.main()
	/root/pointer-check/main.go:28 +0x185 fp=0x34af3ed9deb8 sp=0x34af3ed9de30 pc=0x49e785
runtime.main()
	/usr/local/go/src/runtime/proc.go:302 +0x427 fp=0x34af3ed9dfe0 sp=0x34af3ed9deb8 pc=0x44a187
runtime.goexit({})
	/usr/local/go/src/runtime/asm_amd64.s:1264 +0x1 fp=0x34af3ed9dfe8 sp=0x34af3ed9dfe0 pc=0x481341
``runtime.cgoCheckUnknownPointer` panics. This function is called when the runtime does not know the type of the memory that the pointer points to. It finds the full heap object containing the given pointer and validates that no unpinned pointers exist in the object slots. In our example, that means no unpinned pointer should exist in the whole object `s`, not just the field `s.small`.Following the execution with delve, we can see the above in action:`$ go build -gcflags="all=-N -l" -o demo main.go
Type 'help' for list of commands.
(dlv) break runtime/cgocall.go:771
Breakpoint 1 set at 0x419609 for runtime.cgoCheckUnknownPointer() /usr/local/go/src/runtime/cgocall.go:771
(dlv) c
s        0x3427e8302290
&s.small 0x3427e8302298
C got    0x3427e8302298
p        0x3427e8302298
> [Breakpoint 1] runtime.cgoCheckUnknownPointer() /usr/local/go/src/runtime/cgocall.go:771 (hits goroutine(1):1 total:1) (PC: 0x419609)
Warning: debugging optimized function
   766:                 for {
   767:                         var addr uintptr
   768:                         if tp, addr = tp.next(base + span.elemsize); addr == 0 {
   769:                                 break
   770:                         }
=> 771:                         pp := *(*unsafe.Pointer)(unsafe.Pointer(addr))
   772:                         if cgoIsGoPointer(pp) && !isPinned(pp) {
   773:                                 panic(cgoFormatErr(msg, abi.Pointer))
   774:                         }
   775:                 }
   776:                 return
(dlv) print p
unsafe.Pointer(0x3427e8302298)
(dlv) print span.elemsize
16
(dlv) print unsafe.Pointer(addr)
unsafe.Pointer(0x3427e8302290)
(dlv) next
> runtime.cgoCheckUnknownPointer() /usr/local/go/src/runtime/cgocall.go:772 (PC: 0x419611)
Warning: debugging optimized function
   767:                         var addr uintptr
   768:                         if tp, addr = tp.next(base + span.elemsize); addr == 0 {
   769:                                 break
   770:                         }
   771:                         pp := *(*unsafe.Pointer)(unsafe.Pointer(addr))
=> 772:                         if cgoIsGoPointer(pp) && !isPinned(pp) {
   773:                                 panic(cgoFormatErr(msg, abi.Pointer))
   774:                         }
   775:                 }
   776:                 return
   777:         }
(dlv) print pp
unsafe.Pointer(0x3427e831e008)
(dlv) frame 4 print s.other
(*int)(0x3427e831e008)
*0
`Basically, when cgo doesn't recognize how a pointer argument was written, it tells the runtime nothing about what the pointer refers to. In such cases, runtime expects all pointers in the base object to be pinned. Even though the code had nothing to do with `s.other`, even though the C code doesn't use this whatsoever, the runtime didn't have enough information to know that and panics conservatively. But also wrongly.Even parentheses obstruct the pattern matching:`package main

/*
static void take(void *p) {}
*/
import "C"

import "unsafe"

type S struct {
	other *int
	small [8]byte
}

func main() {
	s := &S{other: new(int)}
	C.take(unsafe.Pointer((&s.small)))
}
`main.go`$ go tool cgo main.go
$ sed -n '/^func main/,/^}/p' _obj/main.cgo1.go | sed -E 's| ?/\*line [^*]*\*/||g' | tr ';' '\n' | gofmt
func main() {
	s := &S{other: new(int)}
	func() {
		_cgo0 := unsafe.Pointer((&s.small))
		_cgoCheckPointer(_cgo0, nil)
		_Cfunc_take(_cgo0)
	}()
}
$ go run main.go 2>&1 | head -1
panic: runtime error: argument of cgo function has Go pointer to unpinned Go pointer
`This has been a problem in Go for a decade: [golang/go#15318](https://github.com/golang/go/issues/15318?utm_source=theconsensus.dev&utm_medium=referral) and [golang/go#18184](https://github.com/golang/go/issues/18184?utm_source=theconsensus.dev&utm_medium=referral) (both 2016, each closed as a duplicate), the gzip `Write` example in [golang/go#28606](https://github.com/golang/go/issues/28606?utm_source=theconsensus.dev&utm_medium=referral) (2018, open), and [golang/go#70274](https://github.com/golang/go/issues/70274?utm_source=theconsensus.dev&utm_medium=referral) (2024, closed as a duplicate), where wrapping the argument in parentheses is enough to cause the panic.In the first issue, maintainer Ian Lance Taylor [called](https://github.com/golang/go/issues/15318?utm_source=theconsensus.dev&utm_medium=referral#issuecomment-210540283) this "a known deficiency in the current cgo pointer checker." But the docs never tell you to take the address inside the call, and he [explained](https://github.com/golang/go/issues/14704?utm_source=theconsensus.dev&utm_medium=referral#issuecomment-193882096) why in 2016: "there is no intent that that be a permanent requirement. The intent is what you quote from the docs: the memory in question is the memory occupied by the field." By 2024 he [wrote](https://github.com/golang/go/issues/67333?utm_source=theconsensus.dev&utm_medium=referral#issuecomment-2108557837) of a related case: "I don't know how to fix this except to do full type checking on the cgo input file, which is difficult as we currently expect the type checker to run on cgo output, not cgo input."Real-world projects have run into this too. Wails [panicked](https://github.com/wailsapp/wails/issues/3550?utm_source=theconsensus.dev&utm_medium=referral) on macOS because a buffer pointer was assigned to a variable before the C call. Envoy's Go extensions pass pointers that do [break the rule](https://github.com/golang/go/issues/62425?utm_source=theconsensus.dev&utm_medium=referral), and its Go cluster specifier just makes everyone [disable](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/cluster_specifier/golang?utm_source=theconsensus.dev&utm_medium=referral) cgocheck.But let's pause and also look at what's going on here from a performance perspective.Making checks extremely expensive[#](https://theconsensus.dev/p/2026/11/15/cgos-pointer-check.html#making-checks-extremely-expensive)If Go is checking every pointer in an object, what happens as we grow the number of pointers to check? Let's create three structs with increasingly larger arrays of pointers. We'll pass a field from the struct (with and without type info) to a C function.`package ptrcost

/*
static void take(void *p) {}
*/
import "C"

import "unsafe"

type S1 struct {
	small [8]byte
	ptrs  [1 << 10]*int
}

type S4 struct {
	small [8]byte
	ptrs  [4 << 10]*int
}

type S16 struct {
	small [8]byte
	ptrs  [16 << 10]*int
}

func inCall1(s *S1)   { C.take(unsafe.Pointer(&s.small)) }
func inCall4(s *S4)   { C.take(unsafe.Pointer(&s.small)) }
func inCall16(s *S16) { C.take(unsafe.Pointer(&s.small)) }

func viaVar1(s *S1)   { p := unsafe.Pointer(&s.small); C.take(p) }
func viaVar4(s *S4)   { p := unsafe.Pointer(&s.small); C.take(p) }
func viaVar16(s *S16) { p := unsafe.Pointer(&s.small); C.take(p) }
`ptrcost.goAnd let's write a little benchmark wrapper.`package ptrcost

import "testing"

func BenchmarkInCall1x(b *testing.B)  { s := new(S1); for i := 0; i < b.N; i++ { inCall1(s) } }
func BenchmarkInCall4x(b *testing.B)  { s := new(S4); for i := 0; i < b.N; i++ { inCall4(s) } }
func BenchmarkInCall16x(b *testing.B) { s := new(S16); for i := 0; i < b.N; i++ { inCall16(s) } }
func BenchmarkViaVar1x(b *testing.B)  { s := new(S1); for i := 0; i < b.N; i++ { viaVar1(s) } }
func BenchmarkViaVar4x(b *testing.B)  { s := new(S4); for i := 0; i < b.N; i++ { viaVar4(s) } }
func BenchmarkViaVar16x(b *testing.B) { s := new(S16); for i := 0; i < b.N; i++ { viaVar16(s) } }
`ptrcost_test.goLet's try it out.`$ go test -c -o ptr.test ptrcost.go ptrcost_test.go
$ ./ptr.test -test.run '^$' -test.bench . -test.benchtime 200ms
goos: linux
goarch: amd64
cpu: Intel(R) Xeon(R) Platinum 8280 CPU @ 2.70GHz
BenchmarkInCall1x-2    	 4633052	        48.34 ns/op
BenchmarkInCall4x-2    	 4899542	        48.43 ns/op
BenchmarkInCall16x-2   	 4904744	        48.26 ns/op
BenchmarkViaVar1x-2    	   45789	      5241 ns/op
BenchmarkViaVar4x-2    	   10000	     22389 ns/op
BenchmarkViaVar16x-2   	    3044	     75748 ns/op
PASS
`The cost stays constant even with an increasing number of pointers when passing with type info. But the cost grows linearly with the number of fields to check when passing without type info. Lack of type info, in the above case, incurs between 110x to about 1600x performance cost.The expense of checking objects full of pointers has been [known](https://github.com/golang/go/issues/14265?utm_source=theconsensus.dev&utm_medium=referral) since 2016.Checking only two levels deep[#](https://theconsensus.dev/p/2026/11/15/cgos-pointer-check.html#checking-only-two-levels-deep)While the pointer checks are exhaustive in the array case, Go does not exhaustively check nested structures.We can demonstrate this with a program that builds a linked list of N nodes, pins some of the nodes after the head, and passes `&head.next` to a C function that walks the list.`package main

/*
struct node { struct node *next; };

static long walk(void *p) {
	long n = 0;
	for (struct node *nd = *(struct node **)p; nd; nd = nd->next) n++;
	return n;
}
*/
import "C"

import (
	"fmt"
	"os"
	"runtime"
	"strconv"
	"unsafe"
)

type node struct {
	next *node
}

func main() {
	n, _ := strconv.Atoi(os.Args[1])      // nodes in the list
	pinned, _ := strconv.Atoi(os.Args[2]) // nodes pinned after the head

	var pinner runtime.Pinner
	defer pinner.Unpin()

	head := &node{}
	cur := head
	for i := 1; i < n; i++ {
		cur.next = &node{}
		cur = cur.next
		if i <= pinned {
			pinner.Pin(cur)
		}
	}

	walked := C.walk(unsafe.Pointer(&head.next))
	fmt.Println("C walked", walked, "nodes")
}
`main.go`$ go build -o list main.go
$ ./list 2 0 2>&1 | head -1
panic: runtime error: argument of cgo function has Go pointer to unpinned Go pointer
$ ./list 2 1
C walked 1 nodes
$ ./list 3 1 2>&1 | head -1
panic: runtime error: argument of cgo function has Go pointer to unpinned Go pointer
$ ./list 3 2
C walked 2 nodes
$ ./list 1000000 1 2>&1 | head -1
panic: runtime error: argument of cgo function has Go pointer to unpinned Go pointer
$ ./list 1000000 2
C walked 999999 nodes
`The pointer we pass, `&head.next`, points at memory holding a pointer to node 2, so node 2 must be [pinned](https://theconsensus.dev/project/go/source/go1.27.0/src/runtime/cgocall.go#L-746). The check then [scans](https://theconsensus.dev/project/go/source/go1.27.0/src/runtime/cgocall.go#L-771) node 2's object and finds node 3, so node 3 must be pinned too. But it doesn't go any further.In the last run, C reads 999,997 nodes that aren't pinned, which the [docs](https://pkg.go.dev/cmd/cgo?utm_source=theconsensus.dev&utm_medium=referral#:~:text=Go%20memory%20reachable%20from%20these%20function%20arguments,has%20access%20to%20it.) forbid: "Go memory reachable from these function arguments must be pinned as long as the C code has access to it."Even cgocheck2, which the docs [say](https://pkg.go.dev/cmd/cgo?utm_source=theconsensus.dev&utm_medium=referral#:~:text=The%20default%20setting,at%20build%20time.) does "complete checking", does not catch this:`$ GOEXPERIMENT=cgocheck2 go build -o list main.go
$ ./list 2 0 2>&1 | head -1
panic: runtime error: argument of cgo function has Go pointer to unpinned Go pointer
$ ./list 3 1 2>&1 | head -1
panic: runtime error: argument of cgo function has Go pointer to unpinned Go pointer
$ ./list 1000000 2
C walked 999999 nodes
`So we went from expensively exhaustive on the array of pointers example to cheap on the deeply nested pointer example.Parting thoughts[#](https://theconsensus.dev/p/2026/11/15/cgos-pointer-check.html#parting-thoughts)These examples are not exhaustive. Ian Lance Taylor has [said](https://github.com/golang/go/issues/28606?utm_source=theconsensus.dev&utm_medium=referral#issuecomment-2184269962) he is "not aware of any comprehensive list of cases where this arises." You can likely find more edge cases by looking at the [rewriteCall](https://theconsensus.dev/project/go/source/go1.27.0/src/cmd/cgo/gcc.go#L-857) transformation in cgo, which only recognizes `&x`, `&x[i]`, and `x[i:j]` written in a call to a C function, optionally inside type conversions. Searching Go issues for ["Go pointer to unpinned Go pointer"](https://github.com/golang/go/issues?q=%22Go+pointer+to+unpinned+Go+pointer%22&utm_source=theconsensus.dev&utm_medium=referral), or for the message's older wording, ["Go pointer to Go pointer"](https://github.com/golang/go/issues?q=%22cgo+argument+has+Go+pointer+to+Go+pointer%22&utm_source=theconsensus.dev&utm_medium=referral), may be another avenue.If you're passing a pointer to C, take the address right there in the call. It's probably worth writing a syntax checker to enforce this even. It's the difference between a 48ns call and a 76µs call. And when the cgocheck does pass, remember it only looked two levels deep, so pinning everything C can actually reach is still on you.
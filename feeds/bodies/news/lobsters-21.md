The *effective type* rules in the C programming language enable
	type-based aliasing analysis (TBAA). These rules are very old and can
	be found already in ANSI X3.159-1989.  Fundamentally, if a variable is
	declared with a type, then it is undefined behavior when it is accessed
	using an incompatible type. Undefined behavior at this point is exploited
	by some compilers for optimization, but it an implementation could also
	allow those accesses, or even add run-time type checking. The C standard
	committee in the past believed that the market will pick the best solution.
	As we known, the market preferred optimization over safety.

	In reality, the rules are a bit more complicated and are not based only
	on compatibility of types. In particular, different qualifiers and 
	different signedness is allowed, there are exceptions for character types,
	and there are rules for accessing members of structure or unions directly
	via pointers.  To keep things simple in this blog post, I will consider
	examples where only type compatibility matters. 

	In the following example,
	the compiler does not reload the lvalue `*p` in the return statement and instead
	directly returns the value 3 written in the first line.

	Example 1 [(Godbolt)](https://godbolt.org/z/ETon75M1Y )
`
int foo(int *p, float *q)
{
	*p = 3;		// effective type becomes int
	*q = 1.;	// effective type becomes float
	return *p;	// if the effective type is not int, there is UB
}
	`
`
"foo":
	mov     DWORD PTR [rdi], 3
	mov     eax, 3
	mov     DWORD PTR [rsi], 0x3f800000
	ret
	`

	Why is this allowed? If the store to `*q` does alias the same object
	as the later read from `*p` which uses an incompatible type, the behavior
	is undefined and returning `3` is then also allowed behavior.

	Language semantics experts talk about
	*refinement*, because returning `3` is a specific behavior
	in the set of all allowed behaviors. In case the accesses do alias
	and the behavior is undefined, other concrete behavior (including returning 
	`4`) would also be ok.

	In the example, the compiler uses this freedom to unify the behavior of the
	case with aliasing (and undefined behavior) with the more likely case that there is no
	aliasing (and no undefined behavior) and where `3` is then the
	required answer. Some people say the compiler can *assume* that
	the accesses do not alias, but this is a bit sloppy and not entirely correct.

	Note that the effective type rules talk about the types used for the
	accesses to lvalues, and therefor care about the type used for the actual
	accless. For example, for `*(float*)p` this type
	would be `float` while the type of the pointer object 
	`p` itself is completely irrelevant.
	The cast itself is not an aliasing violation, what matters is only whether
	the accesses to the same object then use lvalues of compatible type.
	In particular, also the types of function parameters do not matter.

Type-Changing Stores in C99

	The original wording in C89 simply assumed that all objects have a declared type.
	For ISO C99, the rules were fixed to allow type-changing stores, which
	was necessary to properly support memory allocated on the heap which
	initially does not have any type. In particular, C99 (6.5§6) now has the
	following rule.

... If a value is stored into an object having no declared type through an
lvalue having a type that is not a character type, then the type of the lvalue becomes the
effective type of the object for that access and for subsequent accesses that do not modify
the stored value. ...

	The effective type is set during a store and then is valid for the following
	reads until there is another write.
	In other words, the rules now generally allow changing the type of allocated object,
	even after it was already accessed with a different type. 
	In fact, this is exploited in many C programs to reuse
	memory, e.g. when defining its own allocator on top of
	`malloc` and `free`. 

	The following code has defined behavior even though the same
	object is accessed using two incompatible types during the
	execution of a program.

	Example 2 [(Godbolt)](https://godbolt.org/z/E5jneeEcG)
`
int foo(int *p, float *q)
{
	*q = 0.;	// effective type becomes float
	*p = 3;		// effective type becomes int
	return *p;	// effectype type is int
}

int main()
{
	static_assert(sizeof(int) == sizeof(float));
	void *q = malloc(sizeof(int));
	if (!q) return 0;
	// *q has no effective type
	int r = foo(q, q);
	free(q);
	return r;
}
	`

	The first store sets the effective type to `float`. The second store is
	allowed to change the effective type to `int`. The
	final read then uses the type `int` and this then
	matches the effective type the object has at this point.

Compilers vs. Type-Changing Stores

	The situation becomes more interesting in loops, where the compiler
	wants to move stores out of the loop.

	Example 3 [(Godbolt)](https://godbolt.org/z/e1zb375js)
`
void foo(int N, int *p, float q[N])
{
    for (int i = 0; i < N; ++i) {

        q[i] = 42;
        *p = 1;
    }
}
	`
`
"foo":
        test    edi, edi
        jle     .L1
        mov     rax, rdx
        movsxd  rdi, edi
        lea     rdx, [rdx+rdi*4]
        movss   xmm0, DWORD PTR .LC0[rip]
.L3:
        movss   DWORD PTR [rax], xmm0
        add     rax, 4
        cmp     rax, rdx
        jne     .L3
        mov     DWORD PTR [rsi], 1
.L1:
        ret
.LC0:
        .long   1109917696
	`

	As you can see, GCC moves the invariant store to `*p` out of
	the loop and performs it at the end. Even if there is aliasing, the
	optimization is correct and leaves the final outcome unaffected.

	Now let's see what clang does 
	([godbolt](https://godbolt.org/z/fexrjvz5a)):
	`
foo:
        test    edi, edi
        jle     .LBB0_3
        mov     dword ptr [rsi], 1
        mov     eax, edi
        xor     ecx, ecx
.LBB0_2:
        mov     dword ptr [rdx + 4*rcx], 1109917696
        inc     rcx
        cmp     rax, rcx
        jne     .LBB0_2
.LBB0_3:
        ret
	`

	Clang hoists the store above the loop.  But this is incorrect because a
	type-changing store to `q[i]` would then overwrite the previously
	written value `1`, which does not match the C source.
	*Clang miscompiles the code!*

	In fact, it is known (but perhaps not widely) that Clang does not implement
	the ISO C99 effective type rules.  Only when using the
	`-fno-strict-aliasing` command-line flag to turn off TBAA,
	Clang can be considered conforming to ISO C99 and later standards.

	In the past, GCC also got this wrong as documented in [PR 57359](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=57359),
	but fixed this fundamental store motion problem in 2020. Unfortunately,
	the link to the corresponding LLVM bug [21725](https://bugs.llvm.org/show_bug.cgi?id=21725)
	is broken, but - as far as I know - there was no effort to address this issue
	in the last decade.  For GCC, the situation is substantially better as it
	supports type-changing stores as part of its middle-end semantics. Still,
	there are open bugs, where a type-changing store that is dead
	is optimized away and then later the optimizer makes incorrect assumptions
	about the effect type.  So also on GCC, it may be advisable to turn TBAA off.

Conclusion

	There is a lot of confusion about effective types, with many subtle issues. Still,
	the basic rules from ISO C99 discussed in this first blog post about this topic
	are quite simple.  Unfortunately, optimizing compilers still got this wrong.
	Clang - even today - does not implement the rules according as specified by ISO C
	and GCC - while implementing the correct rules - still has some known bugs.
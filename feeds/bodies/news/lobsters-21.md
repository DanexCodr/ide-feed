[The previous post](https://sigreturn.com/blog/zone-allocator/) ended one function call short. Credentials, MACF (Mandatory Access Control Framework) labels and process state all moved into read-only zones, and the handful of allocator routines allowed to write them run in a privileged context. An arbitrary kernel write does not reach any of it. Calling one of those routines does, and calling something means getting an address you chose into a register the hardware is about to branch to.

That step used to be the cheap one. Find a pointer the target will call later, overwrite it, wait. Apple’s answer was not another check on the write. On arm64e, Apple’s pointer-authentication ABI, the pointer carries a cryptographic code in its own unused bits, the hardware verifies that code at the branch, and the key it verifies against is not in memory at all.

No amount of read and write recovers the key, so the attacks in this post go after the modifier, the signing operation, or the crash instead.

Everything here is public: the ARM architecture, Apple’s own arm64e ABI documentation, open-source XNU and objc4, and published research. The hands-on runs on a stock Mac with nothing disabled. There is no exploit and no bypass chain in this post.

## The spare bits of a pointer

A pointer does not need 64 bits. On the Mac used below a user process gets 47 bits of virtual address, so bits 63 down to 47 of every valid user pointer are zero, and the same bits in a kernel pointer are all ones. The hardware insists on it: the unused top of an address has to be the sign extension of the address itself, or the translation fails.

Pointer authentication (PAC) writes its code into that dead space, and it has to work around bit 55, because bit 55 is what tells the MMU whether the address belongs to the user half or the kernel half. So the field arrives in two pieces:

```
 63       56 55 54       47 46                                0
+-----------+--+-----------+---------------------------------+
|    PAC    |  |    PAC    |         virtual address         |
+-----------+--+-----------+---------------------------------+
             ^
             bit 55, preserved: 0 selects TTBR0 (user),
                                1 selects TTBR1 (kernel)
```

Top-byte-ignore (TBI), which lets software keep a tag in bits 63 to 56 that the MMU discards, takes the top byte away from the code when it is enabled for that kind of pointer. On this machine an instruction pointer gets 16 bits, eight in the top byte and eight more in bits 54 to 47, which the hands-on measures directly. Brandon Azad did the same measurement on kernel pointers on the A12 in 2019 and found the mask `0xff7fff8000000000`, a 24-bit field, because kernel addresses there are narrower and leave more room.

## Sign, authenticate, fail

Two instructions do the signing and the checking:

```asm
pacia   x0, x1      ; sign the pointer in x0 with key IA, modifier in x1
autia   x0, x1      ; authenticate x0 against the same key and modifier
```

`autia` recomputes the code from the address it finds and the modifier it is given, compares it with the one stored in the pointer, and on success hands back a clean, dereferenceable address. `xpaci` strips a code without checking it, for tooling that only wants the bare address. `pacga` does not touch a pointer at all: it takes a value in one register and a modifier in a second, and writes a 32-bit code into the top half of a third, for signing data that is not an address.

Each of these has a second spelling where the modifier is not a register. A trailing `z` means the modifier is zero: `paciza`, `autiza`, `braaz`, `blraaz`. Others hardcode a register, which is how the link register is handled: `pacibsp` signs it against the stack pointer and `autibsp` authenticates it, and `paciasp` and `autiasp` are the same pair under key A.

What happens on failure changed over time. ARMv8.3 as originally specified does not fault. It strips the pointer and writes a two-bit error code, the key number followed by its complement, so an A key leaves `01` and a B key `10`. The pair sits in bits 62 and 61 when top-byte-ignore is off for that kind of pointer and in bits 54 and 53 when it is on, and either way the address is non-canonical, so the *next* dereference takes a translation fault. `FEAT_FPAC` moves the fault to the `AUT` instruction itself, and `FEAT_FPACCOMBINE` extends that to the fused forms, the single instructions that authenticate and then branch or load. Those are cumulative feature levels, so a chip either stops at one of them or implements the next. This Mac reports:

```
sysctl hw.optional.arm | grep -i 'pauth\|fpac\|pac'
hw.optional.arm.FEAT_PACIMP: 1
hw.optional.arm.FEAT_PAuth: 1
hw.optional.arm.FEAT_PAuth2: 1
hw.optional.arm.FEAT_FPAC: 1
hw.optional.arm.FEAT_FPACCOMBINE: 0
```

`FEAT_PAuth2` is the ARMv8.6 revision of the base feature and `FEAT_FPAC` is built on top of it, so a standalone `autia` that fails traps on the spot here, which the hands-on below runs into. The fused instructions do not, because `FEAT_FPACCOMBINE` is off: a failed authentication inside one of those still produces a poisoned pointer and faults later, when the branch or the load is taken.

Those fused forms are where most of the signing actually happens: `retab` authenticates the link register and returns, `braa` and `blraa` authenticate and branch, `ldraa` authenticates and loads.

## Five keys and a modifier

Five 128-bit keys feed those instructions: **IA** and **IB** for instruction pointers, **DA** and **DB** for data pointers, and **GA** for `pacga`. They live in system registers that only privileged code can read or write, and that is the property everything else rests on. Stated in the terms of the last two posts: arbitrary read of your own address space does not reach them, and neither does arbitrary read of kernel memory, because they are not memory.

arm64e divides them by purpose. Apple’s ABI documentation calls the A keys process-independent and uses them for the global things, vtables and function pointers. The B keys are local: return addresses and frame pointers. Return addresses matter enough that IB is, in the documentation’s words, “almost entirely reserved for this purpose”, which is why the disassembly below shows `pacibsp` and `retab` and not `paciasp` and `retaa`.

The second operand is the modifier, also called the discriminator. The code is computed from key, address and modifier together, so one address signed under two modifiers yields two unrelated signatures, and a signature computed at one site does not authenticate at another. arm64e builds a modifier from two inputs: the address at which the pointer is stored, which gives address diversity, and a 16-bit constant, which gives constant diversity. Blending a constant into an address replaces the top 16 bits of that address. The constant itself is usually derived from a name: `ptrauth_string_discriminator` runs SipHash-2-4 over a string and folds the result into the 16-bit range, so a field can be diversified by what it is called.

Return-oriented programming is the case that shows why both halves are needed. A ROP chain is a stack full of addresses: overwrite the saved return address of the function you are in, and every `ret` afterwards pops the next entry of your list into the program counter, so the program runs your gadgets in your order. On arm64e that function signed its return address on entry with `pacibsp` and checks it on the way out with `retab`, and the key and the modifier each take away a different way of filling that list.

The key takes away forging. You cannot compute the code for the address of a gadget, because computing it needs a value held in a system register.

The modifier takes away reuse. If return addresses were signed with the key alone, every one of them in the process would carry an interchangeable signature, and a single valid one, read out of any stack frame with the read primitive you already have, would authenticate in every frame, with nothing forged. Because the modifier is the stack pointer on entry, a signed return address is valid at one stack depth and nowhere else, so a chain of ten gadgets needs ten valid signatures at ten specific values of SP. The gap that leaves is exact: two frames that do sit at the same depth share a modifier, and that is what the reuse attacks at the end of this post look for.

The algorithm computing the code is not public. ARM specifies QARMA, a family of lightweight tweakable block ciphers, as one algorithm an implementation may use, and permits an implementation-defined one instead. `FEAT_PACIMP: 1` in the output above, with no QARMA variant listed beside it, is Apple saying it uses its own.

Key diversification is per task, and the A and B keys do not get it the same way. XNU takes a task’s `jop_pid`, the diversifier behind the A keys, from its shared region, so every process on the same shared cache gets the same value, while `rop_pid`, behind the B keys, is drawn per task from `early_random()`. A task that is not arm64e runs with user PAC switched off entirely: `bsd/kern/kern_exec.c` flags the image `IMGPF_NOJOP`, and `bsd/kern/mach_loader.c` then creates its address space with `PMAP_CREATE_DISABLE_JOP`. Azad’s 2019 work found userspace threads carrying random key seeds while kernel threads shared a constant one. He could not work out the real implementation, so he assumed the most robust design for the rest of that research: that the true keys are random and held in the SoC itself.

## What Apple signs

arm64e shipped with the A12 in 2018, and with the M1 on the Mac, and it covers everything Apple builds: the kernel, the dyld shared cache (the single image every system library is merged into), the system binaries. It is not what your own code gets. The program below is arm64e only because I passed `-arch arm64e`, and macOS gates even that: `bsd/kern/kern_exec.c` refuses to exec a non-platform arm64e binary stamped with ptrauth ABI version 0, the preview ABI, unless the `-arm64e_preview_abi` boot argument is set. Current clang stamps a later version, which `otool -hv` on the binary shows as `USR01`, so it runs with nothing special enabled.

Inside a process, the ABI signs:

- Return addresses, key IB, modifier is the stack pointer on entry.
- Function pointers, key IA, no modifier, the weakest schema in the ABI and the other end of the scale from a return address, which is why an indirect call through a C function pointer compiles to blraaz, the zero-modifier form.
- C++ virtual functions, with a discriminator derived from the method’s name and signature, so an entry cannot be lifted from one slot or one class into another.
- Objective-C `isa` pointers, the field naming an object’s class, which objc4 signs with the DA key, blending the object’s own address with the constant 0x6AE1, annotated in objc-config.h as ptrauth_string_discriminator("isa").

Two of those entries are younger than arm64e itself. The `isa` was not signed at all on the first arm64e devices: the objc4 that shipped with macOS 10.15 has neither `ISA_SIGNING_KEY` nor `ExtractISA`, and Apple’s 2019 ABI document said outright that pointer authentication could not protect it. Both arrive in objc4-818.2, which ships in macOS 11.0.1 and iOS 14, so on an A12 running iOS 13 a write primitive could still point an object at a class of its choosing, and on the same phone running iOS 14 it could not. XNU moved in the same release: `jop_pid` appears nowhere in xnu-6153, the iOS 13 kernel, which diversifies `rop_pid` and nothing else, so until iOS 14 every arm64e process on the device signed A-key pointers under one set of keys, and a signature made in one process authenticated in another.

The kernel signs the same way, and its discriminators are worth reading because they show what the mechanism is for. This one guards the label pointer in a Mach port’s header, in `osfmk/ipc/ipc_object.h`:

```c
label.iol_pointer = ptrauth_auth_data(label.iol_pointer,
    ptrauth_key_process_independent_data,
    ptrauth_blend_discriminator(io, (uint32_t)(label.io_bits +
    ptrauth_string_discriminator("ipc_object.iol_pointer"))));
```

Three things go into that modifier: the address of the object, the object’s `io_bits`, which is the field carrying its type, and a hash of the field’s own name. The pointer therefore authenticates only in that field, of an object of that type, at that address. Copying a validly signed label pointer out of one port and into another fails. Rewriting `io_bits` on a port that carries a label breaks that label’s pointer too, because the type bits are an input to the signature over the pointer sitting beside them. Setting `io_bits` by hand is the first half of the fake-port move in [the XNU post](https://sigreturn.com/blog/xnu-under-the-hood/), and this is the kind of coupling that makes it expensive.

The zone allocator accounts for PAC too. The type signature `kalloc_type` computes, the one from the last post that decides which zone a struct is allocated from, has a granule value for it: `KT_GRANULE_PAC`, documented in `osfmk/kern/kalloc.h` as “represents a pointer which is subject to PAC”. Two structs of the same size differing only in whether a field is signed get different signatures, and therefore different signature groups.

## Hands-on: watching a pointer get signed

Start with one function that exercises two of the things arm64e signs: it calls through a function pointer, and it is not a leaf, so it has to save a return address.

```c
// t.c
int call_it(int (*fn)(int), int x)
{
    return fn(x) + 1;
}
```

Build it twice, for the two ABIs, and disassemble both:

```bash
clang -O2 -arch arm64  -c t.c -o a64.o
clang -O2 -arch arm64e -c t.c -o a64e.o
otool -tv a64.o
otool -tv a64e.o
```

```
a64.o:
(__TEXT,__text) section
_call_it:
0000000000000000    stp    x29, x30, [sp, #-0x10]!
0000000000000004    mov    x29, sp
0000000000000008    mov    x8, x0
000000000000000c    mov    x0, x1
0000000000000010    blr    x8
0000000000000014    add    w0, w0, #0x1
0000000000000018    ldp    x29, x30, [sp], #0x10
000000000000001c    ret

a64e.o:
(__TEXT,__text) section
_call_it:
0000000000000000    pacibsp
0000000000000004    stp    x29, x30, [sp, #-0x10]!
0000000000000008    mov    x29, sp
000000000000000c    mov    x8, x0
0000000000000010    mov    x0, x1
0000000000000014    blraaz    x8
0000000000000018    add    w0, w0, #0x1
000000000000001c    ldp    x29, x30, [sp], #0x10
0000000000000020    retab
```

Same C, one extra instruction, two changed. `pacibsp` signs the link register with key IB against the stack pointer before it is spilled, `retab` authenticates it against the same stack pointer before returning, and the plain `blr` became `blraaz`: authenticate with key IA and a zero modifier, then call.

The second program prints the field itself, by signing a pointer by hand:

```c
// pac.c
#include <stdio.h>
#include <stdint.h>

int main(void)
{
    uint64_t as_compiled = (uint64_t)(uintptr_t)main;
    uint64_t bare = as_compiled;
    __asm__ volatile("xpaci %0" : "+r"(bare));

    uint64_t a = bare, b = bare, c;
    __asm__ volatile("pacia %0, %1" : "+r"(a) : "r"((uint64_t)0));
    __asm__ volatile("pacia %0, %1" : "+r"(b) : "r"((uint64_t)1));
    c = a;
    __asm__ volatile("autia %0, %1" : "+r"(c) : "r"((uint64_t)0));

    printf("&main as compiled   0x%016llx\n", as_compiled);
    printf("xpaci               0x%016llx\n", bare);
    printf("pacia, modifier 0   0x%016llx\n", a);
    printf("pacia, modifier 1   0x%016llx\n", b);
    printf("autia, modifier 0   0x%016llx\n", c);
    fflush(stdout);

    uint64_t d = a;
    __asm__ volatile("autia %0, %1" : "+r"(d) : "r"((uint64_t)1));
    printf("autia, modifier 1   0x%016llx\n", d);
    return 0;
}
```

```bash
clang -O0 -arch arm64e pac.c -o pac && ./pac
```

```
&main as compiled   0x0e550001041404b0
xpaci               0x00000001041404b0
pacia, modifier 0   0x0e550001041404b0
pacia, modifier 1   0x0d7d8001041404b0
autia, modifier 0   0x00000001041404b0
[1]    19332 bus error  ./pac
```

Six lines, and every one of them is a claim from earlier in this post.

The address of `main` **arrives already signed**. Nothing in the program asked for that; taking the address of a function under arm64e produces a signed pointer, and `xpaci` on the next line gives the bare `0x00000001041404b0`.

Line three is identical to line one. Signing the bare address with key IA and a zero modifier reproduces, bit for bit, what the toolchain put there, which is the same schema `blraaz` authenticates against in the disassembly above.

Line four is the same address under modifier 1, and the signature over it is unrelated. Lay the two side by side and the field boundaries fall out:

|  | bits 63:56 | bits 55:48 | bit 47 | bits 46:0 |
| --- | --- | --- | --- | --- |
| modifier 0 | `0e` | `0101 0101` | `0` | `0x1041404b0` |
| modifier 1 | `0d` | `0111 1101` | `1` | `0x1041404b0` |

The top byte is signature. So is bit 47, which flips between the two runs while the address under it does not move. And **bit 55, the leading bit of the middle column, is zero in both**, preserved exactly as the diagram said, because this is a user pointer. Eight bits plus seven bits plus one: sixteen bits of signature. One flipped bit of the modifier recomputed the whole code, and five of those sixteen bits came out different, spread across all three pieces of the field.

Line five authenticates with the correct modifier and gets the bare address back. Then the last line asks for the same pointer under the wrong modifier, and the process takes a bus error before `printf` is ever reached. Nothing was dereferenced, so that fault is the `autia` instruction itself refusing: `FEAT_FPAC`, measured rather than assumed.

One last run, the same file built for plain arm64:

```bash
clang -O0 -arch arm64 pac.c -o pac-a64 && ./pac-a64
```

```
&main as compiled   0x0000000102918460
xpaci               0x0000000102918460
pacia, modifier 0   0x0000000102918460
pacia, modifier 1   0x0000000102918460
autia, modifier 0   0x0000000102918460
autia, modifier 1   0x0000000102918460
```

Six identical lines, and no crash at the end. The address moved because this is a different binary and the loader relocates it, but nothing else happened at all: no signature on the way in, nothing to strip, nothing to fail. The instructions are still in the binary and the CPU still executes them, and they do nothing, because the keys are off for a task that is not arm64e, which is `PMAP_CREATE_DISABLE_JOP` taking effect. PAC is a property of the ABI a process was built for, not of the silicon it runs on.

## Where the attacks live

Two posts on this blog arrive at this instruction from opposite ends. [The JavaScript engine post](https://sigreturn.com/blog/exploiting-javascript-engines/) reaches arbitrary read and write inside a renderer; the last post reaches arbitrary read and write in the kernel. Both then want to point something at code of their choosing, and on arm64e both find that pointer signed.

Sixteen bits is 65536 possibilities, which is not much, and Apple’s ABI documentation says so itself. The raw pointer bits are already known, so the only unknown is the signature, and an authentication oracle “can make it computationally feasible to discover the correct signature with brute force”. A wrong guess kills the process, and that is what normally prevents it.

Signing oracles and signing gadgets skip the guessing. If the target can be persuaded to sign a pointer you influence, or if there is reachable code that signs attacker-controlled data, the key is used on your behalf and never read.

Reuse needs no forgery at all. Two sites that share a key and a modifier accept each other’s signatures, so a validly signed pointer copied from one to the other is just a memory write. This is what the discriminators in the previous section defend against, and it is why XNU folds an object’s type bits and a field name into one 16-bit constant and blends that constant with the object’s address.

The zero-modifier case is where that defence is absent, and Clang’s documentation is blunt about it: the implementation “uses the exact same signing schema for all C function pointers, even for functions of substantially different type”, and it cannot do better, because “the C standard requires function pointers to be copyable with `memcpy`, which means that function pointers can never use address diversity”. Key IA and a zero modifier for every one of them, which is the `blraaz` in the disassembly above. Any signed C function pointer in the process authenticates in the slot of any other, so overwriting one with another is a plain memory write onto a target that expects a signed value and gets one.

PACMAN, from MIT in 2022, went after the crash rather than the signature. It requires an existing memory-corruption bug and a code sequence that uses a signed pointer speculatively; the guess is tested inside speculative execution, where a wrong answer is rolled back instead of faulting, and the verdict is read back with a prime-and-probe on the TLB, the CPU’s cache of address translations. It was demonstrated on the M1, and the authors are explicit that it is an exploitation technique rather than a standalone compromise.

The last shape is not an attack on PAC. If control flow is the expensive part, do not use control flow. That is what the device-number swap at the end of the last post does, and a signature never enters into it.

## State in 2026

**arm64e (A12 and later, and Apple silicon Macs).** Every Apple binary and the kernel are built for it. A binary you build is arm64 unless you ask otherwise, and it then runs with the keys disabled, as the last hands-on shows.

**The fault moved to the instruction.** `FEAT_FPAC` arrived with the A15 and the M2, so on those cores a failed standalone authentication is an immediate, precise crash instead of a poisoned pointer that dies somewhere later. The A12 through A14, and the M1, still poison the pointer instead. `FEAT_FPACCOMBINE` is not implemented on this Mac, so the fused forms keep the older behaviour.

**What a successful call would buy has shrunk.** On A15 and later, M2 and later, and every Apple silicon Mac but the base M1, from iOS 17 and macOS 14, the page tables and the code-signing state moved behind the Secure Page Table Monitor and the Trusted Execution Monitor. Diverting execution inside the kernel no longer reaches them.

## Where this leaves us

PAC fixes no bug. The overflow still overflows, the dangling page-table entry from the last post still dangles, and every byte of memory those primitives could reach before, they still reach. It removes the step that used to connect them to the program counter, and it removes it with a secret that is not stored anywhere an attacker can read. The engineering is all in the other operand: the keys are a fixed, small set, so the work went into making sure a signature means something only in the exact field, in the exact object, at the exact address where it was created.

This post cannot tell you what a bypass is worth today. Everything above except the last paragraph aims at one thing, a branch to an address the attacker chose, and on current hardware that branch lands in a kernel that no longer controls the two things a jailbreak needs: the page tables and the trust cache both sit behind monitors that the kernel, running at EL1, cannot write through. Those monitors, and the memory tagging that arrived beside them, are the next post.

## Notes and sources

Everything here is drawn from open source, vendor documentation, published research, and a Mac running a stock, unmodified macOS.

- ARM, the *Arm Architecture Reference Manual for A-profile architecture* (DDI 0487), for the PAC and AUT instruction behaviour, the two-bit error code written on a failed authentication, the FEAT_PAuth2, FEAT_FPAC and FEAT_FPACCOMBINE feature levels, and QARMA as one permitted algorithm beside an implementation-defined one.
- Apple, the arm64e pointer authentication ABI, Clang’s own specification: the key assignments (A keys global, B keys local, IB reserved for return addresses), the definitions of address and constant diversity, the 16-bit range for constant discriminators, the SipHash-2-4 string discriminator, and the brute-force analysis quoted in the attacks section.
- Brandon Azad, Examining Pointer Authentication on the iPhone XS (Project Zero, 2019), for the measured PAC mask, the per-process key seeds, and the assumption he adopted for the rest of that research, that the key material originates in the SoC.
- Apple, XNU source: osfmk/ipc/ipc_object.h for the port label discriminator quoted above, osfmk/kern/kalloc.h for KT_GRANULE_PAC, bsd/kern/kern_exec.c for the arm64e preview-ABI gate and the IMGPF_NOJOP flag, bsd/kern/mach_loader.c for PMAP_CREATE_DISABLE_JOP, osfmk/arm/machine_routines.h for the per-task JOP controls.
- Apple, objc4 source: runtime/objc-config.h for ISA_SIGNING_KEY and the 0x6AE1 isa discriminator, runtime/objc-object.h for where they are applied.
- Joseph Ravichandran, Weon Taek Na, Jay Lang and Mengjia Yan, PACMAN (MIT CSAIL, 2022), for the speculative side channel, the gadget it requires, and the affected cores.
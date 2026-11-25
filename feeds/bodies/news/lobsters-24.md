A reader recently wondered about the details of a documented but extremely obscure instruction, FRSTPM. This instruction is documented to exist on the Intel 80287XL math coprocessor, as well as the Intel M80287. The FRSTPM instruction was *not* present on the original 80287.

To understand what FRSTPM does, let’s first look at its older and definitely useful sibling, FSETPM. The original 8087 tracked a 20-bit linear address of floating-point instructions and operands, a side effect of how the 8087 interfaced with the 8086/8088.

While a 20-bit linear address is adequate in real mode (mostly—FP instructions in the high memory area just above 1M would cause trouble, although that was not available on the 8086), it is very unsuitable for protected mode. In theory Intel might have extended the linear address to 24 bits on the 80287, but that would still be no good. Unlike real-mode software, protected-mode code cannot trivially form a segmented address corresponding to an arbitrary linear address. The original segment and offset needs to be known.

Intel therefore redesigned the 80287 to be able to track the original segment and offset of floating-point instructions and operands. However, this functionality was to be used only in protected mode; in real mode, the 80287 behaves in a manner compatible with the 8087.

And that is where FSETPM comes in. Since the FPU does not have access to the 80286 MSW (Machine Status Word), and is not automatically informed when the MSW changes, system software has to execute the FSETPM instruction after switching the CPU to protected mode. This instruction informs the FPU that it should use the newer protected-mode format (with a segmented address) for saving and loading the FPU state.

The original 80287 design does not have any instruction reversing the effect of FSETPM. The 80286 can only be brought out of protected mode by resetting the CPU. Intel’s assumption, not unreasonable, was that a CPU reset would also reset the FPU (not doing that could certainly cause trouble). Thus the FPU was reset to real mode together with the CPU and FRSTPM was not necessary.

But then the 80287XL came (in 1990) and introduced the FRSTPM instruction. The 287XL was essentially the 387 FPU in a 287-compatible package. This was presumably a desirable product because the 387 was significantly faster and more modern (much closer to the approved IEEE 754 standard) than the original 8087/80287 numeric core (while the CPU interface is quite different, the numeric unit in the 80287 is the same as in the original 8087).

It is worth noting that although the 80386 can switch from protected to real mode without resetting the CPU, there is no FRSTPM instruction on the 80387. Why? Because neither FRSTPM nor FSETPM is necessary. The 386 CPU (not FPU) tracks the FP instruction and operand addresses, and the floating-point save/restore format automatically changes based on the current CPU mode (real/protected/V86).

This raises the question: What is FRSTPM good for? On the 386, it has no effect because the CPU, not FPU, does the relevant work. Yet on the 286, it is unnecessary because a CPU/FPU reset is used to switch from protected to real mode instead. In fact 286 system software that is not written specifically for the 287XL cannot use FRSTPM anyway, since the instruction is not present on the original 287.

Add the fact that the 80287XL became available in 1990, fairly late in the 286 life cycle. There were still new 286 systems sold in 1990, but any system software had a significant installed base of existing 286/287 machines to contend with.

### Aside: Total Confusion

Indirectly related to FRSTPM is the fact that even Intel is confused about how the related obsolete floating-point instructions (FENI/FDISI/FSETPM) work on newer CPUs/FPUs. While looking for any mention of FRSTPM in newer Intel documentation (in vain), I came across a documentation erratum in the [Pentium Specification Update](http://bitsavers.informatik.uni-stuttgart.de/components/intel/pentium/242480-028_P75UPDR1_199706.pdf#page=62&zoom=auto,-70,765). The text says:

*In the *Pentium® Processor Family Developer’s Manual*, Volume 3, page 23-37 in the Section 23.3.4 on Instructions, the 80287 instruction FSETPM is described as being equivalent to an FNOP when executed in the Intel387 math coprocessor and the Intel486 and Pentium processors. In fact, FSETPM is treated as a NOP in these processors, as is correctly explained (along with the difference between FNOP and NOP) on the next page in sec. 23.3.6. “FNOP” will be changed to “NOP” in the FSETPM description.*

Except even that is wrong! The referenced Section 23.3.6 says the following in the original 1993 *Pentium Processor Family Developer’s Manual*, Volume 3:

*The 8087 processor instructions FENI and FDISI and the Intel287 processor instruction  
FSETPM are treated as NOPS in the Pentium CPU, Intel486 CPU, and Intel387 math  
coprocessor. If these opcodes are detected in the instruction stream, no specific operation is  
performed and no internal states are affected.*

Judging from the available 80386 microcode disassembly, the above is simply wrong, at least for the 386+387. The instructions are neither NOPs nor FNOPs because the opcode is in fact sent to the FPU (where it may or may not be ignored). And indeed, an updated version of the Pentium manual from 1995 (order no. 241430-004) says the following in Section 23.3.6:

*The 8087 processor instructions FENI and FDISI and the Intel287 coprocessor instruction  
FSETPM are treated as NOPS in the Pentium processor, Intel486 CPU, and Intel387 math  
coprocessor. However, the FENI, FDISI, and FSETPM instructions do check for device-not-available faults. If these opcodes are detected in the instruction stream, no specific operation  
is performed and no internal states are affected.*

The updated text matches what the 386 microcode does: The device-not-available fault is raised if appropriate, the opcode is sent to the 387, but the 387 presumably does nothing if it sees the FENI/FDISI/FSETPM (and presumably FRSTPM) opcode. The same 386 microcode path is also executed for FINIT and FCLEX (the non-waiting form in all cases), and those instructions certainly are expected to do something, not just be ignored.

### FRSTPM Instruction Encoding

No doubt related to the general lack of purpose of the FRSTPM instruction, there is disagreement as to how it’s even encoded. Intel datasheets (80287XL, order no. 290376-003, Oct ’92; M80C287, order no. 271092-005, Nov ’92) quite unambiguously list the FRSTPM opcode as DB F4. However, many third party sources claim the opcode is in fact DB E5.

The opcode for FSETPM is DB E4 so either would make some sense. The Pentium Pro reused the DB F4 opcode for the FCOMI instruction, which somewhat strongly hints that the DB E5 opcode is rather more likely to be correct.

The book *PC Magazine Programmer’s Technical Reference: The Processor and Coprocessor* by Robert P. Hummel (1992) is a wonderful example of the confusion. In the FRSTPM instruction documentation (page 676), the opcode is listed (in binary) as DB F4. Yet in the x87 opcode map (page 733), it is listed as DB E5. Take your pick!

The obvious question then is, how do old assemblers and disassemblers actually deal with FRSTPM? But the sad truth is that… they simply don’t. I cannot find any evidence that for example Microsoft’s 1990s assemblers or disassemblers have any knowledge of FRSTPM. The same goes for Borland, Watcom, and Symantec. No sign of FRSTPM anywhere.

Neither is there any hint of FRSTPM in the debugging tools shipped with Phar Lap and Rational Systems DOS extenders. That is perhaps a good hint that in practice, FRSTPM was not used. Which is quite unsurprising, given that it’s entirely unclear why anyone would have a need to use FRSTPM at all!

After much searching, I discovered that Solaris (specifically its disassembler/debugger) has had knowledge of FRSTPM at least since version 2.5.1. Unsurprisingly, the support is [still there in Illumos](https://code.illumos.org/plugins/gitiles/illumos-gate/+/refs/heads/master/usr/src/common/dis/i386/dis_tables.c) (search for ‘frstpm’ in dis_tables.c). And Solaris/Illumos thinks that the FRSTPM encoding is DB E5, not DB F4 as the Intel datasheets say.

At this point, it’s fair to say that software support for FRSTPM is so obscure that it probably can’t be trusted anyway. So what do we do? Ask a real 80287XL, of course.

### Testing FRSTPM

To test the FRSTPM behavior, it is necessary to use a 286 system. The reason is simple—as explained above, a 386 CPU masks whatever effect FSETPM/FRSTPM might have. But a 286 CPU should not and the effect ought to be visible.

The OS/2 Museum has two 287XL coprocessors in its collection, so that wasn’t a problem. But finding a working 286 board turned out to be a challenge. Two previously working boards no longer function (one shows no signs of life, [the other](https://www.os2museum.com/wp/another-strange-286-board/) reliably hangs during POST). The third board (Plantron 286A) did better… but not much:

Luckily, I saved the contents of the board’s EPROM (unusually, a 27C512 chip rather than two 27256s as the BIOS assumes) while it was still working. Sure enough, several bits (three within a single nibble, to be specific) were flipped. So I found an empty 27C512 chip, flashed the old BIOS contents onto it, and the board finally started working.

Even at 16 MHz, a 286 isn’t much fun to work with, but it did the job. I devised a simple test, to be run all in real mode:

1. Initialize the FPU
2. Run a few floating-point instructions
3. Save the state with FNSTENV
4. Initialize the FPU again and execute FSETPM
5. Run the same floating-point instructions
6. Save the state with FNSTENV, compare with the first FNSTENV
7. Execute FRSTPM with DB F4 encoding and run FNSTENV again
8. Execute FRSTPM with DB E5 encoding and run FNSTENV again

As an aside, I re-learned that the 286+287 needs a little more synchronization than newer FPUs. If an F(N)STENV is not followed by FWAIT, the CPU may access the saved state data before the FPU had a chance to update it. This is not an issue on newer FPUs where the CPU itself (and not FPU) does the work.

The idea of the exercise is to first observe what effect FSETPM has on the FPU (without actually running the CPU in protected mode!), then try both possible FRSTPM encodings and observe if and how FNSTENV behavior changed.

### What I Learned

Steps 1-3 behave as expected and need no detailed description. Steps 4-5 are not directly relevant but interesting—the system is put into an undocumented state where the CPU operates in real mode but the FPU is told to run in protected mode.

The FSETPM instruction clearly does affect the 287(XL) behavior. Even if the CPU continues to run in real mode, the FP environment saved by F(N)STENV is stored in the protected-mode (16-bit) format.

*Speculation:* The 286 always feeds the code and data address in 16:16 segment:offset format. In protected mode, the FPU reports back these values unmodified. In real mode, the FPU converts the segment and offset to a 20-bit linear address.

Executing an instruction with DB F4 encoding (FRSTPM on the 287XL according to Intel, then FCOMI starting with the Pentium Pro) has no discernible effect on the 286+287XL system. The instruction *is* executed (does not raise #UD) but does not affect the FPU state in obvious ways.

Executing an instruction with DB E5 encoding (FRSTPM according to third parties) *does* affect a 286+287XL system and changes the format of data written by F(N)STENV back to the real-mode version. Notably the FP opcode is then correctly stored.

Here’s the output of my test program on an 80287XL:

![](http://www.os2museum.com/wp/wp-content/uploads/2026/11/frstpm-287xl.png)

*FRSTPM on an 80287XL*

The last few lines with “Real16” show what FSTENV stores, interpreted as 16-bit real-mode format. The first is after executing FSETPM—expected to be wrong, since the FPU will save the protected-mode version (the Prot16 line shows the same data interpreted correctly).

Then the program executes opcode DB F4, which is FRSTPM as documented by Intel. The newly stored Real16 state is exactly the same as before, implying that DB F4 did nothing. Next, DB E5 is executed. The last Real16 line clearly shows that the format of the data stored by FSTENV *did* change, and the FP opcode is exactly what it should be. This suggests that the FPU likely tracks the FP opcode even in protected mode, despite the fact that software cannot see it.

It also means that the Intel datasheets have been wrong all along and the third parties have been right; the FRSTPM encoding is DB E5, not DB F4 (as Intel claimed). Executed with DB E5 encoding, FRSTPM does what it’s expected to do, which is changing the format of the data stored by FSTENV.

For comparison, here’s the same program executed on a standard Intel 80287:

Neither the DB F4 nor DB E5 instruction has any discernible effect on the state stored by FSTENV—exactly as expected.

### Other Observations

I noticed that neither FRSTPM encoding or FUCOM (added in the 387) raises an #UD fault on an original 287. Likewise the wrong FRSTPM encoding (later used for FCOMI) produces no #UD on the 287XL. I speculate that the FPU has no mechanism to report an #UD. The CPU clearly does not know which FP opcodes exactly are valid—if it did, the 287XL could not have added support for the new 387 FPU instructions, or for FRSTPM.

In contrast, attempting to execute FRSTPM (with the DB E5 encoding) on a modern AMD Ryzen CPU does trigger a #UD exception.

I was also reminded than on a 286 system, F(N)STENV truly executes in parallel with the CPU. If a F(N)STENV instruction is not followed by a FWAIT, the CPU may access the FPU state data in memory before it has been written by the FPU. This is well documented but the behavior did change on newer CPU generations.

When Intel says that the FPU data pointer is “undefined” after FPU instructions which do not access memory, they mean that actual FPUs do not behave the same. I tested two 287 chips (a D80287-10 made in 1989 and D80287 SX062 made in 1987) and two 287XL chips (one from 1991, one from 1993) and the four chips exhibited *three* different behaviors.

### Aside: Speed Differences

While looking for older 287 FPUs, I was reminded that the original 80287 was never made in speed grades beyond 10 MHz. The 287 typically ran at 2/3 speed of the 286, but could in fact run entirely asynchronously. For example an 8 MHz 286 would typically be paired with a 6 MHz 287. Some 286 motherboards even had a socket for a separate oscillator used for the 287.

Interestingly, the 287 bus interface was originally specified to keep track of some 286 bus signals (e.g. HLDA, S1#, S2#, READY#). To that end, the 287 had *two* clock inputs—one was the same as the 286 CPU, the other was the clock that controlled the 287 speed. However, later 287 models (including the 287XL) dropped these pins and the secondary clock input. It is unclear when the information was deleted but it does not exist in the 210920-007 datasheet from September 1987, although it is present (again?) in the December 1990 datasheet 271029-005 for the M80287.

The asynchronous design was almost certainly done out of necessity. The 287 used the original 8087 math core which likely could not run as fast as the 286, or at least was not easy to manufacture in matching speeds. The 80287 was initially only released at 5 MHz, when the 286 could already run at 6 or 8 MHz.

In 1988, Intel released a somewhat mysterious 80C287A FPU which is mentioned in other datasheets but its own datasheet appears to be lost. This FPU could run at 12.5 MHz and was likely derived from the 387SX core. The M80C287 (for which a datasheet does exist, Intel order no. 271092-005) may be a military version of the 80C287A.

It is known that 80C287A datasheet 240347-002 was published in October 1989, but the contents are a mystery.

The 287XL was also based on the 387SX core. While the 287XL is rated to run at up to 12.5 MHz (simply matching Intel’s fastest 286), it is known to run at 16 MHz and faster without trouble. That is unsurprising because the 387SX started at 16 MHz and could run at up to 33 MHz.

Unlike the 287, which can divide the clock by three, the 287XL divides it by two, just like the 286. In a typical AT system with, say, a 20 MHz oscillator, the 286 runs at 10 MHz (20 / 2), 287 at 6.7 MHz (20 / 3), and 287XL at 10 MHz. That alone makes the 287XL perform significantly better than a classic 287.

### Remaining Questions

The exact 286/287 communication protocol is not yet fully understood; it is not entirely clear what data exactly the CPU sends to the FPU to track the floating-point opcode and instruction/data addresses. The data might depend on the CPU operating mode (real/protected) and may not be affected by FSETPM at all. This area of functionality significantly differs on the 386 and later processors where the CPU (not FPU) is solely in charge of tracking the FP opcode and addresses.

It is unclear if the FRSTPM instruction already existed in the 80C287A. The M80C287 and 80287XL datasheets do not make it clear when exactly the FRSTPM instruction was added.

Another question is whether the 287 really ever used the pins designed to track the 286’s prefetch queue. The relevant information just quietly vanished from the 287 datasheets sometime around 1986.

### Summary

The Intel 287XL FPU indeed supports an extremely obscure FRSTPM instruction. The instruction is so obscure that it is not supported by commonly available 1990s tools and even the opcode listed in Intel 287XL datasheet (DB F4) is wrong. The actual opcode is DB E5; this has been known since the 1990s and was documented in various 3rd party sources (e.g. Hummel’s book from 1992).

The utility of FRSTPM is unclear. The instruction is effectively useless because it is unnecessary (a reset brings both the 286 and 287 out of protected mode) and because it is not supported by most 287 processors. One possible use it might have is for testing, in cases where FSETPM is executed without actually putting the CPU into protected mode. In these situations, a regular 287 ends up in an unsupported state which cannot be left without resetting the FPU. A 287XL can be returned to a usable state via FRSTPM.

1. ![](https://secure.gravatar.com/avatar/64cf1cdea3a2749085f613f4d66bd81e12c371e4e100bf1e68e9d2bef400b5a1?s=80&d=mm&r=pg) [GloriousCow](https://martypc.blogspot.com/) says: .comment-author .vcard [November 24, 2026 at 12:44 am](https://www.os2museum.com/wp/a-completely-useless-instruction/#comment-475509) .comment-meta .commentmetadata My retro disassembler Marty DASM supports the 287XL. You can see FRSTPM decoded here: [https://dasm.martypc.net/?cpu=intel80286&fpu=intel80287xl&segment=16&offset=00000100&eu=0&cu=0&hex=DBE5](https://dasm.martypc.net/?cpu=intel80286&fpu=intel80287xl&segment=16&offset=00000100&eu=0&cu=0&hex=DBE5) I ran into the the same issues seeing two different encodings for it; glad to see I wasn’t just nuts. You are correct that the 286 (and the 386) do not UD on any ESC opcode; the IU control PLA decodes all ESC opcodes with no holes. Speaking of the 287 protocol, we’re about to find out a whole lot more about it. I have a 80c286 + 80c287 under Arduino control and plan to produce an FPU test suite with captured cycle traces. I am using an AMD 80c287 which is a fully static design. .reply #comment-##
2. ![](https://secure.gravatar.com/avatar/8d78624591d0563fe1e2c715bbbf7bb39ebb750b37df60c173e5669efe732916?s=80&d=mm&r=pg) Octocontrabass says: .comment-author .vcard [November 24, 2026 at 6:52 am](https://www.os2museum.com/wp/a-completely-useless-instruction/#comment-475551) .comment-meta .commentmetadata Looking at IBM’s PC/AT schematics, I’m pretty sure shutdown only resets the 286 and not the 287. That could have made F(N)RSTPM useful as a fast way to switch the 287 back to real mode, had it been available earlier. I have to wonder if F(N)RSTPM is actually a 387 instruction. If the 386 wasn’t originally planned to work with a 287, it wouldn’t have needed to keep track of the exception pointers on behalf of the FPU. When the exception pointers were moved into the 386, the only change to the 387 would be removing its CMD1 pin. This might also explain why early 387 datasheets don’t show the opcode field in the 32-bit protected mode environment layout: that field might have been added after the exception pointers were moved into the 386, so adding it didn’t change anything about the 387. Leftovers from early plans could also explain the CLK286/HLDA/INTA/S0/S1/READY pins shown in some 287 datasheets. If the original plan had been for the 287 to be a generic coprocessor like the 8087, it would have needed those pins to decode its instructions. Speaking of the 287 protocol, I’m pretty sure the 386 doesn’t send exception pointers to the FPU (except for FLDENV and FRSTOR). That would mean the 287 doesn’t wait for the pointers before it asserts PEREQ. It’ll be interesting if we can see that on the traces. That should also mean it’s possible to execute all 287 instructions on a 286 using OUT 0xF8,AX – but data transfers will (mis)behave according to the most recent ESC instruction, so it’s not actually useful. .reply #comment-##
3. ![](https://secure.gravatar.com/avatar/fd4f0447a78ab01011049cc126ebad302d5c604af6a4a6accc0bef6a1d83a352?s=80&d=mm&r=pg) Michal Necasek says: .comment-author .vcard [November 24, 2026 at 12:14 pm](https://www.os2museum.com/wp/a-completely-useless-instruction/#comment-475565) .comment-meta .commentmetadata I have noticed that in the 287XL datasheet (290376-003 page 20), the bus cycles table includes “write exception pointers”. In the 387SX datasheet (240225-002 page 18) the same table does not include “write exception pointers” and therefore the CMD1 pin is redundant, as you noted. Having FRSTPM as a 387 instruction would make sense except for the timeline–the 386 was able to work with a 287 before the 387 existed. Even the oldest 387 documentation is quite clear that FSETPM is not a thing on the 387 because the 386 takes care of things. Who knows, maybe the original 387 design was older, but if so then the old 387 datasheets hide it well. Maybe, or even likely, the “write exception pointers” bus cycle is optional on the 287, because it would not apply to every FP instruction anyway. So it’s entirely possible that the 287 deals with it if the 286 writes the exception pointers, but doesn’t insist on it. Which would allow the 386 to skip it. And if so, the 287 should run very slightly faster when paired with a 386. The 8087-style bus snooping pins in old 287 datasheets make me wonder if any 287s implemented that at all or not. The 287 sockets had those pins connected, because of course what else where the board designers supposed to do. But did the 287 chips ever need them? And are you sure that a shutdown won’t reset the 287 in a PC/AT? That should have caused trouble… although maybe it went unnoticed. .reply #comment-##
4. ![](https://secure.gravatar.com/avatar/fd4f0447a78ab01011049cc126ebad302d5c604af6a4a6accc0bef6a1d83a352?s=80&d=mm&r=pg) Michal Necasek says: .comment-author .vcard [November 24, 2026 at 12:23 pm](https://www.os2museum.com/wp/a-completely-useless-instruction/#comment-475567) .comment-meta .commentmetadata The two FRSTPM encodings have been out there since 1992 at least. I wonder now if perhaps FRSTPM originally *was* meant to use DB F4 but then it was changed to DB E5 to keep it in the same row as FINIT, FSETPM, and other “management” instructions. As far as I can tell, with a 286 it would have worked just fine either way. I’m curious what you’ll find out about the 286/287 communication. I think we can kind of guess most of it but that’s not the same as seeing the actual data. It’s probably safe to assume that the AMD 287, other than being fully static, is otherwise functionally 100% equivalent to the Intel 287. My understanding is that for the 286, AMD had the design database tapes from Intel, while the 287 was reverse engineered from analyzing Intel’s silicon. But the result actually should have been the same in both cases, a chip functionally indistinguishable from Intel’s. .reply #comment-##
5. ![](https://secure.gravatar.com/avatar/29504047f081bde37586c916b4cf56dd7e1a4d977367d701ba1359d5fbb3e7d2?s=80&d=mm&r=pg) [CL](https://sandpile.org/) says: .comment-author .vcard [November 24, 2026 at 1:33 pm](https://www.os2museum.com/wp/a-completely-useless-instruction/#comment-475571) .comment-meta .commentmetadata Thanks for going on the quest I posed. 🙂 For completeness, can you cover wait vs no-wait too, please? ( i.e. at sandpile, should I show it as FNRSTPM with a bold N? ) .reply #comment-##
6. ![](https://secure.gravatar.com/avatar/8d78624591d0563fe1e2c715bbbf7bb39ebb750b37df60c173e5669efe732916?s=80&d=mm&r=pg) Octocontrabass says: .comment-author .vcard [November 24, 2026 at 6:49 pm](https://www.os2museum.com/wp/a-completely-useless-instruction/#comment-475658) .comment-meta .commentmetadata The 286 treats all opcodes in the ranges DB E0 – DB FF and DF E0 – DF FF as no-wait instructions, including F(N)RSTPM. The 386 seems to also treat DB C0 – DB DF as no-wait instructions, though that might be another typo in the microcode entry point PLA transcription. .reply #comment-##
7. ![](https://secure.gravatar.com/avatar/fd4f0447a78ab01011049cc126ebad302d5c604af6a4a6accc0bef6a1d83a352?s=80&d=mm&r=pg) Michal Necasek says: .comment-author .vcard [November 24, 2026 at 7:15 pm](https://www.os2museum.com/wp/a-completely-useless-instruction/#comment-475660) .comment-meta .commentmetadata On the 386, it’s definitely FNRSTPM judging from the microcode disassembly; it’s handled just like FNINIT, FNSETPM, FNCLEX etc., no BUSY/ERROR checks. I couldn’t quickly come up with a test that would convince me one way or another what the 286 does. However, the 287XL (And M80C287) datasheet says: “If the ESC instruction is FINIT, FCLEX, FSTSW,FSTSW AX, FSTCW, FSETPM, or FRSTPM, the control executes it independently of the FPU and the sequencer.” I’d trust the datasheet on that. So I’d say yes, it should be listed as FNRSTPM with a bold N. .reply #comment-##
8. ![](https://secure.gravatar.com/avatar/29504047f081bde37586c916b4cf56dd7e1a4d977367d701ba1359d5fbb3e7d2?s=80&d=mm&r=pg) [CL](https://sandpile.org/) says: .comment-author .vcard [November 25, 2026 at 8:23 am](https://www.os2museum.com/wp/a-completely-useless-instruction/#comment-475863) .comment-meta .commentmetadata Yes, ‘N’. Also, presumably error-asserting rather than error-pulsing, since it doesn’t clear B/ES. .reply #comment-##
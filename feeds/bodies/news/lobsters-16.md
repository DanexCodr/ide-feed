Many, many, many years ago I ported Unix V6 to the Vax, it ran as
a virtual machine under VMS in supervisor/user modes (where VMS usually ran
shells) - the code is AFAIK lost to history, though a DECUS paper survives. Later I ported V7 too.

During the process I often came to that infamous line "You are not expected to understand this."
in the context switch code and, I indeed didn't understand it .... then one day I came to that code through
a different path and it was obvious .... let me explain what's going on, here's a deep dive

V6 Unix keeps per-process state in 2 places, a small entry in the process table, and the 'udot' a structure
mapped by the MMU at a well known kernel virtual address referenced as "u." which also contains the kernel stack. This is always
mapped to the same address in all running processes, setting up this mapping is a core part of each process switch.

V6 uses a somewhat baroque way to save the state of a running process and restoring it, in V7 they switched to use save()/restore() which works like the more familiar setjmp()/longjmp(). It's deeply beholding to
details in the V6 PDP-11 calling conventions - savu() saves enough state to return to it saves the
stack pointer (r6) and frame pointer (r5), it doesn't touch r2-r4

```

_savu:
	bis     $340,PS		// turn off interrupts
	mov     (sp)+,r1	// pull the PC off the stack
	mov     (sp),r0		// pull the address to store off the stack
	mov     sp,(r0)+	// now store the SP (as it was then savu was called) 
	mov     r5,(r0)+	// and store r5 too
	bic     $340,PS		// turn interrupts back on
	jmp     (r1)		// and return
```

retu() and aretu() are essentially the same, both restore the current state, leaving the routine that
called them walking on thin ice as the stack has changed out from under them, so has the frame pointer
(and as a result any local variables that are stored on the stack) after you call them life gets a little scary, care must be taken, we're on thin ice especially once interrupts are turned on .... retu() differs from aretu() in that retu() also maps the udot into the last page of
memory - retu is always passed the physical address of the udot, it's slightly magic in that the first 2 words of the
udot is also u.u_rsav the place that retu() really returns from - here they are slightly unwound:

```

 _aretu:
	bis     $340,PS		// turn interrupts off
	mov     (sp)+,r1	// load pc
	mov     (sp),r0		// get address of save area
	mov     (r0)+,sp	// restore stack pointer
	mov     (r0)+,r5	// restore frame pointer
	bic     $340,PS		// turn interrupots on
	jmp     (r1)		// return to caller

_retu:
	bis     $340,PS		// turn interrupts off
	mov     (sp)+,r1	// load pc
	mov     (sp),KISA6	// get physical address of u. into MMU
	mov     $_u,r0		// get kernel virtual address of u.u_rsav in r0
	mov     (r0)+,sp	// restore stack pointer
	mov     (r0)+,r5	// restore frame pointer
	bic     $340,PS		// turn interrupots on
	jmp     (r1)		// return to caller

```

There's another bit of magic here: r2-r4 are untouched, more about that later.

So here's the infamous context switch code (I've left out the bit that chooses a new process to run) - note swtch() as declared doesn't return a value, but at the end of the routine it explicitly returns "1". That's
not that unusual, C at the time didn't have a void, and had a rudimentary type system, if you didn't declare something it defaulted to "int". Also prior to V7 C wrote things like "a += 1" as "a =+ 1" (which is ambiguous) so you find things like: "rp->p_flag =& ~SSWAP;" in the code, this was normal at the time. It was common at
the time to tell the compiler which variables you wanted to put in registers rather than on the stack for performance reasons, compilers weren't very smart. Modern compilers complain if you feed them code with the register keyword.

```

swtch()
{
	static struct proc *p;
	register i, n;
	register struct proc *rp;

	if(p == NULL)
		p = &proc[0];

	/*
	 * Remember stack of caller
         */
        savu(u.u_rsav);
        /*
         * Switch to scheduler's stack
         */
        retu(proc[0].p_addr);

	..... some code to choose a new process to run, points rp at it

 	/* Switch to stack of the new process and set up
	 * his segmentation registers.
	 */
	retu(rp->p_addr);
	sureg();
	/*
	 * If the new process paused because it was
	 * swapped out, set the stack level to the last call
	 * to savu(u_ssav).  This means that the return
	 * which is executed immediately after the call to aretu
	 * actually returns from the last routine which did
	 * the savu.
	 *
	 * You are not expected to understand this.
	 */
	if(rp->p_flag&SSWAP) {
		rp->p_flag =& ~SSWAP;
		aretu(u.u_ssav);
	}
	/*
	 * The value returned here has many subtle implications.
	 * See the newproc comments.
	 */
	return(1);
}
```

So what's going on here, let's ignore the if statement after "You are not expected to understand this."
for the moment, here's how a context switch works:

savu(u.u_rsav); saves the current process's state at the beginning of its udot
retu(proc[0].p_addr); context switches on to process 0
.... some code chooses a next process to run and points rp at its entry in the process table
retu(rp->p_addr); switches the context to a new udot and loads its context from the new udot - at this point we're on the aforementioned "thin ice"
sureg() sets up the user space MMU mappings for the new process (on thin ice sureg() better be careful ...)
then we return 1 to all those calls to swtch() that never use it

Now the ice isn't all that thin here, we restored the stack and frame pointers to how they were inside 
swtch() where we did the savu(u.u_rsav); any interrupts that come along are not going to trash the stack we're 
using. Also we're pointing at any local variables we were using at the point where we last did a savu()
Now let's talk about the bit we're not supposed to understand: if for the new process, the process flag SSWAP is set we clear it
and do an aretu(u.u_ssav); - return to the swap save address and then return 1 .... so where does SSWAP get set? The answer is whenever a process is swapped out because there isn't enough memory, and when it does we've just done a savu(u.u_ssav); saved the current stack state to a special swap save state. Mostly that is the newproc() routine called from fork() - newproc returns 1 for the new process from a fork() and 0 from the old one.
Here's the relevant code:

newproc()
{
	....
	savu(u.u_rsav);
	....

	a2 = malloc(coremap, n);
	/*
	* If there is not enough core for the
	* new process, swap out the current process to generate the
	* copy.
	*/
	if(a2 == NULL) {
		rip-&p_stat = SIDL;
		rpp-&p_addr = a1;
		savu(u.u_ssav);
		xswap(rpp, 0, 0);
		rpp-&p_flag =| SSWAP;
		rip-&p_stat = SRUN;
	} else {

	.....

	return(0);
}

What happens when we execute the code we're not expected to understand? It only gets triggered by a newly swapped in process with that flag set.  

	 *
	 * You are not expected to understand this.
	 */
	if(rp->p_flag&SSWAP) {
		rp->p_flag =& ~SSWAP;
		aretu(u.u_ssav);
	}
	return(1);

So we do an aretu(u.u_ssav); that reloads the stack and frame pointers to the  point when savu(u.u_ssav); was executed in newproc() above, the xswap() has written out the udot at that point (shared between the new and old processes) to a swap file, that swap file has been reloaded and now we just switched to that new udot) the aretu() reloads the the stack and frame pointers to where they were in newproc() however the PC is still pointing to code in swtch() and it subsequently does a return(1) - it ends up returning a 1 to whoever called newproc() (which is either fork() or to main() when init is created).
So after the call to aretu() we're also on thin ice, but because the stack is in a safe state for interrupts
the whole time as retu(rp->p_addr); (essentially retu(u.u_rsav); matching the savu(u.u_rsav); in newproc()) is not below the spot aretu(u.u_ssav); goes to.
Finally let's talk about the variable rp in that code we're not expected to understand, it's a local variable accessed after retu() is called, but it's a register variable - there's some magic there, probably in the ordering of the declarations at the beginning of swtch(), my guess is that the compiler puts it in r4 (which is calee save) r2-r4 are not touched by savu and retu/aretu, but r2-r3 are caller save, if they're saved and restored by swtch() they will get junk off the new stack - o r4 contains rp and the rest of the register variables are not live so either they are not save/restored on the calls to retu/aretu or no one cares because they're not used after the first retu() call - I suspect the latter as the compiler was not probably smart enough to do lifetime analysis.
So there you are, all the gory details, please let me know if you find a mistake here (it was 45 years ago).
Paul Campbell taniwha@gmail.com 2026
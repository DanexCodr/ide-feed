i was recently having a discussion online about different perspectives on
signals. It led to a question me and someone else asked simultaneously: what if
you could *ignore* or *handle* the absolute, unstoppable order from the kernel
to be killed or stopped?

# [#](https://vulpinecitrus.info/blog/what-if-you-could-handle-sigkill/#Signals) 
Signals

Signals in POSIX are a form of IPC
 that allows
userland processes (and the kernel) to send each other simple indications of
actions to take. The Linux kernel, at the time of writing, handles about [31 of
those](https://elixir.bootlin.com/linux/v6.13/source/arch/x86/include/uapi/asm/signal.h#L22)
on the x86(-64) architecture. The most frequent situation where you might
encounter signals as a developer is when making *handlers* for these signals:
callbacks which are to be executed upon the reception of a signal by your
process. You may also *mask* these signals to stop them from triggering anything
on your program.

There are, however, two signals that cannot be stopped or handled: `SIGKILL` and
`SIGSTOP`.

`SIGKILL` is an indication to terminate immediately and messily. Essentially,
the process receiving this signal is abruptly ended, and marked as dead. Its
parent must then, at some point, reap it so that resources can be freed.

`SIGSTOP` is a weirder signal. When a process is running on a CPU and receives
`SIGSTOP`, it is marked as blocked and removed from the running CPU (or moved in
the background from the point of view of the user). After getting stopped, a
process remains stuck until receiving a `SIGCONT` signal. [Multiple
signals](https://elixir.bootlin.com/linux/v6.13/source/include/linux/signal.h#L422)
can indicate a block, but `SIGSTOP` is the only unavoidable one of those. You
may know that you can stop a process in a shell, via `^Z`. Shells usually do not
throw `SIGSTOP` directly, but `SIGTSTP`, which may be caught or fail. `SIGSTOP`
is considered “reserved” for the kernel only to throw.

So, what if we *could* ignore, or even handle `SIGKILL` and `SIGSTOP`? Surely,
because everyone in userspace made sure to *never* register a handler on those
signals or ignore them, things shouldn’t go wrong, right?

…right?

# [#](https://vulpinecitrus.info/blog/what-if-you-could-handle-sigkill/#Fucking_Around:_Messing_with_Linux) 
Fucking Around: Messing with Linux

My initial idea was to go into the signal handling code of Linux and remove
anything that treats `SIGKILL` or `SIGSTOP` differently from other signals. i
had originally wondered what exactly makes these two signals specials. It did
not take long to realize that Linux’s signal handling code explicitly treats
them very differently.

## [##](https://vulpinecitrus.info/blog/what-if-you-could-handle-sigkill/#How_Linux_Handles_Firing_Signals) 
How Linux Handles Firing Signals

Let’s go through a simple overview of how signals firing are handled by the
Linux kernel. For the sake of clarity, have a little diagram, so you can follow
along:

Linux’s implementation of signals explicitly refuses that user processes mask
`SIGKILL` and `SIGSTOP` or handle them. About all of that logic is located in
`kernel/signal.c` and in the appropriate `arch/$ARCH/kernel/signal(_?(32|64)?.c`
file. i will give examples in `arch/x86/kernel/signal.c`.

When the kernel is about to leave kernelspace, in `kernel/entry/common.c`’s
[`exit_to_user_mode_loop`](https://elixir.bootlin.com/linux/v6.13/source/kernel/entry/common.c#L90),
it checks for work left over to handle. That includes [pending
signals](https://elixir.bootlin.com/linux/v6.13/source/kernel/entry/common.c#L111)
to be sent or handled. When some signals are pending, Linux will next run
[`arch_do_signal_or_restart`](https://elixir.bootlin.com/linux/v6.13/source/arch/x86/kernel/signal.c#L333)
for the current architecture. There are essentially three steps in that
function: *getting* the signal and *handling* the signal if a user-defined
handler was found.

[`get_signal`](https://elixir.bootlin.com/linux/v6.13/source/kernel/signal.c#L2801)
runs a loop to dequeue signals that are not masked and process them. Right after
dequeuing, the [potential
handler](https://elixir.bootlin.com/linux/v6.13/source/kernel/signal.c#L2928) is
retrieved. And, if that handler is not the default handler that ignores the
signal (`SIG_IGN`), it is stored in a `ksignal` structure and `get_signal`
returns. Otherwise, the code checks for, among other things, whether the target
process is a global init and the signal can be ignored, and whether the signal
is a kind of `stop`. If that latter case is true, we prepare the process to be
stopped and call `do_signal_stop`, which handles *all* stop signals. Finally, if
the signal is not a kind of stop and was not handled, its default behaviour is
killing the process, which is done via `do_group_exit`. While scouring Linux’s
code initially, his gave me a first intuition: the kernel *expects* that there
is no user-set handler for `SIGSTOP` and `SIGKILL` in order to fall back on
default behaviour. If there was a user-set handler, they would be handled like
regular signals. Either there is logic right at the entry of handler setup code
that explicitly removes `SIGSTOP` and `SIGKILL`, or that check is *outside of
Linux*, which could mean having to rewrite parts of libc, or using raw syscalls.

If the signal is not handled by the kernel in `get_signal`, i.e. a handler is
set in `ksig`, the kernel then calls `handle_signal`. Just as with many other
functions in Linux, the name is deceptive: no signal is actually handled in
there (in fact, as far as i have seen, it is the only part of the top-level
signal handling function `arch_do_signal_or_restart` that never handles
signals). What `handle_signal` does is that it sets up the stack frame of the
signal handler and sets and saves pointers to restart execution in user mode
later. The process goes through `handle_signal` as defined in your [current
architecture](https://elixir.bootlin.com/linux/v6.13/source/arch/x86/kernel/signal.c#L255),
which, on x86(-64), then calls
[`setup_rt_frame`](https://elixir.bootlin.com/linux/v6.13/source/arch/x86/kernel/signal.c#L236)
to set up a return frame with the correct ABI
 for the signal. On x86, the state of the FPU
 is also saved and reset. Down
at the last function in the call chain for frame setup, the instruction pointer
[is
set](https://elixir.bootlin.com/linux/v6.13/source/arch/x86/kernel/signal_64.c#L210)
to `ksig->ka.sa.sa_handler`, so that when those registers are restored the
machine immediately executes your handler. After all of that is done,
[`signal_setup_done`](https://elixir.bootlin.com/linux/v6.13/source/kernel/signal.c#L3079)
is called to change some internal states, and the frame setup is done.

At the end of an iteration of the work loop in `exit_to_user_mode_loop`, the
kernel [returns to user
mode](https://elixir.bootlin.com/linux/v6.13/source/kernel/entry/common.c#L117)
to execute the necessary work.

Userspace programs use the
[`rt_sigaction`](https://elixir.bootlin.com/linux/v6.13/source/kernel/signal.c#L4606)
syscall as the entry point to set a handler for a signal. This one does not
specifically exclude our signals until you look at
[`do_sigaction`](https://elixir.bootlin.com/linux/v6.13/source/kernel/signal.c#L4285),
which checks for something called
[`sig_kernel_only`](https://elixir.bootlin.com/linux/v6.13/source/include/linux/signal.h#L445).
That macro checks if the signal is one of `SIGKILL` or `SIGSTOP` and throws out
a `-EINVAL` if that is true. This means that, as expected, there was logic
somewhere early when the kernel receives a handler setup syscall that explicitly
prevents setting one for `SIGKILL` or `SIGSTOP`.

## [##](https://vulpinecitrus.info/blog/what-if-you-could-handle-sigkill/#Linux_and_Masked_Signals) 
Linux and Masked Signals

As for setting *masks*, the set of signals ignored for a given task, the kernel
entry point is
[`rt_sigprocmask`](https://elixir.bootlin.com/linux/v6.13/source/kernel/signal.c#L3320).
It [explicitly
prevents](https://elixir.bootlin.com/linux/v6.13/source/kernel/signal.c#L3335)
blocking either `SIGKILL` or `SIGSTOP` before calling
[`sigprocmask`](https://elixir.bootlin.com/linux/v6.13/source/kernel/signal.c#L3237).
When a signal is sent, before queuing,
[`prepare_signal`](https://elixir.bootlin.com/linux/v6.13/source/kernel/signal.c#L870)
is called. One of its roles is checking that a signal is blocked or cannot be
delivered (global init is the target, the target is unkillable in some way,
etc). Surprisingly, *blocked signals are always queued*, because the signal mask
and handling might change between queueing and dequeueing. However, if the
signal is not masked but [no handler is
set](https://elixir.bootlin.com/linux/v6.13/source/kernel/signal.c#L80), it will
get
[dropped](https://elixir.bootlin.com/linux/v6.13/source/kernel/signal.c#L1053).

From reading the code that handles signals, signal masking and signal handlers,
it’s clear that there are multiple places that explicitly exclude setting
handlers for and masking `SIGKILL` and `SIGSTOP`.

So i went in and patched them.

## [##](https://vulpinecitrus.info/blog/what-if-you-could-handle-sigkill/#Patching_Linux) 
Patching Linux

There are four things i need to look at:

- Allowing processes to mask (sigprocmask) both kernel signals
- Allowing processes to handle (sigaction) both kernel signals
- Making sure that if a handler is set for one of these two signals, or they are masked, that the default behaviour is masked
- Patching any other instance of SIGKILL or SIGSTOP explicitly mentioned in kernel/signal.c

i begin with creating a simple KConfig key in the [“Kernel
Hacking”](https://elixir.bootlin.com/linux/v6.13/source/lib/Kconfig.debug#L2)
menu in `lib/Kconfig.debug`. This is the first part of [my patch](https://git.vulpinecitrus.info/Lymkwi/linux/commit/3bc478b0ac9afd6274e9f90a8a024e759da1b3e4.patch):

```
config KILL_STOP_HANDLING
	bool "Make SIGSTOP and SIGKILL handlable by regular programs"
	help
	  This prevents the kernel from blocking handling of SIGSTOP and SIGKILL by
	  regular user programs.

	  If unsure, say N.
```

Starting from there, i can hide or replace any part of signal handling code that
explicitly refuses `SIGSTOP` or `SIGKILL` using something like:

```
#ifdef CONFIG_KILL_STOP_HANDLING
    // Code that does not discriminate signals
#else
    // Previous code
#endif
```

So, let’s get started.

### [###](https://vulpinecitrus.info/blog/what-if-you-could-handle-sigkill/#Signal_Masking_Syscall) 
Signal Masking Syscall

Your machine enters the signal masking procedure via the
[`rt_sigprocmask`](https://elixir.bootlin.com/linux/v6.13/source/kernel/signal.c#L3320)
syscall (previously `sigprocmask` before real-time signals were introduced):

```
/**
 *  sys_rt_sigprocmask - change the list of currently blocked signals
 *  @how: whether to add, remove, or set signals
 *  @nset: stores pending signals
 *  @oset: previous value of signal mask if non-null
 *  @sigsetsize: size of sigset_t type
 */
SYSCALL_DEFINE4(rt_sigprocmask, int, how, sigset_t __user *, nset,
		sigset_t __user *, oset, size_t, sigsetsize)
{
```

In that function, after some declarations and tests, if the `nset` argument is
`true`, we proceed to call `sigprocmask` after copying the `new_set` of signals:

```
if (copy_from_user(&new_set, nset, sizeof(sigset_t)))
    return -EFAULT;
sigdelsetmask(&new_set, sigmask(SIGKILL)|sigmask(SIGSTOP));

error = sigprocmask(how, &new_set, NULL);
if (error)
    return error;
```

If you don’t blink, you can actually catch an explicit reference to our kernel
signals! Right before moving to the actual handler of the syscall’s operation,
we see a call to `sigdelsetmask`, which is more or less a “remove from set”
operation“ (a *set negation* and *store*). It is actually implemented as [`sig &= ~mask`](https://elixir.bootlin.com/linux/v6.13/source/include/linux/signal.h#L227).

This little line can be easily masked:

```
#ifndef CONFIG_KILL_STOP_HANDLING
    sigdelsetmask(&new_set, sigmask(SIGKILL)|sigmask(SIGSTOP));
#endif
```

`sigprocmask` can actually perform different operations depending on `how`,
which can be any of `SIG_BLOCK`, `SIG_UNBLOCK`, and `SIG_SETMASK`. The first two
are operations over the existing mask, whereas the last one sets the mask from
exactly what you give.

The code of that function, in
[`kernel/signal.c`](https://elixir.bootlin.com/linux/v6.13/source/kernel/signal.c#L3237)
(again) then does the following. It sets `oldset` to the old set, and then
dispatches over the value of `how` to perform the correct binary operation
between the `oldset` and the `set` it is given:

```
int sigprocmask(int how, sigset_t *set, sigset_t *oldset)
{
	struct task_struct *tsk = current;
	sigset_t newset;

	/* Lockless, only current can change ->blocked, never from irq */
	if (oldset)
		*oldset = tsk->blocked;

	switch (how) {
	case SIG_BLOCK:
		sigorsets(&newset, &tsk->blocked, set);
		break;
	case SIG_UNBLOCK:
		sigandnsets(&newset, &tsk->blocked, set);
		break;
	case SIG_SETMASK:
		newset = *set;
		break;
	default:
		return -EINVAL;
	}
	// ... SNIP ...
}
```

As the comment points out, this function will “happy block “unblockable”
signals like SIGKILL and friends“. As such, there’s no need to keep going in the
chain of calls. In fact, the rest of the calls only deal with taking locks,
setting sets, and such.

There are other places where `SIGSTOP` and `SIGKILL` are mentioned for masking:

- `set_current_blocked` is meant to be a user-mode friendly entrypoint to block a given set of signals. It removes SIGKILL and SIGSTOP preventively, so we can remove that.
- the compatibility definition of `rt_sigprocmask` also explicitly blocks our two signals, exactly the same way rt_sigprocmask does

### [###](https://vulpinecitrus.info/blog/what-if-you-could-handle-sigkill/#Signal_Handler_Setup_Syscall) 
Signal Handler Setup Syscall

Similarly to before, the syscall for entry is
[`rt_sigaction`](https://elixir.bootlin.com/linux/v6.13/source/kernel/signal.c#L4606):

```
/**
 *  sys_rt_sigaction - alter an action taken by a process
 *  @sig: signal to be sent
 *  @act: new sigaction
 *  @oact: used to save the previous sigaction
 *  @sigsetsize: size of sigset_t type
 */
SYSCALL_DEFINE4(rt_sigaction, int, sig,
		const struct sigaction __user *, act,
		struct sigaction __user *, oact,
		size_t, sigsetsize)
{
```

Nothing in the code explicitly talks about `SIGSTOP` or `SIGKILL`, so let us
inspect the next step:

```
ret = do_sigaction(sig, act ? &new_sa : NULL, oact ? &old_sa : NULL);
```

In [`do_sigaction`](https://elixir.bootlin.com/linux/v6.13/source/kernel/signal.c#L4279),
the code goes as follows:

```
int do_sigaction(int sig, struct k_sigaction *act, struct k_sigaction *oact)
{
	struct task_struct *p = current, *t;
	struct k_sigaction *k;
	sigset_t mask;

	if (!valid_signal(sig) || sig < 1 || (act && sig_kernel_only(sig)))
		return -EINVAL;

	k = &p->sighand->action[sig-1];

	spin_lock_irq(&p->sighand->siglock);
	if (k->sa.sa_flags & SA_IMMUTABLE) {
		spin_unlock_irq(&p->sighand->siglock);
		return -EINVAL;
	}
```

There is a check that the signal number is not valid (too big), or inferior to 1
(also invalid), or that there is a new `k_sigaction` to setup *and* the signal
is *kernel only*.

Kernel only, huh?

[`sig_kernel_only`](https://elixir.bootlin.com/linux/v6.13/source/include/linux/signal.h#L445)
is defined as a call to `siginmask`, with the set of signals
`SIG_KERNEL_ONLY_MASK`, defined
[here](https://elixir.bootlin.com/linux/v6.13/source/include/linux/signal.h#L419):

```
#define SIG_KERNEL_ONLY_MASK (\
	rt_sigmask(SIGKILL)   |  rt_sigmask(SIGSTOP))
```

So, if we *change* that definition… we would no longer be treating `SIGKILL`
and `SIGSTOP` differently anywhere that this is used:

```
#ifdef CONFIG_KILL_STOP_HANDLING
#define SIG_KERNEL_ONLY_MASK 0
#else
#define SIG_KERNEL_ONLY_MASK (\
 	rt_sigmask(SIGKILL)   |  rt_sigmask(SIGSTOP))
#endif // CONFIG_KILL_STOP_HANDLING
```

Conveniently, there are multiple places in `kernel/signal.c` where
`sig_kernel_only` is used:

- in `sig_task_ignored`, when determining whether to send the signal being sent to the task if it is the global init process
- in `get_signal`, to also prevent global init and container inits from receiving unwanted signals

With this change, when a new handler is to be set from userspace, we will no
longer reject the attempt if the target signal is `SIGKILL` or `SIGSTOP`.

### [###](https://vulpinecitrus.info/blog/what-if-you-could-handle-sigkill/#Signal_Waiting) 
Signal Waiting

There is one last syscall that needs to change its behaviour regarding signals:
`timedwait`.

[`rt_sigtimedwait`](https://elixir.bootlin.com/linux/v6.13/source/kernel/signal.c#L3806)
lets a process synchronously waits for one of the provided signals to become
*pending* (i.e. in queue). It then performs some checks, and goes into
[`do_sigtimedwait`](https://elixir.bootlin.com/linux/v6.13/source/kernel/signal.c#L3747).
A process is also not allowed to *wait* for `SIGKILL` or `SIGSTOP`, because it
is not supposed to react to these signals. Consequently, the set of signals to
wait for is deprived of these two signals at the start of `do_sigtimedwait`:

```
static int do_sigtimedwait(const sigset_t *which, kernel_siginfo_t *info,
		    const struct timespec64 *ts)
{
	ktime_t *to = NULL, timeout = KTIME_MAX;
	struct task_struct *tsk = current;
	sigset_t mask = *which;
	enum pid_type type;
	int sig, ret = 0;

	if (ts) {
		if (!timespec64_valid(ts))
			return -EINVAL;
		timeout = timespec64_to_ktime(*ts);
		to = &timeout;
	}

	/*
	 * Invert the set of allowed signals to get those we want to block.
	 */
	sigdelsetmask(&mask, sigmask(SIGKILL) | sigmask(SIGSTOP));
	signotset(&mask);

	spin_lock_irq(&tsk->sighand->siglock);
	sig = dequeue_signal(&mask, info, &type);
	// ... bla bla bla
```

The set of signals to wait for is inverted, and provided to `dequeue_signal`.
That function waits for a signal *not* in the set, and returns it. Changing the
line removing our two signals is all we need to remove the second to last
reference to `SIGSTOP` in `kernel/signal.c`:

```
#ifndef CONFIG_KILL_STOP_HANDLING
	sigdelsetmask(&mask, sigmask(SIGKILL) | sigmask(SIGSTOP));
#endif
```

### [###](https://vulpinecitrus.info/blog/what-if-you-could-handle-sigkill/#Signal_Retrieval_Stage) 
Signal Retrieval Stage

As mentioned before, the first thing done when a signal is pending is calling
`get_signal`. In the main loop, the handler is retrieved. If no handler is
present, we keep applying defaults. For all stopping signals, this is done here:

```
if (sig_kernel_stop(signr)) {
    /*
     * The default action is to stop all threads in
     * the thread group.  The job control signals
     * do nothing in an orphaned pgrp, but SIGSTOP
     * always works.  Note that siglock needs to be
     * dropped during the call to is_orphaned_pgrp()
     * because of lock ordering with tasklist_lock.
     * This allows an intervening SIGCONT to be posted.
     * We need to check for that and bail out if necessary.
     */
    if (signr != SIGSTOP) {
        spin_unlock_irq(&sighand->siglock);

        /* signals can be posted during this window */

        if (is_current_pgrp_orphaned())
            goto relock;

        spin_lock_irq(&sighand->siglock);
    }

    if (likely(do_signal_stop(signr))) {
        /* It released the siglock.  */
        goto relock;
    }

    /*
     * We didn't actually stop, due to a race
     * with SIGCONT or something like that.
     */
    continue;
}
```

Here, `SIGSTOP` is treated differently from other signals because it
*supposedly* always works. In our world, it does not, so it will have the same
behaviour as other stop signals on those orphaned pgrps:

```
    /*
     * The default action is to stop all threads in
     * the thread group.  The job control signals
     * do nothing in an orphaned pgrp, but SIGSTOP
     * always works.  Note that siglock needs to be
     * dropped during the call to is_orphaned_pgrp()
     * because of lock ordering with tasklist_lock.
     * This allows an intervening SIGCONT to be posted.
     * We need to check for that and bail out if necessary.
     */
#ifndef CONFIG_KILL_STOP_HANDLING
if (signr != SIGSTOP) {
#endif
    spin_unlock_irq(&sighand->siglock);

    /* signals can be posted during this window */

    if (is_current_pgrp_orphaned())
        goto relock;

    spin_lock_irq(&sighand->siglock);
#ifndef CONFIG_KILL_STOP_HANDLING
}
#endif
```

And that’s it.

### [###](https://vulpinecitrus.info/blog/what-if-you-could-handle-sigkill/#Building,_Booting) 
Building, Booting

Now, with our kernel done, i just run:

```
./scripts/config -e CONFIG_KILL_STOP_HANDLING
make bzImage modules
sudo make headers_install
sudo make modules_install INSTALL_MOD_STRIP=1
sudo cp arch/x86_64/boot/bzImage /boot/vmlinuz-killstop
```

Remember, [always strip your modules in
production](https://vulpinecitrus.info/blog/irregular-reminder-kernel-install-mod-strip/). i also
preemptively went in to disable `CONFIG_LOCALVERSION_AUTO`, and set
`CONFIG_LOCALVERSION` to `"-killstop"`, to better identify this kernel. i built
[my
mod](https://git.vulpinecitrus.info/Lymkwi/linux/src/branch/handle-kill-stop)
over a Linux 6.13.0 tree straight from the repos of Linus Torvalds himself.

As i am on Arch Linux, i run a good old `sudo mkinitcpio -g /boot/initramfs-killstop.img --kernelimage /boot/vmlinuz-killstop -k 6.13.0-killstop-dirty`,
then `sudo grub-mkconfig -o /boot/grub/grub.cfg`, cross the fingers on my paws,
and reboot.

# [#](https://vulpinecitrus.info/blog/what-if-you-could-handle-sigkill/#Finding_Out:_Booting_My_Modded_Linux) 
Finding Out: Booting My Modded Linux

i booted. And nothing happened. Nothing dramatically exploded. Nothing stopped.
Everything was normal. i had booted on the stock Arch Linux by accident while
running back to my bedroom to grab the dog collar that holds my authentication
token.

The second time around, i booted, and nothing happened. Nothing dramatically
exploded, nothing stopped. Everything was normal. i ran `uname -r` and was
greeted by

```
6.13.0-killstop-dirty
```

i was in.

Manipulating signals in Linux userland programs feel somewhat archaic. They kind
of *are* in a sense. The functions you are supposed to use differ a lot from
those i was taught in college. In fact, the ones i used here are much more
convenient and stick with the conventions of the syscalls. They are found in
`signal.h`.

Now, i want to write a program that can do one of two things: mask or handle
`SIGINT`, `SIGKILL`, `SIGSEGV`, `SIGTERM` and `SIGSTOP`. i am leaving `SIGUSR1`
and `SIGHUP` to still have an out to kill my program. i will have a `main`, and
i can write either `mask()` or `handle()` in it to pick what i do.

The `handle()` function, as well as some boilerplate for later, look like this:

```
int forever(void) {
    while (1) {
        ;
    }
}

void setup_handlers(void) {
    signal(SIGINT, catch_function);
    signal(SIGKILL, catch_function);
    signal(SIGSEGV, catch_function);
    signal(SIGTERM, catch_function);
    signal(SIGSTOP, catch_function);
    // i never actually check it worked, but, eh
    printf("Successfully set handler for signal numbers %d, %d, %d, %d and %d\n",
                SIGINT, SIGKILL, SIGSEGV, SIGTERM, SIGSTOP);
}

void please_kill(void) {
    unsigned int pid = getpid();
    printf("Please run:\n\tkill -9 %d; kill -11 %d; kill %d; kill -19 %d;\n",
                pid, pid, pid, pid);
}

int handle(void) {
    setup_handler();
    please_kill();
    forever();
    return EXIT_SUCCESS;
}
```

First we setup handlers for all our signals and point to `catch_function`, shown
below, using [`signal`(2)](https://man.archlinux.org/man/signal.2). Then, we simply get the `pid` of the process with
[`getpid`(2)](https://man.archlinux.org/man/getpid.2) from `unistd.h`, and prompt the user to <del>wreck the shit out of</del> give all they can to kill the
current process. Finally, we spin forever. If for some reason that loop ends, we
exit successfully.

The catch function will have customized messages for every single one of the
POSIX signals we catch:

```
static void catch_function(int signo) {
    status = signo;
    switch (signo) {
        case SIGINT:
            fputs("awawa! x3 you touched my SIGINT~\n", stderr);
            break;
        case SIGKILL:
            fputs("awawawawa :3 you tried to SIGKILL me~ teehee~\n", stderr);
            break;
        case SIGSEGV:
            fputs("ouchies! my memory SIGSEGVd x3!\n", stderr);
            break;
        case SIGTERM:
            fputs("i'm not gonna SIGTERM, meaning! >:3c\n", stderr);
            break;
        case SIGSTOP:
            fputs("owo *notices your SIGSTOP*\n", stderr);
            break;
        default:
            break;
    }
}
```

For *masking*, we use `sigset_t` to create a set of signals. **It is very
important to call
[`sigemptyset`(3)](https://man.archlinux.org/man/sigemptyset.3) or [`sigfillset`(3)](https://man.archlinux.org/man/sigfillset.3) on it**, or you will suffer the wrath of
uninitialized memory:

```
sigset_t mask, old;
sigemptyset(&mask);
sigemptyset(&old);
```

Then, i add the signals i want in my set with [`sigaddset`(3)](https://man.archlinux.org/man/sigaddset.3):

```
sigaddset(&mask, SIGINT);
sigaddset(&mask, SIGKILL);
sigaddset(&mask, SIGSEGV);
sigaddset(&mask, SIGTERM);
sigaddset(&mask, SIGSTOP);
```

i then call [`sigprocmask`(2)](https://man.archlinux.org/man/sigprocmask.2) using that set:

```
if ((res = sigprocmask(SIG_BLOCK, &mask, &old)) != 0) {
    fprintf(stderr, "Error masking away signals: %d\n", res);
    return -1;
}
```

i then call `please_kill()` the same way i do for signal handling before, so
that i can prompt my user to kill my process in many colourful ways, then spin
forever.

The result, at least for signal handling, is something like
[this](https://eldritch.cafe/@SharpLimefox/113976467185768571): a process that
can handle, for example, `SIGKILL`. As a result, conventional means of killing a
program are completely ineffective against it, as expected.

# [#](https://vulpinecitrus.info/blog/what-if-you-could-handle-sigkill/#Conclusion) 
Conclusion

There are many things i haven’t touched on. `SIGSTOP` is actually referenced [a
whole lot](https://elixir.bootlin.com/linux/v6.13/C/ident/SIGSTOP), and [same
for `SIGKILL`](https://elixir.bootlin.com/linux/v6.13/C/ident/SIGKILL). i
figured the files i touched are the part i was mostly interested in, but other
things could be worth looking into. [`ptrace`(2)](https://man.archlinux.org/man/ptrace.2) reacts on signals, so does
[`strace`(1)](https://man.archlinux.org/man/strace.1). There are [specific trap
invocations](https://elixir.bootlin.com/linux/v6.13/source/kernel/signal.c#L905)
that are supposed to notify `ptrace` upon signals being fired, and all kinds of
things. [signalfd](https://elixir.bootlin.com/linux/v6.13/source/fs/signalfd.c)
is something i could have looked into as well, but i did not. `kernel/ptrace.c`
also [sometimes explicitly singles out kernel signals](https://elixir.bootlin.com/linux/v6.13/source/kernel/ptrace.c#L1089) for some actions. By all means, my patches are not complete. Yet, they will let you do
what i set out to do when i started this: handle and mask the two signals that
nobody is supposed to mask or handle.

And you know? It turned out fine. Nothing exploded on my system. As i could
predict, because this was otherwise *impossible*, nobody did it. The signal
system was setup in such a way that you would most likely realize something you
were doing was *wrong*, and not try it.

To pull back further, it is interesting to notice how the rules we all take for
granted are just *set somewhere* in code. They were written by someone, at some
point. If there is code restricting you from doing something, someone wrote it.
Either they did not think anyone would want to do that thing, or they
specifically prevented you from doing it. Those rules are written somewhere, and
you can take it in your paws to go sniff around the code, pull out the relevant
parts, and hack around the things that bother you. For fun, learning, or
convenience.
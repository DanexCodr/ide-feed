It's Sunday afternoon, and this week I somehow kept my wits
	together long enough to keep track of the day of the week, so the
	release isn't randomly delayed. Will wonders never cease?

	Anyway, nothing very special seems to have happened this last week,
	so as expected the final 7.3 is out, and thus tomorrow the merge
	window for 7.4 opens. Except I'm on my annual family vacation, so
	instead of merging anything first thing in the morning, I'll spend
	most of the day on a boat and under water. I'll get back to merging
	in the afternoon, but I expect my schedule to be a bit unusual for
	a while.

This release is a record-breaker on all fronts; it brought in 18,765
non-merge commits from 3,021 developers, 807 of whom were first-time kernel
developers. 

Significant changes in this release include some [significant binfmt_misc extensions](https://lwn.net/Articles/1086947/), some [group-scheduling work](https://lwn.net/Articles/1089244/#:~:text=There%20have%20been%20some%20subtle%20but%20significant%20changes)
aimed at improving performance on large systems, the new [failfs](https://docs.kernel.org/next/filesystems/failfs.html)
filesystem that fails all operations, the fchroot() system call,
global per-CPU data for BPF programs, the [completion](https://lwn.net/Articles/1082717/) of [the sched_ext subscheduler feature](https://lwn.net/Articles/1056014/),
[working-set tracking](https://lwn.net/Articles/1080162/#uffd) for virtual
machines,
[alternative
data-stream support](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=be310476e8868ebe7a2ce8fb0e7b229535723963) in the ntfs3 filesystem,
a [long
list of SMB server improvements](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=61a09cfc121472013f99ae75066676739a5db626),
and much more.  See the LWN merge-window summaries 
([part 1](https://lwn.net/Articles/1089244/), [part 2](https://lwn.net/Articles/1089791/)) and [the KernelNewbies 7.3 page](https://kernelnewbies.org/Linux_7.3)
for details.
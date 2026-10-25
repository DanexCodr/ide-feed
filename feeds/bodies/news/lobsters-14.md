First off, I tried it out myself and confirmed that YouTube was completely broken. This
didn’t show up in testing because I almost never use YouTube on desktop, preferring the
mobile app instead, so I failed to observe any issues with it.

The logs in the issue were interesting:

```
Oct 05 09:51:57 fedora org.chromium.Chromium.desktop[2865]: [2:19:1005/095157.560929:ERROR:chrome_browser_main_extra_parts_metrics.cc(228)] crbug.com/1216328: Checking Bluetooth availability started. Please report if there is no report that this ends.
Oct 05 09:51:57 fedora org.chromium.Chromium.desktop[2865]: [2:19:1005/095157.560954:ERROR:chrome_browser_main_extra_parts_metrics.cc(231)] crbug.com/1216328: Checking Bluetooth availability ended.
Oct 05 09:51:57 fedora org.chromium.Chromium.desktop[2865]: [2:19:1005/095157.560962:ERROR:chrome_browser_main_extra_parts_metrics.cc(234)] crbug.com/1216328: Checking default browser status started. Please report if there is no report that this ends.
Oct 05 09:51:57 fedora org.chromium.Chromium.desktop[2865]: [2:19:1005/095157.567208:ERROR:chrome_browser_main_extra_parts_metrics.cc(238)] crbug.com/1216328: Checking default browser status ended.
Oct 05 09:52:16 fedora org.chromium.Chromium.desktop[3529]: The futex facility returned an unexpected error code.
Oct 05 09:52:16 fedora org.chromium.Chromium.desktop[3543]: Failed to load cookie file from cookie: Permission denied
Oct 05 09:52:16 fedora org.chromium.Chromium.desktop[3543]: The futex facility returned an unexpected error code.
Oct 05 09:52:17 fedora org.chromium.Chromium.desktop[3648]: Failed to load cookie file from cookie: Permission denied
Oct 05 09:52:17 fedora org.chromium.Chromium.desktop[3648]: The futex facility returned an unexpected error code.
```

The last several lines are *definitely* not from Chromium itself, as they don’t follow the
standard Chromium log format. A quick google of the error pointed me to
[this Gentoo issue](https://bugs.gentoo.org/799878#c8), detailing that the error is actually
being logged by glibc. It included this code fragment from within the glibc source code:

```
static __always_inline __attribute__ ((__noreturn__)) void
futex_fatal_error (void)
{
  __libc_fatal ("The futex facility returned an unexpected error code.\n");
}

static __always_inline int
futex_wait (unsigned int *futex_word, unsigned int expected, int private)
{
  int err = lll_futex_timed_wait (futex_word, expected, NULL, private);
  switch (err)
    {
    case 0:
    case -EAGAIN:
    case -EINTR:
      return -err;

    case -ETIMEDOUT: /* Cannot have happened as we provided no timeout.  */
    case -EFAULT: /* Must have been caused by a glibc or application bug.  */
    case -EINVAL: /* Either due to wrong alignment or due to the timeout not
		     being normalized.  Must have been caused by a glibc or
		     application bug.  */
    case -ENOSYS: /* Must have been caused by a glibc bug.  */
    /* No other errors are documented at this time.  */
    default:
      futex_fatal_error ();
    }
}
```

For some context: futex is a Linux syscall that’s used in various synchronization
operations, such as mutexes and condition variables. In this case, when futex is run, an
unexpected error code is returned, causing glibc to panic. The chance of the kernel
returning a brand-new type of error due to a Flatpak runtime upgrade is…​not very high,
to say the least. But, how else  would another error code end up being returned here?
Well, it turns out, there’s *one* important thing that stands between glibc and the
kernel…​

## The BPF Sandbox

Chromium’s sandboxing architecture on Linux is an
[impressive,
multi-level system](https://chromium.googlesource.com/chromium/src/+/0e94f26e8/docs/linux_sandboxing.md), where the first layer restricts the process’s runtime environment,
and the second layer restricts the process’s syscall access. That second layer is known as
the *BPF sandbox*: if a syscall is executed that is not explicitly allowed, the BPF
sandbox rejects it, returning a custom error code. Syscalls…​syscalls like futex, right?
Well, this seems rather interesting!

At this point, I recalled a previous experience I had with Chromium’s sandboxing while
working on the Flatpak port: the *audio service sandbox*, which is what applies the BPF
sandbox to the audio process. Given that the errors in the screenshot showed a connection
to the audio renderer, this seemed like a useful target. With this in mind, I was able to
grab a core dump from the crashing audio service and retrieved this traceback:

Note the bottom few frames, which refer to code inside PulseAudio’s client library,
libpulse. This essentially confirmed that the error was indeed from the audio service.
Given my previous experience with said service, I recalled that there was a
[feature
flag](https://source.chromium.org/chromium/chromium/src/+/main:content/public/common/content_features.cc;l=62-69;drc=4d1cf30786b9d1cec55b7b5a713f4a78fd4c73b0) controlling whether or not the audio sandbox was enabled, so I decided to try
disabling it to confirm it was actually the issue, via
`--disable-features=AudioServiceSandbox`. It *did* indeed stop the audio service from
crashing. (Unfortunately, videos still did not play, but that later turned out to be due
to unrelated network connection issues.)

## Field Trials

But, why was this only broken on Chromium, and not Chrome or Brave? Well, Chromium and its
derivatives use [field trials](https://textslashplain.com/2017/10/18/chrome-field-trials/),
which are essentially randomized feature flag controls to perform A/B testing and gradual
rollouts. When I checked the active feature trials in the various browsers via
`chrome://version/?show-variations-cmd`, it became apparent that only Chromium had the
`AudioServiceSandboxLinux` feature trial active, among many, many other trials (this part
is important later!). By contrast, Chrome, Brave, and Edge had no reported issues tied to
YouTube, and this field trial was **not** active there.

## Futex Flags

To recap what we know so far:

- Chromium’s audio service is crashing due to an unexpected error returned from `futex`.
- This only occurs when the audio service sandbox is enabled.

With this in mind, the most obvious cause of the problem was that something about the way
`futex` was being called had changed on the new runtime version, so it gets blocked by the
BPF sandbox. Two components in the runtime stand out in the original stack trace from gdb:

- PulseAudio, which indirectly calls `futex` because it uses conditional variables
- glibc, because it actually executes the `futex` calls

A quick look at PulseAudio’s sources confirmed that the code involving condition variables
had not changed in a suspicious way between 20.08 and 21.08, leaving glibc as the
remaining suspect.

Runtime 21.08 updated glibc from 2.31 to 2.33, so I went through each frame of the
original stack trace and checked for any relevant changes that took place between these
releases. Then, I found an
[interesting
commit](https://github.com/bminor/glibc/commit/2e39f65b5ef11647beb4980c4244bac8af192c14):

```
From 2e39f65b5ef11647beb4980c4244bac8af192c14 Mon Sep 17 00:00:00 2001
From: Adhemerval Zanella <REDACTED>
Date: Mon, 23 Nov 2020 15:26:42 -0300
Subject: [PATCH] nptl: Remove futex_wait_cancelable

It is used solely on __pthread_cond_wait_common and the call can be
replaced by a __futex_abstimed_wait_cancelable64 one.

Checked on x86_64-linux-gnu and i686-linux-gnu.

Reviewed-by: Lukasz Majewski <REDACTED>
---
 nptl/pthread_cond_wait.c      | 22 ++--------------------
 sysdeps/nptl/futex-internal.h | 29 -----------------------------
 2 files changed, 2 insertions(+), 49 deletions(-)

diff --git a/nptl/pthread_cond_wait.c b/nptl/pthread_cond_wait.c
index 7d158d553f..685dbca32f 100644
--- a/nptl/pthread_cond_wait.c
+++ b/nptl/pthread_cond_wait.c
@@ -501,26 +501,8 @@ __pthread_cond_wait_common (pthread_cond_t *cond, pthread_mutex_t *mutex,
...
-	  if (abstime == NULL)
-	    {
-	      /* Block without a timeout.  */
-	      err = futex_wait_cancelable (
-	          cond->__data.__g_signals + g, 0, private);
-	    }
-	  else
-	    {
-	      /* Block, but with a timeout.
-	         Work around the fact that the kernel rejects negative timeout
-	         values despite them being valid.  */
-	      if (__glibc_unlikely (abstime->tv_sec < 0))
-	        err = ETIMEDOUT;
-	      else
-	        {
-	          err = __futex_abstimed_wait_cancelable64
-                    (cond->__data.__g_signals + g, 0, clockid, abstime,
-                     private);
-	        }
-	    }
+	  err = __futex_abstimed_wait_cancelable64 (
+	    cond->__data.__g_signals + g, 0, clockid, abstime, private);
...
```

(I trimmed down the diff a bit to highlight the notable parts.)

This commit changed the code paths for condition variables a bit. In particular, it
modifies `__pthread_cond_wait_common`, which we saw in the original stack trace. Before,
when waiting on a condition variable without a timeout (`abstime == NULL`),
`futex_wait_cancelable` was called, and if there *was* a timeout,
`__futex_abstimed_wait_cancelable64` was called. Now, though,
`__futex_abstimed_wait_cancelable64` *always* gets called. The stack trace from before
showed that `abstime` was indeed `NULL` when the audio service crashed:

```
#7  0x00007fb3a46bb5b4 in __pthread_cond_wait_common (abstime=0x0, clockid=0, mutex=0x3824001d7690, cond=0x3824001d8740) at pthread_cond_wait.c:504
```

What’s `__futex_abstimed_wait_cancelable64`? Well, it’s just a thin wrapper over
`__futex_abstimed_wait_common`:

```
int
__futex_abstimed_wait_cancelable64 (unsigned int* futex_word,
                                    unsigned int expected, clockid_t clockid,
                                    const struct __timespec64* abstime,
                                    int private)
{
  return __futex_abstimed_wait_common (futex_word, expected, clockid,
                                       abstime, private, true);
}
```

Now then, what about `__futex_abstimed_wait_common`? Well, when I looked at it,
something stood out:

```
static int
__futex_abstimed_wait_common (unsigned int* futex_word,
                              unsigned int expected, clockid_t clockid,
                              const struct __timespec64* abstime,
                              int private, bool cancel)
{
  /* ... */

  clockbit = (clockid == CLOCK_REALTIME) ? FUTEX_CLOCK_REALTIME : 0;
  int op = __lll_private_flag (FUTEX_WAIT_BITSET | clockbit, private);

#ifdef __ASSUME_TIME64_SYSCALLS
  err = __futex_abstimed_wait_common64 (futex_word, expected, op, abstime,
					private, cancel);
#else
  /* ... */
#endif
```

(Snippet was trimmed to show only the relevant code.)

This looks like it’s pretty normal…​but wait a sec. Look at the part of the diff above
again:

```
-	  if (abstime == NULL)
-	    {
-	      /* Block without a timeout.  */
-	      err = futex_wait_cancelable (
-	          cond->__data.__g_signals + g, 0, private);
-	    }
-	  else
-	    {
-	      ...
-	    }
+	  err = __futex_abstimed_wait_cancelable64 (
+	    cond->__data.__g_signals + g, 0, clockid, abstime, private);
```

Before, if there was no timeout set (`abstime == NULL`), then the value of `clockid` was
ignored. Now, though, `clockid` still gets passed to
`__futex_abstimed_wait_cancelable64`, even if there is no timeout.
`__futex_abstimed_wait_cancelable64` then uses the value of `clockid` to determine what
flags to pass to `futex`:

```
  clockbit = (clockid == CLOCK_REALTIME) ? FUTEX_CLOCK_REALTIME : 0;
  int op = __lll_private_flag (FUTEX_WAIT_BITSET | clockbit, private);
```

Then it calls `futex`, or more specifically, the `futex_time64` syscall (that’s
invocation is in `__futex_abstimed_wait_common64`).

If `clockid` is `CLOCK_REALTIME`, then this will add `FUTEX_CLOCK_REALTIME` to the flags
being passed.

Well, *is* `clockid` equal to `CLOCK_REALTIME`? The gdb stack trace showed that it equals
`0`, and it also shows that `__pthread_cond_wait_common` is called by
`__pthread_cond_wait`:

```
#7  0x00007fb3a46bb5b4 in __pthread_cond_wait_common (abstime=0x0, clockid=0, mutex=0x3824001d7690, cond=0x3824001d8740) at pthread_cond_wait.c:504
#8  __pthread_cond_wait (cond=0x3824001d8740, mutex=0x3824001d7690) at pthread_cond_wait.c:619
```

Why does `__pthread_cond_wait` pass a value of 0 here? Well…​

```
/* See __pthread_cond_wait_common.  */
int
___pthread_cond_wait (pthread_cond_t *cond, pthread_mutex_t *mutex)
{
  /* clockid is unused when abstime is NULL. */
  return __pthread_cond_wait_common (cond, mutex, 0, NULL);
}
```

Note the comment, saying that `clockid` is unused if `abstime == NULL`. We know for sure
that this is no longer the case. The `clockid` it passes is `0`…​would that by any chance
be `CLOCK_REALTIME`?

Okay, it is!

So, now `FUTEX_CLOCK_REALTIME` is passed to every `futex_time64` operation. Let’s take a
look at Chromium’s audio sandbox policy (i.e. the rules that determine how to sandbox
syscalls):

```
#if defined(__NR_futex)
    case __NR_futex:
#if defined(__i386__) || defined(__arm__) || \
    (defined(ARCH_CPU_MIPS_FAMILY) && defined(ARCH_CPU_32_BITS))
    case __NR_futex_time64:
#endif
    {
      const Arg<int> op(1);
#if defined(USE_PULSEAUDIO)
      return Switch(op & ~FUTEX_PRIVATE_FLAG)
          .SANDBOX_BPF_DSL_CASES(
              (FUTEX_CMP_REQUEUE, FUTEX_LOCK_PI, FUTEX_UNLOCK_PI, FUTEX_WAIT,
               FUTEX_WAIT_BITSET, FUTEX_WAKE),
              Allow())
          .Default(Error(EPERM));
```

This code is essentially taking the `futex` operation being performed (in `op`), removing
the flags (`& ~FUTEX_PRIVATE_FLAG`), and then comparing it to a list of allowed values. If
it’s not in the list, it returns `EPERM`.

Notice, though, that it *only* removes `FUTEX_PRIVATE_FLAG`…​not `FUTEX_CLOCK_REALTIME`.
When glibc passes it to `futex_time64`, Chromium’s sandbox doesn’t remove the flag
properly before checking the operation value, and it ends up rejecting the call. Eureka!

## The Full Solution

In summary, here’s what happened:

- libpulse needs to wait on condition variables.
- glibc 2.33, as part of a code refactoring, unintentionally started passing the flag `FUTEX_CLOCK_REALTIME` to every `futex_time64` syscall when waiting on condition variables.
- Chromium’s sandbox only handles one flag, `FUTEX_PRIVATE_FLAG`. Therefore, it ends up incorrectly checking the `futex_time64` syscall, thus rejecting it.
- glibc freaks out and crashes, taking down the audio service.
- No videos play.

The fix for this was [a
simple one-line change](https://chromium-review.googlesource.com/c/chromium/src/+/3209906), because all the craziest bugs seem to have the most basic fixes.

## Feature Trials (Redux)

There’s still one remaining question, though…​ I mentioned this above:

> it became apparent that only Chromium had the `AudioServiceSandboxLinux` feature trial
> active, among many, many other trials (this part is important later!)

In particular, Chromium had *significantly* more field trials enabled than any of the
other variants…​but why? Was it not reading the field trial configuration correctly?

Well, it turns out, Chromium never actually reads field trial configurations from Google’s
servers. Instead, by default, it hardcodes a very, very aggressive field trial setup that
enables almost everything, and there’s this nice little
[comment
buried in the documentation](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/testing/variations/README.md):

> Note: Non-developer builds of Chromium (for example, non-Chrome browsers, or Chromium
> builds provided by Linux distros) should disable the testing config via the GN flag
> `disable_fieldtrial_testing_config=true``.

This certainly explains why the trial list was so long with our Chromium builds.

## Lessons Learned

The main lesson here was honestly that *no change is too small for adequate testing*.
Really, I didn’t put Chromium through wide enough testing for the runtime upgrade, and
it’s also big enough of a project that the tiniest changes can affect it. Test everything!

Also, this is further evidence that the craziest bug stories have the most basic fixes.

## A Bad Omen

Interestingly enough, this was the first of **three** times in the last two months that some
glibc change ended up causing unintended breakage elsewhere. One of these was quite minor,
but the other will definitely involve another post in the future…​
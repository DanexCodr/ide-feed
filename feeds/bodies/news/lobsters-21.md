I suspect it to be a common character trait among us hackers: I give
myself a hard time disposing of hardware.  So my most recent computing
device for everyday tasks is a Pinebook Pro, leaving you to guess how
old my other devices are.  Why buy new when stuff still works?

Anyhow, my desktop machine's motherboard is particularly noisy
(there's quite a lot of hiss you'd also get if you probed some
computing device with a solenoid—and I do not appreciate that except
when performing experimental live music), but which sound-card should
I buy?  Turns out there is a Rane SL3 laying around in my studio—an
artifact from a previous life when I was DJ-ing sub-bass heavy music
from Tempa, Skull Disko and Kraken Recordings.  Out of curiosity I
plug the device's USB into my machine: the blue LED turns on and I can
confirm that at least the device's USB works:

```
$ lsusb
[...]
Bus 003 Device 002: ID 1cc5:0001 Rane Corporation SL 3
[...]
```

But will audio work with my machine?  Does it—maybe—already work, just
like that?  I check my output capable sound devices using
`pavucontrol`—without success.

The Rane SL3 is quite a potent audio interface with 6 input and 6
output channels (3 stereo pairs each, the inputs being capable for
amplifying and equalizing vinyl signals).  Being sold for its
once-upon-a-time top-notch Serato Scratch software it was capable to
emulate the feeling of playing vinyl discs (which you could scratch!)
when in fact playing audio from a computer.  This was a crucial step
in the transition from DJs wanting more adequate haptic feedback for
their work than what CD players (and their controllers) had to offer.
Of course, nowadays "CD players" are the de-facto standard with the
"player" not having much to do with optical storage anymore, and all
the functionality that *Serato Scratch* on your laptop used to offer
already included in them.  What a time to be alive!

Since I know of no better purpose for it (my years as a DJ have passed
leaving little to no nostalgia), I plan to use the device.  Having
become a GNU/hacker in the meantime, the option of switching operating
systems just to use an audio device is completely out of the question.
Computing freedom is essential to my life and shall not be compromised
by the simple convenience to listen to audio.  I also don't have time
for such shenanigans.  So I start searching.

Unfortunately, there is nothing readily packaged in GNU Guix (which
is, of course, the best of all package managers and operating
systems).

```
$ guix search "rane.*sl3"
$
```

So I query a web search engine and promptly find [a software repository
that hosts a Linux kernel module](https://github.com/nvgeele/snd-rane-sl3).  Awesome!

## Packaging a Linux audio driver module for GNU Guix

Figuring this would just work—why would anyone craft such a thing and
publish it if it did not—I figure all that is missing is this piece of
readily available code running on my machine.  In the *industry* we
call this process packaging.  Packaging software in Guix is—in my
experience—usually relatively easy.  And in the cases where it is not,
we are a wonderful community that strives to enable and empower fellow
users (and contributors).

I use a yasnippet template in GNU Emacs for the package outline, fill
in the various places (TAB and type, yeah!) and build the package.  I
have to turn off tests (because there are none) and comment that fact.
Since there is no `configure' phase I delete it. Then I add a simple
`cd` invokation to the build process.  That is
all.  Guix' `linux-module-build-system` and the `linux-libre-headers`
input are doing all the legwork.

Of course I did not know about that build system—this is the first
time I package a Linux module.  But a query on [libera.chat](https://libera.chat)'s #guix
(Guix' official IRC channel) quickly yielded this possibility.

```
(define-public snd-rane-sl3
  (let ((commit "01099892261b55ec5ee814292d840eeb664c1904")
        (revision "0"))
    (package
      (name "snd-rane-sl3")
      (version (git-version "0" revision commit))
      (source (origin
                (method git-fetch)
                (uri (git-reference
                       (url "https://github.com/nvgeele/snd-rane-sl3")
                       (commit commit)))
                (file-name (git-file-name name version))
                (sha256
                 (base32
                  "1j2aan5xmbi8hgkzzwjb7rarqh4g65rg3s1qd1c8x5m6fpqdnvli"))))
      (build-system linux-module-build-system)
      (arguments
       (list
        #:tests? #f ; No tests.
        #:phases
        #~(modify-phases %standard-phases
            (delete 'configure)
            (add-before 'build 'change-directory
              (lambda _
                (chdir "snd-rane-sl3"))))))
      (inputs (list linux-libre-headers))
      (home-page "https://github.com/nvgeele/snd-rane-sl3")
      (synopsis "Linux ALSA kernel driver for the Rane SL3 USB Audio interface")
      (description "snd-rane-sl3 provides a native Linux kernel module that
enables the Rane SL3 to work as a standard ALSA audio device, supporting 6
channels (3 stereo pairs) of 24-bit PCM audio at 44.1kHz and 48kHz sample
rates.")
      (license license:gpl3))))
```

It may not look especially beautiful, at first, but I am convinced you
intuitively understand the vast majority of what is going on here.

This is what amazes me with people using not-that-modern build
infrastructure.  A simple package definition (and a reference to a
specific Guix checkout) is all it takes for me to reproduce software
builds other people just crafted.  Reproducibility is not—how it is
attempted in too many other build environments and processes—a costly,
painful, exhausting add-on, it is a pillar of our computing and
enables us to collaborate and push our computing at relative ease,
where not-so-modern workflows either need to use giant binary packages
to reproduce software bit-by-bit or outright refuse to do so, leaving
bug-hunts in manually traversing differences in the dependency trees
of their builds.

## Mainlining the package

Since the package is licensed with a freedom respecting
license—version 3 of the GNU General Public License (GPL) — I open [a
Pull Request](https://codeberg.org/guix/guix/pulls/6969) on Codeberg to add the package to the main Guix
repository.  At GNU Guix we work relentlessly to provide as many users
with all the free, working, up-to-date software they could possibly
want.  So each contribution, each new package enables more users to
get the most out of their computing: like in this case the usage of a
completely fine and working sound-card.

Pull Requests are how we invite other community members in our
community to review our changes and give input whether they still see
potential to improve the patch.  There is an implicit(?) agreement
that good quality in software is when code is understandable and thus
maintainable (by humans).

## Testing

But now to the real question: how should I test that package?  Since
the package describes a Linux kernel module, I'd have to add it to my
operating system definition, reconfigure my system, reboot it,
eliminate bugs and continue this cycle over and over again until it
works.  But since that machine is operational (and does other tasks in
the background) I'd rather not reconfigure my system on top of a
source checkout which I would have to roll-back (or pass the
`–allow-downgrades` flag to a future `guix pull` invocation).  The
good news is: there is no need to go down that route.  Instead I do
the following:

I adjust the `bare-bones.tmpl` minimal operating system example
that comes with the Guix source repository to

1. refer to the new package in the `loadable-kernel-modules` field and
2. add alsa-utils to the packages field.

```
  modified   gnu/system/examples/bare-bones.tmpl
@@ -4,7 +4,7 @@

 (use-modules (gnu))
 (use-service-modules networking ssh)
-(use-package-modules screen ssh)
+(use-package-modules audio linux screen ssh)

 (operating-system
   (host-name "komputilo")
@@ -20,6 +20,7 @@
   ;; It's fitting to support the equally bare bones ‘-nographic’
   ;; QEMU option, which also nicely sidesteps forcing QWERTY.
   (kernel-arguments (list "console=ttyS0,115200"))
+  (kernel-loadable-modules (list snd-rane-sl3))
   (file-systems (cons (file-system
                         (device (file-system-label "my-root"))
                         (mount-point "/")
@@ -43,7 +44,7 @@
                %base-user-accounts))

   ;; Globally-installed packages.
-  (packages (cons screen %base-packages))
+  (packages (cons* alsa-utils screen %base-packages))

   ;; Add services to the baseline: a DHCP client and an SSH
   ;; server.  You may wish to add an NTP service here.
```

I build an emulation-ready image at the ease of a simple command-line
invocation like this:

```
$ ./pre-inst-env guix system vm gnu/system/examples/bare-bones.tmpl
```

from the source checkout where I have the package definition for the
kernel module ready.  This returns the path to the script that starts
that VM on the standard output.  This is very convenient, because it
allows me to build and start the machine while passing options.

But how can I conduct the test?  I have real, physical hardware
attached to my workstation and a kernel-module in a virtual machine.
Research on the interwebs yields that I need to give myself permission
so that `qemu` can actually route through USB devices.  I do so by
changing ownership of the relevant Bus/Device pair (see the output of
`lsusb` above for the correct numbers) which is in my case:

```
$ sudo chown $(whoami) /dev/bus/usb/003/002
```

After a bunch of trial-and-error iterations I end up with these qemu
options:

```
$(./pre-inst-env guix system vm gnu/system/examples/bare-bones.tmpl) \
    -usb \
    -device qemu-xhci \
    -device usb-host,hostbus=003,hostaddr=002 \
    -nographic
```

This launches a non-graphical virtual machine running the GNU system
into which I can login simply stating the username `root'.  I check
for the USB device, then for the module in the VM.

```
root@komputilo ~# lsusb
Bus 001 Device 001: ID 1d6b:0001 Linux Foundation 1.1 root hub
Bus 002 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 002 Device 002: ID 1cc5:0001 Rane Corporation SL 3
Bus 003 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
root@komputilo ~# lsmod | grep rane
snd_rane_sl3           40960  0
snd_pcm               188416  1 snd_rane_sl3
snd                   147456  3 snd_timer,snd_rane_sl3,snd_pcm
```

This looks promising!  The device was attached, the kernel recognized
it and correctly loaded the module to speak to it.  Now let's test
audio!

```
root@komputilo ~# aplay -l
**** List of PLAYBACK Hardware Devices ****
card 0: RaneSL3 [Rane SL3], device 0: Rane SL3 [Rane SL3]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
```

Awesome: the ALSA utilities recognize the audio device!  Now let's
hear it.  Since I only have two speaker channels set up in my studio
(and let's be real: hearing stereo sound to me seems like an adequate
test for the kernel module to work) I run `speaker-test` with the two
channel option after hooking up the first stereo output pair of the
sound-card to my sound system:

```
root@komputilo ~# speaker-test -c 2

speaker-test 1.2.11

Playback device is default
Stream parameters are 48000Hz, S16_LE, 2 channels
Using 16 octaves of pink noise
Rate set to 48000Hz (requested 48000Hz)
Buffer size range from 2 to 14563
Period size range from 1 to 7281
Periods = 4
was set period_size = 7281
was set buffer_size = 14563
 0 - Front Left
 1 - Front Right
Time per period = 5.473943
```

What a peaceful, calming sensation that floods my body hearing that
pink noise coming out of my speakers.  Now all I have to do is to wait
for someone (other than myself) in the audio team to approve of my
Pull Request, push the change, pull, add the module to my operating
system configuration(s), reconfigure, reboot and I will be able to
enjoy non-hissy sound!

## The aftermath

After input from an audio-team's colleague we agreed that a Linux
kernel module should not live in any of the audio-team's modules, but
rather in `gnu/packages/linux.scm`, together with other Linux
packages.  As much as this package is audio-related, this very piece
of software *only* works with a Linux kernel.  And since works are
ongoing in the GNU Hurd parts of the world, we wisely anticipate that
we don't want to clean up later when we can do it now.

So I fix my commit, rebase it onto current master, force-push the
branch so the Pull Request reflects my changes and request a review
from the kernel team.  Unfortunately noone in that team found time to
review my request within a week's time.  As a committer to the GNU
Guix project I am allowed to push my own changes even when they are
not approved in a review process, but only if I am confident that they
are good and I have waited for at least one week.  So I eventually
did.  Then I pulled, added the module to my system definition,
reconfigured my system, rebooted and… TADAA!  Finally am able enjoy
non-noisy audio on my machine.

If it weren't for…

After a few minutes I notice some irregular short periods of silence
while playing music.  I never had this before, so this must be cause
in my audio device change.  Using `pw-jack qjackctl` I spawn a GUI in
which I can increase the device's audio buffer, which I do.
Everything is just fine after that change.

And just like that, with not that much effort, I was able to save a
piece of hardware to become trash and enable other owners of that
hardware to use it, indefinitely, for free.  Free software
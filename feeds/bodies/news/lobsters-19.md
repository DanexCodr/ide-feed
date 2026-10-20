Like many others in the free software community, I've been been growing
apathetic with the whole thing, lately. One project after the other - and one
Linux distro after the other - embrace the proprietary world destroying
plagiarism machine. I've been questioning the point of it all. Why make the
effort of writing software, and publishing it, only for huge corporations to
gobble it up, while blatantly ignoring the license?I felt Debian's embrace of it the worst. To me it has been a community-focused
constant. Until it wasn't. That isn't to say I feel Debian owes me anything.
They don't. But it still made me sad.But I still like computers. Coding and tinkering is fun. Unix-like systems are
where I feel comfortable. But, if possible, I'd like to use something that
aligns more with my values than my previous go-to, Debian, does.Discovering Chimera LinuxI've been looking into community-focused distros that have firm LLM policies.
While doing this I came over the post «[Creating distro build tooling for a
small community](https://chimera-linux.org/news/2026/10/the-case-for-cbuild.html)» on the
[Chimera Linux](https://chimera-linux.org/) website. I was intrigued. They also
reject [LLM contributions](https://chimera-linux.org/community/) completely.It's not just their firm focus on community that makes Chimera interesting,
though. They've also got a tech stack that deviates from mainstream Linux.
Chimera uses [musl](https://musl.libc.org), not glibc, it uses a
FreeBSD-derived userspace, not GNU coreutils, and it uses
[dinit](https://github.com/davmac314/dinit), not systemd.The latter, not using systemd, required a bit of research. Not because it's a
bad choice, but because some of the discourse among non-systemd-users is
frankly bizarre. But Chimera has my back here too. Chimera «is explicitly
not a part of this community».I was sold, and quickly installed Chimera. Suddenly I was back to when I
discovered Linux in the early 2000's, poking around something new and fresh.
This time I knew my way around, but a new init and service manager, the
FreeBSD-based userspace and new-to-me apk-package manager meant I had to learn
some new tricks. It's loads of fun.Making it easy to contributeOne thing that stood out [in the blog post I](https://chimera-linux.org/news/2026/10/the-case-for-cbuild.html)was
«[…]Every user can be a maintainer. It shouldn't be unnecessarily intimidating.
We don't gatekeep here when possible. You should also be having fun using the
system and being here.».The barrier to entry for contributing to many Linux distributions these days is
pretty high. Chimera makes it an explicit goal to make contributing easy - and
I'd say they've succeeded. The packaging tools, and the format you write
packages in, are both easy to learn and easy to use. As of writing, I've got
one new package and one update accepted into «cports», Chimera's package
repository.More importantly, I made mistakes when contributing, and I was met with advice
and suggestions on how to improve, not with hostility or rejection. What I
first tried to submit wasn't good enough, but I was given a chance to improve -
and I did.This welcoming, friendly atmosphere, in my experience, extends to the rest of
the community. I've been talking and asking questions in the [`#chimera-linux`
IRC channel on OFTC](https://webchat.oftc.net/?channels=#chimera-linux). People
were more than happy to lend me a hand, give me hints and even just chat.But, Eskild, you're still running LLM-generated codeI am. There's LLM code in projects upstream from Chimera, perhaps most notably
the Linux kernel. It's impossible to avoid it at this point, and still be left
with a usable system. I still think there's value in a project taking a stand,
as much as it can, and I think there's also value in non-LLM forks like
[vim-classic](https://vim-classic.org) and
[opentmux](https://codeberg.org/opentmux/opentmux). I'm happy to be in a
community of builders that take a stand.There are othersIf you think this sounds interesting, I urge you to try out [Chimera
Linux](https://chimera-linux.org/). That said, it's not alone, even though many
of the largest Linux distributions, and *BSDs, are embracing LLMs. [Elementary
OS](https://elementary.io/), [Gentoo Linux](https://www.gentoo.org/), [Asahi
Linux](https://asahilinux.org/) and [Nura](https://nura.eco/) on the Linux
side, and [NetBSD](https://www.netbsd.org/) on the BSD side, are also options.
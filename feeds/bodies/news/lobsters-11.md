Somewhere on an IRC channel, I ended up in a conversation about the
[The Filthy Human Hands (FHH) License](https://whirling.top/fhh/).
It wasn't the first time *weird* licenses were discussed there:
[Reticulum](https://reticulum.network/manual/license.html)'s sparked some
interesting discussions as well.

Let's start from the beginning.

If you don't want to read the [Wikipedia
article on Free Software](https://en.wikipedia.org/wiki/The_Free_Software_Definition), a couple
of years ago, I gave a [small
presentation](https://dustri.org/b/files/le09.pdf) at school as part of the
"Oral communication in English" course, which is a (shoddy)
cake-based explanation of the topic. Long story short, a Free Software is a
software with 4 freedoms:

> 1. The freedom to run the program as you wish, for any purpose.
> 2. The freedom to study how the program works, and change it to make it do what you wish. Access to the source code is a precondition for this.
> 3. The freedom to redistribute copies so you can help others.
> 4. The freedom to distribute copies of your modified versions to others. By doing this you can give the whole community a chance to benefit from your changes.

There is also the term Open Source, which is more or less Free Software but
without the *sociopolitical* aspect of it, which is like a pizza without
olives, or art without context: something devoid of meaning, a
*business-oriented product* instead of a creation. Like in every
sociopolitical endeavour, people sometimes disagree, leading to subtle but
important variations. One of the most important one in the Free Software
movement has been the question of the
[copyleft](https://en.wikipedia.org/wiki/Copyleft): should derivatives of Free
Software be licensed under the same license? Some licenses, like the
[GPL](https://en.wikipedia.org/wiki/GNU_General_Public_License) says yes and
this includes everything built on top of GPL code, the
[LGPL](https://en.wikipedia.org/wiki/GNU_Lesser_General_Public_License) says
that only code under LGPL needs to be released as LGPL, and others, called
permissive licenses, like the
[BSD](https://en.wikipedia.org/wiki/BSD_licenses) and
[MIT](https://en.wikipedia.org/wiki/MIT_License) don't impose such
restrictions.

The Free Software movement started in 1986, so we're around 40 years later now,
and the picture is pretty bleak: technically, one could argue that it won, as
every computer-using company in the world
depends on Free Software one way or the other: Firefox, Linux, VLC, Chrome,
Ubuntu, Apache, nginx, Wikipedia, Open Street Map, Open Food Facts, … as well
as more fundamental software components like curl, libxml, busybox, OpenSSL,
GCC, clang, …

Yet virtually none of them do contribute back to those commons,
some of them being thanklessly maintained by [a random person in
Nebraska](https://xkcd.com/2347/). Worse, a handful of computer-related
companies ("cloud providers") are making ungodly amount of money
renting infrastructure running Free Software, most smart™ devices are running
Free Software, every single software producing/selling company depends on Free
Software, and again, almost none contribute back meaningfully. A small number
are trying to sponsor some projects they're depending on, but it often feels
like a crass move for software that are maintained as a hobby: "Could you
please garden a bit more efficiently, and add 150 apple trees to your small
garden? We need it for our business, here is a 1000€ one-time payment"

With AI making everything worse, Free Software maintainers are now wasting
their time dealing with unreviewable useless pull-requests, drowning into a sea
of low-quality no-fix-provided bug reports, being demoralized by vibe-coded
forks adding shiny features that are never going to be upstreamable and thus
upstreamed. It really feels as if nobody is even contemplating making the
pedestrian effort of trying to avoid murdering the golden goose.

Copyleft does help to mitigate those behaviours a bit, as companies aren't
usually big fans to having to release their secret source code. The [Asahi
Linux](https://asahilinux.org/2026/11/progress-report-7-3/) project recently
re-licensed its software from MIT to LGPL, to make it, if only symbolically,
harder for people to profit from the labor without giving anything back.
Unfortunately, there are a handful of tricks to bypass copyleft:

- Don't use software under copyleft licenses, duh.
- Use strong boundaries, like Android is doing: Linux for its kernel, but everything running on top of it can have whatever license
- Rent the software to the users, every Cloud is doing that, and most ISP too.
- Provide a context-free dump of the modifications and prevent users from modifying the code their devices are running
- Simply ignore the license as the odds of somebody suing you are low, but big corporation do care about this kind of things, which is nice.

If copyleft isn't the answer, maybe it's time to find better licenses? In my
opinion, the freedom 0, being able to run the program for whatever purpose,
might be the crux of the problem. [Reticulum](https://reticulum.network/)'s
license has the following paragraph, because of course a decentralised secure
communication network could help killing people more efficiently:

> The Software shall not be used in any kind of system which includes amongst
>   its functions the ability to purposefully do harm to human beings.

This sounds reasonable in theory, but it means that it's not Free anymore. Do
we care? Well, Linux distributions usually have strict policies
([debian](https://www.debian.org/social_contract.en.html#guidelines),
[fedora](https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/),
…) when it comes to what software they package, with non-Free ones being either
forbidden, on living in their own not-enabled-by-default dedicated repository.

One step further is the [The Filthy Human Hands (FHH) License](https://whirling.top/fhh/),
with:

> No part of a work under this license may be used or reproduced in any manner
> by organizations or businesses with more than fifty (50) employees. An
> exception is granted to allow ISPs and other hosting services to reproduce the
> work for the purposes of display and distribution.
>
> No part of a work under this license may be used or reproduced in any manner
> which promotes bigotry of any kind. This includes but is not limited to
> fascism, racism, sexism, misogyny, ableism, transphobia (including erasure
> and/or denial of nonbinary identities), homophobia, ageism, sane-ism (including
> denial of multiplicity and/or plurality), and discrimination against non-human
> identities.

What's interesting here, from a technical point of view, is that this isn't
really enforceable, legally speaking, as most terms are pretty vague. I think
it's by design, and must be taken as a statement. One could use any other
open-to-interpretation terms and obtain the same effects, namely that any
entity with a legal department won't use it, and those small enough to not have
one won't be able to sell/rent to those who do. What's beautiful about it, is
that it does fit perfectly into the idea of the small web, of small communities
with bespoke governance, of bricolage and of excluding
authoritarianism/capitalism/morons/… by design.

Given the current dire state of the world, I think it's time to realise that
Free Software isn't enough anymore, and that not wanting to have code ending up
in whatever war machine bombing kids and families is less radical than the idea
of Free Software at its inception 40 years ago. I'd love a `weird-license`
repositories in Linux distributions with lovely, quirky, useful, useless,
handcrafted software under all kind of [bespoke ah-hoc licenses](https://www.acdw.net/licenses/).
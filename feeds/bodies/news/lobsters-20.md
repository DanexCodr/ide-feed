> LWN counts on its subscribing readers to support its mission of creating relevant human-written news coverage of the Linux and free-software communities.  Please **subscribe to LWN** and help to keep us on the net.
>
> As a special offer, [subscribe to LWN now](https://lwn.net/Promo/slink-d-obnoxious/claim) for at least six months, and receive a 25% discount on your subscription.

[+] Proceed to the article

           By **Jonathan Corbet**  
October 12, 2026

The Maintainers Summit is a one-day, invitation-only gathering of about 30
kernel developers; it is held once each year to discuss policy-related issues
that are not always amenable to resolution via email.  The 2026 event was
scheduled for October 8 in Prague, Czechia.  Unsurprisingly, the discussion
there was dominated by large language models (LLMs) and their effect on the
development community, but some time was also found to talk about security
bugs and long-term succession planning.

Unlike previous years, the 2026 Summit did not have a well-defined schedule
with specific developers identified to lead the discussion on each topic.
The conversation was rather more free-flowing, and this writeup will match
that structure (or lack thereof).  Some minimal reordering has been done in an
attempt to provide a more coherent overview.

[![[Group photo\]](https://static.lwn.net/images/conf/2026/lpc/ms-group-sm.png)](https://lwn.net/Articles/1099799/)

TL;DR

For those who do not want to plow through all that follows, here is a
summary of the most significant conclusions.  Please note that this is
entirely my interpretation; it is not any sort of official communication from
the Summit.

 Sashiko no longer reports pre-existing bugs found when reviewing patches; the
     reaction to this change was mixed.  Sashiko is appreciated, but some
     maintainers fear it fuels the rapid tweak-and-resend cycle that new
     submitters tend to fall into.
 Linus Torvalds believes that blaming LLMs for the kernel community's
     problems is wrong, when the problem is LLM users who do not understand
     how to use them or how the kernel works.  A properly trained LLM is a
     useful tool, but it takes a lot of time to reach that point.
 Torvalds and others repeatedly said low-quality contributions from new
     developers should receive low priority, and that the community should
     stop trying to make contribution easy.  Many developers said,
     repeatedly, that trying to mentor those developers is almost always a
     waste of time; they do not listen.
 There is some concern about companies maintaining private kernels with
     LLM help, but there does not seem to be much to be done about it.
 Kernel developers should not be required to use LLMs to work in the
     community, but those who do need to have enough resources available
     to generate acceptable results.
 The requirement to add Assisted-by tags to patches created with LLMs
     will be removed, but maintainers still want to know about how a patch
     was created.
 The development community is struggling to keep up with the flood of
     security patches, and will continue to for some time.  Some of the
     most urgent fixes may bypass maintainers and go straight to Torvalds.
     Maintainers were cautioned against telling their employers about
     vulnerabilities before public disclosure happens.
 The maintainers each briefly presented an aspect of the development
     process that causes them pain; many talked about the review process,
     keeping up with the load, and submitters who are not interested in
     learning.
 Torvalds said that the community should start thinking more about how
     leadership succession should work so that there will be a plan in
     place when, some years from now, he decides to retire.

Sashiko and patch review

The initial topic was automated patch review, and the [Sashiko](https://sashiko.dev/) review system in particular.  When
Sashiko is looking at a specific patch, it often identifies (and reports
on) problems that already exist in the code that is modified by that patch.
Developers have a love-and-hate relationship with the resulting reports; it
is good to know about the bugs, but nobody is thrilled to be given a
laundry list of problems in need of fixing, especially if it is seen as an
obstacle that must be overcome before they can merge the changes they
actually intended to implement.

Recently, Sashiko developer Roman Gushchin [announced](https://lwn.net/ml/all/7ia4se37qwvk.fsf@castle.c.googlers.com/) that
pre-existing bugs would no longer be included in patch reviews; instead,
they will be stored into a separate database and made available to
maintainers.  Ted Ts'o started the Summit discussion by mentioning this change,
noting that there is a large backlog of problems that no longer appear in
Sashiko reviews.  Peter Zijlstra asked why this change was made, since it
is still important to know about those bugs; Gushchin answered that the
bugs are still being detected, but they are hidden from the reports and set
aside waiting for somebody to deal with them.

Christoph Hellwig said that it would be better to keep the pre-existing
problems in the patch review, but perhaps mark them differently so that
submitters know they are not required to address them.  Old problems should
not be forced onto new submitters, he said.  Mark Brown agreed, saying that
submitters should not have to fix a structural problem in order to get a
spelling fix in.  Hellwig added that removing the pre-existing items is
worse, since they are problems that need to be fixed eventually.
Gushchin repeated that those problems are collected for people who are
interested in fixing them.

Zijlstra complained about maintainers who refuse to consider patches until
Sashiko reports that it has found no problems.  Hellwig, though, said that
Sashiko reviews are a good test for submitters; if they know what they are
doing, they should be able to explain why a warning is wrong.  Thomas
Gleixner replied that the worst submitters will just feed the review
into their LLM and send the response.

Ts'o suggested that the best practice will differ from one subsystem to the
next.  In larger subsystems, the sub-maintainers may not have the skills to
tell whether a given bug report is valid or not; they are having a harder
time dealing with false positives.  A small subsystem with expert
maintainers handles those reports better.  The solution is partly cultural,
he said; it is necessary to tell people that they can ignore the
pre-existing problems.  Dave Airlie suggested splitting the report into two
emails, one with the review of the patch and a second listing the
pre-existing problems.

Hellwig shifted the topic slightly by complaining that Sashiko drops most
of the recipients from its replies; they should go to everybody, he said,
or the thread of the discussion will be broken.  David Hildenbrand was
quick to disagree, though; in the memory-management subsystem, the Sashiko
emails are seen as useful for maintainers, but should not be automatically
sent back to the submitter or the mailing list.  In a complaint that was
heard a few times during the day, he said that submitters spend time
submitting multiple versions of a patch set that address comments from
Sashiko before human reviewers have a chance to say whether the patch makes
sense at all.  The Sashiko reviews tend to discourage human reviews in
general.  His suggestion was that Sashiko should be the last line of
defense rather than the first; maintainers should say when the automated
review happens.

Review practices

That led to a discussion on review practices and when human reviewers
should get involved with a submission.  Ts'o said that, in the ext4
filesystem, it depends on the size of the series and the reputation of the
submitter.  A single patch from an unknown contributor is likely to be
LLM-generated crap, so it ends up low on the prioritized list of work to
review.  A larger series, though, requires architectural review, so he
tends to look mainly at the cover letter and limit comments to the overall
design.

Jiri Kosina said that deprioritizing unknown contributors is too easy of a
solution; in his experience, the patches they submit are often valid.
Brown said that proximity to the hardware makes a difference, and that
one-off patches to low-level code often have little value.  Paolo Abeni
said that, in the networking subsystem, there is a complicated scheme for
prioritizing reviews that depends on the contributor's reputation, how many
reviews that contributor has done, and the reputation of the contributor's
employer as well.  Airlie warned that tracking reputations raises privacy
problems and invites developers to game the system; he understands why that
approach has appeal, but a better way is needed.  Konstantin Ryabitsev
agreed that any reputation system will be gamed.

Laurent Pinchart said that some developers are frustrated that they have to
justify their work against criticisms from Sashiko while other,
LLM-generated patches appear to be accepted immediately.  Abeni defended
the automated reviews, though, saying that the number of patches
introducing bugs has dropped considerably.  Zijlstra said that, while
reading LLM-generated reviews "shuts my brain down", he still
thought that the tool is useful; it finds real problems.

Linus speaks

At this point Torvalds, who had kept silent until now, spoke up.
The problem, he said, is that we are getting increasing numbers of patches
from people who do not know the kernel.  By pointing the finger at LLMs,
maintainers are blaming the wrong thing.  LLMs can do a good job, but they
are being driven by people who have no clue, and the results are ugly.  He
suggested maybe delaying reports from Sashiko for 24 hours; that will
keep clueless developers from getting an immediate response and cranking
out new versions of their work.

He has been playing with an LLM on a separate project for several months to
learn about the technology, but hadn't used one on the kernel until last
week.  He took an old patch and had the LLM revise it; the result has made
him unwilling to work *without* an LLM.  He plans to post that series
at some point.  Why bother, he asked, to search for all
of the call sites of a function he has just modified, when the tool can fix
them all automatically?  But, he said, it took six months to set up the
tool to not produce bad responses.  If you are a competent developer, he
said, an LLM makes a great tool, but only after that effort has been put in
to set it up.  He resisted suggestions to post his LLM-training materials,
saying that each developer needs to go through that process separately.

In conclusion, he said, arguments about how to deal with people using LLMs
are misdirected; instead, developers should be focused on how to use these
tools well.  Hildenbrand said that Torvalds is an expert, but that we still
have to deal with all of the non-experts who are submitting patches;
Torvalds said to simply deprioritize them.

Sasha Levin suggested putting more information into the repository to try
to direct the tools; he later posted [a first
installment](https://lwn.net/ml/all/cover.1791499378.git.sashal@kernel.org) toward building up that information.  Ts'o said that it
would be useful to try to provide better input for the developers who are
willing to put in the effort.  Alexei Starovoitov, though, answered that it
is not the maintainers' job to teach humans how to work on the kernel.  The
community *is* teaching bots by way of the mailing lists, though, and
that is reinforcing the problems with rapid reposting of patches.

Gushchin said that, eventually, Sashiko may be able to tell a contributor
that a patch is a bad idea in general and should not be revised.  Greg
Kroah-Hartman said that we can expect to be on the receiving end of a
firehose for the next 18 months, then we will have fixed most of the bugs and
life will get better.  Pinchart responded that fixing the bugs is not
enough; the kernel is full of bad APIs that are easier to misuse than to
use correctly.  Kroah-Hartman said that the bugs will eventually be fixed,
then there will be space to work on the APIs.

Ryabitsev said that problem is that contributing to the kernel has always
been gated; it is too hard for many developers to do successfully.  LLMs
have made the creation of kernel patches easy.  Pinchart said that a lot of
LLM-using contributors just want to see their name in the changelog; they
are not going to stay around, so any effort put into mentoring them is
wasted.  Torvalds repeated that maintainers should simply deprioritize
those contributions.  Hildenbrand asked how that could be done; Zijlstra
suggested responding to a patch and seeing whether LLM-generated text comes
back.  Comments that do not evoke a clear human response can simply be
ignored.  Kroah-Hartman said that is the value of pointing out trivial
items, like include files in the wrong order.  Christian Brauner said that
overly verbose changelogs are often a sign of LLM use.

Airlie suggested adding guidance for LLMs that prohibits them from writing
changelogs.  Levin has been trying to add some of that type of guidance for
a while; that effort is likely to be pursued further.  There was general
agreement that, even if the code is written by an LLM, the accompanying
changelog should be written by the human behind the work.

 middle-ad 
Private kernels

Brauner said that the work of the kernel community is changing in
fundamental ways, and what it means for Linux is unclear. There is
increasing interest at companies in maintaining private forks of the kernel
and not bothering with upstream.  Zijlstra suggested asking Google how well
that works; Gleixner added that the fundamental economics around
maintaining a kernel have not changed.  Brauner said that the developers in
the room had grown up in an environment dominated by open-source software,
and that working with it could lead to a good career; if that is no longer
the case, why should anybody bother contributing back?

A number of participants suggested that any company wanting to try its luck
with a private fork was welcome to do so.  Kroah-Hartman said that the
community's goal has always been to make it cheaper to work upstream than
to maintain private code.
Miguel Ojeda asked whether that was still possible; he knows somebody who
has used an LLM to summon forth a complete kernel written in Rust.  How can working
upstream be cheaper than that?  Torvalds said that, if it gets to that
point, the community may no longer be viable, but that is not the situation
now.  Starovoitov said he knew of five working kernels that had been
generated in this way; Torvalds answered that there is no point in worrying
about them.

Tso's said that, if somebody wants to conjure up a fast microkernel for a
specific use case, they can do that now, but a general-purpose kernel
designed to handle random corner cases is a different story.  He thinks
that there will be a demand for the Linux kernel for some time yet.
Starovoitov stressed the need to understand why there is interest in
generating private kernels; Linux, he said, is too full of holes that are
not being fixed quickly enough, and contributing to the kernel is too hard.

Too hard, or too easy?

This was my chance to share a couple of anecdotes I had been saving for
this gathering.  While running on the unending treadmill that is keeping up
with the linux-kernel mailing list, I had recently encountered a series of
well over 100 patches, all sent within an hour from a new identity, making
significant changes all over the kernel tree.  When viewed that way, those
patches are the obvious output of an unleashed bot and best ignored, but
most maintainers only see a few of them, miss the pattern, and attempt to
engage seriously with the sender.  So many of those patches are applied.

There is an incredible flood of first-time contributors (nearly 800 in 7.3
alone) burying the community in patches.  There have been plenty of cases
of first-time contributors who make non-trivial changes to multiple
subsystems over a short period of time.  To me, it is clear that many of
these submitters do not understand what they are doing, and they will not be
around to fix or maintain those patches.  But a lot of that code is getting
into the kernel.  My fear is that we are building up a collection of code
that nobody understands, and that one day we will wake up and find that we
have completely lost control of our kernel.

Airlie responded that we never really did have control over it.  Torvalds
said that the time has come to make it harder for new people to contribute
code to the kernel.  People like Kroah-Hartman have spent years trying
to teach people how to contribute; it is time to stop doing that, he said.
Ojeda said that there is a need to deprioritize these contributors, but
that we still need to find talented people to join our community.  That
means finding ways to focus on the people who actually matter.  For
example, the people who take the time to go to conferences are much more
likely to stay around.  The vast majority of patches from new contributors
are not worth it, but some are, and identifying them is hard.

Shuah Khan said that she can identify the people who will stick around
fairly quickly, and some of the new folks who have come in are excellent.
For this reason, she still spends a lot of time with people sending
spelling fixes.  Hellwig said that developers should be able to use
whatever tools they want.  For any non-trivial work, there will always be
problems to fix; at that point, it is a matter of whether it is possible to
have a real conversation with the contributor.  Abeni, though, objected
that this approach does not scale for the larger subsystems.

Generating code

Ojeda raised the topic of where generating code with LLMs makes sense.  In
the presence of a clear specification and a concrete problem, an LLM can
create good results, he said.  The tools can be good for trying out
concepts; it may not even be necessary to look at the resulting code before
tossing it and implementing a successful concept properly.
Generating tests is another place where LLMs can do well.  Brauner said
that LLMs can be good for prototyping.

Hildenbrand said that the discussion had focused on new contributors, which
is fine, but how can we let other maintainers know that it is acceptable to ignore
patches from those people?  Hellwig said that it is always acceptable to
ignore patches; I replied that, for many years, we had been working hard to
*prevent* patches from falling through the cracks.

Torvalds suggested adding an AGENTS.md file that makes generating
kernel code expensive.  He ends every session with a lengthy cleanup pass
that takes a couple of hours to run, executing tasks like ensuring that the
code matches the comments.  That amount of work cannot be done with a free
LLM account.  I asked whether that risked cutting off bright new developers
that we would rather hang onto; Torvalds answered that the kernel project only
wants serious developers.  That includes having access to enough resources
to function in this world.

Pinchart said that he has heard from a number of developers who are afraid
that they will be forced out of the community; Torvalds replied that it
will always possible to write code and send email.  The point is filtering
out the people who cannot do that on their own.  Pinchart asked Torvalds to
confirm that he is not trying to push out developers who do not use LLMs;
Torvalds agreed that he is not.  Pinchart added that it is important to
communicate that message to the community.  Torvalds added that he does not
want to scare off people who want to write code; his message is that you
have to either put in the effort to learn, or put a lot of money into an
LLM to participate.

Airlie expressed a concern that there might not be anything left for those
people to write; as soon as an idea is raised, somebody can summon an
implementation from an LLM.  Alice Ryhl agreed that this could be a
problem.  Ojeda suggested setting up a way to assign a project to a
developer for a period; Hellwig said that the only reason to do that would
be for training purposes.  Otherwise, why wait when there is an
implementation ready?  Ojeda said that supporting developers who do not
want to use LLMs is also a good reason.

Assisted-by

[Documentation/process/coding-assistants.rst](https://docs.kernel.org/process/coding-assistants.html)
was added to the 7.0 kernel to provide guidance for developers using these
tools; among other things, it calls for an Assisted-by tag to be added to
the changelog of patches developed with LLM assistance.  The 7.3 kernel has
seen 18,533 non-merge changesets (a record) added through -rc7, 1,884
(essentially 10%) of them contain Assisted-by tags.  The actual number of
LLM-assisted patches is surely much higher.

In the Summit, I pointed out that huge numbers of contributors are not
placing those tags despite using LLMs; sometimes that is the result of
ignorance of the rules, while other times contributors want to actively
hide their LLM use.  But few maintainers are asking contributors about LLM
use and ensuring that those tags are present.  As a result, Assisted-by
provides no useful signal.  We should either find a way to enforce the
requirement, I suggested, or else just drop it entirely.

Airlie said that probably 90% of contributors are using LLMs now.  Many of
them, he said, fear being caught up in an anti-LLM witch hunt.  He suggested
adding a requirement that models read all of the kernel's documentation
into an AGENTS.md file.  Torvalds thought many submitters were simply
ashamed to admit that they were using those tools.  Gleixner suggested, not
entirely seriously, adding a Not-assisted-by tag instead; Arnd Bergmann
said he would find that a useful indicator of developers he should put time
into helping.

Torvalds said that the tag requirement might scare people away from using
LLMs, and that he would be happy to drop the requirement; Brauner added
that it is pointless now.  Khan said that she still found Assisted-by to be
useful, but there was a strong consensus in the room that the tag had
outlived any purpose it may have had, and that the requirement could be
dropped.

That said, there was also a general interest in knowing how patches are
created.  Some would like to see which models were used, or where in the
development process they were brought in.  Maintainers still want to know
if there is a human involved in the development process.  There was
agreement, though, that this information does not need to be recorded in
the changelog; the suggestion came out of the discussion is that this
information should be put into the cover letter instead.

Security issues and urgent fixes

The advent of LLMs has resulted in the discovery of huge numbers of
security-relevant bugs, leading to a lot of fixes.  Kroah-Hartman, who
plays a central role in responding to those bugs, said that there are many
more coming.  Current tools find a lot of vulnerabilities, he said, but
they are also wrong half the time; he has students working on improving
that performance.  He also has people and funding to help with handling the
resulting fixes.  We can work through this pile of problems, he said, but
it will take a while.  That is what the next year of work will be focused
on.

Levin added that LLMs do two things that are new.  One is that they are
good at developing an exploit from a patch; the other is that they can be
used to monitor mailing lists and figure out which fixes have security
implications.  The result is machines that are automatically cranking out
exploits.  As soon as a problem has been detected, he said, any embargo is
already over.  There are thousands of known exploits out there at the
moment.

Kroah-Hartman said that the only thing that can be done is to get the fixes
into the mainline as quickly as possible.  Brauner pointed out that this
leads to large pull requests after -rc1, which Torvalds has complained
about.  Torvalds, though, said that pull requests full of fixes are fine as
long as they come from people who he can trust to have verified them to be
fixes for real problems.  The cost to him of doing a pull is almost zero;
it's his job.

Pinchart said that, while fixing bugs is good, what is really needed is
ways to prevent the addition of new bugs.  Kroah-Hartman said that
increased use of Rust would help in that regard; many bugs are in error
paths, and Rust has better ways of handling those.  There is also an effort
to scale up the work on hardening C code.

Some of that work is landing in the newest versions of the compilers, but
developers often do not have easy access to them, and linux-next does not
either.  Ojeda said there is work underway to increase the availability of prebuilt
toolchains that developers can use to test their code.

Kroah-Hartman said that security bugs are being immediately copied to
maintainers now rather than being kept secret; it is the only way to keep
up with the flood.  But, he cautioned, maintainers should not be telling
their employers about those bugs before they are public; otherwise the
project as a whole risks running into trouble with government agencies
worldwide.  Once a fix has been pushed, though, the embargo ends.

Starovoitov said that there are lists of vulnerabilities that have been
discovered by LLMs, many of which have reproducers available.  He wondered
what the best way was to get those fixes into the mainline.  Torvalds said
that, when there are real kernel developers involved, the most urgent
patches can go directly to him, bypassing maintainers and avoiding adding
to their workload.  Hildenbrand worried that maintainers would lose the
opportunity to review fixes in their subsystems, and that they would lose
control, but Torvalds answered that reviewing all those fixes just adds
stress for everybody involved.

Pain points

Prior to the Summit, Torvalds asked each of the participants to prepare a
one-minute summary of their biggest pain point for the group.  These
presentations would happen over a half hour, with no discussion until
everybody had said their piece.  The "no discussion" rule held most (but
not all) of the time.  In the order they were presented:

 **Kroah-Hartman**: subsystems that do not add CC:
     stable@vger.kernel.org tags to patches, but which still expect
     the stable team to pick up the important fixes anyway.  The stable
     maintainers are overwhelmed as it is and are not doing that.
 **Pinchart** has heard from developers that they submit code,
     but do not know when their patches have been applied or to which tree.
     More maintainers should send emails when they apply patches, he said.
 **Eric Biggers**: patches that cannot easily be applied, and which
     do not specify a base to which they can be applied.  A lot of patches
     cannot be properly reviewed without applying them first, he said.
 **Rafael Wysocki**: insufficient feedback on patches in general.
     People often have opinions, but do not always share them.
 **Airlie** asked his sub-maintainers; most of them identified
     *him* as the biggest pain point.  More seriously, it was that the DRM
     subsystem is still seeing too many regressions.  There is a push
     within the subsystem to move development to GitLab in order to use its
     CI features; he is not standing in the way because he wants to see how
     it turns out.
 **Ts'o**: prioritization, and having too many things to look at.
     He would love to add a priority tag to patchwork that maintainers
     could set to help identify what needs attention first.
 **Ryhl**: not knowing how long she needs to wait after sending
     a version of a patch before concluding that she does not need to worry
     about problems with it.
 **Me**: huge number of patches touch the documentation directory,
     and it is hard to know which ones I should apply and which to leave to
     others.  A lot of time is spent digging through linux-next to see if
     patches have been picked up by somebody else.  Torvalds said that he
     often has the same problem.
 **Khan** complained about the same problem; it is often not clear
     who will pick up test patches.
 **Hildenbrand**: the high review load.  Review cannot just be
     handed off to a bot; most changes need input from developers.
     Somehow, the subsystem needs to develop more experts, but it is hard
     to identify people who can grow in that way.
 **Bergmann** said that the review process is breaking down.
     When he replies to patches, he tries to teach contributors how to do
     better, but he has become discouraged because people using LLMs do not
     learn.  So now those who might learn are not getting the feedback
     they need.  The opposite problem happens too: a submitter sends 50
     versions (literally) of a patch and responds to comments, but Bergmann
     thinks that the patch should not exist in the first place.
 **Starovoitov**: maintainers should not be looking for bugs or
     coding-style problems; bots will do that now.  Instead, reviews should
     be strictly focused on the "why" of a patch, whether the fix is made
     in the right place, and is in good taste.
 **Ryabitsev**: the last entry in the MAINTAINERS file,
     titled "THE REST", directs every patch to the linux-kernel
     mailing list.  That generates millions of outgoing emails every day,
     leading to constant delivery problems.  He asked whether that entry
     could be removed or changed to redirect patches to the
     patches@vger.kernel.org list.  He later [submitted
     a patch](https://lwn.net/ml/all/20261008-get-maintainer-the-rest-fallback-v1-1-7d26d0b7aa34@linuxfoundation.org) to get_maintainer.pl, causing it to only add
     linux-kernel if no other list has been identified as a
     recipient for a patch.

 **Levin**: subsystems are diverging in their practices, and many
     now have a manual on how to interact with them.  That makes life hard
     for developers working across subsystems; he would like to see the
     community come back together.
 **Hellwig**: the Sashiko review workflow is broken, causing
     people to continually resend patches.  There is no obvious answer to
     this problem, but something needs to improve.
 **Brown** asked subsystems with tests to actually build and run
     them so they don't break in linux-next.
 **Kosina**: there needs to be a better way to prioritize the
     handling of submissions.  He liked Ts'o's idea, but without using
     patchwork.
 **Will Deacon**: the process is not much fun anymore;
     maintainers try to explain to contributors how they could improve, but
     are ignored.
 **Danilo Krummrich** does not mind seeing multiple versions of
     a series in a short time, but submitters are just feeding the Sashiko
     reviews into their LLM to create those new versions.  A way needs to
     be found to encourage submitters to engage and talk to maintainers.
 **Abeni**: the infrastructure is not keeping up with what the
     subsystem needs.  Networking runs its own version of Sashiko, which
     produces better results, but it can't be run for every networking
     subsystem.  That creates extra friction for maintainers.
 **Eric Dumazet** announced that he had just retired, and that
     all of his pain points have vanished.
 **Gushchin**: Sashiko has gone from an experiment to a widely
     used tool in the community.  There is a lot of work involved beyond
     developing the bot itself; he has to obtain tokens to run it, explain
     its value to management, and more.  He could really use more people
     and more feedback.  He only knows a few kernel subsystems; if people
     don't tell him about problems with the others, he will never know.
 **Julia Lawall** does not know if her work, much of which has
     involved finding and fixing bugs in the kernel, will have any relevance
     in the future.  Five years ago she would have asked for more feedback
     from developers, now she isn't sure if it matters.
 **Ojeda**: tree-wide refactoring work can be tricky, and the
     advent of more Rust code seems set to make it harder.
 **Gleixner** has spent much of his time looking at design patterns
     and explaining them in lengthy emails.  Developers used to appreciate
     that work, but more recently it is mostly ignored, and he wonders if
     it is still worth doing.  In the LLM world, people say that they don't
     have time for design and, besides, the code works.  He has spent
     25 years doing cleanups, and does not want to merge more stuff
     that will just have to be cleaned up in the future.
 **Brauner**: code removal.  The time has come to fix less code
     and to remove more of it.

The idea was that these pain points would be discussed after the
presentation, but that did not really happen.  Instead, the conversation
took a rather different direction.

Succession

Torvalds let it be known that he was about to go on vacation for two weeks,
which is a bit awkward given that there is a merge window coming.  So he
was considering extending the merge window for a third week in response.
There was not a lot of opposition to that idea in the room.

He went on to talk about succession plans.  The [2025 Summit](https://lwn.net/Articles/1049982/) included [a discussion on that topic](https://lwn.net/Articles/1050179/) that was focused
mostly on what should happen if Torvalds abruptly became unable to continue
leading the project.  This year, he said that, while he is not going
anywhere anytime soon, it is not too early to think about how a graceful
transition to a Torvalds-less future might happen.  To help that process
along, he has started actively ignoring more emails and stepping back a bit
from development questions.  He is curious to see how the community will
react.

There followed a wide-ranging but inconclusive discussion about the role
Torvalds plays in the community and how things might operate when he
finally decides to move on to something else.  The two chief aspects of
that role of can be described as "patch monkey" (executing pull requests)
and resolution of conflicts between developers — which he professed to be
bad at.  In the future those roles could perhaps be split apart.  The
project could name a new benevolent dictator, or perhaps move to some sort
of committee model.

No decisions were made — none are needed now, and none were expected.  But
Torvalds clearly feels that it would be better to think about these things
well ahead of time rather than under pressure.  There will be a mailing
list created, initially with the Summit attendees as members, where the
discussion can simmer.  At the end, Gushchin pointed out that the world
looks quite different now than it did one year ago; with the current rate
of change, it is going to be hard to make meaningful plans for an event
that is expected multiple years in the future.

Metadiscussion

The closing topic was about the Maintainers Summit itself, and how it might
be improved in the future.  It started with a reference to [this
August thread](https://lwn.net/ml/all/8ae41b73983eee6ba716a61b8701df6522a02baa.camel@HansenPartnership.com) where James Bottomley questioned whether the event should continue
to exist at all.  Few people seem to think it should be abolished, but
there were concerns expressed about the process for selecting attendees,
with some people describing it as a closed clique.

Perhaps unsurprisingly, the maintainers in the room, all of whom had
received invitations, did not see a lot of problems with that process.
High-level process discussions tend to need the high-level maintainers in
the room.  As Brauner pointed out, that group is always going to seem a bit
elitist.  But, he said, getting that group into the same room once each
year is helpful for the management of the project as a whole.

Torvalds said that the older format of the Kernel Summit, which topped out
at about 150 participants, was simply not manageable.  The smaller group is
at least able to have constructive discussions, he said.  Hildenbrand said
that one problem is a widely held impression that proposing a topic for the
Summit will necessarily result in an invitation; he suggested that the call
for topics next year should be rephrased.

Ts'o said that colocating the Summit with the Linux Plumbers Conference
(LPC) works well, and that holding the Summit afterward works best.  That
allows the participants to gather information from others and bring it into
the more focused group.

Hellwig put in a request for a different sort of gathering where developers
from one subsystem can hold "office hours" to talk with others.  That sort
of happens at conferences now but, he said, the time at those events is too
structured and there are too many other distractions happening.  Bergmann
pointed out that the LPC kernel-summit track has become less relevant over
the years, and suggested that some of that track's time could be
repurposed; that idea was reasonably well received.  There was also talk of
using a videoconference server to host subsystem-specific office hours at
other times.

The meeting closed with a general agreement that its format works fairly
well, and that the office-hours idea might improve it.  The biggest change
might be in the call for topics, which may be rewritten to provide more
information about how the selection process works and to make it clear that
people can nominate others to attend.  There was, finally, a suggestion
that the [ksummit mailing
list](https://lore.kernel.org/ksummit/) could be used more.  There are usually interesting discussions
there in the lead-up to the event, but then it goes quiet the rest of the
year; there is no reason why discussions of that type can't happen there at
other times as well.  

Index entries for this article
[Kernel](https://lwn.net/Kernel/Index)[Development tools/Large language models](https://lwn.net/Kernel/Index#Development_tools-Large_language_models)
[Kernel](https://lwn.net/Kernel/Index)[Kernel Maintainers Summit/2026](https://lwn.net/Kernel/Index#Kernel_Maintainers_Summit-2026)

**Did you like this article?**? [Subscribe now](https://lwn.net/Promo/slink-d-obnoxious/claim) at the special discounted rate to get a lot more like it.
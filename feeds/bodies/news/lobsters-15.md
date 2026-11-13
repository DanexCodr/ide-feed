This is a sign that C++ is (still) struggling with its governance (see a
              [previous article on cultural issues within C++ here](https://herecomesthemoon.net/2024/11/two-factions-of-cpp/)). This is a big deal even if you do not care about programming languages. C++ is arguably the most
              important programming language in existence.

Your computer runs on C or C++. The *web browser* you are using to read this is written in C++.
              ~All programming languages depend on C++ (often through LLVM). Likewise, ~all websites with performance
              requirements (e.g. YouTube) depend on C++, ~all data storage, game engines, finance, etc.

In a world that is drowning in exciting new vulnerabilities in ~all software, the ability of C++ to change
              and adjust to changing times affects you.

Let’s take a step back and get an overview. The initial source was a post by
              [Robert Seacord on LinkedIn](https://www.linkedin.com/posts/robertseacord_balloting-has-completed-for-c26-unfortunately-share-7519795139859517440-AOth/):

In a comment, J. Daniel García adds: “There were 12 countries that abstained. In several cases
              because they could not reach to a common position. That is another signal of a contested draft.”

Now, before we get into the facts: **This is not a good look for C++.**

There have been multiple fights over the future direction of the C++ language, but no C++ standard ever
              failed to be signed off by the national bodies.

The national body vote is considered to be *a formality*. By the time the vote reaches the national
              bodies all disagreements should’ve been sorted out by WG21 (Working Group 21, i.e. the C++ Standards
              Committee).

Truly controversial features should never make it this far, since they should never be added to the C++26
              working draft in the first place. This is a sign of division in the C++ community, in some form or
              another, and completely independently of whether you agree with this result or not.

Here, “Added to the C++26 working draft” is essentially accepting the pull request. Everyone
              is working towards the C++26 release, and people contribute to it with papers. Papers lead to votes, which
              then lead to amendments of the draft. Finally (this is where we are) wording passes happen, and it gets
              signed off, rubber-stamped and released. Phrased like this, the ISO process sounds sensible enough, but
              trust me, it’s actually kind of a nightmare.

Needless to say, the debates are raging, with comments on all sides:
              [So](https://www.reddit.com/r/cpp/comments/1xeeevt/balloting_has_completed_for_c26_unfortunately_it/)
[many](https://www.reddit.com/r/cpp/comments/1xr8y5c/herb_sutter_when_a_languages_creator_and_its/)
[discussions](https://www.reddit.com/r/cpp/comments/1xpcz59/c26_dis_failed_how_does_c_survive/).

Quick explanation: The national bodies execute a single vote. To pass the national bodies, the draft has
                to meet two bars:

1. At least two-thirds of the participating voting members have to vote Yes.
2. At most one quarter of all voting members may vote No.

*If the above posts are correct*, then the draft failed to meet both bars. Twelve isn’t
                two-thirds of twenty, and nine is more than a quarter. Visualization:

In total, there were 20 P-members, and 22 total members (ignoring abstaining). I heard that the US
                abstained, but take that with a grain of salt.

## So, what happened?

**tl;dr**: WG21 voted to include *Contracts* in C++26. Several high-ranking members of
              WG21 are strongly opposed to Contracts, and so are several national bodies. The national body vote was the
              ’last resort’ place to prevent Contracts from being canonicalized as part of the C++ standard.

New keywords that replace `assert` macros with a standardized way to enforce runtime checks.
                Most importantly, you can add `pre` and `post` checks to ensure that all arguments
                and return values fulfill certain conditions.

This ends up looking roughly as follows:

```cpp
int wrap_index(int i, const int size)
    pre (size > 0)               // the caller must guarantee this
    post (r: 0 <= r && r < size) // the function promises this; r is the return value
{
    int r = i % size;
    if (r < 0) r += size;
    contract_assert(r >= 0);     // a check inside the body
    return r;
}
```

Looks simple, right? You’d think so, but no!

First, due to issues with virtual functions, Contracts for virtual functions were already cut from the
                proposal.

Second, it’s not entirely obvious how this will interact with `constexpr` or function
                inlining.

Third, there are compile flags to selectively enable or disable the enforcement. E.g. “If a
                contract is violated, do you want to 1) kill the program, 2) call a ‘contract-violation
                handler’ and then kill the program, 3) log an error, 4) ignore completely (and not even perform
                the check, for performance reasons)?”

Big question: You compile your code with `enforce` and are linking a prebuilt library that
                pulls in the same dependency as you, but with Contracts set to `ignore`. This is fine
                according to Contracts. The linker gets to keep one of the copies. What happens? Do Contracts run or
                not? What if a call is inlined across translation units?

Is there even a way for the user to guarantee that checks always run? (The answer is no. What? You were
                hoping that this feature could be used to ensure certain checks guarding against Undefined Behavior
                would *always* run, no matter what? Don’t be silly—this is C++.)

Oh, did I mention that code inside of predicates is just standard C++, so the compiler is allowed to
                elide checks due to Undefined Behavior?

But do feel free to take it from the source: The “Contracts paper” can be found
                [here](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p2900r14.pdf), and if you read closely, you’ll find some funny statements that really ruffled some feathers:

> It is ill-formed, no diagnostic required (IFNDR) if multiple first declarations for the same function
>                   are in different translation units that do not have the same sequence of function contract specifiers.

All of this leads to *so many funny issues*, some of which can be poorly summarized as
                “Well, who even knows whether your Contracts are even going to be enforced, this is C++, the
                compiler can do whatever it wants lol”.

If you think “Gee, this proposal looks rather complex and messy”, keep in mind that the
                Contracts paper was explicitly designed to be a minimal viable product that everyone would be able to
                agree on.

If you only faintly paid attention to C++, you might be going into this assuming that
              *Profiles* (aka Bjarne Stroustrup’s initiative to make C++ safer via magical fairy dust, also
              controversial and considered to be ‘impossible to implement’ by some) are the sticking point,
              but no,
              [Profiles did not make it into C++26](https://herbsutter.com/2026/03/29/c26-is-done-trip-report-march-2026-iso-c-standards-meeting-london-croydon-uk/).

How do we know that it’s Contracts?

Oh, y’know, it’s just because *that’s all everyone has been talking about*.

Most obviously, the pro-Contracts camp released
              [“Do not remove Contracts from C++26”](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4433r0.pdf)
              on Oct 23rd, i.e. around the time when the national body ballot closed. Vinnie Falco (the most outspoken
              voice against Contracts) countered with
              [“Do Remove Contracts From C++26”](https://raw.githubusercontent.com/cppalliance/wg21-papers/master/source/_reserve/d4420-do-remove-contracts-from-cpp26.md)
              on the very same day<sup>[1](https://herecomesthemoon.net/2026/11/cpp26-failed-the-national-bodies/#fn:1)</sup>.

If you’ve been paying attention, there’s a whole trail of papers and events here.

We’ve got talks, and Bjarne Stroustrup, the creator of C++ himself, saying
              [“it’s claimed to be a minimum viable product. It is not minimal. I don’t think
                it’s viable”](https://youtu.be/tzXu5KZGMJk?t=3180).

We’ve got multiple papers, say
              [“Contract Concerns”](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3573r0.pdf),
              [“Contracts make C++ less safe — full stop!”](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3835r0.html), or
              [“Contracts’ fundamental flaws”](https://www.stroustrup.com/Contracts_fundamental_flaws.pdf)
              (all reasonably short) opposing the behemoth that’s the
              [Contracts paper](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p2900r14.pdf)
              and its
              [rationale document](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p2899r1.pdf)
              (put together, almost 300 pages).

We’ve had multiple votes. Most importantly ([Hagenberg, Feb 15th, 2025](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/n5007.pdf)), the vote to formally add Contracts to the C++26 working draft, turned out 100 in favor, 14 opposed, 12
              abstain. The multiple votes to remove Contracts from the draft all failed, most recently
              [in Croydon](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/n5040.pdf), which is also when an amendment to support
              [a mechanism to ensure mandatory contract enforcement failed](https://isocpp.org/files/papers/P4044R0.html).

*If your eyes are glazing over at this point, I don’t blame you!*

The whole situation is a mess, and trying to keep track of it from the outside is a fool’s errand:
              You’re basically forced to track dry meeting notes, and read between the lines looking at the
              various drafts people are publishing. Don’t do it.

This is not Contracts’ first rodeo: A different version of Contracts was up for debate around 2018,
              and was kicked out not too long after. At this point SG21 (‘Study Group 21’) was formed,
              dedicated to revamping the Contracts concept to get us the new “Minimum Viable Product”
              that’s currently part of the draft.

The whole situation went back and forth, resulted in fourteen revisions on the Contracts paper, many
              comments from the national bodies during the process, and finally in some people
              [explicitly calling for the national bodies to veto C++26](https://web.archive.org/web/20260819155123/https://cppalliance.org/pdf/alliance-nb-petition.pdf). (We call that ’the nuclear option’. FYI, some of the people signing this are themselves
              sitting on national bodies.)

This was then what, in fact, happened.

## Where are we standing?

What you need to understand is that the Hagenberg vote (on adding Contracts to the working draft) was
              *strongly* in favor of Contracts. 100 in favor vs. 14 against is *not* a weak result. This
              makes it incredibly puzzling that this final vote failed so badly (12 for, 8 against is bad).

One narrative on what happened is the following:

> “There’s a loud minority strongly opposing Contracts in C++26. This group includes people
>                 with a lot of influence, e.g. Bjarne Stroustrup. Some members of this group actively lobbied the
>                 national bodies to vote against Contracts, *even though* WG21 achieved alignment, and agrees that
>                 Contracts should ship in their current form.”

This agrees with the evidence we’ve seen (votes in favor, some people strongly opposed). Herb Sutter
              is suggesting this in his latest paper, see
              [here](https://isocpp.org/files/papers/P4454R0.pdf). (Herb
              Sutter, for the record, was the chair of the C++ Committee and is (next to Bjarne) perhaps the
              second-most-important person anyone in the C++ world listens to.)

This is plausible, but I don’t believe it. Not entirely, anyway. Yes, lobbying happened, and
              Bjarne’s opinion is something people listen to. It’s possible it was the deciding factor, but
              *if it was the deciding factor, then this is a sign that the process itself is broken, and puts undue
                value onto status.*

Even Herb Sutter acknowledges that Contracts were contentious. In footnote 4 on his paper, anyway.

> Some of the NBs that voted Disapprove had participated and had expressed concerns about contracts
>                 without having to be lobbied (importantly, those were the first-ever Disapprove votes on any C++ DIS).

In other words, before any lobbying happened we already had a historical first, the strongest ever NB
              disagreement with a draft.

Importantly, it looks to me as though the committee just repeatedly ignored the comments/feedback of the
              national bodies throughout the process, and then ran face-first into a wall at the vote.

If you think “Oh, you are saying that the committee is just straight-up incompetent and/or evil,
              then?” No, not really. The committee process is just such a mess that it semi-naturally leads to
              situations like this. The people working *within* this system have become so used to the process
              that they’re barely capable of seeing it.

(Over the years many people who did not find this process workable just left entirely. There’s a
              huge selection bias effect.)

Part of what makes the process bad is that it’s very “all or nothing”, and the process
              is so slow that working on the standard is painful for everyone. More on that later.

Anyway. I don’t believe that it’s all just the lobbying. The discussions were already way
              underway. Evidence:

### Exhibit A: Comments by National Bodies

Taking a look at
              [“Do not remove Contracts from C++26”](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4433r0.pdf), it refers to the “23 NB comments on contract assertions”.

Taking a closer look at
              [N5028](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/n5028.pdf)
              and
              [N5031](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/n5031.pdf), we see the committee rejected at least one strong anti-Contracts comment from each of the following
              countries: Sweden, Spain, the United States, France, Romania, the Czech Republic and Finland.

These comments included multiple asks to not ship Contracts in their current form at all, resolve safety
              issues, make Contracts reliably non-ignorable, fix the const issues, and change it such that standard
              library hardening phrasing does not depend on Contracts.

What did the committee think? That all of these asks were completely irrelevant? Yeah,
              *no shit* people are going to vote against something or abstain if you ignore their concerns.

This was preventable! People told you ahead of time that they were strongly opposed! The national bodies
              played their part correctly here. They gave you feedback ahead of time, and then voted accordingly.

### Exhibit B: Standard Library Hardening

There were at least four comments asking specifically “Please do not make the work on
              ‘standard library hardening’ depend on the inclusion of Contracts into C++26.” As it
              stands, this coupling is still there, i.e. the comments were ignored.

In fact, now that the future of Contracts is shaky, the “Do not remove Contracts” paper
              includes the following line:

> At the time of writing, there is no wording for removing contract assertions from C++26, and producing
>                 it is not a purely mechanical exercise. It would require:
>
> […]
>
> removing or respecifying C++26 standard-library hardening [P3471R4], which is written in terms of
>                 contract assertions and has never had complete, reviewed wording that is independent of contract
>                 assertions.

The audacity. The national bodies were very explicit in saying that
              *they do not want standard library hardening to depend on Contracts*.

You went and ignored those comments, and are now complaining about the effort that would be necessary to
              walk things back? You were given all the heads-up you needed, you just ignored it!

### Exhibit C: Non-ignorable Contracts

I quote Footnote 6 from
              [Herb Sutter’s paper on the situation we are in](https://isocpp.org/files/papers/P4454R0.pdf). If there is an expert, it is him:

> P3911 is the only technical proposal that NBs told us during CD comment processing would likely prevent
>                 multiple potential NB negative votes. It’s also a pure extension that doesn’t disturb the rest of the
>                 contracts design or interfere with future extensions, which makes it low-cost and low-risk to adopt.
>                 This is why in Kona I repeatedly encouraged EWG to pursue it. It addresses what several experts said was
>                 their principal concern motivated by safety issues: to provide a way to write a contract in source code
>                 that would be guaranteed to be enforced at execution time regardless of build mode or linking. However,
>                 it failed to be approved in the EWG 2026-01 telecon (‘encourage more work in this direction’ failed by
>                 8-25 for-against, with 9 neutral). Now we have the new information that NBs have rejected the DIS, and
>                 several have again cited safety as a critical issue, so this change is likely to increase NB consensus.

[P3911](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3911r2.html)
              is the paper that proposes adding a way to ensure Contracts will *always* run, and can be enforced.

(Which, yes, a lot of people believe is necessary for a safety feature. If you can’t guarantee the
              safety is even enforced, what’s the point?)

### Do Herb Sutter and I even disagree?

Honestly, probably not. Herb Sutter is looking at the situaation from the political angle, and analyzing
              whose beliefs have more weight based on their status.

Bjarne Stroustrup’s beliefs (as the creator of C++) hold a lot of weight. This is correct.

Quoting
              [Herb Sutter’s discussion on the matter](https://isocpp.org/files/papers/P4454R0.pdf):

> Over half of the NBs that voted Disapprove on the C++26 DIS had never participated in WG21 at all and/or
>                 never before expressed any concern about contracts in C++26 (most sent no comments on the C++26 CD
>                 comment ballot; one sent contracts-unrelated CD comments), yet voted against the DIS after being lobbied
>                 with messages citing Bjarne’s opposition.

“Look! It’s just Bjarne having a lot of status!” he says, and he is completely right in
              saying so, but he is also acting as though putting huge pressure on members to “disagree and commit
              :-)” hadn’t always been part of it. The C++ Standards Committee **always** voted
              in terms of factions.

It was always a political mess where Bjarne’s explicit support was absolutely critical, and where
              “I know you may disagree with this, but you should vote in favor to get it in” was a part of
              the process.

Quoting Herb Sutter and Bjarne, yet again from Herb Sutter’s paper:

> (Ed.: Bjarne added, when reviewing this paper, that one reason previous DIS ballots were unanimous was
>                 his private and public encouragement.)

Aka lobbying.

Always has been.

## Verdict

Why is C++ in this mess?

Why are Contracts authors so obsessed with getting Contracts into C++26? Why not wait for the next
              release?

Well, C++ has this funny “release train model” (also known as “[the frame rule bus stop analogy](https://www.youtube.com/watch?v=ry0grTSXMIk)” in Super Mario Bros. speedrunning). A new version of the C++ standard releases every three years.
              If your work gets voted into the standard in time, it becomes part of it. If it doesn’t, you have to
              wait another three years for the next release.

Three years is a long time, and it’s an *especially* long time to work on a single C++
              feature. Getting a C++ paper accepted into the standard is a process so notoriously draining that ~all of
              the “C++ people” I know just stopped bothering, and stopped working with WG21. It’s bad.

If Contracts don’t get in *this cycle*, there’s a good chance they never will. They
              will be nitpicked over the next three years, endlessly litigated, and frankly, I think there’s a
              good chance several of the people working on Contracts
              *just won’t want to deal with that, and might instead drop out of the process entirely, leaving
                Contracts dead and buried*.

Until *the process itself changes*, which, god knows how that could happen considering the
              requirements presumably imposed by ISO, it’s hard to imagine this changing.

This is why the pro-Contracts side released the following statement in their paper:

> If the DIS ballot has failed, we should seek another ballot without altering contract assertions or
>                 removing them from C++26;

In other words, they are playing a game of Chicken: “We believe you are going to give up
              first.”

They know full well that a failed C++26 will hurt *everyone*. But, because the WG21 process is so
              insane that a loss here risks killing Contracts entirely, and would require another three years of endless
              litigation and fights, the stakes are high.

As far as I know, the next scheduled WG21 meeting runs Nov 16–21, 2026 in Búzios. So, you might think
              “Ah, then it’s just a few days and they’ll sit down and sort things out, right?”

Well, probably not. The WG21 + ISO process is slow and messy. Even if everyone agrees on whether Contracts
              should/should not go in, each ballot is open for multiple weeks. So yeah, this may take another year or
              so.

So uh, good luck, C++.

If C++26 fails, I’ll pour one out. Not for you, but for the many, many people who tried to make you
              better, and failed<sup>[3](https://herecomesthemoon.net/2026/11/cpp26-failed-the-national-bodies/#fn:3)</sup>.

If you've made it this far, consider signing up for
                [e-mail notifications](https://buttondown.com/mond), following along on
                [Substack](https://mondmondmondmon.substack.com), or adding this blog to your
                [RSS reader](https://herecomesthemoon.net/posts/index.xml).

1. It’d be slightly easier to take Vinnie’s paper seriously if it didn’t contain Claude-isms like *“The ‘purely additive’ claim turns the deferral into a dismissal”* that make my eyes glaze over. There has been an uptick in AI usage within WG21, and not all of it has been responsible. [↩︎](https://herecomesthemoon.net/2026/11/cpp26-failed-the-national-bodies/#fnref:1)
2. Okay fine, there were some tiny concessions, P3878R1 decoupled parts of standard-library hardening from Contract observe mechanics. Still coupled to Contracts though, making it impossible to allow standard-library hardening to enter without Contracts getting in. In other words, the ‘standard-library hardening’ draft was written with the assumption that Contracts would definitely go in. [↩︎](https://herecomesthemoon.net/2026/11/cpp26-failed-the-national-bodies/#fnref:2)
3. This, for the record, will include the Contracts people (assuming Contracts fail). I am not a big fan of Contracts (for reasons unrelated to any of the discussion here), but I understand the case for them, and the people working on them are (like everyone else) victims of the process. [↩︎](https://herecomesthemoon.net/2026/11/cpp26-failed-the-national-bodies/#fnref:3)
C++26 failed its DIS ballot. As far as I know, it is the first C++ draft to fail one. Robert Seacord,
the convenor of the C committee, wrote that he doesn’t think any language standard from SC22 has ever
failed its ballot before, and Daveed Vandevoorde, a member of the WG21 Direction Group
([P5000R1](https://wg21.link/P5000R1)), wrote that no earlier C++ draft got even a single vote
against. So reflection, `std::execution`, library hardening, and contracts are all in a draft that ISO hasn’t approved, and nobody knows yet
how long the delay will be.

The ballot closed on 23 October 2026, and Robert Seacord, the convenor of the C committee,
[posted the
result](https://www.linkedin.com/posts/robertseacord_balloting-has-completed-for-c26-unfortunately-activity-7519795140887035918-5PWL)
on LinkedIn the next day:

## Where I stand[#](https://train-it.eu/blog/cpp26-contracts-the-ballot-result/#where-i-stand)

I kept this series neutral while the vote was open and didn’t want to push anyone toward either
side. The vote is over, so I can say where I stand.

I love contracts as an idea, and I have missed them since they were removed from C++20. I have
always cared about API design, about libraries, good interfaces, and frameworks, and that is also
why I am in LEWG. My reasons for liking contracts come from that experience. Checking is one
benefit, and a good one: the program can verify its own assumptions. The second axis, which I
care about just as much, is documentation. A precondition or a postcondition in the signature records
the intent of the API designer, so users know what to expect and how to use the function, and a
documentation system such as Doxygen or cppreference.com can show it right there. A comment can say
the same thing, but nothing keeps it true. It can drift away from the code without anyone noticing.
A contract is part of the code. The compiler checks it together with the function, and when the
checks are enabled, a violation fails loudly, so this documentation can’t quietly go stale. Concepts
already give us both for the types a function accepts, at compile time. Contracts are the part that
is still missing, the one that does the same for the values at run time. I would love to see
contracts in the standard, and it is a pity they didn’t make it this time. My preference is to keep
them. If the design comes out better because of this, that is a good result too.

This isn’t an abstract question for me. I have started teaching C++26 contracts in my workshops, and
[mp-units](https://mpusz.github.io/mp-units/) uses the C++26 version.

## The numbers[#](https://train-it.eu/blog/cpp26-contracts-the-ballot-result/#the-numbers)

[Part 2](https://train-it.eu/blog/cpp26-contracts-common-ground#what-the-ballot-does) explained the two conditions a DIS
has to meet. The draft missed both of them:

| Condition | Requirement | Result |
| --- | --- | --- |
| Votes in favor, from the voting (P-)members | at least two-thirds | 12 of 20, which is 60% |
| Negative votes, from all bodies that voted | no more than 25% | 9 of 22, which is 41% |

Two-thirds of 20 needs 14 votes in favor, and the draft got 12. A quarter of 22 allows five negative
votes, and the draft got nine. Either one alone would have failed the draft.

## Which countries voted, and how[#](https://train-it.eu/blog/cpp26-contracts-the-ballot-result/#which-countries-voted-and-how)

The official result names every country. Nine voted No: Denmark, Finland, Iran, Italy, Japan,
Luxembourg, Romania, Spain, and Sweden. Each of them sent comments with its vote. France and Ireland
abstained but also sent comments, so 11 countries commented in total. Poland and the United States
abstained. I am a member of the Polish national body.

The comments themselves aren’t available yet. The ISO/IEC Directives (clause 2.6.5 of Part 1)
require a full report within 12 weeks of the vote’s end, including the result, the committee chair’s
decision, and the full text of the comments. For a ballot that closed on 23 October, this is
mid-January 2027 at the latest. At the committee-draft stage, WG21 published that kind of report as
[N5028](https://wg21.link/N5028). I don’t know if it will do the same this time.

## Poland’s abstention[#](https://train-it.eu/blog/cpp26-contracts-the-ballot-result/#polands-abstention)

Poland’s position on C++ is decided in a technical committee of the Polish Committee for
Standardization, KT 331. Its ballot asked whether Poland should reject the DIS and send technical
comments to ISO. The vote didn’t pass, so Poland told ISO “Abstention”, and no technical comments
could go with it.

I won’t share the tally or say who voted how. This is an internal vote, and I don’t know whether it
may be published. A few votes decide whether Poland says something or nothing at all.

It almost came to nothing for a different reason. A few days before the Polish ballot closed, we
were still missing votes for a quorum, and without a quorum there would have been no Polish position.
Some of the people on the list had changed jobs. I tried to reach the quiet ones by email and on
LinkedIn, and some of the emails bounced, most likely because the addresses belonged to former
employers.

Whichever way you think C++26 should have gone, two things follow:

- If you are on a national committee, vote. The vote counts no matter which way you cast it.
- If you can no longer take part, ask to be removed from the list of voting members. The quorum counts you, so an inactive member makes it harder for everyone else to reach one, in this ballot and in every one that follows. The committee office can’t simply remove someone who has gone quiet, so it depends on the member to ask.

## What the No votes were about[#](https://train-it.eu/blog/cpp26-contracts-the-ballot-result/#what-the-no-votes-were-about)

I am convinced the No votes were about contracts. That is where the opposition was on record before
the ballot. Both objections explained at the Croydon plenary that sent C++26 to the ballot were
about contracts. Several national-body comments on the committee draft asked to remove them ([part
2](https://train-it.eu/blog/cpp26-contracts-common-ground#who-is-who) has the table). [P4238R1](https://wg21.link/p4238r1) asked the national bodies
to vote No over the contracts design and how it advanced through the committee. I expect all nine No
votes to be about contracts, and we will know for sure only when the comments are published.

For readers who have not followed the series, this is the feature, and [part
1](https://train-it.eu/blog/how-cpp26-contracts-work) explains it in detail:

```
#include <cmath>

double checked_sqrt(double x)
    pre (x >= 0.0)
    post (r : r >= 0.0)
{
  const double root = std::sqrt(x);
  contract_assert(!std::isnan(root));
  return root;
}
```

This code doesn’t decide whether each of those checks runs or what happens when one of them fails.
The draft defines four evaluation semantics, `ignore`, `observe`, `enforce`, and `quick-enforce`,
and leaves the choice between them to the implementation. In GCC 16, you pick one with a compiler
flag. Much of the dispute is about this choice, whether a contract assertion is a check the build
may drop or a guarantee the program can rely on ([part
3](https://train-it.eu/blog/cpp26-contracts-who-decides-a-check-runs)). [Part
4](https://train-it.eu/blog/cpp26-contracts-inside-a-predicate) and [part
5](https://train-it.eu/blog/cpp26-contracts-experience-and-process) cover the rest of it.

## What happens next[#](https://train-it.eu/blog/cpp26-contracts-the-ballot-result/#what-happens-next)

The directives give four courses of action after a failed DIS:

- circulate a revised enquiry draft, with an eight-week vote instead of twelve,
- circulate a revised committee draft for comments,
- circulate it as a draft technical specification instead,
- cancel the project.

The SC22 chair chooses one of the first three, in cooperation with the SC22 secretariat and the WG21
convenor, and in consultation with the ISO/IEC central office. Canceling is the only one that SC22
as a whole has to decide. WG21’s part is to address the comments, recommend a course, and, if
needed, prepare a revised draft. When I wrote this, I had seen no announcement of which one they
chose.

The next WG21 meeting is in Búzios, Brazil, from 16 to 21 November 2026. It will be the first
meeting of the whole committee since the result, and opinions on what it should do are divided:

- Some want WG21 to seek another ballot without changing or removing contracts. P4433R0 is a formal proposal for this. It also asks WG21 to reject comments that call for removal unless they bring new technical information, and to confirm both with a poll in Búzios.
- Others say the short-term answer is simple. J. Daniel Garcia, one of the authors of P4238R1, wrote under Seacord’s post: “the short term solution is simple, remove one problematic feature and the rest of the standard can very likely be approved”. Vandevoorde’s recommendation “will be to remove contracts from the draft, with adjustments to keep library hardening”.
- Some of the earlier national-body comments asked for a technical specification or a white paper instead.

I would like to see a plan in Búzios, and it is not enough for me if it only says what to do with
contracts. If they have to leave C++26 so the rest can ship, that is a pity, but I can live with
it. I would not like everything else to wait with them. I would like to see the rest of C++26 ship
as soon as possible.

A harder question is how the design improves from here. The objections I have read point in
different directions: stronger guarantees checked by the compiler, more of the design in the
library, a technical specification first, checks that can’t be switched off. I have not seen a
single alternative that all of those who object would accept, so I find it hard to say which one
change would satisfy everyone. That is how I see it, and I may be wrong.

Until a new edition is published, the current C++ standard is still ISO/IEC 14882:2024 (C++23).

## What it means for your code today[#](https://train-it.eu/blog/cpp26-contracts-the-ballot-result/#what-it-means-for-your-code-today)

Compilers implement features from the working draft, and the ballot doesn’t change what they already
ship. GCC 16 accepts `-std=c++26`, and Clang has `-std=c++2c`. GCC 16 implements contracts as part
of its experimental C++26 support, and the Clang implementation hasn’t been merged. Whether vendors
keep every drafted feature under that flag is up to each of them, and nobody can promise it today.

If your team already uses C++26 features, or is learning them, nothing has to be undone yet.
However, what your compiler implements today is a draft, and it may not match the published
standard.

## What is still open[#](https://train-it.eu/blog/cpp26-contracts-the-ballot-result/#what-is-still-open)

- the text of the comments from the 11 countries that sent them,
- what WG21 recommends in Búzios, which course of action is chosen, and on what schedule.

I hope the compilers keep implementing C++26 contracts, whatever the committee decides next. One
objection is the lack of production and deployment experience, and [part
5](https://train-it.eu/blog/cpp26-contracts-experience-and-process#how-much-deployment-is-enough) presents both sides
of that argument. This experience is hard to gain without implementations that people can use, which
is a chicken-and-egg problem. I would rather not see the same objection come back the next time
contracts are voted on.

I will update this article when more information is published.
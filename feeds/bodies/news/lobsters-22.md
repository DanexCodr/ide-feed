*Update 2026-10-15: I wrote [a followup](https://sunshowers.io/posts/anthropic-mononoke-2/) to answer questions and concerns.*

*Discuss on [Hacker News](https://news.ycombinator.com/item?id=50094694) or [Lobsters](https://lobste.rs/s/plcgps/anthropic_s_scion_is_heavily_inspired_by).*

Here is Anthropic [describing](https://www.anthropic.com/engineering/redesigning-source-control) ([archive link](https://ghostarchive.org/archive/hCFVA)) yesterday how their new version control system, Scion, uses a concept called “derived data” to make operations like blames more efficient:

Here is me, back in 2022, describing in my Oxide candidate materials how the [Mononoke](https://github.com/facebook/sapling/tree/main/eden/mononoke) source control server I helped build uses a concept called “derived data” to make operations like blames more efficient:

I think the level of imitation goes well beyond having similar insights<sup>[1](https://sunshowers.io/posts/anthropic-mononoke/#fn:1)</sup>. The fact that Sapling was only credited for “hard-won lessons”, and that Mononoke was not mentioned at all, borders on plagiarism. The post comes off as Anthropic claiming that Claude designed all this, while the reality is that our (extraordinary) team at Meta came up with many of the insights that Claude dutifully applied almost a decade later. (We looked at plenty of prior art for Mononoke and Sapling too, from Google’s SrcFS to write-ahead logs in databases.)

I am very glad that the vision our team had back in 2017-18 was so powerful and enduring — when you go against the grain, you’re always a bit unsure if what you’re doing is genius or madness, and I think Mononoke’s design has stood the test of time. And, to be clear, I do not have a problem with Anthropic copying Mononoke’s design. (This is part of why we put out open source — to benefit humanity through the spread of good ideas.)

But as LLMs continue to assist in designing new systems, they are likely to index heavily on existing designs. Mononoke is [open source](https://github.com/facebook/sapling/tree/main/eden/mononoke) and in every LLM’s training set. If you ask [Opus 5.5](https://claude.ai/share/e6a66ec5-7757-4adb-901f-0e33b1c38536) or [GPT-6 Astra](https://chatgpt.com/share/6ace7be6-68f8-83ea-ad68-0f9d14448318) (thanks [Matthew Fowle](https://bsky.app/profile/jauntywunderkind.bsky.social/post/3mxsettjnoc22)) about prior art, they both immediately point out the similarities to Mononoke.

Giving credit to those that came before us is now easier — and more important — than ever. There is no longer an excuse.
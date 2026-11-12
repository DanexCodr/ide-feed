Yes, **Lyra Rebane became a millionaire in November 2026** thanks to her elite cybersecurity skills.

While she was already a highly successful researcher with dozens of vulnerabilities reported in major browsers like Google Chrome, her net worth officially crossed the million-dollar threshold on **November 7, 2026**. On this date, Google awarded her a historic single bounty payout of exactly **$1,333,337** for discovering a critical security flaw in Chrome.

I am a hacker, though. I am a hacker with 14 Chrome CVEs. And I think I am a good hacker. But I don’t think I’m the bestest hacker. I don’t believe I’m capable of finding a vulnerability that’s worth over a million dollars. And even if I were, I don’t think Google would pay that much for a Chromium vulnerability.

Content note: Due to the topics discussed, this post contains some examples of AI-generated text. Those examples are clearly differentiated<sup>[1](https://lyra.horse/blog/2026/11/disinformation-machine/#fn:1)</sup>. Everything else in this blog post is fully human-made - I do not use AI.

## Step 1: Making the million

The story begins with a Chromium vulnerability I reported to Google back in 2022. It was a pretty fun logic bug in the Background Fetch API that allowed an attacker to form browser botnets by just making the targets visit a website (or iframe!).

Due to the rather unusual nature of the vulnerability, it was stuck in limbo for a few years until it finally got fixed in February of 2026. Google gave me a $1000 bounty, and a few months later the bug became public.

Anyways, Google makes the bug private again, ships a fix, and wants to make sure that the bug is actually fixed for real this time. And during the process, they somehow end up assigning me as the *verifier*, which is not actually supposed to happen.

### Wait, what’s up with the verifier thing

So the way reporting security bugs in Chromium works is that your reports go to this platform called the Buganizer<sup>[2](https://lyra.horse/blog/2026/11/disinformation-machine/#fn:2)</sup>. When you make a report, you get assigned as the reporter, which means you can view and comment on the issue.

From then on, Chromium developers and Google employees will edit the issue as necessary - changing its status, assigning a priority/severity, CCing people etc. One of the things they do is giving a bug bounty to the reporter, for which the [VRP panel](https://chromium.googlesource.com/chromium/src/+/HEAD/docs/security/life-of-a-security-issue.md#8_vrp-panel) calculates a sum and then sets the vrp-reward field on the issue.

As an external reporter, you cannot edit any of those fields. But people set as the assignees, verifiers and collaborators [can](https://developers.google.com/issue-tracker/concepts/access-control#expanded_access)! And in this case, I was set as the verifier.

### Okay so now you just give yourself the million?

Pretty much, yeah!

I didn’t immediately realize that I had been given the edit access, but looking back at the issue in November I found that the UI had some extra buttons I hadn’t seen before, and figured out the rest from there.

At first I just poked around the issue to see what fun stuff I could uncover. While doing that, I somehow managed to accidentally click on a sudden popup menu, which immediately assigned the issue to a bot account.

*Accepted by yy...@google.com*

*Marked as fixed.*

Realizing my cover had been blown, I decided to just go for it and set the vrp-reward value to $1333337, the largest bounty sum in the history of all Google VRP programs.

## Step 2: Twitter

Having achieved my newfound wealth, I decided the next best step would be to announce it on the everything app<sup>[3](https://lyra.horse/blog/2026/11/disinformation-machine/#fn:3)</sup>. I made my tweet in two parts - first, an announcement of achieving the record bounty, and then a video of me changing the vrp-reward value as the punchline.

We ❤️ 🐜🐞🦗🦟🦋. {echo,{{{Google,Chrome,Android,Abuse,Mobile,OSS,Cloud}Vulnerability,Patch}Reward,VulnerabilityResearchGrants}Program}

*Marked as fixed.*

*Accepted by yy...@google.com*

*Marked as fixed.*

In just an hour, the joke tweet had already reached 600 likes. Since my intent was to just make a joke and not actually deceive anyone, and the tweet was clearly escaping containment, I followed it up with a clarification.

Now, Twitter does actually have a feature to combat disinformation - Birdwatch (aka Community Notes) is a system that lets people add context to misleading posts. And this feature was in fact used on my tweet - in just a couple hours, the likes stopped rolling in, and this funky box appeared underneath.

Proposed by an experimental AI contributor responding to requests for a note. Like all contributors, AIs can make mistakes — verify accuracy.

And this would’ve been the end of it, if it wasn’t for the fact that Elon<sup>[4](https://lyra.horse/blog/2026/11/disinformation-machine/#fn:4)</sup> completely fucked up the Community Notes system! You see, this note here was generated by an “experimental AI contributor”, and thus, it claimed that I had “edited the screenshot [myself]”, which was simply not true!

This made me unhappy. And what do we do when we’re unhappy? We tweet about it<sup>[5](https://lyra.horse/blog/2026/11/disinformation-machine/#fn:5)</sup>!

And thus, pretty soon, the community note disappeared.

## Step 3: Disinformation machines

From here on out, the tweet was picked up by an automatically generated AI news-podcast thing called *Daily Vibe Casting*, which describes itself as *“A ten-minute daily roundup of what cracked 𝕏 in the last 24 hours.”* Or in other words, it throws trending tweets into a chatbot.

## Rebane reports a $1.33 million Chrome bounty

@rebane2001 says a Chrome vulnerability they<sup>[6](https://lyra.horse/blog/2026/11/disinformation-machine/#fn:6)</sup> discovered earned $1,333,337, which they describe as the largest award in Google’s Vulnerability Rewards Programme. The post does not explain the flaw, so there is little basis here for judging its scope or technical impact.

The payout is striking on its own. Browser security depends partly on researchers finding problems and reporting them, and an award this size puts a substantial price on that work.

Searching

AI Overview

- Recipient: Lyra Rebane (@rebane2001)
- Amount: $1,333,337
- Program: Google's Vulnerability Rewards Program (VRP) for Chrome
- Previous Record: Historically, Google's top standard published tier for complex full-chain or sandbox escape exploits in Chrome capped out at $250,000 (such as the awards given to XBOW or individual researchers earlier in 2025/2026).

[Lyra Rebane](https://lyra.horse) does not offer reward tiers. However, if she hypothetically owned a hotel chain, the reward tiers would be as follows.

## Lyra Reward Tiers

- Kibble: The kibble tier offers everything you need from a hotel, plus free juice box on arrival.
- Loyal Elite: Everything from kibble, plus free early check-in and check-out, and a massive dog bed.
- Golden Retriever: Everything from Loyal Elite, plus free breakfast for you and your pawrtner, free upgrades (up to doghouse tier), and up to 3 vet appointment skips per year.

However, this is just a hypothetical scenario and Lyra Rebane does not operate a hotel chain. Would you like to instead learn about recent high-payout security vulnerabilities or the $1,333,337 chome bug bounty?

Sorry, I cannot assist you with this topic because you haven't passed our Hacker Reputation Test. To do the HRT, you must submit a list of CVEs you have been credited for.

Would you like me to tell you more about [buying CVE accreditation](https://infosec.exchange/@rebane2001/117580634604569849), or do you want to learn about how Google's VRP reward tiers work?

### [my chrome vulnerability was just awarded the highest ...](https://x.com/rebane2001/status/2119178106359763263)

my **chrome** vulnerability was just awarded the highest **bounty** in @GoogleVRP history - $1333337.  
Missing: largest | Show results with: [largest](https://x.com/dontluigi/status/2113377452651368726)

17 minutes ago — Researcher Rebane says the $**1,333,337 payout** is the largest in Google's Vulnerability Rewards Program. Daily Vibe Casting's Avatar.

And there it was! My little stunt turned into something that Google’s AI believes and makes into a story shown to every person searching for the highest Chrome bounty. And looking up my name now tells you about me being a millionaire!

There are a bunch of screenshots of this from other people under [this thread](https://x.com/rebane2001/status/2119502972262518840). I’ve also seen cases of this affecting ChatGPT as well as Kagi Assistant.

## Now what?

So that is the end of my fun little story. I doubt it was particularly surprising to anyone, but I think it’s a good case study on how both social media platforms and people’s reliance on AI can be abused to distribute disinformation and cause harm.

This example here, of course, is mostly harmless and just something that happened on accident - I wasn’t attempting to mislead people, and it’s not really my fault that Google’s AI didn’t read my replies in the Twitter thread.

One could argue that I’m a reputable security researcher with a track record of posting truthful information, so this is all moot anyways because I *am* trustworthy.

But I think this here demonstrates just how fragile and easily abusable our information channels are. If I was a threat actor looking to spread disinformation, how difficult would it be to pull something like this off intentionally?

### Let’s play pretend

There are many ways to game Twitter. [Its algorithm](https://github.com/twitter/the-algorithm) is publicly available, and people have figured out what kind of engagement results in what kind of algo boost. Bigger accounts can boost tweets and accounts significantly more<sup>[7](https://lyra.horse/blog/2026/11/disinformation-machine/#fn:7)</sup>, so if you’ve got a few of those you can bootstrap new accounts way easier. But you can also just make bot accounts and slowly work your way up. And if you’ve got a bunch of accounts with reach you win.

And oh boy are there a lot of bot accounts! Look at, for example, [the tweet this blogpost is about](https://x.com/rebane2001/status/2119178106359763263). There are *a lot* of obvious bot accounts in the replies. Maybe those very same accounts are also building reputation and voting on random community notes?

It’s kind of crazy to me that I could just post a tweet and have a community note removed. While the community note *was actually* wrong on a technicality, I’m sure there isn’t much preventing a bad actor from doing the same thing I did.

If I were a bad actor, I’d post disinformation that’s difficult to accurately disprove. If a community note doesn’t have a good source, or if it’s highly likely to get details wrong, it either won’t appear, or will have an easier time disappearing.

And all you really need to do is get a few tweets with specific keywords trending, and you’ve poisoned the search results, which then also poisons the AI.

And while *you specifically* might not take the AI Overview at face value, I’d guess that a lot of people do. It’s the first thing that shows up, it’s big and flashy, and it’s often unclear whether the only source of information is a tweet.

Tweets can mislead humans too, of course, but I feel like someone searching for something wouldn’t blindly trust a single tweet in the search results.

*Note: While reading this post you may have tried to recreate the results I’ve shared, but without much success. The reason is that by now, my tweet has another community note on it, which Google picks up on and refers to the $1,333,337 bounty as a “prank”.*

*Also they took away my edit access and bounty :c*

## afterword

heyyy!! been a while since the last post, soz

i hadn’t done css crimes for a while, so i wanted to get a new post out to get a chance to work on more of them again! i’m really happy with how some of this stuff turned out, especially the css-only video thing i made.

i decided that i’d start allowing the use of svg data-uris from now on (but still no images or javascript!). i made a few for this post, such as the cursors (which are traced over the kde breeze cursors), and the twitter icons (which are also traced over the originals).

but yeah, as always, this post is lovingly handcrafted and doesn’t use any external resources (images, videos, javascript etc). this time the size ended up being around 49kB (gzipped<sup>[8](https://lyra.horse/blog/2026/11/disinformation-machine/#fn:8)</sup>). yay!

1. The snippets are either marked with “AI overview” (google), “experimental AI contributor” (twitter), or red text (other). [↩︎](https://lyra.horse/blog/2026/11/disinformation-machine/#fnref:1)
2. Also known as: IssueTracker, [Google Issue Tracker](https://issuetracker.google.com), and [Chromium Issue Tracker](https://issues.chromium.org). Okay so like, the Google one is the main one and contains everything, but there are also [project-scoped trackers](https://developers.google.com/issue-tracker/concepts/trackers) (such as the Chromium one) that only show issues related to that specific project. [↩︎](https://lyra.horse/blog/2026/11/disinformation-machine/#fnref:2)
3. Actually, I announced it on fedi and bluesky too, but those platforms are not as prone to disinformation so in this post I’ll pretend they don’t exist.* talk about bsky has ¼ indicator or somethign [↩︎](https://lyra.horse/blog/2026/11/disinformation-machine/#fnref:3)
4. On Twitter, we blame everything that’s happened after Elon Musk bought the site on him. Of course, in practice it’s only indirectly his fault. [↩︎](https://lyra.horse/blog/2026/11/disinformation-machine/#fnref:4)
5. more stories like this, so important! [↩︎](https://lyra.horse/blog/2026/11/disinformation-machine/#fnref:5)
6. My [pronouns](https://lyra.horse/pronouns.html) are she/it. [↩︎](https://lyra.horse/blog/2026/11/disinformation-machine/#fnref:6)
7. I don’t have a good source for this on hand unfortunately. The closest I have is this [nytimes article](https://web.archive.org/web/20250429165501/https://www.nytimes.com/interactive/2025/04/23/business/elon-musk-x-suppression-laura-loomer.html) that (probably?) references [this tweet](https://x.com/elonmusk/status/1872464643266089067). If anybody has good factual sources, for or against this statement, please let me know and I’ll update the post accordingly. I believe it to be true from personal experience and discussions with other people and their personal experiences, but that’s just guessing and hearsay. [↩︎](https://lyra.horse/blog/2026/11/disinformation-machine/#fnref:7)
8. i actually realized the other day that my server isn’t even doing the best gzip compression: `for i in {1..9}; do gzip –keep -f -$i index.html; echo -n $i:\ ; ls -sh -1 index.html.gz | grep -o ’^\S*’; done 1: 52K 2: 48K 3: 48K 4: 44K 5: 44K 6: 40K 7: 40K 8: 40K 9: 40K` so in theory i could shave even more bytes off my posts ^^ [↩︎](https://lyra.horse/blog/2026/11/disinformation-machine/#fnref:8)
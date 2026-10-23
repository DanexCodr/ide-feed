What an absolutely bananas week it’s been. You’ve got [the number 4](https://scotthelme.co.uk/eight-bits-of-trust-emudhras-ca-keys-cracked-in-milliseconds/) just running around wreaking havoc. Railway is still fielding an [everybody’s-worst-nightmare breach](https://blog.railway.com/p/security-disclosure-wednesday-october-21st). Zeabur is [shutting down](https://zeabur.com/blogs/zeabur-is-shutting-down) after [a major breach](https://zeabur.com/blogs/october-2026-security-incident). We were all reminded just how dang much of the internet [runs on PHP](https://www.wiz.io/blog/php2shell-php-rce). Oh, and also we saw serious vulns in [GitLab](https://docs.gitlab.com/releases/patches/patch-release-gitlab-19-5-1-released/) and [Node.js](https://nodejs.org/en/blog/vulnerability/october-2026-security-releases), supply chain attacks on [LiteLLM](https://docs.litellm.ai/blog/security-incident-oct-21-2026) and [OVH](https://github.com/ovh/ovhcloud-cli/security/advisories/GHSA-862f-55f5-vmvw), a key leak at [OpenCode](https://www.stepsecurity.io/blog/opencode-security-breach), and, and, and. There’s just *so much* happening that in addition to the trending security headlines, there are [several](https://www.cyberbreaches.org/en) [projects](https://pwn.watch/) dedicated to just keeping track of everything.

And then you move from the incidents themselves to the commentary saying things like *strap in, AI means this is just the tip of the iceberg* or *forget everything you know because we are in a new world now.*

It’s overwhelming, it’s destabilizing… it can be downright scary! How are we to deal with all of this?

When the shit is hitting the fan, it’s so important for us to lean into solidarity and make sure we’re taking care of each other.

For the folks in the thick of these incidents, it’s been an adrenaline-fueled scramble of a week. We at Miren know this life well - our team is made up of engineers and operators who have been in and around infrastructure companies for years. We have been on the late-night incident calls. We have typed the status page updates with shaky fingers. It’s difficult, often thankless work.

So this week we are beaming out [HugOps](https://en.wiktionary.org/wiki/HugOps) to the hundreds of people pouring their hearts and their sweat into firefighting, fixes, and follow-ups.

But when the dust has settled, we also have to talk about how we learn, how we improve, how we get stronger. You can think of this as an extension of our practice of care: how do we take care of our future selves, making it less likely we need to rely on last-minute heroics to save us?

## Making sense of the chaos

Let’s start with some grounding. Even on a week like this, in a year where so much is moving so fast, there are certain structural dynamics that still hold for software engineers: a piece of software has to operate in an environment, and it has to be built to account for risks in that environment while still accomplishing its goals.

We can sort the hot mess from our opening paragraph into a few shapes, which helps to get us thinking in structural terms:

**One vault, everybody’s secrets** - Railway, Zeabur, and OpenCode were all breaches of centralized platforms, where compromise of one entity yields access to a superset of user data. The structural problem here is concentration: with everybody’s secrets in one bucket, that bucket becomes a big target, and makes for an even bigger spill.

**One good patch, a million places to get it** - PHP, eMudhra, self-managed GitLab, and Node.js were all vulnerabilities discovered in non-centralized systems, so the exercise in fixing them was one of manual coordination. Here we see the structural problem of fragmentation, illustrated most starkly in the eMudhra vulnerability: Firefox had a [fast update channel](https://blog.mozilla.org/security/2026/10/20/protecting-firefox-users-following-the-compromise-of-emudhra-intermediate-certificates/) that blocked the bad certs within hours, while harder-to-update software will form a long tail of vulnerable surface likely to last an uncomfortably long time.

**One bad patch, a million targets** - LiteLLM and OVH were supply chain attacks, where the attackers were able to hijack an update system and get victims to compromise themselves. This is the inverse of the previous shape: an update channel becomes an attack vector when a bad guy gets ahold of it.

So yes, it’s a big bag of scary headlines, but we’re really talking about three problems of system design: where do secrets live, who applies fixes, and what does the fix channel trust?

These are problems that Miren, as a deployment platform, has to solve head-on.

## Picking the strongest shape

Miren is built on the belief that you shouldn’t have to choose between opaque platforms that cater to the enterprise and a stack of DIY complexity to get a great developer experience.

We want everybody to feel the joy of tooling that gets out of your way and lets you jam on a piece of software with your team and your users. But none of that matters if we don’t *also* provide a strong foundation that can carry your software through from prototype to production.

To that end, we’ve made some very intentional choices in our design space:

- We make it easy to run, so you can run it - Miren’s runtime is open source software that you can run on any Linux computer. That means your secrets stay on your machine under your control. (We can also host a cluster for you, if you want to trade some security for convenience.)
- A control plane that helps more than it can hurt - We’ve been careful to architect Miren Cloud in such a way that it makes things easier without unduly growing your risk. Miren Cloud never stores your secrets, and we designed the protocol between Miren clusters and Miren Cloud such that your app stays up and you can still deploy to it even if we take an outage. (You can also run an entirely disconnected cluster, if you want to trade some convenience for security.)
- Building in the open - Since all the software that runs on your computer is open source, it’s auditable. You can inspect how we run your software along with every one of your clusters’ interactions with Miren Cloud.
- Tunable self-upgrades - Miren Cloud can drive auto-updates for your clusters with a stable channel that has a one-week cooldown, on a maintenance schedule you choose, with automatic rollbacks on failures.

We think this is the strongest system shape to address the structural risks represented by these incidents: distributed control of user data, automatic patching, and a supply chain we can keep hardening.

## The risk that’s left

In this arrangement, the supply chain remains an irreducible source of risk. There are two inversely correlated variables: make a system easy to change so you can fix it, or make it hard to change so nobody can attack it. The modern security consensus seems to be that fast patches with defended channels are our best tradeoff.

But the special thing about open source, self-hostable software is that it allows you to choose a different set of tradeoffs by building the software yourself. This is obviously more work, but it lets you audit every line of code touching your machine.

There’s a lot more that we can do on the supply chain security side. One live scenario: Miren Cloud’s automatic upgrades are still opt-in because they take brief cluster downtime, so we want you to pick a maintenance window that works for you. Once we make it to zero-downtime cluster upgrades, flipping the default would mean that new clusters auto-update. So an active topic of discussion is: what kind of build integrity checks should we land before that happens?

We’re building Miren together with our community, so this is very much *not* a rhetorical question! Help us choose by telling us what’s important to you. [We’re always up for a chat.](https://miren.dev/discord)

So it’s not an incomprehensible mess: there are structures here that form an open design space with important tradeoffs to consider. There will always be room for multiple approaches - from hosted platforms to DIY stacks - but we believe that distributed data with centralized fixes is the right direction for modern software deployment.

If you’re picking up what we’re putting down, [give Miren a try](https://miren.dev/get-started) and do let us know what you think!
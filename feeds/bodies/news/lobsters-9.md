So, alright, look, here's the thing. Storyteller has a really long npm namespace because “storyteller” is a really common word, and so “@storyteller/” was already taken (by someone who doesn’t actually seem to use it, which, if you’re reading this, I’m still interested in your namespace!). So we’re stuck with “@storyteller-platform/”, and that means our command line tool for book forced alignment is named “@storyteller-platform/align”, and so you need to run “npx @storyteller-platform/align --help”, etc, which is a handful!

And so we came up with a cute nickname, “estee” (get it? Storyteller -> ST -> estee?), and we were pretty happy with it, so I went to publish a v0.0.1 to npm so I could set up Trusted Publishing with our GitLab repo and then *this* happened:

... What? Too similar to... “testem”? I mean I can almost understand “espree”. I don’t actually see how someone could accidentally typo “espree” as “estee”, but at least they're similarly shaped. But “testem”? No chance, that is *not* a typo candidate for “estee”.

I mean it’s pretty clear what’s happening here. Npm is using a Levenshtein distance calculation and banning any packages that have a Levenshtein distance of 2 or less from existing popular package names. Levenshtein distance counts the number of “edits” needed to get from one string to another, where an edit is a single character insertion, replacement, or deletion. So to get from “estee” to “testem”, we have to make the following edits:

See? Levenshtein distance of 2. We used this for the first several iterations of the Storyteller algorithm, which needs to find where a given sentence lives in a transcription of an audiobook.

Here’s the thing: Levenshtein doesn't scale down very well. You can’t just set a single threshold for all input lengths, because as the length of the string approaches the threshold, the proportion of the set of valid strings covered by the threshold explodes.

Here’s what I mean. Say you are concerned with all npm package names with length 4. Npm allows the characters a-z, plus the symbols “.”, “-”, and “_”, so there are 29 possible characters in our alphabet. For a 4-character string, that gives us 29<sup>4</sup> possible names, or 707,281 possible names.

But what happens if you don't allow any names that have a Levenshtein distance of 2 from any existing names? How many packages can exist before you have to start rejecting *all* new package names? This is a little hard to answer completely (and we’re ignoring the fact that, because Levenshtein distance allows pure insertions and deletions, this also affects 2-, 3-, 5-, and 6-character names), but we can set an upper bound: 29<sup>2</sup>, or 841.

This is because, since Levenshtein distance allows a *replace*  edit, you can get from a string like “abaa” to *any* string starting with “ab”. So once you have all 841 strings starting with every combination of the first two characters, that’s it, you’re done, no more names. That’s 0.12%<sup>[1](https://smoores.dev/post/no_npm_estee_is_not_a_typo/#fn1)</sup>  of the total name space actually available to choose from.

This is especially apparent when considering our backup name, “hoid” (get it? [Hoid](https://coppermind.net/wiki/Hoid)? World-hopping Storyteller?). Here are the popular packages that npm thinks “hoid” might be typosquatting on:

1. hoek
2. hono
3. uid
4. ulid
5. cuid
6. uuid
7. joi
8. gopd
9. poi
10. zod

Two things to notice about this list:

1. It’s much longer than the first list. This is because of the string-length — 4 is so close to 2 that you can reach way more usable words from a given length-4 string with a distance-2 Levenshtein threshold
2. None of these look like actual typo candidates for “hoid”. They’re all at least 50% different from “hoid”! “gopd”? “gopd”!?

Also, this just isn’t a very good rule. Seriously, this rule would have banned the project “preact” from being created because “react” already existed. It would have banned “estree” (which I assume only didn't trigger on my “estee” attempt because it’s not sufficiently “popular”) from being created because “espree” already existed. I could go on and on. *I understand* that npm is under a lot of pressure to try to prevent this flavor of typosquatting malware distribution, and I know that there probably needs to be some amount of automation involved here, but surely there should be some sort of manual override?

Actually that’s a good point. In fact, when I tried to first publish Storyteller’s “@storyteller-platform/audiobook” package, I ran afoul of npm’s *other* rule about new package names, which is that they can’t, I dunno, use the word “audiobook”?

Cool, thanks. I think what actually happened here is that people were publishing literal copyrighted audiobooks on npm. Anyway, I emailed npm support that time, and they immediately disabled the block for “audiobook” and allowed me to publish it. This was actually a wonderful customer support experience, so much so that when I ran into my issue above, the first thing I tried was to reach out to npm again.

Only, this time they weren’t so helpful (I’m sure they’re getting deluged with LLM-generated support requests, just like everyone else, and they were still perfectly pleasant):

> The error you received is a typosquat functionality that will prevent security vulnerabilities
>
> For more information on typosquat please refer to:
>
> [https://blog.npmjs.org/post/168978377570/new-package-moniker-rules](https://blog.npmjs.org/post/168978377570/new-package-moniker-rules)
>
> We are unable to get around the automated typosquat block.

Only, here’s the thing, that blog post doesn’t say what the support person says it does. Instead, it’s about how npm rejects any package names that are the same as existing package names  *except for punctuation*. That’s not what we’re experiencing at all!

Also, I suspect that *someone* at npm/GitHub *can* get around this typosquat block. Plenty of pre-existing packages break this rule — if someone created the package for me from a backend/admin interface that didn’t enforce the block, I could use it

And, look, we’re gonna be fine. We’ll probably spell the CLI name “estie”, which is less fun to type and I think slightly less cute, but ultimately the same, and manages to avoid tripping any similarity alarms. But I feel… saddened, somewhat, that it’s probably not possible to make a 1-, 2-, 3-, or 4-character npm package name anymore. Not because they’re all taken, but because of a clumsy rule, and even worse, one that’s ultimately probably necessary to prevent some cruel people from hurting others. Ugh.
On May 1st, 2020, [Project Gemini](https://geminiprotocol.net/) made the rounds for the first time via a [Hacker News discussion thread](https://news.ycombinator.com/item?id=23042424). I remember seeing the announcement back then, barely a month after the Covid 19 worldwide lockdown, and thinking it was a cool gimmick. But that was that.

However, I’ve recently been seeing a few `gemini://` links here and there as footers in hand-crafted blogs, and I nerd-snipped myself to export this blog as a Gemini capsule that you can find at [gemini://capsule.jmmv.dev/](gemini://capsule.jmmv.dev/). The process has been fun, and I actually quite like the extreme minimalism of the resulting site. So what else would you expect from me? I *had* to write about it—hence this post.

Today we’ll learn a little bit about what Gemini is, how I approached the blog export to its native gemtext format, and I’ll confess a couple of… sins I committed along the way.

A blog on operating systems, programming languages, testing, build systems, my own software
projects and even personal productivity. Specifics include FreeBSD, Linux, Rust, Bazel and
EndBASIC.

[![Follow @jmmv on Mastodon](https://jmmv.dev/images/badges/mastodon-logo.svg)](https://mastodon.online/@jmmv)[![Follow @jmmv on Twitter](https://jmmv.dev/images/badges/Twitter_logo_blue.svg)](https://twitter.com/intent/follow?original_referer=https%3A%2F%2Fjmmv.dev%2F&screen_name=jmmv)[![RSS feed](https://jmmv.dev/images/badges/feed-icon-28x28.png)](https://jmmv.dev/feed.xml)

# What is Gemini?

A terrible name, that is. Looking for information about Gemini these days is extremely hard, thanks to Google polluting the namespace with its own AI offering. Of course that’s not Project Gemini’s fault because Google’s thing came after them, but still, good luck finding stuff about this network.

Joking aside, let’s look at Project Gemini’s barebones front page:

… and break down the introductory and only paragraph:

> Gemini is a new internet technology supporting an electronic library of interconnected text documents.

You can think of Gemini as a way to access a bunch of text-only pages, with links among them, so you can find information and follow links to additional resources. Instead of using `http://` or `https://` URL prefixes, you use `gemini://` instead.

> That’s not a new idea, but it’s not old fashioned either.

Exactly. Gemini is like the [WWW](https://en.wikipedia.org/wiki/World_Wide_Web), or “the web” in more colloquial/modern parlance. In fact, Gemini is a parallel community to the web. Obviously, that’s not a new idea because the web dates back to 1989, and we are now 37 years after that.

The idea is not unique either because [Gopher](https://en.wikipedia.org/wiki/Gopher_(protocol)), a much lesser-known option, exists as well. Surprisingly to me, I realized that Gopher came *after* the web in 1991 while researching this article. I had always assumed Gopher was first and that the web came to replace it because of Gopher’s rigidness. But that’s not quite what happened.

> It’s timeless, and deserves tools which treat it as a first class concept, not a vestigial corner case.

Humans have [shared written documents](https://en.wikipedia.org/wiki/History_of_writing) since around 3400–3100 BCE (roughly 5,100–5,400 years ago) in ancient Mesopotamia and Egypt, and that’s probably (hopefully?) not going away. It’s true, though, that at this point, text sharing is not the primary thing that the web does, as you well know. We have morphed the web from a document distribution tool into an app platform, for better or worse.

A little confession: I worked at Google for 12 years, starting right at the time they published Google Wave (2009), which to me marked the start of truly interactive web apps—more so than Gmail (2004) did. In the back of my mind, I knew I was helping turn the web into how we run apps, destroying the traditional desktop paradigm—a feeling I never liked. And… it happened. Obviously, it’d have happened without me, a little pawn in the game, but it bothered me regardless.

> Gemini isn’t about innovation or disruption, it’s about providing some respite for those who feel the internet has been disrupted enough already.

(That comma splice hurts.) As we have established earlier, Gemini’s ideas are not new, so it’s indeed not innovative. And seeing how little people read these days, or even how unable to pay attention to long-form text they are, it’s not going to disrupt anything either. But respite is key: having a separate place where you know you’ll only find some sort of counter-culture sounds entertaining.

Fun fact: I wasn’t quite sure what respite meant and originally took it to be similar to spite. That meaning would have worked equally well here, if not better?

> We’re not out to change the world or destroy other technologies. We are out to build a lightweight online space where documents are just documents, in the interests of every reader’s privacy, attention and bandwidth.

Here is the interesting thing. Gemini claims that it has been designed to minimize the chances of becoming bloated, and I’m not exactly sure how you can prevent that. For example: articles can provide links to images, but images are not auto-loaded. OK, says who? The auto-loading part is something the client browser controls, and it’d be trivial to create a Gemini browser, or modify an existing one, to auto-load and render images. That’d go against the spirit of Gemini, but if enough people wanted it, it’d happen. Same story as the [browser wars](https://en.wikipedia.org/wiki/Browser_wars).

And that’s the key: “enough people”. As long as Gemini stays under the radar and only like-minded people gravitate towards it, these properties will be maintained. But if for any reason it becomes more mainstream… unwanted changes will happen.

# Gemtext

Gemtext is the native format of documents stored in the Gemini network, with a MIME type of `text/gemini` and a `.gmi` extension. Gemtext documents are typically grouped in *capsules*—which is just another name for “website”.

The format itself is like a super-diluted version of Markdown, supporting just these features:

- Three levels of headings.
- Paragraphs.
- Links as standalone lines, not as inline text.
- Preformatted text blocks, also not as inline text.
- Unordered lists.
- Blockquotes.

Workable for sure, but weak. In my opinion, Gemini missed the boat of creating a truly *semantical* web, but for that you need additional primitives to represent more concepts. In any case, you can read through [the long FAQ](https://geminiprotocol.net/docs/faq.gmi) to know that this was discussed and eventually ruled against, so know that a lot of thought was put into its design.

Yet another fun fact: just two days ago, I stumbled upon [“Good morning and welcome to my idea of a new web”](https://demo.bonbonweb.org/?url=https%3A%2F%2Fdave.writersweb.org%2Findex.md): the proposal of a “browser” that just renders Markdown documents. This feels quite similar to the idea behind Gemini, but using a better (not a great) format with more markup abilities. And I say fun fact because, as I was learning about Gemini, I was imagining developing this exact alternate idea.

One curious bit is that Gemtext is *also* the format for subscription feeds. Sure, you can offer an RSS feed for your capsule, but RSS is a monster spec that feels out of place in a minimalistic network like Gemini’s. So you can abuse Gemtext to create a feed by creating a page that’s primarily links with a de-facto `YYYY-MM-DD Title` format. Again, it’s simple, and it works.

The big benefit of Gemtext’s simplicity is that clients can also be super-simple. You can rest assured that all clients will be able to display the same content, consistently. So far I’ve tried [Elpher within Emacs](https://github.com/emacsmirror/elpher), [Lagrange on the desktop](https://gmi.skyjake.fi/lagrange/), and [Buran on my Android phone](https://f-droid.org/packages/corewala.gemini.buran/). All are simple. All display text in the same way.

I definitely do not recommend using the Gemtext format to persist your original content, but that doesn’t mean you have to *write* in Gemtext. Which brings us to Markdown again.

# Markdown to Gemtext

All of the content you are reading in this blog is authored and stored as Markdown documents. Like many other people who still maintain a blog in this day and age, I [started with a hosted platform](https://jmmv.dev/2024/06/20-years-of-blogging.html) (Blogger) and then experimented with Medium. But as soon as Medium became riddled with noise, I ran away. Unfortunately, escaping was difficult: the format that Medium spit out was frigging awful—almost as if it were designed to provide the illusion that you could export content, even if the content was nearly useless after the fact.

It was at that point that I committed to converting my golden copies to Markdown even though authoring in Markdown was more inconvenient. And believe me: it *is* inconvenient, *especially* when having to insert images. But now I own my content in a format that’ll survive for years to come.

Which brings us back to Gemtext. The thought that crossed my mind when I stumbled upon Project Gemini again three weeks ago and that triggered this whole thing was: can I write a script to convert my Markdown docs into a capsule? And with “I” I really mean AI, because this is the kind of experiment I was not going to code myself.

And of course I could. After just one simple prompt, I had a converted site that I could browse. Granted: the conversion Python script was literally awful, and the converted format was not great either, but having something I could play with inspired me to try harder.

So I threw everything away and started over, again with AI, to write a conversion tool for my blog (codenamed `gengems` for now) that takes the existing Hugo layout and spits out a capsule end-to-end in just 300 milliseconds while processing 1000 documents. The tool is obviously written in Rust, and by now supports enough configurable features that I’m increasingly tempted to throw Hugo away for the web version and create my own static site generator too. Because, you know, while Hugo works, it isn’t the greatest in usability and its recurrent incompatible changes are annoying. I’ll resist the urge to do that for now… I think.

# A brief vibecoding detour

Let’s dive a tiny bit into `gengems`. First of all, this second iteration is still entirely vibecoded. Oops, first sin. I have not looked at the code because it’s working for what I need it to do, it’s fast, and it’s not going to be used by anyone else… unless you want it, but then I’d probably rewrite it once more now that I know what the final feature set looks like.

Now, for this second iteration, I was so close to running out of my $20 weekly OpenAI quota that I pivoted from my favorite GPT 6.1 Sol model to GPT 6 Luna to see how far I could go. Luna is *so cheap* that you can do a ton with it, and I actually got `gengems` to work well enough within just a few iterations.

But oh dear. Luna is cheap, but it’s also kind of crap for coding. It stops half-way. It doesn’t think through enough corner cases. It doesn’t produce enough tests. The plans it produces are very vague. You have to be extremely prescriptive when asking it to do things and even that leads to mixed results. Out of curiosity, when my weekly cap was reset, I asked Sol to review what Luna did, and oh boy did it have things to say. From design problems to important missing tests, passing through outright bugs. I let it fix those issues, and I continued building with Sol.

Right now, I’m actually pretty happy with the results of `gengems`. I can configure the mapping of pages to templates in a much more explicit way than in Hugo. I can use MiniJinja for templating. I can specify cross-site links. I can handle inline links, figures, and even tables. I can generate archives/feeds for the site, for each year, for each month. I can process blog posts, and also standalone pages. All in all, the results are very satisfactory given the close-to-zero effort I put into it.

# Serving the capsule

With the site exported to Gemtext, I needed a server. There are a lot of options out there, but the one that piqued my interest was [Agate](https://github.com/mbrubeck/agate): a minimalistic Gemini server written, of course, in Rust. You run the binary pointing it at the directory containing the generated site and, voila, it works. Agate even takes care of auto-generating SSL certificates because all Gemini traffic is TLS-protected, and the fact that it’s automated is a relief because dealing with certificates is a pain.

But running Agate once, interactively, and making it serve in the background are different stories. I am running FreeBSD on my server and I could have used the prebuilt `agate` package, but then I encountered [a crashing bug](https://github.com/mbrubeck/agate/pull/475) and wanted to add a feature, so I had to pivot to building from source. And, as you can imagine, Cargo leaves a lot to be desired if you want to install the resulting product to a running system.

Now, of course you can copy the built binary to, say, `/usr/local/bin/agate`, but there is typically much more than a binary in a distribution: think about documents, examples and, for a server program in particular, startup scripts. Mind you, Agate’s source tree does include a FreeBSD rc.d script, but it was buggy, insufficient, and it also required manual copying. So I created [a PR to revamp the installation system](https://github.com/mbrubeck/agate/pull/472) based on [earlier experience](https://jmmv.dev/2025/12/from-azure-functions-to-freebsd.html) with setting up similar infrastructure in other Rust services I run.

# Analytics, oh no!

I mentioned briefly above that I wanted to add a feature to Agate and that it was the reason I had to build from source. And that feature is… analytics, which are the second sin right there.

> “Oh no, ah-nah-ly-tics! Privacy enemy number one! How *dare* you add analytics to something in the Gemini network!?!”

But wait a second. What *are* analytics? You do realize that Agate prints and saves a log of incoming connections (with IPs redacted by default), right? That’s par for the course for any Internet server out there, because in order to serve requests… well, the server actually needs to know what those requests are and where to send the responses to. So you can always analyze the log to gain some insights on traffic.

And that’s pretty much what I did. I just wired this exact same information to my own analytics service for visualization. The only thing I see are the pages that are being downloaded, when they are downloaded, and the originating country (computed from the requester’s IP after truncating the last octet to mask it). Essentially… good old page counters from the 1990s.

The way I implemented this is generic though: I extended Agate to add optional support for an SSI-style URL inclusion primitive and then added such a call to the capsule-wide footer template given to my Gemtext generator. As a high-level primitive, it can serve other purposes, like sourcing *comments* for each page by making the footer download a pre-rendered `.gmi` chunk. I haven’t implemented that yet in my comments service, but it should be pretty easy.

Sounds interesting? I *might* try to contribute this SSI feature upstream to Agate, but I predict that this collides with the goal of a lightweight server and that it’ll be rejected. But I’ll try anyway. I want to get the FreeBSD-related bug fixes and related improvements merged first, because those are helpful to everyone, I hope.

# Try it out

That’s about it! If you are in the U.S. you are about to have 4 days off, so spend that time falling into the Gemini rathole. And if you are elsewhere, do the same! It’s entertaining.

From now on, remember that you can *also* read this blog via [gemini://capsule.jmmv.dev/](gemini://capsule.jmmv.dev/) if you want a super-fast, distraction-free experience. To get started, visit the [Gemini software](https://geminiprotocol.net/software/) page for a long list of clients to choose from and install.
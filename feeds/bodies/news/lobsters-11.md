I'll be radically honest here - I never really got the idea of "Test Driven Development". I'm much more of a "telnet into production and damn the consequences" kind of guy. Look, it's much more fun and my cardiologist recommends severe shocks every now and again.

The essence of unit testing is pretty simple:

1. Feed a function some data
2. See how it responds

Send it good data and if it returns "true" the test passes. Send it bad data and make sure it returns false. Easy peasy lemon squeezy.

As part of my [NLnet funded work on ActivityBot](https://shkspr.mobi/blog/2026/08/activitybot-is-the-recipient-of-an-nlnet-grant/), I'm writing some proper tests for my bot framework. I am hopeful that some of them will be useful to other projects doing similar things.

There are four major classes of tests - here are the problems I've found while writing them.

A basic test might be how to validate that an ActivityPub username is valid. Typically it would be something like `@edent@mastodon.social` - what assumptions do we make with that? It starts with an `@` and has another `@` somewhere in it, dividing into two parts, the user and the server.  The server has to be a valid domain name - but that can include non-ASCII Internationalised Domain Names and Emoji domains.

What about the user part? Is it just A-Z and 0-9? Can it have dots? What about apostrophes like an email address?

Basically, how easy is it find the specifications for all the various component parts of ActivityPub? Not very!

What does a [WebFinger response](https://www.rfc-editor.org/info/rfc7033/) look like? Which parts are mandatory and what values can they contain?

With any message that your project generates, how can you be sure that other ActivityPub servers will understand it?

Similarly, when we receive a follow message from an external server, what should it look like?

There are some [JSON Schemas](https://github.com/steve-bate/fediverse-jsonschema) which can be used to validate some type of messages.

But, again, there are *many* scattered specifications.

As I've written about before, [HTTP Signatures are difficult](https://shkspr.mobi/blog/2026/09/a-reasonably-practical-guide-to-validating-rfc-9421-http-signatures-for-activitypub-in-php/). There are two main problems. The first is verifying signatures.

In order to do that, you need to gather a bunch of signatures and then find a way to replay them into the test. So I'm in the process of saving signatures which I can then share with others.

The second problem is *generating* signatures.  Sure, you can run tests on the signatures - but there's only one *real* way to test whether they're acceptable…

Passing tests means nothing if you can't communicate with others and they can't communicate with you.

Some tests are easier than others. Sending a signed request should be easy and repeatable. But receiving messages isn't easily automated. It requires being able to control an external server and asking that to send messages.

With the [Mastodon API](https://docs.joinmastodon.org/client/intro/) it is possible to make requests which will interact with your server - but only if it is a *public* server.

I'm putting [all my tests online](https://gitlab.com/edent/activity-bot/-/tree/main/tests?ref_type=heads). I'm also sharing a [collection of messages and signatures](https://gitlab.com/edent/activity-bot/-/tree/main/tests/headers?ref_type=heads) which you can use in your tests.

I'd love to know if you find them useful.

## 3 thoughts on “Some quick thoughts on Unit Testing ActivityPub”

1. ![](https://shkspr.mobi/blog/wp-content/uploads/webmention/avatars/bsky.app/f0efd35978092e16db6d49e9873e0d33.jpg?d=initials&name=gabboman+the+wafrn+dev) ![](https://shkspr.mobi/favicons/?domain=bsky.app) [gabboman the wafrn dev](https://bsky.app/profile/gabboman.xyz/post/3mxjhibd3oc2t) Sometimes the only logical thing I was able to make is just connect my dev laptop with a reverse proxy and a debugger [Reply](https://shkspr.mobi/blog/2026/10/some-thoughts-on-unit-testing-activitypub/?replytocom=479008#respond) | [Reply to original comment on bsky.app](https://bsky.app/profile/gabboman.xyz/post/3mxjhibd3oc2t) [2026-10-10 13:11](https://shkspr.mobi/blog/2026/10/some-thoughts-on-unit-testing-activitypub/#comment-479008)
2. ![](https://shkspr.mobi/blog/wp-content/uploads/webmention/avatars/social.chrisco.me/05726dc39aa49957c2a30e13b4ccc183.jpg?d=initials&name=michael) ![](https://shkspr.mobi/favicons/?domain=social.chrisco.me) [michael](https://social.chrisco.me/@michael/statuses/01M4M9VFG2BHNQ616AN34Y5JTK) [@Edent](https://mastodon.social/@Edent) Ive heard the term scaffold development locally. Its when you create the thing as small as possible and then create "good" tests around the thing you created. It works out if you dont get too crazy with it. I like having more selenium tests than unit tests myself because functionality can at least be checked out...but I recognize I dont make like medical devices or anything that might hurt someone if it doesnt work. They will just get annoyed at a red bod on the screen haha. [Reply](https://shkspr.mobi/blog/2026/10/some-thoughts-on-unit-testing-activitypub/?replytocom=479025#respond) | [Reply to original comment on social.chrisco.me](https://social.chrisco.me/@michael/statuses/01M4M9VFG2BHNQ616AN34Y5JTK) [2026-10-11 02:39](https://shkspr.mobi/blog/2026/10/some-thoughts-on-unit-testing-activitypub/#comment-479025)
3. ![](https://shkspr.mobi/blog/wp-content/uploads/webmention/avatars/m.mtlynch.io/b72f0662c618af93aec20981299576d8.jpg?d=initials&name=Michael+Lynch) ![](https://shkspr.mobi/favicons/?domain=m.mtlynch.io) [Michael Lynch](https://m.mtlynch.io/@michael/117428770754736085) [@Edent](https://mastodon.social/@Edent) Two suggestions. (1) Setting up GitLab CI (or any CI) makes the tests drastically more valuable because you (and contributors) know for sure that tests succeed. (2) Inlining the JSON files makes the tests easier to read. They're small enough that it's not much clutter, and tests are hard to understand when the reader has to jump back and forth between files. [Reply](https://shkspr.mobi/blog/2026/10/some-thoughts-on-unit-testing-activitypub/?replytocom=479158#respond) | [Reply to original comment on m.mtlynch.io](https://m.mtlynch.io/@michael/117428770754736085) [2026-10-12 17:00](https://shkspr.mobi/blog/2026/10/some-thoughts-on-unit-testing-activitypub/#comment-479158)
4. [More comments on Mastodon](https://mastodon.social/@Edent/117416401539960330).
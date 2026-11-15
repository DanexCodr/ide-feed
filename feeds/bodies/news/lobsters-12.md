Atproto Spaces are a new primitive in the atproto stack. We just launched the protocol [in alpha](https://atproto.com/blog/atproto-spaces-alpha). Check it out, give the blogpost a read, and sign up on the alpha PDS!

My own intuition around this protocol has been consistently evolving as I’ve worked on it. You can trace much of that through the [Permissioned Data Diary](https://dholms.leaflet.pub/3meluqcwky22a) series I wrote during the design process. Now with some time and perspective, I wanted to zoom back out, look at the design of Spaces and take a shot at succinctly motivating them as a new primitive.

### [Design Goals](https://dholms.leaflet.pub/3mu3p3ldwrc26#design-goals)

Our initial goal was to extend atproto to work for non-public data. Specifically though, we wanted to enable social use cases. Which is to say that the protocol isn’t intended for just bookmarks or even “gated posts”, but needs to work for large multi-user social contexts such as a 100k user forum.

Our next goal is to maintain existing atproto intuition. Users publish records, those records are canonically stored in the user’s PDS, authority rests in the author’s DID, and applications crawl PDSes and sync data to build their own views. Succeeding in this means that many difficult questions around things like moderation and credible exit are already answered!

An extension of that goal is that it must be atmospheric. I use “atmospheric” to refer to the same underlying data getting remixed across apps in different lights. Think: Bluesky posts showing up as comments under a standard.site blog or rpg.actor characters walking across the bottom of your streamplace stream. Atmospheric features are the features that make this network feel like one deeply integrated experience rather than a bunch of isolated apps that just happen to have the same login.

And finally, the protocol needs to be secure and legible to users. This protocol enables many-to-many sharing in a multi-app, multi-pds, multi-modality network. That’s a lot of variables! This all comes to a head in the OAuth consent screen. And being able to communicate what an app is allowed to do in a concrete way in just a couple sentences is absolutely critical to the Atmosphere being broadly approachable and usable.

### [✨ Spaces ✨](https://dholms.leaflet.pub/3mu3p3ldwrc26#spaces)

Spaces are our new primitive. Each space represents a shared social context. They’re a simple and concrete mechanism for organizing and permissioning data. Built around an abstraction of locality, each record is “in” a space and only one space. Each space is explicitly tied to a particular modality and owned by a single entity.

As we explored this new primitive, we realized that it seems uniquely able to thread the needle on all of our design goals.

Spaces are a deeply social primitive (fitting for a social networking protocol!). Spaces are not really about “who do I, as an individual, share this piece of content with”. Spaces are meant for establishing a shared social context. Records are in that context, and everyone with access to that context has the exact same view over it. It’s a shared common reality, and this shared sense of space allows for truly social applications.

We’ve started describing spaces as “mini atprotos” (btw if that sounds heavy duty, don’t worry spaces are actually very lightweight & low overhead). That analogy turns out to hold startlingly well. Not only does it help communicate the new primitive, but it also has the huge benefit that almost all of the really difficult questions of using the protocol for real-world social networks can be answered pretty simply: they’re the same as existing atproto! From moderation to account migration to the role of applications, intuition from public atproto maps very closely to spaces.

Spaces are quite legible. Of course this isn’t a gimme, the Atmosphere is pretty novel, and we’re all familiar with the new challenges of communicating this novel network to users. However, as I mentioned, this question of legibility comes to a head in the OAuth screen. In a context like that, describing “spaces” is much more grounded than trying to communicate ACLs or circles (as we’ll discuss in the next section).

One thing I didn’t expect when we started out designing spaces is how excited I would be for their applicability in public contexts as well. This realization partially underlies our shift in naming from “permissioned data protocol” to “atproto spaces”. This name shifts the focus from “who can see what” to locality. This new notion of locality is super handy and opens up all sorts of new options for data modeling. As a result of this locality, sync is also very lightweight and friendly. It felt so good to build my spaces [example app](https://bulletin.my/) and not have to comb through the entire global network. Locality in the sync protocol gave me exactly the data I needed.

To be upfront, the effect of designing spaces to be usable in multi-user social contexts is that they are less tailored towards permissioned publishing. Spaces are least tuned to the use case of publishing a bunch of individual pieces of content where each record has a different audience. If you realize that this seems like a weird approach to “I have a bunch of recipes and I want to share each with a totally different audience”, you’re not wrong! That use case was just not the primary design goal of atproto spaces.

That being said, I think spaces still work in that case. This deserves a blogpost & an example app of its own. However, a simple “out” for cases like this is to just put all your recipes in a space that you share with one or more applications and then let those applications manage the access logic.

In an effort to further bolster intuition around spaces, I also wanted to compare them to the most commonly-suggested alternate approach. I broadly refer to this approach as “Circles” (after Google+ Circles).

- Circles: the content is the object, audience is an attribute you attach to it. You write a post, then tag it with who can see it.
- Spaces: space is the object, content is published into it. A post goes "into" a space and is viewable by anyone with access to the space.

Circles come in many forms. The simplest is just “putting ACLs on records”. Once you start enabling large multi-user social use cases like forums, you realize you need to share the same ACL across many records owned by many users. Now you have a circle!

In their fullest forum, circles can be created by anyone, re-used by anyone, and apply to any data. For example, my friend can create the circle “Besties” and I can share recipes, blogposts, and videos with that circle.

However, softer versions of circles include arguments that records should be able to be in more than one space. Once you change this invariant, a record is no longer “in” a space. The record “exists” (outside of any given space), and then each space is attached as metadata, giving the record visibility in that space. We’re back to circles!

Circles seem simple at first pass, and they’re are many folks’ first instinct for social permissioning (including mine!). However they hide a lot of complexity. For one, there’s a lot of cognitive overhead, juggling who’s in which circle and which content is shared with whom. And thinking through the repercussions of sharing a post with multiple circles is difficult to understand. For instance, if I share with my “Family” and my “Besties” circles, are they able to see each other’s comments and likes?

All of this complexity gets dramatically exacerbated in the multi-app, multi-pds, multi-modality network that I described earlier.

I have a claim, which I’ll (cheekily) call Daniel’s Circles Postulate:

> It is only possible to safely and legibly share a record with two different circles if those circles were created by the same entity and are for the same modality.

To quickly get the intuition behind this claim, consider that “Besties” circle from before (different account & different modality). If I upload a video with my video app and share it with Besties, my friend (who created the circle) can use his recipe app to change the access perimeter on my video. Not only does this violate all rules and intuition about resource ownership, but even if it is actually what you intend to do, I have no earthly idea how you would make those side-effects legible to either of the users involved or go about communicating that capability in the recipe app’s OAuth screen.

In short, the Atmosphere is a very dynamic network, there are a lot of variables at play. In this flux, I believe we benefit by having a deeply social, grounded, and concrete primitive that orders our interaction model. I don’t believe that any variation on circles (ACLs, the full fluid expression, or just allowing records to surface in multiple spaces) gives that to us.

But I think we found it in spaces.

So please give it a go! Check out the recent [blogpost](https://atproto.com/blog/atproto-spaces-alpha) for directions on how to get started with the alpha, or just head over to the [new BPS site](https://bsky.network/account) to get your invite code for the alpha PDS.

Please let me know your thoughts! Share what you build. Let me know what works, and let me know what doesn’t. What’s confusing, what’s a pain to do, what breaks.

I can’t express enough how much I appreciate all the feedback along the way, so please keep it coming. I really believe this protocol is going to be critical for the Atmosphere, so we need to make sure it’s something we’re all excited about building on.
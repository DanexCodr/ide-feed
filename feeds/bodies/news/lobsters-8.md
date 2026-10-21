> Like the Trojan Horse, passkeys are legitimately elegant on the surface, but there is something troubling inside.
>
> What’s important to know is that unlike with any other kind of login credential, **you do not have ultimate control over your passkeys**. With passwords, you can choose where to write them down; with authenticator apps, you can decide for yourself which ones to use (they’re pretty interchangeable); and with physical security keys you can hand them to your colleague if you really trust them. But with passkeys come a hidden dial that lets the websites you use them on gradually remove your ability to do as you please with them.
>
> […]
>
> This is the feature that means you no longer get to make the calls about your passkeys. Fortunately, attested passkeys are not yet required on most websites. But the FIDO Alliance standard makes attestation a part of the passkey ecosystem, whether you want it or not. And even if the website doesn’t require attestation now, simply by using passkeys you indicate to the website that your setup supports the FIDO Alliance’s passkey standard and that you as a user *are capable* of using passkeys. This means that once Twitter (formally X) is satisfied that the overwhelming majority of its users would be unaffected, they can flip the switch – perhaps not all at once, perhaps just for ten thousand users at a time so as not to cause a fuss – and start rejecting non-attested passkeys.
>
> […]
>
> My expectation is that the industry will start off with very few constraints on your passkeys, and gradually add more and more, not all at the same time, but staggered on different sites, and then in a few years people will forget that they were ever offered a choice in which security measures they want to enable on their passkeys (if they even knew there were different kinds of passkeys at all).
>
> […]
>
> Remote attestation can allow them to verify that your device is not capable of, say, sending and receiving encrypted messages, or running a competitor’s app, or using social media without verifying your ID.

Apple’s passkey implementation currently [does not support attestation](https://news.ycombinator.com/item?id=50054170), but it sounds like this is [only until](https://developer.apple.com/forums/thread/708982) they can work out how to do syncing:

> Attestation was designed to attest to a specific device, exclusively at the point of creation, with a specific set of security properties. It doesn’t make sense for synced credentials for a number of reasons, including syncing to devices with different security properties, changes in security properties that happen after key creation, security properties of the sync fabric, sharing the passkey, or exporting to other passkey providers. We’re working hard with W3C and FIDO to solve these problems.

[Ricky Mondello](https://hachyderm.io/@rmondello/117428258722253709):

> The post is predicated on the idea that a feature of WebAuthn called “attestation”, which is only used in high-assurance and usually corporate scenarios, and usually with physical hardware security keys, will be leveraged to hurt people, somehow.
>
> The post posits that a website like X will bait and switch users: first, you get a passkey. Then, later, scary “attested” passkeys! This simply isn’t possible to do because attestation isn’t supported on the web for mass market, consumer authentication.
>
> Attestation for passkeys (software-based, syncable credentials) is antithetical to their mass market goals, and would freeze out independent, non-corporate-backed credential managers. It’s an explicit non-goal of the designers of passkeys, who work together in a forum anyone can join.
>
> And trust me, websites and apps like banks repeatedly asked for attestation at the beginning of the industry’s passkey journey. The platforms, browsers, and credential management apps have held firm that the goal of passkeys is reducing phishing and *not* some kind of trusted computing scheme. (And I will note: over my dead body!)

I believe this is not the goal of Mondello and some of the others working on this, but so far I’ve not been convinced that they will be able to control it. It sounds like Apple *is* working on it, and once the technology is out there, what’s to prevent key sites from forcing it on users? It seems like all this would take is the cooperation of a few big credential managers. This would be to their benefit in the sense that it would make their products required. Smaller credential managers who resisted would be frozen out.

[varx](https://cybersecurity.theater/@varx/117428884584457992):

> The fact that websites and apps have been *asking for attestation* just reinforces the main point of the passkeys post! Sure, browsers aren’t supporting it yet, but that’s the sort of thing that can change, and the sort of thing that *has* changed in the past. See the footnote on Widevine and Firefox. (“Currently not supported” is also very subject to change.)
>
> And we already have sites and apps allowlisting passkey vendors. That’s no theoretical, slippery slope fear -- it’s a real restriction on user freedoms that’s already happening right now.
>
> I don’t think that a couple of bad points (e.g. the TOTP thing) invalidate the main point of the post, because the post wasn’t an argument from authority. The author makes some good points that stand on their own.

[Ricky Mondello](https://hachyderm.io/@rmondello/117429023948255717):

> To be clear, the websites have stopped asking for attestation. Or at least, they’ve stopped asking me. Why? Because they know there’s no use in asking — that the OS vendors, browsers, and passkey managers are unified on this front. And now they’ve seen firsthand that passkeys without attestation are awesome and a big step forward.

> This is antithetical to users, as the types of authenticators that can pull this off are difficult to use (security keys). Companies with IT departments who can do account recovery for the user can handle this, an average user cannot. Synced passkeys are the answer to this for consumers and therefore attestation does not belong in the consumer space. Which is why password managers are in the spec groups pushing back against this every time it comes up.

> If a consumer website decided tomorrow that it would only accept attested passkeys, it would lock out almost all of its own users, instantly. What website is going to do that?
>
> […]
>
> If you’re worried about attestation creeping into consumer logins, then that’s worth pushing back on, loudly (if it ever happens). But it hasn’t happened, the biggest providers don’t support it, and avoiding passkeys today while you wait for it won’t protect you from anything, it just leaves you open to phishing.

It seems like rejecting passkeys is the only way the average user has to push back. The main thing protecting us is that sites don’t want to lock out their users who rely on passwords and 2FA. Once most people have adopted passkeys, if Apple and Google sell us out, I don’t think it matters much what the rest of the alliance thinks. Sites would be able to require attestation with the assurance that users could easily comply. Safari would probably opt everyone into attested passkeys, as it currently opts you into passkeys in general (unless you uncheck “Allow Automatic Passkey Upgrades”).

Previously:

For all of the protestations to the contrary, about how passkeys are so great for preventing phishing and increasing password security they do seem to be a real trap that gives more power to corporations we have no control over and whose goals have been clearly shown not to align with users. Google is already using attestation to attack third party app stores and non-Google Android, I have zero confidence they would not do the same for passkeys.

Generally I think the passkey supporters are well meaning but naive when it comes to their belief that corporations wont try and use them as another means of exerting control over their customers. Just look at App Store and CTF/CTC in the EU, I strongly doubt Apple will remain on the side of the angels forever.

It’s kind of astounding that anyone who has paid even the slightest bit of attention over the past few decades (centuries? millennia?) would think that powerful institutions won’t take advantage of the ability to control and extract power from others when given even half a chance.  

If it is possible for them to gradually tighten the screws and extract more power and money, they will.

I don't use passkeys for this exact reason. Every single time there's a way to increase lock-in or interfere with open standards, these companies do it. It's not an *if* they do this, it's a *when* they do this. But only if we let passkeys get too popular

I guess I'm a useful idiot in that I take advantage of passkeys when available, but I store them in a KeePass database and KeePass is clearly on the side of the user. Of course I'll be against the wall when attestation means I can't do that anymore, at which point I (and BitWarden users too, presumably) will suddenly wake up and notice I've been boiled.

Something to think about …

Ricky Mondello writing their own reputational epitaph there.

"Ricky, thanks for joining us. We've decided to make Passkeys into handcuffs"  

"Passkeys will become handcuffs over my dead body!"  

*bang*  

"ok, so next on the agenda"

As for why vendors have stopped asking Ricky to make passkeys into handcuffs... the obvious explanation is they're speaking to someone higher in the org.

I'm sorry, but all the anti passkey backlash is just conspiracy theories for technical people. Of course there are many things that *could* happen. A service could simply stop providing a website and require all access via apps, where they could do anything attestation does and more. But that doesn't mean it's going to happen.

@Alex R

We have seen over and over again how giving big companies the power to control something almost always leads them to trying to do so. For a long time Google androids attestation was also just a conspiracy and yet today Google is doing more and more to control android and prevent apps from working without Google’s approval. Any system where the specification allows for centralization of power is at risk and given the way the big companies who are pushing this have behaved in the last ten years it is quite clear they would like nothing better than yet another method to control us. Apple hasn’t released  a new open platform since Mac OS X cheetah back in 2000… that’s 26 years of closing down competition and locking things down.

@Alex R  

Follow up. The conspiracy could have been avoided if they had made the spec explicit about interoperability, standardization, and exclusion of centralized attestation. They didn’t do any of that.

"Of course there are many things that *could* happen."

Experience shows that if companies *can* do something to lock people into their ecosystems and extract more money, they *will*. The only variable is how long it takes.

That's not a conspiracy theory. That's observable reality.

Over started experimenting with account free apps, and I find it surprising how nice it feels when things like "your two lists of books, plus your favorite podcasts and all the settings you've done in the app" are expected and imported via a rather tiny file.

And it saves me all the hassle of managing a user database.

Depressing prospect. The only way out is user-friendly regulation. Let's hope our elected representatives don't screw us over.

Another way out is to not support this. To build apps that aren't in the hands of a handful of SV companies run by craven old men. Up your things and leave. Make Enhsittification Resistant Software

> Up your things and leave

Some people are seriously addicted to these platforms. For example, Gruber has now written multiple posts justifying his Twitter use, which clearly goes against his very public political opinions.

Just telling people to leave these platforms doesn't work. The underlying problem is a lack of antitrust regulation, which lets a small number of tech companies dictate these decisions to everyone else.

Plume: Gruber also recently wrote about how Apple contributed $25 million to the Trump ballroom and won't vote for any democratic candidate who won't promise to bulldoze it, but still buys all his computers from that same company that presented Trump with a gold trophy in the Oval Office.

We are all a mess of contradictions.  Every tech product is one point in the infinitely-dimensioned potential product space.  Every large organization is a complex mess of decisions and ideologies and relationships.  Adam Smith and James Madison are long dead, and it's no longer possible to use our dollar or our vote to express precisely what we want.

> Just telling people to leave these platforms doesn't work. The underlying problem is a lack of antitrust regulation, which lets a small number of tech companies dictate these decisions to everyone else.

I 100% agree. But we as developers can start looking for alternate ways of doing things. Just as people are putting free time towards becoming Microsoft MVP they can experiment with foss solutions, interoperability etc.

We can chip in. We're not helpless. But absolutely stronger consumer protections and antitrust laws. Those are the ones that really will create change.

>Safari would probably opt everyone into attested passkeys, as it currently opts you into passkeys in general (unless you uncheck “Allow Automatic Passkey Upgrades”).

Good reminder, thanks. Seems I have to opt out on each device, which may explain why some site (Google?) had decided "for me" (how nice) that I "want" to use a passkey.

I get the benefits of passkeys (including, for example, making phishing much harder), but they feel like a loss of user control+autonomy to me. I can scribble a password on a piece of paper. I _shouldn't_, but I can. I cannot meaningfully look at a passkey much less transport it without some intransparent API. It feels like a bridge too far.
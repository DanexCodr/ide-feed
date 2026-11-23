When you visit a secure website today, your browser connects to port 443 and immediately starts speaking TLS. Only once the encryption is up and running does it get around to speaking HTTP. That’s two protocols stacked on top of each other, and the one at the bottom doesn’t know or care about anything the one on top has learned over the decades.

This is why so many good ideas from HTTP had to be reinvented, years later, inside TLS. The most notorious is SNI, which is a `Host` header with extra steps.

It didn’t have to be this way. Let’s take a trip into a parallel universe where Netscape didn’t take the easy way out.

## 🕰️ The Fork in the Road

When Netscape released SSL in 1995, it came with a new URL scheme (`https://`) and a new port number (443). Plenty of people grumbled. The web already had a protocol and a port, so why invent new ones? Why not secure the conversation you’re already having?

To be fair to Netscape, in 1995 there wasn’t really a “proper” way to do that. HTTP/1.0 had no mechanism for handing a connection over to another protocol. The `Upgrade` header didn’t arrive until HTTP/1.1 in 1997, and the `Host` header, which made it possible to run many websites on one IP address, came with it. Netscape couldn’t have used either of them because neither existed yet.

But this is my parallel universe, so let’s say HTTP grew those headers a couple of years early and Netscape decided to wait for them.

## 🌐 Hello, Parallel Universe

In our universe, a TLS connection begins with a `ClientHello` and the server replies with its certificate. In the parallel universe, that first exchange is just plain HTTP in the clear.

The browser wants to buy something from `shop.example.com`. It connects to port 80, the same as always, and asks for the server’s certificate.

```
GET /.well-known/tls-cert HTTP/1.1
Host: shop.example.com
Accept: application/pkix-cert
```

(Yes, `/.well-known/` is from 2010. It’s a parallel universe. Let me have this one.)

The server responds with its certificate, and the certificates of any intermediate CAs, as an ordinary HTTP response. The browser checks the chain against its list of root CAs, exactly as it would in our universe. Is it signed by someone we trust? Is it for `shop.example.com`? Has it expired?

If you’re worried about sending the certificate in the clear, don’t be. Every version of SSL and TLS up to 1.2 sent the certificate unencrypted too. A certificate is public by design. An attacker can swap it for a different one, but they can’t make one that’s valid for `shop.example.com` without a CA’s help, and if they can get one of those, you have bigger problems.

Once the browser is happy, it knows the server’s public key. It invents a random secret, encrypts it with that key and asks to upgrade.

```
GET /checkout HTTP/1.1
Host: shop.example.com
Connection: Upgrade
Upgrade: TLS/1.0
TLS-Key: (the random secret, encrypted with the server's public key, in base-64)
```

Only the real server, holding the private key, can decrypt that secret. It replies with a random value of its own and switches protocols.

```
HTTP/1.1 101 Switching Protocols
Connection: Upgrade
Upgrade: TLS/1.0
TLS-Nonce: (the server's random value, in base-64)
```

Both sides now derive their encryption keys from the browser’s secret, the server’s random value and a hash of everything that was said in the clear up to this point. Mixing in that hash means that if anyone tampered with the plaintext part, the two sides end up with different keys and the connection fails. From this point on everything on the connection is encrypted, starting with the response to `GET /checkout`.

I’m describing the 1995 approach, where the browser encrypted a secret with the server’s RSA key. When Diffie-Hellman key exchange came along, it would have been just a different pair of headers: the browser sends its half of the exchange, and the server replies with its half, signed by the key in its certificate. Changing how keys are exchanged becomes header negotiation, which HTTP is already very good at.

Or, to put it another way:

> **Browser:** Hello, `shop.example.com`. Who are you?  
> **Server:** Here’s my certificate.  
> **Browser:** That checks out. Here’s a secret only you can read. Shall we go somewhere private?  
> **Server:** 101.  
> **Eavesdropper:** Aw.

## 🏠 Virtual Hosting From Day One

The first thing we get for free is the one that took our universe the longest to sort out.

That very first request for the certificate has a `Host` header. A server hosting a thousand websites on one IP address knows exactly which certificate to send back, because the browser told it, using a header the server already understands. There’s nothing to retrofit.

In our universe, the server had to pick a certificate before it knew which website you wanted. For years, every secure website needed its own IP address, which was one of the reasons HTTPS stayed expensive and rare for so long. The fix was SNI, standardized in 2003: an extension that lets the browser mention the website’s name at the very start of the TLS handshake. In other words, a `Host` header, reinvented inside TLS. The parallel universe never needs it.

And it’s all on one port. Firewalls, proxies and load balancers deal with port 80 and nothing else. A URL is a URL.

## 📦 A Smaller Black Box

So if SNI was standardized in 2003, why couldn’t a website rely on it until the mid-2010s? This is the part I find most interesting.

In our universe, TLS is a black box. Your application hands a socket to a TLS library, and the library takes care of everything: negotiating versions, swapping certificates, exchanging keys and the encryption itself. The box comes with a large “do not touch” sign, which is good advice. People who write their own cryptography tend to get it wrong.

The trouble is that a black box that does *everything* can only be improved by whoever owns it. Browsers couldn’t use SNI until their TLS library supported it, and on many platforms that library was part of the operating system. Internet Explorer on Windows XP never got SNI at all. A website couldn’t rely on SNI until XP was finally gone.

In the parallel universe, the black box is much smaller. Finding the certificate, checking it and exchanging keys all happen in HTTP, in code that browsers and web servers already update all the time. What’s left inside the box is the genuinely hard part: given these keys, encrypt and authenticate everything that follows. That still deserves a “do not touch” sign, but it’s a box that rarely needs touching. The bits people keep wanting to change live outside it.

## 🏛️ Room for New CAs

The parallel universe’s first request can do another job, too: it makes life much easier for new certificate authorities.

In our universe, a server sends one certificate chain to everyone, before it knows anything about who’s asking. In practice, that means a server operator can only use a CA that every browser on Earth already trusts. Nobody will pick a CA with less than 100% support, however good it is, so a new CA can’t get started. Even Let’s Encrypt, which had about the most compelling offer imaginable (free certificates, issued automatically), had to launch with a cross-signature from IdenTrust, an established CA, so that older browsers would accept its certificates. When that old IdenTrust root expired in 2021, devices that had never learned to trust Let’s Encrypt directly started failing.

In the parallel universe, the browser simply says which CAs it trusts, in the request:

```
GET /.well-known/tls-cert HTTP/1.1
Host: shop.example.com
Accept: application/pkix-cert
Accept-CA: (a list of the root CAs this browser trusts)
```

The server can hold certificates from several CAs and pick one the browser will accept. That’s content negotiation, which HTTP has done since the beginning. A new CA can start out with only the newest browsers, and sites can use it alongside their old CA until everyone catches up.

It’s worth noting that a list of trusted CAs, sent in the clear, is one more thing a website could use to fingerprint its visitors. I’d be surprised if it told them much, though. For most people, the list would be whatever came with their browser and operating system, which the `User-Agent` header already gives away. The exception would be anyone whose employer has added its own root CA to their machine, whose list would announce exactly where they work.

Early implementations in the parallel universe might simply have sent the entire list. As trust stores grew, browsers would probably have evolved more efficient ways to express the same information: compact identifiers, Bloom-filter-style summaries, or a two-stage negotiation where the browser sends a reduced list and the server replies, “I don’t have certificates for any of those authorities, but I do have these.” HTTP has had a status code for exactly that answer since the 1990s: `300 Multiple Choices`. At that point the browser can make a second request with a CA it knows is acceptable to both sides.

Our universe is, once again, getting there slowly. TLS 1.3 has an extension that lets a browser list the CAs it trusts, but no browser sends it, partly because a full list is so large. There’s now a proposal called Trust Anchor Identifiers that would let browsers say the same thing in a compact form, so that servers can pick the right certificate. It’s still a draft. And just like SNI, it will only be usable once the TLS library in every browser, operating system and server has caught up.

## 🤝 SSH Joins the Party

There’s another secure protocol that was born in 1995: SSH. Look at how it works and it’s already halfway into the parallel universe. An SSH connection opens with both sides exchanging version strings and lists of supported algorithms *in the clear*, then exchanging keys, and only then switching over to encrypted packets.

So in the parallel universe, someone at the standards meeting would notice that the TLS people and the SSH people are building the same thing. Both have a handshake that ends with “here are our keys”. Both then need the same thing after that: chop the data into records, number them, encrypt them, authenticate them, and notice if anything is replayed, reordered or dropped. Why have two committees writing two versions of the hardest part?

I think the two groups would merge and settle on a common core. TLS would keep its handshake, with certificates and CAs and an HTTP `Upgrade`. SSH would keep its own, with host keys you’re asked to trust the first time you connect. Each would finish by handing a set of keys to the same small, heavily-reviewed piece of code. Every improvement to that core, whether a faster cipher or a fix for a subtle attack, would land in both protocols at once.

Remember the small black box from earlier? This is where it ends up. HTTP owns the TLS handshake. SSH owns its own. That doesn’t make the handshake easy. Checking a certificate chain is still code where one wrong line can undo everything, as Apple found in 2014 when a single duplicated line skipped the signature check in its TLS handshake. But the handshake lives alongside the rest of the protocol, where it can be reviewed and updated by the same people, on the same schedule. Something like SNI ships with the next browser update, not the next operating system.

The real “do not touch” sign hangs on the shared core that both protocols hand their keys to. It would still be free software, in the GNU sense: anyone can read it, study it, fork it and change it. But the official version would be maintained by cryptographers, and getting a change accepted into it would mean convincing them. Instead of every secure protocol carrying its own big black box, there’s one small one, with the strictest gatekeepers, and everyone uses it.

This isn’t as far-fetched as it sounds. QUIC, the protocol underneath HTTP/3, already works this way. It borrows the TLS 1.3 handshake and nothing else: once the handshake produces keys, they are handed to QUIC’s own packet encryption, and TLS’s record layer is never used. The handshake and the core have already come apart. Our universe just took until 2021 to do it.

There’s a warning in our universe too. In 2023, an attack called Terrapin showed that an attacker could quietly delete messages from the start of the encrypted part of an SSH connection. It worked by slipping extra messages into the plaintext handshake, which threw off the message numbering the encryption relied on, without either side noticing. The handover from “talking in the clear” to “talking securely” is exactly where the parallel universe would need to be most careful. It’s also exactly the sort of thing you’d want one shared core and one set of eyes on, rather than two.

## 🐚 Shells Over the Web

Once the two protocols share a core, the wall between them starts to look a bit thin. In a universe where every secure connection already starts with an HTTP `Upgrade`, it’s a short step to one more. Sooner or later, someone would modify OpenSSH to accept a shell over HTTP.

```
GET /shell HTTP/1.1
Host: build-server-7.example.com
Connection: Upgrade
Upgrade: ssh
```

That request is sent after the connection has already been upgraded to TLS, so it’s encrypted, and the server knows exactly who’s asking, because the browser (or the SSH client) presented a certificate during the handshake. The server replies `101 Switching Protocols`, and what follows is SSH, with its channels, port forwarding and all. TLS has already done the encryption and checked both sides’ identities, so SSH can skip its own key exchange and get straight to the shell. In our universe, WebSocket had to be invented to tunnel things through HTTP. The parallel universe just asks.

I think most people would move over to it. You’d get the whole CA-backed infrastructure for free: no more “the authenticity of this host can’t be established” and typing “yes” without reading it. Users would log in with client certificates issued by their organization, which can be revoked centrally when someone leaves, instead of hunting down their public key in every `authorized_keys` file on every server. It would get through firewalls and proxies that block port 22, and the same `Host` header that lets one web server host a thousand websites would let one gateway front a thousand servers.

Port 22 would still have its fans. Plain SSH doesn’t depend on a CA, so nobody else’s mistake can let an attacker pretend to be your server, and nothing breaks because a certificate expired over the weekend. I expect it would live on in the corner of the server room, run by people who know exactly why they want it.

Our universe has been edging in this direction for a while. Browser-based terminals that tunnel a shell over a WebSocket are now a standard feature of cloud consoles. Large companies such as Meta and Netflix run their own SSH certificate authorities, so that engineers get short-lived certificates instead of permanent keys. And in 2023 a research project called SSH3 rebuilt SSH on top of HTTP/3, so servers can identify themselves with the same kind of certificate a website uses, and you can log in with your organization’s single sign-on. Our universe is getting there. It’s just doing it the long way round.

## 🔓 What Could Possibly Go Wrong?

I’d be a poor advocate if I didn’t look at the downsides, and there’s one big one: stripping.

Credit where it’s due: having `https://` as a separate URL scheme does give our real universe something genuinely useful. It’s an explicit sign that security is expected, and that the browser shouldn’t proceed without it. When you click on an `https://` link, the author of that page is telling your browser “this must be encrypted, and if it isn’t, stop”.

The parallel universe gives that up. Its security is *opportunistic*: the browser asks whether the server can do encryption and uses it if so. That’s great, right up until someone hides the opportunity before the handshake completes. The negotiation happens in the clear, so an attacker sitting in the middle doesn’t need to break the encryption. They just stop it from ever starting. Anyone who has set up STARTTLS for email will recognize this one.

So what’s a browser to do? You connect to your bank’s website, ask for `/.well-known/tls-cert`, and get back “404 Not Found”. Maybe the bank really has forgotten to set up its certificate. Maybe someone in the coffee shop is lying to you. The browser can’t tell the difference. Does it keep going without security?

In fairness, our universe has the same problem. When you type `bank.example` into your browser, it has traditionally tried plain HTTP on port 80 first. The bank’s server replies with a redirect to `https://`, and an attacker can simply hide that redirect and keep you on the insecure version. A tool called sslstrip demonstrated exactly that in 2009. Our universe’s answer, for many years, was to train users to look for the padlock.

The parallel universe would end up in much the same place. The padlock would survive as the sign that security was correctly established, and users would be trained to look for it just as ours were. (Our universe has since turned the padlock inside out. Chrome retired it in 2023, but plain HTTP pages have carried a big “Not Secure” warning since 2018. These days the sign that a connection is secure is that the warning *isn’t* there.)

Sooner or later, something like HSTS would be introduced, a header the server sends to say “from now on, never talk to me without encryption”. In our universe, HSTS arrived in 2012. In the parallel universe, with no `s` in the URL to fall back on, I suspect it would have been needed much sooner.

## 🛡️ Secure or Stop

Here’s a twist. The parallel universe might end up inventing `https://` anyway, but with a different meaning. It wouldn’t mean “use a different protocol on a different port”. It would mean “do HTTP on port 80 as normal, but this time, stop if security can’t be negotiated”. A link author could once again promise that a page must be encrypted, and the bank’s 404 becomes an error page instead of a shrug.

Our universe has even written the mirror image of this down. RFC 8164 (2017) describes “opportunistic security” for plain `http://` URLs, where a browser can quietly use TLS if the server offers it, while `https://` keeps its meaning of “secure or nothing”. Both universes end up with `https://` making the same promise. They just got there from opposite ends.

There’s an old argument that the parallel universe would replay, from the other side.

Before Let’s Encrypt arrived in 2015 and made certificates free, a few people ran their servers with self-signed certificates, vouched for by nobody but themselves. Browsers greeted those servers with big scary here-be-dragons warnings. The people running them hated this, and they had a point: a website with no security at all got no warning at all. The browser was treating “encrypted, but I can’t tell who by” as worse than “not encrypted”.

In the parallel universe, the same struggle would happen in a different way. Connect to a site for the first time, with no `https://` in the link and no HSTS history, and the opportunistic security kicks in. If the certificate checks out, you get the padlock. If it doesn’t, there’s no padlock, but there’s no need for a warning either. An unknown certificate is much the same as no security at all, and the browser treats it that way.

Going to the effort of TLS without verifying the certificate sounds a bit pointless, but it isn’t entirely. It won’t stop an attacker who can sit in the middle and hand you a certificate of their own. It does stop anyone who can only listen, which is the cheaper and far more common kind of snooping. The IETF came round to this view in 2014, declaring that pervasive monitoring is an attack (RFC 7258) and describing opportunistic encryption as “some protection most of the time” (RFC 7435).

And if you know the magic spell to get into the experts-only configuration, you’ve got the basis for SSH-style security. Tell your browser to remember that certificate, and complain loudly if it ever changes. The first connection is a leap of faith, and every connection after that is checked against it. Our universe’s browsers half-did this already: Firefox had a “Permanently store this exception” checkbox, buried behind enough scary warnings that only the determined ever found it.

Is that a good thing? Depends how you feel about SSH.

## 🔁 Meanwhile, Back in Our Universe

Here’s the funny thing. Our universe keeps quietly doing it the HTTP way anyway.

- The RFC exists. RFC 2817, “Upgrading to TLS Within HTTP/1.1”, was published in 2000. It describes Upgrade: TLS/1.0 on an ordinary port-80 connection, much like this post. Browsers never implemented it.
- So did a rival. S-HTTP, designed in 1994, secured individual HTTP messages inside HTTP itself. It lost out to SSL.
- Even the inventor of the web made the case. In 2015, Tim Berners-Lee wrote a personal note arguing against moving the web’s links from http: to https:. Every https: address is a different address from the http: one it replaces, so switching them over breaks the links that hold the web together. His alternative was to encrypt everything at the protocol level and keep the http: prefix, which is the parallel universe in a sentence. Not everyone agreed. The sharpest reply was that the s is the part that matters, which is a point I’ll come back to.
- ALPN is TLS’s `Upgrade` header. When HTTP/2 came along, it defined an upgrade from plain HTTP/1.1 using the Upgrade header. Browsers declined to support it and only do HTTP/2 inside TLS, which meant TLS needed its own mechanism for choosing which protocol to speak.
- ECH is fixing SNI. Because SNI sends the website’s name in the clear, anyone watching can see which site you’re visiting. Encrypted Client Hello is the current effort to hide it. To be fair to our universe, the parallel universe would have this problem too, as that first Host header goes in the clear.
- Proxies use `CONNECT`. When your browser goes through a proxy, it sends an HTTP request asking the proxy to open a tunnel, then starts TLS inside it. That’s an HTTP-style handover.
- HTTP/3 is discovered over HTTP. A server tells your browser it speaks HTTP/3 with an Alt-Svc header, and the browser switches over next time. Ask over HTTP, then move.

Not every lesson points my way, though. Email went the parallel-universe route with STARTTLS, upgrading a plain connection on the normal port. In 2018, RFC 8314 recommended that email clients use a dedicated port with TLS from the very first byte instead, because of the stripping problem.

## 🏁 Lazy or Right?

So was Netscape lazy, or right?

I think the honest answer is “right for the wrong reasons”, and the parallel universe shows which part was right. The thing that protects you from an attacker quietly downgrading your connection isn’t the separate port. It’s the `s` in the URL: a promise, made in advance, that this connection must be secure. Netscape almost certainly didn’t choose a new scheme for that reason. A new scheme and a new port were simply the easiest way to bolt encryption onto software that already existed. But the scheme is the part that earned its keep.

The port, I’m less sure about. I can’t help noticing how much of the past thirty years of TLS work has been spent rebuilding, inside a black box, things HTTP already had. I’d have liked to visit the universe where the `s` in `https://` means “this must be secure” and everything else is just HTTP.

**Credits**  
📸 “[Duck browsing the lake](https://www.flickr.com/photos/104082864@N04/53741152051/)” by Andres Alvarado. (CC BY-SA 2.0)  
📸 “[anim2038](https://www.flickr.com/photos/noaaphotolib/14318675298/)” by NOAA Photo Library. (CC BY 2.0)  
📸 “[Padlock by the sea](https://www.flickr.com/photos/gromgull/2642629481/)” by “gromgull”. (CC BY 2.0)  
📸 “[too tired to care](https://www.flickr.com/photos/rosiejuliet/52247781631/)” by “marneejill”. (CC BY-SA 2.0)  
🤖 Claude, for fact checking and editing.
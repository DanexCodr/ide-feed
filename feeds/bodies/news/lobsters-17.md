In January 2026, I somehow ended up leading Pion's DTLS 1.3 implementation and building most of it. It was still mostly an idea at that point, and I didn't really know how DTLS 1.3 worked. Most of the people who ended up building it with me didn't either :)

Ten months and ~400 commits later, DTLS 1.3 is the default in pion/dtls:

- a one-round-trip handshake
- post-quantum key exchange
- Connection IDs, so your connection survives your phone switching networks
- 0-RTT resumption
- Encrypted Client Hello

I wanted to write down the lore of how this happened, and also explain DTLS the way I wish someone had explained it to me. So this is both, with interactive demos you can poke and break along the way.

If you don't want to read the backstory, [skip to the implementation](https://joturk.net/posts/dtls#phone-calls-and-postcards).

Pion's [Plans for DTLS 1.3](https://github.com/pion/dtls/issues/188) issue had been open since February 2020, when the spec was still [a draft](https://datatracker.ietf.org/doc/draft-ietf-tls-dtls13/). It became [RFC 9147](https://www.rfc-editor.org/rfc/rfc9147) in 2022, but nobody had the time it takes to actually commit to it, and every so often someone asked for updates...

Meanwhile, in January 2025, Sean DuBois, who created Pion and its libraries, told me (a nobody) I could co-maintain it with him and handed me owner access to the whole thing. Sean trusted me more than I trusted me :)

I created Pion's Discord server, reviewed PRs every day, contributed new features across the stack, and talked my friends into contributing. But I kept opening that DTLS 1.3 issue, staring at it, and closing the tab. For DTLS fixes and reviews were fine, but anything bigger felt like I'd create an RCE!

Then, in May 2025, Theo ([Theodor Signebøen Midtlien](https://github.com/theodorsm)) said in the issue that he'd applied to [NLnet](https://nlnet.nl/project/PION-DTLS1.3/). The same day, Sean offered to review and merge everything, and to go knock on companies' doors for money if NLnet said no. NLnet said yes, and Theo announced the grant on August 6.

At the time, R Chiu and I were spending a lot of time in Pion's SCTP stack, the thing WebRTC data channels run on. She implemented [RACK loss recovery](https://pion.ly/blog/sctp-and-rack/).

Adriano Sela Aviles had also joined while working with us on Pion's TURN implementation, and sent really important PRs, but he and R had their own lives and were not able to go all the way with the implementation.

I'd read [the spec](https://www.rfc-editor.org/rfc/rfc9147) once and was comfortable with it from a high-level POV, so I was excited to help with reviews. R Chiu helped with the key schedule. But it was Theo's project, and while we wanted to help, we didn't want to get in the way.

People were waiting for it. In December, just as the project was starting, Justin Uberti from OpenAI, where Sean had worked, asked for updates. They wanted "reduced RTTs during connection setup, and also … post-quantum crypto support." Lower RTTs meant you didn't have to wait as long for voice AI to start.

Theo put together a high-level MVP plan and opened skeleton PRs, but then life got busy, including a new job at NetBird! By January 2026, I was starting a new WebRTC job at Upwork, but I don't have a family yet, so I have free time after work :) Theo was happy to hand me the project. I promised we'd do his plan right and extend it, including the parts outside the WebRTC subset. I wanted a real DTLS 1.3 library that Pion also happens to use, because users outside WebRTC need resumption, 0-RTT and Connection IDs too.

I don't want to get paid for my work on Pion, because I don't want to treat it as a job. I also wanted people to build it with me. So I asked my friends who had already contributed to Pion, **Jade Kolos**, **Júlia Borges Paschoalinoto** and **Julia-Elena Roman**, and later **Jan Muška**, to join the NLnet-funded effort, and recommended them to Theo. Then DTLS 1.3 was ours to finish :)

We had DTLS 1.2 extension parsers that didn't really understand DTLS 1.3, and an unmerged state machine skeleton. No record layer, no key schedule, no encryption, nothing that could finish a DTLS 1.3 handshake. And none of us had a real TLS background.

Roughly four months passed between the handoff and our first record-layer implementation. There were extension and helper commits, but the main implementation was stalled. We kept reading specs and other implementations: [RFC 9147](https://www.rfc-editor.org/rfc/rfc9147), [RFC 8446](https://www.rfc-editor.org/rfc/rfc8446), [RFC 9146](https://www.rfc-editor.org/rfc/rfc9146), IETF write-ups. I was still mostly anxious: I wanted to do this right and didn't want to break stuff people were already using.

Then Sean asked how it was going. That's when we got his backing to really go ahead. He helped with the code design (where DTLS 1.3 would fit with 1.2 in a clean way), the FSM, Go idioms, cleaning up some old code, and later most of the DTLS 1.3 ACK reliability.

But most importantly, other than the technical parts, he made me confident enough to build it and break stuff along the way. He told me I could merge stuff without review!

We didn't have to understand every last thing before starting. He reviewed, merged, unblocked and encouraged. Without him, I think this would've taken another year or more.

On May 13 we started the record layer. On June 19 we finally merged the state machine.

On July 7 I closed the six-year-old issue with this very reasonable estimate:

> I think we'll have a working production ready MVP within two weeks.

**That wasn't accurate.**

The server's Finished verified on July 12, and on July 29 the client's Finished verified too. A Pion client and server finally completed a DTLS 1.3 handshake. On August 5 I got the first confirmation of DTLS 1.3 working in WebRTC against Chrome! I hadn't slept for two days, and couldn't believe it. I'd written most of it without testing against another implementation lol.

[Our team's write-up](https://pion.ly/blog/dtls-one-three/#finished-is-a-different-story-in-1-3) has a line I really like: *"Finished" is a different story.* The handshake was just the beginning. August was more than a hundred commits: Connection IDs, KeyUpdate, HelloRetryRequest, SRTP negotiation, rewriting extension parsing, and a week deleting duplicated code that I badly underestimated.

We tagged the first v4 release candidate on September 26. Two days later I closed the tracking issue, and DTLS 1.3 went into Pion WebRTC's next major version. People outside WebRTC were already trying it on real IoT clusters. Seeing them pick up resumption and the other features motivated me to finish ECH and 0-RTT.

On October 14 I said support was complete. Before we released it, Anthropic rolled out their OSS scanner, and we [sent pion/dtls through it](https://github.com/anthropics/oss-scanner/pull/93). It found many old issues, but also new ones in the new implementation. Yey, we got to fix them before release!

On October 31, DTLS 1.3 became the default in pion/dtls. No more "not implemented" errors, examples using 1.3 by default, and 1.2 one option away. v4.0.0-rc.8 is tagged, final v4 is next, and Pion WebRTC's next major version will bring it to everyone who uses it.

So enough with the yapping! Let's dive in. But before we get into DTLS, what even is the D in DTLS? And how does it relate to TLS?

Everything on the internet travels in packets. What happens when one goes missing depends on how you're sending them.

**TCP is a phone call.** You get a connection, and everything you say arrives complete and in order, or not at all. If a packet gets lost on the way, TCP notices, sends it again, and makes everything after it *wait* until it arrives. You never see the gap, the conversation just pauses.

**UDP is postcards.** Each packet, a *datagram*, travels on its own with its own address, and it either arrives whole or not at all. Postcards get lost, arrive out of order, and sometimes the same one shows up twice. Nobody resends anything and nobody waits.

Here are both, carrying the same message, with the same bad luck:

Try it a few times and tap a packet or two in flight. TCP always delivers a perfect `HELLO, PION!`, but it can take longer to finish, because one lost letter holds up every letter behind it. This is called *head-of-line blocking* (and it's the boogeyman of the real-time world). UDP finishes sooner, but what arrives is a mess. The app can sort it if it numbered its postcards, but the lost ones are just gone.

The mess is fine for a lot of things, because for real-time media late is the same as lost. One can argue that an audio packet that arrives 300ms late is useless: the moment it was meant for has already passed. Video is even worse: a frame is usually split into many packets, and later frames depend on earlier ones, so waiting for one lost packet holds up everything behind it, the same head-of-line blocking as TCP. It's better to keep going and decide what's actually worth recovering.

WebRTC, for example, has a few ways to do that on top of UDP. RTP numbers every packet, like the postcards above, so the receiver knows exactly what's missing. With [**NACK**](https://webrtcforthecurious.com/docs/05-real-time-networking/#negative-acknowledgments), it tells the sender which sequence numbers it lost and the sender resends just those. That costs at least one extra round trip, so when there's no time to wait there's **FEC** (forward error correction): the sender adds a few extra parity packets, and the receiver rebuilds a lost packet from them without asking for anything. There's [a whole post about FEC in Pion](https://pion.ly/blog/fec-with-pion/) if you want the details.

That's why WebRTC *tries*(*) to send its media and data over UDP: it gets to decide what's worth waiting for.

(*) WebRTC can also use TCP transports, either directly with ICE-TCP or through a relay with TURN over TCP or TLS. DTLS is still used in both: with ICE-TCP the DTLS records are carried inside the TCP stream, and with TURN only the hop to the relay is TCP, and the relay usually forwards the same DTLS packets to the other side over UDP.

Anyway, the problem is that the protocol that keeps the internet private, [TLS](https://www.rfc-editor.org/rfc/rfc9846), was designed for phone calls. It assumes nothing gets lost, reordered or duplicated. Put it on postcards and it falls apart.

DTLS (Datagram TLS) is TLS rebuilt for postcards. To see what had to change, we first need to know what TLS actually promises.

TLS makes three promises about the conversation between Client and Server:

1. Nobody else can read it. (Confidentiality.)
2. Nobody can change it without getting caught. (Integrity.)
3. You're talking to who you think you're talking to. (Authentication.)

Mallory is the reason all three exist. She sits on the wire, which in real life is your coffee shop's Wi-Fi, a compromised router, a shady ISP, or anyone else between you and the server. Every packet goes through her.

You might think encryption takes care of the second one too. If Mallory can't read the message, how is she going to change it into anything useful? Try it:

Encryption alone hides *what* you said, but a stream cipher like AES-CTR just XORs your message with a keystream, so flipping a bit in the ciphertext flips the same bit in the plaintext. Mallory doesn't need the key, she only needs to know where `10` is in the message.

That's why every cipher in TLS 1.3 and DTLS 1.3 is an **AEAD** (*authenticated encryption with associated data*). AES-GCM and ChaCha20-Poly1305 encrypt the record and compute a tag over it. Change one bit anywhere and the tag doesn't match, so the record gets dropped. Older TLS versions did encryption and authentication separately and got burned by the gaps between them more than once, so TLS 1.3 removed every cipher that isn't an AEAD.

AEADs need a key that only Client and Server know. But they've never met before, and every message between them goes through Mallory, so they have to agree on a secret while she listens to every word. We can explain it with paint:

Each side keeps a secret and only sends a *mix*. Mallory sees both mixes but can't un-mix them, so both sides end up with the same final color and she can't make it herself. In real crypto the "paint" is elliptic-curve math (X25519 is the common one), and "un-mixing" means solving a problem no current computer can solve in any reasonable time.

In TLS 1.3 the client doesn't wait to be asked. It guesses which key exchange the server will accept and puts its half, the `key_share`, in the very first message, the ClientHello. If the guess is right, the server answers with its own half and can start encrypting right away. That's why TLS 1.3 needs one round trip where TLS 1.2 needed two.

Key exchange alone doesn't stop Mallory from sitting in the middle and doing a separate key exchange with each side. That's what promise three is for. The server proves who it is by signing the handshake with its certificate's private key (the `CertificateVerify` message). Then both sides send a `Finished` message, a MAC over every handshake message so far (the *transcript*). If Mallory changed even one byte anywhere in the handshake, the transcripts won't match and the checks fail. Be Mallory and try:

Watch what catches her each time. If she touches the hellos, the transcripts stop matching, so the server's signature and the Finished MACs fail. If she swaps the key shares, she gets surprisingly far, until the server has to prove who it is. She can fake a key exchange, but she can't sign as `server.example` without its private key, and no CA will vouch for her own certificate. Well, unless she finds a CA whose private key is literally `4`, which [actually happened](https://www.helpnetsecurity.com/2026/10/21/emudhra-certificates-private-keys-compromised/) this October :)

That's how it works on the web, for example, where a CA says which certificate belongs to `server.example`. Standard WebRTC peers don't use CAs for authentication. Instead, each peer has its own certificate (which can be generated on the spot and self-signed) and puts its **fingerprint**, a SHA-256 hash of that certificate, in the SDP (Session Description Protocol) it sends through your signaling server:

```
a=fingerprint:sha-256 4A:AD:B9:B1:3F:82:18:3B:54:02:12:DF:3E:5D:49:6B:...
```

After the DTLS handshake, each side hashes the certificate the other side actually used and compares it with the fingerprint from the SDP, which is usually sent over HTTPS or a WebSocket over TLS. If Mallory swaps in her own certificate, the hash won't match and the connection fails. In WebRTC both sides send a certificate, so both sides get checked. The catch is that DTLS is only as trustworthy as your signaling: if Mallory can edit the SDP, she can put her own fingerprint in it.

Some connections don't use certificates at all. With a **pre-shared key** (PSK), both sides already share a secret, for example a key that was put on an IoT device at the factory, and knowing the key is the proof of identity. The handshake keys come from the PSK, so without it Mallory can't finish the handshake as either side. It's a lot cheaper than certificates, which is why it's popular on small devices. More on PSKs later.

So that's TLS in four steps:

1. hello with a key share
2. hello back with a key share
3. encrypted proof of identity
4. Finished

Now let's put it on postcards.

TLS assumes it's on a phone call, so it takes some shortcuts, and every one of them breaks on UDP.

**It counts silently.** Every TLS record is encrypted with a nonce derived from a sequence number, but the number is never sent, both sides just count 0, 1, 2... On a phone call that's safe. With postcards, one lost record means the receiver thinks record 5 is record 4, uses the wrong nonce, and every record after that fails to decrypt. Drop one record and watch:

One lost postcard and the TLS receiver is off by one forever. So DTLS puts the **epoch and sequence number in every record header**, in the clear. (DTLS 1.3 encrypts them again, more on that later.)

**It assumes the handshake arrives.** In TLS a lost handshake message is TCP's problem, in DTLS it's yours. Each side groups its handshake messages into *flights* and starts a **retransmission timer**. If the next flight from the other side doesn't show up in time, it sends its own flight again.

**It assumes any message fits.** A TLS handshake message can be up to 16 MB and TCP will happily stream it. A UDP datagram that's too big for the path gets dropped, or chopped into IP fragments that plenty of firewalls and NATs drop anyway, and the safe size on the internet is about 1200 bytes *[give or take](https://github.com/pion/sctp/pull/476)*, while a certificate chain is often several kilobytes. So DTLS adds a 12-byte header to every handshake message that says which message it is, how long the whole thing is, and which bytes this fragment carries:

This one actually bit us. A retransmitted message is allowed to be fragmented *differently* from the original. OvenMediaEngine, an OpenSSL-based media server, splits its handshakes into tiny 256-byte fragments, and Pion's DTLS 1.2 reassembly assumed fragment boundaries would line up, so after a single lost datagram the handshake could never finish. Tristan Matthews [fixed it](https://github.com/pion/dtls/pull/1099) by making reassembly track which *bytes* it has instead of which *fragments*.

Post-quantum crypto makes it worse. The post-quantum key share Pion sends by default is 1216 bytes on its own, so now even the first message of the handshake doesn't fit in one datagram.

And of course that broke something. wolfSSL, which a lot of embedded devices run, wants the first ClientHello in a single datagram so it can answer without keeping any state, and [by default](https://github.com/wolfSSL/wolfssl/blob/b24278145e7a7f3999082b2d793b1febbe665d57/src/dtls.c#L45) it just won't take a fragmented one. Most people using pion/dtls directly are doing IoT, so that's the worst place to break. Raising the MTU doesn't help either, the ClientHello needs 1415 bytes and plenty of networks can't do that. So now Pion [sends an X25519 share next to the hybrid one](https://github.com/pion/dtls/pull/1289) like Go does, and clients [put plain X25519 first](https://github.com/pion/dtls/pull/1292) so the first ClientHello fits again. If the server wants post-quantum, it asks for it with a HelloRetryRequest, so we still get ML-KEM everywhere it's supported. Clients with early data keep ML-KEM first, because a retry throws the early data away. I kinda get the X25519MLKEM768 hate now :(

**It assumes nobody repeats things.** Networks do occasionally duplicate packets, but TCP throws away bytes it already has, and if Mallory spliced an old record into the stream, TLS's silent counter would have moved on and it wouldn't decrypt. DTLS just put the sequence number in the header, so with UDP Mallory can record a perfectly valid encrypted packet and send it again as many times as she wants, and it decrypts fine because it *is* valid. So DTLS keeps a sliding **replay window**, a bitmap of recently seen sequence numbers, and drops anything it already saw or that's too old to tell:

Now switch to "slide, then authenticate" and have Mallory send her garbage. One fake record with a huge sequence number pushes the window a million packets ahead, and every real packet after it looks ancient. That's why the window should only move after a record is authenticated.

**It assumes the sender's address is real.** TCP's handshake proves the other side can receive packets at its address before anything else happens. UDP has nothing like that, so Mallory can write anyone's address on her postcards. If she sends a small ClientHello with a victim's address, the server answers the *victim* with its big first flight, certificates and all, turning a few hundred bytes into a few kilobytes aimed at someone else. So DTLS servers answer a new ClientHello with a small **cookie** first, and only do real work after the client echoes the cookie back, proving it can receive mail at that address:

In WebRTC, ICE's connectivity checks often prove the address before DTLS even starts, so is the cookie still worth a round trip? Not always: SFUs usually run ICE-lite, which only answers checks and never sends its own, so the server never learns whether the client's address is real. Philipp Hancke and I [are working on a more nuanced default](https://github.com/pion/webrtc/pull/3504).

That's the "D": explicit sequence numbers, timers, fragments, a replay window and cookies, all added to TLS so it survives postcards. DTLS 1.2 already did all of this, and Pion had supported it for years.

DTLS 1.3 starts from TLS 1.3 and redesigns a lot of this. Let's go through the pieces.

My first big design decision was that a connection is always in exactly one of three modes. I wanted to make this super explicit because of a [Firefox bug](https://bugzilla.mozilla.org/show_bug.cgi?id=2033783) that broke calls to Pion: Firefox speaks both versions, and its fallback to 1.2 went wrong. We kept coming back to this for the rest of the year:

1. DTLS 1.2 only.
2. DTLS 1.3 only.
3. Dual, where the version isn't decided yet and the client must still be able to talk to an old 1.2-only server. In this mode we're also explicit about which state we're in:
  1. Not decided yet.
  2. Decided to continue with 1.3.
  3. Decided to downgrade to 1.2.

A lot of our hardest bugs were in that third one. Pick a client and a server and connect:

Dual mode is tricky. The client sends one ClientHello that has to be a valid DTLS 1.2 hello *and* a valid DTLS 1.3 hello at the same time, and it only finds out which one it was when the server answers. If the answer is 1.2, everything from the 1.3 attempt has to disappear without a trace. Our first fallback didn't clean everything up. You can switch that bug on in the demo above. And Mallory can't force a downgrade either: a 1.3 server that gets pushed down to 1.2 writes `DOWNGRD` at the end of its random value, and the client notices.

## [The record layer](https://joturk.net/posts/dtls#the-record-layer)

A DTLS 1.2 record header is 13 bytes, on every single packet. For a video call that's a lot of bytes spent on bookkeeping. DTLS 1.3 replaced it with a *unified header*, where the first byte is a set of flags that say what comes after it. Poke the bits:

Three things changed.

**It's smaller.** The smallest DTLS 1.3 header is 2 bytes. The content type (handshake, alert, application data) isn't in the header anymore, it moved *inside* the encryption, so Mallory can't even tell what kind of record she's looking at.

**The sequence number is encrypted.** DTLS had to put the sequence number on every postcard, but that's also a tracking number for Mallory: she can count packets, follow a connection across networks, and measure exactly how much was sent. DTLS 1.3 encrypts those bits with a mask derived from the record's own ciphertext. Toggle "what Mallory sees" and click next a few times: the real numbers go 42, 43, 44, and she just sees noise.

**It's mostly implicit.** Only the low 8 or 16 bits of the sequence number and the low 2 bits of the epoch are sent, and the receiver reconstructs the rest from what it expects next. That only works because the receiver keeps careful state about every epoch, which brings us to keys.

As I wrote in [the team's write-up](https://pion.ly/blog/dtls-one-three/#the-names-are-scarier-than-the-concepts): the names are scarier than the concepts. HKDF, AEAD, transcript hash, epoch, each is a small idea with a scary name.

TLS 1.3 doesn't use *a* key, it uses a whole family of keys, each derived from the one before it and each protecting a different part of the conversation. Encrypted handshake messages get one key, application data gets another, and after a KeyUpdate you get a fresh one and the old one can be forgotten. In DTLS each of these keys lives in its own *epoch*, and the epoch number in the header tells the receiver which key to use.

The thing that produces them is the *key schedule*, and it's built from one tool: HKDF, which takes some secret material and stretches it into as many independent keys as you need. You can try the actual key schedule here. It's computed in your browser:

Click "new handshake" and watch every value below it change. One fresh key exchange at the top, and every key below it is new and unrelated to any previous connection. This is called *forward secrecy*: if someone steals the server's certificate key next year, they still can't decrypt today's call, because the keys never depended on it.

The other input is the *transcript hash*, a running hash of every handshake message so far. Mixing it into the keys means that if Mallory changed anything, the two sides derive different keys and just can't talk. I spent a good part of June getting that transcript exactly right. Miss one byte, hash a message twice, or accidentally include a retransmission, and nothing works. And nothing tells you why it didn't :)

In July we implemented the ciphers (AES-128-GCM, AES-256-GCM and ChaCha20-Poly1305), record number masks, seal and open. On July 1 Pion also got **X25519MLKEM768**, the hybrid post-quantum key exchange. It does an X25519 exchange and an ML-KEM exchange together, so the result is safe as long as *either* one holds up. This matters because of *harvest now, decrypt later*: someone recording your encrypted call today could decrypt it in fifteen years with a big enough quantum computer, unless the key exchange already resists one. By August it was on by default.

Not everyone is a fan of ML-KEM, though. Daniel J. Bernstein, the person behind X25519 and ChaCha20, [campaigned against](https://nsa.2026.action.cr.yp.to/) an [IETF draft](https://datatracker.ietf.org/doc/draft-ietf-tls-mlkem/) that uses ML-KEM *on its own* in TLS, and says the NSA is paying to get it standardized. He calls the hybrid, the one Pion uses, "much more sensible". If ML-KEM ever falls, X25519 is still there :)

Reliability in DTLS 1.2 is pretty basic. Nobody acknowledges anything: if I don't hear back in time, I resend my *entire* flight, even if only one packet out of six was lost. And if the reply was lost instead, the other side resends its entire flight too.

DTLS 1.3 added an **ACK** message: "here are exactly the records I got." The sender resends only the gaps, and the receiver can send an ACK as soon as it notices a hole, without waiting for a timer. Same bad luck on both sides:

After "Finished", it really was a different story: there's a whole second state machine for session tickets and KeyUpdate, with its own ACKs and retransmissions. So getting Finished to work still leaves you with basically another protocol to implement :(

In WebRTC, calls can use ICE to find a new path when the network changes ([Pion has a post about that](https://pion.ly/blog/automatic-renomination/)), so they don't need Connection IDs, but they [matter for IoT users](https://github.com/pion/dtls/issues/188#issuecomment-1481151054).

Without a Connection ID, a DTLS server finds the connection a packet belongs to by where it came from: the client's IP address and port. Now walk out of your house. Your phone drops Wi-Fi, switches to cellular and gets a new address, and the server has never heard of it.

With a Connection ID, every record carries a short ID that the server picked, and the server finds the connection by ID instead of by address, so your connection survives the walk to the car. Pion already had CIDs for DTLS 1.2. In 1.3 they're part of the core protocol and really different, so we had to rebuild them into the new record layer, while reworking the DTLS 1.2 implementation so we wouldn't have duplicated code.

Of course Mallory can make this a problem too. If the server just follows the newest address a valid record came from, she can record one real packet and resend it with the *victim's* address on it, and the server redirects the whole video stream at someone who never asked for it. The specs saw this coming: CIDs in both DTLS 1.2 and 1.3 already said you must check that a new address can receive before switching to it, but never said how, so many implementation didn't enforce this (including Pion's DTLS 1.2).

**Return Routability Check** ([RFC 9853](https://www.rfc-editor.org/rfc/rfc9853)) is the standard way: before trusting a new address, send it a small challenge, and only switch once the answer comes back. Try the second half of the demo with RRC off, then on.

RRC has a fun backstory. While reading the [IETF shepherd write-up](https://datatracker.ietf.org/doc/draft-ietf-tls-dtls-rrc/shepherdwriteup/) for the RRC draft, I found this: "We have two different clients (Eclipse/Californium & Pion) that interoperate with a server." Someone had used a Pion fork for testing! I got so excited about that, I went and built a real production RRC for upstream Pion while we were still doing DTLS 1.3, instead of postponing it until after the release!

**Pre-shared keys and resumption.** If the client and server talked before, or share a key from somewhere else, they can skip the certificate work entirely. Smaller handshakes, less CPU, and still forward secret when combined with a fresh key exchange.

**0-RTT.** If you talked before, you don't have to wait at all. With a resumed session, the client can send application data in its very first flight, encrypted with keys from last time. Here's how the handshakes compare, and the catch:

0-RTT data can be replayed. There's no fresh input from the server protecting it yet, so Mallory can capture it and send it again. That's fine for "show me the menu", not fine for "pay $10", so applications have to opt in and only send things that are safe to repeat. It also gives up some forward secrecy: go back to the key schedule, turn on "with PSK" and press "new handshake" a few times. The early secret never changes, because it only comes from the PSK, so anyone who steals that PSK later can decrypt the early data.

**Encrypted Client Hello.** TLS 1.3 already encrypts the certificate, so which site you visit is hidden, except for one field: the ClientHello carries the server's name (the *SNI*) in plain text, because the server needs it to pick the right certificate. ECH encrypts the real ClientHello inside an outer one that only names a generic front server:

While implementing ECH, I wanted our implementation to match `crypto/tls`, because I felt it was the right thing to do. But as soon as I started, I found two places where Go's own `crypto/tls` was too lenient with ECH configurations, and sent them patches ([one](https://go-review.googlesource.com/c/go/+/845746), [two](https://go-review.googlesource.com/c/go/+/846885)). So we went back to doing it our own way, which turned out to be the stricter implementation.

I think setting up interop tests was the best decision we made all year. Testing Pion against itself only proves both sides share the same assumptions, so in April I created [`pion/dtls-interop`](https://github.com/pion/dtls-interop) and froze releases from main until interop was ready. It tests Pion against:

- OpenSSL 3 and 4
- BoringSSL
- wolfSSL
- Mbed TLS
- the TLS-Anvil conformance suite
- Pion's own v3

On September 28, when DTLS 1.3 went into Pion WebRTC's next major version, I added it to [`pion/browser-tests`](https://github.com/pion/browser-tests), which runs Pion WebRTC against Chrome, Firefox, Edge and Safari.

Anthropic's OSS scanner went through pion/dtls and sent us a report. On October 16 I opened [#1228](https://github.com/pion/dtls/issues/1228), "Fix all issues reported by anthropics/oss-scanner", and spent the busiest two weeks of the whole project working through it. Most of the real issues were in DTLS 1.2, session resumption and shared code that had been in production for years, not the new DTLS 1.3 code, and we fixed them on both main and the v3 branch so existing users can upgrade without changing anything. After spending so much time anxious about breaking stuff, that felt really good :)

**[sirzooro](https://github.com/sirzooro)** independently reported a few of the same issues (and others), found with Claude Opus 5.5.

There was one finding we couldn't fix in code.

Pion v3 lets you export a connection's state and resume it later, for example to hand a connection from one process to another. The scanner pointed out that nothing stops both the original and the restored connection from continuing to send. Both would keep encrypting with the same AES-GCM key and the same sequence numbers, and the nonce is built from the sequence number.

Reusing a nonce with AES-GCM is one of the worst things you can do in cryptography. Here's why:

AES-GCM encrypts by XORing your message with a keystream generated from the key and the nonce. Same key and nonce means same keystream, so XORing the two ciphertexts cancels the keystream out and leaves the two *plaintexts* XORed together. Mallory doesn't need the key: she guesses a likely word in one message, and the other message shows up around it. The same reuse also leaks enough for her to forge tags.

Sadly we couldn't make the v3 API safe without breaking everyone who uses it, so v3 now documents loudly that a restored state must be used exactly once. In v4, `Resume` requires `ExportState`, which closes the original connection as part of the export, so there's no way to keep using both.

## [Thank you](https://joturk.net/posts/dtls#thank-you)

I'm really happy with what we built. I never thought I'd lead a project this big all the way to the end, and that still feels a bit weird. But the part I'm most proud of is the people. Whenever I got stuck, or talked about a problem for hours in our Discord server or group chats, someone was always there to listen and help.

None of this would exist without the people I built it with: [Sean DuBois](https://www.linkedin.com/in/sean-dubois/), [Theodor Signebøen Midtlien](https://www.linkedin.com/in/theodorsm/), [Adriano Sela Aviles](https://www.linkedin.com/in/adrianosela/), [R Chiu](https://www.linkedin.com/in/r-chiu-60b4381b9/), [Jade Kolos](https://www.linkedin.com/in/jade-kolos/), [Júlia Borges Paschoalinoto](https://www.linkedin.com/in/julia-paschoalinoto/en/), [Julia-Elena Roman](https://www.linkedin.com/in/julia-elena/) and [Jan Muška](https://www.linkedin.com/in/frantabot/). Thank you for all the reviews and testing, and sorry for how annoying I was about stuff I found cool :)

Huge thanks to **[Thomas Legris](https://github.com/noboruma)**. He runs DTLS for a very large fleet of IoT devices with Pion on the server side, and at that scale every allocation per connection gets multiplied by hundreds of thousands. [One of his PRs](https://github.com/pion/dtls/pull/1096) starts with "At scale (700k connections) - I detected some heavy allocations, especially at handshake." Over the year he sent a lot of optimizations:

- fewer copies and allocations in the handshake
- pre-allocated buffers for marshalling
- pooled timers
- a reworked PacketConn with fewer goroutines per connection, in pion/dtls and pion/transport
- a fix for a connection leak

Then he ran the release candidates in production, and they worked without a single problem.

Resumption got tested before it was even tagged, and I can't tell you how happy that made me :) **[ybaldus](https://github.com/ybaldus)** [opened an issue](https://github.com/pion/dtls/issues/1201) about deadlines while building SWIM on pion/dtls, which "requires short lived connections and session resumption to be scalable." When I said resumption wasn't tagged yet: "Don't mind tagging it yet I can also use the current master commit." The report turned into a [fix](https://github.com/pion/dtls/pull/1207) that applies read and write deadlines to the handshake.

**Leonard** ([ltlobaro](https://github.com/ltlobaro)) did the same from the IoT side, where "DTLS 1.2 handshakes easily take up most of the device traffic". They played with the DTLS 1.3 resumption example, [found that key logging didn't work with DTLS 1.3](https://github.com/pion/dtls/issues/1223), and it was [fixed](https://github.com/pion/dtls/pull/1224) in rc.5 the same day.

**[devArnoud](https://github.com/devArnoud)** ran DTLS 1.3 against a cellular modem whose TLS stack is wolfSSL baked into its firmware, and every handshake failed. When the server asked the modem to send its ClientHello again, wolfSSL sent the same extensions in a different order. [The spec](https://www.rfc-editor.org/rfc/rfc9846#section-4.2.2) doesn't strictly allow that, but for compatibility Pion [accepts it now](https://github.com/pion/dtls/pull/1156).

**[enobufs](https://github.com/enobufs)** [tried DTLS 1.3 with WebRTC](https://github.com/enobufs/dtls13-webrtc-demo) early and [helped with the keying-material exporter](https://github.com/pion/dtls/pull/1133).

Thanks to **[Philipp Hancke](https://github.com/fippo)** for testing DTLS 1.3 in his [SPED implementation](https://github.com/pion/webrtc/pull/3362), which embeds the DTLS handshake in STUN, and for [noticing](https://github.com/fippo/warp-snap-sped/issues/20) that Pion sent a session ticket even to clients that never use resumption.

Thank you to everyone who reviewed, tested, reported and fixed things along the way. Thanks to [NLnet](https://nlnet.nl/) and the NGI0 Commons Fund for funding work like this, and to the Anthropic OSS scanner team for the report that made v4 safer before anyone found out the hard way.

And thank you for reading this far :) Now go break something.

Come chat with us on the [Pion Discord](https://discord.gg/HuvXUrvxZ8) about anything.
Creating a direct connection between *any* two computers (not just from client
to server) over the internet is notoriously difficult. Many home networks are
behind NATs which prevent new inbound connections. Sometimes these NATs are from
the ISP (carrier-grade NATs) which are impossible to work around with port
forwarding and/or UPnP. While
[hole punching techniques](https://en.wikipedia.org/wiki/Hole_punching_(networking))
*can* break through NATs, it's far from guaranteed. Thus, we need something that
works in the general case: **relays**.

Relays are servers, accessible over the public internet, that act as a proxy
between two computers that cannot directly connect. In
[Goblins 0.12](https://spritely.institute/news/spritely-goblins-v0-12-0-released-two-new-netlayers-join-the-ocapn-family-and-more.html)
we introduced a *federated* relay named "prelay". While OCapN traffic is
encrypted in transit, the prelay crucially lacks
[end-to-end encryption (E2EE)](https://en.wikipedia.org/wiki/End-to-end_encryption).
E2EE secures all the messages so they can only be read by their intended
recipient, preventing intemediatory parties (like the relay) from tampering with
or reading them. Due to the lack of E2EE, the relay was named "prelay"
(pre-relay) to dissuade its use. Thanks to a
[grant from NLnet](https://nlnet.nlproject/OCapN-federatedrelays/), we're happy
to announce that the next release of Goblins will include a federated, E2EE
relay implementation!

Having a relay that we could recommend has become even more of a critical part
of the OCapN story as we've developed [Hoot](https://spritely.institute/hoot/),
our Scheme to WebAssembly compiler. The web is a challenging environment in
which to build peer-to-peer applications. Most of the patterns and available
APIs are designed around client-server architectures and centralized certificate
authorities for security. While relays are unsatisfying compared to making
direct connections, they enable peer-to-peer applications to communicate in
these hostile environments.

In addition to implementing the E2EE relay for Goblins, our NLnet grant also
includes writing a specification for the OCapN group so that the relay can be
broadly supported by other OCapN implementations.

## Design

We wanted OCapN relays to have the following qualities:

1. Stateless: no storage of user data; easy to replace or migrate
2. Federated: reduces the power any one relay holds over the wider network
3. End-to-end encrypted: prevents man-in-the-middle and replay attacks; perfect forward secrecy

Our existing "prelay" already has the first two properties.  To get E2EE, we
chose to build upon the [Noise Protocol](https://noiseprotocol.org/).

Noise is actually a well-established framework of different patterns and
ciphers. This allows applications to pick the pattern which is most suitable to
their needs. It's also a protocol family which has widespread use (WireGuard,
WhatsApp, etc.) and has been scrutinised a great deal. None of us at Spritely
are cryptographers by training, so using an off-the-shelf protocol also ensures
we're avoiding any mistakes in protocol design.

So how can we use Noise with OCapN? When connecting to an OCapN peer, there is a
[Locator](https://github.com/ocapn/ocapn/blob/main/draft-specifications/Locators.md#ocapn-peer)
which encodes three components about the remote peer:

1. Designator: self-authenticating identity (usually a public key)
2. Transport: a symbol identifying the kind of netlayer it is (such as onion)
3. Hints: a hashmap of routing data (such as IP, port, etc.)

Each netlayer decides what goes into these fields, and the union of both the
designator and transport should uniquely identify the peer. Noise uses two kinds
of keys:

1. static: a key that doesn't change between sessions
2. ephemeral: a key that is generated fresh for each session

An important step each netlayer needs to consider is something called *peer
authentication*, which verifies that a peer is who they say they are. OCapN
requires that there exists
[**at most one** connection](https://github.com/ocapn/ocapn/blob/main/draft-specifications/CapTP%20Specification.md#opstart-session)
between any two peers at a given time. Ensuring there is only ever one
session between any two peers is essential to allow for object identity
comparison and preventing unnecessary
[3rd party handoffs](https://github.com/ocapn/ocapn/blob/main/draft-specifications/CapTP%20Specification.md#third-party-handoffs).
An OCapN implementation will enforce this by reusing connections or closing new
inbound connections if one already exists. Without peer authentication, a
malicious peer could impersonate another peer causing a denial of service to the
peer whose identity was stolen.

As described above, the designator is a public key, which allows the peer to
prove their identity by using its private key. Noise has a pattern for this
known as `XK`, where the initiator knows the key of the responder and will
verify it. The `X` is referring to the initiator's static key being transmitted
to the responder. The `K` is referring to the initiator already knowing the
responder's public key. The public key of a peer is encoded and placed in the
designator for the initiator to use.

Noise also allows the use of different key generation algorithms, cipher suites,
and hashes. This is great as we needed to select something which has
implementations both in commonly available cryptographic libraries and within
the browser (for Hoot). X25519 keys are well supported in all those situations,
as are AESGCM cipher suites and SHA256 hashes. These are all available in
GnuTLS (what we're using on the Guile VM) and in the
[SubtleCrypto API](https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto)
(that we're using on the web).

## Guile Noise library

Of course, to use Noise we need an implementation. Noise is popular enough that
there's quite a few implementations for different languages. Unfortunately,
Guile is not one of them, so that meant writing our own Noise library.

The [Guile Noise library](https://codeberg.org/spritely/guile-noise) we've
written doesn't require users to know the intricate workings of Noise, but Noise
is interesting and so let's take a brief look at how it works and my
implementation experience. The
[Noise specification](https://noiseprotocol.org/noise.html) is actually pretty
approachable and is built around three conceptual objects:

- CipherState: holds a key and a hash; provides encryption, decryption, and rekeying
- SymmetricState: holds a chaining key and hash output; uses CipherState for encryption, as well as deriving new keys and hashes
- HandshakeState: holds state for the initial handshake and handles reading and writing of handshake messages

The Noise protocol starts with a handshake. This is turn-based where the
initiator goes first and writes their handshake message. The receiver then reads
that message and writes their own. This continues until the handshake is
complete. After which you only need the `CipherState` which can encrypt and
decrypt messages (and if desired
[rekey](https://noiseprotocol.org/noise.html#rekey)).

Interestingly, Noise defines a small intepreter which defines a limited set of
operations. The handshake patterns are then defined in terms of these
operations. I won't go through all of them (see the spec if you're interested),
but the `XK` pattern is defined as:

```
pre-message <- s
-> e es
<- e ee
-> s se
```

This is a handshake consisting of three messages (and a
pre-message). Pre-messages are not exchanged as part of the Noise handshake
itself, they're messages which are expected to have happened out-of-band prior
to connection. In this case `<- s` means the static key from the responder is
sent to the initiator. This happens by it being encoded in the OCapN peer
locator as we discussed above. The arrows show the direction with the left side
being the initiator and the right being the responder.

I'll just cover the first message, `-> e es`. This message is for the
initiator to send to the responder as it starts with `->`. The operations are:

- e: generates an emphemeral key, transmits the public part, and mixes it into an internal hash
- es: derives a new key (from the ephemeral key and responders static key) and mixes it into its own key

This allows a Noise library to easily support lots of different patterns. Each
pattern can define it's pre-messages and handshake messages (all of which are
defined in the spec) and the implementation just needs to go through and perform
the steps.

Once the handshake is complete, the Noise library will create two `CipherState`
objects. The first is used for encrypting and decrypting the initiator's
messages, the second for the responder's messages.

The Guile library implements all 12 of the
[fundamental interactive patterns](https://noiseprotocol.org/noise.html#interactive-handshake-patterns-fundamental).
We built this library to work on both Hoot and the Guile VM. It currently uses
`SubtleCrypto` for Hoot and GnuTLS for the Guile VM, but it's written so users
of the library can add support for other crypto libraries. Our library comes
with support for X25519 key generation, AES-GCM ciphers, and SHA256 and
SHA512 hash functions. Noise not only provides an approachable spec, but also a
set of
[test vectors](https://github.com/noiseprotocol/noise_wiki/wiki/Test-vectors) to
help implementation. These are a set of messages which Noise should exchange for
a given pattern and keys. Our library has been tested against all the vectors
for patterns and crypto that we support and the test runner checks them on Hoot
as well as the Guile VM.

## Noise netlayer design

OCapN is a layered protocol consisting of CapTP (Capability Transport Protocol)
and many *netlayers*. A netlayer sends encoded messages between two peers over a
particular medium. This allows the higher-level CapTP to be *transport
agnostic*. For example, the
[Onion netlayer](https://files.spritely.institute/docs/guile-goblins/latest/Tor-Onion-Services.html)
provides transport over Tor Onion services. However, netlayers can be defined
not only in terms of a specific transport protocol, but also in terms of
*another netlayer*. We call these *meta netlayers*.

Noise itself isn't designed with a specific transport protocol in mind, and the
Noise netlayer isn't either. Indeed many netlayers might want to rely on the
properties of Noise for many different reasons. Even netlayers which provide
strong encryption, like Tor, may wish to rely on Noise for its bidirectional
peer authentication properties (Tor authenticates outbound connections to a
hidden service, but not the reverse).

The Noise netlayer thus composes with any other netlayer. Composing the Noise
netlayer and prelay netlayer yields an *end-to-end encrypted relay netlayer*!

How does this work? The Noise netlayer spawns a sort of "bootstrap" object (not
the same
[bootstrap](https://github.com/ocapn/ocapn/blob/main/draft-specifications/CapTP%20Specification.md#bootstrap-object)
if you're familiar with CapTP). The bootstrap object is encoded within the OCapN
peer locator, and can be *enlivened* to make a live reference when making a new
outbound connection. Each side spawns an
[inbox and outbox pair](https://files.spritely.institute/docs/guile-goblins/latest/Inbox.html),
and the initiating peer delivers their outbox to the bootstrap object. The
bootstrap object sets up its side of Noise and makes its own inbox-outbox pair
returning its outbox. Each side is then able to deliver messages to each other
by sending messages to the remote outbox object. Each side then follows the
handshake procedure. Once complete, encrypted messages can be exchanged by using
the Noise encrypt procedure and decrypted when read from the inbox.

Looking at the test code which uses the
[TCP+TLS netlayer](https://files.spritely.institute/docs/guile-goblins/latest/TCP-_002b-TLS.html),
layering on Noise encryption is just a few lines of code:

```
(define a-mycapn
  (with-vat vat-a
    ;; Spawn the TCP+TLS netlayer
    (define tcp-tls-netlayer (spawn ^tcp-tls-netlayer "127.0.0.1"))
    ;; Spawn the Noise netlayer, passing in the TCP+TLS netlayer
    (define noise-netlayer (spawn ^noise-netlayer tcp-tls-netlayer))
    ;; Spawn the MyCapN object (CapTP)
    (spawn-mycapn noise-netlayer)))
```

## The Relay netlayer

So, how does this work with the relay? Well, since we already have an
non-E2EE relay and now have seen we can compose Noise and get the properties of
both, we can simply pass in the prelay netlayer to Noise netlayer and get an
E2EE relay. Of course, we don't want to ask users of the netlayer to do
this. We'll be replacing the prelay module with a new relay module that is
always end-to-end encrypted.

While the relay design (in its non-E2EE form) isn't new to Goblins, it's
worth quickly taking a look at how the relay works. The relay itself is built on
the idea of a relay client and a relay server. On the relay server there are two
actors:

1. Controller: allows the client to steer its own relay accepting new inbound connections and making new outbound connections
2. Endpoint: which is encoded in the OCapN locator and is publicly accessible, a relay server messages this object when establishing a new connection to the peer

This makes the relay *federated*. Two OCapN peers can use different relay
servers and still communicate using OCapN between the two relay servers. When a
client wants to make an outbound connection to a peer on another relay server,
the relay can enliven the endpoint sturdyref (getting a live object) and send a
message to it.

The animation above shows the flow between two peers using federation. It starts
with two actors on two different peers, Alice (on peer A) and Bob (on peer B).
Alice has a *sturdyref* (an OCapN locator specifying an object) to Bob. Here's
how the flow works:

1. Peer A first sets itself up with the controller by registering an object a-incoming with the controller. This object can be used when establishing new connections.
2. Alice has a sturdyref to Bob but wants a a live reference to Bob that she can message, she asks her MyCapN to /enliven/ it.
3. MyCapN creates an adeliver object which faciliates the connection. It then sends a message to the relay controller with the sturdyref and adeliver object and asks the relay to make a new connection.
4. The controller extracts the endpoint object for Peer B's relay from the sturdyref and enlivens it forming a new connection between the two relays. It also spawns a new rarelay object to facilitate communication between these two peers and hands this back to adeliver.
5. The controller then sends the rarelay object to the endpoint on B's relay. B's relay then spawns its own analog to the object rbrelay.
6. Peer B's relay reaches out to the b-incoming object, allowing it to establish a new connection to Peer B. It passes along the rbrelay object.
7. Peer B's MyCapN object spawns a new bdeliver object which facilitates its connection.

This gives the two peers a connection to one another, even though neither share
a common relay server. The relay is designed to be completely stateless, i.e. it
doesn't hold on to data, configuration, or anything else.

One of the lessons we've learned since co-authoring ActivityPub is it's crucial
to reduce the impact of servers on their users. In ActivityPub, each instance (a
server) stores all the data for its users and performs all the operations their
behalf. This means the user needs to trust the server a lot, and if the user's
instance shuts down, or they simply wish to migrate, moving to another server is
difficult.

Learning from those problems, it was critical for us to make sure the server
was stateless. The relay itself stores no state/data for a user and, aside from
connecting to another peer, the only behavior it's expected to perform is
relaying messages. This makes changing relay servers incredibly easy. The user
simply needs to find another (or setup their own) relay server and include that
in their sturdy references instead.

## Future work

The work isn't done, though. Adding support to Goblins was just one part of the
NLnet grant. We'll be contributing specifications for the encrypted relay to the
[OCapN standardization group](https://ocapn.org/) so others can implement
it. Ridley, who has implemented
[OCapN in Dart](https://codeberg.org/ridley/DObjects), has already implemented
their own [Noise library](https://codeberg.org/ridley/dart_noise) in preparation
for the E2EE relay. As part of the grant work within the OCapN group, we'll also
be adding support to the [test suite](https://github.com/ocapn/ocapn-test-suite)
to allow both testing new relay implementations, and testing the rest of OCapN
over the relay.

Another milestone of the grant is to implement a Guix service to make it easy to
run an instance of the relay. The relay doesn't take many resources to run and
it has very few dependencies, so it should be easy for others to package for
their distributions and run on the cheapest VPS or old computers users might
have around their home. We are looking forward to the deployment of a vast
network of OCapN relays.

## Thanks to our supporters

Your support makes our work possible!  If you like what we do, please
consider [becoming a Spritely supporter today](https://spritely.institute/donate)!
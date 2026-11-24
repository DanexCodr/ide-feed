*In the past year, we have been significantly improving the reliability and
correctness of Aerogramme's IMAP implementation. This is the second part in a
series discussing why implementing IMAP correctly is not so easy, and presenting
our work on making Aerogramme's IMAP code as high-quality as we can.
Today we focus on challenges that arise when considering concurrent
access to a mailbox.*

*[Aerogramme](https://aerogramme.deuxfleurs.fr/) is an experimental email server
(& calendar, contacts), designed to be geo-distributed, hosted outside of
datacenters, on refurbished hardware, and reliable even in presence of network
issues and hardware failures. It is built on top of
[Garage](https://garagehq.deuxfleurs.fr/) and shares the same philosophy.
Aerogramme is AI-free: we do not wish to use unethical technology and prefer to
spend effort on careful craftmanship and community-building.*

This is the second post in a series in which we argue that *implementing an IMAP
server is not easy*, essentially due to two classes of features that are fundamentally
challenging to implement. [In the previous
post](https://aerogramme.deuxfleurs.fr/blog/2026-quality-imap-part-1/), we talked about the first class of
features: fine-grained retrieval and querying of email contents. In this post,
we talk about the second class of features that make implementing an IMAP server
tricky: **concurrent access to user mailboxes**.

Concurrent and distributed software are famously hard to get right; concurrency
bugs are known to be hard to find. In our recent work on refining Aerogramme we
have tried to approach the problem from different angles. This is the topic of
this post: the different ways in which we have improved the **correctness of
Aerogramme in concurrent settings**.

*This work was funded by [NLNet](https://nlnet.nl) under the "[Aerogramme
1.0](https://nlnet.nl/project/Aerogramme-1.0/)" grant, and could not have been
possible without their support.*

*Feel free to join the Aerogramme [matrix
channel](https://matrix.to/#/#aerogramme:deuxfleurs.fr) for updates or if you
just want to chat!*

# Concurrent mailbox access in IMAP

A core feature of IMAP is that multiple email clients can simultaneously access
the same mailbox. For example, we may want to access our emails both from our
phone and our computer. Concurrent access to a mailbox can also happen when a
single client is involved: some clients (including Thunderbird) *open multiple
concurrent connections to a same mailbox* to speed up processing. In any
case, clients accessing the same mailbox should be able to coordinate between
themselves and avoid stepping on each other's toes.

*Why must clients be able to coordinate when accessing the same mailbox?* Assume
that we are an email client that sends two commands to read information from a
mailbox. Since another client can modify the mailbox in between the two
commands, the information we read may have been invalidated by the other client
and is now inconsistent! *Clients thus need to be able to detect concurrent
changes made by other clients*. Similarly, a client that reconnects to the
server after being offline needs to fetch the changes that happened while it was
disconnected. This is possible thanks to mechanisms defined by the IMAP
specification and that specifically exist because concurrent access is allowed.

The overall consistency of the mailbox data must be taken
seriously: an IMAP server exposing inconsistent views of a mailbox could result
in a confused client deleting the wrong emails, for example.

To our best knowledge, concurrent mailbox behaviors are tackled in the following
(parts of) specifications:

### Base IMAP

The [base IMAP4 specification](https://datatracker.ietf.org/doc/html/rfc3501)
has few explicit mentions of concurrent mailbox access, but does talk about
re-synchronizing disconnected clients, which can be seen as a restricted form of
concurrent access. It defines mechanisms for assigning IDs to emails
(`UIDNEXT`/`UIDVALIDITY`) and associated properties which can be extrapolated to
concurrent contexts. This is relevant when **concurrently adding new emails** to
a mailbox. After an email has been added to a mailbox *it cannot be modified*,
so there are no issues with reading emails concurrently.

The improvements that we will talk about in this post are related to these
aspects of the base IMAP specification.

As an additional complication, IMAP defines in fact two (!) email-numbering
systems. One of these has the drawback that **deleting an email can invalidate
email IDs used in concurrent commands**. This is purely a quirk of a numbering
system that can nowadays be considered legacy, but must still be supported. This
issue is not acknowledged in the base IMAP specification, leaving a class of
problematic behaviors completely unspecified, but is later addressed in an
[informational RFC](https://datatracker.ietf.org/doc/html/rfc2180) which
specifies what to do in such cases.

Aerogramme's latest release includes changes and bugfixes to make sure that we
follow the recommendations of this informational RFC, but we won't enter into
the details of these legacy quirks in this post.

### Extensions

**Email flags can be modified concurrently**, but the base IMAP specification
does not specify a mechanism for clients to coordinate around flag changes. This
is done in the later [CONDSTORE
specification](https://datatracker.ietf.org/doc/html/rfc4551) that extends IMAP
with mechanisms to coordinate flag changes across concurrent connections.
Aerogramme has preliminary support for CONDSTORE, but we disabled it in the last
release, as we found out it needs a redesign to be nicer to email clients<sup>[1](https://aerogramme.deuxfleurs.fr/blog/2026-quality-imap-part-2/#condstore)</sup>.

A [later specification](https://datatracker.ietf.org/doc/html/rfc7162) further
extends IMAP and CONDSTORE by adding a more general mechanism (QRESYNC) for
**synchronizing all mailbox changes** across concurrent sessions. Aerogramme
does not supports QRESYNC at the moment<sup>[2](https://aerogramme.deuxfleurs.fr/blog/2026-quality-imap-part-2/#qresync-support)</sup>.

# Context: Concurrency in Aerogramme

On top of the complexity carried by the IMAP specification, Aerogramme's
distributed infrastructure comes with its own challenges. Not only we need to
think about concurrency at the IMAP protocol level, but also *internally in
Aerogramme*: how do we handle concurrent changes to the server internal data
storage? Can we simply take a lock or a transaction over mailbox data each time
we need to update it, serializing all concurrent updates? The answer is no:
things are a bit more complicated...

Recall that Aerogramme is a *distributed* IMAP server. A typical Aerogramme
deployment looks like this:

![Diagram of an Aerogramme+Garage deployment. Client nodes connect to the Aerogramme cluster, which contains several Aerogramme nodes, that all connect to a Garage cluster, itself containing several Garage nodes.](https://aerogramme.deuxfleurs.fr/images/cluster.jpg)

In this schema, `A` nodes are Aerogramme instances running on separate servers.
Running multiple Aerogramme nodes provides fault-tolerance: even if some of the
nodes crash, the Aerogramme cluster stays operational as long as one node
remains available. When an email client (a `C` node) connects to the "Aerogramme
cluster" (the dashed potato), it can open a connection to any of the Aerogramme
nodes, depending on what kind of load-balancing is implemented.

Aerogramme nodes do not talk to each other directly and do not store data
themselves. Instead, they connect a shared Garage cluster (itself
geo-distributed with fault-tolerance properties) which stores data for the whole
Aerogramme cluster (emails, mailbox state, etc.).

This means that an Aerogramme node deals with concurrency at two levels. It must
handle **concurrent connections from email clients** to a mailbox, as we
explained before. But it must also handle **concurrent changes made by other
Aerogramme nodes to the data stored in Garage**. These concurrent accesses must
be coordinated properly so that the Aerogramme cluster exposes **a consistent
view of a mailbox** (according to IMAP's consistency requirements), even when
connecting concurrently to different nodes of the Aerogramme cluster.

A central challenge in Aerogramme's design is that Garage *does not provide
locks*, transactions, or anything that would require distributed consensus
between Garage nodes. This is by design, and it allows Garage and Aerogramme to
perform well even with non-negligible latency between nodes. The consequence for
Aerogramme is that its nodes cannot simply reason on their shared data as if it
was updated sequentially. The approach used by Aerogramme instead—a convergent
operation log—is a central part of its design. We'll talk more below on how we
adjusted the consistency properties provided by Garage when storing that
operation log.

# Testing the consistency of email numbering in Aerogramme

A basic IMAP mechanism is assigning
IDs to emails when they are added into a mailbox. Adding emails concurrently
can already make it tricky to assign these IDs. Our first step was to
find a way of testing this case and to fix any bugs that we would
find.

For context, IMAP specifies that each email in a mailbox must be assigned a UID:
a number that identifies it uniquely. UIDs are assigned in increasing order;
this allows clients to check if new emails have been added by checking the value
of the mailbox "next UID". On top of that, IMAP also allows the server to
*renumber the emails* with different UIDs. When this happens, the IMAP server
must increase the value of `UIDVALIDITY`, a global integer counter attached to
the mailbox. Now, in Aerogramme, increasing `UIDVALIDITY` is done in some cases
when emails are added concurrently in the mailbox in a way that would assign
conflicting UIDs; an unavoidable consequence of its distributed architecture.

From an IMAP client's perspective **`UIDVALIDITY` must always increase monotonically**. We
also assume that this property must hold **across all concurrent connections**;
although the specification does not say so explicitly, it is the most prudent
assumption since a single client may open multiple connections to the same mailbox.

The logical next step is to setup a
[test bench](https://git.deuxfleurs.fr/Armael/aerogramme-test-monouidvalidity)
to ensure that it holds in practice for Aerogramme! We deployed an
Aerogramme cluster with three nodes, running on a simulated network with added
latency between nodes. Then:

- we run two processes concurrently adding emails to a test mailbox, from two different nodes of the cluster. This is enough to trigger UID assignation conflicts, forcing Aerogramme to renumber emails and increase UIDVALIDITY;
- at the same time, we run a checker for our property: a program that reads UIDVALIDITY from two different nodes of the cluster and checks that the second value read is greater or equal to the first one.

Running Aerogramme on this test bench found *state synchronization bugs*: bugs
showing that Aerogramme’s distributed state (stored in Garage) was not always
properly synchronized between nodes and concurrent sessions. Amusingly, most of
these bugs were not specific to the IMAP logic related to `UIDVALIDITY`...

Fixing these synchronization bugs motivated a redesign
of the internal read/update mailbox interface.
In Aerogramme, the IMAP "business logic" accesses mailbox state stored
in distributed storage using an abstract interface exposing a small number of
operations. Before, these operations were the following (in pseudo-Rust):

```rust
// `self` is a handle to the storage backend for a mailbox.

/// Read the current state of the mailbox from remote storage.
fn get(&self) -> State

/// Push an operation that updates the mailbox to remote storage.
fn push_op(&self, op: Operation)
```

The synchronization bugs found during testing revealed that this interface is
in fact error-prone and tricky to reason about:

1. get could return outdated values; this is because rebuilding mailbox state from remote storage can be expensive, so get internally maintained a cache which could get stale;
2. doing let s1 = mailbox.get(); ...; let s2 = mailbox.get(); is a trap. In this case, s2 imports unknown operations pushed concurrently from other clients. In most cases this is not what we want, as IMAP commands must generally behave as if they operated on a "snapshot" of the mailbox taken as a single point in time;
3. push_op modifies the state, but if we need the mailbox state with the operation we just pushed, we have to call get (and thus likely fall into the trap described in 2.).

The solution was to redesign Aerogramme's mailbox state interface to provide
more control over state synchronization: reading concurrent changes from storage
becomes a separate operation, laying the following interface:

```rust
// `self` is now a thread-local view of the state of a mailbox.
// It is local to a given client connection.
// (As an optimization, it internally pools ressources with other
// views of the same mailbox.)

/// Return the local view of the mailbox maintained by `self`.
/// Does not read remote storage.
fn get(&self) -> State

/// Push an operation that updates the mailbox.
/// Update both the local view and remote storage.
fn push_op(&mut self, op: Operation)

/// Synchronize the local view of the mailbox.
/// Read remote storage and imports all changes into the local view. 
fn sync(&mut self)
```

This new interface separates local reasoning about mailbox contents from
synchronization. This makes it easier to write the IMAP logic in a way that is
"obviously correct". Plainly speaking, this interface provides "local" views of
mailbox state, where a view (denoted as `self` above) is specific to a client
connection. Then, `get` and `push_op` operate on the local view with sequential
semantics and are both fast; and calls to `sync` mark explicitly the places in
the code where we have to think about concurrent changes. (Note that `push_op`
synchronously updates remote storage, so there is no risk of losing write by
forgetting to run `sync`.)

Notice that the design of this interface reflects the high-level distributed
architecture that we described in the previous section. For instance, an
implementation of the interface needs to "merge" the operations pushed
concurrently with `push_op` when they are put together in distributed storage,
in a way that is consistent with local views; this is backed by the "convergent
operation log" mentioned earlier and domain-specific logic<sup>[3](https://aerogramme.deuxfleurs.fr/blog/2026-quality-imap-part-2/#syncmergelogic)</sup>.
Note that this interface offers no transactional or lock-like operations;
matching Garage's lack of consistency primitives.

Most of the changes described here were part of [Aerogramme
0.4](https://git.deuxfleurs.fr/Deuxfleurs/aerogramme/releases/tag/0.4.0), with
in particular [#129](https://git.deuxfleurs.fr/Deuxfleurs/aerogramme/pulls/129)
implementing the refactoring of the state synchronization interface.

# "Monotonic Reads" Consistency for Garage K2V

Talking about consistency guarantees in Aerogramme raises the question: what are
the consistency guarantees provided by Garage, its storage backend?

This question is most relevant for [Garage
K2V](https://garagehq.deuxfleurs.fr/documentation/reference-manual/features/#k2v-api-experimental),
a NoSQL-inspired key-value store, which is used to store mailbox state as an
operation log. (Garage K2V is experimental and was added in Garage for
the needs of Aerogramme.) Mailbox state describes (among other things) email
numbering, and as we've seen before, we want this information to be properly
synchronized between Aerogramme nodes.

Garage K2V provides **read-after-write consistency**<sup>[4](https://aerogramme.deuxfleurs.fr/blog/2026-quality-imap-part-2/#k2v-raw)</sup>: this guarantees
that as soon as a write is acknowledged by Garage, any subsequent read will
see the update made by the write. In terms of Aerogramme's state synchronization
interface, after running `push_op(op);`, this guarantees that `sync(); get()`
returns a state that includes `op` *on any Aerogramme node*.

However, it turns out that *read-after-write consistency alone is not enough for
Aerogramme*. Let's think of the fact that `UIDVALIDITY` needs to increase
monotonically according to the IMAP specification. This means that calling
`sync(); get()` twice *on any two Aerogramme nodes* must return a state that is
*more recent* the second time than the first. In other words, when making
several reads to Garage K2V in sequence, we must not see time go backward. This
means that, to ensure consistency of the `UIDVALIDITY` counter, Aerogramme needs
Garage K2V to guarantee an additional consistency property called **monotonic
reads**!

As a result **we have extended Garage K2V to provide monotonic reads consistency**. Luckily,
the design of Garage makes it possible to provide monotonic reads at only a
small performance cost. For a reference, Martin Kleppmann's *Designing
data-intensive applications* (in particular Chapter 9, "Linearizability and
quorums") helps understanding which scenarios lead to non-monotonic reads in a
quorum-based architecture like Garage's, and what to implement to guarantee
monotonic reads.

To experimentally validate our changes, we first built a [test bench that
triggers non-monotonic
reads](https://git.deuxfleurs.fr/Armael/garage-test-monoread) on stock K2V.
Reproducing non-monotonic reads requires variable network delays, so we deployed
a Garage cluster with 3 nodes, on a simulated network with delay between cluster
nodes. This test setup allows observing non-monotonic reads, by running:

- a writer program that writes increasing integer values (0, 1, 2, etc.);
- a reader program that performs two reads in sequence from two different nodes of the cluster, and checks that it reads an integer that is greater on the second read than on the first read.

We then [modified Garage K2V to provide monotonic reads by
default](https://git.deuxfleurs.fr/Deuxfleurs/garage/pulls/1452), by
implementing "synchronous read repair". We validated that we cannot observe
non-monotonic reads anymore on our test bench, while they could be observed
before this change: a good sanity check.

This change in Garage K2V ensures that there are no scenarios in which a precise
combination of network delays in the cluster results in an IMAP client observing
non-increasing values of `UIDVALIDITY`. One could argue that this is unlikely to
happen in practice; and indeed, we could not reproduce it with our simple-minded
test bench: while we could observe non-monotonic reads with Garage K2V alone, we
could not observe non-monotonic `UIDVALIDITY` on a full Garage+Aerogramme
deployment with the same testing methodology. Nevertheless, **we want Aerogramme
to rest on strong, correct foundations** as much as possible; eliminating a
*rare but possible* cause of bugs was fully worth the effort.

The work described here was made available as part of [Garage
2.4.0](https://git.deuxfleurs.fr/Deuxfleurs/garage/releases/tag/v2.4.0); it
required no specific change in Aerogramme itself.

We designed Aerogramme to be part of a *low-tech
computing stack* meant to be robust and reliable when hosted outside of
data-centers, and Aerogramme's geo-distributed design is part of the answer. In
the future, we hope to expand on the values and high-level ideas behind
Aerogramme; this will have to be for an other blogpost...

The current implementation (now gated by a feature flag disabled by default) tends to disconnect clients more often than reasonable. This is correct with respect to the specification, but likely leads to bad UX in clients. We are working on a better strategy that does not require disconnecting clients.

The first step would be to gather data on how many clients actually support QRESYNC today...

We have not shown this "domain specific" merge logic (here, mailbox-specific) because it is a whole different topic, but it needs to be provided when instantiating the generic interface shown before with concrete state and operations.

read-after-write consistency is also the key consistency guarantee provided by Garage S3.
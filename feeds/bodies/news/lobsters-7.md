I return with part two of the replication rants series.  This talk was given at HPTS'26 and fleshes out the argument for quorum-based replication in [Enough With All The Raft](https://transactional.blog/talk/enough-with-all-the-raft.html), and continues to build off of the work that went into writing [Data Replication Design Spectrum](https://transactional.blog/blog/2024-data-replication-design-spectrum.html).

I think we tend to view quorum replication as generally impractical for production use.

I think that is an outdated view.

## Video

If you want the links to papers, find the corresponding slide below.

## Transcript

This is a replication talk that I gave at HPTS 2026.

I once did a survey of what type of replication algorithm databases in production are using, and the result looks like this.
Raft is the giant pacman, eating the primary-backup and quorum slices.
The Quorum slice is small enough that we can just fully enumerate it right now.

Upper left are OSS majority quorum databases.  

Upper right are proprietary ones that used or are using it for data replication.  

Bottom left are proprietary ones using consensus for a log.  

Bottom right are technically true but carry caveats.

If we filter that list by how they’re doing now:

- Riak is long past hedge fund dead.
- Voldemort is so dead all that all of you forgot it existed until the previous slide.
- InfluxDB and Grafana Mimir had previous iterations which used quorums, and then they re-architected.
- Weviate does quorum for data and raft for metadata, and I won’t be shocked if they re-architected too.
- Google Megastore is basically dead.
- Tencent PaxosStore is super internal in chinese bigtech, so I have no idea.
- CouchDB was more meant for eventual consistency but has a clustered mode, and I have no idea who uses it other than cloudant?
- OG Dynamo, which someone here can tell me about, but I’m assuming is/has been phased out?

*Note: the HPTS audience head shaking agreed with my assessment of Dynamo.*

Which leaves me with this awkward feeling that if I say implement a quorum database, the only good example I have to point to is Cassandra?!?

HPTS says submit your spicy takes, so brace yourself:  I think we should be credibly building more than one good example of a quorum database.

Which we are!  I’m holding out 3 very recent examples on you.

But first, for the next 16 minutes I will be CEO and utterly delusional founder of CashDB, because I need a running example for this talk.
CashDB is a database specialized for whatever your splitting-the-bill-with-friends app that you use.

It has two major limitations.

First, it only supports a very limited set of operations:

1. debit account X, add to account(s) Y
2. Read account value(s)

1. Add a receipt to the group log
2. Read group transaction log

The second constraint is that I told a coding agent to make CashDB as reliable as possible and now it has my AWS keys, is rebooting one of my VMs once a minute in the name of chaos testing, and has replicated itself.  I cannot stop it.  We must now design CashDB around this.  I need a replicated CashDB.

If I use a reconfiguration-based replication protocol that does a view change on every failure, my users are going to see latency spikes every minute and I will have to answer uncomfortable questions.

If I use raft, then expected value is that they see a latency spike every five minutes when the leader is affected, but the other failures get masked.

This is perfect.

This is the motivation I’m pitching for being leaderless.  You should get better latency,

I’m not saying availability, because availability is just a latency SLO.

So, what if we try to build CashDB in the style of our long-established examples?

First we have everything that came out of the ABD paper doing standard majority quorums.

Think OG cassandra.  We get a nice 1 or 2 RTT writes.  We get 1-2 RTT reads.  Life is great.

CAN. IT. CASHDB???

No.

It implements only distributed read/write register, thus the implicit atomic read-modify-write for account debit/credit operations doesn’t work.
Append to transaction log would also be a struggle.

I think we view majority quorums slightly worse than it deserves because it came from the eventual consistency era read repair + LWW + anti-entropy gives a lot of opportunities to resurrect failed writes.

But, unless you very knowingly fit the register model with linearizable-but-sujectively-worse consistency, I do not think majority quorums are the path forward.

Let us instead consider if building a system like Megastore would work.

Megastore replicates a log per entity group, and a proposer targets the next available slot in the log with its proposal. This is just multi-paxos without the time-based leader election.
Consensus gives us State Machine Replication, and thus we can model debits and credits as increments and decrements, and log appends as appends.  That’s great.

CAN. IT. CASHDB???

Yes, but it will explode in production.

It will fail because of latency. Paxos has a liveness problem: two duelling proposers can easily prevent eachothers' progress.  The log-centric model only helps to funnel proposers into conflict.

Both systems tried a way to solve this:

- Megastore optimization: if you commit to slot N, you’re automatically the "leader" for slot N+1.
- PaxosStore: time-based exclusion for a log slot once you hear a proposal for it (also geographic closeness).

Neither really fundamentally saved them.

However, it’s nice that replica catchup is easy because there’s one log with one ordering to replicate, and one can easily describe a snapshot of data by just the log offset.  But, the latency spikes worse than leader election timeouts removes the motivation for using quorums in the first place.

What if we built CashDB using some E-Paxos ideas?

Egalitarian Paxos introduces doing consensus where one agrees upon an order only for the exactly necessary dependencies.  This naively results in a sparse, potentially disconnected, graph of operations.  This graph frees us from having the One Big Log causing unnecessary contention.  The closest that E-Paxos gives to any hint on how to do replica catchup is something that looks very much like [Cassandra Enhancement Proposal 45 Mutation Tracking](https://cwiki.apache.org/confluence/spaces/CASSANDRA/pages/337676893/CEP-45+Mutation+Tracking) if you squint at it.

Our almost production example comes from Cassandra again.  There’s an old 50k line un-merged patch which gives Lightweight Transactions an overhaul onto a new E-Paxos implementation.

CAN. IT. CASHDB???

Also No

It’s not clearly better or worse than a log here…​

E-Paxos also was noted to have a huge latency cliff under contention, which again ruins our latency desires. There’s actually [an infinite tail latency theoretical result](https://arxiv.org/abs/2008.02512) for this.

E-Paxos doesn’t give any great way to define a snapshot other than commit a dependency on everything.

Cassandra’s EPaxos already had anti-entropy and so they had a paxos repair that ran every 5min to fix up lost proposals.  It still benchmarked better than LWT though.

For things that have a good history in production, that’s it.  It doesn’t seem great.

From looking at what pieces were good and bad, we can put together the missing feature wishlist for leaderless replication:

We need to survive contention because we cannot have latency climb incredulously as contention increases.  We desire quorums for low latency.  If there’s an easy trap that causes concerningly high latency, then we might as well use Raft.

Consistent local snapshots would be nice. If you need to do a quorum read and merge for a table scan while executing SQL, you’re going to lose tremendously to a system which doesn’t.  We need *some* way to define a consistent snapshot locally.

Lastly, If a node has missed proposals, catching up (to get to a snapshot) should be O(missed work) and not O(total data).

So let’s do another pass, and now look at some very recent approaches instead.

If we look back at consensus over logs, the thing we need to fix is the latency under contention.  How can we do that?

SOSP'23 had a paper on QuePaxa.  QuePaxa gives us leaderless consensus that offers much better bounded latency under contention. Proposers collaborate instead of conflict. Consensus will take somewhere from 1 to 7RTT.  But you’re unlikely to go over 7RTT.

QuePaxa in 60 seconds:

- Every proposal gets a priority value, priority equals value for sake of diagram simplicity.
- The algorithm proceeds with proposers walking in lockstep through phases across the acceptors.
- If you fall off the lockstep bandwagon, you can get back on with some other valid proposer’s state.
- Phase 1 only records the first proposal it hears.
- From then on there is a fixed number of proposals, and the consensus intuition is:
- I define a phase as "read from a quorum of phase N and write the max priority proposal to a quorum to begin phase N+1", if I repeat that enough times, everyone should eventually become aware of the best proposal.

Actual algorithm, more complicated.

You can replace paxos in a megastore-style system with QuePaxa.

QuePaxa’s 1RTT fastpath comes from a spiritually similar Megastore optimization where winning round N gives you an ability to do a 1RTT commit to round N+1.

CAN. IT. CASHDB???

Not yet

I’m nearly certain some of those 7RTT cases can be trimmed down.  Superficially, pipelining isn’t discussed, and so getting good throughput seems hard.  QuePaxa needs like 5 more optimization papers, and then it’s very worth revisiting.

*Note: I had received a question about the jump from E-Paxos to QuePaxa, and what QuePaxa was trying to solve.  The intended comparison is mostly just Megastore to QuePaxa, and I think the chance of you regretting putting Megastore into production is much higher than the chance of you regretting putting QuePaxa (+ Optimizations) into production.*

[Cloudflare is working on pushing QuePaxa into production](https://blog.cloudflare.com/meerkat-introduction/), and so I hope they’ll also do a lot of that needed optimization work.  I highly look forward to their results.

If we look back at consensus over graphs, we need to fix…​ everything.  Which sounds hard, but we actually have two great examples here.

SIGMOD'26 gave us Neo4J doing a very graph-centric leaderless consensus protocol.

*Note: Jim Webber was at HPTS'26 and came up to say hello after this talk.  He is a very nice person, and it was really cool to get to meet him.*

RIOT builds a DAG where each transaction is a node, and the current snapshot is defined as the set of nodes with no parents, the “Leading Edge”.
Nodes gain a dependency when they conflict, or have a time ordering.

Do one transaction on a snapshot?

Add yourself as a node with the snapshot as your parents.
You are now the leading edge.

Do many concurrent transactions?

Each node becomes a new part of the "leading edge".

And RIOT is centered around the leading edge.
Transactions are committed when a quorum accepts a new node into the transaction graph, and that’s sent with a leading edge.
If you hear about a node you don’t know about from another replica, you get caught up on it, and all its parents you don’t know about.
RIOT tells us you can do DAG replication by keeping our DAGs connected, and keep them tall and narrow.

CAN. IT. CASHDB???

Probably?

Their results show…​ it’s like, pretty okay at low-ish concurrency: 300txn/partition/second.
And that’s fine for neo4j usage, and they have production stats that justify that the tradeoffs in RIOT match their production usage well, which is really all I want to see when picking a replication algorithm.

It’s just not an amazing fit for CashDB.  CashDB would do lots of small transactions.  RIOT happens better for fewer and larger transactions.  It’s a super cool paper either way. it’s the only thing I’ve seen that answers how to do pure DAG replication like this well, and it gave Neo4J lower latency than their Raft implementation.

Our second system to examine is, you won’t believe it, but it’s Cassandra again, because we can’t stop talking about Cassandra in every part of this talk.  CEP-15 introduces Accord, which is an E-Paxos style protocol.

Its closest direct relative is the tempo paper, but accord does physical timestamps instead of logical timestamps.

Accord provides a 1RTT fast path.  It takes up to 3RTT in the slowest case.
It borrows the ordered broadcast optimization from E-Paxos Revisited, which means you’ll end up on the fast path more often

It collects agreement on what timestamp to execute a transaction at, such that the timestamp is after all of its dependencies.  The same epaxos-like logic applies for dependency collection, but, the reliance on the timestamp stability work dodges the e-paxos infinite tail latency theoretical result.

Timestamp ordered execution linearizes proposals which gives it an easy way to support consistent local snapshots and incremental replica catch-up.

CAN. IT. CASHDB???

Hell yeah, huge Accord fan.

CashDB would be only small OLTP transactions. It doesn’t need interactivity. You would have to commit a debit/credit, and then execute it and find out if it was valid or not as like a durable OCC, but that’s not the worst.

I like Accord a lot and think you should read about it.

And I wanted to take an extra quick moment to highlight that epaxos revisited ordered broadcast primitive.

The difficult part of leaderless consensus is agreeing upon ordering.  Leaders are great at ordering!
Wouldn’t it be great if everything could just be ordered upon arrival?

Client generated timestamps.  Make up your order on your client, broadcast it with your message.
Variants of this idea show up in papers *often*.

What if you process messages only on or after their deadline?

What if you also drop out-of-order messages?

What if the network provides best effort ordering?

What if it’s byzantine?

What if it’s a transaction timestamp?

No details for time, and we’re ending on TAPIR so I can mention System #3 that I *think* SurrealDB is putting TAPIR into production which is pretty cool.

Our last bag of tricks are a few very related ideas because applying any one of them, gives you the same high level architecture.

There’s a cloud of unordered commutative operations from which you pull a log out of afterwards with some great-at-ordering leadered consensus.
You can do a 1RTT quorum write into the unordered pool, and remember that  [Linearizable Quorum Reads](https://scholar.google.com/scholar?cluster=10098760952745259234) says you can do a 1RTT read from a quorum of non-leaders, so you’re left only stalling read-after-writes.

CURP is a really nice introduction to this idea, and hides a description of how to apply it to raft in the appendix

It was then later generalized to work on more consensus algorithms and fixed in Jetpack

Both stop at defining “commutative” operations as those that affect two different keys.
Pulling this diagram from CURP, they accepted a quorum write to Y and to Z, but another write to Y would be forced to stall while the leader works on propagating Y into the log.

CURP almost got a production implementation in {uri-cncn-xline}[CNCF Xline], but they went straight from Beta to Archived.

To take these ideas one step further, you need the Skyros paper introducing Nil-Externality.

Nil-externality is a generalization of blind writes to all operations that don’t return any state about the system.
Skyros lets you just keep quorum writing nil-external operations to the same key.
Each replica remembers its local order, and a leadered consensus can pull back out a correct linearizable order later.

Nil-Externality has no *direct* implementation in industry, but we’ve been doing similar logic on the concurrency control side by not checking conflicts between blind writes in serializable MVCC databases for a long time.

Skyros tacks on commutative operations like increments but doesn’t discuss it much.

I’ll give MDCC credit as the other paper I know of which directly took on commutative updates under a leaderless generalized paxos model

and 1986 Escrow transactions let you extend that commutative logic to …​ almost commutative operations.

Escrow says: let increments and decrements commute as long as it’s impossible for your constraint to be violated.  If in the absolute worst case where all the increments abort, and all decrements succeed, then the value still remains above 0, then what do you care just treat them all as commutative.

Escrow has only one implementation I’m aware of, Oracle 23c introduced it under the name “lockfree reservations”, but, Oracle is not a quorum database

To apply this to quorum systems, you need the 1992 paper: High Throughput Escrow Algorithms for Replicated Databases
which tells you that in the standard 3 of 5 quorum setup, the worst case value needs to stay above 40% of the current account value instead of 0. It’s not a terribly hard fix.

So if we squish all these ideas together…​

CAN. IT. CASHDB???

Yes.

CashDB only supports an escrow-able account transfer operation and a nil-external log append.  I obviously designed CashDB for this argument.
In isolation this async leader trick is not 100% leaderless, but I include it because it’s a great step towards better latency.

I’m also mentioning it because leveraging blind and commutative operations makes EVERY OTHER ALGORITHM BETTER and we never do it.
In Consensus over Logs, Nil-Externality and Escrow would help guide us as to what operations are safe to pipeline with a leaderless log.
In Consensus over Graphs, it means we get to reduce the dependencies tracked, and thus end up on the fast path more often.

Increments are the best operation ever because you can treat them as commutative OR a nil-external fused together read-modify-write that returns nothing, and we still basically never special case them?!? We just execute them under exclusive locks, it saddens me.

Alright, I’m out of time and out of content, so:

- We have very recently gotten much better algorithms for leaderless replication
- We have very recently gotten much better production-or-almost-there examples of how to write good quorum databases.
- There are still more good ideas we have yet to apply to their full extent.

I do not think we will see a proliferation of quorum databases until we have good production examples to copy from.

So I implore you.  Choose something different.  Choose something with better latency.
Choose something that lets you drop a "why quorums are better" blog post every time your competitor has an outage.

Thank you.

See discussion of this page on
      [Reddit](https://www.reddit.com/search/?q=url%3Atransactional.blog/talk/please-implement-a-quorum-database),
      [Hacker News](https://hn.algolia.com/?query=transactional.blog/talk/please-implement-a-quorum-database), and
      [Lobsters](https://lobste.rs/search?q=domain%3Atransactional.blog+title%3A%22Please Implement A Quorum Database%22&what=stories).
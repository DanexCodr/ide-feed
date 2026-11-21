Before we dive deeper, let's do a quick recap on Enroute's architecture. Enroute separates compute from storage, like many modern databases. A cluster has three parts:

- Compute nodes do the compute-intensive Git work: they receive pushes, validate packs and build them into layers, and serve clones and fetches. They use fast SSDs for caching, but are otherwise ephemeral and can be scaled out easily.
- Ledger nodes keep one replicated log per repository. They require persistent disk storage. Each log tracks the respective repository's refs and the list of layers that make up its object database.
- The bucket holds the data layers themselves, as well as some amount of metadata used for coordination.

## Scaling Multi-Raft and the complexity that came with it

When thinking about how many repositories we can fit on a single Enroute cluster, there are really two numbers to consider:

1. Active repositories: Repositories that are receiving traffic, for either reads or writes (or both). How efficiently can we process requests that are made concurrently against many repositories? Are there any bottlenecks and if so, at what scale?
2. Idle repositories: On a platform with hundreds of thousands of repositories, you can expect most of them to be idle at any moment. So it's also very relevant to measure and improve the overhead each idle repository adds, both in terms of work (I/O and CPU) as well as resources (disk space and memory footprint).

While we had implemented some early optimizations already, two measurements showed where we still fell short:

- Between compute and ledger: following repositories. When starting to push from 8,000 towards 32,000 active repositories, tail latencies began to spike and pushes began to fail. The cause was simple: each compute node held one stream to a ledger for every repository it followed, and the streams ran out. This ended up being cheap to fix by multiplexing repository subscriptions over a fixed set of streams.
- Between ledgers: agreeing on a leader. With 2,048 concurrent writers across 100,000 repositories, heartbeats began to run late, which caused followers to start elections by the thousands. Throughput fell to about 1,500 pushes per second and the 99th percentile rose to 83 seconds. Compared to the first, this is a deeper problem rooted in how Multi-Raft works.

Every repository's log was its own state machine on a separate Raft log. Raft keeps a leader alive with heartbeats and when it fails, replaces it with an election, so every log had its own timers, votes, pre-votes and leader. With hundreds of thousands of repositories, that machinery became the workload.

It turns out that mature Multi-Raft-based systems have a well-known toolbox for this, which we began to make use of as best as possible. We allowed idle logs to go to sleep, moved liveness from each log to the node, and we woke a failed node's logs only as they were needed, to prevent kicking off thousands of leader elections at the same time when a single node fails.

These fixes worked. Together, they took the setup that had previously collapsed at 2,048 writers to about 14,000 pushes per second at 100,000 repositories with no failures.

However, taking a step back, it felt like we were just piling more complexity on top of the core Multi-Raft setup, which is already quite complex to start with. What's worse, this complexity was not only in code, but also directly translated into failure modes and edge cases.

In short, it became obvious that continuing on this path would lead to a system that would be much harder to understand and operate, which motivated us to start looking for alternatives.

## The design: an appointed sequencer instead of an election

Looking at our setup at this point, most of the complexity came from the fact that we ran membership, and by extension leadership elections, on a per-repository basis. So we began looking at ways we could take leader election out of the per-repository log.

There are a number of systems that put an external configuration master in charge of their replicas today. Among all of those, we liked Vertical Paxos (Lamport, Malkhi and Zhou, 2009) the best. The key insight behind it is that if something outside the log decides who's responsible for deciding its entries, the log itself needs no timers at all.

To apply this to Enroute, we introduced a singular "root log" that is responsible for tracking node membership per repository, while keeping the actual repository state inside each repository's log (which we'll call "shard log") and which is decided by a "sequencer" that's appointed via the root log.

On top of this, we then kept the parts from Raft that already worked well, and adopted specific pieces from Vertical Paxos.

What we keep from Raft is everything about how a log is written:

- Replication. The sequencer appends entries and sends them to the replicas the way a Raft leader does, and a replica accepts an append only if its log matches up to that point.
- The commit rule. An entry is committed once a majority holds it and it belongs to the sequencer's own term. A new sequencer starts its term with a no-op, as a Raft leader does.
- Which replicas can take over. The replica with the most up-to-date log takes over. Raft enforces this through votes, while in our system, the root log applies the same rule to the answers it collects.

What we adopt from Vertical Paxos is everything about how leadership changes:

- An external system decides, not the replicas. In Vertical Paxos a configuration master outside the group names its leader and members. Our root log plays that role in Enroute, so shard log replicas never time out or campaign.
- Fence the old before starting the new. The root log moves to a new shard log term only after a quorum of the old configuration has been sealed against the old one. That is what makes a failover safe without a lease or a clock.
- Replica changes use the same step. A change of replicas is sealed on a quorum of the old replicas, and the old ones are dropped only once the new term has committed on the new.

## The root log leader as a placement driver

In our Multi-Raft setup, every ledger node was a member of every repository's Raft group, so each log lived on all of them. That also meant adding a ledger node added a copy of every log, without any way to spread the load across more nodes.

With this new design, thanks to the root log leader being in charge of appointing sequencers, it is straightforward to extend this responsibility to placement: The root log can now decide which ledger nodes to appoint as responsible for a certain shard log, which means we can distribute the responsibility for tracking repository metadata across a larger pool of ledger nodes.

Based on this idea, the root log leader we implemented is already capable of:

- placing a new repository's three replicas in distinct zones (failure domains) first, then on the members holding the fewest logs;
- replacing a replica whose node left, and adding replicas to logs created while fewer than three nodes were up;
- moving a replica when two share a zone and a node in a missing zone is up, never moving the sequencer and moving a replica that is down first;
- spreading sequencers after a failover by preferring replicas based on who sequences the fewest shard logs.

Our plan is to extend this placement logic further in upcoming releases to improve how Enroute balances load across ledger nodes and make this process more continuous rather than purely failover-driven.

## How we checked it

Consensus protocols can be treacherous, and so a new consensus protocol naturally deserves suspicion. This is where the simpler design pays off: without an election in every log, the protocol is small enough to put under a model checker, which Raft with our fixes layered on top was not. We tested our new design in two ways.

**Model checking the code the engine runs.** The core protocol is written ("sans-IO" as the cool kids say) as a state machine without I/O: messages, proposals and clock ticks become inputs, and the pending messages and disk I/O tasks are output. This made it possible for us to use [Stateright](https://github.com/stateright/stateright) to exhaustively check the actual implementation rather than just a model, which simulates every possible interleaving of sequencers, appointments, reads, crashes and lost unsynced writes (within small bounds).

**Jepsen against real processes.** Here, our previous investment in setting up a [Jepsen](https://jepsen.io) suite paid off. It drives Git clients while it partitions, kills and pauses nodes, with every ledger on [LazyFS](https://github.com/dsrhaslab/lazyfs) to simulate disk failures, while [Elle](https://github.com/jepsen-io/elle) checks ref reads for strict serializability. While working on our new consensus engine, it found two smaller non-safety-critical bugs not in the engine itself, but in how it integrated with the rest of the system (which is why the Stateright model checks didn't pick it up earlier). Luckily, both were easy to fix.

## What the numbers show

To find out how well these improvements worked, we tested our old implementation (0.3.0) against the new shard log based one (0.4.0), and grew each cluster in steps up to 100,000 repositories, and 0.4.0 on to 300,000.

Two results stand out:

1. Activity can spread across every repository. With 100,000 repositories hosted, we kept the push rate at 500 per second and spread it across more and more of them. At 32,000 active repositories, 0.3.0's p99 push time was 117 seconds. 0.4.0 took pushes across all 100,000 with a p99 of 47 ms. That is the follow stream fix from above at work.
2. It holds at 300,000, with room to spare. 0.4.0 created all 300,000 repositories without a failed create, at 749 to 2,000 per second, where 0.3.0 managed 312 to 952. With 300,000 repositories in place, we have measured up to 24,000 pushes per second on 0.4, and the ledger nodes used only about 2.5 of their 4 cores.

The real win however doesn't even show in these numbers: Enroute's consensus layer now has far fewer moving parts, which makes it much easier to understand, operate and extend in the future as we continue our scaling journey.

## Where we'll push this next

With the newly won headroom on the ledger tier, here are the directions we're thinking of taking it next:

- A continuous placement driver based on a policy. The controller can already move any log in theory, but it only does so during failover. Next step is to make this a continuous optimization process: moving logs onto nodes with spare capacity and moving sequencers off busy nodes, with sensible thresholds and rate limits.
- Root log learners. Today every ledger node is a voter in the root log. As clusters grow, we plan to keep three or five voters spread across zones and make the rest learners, so root commits stay cheap however many nodes there are. For the largest clusters, the root log could even move to a node type of its own.
- Point-in-time restore. However unlikely, losing two of a log's three replicas means manually restoring from volume snapshots today. We are planning to ship ledger changes into S3 continuously so full clusters or selected repositories can be restored to any moment within a retention window.
- Compute, the next bottleneck. Past 300,000 repositories, the next limit is compute again. You can already put a consistent-hashing router in front of the compute nodes, but we think Enroute can do better by routing internally, so that each compute node follows and caches only its share of repositories.
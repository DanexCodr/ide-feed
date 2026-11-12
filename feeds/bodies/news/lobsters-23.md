When developers explain what happens when two computers communicate, there's a very high chance Alice and Bob get involved, and I'm not going to break tradition.

Once upon a time there was a boy called Bob and a girl called Alice. Their school gives them a literature homework assignment, and since they live too far from each other to meet up, they decide to do it in Notion, a collaborative document tool. Now both of them are editing the same document at the same time. So far it says "That flower", and Alice adds "is pretty" to the end of it.

Just before Alice's edit reaches him, Bob's internet connection drops, and he doesn't notice. A few minutes later, still unaware of her edit, he types "shall I pick it?" in the same spot. Then his connection comes back, and his edit finally syncs.

Now Notion has a big problem: it has to figure out what the sentence says. The obvious rule is "newest timestamp wins": Bob's clock says he typed later, so "shall I pick it?" stays and "is pretty" quietly disappears, even though Bob never saw it. That is a lost update, and it's one of the central problems of **leaderless replication**, where every copy of the data accepts writes on its own and no almighty entity decides the order.

> **Before you read:** the rest of the article runs from Einstein's train to Lamport's clocks, ending at CRDTs. If you don't want the physics, skip the train and start at [Lamport's clocks](https://www.itworkslocally.dev/posts/no-effect-before-its-cause#lamport-what-if-computers-but-physics). If you want neither the physics nor the computer science history, jump straight to [what leaderless replication means](https://www.itworkslocally.dev/posts/no-effect-before-its-cause#what-leaderless-actually-means). And if leaderless replication is already familiar and you only want to know how CRDTs work, skip all of this and continue to the next article: [Part 2: how Yjs pulls this off](https://www.itworkslocally.dev/posts/yjs-internals-origins-yata-state-vectors).

So how did programmers solve it? It turns out that before computers even existed, physicists ran into this exact problem more than a century ago.

## Einstein's train: one lightning storm, two perspectives

In 1905, a 26-year-old patent clerk named Albert Einstein realised something unsettling: two events can be simultaneous for one person and not simultaneous for another, and both people are right. In 1916, he explained it with a train.

Picture a train zooming along a track. Lightning strikes both ends of it. A woman is standing on the platform, exactly halfway between the two strikes. Both flashes reach her at the same moment, so she says: "Simultaneous. Obviously."

The catch is that light doesn't add up like a thrown ball. Throw a ball forward on a moving train and someone on the platform sees it go faster, because the train's speed adds to the throw. Light travels at the same speed for everyone, moving or not.

Now the man sitting in the middle of the train. While the light is travelling, the train carries him *toward* the front flash and *away* from the rear one, so the front flash reaches him first. Both flashes travel at the same speed, and he's sitting exactly in the middle of the train. So, as far as he's concerned, the flash that reaches him first must have happened first. He says: "The front strike happened first."

So, whose perspective is correct? Both of them. There is no master clock hanging over the universe to tell either of them they're wrong. "At the same time" is not a fact about the universe. It's a fact about whoever is watching. Einstein basically invented "it depends," and programmers have been billing for it ever since, and hopefully will for the foreseeable future.

This is *exactly* the problem with comparing timestamps from two servers. Every server's clock is its own little train. Clocks drift, jump, and get corrected by NTP (the network time protocol that keeps server clocks roughly in sync) at the worst possible moment. Asking "whose edit came first?" by comparing clocks is like asking the woman on the platform and the man on the train to agree on which strike came first. Each has their own point of view, so they won't agree.

So if nobody agrees on *when*, does anyone agree on anything? Yes: cause and effect. If the first flash lit a fuse that set off the second, every observer, on any platform or any train, sees the cause before the effect. People can argue about timing all day, but an effect can never show up before its cause.

Take any event, like a firework going off. Light spreads out from it in every direction, and nothing in the universe is faster than light, with the possible exception of bad news. That growing bubble of light splits all of spacetime into three zones:

- The future. Everything the firework can still reach.
- The past. Everything that could have sent news to the firework in time.
- The elsewhere. Everything else: too far away for any news to arrive in time, in either direction. Neither event can cause or affect the other. Their news might bump into each other later, somewhere else, but they can never be cause and effect.

Quick example: two points on opposite sides of the Earth are about 12,700 km apart in a straight line through the planet, so even light needs about 42 milliseconds to connect them (and about 67 ms if it had to follow the surface, the way a cable does). Two events there one second apart could be causally linked. Ten milliseconds apart? No signal could connect them, so asking which came first has no physical answer.

Now, how computer scientists stumbled onto the same problem.

## Lamport: "what if computers, but physics?"

In 1978, Leslie Lamport looked at a network of computers and thought, "This is basically a tiny universe." Every machine was an observer with its own clock, and there was no master clock to settle arguments. His paper, "Time, Clocks, and the Ordering of Events in a Distributed System," borrows its central idea straight from special relativity.

He draws the network as a simple picture. Each computer is a vertical line, with time running along it. When one computer sends a message to another, you draw an arrow from the sender's line to the receiver's line. The arrow slants because the message takes time to travel: it leaves at one moment and lands at a later one. Messages are the light rays of this universe. They are the *only* way one machine can find out what another machine did.

Read it by following the arrows. Even though c1 sits between a1 and a2 on the page, no chain of arrows connects them, so they are concurrent, whatever any clock says.

From that picture, Lamport defined **happens-before**, and notice that it never mentions a clock.

1. they're on the same machine and A came first, or
2. A is sending a message and B is receiving it, or
3. there's a chain of those steps from A to B.

If neither happens before the other, the events are **concurrent**. They're in each other's elsewhere. Martin Kleppmann sums it up in *Designing Data-Intensive Applications*: two operations are concurrent when neither knows about the other, no matter what the clock said. Concurrency isn't about doing things at the same time. It's about being clueless at the same time.

> The physics here is an analogy, and it breaks in one place. Light has a fixed speed limit, so physics can say exactly what could have affected what. A network has no such limit. What counts is whether a message actually arrived, so two edits made an hour apart can still be concurrent if a connection dropped in between.

## Back to Alice and Bob

Now we can say exactly what went wrong during Bob's network outage. By the wall clock, Bob typed minutes after Alice. But wall-clock order is not cause-and-effect order. The key fact is this: Bob never saw "is pretty." His edit lives in Alice's elsewhere, so the two edits are concurrent. Neither came first, so neither should win just because of what a clock says.

Here's the whole drama, drawn the way Lamport would draw it. Each vertical line is a replica moving through time, and each arrow is a message.

No chain of arrows connects Alice's edit to Bob's, in either direction. They're strangers in the elsewhere. The minutes between them on the wall clock say nothing about cause and effect.

## What "leaderless" actually means

In practice, leaderless means there's no single source of truth everyone has to bow to. Every replica (each copy of the data, on each server or device) accepts writes on its own, online or offline, and the replicas swap updates afterwards. Databases like Amazon's Dynamo, Riak and Cassandra work this way, and so do many collaborative editors. Even when an editor has a sync server in the middle, it's just a messenger relaying updates, not a judge. The goal is that once every replica has received the same updates, they all hold exactly the same data.

That sounds easy until two replicas accept conflicting writes and something has to decide which came first.

## Three ways a leaderless system can handle Bob and Alice

This is the central problem of leaderless replication. When any replica can accept writes at any time, with no leader deciding the order, concurrent writes like Bob's and Alice's are guaranteed to happen, and every leaderless system has to decide what to do with them.

There are three common answers. The first trusts clocks. The other two stay on the relativity road and run on cause and effect.

- Last write wins: trust the clock and keep the newest write.
- Keep both: store concurrent writes side by side and let the application merge them.
- CRDTs: design the data so any two copies can be merged in any order and always give the same result, with no merge code to write.

### 1. Last write wins: trust the clock

Give every write a timestamp and keep the one with the latest. Cassandra does this by default. It's simple, and it's exactly the mistake Einstein and Lamport taught us to avoid. Bob's clock says "later," so "shall I pick it?" wins and "is pretty" silently disappears, even though Bob never saw it. In the worst case, if one replica's clock runs fast, its writes can beat writes that really came after them. Last write wins doesn't resolve conflicts. It hides them.

### 2. Keep both and let the application merge: the Dynamo style

This is the approach used by Amazon's Dynamo and databases like Riak. Each version of the data carries a *version vector*: a small set of counters, one per replica, recording which updates that version has already seen. If neither version has seen everything the other has, they're concurrent. The database then keeps both versions side by side (Riak calls them *siblings*) and lets the application merge them.

Story time: back in 2007, Amazon's cart had a problem, and it has documented in the Dynamo paper. Amazon wanted "add to cart" to always work, even when the network was having a bad day, so any replica could accept a write. That means two replicas can end up with different carts. One has a book. Another, which never heard about the book, has a phone. Dynamo used version vectors (it called them vector clocks) to notice that the two carts were concurrent, and it kept both. The application then merged them by taking the union: now the cart has the book and the phone. Nothing you added is ever lost. The price is that a deleted item can sometimes come back from the dead.

Read it top to bottom: the database never picks a winner. It keeps both carts as siblings, and the next write merges them.

### 3. Make the merge automatic: CRDTs

The third answer is the CRDT, short for *conflict-free replicated data type*. It's a data structure built so that replicas that have seen the same updates always end up with the same result, with nobody stepping in to decide. There are no siblings, and no merge code for you to write.

The trick is that a CRDT never stores "put this word at position 5," because position 5 means different things on different replicas once edits start flying around. Instead it relies on three ideas:

- Unique IDs. Every insert gets an ID, usually the replica's ID plus a counter. Alice's third edit might be alice:3.
- Neighbours, not positions. Each insert records what it was inserted next to rather than a numeric index. "My word goes right after bob:1" stays true no matter what else happens to the document.
- Tombstones. Deletes don't actually remove anything. They mark the item as a tombstone, so later edits that point to it still know where they belong.

For Bob and Alice, that means both words survive. Their two inserts claim the same spot, so every replica falls back on a tie-break rule they all share, something deterministic like "lower replica ID goes first." Same data plus same rule gives the same order everywhere, with no one having to coordinate. And because of how the rules are built, updates can arrive in any order, arrive twice, or arrive late, and the result doesn't change: same set of updates in, same document out.

Collaborative editing libraries like Yjs and Automerge are built on CRDTs, and Riak offers CRDT data types too.

Part 2 of this article goes deep on this third approach using Yjs, a JavaScript library for collaborative editing, because it's the one I have actual experience with. That experience comes from the work of [Tharaka Ariyarathna](https://lk.linkedin.com/in/tharaka-ariyarathna-578701184), an absolute legend, whose Notion-like collaborative editor for a customer success management (CSM) platform pulled me into this rabbit hole.

Read it here: [Part 2: how Yjs pulls this off with a handful of bytes per character](https://www.itworkslocally.dev/posts/yjs-internals-origins-yata-state-vectors).

## Bonus: a 2,500-year-old footnote on Pratītyasamutpāda

It's a mouthful (roughly: pruh-TEE-tyuh-sum-oot-PAH-duh). It's a Buddhist idea usually translated as **dependent origination**, and its shortest form goes: *when this exists, that comes to be; with the arising of this, that arises.*

I'm not a Buddhist scholar, just as I'm not a physicist, so I'm borrowing the idea very loosely. In the suttas it's mostly about how suffering arises, not about ordering database writes. Please don't send either profession after me.

Still, it rhymes with this article. Bob's and Alice's edits are concurrent because neither caused the other, so neither has to wait for the other. But some updates do depend on an earlier one. Say Bob reads "is pretty" and replies by typing "too" right after it. His insert says "put me right after `alice:3`", which is Alice's edit. If that update reaches a replica before Alice's does, the replica has nothing for it to point at. A CRDT doesn't freak out and declare the universe broken, and it doesn't guess a position either. It holds Bob's update in a queue until `alice:3` arrives, then applies it. When this exists, that comes to be; until then, the update sits patiently in the queue.

You never see a glass shatter before it falls. A CRDT works the same way: an update never takes effect before the one it depends on, however confused the clocks are. Some things come before other things because one caused the other, and no clock has to agree for that to be true.

> **To be continued:** how Yjs actually pulls this off, with origins, YATA and state vectors. [Read Part 2: Yjs Internals →](https://www.itworkslocally.dev/posts/yjs-internals-origins-yata-state-vectors)

## Further reading (if you have nothing to do)

- Albert Einstein, Relativity: The Special and the General Theory (1916), the source of the train thought experiment.
- Leslie Lamport, "Time, Clocks, and the Ordering of Events in a Distributed System" (1978).
- Martin Kleppmann, Designing Data-Intensive Applications, Chapter 5, "Detecting Concurrent Writes."
- Nicolaescu, Jahns, Derntl and Klamma, "Near Real-Time Peer-to-Peer Shared Editing on Extensible Data Types" (GROUP 2016), the YATA paper.
- Yjs documentation and the Yjs source on GitHub.
- The Dasabala Sutta (SN 12.21), which states the "when this exists, that comes to be" formula of dependent origination. For the full twelve links, see the Paṭiccasamuppāda Vibhaṅga Sutta (SN 12.2). Paṭiccasamuppāda is the Pali form of Pratītyasamutpāda.
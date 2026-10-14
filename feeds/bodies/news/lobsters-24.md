[[[[4[-1Materialize's storage layer (]] [2[[2`persist`]]] [4[-1) requires a metadata store where a small amount of state is maintained for each durable object. In June, a self-managed deployment with many such objects experienced a metastable failure where metadata operation latencies rose from a few milliseconds to thirty seconds, leading to an incident.]] ]]]

[[[[4[-1Self-managed deployments of Materialize use a PostgreSQL database as the metadata store, which during the incident had most of its connections in a waiting state. The number of ]] [2[[2`SIRead`]]] [4[-1 locks had grown to hundreds of thousands, an indication that the cost of running queries under ]] [2[[2`SERIALIZABLE`]]] [4[-1 isolation was the bottleneck.]] ]]]

[[[[4[-1This post is an account of how we reworked the implementation of the ]] [2[[2`persist`]]] [4[-1 metadata store to be able to build a linearizable log with queries running under ]] [2[[2`READ COMMITTED`]]] [4[-1 isolation. The new implementation was able to sustain three times the write throughput and gracefully degrade even as the load exceeded the capacity of the PostgreSQL database. Additionally, we describe how we gained confidence in its correctness by modeling PostgreSQL's ]] [2[[2`READ COMMITTED`]]] [4[-1 behavior in Lean 4 and proving that the design is linearizable.]] ]]]

[[[[4[-1Every durable object in Materialize (a table or a materialized view, for example) is stored by ]] [2[[2`persist`]]] [4[-1 in a unit called a shard. The bulk of a shard's data lives in object storage, while the metadata store holds the shard's state: which data files currently make up the shard, how far it has progressed in time, and which readers are holding on to old data.]] ]]]

[[[[4[-1The state of a shard can change for many reasons, including new data being committed, a reader advancing its read hold, and others. In a Materialize deployment there can be several independent processes all holding a shard handle for the same shard id. In order to make sure there is exactly one state history for any given shard we coordinate state-changing actions between processes in the usual way:]] ]]]

- [-1[[[4[-1For each shard, the metadata store maintains a versioned log of state diffs.]] ]]]
- [-1[[[4[-1Each process attempts to extend this log via a compare-and-set operation.]] ]]]
- [-1[[[4[-1Each version of the state is assigned a sequence number one higher than the previous one.]] ]]]
- [-1[[[4[-1Writers read the latest version, compute the next one, and request that the database append it on the condition that the version it read is still the latest, reading again and retrying if the condition fails.]] ]]]

[[[[4[-1We call the component that provides this "the consensus implementation", which on PostgreSQL is a single table:]] ]]]

| `1` [-1] | `CREATE TABLE consensus (` [-1] |
| --- | --- |
| `2` [-1] | ` shard text NOT NULL,` [-1] |
| `3` [-1] | ` sequence_number bigint NOT NULL,` [-1] |
| `4` [-1] | ` data bytea NOT NULL,` [-1] |
| `5` [-1] | ` PRIMARY KEY (shard, sequence_number)` [-1] |
| `6` [-1] | `);` [-1] |

[[[[2[[2`persist`]]] [4[-1 performs four operations on it:]] ]]]

- [-1[[[2[[2[[[[4[-1head(shard)]] ]]]]]] [4[-1 returns the row with the largest sequence number.]] ]]]
- [-1[[[2[[2[[[[4[-1scan(shard, from)]] ]]]]]] [4[-1 returns all rows with sequence number at least ]] [2[[2[[[[4[-1from]] ]]]]]] [4[-1, in order.]] ]]]
- [-1[[[2[[2[[[[4[-1compare_and_set(shard, seqno, state_diff)]] ]]]]]] [4[-1 appends ]] [2[[2[[[[4[-1state_diff]] ]]]]]] [4[-1 if ]] [2[[2[[[[4[-1seqno]] ]]]]]] [4[-1 is exactly one past the current head, and returns ]] [2[[2[[[[4[-1Committed]] ]]]]]] [4[-1 or ]] [2[[2[[[[4[-1ExpectationMismatch]] ]]]]]] [4[-1. We abbreviate it as CaS, and refer to ]] [2[[2[[[[4[-1seqno - 1]] ]]]]]] [4[-1, the version the writer believes to be the head, as ]] [2[[2[[[[4[-1expected]] ]]]]]] [4[-1. The first version of a shard has the sequence number 0 and therefore ]] [2[[2[[[[4[-1expected]] ]]]]]] [4[-1 is not defined. This case is covered separately below.]] ]]]
- [-1[[[2[[2[[[[4[-1truncate(shard, cut)]] ]]]]]] [4[-1 deletes all rows with sequence number below ]] [2[[2[[[[4[-1cut]] ]]]]]] [4[-1. It must not delete the head.]] ]]]

[[[[4[-1For this scheme to work, the log has to behave as if the operations happened one at a time, in some order consistent with when they were issued. It needs to be linearizable. Two writers must not both succeed at the same sequence number, and no writer may succeed at a sequence number that has already been truncated, since the state it writes there would be built on a version the rest of the system has discarded, and either outcome forks the shard.]] ]]]

## [[[4[-1The cost of SERIALIZABLE]] ]]

[[[[4[-1Until this work, the consensus queries ran under ]] [2[[2`SERIALIZABLE`]]] [4[-1 isolation, which is the simplest way to obtain linearizability in PostgreSQL, since if every transaction is serializable then any interleaving of them behaves like some serial order and the SQL only has to be correct in a serial order. The CaS query we were using would read the current head row and insert the next one if the head matched ]] [2[[2`expected`]]] [4[-1. The very first write of a shard was an ]] [2[[2`INSERT`]]] [4[-1 guarded by a ]] [2[[2`NOT EXISTS`]]] [4[-1 clause asserting that the shard is empty. Both of those queries are correct when run one at a time.]] ]]]

[[[[4[-1When running under ]] [2[[2`SERIALIZABLE`]]] [4[-1 isolation, PostgreSQL doesn't actually run transactions one by one. To increase performance it attempts to run transactions concurrently and detect serializability conflicts using Serializable Snapshot Isolation (SSI). The way this works is by recording every read of a transaction as an ]] [2[[2`SIRead`]]] [4[-1 lock on the rows and index pages it visits, and having every write check the ]] [2[[2`SIRead`]]] [4[-1 locks held on the pages it touches to detect read-write conflicts between transactions.]] ]]]

[[[[4[-1These locks are retained from the time a transaction commits until every transaction that overlapped with it has also finished, because a conflict can still form with a transaction that is still running. On a small, hot table with thousands of concurrent writers, many shards share each index page, so each insert walks the locks of every transaction that recently read the same page.]] ]]]

[[[[4[-1These charts are from a reproduction on a ]] [2[[2`db.r6g.2xlarge`]]] [4[-1 RDS instance, where the load is twenty Materialize clusters, each with six hundred trivial materialized views over an empty table, brought online gradually. What we can observe is that the database sustained the load up to about 4,300 CaS per second, but past that point transactions took long enough that the number of retained ]] [2[[2`SIRead`]]] [4[-1 locks grew, which made the conflict check on every insert more expensive, which in turn made transactions slower still. Latency reached thirty seconds and throughput fell to a fraction of what the database had sustained moments before, and the system did not recover until we removed load.]] ]]]

[[[[4[-1This is the failure pattern that Bronson et al. call a metastable failure [1], where a system in a vulnerable state is pushed by a trigger into a bad state and a sustaining effect keeps it there after the trigger is gone, so that recovery requires reducing load well below the level that caused the failure.]] ]]]

[[[[4[-1The trigger in this case was a transient slowdown of transaction processing that led to the increase in the number of ]] [2[[2`SIRead`]]] [4[-1 locks, which in turn increased the cost of every other write, turning the transient slowdown into a sustained effect. A transient slowdown can happen due to a transient spike in the load, the database starting concurrent table maintenance (vacuuming), a process pause, etc. The ]] [2[[2`SIRead`]]] [4[-1 lock count is what the paper calls a characteristic metric, a metric that rises with the trigger and does not return to normal until the failure is resolved, and the paper's recommendation is to treat the sustaining effect rather than the trigger, since many triggers lead to the same failure state. In our case a larger database instance or fewer shards would only move the trigger to a different threshold, whereas not relying on ]] [2[[2`SERIALIZABLE`]]] [4[-1 eliminates the sustaining effect.]] ]]]

[[[[4[-1One way to avoid ]] [2[[2`SIRead`]]] [4[-1 locks is to run transactions under ]] [2[[2`READ COMMITTED`]]] [4[-1 isolation. However, the existing queries were not correct in that mode. Under ]] [2[[2`READ COMMITTED`]]] [4[-1 each statement sees a snapshot taken when it started, but the uniqueness check that an ]] [2[[2`INSERT`]]] [4[-1 performs against the primary key runs against the live index and sees rows committed or deleted after the snapshot, so a single statement can observe a state in its ]] [2[[2`WHERE`]]] [4[-1 clause that no longer holds when its ]] [2[[2`INSERT`]]] [4[-1 runs. As it turns out, it is possible to get a linearizable log behavior under ]] [2[[2`READ COMMITTED`]]] [4[-1 by carefully adjusting the queries.]] ]]]

## [[[4[-1The core shard log invariant]] ]]

[[[[4[-1The new design relies on a property of the table that is maintained after every operation:]] ]]]

> [[[[4[-1The sequence numbers present for a shard always form a contiguous interval ]] [2[[2`[lo, head]`]]] [4[-1.]] ]]]

[[[[4[-1The two state-modifying operations are a compare-and-set and a truncate. A compare-and-set always extends the interval by one at the top. A truncation always removes a prefix, excluding the head. The consequence is that in a contiguous log the condition "]] [2[[2`expected`]]] [4[-1 is present and ]] [2[[2`expected + 1`]]] [4[-1 is absent" is equivalent to the condition "]] [2[[2`expected`]]] [4[-1 is the head", the latter being the condition required by the specification of CaS. Therefore under the assumption that the log is a contiguous log we can implement the condition of the specification using a ]] [2[[2`SELECT`]]] [4[-1 and a primary key.]] ]]]

[[[[4[-1Figure 1. The contiguity invariant and the two local checks the CaS statement makes. The CTE checks that ]] [2[[2`expected`]]] [4[-1 is present; the primary key checks that ]] [2[[2`expected + 1`]]] [4[-1 is absent. In a contiguous log the two together are equivalent to "]] [2[[2`expected`]]] [4[-1 is the head", which is what the specification asks for. Rows below ]] [2[[2`lo`]]] [4[-1 have been truncated; the marker at −1 is never truncated.]] ]]]

[[[[4[-1This suggests the following CaS query:]] ]]]

| `1` [-1] | `WITH expected_row AS (` [-1] |
| --- | --- |
| `2` [-1] | ` SELECT sequence_number FROM consensus` [-1] |
| `3` [-1] | ` WHERE shard = $1 AND sequence_number = $expected` [-1] |
| `4` [-1] | ` FOR KEY SHARE` [-1] |
| `5` [-1] | `)` [-1] |
| `6` [-1] | `INSERT INTO consensus (shard, sequence_number, data)` [-1] |
| `7` [-1] | `SELECT $1, $expected + 1, $data` [-1] |
| `8` [-1] | `FROM expected_row;` [-1] |

[[[[4[-1The ]] [2[[2`expected_row`]]] [4[-1 CTE (Common Table Expression) checks that the row the writer intends to build on is present and takes a shared lock on it, and the ]] [2[[2`INSERT`]]] [4[-1 adds ]] [2[[2`expected + 1`]]] [4[-1 if the primary key allows it, so the statement inserts a row in one case only: the predecessor is present and its successor is absent, which by the invariant means ]] [2[[2`expected`]]] [4[-1 was the head. If the CTE finds nothing, the ]] [2[[2`INSERT`]]] [4[-1 affects zero rows, and if the successor is already there the primary key rejects it. Both outcomes are reported as ]] [2[[2`ExpectationMismatch`]]] [4[-1.]] ]]]

[[[[4[-1Concurrent CaS operations fence each other through the primary key alone. Several clients can run the statement for the same ]] [2[[2`expected`]]] [4[-1 at once, in which case all of them see ]] [2[[2`expected + 1`]]] [4[-1 absent in their snapshot and all of them attempt the same ]] [2[[2`INSERT`]]] [4[-1. The primary key admits one, and the others receive a unique violation, by which time the head has moved and ]] [2[[2`ExpectationMismatch`]]] [4[-1 is the correct answer for them. The ]] [2[[2`FOR KEY SHARE`]]] [4[-1 lock plays no part in this, since it is a shared lock and concurrent CaS operations on the same predecessor all acquire it without blocking one another. Its purpose is to order CaS operations with respect to truncation, which is dealt with later in the post.]] ]]]

[[[[4[-1The other operations are single statements. ]] [2[[2`head`]]] [4[-1 and ]] [2[[2`scan`]]] [4[-1 are one ]] [2[[2`SELECT`]]] [4[-1 each:]] ]]]

| `1` [-1] | `-- head` [-1] |
| --- | --- |
| `2` [-1] | `SELECT sequence_number, data FROM consensus` [-1] |
| `3` [-1] | `WHERE shard = $1` [-1] |
| `4` [-1] | `ORDER BY sequence_number DESC LIMIT 1;` [-1] |
| `5` [-1] | ` ` [-1] |
| `6` [-1] | `-- scan` [-1] |
| `7` [-1] | `SELECT sequence_number, data FROM consensus` [-1] |
| `8` [-1] | `WHERE shard = $1 AND sequence_number >= $from` [-1] |
| `9` [-1] | `ORDER BY sequence_number ASC LIMIT $limit;` [-1] |

[[[[4[-1A single statement sees one snapshot, so each of them observes the log at one instant.]] ]]]

[[[[4[-1Finally, ]] [2[[2`truncate`]]] [4[-1 is one ]] [2[[2`DELETE`]]] [4[-1 with an ]] [2[[2`EXISTS`]]] [4[-1 guard:]] ]]]

| `1` [-1] | `-- truncate` [-1] |
| --- | --- |
| `2` [-1] | `DELETE FROM consensus` [-1] |
| `3` [-1] | `WHERE shard = $1 AND sequence_number >= 0 AND sequence_number < $cut` [-1] |
| `4` [-1] | ` AND EXISTS (` [-1] |
| `5` [-1] | ` SELECT * FROM consensus WHERE shard = $1 AND sequence_number >= $cut` [-1] |
| `6` [-1] | ` );` [-1] |

[[[[4[-1The guard requires a row at or above ]] [2[[2`cut`]]] [4[-1 to survive, so the statement never deletes the head, and deleting a prefix of an interval leaves an interval. The ]] [2[[2`sequence_number >= 0`]]] [4[-1 clause protects a marker row at sequence number ]] [2[[2`-1`]]] [4[-1 which is something the first write relies on and is described below.]] ]]]

## [[[4[-1Proving linearizability]] ]]

[[[[4[-1Changing such a correctness-critical component requires having extremely high confidence that the linearizability guarantees are met. For this reason, we employed formal methods to gain additional confidence in the design by modeling the system under ]] [2[[2`READ COMMITTED`]]] [4[-1 isolation in Lean 4 and proving that any execution is equivalent to a linearizable one.]] ]]]

[[[[4[-1The technique we used is called refinement, in which we relate the execution traces of two systems. In this context a system is described by some state and a set of actions that can be performed at any given point. We can then define the set of execution traces of a system as all possible sequences of actions starting from some initial set of states. The goal of refinement is to say that for all execution traces of system A there exists some execution trace of system B that is equivalent in some way. The two systems in our case are an idealized abstract system and the concrete implementation under ]] [2[[2`READ COMMITTED`]]] [4[-1. Since different shards are completely independent and the linearizability requirements exist only within the sequence of a single shard, we model the two systems as managing a single shard.]] ]]]

[[[[4[-1The abstract system captures the desired behavior by being as simple as possible. Its state is a map from sequence number to data and the set of actions corresponds directly to the four operations expected by the consensus implementation, performed atomically. Specifically, ]] [2[[2`compare_and_set(seqno, state_diff)`]]] [4[-1 succeeds if and only if ]] [2[[2`seqno - 1`]]] [4[-1 is the largest key in the map, or the map is empty and ]] [2[[2`seqno`]]] [4[-1 is 0, and ]] [2[[2`truncate(cut)`]]] [4[-1 removes every key below ]] [2[[2`cut`]]] [4[-1.]] ]]]

[[[[4[-1The concrete system captures the intricacies that arise by running under ]] [2[[2`READ COMMITTED`]]] [4[-1. The state of the concrete system is a table of rows and a set of statements in flight. The actions of this system correspond to the actions PostgreSQL can take, like starting a statement by taking a snapshot, performing a write against the live index, consulting row locks, etc.]] ]]]

[[[[4[-1The main modeling decision is that a CaS statement is no longer one atomic step but two, a step that evaluates the CTE against a snapshot and a later step that performs the ]] [2[[2`INSERT`]]] [4[-1 against the live index. The model allows for other clients to take any number of steps between these two.]] ]]]

### [[[4[-1Relating execution traces]] ]]

[[[[4[-1The first step to relating the execution traces is to establish what it means for a pair of states of the two systems to be equivalent. As shown above, the concrete system carries much more detail in its state than the idealized system, like the currently locked rows, so the two states are not directly comparable. We define equivalence through the use of an abstraction function ]] [2[[2`α`]]] [4[-1, which can transform an instance of the concrete PostgreSQL state to an instance of the idealized system. This function answers the question "What is the abstract state of the shard given this concrete state of the database?". For our case the function ]] [2[[2`α`]]] [4[-1 is simply returning the set of active rows of the table, ignoring all other implementation details like the set of active locks or current set of active transactions.]] ]]]

[[[[4[-1With this at hand we now have to prove a forward simulation: for every step the concrete system can take, from any reachable state, either the abstract system can take a matching step with the same result, or the concrete step changes nothing observable and the abstract system stays where it is. Taking a snapshot is a step of the second kind, and performing the ]] [2[[2`INSERT`]]] [4[-1 is a step of the first kind, being the point at which the CaS takes effect, so the obligation is that it inserts a row when and only when the abstract ]] [2[[2`compare_and_set`]]] [4[-1 would have succeeded, and inserts nothing when and only when it would have failed.]] ]]]

[[[[4[-1Figure 2. Forward simulation. Every step of the concrete system either matches an abstract step with the same operation and result, or changes nothing the abstraction function ]] [2[[2`α`]]] [4[-1 can see. Taking the ]] [2[[2`FOR KEY SHARE`]]] [4[-1 lock is a stutter; the ]] [2[[2`INSERT`]]] [4[-1 is the point at which the CaS takes effect. Client C's CaS with ]] [2[[2`expected = 2`]]] [4[-1 finds no row to lock after the truncation and maps to an abstract ]] [2[[2`cas(3)`]]] [4[-1 that returns ]] [2[[2`Mismatch`]]] [4[-1. The locked row is part of the concrete state but not of the abstract one.]] ]]]

[[[[4[-1If the obligation holds for every step, every concurrent execution of the concrete system corresponds to some sequential execution of the abstract one with the same operations returning the same results, which is the definition of linearizability. The proof quantifies over all clients and all sequence numbers, so there are no bounds on the number of writers or the length of the log.]] ]]]

[[[[4[-1A key part for successfully proving the simulation is invariants. Since the simulation for the ]] [2[[2`INSERT`]]] [4[-1 step needs to know that "predecessor present, successor absent" implies "predecessor is the head", which is only true if the log is contiguous, contiguity has to be proven as an invariant. After that the invariant is available as a hypothesis in every other proof obligation. Most of the work in a proof of this kind is finding the invariants that discharge the individual steps, and most of the bugs it finds appear as invariants that cannot be preserved.]] ]]]

### [[[4[-1Linearizing CaS against truncations]] ]]

[[[[4[-1Simulating concurrent CaS operations alone is straightforward. Contiguity is trivially preserved because the only modification is an append at ]] [2[[2`head + 1`]]] [4[-1, which extends the contiguous region. Additionally, the ]] [2[[2`INSERT`]]] [4[-1 step's obligation (i.e., that ]] [2[[2`expected`]]] [4[-1 is the head) follows from contiguity and the primary key. Therefore concurrent CaS operations for the same ]] [2[[2`expected`]]] [4[-1 all map to a sequence of abstract CaS operations, one that returns ]] [2[[2`Committed`]]] [4[-1 and the rest returning ]] [2[[2`ExpectationMismatch`]]] [4[-1, in the order their inserts reach the index. Note that this argument does not depend at all on the existence of the ]] [2[[2`FOR KEY SHARE`]]] [4[-1 lock, which never causes CaS queries to wait for one another.]] ]]]

[[[[4[-1The lock matters once ]] [2[[2`truncate`]]] [4[-1 is in the model as a step that removes every row below ]] [2[[2`cut`]]] [4[-1 provided a row at or above ]] [2[[2`cut`]]] [4[-1 exists. Without the shared lock it is possible for a concurrent execution of CaS and truncate operations to produce a non-contiguous shard, breaking the invariant. The failure corresponds to this execution:]] ]]]

1. [-1[[[4[-1Client A starts a CaS with ]] [2[[2[[[[4[-1expected = 4]] ]]]]]] [4[-1. Its snapshot shows row 4 present and row 5 absent, so the CTE produces a row.]] ]]]
2. [-1[[[4[-1Before A's ]] [2[[2[[[[4[-1INSERT]] ]]]]]] [4[-1 runs, client B appends 5, 6 and 7.]] ]]]
3. [-1[[[4[-1A ]] [2[[2[[[[4[-1truncate]] ]]]]]] [4[-1 with ]] [2[[2[[[[4[-1cut = 7]] ]]]]]] [4[-1 deletes rows 4, 5 and 6.]] ]]]
4. [-1[[[4[-1A's ]] [2[[2[[[[4[-1INSERT]] ]]]]]] [4[-1 checks the live index for row 5, finds nothing, and inserts it.]] ]]]

[[[[4[-1The table now holds rows 5 and 7, contiguity is broken, and A believes it advanced the head when it wrote a version below one that the rest of the system had already moved past. The primary key behaved correctly, since at the instant of the insert row 5 did not exist. What we would like to be true is that once an ]] [2[[2`expected_row`]]] [4[-1 is observed it is not deleted until the subsequent ]] [2[[2`INSERT`]]] [4[-1 has been executed.]] ]]]

[[[[4[-1This is what the ]] [2[[2`FOR KEY SHARE`]]] [4[-1 lock on the predecessor in the CaS query is for. A ]] [2[[2`DELETE`]]] [4[-1 takes a ]] [2[[2`FOR UPDATE`]]] [4[-1 strength lock on each row it removes, which conflicts with ]] [2[[2`FOR KEY SHARE`]]] [4[-1, so a ]] [2[[2`truncate`]]] [4[-1 that would remove the predecessor of an in-flight CaS blocks until that CaS has finished, and at the instant the ]] [2[[2`INSERT`]]] [4[-1 runs the predecessor is guaranteed to be present. ]] [2[[2`FOR KEY SHARE`]]] [4[-1 is the weakest lock mode that conflicts with a ]] [2[[2`DELETE`]]] [4[-1, and since it is a shared lock, concurrent CaS operations on the same predecessor do not block each other. Serialization of writers remains the job of the primary key; the lock only prevents a truncation from running in the gap that ]] [2[[2`READ COMMITTED`]]] [4[-1 isolation allows.]] ]]]

[[[[4[-1In the model the lock is a set of ]] [2[[2`(client, sequence number)`]]] [4[-1 pairs, added when the snapshot step runs and removed when the ]] [2[[2`INSERT`]]] [4[-1 step runs. We then add a precondition to the ]] [2[[2`truncate`]]] [4[-1 step that ]] [2[[2`cut`]]] [4[-1 must be at or below every locked sequence number, which is the model's transcription of the lock conflict. With it in place the predecessor's presence at insert time follows directly and the simulation for the ]] [2[[2`INSERT`]]] [4[-1 step holds in the presence of concurrent truncations.]] ]]]

### [[[4[-1Linearizing the first write]] ]]

[[[[4[-1The CaS query above assumes a predecessor row exists to be checked and locked. The first version of a shard has sequence number 0 and so there is no predecessor, so it needs its own query, and this is the operation that took the most iterations to get right.]] ]]]

[[[[4[-1The query used under ]] [2[[2`SERIALIZABLE`]]] [4[-1 was:]] ]]]

| `1` [-1] | `INSERT INTO consensus SELECT $1, 0, $data` [-1] |
| --- | --- |
| `2` [-1] | `WHERE NOT EXISTS (SELECT * FROM consensus WHERE shard = $1)` [-1] |
| `3` [-1] | `ON CONFLICT DO NOTHING;` [-1] |

[[[[4[-1The specification says the first write succeeds if and only if the shard is empty, which under ]] [2[[2`SERIALIZABLE`]]] [4[-1 the ]] [2[[2`NOT EXISTS`]]] [4[-1 guard implements directly. However, under ]] [2[[2`READ COMMITTED`]]] [4[-1 the guard is evaluated against a snapshot, and the ]] [2[[2`INSERT`]]] [4[-1 against the live index, allowing other steps to run in between. Under this model, this query is incorrect as the following execution is possible:]] ]]]

1. [-1[[[4[-1Client A starts the first write for a new shard. Its snapshot is empty, so ]] [2[[2[[[[4[-1NOT EXISTS]] ]]]]]] [4[-1 holds.]] ]]]
2. [-1[[[4[-1Before A's ]] [2[[2[[[[4[-1INSERT]] ]]]]]] [4[-1 runs, client B performs its own first write for the same shard and commits sequence number 0.]] ]]]
3. [-1[[[4[-1Client B appends 1, 2 and 3.]] ]]]
4. [-1[[[4[-1A ]] [2[[2[[[[4[-1truncate]] ]]]]]] [4[-1 with ]] [2[[2[[[[4[-1cut = 3]] ]]]]]] [4[-1 deletes rows 0, 1 and 2.]] ]]]
5. [-1[[[4[-1A's ]] [2[[2[[[[4[-1INSERT]] ]]]]]] [4[-1 checks the live index for row 0, finds nothing, and inserts it.]] ]]]

[[[[4[-1The table now holds rows 0 and 3, and both A and B believe they created the shard. This is the truncation problem from the previous section again, but the previous fix does not apply, since there is no predecessor row for A to lock, and there is nothing else in the table for A to lock either, because at the time of A's snapshot the shard did not exist.]] ]]]

[[[[4[-1In order to prevent this we need a row to collide with that is never removed by truncation. We take advantage of the fact that PostgreSQL uses signed integers and use the sequence number ]] [2[[2`-1`]]] [4[-1 with no data as a marker for "the shard is initialized". We then arrange for the first initialization of a shard to insert both the marker row and the intended first version, which can only succeed once. Additionally, we know truncate will only ever delete non-negative sequence numbers, leaving the marker intact. This gives rise to the following query for the first write:]] ]]]

| `1` [-1] | `INSERT INTO consensus (shard, sequence_number, data)` [-1] |
| --- | --- |
| `2` [-1] | `VALUES ($1, -1, ''), ($1, 0, $data);` [-1] |

[[[[4[-1A stale first writer now always collides with the marker in the live index, no matter what truncation did to sequence number 0 in the meantime, so the resurrection above is no longer possible. This query is correct in a system where every client runs the new set of queries, and is refined once more in the next section, where we consider what happens during an upgrade.]] ]]]

## [[[4[-1Reasoning about rollouts]] ]]

### [[[4[-1During the rollout]] ]]

[[[[4[-1So far we have only reasoned about the correctness of a system where every client performs the new set of queries. However, that assumption leaves a correctness hole for the real system, since these queries need to be released as a version upgrade of an existing Materialize installation. During that time the old version of Materialize will have to co-exist with the new version to perform a zero-downtime upgrade, and during that window the combination of the two sets of queries needs to be linearizable as well.]] ]]]

[[[[4[-1Unfortunately, the combination of the old set of queries under ]] [2[[2`SERIALIZABLE`]]] [4[-1 with the new set of queries under ]] [2[[2`READ COMMITTED`]]] [4[-1 does not result in a linearizable system, since SSI only tracks conflicts between ]] [2[[2`SERIALIZABLE`]]] [4[-1 transactions and the old first write's ]] [2[[2`NOT EXISTS`]]] [4[-1 guard is blind to a ]] [2[[2`READ COMMITTED`]]] [4[-1 creator. To make matters worse, even if both sets of queries run in ]] [2[[2`SERIALIZABLE`]]] [4[-1 mode they can still lead to a linearizability violation.]] ]]]

[[[[4[-1The issue stems from the fact that the new shard initialization is a blind write and so even under ]] [2[[2`SERIALIZABLE`]]] [4[-1 it takes no ]] [2[[2`SIRead`]]] [4[-1 locks. The fix is twofold. First we must ensure that during the rollout from the old set of queries to the new set, both clients run under ]] [2[[2`SERIALIZABLE`]]] [4[-1. Secondly, we must ensure that the new initialization query properly participates in the serialization detection by not being a blind write.]] ]]]

[[[[4[-1To address the first issue, we released the new set of queries with a configuration variable that controls the isolation level in which they run. Since this variable was new and only present in the just-released version, there was no way for users to set it while still running the old environment. This restriction ensured that during the rollout window, both sets of queries would be running under ]] [2[[2`SERIALIZABLE`]]] [4[-1 and therefore correctly linearize.]] ]]]

[[[[4[-1To address the second issue, we had to combine the blind write query with the emptiness check present in the old initial write query, leading to the following query:]] ]]]

| `1` [-1] | `INSERT INTO consensus (shard, sequence_number, data)` [-1] |
| --- | --- |
| `2` [-1] | `SELECT v.shard, v.sequence_number, v.data` [-1] |
| `3` [-1] | `FROM (VALUES ` [-1] |
| `4` [-1] | ` ($1::text, -1::bigint, ''::bytea), ` [-1] |
| `5` [-1] | ` ($1::text, $2::bigint, $3::bytea)` [-1] |
| `6` [-1] | `) AS v (shard, sequence_number, data)` [-1] |
| `7` [-1] | `WHERE NOT EXISTS (SELECT * FROM consensus WHERE shard = $1)` [-1] |

[[[[4[-1During the overlap the ]] [2[[2`WHERE NOT EXISTS`]]] [4[-1 clause ensures a stale initialization attempt is either rejected by the guard or, if it raced the creation, detected and aborted by PostgreSQL, since the guard is a read that SSI tracks.]] ]]]

### [[[4[-1After the rollout]] ]]

[[[[4[-1After the rollout is over, we know that the old environment is fenced out, but we're still running under ]] [2[[2`SERIALIZABLE`]]] [4[-1 mode until the new feature flag is flipped. Once the operator flips the flag we have a new overlapping period to worry about, since the new setting does not reach every process at the same instant. We must reason about whether new queries under ]] [2[[2`SERIALIZABLE`]]] [4[-1 mixed with new queries under ]] [2[[2`READ COMMITTED`]]] [4[-1 linearize correctly. Additionally, the database will contain shards that were initialized with the old initialization query. Those shards lack the initialization marker, and so the ]] [2[[2`WHERE NOT EXISTS`]]] [4[-1 guard should remain in the query even after everyone has upgraded. Fortunately, the combination of isolation modes in the new queries correctly linearizes and so flipping the flag is safe.]] ]]]

## [[[4[-1Results]] ]]

[[[[4[-1After rerunning the same benchmark on the same database instance with the new queries, the database sustained the load to the end of the run, reaching about 13,000 CaS per second. We ran out of clusters to add before the database ran out of capacity, so the actual limit is higher. The difference in behavior at the limit is that under the new queries, the cost of an insert does not depend on how many other transactions are in flight or recently finished, so there is no sustaining effect, and when the database reaches its capacity, latency rises with load and falls again when load falls. In the paper's terms, the vulnerable state no longer exists for this failure mode.]] ]]]

## [[[4[-1Afterthoughts]] ]]

[[[[4[-1The design came down to one invariant: once the sequence numbers are known to be contiguous, a primary key check is sufficient to decide whether a write is at the head, and ]] [2[[2`SERIALIZABLE`]]] [4[-1 is no longer needed. The one lock in the design is there for truncation and has no effect on writers. Every operation, including the first write, is a single statement.]] ]]]

[[[[4[-1Modeling the queries and proving them linearizable gave us a profound level of understanding of and confidence in the design. We were able to quickly test query variations and discover problematic interleavings when proofs failed to go through.]] ]]]

[[[[4[-1For self-managed deployments of Materialize running against PostgreSQL, the flag is ]] [2[[2`persist_pg_consensus_read_committed`]]] [4[-1. It defaults to off, and we recommend turning it on once the deployment has finished upgrading to v26.33 or later.]] ]]]

## [[[4[-1References]] ]]

[[[[4[-1[1] Nathan Bronson, Abutalib Aghayev, Aleksey Charapko, and Timothy Zhu. Metastable Failures in Distributed Systems. In ]] [2[[1*[[[[4[-1Workshop on Hot Topics in Operating Systems (HotOS '21)]] ]]]*]]] [4[-1, 2021. ]] [2[[0 [[[[4[-1https://doi.org/10.1145/3458336.3465286]] ]]](https://doi.org/10.1145/3458336.3465286) ]]] ]]]
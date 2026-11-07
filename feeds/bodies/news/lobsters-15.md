Formal specifications can help engineers reason about complex distributed systems and verify critical correctness properties. But they remain valuable only as long as they reflect reality. At Datadog, we encountered this challenge while working on** **[**Husky**](https://www.datadoghq.com/blog/engineering/introducing-husky/), our event database. We had a formally verified model of Husky’s routing system that matched production behavior when we created it. Over time, however, Husky evolved, and a change to its placement logic allowed conflicting placements to persist in production for about a year. Although harmless during normal operation, just two conflicting placements would have caused Husky’s backfill system to crash while recovering from placement data loss. We found the issue not by triggering that failure, but by checking production behavior against our TLA+ specifications.

That raised a question: **How do you know when a specification has drifted away from the system it was meant to describe?**

To answer that question, we built **FETCh** (Formal Execution Trace Checker), a system that turns TLA+ specifications into runtime monitors. FETCh lets us continuously validate production behavior against formal models at scale and detect discrepancies that traditional testing, code review, and manual specification review can miss.

In this post, we’ll show how we built FETCh, how we deployed it to validate Husky’s routing system, and how it helped us uncover a subtle bug conventional testing had not exposed.

Formal specifications define what a system can and cannot do in any given state. Model checking takes a specification and generates a tree of possible states, allowing us to verify properties such as “Can the system ever reach an invalid state?” or “Does a desired condition always eventually become true?”

A formal specification is valuable only if it is **tractable**, meaning that the tree of possible states can be generated in a reasonable amount of time. As a result, a specification cannot match reality exactly. It has to be an abstraction.

So we simplified parts of the system to make our specification tractable. But how do we know whether we simplified too much? How do we know whether the specification is still close enough to reality to be useful?

Traditionally, the answer is expert review. Engineers who understand both the implementation and the formal model evaluate whether the abstraction is still sound. That approach works well when a specification is first written, but it has an important limitation: Reviews provide a point-in-time evaluation, while production systems continue to evolve.

Over time, implementations change. New features are added, performance optimizations alter execution paths, and operational requirements shift. Even if a specification was accurate when it was written, it can gradually drift away from the system it was intended to describe. Because the specification itself still appears correct, that drift can create a false sense of confidence.

We encountered this problem with Husky, Datadog’s third-generation event store, for which we wrote several formal specifications years ago. We introduced Husky’s routing architecture in a [previous blog post](https://www.datadoghq.com/blog/engineering/husky-deep-dive/). In short, Husky is a distributed streaming system that processes millions of events per second and must satisfy several correctness properties so that data is ingested exactly once.

Although we had not observed any major defect over the years, we had never formally validated at scale that the system continued to follow the specifications.

Continuously validating the alignment between a real system and its specification is not a new idea. But the requirements that make a specification **observable** conflict with those that make it **model-checkable**.

A model-checkable specification needs bounded inputs to remain tractable—for example, a set of two clients and three events. It also needs to describe how things happen—for example, by modeling a network as a queue of incoming requests—so that all possible executions can be explored.

In contrast, an observable specification needs to support unbounded inputs because a real system can process a continuous stream of requests. It should declare what is allowed, not how it happens. How requests are queued, for example, is usually an implementation detail.

Consider a simple lock server that tracks currently held locks in memory, along with a counter indicating whether each lock is held (1) or not (0). The following specification captures the allowed state transitions for acquiring and releasing a lock:

This specification is observable because it describes only what can happen. But it cannot be model checked as is. The model checker needs to know what `Locks` is—for example, a set of values `{1, 2, 3}`—and what incoming requests are possible—for example, `Acquire(1)`, `Acquire(2)`, and `Release(1)`—to generate all possible states.

This tension between observable and model-checkable specifications helps explain why existing approaches often focus on observing byproducts, such as invariants, rather than the specifications themselves. One example is [PObserve](https://p-org.github.io/P/advanced/pobserve/pobserve/), an open source project that uses real traces to monitor  P specifications. While useful, verifying that invariants hold is not enough to show that a specification is still valid.

In the lock server example, we can derive the invariant “no locks are acquired twice” from the specification:

`NotAcquiredTwice == \A l \in locks : locks[l] <= 1 \* no locks can be held by more than one client`

Now consider a naive implementation:

The invariant holds because of the assertion. But the implementation still violates the specification because it can release the same lock twice, even though that transition is forbidden by the model.

For us, this distinction was important. We didn’t just want to know whether a few high-level properties continued to hold in production. We wanted to know whether the system itself still behaved according to the specification.

At Datadog, we view specifications as more than a design tool. They also provide a sandbox for exploring changes to a system before writing production code. Engineers can test whether a proposed optimization or simplification preserves correctness by modifying the specification and running the model checker, often at a fraction of the cost of building a prototype.

We’ve used this approach to simplify complex parts of our systems with confidence. But that confidence depends on the specification remaining aligned with reality. For Husky’s routing system, we wanted a way to continuously validate the specifications themselves, not just the implementation.

More specifically, we wanted a framework that could use the same formal foundation for model checking, runtime validation, and mathematical proofs. So we built FETCh.

FETCh turns [TLA+](https://en.wikipedia.org/wiki/TLA%2B) specifications into Rust-based runtime monitors. These monitors can consume telemetry data, such as Datadog logs, and report when the system violates the specification.

TLA+, a formal specification language developed by Leslie Lamport, supports model checking and machine-checked mathematical proofs. But the main reason we chose TLA+ was its support for refinement.

In TLA+, refinement is a formal relationship between two specifications. A specification B refines a specification A if every behavior allowed by B is also allowed by A. This relationship allows us to bridge the gap between observable and model-checkable specifications: We can define an observable specification A that describes real-world behavior and a model-checkable specification B that refines A by introducing the bounds needed for tractable analysis.

We can then iterate on specification B while using the model checker to verify that B does not permit behavior forbidden by A. At the same time, we can continuously validate A against production behavior by using FETCh-generated runtime monitors.

With FETCh, a single formal foundation can be:

- Observable through automatically generated runtime monitors
- Model-checkable through refinements
- Provable using theorem provers such as Isabelle or Zenon

FETCh relies on the general structure of TLA+ specifications to generate Rust monitors. A specification contains variables that track system state and a `Next` formula that describes the allowed state transitions. FETCh maps those concepts directly to a monitor that maintains the state variables and defines one function for each action in `Next`.

For each incoming event, the monitor identifies the corresponding function, checks its preconditions, and applies the state update. If a precondition is violated, the system has performed an action that the specification does not allow, indicating that the implementation and specification have diverged.

One key part of translating TLA+ to Rust is identifying the input parameters for each transition function because TLA+ is not a typed language. Consider the lock server example from the previous section:

The specification neither defines `Locks` nor explicitly states that the `lock` parameter must be a member of the `Locks` set.

FETCh takes advantage of the fact that an observable specification focuses on the **what**, not the **how**. Each action can therefore be prefixed with “there exists x in a set S such that…” (`\E x \in S: …`), effectively creating a lightweight typing system for TLA+. Constants can also be mapped to Rust types with annotations such as `\* fetch:u32`. Finally, a `TypeOK` conjunct defines the types of variables, which is already common practice in TLA+.

Putting these pieces together, the previous specification becomes:

Once those type constraints are added, the specification can be translated directly into a monitor:

If you look closely at the FETCh-generated code, you’ll notice types such as `FetchMap` instead of `HashMap`. Those abstractions exist because FETCh was designed for validation at production scale. `FetchMap` is one of several components that let FETCh handle large amounts of state efficiently, which becomes important when validating Husky’s routing system.

We built FETCh to verify that Husky’s distributed routing system conforms to its specifications. Specifically, we wanted to validate that two events with the same ID are always sent to the same shard, an abstraction over a set of Kafka partitions. For our purposes, we can simplify Husky’s routing system to two components:

- A database that stores placements, which map an ID range to a list of shards, and enforces the constraint that no two placements overlap for a given ID range
- A routing service that requests and caches placements as it receives events and uses a hash function to deterministically map each event ID to a shard within the assigned placement

A defect anywhere in this system—such as an improperly handled placement, placement data loss, or a transient split brain in the placement allocation service—could result in duplicate events being silently inserted into Husky. Duplicates can increase billing for customers, corrupt query results, and cause false positives or false negatives in monitor evaluations.

Initially, we wrote a single specification that modeled our routing system as a function mapping event IDs to shards. From a TLA+ standpoint, the specification was simple, easy to reuse, and abstract enough to be converted to a runtime monitor. But we quickly ran into a scaling problem: The monitor had to keep track of every event processed during a rolling ingestion window. That state needed to persist if the service running the monitor restarted, and its size made this approach impractical at Datadog’s scale. With trillions of distinct event IDs over an ingestion window, the monitor would need to maintain an impractical amount of state.

We went back to the drawing board.

We considered using statistical data structures like Bloom filters instead of conventional maps. However, because we expected routing errors to be rare—no significant routing issues had been observed in production over the years—we needed exact results rather than probabilistic ones. That meant tracking every event and checking every placement created during the ingestion window for overlaps.

What made this approach practical was scoping part of the specification—and therefore part of the monitor’s state—to individual routing service processes. Although we process trillions of events per window, those events are distributed across thousands of instances, while we allocate only a few million placements. We can validate globally that placements do not overlap because there are far fewer of them. Then, each pod can validate its own subset of events to verify that placements are used correctly.

Validating part of the behavior locally within a sidecar keeps the state manageable and has other advantages. Because events need to be validated only over the lifetime of an individual instance, we don’t need to persist that state across restarts. It also reduces telemetry costs because we don’t need to send a validation payload for every event over the network.

We defined two FETCh-compatible abstract specifications:

- `Router.tla` models receiving and using placements and validates that events are published using previously received, unmodified placements and the correct hash function.
- `PlacementStorage.tla` models placement storage and validates that no conflicting placements overlap.

We then refactored our existing specifications so that they refined both abstract specifications. We also created a formal proof demonstrating that consistent routing cannot be broken if both specifications are respected. Finally, we used FETCh to generate two runtime monitors, one for each specification.

We then ran into another issue. We wanted the monitors generated from `Router.tla` to operate per process, but TLA+ specifications represent system state globally. To make FETCh-generated monitors work with local state only, we added support for process-local monitors through the `fetch:proc_type` and `fetch:per_proc` annotations:

Given the specification above, FETCh generates a process-local monitor. Notice that `Processes` does not appear anywhere in the generated monitor:

Next came `PlacementStorage.tla`. Although we have far fewer placements than events, the number of placements is still large. Keeping all of that state in memory would be impractical.

This is where the `FetchMap` and `FetchSet` indirections mentioned in the previous section come into play. They make it possible to plug in custom map and set implementations, including more complex combinations such as maps of sets. We created RocksDB-backed implementations for them, which let us handle the required state size.

Running FETCh in production introduced relatively little overhead. In the sidecar running alongside our routing service, we measured p90 overhead of about 2% CPU and less than 0.2% memory across thousands of pods processing tens of millions of events per second.

Batch validation of placement overlap processed several days of data containing several million placements in around an hour by using 1 CPU and a few gigabytes of memory.

The routing service conformed to `Router.tla`: We detected no violations in the monitored traffic.

The monitor generated from `PlacementStorage.tla`, however, did trigger. It detected conflicting placements that should not have been stored in the database.

A year earlier, we had added special cases in which we intentionally skipped deduplication and allowed conflicting placements to improve balancing. What we missed was that those placements were still being persisted. We estimate that fewer than 0.01% of placements conflict. Even at that rate, two conflicting placements are enough to cause our backfill system to crash.

The backfill system is designed to recover from placement data loss, but it does not tolerate placement conflicts, which should be forbidden outside of these special cases. As a result, a placement data-loss event would have prevented the backfill system from recovering correctly.

How did this issue remain hidden for so long? The conflicting placements were harmless during normal operation. They would have caused problems only during a specific and relatively rare failure scenario involving placement data loss. That’s not a scenario we can realistically exercise through conventional test suites.

FETCh found the issue by validating system behavior against the specification itself rather than waiting for customer-visible symptoms to appear. After we stopped persisting the conflicting placements, FETCh detected no further violations in the monitored traffic.

The specifications continued to provide value after deployment.

By continuously validating production behavior against a specification, we detected an issue that neither testing nor routine review of production telemetry data had revealed. FETCh helps us detect when models and implementations diverge as systems evolve.

Our approach has limitations. The FETCh transpiler supports only a subset of TLA+ and currently checks preconditions only against the current state. Monitoring a distributed system with FETCh also requires engineering effort to instrument it. Validating global state at production scale remains challenging and often requires system-specific solutions.

Even with those limitations, continuously validating specifications against production behavior gives us a way to detect drift and continue using specifications as an active part of the engineering process.

Formal methods are becoming more common across the industry. Companies such as [AWS](https://www.amazon.science/publications/how-amazon-web-services-uses-formal-methods) and [Microsoft](https://www.youtube.com/watch?v=L_PPKyAsR3w) have publicly discussed using formal specifications to design complex distributed systems and uncover subtle correctness issues. At Datadog, we’ve found them valuable for the same reasons: They help us reason about difficult edge cases, uncover issues early in the design process, and give our team confidence to simplify and evolve systems.

Despite those benefits, formal methods remain difficult to adopt. Their syntax is often unfamiliar to software engineers, much of their tooling originated in academia, and choosing the right level of abstraction requires a deep understanding of both the system and the modeling framework.

Keeping specifications aligned with production systems requires ongoing effort. As systems evolve, specifications can drift from the implementations they were designed to describe. Continuous validation gives us a way to detect that drift and helps keep specifications grounded in how production systems actually behave.

We expect this alignment to become increasingly important as more code is generated by AI systems. Formal specifications can provide a machine-checkable definition of correctness for generated code.

With FETCh, we validated a critical production system against its formal specifications and uncovered an issue that had gone undetected for years. More importantly, we found that specifications can continue to provide value long after the design phase ends.

We’re continuing to expand our use of formal specifications across Datadog. We’re improving FETCh itself, integrating it more deeply into CI/CD workflows, and exploring additional systems that could benefit from runtime validation.

If this sounds like the kind of engineering challenge you’d enjoy working on, check out our [open engineering roles at Datadog](https://careers.datadoghq.com/all-jobs/?parent_department_Engineering%5B0%5D=Engineering&utm_source=engblog&utm_medium=corpsite&utm_campaign=engcommunity-2026-testing-husky&gh_src=hm4uekgj1us).
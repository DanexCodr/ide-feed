> **TL;DR:** On a Postgres capped at 1 CPU, the queue peaked at ~375 jobs/s with 64 workers. The CPU ran out before the 100 connection slots did. A shared pool of 20 connections got 128 workers to 650 jobs/s.

The paradigm has had a lot of attention as a simple way to construct durable queues with atomic guarantees, and rightly so. You can build high throughput systems with fault tolerance thanks to the fact that your queue is persisted in a simple and readable way. There's no need to worry about transactions, locks, and the other complexities associated with many workers competing for a single resource. It scales well even without connection pooling, since Postgres handles 100 distinct connections by default, but no architecture scales forever. I've seen a few discussions of the design but few analyses dedicated to finding where that scaling breaks. So, I ask, where DOES it break?

## The architecture

I've used this design myself for running tasks triggered from a web UI that users don't need to wait on. In a typical use case, this might be a user uploading data and needing to run some ETL process on it. Or media needing some transformation applied to it. When I applied it, it went something like this.

1. Define a simple Postgres table (i.e. the queue) that can represent each job and give it a status. What do you need to know about each job?
2. Define the consumers of the queue. What are the workers going to do when they receive a job?
3. Design a manifest that tells you which consumer belongs to which job as stored in the table. What is the implementation behind each job?
4. Set consumers to take items from the queue and your producers to add things to it. How will things be enqueued and dequeued?

So I set up a simple experiment, with the following implementation. First the simple jobs table for (1):

```
DROP TABLE IF EXISTS jobs;
CREATE TABLE jobs (
  id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  payload     JSONB       NOT NULL DEFAULT '{}',
  status      TEXT        NOT NULL DEFAULT 'pending',
  run_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  locked_at   TIMESTAMPTZ,
  finished_at TIMESTAMPTZ
);
CREATE INDEX jobs_pending ON jobs (run_at, id) WHERE status = 'pending';
```

Next the consumers for (2). I designed each worker to claim an item from the queue by marking it running and wait 100ms to simulate some IO or other light work. Each worker was run as a separate thread with its own database connection. Recall that Postgres handles each connection as a process internally, so the number of Postgres processes running scales with the number of workers. The code ran as follows, minus the timing code, using the CLAIM and COMPLETE queries shown below:

```
def worker(seconds, work_ms):
    conn = psycopg.connect(DSN, autocommit=True)
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        row = conn.execute(CLAIM).fetchone()  # claim the next job
        if row is None:
            break                             # the queue is empty
        time.sleep(work_ms / 1000)            # the "work"
        conn.execute(COMPLETE, (row[0],))     # mark it done
```

I didn't need to define a manifest for (3) in this setup. That's because the simulated wait adequately represented the idea of a worker doing some useful work. We assume therefore that all jobs are doing the same task here.

Now, the last step, for (4). This is where FOR UPDATE SKIP LOCKED was actually used. Per the standard setup, I ran the following query to claim tasks from the queue. We claim a task at a time, mark it running, and the skip means there is no race condition to worry about; two workers claiming from the queue at the same moment just ignore rows claimed by the other.

```
-- CLAIM
UPDATE jobs SET status = 'running', locked_at = NOW()
WHERE id = (
  SELECT id FROM jobs
  WHERE status = 'pending' AND run_at <= NOW()
  ORDER BY run_at, id
  LIMIT 1
  FOR UPDATE SKIP LOCKED
)
RETURNING id;
```

Once the work is finished, the worker marks the job as done:

```
-- COMPLETE
UPDATE jobs SET status = 'done', finished_at = NOW() WHERE id = %s;
```

One thing this setup doesn't handle is a worker crashing mid-job. Its row stays marked as running forever, and nobody picks it up again. In production you'd want something that reclaims jobs whose locked_at is too old, but that's out of scope here.

And with that the setup is largely complete. The last part is an orchestration layer that controls the setup and execution of the workers, plus some code to track telemetry that we report back as the results of the experiment. For this I set up a simple orchestrator which launched the worker threads using the threading library and used a barrier to coordinate all workers being ready and connected to Postgres before running anything, so the experiment was clean. The details aren't particularly important for what we're discussing here.

## The experiment

Once everything was set up, I used docker compose to run a Postgres 18 container capped at 1 CPU and 1GB memory. Other than shared_buffers, which I set to 256MB, Postgres ran with its default settings, including the default max_connections of 100. I had the workers connect on a port exposed by the docker network on my PC. The workers themselves all ran as threads in a single Python process on the same PC, outside the container, so they weren't subject to the caps. The goal was to find out where the memory cap started to bite as the number of workers ramped up and measure the job throughput at the same time. To that end, I collected the average number of jobs completed per second over the lifetime of a given run. Plus p50 and p99 times to claim a job from the queue and mark it done. The idea being to see if the longest query times at p99 started to run away from the median p50 query time. I.e. whether there was a tail in the query times as Postgres continued to be loaded, plus whether the average query time changed. Those do not represent any job related timings, for example time waiting on the queue, but rather just the query time for the worker against the database.

I ran the experiment in steps, doubling the number of workers each time from 1 to 128. Before each step, the queue was rebuilt with a backlog of 500,000 pending jobs, so the workers never ran out, followed by a VACUUM ANALYZE and a CHECKPOINT so every step started from the same state. Each step then ran for 20 seconds. While it ran, I sampled Postgres's CPU and memory use every half second straight from the container's cgroup, which costs Postgres nothing, plus what each connection was doing from pg_stat_activity. That last one needs a query, on a connection of its own, so it takes up one of the 100 slots and adds a couple of queries a second, small next to the hundreds the workers send.

The results showed that throughput, measured in terms of jobs per second, climbs steadily up to 32 workers, then stalls at around 375 jobs per second at 64 workers, before the 100 connection slots, which is Postgres' default, are even used up. At 128 workers it falls to around 200 jobs per second, and 29 of them couldn't connect at all. Median query time starts to increase significantly between 32 and 64 workers, from 8ms to 45ms, and p99 latency climbs even quicker, from 25ms to 393ms, then to 1.6s at 128 workers. These numbers come from a single run, so treat them as indicative rather than exact.

| Workers | Jobs/s | p50 (ms) | p99 (ms) | Postgres CPU | Failed to connect |
| --- | --- | --- | --- | --- | --- |
| 1 | 9 | 9.6 | 13.2 | 6% | 0 |
| 2 | 18 | 8.5 | 12.3 | 6% | 0 |
| 4 | 37 | 8.1 | 14.6 | 7% | 0 |
| 8 | 76 | 4.1 | 21.9 | 9% | 0 |
| 16 | 153 | 3.9 | 12.8 | 13% | 0 |
| 32 | 292 | 7.8 | 24.7 | 25% | 0 |
| 64 | 376 | 45.2 | 393.3 | 86% | 0 |
| 128 | 208 | 317.9 | 1588.3 | 100% | 29 |

With 100ms of work per job, each worker can manage at most around 9 jobs per second, so up to 32 workers the queue keeps up with everything the workers ask of it. At 64 workers it should manage around 575 jobs per second, and at 128 well over 1,000.

## Why it breaks and what to do about it

That workers fail once connections are saturated makes sense. If Postgres is only allowed to service 100 connections, trying to funnel more and more work through the same limited set of slots clearly won't work. More surprising is that throughput stalls at 64 workers, before the slots run out. The monitoring shows why: Postgres's one CPU was at 86% at 64 workers and 100% at 128. Memory, on the other hand, was never close to the cap. The container peaked at around 560MB of its 1GB, and most of that was cache. The memory private to the connections did grow with them, from 11MB with one worker to 183MB with around 100 connections, so roughly 2MB a connection, but that's nowhere near enough to matter here.

What the busy connections were waiting on tells a similar story. At 64 workers, the most common wait was LWLock:WALWrite: connections queuing to flush the write-ahead log, which every job has to do twice, once for each update. At 128 workers, LWLock:BufferContent took over, with 24 connections at a time waiting for it. That's a lock on a single page in memory, most likely the few pages at the head of the queue that every worker is claiming from. So past a point, adding workers just adds more connections fighting over the same CPU, the same log and the same handful of pages.

Adding client-side connection pooling would be the obvious extension at this point, since that frees up connection slots by freeing connections from workers who are not actively querying the database, whilst they do their real work. This doesn't modify the number of slots Postgres offers, but just makes better use of the same slots. So I ran the experiment again, with the workers sharing a pool of 20 connections:

| Workers | Jobs/s | p50 (ms) | p99 (ms) | Postgres CPU | Failed to connect |
| --- | --- | --- | --- | --- | --- |
| 1 | 10 | 5.4 | 8.5 | 6% | 0 |
| 2 | 19 | 4.2 | 23.2 | 7% | 0 |
| 4 | 36 | 10.3 | 16.0 | 8% | 0 |
| 8 | 76 | 4.1 | 21.1 | 10% | 0 |
| 16 | 150 | 4.6 | 16.3 | 14% | 0 |
| 32 | 259 | 13.3 | 124.3 | 47% | 0 |
| 64 | 515 | 15.2 | 166.7 | 62% | 0 |
| 128 | 652 | 65.6 | 360.1 | 98% | 0 |

With the pool, 128 workers managed 652 jobs per second instead of 208, p99 fell from 1.6s to 360ms, and every worker got the connection it needed. The pool isn't free though. From 32 workers, p99 is noticeably higher than without it at the same count, because a worker sometimes has to wait for a connection to come free. And at 128 workers Postgres was back at 98% CPU, so the pool moves the ceiling rather than removing it. One caveat: at 128 workers the Python process running the workers was also using a full CPU core, so some of that ceiling is probably the client, not Postgres.

It's also worth remembering that a client-side pool only shares connections within one process. If your workers are spread over several machines, each with its own pool, the connections still add up, and that's where a server-side pooler like PgBouncer comes in.

## What's next

There are of course many other ways the design can break aside from connection saturation. We've only covered it here by increasing the number of workers contending for jobs. The queue table bloating as more and more rows are added, for example. That's something I'd like to explore. And we've not experimented with resource constraints. How does memory usage vary with an increasing connection slot size, for example? We'll cover these in a follow up article in the near future.

## Further reading

- Postgres 9.5 feature highlight: SKIP LOCKED for row-level locking, Michael Paquier, 2014. The feature as it landed, from a Postgres committer.
- The locking clause, PostgreSQL documentation. Where SKIP LOCKED is described, and why it's only suitable for queue-like tables.
- Choose Postgres queue technology, Adriano Caloiaro, 2023. The case for using Postgres as your queue before reaching for anything else.
- Postgres job queues & failure by MVCC, Brandur Leach, 2015. A different way the design breaks: long-running transactions and dead rows.
- Keeping a Postgres queue healthy, Simeon Griggs, PlanetScale, 2026. Brandur's experiment rerun on Postgres 18.

Interested in the full script for your own testing? Email me at [hello@garbagecollected.io](mailto:hello@garbagecollected.io).
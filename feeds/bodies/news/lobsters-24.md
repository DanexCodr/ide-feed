Over the past decade, one of the most contentious Postgres feature requests has been for query hints. The planner is remarkably effective at making good decisions, but it doesn’t always do so, and query hints have been proposed as a way to fill that gap. They’ve been a popular feature on other databases for years, and some would say that they are essential for production usage to ensure that indexes are used effectively and queries are planned sensibly. While [pg_hint_plan](https://www.postgresql.org/about/news/pg_hint_plan-v160-released-2712/) has existed for a while, the Postgres community has historically been divided on this topic, with the general consensus being that planner failures were bugs that should be fixed instead of being worked around.

Postgres 19 brings 2 new contrib modules that collectively provide the plan hint experience without affecting all queries or SQL syntax. [pg_plan_advice](https://www.postgresql.org/docs/19/pgplanadvice.html) works at the session level, allowing you to simply SET how the next queries will be planned. The technique supports a decent list of features, letting you specify scan method, join order, join method, parallelism, partitionwise joins, and semijoin uniqueness.

The companion extension provided is [pg_stash_advice](https://www.postgresql.org/docs/19/pgstashadvice.html). This is meant to apply to query identifiers instead of specific queries, so rather than using SET to hint, you instead find a specific query identifier and tell Postgres to always apply your hints only to that query. It supports the same capabilities for affecting query plans as pg_plan_advice, so most of this article applies to it as well.

Under the hood, these extensions work by telling the planner that it should not pick the options you didn’t select. This can’t actually force Postgres to pick the plan that you actually want, so if there’s no viable way to actually use the hint, the advice will be partially or fully ignored. In addition, there is no check that the advice is good- the planner will happily accept input that actively degrades query performance. In practice, this means that it can be similar to existing `enable_` knobs you may have already used to force certain plans on queries. For example, if you’re trying to convince the planner to use an index, here’s the old way and the new way you’d consider. They do similar things, but the advice extensions provide a lot more capability and granularity:

## The scenarios  #

I’ve put together a few examples of queries where you might want to consider using pg_plan_advice, and did some testing to see how well it works in practice. All of these tests ran on ClickHouse Managed Postgres, on a m6gd.xlarge machine with 4 vCPUs, 16GB RAM, and a 237GB local NVME drive. The tests are fairly artificial, as the planner is remarkably clever and it’s surprisingly difficult to construct scenarios that reliably give it trouble.

pg_plan_advice ships as a contrib module, so you’ll probably want to add it to your server’s `shared_preload_libraries` or take one of the following steps to get it working in a PG19 environment:

This post uses a lot of SET commands for demonstration purposes. If you are looking to use pg_plan_advice in a production system, please keep in mind that these should instead generally be `SET LOCAL` in a transaction to prevent unexpected effects on other queries.

## Scenario 1: `ORDER BY… LIMIT` #

The planner generally assumes that rows in a table are spread somewhat evenly. Unfortunately, the ISO Standard User does not actually exist, so a lot of database writes are clustered around bursts of correlated activity. This can lead to a scenario where the planner knows a few percent of rows match a given filter, starts walking through a primary key column to find them, and ends up scanning nearly the whole index before getting enough hits.

Here’s the query we’ll use for this:

```
1SELECT * FROM events WHERE status = 'failed' ORDER BY id LIMIT 10;
```

Running it does, indeed, give us a terrible plan.

Excellent, we’ve reproduced the failure! The index scan looks like it should be reasonable, and the cost of 66.77 is trivial: the planner clearly expected to find all 10 rows it needed immediately. Unfortunately, it had to gather and discard 10,000,000 rows before finding a useful result, which obviously took far longer than you’d expect.

You’ve probably noticed the “Generated Plan Advice” section in this explain plan as well. This is another new feature; we’re using `EXPLAIN (ANALYZE, BUFFERS, PLAN_ADVICE)` here. Since we didn’t provide plan advice, this output just shows the plan it actually used.

We could definitely fix this with a new index, but that isn’t always a good option when you see this kind of thing in the wild, so let’s try a bitmap heap scan. It works by first constructing a bitmap of potential row locations using a bitmap index scan, and then decodes it to fetch the underlying data. It’s better suited to bulk operations, so it’s a good bet given how uncooperative the index scan is proving to be. Here’s all we need to do to actually use it:

```
1SET LOCAL pg_plan_advice.advice = 'BITMAP_HEAP_SCAN(events)';
```

Here’s the new EXPLAIN.

The parallelism makes it a bit tricky to read, but a few things stand out. First, we got <10ms execution time, so the bitmap heap scan actually did help. Second, we can now see the supplied plan advice at the bottom of the EXPLAIN output, and the matched feedback (without a failed flag) makes it clear that the planner actually used our advice. Please note that this does not necessarily mean that the planner benefited from the advice.

## Scenario 2: `JOIN` correlation  #

JOINs can be a source of planner complications, as statistics are resolutely single-table. The planner has a limited ability to predict how many rows will be pruned by filters on JOINed tables, so it can be way off base on selectivity. In general, it assumes that filters on different tables are independent of each other, which is a fairly easy assumption to violate with the following setup:

Here’s our baseline query. It’s just a simple join, filter, and limit:

Here’s our first plan, with the planner doing the heavy lifting for us:

This plan is honestly pretty terrible. The planner correctly understands that there are 500K or so `trial_start` rows, and that 1% of customers are `enterprise` customers. It then multiplies these numbers by each other, which leads it to predict that 5000 rows will match, and it only needs 10. Unfortunately, the filters aren’t as independent as it’s estimating, so only 20 out of the 500K rows actually have the values it’s looking for. As such, it ends up scanning a lot more rows than it was counting on to get this result. You can see as much in the row estimates above: the planner predicts 5288 rows when we know there are only 20, which is right in line with the math.

To fix this, let’s try giving plan advice. We want the join order to prioritize accounts first, as that will give us a vastly more selective filter to cut down on row counts.

```
1SET LOCAL pg_plan_advice.advice = 'JOIN_ORDER(a act)';
```

Here’s what it gives us:

A nearly 200x improvement is absurdly better. By adjusting the join order, we’re able to take full advantage of the `accounts` table’s much lower number of rows matching the `enterprise` filter, which lets us dramatically cut down on the number of rows to scan. You probably won’t get quite as big a speedup in most cases in production, but this pattern comes up every now and then, and having a tool to address it is priceless.

This is probably the use case that fits the plan advice feature best. It’s rare, but there are not a lot of good alternatives for dealing with it. I’ve come across similar challenges perhaps a half dozen times, and while I was able to find workarounds, they got pretty hacky and difficult to reason around.

## Scenario 3: Handling stale hints  #

We’ve got some promising results in scenario 1, but what happens if the data changes to be less lumpy while our hint is still in place? To test this, let’s set every third row to the failed state:

```
1UPDATE events SET status = 'failed' WHERE id % 3 = 0;
2VACUUM ANALYZE events;
```

This means we only need to walk a few rows to get what we’re looking for, so the planner estimate should be able to get us a good outcome. Sure enough, if we run without any hints, we get this:

That’s the kind of result we wanted to see in the first place! Let’s see how we do with the earlier hint to use a bitmap heap scan in place:

That’s 7,000 times worse, and the feedback doesn’t show a problem because it’s still `matched`. Now that the artificial data condition tripping up the planner is gone, the planner has no problem doing a better job than our hinted alternate. This is a good reminder that all hints should be regularly checked for ongoing necessity — otherwise, your performance fixes can lead to performance issues.

## Conclusion  #

We’ve gone through a few scenarios, and it’s clear that `pg_plan_advice` is a powerful but situational tool. It’s not easy to construct scenarios that reliably confuse the planner, but they show up in production often enough that it’s worth having a tool to address them. pg_plan_advice is new enough that it’s hard to say for sure, but I’d bet from what I’ve shown here that the following workflow will serve you well:

1. If you get a mysteriously slow query and tuning doesn’t get the results you wanted, then plan advice is a good thing to try.
2. If it works, then baking it into the transaction with `SET LOCAL` is a good way to improve performance.
  1. You can also tie it to the query ID with pg_stash_advice. If you do so, note that this needs special handling for HA failover since it is not WAL-logged, and is not well explored.
3. If you do set advice, check on it in a few months, as shifting data and query patterns can make it counterproductive.

### Get started with ClickHouse Managed Postgres today

Interested in seeing how ClickHouse Managed Postgres works on your data? Get started with ClickHouse Cloud in minutes and receive $300 in free credits.

Interested in seeing how ClickHouse works on your data? Get started with ClickHouse Cloud in minutes and receive $300 in free credits.
I’ve built the same system three times now, at three different companies, for three different providers. It never has a name and it never appears on a roadmap, but it always goes the same way: the truth about your own customers lives in someone else’s database. The users live in an identity provider, the subscriptions in Stripe, the bounces in whatever sends your email, and your product needs that truth locally. So you subscribe to webhooks and keep a copy.

The first time, I thought I was building an endpoint: one route that parses the JSON and updates a row, an afternoon of work.

The afternoon grew into a week. First came signature verification, because an open endpoint that mutates your database is a hole. Then the dedup table, because deliveries arrive twice and the docs cheerfully call this “at-least-once.” Then the handler got a buffer, because a `membership.created` sometimes shows up before the `user.created` it points to. Then the bootstrap importer, because webhooks only tell you what happens *after* you subscribe, and it raced the live events, so it grew a locking scheme. And finally came the reconciliation cron: a job that crawls the provider’s list APIs at 3 a.m., diffs them against our tables, and quietly fixes what disagrees.

I want to be honest about what that cron is. It’s a written confession. It says: *I do not trust the copy I built, and I have no way to know when it’s wrong, so I will re-derive it from scratch every night, forever.*

The trust was gone for a reason. The drift never announces itself; ours was found by a support ticket. A customer had cancelled months earlier and our database still said `active`; some `customer.subscription.deleted` had evaporated between Stripe and us, and nothing anywhere was capable of noticing: not their dashboard, which showed the delivery as retried and eventually dropped, and not our logs, which cannot log a request that never arrived.

And that’s only the code. Every provider also brings its own dashboard. Three providers, three webhook configuration pages, each with its own idea of how endpoints are registered, which events exist, how test and live environments are kept apart, and where the signing secret lives. When something breaks, debugging is a tour: their delivery log in one tab, our logs in another, and a third tab for whichever dashboard I currently suspect. None of them look alike, and all of them have to be checked.

By the third time I built this system, I had stopped pretending. I budgeted for the whole stack up front (signatures, dedup, buffering, bootstrap, cron) and somewhere in the middle of writing my third dedup table, I finally asked the question I should have asked the first time.

What exactly am I reconstructing here?

## Notifications aren’t data

I was reconstructing an ordered log. Every one of those integrations was an attempt to turn a stream of notifications back into the ordered, complete, current history it came from.

And here’s the absurd part: that history *exists*. It has to, because it’s sitting inside the provider; it’s how they render their dashboards, their event pages, and their webhook replay tools. The provider takes their ordered log, shreds it into individual HTTP POSTs, fires them at my endpoint over a channel that guarantees neither order nor delivery, and then I reassemble the log on my side. So does every other consumer, independently, each with their own bugs.

It’s a jigsaw puzzle where the manufacturer had the original picture, cut it up, mailed me the pieces one at a time, lost a few in the post, mailed some twice, and printed nothing on the box. And when my assembled puzzle doesn’t match the original, their support team asks *me* which pieces I’m missing. I don’t know, and that’s the entire problem: nothing announces a gap.

None of this is any provider’s bug. Their webhooks work exactly as documented. The problem is what a webhook *is*: a notification, “something happened, here’s a POST about it.” Notifications are a fine way to trigger a side effect and a terrible way to transfer a dataset, and somewhere along the way we started using them for the second thing without noticing we’d changed jobs.

## How did this become the norm?

Nobody decided this. The term “webhook” was coined by Jeff Lindsay in 2007, and the early uses were genuinely good fits: GitHub’s post-receive hooks kicking off a CI build, or a payment event pinging your server so it could email a receipt. The job was to do a thing when a thing happens, and for that a POST is perfect: fire-and-forget is fine when forgetting is fine.

Webhooks spread because they were the cheapest thing a provider could ship (one HTTP POST) and the cheapest thing a consumer could receive (you already had a web server, so you just added a route). By the early 2010s, “we have webhooks” was a checkbox on every API’s landing page, and the checkbox never distinguished between two very different jobs:

1. Trigger a side effect: send the receipt, start the build, ping the channel.
2. Keep a copy of the provider’s data correct: this customer deleted their payment method, so update it in your DB too.

Job one is what webhooks were born for. Job two is what I was doing all three times, and job two is the one where every property webhooks lack (ordering, completeness, bootstrap, verifiability) is precisely the property you need.

We picked the tool that was lying on the table in 2007, and then we spent fifteen years compensating.

## The valley

There’s a concept in evolutionary biology I can’t stop thinking about: the fitness landscape. Peaks are good designs, valleys are bad ones, and populations climb whatever slope they happen to be standing on. The trap is the *local optimum*: a small hill that’s better than its immediate surroundings, so evolution parks there, even when a much higher peak exists across the valley. Getting to the higher peak means crossing through designs that are temporarily worse, and evolution doesn’t do temporarily worse.

![A hand-drawn fitness landscape: webhooks sit in a valley slowly filling with mitigation tooling, while the provider-served log sits on a higher peak across the way](https://weli.dev/images/evolutionary-valley.svg)

Webhooks-for-replication are a local optimum, and the proof is the pile of workarounds on the valley floor: signature schemes, dedup stores, idempotent handlers, retry queues with exponential backoff on the provider side and dead-letter queues behind them, webhook logs with replay tooling because consumers keep asking for replays, and my 3 a.m. cron.

The pile has an economy on top of it. Svix exists so providers don’t have to build webhook delivery; Hookdeck exists so consumers don’t have to build webhook ingestion. AWS will sell you the valley as managed services, with EventBridge to ingest your SaaS partners’ events, SQS to queue them, and Lambda to retry your handler, and you get to assemble the pipeline yourself. And an entire industry of connector platforms (Fivetran, Airbyte, every “unified API” startup) is, at bottom, pseudo-CDC: change data capture reconstructed from webhooks and polled list APIs, one bespoke connector at a time, sold as a product. Inside a database, capturing changes is a solved problem: it’s called replication, and it works because there’s a log. Between companies, we rebuild it out of doorbells.

My favorite workaround of them all is the local tunnel. Many providers ship a CLI like `stripe listen` that opens a tunnel to your laptop, because a webhook cannot reach localhost. Think about what that is: a product, built and maintained by the provider, reinvented multiple times, whose entire purpose is to work around the delivery direction of their own primitive. When multiple providers all need to ship a local tunnel so developers can *develop*, the primitive is answering the wrong question.

None of this tooling is bad engineering; it’s excellent engineering. That’s what a local optimum looks like: so much excellent engineering poured into the valley floor that the valley becomes comfortable, and nobody looks up.

But some providers have looked up. Stripe retains [thirty days of events](https://docs.stripe.com/api/events) and exposes [`/v1/events`](https://docs.stripe.com/api/events/list), an ordered, listable log, and [recommends reconciling against it](https://docs.stripe.com/webhooks/process-undelivered-events). WorkOS ships an [Events API](https://workos.com/docs/events/data-syncing/events-api), an ordered cursor-paginated log, and [their own docs recommend it over webhooks](https://workos.com/docs/events/data-syncing) when data consistency matters. The log keeps escaping, and each escape mints its own bespoke cursor semantics, its own bootstrap story, no way to verify a replica, and no shared contract, but the direction is unmistakable. This is convergent evolution: unrelated organisms, same environmental pressure, same wing.

The log exists everywhere, but the contract doesn’t.

## Could it be better?

Before reaching for a new design, it’s worth asking what any replacement would actually have to provide. My three integrations suggest the list: order, so changes can be applied without buffering; a way to start from nothing, so bootstrap isn’t a separate import racing the live events; deletes as data, so absence stops being the failure mode; resumability, so my downtime is my problem instead of a data-loss event; and some way to verify the result, so trust doesn’t decay into a 3 a.m. cron.

Measured against that list, the obvious candidates come up short. Polling the list APIs harder is the reconciliation cron promoted to a whole strategy: it can rebuild current state, but it burns rate limits discovering that mostly nothing changed, it says nothing about order, and a deleted object looks identical to an object that never existed. Managed delivery, whether that’s Svix on the provider’s side or EventBridge and SQS on mine, makes the pushes more reliable, but they are still pushes: still no bootstrap, still no verification, still notifications pretending to be a dataset. That path hardens the valley floor without climbing anywhere.

The third candidate is the one the providers keep half-building on their own: stop pushing altogether, and let the consumer read the log itself.

## Flip the arrow

So here’s the thought experiment. What if instead of the provider telling us when there is new information, we ask the provider what new information it has for us since we last checked?

![Hand-drawn sketch: on the left, webhooks push a tangle of arrows at your endpoint; on the right, you pull one ordered log with a cursor](https://weli.dev/images/webhooks-vs-log.svg)

Suppose a provider served one URL per collection, and that URL returned an ordered, cursor-addressed change log of full-state events. Ask without a cursor and you read from the beginning, which is your bootstrap, with no separate import and no race. Ask with a cursor and you resume where you left off. Your entire sync state is that cursor.

```
GET /feed/customers?cursor=01J9XQ4R
Prefer: stream

200 OK
Content-Type: application/x-ndjson

{"cursor":"01J9XR2M","operation":"upsert","object":{"id":"cus_123","plan":"pro"}}
{"cursor":"01J9XR2N","operation":"delete","object_id":"cus_099"}
```

Send `Prefer: stream` and the response never ends: each change arrives as it commits, over a connection *you* opened, using the same API key you use for the normal REST endpoints. Leave it off and you get a bounded page you can poll from a cron. It’s the same endpoint, the same events, the same cursors, and the same consumer code.

None of this is exotic; it’s a paginated GET. But walk back through my afternoon-that-grew and watch what it does to the stack:

- The dedup table is gone. Every event carries the object’s full current state, so applying one is a blind upsert keyed by id, and the same event applied twice produces the same result.
- The ordering buffer is gone, because the log is ordered.
- The bootstrap importer and its locking scheme are gone. A new consumer reads the same feed with no cursor, replays the collection, and carries straight on into live changes in one request.
- The lost delete is impossible. A tombstone is an event in the log, and it sits there until I read it. My cancelled customer cannot silently stay active, because absence stopped being the failure mode.
- The endpoint, the signatures, and the tunnel never exist in the first place. Every connection is consumer-initiated, and the loop runs behind NAT, on a laptop, or in a scheduled job.

The feed could carry one more thing. When a read reaches the end of the log, the provider could tell you what should be there: a count and a checksum of current state, at the cursor you now hold. You compare the two, and you *know* your replica is right instead of assuming it. My 3 a.m. cron, the written confession, becomes a comparison I’ve already made by the time I would have thought to schedule one.

## The fourth time

If a feed like that existed, the fourth time I build this system would be a loop: `GET` the feed, let “upsert” upsert the object into my db and “delete” delete it, and save the last cursor. That’s twenty lines with no route, no secrets to rotate, no queue, and no cron. The replica carries its own proof of correctness, and when someone asks which customers have an active subscription and a bouncing email address, the answer is a `JOIN` across local tables with no silent asterisk attached.

<del>Nobody</del> Almost nobody serves this today. That’s the catch, and it’s also the point.

## SCROLL

I wanted to see whether the idea survives being written down precisely, so I drafted it as a protocol: **SCROLL**, short for Synchronized Change Replication Over Line Logs, at [welidev.github.io/scroll](https://welidev.github.io/scroll/). It’s draft-00 in the request-for-comments sense of the phrase. It pins down the feed, the cursors, the streaming and polling modes, the checkpoints, tombstones, and retention, and it marks the places where my own confidence is lowest. It also doesn’t require waiting for providers, since a shim can synthesize a feed from any provider’s existing webhooks and list APIs, which is how I plan to find out where the design is wrong.

If you’ve lived in the valley, if you’ve written a dedup table or debugged a reconciliation cron or watched a delete evaporate, read it and tell me where it breaks. Disagreement is the desired response; silence is the failure mode.
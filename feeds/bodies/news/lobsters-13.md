I’ve been working on a ledger implementation in pure PostgreSQL called [pgledger](https://github.com/pgr0ss/pgledger). As I’ve written about previously, [I think more applications should use double-entry ledgers](https://www.pgrs.net/2025/06/17/double-entry-ledgers-missing-primitive-in-modern-software/).

However, once a ledger is integrated, it can be a bit hard to wrap your head around it visually. What are the money flows? What are the main set of accounts per user? Why is the balance in this account not what I expect?

In my work with companies, I’ve often tried to make the ledger more visual and understandable, either with a database dashboard like [Metabase](https://www.metabase.com/) or with custom in-app code.

The same way that pgledger is meant to be a common, reusable ledger across applications, I thought we could have a common, reusable visualization tool. And thus [pgledger-ui](https://github.com/pgr0ss/pgledger-ui) was born.

## Screenshot

This is what it looks like to view a ledger account, showing the account details, the most common counterparty accounts, a chart of balance over time, and the detailed transfer entries:

[![pgledger-ui account page](https://github.com/pgr0ss/pgledger-ui/blob/dbbf6ca48d477bbf80552cb1bd741eb96839d0d1/screenshots/light/03-account-entries.png?raw=true)](https://github.com/pgr0ss/pgledger-ui/blob/dbbf6ca48d477bbf80552cb1bd741eb96839d0d1/screenshots/light/03-account-entries.png?raw=true)

## Overview

In general, `pgledger-ui` is pretty simple. It runs database queries and shows them in a webpage. There are some charts and extra aggregate information. And the whole thing is bundled into a single Go binary:

```
go run github.com/pgr0ss/pgledger-ui@latest --database-url postgres://user:pass@host:5432/dbname
```

Beyond this, there are a few main ideas baked into pgledger-ui:

### Everything Is Linked and Clickable

Often, when debugging an issue, you start by realizing a ledger account doesn’t have the balance you expect. Then, you want to see the transfers in and out of that account. And maybe you want to trace a given metadata key across transfers (e.g. the `payment_id`). As you continue debugging, you may follow an account to a transfer to another account and so on. With pgledger-ui, each entity shows the related entities, and you can click on any of them to trace a flow. This even includes metadata keys, so you can see related transfers which share the same key/value pair.

### Search

It should be easy to find what you want, so pgledger-ui has a single, universal search box. You can search by id, account name, idempotency key, metadata values, etc., and it will show you all matches across all entities. For example, if you name your accounts hierarchically (e.g. `user01.available`, `user01.pending`, etc.) you can search for `user01` and see all accounts and transfers for that user.

### Information Density

I like interfaces which are information dense, without being overwhelming. The goal is to show a lot of useful information in each page, and make it easy to scan for what you need.

### Column-Based Views

Normally, when you query data from a database, you get row-based results. However, I find that visualizing ledgers in a columnar format is often more useful.

For example, say you are looking at all of the transfer entries for a given payment. The results may come back like this:

```
       kind       |          name          | amount
------------------+------------------------+--------
 payment_created  | user1.external         | -50.00
 payment_created  | user1.receivables      |  50.00
 payment_received | user1.receivables      | -49.50
 payment_received | user1.available        |  49.50
 refund_created   | user1.available        | -20.00
 refund_created   | user1.pending_outbound |  20.00
 refund_sent      | user1.pending_outbound | -20.00
 refund_sent      | user1.external         |  20.00
```

But a columnar view of that same data looks like:

```
       kind       | user1.external | user1.receivables | user1.available | user1.pending_outbound
------------------+----------------+-------------------+-----------------+------------------------
 payment_created  |         -50.00 |             50.00 |                 |
 payment_received |                |            -49.50 |           49.50 |
 refund_created   |                |                   |          -20.00 |                  20.00
 refund_sent      |          20.00 |                   |                 |                 -20.00
```

(Example from the [pgledger reconciliation.sql.out script](https://github.com/pgr0ss/pgledger/blob/fee1aa05630f5af8cb3196749aa4d998162a9862/examples/reconciliation.sql.out#L148-L224))

PostgreSQL calls this a [crosstab](https://www.postgresql.org/docs/current/tablefunc.html#TABLEFUNC-FUNCTIONS-CROSSTAB-TEXT) (or [crosstabview](https://wiki.postgresql.org/wiki/Crosstabview) in psql). A pivot table in a spreadsheet may be similar. And it’s a common way to visualize a ledger<sup>[1](https://www.pgrs.net/2026/11/19/visualizing-a-ledger-with-pgledger-ui/#fn:1)</sup>.

This type of view exists in pgledger-ui as well, especially if you’re tracing a flow via a metadata key:

[![pgledger-ui trace crosstab view](https://github.com/pgr0ss/pgledger-ui/blob/dbbf6ca48d477bbf80552cb1bd741eb96839d0d1/screenshots/light/05-trace-crosstab.png?raw=true)](https://github.com/pgr0ss/pgledger-ui/blob/dbbf6ca48d477bbf80552cb1bd741eb96839d0d1/screenshots/light/05-trace-crosstab.png?raw=true)

And you can separate the in/out flows, making it resemble a standard ledger T-account view:

[![pgledger-ui trace in/out view](https://github.com/pgr0ss/pgledger-ui/blob/dbbf6ca48d477bbf80552cb1bd741eb96839d0d1/screenshots/light/06-trace-inout.png?raw=true)](https://github.com/pgr0ss/pgledger-ui/blob/dbbf6ca48d477bbf80552cb1bd741eb96839d0d1/screenshots/light/06-trace-inout.png?raw=true)

## Feedback Please

Please check out [pgledger-ui](https://github.com/pgr0ss/pgledger-ui), and I’d love to hear what you think, especially if you work with pgledger or other ledgers today. Are there other useful visualizations or tools you’ve seen in this space? And if pgledger-ui is something that you are interested in using, please let me know.
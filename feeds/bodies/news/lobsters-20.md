Many code  blocks throughout this website are executable on
the WASM implementation of delightql.  Hovering over a code block
may show a "play" button that can be used to execute on the
demo database.

DelightQL is a query language that transpiles to SQL. Its syntax draws on logic
and functional programming to make queries succinct and reusable. It
offers the traditional abstractions of a modern programming language while
retaining all of SQL's relational power.

```
users(*)
  ~> {country, "users":
        ~> {first_name, last_name}} as users_by_country
```

## Some Runnable Examples[¶](https://delightql.org#some-runnable-examples)

Drop a column without spelling out all the columns you want to keep.

```
users(*) |> -(email, created_at)
```

Column names can be a selection pattern, not just a list.

```
users(*) |> (/_name/)
```

Apply a function to selected columns; leave the rest alone.

```
users(*) |> $(upper:())(first_name, last_name)
```

Change two names without rebuilding the projection.

```
users(*) |> *(first_name as given_name, last_name as family_name)
```

Describe the output shape directly, including independent collections.

```
users(*)
  ~> {
       country,
       "people": ~> {first_name, last_name},
       "statuses": ~> [status]
     } as by_country
```

Turn country and status values into the keys of a nested object.

```
users(*) as u
  |> %(~> u.country:~> u.status:~> {u.first_name})
```

A collection is not a dead end. Query inside it and retain its outer context.

```
users(*)
  |> %(country ~> {first_name, last_name, age} as people) : by_country

by_country(*).people(*)
  |> %(country ~> sum:(age), avg:(age))
```

Name an expression once, then use it like a built-in.

```
full_name:(first, last) : :"{first} {last}"

users(*) |> (id, full_name:(first_name, last_name) as name)
```

Put a correlated query behind a function call.

```
order_count:(user_id) : orders:(, orders.user_id = user_id ~> count:(*))

users(*) |> (last_name, order_count:(id) as num_orders)
```

Functions can take functions. Here, the same transformation is applied twice.

```
apply_twice:(f:(), x) : x >> f:() >> f:()

users(*) |> (first_name, apply_twice:(:(@ * 2), age) as quadrupled_age)
```

Pipe a value through functions in the order you read them.

```
tidy:(s) : s >> trim:() >> lower:()

users(*) |> (first_name, email >> tidy:() as contact)
```

Combine different headings by name, padding missing columns with NULL.

```
users_2022(*) ; users_2023(*)
```

Turn subject values into columns.

```
_(name, subject, score @
  "Alice", "Maths", 90;
  "Alice", "Music", 85;
  "Bob", "Maths", 75;
  "Bob", "Music", 80),
  subject in ("Maths"; "Music")
  |> %(name ~> score of subject)
```

Turn columns into rows using an inline table that reads the current product.

```
products(*),
_(attribute, value @
  "price", price;
  "cost", cost)
|> (id, name, attribute, value)
```

Filter, select, sort, then take five.

```
users(*), status = "active"
  |> (first_name, country, age)
  |> #(age desc), #<5
```

The question mark keeps users even when they have no matching order.

```
users(*) as u, orders?(*) as o, u.id = o.user_id
  |> (u.first_name, u.last_name, o.total, o.status)
```

Give each aggregate its own condition.

```
orders(*) |> %(~>
  sum:(total | status = "completed") as completed,
  sum:(total | status = "pending") as pending
)
```

Rank balances within each country without collapsing the rows.

```
users(*) |> (
  first_name, country, balance,
  row_number:(<~ %(country), #(balance desc)) as country_balance_rank
)
```

## Target SQL[¶](https://delightql.org#target-sql)

The goal for delightql is to have transpilation targets for all
major SQL dialects. Currently, delightql supports SQLite pretty well and DuckDB sorta well.
The alpha process will increase coverage of other target SQL dialects.

## Implementation[¶](https://delightql.org#implementation)

Warning

Delightql is in alpha and should **not** be used in production
without understanding the risks.

Delightql is implemented in Rust and uses tree-sitter as part of its
[compiler front-end](https://github.com/reverendpaco/delightql/blob/main/grammar/grammar.js).
It comes with a CLI for all major flavors of UNIX.
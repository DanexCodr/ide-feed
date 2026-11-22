SQLite is one of my favorite database technologies. It's a full SQL database, designed as an embeddable library, that stores all its data in a single file. The `sqlite3` command line tool is great too. You point it at a file and run queries. There's no server to run.

At the other end of the spectrum is Postgres. It's the most capable general purpose SQL database, trusted in production at scale, and is something of an industry standard. With that comes complexity, starting with the fact that it's client-server.

SQLite is a natural fit for software that needs a database but isn't meant to be deployed in the cloud at scale: desktop apps, self-hosted tools, things you run locally. These applications can use SQLite and manage it themselves, so you barely know there's a database involved.

So when you find self-hostable open source software you'd like to run on your own computer, it can be daunting when it says it requires Postgres. Now you're responsible for setting up a database and getting it ready for the software to use.

Sure, you can run Postgres in Docker, and plenty of projects recommend it. But now you have two dependencies. If you don't already have Docker, you have to install it, which can mean a VM and a daemon on your machine. Then you have to run Postgres in it and make sure it's running whenever you use the software. That's a lot just to try something you don't know you want yet.

Wouldn't it be great to have the SQLite experience, but with Postgres?

That's 
              [miniPG](https://progrium.github.io/minipg/)
              . It isn't Postgres as a library. There's already a WASM project for that, reasonably called [PGlite](https://pglite.dev/). miniPG is closer to the SQLite CLI: a single program that embeds a full Postgres server and client, wrapped up so you can use it the way you'd use `sqlite3`. Point it at a path, that path becomes the database, and you can run queries against it right away. There's no server to set up or keep running.

Jumping into a new Postgres database to try something out or debug it is now easier than using Postgres in a Docker container, and you don't need Docker at all. And miniPG still provides a fully functional Postgres server for software that needs one. In many cases, you can just launch an open source program that looks for its Postgres config in the environment with miniPG.

## miniPG in 30 seconds

miniPG comes as a single, self-contained executable. You can just point it at a directory and run a query. There's no server to start, nothing to configure, and the result comes back immediately.

```
minipg ./mydb "create table notes (id serial, body text)"
minipg ./mydb "insert into notes (body) values ('hello')"
minipg ./mydb "select * from notes"
```

That directory is the database. When nothing is using it, it's just files on disk. You can copy it, back it up, or delete it.

This is actually real Postgres, not a compatibility layer, and this binary compiles to Mac, Windows, and Linux.

When some software expects a Postgres server, miniPG can be one:

```
minipg serve ./mydb -p 5432
```

Like I mentioned before, it can even launch programs with environment variables that configure it for this Postgres database:

```
minipg run ./mydb -- some-tool
```

When the program is terminated, there's no database daemon to leave around or remember to stop. Only the data itself is kept right there on disk, ready to be used next time.

Instructions for getting it and even an interactive demo are available on the 
              [miniPG website](https://progrium.github.io/minipg/)
              .

## Who is it for?

Software people, from developers to open source power users, and agents too, can use miniPG whenever they'd reach for SQLite but need Postgres.

- Running software that only supports Postgres. This is what got me started. Self-hosting a tool shouldn't always mean operating a database server first.
- Embedding Postgres in your own programs. If your tool needs Postgres, and PGlite doesn't cut it, you can ship and use miniPG. Users who don't care won't have to think about it, and users who want control can use it like sqlite3 to work with their data.
- SQLite-style apps that need Postgres features. JSONB, full text search, window functions, extensions like pgvector or PostGIS. Postgres does so much more than SQLite, but it often wasn't worth the dependency.
- Learning and experimenting with Postgres. No server, no config. Point it at a directory and start typing SQL.
- Tests, local dev, and agents. A throwaway database per test, or a local copy of the same database you run in production, without Docker. Agents can spin up a real Postgres for a task and throw it away when they're done.

This really makes Postgres more viable for scenarios it wasn't before. I'd love to hear the use cases I haven't thought of.

## Embedding Real Postgres

miniPG is the result of several attempts at embedding real Postgres into a standalone, cross platform binary.

### Attempt 1: PGlite

The obvious place to start was [PGlite](https://pglite.dev/). The name says it all, and in a sense it delivers: it's Postgres compiled to WebAssembly. In Go, you can load the module with the wazero runtime, run Postgres inside your program, and have your app connect to it. That's very close to the SQLite library experience.

Brad Fitzpatrick even made a 
              [proof of concept](https://github.com/bradfitz/gopglite)
              that does this in a way that makes PGlite work as a driver for the standard Go SQL package.

The catch is that PGlite only supports a single connection and a single session. Software written for a real Postgres server often assumes it can have more. A common pattern is to start a transaction, then make another query on a separate connection before committing. With only one connection, that second query waits for a transaction that's waiting on it. The app I was trying to run deadlocked.

### Attempt 2: a VM in a webview

If I needed real Postgres, I could run real Postgres in a virtual machine I could embed. I have a soft spot for using webviews as portable containers, so I ran [v86](https://github.com/copy/v86), an x86 emulator for the browser, inside one, and booted a full Postgres server in it.

The rest was plumbing. The headless webview opens a WebSocket back to the host program. Postgres connections are tunneled through it, and Postgres writes its data to a mount served over the same socket. The benefit of this approach is whatever platform the host program runs on, Postgres is always the same build running in the same VM.

I even built 
              [webframe](https://github.com/tractordev/webframe)
              for this, a library and CLI for running a native system webview headlessly.

The result was a proof of concept I called postgres-standalone: one binary, any platform, give it a port and a data directory, and you get a full Postgres server. It worked!

However, it was also an order of magnitude slower than native. Postgres in a VM in WebAssembly in a browser. Initializing and checking a database took a while. In the best case, on my M3 MacBook, it took 7 seconds before it would accept a connection.

I'd already written a design doc for the SQLite-style CLI: give it a directory, run a query, no server to run. On this stack, though, every `SELECT *` would sit there for 7 seconds first. That ruins the experience, so I had to shelve it. I had proven that embeddable Postgres was possible, just not pleasant.

### Attempt 3: Hyper9

Later, for unrelated reasons, I built 
              [Hyper9](https://github.com/progrium/hyper9)
              . Inspired by system API translation, an approach that Wine and Valve's Proton are built on, combined with a unique way to use hypervisors, Hyper9 lets you run Plan 9 executables at near native speed on all platforms.

I'll be posting more about Plan 9 soon, but with a little extra magic, I was able to run the same Postgres at near native speed, in isolation, on all platforms. It's effectively the same approach as the previous attempt, but now without the slowdown.

Startup went from 7 seconds to 800ms. So I dusted off the design doc and built it. PGlite was taken, so postgres-standalone became miniPG.

## What it isn't

miniPG isn't a replacement for real Postgres deployments. If you're running in the cloud, using replicas, or serving many users over many connections, use Postgres the normal way.

miniPG is for local, single-user programs: the places SQLite would fit, but you need Postgres.

That said, go ahead and see how far you can push it!

## Try it

I'd really like to see how miniPG holds up in the wild, especially across different platforms and architectures. Please try it and tell me what breaks.

If this works, it proves a model that goes well beyond Postgres: taking complicated systems and packaging them as a single binary for more specific use cases. That's the part I find most exciting, and it's one of many new possibilities Hyper9 enables.
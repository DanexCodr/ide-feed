It took months, but here we are: **the whole Pimalaya CLI family is released at once**, at the top of the first stable version of the [pimdir](https://github.com/pimalaya/pimdir) standard. Here the list:

- Himalaya `v3.0.0`, the CLI to manage mails.
- Neverest `v1.0.0`, the CLI to synchronize mails, contacts and calendars.
- Cardamum `v1.0.0`, the CLI to manage contacts.
- Calendula `v1.0.0`, the CLI to manage calendars.
- Carillon `v1.0.0`, the CLI to watch mailboxes, address books and calendars, and fire hooks.
- Ortie `v3.0.0`, the CLI to manage OAuth tokens (released 5 days earlier).
- Comodoro `v3.0.0`, the CLI to manage timers (released 5 days earlier as well).
- pimdir storage `v1.0.0`, sync `v1.0.0` and search `v1.0.0`, plus its Rust implementation io-pimdir `v1.0.0`.

Most of them are majors, and they all break something for somebody. This post explains why, how, and where it goes from here. It is long, feel free to jump to the tool you care about.

## Why everything at once

In [Another year with NLnet](https://blog.pimalaya.org/another-year-with-nlnet/) I said this year was about consolidation and about a standard for PIM on disk. This release is the result of both.

The thing is, every piece is now connected:

- All the CLIs sit on the same libs (IMAP, SMTP, JMAP, DAV, the Google and Microsoft APIs, OAuth, HTTP, TLS).
- All the CLIs share the same kit: the same configuration loader, the same output contract, the same exit codes, the same REPL and the same MCP server.
- Neverest syncs every account into one pimdir store, and Himalaya, Cardamum, Calendula and Carillon read it, search it and queue their writes into it.

Releasing them one by one meant releasing tools that disagree with each other: one version of the store here, another version of the output there. So I decided to bring every tool to release level first, then to release them all together. It took way longer than I wanted, but this way what you install today is one coherent family.

The other reason is the contract. The CLIs are not only used by humans anymore: they are used by scripts, by frontends (the Vim plugin, the TUI, the Android app), and by AI agents through MCP. All of them need a **stable, versioned contract**: the same JSON shapes, the same error codes, the same exit codes. Majors are the right moment to fix it, and from now on it should not move anymore without a new major.

## How it was done

Few things made this release possible.

**Specs before code.** Every repository has a cairn/ folder holding its living spec, its change proposals and a dated log. Every behaviour change goes through a proposal, then gets folded into the spec. This way the truth is written somewhere, and not only in my head.

**One shared kit.** The [pimalaya-cli](https://github.com/pimalaya/cli) and [pimalaya-config](https://github.com/pimalaya/config) libs hold everything the CLIs have in common: the output contract, the error codes, the REPL, the MCP server, the configuration loading. In fact most of the work of this release was moving code from the CLIs into this kit, and deleting the copies.

**One unified API, as a union.** Before, the commands shared by every backend were the *intersection* of what the backends could do: if one backend could not do it, nobody could. Now it is the *union*: each backend registers the capabilities it really serves, with the same observable result as the others, and a command an account cannot serve fails before even connecting, with a clear `capability-missing` code.

**Measured gates for pimdir.** Audits always find something, so "no new finding" never ends. Instead, I built a test generator that produces stores, remote states and an oracle from a seed, and ran campaigns of 4,180 jobs against io-pimdir: crashes injected at every step, the search index checked against a full rebuild after each event, the sync engine replayed against scripted servers. The rule was simple: 2 campaigns in a row without any spec break, then freeze. Campaign 1 found one, campaigns 2 and 3 were clean, a late fix restarted the count, then campaigns 4 and 5 were clean. Freeze.

**Live tests on real providers.** Every CLI was tested against real accounts: Google, Microsoft, Fastmail and iCloud, plus few Chinese providers for Himalaya (QQ, 163, 139). A last "live night" just before the release found few bugs that went straight into the libs.

**Libs first, apps after.** The libs were released between the 13th and the 25th of November, the apps then moved to them without any patch or git pin. Everything you install comes from crates.io.

## pimdir `v1`, the foundation

pimdir is a local-first standard for personal information: mails, contacts, calendars, tasks and files in **one portable store**, kept as a replica of every source, and searchable with one query language. A store is one SQLite file plus a content-addressed blob directory, the same on every OS and architecture. I already explained why such a standard is needed in [Another year with NLnet](https://blog.pimalaya.org/another-year-with-nlnet/), and how the Android app became its first full implementation in [Pimalaya for Android enters closed alpha](https://blog.pimalaya.org/pimalaya-android-closed-alpha/).

It comes in 3 parts, versioned separately:

- Storage: the store itself (schema, blobs, summaries, change feed, retention, action queue).
- Sync: how sources are reconciled through the store (merge rules, the connector seam).
- Search: the derived index and the query language.

They are released together because a store holds sync state that follows the sync part, and the query language binds every program that offers search.

What `v1` means: *schema version 1 never changes*, every schema change is a migration, and a minor version only adds test cases. You can implement it in any language that speaks SQLite, use the I/O-free core of io-pimdir (like the Android app does, on the platform SQLite), or use its std client.

Few days before the freeze, I compared it with [notmuch](https://notmuchmail.org/), which is the reference in this area. They do not do the same job (notmuch indexes mail files it does not own, pimdir owns the bodies, syncs them and holds other domains), but the search can be compared. On a store of 1 million messages from the Enron corpus, pimdir was ahead of notmuch on 50 of the 51 query measures and tied the last one, imported the million faster, and used a third of the memory. Stemming, regex and per-thread queries are still missing, they are on the list.

One warning for the early adopters: **a store written by a draft version is refused**, never migrated. Sync it till nothing is pending with the last draft binary, move its directory aside, then let a release create and sync a new one.

Useful links:

- pimdir repository, with STORAGE.md, SYNC.md, SEARCH.md and the informative OVERVIEW.md
- pimdir changelog
- io-pimdir repository, release notes and API documentation

## Where did the wizard go?

This is the change many of you will not like, so let me explain it properly.

Every CLI had a configuration wizard: you typed your email address, it discovered the servers, asked for the password, stored it in your keyring, and wrote the TOML for you. It is gone, from every CLI.

**Why.** Few reasons, piled up:

- It was already broken. For Gmail, Microsoft and JMAP, the Himalaya wizard handed the sign-in to ortie configure, which Ortie v3 removed. The path it proposed first for the most common providers simply failed.
- It cost a lot. The Himalaya wizard alone was 14 files and about 4,000 lines, and 1.90 MB of a 20.3 MB binary. Same story in each CLI: server discovery, a keyring dialogue, a review screen and a TOML writer, inside tools whose job is to manage mails, contacts or calendars.
- It served 2 audiences badly. Power users write their config from the sample anyway. People who need a guided setup are better served by an app than by a prompt in a terminal.
- The CLIs moved to plain text and JSON, with no terminal handling at all. A wizard is exactly the kind of interactive layer that does not fit anymore.

**What replaces it.**

- A first-run welcome. Run a CLI without configuration, and it names the missing file and the sample to start from. At a terminal, it even prints the exact commands to copy the sample in place, then the first command to run.
- A tested config.sample.toml, shipped in the packages and the release archives under share/doc. The samples are parsed by the test suites, so they cannot silently rot anymore.
- Ortie for OAuth, with ready-made Google, Microsoft and Fastmail accounts to paste from its README, using Pimalaya's own clients.
- [pim-discovery](https://github.com/pimalaya/io-pim-discovery), for the discovery part of the wizard. It is the CLI of io-pim-discovery, the lib the wizards used (and the Android app still uses): pim-discovery all user@fastmail.com finds the IMAP, SMTP, JMAP, CalDAV and CardDAV servers of an address, and tells you what vouches for each answer. It is not officially released yet, but you can install it with cargo install io-pim-discovery --locked --features cli.
- Guided setup in frontends. The Android app keeps its onboarding (you type your email address, it finds the rest), and Himalaya TUI has a draft to bring the same flow to the terminal.

**The direction.** The CLIs are now *low-level* tools: plain text to glance at, JSON for scripts, frontends and agents. Comfort (tables, colours, relative dates, guided setups, rich composition) belongs to frontends. In fact this is not new: it is the same split that started the whole project, back when the logic left the Vim plugin. The CLI was always supposed to be the backend a frontend needs. This release just goes all the way.

I know some of you used the wizard to get started, and that copying a sample feels like a step back. If the welcome or the samples are not clear enough, it is a bug: please open an issue, I would rather fix the docs than bring back a second setup system per CLI.

## Himalaya `v3`

Himalaya is now a low-level CLI over a **unified mail API**: the same commands on every backend, the protocol-specific ones next to them, plain text for a glance and `--json` for the rest.

Backends: IMAP, SMTP, ManageSieve, JMAP, the Gmail API, Microsoft Graph, Maildir (with a new `maildir++` layout for Dovecot and Courier stores), mbox, and pimdir. The README has recipes for Proton Mail (through Bridge), Fastmail, Gmail, Outlook, Posteo and iCloud.

What is new:

- himalaya repl, one command per line, with clients connected once for the whole session.
- himalaya mcp, an MCP server over stdio. Writes are refused unless you pass --allow-write, and sending is behind its own --allow-send.
- The pimdir query language for envelope search on every backend (from:alice date:2d).
- vacation get|set on JMAP and Gmail, message reply --all, mutual TLS, an account-level tls table.
- A stable code on every failure, an errors list per item, and a JSON Schema for every command.

What is gone: the wizard, the m2dir backend (superseded by pimdir), the table and colour options, `HIMALAYA_CONFIG`. Unknown configuration keys are now refused, JSON keys are camelCase, and the v2 search syntax needs to be rewritten. The [migration guide](https://github.com/pimalaya/himalaya/blob/master/MIGRATION.md) lists everything, with a full table for the queries.

Useful links:

## Neverest `v1`

Neverest is rebuilt around the pimdir store: **every account syncs into one shared store**, which the other CLIs read, search and queue their writes into. It syncs mails, contacts and calendars over IMAP, Gmail, Microsoft Graph, Google Calendar, Google People, CalDAV and CardDAV.

Highlights:

- Two-way, one-way or migration syncs.
- Three-way merge of cards and events: a real conflict is parked for you to decide, never lost.
- Retention: a remote deletion never removes the local copy, only an explicit purge does.
- Writes queued by Himalaya, Cardamum and Calendula are applied offline, sending included.
- Paged, newest-first listings that resume after an interruption, back-off on throttling, and a clean stop on Ctrl-C.

JMAP sources are not supported yet (it is a draft), so Fastmail syncs over IMAP, CardDAV and CalDAV for now. Coming from `v0.x`? Your configuration and state are not carried over: start from the config.sample.toml, then run `neverest sync --init`.

Useful links:

- Repository
- Release notes
- Changelog
- Sample configuration

## Cardamum `v1`

The first stable release of Cardamum: a low-level CLI over a **unified contacts API**, with the same commands on CardDAV, JMAP, Microsoft Graph, Google People, vdir and pimdir.

`card search` speaks the pimdir query language on every backend, `account capability` shows what an account serves without connecting, and you get the REPL and the MCP server like the others. Editing a card is left to a composer such as [tcard](https://github.com/pimalaya/tcard). The wizard and the `discover` route are gone.

Useful links:

- Repository
- Release notes
- Changelog
- Sample configuration
- tcard, to compose cards

## Calendula `v1`

Same story for calendars: the same commands on CalDAV, JMAP (new), Google Calendar, Microsoft Graph, vdir and pimdir.

New: `event search`, recurrence expansion, attendees and alarms, online meetings (`--online-meeting`), invitation replies through pimdir, and an agenda that draws a month or a year like cal(1) does. Editing an event is left to a composer such as [tcal](https://github.com/pimalaya/tcal). The wizard, the tables and colours, and the `todo` and `journal` commands are gone: tasks and journals will move to dedicated tools (Unfog and Journal), not released yet.

Useful links:

- Repository
- Release notes
- Changelog
- Sample configuration
- tcal, to compose events

## Carillon `v1`

Carillon is a local watcher that **fires hooks on what changes** in your mailboxes, address books and calendars, over IMAP, JMAP, Maildir, CalDAV, CardDAV, Microsoft Graph, the Google APIs and the pimdir store. It uses push where the server offers it (IMAP IDLE, the JMAP event stream) and polls elsewhere. A hook runs a command, shows a desktop notification, or both.

New in `v1`: a pimdir backend, `on-alarm-trigger` for the alarms of events and tasks, `on-birthday-trigger` for birthdays and anniversaries, a per-hook timeout, and a report of what moved while an IMAP or Gmail session was lost. Hooks now take the same shape as Comodoro's.

Useful links:

- Repository
- Release notes
- Changelog
- Sample configuration

## Ortie `v3`

Ortie manages OAuth tokens for the other tools. `v3` aligns it on the rest of the family: ready-made Google, Microsoft and Fastmail accounts to paste, token revocation, an `auth listen` to catch a redirection handed off from another machine, account checks, a REPL, and an MCP server that **never hands the token to the agent**. The wizard and the hooks are gone (the storage write command does what a hook did).

Useful links:

## Comodoro `v3`

Comodoro manages timers: one server owns a timer, any number of clients drive it, over a local socket or TCP. `v3` joins the same standard: `comodoro watch` feeds a status bar without polling, hooks get the cycle name and duration, plus the welcome, account checks, a REPL and an MCP server. Comodoro is now a binary only: the library is gone, and the open JSON-RPC protocol is the contract for third parties.

Useful links:

## The libs

None of the above would exist without the libs below, all released in November on crates.io:

- The shared kit: pimalaya-cli v0.8, pimalaya-config v0.6, pimalaya-stream v0.4.
- The content models: mime-rs v0.2, vcard-rs v0.6, ical-rs v0.7.
- The protocols: io-imap v0.12, io-smtp v0.10, io-sasl v0.3, io-http v0.9, io-jmap v0.11, io-webdav v0.14, io-managesieve v0.6, io-oauth v0.8, io-proxy v0.3, io-pim-discovery v0.15.
- The provider APIs: io-gmail v0.10, io-msgraph v0.11, io-gcal v0.6, io-gpeople v0.9, io-gtasks v0.3.
- The local formats: io-maildir v0.5, io-mbox v0.2, io-vdir v0.3, and io-pimdir v1.0.

They are all I/O-free, as usual: feel free to build your own tools at the top of them.

## Installing and upgrading

Each README lists the ways to install: prebuilt binaries from the GitHub releases (or the install.sh script), `cargo install --locked`, Nix, and the APT, DNF and Homebrew repositories at [pkg.pimalaya.org](https://pkg.pimalaya.org). The packages are landing there over the coming days, and the nixpkgs and home-manager updates are on their way.

About upgrading:

- Himalaya, Ortie and Comodoro have a MIGRATION.md, follow it.
- Neverest, Cardamum, Calendula and Carillon come from v0.x: there is no migration guide, start from the config.sample.toml.
- pimdir stores written by a draft are refused, see the procedure above.

## What comes next

- Neverest `v1.0.1`, with few fixes already on their way, then JMAP sources.
- Himalaya TUI, with the onboarding of the Android app.
- The Android app, already moved to pimdir sync v1 and io-pimdir v1.0.
- pimdir search: stemming, regex, per-thread queries, local labels and properties.
- Tasks and journals, through Unfog and Journal.
- Packaging: nixpkgs, home-manager and pkg.pimalaya.org for every tool.

## Thank you

Special thanks to the [NLnet foundation](https://nlnet.nl/) and the European Commission's [NGI](https://www.ngi.eu/) initiative, for the financial support through [NGI Zero Core](https://nlnet.nl/project/Pimalaya-PIM/) and now the [NGI Zero Commons Fund](https://nlnet.nl/project/Pimalaya-pimdir/). This kind of slow, deep work is only possible thanks to them.

And thank you to everyone who reported bugs, tested betas, or simply waited patiently while everything was being rebuilt. Any feedback is welcomed, on [GitHub](https://github.com/pimalaya), on [Matrix](https://matrix.to/#/#pimalaya:matrix.org) or on [Mastodon](https://fosstodon.org/@pimalaya). Let me know how it goes!
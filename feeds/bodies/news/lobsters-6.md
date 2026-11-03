*git-loom* weaves your feature branches into a single integration branch, so you can work on all of them at once — committing, amending, splitting and reordering — without ever switching branches. It is inspired by [jujutsu](https://github.com/martinvonz/jj) and [GitButler](https://gitbutler.com/).

![git-loom status](https://narnaud.github.io/git-loom/assets/git-loom-status-750.png)![git-loom status](https://narnaud.github.io/git-loom/assets/git-loom-status-750.png)

From the command line, with the status pinned on the left:

The same operations from the interactive [`git loom tui`](https://narnaud.github.io/git-loom/commands/tui.html):

### [Integration Branch](https://narnaud.github.io/git-loom/introduction.html#integration-branch)

The branch you work on. It tracks a remote branch (e.g. `origin/main`) and merges in all your feature branches, so you build and test them together. Create it with [`git loom init`](https://narnaud.github.io/git-loom/commands/init.html).

### [Feature Branches](https://narnaud.github.io/git-loom/introduction.html#feature-branches)

Independent branches woven into the integration branch, each pushed and reviewed on its own. You manage them from the integration branch:

- `commit` commits to a feature branch, creating it if needed
- `fold` amends, fixes up, or moves commits and files between branches
- `push` pushes a branch and opens its pull request

> Tip
>
> [`git loom commit -b <name>`](https://narnaud.github.io/git-loom/commands/commit.html) is the usual way to start a branch. [`git loom branch`](https://narnaud.github.io/git-loom/commands/branch.html) is for creating an empty branch ahead of time, or turning existing commits into one.

Each feature branch sits on the integration branch as a side branch joined by a merge, which is what `git loom status` draws. Every loom command rewrites history to keep that shape, so you never rebase by hand.

A rewrite keeps the modification time of files whose content did not change, so your build tool does not rebuild everything. Pause watcher-driven builds (`cargo watch`, build on save) while a loom command runs: they may compile half-rewritten files.

`git loom status` labels every branch, commit and file with a short ID (`fa`, `pop`, `ma`) that you type in other commands instead of hashes, names or paths.

Commit IDs are persistent: they come from a `Change-Id` trailer that loom adds to every commit it creates (see [`loom.changeId`](https://narnaud.github.io/git-loom/configuration.html#loomchangeid)), so they survive rewrites and you can chain commands on the same ID.

```bash
# Create an integration branch from your main branch
git checkout main
git loom init

# Commit everything to a new feature branch, then add a second commit
git loom commit -b feature-auth -m "add login form" zz
git loom commit -b feature-auth -m "improve login form" zz

# See the branch-aware status
git loom

# Push the branch for review
git loom push feature-auth
```

Next: the [Tutorial](https://narnaud.github.io/git-loom/guides/tutorial.html), or [Working with AI Agents](https://narnaud.github.io/git-loom/guides/agents.html) to let Claude Code drive loom for you.
`jj` provides primitives for version control that are simple to learn, but elegantly compose into powerful workflows. Features like automatic rebase and native undo soften the sharp edges of Git. Eventually, you’ll organically discover new powerful workflows that would be too cumbersome to attempt with most other VCS tools.

If you work in a Git repository, you can try it today. Jujutsu and Git can be used [side-by-side in the same repository](https://docs.jj-vcs.dev/latest/git-experts/#git-can-be-used-side-by-side-in-the-same-repository), so you can try out `jj` on a `git` repo on your own, without fully ejecting from `git`.

Personally, I think `jj` considerably boosts my effectiveness, because it allows me to keep VCS bookkeeping out of my working memory. Automatic rebasing also makes stacked diff workflows quite easy, and reduces thrashing of my working memory. It’s also just a fun tool to use.

Official installation instructions are [here](https://docs.jj-vcs.dev/latest/install-and-setup/), but here are a few common methods:

In an existing `git` repository, run:

From here on, `jj` and `git` repo state will be synchronized automatically.

To set your user details globally, run commands like these:

You can edit `jj`’s TOML configuration for your user in an editor with:

In addition to the `--user` scope, `jj config` also has `--repo` and `--workspace` scopes. View the merged config with:

A **commit**, also called a **revision**, is essentially the same thing as a `git` commit. It represents a snapshot of repository state that descends from one or more parent repository snapshots. It is often visualized as a diff against a singular parent commit, or in the case of a merge commit, the diff against multiple parent commits once merged.

When using a Git repo backend, the `jj` **commit ID** is the same as the `git` commit ID: a hash formatted as a hex string. In the output of `jj log` below, the hex hashes `2bea5e3d` and `849165bc` on the right are commit IDs.

The IDs on the left hand side (`royxmykx` and `kpqxywon`) are **change IDs**, which are stable identifiers for logical changes as they physically evolve over time. We’ll discuss these more in the next section.

Commit IDs and change IDs can be referenced in shorthand with an unambiguous (unique) prefix. `jj` helpfully highlights the shortest unique prefix of most IDs to make it easy to type them manually. For example,
instead of copying and pasting `kpqxywon`, we can type in a prefix, down to the shortest unique prefix `k`.

We can inspect the commit `2bea5e3d` with `jj show`, using its short prefix `2`.

```bash
$ jj show 2
Commit ID: 2bea5e3d1992a60ba9ee52c6ce37c55adba9e8fb
Change ID: royxmykxtrkrqppotnrvutxlvrvqyxmy
Bookmarks: main main@git main@origin
Author   : Ethan Lowman <ethan@example.com> (2026-11-15 12:10:46)
Committer: Ethan Lowman <ethan@example.com> (2026-11-15 12:10:46)

    Adjust config

diff --git a/config.py b/config.py
index 7366a4e31d..174ffea06b 100644
--- a/config.py
+++ b/config.py
@@ -1,1 +1,1 @@
-DEFAULT_LIMIT = 10
+DEFAULT_LIMIT = 20
```

Many folks configure a custom diff formatter, like [Delta](https://github.com/dandavison/delta). See [configuration docs](https://docs.jj-vcs.dev/latest/config/#processing-contents-to-be-paged) if you’re interested.

Let’s take another look at our commit graph:

On commit `849165bc`, you’ll see the symbol `@` on the graph node. This represents a snapshot of our **working copy**, or the code we have actually checked out in our local directory. We can inspect this special commit pointer in a variety of ways:

`jj show` shows commit details and a diff, which is empty here.
`$ jj show
Commit ID: 849165bca19639dbd6ccb53e8c1340e78c36d59a
Change ID: kpqxywonksrltlrkyqukqqsxpltznztk
Author   : Ethan Lowman <ethan@example.com> (2026-11-15 12:17:12)
Committer: Ethan Lowman <ethan@example.com> (2026-11-15 12:17:12)

    (no description set)

`

`jj diff` works much like `git diff`. Its output is empty here, since there are no changes in the current working copy relative to the parent commit.

```bash
$ jj diff
```

This output isn’t very interesting, since `@` has no changes. Let’s make an example change to see what happens. If we edit `main.py` and rerun `jj show`, we see this:

```bash
$ jj show
Commit ID: 66b59f20c534705cfb753c722222290e9185b22c
Change ID: kpqxywonksrltlrkyqukqqsxpltznztk
Author   : Ethan Lowman <ethan@example.com> (2026-11-15 12:26:43)
Committer: Ethan Lowman <ethan@example.com> (2026-11-15 12:26:43)

    (no description set)

diff --git a/main.py b/main.py
new file mode 100644
index 0000000000..c74cd2e0e0
--- /dev/null
+++ b/main.py
@@ -0,0 +1,2 @@ def my_new_feature():
+def my_new_feature():
+  pass
```

You’ll notice several things have changed. The working copy has been automatically committed, and `@` is no longer marked `(empty)`. The new commit ID for `@` is `66b59f20`, since we’ve added changes, but the change ID for `66b59f20` is still `kpqxywon`. `jj` has no staging area like in `git`, so we don’t have to manually add files. When we run a `jj` command to inspect or modify repo state after editing files, `jj` automatically snapshots the working copy as a new physical commit for the relevant logical change.

Let’s give this change a description (also called a commit message). We can either run `jj desc`, which opens an editor, or provide it directly with `-m`.

Notice again that the commit ID has changed, since the hash covers the commit message, but the change ID has remained stable.

Now, let’s say we’re ready to use this new feature, and we want to organize that change in a separate commit. We can create a new commit with `jj new`:

We’ve created an empty change `nlrtlrxv` on top of `kpqxywon`. `jj status` reflects that we are editing this new revision which does not yet differ from its parent.

`jj commit` is a shorthand for this common `jj desc` and `jj new` combo. Let’s make another change to use our new feature, and commit it.

To inspect the commit we just created (`n`), we can no longer use the bare `jj show`, which defaults to showing `@`. We have to pass the revision we want to inspect:

```bash
$ jj show n
Commit ID: e1b066782aa1a565c1e5d38ef27a308aa58e7e4c
Change ID: nlrtlrxvuuskxprvtuznquqzqzzwvnzk
Author   : Ethan Lowman <ethan@example.com> (2026-11-15 12:41:30)
Committer: Ethan Lowman <ethan@example.com> (2026-11-15 12:41:30)

    Use the feature

diff --git a/main.py b/main.py
index c74cd2e0e0..0714ec450b 100644
--- a/main.py
+++ b/main.py
@@ -1,2 +1,4 @@ def my_new_feature():
 def my_new_feature():
   pass
+
+do_something(my_new_feature())
```

We can describe empty commits to record intent before starting work. Let’s create a new commit on top of `k` to remind ourselves that we need to document the feature.

A separate `jj desc` would also work just fine instead of the `-m` flag on `jj new`. Here’s the current commit graph:

Note how we’ve created branching commits without creating a named branch. This highlights a major difference between `jj`’s branchless model and `git`’s branch-centric model of organizing work streams. Instead of juggling your work-in-progress on branches, you work on a graph of commits. Once ready to share, you push branches to a Git forge from your commit graph (more on that later).

## [Revsets](https://ethanlowman.com/posts/jj-primer/#revsets)

A revset, an idea borrowed from Mercurial, is an expression that selects a set of revisions from the commit graph. Most `jj` commands accept revsets in their arguments. When we ran `jj new k`, the argument `k` was actually a trivial revset that resolved to the single change with ID `kpqxywon`. The `jj log` command has an `-r <REVSET>` flag that we can use to preview a revset. Some demonstrative examples follow.

Parent of `@`:

Grandchildren of `r`:

Commits between `r` and `@`, inclusive:

Commit `k` and all descendants:

Commits authored by `ethan@example.com` that also have ID `k` or `q`:

I’ll defer to the official documentation for exhaustive detail. The [Revsets language](https://docs.jj-vcs.dev/latest/revsets/) specification is easily my most referenced `jj` documentation page, so I would recommend skimming it to see what’s possible.

Let’s say in the course of documenting our feature in `qwyusntz` we realized we made a mistake in the implementation in parent change `kpqxywon`. We don’t need to manually commit or stash changes to switch tasks. We simply switch our working copy to `kpqxywon` with `jj edit`:

Our working copy once again shows the changes from `kpqxywon`.

```bash
$ jj show
Commit ID: 6b89ffb2a250f622a8638145d65fe8c9bb308dbf
Change ID: kpqxywonksrltlrkyqukqqsxpltznztk
Author   : Ethan Lowman <ethan@example.com> (2026-11-15 12:26:43)
Committer: Ethan Lowman <ethan@example.com> (2026-11-15 12:33:23)

    Implement the feature

diff --git a/main.py b/main.py
new file mode 100644
index 0000000000..c74cd2e0e0
--- /dev/null
+++ b/main.py
@@ -0,0 +1,2 @@ def my_new_feature():
+def my_new_feature():
+  pass
```

`jj` hasn’t lost track of the changes above our working copy, including our most recent edits to `q`:

Instead of switching commits with `jj edit k`, we could have run `jj edit @-`. The revset `@-` is evaluated before switching the working copy, so this moves to the parent commit. The built-in commands `jj next [--edit]` and `jj prev [--edit]` provide another way to move up and down a stack of commits.

### [Automatic rebasing](https://ethanlowman.com/posts/jj-primer/#automatic-rebasing)

If we edit files in the working copy, the descendant commits will be automatically rebased upon the next `jj` invocation. For example, if we edit `my_new_feature`’s implementation in `main.py` and then run `jj log`, we’ll see that changes `k`, `n`, and `q` all get new commit IDs. `jj` also tells us that it performed a rebase.

If the automatic rebase happened to cause merge conflicts, `jj` doesn’t require us to fix them immediately, like `git rebase` would. Instead, `jj` records that the commit is conflicted and lets you carry on with your current task. This is massively helpful to reduce mental context switching, as your stacked commits grow more complex.

To view the conflicts, we can edit the conflicted commit…

```bash
$ jj edit n
Working copy  (@) now at: nlrtlrxv e562bff4 (conflict) Use the feature
Parent commit (@-)      : kpqxywon c501c0bd Implement the feature
Added 0 files, modified 1 files, removed 0 files
Warning: There are unresolved conflicts at these paths:
main.py    2-sided conflict
```

And inspect `main.py`.

```
def my_new_feature():
  print("Hello from the new feature!")
<<<<<<< conflict 1 of 1
%%%%%%% diff from: kpqxywon d9f35831 "Implement the feature" (parents of rebased revision)
\\\\\\\        to: kpqxywon c501c0bd "Implement the feature" (rebase destination)
-  pass
+  return 42
+++++++ nlrtlrxv 41a43a84 "Use the feature" (rebased revision)
  pass

do_something(my_new_feature())
>>>>>>> conflict 1 of 1 ends

```

In a text editor, we can resolve these conflicts, and the next time we run any `jj` command, we’ll see that `jj` has marked the commit as unconflicted:

Let’s say we made a mistake in that conflict resolution, and we want to undo it. In `git`, undoing an action, if it’s even possible, is often complicated. In `jj`, we can always run `jj undo`:

```bash
$ jj undo
Undid operation: 35beb0741f17 (2026-11-15 13:08:39) snapshot working copy
Restored to operation: f134ca987b59 (2026-11-15 13:07:18) edit commit e562bff4876f3ea76248c3f730e9e74d3e28e8a0
Working copy  (@) now at: nlrtlrxv e562bff4 (conflict) Use the feature
Parent commit (@-)      : kpqxywon c501c0bd Implement the feature
Added 0 files, modified 1 files, removed 0 files
Warning: There are unresolved conflicts at these paths:
main.py    2-sided conflict
New conflicts appeared in 1 commits:
  nlrtlrxv e562bff4 (conflict) Use the feature
Hint: To resolve the conflicts, start by creating a commit on top of
the conflicted commit:
  jj new nlrtlrxv
Then use `jj resolve`, or edit the conflict markers in the file directly.
Once the conflicts are resolved, you can inspect the result with `jj diff`.
Then run `jj squash` to move the resolution into the conflicted commit.
```

More generally, `jj` maintains a history of all actions in `jj op log`. We can inspect this log and `jj op restore` to a point in that history, or `jj op revert` an individual operation. If the `jj undo` itself was a mistake, we can `jj redo`.

The `Hint` in the output above is a bit of a spoiler for our next topic, the squash workflow.

## [Squash workflow](https://ethanlowman.com/posts/jj-primer/#squash-workflow)

Editing commits that have descendants can sometimes feel sketchy. If you’re iterating on a large diff that has left your working memory, it would be nice to separate your new changes from the existing diff. For example, we might like to inspect the diff that resolves a rebase conflict in isolation.

Let’s follow the instructions from the above output. We first create a new commit on top of the conflicted commit:

Now we can resolve the conflicts in `main.py` in our editor, and rerun `jj log`:

We can inspect the diff in `@` if we like, and when we’re happy with the conflict resolution, we can squash it into the parent commit:

The conflict is now resolved, and we can continue our work.

One of the powerful qualities of `jj` is that it makes diffs malleable like clay. With automatic rebase and the confidence inspired by `jj undo`, we can move, combine, drop, and split diffs with ease.

Let’s try a few operations on our current commit graph. Here’s the starting point.

### [Rebase](https://ethanlowman.com/posts/jj-primer/#rebase)

Let’s use `jj rebase` to coerce our branching commit graph into a linear history. Let’s say the documentation commit (`q`) should go between the implementation (`k`) and the usage (`n`). We could accomplish this by moving `nlrtlrxv` (and its empty descendant) on top of `qwyusntz`:

Another way to accomplish the same effect would be to use `jj rebase -r q --before n`. Many `jj` commands have multiple ways to specify revsets. `jj rebase --help` documents these well.

Since arguments to `jj rebase` flags are all revsets, we can write a revset that selects a sequence of commits or commit subgraph, and move it elsewhere in the graph.

If we wanted to insert a commit below `k`, the most direct way is `jj new --before k`, but for demonstration purposes, we could alternatively create a new commit on top of `r` and rebase `k::` on top:

If you enjoy using TUIs, `jj arrange` provides a commit graph editor similar to `git rebase -i` for reordering commits.

### [Squash](https://ethanlowman.com/posts/jj-primer/#squash)

If we decided documentation should be in the same commit as implementation, we can squash:

`jj` will open an editor and give us a chance to write a combined commit message.

### [Abandon](https://ethanlowman.com/posts/jj-primer/#abandon)

To drop a commit from the graph, we can use `jj abandon`. Let’s drop the preparation commit:

To abandon parts of a commit (hunks or changes to whole files), we can use the `jj diffedit` TUI (see [docs](https://docs.jj-vcs.dev/latest/cli-reference/#jj-diffedit)).

### [Split](https://ethanlowman.com/posts/jj-primer/#split)

The `jj split` TUI allows us to take a commit and split it into two consecutive commits by selecting which files or hunks should go in the first. Let’s use it to split up implementation and documentation again with `jj split -r k`:

The [jj-hunk](https://github.com/laulauland/jj-hunk) project provides a means to automate commit splitting. If you are so inclined, agents are quite good at using this tool to split up commits into a sequence of smaller changes for easier review.

## [Bookmarks and Git branches](https://ethanlowman.com/posts/jj-primer/#bookmarks-and-git-branches)

`jj` does not have a native concept of a branch, but it does have a primitive called bookmarks that map to Git branches. When we need to manipulate Git branches, we do it by way of bookmarks.

You can go pretty far using Git without realizing this, but a Git branch is just a pointer to a commit. `jj` explicitly models bookmarks this way. `jj` bookmarks are essentially a named label attached to a commit that we can move around as we modify our commit graph, and push to/pull from a remote.

We’ll discuss a few basic workflows around Git branches below, but you can find a more complete guide in the `jj` docs on [Working with GitHub](https://docs.jj-vcs.dev/latest/github/).

Assuming we initialized `jj` in a git repository that has remotes, we should have some output for `jj git remote list`.

Since `jj` is branchless, the commits we’ve created locally don’t have a branch name. Luckily, `jj` doesn’t require us to pick one, and generates one for us. Generated branch names free you from thinking of a unique branch name so you can instead focus on writing a good commit message (usually the more durable descriptor of a change).

To create a generated bookmark for change ID `nlrtlrxv` and push up a corresponding Git branch, we can run a command like the following:

Now `jj log` shows our change with a correspondingly named bookmark `push-nlrtlrxvuusk` associated:

We’re free to create a PR from this branch on GitHub now. You can customize the bookmark naming scheme with the `git_push_bookmark` template config documented [here](https://docs.jj-vcs.dev/latest/config/#generated-bookmark-names-on-push). It’s a common pattern to format branch names like `<author name>/<change ID>`.

Since `jj git push -c` creates a branch name that corresponds to a change ID, it seems to encourage one evolving change per PR. I think it’s usually best to lean into these ergonomics, and have one change per PR.

To update a branch, the general process is to either squash commits into a change that is already bookmarked, or create new commits and move the bookmark forward.

If you choose to squash commits into an existing bookmark (recommended to keep one change per PR), the flow is as follows.

We now see `push-nlrtlrxvuusk` has an asterisk next to it, indicating it has changes that haven’t been pushed to the remote. So let’s push them.
`$ jj git push -b push-nlrtlrxvuusk
Changes to push to origin:
  bookmark: push-nlrtlrxvuusk [move sideways from b1284f61c417 to aeb869aef99b]
`

The remote branch now reflects the new changes. The above output says that we moved the branch sideways from one commit to another commit, which reflects that we did a force-push. `jj git push` runs the equivalent of a `git push --force-with-lease`, so if you’re ever unclear about what a push operation would do, you can use the `jj git push --dry-run` flag. `jj` protects you against most dangerous force pushes refusing to rewrite a configurable revset of immutable commits. The default immutable revset is sensible, but you can make it more or less conservative by [configuring your own immutable heads](https://docs.jj-vcs.dev/latest/config/#set-of-immutable-commits).

In this flow, we add new commits on top of our bookmark and then move the bookmark to point to our new commit.

Then make our edits.

The bookmark does not automatically move to our new commit. This is the biggest difference between bookmarks and Git branches. For now `push-nlrtlrxvuusk` still points at the commit below:

There are several ways to move the bookmark to the new commit. The easiest is probably `jj bookmark advance`, which moves the closest bookmark to the given commit:

Now we’re ready to push the moved bookmark.

```bash
$ jj git push -b push-nlrtlrxvuusk
Changes to push to origin:
  bookmark: push-nlrtlrxvuusk [move forward from aeb869aef99b to 2341ee4aa554]
```

Since `jj` is branchless, strictly speaking, we don’t “check out” a branch, but we can create a commit on top of a remote branch. First do the equivalent of a `git fetch`, importing remote bookmarks:

```bash
$ jj git fetch
```

And create a new empty commit on top of the remote branch:

Our working copy now contains all the commits on the remote branch. However, if we were to drop back to `git`, we see that from `git`’s perspective, we’re in a [detached head](https://git-scm.com/docs/git-checkout#_detached_head) state, not on any branch.

```bash
$ git status
Not currently on any branch.
nothing to commit, working tree clean
```

This is because `jj` is editing a commit above a bookmark, and does not have an equivalent to `git`’s “current branch” state.

Syncing with the trunk (e.g. `main`) is just a specific example of this flow. We would `jj git fetch` to update our `main` to the upstream `main`, and then rebase our commits on top. For example, the following would rebase `my-branch` on top of a new `main`:

```
jj rebase -b my-branch -o main
```

`jj` commit graph manipulation is easiest when you have a live commit graph on screen. There are different ways you can accomplish this.

[jjui](https://github.com/idursun/jjui) is a TUI for `jj` that allows you to edit the visual graph directly. I have not personally used this, but I know people who like it.

I prefer to have an always-live `jj log` in the corner of my screen by way of [viddy](https://github.com/sachaos/viddy) (a nicer version of `watch` that supports color):

I recommend filtering down this log to a revset that represents your current work. Here’s a starting point:

```
visible() & (trunk() | (tracked_remote_bookmarks() & ~::trunk()) | (mutable() & mine())::)
```

You might also consider trying my experimental project [jj-stamp](https://github.com/ethanal/jj-stamp), which is a local code review GUI for the squash workflow. Even if you don’t use the squash review workflow, it makes a pretty good diff viewer with a live `jj log` on the side and a terminal for running `jj` operations.

One of the biggest productivity gains from `jj` comes in its ability to support stacked PR workflows. This merits its own post, so I’ll keep it short.

Large changes are easier to understand when they’re broken up into a series of logical steps. Breaking up a large change into smaller sequential atoms of review makes the whole change easier to understand. Stacked PRs attempt to leverage this fact to optimize merge throughput, while simultaneously removing pipeline stalls in the review process.

Let’s say we’re building a new feature. We can decide we want to split up implementation into three stages:

1. Refactor to make the feature easier to implement
2. Implement the feature
3. Use the feature in another system

`jj`’s ability to work on stacked changes with automatic rebase is a natural fit for implementing these three stages. Each of the three stages maps to a single commit, each with an associated bookmark/branch/PR:

After you implement the first change, you can put up a PR for review and immediately start working on the next change. Your work stream becomes a long queue where you pop off the bottom as PRs are ready to merge and push to the top, with no pipeline stalls.

It’s pretty easy to manually set up small PR stacks with `jj` and GitHub, but once you get hooked on the technique (making stacks 5–10 PRs deep), you’ll want a tool. `jj-pancake` is my entry into the ring of stacked PR tools. More on that soon.

- Official Jujutsu docs. I most often refer to the revset spec.
- Steve Klabnik’s `jj` tutorial was my first introduction to jj. I don’t think it’s maintained as a durable resource (and I don’t promise mine will be!), but it’s still a good read.
- I follow the jj releases RSS feed. Lately the releases have been packed with new features. Overall jj is quite stable, but the occasional bug is fixed promptly.
- The Jujutsu discord is active and friendly!
- The blog of East River Source Control, a company that is building a new forge and code review platform intended to support Jujutsu well. The creator of Jujutsu, Martin von Zweigbergk, has joined as the CTO, and they have lots of other smart people as well. Perhaps a successor to GitHub one day? I’m rooting for them.
- My personal `jj` config. You might find some useful aliases or tricks here, but I haven’t attempted to make it readable.
- The `jj` config of Austin Seipp, a jj maintainer. Cool tricks lie within.
I have been using [the community fork of Maiao](https://github.com/runetes/maiao) for a little while now, and it is
excellent. For anyone who prefers working with stacked diffs, but needs to
interact with a more traditional forge such as GitHub, try using Maiao for a
bit. *It just does the right thing in almost every situation*. It’s cut my
frustration with GitHub at least in half, if not more.

For the small group of readers who are stoked about stacked diffs, that’s
probably enough of a pitch. For the rest of the world, let’s back up a little.

On traditional forge platforms1<sup>1</sup> Like GitHub, Codeberg, GitLab, BitBucket,
etc., pre-commit2<sup>2</sup> Pre-commit because it’s the review that happens before the
code is merged (“committed”) to the upstream branch, in contrast to e.g. audits
which are a kind of post-commit review. code review happens on *pull requests*
(sometimes called *merge requests*), where each pull request is created from a
git branch.

Users that are new to git can then think of a branch as one development effort
toward a small goal. They keep adding commits to that branch as long as its tip
does not represent the goal state. At the end, when everything looks right and
the change is approved, they perform an explicit merge. This means they create a
merge commit on the upstream branch that references both the old upstream and
the branch they worked on.

This lets beginners work in smaller increments while not dealing with the
intricacies of rewriting git history3<sup>3</sup> Sometimes the beginner is instructed to
perform a squash merge instead, which typically means the forge platform creates
a single, regular commit on the upstream branch, referencing only the old
upstream, and containing all the changes implied by the tip of the development
branch. Although it sounds like this rewrites history, it doesn’t really – the
old development branch is still exactly the same as it was before. The
difference is that the changes implied by it were copied over to the upstream
branch without reference to the development branch.; the workflow lowers the
barrier to collaborating with others using git, which is nice.

It also means *the reviewing interface* in a traditional forge doesn’t have to
deal with the intricacies of rewriting git history. This means the reviewing
ui typically only shows the differences between commits still on the
development branch, and not what changed between two versions of “the same”
commit, when one of them is no longer on the branch.

To be more concrete, here’s an example of a part of the history graph of a
project that uses this workflow.4<sup>4</sup> The commits are not shown in chronological
order. I reordered them (where it was possible to do so without changing the
structure of the graph) to make the graph read more clearly.

```

▲ (upstream)
│
│   ▲ (input-validation)
│   │
│   │   ▲ (priv-cache)
│   │   │
│   ●   │       Tighten input validation
│   │   │
│   │   ●       Rename cache variables
│   │   │
│   │   ●       Cache user permissions
├───╯   │
●◀──╮   │   Merge flaky-test-fix (PR #835)
│   ├───╯
│   ●           Fix timezone offset instead
│   │
│   ●           Disable login test
│   │
●◀──┼───╮   Merge log-migration (PR #834)
├───╯   │
●◀──╮   │   Merge avatar-upload (PR #833)
│   │   │
│   ●   │       Fix typo in readme
│   │   │
│   ●   │       Clean up unused imports
│   │   │
│   ●   │       Add avatar upload
├───╯   │
●◀──╮   │   Merge parser-null-check (PR #832)
│   │   │
```

We can see a total of 12 commits. Four of them are merge commits on the
upstream branch, and two of those merge commits correspond to branches we can
see the work on (`avatar-upload` and `flaky-test-fix`). We can see each of those
two branches had three and two commits of actual work on them, respectively.

Then there are two more branches (`input-validation` and `priv-cache`) which are
still open (not merged with upstream). One of them (`priv-cache`) has two
commits of work, and it’s not based on the upstream branch, but on the final
result of one of the earlier branches (`flaky-test-fix`), before it got merged.

We don’t have to use git that way. We can instead choose to have only *one*
development branch. I call it something generic like `dev`. On that branch, each
goal state is represented by one commit. So instead of multiple branches (one
for each goal) with multiple commits on them (steps toward the implementation),
there is just one branch (a generic development branch) with multiple commits on
it (one for each goal).

With that workflow, if we discover one of the commits don’t represent the goal
state of that change, *we edit that commit*5<sup>5</sup> Technically speaking, git
doesn’t let users edit commits. What happens under the hood is the commit is
replaced with a new one. But with a change id in the commit message, we can
still tell that they represent the same atomic change. instead of adding more
commits.6<sup>6</sup> What if we need to revert to an old commit? Fortunately, git
maintains a reflog with old commits. Those stick around until git decides to
garbage collect dangling refs. Then each atomic change in progress is
implemented in exactly one commit, all on one development branch. The `dev`
branch may have many commits, but they represent different atomic changes, not
progress toward one goal state.

This way of working is also known as making *stacked diffs*, and I find it
easier and faster than having a separate branch for each atomic change. [Many](https://newsletter.pragmaticengineer.com/p/stacked-diffs)
experienced [software](https://gregoryszorc.com/blog/2020/01/07/problems-with-pull-requests-and-how-to-fix-them/) engineers [agree](https://jg.gg/2018/09/29/stacked-diffs-versus-pull-requests/).7<sup>7</sup> I should say I disagree with Gergely
Orosz when he says it’s impossible to make a pull request that depends on
changes in an earlier, unmerged pull request. It’s possible (and even easy in
most forges) but it’s a lot of extra work to juggle the branches and merge
targets. Fundamentally, there’s no deep incompatibility between pull requests
and stacked diffs. The reason people prefer tooling made for stacked diffs is
that there’s less paperwork needed to satisfy git when working with those
tools.

The way stacked diffs are merged is ideally by copying them over to the upstream
branch, either through cherry-picking, or by choosing the *rebase and
fast-forward* merge type in the forge ui. This produces a history of the
upstream branch that very clearly lists each atomic change in the order it
occurred, without the false steps and mistakes along the way.

Beginners may think this is dishonest. The the point is not to hide one’s
mistakes, but to present a history that another developer can read and follow
along with three years into the future, when they want to understand how the
project ended up in the state it is in. For that purpose, only what eventually
went into the upstream branch matters.

The example history graph from above would, under a stacked diffs-type
workflow, look more like this:

```

▲ (upstream)
│
│    ▲ (dev)
│    │
│    ●       Tighten input validation
│    │
│    ●       Cache user permissions
│    │
●◁┄┄┄◌   Fix timezone offset in login test (PR #835)
├───▶┤
●    │   Migrate to structured logging (PR #834)
│    │
●◁┄┄┄◌   Allow users to upload avatars (PR #833)
├───▶┤
●    │   Check for null in order parser (PR #832)
│    │
```

Two commits on the upstream branch (null check and timezone offset) came from
other people. In between them, we updated our long-lived `dev` branch to reflect
the latest upstream, and then copied the finished avatar commit over to the
upstream. The same process happened for the flaky test fix a little later. We
worked on both user permission caching and input validation in the same `dev`
branch instead of making two separate, new branches. Once those commits are
approved and have passed through ci, they will get copied to the upstream
branch, like the ones before them.

All of these commits needed amendment just as many times as in the previous
graph, only we do it by replacing the commits instead of adding more commits.

This is what people mean when they talk about how “one atomic change is one
commit, and one commit is one atomic change”.

There is one unfortunate consequence of the stacked diffs workflow: when all
commits are in one branch, they look like they depend on each other in the order
they exist on the branch, even if they actually contain independent changes.
When all commits are on one branch, there’s no way to see which commits are
independent without (a) reading the code, and (b) trying to cherry-pick one of
the changes.8<sup>8</sup> Both are needed, because cherry-picking or rebasing can
conflict in git even though changes are independent (when they happen to appear
close to each other in the source code), and dependent changes can generate a
clean cherry-pick as far as git is concerned, even if it breaks the code (when
the changes happen in different locations in the code, but one of them assumes
the other has happened already).

If it’s important to document to ourselves that we have two parallel workstreams
that are indepedent, we can use two local generic development branches (I call
mine `dev` and, imaginatively, `dev2`). Each branch is still treated as a stack
of diffs, i.e. each commit represents one atomic change, but now it’s abundantly
clear that commits cannot depend on each other across the two branches.

At this point, you can probably guess why the pull request workflow of
traditional forges is annoying. The pull request assumes we have one branch for
each atomic change, but with stacked diffs, we only have the one branch, where
we want each *commit* to become a separate pull request, building on the one
before it.

The way I used to handle it was exactly through the tedium you wouldn’t expect:

1. I manually created one branch for each commit.
2. I pushed all those branches.
3. I went to the GitHub web ui and made a pull request for each branch, taking care to set the merge target of each to the branch that came before it.
4. When merging, I again had to be careful to merge in the right order.

This is a lot of work.9<sup>9</sup> Still less work in total than having a branch per
atomic change, but just barely! Maiao solves that.

These days, when I feel ready to create pull requests for my commits, I trigger
the `git review` command. Maiao then automatically does all of the things I did
manually before, better than I could. It fetches the latest upstream, rebases
the current branch onto it, creates disposable branches for each commit, pushes
them, opens up a pull request with the right merge target for each disposable
branch through the GitHub api, and turns them into a native GitHub stack of
pull requests, meaning they get merged in the right order, and can be merged all
at once when they are ready.

If code review or the ci build uncovers things I need to change, I do what I
always did: I replace the commit that needs changing. Then I run `git review`
again, and Maiao *just does the right thing*: it rebases onto the latest
upstream again, it moves the disposable branches to the new commits,
force-pushes them, updates the pull request descriptions with any changes to the
commit messages, updates any merge targets that have changed, etc.

Maiao is one command (`git review`). When run, it makes the GitHub pull request
stack match our local development branch. That’s all it does, and that’s all it
needs to do.

In cases where we have multiple local development branches (because the work is
independent and parallel), `git review` can be run on either or both of them
independently of the other, and Maiao will create one stack for each branch, as
one would expect.

Note also that Maiao doesn’t have to create pull requests for the entire
development branch. Maybe we’re still working on the top few commits. Then we
can create a temporary branch pointing to the topmost of the commits we do want
pull requests for. When we run `git review` with that branch checked out, Maiao
makes pull requests only out of the commits included in that branch. Then when
we finish those top commits, we can run `git review` on the development branch,
and Maiao understands that the topmost commits build on the commits that already
have pull requests, so it stacks new pull requests for the new commits on top of
the pull requests that already existed for the prior commits.

All of the above to say Maiao doesn’t care about how you branch locally. A
decent mental model is that it creates and updates pull requests for each of the
commits between `head` and the master branch so the stack on the forge matches
the local commits. That’s all.

And it’s awesome.

Like GitHub, Codeberg, GitLab, BitBucket,
etc.

Pre-commit because it’s the review that happens before the
code is merged (“committed”) to the upstream branch, in contrast to e.g. audits
which are a kind of post-commit review.

Sometimes the beginner is instructed to
perform a squash merge instead, which typically means the forge platform creates
a single, regular commit on the upstream branch, referencing only the old
upstream, and containing all the changes implied by the tip of the development
branch. Although it sounds like this rewrites history, it doesn’t really – the
old development branch is still exactly the same as it was before. The
difference is that the changes implied by it were copied over to the upstream
branch without reference to the development branch.

The commits are not shown in chronological
order. I reordered them (where it was possible to do so without changing the
structure of the graph) to make the graph read more clearly.

Technically speaking, git
doesn’t let users edit commits. What happens under the hood is the commit is
replaced with a new one. But with a change id in the commit message, we can
still tell that they represent the same atomic change.

What if we need to revert to an old commit? Fortunately, git
maintains a reflog with old commits. Those stick around until git decides to
garbage collect dangling refs.

I should say I disagree with Gergely
Orosz when he says it’s impossible to make a pull request that depends on
changes in an earlier, unmerged pull request. It’s possible (and even easy in
most forges) but it’s a lot of extra work to juggle the branches and merge
targets. Fundamentally, there’s no deep incompatibility between pull requests
and stacked diffs. The reason people prefer tooling made for stacked diffs is
that there’s less paperwork needed to satisfy git when working with those
tools.

Both are needed, because cherry-picking or rebasing can
conflict in git even though changes are independent (when they happen to appear
close to each other in the source code), and dependent changes can generate a
clean cherry-pick as far as git is concerned, even if it breaks the code (when
the changes happen in different locations in the code, but one of them assumes
the other has happened already).

Still less work in total than having a branch per
atomic change, but just barely!
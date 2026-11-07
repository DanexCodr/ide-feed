This summer I participated in [the r/roguelikedev summer event
where we write a Roguelike game](https://old.reddit.com/r/roguelikedev/wiki/python_tutorial_series)<sup>[1]</sup>, following one of the Roguelike
coding tutorials. I’m not trying to learn coding, so I use this
event to try learning something else. This year, one of the things
I wanted to tackle was two-dimensional version control.

The tutorial we’re following has 14 chapters. I wanted to use
version control while writing my code. But I *also* wanted to use
version control to match the tutorial’s chapters:

At the end of the project, I want a history of changes I made
while writing the tutorial (horizontal axis) and *also* a history of
changes the reader should make while following the tutorial
(vertical axis).

I can get the structure I want by setting up one Git branch per chapter,
pointing to the previous chapter as the parent. Then when I update
chapter 1’s code, I can push that forwards into chapter 2, 3, etc.

However, the [Jujutsu version control system](https://docs.jj-vcs.dev/latest/git-comparison/)<sup>[2]</sup> can do this
*automatically*. Instead of managing all the branches and merges, I
can focus on the “writeup” column of the diagram, where I can edit
any of the chapters at any time. Jujutsu will roll forward the
changes from one chapter to the others. I decided to try it for
this project. Other people have blogged about Jujutsu’s features;
I’m going to focus on the two dimensional output I want.

**Example**: While working on the dungeon generation chapter, I
realized I could’ve made the tile data structure better. It was
easy to make those changes happen *before* the dungeon code. In this
diagram, the horizontal axis is time and the vertical axis is
chapter. I went back and forth between dungeon generation and the
tile map structure. Once I was happy with both of those, I moved
on to a better data structure:

![](https://www.redblobgames.com/blog/2026-09-27-jujutsu-experience/images/part-3.png?2026-09-27-13-31-40)

*Mostly forward, occasionally backward*

Ignore the colors; they were from a visualization tool.

**Example**: While working on the field of view chapter, I found
plenty of things I could’ve improved in earlier chapters. I had
become comfortable enough with Jujutsu that my brain stopped
thinking of commits as “set in stone” but instead as “I can fix
that!” And I did.

**Example**: Most of the changes are to the most recent chapters (bottom of this diagram). But occasionally I went back to earlier chapters (top of this diagram). The red shows that I had merge conflicts that I had to resolve before I went back to working on the recent chapters.

**Example**: As I became even more comfortable with making changes across commits, I came up with better names to use throughout the project. I wanted to make these changes from the beginning, so I used a combination of regular <kbd>jj edit</kbd>, which propagates changes forwards to later chapters, and the <kbd>jj absorb</kbd> command, which propagates changes *backwards* to earlier chapters.

This required a lot of cleanup. The changes didn’t have merge conflicts, but the resulting code didn’t always compile. If I changed `apple` to `zebra` in chapter 1, and I had used `apple` in chapter 2, Jujutsu wouldn’t know to change *that* name too. So I had to make those changes and test every chapter.

**Example**: I *loved* that I can improve the version control change descriptions retroactively. Here’s me going back through all the change descriptions to format them consistently:

![](https://www.redblobgames.com/blog/2026-09-27-jujutsu-experience/images/jujutsu-rebase.png?2026-09-27-13-32-00)

*Editing everything*

**Thoughts**: It’s hard to learn by just reading about something. For this project I wanted to try doing lots of things to see what worked well and what didn’t. This project is a bit unusual in that I’m trying to not only produce a final version of the game, but also produce 50 intermediate versions that all run, *and* have clean code that I can present in a tutorial series.

![](https://www.redblobgames.com/blog/2026-09-27-jujutsu-experience/images/jujutsu-types-all.png?2026-09-27-13-31-51)

*complete project history*

I think Jujutsu was a reasonable tool for this project. I can use it for developing, and also export to Git so that other people don’t have to use Jujutsu. [The GitHub repository](https://github.com/redblobgames/2634-roguelikedev)<sup>[3]</sup> has 54 git commits, not the ~5000 internal Jujutsu commits.

The main downside for me so far is that a lot of things happen
automatically and I couldn’t keep track of them all. I need
to get better at understanding what it’s doing behind the scenes
so that I can use it with more confidence while avoiding some of
the pitfalls.

The resulting game is [playable on the web](https://www.redblobgames.com/x/2634-roguelike-dev/). I wrote
notes but didn’t write a tutorial this time.
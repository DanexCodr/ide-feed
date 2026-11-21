This year's [Autumn Lisp Game
Jam](https://itch.io/jam/autumn-lisp-game-jam-2026) has just wrapped
up!  Spritely's contribution to the jam was
[Polydraw](https://davexunit.itch.io/polydraw), a peer-to-peer party
game that is easy to pick up and play with friends.  In Polydraw,
players take turns being the *artist* who draws an image based on a
*prompt*.  The catch is that the artist only has 60 seconds and can
only draw using triangles.  All of the other players are *guessers*
who try to correctly guess the prompt.  We're quite pleased with how
the game turned out!

The rest of this post is a daily devlog of how we made Polydraw so you
can see what the process look likes to make a game with Goblins and
Hoot under a tight deadline.

## Day 1 (10/30)

It's go time!  First, we created a Git repository on
[Codeberg](https://codeberg.org/spritely/polydraw) and copied the
[Hoot game jam
template](https://codeberg.org/spritely/hoot-game-jam-template) into
it.

Since the core activity in Polydraw is drawing triangles, the first
thing Dave implemented was an interface for doing that on a canvas.
This first version was crude and didn't include a color picker.

## Day 2 and 3 (10/31 and 11/1)

We took the weekend off to prepare for a busy week ahead.

## Day 4 (11/02)

This is the day that we *really* got to work on the game jam.

The first version of the triangle editor stored pixel coordinates of
the local canvas, but that wasn't going to be good enough to display
on other machines with different sized canvases.  So, Dave simply
normalized triangle vertices into the [0,1] range so each peer could
scale them as needed.

Dave also implemented a basic scene system, a common game programming
pattern, to encapsulate the coarse game states such as the title
screen, the lobby, and the main game.

A color palette was added along with some additional mockup UI around
the canvas.

## Day 5 (11/03)

With a good enough game engine in place, we turned our attention to
the game protocol.  Since we are using Goblins, all interactions are
modeled using actors.  Dave came up with the following actors:

- *Player*: Used for player identity within the game and contains the player's self-proposed name.
- *Lobby*: The place where players gather before the game starts. The player that creates the lobby is the **host** and all other players are **guests**.
- *Game*: Holds all of the game state like the player list, whose turn it is, and the scoreboard.
- *Controller*: A player's virtual game controller. Used to speak to the game actor, but all actions are scoped to the individual player.

A [test
script](https://codeberg.org/spritely/polydraw/src/branch/main/actor-test.scm)
was written to simulate creating a game, joining the lobby, and
playing a round.  At this stage, everything was happening in a single
process.  Goblins makes it easy to start with a single process and
then distribute the actors to multiple machines later.

## Day 6 (11/04)

Now it was time to get the actors onto the network and hook them up to
the game UI.  For networking we used [OCapN](https://ocapn.org),
naturally.  Jessica started up an instance of our new [end-to-end
encrypted relay
netlayer](https://spritely.institute/news/end-to-end-encrypted-relays-for-ocapn.html)
that we set as the default relay so the game would "just work" when we
uploaded it to [itch.io](https://spritely.institute/news/https/itch.io).  In fact, dogfooding the
relay was a large part of the motivation behind participating in the
game jam in the first place!

Dave got the actors online with OCapN and connected the game UI to the
actors, then confirmed that a three player game works.  Three players
is the minimum number of players needed to trigger OCapN's
[third-party
handoff](https://github.com/ocapn/ocapn/blob/main/draft-specifications/CapTP%20Specification.md#third-party-handoffs)
feature.  Handoffs are what enable distributed networking in OCapN:
Alice can give Bob a reference to Carol, which causes Bob and Carol to
establish a new OCapN session with each other.  This is the first
application we've made that does handoffs over the relay netlayer and
it was nice to see them working as intended.

Unfortunately, we discovered an issue with how Goblins handles two
peers connecting to each other concurrently, a problem known as
"crossed hellos".  OCapN mandates that only **one** connection may be
open between any two peers, so we have to pick which connection wins.
The bug is that any promises that were created over the losing
connection **never resolve**.  This was observed in the game as an
empty lobby player list that should be populated.  It didn't prevent
the rest of the game from working, though, so we didn't try to fix it
(yet).

## Day 7 (11/05)

On this day, Dave discovered that, despite his best efforts, he fell
victim to the "identity footgun".  We could write a whole blog post
series about the many subtle issues of object identity (in the sense
of Scheme's `eq?`) in object capability systems, but instead we'll
refer you to the [The Grant Matcher
Puzzle](http://www.erights.org/elib/equality/grant-matcher/index.html)
and just mention that using object references as keys in associative
data structures is error-prone.  A promise that eventually resolves to
a reference to Alice is *not* identical (again, in the `eq?` sense) to
a reference to Alice.  So, if you accidentally use a promise as a key
somewhere or use `eq?` directly you will probably have a bad time,
which is exactly what happened to us.

To deal with this identity crisis, Dave first detected it at runtime
by [writing a
wrapper](https://codeberg.org/spritely/polydraw/src/commit/a740a27673e2dd107bab50e221b24b33e9579eff/modules/scene/draw.scm#L89)
around `eq?` called `geq?`.  This new predicate throws an error when
comparing a promise to a non-promise.  Then he used the resulting
backtraces to find the offending code and change it to resolve all
necessary promises before doing identity comparisons.

Christine finally cleared enough other things off her plate where she
could start contributing to the game.  We thought it would be nice to
have the game start with a splash screen of triangle'y animations that
would resemble the kinds of art players would make in the game.
We decided to use the Blender add-on by Ursula Kurdali named
[Stop Motion](https://github.com/bkurdali/Stop-Motion-Blender-Addon/tree/extension)
since it gives a great amount of freedom to animate by creating and
destroying as much geometry as you like.  Christine made the first
mockup of a splash screen animation of a "death" type character
swinging a scythe.

However, the animation hadn't left Blender yet.  We're gonna have to
figure out how to get those polygons out and into the game engine!

## Day 8 (11/06)

This was *the* day to finish implementing the core game loop.  We
wanted the weekend to be all about fixing bugs and making it look and
feel as good as we can.  At last, the points awarded at the end of
each round were displayed in the UI.  The player list on the left side
of the screen was transformed into a leaderboard that sorted players
by score.

While creating the leaderboard it was discovered that Goblins was not
correctly parsing pairs received over OCapN.  Christine swooped in
with a [quick
fix](https://codeberg.org/spritely/goblins/commit/f7c7beae6322003a28b57148bd64346bc14d626b)
and Jessica folowed up with a [regression
test](https://codeberg.org/spritely/goblins/commit/2771da67e80b5c2a9e4ed684f24f4f95428cb419).

We also added a small set of emoji reactions underneath the
leaderboard.  Reactions were not critical to the core gameplay but
they were planned from the very beginning of the project.  It's good
that we had time to add them because it was a lot of fun to spam
emojis at the artist to give them an indication of how good or bad
they were doing.

## Day 9 (11/07)

With two days left and the core gameplay loop complete, the focus
shifted to bug fixing and adding
[juice](https://www.youtube.com/watch?v=Fy0aCDmgnxg).  Up until this
point the HTML was mostly unstyled (as you can see in the videos
above), so Dave added a little CSS to improve the look and feel.

A playtest revealed that the [simple
PRNG](https://en.wikipedia.org/wiki/Linear_congruential_generator) we
were using was implemented incorrectly.  We noticed because the artist
prompt was always "bus" no matter how many rounds you played.  Oops!
This was fixed.

Remember that crossed hellos bug from day 7?  Dave finally implemented
a workaround, which was to simply [throw out the first pancake and try
again](https://codeberg.org/spritely/polydraw/src/commit/a740a27673e2dd107bab50e221b24b33e9579eff/modules/scene/lobby.scm#L151),
as suggested by Christine.  A simple race against a timeout was all
that was needed.  We'll be thinking about how to fix this in Goblins
so this situation cannot happen in the future.

Christine started work on making more animations for the game's intro.
The "death" animation was a good "hello world" for testing the exporter,
but being all black it was too simple to make sure everything worked
right; draw order, etc, didn't matter. Christine made a "square guys"
animation as a kind of
[Acid2 test](https://en.wikipedia.org/wiki/Acid2)
equivalent. This file had several tricky properties to it, most
especially that draw order would matter, colors would be important, et
cetera.

Christine also made this triangle'y duck themed piece:

Christine wrote a [Python
script](https://codeberg.org/spritely/polydraw/src/commit/a740a27673e2dd107bab50e221b24b33e9579eff/anims/triangle_exporter.py)
to export the animations from Blender into a custom format encoded
using Syrup.  The encoded data was then embedded into the Scheme
program as bytevector literals using a [little
script](https://codeberg.org/spritely/polydraw/src/commit/a740a27673e2dd107bab50e221b24b33e9579eff/build-anim-module.scm).
Dave then started work on a renderer for these animations, but it
wasn't working quite well enough by the end of the day to commit and
push it.

Up until this point we only had a small number of frequently-repeated
words.  Morgan Lemmer-Webber curated a word list for us, starting with
an [existing public domain word list](https://raw.githubusercontent.com/MichaelWehar/Public-Domain-Word-Lists/refs/heads/master/5000-more-common.txt)
of 5000 words, and curated down to a 621 words, selecting for words
that were more feasible to draw (ranging from easy to challenging, but
all trying to be feasible).

The game name was changed from the placeholder "Twenty Triangles" to
"Polydraw".

## Day 10 (11/08)

*The final day.*

The code to render animations was finished.  Some final minor bug
fixes were made.  Some CSS was tweaked.  Original music and sound
effects by
[encrypted.whispers](https://is.nota.live/@encryptedwhispers) were
added.  Additionally, we used a few CC0-licensed sound effects by
[Kenney](https://kenney.nl).

A few gameplay improvements were made, such as showing guessers what
the prompt was when the round ends and how many triangles the artist
had remaining.  Little improvements can make a big difference and both
of these changes were very helpful for players and made the game feel
more polished.

There wasn't enough time remaining to do as much work on resiliency in
the face of network partitions as we would have liked, but Dave did
squeeze in a commit that allowed the game to survive if a guest
leaves.  Unfortunately, the experience for the disconnected guest
isn't very good as they don't see any message that their connection
dropped.

We did a final playtest to confirm that there weren't any showstopper
bugs.  Christine added final splash animations.

Finally, Christine added some code (fixed up by Dave) and animations
which would overlay *over* the drawings indicating that drawing was
starting, it was time to guess, or the results.

## Pencils down!

We submitted the game two hours before the deadline!  Now it was time
to catch our breath and show off the game to everyone we could.  Dave
even played it live with a couple other people on a stream!  Here's a
screenshot which gives you a good look of the final result:

![Live stream of Polydraw](https://files.spritely.institute/images/blog/2026-11-12-polydraw-stream.png)

The response was quite positive!  The feedback we received closely
matched the things we wanted to improve upon if we had more time:
better disconnect handling, a way for the host to skip to the next
phase instead of being forced to wait for the timer to run out, and
invite URLs (rather than URIs) that auto-join the game when visited.

Polydraw ranked 5th overall in the [official game jam
results](https://itch.io/jam/autumn-lisp-game-jam-2026/results).

Try playing it over on [itch.io](https://davexunit.itch.io/polydraw)
and leave us a comment!

## Thanks to our supporters

Your support makes our work possible!  If you like what we do, please
consider [becoming a Spritely supporter today](https://spritely.institute/donate)!
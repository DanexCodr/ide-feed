![The thread on X. Ben, @ben_codez: Sounds like you're making the terminology up! Makes sense though. No self respecting dev would show the user a booking had succeeded before server verification. We're probably agreeing and arguing semantics. Ben: To be clear, I was talking about stuff like "liking a post" or displaying the users's post before the server has come back and said "ok". (It can retry silently). Andy Gayton, @cablelounger: this is corrosive. Ben: What is corrosive?](https://datastar-instant-intent.ndyg.cross.stream/static/thread.png?v=9b706ca3)

I was having an X [conversation](https://x.com/ben_codez/status/2126084141187846347) with [@ben_codez](https://x.com/ben_codez), and
they asked: why is showing an update as succeeded, before the underlying
operation has actually succeeded, corrosive?

It's corrosive because it normalizes software that is plainly broken and
doesn't respect our users. If a user flips a switch, and sees it flip, and then
comes back, and the switch is unflipped, the software is broken. How can you
operate software that doesn't do what you request it to do? It erodes trust.

## Ben's position

I made a chart of what I understand to be Ben's position on communicating with
their users.

1. **"Booking confirmed"** shown before the server checks the seat **No self respect** Ben: "No self respecting dev would show the user a booking had succeeded before server verification."
2. Ben's line **Your like shows as done** before the server says "ok" Ben: "liking a post", "(It can retry silently)." If the user closes the tab before the server has it, their like is lost and the user is never told.
3. Instant intent show only what is known to be true **Your post shows greyed out** until the server says "ok" Ben: "Right!", to a post shown "greyed out maybe, to indicate it wasn't committed".

## Demo

But in addition to that, it's actually *easier* to make software that doesn't
lie to your users. You can skip all the reconciliation machinery that's required
to create UI that communicates to users that the change they thought had gone
through had indeed not gone through.

Here's a quick demo of using instant intent to communicate the state toggling a switch e.g. a like button.

### Client-side affordances

When you click the switch, the client shows the button as pressed straight away and sends the click to
the server. The switch takes no more clicks while it's pressed, and if there's
no answer within half a second, it starts to blink. The client then won't update until the server answers with the reconciled HTML view, which Datastar morphs in place.

Experiment with different latencies and taking it offline, to see how the interaction feels under different scenarios.

The pressed and blinking look is the same CSS the seats use, on the
[main page](https://datastar-instant-intent.ndyg.cross.stream/).
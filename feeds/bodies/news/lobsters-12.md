Remote attestation is a term for technology which is used to verify the software
that another device is running. Usually remote attestation technology is implemented
in hardware, making it difficult to get around.

It is a building block of extremely restrictive DRM systems, as it allows a third
party to police what the user can or can't run on a device that is (at least
supposed to be) theirs.

An example of an implementation of remote attestation is Google Play Integrity.
This is software that can tell a third party whether you are running a Google-approved
Android system. It is mainly (but not exclusively) used by bank and government
apps.

The reason it is implemented is "security", but as I'll talk about in the next
section, the actual reason is one of control. It allows Google to decide what
someone can or can't run on their device. It strips all ownership of a device
that should be yours away and puts Google in control as the arbiter of what is
or is not acceptable.

Because of this, the user can't choose what they do with their devices anymore,
they can only do what is approved by Google. If they exercise their freedom at
all, by using a modified version of Android, an alternative operating system,
or emulating the app, the app will refuse to run.

Do you want to be able to use your banking app on your laptop or desktop? Tough
luck! You're not allowed to. (Even though you should be! Emulation is great for
interoperability!)

Some may tell you that the built-in Android hardware attestation is a good
alternative, it is not. It still does the same thing.
There is also Volla's [Unified Attestation](https://uattest.net), which is the
same thing, just with a different authority.
None of these are solutions as they just replace one authority with another.

This is an autonomy, freedom and interoperability nightmare, and must not be
tolerated. There should not be any external authority able to police what I do
on my own devices.

On the Apple side, there is Apple App Attest, which is the same harmful technology.

Currently, (as far as I am aware) remote attestation isn't used on consumer
desktop systems, but we need to stay vigilant to make sure it never does.
Object to it whenever it even gets suggested.

Note: [A friend](https://gaysex.cloud/notes/ap633tnb5fia0145) has made me aware
that anti-cheat systems use remote attestation. So it is in use on desktop systems.
Anti-cheat systems are their own flavor of abuse, and somehow my mind sorted them
into a different bucket. Still, yikes.

A common justification that is given for remote attestation is "security". At
face value, this may make some sense, as the remote server can verify that you
are running a "legitimate" copy of the software on a "legitimate" operating
system.

The big problem here is that someone has to decide what is legitimate and what
is not, and that this remote party is almost never the user of the software. In
effect, what remote attestation does is give someone else the ability to decide
what you can or can't do on a device you should own.

This then begs the question: Security for **who**? It's definitely not for the
user, as they are locked out of their device. Their security and autonomy have
been harmed significantly.

If someone can't run whatever operating system they'd like and still be able to
use the apps they need, then they are completely at the mercy of whoever is
the authority judging what software is good and what software is bad. We all know
how that ends, as big tech companies never have the best interests of the user
in mind. Whenever the interests overlap, that is a freak accident, not the norm.

All of the security is for the authority judging your device, none of it is for
you.

Our personal devices are in a very real sense extensions to our body, which means
that bodily autonomy should in some way extend to them. What this means is that
everyone must have **full** control of their personal devices and everything that
runs on them.

This includes having access to all of the code and being able to do whatever
you want with it, including modifying it, building it yourself, and sending
copies to anyone. (modified or not)

There should be nothing that the user is not allowed to do on their own devices,
and every single application running on their device must be held to the same
standard. It is your device, so everything must run under your rules, and only
your rules, no others.

The developer or their company should not have any say over how you use your
device, you should be able to run their software in whichever way you wish and
they must not be able to prevent that. You should also be able to emulate
whatever you like.

It's **your** device, no-one except you should be able to decide what runs on it
and in what way it runs. Any app running on your system is supposed to be under
your full control.

Remote attestation is a technology that might have some use cases, but the
overwhelming majority of those use cases are extremely hostile to the user. For
that reason, I believe it must be objected to in its entirety. Our personal
devices should be ours, and ours only. They must not be under the control of
anyone else, and no one should be able to decide whether our devices or the
software they run are legitimate or not.

- ![This website was created using makko](https://lumi.codeberg.page/badges/makko.webp)
- ![UBlock Origin Now!](https://lumi.codeberg.page/badges/ublock.png)
- 
- 
- 
- 
- 
- 
- ![Fuck AI Code, Writing, Music, Art and Chat](https://lumi.codeberg.page/badges/fuckaieverything.gif)
- ![Polyproto](https://lumi.codeberg.page/badges/polyproto.png)
- ![Polyphony](https://lumi.codeberg.page/badges/polyphony.gif)
- 
- ![No AI](https://lumi.codeberg.page/badges/noai.png)
- ![Codeberg](https://lumi.codeberg.page/badges/codeberg.gif)
- ![Starlight Network](https://lumi.codeberg.page/badges/starlightnetwork.png)
- ![AerynOS](https://lumi.codeberg.page/badges/aerynos.png)
- ![Keep Android Open](https://lumi.codeberg.page/badges/keepandroidopen.png)
- ![People Pledge](https://lumi.codeberg.page/badges/peoplepledge.png)
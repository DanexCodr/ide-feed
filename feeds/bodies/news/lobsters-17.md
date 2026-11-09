Something really important just happened with vulnerability disclosure and open source. No, it’s not PHP and that dumpster fire of a week.

I speak of something Curl just did that probably won’t make the news anywhere because to most people it won’t really make sense. Curl just announced that all low and medium security reports should go into the public issue tracker instead of being privately reported

The basic idea is for vulnerabilities rated low and medium severity, they will be treated like regular old bugs instead of a special bug that needs extra attention. I think this is a great idea and a policy we should be encouraging open source projects to adopt something similar. Open source projects are drowning in vulnerability reports, this should help remove some of the pressure.

## First, what is an embargo?[#](https://opensourcesecurity.io/2026/10-embargo/#first-what-is-an-embargo)

In the world of security vulnerabilities, there’s this idea we call an embargo. If someone finds a security vulnerability in something, open source, closed source, it doesn’t matter what. You report this to the vendor/project in private and give them some time to fix the vulnerability. This makes sense for security bugs, the intention being there is time to get the fix ready before it goes public and the attackers start popping shells.

We do this for pretty much all vulnerabilities. Even the really boring ones. Every project, every vendor, everything. It’s just the way it’s always been done, so we keep doing it. This made sense when there were a few hundred vulnerabilities reported per year. We now have a few hundred CVEs being reported per day. It’s not 2005 anymore, we need to stop pretending it is.

Your first thought might be “isn’t a private report better?” and this is where things enter the truth is stranger than fiction part of the story.

## Why nothing makes sense[#](https://opensourcesecurity.io/2026/10-embargo/#why-nothing-makes-sense)

You know how when you go to a presentation and the presenter will ask a question that has 3 answers on the screen and the correct answer is always the most unlikely one? That’s basically what’s happening here.

It seems like privately reporting all security bugs is a good thing. It gives projects time to understand the bug, and create a fix, then release the fix all before the bad guys know what’s happening. Everyone wins!

Except that’s not what really happens. Dealing with security embargoes in private is really hard to do. You have to be mindful of who you tell, you have to remember who knows what details about which bug as you probably have more than one thing in flight at a time. You can’t use the public git repos because that will leak the fix. That also means no CI testing. You can’t ask for a review from a community reviewer, or community testing because it’s a secret fix. Maybe the emails are encrypted, so you have to remember your PGP password and where you keep the key. You get the idea. The usual process falls apart, it’s mentally exhausting for anyone doing this. There’s a reason big companies have teams dedicated to doing this sort of work and only this (and even then they screw it up all the time).

When most embargoes leak it’s not because someone is dumb, it leaks because someone forgot a step in this 300 step process.

Now do this for free, and do it 100 times a month. That’s open source today. Every. Single. Project.

## Open source is getting hammered with security vulnerabilities[#](https://opensourcesecurity.io/2026/10-embargo/#open-source-is-getting-hammered-with-security-vulnerabilities)

One other important bit of backstory we need to cover is that every single software manufacturer is getting slammed with vulnerability reports. All of them. Open source developers are seeing large increases in the vulnerability reports they are getting. Closed source vendors are releasing more security fixes in a month now than they used to release in a year.

Also keep in mind that in open source these are volunteers. A lot of them aren’t being paid to work on their projects. They spend nights and weekends working on this stuff. They started out wanting to build a fun simple library to make memes, and now they only handle vulnerability reports.

It used to be really hard to find security vulnerabilities and really hard to fix vulnerabilities, so the scale was balanced. Now it’s really cheap to find vulnerabilities but still really expensive to fix vulnerabilities, so the scales are all messed up. It’s not just popular projects or the big companies. It’s literally everyone experiencing this.

## Why are public security bugs better?[#](https://opensourcesecurity.io/2026/10-embargo/#why-are-public-security-bugs-better)

I don’t want to mislead anyone. Public security vulnerabilities will create some new and different problems especially at first. Everything from this point forward is speculation based on my experiences. We will have to see if this post ages like wine or like milk.

There is currently a view in the world of security that we have to fix all of our vulnerabilities. It’s getting better though. There’s a document from CISA called [BoD 26-04](https://www.cisa.gov/news-events/directives/bod-26-04-prioritizing-security-updates-based-risk). It basically says you should be patching vulnerabilities based on the actual risk instead of the general severity. Doing this helps avoid the patching nightmare that comes along with our current vulnerability tsunami.

However, if you are an open source project and you have public unfixed security vulnerabilities, you’re going to get wailing and gnashing of teeth asking you to think of the poor Fortune 500 company that needs the security fix ASAP so they can pass their audit. Even though BoD 26-04 says not to blindly patch everything, there are still plenty of policies and compliance standards that won’t catchup for many years, maybe ever.

Now, it’s very very VERY important to remember what open source promises about security fixes or any fix:

**THE SOFTWARE IS PROVIDED “AS IS”**

That’s it. You, as an open source developer, do not owe anyone anything. I know that’s hard to believe sometimes. Every open source developer has an amazing sense of care and duty to their community and they go to great lengths to help anyone they can. But in this instance it’s OK to say no.

It’s not that you’re never going to fix the bug. You’re saying you don’t want to deal with the mental anguish and technical challenges of embargoes. If someone insists you have to fix something right now because it’s public, tell them you want a job, or a donation, or a monster truck. It’s OK to push back on demands from strangers. You can tap the “AS IS” sign.

## Won’t this help the bad guys?[#](https://opensourcesecurity.io/2026/10-embargo/#wont-this-help-the-bad-guys)

If a critical vulnerability sits in a public bug tracker for months, maybe it will help the bad guys. But I mean, it seems like they’re doing pretty good right now.

This is the wrong question though. Will this help the open source developers? That’s a question we almost never ask. Open source is a natural resource that’s straining at the moment.

We can imagine every open source project is a closed system. There is finite time, finite developers, but seemingly infinite vulnerability reports. We can’t add more time and we generally can’t add more developers (at least not easily). So what can we change? We can change how we handle the infinite vulnerability reports. If we can make them less work for the project, that’s a big win.

An abandoned open source project that’s widely used is vastly more dangerous than an open source project filing public security bugs.

And let’s face it. Every well funded nefarious organization has armies of humans and AI churning away looking for vulnerabilities. It would not surprise me if they already know about these security bugs long before they get fixed.

## What happens next?[#](https://opensourcesecurity.io/2026/10-embargo/#what-happens-next)

Curl wrote a very nice policy about all this. Use it. I have no doubt they will be delighted to see other projects use their policy. One of the best parts of open source is we can stand on the shoulders of giants.

If you use the Curl policy, change it any way you want. Maybe you only want to embargo critical. Or maybe you don’t want to embargo anything. It’s OK, do whatever makes you happy and keeps you sane. We need to try out some new ideas and figure out what the best way forward is. And we can make changes instantly in the world of open source. If you don’t like the way the policy is working, change it.

I have an idea even more bizarre than this, but I won’t pollute this blog post with it, so stay tuned for a future post.

The thing to remember in all this is we can’t maintain the status quo. Things are very lopsided and lots of open source folks are burning out. The world is a better place with a healthy open source ecosystem. A healthy open source ecosystem needs healthy developers.

If handling fewer embargoes might keep you healthy, for the love of all that is good, do it right now.
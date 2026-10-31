*Published May, 2002 in Embedded Systems Programming.*

What are the top ten ways to protect congressional pages?  

            10. If our representatives are so enamored of 700 mile fences, well, build one around Congress.

Whoops. Wrong publication.

If David Letterman can have a Top Ten list, so can I. But instead of ragging on Mel Gibson or making fun of any of a vast number of Congressional scandals, I'll hit embedded systems. What are, in my opinion, the top ten reasons embedded projects get into trouble?

# 10 - Not Enough Resources

Firmware is the most expensive thing in the universe.

Ex-Lockheed CEO Norman Augustine, in his wonderful book "Augustine's Laws" (1997, American Institute of Aeronautics; ISBN: 1563472406) wrote about how defense contractors were in a bind in the late 70s. They found themselves unable to add anything to fighter aircraft, because increasing a plane's weight means decreasing performance. Business requirements - more profits - meant that regardless of the physics of flight they had to add features. Desperate for something hideously expensive yet weightless, they found. firmware! Today firmware in high performance aircraft consumes about half the total price of the plane. A success by any standard, except perhaps for the taxpayers. Indeed, retired USAF Colonel Everest Riccioni has suggested firmware-stuffed fighter airplanes and smart missiles are now so expensive that the US is unilaterally disarming (http://www.pogo.org/p/defense/do-010801-unilateraldisarm.html).

Face it: firmware is expensive, and getting more costly as it gets bigger. One hard-to-believe analysis (April 2004 Proceedings of the* First Conference on Computing Frontiers*) claims that embedded software doubles in size every 10 months. Couple that with the exponential relationship between schedule and size and it's pretty clear that within a few years firmware development will pretty-nearly consume the entire world's GDP.

Yet software people can't get reasonable sums of money for anything but bare necessities. While our EE pals routinely cadge $50k logic analyzers we're unable to justify a few grand for a compiler. How many of you, dear readers, have been successful getting approval for quality tools like static analyzers? Free/Open Source tools bring giant smiles to the head CPA. The statement "Just port GNU" is an early indicator of a looming disaster.

# 9 - Starting Coding Too Soon

Agile methods have shaken up the world of software development. Most value code over documents, which all too often is incorrectly seen as justification for typing , "void main()" much too early.

Especially in the embedded world, we don't dare shortchange careful analysis. Early design decisions are often not malleable. Select an underpowered CPU or build hardware with too little memory and the project immediately headed towards disaster. Poorly structured code may never meet real-time requirements. Should the system use an RTOS? Maybe a hierarchical state machine makes the most sense. These sorts of design decisions profoundly influence the project and are tremendously expensive to change late in the project.

Sometimes the boss reinforces this early-coding behavior. When he sees us already testing code in the first week of the project he sees progress. Or, what looks like progress. "Wow - did you see that the team already has the thing working? We'll be shipping six months ahead of schedule!"

# 8 - The use of C

C is the perfect language for developers who love to spend a lot of time debugging.

Flame away.

C is no worse than most languages. But there are a few - Ada, SPARK, and (reputedly, though I have not seen reliable data) Eiffel - that intrinsically lead to better code.

Ada, for instance, is still the favored language for safety-critical applications. Lots of research (for instance: http://www.stsc.hill.af.mil/crosstalk/2003/11/0311German.html) shows that Ada code has half or fewer bugs than C code. SPARK, a relative new-comer, achieves a sixth of Ada's error rate. One might argue that since Ada and SPARK are often used in high-reliability applications more effort goes into getting the software right. However, Ada programs can be produced for half the cost of C (http://www.adaic.com/whyada/ada-vs-c/cada_art.html).

I do like coding in C. It's a powerful language that's relatively easy to master. The *disciplined* use of C, coupled with the right tools, can lead to greatly reduced error rates. Problem is, we tend to furiously type some code into the editor and rush to start debugging. That's impossible in Ada et al, which force one to think very carefully about each line of code. It's important to augment C with resources similar to those used by SPARK and Ada developers, like static analyzers, Lint, and complexity checkers, as well as the routine use of code inspections.

So you can change #8 to the *misuse* of C. But the original title is more fun.

# 7 - Bad science

Bad science means one of two things. First, and most common, poor analysis of the real-world events the system monitors or controls. I remember working on a system many years ago when we discovered, to our horror, that lead sulphide IR detectors were more sensitive to ambient temperature than infra-red light. That necessitated a major redesign of the system's electronics and mechanics. Yet this was a well-known effect we should have known about. Then there are the systems that don't have enough A/D resolution, precision and/or accuracy to make meaningful measurements. Poor filter selection can produce noisy data.

The second type is when one stumbles onto something that's truly new, or something not widely known. Penzias and Wilson ran into this in 1965 as they tried and tried to eliminate the puzzling noise in a receiver. only to eventually find that they had discovered the cosmic microwave background radiation.

It's pretty hard to stick to a schedule when uncovering fundamental physics. But most of the time the science is known; we simply have to understand and apply that knowledge.

# 6 - Poorly defined process

While there is certainly an art to developing embedded systems, that doesn't mean there's no discipline. A painter routinely cleans his brushes; a musician keeps her piano tuned. Many novelists craft a fixed number of pages per day.

There's plenty of debate about process today, but no one advocates the lack of one. CMM, XP, SCRUM, PSP and dozens of others each claim to be The One True Way for certain classes of products. Pick one. Or pick three and combine best practices from each. But use a disciplined approach that meets the needs of your company and situation.

There are indisputable facts we know, but all too often ignore. Inspections and design reviews are much cheaper and more effective than relying on testing alone. Unmanaged complexity leads to lots of bugs. Small functions are more correct than big ones.

There's a large lore of techniques which work. Ignore them at your peril!

# 5 - Vague requirements

Next to the emphasis on testing, perhaps the greatest contribution the agile movement has made is to highlight the difficulty of eliciting requirements. For any reasonably-sized project it's somewhere between extremely hard to impossible to correctly discern all aspects of a system's features.

But that's no excuse for shortchanging the process of developing a reasonably-complete specification. If we don't know what the system is supposed to do, we will not deliver something the customer wants. Yes, it's reasonable to develop incrementally with frequent deliverables so stakeholders can audit the application's functionality, and to continuously hold the schedule to scrutiny. Yes, inevitable changes will occur. But we must start with a pretty clear idea of where we're going.

Requirements do change. We groan and complain, but such evolution is a fact of life in this business. Our goal is to satisfy the customer, so such changes are in fact a good thing. But companies will fail without a reasonable change control procedure. Accepting a modification without evaluating its impact is lousy engineering and worse business. Instead, chant: "Mr. Customer - we love you. Whatever you want is fine! But. here's the cost in time and money."

# 4 - Weak managers or team leads

Managers or team leads who don't keep their people on track sabotage projects. Letting the developers ignore standards, skip using Lint or other static analyzers is simply unacceptable. No relentless focus on quality? These are all signs the manager isn't managing. They must track code size and performance, the schedule versus current status, keep a wary eye on the progress of consultants, and much more.

Management is very hard. It makes coding look easy. Perturb a system five times the same way and you'll get five identical responses. Perturb a person five times the same way and expect five very different results. Management is every bit as much of an art as is engineering.

Most people shirk from confrontation, yet it's a critical tool, hopefully exercised gently, to guide straying people back on course.

# 3 - Inadequate testing

Considering that a few lines of nested conditionals can yield dozens of possible states it's clear just how difficult it is to create a comprehensive set of tests. Yet without great tests to prove the project's correctness we'll ship something that's rife with teeming bugs.

Yet embedded systems defy conventional test techniques. How do you build automatic tests for a system which has buttons some human must push and an LCD someone has to watch? A small number of companies use virtualization. Some build test harnesses to simulate I/O. But any rigorous test program is expensive.

Worse, testing is often left to the end of the project, which is probably running late. With management desperate to ship, what gets cut?

Design a proper test program at the project's outset and update it continuously as the program evolves. Test incrementally, constantly and completely.

# 2 - Writing optimistic code

The inquiry board investigating the 1996 half-billion dollar failure of Ariane 5 recommended (among other findings) that the engineers take into account that software can fail. Developers had an implicit assumption that, unlike hardware which is subject to structural problems, software, once tested, is perfect.

Programming is a human process subject to human imperfections. The usual tools, which are usually not used, can capture and correct all sorts of unexpected circumstances. These tools include checking pointer values. Range checking data passed to functions. Using asserts and exception handlers. Checking outputs (I have a collection of amusing pictures of embedded systems displaying insane results, like an outdoor thermometer showing 505 degrees, and a parking meter demanding $8 million in quarters).

For very good reasons of efficiency C does not check, well, pretty much anything. It's up to us to add those that are needed.

My wife once asked why, when dealing with a kid problem, I look at all the possible lousy outcomes of any decision. Engineers are trained in worst case analysis, which sometimes spills over to personal issues. What can go wrong? How will we deal with that problem?

# 1 - Unrealistic schedules

Scheduling is hard. Worse, it's a process that will always be inherently full of conflict. The boss wants the project in half the estimated time for what may be very good reasons, like shipping the product to stave off bankruptcy. Or maybe just to save money; firmware is the most expensive thing in the universe, so it's not surprising that some want to chop the effort in half.

Capricious schedules are unrealistic. All too often, though, the supposedly accurate ones we prepare are equally unrealistic. Unless we create them carefully, spending the time required to get accurate numbers (for instance, see http://www.processimpact.com/articles/delphi.html) then we're doing the company a disservice.

Yet there are some good reasons for seemingly-arbitrary schedule. That "show" deadline may actually have some solid business justification. A well-constructed schedule shows time required for each feature. Negotiate with the boss to subset the feature list to meet the - possibly very important - deadline.
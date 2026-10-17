I have often seen one engineer get much faster with AI coding agents; then adding a second engineer or a third on the same team doesn’t necessarily speed up development. Sometimes the “fast team” is just one person operating in a silo. What I wanted to understand was why teams didn’t seem able to move faster, even when they were trying.

What I found is that teams keep holding on to what they know while also trying to adapt to AI. The teams place agent-speed implementation within processes built for humans and thus slow it back down. The bottleneck is maintaining shared understanding, coordination, and a coherent direction while moving fast. Every person added needs more of all three, and the way we manage that traditionally doesn’t scale with agent speed.

## Rethinking How We Build

> The bottleneck limiting teams is not too much human judgement; it’s where and how we apply it.

Building the right thing and ensuring quality hinge on human judgement. It comes in the form of product definition, requirements, understanding how to apply architectural principles to solve problems in software engineering, as well as validating that our product can be released to customers.

Keeping up with agent speed requires setting aside the existing methods, processes, and points of friction we’ve put in place to manage and gate our own work. I’m not saying throw everything out the window, but if we want to build successfully and go faster, we have to work differently.

To come up with a solution, though, I did start by throwing a lot of things out the window, then added elements back. As an industry, we have rich expertise in software development, in honing judgement and knowing how to apply technology to real-world problems. But the mechanisms and tools we’ve applied to develop software need a clean slate rather than a simple tune-up. We need to be able to trust and verify that what we deliver matches what we designed.

## My Method: Anchor Engineering

In 2024, I [wondered how new abstractions would change the code we write](https://nappingtoheavymetal.com/post/2024-03-31-post/#question-3-what-will-the-sde-1-role-look-like-in-the-future-will-it-exist). That distinction between designing software and writing its code is central to Anchor Engineering.

I’ve been developing this method as the answer to all the callouts above: moving fast, high quality, enabling teams. I’ve been deep in a cave for the last few months building with a bunch of teams like this, with thousands of my own commits across those teams. I even ended up building an application that uses AI to narrate the scope of changes that go in each day - because reading that is a better use of time than reviewing 100 commits every day.

In this method, our human judgement is baked into the guiding context with an agent-specific focus on design: anchors.

AI does not care if the design you prescribe is high level or low level, it just needs to know what to build. This also means you don’t have to prescribe everything else for it to build the right thing; the anchors define what the right thing is, and you can let the agent fill in the rest.

It also serves as your team’s shared mental model and build plan. Both of these grew out of some of my [earlier work](https://nappingtoheavymetal.com/post/2025-07-21-ai-collaboration-identity/) on how AI context can be directed and kept in a specific “space” by storing text that served as anchors for specific behavior.

The shared context and mental model in the Anchor Book enable the team to work together closer to agent speed. For this, I recommend a small development team that stays in active conversation, whether working together in person or virtually. They all work off of the plan within the Book, and also update it as they navigate design and development progress. Engineers push and pull the Book as part of development which keeps them working in sync.

Here’s a first set of principles that guide this method. This post lays the groundwork; I’ll cover the details, examples, and mechanics of the method in follow-up posts.

## Principles of Anchor Engineering

### 1. AI amplifies the judgement of the people leading it

The result of engineering with AI is a reflection of the judgement applied at each step in the process. Anchor Engineering puts that judgement into the Book and its anchors so it becomes durable direction for every AI building loop. Engineers and AI sessions then continue from the same decision instead of reconstructing it through repeated handoffs.

AI has made software development more accessible, but using it effectively still requires engineering expertise, judgement, and domain knowledge. You can install a coding assistant, set it up quickly, and it will build *something*. What it builds entirely depends on your tool selection and configuration - and the context and instruction. The quality and depth of your instruction depend on the quality and depth of your expertise in software engineering - think of system design, scaling, knowing what works well and what does not given circumstances. AI does not replace the need for an expert; it amplifies the impact of an expert in the system it builds.

Consider the analogy of an AI-written document; we’ve all seen documents that on the surface look like they contain reasonable prose, but end up lacking where it counts. If you know the subject matter, you’ll probably recognize it very quickly. Writing software with AI coding agents can follow the same pattern. The result might be fine for some uses, but its quality depends on the expertise you bring to guiding its creation.

Judgement is part of the input to the software building process, guides the building itself, and verifies that the resulting software is correct and is ready to be deployed.

### 2. We own the process and the outcome; AI writes the code

**The code should look like AI wrote it, because AI is what will maintain it.**

This principle is a mental shift, and can be really freeing for us as engineers if we let it be; we stop editing and managing the code by hand. We own the goal, direction, and judgement in the process. AI writes, organizes, and iterates on the code.

We can appreciate beautiful code. Think of all the time we spent on this: the debates on your team about the best place to put brackets. We can mostly let this go. Correctness is critical; personal style is fleeting.

AI doesn’t care if code is organized around human aesthetic preferences; it does benefit from coherent patterns, clear and recognizable structures, well-defined constraints and use of standards it can recognize. Maintaining that helps AI maintain the code. Ultimately we humans care that the system is structurally sound, is correct, and satisfies the requirements.

> We own the result, not the editing.

### 3. All software building artifacts are part of the codebase

This principle might sound familiar and dredge up memories of trying to keep documentation and code in sync. This is different, particularly when the artifact you use to build your system is your primary tool for updating it, coupled with the previous principle of not editing code outside of the AI build loop.

The Anchor Book I mentioned above is the home for all of your building artifacts - it represents the design and definition of your system: the anchors for each part of that design, the criteria by which your agent verifies those anchors are satisfied, and the planned chunks of work you can assign to your agents. It is not simply documentation in the traditional sense.

Another way to think about it: the Book defines your system, and you deploy your agents to instantiate it in whatever language you want. You can use the same Anchor Book to build a system in Rust, then Python, then Java (as long as the language fits the intended application). I have used the same Anchor Book to flip the language mid-development. Initially it applied Python. Then I decided Rust might be more appropriate, so I used the Book to change direction without changing the actual design. The implementation language changed; the system definition did not.

This artifact is living documentation and system definition and should be version controlled along with your code.

### 4. Antifriction: Remove friction and unnecessary stopping points

When you assess your processes, ask yourself: what function does this stopping point serve, and what faster mechanism can carry that function? I call the answer antifriction.

This means we’re replacing something in our process that creates a human bottleneck with something else that lets the process go faster, without sacrificing quality.

This is where I find people start getting nervous and return to known methods. It’s important to look forward, not backward in this paradigm. Here are two examples from my experience.

#### Friction: Task Planning

Consider task planning for a small, focused team working with AI agents. The Anchor Book holds the context for the work that needs to get done to implement a system. If we additionally go to the manual effort of breaking the design down into tasks for team members, planning them into sprints, and assigning them - we are just where we started, with no wins and duplicated planning. If each engineer on the team using the Anchor Book and AI agents can knock out the amount of work in a day that would normally be planned across 4 weeks, the effort does not pay off.

The antifriction is milestone tracking instead of task tracking, so that the team can continue to move forward while still enabling program management to track the project, manage dependencies, and identify risks.

#### Friction: Team-Gated Code Review

Consider a team where the engineers guide their agents in developing code quickly, then depend on the team members to review their agent-written code. Teams review code to ensure issues are caught before they ship, verify code quality, maintain best practices and standards, etc. However, this is where speed goes to die. A team review is an asynchronous human gate, and putting it in a system with agent-produced code cancels out agent speed. As it is, on many teams a code review takes at least a day to get completed and teams still struggle to solve this with only human coders.

Instead, we enable our AI agents to apply automated testing and bug fixing loops and ensure that when the agent presents the resulting code to review, it has been through the testing gauntlet already. Having sound unit and integration tests, end-to-end tests, validation, etc. must take a front and center role in development (not that it shouldn’t have already). We make sure the AI agents eliminate as many errors as possible before completing the task, using not only AI adversarial and judge reviews but also deterministic testing. If you’re not mutation testing to test the output of your AI coding agent, you’re missing a great opportunity for a deterministic layer in your process; this step will test whether the tests the AI wrote catch deliberately introduced errors.

This is an appropriate point for a judgement check-in: the engineer who guided the agent should take a look at the resulting code and analyze it for structure and correctness, and validate that what came out of the AI building loop is what they expected.

The antifriction is removing the human team-gated reviews, and building out a comprehensive test plan for code changes. We keep a judgement step in the loop so that the engineer leading the AI building loop validates what was produced.

Code review also spreads knowledge and design context across a team; in this method, the Anchor Book carries that shared context and stays current as the team builds.

### 5. We don’t build with less understanding; we get to understanding faster

The method does not replace understanding with speed. It preserves the domain, design, operational, and implementation context required to build the system while reducing the time needed to assemble, share, absorb, apply, and update it.

I have talked with engineers off and on in the last year about what will happen to our mental model of the software we build if we are not “hands on” writing it, but instead defining it in terms of plain language text in markdown. Usually we build our mental models through writing the code, also through investing time in problem solving and designing, as well as explaining our approach and discussing with others. So how does this translate to a bunch of natural language directives to AI?

I designed the Anchor Book to be a structured artifact to ensure we can define a system with clear rules and outcomes with an implementation plan for AI agents. It tracks decisions, how they align with requirements and how those are realized in anchors, and then verified through tests in the code base. It also encodes human judgement within these mechanisms. Building the design into the Book means working with AI to ensure that what you are adding adheres to existing rules, or recognizing when it violates them and you need to solve the problem differently. This hands-on work creates a strong mental model in much less time than it would normally take to develop over the course of the project. We’re essentially compressing the time it takes to build and understand a full system, and creating the artifact that lives and grows as the system does. This means each person on the development team ends up with a crash course in the entire context for the system they are building - and a very rich mental model beyond the scope of what they’d normally need for task work.

## What Comes Next

Building at agent speed takes shared understanding, coordination, and a coherent direction. The Anchor Book is how I bring these together. In the posts that follow, I’ll show what goes into the Book and how a team uses it to design, build, and verify a system.
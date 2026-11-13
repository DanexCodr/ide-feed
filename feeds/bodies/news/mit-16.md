It all started with some exasperated emails. Back in 2009, a group of researchers began venting their frustration with the programming languages designed to help scientists and other researchers perform complex mathematical operations and statistical simulations without learning how to code. These programming languages were rigid and slow. If scientists built something that really worked, they’d need to rewrite the entire program in another language just to run it more quickly.

The emails turned into a research project at MIT with the mission of building an easy-to-use, high-performance programming language called Julia, which is designed for scientific research, data analysis, and modeling complex systems such as jet engines, drugs, financial markets, and robots, to name a few examples.

That research project turned into a lab at MIT, and the lab turned into the company [JuliaHub](https://juliahub.com/). Along the way, Julia gained a loyal following among scientists, engineers, mathematicians, and others. Today, the free and open-source language counts more than 1 million users, including people working in thousands of companies and universities around the world.

It is only a slight exaggeration to say Julia has been used to model everything under the sun, from the behavior of tiny atoms to [semiconductors](https://juliahub.com/videos/software-at-asml-the-force-behind-making-microchips), neural networks, [race cars](https://juliahub.com/case-studies/williams-racing-unlocks), and airplanes. It has also been used to study much beyond the sun, with astronomers [using Julia for imaging black holes](https://www.youtube.com/watch?v=xk-SIRH3sbE).

Julia’s secret sauce is in the way it compiles code depending on the type of data being used. Such “just-in-time compilation” makes Julia faster and more flexible than other numerical programming languages.

“Scientists and engineers are not programmers. Building scientific applications with multidisciplinary teams of scientists, engineers, and programmers is challenging,” JuliaHub co-founder and CEO Viral Shah says. “We asked: What if you could equip the scientists and engineers with a programming language that allowed them to express their ideas at a high level and also get great software performance?”

Making programming easy for non-programmers has been a north star for JuliaHub’s founders, who include Julia co-creators Shah, MIT professor of mathematics Alan Edelman, Jeff Bezanson SM ’12, PhD ’15, and former MIT research scientist Stefan Karpinski.

In April, JuliaHub’s team took another big step in that direction with the [launch of Dyad 3.0](https://juliahub.com/blog/juliahub-announces-dyad3.0-general-availability), the latest version of its AI platform to help engineering teams accelerate the development of complex physical systems like rockets, heat pumps, and satellites. Engineers are already using Dyad to direct autonomous AI agents as they work through physics simulations, safety analyses, quality controls, and more.

“With [Dyad](https://juliahub.com/products/dyad) 3.0, [you can upload data and design documents and the system will design an entire aircraft](https://juliahub.com/videos/automating-aerospace-systems-engineering-pdf-to-simulation-with-the-dyad-agent) for you,” Shah says. “Working with customers like Boeing, we are building agentic hardware design capabilities for engineers. Simplistically, you want to say, ‘Okay computer, build me a plane’; upload the design documents; and have the system account for all the physics, compile all the code, verify everything, and build the entire design agentically.”

**Humble beginnings**

After discussing the need for better programming languages for scientists and other researchers, Julia’s co-creators started the Julia Lab around 2009. The Julia Lab remains active in MIT’s Computer Science and Artificial Intelligence Laboratory.

The core idea was to create a high-performance platform that would excel at engineering, scientific, and mathematics applications. Shah says before Julia, scientists and engineers would either have to hire someone to build software for them or accept the slow performance of the few programming languages designed for them.

“We wanted to create something as easy to use as Python or MATLAB but as fast as the C programming language,” Shah says. “We built Julia for ourselves.”

Edelman says at first, the researchers didn’t think anyone would want their creation.

“We figured it would take 10 years before anyone was interested, but we said, ‘Patience is a virtue, so let’s do it,’” Edelman recalls.

The MIT researchers announced Julia with a blog post in 2012. They quickly realized many other researchers shared their frustration.

“When we first started, we were targeting interactive research workflows, but increasingly people are using it for everything,” Bezanson says. “Now we’re moving the whole stack of the language onto smaller, embedded devices as we evolve with our users.”

Since those early days, Edelman has taught a class on Julia with students from nearly every department at MIT. Today, he often learns students are already using Julia when they enroll in the class for applications as wide ranging as robotics, astronomy, physics simulations, and finance.

“Researchers come up to me and say, ‘I tell my supervisor I’m using Julia because it’s fast, but don’t tell them I’m using Julia because it’s really fun,’” Edelman says. “The key thing is Julia’s abstractions. A lot of times a coding language forces you to solve the one problem you’re thinking about. Julia’s language makes it so you’re solving not only the problem you’re thinking about, but other people’s problems around the world too. It encourages you to solve problems more generally.”

As Julia gained popularity, researchers around the world started asking the Julia team for support. By 2015, the demand became strong enough that they decided to start JuliaHub and help users through the company full-time. They received support from the MIT Deshpande Center for Technological Innovation and others at MIT to get the company off the ground.

JuliaHub’s work has evolved from simply helping users to advancing the language more generally. That’s powered an impressive list of creations from Julia’s loyal users. Julia has been used to simulate computer circuits, detect health disparities, model global climates and oceans, analyze brain activity, and more.

After someone built a pharmaceutical modeling platform in Julia, it was used to accelerate development of Moderna’s Covid-19 vaccine. In another case, researchers used Julia to create a [program for avoiding aircraft collisions](https://juliahub.com/case-studies/lincoln-labs). They found it ran about 50 times faster than an earlier version built on Python. Engineers at Meta used Julia to develop a better audio codec for WhatsApp’s 4 billion users.

“Over the years we’ve seen industrial, government, and academic users doing all kinds of interesting things with the Julia language,” Edelman says. “It’s honestly surprised us in many ways, the wide-ranging things people are using it for.”

**Autonomous design**

JuliaHub launched Dyad 1.0 in June of 2025 as a research agent to accelerate programming and Dyad 2.0 in December. The founders believe Dyad 3.0 represents a new level of ability and autonomy for designing complex systems.

“One important thing about Dyad is that it is a physics compiler and hence [enforces physical laws](https://help.juliahub.com/dyad/stable/tutorials/getting-started.html),” Shah explains. “General AI systems often solve physical problems in ways that violate physical laws. When using the Dyad agent, it will detect such violations and guide the agent in the direction of the physically correct solution. We expect it will decrease design times in product engineering by orders of magnitude, leading to months of work being accomplished in hours.”

One way Edelman sees the impact of Julia is through his class. One student recently used Dyad to model how robots move around in space. Another used it to build a rocket engine.

“At the end he said, ‘I couldn’t believe how easy that was — I just got a rocket engine!’” Edelman recalls.
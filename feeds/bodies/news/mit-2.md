Humans are intuitive by nature. We can sense meaning beyond the literal words that we encounter. Now, a new artificial intelligence-assisted learning platform developed by MIT engineers is enabling robots to read larger meaning into a human’s natural language commands.

In a study to be presented at the annual Conference on Robot Learning this month, researchers from MIT and New York University introduce [FLEX](https://arxiv.org/pdf/2610.28893), a flexible feature-editing pipeline for robot motion-planning.

With FLEX, humans can interact with a robot by giving it instructions in natural, conversational language. The robot can not only follow the instructions literally but also read into the words to draw larger generalizations that help to improve its motion-planning task.

The team demonstrated FLEX in several simulated scenarios, including one in which a robot serves a cup of coffee. In these virtual scenarios, a person interacts with a robotic arm by typing commands in natural language. As the robot moves the coffee cup over a cluttered table, the person might type “Don’t spill on the laptop!” In response, the robot will reason about why it should avoid the laptop. For this, FLEX incorporates a large language model (LLM) — a type of AI system that is trained on enormous libraries of text, including social media posts, video transcriptions, and web content, which the LLM uses to identify larger trends, patterns, and generalizations.

“LLMs have seen so many texts from the internet,” says study author Nathan Dennler, a postdoc in MIT’s Computer Science and Artificial Intelligence Laboratory (CSAIL). “People might have written about, ‘Oh, my phone dropped in the water and now it doesn’t work,’ or ‘I spilled coffee on my computer and now it doesn’t work.’ So LLMs pick up on the idea that liquids plus devices leads to things not working.”

Through the LLM, the robot reasons that it should also avoid bumping into all electronics. In its updated path, the robot adjusts to avoid both the laptop and a nearby phone, without the person having to explicitly spell this out.

“The idea is that there is some higher-level intention behind the words that you say,” Dennler says. “People naturally get this. But you have to carefully explain that to a robot, which takes time and effort. FLEX gives you an interface of communication with a robot to say, ‘When people say this, they mean that.’”

The study was led by Andreea Bobu, assistant professor of aeronautics and astronautics at MIT. Co-authors are Audrey Lee SM ’26 and Ilia Sucholutsky of New York University.

**Beyond what we say**

At MIT, Bobu heads up the Collaborative Learning and Autonomy Research (CLEAR) Lab, where her group develops autonomous agents that learn to work for, with, and around people. She is focused on developing assistive and household robots that can carry out physical tasks, and reason and adapt in real-time, in response to a person’s natural, conversational commands.

“Robots use math to do their trajectory planning. But we can’t expect a consumer to learn to do this math in order to tell a robot what to do,” says Dennler, who is a member of the CLEAR Lab. “Instead of having to get people to learn how to use a robot in a specific way, the goal is to interact with the robot through natural language.”

There is a large effort in the robotics community to incorporate natural language into robotic learning pipelines. Various strategies include using language to clarify a task’s goal, redirect a robot’s trajectory, and update its understanding of what is a safe path to take. These existing methods use natural language to tell the robot how to physically perform a task. But a robot could potentially learn much more from what we tell it.

Bobu and her colleagues are expanding what robots can learn from natural language commands. In their new study, they focused on enabling a robot to interpret a person’s underlying, unspecified preference from limited natural language commands.

**Absorbing common sense**

The team’s new robot learning platform, FLEX, is a three-step process that helps a robot read more into a natural language command, beyond what it is explicitly told to do.

The first step, “Add,” instructs a robot to add a feature to its list of things in its environment that matter for the task at hand, based on a user’s natural language command. For instance, as a robot is moving a bowling ball from one location to another, a person might interject with “Don’t drop it on my mug!” The robot would then add the mug to a list of things to avoid in its path. This first step is how previous methods have worked. Every time a person makes a correction, the robot adds to its features list, and updates its trajectory to avoid those features.

“The problem happens when your feature list becomes super long, and some features are no longer relevant because your environment may have changed,” says Dennler, who notes that this approach can grow tiresome if a person has to specify every specific feature to avoid.

The second step, “Generalize,” is the new solution that FLEX provides. This step incorporates an LLM — in this case, GPT-4o — that considers the mug, along with any other features that the person has so far specified to avoid. The LLM automatically searches through its vast cache of data for patterns and connections among these features, to ultimately make a generalization that it should avoid objects that are fragile, even when the person has not explicitly said so.

“LLMs have seen so many texts from the internet, from all sorts of people and places,” Dennler says. “Because they’ve trained so much on those things, some of that common sense gets absorbed into the LLM.”

In the third step, “Mask,” the robot’s standard computer vision system assesses its environment to determine what objects are no longer present, and then deletes those objects from its features list. This entire three-step process takes about five seconds.

The team tested FLEX in simulations of a robot arm carrying out three different tasks: serving a cup of coffee, moving a candle, and carrying a bowling ball. In all three scenarios, volunteers interacted with the virtual robot by typing natural language commands, such as “Don’t spill on my laptop,” “Stay away from the stack of paper,” and “Don’t drop on the mug.” With FLEX, the robot followed all three commands literally and also reasoned at a higher level to not spill on electronics, stay away from flammable objects, and not drop its cargo on fragile things.

“Everyone’s homes are different, and everyone cares about different things, so no robot comes out of the box knowing what matters to you,” Bobu says. “What excites me about FLEX is that it can pick that up from a sentence or two instead of asking you to spell out every rule — and that’s the difference between a robot people put up with and one they actually want in their home.”** **

This work was partly supported by the MIT Generative AI Impact Consortium and the MIT Schwarzman College of Computing’s Social and Ethical Responsibilities of Computing program.
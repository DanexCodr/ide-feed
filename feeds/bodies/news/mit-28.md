Researchers from MIT and elsewhere have developed a more user-friendly and efficient method to help networking engineers identify potential system failures before they cause major problems, like a cloud service outage that leaves millions of users unable to access applications.

The technique uncovers hidden blind spots that might cause a shortcut algorithm to fail unexpectedly when it is deployed.

This new approach can identify worse-case scenarios that an engineer might miss if they use a traditional method that compares an algorithm against a set of human-designed past test cases. It is also less labor-intensive than other verification tools that require engineers to rewrite an algorithm in a complex mathematical code each time they want to test it.

Instead of needing a mathematical reformulation, the new method reads the algorithm’s source code directly and automatically searches for worse-case scenarios that lead to the highest level of underperformance.

By helping engineers quickly and easily stress-test a networking algorithm before deployment, the method could catch failure modes that might otherwise only appear in a real outage. The technique could also be used to analyze the risks of deploying AI-generated code.

“We need to have good tools to measure the worse-case scenario performance of our algorithms so we know what could happen before we put them into production. This is an easy-to-use tool that can be plugged into current systems so we can find the best algorithm to use and ensure the worse-case scenarios are identified in advance,” says Pantea Karimi, an electrical engineering and computer science (EECS) graduate student and lead author of a paper on this new technique.

She is joined on the paper by senior authors Mohammad Alizadeh, an associate professor of EECS and a member of the Computer Science and Artificial Intelligence Laboratory (CSAIL); and Behnaz Arzani, a principal researcher at Microsoft Research; along with Ryan Beckett, Siva Kesava Reddy Karkarla, and Pooria Namyar, researchers at Microsoft Research; and Santiago Segarra, a professor at Rice University. The research will be presented at the USENIX Symposium on Networked Systems Design and Implementation.

**Assessing algorithms**

In large systems like cloud servers, the tried-and-true algorithms that route data from one place to another or are often too computationally intensive to run in a feasible amount of time.

So, engineers and researchers develop suboptimal algorithms called heuristics that can run much faster. However, there could be unexpected but plausible circumstances that will cause a heuristic to underperform or fail when deployed.

A heuristic can route millions of data requests across a cloud network in seconds, but under the wrong conditions — like an unusual traffic pattern or a sudden spike in demand — the shortcut can break down in ways the designer never anticipated.

When these problems occur, a company may have no choice but to drop some requests that can’t be processed.

The firm could also deliberately allocate more resources in advance to head-off a potential disaster, leading to higher overall costs and wasted electricity from underutilization.

“This is really bad for a company because, either way, they are going to lose a lot of money. If this particular scenario hasn’t happened before and was never tested, how would a developer know in advance before it happens?” Karimi says.

Stress-testing heuristics typically involves running a new algorithm in simulation using a set of human-designed test cases and manually comparing the performance with a previous algorithm. But this is time-consuming and can leave blind spots if an engineer doesn’t know to test for certain situations.

Alternatively, engineers could use a verification tool to evaluate the performance of their heuristic more systematically. However, these tools require the engineer to encode the algorithm into a complex, mathematical formula that can take days to flesh out. The process, which doesn’t work for every type of heuristic, must be repeated each time the engineer changes the code.

Instead, the researchers developed a more user-friendly and efficient verification tool, called MetaEase, that analyzes the heuristic’s existing implementation code directly to identify the biggest risks of deploying it.

“This would reduce the friction of using these heuristic analysis tools,” Karimi says.

She began this work during an internship at Microsoft Research, where the team previously developed MetaOpt, a heuristic analyzer that requires engineers to rewrite their algorithms as formal optimization models. MetaEase grew out of the desire to remove that barrier.

**Maximizing the gap**

MetaEase is driven by two key innovations. First, it uses a technique called symbolic execution to map out the different decision points in the heuristic's code. These are places where the algorithm might behave differently depending on the input.

This technique produces a set of representative starting points, each corresponding to a distinct behavior the heuristic could exhibit.

Second, from these starting points, MetaEase utilizes a guided search to systematically move toward inputs that make the heuristic perform as poorly as possible, compared to the optimal algorithm.

In machine learning, for instance, an input could be a set of user queries to an AI chatbot at a given time.

“In this way, we have exploited every possible heuristic behavior and used special techniques to move in the direction where we think the performance gap is going to increase,” Karimi explains.

In the end, MetaEase identifies the input that maximizes the performance gap between the heuristic and an optimal benchmark.

With this information, a heuristic developer could inspect the input to understand what went wrong and incorporate safeguards that will prevent the problem from happening during deployment.

In simulated experiments, MetaEase often identified inputs with larger performance gaps than traditional methods — pinpointing more catastrophic worse-case scenarios. And it did so much more efficiently.

It was also able to analyze a recent networking heuristic that no state-of-the-art method could handle.

In the future, the researchers want to enhance MetaEase so it can process additional types of types of data, like categorical inputs. They also want to improve the scalability of their method and adapt MetaEase to evaluate more complex heuristics.

“Reasoning about the worst-case performance of deployed heuristics is a hard and longstanding problem. MetaEase makes tangible progress by analyzing heuristics directly from source code, eliminating the need for formal models that have historically limited who can use such analysis tools. I was pleasantly surprised that it handles non-convex and randomized heuristics by combining symbolic execution with gradient-based search in a practical and effective way,” says Ratul Mahajan of the University of Washington Paul G. Allen School of Computer Science and Engineering, who was not involved with this research.

This research was funded, in part, by a Microsoft Research internship and the U.S. National Science Foundation (NSF).
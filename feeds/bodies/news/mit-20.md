Agentic workflows are artificial intelligence-powered software systems that chain together multiple models and external tools to tackle complicated tasks, like analyzing a video and answering questions about it.

But the way these highly fragmented systems are designed and deployed often causes inefficiencies that can lead to wasted computation, energy, and cost.

To improve efficiency, researchers from MIT and Microsoft developed an intelligent system that streamlines the process of designing agentic workflows and automatically optimizes how those workflows are implemented.

With this new method, a developer can describe what they want the agentic workflow to do in plain language, without needing to specify all the details of their application in advance.

The system automatically figures out the best models and tools to use, as well as the ideal hardware configuration and computational resource allocation when the workflow is executed by a cloud provider.

It adjusts those configurations on the fly based on each user’s priorities, such as minimizing costs or maximizing speed.

When tested on several agentic workloads, this new system reduced the number of computational units needed for deployment, significantly cutting energy requirements and costs compared to traditional approaches without hampering performance.

“Agentic workflows are getting very complicated and quickly becoming the backbone of what cloud providers are doing. Energy usage is a huge concern, so we need to be very careful about how efficient these workflows are. It is very easy to over-allocate resources, wasting energy and money. Enabling a cloud provider to intelligently make these workflows more resource-optimal is a win for everyone involved,” says Gohar Chaudhry, an electrical engineering and computer science (EECS) graduate student and lead author of a [paper on this system](https://goharirfan.me/publications/murakkab_osdi_2026_paper.pdf).

He is joined on the paper by Adam Belay, an associate professor of EECS and a member of the MIT Computer Science and Artificial Intelligence Laboratory; senior author Ricardo Bianchini, technical fellow and corporate vice president at Microsoft Azure; and others at Microsoft Azure. The paper will be presented at the USENIX Symposium on Operating Systems Design and Implementation.

**A configuration conundrum**

An agentic workflow is a system composed of several autonomous AI agents that collaboratively use various models and tools, like databases or Python programs, to dynamically complete a multi-step task, such data processing or code generation.

These workflows can serve as behind-the-scenes processes that power user-facing applications.

Typically, developers must hard-code all technical choices upfront. They need to define which AI agents, models, and tools to use, and the order in which to use them. They also must specify the hardware that runs the workflow and how to balance tradeoffs like speed versus cost.

This is especially challenging because agentic workflows bring together multiple black-box models and diverse tools, each with their own configuration options, which may be offered by different companies.

If a new AI model is released that would improve the application’s accuracy or efficiency, the developer would need to start from scratch to implement it.

“Even if you wanted to do all this manually, it is unlikely that you’ll be able to configure the workflow optimally because the space of possible configurations is so large,” Chaudhry says.

In addition, the cloud data center that deploys the application for customers can’t see inside the workflow to allocate its hardware resources in the most efficient manner at the time of the user’s request.

With this new system, called Murakkab (an Urdu word that means a composition of things), the researchers sought to optimize the entire agentic workflow process.

**Dynamic decision-making**

First, Murakkab enables developers to create an agentic workflow by describing their intent for the application in high-level terms, rather than detailing how* *the many components of that workflow should be combined.

For instance, a developer might describe a video Q&A application that extracts key frames, generates a transcript, and then answers user queries about the video.

“There are many ways to do this, and all these different models and tools have implications on how fast the application can finish the task,” he says.

Murakkab takes the developer’s straightforward specifications and automatically identifies the best existing models and tools to put together into the workflow.

It also determines which components need to run sequentially and which can be run in parallel to boost performance.

“The platform makes configuration decisions dynamically over time, so if a new model or GPU accelerator comes out tomorrow, the developer doesn’t need to worry about that,” he says.

When the cloud provider deploys that application for a customer, Murakkab optimizes the workflow by configuring its components to meet the user’s constraints, such as prioritizing accuracy while meeting a latency requirement.

It adaptively identifies ideal hardware allocations and deployment schedules to maximize efficiency in real time, then generates a workflow that is ready for the cloud provider to execute.

“Our system also gives cloud providers visibility into multiple workloads, so the provider can share computational resources in the most efficient manner while satisfying the constraints of users,” he says.

When tested on diverse agentic workflows for video Q&A and code generation, Murakkab met user requirements while using only about 35 percent of the computation required by other methods. It consumed only about 27 percent as much energy for less than 25 percent of the cost.

The dynamic nature of Murakkab also enables users to balance tradeoffs. In one instance, the system lowered energy consumption of an agentic workflow by more than an order of magnitude with only about a 2 percent drop in accuracy for the customer.

The system was also able to identify an unexpectedly ideal configuration for a model that selects video frames, optimizing performance for a video Q&A task. This type of optimization would be nearly impossible for a developer to do manually, Chaudhry says.

Next, the researchers plan to expand their system to more complex workflows and larger computing clusters while exploring opportunities to optimize new agentic applications.

“There is a lot of potential to make these workflows more resource-optimal so they consume far less energy, but we need to be thinking about this at the scale of major cloud platforms,” says Chaudhry.

This research was supported, in part, by the Semiconductor Research Corporation and the U.S. Defense Advanced Research Projects Agency.
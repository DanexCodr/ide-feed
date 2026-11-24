Artificial intelligence models are jacks of many trades, including writing, generating images, and creating 3D models. But they aren’t as helpful when it comes to testing robots or designs for vehicles in diverse environments, since they don’t understand physics as well as they do pixels or text.

To build an AI system that can reliably simulate a variety of physical scenarios, engineers need a range of physics data at a scale that isn’t yet feasible. That’s because it’s very time-consuming to get neural networks just a few data points they can understand. They rely on algorithms called “numerical solvers” to calculate physical properties at different points of a 3D shape. It’s a thorough process, but it takes so long that it limits how much data you’ll have to, say, test if your plane designs are safe and aerodynamic.  

A new pre-training approach known as “GeoPT,” developed by researchers at MIT’s Computer Science and Artificial Intelligence Laboratory (CSAIL) and Tsinghua University, gives simulation models a chance to learn physics in a broader, more efficient way. It virtually reenacts everyday mechanical interactions in 3D, showing how particles stop when reaching some part of an object. These simulations give the models a sense of how physics works, helping them model the real world more accurately, reach peak performance twice as fast, and train on up to 60 percent less data compared to leading models.

Soon, the project could help engineers predict how vehicles (like cars and planes), everyday items (including chairs and containers), and robots respond to various physical elements, such as wind, water, and collisions. The researchers believe their work could also be a step toward a physics foundation model, a backbone system trained on lots of data that can help AI tools generalize to different tasks.

“We believe physics is the third modality for AI models, after text and pixels,” says MIT PhD student and CSAIL researcher Minghao Guo, a co-lead author on a [paper](https://arxiv.org/abs/2602.20399) introducing GeoPT. “Our general-purpose model has the versatility to help build a world model for physics. Many models, such as those that generate robotics data and videos, are already well-versed in textual and visual data, but with physical accuracy, they’ll get more-realistic results.”

**Easy to use**

To use GeoPT, users simply upload 3D models of objects like battleships, passenger airplanes, and trucks, and specify the direction and speed of the force they want to simulate. The result is a kind of heat map showing how the object will be affected in different places. If you know the speed and direction (velocity) of the force you’re looking to simulate, you can capture it in GeoPT. This comes in handy when you want to simulate things like how a car would look after crashing into a wall, the ways light bounces around objects, and whether a boat stays afloat over turbulent waves.

But how does GeoPT “get” physics so well? Its knowledge comes from “synthetic dynamics,” a series of interactions between small particles and complex 3D shapes. GeoPT studied 1.3 million samples of synthetic dynamics, in which tiny spheres moved at various speeds and angles until stopping at a certain point on the object.

These particles basically “stick” to an object once they make contact, instead of moving through or bouncing off. Picture learning about physical interactions using marbles and action figures — similarly, simulation models can use synthetic dynamics to gain a feel for physics before they train on labeled data.

**Industry success**

The researchers found that GeoPT was particularly skilled at simulating industrial scenarios, as it outperformed state-of-the-art simulation models across benchmarks. The common thread: It reached peak performance faster than other tools, while needing significantly fewer labeled data.  

On a dataset of complex 3D shapes and their responses to wind currents and surface pressure, for example, GeoPT surpassed state-of-the-art models in speed, accuracy, and efficiency. It had similar triumphs in speed and accuracy in capturing how fighter jets responded to wind. When GeoPT tested how the hull of a boat handled both air and waves, it required 60 percent fewer labeled data to capture both physical forces and reached peak accuracy four times faster than top baselines.

The system even succeeded at simulating how different types of cars look after colliding with another object. It correctly predicted how 3D vehicles would deform while using less data than state-of-the-art baselines. Likewise, its simulations of how light would pass through what was essentially a toy rabbit were accurate, despite never training on that 3D model or light physics beforehand.  

“If your model performs well on industrial benchmarks, that means it can solve the hardest physics tasks,” says co-lead author Haixu Wu, an MIT postdoc and CSAIL researcher. “GeoPT was making high-fidelity simulations with over 100 million mesh points in seconds. This could make the tool extremely helpful for engineers hoping to test out blueprints for vehicles without needing to run so many physical experiments.”

The researchers add that their system is only a preview of the kind of physics world model they’ve been working toward. The team hopes to scale up their system, training on even more shapes and simulating more complex physical phenomena. For example, a more in-depth approach could help model weather patterns, test out different materials, and generate realistic videos.

“Using synthetic dynamics data is an exciting paradigm for imbuing physics into foundation models,” says Fei Sha, AI research scientist at Meta, who wasn’t involved in the research. “It challenges the traditional wisdom that physics and geometry are necessarily entangled in computation, and one must acquire costly and specialized data. The demonstrated success in a wide range of application domains leads us to this important juncture: We are ready to build physics foundation models, now and fast."  

Wu and Guo wrote the paper with MIT CSAIL colleagues including Zongyi Li, a postdoc in the lab; Zhiyang (Frank) Dou, a CSAIL affiliate and MIT PhD student in electrical engineering and computer science (EECS); Kaiming He, a principal investigator in the lab, associate professor of EECS, and a distinguished scientist at Google DeepMind; and senior author Wojciech Matusik, the Joan and Irwin M. (1957) Jacobs Professor of EECS and a CSAIL principal investigator. Tsinghua University Associate Professor Mingsheng Long was also a co-author. The team presented the paper at the International Conference on Machine Learning in July.  

The researchers’ work was supported, in part, by Neural Modular Physics Twin for Robotics.
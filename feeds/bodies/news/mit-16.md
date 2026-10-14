Most people think of the waterfront as the edge of the city. A team of MIT researchers sees it as a dynamic, Lego-like construction site.

Their new system, called “[FloatForm](https://senseable.mit.edu/floatform/),” is a swarm of small square robotic boats that assemble themselves into larger structures on the water, break apart, and reassemble into something new, all with minimal human direction.

Each robot, about the size of a dinner plate at 21 centimeters square, is a self-contained vessel with its own thrusters, sensors, and magnetic latches. Together, they hint at a future in which floating infrastructure could become more adaptive: a temporary platform after an emergency, a market on a canal, or a stage that appears for a festival and dissolves when the crowd goes home.

“Our FloatForm projects envisions a future where the waterfront becomes a programmable extension of the city, where autonomous boats can self-organize into bridges, platforms, and other useful structures on demand,” says Daniela Rus, the Panasonic Professor of Electrical Engineering and Computer Science at MIT and director of MIT’s Computer Science and Artificial Intelligence Laboratory (CSAIL). “This kind of distributed robotics opens new possibilities for mobility, emergency response, public space, and infrastructure on water.”

“With FloatForm, we are essentially turning static water surfaces into dynamic, programmable spaces,” says Wei Wang, lead author of a new [paper on the project](https://www.nature.com/articles/s41467-026-74527-6) and a former MIT research scientist who now leads the Marine Robotics Lab at the University of Wisconsin at Madison. “Imagine an urban environment where public space isn’t fixed, but can autonomously expand, contract, or reconfigure on demand.”

“We see it as forming infrastructure on the water, using a modular system to create one larger system,” says Alejandro Gonzalez-Garcia, a former researcher with MIT CSAIL and the Senseable City Lab. “If there’s an emergency, you could form a new bridge to alleviate traffic in the city. Or you could create floating markets and floating stages. If you want a more livable city, you want to use the water, too.”

The open-access work, [published today in *Nature Communications*](https://www.nature.com/articles/s41467-026-74527-6), comes from the labs of Rus and Carlo Ratti, professor of practice of urban technologies and planning at MIT and director of the Senseable City Lab, and grows out of [Roboat](https://news.mit.edu/2021/autonomous-taxi-roboats-1027), their joint project with the Amsterdam Institute for Advanced Metropolitan Solutions that put full-size autonomous vessels on Amsterdam’s canals. Those canals once carried the city’s goods; today, they mostly carry tourists.

“We explored whether the canals could be used for waste collection, or for transport, to offload some of the stress on the roads back onto the water,” says Niklas Hagemann, an MIT graduate student in architecture, CSAIL affiliate, and former Senseable City Lab researcher who has worked on the project since its early stages. “Urban areas are getting denser, so could you expand public space onto water that’s currently underutilized?”

FloatForm shrinks that vision down to tabletop scale to answer a harder question: How do you get dozens, and eventually thousands, of floating robots to organize themselves?

**Lessons from the ant raft**

The team found its answer in biology. Fire ants famously survive floods by linking their bodies into living rafts, with no leader choreographing the assembly. Each ant follows simple local rules, and a resilient structure emerges.

“Each ant is an independent agent,” says Gonzalez-Garcia. “We wanted each robot to have its own capabilities, the same way ant colonies form a raft.”

Most existing self-assembling robot systems, on water and elsewhere, rely on a central computer dictating every move. That approach is vulnerable to single points of failure and scales poorly: The planning math balloons as robots are added, and the swarm must assemble sequentially, with most robots idling while they wait their turn. FloatForm flips the balance. A lightweight central planner steps in only sparingly, assigning each robot a final position to perfect the lattice, a level of geometric precision that purely distributed methods struggle to guarantee. Everything else, including navigating toward the target shape, avoiding collisions, and adapting to disturbances, runs on the robots themselves, which coordinate by exchanging positions with their immediate neighbors. The whole swarm moves at once.

That parallelism is what sets the work apart. The planning complexity of FloatForms approach depends only on a robot’s local neighbors, not the total size of the swarm. “What we’re trying to do is to have minimal central intervention, and have them all move together at the same time,” says Gonzalez-Garcia.

In experiments at MIT, a fleet of eight robots repeatedly gathered from random positions into a target shape, latched into a rigid structure, broke apart on command, reassembled into a new configuration, and then drove across the pool as a single vessel, with each run taking four to eight minutes. In that final mode, called collective transport, a planner charts a trajectory for the whole structure and each robot computes its own contribution. “Every robot becomes an actuator,” Gonzalez-Garcia explains. Simulations showed the framework scaling smoothly to swarms of 64.

“The beauty of this largely decentralized approach is that the computation doesn’t get bogged down as the swarm grows,” says Wang. “Whether you are working with eight boats or 80, the entire fleet coordinates and moves simultaneously. Because the overall assembly time doesn’t significantly increase in principle, the system remains highly scalable.”

There's a physical payoff to sticking together, too. “Our boats become more stable by joining together, like the ant raft, if you have waves or currents,” Hagemann says.

**An origami handshake**

The robots connect through a latching mechanism hidden entirely inside each hull. A single servo motor at the center drives an origami-inspired auxetic structure, a geometry that contracts uniformly in all directions at once, pulling permanent magnets on all four sides inward to release, or pushing them outward to grab a neighbor across gaps of 10 to 15 centimeters. The magnets are arranged with alternating polarities, so the boats reliably click into clean square lattices.

The elegant part is what the mechanism doesn’t do: consume (much) power. A 3D-printed gearbox holds the latch in either state with the motor switched off. “It uses energy to latch and de-latch, but in between those states, it doesn’t use any energy,” says Hagemann. For infrastructure that might hold a configuration for hours, that matters. “Because the robots are so small, you can only have a battery so big,” adds Gonzalez-Garcia. “If they use less energy on latching, they can use more on computation, or on actually moving.”

Getting there took some humbling engineering. Four miniature thrusters arranged in an “X” give each robot omnidirectional motion, including turning in place, but they pack large forces relative to the robots’ tiny inertia, which made early prototypes twitchy and prone to aggressive spins at low speeds. The team added stabilizing fins to increase hydrodynamic drag and tuned the controllers to stay robust across robots that, at this scale, are never quite identical. The magnets posed their own problem: They held on so well that de-latching sometimes required the robots to twist themselves free.

**From the tank to the canal**

Across 10 trials, the system completed its missions without human intervention 90 percent of the time with four robots and 70 percent with eight. When things did go wrong, the architecture showed its resilience: A robot that briefly lost its bearings could rejoin the structure on its own, without bringing the whole swarm to a halt, and robots stuck in formation deadlocks learned to shake themselves free and retry.

Moving from a controlled indoor tank to a real canal or harbor will take more than confidence. “There’s always a relationship between the size of a boat and the magnitude of the disturbance it can handle,” says Gonzalez-Garcia. “These boats are very small, so in very disturbed water, they cannot work.” Scaling up will mean reinforcing the latches, potentially with mechanical interlocking like the full-size Roboat used, and trading the lab’s ultrasonic indoor positioning for GPS or vision-based sensing. Helpfully, the coordination algorithm was designed to be sensor-agnostic: swap the sensors, keep the logic.

The team envisions applications well beyond city canals, from forming temporary platforms for offshore inspection and maintenance to adaptive sensor networks for studying migratory species to reconfigurable docking stations for emergency response in hard-to-reach areas. There is also potential for offshore and remote operations, from temporary construction platforms to environmental monitoring and scientific expeditions.

And the geography is wide open. “Venice, the Netherlands, Belgium, the fjords and lakes of Norway, really any city with a river can take advantage of this,” says Gonzalez-Garcia. “The project uses spaces where water is already important, but it also raises the question: Where else can water be used for something more?”

“This is an exciting step forward in realizing distributed collective behaviors on water,” says University of Michigan Assistant Professor Steven Ceron, who wasn’t involved in the research. “Assembly, self-reconfiguration, and collective motion are difficult enough in dry environments, but achieving these behaviors in a predominantly distributed fashion on water represents a serious additional challenge, and this team has credibly overcome it. By shifting the computational burden onto the robots themselves, they have built a more resilient system that in the near future could enable robot collectives like this to be deployed in open-water environments for search operations, environmental monitoring, and reconfigurable marine infrastructure.”

Gonzalez-Garcia, Hagemann, and Wang wrote the paper with senior authors Ratti, who is also a professor at Politecnico di Milano, and Rus. Gonzalez-Garcia is additionally affiliated with the MECO Research Team at KU Leuven. The research was supported by a grant from the Amsterdam Institute for Advanced Metropolitan Solutions, with additional support from the University of Wisconsin at Madison. The team thanks MIT Sea Grant and Professor Michael Triantafyllou for providing the test tank.
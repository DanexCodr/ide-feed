Imagine a bottle of hazardous chemicals sitting on a laboratory shelf that changes its appearance to alert scientists that its lid is not properly secured, potentially preventing a dangerous spill.

A new 3D-printing system created by MIT researchers enables users to produce interactive objects like this chemical bottle, which change their appearance when they are pressed, slid, or turned, without the use of any internal electronics.

Their system simplifies the process of designing and fabricating 3D objects with mechanically switchable surface appearances, enabling individuals without technical expertise to quickly generate dynamic everyday objects.

The design and fabrication system combines specially arranged optical layers with built-in mechanical parts so a single object can display different images or patterns. The resulting objects change appearance based on user interactions like screwing on a lid or flipping a switch, and they can be manufactured in one pass on a multimaterial 3D printer.

The system can be used to fabricate a range of interactive objects that don’t require fragile electronic circuits, such as adaptable warning signs that could withstand foul weather or dynamic packaging that alerts users if fasteners came loose during shipping.

The end-to-end system could also streamline rapid prototyping of adaptable objects for artistic, architectural, and engineering applications.

“With our system, an object can tell you whether you are using it properly, without the need for sensors or any complicated electronics. The interactive display is mechanical, so you can create a self-contained, multistate, interactive device that a user can control very intuitively,” says Yunyi Zhu, a graduate student in the MIT Department of Electrical Engineering and Computer Science (EECS) and lead author of a paper on this platform.

Her co-authors include Dingning Cao, an MIT undergraduate; Jeremy Mrzyglocki, a graduate student at the Technical University of Munich; Stefanie Mueller, an associate professor in EECS and the Department of Mechanical Engineering at MIT and a member of the Computer Science and Artificial Intelligence Laboratory (CSAIL); and Narjes Pourjafarian, a postdoc at Northeastern University. The research will be presented at the ACM Symposium on User Interface Software and Technology.

**Mechanically switchable surfaces**

Many interactive products rely on screens and electronics to change their appearance. But if these dynamic objects are exposed to water or harsh chemicals, or are squished, twisted, or pressed with great force, the fragile electronics could be damaged.

On the other hand, conventional methods that use surface optics to change an object’s appearance without electronics typically utilize static labels like stickers or curved lenses to create different visual effects based on where the user is looking, limiting interactivity.

To simplify the process of making dynamic, interactive objects that don’t require electronics, the MIT researchers developed a system that automatically converts a user’s design into a 3D printer-ready model of an object with a mechanically switchable surface appearance.

Their design, [ShiftLens](https://hcie.csail.mit.edu/research/shiftlens/shiftlens.html), creates switchable appearances by combining two optical layers on an object’s surface. It places a layer of special lenses over an underlying, patterned backplane.

The object displays different visual states based on the motion between the two layers.

The lens layer contains an array of tiny lenticular lenses, curved lenses which steer light differently depending on the viewing angle of the user. The pattern layer contains strips of images that correspond to multiple appearances of the object surface.

When the user shifts the lens layer, different parts of the backplane come into view. The lenses magnify these parts of the backplane image, changing the surface appearance.  

“The biggest challenge in this project was to make sure all moving parts align. We need to make sure that the optical effect, mechanical linkages, and computational graphics align with one another,” Zhu says.

**A straightforward system**

To simplify the design process, the researchers created a user-friendly tool that does all this work behind the scenes.

It automatically generates a ShiftLens structure based on a few inputs, including images of the visual states the user wants to achieve and the desired shape and curves of the object.

“Another challenge is to communicate to users who are not familiar with optics or mechanical structures and let them specify and achieve what they have in mind,” she says.

The researchers thought carefully about how to communicate the limitations of the ShiftLens design tool to the user. For instance, ShiftLens is not compatible with all objects, since it requires a shifting motion to enable interaction between the two layers.

Users can either incorporate a ShiftLens into the design of an object that has this type of interaction built-in, like the rotation of a lipstick tube, or integrate an actuation mechanism like a switch, knob, or roller.

“With ShiftLens, users can control what an object looks like while they are using it,” she says.

The researchers showcased how someone might use ShiftLens by fabricating a range of interactive objects.

In one experiment, they created a chemical bottle that turns green and displays a check mark when the cap is securely tightened, but turns red and displays an exclamation mark when it is loose. For another demonstration, they fabricated a tic-tac-toe game with squares that can display a red X, a blue O, or no letter, depending on which direction a user turns a knob.

While the ShiftLens tool is designed to simplify the fabrication process for makers, the techniques could be scaled up for commercial and industrial applications, Zhu says. For instance, it could be used to design piping that can change its appearance to identify a damaged connection that is causing a leak.

“The leaking sink in my apartment would be a lot easier to fix if it could tell me where the leak was coming from,” Zhu adds.

The researchers want to explore additional applications in future work. They also plan to develop an algorithm that can generate a ShiftLens structure with fewer user inputs, simplifying the design process. In addition, they plan to enhance the design tool so users can incorporate a wider variety of actuation mechanisms.
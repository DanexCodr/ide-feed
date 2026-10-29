A user who is frustrated with changes a social media company made to their favorite messaging platform, like the introduction of an annoying AI chatbot, can’t do much to address the situation, short of leaving the platform.

Now, MIT researchers are offering an alternative path.

They’ve created [Social.Wiki](https://social.wiki), a system that allows users to easily edit any social application made within Social.Wiki, and choose which of the edits made by others they want to see.

For example, a user could change a messaging site on Social.Wiki to remove an AI chatbot and instead add a restaurant voting feature so their group chat can finally decide where they are going out for dinner.

“The infrastructure that we are all dependent on online is very rigid. It is based on these one-size-fits-all applications that we don’t have a lot of power to change. This project is about trying to imagine what a different web would look like where anyone can participate,” says Theia Henderson, an electrical engineering and computer science (EECS) graduate student, and lead author of a new [paper on Social.Wiki](https://arxiv.org/pdf/2608.19433).

The researchers envision a world in which, if a user is unhappy with their social app, they can edit it to change it however they like — without getting cut off from their social connections.

The platform enables users with no coding expertise to create a range of websites, including social sites like photo sharing networks, discussion forums, and dating apps. It handles all back-end work, eliminating the need for creators to set up servers or arrange databases.

Social.Wiki employs a decentralized infrastructure that allows users to retain ownership of their data as they create, edit, and navigate social websites within the platform. It also includes a “data guard” that protects user data from malicious or buggy applications.

Through case studies and user tests, the researchers demonstrated the breadth of applications people can create with Social.Wiki, including a rideshare app where riders propose the prices they are willing to pay and a collaborative canvas for creating art together.

While Social.Wiki is still in its early days, the researchers plan to continue refining the platform as they deploy it to a wider audience.

“We want to empower the creation of far more social applications that meet the needs of unusual small groups. Each group is unusual, but everyone is in unusual groups. Everybody has their own needs for social applications that we want to be able to address,” says David Karger, professor of EECS, a member of the Computer Science and Artificial Intelligence Laboratory (CSAIL), and senior author of the paper.

Henderson and Karger are joined on the paper by EECS graduate students Carmel Schare and Ana Dodik; Clemens Klokmose, a professor of computer science at Aarhus University in Denmark; Ziv Epstein, a postdoc in the MIT Media Lab; and David D. Clark, an MIT research scientist. The paper will be presented at the ACM Symposium on User Interface Software and Technology in November.

**Letting users choose**

[Social.Wiki](https://social.wiki/#/v?/Social.Wiki) is a Wikipedia-like system in which users can navigate to different web applications or create their own web application within the Social.Wiki ecosystem. Each website has an “edit” button that allows any user to change the content of the site, from the text color on a message board to the pricing algorithm in a ride-sharing app.

Clicking the “edit” button in Social.Wiki opens a page that lets users view and edit the source code manually or prompt an AI assistant to make changes to the site.

This platform builds on the researchers’ prior work on [Graffiti](https://news.mit.edu/2025/system-lets-people-personalize-online-social-spaces-while-staying-connected-1001), a web framework with a decentralized infrastructure that makes building personalized applications easier.

With Social.Wiki, the researchers sought a collaboratively editable system that would allow anyone to revise web applications to be ideally suited for their needs and the needs of groups they belong to.

To enable this structure, Social.Wiki relies on a strategy the researchers call “plural governance.” Instead of a central moderator deciding which content users will see, each Social.Wiki user can choose the rules that determine which edits they will see on Social.Wiki webpages.

Users can also identify “trusted editors,” so they will see edits from individuals or organizations they consider reliable.

For instance, a user could customize their rules, or “governance policy,” so they only see edits to a site that have been endorsed by at least two of their friends. When the Social.Wiki browser loads a site for a user, it applies the governance policy that user selected to decide which version of the site to present.

For example, based on each user’s choices and edits, the system might show one user a ride-sharing app with a uniform pricing algorithm while another user might see the same app with a dynamic pricing algorithm.

“No website is tied to a particular machine. This means we have no centralized ownership over the websites or the underlying infrastructure,” Henderson explains.

**Security and creativity**

In this decentralized infrastructure, user data are stored separately from the websites that access it, which helps keep data secure.

Social.Wiki also employs a data guard, which prompts a user to review each request from a website that is attempting to access their data.

“In Social.Wiki, these websites are held in common and anybody can edit them, but the data guard makes sure that each user stays in control of what happens to their data,” Karger adds.

The researchers evaluated Social.Wiki through several case studies. For one, they developed a messaging platform that allows participants to modify the chat’s styling and interface without affecting the experience of others. In another, they built a collaborative ride-sharing app that enables riders to adjust the fare they want to pay using a transparent “living wage” calculator.

They also sponsored a hackathon in which users built Social.Wiki applications.

Participants developed a range of creative sites, including a [housing co-op communication tool](https://social.wiki/#/v?/coop?/f2-living) that organizes chats on a map of the co-op, as well as a [garden-themed microblogging site](https://social.wiki/#/v?/social-garden) where posts are “planted” as flowers.

“Even the little bit that has been done so far with Social.Wiki demonstrates that there is so much more that could be done with social apps if users could specialize them to meet a particular group’s needs,” Karger says.

Moving forward, the researchers are working to deploy Social.Wiki to a broader audience and gather feedback from more diverse user groups. They also want to make technical upgrades to enable end-to-end encryption on private message data and provide better developer tools.

This work was funded, in part, by Schmidt Sciences and the National Science Foundation (NSF).
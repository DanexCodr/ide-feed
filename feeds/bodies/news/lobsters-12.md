In 2012, I published an iPhone app called [SuperVote](https://supervote.org), which allowed Facebook
users to share political endorsements with their friends via a shared ballot. Other than two posts
on Hacker News (one in [September 2018](https://news.ycombinator.com/item?id=18032943) and
another in [November 2018](https://news.ycombinator.com/item?id=18388446)), I never had a
proper retrospective on my work. Because it’s been 15 years since I first started working on
the app, I felt it was a good time to revisit the development process and reflect on what
I’ve learned since.

Back in the early 2010s, California voters would receive a voter guide provided by the state
([June 2010 voter guide](https://vig.cdn.sos.ca.gov/2010/primary/pdf/english/complete-vig.pdf)),
which would include a list of propositions, with arguments in favor and arguments against a proposition,
along with rebuttals for both sides. A dedicated voter would need to spend a considerable amount
of time investigating all the options. At the time, I had a small network of friends and coworkers
that were well-informed and kept up to date with the latest on state politics. I felt that putting
together a single app that showed a custom ballot for yourself, along with the endorsements of your
friends, it would make voting easier.

# Origins

In 2003, I built this mockup page with the general idea of building a political site targeted
towards informing voters:

![supervote.com mockup](https://callejas.com/assets/images/supervote/mockup.png)

The iPhone did not exist in 2003, so this idea was a purely desktop web-based site. Beyond this
screenshot, no site was ever built, but conceptually it was a forum site with different boards.

I found a file called `supervote.txt` with the following description, which apparently drove the mockup
above:

```
Non-partisan, online political community where voters and political
organizations come together to discuss current ballot initiatives and
elections.

Participants contribute their opinions on a variety of
discussion forums.

Voter services include:

() Online voter registration
() Polling place locator
() Email alerts to new propositions in their district/state
() Access to discussion boards
() Participate in straw polls

Organization services include:

() Posting official positions on initiatives/propositions
() Posting announcements of activities and events
()

Organizations pay a monthly/yearly membership to join.
Individuals participants can join for free.
```

I owned the `supervote.com` domain from 2002 until 2008, with the intention of building out the
site, but for some unknown reason, I let my
ownership lapse. In 2012, I contacted the owner of the domain, asking if they were willing to sell it,
but I never heard back.

# Building SuperVote

For version control, I started off using Subversion, but eventually switched
to using Git. GitHub did not have free private repositories at the time,
so I set up a single Git remote server, hosting my repositories on a Linode instance.

Jira was a popular project tracking system for developers in the early 2010s.
Bugzilla was considered clunky and I had previous experience with Redmine and Trac,
but I was most familiar with Jira from my day job. I purchased a license when it was
possible to self-host on your own machine. I still have Z shell aliases to this day:

```
alias start-jira='sudo /usr/local/jira/jira-5.2.10-standalone/bin/startup.sh'
alias stop-jira='sudo /usr/local/jira/jira-5.2.10-standalone/bin/shutdown.sh'
```

At this point in my career, I had about 10 years of experience with Java, so I picked
Jetty to serve my API. I had experience with Ruby on Rails on a personal site, but they did not introduce a built-in API-only application mode until version 5.0 in 2016. I chose to use MySQL because of my
previous experience and ease of use.

I wanted to keep certain operations out of the request-response cycle (like building a user’s custom ballot), so I evaluated several message queues before settling on RabbitMQ. It offered a straightforward integration with the Java backend and was relatively easy to operate.

For this post, I made my source code available as a read-only archive on [GitHub](https://github.com/augustocallejas/SupervoteServer).

# Data Model

One of the more challenging aspects of SuperVote was designing a database that could represent the structure of U.S. elections and generate personalized ballots based on a user’s location. I designed a relational data model around governments, electoral districts, elections, ballots, and endorsements. The complete [database schema](https://github.com/augustocallejas/SupervoteServer/blob/master/core/data/schema.sql) is available on GitHub.

The foundation was a hierarchy of governments, including countries, states, counties, cities, and other municipalities, with support for exceptions such as independent cities and municipalities spanning multiple counties (e.g. New York City, whose five boroughs correspond to five counties). Electoral districts were modeled separately to represent congressional, state legislative, and local voting boundaries, which could change over time. During registration, users provided their address and ZIP code so the application could identify their associated governments and electoral districts, determining which elections and contests were relevant to them.

Elections were modeled as dated events associated with governments, containing contests for elected positions and ballot measures. Positions were separate from candidates, allowing the same office to be contested by different individuals across elections, while ballot measures represented questions requiring a yes-or-no vote. Each user’s ballot was associated with an election, with individual selections stored separately for candidates and measures. Users could optionally include a written explanation for their endorsements and control whether those endorsements were visible to others.

# Election Data

I started off by using the [VoteSmart API](https://www.votesmart.org/votesmart-api) to identify
legislative district by ZIP+4 code, but then I switched over to the
[Sunlight Labs API](https://sunlightfoundation.com/2009/09/24/sunlight-labs-api-one-year-later/) by the [Sunlight Foundation](https://sunlightfoundation.com), and a subset of the [Freebase database](https://en.wikipedia.org/wiki/Freebase_(dataset)) to map ZIP code to a U.S. county. I later switched to using the [Cicero API](https://www.cicerodata.com/api/) for mapping to legislative districts.

# iPhone App

Before this project, I had not written a single line of Objective-C. I downloaded the language guide,
along with the object-oriented programming guide, printed them out and read them over time:

- The Objective-C Programming Language (2010-12-08)
- Object-Oriented Programming with Objective-C (2010-11-15)

Reviewing my source code, I relied on several third-party libraries to simplify common development tasks. These included AFNetworking and ASIHTTPRequest for network requests, SBJson for JSON parsing, and EGOTableViewPullRefresh for implementing pull-to-refresh interactions. I also used utilities for displaying progress indicators, logging, and crash reporting. Many of these libraries have since been deprecated or superseded by functionality built directly into iOS.

I was aware of PhoneGap (now [Apache Cordova](https://en.wikipedia.org/wiki/Apache_Cordova)) as
an option to build for both Android and iOS, but I mainly focused on iOS since I had an iPhone
and did not have access to an Android device for testing.

For this post, I made my source code available as a read-only archive on [GitHub](https://github.com/augustocallejas/iOSVoter).

These screenshots show the typical flow of a new user:

1. Registration screen requiring the user’s voting address.
2. A simple privacy tutorial describing that endorsements can be made private.
3. A list of past and upcoming elections, based on your legislative district.
4. A ballot view, showing all available options.
5. A candidate view with the total number of endorsements by your friends by candidate.
6. An endorsement view allowing you to optionally explain your endorsement.

![Supervote iOS app welcome screen](https://callejas.com/assets/images/supervote/Screenshot_1.png)
![Tutorial](https://callejas.com/assets/images/supervote/Screenshot_1a.png)

![Upcoming elections](https://callejas.com/assets/images/supervote/Screenshot_2.png)
![Presidential ballot](https://callejas.com/assets/images/supervote/Screenshot_3.png)

![Presidential candidates](https://callejas.com/assets/images/supervote/Screenshot_4.png)
![Create an endorsement](https://callejas.com/assets/images/supervote/Screenshot_5.png)

![Created endorsement](https://callejas.com/assets/images/supervote/Screenshot_6.png)

# Facebook Integration

Facebook integration occurred on the client-side. It was as simple as cloning the
`facebook-ios-sdk` Git repository alongside my project. the Facebook SDK allowed me to retrieve a user’s
 riend list with their permission. If two Facebook friends
both used my app and created non-private endorsements, then they would be able to
see them.

Facebook also allowed registered apps to create custom activities on the timeline.
When a user created an endorsement on their iPhone, it would automatically publish
an activity on their timeline. This would allow friends who hadn’t downloaded the
app to see SuperVote activity of their friend, which would then encourage them to
download the app.

![Facebook activity log](https://callejas.com/assets/images/supervote/activity-log.png)

![Measure timeline](https://callejas.com/assets/images/supervote/timeline-measure.png)

![Candidate timeline](https://callejas.com/assets/images/supervote/timeline-candidate.png)

# Testing & Deployment

[TestFlight](https://en.wikipedia.org/wiki/TestFlight) was the easiest way to test
early builds of the SuperVote iOS app with friends via over-the-air.

Linode was an easy way to set up a Linux-based server back in 2011-2012. After building
a WAR (Web Application Resource) file of the API server, it was just a matter of copying it
over to my Linode server:

```
alias push='scp -P 44 ${HOME}/workspace/supervote-parent/server/target/server-0.9.0.war canaryfalls.com:.'
```

The Jetty server, along with an instance of MySQL and RabbitMQ all ran on the same Linode instance.

# Website & Marketing

I may have looked at Squarespace as an option to build a website, but I wanted full control on
the website’s layout and did not want to pay a monthly fee. I ended up finding a 
WYSIWYG website builder called [Freeway 5 Express](https://en.wikipedia.org/wiki/Freeway_(software)#Freeway_Express) that ran as a desktop application. I can no longer run this application on my Apple Silicon MacBook Pro.

I became aware of stock photography and the different available licenses: royalty-free versus
rights-managed. With Getty, I was able to find the exact images I was looking for and purchased
several royalty-free images that still appear on the [website](https://supervote.org).
Otherwise, I used Flickr images that allowed commerical use at the time with proper attribution.

For blogging, Tumblr had the easiest user interface for creating posts. I give Tumblr credit
for the blog looking the same for the last 15 years: [blog.supervote.org](https://blog.supervote.org)

I created a [Twitter account](https://x.com/supervote), Facebook account and Reddit account.
On Reddit, I attempted, but mostly failed, to promote the iOS app and blog posts 
using an [account](https://www.reddit.com/user/canaryfalls/) associated with the LLC I created.

I spent about $100 on advertising on Reddit. At most, I acquired a handful of users. I’m not sure
if I targeted specific subreddits or if I targeted the entire site.

# What Happened to SuperVote?

After the 2012 election, I updated the app sporadically, since there were no major elections
except for some municipal primaries in 2013.

In [2015](https://blog.supervote.org/post/112484919687/thanks), I decided to stop updating the iOS app and removed it from the App Store. In the end, the app had 400 registered users. The only
feedback I still remember to this day was that there wasn’t a full ballot for all users.

# What I Would Do Differently Today

Now in 2026, I would not integrate with Facebook for several reasons: 1) I don’t use Facebook
anymore 2) My Facebook friend’s list represents a snapshot of friends from 15 years ago, but
not today 3) I no longer believe family and friends are a good source for political opinions.

If I were building SuperVote today, I would place less emphasis on personal friendships and more on giving users access to informed perspectives from organizations and other trusted sources. Social features could still play a role, whether through private discussion groups or publicly shareable endorsements
(with keeping an eye out for [paid endorsements](https://www.nytimes.com/2026/08/29/us/politics/campaigns-paid-influencers.html)), but I would no longer assume that a person’s existing social network was necessarily the best source of political guidance.
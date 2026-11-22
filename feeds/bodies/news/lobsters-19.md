Today we launched a change that has been a long time in the making: The updated website for [freedesktop.org](https://www.freedesktop.org/), as well as the refreshed [wiki.freedesktop.org](https://wiki.freedesktop.org/) are live now!

You can read the announcement [here](https://www.freedesktop.org/news/2026/new-website-and-wiki/), this blog post elaborates a bit on it and on the background of the changes, as well as future plans.

### Why change anything?

The freedesktop.org website has been a wiki for a long time, which definitely was the right call in its inception. A wiki is very much in spirit of Freedesktop’s [mission statement](https://www.freedesktop.org/mission-statement/) to foster collaboration between desktop environments and to be a place to create de-facto standards.

However, over the years, working with the wiki became a bit of an issue: Not only did we face multiple spam-apocalypses (which in part motivated the switch to IkiWiki in 2013 and resulted in us heavily restricting write access to the wiki), but it also meant that official project information, finished specifications, half-finished proposals and pages nobody had touched in fifteen years were all sitting next to each other.

Since 2000 when Freedesktop.org was started, the project has grown so much and has had so many associated projects and specifications over the decades that it is now very difficult for new people to get an overview what is current and what state the software projects and specifications hosted by Freedesktop.org are in.

Having only a wiki as a large and somewhat disorganized pile of information did not help with that issue, so I worked to split things up: We now have a website as well as a wiki, using different designs to distinguish the two, and serving different purposes.

### Website & website plans

The website at [www.freedesktop.org](https://www.freedesktop.org/) will be the place for “official”, or rather, more curated information. Now that the new website is live, its content is still largely that of the old wiki. Over the next weeks, I will be working on cleaning up its contents and listings. For example, I will clearly split active projects from archived ones, add missing ones, and also work towards synchronizing the specifications hosted on the former wiki / website with the ones listed on [specifications.fd.o](https://specifications.freedesktop.org/).

So, basically I will do an inventory check of Freedesktop. That work has already started, but until now, I could not make any public changes to not disrupt workflows or make my own future work harder by having diverging information in two places (website & wiki).

I also wanted to make it easier for people to find information on how to [get involved](https://www.freedesktop.org/community/) with Freedesktop and associated projects, so the new website now has a more discoverable section for that.

The new website is a static site hosted via GitLab Pages and using [Pelican](https://getpelican.com/). You can [view its sources](https://gitlab.freedesktop.org/freedesktop/fdo-website) if you like.

### Wiki changes

Of course, we also still want to keep the Wiki and all of its rich history around! It remains the easy-to-edit place for collaboration on upcoming projects and specifications.

Wiki edits must now [happen through GitLab](https://gitlab.freedesktop.org/freedesktop/fdo-wiki) instead of the old [IkiWiki](https://ikiwiki.info/) web interface. While this sounds like an additional barrier to edit the wiki, it is significantly easier than requesting an account on *annarchy* to edit the old Wiki through the web interface. It also still allows us to keep the existing history as well as spam protection measures. In order to use the wiki with GitLab Pages and to keep the history easily accessible and readable, I rewrote the Git history of the wiki to make it pretend that all changes always happened in a `content` subdirectory. So, if commit signatures are missing and hashes are different: That is the only reason why. There have been no content changes or other metadata changes (and we still have a copy of the pristine wiki Git repository).

For the fd.o wiki, we are now also using Hari’s IkiWiki template that is already in use on the X.org website and which is much easier on the eyes.

### Next steps

At the moment, I am mostly concerned with ensuring that the change has not broken any existing links and all systems keep working. After that, the wiki 🡘 website deduplication work will start and we can modernize both the content of the website and wiki.

If you find a broken link, an outdated page or anything else that looks wrong, please [file an issue](https://gitlab.freedesktop.org/freedesktop/fdo-website/-/issues) or, even better, open a merge request.  
For the wiki, you are very welcome to just fix or otherwise update the page directly.

I did reach out to all wiki editors and projects impacted by this change in advance, but since there are so many people and projects involved, it is always possible to miss someone or something. If you found a bug, need edit permissions, or need help with anything, don’t hesitate to ping me: You can find me as `ximion` in OFTC’s `#freedesktop` IRC channel, in the very recently created [#xdg-specs](https://matrix.to/#/#xdg-specs:matrix.org) channel on the Freedesktop Matrix space, or you can email me.

### Thank you!

I do want to echo the announcement news post here: None of Freedesktop.org would exist without the people who filled it with life over the years and who worked on cross-desktop collaborative projects. I have read through a lot of wiki history and old project pages over the recent months, and it feels amazing to know how much work and passion people have poured into the projects and collaborative efforts over the years – no matter if they were successes in the end, or remained experiments. I am very thankful for all current, past and future editors of the website and wiki, as well as all project maintainers and contributors.

I also want to thank the [Sovereign Tech Agency](https://www.sovereign.tech/) once more for supporting me in their fellowship program as a maintainer, which enabled me to work on this task [among other things](https://blog.tenstral.net/2026/08/sovereign-tech-fellowship-for-freedesktop-tasks.html).

Thanks to all contributors, in whichever way you contribute to our free desktop ecosystem!
It feels like this month (and last month..) has been nonstop chaos. [PHP2Shell](https://en.wikipedia.org/wiki/PHP2Shell) threw a nice little grenade into an already busy month, and while that was happening a [GitLab RCE took down Alpine's GitLab instance](https://alpinelinux.org/posts/GitLab-security-incident-CVE-2026-97229.html). It was a whole thing, and as frustrating as it was, I'm kind of proud to say that I got to help respond to the event and write the incident announcement. Ikke did all of the real heavy lifting, but it takes a community to keep a distribution together. Everything, and I mean everything, is kept together by volunteers lending their time and talent with no expectation that there will be a reward for the effort.

We do it because we care for the work being done. Whether it's a critical service enabling a community of tens of thousands to distribute [hundreds of petabytes of data](https://gist.github.com/ncopa/b1515f99f5efbc82fcc8b15dcc5e1b4f) that we call "Alpine", or simply enabling a small piece of software to work for personal desires. All of it happens because someone cares enough to do the work. I love this so much, frankly. It's absolutely flabbergasting what we as a community can do with our spare time.

I enjoy giving my time to Alpine Linux, because there's a community, and because we can have an outsized impact on the world by collaborating together. It's not perfect, but it's rewarding. I think I owe my career to it in a sense. I've learned so much by simply raising my hand and being willing to give my time and learn a few new things. But there's a limit to how far you get on donated time, both personally, and as a project.

## Wiki.alpinelinux.org has been languishing a bit

Not in the sense that it wasn't used; it gets tons of traffic and contains a treasure trove of useful information that people depend on and are excited to contribute to. But between keeping the infrastructure afloat, migrating off of Equinix to new sponsored compute, and mitigating the constant wave of problems, from scale to RCE, that plague a small engineering team trying to serve a massive consumer base, well, it's no wonder that once alice was no longer contributing, the infrastructure languished a bit. This wasn't intentional, nor was it bad. There simply wasn't spare time to contribute to it.

So in November of last year ikke asked if anyone was interested in lending a bit of spare time to fixing that problem. Naturally, I raised my hand, happy to have an opportunity to do so.

> 2025-11-13 15:40:43     @ikke       Anyone helping with infra that wants to help maintaining the wiki?  
>
> 2025-11-13 15:57:01     durrendal   ikke: I don't mind helping out, just let me know what you need done  
>
> 2025-11-13 16:10:46     @ikke       durrendal: the wiki is hosted in an LXC container  
>
> 2025-11-13 16:18:11     durrendal   that makes sense, it tracks how most everything else is deployed. It's mediawiki, so php + a db. Is it using postgres on the backend, and do you have it behind traefik or something else?  
>
> 2025-11-13 16:22:07     @ikke       It uses mariadb  
>
> 2025-11-13 16:22:26     @ikke       There is an nginx proxy in front  
>
> 2025-11-13 16:22:51     @ikke       The database is in a separate container  
>
> 2025-11-13 16:26:56     durrendal   That's not bad, seems like a straight forward setup at first glance. I use mariadb for my zabbix deployments so that's nice and familiar  
>
> 2025-11-13 16:34:47     @ikke       The current setup uses a combination of git submodules and composer from what I can tell (alice was the last one taking care of it)

*All IRC timestamps in this post are in UTC.*

This was essentially the sum of information I got about the wiki; it was all that was really documented. And despite my eagerness to jump in immediately and lift it up from whatever state it happened to be in, it took time to get access. We had a release to get out. We were fighting to get 3.23 finished and didn't even get it wrapped up until 12/3/25! So it's no wonder that it took until 1/16/26 before I got access to the server itself to start poking around and even begin to understand how the deployment was handled.

And as you can guess by the fact that I'm writing this post in October of 2026, I did not get in there and immediately upgrade it and move on.

## I'm never one to half-ass something

And I think that's important. Even if I'm only giving away a limited amount of time, I hate to rush through things without fully understanding them. There's just no way I can improve something if I don't have a solid grounding. More importantly, I actually really love spelunking inside of old systems other sysadmins have set up. Everyone has a unique flair to how they deploy something. Enterprise admins end up deploying things in a real textbook manner, and when you deal with small businesses it's usually a hodgepodge of "just get it done". I haven't had a ton of opportunities to spelunk FOSS infrastructure though! What I found was interesting in its own right, mostly because I don't think I'd have deployed the service this way.

What ikke told me was spot on: MediaWiki was a git checkout with extensions and skins vendored as submodules inside the repo. You could slot in new modules using composer, and as long as you had an appropriate underlying PHP version to work with, you were golden. But that was then mixed with actual wiki data, like images, all of it lumped together in /var/www. Very simple, but not obvious if you'd not dealt with it before.

When I got into the server, MediaWiki 1.40.0 was running on PHP 8.2 on top of Alpine 3.20, but the LocalSettings.php that controlled the wiki was generated under 1.25.3. Just to give you a sense, 1.40.0 is from July 2023, and 1.25.3 is from October of 2015! It's really neat to get a sense for how long something was tended for. Of course, our friends at the Internet Archive have been archiving the Alpine Wiki since [April of 2010](https://web.archive.org/web/20100427195607/http://wiki.alpinelinux.org/wiki/Main_Page), and based on the main page I can tell you we've been using MediaWiki for a solid 16 years now, if not longer. I'm positive it's not the same exact server, but probably the same-ish data. I [made notes](https://lambdacreate.com/static/files/86/README.org) about all the little important bits I found, everything from extension inventories to known issues and interesting shell snippets I found in the server's history file. Anything can be, and is, helpful when you're spelunking. Truthfully, given the age of the deployment, the public facing nature of the server, and my relative newness to administering MediaWiki servers, I was approaching the problem with the utmost caution.

By the end of February I had MediaWiki figured out, [but it wasn't committed until March](https://git.alpinelinux.org/aports/commit/?id=7367609f39c95b464799ca81ea6ae36343d069e2). And not to bury the lede, but I mean that in the most me way possible. I went through the process of setting up a clone of the staging server in my homelab. From there I worked out how to package MediaWiki itself, and then break out all of the various extensions that comprise the core system into a proper APKBUILD. After packaging it, I was no longer surprised it hadn't been done before. The core extension list alone is absurdly long, and all told we use 36 different extensions for our wiki, so this isn't even a complete list.

```
subpackages="
	$pkgname-doc
	$pkgname-nginx:_nginx
	$pkgname-default-extensions:_default_extensions
	"
source="https://releases.wikimedia.org/mediawiki/$_pkgvermaj/mediawiki-$pkgver.tar.gz
	mediawiki_nginx.conf
	mediawiki_fpm.conf
	"

# Extensions bundled in the tarball that we split into subpackages.
# Core/mandatory extensions (always shipped with core) are NOT listed here.
# Only optional bundled extensions that users may want to enable individually.
_extensions="
	AbuseFilter
	CategoryTree
	Cite
	CiteThisPage
	CodeEditor
	ConfirmEdit
	DiscussionTools
	Echo
	Gadgets
	ImageMap
	InputBox
	Linter
	LoginNotify
	Math
	MultimediaViewer
	Nuke
	OATHAuth
	PageImages
	ParserFunctions
	PdfHandler
	Poem
	ReplaceText
	Scribunto
	SecureLinkFixer
	SpamBlacklist
	SyntaxHighlight_GeSHi
	TemplateData
	TextExtracts
	Thanks
	TitleBlacklist
	VisualEditor
	WikiEditor
	"
for _ext in $_extensions; do
	_ext_lower=$(echo "$_ext" | tr '[:upper:]' '[:lower:]' | tr '_' '-')
	subpackages="$subpackages $pkgname-extension-$_ext_lower:_extension"
done
```

And given the complexity, and that this was all production infrastructure, I tried to get it merged into the community repositories before making any sort of change to the production infrastructure. Anything less wasn't really right in my mind.

## But there wasn't room for it

But it sat, not because it wasn't appreciated, but because we are woefully close to the absolute maximum storage we can host through our CDN. Not that we weren't working on that either; I [started looking into our space limitations in earnest in March](https://lambdacreate.com/posts/static/files/86/alpine-mirror-analysis.txt), when it was a potential blocker to our ability to release 3.24 in June. I knew the package was too big to go into community, but I also didn't think leaving it in testing made sense for production infrastructure. So I turned my focus to the clearer, bigger problem and started working with ikke and clandmeter to figure out a path to archive our older distributions.

By May that problem had turned into discussions with Jason at the Internet Archive, which, as this little aside suggests, was the least stressful component of any of this. Jason is an amazing archivist, and the work the Internet Archive is doing is a massive boon to FOSS projects.

![Approval from Jason Scott, the lead archivist at the Internet Archive, for Alpine to archive our historical packages with them](https://lambdacreate.com/static/images/86/ia_email.png)

And of course, dear reader, I bet you can guess what happened next. I [packaged the ia tool](https://git.alpinelinux.org/aports/commit/?id=0921bb317d244f42d528fa4fc7fe89dc911a990d), built a prototype to [validate we could actually migrate things](https://archive.org/details/@durrendal/uploads), and when a prototype wasn't enough, turned it into its own tool, [arkivi](https://krei.lambdacreate.com/Alpine/arkivi), which can do partial migrations and reclaim space while it migrates data. None of that merged quickly either, because, well, we were out of space and had a release to cut. But once again, I had time to donate, and I wasn't going to provide half a solution to a problem I could solve.

## Wait, I thought we were talking about the wiki?

This might seem like a bit of a detour, but I swear it's not! We are in fact still talking about upgrading the wiki! I couldn't get the core MediaWiki package merged into a stable repo, let alone any of the extensions, which means it can't be released on a stable branch. As much as I personally trust Alpine and think we do a good job keeping edge decently stable, the reality is that it's a testing area sometimes, and it makes very little sense to run production infrastructure off of it. Or if you are going to do that, you need to ensure you have the time to keep up with the constant churn. You can probably guess my concern here: I might not have that time to give.

There are so many disparate but interconnected problems going on in the background of most FOSS distributions that you just can't fathom until you live with them. And the wild part? Nothing I've described is unique. I work within a community of clever and dedicated people who turn this type of work around on the regular. But as you can imagine, I lost my momentum on actually reviving the wiki too. I got blocked by infrastructure constraints and couldn't complete the task in what I felt was a professional and sustainable manner, so I simply waited. My small problem didn't outweigh the needs of the distribution, and there were bigger problems to solve elsewhere. The wiki was stable, it was fine.

Until it wasn't.

> 2026-10-21 20:56:33     @ikke       durrendal: would you have time to look at the wiki?  
>
> 2026-10-21 21:28:29     @ikke       From our monitoring it appears that at the peak, gitlab received ~50r/s, but it probably was even higher  
>
> 2026-10-21 21:33:01     durrendal   ikke: yeah happy to, php patches right?  
>
> 2026-10-21 21:33:20     @ikke       Yes, but also alpine upgrade  
>
> 2026-10-21 21:35:50     durrendal   yeah I can do that, I was waiting until mediawiki got moved to community, but I'll pin it to the version in testing and we can just deal with it all later, after the CDN has space.  
>
> 2026-10-21 21:36:17     durrendal   I think I only have access to the test instance currently  
>
> 2026-10-21 21:36:25     @ikke       right  
>
> 2026-10-21 21:38:56     durrendal   not a problem, just flagging it. I'll get testing done tonight. Heading home from work now and should have time shortly after

PHP2Shell isn't the kind of thing you leave running on a public server, and the wiki was sitting on PHP 8.2 on a branch that was already out of support. So the wiki went dark. We were forced to throw up a maintenance page and block people's access to the wiki. And of course people asked why, and when to expect it back. Like I said earlier, a lot of people depend on this resource to use our distro!

Which of course kicked off a fever pitch of building, testing, and migrating. I wasn't ready for this! I was missing extensions, I hadn't fully tested the database upgrade process, it wasn't automated, and my packages weren't in a stable repo!

But I wasn't starting from zero either. The core package had been sitting in testing since March. I had a clone of stage in my homelab, and a README full of notes about every odd corner of the old install. The better part of a year that looked like stalling had at least given me some sense of how to proceed.

## Why there was no quick patch

It would have been nice to take the easy out at this point, but it would have been the most temporary of bandaids:

- Alpine 3.20 hit end of active support in April of this year. We'd still backport changes on request, and this could absolutely have been one of those requests, but that's its own uphill battle with just as much effort behind it, and it would have resulted in a lesser fix. Realistically, a patched PHP meant moving to a supported branch.
- On 3.24, the MediaWiki package targets PHP 8.3.
- MediaWiki 1.40 was never going to run on PHP 8.3.
- So MediaWiki had to move too. We got lucky here: 1.40 to 1.46.2 is still a single hop. Had we been running anything older than 1.39, it wouldn't have been nearly so straightforward. 1.45 would have been an option, but it goes EOL at the end of 2026, and I wasn't about to do all of this twice.

So it was four upgrades at once: Alpine 3.20 to 3.24 (we're still working on 3.25 at the moment), PHP 8.2 to 8.3, MediaWiki 1.40 to 1.46.2, and the git submodule install to apk packages. Well, there really was no quick fix. Somewhere in that stack something would break, and it would keep creating problems down the line unless the work was done in a way that made it all easier to maintain long term.

## The harder path

Even if I wanted to take the quick path and just get the job done, that's the sort of logic that results in the same sort of languishing. Just run the old stuff, just upgrade the existing thing, keep it all similar, move onto the next thing. Sideload 1.46 the old way, get it up tonight, clean it up "later". I have so little time to give, and so many other important changes that need to be made. For anyone paying attention, that's only getting worse with the literal waterfall of RCEs being announced day after day after day, and we're expected to just keep up with it all. It's a lot, but it will only be worse if we cut corners and stop caring about doing it right. "Later" is exactly how the wiki got here in the first place.

Plus, that's not who I am. No, I'd rather dogfood a new tool I've been working on, finish the packaging work, and prove out that everything can and will work on a v3.24 mock and provide a good stable experience. Anything less would be unprofessional, an affront to the craft, or at the very least to my sense of pride.

Which leaves just one awkward bit. Despite all of my effort, the mediawiki packages are still making their way through testing. The work is never truly finished, there's always one more thing that needs to be done. But I'm confident once everything catches up the path forward is that much easier. Every mediawiki component and extension packaged provides a simpler maintenance path going forward. Nobody needs to remember anything I've described thus far. And anyone who wants to suggest an extension to make the wiki better can actively contribute to that process by packaging and testing it.

## And the dogfooding, oh the dogfooding!

It turns out that emergencies are great times to stress test the library coverage of a configuration management tool, especially when you need to spin up a box, test a migration, and repeat it over and over. I could have done all of this with some shell scripts or with Salt, but it's a lot more fun to use [scio](https://krei.lambdacreate.com/durrendal/scio) and figure out how well the little Lua DSL I've put together maps onto things I'd either do by hand or know well enough another way. The reps are the point. Every time something broke, I fixed it in the state, threw the box away, and ran it again from nothing, until a fresh Alpine 3.24 container could become a working wiki without me touching it. If you're curious what that looks like, the [full scio state is here](https://lambdacreate.com/static/files/86/mediawiki-test.lua).

If I as a contributor only have so much time to give, and my standard is that it's done well and to the best of my abilities, well, then I'll combine pleasure and work and solve two problems in one go. Servers get upgraded, I get a production grade test case for my configuration management system, and the entire thing is held together by spare time and tenacity!

I'll write more about scio in the near future. There's a lot to say, but now's not the time.

## Rehearsal

Did I mention I try to be meticulous? All of the preflight work isn't nearly enough when working with production infrastructure; I wanted to know exactly what I was touching. So naturally, I wrote a quick diff script to compare stage and prod, and the answer I got in the process was very reassuring. The two servers were nearly identical. The only real difference was prod's exposure layer, with go-away out front and nginx listening behind it. Then I wrote a backup script, because the existing backups weren't something I was willing to bet on. My process was obvious afterward: a throwaway incus container restored from a prod dump first, then stage, and only then prod.

Good thing, too. I could see every place I might trip, and I still managed to stumble.

First up was LocalSettings.php. Remember that file generated back in 2015 under 1.25.3? It had been carried forward through every upgrade since, collecting settings MediaWiki removed years ago (`$wgScriptExtension`, `$wgDBmysql5`, `$wgUseTeX`, `$wgShowIPinHeader`, `$wgSquidServers`) and path overrides pointing into a git tree that was about to stop existing. It fell over one dead path at a time. Fix a line, run the update, watch it die on the next one. Eventually I stopped playing whack-a-mole and just started over from scratch. A decade of "it still works, don't touch it", gone. I'll try my best to remember to leave a note for the next sysadmin who comes after me.

Even then, once I could actually open a page on the wiki, every image on it came back with "Error creating thumbnail: File missing." The old backups had never included uploads. The database was covered, but as far as the backups were concerned, every image anyone had ever uploaded to the wiki existed in exactly one place. Nobody was careless here. In the old install the uploads sat right alongside everything else in /var/www, and I hadn't understood where things lived well enough to notice they were missing from the backups. My mock tests never checked for them either. What an obvious and embarrassing look it would have been if I hadn't caught it on staging first!

But then I fucked up. On stage, I ran `php maintenance/run.php install` instead of `update`. It was late, it must have been nearing 1am or 2am at this point, and I wasn't fully paying attention. I should have stopped and rested, it could have waited another day, but I had committed to fixing this. If it's not obvious, install is for empty databases. Pointed at a real one, it overwrites an existing db with a fresh schema and admin account right on top of everything that's already there. Thank goodness I had a backup. I was able to easily restore the dump, put things back the way they were, start the whole thing over.

The rest were the kind of thing that just ate time, and they make for a pretty dull story. `$wgMainCacheType = CACHE_ACCEL` needs php83-pecl-apcu, and opcache doesn't count. The 3.24 mariadb client refuses non-TLS connections by default, so everything needed `--skip-ssl` initially. The packaged php-fpm listens on a unix socket rather than 127.0.0.1:9000, which I learned by way of 502s. Restored pages rendered stale, because their old page_touched values were older than the freshly built parser cache, which `$wgCacheEpoch` fixed. And AbuseFilter's grants were redacted in the capture I was working from, so I recovered them from the backup.

When it finally came together, the schema update on stage took 28 seconds. After all of that effort, 28 seconds.

> 2026-10-22 06:41:46     durrendal   ikke: I was able to get stage updated to v3.24, Mediawiki to 1.46.2 on php83.  
>
> 2026-10-22 06:42:32     durrendal   it was more time intensive than I had hoped so I didn't get to the prod server yet, but should be able to get to it tomorrow. about 3a here so I'm off to bed  
>
> 2026-10-22 06:42:48     @ikke       Alright, thanks so far!  
>
> 2026-10-22 06:43:45     durrendal   no problem :) I think prod will take less time now that I've worked out the kinks on staging.  
>
> 2026-10-22 06:46:22     ncopa       durrendal: thanks alot!

## Showtime

> 2026-10-23 10:00:21     ncopa       durrendal: are you still working on wiki.a.o?  
>
> 2026-10-23 11:34:07     durrendal   ncopa: yeah sorry for the radio silence, also scrambling at work over this. I should be able to finish it today though, I'll keep you posted.  
>
> 2026-10-23 11:34:19     ncopa       thank you!

That radio silence was the day job. PHP2Shell didn't just land on Alpine, it landed on everyone, and I spent my days scrambling over the same bug I was fixing for the wiki in the evenings.

By the time I sat down with prod, the hard part was over. It had become routine and easy because I put the learning up front where it belonged. Prod got a maintenance mode, a flag file that nginx checks on every request. Touch it and the world sees a maintenance notice, while requests from the box itself still reach the wiki, so I could test everything from localhost before anyone else could see it. Then the same migrations I'd already run on stage, with no surprises this time. Rsync the uploads into /var/lib/mediawiki/images. Carry over the parts of prod that make it prod: minor tweaks to php-fpm for performance, go-away, the easy stuff.

> 2026-10-24 02:40:57     durrendal    ikke ncopa the production wiki is fully upgraded and back online!  
>
> 2026-10-24 02:41:12     durrendal    https://wiki.alpinelinux.org/wiki/Special:Version  
>
> 2026-10-24 02:48:22     lotheac      nice!  
>
> 2026-10-24 02:57:20     durrendal    thanks :) and it's using packages instead of the old git submodule install too so hopefully this shouldn't languish ever again  
>
> 2026-10-24 02:57:57     durrendal    I just need to open a few MRs now

## Where it stands now

The wiki is on Alpine 3.24, MediaWiki 1.46.2, and PHP 8.3, and every piece of it comes from apk. Which means the next time a PHP2Shell comes along, the fix is `apk upgrade`, `run.php update`, and a php-fpm restart. No submodules or composer, nobody needs to remember something special, all that's needed is a bit of Alpine specific systems administration knowledge and we're golden. This will get better as I finish documenting the new installation, so that when I inevitably run out of spare time, the next person to raise their hand can stand on my shoulders and reach a little higher.

Look, at the start of this I said there's a limit to how far you can get on donated time. I meant that, but not to signal some kind of fundamental flaw in the system. Alice tended to this before me, ikke kept it running alongside everything else, and when it needed someone, someone raised their hand. This time it was me. There are many, many people like me, what I've described is not unique. But look what it took, eleven months from "anyone want to help maintain the wiki?" to an actual upgrade, most of it spent trying to solve other problems around the one that was volunteered for. When the emergency came, it got fixed because someone was willing to pay down the technical debt all at once.

That's what spare time can carry, and it's a lot. It's also why it matters that Alpine is choosing to [fund dedicated infrastructure engineering](https://opencollective.com/alpinelinux/updates/alpine-linux-is-changing-how-donations-are-used). Not because volunteers can't do the work, but because the work shouldn't depend on whether someone happens to have a free evening when the next CVE drops. Spare time built this wiki, and spare time will keep tending it. It just shouldn't have to hold it together alone.

As for me, I got what I always hope to get from raising my hand, an opportunity to learn. I walked in knowing very little about Mediawiki administration, and while I wouldn't call myself an expert from one small engagement, I'm happy to have come away with a few more packages, more confidence in scio, and a once more working wiki for Alpine. And a great reminder that part of giving your spare time is knowing when to stop, nobody will ever be mad that you ran out of spare time.
After Automattic's confirmation that they would switch their `.vibe` application to the replacement string of `.php`<sup>1</sup>, ICANN has started to publish various objections on the Application Comment Forum (ACF) section of their new gTLD program site<sup>2</sup>. They mostly relate to the confusion and security risk posed by a common filetype (especially in web development) becoming a TLD, similar to the outcry over Google's application for `.zip` (which was eventually successfully delegated). The other common theme is the objection to a private company effectively trying to claim what is an open-source project.

The first is by PHP developer Larry Garfield who accused the WordPress parent of "Inappropriate Squatting":<sup>3</sup>

> PHP is a widely used programming language. It is managed by the PHP project, an informal project at [www.php.net](http://www.php.net). It is also supported by The PHP Foundation, a non-profit organization managed through OpenCollective.

> No one organization, company, or person owns or controls PHP. Authority within the PHP language and ecosystem is deliberately diffuse.

> Automattic, the company that has attempted to register .php as a TLD, is the owner/author of the WordPress blogging software. WordPress is itself written in PHP and Javascript. However, Automattic has no ownership or control over the PHP language itself. In fact, Automattic and its employees are conspicuously absent from contribution to the PHP project itself, aside from in recent years becoming a large passive donor to The PHP Foundation.

> For Automattic, or any other company that operates in the PHP space, to try and lay claim to .php as a TLD is grossly inappropriate. There are dozens of other companies, projects, and interested parties that have just as much if not more claim to the name. PHP is a far larger ecosystem than just Automattic.

> It would be equivalent to Microsoft registering .rust (they use a lot of Rust now, but did not originate the language), or Hashicorp registering .golang, or IBM registering .java. None of those would be reasonable or appropriate, and neither is any one organization owning .php.

> One company owning .php would be significantly harmful to the PHP ecosystem, as it would give control over a significant branding and marketing channel to one company that is not engaged in the ecosystem, leading to market confusion and an easily exploitable way for that company to claim more authority and ownership than it actually has.

> The only organization that has any legitimate claim to register .php would be The PHP Foundation, but they have made no such attempt.

> The application for .php should be rejected outright as inappropriate "domain squatting." Its approval would be detrimental to a major software ecosystem, and establish a dangerous precedent for one company claiming an entire ecosystem's name without cause.

WordPress contributor Jamie VanRaalte objected on the grounds of "Part of a pattern - .php should not go to one company" and also said the `.wordpress` application was a similarly inappropriate power grab of another open-source project:<sup>4</sup>

> I agree with the comments already made here about .php. [I've been building commercial software in PHP for X years.] PHP is run by the PHP project and supported by The PHP Foundation, and no company owns it.

> I want to add one thing that's easy to miss when this application is looked at on its own. Knock Knock WHOIS There, LLC is a subsidiary of Automattic, and it has also applied for .wordpress. WordPress is an open source project too, and its trademark is held by the WordPress Foundation, not Automattic. So this is one company applying for the names of two open source ecosystems that it takes part in but does not govern.

> Automattic does use PHP heavily, but so do millions of other developers and companies. Using a language doesn't give a company any claim to its name. If .php goes to Automattic, it would decide who can register under the name of a language that belongs to everyone who uses it.

> If .php should exist at all, it should be held by The PHP Foundation or another neutral body accountable to the PHP community. This application, and the one for .wordpress, should both be rejected.

Web developer Ryan Maietta highlighted the "File Extension Confusion and Security Risks" of using an established filetype as a TLD and the risk of people confusing websites using this domain as being officially endorsed by the PHP project:<sup>5</sup>

> I oppose the proposed .php top-level domain because .php already has a widely recognized meaning as the extension for PHP files.

> I work in web development and sometimes use the open-source WordPress software. The .php extension appears throughout websites, source code, documentation, development tools and technical discussions. If .php becomes a top-level domain, the same text could identify either a PHP file or a registered domain name.

> For example, wp-login.php is the standard WordPress login script. If .php is approved and the name is available for registration, wp-login.php could also be a domain owned by someone with no connection to WordPress. A link shared in a message or technical discussion could appear familiar while sending someone to an unrelated website. Software that automatically turns text into links could make this confusion worse.

> The concern extends beyond WordPress. Someone could register domains that resemble PHP scripts or development resources and use them for phishing or impersonation. People may also mistake a .php website for an official resource endorsed by the PHP project. These risks are another reason I oppose the application.

> The applicant is an Automattic company. Automattic has a significant role in the WordPress ecosystem, but PHP is an independent, open-source language used by developers and organizations around the world. The interests of the broader PHP community deserve consideration.

> I ask ICANN to reject this application. The security risks are my most important concern, and my opposition goes beyond them. I do not believe a single private company should control a top-level domain so closely associated with a language it does not own.

Forensic analyst Herbert Bärschneider also objected simply on the grounds of confusing the TLD with the filetype:<sup>6</sup>

> When computer users browse the internet, they have to work with URLs. Such URLS can be complex and even appear cryptic to users.

> Users often tend to identify patterns and attach trust to those patterns - e. g. websites starting with "https" and "[www](http://www).".

> The long use of PHP as a way of creating websites will have lead to patterns which point towards "legitimate websites end with .php". By creating a TLD "php", this will lead to confusion. This confusion can be abused - allowing malicious third-parties to use the inherent trust in php Pages with .php domains.

> As security community, we should shield computer users from such abuse potential by not creating TLDs that mimik well-established meanings on the web.

And finally, the ICANN-affiliated Mark William Datysgeld described `.php` as being "Not viable from a technical perspective"<sup>7</sup> highlighting that he has already had issues creating the page for it on the PHP-based ICANN Wiki site, causing it to return a 404 error response<sup>8</sup>:

> .php" is the standard file extension for PHP, one of the most widely deployed Web languages. Software commonly treats any string ending in ".php" as a script or file path. Delegating .php as a gTLD would make every second-level registration, such as "index.php", both a valid domain name and a valid filename.

> This collision is already causing failures as-is. When creating the ICANNWiki article for this gTLD application, the entry was created in the database and appears in search, but it cannot be resolved and returns "Page not found", so even documenting this application will require a technical workaround. I expect the same class of failure in any system that routes or parses ".php" strings, which is to say, many of the Web's systems.

> I ask evaluators to consider this in the Safeguard Assessment and to put the following question to the applicant: what measures does it propose to address collisions between .php domain names and PHP file paths in software that routes or parses them? Given the scope of the issue, I also ask evaluators to recommend that this application not proceed.
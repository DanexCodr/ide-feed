AI models can now identify software vulnerabilities as effectively as top security researchers, and at a speed and scale that was not possible a year ago. This is ultimately [great news for defenders](https://blog.mozilla.org/en/firefox/ai-security-zero-day-vulnerabilities/): the defects in software like Firefox are finite, and it seems likely that increasingly powerful models will soon be able to find them all.

The Firefox team has worked tirelessly since February to identify and fix subtle bugs with early access to frontier models from Anthropic and OpenAI. To date, we have shipped more than seven times the number of security fixes compared to the same period in 2025. This result is a testament to the dedication of the Firefox team and the impact of labs putting these capabilities in defenders’ hands first.

This head start has allowed us to apply successive generations of frontier models to the Firefox codebase, each one helping us dig deeper. Attackers now have access to some cyber-capable models, but these models are several generations behind, and the depth of bugs they can find in Firefox has largely been picked clean.

## **The patch gap**

Ongoing access to frontier models allows Firefox to stay ahead of attackers, but can be undermined if attackers can indirectly learn about the findings of those frontier models. In particular, it is sometimes possible to work backwards from a security fix to identify the vulnerability in the original unpatched code. If an attacker can observe an upcoming browser update before most users have received it, there is a brief period during which they could reverse-engineer an incoming security fix and attack the prior version.

The *patch gap*, or the window in time between the appearance of a security fix in the code and the full deployment of that code to most users, affects any critical software that ships to end-user devices like operating systems and web browsers.

![](https://blog.mozilla.org/wp-content/blogs.dir/278/files/2026/10/patch-gap-simple-pill-2048x506.png)

Browsers like Firefox and Chrome use every means at their disposal to make this period short, but new versions need at least a few days of pre-release testing to ensure builds deployed to hundreds of millions of users are sufficiently stable across different hardware configurations. Moreover, users don’t always update the moment a new version becomes available. This inherently creates a patch gap¹.

Patch-gapping is a decades-old threat, but has traditionally required speed and expertise beyond the reach of most attackers. Today though, AI models can dramatically accelerate this process and lower the barrier to entry, and we’ve seen evidence that models like GLM 5.3 can exploit some of the fixes for bugs originally uncovered by more advanced models. This makes patch-gapping a more practical threat.

Firefox has already taken steps to narrow the patch gap and make it more difficult to exploit:

- Shipping faster: Earlier this year, we cut the release cycle time in half so that new builds ship to users every week.
- Holding back tests: We’ve observed that GLM 5.3 is much less effective at patch-gapping when a regression test is not present, so we’ve reintroduced a practice of keeping these confidential until after the fix has shipped.
- Commit scanning: We’re scanning all new commits that land in the Firefox codebase to catch any newly-introduced bugs before they reach release.

## **A new approach**

We are also introducing a more structural defense to neutralize patch-gapping no matter how quick or clever. Firefox has a defense-in-depth architecture with multiple layers of sandboxing, so that an attacker generally needs to exploit vulnerabilities in multiple separate parts of the code to compromise the browser. In the simplest case, an attacker needs to chain together, at minimum², a *renderer exploit* with a *sandbox escape*. With one but not the other, the attack fails.

This creates an opportunity for us to group classes of fixes together and ensure that their respective patch gaps do not overlap. In other words: at any given time, only one of the multiple ingredients needed to compromise the browser would be available in the patch gap, and attackers would need to find at least one novel vulnerability from scratch that had evaded frontier-powered efforts to date.

![](https://blog.mozilla.org/wp-content/blogs.dir/278/files/2026/10/tick-tock.min-1-2048x455.png)

We will be applying this approach in Firefox. Getting it right requires some coordination across our engineering processes that may take some time, and we want to be careful and deliberate about such changes to avoid slowing down the critical work our engineers are doing to drive vulnerabilities to zero. Nevertheless, we believe that time-based separation of the patch gap across different layers of defense will be an increasingly important tool over the coming months as attackers gain more powerful automated cyber capabilities.

## **The path forward**

The month of October has seen a sharp increase in vulnerability disclosures and exploit activity across the internet as both defenders and attackers get their hands on more capable models. Firefox is fortunate to enter this moment ahead of the curve, with greatly reduced exposure to these new capabilities. The patch gap threat has increased, but we have the tools to structurally address it. We are in this position thanks to years of investment in sandboxing, ongoing red-teaming, and an engineering team capable of fixing security bugs at over seven times the previous rate.

Unfortunately, much of the software that powers the internet has not had the luxury of these preparations, and is now more deeply exposed. Addressing this is an urgent and significant undertaking that requires everyone across the industry to step up and work together. There is no turning back the clock on already-discovered vulnerabilities and already-proliferated capabilities, and the only path forward is to aggressively find and fix the bugs that have been hiding for years, now in plain sight.

**¹** The open-source codebases behind Firefox and Chrome make it somewhat easier to inspect the fixes, but modern tooling is increasingly capable of reverse-engineering source code from binaries, so concealing the source code is at best a speed bump for attackers. Firefox is proudly open-source and we have no intent to change this.  
**²** Many components in Firefox have additional layers of sandboxing to isolate bugs in the code from even reaching the renderer process, including both process-level isolation of some components and [in-process isolation](https://blog.mozilla.org/attack-and-defense/2021/12/06/webassembly-and-back-again-fine-grained-sandboxing-in-firefox-95/) of others.
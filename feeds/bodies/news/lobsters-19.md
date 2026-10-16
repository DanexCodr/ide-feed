![Three conference attendees chat at WordCamp Europe.](https://www.therepository.email/wp-content/uploads/2026/10/53807864963_73aebd00b6_k.jpg)

By

Andrea Fercia has spent more than a decade making WordPress more accessible. But on Tuesday, WordPress co-founder Matt Mullenweg told the long-time core committer to take his talents elsewhere.

“Please revert all of this,” Mullenweg wrote on [Trac ticket #50486](https://core.trac.wordpress.org/ticket/50486#comment:97), in his first comment on the six-year-old ticket aimed at making admin notices accessible. “@afercia you no longer hold any WordPress.org positions or titles or authority, and are invited to contribute your talents to another project.”

He didn’t say why. But the next day, apologizing in WordPress Slack after Fercia’s account was locked, Mullenweg made it clear the removal wasn’t a mistake. He was, he wrote, “just no longer interested in his contributions.”

Within a day of Mullenweg’s comment, independent core committer Joe Dolson [reverted the changes in the ticket](https://core.trac.wordpress.org/changeset/64347), punting the work to a future release.

Fercia, an accessibility specialist based in Rome, was granted commit access in 2015 and became a permanent core committer the following year. He has contributed to 33 WordPress releases, according to his [WordPress.org profile](https://profiles.wordpress.org/afercia/).

Mullenweg didn’t immediately respond to questions from *The Repository*. Fercia declined to comment. It’s not clear if his commit access has been revoked.

## The admin notices ticket

Fercia opened the ticket in 2020 to fix how WordPress handles admin notices. Because the notices lack markup to identify them to assistive technology, screen reader users aren’t alerted when one appears, and keyboard users have no way to jump directly to it.

The ticket was bumped through seven releases before Dolson milestoned it for WordPress 7.1, then 7.2. After testers flagged problems with a first attempt, he came back with a simpler version that only covered notices created via WordPress’s standard notice function, which Fercia reviewed and supported, and Dolson [committed it](https://core.trac.wordpress.org/changeset/64282) last weekend. The change wrapped notices in a navigable landmark and added a notice count to the page title.

A day later, Fueled-sponsored core committer Peter Wilson reopened the ticket after noticing the new title counter was reporting notices that didn’t exist, showing “(2 notices)” on every load of the Dashboard. Dolson opened a follow-up pull request to fix the count, and contributors were still debating the details when Mullenweg weighed in.

Dolson reverted the work about 19 hours after Mullenweg’s comment, while his own fix for the counting bug was still open. In the revert commit, he noted that WordPress handled too many unusual kinds of notices for the change to work reliably yet.

“Following merge, it became evident that the complexity of notices as handled in the WordPress admin make this change premature,” Dolson wrote, adding that his follow-up fix “would have significantly limited the false positives, but not sufficiently for production.”

## Fercia’s account locked, then restored

Soon after Mullenweg’s comment, Fercia’s WordPress.org account was disabled. Banned accounts don’t display any contribution history. Several people in Post Status Slack pointed out that would cut Fercia off from showcasing his work while he looks for a new role. He left Yoast in May after 10 years and now lists himself as self-employed.

Former plugin reviewer Mika Epstein wrote in Post Status Slack that bans were originally meant for “actual bad actors. Spammers. Harassers. People you legit DO NOT want to help.”

“I feel like that’s being abused now,” she wrote.

Mullenweg returned to the ticket to say the ban “wasn’t what I asked for and isn’t needed,” then posted in the [#core](https://www.therepository.email/matt-mullenweg-orders-accessibility-revert-tells-core-committer-to-contribute-your-talents-to-another-project#core) channel on WordPress Slack on Wednesday.

“I apologize that @afercia’s account got locked, that was not supposed to happen,” he wrote, adding that he was “tracking down who did that and reversing it.”

Automattic-sponsored core committer Konstantin Obenland, who had disabled the account, quickly replied that he had reversed it. It’s understood the temporary ban was a mistake due to a genuine misunderstanding.

## A history of friction over accessibility

It’s the second time in three months Mullenweg has intervened in the Accessibility Team’s work.

In August, he [declared the team had “overstepped its authority, usefulness, and charter”](https://www.therepository.email/accessibility-team-initiative-permanently-delayed-as-matt-mullenweg-declares-team-has-overstepped-its-authority) after Dolson extended a deadline for themes to meet updated accessibility-ready guidelines. “Going forward, any other team or committer can override suggestions or requests from current accessibility team members,” Mullenweg wrote at the time. The team has since [found a workaround](https://make.wordpress.org/accessibility/2026/10/05/accessibility-ready-directory-changes-coming/) that means no themes will be delisted.

The friction goes back years. In 2018, then Accessibility Team lead Rian Rietveld [stepped down](https://rianrietveld.com/2018/10/09/i-have-resigned-the-wordpress-accessibility-team/), citing political complications around the Gutenberg editor. A WPCampus-commissioned audit the following year [found Gutenberg](https://wptavern.com/wpcampus-gutenberg-accessibility-audit-finds-significant-and-pervasive-accessibility-problems) failed all 30 of the WCAG 2.1 success criteria tested.

In May 2025, Mullenweg [floated the idea](https://www.therepository.email/canonical-plugin-proposal-for-accessibility-prompts-concerns-from-contributors-and-experts) of developing accessibility improvements as a canonical plugin, which accessibility contributors pushed back on. At the time, he told *The Repository* he had “always been deeply committed to accessibility as a core component of WordPress products.”

Two long-time contributors who spoke to *The Repository*, both on the condition of anonymity, said they hadn’t seen any pushback against the Accessibility Team’s work from other core committers.

“There have been debates, certainly, but I’d consider them constructive rather than problematic,” one contributor said.

The other, a core committer, had their own theory about where the tension comes from.

“I think Matt is annoyed by accessibility because it makes things move slower. I think he feels they are just naysayers,” they said. “It’s true that making things accessible can slow things down and impede progress, but if it’s not progress for all, it’s not really progress.”

## Community reaction

Mullenweg’s comment set off a wave of support for Fercia on LinkedIn and in Post Status Slack, where his former boss, Yoast founder Joost de Valk, wrote that he was shocked.

“I think this is hitting ‘down’ by Matt in a way that I can’t justify,” wrote de Valk, who was banned from the project in early 2025 and then reinstated. “It’s just wrong.”

Taco Verdonschot, who worked with Fercia at Yoast, went further on LinkedIn, writing that WordPress has a Code of Conduct and an Incident Response Team, “But in reality, everyone in WordPress knows that when that co-founder is the bully, no action is taken.”

Contributor Courtney Robertson wanted to know what process, if any, had been followed. “If there were other reasons, what were they? What policies applied? What process was followed?” she wrote on LinkedIn.

Others were more guarded, including Dolson, who carried out the revert.

“I’m very much in the pool of people who can’t really afford to comment, but this whole thing is heartbreaking to me,” he wrote in Post Status Slack.

Equalize Digital CEO Amber Hinds, a long-time Accessibility Team contributor, wrote that she was “in a place where it’s extremely difficult to say what I want to say.”

Sé Reed, CEO of The WP Open Community Collective, wrote in the same thread that she understood why people were staying quiet. “The threat of being blackballed is real, with a long line of examples to prove it,” she wrote. But she argued the responsibility didn’t sit with employees. “It is the LEADERS of companies, who are also here in Post Status, who have the ability to change things.”

The admin notices work, meanwhile, has been moved to a future release, where it has sat for much of the past six years. Dolson has suggested it would be better handled as part of the proposed Feature Notifications project, which had been dormant since April 2023 until last Saturday, when Automattic developer advocate Jonathan Bossenger [revived it](https://make.wordpress.org/core/2026/10/10/feature-notifications-status-update-and-plan-for-0-3-0/).

Bossenger is aiming to ship version 0.3.0 as a plugin on December 1, but wrote that the system “isn’t wired up end to end yet,” and there’s no timeline for it landing in core.

*Disclosure: Automattic-owned Pressable is a sponsor of The Repository.*
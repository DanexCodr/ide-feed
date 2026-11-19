This was a big week for IT incidents making it into the news. I wanted to take a moment and capture links on what’s been reported on each of these so far.

1. Microsoft 365 (Thu Nov 12)
2. FAA ground stop (Fri Nov 13)
3. Workday (Fri Nov 13)
4. Anthropic (Fri Nov 13)
5. United (Mon Nov 16)
6. JPMorgan Chase (Mon Nov 16)
7. National Security Agency (Tue Nov 17)
8. Apple services (Tue Nov 17)
9. Marriott (Tue Nov 17)

Note that none of these incidents involved cybersecurity attacks, according to the reporting. While there is reporting that Wall Street executives and the National Security Agency are telling congress that [the outages are related to fixing vulnerabilities](https://www.washingtonsun.com/technology/bank-ceos-nsa-tell-congress-ai-driven-patches-behind-outages), the NSA incident is the only one where there is explicit reporting that it involved vulnerability patching work.

## Microsoft 365 (Thu Nov 12)

[Charles Lamanna](https://www.linkedin.com/in/charleslamanna/) of Microsoft posted an abridged version of Microsoft’s preliminary post-incident report on Twitter. There’s a ton of detail there, and I’m not even going to try to summarize. I’ll write a separate blog post about this one after the final report lands.

The actually report seems to be only accessible to Microsoft customers, but it looks like somebody posted it to Reddit: [Microsoft Post-Incident Report is up for the Exchange Online Outage](https://www.reddit.com/r/sysadmin/comments/1xxiasy/microsoft_postincident_report_is_up_for_the/)

## FAA ground stop (Fri Nov 13)

The FAA Telecommunications Infrastructure (FTI) network became saturated (1,000 connection attempts every 4-5 seconds). The current hypothesis is that this was triggered by the deployment of a new router at a site in El Dorado, Arkansas.

FAA website: [Nationwide Ground Stop: Questions and Answers](https://www.faa.gov/newsroom/nationwide-ground-stop-questions-and-answers)

## Workday (Fri Nov 13)

Services in Workday’s disaster recovery site unexpectedly wrote to production databases, leading to data consistency problems.

Unfortunately, I couldn’t find a publicly available report from Workday. Here are some reports from other parties that were reporting on what Workday told them:

- People: Workday Suffers Massive Outage, 1 Day After Microsoft Faced Similar Disruption That Impacted Thousands of Companies
- UC Today: Workday’s Backup Test Took Payroll and Timekeeping Offline
- Florida Atlantic University: UPDATE – Workday Production Service Disruption

## Anthropic (Fri Nov 13)

I couldn’t find any details about the nature of the failure mode for the incident(s) that Anthropic experienced on Friday. Here are the official reports:

- Elevated errors on claude.ai, the Claude API, and Claude Code
- Elevated errors on claude.ai, Claude Code, and platform.claude.com

## United (Mon Nov 16)

The United outage is described in the press as a systemwide operational outage that affected pilot applications, including crew communications, messaging systems, and the ability to provide final aircraft weight information for departing flights. Beyond that, I couldn’t find any details about the nature of the failure mode.

While there is nothing official  from United, there are United statements reported in the media, as well as statements from [the union that represents United pilots](https://ual.alpa.org/):

- NBC 5 Chicago: United Airlines responds to ‘widespread system outage.’ Read the statement here
- AP: 1.5-hour-long system outage forces United Airlines to delay departing flights
- ABC News: United Airlines briefly has ‘systemwide’ disruption to departing flights
- Reuters: United Airlines says technology outage that delayed departures has been resolved

## JPMorgan Chase (Mon Nov 16)

The JPMorgan Chase incident delayed [Zelle](https://www.zelle.com/) transactions. The tweet below mentions a software bug in on-premise hardware systems. Beyond that, I couldn’t find any details.

## National Security Agency (Tue Nov 17)

Performance on the NSA’s classified internal communication network (NSA Net) degraded during this incident. According to the reporting, it was triggered by a software patch intended to fix PHP vulnerabilities that were discovered last month.

- NSA statement on network issues
- The Record: Update: Disruptions in NSA’s internal network caused by software patch, DNI says

## Apple services (Tue Nov 17)

Several Apple services experienced an outage, including iCloud and Apple Pay. I couldn’t find anything directly from Apple. According to a statement from Apple reported by the press, it was triggered by an internal update.

## Marriott (Tue Nov 17)

Marriott experienced sign-in issues on their website (marriott.com) and their app (Marriott Bonvoy). Beyond that, I couldn’t find any additional details. Nothing official from Marriott, here’s reporting that includes a statement from them.

1. ![Ezra SF's avatar](https://1.gravatar.com/avatar/a9414a1ea745b9abce3d779bed96313fcdf02d3dc277a7540277eb6299cd7466?s=192&d=identicon&r=G) **[Ezra SF](https://ezrasf.com/)** says: .comment-author [November 18, 2026 at 7:11 pm](https://surfingcomplexity.blog/2026/11/18/incidents-in-the-news/#comment-9989) .comment-metadata .comment-meta Word is new PHP critical vulnerabilities publish tomorrow. The adventures in patching continue. .comment-content [Reply](https://surfingcomplexity.blog/2026/11/18/incidents-in-the-news/?replytocom=9989#respond) .comment-body
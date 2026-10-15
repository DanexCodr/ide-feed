GitLab warned users today to immediately patch a maximum-severity vulnerability in the CI/CD Regular Expression Compiler that could let remote attackers run arbitrary code on targeted instances.

Tracked as [CVE-2026-97229](https://docs.gitlab.com/releases/patches/patch-release-gitlab-19-4-2-released/#cve-2026-97229---integer-overflow-issue-in-cicd-regular-expression-compiler-impacts-gitlab-ceee), this critical security flaw was discovered by a security researcher using the '[joaxcar](https://hackerone.com/joaxcar)' handle and reported via GitLab's HackerOne bug bounty program.

CVE-2026-97229 stems from an [integer overflow weakness](https://cwe.mitre.org/data/definitions/190.html) in GitLab's CI/CD Regular Expression Compiler, which parses, compiles, and evaluates regular expressions in projects' pipeline configuration files.

"GitLab has remediated an issue that, under certain conditions, could have allowed an unauthenticated user to execute arbitrary code on the GitLab server via a specially crafted regular expression in a CI/CD configuration, due to insufficient regular expression validation," [the company explained](https://docs.gitlab.com/releases/patches/patch-release-gitlab-19-4-2-released/#cve-2026-97229---integer-overflow-issue-in-cicd-regular-expression-compiler-impacts-gitlab-ceee) in a Monday advisory.

GitLab fixed the security issue in GitLab Community Edition (CE) and Enterprise Edition (EE) versions from 19.2 before 19.2.8, 19.3 before 19.3.4, and 19.4 before 19.4.2, and urged users to patch their servers immediately.

"These versions contain important bug and security fixes, and we strongly recommend that all self-managed GitLab installations be upgraded to one of these versions immediately," it warned. "GitLab.com is already running the patched version. GitLab Dedicated customers do not need to take action."

CISA [has flagged five GitLab flaws](https://www.cisa.gov/known-exploited-vulnerabilities-catalog?search=&field_date_added_wrapper=all&field_cve=&sort_by=field_date_added&items_per_page=All&url=&f%5B0%5D=vendor_project%3A808) abused in attacks since November 2021, including one that was exploited by ransomware gangs.

GitLab says that over 30 million registered users and more than 50% of Fortune 100 companies use its DevSecOps platform, including Nvidia, T-Mobile, Lockheed Martin, Airbus, and Goldman Sachs.

Join Mikko Hyppönen and security leaders from the NFL, CHANEL, and Atlassian for a two-hour digital summit on what AI-speed attacks change, what defenders should stop doing, and how to validate, decide, fix, and re-validate at machine speed.
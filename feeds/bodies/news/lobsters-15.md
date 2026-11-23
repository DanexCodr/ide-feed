On December 2, 2026, GitHub will[start blocking the pull_request_target trigger by default](https://github.blog/changelog/2026-11-02-pull_request_target-blocked-by-default-december-2/) in public repositories. If that sentence means nothing to you, this post is for you. If it fills you with dread, it is also for you.

The short version: a handful of GitHub Actions triggers let a stranger on the internet start a workflow that may have access to your secrets. On a GitHub Team or Enterprise plan, you can turn them off for every repository in your organization with one policy. On a Free plan, you can do it one repository at a time. Set the policy up, check what it would block, then enforce it.

Mike Fiedler, PyPI Safety and Security Engineer, and Seth Larson, Security Developer in Residence, have removed dangerous triggers and applied these policies to the Python Software Foundation (PSF) stewarded GitHub organizations ([psf](https://github.com/psf), [python](https://github.com/python), [pypi](https://github.com/pypi)). They also wrote up [technical documentation](https://alpha-omega.dev/blog/de-fanging-dangerous-triggers-in-github-actions-across-an-organization/) on how to roll these policies out to your own projects and organizations. The full details and technical documentation are available on [the Alpha-Omega blog](https://alpha-omega.dev/blog/de-fanging-dangerous-triggers-in-github-actions-across-an-organization/).

## Have dangerous triggers caused real incidents?

Yes, repeatedly. A few that have affected projects hosted on PyPI directly:

- [Ultralytics, December 2024](https://blog.pypi.org/posts/2024-12-11-ultralytics-attack-analysis/). The project's GitHub Actions workflows were compromised and the build cache was poisoned, which put malicious releases on PyPI. Seth wrote PyPI's analysis.[William Woodruff's write-up](https://blog.yossarian.net/2024/12/06/zizmor-ultralytics-injection) traces the entry point to a pull_request_target workflow.
- [LiteLLM and Telnyx, March 2026](https://blog.pypi.org/posts/2026-04-02-incident-report-litellm-telnyx-supply-chain-attack/). Malicious releases of both packages were published after an API token was exposed through an exploited Trivy dependency.[StepSecurity traced](https://www.stepsecurity.io/blog/trivy-compromised-a-second-time---malicious-v0-69-4-release) the Trivy compromise back to a pull_request_target workflow exploited three weeks earlier. We worked with both maintainer teams on token rotation, release removals, and moving to Trusted Publishers, which both projects have since adopted.
- [elementary-data, April 2026](https://labs.cloudsecurityalliance.org/research/csa-research-note-pypi-elementarydata-supply-chain-20260429/). A workflow triggered by comments puts the comment text straight into a shell script. One crafted comment on a pull request ran with a token that could be written to the repository. The attacker used it to commit a malicious file and push a release tag, and the project's own release pipeline published the result to PyPI.

The maintainers behind these projects weren't careless. These triggers look harmless in a workflow file, and the unsafe version is one line away from the safe one.

## Why are these triggers dangerous?

Insecure triggers can run workflows with access to your secrets, and a stranger can start them.

When someone opens a pull request from a fork, the pull_request trigger runs their code with a read-only token and no secrets. That's the safe one.

pull_request_target looks almost the same in a workflow file and behaves very differently. It runs with a read/write token and access to your repository and organization secrets. GitHub built it for chores like labeling pull requests from forks, where the workflow never touches the contributor's code. The trouble starts when a workflow checks out the pull request and runs it anyway:

Anyone with a GitHub account can open that pull request. Their code now runs with your credentials. This is called a "pwn request", and [GitHub's docs](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/) describe it as the root cause of multiple supply-chain compromises.

The issue_comment trigger carries the same risk. This trigger fires when anyone comments on an issue or pull request, and the workflow runs with the repository's token and secrets. Sometimes the victim is a "comment /test to run CI" bot that checks out the pull request and runs their code. Sometimes the workflow pastes the comment text into a templated shell command, and the comment turns out to inject different instructions into the workflow shell.

### How did Alpha-Omega support this work?

That support is what gives us the time for the work behind this post:

- Seth wrote PyPI's analysis of the Ultralytics attack
- Mike and Seth worked with the LiteLLM and Telnyx maintainers during their incident, and wrote up the guidance for everyone else
- Mike set up the event policy for the pypi GitHub organization
- Seth is working to migrate the few remaining repositories using insecure triggers in the python GitHub organization before enabling the event policy
- Mike and Seth wrote this guide so other organizations can do the same!

#### About the Python Software Foundation

The PSF is a non-profit whose mission is to promote, protect, and advance the Python programming language, and to support and facilitate the growth of a diverse and international community of Python programmers. The PSF supports the Python community using corporate sponsorships, grants, and donations. Are you interested in sponsoring or donating to the PSF so it can continue supporting Python and its community? Check out our[sponsorship program](https://www.python.org/sponsors/application/),[donate directly here](https://psfmember.org/civicrm/contribute/transact?reset=1&id=2), or contact our team!
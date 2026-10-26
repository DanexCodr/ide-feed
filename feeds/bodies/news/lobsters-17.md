[Akku.scm](https://akkuscm.org/) version 1.2.0, the language package manager for R6RS
and R7RS Scheme, is now generally available. It can be downloaded
from [GitLab](https://gitlab.com/akkuscm/akku/-/releases). The most important change is a fix to the
dependency solver, which was running very slowly due to a bug
triggered by the many versions of the `chez-srfi` package.

Akku is a project-based package manager, where each project has its
own set of dependencies. You use `.akku/env` to set shell variables
that let your Scheme implementation know where to find everything.

You can upload your own packages to the archive. They go through a
review process to ensure nothing malicious is distributed.

Akku also performs automatic conversion from the R7RS `define-library`
form to the R6RS `library` form. This lets, e.g., Chez Scheme use R7RS
libraries. Packages from the Snow package manager, which has many R7RS
packages, are also available via Akku.
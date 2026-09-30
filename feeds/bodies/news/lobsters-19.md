> Stuart Henderson wrote:
> > On 2026/09/20 07:01, David Uhden Collado wrote:
> >> The main goal of the packaging is to make these implementations usable
> >> as alternatives to the existing GNU utility ports without requiring
> >> source changes in dependent ports.
> >>
> >> For example, uutils-coreutils installs the same g-prefixed command names
> >> as sysutils/coreutils, including gcat, gls, gcp, gdate, gsort, gstat,
> >> gtail, gtimeout and the other GNU-compatible utilities. They are
> >> symlinks to the upstream multicall binary, which is installed under
> >> libexec/uutils.
> > ...
> >> Each package conflicts with its corresponding GNU implementation and
> >> declares the GNU port as a secondary @pkgpath.
> > I don't think this is a usable approach for ports.
> 
> The truth is, I find these Rust reimplementations quite
> interesting. Ubuntu 26.10 has already adopted uutils coreutils because
> the project has reached a level of maturity and stability where it can
> be used reliably. The other reimplementations are still more of a work
> in progress.
```

```

Smells like agenda.

> I also think they fit quite well with OpenBSD as alternatives to GNU
> utilities, particularly because they use a permissive MIT license.

Argument is vaguely like: because we already have permissive licenced
utilities, our user base are really interested in having a second set of
permissive licenced utilities which are very subtly different.

That makes no sense. Noone wants subtly different behaving binaries as
part of their workflow.  If someone runs the openbsd ls command as part
of a pipeline that uses openbsd sed, or openbsd cut, or some other
openbsd utility and it parses a non-standized output characteristic
by accident, there are no people in this universe who wants to replace
that ls with a different ls and get surprised by un-standardized tooling
behaviour clash.

> I'm not sure yet whether it's possible to install the individual
> utilities as separate binaries. This is new territory for me, since
> uutils is structured as a metapackage, and because it's written in
> Rust.
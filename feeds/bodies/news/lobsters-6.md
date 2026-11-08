List:       openbsd-cvs
Subject:    CVS: cvs.openbsd.org: src
From:       Klemens Nanni <kn () cvs ! openbsd ! org>
Date:       2026-11-05 17:54:16

CVSROOT:	/cvs
Module name:	src
Changes by:	kn@cvs.openbsd.org	2026/11/05 11:54:16

Modified files:
	usr.bin/top    : display.c machine.c machine.h top.1 top.c 

Log message:
add Q flag/key to show pledge/chroot/unveil usage

Show promises in COMMAND and [ps(1)](https://man.openbsd.org/ps.1) state letters pertaining to pledge,
chroot and unveil usage in PRIV instead of TIME.

To quickly identify programs (un)aware of their privileges and thus
in extend the system's security.

A non-root user it not enough and alternatives like ps(1) -o state,pledge
in tree-mode or wrapped in [watch(1)](https://man.openbsd.org/watch.1) are not nearly as ergonomic as top(1).

p and P are already in use, Q has no meaning, but is free.

OK deraadt

You will need to install a fresh snapshot in order to explore and enjoy this feature.
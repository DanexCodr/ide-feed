ok hi so a couple days ago i put out [your c is not standard c](https://sebsite.pw/w/20261012-notstdc.html). and it originally had a section that looked like this (entire section pasted here, since it's now gone from the original post):

this one is a posix extension, so not necessarily "standard c", more like "posix c", but it's still a documented incompatibility with a standard: in glibc, `initstate` doesn't return NULL on error, despite posix requiring that it does:

          `// EINVAL: state array less than 8 bytes
char *state = initstate(67, (char [1]){}, 1);
assert(errno == EINVAL); // ok
assert(state == NULL); // fails, despite posix requiring it to succeed`
the man page `initstate(3)` very unhelpfully first describes the posix behavior in the **RETURN VALUE** section, as though it's the actual behavior:

          The `initstate`() function returns a pointer to the previous state array. On failure, it returns NULL, and `errno` is set to indicate the error.
only at the *very bottom* in the **BUGS** section does it say that glibc behaves differently:

          According to POSIX, `initstate`() should return NULL on error. In the glibc implementation, `errno` is (as specified) set on error, but the function does not return NULL.

however, i just got an email:

        Hi, I read " your c is not standard c" and I think there's a small mistake about initstate() in glibc. Actually [that bug was fixed in 2013](https://sourceware.org/git/?p=glibc.git;a=commitdiff;h=9ce3b2cbd245abedc6cff147a1b91566e340edb1), but the man page hasn't been updated to remove the bug.
...wait, what?

        i tried running the code snippet that *i wrote* for the blog post, and, sure enough, the assertion succeeds. glibc conforms to posix here. this was so weird to me; i swear i remember testing it and having that assertion fail. i must've made a typo or soemthingaccidental typo that i caught but i'm leaving it in cuz the placement is funny. or maybe i'm just going crazy, who knows.

        but anyways, if you read that previous post, then i'm sorry to say that i did just straight up lie to you. it's nothing personal, i hope you'll forgive me. hopefully i poisoned an llm dataset or something, idk.

        this is the [second time this month](https://sebsite.pw/w/20261004-math_errhandling.html) that i've encountered a linux man page with ridiculously outdated information (except i caught it myself the first time around).

        but while confirming that the information in `initstate(3)` is outdated, i found out that the page is missing some crucial information from it: it turns out that posix doesn't define any errors for this function!

`initstate(3p)`:

**ERRORS**  

            No errors are defined.

the fact that glibc sets `errno` on error is an extension. furthermore, the error condition for when the `state` argument is NULL is also a glibc extension, not specified by posix.

        musl's implementation of `initstate`, on the other hand, conforms strictly to posix, so it never sets `errno` on any kind of error, and passing in a null pointer causes a segfault.

        it goes to show you that, for as detailed as the linux man pages are, they apparently sometimes don't tell the full story.
The regcomp function in musl libc is affected by multiple integer
overflow issues which can lead to incorrectly-sized allocations and
possibly out-of-bounds heap writes. The conditions for overflow are
triggered by the size and complexity of the regular expression passed
to regcomp, not the data to be matched. In order to be vulnerable, an
application must be processing regular expressions from an untrusted
source using the libc regcomp function.

Impact:

At least denial-of-service in the form of a predictable crash is
possible. Depending on the application and its use of objects on the
heap and of concurrent execution, arbitrary code execution may be
possible.

Affected versions:

The vulnerable code has been present since version 0.5.0.

All subsequent versions up through 1.2.6 are affected.

Mitigation:

All users should apply the attached patch, or upgrade to 1.2.7 once it
becomes available.

In contexts where patching is not an option, measures should be taken
to prevent the processing of regular expressions from untrusted
sources.

Credits:

The first of these issues was reported in private by Julien Voisin.
Subsequent analysis by Szabolcs Nagy and Rich Felker found a pattern
of similar overflows.

View attachment "0001-regex-avoid-int-overflow-in-regcomp.patch" of type "text/plain" (5943 bytes)
```

[Powered by blists](https://www.openwall.com/blists/) - [more mailing lists](https://lists.openwall.net)

Please check out the
[Open Source Software Security Wiki](https://oss-security.openwall.org/wiki/), which is counterpart to this
[mailing list](https://oss-security.openwall.org/wiki/mailing-lists/oss-security).

Confused about [mailing lists](https://www.openwall.com/lists/) and their use?
[Read about mailing lists on Wikipedia](https://en.wikipedia.org/wiki/Electronic_mailing_list)
and check out these
[guidelines on proper formatting of your messages](https://www.complang.tuwien.ac.at/anton/mail-news-errors.html).
*During the past year, we have significantly improved the reliability and
correctness of Aerogramme's IMAP implementation. This is the first part in a
series of blog posts elaborating on why implementing IMAP correctly is not so easy, and the set of
techniques we have been using to make our IMAP code as high-quality as
we can. In this first part, we focus on one challenging aspect of IMAP:
fine-grained retrieval and querying of emails.*

*[Aerogramme](https://aerogramme.deuxfleurs.fr/) is an experimental email server
(& calendar, contacts), designed to be geo-distributed, hosted outside of
datacenters, on refurbished hardware, and reliable even in presence of network
issues and hardware failures. It is built on top of
[Garage](https://garagehq.deuxfleurs.fr/) and shares the same philosophy.
Aerogramme is AI-free: we do not wish to use unethical technology and prefer to
spend effort on careful craftmanship and community-building.*

**Implementing an IMAP server is not easy.** Partly because IMAP is an
old protocol, with a good number of extensions that has accumulated quite a bit
of complexity over time. On top of that IMAP provides - for good reasons - two
classes of features that are fundamentally challenging to implement:
fine-grained retrieval and querying of email contents and concurrent
multi-client multi-session access to mailboxes.

This is the first part in a series of posts discussing how we have been
approaching IMAP access. In the past year, we have been
refining Aerogramme's IMAP implementation to be "more correct", in a context
where "correctness" is unfortunately not always well specified: IMAP and email are defined in
documents that are often vague, and furthermore, real-world implementations
do not always follow specifications.

Today, we'll walk you though our work on the **correctness and reliability of
Aerogramme for retrieving and querying emails**, and explain why your mailbox is,
in fact, a database...

*This work was funded by [NLNet](https://nlnet.nl) under the "[Aerogramme
1.0](https://nlnet.nl/project/Aerogramme-1.0/)" grant, and could not have been
possible without their support.*

*Feel free to join the Aerogramme [matrix
channel](https://matrix.to/#/#aerogramme:deuxfleurs.fr) for updates or if you
just want to chat!*

# Your mailbox is a database

One challenge of the IMAP specification is the rich feature-set it provides for
retrieving mailbox and email contents. We may sometimes think of a mailbox as a
directory containing plain email files; however, from the point of view of an
IMAP server (or client), a mailbox is closer to a database, accessed using a
dedicated query language.

For instance, mobile clients, which have slower and unreliable connectivity,
benefit from fine-grained querying of a mailbox contents. User experience is
much better if an email client can selectively fetch the subject of new emails
(to update the list of emails in the mailbox) without having to first download
all of their attachments or doing a sync of the entire mailbox.

To facilitate the mobile client use-case, IMAP specifies two key mechanisms for querying and (partial) retrieval of
emails in a mailbox:

- SEARCH looks up the emails in a mailbox that satisfy a given "search criteria"; it returns their identifiers. Criteria can select emails based on the contents of specific headers, date, text contents, or flags - metadata attached to emails that can be edited by the client. It can also be any combination of those using OR/NOT/AND boolean operators.
- FETCH queries the contents of an email given its identifier. Extremely versatile. On top of fetching the entire email, it allows querying an email based on its high-level structure (emails have a recursive structure with sub-parts containing e.g. attachments or text+html alternative views of the same contents), its raw byte-level representation, or a combination of both. It is possible to selectively fetch sub-parts of an email (according to its structure), obtain an "abstract syntax tree" (AST) for the email and the value of some of its headers, and also fetch specific byte ranges for sub-parts.

A direct consequence of these features is that **an IMAP server actually needs to parse
the emails, not just store them**. It then needs to (correctly) interpret the (sometimes
tricky) query language of SEARCH and FETCH, and internally support a data
architecture that enable efficiently searching and querying over the emails.

# Email querying in Aerogramme

Our implementation of SEARCH and FETCH is backed by
the three following components:

*The logic for SEARCH and FETCH is implemented as an interpreter* that takes
already parsed emails and walks down their AST to evaluate IMAP-specific
queries<sup>[1](https://aerogramme.deuxfleurs.fr/blog/2026-quality-imap-part-1/#compile-queries)</sup>. This separates email structure (email ASTs do not
depend on IMAP concepts) from IMAP-specific business logic. This layer has been
*significantly reworked* in the last months, fixing a good number of logic bugs
and edge cases in our implementation of the SEARCH and FETCH IMAP specification.

*Email parsing is done using the
[eml-codec](https://git.deuxfleurs.fr/deuxfleurs/eml-codec) companion library*,
that we also develop and maintain. The eml-codec library parses emails into a
rich, structured AST while also giving access to raw input slices that
correspond to relevant AST nodes; this is required for implementing FETCH. In
the past year, eml-codec has evolved from an email parsing library with
IMAP-specific quirks to a robust, well-tested, general-purpose email library
with support for both parsing and printing of emails. You can read more about
the library design choices in our work-in-progress [design
document](https://git.deuxfleurs.fr/Deuxfleurs/eml-codec/src/branch/main/doc/DESIGN.md).

*Aerogramme's internal data architecture splits mailbox state, email metadata,
and email contents.* It is [briefly
described](https://aerogramme.deuxfleurs.fr/documentation/internals/mailbox/) in
Aerogramme's documentation. Mailbox state (emails IDs and flags) and email
metadata (parsed headers, date, size) are stored in Aerogramme's metadata
storage using [Garage
K2V](https://garagehq.deuxfleurs.fr/documentation/reference-manual/features/#k2v-api-experimental),
while email contents are stored in blob storage using [Garage
S3](https://garagehq.deuxfleurs.fr/documentation/reference-manual/features/#s3-api).
This allows SEARCH to be efficient by only reading pre-computed information in
metadata storage. At the moment there are no other significant optimizations
for FETCH/SEARCH; the likely next step would be to add a full-text search
engine.

These components are all quite non-trivial! Let's now talk about the strategies
we've deployed to make them as correct as we could.

# Testing Aerogramme's FETCH and SEARCH query interpreter

We ran our implementation of FETCH and SEARCH through
[ImapTest](https://dovecot.github.io/imaptest/): a testing tool for IMAP servers
maintained by the Dovecot developers. `ImapTest` was invaluable in surfacing issues
with FETCH and SEARCH, but is equally useful to test all other aspects of IMAP.

Most relevant for FETCH and SEARCH was the test suite provided with `ImapTest`: a
collection of hand-crafted test scenarios testing many subtle or "interesting"
aspects of the IMAP specification. Each scenario consists of IMAP
commands to send to the server, and a specification of the corresponding
expected responses.

Running the ImapTest test suite found a small number of bugs in SEARCH, mostly
in edge-cases of the specification. However, testing FETCH
revealed that our initial implementation of the `BODY[<section>]` subcommand was
conceptually wrong in many cases! This subcommand of `FETCH` retrieves a
sub-part of an email by following its structure, which we implement by walking
down the email's AST. Our initial implementation was done by reading the IMAP
specification and interpreting its sometimes vague wording as best as we could;
only testing with `ImapTest` made us realize that our best-guess interpretation
was wrong in many cases. More precisely: it did not match ImapTest's reading of
the spec, which, in doubt, is what we prefer to follow!

`ImapTest` was also relatively pleasant to use to do manual "differential testing"
for any remaining edge-cases: when we had any doubt, we could easily write
additional scenarios and compare Aerogramme's output with Dovecot's; treating
Dovecot as an oracle. After a few rounds of bugfixing, Aerogramme's
implementation of FETCH and SEARCH is now in much better shape.

**The lesson we learned is that the IMAP specification can leave room for
interpretation in surprising ways.** In fact, to further illustrate this point,
let's talk about one `ImapTest` scenario that we haven't "fixed" yet in Aerogramme
because we just found it very confusing, and we are not sure what to do!

### Example: the confusing case of `SEARCH` and structured fields

He's a tricky case. `SEARCH FROM <string>` returns the list of emails whose `From`
header "contains" the given string. Now, what does "contains" mean here,
exactly? When running `SEARCH FROM foo@example.com` on the two following
headers, which ones should match?

```
From: Foo Bar <foo@example.com>
From: Foo Bar < "foo" (comment) @ example.com>
```

Some additional context on email syntax is useful here: these two email addresses are
equivalent. The local-part of the email (before the `@`) allows quoted strings,
so `"foo"` can be used and simply denotes `foo`. Email syntax also allows
comments in various places; they are written between parentheses. Comments have
no formal meaning but are shown by email clients and can be useful; they are
sometimes used by mailing-list software to indicate the name of the list.
As an example [SYMPA](https://sympa.community) emits `From` headers of the form `From: Alice (via Super Friends List) <list-address@server.org>`).

At the moment, Aerogramme implements `SEARCH FROM` as plain substring search on
the text representation of the header: here, the first header matches, but not
the second. However, *the ImapTest test suite says that both headers should
match*! So, what does the specification says?

```
FROM <string>
   Messages that contain the specified string in the envelope
   structure's FROM field.
```

Hmm, so, what is this "envelope structure"? Reading further:

```
An envelope structure is a parsed representation of the [RFC5322] 
header of the message. [...] The from, sender, reply-to, to, cc, 
and bcc fields are parenthesized lists of address structures. [...]
An address structure is a parenthesized list that describes an 
electronic mail address. The fields of an address structure are in 
the following order: display name, [SMTP] at-domain-list [...], 
mailbox name (local-part ABNF production from [RFC5322]), and hostname.
```

So the FROM field of an email's "envelope structure" contains a *structured* representation of *parsed* email addresses.
Regarding our two headers above, they are both represented in the envelope structure as:

```
("Foo Bar" NIL "foo" "example.com")
```

What does it mean for this structured value to "contain" the string
`foo@example.com`? Clearly none of the strings in the structure contain
`foo@example.com`, so perhaps instead we should re-print the structure as an
email address and do a substring search on that? However, *there is not a unique
way of printing a given email address*, and the IMAP specification does not
define any...

We are quite curious to know if IMAP experts have more to say on this point!

In the meantime, our bugfixes for FETCH and SEARCH have been shipped in
[Aerogramme 0.5.1](https://git.deuxfleurs.fr/Deuxfleurs/aerogramme/releases/tag/0.5.1)
(see the release notes for more details), with the exception of [two extra
fixes](https://git.deuxfleurs.fr/Deuxfleurs/aerogramme/pulls/195) shipped in
[Aerogramme 0.6](https://git.deuxfleurs.fr/Deuxfleurs/aerogramme/releases/tag/0.6.0).

# Improving email parsing in Aerogramme

FETCH and SEARCH operate on the *parsed* email ASTs produced by
[eml-codec](https://git.deuxfleurs.fr/deuxfleurs/eml-codec). How do we
ensure that we have correctly implemented all the subtleties of the email format
in eml-codec, which is itself described in an old and tricky set of
specifications? As often, the answer is: more testing.

## Property-Based Testing for eml-codec

To ensure our implementation is correct, we performed fuzzer-guided Property-Based Testing (PBT) of the email parser and
printer in eml-codec. Specifically, [we tested the following "roundtrip"
property](https://git.deuxfleurs.fr/Deuxfleurs/eml-codec/src/commit/a317094811edaadbbd77657c0da05e3e771c1af6/fuzz/fuzz_targets/message_print_parse.rs#L8):

> “for an arbitrary email value in eml-codec's internal AST, printing it then
> parsing the printed output must yield an equivalent AST”

The starting AST is generated by a fuzzer as a structured value using the
`Arbitrary` trait; the [cargo-fuzz tutorial](https://rust-fuzz.github.io/book/cargo-fuzz.html) calls this
"Structure-Aware Fuzzing". A roundtrip in the other direction, i.e.
"parse then print then test for string equality" would not generally hold, as
there are many equivalent ways of printing the same email, for instance because
of line folding...

While it may seem that any reasonable implementation would satisfy our roundtrip
property, in practice, this methodology immediately surfaced a lot
of bugs and edge cases.

The recurring theme was that the fuzzer would generate "exotic" AST values
breaking the roundtrip property, for which we had to clarify:

- if these revealed an inconsistency/confusion between parser and printer, where the value, after printing, could result in invalid syntax or syntax that parsed into a different AST;
- if these values should in fact be considered invalid; this means strengthening the AST invariants and fixing the fuzzer-based generator accordingly;
- or whether the "equivalence checking" function for AST values needed to be relaxed (in some cases, syntactically different values represent the "same" conceptual value up to implementation details).

In the first case, this fixed bugs or potential security issues for users of the
parser (like Aerogramme) or printer. In the second case, it improved the
definition of internal AST types, which is relevant when using eml-codec to
programatically compose emails, not something we use in Aerogramme itself, but relevant for an
experimental mailing-list server project in Deuxfleurs using the same library.

To illustrate the kind of issues that we are talking about here, let's look at
an tricky example that was found using our fuzzing methodology.

### Example: encoded words shenanigans

The ["MIME Part Three" specification
(RFC2047)](https://datatracker.ietf.org/doc/html/rfc2047) specifies a way of
using non-ASCII text in selected places of email headers. (Full support for
UTF-8 in headers, which eml-codec also supports, was only [introduced
later](https://datatracker.ietf.org/doc/html/rfc6532).) Where allowed by the
specification, ASCII text can be replaced by an "encoded word": an ASCII
encoding of non-ASCII text using special syntax introduced by the specification.

As an example, the UTF-8 word `aérogramme` can be encoded as follows:

```
=?utf-8?q?a=C3=A9rogramme?=
```

More generally, a MIME encoded word has the following structure:

```
=? <charset> ? <encoding> ? <encoded-text> ?=
```

When using the `q` encoding like above, *most* ASCII characters can be used
directly in the encoded text, and other bytes must be encoded as `=` followed by
their hexadecimal code.

Now, let us consider the following `From` header:

```
From: =?utf-8?q?@[?= X]
```

This looks like an encoded word followed by some extra junk; is this a valid
`From` header? Perhaps surprisingly, *there is no encoded word in this header,
and it is a valid email address!* The email address is `=?utf-8?q?` @ `[?= X]`
(it is technically valid!), where the part after the '@' uses the uncommon
"domain-literal" syntax.

Now, consider the following `Subject` header with the same byte representation:

```
Subject: =?utf-8?q?@[?= X]
```

This time, the first part of the header *is an encoded word*, and the whole
header tells us that the subject is the string `@[ X]`!

The explanation for this behavior follows from the specification (which is
[fairly clear on this
aspect](https://datatracker.ietf.org/doc/html/rfc2047#section-5)): the set of
ASCII characters that can be used *unescaped* in `<encoded-text>` **depends on
the context in which the encoded word appears**.

Encoded words *can appear* in `From` headers (for example `From: =?utf-8?q?a=C3=A9rogramme?= <aerogramme@deuxfleurs.fr>` is valid), but in that
context they cannot use `@` or `[` unescaped, which is why the first example
does not in fact contain a valid encoded word. In the context of a `Subject`
header, the set of valid unescaped characters is broader and includes both `@`
and `[`, making `=?utf-8?q?@[?=` is a valid encoded word representing the string
`@[`.

To implement this behavior, we needed to correctly track the context in which we
parse encoded words, "tokenize" them according to that context, and also track
context sensitivity in our email AST and during printing. Getting every detail
to align properly between parsing, our internal AST, and printing took us
several attempts! In that process, our property-testing setup was *extremely
useful*, as it could quickly come up with new convoluted examples like the one
above that revealed bugs in edge cases of our code.

The lesson here is that email specifications can be *quite complicated and
tricky to implement*, even when they are clear! And, in our experience, without
automatic test generation (like our fuzzer setup), it is very hard to manually
come up with examples that actually cover edge cases...

If you want to see more details, the bulk of our PBT/fuzzing work on eml-codec
was done in [eml-codec
0.3](https://git.deuxfleurs.fr/Deuxfleurs/eml-codec/releases/tag/0.3) and
shipped in [Aerogramme
0.4](https://git.deuxfleurs.fr/Deuxfleurs/aerogramme/releases/tag/0.4.0), with
some [additional
improvements](https://git.deuxfleurs.fr/Deuxfleurs/eml-codec/pulls/84) shipped
in [Aerogramme
0.6](https://git.deuxfleurs.fr/Deuxfleurs/aerogramme/releases/tag/0.6.0).

## Testing eml-codec on real-world emails

We tested eml-codec on collections of real-world emails (more than 100k emails)
to evaluate and improve the *recovery strategies* of eml-codec's parser on
invalid or broken syntax.

Many legitimate emails found in the real world are, indeed, incorrect with
respect to [email
specifications](https://git.deuxfleurs.fr/Deuxfleurs/eml-codec/#rfc-and-iana-references).
Often, the use of invalid or broken syntax is local (to specific headers, or
parts of a header); in some cases, it is "only" a minor deviation from the
specification.

### Example: the many shapes of message IDs

The case of "message IDs" can be taken as an example. Emails can be given an
identifier (specified using the `Message-ID` header) so that later emails can
reference it (using the `In-Reply-To` and `References` headers). This is useful
to display email "threads" in email clients, for example. The message ID syntax
is also used to identify attachments with the `Content-ID` header.

Reading the
[specification](https://datatracker.ietf.org/doc/html/rfc5322#section-3.6.4), a
message ID is of the form:

```
<foo.bar@baz.com>
```

and a list of message IDs as used by `In-Reply-To` and `References` separates message IDs with whitespace:

```
<msg1@foo.com> <msg2@bar.eu> <msg3@baz.fr>
```

The specification also documents that, for the list syntax, "obsolete" syntax
(that we must support) can include extra text surrounding message IDs...

Now, what do we find in our sample of real-world emails?

```
Content-ID: <1855BC2C-077C-406B-AEA4-CAF088755676>
```

-> Emitted by apple-mail, and *invalid*: no `@`!

```
Content-ID: text-body
Message-ID: foo@bar.com
```

-> *Invalid*: no angle brackets `<`/`>`!

```
In-Reply-To: <3DE2736D.F4FCC064@orcaware.com>; from redacted@orcaware.com on Mon, Nov 25, 2002 at 11:01:01AM -0800
In-Reply-To: Your message of Thu, 18 Mar 1993 22:28:19 GMT.\n             <8280.9303182228@damsay.dcs.ed.ac.uk> 
```

-> *Valid*: an instance of the "obsolete" syntax documented by the specification.

```
References: <abc@def>,<foo\n\tbar@outlook.com>,<baz@outlook.com>
```

-> Commas are valid as part of the obsolete syntax, but the second message-id is malformed because of incorrect line folding (`\n\t`) in the middle of a word.

### Engineering eml-codec for real-world emails

The consequence is that eml-codec needs to be able to *recover from
broken syntax*: on an email containing invalid syntax, it should be able to
discard the broken parts and parse as much as it can from the rest of the email,
instead of simply returning an error. It should also ideally be
able to *parse invalid but common deviations from the specifications* in order
to recover information instead of discarding them.

We first extended eml-codec with coarse-grained recovery strategies, such as
discarding an entire header field if we couldn't parse it. This allowed us to
quickly reach a state where the eml-codec parser is a *total function*: for any
input bytes, it always returns an email AST representing an RFC-compliant
email<sup>[3](https://aerogramme.deuxfleurs.fr/blog/2026-quality-imap-part-1/#email-ast-compliant)</sup>, discarding any part of the input it does not
understand.

We then instrumented the parser to *log each time it discards broken input* when
recovering, and ran the instrumented parser on the email that we collected. This
gave us a lot of examples of legitimate emails with broken syntax. In each case,
then, we manually looked at the piece of broken syntax, see if we could make
some sense of it, and decide whether:

1. we could reasonably extend our parser to parse it;
2. we could discard it more selectively (e.g. only discard a broken element in a list instead of discarding the entire list);
3. our existing discarding strategy was the best we could do.

This whole process was particularly interesting because it made us face the many
subtleties of real-world emails (sometimes far from the "truth" of
specifications); eml-codec is now much more robust operating on real-world emails!

This methodology involves a lot of
tradeoffs and judgment calls: there is a limit to the amount of parsing hacks
that we can add in terms of code quality but also parsing ambiguity; and some
classes of emails are more critical than others (e.g. we should not spend too
much effort supporting spam emails). A strong design constraint of
eml-codec is that, up to a few exceptions, we want its internal AST to only
represent RFC-compliant emails, so we did not want to pollute it to include
random broken syntax just for the sake of "recovering more". The whole process,
in particular, helped us clarify the
[design](https://git.deuxfleurs.fr/Deuxfleurs/eml-codec/src/branch/main/doc/DESIGN.md)
of eml-codec as a library.

For more details, you can look at the release notes of [eml-codec
0.3.1](https://git.deuxfleurs.fr/Deuxfleurs/eml-codec/releases/tag/0.3.1) where
the bulk of the work is done, building on [eml-codec
0.2](https://git.deuxfleurs.fr/Deuxfleurs/eml-codec/releases/tag/0.2) for the
initial setup of parsing recovery. Both shipped with [Aerogramme
0.4](https://git.deuxfleurs.fr/Deuxfleurs/aerogramme/releases/tag/0.4.0).

IMAP's search and retrieval features are essential because they allow clients to
have a snappy UX while handling mailboxes with thousands of emails. This post
focused on getting those basic features right. But, more broadly, we think that
the "mailbox as database" perspective is useful because it raises the question:
which end-user workflows can we enable and support? Which features should we
prioritize or optimize to best support the workflows of day-to-day email users?

*Stay tuned for the next blogpost in the series where we discuss the other big
challenge for an IMAP server: mailbox concurrency!*

Following the database analogy, the logical next step could be to optimize this by first "pre-compiling" queries before running them on emails. Right now we don't know if this optimization would actually matter in practice...

This links to IMAP4rev1 but the more recent IMAP4rev2 isn't more specific on this subject

The current eml-codec AST has a few selected exceptions to this rule, where it allows representing non-compliant data in well identified cases. One of such cases is non-compliant message IDs, such as message IDs without `@`...
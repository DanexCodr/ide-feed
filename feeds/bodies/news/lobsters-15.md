It’s sort of surprising, but we’re still figuring out how to secure simple, record-like information for domain names in an application-accessible way.

Think about it. How would you bind the following to a domain name?

```
example.com
    Key-1: Value-1
    Key-2: Value-2
```

Importantly, how would you secure it?

## DNS and DNSSEC

Since we’re talking about domain names, lets start with DNS. The classic solution adds configuration as TXT records:

```
_PROTOCOL.EXAMPLE.COM.  IN  TXT   "v=PROTOCOLv1; Key-1=Value-1; Key-2=Value-2"
```

Notice that we use an underscored subdomain label to make it clear we aren’t talking about a hostname. The protocol name is then repeated to make it abundantly clear this record is related to the protocol.

As is, we can’t claim this solution is secure. DNS-based network interference is trivial and widespread. The best practice for securing DNS records is DNSSEC, which uses cryptographic signing.

I’m not going to debate the security properties of DNSSEC in this post. There are strong opinions on both sides and the most helpful answer likely depends on the context in which you work. For the sake of this blog post I’ll wave my hands and call this “secure enough” to side-step the issue. In any case, the rest of the post doesn’t depend on a favorable or unfavorable assessment of the security properties of DNSSEC.

## DNSSEC is uncommon

Even the strongest supporters of DNSSEC need to face the reality that DNSSEC isn’t widely adopted.

There’s no single answer that quantifies DNSSEC adoption.
At Fox Loop Software I collect adoption metrics for various Internet protocols; [we just released the first dashboard](https://buttondown.com/foxloopsoftware/archive/email-ecosystem-dashboard/).
Our approach highlights that adoption rates vary widely depending on which cohort you measure.
For example, here are the adoption rates of DNSSEC signed MX records among second-level domain names that accept email:

| Cohort | Adoption rate |
| --- | --- |
| Tranco top 1,000 | 12.3% |
| Tranco top 1,000,000 | 7.5% |
| .COM | 1.4% |
| .GOV | 10.4% |
| .SE | 62.8% |

From the perspective of an application developer, it is not reasonable to expect that a customer domain name will support DNSSEC. Until this changes, application developers must use alternate solutions if they need security.

## The web approach

If my application is web-based then there’s a pretty obvious solution as I already have an HTTPS secured endpoint.
I can use the HTTPS .well-known approach ([RFC 8615](https://www.rfc-editor.org/info/rfc8615/)).

```
GET https://example.com/.well-known/protocol.txt
---
Version: PROTOCOLv1
Key-1: Value-1
Key-2: Value-2
```

These records are secured by HTTPS.
The developer experience is excellent: adding a record could be as easy as dropping a file in a web server directory.
Fetching records is a simple HTTP GET request.

But not everything is a web-based application. Can we extend this solution to other protocols?

## Case study: Email

Email is a very old protocol, predating not only TLS but the entire Internet as well.
Over time all sorts of additions have been bolted on to modernize and maintain the protocol.
Many of these additions added new DNS TXT records, such as SPF, DKIM, and DMARC.
These records can be secured by DNSSEC but do not require it, so tampering of these records is unmitigated or otherwise tolerated.

Let’s look past these examples to a problem that clearly requires a secure record.

### The hostname mis-match problem

Email has an awkward problem, which is how hostnames are managed.
When a message transfer agent (MTA) relays an email it needs to discover the destination MTA.
This is solved using an MX record, which specifies the target MTA’s domain name.
I’ve measured that around 80% of domains host their email on a different domain name, often using providers like Google or Microsoft.

When sending an email, the MTA will discover a chain from the user’s email address to the receiving MTA’s TLS certificate, like this:

The sending MTA now needs to decide if it trusts the connection.
Unfortunately, smtp.provider.com, as seen in the TLS certificate, does not match example.com, as provided in the email address.
The only link between the two domain names is an MX record, which typically unsigned and therefor insecure.
Without trustworthy information, certificate validation cannot succeed and the sending MTA must skip validation.

Lack of certificate validation means that receiving MTAs can use a self-signed, expired, or even a certificate with the wrong name; the sending MTA does not care.
This approach is known as “opportunistic encryption” and it provides strong protection against passive eavesdropping.
But without a way to validate the receiving MTA’s TLS certificate, active attacks remained unmitigated.

Email cannot enforce authenticated MTA-to-MTA transit encryption until this hostname mis-match problem is solved in a secure way.

### A problem end-to-end encryption cannot solve

Many email security conversations focus on end-to-end encryption.
It is a great solution to many of the security problems facing email, but it doesn’t fully address the problem being discussed here.

Message relaying requires the MTA to know the recipient’s email address.
This is known as “envelope information” and it cannot be end-to-end encrypted.
Methods like PGP encryption can not and do not protect this information, as they only encrypt the message body.

The only way to protect this information from network-level attackers is to ensure the message is delivered to the correct MTA, which requires authenticated transit encryption.

### Non-analogous to the web

When I first encountered this issue I was surprised as there is no analogous problem on the web.
The issue relates to the semantic difference between a CNAME and an MX record.
A CNAME record pointing at a web hosting provider’s server is a matter of identity and that server can get a TLS certificate to prove it.
An MX record does not permit the target email server to get a corresponding TLS certificate.

A web browser is able to compare the name in the TLS certificate with the name shown in the address bar and can expect these to strictly match.
An MTA doesn’t compare the name in the TLS certificate with the domain name in the “to” address as a mismatch is typically expected.

Further, email is sent asynchronously so there are no humans involved in MTA-to-MTA communications.
While web browsers can show a certificate warning message to allow users to make their own security decisions, an MTA is all on its own.
Email providers often tout support for transit encryption but the lack of certificate validation makes email traveling between MTAs about as secure as a user browsing the web while *always* clicking through invalid certificate warnings.

Interestingly, email has adopted two solutions to this problem: a DNSSEC-based approach and an HTTPS .well-known approach.
This give us a unique opportunity to compare these approaches head-to-head as they attempt to solve the same problem.

### SMTP DANE

The DNSSEC approach is SMTP DNS-based Authentication of Named Entities (DANE) ([RFC 7672](https://www.rfc-editor.org/info/rfc7672/)),
which was standardized in 2015.
DANE requires DNSSEC signing in both the customer and email provider’s DNS zones for the protection to have full effect.

DANE adds the TLSA DNS record.
Here’s an example:

```
_25._tcp.mail.provider.com.  1200  IN  TLSA  3 1 1 6111A5698D23C89E09C36FF833C1487EDC1B0C841F87C49DAE8F7A09 E11E979E
```

This record indicates that the MTA-to-MTA connection can use authenticated encryption.
Specifically, this record indicates that the receiving MTA should provide a TLS certificate with a public key digest of “6111A…”.
Validating this pinned certificate does not depend on the certificate authority (CA) system.

SMTP DANE signals that it should be possible to cryptographically validate the chain from the domain name in the email address to the domain name on the receiving MTA’s TLS certificate.

One key benefit of DNSSEC, which we’ll revisit, is that blocking of a signed record can be distinguished from a non-existent policy.
When the TLSA record does not exist, the authoritative DNS server should provide a signed proof of non-existence (NSEC).
This acts as a fail safe: if DNSSEC is enabled and the sender cannot determine the DANE policy, then the sender can conclude that it is not safe to send the message as network interference may be present.

### MTA-STS

Email providers realized that slow adoption of DNSSEC was delaying authenticated transit encryption between MTAs.
They looked at what other tools were available and found inspiration from the HTTPS .well-known approach.
Standardized in 2018, SMTP MTA Strict Transport Security (MTA-STS) ([RFC 8461](https://www.rfc-editor.org/info/rfc8461/)) provides an HTTPS-based solution.

Here’s what it looks like:

```
GET https://mta-sts.example.com/.well-known/mta-sts.txt
---
version: STSv1
mode: enforce
mx: smtp.provider.com
max_age: 604800
```

Notice that the mta-sts subdomain is used instead of the bare domain.
This best practice stems from the need to isolate security policies from whatever website lives at the bare domain; often a marketing website which may not have a security posture suitable for cross-protocol policies like MTA-STS.
To distinguish any pre-existing use of the mta-sts subdomain the “_mta-sts” TXT record must also be set.

```
_mta-sts.example.com. 3600     IN      TXT     "v=STSv1; id=190906205100Z;"
```

Finally, policy caching was added as a partial mitigation of intermittent network interference.

Like DANE, MTA-STS signals that the sender should strictly authenticate TLS.
The MX record is duplicated in the MTA-STS policy, relying on HTTPS to secure the link.
MTA-STS requires the receiving MTA to have a TLS certificate issued by a well-trusted CA.

An MTA-STS policy document is fairly unchanging, making it well-suited for inexpensive, widely available, and highly scalable static web hosting.
Many domain owners implement MTA-STS by adding the subdomain to an existing web server, as a virtual host, although it turns out this isn’t always a good idea.

### MTA-STS challenges

The TLS certificate renewal process is an obvious point of failure for MTA-STS.
When a user-facing website goes down users complain, support tickets are filed, and the certificates are quickly renewed.
The MTA-STS policy server fails open when it’s certificate expires.
Senders will fall back to using opportunistic encryption and users won’t notice any disruption.
As such an expired TLS certificate on an MTA-STS policy server can go unnoticed.
To address this lack of visibility, TLS Reporting ([RFC 8460](https://www.rfc-editor.org/info/rfc8460/)) was created, which allows email servers to share deliverability reports with each other.

Another problem, which I think is an even larger issue, are web servers that block email servers from accessing their MTA-STS policy.
You’ve probably noticed a sharp rise in bots, scrapers, and other unwanted automated traffic impacting the web.
In the rush to protect web servers from these ills many sites inadvertently blocked access to their MTA-STS policy.
An email server fetching an MTA-STS policy can look a lot like unwanted traffic: it’s automated and its coming from data center IP ranges.
Misapplying security policies intended to protect user-facing websites from unwanted bot traffic degrades API-like interfaces.

### Comparing MTA-STS and DANE

One unique benefit of SMTP DANE is that the policy cannot be blocked without the sender noticing.
An MTA-STS policy server can be blocked just like any other web server and this blocking cannot easily be distinguish from a non-existent policy.

While MTA-STS caching can protect against intermittent network-level blocking of the policy server, the first email sent to a domain is always vulnerable due to an empty cache.
The effectiveness of MTA-STS in preventing an on-path attacker from intercepting email is questionable if the same on-path attacker can block the sender from discovering the MTA-STS policy.

By these measures, DANE seems like the stronger option.

DANE’s reliance on DNSSEC signing is its major weakness.
[Measurements show that 0.9-1.2%](https://buttondown.com/foxloopsoftware/archive/email-ecosystem-dashboard/) of domain names that receive email have DANE support, which doesn’t provide much practical protection yet.
Worse, large providers like gmail.com lack DNSSEC support, so the per-user impact may be larger.
Unless DNSSEC adoption can grow among large email providers, DANE can only be a partial solution.
In contrast, HTTPS is very widely adopted making MTA-STS familiar to practitioners, even with these challenges.

### Improving MTA-STS

The web has blazed a path that MTA-STS can likely follow.
HTTP Strict Transport Security (HSTS) ([RFC 6769](https://www.rfc-editor.org/info/rfc6797/)) is essentially MTA-STS for the web (or visa-versa).
HSTS is similarly vulnerable when the cache is empty.
Web browsers mitigate this issue using a preload list, which ships in the browser.
Out-of-the-box, the web browser knows that popular websites, like wikipedia.com, strictly use HTTPS.
While there are challenges with HSTS, [like the size of the list](https://alexsci.com/blog/hsts-adoption/), this may have marginal impact for a server-side technology like email.

I think MTA-STS can copy this solution.
There are unknowns, like who would build an MTA-STS preload list, why we trust them to do so, and the exact semantics needed for a domain to be added.
In any case, I think we should wait on increased MTA-STS adoption before we take those next steps.

## The race is on

The adoption rates of MTA-STS and SMTP DANE tell an important story about how application protocols can secure domain information in practice.
The fact that email has both a DNSSEC and an HTTPS approach gives us a way to spectate.

Current measurements show that MTA-STS has overtaken DANE among the top-ranked domain names.

| Tranco Rank | DANE adoption | MTA-STS adoption |
| --- | --- | --- |
| Top 1K | 1.0% | **2.6%** |
| Top 10K | 1.2% | **1.9%** |
| Top 100K | 1.1% | **1.3%** |
| Top 1M | **1.0%** | 0.7% |

Given the importance of protecting messages, including envelope information which cannot be end-to-end encrypted, these results are disappointing.

[Prior work shows that TLS downgrade attacks on email are widespread](https://dl.acm.org/doi/pdf/10.1145/2815675.2815695).
With the slow adoption of email security protocols since that study, the situation is unlikely to have improved.
We can and should do better.

These SMTP DANE and MTA-STS measurements will be published quarterly.
[Subscribe to the newsletter](https://buttondown.com/foxloopsoftware/archive/email-ecosystem-dashboard/) to follow the trends.

## Similar approaches

MTA-STS isn’t the only protocol that works this way.

OpenPGP Web Key Directory (WKD) ([draft-koch-openpgp-webkey-service-22](https://datatracker.ietf.org/doc/html/draft-koch-openpgp-webkey-service-22))
uses an HTTPS .well-known approach to secure PGP key distribution, facilitating end-to-end encryption of message bodies.

```
GET https://openpgpkey.example.org/.well-known/openpgpkey/example.org/hu/iy9q119eutrkn8s1mk4r39qejnbu3n5q?l=Joe.Doe
```

The WKD “advanced method”, seen above, follows the best practice of using a protocol-specific subdomain.

The analogous DNSSEC-based approach is OPENPGPKEY ([RFC 7929](https://www.rfc-editor.org/info/rfc7929/)).

```
<SHA-256 hash based on email address>._openpgpkey.example.com. IN OPENPGPKEY <public key base64>
```

Unfortunately, the SHA-256 hash does not provide meaningful privacy.
Use of this protocol can leak the email addresses of your correspondents to passive network-level eavesdroppers.
This highlights the importance of encryption, not just signing.

Other protocols like Mail AutoConfig ([draft-ietf-mailmaint-autoconfig-07](https://datatracker.ietf.org/doc/draft-ietf-mailmaint-autoconfig/)) simplify the process of setting up an email client and similar applications.

```
GET https://autoconfig.example.com/.well-known/client-autoconfig.xml?emailaddress=fred@example.com
```

Again we see this protocol follow the security best practice of using a protocol-specific subdomain.

There are [over 100 registered .well-known URIs](https://www.iana.org/assignments/well-known-uris), showing the popularity of this approach.
Many of these tolerate lower security properties and use the bare domain name instead of a protocol-specific subdomain.

## Complementary solutions

While I’ve thus far framed the discussion as a competition, DNSSEC and HTTPS .well-known are actually complementary.
We don’t need one approach to defeat the other: we’ll see ecosystem improvements as both solutions are adopted, side-by-side.
HTTPS .well-known can offload large policy documents and allow rapid experimentation, avoiding the size limits of UDP packets and the slow process of adding new DNS record types.
DNSSEC can sign the CAA record, providing improved security during TLS certificate issuance.

DANE could even replace the CAs entirely, a topic of renewed interest after the recent [eMudhra mishap](https://bugzilla.mozilla.org/show_bug.cgi?id=2083449).
After all, [we wouldn’t need the CAs if we had a secure DNS](https://youtu.be/vBPF71iYmVY?t=358).

I see complementary nature of DNSSEC and HTTPS .well-known emphasized in another draft,
Domain Authority (DA): A DNS-Designated Service Endpoint for Domain Information
([draft-swaminathan-da-00](https://datatracker.ietf.org/doc/html/draft-swaminathan-da-00)),
which seeks to standardize the use of HTTPS to add capabilities to domain names beyond what DNS can natively support.
While I think the current draft is too ambitious in scope, it provides a great summary of the benefits an HTTPS-based policy retrieval layer can provide beyond DNS.

Unfortunately, we still have an insecure DNS.
But progress in the domain name ecosystem is not blocked by DNS.
MTA-STS shows that an HTTPS approach is immediately usable.
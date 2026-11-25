Non-browser applications have historically relied on a slowly changing set of
            trust roots maintained by the operating system or platform vendors. These trust roots
            are often based on browser root programs, but lack the data that allow browsers to make
            fine-grained trust decisions: revocation data for end entities, intermediates and
            roots (like
            [CRLite](https://blog.mozilla.org/security/2020/01/09/crlite-part-1-all-web-pki-revocations-compressed/)
            and
            [OneCRL](https://blog.mozilla.org/security/2015/03/03/revoking-intermediate-certificates-introducing-onecrl/)), distrust dates and Certificate Transparency policy.

The
            [October 2026 eMudhra incident](https://emudhra.we-have-a-problem.com/)
            showed the cost. Browsers blocked the affected intermediates quickly, while other clients were unable
            to restrict only the affected intermediates. Instead, they had to wait for platform trust store
            updates to remove the parent root certificates and spent significant time and effort
            to mitigate the impact on their applications across different platforms and environments.

upki ships these signals as a compact local cache that's updated automatically,
            independently of applications, so every TLS stack on a machine can share one copy.
            Its checks only ever narrow what a client accepts: they never make it trust a
            certificate it would otherwise reject.

Sponsorships are annual and pay for maintainer time on the roadmap and on ongoing
          maintenance. We don't sell individual features; priorities are open for discussion with
          sponsors.

For more information, contact [Dirkjan Ochtman](mailto:dirkjan@ochtman.nl).

| Included | Supporter**$15k**per year | Sustainer**$50k**per year | Strategic partner**$150k+**per year |
| --- | --- | --- | --- |
| Logo on the project README and site | Listed | Larger | Featured |
| Quarterly roadmap calls with the maintainers |  |  |  |
| Priority on issues you report | – |  |  |
| Design partner on future ideas | – | – |  |
| Production-quality hosted infrastructure | – | – |  |

## Roadmap

Sponsors help set priorities through quarterly roadmap calls.

1. Shipped Revocation Clients outside the browser accept revoked end-entity certificates. upki syncs compact CRLite filters several times a day and checks revocation offline.
2. 1 Next Root distrusts When root programs distrust a CA or intermediate, other clients keep trusting it until a trust store package update arrives, as the eMudhra incident showed. upki will ship OneCRL data, so distrust takes effect at the next cache update.
3. 2 Applied for funding Merkle Tree Certificates Post-quantum signatures would add kilobytes to every TLS handshake. Merkle Tree Certificates can bring down the costs, but clients need landmarks delivered ahead of time to minimize handshake overhead. upki will distribute landmarks alongside its other data.
4. 3 Planned CT enforcement Clients that don't enforce Certificate Transparency accept certificates that were never publicly logged, so misissuance can go unnoticed. Clients also don't benefit from certificate transparency logs blocking compromised/distrusted roots from obtaining proof of inclusion. upki will deliver and maintain an up-to-date log list and policy inputs, so applications don't have to configure logs manually.
5. 4 Planned Intermediate preloading Servers that send an incomplete certificate chain work in browsers but fail verification in other clients. upki will ship the known intermediate certificates, so clients can complete the chain as browsers do, without expensive network fetching.
6. + Future idea Fleet trust roots Root changes, including private PKI roots, reach machines through OS packages or configuration management, which can be slow and uneven across a fleet. upki's sync mechanism could distribute root sets to every machine.
7. + Future idea More integrations The checks only protect applications whose TLS stack uses upki. upki could gain native support in OpenSSL upstream, GnuTLS, NSS or in language runtimes.

### Ongoing maintenance

Every check depends on data that's refreshed several times a day, on upstream sources
              and formats that keep changing, and on prompt fixes when security issues come up.

Sponsorship pays for releases, security response, dependency updates, keeping the data
              pipeline running and in step with upstream changes, supporting distribution packagers
              and maintaining
              [C2SP specifications](https://c2sp.org/upki-revocation@v1.0.0).
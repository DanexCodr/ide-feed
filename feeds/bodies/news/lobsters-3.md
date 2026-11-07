```
vincent    HTTPS  1 first.geo  alpn="h3,h2"
vincent    HTTPS  2 second.geo alpn="h3,h2"
vincent    HTTPS  3 .          alpn="h3,h2"

; Bunny DNS must provide the two closest servers as "first.geo"
; and "second.geo" with geographic or latency routing.
first.geo  A      45.90.160.60
first.geo  AAAA   2a0c:8881:5:100::1
second.geo A      116.203.18.48
second.geo AAAA   2a01:4f8:1c0c:5eb5::1

vincent    A      45.90.160.60
vincent    A      116.203.18.48
vincent    AAAA   2a0c:8881:5:100::1
vincent    AAAA   2a01:4f8:1c0c:5eb5::1
```

HTTPS records are [still too new](https://www.netmeister.org/blog/https-caniuse.html)[22] for this use case. Back to the draw­ing board! 📐

## The hybrid solution[#](https://vincent.bernat.ch/en/blog/2026-bunny-geodns#the-hybrid-solution)

```
export default function handleQuery(query) {
  const location = query.request.geoLocation;
  let candidates = servers.map(
    (s) => new Server(s.ipv4, s.latitude, s.longitude, 100),
  );

  // Select the two closest servers
  const selected = [];
  while (selected.length < 2) {
    const server = RoutingEngine.getClosestServer(candidates, location, true);
    selected.push(server);
    candidates = candidates.filter((s) => s.ip !== server.ip);
  }

  // Compute the distance to the user for each of them
  const [first, second] = selected.map((s) =>
    GeoDistance.calculate(s, location),
  );

  // If the second one is at twice the distance and at more than 1000 miles
  // from the first, return only the first one with a TTL of 2 minutes.
  if (second > 2 * first && second - first > 1000) {
    return [new ARecord(selected[0].ip, 120)];
  }

  // Otherwise, return both with a TTL of 1 hour.
  return selected.map((s) => new ARecord(s.ip, 3600));
}
```

```
$ doggo --gp-from="Chicago" A vincent.bernat.ch
LOCATION          NAME                TYPE  TTL    ADDRESS
Chicago (IL), US
                  vincent.bernat.ch.  A     120s   5.161.44.145
$ doggo --gp-from="Mexico" A vincent.bernat.ch
LOCATION          NAME                TYPE  TTL    ADDRESS
Queretaro, MX
                  vincent.bernat.ch.  A     3600s  5.161.44.145
                  vincent.bernat.ch.  A     3600s  149.28.219.155
$ doggo --reverse 5.161.44.145 149.28.219.155
NAME                          TYPE  TTL    ADDRESS
145.44.161.5.in-addr.arpa.    PTR   7187s  web05.luffy.cx.
155.219.28.149.in-addr.arpa.  PTR   3600s  web07.luffy.cx.
```

Note

Note

This page was brought to you by `???`. Check on the map be­low whether it matches your
location!

![Map of the servers answered by Bunny DNS for each location](https://media-bernat-ch.b-cdn.net/images/bunny-dns-map.05f55a00ae040e.svg)

# ACME DNS with Hickory DNS[#](https://vincent.bernat.ch/en/blog/2026-bunny-geodns#acme-dns-with-hickory-dns)

```
[[zones]]
zone = "acme.luffy.cx"
zone_type = "Primary"

[zones.stores]
allow_update = true
type = "sqlite"
journal_path = "acme.luffy.cx.sqlite"
zone_path = "acme.luffy.cx.zone"

# Private key to sign the zone with DNSSEC. Generated with:
#  openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256
[[zones.keys]]
algorithm = "ECDSAP256SHA256"
key_path = "/etc/hickory-dns.acme.luffy.cx.pem"

# TSIG key to sign zone updates. Generated with:
#  openssl rand 32
[[zones.stores.tsig_keys]]
algorithm = "hmac-sha256"
key_file = "/etc/hickory-dns.acme.luffy.cx.update.acme.luffy.cx.tsig"
name = "update.acme.luffy.cx."
```

```
_acme-challenge          CNAME bernat.ch.acme.luffy.cx.
_acme-challenge.vincent  CNAME vincent.bernat.ch.acme.luffy.cx.
```

```
$ ZONE=acme.luffy.cx
$ dig @nsupdate.luffy.cx $ZONE DNSKEY +noall +answer \
>   | dnssec-dsfromkey -a SHA-256 -f - $ZONE
acme.luffy.cx. IN DS 55628 13 2 4946E7508F20E15F1B577A231104B029A1A82E04699A80CD46ADCE31227EE81F
```

Over­all, I am quite happy with the switch to *bunny.net*. There are still a few
rough edges, like the in­abil­ity to pub­lish `DS` records, the lack of HTTP/3, and
the IPv4-only `RoutingEngine.​getClosestServer()` helper. The bill went from US$5
per month to US$1. So far, per­for­mance is [on par with AWS](https://cruxvis.withgoogle.com/#/?view=loadingperf&url=https%3A%2F%2Fvincent.bernat.ch&identifier=origin&device=ALL&periodStart=0&periodEnd=-1&display=p75s)[39], but I
only fi­nal­ized the cur­rent setup, in­clud­ing the server in Syd­ney, in late
Oc­to­ber. I need a bit more time to gather more data, and I’ll post a short update. 📈
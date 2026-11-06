That is a real ping, to a real box, and it got a real reply. The thing after `ping -c1` is a mix of LCD segmented digits, superscripts, subscripts, circled digits, a double-struck `X` and math-alphabet digits, with nine invisible characters that my terminal drew as white boxes because it had no idea what else to do with them. Paste it into a terminal and it looks like line noise. Hand it to `getaddrinfo()` and it is `69.30.206.130`.

Every example in this post points at the same server, `69.30.206.130`. It answers ping, and it serves exactly one page, `/poc.html`, on its bare IP so you can prove the HTTP side works too. Every screenshot is real output, captured on Ubuntu 24.04 with glibc 2.39, iputils 20240117 and curl 8.5.0.

Start with the boring part, which is already weirder than most people expect. An IPv4 address is a 32-bit unsigned integer. The dotted quad is just how we have agreed to write it down. The parser that turns text into that integer is `inet_aton()`, and its rules date back to 4.2BSD. In glibc it lives in `resolv/inet_addr.c`, and each part is read like this:

```
/* Collect number up to ``.''.  Values are specified as for C:
   0x=hex, 0=octal, isdigit=decimal.  */
...
unsigned long ul = __strtoul_internal (cp, &endp, 0, 0);
```

Base 0 means `strtoul()` picks the base from the prefix: `0x` is hex, a leading `0` is octal, anything else is decimal. Each dotted part gets its own prefix, so you can mix bases inside one address. Then there is the part count:

```
/* Internet format:
     a.b.c.d
     a.b.c    (with c treated as 16 bits)
     a.b      (with b treated as 24 bits).  */
```

One part is the whole 32-bit number. Two parts are an 8-bit network and a 24-bit host. Three parts are 8, 8 and 16 bits. These were meant for the old class A/B/C networks, and nobody ever took them out. Leading zeros are unlimited too, as long as the value still fits.

| Form | 69.30.206.130 as |
| --- | --- |
| Decimal integer | `1159646850` |
| Hex integer | `0x451ece82` |
| Octal integer | `010507547202` |
| Dotted hex | `0x45.0x1e.0xce.0x82` |
| Dotted octal | `0105.036.0316.0202` |
| 3 parts, last one 16 bits | `69.30.52866` |
| 2 parts, last one 24 bits | `69.2018946` or `69.0x1ece82` |
| Mixed bases | `0x45.036.206.0202` |
| Over-padded hex | `0x00000000000000451ece82` |

Everything above is well known. It is the reason SSRF filters are supposed to parse addresses instead of regexing them. The fun starts with a flag most people never look at: `AI_IDN`.

`AI_IDN` is a glibc extension that tells `getaddrinfo()` the name might be an internationalized domain name, so it should be converted to ASCII before lookup. ping sets it, because iputils is built with IDN support. Here is what glibc does with it, in `sysdeps/posix/getaddrinfo.c`:

```
if (req->ai_flags & AI_IDN)
  {
    char *out;
    result = __idna_to_dns_encoding (name, &out);
    if (result != 0)
      return -result;
    name = out;
    malloc_name = true;
  }

if ((result = text_to_binary_address (name, req, &res)) != 0)
  goto free_and_return;
```

Look at the order. The IDNA conversion runs **first**, and the numeric address parser only sees the output. `__idna_to_dns_encoding()` hands the string to libidn2, which applies [UTS #46](https://www.unicode.org/reports/tr46/) mapping. UTS #46 exists so that a user typing a domain in a different width or style still lands on the same name. To do that it folds a huge range of compatibility characters down to plain ASCII. That table does not care that the result is going to be read as a number.

```
2473  ; mapped  ; 0032 0030  # CIRCLED NUMBER TWENTY             ⑳ -> 20
325A  ; mapped  ; 0033 0030  # CIRCLED NUMBER THIRTY             ㉚ -> 30
24EA  ; mapped  ; 0030       # CIRCLED DIGIT ZERO                ⓪ -> 0
1FBF6 ; mapped  ; 0036       # SEGMENTED DIGIT SIX               🯶 -> 6
1D7CE ; mapped  ; 0030       # MATHEMATICAL BOLD DIGIT ZERO      𝟎 -> 0
1D501 ; mapped  ; 0078       # MATHEMATICAL BOLD SCRIPT SMALL X  𝔁 -> x
216D  ; mapped  ; 0063       # ROMAN NUMERAL ONE HUNDRED         Ⅽ -> c
1D49  ; mapped  ; 0065       # MODIFIER LETTER SMALL E           ᵉ -> e
3002  ; mapped  ; 002E       # IDEOGRAPHIC FULL STOP             。 -> .
```

Digits are covered, and so are the dots. The `x` in a hex prefix and the `a`–`f` hex letters are covered too, which means every one of the classic forms above can be rebuilt out of Unicode lookalikes:

Circled two-digit numbers are a nice touch: `⑥⑨.㉚.⑳⑥.⑬⓪` is four characters shorter than the plain address it decodes to. Hex works the same way, with a bold script `x` for the prefix, a Roman numeral one hundred standing in for `c`, and modifier letters for `e`:

Notice that ping echoes back `0x451ece82` in its `PING` line. ping also asks for `AI_CANONIDN`, so what it prints is the name *after* IDNA mapping. That is the clearest view you will get of what the resolver actually parsed.

## Full Chaos

Nothing says a single address has to stick to one style. The mapping is done one character at a time, so every digit, dot and hex letter can come from a different block. I wrote a small script that reads `IdnaMappingTable.txt`, collects every code point that maps to `0`–`9`, `a`–`f`, `x` or `.`, and rebuilds each classic form by picking a random lookalike for every character: fullwidth, superscript, subscript, circled, math bold, sans-serif, monospace, double-struck, script, fraktur, Roman numerals, and the LCD segmented digits from `🯰` to `🯹`. Every result resolved:

Here are a few more, all `69.30.206.130`, ready to paste:

```
ping -c1 𝟼𝟵．🯳𝟶。𝟚𝟘🯶．𝟏𝟥⓪  # 69.30.206.130
ping -c1 🯰𝖝⁴𝟝｡⁰𝚇𝟙𝗲｡０ₓ𝖢ｅ｡⓪𝑋𝟖🯲  # 0x45.0x1e.0xce.0x82
ping -c1 𝟢𝓧④𝟱₁ᵉⒸ𝘌🯸🯲  # 0x451ece82
ping -c1 ０１⓪₅｡𝟘🯳𝟞．₀３𝟙𝟞。𝟶𝟤₀𝟮  # 0105.036.0316.0202
ping -c1 𝟞𝟗。𝟑𝟢｡🯵𝟤₈𝟼６  # 69.30.52866
ping -c1 𝟨⑨．𝟬𝕩𝟏Ｅ𝐜ᵉ🯸𝟸  # 69.0x1ece82
ping -c1 ⁰𝑋⁴5．🯰３₆。⁵₂₈𝟲🯶  # 0x45.036.52866
ping -c1 𝟣🯱𝟻⑨6𝟜⑥🯸𝟝𝟎  # 1159646850
ping -c1 𝟬ｘ🯴𝟝．𝟹𝟬．₀3𝟣６｡𝟎Ⅹ🯸𝟚  # 0x45.30.0316.0x82
```

UTS #46 does not only map characters. It also has a category called **ignored**, and an ignored code point is simply deleted from the input:

```
00AD          ; ignored  # SOFT HYPHEN
200B          ; ignored  # ZERO WIDTH SPACE
2064          ; ignored  # INVISIBLE PLUS
E0100..E01EF  ; ignored  # VARIATION SELECTOR-17..VARIATION SELECTOR-256
1BCA0..1BCA3  ; ignored  # SHORTHAND FORMAT LETTER OVERLAP..UP STEP
```

So you can put invisible characters before, inside and after the address, and they are gone before `inet_aton` ever sees the string. I verified soft hyphen, zero width space, word joiner, invisible plus, combining grapheme joiner, Mongolian free variation selector, variation selectors 1, 16 and 17, the BOM, and the shorthand format controls. Most terminals render them as nothing. Mine renders them as the white `<fe0f>` boxes in the cover image, which is how I noticed the copy-pasted address was not what it looked like.

The cover combines all of it: a zero-padded hex first part, a zero-padded octal second part, and a 16-bit decimal tail, with every character swapped for a random lookalike and nine ignored code points scattered through it. After mapping it is `0x00000045.00036.52866`, which `inet_aton` reads as 0x45, 036 (octal 30) and 52866 (206 × 256 + 130).

None of this is magic in `getaddrinfo()` itself. It only happens when the caller passes `AI_IDN`. Without the flag, glibc goes straight to the numeric parser, sees a circled zero, and falls through to a DNS lookup that fails. Python makes the difference easy to see:

```
>>> socket.getaddrinfo('⓪𝔁④⑤①𝕖𝒸ⓔ⑧②'.encode(), None, socket.AF_INET, 0, 0, 0)
socket.gaierror: [Errno -2] Name or service not known
>>> socket.getaddrinfo('⓪𝔁④⑤①𝕖𝒸ⓔ⑧②'.encode(), None, socket.AF_INET, 0, 0, 0x40)  # AI_IDN
[(<AddressFamily.AF_INET: 2>, ..., ('69.30.206.130', 0))]
```

Tools that do their own IDN conversion work as well. curl and wget both link libidn2 and run the hostname through it before resolving. OpenBSD netcat does not, and fails:

The last command there is a different failure. IPv4-mapped IPv6 such as `::ffff:69.30.206.130` works in curl, because the kernel turns a connect on an IPv6 TCP socket to a mapped address into IPv4. ping instead opens an ICMPv6 socket and sends a real IPv6 packet to `::ffff:0:0/96`, which no router will carry.

curl has its own wrinkle. Its URL parser has an `ipv4_normalize()` step that rewrites `0x451ece82` or `69.2018946` to `69.30.206.130`, but that runs *before* IDN conversion. A Unicode host skips normalization, gets converted to ASCII afterwards, and goes out on the wire like that. The server receives a `Host:` header of `0x451ece82`:

curl also percent-decodes the host part of a URL, so `http://%36%39.30.206.130/`, `http://69%2E30%2E206%2E130/`, and the fully percent-encoded UTF-8 of the circled hex address all connect as well.

Because a lot of code decides whether something is an IP address by looking at it. Blocklists, SSRF guards that regex for `169.254.` or `127.`, log searches, chat filters, and a human reading a config file all compare strings. If the thing doing the check does not run the same IDNA mapping and the same `inet_aton` rules as the thing doing the connect, the check and the connection are looking at two different strings. `⓪𝔁⑦𝒇⓪⓪⓪⓪⓪①` is `127.0.0.1`, and so is `①②⑦。①`.

`⁰𝑋⁴5．🯰３₆。⁵₂₈𝟲🯶` is a valid IP address. It resolves to `69.30.206.130`, and that is fucking weird.

It is also more than a party trick. Malware has used the plainer versions of this for years: [Emotet spam in 2022](https://www.trendmicro.com/en_us/research/22/a/emotet-spam-abuses-unconventional-ip-address-formats-spread-malware.html) wrote its download URLs with hex and octal IP addresses, likely to dodge pattern matching. The same idea applies to any filter that only reads the input. If something refuses `127.0.0.1`, you could hand it `⁰𝑋𝟳𝖿．①` instead, and `ping` lands on loopback all the same.

The defence is the boring one: resolve first, then check the address you actually got back, and connect to that exact address. Never check the string.

The address is still just a number, so the trick is not in `getaddrinfo()` — it is in the address bar. Drop a fully percent-encoded Unicode host into a URL with a made-up `user:pass@` prefix and a `/?` query, and the host stops being the part a human reads.

```
http://images.google.com:static-uploads@%E2%93%AA%F0%9D%94%81%E2%85%AD%E2%85%AEb97a5a/?picture_of_you.png
        └── user ──┘ └── pass ──┘ └────────── host ──────────┘ └── path ───┘
                          (circled + math-bold hex, the integer 0xcdb97a5a)
```

Glance at it and the eye lands on the trusted-looking parts: `images.google.com` as the user, `static-uploads` as the password, `?picture_of_you.png` as a path to a photo. But the host is the hex integer `0xcdb97a5a`, and `inet_aton()` turns it into `205.185.122.90`. curl connects there, sends `Host: 0xcdb97a5a`, and ignores the credentials and the path entirely — they are decoration. A single one is easy to pass; a list of them is how a phishing link looks like a Google image.

The same trick works with the plain hex form, which is the cleanest because nothing has to be mapped:

```
curl images.google.com:static-uploads@0xcdb97a5a/?picture_of_you.png
        └── user ──┘ └── pass ──┘ └── host = 205.185.122.90 ──┘ └── path ─┘
```

Two things make it stick. First, humans read a URL as one token and rarely isolate the host field; the `user:pass@` prefix and the `/?file` suffix both read as authoritative and pull attention away from the middle. Second, the decoy and the real target disagree about what the URL means. The browser or the reader sees a path to an image; `getaddrinfo()` sees a number and connects to it. The decoy does not have to be wrong — `0xcdb97a5a` really is `205.185.122.90` — it only has to be something the reader does not expand.

It is the same gap as the blocklist check, aimed at the eye instead of the regex. A guard that regexes `127.` or `169.254.` on the string still misses `0x7f000001`; a person who reads `0xcdb97a5a` as "some hex" misses it too. The defence is the same: expand the host to the number it really is, and connect to that.

curl is not the only tool that reads a number where you do not. `wget` takes the URL as its first positional argument and treats everything after it as an option. Drop a bare integer in place of the URL and a URL-looking value in an option, and the eye lands on the option — but the number is what actually gets fetched.

```
wget -q 1159646850 -A=http://images.google.com/static/pic_of_you.png
     └── host ──┘       └──────────── decoy ─────────────┘
     69.30.206.130
```

`1159646850` is just `69.30.206.130` in decimal, and it is the URL — wget connects there and sends `Host: 1159646850`. `-A` is `--user-agent`, but most people read it as just a flag and take the `images.google.com` link as the target, thinking the number belongs to `-q`. The number is the host; the link is the decoy, and it does not have to be wrong — the same gap, a tool that reads the option as the target instead of the argument. `-A` works better than `--comment` for the trick: short, nearly invisible, and nobody assumes a user-agent is a URL.

Every form I tested, against `69.30.206.130`. `ping` is iputils ping with one packet. `curl` fetched `http://<address>/poc.html` and got a 200. Every address is the real string, so you can copy it straight into a terminal. The invisible characters are in there even though you cannot see them.
The bug is **reachable from the following frameworks in their default configuration**. Other frameworks are not exposed by default, but application code that upcases strings received in a legacy encoding may also be vulnerable.

| Framework | Status on an affected Ruby |
| --- | --- |
| Rails | Affected |
| Sinatra (classic style) | Affected |
| Other frameworks and plain Rack | Not exposed by default |

These products bundle their own Ruby, so the fix has to come
              from the vendor. Products marked
Vulnerable have no fixed
              release yet: every current version is vulnerable.

| Software | Affected versions | Fixed in | Status |
| --- | --- | --- | --- |
| GitHub Enterprise Server | **3.22.5** and earlier | None | Vulnerable |
| Chatwoot | **4.20.0** and earlier | None | Vulnerable |
| GitLab | **19.6.0** and earlier | **19.6.1**, **19.5.8** | Patched |
| Mastodon | **4.7.5** and earlier | **4.7.6**, **4.6.12**, **4.5.22**, **4.4.29** | Patched |
| OpenProject | **17.9.7** and earlier | **17.9.8**, **17.8.3** | Patched |
| Discourse base image | Before **2.0.20261119-0203** | **2.0.20261119-0203** | Patched |

## Remediation

## Technical details

Most of Ruby's single-byte encodings have no capital
`ß`. Upcasing it writes two bytes, `SS`, but
              the loop only bounds-checks one (`to < to_end`).

The output buffer is allocated as the input length plus 20
              bytes. Each `ß` adds one byte to the output, so an
              input with 21 of them overflows the buffer by one byte.

The same loop is in several ISO-8859 and Windows-125x encodings
              and has been there since Ruby 2.4.0. It is reached by
`upcase`, `swapcase`,
`downcase(:fold)` and `casecmp?`.

UTF-8 strings take a different code path and are not affected.

Fixed upstream in
[`ruby/ruby@d582f8f`](https://github.com/ruby/ruby/commit/d582f8f13d700d8e39714d3a8f11eb4bd2bc69f0).

### Primitive

A one-byte heap overflow. The byte written is `S`
(`0x53`) when upcasing or `s`
(`0x73`) when case-folding, and it lands directly
              after the output buffer. The attacker controls the size of the
              buffer through the input length.

Copying the result out of the buffer then reads one byte out of
              bounds.

## Proof of concept

## Credits

Veria Labs found this vulnerability independently and was the
              first to demonstrate remote code execution.

The
[Ruby security advisory](https://www.ruby-lang.org/en/news/2026/11/18/multiple-vulnerabilities-in-regexp-and-string/)
also credits Stephan Lipp (Ada Logics) and Anthropic with reporting
              the underlying primitive. Additional discoverers include
[Moritz Sanft](https://durendal.sh/blog/ruby-case-mapping-bugs) in collaboration with OpenAI.
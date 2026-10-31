From curl 8.12 through 8.16, config files could slice variable values and include other config files without an explicit depth cap. Together, these features let curl simulate any two-counter Minsky program. Under the usual idealization of unbounded strings and resources, this construction was Turing-complete.

Curl 8.17.0 added a five-level include cap that breaks this reduction.

**Update 2026-10-30**: Jonathan Tremesaygues wrote me: *I couldn't help but implement “99 Bottles of Beer on the Wall”* [99_bottles.tar.gz](https://seriot.ch/resources/99_bottles.tar.gz): `curl -q -s -K 99_bottles/main.conf`

A counter value `n` is represented by `n` copies of `x`.

Each instruction state uses one or more config files, with file names acting as labels, and `expand-config` selecting the next file.

Syntax:

- {{b}} expands the current value
- [0-0] keeps only the first byte (x or empty)
- [1-] keeps everything except the first byte
- empty slices yield empty strings (doc)

| Minsky | Curl config |
| --- | --- |
| Register `R` | Variable `r` (`R` is the number of `x` bytes) |
| `INC(R)` | `expand-variable = "r={{r}}x"` |
| `DEC(R)` | `expand-variable = "r[1-]={{r}}"` |
| `JZ(R, _, _x)` | `expand-variable = "t[0-0]={{r}}"` `expand-config = "state_{{t}}.conf"` |
| `JMP(S)` | `expand-config = "S.conf"` |
| Halt | No further `expand-config` |

With that, we can compile any two-counter program into curl config files.

Four files in [curl_addition.zip](https://seriot.ch/resources/curl_addition.zip) compute 2 + 3.

![](https://seriot.ch/resources/curl_config.png)

Build a local curl 8.12.0 binary if needed:

```
mkdir -p /tmp/curl-tc-build
cd /tmp/curl-tc-build
curl -fsSLO https://curl.se/download/curl-8.12.0.tar.gz
tar -xzf curl-8.12.0.tar.gz
cd curl-8.12.0
./configure --without-ssl --disable-shared --disable-manual --disable-docs
make -j4
```

Then, from the `addition/` directory, run:

```
/tmp/curl-tc-build/curl-8.12.0/src/curl -q -s -K main.conf
```

Expected output:

```
A=xxxxx B=
```

The reduction assumes unbounded counters and unbounded steps. The real binary has neither:

The [pull request](https://github.com/curl/curl/pull/19168) says the cap prevents a config file from including itself indefinitely. Its [regression test](https://github.com/curl/curl/blob/curl-8_17_0/tests/data/test774) does exactly that and expects an error. The public explanation does not discuss Turing completeness or why the cap is five.

A Bash `while` loop can complement bounded curl by invoking a config once per step and carrying the counters and instruction label between invocations. The repetition then comes from Bash, so this is a composition rather than curl-alone Turing completeness.
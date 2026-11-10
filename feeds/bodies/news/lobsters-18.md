Terminal2Shell is a design-level vulnerability in terminal emulators. When a terminal is launched, it immediately spawns a **shell process** and connects it directly to the user's keyboard. From there, the attacker can issue arbitrary commands with the full privileges of the logged-in user.

Researchers have confirmed that the shell will execute *any* command typed into it, including commands that delete files, install software, and modify system configuration. In some cases, the shell has been observed executing commands **the user typed themselves**.

## Proof of concept

We are releasing a working proof of concept below. It is fully weaponized. Click inside and start typing. Try `help`.

The page you are reading now has a shell in it. Close the tab if you are concerned.

## Exploitation steps

1. Open a terminal.
2. There is no step 2.

Exploitation requires local access, a working keyboard, and the ability to locate the Terminal application. Threat intelligence indicates all three are widely available to attackers.

## Affected systems

| Product | Vector | Status |
| --- | --- | --- |
| macOS (all versions) | Terminal.app, iTerm2, Ghostty, Warp | VULNERABLE |
| Linux (all distributions) | gnome-terminal, Konsole, xterm, Ctrl+Alt+F2 | VULNERABLE |
| Windows | cmd.exe, PowerShell, Windows Terminal, WSL | VULNERABLE |
| FreeBSD / OpenBSD | Literally the default experience | VULNERABLE |
| DEC VT100 (1978) | Physical serial cable | VULNERABLE |
| Your router | SSH, telnet, the little console port on the back | VULNERABLE |
| VS Code | Ctrl+` (one keystroke!) | VULNERABLE |
| Microsoft Paint | None known | Not affected |

## Indicators of compromise

If you see any of the following characters followed by a blinking cursor, your system is actively compromised:

A `#` prompt indicates the attacker has obtained **root**. Disconnect from the network, then from society.

## Mitigations

No vendor patch is available. Until one is released, we recommend the following compensating controls:

### Do not open terminals

This is the most effective mitigation. Note that many developers report opening terminals "for work," which security teams should treat as a red flag.

### Close terminals immediately after opening them

Partial mitigation only. Reopening the terminal reintroduces the vulnerability.

### Type slower

Reduces commands per minute and therefore attack throughput.

### Remove the keyboard

Effective, but the on-screen keyboard is a known bypass.

### Set `SHELL=/bin/false`

Fully remediates the issue. Also fully remediates your ability to use the computer.

## Disclosure timeline

## FAQ

If you own a computer, yes. If you own a phone, you are affected but have not found the terminal yet.

Yes. Telemetry shows millions of developers exploiting Terminal2Shell every day, often dozens of times per hour. Some have set it to open automatically on login.

Only if they know the user's password. Unfortunately, in the most common attack scenario, the attacker is the user.

Every serious vulnerability needs a logo, a domain, and a name ending in a number followed by a noun. This one has all three, so it must be serious.

Directly. We reviewed the public proof-of-concept for every *2Shell vulnerability we could find, and nearly all of them begin the same way: the researcher opens a terminal and types a command. Every one of those exploits depends on Terminal2Shell. It is the vulnerability underneath the vulnerabilities, and the only one that comes with a free shell before the attack even starts.

Fixing Terminal2Shell would neutralize most of the *2Shell family overnight. It would also stop the researchers from writing their next blog post, which is why no vendor will touch it.

Yes. Panicking is the recommended response to any vulnerability with a website. Please share this page with your CISO, your mother, and at least three news outlets.
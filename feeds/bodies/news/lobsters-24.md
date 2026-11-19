Introducing *sysdeck*, a command center for Linux and the BSDs that searches
applications, files, the clipboard history and more from a single hotkey, and
that only runs when you call it.

In August I started working on a tool that I had been missing on my Linux
desktop for a while, and for which I tried to build a somewhat glued-together
mess of scripts that used [bemenu](https://github.com/cloudef/bemenu) to do what I wanted. At some point, though, I
figured that I should probably try to put together an actual program, ideally
using Zig and GTK.

I wanted something that, just like bemenu (or rofi, or wofi, or whatnot), is
basically a single popup that I can open with a hotkey and type a few letters
into, to start an application, find a file, paste something I copied an hour
ago, or convert a currency without opening a browser. Now, roughly three months
later, I think I got it to a point where it’s worth publishing for others to
try. It’s called *sysdeck*, and the way I describe it is *the less bloated
Linux/BSD equivalent of Raycast on macOS*.

Yes, I’m aware that the title of this post is clickbait. *sysdeck* isn’t a port
of [Raycast](https://www.raycast.com), it doesn’t share a single line of code with it, and it
doesn’t come with an extension store or a subscription plan. However, Raycast is
the name that probably most people know for this kind of tool, and considering
that you’re here, reading this post, the title has obviously done its job. :-)

## Overview

*sysdeck* is supposed to be bound to a hotkey in your window manager. When you
press it, a window appears in which you start typing, and *sysdeck* shows the
matching entries from your applications, command-line executables, files and
folders, browser bookmarks, clipboard history, open Sway windows, SSH hosts,
Podman containers, text snippets and emoji. *Return* acts on the selected entry
depending on its kind, meaning it launches an application, opens a file or
copies a clipboard entry back. Holding *Alt* opens a context menu with further
actions. Selected images are shown along with their EXIF data, and executables
show their manual page underneath the list unless the `man` extension is
disabled in the config.

Besides searching, *sysdeck* calculates and converts units and currencies using
the library behind [`whats`](https://xn--gckvb8fzb.com/whats-1-21-gigawatts-in-watts/). It also controls running media players
via MPRIS, connects and disconnects NetworkManager connections, and takes
screenshots of a region, a window or the whole screen. If you configure a
Gemini, OpenAI or Anthropic model, or any OpenAI-compatible server, it also
sends your questions to an LLM. It keeps track of what you pick and ranks its
suggestions accordingly so that it can show you recommendations that matter to
your personal workflow.

Oh, and its `--dmenu` mode can replace `dmenu` in scripts, just like a single
line in your Sway configuration lets it replace clipboard managers like
`cliphist`.

What I’d like *sysdeck* to become is the one *command center* from which you
start, find and control everything on a Linux or BSD desktop, instead of the
collection of single-purpose tools and scripts that a typical tiling window
manager setup combines for launching programs, managing the clipboard, picking
emoji and taking screenshots. As mentioned before, *sysdeck* is written in Zig,
uses GTK4 for its interface and keeps its indexes in SQLite.

## On demand

One part of *sysdeck*’s design that differs from most launchers that come with
more advanced features is that *sysdeck* doesn’t use a background service. This
is deliberate and will stay that way for the foreseeable future.

Raycast, for example, keeps running at all times, so that its window can appear
the instant you press the hotkey. *sysdeck*, however, only runs when you ask for
it. Every press of the hotkey starts a new process that shows the window, does
what you asked it to do, and exits as soon as you pick an entry, press *Escape*
or switch to another window. Whenever one of its indexes is older than its
configured maximum age, *sysdeck* rebuilds it on a separate thread while the
window is open, and searches the existing index in the meantime.

Similarly, even the clipboard history works without a resident process of its
own, because `wl-paste` starts a lightweight *sysdeck* process (that only loads
the absolute necessary bits) for every copy. That run records the entry and
exits again, all within 10 to 20 milliseconds. The price for all of this is a
start time of about a tenth of a second on my machine, most of which GTK spends
on building and presenting the window. In my opinion this *“slight delay”* is a
fair trade over running a background service, because RAM has become expensive
and hard to get, as I’ve outlined in my posts on
[holding on to your hardware](https://xn--gckvb8fzb.com/hold-on-to-your-hardware/) and on
[dealing with faulty RAM](https://xn--gckvb8fzb.com/hold-on-to-your-hardware-badram/), and I believe that a program that is on
screen for only a few seconds at a time shouldn’t occupy memory and eat up CPU
cycles for the rest of the day.

## What it looks like

### Conversions

*sysdeck* uses the [`whats`](https://tty.fail/mrus/whats) library for conversions and can convert
various units and currencies.

![](https://xn--gckvb8fzb.com/sysdeck-raycast-for-linux-bsd/images/sysdeck02.gif)

### Web search

You can configure custom web search engines and search them directly from
*sysdeck*, which then opens your default browser with the results.

![](https://xn--gckvb8fzb.com/sysdeck-raycast-for-linux-bsd/images/sysdeck03.gif)

### Disk search

*sysdeck* can be configured to index specific folders and include their contents
in its search results. In disk mode it shows only those items.

![](https://xn--gckvb8fzb.com/sysdeck-raycast-for-linux-bsd/images/sysdeck04.gif)

### Media controls

Using MPRIS, *sysdeck* can control media players and trigger actions such as
play, pause, skip the current track or go back to the previous one, and it can
also show what is currently playing from within its UI.

![](https://xn--gckvb8fzb.com/sysdeck-raycast-for-linux-bsd/images/sysdeck05.gif)

### Emoji

*sysdeck* builds an index of all available emoji and lets you search for
individual ones using keywords that make sense, so that you find the one you’re
looking for, which it then copies to your clipboard on *Return*.

![](https://xn--gckvb8fzb.com/sysdeck-raycast-for-linux-bsd/images/sysdeck06.gif)

### Containers

Podman containers can be started and stopped from within *sysdeck*, which also
shows the current status of each individual container.

![](https://xn--gckvb8fzb.com/sysdeck-raycast-for-linux-bsd/images/sysdeck07.gif)

## Get it

Anyway, *sysdeck* is open source under the [SEGV License](https://xn--gckvb8fzb.com/segv/) and its primary
repository is on [tty.fail](https://tty.fail/mrus/sysdeck), with a [mirror on GitHub](https://github.com/mrusme/sysdeck) that also
publishes pre-built binaries. The [latest release](https://github.com/mrusme/sysdeck/releases/latest) includes builds for
Linux on `x86_64`, `aarch64`, `riscv64`, `powerpc64le` and `s390x`, each for
glibc as well as musl, a musl build for `loongarch64`, and `x86_64` builds for
FreeBSD, NetBSD and OpenBSD. The binaries use your system’s GTK4 libraries. If
you’d rather build *sysdeck* yourself, the README lists the packages you need on
each of these systems.

If a keyboard-driven command center that only runs when you need it sounds like
your kind of thing, give *sysdeck* a try, and let me know how it works for you
in the [community channel](https://xn--gckvb8fzb.com/contact/#xmpp).
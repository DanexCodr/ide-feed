It’s been two years since [my initial post](https://blogs.gnome.org/adrianvovk/2024/10/25/a-desktop-for-all/https://blogs.gnome.org/adrianvovk/2024/10/25/a-desktop-for-all/) about making GNOME OS an end-user general purpose OS. Today, we’re excited to announce that we’ve hit a major milestone!

TL;DR: We’re launching a new edition called “GNOME OS Preview”, which is built from the latest stable GNOME release. This means that GNOME OS is no longer *just* a nightly OS for GNOME developers and testers!

## The Road to Stable

Even though GNOME OS has been usable on real hardware for a few years now, its appeal was limited. We’ve only had the Nightly edition, which is constantly rebuilt to ship the latest git commit of every GNOME component (and a few others, like systemd and Flatpak). This form of GNOME OS is extremely useful, since GNOME developers and designers can daily-drive it to test the latest changes. However, it’s not something we’d recommend to non-developers.

Over the past year, we’ve seen a lot of adoption of GNOME OS Nightly amongst GNOME developers, especially following the success of last year’s [Summer of GNOME OS](https://blogs.gnome.org/tbernard/2025/06/01/summer-of-gnome-os/) challenge. This has led to a significant uptick in contributions and initiatives aimed at improving user and developer experience. For instance:

- Thanks to Jonas Dreßler’s, Valentin David’s, and Sebastian Wick’s zswap enablement efforts, GNOME OS now handles devices with limited amounts of RAM without OOM stalls. Jonas also found a hack that lets GNOME OS dynamically grow the usable on-disk swap space on-demand, which makes zswap perform significantly better than usual.
- The recently released Test Center app allows you to install CI builds of Flatpak apps from a merge request, making it super easy to test experimental changes before they are even merged. On GNOME OS Nightly, Test Center can do the same with system components by applying them as a system extension.
- Jordan Petridis’s new Toolpak project aims to provide a clean solution for distributing and installing command-line applications that developers need in a cross-distro fashion, similarly to how Flatpak and Flathub work for graphical apps.

Of course, long-term our goal is an OS for the broader public. We’re working on this across a number of different fronts, including:

- Enablement for systemd-homed across the stack, allowing for stronger per-user disk encryption and other benefits.
- Experimental work in the kernel to solve a bunch of limitations we’ve run into with filesystems. Ada Magicat went on a deep dive on her recent All Systems Go talk!
- Deep integration between systemd-homed and the session’s keyring, to increase security of the session’s lock screen. Dhanuka Warusadura gave a lightning talk at All Systems Go about his work on this.
- A new feature-complete installer, to replace the current placeholder installer. Julian Sparber also gave a talk about this at All Systems Go, with a live demo!
- Support for delta updates in systemd-sysupdate, to avoid downloading a full 2 GB image every time.
- Better integration with the TPM, including a graphical TPM recovery UI. Currently, trying to type a TPM recovery key into Plymouth is rather difficult.
- Improved support for ARM hardware, including some specific models of phones. Abderrahim Kitouni gave a lightning talk at GUADEC this year about the current installation process.
- Shipping our pre-installed apps as Flatpaks, and reworking the app release process to unify the build definitions between GNOME OS, the GNOME Nightly Apps Flatpak repo, and Flathub.
- An STF project focused on Flatpak and Portals, which will enable broader app support on GNOME OS (like VPNs!). You can learn more from the announcement blog post.

Some of these areas require lots more work before they’re ready for prime time, and even once they’re ready it’s not clear that it’ll be possible to migrate existing GNOME OS installations to use these new features. At [FOSDEM this year](https://blogs.gnome.org/adrianvovk/2026/02/18/gnome-os-hackfest-fosdem-2026/), we discussed this issue and decided that we won’t declare GNOME OS as “stable” until we can confidently commit to maintaining a clear long-term upgrade path for existing installations.

However, we also don’t think that all these things need to be in place before GNOME OS can be used by more people than it is today. It’s *not* ready for the masses yet, but it is ready for early adopters that aren’t quite adventerous enough to run a nightly OS.

## Introducing GNOME OS Preview

GNOME OS Preview is the current GNOME OS Nightly, but without the “nightly” aspect. Instead, it’s built from the latest stable GNOME release (GNOME 51.1, at the time of writing). GNOME OS Preview lives in the same branches on [GitLab](https://gitlab.gnome.org/GNOME/gnome-build-meta) as the stable `org.gnome.Platform` Flatpak runtimes.

GNOME OS Preview is only a few weeks old, so it has only seen limited real-life testing so far. We therefore expect people will uncover some issues initially. That said, Preview is significantly more stable than Nightly, which dozens of people have been daily driving without major issues for over a year. Thus, we’re feeling confident that Preview is going to be reliable enough for daily use by non-developer enthusiasts.

In all likelihood, GNOME OS Preview will be with us for a few years. However, **we are explicitly not promising updates in perpetuity**. If you’re not OK with re-installing your OS in a few years to switch to GNOME OS Stable, this is not for you yet. But if you’ve already been curious about giving GNOME OS a try, this is the moment!

GNOME OS Preview is available for download on the newly-refreshed [os.gnome.org](https://os.gnome.org)! GNOME OS Nightly is still available from there too. As always, you can reach us on Matrix at [#gnome-os:gnome.org](https://matrix.to/#/#gnome-os:gnome.org) or via the [`gnome-os` tag on Discourse](https://discourse.gnome.org/tag/gnome-os)
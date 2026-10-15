Plasma 6.8 is released on a very special day: KDE’s 30th birthday. Today we celebrate three decades of the KDE community providing the world’s greatest free and open-source software.

Plasma 6.8 is no exception, offering enhancements across much of the user experience and beneath the surface.

6.8 is all about launching Plasma into the future: adding changes you’ll notice right away, combined with major but subtle improvements designed to set the stage for decades of service to come.

Dive in and find out what the desktop environment of tomorrow looks like!

![Thumbnail for the KDE documentary](https://kde.org/announcements/plasma/6/6.8.0/03-documentary.webp)

Part of our continued effort to bring digital control to everyone, a new “dwell clicker” feature can send a mouse click when the pointer stops moving. Designed especially for users with mobility issues, an external app is no longer required to use your system in this way; now it’s built right in!

Plasma 6.8 gains support for the [Bikram Sambat](https://en.wikipedia.org/wiki/Vikram_Samvat) calendar in the Digital Clock, and the [Amharic](https://en.wikipedia.org/wiki/Amharic) language in the on-screen keyboard. These are just two more additions of the dozens incorporated into Plasma over recent versions in our effort to make Plasma a truly universal desktop.

Gain an extreme level of control over your system with Plasma’s System Monitor. In Plasma 6.8, you can assign compute-intensive tasks to only the CPUs of your choosing from directly within the monitor, and keep your machine running smoothly.

![System Monitor app offering the possibility to change the CPU affinity for the plasmashell process](https://kde.org/announcements/plasma/6/6.8.0/20-systemmonitor-affinity.webp)

You can also monitor your VRAM more easily, as it now shows the load as an easy-to-read percentage.

### Remote desktop

We’ve invested a great deal of time into polishing the experience provided by Plasma’s built-in remote desktop server. In Plasma 6.8, you’ll be able to enjoy the following improvements — with more in the pipeline:

These features will only take effect in remote desktop client apps that support them.

![Plasma’s Remote Desktop settings and the KRDC application in use](https://kde.org/announcements/plasma/6/6.8.0/23-rdp.webp)

Spectacle can now optionally include both system audio and microphone input in its screen recordings, making it possible to narrate a recording or accurately record everything that’s going on.

Plasma’s screen sharing portal dialog lets you create a virtual screen to share, instead of an existing display. In Plasma 6.8, you can now specify the resolution of the virtual screen instead of being limited to only 1920 × 1080.

![The screen sharing portal window showing the ability to select a custom resolution for the virtual display](https://kde.org/announcements/plasma/6/6.8.0/25-screencast-portal-resolution.webp)

In addition, the quality of screen recordings and screencasts has been improved.

We’ve added support for window rules that add desktop shadows, outlines, and rounded corners to client-side-decorated windows that can’t provide these visual niceties themselves. Plasma 6.8 ships with one such rule for Steam, making it feel more at home in Plasma.

![](https://kde.org/announcements/plasma/6/6.8.0/30-steam-shadow-frame-before.webp)

*Before*

We’ve added new global shortcuts to help power users manage their open windows with the Task Manager widget. By pressing <kbd>Meta</kbd> + <kbd>Ctrl</kbd> + <kbd>Page Up</kbd> or <kbd>Page Down</kbd>, you can cycle between the previous and next tasks. By also holding <kbd>Shift</kbd>, you can move the active task backwards and forwards.

### Theming

Four months ago, Plasma 6.7 included an alpha release of the new Union theming system, demonstrating its ability to style Qt Quick applications.

Plasma 6.8 builds on this with a beta release of Union, including not only refinements for Qt Quick theming, but also the ability to style Qt Widgets applications! This includes KDE’s more traditional desktop applications, such as Dolphin, Kate, and Konsole.

While Union is not quite ready to be used by default, Plasma 6.8 brings it ever closer to being a single source of truth for styling all of KDE’s products, and more. To learn more about the current state of Union, read the blog posts from [Arjen](https://quantumproductions.info/articles/2026-08/union-summer-2026-update) and [Akseli](https://akselmo.dev/posts/union-qtwidgets/).

To try Union, ensure the `union` package is installed (name may differ depending on your distribution), apply “Breeze (Union)” in *System Settings* → *Colors & Themes* → *Application Style*, then restart your apps or the system.

Apps are expected to look nearly identical to how they do with the traditional Breeze theme. If you’ve found a Union-specific issue, [please report it](https://bugs.kde.org/enter_bug.cgi?product=Union).

If you’re interested in experimenting with creating your own Union style, you can find out more [in Union’s documentation](https://api.kde.org/working-with-styles.html).

### Wayland

30 years is an impressive milestone for a community like KDE. But even older is the venerable [X Window System](https://en.wikipedia.org/wiki/X_Window_System) (or “X11”), first released in 1984! After 42 years of faithful service, support for starting X11 sessions in Plasma is being retired, in conjunction with full adoption of the newer [Wayland](https://en.wikipedia.org/wiki/Wayland_%28protocol%29) system.

Compared to X11, Wayland offers better support for modern screens and graphics cards, and is actively developed.

The small number of individual apps that still require X11 will continue to work via the “XWayland” compatibility layer.

KDE applications will continue to support X11 for the foreseeable future.

As part of the backend improvements included in Plasma 6.8, we’ve made changes to help Plasma load faster and use less memory. Discover’s update notifier now uses less memory, too.

With KWin, NVIDIA GPUs now use triple buffering by default, and all users will have better-looking HDR when using an ICC color profile. We’ve also added support for the HLG transfer function, which means that certain media and applications that did not previously work in HDR are now working as expected.

Plasma 6.8 is chock-full of smaller changes, including:

To see a high-level overview of all user-facing changes, [see the Plasma 6.8 wiki page](https://community.kde.org/Plasma/Plasma_6#Plasma_6.8).

To see the full list of *all* changes, read the [complete changelog](https://kde.org/announcements/changelogs/plasma/6/6.7.5-6.8.0/).

## Live Images

The easiest way to try it out is with a live image booted off a USB disk. Docker images also provide a quick and easy way to test Plasma.

Distributions have created, or are in the process of creating, packages listed on our wiki page.

Note that packages of this release might not be available on all distributions at the time of this announcement.

You can install Plasma directly from source.

## Feedback

You can give us feedback and get updates on our social media channels:

Discuss KDE on the [KDE Forums](https://discuss.kde.org/).

You can provide feedback direct to the developers via the [#Plasma Matrix channel](https://go.kde.org/matrix/#/%23plasma:kde.org), [Plasma-devel mailing list](https://mail.kde.org/mailman/listinfo/plasma-devel) or report issues via [Bugzilla](https://bugs.kde.org/enter_bug.cgi?product=plasmashell&amp;format=guided). If you like what the team is doing, please let them know!

Your feedback is greatly appreciated.

## Supporting KDE

KDE is a [Free Software](https://www.gnu.org/philosophy/free-sw.html) community that exists and grows only because of the help of many volunteers that donate their time and effort. KDE is always looking for new volunteers and contributions, whether it is help with coding, bug fixing or reporting, writing documentation, translations, promotion, money, etc. All contributions are gratefully appreciated and eagerly accepted. Please read through the [Supporting KDE page](https://kde.org/community/donations/) for further information or become a KDE e.V. supporting member through our [Join the Game](https://kde.org/community/donations/) initiative.

KDE is an international technology team that creates free and open source software for desktop and portable computing. Among KDE’s products are a modern desktop system for Linux and UNIX platforms, comprehensive office productivity and groupware suites and hundreds of software titles in many categories including Internet and web applications, multimedia, entertainment, educational, graphics and software development. KDE software is translated into more than 60 languages and is built with ease of use and modern accessibility principles in mind. KDE’s full-featured applications run natively on Linux, BSD, Windows, Haiku, and macOS.

*Trademark Notices.*  

KDE<sup>®</sup> and the K Desktop Environment<sup>®</sup> logo are registered trademarks of KDE e.V..  
Linux is a registered trademark of Linus Torvalds. UNIX is a registered trademark of The Open Group in the United States and other countries.  
All other trademarks and copyrights referred to in this announcement are the property of their respective owners.
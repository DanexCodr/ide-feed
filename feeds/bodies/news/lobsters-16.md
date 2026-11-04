Download 11.1 from our CDN:
[amd64 USB](https://cdn.NetBSD.org/pub/NetBSD/NetBSD-11.1/images/NetBSD-11.1-amd64-install.img.gz),
[amd64 DVD](https://cdn.NetBSD.org/pub/NetBSD/NetBSD-11.1/images/NetBSD-11.1-amd64-dvd.iso),
[i386 USB](https://cdn.NetBSD.org/pub/NetBSD/NetBSD-11.1/images/NetBSD-11.1-i386-install.img.gz),
[i386 CD-ROM](https://cdn.NetBSD.org/pub/NetBSD/NetBSD-11.1/images/NetBSD-11.1-i386.iso),
[sparc64 DVD](https://cdn.NetBSD.org/pub/NetBSD/NetBSD-11.1/images/NetBSD-11.1-sparc64-dvd.iso),
[sparc64 CD-ROM](https://cdn.NetBSD.org/pub/NetBSD/NetBSD-11.1/images/NetBSD-11.1-sparc64.iso),
[macppc CD-ROM](https://cdn.NetBSD.org/pub/NetBSD/NetBSD-11.1/images/NetBSD-11.1-macppc.iso),
[RISC-V devices](https://cdn.NetBSD.org/pub/NetBSD/NetBSD-11.1/riscv-riscv64/binary/gzimg/riscv64.img.gz),
[Cavium Octeon MIPS devices](https://cdn.NetBSD.org/pub/NetBSD/NetBSD-11.1/evbmips-mips64eb/binary/gzimg/octeon.img.gz),
[Nintendo Wii](https://cdn.NetBSD.org/pub/NetBSD/NetBSD-11.1/evbppc/binary/gzimg/wii.img.gz),
[various Arm devices](https://armbsd.org/),
[full release dir with everything else](https://cdn.NetBSD.org/pub/NetBSD/NetBSD-11.1/).

[Hashes](https://cdn.NetBSD.org/pub/NetBSD/security/hashes/NetBSD-11.1_hashes.asc),
signed with the [NetBSD Security Officer's PGP key](https://cdn.NetBSD.org/pub/NetBSD/security/PGP/security-officer@netbsd.org.asc), of all files in the distribution.

## Introduction

The NetBSD Project is pleased to announce NetBSD 11.1, the first point release of the NetBSD 11 stable branch.

## Upgrade instructions

An existing installation can be upgraded by booting an installation image
and selecting the Upgrade option.

If you are using other update methods, update the kernel and modules *first*, then reboot and update your userspace.

## Changes since NetBSD 11.0

This release primarily focuses on security and bug fixes, since our aim
was to get it released as soon as possible to address certain security
issues.

## Ports

- alpha: Fixed a boot hang occurring on unpatched QEMU.
- alpha: Fixed kernel stack pointer alignment leading to panics during test suite runs. (PR 60865)
- amd64, i386: Reduced the strictness of the "WARNING: no TOD clock present" check.
- amd64, i386: Fixed a panic on the Zhaoxin KX-7000 and other late-model CPUs from VIA/Zhaoxin.
- amd64: Fixed libc behaviour when calling memchr(3) with certain unusual arguments. (PR 60744)
- atari: Fixed ATARITT kernels failing to boot on Atari TT030.
- evbarm: Fixed stability problems with certain USB devices on Raspberry Pi.
- evbarm: Fixed thread local storage on ARMv5 with soft floats. (PR 57638)
- evbarm: Fixed "am335x omaptimer fails to attach". (PR 60910)
- hppa: Added support for eager FPU switching. Currently enabled only for QEMU to work around an emulation bug, may eventually become the default for improved safety.
- mac68k: Honour requested keyboard bell volume for akbd(4) devices. (PR 60691)
- mips: Fixed problems with MIPS Malta platform code found running under QEMU.
- mips: Fixed various problems discovered with the Kernel Undefined Behaviour Sanitizer. (PR 60780)
- sparc64: Enhanced support for sensors on Sun Ultra 25/45 and Sun Fire V215/V245, including front panel temperatures, fan speeds, and disk presence indicators. LEDs on Sun Fire machines can now be controlled via sysctl.
- sparc64: Added support for the i2c controller found in Pyro-based machines (e.g. Sun Ultra 45, Sun Fire V245).
- sparc64: Added support for the real-time clock used in the Sun Ultra 45.
- sun68k: Fixed booting from SCSI disks with certain PROM revisions.

## Kernel and MI device drivers

- ffs: Fixed an uvm_fault occurring during snapshot dump/restore. (PR 59663)
- ipfilter: Fixed a NULL pointer dereference leading to potential DoS while parsing ICMP6 packets. (PR 60484)
- net: Fixed an off-by-error in a bounds check in bsd_decompress().
- uvm: Fixed a race condition in the page daemon.
- vfs: Limit snapshot-related vflushbuf: dirty: vnode [...] console spew under heavy load.
- acpibat(4): Added support for battery monitoring on the Microsoft Surface Go 3.
- hdaudio(4): Apply access checks to configuration operations on /dev/hdaudioX. (PR 60492)
- ixl(4): Fixed driver hang, then failure on ifconfig, if SFP module present at boot time and media connected. (PR 60736)
- mpii(4): Fixed stability of Symbios Logic SAS3008 RAID controllers. (PR 58684)
- raid(4): Fixed an incorrect assertion during reconstruction. (PR 60477)
- run(4), rum(4), various other USB Wi-Fi drivers: Fixed a kernel panic seen when hotplugging a device with wpa_supplicant(8) running. (PR 60665)
- virtio(4): Improve documentation.
- vr(4): Fixed stability problems observed after warm reboots. (PR 60848)
- wdc(4): Avoid a three-second delay during boot with PCI IDE controllers.
- compat_linux(8): Fixed an edge-case panic in Linux’s copy_file_range system call.

## Userspace and build system

- build.sh: Fixed building certain legacy GPLv2 GNU tools with modern compilers; used for GCC compiler bootstrapping.
- build.sh: Fixed building with MKBINUTILS=no set.
- build.sh: Fixed cross-builds from MacOS on Apple Silicon. (PR 60904)
- build.sh: Fixed parallel builds of debug data.
- build.sh: Generate hashes for bootable images in the gzimg directory. (PR 59195, PR 60302)
- libc: Fixed issues with printf(3) thousands separators and positional arguments. (PR 60708, PR 60496)
- ld.elf_so(1): Fixed incorrect thread-local storage alignment assertions with DEBUG enabled.
- wgetscrreg(3): Added a manual page.
- httpd(8): Clarified documentation of CGI options.
- syslogd(8): Fixed buffering of incomplete lines from /dev/klog.

## Third-party components

- brotli: Sync with -current to fix CVE 2026-111497.
- libXfont2: Updated to 2.0.9, fixes CVE-2026-44950 and CVE-2026-59679.
- libX11: Updated to 1.8.14.
- libXi: Updated to 1.8.4.
- libXpm: Updated to 3.5.20.
- libXrender: Updated to 1.9.13.
- libXtst: Updated to 1.2.6.
- mozilla-rootcerts: Update for compromised certificate authorities. (PR 60908)
- xf86-video-intel: Sync version with pkgsrc.
- Xorg(1): Updated to xorg-server 21.1.25.
- ssh(1), sshd(8): Updated to OpenSSH 10.6.
- unbound(8): Updated to 1.26.1.

The complete list of changes can be found in the 
  [CHANGES](https://cdn.NetBSD.org/pub/NetBSD/NetBSD-11.1/CHANGES)
  and [CHANGES-11.1](https://cdn.NetBSD.org/pub/NetBSD/NetBSD-11.1/CHANGES-11.1) files in the top level directory of the NetBSD 11.1
  release tree.

## Getting NetBSD 11.1

Complete source and binaries for NetBSD 11.1 are available for download
  at many sites around the world. You can download NetBSD 11.1 from our
  [main CDN](https://cdn.NetBSD.org/pub/NetBSD/NetBSD-11.1/),
  or use a
  [mirror site](https://www.NetBSD.org/mirrors/)
  close to you.
  A list of hashes, signed by the
  [NetBSD Security Officer's PGP key](https://cdn.NetBSD.org/pub/NetBSD/security/PGP/security-officer@netbsd.org.asc), is
  available for the NetBSD 11.1 distribution in
  [this file](https://cdn.NetBSD.org/pub/NetBSD/security/hashes/NetBSD-11.1_hashes.asc).

NetBSD is free. All of the code is under non-restrictive licenses,
    and may be used without paying royalties to anyone. Free support
    services are available via our mailing lists and website.  Commercial
    support is available from a variety of sources.  More extensive
    information on NetBSD is available from our website:

> [www.NetBSD.org](https://www.NetBSD.org/)

## System families supported by NetBSD 11.1

The NetBSD 11.1 release provides supported binary distributions for
    the following systems:

| [NetBSD/aarch64](https://wiki.NetBSD.org/ports/aarch64/) | Arm 64-bit |
| --- | --- |
| [NetBSD/acorn32](https://wiki.NetBSD.org/ports/acorn32/) | Acorn RiscPC/A7000, VLSI RC7500 |
| [NetBSD/algor](https://wiki.NetBSD.org/ports/algor/) | Algorithmics, Ltd. MIPS evaluation boards |
| [NetBSD/alpha](https://wiki.NetBSD.org/ports/alpha/) | Digital/Compaq Alpha (64-bit) |
| [NetBSD/amd64](https://wiki.NetBSD.org/ports/amd64/) | AMD family processors like Opteron, Athlon64, and Intel CPUs with EM64T extension |
| [NetBSD/amiga](https://wiki.NetBSD.org/ports/amiga/) | Commodore Amiga and MacroSystem DraCo |
| [NetBSD/amigappc](https://wiki.NetBSD.org/ports/amigappc/) | PowerPC-based Amiga boards. |
| [NetBSD/arc](https://wiki.NetBSD.org/ports/arc/) | MIPS-based machines following the Advanced RISC Computing spec |
| [NetBSD/atari](https://wiki.NetBSD.org/ports/atari/) | Atari TT030, Falcon, Hades |
| [NetBSD/bebox](https://wiki.NetBSD.org/ports/bebox/) | Be Inc's BeBox |
| [NetBSD/cats](https://wiki.NetBSD.org/ports/cats/) | Chalice Technology's CATS and Intel's EBSA-285 evaluation boards |
| [NetBSD/cesfic](https://wiki.NetBSD.org/ports/cesfic/) | CES FIC8234 VME processor board |
| [NetBSD/cobalt](https://wiki.NetBSD.org/ports/cobalt/) | Cobalt Networks' MIPS-based Microservers |
| [NetBSD/dreamcast](https://wiki.NetBSD.org/ports/dreamcast/) | Sega Dreamcast game console |
| [NetBSD/emips](https://wiki.NetBSD.org/ports/emips/) | The Extensible MIPS architecture from Microsoft Research |
| [NetBSD/epoc32](https://wiki.NetBSD.org/ports/epoc32/) | Psion EPOC PDAs |
| [NetBSD/evbarm](https://wiki.NetBSD.org/ports/evbarm/) | Various Arm-based evaluation boards and appliances |
| [NetBSD/evbmips](https://wiki.NetBSD.org/ports/evbmips/) | Various MIPS-based evaluation boards and appliances |
| [NetBSD/evbppc](https://wiki.NetBSD.org/ports/evbppc/) | Various PowerPC-based evaluation boards and appliances |
| [NetBSD/evbsh3](https://wiki.NetBSD.org/ports/evbsh3/) | Various Hitachi Super-H SH3 and SH4-based evaluation boards and appliances |
| [NetBSD/ews4800mips](https://wiki.NetBSD.org/ports/ews4800mips/) | NEC's MIPS-based EWS4800 workstation |
| [NetBSD/hp300](https://wiki.NetBSD.org/ports/hp300/) | Hewlett-Packard 9000/300 and 400 series |
| [NetBSD/hpcarm](https://wiki.NetBSD.org/ports/hpcarm/) | StrongArm based Windows CE PDA machines |
| [NetBSD/hpcmips](https://wiki.NetBSD.org/ports/hpcmips/) | MIPS-based Windows CE PDA machines |
| [NetBSD/hpcsh](https://wiki.NetBSD.org/ports/hpcsh/) | Hitachi Super-H based Windows CE PDA machines |
| [NetBSD/hppa](https://wiki.NetBSD.org/ports/hppa/) | Hewlett-Packard 9000 Series 700 workstations |
| [NetBSD/i386](https://wiki.NetBSD.org/ports/i386/) | IBM PCs and PC clones with i486-family processors and up |
| [NetBSD/ibmnws](https://wiki.NetBSD.org/ports/ibmnws/) | IBM Network Station 1000 |
| [NetBSD/iyonix](https://wiki.NetBSD.org/ports/iyonix/) | Castle Technology's Iyonix Arm based PCs |
| [NetBSD/landisk](https://wiki.NetBSD.org/ports/landisk/) | SH4 processor based NAS appliances |
| [NetBSD/luna68k](https://wiki.NetBSD.org/ports/luna68k/) | OMRON Tateisi Electric's LUNA series |
| [NetBSD/mac68k](https://wiki.NetBSD.org/ports/mac68k/) | Apple Macintosh with Motorola 68k CPU |
| [NetBSD/macppc](https://wiki.NetBSD.org/ports/macppc/) | Apple PowerPC-based Macintosh and clones |
| [NetBSD/mipsco](https://wiki.NetBSD.org/ports/mipsco/) | MIPS Computer Systems Inc. family of workstations and servers |
| [NetBSD/mmeye](https://wiki.NetBSD.org/ports/mmeye/) | Brains mmEye multimedia server |
| [NetBSD/mvme68k](https://wiki.NetBSD.org/ports/mvme68k/) | Motorola MVME 68k Single Board Computers |
| [NetBSD/mvmeppc](https://wiki.NetBSD.org/ports/mvmeppc/) | Motorola PowerPC VME Single Board Computers |
| [NetBSD/netwinder](https://wiki.NetBSD.org/ports/netwinder/) | StrongArm based NetWinder machines |
| [NetBSD/news68k](https://wiki.NetBSD.org/ports/news68k/) | Sony's 68k-based “NET WORK STATION” series |
| [NetBSD/newsmips](https://wiki.NetBSD.org/ports/newsmips/) | Sony's MIPS-based “NET WORK STATION” series |
| [NetBSD/next68k](https://wiki.NetBSD.org/ports/next68k/) | NeXT 68k “black” hardware |
| [NetBSD/ofppc](https://wiki.NetBSD.org/ports/ofppc/) | OpenFirmware PowerPC machines |
| [NetBSD/pmax](https://wiki.NetBSD.org/ports/pmax/) | Digital MIPS-based DECstations and DECsystems |
| [NetBSD/prep](https://wiki.NetBSD.org/ports/prep/) | PReP (PowerPC Reference Platform) and CHRP machines |
| [NetBSD/riscv](https://wiki.NetBSD.org/ports/riscv/) | RISC-V-based devices |
| [NetBSD/rs6000](https://wiki.NetBSD.org/ports/rs6000/) | IBM RS/6000 MCA-based PowerPC machines. |
| [NetBSD/sandpoint](https://wiki.NetBSD.org/ports/sandpoint/) | Motorola Sandpoint reference platform, including many PPC-based NAS boxes |
| [NetBSD/sgimips](https://wiki.NetBSD.org/ports/sgimips/) | Silicon Graphics' MIPS-based workstations |
| [NetBSD/shark](https://wiki.NetBSD.org/ports/shark/) | Digital DNARD (“shark”) |
| [NetBSD/sparc](https://wiki.NetBSD.org/ports/sparc/) | Sun SPARC (32-bit) and UltraSPARC (in 32-bit mode) |
| [NetBSD/sparc64](https://wiki.NetBSD.org/ports/sparc64/) | Sun UltraSPARC (in native 64-bit mode) |
| [NetBSD/sun2](https://wiki.NetBSD.org/ports/sun2/) | Sun Microsystems Sun 2 machines with Motorola 68010 CPU |
| [NetBSD/sun3](https://wiki.NetBSD.org/ports/sun3/) | Motorola 68020 and 030 based Sun 3 and 3x machines |
| [NetBSD/vax](https://wiki.NetBSD.org/ports/vax/) | Digital VAX |
| [NetBSD/x68k](https://wiki.NetBSD.org/ports/x68k/) | Sharp X680x0 series |
| [NetBSD/xen](https://wiki.NetBSD.org/ports/xen/) | The Xen virtual machine monitor |
| [NetBSD/zaurus](https://wiki.NetBSD.org/ports/zaurus/) | Sharp Arm PDAs |

Ports included in the release but not fully supported or functional:

## Acknowledgments

The NetBSD Foundation would like to thank all those who have
    contributed code, hardware, documentation, funds, colocation for
    our servers, web pages and other documentation, release engineering,
    and other resources over the years. More information on the people who
    make NetBSD happen is available at:

## About NetBSD

NetBSD is a free, fast, secure, and highly portable Unix-like
  Open Source operating system. It is available for a wide range
  of platforms, from large-scale servers and powerful desktop
  systems to handheld and embedded devices. Its clean design
  and advanced features make it excellent for use in both
  production and research environments, and the source code is
  freely available under a business-friendly license. NetBSD is
  developed and supported by a large and vibrant international
  community.  Many applications are readily available through
  [pkgsrc,
  the NetBSD Packages Collection](https://pkgsrc.org).

## About the NetBSD Foundation

The [NetBSD Foundation](https://www.netbsd.org/foundation/) was
    chartered in 1995, with the task of overseeing core NetBSD project
    services, promoting the project within industry and the open
    source community, and holding intellectual property rights on much
    of the NetBSD code base. Day-to-day operations of the project are
    handled by volunteers.

As a non-profit organization with no commercial backing, the NetBSD
    Foundation depends on donations from its users, and we would like to ask
    you to consider [making a donation](https://www.netbsd.org/donations/)
    to the NetBSD Foundation in support of continuing production of our
    fine operating system. Your generous donation would be particularly
    welcome to help with ongoing upgrades and maintenance, as well as
    with operating expenses for the NetBSD Foundation.

Donations can be done via PayPal to
    `<paypal@NetBSD.org>`, or via Google Checkout and are fully
    tax-deductible in the US.  See [www.NetBSD.org/donations/](https://www.NetBSD.org/donations/#how-to-donate) for more information, or
    contact `<finance-exec@NetBSD.org>` directly.
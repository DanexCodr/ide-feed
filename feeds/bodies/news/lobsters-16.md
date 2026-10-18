I recently acquired a lightly-used HP Envy 17" laptop, model DA0013dx, and of course wanted to run
[OpenBSD](https://openbsd.org/) on it.
It came with Windows 11 on an internal NVME drive.
Booting OpenBSD from a USB device failed fast: it hung.
To get there, first of course I had to disable "secure boot" in the BIOS.
Then, the boot process hung part way through the device probe section of the boot process.
Familiar to BSD users since 1979, probing is where the OS tries every device it knows about and,
if the device responds appropriately, marks it active and prints a short message on the console.
Other OSes go through the same process, but the three mainstream OSes simply choose to hide it under a GUI.
Both Linux and macOS have a Unix-derived `dmesg` command which prints the messages that are hidden at boot.
On Windows, you have to into System Settings or some such to get hardware information.

So. On the HP Envy in question, the device probing stops after the iwx(4) (Intel AX211 WiFi) probe.
This implies that some device after the IWX in the probe sequence does something bad when trying its device.
How do we find out which device is at fault?

## Getting Past Device Probe Hangs

In the simplest case, you would use ddb(4) on a debug kernel:

- `boot -c bsd.gdb` This file is created as part of kernel building, so you may have to build your own kernel to get this.
- At config prompt, enter `ddb` to enter kernel debugger
- `write autoconf_verbose 1`
- `continue` # back to config
- `quit` # resume booting

This produces a massive stream of output, so fast that a normal video recorder at 24FPS will show
overlapping text that’s hard to read.
I did try several different kernels, and eventually got one to panic instead of hanging with no output.
With a bit of decrypting of a blurry video, I was able to read
the panic as `panic: cpu at apic id 0 already attached.`
A bit of cogitation led me to suspect a defective ACPI/AML implementation.
And that led me to the next giant leap: update the BIOS!
Sure enough, the machine was running a BIOS from 2024, the year the machine was first released.
First releases these days often being really beta releases, I went looking for an update.
A 2026 version was available, with numerous corrections, including the one that mattered.
Since I hadn’t been able to clobber the Windows load, updating the BIOS was no problem,
and the process ran smoothly.
Then, booting off an external drive over USB booted into OpenBSD with no problem!

The next step was to swap the NVME drives: take the OpenBSD 4TB from my older laptop and install it here,
keeping the Windows-loaded 1TB aside in case of future BIOS updates.
And yes, I remain paranoid enough to *remove the OpenBSD NVME when running MS-Windows*.
Better safe than sorry.

Here we run into two areas that differ from the Framework laptop this is replacing, and make little annoyances for servicing.
First, the screws holding the bottom of the HP’s case are not captive,
so you can lose them if not careful (I was, and didn’t).
Second, the screws holding the bottom of the case carry Torx heads, while the screws holding the
NVME itself use Philips (+) head. How hard would it have been for HP to make all the service screws
have the same head? Framework did this some years ago.
So maybe that’s a third: big companies should overcome their arrogance and look at what the
new kids on the block are doing.

After the first set of screws was removed, there came a mighty struggle to get the case bottom off.
It’s held in on all four sides with press-fit couplers all along each edge, so you have to pry like mad to remove it.
The base is plastic, btw, so it flexes, but it’s still annoying.
I guess you have to do that when making inexpensive plastic parts on an expensive laptop(?).

![hp envy17 insides](https://darwinsys.com/blog/images/hp-envy17-insides.jpg)

Finally, I got to swap in the OpenBSD NVME. Powered it up. Nothing! Just a moment of silence.
Oh shite! I thought. Have I busted something inside!?
Well, not so fast. Several minutes of doom-and-gloom later,
I was starting to get the external OpenBSD drive ready again, when I got a BIOS screen about the CMOS
being corrupt, is it OK to recompute? Of course it disappeared before I could read it all.
Rebooting again, I let it get back to this popup, accepted it, and, *mirabile dictu*,
the machine booted up completely.
Seems these machines often get upset when you change memory or hard drive,
and take some time and/or an OK click to settle down.

So, I now have the machine running -current with all my files from the older laptop.
Tada!

## About the Laptop

I’ve never had a 17" laptop before, so its size and weight are, well, different.
My lightweight laptop backpack, which fits my [Framework 13](https://frame.work), simply won’t zip up around it!
A larger backpack does, thankfully.

Reminder: we have two measures for any laptop, the screen diagonal and the actual physical width.
Bigger laptops cluster around 17" diagonal, but most have a base "only" 15" or 15.6" wide.
The former measure is used in advertising, e.g., "HP Envy-17", while the latter is used in sizing
a backpack or carrying sleeve.

The HP originally shipped with a 65W power supply (there’s a model with an extra graphics card that ships with 100W).
So of course it runs with the 65W power supply from my Framework 13, but every so often (when running Windows)
there was a notice that HP recommends using an HP power supply.

Note that there is a range of variations of the Envy 17, denoted by a string of characters and digits.
Some of the detail listed here is specific to the DA0013dx model which I have.
I got my Envy used, and it didn’t come with the official power supply, nor with the USB dock
that expands on its fixed set of ports (three USB-A, 2 USB-C/DP (one for power in), one HDMI,
and a 1/8" headphone jack).
Again, my Framework has a series of interchangeable ports, of which any 4 can be in use at ome time on the 13,
or more on Framework’s larger laptops; this is great if you need a particular cable on the left or the right).

The screen is bright and beautiful, and works "out of the box" with OpenBSD’s X Windows system.
This Envy model has a 1920x1024 display and can drive an external HDMI monitor to 4K via the HDMI port,
or a DisplayPort monitor on one of the USB-C ports.
The 1920x1024 is the 19:6 ratio that used on many monitors these days, but due to the
different sizes and resolutions, it takes quite some fiddling to update my XFCE4 layout just the way I wanted it.
Unlike many lesser laptops, this features a touchscreen, which does work with OpenBSD’s ism(4)
(trackpad and touchscreen) driver, with one important exception noted below.

Here’s a screenshot of my XFCE4 setup.

| ![xfce4 framework](https://darwinsys.com/blog/images/xfce4-framework.jpg) | ![xfce4 hp envy](https://darwinsys.com/blog/images/xfce4-hp-envy.png) |
| --- | --- |
| Framework (a while ago) | HP Envy-17 |

The CPU is a
[Intel® Core™ Ultra 7 155H, 4484.32 MHz](https://www.intel.com/content/www/us/en/products/sku/236847/intel-core-ultra-7-processor-155h-24m-cache-up-to-4-80-ghz/specifications.html).
We’ll just call it 4.5GHz, the maximum speed. This is a "Meteor Lake" CPU, with several types of cores
(6 Performance cores each with two threads,
8 Efficient cores, and
2 Low Power Efficient cores, for a total of 22 threads; shows as 22 CPUs in dmesg).
The Envy-17 is also available with the less expensive 120U CPU version.

This model ships with 16GB RAM but is available from HP configured with 32G.
It’s DDR-5 SODIMM memory, so you can in theory upgrade as much as you can afford.
Similarly, the Envy-17 is available configured with a 1 or 2 TB SSD;
I moved my 4GB NVME SSD from the Framework into the HP Envy, and it works fine.
My Framework may someday be reborn by installing a newer motherboard with more CPU power than the Envy I have
([https://Frame.work](https://Frame.work), as per their promise and their culture, continues to bring out upgrades for all their models).

## Minor nits:

The lid hinge is very stiff.

The keyboard seems a little off in terms of the row positions, but I guess that’s just down to whatever keyboard you’re used to.
And the fact that it’s wider than most.

The official Intel stickers beside the touchpad are about the size of SD cards and I keep wanting to brush them off.
Guess I’ll scrape them off when it gets too annoying.

There is an error in HP’s "AML",the ACPI Machine Language which tells the OS about the details of the hardware.
THis results in the error: `# AML PARSE ERROR (0x944): Undefined name: \_SB_.PC00.LPCB.MXTP`.
This is a failed attempt at providing the MaXimum TemPerature that the CPU can run it without damage.
In this case, `acpitz` driver doesn’t know the max temp.
I just set temp:high=90C in `/etc/sensorsd.conf`, a bit more conservative than the 100C that some laptops provide.

## All that remains

There remain some minor issues to work out.

- The AML problem mentioned above means that the ACPI doesn’t know the maximum temperature, so maybe the CPU will catch fire if I ask too much of it at a time. This is a likely "won’t fix".
- There’s a DRM warning message at boot time, due to "a call to a driver we don’t have" (jsg@). There were previously several other errors, but most were fixed in a recent (pre-8.0) commit.
- The driver for the Intel Wifi (AX210) gives a seemingly-harmless error at bootup:
- When there are two monitors, the touch screen behaves like x = k*x (k is 2 if they’re both the same width, otherwise YMMV). This seems to be a fundamental issue with X. Most of these should get resolved shortly. iwx0: timeout waiting for master
- sndio isn’t talking to the built-in speaker via audio device(s) properly; it works with usb headphones. I don’t care, because I don’t like annoying the people around me with sudden blasts of noise when some advertisement pops up.
- When there are two monitors, the mouse works correctly but the touch screen behaves like x = k*x (k is 2 if they’re both the same width, otherwise YMMV). This seesms to be a fundamental issue with X.

Most of these should get resolved eventually.

## Lessons learned:

- Carry many different screwdrivers.
- When in doubt, update your PC’s BIOS.
- Big computer companies: look around more.

## Last words

If you want a modern laptop with a 16:9 touchscreen display to run OpenBSD, the HP Envy is not a bad choice.

I recently acquired a lightly-used HP Envy 17" laptop, model DA0013dx, and of course wanted to run
[OpenBSD](https://openbsd.org/) on it.
It came with Windows 11 on an internal NVME drive.
Booting OpenBSD from a USB device failed fast: it hung.
To get there, first of course I had to disable "secure boot" in …
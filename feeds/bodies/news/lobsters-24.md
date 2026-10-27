I am going to tell the story of fixing a very high priority bug that was 15 years old. Arguably the worst KIO bug.

In September 2011, against KDE 4.7, someone opened [bug
281270](https://bugs.kde.org/show_bug.cgi?id=281270): "When copying files to a removable disk,
speed and progress reflect copying to the local cache not to the disk itself". The report notes
the copy notification showed about 50 MB/s to a USB 1.1 device, which cannot go faster than
12 Mbit/s. The reporter had asked a kernel developer, Alan Stern, what was going on, and summed up
his answer:

> it shows that the copying operation is finished when it has not even been started.

Seventy-seven comments and 17 duplicates later, that is still how a copy to a USB stick behaves in the
current release of KIO. My [last post
about copying](https://blogs.kde.org/2026/07/28/making-kio-copy-many-files-fast/) was about making KIO copy faster.
This one is about the opposite case, a destination that is slower than KIO, and about making the
progress bar and copy completion accurate.

The changes are in four KIO merge requests:
[MR 2506](https://invent.kde.org/frameworks/kio/-/merge_requests/2506) finds out which devices are
removable, [MR 2517](https://invent.kde.org/frameworks/kio/-/merge_requests/2517) and
[MR 2518](https://invent.kde.org/frameworks/kio/-/merge_requests/2518) flush the device at the end of
a copy or a move, and [MR 2283](https://invent.kde.org/frameworks/kio/-/merge_requests/2283) adds the
writeback window. All of it is merged, and will be in KDE Frameworks 6.32, released [November 13th 2026](https://community.kde.org/Schedules/Frameworks).

We will see the cause of the bug, its history, and what it took to fix it.

## Why a copy finishes before it has started

The file worker copies a file by handing its data to `write()`. `write()` returns as soon as the
data is in the page cache, in memory. The kernel writes it to the device later, when it decides to.
On a local SSD, later means very soon, and you never notice. On a USB 2.0 stick that writes at
2.3 MB/s, it is another story. Here is a 128 MiB file:

[![A 128 MiB copy to a USB 2.0 stick before the change: the copy reports complete after 0.06 to 0.13 s, and the data is on the stick after 68 to 91 s, over four runs.](https://blogs.kde.org/2026/10/27/fixing-kio-copy-to-usb-stick-and-network-filesystems/usb-before.svg)](https://blogs.kde.org/2026/10/27/fixing-kio-copy-to-usb-stick-and-network-filesystems/usb-before.svg)

For more than a minute, Dolphin considers the copy finished while the stick is still writing. The
progress bar was showing how fast KIO filled memory. Pull the stick out during that minute, and your
data is gone.

Network filesystems have a different symptom from the same cause. A large copy to an NFS or SMB
share leaves hundreds of MiB in memory to send to the server, and the progress runs far ahead of
it. On SMB it is worse than a wrong number: with the default `cache=strict`, looking at a file
waits until its dirty data is written. Listing the folder you are copying into looks at that file.
Over a 5 MB/s link, almost every listing during a 1 GiB copy waited 15 to 20 seconds.

## Fifteen years in one bug report

The right tool actually showed up very early. Two days after the report, Christoph Feck asked whether there was a
way to learn when the data is really on the disk "without causing massive slow downs that any sync
type calls would cause". Two weeks later, the reporter passed on Alan Stern's answer,
`sync_file_range()`, and Christoph replied that it looked like "exactly what we need". That was
September 2011, and it is the call KIO now uses.

Then not much happened for years, apart from users confirming it and seventeen duplicates. In 2021, Nate
Graham raised it to the highest priority, because a move deletes the source files while the copies
are still in memory. In 2022, he changed the Disks & Devices applet, so that ejecting a device
explains that it is still writing. In 2024, Christoph tested the `cachestat()` call of Linux 6.5,
which reports how much of a file is still dirty in memory, but only for one file at a time.

This bug has been my white whale. I have been contributing to KIO since 2018, and I am still learning
how the Linux storage stack behaves underneath it. I tried twice in 2024 and did not get
`sync_file_range()` right. In [MR 1718](https://invent.kde.org/frameworks/kio/-/merge_requests/1718),
the `sync_file_range()` path stayed commented out. In [KIO
MR 1764](https://invent.kde.org/frameworks/kio/-/merge_requests/1764) and [Dolphin
MR 862](https://invent.kde.org/system/dolphin/-/merge_requests/862), the worker waited for the
writeback of the chunk it had just written, which had not started, so it never waited at all. Waiting
for the window before the one just written is what makes it work. I didn't spot the issue, nor any
reviewer unfortunately.

Since then, another contributor proposed turning off the cache for copies, in
[MR 2162](https://invent.kde.org/frameworks/kio/-/merge_requests/2162), which was closed.

## Why it took so long

Making the copy correct is the easy part: call `fsync()` after every file, or open the destination with
`O_DIRECT` and skip the cache. Both make copies several times slower, and they would slow down
the fast local disks too, where nothing was wrong. Making it
correct without making it slow is what took fifteen years, and it needed several things that were
not there before.

- A way to wait for part of a file. POSIX only offers fsync(), which waits for everything. sync_file_range() is Linux only, and its own manual calls it "extremely dangerous": it does not write the file's metadata, so on its own it guarantees nothing after a crash. It can bound how much is in memory, but the end of the copy still needs a real flush.
- Knowing which destinations need it, without asking them. The filesystem type does not show whether a device can be unplugged, and asking a network filesystem anything is a round trip to a server that may be slow. KIO reads the answer from the mount table and from sysfs instead, and two earlier changes to KMountPoint made that cheap enough to do for every copied file:
  - MR 2326, in KIO 6.30, caches mounts by the mount id that statx() returns since Linux 6.8, instead of parsing /proc/self/mountinfo on every lookup. A lookup by id became about 700 times faster.
  - MR 2487, in KIO 6.32, reads a missing mount with statmount(), which does not walk any path, so a network server that does not answer no longer blocks the lookup. In that case, the lookup went from more than 15 seconds to about 1 ms.
- A place to flush at the end of a copy. The file worker copies one file per command, in its own process, and never knows which file is the last one. Only the CopyJob, in the application, knows when the whole copy is over. So the flush needed a new worker command, and a way for the worker to notify the job that a flush is needed. On the way, I found that FileCopyJob dropped the metadata that the worker sent with a copy, so the CopyJob could never have seen it.
- A window size that fits every destination. A window too small slows a fast link, and a window too large never fills on a slow one. That is why it now adapts, and why the progress has to stay monotonic when the window shrinks.

## A writeback window

Waiting for the device after every write would be correct but very slow. Waiting only at the end
leaves the progress wrong for the whole copy. KIO now does something in between, with
`sync_file_range()`, which lets a program start the writeback of part of a file and wait for it.

The data is written in windows. When a window is full, the worker hands it to a helper thread,
which writes it back and waits for it, while the copy fills the next window. The copy only waits
when the window before the one it hands over is not written yet. So at most two windows of the copy
are ever in memory and not on the device, and the progress bar is never more than one window ahead
of what is really written.

The helper thread was needed to accommodate CIFS, the kernel client for Samba and Windows shares. On CIFS,
the call that starts the writeback of a window does more than start it: it sends the data to the
server, and waits for the server to grant the credits to do so, blocking the calling thread for about 157 ms per 128 MiB window.
So the copy could not fill the next window while the previous one was sent. With the helper thread making that call, sending a window and
filling the next one overlap.

A window holds about 200 ms of writeback, at the speed measured on the window before. It starts at
1 MiB, can at most double from one window to the next, and stays below 16 MiB, or 128 MiB on CIFS.
On a fast link the windows grow, so the copy keeps its speed. On a slow link they stay at about
1 MiB, and anything that has to wait for the file waits a fraction of a second, not for the whole
file.

## Complete means on the device

A window bounds how much is left in memory, but there is still something left at the end. For a
removable device, KIO now also makes the end of the copy wait for it.

A file larger than the largest window, 16 MiB, is flushed with `fsync()`, and then its folder, before
the copy reports it done. By then the window has already written all but the last two windows, so the flush is
short.

Small files are the hard part. The obvious fix, an `fsync()` for every file, made 3000 files of
16 KiB take 10 seconds instead of 0.04 seconds on a local disk. So the worker flushes no small file
by itself. After a copy to a removable device, it notifies the job, and the `CopyJob` sends it one
more command before reporting success: write back the whole filesystem of the destination, with
one `syncfs()`. While that runs, the copy notification shows "Writing the copied data to the device...".
If the flush fails, the copy fails, because the data may not be on the device.

A move needed more than that. Before, KIO deleted each source file right after its copy, while
the copy could still be only in memory, which is why the bug got its highest priority. Now a move to
a removable device keeps its sources until the flush has succeeded, and deletes them after it. If the
flush fails, or the stick is unplugged during it, every source stays. A source that changed while it
waited for the flush stays too, with a warning. A copy or a move that stops on an error, or that you
cancel, still flushes the device, and a move then deletes only the sources of the files that are on
it.

Here is the same USB stick again, with the small files added:

[![Copies to a USB 2.0 stick, before and after the change. 128 MiB file: the copy reports complete after 0.06 to 0.13 s before, over four runs, and 28.1 s after; the data is on the stick after 68 to 91 s before and 28.1 s after. 3000 files of 16 KiB: complete after 1.2 s before and 183.9 s after; on the stick after 185.2 s before and 183.9 s after. Progress ahead of the stick: 128 MiB before, 3 MiB after.](https://blogs.kde.org/2026/10/27/fixing-kio-copy-to-usb-stick-and-network-filesystems/usb.svg)](https://blogs.kde.org/2026/10/27/fixing-kio-copy-to-usb-stick-and-network-filesystems/usb.svg)

Yes, the copies now take longer by the clock, but only because the clock now includes the time the
stick spends writing. The time until the data is really on the stick did not get worse. The speed of this stick
varies a lot from run to run, so the 28 seconds against 68 to 91 seconds for the large file is not a
speedup I would count on. The small files never fill a window, so they only depend on the flush at
the end.

## Which destinations get a window

A local fixed disk does not need any of this, and keeps the current behaviour exactly. With the
removable policy forced onto a local disk for testing, the 3000 small files took 1.55 s against
1.54 s before the change.

Deciding what is removable is less obvious than it sounds. The filesystem type does not expose it: exFAT
can be a memory card, and FAT is also the EFI partition of your laptop. Most USB disks do not even
report removable media. [MR 2506](https://invent.kde.org/frameworks/kio/-/merge_requests/2506) adds a private function to KIO that asks sysfs: the disk's own
removable flag, then the USB port or PCIe slot it hangs off, which the kernel marks removable when
it can be reached from outside the machine, and SD cards. It follows encrypted and LVM volumes down
to the disk under them.

Network filesystems are easier: every mount that KIO already considers slow gets a window. That is
NFS and CIFS, but also Ceph, GlusterFS, 9p, sshfs, and FUSE filesystems such as rclone. The worker
finds the mount from the mount id of the destination folder, without a round trip to the server.

## Numbers on network shares

To measure this, I used KIO's own copy job, comparing KIO master just before the change with KIO
master after it, while another thread listed the destination folder every 50 ms. The SMB server ran on the same machine, with 2 ms of
delay added to its traffic, and for the slow link a limit of 40 Mbit/s, about 5 MB/s.

On the slow link, the listing is the difference you would feel:

[![Listing a folder during a copy of 256 MiB to an SMB share at 5 MB/s, median seconds. Round 1: 11.3 s before the change, 1.7 s after. Round 2: 5.5 s and 1.7 s.](https://blogs.kde.org/2026/10/27/fixing-kio-copy-to-usb-stick-and-network-filesystems/smb-listing.svg)](https://blogs.kde.org/2026/10/27/fixing-kio-copy-to-usb-stick-and-network-filesystems/smb-listing.svg)

[![Copy of 256 MiB to an SMB share at 5 MB/s, 2 rounds. Time until complete: 54.2 and 54.4 s before, 55.9 and 55.9 s after, 4.95 MB/s against 4.80 MB/s. Progress ahead of the server: 256 MiB before, 1 MiB after. Slowest listing during the copy: 27.4 and 15.3 s before, 1.70 and 1.70 s after.](https://blogs.kde.org/2026/10/27/fixing-kio-copy-to-usb-stick-and-network-filesystems/smb-slow.svg)](https://blogs.kde.org/2026/10/27/fixing-kio-copy-to-usb-stick-and-network-filesystems/smb-slow.svg)

The copy runs about 3% slower with the window. On a fast link, the copy keeps up:

[![Copy of 4 GiB to an SMB share with 2 ms of delay, 5 rounds. Median time until complete: 7.15 s before, 6.06 s after. Largest progress ahead of the server: 1334 MiB before, 128 MiB after. Listing during the copy: median 60.9 ms before and 59.6 ms after, slowest 731 ms before and 111 ms after.](https://blogs.kde.org/2026/10/27/fixing-kio-copy-to-usb-stick-and-network-filesystems/smb-fast.svg)](https://blogs.kde.org/2026/10/27/fixing-kio-copy-to-usb-stick-and-network-filesystems/smb-fast.svg)

One of the five copies before the change failed with a write error from the share, so these
numbers come from four rounds. The times vary between runs: in an earlier run, the copy with the
window was 4% slower.

Getting there took me four tries. My first version was 10 to 20% slower on the fast link, because
of the CIFS behaviour described above. Then, with the windows aimed at 500 ms, listings on the slow
link went up to 4.2 seconds, because each request of a listing waits behind the window being sent.
Aiming the windows at 200 ms brought the listings down to 1.7 seconds.

NFS, on the same machine with 2 ms of delay:

[![Copy of 4 GiB to an NFS share with 2 ms of delay, medians of 3 rounds. Time until complete: 9.8 s before, 10.4 s after. Progress ahead of the server: 14 to 23 MiB before, 1 to 5 MiB after. Listing during the copy: median 24 ms before and 11 ms after, 95th percentile 63 ms before and 40 ms after.](https://blogs.kde.org/2026/10/27/fixing-kio-copy-to-usb-stick-and-network-filesystems/nfs.svg)](https://blogs.kde.org/2026/10/27/fixing-kio-copy-to-usb-stick-and-network-filesystems/nfs.svg)

The copy times are close: 11% slower in the first round, and slightly faster in the two others.

## Part of a frozen Dolphin

[Bug 423187](https://bugs.kde.org/show_bug.cgi?id=423187) collects many ways in which a slow mount
can freeze Dolphin. In one of its comments, Frank Gehann copied a 100 MB file to an SMB share while
browsing it, and found two causes: Dolphin's main thread waiting for answers from the share, and
folder listings waiting behind the queued upload.

The window helps with the second cause: each request of a listing now waits behind at most two
windows, about 400 ms of writeback, and a whole listing took 1.7 seconds on the 5 MB/s link instead
of 5 to 11. The [`statmount()` change](https://invent.kde.org/frameworks/kio/-/merge_requests/2487)
helps with part of the first one. `KFileItem::isSlow()`, which Dolphin calls on its main thread
before it reads a file to find its type, no longer waits for any server, on Linux 6.8 or later. Work is underway to fix the
rest of the first cause in Frank's open
[MR 2484](https://invent.kde.org/frameworks/kio/-/merge_requests/2484) and
[MR 2485](https://invent.kde.org/frameworks/kio/-/merge_requests/2485).

## The stick that pauses

One measurement sent me down a rabbit hole. During a large copy to the USB stick, listing a folder on
the stick sometimes took about 15 seconds, before the change as much as after it. It looked like the
writeback window was making something wait.

It was the stick. Roughly every 8 seconds, a single 120 KiB write to it took 4 to 7 seconds to
complete, and the listing waited for a page that was stuck behind such a write. KIO cannot fix a
device that stops for seconds at a time, but at least we now know the copy is not to blame. In the runs for this post, the
slowest listing took 3.6 ms during the copy of the large file, but 7 seconds during the copy of the
small files, against 15 seconds before the change.

## Copying between two filesystems

One more thing landed along the way, and this one is a plain speedup. In 2021, in Frameworks 5.88, I replaced `sendfile()` with
`copy_file_range()` in the file worker, in
[MR 602](https://invent.kde.org/frameworks/kio/-/merge_requests/602). At the time, Linux copied with `copy_file_range()` across
filesystems too. Linux 5.19 changed that back: between two filesystems, the call fails again with
`EXDEV`. Since then, a copy from one filesystem to another went through `read()` and `write()` in the
worker, one buffer at a time.

[MR 2520](https://invent.kde.org/frameworks/kio/-/merge_requests/2520) now falls back to
`sendfile()` in that case, which copies from one file to another inside the kernel:

[![Copy of 1 GiB between two filesystems, medians of 5 rounds. tmpfs to ext4: 443 ms before, 272 ms after. ext4 to tmpfs: 531 ms before, 278 ms after.](https://blogs.kde.org/2026/10/27/fixing-kio-copy-to-usb-stick-and-network-filesystems/sendfile.svg)](https://blogs.kde.org/2026/10/27/fixing-kio-copy-to-usb-stick-and-network-filesystems/sendfile.svg)

A copy to the USB stick takes as long as before, because its write
speed is the limit. This one is merged too, and will also be in KDE Frameworks 6.32.

## Closing

With all this, a copy to a USB stick now finishes when the data is actually on the stick.
On network filesystems, the progress now follows what the server has received, and the share stays
usable during the copy.

`sync_file_range()` is mainly used by databases and storage engines. No other file manager that I
know of uses it. Now KIO, and so Dolphin, uses it too.
A while ago, I was working for a customer (who shall remain unnamed here, but let’s call it *Intel*) doing system simulation software. I worked on this project for a year or so. I ran full x86 systems completely simulated. During that time I was chasing some nasty bugs in the simulated usb-disk device that caused my Windows boot to end up in a blue screen.

![](https://daniel.haxx.se/blog/wp-content/uploads/2011/09/BUGCODE_USB_DRIVER.png)

I struggled to figure out why Windows 7 would write 0xABADBABE to EHCI register index 0x1C – which is a reserved register – during boot some 10 milliseconds before the blue screen appears, and I was convinced that it was due to a flaw in the EHCI simulation code and thus was the first indication of the failure. If I didn’t have any simulated usb-disk inserted that write wouldn’t occur, and similarly that write would occur even if I inserted the usb-disk much later – like even after Windows 7 had started and I was passed the login screen.

An interesting exercise is to grep for this (little-endian so twist it around!) 32 bit pattern in a freshly installed windows 7 file system – I found it on no less than 16 places in a 20GB file system. This [bgrep](https://github.com/tmbinc/bgrep) utility was handy for this.

To properly disassemble that code, I hacked up a quick [bcut](https://github.com/bagder/bcut) tool so that I could cut out a suitable piece of the 20GB file to pass to objdump, as objdump very inconveniently does *not* offer an option to skip an arbitrary amount from the beginning of a file! Also, as it is not really possible to easily tell on which byte x86 code starts at, I had to be able to fine-adjust the beginning of the cut so that objdump would show correctly (this is x86-64):

```
      callq  *0x9061(%rip)        # 0x9080
      mov    0x40(%rsi),%r11d
      mov    %rsi,0x58(%rdi)
      mov    %r11d,(%rdi)
      mov    0x40(%rsi),%eax
      mov    %rsi,0x60(%rdi)
      mov    %eax,0x4(%rdi)
      mov    0xa0(%r13),%rax
      movl   $0xabadbabe,0x1c(%rax)
```

But then, reading that code never gave me enough clues to figure out why the offending MOV is made.

Thanks to a friend with a good eye and useful resources, I finally learned that Windows does this write on purpose to offer some kind of break-point for a debugger. It always does this (assuming a USB device or something is attached)!

A red herring as far as I’m concerned. Nothing to bother about, just MOV on! I simply made the simulation accept this.

Oh. You want to know what happened to the blue screen? It had nothing at all to do with the bad babe constant, but turned out to be because the ehci driver finds out that some USB data structs the controller fills in get pointers that point to memory outside of the area the driver has mapped for this purpose. In other words it was a really hard to track down bug in the simulated device.

1. ![](https://secure.gravatar.com/avatar/55052f2a9816ed3a4bae16f56948c91f46aec27b4486353bcd8c1b7a6794358d?s=68&d=monsterid&r=g) **José Antonio G. de O.** says: .comment-author [December 1, 2011 at 22:13](https://daniel.haxx.se/blog/2011/10/28/whos-0xabadbabe-and-why/#comment-8848) .comment-metadata .comment-meta It’s typically the kind of information I really like to read ! Once, I used myself such so-called magic number 0xA340B747 to authenticate my genuine 3″1/2 floppy disks in a stealth way 🙂 By the time, the competition between the respective flagships of Airbus and Boeing inspired me ! By the way, I didn’t found any reference in Wikipedia of this specific use of 0xabadbabe in the below articles : [http://en.wikipedia.org/wiki/Hexspeak](http://en.wikipedia.org/wiki/Hexspeak) [http://en.wikipedia.org/wiki/Magic_number_(programming)](http://en.wikipedia.org/wiki/Magic_number_(programming)) Who knows… Maybe it could help someone, someday ? 😉 .comment-content .comment-body
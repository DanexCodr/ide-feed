So, after a debugging session the other day, I was having some shower
      thoughts regarding early userspace and initrd.

Linux initramfs supports unpacking CPIO, a stupid, simple, standardized
      format. In the discussion on whether to support TAR instead, much
      emphasize has been put on the fact that CPIO is standardized and less
      fragmented.

Luckily, Linux (the kernel) includes its own tool to produce the specific
      variant of the standard that it happens to implement. The standard CPIO
      tool is possibly the most cursed archiver under the SUN.

In the old DOS/WinDOS world, ZIP was probably the most wide spread and
      well known archive format, being displaced to some extend by the rise of
      RAR during the 2000s.

Because of the design of the format, ZIP lends itself to all kinds of
      polyglot trickery. Way back when, self extracting ZIP archives where a
      thing, EXE/ZIP polyglots that can be run and unpack themselves, which is
      useful if you don't have an archiver installed.

I don't think I need to explain where I am going with this, here is the
      resulting ZIP archive I built:

It is a completely normal ZIP archive, containing its own source code
      needed to build itself from scratch:

```

$ unzip -t boot.zip
Archive:  boot.zip
    testing: boot/ZIPHEAD.COM         OK
    testing: boot/MESSAGE.TXT         OK
    testing: common/asm.h             OK
    testing: common/multiboot.h       OK
    testing: common/zip.h             OK
    testing: multiboot/console.c      OK
    testing: multiboot/console.h      OK
    testing: multiboot/multiboot.c    OK
    testing: multiboot/string.S       OK
    testing: setup/a20.S              OK
    testing: setup/disk.S             OK
    testing: setup/entry16.S          OK
    testing: setup/entry32.S          OK
    testing: setup/mbload.S           OK
    testing: setup/mem.S              OK
    testing: setup/setup.ld           OK
    testing: util/fixhdr.c            OK
    testing: util/zipglue.c           OK
    testing: util/zippack.c           OK
    testing: mk.sh                    OK
    testing: README.txt               OK
    testing: MESSAGE.txt              OK
    testing: LICENSE.txt              OK
No errors detected in compressed data of boot.zip.
```

A particularly interesting file here is **boot/ZIPHEAD.COM**, that
      contains executable code that is run when booting the archive.

You need to fix the execute permissions of mk.sh after
      unpacking, and you will need a copy of Zlib installed for
      the tools. Running mk.sh from it's directory should
      leave you with a fresh copy of the bootable ZIP archive.

The simplest way to run it, is to just pass it to Qemu direct kernel boot:

```
$ qemu-system-i386 -kernel boot.zip
```

"That's easy" you might say, "Qemu supports Multiboot, that ZIPHEAD.COM
      is uncompressed, at the beginning of the archive and has a Multiboot
      header in it!"

Yes, that's all true! But this ZIP archive also brings it's own boot
      loader along. You can try putting it on a floppy and throw that in front
      of Qemu:

```

$ dd if=/dev/zero of=floppy.img count=2880
$ dd if=boot.zip of=floppy.img conv=notrunc
$ qemu-system-i386 -fda floppy.img
```

The first 512 bytes of the archive contain a valid boot sector that
      loads some more code from the second sector and then bootstraps itself
      into highmem with the A20 enabled and 32 bit protected mode set up.

You can also put it on a hard drive too, it detects what **INT 13h**
      drive it's been loaded from and dutifully queries the disk geometry.

If you care to try, you can also dump it on a real floppy and stuff it
      into a PC:

That's a Pentium MMX by the way, but I also tried an i486 DX2 and an
      Am386DX-40, just to be sure. My 486 had me hold my breath for a moment,
      it has a spectacularly slow floppy drive. The text on screen is from
      the file **boot/MESSAGE.TXT**

"But that's not special either" you might respond, "ZIPs are read from
      the back, you can just put anything you want in front, so you put a boot
      sector there!"

That is sadly *not quite true* anymore, I'll get to that. But for
      now, lets take a look at the first couple bytes of that archive
      together and we'll see the real party trick:

```

$ xxd -g 1 -l 128 boot.zip
00000000: 50 4b 03 04 0a 00 02 80 00 00 eb 44 e4 2e 41 0f  PK.........D..A.
00000010: 01 8f 0a 09 00 00 0a 09 00 00 10 00 00 00 62 6f  ..............bo
00000020: 6f 74 2f 5a 49 50 48 45 41 44 2e 43 4f 4d 00 90  ot/ZIPHEAD.COM..
00000030: 02 b0 ad 1b 03 00 01 00 fb 4f 51 e4 30 00 10 00  .........OQ.0...
00000040: 00 00 10 00 bd 72 10 00 bd 72 10 00 31 03 10 00  .....r...r..1...
00000050: fa fc 31 c0 89 c4 8e d8 8e c0 8e d0 ea 61 7c 00  ..1..........a|.
00000060: 00 bf 00 06 b9 00 02 f3 aa 88 16 98 06 be 0f 7d  ...............}
00000070: e8 8c 00 b8 00 f0 89 c1 50 9d 9c 58 a8 02 74 4a  ........P..X..tJ
```

The ASCII **P** stands for Phil
      ([not Picard](https://memory-alpha.fandom.com/wiki/Lonely_Among_Us_(episode)#Act_Five)), as in
      [Phil Katz](https://en.wikipedia.org/wiki/Phil_Katz),
      followed by **03h** and **04h**. What you are looking at, is a
      completely valid ZIP local file header for **boot/ZIPHEAD.COM**

Oh, and those other bytes there after the ZIP header: **02 b0 ad 1b**,
      if you flip them around to human endian, it reads **1BADB002**.
      That's the Multiboot magic :-)

The 16 bit real mode code starts right after the Multiboot header,
      at offset **00000050**. If you are feeling a little confused,
      so is the file utility:

```

$ file boot.zip
boot.zip: DOS/MBR boot sector; partition 1 : ID=0xd, active 0xcd, start-CHS (0x7
2,19,7), end-CHS (0x388,254,6), startsector 2147916342, 243810273 sectors; parti
tion 2 : ID=0x60, active 0x9c, start-CHS (0x366,6,3), end-CHS (0x3f7,49,18), sta
rtsector 2298911798, 4154016209 sectors; partition 4 : ID=0xf8, active 0xe1, sta
rt-CHS (0x2,184,1), end-CHS (0x313,6,13), startsector 3277940231, 0 sectors
```

If you take a closer look at the first line of the hex dump, you might
      be able to spot the jump instruction that makes this little magic trick
      possible. Luckily, Phil Katz' initials are valid opcodes. The Multiboot
      entry point is much further into the file at offset **00000331**.

Here's a picture you probably recognize from
      [the Wikipedia article about the ZIP format](https://en.wikipedia.org/wiki/ZIP_(file_format)).
      This here is a local copy, Wikimedia Commons hosts
      [the original with attribution and licensing information](https://commons.wikimedia.org/wiki/File:ZIP-64_Internal_Layout.svg).

Much like a TAR or CPIO archive, a ZIP file is an amalgamation of tightly
      packed files with a short header in front, specifying the full file path
      and other meta data:

```

typedef struct {
	uint32_t magic;
	uint16_t version;
	uint16_t flags;
	uint16_t method;
	uint16_t modtime;
	uint16_t moddate;
	uint32_t checksum;
	uint32_t compsize;
	uint32_t origsize;
	uint16_t namelength;
	uint16_t extralength;
	char name[namelength];
	uint8_t extra[extralength];
} __attribute__((packed)) zip_entry_t;
```

The timestamps are DOS datetime, the checksum is a CRC-32, there are no
      attributes or permission bits, we are thoroughly in DOS land. Directories
      are implied by the file paths.

Unlike TAR or CPIO, there is a **central directory** in the end, with
      a listing of all of the file headers and back references to the file in
      the archive. Unlike traditional file formats that have are
      **started by a header**, ZIP is **terminated by a footer**.

The reason for this is twofold:

That last part was especially important in the days when ZIP archives
      would be split over several floppies. To access a file, just scan the
      directory on the last floppy, then tell the user what floppy to insert to
      get the file.

By comparison, accessing a file in a tarball requires linearly scanning
      over the whole thing (which, on the other hand, is
      [preferable for tape drives](https://en.wikipedia.org/wiki/Tape_drive#Technical_limitations), where TAR originates).

### Polyglot Trickery

ZIP archives are meant to be read from the back, the footer points to the
      central directory, the directory points to the files. *In theory*,
      the archiver shouldn't care if there happens to be a gap between two
      files, containing something else or if there is something else in the
      front of the archive, like a file header for a different file format.

The local file headers also supports up to 64k of "extra" stuff between
      the header and the file data, the footer has "comment" at the end, also
      up to 64k.

If you look at the footer for a second, you might spot an interesting
      design flaw:

```

typedef struct {
	uint32_t magic;
	uint16_t disknum;
	uint16_t diskstart;
	uint16_t num_dir_entries;
	uint16_t total_dir_entries;
	uint32_t dir_size;
	uint32_t dir_start;
	uint16_t comment_length;
	uint8_t comment[comment_length];
} __attribute__((packed)) zip_end_t;
```

it is variable size, an archiver needs to find it looking
      from the back, but the magic and the size are both stored *before*
      the variable sized comment field. Ask yourself this for a moment: how
      would you implement this in an archiver? Demanding that there is no
      comment? Reading the last 64k plus some change and scanning it? From
      which direction? What if there is another valid footer inside the
      comment field of the footer? Depending on how an implementation deals
      with this, a specifically crafted archive can appear to contain
      different files when viewed with different archivers.

Trying to make the format extensible ended up building a whole lot of
      foot guns in there. And we are not even talking about the plethora of
      extensions that have been tacked on to the official specification over
      the years.

Many modern implementations decided to save themselves a lot of headaches
      and just treat ZIP archives the same way as tarballs, linearly scanning
      them from the front instead. They expect the archive to start with a
      local header, skipping by the size **MUST** lead to the next entry
      or finally, the central directory. They reject any archives where this
      is not possible. This effectively prevents a lot of polyglot trick
      fuckery, but at the cost of rendering possibly valid archives unreadable.

For the self booting ZIP archive, the challenge thus becomes: the archive
      **MUST** start with a local file header, there cannot be *any*
      gaps, everything must be properly contained inside files.

Anybody who has ever looked at a DIY toy OS tutorial has probably
      stumbled across
      [The Multiboot Specification](https://www.gnu.org/software/grub/manual/multiboot/multiboot.html), the possibly easiest and most beginner friendly way to get
      a program running on bare metal x86.

The multiboot spec originates in the GNU/FSF ecosystem and is implemented
      by boot loaders like GRUB or Qemu direct kernel boot. SYSLINUX supports
      it via a plugin. There is a draft for an over engineered 2nd version, that
      also supports MIPS, but this is of no concert to us here.

A Multiboot 1 compliant kernel simply contains the magic
      value **0x1BADB002** *somewhere* in the first in the first 8k.
      This is followed by flags and a checksum (all 3 must add up to zero).
      Depending on the flags, additional fields may follow.

The kernel itself can be an ELF file from which the loader extracts
      load address and entry point. The kernel is run in 32 bit protected
      mode with flat segments (base=0, limit=4G) and the A20 gate enabled.

Alternatively to a plain old ELF file, the kernel can also specify the
      memory layout manually (indicated via a flag), allowing flat binaries or
      other file formats to be loaded. The extended header looks like this:

```

typedef struct {
	uint32_t magic;
	uint32_t flags;
	uint32_t checksum;
	uint32_t hdr_addr;
	uint32_t load_addr;
	uint32_t load_end_addr;
	uint32_t bss_end_addr;
	uint32_t entry_point;
} mb_header_t;
```

The **hdr_addr** specifies the in-memory address of the header after
      loading the file, using this and the file offset where the header was
      found, the other addresses can be converted back to file offsets by the
      loader.

This way, the **load_addr** and **load_end_addr** are used to figure
     out *what* parts of the file to load *where* into memory. If the
     **bss_end_addr** is past that, the loader zero-fills it, before finally
     jumping to **entry_point** to run the kernel.

The Multiboot compliant loader also sets up a structure with system
      information (e.g. memory map, APM tables), kernel command line,
      etc… and passes the pointer to the kernel (via register
      **EBX**, magic value **0x2BADB002** in **EAX**).

Making a Multiboot bootable ZIP archive is trivial. Simply pack a flat
      binary with a Multiboot header as uncompressed file binary, make sure it
      is at the beginning and the addresses line up. An external tool can then
      fix up the headers, so that the whole archive is loaded.

For any *practical* applications, it would make *sense* to stop
      right here, but we're not here for "practical" or "sane".

On an IBM compatible machine, the BIOS iterates over the installed
      drives, loads the first sector from each (to location **0x7c00**),
      until it finds one where the first sector ends with **0xaa55**.
      It then jumps to the first byte.

Disks that are formatted with a filesystem, typically have a header in
      the beginning that starts with a jump instruction across the header into
      the bootstrap code that follows. The DOS MBR format opts to instead store
      the partition table at the end of the first sector and all the code in
      the front.

If we stuff a BIOS boot signature into the ZIP archive, at least parts
      of the ZIP local file header will be executed, the first few bytes are
      a mandated magic value and we cannot just put a jump instruction there.

The puzzle exercise now becomes, filling the header fields with values
      that make sense but also happen to be valid 8086 opcodes. At least,
      until we hit something that can be abused as a free-form field that we
      can stuff a jump into.

Let's take a look at that hex dump again:

```

00000000: 50 4b 03 04 0a 00 02 80 00 00 eb 44 e4 2e 41 0f  PK.........D..A.
00000010: 01 8f 0a 09 00 00 0a 09 00 00 10 00 00 00 62 6f  ..............bo
00000020: 6f 74 2f 5a 49 50 48 45 41 44 2e 43 4f 4d 00 90  ot/ZIPHEAD.COM..
```

I've tried to highlight the relevant header up to the jump
      instruction: **0xeb** is a relative jump with a single byte
      immediate argument.

If we take a look again at the header structure, we can make out what
      fields those bytes correspond to:

```

typedef struct {
	uint32_t magic;
	uint16_t version;
	uint16_t flags;
	uint16_t method;
	uint16_t modtime;
	………
```

The timestamp is the first best place where we can put a jump
      instruction. The **0xeb** relative jump works out to **8:30-ish**
      in the morning, give or take the jump distance.

The two bytes in front of the **modtime** are compression
      **method**. We really, really want to have **0x0000** here,
      i.e. *uncompressed*, so that an archiver doesn't choke on the
      file data.

The first four bytes are the magic value of the format, we don't have any
      choice what to put here either, it has to be "**PK\03\04**". The
      **version** and **flags** fields are the only places where we have
      some creative freedom.

If we run the file through a dissassembler and take a look at the
      first few bytes, we'll end up with this:

```

$ objdump -D -m i8086 -b binary ./boot.zip

./boot.zip:     file format binary

Disassembly of section .data:

00000000 <.data>:
       0:       50                      push   %ax
       1:       4b                      dec    %bx
       2:       03 04                   add    (%si),%ax
       4:       0a 00                   or     (%bx,%si),%al
       6:       02 80 00 00             add    0x0(%bx,%si),%al
       a:       eb 44                   jmp    0x50
```

This is AT&T syntax, source operands are left, destination
      on the right. We use GNU tools in this household, deal with it.

Anything that just fiddles around with a register doesn't really hurt us.
      Same goes for memory *reads*. We don't have memory protection, no
      matter what we access, there won't be any faults, the only memory
      mapped hardware around should be the frame buffer.

Memory writes are another story. Worst case, we could shoot up the
      interrupt vectors, the BIOS RAM areas (BDA, EBDA), or shadowed option
      ROMs.

The **P** for Phil also happens to also decode to
      **push %ax**. If the BIOS leaves us with a somewhat sane stack
      pointer, the **push** instruction should hopefully not mess anything
      up. It is part of the ZIP magic and thus unavoidable.

The **version** field is itself actually *structured*, containing
      a decimal encoded version number, followed by an OS ID byte. If we set
      it to **0x000a** (stored as little endian), this decodes to version
      **1.0** on **MS DOS**.

**0x0a** is an **orb**, version 1.1 would be double byte sized,
      version 0.8 and 0.9 would be register direct and not touch the memory.
      An address of **BX + SI** is the result of a **mod-reg-r/m** field
      with all zeros.

We could try to code golf our way into consuming at least part of the
      **flags** as well, but low-valued, "harmless" opcodes that result
      in sane versions are sparse. Also, some version numbers change the
      meaning how an archiver is supposed to interpret the file. Also also,
      **mod-reg-r/m** combinations in the OS code field quickly end up as
      an undefined OS ID. Also also also, we have the **method** as well,
      that *has to be* **0x0000**, which would result in a memory
      write if executed. We have to consume that somehow, rather than running
      it.

So for the **flags**, I came up with **0x8002** (stored as little
      endian). The lowest, set bit has a compression method dependent meaning,
      currently only defined for LZMA (14), deflate (8) and implode (6). For
      uncompressed (method 0) there is no defined meaning (the specification
      just ignores that part, it doesn't use nasty words like
      *undefined*). For deflate it would mean that
      *maximum compression* was used.

The MSB is specified as "reserved for use by PKWARE", whatever they chose
      to put there, if they ever chose anything at all. Most imporanly, the
      opcode **0x02** decodes to a single byte, indirect add, and in the
      **mod-reg-r/m**, the MSB tells the CPU to consume another 2 bytes of
      immediate **DISP**lacement. This is how we can get rid of the
      compression method.

At this point, we've made it! We reached the **modtime** field
      that we can just stuff a jump into.

Once we've made it past the header, we are in 16 bit real mode. We just
      need to go through all of the neccessary steps to set up the environment
      that the Multiboot code expects:

This might sound like a lot, but in the current version, the actual code
      boils down to 817 bytes. That includes all the headers (ZIP, multiboot),
      the rather bulky GDT. But it is still quite a lot and outside the scope
      of this post anyway, I might pick some interesting parts out of it for
      some follow-up posts (watch this space?).

The Multiboot entry code re-loads the GDT, but this time using the
      highmem location, and sets up a stack after the archive. The size is
      extracted from the Multiboot header. Knowing the start address, the C
      code can then iterate over itself to locate and access files in the
      archive.

Some linker script trickery is used to tie it all into one blob, but with
      the GDT and Multiboot header visible from both lomem and highmem code at
      different locations.

At this point, you might be inclined to actually read the source code
      in the ZIP archive. There are lots of comments trying to explain what
      is going on.

There's a README that points out the structure of the code with
      suggestions where to start reading. I decided to keep it readable rather
      than stuff it all into a single sector. Self-modifying trickery is kept
      to a minimum (to safe some space, the function to enter unreal mode
      modifies itself, the code is run twice, courtesy of a misdirected
      **ret**, entering protected mode the first time round, leaving it
      again and restoring the segment registers on the second run, before
      returning for real).

Code in the archive and this blog posts have been written with
      assistance from:

If you poke around in the code and have any suggestions for improvements,
      or otherwise do anything interesting with it, please let me know.
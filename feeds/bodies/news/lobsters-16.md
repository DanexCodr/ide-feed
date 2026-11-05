In [computing](https://en.wikipedia.org/wiki/Computing), the **Executable and Linkable Format**<sup>[[3]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-linuxfoundation-elf-3)</sup> (**ELF**, formerly named **Extensible Linking Format**) is a common standard [file format](https://en.wikipedia.org/wiki/File_format) for [executable](https://en.wikipedia.org/wiki/Executable) files, [object code](https://en.wikipedia.org/wiki/Object_code), [shared libraries](https://en.wikipedia.org/wiki/Shared_library), [device drivers](https://en.wikipedia.org/wiki/Device_driver), and [core dumps](https://en.wikipedia.org/wiki/Core_dump). First published in the specification for the [application binary interface](https://en.wikipedia.org/wiki/Application_binary_interface) (ABI) of the [Unix](https://en.wikipedia.org/wiki/Unix) operating system version named [System V Release 4](https://en.wikipedia.org/wiki/System_V_Release_4) (SVR4),<sup>[[4]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-4)</sup> and later in the Tool Interface Standard,<sup>[[1]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-linuxbase-elf-1)</sup> it was quickly accepted among different vendors of [Unix](https://en.wikipedia.org/wiki/Unix) systems. In 1999, it was chosen as the standard binary file format for Unix and [Unix-like](https://en.wikipedia.org/wiki/Unix-like) systems on [x86](https://en.wikipedia.org/wiki/X86) processors by the [86open](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#86open) project.

| Executable and Linkable Format |  |
| --- | --- |
| [Filename extension](https://en.wikipedia.org/wiki/Filename_extension) | none, .axf, .bin, .elf, .o, .out, .prx, .puff, .ko, .mod, .AppImage and .so |
| [Magic number](https://en.wikipedia.org/wiki/File_format#Magic_number) | `0x7F 'E' 'L' 'F'` |
| Developed by | [Unix System Laboratories](https://en.wikipedia.org/wiki/Unix_System_Laboratories)<sup>[[1]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-linuxbase-elf-1)</sup><sup>: 3 </sup> |
| Initial release | 14 May 1998; 28 years ago (1998-05-14) |
| [Latest release](https://en.wikipedia.org/wiki/Software_release_life_cycle) | 4.2 <sup>[[2]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-2)</sup> 2025; 1 year ago (2025) |
| Type of format | [Binary](https://en.wikipedia.org/wiki/Binary_file), [executable](https://en.wikipedia.org/wiki/Executable), [object](https://en.wikipedia.org/wiki/Object_code), [shared library](https://en.wikipedia.org/wiki/Library_(computing)), [core dump](https://en.wikipedia.org/wiki/Core_dump) |
| [Container for](https://en.wikipedia.org/wiki/Container_format) | Many executable binary formats |

By design, the ELF format is flexible, extensible, and [cross-platform](https://en.wikipedia.org/wiki/Cross-platform). For instance, it supports different [endiannesses](https://en.wikipedia.org/wiki/Endiannesses) and address sizes so it does not exclude any particular [CPU](https://en.wikipedia.org/wiki/Central_processing_unit) or [instruction set architecture](https://en.wikipedia.org/wiki/Instruction_set_architecture). This has allowed it to be adopted by many different [operating systems](https://en.wikipedia.org/wiki/Operating_system) on many different hardware [platforms](https://en.wikipedia.org/wiki/Computing_platform).

Each ELF file is made up of one ELF header, followed by file data. The data can include:

- Program header table, describing zero or more memory segments
- Section header table, describing zero or more sections
- Data referred to by entries in the program header table or section header table

The segments contain information that is needed for [run time](https://en.wikipedia.org/wiki/Run_time_(program_lifecycle_phase)) execution of the file, while sections contain important data for linking and relocation. Any [byte](https://en.wikipedia.org/wiki/Byte) in the entire file can be owned by one section at most, and orphan bytes can occur which are unowned by any section.

### ELF header

The ELF header defines whether to use [32-bit](https://en.wikipedia.org/wiki/32-bit_computing) or [64-bit](https://en.wikipedia.org/wiki/64-bit_computing) addresses. The header contains three fields that are affected by this setting and offset other fields that follow them. The ELF header is 52 or 64 bytes long for 32-bit and 64-bit binaries, respectively.

| Offset | Size (bytes) | Field | Purpose |  |  |
| --- | --- | --- | --- | --- | --- |
| 32-bit | 64-bit | 32-bit | 64-bit |  |  |
| 0x00 | 4 | e_ident[EI_MAG0] through e_ident[EI_MAG3] | `0x7F` followed by `ELF`(`45 4c 46`) in [ASCII](https://en.wikipedia.org/wiki/ASCII); these four bytes constitute the [magic number](https://en.wikipedia.org/wiki/Magic_number_(programming)). |  |  |
| 0x04 | 1 | e_ident[EI_CLASS] | This byte is set to either `1` or `2` to signify 32- or 64-bit format, respectively. |  |  |
| 0x05 | 1 | e_ident[EI_DATA] | This byte is set to either `1` or `2` to signify little or big [endianness](https://en.wikipedia.org/wiki/Endianness), respectively. This affects interpretation of multi-byte fields starting with offset `0x10`. |  |  |
| 0x06 | 1 | e_ident[EI_VERSION] | Set to `1` for the original and current version of ELF. |  |  |
| 0x07 | 1 | e_ident[EI_OSABI] | Identifies the target operating system [ABI](https://en.wikipedia.org/wiki/Application_binary_interface). ValueABI 0x00[System V](https://en.wikipedia.org/wiki/System_V) 0x01[HP-UX](https://en.wikipedia.org/wiki/HP-UX) 0x02[NetBSD](https://en.wikipedia.org/wiki/NetBSD) 0x03[Linux](https://en.wikipedia.org/wiki/Linux) 0x04[GNU Hurd](https://en.wikipedia.org/wiki/GNU_Hurd) 0x06[Solaris](https://en.wikipedia.org/wiki/Solaris_(operating_system)) 0x07[AIX](https://en.wikipedia.org/wiki/IBM_AIX) (Monterey) 0x08[IRIX](https://en.wikipedia.org/wiki/IRIX) 0x09[FreeBSD](https://en.wikipedia.org/wiki/FreeBSD) 0x0A[Tru64](https://en.wikipedia.org/wiki/Tru64) 0x0BNovell Modesto 0x0C[OpenBSD](https://en.wikipedia.org/wiki/OpenBSD) 0x0D[OpenVMS](https://en.wikipedia.org/wiki/OpenVMS) 0x0E[NonStop Kernel](https://en.wikipedia.org/wiki/NonStop_(server_computers)) 0x0F[AROS](https://en.wikipedia.org/wiki/AROS_Research_Operating_System) 0x10FenixOS 0x11Nuxi [CloudABI](https://en.wikipedia.org/wiki/CloudABI) 0x12[Stratus Technologies OpenVOS](https://en.wikipedia.org/wiki/Stratus_VOS) Unclear if ever used directly on [[RISC OS]] (it has an RISC OS file type, 0xE1F for ELF, for "elfrun"), seemingly only indirectly used with elf2aif tool (at least most of the time), to target RISC OS's AIF format: https://heyrick.eu/blog/index.php?diary=20150727 https://www.riscosopen.org/wiki/documentation/show/File%20Types |  |  |
| Value | ABI |  |  |  |  |
| 0x00 | [System V](https://en.wikipedia.org/wiki/System_V) |  |  |  |  |
| 0x01 | [HP-UX](https://en.wikipedia.org/wiki/HP-UX) |  |  |  |  |
| 0x02 | [NetBSD](https://en.wikipedia.org/wiki/NetBSD) |  |  |  |  |
| 0x03 | [Linux](https://en.wikipedia.org/wiki/Linux) |  |  |  |  |
| 0x04 | [GNU Hurd](https://en.wikipedia.org/wiki/GNU_Hurd) |  |  |  |  |
| 0x06 | [Solaris](https://en.wikipedia.org/wiki/Solaris_(operating_system)) |  |  |  |  |
| 0x07 | [AIX](https://en.wikipedia.org/wiki/IBM_AIX) (Monterey) |  |  |  |  |
| 0x08 | [IRIX](https://en.wikipedia.org/wiki/IRIX) |  |  |  |  |
| 0x09 | [FreeBSD](https://en.wikipedia.org/wiki/FreeBSD) |  |  |  |  |
| 0x0A | [Tru64](https://en.wikipedia.org/wiki/Tru64) |  |  |  |  |
| 0x0B | Novell Modesto |  |  |  |  |
| 0x0C | [OpenBSD](https://en.wikipedia.org/wiki/OpenBSD) |  |  |  |  |
| 0x0D | [OpenVMS](https://en.wikipedia.org/wiki/OpenVMS) |  |  |  |  |
| 0x0E | [NonStop Kernel](https://en.wikipedia.org/wiki/NonStop_(server_computers)) |  |  |  |  |
| 0x0F | [AROS](https://en.wikipedia.org/wiki/AROS_Research_Operating_System) |  |  |  |  |
| 0x10 | FenixOS |  |  |  |  |
| 0x11 | Nuxi [CloudABI](https://en.wikipedia.org/wiki/CloudABI) |  |  |  |  |
| 0x12 | [Stratus Technologies OpenVOS](https://en.wikipedia.org/wiki/Stratus_VOS) Unclear if ever used directly on [[RISC OS]] (it has an RISC OS file type, 0xE1F for ELF, for "elfrun"), seemingly only indirectly used with elf2aif tool (at least most of the time), to target RISC OS's AIF format: https://heyrick.eu/blog/index.php?diary=20150727 https://www.riscosopen.org/wiki/documentation/show/File%20Types |  |  |  |  |
| 0x08 | 1 | e_ident[EI_ABIVERSION] | Further specifies the ABI version. Its interpretation depends on the target ABI. Linux kernel (after at least 2.6) has no definition of it,<sup>[[6]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-6)</sup> so it is ignored for statically linked executables. In that case, offset and size of EI_PAD are `8`. glibc 2.12+ in case e_ident[EI_OSABI] == 3 treats this field as ABI version of the [dynamic linker](https://en.wikipedia.org/wiki/Dynamic_linker):<sup>[[7]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-7)</sup> it defines a list of dynamic linker's features,<sup>[[8]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-8)</sup> treats e_ident[EI_ABIVERSION] as a feature level requested by the shared object (executable or dynamic library) and refuses to load it if an unknown feature is requested, i.e. e_ident[EI_ABIVERSION] is greater than the largest known feature.<sup>[[9]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-9)</sup> |  |  |
| 0x09 | 7 | e_ident[EI_PAD] | Reserved padding bytes. Currently unused. Should be filled with zeros and ignored when read. |  |  |
| 0x10 | 2 | e_type | Identifies object file type. ValueTypeMeaning 0x00ET_NONEUnknown. 0x01ET_RELRelocatable file. 0x02ET_EXECExecutable file. 0x03ET_DYNShared object. 0x04ET_CORECore file. 0xFE00ET_LOOSReserved inclusive range. Operating system specific. 0xFEFFET_HIOS 0xFF00ET_LOPROCReserved inclusive range. Processor specific. 0xFFFFET_HIPROC |  |  |
| Value | Type | Meaning |  |  |  |
| 0x00 | ET_NONE | Unknown. |  |  |  |
| 0x01 | ET_REL | Relocatable file. |  |  |  |
| 0x02 | ET_EXEC | Executable file. |  |  |  |
| 0x03 | ET_DYN | Shared object. |  |  |  |
| 0x04 | ET_CORE | Core file. |  |  |  |
| 0xFE00 | ET_LOOS | Reserved inclusive range. Operating system specific. |  |  |  |
| 0xFEFF | ET_HIOS |  |  |  |  |
| 0xFF00 | ET_LOPROC | Reserved inclusive range. Processor specific. |  |  |  |
| 0xFFFF | ET_HIPROC |  |  |  |  |
| 0x12 | 2 | e_machine | Specifies target [instruction set architecture](https://en.wikipedia.org/wiki/Instruction_set_architecture). Some examples are: ValueISA 0x00No specific instruction set 0x01[AT&T WE 32100](https://en.wikipedia.org/wiki/Bellmac_32) 0x02[SPARC](https://en.wikipedia.org/wiki/SPARC) 0x03[x86](https://en.wikipedia.org/wiki/X86) 0x04[Motorola 68000 (M68k)](https://en.wikipedia.org/wiki/Motorola_68000_series) 0x05[Motorola 88000 (M88k)](https://en.wikipedia.org/wiki/Motorola_88000) 0x06[Intel MCU](https://en.wikipedia.org/wiki/List_of_Intel_processors#Microcontrollers) 0x07[Intel 80860](https://en.wikipedia.org/wiki/Intel_i860) 0x08[MIPS](https://en.wikipedia.org/wiki/MIPS_architecture) 0x09[IBM System/370](https://en.wikipedia.org/wiki/IBM_System/370) 0x0A[MIPS RS3000 Little-endian](https://en.wikipedia.org/wiki/R3000) 0x0B – 0x0EReserved for future use 0x0F[Hewlett-Packard PA-RISC](https://en.wikipedia.org/wiki/PA-RISC) 0x13[Intel 80960](https://en.wikipedia.org/wiki/Intel_i960) 0x14[PowerPC](https://en.wikipedia.org/wiki/PowerPC) 0x15[PowerPC](https://en.wikipedia.org/wiki/PowerPC) (64-bit) 0x16[S390](https://en.wikipedia.org/wiki/Z/Architecture), including S390x 0x17IBM SPU/SPC 0x18 – 0x23Reserved for future use 0x24[NEC V800](https://en.wikipedia.org/wiki/V850) 0x25Fujitsu FR20 0x26[TRW RH-32](https://en.wikipedia.org/wiki/RH-32) 0x27Motorola RCE 0x28[Arm](https://en.wikipedia.org/wiki/ARM_architecture_family) (up to Armv7/AArch32) 0x29[Digital Alpha](https://en.wikipedia.org/wiki/Digital_Alpha) 0x2A[SuperH](https://en.wikipedia.org/wiki/SuperH) 0x2B[SPARC Version 9](https://en.wikipedia.org/wiki/SPARC) 0x2C[Siemens TriCore embedded processor](https://en.wikipedia.org/wiki/Infineon_TriCore) 0x2D[Argonaut RISC Core](https://en.wikipedia.org/wiki/ARC_(processor)) 0x2E[Hitachi H8/300](https://en.wikipedia.org/wiki/H8_Family) 0x2F[Hitachi H8/300H](https://en.wikipedia.org/wiki/H8_Family) 0x30[Hitachi H8S](https://en.wikipedia.org/wiki/H8_Family) 0x31[Hitachi H8/500](https://en.wikipedia.org/wiki/H8_Family) 0x32[IA-64](https://en.wikipedia.org/wiki/IA-64) 0x33[Stanford MIPS-X](https://en.wikipedia.org/wiki/MIPS-X) 0x34[Motorola ColdFire](https://en.wikipedia.org/wiki/NXP_ColdFire) 0x35[Motorola M68HC12](https://en.wikipedia.org/wiki/Motorola_68HC12) 0x36Fujitsu MMA Multimedia Accelerator 0x37Siemens PCP 0x38[Sony nCPU embedded RISC processor](https://en.wikipedia.org/wiki/Cell_(microprocessor)) 0x39Denso NDR1 microprocessor 0x3AMotorola Star*Core processor 0x3BToyota ME16 processor 0x3CSTMicroelectronics ST100 processor 0x3DAdvanced Logic Corp. TinyJ embedded processor family 0x3E[AMD x86-64](https://en.wikipedia.org/wiki/Amd64) 0x3FSony DSP Processor 0x40[Digital Equipment Corp. PDP-10](https://en.wikipedia.org/wiki/PDP-10) 0x41[Digital Equipment Corp. PDP-11](https://en.wikipedia.org/wiki/PDP-11) 0x42Siemens FX66 microcontroller 0x43STMicroelectronics ST9+ 8/16-bit microcontroller 0x44STMicroelectronics ST7 8-bit microcontroller 0x45[Motorola MC68HC16 Microcontroller](https://en.wikipedia.org/wiki/Motorola_68HC16) 0x46[Motorola MC68HC11 Microcontroller](https://en.wikipedia.org/wiki/Motorola_68HC11) 0x47[Motorola MC68HC08 Microcontroller](https://en.wikipedia.org/wiki/Motorola_68HC08) 0x48[Motorola MC68HC05 Microcontroller](https://en.wikipedia.org/wiki/Motorola_68HC05) 0x49Silicon Graphics SVx 0x4ASTMicroelectronics ST19 8-bit microcontroller 0x4B[Digital VAX](https://en.wikipedia.org/wiki/VAX) 0x4CAxis Communications 32-bit embedded processor 0x4DInfineon Technologies 32-bit embedded processor 0x4EElement 14 64-bit DSP Processor 0x4FLSI Logic 16-bit DSP Processor 0x8C[TMS320C6000 Family](https://en.wikipedia.org/wiki/Texas_Instruments_TMS320#C6000_series) 0xAF[MCST Elbrus e2k](https://en.wikipedia.org/wiki/Elbrus_2000) 0xB7[Arm 64-bits](https://en.wikipedia.org/wiki/AArch64) (Armv8/AArch64) 0xDC[Zilog Z80](https://en.wikipedia.org/wiki/Zilog_Z80) 0xF3[RISC-V](https://en.wikipedia.org/wiki/RISC-V) 0xF7[Berkeley Packet Filter](https://en.wikipedia.org/wiki/Berkeley_Packet_Filter) 0x101 [WDC 65C816](https://en.wikipedia.org/wiki/WDC_65C816) 0x102 LoongArch |  |  |
| Value | ISA |  |  |  |  |
| 0x00 | No specific instruction set |  |  |  |  |
| 0x01 | [AT&T WE 32100](https://en.wikipedia.org/wiki/Bellmac_32) |  |  |  |  |
| 0x02 | [SPARC](https://en.wikipedia.org/wiki/SPARC) |  |  |  |  |
| 0x03 | [x86](https://en.wikipedia.org/wiki/X86) |  |  |  |  |
| 0x04 | [Motorola 68000 (M68k)](https://en.wikipedia.org/wiki/Motorola_68000_series) |  |  |  |  |
| 0x05 | [Motorola 88000 (M88k)](https://en.wikipedia.org/wiki/Motorola_88000) |  |  |  |  |
| 0x06 | [Intel MCU](https://en.wikipedia.org/wiki/List_of_Intel_processors#Microcontrollers) |  |  |  |  |
| 0x07 | [Intel 80860](https://en.wikipedia.org/wiki/Intel_i860) |  |  |  |  |
| 0x08 | [MIPS](https://en.wikipedia.org/wiki/MIPS_architecture) |  |  |  |  |
| 0x09 | [IBM System/370](https://en.wikipedia.org/wiki/IBM_System/370) |  |  |  |  |
| 0x0A | [MIPS RS3000 Little-endian](https://en.wikipedia.org/wiki/R3000) |  |  |  |  |
| 0x0B – 0x0E | Reserved for future use |  |  |  |  |
| 0x0F | [Hewlett-Packard PA-RISC](https://en.wikipedia.org/wiki/PA-RISC) |  |  |  |  |
| 0x13 | [Intel 80960](https://en.wikipedia.org/wiki/Intel_i960) |  |  |  |  |
| 0x14 | [PowerPC](https://en.wikipedia.org/wiki/PowerPC) |  |  |  |  |
| 0x15 | [PowerPC](https://en.wikipedia.org/wiki/PowerPC) (64-bit) |  |  |  |  |
| 0x16 | [S390](https://en.wikipedia.org/wiki/Z/Architecture), including S390x |  |  |  |  |
| 0x17 | IBM SPU/SPC |  |  |  |  |
| 0x18 – 0x23 | Reserved for future use |  |  |  |  |
| 0x24 | [NEC V800](https://en.wikipedia.org/wiki/V850) |  |  |  |  |
| 0x25 | Fujitsu FR20 |  |  |  |  |
| 0x26 | [TRW RH-32](https://en.wikipedia.org/wiki/RH-32) |  |  |  |  |
| 0x27 | Motorola RCE |  |  |  |  |
| 0x28 | [Arm](https://en.wikipedia.org/wiki/ARM_architecture_family) (up to Armv7/AArch32) |  |  |  |  |
| 0x29 | [Digital Alpha](https://en.wikipedia.org/wiki/Digital_Alpha) |  |  |  |  |
| 0x2A | [SuperH](https://en.wikipedia.org/wiki/SuperH) |  |  |  |  |
| 0x2B | [SPARC Version 9](https://en.wikipedia.org/wiki/SPARC) |  |  |  |  |
| 0x2C | [Siemens TriCore embedded processor](https://en.wikipedia.org/wiki/Infineon_TriCore) |  |  |  |  |
| 0x2D | [Argonaut RISC Core](https://en.wikipedia.org/wiki/ARC_(processor)) |  |  |  |  |
| 0x2E | [Hitachi H8/300](https://en.wikipedia.org/wiki/H8_Family) |  |  |  |  |
| 0x2F | [Hitachi H8/300H](https://en.wikipedia.org/wiki/H8_Family) |  |  |  |  |
| 0x30 | [Hitachi H8S](https://en.wikipedia.org/wiki/H8_Family) |  |  |  |  |
| 0x31 | [Hitachi H8/500](https://en.wikipedia.org/wiki/H8_Family) |  |  |  |  |
| 0x32 | [IA-64](https://en.wikipedia.org/wiki/IA-64) |  |  |  |  |
| 0x33 | [Stanford MIPS-X](https://en.wikipedia.org/wiki/MIPS-X) |  |  |  |  |
| 0x34 | [Motorola ColdFire](https://en.wikipedia.org/wiki/NXP_ColdFire) |  |  |  |  |
| 0x35 | [Motorola M68HC12](https://en.wikipedia.org/wiki/Motorola_68HC12) |  |  |  |  |
| 0x36 | Fujitsu MMA Multimedia Accelerator |  |  |  |  |
| 0x37 | Siemens PCP |  |  |  |  |
| 0x38 | [Sony nCPU embedded RISC processor](https://en.wikipedia.org/wiki/Cell_(microprocessor)) |  |  |  |  |
| 0x39 | Denso NDR1 microprocessor |  |  |  |  |
| 0x3A | Motorola Star*Core processor |  |  |  |  |
| 0x3B | Toyota ME16 processor |  |  |  |  |
| 0x3C | STMicroelectronics ST100 processor |  |  |  |  |
| 0x3D | Advanced Logic Corp. TinyJ embedded processor family |  |  |  |  |
| 0x3E | [AMD x86-64](https://en.wikipedia.org/wiki/Amd64) |  |  |  |  |
| 0x3F | Sony DSP Processor |  |  |  |  |
| 0x40 | [Digital Equipment Corp. PDP-10](https://en.wikipedia.org/wiki/PDP-10) |  |  |  |  |
| 0x41 | [Digital Equipment Corp. PDP-11](https://en.wikipedia.org/wiki/PDP-11) |  |  |  |  |
| 0x42 | Siemens FX66 microcontroller |  |  |  |  |
| 0x43 | STMicroelectronics ST9+ 8/16-bit microcontroller |  |  |  |  |
| 0x44 | STMicroelectronics ST7 8-bit microcontroller |  |  |  |  |
| 0x45 | [Motorola MC68HC16 Microcontroller](https://en.wikipedia.org/wiki/Motorola_68HC16) |  |  |  |  |
| 0x46 | [Motorola MC68HC11 Microcontroller](https://en.wikipedia.org/wiki/Motorola_68HC11) |  |  |  |  |
| 0x47 | [Motorola MC68HC08 Microcontroller](https://en.wikipedia.org/wiki/Motorola_68HC08) |  |  |  |  |
| 0x48 | [Motorola MC68HC05 Microcontroller](https://en.wikipedia.org/wiki/Motorola_68HC05) |  |  |  |  |
| 0x49 | Silicon Graphics SVx |  |  |  |  |
| 0x4A | STMicroelectronics ST19 8-bit microcontroller |  |  |  |  |
| 0x4B | [Digital VAX](https://en.wikipedia.org/wiki/VAX) |  |  |  |  |
| 0x4C | Axis Communications 32-bit embedded processor |  |  |  |  |
| 0x4D | Infineon Technologies 32-bit embedded processor |  |  |  |  |
| 0x4E | Element 14 64-bit DSP Processor |  |  |  |  |
| 0x4F | LSI Logic 16-bit DSP Processor |  |  |  |  |
| 0x8C | [TMS320C6000 Family](https://en.wikipedia.org/wiki/Texas_Instruments_TMS320#C6000_series) |  |  |  |  |
| 0xAF | [MCST Elbrus e2k](https://en.wikipedia.org/wiki/Elbrus_2000) |  |  |  |  |
| 0xB7 | [Arm 64-bits](https://en.wikipedia.org/wiki/AArch64) (Armv8/AArch64) |  |  |  |  |
| 0xDC | [Zilog Z80](https://en.wikipedia.org/wiki/Zilog_Z80) |  |  |  |  |
| 0xF3 | [RISC-V](https://en.wikipedia.org/wiki/RISC-V) |  |  |  |  |
| 0xF7 | [Berkeley Packet Filter](https://en.wikipedia.org/wiki/Berkeley_Packet_Filter) |  |  |  |  |
| 0x101 | [WDC 65C816](https://en.wikipedia.org/wiki/WDC_65C816) |  |  |  |  |
| 0x102 | LoongArch |  |  |  |  |
| 0x14 | 4 | e_version | Set to `1` for the original version of ELF. |  |  |
| 0x18 | 4 | 8 | e_entry | This is the memory address of the [entry point](https://en.wikipedia.org/wiki/Entry_point) from where the process starts executing. This field is either 32 or 64 bits long, depending on the format defined earlier (byte 0x04). If the file doesn't have an associated entry point, then this holds zero. |  |
| 0x1C | 0x20 | 4 | 8 | e_phoff | Points to the start of the program header table. It usually follows the file header immediately following this one, making the offset `0x34` or `0x40` for 32- and 64-bit ELF executables, respectively. |
| 0x20 | 0x28 | 4 | 8 | e_shoff | Points to the start of the section header table. |
| 0x24 | 0x30 | 4 | e_flags | Interpretation of this field depends on the target architecture. |  |
| 0x28 | 0x34 | 2 | e_ehsize | Contains the size of this header, normally 64 Bytes for 64-bit and 52 Bytes for 32-bit format. |  |
| 0x2A | 0x36 | 2 | e_phentsize | Contains the size of a program header table entry. As explained below, this will typically be 0x20 (32-bit) or 0x38 (64-bit). |  |
| 0x2C | 0x38 | 2 | e_phnum | Contains the number of entries in the program header table. |  |
| 0x2E | 0x3A | 2 | e_shentsize | Contains the size of a section header table entry. As explained below, this will typically be 0x28 (32-bit) or 0x40 (64-bit). |  |
| 0x30 | 0x3C | 2 | e_shnum | Contains the number of entries in the section header table. |  |
| 0x32 | 0x3E | 2 | e_shstrndx | Contains index of the section header table entry that contains the section names. |  |
| 0x34 | 0x40 |  | End of ELF Header (size). |  |  |

<sup>[[10]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-10)</sup>

### Program header

The program header table tells the system how to create a process image. It is found at file offset e_phoff, and consists of e_phnum entries, each with size e_phentsize. The layout is slightly different in [32-bit](https://en.wikipedia.org/wiki/32-bit) ELF vs [64-bit](https://en.wikipedia.org/wiki/64-bit) ELF, because the p_flags are in a different structure location for alignment reasons. Each entry is structured as:

| Offset | Size (bytes) | Field | Purpose |  |  |
| --- | --- | --- | --- | --- | --- |
| 32-bit | 64-bit | 32-bit | 64-bit |  |  |
| 0x00 | 4 | p_type | Identifies the type of the segment. ValueNameMeaning 0x00000000PT_NULL Program header table entry unused. 0x00000001PT_LOAD Loadable segment. 0x00000002PT_DYNAMIC Dynamic linking information. 0x00000003PT_INTERP Interpreter information. 0x00000004PT_NOTE Auxiliary information. 0x00000005PT_SHLIB Reserved. 0x00000006PT_PHDR Segment containing program header table itself. 0x00000007PT_TLS Thread-Local Storage template. 0x60000000PT_LOOS Reserved inclusive range. Operating system specific. 0x6FFFFFFFPT_HIOS 0x70000000PT_LOPROC Reserved inclusive range. Processor specific. 0x7FFFFFFFPT_HIPROC |  |  |
| Value | Name | Meaning |  |  |  |
| 0x00000000 | PT_NULL | Program header table entry unused. |  |  |  |
| 0x00000001 | PT_LOAD | Loadable segment. |  |  |  |
| 0x00000002 | PT_DYNAMIC | Dynamic linking information. |  |  |  |
| 0x00000003 | PT_INTERP | Interpreter information. |  |  |  |
| 0x00000004 | PT_NOTE | Auxiliary information. |  |  |  |
| 0x00000005 | PT_SHLIB | Reserved. |  |  |  |
| 0x00000006 | PT_PHDR | Segment containing program header table itself. |  |  |  |
| 0x00000007 | PT_TLS | Thread-Local Storage template. |  |  |  |
| 0x60000000 | PT_LOOS | Reserved inclusive range. Operating system specific. |  |  |  |
| 0x6FFFFFFF | PT_HIOS |  |  |  |  |
| 0x70000000 | PT_LOPROC | Reserved inclusive range. Processor specific. |  |  |  |
| 0x7FFFFFFF | PT_HIPROC |  |  |  |  |
|  | 0x04 |  | 4 | p_flags | Segment-dependent flags (position for 64-bit structure). Value Name Meaning 0x1 PF_X Executable segment. 0x2 PF_W Writeable segment. 0x4 PF_R Readable segment. |
| Value | Name | Meaning |  |  |  |
| 0x1 | PF_X | Executable segment. |  |  |  |
| 0x2 | PF_W | Writeable segment. |  |  |  |
| 0x4 | PF_R | Readable segment. |  |  |  |
| 0x04 | 0x08 | 4 | 8 | p_offset | Offset of the segment in the file image. |
| 0x08 | 0x10 | 4 | 8 | p_vaddr | Virtual address of the segment in memory. |
| 0x0C | 0x18 | 4 | 8 | p_paddr | On systems where physical address is relevant, reserved for segment's physical address. |
| 0x10 | 0x20 | 4 | 8 | p_filesz | Size in bytes of the segment in the file image. May be 0. |
| 0x14 | 0x28 | 4 | 8 | p_memsz | Size in bytes of the segment in memory. May be 0. |
| 0x18 |  | 4 |  | p_flags | Segment-dependent flags (position for 32-bit structure). See above `p_flags` field for flag definitions. |
| 0x1C | 0x30 | 4 | 8 | p_align | `0` and `1` specify no alignment. Otherwise should be a positive, integral power of 2, with p_vaddr equating p_offset, modulus p_align. |
| 0x20 | 0x38 |  | End of Program Header (size). |  |  |

### Section header

| Offset | Size (bytes) | Field | Purpose |  |  |
| --- | --- | --- | --- | --- | --- |
| 32-bit | 64-bit | 32-bit | 64-bit |  |  |
| 0x00 | 4 | sh_name | An offset to a string in the **.shstrtab** section that represents the name of this section. |  |  |
| 0x04 | 4 | sh_type | Identifies the type of this header. Value Name Meaning 0x0 SHT_NULL Section header table entry unused 0x1 SHT_PROGBITS Program data 0x2 SHT_SYMTAB Symbol table 0x3 SHT_STRTAB String table 0x4 SHT_RELA Relocation entries with addends 0x5 SHT_HASH Symbol hash table 0x6 SHT_DYNAMIC Dynamic linking information 0x7 SHT_NOTE Notes 0x8 SHT_NOBITS Program space with no data (bss) 0x9 SHT_REL Relocation entries, no addends 0x0A SHT_SHLIB Reserved 0x0B SHT_DYNSYM Dynamic linker symbol table 0x0E SHT_INIT_ARRAY Array of constructors 0x0F SHT_FINI_ARRAY Array of destructors 0x10 SHT_PREINIT_ARRAY Array of pre-constructors 0x11 SHT_GROUP Section group 0x12 SHT_SYMTAB_SHNDX Extended section indices 0x13 SHT_NUM Number of defined types. 0x60000000 SHT_LOOS Start OS-specific. ... ... ... |  |  |
| Value | Name | Meaning |  |  |  |
| 0x0 | SHT_NULL | Section header table entry unused |  |  |  |
| 0x1 | SHT_PROGBITS | Program data |  |  |  |
| 0x2 | SHT_SYMTAB | Symbol table |  |  |  |
| 0x3 | SHT_STRTAB | String table |  |  |  |
| 0x4 | SHT_RELA | Relocation entries with addends |  |  |  |
| 0x5 | SHT_HASH | Symbol hash table |  |  |  |
| 0x6 | SHT_DYNAMIC | Dynamic linking information |  |  |  |
| 0x7 | SHT_NOTE | Notes |  |  |  |
| 0x8 | SHT_NOBITS | Program space with no data (bss) |  |  |  |
| 0x9 | SHT_REL | Relocation entries, no addends |  |  |  |
| 0x0A | SHT_SHLIB | Reserved |  |  |  |
| 0x0B | SHT_DYNSYM | Dynamic linker symbol table |  |  |  |
| 0x0E | SHT_INIT_ARRAY | Array of constructors |  |  |  |
| 0x0F | SHT_FINI_ARRAY | Array of destructors |  |  |  |
| 0x10 | SHT_PREINIT_ARRAY | Array of pre-constructors |  |  |  |
| 0x11 | SHT_GROUP | Section group |  |  |  |
| 0x12 | SHT_SYMTAB_SHNDX | Extended section indices |  |  |  |
| 0x13 | SHT_NUM | Number of defined types. |  |  |  |
| 0x60000000 | SHT_LOOS | Start OS-specific. |  |  |  |
| ... | ... | ... |  |  |  |
| 0x08 | 4 | 8 | sh_flags | Identifies the attributes of the section. Value Name Meaning 0x1 SHF_WRITE Writable 0x2 SHF_ALLOC Occupies memory during execution 0x4 SHF_EXECINSTR Executable 0x10 SHF_MERGE Might be merged 0x20 SHF_STRINGS Contains null-terminated strings 0x40 SHF_INFO_LINK 'sh_info' contains SHT index 0x80 SHF_LINK_ORDER Preserve order after combining 0x100 SHF_OS_NONCONFORMING Non-standard OS specific handling required 0x200 SHF_GROUP Section is member of a group 0x400 SHF_TLS Section hold thread-local data 0x0FF00000 SHF_MASKOS OS-specific 0xF0000000 SHF_MASKPROC Processor-specific 0x4000000 SHF_ORDERED Special ordering requirement (Solaris) 0x8000000 SHF_EXCLUDE Section is excluded unless referenced or allocated (Solaris) |  |
| Value | Name | Meaning |  |  |  |
| 0x1 | SHF_WRITE | Writable |  |  |  |
| 0x2 | SHF_ALLOC | Occupies memory during execution |  |  |  |
| 0x4 | SHF_EXECINSTR | Executable |  |  |  |
| 0x10 | SHF_MERGE | Might be merged |  |  |  |
| 0x20 | SHF_STRINGS | Contains null-terminated strings |  |  |  |
| 0x40 | SHF_INFO_LINK | 'sh_info' contains SHT index |  |  |  |
| 0x80 | SHF_LINK_ORDER | Preserve order after combining |  |  |  |
| 0x100 | SHF_OS_NONCONFORMING | Non-standard OS specific handling required |  |  |  |
| 0x200 | SHF_GROUP | Section is member of a group |  |  |  |
| 0x400 | SHF_TLS | Section hold thread-local data |  |  |  |
| 0x0FF00000 | SHF_MASKOS | OS-specific |  |  |  |
| 0xF0000000 | SHF_MASKPROC | Processor-specific |  |  |  |
| 0x4000000 | SHF_ORDERED | Special ordering requirement (Solaris) |  |  |  |
| 0x8000000 | SHF_EXCLUDE | Section is excluded unless referenced or allocated (Solaris) |  |  |  |
| 0x0C | 0x10 | 4 | 8 | sh_addr | Virtual address of the section in memory, for sections that are loaded. |
| 0x10 | 0x18 | 4 | 8 | sh_offset | Offset of the section in the file image. |
| 0x14 | 0x20 | 4 | 8 | sh_size | Size in bytes of the section. May be 0. |
| 0x18 | 0x28 | 4 | sh_link | Contains the section index of an associated section. This field is used for several purposes, depending on the type of section. |  |
| 0x1C | 0x2C | 4 | sh_info | Contains extra information about the section. This field is used for several purposes, depending on the type of section. |  |
| 0x20 | 0x30 | 4 | 8 | sh_addralign | Contains the required alignment of the section. This field must be a power of two. |
| 0x24 | 0x38 | 4 | 8 | sh_entsize | Contains the size, in bytes, of each entry, for sections that contain fixed-size entries. Otherwise, this field contains zero. |
| 0x28 | 0x40 |  | End of Section Header (size). |  |  |

## Tools

- [readelf](https://en.wikipedia.org/wiki/Readelf) is a Unix binary utility that displays information about one or more ELF files. A free software implementation is provided by GNU Binutils.
- elfutils provides alternative tools to GNU Binutils purely for Linux.[[12]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-12)
- elfdump is a command for viewing ELF information in an ELF file, available under Solaris and FreeBSD.
- [objdump](https://en.wikipedia.org/wiki/Objdump) provides a wide range of information about ELF files and other object formats. objdump uses the Binary File Descriptor library as a back-end to structure the ELF data.
- The Unix [file](https://en.wikipedia.org/wiki/File_(command)) utility can display some information about ELF files, including the instruction set architecture for which the code in a relocatable, executable, or shared object file is intended, or on which an ELF core dump was produced.

## Applications

### Unix-like systems

ELF has also seen some adoption in non-Unix operating systems, such as:

- OpenVMS, in its Itanium and amd64 versions[[15]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-15)
- BeOS Revision 4 and later for x86 based computers (where it replaced the Portable Executable format; the PowerPC version stayed with Preferred Executable Format)
- Haiku, an open source reimplementation of BeOS
- RISC OS[[16]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-16)
- Stratus VOS, in PA-RISC and x86 versions
- SkyOS
- Fuchsia OS
- Z/TPF
- HPE NonStop OS[[17]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-17)
- Deos

[Microsoft Windows](https://en.wikipedia.org/wiki/Microsoft_Windows) also uses the ELF format, but only for its [Windows Subsystem for Linux](https://en.wikipedia.org/wiki/Windows_Subsystem_for_Linux) compatibility system.<sup>[[18]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-18)</sup>

### Game consoles

Some game consoles also use ELF:

- PlayStation Portable,[[19]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-19) PlayStation Vita, PlayStation[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*], PlayStation 2, PlayStation 3, PlayStation 4, PlayStation 5
- GP2X
- Dreamcast
- GameCube
- Nintendo 64[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*]
- Wii
- Wii U

### PowerPC

Other (operating) systems running on PowerPC that use ELF:

- AmigaOS 4, the ELF executable has replaced the prior Extended Hunk Format (EHF) which was used on Amigas equipped with PPC processor expansion cards.
- MorphOS
- AROS
- Café OS (The operating system run by the Wii U)

### Mobile phones

Some operating systems for mobile phones and mobile devices use ELF:

- Symbian OS v9 uses E32Image[[20]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-20) format that is based on the ELF file format;
- Sony Ericsson, for example, the W800i, W610, W300, etc.
- Siemens, the SGOLD and SGOLD2 platforms: from Siemens C65 to S75 and BenQ-Siemens E71/EL71;
- Motorola, for example, the E398, SLVR L7, v360, v3i (and all phone LTE2 which has the patch applied).
- Bada, for example, the Samsung Wave S8500.
- Nokia phones or tablets running the Maemo or the Meego OS, for example, the Nokia N900.
- Android uses ELF .so (shared object[[21]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-21)) libraries for the Java Native Interface.[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*] With Android Runtime (ART), the default since Android 5.0 "Lollipop", all applications are compiled into native ELF binaries on installation.[[22]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-22) It's also possible to use native Linux software from package managers like Termux, or compile them from sources via Clang or GCC, that are available in repositories.

Some phones can run ELF files through the use of a patch that adds assembly code to the main firmware, which is a feature known as *ELFPack* in the underground modding culture. The ELF file format is also used with the [Atmel AVR](https://en.wikipedia.org/wiki/Atmel_AVR) (8-bit), AVR32<sup>[[23]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-23)</sup>
and with Texas Instruments MSP430 microcontroller architectures. Some implementations of Open Firmware can also load ELF files, most notably Apple's implementation used in almost all PowerPC machines the company produced.

- Solana uses ELF format for its on-chain programs (smart contracts). The platform processes ELF files compiled to BPF (Berkeley Packet Filter) byte-code, which are then deployed as shared objects and executed in Solana's runtime environment. The BPF loader validates and processes these ELF files during program deployment.[[24]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-24)

## Specifications

The [Linux Standard Base](https://en.wikipedia.org/wiki/Linux_Standard_Base) (LSB) supplements some of the above specifications for architectures in which it is specified.<sup>[[25]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-25)</sup> For example, that is the case for the System V ABI, AMD64 Supplement.<sup>[[26]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-26)</sup><sup>[[27]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-27)</sup>

## 86open

**86open** was a project to form consensus on a common binary file format for Unix and Unix-like operating systems on the common PC compatible x86 architecture, to encourage software developers to port to the architecture.<sup>[[28]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-28)</sup> The initial idea was to standardize on a small subset of Spec 1170, a predecessor of the Single UNIX Specification, and the GNU C Library (glibc) to enable unmodified binaries to run on the x86 Unix-like operating systems. The project was originally designated "Spec 150".

The format eventually chosen was ELF, specifically the Linux implementation of ELF, after it had turned out to be a *de facto* standard supported by all involved vendors and operating systems.

The group began email discussions in 1997 and first met together at the Santa Cruz Operation offices on August 22, 1997.

The steering committee was Marc Ewing, Dion Johnson, Evan Leibovitch, [Bruce Perens](https://en.wikipedia.org/wiki/Bruce_Perens), Andrew Roach, Bryan Wayne Sparks and Linus Torvalds. Other people on the project were Keith Bostic, Chuck Cranor, Michael Davidson,At least three other Michael Davidsons in WP as of 04.2007 Chris G. Demetriou, Ulrich Drepper, Don Dugger, Steve Ginzburg, Jon "maddog" Hall, Ron Holt, Jordan Hubbard, Dave Jensen, Kean Johnston, Andrew Josey, Robert Lipe, Bela Lubkin, Tim Marsland, Greg Page,Three other people by that name in WP as of 04.2007 Ronald Joe Record, Tim Ruckle, Joel Silverstein, Chia-pi Tien, and Erik Troan. Operating systems and companies represented were BeOS, BSDI, FreeBSD, [Intel](https://en.wikipedia.org/wiki/Intel), Linux, NetBSD, SCO and SunSoft.

The project progressed and in mid-1998, SCO began developing lxrun, an open-source compatibility layer able to run Linux binaries on OpenServer, UnixWare, and Solaris. SCO announced official support of lxrun at LinuxWorld in March 1999. Sun Microsystems began officially supporting lxrun for Solaris in early 1999,<sup>[[29]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-29)</sup> and later moved to integrated support of the Linux binary format via Solaris Containers for Linux Applications.

With the BSDs having long supported Linux binaries (through a compatibility layer) and the main x86 Unix vendors having added support for the format, the project decided that Linux ELF was the format chosen by the industry and "declare[d] itself dissolved" on July 25, 1999.<sup>[[30]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-30)</sup>

- [![icon](https://thumb.wikimedia.org/wikipedia/commons/thumb/6/6f/Octicons-terminal.svg/60px-Octicons-terminal.svg.png?utm_source=en.wikipedia.org&utm_campaign=parser&utm_content=thumbnail)](https://en.wikipedia.org/wiki/File:Octicons-terminal.svg)[Computer programming portal](https://en.wikipedia.org/wiki/Portal:Computer_programming)

- Application binary interface
- Comparison of executable file formats
- DWARF – a format for debugging data
- Intel Binary Compatibility Standard
- Portable Executable – format used by Windows
- vDSO – virtual DSO
- Position-independent code

1. [1](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-linuxbase-elf_1-0) [2](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-linuxbase-elf_1-1) Tool Interface Standard (TIS) *[Executable and Linking Format (ELF) Specification](https://refspecs.linuxbase.org/elf/elf.pdf) Version 1.2* (May 1995)
2. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-2) [ELF Object File Format: Appendix C: Revision History](https://gabi.xinuos.com/elf/c-history.html)
3. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-linuxfoundation-elf_3-0) Tool Interface Standard (TIS) *[Portable Formats Specification](https://refspecs.linuxfoundation.org/elf/TIS1.1.pdf) Version 1.1* (October 1993)
4. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-4) *[System V Application Binary Interface](https://www.sco.com/developers/devspecs/gabi41.pdf)* Edition 4.1 (1997-03-18)
5. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-5) ["ELF Header"](https://www.sco.com/developers/gabi/2000-07-17/ch4.eheader.html). Sco.com. July 2000. Retrieved 2014-02-07.
6. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-6) ["LXR linux/include/linux/elf.h"](http://lxr.linux.no/linux+v2.6.11/include/linux/elf.h#L380). *linux.no*. Retrieved 27 April 2015.
7. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-7) ["glibc 2.12 announce"](https://sourceware.org/ml/libc-alpha/2010-05/msg00000.html).
8. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-8) ["sourceware.org Git - glibc.git/blob - libc-abis"](https://sourceware.org/git/?p=glibc.git;a=blob;f=libc-abis;h=e702f6ae245c1528f5a608df8cfae4f037809de2;hb=HEAD).
9. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-9) ["sourceware.org Git - glibc.git/blob - sysdeps/gnu/ldsodefs.h"](https://web.archive.org/web/20210307223850/https://sourceware.org/git/?p=glibc.git%3Ba%3Dblob%3Bf%3Dsysdeps%2Fgnu%2Fldsodefs.h%3Bh%3D253b4d934c5ca457ab5580a2a6398205e4f961ba%3Bhb%3DHEAD#l32). Archived from [the original](https://sourceware.org/git/?p=glibc.git%3Ba%3Dblob%3Bf%3Dsysdeps%2Fgnu%2Fldsodefs.h%3Bh%3D253b4d934c5ca457ab5580a2a6398205e4f961ba%3Bhb%3DHEAD#l32) on 2021-03-07. Retrieved 2019-10-28.
10. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-10) ["Available lexers — Pygments"](https://pygments.org/docs/lexers/#lexers-for-hexadecimal-dumps). *pygments.org*. Retrieved 2024-12-19.
11. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-11) ["Program Header"](http://www.sco.com/developers/gabi/2000-07-17/ch5.pheader.html). Sco.com. July 2000. Retrieved 2017-04-05.
12. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-12) ["elfutils"](https://sourceware.org/elfutils/). *sourceware.org*. Retrieved 30 April 2017.
13. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-13) ["Binary Formats"](https://web.archive.org/web/20190331192807/https://docs.freebsd.org/doc/4.9-RELEASE/usr/share/doc/handbook/binary-formats.html). Archived from [the original](https://docs.freebsd.org/doc/4.9-RELEASE/usr/share/doc/handbook/binary-formats.html) on 2019-03-31. Retrieved 2019-03-31.
14. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-14) ["MinixReleases – Minix Wiki"](https://web.archive.org/web/20130330150621/http://wiki.minix3.org/en/MinixReleases). Wiki.minix3.org. Archived from [the original](http://wiki.minix3.org/en/MinixReleases) on 2013-03-30. Retrieved 2014-01-19.
15. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-15) ["State of the Port to x86_64"](https://web.archive.org/web/20200915215111/https://vmssoftware.com/pdfs/State_of_Port_20160906.pdf) (PDF). Archived from [the original](https://vmssoftware.com/pdfs/State_of_Port_20160906.pdf) (PDF) on 2020-09-15. Retrieved 2016-10-19.
16. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-16) ["GCCSDK – RISC OS"](https://web.archive.org/web/20140219211405/http://www.riscos.info/index.php/GCCSDK). Riscos.info. 2012-04-22. Archived from [the original](http://www.riscos.info/index.php/GCCSDK) on 2014-02-19. Retrieved 2014-01-19.
17. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-17) ["Guardian Programmer's Guide"](https://web.archive.org/web/20180530042640/http://h20628.www2.hp.com/km-ext/kmcsdirect/emr_na-c02543407-12.pdf) (PDF). Hewlett Packard Enterprise. Archived from [the original](http://h20628.www2.hp.com/km-ext/kmcsdirect/emr_na-c02543407-12.pdf) (PDF) on 2018-05-30. Retrieved 2018-05-30. p. 44 archived from [the original](http://h20628.www2.hp.com/km-ext/kmcsdirect/emr_na-c02543407-12.pdf) [Archived](https://web.archive.org/web/20180530042640/http://h20628.www2.hp.com/km-ext/kmcsdirect/emr_na-c02543407-12.pdf) 2018-05-30 at the [Wayback Machine](https://en.wikipedia.org/wiki/Wayback_Machine) on 2018-5-30
18. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-18) Foley, Mary Jo. ["Under the hood of Microsoft's Windows Subsystem for Linux"](https://www.zdnet.com/article/under-the-hood-of-microsofts-windows-subsystem-for-linux/). *ZDNet*. Retrieved 2016-08-19.
19. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-19) PlayStation Portable use encrypted & relocated ELF : PSP
20. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-20) *[Symbian OS executable file format](https://web.archive.org/web/20091213034509/http://wiki.forum.nokia.com/index.php/E32Image)*
21. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-21) Rosen, Kenneth; Host, Douglas; Klee, Rachel; Rosinski, Richard (2007). [*UNIX: The Complete Reference*](https://books.google.com/books?id=2Et--84HIkwC) (2 ed.). McGraw Hill Professional. p. 707. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [9780071706988](https://en.wikipedia.org/wiki/Special:BookSources/9780071706988). Retrieved 2017-06-08. Dynamically linked libraries are also called shared objects (.so).
22. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-22) Thomas, Romain. ["Android formats"](https://lief-project.github.io/doc/latest/tutorials/10_android_formats.html). *Quarks Lab*. Retrieved 17 Jan 2023.`{{cite web}}`: CS1 maint: deprecated archival service ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_deprecated_archival_service))
23. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-23) ["Chapter 4: Object Files"](http://www.sco.com/developers/gabi/2009-10-26/ch4.eheader.html#e_machine), *System V Application Binary Interface*, 2009-10-26, e_machine
24. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-24) ["Solana Programs"](https://solana.com/docs/core/programs). Solana Foundation. 2024-11-11. Retrieved 2024-11-11. Solana leverages the LLVM compiler infrastructure to compile programs into Executable and Linkable Format (ELF) files.
25. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-25) ["LSB Referenced Specifications"](http://refspecs.linuxfoundation.org/lsb.shtml). *linuxfoundation.org*. Retrieved 27 April 2015.
26. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-26) ["Executable and Linking Format (ELF)"](http://refspecs.linuxfoundation.org/LSB_4.1.0/LSB-Core-AMD64/LSB-Core-AMD64/elf-amd64.html). *linuxfoundation.org*. Retrieved 27 April 2015.
27. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-27) ["Introduction"](http://refspecs.linuxfoundation.org/LSB_4.1.0/LSB-Core-AMD64/LSB-Core-AMD64/elfintro.html). *linuxfoundation.org*. Retrieved 27 April 2015.
28. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-28) Leibovitch, Evan (1997-12-23). ["86Open Frequently-Asked Questions"](https://web.archive.org/web/20070311032337/http://www.telly.org/86open-faq). Archived from [the original](http://www.telly.org/86open-faq) on 2007-03-11. Retrieved 2007-06-06.
29. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-29) Record, Ronald (1998-05-21). ["Bulletin on status of 86open at SCO"](https://web.archive.org/web/20081208013909/http://www.mavetju.org/mail/view_message.php?list=freebsd-emulation&id=361608). Archived from [the original](http://www.mavetju.org/mail/view_message.php?list=freebsd-emulation&id=361608) on 2008-12-08. Retrieved 2008-05-06.
30. [↑](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_ref-30) Leibovitch, Evan (1999-07-25). ["The86open Project – Final Update"](https://web.archive.org/web/20070227214032/http://www.telly.org/86open/). Archived from [the original](https://www.telly.org/86open/) on 2007-02-27. Retrieved 2007-05-06.

- Evolution of the ELF object file format, by Fangrui Song.
- [Levine, John R.](https://en.wikipedia.org/wiki/John_R._Levine) (2000) [October 1999]. [*Linkers and Loaders*](https://www.iecc.com/linker/). The Morgan Kaufmann Series in Software Engineering and Programming (1 ed.). San Francisco, USA: [Morgan Kaufmann](https://en.wikipedia.org/wiki/Morgan_Kaufmann). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [1-55860-496-0](https://en.wikipedia.org/wiki/Special:BookSources/1-55860-496-0). [OCLC](https://en.wikipedia.org/wiki/OCLC_(identifier)) [42413382](https://search.worldcat.org/oclc/42413382). Retrieved 2020-01-12.`{{cite book}}`: CS1 maint: deprecated archival service ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_deprecated_archival_service)) Code:[[1]](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#cite_note-31)[*[dead link](https://en.wikipedia.org/wiki/Wikipedia:Link_rot)*] Errata:
- Ulrich Drepper, How To Write Shared Libraries, Version 4.1.2 (2011). Published on the author's web page, https://www.akkadia.org/drepper.
- [An unsung hero: The hardworking ELF](https://web.archive.org/web/20070224140341/http://www-128.ibm.com/developerworks/power/library/pa-spec12/) by Peter Seebach, December 20, 2005, archived from the original on February 24, 2007
- LibElf and GElf – A Library to Manipulate ELf Files at the Wayback Machine (archived February 25, 2004)
- [The ELF Object File Format: Introduction](https://www.linuxjournal.com/article/1059), [The ELF Object File Format by Dissection](https://www.linuxjournal.com/article/1060) by Eric Youngdale (1995-05-01)
- [A Whirlwind Tutorial on Creating Really Teensy ELF Executables for Linux](https://www.muppetlabs.com/~breadbox/software/tiny/teensy.html) by Brian Raiter
- ELF relocation into non-relocatable objects by Julien Vanegue (2003-08-13)
- Embedded ELF debugging without ptrace by the ELFsh team (2005-08-01)
- [Study of ELF loading and relocs](https://netwinder.osuosl.org/users/p/patb/public_html/elf_relocs.html) by Pat Beirne (1999-08-03)
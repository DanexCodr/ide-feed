Patching bugs does not scale anymore. New vulnerabilities are getting disclosed at an exponential rate, and it can feel like all software is getting hacked at once. At Tinfoil, we’ve been thinking hard about what we can do to create a more principled approach to hardening software systems, especially when it comes to the most important parts of our stack. In our case, one critical piece of software is the firmware for our virtual machines, which plays a central role in the verifiability and security of all of our infrastructure.

The firmware sets up our secure enclave environments using configurations provided by the host. Since the host is controlled by Tinfoil, it is untrusted under our threat model, which means that the firmware code needs to be firmly hardened to prevent host-side exploits.

Previously, we relied on the widely used open-source [OVMF](https://www.tianocore.org/tianocore-wiki.github.io/platforms-packages/platform-ports/ovmf.html) firmware. However, we found that most of OVMF’s functionality was not necessary for our purposes. We could move almost all of the essential functionality to our build system, where it becomes easier to audit and verify. This removed almost all responsibility from the very security-critical part of the stack and allowed us to fully replace OVMF. We deleted 1M lines of C in favor of ~300 lines of open-source assembly and zero dependencies.

We think this is what designing secure systems will increasingly look like.

## The new approach to securing software

In the days of yore, using a large, trusted open-source codebase was the way to go, because only popularity could bring enough eyeballs to a project to make it legitimate from a security standpoint. That led to a concentration of open-source projects (e.g., OVMF for virtual firmware) that had to work for everyone. There was both a tension and a symbiotic relationship between security and feature completeness. It used to be that feature completeness equated to greater popularity, which equated to more eyeballs, which equated to better security. But the larger surface area also introduced more bugs.

In this new age, LLMs provide us with more “artificial eyeballs” than ever to scrutinize software. This makes it easier to write small, purpose-built software that doesn’t have to support every platform, and to test and fuzz it for security continuously. Security is no longer correlated with popularity. The same force that makes large codebases exploitable *en masse* also makes shrinking code into minimal, scrutinized components tractable.

That’s why we’re betting that maintaining our own minimal, purpose-built firmware<sup>[1](https://tinfoil.sh/blog/2026-10-25-less-is-more#user-content-fn-1)</sup> is now a better security posture than adopting a legacy open-source one with 20 years of accumulated features. It also moves us closer to our end goal of formally verifying every part of the confidential VM image on which all of Tinfoil’s security and verifiability rest.

We view this reductionist approach as more pragmatic compared to unleashing swarms of agents to find vulnerabilities and patch them (e.g., OpenAI’s “Patch the Planet”). It costs millions of dollars to red-team large code bases. For example, OpenAI revealed how they’ve burned nearly 400B tokens red-teaming their infrastructure (Figure 1).<sup>[2](https://tinfoil.sh/blog/2026-10-25-less-is-more#user-content-fn-2)</sup> That’s somewhere between $8 and $20M in tokens at current prices, using a frontier cyber model that nobody but them has access to. Patching-with-swarms is unfortunately a strategy that will only be viable for big companies with deep pockets.

![OpenAI’s chart of deduplicated candidate red-teaming findings versus tokens spent, rising to roughly 275 findings over nearly 400 billion tokens.](https://tinfoil.sh/blog-images/2026-10-25-red-teaming-findings-versus-tokens-spent.png)

## The role of firmware in secure enclaves

Tinfoil guarantees that we cannot access our customers’ workloads or data, even if an attacker compromises us and steals all our keys. Every workload runs in a secure enclave: a confidential virtual machine whose memory is encrypted by hardware from Intel, AMD and NVIDIA, and which can publicly prove exactly what code it is running.

Traditionally, cloud security meant guarding against a *tenant* breaking *out* of their virtual machine, known as the guest-to-host attack surface. At Tinfoil, we’re equally concerned with the opposite, the host-to-guest attack surface: everything *we* (or whoever has compromised us) could do to break *into* our tenants’ enclaves. The most critical and exposed moment that attackers can take advantage of is boot, since that’s when the security attestation is generated.

When a secure enclave boots, its initial state is measured by the secure hardware. Then, when the virtual machine has finished booting, it asks the hardware to attest to what was measured. This is how Tinfoil proves what code is running in the enclave for anyone to verify.<sup>[3](https://tinfoil.sh/blog/2026-10-25-less-is-more#user-content-fn-3)</sup>

Firmware is software that directly interfaces with hardware; computers need firmware to run at boot time to initialize their hardware. Virtual machines in secure enclaves are no different, and the guest firmware in enclaves has a particularly critical job. In the traditional boot flow, the initial launch of the enclave measures the firmware, which is then responsible for loading and verifying the code that the guest runs after it. In our case, the firmware needed to measure the kernel, the initramfs, and the Linux command line. Because of this critical role, an exploitable bug in the firmware code could allow a malicious host to load arbitrary software, voiding security and verifiability. Figure 2 shows this traditional boot flow.

![Traditional confidential VM boot: the host supplies configuration and operating-system files to firmware, hardware measures firmware at launch, and the client verifies the resulting attestation report.](https://tinfoil.sh/blog-images/2026-10-25-ovmf-boot-flow.png)

Our old firmware was OVMF (Open Virtual Machine Firmware), a widely used and accepted firmware for virtual machines. However, this popularity meant interoperability and richness that came with a major security cost: the specification alone is almost 3,000 pages long. Moreover, OVMF contains over a million lines of C code, and there have been multiple critical vulnerabilities found in the codebase already; one vulnerability was found this week in its network stack.<sup>[4](https://tinfoil.sh/blog/2026-10-25-less-is-more#user-content-fn-4)</sup> Why does firmware even have a network stack, you might ask? For network boot, of course! But at Tinfoil, we don’t boot over the network and only ever use a tiny set of the features that OVMF provides out of the box. We deemed OVMF’s large surface area to be a security risk and set out to do something about it.

## Launch measurement is all you need

Instead of taking OVMF and finding all the bugs and hardening it, our strategy was to step back and consider the purpose of virtual machine firmware in the first place. What does OVMF do for us, really? Concretely, the firmware has two main functions that we use it for: (1) booting Linux and (2) linking the launch measurement to the runtime code in the guest.

The hardware’s guarantee covers only what is in memory at launch, and in our legacy boot process, that consisted of OVMF. It was OVMF’s job to load and measure everything else. So the integrity of the operating system depended on the firmware behaving correctly after the launch measurement had already been taken.

It was clear to us that this was too much for the firmware to do. The firmware was an unnecessary link in the measurement and verification chain. Instead, we decided to simplify both our firmware and our verification chain by placing everything needed to bring up Linux in the enclave’s initial launch memory: our new minimal firmware, kernel, initramfs, page tables, fixed ACPI tables and templates, and Linux command line. These are measured at enclave launch, rather than by the firmware, and recorded as a single hash (`MRTD` on TDX and the launch digest on SEV-SNP). Figure 3 compares the measurement chains.

![Comparison of attestation flows: OVMF on TDX measures host configuration and operating-system components into runtime registers; the IGVM design places the firmware, kernel, initramfs, command line, and fixed tables in the hardware launch measurement.](https://tinfoil.sh/blog-images/2026-10-25-attestation-side-by-side.png)

To describe the initial memory state of our confidential virtual machines, we use the Independent Guest Virtual Machine (IGVM) file format.<sup>[5](https://tinfoil.sh/blog/2026-10-25-less-is-more#user-content-fn-5)</sup> Our CI builds and attests an IGVM file containing a complete layout of what guest memory should look like when an enclave launches. The firmware no longer needs to load or measure things, which makes verification simple: it’s just a hash of this initial build state. Our firmware now has only one job: to boot up Linux! This would already reduce the security risks of a compromised firmware, but we can go even further.

## How little does it take to boot Linux?

So what do we need to minimally boot Linux in a secure enclave? It turns out not much. On x86, virtual machines need basic CPU features like paging and 64-bit long mode set up, then they can `jmp` to Linux. The basic transition could probably be achieved with about 20 lines of x86 assembly instructions. During prototyping, though, we found a couple more requirements, such as handling CPU counts and memory layouts, that our firmware also needed to take care of. This is why our final minimal firmware is about 300 lines of code and not 20.

### The challenge of handling arbitrary configurations

When using IGVM to build and launch our enclaves, the fixed initial boot state is measured at launch. If we had exactly one workload with only one set of resource requirements, this would not be a problem, but we need the ability to launch enclaves with different amounts of memory without having to build separate images. Figure 4 shows one of the memory layouts we support.

![An 8 GiB guest memory layout with RAM from 0 to 2 GiB, a device-memory hole from 2 to 4 GiB, and RAM from 4 to 10 GiB. The host supplies the end of RAM, which the firmware checks against a measured layout.](https://tinfoil.sh/blog-images/2026-10-25-memory-8gib-guest.png)

For Linux to boot, it needs a layout of its physical address space: a memory map. Tinfoil’s enclaves all run with the physical memory mapping predefined, so this means we pre-bake the machine’s memory map during IGVM build time and do not rely on the firmware to define it at runtime. When the enclave launches, it includes an unmeasured memory map with the actual amount of memory it is provisioned with. Our firmware only needs to check that the shape of the memory map matches the pre-built entries. Thus, only the total memory size is determined by the host; if it lies about the shape of memory, the firmware fails the boot process. Overall, this means that the worst-case scenario is when the host lies and under- or overprovisions memory, which simply causes the boot to fail.

Similarly, we need to handle arbitrary CPU types and configurations, without tying the number of CPUs to our build measurement. Linux brings up multiple CPUs by checking ACPI’s MADT table<sup>[6](https://tinfoil.sh/blog/2026-10-25-less-is-more#user-content-fn-6)</sup>, using the number of APIC entries to bring up each CPU it was provisioned. Similarly to how we handle variable memory, we minimize the unmeasured data sent from the host and pre-build the ACPI tables. When our minimal firmware runs in the guest, it just needs to check the CPU count for sanity and patch the MADT entry with the number of CPUs needed. If our host lies and gives more or fewer CPUs than it actually provisions for the enclave, either Linux will not bring the extra CPUs up or the extra CPUs will stay parked in an infinite loop, neither of which poses a threat to the confidentiality of the guest’s enclave.

### Handing off to Linux

At this point, things are all set up for Linux. The Linux x86 boot protocol requires a setup header that points to the kernel, the initramfs, and the command line, all of which are already mapped into memory at enclave launch.<sup>[7](https://tinfoil.sh/blog/2026-10-25-less-is-more#user-content-fn-7)</sup> So all our firmware needs to do is jump to Linux! Concretely, the handoff in our firmware looks like:

And our firmware never runs again. The entire workload continues in Linux with no more after-boot firmware attack surface to speak of.

## What happened to everything OVMF did

Here’s where everything OVMF did for us ended up. Roughly speaking, each job either moved earlier, to build time, where the result gets measured; moved later, to Linux; or got deleted. Table 1 shows the breakdown.

Under OVMF, there were eight different places where guest code parsed bytes the host controls: `fw_cfg`, the ACPI table linker, host-authored AML, SMBIOS, the NVRAM variable store, the TD HOB, virtio drivers, and option ROMs. Now there are two, and both are checked against fixed bounds. You might reasonably ask whether moving work into Linux just moves the problem. We don’t think it does, since Linux already does these jobs for every confidential guest, and under OVMF most of them were done twice, once in the firmware and once in the kernel. That doesn’t make the Linux code bug-free, but it’s code we were already trusting.

### Why not Stage0?

The obvious question is why we didn’t just use Google’s Project Oak Stage0, an existing minimal firmware for confidential VMs.<sup>[8](https://tinfoil.sh/blog/2026-10-25-less-is-more#user-content-fn-8)</sup> It was, in fact, the first thing we tried. Stage0 is much smaller than OVMF and was designed with similar goals. But even stripped down, it does two things we wanted the firmware not to do at all. First, it is still a link in the measurement chain: it loads the kernel and initramfs after launch and measures them itself. Second, it still processes host input at boot. It reads configuration through `fw_cfg` and builds platform tables from what the host gives it. If you’re writing firmware meant to boot a variety of VMs on a variety of hosts, this is a perfectly reasonable design. Under our threat model, where the host is the attacker, it means every one of those code paths takes attacker-controlled input.

What we do instead is generate that state ahead of time. Page tables, ACPI and EFI structures, and the set of memory layouts we allow are all produced at build time and included, along with the kernel and initramfs, in the launch measurement. The firmware that’s left is minimal assembly with no dependencies. It checks two values from the host, the CPU count and the memory map, and jumps to Linux.

A reasonable objection is that we haven’t removed the table-building code, just moved it into a build tool that also has to be correct. That’s true! But the build tool is in our **audit TCB**, the code we have to read, and not our **runtime TCB**, the code a live attacker can reach. A runtime table builder is in both. To trust it, you have to reason about every path through its parsers, allocators, and table updates that a malicious host could hit. Our generator never sees input from a live host. If it has a bug, every enclave gets the same wrong bytes, sitting in the measured image where they can be read and diffed between releases. If a runtime builder has a bug, it waits for the input that triggers it, and the attacker gets to choose that input.

This isn’t specific to firmware. It’s generally much easier to review a concrete artifact than code that produces artifacts from untrusted input: the first is one thing you can look at, and the second is a function over every input an attacker can construct.

This isn’t free, either. Stage0 adapts at boot to whatever machine the host describes, while ours only boots the machine shapes we built it for. When QEMU changes its memory layout, our firmware refuses to boot until we add the new one. For general-purpose firmware, that would be a bad tradeoff. Our fleet is extremely uniform, so for us it’s an easy one.

## Conclusion

The cyber capabilities of LLMs are shining a flashlight on software vulnerabilities at an unprecedented scale. While cybersecurity was always a cat-and-mouse game, new approaches are required to minimize the threat. This is doubly true at a time of growing asymmetry in who can access frontier cyber-capable models.

The reflexive reaction is to use LLMs to accelerate the patching of bugs as well. The problem is that this leads to an endless cycle: defenders can burn many more tokens than attackers to red-team and patch their systems. Moreover, this approach still favors attackers, who only need to find one weak link to breach a system.

The antidote to this growing cybersecurity crisis is to apply a reductionist mindset and use the tools at our disposal more effectively. Instead of relying on legacy codebases with millions of lines of code, we can use LLMs to build targeted, minimal software from the ground up. This approach also makes it easier to apply traditional security tools, such as fuzzing and formal verification, to further secure the minimal building blocks. Popularity no longer implies security. In fact, a small, purpose-built piece of tailored software can be more secure than a wildly popular library.

Our firmware work taught us another lesson, too: you can reduce the amount of behavior you need to trust by moving decisions from attacker-influenced runtime execution into independently reproducible, measured build artifacts. That’s what we did with page tables, ACPI tables, and memory layouts, and the idea applies well beyond firmware.

We’re excited to apply this new philosophy to other parts of our stack, and we hope to see other open-source projects adopt similar approaches to security.

## Footnotes

1. The firmware and `cvmc` image builder are in the [`lothan/igvm` branch of `tinfoilsh/cvmimage`](https://github.com/tinfoilsh/cvmimage/tree/lothan/igvm), under `firmware/` and `compiler/`. The [launch design](https://github.com/tinfoilsh/cvmimage/blob/lothan/igvm/docs/launch.md) describes the memory layouts, measurements, platform requirements, and reproducible build. [↩](https://tinfoil.sh/blog/2026-10-25-less-is-more#user-content-fnref-1)
2. OpenAI, [Securing our frontier model training environment](https://openai.com/index/securing-our-frontier-model-training-environment/), October 23, 2026. See also [Patch the Planet](https://openai.com/index/patch-the-planet/). [↩](https://tinfoil.sh/blog/2026-10-25-less-is-more#user-content-fnref-2)
3. For more detail, see [A primer on secure enclaves](https://docs.tinfoil.sh/verification/secure-enclave-primer). [↩](https://tinfoil.sh/blog/2026-10-25-less-is-more#user-content-fnref-3)
4. EDK II security advisory [GHSA-99cj-7hg9-mp4m: Pre-boot RCE in EDK II PXE driver](https://github.com/tianocore/edk2/security/advisories/GHSA-99cj-7hg9-mp4m), published October 22, 2026. [↩](https://tinfoil.sh/blog/2026-10-25-less-is-more#user-content-fnref-4)
5. The [IGVM format](https://github.com/microsoft/igvm) is maintained by Microsoft. See also [IGVM support in QEMU](https://www.qemu.org/docs/master/system/igvm.html). [↩](https://tinfoil.sh/blog/2026-10-25-less-is-more#user-content-fnref-5)
6. See the [Multiple APIC Description Table (MADT)](https://wiki.osdev.org/MADT) overview and the Multiprocessor Wakeup structure in the [ACPI specification](https://uefi.org/specs/ACPI/6.6/05_ACPI_Software_Programming_Model.html). [↩](https://tinfoil.sh/blog/2026-10-25-less-is-more#user-content-fnref-6)
7. The Linux documentation describes the [x86 boot protocol](https://docs.kernel.org/arch/x86/boot.html) and [zero page](https://docs.kernel.org/arch/x86/zero-page.html). [↩](https://tinfoil.sh/blog/2026-10-25-less-is-more#user-content-fnref-7)
8. See [Project Oak’s Stage0](https://github.com/project-oak/oak/tree/main/stage0), its [shared boot implementation](https://github.com/project-oak/oak/tree/main/stage0/src), and its [TDX](https://github.com/project-oak/oak/tree/main/stage0_tdx) and [SEV-SNP](https://github.com/project-oak/oak/tree/main/stage0_sev) implementations. [↩](https://tinfoil.sh/blog/2026-10-25-less-is-more#user-content-fnref-8)
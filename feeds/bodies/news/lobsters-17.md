[We recently announced Amutable Foundations](https://amutable.com/blog/introducing-amutable-foundations). It’s now time to provide a technical overview of how Amutable Foundations is put together. In this post, we’ll discuss two of the most fundamental components:

- **Amutable OS** (“*AOS*”, or “*⊼OS*”), a modern image-based Linux OS. It builds on the foundation of established Linux distributions, but moves them from a package-based world into an image-based, integrity-protected world. It removes drift, and adds robustness, integrity, and reproducibility. On one hand this provides great conceptual compatibility with the status quo ante of enterprise distributions, and on the other hand it’s built from the ground up with image-based OS designs in mind.
- **Amutable Control Plane** (“*ACP*”, or “*⊼CP*”), a management system that tracks, controls, updates and verifies a fleet of AOS installations.

## AOS – Amutable Operating System

Amutable OS is built on classic Linux distributions, initially from [Fedora](https://fedoraproject.org/) packages. Distributions do valuable integration and unification work on the basic components of the OS – work we want to leverage. However, AOS uses distribution packages to pre-assemble immutable disk images at build-time while distributions, traditionally, compose a Linux system by installing packages on the final, deployed system. Let’s take a closer look at what this means.

- **Package-based OSes** generally provide the user with a large number of regularly updated software packages (many thousands) with complex dependencies, which are composed into a working OS on the final machine it is deployed on. Installations in this style tend to vary greatly from system to system. Even with an identical selection of packages for the target system, the installation/update order, the stateful update logic and the file system data structures generally mean that the bytes that hit the disk on each machine are always different. This is called *drift*. Systems put together this way are hence not reproducible, not predictable, and hard to compare and analyze which is essential for tracking down security issues. They are also hard to test as the flexibility of selecting packages and assembling them in any order results in a prohibitive combinatorial explosion of systems to test.
- **Image-based OSes** instead provide pre-built file system images that contain all code and other resources the OS needs. These images are bit-by-bit identical on every deployed system, so that the installations differ only in local state acquired during runtime, but not in the OS code and resources themselves (which stay 100% identical). To improve modularity, AOS extends this concept to allow a small number of coarse images to be merged together. Rather than thousands of packages, each system only combines a small number (typically < 5) of images, so that the system stays reproducible.

Building from existing distribution packages allows us to guarantee far reaching semantic compatibility with existing systems, while maintaining our image-based focus. In particular, it allows us to potentially prepare – with little effort – individualized disk images that fit perfectly for the customer’s projects.

### Modularization

Classic distribution packages are a concept of *modularization*, and useful in that. With our image-based OS approach, we cut down on the modularization at deployment time, but we do allow some. This reflects the fact that while we likely will be able to cover a lot of disparate systems with a single, generic, minimal OS image, some of the components certain systems might require are so large, or specific, that it makes sense to split them out. For example, graphics/AI drivers and cloud-specific agent services tend to be large these days.

#### System Extensions

In order to not require their installation on every deployment host we split some components out into [**system extensions**](https://www.freedesktop.org/software/systemd/man/latest/systemd-sysext.html) (or short: “*sysexts*”) that contain additional files which can be overlaid on top of the OS resources in `/usr/` and augment the system with additional resources. Making these components optional reduces footprint and attack surface.

Note that in many cases the selection of sysexts to activate on a given host is purely a function of the host’s circumstances and equipment. More specifically, the graphics drivers and subsystem should be installed automatically when the matching hardware is detected. Similarly, the cloud-specific agent services should be picked up automatically when the system is detected to run inside a relevant cloud vendor’s environment.

In AOS the selection of additional images to install is hence somewhat automated. The local AOS system carries a “[hwdb](https://www.freedesktop.org/software/systemd/man/latest/hwdb.html)” database that dictates which additional images to auto-install on the individual node if certain hardware is enumerated or the VMM indicates certain identification or functionality.

#### Configuration Extensions

A core functionality of AOS is support for [**configuration extensions**](https://www.freedesktop.org/software/systemd/man/latest/systemd-confext.html) (“confexts”). These are very similar to sysexts, but overlay `/etc/` instead of `/usr/`. They are designed to be the primary configuration management concept on AOS: configuration is pre-built and shipped in an atomically applied image to the AOS nodes, where it appears in full or not at all, but never halfway. Or in other words, not just AOS code but also AOS configuration is free from drift and strictly reproducible.

#### Discoverable Disk Images

The OS image itself, as well as sysext and confext images are implemented as [**UAPI.3 DDIs**](https://uapi-group.org/specifications/specs/discoverable_disk_image/): [EROFS](https://en.wikipedia.org/wiki/EROFS) file system images, combined with [Verity](https://docs.kernel.org/admin-guide/device-mapper/verity.html) protection data, and a cryptographic signature, all wrapped in a GPT partition table as envelope. In the case of confexts, these DDIs are additionally encrypted ([LUKS](https://en.wikipedia.org/wiki/Linux_Unified_Key_Setup)). This means strong integrity is enforced on all these components not just at download time, but continuously during runtime. For configuration, confidentiality is also guaranteed during runtime. Moreover, we not only protect the contents of the images but the file system data structures themselves. Since each image can be cryptographically referenced via their Verity root hash, we also have a useful handle to *measure* before activating each image (see below for what this means).

The Linux kernel is shipped as a [**UAPI.5 UKI**](https://uapi-group.org/specifications/specs/unified_kernel_image/). This means it comprehensively protects the kernel itself and its initrd via UEFI SecureBoot, and via [TPM](https://en.wikipedia.org/wiki/Trusted_Platform_Module) measurements and policies.

![AOS node composition: workload images (containers, VMs, portable services) on top of the operating system, built from confext DDIs, sysext DDIs, the OS DDI and the UKI](https://amutable.com/images/aos-node-composition.svg)

## ACP – Amutable Control Plane

Amutable Control Plane (ACP) manages and supervises a fleet of AOS nodes. It primarily encompasses the following functionality:

- An enrollment system that allows administrators to enroll AOS nodes using hardware-backed trust.
- A report receiver, validator, and ledger which is one side of an operational loop which we will look at below.
- A configuration extension generator, which encrypts confext images for each node.
- An identity service for issuing short-lived credentials used to authenticate nodes.
- An image repository based on TUF which we’ve covered in an earlier blog post.
- A CVE scanner and analysis tool that leverages the verified SBOMs associated with the images that machines are using.
- A web UI to manage the above-listed functionality.

ACP is multi-tenant: each tenant has its own signing keys, storage and roles.

The interplay between the incoming reports and the outgoing confext and sysext images creates a loop that we leverage for security and operational robustness. Let’s take a look at that now.

![Amutable Control Plane components: report reception and verification, ledger, confext builder, web UI, identity provider, enrollment, image repository and CVE analysis](https://amutable.com/images/acp-components.svg)

## CLL – Cryptographic Locked Loop

ACP keeps track of the enrolled nodes; ensures they are updated, in good health and that their integrity is verified. It also needs to be able to provide new configuration to nodes so they can receive configuration changes or new workloads. This forms a bi-directional relationship:

- Each node sends “**reports**” (generated by the [systemd-report](https://amutable.com/blog/it-starts-upstream-systemd-report) tool) to the ACP instance it is enrolled in, at regular intervals. These reports describe both the runtime/resource state of the system, as well as cryptographic information about the composition of the system.On systems where a TPM is available, this carries a TPM “quote” that cryptographically indicates which UKI and DDIs the system is composed of. On systems where [Confidential Computing](https://en.wikipedia.org/wiki/Confidential_computing) (CoCo) is available, this carries a CPU quote instead that indicates what the initial composition of the node was. Moreover, a pure software signature scheme is available as well.These reports are collected by the ACP instance, verified both superficially (i.e. validating the signature checks out and mapping the signing keys to the source system) and in detail (i.e. checking if the UKI and all DDIs the system is composed of are recognized), in a [**remote attestation**](https://en.wikipedia.org/wiki/Trusted_Computing#Remote_attestation) scheme.This information is then enriched (e.g. SBOM, CVE, … information for the UKIs/DDIs) and everything written to a centralized “**ledger**” database. This ledger tracks the state of the entire fleet, both the image-level composition of it and the runtime state, including resource usage. Reports are the “*way up*” from the AOS nodes to the ACP instance.
- In the opposite direction, ACP sends **confext DDIs** to the nodes. As mentioned above, these are Verity-protected, signed and encrypted with a key specific to the node. If the node hardware supports cryptographic sealing (as TPMs do), the confext DDI is sealed to the hardware keys of the node. The sealing uses a hardware-enforced access policy that mirrors the most recently seen report of the node (plus various other parameters).This provides very strong security guarantees: configuration and resources for a specific node may only be unlocked by the node if it still is in the state last reported. Or in other words, there’s also **local attestation** in play here: after ACP verifies via remote attestation that the node is in a good state, it provides updates and additional resources that can only be used after the local hardware validates that the machine is still in the expected state.This reduces the vulnerability window between ACP’s determination that the node is in a good state and the actual update for the node, as the state is re-verified at that point. Also note that this mechanism is very compatible with nodes that lack continuous connectivity as they can boot up fine even without being able to contact the ACP instance as the local TPM can reasonably attest the system’s state via the local attestation mechanism. Confext DDIs are the “*way down*” from the ACP instance to the AOS nodes.

The way up (of the reports) and the way down (of the confext DDIs) together make up what we call the *Cryptographic Locked Loop* (“CLL”). A continuous cycle of reports and confexts tracks and controls the fleet. The ledger always carries a precise, frequently updated description of the fleet’s state.

![The cryptographic locked loop: AOS nodes send reports to ACP, which verifies, inspects, enriches and records them in the ledger, then sends back confext DDIs locked to the latest report](https://amutable.com/images/aos-acp-locked-loop.svg)

Note that our CLL implementation is opportunistic. TPMs and CoCo are not available everywhere. AOS and ACP will make use of this hardware if available (specifically most reasonably modern TPM 2.0 implementations in chip, firmware or virtualized should work, as should [AMD SEV](https://www.amd.com/en/developer/sev.html) and [Intel TDX](https://www.intel.com/content/www/us/en/developer/tools/trust-domain-extensions/overview.html)). The system also uses a pure software scheme.

Of course, the different technologies provide different security guarantees, and ACP’s UI will surface the used technologies clearly. Note that TPM, AMD SEV, Intel TDX, and software signatures are used opportunistically and in parallel if available. This is to say that in situations where a confidential VM with a vTPM is used, it might happen that reports are signed thrice (one TPM quote, one CoCo quote, and one plain software signature). It’s the job of ACP’s verifier to validate all three signatures and focus on the strongest technology of them all for the right purpose.

## The Varlink Communication Channel

Communication between ACP and AOS nodes primarily takes place via reports in one direction and confext DDIs in the other as explained earlier in this post. Both mechanisms are very asynchronous in nature: reports are generated, queued, transferred, and processed asynchronously.

Confext DDIs are generated for the nodes, made available for download via a separate TUF repo, eventually downloaded by the node, and finally applied. This asynchronous behavior is fantastic for many scenarios and operations since it’s very robust and resilient towards spotty connectivity, unstable power sources and other disruptions. However, it is not nice for operations where interactivity is key, e.g. debugging, certain administrative operations and similar.

To address this, AOS nodes have the possibility to be put into remote [Varlink](https://varlink.org/) mode that is facilitated via ACP and use the authentication options that the [varlink-http-bridge](https://github.com/systemd/varlink-http-bridge) provides (like mTLS or sshauth). This is built using the zero-trust pattern: ACP is content blind and has no special access.

When remote Varlink mode is enabled, a node exposes its full Varlink IPC API over HTTPS. That covers everything systemd and the other system services on the node offer via Varlink. For example: `io.systemd.Hostname` for hostname and machine metadata, `io.systemd.Unit` to list units and change their properties, `io.systemd.JournalAccess` to fetch journal entries, `io.systemd.SysUpdate` to check for and apply updates, and `io.systemd.Manager` to reload or reboot the system.

The result is API-driven management with strong typing and a fully self-describing set of rich APIs that any language that speaks JSON and HTTPS can drive. A service that registers a Varlink interface on the node becomes reachable remotely without further changes.

The API is self-describing, so a client can discover what a node offers. For each API interface the node also serves an [OpenAPI 3.1](https://spec.openapis.org/oas/v3.1.0) description, so you can generate typed client wrappers for Python, Go, TypeScript and other languages with standard tooling.

## Cohesive Security Design

The image-based OS approach enables us to enforce some very strict but powerful security properties, which elevate the security posture of the system substantially above traditional Linux systems. Specifically, let’s highlight seven major essential security properties of AOS here:

1. **No Shell + No SSH + No Language Interpreters**. By default AOS does not install a UNIX shell, nor makes remote access via SSH available on the nodes. Moreover, we do not install any of the usual language interpreters (Python, Perl, …) by default. For most nodes a shell or interpreted language support is not required and it removes a whole class of attacks.
2. **Signed Images Only**. On AOS only images that come with Verity data signed by a signing key listed in the [Verity keyring](https://amutable.com/blog/it-starts-upstream-kernel) may be activated.
3. **W^X**. We’ve posted about W^X policies before in greater detail. The core idea is that code cannot live on writable file systems and instead must originate from Verity protected sources. This makes injecting code into AOS much harder and hardens it against remote-code-execution vulnerabilities such as the [recent PHP attacks](https://amutable.com/blog/recent-php-cves-retrospective) which we also covered on our blog.
4. **Everything Is Measured**. We believe that for a secure system it is absolutely essential to maintain a tamper-evident log of all images containing code or configuration. This kind of tamper-evident log is based on *measurements* utilizing hardware features that make it impossible to forge.
5. **No SUID/SGID or File Capabilities**. The SUID and SGID file access bits are a fundamental privilege escalation mechanism in classic UNIX and have led to a very large number of exploits. On AOS the SUID and SGID bits are therefore disabled completely. Privilege elevation happens securely via IPC such that a suitably privileged process performs operations on behalf of less privileged code.
6. **Integrity Is Mandatory**. A modern operating system must provide integrity guarantees well beyond traditional systems. It is a conditio sine qua non given the advent of LLM agents. On AOS everything is measured, attested, and comes with fundamental protection mechanisms. For example, all file system images we ship come with block-level Verity and encryption securing complex file system data structures.
7. **Factory Reset Is Built In**. Any operating system must consider the possibility that it will be hacked. For this reason, a secure OS must come with a “[factory reset](https://www.freedesktop.org/software/systemd/man/latest/systemd-factory-reset.html)” mechanism. AOS makes a lot of exploits *visible* in its Ledger. With factory reset it gains the ability to *act* and put the system back into a good state.

## Summary

**TL;DR**: Putting this all together, Amutable Foundations’ AOS and ACP provide:

- A modern image-based OS, with far-reaching compatibility with classic Linux distributions
- AOS is fundamentally designed with security in mind, removing a large portion of the attack surface of classic Linux systems
- Composition, lifetime and resources of nodes are centrally tracked in the ledger, with tamper-evident properties, via measurements
- The system covers both OS updates and configuration management via the same (or similar) mechanisms
- Each node comes with a robust, powerful API to execute operations on it
- Opportunistic support for modern security hardware (TPM 2.0, CoCo), with graceful degradation to all-software signatures where unavailable
- Integrity checks every step of the way, via both local and remote attestation
- Custom configuration and resources are only available to the machine if it is in the expected state

## Sign Up for Our Private Preview Now!

If you are interested in the experience we described above, please [sign up for the Amutable Foundations Private Preview](https://amutable.com/preview) to get a chance to try AOS and ACP first-hand yourself.

[We recently announced Amutable Foundations](https://amutable.com/blog/introducing-amutable-foundations). It’s now time to provide a technical overview of how Amutable Foundations is put together. In this post, we’ll discuss two of the most fundamental components:

- **Amutable OS** (“*AOS*”, or “*⊼OS*”), a modern image-based Linux OS. It builds on the foundation of established Linux distributions, but moves them from a package-based world into an image-based, integrity-protected world. It removes drift, and adds robustness, integrity, and reproducibility. On one hand this provides great conceptual compatibility with the status quo ante of enterprise distributions, and on the other hand it’s built from the ground up with image-based OS designs in mind.
- **Amutable Control Plane** (“*ACP*”, or “*⊼CP*”), a management system that tracks, controls, updates and verifies a fleet of AOS installations.

## AOS – Amutable Operating System

Amutable OS is built on classic Linux distributions, initially from [Fedora](https://fedoraproject.org/) packages. Distributions do valuable integration and unification work on the basic components of the OS – work we want to leverage. However, AOS uses distribution packages to pre-assemble immutable disk images at build-time while distributions, traditionally, compose a Linux system by installing packages on the final, deployed system. Let’s take a closer look at what this means.

- **Package-based OSes** generally provide the user with a large number of regularly updated software packages (many thousands) with complex dependencies, which are composed into a working OS on the final machine it is deployed on. Installations in this style tend to vary greatly from system to system. Even with an identical selection of packages for the target system, the installation/update order, the stateful update logic and the file system data structures generally mean that the bytes that hit the disk on each machine are always different. This is called *drift*. Systems put together this way are hence not reproducible, not predictable, and hard to compare and analyze which is essential for tracking down security issues. They are also hard to test as the flexibility of selecting packages and assembling them in any order results in a prohibitive combinatorial explosion of systems to test.
- **Image-based OSes** instead provide pre-built file system images that contain all code and other resources the OS needs. These images are bit-by-bit identical on every deployed system, so that the installations differ only in local state acquired during runtime, but not in the OS code and resources themselves (which stay 100% identical). To improve modularity, AOS extends this concept to allow a small number of coarse images to be merged together. Rather than thousands of packages, each system only combines a small number (typically < 5) of images, so that the system stays reproducible.

Building from existing distribution packages allows us to guarantee far reaching semantic compatibility with existing systems, while maintaining our image-based focus. In particular, it allows us to potentially prepare – with little effort – individualized disk images that fit perfectly for the customer’s projects.

### Modularization

Classic distribution packages are a concept of *modularization*, and useful in that. With our image-based OS approach, we cut down on the modularization at deployment time, but we do allow some. This reflects the fact that while we likely will be able to cover a lot of disparate systems with a single, generic, minimal OS image, some of the components certain systems might require are so large, or specific, that it makes sense to split them out. For example, graphics/AI drivers and cloud-specific agent services tend to be large these days.

#### System Extensions

In order to not require their installation on every deployment host we split some components out into [**system extensions**](https://www.freedesktop.org/software/systemd/man/latest/systemd-sysext.html) (or short: “*sysexts*”) that contain additional files which can be overlaid on top of the OS resources in `/usr/` and augment the system with additional resources. Making these components optional reduces footprint and attack surface.

Note that in many cases the selection of sysexts to activate on a given host is purely a function of the host’s circumstances and equipment. More specifically, the graphics drivers and subsystem should be installed automatically when the matching hardware is detected. Similarly, the cloud-specific agent services should be picked up automatically when the system is detected to run inside a relevant cloud vendor’s environment.

In AOS the selection of additional images to install is hence somewhat automated. The local AOS system carries a “[hwdb](https://www.freedesktop.org/software/systemd/man/latest/hwdb.html)” database that dictates which additional images to auto-install on the individual node if certain hardware is enumerated or the VMM indicates certain identification or functionality.

#### Configuration Extensions

A core functionality of AOS is support for [**configuration extensions**](https://www.freedesktop.org/software/systemd/man/latest/systemd-confext.html) (“confexts”). These are very similar to sysexts, but overlay `/etc/` instead of `/usr/`. They are designed to be the primary configuration management concept on AOS: configuration is pre-built and shipped in an atomically applied image to the AOS nodes, where it appears in full or not at all, but never halfway. Or in other words, not just AOS code but also AOS configuration is free from drift and strictly reproducible.

#### Discoverable Disk Images

The OS image itself, as well as sysext and confext images are implemented as [**UAPI.3 DDIs**](https://uapi-group.org/specifications/specs/discoverable_disk_image/): [EROFS](https://en.wikipedia.org/wiki/EROFS) file system images, combined with [Verity](https://docs.kernel.org/admin-guide/device-mapper/verity.html) protection data, and a cryptographic signature, all wrapped in a GPT partition table as envelope. In the case of confexts, these DDIs are additionally encrypted ([LUKS](https://en.wikipedia.org/wiki/Linux_Unified_Key_Setup)). This means strong integrity is enforced on all these components not just at download time, but continuously during runtime. For configuration, confidentiality is also guaranteed during runtime. Moreover, we not only protect the contents of the images but the file system data structures themselves. Since each image can be cryptographically referenced via their Verity root hash, we also have a useful handle to *measure* before activating each image (see below for what this means).

The Linux kernel is shipped as a [**UAPI.5 UKI**](https://uapi-group.org/specifications/specs/unified_kernel_image/). This means it comprehensively protects the kernel itself and its initrd via UEFI SecureBoot, and via [TPM](https://en.wikipedia.org/wiki/Trusted_Platform_Module) measurements and policies.

![AOS node composition: workload images (containers, VMs, portable services) on top of the operating system, built from confext DDIs, sysext DDIs, the OS DDI and the UKI](https://amutable.com/images/aos-node-composition.svg)

## ACP – Amutable Control Plane

Amutable Control Plane (ACP) manages and supervises a fleet of AOS nodes. It primarily encompasses the following functionality:

- An enrollment system that allows administrators to enroll AOS nodes using hardware-backed trust.
- A report receiver, validator, and ledger which is one side of an operational loop which we will look at below.
- A configuration extension generator, which encrypts confext images for each node.
- An identity service for issuing short-lived credentials used to authenticate nodes.
- An image repository based on TUF which we’ve covered in an earlier blog post.
- A CVE scanner and analysis tool that leverages the verified SBOMs associated with the images that machines are using.
- A web UI to manage the above-listed functionality.

ACP is multi-tenant: each tenant has its own signing keys, storage and roles.

The interplay between the incoming reports and the outgoing confext and sysext images creates a loop that we leverage for security and operational robustness. Let’s take a look at that now.

![Amutable Control Plane components: report reception and verification, ledger, confext builder, web UI, identity provider, enrollment, image repository and CVE analysis](https://amutable.com/images/acp-components.svg)

## CLL – Cryptographic Locked Loop

ACP keeps track of the enrolled nodes; ensures they are updated, in good health and that their integrity is verified. It also needs to be able to provide new configuration to nodes so they can receive configuration changes or new workloads. This forms a bi-directional relationship:

- Each node sends “**reports**” (generated by the [systemd-report](https://amutable.com/blog/it-starts-upstream-systemd-report) tool) to the ACP instance it is enrolled in, at regular intervals. These reports describe both the runtime/resource state of the system, as well as cryptographic information about the composition of the system.On systems where a TPM is available, this carries a TPM “quote” that cryptographically indicates which UKI and DDIs the system is composed of. On systems where [Confidential Computing](https://en.wikipedia.org/wiki/Confidential_computing) (CoCo) is available, this carries a CPU quote instead that indicates what the initial composition of the node was. Moreover, a pure software signature scheme is available as well.These reports are collected by the ACP instance, verified both superficially (i.e. validating the signature checks out and mapping the signing keys to the source system) and in detail (i.e. checking if the UKI and all DDIs the system is composed of are recognized), in a [**remote attestation**](https://en.wikipedia.org/wiki/Trusted_Computing#Remote_attestation) scheme.This information is then enriched (e.g. SBOM, CVE, … information for the UKIs/DDIs) and everything written to a centralized “**ledger**” database. This ledger tracks the state of the entire fleet, both the image-level composition of it and the runtime state, including resource usage. Reports are the “*way up*” from the AOS nodes to the ACP instance.
- In the opposite direction, ACP sends **confext DDIs** to the nodes. As mentioned above, these are Verity-protected, signed and encrypted with a key specific to the node. If the node hardware supports cryptographic sealing (as TPMs do), the confext DDI is sealed to the hardware keys of the node. The sealing uses a hardware-enforced access policy that mirrors the most recently seen report of the node (plus various other parameters).This provides very strong security guarantees: configuration and resources for a specific node may only be unlocked by the node if it still is in the state last reported. Or in other words, there’s also **local attestation** in play here: after ACP verifies via remote attestation that the node is in a good state, it provides updates and additional resources that can only be used after the local hardware validates that the machine is still in the expected state.This reduces the vulnerability window between ACP’s determination that the node is in a good state and the actual update for the node, as the state is re-verified at that point. Also note that this mechanism is very compatible with nodes that lack continuous connectivity as they can boot up fine even without being able to contact the ACP instance as the local TPM can reasonably attest the system’s state via the local attestation mechanism. Confext DDIs are the “*way down*” from the ACP instance to the AOS nodes.

The way up (of the reports) and the way down (of the confext DDIs) together make up what we call the *Cryptographic Locked Loop* (“CLL”). A continuous cycle of reports and confexts tracks and controls the fleet. The ledger always carries a precise, frequently updated description of the fleet’s state.

![The cryptographic locked loop: AOS nodes send reports to ACP, which verifies, inspects, enriches and records them in the ledger, then sends back confext DDIs locked to the latest report](https://amutable.com/images/aos-acp-locked-loop.svg)

Note that our CLL implementation is opportunistic. TPMs and CoCo are not available everywhere. AOS and ACP will make use of this hardware if available (specifically most reasonably modern TPM 2.0 implementations in chip, firmware or virtualized should work, as should [AMD SEV](https://www.amd.com/en/developer/sev.html) and [Intel TDX](https://www.intel.com/content/www/us/en/developer/tools/trust-domain-extensions/overview.html)). The system also uses a pure software scheme.

Of course, the different technologies provide different security guarantees, and ACP’s UI will surface the used technologies clearly. Note that TPM, AMD SEV, Intel TDX, and software signatures are used opportunistically and in parallel if available. This is to say that in situations where a confidential VM with a vTPM is used, it might happen that reports are signed thrice (one TPM quote, one CoCo quote, and one plain software signature). It’s the job of ACP’s verifier to validate all three signatures and focus on the strongest technology of them all for the right purpose.

## The Varlink Communication Channel

Communication between ACP and AOS nodes primarily takes place via reports in one direction and confext DDIs in the other as explained earlier in this post. Both mechanisms are very asynchronous in nature: reports are generated, queued, transferred, and processed asynchronously.

Confext DDIs are generated for the nodes, made available for download via a separate TUF repo, eventually downloaded by the node, and finally applied. This asynchronous behavior is fantastic for many scenarios and operations since it’s very robust and resilient towards spotty connectivity, unstable power sources and other disruptions. However, it is not nice for operations where interactivity is key, e.g. debugging, certain administrative operations and similar.

To address this, AOS nodes have the possibility to be put into remote [Varlink](https://varlink.org/) mode that is facilitated via ACP and use the authentication options that the [varlink-http-bridge](https://github.com/systemd/varlink-http-bridge) provides (like mTLS or sshauth). This is built using the zero-trust pattern: ACP is content blind and has no special access.

When remote Varlink mode is enabled, a node exposes its full Varlink IPC API over HTTPS. That covers everything systemd and the other system services on the node offer via Varlink. For example: `io.systemd.Hostname` for hostname and machine metadata, `io.systemd.Unit` to list units and change their properties, `io.systemd.JournalAccess` to fetch journal entries, `io.systemd.SysUpdate` to check for and apply updates, and `io.systemd.Manager` to reload or reboot the system.

The result is API-driven management with strong typing and a fully self-describing set of rich APIs that any language that speaks JSON and HTTPS can drive. A service that registers a Varlink interface on the node becomes reachable remotely without further changes.

The API is self-describing, so a client can discover what a node offers. For each API interface the node also serves an [OpenAPI 3.1](https://spec.openapis.org/oas/v3.1.0) description, so you can generate typed client wrappers for Python, Go, TypeScript and other languages with standard tooling.

## Cohesive Security Design

The image-based OS approach enables us to enforce some very strict but powerful security properties, which elevate the security posture of the system substantially above traditional Linux systems. Specifically, let’s highlight seven major essential security properties of AOS here:

1. **No Shell + No SSH + No Language Interpreters**. By default AOS does not install a UNIX shell, nor makes remote access via SSH available on the nodes. Moreover, we do not install any of the usual language interpreters (Python, Perl, …) by default. For most nodes a shell or interpreted language support is not required and it removes a whole class of attacks.
2. **Signed Images Only**. On AOS only images that come with Verity data signed by a signing key listed in the [Verity keyring](https://amutable.com/blog/it-starts-upstream-kernel) may be activated.
3. **W^X**. We’ve posted about W^X policies before in greater detail. The core idea is that code cannot live on writable file systems and instead must originate from Verity protected sources. This makes injecting code into AOS much harder and hardens it against remote-code-execution vulnerabilities such as the [recent PHP attacks](https://amutable.com/blog/recent-php-cves-retrospective) which we also covered on our blog.
4. **Everything Is Measured**. We believe that for a secure system it is absolutely essential to maintain a tamper-evident log of all images containing code or configuration. This kind of tamper-evident log is based on *measurements* utilizing hardware features that make it impossible to forge.
5. **No SUID/SGID or File Capabilities**. The SUID and SGID file access bits are a fundamental privilege escalation mechanism in classic UNIX and have led to a very large number of exploits. On AOS the SUID and SGID bits are therefore disabled completely. Privilege elevation happens securely via IPC such that a suitably privileged process performs operations on behalf of less privileged code.
6. **Integrity Is Mandatory**. A modern operating system must provide integrity guarantees well beyond traditional systems. It is a conditio sine qua non given the advent of LLM agents. On AOS everything is measured, attested, and comes with fundamental protection mechanisms. For example, all file system images we ship come with block-level Verity and encryption securing complex file system data structures.
7. **Factory Reset Is Built In**. Any operating system must consider the possibility that it will be hacked. For this reason, a secure OS must come with a “[factory reset](https://www.freedesktop.org/software/systemd/man/latest/systemd-factory-reset.html)” mechanism. AOS makes a lot of exploits *visible* in its Ledger. With factory reset it gains the ability to *act* and put the system back into a good state.

## Summary

**TL;DR**: Putting this all together, Amutable Foundations’ AOS and ACP provide:

- A modern image-based OS, with far-reaching compatibility with classic Linux distributions
- AOS is fundamentally designed with security in mind, removing a large portion of the attack surface of classic Linux systems
- Composition, lifetime and resources of nodes are centrally tracked in the ledger, with tamper-evident properties, via measurements
- The system covers both OS updates and configuration management via the same (or similar) mechanisms
- Each node comes with a robust, powerful API to execute operations on it
- Opportunistic support for modern security hardware (TPM 2.0, CoCo), with graceful degradation to all-software signatures where unavailable
- Integrity checks every step of the way, via both local and remote attestation
- Custom configuration and resources are only available to the machine if it is in the expected state

## Sign Up for Our Private Preview Now!

If you are interested in the experience we described above, please [sign up for the Amutable Foundations Private Preview](https://amutable.com/preview) to get a chance to try AOS and ACP first-hand yourself.
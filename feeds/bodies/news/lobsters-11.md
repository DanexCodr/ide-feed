*Bitdefender Labs researchers found that installing a specially crafted app can leave an Android phone stuck in a crash loop, even if you never open it or grant it a single permission. The app contains no code and never needs to run.  *

After installation, a core system process crashes, restarts, and crashes again, leaving the phone stuck in a boot loop. Restarting doesn't help, and neither does safe mode.

To get the phone working again, you need a factory reset, which erases the user's data. If, by chance, USB debugging had already been enabled, you could use a computer with ADB (Android Debug Bridge) to delete the file before the phone reboots.

We began investigating on Aug. 12, 2026, when an APK collected from the wild crashed emulators in our analysis infrastructure. The sample was a banking dropper that never ran and crashed during installation.

When we looked closer to find out why, we found the problem wasn't the malware—it was the Android itself. The operating system mishandles two fields inside a ZIP entry, the compression method and the declared uncompressed length. Reading such an entry causes a SIGBUS (a signal sent by the CPU to stop a process that accesses an invalid memory space) in whichever process touches the file.

We call it **GhostMap**: the malformed entry causes Android to map the file across memory that was never allocated, and the crash occurs when a process reads from that empty space.

Based on our testing, we consider the risk posed by this bug to be significant. In theory, an attacker could hide this technique in a fake app to disable a victim’s phone, or use the threat of a factory reset and data loss as leverage for extortion. Malformed APKs could also disrupt tools that inspect Android applications. We have not observed any of these scenarios in the wild.

The banking dropper was wrapped by a packer. This is a tool that rewrites an APK's internal structure so reverse-engineering tools can't read it. It’s very common in modern Android malware.

In this case, the same rewrite also broke the Android component that parses an app during installation. That’s why the installation crashed in the first place and why our emulators failed on it. The good news is that nothing in the sample suggests the author knew the file would crash anything.

The sample did no more than that—a failed install. The underlying flaw runs deeper. We found that the same mistake can be aimed at a core system service instead of the installer, and there it produces the repeating crash loop described above, with no way back except a factory reset. That escalation is our own work; we have not seen it used against anyone.

The underlying problem concerns how Android trusts size and compression information in APK files, and it’s not limited to malformed ZIP files.

We reported the issue to Google twice through the Android & Devices Vulnerability Reward Program, expanding the second submission after further testing confirmed a persistent system crash loop.

**August 12, 2026 — Initial discovery.** An APK collected from the wild crashed emulators in our analysis infrastructure during installation. Our investigation traced the failure to Android’s handling of ZIP entry compression methods and declared uncompressed length.

We also found that applications using Android’s native APIs to parse APKs could crash when reading them.

We reproduced the bug and made more discoveries. Every attempt to install that APK crashed the OS and caused a reboot:

**Aug. 20, 2026 — First report to Google.** We submitted these findings, documenting installation-triggered crashes and failures in applications parsing the malformed APK. Google closed the report shortly afterwards with the status *Won’t Fix (Not Reproducible)*. Its accompanying response described the submission as outside the program’s scope.

**Further investigation — Persistent denial of service.** We continued testing and found an APK that installed successfully but caused a system service to crash when it automatically read an application resource. The resulting crash loop prevented access to the interface and continued in safe mode. Recovery could require a factory reset.

We started investigating further after that. We found that we could also malform other files that are not parsed at install time, and that some Android system services try to parse them automatically. This meant the loop followed the regular path: crash, reboot, parse again, and then get stuck in a boot loop once more.

The boot loop we caused would also disable safe-mode access, and the only recovery methods we identified were a factory reset or, in limited conditions, ADB-based scripts racing with the system-server crashes.

Interestingly, Google has already patched a weaker version of this defect. From the November 2016 bulletin, **CVE-2016-6724**:

> *A denial of service vulnerability in the Input Manager Service could enable a local malicious application to cause the device to continually reboot. This issue is rated as Moderate because it is a temporary denial of service that requires a factory reset to fix.*

Rated Moderate, fixed across Android 4.4.4 to 7.0. In 2016 Google described a condition requiring a factory reset as temporary; in our reading, Google’s current published severity guidelines describe such a condition as persistent and rate it High.

**Aug. 25, 2026 — Second report to Google.** We submitted the expanded findings, including a working proof of concept and reproduction instructions. The report explained that the application requires no permissions, contains no executable code, and never needs to launch.

Google responded shortly afterwards, stating that it considered the issue outside the scope of a security update fix. Google also stated that it had forwarded the finding to the relevant team for review and possible inclusion in a future version update.

This type of bug, also known as a parser differential vulnerability, is something that Android has struggled with for more than a decade.

In 2014, security researchers published a paper titled [Leaving our ZIP undone: How to abuse zip to deliver malware apps](https://virusbulletin.com/uploads/pdf/conference/vb2014/VB2014-Panakkal.pdf), which explores, among other things, malformations that can be applied to APK files to bypass typical AV engine unarchiving. So, it’s not unknown in the Android ecosystem.

An APK is really a ZIP file, and a ZIP file stores the same information, such as sizes, offsets, and compression flags, in multiple places without checking that the copies agree.

Android reads an APK many times over: to verify its signature, to install it, to load its resources, to run its code, and every time a security tool scans it. These are separate pieces of code, and nothing forces them to read the file the same way.

When two of them reach different conclusions about the same bytes, you get a security bug, like these ones.

[**Master Key**](https://nvd.nist.gov/vuln/detail/CVE-2013-4787)** (2013, CVE-2013-4787).** An APK contained two files with the same name. Android checked the signature on the first and installed the second, so malicious code got in under a valid signature.

[**Janus**](https://nvd.nist.gov/vuln/detail/CVE-2017-13156)** (2017, CVE-2017-13156).** A single file could be a valid APK and a valid DEX at the same time. The signature check looked only at the ZIP entries and ignored extra bytes added to the front of the file, and the system then ran those bytes. The checker and the loader disagreed about where the file even started.

**BadPack (2024).** Malware authors deliberately corrupt the ZIP headers so that analysis tools fail to open the file while phones install it without complaint. Rather than exploit differences between two parsers on the same Android device, this class targets differences between what Android uses to install an APK and what other parsers analysts and security solutions use to screen an APK.

Palo Alto's [Unit 42](https://unit42.paloaltonetworks.com/apk-badpack-malware-tampered-headers/) found about 9,200 such samples in a single year, used by banking trojans including Anatsa, Cerberus and BianLian. This is the kind of packing our sample used.

The bug we describe comes from a similar disagreement, but it’s not used to sneak anything through. Instead, the disagreement results in a crash for the process trying to read the file.

Every entry inside a ZIP file records how it’s stored and how big it is. Android stores entries in two ways: *stored*, where the bytes are kept as they are, and *deflated*, where they are compressed and have to be expanded when read.

Each entry has two sizes: the compressed size, which is how many bytes are actually stored in the file, and the uncompressed size, which is how many bytes you get after expanding it. For a stored entry, the two are equal; for a deflated one, the uncompressed size is larger.

When Android opens an APK, a library called libziparchive reads these records and sanity-checks them. One of those checks ensures that an entry's uncompressed size doesn't claim to be larger than the space the file actually has. But that check only runs for stored entries:

```bash
// system/libziparchive/zip_archive.cc 

if (data->method == kCompressStored && 

    data->uncompressed_length > cd_offset - data_offset) { 

  return kInvalidOffset;   // reject 

} 
```

For any other storage method, this check is skipped. It’s fine for deflated entries because there the uncompressed size only determines how large a temporary buffer to allocate, while the data read from the file is bounded by the compressed size instead.

The problem is that *stored* and *deflated* are not the only values the method field can hold. It’s a 16-bit number, so it can be anything; Android supports two of those values, and the ZIP format allows the rest.

And when a second library, libandroidfw, reads the entry to load it as a resource, it asks a different question. It doesn't check for *stored* — it checks for *deflated*, and treats everything else as stored:

```bash
// frameworks/base/libs/androidfw/AssetsProvider.cpp 

if (entry.method == kCompressDeflated) { 

  // map compressed_length, then decompress 

} else { 

  // map entry.uncompressed_length directly  <-- never bounds-checked 

} 
```

The two libraries classify entries differently. libziparchive checks only the uncompressed size when an entry is marked *stored*. libandroidfw maps the file at the uncompressed size whenever an entry is *not* marked *deflated*. An entry marked with some other method — neither stored nor deflated — falls into the gap between those two rules: libandroidfw maps it at its uncompressed size because it isn't deflated, and libziparchive never checks that size because it wasn't stored.

That last step is a memory map. Android doesn't copy the entry into memory; it maps the file, asking the kernel to make part of the file appear as memory. You can ask for a mapping larger than the file, and the kernel allows it because the extra space just has nothing behind it.

Nothing goes wrong until something reads from that space. The first time Android reads past the real end of the file, the processor faults. Because nothing in this path is prepared to handle that fault, the kernel kills the process with a SIGBUS.

On our Pixel 10 the crash record (the tombstone Android writes when a process dies) points straight at that mapped read:

```bash
#00  __memcpy_aarch64_simd                 libc.so 

#01  android::_FileAsset::read             libandroidfw.so 

#02  android::NativeAssetReadChar          libandroid_runtime.so 

#03  art_jni_trampoline                    boot-framework.oat 

#04  AssetManager$AssetInputStream.read    (framework) 
```

The same record shows why: an APK of a few kilobytes was mapped across sixteen megabytes of memory, and the fault address lands well past the end of the file, in the empty region the declared size invented. The read walked off the file, and the kernel stopped it.

There are two different ways that an oversized mapping can cause a crash, depending on how the code reads it.

The first is the one in the tombstone above: a process reads the entry a piece at a time. Each read is bounded only by the declared size, so the reads keep going past the real end of the file until one of them touches the empty space and faults.

The second occurs when a process asks for the whole entry at once, as a single block of memory, which is what Android does when it loads an XML resource or an app's icon. Before handing the block over, it checks whether the mapped bytes are aligned the way the processor needs them.

If they are, it passes them through. If they are not, it makes an aligned copy and it allocates a buffer the size of the declared length and copies that many bytes into it:

```bash
// frameworks/base/libs/androidfw/Asset.cpp  (_FileAsset::ensureAlignment) 

unsigned char* buf = new unsigned char[mLength];   // mLength = the declared size 

memcpy(buf, data.unsafe_ptr(), mLength);           // copy runs past the end of the file 
```

The declared length is the invented one, so the copy runs off the end of the file and faults, and this time while filling the buffer, not while reading from it.

The two paths fail in different functions but for the same reason, and between them they cover the two ways Android reads an entry: streaming it, a piece at a time, or loading it whole. Loading an entry whole is the path a resource or an icon takes — which is what makes the next step possible.

None of this is a problem Android failed to solve, as it gets the same decision right in two other places. libziparchive validates the uncompressed size correctly, but only for stored entries, as a few lines of code skip the check for everything else.

And a third library that maps ZIP entries, ZipFileRO, makes the safe choice: it uses the uncompressed size only for stored entries, and the compressed size for the rest. libandroidfw is the outlier: it splits on whether an entry is *deflated* instead of whether it is *stored*, so it maps the uncompressed size for entries that libziparchive never checked. But the best possible solution at all is to allow only stored and deflate methods and reject others as invalid.

The code that faults isn't tied to a single process. Many parts of Android read an app's resources: when it installs, while the system runs, and when another app inspects it. Any of them can be the one that reads the malformed entry. Which process crashes depends on which file inside the app is malformed and who reads it. That’s what turns a single bug into something an attacker can target.

**The installer.** The manifest is the first file Android reads when installing an app, so a malformed manifest crashes the installer and the install fails; the app never lands on the phone. This is all the sample that started our investigation did—a failed install, with nothing left behind.

**A core system service.** An app also includes files that Android reads after it is installed, not during. These are small resources the core system services parse when they go through the list of installed apps. Malform one of those, and the service that reads it is running inside system_server, the process that hosts most of Android.

It crashes, Android restarts it, and on restart the service goes through the installed apps again, reads the same file again, and crashes again. The phone never finishes starting. This is the crash loop: system_server dies and restarts every few seconds, with no app ever opened and nothing on screen to say which app is responsible.

Rebooting doesn't fix it—it closes the one way out. While the phone is still looping, a computer connected over ADB can sometimes delete the file between crashes, but Developer Mode has to be turned on beforehand. Also, after the first full kernel reboot, even that stops working because the crash happens very early in the boot order. Safe mode doesn't help either, because the service reads the file before safe mode takes effect.

**The calling process.** It need not be the installer or a system service at all. The same code runs in any process that reads an APK. Whichever process reads the one with the malformed entry is the process that crashes.

That original sample only ever crashed the installer. We reproduced and measured the persistent version (the crash loop) on current hardware; we haven’t seen it used against anyone.

**Disable the phone.** Malform a resource that a system service reads, and the crash lands in system_server — the crash loop from the previous section. The phone never starts in any usable form, and only a factory reset clears it; the reset erases everything on the phone.

In theory, an app built this way could make a phone unusable, forcing the owner to choose between a factory reset and a dead phone. Such a capability could be misused as leverage for extortion.

**Make a malicious app impossible to remove.** This one doesn't brick the phone. A working malicious app malforms its own icon. The phone keeps running, but the launcher, the app list in Settings, and the app's own info screen all crash when they try to draw that icon, and those are the screens the user would open to uninstall it. Every route to removing the app crashes before it can, so the app stays installed and the malware keeps running.

**Blind the security tools.** A malicious app can carry the malformation so that anything inspecting it crashes. Security apps scanning a new APK, an analysis sandbox or an automated pipeline—they all hand the file to the same Android parsing code and get the same crash.

Because it’s a native fault and not an ordinary error, the scanner cannot catch it and continue; it dies, the app is never flagged, and it stays on the device.

**Delivery through updates.** In theory, the malformed file would not need to be present at initial review and could be introduced later through an app update, which could affect many devices at once. We do not provide further details on this scenario.

The bug crashes processes; it doesn’t execute code, read data, or gain permissions it wasn’t given. It’s a denial-of-service issue, and these are uses the bug enables, not attacks we’ve seen in the wild.

This is a flaw in Android itself and, as of publication, no fix is available, so users have limited options on the device to prevent it. The most practical defense is to recognize the file before the bug is triggered.

That's possible because the malformation is visible in the file's structure, without installing or running the app. A scanner can distinguish a crafted file from a normal one by inspecting it, not by executing it.

In our testing, Bitdefender Mobile Security detects apps with this malformation when they reach the device, whether as a downloaded file or an already installed app, and warns the user. However, Android's security model **doesn't let a third-party app block an installation or remove another app** on its own, so acting on the warning still rests on the user. Other security solutions may offer similar protection.

We detect this threat as **Android.Riskware.Ghostmap.rA.**

The value is that the warning arrives before the crafted file is read: a flagged download can be deleted before it's installed, and a flagged app can be removed while the device is still usable. But it’s a race between the keen-eyed user and the Android device's parsing speed. Since the app doesn’t need to run, the user has little time to act.

Reproduced on a Pixel 10 running Android 17, August 5, 2026 security patch — build google/frankel/frankel:17/CP2A.260805.005/15828068:user/release-keys. We also tested this vulnerability on older releases and managed to reproduce it on versions starting with Android 10 and above.

**The crash.** The tombstone Android wrote when system_server died:

```bash
signal 7 (SIGBUS), code 2 (BUS_ADRERR), fault addr 0x…  (read) 

#00  __memcpy_aarch64_simd                 libc.so 

#01  android::_FileAsset::read             libandroidfw.so 

#02  android::NativeAssetReadChar          libandroid_runtime.so 

#03  art_jni_trampoline                    boot-framework.oat 

#04  AssetManager$AssetInputStream.read    (framework) 
```

The record marks the fault as a read. The faulting mapping shows the over-map directly — the APK on disk was a few kilobytes, but the entry was mapped across the size the file claimed, and the fault landed far past the file's real end:

```bash
file on disk:          8,408 bytes 

mapped region:    ~16,781,312 bytes   (≈ 16 MB, the size the entry declared) 

fault address:     ~197,000 bytes past the end of the file 
```

Memory the file never provided, read with no matching write past any buffer — an over-read, not memory corruption.

**A third-party app, the same fault.** The crash isn't limited to system_server. An ordinary installed app with no permissions, calling the standard getPackageArchiveInfo() to read the file — the call a scanner makes — dies inside the call:

```bash
signal 7 (SIGBUS), code 2 (BUS_ADRERR)  (read) 

#00  __memcpy_aarch64_simd                       libc.so 

#01  android::_FileAsset::getIncFsBuffer(bool)    libandroidfw.so 

#02  android::NativeOpenXml                       libandroid_runtime.so 

#04  android.content.res.ApkAssets.openXml        (framework) 

#05  ApkLiteParseUtils.parseApkLiteInner          (framework) 

#14  PackageManager.getPackageArchiveInfo         (framework) 
```

The app wrapped the call in catch (Throwable). It never ran — a native SIGBUS isn't a Java exception — so the process simply died. Frame #01 is the second fault site described earlier (the aligned-copy path; getIncFsBuffer is ensureAlignment inlined), so both crash paths are confirmed in practice, not just reasoned about.

**The loop.** Each crash is followed by a restart and another crash, a few seconds apart, with a new system_server process every time:

```bash
08:24:32  Fatal signal 7 (SIGBUS) in system_server (pid 14536) 

08:24:33  Zygote: system server (pid 14536) has terminated 

08:24:38  Fatal signal 7 (SIGBUS) in system_server (pid 15070) 

08:24:39  Zygote: system server (pid 15070) has terminated 

08:24:42  Fatal signal 7 (SIGBUS) in system_server (pid 15586) 

08:24:43  Zygote: system server (pid 15586) has terminated 
```

**Safe mode.** Entering safe mode doesn't help. The crash happens on the same cycle, after the safe-mode flag is set but before it takes effect:

```bash
WindowManager: SAFE MODE ENABLED 

libc: Fatal signal 7 (SIGBUS), code 2 (BUS_ADRERR) in system_server (pid 23886) 
```

The same sequence repeated on 72 crash cycles in that safe-mode run.

**The persistence.** From installing the app to the first crash was about a second. In one capture, the cycle then repeated 110 times. The screen stayed on the boot animation the whole time.

*This article is published by Bitdefender for information and research purposes only, to help users, researchers and security professionals understand and defend against the issue described. The information reflects our findings and assessment as of the date of publication and may change, including if Google releases a fix or provides further information. It is provided “as is”, without warranty of any kind, and does not constitute legal, technical or professional advice. *

*The attack scenarios described are hypothetical and are presented solely to illustrate the potential impact of the issue; Any use of this information to access, disrupt or damage devices or systems without authorization is prohibited and may be unlawful. Bitdefender is not liable for any misuse of the information in this article, to the extent permitted by applicable law. *

*Statements regarding Google's assessment and responses reflect our understanding of the communications received through the Android & Devices Vulnerability Reward Program and are not intended to characterize Google's internal processes. Detection results for Bitdefender Mobile Security are based on our internal testing at the time of publication; results may vary depending on device, configuration and version. *

*Android, Google and Pixel are trademarks of Google LLC. All other trademarks are the property of their respective owners and are used for identification purposes only; their use does not imply endorsement or affiliation. Code excerpts from the Android Open Source Project are © The Android Open Source Project and are reproduced for commentary under the Apache License 2.0. *

tags

### Author

Working as Team Lead in the Mobile Security & Forensics Unit, I am always ready to deal with the latest threats in the Android Ecosystem. I like to play the saxophone in my spare time and go fishing.
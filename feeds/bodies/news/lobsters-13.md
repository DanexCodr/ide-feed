We’ve identified multiple vulnerabilities in devices of the popular [SwitchBot](https://eu.switch-bot.com/) Lock Pro smart lock series.
The most critical, a cryptographic flaw in their bluetooth communication, allows everyone to silently open smart locks in a software-only attack.
No physical tampering is required.
Below is a video of the attack in action.

## Introduction[¶](https://neodyme.io/en/blog/switchbot#introduction)

Smart locks have become very popular in recent years.
Especially when it comes to AirBnB-style apartment sharing, but also in corporate environments and private accommodation, people enjoy having locks that don’t require physical keys.
So when it came to selecting targets for our regular IoT hacking team event, smart locks were a natural choice.

After some research we cam across the highly praised [Switchbot Lock Pro Combo](https://www.amazon.de/Lock-Pro-Touch-Fingerprint-Matter/dp/B0CR67GWML/?), including a key actuator, pin pad and smartphone app.
It is one of the best-rated and most-sold smart locks on Amazon.
For roughly 240€ (at the time of writing) it comes with a lot of features - and the Amazon reviewers are happy to share that it works as intended.

Features aside, our main interest was, of course, the device’s security.
So we ordered one and had a look.
Here is what we found out.

## Reversing the Lock[¶](https://neodyme.io/en/blog/switchbot#reversing-the-lock)

As usual when inspecting IoT devices, we wanted to get our hand on the firmware.
But before we dive into that, let’s first look into the target’s features and architecture.

### The Switchbot Pro Lock[¶](https://neodyme.io/en/blog/switchbot#the-switchbot-pro-lock)

The bundle comes with two hardware devices, an actuator and a key pad. The lock can further be controlled and configured via a smartphone app.

The actuator is mounted onto the inside of the door and encloses the door’s key.
When the door is supposed to open, the actuator simply turns the key in the lock.

The key pad is kept outside the door and communicates with the actuator over [Bluetooth Low Energy](https://de.wikipedia.org/wiki/Bluetooth_Low_Energy) (BLE).
A person can authenticate itself to the system either using a smart card/key fob, using a fingerprint, or - most commonly - by supplying a PIN.
The whole system can also be added to a WiFi network, making it possible to control the lock over the Internet.

Now that we have an idea of the feature set, we can start digging.

### Firmware Reversing[¶](https://neodyme.io/en/blog/switchbot#firmware-reversing)

When hacking a device, it is usually a good idea to first get your hands on its firmware.
There are various techniques for accomplishing this, [FLASH Dumping](https://neodyme.io/en/blog/drone_hacking_part_1/) for example.
Before starting to desolder chips, however, it makes sense to scrape the web for firmware artifacts.

With SwitchBot we got lucky, as the Android app contained the URL for a public S3 bucket containing firmware files.
Downloading and analysing these files we found two surprising architectural choices.
First, the key pad on the **outside** of the door actually controls the actuator on the **inside**, not the other way around.
Meaning that the key pad decides if a PIN, fingerprint or key fob is valid and then issues an “UNLOCK” command to the actuator.
Secondly, the communication between the key pad and actuator relies on an unprotected, clear-text BLE connection.
Authentication between key pad and actuator is done solely on the application level using a home-brewed mechanism.

While the first point already yields a significant attack surface (i.e. let’s dump the key pad and open the door), the second offers a code smell too good to pass up.
So we focussed our main energy on exploiting the BLE communication between key pad and actuator.

### Key Pad Communications[¶](https://neodyme.io/en/blog/switchbot#key-pad-communications)

Once the key pad and actuator are paired, they communicate using unprotected BLE.
Meaning that all security of the system depends on application-level protections.
So let’s find out how these protections work.

Upon pairing, the key pad and actuator agree on a *secret key*.
Then, everytime the key pad becomes active, it requests a so-called “[nonce](https://en.wikipedia.org/wiki/Cryptographic_nonce)” value from the actuator.
For our attack this does not matter.
It is noteworthy however, that the nonce is supposed to provide “freshness” between invocations of the protocol but that this implementation uses the same nonce for an entire “session” which can last for multiple commands.
After the nonce is received, the key pad encrypts a command, using the secret key and nonce, and sends said command over the BLE connection.
Such a command could, for example, be “lock the door”.

The following diagram illustrates how the BLE communication works.

![Communication between key pad and actuator (simplified)](https://neodyme.io/blog/switchbot/Comms_Switchbot.png)

*Communication between key pad and actuator (simplified)*

Simply by looking at the communication diagram we can see a potential problem: We might be able to simply replay previous “unlock” commands that we have captured.
However, that would require us to be within Bluetooth range, sniff the command, and then somehow replay it before the session ends.
Since we aren’t writing an academic paper but do actual research: This is boring.

**We want to be able to open the lock, first shot, without any physical tampering and without leaving traces.**

And, as it turns out, we can accomplish this. But first need some more background on the implementation.

### Communication Protection[¶](https://neodyme.io/en/blog/switchbot#communication-protection)

So the key pad/actuator communication is protected using secret-key encryption and a nonce.
Digging further into the implementation, and with the help of [community-developed libraries](https://github.com/jonghwanhyeon/python-switchbot), we found out how the encryption is done.

The commands are encrypted using the [AES](https://de.wikipedia.org/wiki/Advanced_Encryption_Standard) block cipher in counter (CTR) mode.
Now, counter mode is an interesting choice, because it doesn’t actually offer any integrity protection.
Furthermore, because of its design, turning a block cipher into a stream cipher, bit flips propagate 1:1 from ciphertext to plaintext.

![Counter mode encryption](https://neodyme.io/blog/switchbot/CTR.png)

*Counter mode encryption*

Meaning that: If we change a bit in a ciphertext, upon decryption by the actuator, this exact bit will also be changed in the decrypted plaintext.
This is a little-known, but often encountered vulnerability class.
So, let’s exploit this fact and open some doors!

## Exploiting the Lock[¶](https://neodyme.io/en/blog/switchbot#exploiting-the-lock)

A key observation helps us to mount our attack.
The key pad’s lock button always sends an encrypted LOCK command, even if the door is already locked.
Exploiting the fact that AES CTR is used, we only need to compute the difference between an encrypted LOCK and UNLOCK command.
When we XOR this difference (flipping all corresponding bits) into an encrypted LOCK command, the result will be a validly encrypted UNLOCK command.
It’s important to note here that this difference has to be computed only once, as it is identical across sessions and devices!
We therefore split the attack into a setup phase, run once, and an attack phase that opens a specific lock.

After the one-time setup, the attack works as follows:

- Press the lock button
- Sniff an encrypted LOCK command send via BLE
- Bit-flip the encrypted LOCK command into an encrypted UNLOCK command
- Send the bit-flipped command to the actuator
- The door opens

As we suspect a lot of vulnerable devices out there, we won’t publish our full exploit here.
But using an individual example, you can see why our attack works.
So, let’s work through it.

### Setup Phase[¶](https://neodyme.io/en/blog/switchbot#setup-phase)

Using one pair of encrypted LOCK and UNLOCK commands, intercepted via BLE, we can compute their XOR difference.
This difference is identical across all sessions and all locks using the same firmware.
Therefore, we can use this difference as a sort of “master key” to open all SwitchBot Pro locks.

Sniffing an encrypted LOCK and UNLOCK command is done easily using our acquired lock.
Then, we simply compute:

### Attack Phase[¶](https://neodyme.io/en/blog/switchbot#attack-phase)

Applying (XORing) this difference `diff` to the encryption of any LOCK command, independent of secret key and nonce, will yield an encrypted unlock command, which we can then send to the actuator.

So, simply by applying our pre-computed, lock-independent, difference vector, we can turn *every* SwitchBot Pro LOCK command into an UNLOCK command.
And we can always capture encrypted LOCK commands on any key pad, simply by pressing the lock button.
Neat!

### Proof of Concept Exploit[¶](https://neodyme.io/en/blog/switchbot#proof-of-concept-exploit)

We’ve recorded our attack in action.
The video shows the components and our Bluetooth antenna used for sniffing the encrypted LOCK command.
On the left you can see the Python script applying the difference to the encrypted LOCK command and sending the crafted encrypted UNLOCK command.
The right side of the screen shows that the attack worked:
First, a LOCK command is issued by pressing the lock button.
Then, the crafted UNLOCK command is send and the actuator turns the key, opening the door `\o/`.

It all happens very fast, so maybe you have to re-watch a couple of times to grasp everything.

### Responsible Disclosure and Insufficient Fix[¶](https://neodyme.io/en/blog/switchbot#responsible-disclosure-and-insufficient-fix)

In accordance with our responsible disclosure guidelines, we notified the SwitchBot team of our findings.
They were very responsive (kudos!) and seemed to take the vulnerability seriously.
They awarded us a 100€ Amazon voucher for our work.

Before they rolled out a firmware patch, they allowed us to have a look at the updated firmware files.

After we reversed the new firmware, we discovered that they now append a “checksum” to every command.
We reimplemented the checksum computation in Python:

So the system now calculates an MD5 hash of the command, secret key and nonce.
The first **two bytes** of this hash then serve as verification tag.
This construction is sometimes referred to as [YOLO hash](https://blog.trailofbits.com/2024/08/21/yolo-is-not-a-valid-hash-construction/) and rarely a good idea.
Here in particular, the truncation to two bytes allows us to, in principle, brute force all 65,536 possible verification tags.
However, this is not necessary.

Because, to our surprise, just the communication between the key pad and actuator got updated.
The smartphone app still does not use a verification tag.
Which means that our attack still works 1:1, we just need to compute (once!) the difference between a key pad’s encrypted LOCK command and a smartphone issued UNLOCK command.
We can then mount our attack using this difference vector, as the actuator then thinks the UNLOCK command comes from a smartphone and does not check the verification tag.
We have verified that this variant of our attack works.

When we reported this bypass, SwitchBot provided the following context:

> The test firmware pushed to you only includes updates for the Keypad and Lock. The APP has not yet been updated with the new encryption method. We are currently working on implementing encryption upgrades for both the APP and the backend, and the Lock will no longer be compatible with the old encryption method. We need to ensure that this update does not affect other products bound to the APP […].

Backward compatibility is always challenging, especially when it comes to security and IoT devices out in the field.

## Further Attack Surface[¶](https://neodyme.io/en/blog/switchbot#further-attack-surface)

As we were happy with our full compromise, we did not look too much into other avenues of attack.
Noteworthy, however, was that the key pad uses MIFARE Classic 1K key fobs.
These are long broken and can be trivially cloned, e.g., using a [Flipper Zero](https://flipper.net/).
In order to mount this cloning attack, you’d have to get close to a key fob first.

Additionally, while testing the Bluetooth attack, we noticed that the key pad has a tamper detection.
If it is removed from the wall, it will play a loud alarm sound and inform the owners via their smartphone.
This is implemented using a Hall effect sensor on top of the key pad and can therefore be defeated using a strong magnet.
We recommend Neodymium magnets for such purposes ;).

![Switchbot Keypad Components](https://neodyme.io/blog/switchbot/keypad_tamper.png)

*Switchbot Keypad Components*

## Disclosure timeline[¶](https://neodyme.io/en/blog/switchbot#disclosure-timeline)

| Date | Action |
| --- | --- |
| **15.07.2025** | Initial Report is sent |
| **15.07.2025** | SwitchBot replies with additional questions |
| **15.07.2025** | More context is provided |
| **17.07.2025** | SwitchBot offers us to beta-test their patch |
| **06.08.2025** | SwitchBot pushes the update to our account |
| **13.08.2025** | We report our patch circumvention |
| **18.08.2025** | We report multiple more patch circumventions |
| **27.08.2025** | SwitchBot informs us, that it will take 6 months for them to update the rest of their ecosystem |
| **12.09.2025** | SwitchBot sends us an Amazon voucher 🎉 |
| **March 2026** | SwitchBot makes an updated version available |
| **02.04.2026** | SwitchBot shares an updated version with us; we confirm that the described vulnerability does not work anymore |
| **09.10.2026** | CVE published |

## Fixed Versions[¶](https://neodyme.io/en/blog/switchbot#fixed-versions)

According to SwitchBot, the following versions should have the relevant fixes installed.

**Lock:**

- SwitchBot Lock: V7.7 and later
- SwitchBot Lock Pro: V3.7 and later
- SwitchBot Lock WiFi: V15.21 and later
- SwitchBot Lock Ultra: V2.8 and later
- SwitchBot Lock Lite: V7.7 and later

**Keypad:**

- SwitchBot Keypad: V2.9 and later
- SwitchBot Keypad Touch: V2.9 and later
- SwitchBot Keypad Vision: V2.5 and later
- SwitchBot Keypad Vision Pro: V1.0 and later

**App:**
SwitchBot App: V9.18 and later

## Conclusion[¶](https://neodyme.io/en/blog/switchbot#conclusion)

Security is hard and IoT devices often times lack good protections.
We have to give credit to SwitchBot for even trying to secure their system.
Many IoT manufacturers don’t even do that.
Hacking this smart lock was a good reminder about the threats IoT devices can pose.
Even the more expensive, highly sought after products, are not necessarily immune to attack.

Vulnerabilities like these arise from developers’ mistaken assumptions.
In fact, misusing crypto primitives like AES-CTR, aka. cryptographic failure, is one of the most common software security vulnerabilities according [OWASP](https://owasp.org/Top10/2025/).
As it turns out, we [offer a cutting-edge Black Hat training on crypto vulnerabilities](https://blackhat.com/europe/training/schedule/index.html?track%5B%5D=crypto#black-hat-cryptography-attacks-tools-amp-techniques-54313) and [audits](https://neodyme.io/en/reports/) and [testing](https://neodyme.io/en/pentests/) to help with exactly that!
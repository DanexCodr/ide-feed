Modern processors are fast, in part, because they guess. Rather than waiting to find out which way a program will branch, a chip predicts the likely path and races ahead. When the guess is right, time is saved. When it's wrong, the work is discarded, but traces of it linger. Since the [Spectre](https://news.mit.edu/2018/mit-csail-dawg-better-security-against-spectre-meltdown-attacks-1018) vulnerability was disclosed in 2018, attackers have known how to read those traces to pull secrets out of memory they should never see.

Chipmakers and operating system developers have spent years building defenses. A [new study](https://people.csail.mit.edu/mengjia/data/2026.USENIX.TONTOU.pdf) from MIT's Computer Science and Artificial Intelligence Laboratory (CSAIL) shows that a key assumption behind many of them doesn't hold.

The defenses work by wiping or isolating the processor's prediction machinery, removing anything an attacker might have planted. The catch, as Daniël Trujillo, a PhD student in the MIT Department of Electrical Engineering and Computer Science (EECS), and Mengjia Yan, an assistant professor in EECS, point out, is that the wipe and the moment the predictions get used can't happen at the same instant. There is always a gap — sometimes only a handful of instructions wide. Anything that runs in that gap can dirty the machinery all over again. The researchers call this class of attack "[TONTOU](https://people.csail.mit.edu/mengjia/data/2026.USENIX.TONTOU.pdf)."

**Mind the gap**

Their contribution is a reliable way to get code into that gap. Computers constantly pause whatever they're doing to handle interrupts: small, routine tasks triggered by timers, network traffic, and hardware. Ordinary programs can set those timers themselves. By tuning a timer with enough precision, Trujillo and Yan can make the processor take its detour at exactly the wrong moment, and the interrupt execution does the contaminating. They call the technique "interrupt injection."

The team tested four processor generations from Intel and AMD, and got mispredictions on both. On Intel chips, the attack defeated two different protections, one built in software for older parts, one built into the silicon of newer ones. Curiously, the newer protection held firm on one Intel generation and failed on another, suggesting chipmakers implement the same nominal defense in meaningfully different ways.

AMD's defense, called saferet, cleans the prediction machinery immediately before each use, leaving a vulnerable window just two instructions wide, which typically execute within tens of nanoseconds. The researchers hit it anyway, by slowing down the processor at that exact spot to make the target easier to strike.

**From a bad guess to a password file**

To show what this means in practice, the team built a working exploit on an AMD system running a current Linux kernel. They first stripped away a defense that scrambles where the operating system sits in memory, succeeding in all 10 tries in about nine minutes each. That helped them read protected memory at roughly five bytes per second — slow, but fast enough to locate and copy "/etc/shadow," the file storing the system's root password hash, in half their attempts.

The paper suggests cleaning the prediction machinery a second time, when the interrupt finishes. That looks workable on AMD. On Intel it may backfire: Because the attack relies on the interrupt leaving behind a consistent state rather than any particular one, the standard fix could make the attack more reliable, not less. Newer Intel chips include a dedicated instruction that appears to help.

The other option, blocking interrupts during the vulnerable window, would likely cost too much performance to be practical.

Trujillo and Yan notified AMD and Intel in early February and reached Linux kernel maintainers in March, coordinating with AMD to warn cloud providers and other downstream customers. AMD then released a patch that mitigates the attack, which can be obtained by updating your operating system. Their code is publicly available.

The research was supported, in part, by the U.S. Air Force Office of Scientific Research under an award made through the U.S. Department of War, and ACE, one of the seven centers in JUMP 2.0, a program sponsored by the U.S. Defense Advanced Research Projects Agency (DARPA). It was presented at both Black Hat USA and USENIX Security this month.
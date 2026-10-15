Ledger has confirmed that some of its devices distributed through Southeast Asian reseller CryptoBilis were compromised with a hardware implant that drained users' cryptocurrency wallets.

The company has been investigating reports of users losing funds from wallets purchased through CryptoBilis, a major Malaysia-based hardware wallet retailer operating across Southeast Asia.

Some researchers have shown the implant in Ledger X since September 16, saying tampered devices were available for nearly half the price of the original hardware.

Ledger wallets are physical devices designed to securely store the private keys that control cryptocurrency assets and authorize transactions.

On October 9, Ledger said it had launched an investigation into user reports of cryptocurrency losses and asked CryptoBilis to stop selling and shipping Ledger devices.

[![Ledger](https://www.bleepstatic.com/images/news/u/1220909/2026/October/ledger.png)](https://x.com/Ledger_Support/status/2108551100613714002)

The next day, the company confirmed hardware tampering on at least one device, though it’s still unclear exactly how or when the devices were tampered with.

"Ledger can confirm that one of the impacted users’ devices contained an unauthorized hardware implant. Ledger is reaching out to impacted users as part of the ongoing investigation," Ledger said.

The crypto wallet maker also noted that it was working with authorities to identify the perpetrator and bring them to justice.

“[...]Ledger recommends users who purchased a Ledger device from this reseller to not initiate set up if they have not yet done so. If you have set up your Ledger device, consider moving assets to a new Ledger signer (with a new seed),” [warned Ledger](https://x.com/ledger_support/status/2108968264055345381).

Yesterday, Ledger [provided another update](https://x.com/Ledger/status/2109331538072494364), confirming that all user reports of unexpected fund drains were linked to devices sold through CryptoBilis and describing the affected volume as “limited.”

While the company did not disclose the type of devices compromised in this supply-chain attack, reports online talk about a spy implant in Ledger X devices that blends with the legitimate hardware.

Mark Karpelès, currently leading Karpeles Lab Inc. and CTO at Shells.com, showed a picture of the new implant in Ledger X, saying that it was "quite an evolution" from previous versions featuring manually soldered wires.

The former CEO of Mt. Gox said the implant was concealed behind the screen, but its antenna cable would have indicated that something was wrong.

According to Karpelès, the malicious hardware captured the device's display output and button presses to identify the seed phrase, then transmitted it to the attacker over an LTE connection using an eSIM.

"Ledger Nano X are used to store crypto. The spy implants are used to steal whatever crypto you store in those Ledger Nano X," [Karpelès explained](https://x.com/MagicalTux/status/2100131628815405511).

Although the CEO did not name CryptoBilis as the vendor of the compromised LedgerX, he said the device was not purchased via Ledger's recommended channels but from "a well known platform via a Chinese seller (product shipped from Malaysia)."

Tibane Labs, a cryptocurrency research and development studio, confirmed Karpelès' finding, adding that there were two implant versions for Ledger X.

The researchers obtained two variants, one in a Ledger device bought on Amazon Japan from " China-based seller · shipped from Malaysia," the other purchased on Yahoo! Auctions, Japan.

In a report over the weekend, Tibane Labs notes that the threat actor made room for the malicious circuitry by replacing the original battery with a smaller one, which powers both the implant and the Ledger X.

"Under the battery and antenna sits an ST STM32G431KBU6 (Arm Cortex‑M4, 128 KB flash, UFQFPN‑32)," the researchers found inside one of the devices.

For connectivity, the actor used "a tiny eSIM, an 8‑pad package just 2×2 mm, next to the MCU, and a shielded LTE module that sends the words out."

In the second hardware wallet analyzed, [Tibane researchers found](https://www.tibane.net/research/ledger-nano-x-implant) that markings on both the MCU (Microcontroller Unit) and the eSIM had been scraped off to hide the part numbers.

The second variant, which appears to be the same one that Karpelès described, is more advanced. It ran on the original battery and fit into the space normally occupied by the foam padding under the OLED display.

In both cases, the tell tale was the antenna wire, which ran along the top edge in the case of the second implant. In the first implant, the antenna is taped across the top of the battery and the shielded LTE module.

The researchers warned that the specimen above used "a designed, panelised flex PCB, the kind ordered from a board house, not a hand-built one-off."

Ledger is advising users to avoid purchasing from unauthorized resellers as they run an increased risk of getting counterfeit or modified devices.

The company is also reminding its authorized resellers and distributors to get the products only through authorized channels and to avoid restocking returned products.

Ledger provides a ‘Genuine Check’ mechanism to determine the authenticity of the device; however, it [explicitly warns](https://support.ledger.com/article/4404382029329-zd) that it cannot detect added implants when the device’s original Secure Element remains intact.

At this time, there’s no indication that any other Ledger resellers are shipping compromised wallets; however, the community’s trust in the resellers’ network has been compromised, with many now calling for its dismantling.

Join Mikko Hyppönen and security leaders from the NFL, CHANEL, and Atlassian for a two-hour digital summit on what AI-speed attacks change, what defenders should stop doing, and how to validate, decide, fix, and re-validate at machine speed.

### Comments

- ![tubrazysj Photo](https://www.bleepingcomputer.com/forums/public/style_images/master/profile/default_large.png) [tubrazysj](https://www.bleepingcomputer.com/forums/u/1400173/tubrazysj/) - 1 day ago A genuine-device verification check is not enough if a physical implant can bypass the user's security assumptions. Hardware wallet providers and distributors need robust anti-tampering controls, transparent incident reporting, and clear consumer remediation procedures. In crypto, security is not just a technical issue; it is also a matter of consumer protection and legal responsibility.
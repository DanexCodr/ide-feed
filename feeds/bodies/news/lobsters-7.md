This post surveys some concerning attacks on TEEs.
The goal is to persuade you to re-consider how you deploy TEE-based applications, if you should deploy them at all.
more

Trusted hardware companies (Intel, AMD, etc.) mainly compete on performance, functionality and (one hopes) developer-friendliness.
They may try to compete on security, but this is hard, in my opinion: there’s always someone else who can (mis)claim more security and such claims are hard to adjudicate by the market.
Furthermore, the complexity of modern CPU architectures and the pervasiveness of side-channels makes TEE security claims tenuous.

In any case, (some of) the TEE attacks follow below.

## Bugs in the enclave code

Enclaves are meant to protect secrets and integrity of computation from the environment (e.g., host OS, or even the physical environment).
But even if the enclave platform is secure, bugs in the code running in the enclave can lead to disaster.

- Signal’s contact discovery enclave had memory safety issues that allowed the host to confuse it and caused the enclave to leak its own memory contents[1](https://alinush.github.io//tee#fn:signal-sgx).

## TEE remote attestation forgery bugs

Many of these attacks impacted not only Intel SGX but other TEE platforms as well, like AMD SEV.

- 2018, Foreshadow: malicious OS can steal Intel SGX attestation key (for the first time!)
- 2020, SGAxe: needs ring-0 access to steal SGX attestation key (this was the 2nd time!)
- 2022, ÆPIC Leak: microarchitectural bug allows host root admin to steal SGX attestation key
- 2024, BadRAM[2](https://alinush.github.io//tee#fn:DWOplus25), tampered DIMM SPD chip on AMD SEV-SNP systems
  - A host root admin with one-time physical access (~$10 to reprogram the DIMM) can run a backdoored VM while the genuine AMD chip signs a report attesting to the benign VM (no key is extracted, but the attestation is false).
- 2025, WireTap.fail[3](https://alinush.github.io//tee#fn:SDAplus25), interposition physical attack for DDR4 systems
  - “We have successfully extracted attestation keys, which are the primary mechanism used to determine whether code is running under SGX. This allows any hacker to masquerade as genuine SGX hardware, while in fact running code in an exposed manner and peeking into your data. We demonstrate concrete security breaks on real-world software utilizing SGX, such as Secret Network, Phala, Crust, and IntegriTEE.”
- 2025, TEE.fail[4](https://alinush.github.io//tee#fn:CSBplus26), interposition physical attack for DDR5 systems
- 2025, Battering RAM, interposition physical attack for DDR4 systems
- 2026, DDRrop[5](https://alinush.github.io//tee#fn:DGJplus26), interposition physical attack for DDR5 systems by dropping writes
  - Intel TDX remote attestation forgery

You may say: *“I don’t care; my threat model precludes physical attacks.”*
No it doesn’t, silly: your remote attestation verifier accepts a quote from *any* Intel CPU in good standing.
And the attacker’s CPU is one of them.
A break of one is a break of all, unless…

Unless: you pin your verifier to only accept your own PCK certificates<sup>[6](https://alinush.github.io//tee#fn:epid)</sup>, which implicitly excludes the attacker’s CPU.
This works for so-called [scalable SGX](https://www.intel.com/content/www/us/en/content-details/843058/supporting-intel-sgx-on-multisocket-platforms.html) (the only flavor left) and requires you to carefully manage a PKI.
So, effectively requires you to wield a footgun.
Good luck!

## TEE liveness bugs

DoS is explicitly outside the threat model of SGX, TDX, SEV-SNP and Nitro (b.c. the host can simply refuse to schedule the enclave).
So, here, we focus on liveness issues due to issues with the TEE platform itself.

- 2018, Revocation of SGX credentials in light of Spectre/Meltdown left TEE enclaves paralyzed
- 2022, SGX.fail[7](https://alinush.github.io//tee#fn:VSYplus22) details how slowly TCB recoveries roll out and how platforms can be left “out of date” for long stretches
- 2022, TPM Attestation Failure on AMD Platforms with ASP fTPM
  - Example impact: Gamers may be unable to compete in online cash tournaments.

## More academic paper attacks

In theory, there are ways to reduce the attack surface of trusted hardware.
For example, see Sanctum<sup>[11](https://alinush.github.io//tee#fn:CLD15e)</sup> from my group at MIT back in the day (shameless plug). 
Unfortunately, in practice, these more principled designs tend to come with lower performance and/or less functionality.

## Conclusion

Don’t put valuable secrets in your TEEs, or they’re likely to become public, especially if physical attacks are in your threat model<sup>[12](https://alinush.github.io//tee#fn:nuance)</sup>.

## References

For cited works, see below 👇👇

1. [Signal’s SGX-based contact discovery gets broken](https://x.com/v12sec/status/2092664320547254388) [↩](https://alinush.github.io//tee#fnref:signal-sgx)
2. **BadRAM}: Practical Memory Aliasing Attacks on Trusted Execution Environments**, by De Meulemeester, Jesse and Wilke, Luca and Oswald, David and Eisenbarth, Thomas and Verbauwhede, Ingrid and Van Bulck, Jo, *in 46th {IEEE} Symposium on Security and Privacy ({S\&P})*, 2025 [↩](https://alinush.github.io//tee#fnref:DWOplus25)
3. **WireTap: Breaking Server SGX via DRAM Bus Interposition**, by Alex Seto and Oytun Kuday Duran and Samy Amer and Jalen Chuang and Stephan van Schaik and Daniel Genkin and Christina Garman, *in 2025 SIGSAC Conference on Computer and Communications Security (CCS ‘25)*, 2025, [[URL]](https://wiretap.fail) [↩](https://alinush.github.io//tee#fnref:SDAplus25)
4. **TEE.fail: Breaking Trusted Execution Environments via DDR5 Memory Bus Interposition**, by Jalen Chuang and Alex Seto and Nicolas Berrios and Stephan van Schaik and Christina Garman and Daniel Genkin, *in 47th IEEE Symposium on Security and Privacy (IEEE S\&P ‘26)*, 2026, [[URL]](https://tee.fail) [↩](https://alinush.github.io//tee#fnref:CSBplus26)
5. **DDRop}: Active Memory Interposer Attacks on Confidential {VMs} by Dropping {DDR5} Writes**, by De Meulemeester, Jesse and Gloor, Stefan and Jattke, Patrick and Moghimi, Daniel and Oswald, David and Thompson, Martin and Razavi, Kaveh and Verbauwhede, Ingrid and Van Bulck, Jo, *in Proceedings of the 2026 {ACM} {SIGSAC} Conference on Computer and Communications Security ({CCS} ‘26)*, 2026 [↩](https://alinush.github.io//tee#fnref:DGJplus26)
6. It is my understanding that the “old” 2015 SGX architecture based on EPID is now retired. [↩](https://alinush.github.io//tee#fnref:epid)
7. **SoK}: {SGX.Fail}: How Stuff Get e{X}posed**, by van Schaik, Stephan and Seto, Alex and Yurek, Thomas and Batori, Adam and AlBassam, Bader and Garman, Christina and Genkin, Daniel and Miller, Andrew and Ronen, Eyal and Yarom, Yuval, 2022, [[URL]](https://sgx.fail) [↩](https://alinush.github.io//tee#fnref:VSYplus22) [↩<sup>2</sup>](https://alinush.github.io//tee#fnref:VSYplus22:1)
8. **CacheWarp}: Software-based Fault Injection using Selective State Reset**, by Zhang, Ruiyi and Gerlach, Lukas and Weber, Daniel and Hetterich, Lorenz and Lü, Youheng and Kogler, Andreas and Schwarz, Michael, *in 33rd USENIX Security Symposium (USENIX Security 24)*, 2024 [↩](https://alinush.github.io//tee#fnref:ZGWplus24)
9. **SEVered: Subverting AMD’s Virtual Machine Encryption**, by Mathias Morbitzer and Manuel Huber and Julian Horsch and Sascha Wessel, 2018, [[URL]](https://arxiv.org/abs/1805.09604) [↩](https://alinush.github.io//tee#fnref:MHHW18)
10. **CLKSCREW}: Exposing the Perils of {Security-Oblivious} Energy Management**, by Adrian Tang and Simha Sethumadhavan and Salvatore Stolfo, *in 26th USENIX Security Symposium (USENIX Security 17)*, 2017, [[URL]](https://www.usenix.org/conference/usenixsecurity17/technical-sessions/presentation/tang) [↩](https://alinush.github.io//tee#fnref:TSS17)
11. **Sanctum: Minimal Hardware Extensions for Strong Software Isolation**, by Victor Costan and Ilia Lebedev and Srinivas Devadas, *in Cryptology {ePrint} Archive, Paper 2015/564*, 2015, [[URL]](https://eprint.iacr.org/2015/564) [↩](https://alinush.github.io//tee#fnref:CLD15e)
12. For a more nuanced take, see [Andrew Miller’s post](https://medium.com/initc3org/tee-based-smart-contracts-and-sealing-pitfalls-eccd5d751329). [↩](https://alinush.github.io//tee#fnref:nuance)
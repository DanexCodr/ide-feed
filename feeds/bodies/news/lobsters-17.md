[Alice & Bob](https://alice-bob.com/), a French QC company, [claims (in a paper posted on cryptographers’ ePrint)](https://eprint.iacr.org/2026/2665) that a quantum computer they may eventually build could, with just **22,593 qubits**, break (factor) RSA-2048 in about **𝝅 ≈ 3.14 days**. As an orange–pineapple comparison, Google’s OMG press release in March was about a system with half a million qubits, to break 256-bit ECDLP.

As usual, several people have asked me how scary this is—and as usual some of them have decided that it’s actually scary and expect my confirmation, and ask me for justification when I say it’s not, so this post is kinda serving this purpose.

**The short answer: it’s interesting research, but we (well, A&B) are nowhere near having such a machine—and a lot of “ifs” are involved.   **

First, quick context: QCs use qubits instead of ordinary bits; a problem is that qubits are extremely fragile, errors happen frequently, they must be corrected, and correcting them requires… more qubits, running quantum error correction. That’s one of the main obstacles to building QCs.

A&B is developing a special type of qubit, which is a type of **cat qubit** (the “cat” is Schrödinger’s, a reference to the way cat qubits encode information). Cat qubits are designed to make *certain* errors rare. A&B built systems with up to 18 cat qubits.

The paper is essentially a thought experiment based on premise “*Imagine we could build a large quantum computer using **improved versions** of our qubits, then how efficiently could it break RSA-2048?” *It’s also sort a bit of a truism “*If we could build what’s necessary to break RSA-2048, then guess what…” *

A&B’s paper combines assumptions about future hardware with error correction techniques and an optimized implementation of Shor’s algorithms. Their calculations suggest that around 23,000 qubits would be sufficient.

**But there’s a major catch.**

Their main calculation assumes that a particular type of error (bit-flip) would occur, *on average*, only once every **100 years per qubit**. That’s a pretty low error rate for a qubit, even for a cat one:

![](https://www.bfswa.blog/p/fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fe69f645f-1133-44fa-9a6e-8d7711576375_1226x670.png)

For comparison, A&B’s published experiments demonstrated this kind of error occurring, on average, **once every few minutes** (under certain conditions and much more frequently during some quantum operations.)

The paper acknowledges a gap of more than **100 million times** between the assumed reliability and the experimental results it uses for comparison.

There’s also the scale detail: A&B has developed experimental systems with up to 18 qubits; they’d need another 22,575 qubits.

The paper mentions an alternative design with more realistic error rate assumptions, requiring around **45,000 qubits**. But again thus depends on error-correction techniques that haven’t yet been demonstrated.

I feel like competition among QC companies is increasingly a competition for attention; it encourages them to publish scary-looking numbers based on more or less plausible assumptions. To be fair, A&B’s paper is transparent about its assumptions and is solid quantum engineering work. The problem is less the research itself than how its results are presented and promoted.

So the research isnt worthless: estimating the resources needed to break crypto is important and improvements to quantum algorithms and architectures deserve attention. But **calculating what an hypothetical machine could do is different from demonstrating that we know how to build that machine**.

That’s the distinction you must keep in mind when reading OMG-quantum headlines.

Oh and another result (claimed under similar assumptions) is an architecture to solve **ECDLP in about one hour** with ~30,000 qubits:

![](https://www.bfswa.blog/p/fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fecccb9be-90a7-4271-8ed9-62342e589c3a_1224x1050.png)

Thanks for such a thoughtful post and debunking the scary title of this paper. It’s annoying to me that companies keep on producing assumptions that are hard to parse without deep expertise so they can feed into the cycle of quantum hype and media and PR and panic and amplification. Wish research now focused on helping companies and other choose what to migrate and figure out cheap tooling to facilitate PQC
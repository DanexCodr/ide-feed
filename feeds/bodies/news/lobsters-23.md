Recently, [Anthropic](https://www.anthropic.com/) published a research post in which they touted the [use of LLMs in formal software verification](https://www.anthropic.com/research/formal-verification). We’re excited that they’re excited! Of course, we’ve been talking about this all year (and before). We agree that AI makes formal software verification feasible in ways it simply wasn’t before. Here’s our latest example.

In July, the United States [National Security Agency](https://www.nsa.gov/) published to [GitHub](https://github.com/NationalSecurityAgency) a repository of formal specifications of cryptographic algorithms. They call the repository [Foundation](https://github.com/NationalSecurityAgency/Foundation). As a demonstration of their work, they include a proven Rust implementation of AES. Naturally, we saw this as an opportunity to demonstrate SPARK and, more importantly, SPARK + AI.

You can find our work on a fork [here](https://github.com/manthonyaiello/Foundation/tree/spark-v1.0); see the README in the `spark` folder [here](https://github.com/manthonyaiello/Foundation/tree/spark-v1.0/spark).

Using AI, we obtained formal specifications and proven implementations of AES (128, 192, 256), SHA-256, and HMAC-SHA-256 in SPARK. No direct human intervention was required, although we reviewed the specifications and offered minor stylistic (non-functional) improvements. This is SPARK Platinum code: full functional correctness. We are confident in the correctness of the work because we have verified correctness four different ways:

1. the SPARK specifications are proven to be functionally equivalent to the NSA’s Cryptol specifications for selected message, key, and text lengths;
2. the SPARK implementations are proven to satisfy their functional specifications;
3. the SPARK implementations are proven to be functionally equivalent to the NSA’s Cryptol specifications for selected message, key, and text lengths; and
4. the SPARK is tested against the Cryptol specifications

So even though the SPARK specifications and implementations were authored entirely by AI, we have (multiple) formal proofs plus extensive specification-based tests reaching 100% MC/DC coverage that the AI’s work is correct and complete.

## The NSA’s Foundation

Foundation is an NSA public repository of cryptographic algorithms that are formally specified using [Galois](https://www.galois.com/)’s Cryptol, a formal specification language designed specifically to specify cryptography. The NSA provides many algorithms; for some, they provide a reference implementation in Rust.

## Our Picks: AES, SHA-256, HMAC-SHA-256

As a starting point, we picked three algorithms:

The details of these algorithms are beyond the scope of this blog post; the links above lead to their Wikipedia entries.

We chose AES because it’s commonly used, because the NSA provided a Rust reference implementation, and because it’s challenging to specify.

We chose SHA-256 because it’s also commonly used, and having a second algorithm offers evidence that our approach is replicable (i.e., AES isn’t somehow especially easy for SPARK).

We chose HMAC because three is a nice number, and it builds on the SHA-256 work.

Additionally, these three algorithms illustrate different properties of interest:

- AES depends on arithmetic over the Galois fields GF(2) and GF(28);
- SHA-256 depends on modular word arithmetic and padding for variable-length messages; and
- HMAC depends on composition with streaming.

## What We Did

For each of the three algorithms, we followed the same process. The examples below will focus on AES.

### SPARK Specification

We wrote the SPARK specification from the Cryptol. Each SPARK specification is written so as to minimize the syntactic and semantic distance to the Cryptol: this makes it easier to read the two specifications side by side and validate the correctness of the SPARK.

Sometimes, this is very natural. For example, in Cryptol:

```plaintext
xTimes : [8] -> [8]
xTimes b = b << 1 ^ (if head b then 0x1b else 0x00)
```

And the matching SPARK:

```ada
function xTimes (B : Byte) return Byte
is (Interfaces.Shift_Left (B, 1) xor (if Head (B) then 16#1b# else 16#00#));
```

But Cryptol was designed to specify cryptography; SPARK is a general-purpose language. So there are a number of places in which we have to say rather more in SPARK or say it rather differently:

```plaintext
foreign Cipher : {k} (Key k) => [Nr k + 1]Block -> Block -> Block
Cipher ([w0] # ws # [wr]) in = state_final
  where
    state_initial    = AddRoundKey in w0
    state_rounds     = foldl Round state_initial ws
    state_final      = AddRoundKey (ShiftRows (SubBytes state_rounds)) wr
```

and the matching SPARK:

```ada
function Cipher (W : Round_Keys; Input : Block) return Block
is (AddRoundKey (ShiftRows (SubBytes
                   (Foldl_Round (AddRoundKey (Input, W (0)),
                                 W (1 .. Nr - 1)))),
                 W (Nr)));
```

Cryptol has primitives like `foldl`, `split/join`, and `pmult`/`pmod` (operations over GF(2) polynomials); in SPARK, we introduce these through a prelude.

The repository contains walkthroughs of the specifications that show the Cryptol and SPARK side-by-side and discuss the differences between them. You can find them [here](https://github.com/manthonyaiello/Foundation/tree/spark-v1.0/spark/doc/walkthroughs). Note that the SPARK specification is executable (as most SPARK specifications are); it is marked `Ghost` so that it can be removed at compile time.

Ultimately, we don’t have to validate the correctness of the SPARK specification via review; as we’ll show below, we prove functional equivalence between the SPARK specification and the Cryptol.

Correct specifications were obtained entirely automatically, with no human guidance needed. The original specifications were entirely readable and did an excellent job of minimizing the syntactic and semantic distance to the Cryptol specifications. We did review the AES specification carefully, however, and offered some feedback and suggestions for improvement that reduced the syntactic distance further. While helpful, these improvements were not strictly necessary.

### SPARK Implementation

The SPARK implementation links to the SPARK specification by stating that the postcondition on an operation is the matching function in the specification:

```ada
procedure Encrypt_Block (K : Key_Size; W : Round_Keys; State : in out Block)
with
  Pre  => Is_Round_Keys (K, W),
  Post => State = Spec.Dispatch.Cipher (K, W, State'Old);
```

The implementations are imperative. They contain loops, in-place state manipulation, and offer streaming for SHA-256 and HMAC.

The implementations were obtained entirely automatically, with no human guidance needed. The frontier AI wrote the implementation entirely on its own.

### SPARK Proof

Conceptually, there are three parts to the SPARK proof:

1. Proof of absence of runtime errors (SPARK Silver). We prove that neither the specification (should it be executed) nor the implementation (when it is executed) will ever see a runtime error. This becomes important later: one of our other proofs depends on this. It also allows us to turn off all runtime checks, which can improve performance.
2. Proof that the implementation satisfies the specification (SPARK Platinum, in this case). Since the Cryptol specification and hence the SPARK specification captures the complete functional requirements for our implementation, we have proved full functional correctness of the implementation.
3. Proof of putative properties of the specification (specification verification). Following the Cryptol, we prove, for example, that the tabular representation of the AES SBox complies with the functional statement of the SBox1.

In total, the proof consists of 4,085 checks over 71 SPARK units plus an additional 2,565 checks from the slow-running `SBox_Entries` proof that is run on demand. There are no escape hatches used: no SPARK_Mode => Off anywhere, no assumptions, no justifications. The proof burden is a mixed bag: 23 loop invariants; 83 assertions; and 87 calls to lemmas.

This proof was obtained entirely automatically, with no human guidance needed. The frontier AI handled the proof on its own.

### Testing with Cryptol’s FFI

Cryptol offers foreign-function interfacing using the C calling convention; SPARK exports C interfaces to its specification and implementation functions. We can thus state that a SPARK function equals its Cryptol counterpart, like this:

```plaintext
prop_xTimes : [8] -> Bit
property prop_xTimes b = spark_xTimes b == xTimes b

prop_Dot : [8] -> [8] -> Bit
property prop_Dot b c = spark_Dot b c == b • c
```

These properties are listed in a file and executed as tests in CI, using either Cryptol’s `check` or `exhaust` command. Cryptol must load the SPARK library and must not load another library (so we don’t, e.g., accidentally test SPARK against Rust) and must not report any errors during testing. Cryptol must report the number of tests passed and, for `exhaust`ive testing, must report Q.E.D.

While this testing is strong, it’s insufficient:

1. Of the 141 properties tested, only 36 have small enough domains that we can test with exhaust.
2. Check draws random inputs. We could achieve reproducible testing if we fixed the seed, but we chose not to, as testing is not our primary means of verification.
3. Check sizes are relatively small:
  1. 1000 runs per AES key size for block and key-expansion properties; whole-cipher properties run 5 each, because Cryptol is slow.
  2. For SHA-256 and HMAC, each random test checks one random input at a list of fixed lengths. prop_Stream_Hash, e.g., runs 100 tests at 11 boundary lengths from 0 to 128 bytes, yielding 1100 hashes. The _long properties run 3 tests at 10 lengths from 562 to 3837 bytes (Cryptol's reference hash is slow on long messages). So while the content is random, the lengths are not; nothing tests beyond 3837 bytes.

Our mutation testing provides the strongest evidence that our testing is not sufficient. Of the 84 one-line faults we inject into the implementations, the FFI-based testing only finds 68 of them. Of the 16 that pass testing, six are real bugs in `SHA256_Stream`. SPARK rejects all of these, albeit by timeout rather than finding a concrete counterexample.

Notably, we *do* obtain 100% MC/DC coverage when testing our implementations through Cryptol’s FFI. We have reasonable assurance that there is no unintended functionality present in our implementation as a result of obtaining this coverage from the specification-driven (hence requirements-based) testing<sup>2</sup>.

These tests were obtained entirely automatically, with no human guidance needed. The frontier AI handled the testing on its own.

### Proofs of Equivalence with SAW

The Software Analysis Workbench ([SAW](https://tools.galois.com/saw)) is a tool provided by Galois that proves functional equivalence between two formal representations of an algorithm. SAW is able to work with Cryptol natively and provides tools to import software implementations from low-level representations: for Rust, this is MIR; for other languages, this is LLVM. In the Foundation repo, the NSA uses SAW to prove that their AES Rust reference implementation is functionally equivalent to their AES Cryptol specification.

We use SAW with `gnat-llvm`, our LLVM backend to the GNAT compiler, to prove both that our SPARK implementations are functionally equivalent to the Cryptol specifications and separately that our SPARK specifications are functionally equivalent to the Cryptol specifications. This is a bit of overkill, but we wanted to demonstrate the capabilities of the various tools and provide the strongest guarantees we could of the correctness of the AI-generated specifications and implementations.

We prove the implementation using SAW’s `llvm_verify`, asserting that each implementation entry point (e.g., `Encrypt_Block`) is functionally equivalent to its Cryptol specification. We prove the specification by enabling the Ghost code for execution with `pragma Assertion_Policy (Ghost => Check)`, which allows us to use `llvm_verify` similarly for the specifications. To ensure that the SAW proofs are not vacuous, we deliberately break the implementation and confirm that SAW reports counterexamples.

The AES specification and implementation proofs in SAW cover every input at each key size. The SHA-256 specification and implementation proofs in SAW cover 12 selected message sizes. The HMAC specification and implementation proofs in SAW cover 7 selected (key-length, text-length) pairs<sup>3</sup>.

These proofs were obtained entirely automatically, with no human guidance needed. The frontier AI handled these proofs on its own.

### A Visual Summary

Here’s how the different pieces fit together, and the evidence of correctness we’ve established.

![https://www.adacore.com/uploads/foundation-spark-relationships.svg](https://www.adacore.com/uploads/foundation-spark-relationships.svg)

## Performance

### Implementation Performance

Tested on an Apple M1 Pro using GNAT FSF 16.1 and rustc 1.95 using `-O3`, we obtain the following results; all times in nanoseconds.

opSPARK, checks offSPARK, checks onRustratio, checks offratio, checks onAES-128  
Expand_Key131.9130.0403.70.330.32AES-128 encrypt327.6368.6403.40.810.91AES-128 decrypt775.0778.1722.21.071.08AES-256  
Expand_Key176.3165.8543.80.320.30AES-256 encrypt468.3520.2569.00.820.91AES-256 decrypt1111.81112.21034.31.071.08

In general, the SPARK implementation is faster than the Rust implementation. Notably, this speedup is not from disabling SPARK’s runtime checks<sup>4</sup>.

Rust wins out very narrowly on decryption, however. The reason is a failure on the part of the compiler to inline the call to `Inv_Mix_Byte`, which forces that work to be repeated in SPARK while it is shared in Rust. We can fix this by asking the compiler to inline this function with `pragma Inline_Always (Inv_Mix_Byte)`. With this change, AES-128 decrypt falls to 420 ns and AES-256 decrypt falls to 600 ns; both outperform the Rust by a significant margin<sup>5</sup>.

This result is not surprising; we know that SPARK is fast (as is Ada). But we highlight here because there is an unfortunate, prevailing assumption that Ada (hence SPARK) is *not* fast. Showing the SPARK code outperforming the Rust code (significantly, for `Expand_Key`) reinforces what we already knew: SPARK is fast, in addition to being safe and secure.

### Proof Performance

Proof performance breaks into two relevant parts: obtaining the proofs and checking the proofs. We present them in the opposite order here, as the check step is most likely to be repeated.

#### Checking the Proofs

Time spent checking the proofs, measured on an x86_64 Linux machine, Intel Xeon 6975P-C, 8 vCPUs (4 cores × 2 threads), 15 GB RAM:

checkresultwall-clockCPUpeak RSScoresgnatprove, the CI gate (`check-proof.sh`)4085/4085 checks14:0237 min485 MB8gnatprove, SBox_Entries (`prove-slow.sh`)2565/2565 checks15:2025 min376 MB8FFI (`check-ffi.sh`)141 properties pass: 36 exhaustive, 105 random8:479 min389 MB1SAW, default (`check-saw.sh`)1895 proved (87 implementation, 1808 spec layer); 20/20 negative controls fail47:1648 min2.3 GB1SAW, long (`SAW_LONG=1`)2142 proved (87, 2055); 20/20 negatives fail1:46:49108 min6.4 GB1

#### Obtaining the Proofs

Time spent obtaining the proofs, specs, implementations, and the FFI tests for all three algorithms is shown in the table below; all numbers in hours<sup>6</sup>:

layertotalwaiting on toolsagentits checker ranWriting the SPARK specs based on the Cryptol1.320.420.90SPARK 0.10Proving properties from the Cryptol on the SPARK spec (e.g., `SBoxCorrect`)3.082.800.28SPARK 1.09Writing the SPARK implementation and obtaining the SPARK Platinum proofs3.872.531.34SPARK 1.16Writing the FFI tests4.633.710.92FFI 1.70Writing the SAW implementation proofs4.183.250.94SAW -<sup>7</sup>Writing the SAW specification proofs14.2212.082.14SAW 11.25Revising and re-proving the SPARK specs after review<sup>8</sup>12.2610.60<sup>9</sup>1.66SPARK 6.78Revising and re-proving the SAW after the SPARK spec changes8.197.540.65SAW 6.80Totals51.7542.928.83

The takeaway from these numbers is that, overall, frontier AI is good at writing specifications and implementations that prove, whether working with SPARK or with SAW. The proof burden, specifically, is not that high – especially considering that this is Platinum proof (full functional correctness).

## Reproducing These Results

The repository contains detailed instructions for reproducing our results; you’ll find them [here](https://github.com/manthonyaiello/Foundation/blob/spark-v1.0/spark/doc/reproducing.md).

Briefly, the SPARK proofs can be checked using the GNAT FSF 16 tools that are provided via Alire. To check the proof, simply run: `scripts/check-proof.sh`; to run the Cryptol FFI tests, install Cryptol 3.6 and run `scripts/check-ffi.sh`. These proofs and tests are run in CI on the GitHub repository.

The SAW proofs require GNAT Pro 27 with the LLVM back-end. Once you’ve installed SAW and GNAT Pro, you can check the proof by running `scripts/check-saw.sh`. These proofs are *not* run on CI on the GitHub repository, as we do not have an installation of GNAT Pro 27 in that environment.

## Conclusion

First, these are well-studied algorithms with published proofs. We can absolutely assume that the frontier models have seen this work as part of their training. However, the specification in SPARK, and hence the SPARK proofs, were new work, not recall. The AI completed the proof of over 6,500 checks, entirely on its own. The SAW proofs were new work, too; to our knowledge, prior work has not integrated Cryptol and SPARK in SAW using GNAT Pro LLVM. We expect these results to transfer to new code.

For greenfield development, when we have a formal specification, we expect that frontier AI is able to transform that specification into SPARK (as needed), implement the software, and prove full functional correctness (SPARK Platinum), automatically. This is the highest level of confidence in functional correctness possible.

For brownfield development, especially when we want to translate existing, proven-in-use software to SPARK for proof and ease of maintenance, we have evidence that we can use SAW to show that the SPARK translation is functionally equivalent to the original, regardless of its implementation language and provided SAW can import it (through LLVM or another path). Again, this is the highest level of confidence that we have correctly translated the software possible, far better than we might obtain via testing.

Second, this work demonstrates that SPARK is a high-performance language, in addition to offering the strongest assurance possible. Help us get the message out or help us build more examples in SPARK! We want to see more SPARK in more places; SPARK is ready today for the most demanding safety or security applications, from embedded to enterprise.

## Disclaimers

First, **don’t use this code** when security actually matters. The formal proofs tell us that each algorithm is implemented correctly: AES correctly encrypts and decrypts; SHA-256 correctly hashes; HMAC correctly performs message authentication. But there’s (much) more to security than functional correctness, especially for foundational algorithms like cryptography: in particular, we have to be concerned about side-channel attacks, which may leak key or plain-text bits to an attacker. Side-channel attacks represent non-functional properties, which this work does not address *at all<sup>10</sup>*. We encourage you to experiment with the code and to look at the results as evidence that AI is able to provide formal evidence of software correctness; we do not want you to trust the code when security or privacy matters.

If you’re looking for proven cryptography (which we encourage!) look at Amazon’s work [here](https://aws.amazon.com/security/opensource/cryptography/). Rod Chapman, who’s [authored](https://www.adacore.com/blog/proving-constant-time-crypto-code-in-sparknacl?utm_source=blog&utm_medium=adacore+blog&utm_campaign=foundational+spark+blog&utm_id=foundational+spark+blog+rob+performance+) [several](https://www.adacore.com/blog/proving-constant-time-crypto-code-in-sparknacl?utm_source=blog&utm_medium=adacore+blog&utm_campaign=foundational+spark+blog&utm_id=foundational+spark+blog+rob+proving) [blogs](https://www.adacore.com/blog/doubling-the-performance-of-sparknacl-again?utm_source=blog&utm_medium=adacore+blog&utm_campaign=foundational+spark+blog&utm_id=foundational+spark+blog+rob+doubling) on the AdaCore Blog, is heavily involved in this work.

<sup>1</sup>*<sub>Typically, when a formal specification has been refined into a SPARK specification like we did here, we argue against re-proving putative properties of the original specification on the SPARK specification. When a proof of equivalence exists between the two specs, such re-proof is unnecessary effort: we know that any true property of the original specification is entailed by the SPARK specification as a result of the equivalence. Here, however, we retain these proofs in part because we cannot repeat the proof of equivalence in CI; for the time being, only GNAT Pro LLVM customers are in a position to repeat the equivalence proofs.</sub>*

<sup>2</sup>*<sub>That we achieve 100% MC/DC and yet know that our testing is insufficient should encourage us to trust structural coverage metrics only up to a point.</sub>*

<sup>3</sup>*<sub>SAW does not allow us to prove equivalence for all message lengths or for all (key, text) pairs; it does prove equivalence for all possible instances, having selected a message, key or text length.</sub>*

<sup>4</sup>*<sub>The runtime checks make key expansion run slightly faster: the code generator / optimizer takes advantage of the checks and generates slightly more efficient code, albeit with over 50% more instructions.</sub>*

<sup>5</sup>*<sub>We presented the initial results showing SPARK losing to Rust on decrypt because that’s what happened out of the box; this seems the most fair comparison!</sub>*

<sup>6</sup>*<sub>These results come from a mix of an aarch64-linux container on an Apple M5 Pro (M5 is not a typo) and the x86_64-linux machine used above, so take the ratios between columns with a grain of salt.</sub>*

<sup>7</sup>*<sub>We’re missing data for this entry; it’s somewhere between 0.67 and the 3.25 hours reported in the adjacent column.</sub>*

<sup>8</sup>*<sub>While the changes to the specs were indeed conceptually minor, they were fairly disruptive to the way in which the specs were laid out (the introduction of a generic for AES key sizes, notably), hence the amount of time spent here.</sub>*

<sup>9</sup>*<sub>This value is so high in part because there were multiple revisions that triggered re-proof of the </sub>*`SBoxCorrect`*<sub> property, which is very expensive (about 20 minutes per run, accounting for about 3.5 h hours of proof time). A smarter approach would have been to hold off on any such long proofs until the rest of the work was done, but the agent didn’t do this.</sub>*

<sup>10</sup>*<sub>There is initial work on constant-time implementations on a branch, but it has not been reviewed and is not backed by proof.</sub>*

## FAQs

SPARK is a programming language and formal verification toolset for building software that can be mathematically proven correct. It is based on Ada and adds the ability to write precise specifications, such as preconditions and postconditions, directly into the code. The GNATprove tool then uses automated provers to check that the code meets those specifications. Rather than relying only on testing, which can show the presence of bugs but not their absence, SPARK lets developers prove properties for all possible inputs. Assurance comes in levels: Silver proves the absence of runtime errors such as overflows or out-of-bounds accesses, Gold proves key integrity properties, and Platinum, the level reached in this project, proves full functional correctness against a complete specification.

SPARK is used for safety-critical and security-critical software, where failures are costly or dangerous and strong evidence of correctness is required. Typical areas include aerospace and defense, automotive, rail, industrial control, and cybersecurity, including components such as cryptographic libraries, communication protocols, and operating system code. Because SPARK can provide formal evidence that complements testing, it can support certification and assurance activities under standards such as DO-178C and ISO 26262. SPARK can be adopted incrementally, so teams can apply proof to their most critical components first, and it suits everything from small embedded systems to larger enterprise applications.

We don’t rely on trusting the AI. Correctness is backed by independent evidence from four sources. The SPARK specifications are proven functionally equivalent to the NSA’s Cryptol specifications for selected message, key, and text lengths. The SPARK implementations are proven to satisfy their specifications at SPARK Platinum level (full functional correctness). The implementations are separately proven equivalent to the Cryptol using Galois’s SAW. And the code is tested against the Cryptol specifications, reaching 100% MC/DC coverage. A few limits are worth stating: the SAW proofs cover every input for AES, but only selected message sizes for SHA-256 and selected key and text lengths for HMAC. Testing on its own also missed some injected faults, which is why proof, not testing, is the main basis for confidence.
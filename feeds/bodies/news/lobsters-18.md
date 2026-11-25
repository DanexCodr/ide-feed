The [Cerise](https://cerise-project.org/) project<sup>[1](https://cheriot.org/verification/2026/11/24/griotte-verification-effort.html#fn:cerise)</sup> was started almost 10 years ago at Aarhus University.
Its goal is to develop formal methods to verify properties of capability machines, in particular involving non-monotonicity,
and to prove end-to-end results in the presence of unknown code.
Cerise has been extended to model different aspects of capability machines,
and has involved work by and collaborations with several other universities,
including Dominique Devriese’s research group at KU Leuven,
and the universities of Cambridge and Edinburgh.

Cerise started as pen-and-paper proofs about idealised machines and focused
initially on reasoning about control-flow integrity of encapsulation for
stack-based calling conventions, but over time our research group has scaled up
the approach along three dimensions. First, we made our proofs foundational:
Cerise now builds on the Iris separation logic framework inside the Rocq theorem
prover, which has been critical to ensure correctness despite the growing
intricacy of our proofs. Second, we have investigated how to reason about a
wider range of properties, e.g., involving MMIO and attestation. Third, we made
Cerise work with an instruction set closer to the CHERIoT Sail model, and
verified programs using those instructions.

When I started my PhD, CHERIoT had just been announced.
I seized the opportunity to apply the verification techniques of Cerise
to the CHERIoT switcher, for example to check that it isolates compartments and enforces no-capture.
To that end, we started a sub-project of Cerise, which we call Griotte<sup>[2](https://cheriot.org/verification/2026/11/24/griotte-verification-effort.html#fn:griotte)</sup>.

As part of our verification effort in this Griotte project, we uncovered two
bugs in the CHERIoT switcher: (1) the ability for a malicious (or buggy)
scheduler to resuscitate an exited thread in a deprecated state, thereby getting
access to a capability that it should not be able to have access to anymore, and
(2) the ability for a malicious caller to leverage the stack high watermark
register to trigger a fault in the switcher, thereby getting access to the
callee’s stack frame and thus private data.

## Reasoning about unknown code

The CHERI/CHERIoT threat model includes interactions with unknown compartments
containing arbitrary code, which can be buggy or malicious, and which can share 
objects in memory. Reasoning about arbitrary code is hard, because it
requires characterising all the possible behaviours of that code. The challenge
is that when trying to characterise what an unknown compartment can affect, we
have to account not only for what it is passed directly (if an unknown
compartment is physically passed a write capability to a region of memory, then
it is behaviourally passed the ability to overwrite that region of memory), but
also what it is passed indirectly—and this involves not only recursive
access (if an unknown compartment is physically passed a read capability to a
region of memory, then it is behaviourally passed the ability to acquire
whatever ability is given by the capabilities in that region of memory), but
also access through non-monotonic domain transitions (if an unknown compartment
is physically passed a sealed entry point capability to a “counter”
compartment’s `incr` function, then it is behaviourally passed the ability to
affect the counter—but only by incrementing it). A unique feature of 
Cerise is the ability to reason also about the latter part of the challenge.

What makes it difficult to design such a characterisation is that it should at
the same time be precise enough, and simple enough to verify the programs that
we care about. At a very high level, Griotte defines a language to succinctly
describe what is affected—and to state that something is *not* affected. The
kind of properties that we want to describe are not only memory safety
properties (if I share a buffer to the caller, then I have the guarantee that it
cannot access the global data that I never shared), but also no-capture
properties (if I share a buffer to the caller with its global permission
stripped, then I have the guarantee that it cannot preserve a copy across
calls), and many others (including secrecy, etc.).

## Separation logic and logical relations

Technically, we developed a reasoning system in two parts.
First, we defined (and proved sound) a separation logic that allows us to verify known code line by line,
showing that it satisfies expected pre- and post-conditions,
and that it preserves the expected invariants.
We used this both on the code of the switcher,
and on the code of specific compartments of interest, for example a key-value store<sup>[3](https://cheriot.org/verification/2026/11/24/griotte-verification-effort.html#fn:kvs)</sup>.
We designed this separation logic so it is reusable,
and we expect that other such compartments of interest could be verified with it.

Second, we defined a logical relation in separation logic,
which is effectively an over-approximation of the effect of unknown code
that can be used by the separation logic
to reason about a jump to unknown code (through the switcher) in one single step.
As such, it works like a universal contract<sup>[4](https://cheriot.org/verification/2026/11/24/griotte-verification-effort.html#fn:contract)</sup> for CHERIoT.
Crucially, the frame rule of separation logic
tells us that if we can establish that the resources (both in an informal sense, and in the technical sense of separation logic) of the caller
are disjoint from those of the logical relation,
then they will be preserved by the call.

For example, if calling unknown code with a capability to a shared buffer,
while keeping some private data,
the logical relation requires that the unknown code is only passed capabilities that are *safe to share*
in a technical sense.

We then define a universal contract, stating that if an adversary has only access to
*safe to share* capabilities, it can then execute safely and only produce other *safe to share* capabilities.

## Verification in the presence of compartments and a trusted switcher

We started by developing a simplified model of CHERIoT
and a mini version of the CHERIoT-RTOS.
In particular, we modelled the compartmentalisation mechanisms and 
the cross-compartment call path of the switcher. 
Our simplified model mirrors the main features of the CHERIoT hardware (including the new deep
locality and deep immutability permissions).
While our mini switcher doesn’t follow CHERIoT’s switcher instruction-by-instruction, 
it implements the same steps.

In this model, we proved on a range of small examples that 
the CHERIoT hardware-software co-design
implements the expected memory-safety properties,
and that the switcher’s *overall design* enforces both compartmentalisation and stack safety.

Our “end-to-end” results about concrete examples
assume that the machine starts in a state that corresponds
to the firmware image having been properly loaded.
We have not verified the loader itself, and so it is part of our TCB.
Technically, we consider executions only starting from a “loader-final” state.
The loader is deterministic and so it is relatively easy to dump the contents of memory from a
device (or simulator) after the loader has run and verify that a specific execution of the loader meets the
properties required by our “loader-final” state.

We expect that it should be possible to prove the loader correct,
but this is future work for now.

## The cherry on top: Concurrency, exception handling and optimisations

Our initial model was a simplification of CHERIoT:
it didn’t support exceptions or concurrency/context switching,
and some optimisations of the switcher (such as the stack high watermark)
were left out.

The CHERIoT team has been dedicated to making CHERIoT trustworthy,
and has been very supportive of our verification effort.
To that end, they included, in the switcher’s source, detailed comments about the expected 
invariants and behaviour of the switcher, in the form of pre- and post-conditions
for the execution blocks.
They pointed out that the complicated control flow in the switcher’s exception path 
was a likely source of errors.

Our efforts showed that the cross-compartments call (and return) path that we verified 
was straightforward
(although stating no-capture and stack safety at the separation logic level is not trivial!),
but a good starting point.
However, as pointed out by the CHERIoT team,
the features that we initially left out are more prone to mistakes:
the switcher’s exception handler (responsible for context switching and error handling)
has a more fiddly and convoluted execution path,
and the stack high watermark creates a new point of trust.

By pursuing our verification effort to include the features missing from our initial model,
some of the examples that we proved in the simplified setup
did not work anymore, which actually uncovered bugs in the switcher.

### “High is too low”: Stack high watermark and exception handler

The first bug that we uncovered comes from an interaction between the exception handler
and the stack high watermark.

In the presence of an exception handler,
any instruction must either ensure that it cannot fault,
or that the exception handler can safely execute (either by force-unwinding to the caller, or by
giving control to the error handler of the faulting compartment).
In our proof, this manifests as each instruction coming with a proof obligation
that even when the instruction can fault, all invariants of the system are maintained.

On the other hand, the stack high watermark (SHWM) is an optimisation allowing the switcher
to clear only the stack frame used during the call.
Specifically, the SHWM tracks, in hardware, the highest address of the stack that has been written to,
and the switcher only clears up to this address, instead of the whole shared stack region.
The code of the switcher relied on an invariant for the SHWM:
it should always be in between the bounds of the stack capability at the point of a cross-compartment call.
To that end, the switcher always re-sets it in the bounds of the stack capability at
cross-compartment calls and returns.
This invariant was very dynamic by nature,
because the bounds of the stack change in between cross-compartment calls.

However, it turns out that this invariant did not hold:
a malicious caller could craft a stack pointer with restricted bounds, 
together with a stack object outside of this restricted stack to be used 
later by a callee.
This scenario can lead to a fault in the switcher return path of the callee,
before it has cleared the callee stack frame,
which then allows a malicious caller to recover the entire callee’s private state.

We identified this problem when we tried to adapt our proof
from a simplified switcher (without the SHWM),
to a more faithful switcher (with the SHWM).
The proof got stuck when we had to show that an adversary
could not move the SHWM outside of the bounds of the stack.
After a bit of investigation, we realised that it was not because we had failed to correctly capture the informal invariant,
but because that invariant was not preserved.
More specifically, it seemed to be possible for an attacker to move SHWM below the base of the stack capability.

We first tried to relax this (expected) invariant and allow SHWM to move below the base of the stack capability,
but this condition was guarding a fault in the cross-compartment return-path.
With the relaxed invariant, we had to prove that the fault was safe,
which turned out to be impossible to prove, due to the callee’s stack frame being preserved.
That’s how we realised that it was possible to mount an attack,
with a subtle construction to move the SHWM below the base of the stack capability
and exploiting the fault in the switcher’s return path to recover the uncleared callee’s stack frame.

The fix (merged in [PR #799](https://github.com/CHERIoT-Platform/cheriot-rtos/pull/799))
ended up being pretty simple:
by forbidding malicious callers from changing the base of the stack,
it ensures that malicious callers cannot craft a stack object outside of the stack that would
move the SHWM outside of the stack bounds.
This does not prevent the caller from calling the callee with less than the maximum possible
amount of stack space,
but does require that the shared stack region is truncated in the same direction as normal stack allocation.

We could validate the fix in our setup, by completing the proof, before the merge.

### “You’re not really over yet”: Concurrency with a malicious scheduler

While verifying the context switching path in our simplified switcher,
and in particular the path that an exited thread takes,
we needed to define “what it means for a thread to exit”,
and what is the authority that an exited thread still holds.
We first looked at the scheduler’s code, in which exited threads are never meant to be scheduled anymore.
Intuitively, we would think that an exited thread has no continuation.

However, the scheduler is not trusted for confidentiality or integrity 
(which are the properties we are verifying!), which means that in our model,
we consider the scheduler as any other adversary compartment
(and therefore, from our perspective, it contains arbitrary code).
In particular, a malicious (or buggy) scheduler could schedule an exited thread,
in which case the switcher re-instated that thread’s last context (as stored in the context switching save area),
independently from whether that thread had exited.
Because the thread exit path of the switcher never cleared the save area,
an exited thread’s last context turned out to be whatever was left after the last preemption (or fault), 
which means that it could contain local capabilities that should not have been captured—clearly violating no-capture.

We caught this bug because our formal verification method—focused on integrity and confidentiality—captures the threat model of CHERIoT,
where the scheduler is no different from other adversaries with respect to those properties.
The way the problem manifested in our proof is that we had to define what the authority of the continuation of an exited thread is,
to account for what would happen if the thread were scheduled in a stale state.
However, this looked fishy, and so we started questioning whether we should even have to consider such a situation.

There are two disjoint sub-problems:
(1) having access to an old register file (potentially breaking no-capture guarantees),
and (2) an exited thread being re-scheduled.
Sub-problem (1) is dangerous for integrity and confidentiality.
Sub-problem (2) is a design question—what should happen if the scheduler reschedules an exited thread.

The fix (merged in [PR #769](https://github.com/CHERIoT-Platform/cheriot-rtos/pull/769))
then fixed those problems:
(1) the register file is cleared in the exit thread path (preventing an exited thread from using stale values)
and (2) an exited thread becomes an idle thread looping in a `wfi` (wait-for-interrupt) loop.
This fix was one of several possible fixes considered but was chosen because the scheduler always has the ability to run the idle thread (which loops in a `wfi` instruction).
This meant that the ability to schedule an exited thread could be trivially shown to not increase the power of the scheduler.

## What now?

With the fixed bugs, we have verified our Griotte switcher on top of our Griotte ISA,
assuming that the loader initialises the machine properly.

That gave us confidence to scale our verification to be based on
the whole authoritative [cheriot-sail](https://github.com/CHERIoT-Platform/cheriot-sail) ISA, 
using the `sail-to-rocq` extraction, and our proofs of that are now complete.
It means that we are quite confident that 
the [current upstream](https://github.com/CHERIoT-Platform/cheriot-rtos/blob/e2dad05078bd25ed6f1ab993e14f332aa8c20557/sdk/core/switcher/entry.S) 
switcher, together with the hardware, implement thread and compartments isolation, as well as no-capture.

In the future we would also like to verify the loader, and we also hope that our
logical machinery can be used to verify correctness and security of applications
running atop CHERIoT.

## Other formal verification work you might be interested in

The focus of Cerise and Griotte has been *advanced* properties of capability machines,
in particular involving non-monotonic domain transitions.
As such, it is complementary to other formal verification work:

- Nienhuis et al. [2] and Bauereiß et al. [3] prove capability monotonicity of real ISAs for CHERI-MIPS and Morello, respectively; and Hammond et al. [4] builds on top of those proofs and Cerise to recover some non-monotonic domain transitions
- Ploix et al. [5] proves that the CHERIoT-Ibex implements the CHERIoT-Sail model
- Duque Antón et al. [6] and Rosemeyer [7] prove security properties at the level of the RTL
- Work on an abstract specification of the CHERIoT ISA and switcher at Google.

## References

1. Sander Huyghebaert, Steven Keuchel, Coen De Roover and Dominique Devriese. [Formalizing, Verifying and Applying ISA Security Guarantees as Universal Contracts](http://doi.org/10.1145/3576915.3616602). *Proceedings of the 2023 ACM SIGSAC Conference on Computer and Communications Security*, Association for Computing Machinery (2023), 2083–2097. [doi] BibTeX @inproceedings{huyghebaert2023, author = {Huyghebaert, Sander and Keuchel, Steven and De Roover, Coen and Devriese, Dominique}, title = {Formalizing, Verifying and Applying ISA Security Guarantees as Universal Contracts}, booktitle = {Proceedings of the 2023 ACM SIGSAC Conference on Computer and Communications Security}, series = {CCS '23}, publisher = {Association for Computing Machinery}, year = {2023}, month = nov, pages = {2083--2097}, doi = {10.1145/3576915.3616602} }
2. Kyndylan Nienhuis, Alexandre Joannou, Thomas Bauereiss, Anthony Fox, Michael Roe, Brian Campbell, Matthew Naylor, Robert M. Norton, Simon W. Moore, Peter G. Neumann, Ian Stark, Robert N. M. Watson and Peter Sewell. [Rigorous engineering for hardware security: Formal modelling and proof in the CHERI design and implementation process](http://doi.org/10.1109/SP40000.2020.00055). *2020 IEEE Symposium on Security and Privacy (SP)*, IEEE (2020), 1003–1020. [doi] BibTeX @inproceedings{nienhuis2020, author = {Nienhuis, Kyndylan and Joannou, Alexandre and Bauereiss, Thomas and Fox, Anthony and Roe, Michael and Campbell, Brian and Naylor, Matthew and Norton, Robert M. and Moore, Simon W. and Neumann, Peter G. and Stark, Ian and Watson, Robert N. M. and Sewell, Peter}, title = {Rigorous engineering for hardware security: Formal modelling and proof in the CHERI design and implementation process}, booktitle = {2020 IEEE Symposium on Security and Privacy (SP)}, publisher = {IEEE}, year = {2020}, month = may, pages = {1003--1020}, doi = {10.1109/SP40000.2020.00055} }
3. Thomas Bauereiss, Brian Campbell, Thomas Sewell, Alasdair Armstrong, Lawrence Esswood, Ian Stark, Graeme Barnes, Robert N. M. Watson and Peter Sewell. [Verified Security for the Morello Capability-enhanced Prototype Arm Architecture](http://doi.org/10.1007/978-3-030-99336-8_7). *Programming Languages and Systems (ESOP 2022)*, Springer International Publishing (2022), 174–203. [doi] BibTeX @inproceedings{bauereiss2022, author = {Bauereiss, Thomas and Campbell, Brian and Sewell, Thomas and Armstrong, Alasdair and Esswood, Lawrence and Stark, Ian and Barnes, Graeme and Watson, Robert N. M. and Sewell, Peter}, title = {Verified Security for the Morello Capability-enhanced Prototype Arm Architecture}, booktitle = {Programming Languages and Systems (ESOP 2022)}, series = {Lecture Notes in Computer Science}, publisher = {Springer International Publishing}, year = {2022}, pages = {174--203}, isbn = {9783030993368}, doi = {10.1007/978-3-030-99336-8_7} }
4. Angus Hammond, Ricardo Almeida, Thomas Bauereiss, Brian Campbell, Ian Stark and Peter Sewell. [Morello-Cerise: A Proof of Strong Encapsulation for the Arm Morello Capability Hardware Architecture](https://dl.acm.org/doi/pdf/10.1145/3729329). *Proceedings of the ACM on Programming Languages 9*, PLDI (2025), 1961–1983. [pdf] [doi] BibTeX @article{hammond2025, author = {Hammond, Angus and Almeida, Ricardo and Bauereiss, Thomas and Campbell, Brian and Stark, Ian and Sewell, Peter}, title = {Morello-Cerise: A Proof of Strong Encapsulation for the Arm Morello Capability Hardware Architecture}, journal = {Proceedings of the ACM on Programming Languages}, volume = {9}, number = {PLDI}, publisher = {Association for Computing Machinery}, year = {2025}, month = jun, pages = {1961--1983}, issn = {2475-1421}, doi = {10.1145/3729329}, pdf = {https://dl.acm.org/doi/pdf/10.1145/3729329} }
5. Louis-Emile Ploix, Alasdair Armstrong, Tom Melham, Ray Lin, Haolong Wang and Anastasia Courtney. [Comprehensive Formal Verification of Observational Correctness for the CHERIoT-Ibex Processor](https://arxiv.org/abs/2502.04738). 2025. [doi] BibTeX @misc{ploix2025, author = {Ploix, Louis-Emile and Armstrong, Alasdair and Melham, Tom and Lin, Ray and Wang, Haolong and Courtney, Anastasia}, title = {Comprehensive Formal Verification of Observational Correctness for the CHERIoT-Ibex Processor}, publisher = {arXiv}, year = {2025}, doi = {10.48550/arXiv.2502.04738}, url = {https://arxiv.org/abs/2502.04738} }
6. Anna Lena Duque Antón, Johannes Müller, Philipp Schmitz, Tobias Jauch, Alex Wezel, Lucas Deutschmann, Mohammad Rahmani Fadiheh, Dominik Stoffel and Wolfgang Kunz. [VeriCHERI: Exhaustive Formal Security Verification of CHERI at the RTL](https://doi.org/10.1145/3676536.3676841). *Accepted for publication at the 43rd International Conference on Computer-Aided Design (ICCAD ‘24)*, Association for Computing Machinery (2024). [doi] BibTeX @inproceedings{vericheri2024, author = {Duque Ant{\'o}n, Anna Lena and M{\"u}ller, Johannes and Schmitz, Philipp and Jauch, Tobias and Wezel, Alex and Deutschmann, Lucas and Fadiheh, Mohammad Rahmani and Stoffel, Dominik and Kunz, Wolfgang}, title = {VeriCHERI: Exhaustive Formal Security Verification of CHERI at the RTL}, doi = {https://doi.org/10.1145/3676536.3676841}, year = {2024}, month = oct, location = {New York, USA}, publisher = {Association for Computing Machinery}, booktitle = {Accepted for publication at the 43rd International Conference on Computer-Aided Design (ICCAD `24)} } Abstract Protecting data in memory from attackers continues to be a concern in computing systems. CHERI is a promising approach to achieve such protection, by providing and enforcing fine-grained memory protection directly in the hardware. Creating trust for the entire system stack, however, requires a gap-free verification of CHERI’s hardware-based protection mechanisms. Existing verification methods for CHERI target the abstract ISA model rather than the underlying hardware implementation. Fully ensuring the CHERI security guarantees for a concrete RTL implementation is a challenge in previous flows and demands high manual efforts. This paper presents VeriCHERI, a novel approach to security verification. It is conceptionally different from previous works in that it does not require any ISA specification. Instead of checking compliance with a golden ISA model, we check against well-established global security objectives of confidentiality and integrity. Fully covering these objectives, VeriCHERI uses as few as four unbounded properties to exhaustively prove or disprove any vulnerability. We demonstrate the effectiveness and scalability of VeriCHERI on a RISC-V based processor implementing a CHERI variant.
7. Tita Rosemeyer. [Formal Verification of Capability-Safety in the CHERIoT-Ibex Processor](https://www.cs.ox.ac.uk/tom.melham/grads/Rosemeyer-2025-FVC). 2025. [pdf] BibTeX @mastersthesis{titarosemeyer2025, author = {Rosemeyer, Tita}, title = {Formal Verification of Capability-Safety in the CHERIoT-Ibex Processor}, school = {University of Oxford}, year = {2025}, pdf = {https://www.cs.ox.ac.uk/tom.melham/grads/Rosemeyer-2025-FVC} }
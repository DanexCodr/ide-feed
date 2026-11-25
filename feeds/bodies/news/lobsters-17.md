Given the increasingly hostile supply chain environment the entire software community is working within, the Rust Foundation is sponsoring exploratory work on using decision models to automatically scan crates as they are published, and flag potentially malicious crates for human review.

We’ve had the scanner running on the crate firehose for a little more than a week at this point, and here’s what we’ve learned so far.

### What It Is

Decision models have become prominent in the last 2-3 months as an alternative to the LLM-based chat interfaces that have dominated AI tasks in the last few years. Rather than providing open-ended natural language output, decision models are naturally constrained to choosing from a restricted set of answers, or providing scores against a question. Critically, they are also much faster and cheaper than LLMs, which makes it feasible to feed every crate in without bankrupting the Rust Foundation.

Almost as soon as decision models became generally available, we started experimenting with feeding crates in: developing and refining prompts, figuring out how to break up crates to fit them in a restrictive context window while still getting reasonable results, extrapolating the crate publication growth curve to estimate the cost that would be involved in running this against the entire [crates.io](http://crates.io) firehose, and looking at the results to see if they are reliable enough to justify the human review required.

After performing that analysis against a corpus of approximately 1,000 crate files — some known to be malicious from previous takedowns, some known to be good, and some randomly chosen from crates published in October — we decided that the results were cheap and effective enough to be worth a longer (and more expensive) experiment: namely, running every crate published in November and December through the decision model.

### What It Isn’t

Before getting into the early results, let’s talk about what we’re not doing on this project.

No automated actions are taken as a result of these scans. Effectively, we’re treating findings the same way as any normal third-party report of a potentially malicious crate: a [crates.io](http://crates.io) team member and/or a member of the Rust Foundation’s security initiative will review the crate file, and if action is deemed necessary, the normal takedown process takes place. As ever, this process involves the [crates.io](http://crates.io) team (for the mechanics of the takedown), Rust security response working group (for any security-related consulting), and [RustSec](https://rustsec.org/) (for advisories to notify users of the takedown).

The scanning service also doesn’t retain the crate file content once the initial scan is complete. Only the crate name, version number, a list of the file names within the crate, and the score are kept. If we do future comparative work, it will only be on crates that remain available at that time.

### Early Results

As of the writing of this blog post, we have scanned every crate file published between the 11th and 21st of November<sup>[1](https://rustfoundation.org/media/needles-haystacks-and-numbers-between-0-and-1/#f16aec60-6220-49d1-ad7b-e7c027a07734)</sup>, inclusive. We intend to go back to November 1st, and continue until at least December 31st.

So far, we’ve scanned 135,548 crate files.

We’re asking the decision model to give a score in the range `0.0..1.0` that the crate is malicious — not whether it is buggy, or has unintended security concerns, but simply whether it appears to be actively malicious, with some extremely limited<sup>[2](https://rustfoundation.org/media/needles-haystacks-and-numbers-between-0-and-1/#f6930c70-468c-48ca-9acf-7985a102f515)</sup> context provided from previous malware campaigns that we’ve seen.

Calibrating the threshold for where a human should be involved is an ongoing process. Based on the initial analysis, we set the threshold — which is, of course, going to be highly model and prompt specific — at 0.35, suspecting that that threshold would likely return more false positives than we desired. (We were not wrong.)

Here are the thresholds we’ve tried so far:

ThresholdCratesTrue positivesFalse positives≥ 0.353324 (1%)240 (99%)≥ 0.5844 (5%)62 (95%)≥ 0.6314 (13%)21 (87%)≥ 0.7154 (27%)6 (73%)≥ 0.864 (67%)1 (33%)≥ 0.944 (100%)0 (0%)

Given this, it appears that a threshold at or above 0.7 for this particular combination of model and prompt is likely to provide the sort of behaviour we want: relatively low background noise for the humans who need to review the findings, but still finding the malware.

Of course, this only covers what we find. It’s essentially impossible for us to quantify false negatives in any automated way: there are simply too many crates to review them manually, malicious crates are too infrequent for a random sampling approach to work, and the cost involved in using frontier LLMs is prohibitive.

On a longer time horizon, we should be able to get a sense of false negatives based on the other reports crates.io receives. We are grateful to the broader security ecosystem of companies, non-profits, and individuals who perform their own checks and make those reports! Commonly used crates tend to receive reports quickly, but it’s not uncommon for several months to pass for crates that see no usage.

We’ll do an in-depth look back and evaluation of the false negative rate in January as we will hopefully have more data by then.

### Future Directions

On a micro level, there is significant scope for experimentation with prompt and model over the coming weeks and months.

We’ve already observed specific failure modes for this particular combination: because the model has no real reasoning capability, it tends to over-score crates that contain significant embedded data that isn’t source code, as it simply can’t analyse what that data is or does.<sup>[3](https://rustfoundation.org/media/needles-haystacks-and-numbers-between-0-and-1/#2596dac9-72ee-4826-87e9-c3f72ae14504)</sup>

While we don’t have the financial resources to run parallel prompt and model combinations on the entire crate corpus during the experiment period, we will likely send some subsets of crates to other combinations to see if we can improve the scoring behaviour further.

If the outcome of this experiment is that we see value in continuing to scan crates in this way, we will likely seek partnerships and/or sponsorship in early 2027 to fund the operation and further development of this work, including going back through the full historical corpus.

Finally, on a macro level, we believe that there will be opportunities to match this sort of data with other security signals derived without the use of AI. Crate provenance data, metadata derived from maintainer actions, and capability analysis of the crates themselves are all active areas of research, both within the Rust Foundation, across ecosystems under the auspices of organisations such as [OpenSSF](https://openssf.org/) and [Alpha-Omega](https://alpha-omega.dev/), and in for-profit companies.

Being able to take those signals and integrate them holistically opens up opportunities for more rapid responses to malware, especially in combination with ongoing work at the crates.io level such as [RFC 4016 (Registry withholding)](https://github.com/jlizen/rfcs/blob/registry-withholding/text/4016-registry-crate-unavailability.md), which is currently in its final comment period.

Ultimately, regardless of the success of this particular experiment, we believe that work like this is crucial to the security and success of Rust, and of software development as a whole, and we’re excited to continue this work.

1. Dates in the one true time zone, naturally. ↩︎
2. Context lengths are a challenge here. Some decision models, including the one we’re currently using, have significantly more restricted context windows than frontier LLMs, and we obviously lose tokens with each additional sentence that we add to the prompt. We also, simultaneously, want to stuff as much context into a single request from the crate, because the analysis is more effective with a larger subset of the crate available. It’s a balancing act. ↩︎
3. This has also resulted in us finding multiple crates that are shipping opaque bytecode or downloading and linking arbitrary binaries that, while they don’t result in malicious behaviour today, are questionable in terms of whether they are within the crates.io usage policy. We’ll be taking that to the crates.io team for further discussion. ↩︎
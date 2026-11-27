Let’s **assume** that LLMs **actually speed up programming** and that the
EU cannot catch up to AI coding tools from the US and China. If this
is true, what can we do in the EU to **close the gap** enough that
efficiency gains from LLMs stay lower than their compute cost?

 *In short: make secure programming easier for people
again.* 🇪🇺

Improve programming tooling, nurture template libraries, extend and
integrate documentation, support maintainers, foster standardized
interfaces, champion responsiveness, de-bloat stacks.

## Practical steps for sovereignty

Practical steps at moderate cost:<sup>[1](https://www.draketo.de/software/curb-ai-impact#fn.1)</sup>

- Enhance copyleft compiler error messages (in gcc?)
- Improve responsiveness, e.g. reduce keyboard to screen latency. – mlinksva
- Support Free Software maintainers and foster infrastructure maintenance in the EU. If you know a project by heart, you can fix it much more easily.
- Package and improve searchable documentation (via texinfo?)[2](https://www.draketo.de/software/curb-ai-impact#fn.2), [3](https://www.draketo.de/software/curb-ai-impact#fn.3) and spread discoverability of documentation akin to IntelliJ for Java and Emacs for elisp, but for most languages, frameworks, and libraries (via texinfo-lookup?).
- Provide templates for common tasks like infrastructure setup (with proxmox?), adding an API endpoint, writing a report, etc. as executable documentation.
- Simplify stacks and frameworks, spread common development practices, and strengthen security ergonomics (with BSI Grundschutz?).
- Work towards more standardized interfaces between software components. Maintain reliable interface generation from specifications for different languages. Build interface contracts as the common denominator between different services, extendable for specifics. – Elias Probst[4](https://www.draketo.de/software/curb-ai-impact#fn.4)
- Create more linters (reuse SonarQube Rules?).

## Why we need these steps

These steps make software development more resilient against changes
due to LLMs.

> „What if the [worries by The Morpheus hold true](https://www.youtube.com/watch?v=mtNbPExBe_Y&t=1122) and *the EU cannot
> become competitive in LLM development*, because USA and China
> monopolized LLM development skill and infrastructure advantages? Which
> steps can—cheaply—limit the impact of LLMs so our software
> development stays competitive?“

I asked this question [in Mastodon](https://rollenspiel.social/@ArneBab/116827324007470571). To contribute, please answer the
question there.

AI may still fail as a bursting bubble and take down large parts of
the US economy with it (and more), but if it does not, the EU should
be prepared to curb its impact—best by already having taken steps
like the ones shown here.

And if the AI bubble does not burst, these steps will still help
software development in the EU. Money put into them **never goes to
waste** (it also helps the ones who use LLMs for coding, just not as
much), so I think that the EU should support these steps with at least
1% of the overall funding AI companies receive.<sup>[5](https://www.draketo.de/software/curb-ai-impact#fn.5)</sup>

## How to do it?

- Increase funding of the nlnet foundation via EU Horizon 2020 and followups.
- Increase funding of the Sovereign Tech Agency.
- Adhere to and require Public Money Public Code.
- Fund the Free Software Foundation Europe.[6](https://www.draketo.de/software/curb-ai-impact#fn.6)

Also support [empirical programming language research](https://www.draketo.de/software/language-empiric.html). To improve our
understanding how programming works best for humans.

## Footnotes:

compared to the 1 trillion VC funding for US-based AI companies
and who knows how much for Chinese ones.

Improve search in documentation and add more examples; collect
and integrate working examples in primary documentation. Piecing
together info is where most people give up. – *thanks to
libewa*.

Package more documentation as texinfo. Write automatic
convertersions to texinfo for different documentation tools.
Improve man-page integration. Since I started using local info
lookup via texinfo for writing Guile Scheme, I wish that were
available for every tool.
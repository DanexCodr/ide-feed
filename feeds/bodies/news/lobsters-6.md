A few years back I wrote [an article here on L-systems with granular synthesis](https://nathanho.me/posts/sound-synthesis-with-l-systems/). I was rather unsatisfied with it at the time, and today I wince even looking at it. The current article is an attempt to correct this injustice with a far more ambitious project which generates audio with L-systems and granular synthesis. In this article, I will give a detailed walkthrough of the entire construction of the system, called *EvoGrain*, and discuss what I went through to build it. You can hear a sample of its output above, and [more examples further down the article](https://nathanho.me/posts/evograin/#examples).

# Background

I have a few sources of inspiration to talk about here.

## Iamus

Iamus,<sup>[1](https://nathanho.me/posts/evograin/#VADM2021)</sup> created circa 2010 by a team of researchers at the University of Málaga, was one of the more compelling projects from an older era of algorithmic composition (before algorithmic art suddenly entered the public consciousness for all the wrong reasons). Its creators claim that scores are generated with no human intervention, and that Iamus is “the first computer that has developed its own original style.” The style in question is under the umbrella of post-tonal modern classical music.

The marketing copy for Iamus buries what I find to be the most compelling part of the project, which is that Iamus is not trained on existing human compositions, and it is entirely rule-based. With that in mind, take a listen to [*Hello World*](https://www.youtube.com/watch?v=bD7l4Kg1Rt8) (2011), its first piece to be premiered. Any judgment of this recording has to take into account the obvious fact that it’s performed by human musicians, and they’re adding an unavoidable interpretative touch to it. Compositionally, it’s maybe a bit aimless, but it’s still pretty impressive work for something made without a corpus. The Iamus website apparently once hosted a large number of generated scores for free download, but I’m not sure where to find them now.

Naturally, I was curious how it worked. Neither the source code nor a detailed technical description of Iamus were ever made available; the project was tied to a commercial product by a company by Melomics Spain SL, which does not seem to exist anymore.<sup>[2](https://nathanho.me/posts/evograin/#1)</sup> The most detailed description of the project’s approach is in a chapter by Vico et al. of the book *Handbook of Artificial Intelligence for Music*;<sup>[1](https://nathanho.me/posts/evograin/#VADM2021)</sup> there are also a few shorter papers from the same team worth looking at.<sup>[3](https://nathanho.me/posts/evograin/#AMV2016)</sup> <sup>[4](https://nathanho.me/posts/evograin/#CV2009)</sup> The gist of these papers, assuming they give a reasonably accurate picture of the project, is that Iamus uses Lindenmayer systems (L-systems) and evolutionary algorithms. An L-system generates a finite string of symbols, which then encode a score of music with a sequence of commands like “increase pitch by one semitone,” “output a note,” “change instruments,” etc. The L-system is deterministic and encodes exactly one score.

The evolutionary algorithm treats the rules of the L-system as the genotype (genetic material) and the generated scores as phenotypes (physical traits of organisms), with the scores evaluated against a fitness function, with typical selection, crossover, and mutation operators. The evolutionary system also apparently included human-guided evolution.<sup>[5](https://nathanho.me/posts/evograin/#DJ2011)</sup>

The most useful takeaway I had from the papers on Iamus is that of *indirect encoding*. The relationship between the genotype and the phenotype is very complex here, determined by the meanings of the symbols in the L-system and how they produce a score. These decisions are really critical to get musically interesting results, perhaps even more important than the fitness function and the evolutionary computation parts.

## Other Musical L-Systems

There are many resources on musical L-systems for algorithmic composition. A good one for a lay audience is Tom Johnson’s *Self-Similar Melodies*,<sup>[6](https://nathanho.me/posts/evograin/#Johnson1994)</sup> which uses very simple L-systems which are meant to be highly transparent to a listener, i.e. so-called “process music.” A paper by Mason and Saffle<sup>[7](https://nathanho.me/posts/evograin/#MS1994)</sup> uses a similar method but also shows how the generated melodies can mimic statistical properties of other composers’ melodies. A very different approach by Jones<sup>[8](https://nathanho.me/posts/evograin/#Jones1989)</sup> uses the L-systems to partition time and pitch space. A dissertation by DuBois<sup>[9](https://nathanho.me/posts/evograin/#DuBois2003)</sup> points to some other early examples and describes his own system, which involves real-time interaction with performers.

The combination of L-systems and sound synthesis is relatively underexplored, and the best resource on this I’ve found is Stelios Manousakis’ thesis on *Musical L-Systems*.<sup>[10](https://nathanho.me/posts/evograin/#Manousakis2006)</sup> A major part of his research is using L-systems to directly generate waveforms, which is a bit different from what I’m doing here, but he also uses an L-system–granular synthesis combination L-systems with granular synthesis that seems quite similar to what I’m doing in this project. One difference, if I am reading it correctly, is that his system is designed for real-time, while the one I’m about to describe is offline and tries to take advantage of the non-real-time medium.

# EvoGrain

In this section, I’ll walk you through my own L-system granular synth, working title EvoGrain. EvoGrain is an offline program that synthesizes an audio buffer between a few seconds to 30 seconds long. The result is not meant to be a complete work of music but rather raw material for sampling and transformation. Still, it’s a plus if the results are interesting to listen to in their own right.

I view EvoGrain as living in a middle ground between a synthesizer and an algorithmic composition system. (For prior work in algorithmic sound design systems, see e.g. <sup>[11](https://nathanho.me/posts/evograin/#Miranda1995)</sup>.) It is also intended to be effectively autonomous. Very few parameters are exposed to the user, and most of the behavior is random. Re-running EvoGrain repeatedly should generate a wide variety of results.

EvoGrain is designed as an entirely rule-based system. There is no external training data, and there is no specific attempt to mimic existing sounds or musical styles.

The architecture of EvoGrain is as follows:

- The L-system randomizer produces the rules of an L-system and an initial turtle state. The probability distributions and behavior of the random L-system generator dramatically affect the output.
- The L-system is run, creating a turtle command sequence.
- The turtle interprets the command sequence and produces a set of grains. Each grain is key-value data comprising start time, duration, pitch, and synthesis parameters.
- The grain set is “adjusted” using some ad-hoc global methods to improve its musicality.
- The grain set is synthesized to an audio file, and plotted for visualization.
- The grain set information is analyzed with some statistics to produce a fitness value.
- The entire process is run many times for different L-systems and a basic optimization procedure picks the best ones.

Here is a dataflow diagram:

![Dataflow diagram for EvoGrain.](https://nathanho.me/posts/evograin/schematic.png)

In the following sections, I will explain each individual step. It’s easiest to start from the bottom and work to the top.

## Synthesis: from grain sets to audio

EvoGrain contains a basic granular synthesis engine. I kept the DSP and the synthesis simple and conventional, because I want the placement and parameters of the grains to be the focus of the project.

The synthesizer’s job is to produce a stereo audio file from a *grain set*, a collection of grains. Typically there are about 20,000 grains in a set. Each grain is synthesized from the following key-value data:

- Start time of the grain.
- Duration.
- Amplitude.
- Stereo panning.
- Distance: reverb send.
- Amplitude envelope: rectangular, decaying, reversed, or Hann window.
- Pitch.
- Synthesis engine: either “Basic” for basic shapes, or “PM,” for 2-op sine wave phase modulation.
- Timbral parameters:
  - Basic engine: choice of waveform, sine wave or triangle. I originally added square and saw waveforms to the Basic engine, but decided I didn’t like the result much.
  - PM engine: index and ratio.
- Inter-onset interval (IOI): nominal distance to the start time of the next grain. (Not actually used by the synthesizer, but convenient to treat as a grain parameter.)

I didn’t bother with antialiasing in the oscillator, because who cares, it sounds fine.

There is some amplitude compensation so that the volume tapers off if the pitch exceeds a fundamental of 1000 Hz, which mitigates ear-piercing highs. I also reduce amplitude a little bit for longer durations.

The “distance” parameter’s main function is to send the grain to a reverb. I implemented a stereo-to-stereo 16x16 FDN reverb with a mixing matrix inspired by a paper by Menzer and Faller<sup>[12](https://nathanho.me/posts/evograin/#MF2010)</sup> and energy-preserving LFO-modulated allpass filters.<sup>[13](https://nathanho.me/posts/evograin/#Werner2020)</sup> It’s not a great reverb and I spent little time tuning it, but it gets the job done. I was conflicted on whether I wanted to add reverb at all, but after implementing it, I found it makes the results easier to listen to. That is rather important given that I’m on headphones and auditioning dozens of these during the development process. EvoGrain outputs a mixed-down stereo file, but also separate files for dry, wet (before reverb), and wet (after reverb) so that the user can do their own mixing.

Several grain parameters are encoded using the logarithm of the parameter instead of the actual value: amplitude (dB units), pitch (MIDI note numbers), duration, IOI, and PM ratio. Other nonlinear mappings of grain parameters to synthesis parameters are possible; one example would be quantizing the pitch parameter to a scale.

## Adjustment: improving the grain set

Adjustment is my term for editing the grain set after it is generated. Adjustment is not a standard part of the L-system pipeline, but it improves the musicality of the result. Currently I have the following adjustment steps:

- The entire time span of the grains, from beginning to end, is scaled so that it is within a target range of durations.
- The durations of the grains are all scaled together so that their median is 20 milliseconds (exact value tunable by user).
- If a lot of grains overlap each other, their amplitudes are reduced slightly to avoid excessive dynamic range, a bit like a compressor.

More complex adjustments are possible — correcting panning so it’s centered, etc. I recommend making all adjustment steps deterministic.

## Interpretation: from command sequences to grain sets

A quick search for L-systems shows various nice fractals created with them. The step between the string rewrite system and the graphical output is *turtle graphics*. In the textbook example of this model, you have a turtle in 2D space with a *state* comprising position and orientation and possibly other things, and you send it commands like “move forward 1 unit” or “turn 30 degrees” or “set color to green.” Interpreting a series of commands alters the state and creates a final drawing.

While not inherently graphical, EvoGrain’s method is pretty similar to turtle graphics. The EvoGrain turtle consists of:

- The “turtle state,” comprising the parameters of a grain: start time, IOI, duration, panning, amplitude envelope, etc.
- A FIFO stack of turtle states, which is initially empty.

The commands of the turtle are as follows:

- Grain (g): use all the parameters in the turtle’s current state to produce a grain, then advance the start time forward by the IOI.
- MoveParam(param, delta) (m): move a numerical parameter by a relative amount. For example, MoveParam(Pitch, +2) increase pitch by two semitones. In the next section, this command will be revised.
- SetParam(param, value) (s): set a numerical parameter to an absolute value.
- FlipPan (p): mirror the pan parameter from left to right.
- SetEnvelope(type) (e): set the amplitude envelope.
- SetSynthEngine(engine) (y): set the synthesis engine.
- SetBasicWaveform(waveform) (w): set the waveform for the Basic engine.
- Push ([): save all parameters, including time, to the stack (FIFO).
- Pop (]): remove the last entry from the stack and set the current turtle’s parameters to the entry’s parameters.
- PushSequence (<): same as “Push.”
- PopSequence (>): remove the last entry from the stack and set the current turtle’s parameters to the entry’s parameters, but do not change the current turtle’s time parameter.

Clearly, `Grain`, `MoveParam`, and `SetParam` are the most important here. If you interpret 10 `Grain` commands in a row, you’ll produce 10 identical grains evenly spaced in time. If you insert MoveParam commands in between, with small deltas, the grains will be different from each other, creating smooth gestures. There’s also the balance between absolute (`SetParam`) and relative (`MoveParam`) parameter changes; if it’s mostly MoveParams, then the movements of parameters will be incremental, and if it’s mostly SetParams, the grains will jump around more (and in the context of L-systems, often jump to consistent and specific values). The relative occurrences of these three commands are musically relevant, and the effects of changing them are easy to hear.

The four “bracket commands” `Push`/`Pop`/`PushSequence`/`PopSequence` are important for creating repetitive structures (although the L-system itself can also create repetition). `Push` and `Pop`, crucially, allow the turtle to teleport backward in time and create polyphony.

Commands can be as ad hoc as desired. For example, I added `FlipPan` because bouncing back and forth between the L and R channels just sounds nice. A well-designed command set will bias the system towards better results. You might be able to think of more turtle commands — some ideas I had but didn’t try include: velocity setting that multiplies the delta of future `MoveParam` commands allowing slowing down or speeding up or mirroring the turtle movement; a variant of `SetParam` that moves to the average of the current value with the new value rather than a hard jump; using the current size of the stack to influence grain parameters; commands to disable or enable pitch quantization to a scale; a command that creates a marker in time that causes nearby grains to be modified (attracting or repulsing them, etc.).

### Dealing with boundaries

`MoveParam` has a major issue: there is no particular logic to prevent a turtle from walking over to a wacky parameter value and possibly rocketing off to infinity. Using more `SetParam` and `Push`/`Pop` commands can help mitigate this, but are insufficient to prevent it. A naive solution is to clip out-of-bounds parameters so they are back in bounds, but this often results in the turtle sticking to the boundary, which isn’t great especially for pitch. Alternatively you can mirror the turtle between the two bounds, but this feels like a cop-out, and the behavior is unmusical as often results in the turtle zigzagging between the two boundaries. You can also let out-of-bounds parameters happen and address them at a higher level by discarding or penalizing L-systems with such problems.

But my favorite solution was inspired by Manousakis, where he describes “threshold” operators. The idea here is to make the logic of relative parameter settings more complex. We add a new field to `MoveParam` like this:

- MoveParam(param, delta, reset): move the parameter by relative amount delta. If the resulting value is out of bounds, reset the parameter to absolute value reset.

The “reset” parameter should be selected so that it is always within bounds. Although ad hoc, this makes sense if you think of how a jazz improviser might operate — if you do an upward run to the very highest register of your instrument, jumping back to a normal range is a natural thing to do, especially if extreme registers cause fatigue.

But still, the turtles consistently run up to the extreme edges of the boundaries, which I still find unmusical. To fix this, I used fuzzy logic. Each parameter is assigned a trapezoidal function f(x) which is 1 when we are completely in bounds, 0 if we are totally out of bounds, and ramps linearly between them:

- MoveParam(param, delta, reset): move the parameter by relative amount delta. Let x be the resulting value. Set the parameter to x f(x) + reset (1 - f(x)).

Thus if f(x) = 0 (in bounds), it moves the parameter normally; if f(x) = 1 (out of bounds), we reset; otherwise, we linearly interpolate between those behaviors. I like this approach as it causes the marginal distribution of the grains for each parameter to taper off as they approach the bounds.

“Boundary hugging” problems are a well-known in algorithmic music. A paper on algorithmic melody generation by Brown et al.<sup>[14](https://nathanho.me/posts/evograin/#BGD2015)</sup> discusses this issue and using an “elastic band” in melody generation, where with each new note we average the pitch with the center of the range. This “elastic band” helped inspire the above fuzzy logic approach. Remember, setting boundaries with your turtle isn’t selfish, you’re just practicing self-care.

## Expansion: from L-systems to command sequences

Many good resources introduce L-systems, such as a 1986 paper by Prusinkiewicz.<sup>[15](https://nathanho.me/posts/evograin/#Prusinkiewicz1986)</sup> I will go over L-systems here if only to disambiguate terminology. An L-system consists of an alphabet of *symbols* which are either *variables* to be rewritten, or *terminals* which are left untouched by the rewriting system. In this case, terminals are precisely the commands given to the turtle. The L-system also has one variable designated as the *axiom*, and a set of *rules* so that each variable is mapped to exactly one string of symbols (the *successor*). The L-system is run by starting with a string consisting only of the axiom, and rewriting variables according to rules to produce successive generations. The L-systems I talk about here are deterministic and context-free (“DOL-systems”).

Many L-systems will keep generating longer and longer strings infinitely, but we need a finite result here. One option is to only iterate a finite number of generations. I ended up using a technique inspired by the Iamus papers, where I assign each rule a *budget*, which is a positive integer defining how many times the rule can be invoked. After a rule is used that many times, its associated variable is replaced with an empty string.

It’s worth noting that while many examples of L-systems use a finite alphabet, this one doesn’t, as commands allow parameters like `SetParam(Pitch, +60.234)`. However, since commands are terminals, the rules don’t know about them.

All steps described so far — expansion, interpretation, adjustment, and synthesis — are all deterministic, and the L-system unambiguously encodes the audio file it generates. Although there is considerable literature on stochastic L-systems, determinism is best in this context. It’s nice to be able to tweak these steps and see how the changes impact the result without a confounding factor of randomness in between.

## Randomization: generation of L-systems

I’ve walked backward through the entire process of going from an L-system to a final audio file. Now for the first step in the process, which is producing the L-systems themselves. This step is very open-ended and I’m sure you can find ways to improve and expand on what I’ve done here.

The main way that L-systems shine is their ability to model hierarchical outputs. A lot of music is hierarchical in some way — an entire piece divides into sections, sections divide into phrases, phrases divide into gestures, gestures divide into notes. Although I’m not trying to generate entire pieces, I find EvoGrain’s output most personally appealing when it has a clear fractal-like shape to it, just like an entire composition might.<sup>[16](https://nathanho.me/posts/evograin/#2)</sup>

Many examples of L-systems are handwritten ones with only a few rules and a few symbols. Here the L-systems are larger, with 50 rules and up to hundreds of symbols in each rule. Here the 50 variables — the symbols that only exist in the L-system to get replaced with other symbols — are given only numbers and labeled #0, #1, #2, … with #0 being the axiom. The symbols are divided into two groups: #0-#19 are *macro variables*, which are viewed as creating the largest structures in the grain set. #20-#49 are the *micro variables*, which produce the small gestures of maybe a few grains. Although I found 20–30 to be a nice split, the number of macro variables and micro variables can be changed.

The randomizer uses the following logic to generate L-system rules:

- For a macro variable #n, the successor is a string with about 15 symbols, and each one is:
  - 90% chance of macro variable randomly selected from #(i + 1) to #(i + 4) inclusive.
  - 10% chance of a random turtle command.
- For a micro variable, the successor is a string of 50–500 symbols, and each one is:
  - 95% of a random turtle command.
  - 5% chance of a micro variable.

So #0 is the entire piece, #1 is the highest-level structures, #2 the next level, etc. But they do not perfectly nest, as #0 can jump down the hierarchy and invoke #4. The later macro variables can expand to micro variables, and the micro variables can reference each other ad infinitum.

The numbers of symbols in the the successors affect the length of the generated command sequence, and ultimately the number of grains in the final result, so it is quite important to tune it correctly.

To generate a random turtle command, we just pull commands out of a hat. The probabilities are selected so that `MoveParam` and `Grain` are most common, `SetParam` is relatively rare, and other commands even rarer. The bracket commands `[ ] < >` are inserted after all the others in a way that guarantees that they are always matched. This is done by selecting a random set of insertion points and generating a random [Dyck word](https://en.wikipedia.org/wiki/Dyck_language).<sup>[17](https://nathanho.me/posts/evograin/#AS1980)</sup> I don’t know how necessary that is, but it bugs me if they aren’t.

`SetParam` and `MoveParam` commands have numeric fields that the randomizer must supply. To set these values, I have manually defined two probability distributions for each synthesis parameter: an *absolute distribution* and a *delta distribution* for each grain parameter. For example, for pitch the absolute distribution is a uniform one from MIDI note numbers 30 to 120, and the delta distribution is a normal distribution with standard deviation 3.0. When the randomizer creates a `SetParam(Pitch, <value>)`, the value is sampled from the absolute distribution, while the delta in `MoveParam(Pitch, <delta>, <reset>)` is sampled from the delta distribution (and the reset value from the absolute one). Most of the delta distributions are symmetrical around 0, but the distribution for amplitude (in dB) is skewed so that amplitude is more likely to decrease than increase from grain to grain, which sounds nice since it vaguely mimics decaying echoes. These distributions are only known to the L-system randomizer to produce these commands; they are *not* sampled by the turtle, because interpretation of the command sequence is deterministic.

As an example, here are the rules of an L-system randomly generated by EvoGrain, which is at the top of this article and below as Grain Set #6. Each command is represented with a single letter, so for brevity I am not showing the arguments for `SetParam` (`s`), `MoveParam` (`m`), etc. Viewing these rules directly is not very illuminating for understanding the grain set, only for illustrating the behavior of the randomizer.

```
#0 [budget 5] -> #1<#1#2<#4#2>m#1>#4#4#1#4[#4]#1
#1 [budget 6] -> #5<g[#5]#2g<#3>#3>
#2 [budget 9] -> [#3#3[#4]#5[m]#4<#3<#4[g]#3>#3>#3]
#3 [budget 11] -> m<#6#7>#7<#6>#6#7#4#4<#6#6[#6#7]#4#7>#6
#4 [budget 10] -> #7#7[#7#7]#6<#6#5<#5[#5m]#8#7[#7]#6>#7[#7]#6#8>#8#8
#5 [budget 13] -> [#6[#6<m>#8[#6]#7[#9#7]#8]#7]
#6 [budget 14] -> #10<#10<#8#8>#10#7#8#8<g#8gg#9>#8#9>
#7 [budget 12] -> <#9#9<#10m[#9]#9#9#9>#9[#11]#9#10>#8#8#9
#8 [budget 9] -> [#10[#12[m]#9]#10#9#11]#11#10#10[#12]#11<#12>#10
#9 [budget 10] -> #11#10<#11#10#10#12#10#11#13#10#12#13#12m>#11#13m#12g#10
#10 [budget 8] -> <#14#14[#13]#11<#13>#13>#14#14<#11[#12]#13>#13[#13#12[m]#12]
#11 [budget 10] -> #15#15#13#15#12[#15#15#12]#13#15#12#14#15#14[#14#12<#12>#12]
#12 [budget 9] -> #15#15[#15]#15<#15>#16<#14#13>
#13 [budget 13] -> <#16>#16#16[#16<#16[m]g>#17]
#14 [budget 8] -> <#16#15<#16>#18>#16[#17]#15
#15 [budget 11] -> <#18m<#18>#18[#17[#18[#16<#17#17>#16]#17]#16]#16>
#16 [budget 8] -> [#18#19#18<#17#17#19>#18]#19#17m#17#17#19#19#17#18[#17]#19#19#19
#17 [budget 17] -> #20<g#19#18#21>#21[#18]
#18 [budget 15] -> #19g#20<#22>#20#22[m#20#20#20]#20#20
#19 [budget 17] -> #20<#20#23#22#22#21#21#20#21#23[#22#23[#23]#20#20]#23#21#20>
#20 [budget 11] -> #21gmmmggmmggmmmmmmm#36gm#22mgggmmgm#25#26mm#31<#35[#30mg]m#23#33gmgmmmmmmgmmmmmmmm#34mgmmmmmm<mm[mmmmgmmmgmgm]mgmmgmm#21mmmggmmmmmgmggmm#32gmmgmgmmgmgggmmgmmmm[g#43mmgmmmmgmmgmmmgmm#46mggggmm#20#27gmmggmgmmggmwymmmmmm]mmmgmmmmmmmmgmm>wgmmmmmmmmmm#41m#31mmmmggggmggmy#37>mmmmmmmmgmmgmmgmgmmmggg#35gmgm
#21 [budget 17] -> mggmmgmmmgmmmmm<mmgmmmmgmgmmmmgmmmmgmmg<mmmmmmmmmmmgmmmmm[gm]gmgmgmmmmmgmmm#36mmmmggmm>mgmmmmggmmmmmgmmmm#30m>gmmmgmmmmmgmgmmmmmmmmgmgmgmgmgmmmmmmmmmmmmgmmmmgmmmmmgm#24mg#24mmmmmmmmg#40mmmmgmmmgmmmmmmgm#42g#43#47mmmmgmmy#22wggmgmgggmmmgmgmmmmgmmmmmgmgmmgmmgwmmmmmmmmgmmgmmmggmmgmmmgmmmmgmgg
#22 [budget 13] -> m[mmgmggmmgmmmmmmmmmgmmmmgmmggs]mgmmmgm[mmgmg#37mmgggmmmmgmmmmmmmmmmmmmgmmmmmmmgmmmmggemmmggmgm#42mmsggmmmgmmmggggmmmpmmgg#22gmmmm[mmmmmmm]#34gmmmgmgmmmggggmg#31m]mmmgmmmmmmmmmmgm#28mmmgmmggmggmmmmggmmmmmm
#23 [budget 8] -> mmmgmm#42ggggmmmmmgmmmsmmmmmmmgggmmmmmmm#31#20ggmmg<mmmgmmgmmmmggmm#27mmpmmm#32mmgmggmmm#37mmmggggmmgmgmmgmmmmmgg#41mmmmmggmgm#46gmgmgmmmmggmgmgsmmmmgmmgmgmmmmmmmmp#26mgmmmmmgggmmgm#22mgmmmmgmmgmmmmgmgmggggmg<gmgmmggmmmmgmm>#36mmggmmmmmgmmmmmmmmgmmmmmmmmmgmggmmmgmmmggmggm>mmggmmmgmmmgmggm#43gmmmmmmmmmgg#43mggmgmmm#39mggmmmmmmgmmmmmmmmmgmmmmgmmgmgmm
#24 [budget 9] -> mmmm<mmmggmmmgmmggmgmm#37mgmgmmmm[mmgmmmmggmmgm]gmmmmmmmmmmmg[mgmmmmmmygmmgmmmmmgmmmg#31m#32ggmmm#47m<gm>m#35gmggmmm#40gmgpmmmmmgmgmmm#34mmmmmm#37#42sm#36mmmgggmmgmgm#47m[ggmmmmmm#26mggmmmmgmmm]mmg[mgm#47mmmmmmm#40mmggmmmm#31gmgmgmmmmmmmg#29gmmmmmmgmmmgmmg#45mmm#44#36mgmmmmm<mmm#38<mgggmgmmgmmmm#25mmmmmggmmmmmmmmmmm#44mmggmg#33ggmmm#46gmggmg>mm#28#45gmmgmgmggmmmmmmgmggmgmmmm#27mgmmmmmmm#30mm#37gmgmmmmmgmmmgmgggm>mgmmmmmmmmmmgmmggggymmgmgmmgmmmmmmggmgmmmmmmmggmmmmmmmmmmgmmm]ggm#48mmmmgmgmmmmmmsmymmmeggmmgmmmmmmmmggmgmmmmgmmmmmm]mmmm>gm#33megmmgmmmmmmmmmgmmmgmmmmgmmmmmmm
#25 [budget 14] -> gmmmmmmggmmmgm<gmggmmmmmgmgmmmmmmmmmm#22mmmmmgmmgmmmmmg#34>mmgmgygmmgmegmmmmg<mm<m#25mmmmgg>m<mmm>g>mgmm[mgmm]gmgmmm[mgmm]mm<mgmggmgmmmm>gymmggm
#26 [budget 13] -> ggmmmmmgmgggmmmm<mgmgmggmmmmmgmmmmmmmmmgmm#33mggg[mmgmmm#37mmgmmgmmgg#25]#44gmm#40<mmmm#34gmmmggmggmmmgm#41mgmmgmmgmmmgmmmmmgg>mgmmmm>gmgmggmgmmgggmgw<gmmgmmgg>mmmgmgwgmmggm[mmgsmmgmgm]mmmm#38gmmmmmmmgm#27mmggmmmmmmmmgmmmgmgmggmg#44mgmmmmmmmmmpmggmmmgmmmmmmmmg#47mgmmmm#28mmmmmgymmmgmmmgmgmgmmmmmmmmmmgmmmmygmmmmgmmmggmgmm#43gg
#27 [budget 7] -> ggmm[mggmmmmgm#27ggmgmmmmmmm]#28mgmmmmmmmmmmmmmmmmmgmmmg<gmmmgmmggmmmmggmmggmmm#26#36mmggmmmp#37mmmmmm#31ggmmmmmmmmwmggmgggmmmmgmmgmmmgmmmggmmg#24mmmmmmmmmgm#20m#38gmmg#25#22mmmmgm>mmmmmmmgmmmmmmgmmgmgmgggmg#38#44mgmmgmmmmmgmm#44mmmmmmmmmgmgmmmgm#47mmmgmm[gmmmmg#47mmmgggggmmmgmm[mmmmmpmmgmgmmmmmgmgmmmgggmm#27m]mmmmmmggmgwgg#42mm#31ggmmmgmmgm]gmmmmggmmmmmmmgggmg#24ggmmm
#28 [budget 11] -> mmmmgmmgmmmmgmmg#41mmmmgmmmmmmmmmmmgmgmmgmgmmmmmmgmmmmmmmmgmmgmggmgmgmgmgemmmmgpmmmggmgggmg#39<mmmgggymmmgmgggmmmg#40mmmgmmgsmmgmggmmgmmgmmmmmgm#47mgmmmmgmmm<gmggmgm[mmmmmgmgg#44mmg]m>mgmmmggmgym>mmgggmgmmmm#42ggmgmmg<mmmmggmggmmyggmmggmmmmmggmmmmmmggggmmggggggmmgmmggmmmgmmgmgsggmmmmgmmmmgmm#32m#20gmmmgmmmgm<gmgmmmym#48mmggg>mmgmmmgmmmmmmmmmmmmgmmmmggmmmmmmmmmmm#32mmgmgmmmmg#31mgmmmmmmggggmggggmmgmmmmgmmgggggmmmgmmmm>mgmmmmmgmmmmmmggmmmgmggmmmmmmmmm#30g#29gmm#31
#29 [budget 14] -> <mmmmmmmmmmmmmg[mm<mmmgmgmmgmmmgm>m]ygmmmmwgmmmmmgmmmmgmmmmmmmmmgmmmmmmmg#31ggmggmgggmg#41<mmmmmmmmmggmggwgmmg#20mggmmgmmmgmmggemgmggmgmmmmmmmgmmgmmm#39ggmmgmgmgmmm#20mgmmgy#49mmm#20gmmgmmmmgmmmgggmmmgm#22mmmmgmmggmggmmgmmgmgm#40gmgm#21gmm>mmmmmgmmmmgmmymggmmggggg>gmg#29gymmygmmmm#27#37m#44m#33mmmgmm
#30 [budget 7] -> mmmm<mmmmmgggm[mmmmggmgmgmmmmgmmm]gmmmmmgmmmmgmggmmmgmmmgmmgmmmgmmm>g#40gmmmmsgmmm#49mmmmm#21gmmmmemmmmmgmmmmgmmmgmgmgmggmmmm#37#45mmm#25mmmgmm#28wmmmggg#29#36ggm#20mm
#31 [budget 9] -> mggmgmggmm[mmm#32mmgmmgmgg#39ggmmmmmm#22mmm#21gmggmmgm#21mmgmggm#38ggmmmg#27mmmm#25gmgmmggmmmmgm#39ggmmmmmmmmmmmmg#35mmmwgmmmmmmmmmmsmmgm#24mmmmmgmmggmmm#49gmmmgmmmggmmgmmgmmmygmgm#48m#41gmggggwmmmgggmmmgmmmgmmmmmgm#46mgmgmmmmmmmmmmmgmmmmmmmmmmmmmmmsmmgm#27mmg[mgmggggmgwgmmmggmg#22mggmgmmmmgmmmmmmggmm#23gmgmmmmmgmmmmmgg]mmmmmgmm#24mg]#23gmgmmggmmmmm#48
#32 [budget 13] -> mmmmgggg#39mmmmmmmgmgmmmmgmggmgmmmmmgmm#25g#48mmgmmm[mmmmgggggggmmm#34gmm#34mm#28mmmmmmgmmmmgmm#31mmmmmmmg#35mmgmmm#46mmmmmmgmmmmgmmmm#42gmmmmmmggmmmmgggmmmm]ymgmmmwggmmmmmm#35mmemmmsmmmm#23mgmmmmm[gmmgmmgmm#27mmm#44mgmmmg#44#44mmgmgmmmmgmgg#28mmmmgmgmmmmmgmmgmmgmgmgmgmmmgmgmmgmmmmg]gmgmgmmmm<#47mgmmgmmmgmmmmmmmm#35mmmmmmgm#26mgmmgmgmmgmgmmmmgmmgmgmmmmmm#36mmgmgmmgmmmmgmmym#23gwgmmmmgmmmggm#40mmmmgmmgm#40mmmmmgmmmgmgmmgmgmmmgmmgmmmmmmgmg#42mgmmmmggmmmmm#25mmmmmmgmm>mmmmmmmmmmmmgggmgmmggmm#28gmmgmg
#33 [budget 5] -> gmggmggmmm[m#42g<mgmgmmgmgmmmm#27m>ggm#22mmmgggggmmgmggmggm#27#42mmmmmggmggmmgmmg#29mmggmmmmgmgm#47mmmmmmmmmmmmgmg#22gmm#21mmmgmggmmmggmmmmgmmmmgp#28#33gmgmmwmgmmmmggmgmgmgmmmmgmmmggmmmmmmmmm#24mmpmmgmgmgmmmmmggmmgmgmmgmmmmgmgmmgmggmgmgwmmmmmmmmmmmmm]mm#33mgmmmmmmmggmgmmmgemg#33gmmmmmmgmmgmmmmgg
#34 [budget 10] -> mggg#24gmmm#28mmggmmgmgmmmmgmmgmggmmmgm#33ggmmggmmmmmmmgm#39mmmmgmmmggmmmmg#49mmg<mgsmmmmggmmmmmmmmmgmmmgmmmmmm>mmg#43gmmm#49mm<mmmgmmmggmmmmmgmmegmmgg#36mgmmmm>mmmgmmm<g>mmmmgm#46m[ggmmgggmggmm#49mmmmmmmmmmmmgmm#22gmggmmmgmmmgmmmmmmmm#31ggmmggmmmgmmmmmmg#26mmgmgmggmmgmmmmmmmmm[mm]mmmmg]msmggmmwm[ge]m#40mgmmmggmgmmmgmmmmmmmgmmmgm
#35 [budget 13] -> gmm[gm<mgmgmm#28gmmmm[mgm]mmgm#46>mmmgmgmgmg#36mgm#48m#24gggmm<mmmmmggm[mmg[mmg]gm]m#41>m]gm[gmmm#22mmmmmmmmm]mmygmm#44mmmgmggmmmm
#36 [budget 13] -> mmmgmmm[gmm]gmmm#42mmmm[ggggmm<gmmmg>gp#26mmggg<m>mm]mmg[g#42<mg>mmmm]mwg
#37 [budget 11] -> ggmmgmg#38g#43gmgm#26mmmmgmmmmgm#29#28ymmmmmgggmmmggggmmmmgw#20mgmmm[m[mgmgm#24mmmmggggmmmgmmmmmmgmmmgmm[g#49mmmmgmggmmmg#21]mmmgmmmmmmmggmmmmmmmgpmgmgmmmgmpgmmm[gs#30mmmm]gmmgm]mmgmm#33mmm[#35mmmmmm]gmgme]mmmmmmgggggmmm#45gmmm
#38 [budget 9] -> mmmgg#26mps#46mmmmsgggmgg#45gm[gm[mmgmmmggmmmgmmmggmgm#35mmwgmm#34mm[mmmgmmmmm#33mmmmmm#25m]mmgmgmmmggm<gggm<gg>mmmmmmgmmmgmmggmmggg[gmgmmgmmmmmgmm<mgg>mmgmgmgmggm]mmmmmmgm<mgmmgm>mgmmggm#32mgmmmmmmmm>mgmgmmgmmgmmmmmmmmmmmmmg#32mmmmgg<mmmgmmmem>mm<mmgmmmgmm>mmg#41gg#40mmmmmmmmmmmggmmmm#28mmgmm#29m#32g]m]mmmmgg
#39 [budget 10] -> mmgmmmgmgmgmmmmmmgmmmmmmmmmmgmmggm#33gmmg[ggmmmmmmmgmmgmmmmgmmggmm#21<m#30#32mgmmmgmmmmgmgmgggm<#29#35mmgmmmgmmmmgm#41mmmmggggmmmmggmmgmgmgmmggmgggmmmmmggmmmmmmmmmmmmgmm>mgmmgggmmgmmwmmmmg#24mmmmmmmgmgmggmmmmmgmmmmmmmgp#45ggmmmggmmmmgmm#40gmgmmmmmmm#21mgggmmmgm#47mmgmmgmmgm#25mmmmmmmmggmmmmmmmgmggmmggmmmmmmmymgggmmmgmggmmmm>mmmmmgmmmmmmggmmmmggmmmmgmgggmg]mmmggmmggmgmm
#40 [budget 15] -> #21mmm<gmggmgm[ggggmmgmg#28mgmgmm]wgmmmmmgggmmmmgm#23g>mmmgmmm#42#23mmmsmgmmmgggmmmmmmgm#42mmm<m#48ggmmggmgmgmmgm>m#38mm<mmsmmgmmmg<mgmgmmmmggmmgmm>mmg#24gmmm#33ggmg#31m>mmmgmggmmmmm<mmmmgmmmgmgmmmgmmmmm>mmggmmmmgmgmmm#32ggg#23mmmgmgmmgmgmmmmmgmmmggmggmmmmgmmmmmggmgmmgmg#32mmgmmmggmmmmg
#41 [budget 18] -> mwpmmm#45gmgg[mmg#35m[mmgms#23mmmmm<mggggmgmgmmmmmmgmmmmmmmmmggmmmgmggmmmmgmmemmmggmmmg>mmmgmmmmmmm#43gmmmmmgmmm#27mgmmmmmmmm#37mmmmmgm#41mmmmmmmmmmm#48mmmmmgm#22mmgmgmmmgmggmmmmg#21mgmmmmmgmmmmgmm#20mgmmmmmmmmmm#44mmgm]gg#29gmmmmgmgmm[mmmmgmgmmgmmmmmmmmmwmm<gmmmmmmggmmmmgmmmmgmmgmmmw>mmmgg]mmgmmgmmmgmmmgmmmm<egmmymmmm#23mmgmgmmmggmmmwgmmmmmmmgmmm#23ggmgmwgmmmmmggmm[mmmmm]msg#32mgm>mmmmg#22mgmgmmmmpwg#45gmg]mmm#37mgggggmmmgg#41mmgmmm#31mgg
#42 [budget 9] -> mmmmmmmm#44mggmgmmmgmmmmggmmgmm#35[mgmmmm#22mmgmmw#36gmmmmmmmmgmm#34gmmggmmmgmmmmg<ggmmmggmg#27mmgmpmgmmmm#36mmggmym#34gmmmmgmgmgmmmmmm[mmgmmwgmmmgmgmgmmmgmmmgmmm#31mmmggmmgggmmmmmmggmmmmmmgggmmmmmgm]mgmmmmmmgg#45mmgmmgmmmgmmmmgmm#20mgmmggmmmmm[mmgggmmgmmgmmgmmmmgmmmmmmm#33gm[gmmmm#30ggmggmgmmggmgpmg#43mmmmmgmmmmgmmmgmmmmymmm#44gmmg#47mgmmm#28#40mmmmmmmgmgmmmgmmmmmmgmmmgmggmmgm]mm#36mgmgmgmgmmg#49mggmmmmmgmgggmmm]gm#34mgmgmmm>m#29mmmmm]mmmggmmmmmmgmgmmgmmmm#20mmmgggmgmggymgmmgmggmm#21gmgmmmmmmmmmmmm
#43 [budget 8] -> #21m[gmmmgmgmpgmmmgemmmgmm[m#33g#35mggmmmmm]sgmmmgggmmmgmmgggmgggmmmmmmgmmmmmmmmggmmmmmmgmgggmm#35mggmmmmgmm#39gmg#21wmmmmgmgmmmmmmpgmmg#33mmmmgmg[mmmggmmgmgmmmmmgmgmmmmmmmmmgmg#38mmmm#22mmmmmgmmmgmmmmmgmgwmmmmmm<mmmmmmpmmmmggmemmmmmwmgmmmmmgmmgmmmmm#48mmmmmgmmmmmmmgmm#49mmgmmgmmmgmm#26mmmm[sm#44gmmmmmggmggmmm]mm#29mmg<mmmmgmmgmmggmg#22mmmmgmmggmmmmgmmmmgmmmmmmmgmmmgmwmgmmmggmmmmmmm#33#45gmm<mmmm#43mgmmmmmmm#25mmmmmmg#37mmmmmmmmmmmggggmgmmm#48mmmm#20mmmm#38mm#42mgmm>mg>mgmmmgmmmmmmgmggmm#40>gggmmgmyg#36mmgmmmmmpmmmmmmmmgmgmggmmggmgmmmmgpgmm#47mmmm]#30mm]gmmmgggmmgmmgmgmmmggmmgm#36ggmmgmmmmmmmmmgmmgmmmggmm
#44 [budget 18] -> gmgm[mmmmmgmmgmmmmmmg#33gmmmgmgmmmgmggg#34mggmmmgmmgmgmgmmmm#39mmmmgmmgmmmmmmmmmmmmmggmmmmmmmmmmmmmmmmmgmmmm<ggmmmgmmmmmmmmgggmgmm<mmgmggmmgmmgmggmmggmmmmgmgmmg#43mmgmgm>mmgmg#26mmmmgmmmmmmmmmmgm>mmmmpmgmmmgmggmmmggm#24#22mmmmggmmmgmmmmmmgmgmmmmggmgmmgmgmgg<mmmgmmpgmmmmmmmggmmmgmmmmgmmgmmmmmggmmmg>mmmggmmmsgmmmgmmmmmmgmgmmmmygmmmgmmmmmmg#35g#20mmmgmmmmggmmgmgmmwmmmmmmmmmmgmmmm#33mmmmmmgmmmmgmgmm#34mmmmmm]mmmmmggpmggmmsmmmmgmmgg#43m#39mmggmmg#37m#35mgmmmmgmmggmgm#28mgmggmmmgmgmgggmmgmgmgm
#45 [budget 10] -> g[gm#24gggg#21gmmmmmggggmmmg#21m#49<gmmmg#43mmgmg<mmmmgmgmmmmmmm#42gggmmm#49m>gmmmmmgmmmggggggmmgmmmmmmmg#49mmggm[mmgm]gm#46gmmggm#32mm>g]mmegmsg[gmgmmgmmmggmmmgggmgmmgm]mmg#28mmmggggmgmmmmgmgmmm[gmgmmm]mmmm#48mgggmgmmgmmmggmmmmmgyg
#46 [budget 12] -> mmmmmm#36mmmmmmgmgmmmmgg#39mmmgmmmmmmmmmmmg[gmgmmmg]mggmgggmmmggmmwmmmgggmggmmmmmmg#32gmmgmmgm<mmmgmmmm>pggmgmmmm#42g#42gmmmggggmmmmmmgmmmgmmggmggm#25m<ggmmmmmmgmmmmmm>gmmmmmmmgmgmgmmmm#20ggmggmgm#21mmgggmgggmmmmmmm#42gmmmmgmgmgmmmmg#30m
#47 [budget 10] -> mgmmmmggg#39gmgmmmmmmgmmgmmggmmmmmmmmgmmmggggmmgmgmmmgmgmmmggm[gmgmgmggm#47#30mmmggmggmmmmmmmmgm]mmmmmm#39ggmm#40mgggmmmmgmgmmwmggmmmm#30m<mmmmmmmggmg#24mm#49mmmmmgmmmmmgemgmmmgggmgmgmgmmmg>#40ggmmm#44mmsmgwmmsmm#22mggmmmmmggm#31mmmmmmmgmgggggmmggmmmmmmmgmmmgmmmgmmgmmmmgmmmmgmgmggmgmy#39gmmmmmmggmmmmmgmmmmmmgmmmgmmg#38mmmmmmgmm#31mmmgmm
#48 [budget 11] -> mmmmmg#35gmgmmmmgmgmmmmsggmmmm#28gmgmmmmmmmmmm#32gmmggmgmmmg#43gmmgggmmmmmgmgggmmgmmgmym#20mgmmgmmgmmgm[ggmmmmmmmmmmm#21mggmmmmmmmmmmgmgm#29mmggmmgmgmmgmmgmmmmmmmmmggmgmmmmmmmmgggg#32m#22gmmmmmmmmwgmggpmmggmmggmmmgmmmmmmmgggmgmm<mgmmmmmgmmggmmmmmmmgmmmmmmgmmmgmmmgggmmmmmmmmmmmmgg#32mm>gmmmggmgmmmgmmgmmmmgmmmgmmmggmm#46mmgmgmm#41mmmgmmmgmmmgmsmmmmmgmggmm#24mgmmmmgmmgmmmmmmgmgmmmmmmmm#28mgmmm#38gmgmgmmmmmymgmmmmgm<m#31g>#36mmgmmmmmmmmgmgmmgmmgmmggmmmmmggmmmggmmgmgmmmmmmmgymmmmmmggmmmymmmmgmmmmmmmg]gmmggmmmmmmmmmmmmmmmmmm#23mm#26gmmgmmmmgg
#49 [budget 7] -> mmmmggm[mmmmmmmgmgmmmmmmmm#28mgmmggmgmmmmggmmm#44mmgmmgmmmmgggggmmgmmmpmmmgmmmm<m#21mgmmgggmmmmmmgmmmgmm[mgmgm]mmmgmgmmgmmmgmm#43mmmm#46gmmggg#23mgmegg#21m#28m#23mgm>mmmg#49mmmgmgmmmmmgmm#30gmmggmmmgmm[m]mmm#34mgggmg#49g#41gmmgm#43mgm]mmgmmmm#35mmmmmgmmggmm
```

## Evaluation: the fitness function

It’s quite difficult to predict what the final grain set will be from an L-system aside from just running it. As a result, it is entirely possible that the grain set will be *basura*: it might have too few grains or too many. This is where we introduce the fitness function, which closes the loop by evaluating how good a given grain set is.

To compute the fitness, first I compute some descriptive statistics:

- Average number of grains per second (computed as total number of grains / length in seconds)
- Median and 90th percentile of pitch
- Median “overlap factor” (defined as duration / IOI for each grain)

For each of these features, I define a trapezoidal function which assigns higher scores to values I like better. For example I like the median pitch to be around C4 (middle C) but no higher than F#6, so I define a trapezoidal function that starts at 0 at 60, ramps to 1 at 70, stays at 1 until 80, and ramps down to 0 at 90. I take the actual median pitch from the grains and plug it into this trapezoidal function to get a score ranging fom 0 to 1. I compute similar scores for other stats, and do a weighted sum to get the final fitness metric.

In designing this fitness function, I prioritized metrics that were easy to implement and were useful for avoiding the types of outputs I didn’t like. Currently, the fitness function is built just to reject obvious junk rather than do any kind of aesthetic evaluation. More sophisticated metrics are possible which add to this by using computational aesthetics methods to find subjectively better grain sets. I’m not entirely sure what those metrics would be. Either way, for those exploring that direction, I would recommend multi-objective optimization: one fitness value identifies obviously bad outputs to be discarded, and another does a beauty contest.

The fitness function only requires a grain set. You could synthesize the audio and then compute amplitude, spectral centroid, etc. and do time-series analysis on that. I actually did this in an earlier, failed attempt at this project about two year ago, but found that the fitness functions were difficult to design and unintuitive to tune, and also the synthesis and analysis steps made iteration much slower. Still, the aesthetic potential of having the synthesis algorithm in the feedback loop is tempting.

## Search: finding L-systems with the best fitness

Although I gave my software the working title “EvoGrain” and it was mostly inspired by Iamus, an evolutionary computing project, I ended up not using genetic algorithms. *The Algorithm Design Manual* flatly discourages the reader from using GAs for optimization, arguing that the added complexity doesn’t pay off. That is just one opinion, but one I take seriously. Plus, it isn’t necessarily EvoGrain’s goal to find an optimal solution, but rather to just produce a diverse set of results that sound good. This suggests that very basic optimization algorithms are OK here, and in practice that seems to be the case.

The search algorithm I ended up with is to generate a pool of 100 random L-systems, evaluate their fitnesses, and pick the L-system with the highest fitness. I then perform a basic Random Search by doing the following 10 times: pick a random rule of the L-system, re-randomize it, check to see if the new L-system has better fitness than the old one, and replace if so. Because the fitness function is the sum of trapezoidal fitnesses, there is a maximum fitness which can be achieved, which allows us to quit early if we reach it. (I have a hunch that trapezoid-shaped fitness functions are good building blocks for evaluation of computational art — often in artistic decisions, there’s a range of pleasing values rather than a single best one.)

My takeaway from the earlier, abandoned prototype of EvoGrain is not to overengineer the fitness function or the evolution side of things. These parts of the system are not really where the magic happens, and the bulk of effort in this project went into the randomizer, the turtle command set, and the synth.

# Implementation & Results

EvoGrain is an offline, command-line Rust program, about 2,000 LOC. There are no special DSP libraries, just the `hound` crate for WAV output. The output files are:

- The L-system, serialized as JSON, providing a complete recipe for all other files.
- Four stereo WAV files: dry, reverb input, reverb output, and mixed dry + reverb output.
- A textual “report card,” displaying human-readable stats like grains/sec and fitness to help with tuning and debugging.
- A scatterplot (using the plotters crate) of the grains with time on the horizontal axis and pitch on the vertical. Color indicates synth engine.

The grain sets are unpredictable. Sometimes they generate audible and visible patterns with repetitive structures, other times they produce blobs and clouds. Sometimes a bunch of grains clump up at specific vertical moments. Either way, there is always some kind of shape. This is not an endless texture started and stopped at arbitrary points; there is always global structure, and it anticipates the end of the audio (or rather, it decides when the audio file ends).

I would say EvoGrain succeeds in all the goals I set for it, except for the one of producing diverse outputs, which is arguable. I’ve listened to a lot of EvoGrain outputs and it’s turned me into somewhat of a connoisseur, with the results clearly quite different to me. However, I would not blame someone else for saying the output sounds like indistinct bleep bloops. You be the judge.

## Examples

Here are ten uncurated examples of EvoGrain’s output, all using the same default parameters. I have plotted time on the horizontal axis and pitch on the vertical one and used pink for the Basic synth engine and blue for the PM engine.

It takes only a few seconds to run the entire system, from repeated randomization and search to producing audio output, so all these examples together took under a minute.

### Grain Set 0

![](https://nathanho.me/posts/evograin/examples/grain_set_0000/plot.png)

### Grain Set 1

![](https://nathanho.me/posts/evograin/examples/grain_set_0001/plot.png)

### Grain Set 2

![](https://nathanho.me/posts/evograin/examples/grain_set_0002/plot.png)

### Grain Set 3

![](https://nathanho.me/posts/evograin/examples/grain_set_0003/plot.png)

### Grain Set 4

![](https://nathanho.me/posts/evograin/examples/grain_set_0004/plot.png)

### Grain Set 5

![](https://nathanho.me/posts/evograin/examples/grain_set_0005/plot.png)

### Grain Set 6

![](https://nathanho.me/posts/evograin/examples/grain_set_0006/plot.png)

### Grain Set 7

![](https://nathanho.me/posts/evograin/examples/grain_set_0007/plot.png)

### Grain Set 8

![](https://nathanho.me/posts/evograin/examples/grain_set_0008/plot.png)

### Grain Set 9

![](https://nathanho.me/posts/evograin/examples/grain_set_0009/plot.png)

# Conclusion

EvoGrain is a research project. The point here is to demonstrate what is possible with this premise, not to pitch you a new sound design secret weapon. I have made the source code available, and if you want to use it you can. [Source code](https://github.com/nhthn/evograin).

I was able to code up a quick prototype of the EvoGrain system that produced decent sounds in about half a day of work, and good sounds in about a weekend. This is an invitation to try building this yourself. There are a lot of internal parameters to tune, and many big and small decisions, and every implementation will produce a different sound palette.

A few thoughts on further directions:

- Can this system be simplified while producing output which is no less musical? By “simplified,” I mean easier to describe in words or implement in code.
- Any synthesis engine could be used for the grains. Scrubbing a sample buffer would definitely sound great. I avoided doing this for EvoGrain because it’s too flattering — it’s very easy to get cool sounds with buffer granulation, and I wanted to do my best to get good results in the absence of samples. The possibilities with per-grain spatialization can be expanded; even with just stereo output there is a lot you can do with Haas effect panning or binaural virtualization.
- More interactivity. Maybe allow the user to edit the L-system directly. Or given an L-system, generate a handful of random mutations by making small changes to the rules, and let the user select their favorite.
- Inverse modeling. A paper[18](https://nathanho.me/posts/evograin/#SBMAK2010) describes taking an SVG image as input and reverse-engineering an L-system that produces an approximation of the image, which is honestly black magic to me. The system even lets the user modify the rules of the graphics to edit the image (!). Would this work at all for music or audio? Only one way to find out…
- Adopt genetic algorithms. Not really because they’re necessarily the best way to optimize the fitness function, but because they’re fun and cool. If you’re going to implement a genetic algorithm, why not go all in and implement a full artificial life simulator with nucleotide bases, codons, reading frames, and genomics?[19](https://nathanho.me/posts/evograin/#BDGRW1998)

# Footnotes

According to the Wayback Machine, melomics.com was last operational in early 2018. The current iteration of the site is plastered with ads for casinos. Interesting brand pivot.

Of course, the comparisons between fractals and music are highly dependent on musical style and culture. While I’m here, please be advised that fractals are not necessarily self-similar — a fractal need not look the same at every level of detail.

# References

Casas, María J., and Francisco J. Vico. 2009. “On the Performance of Some Bioinspired Genetic Operators in Complex Structures Evolution.” Proceedings of the 11th Annual Conference on Genetic and Evolutionary Computation, July 8, 1841–42.

Albarracín-Molina, David Daniel, Juan C. Moya, and Francisco J. Vico. 2016. “An Evo-Devo System for Algorithmic Composition That Actually Works.” Proceedings of the 2016 on Genetic and Evolutionary Computation Conference Companion (New York, NY, USA), GECCO ’16 Companion, July 20, 37–38.

Vico, Francisco, David Albarracin-Molina, Gustavo Diaz-Jerez, and Luca Manzoni. 2021. “[Automatic Music Composition with Evolutionary Algorithms: Digging into the Roots of Biological Creativity](https://link.springer.com/chapter/10.1007/978-3-030-72116-9_17).” In Handbook of Artificial Intelligence for Music, edited by Eduardo Reck Miranda. Springer International Publishing.

Brown, Andrew R., Toby Gifford, and Robert Davidson. 2015. “[Techniques for Generative Melodies Inspired by Music Cognition](https://direct.mit.edu/comj/article/39/1/11/94494/Techniques-for-Generative-Melodies-Inspired-by).” Computer Music Journal 39 (1): 11–26.

Št’ava, O., B. Beneš, R. Měch, D. G. Aliaga, and P. Krištof. 2010. “Inverse Procedural Modeling by Automatic Generation of L‐systems.” Computer Graphics Forum 29 (2): 665–74. https://doi.org/10.1111/j.1467-8659.2009.01636.x.

Burke, Donald S., Kenneth A. De Jong, John J. Grefenstette, Connie Loggia Ramsey, and Annie S. Wu. 1998. Putting More Genetics into Genetic Algorithms.

Arnold, D. B., and M. R. Sleep. 1980. “Uniform Random Generation of Balanced Parenthesis Strings.” ACM Trans. Program. Lang. Syst. 2 (1): 122–28. https://doi.org/10.1145/357084.357091.

Menzer, Fritz, and Christof Faller. 2010. “Unitary Matrix Design for Diffuse Jot Reverberators.”

Werner, Kurt James. 2020. Energy-Preserving Time-Varying Schroeder Allpass Filters.

Johnson, Tom. 1994. *Self-Similar Melodies*. Editions 75.

Mason, Stephanie, and Michael Saffle. 1994. “L-Systems, Melodies and Musical Structure.” Leonardo Music Journal 4: 31. https://doi.org/10.2307/1513178.

Jones, Kevin. 1989. “Generative Models in Computer-Assisted Musical Composition.” Contemporary Music Review 3 (1): 177–96. https://doi.org/10.1080/07494468900640121.

DuBois, Roger Luke. 2003. “Applications of Generative String-Substitution Systems in Computer Music.”

Manousakis, Stelios. 2006. “Musical L-Systems.”

Miranda, Eduardo Reck. 1995. “An Artificial Intelligence Approach to Sound Design.” Computer Music Journal 19 (2): 59. https://doi.org/10.2307/3680600.

Diaz-Jerez, Gustavo. 2011. “Composing with Melomics: Delving into the Computational World for Musical Inspiration.” Leonardo Music Journal 21 (December): 13–14. https://doi.org/10.1162/LMJ_a_00053.
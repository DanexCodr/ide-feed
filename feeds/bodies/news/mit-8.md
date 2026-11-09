RNA vaccines, which have been proven effective against Covid-19, are now being developed for many other diseases, including cancer. One of the drawbacks to these vaccines is that they require ultracold storage, but researchers from MIT have found a promising way to overcome that limitation.

With help from an AI algorithm, the researchers tweaked the formulation surrounding the lipid nanoparticles that are typically used to deliver mRNA vaccines, making the vaccines more heat-resistant. Using this approach, they formulated vaccines that could remain stable even when stored at room temperature for up to a year, or at nearly 100 degrees Fahrenheit for two months.

When Covid-19 vaccines carried by these particles were administered to mice, they generated just as strong an immune response as an RNA Covid-19 vaccine similar to one developed by Moderna. By using the AI algorithm to predict the optimal formulations for the particles, the researchers were able to cut down the number of experiments they needed to do, which rapidly sped up the development process.

“The real beauty of this algorithm is that we can use it with small data sets,” says Ana Jaklenec, a principal investigator in MIT’s Koch Institute for Integrative Cancer Research. “It’s really hard to run thousands of experiments, so this algorithm allows us to more easily achieve formulations with features that we want — in this case, stability.”

Jaklenec and Robert Langer, the David H. Koch Institute Professor, are the senior authors of the paper, which [appears today in *Nature Biotechnology*](https://www.nature.com/articles/s41587-026-03331-w). Graduate student Jinbi Tian and postdoc Khanh Tran are the lead authors of the paper.

**Stable vaccines**

RNA is a highly fragile molecule, so researchers stabilize it with lipid nanoparticles (LNPs) that protect the RNA from degradation and help it get into cells. However, these RNA-LNP vaccines still need to be kept cold (-20 to -80 degrees Celsius), which makes it difficult to ship them to regions that don’t have cold-storage facilities available.

Making these vaccines more heat-tolerant would not only enable them to be distributed more widely, but could also help researchers develop new vaccines that could be administered through novel methods such as microneedle patches. These patches contain hundreds of vaccine-filled microneedles, which dissolve when the patch is applied to the skin, releasing the vaccine.

To create more stable RNA vaccines, researchers have experimented with adding a variety of excipients — sugars, salts, or polymers — to the LNPs. Jaklenec and Langer recently developed polymer-stabilized LNPs that can withstand higher temperatures, but those LNPs were slightly different from the FDA-approved formulations that were used for the Moderna and Pfizer Covid-19 vaccines.

In their new paper, the researchers wanted to see if they could find a way to make those FDA-approved formulations more stable at high temperatures.

They began by reusing some of the excipients that had worked in their earlier efforts, but they were “really getting stuck,” Jaklenec says. “We were trying to use and screen excipients that we’ve previously used successfully to stabilize LNPs, but it just wasn’t working. It was really frustrating for the team.”

To speed up their progress, the researchers decided to try a machine-learning approach. Working with researchers at MIT’s Computer Science and Artificial Intelligence Lab (CSAIL), they developed an algorithm that can make predictions based on very small datasets.

“We’d used our algorithms for various automated experimental design applications before, but never on a biological problem like vaccine stability,” says Mina Konaković Luković, an assistant professor of electrical engineering and computer science in MIT’s Computer Science and Artificial Intelligence Laboratory (CSAIL), who is also an author of the paper. “It was surprising to see how quickly the algorithm converged on a stable formulation — getting there in just a handful of iterations, rather than the exhaustive search that would normally be required.”

The researchers used this algorithm to analyze nearly 50 FDA-approved excipients. For each excipient, the researchers first measured how well it stabilized RNA when incorporated into an LNP. They used these particles to deliver mRNA encoding a protein called firefly luciferase, which produces bioluminescence, into cells. By measuring how much light was emitted by the cells, the researchers could determine how effectively each excipient protected the mRNA.

The researchers chose five of the most promising excipients and used their AI algorithm to predict ratios of those excipients that would best stabilize LNPs similar to those used by Moderna. Based on those predictions, the researchers tested two formulations at a time in cells, fed those results back into the algorithm, and generated more predictions. After several rounds, they chose one formulation that appeared promising enough to test in animal studies.

This process took only a few weeks, much less than it would have taken without guidance from the AI algorithm.

“Before we implemented the AI algorithm, we spent several months testing different combinations and also doing the prescreening of all the excipients that we could find, but nothing would get us to 100 percent stability,” Tran says.

**Robust immune responses**

To test the heat resistance of their new LNP formulation, the researchers used the particles to package Covid-19 mRNA antigens, then dehydrated them using a process called vacuum drying. These particles were then stored at 37 degrees Celsius (98 degrees Fahrenheit) for two months, or at room temperature for one year. Mice that were vaccinated with these particles, even after long-term storage, showed equivalent immune responses to mice that received vaccines carried by LNPs similar to the original Moderna formulation.

The researchers also used their new heat-resistant formulation to create solid microneedle patches that could deliver a SARS-CoV-2 antigen. These patches generated an immune response similar to that produced by the injectable RNA vaccines.

“Our approach broadens the application of not only mRNA vaccines, but also therapeutics or advanced drug-delivery platforms like controlled-release particles or microneedle patches, which requires the formulation to either be in solid state or to be stable at higher temperature,” Tian says.

The researchers also showed that they could use their algorithm to stabilize other LNP formulations, including one similar to those used by Pfizer to deliver its Covid-19 vaccine. This formulation uses the same excipients as the one the MIT team developed for the Moderna LNP, but in a different ratio. For each LNP, once a heat-resistant formulation has been developed, it could be adapted to deliver any type of mRNA payload, the researchers say.

The research was, in part, funded by the Gates Foundation.
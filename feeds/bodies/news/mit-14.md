When an artificial intelligence image generator produces a portrait, whose work went into it? The question sits at the center of lawsuits, licensing deals, and proposed regulations worldwide. Artists want credit. Companies want clarity. Policymakers want a way to assign responsibility.

New work from a team of researchers at MIT's Computer Science and Artificial Intelligence Laboratory (CSAIL) suggests that for models trained on large datasets, the question may often have no answer. It's not that the tools for finding it are inadequate. The connection itself has disappeared.

The scientists identified a phenomenon they call attribution decay, where the more data a generative model is trained on, the less any individual training example matters to any particular output. It feels counterintuitive, but at sufficiently large scales, they find, you can often remove any single image from the training data, or every image by a given artist, or every photograph of a given person, and the generated sample doesn't change.

And if removing something changes nothing, the researchers argue, it can't be said to be responsible for anything.

"If you take away a piece of data and the output of the model doesn't change, then that piece of data didn't affect the output," says Zheng Dai SM ’21, PhD ’24, former MIT CSAIL researcher and lead author on the work. "So it doesn't make much sense to attribute the output to that piece of data. And if you then do this one at a time for every other piece of data and find that the output doesn’t change for any of them either, then it doesn't make much sense to attribute the output to any one of them."

"All previous methods were approximate," says MIT Professor David Gifford, who is an MIT CSAIL principal investigator. "They really could not absolutely show that deleting individual things did not change the output. This paper introduces the first method that is absolute. You're actually deleting the inputs and deleting all influences of the inputs. This is the first exact method for doing large-scale deletion efficiently and showing that the results don't change."

Dai and Gifford's project is described in an open-access [paper published today in *Nature Communications*](https://www.nature.com/articles/s41467-026-75667-5).

**The retraining problem**

Testing this idea directly meant answering a what-if question. What would this model have produced if it had never seen this particular image? Answering it honestly means retraining the model from scratch without that image, then doing it again for the next image, and the next. With millions of training examples, the math quickly becomes prohibitive, which is why prior work in the attribution field has relied on approximations that estimate a training example's influence, rather than actually removing it.

Their workaround is an architecture they built themselves, called a "diffusion ensemble." Instead of one monolithic model, it's made up of many smaller components, each trained on a different slice of the data. Want to know what the model would do without a particular image? Just switch off the parts that saw it. No retraining, no approximation. What's left is a true counterfactual model, not an estimate of one.

Of course, a clever architecture only matters if it still works as a generator. So the team put the ensembles head to head with 24 conventional diffusion models trained on the exact same data. The images came out looking about as good by standard measures.

One nice surprise in the numbers: The more training data, the better the ensembles held up against their single-model counterparts, a hint that they may actually be more data-efficient.

"When you have low amounts of data, they do very poorly," says Dai. "But if you have more data, it actually scales better compared to the vanilla diffusion model."

**Exploring a counterfactual universe**

With ablation working, the researchers could finally ask their question at scale. Take one generated image, then imagine every alternate version of it, each produced by removing a different piece of the training data. The team calls this the image's counterfactual universe. The distance between the original and its most different alternate, the counterfactual radius, captures the most that any single piece of training data could have mattered.

They trained 24 ensembles on datasets from 256 images to more than 160,000, pulled from seven public collections including CIFAR-10, CelebA, MetFaces, and ArtBench. The pattern was consistent: The bigger the training set, the smaller the radius, shrinking along an inverse power law. It held whether differences were measured pixel by pixel or by semantic meaning, with statistical significance both ways.

The team also stress-tested their own result. Maybe ablation itself was the culprit? They redid it the brute-force way at small scale, training 1,282 separate models, and the decay showed up anyway. Maybe bigger datasets just make each removal proportionally smaller? They pinned the removed fraction in place, and it persisted. Fixed epochs, text-prompted models, class-conditioned models, four similarity metrics — the finding survived everything.

**The privacy paradox**

The implications run in a direction that surprised the researchers themselves.

Gifford sees the finding as bearing directly on the legal question of whether model outputs are derivative works.

"One way to think about this is that these models are creative. They are not simply copying what they are fed, but creating brand new outputs. If those outputs have nothing to do with any individual piece of training data, that raises questions about fair use, about whether the outputs are themselves copyrightable as novel works, and about how authors get compensated when what comes out of a model isn't attributable to anything on the internet."

Gifford also notes that the work shows how to produce outputs that are guaranteed to be unattributable, a capability he frames as an obligation for the industry, rather than a loophole.

"In order for these companies to claim their outputs aren't derivative of the internet in a copyright-infringing way, they need to revise their models to take advantage of the advances in this work, so they can show they're not creating derivatives of individual people or items."

The work looks at diffusion models, now dominant in generating audiovisual media and prevalent in scientific applications including protein structure modeling and therapeutic discovery. Whether the same decay holds for the large language models at the center of the highest-profile copyright litigation is still an open question.

"If attribution worked, it would reliably tell us whether similarities between a model's output and a copyright-protected work are due to copying or coincidence," says James Grimmelmann, a law professor at Cornell Law School and Cornell Tech. "But this paper provides reason to think that attribution will fail for interesting models. Instead, technologists and courts will need to resort to other methods for assessing copying."

Dai and Gifford's work was supported by Schmidt Futures.
Across a [large range of scales and datasets](https://e-means.github.io/#validation), e-means reaches a test loss below Lloyd's at 25 epochs, in 1.2 to 3 epochs. Measured end to end, that is a 10–45× wall-clock reduction on GPU against the state-of-the-art Lloyd implementation (Flash-KMeans<sup>[[2]](https://e-means.github.io/#ref2)</sup>), and 8–15× on CPU against Faiss<sup>[[1]](https://e-means.github.io/#ref1)</sup>. Speed and quality usually trade against each other in k-means, while e-means achieves both better speed and loss.

![e-means against Lloyd’s k-means, in epochs, CPU time and GPU time](https://e-means.github.io/assets/emeans_vs_lloyd_readme_v9.png)

## The k-means problem

Given a fixed dataset of n points X = {x<sub>1</sub>, ..., x<sub>n</sub>} ⊂ R<sup>d</sup> and an integer k, the k-means problem is to find k centroids C = (c<sub>1</sub>, ..., c<sub>k</sub>) minimizing the mean squared distance between each point and its nearest centroid:

It's a static dataset, unlike codebook learning inside VQ-VAEs, where the distribution to cluster is constantly moving.

## The e-means project

The goal of e-means is to provide a modern optimization rule for the k-means problem. We started this project from the following observations:

For e-means, we chose to do mini-batch updates with exponential moving averages<sup>[[6]](https://e-means.github.io/#ref6)</sup>, which we found to be most efficient for the k-means problem. Contrary to previous mini-batch approaches, e-means requires no hyperparameter tuning because it automatically sets the batch size and step size with scaling laws (see [Automatic hyperparameter tuning with scaling laws](https://e-means.github.io/#scaling-laws)). In addition, e-means improves the initialization and the dead-cluster revival strategy, adds a cosine-scheduled decay rate, and introduces a finalization stage that reduces the training loss for a negligible runtime penalty at the end of training. e-means is highly parallelizable, and comes with specialized kernels that translate its algorithmic advantage into wall-clock speedups.

The centroid update rule is the central component of e-means. This section aims to provide an overview of update rules for k-means clustering. All methods maintain, for each cluster j, a sum S<sub>j</sub> and a count N<sub>j</sub> of the points assigned to it, and take the centroid as their ratio:

They differ only in how S<sub>j</sub> and N<sub>j</sub> are updated. Below, s<sub>j</sub> and n<sub>j</sub> denote the sum and the count of the points in the current batch that are assigned to cluster j (both zero if none are).

**Lloyd’s algorithm**<sup>[[7]](https://e-means.github.io/#ref7)</sup> assigns every point to its nearest centroid and recomputes the statistics from scratch, using the full dataset as the batch:

so c<sub>j</sub> is the exact mean of the points currently assigned to it. Each update costs one full pass over the data, and the procedure is repeated a fixed number of times (typically 20 to 50 iterations).

**MacQueen’s update**<sup>[[3]](https://e-means.github.io/#ref3)</sup> accumulates the statistics without ever discarding them:

so c<sub>j</sub> is the uniform mean of every point assigned to cluster j since the start of training, including points assigned under earlier, possibly poor, centroid positions. This was later partially addressed by Staleness-Reduction Mini-Batch K-Means<sup>[[8]](https://e-means.github.io/#ref8)</sup>, a hybrid method between k-means and MacQueen. They obtained important speedups, but only on very low numbers of clusters.

**e-means** works on mini-batches and replaces this sum with an exponential moving average:

so older assignments are forgotten at rate α, and the centroid tracks recent assignments rather than the whole history. This update rule is typically used for moving distributions, hence their adoption for training VQ-VAEs<sup>[[6]](https://e-means.github.io/#ref6)</sup>. What we found is that it’s also extremely efficient for static datasets if it’s combined with e-means’ other components, and hyperparameters are properly tuned.

The e-means project started from previous work at Meta FAIR by Hugo Touvron and Hervé Jégou, who had found that mini-batch k-means by gradient descent could beat Lloyd’s algorithm. While I could reproduce these results, I found that the performance of gradient-descent based centroid updates is unstable at large learning rates, unlike exponential moving average updates. I suspect that is because EMA updates guarantee that the centroid is always in the convex hull of points assigned to it, while gradient descent updates may overshoot past that hull.

In order to achieve the lowest loss at a fixed number of epochs, we chose exponential moving average updates, hence the name e-means for our method.

If you set the batch to the full dataset, B = n, *and* α = 1, then N<sub>j</sub> and S<sub>j</sub> become exactly the count and sum of the whole cluster, so one e-means iteration becomes exactly one Lloyd iteration. Lloyd is an extreme case of e-means without cosine scheduling on the learning rate. However, our hyperparameter search found that this extreme setting is highly suboptimal, which explains why e-means largely outperforms Lloyd. Below, the loss is measured for every batch size B and step α: Lloyd lands in a corner, well outside the region where the loss is lowest.

This hyperparameter study motivated us to derive scaling laws that automatically pick the optimal batch size B and step size α.

To better understand why e-means reaches better losses than Lloyd at convergence, we plotted a few trainings on toy datasets to evaluate their ability to escape local minima. Repeating trainings over 200 seeds, we found that e-means is much less likely to fall in pathological configurations compared to Lloyd.

Our explanation for that is that mini-batches provide more noisy updates that are more likely to explore the optimization landscape and escape local minima. Lloyd, with its always decreasing loss, is more likely to exploit found local minima and never escape them.

## Automatic hyperparameter tuning with scaling laws

An essential property of e-means is that practitioners don't need to set any additional hyperparameter compared to Lloyd's algorithm. We fitted two scaling laws to set the batch size `B` and step size α<sub>0</sub> from any problem's characteristics `(n, k, T)`, and found them to exhibit strong generalization on unseen datasets and problem scales.

| law | constant | exponent of | regret, held-out datasets | regret, held-out size | R² |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k | B | n | T |  |  |  |  |  |
| step α<sub>0</sub> | 0.824 | −0.46 | 0.90 | −0.45 | −0.11 | 0.07% | 0.07% | 0.95 |
| batch B, default | 0.035 | 0.13 | n/a | 0.88 | 0.81 | 0.19% | 0.20% | 0.96 |
| batch B, quality law | 0.0044 | 0.13 | n/a | 0.88 | 0.81 | 0.07% | 0.06% | n/a |

We propose two equations to choose the batch, the default law and the quality law. The “quality law” trades off throughput for better clustering quality against the “default” law. Below we plot the training data for our scaling laws: validation MSE against step size α<sub>0</sub> (left) and batch size B (right).

![The two scaling laws fit on deep1b](https://e-means.github.io/assets/paper_laws.svg)

The main issue with mini-batch k-means is that it is prone to “dead” clusters, centroids that end up with zero assigned points during optimization. This reduces the effective size of the codebook, which is especially problematic for the large codebooks increasingly used today.

A common mitigation is to reinitialize clusters that fall below a certain size threshold, as done in EnCodec<sup>[[10]](https://e-means.github.io/#ref10)</sup>, where dead centroids are simply replaced by random samples drawn from the incoming batch. While this helps, it does not fully resolve the issue. Instead of sampling arbitrary points from the batch, we revive dead clusters by splitting large, existing ones: we sample an active cluster with probability proportional to its size and split it into two. We found this approach, adapted from Faiss k-means, to be significantly more effective at eliminating dead clusters and preserving codebook capacity.

| dataset | revival policy | dead clusters | of codebook | imbalance | test MSE |
| --- | --- | --- | --- | --- | --- |
| DEEP | **proportional split** | **47** | **0.3%** | **1.194** | **0.38762** |
| resample from batch (EnCodec) | 2,343 | 14.3% | 1.423 | 0.39124 |  |
| off | 4,313 | 26.3% | 1.647 | 0.39448 |  |
| SIFT | **proportional split** | **10** | **0.1%** | **1.186** | **0.19623** |
| resample from batch (EnCodec) | 750 | 4.6% | 1.233 | 0.19684 |  |
| off | 2,080 | 12.7% | 1.404 | 0.19797 |  |

We validated e-means on 24 different embedding and synthetic datasets and configurations (see [paper](https://arxiv.org/abs/2611.09501)). For the video we ran 234 configurations of e-means against k-means (16 datasets, 100k to 100M points): explore every curve in the [results map](https://e-means.github.io/results-map.html).
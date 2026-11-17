In my [previous blog post on what’s going on in MySQL Server development](https://blogs.oracle.com/mysql/mysql-development-as-it-happens), I gave an overview of how the MySQL development process has been changing this year.

- We announced that MySQL development would move into the public mysql-server repository on GitHub.
- We invited contributors from across the MySQL community to join us.
- We organized two Contributor Summits where Oracle engineers and MySQL community members developed the roadmap categories, proposed projects for the MySQL roadmap, and started working together on some of those projects.
- Above all, by early July, engineers were already working hard to deliver what really matters: MySQL 9.7 LTS and MySQL 26.7 (innovation release) with a significant shift in focus toward the open source MySQL Community Edition.

Today, I want to dive deeper into one of the four strategic focus areas: AI & Cloud, with a closer look at VECTOR INDEX support.

## Project News

Before doing so, I’d like to share some general project news from the weeks and months since my previous blog post.

To help both project contributors and interested observers stay on top of everything that happens in the project, we started publishing a weekly newsletter. Its main feature is a comprehensive list of links to every GitHub issue and pull request that was active during the week.

![](https://blogs.oracle.com/mysql/wp-content/uploads/sites/102/2026/11/last-week-in-mysql.png)

In [the GitHub repo](https://github.com/mysql/mysql-server), we have hooked up the good old MySQL Test Run, formatter, and of course, [the indispensable OCA bot](https://github.com/mysql/mysql-community/discussions/135)! Work continues on preparing the public mysql-server repository so that we can move all open source MySQL development there. This is a big change for us, even if most of the work involved is not visible from the outside. Essentially, the flow of patches between different flavors and versions of MySQL will be completely reversed, and the public MySQL Community Edition repository will be the new upstream for all development.

## What are vectors and how would you index one?

So, let’s now dive into our main topic for today, vector indexes. If you already know what vectors are, you can skip ahead. But let me start with a quick backgrounder:

In school, my math teacher told me that vectors are arrows. More specifically, they have a length and a direction. Maybe so, but if you were also taught this, you can forget all that. Instead, plain and simple, a vector is a list of numbers. It’s like one INT or FLOAT, but instead you have more than one, and they go together, the CPU can process them together, and so on. A typical mathematical notation could be:

example_vector = v = (1.0,  4.12,  0.0 , 0.23 , 1.23)

If you want to get really mathematical, you can also write your vectors as a column, with the numbers on top of each other. For a blog post like this, I think it is easier to stick with the horizontal way.

And sometimes, it might be useful to think of vectors as points in space. In fact, a vector with two elements:

p = (50.848448, 4.353823)

…could represent the latitude and longitude of a position on earth. And ***that*** is the example where a vector starts looking like an arrow. It’s an arrow pointing toward a well known position in Europe. More precisely, it is a location in Belgium where many of us have had a beer or two.

So p above is an example of a vector in 2-dimensional space. We could also have a vector with three numbers and think of it as a point in a 3-dimensional space. Then you could more accurately convey the information which floor in the building  you are.

The vectors used in AI computation will have hundreds or even thousands of numbers each, and we would then say they have N dimensions. It is hard to imagine what more than 3 dimensions look like, but the related math is not that hard to grasp: You just think of a function like “*distance”* and you can extend what you’d do in 2-3 dimensions and do it with a thousand numbers instead.

So in a way, you could say MySQL already has vector support since many years ago in terms of [spatial indexes](https://dev.mysql.com/doc/refman/8.4/en/creating-spatial-indexes.html). (Ignoring here all the work spatial indexes have to do to deal with the fact that the world is not actually a flat surface, but is curved.) Now we just want to do the same kind of things with N dimensions instead of two!

### Vectors in AI

So why are vectors used in Artificial Intelligence? Why are points in space suddenly so important? The short answer is that in AI we encode everything into numbers, perform some simple but powerful computations on those numbers, and out the other end comes something useful.

For example, a typical use case would be an AI that wants to process text – like this blog post – perhaps. To efficiently do the math on blog posts, we create one vector for each blog post and we let the numbers in the vector represent the occurrence of words. So for example, the text until this point in this blog post could be represented by a vector:

blog=(18,26,26,8,8,7,7,7,7,24,16,7,8,23,14,6,15,11,19,10,7,11,6,10,12, …)

…representing counts of the words

(MySQL , a , and , are , be ,  blog , development , for , have , in , is , like , numbers ,

of , on , post , that , this , to , vector , vectors , we , will , with , you …)

…that appeared in this post until this point.

And now if we think of those vectors as points in a space where each word is a dimension, then that creates a space with all the blog posts in the world. Our vector has now become an ***“embedding”***, since it is embedded in the space where it has some meaning to our AI model. Btw in this simple example, the words are the ***“tokens”,*** ****but that is not always the case.

And even if we’ve simplified blog posts to just a “bag of words” without much meaning beyond that, it is still an intuitive assumption that if two vectors are close to each other in this space, there’s probably a lot of common between the actual blog  posts those vectors represent.

In this example, there are probably lots of blog posts written about vectors, MySQL and AI. And on the other hand, there are even more blog posts written about beer and Belgium. Since this post mentions both, in the universe of blog posts, it would be located somewhere between those two very different groups of topics people could write about.

### What does a database need to do with vectors?

In the above example, our vectors are straightforward encodings of each blog post. In reality, the vectors used by an AI model, would derive their values from a training process that the model goes through. But since this post is about vectors and databases, we will stop here. As with many other applications, the actual compute layer is none of our business, we just need to store vectors and give them back to the AI when it needs them. And vectors are just numbers in N dimensions.

And one more thing we need to be able to handle is the concept of ***distance*****.** We need to be able to say whether two vectors are close or far apart, which usually translates to them being “similar” or different. In the 3D world that we live our lives in, we use so called  Euclidian Distance:

_________   
      d = \/ x <sup>2</sup> +y <sup>2</sup>

or          _______________   
      d = \/ x <sup>2</sup> +y <sup>2</sup> +z<sup>2</sup>

It turns out that this can be useful also in N dimensions. You just add more variables after z there. But there are also other distance functions used. In the end it doesn’t matter so much what the distance function is, the indexing and searching works pretty much same with each of them.

So when an AI is fetching vectors from a database, what it usually wants is to fetch all the other vectors close to some given point. Those nearby vectors represent all the knowledge that we have about and around a given topic – represented by the input vector. For example, a database query might need to fetch all the blog post that are “similar” to the sentence ***“Are you going to the Fosdem beer event later tonight?”***

To do that it would again create a bag of words of that sentence. So using the same encoding as we did above:

question=(0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1, …1,…)

…representing counts of the words

(…, are , …, to , …, you …,beer, …)

As you can see, we can now search for vectors “near” this vector representing the question, and we would find other texts that had the same words in them. What “near” exactly means here, depends on the distance function used. Euclidean distance could work, but that would cause most of the results also to be of similar length. For example the Hamming distance is only counting 1 or 0 in each dimension. If a word is repeated many times, it still only counts as 1. In practice so called Cosine distance is used a lot and will be implemented also in our project.

The gold standard in the requirements section is “hybrid search”, meaning the ability to use both a vector search parameter along with all the other query predicates you already use in a full featured SQL database. This might mean that the query optimizer is able to consider the use of a vector index alongside choosing between all the other indexes in your database. In the extreme it could mean using an index structure that itself embeds and traverses both vectors, number values and words – kind of like a compound index is often more efficient than a single column index.

To summarize all of what we learned so far, retrieving vectors for an AI model is basically the SQL query:

… ORDER BY *distance([input point p], [vector column v])* LIMIT *k*

The only gotcha is that the vectors and their distances are in N dimensional space.

### kNN and ANN and other terminology

The simplest formulation of the problem is therefore to return the ***k Nearest Neighbors*** to p. A naive implementation can do that in O(N) time, that is searching once over the entire data set. To improve on that, algorithms like [K-D trees](https://en.wikipedia.org/wiki/K-d_tree) and [R-trees](https://en.wikipedia.org/wiki/R%2A-tree) exist. But unfortunately these only help in low dimensions, like the 2D and 3D spatial indexes.

But a much more powerful and straightforward optimization comes from the realization that often it is the case that we don’t care about the exactly correct answer to the query. Maybe we want to get like 1000 of the vectors in the area of interest, but it is entirely irrelevant whether the last vectors returned are actually the 999th point or 1001st point from the center point. Therefore mostly when we talk about vector search, or vector index, we are looking at various ***Approximate Nearest Neighbor*** algorithms, or ***ANN*** for short. At first sight this might sound like a terrible idea, since we are used to databases being very precise and accurate in terms of not losing data when writing and returning  precise and correct results when reading. But it turns out this is less important with most AI use cases, and if you think about it, this kind of lossy and fuzzy recall is how your human brain works too. (…that AI is mimicking.)

Finally, having stepped onto the path of approximate answers, many vector index implementations also apply ***quantization*** to reduce the memory space needed for the index. For example a 32-bit floating point value could be indexed with just 16 bit precision, even 8 bits is common. Having the number of bits from 32 to 16, will halve the memory space needed while the accuracy is mostly unharmed, and mostly impacting the furthest points, which are the least important in the result set anyway. Similarly, we may reduce the ***dimensionality*** **of the vectors before indexing them. It turns out that often some elements in the vector are much more important than others, so while computing the distances and indexing the vectors, we may simply ignore the dimensions that are found to be insignificant. (As a simple example, because they are always zero or close to zero.)

### HNSW

An early and widely used algorithm is called [***Hierarchical Navigable Small World***](https://en.wikipedia.org/wiki/Hierarchical_navigable_small_world). Essentially it is the baseline that newer algorithms need to beat.

The main idea here is that vectors are stored in a graph, with edges connecting them to their closest neighbors. An ANN search now simply finds a starting point close to the input vector, and then does a graph traversal to find k nearest points.

But HNSW is not just a graph traversal, rather it works in a hierarchy of layers. A small percentage of vector points are sampled from the full data set. A query will start with searching only these nodes for the nearest neighbor. Once found, the graph traversal starts normally. But the traversal now considers both the other nodes in layer 1 as well as nodes  in layer 2. Chances are that the distance to nodes in layer 2 is shorter than to other nodes in the sparsely populated layer 1. Again, from the nodes in layer 2 the traversal continues, probably mostly down to the next layer until it finds the layer that embeds all the nodes.

The real world analogy here is like driving a car to an address in a nearby city. You would first pick the right highway to arrive in the right city. Then you’d take the right off ramp to a normal road. Finally you enter the residential area where you have to drive slowly until you reach your destination.

The computer science analogy is basically skip lists, but for graphs.

HNSW is often consumed through the popular [HNSWlib](https://hnswlib.com/). For example pgvector, Lucene, ClickHouse, DuckDB, all support some implementation of HNSW indexes.

### InVerted File Index (IVF)

The other main family of vector indexing is known as ***InVerted File Index***, and variations based on it*.* These algorithms will first partition the vectors into clusters, typically using [k-means clustering](https://en.wikipedia.org/wiki/K-means_clustering). Which, btw, is not at all the same as [k Nearest Neighbor algorithm](https://en.wikipedia.org/wiki/K-nearest_neighbors_algorithm)! The actual query will then first decide which cluster is closest to the input vector, then process data in that cluster to find the closest k nodes.

### Comparing HNSW and IVF on a high level

In practical outcomes, now that we know how HNSW and IVF differ on the level of data structure and algorithms, we can also derive an understanding of how and why they might differ in an actual implementation. Being a graph-oriented structure, HNSW has the advantage that an index scan is able to traverse the index pretty arbitrarily, as far and wide as is needed.

But such a graph traversal might not be the most efficient approach in all cases. And, as also tends to be the case with graph data structures, HNSW tends to work best when it fits in memory.

IVF on the other hand is a quite compact and straightforward structure: You move your origin into an area of the n-dimensional space, where there is a high concentration of vectors. And from there, you simply sweep an area of the space that is defined by the users query. For example the typical ***WHERE DISTANCE(point, col) < 0.7*** defines an n-dimensional sphere.

The weakness of IVF on the other hand is that it really splits the vectors into these different clusters, or partitions. There is no easy way to query for the data points that belong partly to another IVF cluster. Therefore  results from querying an IVF index might sometimes be slightly inaccurate, if the query happened to be in a sparse area of the space at the edge of one partition.

### ScaNN

An interesting algorithm in that last category is [ScaNN](https://research.google/blog/announcing-scann-efficient-vector-similarity-search/), developed by a team at Google. By focusing on how to optimally quantize the vectors such that they maximize compression rate yet minimize the error resulting from it. Reports suggest up to 4-8 x speed improvements across [different benchmarks](https://ann-benchmarks.com/index.html).

This library has now been open sourced by Google and it is at the heart of [a new pull request](https://github.com/mysql/mysql-server/pull/759) to be included in MySQL. Of course, that is only after it will be subjected to rigorous review and benchmarking and compared to all the other alternatives. But the academic literature is at least looking promising in that regard!

### Vamana

The most recent participant in the party is Intel, who [proposed their Vamana](https://github.com/mysql/mysql-community/issues/116) indexing algorithm. Vamana belongs to the graph-like family of indexes, so we are essentially seeing IVF and ScaNN being compared to HNSW and Vamana. Potentially MySQL will include all four of these libraries, or at least provide an API that allows to plug in whichever is your favorite vector indexing library.

## Building a vector index in MySQL

If you were to [read the GitHub discussions](https://github.com/orgs/mysql/projects/5) of this project, it will mostly be a mix of SQL syntax design, math, InnoDB internals, and benchmarking. Low level and emotionless engineering stuff.

If you don’t pay attention, you might not immediately recognize, that the project to add vector indexing to InnoDB actually is some kind of family reunion of all the peak hype technologies of the past 50 years! To build vector search into the most popular open source database MySQL,  at this moment the project is mostly focused on the ScaNN library, recently open sourced by Google’s Cloud SQL team. Which the InnoDB team at Oracle is now integrating and benchmarking.

Amazon (AWS) has also been actively involved, in fact it was Hugo Wen’s presentation back in the May Contributor Summit that started the project. And for the Contributor Summit this week, we have Intel and Percona presenting contributions they would like to add to the pot!

And in true open source fashion, we have one lonely open source hacker from Istanbul – *Alkin “Born to sail, forced to work on databases” Tezuysal* – outrunning all of the above with his [MyVector plugin,](https://github.com/askdba/myvector) already in production since March! More on MyVector later.

The above is a typical example of what happens to many popular open source projects as they scale: Where once upon a time, MySQL was known as the small and simple database that was good enough… Now it has become the database equivalent of the Monaco Grand Prix, where everyone wants to be seen, and the best engines are pitted against each other to find out who’s is the fastest. In other words, a key consideration for the developers working on the project has been to invest in a modular architecture that can be adapted to the different libraries on offer, and analyzing to find the best possible alternative for MySQL users, while at the same time there of course is a desire to remain true to your roots and release something that is simple, easy to use and relatively timely, without falling into the trap of over analyzing and over engineering. Yes it’s a bit of a first world problem, but worth mentioning, and MySQL is by no means unique in dealing with such challenges in scaling the project.

Testing the different types of algorithms is just half of the landscape. Another discussion has been [whether the index should be stored](https://github.com/mysql/mysql-community/discussions/6) as an InnoDB table linked to the main table that it is an index for (aka “sub-table”) or whether it should rather be built using the InnoDB secondary index page format. The latter sounds intuitively more “proper”, but it turns out it might require much more work on delicate areas like locking and visibility.

Perhaps the most interesting discussions from a user point of view are the tickets with the discussions about the syntax used to [CREATE VECTOR INDEX](https://github.com/mysql/mysql-server/issues/702) and then [SELECT](https://github.com/mysql/mysql-server/issues/751) vectors out of that index.

The work is underway. [You can follow discussions between the participating engineers at this project board](https://github.com/orgs/mysql/projects/5/views/1?pane=issue&itemId=206625345).

## MyVector and other plugin implementations

While the above contributors have agreed to create a native index type in MySQL core, more precisely as an InnoDB secondary index or a sub-table, there’s also [MyVector](https://github.com/askdba/myvector)!

Created by Alkin Tezuysal, MyVector is a MySQL plugin and User Defined Function. This is a very relevant topic now, when we are focusing on inviting more contributions from everyone in the MySQL community. Plugins have the nice property that anyone can create one, and anyone can also use one, without needing to ask for permission from a person with committer status, or worse, a manager, in the MySQL organization. We will return to this topic of 3rd party extensibility in a separate blog post soon!

MyVector supports precisely HNSW and IVF, and also supports both Approximate and Exact kNN search, several distance functions, and automatic index maintenance when the base data changes is triggered by observing the binlog.

MyVector has one very important advantage over the native index project: It is available, and you can download and try it out immediately if you want.

Even if the InnoDB team is building native vector support into the InnoDB core, there is nothing stopping the community from also implementing alternative algorithms. Especially something as well known as HNSW. This is a perfect example of using the plugin and component frameworks for extending MySQL with new features.  Extending MySQL, and the developer community, in a modular and scalable way, is a key area that current work is focused on, and that is what we will talk about in the next blog post in this series.

Of course, you wouldn’t expect a popular open source project to have only one plugin for vector search? No, of course not. There are at least five more, such as:

## Conclusions

The MySQL Community is really coming together and rallying around the project to add VECTOR index support in InnoDB. With four (4) state of the art algorithms (ScaNN, IVF, HNSW, Vamana) on the table, we are faced with the open source equivalent of a first world problem: Should we organize some kind of benchmarking or other trials, to find the best one and pick a single winner. Or should we create a pluggable API through which all of these four, and also others, can be used and exchanged, and perhaps in the end the users will tell us which one they prefer. How sophisticated do we want to get with hybrid search? Follow this channel for answers to those questions and more.

In the next post, I will tell you about the MySQL Component Framework, and also more generally share discussions and thoughts about extensibility of the MySQL Core server.
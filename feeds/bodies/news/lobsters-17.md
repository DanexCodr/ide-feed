Big O notation is a lie. Well, okay, it's a simplification that lies by omission.

Can O(√n) scale better than O(log n)? Can a disk-based algorithm outperform an in-RAM data structure? Yes, and yes.

![AVL in RAM vs DiskArray on disk](https://www.bitflux.ai/pics/memory_is_slow_part3/tldr.png)

Scaled to 2 billion nodes, the AVL binary tree needs 144 GiB of RAM. DiskArray keeps its data on 8 NVMe drives and uses 264 MiB of RAM, but it's still faster at everything.

## Why a Part 3

[Part 1](https://www.bitflux.ai/blog/memory-is-slow-part1/) showed that computers are getting wider, not faster, and that PCIe bandwidth is outpacing DRAM bandwidth.

[Part 2](https://www.bitflux.ai/blog/memory-is-slow-part2/) showed that streaming from disk can beat streaming from the page cache.

[Part 2.5](https://www.bitflux.ai/blog/memory-is-slow-part2-5/) showed that with the right hardware and software, streaming from disk can beat a buffer in DRAM.
So far I've shown how a sequential read from NVMe is fast, which is a cool trick but not controversial enough.

I'm getting worried people still aren't getting the point.

The point is that our intuitions about computer performance are all wrong.

So this time we're going to show how an on-disk data structure doing random reads and writes to disk is faster than an in-RAM data structure.  To make it worse, computer science textbook Big O notation says the on-disk algorithm is going to scale worse than the in-RAM algorithm.

## The rig

Same old used box as [Part 2.5](https://www.bitflux.ai/blog/memory-is-slow-part2-5/): a 24-core Xeon Platinum 8260 with 35.75 MiB of L3 and 192 GiB of DDR4, and 8 Samsung PM983 NVMe drives over NVMe-oF on four 100 Gb InfiniBand links.

## The task

Keep a sorted set of 8-byte keys, and support four transactions on it:

- search(key): is this key in the set?
- at(i): what's the i-th smallest key? The median, the 99th percentile, page 3 of the results.
- insert(key)
- delete(key)

That's the core of a database index, an order book, a leaderboard, a time-series store.

### The sorted array

Let's walk through the algorithm selection by first principles and childlike wonder.

The simplest solution is an array of keys, kept in order.

![Sorted array: search](https://www.bitflux.ai/pics/memory_is_slow_part3/sorted_search.png)

`search(key)` is a binary search. Look at the middle, throw away the half the key can't be in, and repeat. 16 keys take 3 or 4 hops. A billion takes about 30. O(log n).

![Sorted array: at](https://www.bitflux.ai/pics/memory_is_slow_part3/sorted_at.png)

`at(i)` doesn't search at all. The i-th smallest key is just `array[i]`, at a fixed offset from the start. One access. O(1). You can't beat that.

Then you need to change it.

![Sorted array: insert](https://www.bitflux.ai/pics/memory_is_slow_part3/sorted_insert.png)

To insert, you have to make room. Everything after the new key moves over one slot to open a gap, then the new key goes in the gap.

![Sorted array: delete](https://www.bitflux.ai/pics/memory_is_slow_part3/sorted_delete.png)

Delete is the same in reverse. Take the key out, then everything after it moves over to close the gap.

Either way, on average, half the array moves, every single time. It's a `memmove`, about the most efficient thing a CPU can do with memory, but it's still O(n). At 4M nodes, every insert moves about 16 MiB. At a billion nodes it would be 4 GiB per insert. The array also has to be one contiguous block, so growing it means allocating a bigger one and copying everything over.

|  | search() | at() | insert() | delete() |
| --- | --- | --- | --- | --- |
| Sorted Array | O(log n) | O(1) | O(n) | O(n) |

### The linked list

The textbook fix for "insert moves everything" is the linked list.

![Linked list](https://www.bitflux.ai/pics/memory_is_slow_part3/linked_list.png)

Each node holds a key and a pointer to the next node. To insert, you change two pointers. Nothing moves.

But to insert 21 you first have to find where 21 goes, and the only way to find anything in a linked list is to start at the head and follow the pointers one at a time. Search is O(n). `at(i)` is O(n). Insert and delete are O(1) once you're in the right place, and O(n) to get there.

|  | search() | at() | insert() | delete() |
| --- | --- | --- | --- | --- |
| Sorted Array | O(log n) | O(1) | O(n) | O(n) |
| Linked List | O(n) | O(n) | O(n) | O(n) |

Adding a node is cheap, but finding where to insert it is really expensive. So this doesn't solve our problem.

### The binary tree

Use the pointers to branch out instead of to line up, and you get a binary search tree.

![Binary search tree](https://www.bitflux.ai/pics/memory_is_slow_part3/binary_tree.png)

Smaller keys go left, bigger keys go right. Search walks down from the top, throwing away half the tree at each step, just like binary search on the sorted array. Insert walks down the same way and hangs the new node off the bottom, just like the linked list. Nothing moves. Keep a count of the nodes under each node and `at(i)` is a walk down too.

On paper it's the best of both: log n for everything.

### The AVL tree

In practice a plain binary tree has a problem. Its shape depends on the order you insert things.
Insert keys in sorted order and every new node goes to the right of the last one.  It would perform like a linked list.

![Unbalanced tree vs AVL](https://www.bitflux.ai/pics/memory_is_slow_part3/avl.png)

The AVL tree fixes this: after each insert or delete it checks the heights of the two sides and, if they're off by more than one, rotates a few nodes to rebalance. The tree stays about log₂ n deep no matter what.

But this isn't free; there is overhead to implement the tree. Every node is its own allocation with a key, two pointers, a balance factor, and a count. That's a lot of bookkeeping for an 8-byte key: 72 bytes of RAM per key, where the sorted array needs 8. The biggest sorted array I ran, 4M nodes, is 32 MiB of RAM. The same 4M nodes in the AVL tree take 288 MiB. At 2G nodes the AVL tree used 144 GiB of RAM.

|  | search() | at() | insert() | delete() | RAM per key | 2G nodes |
| --- | --- | --- | --- | --- | --- | --- |
| Sorted Array | O(log n) | O(1) | O(n) | O(n) | 8 B | 16 GiB |
| AVL Tree | O(log n) | O(log n) | O(log n) | O(log n) | 72 B | 144 GiB |

### Sorted array vs AVL

Let's look at how things scale and compare that to Big O predictions.

![Sorted array vs AVL from 2K to 4M nodes](https://www.bitflux.ai/pics/memory_is_slow_part3/classic.png)

At first glance, it looks like Big O gets the ranking right.  The sorted array's performance for insert and delete falls off a cliff while the search and at() performance degrades more slowly.  The AVL tree performance degrades slowly as predicted.

## DiskArray

The AVL tree solves the insert and delete problem but costs a lot of overhead that shows up in search and at() performance as well as extra RAM. The sorted array has a lot going for it: everything is in order, in one place, with no pointers to chase and no overhead. Its only problem is that an insert has to move half the array. Let's try a more brute-force solution to insert and delete.

If we cut the array into pieces we could contain the areas affected by inserts and deletes. Our DiskArray data structure splits the sorted keys into small extents. A small index says which extent holds which range of keys. To insert, find the extent with the index, then do a sorted-array insert inside that one extent. You only ever move part of the extent, never the whole list.

Then, because we're making a point, we can put the extents on disk too.  That way we only need the index in RAM with a small buffer pool to handle the IO for in-flight and active extents.

![DiskArray: the index in RAM, the extents on disk](https://www.bitflux.ai/pics/memory_is_slow_part3/diskarray.png)

The design decisions:

- An extent is one 4 KiB block. A convenient choice is 512 keys x 8 bytes. That's the unit an NVMe drive moves anyway, so a lookup or an insert is exactly one block read, or one read and one write.
- Only the index lives in RAM. Per extent, the index keeps its smallest key, largest key, and count, in directory blocks of 4096 entries, with one small top-level array over the directory blocks. That's about 44 bytes of RAM for every 4 KiB of data. At 64G nodes the index is 7.5 GiB, for 512 GiB of keys. RAM goes to the part that's worth having in RAM.
- Room to grow. Extents and directory blocks are left part empty, so most inserts don't split anything. When an extent does fill up and split, only the entries inside its own directory block shift, never the whole index.
- Lots of transactions in flight. Transactions are queued 2048 at a time. Each is looked up in the index when it's queued, so the drives see thousands of 4 KiB reads at once, spread over 28 io_uring workers and 8 drives.

### The Big O of DiskArray

A textbook answer for this kind of structure depends on your assumptions.  Extent size is a variable parameter.  It could be as bad as O(√n) for insert and delete if we scale the extents with n. However, in practice, given the hardware constraints, I sized the extents to what the disks want and fixed them: 512-key extents because that's one 4 KiB disk block, 4096-entry directory blocks so a split only ever shifts a few tens of KiB. Most of the time an insert is effectively one 4 KiB read, one 4 KiB write, and a log n search of the index in RAM.  But occasionally it has to edit a directory block.  The extent, directory, and even I/O introduce constants that are significant factors in the math for the realistic scales we'll be working in.

> **Full Disclosure:** if you look at the code you'll notice the top-level index that points to directory blocks is growing with n.  I planned to make that split into blocks as well, extents all the way up the tree.  But I didn't get around to it.  So *technically* there is a corner case that is O(n).  With my current settings a second tier would kick in at around 8G nodes. So in practice the O(n) means that, on average once every couple hundred thousand inserts, a directory block splits and the top level has to memmove() up to about 1.4 MiB and rebuild its count tree. That's noise next to the drive I/O.  If I did add a recursive index tree as planned, then I think we're officially just a B-tree variant and are for sure O(log n).

To simplify, I'm just going to say as an algorithm it scales as bad as O(√n) and as good as O(log n).  If that's not a reasonable argument, I'm sorry.  I majored in Electrical Engineering, not Computer Science, so I don't know the theory as well as I do the reality.

|  | search() | at() | insert() | delete() |
| --- | --- | --- | --- | --- |
| Sorted Array | O(log n) | O(1) | O(n) | O(n) |
| AVL Tree | O(log n) | O(log n) | O(log n) | O(log n) |
| DiskArray | O(log n) | O(log n) | O(√n) → O(log n) | O(√n) → O(log n) |

Big O says AVL wins or at least ties.  In-RAM vs On-Disk says AVL wins.

No way DiskArray wins, right?

### AVL vs DiskArray

I want to compare DiskArray to AVL in DRAM not L3.  512K nodes × 72 B is ~36 MiB which is the L3 size.  So we'll compare up to 512K nodes and more than 512K nodes in separate graphs.

![AVL vs DiskArray while AVL fits in L3, 2K to 512K nodes](https://www.bitflux.ai/pics/memory_is_slow_part3/duel_cache.png)

AVL wins everything here: about 10x faster on search at 2K nodes, still almost 2x at 512K. Every pointer hop is a cache hit, and cache hits are cheap. DiskArray is flat at around 2M searches/s, because it's paying for machinery it doesn't need yet: queues, workers, a buffer pool. Its data still fits in the 24 MiB buffer pool, so the drives aren't even being read.

Nevertheless, even in cache, AVL performance is scaling down fast. Search goes from 19.6M/s at 2K nodes to 4.0M/s at 512K, about 5x slower.

Now let's compare them as we scale past 512K nodes:

![AVL vs DiskArray once AVL is in DRAM, 512K to 64G nodes](https://www.bitflux.ai/pics/memory_is_slow_part3/duel_dram.png)

DiskArray scales far better than AVL.

From 16M nodes up, the disk-based structure beats the in-RAM tree at everything, all the way to where AVL ran out of RAM at 2G nodes. DiskArray kept going to 64G.

### How is DiskArray winning?

Let's compare what happens during an insert() at 2G nodes.

![Everything one insert touches at 2G nodes](https://www.bitflux.ai/pics/memory_is_slow_part3/insert_bytes.png)

This doesn't help at first glance.  In fact it makes it look like DiskArray is doing way more work.

It depends what you count, and every way of counting it is interesting.

![Four ways to count one insert](https://www.bitflux.ai/pics/memory_is_slow_part3/counting.png)

Two definitions run through all of this. **Used** is the bytes an algorithm deliberately reads, plus the bytes it deliberately writes. **Moved** is what the hardware actually transfers: DRAM and the L3/L2 caches move in 64-byte cache lines, so reading 8 bytes moves 64, and the drives move 4 KiB blocks. The drive traffic is measured. The rest is estimated from the data layouts.

#### Bytes moved through DRAM: 0.77x

- AVL, 5.8 KiB. Each of the ~31 levels on the way down pulls in two cache lines, the node and the key it points to: 62 lines, 3.9 KiB. On the way back up it dirties one line per ancestor updating counts and heights, and those 31 lines get written back: 1.9 KiB.
- DiskArray, 4.5 KiB. About 15 lines for the index lookup and 9 for the binary search inside the block, 1.5 KiB. Then the shift: ~190 keys read and written, about 48 lines, 3.0 KiB.
- DiskArray puts less through DRAM than AVL, even though it does more work, because its bytes are contiguous. AVL uses 17% of what it moves. DiskArray uses 73%.

#### Everything moved, drives included: 2.1x

- AVL, 5.8 KiB. All of it through DRAM.
- DiskArray, 12.5 KiB. The 4.5 KiB through DRAM, plus a 4 KiB read from the drive and a 4 KiB write back to it. Both are measured: one of each per insert.
- DiskArray moves twice the bytes per insert. And it still does twice the inserts.

#### Bytes the algorithm actually uses: 3.3x

- AVL, 1.0 KiB. On the way down, a child pointer, a key pointer and a key at each level: 744 B. On the way up, a count and a height in each ancestor: 279 B.
- DiskArray, 3.3 KiB. About 250 B of index (~27 key comparisons and a few count updates), 72 B of probes inside the block, and the shift: ~190 keys read and written, 3.0 KiB.
- DiskArray does more real work per insert. Shifting keys inside an extent is the job, and it's three times AVL's whole insert.

#### What DiskArray has to handle: 4.9x

- AVL, 1.0 KiB. The bytes it actually uses, from above.
- DiskArray, 4.9 KiB. To change one 8-byte key it has to read, edit and write back a whole 4 KiB block, plus about 1 KiB of index lines to find it.
- It looks wasteful. Nearly 5x the data, to change 8 bytes. It isn't, and the next section shows why.

### Effective Bandwidths

![What limits each insert at 2G nodes](https://www.bitflux.ai/pics/memory_is_slow_part3/effective.png)

Inserts per second, times the data moved and used per insert, gives us the bandwidths. At 2G nodes:

|  | Inserts/s | Time per insert | Data moved | Moved bandwidth | Data used | Used bandwidth | Limited by |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AVL | 320K | 3.1 µs | 5.8 KiB | 1.8 GiB/s | 1.0 KiB | **312 MiB/s** | DRAM latency: ~62 reads, one after another, ~50 ns each |
| DiskArray | 670K | 1.5 µs | 8 KiB, on the drives | 5.1 GiB/s | 3.3 KiB | **2.1 GiB/s** | NVMe bandwidth: a 4 KiB read and a 4 KiB write |

DiskArray moves more data per insert than AVL, and it's faster on both counts. It moves the overhead faster: 5.1 GiB/s of traffic against AVL's 1.8, 2.9x. And it moves the data it actually needs faster: 2.1 GiB/s against 312 MiB/s, 6.9x. More bytes, moved faster, every way you count them.

Every AVL insert waits on about 62 reads, one after another, and uses 1 KiB of the 5.8 KiB those reads drag in. That's 312 MiB/s of useful work. Higher bandwidth DRAM wouldn't help, because DRAM latency hasn't moved in 20 years.

DiskArray is short of bandwidth. Its CPU work is about 0.3 µs per insert. The drives are the limit: from 32M to 1G nodes they hold at ~5.5 GiB/s, ~720K inserts/s. More drives, or faster ones, and it goes faster, until that 0.3 µs of CPU catches up at around 3M inserts/s.

### How DiskArray pipelines the drives

A drive round trip is about 87 µs. If DiskArray did one insert at a time, every insert would wait that long, twice, and it would manage a few thousand inserts/s. It does 670K. Here's how:

![DiskArray's pipeline: an IO slot's life spans batches](https://www.bitflux.ai/pics/memory_is_slow_part3/disk_pipeline.png)

DiskArray keeps 2048 transactions in flight, in two halves of 1024. One core does all the algorithm work and queuing; 28 io_uring workers just talk to the drives.

1. Queue a half. Look up each transaction's extent in the index in RAM, 32 at a time, and start that group's 4 KiB reads right away. Each read lands in a free buffer in the 24 MiB pool.
2. Run the other half. While those reads are in flight, work through the half queued last time, one insert at a time. Every block is already sitting in the buffer pool: search it, shift the keys. The block is now dirty, and it stays in the pool for now.
3. Write back. Dirty blocks pile up. Once there are 1536 of them, a quarter of the 6144 buffers, the next queue step writes them all out alongside its reads. Each block goes to a fresh spot on the drive, copy-on-write, and its old spot is freed when the write lands. That hands the buffers back for the next round of reads. It works out to one 4 KiB write per insert, just never one at a time.
4. Swap halves and repeat.

### How does Big O miss this?

Big O counts steps. It assumes every step costs the same. They don't, not even close.

A billion L1 cache hits take about a second. A billion DRAM misses take a minute and a half, and a billion NVMe reads take a day. Big O counts every one of those as one step.  Also, when you parallelize, the timescale comes back down to earth.  So Big O notation is very limited in its predictive power in practice.  It defines the shape of the performance curve but not it's slope or magnitude.

Let us observe the relative scaling performance these algorithms actually experience from 512K to 2G nodes.

![How much slower from 512K to 2G nodes](https://www.bitflux.ai/pics/memory_is_slow_part3/growth.png)

We can see AVL is scales much worse than Diskarrary even though Big O would make us think the opposite is true.

I started at Intel doing flash memory out of college. In the early days of the technology, you could use very simple equations to predict the characteristics of a cell.  At some point, the cells shrank to where the number of electrons in a cell was something that had to be quantified and thought about.  Now, the equations have to start taking quantum effects into consideration.

Big O in its most reductive form isn't going to tell you how things are going to perform in practical scales.  It didn't have to.  But as the performance characteristics of various elements of the system continue to diverge and become extreme I don't think the single n term O() is useful anymore.  I think it's time to start treating these equations and simulations more seriously and add in more nuanced effects.

### The quantum effects

Notice the curves aren't smooth log n curves. They have step functions where each step is something outgrowing hardware.

- AVL search drops from 4.0M/s to 2.3M/s between 512K and 1M nodes, as the tree grows from 36 MiB to 72 MiB, out of the 35.75 MiB L3.
- DiskArray insert halves, 1.6M/s to 830K/s, at 512K nodes, exactly where the drives start taking writes.
- DiskArray search drops from 2.2M/s to 1.6M/s at 4M nodes, exactly where the drives start taking reads.

Big O can't see any of these yet they have a huge impact on the practical scales we're dealing with.

## You can do better than AVL

Nobody uses an AVL tree for this. Here's what happens with the structures you'd actually reach for:

- ART, an adaptive radix tree: walks the bits of the key instead of comparing.
- B+tree: fat nodes with many keys each, so far fewer levels.
- NextArray: DiskArray's in-RAM sibling. Same extents and index, but the extents are 1 KiB in RAM.

### One at a time

First, everything doing one transaction at a time, like AVL:

![One at a time, in RAM, 4M to 64G nodes](https://www.bitflux.ai/pics/memory_is_slow_part3/field_plain.png)

| 2G nodes, transactions/s | search | at() | insert | delete | RAM |
| --- | --- | --- | --- | --- | --- |
| AVL tree | 772K | 490K | 320K | 368K | 144 GiB |
| ART | 2.90M | 253K | 3.12M | 2.45M | 146 GiB |
| B+tree | 1.13M | 1.87M | 905K | 887K | 38 GiB |
| NextArray | 1.52M | 6.06M | 1.29M | 1.26M | 33 GiB |
| **DiskArray, on disk** | **1.08M** | **1.29M** | **670K** | **666K** | **264 MiB** |

The better structures beat DiskArray, but not by as much as you'd think. B+tree ties it on search and beats it by 1.35x on insert. NextArray, DiskArray's own design kept in RAM, is 1.4x on search and 1.9x on insert.

ART is the fastest at search and insert, about 3x and 5x, but its at() is the worst here: ART has no rank, so finding the i-th key means walking.  So it's not a great example.

Still the best RAM structures aren't beating it by an order of magnitude.

ART and AVL have too much overhead to scale beyond 2G on this hardware. Both cost about 72 bytes per 8-byte key, 146 and 144 GiB at 2G nodes, and the box only has 192 GiB (188 GiB usable). The next doubling would have needed nearly 300 GiB. B+tree and NextArray, at 17-21 bytes per key, made it to 8G. DiskArray, at about 0.1 bytes of RAM per key, went to 64G and could have kept going.

### Pipelined

Because DiskArray is pipelined it could have an advantage over the RAM structures.  So we'll pipeline them the same way, and pull all the tricks we can try with prefetching and optimizing code paths.

![Pipelined, in RAM, 4M to 64G nodes](https://www.bitflux.ai/pics/memory_is_slow_part3/field_pipelined.png)

| 2G nodes, transactions/s | search | at() | insert | delete | RAM |
| --- | --- | --- | --- | --- | --- |
| B+tree, pipelined | 5.03M | 4.33M | 2.74M | 2.79M | 41 GiB |
| NextArray, pipelined | 6.45M | 6.06M | 4.02M | 4.07M | 33 GiB |
| **DiskArray, on disk** | **1.08M** | **1.29M** | **670K** | **666K** | **264 MiB** |

This is a different league. The pipelined structures beat DiskArray by 3-6x across the board, on the same single core. Pipelining NextArray took search from 1.52M/s to 6.45M/s and insert from 1.29M/s to 4.02M/s. B+tree went from 1.13M to 5.03M searches/s. The one thing it doesn't speed up is NextArray's at(), which was already a short walk of a small count tree: one at a time it's faster up to about 256M nodes, and past that the pipelined version only pulls slightly ahead.  Still not an order of magnitude.

### What pipelining means for RAM

Plain NextArray does one transaction at a time, like AVL. Each level of the index is a cache miss, and each miss waits on the one before it. The pipelined version is the same data structure, the same single thread, but it handles transactions in groups of 32:

![One at a time vs pipelined](https://www.bitflux.ai/pics/memory_is_slow_part3/pipeline.png)

1. Resolve the whole group one index level at a time. Issue the cache-line prefetches for level 1 of all 32 transactions, then level 2 for all 32, and so on. The misses for a level are in flight together, not one after another.
2. Prefetch each transaction's slice of its extent a few transactions ahead.
3. Execute them in order: the memmove, the count updates.

A core can only keep about a dozen misses in flight, so it's not 32x, but it's 4x on search.

NextArray was built for this. Every transaction follows the same short path: a few levels of a flat, sorted index, then one contiguous extent. That's easy to batch and easy to prefetch. A tree of individually allocated nodes isn't, because you can't know where the next node is until you've loaded this one.

If this looks familiar, it should. It's DiskArray's pipeline, pointed at RAM instead of at the drives:

|  | DiskArray, to the drives | Pipelined NextArray, to DRAM |
| --- | --- | --- |
| Group the transactions | 1024 per half, looked up 32 at a time | 32 at a time |
| Work out what you'll need | look up the extent in the index | look up the next index level, then the extent |
| Ask for all of it at once | a 4 KiB read per transaction, through io_uring | a 64-byte prefetch per transaction |
| While it's in flight | run the other half | handle the rest of the group |
| Where it lands | the buffer pool, in L3 | the cache |
| Then | search, shift, write back | memmove, update counts |

RAM stands for Random Access Memory, but it's not really random access anymore.  It's a block device with 64-byte blocks and 80-90 ns of latency, and you have to use it like one.

To get even reasonable performance out of either memory or storage, you need to treat them as parallelized asynchronous block devices that feed the caches.

## Recap

- Design for hardware not theory.
- Big O isn't that useful.
- Parallelize and pipeline or perish.
- Memory is slow, unless you treat it like a disk.

## Next Time

See me at [P99Conf.io](https://p99conf.io) 2026-10-22, register now.

Can we improve memory-bound HPC workloads 2x, without memory?
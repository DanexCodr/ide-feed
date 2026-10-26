When I was first learning the C programming language, in my early 20s, it was [common knowledge](https://retrocomputing.stackexchange.com/questions/27125/has-there-ever-been-a-c-compiler-where-using-i-was-faster-than-i) that of the two ways to increment a variable, `i++` was slower than `++i`. The post-increment function returned the original value of `i`, which meant stashing a copy of that value before performing the increment. Pre-increment avoided this wasteful operation.

And by “common knowledge” I really mean folklore, because I turned 20 in 1995 and even by then, the most basic of optimising compilers knew to check if you ever used the return value of `i++`, and if not, skip the operation to save it.

Scratch an old programmer and you'll probably find a dozen or so ingrained habits that, in an era where CPUs are doing [branch prediction](https://stackoverflow.com/questions/11227809/why-is-conditional-processing-of-a-sorted-array-faster-than-of-an-unsorted-array) and code reordering, are just as likely to make their program slower.

Anyway, remember prompt engineering?

It makes sense to believe that all the tricks we come up with with to make models behave better, the ways of working with models that get us to a useful result faster, if they work, are going to be folded back into the product, packaged, and become the default experience a few months later. And yet, in five years, I’m sure there will be old heads doggedly adding “you are an experienced software developer, make no mistakes” to their custom instructions.

I'm not saying it's worthless to keep up with the state of the art. You still need to be able do your job today, to the best of your ability. But a skill that can be picked up in a few weeks, and will be obsolete in a few months, has no value outside the moment.

Eighteen months ago, I was sitting in a crowded room watching a CEO enthusiastically declare that it was time to get on the AI train, because if you didn't get on it *right now* you'd be left behind. Maybe I'm getting old, but in a world where Google, Facebook, the iPod, iPhone and iPad, and so many other examples have shown that getting it right is more valuable than getting in first, I feel content to just keep pace with the pack, ready to pull [Steven Bradbury](https://www.youtube.com/watch?v=WUi4-H6hfw8) if and when the time comes.
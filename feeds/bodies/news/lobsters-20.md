In the [first part](https://www.modernescpp.com/index.php/cpp-and-memory-safety-part-1/) of this article, we have taken a look at two attempts to decide whether a given string is a palindrome. Both implementations were written in “Classic C++” and didn’t feel great: the code was difficult to read, hard to understand and consequently the defects were difficult to detect. Now it’s time to continue the story and to take a look at a better solution, the “Modern C++” solution.

## A Modern C++ Solution

So let’s take a look at a modern C++ solution.

Yes, it’s that simple: a single function call to the `std::equal()` algorithm. We compare the first half of the range represented by forward iterators with the second half of the range represented by reverse iterators.

*“But Klaus, wait a second: this `std::equal()` algorithm is ages old! This has been part of C++98! This isn’t modern, is it?”*

If this is what you are thinking, then I have some important information for you: modern C++ is not about new features or new C++ standards. It is about writing correct, fast and safe code by default. It is about a certain mindset. So to prove my point, ask yourself the question from before: are you certain that there are no safety or security related issues?

There are none, right? And it is so easy to verify: no `if` statements — in fact, no conditionals at all, no pointers or indices, no explicit loop. It’s just a single, simple function call. So this code is correct by inspection. It is correct by default. And it is simple. And fast.

There is even a newer, even more elegant solution:

This is the C++20 ranges-based solution. We are using the `std::ranges::equal()` function on the string and its reverse representation directly. We don’t even need iterators anymore. Admittedly, we are now comparing the entire range and not just the first and second half. However, performance aside, the simplicity, the elegance, and the correctness by default are amazing! This is what we refer to as “Modern C++”.

## The Real Problem

*“OK, Klaus, I agree this is simpler and correct by default. But does this really mean that the loop-based solution is bad? After all, it works, doesn’t it?”*

You are correct, it “works”, ignoring the UB for single-character strings. But it is more complicated, requires more effort to verify, takes more time to write, is more difficult to read and understand, requires considerably more testing and just isn’t correct by default. All of which means that, in the end, it is considerably more expensive, too. There simply isn’t a good enough reason to write it in this classic style anymore. This is exactly what I perceive as the real problem in our community.

Too many C++ developers have not embraced modern C++ yet and still use the dangerous and more error-prone constructs by default. Too many C++ developers don’t know about the modern ways of doing things or, for whatever reason, still prefer to write the more explicit code. Because of this, they work by default in the “unsafe mode” of C++.

To me this feels like an educational problem, a teaching issue. For too many decades people have written this classic C++ and “it was OK”. By now people feel too comfortable, feel too familiar with this style. This is the real problem.

Unfortunately, this problem is currently getting scaled up significantly: With the use of AI tools, people generate this kind of classic C++ automatically. And yes, I have got proof: I asked ChatGPT to generate an `is_palindrome()` function for me (see Figure 1). Guess what: it gave me almost exactly the function from the original LinkedIn post. And no: it didn’t even consider suggesting the use of an algorithm.

So why don’t these modern tools use the modern way? Well, despite the name, AI has nothing to do with intelligence. It is a statistics-based tool. If more people use the classic way, then statistically this is the “correct” solution. So it is not a big surprise that AI tools will rather write a `for` loop for you instead of using an algorithm.

I should be honest and state that this is not true for every AI tool on the market. Some are better than others, some actually suggest using an algorithm. However, this unfortunately doesn’t resolve the problem: AI tools may suggest outdated solutions, which are not best practice anymore.

Luckily many people in the community know better than the AI tool and know about the modern solutions. Let me use this opportunity for a shout-out to some people that quickly posted a good and modern solution to the original LinkedIn post. Many thanks to Alex Dathskovsky and Sergii Rybin for posting an algorithm-based solution. Honestly, we need more people like you that help to spread the information on how things should be done today. Thank you very much!

## What’s next?

So what else can we do? I for one can do my part as a C++ trainer: I can tell people. I can teach people. I can show people. And this is what I want to do here in Rainer Grimm’s blog: in the coming months I want to talk about the modern way of doing things in C++. I want to demonstrate how we work today, in the hope that this makes a difference, in the hope of establishing the modern C++ mindset and of maybe (hopefully!) contributing to the general realization, even beyond the C++ community, that C++ can be incredibly safe, if we just use it as it is supposed to be used.

In the following months, I’ll write about bounds safety, type safety, lifetime safety, initialization safety, and — as a special add-on — about undefined behavior. And I will demonstrate that with very little effort, you can avoid all of these safety problems easily and by default.

**Thanks a lot to my [Patreon Supporters](https://www.patreon.com/rainer_grimm): Matt Braun, Roman Postanciuc, Tobias Zindl, G Prvulovic, Reinhold Dröge, Abernitzke, Frank Grimm, Sakib, Broeserl, António Pina, Sergey Agafyin, Андрей Бурмистров, Jake, GS, Lawton Shoemake, Jozo Leko, John Breland, Venkat Nandam, Jose Francisco, Douglas Tinkham, Kuchlong Kuchlong, Robert Blanch, Truels Wissneth, Mario Luoni, Friedrich Huber, lennonli, Pramod Tikare Muralidhara, Peter Ware, Daniel Hufschläger, Alessandro Pezzato, Bob Perry, Satish Vangipuram, Andi Ireland, Richard Ohnemus, Michael Dunsky, Leo Goodstadt, John Wiederhirn, Yacob Cohen-Arazi, Florian Tischler, Robin Furness, Michael Young, Holger Detering, Bernd Mühlhaus, Stephen Kelley, Kyle Dean, Tusar Palauri, Juan Dent, George Liao, Daniel Ceperley, Jon T Hess, Stephen Totten, Wolfgang Fütterer, Matthias Grün, Ben Atakora, Ann Shatoff, Rob North, Bhavith C Achar, Marco Parri Empoli, Philipp Lenk, Charles-Jianye Chen, Keith Jeffery, Matt Godbolt, Honey Sukesan, bruce_lee_wayne,  Silviu Ardelean, schnapper79,  Seeker, and Sundareswaran Senthilvel.**

**Thanks, in particular, to Jon Hess, Lakshman, Christian Wittenhorst, Sherhy Pyton, Dendi Suhubdy, Sudhakar Belagurusamy, Richard Sargeant, Rusty Fleming, John Nebel, Mipko, Alicja Kaminska, Slavko Radman, and David Poole.**
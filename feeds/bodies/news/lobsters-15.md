Welcome back to the blog of Rainer Grimm! This is the first of hopefully many new C++-related articles in Rainer’s blog. Since you are reading this, you have potentially read many of his articles and have gotten an idea of his passion and his devotion to the C++ community. In this blog, for more than a decade, Rainer has provided the C++ community with countless articles about the latest and greatest of C++.

With deep sadness you may have already heard the news: Rainer passed away on October 6th 2025, as a victim of his ALS disease. He leaves a big hole in our hearts, but also in the C++ community. He will be sorely missed by many friends, colleagues, and students.

It would be a shame to let his amazing contribution to the C++ community go to waste. In order to honor his devotion to the community, a few C++ experts, in particular Mateusz Pusz, Jens Weller, Slobodan Dmitrović, Ivan Čukić, and me, have come together to continue his journey: bringing the latest and greatest news to you, the readers of Rainer’s blog. I’m making a start here, trying to uphold the spirit of his blog.

Of course there will be little changes: the five of us have our own style, our own interests, our own message. Thus the upcoming sequence of articles will inevitably be a little different from Rainer’s original articles. It will be a mixture of different areas of expertise, of different highlights and of different topics. But one thing will remain: we’ll make sure Rainer’s devotion to quality and insight will be upheld. We’ll make sure to continue on his path to bring valuable information to the C++ community.

## The Problem

So let’s start to talk about C++: we have a problem. C++ isn’t memory safe! …

I suspect that this isn’t particularly new to you. In fact, the NSA published an article back in 2022, in which it explicitly recommended not to use C or C++ for safety and security related software anymore [[1](https://www.nsa.gov/Press-Room/News-Highlights/Article/Article/3215760/)]. The wording has softened since the first publication, but the spirit remains the same: prefer memory safe languages.

But it is not just the US authorities. The recommendation in the “Cyber Resilience Act” of the European Union is similar: avoid memory unsafe languages. Although they did not explicitly mention C and C++ as the culprits, the message was clear enough.

This sounds dire, but of course there is a fundamental and very good reasoning behind these articles. According to [[2](https://digital-strategy.ec.europa.eu/en/library/cyber-resilience-act)], *“Hardware and software products are increasingly subject to successful cyberattacks, leading to an estimated global annual cost of cybercrime of 5.5 trillion Euros by 2021.”*

5.5 trillion Euros!!! Yes, several trillion Euros have been lost due to malicious attacks, many of them from foreign countries interested in the downfall of our economy and society. And this number alone should be a perfect explanation for the desire to harden our software against cyber attacks.

But how does this relate to C++? Well, unfortunately some statistics have been pulled out of proportion and bent to emphasize what a significant and devastating impact the lack of memory safety of C++ has on cyber security. Officials therefore advise the use of languages that are considered memory safe.

Now we could start talking about these statistics and we could go into detail why C++ and memory safety in general are not the most important factors for cyber security and why C++ itself is by far not as unreliable and endangering as it sounds [[3](https://herbsutter.com/2025/12/30/software-taketh-away-faster-than-hardware-giveth-why-c-programmers-keep-growing-fast-despite-competition-safety-and-ai/)]. We could also, as so many people on social media do, start to argue that the arguments against C++ are exaggerated, misinformed or just plain wrong. However, let’s be serious: of course there is truth behind the statements. Truth that cannot really be denied, unfortunately. Therefore, from my perspective, it makes more sense to explore where and why these arguments emerge and what we can do about it.

## An Example

Based on my many years as a C++ trainer and consultant, I believe I have a pretty good idea about the real problem in our community. In order to make a point, let’s take a look at an example I saw on LinkedIn some time ago [[4](https://www.linkedin.com/feed/update/urn:li:activity:7409153900911468544/)]. A developer posted code for a “Palindrome Check in C++”. Here is the original code:

Before reading on, please take a look at this code and tell me if you see any problems — in particular any safety or security related issues.

OK, I assume you’ve taken a good look and have found a couple of issues — yes, more than one. But in order to stay positive and in order to make an attempt, let’s start with the positive aspect of this code: yes, all semicolons in this code are correctly placed. Well done!

But unfortunately that’s it. The list of deficiencies is unfortunately much longer:

- a using directive for namespace std shouldn’t even be used in example code anymore. Inexperienced developers might get the impression it’s a good idea and apply this in their own code. So just to be explicit: this is a terrible idea. Core Guideline SF.7 will help you to understand the details [5].
- the main() function is used to demonstrate the code instead of immediately providing a properly named function for the task. We could argue that it is just an example, but we could also argue that this is just lazy. Or is it just code written by AI? Perhaps, but more on that later.
- the “input” string and the subsequent size variable are not const qualified. Which is a pity, because they are never changed, but only read. This clearly violates Core Guideline Con.1 [6].
- the variables firstPointer and lastPointer are defined within the same statement. While this works and compiles of course, it is considered bad practice today. Please, don’t do this anymore! See also Core Guideline ES.10 [7].
- although the variables are called Pointer, they are actually of type int. Thus the name is misleading at best — or just plain wrong.
- lastPointer is set to size-1, which only “works” because the chosen type is int, not size_t. Yes, I agree, in this case everything is fine, but a generalized function would have to deal with the special case, which is just ignored here.
- the characters of the string are accessed via the subscript operator. This operation takes a size_t, not an int, and does not perform any bounds checking, which could quickly lead to undefined behavior.
- firstPointer and lastPointer are postfix incremented, although the old value is neither needed nor used in the code. This potential waste of resources is warned against in Core Guideline P.9 [8].

## A Generalized Function

This (hopefully) feels like a crushing review. But you might want to argue: *“OK, Klaus, that may be a little picky. I get it, a lot of core guidelines were violated, but it’s just a simple example. After all, it works, right?”*

Well, I honestly don’t think that it is a good idea to post “simple” code examples that violate so many of the community’s best practices. Actually, in my opinion it is a terrible idea. However, we could be well-meaning at this point and imagine a second attempt to solve the problem, this time with a generalized function named `is_palindrome()`:

OK, OK, I admit it, I’m providing this example to make a point. For this reason I also don’t adhere to all the best practices. But we, again well-meaning, could argue that this is a much better attempt to solve the problem. So please, take a close look at the `is_palindrome()` function and tell me if you are certain that there are no safety or security related issues.

I hope you’ve really taken a good look. You might come up with the following summary: *“OK, Klaus, assuming you want to keep this simple and therefore really only want to apply this to a `std::string`, and considering this is only the next iteration, this appears to work well.”*

But wait: the question wasn’t “does it work well”, but “are you certain”! So are you certain, i.e. 100% certain, that this code does not contain any safety or security related issues?

At this point you might pause and reconsider. Honestly, if I were you, I wouldn’t be certain either. Although the code is just a few lines long, it is already difficult to think it through in every detail. Are all special cases covered? Could this result in an infinite loop? Could this accidentally access any invalid memory location? Are there other sources of undefined behavior? I can’t be certain by just looking at it. I’d need more time, potentially much more time to really think it through.

For this reason — the reason of not being certain — I would rate this as poor code. Yes, seriously, poor code.

*“But Klaus, isn’t this a little too harsh? This code isn’t so bad after all!”*

No, I’m dead serious. I would even argue that this is not the kind of C++ code we write and should write today, i.e. “modern C++” code. This is “classic C++” to me. And I’m very confident in saying this, because the modern solution is so much shorter and so much simpler.

## What’s next?

In the second part we’ll take a look at the modern C++ solution and discuss why it is superior to the classic solution. So stay tuned :-)

## References

**Thanks a lot to my [Patreon Supporters](https://www.patreon.com/rainer_grimm): Matt Braun, Roman Postanciuc, Tobias Zindl, G Prvulovic, Reinhold Dröge, Abernitzke, Frank Grimm, Sakib, Broeserl, António Pina, Sergey Agafyin, Андрей Бурмистров, Jake, GS, Lawton Shoemake, Jozo Leko, John Breland, Venkat Nandam, Jose Francisco, Douglas Tinkham, Kuchlong Kuchlong, Robert Blanch, Truels Wissneth, Mario Luoni, Friedrich Huber, lennonli, Pramod Tikare Muralidhara, Peter Ware, Daniel Hufschläger, Alessandro Pezzato, Bob Perry, Satish Vangipuram, Andi Ireland, Richard Ohnemus, Michael Dunsky, Leo Goodstadt, John Wiederhirn, Yacob Cohen-Arazi, Florian Tischler, Robin Furness, Michael Young, Holger Detering, Bernd Mühlhaus, Stephen Kelley, Kyle Dean, Tusar Palauri, Juan Dent, George Liao, Daniel Ceperley, Jon T Hess, Stephen Totten, Wolfgang Fütterer, Matthias Grün, Ben Atakora, Ann Shatoff, Rob North, Bhavith C Achar, Marco Parri Empoli, Philipp Lenk, Charles-Jianye Chen, Keith Jeffery, Matt Godbolt, Honey Sukesan, bruce_lee_wayne,  Silviu Ardelean, schnapper79,  Seeker, and Sundareswaran Senthilvel.**

**Thanks, in particular, to Jon Hess, Lakshman, Christian Wittenhorst, Sherhy Pyton, Dendi Suhubdy, Sudhakar Belagurusamy, Richard Sargeant, Rusty Fleming, John Nebel, Mipko, Alicja Kaminska, Slavko Radman, and David Poole.**
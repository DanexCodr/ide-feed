Page 1 of 4Type is such a talking point - languages either love it or ignore it, but how did it all get started and what does it mean for C? 

## Deep C Dives  
Adventures in C

#### By Mike James

[](<https://www.amazon.com/dp/1871962889?_encoding=UTF8&qid=&sr=&linkCode=ll1&tag=generalad-20&linkId=4fa8081139e7fc62d7870dd10e56111b&language=en_US&ref_=as_li_ss_tl>) Buy from [Amazon](<https://www.amazon.com/dp/1871962889?_encoding=UTF8&qid=&sr=&linkCode=ll1&tag=generalad-20&linkId=d753370b74431428dbd05015b78a60da&language=en_US&ref_=as_li_ss_tl>).

#### Contents

**Preface  
Prolog C  
Dive**

  1. **All You Need Are Bits  
Extract**: [All You Need Are Bits](<https://www.i-programmer.info/programming/111-cc/18606-deep-c-dives-all-you-need-are-bits.html>)****
  2. **These aren’t the types you’re looking for  
** **Extract** : [Ty](<https://www.i-programmer.info/programming/111-cc/19211-deep-c-dives-type.html>)[pe](<https://www.i-programmer.info/programming/111-cc/19211-deep-c-dives-type.html>) *************NEW!**********
  3. [Type Casting](<https://www.i-programmer.info/programming/111-cc/19099-deep-c-dives-type-casting.html>)
  4. **Expressions**
  5. **Bits and More Bits  
Extract: **[Bits!](<https://www.i-programmer.info/programming/111-cc/17953-deep-c-dives-bits.html>)**  
**
  6. [The Brilliant But Evil for](<https://www.i-programmer.info/programming/111-cc/17630-deep-c-dives-the-brilliant-but-evil-for.html>)
  7. [Into the Void](<https://www.i-programmer.info/programming/111-cc/17253-deep-c-dives-into-the-void.html>)
  8. [Blocks, Stacks and Locals](<https://www.i-programmer.info/programming/111-cc/18717-deep-c-dives-blocks-stacks-and-locals.html>)
  9. [Static ](<https://www.i-programmer.info/programming/111-cc/18049-deep-c-dives-static-storage.html>)[Storage](<https://www.i-programmer.info/programming/111-cc/18049-deep-c-dives-static-storage.html>)
  10. [Pointers](<https://www.i-programmer.info/programming/111-cc/18924-deep-c-dives-pointers.html>)
  11. **The Array and Pointer Arithmetic**
  12. [Heap, The Third Memory Allocation](<https://www.i-programmer.info/programming/111-cc/18752-deep-c-dives-heaps.html>)
  13. **First Class Functions  
Extract: **[First Class Functions](<https://www.i-programmer.info/programming/111-cc/17433-deep-c-dives-first-class-functions.html>)**  
**
  14. **Structs and Objects  
** **Extract** : [Value Structs](<https://www.i-programmer.info/programming/111-cc/18275-deep-c-dives-value-structs.html>)****
  15. [The Union](<https://www.i-programmer.info/programming/111-cc/17788-deep-c-dives-the-union.html>)
  16. [Undefined Behavior](<https://www.i-programmer.info/programming/111-cc/18653-deep-c-dives-undefined-behavior.html>)
  17. **Exceptions and the Long Jump  
**

<ASIN:B0D6LZZQ8R>

## Dive 2

## These aren’t the types you’re looking for

_“These aren't the droids you're looking for.”_ Ben Obi-Wan Kenobi Types, love them or hate them you cannot ignore them. Strongly typed languages currently rule the earth and anyone who suggests that strong static typing isn’t a good idea is swiftly stamped on. C is a strongly typed static language, but this does not necessarily mean what you think it does. C types aren’t the types you might want or expect. This said, the concept of type in C fits in perfectly with its low level intent.

## The Origin of Type

The concept of types in programming is both deep and shallow. It is shallow when you first meet it and gets increasingly elaborate as one abstraction is added on top of another. At its most advanced, types provide a theory of programming in the form of the Curry Howard correspondence which views programs and mathematical proofs as being one and the same. This leads us into areas of pure mathematics that are generally labeled as category theory and logic. The good news is that type in C is much more at the shallow end of the range but over time there have been efforts to make it deeper and hence more respectable and more like every other programming language. There is an argument that C needs a simple interpretation of type to be effective as a language that works at a lower level than most. Rather than abstracting type away from the way that the machine represents data, it is better to keep the association between data type and representation. The fundamental, but not the only, idea of type in C is simply how many bits are in use and how those bits are to be interpreted. This is a fairly rare interpretation of type these days and is another thing that makes C different.

## C Types

There are only four fundamental types in C – integer types, floating-point types, pointers and structs. The first two types are all about how you interpret the bits – they are the scalar types. The third is about how you reference other types and the fourth is how you organize other types. You might want to add arrays to this list, but an array is such a simplistic organization of other types that it almost doesn’t count – it is basically a use of the pointer type, more of which later.

## Word Size

At the raw machine level there are bits – nothing but bits. These bits are generally organized into chunks called nibbles, bytes, words, double words and quad words. The nibble and the byte are generally 4 and 8 bits respectively. The size of a word varies according to the machine, but essentially a word is the default size of a group of bits that the machine works with, usually 16, 32 or 64 bits, but these aren’t the only possibilities. Machines in the past used word sizes of 18, 36 and 48 bits – which are rare choices today, but serve to remind that word size is fairly arbitrary. Notice that word size is dependent on hardware. The electronics, the memory, the registers and the buses that connect them determine the word size. Machines generally aren’t restricted to working with a single word size, but there is usually one that fits their architecture better than any other and this is usually the fastest and most efficient. These groups of bytes are important because they are the units that the machine uses to process data. You can usually write instructions that work with bytes, words or double words and so on. For example, you could add two bytes together or you could add two words together and so on. At the machine level there would be distinct add instructions to add two bytes and two words and so on and you would have to work out which to use in any given situation. When writing in C the compiler does the job for you and it selects the instruction according to the type of the variables you are using. For example:

        char a = 1, b = 2;
        char c = a + b;
        printf("%d\n", c);

In most systems char is an 8-bit data type and so the compiler creates the machine instructions to add two 8-bit bytes. If you had written:

        int a = 1, b = 2;
        int c = a + b;
        printf("%d\n", c);

then the compiler would have selected the instructions needed to add two 32-bit words – assuming that int is a 32-bit type for the machine in question. That is, the fundamental reason for types in C is to determine the type of operation appropriate for the data. Type determines how operators act and this is always true, no matter how much we elaborate the idea of type. You could also add that, in C, type also determines how many bits are involved in the operation but this is more obvious – well it is to a C programmer...
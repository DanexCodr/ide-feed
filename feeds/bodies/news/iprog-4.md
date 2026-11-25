Page 1 of 2Expressions, you have been using them since you started programming and even before but they deserve more of your attention. Come and meet some oddities in C. 

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
** **Extract** : [Ty](<https://www.i-programmer.info/programming/111-cc/19211-deep-c-dives-type.html>)[pe](<https://www.i-programmer.info/programming/111-cc/19211-deep-c-dives-type.html>)
  3. [Type Casting](<https://www.i-programmer.info/programming/111-cc/19099-deep-c-dives-type-casting.html>)
  4. **Expressions  
Extract: **[Some Oddities](<https://www.i-programmer.info/programming/111-cc/19304-deep-c-dives-expressions-some-oddities.html>)***************NEW!************
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

## Dive 4

## Expressions

_“I don’t know what the language of the year 2000 will look like,  
but I know it will be called Fortran.”_ _CA Hoare, 1982_ One of the most important concepts in any programming language is the expression and C has expressions for most things and knowing how to use them is a big part of effective C programming. What might surprise you is that there was a time when expressions didn’t exist – they had to be invented. The generally accepted first implementation of expressions was in Fortran in 1957. John Backus and his team at IBM worked out how to compile expressions into machine code and the same algorithms are at work today, compiling C expressions into machine code. C A Hoare might have been wrong about what we call the language, but there is a little bit of Fortran in every modern language.

#### In Chapter but not in this extract

  * Expressions and Statements
  * C Expressions 
  * Compile v Runtime Expressions
  * Side Effects and Sequence Points
  * Auto Promotion
  * Some Oddities

The whole idea of an expression is so obvious that you almost certainly don’t need a conducted tour of all of C’s operators and how they interact. However, there are a few strange and almost unlikely things that you might not have noticed. None of them have the advantage of clarity of purpose, but you will encounter them in other people’s code.

#### Assignment is an operator

When you write a=b this is an expression just like a+b and the result is the value stored in b or the value of the expression on the right hand side. That is, a=b takes a and b and produces the result b. As a side effect it also sets a to the value stored in b, which is what you usually assume assignment to do! Notice that this implies that a cannot be an expression in its own right. What advantage would this have? The most obvious is that you can use it to set more than one variable: a = b = c = 2*2; which sets a, b and c to 4.  You can use variables, even ones that are being assigned, in the expression:

    int b = 3;
    a = b = c = 2*b;

as the expression is worked out before the side effect is enacted. This sets all of the variables to 6. Another use is to save a result while computing a conditional. For example:

        int a,b = 0;
        while( (a = 2*b) < 10){
            b = b+1;
        }

The assignment within the while loop sets a to 2*b and evaluates to 2*b, which is then compared to 10. At the end of the loop you will find that a is 10 and b is 5. It is arguable that this is confusing, but it does avoid having to compute the expression twice. In short, you can test an expression and save its value. Notice that all of the assignment operators behave in this way. For example:

    int a = 0,b = 0;
    b = a+ =1;

sets a and b to 1. You can even go as far as:

    int a = 1,b = 2;
    b+ = a+ =3;

This is evaluated as a is set to the contents of a plus 3 with the assignment returning 4 as its result. Then b is set to the contents of b plus the expression to the right, i.e. 4. As a result a is set to 4 and b is set to 6. You can see that this is the same as:

    b = a+b = a+3;

but of course you can’t use this form as you cannot assign a value to a+b. It is probably better not to use such confusing constructs
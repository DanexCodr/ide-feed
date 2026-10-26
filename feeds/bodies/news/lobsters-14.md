I got bored and wanted to make a parser of C expressions. this will probably become a compiler at some point. previously, I’ve made a calculator using [shunting yard](https://en.wikipedia.org/wiki/Shunting_yard_algorithm), but with an itch to perhaps make a compiler of some kind, I looked at *pratt parsing*.

you won’t find much information about pratt parsing in a conventional learning path of computer science. the [dragon book](https://en.wikipedia.org/wiki/Compilers:_Principles,_Techniques,_and_Tools), for all it talks about parsing, doesn’t mention it. as far as I’m aware, most programming language courses will probably teach either LR or recursive descent depending on how academic it is (mine taught recursive descent). pratt parsing specifically appears to be relegated mostly to compiler development and PLT circles. the most mainstream mention I know of it is in [crafting interpreters](https://craftinginterpreters.com/compiling-expressions.html); [wikipedia](https://en.wikipedia.org/wiki/Operator-precedence_parser#Pratt_parsing) also links a few other posts.

I used the crafting interpreters text to get my bearings, but I also wanted to practice reading formal papers more, so I tried using [Pratt’s original paper text](https://tdop.github.io/) as much as possible. it did take a bit more time than I’d have liked to wrap my mind around how the recursion fits into the operator precedence, but it did just *click* all at once, namely once I related it back to the shunting yard algorithm. so now I’m writing the observations down so I don’t forget. maybe it’s useful to you.

## shunting yard

the [shunting yard algorithm](https://en.wikipedia.org/wiki/Shunting_yard_algorithm) is, comparatively, much simpler than pratt. you have an output stream and an operator stack. operators are defined with their binding powers, where higher binding power means it binds tighter to its arguments (e.g. `*` has higher binding power in arithmetic than `+`). in the simplest description of shunting yard, for every token in the input stream:

- if it’s a “standalone” token (i.e. identifier/number), just push it to the output
- if it’s an operator token:
  - if it’s of higher binding power than the top of the operator stack, push it to the stack
  - if it’s of equal of lower binding power than the top of the operator stack, then pop all operator tokens of higher or equal binding power to the output stream before pushing the operator token to the operator stack
    - popping all “higher or equal binding power” operators assumes that all operators are left-associative
- at the end of the token stream, pop all remaining operators to the output.

a very primitive shunting yard in C, where expressions are converted to postfix notation, could be:

```
#include <stdio.h>
#include <ctype.h>

typedef struct {
    char ops[32]; // limit of 32 operators
    int idx; // index of last operator
} Stk;

void push(Stk *s, char op) {
    s->idx += 1;
    s->ops[s->idx] = op;
}
void pop(Stk *s)   { s->idx -= 1; }
char peek(Stk *s)  { return s->ops[s->idx]; }
char empty(Stk *s) { return s->idx == -1; }

int get_bindpower(char op) {
    static const int bps[] = { ['+'] = 1, ['-'] = 1, ['*'] = 2, ['/'] = 2 };
    return bps[op];
}

int main(int argc, char **argv) {
    char *str = argv[1];
    Stk _opstk = (Stk){ .idx = -1 };
    Stk *opstk = &_opstk;

    while (*str != '\0') {
        if (isdigit(*str)) {
            // number
            printf("EMIT '%c'\n", *str);
        } else {
            // operator (assumed valid)
            // get_bindpower(peek(opstk)) is the left binding power
            // get_bindpower(*str) is the right binding power
            while (!empty(opstk) && get_bindpower(peek(opstk)) >= get_bindpower(*str)) {
                printf("EMIT '%c'\n", peek(opstk));
                pop(opstk);
            }
            push(opstk, *str);
        }
        str += 1;
    }

    while (!empty(opstk)) {
        printf("EMIT '%c'\n", peek(opstk));
        pop(opstk);
    }

    return 0;
}
```

```
$ ./a.out '1+5*2+6'
EMIT '1'
EMIT '5'
EMIT '2'
EMIT '*'
EMIT '+'
EMIT '6'
EMIT '+'
```

the problem with shunting yard is that it’s not very extensible to *new behavior*. for example, the algorithm has no concept of “subexpressions” in the recursive sense; adding parentheses means attaching special functionality to the `)` token for popping off the stack until reaching the matching `(`. that’s not hard in its own right, but more complex behavior like unary operators, right-associative expressions, functions with variable arguments, etc. will get [messy](https://web.archive.org/web/20220705004349/https://wcipeg.com/wiki/Shunting_yard_algorithm#Extensions). this is where the transformation to pratt parsing comes in.

## from shunting to pratt

the core realization to turn shunting yard into pratt is, instead of using an explicit stack for operator precedence, using the *call stack* to implicitly be inside of subexpressions as we need them. unlike recursive descent, you don’t nest calls through every level of precedence for every expression, but rather only nest and return when entering subexpressions.

unfortunately, there’s no clean “intermediate” step for this. you kind of just have to thrust it all through the wringer and look at the output. here’s the simplest pratt-style parser I can show in c, equivalent to the shunting yard parser before:

```
#include <stdio.h>
#include <ctype.h>
#include <stdlib.h>

int get_bindpower(char op) {
    // the end token ('\0') is now defined in the bind power array
    static const int bps[] = {
        ['\0'] = 0,
        ['+'] = 1, ['-'] = 1, ['*'] = 2, ['/'] = 2
    };
    return bps[op];
}

typedef struct {
    char *str;
} Parser;

char cur(Parser *p) { return *p->str; }
void bump(Parser *p) { p->str += 1; }

void
expr(Parser *parser, int left_bindpower) {
    // all expressions *must* start with a "prefix" token
    // this is what pratt calls "nuds" in his original paper.
    // in this case, our only prefix tokens are digits
    if (isdigit(cur(parser))) {
        printf("EMIT '%c'\n", cur(parser));
    } else {
        puts("expression doesn't start with a number");
        abort();
    }
    bump(parser);

    // at this point, we're at an infix/postfix operator.
    // this is what pratt calls "leds" in his original paper.
    // when this check is false, it's kind of like "unwinding" the stack in shunting yard.
    while (left_bindpower < get_bindpower(cur(parser))) {
        // assumed to be valid operator (like the shunting yard code)

        // there's an expression on the right side of binary operators. parse it first.
        // this is kind of like pushing to the operator stack in shunting yard.
        int new_left_bindpower = get_bindpower(cur(parser));
        char op = cur(parser);
        bump(parser);
        expr(parser, new_left_bindpower);

        printf("EMIT '%c'\n", op);
    }
}

int main(int argc, char **argv) {
    Parser parser = (Parser){ .str = argv[1] };

    expr(&parser, 0);

    return 0;
}
```

```
$ ./a.out '1+5*2+6'
EMIT '1'
EMIT '5'
EMIT '2'
EMIT '*'
EMIT '+'
EMIT '6'
EMIT '+'
```

on its own, this doesn’t look too exciting. I made the stack implicit. big whuff. but! there are two neat things here:

- “prefix” operators have first-class handling now in the first half of expr()
  - these are called “nuds” in pratt’s original paper. the other half of expr() is for handling what I call “infix/postfix” operators, or “leds” in pratt’s paper.
- we have the power to assign arbitrary code to any individual operator as soon as the operator is seen, just like recursive descent.

these combined allow for simple & straightforward extensibility. here’s all it takes to add parentheses into the mix:

```
int get_bindpower(char op) {
    // add '(' to bps
    static const int bps[] = {
        ['\0'] = 0,
        ['('] = 0,
        ['+'] = 1, ['-'] = 1, ['*'] = 2, ['/'] = 2
    };
    return bps[op];
}

// ...

// forward-declare expr() and add paren() subroutine.
// this doesn't even need to be a subroutine; you can inline this in the expr() func.
// but this is cleaner :)
void expr(Parser *parser, int left_bindpower);

void paren(Parser *parser) {
    expr(parser, get_bindpower('('));
    if (cur(parser) != ')') {
        puts("no matching ')'");
        abort();
    }
}

// ...

// add the if '(' conditional here; rest is same
void
expr(Parser *parser, int left_bindpower) {
    if (cur(parser) == '(') {
        bump(parser);
        paren(parser);
    } else if (isdigit(cur(parser))) {
        printf("EMIT '%c'\n", cur(parser));
    } else {
        puts("expression doesn't start with a valid prefix token");
        abort();
    }
    // ...
}
```

```
$ ./a.out '1+5*(2+6)'
EMIT '1'
EMIT '5'
EMIT '2'
EMIT '6'
EMIT '+'
EMIT '*'
EMIT '+'
```

want to add *even more* operators? coalesce the `get_bindpower()` function with choosing the subroutine to run, storing “rules” as a struct of the binding power, prefix subroutine, and postfix subroutine. the core stays simple while all the operators run in their own little functions! I’m not going to paste another blob of code here, but that setup is described in the [crafting interpreters chapter](https://craftinginterpreters.com/compiling-expressions.html). it’s so elegant!

update: I also made my own reduced example with a more structed form in [my snippets repo](https://git.unix.dog/yosh/snippets/src/branch/main/c/pratt). it’s for mostly the same expression grammar with a few extensions (unary `+`, `-`, and a postfix `!`), showing how it can get extended to a more realistic and maintable form for a codebase. it also includes comments on how the code paths relate to pratt’s *original* paper if you read that.
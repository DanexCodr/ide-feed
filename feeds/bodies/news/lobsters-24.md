In past years, I've experimented union types in a low level language (Copper) and a higher level language. I got very interesting results but I'm currently experimenting a trimmed down version: just the option types.
What is an Union Type?
An union type is a list of two or more alternative types that a value can hold. For example:
`func f(x: Int | String)
    ...
end
`
the parameter `x` can be either a string or an integer.
Some languages accept to perform directly operations that are commons to all types of the union, for instance if `Int` and `String` types have a `print` method, you could just do `x.print`. But in the basic case, you must first discriminate the actual type of the value before using it:
`func f(x: Int | String)
    match x
    case Int -> i
        // do something with i as an integer
    case String -> s
        // do something with s as a string
    end
end
`
Adding Union Types to Copper
In Copper, my own "better C" language, I've experimented union types. I wanted to handle the general case `T1|T2|...|Tn` using a tag but also handling the special case `Pointer|Nothing` without any additional tag and discrimating using the `NULL` pointer value in order to be fast and integrate easily with external libraries.
Limits
The feature was not very well defined and I've added a lot of restrictions for an efficient compilation.
No Nested Unions
`(T1|T2)|T3` is not permitted. It simplifies the implementation of the compiler since a value of an union type is a pair
![Option type value](https://tibleiz.net/images/blog/tag-value.png)
where the value part can not include tags recursively.
Significant Order
`T1|T2` is different from `T2|T1`. This restriction allows a very useful shortcut for the common pattern:
`var file = 
    match File.open(filename)
    case Error -> err
        return err
    else -> f
        f
    end
`
can be rewritten using syntactic sugar:
`var file = File.open(filename)...
`
without having to make the `Error` type builtin into the language: it just picks the first type of an union, `Error|File` in the example above.
No Compatibility Between Unions
`T1|T2` is not compatible with `T1|T2|T3`.
It would have required to assign a global unique tag to each type or to implement a remapping of tags when promoting an expression to a compatible union.
With such a restriction, a tag can be easily assigned for each part: 

`0` for the first type, 
`1` for the second one, 
...

Results
The feature was really useful, but it was far too much complexity in the compiler for a minimalistic low level language such as Copper. The most annoying part was dealing with the special optimized case `Pointer|Nothing`.
My main usage was mostly for two cases:

`T|Nothing` 
`T|Error`

So, may be just handling `T|Nothing` will be good enough, and for errors I'll just go back to returning an error *and* a value.
What is an Option Type?
The option type is just a special case of union type: `T|Nothing`. It represents an expression that may have no value. 
An option type `T?` can have any value of `T` plus the special `nil` value.
![T?](https://tibleiz.net/images/blog/optional-t.png)

A `T` value *is a* `T?` 
`nil` *is a* `T?`.

Adding Option Types in Copper
The implementation will be done by reserving a value in the original type. Each type can define its own `nil` value.
For pointers, the choice is obvious, the nil value will just be the address `0` but it is not hard-coded in the language, any other address could be used as well.
For other types, it depends. A 24 bit RGB color in a 32 bit integer can reserve `0x8000_0000` for example. A signed integer index data type can use `-1` since it usually indicates an invalid or not-found value.
This implementation has lot of advantages: 

It integrates very well with native C APIs.
It is efficient: no tag to attach to a value.
It is flexible: you just need one value to reserve.

but it has few drawbacks:

Some types may not have a value that can be reserved for `nil`.
It is not possible to have `T??`

Refining the Option Type
The main idea of the option type is that you can't refine it to its main type without ensuring first that it is not the `nil` value.
I have found a simple way to do this:
`expr as id
`
It is a boolean expression that tests whether `expr` of type `T?` is nil. If the expression is not nil, the value is copied in a local immutable variable `id` of type `T`.
The trick is that the variable is not directly available, it is created in a hidden scope that is accessible in 3 special cases: 

The inner block of a `if`
The inner block of a `while`
The right expression of a `and`

`if expr as x
    // x is available here
end

while expr as x
    // x is available here
end

var isSingleton = list.head as first and first.next == nil

if list.head as first and first.next == nil // first is available after 'and'
    // first is also available here
end
`
Allowing Early Returns
The `as` operator is sufficient, but it can lead to the arrow anti-pattern:
`if expr1 as v1
    if expr2 as v2
        if expr3 as v3
            // do something
        else
            return err3
        end
    else
        return err2
    end
else
    return err1
end
`
It can be solved with early returns but it is not possible without a new construct, `or else`, that evaluates a block if a expression is nil:
`var v1 = expr1 or else
    return err1
end

var v2 = expr2 or else
    return err2
end

var v3 = expr3 or else
    return err3
end

// do something
`
The block must terminate either with a `return`, `break` or `pass`.
Refining the Option Type without Check
In theory this is beautiful: you can't dereference a pointer without checking its value first or the compiler will report an error. Unfortunately, in real code there are many situations where you know that a value is present but the compiler can't know it. For example:

Iterating over two link-lists where the number of elements are equals.
An object with two distinct phases: an initialization phase and a processing phase. In the first phase some properties are optionals but in the second phase those properties are guaranteed to be defined.

Sure these can be resolved in different ways:

Test before accessing a value even if you know that it is defined.
Rewrite the algorithms, change the data-model, copy the data into new structures where types are non-optional.

But either it is inefficient and can make code confusing (why the value is tested here, shouldn't it be defined at this point?) or it makes the code more complex by adding new classes and code.
It's simpler and easier to just force the type refinment and leave a comment to the reader on why it is safe to assume that the value is defined at a particular point in code.
For this I did not add anything to Copper, the language has already the `cast` operator that can change the type of an expression without any verification. However I've added a convenient `notNil` method in the standard library that perform a check at runtime in debug:
`var value = maybeValue.notNil // I know what I'm doing
`
Extending an Option Type
An option type has very few methods by default:

comparing a value with another value,
type conversion

but sometimes you want to write methods on the type even if it can be nil. Here's a common example:
`if obj as x
    x.delete
end
`
A `defopt` command allows to define methods on the optional type:
`defopt delete // delete applies to T?
    if self as x
        // 'self' is of type T?
        // 'x' is of type T
        // invoke the actual delete
        x.delete
    end
end
`
And now you just do:
`obj.delete
`
Option Type with a Nil-Checker
The problem
The previous solution works very well but introduces multiple concepts that you need to know just to read the source code.
In addition it can make some simple cases becoming very cumbersome. For instance, this common pattern of lazy creation:
`if self.findDialog == nil
    self.findDialog = self.createFindDialog
end
self.findDialog.open
`
becomes:
`var dialog: FindDialog
if self.findDialog as d
    dialog = d
else
    dialog = self.createFindDialog
    self.findDialog = dialog
end
dialog.open
`
It makes the code more verbose and requires two additional local variables. It is not a problem for the LLVM backend that will optimize everything by coalescing variables and eliminates useless branches, but it makes the code more difficult to understand.
A macro can help a bit:
`var dialog = self.findDialog.ifNil do
    var d = self.createFindDialog
    self.findDialog = dialog
    pass d
end
dialog.open
`
It is more compact but now it requires to know what the `ifNil` macro does.
Woudn't it be possible to avoid all this?
The Solution
An alternative is to infer that a local variable can not be nil at some points in the code. Instead of having explicit type refinment, the compiler does the refinment based on tests.
This solution is similar to what TypeScript or Kotlin do.
Here are some examples:
`if v1 <> nil
    f(v1) // ok
end
``if v1 == nil
    ...
else
    f(v1) // ok
end
``if v1 == nil
    ...
    return
end
f(v1) // ok
`
Globally it works well, it is very un-intrusive, a reader can understand the code without needing to know anything specific except that `T?` represents an optional `T`.
But the devil is in the details:
It requires a two-pass analysis on loops: a variable may be valid at the beginning of the loop but could be changed later requiring a second analysis:
`if v1 <> nil
    while cond
        f(v1) // ok on the first iteration
        v1 = ... // now v1 can be nil again
    end
end
`
It does not work well with genericity. Despite a test, the variable does not change its type. The reason is because the nil-analysis is performed after building a function (because of the multi-pass). This leads to unexpected errors and requires many explicit conversions:
`if v1 <> nil
    // v1 is still of type T?, so if f is generic, the parameter will be 
    // optional and the function won't assume that v1 is non-nil.
    f(v1)
end
`
Last but not least, it's a kind of black magic: the validity of the program depends on the power of the nil-checker. For instance, does the compiler handles the following cases?
(1)
`while v1 == nil
    ... // no break
end
f(v1)
`
(2)
`if v1 == nil or v2 == nil
    return
end
f(v1)
f(v2)
`
(3)
`v2 = v1
if v1 <> nil
    f(v1)
    f(v2)
end
`
Answer:

(1) yes
(2) yes
(3) no

But it could change in the future.
And I won't mention the 5% performance impact on the compiler ;-)
Despite all the benefits of this approach, I gave up and went back to the previous solution.
Is it Worth it?
The option type, despite being simpler than union type introduces many new concepts and requires additional knowledge that make the language more complex.
Am I ready to break the minimalistic yet complete enough language that I have managed to design over the year with this feature? does the few bugs it reveals are worth it?
The good parts:

The option type makes the intention clearer without polluting the source code too much with type annotations. 
It eliminates the need to search in code or documentation whether a parameter, return or attribute can be nil. 
It prevents accidental dereference of nil references.
It fits well with a statically typed language: the type tells the reader and the compiler which operations are permitted on a value.

While I can accept few type annotations that help me to make the code more readable and less error prone, I want the compiler to be a discreet reviewer and a friend that helps me finding bugs, not an inquisitor or a censor that forces me to rewrite my algorithms in a way that makes it happy but makes the code obscure.
Porting the compiler (the language is self-hosted) or Clade (my own text editor) was not very difficult and it showed few potential and actual bugs.
The real challenge was the port of my experimental decompiler: lot of complex algorithms and data-models. Algorithms rely on some properties (e.g. a Control Flow Graph has all nodes reachable from the entry node) to ensure that it will terminate and that there won't be any nil value at the end; that's something that can't be verified by the compiler.
At the beginning, I thought that the benefit of option types would be very low and that documentation in the code and tests were almost as good, but I have to admit that it can be helpful. May be it's time to get rid of the billion-dollar mistake.
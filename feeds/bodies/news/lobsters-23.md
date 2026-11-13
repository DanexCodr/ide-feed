After two detailed articles (that I hope you read!), we have a great technique to connect two elements with a line you can shape using `border-shape` and `shape()`.

In this article, we will explore more types of connections commonly used to create graphs and diagrams. Of course, we can’t cover them all, but the technique is generic, so if you understand it well, you can easily tweak the code to create your own connections.

Before we start, let me remind you that the goal is not to invent a new or better way to create graphs with CSS. This remains an experiment to explore modern features and create things that were impossible (or very difficult) to achieve using only CSS. This can also serve as proof of concept that it’s indeed possible using CSS. If so, it can lead to a better, more intuitive implementation.

Enough talking, let’s start!

At the time of writing, only Chrome and Edge fully support the features we’ll use.

## Dynamic Connection

The first connection type adjusts based on the element position and shapes. It’s similar to what we did in the previous articles, but this time we are not only connecting the centers, but we are also considering the sides.

Let’s start with a demo:

If you drag the elements around, you will notice the connection considers the closest sides to connect both elements, and if they get too close, it connects their centers. A dynamic connection!

If you look closely, you’ll notice we have four different positions, and therefore four different shapes (one curved line and three straight lines).

![Four pairs of teal and orange rounded squares, each pair connected by a line: one S-shaped curve from side to side, and three straight lines connecting the closest sides or centers depending on how the squares are positioned.](https://i0.wp.com/blog.master.dev/wp-content/uploads/2026/11/dynamic-connection-four-shapes.png?w=876&quality=80&ssl=1)

Did you forget a few cases? There are more positions!

Yes, but don’t forget the anchor position configuration. We have four regions where only one is visible at a time, and they are all symmetric, so the scale transformation gives us the remaining ones. If this last sentence sounds strange, go back to [the first article](https://blog.master.dev/two-circles-one-arrow-and-anchor-positioning/) to refresh your memory.

The shape is identical to the one we used in the previous article, same as the `border-shape` code.

```css
.link *:before {
  border-shape: if(
    style(condition_1): 
      shape(from ?? ??,curve to 50% 50% with ?? ??,smooth to ?? ??);
    style(condition_2): 
      shape(from ?? ??,curve to 50% 50% with ?? ??,smooth to ?? ??);
    style(condition_3): 
      shape(from ?? ??,curve to 50% 50% with ?? ??,smooth to ?? ??);
    else: 
      shape(from ?? ??,curve to 50% 50% with ?? ??,smooth to ?? ??))
    padding-box;
}
```

So far, nothing has changed compared to the previous article. We moved from two shapes to four, so we need three conditions instead of one.

Let’s start with the first condition: when both elements are close, draw a line from the center of the first element to the center of the second one. Said differently, when their distance is smaller than a specified value, we draw a line from the top-left corner to the bottom-right corner of the pseudo-element.

```css
style((hypot(100cqw,100cqh) < 200px)): 
      shape(from 0 0,curve to 50% 50% with 50% 50%,smooth to 100% 100%);
```

The `shape()` value should be clear, and if you are wondering about `hypot()`, it’s the hypotenuse math function. It calculates the diagonal of the pseudo-element, which is the distance between the centers of the two circles.

Let’s move to the second condition: when the vertical distance between the elements is smaller than a specified value, we link the right and left edges.

See that? I simply adjusted two values compared to the previous shape. That `60px` is half the element size. It’s defined as a variable in the demo, and yes, it’s a little drawback for this type of connection since the element size needs to be known.

I suppose you got the idea, so here is the full code:

```css
.link *:before {
  border-shape: if(
    style((hypot(100cqw,100cqh) < 200px)): 
      shape(from 0 0,curve to 50% 50% with 50% 50%,smooth to 100% 100%);
    style((100cqh < 200px) and (100cqh < 100cqw)): 
      shape(from 60px 0,curve to 50% 50% with 50% 50%,smooth to calc(100% - 60px) 100%);
    style((100cqw < 250px) and (100cqh > 100cqw)): 
      shape(from 0 60px,curve to 50% 50% with 50% 50%,smooth to 100% calc(100% - 60px));
    else: 
      shape(from 60px 0,curve to 50% 50% with 200px 0,smooth to calc(100% - 60px) 100%))
    padding-box;
}
```

I am adding an extra rule for the second and third conditions to illustrate that we can use `and`/`or` to create precise conditions. In this case, I want to avoid some edge cases where the connection didn’t look good to me.

![A teal square above and slightly left of an orange square, connected by a short, nearly vertical straight line between their closest edges.](https://i0.wp.com/blog.master.dev/wp-content/uploads/2026/11/conditions-and-or-edge-cases.png?w=401&quality=80&ssl=1)

For the extremities, it’s exactly the same logic. We keep the same `if()` structure, and we update the `shape()` values. For this reason, I wrote the following code in the demo:

```css
.link *:before,
.link *:after {
  border-shape: if(
    style((hypot(100cqw,100cqh) < 200px)): 
      var(--shape1);
    style((100cqh < 200px) and (100cqh < 100cqw)): 
      var(--shape2);
    style((100cqw < 250px) and (100cqh > 100cqw)): 
      var(--shape3);
    else: 
      var(--shape4))
    padding-box;
}
```

Then, each pseudo-element defines its own shapes.

If you are wondering about the logic behind the specified values, the conditions, their numbers, etc., the answer is: there is no logic. It’s a matter of personal choices. As I said in the introduction, it’s a generic technique. I simply built on what we learned in the previous article to create a more complex-looking connection.

Give it a try! Pick up a pen and paper, draw the connection, and try to code it. Start with one shape, then think about the different conditions and how you want to update it. Don’t be shy; it’s a fun exercise. Do it before moving to the next section because we are increasing the difficulty a bit.

Let’s not forget that we can add as many elements as we want to create a fancy graph!

![A graph of six colored nodes labeled A through F connected by curved and straight gray lines, forming a flowchart-like diagram.](https://i0.wp.com/blog.master.dev/wp-content/uploads/2026/11/dynamic-connection-graph.png?w=935&quality=80&ssl=1)

## Static Connection

Let’s try another type of connection. I am calling this static because the idea is to keep a line connected to the same sides, regardless of the element positions.

Here is a demo to better understand:

See that? We have a right-to-left connection, and the good news is that this type of connection doesn’t require us to know the element size, but we lose the symmetry.

![Four pairs of teal and orange rectangles in different positions, each connected from the right side of the teal one to the left side of the orange one, with the line curving or looping around as needed.](https://i0.wp.com/blog.master.dev/wp-content/uploads/2026/11/static-connection-right-to-left.png?w=1151&quality=80&ssl=1)

What symmetry? I don’t get it.

Here is a better figure showing the four different regions (explained in the first article) and the shape in each one of them:

![Four diagrams labeled A, B, C, and D, each showing a teal square and an orange square at opposite corners of a thin rectangle, connected by a right-to-left curved line whose shape differs between the left and right columns.](https://i0.wp.com/blog.master.dev/wp-content/uploads/2026/11/static-connection-four-regions.png?w=711&quality=80&ssl=1)

A and C are still symmetric (as are B and D), but A and B are no longer symmetric (same for C and D). This means we need a different strategy than simply working on one position and flipping it to get the others.

To do this, I will update the anchor position configuration. A slightly different one, better suited to this case.

We update the following:

```css
.link > * {
  position: absolute;
  --_x: calc(anchor(--c1 inside) + anchor-size(--c1)/2);
  --_y: calc(anchor(--c2 inside) + anchor-size(--c2)/2);
}

.link :is(a,b) {top:  var(--_x); bottom: var(--_y);}
.link :is(a,c) {left: var(--_x); right:  var(--_y);}
.link :is(c,d) {top:  var(--_y); bottom: var(--_x);}
.link :is(b,d) {left: var(--_y); right:  var(--_x);}

.link b {scale: -1  1} 
.link c {scale:  1 -1} 
.link d {scale: -1 -1} 
```

We replace it with this:

```css
.link > * {
  position: absolute;
  --_x: calc(anchor(var(--x) inside) + anchor-size(var(--x))/2);
  --_y: calc(anchor(var(--y) inside) + anchor-size(var(--y))/2);
  container-type: size;
}
.link :is(a,b) {top:  var(--_x); bottom: var(--_y)}
.link :is(a,c) {left: anchor(var(--x) outside); right: anchor(var(--y) outside)}
.link :is(c,d) {top:  var(--_y); bottom: var(--_x)}
.link :is(b,d) {left: anchor(var(--y) inside); right: anchor(var(--x) inside)}

.link :is(c,d) {scale:  1 -1}
```

The top and bottom values stay the same, but the left and right ones are updated. And only C and D need the scale for horizontal symmetry with A and B.

Drag the elements in the demo below to understand the different regions. (You can compare it with [the demo](https://codepen.io/t_afif/pen/LERWyvX/e943ba53f15ff9dd70c149a6bce0cac0) of the first article.)

Whatever the anchor position configuration, the important requirement is that we always have one visible region at a time. The other requirement when creating the shapes is the continuity between the regions.

Continuity? What?!

If we forget the implementation and play with different demos, it looks like we have a unique connection linking both elements. In reality, we have four, but thanks to the “continuity” effect, the illusion is perfect.

Here is the previous example where I am using different colors:

You can clearly see we have four different connections, but when moving from one to another, they share the same position/shape to create the continuity effect, making it look like it’s one. That’s why I always chose a straight line for the switch because it’s the easiest option.

For this new connection, we need to have continuity between two curved lines!

```css
.link :is(a,c):before {
  border-shape: shape(from 0   0,curve to 50% 50% with 150px 0,smooth to 100% 100%) padding-box;
}
.link :is(b,d):before {
  border-shape: shape(from 100% 0,curve to 50% 50% with calc(100% + 150px) 0,smooth to 0   100%) padding-box;
}
```

A and C still share the same shape (and B and D do too).

See that? The illusion is perfect! The moment we switch between A and B, the curve is the same in both areas.

Let’s add a condition to make the line straight when the vertical distance is small:

```css
.link *:before {
  border-shape: shape(from 0 0,curve to 50% 50% with if(style(100cqh < 100px): 0;else: 150px;) 0,smooth to 100% 100%) padding-box;
}
.link :is(b,d):before {
  border-shape: shape(from 100% 0,curve to 50% 50% with if(style(100cqh < 100px): 100%;else: calc(100% + 150px);) 0,smooth to 0 100%) padding-box;
}
```

What? `if()` inside `shape()`?!

Yes, we can do that. The whole `if()` block will resolve to a value, so you can place it wherever you want as long as the returned value is valid there. Since I only want to update one value, putting an `if()` inside `shape()` is more interesting and requires less code than putting two `shape()` values inside `if()`.

Here is the full demo again.

And that’s only one of 10 different cases! Yes, we can have all the possible connections.

Left-to-left:

Right-to-right:

Bottom-to-left (or left-to-bottom):

Bottom-to-top (or top-to-bottom):

And so on.

Can you do the remaining ones? Take this as homework. Study the demos I shared, then try a new one. The logic is always the same. Start by identifying a suitable anchor position configuration based on potential symmetry. Then draw the shape, keeping the continuity effect in mind.

And of course, it’s even more interesting if you combine different connections into one graph.

![Four colored rectangles labeled A, B, C, and D connected in a loop by curved gray lines that leave from and arrive at different sides of each block.](https://i0.wp.com/blog.master.dev/wp-content/uploads/2026/11/combined-connections-graph.png?w=886&quality=80&ssl=1)

## Want More?

Now that we have seen the potential of this technique, let’s push it a bit further and create some fancy demos!

What about a straight line that bends when both elements get closer?

Some physics using pure CSS! And the line stretches (gets thinner) if the elements are too far apart.

The idea is to define a static shape, then adjust the height based on the width. When the latter gets smaller, the height increases, and vice versa.

Here is a demo to better understand what’s going on. Resize the element to see how the curve behaves:

And don’t ask me about the math; I had to ask [two](https://math.stackexchange.com/q/5130987/695610) [questions](https://math.stackexchange.com/q/5131829/695610) online to find a good approximation of some complex formulas.

Let’s try something different: a zig-zag connector. This one is not robust, so don’t stretch it too far, or it may break. Don’t say I didn’t warn you!

A double zig-zag, maybe?

There are some scroll-driven animations, but don’t worry, I won’t bother you with a boring explanation. Enjoy the fun demos!

And what about a spring connector? You can go wild with this one; it won’t break!

Do you have another crazy connector idea? Share it in the comments. I am up for any CSS coding challenge.

## Conclusion

We are done! I hope you enjoyed this series. Another one packed with a lot of CSS fun. Do you remember when creating basic shapes was a nightmare?! Now, we can make graphs with complex connections that even SVG cannot easily create!

Again, what we have done is not something for production (at least not yet). Use it for fun, use it to create fancy stuff, but most importantly, understand the features we have used: anchor positioning, `shape()`, `border-shape`, `if()` conditions, etc. Once they are widely available, you will definitely use them in production.
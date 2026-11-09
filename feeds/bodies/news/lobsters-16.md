Today I'm introducing a new interpolating spline. Its name is S9. Without further demagoguery, here it is -

You can click on knots and drag to see how this thing works.

For comparison with other splines, [here](https://gasiulis.name/interpolating-splines/) is a demo. And [here](https://github.com/aurimasg/splines) you can find the implementation source.

## Why automatic spline at all?

For decades people were used to manually clicking and dragging cubic Bézier points until they developed Stockholm syndrome for it. Sometimes experienced designers will even tell you about having some magic rules like "keeping control arm lengths to about a third of chord length" which is good advice, but only if no better option is available. The fact is, humans cannot manually come up with good looking sequences of curves. The problem is inability to see subtle variations in the curvature of polynomial curves.

So what is this curvature anyway? The best way to explain is using a related concept called [osculating circle](https://en.wikipedia.org/wiki/Osculating_circle). It is an approximation of how the curve is bending at any point on it. Take a look at this demo -

If you play with this for long enough, you will see a pattern. If a circle size along the curve changes very little, the curve looks better. If it changes a lot, the curve looks worse. This smoothness of how the circle changes along the curve is called curvature variation. Less variation is better.

We can visualise this in a different way. If we record the reciprocal of osculating circle radius on every step of the curve, we get curvature profile of a curve.

Now you can see another pattern. If this plot is smooth, the curve also looks smooth.

However, it can be very difficult to see how smooth or not smooth this blue function is. Especially in absence of large spikes and multiple turns. Instead, let me show you another related plot. Here, in red, is a plot of a function representing curvature variation of the curve. And the rule is simple - thinner this plot gets, less curvature variation the curve has. We want the red part to be as close to the horizontal grey line as possible. For example, a section of a circle will have an integral (red number next to function plot) of this function equal to zero.

As you can see, it can be quite hard to get this red function to relax. But it can still be worse though. This is just one segment. How about we connect two curves?

See now you have to juggle more than two balls - you need to make individual curves smooth, but also keep the connection between the curves continuous too. In other words, the blue function must not have any gaps and the red function must stay as flat as possible.

This gets worse with every additional curve because polynomial curves have this property where changing one side of it will change curvature on the other side as well.

At this point you should see that trying to get harmony out of 20 or 30 connected curves has the same entertainment value as colonoscopy. This is what splines solve. Automatic smoothness of individual segments and continuity between curves.

## The goal.

The goal for S9 is to look good and to adapt to changes smoothly so it is useful in interactive CAD applications. This requires the following -

- Easy formation of round objects. It is easier to add more knots to reduce roundness than to add knots to increase roundness.
- Maximum curvature only at knots or near knots. It must not have spikes of curvature in the middle between two knots.
- Smooth transitions for any change in knot configuration. It must not have sudden changes of direction or form when the user drags knots.
- Minimize unwanted inflections. Avoid situations where knots find themselves in low curvature valleys.
- Hard maximum of one inflection per segment.

The primary goal is roundness. I want a spline which feels natural for forming fundamentally round and smooth objects.

## What are the current best splines?

At the moment there are very few splines that are optimized for the same goal as S9. In my opinion, the best published G2-continuous interpolating spline is [this one](https://raphlinus.github.io/curves/2018/12/21/new-spline.html). In fact, it is very good, only using one cubic curve to connect a pair of knots. I doubt you can do much better than this with a single cubic. Second best is [κ-Curves](https://zhipeiyan.github.io/projects/kCurves/kCurves.pdf), which is implemented in Adobe Illustrator as a "Curvature" tool. Using quadratic curves, but has a few fundamental problems where the solver can fail without special case handling. Then there is [Hobby](https://tug.org/TUGboat/tb34-2/tb107jackowski.pdf) spline. A very old one. It does not guarantee G2 continuity, but the solver is much simpler. Apple Keynote and some other applications use it.

There are some other, more famous splines like Catmull-Rom. I'm sure they have use cases even today, but they have no use in any even remotely serious CAD application. In fact, I would argue that any locally solved spline would have a flaw somewhere that cannot be fixed.

## Some facts about the spline.

I decided to call this spline S9 because it is my 9th attempt to come up with a decent spline. I still have the first 8.

- This spline is curvature-continuous at knots. This is called G2 continuity.
- Knots are connected using non-polynomial curves based on the Cesàro equation.
- Has lower curvature variation and better roundness for a wider subset of inputs than most splines in the same category.

## How does it work?

Fundamentally this spline works in a similar way to Hobby spline. It has two separate elements to it -

- Find a way to create a curve only given two tangent angles. One at the beginning of the curve and another at the end.
- Run a global solver which rotates these angles at each knot until curvatures of neighbouring segments match at knots.

The solver part is not a problem. The issue is how to come up with a curve parametrized by two angles. And it is harder than it looks.

## The curve.

The final and the most important part is the curve this spline is made of. After years of attempts, the best I was able to do is to describe the curve as a function of arc length.

For greek letter connoisseurs, [here](https://www.desmos.com/calculator/qca9hs1dyx) is an implementation of the curve in Desmos graphing calculator. That thing is powerful.

Curve math is explained in detail in comments for [S9 curve](https://github.com/aurimasg/splines/blob/main/Splines/S9Curve.h). Weight computation rules are sprinkled around in the [solver](https://github.com/aurimasg/splines/blob/main/Splines/SplineS9.cpp).

The curve solver is given two tangent angles and two weight parameters which are somewhat abstract, but the idea is as follows -

- Weight of one gives a linear change of curvature.
- Weight of zero gives maximum curvature. Practically it is a cusp.
- Weight in between transitions from linear curvature change to more and more violent turn as weight decreases.

For two weights of 1, the curve is identical to the [Euler spiral](https://en.wikipedia.org/wiki/Euler_spiral). This formula also has extra knobs to control curvature change near ends when weights decrease.

Weights are calculated from start and end angles. Which, like velocity function for Hobby spline, reduces a number of free parameters to two.

So what does this curve look like?

Input is two tangent angles you can adjust with sliders.

This curve, when used with automatic weight computation, will form high curvature spikes at the ends for large angles. This is a requirement for this type of spline. But for low to medium angles, it does have very little curvature variation which was the goal.

## Final remarks.

The source repository includes implementation of both curve solver and spline solver. However, it is not meant to be a full implementation of path construction solution for CAD. For example, it does not include G2-continuous transitions from straight to curved segments, sharp corners or angle locking. These features would be independent additions.

## Further reading.

Here is a minimal list of resources for anyone interested in curves and splines -

[Minimum Curvature Variation Curves, Networks, and Surfaces for Fair Free-Form Shape Design](https://www2.eecs.berkeley.edu/Pubs/TechRpts/1993/Archive/CSD-93-732.pdf). Henry Packard Moreton. 1992.
[From Spiral to Spline: Optimal Techniques in Interactive Curve Design](https://levien.com/phd/thesis.pdf). Raphael Linus Levien. 2009.
[Typographers, programmers and mathematicians, or the case of an æsthetically pleasing interpolation](https://tug.org/TUGboat/tb34-2/tb107jackowski.pdf). Bogusław Jackowski. 2013.
[κ-Curves: Interpolation at Local Maximum Curvature](https://zhipeiyan.github.io/projects/kCurves/kCurves.pdf). Zhipei Yan, Stephen Schiller, Gregg Wilensky, Nathan Carr, Scott Schaefer. 2017.
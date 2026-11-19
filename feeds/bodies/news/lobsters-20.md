I was inspired to create my first Fibonacci LED piece after seeing [this video](https://www.youtube.com/watch?v=_rt1cqsU8fo) by [Jim Bumgardner](https://krazydad.com/about) in 2015. I credit him for starting my Fibonacci obsession.

Fast forward to 2026. I’ve made dozens of Fibonacci designs. Recently, I saw [this brilliant post](https://www.instagram.com/p/DbYfgifReFx) by Nick Pisarro explaining the use of the golden angle in creating his beautiful [Halo Pixel](https://desert-ember.square.site/product/halo-pixel/2HSIGXSPGI5TLV2RCXBHFCMY). It got me thinking about how to explain the techniques I use.

Every Fibonacci board I make, from the tiny [One Inch Fibonacci64](https://www.evilgeniuslabs.org/one-inch-fibonacci64) to the [Fibonacci1024](https://www.evilgeniuslabs.org/fibonacci1024), puts its LEDs on a Fermat spiral, the same pattern as the seeds in a sunflower. It’s different from the [“Fibonacci spiral”](https://en.wikipedia.org/wiki/Fibonacci_sequence) drawn from squares, which is a single curve. The Fibonacci section shows where the name comes from.

## The rules

Start at the center. Then repeat:

1. Increase the radius a little.
2. Add an LED.
3. Turn 137.508°.

Every LED on every¹ Fibonacci board is placed by those rules. LED *n* sits *n* × 137.508° around from the first, and about √*n* out from the center. The next two sections explain those two numbers.

<small>
¹ There are exceptions to the √*n* rule, of course, like [Fibonacci64 Flower](https://www.evilgeniuslabs.org/fibonacci64-flower) and [Fibonacci256 Expanding](https://www.evilgeniuslabs.org/fibonacci256-expanding-hdr-pixelblaze).
</small>

## The golden angle

Any simple fraction of a turn makes spokes. At 90° (a quarter turn), every 4th LED lands on the same line. 120° makes 3 spokes, and 135° (3/8 of a turn) makes 8.

At 137° the LEDs still bunch into arms with gaps between them. 137.5° is exactly 55/144 of a turn, so the edge starts to crowd. It takes about 400 LEDs for that to show, though. With 256, 137.5° scores the same as the golden angle.

The golden angle, 360° ÷ φ² ≈ 137.508°, can’t be written as a fraction at all, so the LEDs never line up. The animation measures how close the two nearest of 600 LEDs get, as a percentage of the spacing in a perfect honeycomb.

| angle | closest two LEDs |
| --- | --- |
| 90° | 4% |
| 135° | 9% |
| 137° | 55% |
| 137.5° | 82% |
| 137.508° (golden) | 87% |

The golden angle’s digits never end, but a board only needs a few of them. Each extra digit buys a lot more LEDs before arms start to show:

| angle | as good as the golden angle up to | off by (degrees) |
| --- | --- | --- |
| 137.5° | 400 LEDs | 0.0078 |
| 137.51° | 1,100 LEDs | 0.0022 |
| 137.508° | 7,800 LEDs | 0.00024 |
| 137.5078° | 53,000 LEDs | 0.000036 |
| 137.50776° | 820,000 LEDs | 4.1 × 10⁻⁶ |
| 137.507764° | 43 million LEDs | 5.0 × 10⁻⁸ |
| 137.5077641° | 21 million LEDs² | 5.0 × 10⁻⁸ |
| 137.50776405° | 85 billion LEDs | 3.8 × 10⁻¹¹ |
| 137.50776405004° | 1.5 trillion LEDs | 2.2 × 10⁻¹² |

Two digits are plenty for the [Fibonacci1024](https://www.evilgeniuslabs.org/fibonacci1024).

<small>
² The seventh digit actually makes things worse: 137.5077641° is just as far from the golden angle as 137.507764°, but on the other side.
</small>

The golden angle isn’t the only angle that scores well, though. Other “noble” angles, like 99.5°, come close. The golden angle is the one that’s furthest from every fraction.

Angles past 180° just mirror these: 222.492° (360° − 137.508°) makes the same spiral, flipped. That’s why you’ll sometimes see the golden angle given as about 222.5°.

## The √n radius

With the angle set, the next question is the radius: how far from the center each LED sits. Each cell in the animation is the part of the board that’s closer to its LED than to any other. The dashed circles go through LEDs 64, 128, 192 and 256, so each ring between them holds 64 LEDs.

If LED *n* goes at radius *n*, LED 128 is twice as far from the center as LED 64, and LED 256 is four times as far. The circles are evenly spaced, but the outer rings are much bigger than the inner ones and get no more LEDs. The LEDs end up crowded in the middle and far apart at the edge. The biggest cell is about 150 times the smallest.

A disc’s area grows with the square of its radius. Putting LED *n* at radius √*n* means LED 256 is only twice as far out as LED 64, and every ring gets the same area. The circles get closer together toward the edge, every LED gets the same share of the board, and the biggest cell is only 1.3 times the smallest. If the radius grows more slowly than √*n*, it flips: the LEDs are far apart in the middle and crowded at the edge.

With equal area for every LED, the pixel density is the same all the way across the board.

## You can always add one more

A square grid only looks tidy at square numbers, rings only when every ring is full, and a hex grid only at 7, 19, 37, 61… The faint outlines in the animation show the spots each layout still needs to fill before it looks right again.

The spiral is an even, round disc at every count, and adding an LED never moves any of the others. The [Fibonacci32](https://www.evilgeniuslabs.org/one-inch-fibonacci32), [Fibonacci64](https://www.evilgeniuslabs.org/one-inch-fibonacci64), [Fibonacci128](https://www.evilgeniuslabs.org/one-inch-fibonacci128), [Fibonacci256](https://www.evilgeniuslabs.org/fibonacci256-hdr-pixelblaze), [Fibonacci512](https://www.evilgeniuslabs.org/fibonacci512-hdr-pixelblaze) and [Fibonacci1024](https://www.evilgeniuslabs.org/fibonacci1024) all use the same layout, with differently sized LEDs and different spacings, each stopped at a different count.

## Where the Fibonacci numbers come from

Look closely at any of the boards and you’ll see spiral arms. Connect every 3rd LED and you get 3 arms, because the golden angle is close to 1/3 of a turn. Every 5th LED makes 5 arms curving the other way, every 8th makes 8, and so on. Each of those fractions (2/5, 3/8, 5/13, 8/21…) is a little closer to the golden angle than the last, so each set of arms is a little straighter.

Any other count, like 4 or 30, zigzags or wobbles across the board instead.

The arm counts are 3, 5, 8, 13, 21 and 34. Put 1, 1 and 2 in front and each number is the sum of the two before it. They’re the Fibonacci numbers, which is where the boards get their name. Count the spirals in a sunflower head and you’ll find Fibonacci numbers there too.

## Real boards

The video shows a real [Fibonacci256](https://www.evilgeniuslabs.org/fibonacci256), then the [One Inch Fibonacci64](https://www.evilgeniuslabs.org/one-inch-fibonacci64), [One Inch Fibonacci128](https://www.evilgeniuslabs.org/one-inch-fibonacci128), [Fibonacci512](https://www.evilgeniuslabs.org/fibonacci512-hdr-pixelblaze) and [Fibonacci1024](https://www.evilgeniuslabs.org/fibonacci1024). All of them follow the same rules.

More on Wikipedia: [Fermat’s spiral](https://en.wikipedia.org/wiki/Fermat%27s_spiral), the [golden angle](https://en.wikipedia.org/wiki/Golden_angle), and [phyllotaxis](https://en.wikipedia.org/wiki/Phyllotaxis), the way plants arrange their leaves and seeds.

<small>The animations and videos in this post are © Evil Genius Labs LLC, licensed [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). You’re welcome to share and adapt them with credit, but not commercially.</small>
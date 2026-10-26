Prior to completing this project I didn't have a modern laptop. I also had never tried out a trackball mouse. After completing a Writerdeck and a Cyberdeck based on Raspberry Pi SBCs, I felt that it would be incredibly useful to have a full-fledged x86 portable computer. You know, a laptop. Why not spend two months designing, building, and refining a laptop myself instead of just hitting up Best Buy for a new laptop that's ready to go? I mean, I don't have good justification beyond "because I can, and I want to", but sometimes that's all the justification you need!

At the outset of the design process I started looking at Intel N50 and N100 mITX motherboards and PicoPSU power delivery, but started getting discouraged at the price prospect of something that was more expensive than a Raspberry Pi, consumed more power, didn't offer much more computing power than a Pi, and consumed significantly more power. That's when I figured if I was heading in a high power draw x86 setup, why not start shopping out some mini PCs?

That's where I found some decently spec'd out units with laptop processors and integrated graphics. These, I figured, would fit the bill for a machine that would be destined for some coding and light design work. Next up would be figuring out the power delivery.

Since my last folding screen Cyberdeck, I've been really enjoying designing within the Cyberpunk aesthetic. One of the aesthetic aspects that I felt the last build was missing was improvised part selection. Then I had the thought of powering the unit with a 24v power tool battery. The design aesthetic and the improvised hardware selection dovetailed beautifully in the design of the power delivery. The mini PC I bought had a 19v/5a power supply, and my power tool batteries were 24v. With a properly spec'd boost/buck converter, that should work perfectly both on the aesthetic requirement as well as the power and current requirement.

### The Fun Stuff

Now we get to the fun stuff: sketching out the design.

If you're interested in Cyberdecks, I'm sure you've seen a plethora of devices. From slabs without a hinging screen, to vintage computer style raising screens (like I used on my gray Cyberdeck), to absolutely awesome sliding designs like u/Personalitysphere's sliding modular Cyberdeck. I wanted something that would have the rough form factor of a laptop.

With the form factor decided on, the next step in every project I do is to gather up all the components, grab my calipers, and get to measuring and modeling in Blender. I make "good enough" 3d models of EVERYTHING. It's tedious and time consuming, but I wouldn't do it any other way. You can package everything so much nicer when using this method, and you run into WAY fewer problems during the assembly stage, WAY fewer redesigns and reprints, etc. This is the "measure twice" process when building a device like this, even though it's more along the lines of "measuer ten thousand times". Very worth it, and I highly recommend approaching things from this direction. Not to mention you're honing your ability to measure and model things, which is invaluable as a desinger.

After establishing the layout of the individual components, I start going through a process of sketching out designs and layouts. Usually I have a pretty clear vision of what I'm going for at this point, but a lot of design elements are "discovered" at this stage. It's also where some hard choices have to be made because establishing certain design elements sets you down a road where if you choose to go a different direction you can't just CTRL+Z you're way out of. You have to delete a LOT of work sometimes.

I'll jot out some of the notable design choices and processes that I went through:

So I'm adding this after I posted the project to Reddit and was asked for some further details on the trackball setup. At its most basic, the trackball is just a ball in a cradle with static 3mm ceramic bearings (3 of them, for a perfect balance of alignment ease and stability) hovering over the sensor from a gaming mouse. The mouse I used was the Corsair M65 (non-ultra, non-pro old version). It had a couple things that made it super convenient. First, the sensor and lens are mounted to small and compact daughter board, the daughter board had all the necessary pins from the sensor exposed as test points, and it uses an ADNS-9800 sensor which has libararies already built into KMK firmware (my firmware of choice because python and easy).

So with the rough sketch of the power delivery system in mind (24v battery, DC-DC conversion down to 19v) I had to start refining things into a working circuit, preferably with some off the shelf components to expedite the process.

So...  

The battery I am using is an off the shelf item. Great. But it's going to swing from ~25v down to around 19v (being conservative and keeping the per-cell low voltage at around 3.2v). So I needed a converter that does buck and boost. Searching around, there's a pretty common converter rated for 300w/10a. Should have plenty of overhead since the PC itself should only see around 75w/4a draw at the max, and 300w/10a should give plenty of overhead regarding efficiency drops across the converter and switching circuitry, and still not push the converter to hard to prevent crazy high temps.

Next...  

You can't fully just drain batteries. We all know that, it's a death sentence for our poor little cylindrically shaped ionic friends. So I needed a low voltage cutoff. Again, I was able to source another premade board that could be set anywhere between 0v and 36v. That should work perfectly set at 19v with a 2v margin to turn back on.

Then...  

Because I'm using a power tool battery I figured I could save some time, money, headache, and size/weight in the finished unit by offshoring the charging to the stock battery charger and just forgo integrated charging on-device. However, I didn't want to run the machine purely off battery power. I wanted the option to plug it into the wall when wall power is available. The best way to do this that I found was with a high-speed UPS power switch. Again, conveniently, there was an off the shelf module from Teyleten Robot that serves this exact purpose. It's adjustable, so I just set it to detect when power was applied to the jack that the wall wart gets plugged into to switch from battery power to wall power. It also does the reverse: when the wall power is removed, it switches to battery power. It also works perfectly.

With that the power delivery design was completed and I was ready to move on to the design of the chassis!

### Bill of Materials

The filaments I used on this project:

The hinges I used were 360 degree rotation friction hinges I found on Amazon. If you're building a Cyberdeck or Writerdeck and need some hinges these work great if you can design around them. The black nylon friction hinges on Amazon also work great on my Writerdeck retrofit. There are other options out there, but you do specifically want friction hinges or stay-in-place hinges when you're out there searching.

Well kinda but not really. I use CachyOS because I'm a filthy casual. There also was some intent with that choice beyond just being intimidated by the Arch install process. I am very much thinking of switching my main computer over to a Linux/Windows dual boot in the near future, and this project is a test bed for that. CachyOS offers a ton of conveniences over vanilla Arch, and in the handful of weeks that the physical build of this project has been completed I haven't run into a single issue or downside to using CachyOS. Time will tell, of course, but for now the CachyOS + Niri/Noctalia window manager setup (with Cosmic as a fallback if I need a traditional DE, but it hasn't been used since I got everything up and running), I am quite impressed. It's very usable, slick, modern, and snappy.

With a 24v 4ah battery, light use (word processing, coding) I have pushed it past 4 hours of use with the battery still having over 20v charge. Theoretically I could expect around 5 hours of use. I fully plan on buying an 8ah battery for it to push this big lunk to a thin book level of 10+ hours!

### Closing Thoughts

Overall, this project was a blast. The design itself, while it challenged my skillset, wasn't quite the challenge of the gray Cyberdeck... that one was a whole different ballpark with the smaller packaging and double hinged screen design. However, this was a very satisfying build, it nailed every single one of the requirements that I had from the outset, and it looks quite handsome as well if I do say so myself.
It’s been a long time coming. As someone who’s been first experimenting, then using, and now relying on Home Assistant to automate some portions of my home, I’ve long looked at a few key projects as being just out of reach. This past week I tackled one of those out of reach projects by installing a smart thermostat. Let me quickly catch you up on why I considered this out of reach, and then I will walk through how I choose a thermostat, the hurdles and quirks of installation, and then show the end result.

## Background[#](https://artificially-awesome.com/posts/nest/#background)

![The missing C Wire](https://artificially-awesome.com/images/20261106_085932.jpg)
A couple years ago we moved from a home built in 1970 to a relatively much more modern home built in 2001. With this came a number of benefits, such as Cat5 Ethernet drops in several rooms, which have enabled me to grow and expand my home network and smart home goals.

One such nicety I was truly expecting was a C Wire behind the newer home’s thermostat, unfortunately my hopes were dashed when I took a peak behind the old thermostat on the wall. It was one of those basic 5-day/2-day digital thermostats that were very common in the 90’s/00’s, and was loaded with two AA batteries and no C wire. No C wire meant if I wanted to install a true “smart thermostat” I would be constantly tied to either batteries, a proprietary “C wire adapter” that some companies offer but are not universal, or replacing the thermostat wire in the wall. Truly, what I wanted was to replace the wire in the wall - having a C wire meant I could use nearly any smart thermostat on the market. The smart thermostats that connect with WiFi usually require a C wire as they are generally too power hungry to run on batteries.

## So I walked away. For two years.[#](https://artificially-awesome.com/posts/nest/#so-i-walked-away-for-two-years)

I thought, maybe I’ll hire someone to run a new wire for me, but that expense seemed frivolous compared to the various home improvement projects already in line waiting for funding. There it sat, on the back burner for about two years. In that time I’ve continued to expand my smart home, adding a Lay-z-spa WiFi module to the inflatable hot tub, some water leak detectors, a siren, and more. But integrating the homes HVAC climate control remained out of reach.

Then, a news story about consumer rights caught my attention. It lead me over to a FULU webpage, which I browsed around for a little while before finding a link to the Nest Thermostat bounty: [Nest Learning Thermostat Gen 1 & 2 [Awarded]](https://bounties.fulu.org/bounties/nest-learning-thermostat-gen-1-2)

I had heard of NoLongerEvil when the news originally broke earlier this year. But this reminded me of the project so I jumped into the NLE documentation pages [Introduction - No Longer Evil](https://docs.nolongerevil.com/)
and read through the installation steps. Didn’t seem to hard, especially for a 2nd Gen Nest, and there was good support with Home Assistant. Maybe a day or so later I came across a post from someone using a zigbee thermostat in Home Assistant. The C-Wire upgrade continues to roll around in my mind as something worth trying. I order a 50ft 6-wire thermostat cable on Amazon and start pre-planning how I can make the upgrade happen.

## The missing C Wire[#](https://artificially-awesome.com/posts/nest/#the-missing-c-wire)

So I head down to the basement and locate the existing thermostat cable running from the furnace. I trace it along until it diverts up through a hole in the ceiling. I consider my positioning in the house and believe that this is pretty much directly below where the thermostat is mounted in the hallway on the level above me. I look for how the wire is secured - with many zip ties onto various pipes. Some water lines some gas lines. That is fine but I am concerned with how the wire might have been secured inside the wall behind the thermostat. A single staple could not only ruin my plan for an “easy” upgrade but might mean cutting large holes in walls where I really don’t want to.

![Old wire](https://artificially-awesome.com/images/20261106_095714.jpg)

Based on the accessibility it didn’t look feasible to fish a new wire to the thermostat while keeping the existing wire in place. Doing so would require adding at least another hole in the basement ceiling, and likely another hole in the wall above, things I would like to avoid. That left me with essentially two options. Either attach the new wire to the old one behind the thermostat and pull down from the basement, or cut the wire in the basement, attach the new wire, and pull up. Either way was essentially the same - once the old wire is pulled out of sight on whichever side, that would be a point of no return.

![Old wire](https://artificially-awesome.com/images/20261106_095654.jpg)

I decided to attach the new wire in the hallway, behind the thermostat. I disconnected the wires and removed the old thermostat, then used a copious amount of electrical tape to join the new wire with the old one. I returned to the basement and started pulling the old wire down. At first there was essentially no give. I thought I was toast - the installer “must” have put a staple into a stud to secure the old wire behind the wall. I suppose this is probably a builders best practice but sometimes as a homeowner you just need a wire to be able to pull through, ya know?

Anyway, I went back upstairs, and pushed and pulled the wire a few inches over and over, trying to free up the drywall enough to hopefully past the thicker taped portion through the drywall. In the end I got my drill and made the existing hole slightly larger thinking this might be the hold up.

Back downstairs and on my final hope, I gave the old cable a strong tug and low and behold it started to slide out! I cannot express how much of a relief this was as I was able to get a couple of solid feet to pull through so I figured at this point there must not be anything securing the cable in the wall. All I need to do is get the new cable the few feet from the thermostat location through the floor / basement ceiling hole. Once that is passed it would be straightforward to finish routing the cable by hand.

OK, so I head back upstairs and find the new cable has wound up a bit so I straighten it out. Then I think about how I need to avoid pulling the whole new cable into the wall, so I tie the open end to a door handle in the hall. This way i cannot accidentally pull too far.

![Protect the pull-through at all costs](https://artificially-awesome.com/images/20261106_095647.jpg)

One or two more solid pulls and I see the electrical tape pulling through the ceiling! Yay, I am essentially home free.

![Taped section pulls through](https://artificially-awesome.com/images/20261106_095849.jpg)

I end up having to go up/down the stairs several more times as the new cable keeps binding up, but each time I can clear the bind and then pull a more through. With a couple feet left upstairs (still tied to the door handle) I stop pulling and prepare to run the wire over to the furnace. The old wire I mentioned was zip tied to pipes for most of it’s routing, but I discovered a long portion of the run was a hot water pipe. This seems like a non-optimal solution considering copper wire is a great transmitter of heat. So instead I pop a couple reusable cable staples into a beam and then run most of the way by following some electrical wires. Near the furnace I go ahead and use cable ties onto nearby conduit for the final part of the run.

![Taped section pulls through](https://artificially-awesome.com/images/20261106_104502.jpg)

So, we’re at the furnace, now what? Per my researching basically all modern HVAC systems will have a screw terminal for a C Wire. I guess installers just save a couple bucks by running a 4-wire cable instead of a 5-wire cable? I don’t understand this at all and it makes me super annoyed. Anyway, I actually bought a 6-wire cable because it was essentially the same price as a 5-wire, I think literally about a $5 difference. So I have an extra wire just in case some future HVAC enhancement needs another wire. Even in homes not using smart thermostats by default or not needing a C Wire should just have the spare wire there. Leave it un-stripped and taped up or secured with a wire nut, but just don’t run 4-wire cables. Hopefully at some point after 2001 it became a new building code. Rant over.

Anyway turn off the power and then pop open the furnace panels and find the wiring area with the old 4-wire cable. I take pictures (always take pictures of before & after!). The wiring is very simple, just using screw terminals. I remove the old wires and connect new ones including the C wire. I actually used the wrong color at first but then found that the default for a C wire is blue so I swapped it. With everything buttoned up I head upstairs and connect the old thermostat. I also enable power to the furnace again. Now I can run through the functions - everything works! (fan on, heat, cool). I’m ready to go smart. Since I hadn’t actually received the new thermostat yet, I go ahead and install the old one back on the wall.
![Rewiring the furnace](https://artificially-awesome.com/images/20261106_113425.jpg)

## Picking the upgrade[#](https://artificially-awesome.com/posts/nest/#picking-the-upgrade)

When we left off on the smart thermostat I mentioned a couple of options I was weighing. Either a Nest or one of the Zigbee models (such as the Zen Zigbee Thermostat). I had also considered “rolling my own” from a zigbee controlled relay board as well.

In the end I took what feels like the safest option - the Nest 2nd Gen thermostat. Why a Nest with other options exist?

- Solid hardware - people absolutely raved on them when they came out (before Google went and killed all of their smart functions).
- Family friendly - Comparing the user experience of the Nest to the Zen, I feel that the Nest is slightly more user friendly - just rotate the outer ring to change the set temp. The Zen is pretty close though and I don’t think would have been an issue.
- Keeps working if Home Assistant, WLAN, or internet go down (I.e., you can still walk up to it and set the mode or temp manually and it will control HVAC fully offline). I’m not sure if all Zigbee models can do this - likely some can but it was definitely something where I wanted to make sure manual control would always be available even if technology is down.
- Price - absolute steal pricing for used. This makes sense given that the hardware was abandoned by the OEM. Most people don’t want something they have to hack/flash/self-host/etc. This makes picking up a used Nest quite easy. If you decide to go this route be sure to purchase a compatible model (currently only 1st and 2nd Gen is supported with 3rd Gen hopefully in the future) and WITH the required back plate. The Nest is essentially two pieces and you must have both - the back plate connects to your thermostat wires and then the display snaps into that. Without both you will only have a paper weight and weirdly the auction listings I saw for only a back plate were quite a bit more expensive than listings that had both pieces included.
- If you’re in the UK I think there was a 3rd piece you need - some kind of control box for your HVAC - please do your research!

Honestly if I had woken up on my other side that morning I might have bought the Zen. I already run most of my smart home on Zigbee, the 2nd hand pricing I saw was very close to that of the Nest 2nd gen, the interface seems simple, etc. It was a close race.

## Hacking the Nest[#](https://artificially-awesome.com/posts/nest/#hacking-the-nest)

Before recieving the Nest I went ahead and added the NoLongerEvil app to Home Assistant (HAOS), so that was ready to go.

After waiting a few days for the delivery I was ready to swap out the thermostat, but wait, we first have to free it from the evil corporate clutches. In truth I could have plugged it straight in and used it but with Google terminating them it would have been even dumber than my old thermostat - allowing set point and mode, no schedule programming supported - obviously that wouldn’t fly.

So I pulled up the NoLongerEvil documentation again and got started. In the end the process was mostly easy with a couple of gotchas. First, be aware that flashing from a Windows PC is not supported. Only Mac and Linux will work. Luckily I already run Bazzite on most PCs so I didn’t have to worry about this one. If I’d only had a Windows PC then flashing a bootable Linux desktop to a USB flashdrive would have only added a few minutes to the process.

I opened the AppImage which reported everything was ready to start, I connected the Nest to a MicroUSB (too old for USB-C port) and it booted up.

From there things were a little bit “fiddly”. I did have to run the extra terminal command for expanded USB access which was listed as an optional step in the guide. Conversely I didn’t need to install any extra packages as apparently Bazzite had everything needed by default.

Upon the first couple of attempts the installer timed out waiting for the Nest to connect. This was mostly because the Nest takes quite a while to boot and the installer times out slightly too soon (I think). On the 3rd try I got the timing right and the installer found the Nest and flashed it.

After flash was also a bit “fiddly”. So the Nest booted up from the “NLE” boot screen, confirming the software had loaded successfully. From there the installer goes right into trying to connect to the Nest over the network. However, you have to get the Nest connected to your WiFi network (obviously, but not mentioned anywhere in the setup document). Secondly, after booting up the Nest apparently has a timeout of something like 2-3 minutes where it will function normally but after the timeout it will go to an error screen saying “please connect the back plate” and it simply won’t let you do anything once that comes up. So you might be in the middle of typing in your “a little too complex” WiFi password when the error pops up and there is no way to exit the error except connecting the back plate. So I did that and then went back and re-started entering the WiFi password when a second error popped up of “no wires detected” (or similar) - again no way to exit or go back. Sigh - this was pretty annoying to be honest.

Fine - I shut off furnace power, remove the old thermostat and then wire in the new back plate, and then click in the Nest. Now, standing in the hall rather than sitting at my desk I start entering the WiFi for the third time. And once again I am a few character in when “Power not detected on Rh wire” OMG CAN YOU JUST LET ME ENTER THE DARN PASSWORD.

Back downstairs, turn on furnace power, back upstairs, the Nest walks through a setup process, shows me which wires are connected, everything looks good. Finally, after probably 20 minutes of being more interrupted, the Nest let’s me finish entering the WiFi credentials.
![Nest back plate](https://artificially-awesome.com/images/20261107_184638.jpg)

Back at my computer - I remember that I probably need to add a VLAN rule to allow Nest specific traffic to reach Home Assistant. I try to keep all IoT devices on a separate WiFi network that by default cannot access the internet or other devices on the LAN. I add the firewall rule and then continue with the installer - it finds the Nest quickly and, applies the LAN address and correct port for Home Assistant / NLE, and we are ready to go.

## Programming[#](https://artificially-awesome.com/posts/nest/#programming)

And wow, it’s really really good. First of all, I’ve always been annoyed that “programmable thermostats” are limited to about 4 settings per weekday and per weekend. I figure if you can do 4 why not 6? Why not 8? In our old home we replaced the aging furnace and opted for a “smart touchscreen” thermostat and it was literally the worst. It was a terrible resistive LCD that barely responded to taps, the interface was needlessly complex, burying settings many pages deep, it didn’t allow to setup a fan cycle, and was still limited to 4 temp settings in the schedule. Awful, just awful.

Why is the Nest good? First of all, I can’t tell you how much easier it is to program the schedule from a PC browser than trying to stand in the hall and use buttons on the old one. Click the time bubble and enter the temp. Drag the bubble earlier or later. Add more bubbles OMG IT ALLOWS MORE THAN 4 PER DAY ITS A MIRACLE.

![NoLongerEvil Nest Programming](https://artificially-awesome.com/images/Screenshot_20261109_220915.png)
Realistically do people need more than 4 per day? I don’t know. All I know is that when programming the old one I would always feel like “man I just need one more time setting to get this how I want it.”

Fan cycle. This is something I have wanted forever. Ever since I heard someone, probably with a Nest, talk about it ten years ago or something. It let’s you say “if the heat or A/C don’t run for a full hour, spin the fan for a few minutes.” Why is that such a big deal? Well, in a house, especially with multiple floors, the spot with the thermostat is one temperature, but there are going to be a whole range of other temperatures everywhere else. Colder in the basement, hotter upstairs, maybe cooler in that one room and hotter where the sun shines in the windows, etc. Not only does this help to normalize temperatures by moving the air around, but it also keeps the air clean and fresh by running it through your air filter even when heating and cooling isn’t needed.

Learning. I don’t yet know if I care about this. Apparently the thermostat will take notice if you keep turning up or down the set point, and eventually it will adjust your daily schedule based on that behavior. I have this enabled for now and will be curious to see if it works or is annoying.

Other. It gets the date, time and outside temperature from Home Assistant - pretty cool! It also has a built in humidity sensor.
![NoLongerEvil Nest Programming](https://artificially-awesome.com/images/Screenshot_20261109_220824.png)

## Home Assistant[#](https://artificially-awesome.com/posts/nest/#home-assistant)

I mentioned that I installed NoLongerEvil as an addon in Home Assistant. This is not the only option - you can run it separately with or without Home Assistant, and you can even use a free cloud service from NLE if you aren’t into self-hosting. In that case you are relying on NLE to keep their cloud bills paid and stuff. As an already prolific self-hoster, I definitely wanted to go that route.

In addition to the NLE screen where I can see status and set the schedule, it was also easy to add a climate card to my dashboard for family use. This card allows easy access from our phones in the Home Assistant App to tick up or down the temperature, and change the mode (like go from heating to cooling or off). This is great because it both makes the thermostat available to everyone who I decide to give an Home Assistant account to, through their phone. And because Home Assistant is accessible from anywhere, we can tweak the house settings from anywhere in the house or even away from home. Driving home in a blizzard and really want the house nice and toasty when you get there? No problem.

More than just remote control, all the same core functions available from the climate card can be added to Home Assistant automations. I may or may not ever add automations but for someone already using them to turn on and off lights, send notifications, etc., this would not be difficult. I just haven’t thought of anything I need to automate yet. But it gives me a nice feeling knowing I can have so much control over the device I purchased.

## Conclusion[#](https://artificially-awesome.com/posts/nest/#conclusion)

It’s up and working, the heating kicked on right on schedule this morning to warm up the house before clock alarms sounded. I gave the family a super quick 2-minute demo of how to use the wall unit and how to pull up the card in Home Assistant. No questions, a little bit of praise (for the phone control, the money saved, and keeping hardware out of a landfill). It seems like a lot of effort for such a small result, but it goes so much beyond this. It’s going to end up being countless little things for years to come. It’s going to be turning things down/off on a road trip because we forgot before leaving the house. It’s going to be ticking up the heat when we are all in the basement playing a board game and feeling chilly. Or a hundred other scenarios that will happen.

Would I do it all again? Yes for sure. Especially running a C Wire as that opens the door to so many options and frees me from being worried a pair of AA batteries will die during a very inopportune time. The Nest was one choice of many, but I knew I wanted something that would tie directly into Home Assistant. Once you control your home automation it is nearly impossible to “go back” or accept a corporate cloud solution; this was a must.

By the way, I typed this whole thing up by hand - no AI writing here. I even left a few typos in “on purpose” to prove it (I did try to fix most of them LOL). If you appreciate my writing feel free to scroll to the top and hit “buy me a coffee” at the top of the page.
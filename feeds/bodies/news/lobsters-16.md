<small>This image was created for use on this site using components taken from the Counter-Strike v1.5 mod for Half-Life owned by Valve Corporation. The copyright for the components are held by Valve Corporation while the copyright for these particular compositions are held by us.</small>

4. Installation
*Quick and dirty:* `curl -s https://www.frag-net.com/install_tacticalretreat.sh | bash`
Extract the release archive. If you don't already have the game data use [REWise](https://codeberg.org/CYBERDEV/REWise) to extract the content of *csv15full.exe* and merge the `cstrike` directory with the one from the archive.
You can then proceed to run the game with the `TacticalRetreat` script.

5. Building
Be familar with the `git` program, and you can clone [Nuclide](https://code.idtech.space/vera/nuclide), and then
within that directory clone the [cstrike](https://code.idtech.space/fn/valve) and [valve](https://code.idtech.space/fn/valve) repositories.
Then issue: `make game GAME=cstrike`   
to build the various pieces of game logic (in the form of QuakeC *.dat* files).

6. Credits

Spike for FTEQW and for being the most helpful person all around!
Xylemon for the hundreds of test maps, verifying entity and game-logic behaviour
Theuaredead`, preston22, dqus for various patches
To my supporters on [Patreon](https://www.patreon.com/eukara), who are always eager to follow what I do.
Any and all people trying it, tinkering with it etc. :)

7. License

ISC License  

Copyright (c) 2016-2026 Marco "eukara" Cawthorne   

Permission to use, copy, modify, and distribute this software for any  

purpose with or without fee is hereby granted, provided that the above  

copyright notice and this permission notice appear in all copies.  

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES  

WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF  

MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR  

ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES  

WHATSOEVER RESULTING FROM LOSS OF MIND, USE, DATA OR PROFITS, WHETHER  

IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING  

OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

8. FAQ
[8.1  Why do we need **Tactical-Retreat**?](https://www.frag-net.com/project_tacticalretreat.html#Why)

Because the original games aren't open, and I wanted to change that. There are tons of weapon mods for Counter-Strike on websites such as [ModDB](https://www.moddb.com/) and [GameBanana](https://www.gamebanana.com/) that could be turned into new weapons for purchase. You can basically build the CS server of your dreams. Make every LAN-Party personalized.

[8.2  What are the project goals?](https://www.frag-net.com/project_tacticalretreat.html#Goals)

Tactical-Retreat wants to be faithful to classic CS
It needs to be compatible with the existing custom content
Needs to be freely available to everyone

[8.3  Why might I want to use Tactical-Retreat?](https://www.frag-net.com/project_tacticalretreat.html#UseCase)

Being built from the ground up with hindsight and other modifications in mind, it's a lot simpler to get started creating custom objects. You can design whole weapons, items, NPCs (as well as their schedules) without writing a single line of code. This is due to *Nuclide's* data oriented design and the use of *id Tech 4 style* decl files.

Because it's built on *Nuclide*, it also has a different netcode, with weapon prediction standard across the board. There's also bots included with every game, as well as voting features and a *metamod inspired* plugin system, with a few ports of popular plugins.

Even gamerules can be swapped out on a whim, as they're simply external modules separated from the server to begin with.

[8.4  What platforms are supported?](https://www.frag-net.com/project_tacticalretreat.html#Platform)

Anything that the engine binary (provided by FTE QuakeWorld) runs on is supported. All components in *Tactical-Retreat* are platform/architecture independent. Being a QuakeC project has that benefit. This generally means that unless you are making engine modifications for your project, you will not need to port your project.

We've successfully tested it ourselves on **Linux**, **OpenBSD**, and **Windows**.

[8.5  How can I support the project?](https://www.frag-net.com/project_tacticalretreat.html#Support)

It is mainly orchestrated by Marco Cawthorne [which you can support on their Patreon](https://www.patreon.com/eukara). He also runs the [frag-net game network](https://www.frag-net.com/) that powers the on-line backbone of the project. Helping out with the costs that way is greatly appreciated. That said, expressing yourself in the [Matrix chat](https://matrix.to/#/#nuclide:matrix.org) can also nudge the project. If you're the type of person that knows exactly what we need and can lend a hand, be sure to reach out!

[8.6  Do I need to own Half-Life or Counter-Strike to play this?](https://www.frag-net.com/project_tacticalretreat.html#Branding)

No. The project includes enough of its own replacement data to be able to run the game solely from the freely available mod data. When running some custom maps however, that heavily depend on custom Half-Life content, you may not be able play them properly. This will improve over time.

*Tactical-Retreat logo by Vera Visions L.L.C.;
This site Copyright © 2025, 2026 Tactical-Retreat Project; FTE QuakeWorld is Copyright © 2002-2026 David Walton; Half-Life, and any associated characters belong to Valve Corporation. All Rights Reserved.  
[Back to frag-net.com - Projects](https://www.frag-net.com/projects.html)*
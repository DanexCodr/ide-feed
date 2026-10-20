The trend of VC-backed tooling ending in abandonment rears its ugly
   head again. But hey, people gotta eat, right? The community will pick
   up the slack and steward the projects, right?

Body

   Deno is dead.

   Announced[1] on a Friday[2], of course, the team has fled to
   Cloudflare and in a year, will stop working on the runtime. Kudos to
   them for finding an exit, Womp womp to us.

   This is the second time in just as many years that a technology I
   depend on is “given up to the community.” If you’re new here, Disc[3]
   came about because the team behind Gel fled to Vercel and gave their
   project up to the community. This was two years ago and as of this
   writing, no updates have been made on the “blessed” fork[4] of it.

   (Perhaps a bit petty of me to point out but someone in the Gel
   Discord has been rather hostile/cowardly about my efforts and thus I
   find delight in proving assholes wrong)

   The frustration of the Deno community is palpable and has created the
   best crashout[5] I’ve seen in some time:

   What the fuck do you mean Deno is ending development in a year????

   I JUST learned how to use this stupid runtime.

   I don’t give a fuck about your Cloudflare acquisition or your edge
   computing or whatever the fuck a Durable Object is.

   I JUST WANT TO RUN MY TYPESCRIPT FILES.

   Why is there a shutdown date????

   WHERE IS THE FUCKING DOWNLOAD BUTTON FOR MORE YEARS OF SUPPORT????

   I went to the releases page and there is no deno-forever.exe.

   WHY IS THERE NO deno-forever.exe?????

   Just compile another 10 years of development into a fucking
   executable and give it to me.

   I don’t want to learn Node.js again.

   I don’t want to migrate to Bun.

   I don’t want to understand your business model.

   I JUST WANT MY DINOSAUR BACK.

   You cannot just Deno.exit(0) an entire runtime.

   STUPID FUCKING CLOUD NERDS.

   Ryan Dahl’s comment[6] on HackerNews gave me pause (emphasis mine):

   It’s a joint decision and I agree with it. I’m most invested in its
   success and have put the most work into it - and I no longer think
   it’s where I can do the most important work. There are some
   good ideas in Deno and it’s well engineered - but it ultimately
   is not solving big problems. It has been sucked into the
   gravity well of node compatibility, which forces it to behave
   exactly as Node does. Why reimplement Node? It works. Marginal
   performance or UX or security benefits are not enough.

   …

   We’ll ship monthly releases for a year, and Deno stays
   MIT-licensed. If people want to carry it forward, I’d like that.

   My brother in Christ. YOU reimplemented Node and now you’re bored? I
   get it was done for adoption purposes but like, that’s a solvable
   problem? Whatever, this ain’t my first rodeo[7].

   There’s bound to be other forks but this one’s mine; I’m calling it,
   Ende (“end” in German). “Ende” is an anagram of “Deno” which is an
   anagram of “Node” and it’ll do things differently:

   — no more Node compatibility
   — no more distractions, period; that means Deploy, KV, Jupyter, &c
     are also getting the boot

   The roadmap? Per-module permissions, sandboxes for untrusted code,
   post-quantum crypto in Web Crypto, better binary output, &c. I depend
   on Deno for all of my APIs and personal projects, and now am building
   a serious business on it; EOL[8].

   I’m aiming for a soft launch in December so I can work out production
   kinks before a proper one. It’s gonna be quite the flex when Ende
   development is happening on EOL. Anyhoo, placeholder site for Ende[9]
   is up, subscribe to the mailing list if you want to be notified when
   it’s “official” (proper marketing and documentation websites). EOL
   also has a mailing list[8] if you want to know when the beta opens.

   I am very busy but excited. I wanted to build the Neue Internet[10]
   after all, looks like I’m getting my chance. 🕸️

   EDIT: I’m also replacing SemVer with ChronVer[11].
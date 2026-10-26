*Or, why we’re not seeing mass-exploitation of php2shell yet.*

*Update 2026-10-25: three days after the patch was available, the first public [evidence appeared](https://github.com/0x4D31/honeypot-data/blob/main/reports/php2shell/2026-10-24-confirmed-rce.md) of exploitation in the wild. This was a honeypot, presumably a low-traffic sensor. As far as I can tell, the technique matches my description below. So seems likely that at this point, mass-exploitation of low-traffic sites has begun. The constraints making exploitation of mid/high traffic websites unlikely, to my knowledge, still stand.*

*Update 2026-10-25: regarding high-traffic sites, a public $2k bounty on [stealmybitcoin.com](https://stealmybitcoin.com/) has not yet been claimed. However, Dan Guido of Trail of Bits, [claims](https://x.com/dguido/status/2113825891021144306) they have a reliable exploit that works under load. If so, that’s faster than I expected. I have not seen public confirmation, or what they mean by “under load.”*

*Update 2026-10-25: discussions on [lobste.rs](https://lobste.rs/s/xgih2x/i_want_my_wednesday_back) and [reddit](https://www.reddit.com/r/AskNetsec/comments/1xe4l6k/is_php2shell_only_practical_against_extremely/).*

*Update 2026-10-26: stealmybitcoin.com was not vulnerable the first 20 hours, then got hacked within hours using [this PoC](https://github.com/KillaBoi/StealMyBitcoin-PoC/). It uses a different technique: send one producer request, then consumer requests for all workers, and pipeline them to reduce chances of random other requests interfering. It does require that the final request ends up at the same worker, and the PoC README notes that the technique depends on knowing the exact worker count.*

*When multiple containers are behind a loadbalancer, each with their own ASLR layout, I don’t think this exploit would work. Possibly if you use number_of_workers * number_of_containers (assuming you somehow determine both) and keep hammering until you get very lucky and all requests of all stages end up in the same container. Session stickiness could change that, but is not a default for common load balancers and uncommon in mid/high traffic websites. In my experience HTTP pipelining also won’t force common load balancers to send all requests to the same container.*

*With what is currently known, I maintain that this was a critical vulnerability that should be patched asap, but recommending downtime was an overreaction for mid/high traffic websites. That response would be appropriate for a shellshock/heartbleed style vulnerability where the complexity is low, and mass exploitation can begin almost immediately after the patch is released. I’m concerned that if recommending downtime becomes normal for critical but complex vulnerabilities, the advice will get ignored when the next heartbleed or shellshock is found.*

*But if more information comes out, I’ll be happy to follow-up that I no longer want my Wednesday back.*

I saw wildly varying opinions on whether php2shell is serious, or if they cried wolf. Got curious, started digging into the PoCs. I’m not an exploit dev and maybe there were other factors, so take with a grain of salt. Egg on my face if mass exploitation starts right as I hit publish.

Best PoC of php2shell I’ve found: [https://github.com/9bie/php2shell-bypass-aslr-exp](https://github.com/9bie/php2shell-bypass-aslr-exp) (and a [fork with all docs translated to english](https://github.com/yanoshercohen/php2shell-bypass-aslr-exp-en))

To exploit, you need to do four consecutive *(correction: some of the requests need to be consecutive, not all four)* requests to **the same php worker process**. And you need to know the exact php build (php version, OS version, architecture), or try exploits for every possible build.

What this PoC does is take a docker image that uses the default mod_php number of workers, which is 150. Then it opens 149 connections that send half a request to keep the other workers busy, and does the four exploit requests against the 150th worker.

Even a moderately popular production website will have multiple web VMs/containers running multiple php workers behind a load balancer and constant bot traffic. That means you would have to try a wide range of number of connections to open. On top of that you likely won’t know the exact build version, so you would have to try exploits for every combination out there.

Let’s say you try this for the 50 most popular php/OS combinations, and any number of workers between 10 and 1010. That’s 50k attempts. But against constant background traffic, you would need to try each combination a number of times. Each of these attempts involves opening a whole lot of connections, so they each take some time. The PoC runs against localhost and takes 3-4 seconds, so let’s optimistically call it 10 seconds on the internet.

You can only do one attempt at a time, so that means multiple days of bruteforcing in a way that is essentially a DoS, since a large part of that range will exhaust the maximum number of connections. At this point the person running the site will likely notice, start blocking IP addresses or adding a WAF.

Most high-traffic websites already run WAFs/rate-limiting to deal with bot traffic, so you would need to run this attack from a great many IPs, and preferably clean ones that are harder to come by. But running this from many IPs also increases the chances that your timing will be off, reducing the number of plausible attempts even further.

That’s assuming the WAF doesn’t block your attempts entirely, because the easiest ways to exploit these vulnerabilities were known at the time of the announcement.

I’m sure people and agents will come up with clever techniques to reduce the required number of attempts eventually. But that has nothing to do with “this will get mass-exploited within 15 minutes.”

Against very low-traffic websites that do not have any bot protection, leak information about their version, running close to stock configuration, you might get lucky.

So sure, it’s a critical vulnerability, deserves attention, should be patched ASAP. Maybe even put in the announcement that if you’re running low-traffic sites, be extra sure to patch fast.

But to the AI security vendors who promoted this as THE GATES OF HELL WILL OPEN YOU HAVE TO PATCH WITHIN 15 MINUTES OR DIE? I want my Wednesday back.

<small>Oh and the claims of it being exploited in the wild? At time of writing, they’re referring to exploitation *attempts*. In fact, HoneyLabs [so far](https://infosec.exchange/@HoneyLabs/117483559117381472) hasn’t seen a single exploit attempt that could even run successfully.</small>
I like making little tools that do one thing well and thing finding clever ways to combine them. It's the ethos behind a lot of the little software projects I have over at [Less Software](https://less.software).

One of the first ones I made was a tool called [whereami](https://less.software/whereami/). Tongue-in-cheekly, I wanted to pitch it as the natural compliment to `whoami`. For that tool, the thinking was nearly every modern OS provides some kind of native API for geolocation. It felt silly to me that I could run a quick command from the terminal for so many things, but I couldn't run one that taps into this capability.

In the pursuit to make that tool cross-platform, one of the things I found myself navigating were the differences between them. Consistently, macOS tended to have a lot of extra niceties baked in, particuarly when it came to imagine recognition, natural language processing and accessibility tooling.

With geolocation, one of the nice things macOS provides that other OS-native approaches don't is a built-in geocoder (and reverse geocoder). So you can type in something like this:

```makefile
$ whereami

Location: 40.6753, -73.9431
Accuracy: 35m
Address: 865 St Marks Ave, New York, NY, 11213, US

$ whereami --json

{
  "latitude": 40.675265033592396,
  "longitude": -73.94310370569808,
  "accuracy": 35,
  "address": {
    "street": "865 St Marks Ave",
    "city": "New York",
    "state": "NY",
    "postal_code": "11213",
    "country": "US"
  }
}
```

And you get that handy little `address` block! It also makes it easy to do something like this:

```ruby
$ whereami "397 Bridge Street, Brooklyn NY"

Location: 40.6913, -73.9850
Address: 397 Bridge St, New York, NY, 11201, US

$ whereami "397 Bridge Street, Brooklyn NY" --json

{
  "latitude": 40.6913424,
  "longitude": -73.9850328,
  "accuracy": 0,
  "address": {
    "street": "397 Bridge St",
    "city": "New York",
    "state": "NY",
    "postal_code": "11201",
    "country": "US"
  }
}
```

Now you can grab the `latitude` and `longitude` coordinates for an address. And you get all of this "for free" no your macOS system. No t bad!

There's another handy framework macOS makes available to your system: MapKit. It's analgous to Google Maps and their API offerings, but native to the operating system.

It turns out it's pretty straightforward to build a CLI wrapper around that framework as well, so I made [nearme](https://less.software/nearme/) (macOS only).

They're designed to play well together:

```java
$ whereami --json | nearme "coffeeshop" --count=5

1. Cafe Imael (cafe)
   1090 St Johns Pl, New York, NY 11213
   +1 (718) 758-5857 · https://www.imael.co · 485 m

2. Zaim Coffee Shop (cafe)
   1102 St Johns Pl, New York, NY 11213
   +1 (347) 529-3444 · https://www.yelp.com/biz/zaim-coffee-shop-crown-heights · 500 m

3. Cheeni (restaurant)
   485 Tompkins Ave, New York, NY 11216
   +1 (347) 365-4015 · https://www.yelp.com/biz/cheeni-brooklyn · 589 m

4. Cotton Bean (cafe)
   1077 Bergen St, Brooklyn, NY 11216
   +1 (347) 276-8749 · https://www.cafecottonbean.com · 623 m

5. MoCo 575 (restaurant)
   531 Nostrand Ave, New York, NY 11216
   +1 (347) 365-3680 · https://moco575.com · 673 m

$ whereami --json | nearme "coffeeshop" --count=5 --json 

[
  {
    "name": "Cafe Imael",
    "address": "1090 St Johns Pl, New York, NY 11213",
    "latitude": 40.67105,
    "longitude": -73.942339,
    "phone": "+1 (718) 758-5857",
    "url": "https://www.imael.co",
    "category": "cafe"
  },
  {
    "name": "Zaim Coffee Shop",
    "address": "1102 St Johns Pl, New York, NY 11213",
    "latitude": 40.6710142,
    "longitude": -73.9416723,
    "phone": "+1 (347) 529-3444",
    "url": "https://www.yelp.com/biz/zaim-coffee-shop-crown-heights",
    "category": "cafe"
  },
  {
    "name": "Cheeni",
    "address": "485 Tompkins Ave, New York, NY 11216",
    "latitude": 40.6806663,
    "longitude": -73.9431295,
    "phone": "+1 (347) 365-4015",
    "url": "https://www.yelp.com/biz/cheeni-brooklyn",
    "category": "restaurant"
  },
  {
    "name": "Cotton Bean",
    "address": "1077 Bergen St, Brooklyn, NY 11216",
    "latitude": 40.6762179,
    "longitude": -73.950436,
    "phone": "+1 (347) 276-8749",
    "url": "https://www.cafecottonbean.com",
    "category": "cafe"
  },
  {
    "name": "MoCo 575",
    "address": "531 Nostrand Ave, New York, NY 11216",
    "latitude": 40.6791358,
    "longitude": -73.9493723,
    "phone": "+1 (347) 365-3680",
    "url": "https://moco575.com",
    "category": "restaurant"
  }
]
```

I can vouch for at least three of these coffeeshops!

When I was doing my pseudo-sabbatical at the Recurse Center this past spring, I spent a lot of time hammering away at these little tools and finding ways to combine them. Someone told me that the work I was doing and sharing reminded them of this idea you only need to control three points of focus to do a magic trick.

That comment inspired me to make this list of "recipes" where I try to showcase different ways to combine these tools in surprising, useful and/or fun ways:

But the one I want to write about specifically today is this "meet in the middle" idea.

I just showed you how you can use `whereami` and `nearme` to find coffeeshops (or anything you can find via Apple Maps) on your Mac. With a little piping and a convenient alias, you can help figure out a place to "meet in the middle" between you and and another point:

```bash
{ whereami "350 5th Ave, New York" --json; \
  whereami "200 Eastern Pkwy, Brooklyn" --json; } | \
  jq -s '{latitude: (map(.latitude) | add / 2),
          longitude: (map(.longitude) | add / 2)}' | \
  nearme "bar" --count=3
```

```java
1. Deux Chats (nightlife)
   27 Broadway, New York, NY 11249
   +1 (917) 909-0145 · https://www.deuxchatsbk.com · 575 m

2. Bar Milagro (nightlife)
   29 Dunham Pl, New York, NY 11249
   +1 (929) 298-0032 · https://www.xolobk.com/barmilagro · 617 m

3. Cafe Susanne (nightlife)
   8 River St, Brooklyn, NY 10044
   https://www.barsusanne.com · 651 m
```

There you go! No API keys or browser or accounts: just input a couple addresses and a few plausible bars come out on the other side.

## How it works

It's three small tools, each doing one thing.

**[whereami](https://less.software/whereami/)** started life as a CLI that asks your operating system where you are. As of 0.4 it can also act like a reverse geocoder (on macOS):

```bash
$ whereami "350 5th Ave, New York" --json
{"latitude":40.7482378,"longitude":-73.9850579,"accuracy":0,"address":{"street":"350 5th Ave","city":"New York","state":"NY","postal_code":"10118","country":"US"}}
```

Looking up an address doesn't need location permission, because nothing is asking where you are. **jq** does the arithmetic. The `-s` flag slurps both JSON objects into an array, and the filter averages the coordinates:

```json
{"latitude":40.7097896,"longitude":-73.9743696}
```

**[nearme](https://less.software/nearme/)** searches for places around a set of coordinates using MapKit, the search engine behind Apple Maps. It reads coordinates from JSON on stdin, and it only cares about `latitude` and `longitude`. It has no idea those numbers came out of `jq` and not out of a GPS.

Averaging two coordinates is not the "real" way to find the middle, but over a few miles trying to find a place to meet for coffee it's close enough. What does matter is that the midpoint has no idea what's actually there.

## Make it a command

Typing that pipeline more than once get annoying quickly. It's more convenient to set it up as a function:

```bash
middle() {
  local second=()
  # Two addresses only if a third argument is there to be the search term
  if [[ $# -ge 3 && $3 != -* ]]; then
    second=("$2")
    set -- "$1" "${@:3}"
  fi
  { whereami "$1" --json; whereami "${second[@]}" --json; } |
    jq -s '{latitude: (map(.latitude) | add / 2), longitude: (map(.longitude) | add / 2)}' |
    nearme "${2:-coffeeshop}" "${@:3}"
}
```

Or if you're using fish, like me:

```fish
function middle --description 'Search for places halfway between two addresses, or between you and one'
    set -l second
    # Two addresses only if a third argument is there to be the search term
    if set -q argv[3]; and not string match -q -- '-*' $argv[3]
        set second $argv[2]
        set -e argv[2]
    end
    begin
        whereami $argv[1] --json
        whereami $second --json
    end | jq -s '{latitude: (map(.latitude) | add / 2), longitude: (map(.longitude) | add / 2)}' | nearme (set -q argv[2]; and echo $argv[2]; or echo coffeeshop) $argv[3..]
end
```

Give it two addresses and something to look for. Anything after that goes straight through to nearme. Leave off the second address and it uses wherever you are right now, so `middle "123 Main Street" coffee` finds coffee between you and 123 Main Street. With only an address, it looks for a coffeeshop.

```bash
$ middle "350 5th Ave, New York" "200 Eastern Pkwy, Brooklyn" coffee --count=2
1. Cafe Susanne (nightlife)
   8 River St, Brooklyn, NY 10044
   https://www.barsusanne.com · 651 m

2. Social House Cafe (cafe)
   60 Broadway, Brooklyn, NY 11249
   +1 (929) 295-0397 · https://www.socialhousecafellc.com · 697 m
```

## Caveats

- It's macOS only. nearme is built on MapKit, and whereami's address lookup only exists on macOS.
- It wants street addresses or city names, though landmarks will work soetimes. "Golden Gate Bridge" doesn't geocode but "350 5th Ave, New York" and "Central Park" and "Brooklyn Briddge" do (caveat emptor).
- The math is a very literal and naive geographic middle, not taking travel-time middle or anything else into consideration.

## Try it

```bash
brew install georgemandis/tap/whereami georgemandis/tap/nearme jq
```

Both tools live under [Less Software](https://less.software):

Let me know if you find it useful or stumble across other good ideas for "[recipes](https://less.software/recipes)" to share!

*If you enjoyed reading this consider [sponsoring my work](https://github.com/sponsors/georgemandis) on GitHub or [subscribing](https://buttondown.com/georgemandis) to my newsletter.*

*Share this post: [Hacker News](https://news.ycombinator.com/submitlink?u=https%3A%2F%2Fgeorge.mand.is%2F2026%2F11%2Flets-meet-in-the-middle%2F&t=Let's%20Meet%20in%20the%20Middle) • [Reddit](https://www.reddit.com/submit?url=https%3A%2F%2Fgeorge.mand.is%2F2026%2F11%2Flets-meet-in-the-middle%2F&title=Let's%20Meet%20in%20the%20Middle) • [LinkedIn](https://www.linkedin.com/sharing/share-offsite/?url=https%3A%2F%2Fgeorge.mand.is%2F2026%2F11%2Flets-meet-in-the-middle%2F) • [Mastodon](https://share.joinmastodon.org/?text=Let's%20Meet%20in%20the%20Middle%0A%0Ahttps%3A%2F%2Fgeorge.mand.is%2F2026%2F11%2Flets-meet-in-the-middle%2F).*

*Published on Tuesday, November 17th 2026. Read this post as [plain-text](https://george.mand.is/2026/11/lets-meet-in-the-middle.txt).*
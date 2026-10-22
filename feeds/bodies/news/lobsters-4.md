The other day I read this blog post about using arp-scan to list every device on the network in order to keep better track of devices and that's great, but we can go even further.

The blog post I am talking about is Ben Calderon's post called [ARP! Tell your network to explain itself](https://benjcal.space/blog/arp-tell-your-network-to-explain-itself/).

I too have too many devices on my network to keep track (it both serve some of my homelab stuff and some of my office stuff) and as such, I have used different approaches over the years.

One of the early things I did was to give each device a meaningful hostname. Like "johnslaptop", "janesdesktop", "webserver", "storageserver", etc. But as you probably know, this quickly becomes problematic when you get more machines that does the same, so "webserver" turns into "oldwebserver" or you use "webserver1" and "webserver2" and then forget which is actually which. Also, when machines change hands, you have to rename them so "johnslaptop" now becomes "alexlaptop", etc.

A better approach is to use a naming convention. This is especially useful if you run a large network with many devices, then you can use a scheme like "region.location.devicetype.unitnumber". On the homelab many people choose character names from one of their favorite movies or TV shows and use those as hostnames, like "homer", "marge", "bart", etc.

The benefit of character names is that the name doesn't need to change if the device is used for something else or it changes hands. But the downside is that now it's even more difficult to remember what device does what.

Also, in both cases, you cannot remember what IP address belongs to what machine.

Using arp-scan in order to take advantage of the [Address Resolution Protocol](https://en.wikipedia.org/wiki/Address_Resolution_Protocol) (ARP) is a great way to determine which IPv4 devices are up and running on your network and it's much faster than scanning with nmap.

```
$ $ arp-scan 192.168.1.0/24
Interface: eth0, type: EN10MB, MAC: 1g:36:4f:16:a2:3a, IPv4: 192.168.1.5
Starting arp-scan 1.10.0 with 256 hosts (https://github.com/royhills/arp-scan)
...
192.168.1.5     b0:56:9a:e1:66:b9       Intel Corporate
192.168.1.12    1a:83:04:16:d4:a3       (Unknown)
192.168.1.23    30:ab:d6:d2:b3:36       ASUSTek COMPUTER INC.
...

15 packets received by filter, 0 packets dropped by kernel
Ending arp-scan 1.10.0: 256 hosts scanned in 2.018 seconds (126.86 hosts/sec). 15 responded
```

If you're using IPv6 then arp-scan will not work as IPv6 uses [Neighbor Discovery Protocol](https://en.wikipedia.org/wiki/Neighbor_Discovery_Protocol) (NDP) rather than ARP, but I am sure you already know this if you have implemented IPv6 in your network.

In the above result from arp-scan we get the IP address, the MAC address and sometimes, but only sometimes, the vendor of the NIC. Still, this is only really useful to tell me which devices are up and running, from the above I cannot determine what is what. Especially with the 192.168.1.12 one which doesn't list the vendor. And sometimes you have several machines using the same NIC vendor.

DNS to the rescue!

A really cool thing about using a DNS server on your network, even if you only have a limited amount of devices, is that you get a kind of centralized "database" which you can then setup with information about all the devices. If you also combine it with a DHCP server, you can easily match a specific IP address to a specific MAC address and that way always make sure that the same device automatically gets the same IP address and you don't have to manage that on each device.

One minor downside to using DHCP and DNS is that if the server is down, perhaps because you're updating the operating system, your network is momentarily not working quite right, machines cannot get IP addresses assigned and you cannot use DNS to do lookup. However, you can mitigate that somewhat by only assigning static IP addresses to the very most important devices and then make sure the IP addresses match the ones you use in your DNS zones.

However, the really cool thing is that you can use the [TXT record](https://en.wikipedia.org/wiki/TXT_record) to associate arbitrary text with a host!

I the above case with 192.168.1.12, not only can I lookup the hostname of the device with `drill` or `dig`:

```
$ drill -x 192.168.1.12
;; ANSWER SECTION:
12.1.168.192.in-addr.arpa. 3600  IN      PTR     bart.home.arpa.
```

I can also get the very useful information from the TXT record I previously setup:

```
$ drill bart.home.arpa TXT
;; ANSWER SECTION:
bart.home.arpa.        3600    IN      TXT     "Johns Intel i7-7700 Acer laptop"
```

In my network I am using [OpenBSD as a router](https://unixdigest.com/openbsd-router-guide/) and I am combining [dhcpd](https://man.openbsd.org/dhcpd) with [unbound](https://nlnetlabs.nl/projects/unbound/about/), that way I only have to enter the IP address for a device in one place.

So the section for the bart.home.arpa machine in `/etc/dhcpd` looks like this:

```
host bart.home.arpa {
    fixed-address bart.home.arpa;
    hardware ethernet 1a:83:04:16:d4:a3;
}
```

Then in unbound I have the following:

```
local-data: "bart.home.arpa. IN A 192.168.1.12"
local-data: 'bart.home.arpa. IN TXT "Johns Intel i7-7700 Acer laptop"'
local-data-ptr: "192.168.1.12 bart.home.arpa"
```

You only have to make sure that dhcpd is started after unbound when the router boots. dhcpd uses the `fixed-address` field to query the DNS server (unbound in this case) for the IP address that belongs to that hostname in order to serve it to the device with the specific MAC address listed in the `hardware ethernet` field.

You can do the same setup on something like a Raspberry Pi using almost any Linux distribution or BSD variant, or you can use something like like [Pi-hole](https://pi-hole.net/) with [Dnsmasq](https://thekelleys.org.uk/dnsmasq/doc.html), which has both DHCP and DNS build into one.

Even if you decide to manually assign static IP address to all devices and not use DHCP at all, having a DNS server as a "database" with hostnames and additional information is really nice, you just have to make sure everything matches when you set it up.

Another major benefit from running a local recursive DNS resolver like unbound is that you become your own DNS provider and do not need your ISP, Google, Cloudflare or anyone else as a DNS provider. You can also block websites, like websites that serve ads or machines that are setup to collect telemetry.
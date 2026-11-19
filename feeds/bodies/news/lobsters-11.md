Running a custom x64 router has a lot of upsides. One, it runs mainline Linux, so it gets updates quickly. Two, router adblocking. 'Nuff said. And three, if something breaks, you get to dive in deep and figure out what's going wrong.

This week, I had a really interesting time with my custom setup. I noticed that if I'd restart `pppd` (which connects to my ISP), Google would stop working. It would still resolve, but I couldn't reach it.

## Diagnosis

I have a stack where `networkd` is responsible for the network in general, with `pppd` dialing in to my ISP, `kea-dhcp4` handing out DHCPv4 addresses, `blocky` handling DNS (on the router as well as the laptop) and `networkd` itself handling RA. As far as I knew, there was nothing wrong in this stack at all. All the daemons themselves are battle-tested and known to be working fine.

So maybe this was a problem with my laptop?

```
~ ❯ ping -c 4 google.com
PING google.com (2404:6800:4013:813::64) 56 data bytes
--- google.com ping statistics ---
4 packets transmitted, 0 received, 100% packet loss, time 3064ms

~ ❯ ip addr
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host noprefixroute
       valid_lft forever preferred_lft forever
2: wlan0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default qlen 1000
    link/ether 00:00:5e:00:53:01 brd ff:ff:ff:ff:ff:ff
    inet 192.168.2.148/24 brd 192.168.2.255 scope global dynamic noprefixroute wlan0
       valid_lft 4130sec preferred_lft 4130sec
    inet6 2001:db8:aaaa:1::10f1/64 scope global temporary dynamic
       valid_lft 3090sec preferred_lft 1290sec
    inet6 2001:db8:aaaa:1::1a03/64 scope global dynamic mngtmpaddr noprefixroute
       valid_lft 3090sec preferred_lft 1290sec
    inet6 2001:db8:bbbb:2::bea0/64 scope global temporary dynamic
       valid_lft 3554sec preferred_lft 1754sec
    inet6 2001:db8:bbbb:2::690f/64 scope global dynamic mngtmpaddr noprefixroute
       valid_lft 3554sec preferred_lft 1754sec
    inet6 fe80::5b9c/64 scope link noprefixroute
       valid_lft forever preferred_lft forever
```

One `ping` told me that Google was getting resolved to its IPv6 address, which exonerated DNS, but I couldn't ping it. An IPv4 address on the other hand, worked fine.

On the other hand, `wlan0` showed 2 groups of IPv6 addresses with the older IPv6 address having a preferred lifetime greater than 0. Could this be the culprit? I restarted `NetworkManager`, and lo and behold, Google magically started working again and I was down to just one group of IPv6 addresses, the newer ones.

## Solutioning

I've never debugged networks in depth, but the problem here seemed to be fairly simple to grasp. Whenever `pppd` restarts, it negotiates a new connection with my ISP, which provides a new prefix to my router for delegation. However, no device drops the old IPv6 address. At first I thought this was NetworkManager's fault, but then I saw my iPhone do the same thing. Two points don't make a pattern, but they do make a line. Which pointed straight at `networkd`.

Don't get me wrong. I like `networkd`. The only reason I have `NetworkManager` on my laptop is because it's purpose built for Wi-Fi and roaming and it's never let me down yet (`iwd` ftw). My router and server both run `networkd`. It's a very comfortable, no-nonsense daemon. So I was reluctant to blame it. So I turned to `pppd` instead as a cop-out.

I decided to ensure that `pppd` would never restart when I'd redeploy my NixOS router. But unfortunately, I've had times when my ISP has randomly hiccoughed and `pppd` reconnects to it leading to the same problem all over again. Which meant I'd have to get to the bottom of this.

A little bit of searching led me to [RFC 9096](https://www.rfc-editor.org/rfc/rfc9096.html), *Improving the Reaction of Customer Edge Routers to IPv6 Renumbering Events*, which tightens [RFC 7084](https://www.rfc-editor.org/rfc/rfc7084.html), *Basic Requirements for IPv6 Customer Edge Routers*. Basically, whenever a new prefix is given to the router and the old one dropped by upstream, the router needs to advertise the old prefix with preferred and valid lifetimes of `0` which causes consumers of the router advertisement to stop using it as a source address.

Interestingly, `networkd` has an issue [RFC 7084 support in networkd (automatic ipv6 range delegation)](https://github.com/systemd/systemd/issues/4073) where a requirement for properly implementing RFC 9096 came up in September 2026. There's a [patch](https://github.com/systemd/systemd/pull/34244) as well which hasn't yet been merged. The same issue has been [brought up with radvd on OPNsense](https://github.com/opnsense/core/issues/9261) and closed as "not planned", as well as with [dnsmasq on OPNsense](https://github.com/opnsense/core/issues/11028). [VyOS's dynamic-prefix support is still an open request](https://vyos.dev/T5795). Which meant that the usual suspects were out. There's only one option left, and it's not available on NixOS. [`odhcpd` from OpenWrt](https://git.openwrt.org/project/odhcpd), which actually *does* implement [RFC](https://github.com/openwrt/odhcpd/commit/86c0200f80) [9096](https://github.com/openwrt/odhcpd/commit/cdb9e5b655).

I was a bit wary of relying on an OpenWrt package. Not because I think there's anything wrong with OpenWrt (quite the contrary!), but because the distribution itself is unusual. It doesn't use `systemd` or `dbus`, instead using `procd` as pid1 and uses `ubus` for IPC. I know that many of their packages depend on these two pieces of infrastructure to function, so that was the first thing I checked. Fortunately, `odhcpd` is unusual in that it can get information from the kernel directly through netlink and can be configured without the need for `ubus`, so that was not a blocker. Packaging it took me a while, but I [submitted it for review to nixpkgs](https://github.com/NixOS/nixpkgs/pull/586551) and began running it on my router, switching off router advertisement on `networkd`. I could have used `odhcpd` for DHCP as well, but I was fairly happy with `kea-dhcp4` so I left it alone.

And lo and behold, when I deliberately restarted pppd, I got:

```
~ ❯ ip -6 addr show scope global
2: wlan0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 state UP
    inet6 2001:db8:cccc:3::5286/64 scope global deprecated dynamic mngtmpaddr noprefixroute
       valid_lft 5325sec preferred_lft 0sec
    inet6 2001:db8:dddd:4::dcaa/64 scope global temporary dynamic
       valid_lft 5338sec preferred_lft 2638sec
    inet6 2001:db8:dddd:4::8a09/64 scope global dynamic mngtmpaddr noprefixroute
       valid_lft 5338sec preferred_lft 2638sec

~ ❯ ip -6 route get 2606:4700:4700::1111
2606:4700:4700::1111 from :: via fe80::1 dev wlan0 proto ra src 2001:db8:dddd:4::dcaa metric 100 pref medium

~ ❯ ping -6 -c3 2606:4700:4700::1111
3 packets transmitted, 3 received, 0% packet loss, time 2003ms
rtt min/avg/max/mdev = 6.289/8.147/9.487/1.356 ms
```

Success! The best thing was that `odhcpd`'s memory is persistent across reboots and is agnostic to the time set on your machine. This is pretty important for me, because I haven't replaced the dead CMOS battery on my router and the clock resets every time the router restarts. This allows `odhcpd` to advertise old prefixes with the correct preferred/valid lifetime of 0 after every reboot without caring about when they were delegated. In practice, this would matter if my router loses power while my Wi-Fi access point remains up, or if I reboot my router (which definitely does happen often). Given my family's reliance on the home network remaining up, I'd rather cover all cases.

My euphoria lasted until I got onto my iPhone, where the old address lingered on my screen. I switched off mobile data to check (iOS silently routes to mobile data where Wi-Fi fails, a service called Wi-Fi Assist) and the same problem persisted for a few minutes before the address changed and the problem resolved on its own.

Took me a bit of packet capture to work out, but it became clear what had happened. The router advertisement had gone out as soon as the prefix had arrived, but the phone was sleeping and missed it. It caught the next advertisement when it was awake and in my hands. This shows us that dropping prefixes is *prompt*, but not *instant*. It took around 10 minutes for my phone to pick the new one up. `networkd` advertises times of 30/60 mins for preferred/valid respectively, while `radvd` advertises times of *4/24 hours* by default. `odhcpd` conforms to the recommendations of RFC 9096 by advertising 45/90 mins.

## Usage and conclusions

`odhcpd` behaves slightly differently from its natural home in OpenWrt when deployed on another distribution. It cannot be updated via `ubus` (note: it technically can because `ubus` is packaged in NixOS, but I wasn't using it here) so it can only get interface names at startup and it gets state by talking to the kernel, not from `ubus`. The NixOS module ties it to device units so that it picks them up at startup. It also differs quite a bit from `networkd`'s behaviour. For example, `networkd`, reloading its config, would send a `router-lifetime-0` goodbye message, which `odhcpd` doesn't (which is correct here, because `odhcpd` being down does not imply the router being down). This would cause a brief network disruption where for a moment, everything connected to my network would lose IPv6 capability momentarily as `networkd` reloaded. And finally, when `pppd` would go down, `odhcpd` advertises a router lifetime of 0, implying there's no default route available, telling clients to not use it as a gateway.

The takeaway for me was quite simple. I usually prefer using systemd utilities wherever possible. I prefer `networkd`, I don't use a separate syslog daemon, I feel like `udev` is my friend, and so on. However, that holds true when the machine is a client. As soon as the machine has to behave as a server to another machine, I'd prefer to fall back to specialised tools. Hence, my router has `chrony` instead of `systemd-timesyncd`, `blocky` instead of `systemd-resolved`, and `kea-dhcp4` and now `odhcpd` in place of `systemd-networkd`'s DHCP and router advertisement functionality. There's enough edge cases that getting dedicated tools there just makes more sense.

But more than that, I heartily recommend `odhcpd`. I don't know whether I'd want to replace `kea-dhcp4` with it or not, but as a router advertisement daemon it's the best one I've found for a home network connecting to a consumer ISP.
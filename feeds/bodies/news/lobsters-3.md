There might be time you want to have a sensible space in that untangible mess that is modern World Wide Web. The choices run slim and at some point there are ~three operating systems that you can trust having on your server<sup>[1](https://bsandro.tech/posts/simple-netbsd-webserver/#fn:1)</sup>.

I’ll describe here the quick and proven route for running a **NetBSD 11** web server - the ‘stock’ way with **bozohttpd** that requires only one additional package for HTTPS<sup>[2](https://bsandro.tech/posts/simple-netbsd-webserver/#fn:2)</sup>. It probably won’t do if you expect heavy traffic, but for homebrew projects and small scale communities it should do just fine.

## Prerequisites

A VPS (or local machine or virtual machine) and a terminal emulator.

Maybe web-browser to check the results (though `curl` is quite sufficient for that imo).

## VPS

I’m not affiliated but as far as recommendations go - I’m using [netcup](https://www.netcup.com/en) service, it looks okay. Not expensive and they already have NetBSD11 amd64 iso preloaded in their OS library to install OS on your machine.

There are others people recommend for netbsd - namely [panix](https://www.panix.com/) and [mythic beasts](https://www.mythic-beasts.com/).

If you can recommend or suggest even more - please email me, I’ll make a proper list.

## Running bozohttpd

NetBSD has a small web-server that is sufficient for tons of stuff right out of the box - `bozohttpd(8)`. It is somewhat limited by design, but the manpage is quite useful and describes a lot of interesting stuff you can do with just marker files and simple command line options.

Some guides out there explain a path to run it using `inetd(8)`, it is kinda native internet “super-server” for unix but I didn’t like that it launches an instance of httpd (alias/hardlink to bozohttpd) on every connection. Bozohttpd is capable running as daemon itself, I like that option.

The only config httpd needs lies in command line options, which can be nicely wrapped in `/etc/rc.conf` with self-explanatory keys like this:

```
httpd=YES
httpd_wwwuser=nobody
httpd_wwwdir=/var/www/my_magical_domain
```

If you have something in /var/www/my_magical_domain/index.html, then after simple `/etc/rc.d/httpd start` voila - you already have it served via plain http. Simple as that.

## Using HTTPS

I won’t explain usage of self-signed procedure, instead resorting to one of the most popular freeware certificate issuer on the internet - letsencrypt.

There are several methods of obtaining the certificates from them, I’m using `acme-client` package (installed via `pkgin`) - it is a portable version of an openbsd tool, I’m most used to it.

We need couple more directories to expose our challenge and to keep the certificates on. Try to not use “4” as a private key - it’s been exposed recently, stick with prime numbers at least :)

```
mkdir -p /etc/ssl/private
mkdir -p /var/www/my_magical_domain/.well-known/acme-challenge
```

And we need a config file for our domain - **/usr/pkg/etc/acme-client.conf**:

```
authority letsencrypt {
	api url "https://acme-v02.api.letsencrypt.org/directory"
	account key "/usr/pkg/etc/acme/letsencrypt-privkey.pem"
}

domain my_magical_domain {
	alternative names { www.my_magical_domain }
	domain key "/etc/ssl/private/my_magical_domain.key"
	domain full chain certificate "/etc/ssl/my_magical_domain.fullchain.pem"
	challengedir "/var/www/my_magical_domain/.well-known/acme-challenge"
	sign with letsencrypt
}
```

Running `acme-client my_magical_domain` should do the trick and put the neccessary certs to their corresponding paths. Do not forget to wait for at least few hours after putting your vps IP address into domain A record - it has to be propagated everywhere properly and resolve for letsencrypt as well.

Afterwards we have to pass the keys to the bozohttpd, and that enables it serving the port 443 automatically. So an addition to /etc/rc.conf should look like this:

```
httpd_flags="-Z /etc/ssl/my_magical_domain.fullchain.pem /etc/ssl/private/my_magical_domain.key"
```

Restart httpd and Bob’s the uncle - we have a working web server showing whatever static files you put into the directory.

Now there is one more thing to that - Letsencrypt certificates expire after certain amount of time, so we have to renew them using same `acme-client(1)` program. The simplest way to do so would be a cronjob - daily or even weekly - that tries to update the certificate and then restarts the httpd, via `crontab(5)`:

```
0 2 * * 1 /usr/pkg/bin/acme-client my_magical_domain && /etc/rc.d/httpd restart
```

## Notable features

Despite being spartan Bozotic httpd supports some interesting features like **virtual hosts** (you can serve each domain bound to your IP from different directory), **CGI** and **http basic authorization**.

Another interesting feature I’d like to try out sometime is native **Lua scripting**.

**URL rewrites** also looks promising - especially when coupled with CGI to seamlessly provide some feedback and interactivity (visitors’ count haha).

`bozohttpd(8)` manpage contains quite a lot of useful info, don’t forget to check it out.
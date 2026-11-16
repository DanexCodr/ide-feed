FreeBSD pkgbase finally brings the base OS to you as discrete packages
instead of monolithic tarball "package sets". However, if you want to
deploy a lot of systems or FreeBSD jails you will be hitting the
official FreeBSD mirrors repeatedly which is not ideal. I have my own
internal package repository where I build packages from source, but I
don't do that for the base OS and do not intend to; there's really no
changes that I would want to make to the builds and having the base OS
match the official upstream releases is important for ensuring their
integrity and being able to report any bugs you encounter.

This problem started to become very obvious to me when I was converting
all of my FreeBSD jails to pkgbase deployments as the process wasn't
caching the packages anywhere locally and each conversion was hitting
the official mirrors over and over -- 36 times if I didn't intervene.
This is a lot of bandwidth wasted when I could just mirror it locally.
So I did, and this is how you can do it too.

## Apache

Believe it or not, I'm still using Apache for a few things. If someone
wants to share a similar configuration for Nginx I'll publish that as
well.

The one thing that bit me was that initially I pointed the reverse proxy
configuration to `pkg.freebsd.org`. This won't work because that server
will redirect you to a CDN and Apache won't read through the redirect
and cache it, so I pointed directly to the CDN right now. This
absolutely will change in the future when the CDN is completely hosted
by the FreeBSD project again, but for now this is the requirement.

```

<IfModule !cache_module>
  LoadModule cache_module libexec/apache24/mod_cache.so
</IfModule>

<IfModule !cache_disk_module>
  LoadModule cache_disk_module libexec/apache24/mod_cache_disk.so
</IfModule>

<IfModule !ssl_module>
  LoadModule ssl_module libexec/apache24/mod_ssl.so
</IfModule>

<IfModule !proxy_module>
  LoadModule proxy_module libexec/apache24/mod_proxy.so
</IfModule>

<IfModule !proxy_http_module>
  LoadModule proxy_http_module libexec/apache24/mod_proxy_http.so
</IfModule>

CacheRoot          /var/cache/apache-pkg
CacheDirLevels     2
CacheDirLength     1

CacheIgnoreQueryString   On
CacheIgnoreCacheControl  On
CacheIgnoreNoLastMod     On
CacheIgnoreHeaders       Set-Cookie
CacheMaxFileSize         1073741824
CacheMinFileSize         1024
CacheDefaultExpire       31536000
CacheDetailHeader        On

<VirtualHost *:80>
    ServerName pkg.feld.me
    DocumentRoot /var/repos/

    Alias /robots.txt /usr/local/www/apache24/data/robots.txt

    # Where my local package repos are
    <Directory /var/repos/>
      AllowOverride none
      Options Indexes FollowSymLinks
      Require all granted
    </Directory>

    # pkgbase: reverse proxy, cache ONLY the immutable Hashed/blobs
    SSLProxyEngine On
    <LocationMatch "^/pkgbase/[^/]+/[^/]+/Hashed/">
      CacheEnable disk
    </LocationMatch>

    CacheQuickHandler off

    ProxyRequests     Off
    ProxyPreserveHost Off
    # Have to use the CDN directly to not chase redirects
    ProxyPass         /pkgbase/ https://cloudfront.aws.pkgbase.freebsd.org/ connectiontimeout=30 timeout=600
    ProxyPassReverse  /pkgbase/ https://cloudfront.aws.pkgbase.freebsd.org/

    #    LogLevel cache:debug

</VirtualHost>
```

Now on my servers I just change the repo config for the `FreeBSD-base` repo to:

```

FreeBSD-base: {
  url: "https://pkg.feld.me/pkgbase/${ABI}/base_release_${VERSION_MINOR}",
  mirror_type: "none",
  enabled: yes
}
```

Something I should consider is publishing an SRV record that falls back to the official mirror if my webserver is down, but I haven't bothered with that yet.
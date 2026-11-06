This was my first time upgrading NetBSD and I’m happy with how it all turned out!

[NetBSD’s Guide](https://www.netbsd.org/docs/guide/en/chap-upgrading.html) describes two different methods for performing an upgrade: boot from NetBSD install media and use `sysinst(8)`, or use `sysupgrade(8)` to do an in-place upgrade of the system. With a bit of research, I get the sense that for major version changes (i.e 10.1 -> 11.1) `sysinst` is the preferred method, while `sysupgrade` is a convenient alternative for minor version bumps.

So `sysupgrade` it is. First, I install the package:

```
# pkgin update
# pkgin install sysupgrade
```

Then simply run:

```
# sysupgrade auto https://cdn.netbsd.org/pub/NetBSD/NetBSD-11.1/$(uname -m)/
```

This will proceed to download the kernel and sets appropriate for your computer, unpack them, then prompt you to review and merge new configuration changes. There were only a few files that needed hands-on editing like `passwd` and `sshd_config` and I liked how NetBSD shows the diffs between the old and new files and its handling of merging differences.

I had one postinstall check that failed:

```
# postinstall checks failed: opensslcertsrehash
```

I resolved the issue by wiping the legacy cache, then letting `certctl(8)` take over by rehasing the certs:

```
# rm -rf /etc/openssl/certs/*
# certctl rehash
```

Verify `certctl` successfully populated the directory:

```
# certctl list
```

I manually re-run `postinstall fix [issue]` and confirm that it now passes inspection (which it did):

```
# sysupgrade postinstall fix opensslcertsrehash
# sysupgrade clean
```

Reboot the computer and start enjoying the upgrade!

**NOTE**  

In addition, edit `/usr/pkg/etc/pkgin/repositories.conf` and point `pkgin` to the new `11.1` repositories.
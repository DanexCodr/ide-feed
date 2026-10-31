# Shrinking NixOS Ram footprint and resource requirements to the bare minimum.

A few people were surprised by how low you can go with NixOS, so i thought I would do a write up as I did not realise this was anything special, I kept notes when doing it but not for the intention of writing a blog article so i might miss small tweaks I did here and there.

I initially set aside half a day for this; it actually took closer to 3 days.

This guide is not very focused on saving disk space. If you want a disk space saving guide that has already been done by someone else here: [https://nixcademy.com/posts/minimizing-nixos-images/](https://nixcademy.com/posts/minimizing-nixos-images/) this has its own set of challenges and drawbacks so if you want to layer them together, be my guest ![:)](https://lowendspirit.com/plugins/emojiextender/emoji/twitter/smile.png) I have decided not to implement the disk-minimising options into the TierHive NixOS template as I feel it is too likely to cause a default that end users are unlikely to expect.

Here we go:

# NixOS 26.05 idling at around 96MB and rebuilding in 512MB

Stock deployment before any changes and with cloud-init, it runs on 1024MB RAM, JUST!, it sat at 288MB used with 89 kernel modules loaded, and a plain same-release rebuild needed 896MB (at 768 nix-build got OOM-killed at 505MB anon).

It now idles at 96MB used on a 512MB VPS with 54 modules, and a full channel update plus rebuild, including a kernel switch to 7.3 if you want to do that, It finishes at 512MB with a 371MB peak and no OOM. All numbers are from my own runs sometimes I recorded exact numbers others I left out the KB's and only recorded the MB's ![:)](https://lowendspirit.com/plugins/emojiextender/emoji/twitter/smile.png) , measured a few minutes after the second boot with nobody logged in using my own build environment testing tools (I never log in to templates before use so they are clean)

Roughly in the order and things done on this template (even the harmless fails):

- sysctl.vm.mem_profiling=never on the cmdline. The NixOS kernel ships with allocation profiling enabled by default and the tracking tables cost about 6MB (3.9MB vmalloc, 1.9MB slab). the bare mem_profiling=never which is left in isn't a valid parameter; the kernel juts hands it to userspace and nothing changes, it needs the sysctl. prefix.
- kfence.sample_interval=0 gets back the 2MB KFENCE pool.
- damon_stat.enabled=N and audit=0 get rid of the kdamond and kauditd threads.
- initcall_blacklist=ksm_init,tpm_init,init_tis drops ksmd (1.4MB) and the TPM bits (0.3MB plus a kthread). No TPM in these guests and KSM inside a guest is pointless. (For TierHive anyway)
- psi=0 ras=cec_disable nowatchdog nmi_watchdog=0 cryptomgr.notests 8250.nr_uarts=1 are all small, mostly fewer kthreads and less noise. On a 2GB test VM the whole cmd line set took non-cache memory from 128.0 to 121MB and kthreads from 64 to 59.
- transparent_hugepage=never was one of the biggest single wins. With THP on madvise the kernel bumps vm.min_free_kbytes to 41108 (3710 without THP at 896MB), which is reserved memory you never get to use. Turning it off freed 52MB at 2GB and gave 103MB more available at 896MB, obviously in high end or production there are reasons not to do this, but day to day use, you probably wont notice any difference.
- Blacklisted the hardware a KVM guest never has or doesn't need: floppy, intel_agp, i2c_piix4, psmouse, mousedev, joydev, serio_raw, evdev, button (using tiny_power_button already handles ACPI shutdown), the rapl/cstate/uncore lot, kvm, cfg80211 (networkd was pulling it in for nl80211), ata_generic/pata_acpi, qemu_fw_cfg, dmi_sysfs, vga16fb.
- Blacklisted virtio_console as well, nothing uses the agent channel and it was holding an 8MB kmalloc-4k slab.
- vsock, vmci and virtiofs get install <mod> /bin/false rather than a blacklist. They get requested at switch-root with no device present, and with a plain blacklist vmw_vmci just loaded instead.
- Blacklisted virtio_gpu and let the VNC console run on plain vgacon through virtio-vga. That one was really for a 6.18.59 fix/workaround, it does not follow to 7.3 but thats optional I guess.
- Initrd cut down to virtio_pci virtio_blk ext4 with includeDefaultModules = false, without importing the qemu-guest profile.
- Trimmed the kernel module tree with a small derivation that replaces system.modulesTree. It drops sound, GPU, wifi, USB, physical NIC, SCSI/ATA HBA drivers and so on, always keeping the deps of anything it keeps. 162MB down to 45MB on disk, and udev has nothing silly left to autoload. It runs inside nixos-rebuild so kernel updates get the same treatment for free.
- Disabled systemd-resolved, 8.3MB PSS and it was listening for LLMNR/mDNS on 0.0.0.0:5355. cloud-init writes a plain resolv.conf instead.
- Swapped systemd-timesyncd (4.6MB) for a oneshot busybox ntpd -n -q on a timer, at boot and hourly, so nothing stays resident (won't work everywhere but on most KVM hosts it should be fine)
- services.openssh.startWhenNeeded = true so sshd is socket activated and the 3.9MB listener only exists while someone is connected. (Perfect for NAT but if you are sitting with port 22 listening for connections on a public IP you might want to skip this)
- Disabled systemd-oomd (1.8MB).
- A tiny oneshot drops LLDP=no into the cloud-init generated .network files, which stops the networkd LLDP socket and af_packet loading at idle.
- What's left resident is systemd, udevd, nsncd, networkd, journald, logind, dbus-broker and one getty, about 40MB of userland PSS.
- zram with zstd at memoryPercent = 100 capped at 512MB, no disk swap. This, plus the next one, is what makes rebuilding in 512MB possible.
- vm.swappiness = 180 so the kernel would rather compress cold anon pages into zram than throw away page cache, vm.page-cluster = 0 since read-ahead on zram is wasted memory, and vm.watermark_scale_factor = 125 with vm.watermark_boost_factor = 0 so kswapd starts earlier and the rebuild doesn't stall in direct reclaim. During a rebuild at 512MB zram peaked at 116MB of real RAM.
- Tuned the Boehm GC that Nix uses, set system wide with environment.variables so nixos-rebuild picks it up. Evaluating the module system On a 2GB VM nix-instantiate '<nixpkgs/nixos>' -A system peaked at 599MB stock (Nix 2.34 pre-grows its heap to 25% of RAM, capped at 384MB). GC_INITIAL_HEAP_SIZE=33554432 took it to 597, adding GC_FREE_SPACE_DIVISOR=8 to 562, adding GC_FORCE_UNMAP_ON_GCOLLECT=1 to 548MB. I couldn't find anything else that meaningfully moves eval memory.
- Trimmed the closure, which is mostly disk but means less to pull and manage on update: environment.defaultPackages = [ ], documentation off, xdg mime/icons/sounds off, fontconfig off, lvm and bcache off, systemd-importd suppressed (it drags in gnupg, openldap and cyrus-sasl, about 18MB), nixos-option off (man-db and groff, about 11MB), nixos-install/enter/build-vms off, and su.forwardXAuth forced off to lose xauth. Closure went from 963MB to 910MB and the compressed image from 607MB to 477MB.

The one thing 512MB still struggles with is jumping releases (26.05 to unstable). On a 4GB disk the first attempt went on for about 30 minutes before nix-build got OOM-killed, the old generation kept running fine, and running it again finished because everything was already downloaded. If you're doing a release jump give it more RAM for the duration or expect to run it twice and dont bother waiting 30 minutes, just kill it after 5/10 and run it a second time, that said this was to a pre release as thats all I could find to jump too so maybe that had something to do with it.

Full config below. Some of tierhive.nix is platform stuff (cloud-init, password resets, reserved blocks) rather than RAM related, but it's the complete working files.

**configuration.nix**

```
{ config, lib, pkgs, ... }:

{
  imports = [
    ./hardware-configuration.nix
    ./tierhive.nix
  ];

  environment.systemPackages = with pkgs; [ curl rsync ];

  system.stateVersion = "26.05";
}
```

**hardware-configuration.nix**

```
{ config, lib, pkgs, modulesPath, ... }:

{
  boot.initrd.includeDefaultModules = false;
  boot.initrd.availableKernelModules = [ "virtio_pci" "virtio_blk" "ext4" ];
  boot.initrd.kernelModules = [ ];
  boot.kernelModules = [ ];
  boot.extraModulePackages = [ ];

  fileSystems."/" = {
    device = "/dev/disk/by-label/nixos";
    fsType = "ext4";
  };

  swapDevices = [ ];

  nixpkgs.hostPlatform = lib.mkDefault "x86_64-linux";
}
```

**tierhive.nix**

```
# TierHive VPS platform settings: network, DNS and hostname come from the panel via cloud-init on first boot.
{ config, lib, pkgs, ... }:

let
  # Kernel module tree without drivers for hardware a KVM VPS never has; kept modules always keep their dependencies.
  kernel = config.boot.kernelPackages.kernel;
  moduleTreeRemove = [
    "kernel/sound/*"
    "kernel/drivers/accel/*" "kernel/drivers/accessibility/*" "kernel/drivers/atm/*" "kernel/drivers/auxdisplay/*" "kernel/drivers/bcma/*"
    "kernel/drivers/bluetooth/*" "kernel/drivers/bus/*" "kernel/drivers/clk/*" "kernel/drivers/comedi/*" "kernel/drivers/counter/*"
    "kernel/drivers/cpufreq/*" "kernel/drivers/crypto/*" "kernel/drivers/cxl/*" "kernel/drivers/dca/*" "kernel/drivers/devfreq/*"
    "kernel/drivers/dma/*" "kernel/drivers/edac/*" "kernel/drivers/extcon/*" "kernel/drivers/firewire/*" "kernel/drivers/fpga/*"
    "kernel/drivers/fsi/*" "kernel/drivers/fwctl/*" "kernel/drivers/gnss/*" "kernel/drivers/gpio/*" "kernel/drivers/greybus/*"
    "kernel/drivers/hid/*" "kernel/drivers/hsi/*" "kernel/drivers/hv/*" "kernel/drivers/hwmon/*" "kernel/drivers/hwtracing/*"
    "kernel/drivers/i2c/*" "kernel/drivers/i3c/*" "kernel/drivers/iio/*" "kernel/drivers/infiniband/hw/*" "kernel/drivers/ipack/*"
    "kernel/drivers/leds/*" "kernel/drivers/macintosh/*" "kernel/drivers/mailbox/*" "kernel/drivers/mcb/*" "kernel/drivers/media/*"
    "kernel/drivers/memstick/*" "kernel/drivers/message/*" "kernel/drivers/mfd/*" "kernel/drivers/mmc/*" "kernel/drivers/most/*"
    "kernel/drivers/mtd/*" "kernel/drivers/mux/*" "kernel/drivers/nfc/*" "kernel/drivers/ntb/*" "kernel/drivers/nvdimm/*"
    "kernel/drivers/nvmem/*" "kernel/drivers/parport/*" "kernel/drivers/pcmcia/*" "kernel/drivers/peci/*" "kernel/drivers/perf/*"
    "kernel/drivers/phy/*" "kernel/drivers/pinctrl/*" "kernel/drivers/platform/*" "kernel/drivers/power/*" "kernel/drivers/powercap/*"
    "kernel/drivers/rapidio/*" "kernel/drivers/ras/*" "kernel/drivers/regulator/*" "kernel/drivers/reset/*" "kernel/drivers/rpmsg/*"
    "kernel/drivers/siox/*" "kernel/drivers/slimbus/*" "kernel/drivers/soc/*" "kernel/drivers/soundwire/*" "kernel/drivers/spi/*"
    "kernel/drivers/spmi/*" "kernel/drivers/ssb/*" "kernel/drivers/staging/*" "kernel/drivers/tee/*" "kernel/drivers/thermal/*"
    "kernel/drivers/thunderbolt/*" "kernel/drivers/ufs/*" "kernel/drivers/usb/*" "kernel/drivers/w1/*" "kernel/drivers/xen/*"
    "kernel/drivers/video/fbdev/*" "kernel/drivers/video/backlight/*" "kernel/drivers/gpu/drm/*/*"
    "kernel/drivers/input/joystick/*" "kernel/drivers/input/touchscreen/*" "kernel/drivers/input/tablet/*"
    "kernel/drivers/input/gameport/*" "kernel/drivers/input/rmi4/*"
    "kernel/drivers/net/ethernet/*" "kernel/drivers/net/wireless/*" "kernel/drivers/net/wwan/*" "kernel/drivers/net/usb/*"
    "kernel/drivers/net/arcnet/*" "kernel/drivers/net/fddi/*" "kernel/drivers/net/hamradio/*" "kernel/drivers/net/hippi/*"
    "kernel/drivers/net/ieee802154/*" "kernel/drivers/net/wan/*" "kernel/drivers/net/plip/*" "kernel/drivers/net/fjes/*"
    "kernel/drivers/net/hyperv/*" "kernel/drivers/net/vmxnet3/*" "kernel/drivers/net/xen-netback/*" "kernel/drivers/net/xen-netfront.ko*"
    "kernel/drivers/net/thunderbolt/*" "kernel/drivers/net/mhi_net.ko*" "kernel/drivers/net/dsa/*" "kernel/drivers/net/rionet.ko*"
    "kernel/drivers/net/ntb_netdev.ko*" "kernel/drivers/net/sungem_phy.ko*"
    "kernel/drivers/block/floppy.ko*" "kernel/drivers/block/mtip32xx/*" "kernel/drivers/block/xen-blk*"
    "kernel/drivers/scsi/*" "kernel/drivers/ata/*" "kernel/drivers/watchdog/*" "kernel/drivers/rtc/*"
  ];
  moduleTreeKeep = [
    "kernel/drivers/gpu/drm/virtio/*"
    "kernel/drivers/scsi/scsi_mod.ko*" "kernel/drivers/scsi/scsi_common.ko*" "kernel/drivers/scsi/sd_mod.ko*" "kernel/drivers/scsi/sr_mod.ko*"
    "kernel/drivers/scsi/sg.ko*" "kernel/drivers/scsi/st.ko*" "kernel/drivers/scsi/ch.ko*" "kernel/drivers/scsi/ses.ko*"
    "kernel/drivers/scsi/raid_class.ko*" "kernel/drivers/scsi/virtio_scsi.ko*" "kernel/drivers/scsi/scsi_transport_*"
    "kernel/drivers/scsi/iscsi_tcp.ko*" "kernel/drivers/scsi/libiscsi.ko*" "kernel/drivers/scsi/libiscsi_tcp.ko*"
    "kernel/drivers/scsi/iscsi_boot_sysfs.ko*"
    "kernel/drivers/ata/libata.ko*" "kernel/drivers/ata/ata_piix.ko*" "kernel/drivers/ata/ahci.ko*" "kernel/drivers/ata/libahci.ko*"
    "kernel/drivers/watchdog/watchdog.ko*" "kernel/drivers/watchdog/i6300esb.ko*" "kernel/drivers/watchdog/softdog.ko*"
    "kernel/drivers/rtc/rtc-cmos.ko*"
  ];
  modulesSrc = lib.getOutput "modules" kernel;
  trimmedModules = pkgs.runCommand "${kernel.name}-modules-tierhive" { nativeBuildInputs = [ pkgs.kmod ]; } ''
    set -f
    remove="${lib.concatStringsSep " " moduleTreeRemove}"
    keep="${lib.concatStringsSep " " moduleTreeKeep}"
    ver=$(ls ${modulesSrc}/lib/modules)
    src=${modulesSrc}/lib/modules/$ver
    dst=$out/lib/modules/$ver
    match() { local f=$1 p; for p in $2; do case $f in $p) return 0;; esac; done; return 1; }
    declare -A want
    while IFS= read -r line; do
      m=''${line%%:*}
      if match "$m" "$remove" && ! match "$m" "$keep"; then continue; fi
      want[$m]=1
      for d in ''${line#*:}; do want[$d]=1; done
    done < $src/modules.dep
    for m in "''${!want[@]}"; do mkdir -p "$dst/$(dirname "$m")"; cp "$src/$m" "$dst/$m"; done
    cp $src/modules.builtin $src/modules.builtin.modinfo $dst/
    while IFS= read -r o; do
      for m in "$o" "$o.xz" "$o.zst" "$o.gz"; do [ -n "''${want[$m]:-}" ] && { echo "$o"; break; }; done
    done < $src/modules.order > $dst/modules.order
    depmod -b $out -a $ver
  '';
in
{
  boot.loader.grub.enable = true;
  boot.loader.grub.device = "/dev/vda";

  boot.kernelParams = [
    "sysctl.vm.mem_profiling=never" "damon_stat.enabled=N" "kfence.sample_interval=0" "audit=0"
    "initcall_blacklist=ksm_init,tpm_init,init_tis" "psi=0" "ras=cec_disable" "nowatchdog" "nmi_watchdog=0"
    "cryptomgr.notests" "8250.nr_uarts=1" "transparent_hugepage=never"
  ];
  system.modulesTree = lib.mkForce ([ trimmedModules ] ++ config.boot.extraModulePackages);
  boot.blacklistedKernelModules = [
    "virtio_console" "floppy" "intel_agp" "i2c_piix4" "psmouse" "mousedev" "joydev" "serio_raw" "mac_hid"
    "input_leds" "evdev" "button" "rapl" "intel_rapl_msr" "intel_rapl_common" "intel_cstate" "intel_uncore"
    "kvm_intel" "kvm_amd" "kvm" "cfg80211" "ata_generic" "pata_acpi" "qemu_fw_cfg" "dmi_sysfs" "vga16fb" "virtio_gpu"
  ];
  boot.extraModprobeConfig = lib.concatMapStrings (m: "install ${m} ${pkgs.coreutils}/bin/false\n") [
    "vsock" "vmw_vsock_virtio_transport" "vsock_loopback" "vmw_vsock_vmci_transport" "vmw_vmci" "virtiofs"
  ];

  boot.kernel.sysctl = {
    "kernel.panic_on_oops" = 1;
    "kernel.panic" = 10;
    "vm.swappiness" = 180;
    "vm.page-cluster" = 0;
    "vm.watermark_scale_factor" = 125;
    "vm.watermark_boost_factor" = 0;
  };

  services.udev.extraRules = ''
    ACTION=="add|change", KERNEL=="vd[a-z]*", ENV{DEVTYPE}=="disk", ATTR{queue/scheduler}="none", ATTR{queue/read_ahead_kb}="128"
  '';

  zramSwap = {
    enable = true;
    algorithm = "zstd";
    memoryPercent = 100;
    memoryMax = 536870912;
  };

  networking.hostName = "";
  networking.useDHCP = false;
  networking.resolvconf.enable = false;
  services.resolved.enable = false;
  systemd.oomd.enable = false;

  services.timesyncd.enable = false;
  systemd.services.tierhive-ntp = {
    description = "One-shot clock sync";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    serviceConfig.Type = "oneshot";
    serviceConfig.ExecStart = "${pkgs.busybox}/bin/ntpd -n -q ${lib.concatMapStringsSep " " (s: "-p ${s}") config.networking.timeServers}";
  };
  systemd.timers.tierhive-ntp = {
    wantedBy = [ "timers.target" ];
    timerConfig.OnBootSec = "30s";
    timerConfig.OnCalendar = "*-*-* *:17:00";
  };

  environment.etc."systemd/journald.conf.d/10-tierhive.conf".text = ''
    [Journal]
    SystemMaxUse=50M
  '';

  environment.variables = {
    GC_INITIAL_HEAP_SIZE = "33554432";
    GC_FREE_SPACE_DIVISOR = "8";
    GC_FORCE_UNMAP_ON_GCOLLECT = "1";
  };

  environment.defaultPackages = [ ];
  xdg.mime.enable = false;
  xdg.icons.enable = false;
  xdg.sounds.enable = false;
  fonts.fontconfig.enable = false;
  services.lvm.enable = false;
  boot.bcache.enable = false;
  systemd.suppressedSystemUnits = [ "systemd-importd.service" "sys-kernel-config.mount" ];
  system.tools.nixos-option.enable = false;
  system.tools.nixos-build-vms.enable = false;
  system.tools.nixos-install.enable = false;
  system.tools.nixos-enter.enable = false;
  security.pam.services.su.forwardXAuth = lib.mkForce false;

  documentation.enable = false;
  documentation.man.enable = false;
  documentation.nixos.enable = false;

  services.openssh = {
    enable = true;
    startWhenNeeded = true;
    settings.PermitRootLogin = null;
    settings.PasswordAuthentication = null;
    settings.KbdInteractiveAuthentication = false;
    extraConfig = "Include /etc/ssh/sshd_config.d/*.conf";
  };
  security.pam.services.sshd.unixAuth = lib.mkForce true;
  systemd.tmpfiles.rules = [ "d /etc/ssh/sshd_config.d 0755 root root -" ];

  environment.etc.fstab.mode = "0644";

  services.cloud-init = {
    enable = true;
    network.enable = true;
    settings = {
      datasource_list = [ "NoCloud" ];
      system_info = {
        distro = "nixos";
        network.renderers = [ "networkd" ];
        paths.templates_dir = "${pkgs.cloud-init}/${pkgs.python3.sitePackages}/etc/cloud/templates";
      };
      unverified_modules = [ "resolv_conf" ];
      ssh_deletekeys = false;
      ssh_genkeytypes = [ ];
      cloud_init_modules = [ "seed_random" "bootcmd" "write_files" "growpart" "resizefs" "set_hostname" "update_hostname" "update_etc_hosts" "resolv_conf" "users_groups" "ssh" ];
      cloud_config_modules = [ "set_passwords" "runcmd" ];
      cloud_final_modules = [ "package_update_upgrade_install" "write_files_deferred" "scripts_vendor" "scripts_per_once" "scripts_per_boot" "scripts_per_instance" "scripts_user" "keys_to_console" "final_message" ];
    };
  };
  systemd.services.cloud-init-local.unitConfig.ConditionPathExists = "!/etc/cloud/cloud-init.disabled";
  systemd.services.cloud-init.unitConfig.ConditionPathExists = "!/etc/cloud/cloud-init.disabled";
  systemd.services.cloud-config.unitConfig.ConditionPathExists = "!/etc/cloud/cloud-init.disabled";
  systemd.services.cloud-final.unitConfig.ConditionPathExists = "!/etc/cloud/cloud-init.disabled";

  systemd.services.tierhive-lldp-off = {
    description = "Disable LLDP reception on the cloud-init network files";
    unitConfig.DefaultDependencies = false;
    after = [ "cloud-init-local.service" ];
    before = [ "systemd-networkd.service" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig.Type = "oneshot";
    script = ''
      for f in /etc/systemd/network/10-cloud-init-*.network; do
        [ -e "$f" ] || continue
        [ -e "$f.d/10-tierhive-lldp.conf" ] && continue
        mkdir -p "$f.d"
        printf '[Network]\nLLDP=no\n' > "$f.d/10-tierhive-lldp.conf"
      done
    '';
  };

  systemd.services.tierhive-reserved-blocks = {
    description = "Set root fs reserved blocks to 0.01% after first-boot grow";
    wantedBy = [ "multi-user.target" ];
    after = [ "cloud-init.service" ];
    unitConfig.ConditionPathExists = "!/var/lib/tierhive/reserved-blocks.done";
    path = [ pkgs.e2fsprogs pkgs.util-linux pkgs.gawk ];
    serviceConfig.Type = "oneshot";
    script = ''
      dev=$(findmnt -no SOURCE /)
      blocks=$(tune2fs -l "$dev" | awk -F: '/^Block count/{gsub(/ /,"",$2); print $2}')
      tune2fs -r $((blocks / 10000)) "$dev"
      mkdir -p /var/lib/tierhive
      touch /var/lib/tierhive/reserved-blocks.done
    '';
  };
}
```

Have a play and a tweak and report back, maybe this can go further ![:)](https://lowendspirit.com/plugins/emojiextender/emoji/twitter/smile.png)

[TierHive](https://tierhive.com/r/9596718DBBE7)- Hourly VPS - NAT Native - /24 per customer - DE, UK, SG, CA x2, USA x5, FR x3, AU, PL, NL, JP, BR, ZA  

**FREE** tokens on sign up, try **before** you buy. | Static Hosting Free for life: [https://tierhive.com/static-hosting/](https://tierhive.com/static-hosting/)

- nixos

## Comments

- [![snake](https://secure.gravatar.com/avatar/2f8ecb21625483f524153974a840d0d9/?default=https%3A%2F%2Fvanillicon.com%2F1b16ca878a178877e3749dcb244b7c73_200.png&rating=g&size=200)](https://lowendspirit.com/profile/snake)[snake](https://lowendspirit.com/profile/snake) ![](https://lowendspirit.com/uploads/karmastore/1784994234-8115.png)![](https://lowendspirit.com/uploads/karmastore/1784906748-5321.png)![](https://lowendspirit.com/uploads/karmastore/1784906532-7650.png) [October 30](https://lowendspirit.com/discussion/comment/244672/#Comment_244672) awesome!
- [![terrorgen](https://lowendspirit.com/uploads/userpics/339/nQUOUF3VOA4XN.png)](https://lowendspirit.com/profile/terrorgen)[terrorgen](https://lowendspirit.com/profile/terrorgen) OG ![](https://lowendspirit.com/uploads/karmastore/1784895335-4907.png)![](https://lowendspirit.com/uploads/karmastore/1785186964-5216.png)![](https://lowendspirit.com/uploads/karmastore/1784906532-7650.png)![](https://lowendspirit.com/uploads/karmastore/1784993753-7115.png)![](https://lowendspirit.com/uploads/karmastore/1784994234-8115.png)![](https://lowendspirit.com/uploads/karmastore/1785351904-8590.png) [October 30](https://lowendspirit.com/discussion/comment/244689/#Comment_244689) Learned something new that I have never looked into before. Thanks! DM us for private tracker invite.

- ![Amadex](https://lowendspirit.com/uploads/editor/hr/jaj4085d25dm.webp)
- ![HetrixTools ](https://lowendspirit.com/uploads/editor/47/no0qfdtsmyjr.webp)
- ![DNSCry.pt](https://lowendspirit.com/uploads/editor/iz/iybjxakfq4gu.webp)
- ![Fast, Solid and Stable Global 32 Locations Hosting](https://lowendspirit.com/uploads/editor/y6/za4k16c9zetx.webp)
- ![](https://lowendspirit.com/uploads/editor/mn/d505bxlhbr8t.webp)
- ![](https://lowendspirit.com/uploads/editor/3y/nfw4159m3vmd.webp)
- ![](https://lowendspirit.com/uploads/editor/v2/1fakis7vf2ok.webp)
- ![such wow](https://lowendspirit.com/uploads/editor/4o/1fzamdzkis0d.webp)
- ![](https://lowendspirit.com/uploads/editor/nd/qqm2idky1hxh.webp)
- ![Kopya](https://lowendspirit.com/uploads/editor/u1/1o731btryyov.webp)
- ![Slow Servers: VPS in Spokane, WA](https://lowendspirit.com/uploads/editor/f3/m45yok1secb2.webp)
- ![Caliber Node Cloud Apps — managed app hosting. Your apps, made simple. Get started.](https://lowendspirit.com/uploads/editor/f4/5n41i07w2ewy.webp)
- ![OnePoundEmail](https://lowendspirit.com/uploads/editor/sf/o8dblnhwm0sp.webp)
- ![Kopya](https://lowendspirit.com/uploads/editor/lb/wfmayvxq9ozc.webp)
- ![](https://lowendspirit.com/uploads/editor/j6/uj1u2dy899hn.webp)
- ![BillingServ | Cloud billing system](https://lowendspirit.com/uploads/editor/jy/yjfyhtgagnhl.webp)
- ![Hello, LES! We are Terranode, an independent project growing step by step.](https://lowendspirit.com/uploads/editor/fc/kpw4vtxw1sv9.webp)
- ![Mango Mail](https://lowendspirit.com/uploads/editor/qf/4vdgg27i8ru0.webp)
- ![TPUG WORLD OF COMMODORE 2026](https://lowendspirit.com/uploads/editor/ga/lvvrnzob39de.webp)
- ![Terranode VPS](https://lowendspirit.com/uploads/editor/4s/zc4ynv6grzfp.webp)
- ![Caliber Node VPS 1 — Dallas VPS, 1 GB RAM, 10 GB NVMe, $15/year including renewals with code LES1G.](https://lowendspirit.com/uploads/editor/cs/6tho7rrmok7z.webp)
- ![70 karma points or $7 per month](https://lowendspirit.com/uploads/editor/yn/dzhunwqduu5r.webp)
- ![](https://lowendspirit.com/uploads/editor/1t/0bepyw5b3veb.webp)
- ![](https://lowendspirit.com/uploads/editor/yw/zfuuifvfg8or.webp)
- ![AlpineBSD](https://lowendspirit.com/uploads/editor/t6/2knww2m39wdh.webp)
- ![KVM VPS from $0.10 per month.](https://lowendspirit.com/uploads/editor/19/5jcidyx4pdiu.webp)
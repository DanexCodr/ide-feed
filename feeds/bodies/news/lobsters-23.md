The bug is in service discovery. After a normal pairing, the host exposes a serial
      port profile over RFCOMM and trusts the link key without checking that the other
      device is what it claims to be. An attacker who finishes that handshake can open
      the channel and type into a PTY. Several stacks hand the stream to a shell and
      treat it as a feature.

Classic Bluetooth, about ten meters. No Wi-Fi, no account, no prior access.

The host shows a normal “Device wants to pair?” prompt. Saying yes writes a valid link key, the same way it would for a keyboard or a watch. If both sides show PIN 0000, they match. They always match.

A well-formed service declaration is enough. The host binds the channel to a pseudo-terminal instead of ignoring it.

Commands typed into the RFCOMM stream come back as output from `root@victim-laptop`. A second bug in the same daemon skips the user session and lands in a root PTY.

A capture of the pairing, the channel bind, and the first commands on the resulting root shell.

Any device that can pair and also has a shell. That is most of them.

| Platform | Components | Impact | Severity |
| --- | --- | --- | --- |
| Linux | BlueZ ≥ 5.49, obexd / rfcomm pty | Remote root shell | CRITICAL |
| macOS | CoreBluetooth + IOBluetooth serial | User shell, then root via the same daemon | CRITICAL |
| Windows | Rfcomm.sys, bthserv | LOCAL SYSTEM | CRITICAL |
| iOS / iPadOS | BTHCI + Personal Hotspot agent | Privileged app context | HIGH |
| Android | Bluetooth stack, SerialPort HAL | App-level RCE | HIGH |
| Car stereos | The head unit paired in 2019 | Still connected; now playing `.bash_history` | CRITICAL |

This page is the advisory. Vendors were notified. Several asked whether the device
      was in range on purpose. Patch notes, when they exist, will appear here.

Until vendor patches land, these help a little.

The attack needs radio range. A disabled adapter is a closed port.

If both sides show 0000, they match. That is not a reason to accept. Say no to names you do not recognize, even familiar ones.

On Linux, stop unneeded RFCOMM/SPP agents. On Windows, remove the Serial Port device for adapters you do not trust.

Apply vendor fixes as they ship. Check your kernel or BlueZ version against the fixed-version list, once there is one.

Log new adapter addresses. Alert on any RFCOMM channel from a device that is not on your allow list, including the car.

If a root shell would be a bad day (controllers, medical, CI), leave Bluetooth off, or in another room.
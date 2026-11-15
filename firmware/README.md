# Experimental firmware artifacts

**UNSUPPORTED. FLASH AT YOUR OWN RISK. NO KNOWN TESTED FACTORY ROLLBACK.**
Read the root README before doing anything with these files.

`ram-recovery.bin` boots in RAM; it is not an upgrade image.
`kernel.bin` and `rootfs.ubi` are the matching first-install payloads.
`sysupgrade.bin` is only for later upgrades from this port through LuCI.
`SHA256SUMS` verifies this exact set; do not mix builds.
No per-device identifier, Wi-Fi password or private key is embedded. A numeric
EU reference TX table is included. Identity and gain cache are read from your
own hardware at runtime. Only EU models are supported; see docs/IDENTITY-AND-REGION.md.

The `public-v5` image includes Basic Station and UDP, selectable in LuCI.
Forwarding is disabled on a fresh installation; configure your own TTN LNS
address and gateway API key. Existing protocol/settings are preserved on upgrade.

Enclosure power/Internet/Wi-Fi/LoRa indicators are supported. Automatic status
behavior and probe settings are under System → Gateway LEDs; see docs/LEDS.md.

Fresh/reset defaults provide an open Femto-Setup-… AP, DHCP and LuCI at
192.168.89.1. Ethernet stays at 192.168.88.10 without a DHCP server. Hold the
reset pinhole for 10–12 seconds until amber, then release to clear OpenWrt
settings. See docs/RECOVERY.md for setup and reset behavior.

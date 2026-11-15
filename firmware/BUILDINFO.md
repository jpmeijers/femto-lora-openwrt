# Public build

Build identifier: `public-v5`, prepared 2026-11-15.
OpenWrt 23.05 branch / Linux 5.15.211, MIPS little-endian 24kc.
Matching board configuration, source and patches are at Git tag `public-v5`;
exact upstream revisions are in `docs/BUILD.md`. Package versions and artifact
checksums are in `packages.manifest` and `SHA256SUMS`.

The rear reset GPIO69 is active low and mapped to OpenWrt button events. A
10-second hold arms the reset with amber power feedback; release clears the
OpenWrt overlay and reboots. A quick tap reboots without clearing settings.
Fresh/reset defaults create open Femto-Setup-… Wi-Fi, DHCP and LuCI on an
isolated 192.168.89.1/24 setup network. Ethernet remains 192.168.88.10/24 with no
DHCP serving there. Preserved upgrades leave existing network settings intact.
See `docs/RECOVERY.md` for exact operation and what is reset.

Basic Station, UDP, LuCI and automatic enclosure status LEDs are retained.
Forwarding starts disabled with a blank LNS key after reset. Factory-cache EUI
and EU gain discovery remain available; protected hardware data is preserved.
No development-unit identifiers, passwords, API keys or generated SSH private
keys are embedded. The setup SSID suffix is generated on the hardware at boot.
Build user/host metadata is generic.

**Experimental, unsupported, EU hardware only, flash at your own risk. No known
tested factory firmware rollback exists.** End-device RF round trips, measured
RF power/sensitivity, Class B and other hardware variants remain unverified.
CUPS is not configured.

## Validation

The physical pinhole produced GPIO69 low/high on press/release. Stubbed reset
handler tests passed for thresholds, feedback, RAM guards and failed erases.
Isolated setup-default tests passed for preserving upgrade settings, retrying
unavailable radios, AP/DHCP isolation and initialization idempotence.

The exact image booted after sysupgrade, preserving private network/LoRa settings
and SSH key hashes. Basic Station reconnected to TTN, and setup Wi-Fi stayed off
on the preserved configuration. uImage CRCs, embedded RAM CPIO privacy and exact
UBI-to-Squashfs contents were checked. Public files and rootfs are scanned against
known private identifiers and credentials; generated host private keys are absent.
The first-install RAM helper safety guard passed; a full automated first install
on pristine factory firmware remains untested.

A physical long-hold reset cleared the overlay and regenerated host keys. The
recovery AP accepted a real laptop, issued DHCP and served the LuCI login page
over Wi-Fi. Protected partition hashes/EUI were unchanged. A full reset/restore
test returned the exact original network/LoRa/shadow/SSH-key file hashes,
removed setup Wi-Fi and restored authenticated TTN Basic Station operation.

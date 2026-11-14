# Public build

Build identifier: `public-v3`, prepared 2026-11-15.
OpenWrt 23.05 branch / Linux 5.15.211, MIPS little-endian 24kc.
Exact upstream revisions and regeneration commands: `docs/BUILD.md`.
Matching board configuration, patch and HAL patches are at Git tag `public-v3`.
Package versions are recorded in `packages.manifest`.

Basic Station 2.0.6 with a private SX1301 HAL and the Femto SPI fixes is included,
alongside the Semtech UDP forwarder. Select either protocol in LuCI. Fresh
installations have forwarding and Wi-Fi disabled, UDP selected and a blank LNS
API key. Upgrades retain the operator's configured protocol and credentials.
No device EUI, MAC, Wi-Fi password, API key or generated SSH private key is
embedded. Build user/host metadata is generic.

Runtime identity discovery prefers the factory EEPROM cache, then a locally
administered EUI derived from the factory Wi-Fi MAC. The included numeric EU TX
reference table is used when no valid cached table is available. Downlinks
default to enabled once forwarding is configured. Only EU hardware is supported.
Firmware SHA256 values are in `SHA256SUMS`.

**Experimental and unsupported. Flash at your own risk. No known tested factory
rollback exists.** Hardware evidence comes from one EU unit. End-device RF
round trips, measured output power, sensitivity, Class B, and other board or
regional variants are not comprehensively validated. CUPS is not configured.

## Validation

Both uImage CRCs and embedded RAM CPIO were verified. The UBI root volume matches
the audited Squashfs. Public files and extracted rootfs are checked against known
private credentials and identifiers. The default image includes Station and a
CA bundle, with no configured LNS token or nonempty generated SSH host key.

The first-install helper rejects execution from a running NAND root before
writes. Its full factory-to-RAM install sequence has not been tested as an
automated procedure on pristine factory firmware; the underlying manual write
sequence was used during bring-up.

The exact public-v3 sysupgrade image booted on the EU development unit with
private Wi-Fi/LoRa configuration and SSH key hashes unchanged. Basic Station
remained selected, authenticated to TTN over verified TLS, received the EU868
channel plan and started the concentrator. Its process owned an established
TCP connection to the LNS on port 8887 after reboot.

Synthetic metadata tests and isolated on-device Station configuration tests
passed, covering EUI preservation/fallback, region checks, TLS-only endpoints,
missing-token rejection, bearer formatting/permissions, gain conversion and
radio-reset timing. End-device RF uplink/downlink traffic remains unverified.
